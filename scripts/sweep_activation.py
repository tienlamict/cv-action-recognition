"""Hai bảng đánh đổi của Phase 9 trên video val — không học lại mô hình nào.

1. MIN_PRESENCE lúc chạy (FSM_PRESENCE_SWEEP): tỉ lệ bước có tay mà bộ đệm đòi
   trước khi trả một cửa sổ. Nâng nó để chống kích hoạt nhầm thì bỏ sót đúng
   những cú vuốt nhanh, vì cửa sổ vuốt nhanh hay mất tay nhất (SPEC Phase 9).
   Số liệu cho results/phase9/tradeoff.md.
2. Tham số máy trạng thái (FSM_FIRE_SWEEP × FSM_K_SWEEP, n của K_OF_N giữ
   nguyên): số lệnh trên một cử chỉ phải nằm trong FSM_CMDS_RANGE (Định nghĩa
   hoàn thành Phase 9).

Video val chạy MỘT lần qua đúng WindowStream của demo, với ngưỡng thấp nhất của
lưới. Mỗi mô hình đã lưu chấm mọi cửa sổ một lần. Mỗi ngưỡng cao hơn chỉ chặn bớt
các lần dự đoán (events.gate_presence — trùng việc chạy lại video). Mô hình học
với MIN_PRESENCE: cửa sổ có tỉ lệ có tay thấp hơn là thứ chúng chưa từng thấy.

Bảng ra results/phase9/sweep_activation/run_NN/:
  presence_by_class  tỉ lệ có tay của cửa sổ val theo lớp (windows.npz), và phần
                     cửa sổ mỗi ngưỡng cao hơn sẽ chặn
  confidence_by_class  độ tin của cửa sổ cử chỉ val được đoán ĐÚNG, theo mô hình:
                     phần đạt từng mức CONF_FIRE của lưới — máy trạng thái chỉ mở
                     ứng viên từ mức đó, nên thang độ tin của mô hình quyết định
                     nó phát được bao nhiêu lệnh
  presence_sweep     mô hình × ngưỡng: phần thời gian có cửa sổ, F1 sự kiện, recall
                     vuốt và zoom, lệnh trên một cử chỉ, lệnh nhầm mỗi phút (tổng,
                     lúc D0X, lúc tay chỉ trỏ)
  fsm_grid           mô hình × CONF_FIRE × k: cùng các cột, cộng cờ in_range

Ví dụ:
    python scripts/sweep_activation.py
    python scripts/sweep_activation.py --models hybrid lstm
"""

import sys
import time
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.activation import ActivationFSM  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.evaluation import label_confidence, split_features  # noqa: E402
from src.events import (clip_paths, clip_streams, evaluate_timelines,  # noqa: E402
                        gate_presence, scatter, summarize_events)
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits, split_of  # noqa: E402
from src.tables import write_table  # noqa: E402

SWIPES, ZOOMS = ("swipe_left", "swipe_right"), ("zoom_in", "zoom_out")
EVENT_COLUMNS = ["valid_share", "event_f1", "precision", "recall", "recall_swipes",
                 "recall_zooms", "cmds_per_gesture", "false_per_min",
                 "false_per_min_D0X", "false_per_min_pointing"]


def presence_by_class(windows_path, splits, thresholds):
    """Tỉ lệ có tay của các cửa sổ val theo lớp, và phần cửa sổ mỗi ngưỡng
    trong ``thresholds`` sẽ chặn."""
    with np.load(windows_path, allow_pickle=False) as data:
        pick = split_of(data["subject"], splits) == "val"
        y, presence = data["y"][pick], data["presence"][pick]
    rows = []
    for c, name in enumerate(config.CLASSES):
        p = presence[y == c]
        rows.append({"class": name, "n_windows": int(p.size),
                     "median_presence": float(np.median(p)),
                     **{f"blocked_at_{t:g}": float(np.mean(p < t)) for t in thresholds}})
    return rows


def confidence_by_class(models, splits, fires):
    """Độ tin của các cửa sổ cử chỉ val (windows.npz) mà mỗi mô hình đoán ĐÚNG:
    trung vị, và phần đạt từng mức trong ``fires``."""
    with np.load(config.WINDOWS_NPZ, allow_pickle=False) as data:
        F, y, pick = split_features(data["X"], data["y"], data["presence"],
                                    data["subject"], splits, "val")
        X = data["X"][pick]
    rows = []
    for model in models:
        labels, confidences, _ = label_confidence(model, F, X)
        for c in range(1, len(config.CLASSES)):
            conf = confidences[(y == c) & (labels == c)]
            rows.append({"model": model, "class": config.CLASSES[c], "n_correct": int(conf.size),
                         "median_confidence": float(np.median(conf)) if conf.size else np.nan,
                         **{f"share_ge_{f:g}": float(np.mean(conf >= f)) if conf.size else np.nan
                            for f in fires}})
    return rows


def event_row(timelines, labels, confidences, event_filter):
    """Các chỉ số mức sự kiện của một cấu hình."""
    s = summarize_events(evaluate_timelines(timelines, labels, confidences, event_filter))
    recall = {r["class"]: r["recall"] for r in s["per_class"]}
    false = {}
    for r in s["false_by_src"]:
        if r["kind"] == "none":
            false[r["src_label"]] = false.get(r["src_label"], 0.0) + r["per_min"]
    return {"valid_share": (sum(int(t.valid.sum()) for t in timelines)
                            / sum(t.ts.size for t in timelines)),
            "event_f1": s["f1"], "precision": s["precision"], "recall": s["recall"],
            "recall_swipes": float(np.mean([recall[c] for c in SWIPES])),
            "recall_zooms": float(np.mean([recall[c] for c in ZOOMS])),
            "cmds_per_gesture": s["cmds_per_gesture"], "false_per_min": s["false_per_min"],
            "false_per_min_D0X": false.get("D0X", 0.0),
            "false_per_min_pointing": sum(false.get(c, 0.0)
                                          for c in config.POINTING_SRC_LABELS)}


def print_rows(title, rows, keys):
    print(f"\n{title}")
    print("  " + "".join(f"{k[:12]:>13}" for k in keys))
    for r in rows:
        print("  " + "".join(f"{r[k]:>13.3f}" if isinstance(r[k], float) else f"{r[k]!s:>13}"
                             for k in keys))


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--models", nargs="+", default=list(config.MODEL_NAMES),
                        choices=config.MODEL_NAMES)
    args = parser.parse_args()

    splits = read_splits()
    paths, skipped = clip_paths(splits["val"])
    low = min(config.FSM_PRESENCE_SWEEP)
    started = time.perf_counter()
    timelines, X, F = clip_streams(paths, min_presence=low)
    print(f"{len(paths)} video val, {X.shape[0]} cửa sổ hợp lệ với ngưỡng {low:g} "
          f"({time.perf_counter() - started:.0f} s).")

    run_dir = next_run_dir(config.PHASE9_RESULTS_DIR / "sweep_activation")
    above = [t for t in config.FSM_PRESENCE_SWEEP if t > config.MIN_PRESENCE]
    presence_rows = presence_by_class(config.WINDOWS_NPZ, splits, above)
    write_table(presence_rows, list(presence_rows[0]), run_dir / "presence_by_class")
    confidence_rows = confidence_by_class(args.models, splits, config.FSM_FIRE_SWEEP)
    write_table(confidence_rows, list(confidence_rows[0]), run_dir / "confidence_by_class")

    lo, hi = config.FSM_CMDS_RANGE
    n = config.K_OF_N[1]
    sweep_rows, grid_rows = [], []
    for model in args.models:
        labels, confidences, _ = label_confidence(model, F, X)
        per_clip = scatter(timelines, labels, confidences)
        for threshold in config.FSM_PRESENCE_SWEEP:
            gated = gate_presence(timelines, *per_clip, threshold)
            sweep_rows.append({"model": model, "min_presence": threshold,
                               **event_row(*gated, "fsm")})
        gated = gate_presence(timelines, *per_clip, config.MIN_PRESENCE)
        for fire in config.FSM_FIRE_SWEEP:
            for k in config.FSM_K_SWEEP:
                fsm = partial(ActivationFSM, conf_fire=fire,
                              conf_hold=min(config.CONF_HOLD, fire), k_of_n=(k, n))
                row = event_row(*gated, fsm)
                grid_rows.append({"model": model, "conf_fire": fire, "k_of_n": f"{k}/{n}",
                                  **row, "in_range": lo <= row["cmds_per_gesture"] <= hi})
        print(f"[{model}] xong ({time.perf_counter() - started:.0f} s)", flush=True)

    write_table(sweep_rows, ["model", "min_presence", *EVENT_COLUMNS],
                run_dir / "presence_sweep")
    write_table(grid_rows, ["model", "conf_fire", "k_of_n", *EVENT_COLUMNS, "in_range"],
                run_dir / "fsm_grid")
    print_rows("Tỉ lệ có tay của cửa sổ val, theo lớp", presence_rows, list(presence_rows[0]))
    print_rows("Độ tin của cửa sổ cử chỉ val đoán đúng", confidence_rows,
               list(confidence_rows[0]))
    print_rows("MIN_PRESENCE lúc chạy (máy trạng thái theo config)", sweep_rows,
               ["model", "min_presence", *EVENT_COLUMNS])
    print_rows(f"Tham số máy trạng thái (MIN_PRESENCE {config.MIN_PRESENCE:g}; "
               f"lệnh trên một cử chỉ phải trong [{lo:g}, {hi:g}])", grid_rows,
               ["model", "conf_fire", "k_of_n", "event_f1", "recall", "cmds_per_gesture",
                "false_per_min", "in_range"])
    write_manifest(run_dir, {"script": "sweep_activation", "models": args.models,
                             "clips": len(paths), "skipped_length_mismatch": skipped,
                             "stream_min_presence": low,
                             "seconds": time.perf_counter() - started})
    print(f"\nBảng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
