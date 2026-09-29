"""Tính số liệu cho mọi thí nghiệm quan sát đã ghi bằng observe.py.

Quét results/phase1/e*/run_*/landmarks.csv và xuất vào
results/phase1/analysis/run_NN/:

- runs.csv / runs.md       — mỗi lần chạy một dòng
- summary.csv / summary.md — gộp theo thí nghiệm + điều kiện: trung bình, độ
                             lệch chuẩn, số lần chạy
- manifest.json

Rồi in dòng AUG_NOISE_SIGMA để dán vào config.py — sigma cho tăng cường
nhiễu Gauss ở Phase 4, đo trên thí nghiệm OBS_JITTER_EXPERIMENT (tay đứng yên
hoàn toàn). Sigma báo theo đơn vị ĐÃ CHUẨN HOÁ (cỡ lòng bàn tay), đúng đơn vị
mà normalize_window dùng; bản tính bằng pixel in kèm để đối chiếu.

Ví dụ:
    python scripts/analyze_observations.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.observations import aggregate, run_metrics  # noqa: E402
from src.recording import read_frames_csv  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.tables import write_table  # noqa: E402

_EXPERIMENT_DIR = re.compile(r"^e\d")

METRICS = [
    "n_frames", "duration_sec", "fps", "detection_rate", "n_losses",
    "longest_gap_frames", "longest_gap_sec", "mean_score",
    "jitter_index_std_px", "jitter_index_diff_px",
    "sigma_std_px", "sigma_diff_px", "palm_px", "sigma_std_palm",
]


def find_runs():
    for exp_dir in sorted(config.PHASE1_RESULTS_DIR.iterdir()):
        if not (exp_dir.is_dir() and _EXPERIMENT_DIR.match(exp_dir.name)):
            continue
        for csv_path in sorted(exp_dir.glob(f"run_*/{config.LANDMARKS_CSV_NAME}")):
            yield exp_dir.name, csv_path


def main():
    setup_console()
    make_parser(__doc__).parse_args()

    if not config.PHASE1_RESULTS_DIR.is_dir():
        print("Chưa có results/phase1/. Chạy scripts/observe.py trước.")
        return

    rows = []
    for experiment, csv_path in find_runs():
        metrics = run_metrics(read_frames_csv(csv_path))
        rows.append({"experiment": experiment, "run": csv_path.parent.name,
                     **metrics})
    if not rows:
        print("Chưa có lần chạy thí nghiệm nào. Chạy scripts/observe.py trước.")
        return

    summary = aggregate(rows, "experiment", METRICS)
    summary_columns = ["experiment", "n_runs"] + [
        f"{m}_{s}" for m in METRICS for s in ("mean", "std")
    ]

    out_dir = next_run_dir(config.PHASE1_RESULTS_DIR / "analysis")
    write_table(rows, ["experiment", "run", *METRICS], out_dir / "runs")
    write_table(summary, summary_columns, out_dir / "summary")

    print(f"{len(rows)} lần chạy, {len(summary)} nhóm thí nghiệm. "
          f"Bảng tại {relative_to_root(out_dir)}\n")
    print(f"{'thí nghiệm':28s} {'lần':>4s} {'phát hiện':>10s} {'FPS':>6s} "
          f"{'rung ngón trỏ (px)':>19s}")
    for s in summary:
        warn = (f"  <- chưa đủ {config.OBS_MIN_RUNS} lần"
                if s["n_runs"] < config.OBS_MIN_RUNS else "")
        print(f"{s['experiment']:28s} {s['n_runs']:4d} "
              f"{s['detection_rate_mean']:10.1%} {s['fps_mean']:6.1f} "
              f"{s['jitter_index_std_px_mean']:19.2f}{warn}")

    jitter = [s for s in summary if s["experiment"] == config.OBS_JITTER_EXPERIMENT]
    sigma = None
    if jitter:
        j = jitter[0]
        sigma = {"sigma_std_px": j["sigma_std_px_mean"],
                 "sigma_std_palm": j["sigma_std_palm_mean"],
                 "sigma_diff_px": j["sigma_diff_px_mean"],
                 "n_runs": j["n_runs"]}
        print(f"\nSigma độ rung điểm mốc (từ {config.OBS_JITTER_EXPERIMENT}, "
              f"{j['n_runs']} lần chạy):")
        print(f"  {j['sigma_std_px_mean']:.3f} px, tức "
              f"{j['sigma_std_palm_mean']:.4f} cỡ lòng bàn tay (điểm 0 -> 9)")
        print(f"  đối chiếu theo chênh lệch frame liền nhau: "
              f"{j['sigma_diff_px_mean']:.3f} px")
        if j["n_runs"] < config.OBS_MIN_RUNS:
            print(f"  CẢNH BÁO: mới {j['n_runs']} lần — cần ít nhất "
                  f"{config.OBS_MIN_RUNS}.")
        print("\nDán dòng sau vào src/config.py, thay cho AUG_NOISE_SIGMA = None:\n")
        print(f"AUG_NOISE_SIGMA = {j['sigma_std_palm_mean']:.4f}"
              f"    # đo ở Phase 1B, {config.OBS_JITTER_EXPERIMENT}, "
              f"{j['n_runs']} lần chạy; đơn vị cỡ lòng bàn tay")
    else:
        print(f"\nChưa có {config.OBS_JITTER_EXPERIMENT} — chưa tính được sigma.")

    write_manifest(out_dir, {"script": "analyze_observations",
                             "n_runs": len(rows), "sigma": sigma})


if __name__ == "__main__":
    main()
