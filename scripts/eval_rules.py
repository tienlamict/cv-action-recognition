"""Đánh giá mô hình luật ở mức cửa sổ, mặc định trên tập val.

Ma trận nhầm lẫn, precision/recall/F1 từng lớp, macro-F1, và hai đường cơ sở:
đoán ngẫu nhiên đều 5 lớp (20% mỗi lớp, seed SEED) và luôn đoán none. Hợp lệ
vì ba ngưỡng chọn trên train. Ghi một hàng vào bảng so sánh mô hình
results/model_comparison.{csv,md}.

test và real_test chỉ chạy ĐÚNG MỘT LẦN ở cuối dự án (luật 13): phải thêm
--final mới chạy được.

Ví dụ:
    python scripts/eval_rules.py
    python scripts/eval_rules.py --split test --final
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
from sklearn.metrics import (confusion_matrix, f1_score,  # noqa: E402
                             precision_recall_fscore_support)

from src import config, rules  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.features import window_features  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import SPLIT_NAMES, read_splits, split_of  # noqa: E402
from src.tables import write_table  # noqa: E402

LABELS = list(range(len(config.CLASSES)))
COMPARISON_COLUMNS = ["model", "split", "n_windows", "macro_f1",
                      "baseline_random", "baseline_none", "run"]


def macro_f1(y_true, y_pred):
    return float(f1_score(y_true, y_pred, labels=LABELS, average="macro",
                          zero_division=0))


def baselines(y_true, seed=config.SEED):
    """Macro-F1 của hai đường cơ sở: ngẫu nhiên đều 5 lớp, và luôn none."""
    rng = np.random.default_rng(seed)
    random_pred = rng.integers(0, len(LABELS), size=y_true.size)
    return (macro_f1(y_true, random_pred),
            macro_f1(y_true, np.zeros_like(y_true)))


def upsert_comparison(row, stem=config.MODEL_COMPARISON):
    """Thêm hoặc thay hàng ``(model, split)`` trong bảng so sánh mô hình."""
    csv_path = Path(stem).with_suffix(".csv")
    rows = []
    if csv_path.is_file():
        with open(csv_path, newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f)
                    if (r["model"], r["split"]) != (row["model"], row["split"])]
    rows.append(row)
    write_table(rows, COMPARISON_COLUMNS, stem)
    return csv_path


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    parser.add_argument("--split", default="val", choices=SPLIT_NAMES)
    parser.add_argument("--final", action="store_true",
                        help="bắt buộc với test/real_test — chỉ chạy một lần, ở cuối")
    args = parser.parse_args()
    if args.split in ("test", "real_test") and not args.final:
        raise SystemExit(f"Tập {args.split} chỉ chạy đúng một lần ở cuối dự án "
                         "(luật 13). Thêm --final nếu đúng là lúc đó.")

    with np.load(args.windows, allow_pickle=False) as data:
        pick = split_of(data["subject"], read_splits()) == args.split
        X, y, presence = data["X"][pick], data["y"][pick], data["presence"][pick]
    if y.size == 0:
        raise SystemExit(f"Tập {args.split} không có cửa sổ nào.")

    pred = np.array([rules.classify(window_features(win, ratio))[0]
                     for win, ratio in zip(X, presence)])
    score = macro_f1(y, pred)
    random_f1, none_f1 = baselines(y)

    run_dir = next_run_dir(config.PHASE5_RESULTS_DIR / "eval_rules")
    cm = confusion_matrix(y, pred, labels=LABELS)
    write_table([{"true \\ pred": config.CLASSES[i],
                  **{config.CLASSES[j]: int(cm[i, j]) for j in LABELS}}
                 for i in LABELS],
                ["true \\ pred", *config.CLASSES], run_dir / "confusion")
    p, r, f, n = precision_recall_fscore_support(y, pred, labels=LABELS,
                                                 zero_division=0)
    per_class = [{"class": c, "precision": float(p[i]), "recall": float(r[i]),
                  "f1": float(f[i]), "support": int(n[i])}
                 for i, c in enumerate(config.CLASSES)]
    write_table(per_class, ["class", "precision", "recall", "f1", "support"],
                run_dir / "per_class")
    row = {"model": "rules", "split": args.split, "n_windows": int(y.size),
           "macro_f1": score, "baseline_random": random_f1,
           "baseline_none": none_f1, "run": relative_to_root(run_dir)}
    table = upsert_comparison(row)
    write_manifest(run_dir, {"script": "eval_rules", **row,
                             "thresholds": {k: getattr(config, k) for k in
                                            ("RULE_VX_HI", "RULE_DX_HI", "RULE_P_HI")}})

    print(f"Tập {args.split}: {y.size} cửa sổ\n")
    print("Ma trận nhầm lẫn (hàng = thật, cột = đoán):")
    print(" " * 13 + "".join(f"{c[:11]:>12}" for c in config.CLASSES))
    for i, c in enumerate(config.CLASSES):
        print(f"{c:<13}" + "".join(f"{v:>12}" for v in cm[i]))
    print()
    for row_ in per_class:
        print(f"{row_['class']:<13} P {row_['precision']:.3f}  R {row_['recall']:.3f}"
              f"  F1 {row_['f1']:.3f}  (n={row_['support']})")
    print(f"\nmacro-F1 luật          {score:.4f}")
    print(f"macro-F1 ngẫu nhiên    {random_f1:.4f}")
    print(f"macro-F1 luôn none     {none_f1:.4f}")
    verdict = "CAO HƠN" if score > max(random_f1, none_f1) else "KHÔNG cao hơn"
    print(f"→ luật {verdict} cả hai đường cơ sở")
    print(f"\nBảng: {relative_to_root(run_dir)}; so sánh mô hình: "
          f"{relative_to_root(table)}")


if __name__ == "__main__":
    main()
