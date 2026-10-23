"""Đánh giá một mô hình đã có trên một tập, ở hai mức (Phase 8).

Mức CỬA SỔ (luôn chạy): macro-F1, precision/recall/F1 từng lớp, ma trận nhầm
lẫn thô và chuẩn hoá theo hàng (hình nhiệt có số trong từng ô), hai đường cơ sở,
và cửa sổ none bị báo nhầm theo nhãn gốc IPN.

Mức SỰ KIỆN (--events BỘ_LỌC): chạy hệ thống hoàn chỉnh trên các video IPN LIÊN
TỤC của tập — đúng đường đi của webcam, qua src/events.py — rồi khớp chuỗi lệnh
với chuỗi cử chỉ đã gán nhãn:
  - TP: lệnh đúng loại phát từ lúc cử chỉ bắt đầu tới lúc kết thúc +
    EVENT_TOL_SEC (EVENT_MATCH = "span"; con số theo định nghĩa ban đầu của
    SPEC, ±EVENT_TOL_SEC quanh lúc kết thúc, in kèm để đối chiếu);
  - FP: lệnh không khớp cử chỉ nào, gồm cả lệnh thứ hai cho cùng cử chỉ;
  - FN: cử chỉ không có lệnh nào khớp;
cộng số lệnh trên một cử chỉ, lệnh nhầm mỗi phút, và lệnh nhầm theo nhãn gốc IPN.
Bộ lọc biến chuỗi nhãn thành chuỗi lệnh và là THAM SỐ: raw (mỗi lần dự đoán ra
cử chỉ là một lệnh), edge (mỗi chuỗi dự đoán liền nhau cùng lớp là một lệnh).
Phase 9 thêm máy trạng thái vào src/events.EVENT_FILTERS; file này không phải sửa.

Mặc định là tập val. Tập test và real_test chỉ chạy ĐÚNG MỘT LẦN ở cuối dự án
(luật 13): script từ chối chạy nếu thiếu --final, và khi chạy thì ghi một dòng
vào results/TEST_USED.log — tên tập, thời điểm, mô hình, dòng lệnh, hằng số —
TRƯỚC khi đọc dữ liệu của tập đó.

Ví dụ:
    python scripts/evaluate.py --model rf
    python scripts/evaluate.py --model lstm --events edge
    python scripts/evaluate.py --model hybrid --events raw
    python scripts/evaluate.py --model rf --split test --final --events edge
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.evaluation import (alarm_clusters, baselines, event_rows,  # noqa: E402
                            false_alarm_rows, guard_split, label_confidence,
                            split_features, summarize, upsert_comparison,
                            write_summary)
from src.events import (EVENT_FILTERS, clip_paths, clip_streams,  # noqa: E402
                        evaluate_timelines, scatter, summarize_events)
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import SPLIT_NAMES, read_splits  # noqa: E402
from src.tables import write_table  # noqa: E402
from src.viz import plot_confusion  # noqa: E402

EVENT_CLASS_COLUMNS = ["class", "n_gestures", "n_commands", "tp", "fp", "fn",
                       "precision", "recall", "f1", "cmds_per_gesture", "early"]


def event_level(model, split, filter_name, splits):
    """Chạy hệ thống trên mọi video của ``split`` và gộp mức sự kiện.

    Returns:
        ``(summary, info)`` — ``summary`` của ``events.summarize_events`` theo
        ``EVENT_MATCH``; ``info`` đếm video đã chạy, video bỏ vì lệch nhãn, số
        lần dự đoán, và F1 theo các cách khớp còn lại.
    """
    source = "self" if split.startswith("real") else "ipn"
    paths, skipped = clip_paths(splits.get(split, []), config.LANDMARKS_DIR / source)
    if not paths:
        raise SystemExit(f"Tập {split} không có video nào trong "
                         f"{relative_to_root(config.LANDMARKS_DIR / source)}.")
    started = time.perf_counter()
    timelines, X, F = clip_streams(paths)
    labels, confidences, _ = label_confidence(model, F, X)
    per_clip = scatter(timelines, labels, confidences)
    summary = summarize_events(evaluate_timelines(timelines, *per_clip, filter_name))
    info = {"clips": len(paths), "skipped_length_mismatch": skipped,
            "predictions": int(sum(t.ts.size for t in timelines)),
            "valid_predictions": int(sum(t.valid.sum() for t in timelines)),
            "seconds": time.perf_counter() - started,
            "f1_other_match": {mode: summarize_events(evaluate_timelines(
                timelines, *per_clip, filter_name, mode=mode))["f1"]
                for mode in config.EVENT_MATCH_MODES if mode != config.EVENT_MATCH}}
    return summary, info


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--model", required=True, choices=config.MODEL_NAMES)
    parser.add_argument("--split", default="val", choices=SPLIT_NAMES)
    parser.add_argument("--final", action="store_true",
                        help="bắt buộc với test/real_test — chỉ chạy một lần, ở cuối")
    parser.add_argument("--events", default=None, choices=list(EVENT_FILTERS),
                        help="đánh giá thêm mức sự kiện trên video liên tục, với "
                             "bộ lọc sự kiện này")
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    args = parser.parse_args()

    # Chốt luật 13 trước mọi thứ khác, kể cả trước khi nạp mô hình.
    guard_split(args.split, args.final, args.model, details={"events": args.events})

    splits = read_splits()
    with np.load(args.windows, allow_pickle=False) as data:
        F, y, pick = split_features(data["X"], data["y"], data["presence"],
                                    data["subject"], splits, args.split)
        X = data["X"][pick]
        clip, t0, src = (data[k][pick] for k in ("clip", "t0", "src_label"))
    if y.size == 0:
        raise SystemExit(f"Tập {args.split} không có cửa sổ nào.")

    pred, _, details = label_confidence(args.model, F, X)
    summary = summarize(y, pred)
    random_f1, none_f1 = baselines(y)

    run_dir = next_run_dir(config.PHASE8_RESULTS_DIR / "evaluate")
    write_summary(summary, run_dir)
    plot_confusion(summary["confusion"], summary["confusion_row"], config.CLASSES,
                   run_dir / "confusion.png",
                   title=f"{args.model} — tập {args.split} ({y.size} cửa sổ)")
    events = event_rows(y, pred, clip, t0)
    write_table(events, list(events[0]), run_dir / "events_approx")
    alarms = false_alarm_rows(y, pred, src)
    write_table(alarms, list(alarms[0]), run_dir / "none_false_alarms_by_src")
    clusters, minutes = alarm_clusters(y, pred, clip, t0)
    row = {"model": args.model, "split": args.split, "n_windows": int(y.size),
           "macro_f1": summary["macro_f1"], "baseline_random": random_f1,
           "baseline_none": none_f1, "run": relative_to_root(run_dir)}

    event_summary = event_info = None
    if args.events:
        event_summary, event_info = event_level(args.model, args.split, args.events,
                                                splits)
        write_table(event_summary["per_class"], EVENT_CLASS_COLUMNS,
                    run_dir / "events_per_class")
        false_rows = event_summary["false_by_src"]
        write_table(false_rows, ["kind", "src_label", "n", "per_min",
                                 *config.CLASSES[1:]], run_dir / "events_false_by_src")
        row.update(event_filter=args.events, event_f1=event_summary["f1"],
                   cmds_per_gesture=event_summary["cmds_per_gesture"],
                   false_per_min=event_summary["false_per_min"])

    table = upsert_comparison(row)
    write_manifest(run_dir, {
        "script": "evaluate", **row, "model_details": details,
        "none_alarm_rate": float(np.mean(pred[y == 0] != 0)),
        "alarm_clusters_per_min": clusters / minutes,
        "events": None if event_summary is None else {
            **{k: v for k, v in event_summary.items()
               if k not in ("per_class", "false_by_src")}, **event_info}})

    print(f"{args.model} trên tập {args.split}: {y.size} cửa sổ\n")
    print(summary["report"])
    print(f"macro-F1 {summary['macro_f1']:.4f}   (ngẫu nhiên {random_f1:.4f}, "
          f"luôn none {none_f1:.4f})")
    print("Mức sự kiện xấp xỉ — cử chỉ có >= 1 cửa sổ được nhận đúng: "
          + ", ".join(f"{r['class']} {r['hit_1']:.0%}" for r in events))
    print(f"Cửa sổ none bị báo nhầm: {np.mean(pred[y == 0] != 0):.1%}, "
          f"{clusters / minutes:.1f} cụm mỗi phút none")
    if event_summary is not None:
        s = event_summary
        window = (f"từ lúc cử chỉ bắt đầu tới lúc kết thúc + {s['tol']:g} s"
                  if s["mode"] == "span" else f"±{s['tol']:g} s quanh lúc cử chỉ kết thúc")
        print(f"\nMức SỰ KIỆN, bộ lọc '{args.events}', vùng khớp {window} — "
              f"{s['n_clips']} video, {s['minutes']:.1f} phút, {s['n_gestures']} cử "
              f"chỉ, {s['n_commands']} lệnh ({event_info['seconds']:.0f} s):")
        print(f"{'lớp':<12}{'cử chỉ':>7}{'lệnh':>6}{'TP':>5}{'FP':>5}{'FN':>5}"
              f"{'P':>7}{'R':>7}{'F1':>7}{'lệnh/cc':>9}{'sớm':>5}")
        for r in s["per_class"]:
            print(f"{r['class']:<12}{r['n_gestures']:>7}{r['n_commands']:>6}{r['tp']:>5}"
                  f"{r['fp']:>5}{r['fn']:>5}{r['precision']:>7.3f}{r['recall']:>7.3f}"
                  f"{r['f1']:>7.3f}{r['cmds_per_gesture']:>9.2f}{r['early']:>5}")
        print(f"Gộp: P {s['precision']:.3f}, R {s['recall']:.3f}, F1 {s['f1']:.3f} "
              f"(macro {s['macro_f1']:.3f}); {s['cmds_per_gesture']:.2f} lệnh mỗi cử chỉ; "
              f"{s['false_per_min']:.2f} lệnh nhầm mỗi phút.")
        print("F1 theo cách khớp khác, để đối chiếu: " + ", ".join(
            f"'{m}' {f1:.3f}" for m, f1 in event_info["f1_other_match"].items()))
        print("Lệnh nhầm nhiều nhất theo lúc phát:")
        for r in s["false_by_src"][:6]:
            print(f"  {r['kind']:<12} {r['src_label'] or '(ngoài đoạn)':<6} {r['n']:>4} "
                  f"({r['per_min']:.2f}/phút)")
    print(f"\nBảng: {relative_to_root(run_dir)}; so sánh mô hình: "
          f"{relative_to_root(table)}")


if __name__ == "__main__":
    main()
