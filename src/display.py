"""Bản hiển thị cho người xem — nơi DUY NHẤT trong src/ được lật ảnh.

Ảnh vào mô hình không bao giờ lật. Người xem thì cần ảnh gương để điều khiển tự
nhiên: đưa tay sang phải thì hình trên màn hình cũng đi sang phải. Hàm ở đây
nhận frame GỐC cùng toạ độ tính trên frame gốc, rồi tự lật cả hai cho khớp.

``cv2.putText`` không vẽ được tiếng Việt có dấu — chữ trên màn hình phải là
ASCII.
"""

import cv2
import numpy as np
from mediapipe.tasks.python import vision

from src import config

_CONNECTIONS = [
    (c.start, c.end) for c in vision.HandLandmarksConnections.HAND_CONNECTIONS
]


def make_display(frame_bgr, xy_norm=None, lines=(), mirror=True, big_text=None):
    """Tạo ảnh để hiển thị; KHÔNG sửa ``frame_bgr``.

    Args:
        frame_bgr: frame đúng như đưa vào mô hình.
        xy_norm: ``(21, 2)`` toạ độ chuẩn hoá trên chính ``frame_bgr``, hoặc
            ``None``/NaN nếu không có tay.
        lines: các dòng chữ ASCII vẽ ở góc trên bên trái.
        mirror: ``True`` để lật gương cho người xem. Đặt ``False`` khi
            ``frame_bgr`` vốn đã được lật trước đó.
        big_text: một dòng chữ lớn ở giữa khung, ví dụ lệnh đếm ngược.

    Returns:
        Ảnh BGR mới.
    """
    if mirror:
        image = cv2.flip(frame_bgr, config.DISPLAY_FLIP_CODE)
    else:
        image = frame_bgr.copy()
    h, w = image.shape[:2]

    if xy_norm is not None and np.all(np.isfinite(xy_norm)):
        xs = xy_norm[:, 0]
        if mirror:
            xs = 1.0 - xs
        points = [(int(x * w), int(y * h)) for x, y in zip(xs, xy_norm[:, 1])]
        for a, b in _CONNECTIONS:
            cv2.line(image, points[a], points[b], config.COLOR_LINE,
                     config.LINE_THICKNESS)
        for p in points:
            cv2.circle(image, p, config.POINT_RADIUS, config.COLOR_POINT,
                       cv2.FILLED)

    x0, y0 = config.TEXT_ORIGIN
    for i, text in enumerate(lines):
        _put_text(image, text, (x0, y0 + i * config.TEXT_LINE_HEIGHT),
                  config.FONT_SCALE, config.COLOR_TEXT)

    if big_text:
        (tw, th), _ = cv2.getTextSize(big_text, cv2.FONT_HERSHEY_SIMPLEX,
                                      config.FONT_SCALE_BIG,
                                      config.TEXT_SHADOW_THICKNESS)
        _put_text(image, big_text, ((w - tw) // 2, (h + th) // 2),
                  config.FONT_SCALE_BIG, config.COLOR_ALERT)

    return image


def _put_text(image, text, origin, scale, color):
    """Chữ có viền tối để đọc được trên mọi nền."""
    cv2.putText(image, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale,
                config.COLOR_TEXT_SHADOW, config.TEXT_SHADOW_THICKNESS,
                cv2.LINE_AA)
    cv2.putText(image, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color,
                config.TEXT_THICKNESS, cv2.LINE_AA)


def quit_pressed():
    """Vẽ cửa sổ và báo người dùng có bấm phím thoát không.

    ``waitKey`` chính là lúc OpenCV vẽ giao diện — thiếu nó cửa sổ sẽ treo.
    """
    key = cv2.waitKey(config.DISPLAY_WAIT_MS)
    return key in config.QUIT_KEYS
