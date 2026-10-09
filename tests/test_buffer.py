"""Kiểm thử TimeBuffer và vòng dự đoán — không webcam, không data/."""

import numpy as np
import pytest

from src import config
from src.buffer import TimeBuffer
from src.live import (LivePredictor, PRACTICE_CLASSES, count_episodes,
                      practice_status, screen_lines)
from src.features import FEATURE_NAMES
from tests.fixtures import make_static

W, H = config.CAM_W, config.CAM_H


def static_norm(n, seed=0):
    return make_static(n, seed=seed) / np.array([W, H])


def fill(buffer, fps, seconds, missing=()):
    """Đẩy ``seconds`` giây frame tay đứng yên ở ``fps``; frame có chỉ số trong
    ``missing`` là mất tay (NaN, vẫn đẩy vào — luật 4)."""
    n = int(round(seconds * fps))
    xy = static_norm(n)
    for i in range(n):
        frame = np.full((21, 2), np.nan) if i in missing else xy[i]
        buffer.push(i / fps, frame, W, H)
    return n


def test_timebuffer_tra_ve_dung_T_buoc():
    buffer = TimeBuffer()
    fill(buffer, fps=30, seconds=2.0)
    win, presence = buffer.window()
    assert win.shape == (config.T, config.NUM_LANDMARKS, 2)
    assert presence == 1.0
    assert np.nanmax(win) > 100, "cửa sổ ở toạ độ pixel, chưa chuẩn hoá"


def test_timebuffer_tra_ve_none_khi_presence_duoi_MIN_PRESENCE():
    buffer = TimeBuffer()
    fill(buffer, fps=30, seconds=0.5)
    assert buffer.window() is None, "chưa đủ T bước"

    buffer = TimeBuffer()
    n = int(2.0 * 30)
    # mất tay 0,5 s liền ngay trước hiện tại: quá MAX_GAP nên giữ NaN
    fill(buffer, fps=30, seconds=2.0, missing=set(range(n - 15, n)))
    assert buffer.window() is None

    buffer = TimeBuffer()
    fill(buffer, fps=30, seconds=2.0, missing=set(range(n - 37, n - 35)))
    assert buffer.window() is not None, "lỗ 2 frame được vá, cửa sổ vẫn hợp lệ"


def test_timebuffer_giu_theo_thoi_gian_khong_theo_so_frame():
    """30 FPS hay 10 FPS thì bộ đệm vẫn giữ đúng WIN_SEC + BUFFER_EXTRA_SEC
    giây, và cửa sổ vẫn là T bước = WIN_SEC giây."""
    keep = config.WIN_SEC + config.BUFFER_EXTRA_SEC
    for fps in (30, 10):
        buffer = TimeBuffer()
        fill(buffer, fps=fps, seconds=4.0)
        assert len(buffer) == pytest.approx(keep * fps + 1, abs=1)
        win, _ = buffer.window()
        assert win.shape[0] == config.T


def test_timebuffer_tu_choi_ts_khong_tang():
    buffer = TimeBuffer()
    buffer.push(1.0, static_norm(1)[0], W, H)
    with pytest.raises(ValueError):
        buffer.push(1.0, static_norm(1)[0], W, H)


def test_live_du_doan_dung_nhip_STRIDE_SEC():
    calls = []

    def model(features):
        calls.append(features)
        return 0, 1.0

    predictor = LivePredictor(model)
    xy = static_norm(90)
    preds = [p for i in range(90)
             if (p := predictor.update(i / 30, xy[i], W, H)) is not None]
    gaps = np.diff([p.ts for p in preds])
    np.testing.assert_allclose(gaps, config.STRIDE_SEC, atol=1 / 30 + 1e-9)
    assert any(p.label is None for p in preds), "lúc đầu chưa đủ cửa sổ → '-'"
    assert len(calls) == sum(p.label is not None for p in preds)


def test_live_nap_san_mo_hinh_truoc_vong_lap():
    """Mô hình có ``load()`` được nạp ngay khi tạo LivePredictor, không phải ở
    lần dự đoán đầu (lúc đó demo sẽ đứng hình)."""
    class Lazy:
        loaded = False

        def load(self):
            self.loaded = True

        def __call__(self, features):
            return 0, 1.0

    model = Lazy()
    LivePredictor(model)
    assert model.loaded
    LivePredictor(lambda features: (0, 1.0))      # hàm thường: không có load, không lỗi


def test_dem_dot_bao_lien_nhau_cung_lop():
    labels = [0, 1, 1, 1, 0, None, 1, 3, 3, 0, 4]
    assert count_episodes(labels) == {"swipe_left": 2, "swipe_right": 0,
                                      "zoom_in": 1, "zoom_out": 1}


def test_man_hinh_luyen_tap_to_mau_va_chi_dung_ascii():
    features = np.zeros(len(FEATURE_NAMES), dtype=np.float32)
    features[FEATURE_NAMES.index("pinch_delta")] = 1.0
    box = {"p25": 0.5, "p75": 1.5}
    ranges = {c: {n: box for n in config.SHOW_FEATURES} for c in PRACTICE_CLASSES}

    status = practice_status(features, ranges, "zoom_in")
    assert [s[0] for s in status] == list(config.SHOW_FEATURES)
    assert [s[4] for s in status] == [True, False, False]

    from src.live import Prediction
    pred = Prediction(1.0, 3, 0.8, 0.9, features)
    lines, colors, big = screen_lines(pred, 29.5, ranges, "zoom_in")
    assert big.startswith("zoom_in")
    assert len(lines) == len(colors)
    assert config.COLOR_IN_RANGE in colors and config.COLOR_OUT_RANGE in colors
    assert all(text.isascii() for text in lines + [big]), "cv2.putText chỉ vẽ ASCII"
