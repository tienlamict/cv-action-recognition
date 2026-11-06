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


SPACE, PAUSE, REDO = ord(" "), ord("p"), ord("r")


def presser(take_sec, extra=None):
    """Người bấm giả: đang nghỉ thì bấm SPACE; đang quay được ``take_sec`` giây thì
    bấm SPACE. ``extra``: ``(số giây, phím)`` của lần quay ĐẦU — bấm thêm một
    phím khác ở thời điểm đó, đúng một lần."""
    pending = list(extra or [])

    def keys(ts, state, elapsed):
        if pending and state == "record" and elapsed >= pending[0][0]:
            return pending.pop(0)[1]
        if state == "idle" or elapsed >= take_sec:
            return SPACE
        return -1
    return keys


@pytest.fixture
def quick(monkeypatch):
    monkeypatch.setattr(config, "REC_MIN_CLIP_SEC", 0.3)


def test_space_luu_lan_nay_va_bat_dau_ngay_lan_sau(tmp_path, quick):
    """Bốn cử chỉ, mỗi cử chỉ một lần, người quay bấm SPACE sau 0,8 giây. Bốn video,
    mỗi video kèm file mốc thời gian có đúng số frame, bắt đầu từ 0, tăng ngặt.
    Lần sau bắt đầu ngay frame kế tiếp của lần trước — không có khoảng hở. Chạy
    lại: không quay thêm gì."""
    video = black_video(tmp_path / "nguon.avi", 6)
    saved = rec.run(args_for(tmp_path, video), keys=presser(0.8))
    assert len(saved) == 4
    assert {selfdata.parse_name(p).label for p in saved} == set(selfdata.GESTURES)
    metas = [selfdata.read_sidecar(p) for p in saved]
    for path, meta in zip(saved, metas):
        frames = sum(1 for _ in iter_frames(str(path)))
        assert meta["n_frames"] == frames == len(meta["ts"])
        ts = np.array(meta["ts"])
        assert ts[0] == 0 and np.all(np.diff(ts) > 0)
        assert ts[-1] == pytest.approx(0.8, abs=1.5 / config.HZ)
        assert (meta["person"], meta["session"], meta["block"]) == ("p01", "buoi1", "gestures")
        assert meta["trim_sec"] == config.REC_TRIM_SEC
    for before, after in zip(metas, metas[1:]):
        gap = after["stream_ts0"] - (before["stream_ts0"] + before["ts"][-1])
        assert gap == pytest.approx(1 / config.HZ, abs=1e-3), "SPACE nối liền hai lần quay"
    assert rec.run(args_for(tmp_path, video), keys=presser(0.8)) == []


def test_bam_space_qua_nhanh_hay_r_thi_quay_lai_dung_lan_do(tmp_path, quick):
    """SPACE ở 0,2 giây (dưới REC_MIN_CLIP_SEC) là bấm nhầm; r ở 0,5 giây là bỏ lần
    đang quay. Cả hai: bản bỏ đi vào rejected/, lần đó quay lại, vẫn đủ bốn video."""
    for extra in ([(0.2, SPACE)], [(0.5, REDO)]):
        root = tmp_path / ("space" if extra[0][1] == SPACE else "redo")
        video = black_video(tmp_path / "nguon.avi", 8)
        saved = rec.run(args_for(root, video), keys=presser(0.8, extra))
        assert len(saved) == 4
        rejected = list((root / "raw" / "buoi1" / "rejected").glob("*.mp4"))
        assert len(rejected) == 1
        assert selfdata.parse_name(rejected[0].with_name(rejected[0].name.split("~")[0] + ".mp4")
                                   ).label == selfdata.parse_name(saved[0]).label


def test_p_luu_roi_nghi_space_quay_tiep(tmp_path, quick):
    """p ở 0,8 giây: lần đầu được lưu, máy chuyển sang nghỉ; SPACE quay tiếp."""
    states = []

    def keys(ts, state, elapsed):
        states.append(state)
        if state == "record" and elapsed >= 0.8:
            return PAUSE if states.count("idle") == 1 else SPACE
        return SPACE if state == "idle" else -1

    video = black_video(tmp_path / "nguon.avi", 8)
    saved = rec.run(args_for(tmp_path, video), keys=keys)
    assert len(saved) == 4
    assert states.count("idle") >= 2, "sau p phải có lúc nghỉ"


def test_het_nguon_giua_luc_quay_thi_ban_do_vao_rejected(tmp_path, quick):
    """Lần 1 lưu ở 0,8 giây, lần 2 quay dở khi video nguồn hết: bản dở vào
    rejected/, và lần đó vẫn còn phải quay."""
    video = black_video(tmp_path / "ngan.avi", 1.4)
    saved = rec.run(args_for(tmp_path, video), keys=presser(0.8))
    assert len(saved) == 1
    rejected = list((tmp_path / "raw" / "buoi1" / "rejected").glob("*.mp4"))
    assert len(rejected) == 1, "lần quay dở không được tính là đã quay"
    left = rec.program("p01", tmp_path / "raw" / "buoi1", 1, 0, 0, ["gestures"],
                       np.random.default_rng(0))
    assert len(left) == 3


def test_phan_quay_lien_tuc_cat_thanh_file_noi_lien(tmp_path, quick, monkeypatch):
    """Quay liên tục 1,2 giây với file 0,5 giây: một lần SPACE, ba file 0,5 / 0,5 /
    0,2 giây nối liền nhau."""
    monkeypatch.setattr(config, "REC_CONTINUOUS_MIN", {"rest": 0.02})
    monkeypatch.setattr(config, "REC_CHUNK_SEC", 0.5)
    items = rec.program("p01", tmp_path, 0, 0, 0, ["continuous"], np.random.default_rng(0))
    assert [(i.label, i.take, i.seconds) for i in items] == [
        ("none-rest", 1, 0.5), ("none-rest", 2, 0.5), ("none-rest", 3, pytest.approx(0.2))]
    pressed = []

    def keys(ts, state, elapsed):
        if state == "idle":
            pressed.append(ts)
            return SPACE
        return -1

    video = black_video(tmp_path / "nguon.avi", 3)
    saved = rec.run(args_for(tmp_path, video, blocks=["continuous"]), keys=keys)
    assert [p.name for p in saved] == [f"p01_none-rest_0{k}.mp4" for k in (1, 2, 3)]
    assert len(pressed) == 1, "các file sau nối liền, không chờ phím"
    assert selfdata.read_sidecar(saved[0])["trim_sec"] == 0.0


def test_qua_lau_thi_man_hinh_nhac_luu():
    item = rec.Item("gestures", "zoom_in", 3, None)
    lines, big = rec.screen(item, 0, 10, "record", config.REC_MAX_CLIP_SEC + 1, "")
    assert big.startswith("REC") and any("SPACE de luu" in line for line in lines)
    assert all(line.isascii() for line in lines)


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
    monkeypatch.setattr(config, "REC_MAX_CLIP_SEC", 99.0)
    assert experiments.record_key(spec, "dữ liệu") == base
