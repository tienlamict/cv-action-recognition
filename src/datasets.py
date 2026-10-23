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
from src.augment import (ZOOM_LABELS, restyle_zoom, static_window,
                         usable_steps)
from src.augment import augment as augment_window
from src.preprocess import normalize_window


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


def window_sequences(X, sequence=None):
    """:func:`window_sequence` cho cả một lô: ``(N, T, 21, 2)`` → ``(N, T, 42)``.

    Args:
        sequence: hàm ``cửa sổ đã chuẩn hoá → chuỗi`` thay cho
            :func:`window_sequence` — chỉ các biến thể của bảng khảo sát Phase 8
            (``src/variants.py``) dùng.
    """
    X = np.asarray(X)
    if len(X) == 0 and sequence is None:
        return np.empty((0, X.shape[1] if X.ndim > 1 else config.T,
                         config.LSTM_INPUT_SIZE), dtype=np.float32)
    sequence = sequence or window_sequence
    return np.stack([sequence(win) for win in X])


class WindowDataset(Dataset):
    """Cửa sổ của MỘT tập → ``(tensor (T, 42), nhãn)``.

    Có tăng cường thì mỗi lần lấy một mẫu là một bản tăng cường MỚI
    (``augment.augment``), nên mỗi epoch mô hình thấy một bản khác của cùng cửa
    sổ. Phép lật ngang đổi nhãn cặp vuốt, nên nhãn trả về là nhãn SAU tăng cường.
    Thêm hai phép riêng cho LSTM (thêm 2026-10-10):

    - cửa sổ zoom, với xác suất ``zoom_style_p``, mang dáng ngón phụ của một bàn
      tay IPN khác trong ``finger_pool``, đứng yên (``augment.restyle_zoom``);
    - ``static_share`` × N mẫu nữa là bàn tay ĐỨNG YÊN ở dáng một bước bất kỳ của
      một cửa sổ bất kỳ, nhãn ``none`` — rút mới mỗi lần lấy.

    Hiếm khi một bản tăng cường làm lòng bàn tay bước đầu ngắn bất thường so với
    cả cửa sổ và ``normalize_window`` từ chối nó; lúc đó bỏ phần tăng cường chung
    (vẫn giữ hai phép riêng ở trên), và đếm vào ``n_fallback`` để báo cáo.

    Args:
        X: ``(N, T, 21, 2)`` cửa sổ đã chuẩn hoá.
        y: ``(N,)`` chỉ số lớp.
        split: tên tập.
        augment: ``True`` để bật tăng cường — chỉ hợp lệ với ``"train"``.
        rng: ``np.random.Generator`` cho tăng cường; ``None`` thì seed ``SEED``.
        sigma: nhiễu của tăng cường; ``None`` thì đọc ``AUG_NOISE_SIGMA``.
        finger_pool: kho dáng ngón phụ ``augment.finger_pose_pool``, dựng từ train.
        zoom_style_p, static_share: như trên; chỉ có tác dụng khi ``augment``.
        sequence: hàm ``cửa sổ đã chuẩn hoá → chuỗi``; ``None`` là
            :func:`window_sequence`. Biến thể của bảng khảo sát Phase 8 chạy SAU
            tăng cường, đúng thứ tự của luật 5.

    Raises:
        ValueError: bật tăng cường cho tập khác ``"train"`` (luật 9); đổi dáng
            ngón phụ mà không có ``finger_pool``.
    """

    def __init__(self, X, y, split, augment=False, rng=None, sigma=None,
                 finger_pool=None, zoom_style_p=0.0, static_share=0.0,
                 sequence=None):
        if augment and split != "train":
            raise ValueError(
                f"Tăng cường chỉ cho tập train, không cho '{split}' (luật 9).")
        if augment and zoom_style_p > 0 and finger_pool is None:
            raise ValueError("Đổi dáng ngón phụ cần finger_pool dựng từ tập train.")
        self.X = np.asarray(X, dtype=np.float32)
        self.y = np.asarray(y, dtype=np.int64)
        self.split = split
        self.augment = augment
        self.rng = rng if rng is not None else np.random.default_rng(config.SEED)
        self.sigma = sigma
        self.finger_pool = finger_pool
        self.zoom_style_p = zoom_style_p if augment else 0.0
        self.n_static = int(round(static_share * len(self.y))) if augment else 0
        self.n_fallback = 0
        self.sequence = sequence or window_sequence
        # không tăng cường thì chuỗi không bao giờ đổi: tính một lần
        self._fixed = None if augment else window_sequences(self.X, sequence)

    def __len__(self):
        return len(self.y) + self.n_static

    @property
    def labels(self):
        """Nhãn của MỌI mẫu một epoch sẽ thấy, kể cả mẫu bàn tay đứng yên —
        để tính trọng số lớp đúng với thứ mô hình thật sự học."""
        return np.concatenate([self.y, np.zeros(self.n_static, dtype=np.int64)])

    def __getitem__(self, i):
        if self._fixed is not None:
            return torch.from_numpy(self._fixed[i]), int(self.y[i])
        # Tắt cả hai phép riêng (zoom_style_p = 0, static_share = 0) thì không
        # rút thêm số ngẫu nhiên nào và mọi phép tính như trước khi có chúng:
        # cho lại đúng từng con số của các lần huấn luyện cũ.
        if i < len(self.y):
            win, label = self.X[i], int(self.y[i])
            if (label in ZOOM_LABELS and self.zoom_style_p > 0
                    and self.rng.random() < self.zoom_style_p):
                win = restyle_zoom(win, self.rng, self.finger_pool)
        else:
            source = self.X[int(self.rng.integers(len(self.y)))]
            win = normalize_window(
                static_window(source, int(self.rng.choice(usable_steps(source)))))
            label = config.CLASSES.index("none")
        # win luôn đã chuẩn hoá: cửa sổ gốc, bản đổi dáng ngón phụ (cổ tay và
        # lòng bàn tay bước đầu giữ nguyên), hay bản đứng yên vừa chuẩn hoá
        try:
            win, label = augment_window(win, label, self.rng, self.sigma)
        except ValueError:
            self.n_fallback += 1
        return torch.from_numpy(self.sequence(win)), int(label)
