"""Bộ dữ liệu cho LSTM (Phase 7): mỗi cửa sổ thành một chuỗi ``(T, 42)``.

Đường đi của một cửa sổ, đúng thứ tự của luật 5::

    windows.npz (đã chuẩn hoá) → [augment.augment — chỉ train, MỚI mỗi epoch]
    → window_sequence → tensor (T, 42)

:func:`window_sequence` là cửa DUY NHẤT vào LSTM, cho cả dữ liệu IPN lẫn webcam
lúc chạy thật (luật 1): ``models.LSTMRunner`` của demo gọi đúng hàm này.

**Bước mất tay.** Cửa sổ hợp lệ vẫn có thể còn bước NaN — lỗ dài hơn
``MAX_GAP`` mà ``fill_short_gaps`` cố ý không vá; trên IPN đó là 5–8% số cửa sổ,
1–1,5% số bước. LSTM không nhận NaN, và đầu vào phải đúng 42 chiều nên không
thêm được kênh đánh dấu. Bước NaN lấy giá trị của bước có tay gần nhất TRƯỚC
nó:

- chỉ dùng quá khứ (luật 10);
- không bịa quỹ đạo giữa hai điểm — nội suy lỗ dài hơn ``MAX_GAP`` bị cấm;
- không tạo cú nhảy giả như điền 0: sau chuẩn hoá, 0 là vị trí cổ tay ở bước
  đầu, nên điền 0 làm bàn tay "nhảy" về đó rồi quay lại.

Bước đầu luôn có tay, vì ``normalize_window`` đòi điều đó.
"""

import numpy as np
import torch
from torch.utils.data import Dataset

from src import config
from src.augment import augment as augment_window


def window_sequence(win_norm):
    """Cửa sổ đã chuẩn hoá ``(T, 21, 2)`` → chuỗi ``(T, 42)`` float32 cho LSTM.

    Mỗi bước là 21 điểm ``(x, y)`` trải phẳng theo thứ tự điểm mốc —
    ``reshape``, không thêm hay bớt gì. Bước mất tay lấy bước có tay gần nhất
    trước nó.

    Raises:
        ValueError: shape sai, hoặc bước đầu không có tay.
    """
    win = np.asarray(win_norm, dtype=np.float32)
    if win.ndim != 3 or win.shape[1:] != (config.NUM_LANDMARKS, 2):
        raise ValueError(f"Cửa sổ phải có shape (T, {config.NUM_LANDMARKS}, 2), "
                         f"nhận {win.shape}")
    seq = win.reshape(win.shape[0], -1).copy()
    missing = ~np.isfinite(seq).all(axis=1)
    if missing[0]:
        raise ValueError("Bước đầu cửa sổ không có tay — cửa sổ này phải bị loại.")
    for t in np.flatnonzero(missing):
        seq[t] = seq[t - 1]
    return seq


def window_sequences(X):
    """:func:`window_sequence` cho cả một lô: ``(N, T, 21, 2)`` → ``(N, T, 42)``."""
    X = np.asarray(X)
    if len(X) == 0:
        return np.empty((0, X.shape[1] if X.ndim > 1 else config.T,
                         config.LSTM_INPUT_SIZE), dtype=np.float32)
    return np.stack([window_sequence(win) for win in X])


class WindowDataset(Dataset):
    """Cửa sổ của MỘT tập → ``(tensor (T, 42), nhãn)``.

    Có tăng cường thì mỗi lần lấy một mẫu là một bản tăng cường MỚI
    (``augment.augment``), nên mỗi epoch mô hình thấy một bản khác của cùng cửa
    sổ. Phép lật ngang đổi nhãn cặp vuốt, nên nhãn trả về là nhãn SAU tăng cường.

    Hiếm khi một bản tăng cường làm lòng bàn tay bước đầu ngắn bất thường so với
    cả cửa sổ và ``normalize_window`` từ chối nó; lúc đó trả về cửa sổ gốc, và
    đếm vào ``n_fallback`` để báo cáo.

    Args:
        X: ``(N, T, 21, 2)`` cửa sổ đã chuẩn hoá.
        y: ``(N,)`` chỉ số lớp.
        split: tên tập.
        augment: ``True`` để bật tăng cường — chỉ hợp lệ với ``"train"``.
        rng: ``np.random.Generator`` cho tăng cường; ``None`` thì seed ``SEED``.
        sigma: nhiễu của tăng cường; ``None`` thì đọc ``AUG_NOISE_SIGMA``.

    Raises:
        ValueError: bật tăng cường cho tập khác ``"train"`` (luật 9).
    """

    def __init__(self, X, y, split, augment=False, rng=None, sigma=None):
        if augment and split != "train":
            raise ValueError(
                f"Tăng cường chỉ cho tập train, không cho '{split}' (luật 9).")
        self.X = np.asarray(X, dtype=np.float32)
        self.y = np.asarray(y, dtype=np.int64)
        self.split = split
        self.augment = augment
        self.rng = rng if rng is not None else np.random.default_rng(config.SEED)
        self.sigma = sigma
        self.n_fallback = 0
        # không tăng cường thì chuỗi không bao giờ đổi: tính một lần
        self._fixed = None if augment else window_sequences(self.X)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        if self._fixed is not None:
            return torch.from_numpy(self._fixed[i]), int(self.y[i])
        try:
            win, label = augment_window(self.X[i], int(self.y[i]), self.rng,
                                        self.sigma)
        except ValueError:
            self.n_fallback += 1
            win, label = self.X[i], int(self.y[i])
        return torch.from_numpy(window_sequence(win)), int(label)
