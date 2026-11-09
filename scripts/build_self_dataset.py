"""Dựng bộ cửa sổ của dữ liệu tự quay (Phase 11) từ data/landmarks/self/.

    load_sequence → cut_windows → normalize_window      (đúng collect_windows của IPN)
    → [chỉ real_tune] bỏ đoạn học không dạy đúng cử chỉ (selfdata.window_ok)

- Mọi người–buổi của --split trong splits.json. Cột subject là mã người–buổi
  (p01/2026-11-06), cột clip là buổi/tên lần quay.
- real_tune: cửa sổ dương phải đi đúng chiều, đủ rõ, không kéo về
  (results/phase11/qa_p02.md). Cửa sổ none giữ hết; không lấy mẫu con.
- real_test: KHÔNG lọc gì, tập chấm giữ nguyên như quay. Cần --final (luật 13).
- Ra config.SELF_WINDOWS[split], tách khỏi windows.npz của IPN.

Ví dụ:
    python scripts/build_self_dataset.py
    python scripts/build_self_dataset.py --split real_test --final      # lần chấm cuối
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config, selfdata  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits  # noqa: E402
from src.tables import write_table  # noqa: E402
from src.windows import FIELDS, collect_windows  # noqa: E402


def self_clip_paths(keys, landmarks_dir=None):
    """File điểm mốc của các người–buổi ``keys``.

    Raises:
        SystemExit: một người–buổi chưa trích (chạy extract_landmarks.py --source self).
    """
    landmarks_dir = Path(landmarks_dir or config.SELF_LANDMARKS_DIR)
    paths = []
    for key in keys:
        person, session = key.split("/")
        found = sorted((landmarks_dir / session).glob(f"{person}_*.npz"))
        if not found:
            raise SystemExit(f"Chưa có điểm mốc của {key} — chạy "
                             "scripts/extract_landmarks.py --source self trước.")
        paths += found
    return paths


def filter_positives(windows):
    """Mặt nạ giữ: mọi cửa sổ none, và cửa sổ dương đạt ``selfdata.window_ok``."""
    keep = np.ones(windows["y"].size, dtype=bool)
    for i, (label, win) in enumerate(zip(windows["y"], windows["X"])):
        if label != 0:
            keep[i] = selfdata.window_ok(config.CLASSES[label], win)
    return keep


def count_rows(windows, keep):
    """Số cửa sổ mỗi người × lớp, trước và sau khi lọc."""
    person = np.array([s.split("/")[0] for s in windows["subject"]])
    rows = []
    for who in sorted(set(person)):
        for k, cls in enumerate(config.CLASSES):
            pick = (person == who) & (windows["y"] == k)
            rows.append({"person": who, "class": cls, "before": int(pick.sum()),
                         "after": int((pick & keep).sum())})
    return rows


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--split", choices=("real_tune", "real_test"), default="real_tune")
    parser.add_argument("--final", action="store_true",
                        help="bắt buộc với real_test: buổi chấm chỉ mở ở lần cuối")
    args = parser.parse_args()
    if args.split == "real_test" and not args.final:
        raise SystemExit("real_test chỉ được mở ở lần chạy cuối (luật 13) — thêm --final "
                         "nếu đúng là lúc đó.")

    keys = read_splits().get(args.split) or []
    if not keys:
        raise SystemExit(f"{args.split} trong {config.SPLITS_JSON.name} còn trống.")
    windows, info = collect_windows(self_clip_paths(keys))
    keep = (filter_positives(windows) if args.split == "real_tune"
            else np.ones(windows["y"].size, dtype=bool))

    out = Path(config.SELF_WINDOWS[args.split])
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, **{k: windows[k][keep] for k in FIELDS})

    rows = count_rows(windows, keep)
    run_dir = next_run_dir(config.PHASE11_RESULTS_DIR / "build_self_dataset")
    write_table(rows, ["person", "class", "before", "after"], run_dir / "windows_by_person_class")
    totals = Counter()
    for row in rows:
        totals[(row["class"], "before")] += row["before"]
        totals[(row["class"], "after")] += row["after"]
    write_manifest(run_dir, {
        "script": "build_self_dataset", "split": args.split, "keys": keys,
        "out": relative_to_root(out), "n_clips": info["n_clips"],
        "low_presence": info["low_presence"], "ambiguous": info["ambiguous"],
        "n_unnormalizable": info["n_unnormalizable"],
        "n_windows_saved": int(keep.sum()), "filtered": args.split == "real_tune",
        "min_net": config.SELF_MIN_NET, "max_back": config.SELF_MAX_BACK})

    print(f"{args.split}: {info['n_clips']} lần quay của {len(keys)} người–buổi.")
    print(f"{'lớp':<12}{'trước lọc':>10}{'sau lọc':>9}")
    for cls in config.CLASSES:
        print(f"{cls:<12}{totals[(cls, 'before')]:>10}{totals[(cls, 'after')]:>9}")
    print(f"Cửa sổ bị bỏ khi cắt: {info['low_presence']} vì thiếu tay, {info['ambiguous']} "
          f"vì mơ hồ, {info['n_unnormalizable']} vì không chuẩn hoá được.")
    print(f"→ {relative_to_root(out)}; bảng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
