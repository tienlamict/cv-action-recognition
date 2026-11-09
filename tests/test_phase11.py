"""Kiểm thử Phase 11 — dữ liệu tự quay. Không cần camera: nguồn quay là một video
đen tổng hợp; không đụng data/ hay results/ thật."""

import argparse
import json

import cv2
import numpy as np
import pytest

from src import config, experiments, selfdata
from src.io_video import iter_frames
from src.splits import check_self_split
from src.windows import core_times
from tests.fixtures import CENTER, OPEN_TIGHT, PALM_PX, black_video, hand
from tests.scripts_import import load_script

rec = load_script("record_session")
split_self = load_script("split_self")
extract = load_script("extract_landmarks")
build_self = load_script("build_self_dataset")
train_self = load_script("train_self")
compare = load_script("compare_self")


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


START, STOP, REDO = config.REC_START_KEY, config.REC_STOP_KEY, config.REC_REDO_KEY


def presser(take_sec, extra=None):
    """Người bấm giả: đang nghỉ thì bấm phím bắt đầu; đang quay được ``take_sec`` giây
    thì bấm SPACE. ``extra``: ``(số giây, phím)`` của lần quay ĐẦU — bấm thêm một
    phím khác ở thời điểm đó, đúng một lần."""
    pending = list(extra or [])

    def keys(ts, state, elapsed):
        if pending and state == "record" and elapsed >= pending[0][0]:
            return pending.pop(0)[1]
        if state == "idle":
            return START
        return STOP if elapsed >= take_sec else -1
    return keys


@pytest.fixture
def quick(monkeypatch):
    monkeypatch.setattr(config, "REC_MIN_CLIP_SEC", 0.3)


def test_phim_bat_dau_space_ket_thuc_roi_may_nghi(tmp_path, quick):
    """Người dùng chọn 2026-11-07: mỗi lần quay bấm b để bắt đầu, SPACE để kết thúc.
    Bốn cử chỉ, mỗi lần 0,8 giây: bốn video, mỗi video kèm file mốc thời gian đúng số
    frame, bắt đầu từ 0, tăng ngặt. Kết thúc xong máy luôn nghỉ, lần sau chỉ bắt đầu
    khi bấm b. Chạy lại: không quay thêm gì."""
    states = []
    base = presser(0.8)

    def keys(ts, state, elapsed):
        states.append(state)
        return base(ts, state, elapsed)

    video = black_video(tmp_path / "nguon.avi", 6)
    saved = rec.run(args_for(tmp_path, video), keys=keys)
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
        assert gap == pytest.approx(2 / config.HZ, abs=1e-3), "có một frame nghỉ, rồi mới b"
    runs = "".join("i" if s == "idle" else "r" for s in states)
    assert runs.count("ri") == 3, "nghỉ sau mỗi lần quay, trừ lần cuối buổi"
    assert rec.run(args_for(tmp_path, video), keys=presser(0.8)) == []


def test_ket_thuc_qua_nhanh_hay_r_thi_bo_lan_do_va_cho_bat_dau(tmp_path, quick):
    """SPACE ở 0,2 giây (dưới REC_MIN_CLIP_SEC) là bấm nhầm; r ở 0,5 giây là bỏ lần
    đang quay. Cả hai: bản bỏ đi vào rejected/, máy nghỉ, b quay lại đúng lần đó;
    vẫn đủ bốn video."""
    for extra in ([(0.2, STOP)], [(0.5, REDO)]):
        root = tmp_path / ("space" if extra[0][1] == STOP else "redo")
        video = black_video(tmp_path / "nguon.avi", 8)
        saved = rec.run(args_for(root, video), keys=presser(0.8, extra))
        assert len(saved) == 4
        rejected = list((root / "raw" / "buoi1" / "rejected").glob("*.mp4"))
        assert len(rejected) == 1
        assert selfdata.parse_name(rejected[0].with_name(rejected[0].name.split("~")[0] + ".mp4")
                                   ).label == selfdata.parse_name(saved[0]).label


def test_quen_tay_space_luc_nghi_hay_b_luc_quay_khong_lam_gi(tmp_path, quick):
    """SPACE lúc đang nghỉ không bắt đầu quay; b lúc đang quay không cắt lần đó. Phím
    viết hoa (Caps Lock bật) vẫn được nhận."""
    states = []

    def keys(ts, state, elapsed):
        states.append(state)
        if state == "idle":
            return STOP if states.count("idle") <= 3 else ord(chr(START).upper())
        if 0.3 <= elapsed < 0.5:
            return START
        return STOP if elapsed >= 0.8 else -1

    video = black_video(tmp_path / "nguon.avi", 8)
    saved = rec.run(args_for(tmp_path, video), keys=keys)
    assert len(saved) == 4
    assert states[:5] == ["idle"] * 4 + ["record"], "SPACE lúc nghỉ không bắt đầu"
    for path in saved:
        assert selfdata.read_sidecar(path)["ts"][-1] == pytest.approx(0.8, abs=1.5 / config.HZ)


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
    """Quay liên tục 1,2 giây với file 0,5 giây: một lần bấm b, ba file 0,5 / 0,5 /
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
            return START
        return -1

    video = black_video(tmp_path / "nguon.avi", 3)
    saved = rec.run(args_for(tmp_path, video, blocks=["continuous"]), keys=keys)
    assert [p.name for p in saved] == [f"p01_none-rest_0{k}.mp4" for k in (1, 2, 3)]
    assert len(pressed) == 1, "các file sau nối liền, không chờ phím"
    assert selfdata.read_sidecar(saved[0])["trim_sec"] == 0.0


def test_nguoi_khac_mac_dinh_chi_quay_bon_cu_chi(tmp_path):
    """Người dùng chốt 2026-11-06: chủ đề tài quay đủ bốn khối; p02 trở đi chỉ quay bốn
    cử chỉ, ít lần hơn. --takes và --blocks vẫn đè được."""
    main = rec.parse_args(["--person", config.REC_MAIN_PERSON])
    assert (main.takes, main.blocks) == (config.REC_GESTURE_TAKES, list(rec.BLOCKS))
    helper = rec.parse_args(["--person", "p02"])
    assert helper.blocks == ["gestures"]
    assert helper.takes == config.REC_HELPER_TAKES < config.REC_GESTURE_TAKES
    items = rec.program("p02", tmp_path, helper.takes, helper.near_takes,
                        helper.transition_takes, helper.blocks, np.random.default_rng(0))
    assert len(items) == len(selfdata.GESTURES) * helper.takes
    assert {item.block for item in items} == {"gestures"}
    custom = rec.parse_args(["--person", "p03", "--takes", "20", "--blocks", "gestures", "near"])
    assert (custom.takes, custom.blocks) == (20, ["gestures", "near"])


def test_qua_lau_thi_man_hinh_nhac_luu():
    item = rec.Item("gestures", "zoom_in", 3, None)
    lines, big, colors = rec.screen(item, 0, 10, "record", config.REC_MAX_CLIP_SEC + 1, "")
    assert big.startswith("REC") and len(colors) == len(lines)
    note = next(i for i, line in enumerate(lines) if "SPACE de ket thuc" in line)
    assert colors[note] == config.COLOR_ALERT
    assert all(line.isascii() for line in lines)


# --- Kiểm tra từng lần quay cử chỉ -------------------------------------------------

def smooth_step(t, at, size, dur):
    """Một cú chuyển động trơn: 0 trước ``at - dur/2``, ``size`` sau ``at + dur/2``."""
    u = np.clip((t - at) / dur + 0.5, 0.0, 1.0)
    return size * u * u * (3 - 2 * u)


def hand_at(label, amount):
    """Bàn tay mẫu, toạ độ chuẩn hoá. Vuốt: cổ tay dời ``amount`` lòng bàn tay theo
    x. Zoom: xoè thêm ``amount`` tính từ chụm."""
    if label.startswith("swipe"):
        px = hand(center=(CENTER[0] + amount * PALM_PX, CENTER[1]))
    else:
        px = hand(openness=OPEN_TIGHT + amount)
    return px / np.array([config.CAM_W, config.CAM_H])


def synthetic_take(label, seconds, strokes, missing=None, seed=0):
    """Một lần quay tổng hợp ở ``CAM_FPS``, rung 0,3 px như điểm mốc thật.

    Args:
        strokes: list ``(giây, cỡ, độ dài)``, mỗi phần một cú :func:`smooth_step`.
        missing: ``(từ, đến)`` giây mất tay.

    Returns:
        ``(ts, xy_norm)``.
    """
    ts = np.arange(int(round(seconds * config.CAM_FPS))) / config.CAM_FPS
    xy = np.stack([hand_at(label, sum(smooth_step(t, *s) for s in strokes)) for t in ts])
    rng = np.random.default_rng(seed)
    xy = xy + rng.normal(0.0, 0.3, xy.shape) / np.array([config.CAM_W, config.CAM_H])
    if missing is not None:
        xy[(ts >= missing[0]) & (ts < missing[1])] = np.nan
    return ts, xy.astype(np.float32)


def check(label, seconds, strokes, **kwargs):
    ts, xy = synthetic_take(label, seconds, strokes, **kwargs)
    return selfdata.check_take(ts, xy, config.CAM_W, config.CAM_H, label, config.REC_TRIM_SEC)


def test_lan_quay_ro_rang_thi_khong_bao_va_dung_khoanh_khac_cua_gan_nhan():
    """Một cú vuốt rõ ở giữa lần quay: không báo gì. Khoảnh khắc chính của phép kiểm
    tra đúng là khoảnh khắc mà việc gán nhãn chọn (windows.core_times) — cùng hàm,
    không phải bản "gần giống"."""
    for label, strokes in (("swipe_left", [(1.5, 2.0, 0.3)]),
                           ("zoom_in", [(1.5, 0.8, 0.25)]),
                           ("zoom_out", [(-1.0, 0.8, 0.1), (1.5, -0.8, 0.25)])):
        result = check(label, 3.0, strokes)
        assert result.problem is None, (label, result)
        assert result.core_sec == pytest.approx(1.5, abs=0.1)
        assert result.ratio < config.REC_CORE_RATIO_MAX and result.n_windows >= 1
        ts, xy = synthetic_take(label, 3.0, strokes)
        segments, src = selfdata.clip_segments(label, ts, config.REC_TRIM_SEC)
        labeled = core_times(ts, xy, config.CAM_W, config.CAM_H, segments, src)[0]
        assert result.core_sec == round(labeled, 3)


def test_chuan_bi_manh_ngang_cu_chi_thi_bao_chua_ro():
    """Đúng lỗi của buổi quay thử: kéo tay ngược chiều trước khi vuốt, hay mở các ngón
    trước khi chụm — mạnh gần bằng cử chỉ, cách xa hơn REC_CORE_SEP_SEC."""
    swipe = check("swipe_left", 3.0, [(1.0, -1.8, 0.3), (2.0, 2.0, 0.3)])
    assert swipe.problem == "unclear" and swipe.ratio >= config.REC_CORE_RATIO_MAX
    assert swipe.core_sec == pytest.approx(2.0, abs=0.1), "cử chỉ thật vẫn mạnh hơn"
    zoom = check("zoom_out", 3.0, [(1.0, 0.8, 0.25), (2.0, -0.8, 0.25)])
    assert zoom.problem == "unclear"


def test_cu_chi_roi_vao_phan_bo_dau_hay_cuoi_thi_bao_som_hay_muon():
    """Phần đầu và cuối REC_TRIM_SEC không gán nhãn. Cú vuốt thật nằm ở đó thì việc gán
    nhãn sẽ chọn một cử động nhỏ trong đoạn: làm ngay khi vừa bắt đầu quay là ``early``,
    bấm SPACE ngay sau cử chỉ là ``late``."""
    early = check("swipe_right", 3.0, [(0.25, -2.0, 0.3), (2.0, -0.3, 0.3)])
    assert early.problem == "early" and early.rival_sec < config.REC_TRIM_SEC
    late = check("swipe_right", 3.0, [(1.2, -0.3, 0.3), (2.8, -2.0, 0.3)])
    assert late.problem == "late" and late.rival_sec > 3.0 - config.REC_TRIM_SEC
    assert early.ratio > 1 and late.ratio > 1


def test_mat_tay_hay_qua_ngan_thi_bao():
    """Mất tay cả đoạn: không có khoảnh khắc chính. Lần quay ngắn hơn một cửa sổ: có
    khoảnh khắc chính nhưng không cắt được cửa sổ nào mang nhãn cử chỉ."""
    lost = check("zoom_in", 3.0, [(1.5, 0.8, 0.25)], missing=(0.4, 2.7))
    assert lost.problem == "no_hand" and lost.core_sec is None
    short = check("zoom_in", config.WIN_SEC - 0.1, [(0.55, 0.8, 0.1)])
    assert short.problem == "no_window" and short.n_windows == 0
    with pytest.raises(ValueError):
        check("none-wave", 3.0, [])


def test_doan_gan_nhan_bo_hai_dau_cu_chi_con_none_lay_ca_lan():
    ts = np.arange(90) / 30.0                       # 3 giây
    (seg,), src = selfdata.clip_segments("zoom_out", ts, 0.5)
    assert ts[seg[0]] == pytest.approx(0.5) and ts[seg[1] - 1] <= ts[-1] - 0.5
    assert seg[2] == config.CLASSES.index("zoom_out") and src[0] == "zoom_out"
    (seg,), src = selfdata.clip_segments("none-wave", ts, 0.5)
    assert tuple(seg) == (0, 90, 0) and src[0] == "none-wave"
    (seg,), _ = selfdata.clip_segments("swipe_left", ts[:20], 0.5)
    assert seg[1] >= seg[0], "lần quay quá ngắn: đoạn rỗng, không âm"


def test_loi_bao_ascii_vua_khung():
    item = rec.Item("gestures", "swipe_left", 1, None)
    texts = list(selfdata.CHECK_NOTES.values())
    for state, alert in (("idle", False), ("idle", True), ("record", False)):
        texts += rec.screen(item, 0, 100, state, 1.0, "", alert)[0]
    texts += rec.screen(None, 100, 100, "idle", 0.0, selfdata.CHECK_NOTES["late"], True)[0]
    for text in texts:
        assert text.isascii(), text
        (width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE,
                                        config.TEXT_THICKNESS)
        assert config.TEXT_ORIGIN[0] + width < config.CAM_W, text


class FakeTracker:
    """Thay MediaPipe: bàn tay tổng hợp theo thời gian của luồng quay."""

    def __init__(self, label="swipe_left", strokes=()):
        self.label, self.strokes = label, list(strokes)
        self.rng = np.random.default_rng(0)

    def process(self, frame_bgr, ts_ms):
        t = ts_ms / 1000.0
        xy = hand_at(self.label, sum(smooth_step(t, *s) for s in self.strokes))
        xy = xy + self.rng.normal(0.0, 0.3, xy.shape) / np.array([config.CAM_W, config.CAM_H])
        return xy.astype(np.float32), True, 1.0

    def close(self):
        pass


def scripted_checks(monkeypatch, flag_calls):
    """Thay check_take: lần gọi thứ ``n`` (đếm từ 1) trong ``flag_calls`` bị báo
    ``unclear``, các lần khác ổn. Returns: list tham số của từng lần gọi."""
    calls = []

    def fake(ts, xy, w, h, label, trim_sec):
        calls.append((np.asarray(ts), np.asarray(xy), label, trim_sec))
        problem = "unclear" if len(calls) in flag_calls else None
        return selfdata.TakeCheck(problem, 1.0, 2.0, 0.9 if problem else 0.1, 4)

    monkeypatch.setattr(selfdata, "check_take", fake)
    return calls


def idle_keys(take_sec, plan=None):
    """Người bấm giả: đang quay ``take_sec`` giây thì SPACE. Ở frame đầu của đoạn nghỉ
    thứ ``k`` (đếm từ 0 = đầu buổi; đoạn ``k`` là sau lần quay thứ ``k``) bấm
    ``plan[k]`` nếu có; còn lại bấm phím bắt đầu."""
    plan, states, runs = dict(plan or {}), [], [-1]

    def keys(ts, state, elapsed):
        fresh = state == "idle" and (not states or states[-1] != "idle")
        states.append(state)
        if state == "record":
            return STOP if elapsed >= take_sec else -1
        if fresh:
            runs[0] += 1
            return plan.pop(runs[0], START)
        return START
    return keys


def test_lan_quay_bi_bao_r_quay_lai_dung_lan_do(tmp_path, quick, monkeypatch):
    """Lần 1 bị báo; lúc máy nghỉ, r chuyển lần 1 vào rejected/ và xếp lại đúng lần đó
    để b quay lại. check_take nhận đúng nhãn, REC_TRIM_SEC, mốc thời gian tăng ngặt và
    điểm mốc (n, 21, 2)."""
    calls = scripted_checks(monkeypatch, {1})
    video = black_video(tmp_path / "nguon.avi", 8)
    saved = rec.run(args_for(tmp_path, video), keys=idle_keys(0.8, {1: REDO}),
                    tracker=FakeTracker())
    assert len(saved) == 4 and len(calls) == 5
    first = calls[0][2]
    rejected = list((tmp_path / "raw" / "buoi1" / "rejected").glob("*.mp4"))
    assert [p.name for p in rejected] == [f"p01_{first}_01~1.mp4"]
    assert selfdata.read_sidecar(rejected[0])["live_check"]["problem"] == "unclear"
    assert calls[1][2] == first, "lần quay ngay sau r là đúng lần bị báo"
    redo = next(p for p in saved if selfdata.parse_name(p).label == first)
    assert selfdata.read_sidecar(redo)["live_check"]["problem"] is None
    for ts, xy, label, trim in calls:
        assert label in selfdata.GESTURES and trim == config.REC_TRIM_SEC
        assert np.all(np.diff(ts) > 0) and xy.shape == (ts.size, config.NUM_LANDMARKS, 2)


def test_lan_cuoi_bi_bao_van_cho_quay_lai(tmp_path, quick, monkeypatch):
    """Lần cuối buổi bị báo: máy không thoát mà chờ. r quay lại đúng lần đó; SPACE giữ
    lần đó và kết thúc buổi."""
    calls = scripted_checks(monkeypatch, {4})
    video = black_video(tmp_path / "nguon.avi", 8)
    saved = rec.run(args_for(tmp_path, video), keys=idle_keys(0.8, {4: REDO}),
                    tracker=FakeTracker())
    assert len(saved) == 4 and len(calls) == 5
    rejected = list((tmp_path / "raw" / "buoi1" / "rejected").glob("*.mp4"))
    assert [p.name for p in rejected] == [f"p01_{calls[3][2]}_01~1.mp4"]

    calls = scripted_checks(monkeypatch, {4})
    root = tmp_path / "giu"
    saved = rec.run(args_for(root, video), keys=idle_keys(0.8, {4: STOP}),
                    tracker=FakeTracker())
    assert len(saved) == 4 and len(calls) == 4
    assert selfdata.read_sidecar(saved[-1])["live_check"]["problem"] == "unclear"
    assert not (root / "raw" / "buoi1" / "rejected").exists()


def test_kiem_tra_chay_tren_diem_moc_luc_quay(tmp_path, quick):
    """Không thay check_take: điểm mốc theo dõi lúc quay đi thẳng vào phép kiểm tra.
    Lần 1 (0–2,4 s) có một cử chỉ rõ thì không bị báo; có cú chuẩn bị mạnh ngang thì
    file mốc thời gian ghi lý do."""
    first = rec.program("p01", tmp_path / "trong", 1, 0, 0, ["gestures"],
                        np.random.default_rng(config.SEED + 1))[0].label   # đúng lịch của run
    if first.startswith("swipe"):
        variants = (("ro", [(1.2, 2.0, 0.3)]), ("chua_ro", [(0.9, -1.8, 0.3), (1.7, 2.0, 0.3)]))
    else:
        variants = (("ro", [(1.2, 0.8, 0.25)]),
                    ("chua_ro", [(0.9, 0.8, 0.25), (1.7, -0.8, 0.25)]))
    video = black_video(tmp_path / "nguon.avi", 12)
    outcomes = {}
    for name, strokes in variants:
        root = tmp_path / name
        saved = rec.run(args_for(root, video), keys=idle_keys(2.4),
                        tracker=FakeTracker(first, strokes))
        assert selfdata.parse_name(saved[0]).label == first
        outcomes[name] = selfdata.read_sidecar(saved[0])["live_check"]["problem"]
    assert outcomes == {"ro": None, "chua_ro": "unclear"}


def test_loi_nhac_ascii_vua_khung_va_du_moi_nhan():
    labels = {*selfdata.GESTURES, *selfdata.near_labels(), selfdata.TRANSITION,
              *selfdata.continuous_labels()}
    assert labels == set(selfdata.PROMPTS)
    for text in selfdata.PROMPTS.values():
        assert text.isascii(), text
        (width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE,
                                        config.TEXT_THICKNESS)
        assert config.TEXT_ORIGIN[0] + width < config.CAM_W, text


# --- Chia real_tune / real_test (luật 15) -------------------------------------------

def fake_session(raw, session, names):
    """Một buổi quay giả: video rỗng kèm file mốc thời gian."""
    folder = raw / session
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        video = folder / f"{name}.mp4"
        video.write_bytes(b"video")
        selfdata.write_sidecar(video, [0.0, 0.1], person=name[:3])
    return folder


def test_real_tune_va_real_test_khong_chung_nguoi_hoac_buoi(tmp_path):
    """Đơn vị chia là người–buổi: p01 ở cả hai phía bằng hai buổi khác nhau. Không
    người–buổi nào, không buổi quay nào ở cả hai phía; rejected/ không tính."""
    raw = tmp_path / "raw"
    fake_session(raw, "2026-11-06", ["p01_swipe_left_01", "p01_none-wave_01"])
    fake_session(raw, "2026-11-07", ["p02_zoom_in_01"])
    fake_session(raw, "p01-test", ["p01_zoom_out_01"])
    (raw / "2026-11-06" / "rejected").mkdir()
    (raw / "2026-11-06" / "rejected" / "p01_swipe_left_02~1.mp4").write_bytes(b"video")
    found = selfdata.sessions(raw)
    assert {k: len(v) for k, v in found.items()} == {
        "p01/2026-11-06": 2, "p02/2026-11-07": 1, "p01/p01-test": 1}
    assert split_self.plan(found, ["p01/p01-test"]) == {
        "real_tune": ["p01/2026-11-06", "p02/2026-11-07"], "real_test": ["p01/p01-test"]}
    with pytest.raises(ValueError):
        split_self.plan(found, ["p09/khong-co"])
    for bad in ({"real_tune": ["p02/2026-11-06"], "real_test": ["p01/2026-11-06"]},
                {"real_tune": ["p01/a"], "real_test": ["p01/a"]},
                {"real_tune": ["p01"], "real_test": []}):
        with pytest.raises(ValueError):
            check_self_split(bad)
    with pytest.raises(ValueError):
        selfdata.session_key("p01", "mot-buoi-co-ten-rat-dai")


def test_split_self_tu_choi_ghi_de(tmp_path, monkeypatch):
    """Chia một lần: lần chạy thứ hai không đổi gì trong splits.json."""
    raw = tmp_path / "raw"
    fake_session(raw, "2026-11-06", ["p01_swipe_left_01"])
    fake_session(raw, "p01-test", ["p01_zoom_out_01"])
    path = tmp_path / "splits.json"
    path.write_text(json.dumps({"train": ["1"], "val": ["2"], "test": ["3"],
                                "real_tune": [], "real_test": []}), encoding="utf-8")
    monkeypatch.setattr(config, "SPLITS_JSON", path)
    split_self.main(["--test", "p01/p01-test", "--raw", str(raw)])
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["real_tune"] == ["p01/2026-11-06"] and written["real_test"] == ["p01/p01-test"]
    assert written["train"] == ["1"]
    with pytest.raises(SystemExit):
        split_self.main(["--test", "p01/p01-test", "--raw", str(raw)])
    assert json.loads(path.read_text(encoding="utf-8")) == written


def test_chia_du_lieu_tu_quay_khong_lam_ban_ghi_het_han(tmp_path, monkeypatch):
    """Thí nghiệm Phase 8 chỉ dùng IPN: ghi real_tune/real_test không đổi dấu vân tay
    dữ liệu, còn đổi người của val thì có."""
    path = tmp_path / "splits.json"
    base = {"train": ["1"], "val": ["2"], "test": ["3"], "real_tune": [], "real_test": []}
    path.write_text(json.dumps(base), encoding="utf-8")
    monkeypatch.setattr(config, "SPLITS_JSON", path)
    before = experiments.data_fingerprint(tmp_path)
    path.write_text(json.dumps({**base, "real_tune": ["p01/2026-11-06"],
                                "real_test": ["p01/p01-test"]}), encoding="utf-8")
    assert experiments.data_fingerprint(tmp_path) == before
    path.write_text(json.dumps({**base, "val": ["2", "4"]}), encoding="utf-8")
    assert experiments.data_fingerprint(tmp_path) != before


# --- Trích điểm mốc dữ liệu tự quay ------------------------------------------------

class RecordingTracker:
    """Thay HandTracker trong extract_landmarks: trả bàn tay mẫu dời dần, và ghi lại
    mốc thời gian (ms) mà vòng theo dõi đưa cho MediaPipe."""
    calls = []

    def __init__(self):
        RecordingTracker.calls = []

    def process(self, frame_bgr, ts_ms):
        RecordingTracker.calls.append(ts_ms)
        k = len(RecordingTracker.calls)
        return hand_at("swipe_left", 0.05 * k).astype(np.float32), True, 1.0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_extract_self_dung_cung_ham_voi_ipn(tmp_path, monkeypatch):
    """Dữ liệu tự quay đi qua ĐÚNG vòng theo dõi tay của IPN (track_video), với mốc
    thời gian THẬT trong file .json — không phải mốc suy từ FPS. Đoạn gán nhãn là
    selfdata.clip_segments; clip nạp lại không bị lật. Số frame lệch file mốc thời
    gian thì báo lỗi, không đoán."""
    import inspect

    from src.hands import seconds_to_ms
    from src.io_data import load_clip

    assert "track_video(" in inspect.getsource(extract.extract_ipn)
    assert "track_video(" in inspect.getsource(extract.extract_self)
    monkeypatch.setattr(extract, "HandTracker", RecordingTracker)
    video = black_video(tmp_path / "p01_swipe_left_03.avi", 1.0)          # 15 frame
    ts = np.cumsum([0.0] + [0.05, 0.09] * 7)                             # FPS không đều
    selfdata.write_sidecar(video, ts, trim_sec=0.2, fps_nominal=30, block="gestures",
                           live_check=None)
    task = {"clip_id": "buoi/p01_swipe_left_03", "video": str(video),
            "out": str(tmp_path / "ra" / "buoi" / "p01_swipe_left_03.npz"),
            "expected_frames": None, "split": "real_tune",
            "self": {"key": "p01/buoi", "person": "p01", "session": "buoi",
                     "label": "swipe_left"}}
    result = extract.extract_one(task)
    assert result["ok"] and result["n_frames"] == ts.size
    assert RecordingTracker.calls == [seconds_to_ms(t) for t in ts]
    got_ts, xy, w, h, segments, src, meta = load_clip(task["out"])
    np.testing.assert_allclose(got_ts, ts)
    np.testing.assert_allclose(xy[3], hand_at("swipe_left", 0.2), atol=1e-6)
    want_segments, want_src = selfdata.clip_segments("swipe_left", ts, 0.2)
    np.testing.assert_array_equal(segments, want_segments)
    assert list(src) == list(want_src) and (w, h) == (64, 48)
    assert (meta["source"], meta["subject"], meta["flip_applied"]) == ("self", "p01/buoi", False)

    selfdata.write_sidecar(video, ts[:-2], trim_sec=0.2, fps_nominal=30)  # thiếu 2 mốc
    task["out"] = str(tmp_path / "ra" / "lech.npz")
    bad = extract.extract_one(task)
    assert not bad["ok"] and "mốc thời gian" in bad["error"]


# --- Lọc đoạn học, học thêm, so cũ–mới -----------------------------------------------

def normalized(points):
    from src.preprocess import normalize_window
    return normalize_window(np.asarray(points, dtype=np.float64))


def swipe_path(offsets_palms):
    """Cửa sổ pixel: cổ tay đi theo ``offsets_palms`` lòng bàn tay trên trục x ảnh."""
    return [hand(center=(CENTER[0] + o * PALM_PX, CENTER[1])) for o in offsets_palms]


def test_loc_doan_hoc_giu_dung_chieu_bo_nguoc_chieu_va_keo_ve():
    """Đoạn học tốt: đi đúng chiều cử chỉ (vuốt theo SWIPE_LEFT_SIGN đã đo), ít nhất
    SELF_MIN_NET, không kéo ngược quá SELF_MAX_BACK quãng đã đi."""
    left = config.SWIPE_LEFT_SIGN
    steps = np.linspace(0.0, 1.0, config.T)
    clean = normalized(swipe_path(left * 2.0 * steps))
    assert selfdata.window_progress("swipe_left", clean) == pytest.approx((2.0, 2.0))
    assert selfdata.window_ok("swipe_left", clean)
    assert not selfdata.window_ok("swipe_right", clean), "ngược chiều"
    there_and_back = normalized(swipe_path(left * 2.0 * np.sin(np.pi * steps)))
    assert not selfdata.window_ok("swipe_left", there_and_back), "kéo về"
    tiny = normalized(swipe_path(left * 0.5 * config.SELF_MIN_NET["swipe_left"] * steps))
    assert not selfdata.window_ok("swipe_left", tiny), "quá nhỏ"
    opening = normalized([hand(openness=o) for o in np.linspace(0.0, 1.5, config.T)])
    assert selfdata.window_ok("zoom_in", opening) and not selfdata.window_ok("zoom_out", opening)
    windows = {"y": np.array([0, 1, 1]), "X": np.stack([there_and_back, clean, there_and_back])}
    assert build_self.filter_positives(windows).tolist() == [True, True, False], \
        "none giữ hết, chỉ lọc cửa sổ dương"


def test_buoi_cham_chi_mo_voi_final(monkeypatch):
    """Trích điểm mốc hay dựng cửa sổ của real_test đều cần --final (luật 13)."""
    import sys
    for module, argv in ((extract, ["--source", "self", "--split", "real_test"]),
                         (build_self, ["--split", "real_test"])):
        monkeypatch.setattr(sys, "argv", ["script.py", *argv])
        with pytest.raises(SystemExit, match="--final"):
            module.main()


def windows_of(subjects):
    """Bộ cửa sổ tối thiểu đúng các cột của windows.npz."""
    n = len(subjects)
    return {"X": np.zeros((n, config.T, config.NUM_LANDMARKS, 2), np.float32),
            "y": np.arange(n, dtype=np.int64) % len(config.CLASSES),
            "presence": np.ones(n, np.float32), "subject": np.array(subjects, dtype="<U16"),
            "clip": np.array([f"c{i}" for i in range(n)], dtype="<U64"),
            "t0": np.zeros(n, np.float32), "src_label": np.array([""] * n, dtype="<U32")}


def test_hoc_them_chi_lay_real_tune():
    """Tập học mới là người train của IPN cộng người–buổi real_tune; val vẫn là val IPN.
    Cửa sổ của real_test lọt vào thì dừng ngay."""
    splits = {"train": ["1"], "val": ["2"], "test": ["3"],
              "real_tune": ["p01/a"], "real_test": ["p01/b"]}
    data, part = train_self.merged(windows_of(["1", "2"]), windows_of(["p01/a"]), splits)
    assert part == {"train": ["1", "p01/a"], "val": ["2"]} and data["y"].size == 3
    with pytest.raises(ValueError, match="p01/b"):
        train_self.merged(windows_of(["1"]), windows_of(["p01/b"]), splits)


def test_so_cu_moi_tren_real_test_chi_mot_lan_mot_dong(tmp_path, monkeypatch):
    """compare_self trên real_test: thiếu --final thì dừng, không ghi gì. Có --final thì
    ghi ĐÚNG MỘT dòng cho cả hai mô hình, TRƯỚC khi đọc dữ liệu (dữ liệu thiếu vẫn
    còn dòng đó)."""
    from src import evaluation
    log = tmp_path / "TEST_USED.log"
    monkeypatch.setattr(compare, "guard_split",
                        lambda *a, **k: evaluation.guard_split(*a, **k, log_path=log))
    monkeypatch.setattr(compare, "read_splits", lambda: {
        "train": ["1"], "val": ["2"], "test": ["3"],
        "real_tune": ["p01/a"], "real_test": ["p01/b"]})
    monkeypatch.setattr(config, "SELF_WINDOWS", {"real_tune": tmp_path / "a.npz",
                                                 "real_test": tmp_path / "khong_co.npz"})
    with pytest.raises(SystemExit):
        compare.main(["--split", "real_test"])
    assert not log.exists()
    with pytest.raises(FileNotFoundError):
        compare.main(["--split", "real_test", "--final"])
    entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert len(entries) == 1 and entries[0]["split"] == "real_test"
    assert set(entries[0]["details"]) == {f"{side} s{seed}" for side in ("cũ", "mới")
                                          for seed in config.SELF_SEEDS}


def test_moi_ben_moi_hat_mot_mo_hinh_va_khong_ghi_de_demo():
    """IPN thuần với hạt SEED là chính mô hình demo; mọi hạt và bên khác có file riêng.
    train_self từ chối học lại mô hình demo. Bảng gộp lấy trung bình và khoảng mỗi bên."""
    assert selfdata.model_paths(False, config.SEED) == (config.RF_MODEL_PATH,
                                                         config.LSTM_MODEL_PATH)
    assert selfdata.model_paths(True, config.SEED) == (config.SELF_RF_PATH,
                                                        config.SELF_LSTM_PATH)
    others = {p for side in (False, True) for s in config.SELF_SEEDS if s != config.SEED
              for p in selfdata.model_paths(side, s)}
    assert len(others) == 4 * (len(config.SELF_SEEDS) - 1)
    assert all(p.parent == config.SELF_SEED_DIR for p in others)
    with pytest.raises(SystemExit, match="demo"):
        train_self.targets(True, config.SEED)
    rows = [{"variant": "cũ s42", "model": "rf", "f1": 0.2},
            {"variant": "cũ s43", "model": "rf", "f1": 0.4},
            {"variant": "mới s42", "model": "rf", "f1": 0.5}]
    sides = compare.side_rows(rows, ["model"], ["f1"])
    assert sides[0] == {"variant": "cũ", "model": "rf", "n_seeds": 2,
                        "f1": pytest.approx(0.3), "f1_min": 0.2, "f1_max": 0.4}
    assert sides[1]["n_seeds"] == 1 and sides[1]["f1"] == 0.5


def test_demo_chon_mo_hinh_tu_quay_theo_hat(tmp_path, monkeypatch):
    """demo.py --self-seed: rừng và LSTM học thêm dữ liệu tự quay của hạt đó; thiếu file
    thì chỉ cách học. Không cờ thì vẫn là mô hình demo."""
    from src import live
    assert live.model_files(None) == (None, None)
    assert live.make_model("hybrid").forest.path is None
    monkeypatch.setattr(config, "SELF_SEED_DIR", tmp_path)
    with pytest.raises(FileNotFoundError, match="train_self.py --seed 43"):
        live.model_files(43)
    rf, lstm = selfdata.model_paths(True, 43)
    rf.write_bytes(b"")
    lstm.write_bytes(b"")
    assert live.model_files(43) == (rf, lstm)
    model = live.make_model("hybrid", lstm_path=lstm, rf_path=rf)
    assert model.forest.path == rf and model.lstm_path == lstm
    assert live.make_model("rf", rf_path=rf).path == rf


def test_noi_them_giu_yen_khong_doi_nhan(tmp_path):
    """Bản 'giữ yên' của một lần quay: thêm SELF_HOLD_SEC giây, mốc thời gian nối tiếp,
    tay lặp frame cuối kèm rung nhỏ; nhãn và mã người–buổi không đổi."""
    from src.io_data import load_clip, save_clip
    ts, xy = synthetic_take("swipe_left", 2.0, [(1.0, 2.0, 0.3)])
    segments, src = selfdata.clip_segments("swipe_left", ts, config.REC_TRIM_SEC)
    path = tmp_path / "buoi" / "p01_swipe_left_01.npz"
    path.parent.mkdir()
    save_clip(path, ts, xy, np.ones(ts.size, bool), segments, src,
              {"w": config.CAM_W, "h": config.CAM_H, "fps": 30, "source": "self",
               "subject": "p01/buoi", "clip_id": "buoi/p01_swipe_left_01"})
    out = compare.held(path, tmp_path / "ra", np.random.default_rng(0))
    ts2, xy2, w, h, seg2, src2, meta2 = load_clip(out)
    extra = round(config.SELF_HOLD_SEC * config.CAM_FPS)
    assert ts2.size == ts.size + extra and np.all(np.diff(ts2) > 0)
    np.testing.assert_array_equal(seg2, segments)
    assert list(src2) == list(src) and meta2["subject"] == "p01/buoi"
    drift_px = np.abs(xy2[ts.size:] - xy[-1]) * np.array([w, h])
    assert drift_px.max() < 6 * config.SELF_HOLD_JITTER_PX


def test_khong_co_none_thi_so_bang_trung_binh_bon_lop_cu_chi():
    """real_test không có cửa sổ none: macro-F1 năm lớp tính cả F1 = 0 của none, còn
    trung bình bốn lớp cử chỉ thì không. Hàng giữ ma trận nhầm lẫn thô."""
    k = config.CLASSES.index
    y = np.array([k(c) for c in selfdata.GESTURES for _ in range(2)])
    pred = y.copy()
    pred[0], pred[4] = k("none"), k("zoom_out")
    row = compare.window_row("cũ s42", "rf", y, pred)
    assert row["gesture_recall"] == pytest.approx((0.5 + 1 + 0.5 + 1) / 4)
    assert row["none"] == 0 and row["macro_f1"] == pytest.approx(row["gesture_f1"] * 4 / 5)
    assert np.array(row["confusion"]).sum() == y.size


def test_lenh_dau_tien_cua_lan_quay_va_ban_ghi_du_de_phan_tich_lai():
    """Lệnh đầu tiên quyết định đúng / nhầm / sót. Bản ghi từng lần quay giữ cử chỉ,
    đoạn của nó và MỌI lệnh, ghi được ra JSON — real_test không chấm lại được."""
    k = config.CLASSES.index
    results = [
        {"clip": "b/a1", "gestures": [(k("swipe_left"), 0.3, 1.5, "")],
         "commands": [(0.9, k("swipe_left"))]},
        {"clip": "b/a2", "gestures": [(k("zoom_in"), 0.2, 1.4, "")],
         "commands": [(0.5, k("zoom_out")), (1.0, k("zoom_in"))]},
        {"clip": "b/a3", "gestures": [(k("zoom_out"), 0.2, 1.4, "")], "commands": []}]
    out = compare.take_outcomes(results)
    assert out["swipe_left"]["đúng"] == 1 and out["zoom_in"]["nhầm"] == 1
    assert out["zoom_out"]["sót"] == 1 and sum(out["swipe_right"].values()) == 0
    record = compare.take_record("như quay", "mới s43", results[1])
    assert record["gesture"] == "zoom_in" and record["span"] == [0.2, 1.4]
    assert record["commands"] == [[0.5, "zoom_out"], [1.0, "zoom_in"]]
    assert json.loads(json.dumps(record, ensure_ascii=False)) == record


def test_tim_clip_ca_trong_thu_muc_con_va_nap_mo_hinh_theo_duong_dan(tmp_path):
    """Điểm mốc tự quay nằm theo buổi: clip_paths tìm cả thư mục con. Đánh giá nạp
    được mô hình ở đường dẫn khác mô hình demo."""
    from src import evaluation
    from src.events import clip_paths
    from src.io_data import save_clip
    ts = np.arange(3) / 30.0
    xy = np.full((3, config.NUM_LANDMARKS, 2), np.nan, np.float32)
    for rel, subject in (("a.npz", "1"), ("buoi/b.npz", "p01/buoi")):
        (tmp_path / rel).parent.mkdir(exist_ok=True)
        save_clip(tmp_path / rel, ts, xy, np.zeros(3, bool), np.zeros((0, 3)), [],
                  {"w": 64, "h": 48, "fps": 30, "source": "self", "subject": subject,
                   "clip_id": rel})
    assert clip_paths(["p01/buoi"], tmp_path)[0] == [tmp_path / "buoi" / "b.npz"]
    with pytest.raises(FileNotFoundError, match="khong_co"):
        evaluation.model_proba("rf", np.zeros((1, 15)), rf_path=tmp_path / "khong_co.joblib")


def test_hang_so_quay_khong_lam_ban_ghi_het_han(monkeypatch):
    """Thí nghiệm Phase 8 chỉ dùng IPN: cách quay dữ liệu tự quay không băm vào."""
    spec = experiments.full_spec({"model": "lstm"})
    assert not any(k.startswith("REC_") for k in experiments.relevant_config())
    base = experiments.record_key(spec, "dữ liệu")
    monkeypatch.setattr(config, "REC_MAX_CLIP_SEC", 99.0)
    assert experiments.record_key(spec, "dữ liệu") == base
