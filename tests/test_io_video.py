"""Kiểm thử iter_frames trên một video tổng hợp — không cần dữ liệu thật."""

import cv2
import numpy as np
import pytest

from src.io_video import iter_frames

N_FRAMES = 20
FPS = 30.0
SIZE = (64, 48)   # (w, h)


@pytest.fixture
def synthetic_video(tmp_path):
    path = tmp_path / "synthetic.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"),
                             FPS, SIZE)
    assert writer.isOpened(), "OpenCV không tạo được video MJPG để kiểm thử"
    for i in range(N_FRAMES):
        frame = np.full((SIZE[1], SIZE[0], 3), i * 10, dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return path


def test_iter_frames_ts_tang_don_dieu(synthetic_video):
    """Video đọc tuần tự: đủ số frame, ts[0] = 0 và tăng ngặt theo 1/FPS."""
    ts = np.array([t for _, t in iter_frames(synthetic_video)])

    assert ts.size == N_FRAMES, "không được bỏ frame nào"
    assert ts[0] == 0.0
    assert np.all(np.diff(ts) > 0)
    np.testing.assert_allclose(ts, np.arange(N_FRAMES) / FPS)


def test_iter_frames_bao_loi_khi_thieu_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        list(iter_frames(tmp_path / "khong_co.avi"))
