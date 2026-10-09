"""Đánh giá mô hình luật ở mức cửa sổ, mặc định trên tập val.

Ma trận nhầm lẫn, precision/recall/F1 từng lớp, macro-F1, và hai đường cơ sở:
đoán ngẫu nhiên đều 5 lớp (20% mỗi lớp, seed SEED) và luôn đoán none. Hợp lệ
vì ba ngưỡng chọn trên train. Ghi một hàng vào bảng so sánh mô hình
results/model_comparison.{csv,md}.

test và real_test chỉ chạy ĐÚNG MỘT LẦN ở cuối dự án (luật 13): phải thêm
--final, và lần chạy được ghi vào results/TEST_USED.log.

Ví dụ:
    python scripts/eval_rules.py
    python scripts/eval_rules.py --split test --final
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config, rules  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.evaluation import (baselines, guard_split, split_features,  # noqa: E402
                            summarize, upsert_comparison, write_summary)
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import SPLIT_NAMES, read_splits  # noqa: E402

THRESHOLDS = ("RULE_VX_HI", "RULE_DX_HI", "RULE_P_HI")


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    parser.add_argument("--split", default="val", choices=SPLIT_NAMES)
    parser.add_argument("--final", action="store_true",
                        help="bắt buộc với test/real_test — chỉ chạy một lần, ở cuối")
    args = parser.parse_args()
    guard_split(args.split, args.final, "rules",
                {k: getattr(config, k) for k in THRESHOLDS})

    with np.load(args.windows, allow_pickle=False) as data:
        F, y, _ = split_features(data["X"], data["y"], data["presence"],
                                 data["subject"], read_splits(), args.split)
    if y.size == 0:
        raise SystemExit(f"Tập {args.split} không có cửa sổ nào.")

    pred = np.array([rules.classify(f)[0] for f in F])
    summary = summarize(y, pred)
    random_f1, none_f1 = baselines(y)

    run_dir = next_run_dir(config.PHASE5_RESULTS_DIR / "eval_rules")
    write_summary(summary, run_dir)
    row = {"model": "rules", "split": args.split, "n_windows": int(y.size),
           "macro_f1": summary["macro_f1"], "baseline_random": random_f1,
           "baseline_none": none_f1, "run": relative_to_root(run_dir)}
    table = upsert_comparison(row)
    write_manifest(run_dir, {"script": "eval_rules", **row,
                             "thresholds": {k: getattr(config, k) for k in THRESHOLDS}})

    print(f"Tập {args.split}: {y.size} cửa sổ\n")
    print("Ma trận nhầm lẫn (hàng = thật, cột = đoán):")
    print(" " * 13 + "".join(f"{c[:11]:>12}" for c in config.CLASSES))
    for i, c in enumerate(config.CLASSES):
        print(f"{c:<13}" + "".join(f"{v:>12}" for v in summary["confusion"][i]))
    print()
    print(summary["report"])
    print(f"macro-F1 luật          {summary['macro_f1']:.4f}")
    print(f"macro-F1 ngẫu nhiên    {random_f1:.4f}")
    print(f"macro-F1 luôn none     {none_f1:.4f}")
    verdict = "CAO HƠN" if summary["macro_f1"] > max(random_f1, none_f1) else "KHÔNG cao hơn"
    print(f"→ luật {verdict} cả hai đường cơ sở")
    print(f"\nBảng: {relative_to_root(run_dir)}; so sánh mô hình: "
          f"{relative_to_root(table)}")


if __name__ == "__main__":
    main()
