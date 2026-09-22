"""Kiểm thử logic quyết định dấu SWIPE_LEFT_SIGN và bản hiển thị."""

import numpy as np

from src.calibration import decide_sign, rep_dx
from src.display import make_display


def test_decide_sign_chi_ket_luan_khi_dut_khoat():
    # Mười lần cùng dấu dương → +1.
    assert decide_sign([0.3] * 10)["sign"] == 1
    # Mười lần cùng dấu âm → -1: dấu đến từ số đo, không viết cứng.
    assert decide_sign([-0.3] * 10)["sign"] == -1
    # Một lần hợp lệ ngược dấu → không kết luận.
    assert decide_sign([0.3] * 9 + [-0.3])["sign"] is None
    # Quá ít lần hợp lệ (NaN hoặc gần như không di chuyển) → không kết luận.
    assert decide_sign([0.3] * 3 + [np.nan] * 4 + [0.01] * 3)["sign"] is None


def test_rep_dx_bo_qua_frame_mat_tay():
    dx, n_present = rep_dx([np.nan, 0.2, np.nan, 0.3, 0.5, np.nan], min_frames=3)
    assert n_present == 3
    assert np.isclose(dx, 0.3)
    assert np.isnan(rep_dx([0.2, np.nan], min_frames=3)[0])


def test_display_khong_sua_frame_goc():
    """Lật chỉ xảy ra trên bản hiển thị; frame đưa vào mô hình giữ nguyên."""
    frame = np.zeros((48, 64, 3), dtype=np.uint8)
    frame[:, :8] = 255     # vạch trắng ở mép TRÁI của frame gốc
    original = frame.copy()

    shown = make_display(frame, lines=())

    np.testing.assert_array_equal(frame, original)
    assert shown[:, -1].mean() == 255, "bản hiển thị phải là ảnh gương"
