"""Dựng data/windows/windows.npz từ điểm mốc IPN đã trích.

    load_sequence → cut_windows → normalize_window → chia tập theo người
    → lấy mẫu con lớp none (CHỈ tập train)

- Bỏ clip có length_mismatch (docs/ipn_format.md mục 6).
- Nhãn neo vào khoảnh khắc chính của cử chỉ; cửa sổ giao cử chỉ đích mà không
  chứa khoảnh khắc đó bị bỏ, không gán none (src/windows.py).
- Cửa sổ normalize_window từ chối (lòng bàn tay frame đầu bất thường) bị bỏ.
- Tập của mỗi cửa sổ suy từ cột subject và data/splits.json — chạy
  scripts/make_splits.py trước.
- Lớp none của tập train lấy mẫu con xuống NONE_TRAIN_SHARE, quota CHIA ĐỀU theo
  nhãn gốc: nhóm nhỏ hơn phần chia thì giữ hết, phần dư chia cho nhóm còn lại.
  Val và test giữ nguyên phân bố tự nhiên.
- Không tăng cường ở đây: tăng cường tạo mới mỗi epoch, chỉ trên train (Phase
  6–7, qua src/augment.py).

Ví dụ:
    python scripts/build_dataset.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import (equal_quota, read_splits, split_of,  # noqa: E402,F401
                        subsample_none)
from src.tables import write_table  # noqa: E402
from src.windows import FIELDS  # noqa: E402
from src.windows import collect_windows as collect  # noqa: E402

# collect, equal_quota, subsample_none nằm trong src/ từ Phase 8: các bảng khảo
# sát dựng bộ cửa sổ bằng đúng các hàm này (luật 1).


def count_rows(y, split, keep):
    """Bảng số cửa sổ theo tập × lớp, trước và sau lấy mẫu con."""
    rows = []
    for name in ("train", "val", "test"):
        in_split = split == name
        for k, cls in enumerate(config.CLASSES):
            before = int(np.sum(in_split & (y == k)))
            after = int(np.sum(in_split & (y == k) & keep))
            rows.append({"split": name, "class": cls, "before": before,
                         "after": after})
        total_after = int(np.sum(in_split & keep))
        none_after = int(np.sum(in_split & keep & (y == 0)))
        rows.append({"split": name, "class": "TỔNG",
                     "before": int(in_split.sum()), "after": total_after,
                     "none_share_after": none_after / max(total_after, 1)})
    return rows


def save_windows(path, windows):
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **{k: windows[k] for k in FIELDS})
    return path


def load_seconds(path):
    """Thời gian nạp TOÀN BỘ windows.npz vào bộ nhớ."""
    started = time.perf_counter()
    with np.load(path, allow_pickle=False) as data:
        for k in data.files:
            _ = data[k]
    return time.perf_counter() - started


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--landmarks", default=None,
                        help="thư mục .npz (mặc định data/landmarks/ipn)")
    parser.add_argument("--out", default=config.WINDOWS_NPZ,
                        help="file ra (mặc định %(default)s)")
    args = parser.parse_args()

    splits = read_splits()
    landmarks_dir = Path(args.landmarks or config.LANDMARKS_DIR / "ipn")
    clip_paths = sorted(landmarks_dir.glob("*.npz"))
    if not clip_paths:
        raise SystemExit(f"Chưa có .npz nào trong {relative_to_root(landmarks_dir)}.")

    windows, info = collect(clip_paths)
    split = split_of(windows["subject"], splits)
    unassigned = sorted(set(windows["subject"][split == ""]))
    if unassigned:
        raise SystemExit(f"Người không thuộc tập nào trong splits.json: {unassigned}")

    rng = np.random.default_rng(config.SEED)
    keep, quota = subsample_none(windows["y"], windows["src_label"], split, rng)

    run_dir = next_run_dir(config.PHASE4_RESULTS_DIR / "build_dataset")
    counts = count_rows(windows["y"], split, keep)
    write_table(counts, ["split", "class", "before", "after", "none_share_after"],
                run_dir / "windows_by_split_class")

    train_none = (split == "train") & (windows["y"] == 0)
    src_rows = [{"src_label": k,
                 "before": int(np.sum(train_none & (windows["src_label"] == k))),
                 "after": quota[k]} for k in sorted(quota)]
    write_table(src_rows, ["src_label", "before", "after"],
                run_dir / "train_none_by_src_label")

    out_path = save_windows(Path(args.out), {k: v[keep] for k, v in windows.items()})
    seconds = load_seconds(out_path)

    for row in counts:
        if row["class"] == "TỔNG":
            print(f"{row['split']:<6} {row['before']:>7} → {row['after']:>6} cửa sổ, "
                  f"none chiếm {row['none_share_after']:.1%}")
    train_rows = [r for r in counts if r["split"] == "train" and r["class"] != "TỔNG"]
    n_train = sum(r["after"] for r in train_rows)
    dist = ", ".join(f"{r['class']} {r['after']} ({r['after'] / n_train:.1%})"
                     for r in train_rows)
    print(f"\nSau khi cắt cửa sổ và lấy mẫu con lớp nền, tập huấn luyện có "
          f"{n_train} mẫu với phân bố lớp như sau: {dist}.")
    print(f"\n{info['n_clips']} clip dùng, {len(info['mismatched'])} clip bỏ vì "
          f"length_mismatch. Cửa sổ bị bỏ: {info['low_presence']} vì thiếu tay, "
          f"{info['ambiguous']} vì mơ hồ (giao cử chỉ đích, không chứa khoảnh "
          f"khắc chính), {info['n_unnormalizable']} vì không chuẩn hoá được.")
    print(f"windows.npz: X {windows['X'][keep].shape}, nạp toàn bộ trong "
          f"{seconds:.2f} s → {relative_to_root(out_path)}")

    write_manifest(run_dir, {
        "script": "build_dataset", "out": relative_to_root(out_path),
        "n_clips": info["n_clips"], "mismatched": info["mismatched"],
        "n_unnormalizable": info["n_unnormalizable"],
        "low_presence": info["low_presence"], "ambiguous": info["ambiguous"],
        "n_windows_saved": int(keep.sum()), "load_seconds": seconds,
        "train_none_quota": quota})
    print(f"Bảng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
