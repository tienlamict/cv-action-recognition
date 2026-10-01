"""Kiểm thử schema .npz và quy ước lật x — dùng dữ liệu tổng hợp."""

import json
from pathlib import Path

import numpy as np
import pytest

from src import config
from src.io_data import load_clip, save_clip
from tests.fixtures import make_swipe

FPS = 30.0


def build_clip(tmp_path, source="ipn", n_frames=None):
    """Một clip tổng hợp: cửa sổ vuốt, vài frame mất tay, hai đoạn nhãn."""
    win = make_swipe(+1, steps=n_frames or config.T)
    xy_norm = (win / np.array([config.CAM_W, config.CAM_H])).astype(np.float32)
    xy_norm[2] = np.nan                     # một frame mất tay
    present = np.all(np.isfinite(xy_norm.reshape(xy_norm.shape[0], -1)), axis=1)
    ts = np.arange(xy_norm.shape[0], dtype=np.float64) / FPS

    half = xy_norm.shape[0] // 2
    segments = np.array([[0, half, config.CLASSES.index("none")],
                         [half, xy_norm.shape[0],
                          config.CLASSES.index("swipe_left")]], dtype=np.int64)
    meta = {"w": config.CAM_W, "h": config.CAM_H, "fps": FPS, "source": source,
            "subject": "1CM1_1", "clip_id": "clip_thu_nghiem"}

    path = tmp_path / "clip.npz"
    save_clip(path, ts, xy_norm, present, segments, ["D0X", "G05"], meta)
    return path, ts, xy_norm, segments


def test_save_load_clip_khu_hoi(tmp_path):
    """Lưu rồi nạp phải ra đúng những gì đã lưu."""
    path, ts, xy_norm, segments = build_clip(tmp_path, source="self")

    (ts_back, xy_back, w, h, segments_back, src_labels,
     meta) = load_clip(path)

    np.testing.assert_allclose(ts_back, ts)
    np.testing.assert_array_equal(np.isnan(xy_back), np.isnan(xy_norm))
    np.testing.assert_allclose(xy_back[~np.isnan(xy_back)],
                               xy_norm[~np.isnan(xy_norm)], rtol=1e-6)
    np.testing.assert_array_equal(segments_back, segments)
    assert src_labels.tolist() == ["D0X", "G05"]
    assert (w, h) == (config.CAM_W, config.CAM_H)
    assert meta["subject"] == "1CM1_1" and meta["clip_id"] == "clip_thu_nghiem"
    assert meta["flip_applied"] is False, "nguồn self không bao giờ bị lật"


def test_npz_dung_schema(tmp_path):
    """Shape, dtype và ts tăng đơn điệu — đúng mục Hợp đồng dữ liệu."""
    path, ts, xy_norm, _ = build_clip(tmp_path)

    with np.load(path, allow_pickle=False) as data:
        assert data["xy"].dtype == np.float32
        assert data["xy"].shape == (ts.size, config.NUM_LANDMARKS, 2)
        assert data["ts"].dtype == np.float64
        assert data["present"].dtype == np.bool_
        assert data["segments"].dtype == np.int64
        assert data["segments"].shape[1] == 3
        assert data["src_labels"].dtype.kind == "U"
        assert np.all(np.diff(data["ts"]) > 0), "ts phải tăng đơn điệu"
        assert data["ts"][0] == 0.0
        meta = json.loads(str(data["meta"]))

    assert {"w", "h", "fps", "source", "subject", "clip_id"} <= set(meta)

    # Điểm mốc lưu ở dạng THÔ: toạ độ chuẩn hoá [0,1], không phải đã
    # normalize_window (khi đó cổ tay frame đầu sẽ là gốc 0,0).
    with np.load(path, allow_pickle=False) as data:
        xy = data["xy"]
    assert np.nanmin(xy) >= 0.0 and np.nanmax(xy) <= 1.0
    assert not np.allclose(xy[0, config.WRIST], [0.0, 0.0])


def test_lat_x_hai_lan_bang_khong_lat(tmp_path, monkeypatch):
    """Lật hai lần trở về như cũ; y không bao giờ bị đụng tới."""
    path, _, xy_norm, _ = build_clip(tmp_path, source="ipn")

    monkeypatch.setattr(config, "IPN_FLIP_X", 1)
    _, xy_plain, *_ , meta_plain = load_clip(path)
    assert meta_plain["flip_applied"] is False

    monkeypatch.setattr(config, "IPN_FLIP_X", -1)
    _, xy_flipped, *_, meta_flipped = load_clip(path)
    assert meta_flipped["flip_applied"] is True

    twice = xy_flipped.copy()
    twice[..., 0] = 1.0 - twice[..., 0]
    np.testing.assert_allclose(twice[~np.isnan(twice)],
                               xy_plain[~np.isnan(xy_plain)], rtol=1e-6)
    np.testing.assert_allclose(xy_flipped[..., 1][~np.isnan(xy_flipped[..., 1])],
                               xy_plain[..., 1][~np.isnan(xy_plain[..., 1])])


def test_ipn_flip_chi_ap_dung_trong_load_clip():
    """Đọc mã nguồn: ngoài load_clip, không nơi nào dùng IPN_FLIP_X."""
    import inspect

    from src import io_data

    assert "IPN_FLIP_X" in inspect.getsource(io_data.load_clip)

    offenders = []
    for folder in (config.SRC_DIR, config.SCRIPTS_DIR):
        for path in Path(folder).glob("*.py"):
            if path.name in ("config.py", "io_data.py"):
                continue
            if "IPN_FLIP_X" in path.read_text(encoding="utf-8"):
                offenders.append(path.name)
    assert offenders == [], f"IPN_FLIP_X còn xuất hiện ở: {offenders}"


def test_save_clip_bat_loi_shape(tmp_path):
    with pytest.raises(ValueError):
        save_clip(tmp_path / "x.npz", [0.0, 1.0],
                  np.zeros((3, config.NUM_LANDMARKS, 2)), [True] * 2,
                  np.zeros((0, 3)), [], {"w": 1, "h": 1, "source": "ipn"})
