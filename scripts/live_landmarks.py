"""Xem 21 điểm mốc bám theo bàn tay trên webcam, kèm FPS.

Ảnh vào mô hình KHÔNG lật; chỉ bản hiển thị được lật như gương. FPS trung bình
và phân vị thấp chỉ tính sau FPS_WARMUP_SEC giây đầu.

Bấm q hoặc Esc để thoát.

Ví dụ:
    python scripts/live_landmarks.py
    python scripts/live_landmarks.py --source data/raw/p03_swipe_left_07.mp4
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402

from src import config  # noqa: E402
from src.cli import add_source_arg, make_parser, setup_console  # noqa: E402
from src.display import make_display, quit_pressed  # noqa: E402
from src.fps import FpsMeter  # noqa: E402
from src.hands import HandTracker  # noqa: E402
from src.io_video import iter_frames  # noqa: E402
from src.recording import status_lines, track  # noqa: E402

WINDOW = "live_landmarks (q = quit)"


def main():
    setup_console()
    parser = make_parser(__doc__)
    add_source_arg(parser)
    args = parser.parse_args()

    fps_meter = FpsMeter()
    n_frames = n_present = 0
    with HandTracker() as tracker:
        try:
            for tracked in track(iter_frames(args.source), tracker):
                if n_frames == 0:
                    h, w = tracked.frame_bgr.shape[:2]
                    print(f"Khung hình: {w}x{h} "
                          f"(cấu hình: {config.CAM_W}x{config.CAM_H})")
                n_frames += 1
                n_present += tracked.present
                fps_meter.tick(tracked.ts)

                cv2.imshow(WINDOW, make_display(
                    tracked.frame_bgr, tracked.xy_norm,
                    status_lines(tracked, fps_meter),
                ))
                if quit_pressed():
                    break
        finally:
            cv2.destroyAllWindows()

    print(f"Số frame: {n_frames}, thấy tay: {n_present} "
          f"({n_present / max(n_frames, 1):.1%})")
    summary = fps_meter.summary()
    if summary:
        print(f"FPS sau {config.FPS_WARMUP_SEC:.0f} giây đầu: trung bình "
              f"{summary['mean_fps']:.1f}, phân vị "
              f"{config.FPS_LOW_PERCENTILE:g}% thấp {summary['low_fps']:.1f} "
              f"(trên {summary['n_frames']} frame)")
    else:
        print(f"Chạy chưa đủ {config.FPS_WARMUP_SEC:.0f} giây để thống kê FPS.")


if __name__ == "__main__":
    main()
