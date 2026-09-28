"""Kiểm thử vector đặc trưng 13 chiều trên các cửa sổ tổng hợp."""

import numpy as np

from src import config
from src.features import FEATURE_NAMES, window_features
from src.preprocess import normalize_window
from tests.fixtures import make_static, make_swipe, make_wave, make_zoom


def features_of(win_px, presence_ratio=1.0):
    """Chuẩn hoá rồi trích đặc trưng, trả về dict tên → giá trị."""
    values = window_features(normalize_window(win_px), presence_ratio)
    return dict(zip(FEATURE_NAMES, values))


def flip_x(win_px, width=config.CAM_W):
    """Lật ngang trong toạ độ PIXEL, như soi gương cả khung hình."""
    flipped = win_px.copy()
    flipped[..., 0] = width - flipped[..., 0]
    return flipped


def test_flip_doi_dau_dx_va_mean_vx():
    """Lật ảnh thì hai đặc trưng có dấu phải đổi dấu — chúng mang thông tin hướng."""
    win = make_swipe(+1)
    original = features_of(win)
    mirrored = features_of(flip_x(win))

    assert np.isclose(mirrored["dx"], -original["dx"], atol=1e-5)
    assert np.isclose(mirrored["mean_vx"], -original["mean_vx"], atol=1e-5)
    assert abs(original["dx"]) > 1.0, "cửa sổ mẫu phải có dời ngang rõ rệt"


def test_flip_giu_nguyen_open_delta():
    """Lật ảnh là phép đối xứng: mọi khoảng cách, nên độ xòe, giữ nguyên."""
    win = make_zoom("in")
    original = features_of(win)
    mirrored = features_of(flip_x(win))

    assert np.isclose(mirrored["open_delta"], original["open_delta"], atol=1e-5)
    assert np.isclose(mirrored["open_range"], original["open_range"], atol=1e-5)


def test_zoom_in_open_delta_duong_zoom_out_am():
    zoom_in = features_of(make_zoom("in"))
    zoom_out = features_of(make_zoom("out"))

    assert zoom_in["open_delta"] > 0
    assert zoom_out["open_delta"] < 0
    assert zoom_in["open_trend"] > 0 > zoom_out["open_trend"]


def test_swipe_straightness_tren_0_8_wave_duoi_0_5():
    """Vuốt đi thẳng; vẫy tay đi rất xa mà dời được rất ít."""
    swipe = features_of(make_swipe(-1))
    wave = features_of(make_wave())

    assert swipe["straightness"] > 0.8
    assert wave["straightness"] < 0.5


def test_features_dung_13_chieu_va_khop_FEATURE_NAMES():
    values = window_features(normalize_window(make_static()), 0.75)

    assert len(FEATURE_NAMES) == 13
    assert values.shape == (13,)
    assert values.dtype == np.float32
    assert len(set(FEATURE_NAMES)) == 13, "tên đặc trưng không được trùng"
    assert dict(zip(FEATURE_NAMES, values))["presence"] == np.float32(0.75)


def test_features_khong_bao_gio_tra_ve_nan():
    """Kể cả khi cửa sổ còn 30% số bước là NaN sau khi vá."""
    rng = np.random.default_rng(config.SEED)
    for make in (make_swipe(+1), make_zoom("out"), make_wave(), make_static()):
        win = make.copy()
        n_missing = int(round(0.3 * config.T))
        # Frame đầu phải còn tay, nếu không thì cửa sổ bị loại từ trước.
        missing = rng.choice(np.arange(1, config.T), size=n_missing,
                             replace=False)
        win[missing] = np.nan
        presence_ratio = 1.0 - n_missing / config.T

        values = window_features(normalize_window(win), presence_ratio)

        assert np.all(np.isfinite(values)), "đặc trưng không được có NaN hay inf"
        assert np.isclose(dict(zip(FEATURE_NAMES, values))["presence"],
                          presence_ratio)
