"""Đường ống biểu diễn: pixel → lưới thời gian đều → vá lỗ ngắn → chuẩn hoá.

Thứ tự CỐ ĐỊNH, đổi chỗ bất kỳ bước nào cũng làm biểu diễn khác đi mà không có
gì báo lỗi::

    to_pixels → resample(15 Hz) → fill_short_gaps → cắt cửa sổ → [tăng cường]
    → normalize_window → đặc trưng hoặc LSTM

Ba bước đầu gói trong :func:`load_sequence` — cửa duy nhất để dữ liệu vào
đường ống. Ngoài ``tests/``, không nơi nào được gọi :func:`resample` hay
:func:`fill_short_gaps` trực tiếp — trừ phép "xoá bước rồi vá" của
``src/augment.py``, mà SPEC Phase 4 yêu cầu đích danh.

Hai quyết định của file này quyết định chất lượng mọi phase sau:

1. **Không nội suy xuyên qua khoảng mất tay.** ``np.interp`` sẽ vui vẻ nối một
   đường thẳng qua chỗ không có dữ liệu và không báo gì. Chuyển động bịa ra đó
   trông y như chuyển động thật ở mọi bước sau.
2. **Gốc toạ độ và đơn vị lấy từ FRAME ĐẦU cửa sổ**, dùng chung cho mọi frame.
   Trừ cổ tay của từng frame sẽ xoá sạch quỹ đạo — và hai lớp vuốt biến mất.
"""

import numpy as np

from src import config


def to_pixels(xy_norm, w, h):
    """Toạ độ chuẩn hoá ``[0, 1]`` → pixel.

    Hai trục nhân hai hệ số khác nhau: một đơn vị ``x`` dài ``w`` pixel còn một
    đơn vị ``y`` dài ``h`` pixel. Dùng chung một hệ số sẽ làm méo mọi khoảng
    cách và góc khi ảnh không vuông.
    """
    xy_norm = np.asarray(xy_norm, dtype=np.float64)
    return xy_norm * np.array([w, h], dtype=np.float64)


def _frame_present(xy):
    """``(N,)`` bool — frame có đủ toạ độ hữu hạn hay không."""
    xy = np.asarray(xy, dtype=np.float64)
    return np.all(np.isfinite(xy.reshape(xy.shape[0], -1)), axis=1)


def resample(ts, xy, hz=config.HZ):
    """Đưa chuỗi về lưới thời gian đều ``hz``.

    Lưới bắt đầu đúng tại ``ts[0]``, bước đúng ``1/hz``, không vượt quá
    ``ts[-1]``. Nội suy tuyến tính từng toạ độ, CHỈ từ các frame có tay.

    Một điểm lưới là NaN nếu hai frame kẹp nó không cùng có tay — nhờ vậy
    khoảng mất tay vẫn là khoảng trống, thay vì bị nối bằng một đoạn thẳng bịa
    ra.

    Args:
        ts: ``(N,)`` giây, tăng dần.
        xy: ``(N, 21, 2)`` pixel, NaN ở frame mất tay.

    Returns:
        ``(grid_ts, xy_grid)`` với ``xy_grid`` ``(M, 21, 2)``.
    """
    ts = np.asarray(ts, dtype=np.float64)
    xy = np.asarray(xy, dtype=np.float64)
    if ts.size == 0:
        return ts.copy(), xy.reshape(0, *xy.shape[1:]).copy()

    n_steps = int(np.floor((ts[-1] - ts[0]) * hz)) + 1
    grid_ts = ts[0] + np.arange(n_steps, dtype=np.float64) / hz

    present = _frame_present(xy)
    xy_grid = np.full((n_steps, *xy.shape[1:]), np.nan)
    if present.sum() >= 2:
        ts_ok = ts[present]
        flat = xy[present].reshape(present.sum(), -1)
        interpolated = np.stack(
            [np.interp(grid_ts, ts_ok, column) for column in flat.T], axis=1
        )
        xy_grid = interpolated.reshape(n_steps, *xy.shape[1:])

    xy_grid[~_bracketed_by_present(ts, present, grid_ts)] = np.nan
    return grid_ts, xy_grid


def _bracketed_by_present(ts, present, grid_ts):
    """``(M,)`` bool — điểm lưới có được kẹp giữa hai frame CÙNG có tay không.

    Điểm lưới rơi đúng vào một frame gốc thì chỉ cần frame đó có tay.
    """
    left = np.clip(np.searchsorted(ts, grid_ts, side="right") - 1,
                   0, ts.size - 1)
    right = np.clip(left + 1, 0, ts.size - 1)
    exact = ts[left] == grid_ts
    return np.where(exact, present[left], present[left] & present[right])


def fill_short_gaps(xy, max_gap=config.MAX_GAP):
    """Vá các đoạn NaN NGẮN, giữ nguyên các đoạn dài.

    Một đoạn được vá khi dài không quá ``max_gap`` bước **và** có đủ hai đầu
    mút hữu hạn để nội suy. Đoạn dài hơn, hoặc đoạn chạm đầu/cuối chuỗi, giữ
    NaN: mất tay lâu là một tín hiệu thật, không phải dữ liệu để bịa.

    Không sửa mảng đầu vào tại chỗ.
    """
    xy = np.array(xy, dtype=np.float64, copy=True)
    if xy.shape[0] == 0:
        return xy

    flat = xy.reshape(xy.shape[0], -1)
    steps = np.arange(flat.shape[0], dtype=np.float64)

    for column in flat.T:
        missing = ~np.isfinite(column)
        if not missing.any() or missing.all():
            continue
        for start, stop in _nan_runs(missing):
            touches_edge = start == 0 or stop == flat.shape[0]
            if touches_edge or (stop - start) > max_gap:
                continue
            column[start:stop] = np.interp(
                steps[start:stop], [steps[start - 1], steps[stop]],
                [column[start - 1], column[stop]],
            )

    return flat.reshape(xy.shape)


def _nan_runs(missing):
    """Các đoạn ``True`` liên tiếp, trả về ``(start, stop)`` nửa mở."""
    padded = np.concatenate(([False], missing, [False]))
    edges = np.diff(padded.astype(np.int8))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def load_sequence(ts, xy_norm, w, h, fill=True):
    """Cửa DUY NHẤT để dữ liệu vào đường ống.

    Gọi :func:`to_pixels` → :func:`resample` → :func:`fill_short_gaps`, đúng
    thứ tự đó. Mọi nguồn — CSV webcam, video IPN, video tự quay — đều đi qua
    đây, nên cả ba nhận đúng cùng một cách xử lý.

    Args:
        fill: đặt ``False`` để lấy chuỗi TRƯỚC khi vá lỗ hổng. Chỉ dùng cho
            chẩn đoán (``scripts/check_pipeline.py`` so tỉ lệ NaN trước và sau
            vá); đường ống xử lý luôn để mặc định ``True``.

    Returns:
        ``(grid_ts, xy)`` với ``xy`` ``(M, 21, 2)`` pixel trên lưới đều.
    """
    grid_ts, xy = resample(ts, to_pixels(xy_norm, w, h))
    return grid_ts, (fill_short_gaps(xy) if fill else xy)


def normalize_window(win):
    """Chuẩn hoá một cửa sổ ``(T, 21, 2)`` pixel về gốc và đơn vị của FRAME ĐẦU.

    - Gốc toạ độ: cổ tay của frame đầu cửa sổ.
    - Đơn vị: khoảng cách cổ tay → gốc ngón giữa (điểm 0 → 9) của frame đầu.

    Cả hai lấy MỘT lần và dùng chung cho mọi frame trong cửa sổ. Nhờ vậy kết
    quả bất biến với việc bàn tay ở đâu trong khung và cách camera bao xa,
    nhưng vẫn **giữ nguyên quỹ đạo** — thứ phân biệt vuốt trái với vuốt phải.

    NaN ở các frame khác được giữ nguyên.

    Đơn vị lấy từ một frame duy nhất nên dễ hỏng: khi tay nghiêng cạnh về phía
    camera, hoặc điểm mốc frame đầu sai, lòng bàn tay frame đầu ngắn bất thường
    và mọi toạ độ bị phóng to theo — trên IPN có cửa sổ ra độ xòe 30 lòng bàn
    tay. Vì vậy so với trung vị lòng bàn tay của CẢ cửa sổ. Cửa sổ chỉ chứa quá
    khứ của thời điểm quyết định, nên phép so này vẫn nhân quả.

    Raises:
        ValueError: frame đầu có NaN; cỡ lòng bàn tay nhỏ hơn
            ``NORM_MIN_SCALE``; hoặc nhỏ hơn ``NORM_MIN_PALM_RATIO`` lần trung
            vị lòng bàn tay của cửa sổ (đơn vị không tin được).
    """
    win = np.asarray(win, dtype=np.float64)
    first = win[0]
    if not np.all(np.isfinite(first)):
        raise ValueError(
            "Frame đầu cửa sổ không có tay — không xác định được gốc toạ độ và "
            "đơn vị. Cửa sổ này phải bị loại, không được chuẩn hoá."
        )

    origin = first[config.WRIST]
    scale = float(np.linalg.norm(first[config.MIDDLE_MCP] - origin))
    if scale < config.NORM_MIN_SCALE:
        raise ValueError(
            f"Cỡ lòng bàn tay ở frame đầu quá nhỏ ({scale:.3g} px) — không "
            "dùng làm đơn vị được."
        )

    palms = np.linalg.norm(win[:, config.MIDDLE_MCP] - win[:, config.WRIST],
                           axis=-1)
    typical = float(np.nanmedian(palms))
    if scale < config.NORM_MIN_PALM_RATIO * typical:
        raise ValueError(
            f"Lòng bàn tay frame đầu ({scale:.3g}) ngắn bất thường so với trung "
            f"vị của cửa sổ ({typical:.3g}) — đơn vị không tin được."
        )

    return (win - origin) / scale
