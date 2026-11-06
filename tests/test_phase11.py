"""Kiểm thử Phase 11 — dữ liệu tự quay. Không cần camera: nguồn quay là một video
đen tổng hợp; không đụng data/ hay results/ thật."""

import argparse

import cv2
import numpy as np
import pytest

from src import config, experiments, selfdata
from src.io_video import iter_frames
from tests.fixtures import black_video
from tests.scripts_import import load_script

rec = load_script("record_session")


def test_ten_file_suy_ra_nhan_va_ma_nguoi():
    """Tên file là nhãn (cẩm nang 12.5): mã người, nhãn, số thứ tự; buổi quay là
    thư mục chứa file. Tên sai quy ước hay nhãn lạ bị từ chối, không đoán."""
    clip = selfdata.parse_name("data/raw/2026-11-07/p03_swipe_left_07.mp4")
    assert clip == selfdata.SelfClip("p03", "swipe_left", 7, "2026-11-07")
    assert selfdata.class_of(clip.label) == config.CLASSES.index("swipe_left")
    near = selfdata.parse_name("p12_none-throwup_10.json")
    assert near.label == "none-throwup" and selfdata.class_of(near.label) == 0
    for bad in ("p3_swipe_left_07.mp4", "p03_swipe_up_01.mp4", "p03_swipe_left.mp4",
                "p03_none-dance_01.mp4", "x03_zoom_in_01.mp4"):
        with pytest.raises(ValueError):
            selfdata.parse_name(bad)
    for label in (*selfdata.GESTURES, *selfdata.near_labels(), selfdata.TRANSITION,
                  *selfdata.continuous_labels()):
        name = selfdata.clip_name("p01", label, 3)
        assert selfdata.parse_name(name + ".mp4").label == label
    with pytest.raises(ValueError):
        selfdata.clip_name("p1", "zoom_in", 1)


def test_lich_quay_xao_tron_va_quay_lai_dung_so_con_thieu():
    rng = np.random.default_rng(0)
    plan = selfdata.schedule(selfdata.GESTURES, 3, rng)
    assert sorted(plan) == sorted((g, t) for g in selfdata.GESTURES for t in (1, 2, 3))
    assert [label for label, _ in plan] != sorted(label for label, _ in plan), "phải xáo trộn"
    left = selfdata.schedule(["zoom_in"], 4, rng, {"zoom_in": {1, 3}})
    assert sorted(left) == [("zoom_in", 2), ("zoom_in", 4)]


def test_quay_lai_chuyen_ban_hong_vao_rejected_khong_xoa(tmp_path):
    for n in (1, 2):
        video = tmp_path / "p01_zoom_in_01.mp4"
        video.write_bytes(b"video")
        selfdata.write_sidecar(video, [0.0, 0.1], person="p01")
        assert selfdata.existing_takes(tmp_path, "p01", "zoom_in") == [1]
        moved = selfdata.reject(video)
        assert moved == tmp_path / "rejected" / f"p01_zoom_in_01~{n}.mp4"
        assert moved.is_file() and moved.with_suffix(".json").is_file()
        assert selfdata.existing_takes(tmp_path, "p01", "zoom_in") == []


def args_for(tmp_path, video, **kwargs):
    return argparse.Namespace(**{
        "person": "p01", "session": "buoi1", "takes": 1, "near_takes": 0,
        "transition_takes": 0, "blocks": ["gestures"], "source": str(video),
        "out": tmp_path / "raw", "no_display": True, "no_track": True, **kwargs})


@pytest.fixture
def quick(monkeypatch):
    monkeypatch.setattr(config, "REC_CLIP_SEC", 0.6)
    monkeypatch.setattr(config, "REC_COUNTDOWN_SEC", 0.2)


def test_quay_ghi_video_khong_lat_kem_moc_thoi_gian_that_va_lam_tiep(tmp_path, quick):
    """Bốn cử chỉ, mỗi cử chỉ một lần: bốn video, mỗi video một file mốc thời gian
    có đúng số frame của video, bắt đầu từ 0 và tăng ngặt. Chạy lại: không quay
    thêm gì."""
    video = black_video(tmp_path / "nguon.avi", 6)
    saved = rec.run(args_for(tmp_path, video))
    assert sorted(p.name for p in saved) == sorted(f"p01_{g}_01.mp4" for g in selfdata.GESTURES)
    for path in saved:
        meta = selfdata.read_sidecar(path)
        frames = sum(1 for _ in iter_frames(str(path)))
        assert meta["n_frames"] == frames == len(meta["ts"])
        ts = np.array(meta["ts"])
        assert ts[0] == 0 and np.all(np.diff(ts) > 0)
        assert ts[-1] == pytest.approx(config.REC_CLIP_SEC, abs=1.5 / config.HZ)
        assert (meta["person"], meta["session"], meta["block"]) == ("p01", "buoi1", "gestures")
        assert meta["trim_sec"] == config.REC_TRIM_SEC
    assert rec.run(args_for(tmp_path, video)) == []


def test_het_nguon_giua_luc_quay_thi_ban_do_vao_rejected(tmp_path, quick):
    """Lần 1: đếm ngược 0–0,2 s, quay 0,2–0,8 s. Lần 2 bắt đầu quay ở 1,0 s thì
    video nguồn hết ở 1,33 s: bản dở vào rejected/, và vẫn còn phải quay."""
    video = black_video(tmp_path / "ngan.avi", 1.4)
    saved = rec.run(args_for(tmp_path, video))
    assert len(saved) == 1
    rejected = list((tmp_path / "raw" / "buoi1" / "rejected").glob("*.mp4"))
    assert len(rejected) == 1, "lần quay dở không được tính là đã quay"
    left = rec.program("p01", tmp_path / "raw" / "buoi1", 1, 0, 0, ["gestures"],
                       np.random.default_rng(0))
    assert len(left) == 3


def test_phan_quay_lien_tuc_cat_thanh_file_noi_lien(tmp_path, quick, monkeypatch):
    """Quay liên tục 1,2 giây với file 0,5 giây: ba file 0,5 / 0,5 / 0,2 giây; chỉ
    file đầu có đếm ngược."""
    monkeypatch.setattr(config, "REC_CONTINUOUS_MIN", {"rest": 0.02})
    monkeypatch.setattr(config, "REC_CHUNK_SEC", 0.5)
    items = rec.program("p01", tmp_path, 0, 0, 0, ["continuous"], np.random.default_rng(0))
    assert [(i.label, i.take, i.seconds) for i in items] == [
        ("none-rest", 1, 0.5), ("none-rest", 2, 0.5), ("none-rest", 3, pytest.approx(0.2))]
    assert [i.countdown for i in items] == [config.REC_COUNTDOWN_SEC, 0.0, 0.0]
    video = black_video(tmp_path / "nguon.avi", 3)
    saved = rec.run(args_for(tmp_path, video, blocks=["continuous"]))
    assert [p.name for p in saved] == [f"p01_none-rest_0{k}.mp4" for k in (1, 2, 3)]
    assert selfdata.read_sidecar(saved[0])["trim_sec"] == 0.0


def test_loi_nhac_ascii_vua_khung_va_du_moi_nhan():
    labels = {*selfdata.GESTURES, *selfdata.near_labels(), selfdata.TRANSITION,
              *selfdata.continuous_labels()}
    assert labels == set(selfdata.PROMPTS)
    for text in selfdata.PROMPTS.values():
        assert text.isascii(), text
        (width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE,
                                        config.TEXT_THICKNESS)
        assert config.TEXT_ORIGIN[0] + width < config.CAM_W, text


def test_hang_so_quay_khong_lam_ban_ghi_het_han(monkeypatch):
    """Thí nghiệm Phase 8 chỉ dùng IPN: cách quay dữ liệu tự quay không băm vào."""
    spec = experiments.full_spec({"model": "lstm"})
    assert not any(k.startswith("REC_") for k in experiments.relevant_config())
    base = experiments.record_key(spec, "dữ liệu")
    monkeypatch.setattr(config, "REC_CLIP_SEC", 9.0)
    assert experiments.record_key(spec, "dữ liệu") == base
