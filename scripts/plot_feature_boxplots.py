"""Vẽ boxplot từng đặc trưng theo từng lớp, từ bộ cửa sổ đã dựng.

Viết ở Phase 2, **chạy** ở Phase 4 khi đã có data/windows/windows.npz. Ba hình
cần nhìn là cổng kiểm tra của Phase 4:

- open_delta: hộp zoom_in hẳn bên dương, zoom_out hẳn bên âm
- dx: hai hộp của hai lớp vuốt nằm hai phía của 0
- straightness: hộp hai lớp vuốt cao hơn hẳn hộp lớp none

Ví dụ:
    python scripts/plot_feature_boxplots.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.features import FEATURE_NAMES, window_features  # noqa: E402
from src.runlog import (next_run_dir, relative_to_root,  # noqa: E402
                        write_manifest)
from src.viz import plot_boxplots  # noqa: E402


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ,
                        help="bộ cửa sổ .npz (mặc định %(default)s)")
    args = parser.parse_args()

    path = Path(args.windows)
    if not path.is_file():
        print(f"Chưa có {relative_to_root(path)}. Bộ cửa sổ được dựng ở "
              "Phase 4 bằng scripts/build_dataset.py.")
        return

    data = np.load(path, allow_pickle=False)
    X, y, presence = data["X"], data["y"], data["presence"]
    F = np.stack([window_features(win, ratio)
                  for win, ratio in zip(X, presence)])

    out_dir = next_run_dir(config.RESULTS_DIR / "phase4" / "boxplots")
    out_path = plot_boxplots(F, y, FEATURE_NAMES, out_dir / "features.png")
    write_manifest(out_dir, {"script": "plot_feature_boxplots",
                             "windows": relative_to_root(path),
                             "n_windows": int(X.shape[0])})
    print(f"{X.shape[0]} cửa sổ → {relative_to_root(out_path)}")


if __name__ == "__main__":
    main()
