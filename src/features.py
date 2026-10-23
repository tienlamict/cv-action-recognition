"""Vector đặc trưng 15 chiều của một cửa sổ đã chuẩn hoá.

Năm đặc trưng **có dấu** — ``open_delta``, ``open_trend``, ``pinch_delta``,
``dx``, ``mean_vx`` — gánh phần lớn việc phân biệt hai cặp lớp (vuốt trái/phải,
zoom in/out). Bỏ chúng đi thì hai cặp này sập hoàn toàn; Phase 8 sẽ đo chính
xác điều đó.

``pinch_delta`` và ``pinch_range`` (khoảng cách đầu ngón cái – đầu ngón trỏ)
thêm ngày 2026-10-05, sau khi cổng boxplot Phase 4 không đạt: zoom của IPN là
chụm/mở ba đầu ngón cái, trỏ, giữa với nhẫn và út gập suốt, nên độ xòe trung
bình của cả năm ngón đổi rất ít. Đo trên train, ``pinch_delta`` tách hẳn hai
hộp zoom, ``open_delta`` thì không (``docs/gestures.md``).

File này KHÔNG suy ra hướng trái hay phải. Nó chỉ tính dấu của chuyển động
trong hệ toạ độ ảnh; việc dịch dấu đó thành nhãn là của ``rules.py`` ở Phase 3,
và phải đi qua ``SWIPE_LEFT_SIGN``.

Mọi hàm ở đây nhận cửa sổ có thể còn NaN (bước mất tay mà ``fill_short_gaps``
không vá). Vector trả về **không bao giờ** chứa NaN hay inf: đặc trưng không
tính được thì bằng 0, và cột ``presence`` cho biết cửa sổ có bao nhiêu dữ liệu
thật.
"""

import warnings

import numpy as np

from src import config

FEATURE_NAMES = [
    "open_start", "open_end", "open_delta", "open_range", "open_trend",
    "pinch_delta", "pinch_range",
    "dx", "dy", "max_vx", "mean_vx", "max_vy",
    "straightness", "horiz_ratio", "presence",
]

#: Đặc trưng góc khớp — KHÔNG thuộc vector 15 chiều. Chỉ Bảng 5 của Phase 8
#: (dòng "thêm góc khớp") nối chúng vào sau ``FEATURE_NAMES``.
ANGLE_NAMES = [f"angle_{stat}_{finger}" for stat in ("mean", "delta")
               for finger in config.ANGLE_JOINTS]


def openness(win):
    """Độ xòe của từng bước: ``(T,)``.

    Trung bình khoảng cách từ 5 đầu ngón tới cổ tay **của cùng frame đó** —
    không phải tới gốc toạ độ. Nhờ vậy độ xòe không đổi khi cả bàn tay dời đi,
    và đó chính là thứ phân biệt zoom với vuốt.
    """
    win = np.asarray(win, dtype=np.float64)
    wrist = win[:, config.WRIST][:, None, :]
    tips = win[:, config.TIPS]
    return _nanmean(np.linalg.norm(tips - wrist, axis=2), axis=1)


def pinch(win):
    """Độ mở cái–trỏ của từng bước: ``(T,)`` — khoảng cách đầu ngón cái tới
    đầu ngón trỏ. Không đổi khi cả bàn tay dời đi, như :func:`openness`."""
    win = np.asarray(win, dtype=np.float64)
    return np.linalg.norm(win[:, config.THUMB_TIP] - win[:, config.INDEX_TIP],
                          axis=1)


def window_features(win_norm, presence_ratio):
    """Vector 15 chiều theo đúng thứ tự ``FEATURE_NAMES``.

    Args:
        win_norm: ``(T, 21, 2)`` cửa sổ **đã chuẩn hoá** bằng
            ``preprocess.normalize_window``.
        presence_ratio: tỉ lệ bước có tay của cửa sổ, trong ``[0, 1]``.

    Returns:
        ``np.float32`` shape ``(15,)``, không có NaN và không có inf.
    """
    win_norm = np.asarray(win_norm, dtype=np.float64)
    o = openness(win_norm)
    p = pinch(win_norm)
    wrist = win_norm[:, config.WRIST]

    open_start, open_end = _edge_mean(o), _edge_mean(o, tail=True)
    head, tail = _edge_mean(wrist), _edge_mean(wrist, tail=True)
    displacement = tail - head

    velocity = np.diff(wrist, axis=0) * config.HZ

    values = [
        open_start,
        open_end,
        open_end - open_start,
        _nanmax(o) - _nanmin(o),
        _slope(o),
        _edge_mean(p, tail=True) - _edge_mean(p),
        _nanmax(p) - _nanmin(p),
        displacement[0],
        displacement[1],
        _nanmax(np.abs(velocity[:, 0])),
        _nanmean(velocity[:, 0]),
        _nanmax(np.abs(velocity[:, 1])),
        _straightness(wrist, displacement),
        abs(displacement[0]) / (abs(displacement[0]) + abs(displacement[1])
                                + config.FEATURE_EPS),
        presence_ratio,
    ]

    features = np.array([_finite(v) for v in values], dtype=np.float32)
    assert features.size == len(FEATURE_NAMES)
    return features


def joint_angles(win):
    """Góc gập ở khớp giữa của năm ngón, từng bước: ``(T, 5)`` radian, theo
    thứ tự ``ANGLE_JOINTS``. ``π`` là ngón duỗi thẳng, càng nhỏ càng gập.

    Góc tại đỉnh ``b`` giữa hai đoạn ``b→a`` và ``b→c``. Tự nó bất biến với
    tịnh tiến, tỉ lệ và xoay trong mặt phẳng ảnh. Hai chỗ chặn lỗi im lặng
    (cẩm nang mục 9.c): ``cos`` kẹp vào ``[-1, 1]`` trước ``arccos``, và đoạn
    xương dài không quá ``NORM_MIN_SCALE`` cho góc NaN thay vì chia cho 0.
    """
    win = np.asarray(win, dtype=np.float64)
    out = []
    for a, b, c in config.ANGLE_JOINTS.values():
        u, v = win[:, a] - win[:, b], win[:, c] - win[:, b]
        lu, lv = np.linalg.norm(u, axis=1), np.linalg.norm(v, axis=1)
        ok = (lu > config.NORM_MIN_SCALE) & (lv > config.NORM_MIN_SCALE)
        cos = np.full(win.shape[0], np.nan)
        cos[ok] = np.sum(u[ok] * v[ok], axis=1) / (lu[ok] * lv[ok])
        out.append(np.arccos(np.clip(cos, -1.0, 1.0)))
    return np.stack(out, axis=1)


def angle_features(win_norm):
    """Mười đặc trưng góc khớp của một cửa sổ, theo thứ tự ``ANGLE_NAMES``:
    góc trung bình của từng ngón (ngón đang duỗi hay co), rồi góc cuối − đầu
    (ngón đang duỗi ra hay co lại). Không bao giờ NaN.

    Chỉ dùng ở Bảng 5 của Phase 8. Bộ 15 đặc trưng không đo cấu hình ngón, nên
    không tách được tay chỉ trỏ (ngón trỏ duỗi, các ngón kia co) với cú hất mở
    cả bàn tay (``results/phase6/notes.md`` mục 4.1, giả thuyết A).
    """
    angles = joint_angles(win_norm)
    means = [_nanmean(angles[:, j]) for j in range(angles.shape[1])]
    deltas = [_edge_mean(angles[:, j], tail=True) - _edge_mean(angles[:, j])
              for j in range(angles.shape[1])]
    return np.array([_finite(v) for v in means + deltas], dtype=np.float32)


def _edge_mean(values, tail=False):
    """Trung bình ``FEATURE_EDGE_STEPS`` bước đầu (hoặc cuối) theo trục thời gian.

    Nhận cả chuỗi vô hướng ``(T,)`` lẫn chuỗi điểm ``(T, D)``.
    """
    k = config.FEATURE_EDGE_STEPS
    edge = values[-k:] if tail else values[:k]
    return _nanmean(edge, axis=0)


def _straightness(wrist, displacement):
    """Độ thẳng của quỹ đạo cổ tay trong ``[0, 1]``.

    Bằng độ dời thẳng chia cho tổng độ dài đường đi. Vuốt là một đường gần
    thẳng nên gần 1; vẫy tay qua lại đi rất xa mà dời rất ít nên gần 0. Các
    đoạn chạm bước NaN bị bỏ khỏi tổng độ dài.
    """
    steps = np.linalg.norm(np.diff(wrist, axis=0), axis=1)
    path = float(np.nansum(steps))
    if path < config.FEATURE_EPS:
        return 0.0
    return float(np.clip(np.linalg.norm(displacement) / path, 0.0, 1.0))


def _slope(values):
    """Hệ số góc hồi quy tuyến tính của ``values`` theo GIÂY (bỏ qua NaN)."""
    values = np.asarray(values, dtype=np.float64)
    seconds = np.arange(values.size, dtype=np.float64) / config.HZ
    ok = np.isfinite(values)
    if ok.sum() < 2:
        return 0.0
    return float(np.polyfit(seconds[ok], values[ok], 1)[0])


def _nanmean(values, axis=None):
    return _reduce(np.nanmean, values, axis)


def _nanmax(values, axis=None):
    return _reduce(np.nanmax, values, axis)


def _nanmin(values, axis=None):
    return _reduce(np.nanmin, values, axis)


def _reduce(function, values, axis):
    """Gọi hàm nan-aware mà không để lát toàn NaN sinh cảnh báo."""
    values = np.asarray(values, dtype=np.float64)
    ok = np.isfinite(values)
    if not ok.any():
        return np.nan if axis is None else np.full(
            np.delete(values.shape, axis), np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return function(values, axis=axis)


def _finite(value):
    """Giá trị hữu hạn, hoặc 0.0 nếu không tính được."""
    value = float(value)
    return value if np.isfinite(value) else 0.0
