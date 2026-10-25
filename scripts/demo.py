"""Demo thời gian thực: webcam → 21 điểm → cửa sổ 1,2 giây → đặc trưng → mô hình
→ máy trạng thái kích hoạt → lệnh.

Mỗi STRIDE_SEC giây ra một nhãn mới, nên nhãn nhấp nháy khi làm cử chỉ — đó là
chuyện bình thường của mô hình. Máy trạng thái (src/activation.py, Phase 9) biến
chuỗi nhãn thành lệnh rời rạc: màn hình hiện trạng thái của nó và lệnh vừa phát
(">> COMMAND"). Hạ tay ra khỏi khung hình là huỷ.

Phím c bật/tắt ĐIỀU KHIỂN — gửi phím tắt thật qua pyautogui (CTRL_HOTKEYS: vuốt
trái → slide trước, vuốt phải → slide sau, zoom → Ctrl +/−). Mặc định TẮT. Phím
tắt đi vào cửa sổ đang có focus: bấm c trong cửa sổ demo, rồi bấm chuột vào ứng
dụng trình chiếu (PowerPoint: đang chạy trình chiếu, F5). Cửa sổ demo luôn nằm
trên cùng nên vẫn nhìn thấy. Phím ? (hoặc h) hiện tóm tắt docs/gestures.md.

Màn hình là bản LẬT GƯƠNG cho người xem; ảnh vào mô hình không lật. "-" nghĩa là
không có cửa sổ hợp lệ (chưa đủ 1,2 giây, mất tay, hay tay nghiêng cạnh ở đầu
cửa sổ).

--show-features: chế độ luyện làm cử chỉ theo IPN. Phím 1–4 chọn cử chỉ đang
luyện; các đặc trưng SHOW_FEATURES của cửa sổ vừa rồi — ba đặc trưng của cổng
cộng độ xòe open_range — tô xanh nếu nằm trong hộp 25–75 của lớp đó trên IPN,
đỏ nếu nằm ngoài. Với vuốt, open_range xanh nghĩa là bàn tay có mở ra trong lúc
hất như IPN. Log của --log ghi đúng các đặc trưng này.

--log FILE: ghi mỗi lần dự đoán vào FILE (CSV, kèm trạng thái máy kích hoạt, lệnh
vừa phát và phím đã gửi), MỌI lần chuyển trạng thái vào FILE_fsm.csv, và điểm mốc
thô của cả phiên vào FILE_landmarks.npz — chạy lại phiên đó qua mô hình bất kỳ
bằng scripts/replay_log.py.

Bấm q hoặc Esc để thoát. Mọi xử lý nằm trong src/live.py — file này chỉ nối
webcam, màn hình và log.

Ví dụ:
    python scripts/demo.py --model rules
    python scripts/demo.py --model rf --log results/phase6/live_rf.csv
    python scripts/demo.py --model lstm --log results/phase7/live_lstm.csv
    python scripts/demo.py --model rules --show-features
    python scripts/demo.py --model rules --log results/phase5/misfires_log.csv
    python scripts/demo.py --source data/ipn/videos/videos/1CM42_11_R__205.avi --no-display --max-sec 30
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402

from src import config  # noqa: E402
from src.activation import ActivationFSM  # noqa: E402
from src.cli import add_source_arg, make_parser, setup_console  # noqa: E402
from src.control import Controller  # noqa: E402
from src.display import keep_on_top, make_display, read_key  # noqa: E402
from src.fps import FpsMeter  # noqa: E402
from src.hands import HandTracker  # noqa: E402
from src.io_video import iter_frames  # noqa: E402
from src.live import (PRACTICE_CLASSES, LandmarkRecorder,  # noqa: E402
                      LivePredictor, PredictionLog, TransitionLog, count_episodes,
                      fsm_log_path, help_screen, label_name, landmarks_path,
                      load_feature_ranges, make_model, recent_command, screen_lines)
from src.recording import track  # noqa: E402

WINDOW = "demo (q = quit)"


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--model", default="rules", choices=config.MODEL_NAMES)
    add_source_arg(parser)
    parser.add_argument("--log", default=None, help="ghi mỗi lần dự đoán vào CSV")
    parser.add_argument("--show-features", action="store_true",
                        help="chế độ luyện làm cử chỉ theo IPN (phím 1-4)")
    parser.add_argument("--no-display", action="store_true",
                        help="không mở cửa sổ — chạy thử trên file video")
    parser.add_argument("--max-sec", type=float, default=None,
                        help="dừng sau bấy nhiêu giây")
    args = parser.parse_args()

    predictor = LivePredictor(make_model(args.model))
    ranges = load_feature_ranges() if args.show_features else None
    practice = PRACTICE_CLASSES[0] if args.show_features else None
    log = PredictionLog(args.log) if args.log else None
    transitions = TransitionLog(fsm_log_path(args.log)) if args.log else None
    recorder = LandmarkRecorder() if args.log else None
    fsm = ActivationFSM(on_transition=transitions.write if transitions else None)
    controller = Controller()
    fps_meter = FpsMeter()
    last, labels, commands, show_help, on_top = None, [], [], False, False

    with HandTracker() as tracker:
        try:
            for tracked in track(iter_frames(args.source), tracker):
                h, w = tracked.frame_bgr.shape[:2]
                fps_meter.tick(tracked.ts)
                prediction = predictor.update(tracked.ts, tracked.xy_norm, w, h)
                if recorder:
                    recorder.add(tracked.ts, tracked.xy_norm, tracked.present, w, h)
                if prediction is not None:
                    last = prediction
                    labels.append(prediction.label)
                    command = fsm.update(prediction.label, prediction.confidence,
                                         prediction.presence, prediction.ts)
                    if command is not None:
                        commands.append((prediction.ts, command))
                    sent = controller.handle(command)
                    if log:
                        log.write(prediction, fsm.state, command, sent)
                    if args.no_display and prediction.label not in (None, 0):
                        print(f"{prediction.ts:7.2f}s  {label_name(prediction.label):<12}"
                              f"{prediction.confidence:.2f}"
                              + ("" if command is None else
                                 f"  >> LỆNH {label_name(command)}"))

                if not args.no_display:
                    lines, colors, big = help_screen() if show_help else screen_lines(
                        last, fps_meter.rolling_fps, ranges, practice, state=fsm.state,
                        command=recent_command(commands, tracked.ts),
                        control=controller.enabled)
                    cv2.imshow(WINDOW, make_display(tracked.frame_bgr,
                                                    tracked.xy_norm, lines,
                                                    big_text=big,
                                                    line_colors=colors))
                    if not on_top:
                        keep_on_top(WINDOW)
                        on_top = True
                    key = read_key()
                    if key in config.QUIT_KEYS:
                        break
                    if key in config.DISPLAY_HELP_KEYS:
                        show_help = not show_help
                    if key == config.CTRL_TOGGLE_KEY:
                        try:
                            print("Điều khiển: BẬT — bấm chuột vào cửa sổ trình chiếu để "
                                  "phím tắt đi vào đó" if controller.toggle()
                                  else "Điều khiển: tắt")
                        except RuntimeError as error:
                            print(error)
                    if practice and ord("1") <= key < ord("1") + len(PRACTICE_CLASSES):
                        practice = PRACTICE_CLASSES[key - ord("1")]
                if args.max_sec is not None and tracked.ts >= args.max_sec:
                    break
        finally:
            cv2.destroyAllWindows()
            if log:
                log.close()
            if transitions:
                transitions.close()
            if recorder and recorder.ts:
                recorder.save(landmarks_path(args.log), model=args.model)

    n_valid = sum(label is not None for label in labels)
    print(f"\n{len(labels)} lần dự đoán, {n_valid} có cửa sổ hợp lệ.")
    print("Số đợt báo (chuỗi dự đoán liền nhau cùng lớp):",
          count_episodes(labels))
    print(f"Máy trạng thái phát {len(commands)} lệnh:",
          {name: sum(label_name(c) == name for _, c in commands)
           for name in PRACTICE_CLASSES})
    summary = fps_meter.summary()
    if summary:
        print(f"FPS trung bình {summary['mean_fps']:.1f}, "
              f"phân vị {config.FPS_LOW_PERCENTILE:g}% thấp {summary['low_fps']:.1f}")
    if log:
        print(f"Log: {log.path}")
        print(f"Chuyển trạng thái: {transitions.path}")
        print(f"Điểm mốc (chạy lại bằng scripts/replay_log.py): {landmarks_path(args.log)}")


if __name__ == "__main__":
    main()
