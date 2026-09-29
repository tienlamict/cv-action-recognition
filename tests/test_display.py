"""Kiểm thử bản hiển thị — nơi duy nhất được lật ảnh (luật 11)."""

import numpy as np

from src.display import make_display


def test_display_khong_sua_frame_goc():
    """Lật chỉ xảy ra trên bản hiển thị; frame đưa vào mô hình giữ nguyên."""
    frame = np.zeros((48, 64, 3), dtype=np.uint8)
    frame[:, :8] = 255     # vạch trắng ở mép TRÁI của frame gốc
    original = frame.copy()

    shown = make_display(frame, lines=())

    np.testing.assert_array_equal(frame, original)
    assert shown[:, -1].mean() == 255, "bản hiển thị phải là ảnh gương"
