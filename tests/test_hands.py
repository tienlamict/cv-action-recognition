"""Kiểm thử HandTracker — không cần camera, không cần dữ liệu thật."""

import inspect

import numpy as np

from src import config, hands
from src.hands import HandTracker


def test_hands_tra_ve_nan_tren_anh_den():
    """Ảnh đen → không có tay: present False, xy toàn NaN, không trả về None."""
    black = np.zeros((config.CAM_H, config.CAM_W, 3), dtype=np.uint8)
    with HandTracker() as tracker:
        xy, present, score, handedness = tracker.process(black, 0)

    assert present is False
    assert xy is not None
    assert xy.shape == (config.NUM_LANDMARKS, 2)
    assert xy.dtype == np.float32
    assert np.all(np.isnan(xy))
    assert np.isnan(score)
    assert handedness == ""


def test_hands_khong_lat_anh_dau_vao():
    """Đọc mã nguồn: hands.py không được lật ảnh đưa vào mô hình (luật 11)."""
    source = inspect.getsource(hands)
    assert "cv2.flip" not in source
    assert "flip(" not in source
    assert "[:, ::-1]" not in source
