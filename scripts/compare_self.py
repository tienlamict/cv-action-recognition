"""So mô hình học trên IPN thuần (cũ) với mô hình học thêm dữ liệu tự quay (mới) — Phase 11.

Một lần chạy, một tập, mọi mô hình đi cạnh nhau. Mỗi bên có SELF_SEEDS hạt, vì LSTM
dao động mạnh theo hạt (selfdata.model_paths):

- cũ: IPN thuần; hạt SEED là chính mô hình demo (RF_MODEL_PATH + LSTM_MODEL_PATH);
- mới: IPN + real_tune, từ train_self.py.

Bảng in từng mô hình, rồi trung bình và khoảng (nhỏ nhất–lớn nhất) của mỗi bên.

Hai cấp đo:

1. CỬA SỔ: macro-F1 và F1 từng lớp của rừng, LSTM và mô hình ghép. val dùng
   windows.npz (IPN); real_test dùng self_real_test.npz, KHÔNG lọc.
2. LỆNH: mô hình ghép cộng máy trạng thái cấu hình cuối, chạy trên video liên tục
   của tập (val: video IPN; real_test: từng lần quay). Với real_test, đo thêm lệnh
   đầu tiên của mỗi lần quay: đúng / nhầm / sót. Đo hai cách: như quay, và nối thêm
   SELF_HOLD_SEC giây tay giữ yên — lúc dùng thật, luồng hình chạy tiếp sau cử chỉ,
   còn lần quay thì hết ngay.

real_test chỉ chạy ĐÚNG MỘT LẦN (luật 13): cần --final, và script ghi MỘT dòng vào
results/TEST_USED.log cho cả hai mô hình, trước khi đọc dữ liệu.

Ví dụ:
    python scripts/compare_self.py                         # val IPN
    python scripts/compare_self.py --split real_test --final
"""

import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config, selfdata  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.evaluation import (guard_split, label_confidence, split_features,  # noqa: E402
                            summarize)
from src.events import (clip_paths, clip_streams, evaluate_timelines,  # noqa: E402
                        scatter, summarize_events)
from src.io_data import load_clip, save_clip  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits  # noqa: E402
from src.tables import write_table  # noqa: E402

MODELS = ("rf", "lstm", "hybrid")
OUTCOMES = ("đúng", "nhầm", "sót")


SIDES = (("cũ", False), ("mới", True))


def variants():
    """Mọi mô hình đem so: ``"cũ s42"``… → đường dẫn rừng và LSTM."""
    out = {}
    for side, with_self in SIDES:
        for seed in config.SELF_SEEDS:
            rf, lstm = selfdata.model_paths(with_self, seed)
            out[f"{side} s{seed}"] = {"rf_path": rf, "lstm_path": lstm}
    return out


def side_rows(rows, keys, metrics):
    """Trung bình và khoảng của mỗi bên: gom các hàng cùng ``keys`` (trừ hạt)."""
    groups = {}
    for row in rows:
        side = row["variant"].split()[0]
        groups.setdefault((side, *(row[k] for k in keys)), []).append(row)
    out = []
    for (side, *rest), members in groups.items():
        row = {"variant": side, **dict(zip(keys, rest)), "n_seeds": len(members)}
        for m in metrics:
            values = np.array([r[m] for r in members], dtype=float)
            row.update({m: float(values.mean()), f"{m}_min": float(values.min()),
                        f"{m}_max": float(values.max())})
        out.append(row)
    return out


def window_level(split, splits):
    """macro-F1 và F1 từng lớp của từng (mô hình, biến thể)."""
    path = config.WINDOWS_NPZ if split == "val" else config.SELF_WINDOWS[split]
    with np.load(path, allow_pickle=False) as data:
        F, y, pick = split_features(data["X"], data["y"], data["presence"],
                                    data["subject"], splits, split)
        X = data["X"][pick]
    rows = []
    for name, paths in variants().items():
        for model in MODELS:
            pred, _, _ = label_confidence(model, F, X, **paths)
            summary = summarize(y, pred)
            rows.append({"variant": name, "model": model, "n_windows": int(y.size),
                         "macro_f1": summary["macro_f1"],
                         **{r["class"]: r["f1"] for r in summary["per_class"]}})
    return rows


def held(path, out_dir, rng, seconds=None, jitter_px=None):
    """Bản sao của một lần quay nối thêm ``seconds`` giây tay giữ yên: frame có tay
    cuối cùng lặp lại, rung ``jitter_px`` pixel. Nhãn không đổi.

    Returns:
        đường dẫn bản sao.
    """
    seconds = config.SELF_HOLD_SEC if seconds is None else seconds
    jitter_px = config.SELF_HOLD_JITTER_PX if jitter_px is None else jitter_px
    ts, xy, w, h, segments, src_labels, meta = load_clip(path)
    present = np.all(np.isfinite(xy.reshape(len(xy), -1)), axis=1)
    extra = int(round(seconds * config.CAM_FPS))
    last = xy[np.flatnonzero(present)[-1]] if present.any() else xy[-1]
    tail = last[None] + rng.normal(0.0, jitter_px, (extra, *xy.shape[1:])) / np.array([w, h])
    ts2 = np.concatenate([ts, ts[-1] + np.arange(1, extra + 1) / config.CAM_FPS])
    xy2 = np.concatenate([xy, tail.astype(xy.dtype)])
    meta = {k: v for k, v in meta.items() if k != "flip_applied"}
    out = Path(out_dir) / Path(path).parent.name / Path(path).name
    out.parent.mkdir(parents=True, exist_ok=True)
    save_clip(out, ts2, xy2, np.all(np.isfinite(xy2.reshape(len(xy2), -1)), axis=1),
              segments, src_labels, meta)
    return out


def take_outcomes(results):
    """Lệnh đầu tiên của từng lần quay so với cử chỉ của nó: lớp → Counter."""
    out = {config.CLASSES[k]: Counter() for k in range(1, len(config.CLASSES))}
    for r in results:
        if not r["gestures"]:
            continue
        want = r["gestures"][0][0]
        first = r["commands"][0][1] if r["commands"] else None
        outcome = "sót" if first is None else "đúng" if first == want else "nhầm"
        out[config.CLASSES[want]][outcome] += 1
    return out


def event_level(paths):
    """Mô hình ghép + máy trạng thái trên các video ``paths``, từng biến thể.

    Returns:
        dict tên biến thể → ``(summarize_events, kết quả từng video)``.
    """
    timelines, X, F = clip_streams(paths)
    out = {}
    for name, model_paths in variants().items():
        labels, confidences, _ = label_confidence("hybrid", F, X, **model_paths)
        results = evaluate_timelines(timelines, *scatter(timelines, labels, confidences),
                                     "fsm")
        out[name] = (summarize_events(results), results)
    return out


def main(argv=None):
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--split", choices=("val", "real_test"), default="val")
    parser.add_argument("--final", action="store_true",
                        help="bắt buộc với real_test — chỉ chạy một lần, ở cuối")
    args = parser.parse_args(argv)

    # Luật 13: chốt trước mọi thứ khác, kể cả trước khi nạp mô hình. Một dòng cho mọi mô hình.
    guard_split(args.split, args.final, "hybrid: cũ và mới, mọi hạt (compare_self.py)",
                details={name: {k: Path(v).name for k, v in p.items()}
                         for name, p in variants().items()})
    splits = read_splits()
    windows = window_level(args.split, splits)

    if args.split == "val":
        paths, _ = clip_paths(splits["val"])
        runs = {"video IPN": event_level(paths)}
    else:
        paths, _ = clip_paths(splits[args.split], config.SELF_LANDMARKS_DIR)
        rng = np.random.default_rng(config.SEED)
        with tempfile.TemporaryDirectory() as tmp:
            held_paths = [held(p, tmp, rng) for p in paths]
            runs = {"như quay": event_level(paths),
                    f"+{config.SELF_HOLD_SEC:g} s giữ yên": event_level(held_paths)}

    run_dir = next_run_dir(config.PHASE11_RESULTS_DIR / "compare_self")
    metrics = ["macro_f1", *config.CLASSES]
    write_table(windows, ["variant", "model", "n_windows", *metrics], run_dir / "windows")
    window_sides = side_rows(windows, ["model"], metrics)
    write_table(window_sides, list(window_sides[0]), run_dir / "windows_by_side")
    event_rows, take_rows = [], []
    for how, by_variant in runs.items():
        for name, (summary, results) in by_variant.items():
            event_rows.append({"how": how, "variant": name, "n_gestures": summary["n_gestures"],
                               "n_commands": summary["n_commands"], "precision": summary["precision"],
                               "recall": summary["recall"], "f1": summary["f1"],
                               "false_per_min": summary["false_per_min"],
                               "cmds_per_gesture": summary["cmds_per_gesture"]})
            if args.split != "val":
                outcomes = take_outcomes(results)
                for cls, counts in outcomes.items():
                    take_rows.append({"how": how, "variant": name, "class": cls,
                                      **{k: counts[k] for k in OUTCOMES}})
                total = sum(outcomes.values(), Counter())
                take_rows.append({"how": how, "variant": name, "class": "tất cả",
                                  **{k: total[k] for k in OUTCOMES}})
    event_metrics = ["precision", "recall", "f1", "false_per_min", "cmds_per_gesture"]
    event_sides = side_rows(event_rows, ["how"], event_metrics)
    take_sides = side_rows(take_rows, ["how", "class"], list(OUTCOMES)) if take_rows else []
    write_table(event_rows, list(event_rows[0]), run_dir / "events")
    write_table(event_sides, list(event_sides[0]), run_dir / "events_by_side")
    if take_rows:
        write_table(take_rows, list(take_rows[0]), run_dir / "takes")
        write_table(take_sides, list(take_sides[0]), run_dir / "takes_by_side")
    write_manifest(run_dir, {"script": "compare_self", "split": args.split,
                             "final": args.final, "n_clips": len(paths),
                             "variants": {n: {k: relative_to_root(v) for k, v in p.items()}
                                          for n, p in variants().items()},
                             "windows": windows, "events": event_rows, "takes": take_rows,
                             "by_side": {"windows": window_sides, "events": event_sides,
                                         "takes": take_sides}})

    print(f"Tập {args.split} — mức cửa sổ ({windows[0]['n_windows']} cửa sổ):")
    print(f"{'':<9}{'mô hình':<8}{'macro-F1':>9}" + "".join(f"{c[:11]:>12}" for c in config.CLASSES))
    for row in windows:
        print(f"{row['variant']:<9}{row['model']:<8}{row['macro_f1']:>9.4f}"
              + "".join(f"{row[c]:>12.3f}" for c in config.CLASSES))
    print("Trung bình mỗi bên [nhỏ nhất–lớn nhất]:")
    for row in window_sides:
        print(f"  {row['variant']:<5}{row['model']:<8}macro-F1 {row['macro_f1']:.4f} "
              f"[{row['macro_f1_min']:.4f}–{row['macro_f1_max']:.4f}]   "
              + "  ".join(f"{c} {row[c]:.3f}" for c in config.CLASSES[1:]))
    print(f"\nMức lệnh (mô hình ghép + máy trạng thái), {len(paths)} video:")
    for row in event_rows:
        print(f"  {row['how']:<14}{row['variant']:<9} P {row['precision']:.3f}  R {row['recall']:.3f}"
              f"  F1 {row['f1']:.3f}  lệnh nhầm/phút {row['false_per_min']:.2f}"
              f"  lệnh/cử chỉ {row['cmds_per_gesture']:.2f}")
    for row in event_sides:
        print(f"  {row['how']:<14}{row['variant']:<9} trung bình F1 {row['f1']:.3f} "
              f"[{row['f1_min']:.3f}–{row['f1_max']:.3f}], lệnh nhầm/phút "
              f"{row['false_per_min']:.2f} [{row['false_per_min_min']:.2f}–"
              f"{row['false_per_min_max']:.2f}]")
    if take_rows:
        print("\nLệnh đầu tiên của từng lần quay (đúng / nhầm / sót):")
        for row in take_rows:
            print(f"  {row['how']:<14}{row['variant']:<9}{row['class']:<12}"
                  f"{row['đúng']:>3} / {row['nhầm']:>2} / {row['sót']:>2}")
        print("Trung bình mỗi bên [nhỏ nhất–lớn nhất của số đúng]:")
        for row in take_sides:
            print(f"  {row['how']:<14}{row['variant']:<5}{row['class']:<12}đúng {row['đúng']:.1f} "
                  f"[{row['đúng_min']:.0f}–{row['đúng_max']:.0f}]  nhầm {row['nhầm']:.1f}  "
                  f"sót {row['sót']:.1f}")
    print(f"\nBảng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
