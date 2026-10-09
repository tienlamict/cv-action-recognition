"""Kiểm thử các phép biến đổi của probe_swipes.py trên cửa sổ tổng hợp."""

import numpy as np

from src import augment, config
from src.features import FEATURE_NAMES, openness, window_features
from src.preprocess import normalize_window
from tests.fixtures import hand, make_swipe, make_zoom
from tests.scripts_import import load_script

probe = load_script("probe_swipes")
W = config.WRIST


def opening_swipe():
    """Vuốt kiểu IPN: cổ tay dời ngang trong khi bàn tay mở dần."""
    shift = np.linspace(0, 240, config.T)
    open_ = np.linspace(0.2, 1.0, config.T)
    return normalize_window(np.stack([hand(openness=o, center=(200 + s, 240))
                                      for s, o in zip(shift, open_)]))


def test_tham_do_dung_chung_phep_bien_doi_voi_tang_cuong():
    """Bàn tay cứng của phép thăm dò và của tăng cường là MỘT hàm (luật 1):
    thăm dò đo đúng thứ mà tăng cường tạo ra."""
    assert probe.rigid_hand is augment.rigid_hand
    assert probe.shape_scaled is augment.shape_scaled


def test_lieu_luong_a_1_la_phep_dong_nhat():
    win = opening_swipe()
    np.testing.assert_allclose(probe.motion_scaled(win, 1.0), win)
    half = probe.motion_scaled(win, 0.5)
    np.testing.assert_allclose(half[-1, W] - half[0, W], 0.5 * (win[-1, W] - win[0, W]))
    np.testing.assert_allclose(openness(half), openness(win))


def test_co_tay_dung_yen_giu_dang_tay():
    win = normalize_window(make_zoom("in"))
    still = probe.static_wrist(make_swipe(+1).astype(float))
    np.testing.assert_allclose(still[:, W], np.repeat(still[:1, W], len(still), axis=0))
    np.testing.assert_allclose(openness(probe.static_wrist(win)), openness(win))


def test_di_ra_roi_quay_ve_triet_tieu_quang_doi():
    """Cổ tay đi ra rồi quay về: dời ròng nhỏ hẳn, tốc độ đỉnh giữ nguyên."""
    start = np.repeat(hand()[None], 6, axis=0)
    move = make_swipe(+1, 6)
    end = np.repeat(move[-1][None], 6, axis=0)
    win = normalize_window(np.concatenate([start, move, end]))
    back = probe.out_and_back(win)
    f, g = (dict(zip(FEATURE_NAMES, window_features(w, 1.0))) for w in (win, back))
    assert abs(g["dx"]) < 0.3 * abs(f["dx"])
    assert g["max_vx"] >= 0.9 * f["max_vx"]
