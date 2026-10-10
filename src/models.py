"""LSTM một chiều trên chuỗi 42 chiều (Phase 7): mô hình, checkpoint, và bộ
phân loại cho ``demo.py --model lstm``.

Lớp LSTM luôn tạo với ``bidirectional=False``, cố định bên trong và KHÔNG phải
tham số đặt được: LSTM hai chiều đọc cả những bước sau thời điểm quyết định,
nên con số báo cáo không đạt được trong hệ thống thời gian thực (luật 10).

File này nạp ``torch`` ngay khi import (~3 giây), nên chỉ import nó khi thật sự
dùng LSTM — ``live.make_model`` và ``evaluation.predict_windows`` nạp lười.

Checkpoint lưu kèm danh sách lớp, ``T`` và ``HZ``. Lúc nạp, ba thứ đó phải khớp
``config`` hiện tại: dùng mô hình học trên cửa sổ khác độ dài hay lưới thời gian
khác là một lỗi im lặng điển hình, nên ở đây nó là một lỗi ồn ào.
"""

from pathlib import Path

import numpy as np
import torch
from torch import nn

from src import config
from src.datasets import window_sequence

#: Cách gộp chuỗi đầu ra của LSTM thành một vector trước lớp phân loại.
POOLINGS = ("last", "mean", "max")


class LSTMClassifier(nn.Module):
    """LSTM một chiều → gộp theo thời gian → dropout → lớp tuyến tính.

    Args:
        input_size: số chiều mỗi bước — 42 (21 điểm × 2 toạ độ).
        hidden: số đơn vị ẩn mỗi lớp LSTM.
        num_layers: số lớp LSTM xếp chồng.
        dropout: dropout giữa các lớp LSTM và trước lớp phân loại.
        pooling: ``"last"`` (đầu ra ở bước cuối — đọc hết cửa sổ rồi quyết
            định), ``"mean"`` hoặc ``"max"`` theo thời gian.
        n_classes: số lớp đầu ra.
    """

    def __init__(self, input_size=config.LSTM_INPUT_SIZE, hidden=config.LSTM_HIDDEN,
                 num_layers=config.LSTM_LAYERS, dropout=config.LSTM_DROPOUT,
                 pooling=config.LSTM_POOLING, n_classes=len(config.CLASSES)):
        super().__init__()
        if pooling not in POOLINGS:
            raise ValueError(f"pooling phải là một trong {POOLINGS}, nhận '{pooling}'")
        self.hparams = {"input_size": int(input_size), "hidden": int(hidden),
                        "num_layers": int(num_layers), "dropout": float(dropout),
                        "pooling": pooling, "n_classes": int(n_classes)}
        self.lstm = nn.LSTM(input_size, hidden, num_layers=num_layers,
                            batch_first=True, bidirectional=False,
                            dropout=dropout if num_layers > 1 else 0.0)
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(hidden, n_classes)

    def forward(self, x):
        """``x`` ``(lô, T, input_size)`` → logit ``(lô, n_classes)``."""
        if x.dim() != 3 or x.shape[-1] != self.hparams["input_size"]:
            raise ValueError(f"Đầu vào phải có shape (lô, T, "
                             f"{self.hparams['input_size']}), nhận {tuple(x.shape)}")
        out, _ = self.lstm(x)
        pooling = self.hparams["pooling"]
        if pooling == "last":
            pooled = out[:, -1]
        elif pooling == "mean":
            pooled = out.mean(dim=1)
        else:
            pooled = out.max(dim=1).values
        return self.head(self.dropout(pooled))


def save_checkpoint(model, path=None, **meta):
    """Lưu trọng số, siêu tham số, danh sách lớp, ``T``, ``HZ`` và ``meta``,
    rồi nạp lại ngay ở chế độ an toàn ``weights_only``.

    Chế độ đó chỉ nhận kiểu Python thuần, nên ``meta`` được đổi về kiểu thuần
    trước khi lưu: ``torch.__version__`` là một lớp con của ``str``, số numpy
    không phải số Python — lọt vào thì file vẫn ghi được nhưng không nạp được.
    Nạp lại ngay là để lỗi hiện ra lúc lưu, không phải lúc chạy demo.
    """
    path = Path(path or config.LSTM_MODEL_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "hparams": dict(model.hparams),
                "classes": list(config.CLASSES), "T": int(config.T),
                "hz": float(config.HZ), **{k: _plain(v) for k, v in meta.items()}},
               path)
    load_checkpoint(path)
    return path


def _plain(value):
    """Giá trị ``meta`` ở kiểu Python thuần, để ``weights_only`` nạp được."""
    if isinstance(value, str):
        return str(value)
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value)
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def load_checkpoint(path=None):
    """Nạp checkpoint, dựng lại mô hình ở chế độ ``eval``.

    Returns:
        ``(model, checkpoint dict)``.

    Raises:
        FileNotFoundError: chưa huấn luyện.
        ValueError: checkpoint lưu với danh sách lớp, ``T`` hoặc ``HZ`` khác
            ``config`` hiện tại.
    """
    path = Path(path or config.LSTM_MODEL_PATH)
    if not path.is_file():
        raise FileNotFoundError(
            f"Chưa có mô hình {path.name}. Chạy python scripts/train_lstm.py trước.")
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    expected = {"classes": list(config.CLASSES), "T": config.T, "hz": config.HZ}
    for key, value in expected.items():
        if checkpoint.get(key) != value:
            raise ValueError(f"{path.name} huấn luyện với {key} = {checkpoint.get(key)}, "
                             f"còn config hiện tại là {value} — huấn luyện lại.")
    model = LSTMClassifier(**checkpoint["hparams"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, checkpoint


@torch.no_grad()
def predict_proba(model, sequences, batch=config.LSTM_EVAL_BATCH):
    """Xác suất softmax cho cả một lô chuỗi.

    Args:
        sequences: ``(n, T, 42)`` từ ``datasets.window_sequences``.

    Returns:
        ``(n, n_classes)`` float32.
    """
    model.eval()
    sequences = np.ascontiguousarray(sequences, dtype=np.float32)
    out = [torch.softmax(model(torch.from_numpy(sequences[i:i + batch])), dim=1).numpy()
           for i in range(0, len(sequences), batch)]
    if not out:
        return np.empty((0, model.hparams["n_classes"]), dtype=np.float32)
    return np.concatenate(out)


class LSTMRunner:
    """LSTM dạng hàm ``cửa sổ đã chuẩn hoá → (label, confidence)`` cho ``demo.py``.

    ``input_kind = "window"`` báo cho ``LivePredictor`` đưa vào cửa sổ, không
    đưa vector đặc trưng. Nhãn là lớp có xác suất softmax cao nhất,
    ``confidence`` là xác suất đó. Nạp lười như ``forest.ForestClassifier``:
    tạo đối tượng không tốn gì; ``LivePredictor`` gọi :meth:`load` trước khi
    camera chạy.
    """

    input_kind = "window"

    def __init__(self, path=None):
        self.path = path
        self.model = None

    def load(self):
        if self.model is None:
            self.model, _ = load_checkpoint(self.path)
        return self

    def __call__(self, win_norm):
        self.load()
        proba = predict_proba(self.model, window_sequence(win_norm)[None])[0]
        k = int(np.argmax(proba))
        return k, float(proba[k])
