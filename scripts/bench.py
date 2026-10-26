"""Đo đạc Phase 10 trên webcam — ba lệnh con, kết quả ở results/phase10/.

  speed    FPS và phân rã thời gian từng khâu, lần lượt từng mô hình: bỏ
           FPS_WARMUP_SEC giây đầu rồi đo BENCH_SPEED_SEC giây. Chạy hai lần, mỗi
           mức ánh sáng một lần (--light). Giữ tay trong khung, cử động tự nhiên.
  record   ghi một phiên vào BENCH_SESSIONS_DIR: điểm mốc thô đúng schema của
           data/landmarks. KHÔNG gửi phím nào. Bốn kịch bản:
             reading | typing | talking   làm việc bình thường BENCH_SCENARIO_MIN
                                          phút (đọc tài liệu; gõ phím và dùng
                                          chuột; nói chuyện có khua tay), KHÔNG
                                          làm cử chỉ nào
             gestures                     làm từng cử chỉ theo lời nhắc trên màn
                                          hình, BENCH_GESTURES_PER_CLASS lần mỗi lớp;
                                          lời nhắc lưu thành đoạn có nhãn
  analyze  chạy lại mọi phiên đã ghi qua từng mô hình với ba cấu hình của bảng
           đánh đổi (FSM_TRADEOFF), cùng đường ống của demo (events.clip_stream),
           nên trùng kết quả chạy thật; chạy cùng các cấu hình đó trên video val
           của IPN. Ra: kích hoạt nhầm mỗi phút theo kịch bản; với phiên gestures,
           recall (vuốt, zoom), số lệnh đúng loại trên một cử chỉ và tổng số lệnh
           chia số lời nhắc (định nghĩa của SPEC); độ trễ; và bảng đánh đổi.

Số lệnh trên một cử chỉ gần 1,0 chưa chắc là "mỗi cử chỉ một lệnh": cử chỉ bị sót
(0 lệnh) và cử chỉ bị phát trùng (2 lệnh) bù cho nhau. Luôn đọc kèm recall.

Độ trễ = cửa sổ + dự đoán + đồng thuận + xử lý (cẩm nang 20). analyze đo trên
video val, nơi đoạn nhãn ôm sát cử chỉ:
  - tổng ba phần đầu: từ khoảnh khắc chính của cử chỉ (windows.core_times, đúng
    hàm gán nhãn) tới lúc phát lệnh;
  - riêng phần đồng thuận: từ lúc mở ứng viên tới lúc phát lệnh;
  - phần dự đoán: trung bình nửa STRIDE_SEC (lúc cử chỉ xong rơi đều trong nhịp);
  - phần xử lý: thời gian xử lý một frame của lần speed gần nhất.
Trên webcam, khung lời nhắc 4 giây chứa cả động tác chuẩn bị và lúc thu tay, nên
không tìm khoảnh khắc chính được: độ trễ đầu-cuối thật đo thủ công — quay màn hình
có cả khung webcam và ứng dụng bị điều khiển, rồi đếm frame (cẩm nang 20.3).

Ví dụ:
    python scripts/bench.py speed --light bright
    python scripts/bench.py speed --light dim
    python scripts/bench.py record reading
    python scripts/bench.py record gestures
    python scripts/bench.py analyze
"""

import csv
import os
import platform
import sys
import time
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.activation import CANDIDATE, COOLDOWN, ActivationFSM  # noqa: E402
from src.cli import add_source_arg, make_parser, setup_console  # noqa: E402
from src.display import make_display, read_key  # noqa: E402
from src.evaluation import label_confidence  # noqa: E402
from src.events import (clip_meta, clip_paths, clip_stream,  # noqa: E402
                        clip_streams, evaluate_timelines, scatter, summarize_events)
from src.fps import FpsMeter  # noqa: E402
from src.hands import HandTracker, seconds_to_ms  # noqa: E402
from src.io_data import load_clip  # noqa: E402
from src.io_video import iter_frames  # noqa: E402
from src.live import (LandmarkRecorder, LivePredictor, make_model,  # noqa: E402
                      recent_command, screen_lines)
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits  # noqa: E402
from src.tables import write_table  # noqa: E402
from src.windows import core_times  # noqa: E402

WINDOW = "bench (q = quit)"
#: Các khâu của một vòng lặp. camera là lúc chờ frame kế tiếp; năm khâu của SPEC
#: là color (chuyển màu), mediapipe, window (chuẩn hoá và đặc trưng), model, draw.
COMPONENTS = ("camera", "color", "mediapipe", "window", "model", "fsm", "draw", "other")
SPEC_COMPONENTS = ("color", "mediapipe", "window", "model", "draw")
SCENARIOS = (*config.BENCH_SCENARIOS, "gestures")


# --------------------------------------------------------------------------
# speed
# --------------------------------------------------------------------------

def machine_info():
    import mediapipe
    return {"processor": platform.processor() or platform.machine(),
            "logical_cpus": os.cpu_count(), "platform": platform.platform(),
            "python": platform.python_version(), "opencv": cv2.__version__,
            "mediapipe": mediapipe.__version__}


def machine_note(machine):
    """Chú thích bắt buộc của mọi bảng tốc độ (SPEC Phase 10)."""
    return (f"Máy đo: {machine['processor']}, {machine['logical_cpus']} luồng logic, "
            f"{machine['platform']}; camera {config.CAM_W}×{config.CAM_H} @ "
            f"{config.CAM_FPS} FPS.")


def measure_speed(model_name, source, seconds, light):
    """Chạy demo với một mô hình — không ghi gì, không gửi phím — và đo FPS
    cùng thời gian từng khâu sau ``FPS_WARMUP_SEC`` giây đầu.

    Returns:
        ``(fps, totals, n_frames)`` — ``fps`` của ``FpsMeter.summary``;
        ``totals`` tổng số giây của từng khâu trong ``COMPONENTS``.
    """
    predictor = LivePredictor(make_model(model_name))
    fsm, meter = ActivationFSM(), FpsMeter()
    totals, n_frames = dict.fromkeys(COMPONENTS, 0.0), 0
    last, commands = None, []
    stop = config.FPS_WARMUP_SEC + seconds
    with HandTracker() as tracker:
        mark = time.perf_counter()
        for frame_bgr, ts in iter_frames(source):
            got = time.perf_counter()
            h, w = frame_bgr.shape[:2]
            xy, _, _ = tracker.process(frame_bgr, seconds_to_ms(ts))
            prediction = predictor.update(ts, xy, w, h)
            fsm_start = time.perf_counter()
            if prediction is not None:
                last = prediction
                command = fsm.update(prediction.label, prediction.confidence,
                                     prediction.presence, prediction.ts)
                if command is not None:
                    commands.append((ts, command))
            draw_start = time.perf_counter()
            lines, colors, big = screen_lines(last, meter.rolling_fps, state=fsm.state,
                                              command=recent_command(commands, ts))
            cv2.imshow(WINDOW, make_display(
                frame_bgr, xy, [f"BENCH speed {model_name} [{light}] {ts:4.0f}/{stop:.0f} s",
                                *lines],
                big_text=big, line_colors=[config.COLOR_ALERT, *colors]))
            key = read_key()
            done = time.perf_counter()
            meter.tick(ts)
            if ts >= config.FPS_WARMUP_SEC:
                parts = {"camera": got - mark, **tracker.last_timing,
                         **predictor.last_timing, "fsm": draw_start - fsm_start,
                         "draw": done - draw_start}
                parts["other"] = (done - mark) - sum(parts.values())
                for name in COMPONENTS:
                    totals[name] += parts[name]
                n_frames += 1
            mark = done
            if key in config.QUIT_KEYS or ts >= stop:
                break
    cv2.destroyAllWindows()
    return meter.summary(), totals, n_frames


def speed_rows(model_name, light, fps, totals, n_frames):
    """Một hàng FPS và các hàng phân rã thời gian của một mô hình."""
    processing = sum(totals[c] for c in COMPONENTS if c != "camera")
    loop = sum(totals.values())
    row = {"model": model_name, "light": light, "mean_fps": fps["mean_fps"],
           "low_fps": fps["low_fps"], "n_frames": n_frames,
           "processing_ms": processing / n_frames * 1000, "loop_ms": loop / n_frames * 1000,
           "spec_share": sum(totals[c] for c in SPEC_COMPONENTS) / processing}
    parts = [{"model": model_name, "light": light, "component": c,
              "ms_per_frame": totals[c] / n_frames * 1000,
              "share_of_processing": np.nan if c == "camera" else totals[c] / processing,
              "share_of_loop": totals[c] / loop} for c in COMPONENTS]
    return row, parts


def write_with_notes(rows, columns, stem, notes):
    """Bảng .csv + .md; ``.md`` có thêm chú thích bên dưới."""
    _, md = write_table(rows, columns, stem)
    with open(md, "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(f"- {line}" for line in notes) + "\n")
    return md


def run_speed(args):
    machine = machine_info()
    rows, parts = [], []
    for model_name in args.models:
        print(f"[{model_name}] khởi động {config.FPS_WARMUP_SEC:g} s rồi đo {args.sec:g} s — "
              "giữ tay trong khung, cử động tự nhiên.", flush=True)
        fps, totals, n_frames = measure_speed(model_name, args.source, args.sec, args.light)
        if not fps or n_frames == 0:
            print(f"[{model_name}] không đủ frame sau thời gian khởi động — bỏ qua.")
            continue
        row, model_parts = speed_rows(model_name, args.light, fps, totals, n_frames)
        rows.append(row)
        parts += model_parts
        print(f"[{model_name}] {row['mean_fps']:.1f} FPS (phân vị "
              f"{config.FPS_LOW_PERCENTILE:g}% thấp {row['low_fps']:.1f}), xử lý "
              f"{row['processing_ms']:.1f} ms mỗi frame", flush=True)
    if not rows:
        raise SystemExit("Không đo được mô hình nào.")
    run_dir = next_run_dir(args.out)
    notes = [machine_note(machine), f"Ánh sáng: {args.light}. Bỏ {config.FPS_WARMUP_SEC:g} s "
             f"đầu; FPS thấp là phân vị {config.FPS_LOW_PERCENTILE:g}% của FPS tức thời."]
    write_with_notes(rows, list(rows[0]), run_dir / "speed", notes)
    write_with_notes(parts, list(parts[0]), run_dir / "breakdown", notes + [
        "share_of_processing: phần trăm thời gian xử lý — mọi khâu trừ lúc chờ camera; "
        "spec_share ở bảng speed là tổng năm khâu của SPEC trên thời gian đó."])
    write_manifest(run_dir, {"script": "bench speed", "light": args.light,
                             "seconds": args.sec, "machine": machine})
    print(f"\nBảng: {relative_to_root(run_dir)}")


# --------------------------------------------------------------------------
# record
# --------------------------------------------------------------------------

def session_path(scenario, directory=None):
    """``<thư mục>/<kịch bản>_NN.npz`` với NN kế tiếp chưa dùng."""
    directory = Path(directory or config.BENCH_SESSIONS_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    k = 1
    while (directory / f"{scenario}_{k:02d}.npz").exists():
        k += 1
    return directory / f"{scenario}_{k:02d}.npz"


def prompt_schedule(per_class, rng):
    """Lịch nhắc của phiên gestures: mỗi lớp cử chỉ ``per_class`` lần, thứ tự
    xáo bằng ``rng``; trước mỗi lời nhắc nghỉ ``BENCH_REST_SEC`` giây.

    Returns:
        list ``(giây bắt đầu, giây kết thúc, lớp)``.
    """
    order = rng.permutation(np.repeat(np.arange(1, len(config.CLASSES)), per_class))
    schedule, t = [], 0.0
    for cls in order:
        t += config.BENCH_REST_SEC
        schedule.append((t, t + config.BENCH_PROMPT_SEC, int(cls)))
        t += config.BENCH_PROMPT_SEC
    return schedule


def prompt_segments(ts, schedule):
    """Lời nhắc đã hiện TRỌN → đoạn ``(frame đầu, frame sau cuối, lớp)`` của phiên."""
    ts = np.asarray(ts, dtype=np.float64)
    return [(int(np.searchsorted(ts, a)), int(np.searchsorted(ts, b)), cls)
            for a, b, cls in schedule if ts.size and b <= ts[-1]]


def clock(seconds):
    return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"


def record_screen(scenario, ts, duration, schedule):
    """Dòng đầu và chữ lớn của màn hình ghi, toàn ASCII."""
    head = f"REC {scenario} {clock(ts)} / {clock(duration)}"
    if scenario != "gestures":
        return f"{head}  KHONG lam cu chi", None
    done = sum(b <= ts for _, b, _ in schedule)
    active = [(b, cls) for a, b, cls in schedule if a <= ts < b]
    if active:
        b, cls = active[0]
        return f"{head}  {done}/{len(schedule)}", f"LAM: {config.CLASSES[cls]}  {b - ts:.0f}"
    return f"{head}  {done}/{len(schedule)}", "nghi - tay de yen"


def run_record(args):
    gestures = args.scenario == "gestures"
    schedule = (prompt_schedule(config.BENCH_GESTURES_PER_CLASS,
                                np.random.default_rng(args.seed)) if gestures else [])
    duration = schedule[-1][1] + config.BENCH_REST_SEC if gestures else args.minutes * 60
    path = session_path(args.scenario, args.out)
    recorder = LandmarkRecorder()
    predictor = LivePredictor(make_model(args.model))
    fsm, meter = ActivationFSM(), FpsMeter()
    last, commands, complete = None, [], False
    print(f"Ghi '{args.scenario}' trong {clock(duration)} vào {relative_to_root(path)}. "
          "Không phím nào được gửi. q để dừng sớm.", flush=True)
    with HandTracker() as tracker:
        try:
            for frame_bgr, ts in iter_frames(args.source):
                h, w = frame_bgr.shape[:2]
                xy, present, _ = tracker.process(frame_bgr, seconds_to_ms(ts))
                recorder.add(ts, xy, present, w, h)
                meter.tick(ts)
                prediction = predictor.update(ts, xy, w, h)
                if prediction is not None:
                    last = prediction
                    command = fsm.update(prediction.label, prediction.confidence,
                                         prediction.presence, prediction.ts)
                    if command is not None:
                        commands.append((ts, command))
                if ts >= duration:
                    complete = True
                    break
                if not args.no_display:
                    head, big = record_screen(args.scenario, ts, duration, schedule)
                    lines, colors, _ = screen_lines(last, meter.rolling_fps, state=fsm.state,
                                                    command=recent_command(commands, ts))
                    cv2.imshow(WINDOW, make_display(frame_bgr, xy, [head, *lines],
                                                    big_text=big,
                                                    line_colors=[config.COLOR_ALERT,
                                                                 *colors]))
                    if read_key() in config.QUIT_KEYS:
                        break
        finally:
            cv2.destroyAllWindows()
    if not recorder.ts:
        raise SystemExit("Không ghi được frame nào.")
    ts = np.asarray(recorder.ts) - recorder.ts[0]
    segments = prompt_segments(ts, schedule)
    recorder.save(path, segments=segments, src_labels=["prompt"] * len(segments),
                  scenario=args.scenario, model=args.model, complete=complete,
                  prompts=[list(p) for p in schedule])
    print(f"Đã ghi {ts[-1] / 60:.1f} phút{'' if complete else ' (dừng sớm)'}, "
          f"{len(segments)} lời nhắc. Lúc ghi, {args.model} phát {len(commands)} lệnh "
          f"— số chính thức tính bằng: python scripts/bench.py analyze")


# --------------------------------------------------------------------------
# analyze
# --------------------------------------------------------------------------

def fsm_factory(conf_fire, k, on_transition=None):
    """Máy trạng thái của một hàng bảng đánh đổi: ``CONF_FIRE`` và ``k`` đổi, mọi
    thứ khác theo ``config.py``."""
    return partial(ActivationFSM, conf_fire=conf_fire,
                   conf_hold=min(config.CONF_HOLD, conf_fire),
                   k_of_n=(k, config.K_OF_N[1]), on_transition=on_transition)


class ConsensusLog:
    """``on_transition`` ghi độ trễ đồng thuận: từ lúc mở ứng viên tới lúc phát lệnh."""

    def __init__(self):
        self.opened, self.delays = None, []

    def __call__(self, ts, previous, state, reason):
        if state == CANDIDATE:
            self.opened = ts
        elif previous == CANDIDATE and state == COOLDOWN:
            self.delays.append(ts - self.opened)


def gesture_cores(path, timeline):
    """Khoảnh khắc chính (giây) của từng cử chỉ trong ``timeline.gestures``, cùng
    thứ tự; ``None`` ở cử chỉ không đo được."""
    ts, xy, w, h, segments, src_labels, _ = load_clip(path)
    segments = np.asarray(segments).reshape(-1, 3)
    cores = core_times(ts, xy, w, h, segments, src_labels)
    by_start = {(int(cls), float(ts[int(start)])): cores.get(k)
                for k, (start, _, cls) in enumerate(segments)
                if cls != 0 and int(start) < len(ts)}
    return [by_start.get((cls, start)) for cls, start, _, _ in timeline.gestures]


def score(timelines, labels, confidences, conf_fire, k, cores=None):
    """Một cấu hình máy trạng thái trên một nhóm video.

    Args:
        labels, confidences: mỗi video một mảng như ``events.scatter``.
        cores: ``clip → list giây`` của :func:`gesture_cores`.

    Returns:
        dict của ``events.summarize_events``, cộng ``latency`` (giây từ khoảnh
        khắc chính tới lệnh, mỗi lệnh đúng một số) và ``consensus`` (giây từ lúc
        mở ứng viên tới lúc phát, mỗi lệnh một số).
    """
    log = ConsensusLog()
    results = evaluate_timelines(timelines, labels, confidences,
                                 fsm_factory(conf_fire, k, log))
    latency = []
    for r in results:
        core = (cores or {}).get(r["clip"], [])
        latency += [r["commands"][i][0] - core[j] for i, j in r["match"]["tp"]
                    if j < len(core) and core[j] is not None]
    return {**summarize_events(results), "latency": latency, "consensus": log.delays}


def pooled_score(paths, timelines, predictions, conf_fire, k):
    """:func:`score` cho cả một nhóm phiên: lệnh, cử chỉ cộng dồn; nhầm/phút
    chia TỔNG thời lượng — phiên 10 phút nặng gấp mười phiên 1 phút.

    Args:
        timelines: ``phiên → Timeline``; predictions: ``phiên → events.scatter``.

    Returns:
        dict của :func:`score`, hoặc ``None`` khi nhóm không có phiên nào.
    """
    if not paths:
        return None
    return score([timelines[p] for p in paths], [predictions[p][0][0] for p in paths],
                 [predictions[p][1][0] for p in paths], conf_fire, k)


def valid_share(timelines):
    """Tỉ lệ lần dự đoán có cửa sổ hợp lệ — có tay trong khung để mô hình chạy."""
    n = sum(t.valid.size for t in timelines)
    return sum(int(t.valid.sum()) for t in timelines) / n if n else float("nan")


def per_hand_minute(s, timelines):
    """Lệnh nhầm mỗi phút CÓ TAY: lệnh nhầm chỉ phát được khi mô hình chạy, nên
    phiên ít thấy tay cho nhầm/phút thấp mà không nói gì về mô hình. NaN khi
    không có phút nào thấy tay — chưa đo, không phải 0."""
    hand = sum(t.duration * valid_share([t]) for t in timelines if t.valid.size) / 60
    return s["false_per_min"] * s["minutes"] / hand if s and hand else float("nan")


def median(values):
    return float(np.median(values)) if len(values) else float("nan")


SWIPES, ZOOMS = ("swipe_left", "swipe_right"), ("zoom_in", "zoom_out")
GESTURE_COLUMNS = ("recall", "recall_swipes", "recall_zooms", "cmds_per_gesture",
                   "commands_per_prompt", "duplicates_per_gesture")


def gesture_metrics(s):
    """Chỉ số của một phiên có lời nhắc, từ :func:`score`: recall chung và theo
    nhóm vuốt/zoom, lệnh đúng loại trên một cử chỉ, mọi lệnh chia số lời nhắc
    (định nghĩa của SPEC), và lệnh phát trùng trên một cử chỉ. NaN khi phiên
    không có lời nhắc nào."""
    if not s["n_gestures"]:
        return dict.fromkeys(GESTURE_COLUMNS, np.nan)
    recall = {r["class"]: r["recall"] if r["n_gestures"] else np.nan for r in s["per_class"]}
    return {"recall": s["recall"],
            "recall_swipes": float(np.nanmean([recall[c] for c in SWIPES])),
            "recall_zooms": float(np.nanmean([recall[c] for c in ZOOMS])),
            "cmds_per_gesture": s["cmds_per_gesture"],
            "commands_per_prompt": s["n_commands"] / s["n_gestures"],
            "duplicates_per_gesture": s["cmds_per_gesture"] - s["recall"]}


def predict(model_name, X, F):
    """Nhãn và độ tin của mô hình trên các cửa sổ hợp lệ (có thể không có cửa sổ nào)."""
    if len(X) == 0:
        return np.empty(0, dtype=np.int64), np.empty(0)
    labels, confidences, _ = label_confidence(model_name, F, X)
    return labels, confidences


def processing_ms(speed_run=None):
    """Thời gian xử lý một frame (ms) theo mô hình, trung bình các mức ánh sáng của
    một lần ``bench.py speed`` — mặc định lần gần nhất; ``{}`` khi chưa đo."""
    if speed_run is None:
        runs = sorted((config.PHASE10_RESULTS_DIR / "speed").glob("run_*"))
        speed_run = runs[-1] if runs else None
    path = Path(speed_run) / "speed.csv" if speed_run else None
    if path is None or not path.is_file():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_model = {}
    for r in rows:
        by_model.setdefault(r["model"], []).append(float(r["processing_ms"]))
    return {m: float(np.mean(v)) for m, v in by_model.items()}


def run_analyze(args):
    started = time.perf_counter()
    n = config.K_OF_N[1]
    sessions = []
    for path in sorted(Path(args.sessions).glob("*.npz")):
        timeline, X, F = clip_stream(path)
        scenario = clip_meta(path).get("scenario", path.stem.rsplit("_", 1)[0])
        sessions.append((path, scenario, timeline, X, F))
    if not sessions:
        print(f"Chưa có phiên nào trong {relative_to_root(Path(args.sessions))} — chỉ chấm "
              "video val. Ghi phiên bằng: python scripts/bench.py record <kịch bản>")
    val_paths, _ = clip_paths(read_splits()["val"])
    val_timelines, val_X, val_F = clip_streams(val_paths)
    val_cores = {t.clip: gesture_cores(p, t) for p, t in zip(val_paths, val_timelines)}
    speed = processing_ms(args.speed)
    print(f"{len(sessions)} phiên webcam, {len(val_paths)} video val "
          f"({time.perf_counter() - started:.0f} s).", flush=True)

    timelines = {p: t for p, _, t, _, _ in sessions}
    groups = {sc: [p for p, scenario, *_ in sessions if scenario == sc] for sc in SCENARIOS}
    members = {**groups, "live": [p for sc in config.BENCH_SCENARIOS for p in groups[sc]]}
    coverage = {sc: (sum(timelines[p].duration for p in groups[sc]) / 60,
                     valid_share([timelines[p] for p in groups[sc]]))
                for sc in SCENARIOS if groups[sc]}

    session_rows, tradeoff_rows, latency_rows = [], [], []
    for model in args.models:
        val_per = scatter(val_timelines, *predict(model, val_X, val_F))
        per_session = {p: scatter([t], *predict(model, X, F)) for p, _, t, X, F in sessions}
        for conf_fire, k in config.FSM_TRADEOFF:
            key = {"model": model, "conf_fire": conf_fire, "k_of_n": f"{k}/{n}"}
            val = score(val_timelines, *val_per, conf_fire, k, val_cores)
            for path, scenario, timeline, _, _ in sessions:
                s = score([timeline], *per_session[path], conf_fire, k)
                session_rows.append({
                    "session": path.stem, "scenario": scenario, **key,
                    "minutes": s["minutes"], "valid_share": valid_share([timeline]),
                    "n_commands": s["n_commands"], "false_per_min": s["false_per_min"],
                    "n_gestures": s["n_gestures"], **gesture_metrics(s)})
            pooled = {sc: pooled_score(paths, timelines, per_session, conf_fire, k)
                      for sc, paths in members.items()}
            gestures = (gesture_metrics(pooled["gestures"]) if pooled["gestures"]
                        else dict.fromkeys(GESTURE_COLUMNS, np.nan))
            tradeoff_rows.append({
                **key, "event_f1_val": val["f1"], "recall_val": val["recall"],
                "false_per_min_val": val["false_per_min"],
                **{f"false_per_min_{sc}": pooled[sc]["false_per_min"] if pooled[sc]
                   else np.nan for sc in (*config.BENCH_SCENARIOS, "live")},
                **{f"false_per_hand_min_{sc}": per_hand_minute(
                    pooled[sc], [timelines[p] for p in members[sc]])
                   for sc in (*config.BENCH_SCENARIOS, "live")},
                **{f"{c}_live": v for c, v in gestures.items()},
                "latency_val": median(val["latency"]),
                "processing_ms": speed.get(model, np.nan)})
            total, consensus = median(val["latency"]), median(val["consensus"])
            latency_rows.append({
                **key, "n_commands": len(val["latency"]), "total_median": total,
                "consensus_median": consensus, "prediction_mean": config.STRIDE_SEC / 2,
                "window_est": total - consensus - config.STRIDE_SEC / 2,
                "processing_ms": speed.get(model, np.nan)})
        print(f"[{model}] xong ({time.perf_counter() - started:.0f} s)", flush=True)

    run_dir = next_run_dir(args.out)
    notes = [f"Ba cấu hình của FSM_TRADEOFF; CONF_HOLD = min({config.CONF_HOLD:g}, CONF_FIRE), "
             f"COOLDOWN_SEC {config.COOLDOWN_SEC:g}, MIN_PRESENCE {config.MIN_PRESENCE:g}.",
             "Phiên webcam chạy lại qua đúng đường ống của demo; *_val là 27 video val của IPN.",
             "Nhầm/phút của từng kịch bản và false_per_min_live (cả ba kịch bản) GỘP theo "
             "thời lượng: tổng lệnh nhầm chia tổng số phút. Chỉ số *_live của phiên gestures "
             "cũng gộp: cộng dồn lời nhắc và lệnh của mọi phiên.",
             "Thời lượng và tỉ lệ lần dự đoán có tay (valid_share) theo kịch bản: "
             + "; ".join(f"{sc} {minutes:.1f} phút, {share:.0%}"
                         for sc, (minutes, share) in coverage.items())
             + ". Kịch bản gần 0% tay thì nhầm/phút gần 0 vì camera không thấy tay, "
             "không phải vì mô hình tốt. false_per_hand_min_* chia cho số phút CÓ TAY "
             "(mô hình chỉ phát lệnh khi thấy tay); trống = chưa đo.",
             "Phiên gestures: cmds_per_gesture là lệnh đúng loại trong vùng khớp trên một cử "
             "chỉ; commands_per_prompt là MỌI lệnh chia số lời nhắc (định nghĩa của SPEC); "
             "duplicates_per_gesture = cmds_per_gesture − recall. Gần 1,0 mà recall thấp "
             "nghĩa là cử chỉ bị sót và cử chỉ bị phát trùng bù cho nhau.",
             "Độ trễ (giây, video val): từ khoảnh khắc chính của cử chỉ tới lúc phát lệnh, "
             "trung vị trên các lệnh đúng; processing_ms của lần bench.py speed gần nhất."]
    write_with_notes(tradeoff_rows, list(tradeoff_rows[0]), run_dir / "tradeoff", notes)
    write_with_notes(latency_rows, list(latency_rows[0]), run_dir / "latency", notes + [
        "window_est = total − consensus − prediction_mean (dự đoán: trung bình nửa nhịp)."])
    if session_rows:
        write_with_notes(session_rows, list(session_rows[0]), run_dir / "sessions", notes)
    write_manifest(run_dir, {"script": "bench analyze", "models": args.models,
                             "sessions": [relative_to_root(p) for p, *_ in sessions],
                             "val_clips": len(val_paths), "speed": speed,
                             "seconds": time.perf_counter() - started})

    print(f"\n{'mô hình':<8}{'FIRE':>6}{'k/n':>5}{'F1 val':>8}{'nhầm/ph val':>12}"
          + "".join(f"{sc[:8]:>9}" for sc in config.BENCH_SCENARIOS)
          + f"{'/ph có tay':>11}{'R vuốt':>8}{'R zoom':>8}{'lệnh/cc':>9}{'lệnh/nhắc':>10}{'trễ val':>9}")
    for r in tradeoff_rows:
        print(f"{r['model']:<8}{r['conf_fire']:6.2f}{r['k_of_n']:>5}{r['event_f1_val']:8.3f}"
              f"{r['false_per_min_val']:12.2f}"
              + "".join(f"{r[f'false_per_min_{sc}']:9.2f}" for sc in config.BENCH_SCENARIOS)
              + f"{r['false_per_hand_min_live']:11.2f}{r['recall_swipes_live']:8.2f}{r['recall_zooms_live']:8.2f}"
              f"{r['cmds_per_gesture_live']:9.2f}{r['commands_per_prompt_live']:10.2f}"
              f"{r['latency_val']:9.2f}")
    print("\nKịch bản (nhầm/phút gộp theo thời lượng): " + "; ".join(
        f"{sc} {minutes:.1f} phút, có tay {share:.0%}" for sc, (minutes, share) in coverage.items()))
    print(f"Bảng: {relative_to_root(run_dir)}")


def main():
    setup_console()
    parser = make_parser(__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    speed = commands.add_parser("speed", help="FPS và phân rã thời gian")
    speed.add_argument("--light", required=True,
                       help="nhãn mức ánh sáng của lần đo, ví dụ bright hoặc dim")
    speed.add_argument("--models", nargs="+", default=list(config.MODEL_NAMES),
                       choices=config.MODEL_NAMES)
    speed.add_argument("--sec", type=float, default=config.BENCH_SPEED_SEC,
                       help="giây đo mỗi mô hình, sau thời gian khởi động")
    speed.add_argument("--out", default=config.PHASE10_RESULTS_DIR / "speed",
                       help="thư mục chứa run_NN (mặc định %(default)s)")
    add_source_arg(speed)

    record = commands.add_parser("record", help="ghi một phiên kịch bản")
    record.add_argument("scenario", choices=SCENARIOS)
    record.add_argument("--minutes", type=float, default=config.BENCH_SCENARIO_MIN,
                        help="thời lượng của reading, typing, talking")
    record.add_argument("--model", default="hybrid", choices=config.MODEL_NAMES,
                        help="mô hình hiện trên màn hình lúc ghi — chỉ để xem; "
                             "analyze chấm mọi mô hình")
    record.add_argument("--seed", type=int, default=config.SEED,
                        help="thứ tự lời nhắc của gestures")
    record.add_argument("--out", default=None, help="thư mục phiên (mặc định BENCH_SESSIONS_DIR)")
    record.add_argument("--no-display", action="store_true")
    add_source_arg(record)

    analyze = commands.add_parser("analyze", help="chấm các phiên đã ghi")
    analyze.add_argument("--sessions", default=config.BENCH_SESSIONS_DIR)
    analyze.add_argument("--models", nargs="+", default=list(config.MODEL_NAMES),
                         choices=config.MODEL_NAMES)
    analyze.add_argument("--speed", default=None,
                         help="thư mục run của bench.py speed (mặc định lần gần nhất)")
    analyze.add_argument("--out", default=config.PHASE10_RESULTS_DIR / "analyze",
                         help="thư mục chứa run_NN (mặc định %(default)s) — lần chạy thử "
                              "nên ghi ra chỗ khác")

    args = parser.parse_args()
    {"speed": run_speed, "record": run_record, "analyze": run_analyze}[args.command](args)


if __name__ == "__main__":
    main()
