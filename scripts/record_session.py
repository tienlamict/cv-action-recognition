"""Phiên quay dữ liệu tự quay có hướng dẫn (Phase 11, cẩm nang bước 12).

Một buổi gồm bốn khối, theo thứ tự:

1. ``gestures`` — bốn cử chỉ, mỗi cử chỉ ``--takes`` lần, xáo trộn lẫn nhau.
   Làm theo KIỂU CỦA BẠN, nhưng giữ phần cốt lõi (xem docs/huong-dan-quay-du-lieu.md).
2. ``near`` — động tác gần giống (``REC_NEAR_GROUPS``), đều là ``none``.
3. ``transition`` — đưa tay vào khung rồi hạ xuống, cũng là ``none``.
4. ``continuous`` — các phần quay liên tục (``REC_CONTINUOUS_MIN``): tay yên, làm
   việc bình thường, với cốc, nói chuyện, khung trống. Cắt thành file
   ``REC_CHUNK_SEC`` giây.

Mỗi lần quay: đếm ngược ``REC_COUNTDOWN_SEC`` để đặt tay vào tư thế, rồi quay
``REC_CLIP_SEC``. Video ghi KHÔNG lật, kèm mốc thời gian thật của từng frame
(``src/selfdata.py``). Màn hình là bản lật gương, có khung xương tay, để thấy
ngay lần nào mất tay.

Phím: SPACE tạm dừng hoặc tiếp tục; ``r`` quay lại lần vừa xong (bản cũ chuyển
vào ``rejected/``, không xoá); ``q`` thoát. Chạy lại cùng ``--person`` và
``--session`` là làm tiếp chỗ dở; lần thoát giữa chừng cũng vào ``rejected/``.

Ví dụ:
    python scripts/record_session.py --person p01
    python scripts/record_session.py --person p01 --takes 15        # buổi chỉ để chấm
    python scripts/record_session.py --person p02 --blocks gestures near
"""

import math
import sys
from collections import namedtuple
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from src import config, selfdata  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.display import keep_on_top, make_display, read_key  # noqa: E402
from src.hands import HandTracker, empty_landmarks, seconds_to_ms  # noqa: E402
from src.io_video import iter_frames  # noqa: E402
from src.runlog import relative_to_root  # noqa: E402

WINDOW = "record (SPACE tam dung, r quay lai, q thoat)"
BLOCKS = ("gestures", "near", "transition", "continuous")
KEY_SPACE, KEY_REDO = ord(" "), ord("r")

Item = namedtuple("Item", "block label take seconds countdown")
Item.__doc__ = """Một lần quay: khối, nhãn, số thứ tự, số giây quay, số giây đếm
ngược trước đó (0 khi nối liền phần quay liên tục trước)."""


def program(person, directory, takes, near_takes, transition_takes, blocks, rng):
    """Các lần quay còn thiếu của một người trong một buổi, theo thứ tự quay."""
    def missing(labels):
        return {label: set(selfdata.existing_takes(directory, person, label))
                for label in labels}

    items = []
    takes_by_block = (("gestures", selfdata.GESTURES, takes),
                      ("near", selfdata.near_labels(), near_takes),
                      ("transition", (selfdata.TRANSITION,), transition_takes))
    for block, labels, n in takes_by_block:
        if block in blocks and n > 0:
            items += [Item(block, label, take, config.REC_CLIP_SEC, config.REC_COUNTDOWN_SEC)
                      for label, take in selfdata.schedule(labels, n, rng, missing(labels))]
    if "continuous" in blocks:
        for label, minutes in zip(selfdata.continuous_labels(),
                                  config.REC_CONTINUOUS_MIN.values()):
            total = minutes * 60
            have = set(selfdata.existing_takes(directory, person, label))
            first = True
            for chunk in range(1, math.ceil(total / config.REC_CHUNK_SEC) + 1):
                if chunk in have:
                    continue
                seconds = min(config.REC_CHUNK_SEC, total - (chunk - 1) * config.REC_CHUNK_SEC)
                items.append(Item("continuous", label, chunk, seconds,
                                  config.REC_COUNTDOWN_SEC if first else 0.0))
                first = False
    return items


def checks_hand(item):
    """Lần quay này phải thấy tay — khung trống và các phần liên tục thì không."""
    return item.block != "continuous"


class Take:
    """Một lần đang quay: ghi frame vào video và giữ mốc thời gian."""

    def __init__(self, path, item, size):
        self.path, self.item, self.size = path, item, size
        self.writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*config.REC_FOURCC),
                                      config.CAM_FPS, size)
        if not self.writer.isOpened():
            raise SystemExit(f"OpenCV không mở được bộ ghi {config.REC_FOURCC} cho {path.name}.")
        self.ts, self.present = [], []

    def add(self, frame_bgr, ts, present):
        self.writer.write(frame_bgr)
        self.ts.append(ts)
        self.present.append(present)

    def finish(self, person, session, tracked):
        self.writer.release()
        hand = float(np.mean(self.present)) if tracked and self.present else None
        selfdata.write_sidecar(
            self.path, self.ts, person=person, session=session, label=self.item.label,
            take=self.item.take, block=self.item.block, planned_sec=self.item.seconds,
            trim_sec=config.REC_TRIM_SEC if self.item.block == "gestures" else 0.0,
            w=int(self.size[0]), h=int(self.size[1]), fps_nominal=config.CAM_FPS,
            hand_share=hand, created=datetime.now().isoformat(timespec="seconds"))
        return hand


def screen(item, index, total, state, remaining, note, paused):
    """Dòng chữ và chữ lớn của màn hình quay, toàn ASCII."""
    head = f"{item.block} {index + 1}/{total}  {item.label} #{item.take:02d}"
    lines = [head, selfdata.PROMPTS[item.label]]
    if paused:
        big = "TAM DUNG - SPACE"
    elif state == "countdown":
        big = f"{math.ceil(remaining)}"
    else:
        big = f"REC {remaining:.1f}"
    if note:
        lines.append(note)
    lines.append("SPACE tam dung   r quay lai lan vua xong   q thoat")
    return lines, big


def run(args):
    session = args.session or date.today().isoformat()
    selfdata.clip_name(args.person, selfdata.GESTURES[0], 1)     # kiểm mã người
    directory = Path(args.out or config.RAW_DIR) / session
    directory.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(config.SEED + int(args.person[1:]))
    queue = program(args.person, directory, args.takes, args.near_takes,
                    args.transition_takes, args.blocks, rng)
    if not queue:
        print(f"{args.person} đã quay đủ các khối {', '.join(args.blocks)} của buổi {session}.")
        return []
    print(f"{args.person}, buổi {session}: {len(queue)} lần quay còn thiếu → "
          f"{relative_to_root(directory)}", flush=True)

    saved, low_hand = [], []
    index, state, start, take, paused, note, last = 0, "countdown", None, None, False, "", None
    tracker = None if args.no_track else HandTracker()
    shown = False
    try:
        for frame_bgr, ts in iter_frames(args.source):
            h, w = frame_bgr.shape[:2]
            xy, present = empty_landmarks(), False
            if tracker is not None:
                xy, present, _ = tracker.process(frame_bgr, seconds_to_ms(ts))
            item = queue[index]
            if start is None or (paused and state == "countdown"):
                start = ts
            if state == "countdown" and ts - start >= item.countdown and not paused:
                path = directory / f"{selfdata.clip_name(args.person, item.label, item.take)}.mp4"
                take, state, start = Take(path, item, (w, h)), "record", ts
            if state == "record":
                take.add(frame_bgr, ts, present)
                if ts - start >= item.seconds:
                    hand = take.finish(args.person, session, tracker is not None)
                    saved.append(take.path)
                    last, note = take, ""
                    if hand is not None and checks_hand(item) and hand < config.REC_MIN_HAND_SHARE:
                        low_hand.append(take.path.name)
                        note = f"Lan vua roi chi thay tay {hand:.0%} - bam r de quay lai"
                    take, state, start = None, "countdown", ts
                    index += 1
                    if index == len(queue):
                        break
                    if queue[index].block != item.block and not args.no_display:
                        paused, note = True, f"Xong khoi {item.block}. Tiep: {queue[index].block}"
            if not args.no_display:
                current = queue[index]
                remaining = (current.countdown - (ts - start) if state == "countdown"
                             else current.seconds - (ts - start))
                lines, big = screen(current, index, len(queue), state, max(remaining, 0.0),
                                    note, paused)
                colors = [config.COLOR_ALERT if state == "record" else None] + [None] * (len(lines) - 1)
                cv2.imshow(WINDOW, make_display(frame_bgr, xy, lines, big_text=big,
                                                line_colors=colors))
                if not shown:
                    keep_on_top(WINDOW)
                    shown = True
                key = read_key()
                if key in config.QUIT_KEYS:
                    break
                if key == KEY_SPACE and state == "countdown":
                    paused = not paused
                    note = "" if not paused else note
                if key == KEY_REDO and state == "countdown" and last is not None:
                    selfdata.reject(last.path)
                    saved.remove(last.path)
                    if last.path.name in low_hand:
                        low_hand.remove(last.path.name)
                    queue.insert(index, last.item)
                    note, last, start = f"Quay lai {last.item.label} #{last.item.take:02d}", None, ts
    finally:
        if take is not None:                     # thoát hay hết nguồn giữa một lần quay
            take.finish(args.person, session, tracker is not None)
            selfdata.reject(take.path)
        if tracker is not None:
            tracker.close()
        if not args.no_display:
            cv2.destroyAllWindows()

    left = len(queue) - index
    print(f"Đã ghi {len(saved)} lần quay vào {relative_to_root(directory)}"
          + (f"; còn {left} lần — chạy lại cùng lệnh để làm tiếp." if left else "; đủ cả buổi."))
    if low_hand:
        print("Thấy tay ít — nên xem lại: " + ", ".join(low_hand))
    return saved


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--person", required=True, help="mã người quay, ví dụ p01")
    parser.add_argument("--session", default=None,
                        help="tên buổi quay (thư mục con của data/raw); mặc định là ngày hôm nay")
    parser.add_argument("--takes", type=int, default=config.REC_GESTURE_TAKES,
                        help="số lần mỗi cử chỉ (mặc định %(default)s)")
    parser.add_argument("--near-takes", type=int, default=config.REC_NEAR_TAKES,
                        help="số lần mỗi động tác gần giống (mặc định %(default)s)")
    parser.add_argument("--transition-takes", type=int, default=config.REC_TRANSITION_TAKES,
                        help="số lần đưa tay vào khung rồi hạ xuống (mặc định %(default)s)")
    parser.add_argument("--blocks", nargs="+", default=list(BLOCKS), choices=BLOCKS)
    parser.add_argument("--source", default=config.CAM_INDEX,
                        help="webcam (số) hoặc file video — file chỉ để kiểm thử")
    parser.add_argument("--out", default=None, help="thư mục gốc (mặc định data/raw)")
    parser.add_argument("--no-display", action="store_true", help="không mở cửa sổ")
    parser.add_argument("--no-track", action="store_true",
                        help="không chạy MediaPipe lúc quay (máy yếu)")
    args = parser.parse_args()
    if isinstance(args.source, str) and args.source.isdigit():
        args.source = int(args.source)
    run(args)


if __name__ == "__main__":
    main()
