"""Thống kê bộ điểm mốc đã trích: theo lớp, theo người, theo thời lượng.

Hai con số quan trọng nhất cho các phase sau:

- **tỉ lệ frame mất tay theo lớp** — lớp nào MediaPipe hay mất dấu nhất;
- **thời lượng trung vị và phân vị 90 của từng lớp**, cùng tỉ lệ đoạn dài hơn
  WIN_SEC — cho biết nên làm cử chỉ nhanh cỡ nào, và cửa sổ 1,2 giây có bắt
  trọn một cử chỉ hay không.

Ví dụ:
    python scripts/dataset_stats.py
"""

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.io_data import load_clip  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.tables import write_table  # noqa: E402


def gather(clip_paths):
    """Duyệt mọi clip, gom số liệu theo lớp, theo người và theo nhãn gốc."""
    per_class = collections.defaultdict(
        lambda: {"n_segments": 0, "frames": 0, "missing": 0, "durations": []})
    per_subject = collections.defaultdict(
        lambda: collections.Counter())
    per_src_label = collections.Counter()
    clips = []

    for path in clip_paths:
        ts, xy_norm, w, h, segments, src_labels, meta = load_clip(path)
        present = np.all(np.isfinite(xy_norm.reshape(xy_norm.shape[0], -1)),
                         axis=1)
        fps = meta.get("fps") or config.CAM_FPS
        subject = meta.get("subject", "?")

        clips.append({
            "clip_id": meta.get("clip_id", path.stem),
            "subject": subject,
            "official_split": meta.get("official_split", ""),
            "n_frames": int(ts.size),
            "detection_rate": float(present.mean()) if ts.size else float("nan"),
            "n_segments": int(segments.shape[0]),
            "length_mismatch": bool(meta.get("length_mismatch", False)),
        })

        for (start, end, class_id), src_label in zip(segments, src_labels):
            name = config.CLASSES[class_id]
            row = per_class[name]
            row["n_segments"] += 1
            row["frames"] += int(end - start)
            row["missing"] += int(np.sum(~present[start:end]))
            row["durations"].append((end - start) / fps)
            per_subject[subject][name] += 1
            per_src_label[str(src_label)] += 1

    return clips, per_class, per_subject, per_src_label


def class_rows(per_class):
    rows = []
    for name in config.CLASSES:
        row = per_class.get(name)
        if not row:
            continue
        durations = np.array(row["durations"], dtype=np.float64)
        rows.append({
            "class": name,
            "n_segments": row["n_segments"],
            "n_frames": row["frames"],
            "missing_hand_rate": row["missing"] / max(row["frames"], 1),
            "duration_median_sec": float(np.median(durations)),
            "duration_p90_sec": float(np.percentile(durations, 90)),
            "duration_min_sec": float(durations.min()),
            "duration_max_sec": float(durations.max()),
            "frac_longer_than_win": float(np.mean(durations > config.WIN_SEC)),
        })
    return rows


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--landmarks", default=None,
                        help="thư mục .npz (mặc định data/landmarks/ipn)")
    args = parser.parse_args()

    landmarks_dir = Path(args.landmarks or config.LANDMARKS_DIR / "ipn")
    clip_paths = sorted(landmarks_dir.glob("*.npz"))
    if not clip_paths:
        raise SystemExit(
            f"Chưa có .npz nào trong {relative_to_root(landmarks_dir)}. "
            "Chạy scripts/extract_landmarks.py --source ipn trước."
        )

    clips, per_class, per_subject, per_src_label = gather(clip_paths)
    run_dir = next_run_dir(config.PHASE3_RESULTS_DIR / "dataset_stats")

    by_class = class_rows(per_class)
    write_table(by_class, ["class", "n_segments", "n_frames",
                           "missing_hand_rate", "duration_median_sec",
                           "duration_p90_sec", "duration_min_sec",
                           "duration_max_sec", "frac_longer_than_win"],
                run_dir / "by_class")

    subject_rows = [{"subject": s, "n_segments": sum(c.values()),
                     **{name: c.get(name, 0) for name in config.CLASSES}}
                    for s, c in sorted(per_subject.items())]
    write_table(subject_rows, ["subject", "n_segments", *config.CLASSES],
                run_dir / "by_subject")

    write_table(clips, ["clip_id", "subject", "official_split", "n_frames",
                        "detection_rate", "n_segments", "length_mismatch"],
                run_dir / "by_clip")

    src_rows = [{"src_label": k, "n_segments": v}
                for k, v in sorted(per_src_label.items())]
    write_table(src_rows, ["src_label", "n_segments"], run_dir / "by_src_label")

    total_frames = sum(c["n_frames"] for c in clips)
    missing = sum(c["n_frames"] * (1 - c["detection_rate"]) for c in clips)
    print(f"{len(clips)} clip, {total_frames:,} frame, "
          f"{len(per_subject)} người diễn.")
    print(f"Tỉ lệ frame mất tay toàn bộ: {missing / max(total_frames, 1):.1%}\n")

    print(f"{'lớp':<14}{'đoạn':>7}{'mất tay':>10}{'trung vị':>10}"
          f"{'p90':>8}{'> WIN_SEC':>11}")
    for row in by_class:
        print(f"{row['class']:<14}{row['n_segments']:>7}"
              f"{row['missing_hand_rate']:>10.1%}"
              f"{row['duration_median_sec']:>9.2f}s"
              f"{row['duration_p90_sec']:>7.2f}s"
              f"{row['frac_longer_than_win']:>11.1%}")

    write_manifest(run_dir, {"script": "dataset_stats", "n_clips": len(clips),
                             "n_frames": total_frames,
                             "n_subjects": len(per_subject)})
    print(f"\nBảng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
