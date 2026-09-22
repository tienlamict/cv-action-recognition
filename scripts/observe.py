"""Chạy một thí nghiệm quan sát có tên (cẩm nang bước 6) và ghi CSV điểm mốc.

Kết quả: results/phase1/<exp>[_<condition>]/run_NN/landmarks.csv + manifest.json.
Mỗi thí nghiệm lặp ÍT NHẤT BA LẦN — mỗi lần chạy lại tạo một run_NN mới.
Sau đó chạy scripts/analyze_observations.py để ra bảng số liệu.

--flip-input là NGOẠI LỆ CHỈ DÀNH CHO THÍ NGHIỆM 6: nó lật ảnh TRƯỚC khi đưa
vào mô hình để đo quy ước nhãn Left/Right. Đường ống chính không bao giờ lật
ảnh đầu vào. Cờ này được ghi vào manifest.

Ví dụ:
    python scripts/observe.py --list
    python scripts/observe.py --exp e1_distance --condition 0.5m
    python scripts/observe.py --exp e6_handedness --condition right_flip --flip-input
    python scripts/observe.py --exp e9_jitter --seconds 10
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402

from src import config  # noqa: E402
from src.cli import add_source_arg, make_parser, setup_console  # noqa: E402
from src.hands import HandTracker  # noqa: E402
from src.io_video import iter_frames  # noqa: E402
from src.recording import record_session  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402

EXPERIMENTS = {
    "e1_distance": (
        "Tay đứng yên ở một khoảng cách. --condition là khoảng cách, ví dụ "
        "0.3m / 0.5m / 0.7m / 1.0m. Đo: tỉ lệ phát hiện, độ rung đầu ngón trỏ."
    ),
    "e2_swipe_speed": (
        "Vuốt liên tục ở cùng khoảng cách. --condition slow hoặc fast. Đo: tỉ "
        "lệ phát hiện TRONG lúc vuốt, số lần mất tay, đợt mất dài nhất."
    ),
    "e3_open_close": (
        "Xòe và chụm tay liên tục. Đo: tỉ lệ phát hiện khi chụm so với khi xòe."
    ),
    "e4_lighting": (
        "Vuốt nhanh trong phòng sáng / phòng tối. --condition bright hoặc dark. "
        "Đo: FPS xử lý, tỉ lệ phát hiện."
    ),
    "e5_context": (
        "Tay trước mặt / trên bàn phím / cầm cốc. --condition front, keyboard "
        "hoặc cup. Đo: có phát hiện không, điểm mốc có hợp lý không."
    ),
    "e6_handedness": (
        "Giơ tay phải rồi tay trái, ảnh không lật và đã lật: bốn điều kiện "
        "right_noflip, left_noflip, right_flip, left_flip (hai điều kiện _flip "
        "dùng --flip-input). Đo: nhãn Left/Right MediaPipe trả về."
    ),
    "e7_reenter": (
        "Đưa tay ra khỏi khung rồi vào lại nhiều lần. Đo: số frame mất tay "
        "trước khi điểm mốc xuất hiện lại."
    ),
    "e8_wrist_tilt": (
        "Nghiêng cổ tay. --condition 45deg hoặc 90deg. Đo: điểm mốc còn đúng "
        "không (xem bằng mắt + tỉ lệ phát hiện)."
    ),
    config.OBS_JITTER_EXPERIMENT: (
        "Cẩm nang 6.9: giữ tay HOÀN TOÀN bất động khoảng 10 giây. Đo: độ lệch "
        "chuẩn từng toạ độ → sigma cho tăng cường nhiễu Gauss ở Phase 5."
    ),
}

_CONDITION_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def flipped(frames):
    """CHỈ cho thí nghiệm 6: lật ảnh trước khi đưa vào mô hình."""
    for frame_bgr, ts in frames:
        yield cv2.flip(frame_bgr, config.DISPLAY_FLIP_CODE), ts


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--exp", choices=sorted(EXPERIMENTS),
                        help="tên thí nghiệm")
    parser.add_argument("--condition", default=None,
                        help="điều kiện của thí nghiệm, ví dụ 0.5m, fast, dark")
    parser.add_argument("--seconds", type=float, default=config.OBS_DEFAULT_SEC,
                        help="thời lượng ghi (mặc định %(default)s giây)")
    parser.add_argument("--flip-input", action="store_true",
                        help="CHỈ cho e6_handedness: lật ảnh trước khi vào mô hình")
    parser.add_argument("--no-display", action="store_true",
                        help="không mở cửa sổ hiển thị")
    parser.add_argument("--list", action="store_true",
                        help="liệt kê các thí nghiệm rồi thoát")
    add_source_arg(parser)
    args = parser.parse_args()

    if args.list or not args.exp:
        for name, text in EXPERIMENTS.items():
            print(f"{name}\n    {text}\n")
        if not args.list:
            parser.error("cần --exp")
        return

    if args.condition and not _CONDITION_PATTERN.match(args.condition):
        parser.error("--condition chỉ gồm chữ không dấu, số, '.', '_', '-'")
    if args.flip_input and args.exp != "e6_handedness":
        parser.error("--flip-input chỉ dành cho e6_handedness")

    name = f"{args.exp}_{args.condition}" if args.condition else args.exp
    print(f"Thí nghiệm {name}: {EXPERIMENTS[args.exp]}")
    print(f"Thời lượng {args.seconds:g} giây. Bấm q hoặc Esc để dừng sớm.")
    if args.flip_input:
        print("CHÚ Ý: ảnh vào mô hình ĐANG BỊ LẬT (--flip-input).")
    input("Nhấn Enter để bắt đầu ghi...")

    run_dir = next_run_dir(config.PHASE1_RESULTS_DIR / name)
    csv_path = run_dir / config.LANDMARKS_CSV_NAME
    extra = {"script": "observe", "experiment": args.exp,
             "condition": args.condition, "flip_input": args.flip_input,
             "source": str(args.source)}
    write_manifest(run_dir, extra)

    frames = iter_frames(args.source)
    if args.flip_input:
        frames = flipped(frames)

    header = [f"{name}  (INPUT FLIPPED)" if args.flip_input else name]
    with HandTracker() as tracker:
        stats = record_session(
            frames, tracker, csv_path, max_sec=args.seconds,
            show=not args.no_display,
            # Ảnh đã lật trước khi vào mô hình thì không lật thêm lần nữa.
            mirror_display=not args.flip_input,
            window_title="observe (q = stop)", header=header,
        )

    write_manifest(run_dir, {**extra, "result": stats})
    rate = stats["n_present"] / max(stats["n_frames"], 1)
    print(f"Xong: {stats['n_frames']} frame, thấy tay {rate:.1%}. "
          f"Lưu tại {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
