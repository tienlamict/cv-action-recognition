"""Trích 21 điểm mốc cho mọi video của một nguồn, lưu .npz theo schema.

Đây là bước tốn thời gian nhất của cả project — thiết kế để chạy qua đêm:

- đọc TUẦN TỰ qua iter_frames, không nhảy frame;
- mỗi video một HandTracker MỚI, vì chế độ VIDEO giữ trạng thái bám theo và
  đòi mốc thời gian tăng dần trong phạm vi một video;
- bỏ qua clip đã có .npz, nên chạy lại là tiếp tục chứ không làm lại từ đầu;
- clip lỗi ghi vào results/phase3/failed.txt rồi chạy tiếp.

Hai nguồn đi qua CÙNG vòng theo dõi tay (track_video, luật 1):

- ``ipn``: mốc thời gian lấy từ vị trí frame trong file video;
- ``self`` (Phase 11): mốc thời gian THẬT của từng frame, từ file .json đi kèm video
  (FPS webcam không cố định). Đoạn gán nhãn là ``selfdata.clip_segments``. Chỉ trích
  các người–buổi của ``--split`` trong splits.json; ``real_test`` cần thêm --final, vì
  buổi chấm chỉ được mở ở lần chạy cuối (luật 13). Ra data/landmarks/self/<buổi>/.

Ví dụ:
    python scripts/extract_landmarks.py --source ipn --limit 3
    python scripts/extract_landmarks.py --source ipn --workers 4
    python scripts/extract_landmarks.py --source ipn --estimate-only
    python scripts/extract_landmarks.py --source self                # real_tune
"""

import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402

from src import config, ipn, selfdata  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.hands import HandTracker, seconds_to_ms  # noqa: E402
from src.io_data import save_clip  # noqa: E402
from src.io_video import iter_frames  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits  # noqa: E402


def self_tasks(split):
    """Việc trích của dữ liệu tự quay: mọi video của các người–buổi trong ``split``."""
    keys = read_splits().get(split) or []
    if not keys:
        raise SystemExit(f"{split} trong {config.SPLITS_JSON.name} còn trống — chạy "
                         "scripts/split_self.py trước.")
    found = selfdata.sessions()
    tasks = []
    for key in keys:
        person, session = key.split("/")
        for video in found.get(key, []):
            tasks.append({
                "clip_id": f"{session}/{video.stem}",
                "video": str(video),
                "out": str(config.SELF_LANDMARKS_DIR / session / f"{video.stem}.npz"),
                "expected_frames": None,
                "split": split,
                "self": {"key": key, "person": person, "session": session,
                         "label": selfdata.parse_name(video).label},
            })
    return tasks


def build_tasks(source, split="real_tune"):
    """Danh sách việc cần làm: mỗi video một dict, kèm nhãn và thông tin nguồn.

    Args:
        split: chỉ với ``self`` — người–buổi của tập nào trong splits.json.
    """
    if source == "self":
        return self_tasks(split)
    out_dir = config.LANDMARKS_DIR / source
    out_dir.mkdir(parents=True, exist_ok=True)

    if source == "ipn":
        videos = sorted(config.IPN_VIDEO_DIR.glob(f"*{config.IPN_VIDEO_SUFFIX}"))
        if not videos:
            raise SystemExit(
                f"Không có video nào trong {relative_to_root(config.IPN_VIDEO_DIR)}. "
                "Tải và giải nén IPN Hand trước — xem README."
            )
        annotations = ipn.read_annotations()
        splits = ipn.read_video_lists()
        metadata = ipn.read_metadata()
        tasks = []
        for path in videos:
            clip_id = path.stem
            meta_row = metadata.get(clip_id)
            tasks.append({
                "clip_id": clip_id,
                "video": str(path),
                "out": str(out_dir / f"{clip_id}.npz"),
                "segments": annotations.get(clip_id, []),
                "expected_frames": (int(meta_row["Frames"]) if meta_row
                                    else None),
                "split": splits.get(clip_id),
            })
        return tasks
    raise SystemExit(f"Nguồn lạ '{source}'")


def pending(tasks):
    """Bỏ những clip đã có ``.npz`` — chạy lại là tiếp tục, không làm lại."""
    return [t for t in tasks if not Path(t["out"]).is_file()]


def track_video(video, ts=None):
    """Theo dõi tay trên MỘT video bằng một ``HandTracker`` mới — vòng lặp chung của
    mọi nguồn (luật 1).

    Args:
        ts: mốc thời gian thật của từng frame (dữ liệu tự quay). ``None``: mốc của
            ``iter_frames`` (video IPN).

    Returns:
        ``(ts_list, xy_list, present_list, (w, h))``.

    Raises:
        ValueError: không đọc được frame nào, hoặc số frame khác số mốc thời gian.
    """
    ts_list, xy_list, present_list, size = [], [], [], None
    stamps = None if ts is None else iter(ts)
    with HandTracker() as tracker:
        for frame_bgr, frame_ts in iter_frames(video):
            if stamps is not None:
                frame_ts = next(stamps, None)
                if frame_ts is None:
                    raise ValueError("video có nhiều frame hơn file mốc thời gian")
            if size is None:
                h, w = frame_bgr.shape[:2]
                size = (w, h)
            xy, present, _ = tracker.process(frame_bgr, seconds_to_ms(frame_ts))
            ts_list.append(frame_ts)
            xy_list.append(xy)
            present_list.append(present)
    if not ts_list:
        raise ValueError("không đọc được frame nào")
    if ts is not None and len(ts_list) != len(ts):
        raise ValueError(f"video {len(ts_list)} frame, file mốc thời gian {len(ts)}")
    return ts_list, xy_list, present_list, size


def extract_ipn(task):
    """Một video IPN: nhãn từ file chú thích của IPN."""
    ts_list, xy_list, present_list, size = track_video(task["video"])
    cap = cv2.VideoCapture(task["video"])
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    # Nhãn IPN đếm frame theo cách khác nhau tuỳ video: đo, rồi đổi chỉ
    # số frame của nhãn sang chỉ số hàng. Xem docs/ipn_format.md mục 6.
    frame_index, frame_match = None, None
    if task["segments"]:
        frame_index, frame_match = ipn.match_label_frames(
            ts_list, fps, ipn.label_frames(task["segments"]))
    segments, src_labels = ipn.segments_array(task["segments"],
                                              frame_index)
    meta = ipn.clip_meta(task["clip_id"], *size, fps, len(ts_list),
                         frame_match=frame_match,
                         expected_frames=task["expected_frames"],
                         split=task["split"])
    save_clip(task["out"], ts_list, xy_list, present_list, segments,
              src_labels, meta)
    return ts_list, present_list, src_labels, meta


def extract_self(task):
    """Một lần quay tự quay: mốc thời gian thật và nhãn từ tên file + file .json."""
    info = task["self"]
    sidecar = selfdata.read_sidecar(task["video"])
    ts_list, xy_list, present_list, size = track_video(task["video"], sidecar["ts"])
    segments, src_labels = selfdata.clip_segments(info["label"], ts_list,
                                                  sidecar["trim_sec"])
    meta = {"w": size[0], "h": size[1], "fps": sidecar["fps_nominal"], "source": "self",
            "subject": info["key"], "clip_id": task["clip_id"], "person": info["person"],
            "session": info["session"], "label": info["label"],
            "block": sidecar.get("block"), "trim_sec": sidecar["trim_sec"],
            "n_frames": len(ts_list), "live_check": sidecar.get("live_check")}
    Path(task["out"]).parent.mkdir(parents=True, exist_ok=True)
    save_clip(task["out"], ts_list, xy_list, present_list, segments, src_labels, meta)
    return ts_list, present_list, src_labels, meta


def extract_one(task):
    """Trích một video. Luôn trả về dict kết quả, không ném lỗi ra ngoài."""
    started = time.perf_counter()
    try:
        extract = extract_self if "self" in task else extract_ipn
        ts_list, present_list, src_labels, meta = extract(task)
        return {"clip_id": task["clip_id"], "ok": True,
                "n_frames": len(ts_list), "n_present": sum(present_list),
                "n_segments": len(src_labels),
                "length_mismatch": meta.get("length_mismatch", False),
                "seconds": time.perf_counter() - started}
    except Exception as error:                      # noqa: BLE001
        return {"clip_id": task["clip_id"], "ok": False, "n_frames": 0,
                "error": f"{type(error).__name__}: {error}",
                "seconds": time.perf_counter() - started}


def print_estimate(frames, elapsed, per_process_seconds, total_frames, workers):
    """Ước lượng thời gian trích toàn bộ nguồn, dựa trên thông lượng THỰC ĐO.

    Chỉ ngoại suy cho đúng số tiến trình vừa chạy. Nhân tốc độ một tiến trình
    với K sẽ phóng đại mức tăng tốc, vì MediaPipe đã dùng nhiều luồng cho một
    tiến trình rồi — chạy K tiến trình là chúng tranh nhau cùng số lõi.
    """
    throughput = frames / elapsed
    hours = total_frames / throughput / 3600
    print(f"\nThông lượng thực đo với {workers} tiến trình: "
          f"{throughput:.1f} frame/giây "
          f"({frames / per_process_seconds:.1f} frame/giây mỗi tiến trình).")
    print(f"Tổng số frame của nguồn: {total_frames:,}")
    print(f"  ước lượng trích toàn bộ với {workers} tiến trình: "
          f"khoảng {hours:.1f} giờ")
    print("  (muốn so sánh, chạy lại với --workers khác; đừng nhân tốc độ "
          "một tiến trình với số tiến trình)")


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--source", choices=("ipn", "self"), required=True)
    parser.add_argument("--limit", type=int, default=None,
                        help="chỉ xử lý N clip đầu (để chạy thử)")
    parser.add_argument("--workers", type=int, default=1,
                        help="số tiến trình chạy song song (mặc định %(default)s)")
    parser.add_argument("--estimate-only", action="store_true",
                        help="chỉ in ước lượng thời gian, không trích gì")
    parser.add_argument("--split", choices=("real_tune", "real_test"), default="real_tune",
                        help="chỉ với --source self (mặc định %(default)s)")
    parser.add_argument("--final", action="store_true",
                        help="bắt buộc với --split real_test: buổi chấm chỉ mở ở lần cuối")
    args = parser.parse_args()
    if args.source == "self" and args.split == "real_test" and not args.final:
        raise SystemExit("real_test chỉ được mở ở lần chạy cuối (luật 13) — thêm --final "
                         "nếu đúng là lúc đó.")

    tasks = build_tasks(args.source, args.split)
    total_frames = sum(t["expected_frames"] or 0 for t in tasks)
    todo = pending(tasks)
    done_already = len(tasks) - len(todo)
    if args.limit is not None:
        todo = todo[:args.limit]

    print(f"Nguồn {args.source}: {len(tasks)} clip, đã có {done_already} .npz, "
          f"sẽ xử lý {len(todo)}.")
    if args.estimate_only or not todo:
        if not todo:
            print("Không còn clip nào cần trích.")
        return

    run_dir = next_run_dir(config.PHASE3_RESULTS_DIR / "extract")
    write_manifest(run_dir, {"script": "extract_landmarks",
                             "source": args.source, "n_todo": len(todo),
                             "workers": args.workers})

    results, started = [], time.perf_counter()
    if args.workers > 1:
        with Pool(args.workers) as pool:
            for result in pool.imap_unordered(extract_one, todo):
                results.append(result)
                report(result, len(results), len(todo), started)
    else:
        for result in map(extract_one, todo):
            results.append(result)
            report(result, len(results), len(todo), started)

    failed = [r for r in results if not r["ok"]]
    mismatched = [r for r in results if r.get("length_mismatch")]
    if failed:
        path = config.PHASE3_RESULTS_DIR / "failed.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            for r in failed:
                f.write(f"{r['clip_id']}\t{r['error']}\n")
        print(f"\n{len(failed)} clip lỗi, đã ghi vào {relative_to_root(path)}")

    elapsed = time.perf_counter() - started
    frames = sum(r["n_frames"] for r in results)
    print(f"\nXong {len(results) - len(failed)}/{len(todo)} clip, {frames:,} "
          f"frame trong {elapsed / 60:.1f} phút.")
    if mismatched:
        print(f"{len(mismatched)} clip có length_mismatch=True "
              "(xem docs/ipn_format.md mục 6): "
              + ", ".join(r["clip_id"] for r in mismatched[:5]))

    write_manifest(run_dir, {"script": "extract_landmarks",
                             "source": args.source, "n_done": len(results),
                             "n_failed": len(failed), "workers": args.workers,
                             "elapsed_sec": elapsed, "n_frames": frames})

    if frames and elapsed > 0 and total_frames:      # tự quay không biết trước số frame
        print_estimate(frames, elapsed, sum(r["seconds"] for r in results),
                       total_frames, args.workers)


def report(result, done, total, started):
    elapsed = time.perf_counter() - started
    remaining = (elapsed / done) * (total - done)
    status = "OK  " if result["ok"] else "LỖI "
    print(f"[{done:>4}/{total}] {status}{result['clip_id']:<22} "
          f"{result['n_frames']:>5} frame  {result['seconds']:>6.1f}s  "
          f"| còn lại ~{remaining / 60:.1f} phút")
    if not result["ok"]:
        print(f"       {result['error']}")


if __name__ == "__main__":
    main()
