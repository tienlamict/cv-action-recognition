"""Bộ đệm theo THỜI GIAN cho lúc chạy thật — Phase 5.

Giữ các frame trong ``WIN_SEC + BUFFER_EXTRA_SEC`` giây gần nhất, theo mốc
thời gian chứ không theo số frame: webcam tụt FPS khi phòng tối, và cửa sổ phải
luôn dài đúng ``WIN_SEC`` giây (luật 7).

:meth:`TimeBuffer.window` đi qua đúng ``load_sequence`` như dữ liệu IPN (luật
1), rồi lấy ``T`` bước cuối. Không gọi ``resample`` hay ``fill_short_gaps``
trực tiếp. Bộ đệm chỉ chứa quá khứ, nên mọi thứ tính từ nó đều nhân quả.
"""

from collections import deque

import numpy as np

from src import config
from src.preprocess import load_sequence


class TimeBuffer:
    """Bộ đệm frame theo thời gian."""

    def __init__(self, keep_sec=config.WIN_SEC + config.BUFFER_EXTRA_SEC):
        self.keep_sec = keep_sec
        self._ts = deque()
        self._xy = deque()
        self._size = None

    def __len__(self):
        return len(self._ts)

    def push(self, ts, xy_norm, w, h):
        """Thêm một frame; frame không thấy tay vẫn phải đẩy vào, với ``xy_norm``
        toàn NaN (luật 4). Bỏ các frame cũ hơn ``ts - keep_sec``.

        Raises:
            ValueError: ``ts`` không tăng, hoặc kích thước khung đổi giữa chừng.
        """
        if self._ts and ts <= self._ts[-1]:
            raise ValueError(f"ts phải tăng ngặt: {self._ts[-1]} → {ts}")
        if self._size is not None and self._size != (w, h):
            raise ValueError(f"Kích thước khung đổi: {self._size} → {(w, h)}")
        self._size = (w, h)
        self._ts.append(float(ts))
        self._xy.append(np.asarray(xy_norm, dtype=np.float64))
        while self._ts and self._ts[0] < ts - self.keep_sec:
            self._ts.popleft()
            self._xy.popleft()

    def window(self):
        """Cửa sổ ``T`` bước cuối, ở toạ độ PIXEL, chưa chuẩn hoá.

        Returns:
            ``(win_pixel (T, 21, 2), presence_ratio)``, hoặc ``None`` khi chưa
            đủ ``T`` bước, tỉ lệ có tay dưới ``MIN_PRESENCE``, hay bước đầu
            mất tay.
        """
        if len(self._ts) < 2:
            return None
        w, h = self._size
        _, xy = load_sequence(np.array(self._ts), np.stack(self._xy), w, h)
        if xy.shape[0] < config.T:
            return None
        win = xy[-config.T:]
        finite = np.all(np.isfinite(win.reshape(config.T, -1)), axis=1)
        presence = float(finite.mean())
        if presence < config.MIN_PRESENCE or not finite[0]:
            return None
        return win, presence
