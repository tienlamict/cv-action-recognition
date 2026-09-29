"""Ghi và đọc điểm mốc từng frame ra CSV.

Mỗi frame là MỘT dòng, kể cả frame không thấy tay: dòng đó vẫn có ``ts``,
``present=0`` và các cột toạ độ để trống. Bỏ frame sẽ làm đứt trục thời gian,
còn một dòng trống giữ được thông tin "ở thời điểm này không có tay".

Toạ độ ghi ra là toạ độ chuẩn hoá của MediaPipe (``[0, 1]``) kèm ``w``, ``h``
của frame. Đổi sang pixel là việc của bước đầu tiên trong đường ống
(``to_pixels``, Phase 2), không làm ở đây.

Cột: ``ts, present, score, w, h, x0..x20, y0..y20``.
"""

import csv
from collections import namedtuple
from pathlib import Path

import cv2
import numpy as np

from src import config
from src.display import make_display, quit_pressed
from src.fps import FpsMeter
from src.hands import seconds_to_ms

X_COLUMNS = [f"x{i}" for i in range(config.NUM_LANDMARKS)]
Y_COLUMNS = [f"y{i}" for i in range(config.NUM_LANDMARKS)]
CSV_COLUMNS = ["ts", "present", "score", "w", "h",
               *X_COLUMNS, *Y_COLUMNS]

TrackedFrame = namedtuple(
    "TrackedFrame", "frame_bgr ts xy_norm present score"
)


def track(frames, tracker):
    """Chạy ``tracker`` trên mọi frame của ``frames`` — KHÔNG bỏ frame nào.

    Args:
        frames: iterable sinh ``(frame_bgr, ts_sec)``, thường là
            ``io_video.iter_frames``.
        tracker: đối tượng có ``process(frame_bgr, ts_ms)`` như ``HandTracker``.

    Yields:
        ``TrackedFrame`` cho từng frame, kể cả frame không thấy tay.
    """
    for frame_bgr, ts in frames:
        xy_norm, present, score = tracker.process(frame_bgr,
                                                  seconds_to_ms(ts))
        yield TrackedFrame(frame_bgr, ts, xy_norm, present, score)


class FrameCsvWriter:
    """Ghi mỗi frame một dòng CSV theo ``CSV_COLUMNS``."""

    def __init__(self, path):
        self.path = Path(path)
        self.n_rows = 0
        self.n_present = 0
        self._fmt = f"{{:.{config.CSV_FLOAT_DECIMALS}f}}"
        self._file = open(self.path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(CSV_COLUMNS)

    def write(self, ts, present, score, w, h, xy_norm):
        if present:
            coords = [self._fmt.format(v) for v in xy_norm[:, 0]]
            coords += [self._fmt.format(v) for v in xy_norm[:, 1]]
            score_text = self._fmt.format(score) if np.isfinite(score) else ""
            self.n_present += 1
        else:
            coords = [""] * (2 * config.NUM_LANDMARKS)
            score_text = ""

        self._writer.writerow([
            self._fmt.format(ts), int(bool(present)), score_text,
            int(w), int(h), *coords,
        ])
        self.n_rows += 1

    def write_tracked(self, tracked):
        h, w = tracked.frame_bgr.shape[:2]
        self.write(tracked.ts, tracked.present, tracked.score, w, h,
                   tracked.xy_norm)

    def close(self):
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def read_frames_csv(path):
    """Đọc lại một CSV do ``FrameCsvWriter`` ghi.

    Returns:
        dict với các mảng dài ``N`` (số dòng = số frame):

        - ``ts`` float64, ``present`` bool, ``score`` float64 (NaN khi mất tay)
        - ``w``, ``h`` int64 — kích thước khung hình
        - ``xy`` float32 ``(N, 21, 2)``, toạ độ chuẩn hoá, NaN khi mất tay
    """
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    def floats(column):
        return np.array([float(r[column]) if r[column] != "" else np.nan
                         for r in rows], dtype=np.float64)

    xy = np.stack([
        np.stack([floats(c) for c in X_COLUMNS], axis=1),
        np.stack([floats(c) for c in Y_COLUMNS], axis=1),
    ], axis=2) if rows else np.empty((0, config.NUM_LANDMARKS, 2))

    return {
        "ts": floats("ts"),
        "present": np.array([r["present"] == "1" for r in rows], dtype=bool),
        "score": floats("score"),
        "w": np.array([int(r["w"]) for r in rows], dtype=np.int64),
        "h": np.array([int(r["h"]) for r in rows], dtype=np.int64),
        "xy": xy.astype(np.float32),
    }


def status_lines(tracked, fps_meter):
    """Các dòng trạng thái ASCII cho màn hình: FPS và tình trạng bàn tay."""
    rolling = fps_meter.rolling_fps
    lines = [f"t {tracked.ts:6.1f}s   FPS {rolling:5.1f}" if rolling
             else f"t {tracked.ts:6.1f}s"]
    summary = fps_meter.summary()
    if summary:
        lines.append(f"mean {summary['mean_fps']:5.1f}   "
                     f"low {summary['low_fps']:5.1f}")
    else:
        lines.append("(warm-up: FPS stats start after "
                     f"{config.FPS_WARMUP_SEC:.0f}s)")
    if tracked.present:
        lines.append(f"Hand: YES  score {tracked.score:.2f}")
    else:
        lines.append("Hand: NO")
    return lines


def record_session(frames, tracker, csv_path, *, max_sec=None, show=True,
                   mirror_display=True, window_title="record", header=()):
    """Vòng lặp ghi CSV dùng chung cho ``record_csv.py`` và ``observe.py``.

    Dừng khi hết nguồn, khi đạt ``max_sec`` giây, hoặc khi người dùng bấm phím
    thoát trên cửa sổ hiển thị.

    Returns:
        dict ``{"n_frames", "n_present", "duration_sec", "fps"}``.
    """
    fps_meter = FpsMeter()
    last_ts = 0.0
    with FrameCsvWriter(csv_path) as writer:
        try:
            for tracked in track(frames, tracker):
                writer.write_tracked(tracked)
                fps_meter.tick(tracked.ts)
                last_ts = tracked.ts

                if show:
                    lines = [*header, *status_lines(tracked, fps_meter)]
                    cv2.imshow(window_title, make_display(
                        tracked.frame_bgr, tracked.xy_norm, lines,
                        mirror=mirror_display,
                    ))
                    if quit_pressed():
                        break
                if max_sec is not None and tracked.ts >= max_sec:
                    break
        finally:
            if show:
                cv2.destroyAllWindows()

    return {
        "n_frames": writer.n_rows,
        "n_present": writer.n_present,
        "duration_sec": last_ts,
        "fps": fps_meter.summary(),
    }
