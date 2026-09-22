"""Đo FPS xử lý từ mốc thời gian của từng frame.

Hai con số khác nhau cho hai mục đích:

- **FPS trượt** trên ``FPS_ROLLING_FRAMES`` frame gần nhất — để hiển thị.
- **Tóm tắt** sau khi bỏ ``FPS_WARMUP_SEC`` giây đầu — để báo cáo: FPS trung
  bình và phân vị thấp ``FPS_LOW_PERCENTILE`` của FPS tức thời. Vài giây đầu
  camera còn tự chỉnh phơi sáng nên bị loại.
"""

from collections import deque

import numpy as np

from src import config


class FpsMeter:
    def __init__(self, warmup_sec=config.FPS_WARMUP_SEC,
                 rolling_frames=config.FPS_ROLLING_FRAMES):
        self.warmup_sec = warmup_sec
        self._recent = deque(maxlen=rolling_frames)
        self._t_first = None
        self._kept = []

    def tick(self, ts):
        """Ghi nhận một frame có mốc thời gian ``ts`` (giây)."""
        if self._t_first is None:
            self._t_first = ts
        self._recent.append(ts)
        if ts - self._t_first >= self.warmup_sec:
            self._kept.append(ts)

    @property
    def rolling_fps(self):
        """FPS trên các frame gần nhất; ``None`` khi chưa đủ hai frame."""
        if len(self._recent) < 2:
            return None
        span = self._recent[-1] - self._recent[0]
        return (len(self._recent) - 1) / span if span > 0 else None

    @property
    def warming_up(self):
        return len(self._kept) < 2

    def summary(self):
        """``{"mean_fps", "low_fps", "n_frames"}`` sau thời gian khởi động.

        Trả về ``None`` khi chưa đủ dữ liệu sau thời gian khởi động.
        """
        if self.warming_up:
            return None
        ts = np.asarray(self._kept)
        dt = np.diff(ts)
        dt = dt[dt > 0]
        if dt.size == 0:
            return None
        return {
            "mean_fps": float((len(ts) - 1) / (ts[-1] - ts[0])),
            "low_fps": float(np.percentile(1.0 / dt, config.FPS_LOW_PERCENTILE)),
            "n_frames": int(len(ts)),
        }
