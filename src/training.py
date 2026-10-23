"""Vòng huấn luyện LSTM (Phase 7).

Tách khỏi ``scripts/train_lstm.py`` để kiểm thử được: ``test_overfit_10_mau``
chạy đúng :func:`train_epoch` này. Mô hình không học thuộc nổi mười mẫu thì lỗi
nằm ở vòng huấn luyện chứ không ở dữ liệu, và mọi con số sau đó vô nghĩa.

Mỗi epoch đo hai thứ trên CÙNG một cách — chế độ ``eval``, không tăng cường,
cùng hàm loss có trọng số — cho cả tập train lẫn tập val. Loss chạy trong lúc
học thì đo trên bản tăng cường, có dropout, nên không đặt cạnh loss val được:
khoảng cách giữa hai đường khi đó lẫn cả tác dụng của tăng cường và dropout,
không chỉ quá khớp.
"""

import copy
import random
import time
from collections import namedtuple

import numpy as np
import torch

from src import config


def set_seed(seed=config.SEED):
    """Cố định seed ở cả ba chỗ: ``random``, ``numpy``, ``torch``."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def class_weights(y, n_classes=len(config.CLASSES)):
    """Trọng số lớp kiểu "balanced", ``N / (K · n_lớp)``, tính trên nhãn train:
    lớp càng ít mẫu càng nặng, tổng có trọng số của mỗi lớp như nhau.

    Raises:
        ValueError: có lớp không có mẫu nào.
    """
    counts = np.bincount(np.asarray(y), minlength=n_classes)
    if np.any(counts == 0):
        missing = [config.CLASSES[k] for k in np.flatnonzero(counts == 0)]
        raise ValueError(f"Lớp không có mẫu train nào: {missing}")
    return torch.tensor(len(y) / (n_classes * counts), dtype=torch.float32)


def train_epoch(model, loader, loss_fn, optimizer):
    """Một lượt qua ``loader`` ở chế độ ``train``.

    Returns:
        loss trung bình theo mẫu.
    """
    model.train()
    total, count = 0.0, 0
    for x, y in loader:
        optimizer.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        optimizer.step()
        total += loss.item() * len(y)
        count += len(y)
    return total / max(count, 1)


@torch.no_grad()
def evaluate(model, sequences, y, loss_fn, batch=config.LSTM_EVAL_BATCH):
    """Loss và nhãn dự đoán trên một tập chuỗi cố định, chế độ ``eval``.

    Returns:
        ``(loss, pred (n,) int64)``.
    """
    model.eval()
    sequences = np.ascontiguousarray(sequences, dtype=np.float32)
    logits = torch.cat([model(torch.from_numpy(sequences[i:i + batch]))
                        for i in range(0, len(sequences), batch)])
    loss = loss_fn(logits, torch.as_tensor(np.asarray(y), dtype=torch.int64))
    return float(loss), logits.argmax(dim=1).numpy().astype(np.int64)


class EarlyStop:
    """Dừng sớm theo TRUNG BÌNH TRƯỢT ``window`` epoch của một điểm số càng cao
    càng tốt (macro-F1 val).

    macro-F1 val dao động mạnh giữa hai epoch liền nhau — mỗi lớp cử chỉ của
    val chỉ có khoảng 100 cửa sổ. Chọn epoch có điểm THÔ cao nhất là chọn một
    đỉnh nhiễu: con số báo cáo lạc quan, và một đỉnh đến sớm làm dừng giữa
    chừng khi mô hình còn đang học (đổi 2026-10-10; ``results/phase7/notes.md``
    mục 9). Đường làm mượt cho biết mô hình ỔN ĐỊNH ở đâu.

    Checkpoint là epoch CUỐI của cửa sổ trượt có trung bình cao nhất — chọn
    được ngay lúc epoch đó vừa xong, không cần nhìn trước. Chưa đủ ``window``
    epoch thì chưa chọn và chưa đếm kiên nhẫn: trung bình của vài epoch đầu vẫn
    để một đỉnh nhiễu thắng. Bằng điểm tốt nhất không tính là tốt hơn — giữ
    epoch sớm hơn. ``window=1`` là dừng sớm theo điểm thô.
    """

    def __init__(self, patience=config.LSTM_PATIENCE, window=config.LSTM_CURVE_SMOOTH):
        self.patience = patience
        self.window = window
        self.scores = []
        self.best_epoch = 0
        self.best_score = -np.inf       # trung bình trượt tốt nhất
        self.best_raw = None            # điểm thô của chính epoch đó
        self.best_state = None
        self.last_epoch = 0

    def update(self, epoch, score, model):
        """Ghi điểm của một epoch. Trả về ``True`` nếu đây là epoch tốt nhất."""
        self.last_epoch = epoch
        self.scores.append(float(score))
        if len(self.scores) < self.window:
            return False
        smoothed = float(np.mean(self.scores[-self.window:]))
        if smoothed > self.best_score:
            self.best_epoch, self.best_score, self.best_raw = epoch, smoothed, float(score)
            self.best_state = copy.deepcopy(model.state_dict())
            return True
        return False

    @property
    def should_stop(self):
        return self.best_epoch > 0 and self.last_epoch - self.best_epoch >= self.patience


def smoothed_minimum(history, key, window=config.LSTM_CURVE_SMOOTH):
    """Epoch mà trung bình trượt ``window`` epoch của ``key`` thấp nhất.

    Loss val dao động mạnh giữa hai epoch liền nhau, nên điểm thấp nhất của
    đường thô chủ yếu là may rủi; điểm thấp nhất của đường đã làm mượt cho biết
    loss val ngừng giảm ở đâu — sau đó là quá khớp.

    Returns:
        ``(epoch cuối của cửa sổ trượt, giá trị trung bình)``.
    """
    values = np.array([r[key] for r in history], dtype=np.float64)
    window = min(window, len(values))
    rolling = np.convolve(values, np.ones(window) / window, mode="valid")
    k = int(np.argmin(rolling))
    return int(history[k + window - 1]["epoch"]), float(rolling[k])


def tail_stats(history, key, n=config.LSTM_PATIENCE):
    """Trung bình và độ lệch chuẩn của ``key`` trong ``n`` epoch cuối.

    Checkpoint là epoch có macro-F1 val CAO NHẤT — đỉnh của một chuỗi nhiễu,
    chọn trên chính tập val, nên lạc quan. Mức quanh nó cho biết mô hình thường
    đạt bao nhiêu.
    """
    values = np.array([r[key] for r in history[-n:]], dtype=np.float64)
    return float(values.mean()), float(values.std())


def fit(model, train_loader, train_sequences, y_train, val_sequences, y_val,
        loss_fn, optimizer, max_epochs=config.LSTM_MAX_EPOCHS,
        patience=config.LSTM_PATIENCE, on_epoch=None, window=config.LSTM_CURVE_SMOOTH):
    """Huấn luyện, dừng sớm theo macro-F1 val đã làm mượt (``EarlyStop``).

    Args:
        train_loader: lô train (có tăng cường) để học.
        train_sequences, y_train: tập train KHÔNG tăng cường, để đo. ``None``
            thì không đo train — bảng khảo sát của Phase 8 chỉ cần val, và đo
            train không đổi gì trong quá trình học (chế độ eval, không rút số
            ngẫu nhiên).
        val_sequences, y_val: tập val, để đo và dừng sớm.
        on_epoch: hàm gọi sau mỗi epoch với ``(dòng lịch sử, EarlyStop)``.
        window: số epoch của trung bình trượt; ``1`` là theo điểm thô.

    Returns:
        ``(history, stopper)`` — ``history`` là list dict mỗi epoch một dòng:
        ``epoch``, ``train_loss_running``, ``train_loss``, ``val_loss``,
        ``train_macro_f1``, ``val_macro_f1``. ``stopper`` giữ epoch tốt nhất và
        trọng số của nó.
    """
    from src.evaluation import macro_f1   # nạp lười: kéo theo scikit-learn

    stopper = EarlyStop(patience, min(window, max_epochs))   # lần chạy ngắn vẫn có checkpoint
    history = []
    for epoch in range(1, max_epochs + 1):
        running = train_epoch(model, train_loader, loss_fn, optimizer)
        row = {"epoch": epoch, "train_loss_running": running}
        if train_sequences is not None:
            train_loss, train_pred = evaluate(model, train_sequences, y_train, loss_fn)
            row.update(train_loss=train_loss,
                       train_macro_f1=macro_f1(y_train, train_pred))
        val_loss, val_pred = evaluate(model, val_sequences, y_val, loss_fn)
        row.update(val_loss=val_loss, val_macro_f1=macro_f1(y_val, val_pred))
        history.append({key: row[key] for key in HISTORY_KEYS if key in row})
        stopper.update(epoch, row["val_macro_f1"], model)
        if on_epoch is not None:
            on_epoch(history[-1], stopper)
        if stopper.should_stop:
            break
    return history, stopper


#: Thứ tự cột của bảng lịch sử huấn luyện.
HISTORY_KEYS = ("epoch", "train_loss_running", "train_loss", "val_loss",
                "train_macro_f1", "val_macro_f1")

LSTMTraining = namedtuple("LSTMTraining",
                          "model history stopper dataset finger_pool weights seconds")
LSTMTraining.__doc__ = """Kết quả của :func:`train_lstm`. ``model`` mang trọng số
đã chọn: của epoch tốt nhất khi dừng sớm, của epoch cuối khi học số epoch cố
định (khi đó ``stopper`` là ``None``)."""


def train_lstm(X_tr, y_tr, X_va=None, y_va=None, seed=config.SEED, augment=True,
               zoom_style_p=config.AUG_ZOOM_STYLE_P,
               static_share=config.AUG_STATIC_SHARE,
               max_epochs=config.LSTM_MAX_EPOCHS, patience=config.LSTM_PATIENCE,
               window=config.LSTM_CURVE_SMOOTH, fixed_epochs=None,
               measure_train=True, sequence=None, model_kwargs=None,
               on_epoch=None):
    """Toàn bộ quy trình huấn luyện LSTM của Phase 7, gói lại để
    ``scripts/train_lstm.py`` và các bảng khảo sát của Phase 8 chạy ĐÚNG MỘT
    quy trình.

    Seed đặt ở ba chỗ (``set_seed``), rồi seed riêng cho tăng cường và cho thứ
    tự lô — cùng ``seed`` thì cùng từng chữ số, không phụ thuộc số luồng torch.
    Tăng cường mới mỗi epoch, chỉ trên train (luật 9); kho dáng ngón phụ dựng
    từ chính ``X_tr``. Adam, ``CrossEntropyLoss`` có trọng số lớp "balanced"
    tính trên đúng các nhãn mô hình thấy.

    Args:
        X_tr, y_tr: cửa sổ đã chuẩn hoá và nhãn của train.
        X_va, y_va: tập val để dừng sớm; không cần khi ``fixed_epochs``.
        fixed_epochs: học đúng bấy nhiêu epoch, không đo và không chọn gì trên
            val — k-fold của Phase 8, nơi fold giữ lại là tập đánh giá.
        measure_train: ``False`` thì không đo train mỗi epoch (bảng khảo sát).
        sequence: hàm ``cửa sổ đã chuẩn hoá → chuỗi`` — biến thể biểu diễn.
        model_kwargs: tham số cho ``LSTMClassifier`` khác mặc định.
        on_epoch: như :func:`fit`; với ``fixed_epochs`` nhận ``(dòng, None)``.

    Returns:
        :class:`LSTMTraining`.
    """
    from torch import nn
    from torch.utils.data import DataLoader

    from src.augment import finger_pose_pool
    from src.datasets import WindowDataset, window_sequences
    from src.models import LSTMClassifier

    set_seed(seed)
    # kho dáng ngón phụ CHỈ từ train (luật 9); không tăng cường thì không cần
    pool = finger_pose_pool(X_tr) if augment else None
    dataset = WindowDataset(X_tr, y_tr, "train", augment=augment,
                            rng=np.random.default_rng(seed), finger_pool=pool,
                            zoom_style_p=zoom_style_p, static_share=static_share,
                            sequence=sequence)
    loader = DataLoader(dataset, batch_size=config.LSTM_BATCH, shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    model = LSTMClassifier(**(model_kwargs or {}))
    weights = class_weights(dataset.labels)
    loss_fn = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.LSTM_LR)

    started = time.perf_counter()
    if fixed_epochs:
        history, stopper = [], None
        for epoch in range(1, fixed_epochs + 1):
            history.append({"epoch": epoch, "train_loss_running":
                            train_epoch(model, loader, loss_fn, optimizer)})
            if on_epoch is not None:
                on_epoch(history[-1], None)
    else:
        seq_tr = window_sequences(X_tr, sequence) if measure_train else None
        history, stopper = fit(model, loader, seq_tr, y_tr,
                               window_sequences(X_va, sequence), y_va, loss_fn,
                               optimizer, max_epochs=max_epochs, patience=patience,
                               on_epoch=on_epoch, window=window)
        model.load_state_dict(stopper.best_state)
    model.eval()
    return LSTMTraining(model, history, stopper, dataset, pool, weights,
                        time.perf_counter() - started)
