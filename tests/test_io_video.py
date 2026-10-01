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


class FakeCapture:
    """VideoCapture giả: trả frame tại các vị trí container cho trước.

    Mô phỏng bộ giải mã FFmpeg bỏ frame "not coded" của XVID: ``read()`` không
    bao giờ trả frame ở vị trí bị bỏ, nhưng ``CAP_PROP_POS_MSEC`` vẫn cho vị
    trí thật của frame vừa đọc.
    """

    def __init__(self, positions, fps=FPS):
        self.positions = list(positions)
        self.fps = fps
        self.current = None

    def isOpened(self):
        return True

    def read(self):
        if not self.positions:
            return False, None
        self.current = self.positions.pop(0)
        return True, np.zeros((SIZE[1], SIZE[0], 3), dtype=np.uint8)

    def get(self, prop):
        if prop == cv2.CAP_PROP_FPS:
            return self.fps
        if prop == cv2.CAP_PROP_POS_MSEC:
            return self.current * 1000 / self.fps
        raise AssertionError(f"iter_frames không được đọc thuộc tính {prop}")

    def release(self):
        pass


def test_iter_frames_ts_theo_vi_tri_khi_bo_giai_ma_bo_frame(tmp_path,
                                                             monkeypatch):
    """Frame bị bộ giải mã bỏ để lại khoảng trống trong ts, không kéo các
    frame sau sớm lên — nếu không, nhãn IPN trôi dần tới 48 frame."""
    path = tmp_path / "co_frame_bi_bo.avi"
    path.touch()
    positions = [0, 1, 2, 4, 5, 8, 9]          # frame 3, 6, 7 bị bỏ
    monkeypatch.setattr(cv2, "VideoCapture",
                        lambda _: FakeCapture(positions))

    ts = np.array([t for _, t in iter_frames(path)])

    np.testing.assert_allclose(ts, np.array(positions) / FPS)


def test_iter_frames_bao_loi_khi_vi_tri_khong_tang(tmp_path, monkeypatch):
    """Container không cho vị trí dùng được thì dừng, không đoán."""
    path = tmp_path / "khong_co_moc.avi"
    path.touch()
    monkeypatch.setattr(cv2, "VideoCapture",
                        lambda _: FakeCapture([0, 1, 1, 2]))

    with pytest.raises(RuntimeError, match="không tăng ngặt"):
        list(iter_frames(path))
