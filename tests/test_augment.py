"""Kiểm thử tăng cường: mỗi phép trả lời "có đổi lớp không"."""

import numpy as np
import pytest

from src import augment, config
from src.features import FEATURE_NAMES, window_features
from src.preprocess import normalize_window
from tests.fixtures import make_static, make_swipe, make_zoom

SIGMA = 0.01
CLS = {name: i for i, name in enumerate(config.CLASSES)}


def feature(win, name):
    return window_features(normalize_window(win), 1.0)[FEATURE_NAMES.index(name)]


def test_flip_doi_nhan_cap_vuot_va_giu_nhan_cap_zoom():
    """Lật swipe_left → swipe_right, dx đổi dấu, open_delta giữ nguyên;
    zoom và none giữ nhãn."""
    win = normalize_window(make_swipe(+1))
    flipped, label = augment.flip_horizontal(win, CLS["swipe_left"])

    assert label == CLS["swipe_right"]
    assert np.sign(feature(flipped, "dx")) == -np.sign(feature(win, "dx")) != 0
    assert feature(flipped, "open_delta") == pytest.approx(feature(win, "open_delta"))
    assert augment.flip_horizontal(win, CLS["swipe_right"])[1] == CLS["swipe_left"]

    zoom = normalize_window(make_zoom("in"))
    zoom_flipped, label = augment.flip_horizontal(zoom, CLS["zoom_in"])
    assert label == CLS["zoom_in"]
    assert feature(zoom_flipped, "open_delta") == pytest.approx(
        feature(zoom, "open_delta"))
    assert augment.flip_horizontal(zoom, CLS["zoom_out"])[1] == CLS["zoom_out"]
    assert augment.flip_horizontal(zoom, CLS["none"])[1] == CLS["none"]


def test_tang_cuong_khong_cham_vao_val_va_test():
    """Tăng cường chỉ cho train (luật 9); mảng đầu vào không bị sửa."""
    X = np.stack([normalize_window(make_swipe(+1)),
                  normalize_window(make_zoom("out"))]).astype(np.float32)
    y = np.array([CLS["swipe_left"], CLS["zoom_out"]])
    rng = np.random.default_rng(config.SEED)

    for split in ("val", "test", "real_tune", "real_test"):
        with pytest.raises(ValueError, match="train"):
            augment.augment_windows(X, y, split, rng, sigma=SIGMA)

    X_before, y_before = X.copy(), y.copy()
    X_aug, y_aug = augment.augment_windows(X, y, "train", rng, sigma=SIGMA)
    np.testing.assert_array_equal(X, X_before)
    np.testing.assert_array_equal(y, y_before)
    assert X_aug.shape == X.shape and X_aug.dtype == np.float32
    assert not np.allclose(X_aug, X)


def test_ket_qua_tang_cuong_da_chuan_hoa():
    """Bản tăng cường đã qua normalize_window: cổ tay frame đầu ở gốc, lòng
    bàn tay frame đầu dài đúng 1."""
    rng = np.random.default_rng(config.SEED)
    for _ in range(20):
        win, _ = augment.augment(normalize_window(make_swipe(-1)),
                                 CLS["swipe_right"], rng, sigma=SIGMA)
        np.testing.assert_allclose(win[0, config.WRIST], 0.0, atol=1e-9)
        assert np.linalg.norm(win[0, config.MIDDLE_MCP]) == pytest.approx(1.0)
        assert np.all(np.isfinite(win))


def test_co_gian_deu_bi_chuan_hoa_triet_tieu_con_doi_dan_thi_khong():
    """Lý do thay co giãn đều bằng co giãn đổi dần (quyết định 2026-10-05)."""
    win = normalize_window(make_swipe(+1))

    np.testing.assert_allclose(normalize_window(win * 1.1), win, atol=1e-9)

    ramp = normalize_window(augment.scale_ramp(win, 1.1))
    np.testing.assert_allclose(ramp[0], win[0], atol=1e-9)
    np.testing.assert_allclose(ramp[-1], win[-1] * 1.1, atol=1e-9)


def test_xoay_giu_khoang_cach_va_goc():
    win = normalize_window(make_zoom("in"))
    rotated = augment.rotate(win, 10.0)
    np.testing.assert_allclose(np.linalg.norm(rotated, axis=-1),
                               np.linalg.norm(win, axis=-1), atol=1e-9)
    np.testing.assert_allclose(rotated[0, config.WRIST], 0.0, atol=1e-12)


def test_co_gian_thoi_gian_neo_buoc_dau_va_giu_T():
    win = normalize_window(make_swipe(+1))
    np.testing.assert_allclose(augment.time_warp(win, 1.0), win)

    slow = augment.time_warp(win, 0.5)
    assert slow.shape == win.shape
    np.testing.assert_allclose(slow[0], win[0])
    np.testing.assert_allclose(slow[2], win[1])                  # bước 2 ← bước 1
    np.testing.assert_allclose(slow[1], (win[0] + win[1]) / 2)   # nội suy giữa

    fast = augment.time_warp(win, 1.2)
    np.testing.assert_allclose(fast[-1], win[-1])                # giữ bước cuối


def test_xoa_buoc_roi_va_lai():
    win = normalize_window(make_static())
    patched = augment.drop_steps(win, start=5, length=3)
    assert np.all(np.isfinite(patched))
    np.testing.assert_allclose(patched[:5], win[:5])
    np.testing.assert_allclose(patched[8:], win[8:])


def test_tang_cuong_doi_hoi_sigma_da_do(monkeypatch):
    """Không truyền sigma thì đọc AUG_NOISE_SIGMA qua require_measured: còn
    None thì dừng, đã đo thì dùng."""
    win = normalize_window(make_static())
    monkeypatch.setattr(config, "AUG_NOISE_SIGMA", None)
    with pytest.raises(RuntimeError, match="AUG_NOISE_SIGMA"):
        augment.augment(win, 0, np.random.default_rng(0))

    monkeypatch.setattr(config, "AUG_NOISE_SIGMA", SIGMA)
    out, label = augment.augment(win, 0, np.random.default_rng(0))
    assert out.shape == win.shape and label == 0
