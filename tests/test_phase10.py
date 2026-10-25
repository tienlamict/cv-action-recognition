"""Kiểm thử Phase 10 — demo hoàn chỉnh và đo đạc. Không cần camera, không cần
pyautogui, không đụng data/ hay results/ thật."""

import ast

import cv2
import numpy as np
import pytest

from src import config, events
from src.control import Controller
from src.fps import FpsMeter
from src.live import HELP_LINES, LandmarkRecorder, help_screen, screen_lines
from tests.fixtures import PALM_PX, SWIPE_PALMS, make_static, make_swipe, save_parts_clip
from tests.scripts_import import load_script

LEFT = config.CLASSES.index("swipe_left")
bench = load_script("bench")


def test_dieu_khien_mac_dinh_tat():
    """Không gửi phím nào cho tới khi người dùng bật điều khiển."""
    sent = []
    controller = Controller(send=lambda *keys: sent.append(keys))
    assert controller.enabled is False
    assert controller.handle(LEFT) is None and sent == []
    assert controller.toggle() is True
    assert controller.handle(LEFT) == tuple(config.CTRL_HOTKEYS["swipe_left"])
    assert controller.handle(None) is None
    assert controller.toggle() is False and controller.handle(LEFT) is None
    assert sent == [tuple(config.CTRL_HOTKEYS["swipe_left"])]


def test_bat_dieu_khien_khi_chua_cai_pyautogui_bao_ro_va_van_tat(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def no_pyautogui(name, *args, **kwargs):
        if name == "pyautogui":
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_pyautogui)
    controller = Controller()
    with pytest.raises(RuntimeError, match="pip install pyautogui"):
        controller.toggle()
    assert controller.enabled is False


def test_demo_import_ham_chung():
    """demo.py chỉ nối webcam, màn hình và log: không định nghĩa hàm nào ngoài
    main, và lấy mọi xử lý từ src/."""
    tree = ast.parse((config.SCRIPTS_DIR / "demo.py").read_text(encoding="utf-8"))
    defined = [node.name for node in ast.walk(tree)
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    assert defined == ["main"]
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                and (node.module or "").startswith("src") for alias in node.names}
    assert {"LivePredictor", "ActivationFSM", "Controller"} <= imported


def test_fps_bo_qua_ba_giay_dau():
    """3 giây đầu chậm (camera còn chỉnh phơi sáng) không kéo tụt FPS báo cáo."""
    meter = FpsMeter()
    slow = np.arange(0, config.FPS_WARMUP_SEC, 1 / 5)
    fast = config.FPS_WARMUP_SEC + np.arange(0, 5, 1 / 30)
    for ts in np.concatenate([slow, fast]):
        meter.tick(float(ts))
    summary = meter.summary()
    assert summary["mean_fps"] == pytest.approx(30, rel=0.01)
    assert summary["n_frames"] == fast.size


def test_man_hinh_ascii_va_vua_khung():
    """cv2.putText chỉ vẽ ASCII; trang trợ giúp phải vừa khung camera."""
    lines, colors, big = help_screen()
    assert lines == list(HELP_LINES) and len(colors) == len(lines) and big is None
    for line in HELP_LINES:
        assert line.isascii(), line
        (width, _), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE,
                                        config.TEXT_THICKNESS)
        assert config.TEXT_ORIGIN[0] + width < config.CAM_W, line
    assert config.TEXT_ORIGIN[1] + len(HELP_LINES) * config.TEXT_LINE_HEIGHT < config.CAM_H
    status, _, _ = screen_lines(None, 30.0, state="READY", control=True)
    assert any("control ON" in line for line in status) and all(s.isascii() for s in status)


def test_lich_nhac_du_moi_lop_va_tai_lap():
    schedule = bench.prompt_schedule(config.BENCH_GESTURES_PER_CLASS,
                                     np.random.default_rng(config.SEED))
    classes = [cls for _, _, cls in schedule]
    assert len(schedule) == config.BENCH_GESTURES_PER_CLASS * (len(config.CLASSES) - 1)
    assert all(classes.count(c) == config.BENCH_GESTURES_PER_CLASS
               for c in range(1, len(config.CLASSES)))
    starts = np.array([a for a, _, _ in schedule])
    ends = np.array([b for _, b, _ in schedule])
    np.testing.assert_allclose(ends - starts, config.BENCH_PROMPT_SEC)
    np.testing.assert_allclose(starts[1:] - ends[:-1], config.BENCH_REST_SEC)
    assert schedule == bench.prompt_schedule(config.BENCH_GESTURES_PER_CLASS,
                                             np.random.default_rng(config.SEED))


def test_phien_ghi_luu_loi_nhac_thanh_doan_co_nhan(tmp_path):
    """bench.py record lưu lời nhắc thành đoạn; clip_stream đọc ra cử chỉ — nhờ
    vậy phiên webcam được chấm như video IPN."""
    recorder = LandmarkRecorder()
    ts = np.arange(120) / config.HZ
    still = make_static(120) / np.array([config.CAM_W, config.CAM_H])
    for t, frame in zip(ts, still):
        recorder.add(t, frame, True, config.CAM_W, config.CAM_H)
    schedule = [(2.0, 5.0, LEFT), (6.0, 10.0, LEFT)]       # lời nhắc thứ hai chưa hiện trọn
    segments = bench.prompt_segments(ts, schedule)
    assert segments == [(30, 75, LEFT)]
    path = recorder.save(tmp_path / "gestures_01.npz", segments=segments,
                         src_labels=["prompt"], scenario="gestures")
    timeline, _, _ = events.clip_stream(path)
    assert [(g[0], g[3]) for g in timeline.gestures] == [(LEFT, "prompt")]
    assert timeline.gestures[0][1] == pytest.approx(2.0)
    assert events.clip_meta(path)["scenario"] == "gestures"


def test_cham_lenh_do_tre_va_kich_hoat_nham():
    """Một cú vuốt trái được nhắc ở giây 10–12, mô hình đồng ý từ 10,6 s: máy
    3/5 phát ở 11,0 s. Độ trễ từ khoảnh khắc chính (10,8 s) là 0,2 s; đồng
    thuận 0,4 s. Một lần báo vuốt lúc không nhắc gì là kích hoạt nhầm."""
    step = config.STRIDE_SEC
    ts = np.round(np.arange(0, 30, step), 6)
    labels = np.zeros(ts.size, dtype=np.int64)
    labels[(ts >= 10.6) & (ts <= 11.4)] = LEFT
    labels[(ts >= 20.0) & (ts <= 20.6)] = LEFT
    gesture = (LEFT, 10.0, 12.0, "prompt")
    timeline = events.Timeline("s", "live", ts, np.ones(ts.size), np.ones(ts.size, bool),
                               30.0, [gesture], [(10.0, 12.0, LEFT, "prompt")])
    s = bench.score([timeline], [labels], [np.full(ts.size, 0.9)], 0.75, 3,
                    cores={"s": [10.8]})
    assert (s["tp"], s["fp"], s["fn"]) == (1, 1, 0)
    assert s["cmds_per_gesture"] == 1.0
    assert s["false_per_min"] == pytest.approx(2.0)
    assert s["latency"] == [pytest.approx(0.2)]
    assert s["consensus"] == [pytest.approx(2 * step), pytest.approx(2 * step)]
    two = bench.score([timeline], [labels], [np.full(ts.size, 0.9)], 0.6, 2)
    assert two["consensus"][0] == pytest.approx(step), "k = 2: phát ở cửa sổ thứ hai"


def black_video(path, seconds, fps=config.HZ, size=(64, 48)):
    """Video MJPG toàn đen — đủ để chạy cả vòng lặp mà không cần camera."""
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), fps, size)
    assert writer.isOpened(), "OpenCV không tạo được video MJPG để kiểm thử"
    for _ in range(int(seconds * fps)):
        writer.write(np.zeros((size[1], size[0], 3), dtype=np.uint8))
    writer.release()
    return path


def test_do_toc_do_chay_du_vong_lap_va_phan_ra_cong_du_100(tmp_path, monkeypatch):
    """bench.py speed trên một video thay webcam, không mở cửa sổ: FPS lấy từ mốc
    thời gian của frame, và các khâu xử lý cộng lại đúng 100% thời gian xử lý."""
    monkeypatch.setattr(bench.cv2, "imshow", lambda *a: None)
    monkeypatch.setattr(bench, "read_key", lambda: -1)
    video = black_video(tmp_path / "v.avi", config.FPS_WARMUP_SEC + 2)
    fps, totals, n_frames = bench.measure_speed("rules", str(video), 1.0, "test")
    assert fps["mean_fps"] == pytest.approx(config.HZ, rel=0.05)
    assert n_frames >= config.HZ and all(v >= 0 for k, v in totals.items() if k != "other")
    row, parts = bench.speed_rows("rules", "test", fps, totals, n_frames)
    shares = [p["share_of_processing"] for p in parts if p["component"] != "camera"]
    assert sum(shares) == pytest.approx(1.0)
    assert 0 < row["spec_share"] <= 1 and row["processing_ms"] > 0


def test_ghi_phien_tu_video_khong_gui_phim(tmp_path, monkeypatch):
    """bench.py record trên một video, không cửa sổ: phiên lưu đúng schema, có
    kịch bản trong meta, và không có đoạn nhãn nào ở kịch bản tự do."""
    import argparse

    monkeypatch.setattr(bench.cv2, "destroyAllWindows", lambda: None)
    video = black_video(tmp_path / "v.avi", 4)
    args = argparse.Namespace(scenario="reading", minutes=3 / 60, model="rules", seed=0,
                              out=tmp_path / "sessions", no_display=True, source=str(video))
    bench.run_record(args)
    (path,) = sorted((tmp_path / "sessions").glob("*.npz"))
    assert path.name == "reading_01.npz"
    meta = events.clip_meta(path)
    assert meta["scenario"] == "reading" and meta["complete"] is True
    timeline, _, _ = events.clip_stream(path)
    assert timeline.gestures == [] and timeline.duration == pytest.approx(3, abs=0.2)
    assert bench.session_path("reading", tmp_path / "sessions").name == "reading_02.npz"
    assert bench.gesture_cores(path, timeline) == [], "phiên không có đoạn nhãn nào"


def test_khoanh_khac_chinh_cua_phien_nam_trong_cu_vuot(tmp_path):
    """gesture_cores dùng đúng windows.core_steps: khoảnh khắc chính của một cú
    vuốt tổng hợp rơi vào giữa cú vuốt, không vào lúc tay đứng yên."""
    sign = config.SWIPE_LEFT_SIGN or 1
    shift = np.array([sign * SWIPE_PALMS * PALM_PX, 0.0])
    parts = [(make_static(30), "D0X", "none"), (make_swipe(sign, 15), "G05", "swipe_left"),
             (make_static(30, seed=1) + shift, "D0X", "none")]
    path = save_parts_clip(tmp_path / "c.npz", parts, subject="p")
    timeline, _, _ = events.clip_stream(path)
    (core,) = bench.gesture_cores(path, timeline)
    start, end = timeline.gestures[0][1], timeline.gestures[0][2]
    assert start <= core <= end
