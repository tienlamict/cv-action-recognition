"""Hiệu chuẩn ba ngưỡng của rules.py trên tập TRAIN của IPN.

Ngưỡng = trung điểm của phân vị CALIB_NONE_PCT nhóm phải nằm dưới và phân vị
CALIB_TARGET_PCT nhóm phải nằm trên (xem src/calibration.py). Hai phân vị chồng
nhau thì vẫn đề xuất trung điểm nhưng in cảnh báo.

Ghi bảng phân vị và lý do vào results/phase5/thresholds.md. In ra đúng ba dòng
để dán vào config.py — KHÔNG tự sửa config.py.

Ví dụ:
    python scripts/calibrate_rules.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.calibration import propose, train_features  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.features import FEATURE_NAMES  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits  # noqa: E402
from src.tables import write_table  # noqa: E402

PCTS = (10, 25, 50, 75, 90)


def percentile_rows(F, y):
    """Phân vị của ba đặc trưng luật dùng, theo lớp — bối cảnh cho từng ngưỡng."""
    rows = []
    for name, transform in (("max_vx", lambda v: v), ("dx", np.abs),
                            ("pinch_delta", np.abs)):
        column = transform(F[:, FEATURE_NAMES.index(name)])
        label = name if name == "max_vx" else f"|{name}|"
        for k, cls in enumerate(config.CLASSES):
            values = np.percentile(column[y == k], PCTS)
            rows.append({"feature": label, "class": cls, "n": int(np.sum(y == k)),
                         **{f"p{p}": float(v) for p, v in zip(PCTS, values)}})
    return rows


def render(proposals, pct_rows, n_train):
    lines = ["# Ngưỡng của mô hình luật", "",
             f"Hiệu chuẩn trên **tập train** của IPN ({n_train} cửa sổ, "
             "`data/windows/windows.npz`) bằng `scripts/calibrate_rules.py`. "
             "Không dùng val hay test.", "",
             "| Ngưỡng | Giá trị | Lý do |", "|---|---|---|"]
    for r in proposals:
        warn = " — ⚠ hai phân vị chồng nhau" if r["overlap"] else ""
        lines.append(f"| `{r['threshold']}` | {r['value']:.4f} | {r['reason']}{warn} |")
    lines += ["", "## Phân vị theo lớp", "",
              "| Đặc trưng | Lớp | n | " + " | ".join(f"p{p}" for p in PCTS) + " |",
              "|---|---|---|" + "---|" * len(PCTS)]
    for r in pct_rows:
        lines.append(f"| {r['feature']} | {r['class']} | {r['n']} | "
                     + " | ".join(f"{r[f'p{p}']:.3f}" for p in PCTS) + " |")
    overlaps = [r for r in proposals if r["overlap"]]
    if overlaps:
        lines += ["", "## Cảnh báo", ""]
        for r in overlaps:
            lines.append(
                f"- `{r['threshold']}`: phân vị {config.CALIB_NONE_PCT} của nhóm "
                f"dưới ({r['below_pct']:.3f}) lớn hơn phân vị "
                f"{config.CALIB_TARGET_PCT} của nhóm trên ({r['above_pct']:.3f}). "
                "Một ngưỡng không tách sạch hai nhóm; sai ở cả hai phía là "
                "không tránh được với luật.")
    return "\n".join(lines) + "\n"


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    args = parser.parse_args()

    with np.load(args.windows, allow_pickle=False) as data:
        F, y = train_features(data["X"], data["y"], data["presence"],
                              data["subject"], read_splits())
    proposals = propose(F, y)
    pct_rows = percentile_rows(F, y)

    run_dir = next_run_dir(config.PHASE5_RESULTS_DIR / "calibrate")
    write_table(proposals, ["threshold", "value", "below_pct", "above_pct",
                            "overlap", "reason"], run_dir / "thresholds")
    write_table(pct_rows, ["feature", "class", "n", *[f"p{p}" for p in PCTS]],
                run_dir / "percentiles")
    report = render(proposals, pct_rows, int(y.size))
    (config.PHASE5_RESULTS_DIR / "thresholds.md").write_text(report, encoding="utf-8")
    write_manifest(run_dir, {"script": "calibrate_rules", "n_train": int(y.size),
                             "proposals": proposals})

    print(report)
    print("Dán ba dòng sau vào src/config.py, thay cho ba dòng RULE_* = None:\n")
    for r in proposals:
        print(f"{r['threshold']} = {r['value']:.4g}")
    print(f"\nBằng chứng: {relative_to_root(run_dir)}, "
          f"{relative_to_root(config.PHASE5_RESULTS_DIR / 'thresholds.md')}")


if __name__ == "__main__":
    main()
