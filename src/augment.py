"""Tăng cường dữ liệu — Phase 4. Mỗi phép trả lời một câu hỏi: **biến đổi này
có làm đổi lớp không?**

| Phép | Tham số | Đổi nhãn? |
|---|---|---|
| Lật ngang | — | **Có** với cặp vuốt, **không** với cặp zoom |
| Co giãn đổi dần | 1 → 1 ± ``AUG_SCALE_RAMP`` | Không |
| Xoay nhẹ | ± ``AUG_ROTATE_DEG`` | Không |
| Co giãn thời gian | ``AUG_TIME_WARP`` | Không |
| Nhiễu Gauss | ``AUG_NOISE_SIGMA`` | Không |
| Xoá bước ngẫu nhiên | ``AUG_DROP_STEPS`` rồi ``fill_short_gaps`` | Không |

**Đầu vào là cửa sổ ĐÃ chuẩn hoá** (gốc tại cổ tay frame đầu, đơn vị lòng bàn
tay — đúng thứ ``windows.npz`` lưu), và **kết quả phải đi qua
``normalize_window`` lần nữa**. Luật 5 đặt tăng cường trước chuẩn hoá; cách làm
này tương đương vì ``normalize_window`` của một cửa sổ đã chuẩn hoá là phép đồng
nhất, và lật, xoay, co giãn thời gian, vá lỗ đều giao hoán với phép dời và
co giãn đều mà chuẩn hoá thực hiện. Nhiễu và co giãn đổi dần thì phải đo bằng
đơn vị lòng bàn tay — ``AUG_NOISE_SIGMA`` được ước lượng SAU chuẩn hoá.

**Co giãn đều bị bỏ:** nhân mọi điểm với cùng một hệ số rồi chuẩn hoá thì hệ số
đó bị chia mất. Thay bằng co giãn đổi dần dọc cửa sổ — mô phỏng tay tiến hoặc
lùi so với camera, thứ chuẩn hoá theo frame đầu không khử được.

Mọi phép không sửa mảng đầu vào và giữ bước đầu hữu hạn, để ``normalize_window``
luôn chạy được.
"""

import numpy as np

from src import config
from src.preprocess import fill_short_gaps, normalize_window

_SWAP = {"swipe_left": "swipe_right", "swipe_right": "swipe_left"}
#: Lớp sau khi lật ngang, theo chỉ số trong ``config.CLASSES``.
FLIP_LABEL = {i: config.CLASSES.index(_SWAP.get(name, name))
              for i, name in enumerate(config.CLASSES)}


def flip_horizontal(win, label):
    """Lật ngang quanh cổ tay frame đầu: ``x → -x``.

    Returns:
        ``(cửa sổ mới, nhãn mới)`` — cặp vuốt đổi nhãn cho nhau, zoom và
        ``none`` giữ nguyên. Không cần hoán đổi chỉ số điểm mốc: 21 điểm của
        một bàn tay không có cặp trái — phải.
    """
    out = np.array(win, dtype=np.float64, copy=True)
    out[..., 0] = -out[..., 0]
    return out, FLIP_LABEL[int(label)]


def rotate(win, degrees):
    """Xoay quanh cổ tay frame đầu một góc ``degrees`` trong mặt phẳng ảnh."""
    theta = np.deg2rad(degrees)
    c, s = np.cos(theta), np.sin(theta)
    matrix = np.array([[c, -s], [s, c]])
    return np.asarray(win, dtype=np.float64) @ matrix.T


def scale_ramp(win, end_scale):
    """Co giãn đổi dần: hệ số đi từ 1 ở bước đầu tới ``end_scale`` ở bước cuối,
    quanh cổ tay frame đầu."""
    win = np.asarray(win, dtype=np.float64)
    factors = np.linspace(1.0, end_scale, win.shape[0])
    return win * factors[:, None, None]


def time_warp(win, factor):
    """Co giãn thời gian, neo ở bước đầu.

    Bước ``i`` mới lấy nội suy tuyến tính tại bước cũ ``i * factor``.
    ``factor > 1``: cử chỉ nhanh hơn — phần vượt quá cuối cửa sổ giữ bằng bước
    cuối, vì cửa sổ không có dữ liệu sau nó. ``factor < 1``: chậm hơn — phần
    cuối của cửa sổ cũ bị cắt. Nội suy cạnh một bước NaN cho NaN: không bịa dữ
    liệu qua chỗ mất tay.
    """
    win = np.asarray(win, dtype=np.float64)
    n = win.shape[0]
    tau = np.minimum(np.arange(n) * factor, n - 1)
    left = np.floor(tau).astype(int)
    right = np.minimum(left + 1, n - 1)
    alpha = (tau - left)[:, None, None]
    return (1 - alpha) * win[left] + alpha * win[right]


def add_noise(win, sigma, rng):
    """Nhiễu Gauss độc lập trên mọi toạ độ, ``sigma`` theo đơn vị lòng bàn tay."""
    win = np.asarray(win, dtype=np.float64)
    return win + rng.normal(0.0, sigma, size=win.shape)


def drop_steps(win, start, length):
    """Xoá ``length`` bước liền nhau từ ``start`` rồi vá bằng ``fill_short_gaps``
    — mô phỏng MediaPipe mất tay vài frame."""
    out = np.array(win, dtype=np.float64, copy=True)
    out[start:start + length] = np.nan
    return fill_short_gaps(out)


def augment(win, label, rng, sigma=None):
    """Một bản tăng cường ngẫu nhiên của một cửa sổ đã chuẩn hoá.

    Args:
        win: ``(T, 21, 2)`` cửa sổ đã chuẩn hoá.
        label: chỉ số lớp.
        rng: ``np.random.Generator``.
        sigma: độ lệch chuẩn của nhiễu; ``None`` thì đọc
            ``AUG_NOISE_SIGMA`` qua ``require_measured``.

    Returns:
        ``(cửa sổ, nhãn)`` — cửa sổ ĐÃ chuẩn hoá lại.
    """
    if sigma is None:
        sigma = config.require_measured("AUG_NOISE_SIGMA")

    out = np.asarray(win, dtype=np.float64)
    if rng.random() < config.AUG_FLIP_P:
        out, label = flip_horizontal(out, label)
    out = rotate(out, rng.uniform(-config.AUG_ROTATE_DEG, config.AUG_ROTATE_DEG))
    out = scale_ramp(out, 1.0 + rng.uniform(-config.AUG_SCALE_RAMP,
                                            config.AUG_SCALE_RAMP))
    out = time_warp(out, rng.uniform(*config.AUG_TIME_WARP))
    out = add_noise(out, sigma, rng)
    if rng.random() < config.AUG_DROP_P:
        lo, hi = config.AUG_DROP_STEPS
        length = int(rng.integers(lo, hi + 1))
        # tránh bước đầu (gốc toạ độ) và bước cuối (fill_short_gaps không vá
        # được lỗ chạm mép)
        start = int(rng.integers(1, out.shape[0] - length))
        out = drop_steps(out, start, length)
    return normalize_window(out), label


def augment_windows(X, y, split, rng, sigma=None):
    """Tăng cường cả một lô — CHỈ cho tập train (luật 9).

    Raises:
        ValueError: ``split`` không phải ``"train"``. Tăng cường val hay test
            là làm sai con số đánh giá, nên chặn ngay ở đây.

    Returns:
        ``(X_aug float32, y_aug int64)`` — mảng MỚI, ``X`` và ``y`` không đổi.
    """
    if split != "train":
        raise ValueError(
            f"Tăng cường chỉ cho tập train, không cho '{split}' (luật 9).")
    pairs = [augment(win, label, rng, sigma) for win, label in zip(X, y)]
    X_aug = np.stack([p[0] for p in pairs]).astype(np.float32)
    y_aug = np.array([p[1] for p in pairs], dtype=np.int64)
    return X_aug, y_aug
