"""Kiểm thử Phase 11 — dữ liệu tự quay. Không cần camera: nguồn quay là một video
đen tổng hợp; không đụng data/ hay results/ thật."""

import argparse

import cv2
import numpy as np
import pytest

from src import config, experiments, selfdata
from src.io_video import iter_frames
from src.windows import core_times
from tests.fixtures import CENTER, OPEN_TIGHT, PALM_PX, black_video, hand
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


def test_hang_so_quay_khong_lam_ban_ghi_het_han(monkeypatch):
    """Thí nghiệm Phase 8 chỉ dùng IPN: cách quay dữ liệu tự quay không băm vào."""
    spec = experiments.full_spec({"model": "lstm"})
    assert not any(k.startswith("REC_") for k in experiments.relevant_config())
    base = experiments.record_key(spec, "dữ liệu")
    monkeypatch.setattr(config, "REC_MAX_CLIP_SEC", 99.0)
    assert experiments.record_key(spec, "dữ liệu") == base
