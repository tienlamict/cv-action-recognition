"""Tóm tắt log của demo.py: đếm "cụm" nhãn và số cụm mỗi phút.

Một cụm là một chuỗi dự đoán LIỀN NHAU cùng nhãn. Chưa có máy trạng thái (Phase
9), nên số cụm khác none là cách xấp xỉ số lần hệ thống SẼ phát lệnh — dùng cho
lần thử trực tiếp ở Phase 6 (làm việc bình thường 5 phút) và bài đếm báo nhầm
ở Phase 5.

Ví dụ:
    python scripts/demo.py --model rf --log results/phase6/live_rf.csv
    python scripts/summarize_log.py results/phase6/live_rf.csv
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.live import NO_LABEL, count_clusters, read_prediction_log  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.tables import write_table  # noqa: E402


def summarize_log(ts, names):
    """Số cụm từng lớp đích và số cụm mỗi phút.

    Returns:
        ``(rows, totals)`` — ``rows`` mỗi lớp một dict; ``totals`` gồm thời
        lượng, số dự đoán, số dự đoán có cửa sổ hợp lệ, tổng số cụm.
    """
    minutes = max(ts[-1] - ts[0], config.STRIDE_SEC) / 60.0 if ts else 0.0
    clusters = count_clusters(names)
    rows = [{"label": name, "clusters": n,
             "per_minute": n / minutes if minutes else 0.0}
            for name, n in clusters.items()]
    total = sum(clusters.values())
    totals = {"minutes": minutes, "n_predictions": len(names),
              "n_valid": sum(name != NO_LABEL for name in names),
              "clusters": total, "per_minute": total / minutes if minutes else 0.0}
    return rows, totals


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("log", help="file CSV do demo.py --log ghi")
    args = parser.parse_args()

    ts, names = read_prediction_log(args.log)
    rows, totals = summarize_log(ts, names)

    run_dir = next_run_dir(config.PHASE6_RESULTS_DIR / "summarize_log")
    write_table(rows + [{"label": "TỔNG (khác none)", "clusters": totals["clusters"],
                         "per_minute": totals["per_minute"]}],
                ["label", "clusters", "per_minute"], run_dir / "clusters")
    write_manifest(run_dir, {"script": "summarize_log",
                             "log": relative_to_root(args.log), **totals})

    print(f"{relative_to_root(args.log)}: {totals['minutes']:.1f} phút, "
          f"{totals['n_predictions']} dự đoán, {totals['n_valid']} có cửa sổ hợp lệ\n")
    print(f"{'nhãn':<14}{'số cụm':>8}{'cụm/phút':>10}")
    for r in rows:
        print(f"{r['label']:<14}{r['clusters']:>8}{r['per_minute']:>10.2f}")
    print(f"{'tổng khác none':<14}{totals['clusters']:>8}{totals['per_minute']:>10.2f}")
    print(f"\nBảng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
