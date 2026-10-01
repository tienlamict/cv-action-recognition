"""Xuất đoạn mẫu có vẽ điểm mốc, để người dùng học cách làm cử chỉ theo IPN.

Mỗi lớp đích lấy EXAMPLES_PER_CLASS đoạn từ ngần ấy người khác nhau. Video ghi
ra **KHÔNG lật** — đúng như ảnh đưa vào mô hình — và có tên lớp cùng thời lượng
in trên khung hình.

Đây là tư liệu để viết docs/gestures.md.

Ví dụ:
    python scripts/export_examples.py
    python scripts/export_examples.py --classes zoom_in zoom_out
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.display import make_display  # noqa: E402
from src.io_data import load_clip  # noqa: E402
from src.io_video import iter_frames  # noqa: E402
from src.runlog import relative_to_root, write_manifest  # noqa: E402

TARGETS = ["swipe_left", "swipe_right", "zoom_in", "zoom_out"]


def choose(clip_paths, classes, per_class):
    """Chọn đoạn mẫu: mỗi lớp ``per_class`` đoạn, mỗi đoạn một người khác nhau."""
    chosen = {name: [] for name in classes}
    used = {name: set() for name in classes}

    for path in clip_paths:
        if all(len(v) >= per_class for v in chosen.values()):
            break
        ts, _, _, _, segments, src_labels, meta = load_clip(path)
        if meta.get("length_mismatch"):
            continue            # mốc frame của clip này còn nghi vấn
        subject = meta.get("subject", "?")
        fps = meta.get("fps") or config.CAM_FPS

        for (start, end, class_id), src_label in zip(segments, src_labels):
            name = config.CLASSES[class_id]
            if (name not in chosen or len(chosen[name]) >= per_class
                    or subject in used[name]):
                continue
            used[name].add(subject)
            chosen[name].append({
                "clip_id": meta.get("clip_id", path.stem),
                "subject": subject, "start": int(start), "end": int(end),
                "fps": float(fps), "src_label": str(src_label),
                "duration": (end - start) / fps,
            })
    return chosen


def export(sample, label, out_dir):
    """Ghi một đoạn ra .mp4 có vẽ điểm mốc; trả về đường dẫn."""
    video = config.IPN_VIDEO_DIR / f"{sample['clip_id']}{config.IPN_VIDEO_SUFFIX}"
    npz = config.LANDMARKS_DIR / "ipn" / f"{sample['clip_id']}.npz"
    _, xy_norm, _, _, _, _, _ = load_clip(npz)

    out_path = out_dir / f"{label}_{sample['subject']}.mp4"
    writer = None
    text = (f"{label}  ({sample['src_label']})  "
            f"{sample['duration']:.1f}s  {sample['subject']}")

    for index, (frame_bgr, _) in enumerate(iter_frames(video)):
        if index < sample["start"]:
            continue
        if index >= sample["end"]:
            break
        # mirror=False: bản xuất ra phải giống hệt ảnh đưa vào mô hình.
        shown = make_display(frame_bgr, xy_norm[index], [text], mirror=False)
        if writer is None:
            h, w = shown.shape[:2]
            writer = cv2.VideoWriter(str(out_path),
                                     cv2.VideoWriter_fourcc(*"mp4v"),
                                     sample["fps"], (w, h))
            if not writer.isOpened():
                raise SystemExit(f"Không mở được VideoWriter cho {out_path}")
        writer.write(shown)

    if writer is not None:
        writer.release()
    return out_path


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--classes", nargs="+", default=TARGETS,
                        choices=config.CLASSES)
    parser.add_argument("--per-class", type=int,
                        default=config.EXAMPLES_PER_CLASS)
    parser.add_argument("--landmarks", default=None)
    args = parser.parse_args()

    landmarks_dir = Path(args.landmarks or config.LANDMARKS_DIR / "ipn")
    clip_paths = sorted(landmarks_dir.glob("*.npz"))
    if not clip_paths:
        raise SystemExit(
            f"Chưa có .npz nào trong {relative_to_root(landmarks_dir)}. "
            "Chạy scripts/extract_landmarks.py --source ipn trước."
        )

    out_dir = config.PHASE3_RESULTS_DIR / "examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    chosen = choose(clip_paths, args.classes, args.per_class)

    exported = []
    for label, samples in chosen.items():
        for sample in samples:
            path = export(sample, label, out_dir)
            exported.append({"class": label, **sample,
                             "file": relative_to_root(path)})
            print(f"{label:<13} {sample['clip_id']:<22} "
                  f"frame {sample['start']}–{sample['end']}  "
                  f"{sample['duration']:.1f}s  -> {relative_to_root(path)}")
        if len(samples) < args.per_class:
            print(f"  CHÚ Ý: {label} mới có {len(samples)}/{args.per_class} "
                  "đoạn — chưa đủ clip đã trích, hoặc chưa đủ người khác nhau.")

    write_manifest(out_dir, {"script": "export_examples",
                             "exported": exported})
    print(f"\n{len(exported)} video trong {relative_to_root(out_dir)}")


if __name__ == "__main__":
    main()
