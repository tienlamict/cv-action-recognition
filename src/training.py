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
    """Dừng sớm theo một điểm số càng cao càng tốt (macro-F1 val).

    Giữ bản sao trọng số của epoch tốt nhất. Điểm bằng điểm tốt nhất không tính
    là tốt hơn — giữ epoch sớm hơn.
    """

    def __init__(self, patience=config.LSTM_PATIENCE):
        self.patience = patience
        self.best_epoch = 0
        self.best_score = -np.inf
        self.best_state = None
        self.last_epoch = 0

    def update(self, epoch, score, model):
        """Ghi điểm của một epoch. Trả về ``True`` nếu đây là epoch tốt nhất."""
        self.last_epoch = epoch
        if score > self.best_score:
            self.best_epoch, self.best_score = epoch, float(score)
            self.best_state = copy.deepcopy(model.state_dict())
            return True
        return False

    @property
    def should_stop(self):
        return self.last_epoch - self.best_epoch >= self.patience


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
        patience=config.LSTM_PATIENCE, on_epoch=None):
    """Huấn luyện, dừng sớm theo macro-F1 val.

    Args:
        train_loader: lô train (có tăng cường) để học.
        train_sequences, y_train: tập train KHÔNG tăng cường, để đo.
        val_sequences, y_val: tập val, để đo và dừng sớm.
        on_epoch: hàm gọi sau mỗi epoch với ``(dòng lịch sử, EarlyStop)``.

    Returns:
        ``(history, stopper)`` — ``history`` là list dict mỗi epoch một dòng:
        ``epoch``, ``train_loss_running``, ``train_loss``, ``val_loss``,
        ``train_macro_f1``, ``val_macro_f1``. ``stopper`` giữ epoch tốt nhất và
        trọng số của nó.
    """
    from src.evaluation import macro_f1   # nạp lười: kéo theo scikit-learn

    stopper = EarlyStop(patience)
    history = []
    for epoch in range(1, max_epochs + 1):
        running = train_epoch(model, train_loader, loss_fn, optimizer)
        train_loss, train_pred = evaluate(model, train_sequences, y_train, loss_fn)
        val_loss, val_pred = evaluate(model, val_sequences, y_val, loss_fn)
        row = {"epoch": epoch, "train_loss_running": running,
               "train_loss": train_loss, "val_loss": val_loss,
               "train_macro_f1": macro_f1(y_train, train_pred),
               "val_macro_f1": macro_f1(y_val, val_pred)}
        history.append(row)
        stopper.update(epoch, row["val_macro_f1"], model)
        if on_epoch is not None:
            on_epoch(row, stopper)
        if stopper.should_stop:
            break
    return history, stopper
