"""Biến thể biểu diễn cho các bảng khảo sát của Phase 8 — KHÔNG dùng ở demo,
ở mô hình chính, hay ở bất kỳ đường ống nào khác.

Mỗi biến thể nhận cửa sổ ĐÃ ``normalize_window`` (gốc tại cổ tay frame đầu, đơn
vị lòng bàn tay frame đầu) và đổi đúng MỘT yếu tố, đứng sau chuẩn hoá trong thứ
tự của luật 5. Không định nghĩa lại ``normalize_window``: chuẩn hoá vẫn chỉ có
một bản, ở ``src/preprocess.py``.

- :func:`per_frame_origin` — Bảng 2: gốc toạ độ là cổ tay của TỪNG frame (cách
  A, cẩm nang mục 8.c), đơn vị giữ nguyên lòng bàn tay frame đầu.
- :func:`select_landmarks` — bảng phụ: 11 điểm rút gọn ``REDUCED_LANDMARKS``.
"""

import numpy as np

from src import config


def per_frame_origin(win_norm):
    """Dời gốc về cổ tay của chính từng frame: ``win[t] − win[t, cổ tay]``.

    Cổ tay khi đó nằm ở gốc ở MỌI frame, nên mọi thông tin về việc bàn tay đã
    đi đâu biến mất — đúng điều Bảng 2 đo. Dáng tay giữ nguyên. Bước mất tay
    (NaN) vẫn là NaN.
    """
    win = np.asarray(win_norm, dtype=np.float64)
    return win - win[:, config.WRIST:config.WRIST + 1]


def select_landmarks(win, idx=config.REDUCED_LANDMARKS):
    """Chỉ giữ các điểm ``idx``: ``(T, 21, 2)`` → ``(T, len(idx), 2)``.

    Gọi SAU ``normalize_window``: chuẩn hoá cần cổ tay và gốc ngón giữa, và cả
    hai đều có trong ``REDUCED_LANDMARKS``.
    """
    return np.asarray(win)[:, list(idx)]


def landmark_columns(idx=config.REDUCED_LANDMARKS):
    """Cột của các điểm ``idx`` trong chuỗi ``(T, 42)`` của LSTM — điểm ``i``
    chiếm hai cột ``2i`` (x) và ``2i + 1`` (y), như ``datasets.window_sequence``."""
    return [2 * i + axis for i in idx for axis in (0, 1)]
