"""Cửa vào DUY NHẤT của mọi nguồn ảnh: webcam và file video.

Mọi script đọc ảnh đều phải đi qua :func:`iter_frames`. Nhờ vậy dữ liệu IPN,
dữ liệu tự quay và webcam lúc chạy thật có cùng một cách gắn mốc thời gian.

Hai nguồn gắn mốc thời gian khác nhau, và đó là chủ ý:

- **Webcam**: đồng hồ thật (``time.perf_counter``) đọc ngay sau khi lấy frame.
  FPS webcam không phải hằng số — nó tụt khi phòng tối — nên chỉ đồng hồ thật
  mới cho biết frame thực sự xảy ra lúc nào.
- **File video**: chỉ số frame chia FPS của file, đọc TUẦN TỰ. Không bao giờ
  nhảy frame bằng ``CAP_PROP_POS_FRAMES`` — với nhiều codec nó chậm và lệch.

"Chỉ số frame" là **vị trí của frame trong container**, đọc từ
``CAP_PROP_POS_MSEC`` sau mỗi ``read()``, KHÔNG phải số lần ``read()`` thành
công. Hai thứ đó khác nhau: bộ giải mã FFmpeg âm thầm bỏ các frame "not coded"
của XVID (chunk 6 byte, nghĩa là "giữ nguyên ảnh trước"). Trên IPN, 101/200
video có frame kiểu này, nhiều nhất 56 frame một video. Đếm số lần ``read()``
thì mỗi frame bị bỏ làm ``ts`` của mọi frame sau sớm đi 1/FPS. Đếm theo vị trí
thì frame bị bỏ chỉ để lại một khoảng trống trong ``ts`` — đúng với thời gian
thật, và ``resample`` xử lý khoảng trống đó như mọi lỗ hổng khác. Vị trí tính
từ frame ĐẦU TIÊN giải mã được, để ``ts[0] = 0`` cả khi file mở đầu bằng frame
"not coded" (4 video IPN mở đầu bằng 10 frame như vậy). Xem
``docs/ipn_format.md`` mục 6.

Cả hai đều trả ``ts`` tính bằng giây, bắt đầu từ 0.0 ở frame đầu tiên.
"""

import time
from pathlib import Path

import cv2

from src import config


def iter_frames(source):
    """Sinh ra ``(frame_bgr, ts_sec)`` cho từng frame của nguồn.

    Args:
        source: số nguyên là chỉ số webcam (ví dụ ``config.CAM_INDEX``),
            hoặc đường dẫn tới file video.

    Yields:
        ``(frame_bgr, ts_sec)`` — ảnh BGR đúng như OpenCV đọc được (KHÔNG
        lật, không đổi kênh màu) và mốc thời gian tính bằng giây.

    Raises:
        FileNotFoundError: file video không tồn tại.
        RuntimeError: không mở được nguồn, hoặc vị trí frame trong file video
            không tăng ngặt (container không có mốc thời gian dùng được).
        ValueError: file video không khai báo FPS hợp lệ.
    """
    if isinstance(source, int):
        yield from _iter_webcam(source)
    else:
        yield from _iter_video_file(Path(source))


def _iter_webcam(index):
    cap = cv2.VideoCapture(index)
    try:
        if not cap.isOpened():
            raise RuntimeError(
                f"Không mở được webcam số {index}. Ứng dụng khác có đang dùng "
                "camera không, hoặc Windows có đang chặn quyền camera không?"
            )
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_H)
        cap.set(cv2.CAP_PROP_FPS, config.CAM_FPS)

        t0 = None
        while True:
            ok, frame_bgr = cap.read()
            now = time.perf_counter()
            if not ok:
                break
            if t0 is None:
                t0 = now
            yield frame_bgr, now - t0
    finally:
        cap.release()


def _iter_video_file(path):
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file video: {path}")

    cap = cv2.VideoCapture(str(path))
    try:
        if not cap.isOpened():
            raise RuntimeError(f"OpenCV không mở được file video: {path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            raise ValueError(
                f"File {path} không khai báo FPS hợp lệ ({fps}); không thể "
                "suy ra mốc thời gian."
            )

        first = previous = None
        while True:
            ok, frame_bgr = cap.read()
            if not ok:
                break
            index = round(cap.get(cv2.CAP_PROP_POS_MSEC) * fps / 1000)
            if previous is not None and index <= previous:
                raise RuntimeError(
                    f"{path}: vị trí frame không tăng ngặt ({previous} → "
                    f"{index}). Container này không cho mốc thời gian dùng "
                    "được; đừng thay bằng cách đếm read() — xem docstring."
                )
            if first is None:
                first = index
            yield frame_bgr, (index - first) / fps
            previous = index
    finally:
        cap.release()
