"""Đánh giá một mô hình đã có ở mức cửa sổ, trên một tập bất kỳ.

Mặc định là tập val. Tập test và real_test chỉ chạy ĐÚNG MỘT LẦN ở cuối dự án
(luật 13): script từ chối chạy nếu thiếu --final, và khi chạy thì ghi một dòng
vào results/TEST_USED.log — tên tập, thời điểm, mô hình, dòng lệnh, hằng số —
TRƯỚC khi đọc dữ liệu của tập đó.

Phase 8 sẽ mở rộng script này sang đánh giá mức sự kiện.

Ví dụ:
    python scripts/evaluate.py --model rf
    python scripts/evaluate.py --model rules --split val
    python scripts/evaluate.py --model lstm --split val
    python scripts/evaluate.py --model rf --split test --final
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.evaluation import (baselines, guard_split, predict_windows,  # noqa: E402
                            split_features, summarize, upsert_comparison,
                            write_summary)
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import SPLIT_NAMES, read_splits  # noqa: E402
from src.viz import plot_confusion  # noqa: E402


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--model", required=True, choices=config.MODEL_NAMES)
    parser.add_argument("--split", default="val", choices=SPLIT_NAMES)
    parser.add_argument("--final", action="store_true",
                        help="bắt buộc với test/real_test — chỉ chạy một lần, ở cuối")
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    args = parser.parse_args()

    # Chốt luật 13 trước mọi thứ khác, kể cả trước khi nạp mô hình.
    guard_split(args.split, args.final, args.model)

    with np.load(args.windows, allow_pickle=False) as data:
        F, y, pick = split_features(data["X"], data["y"], data["presence"],
                                    data["subject"], read_splits(), args.split)
        X = data["X"][pick]
    if y.size == 0:
        raise SystemExit(f"Tập {args.split} không có cửa sổ nào.")

    pred, details = predict_windows(args.model, F, X)
    summary = summarize(y, pred)
    random_f1, none_f1 = baselines(y)

    run_dir = next_run_dir(config.PHASE6_RESULTS_DIR / "evaluate")
    write_summary(summary, run_dir)
    plot_confusion(summary["confusion"], summary["confusion_row"], config.CLASSES,
                   run_dir / "confusion.png",
                   title=f"{args.model} — tập {args.split} ({y.size} cửa sổ)")
    row = {"model": args.model, "split": args.split, "n_windows": int(y.size),
           "macro_f1": summary["macro_f1"], "baseline_random": random_f1,
           "baseline_none": none_f1, "run": relative_to_root(run_dir)}
    table = upsert_comparison(row)
    write_manifest(run_dir, {"script": "evaluate", **row, "model_details": details})

    print(f"{args.model} trên tập {args.split}: {y.size} cửa sổ\n")
    print(summary["report"])
    print(f"macro-F1 {summary['macro_f1']:.4f}   (ngẫu nhiên {random_f1:.4f}, "
          f"luôn none {none_f1:.4f})")
    print(f"\nBảng: {relative_to_root(run_dir)}; so sánh mô hình: "
          f"{relative_to_root(table)}")


if __name__ == "__main__":
    main()
