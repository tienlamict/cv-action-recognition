"""Kiểm thử tăng cường: mỗi phép trả lời "có đổi lớp không"."""

import numpy as np
import pytest

from src import augment, config
from src.features import FEATURE_NAMES, openness, window_features
from src.preprocess import normalize_window
from tests.fixtures import (OPEN_TIGHT, OPEN_WIDE, hand, make_static,
                            make_swipe, make_zoom)

SIGMA = 0.01
CLS = {name: i for i, name in enumerate(config.CLASSES)}
W = config.WRIST


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


def test_co_gian_thoi_gian_khong_lam_mat_buoc_dau():
    """Bước 1 mất tay: bước đầu vẫn nguyên (0 × NaN là NaN — lỗi cũ làm
    normalize_window từ chối cả cửa sổ); bước nội suy cạnh chỗ mất tay vẫn NaN."""
    win = normalize_window(make_swipe(+1))
    win[1] = np.nan
    for factor in (0.8, 1.0, 1.2):
        warped = augment.time_warp(win, factor)
        np.testing.assert_allclose(warped[0], win[0])
    assert np.isnan(augment.time_warp(win, 0.5)[1]).all()       # giữa bước 0 và 1


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


def opening_swipe():
    """Vuốt kiểu IPN: cổ tay dời ngang trong khi bàn tay mở dần."""
    shift = np.linspace(0, 240, config.T)
    open_ = np.linspace(OPEN_TIGHT, OPEN_WIDE, config.T)
    return normalize_window(np.stack([hand(openness=o, center=(200 + s, 240))
                                      for s, o in zip(shift, open_)]))


def mixed_windows(n=3):
    """``n`` lượt, mỗi lượt một cửa sổ mỗi lớp; hai lớp vuốt mở bàn tay khi dời."""
    swipe = opening_swipe()
    X, y = [], []
    for _ in range(n):
        X += [swipe, augment.flip_horizontal(swipe, CLS["swipe_left"])[0],
              normalize_window(make_static()), normalize_window(make_zoom("in")),
              normalize_window(make_zoom("out"))]
        y += [CLS["swipe_left"], CLS["swipe_right"], CLS["none"],
              CLS["zoom_in"], CLS["zoom_out"]]
    return np.stack(X).astype(np.float32), np.array(y)


def tip_offset(win):
    """Đầu ngón trỏ so với cổ tay cùng bước — một phần của dáng tay."""
    return win[:, config.INDEX_TIP] - win[:, W]


def test_ban_tay_cung_giu_quy_dao_bo_doi_dang():
    win = opening_swipe()
    assert np.ptp(openness(win)) > 0.3
    for ref in (0, config.T - 1):
        rigid = augment.rigid_hand(win, ref)
        np.testing.assert_allclose(rigid[:, W], win[:, W])
        np.testing.assert_allclose(openness(rigid), openness(win)[ref])


def test_giu_k_phan_doi_dang_tay():
    win = opening_swipe()
    np.testing.assert_allclose(augment.shape_scaled(win, 1.0), win)
    half = augment.shape_scaled(win, 0.5)
    np.testing.assert_allclose(half[:, W], win[:, W])
    np.testing.assert_allclose(tip_offset(half) - tip_offset(half)[0],
                               0.5 * (tip_offset(win) - tip_offset(win)[0]))


def test_ban_tay_cung_chi_cho_cap_vuot_va_chi_tap_train():
    """Mỗi cửa sổ vuốt một bản: cổ tay dời như cũ, dáng tay gần như không đổi,
    đã chuẩn hoá lại; zoom và none không có bản nào; val, test bị từ chối."""
    X, y = mixed_windows()
    rng = np.random.default_rng(config.SEED)
    for split in ("val", "test", "real_tune", "real_test"):
        with pytest.raises(ValueError, match="train"):
            augment.rigid_swipes(X, y, split, rng, share=1.0, sigma=SIGMA)

    X_before = X.copy()
    X_r, y_r, source = augment.rigid_swipes(X, y, "train", rng, share=1.0,
                                            keep=(0.0, 0.0), sigma=SIGMA)
    np.testing.assert_array_equal(X, X_before)
    swipes = np.flatnonzero(np.isin(y, augment.SWIPE_LABELS))
    assert sorted(source) == sorted(swipes)
    np.testing.assert_array_equal(y_r, y[source])
    assert X_r.shape == (swipes.size, *X.shape[1:]) and X_r.dtype == np.float32
    for win, i in zip(X_r, source):
        np.testing.assert_allclose(win[0, W], 0.0, atol=1e-6)
        assert np.linalg.norm(win[0, config.MIDDLE_MCP]) == pytest.approx(1.0, abs=1e-6)
        assert np.ptp(openness(win)) < 0.2 * np.ptp(openness(X[i]))
        # nhiễu ở lòng bàn tay bước đầu co giãn cả cửa sổ khi chuẩn hoá lại
        moved, original = win[-1, W] - win[0, W], X[i][-1, W] - X[i][0, W]
        np.testing.assert_allclose(moved, original, rtol=0.05, atol=0.05)


def test_so_ban_bang_tay_cung_theo_share():
    X, y = mixed_windows(n=4)     # 8 cửa sổ vuốt
    rng = np.random.default_rng(0)
    for share, expected in ((0.0, 0), (0.5, 4), (1.0, 8), (1.5, 12)):
        X_r, y_r, source = augment.rigid_swipes(X, y, "train", rng, share=share,
                                                sigma=SIGMA)
        assert len(X_r) == len(y_r) == len(source) == expected
    _, _, half = augment.rigid_swipes(X, y, "train", rng, share=0.5, sigma=SIGMA)
    assert len(set(half)) == len(half), "phần lẻ chọn không lặp"


def test_khoang_k_giu_dung_phan_doi_dang_tay():
    """k = 0,5 cố định: dáng tay đổi đúng một nửa, dù bước mốc là bước nào."""
    X, y = mixed_windows(n=2)
    X_r, _, source = augment.rigid_swipes(X, y, "train", np.random.default_rng(0),
                                          share=1.0, keep=(0.5, 0.5), sigma=0.0)
    for win, i in zip(X_r, source):
        np.testing.assert_allclose(np.ptp(tip_offset(win), axis=0),
                                   0.5 * np.ptp(tip_offset(X[i]), axis=0), atol=1e-5)


def test_moc_dang_tay_bo_buoc_long_ban_tay_bat_thuong():
    """Bước tay nghiêng cạnh (lòng bàn tay ngắn bất thường) hay mất tay không
    bao giờ làm mốc dáng tay; bước mất tay vẫn là NaN trong bản tạo ra."""
    win = opening_swipe().copy()
    win[5, config.MIDDLE_MCP] = win[5, W] + 0.02 * (win[5, config.MIDDLE_MCP] - win[5, W])
    win[8] = np.nan
    steps = augment.usable_steps(win)
    assert 0 in steps and 5 not in steps and 8 not in steps

    X = np.stack([win] * 30).astype(np.float32)
    y = np.full(30, CLS["swipe_left"])
    X_r, _, source = augment.rigid_swipes(X, y, "train", np.random.default_rng(0),
                                          share=1.0, keep=(0.0, 0.0), sigma=SIGMA)
    assert len(source) == 30
    assert np.all(np.isnan(X_r[:, 8]))
