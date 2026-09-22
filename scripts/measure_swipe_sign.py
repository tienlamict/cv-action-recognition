"""ĐO hằng số SWIPE_LEFT_SIGN — không đoán.

Quy trình có hướng dẫn trên màn hình: với mỗi lần (mặc định SWIPE_MEASURE_REPS
lần), đếm ngược rồi hiện "SWIPE LEFT NOW" — bạn vuốt tay sang TRÁI CỦA BẠN.
Với mỗi lần, lấy x của cổ tay ở frame có tay cuối trừ frame có tay đầu, trên
ảnh KHÔNG lật. Dấu của trung vị là SWIPE_LEFT_SIGN.

Script KHÔNG tự sửa config.py. Nó in ra đúng dòng cần dán vào config.py — chỉ
khi kết quả dứt khoát. Chạy ba lần độc lập; ba lần phải cho cùng một dấu.

Kết quả lưu ở results/phase1/swipe_sign/run_NN/: landmarks.csv (mọi frame),
reps.csv (từng lần vuốt) và manifest.json (kèm kết luận).

Ví dụ:
    python scripts/measure_swipe_sign.py
    python scripts/measure_swipe_sign.py --reps 5
"""

import math
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402

from src import config  # noqa: E402
from src.calibration import decide_sign, rep_dx  # noqa: E402
from src.cli import add_source_arg, make_parser, setup_console  # noqa: E402
from src.display import make_display, quit_pressed  # noqa: E402
from src.fps import FpsMeter  # noqa: E402
from src.hands import HandTracker  # noqa: E402
from src.io_video import iter_frames  # noqa: E402
from src.recording import FrameCsvWriter, status_lines, track  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.tables import write_table  # noqa: E402

RUN_NAME = "swipe_sign"
WINDOW = "measure_swipe_sign (q = abort)"

INSTRUCTIONS = """
ĐO SWIPE_LEFT_SIGN
------------------
1. Ngồi cách webcam khoảng nửa mét, giơ MỘT bàn tay vào giữa khung hình.
2. Mỗi lần có {countdown:.0f} giây chuẩn bị ("Get ready"), rồi {record:.1f} giây
   ghi ("SWIPE LEFT NOW").
3. Khi thấy "SWIPE LEFT NOW": vuốt tay sang TRÁI CỦA BẠN — theo cảm nhận của
   người làm cử chỉ. Trên màn hình (ảnh gương) tay cũng đi sang trái.
4. Giữ tay trong khung suốt lúc vuốt. Làm tổng cộng {reps} lần.
Bấm q hoặc Esc để huỷ.
"""


def collect(source, reps, csv_path):
    """Chạy phiên đo. Trả về danh sách x cổ tay của từng lần, hoặc None nếu huỷ."""
    countdown = config.SWIPE_MEASURE_COUNTDOWN_SEC
    period = countdown + config.SWIPE_MEASURE_RECORD_SEC
    total = reps * period
    wrist_x = [[] for _ in range(reps)]

    fps_meter = FpsMeter()
    with HandTracker() as tracker, FrameCsvWriter(csv_path) as writer:
        try:
            for tracked in track(iter_frames(source), tracker):
                writer.write_tracked(tracked)
                fps_meter.tick(tracked.ts)
                if tracked.ts >= total:
                    return wrist_x

                k = int(tracked.ts // period)
                t_in = tracked.ts - k * period
                if t_in >= countdown:
                    # Toạ độ trên ảnh KHÔNG lật; NaN khi mất tay.
                    wrist_x[k].append(float(tracked.xy_norm[config.WRIST, 0]))
                    big = f"SWIPE LEFT NOW  {k + 1}/{reps}"
                else:
                    big = f"Get ready {k + 1}/{reps}: {countdown - t_in:.1f}"

                cv2.imshow(WINDOW, make_display(
                    tracked.frame_bgr, tracked.xy_norm,
                    status_lines(tracked, fps_meter), big_text=big,
                ))
                if quit_pressed():
                    return None
        finally:
            cv2.destroyAllWindows()
    # Nguồn cạn trước khi đủ số lần (ví dụ video quá ngắn).
    return wrist_x


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--reps", type=int, default=config.SWIPE_MEASURE_REPS,
                        help="số lần vuốt trái (mặc định %(default)s)")
    add_source_arg(parser)
    args = parser.parse_args()

    print(INSTRUCTIONS.format(countdown=config.SWIPE_MEASURE_COUNTDOWN_SEC,
                              record=config.SWIPE_MEASURE_RECORD_SEC,
                              reps=args.reps))
    input("Nhấn Enter khi đã sẵn sàng...")

    run_dir = next_run_dir(config.PHASE1_RESULTS_DIR / RUN_NAME)
    extra = {"script": "measure_swipe_sign", "source": str(args.source),
             "reps": args.reps}
    write_manifest(run_dir, extra)

    wrist_x = collect(args.source, args.reps,
                      run_dir / config.LANDMARKS_CSV_NAME)
    if wrist_x is None:
        write_manifest(run_dir, {**extra, "result": "aborted"})
        print("Đã huỷ giữa chừng — không kết luận.")
        return

    rows, dxs = [], []
    for k, xs in enumerate(wrist_x):
        dx, n_present = rep_dx(xs)
        dxs.append(dx)
        rows.append({"rep": k + 1, "n_frames": len(xs),
                     "n_present": n_present, "dx": dx,
                     "valid": math.isfinite(dx)
                     and abs(dx) >= config.SWIPE_MEASURE_MIN_DX})
    write_table(rows, ["rep", "n_frames", "n_present", "dx", "valid"],
                run_dir / "reps")

    result = decide_sign(dxs)
    write_manifest(run_dir, {**extra, "result": result})

    print("\nTừng lần vuốt (dx theo tỉ lệ chiều rộng khung, ảnh không lật):")
    for row in rows:
        mark = "hợp lệ" if row["valid"] else "LOẠI"
        print(f"  lần {row['rep']:2d}: dx = {row['dx']:+.3f}   "
              f"({row['n_present']}/{row['n_frames']} frame thấy tay, {mark})")
    print(f"\nTrung vị dx = {result['median_dx']:+.3f}; {result['reason']}.")
    print(f"Lưu tại {relative_to_root(run_dir)}")

    if result["sign"] is None:
        print("\nKẾT QUẢ KHÔNG DỨT KHOÁT — không điền config.py. Chạy lại, vuốt "
              "rõ ràng hơn và giữ tay trong khung.")
        return

    print("\nDán dòng sau vào src/config.py, thay cho dòng SWIPE_LEFT_SIGN = None:\n")
    print(f"SWIPE_LEFT_SIGN = {result['sign']}    # đo {date.today()} bằng "
          f"measure_swipe_sign.py ({run_dir.name}): {result['n_agree']}/"
          f"{result['n_reps']} lần cùng dấu, trung vị dx = "
          f"{result['median_dx']:+.3f} W")
    print("\nNhớ chạy đủ ba lần độc lập và kiểm tra ba lần cùng dấu trước khi dán.")


if __name__ == "__main__":
    main()
