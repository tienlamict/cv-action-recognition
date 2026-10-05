"""Vẽ quỹ đạo cổ tay và đường độ xòe của một cửa sổ ngẫu nhiên mỗi lớp.

Mục cuối của Định nghĩa hoàn thành Phase 4: xem bằng mắt cửa sổ có đúng là cử
chỉ mang nhãn đó không. Lấy từ tập train, chọn với SEED (đổi bằng --seed).

Ví dụ:
    python scripts/plot_window_examples.py
    python scripts/plot_window_examples.py --seed 7
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.features import openness, pinch  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits, split_of  # noqa: E402
from src.viz import plot_window_traces  # noqa: E402


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    parser.add_argument("--seed", type=int, default=config.SEED)
    args = parser.parse_args()

    with np.load(args.windows, allow_pickle=False) as data:
        train = split_of(data["subject"], read_splits()) == "train"
        X, y = data["X"], data["y"]
        clip, t0, src = data["clip"], data["t0"], data["src_label"]

    rng = np.random.default_rng(args.seed)
    windows, titles, picked = [], [], []
    for k, cls in enumerate(config.CLASSES):
        i = int(rng.choice(np.flatnonzero(train & (y == k))))
        windows.append(X[i])
        titles.append(f"{cls} ({src[i]})\n{clip[i]} t0={t0[i]:.1f}s")
        picked.append({"class": cls, "clip": str(clip[i]),
                       "t0": float(t0[i]), "src_label": str(src[i])})

    run_dir = next_run_dir(config.PHASE4_RESULTS_DIR / "window_examples")
    out = plot_window_traces(windows, titles,
                             {"độ xòe": openness, "cái–trỏ": pinch},
                             run_dir / "windows.png")
    write_manifest(run_dir, {"script": "plot_window_examples",
                             "seed": args.seed, "picked": picked})
    for p in picked:
        print(f"{p['class']:<12} {p['clip']:<18} t0={p['t0']:6.1f}s  ({p['src_label']})")
    print(f"\n→ {relative_to_root(out)}")


if __name__ == "__main__":
    main()
