"""Đọc dữ liệu điểm mốc đã ghi trên đĩa thành mảng để đưa vào đường ống.

Đây là lớp mỏng trên ``recording.read_frames_csv`` — nơi biết định dạng CSV của
``scripts/record_csv.py``. Không đọc CSV theo cách nào khác ở chỗ nào khác.
"""

import numpy as np

from src.recording import read_frames_csv


def read_record_csv(path):
    """Đọc một CSV điểm mốc.

    Args:
        path: đường dẫn tới ``landmarks.csv``.

    Returns:
        ``(ts, xy_norm, present, w, h)``:

        - ``ts`` float64 ``(N,)`` — giây
        - ``xy_norm`` float32 ``(N, 21, 2)`` — toạ độ chuẩn hoá ``[0, 1]``,
          NaN ở dòng mất tay
        - ``present`` bool ``(N,)``
        - ``w``, ``h`` int — kích thước khung hình

    Raises:
        ValueError: file rỗng, hoặc kích thước khung đổi giữa chừng (hai nguồn
            bị trộn vào một file).
    """
    data = read_frames_csv(path)
    if data["ts"].size == 0:
        raise ValueError(f"{path} không có dòng dữ liệu nào")

    sizes = {(int(w), int(h)) for w, h in zip(data["w"], data["h"])}
    if len(sizes) > 1:
        raise ValueError(f"{path} chứa nhiều kích thước khung hình: {sizes}")
    w, h = sizes.pop()

    return (np.asarray(data["ts"], dtype=np.float64), data["xy"],
            data["present"], w, h)
