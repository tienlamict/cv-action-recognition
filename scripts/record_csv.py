"""Ghi điểm mốc ra CSV, mỗi frame một dòng — kể cả frame mất tay.

Kết quả: results/phase1/<name>/run_NN/landmarks.csv kèm manifest.json.
Cột: ts, present, score, handedness, w, h, x0..x20, y0..y20. Frame mất tay vẫn
có dòng, các cột toạ độ để trống.

Dừng khi hết --seconds, khi hết video, hoặc khi bấm q/Esc.

Ví dụ:
    python scripts/record_csv.py --name thu_nghiem --seconds 30
    python scripts/record_csv.py --name ipn_mau --source data/ipn/videos/videos/1CM1_1_R__217.avi --no-display
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config  # noqa: E402
from src.cli import add_source_arg, make_parser, setup_console  # noqa: E402
from src.hands import HandTracker  # noqa: E402
from src.io_video import iter_frames  # noqa: E402
from src.recording import record_session  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--name", default="recording",
                        help="tên lần ghi, thành tên thư mục trong "
                             "results/phase1/ (mặc định %(default)s)")
    parser.add_argument("--seconds", type=float, default=None,
                        help="dừng sau số giây này (mặc định: chạy tới khi "
                             "bấm q hoặc hết video)")
    parser.add_argument("--no-display", action="store_true",
                        help="không mở cửa sổ hiển thị")
    add_source_arg(parser)
    args = parser.parse_args()

    run_dir = next_run_dir(config.PHASE1_RESULTS_DIR / args.name)
    csv_path = run_dir / config.LANDMARKS_CSV_NAME
    extra = {"script": "record_csv", "source": str(args.source)}
    write_manifest(run_dir, extra)
    print(f"Ghi vào {relative_to_root(csv_path)} ...")

    with HandTracker() as tracker:
        stats = record_session(
            iter_frames(args.source), tracker, csv_path,
            max_sec=args.seconds, show=not args.no_display,
            window_title="record_csv (q = stop)",
        )

    write_manifest(run_dir, {**extra, "result": stats})
    print(f"Xong: {stats['n_frames']} dòng = {stats['n_frames']} frame, "
          f"thấy tay {stats['n_present']}, dài {stats['duration_sec']:.1f} s.")


if __name__ == "__main__":
    main()
