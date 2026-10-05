"""Cắt cửa sổ trượt và gán nhãn cho từng cửa sổ — Phase 4.

Vị trí trong đường ống (luật 5)::

    load_sequence (to_pixels → resample → fill_short_gaps) → cut_windows
    → [tăng cường] → normalize_window

Ba quyết định về cách cắt:

1. **Cắt trong phạm vi từng clip.** Mỗi lần gọi :func:`cut_windows` chỉ nhận
   một clip, nên không cửa sổ nào bắc cầu qua hai video.
2. **Cửa sổ tính bằng giây.** ``T`` và ``STRIDE`` là số bước trên lưới
   ``HZ``, suy từ ``WIN_SEC`` và ``STRIDE_SEC`` trong ``config``.
3. **Cửa sổ trả về ở toạ độ PIXEL, chưa chuẩn hoá.** Tăng cường phải đứng
   trước ``normalize_window``; chuẩn hoá là việc của người gọi.

Cửa sổ bị loại khi tỉ lệ bước có tay dưới ``MIN_PRESENCE`` hoặc bước đầu không
có tay — bước đầu là gốc toạ độ và đơn vị của ``normalize_window``.

**Gán nhãn: neo vào khoảnh khắc chính** (quyết định 2026-10-05, thay luật "lớp
đích chiếm >= 60% số bước" của SPEC). Đoạn cử chỉ của IPN dài ~2 s gồm chuẩn
bị, động tác chính ~0,3 s, và thu tay. Với luật cũ, 49% cửa sổ dương không chứa
động tác chính, và cổng boxplot không đạt. Luật mới, với mỗi đoạn cử chỉ đích:

- **khoảnh khắc chính** là bước có tín hiệu đổi nhanh nhất trong đoạn (đã làm
  mượt ``CORE_SMOOTH_STEPS`` bước): vị trí ngang của cổ tay với hai lớp vuốt,
  độ mở cái–trỏ với hai lớp zoom, chia cho trung vị lòng bàn tay của đoạn;
- cửa sổ mang lớp của đoạn khi khoảnh khắc chính nằm trong
  ``[CORE_MARGIN_STEPS, T - CORE_MARGIN_STEPS)`` của nó;
- cửa sổ **giao** với một đoạn cử chỉ đích mà không thoả điều trên thì **bị
  bỏ**, không gán ``none`` — nó chứa một phần cử chỉ, gán ``none`` là dạy sai;
- cửa sổ không giao đoạn cử chỉ đích nào là ``none``.

Khoảnh khắc chính dùng cả đoạn, kể cả phần sau cửa sổ. Điều này không phạm
luật 10: nhãn là chân lý ngoại tuyến như chính file nhãn của IPN, mô hình
không bao giờ thấy nó. Nhãn phụ thuộc tín hiệu chuyển động, nên phải nói rõ
trong báo cáo; dấu của chuyển động thì không được dùng để gán nhãn.
"""

import numpy as np

from src import config
from src.io_data import load_clip
from src.preprocess import load_sequence


def step_labels(ts, segments, src_labels, grid_ts):
    """Nhãn của từng bước trên lưới thời gian đều.

    Bước tại thời điểm ``g`` mang nhãn của frame cuối cùng có ``ts <= g``.

    Args:
        ts: ``(N,)`` giây của từng frame.
        segments: ``(K, 3)`` ``[start, end, class_id]`` theo chỉ số frame.
        src_labels: ``(K,)`` nhãn gốc của từng đoạn.
        grid_ts: ``(M,)`` thời điểm của các bước, từ ``load_sequence``.

    Returns:
        ``(class_id (M,) int64, segment (M,) int64)`` — ``segment`` là chỉ số
        đoạn trong ``segments``, ``-1`` nếu frame không thuộc đoạn nào (khi đó
        lớp là ``none``).
    """
    ts = np.asarray(ts, dtype=np.float64)
    row_segment = np.full(ts.size, -1, dtype=np.int64)
    for k, (start, end, _) in enumerate(np.asarray(segments).reshape(-1, 3)):
        row_segment[start:end] = k

    rows = np.clip(np.searchsorted(ts, grid_ts, side="right") - 1, 0,
                   ts.size - 1)
    segment = row_segment[rows]
    classes = np.asarray(segments).reshape(-1, 3)[:, 2]
    class_id = np.where(segment >= 0, classes[np.maximum(segment, 0)], 0)
    return class_id.astype(np.int64), segment


def core_steps(xy, segment, segments):
    """Khoảnh khắc chính của từng đoạn cử chỉ đích.

    Args:
        xy: ``(M, 21, 2)`` pixel trên lưới, từ ``load_sequence``.
        segment: ``(M,)`` chỉ số đoạn của từng bước, từ :func:`step_labels`.
        segments: ``(K, 3)`` ``[start, end, class_id]``.

    Returns:
        dict ``{chỉ số đoạn: bước}``. Đoạn không đo được (mất tay cả đoạn)
        không có mặt — mọi cửa sổ giao với nó sẽ bị bỏ.
    """
    palm = np.linalg.norm(xy[:, config.MIDDLE_MCP] - xy[:, config.WRIST], axis=1)
    pinch_px = np.linalg.norm(xy[:, config.THUMB_TIP] - xy[:, config.INDEX_TIP],
                              axis=1)
    kernel = np.ones(config.CORE_SMOOTH_STEPS) / config.CORE_SMOOTH_STEPS

    cores = {}
    for k, (_, _, class_id) in enumerate(np.asarray(segments).reshape(-1, 3)):
        name = config.CLASSES[class_id]
        steps = np.flatnonzero(segment == k)
        if name == "none" or steps.size == 0:
            continue
        unit = np.nanmedian(palm[steps]) if np.isfinite(palm[steps]).any() else np.nan
        if not np.isfinite(unit) or unit <= 0:
            continue
        signal = (xy[steps, config.WRIST, 0] if name.startswith("swipe")
                  else pinch_px[steps])
        change = np.abs(np.diff(signal, prepend=signal[0])) / unit
        change = np.convolve(np.where(np.isfinite(change), change, 0.0),
                             kernel, mode="same")
        cores[k] = int(steps[int(np.argmax(change))])
    return cores


def cut_windows(ts, xy_norm, w, h, segments, src_labels):
    """Cắt mọi cửa sổ hợp lệ của MỘT clip và gán nhãn.

    Returns:
        ``(windows, stats)``. ``windows`` là dict các mảng, mỗi cửa sổ một dòng:

        - ``X`` float32 ``(n, T, 21, 2)`` — PIXEL, chưa chuẩn hoá
        - ``y`` int64 ``(n,)``
        - ``presence`` float32 ``(n,)`` — tỉ lệ bước có tay
        - ``t0`` float32 ``(n,)`` — giây, thời điểm bước đầu trong clip
        - ``src_label`` ``<U32`` ``(n,)`` — với cửa sổ dương: nhãn gốc của đoạn
          cử chỉ; với ``none``: của đoạn chiếm nhiều bước nhất

        ``stats`` đếm ``low_presence`` (bị loại vì thiếu tay) và ``ambiguous``
        (giao cử chỉ đích nhưng không chứa khoảnh khắc chính — bị bỏ).
    """
    segments = np.asarray(segments).reshape(-1, 3)
    src_labels = np.asarray(src_labels)
    grid_ts, xy = load_sequence(ts, xy_norm, w, h)
    _, segment = step_labels(ts, segments, src_labels, grid_ts)
    finite = np.all(np.isfinite(xy.reshape(xy.shape[0], -1)), axis=1)
    cores = core_steps(xy, segment, segments)
    is_target = segments[:, 2] != 0
    in_target = (segment >= 0) & is_target[np.maximum(segment, 0)]

    margin = config.CORE_MARGIN_STEPS
    rows = {key: [] for key in ("X", "y", "presence", "t0", "src_label")}
    stats = {"low_presence": 0, "ambiguous": 0}
    for start in range(0, xy.shape[0] - config.T + 1, config.STRIDE):
        stop = start + config.T
        presence = finite[start:stop].mean()
        if presence < config.MIN_PRESENCE or not finite[start]:
            stats["low_presence"] += 1
            continue

        center = start + config.T / 2
        inside = [k for k, step in cores.items()
                  if start + margin <= step < stop - margin]
        if inside:
            k = min(inside, key=lambda k: abs(cores[k] - center))
            y, src = int(segments[k, 2]), src_labels[k]
        elif in_target[start:stop].any():
            stats["ambiguous"] += 1
            continue
        else:
            own = segment[start:stop]
            own = own[own >= 0]
            y = 0
            src = src_labels[np.bincount(own).argmax()] if own.size else ""

        rows["X"].append(xy[start:stop])
        rows["y"].append(y)
        rows["presence"].append(presence)
        rows["t0"].append(grid_ts[start])
        rows["src_label"].append(src)

    windows = {
        "X": np.asarray(rows["X"], dtype=np.float32).reshape(
            -1, config.T, config.NUM_LANDMARKS, 2),
        "y": np.asarray(rows["y"], dtype=np.int64),
        "presence": np.asarray(rows["presence"], dtype=np.float32),
        "t0": np.asarray(rows["t0"], dtype=np.float32),
        "src_label": np.asarray(rows["src_label"], dtype="<U32"),
    }
    return windows, stats


def windows_from_clip(path):
    """:func:`cut_windows` cho một ``.npz``, kèm ``subject`` và ``clip``.

    Returns:
        ``(windows, meta, stats)`` — ``windows`` như :func:`cut_windows` cộng
        hai cột ``subject``, ``clip``; ``meta`` là ``meta`` của clip.
    """
    ts, xy_norm, w, h, segments, src_labels, meta = load_clip(path)
    windows, stats = cut_windows(ts, xy_norm, w, h, segments, src_labels)
    n = windows["y"].size
    windows["subject"] = np.full(n, meta["subject"], dtype="<U16")
    windows["clip"] = np.full(n, meta["clip_id"], dtype="<U64")
    return windows, meta, stats
