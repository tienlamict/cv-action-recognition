"""Kiểm thử cắt cửa sổ và gán nhãn — dữ liệu tổng hợp, không đụng data/."""

import numpy as np

from src import config
from src.windows import cut_windows, windows_from_clip
from tests.fixtures import (CENTER, PALM_PX, SWIPE_PALMS, hand, make_static,
                            make_swipe, save_parts_clip)
from tests.scripts_import import load_script

build = load_script("build_dataset")

SWIPE_LEFT = config.CLASSES.index("swipe_left")


def swipe_with_rest(rest=10, moving=10):
    """Đoạn cử chỉ kiểu IPN: đứng yên, vuốt nhanh, đứng yên — tổng
    ``2 * rest + moving`` bước. Khoảnh khắc chính nằm giữa phần vuốt."""
    start = np.repeat(hand()[None], rest, axis=0)
    end_center = (CENTER[0] + SWIPE_PALMS * PALM_PX, CENTER[1])
    end = np.repeat(hand(center=end_center)[None], rest, axis=0)
    return np.concatenate([start, make_swipe(+1, moving), end])


def test_gan_nhan_neo_vao_khoanh_khac_chinh(tmp_path):
    """Cửa sổ dương phải chứa khoảnh khắc chính, cách hai mép ít nhất
    CORE_MARGIN_STEPS bước. Cửa sổ giao cử chỉ mà không chứa nó bị BỎ, không
    thành none. Cửa sổ none không bao giờ chạm đoạn cử chỉ."""
    path = save_parts_clip(tmp_path / "c.npz", [
        (make_static(30), "B0A", "none"),
        (swipe_with_rest(), "G05", "swipe_left"),        # bước 30–59
        (make_static(30, seed=1), "D0X", "none")], subject="p1")

    windows, _, stats = windows_from_clip(path)
    starts = np.rint(windows["t0"] * config.HZ).astype(int)
    m = config.CORE_MARGIN_STEPS
    moving = np.arange(40, 50)          # phần vuốt của đoạn G05 trên lưới

    positive = windows["y"] == SWIPE_LEFT
    assert positive.any()
    for s in starts[positive]:
        core_inside = (moving >= s + m) & (moving < s + config.T - m)
        assert core_inside.any(), f"cửa sổ dương bắt đầu ở {s} không chứa động tác"
    assert set(windows["src_label"][positive]) == {"G05"}

    for s in starts[~positive]:
        assert s + config.T <= 30 or s >= 60, f"cửa sổ none {s} chạm đoạn cử chỉ"
    assert {"B0A", "D0X"} == set(windows["src_label"][~positive])

    all_starts = np.arange(0, 90 - config.T + 1, config.STRIDE)
    overlapping = all_starts[(all_starts < 60) & (all_starts + config.T > 30)]
    assert stats["ambiguous"] == overlapping.size - positive.sum()
    assert stats["ambiguous"] > 0


def test_cua_so_khong_bac_cau_qua_hai_clip(tmp_path):
    """Hai clip 25 bước: mỗi clip chỉ có 3 cửa sổ (bắt đầu 0, 3, 6). Nối hai
    clip rồi cắt thì sẽ ra 11 cửa sổ, trong đó có cửa sổ bắc cầu."""
    paths = [save_parts_clip(tmp_path / f"{name}.npz",
                             [(make_static(25, seed=i), "D0X", "none")],
                             subject=name)
             for i, name in enumerate(("a", "b"))]

    windows, info = build.collect(paths)

    assert info["n_clips"] == 2
    assert windows["y"].size == 6
    for name in ("a", "b"):
        t0 = windows["t0"][windows["clip"] == name]
        np.testing.assert_allclose(t0, [0.0, 0.2, 0.4], atol=1e-6)
        assert np.all(t0 + (config.T - 1) / config.HZ <= 24 / config.HZ + 1e-6)


def test_cat_cua_so_loai_cua_so_thieu_tay():
    """Bước đầu mất tay, hoặc tỉ lệ có tay < MIN_PRESENCE: loại cửa sổ."""
    ts = np.arange(config.T) / config.HZ
    segments = np.array([[0, config.T, 0]])

    seq = make_static(config.T)
    seq[0] = np.nan                          # bước đầu mất tay
    xy = seq / np.array([config.CAM_W, config.CAM_H])
    windows, stats = cut_windows(ts, xy, config.CAM_W, config.CAM_H, segments,
                                 ["D0X"])
    assert windows["y"].size == 0 and stats["low_presence"] == 1

    seq = make_static(config.T)
    seq[4:10] = np.nan                       # 6 bước liền: quá MAX_GAP, giữ NaN
    xy = seq / np.array([config.CAM_W, config.CAM_H])
    windows, _ = cut_windows(ts, xy, config.CAM_W, config.CAM_H, segments,
                             ["D0X"])
    assert windows["y"].size == 0, "12/18 = 67% < MIN_PRESENCE"


def test_cua_so_o_toa_do_pixel_chua_chuan_hoa(tmp_path):
    """cut_windows trả PIXEL: tăng cường phải đứng trước normalize_window."""
    path = save_parts_clip(tmp_path / "c.npz",
                           [(make_static(30), "D0X", "none")], subject="p1")
    windows, meta, _ = windows_from_clip(path)
    assert windows["X"].shape[1:] == (config.T, config.NUM_LANDMARKS, 2)
    assert np.nanmax(windows["X"]) > 100, "phải là pixel, không phải đơn vị lòng bàn tay"
    assert set(windows["subject"]) == {"p1"} and set(windows["clip"]) == {"c"}
