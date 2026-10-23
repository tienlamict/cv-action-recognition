"""Kiểm thử đánh giá mức sự kiện (Phase 8) — logic thuần và clip tổng hợp,
không đụng data/ hay results/."""

import inspect

import numpy as np
import pytest

from src import config, events
from src.events import EdgeFilter, RawFilter, Timeline
from src.features import FEATURE_NAMES
from src.live import LivePredictor
from tests.fixtures import PALM_PX, SWIPE_PALMS, make_static, make_swipe, save_parts_clip

LEFT, RIGHT, ZOOM_IN = (config.CLASSES.index(c) for c in ("swipe_left", "swipe_right",
                                                          "zoom_in"))


def run_filter(event_filter, labels):
    return [i for i, label in enumerate(labels)
            if event_filter.update(label, 0.9, 1.0, i * 0.2) is not None]


def test_bo_loc_canh_len_moi_chuoi_lien_nhau_mot_lenh():
    """Chuỗi cùng lớp liền nhau là một lệnh; none, mất tay (None) hay đổi lớp
    đều cắt chuỗi — cùng cách đếm cụm của summarize_log.py."""
    labels = [1, 1, 1, 0, 1, None, 1, 3, 3, 4]
    assert run_filter(EdgeFilter(), labels) == [0, 4, 6, 7, 9]
    assert run_filter(RawFilter(), labels) == [0, 1, 2, 4, 6, 7, 8, 9]
    assert run_filter(EdgeFilter(), [0, None, 0]) == []


def timeline(gestures, spans=None, ts=None, clip="c", subject="p"):
    ts = np.asarray(ts if ts is not None else [0.0])
    return Timeline(clip, subject, ts, np.ones(ts.size), np.ones(ts.size, bool), 60.0,
                    gestures, spans or [(g[1], g[2], g[0], g[3]) for g in gestures])


def test_moi_video_mot_bo_loc_moi():
    """Chuỗi nhãn vuốt kéo qua ranh giới hai video vẫn là HAI lệnh: trạng thái
    bộ lọc không lọt sang video sau."""
    ts = np.arange(3) * 0.2
    labels = np.array([0, LEFT, LEFT])
    a, b = timeline([], ts=ts, clip="a"), timeline([], ts=ts, clip="b")
    first = events.commands(a, labels, np.ones(3), "edge")
    second = events.commands(b, np.array([LEFT, LEFT, 0]), np.ones(3), "edge")
    assert len(first) == 1 and len(second) == 1


def test_khop_lenh_theo_vung_khop():
    """Vùng "span": từ lúc cử chỉ bắt đầu tới kết thúc + EVENT_TOL_SEC; vùng
    "end" (SPEC ban đầu): ±EVENT_TOL_SEC quanh lúc kết thúc. Lệnh thứ hai cho
    cùng cử chỉ, lệnh khác lớp, lệnh quá muộn đều là FP."""
    tol = 1.0
    gesture = [(LEFT, 10.0, 12.0, "G05")]
    early = events.match([(10.8, LEFT)], gesture, tol, "span")
    assert early["tp"] == [(0, 0)] and early["fp"] == [] and early["fn"] == []
    end = events.match([(10.8, LEFT)], gesture, tol, "end")
    assert end["tp"] == [] and end["fp"] == [0] and end["fn"] == [0]
    assert end["early"] == [1], "lệnh đúng loại nhưng sớm hơn vùng khớp"

    twice = events.match([(11.0, LEFT), (11.2, LEFT)], gesture, tol, "span")
    assert twice["tp"] == [(0, 0)] and twice["fp"] == [1] and twice["in_tol"] == [2]
    wrong = events.match([(11.0, RIGHT)], gesture, tol, "span")
    assert wrong["fp"] == [0] and wrong["fn"] == [0]
    late = events.match([(13.5, LEFT)], gesture, tol, "span")
    assert late["fp"] == [0] and late["fn"] == [0]
    with pytest.raises(ValueError):
        events.match([], gesture, tol, "giữa")


def test_tong_hop_su_kien_dem_dung_va_phan_loai_lenh_nham():
    """Một video 60 s: cú vuốt trái nhận đúng một lần rồi lặp, zoom in bị sót,
    một lệnh nhầm lúc tay chỉ trỏ (B0A), một lệnh sai lớp trong lúc zoom."""
    gestures = [(LEFT, 10.0, 12.0, "G05"), (ZOOM_IN, 30.0, 32.0, "G10")]
    spans = [(0.0, 9.9, 0, "D0X"), (10.0, 12.0, LEFT, "G05"), (12.1, 29.9, 0, "B0A"),
             (30.0, 32.0, ZOOM_IN, "G10"), (32.1, 60.0, 0, "D0X")]
    tl = timeline(gestures, spans, ts=[10.5, 10.9, 20.0, 31.0])
    labels = np.array([LEFT, LEFT, RIGHT, LEFT])
    # raw: mỗi lần dự đoán ra cử chỉ là một lệnh
    results = events.evaluate_timelines([tl], [labels], [np.full(4, 0.9)], "raw",
                                        tol=1.0, mode="span")
    s = events.summarize_events(results)
    assert (s["tp"], s["fp"], s["fn"]) == (1, 3, 1)
    assert s["precision"] == pytest.approx(0.25) and s["recall"] == pytest.approx(0.5)
    assert s["false_per_min"] == pytest.approx(3.0)
    assert s["cmds_per_gesture"] == pytest.approx((2 + 0) / 2)
    kinds = {(r["kind"], r["src_label"]): r["n"] for r in s["false_by_src"]}
    assert kinds == {("cùng cử chỉ", "G05"): 1, ("none", "B0A"): 1,
                     ("cử chỉ khác", "G10"): 1}
    rows = {r["class"]: r for r in s["per_class"]}
    assert rows["swipe_left"]["tp"] == 1 and rows["zoom_in"]["fn"] == 1
    assert s["macro_f1"] == pytest.approx(np.mean([r["f1"] for r in s["per_class"]]))


def swipe_clip(path, subject="p1"):
    """Clip tổng hợp: tay đứng yên, vuốt trái (theo SWIPE_LEFT_SIGN), đứng yên ở
    chỗ cú vuốt dừng — không có cú nhảy ngược về giữa khung."""
    sign = config.SWIPE_LEFT_SIGN or 1
    shift = np.array([sign * SWIPE_PALMS * PALM_PX, 0.0])
    return save_parts_clip(path, [(make_static(30), "D0X", "none"),
                                  (make_swipe(sign, 15), "G05", "swipe_left"),
                                  (make_static(45, seed=1) + shift, "D0X", "none")],
                           subject=subject)


def test_dong_thoi_gian_video_trung_live_predictor(tmp_path):
    """Video đi qua đúng WindowStream của demo: cùng thời điểm, cùng đặc trưng,
    cùng chỗ không có cửa sổ hợp lệ như LivePredictor."""
    from src.io_data import load_clip

    path = swipe_clip(tmp_path / "c1.npz")
    timeline_, X, F = events.clip_stream(path)
    seen = []
    predictor = LivePredictor(lambda f: (seen.append(f) or 0, 1.0))
    ts, xy, w, h, _, _, _ = load_clip(path)
    preds = [p for t, frame in zip(ts, xy)
             if (p := predictor.update(float(t), frame, w, h)) is not None]
    np.testing.assert_allclose(timeline_.ts, [p.ts for p in preds])
    np.testing.assert_array_equal(timeline_.valid, [p.label is not None for p in preds])
    np.testing.assert_array_equal(F, np.stack(seen))
    assert X.shape == (len(seen), config.T, config.NUM_LANDMARKS, 2)
    assert timeline_.gestures[0][0] == LEFT and timeline_.gestures[0][3] == "G05"


def test_danh_gia_su_kien_tu_dau_den_cuoi_tren_clip_tong_hop(tmp_path):
    """Mô hình "dời trái hơn 1,5 lòng bàn tay là vuốt trái" trên video tổng hợp:
    đúng một lệnh, rơi vào vùng khớp của cú vuốt, không lệnh nhầm."""
    path = swipe_clip(tmp_path / "c1.npz")
    timelines, X, F = events.clip_streams([path])
    dx = F[:, FEATURE_NAMES.index("dx")] * (config.SWIPE_LEFT_SIGN or 1)
    labels = np.where(dx > 1.5, LEFT, 0)
    per_clip = events.scatter(timelines, labels, np.ones(labels.size))
    s = events.summarize_events(events.evaluate_timelines(timelines, *per_clip, "edge"))
    assert (s["tp"], s["fp"], s["fn"]) == (1, 0, 0)
    assert s["cmds_per_gesture"] == 1.0

    out = tmp_path / "streams.npz"
    events.save_streams(out, timelines, X, F)
    back, X_back, F_back = events.load_streams(out)
    assert back[0].gestures == timelines[0].gestures and back[0].spans == timelines[0].spans
    np.testing.assert_array_equal(back[0].ts, timelines[0].ts)
    np.testing.assert_array_equal(X_back, X)
    assert events.load_streams(out, windows=False)[1] is None


def test_scatter_dat_du_doan_vao_dung_lan_hop_le():
    valid = np.array([False, True, True, False, True])
    tl = Timeline("c", "p", np.arange(5) * 0.2, np.ones(5), valid, 1.0, [], [])
    labels, conf = events.scatter([tl, tl], np.arange(6), np.arange(6) / 10)
    np.testing.assert_array_equal(labels[0], [-1, 0, 1, -1, 2])
    np.testing.assert_array_equal(labels[1], [-1, 3, 4, -1, 5])
    assert np.isnan(conf[0][0]) and conf[1][4] == pytest.approx(0.5)
    with pytest.raises(ValueError):
        events.scatter([tl], np.arange(4), np.arange(4))


def test_bo_loc_su_kien_la_tham_so_cua_evaluate(monkeypatch):
    """evaluate.py nhận MỌI bộ lọc trong EVENT_FILTERS, nên Phase 9 chỉ cần
    đăng ký ActivationFSM ở src/events.py, không sửa evaluate.py."""
    from tests.scripts_import import load_script

    source = inspect.getsource(load_script("evaluate").main)
    assert "choices=list(EVENT_FILTERS)" in source

    class Every:
        def update(self, label, confidence, presence, ts):
            return LEFT

    monkeypatch.setitem(events.EVENT_FILTERS, "every", Every)
    tl = timeline([(LEFT, 0.0, 1.0, "G05")], ts=[0.2, 0.4])
    results = events.evaluate_timelines([tl], [np.array([0, 0])], [np.ones(2)], "every")
    assert len(results[0]["commands"]) == 2
    with pytest.raises(ValueError, match="raw"):
        events.make_filter("không có")
