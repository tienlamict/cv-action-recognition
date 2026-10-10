"""Kiểm thử đường ống biểu diễn — bộ kiểm thử quan trọng nhất của dự án.

Nó chứng minh hai điều ngược nhau mà chuẩn hoá phải làm cùng lúc: **bất biến**
với chỗ đứng và cỡ bàn tay, nhưng **giữ nguyên** quỹ đạo chuyển động.
"""

import numpy as np
import pytest

from src import config
from src.features import FEATURE_NAMES, window_features
from src.preprocess import (fill_short_gaps, normalize_window, resample,
                            to_pixels)
from tests.fixtures import hand, make_swipe

FPS_IN = 30.0


def _sequence(n_frames, absent=()):
    """Chuỗi ``(ts, xy)`` pixel ở 30 FPS, cổ tay dời đều; ``absent`` là NaN."""
    ts = np.arange(n_frames) / FPS_IN
    xy = np.stack([hand(center=(300.0 + 10.0 * i, 240.0))
                   for i in range(n_frames)])
    xy[list(absent)] = np.nan
    return ts, xy


def test_to_pixels_hai_truc_khac_thang():
    """Hai trục nhân hai hệ số khác nhau, không dùng chung một hệ số."""
    xy_norm = np.array([[[0.5, 0.5], [1.0, 1.0]]])
    xy_px = to_pixels(xy_norm, config.CAM_W, config.CAM_H)

    np.testing.assert_allclose(xy_px[0, 0], [320.0, 240.0])
    np.testing.assert_allclose(xy_px[0, 1], [640.0, 480.0])
    assert xy_px[0, 1, 0] != xy_px[0, 1, 1], "ảnh 640x480 không vuông"


def test_resample_luoi_deu_dung_1_tren_15():
    """Mốc thời gian vào bị rung, lưới ra vẫn đều tuyệt đối."""
    rng = np.random.default_rng(config.SEED)
    n = 60
    jitter = rng.normal(0.0, 0.004, size=n)
    jitter[0] = 0.0
    ts = np.sort(np.arange(n) / FPS_IN + jitter)
    _, xy = _sequence(n)

    grid_ts, xy_grid = resample(ts, xy)

    step = 1.0 / config.HZ
    assert grid_ts[0] == ts[0]
    assert grid_ts[-1] <= ts[-1]
    assert np.abs(np.diff(grid_ts) - step).max() < 1e-12
    assert np.all(np.isfinite(xy_grid))


def test_resample_khong_noi_suy_xuyen_lo_mat_tay():
    """np.interp sẵn sàng nối thẳng qua chỗ mất tay — bước này phải chặn nó."""
    gap = range(20, 35)
    ts, xy = _sequence(60, absent=gap)

    grid_ts, xy_grid = resample(ts, xy)

    inside = (grid_ts >= ts[gap[0]]) & (grid_ts <= ts[gap[-1]])
    assert inside.any(), "cần ít nhất một điểm lưới rơi vào khoảng mất tay"
    assert np.all(np.isnan(xy_grid[inside])), "đã nội suy xuyên qua lỗ mất tay"
    assert np.all(np.isfinite(xy_grid[grid_ts < ts[gap[0] - 1]]))


def test_fill_va_lo_hong_2_buoc_giu_lo_hong_10_buoc():
    xy = np.stack([hand(center=(300.0 + 10.0 * i, 240.0)) for i in range(40)])
    expected = xy.copy()
    xy[5:7] = np.nan         # lỗ 2 bước  -> vá
    xy[20:30] = np.nan       # lỗ 10 bước -> giữ

    filled = fill_short_gaps(xy, max_gap=config.MAX_GAP)

    assert np.all(np.isfinite(filled[5:7])), "lỗ ngắn phải được vá"
    np.testing.assert_allclose(filled[5:7], expected[5:7], atol=1e-9)
    assert np.all(np.isnan(filled[20:30])), "lỗ dài phải giữ NaN"
    assert np.all(np.isnan(xy[20:30])) and np.all(np.isnan(xy[5:7])), \
        "không được sửa mảng đầu vào tại chỗ"


def _fill_tung_cot(xy, max_gap):
    """Thuật toán gốc của fill_short_gaps: tìm và vá đoạn NaN cho TỪNG cột."""
    flat = np.array(xy, dtype=np.float64).reshape(len(xy), -1)
    steps = np.arange(len(flat), dtype=np.float64)
    for column in flat.T:
        missing = ~np.isfinite(column)
        padded = np.diff(np.concatenate(([0], missing.astype(np.int8), [0])))
        for start, stop in zip(np.flatnonzero(padded == 1), np.flatnonzero(padded == -1)):
            if start == 0 or stop == len(flat) or stop - start > max_gap:
                continue
            column[start:stop] = np.interp(steps[start:stop], [start - 1, stop],
                                           [column[start - 1], column[stop]])
    return flat.reshape(np.shape(xy))


def test_fill_gom_theo_kieu_mat_ra_dung_tung_bit_nhu_tung_cot():
    """Bản nhanh (tìm đoạn NaN một lần cho mỗi kiểu mất) phải giống hệt bản vá
    từng cột — kể cả khi các cột mất ở những bước khác nhau."""
    rng = np.random.default_rng(0)
    for _ in range(50):
        xy = rng.normal(300.0, 50.0, size=(40, 21, 2))
        xy[rng.random(40) < 0.15] = np.nan                    # mất cả bước
        xy[rng.random((40, 21, 2)) < 0.03] = np.nan           # mất lẻ từng toạ độ
        np.testing.assert_array_equal(fill_short_gaps(xy, max_gap=config.MAX_GAP),
                                      _fill_tung_cot(xy, config.MAX_GAP))


def test_fill_giu_nan_o_dau_va_cuoi_chuoi():
    """Đoạn chạm đầu hoặc cuối chuỗi không có đủ hai đầu mút để nội suy."""
    xy = np.stack([hand(center=(300.0 + 10.0 * i, 240.0)) for i in range(20)])
    xy[:2] = np.nan
    xy[-2:] = np.nan

    filled = fill_short_gaps(xy, max_gap=config.MAX_GAP)

    assert np.all(np.isnan(filled[:2]))
    assert np.all(np.isnan(filled[-2:]))
    assert np.all(np.isfinite(filled[2:-2]))


def test_normalize_bat_bien_voi_tinh_tien():
    """Dời cả cửa sổ 137 px thì biểu diễn không đổi."""
    win = make_swipe(+1)
    moved = win + 137.0

    np.testing.assert_allclose(normalize_window(win), normalize_window(moved),
                               atol=1e-5)


def test_normalize_bat_bien_voi_ti_le():
    """Ngồi gần camera hơn 1,6 lần thì biểu diễn cũng không đổi."""
    win = make_swipe(+1)
    zoomed = win * 1.6

    np.testing.assert_allclose(normalize_window(win), normalize_window(zoomed),
                               atol=1e-5)


def test_normalize_giu_quy_dao():
    """Bất biến với vị trí và cỡ, nhưng KHÔNG được xoá quỹ đạo."""
    win_norm = normalize_window(make_swipe(+1))
    features = dict(zip(FEATURE_NAMES, window_features(win_norm, 1.0)))

    assert abs(features["dx"]) > 2.0, "cú vuốt phải còn nguyên độ dời ngang"


def test_normalize_nem_loi_khi_frame_dau_mat_tay():
    win = make_swipe(+1)
    win[0, config.WRIST] = np.nan

    with pytest.raises(ValueError):
        normalize_window(win)


def test_normalize_dat_goc_va_don_vi_theo_frame_dau():
    """Frame đầu: cổ tay về gốc, cỡ lòng bàn tay thành 1."""
    win_norm = normalize_window(make_swipe(+1))

    np.testing.assert_allclose(win_norm[0, config.WRIST], [0.0, 0.0],
                               atol=1e-12)
    assert np.isclose(np.linalg.norm(win_norm[0, config.MIDDLE_MCP]), 1.0)
    # Các frame sau KHÔNG bị kéo về gốc — đó mới là chỗ giữ quỹ đạo.
    assert np.linalg.norm(win_norm[-1, config.WRIST]) > 1.0


def test_normalize_tu_choi_long_ban_tay_frame_dau_bat_thuong():
    """Lòng bàn tay frame đầu ngắn hơn NORM_MIN_PALM_RATIO lần trung vị của
    cửa sổ thì đơn vị không tin được — không được phóng to cả cửa sổ."""
    win = make_swipe(+1)
    squashed = win.copy()
    wrist = squashed[0, config.WRIST]
    squashed[0] = wrist + (squashed[0] - wrist) * 0.3   # tay nghiêng cạnh
    with pytest.raises(ValueError, match="bất thường"):
        normalize_window(squashed)

    mild = win.copy()
    mild[0] = wrist + (mild[0] - wrist) * 0.8
    normalize_window(mild)                               # vẫn chấp nhận
