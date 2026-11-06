"""Phiên quay dữ liệu tự quay có hướng dẫn (Phase 11, cẩm nang bước 12).

Một buổi gồm bốn khối, theo thứ tự:

1. ``gestures`` — bốn cử chỉ, mỗi cử chỉ ``--takes`` lần, xáo trộn lẫn nhau.
   Làm theo KIỂU CỦA BẠN, nhưng giữ phần cốt lõi (docs/huong-dan-quay-du-lieu.md).
2. ``near`` — động tác gần giống (``REC_NEAR_GROUPS``), đều là ``none``.
3. ``transition`` — đưa tay vào khung rồi hạ xuống, cũng là ``none``.
4. ``continuous`` — các phần quay liên tục (``REC_CONTINUOUS_MIN``): tay yên, làm
   việc bình thường, với cốc, nói chuyện, khung trống. Tự cắt thành file
   ``REC_CHUNK_SEC`` giây.

**Người quay tự quyết nhịp** (đổi 2026-11-07: đoạn quay cố định 3 giây quá vội).
Ba khối đầu quay từng lần:

- SPACE: lưu lần đang quay và **bắt đầu ngay lần tiếp theo**; lúc đang nghỉ thì
  bắt đầu quay;
- ``p``: lưu lần đang quay rồi nghỉ;
- ``r``: đang quay thì bỏ lần này và quay lại ngay; đang nghỉ thì quay lại lần
  vừa lưu. Bản bỏ đi chuyển vào ``rejected/``, không bao giờ bị xoá;
- ``q``: thoát. Lần đang quay dở vào ``rejected/``; chạy lại cùng ``--person`` và
  ``--session`` là làm tiếp chỗ dở.

Bấm SPACE sớm hơn ``REC_MIN_CLIP_SEC`` sau khi bắt đầu một lần là bấm nhầm: bỏ
đoạn đó, quay lại đúng lần ấy. Quá ``REC_MAX_CLIP_SEC`` thì màn hình nhắc lưu.

Video ghi KHÔNG lật, kèm mốc thời gian thật của từng frame (``src/selfdata.py``).
Màn hình là bản lật gương, có khung xương tay, để thấy ngay lần nào mất tay.

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

WINDOW = "record (SPACE luu va quay tiep, p nghi, r quay lai, q thoat)"
BLOCKS = ("gestures", "near", "transition", "continuous")
KEY_SPACE, KEY_PAUSE, KEY_REDO = ord(" "), ord("p"), ord("r")
IDLE, RECORD = "idle", "record"

Item = namedtuple("Item", "block label take seconds")
Item.__doc__ = """Một lần quay: khối, nhãn, số thứ tự; ``seconds`` là độ dài của
một file quay liên tục, ``None`` với lần quay mà người quay tự kết thúc."""


def program(person, directory, takes, near_takes, transition_takes, blocks, rng):
    """Các lần quay còn thiếu của một người trong một buổi, theo thứ tự quay."""
    def done(labels):
        return {label: set(selfdata.existing_takes(directory, person, label))
                for label in labels}

    items = []
    takes_by_block = (("gestures", selfdata.GESTURES, takes),
                      ("near", selfdata.near_labels(), near_takes),
                      ("transition", (selfdata.TRANSITION,), transition_takes))
    for block, labels, n in takes_by_block:
        if block in blocks and n > 0:
            items += [Item(block, label, take, None)
                      for label, take in selfdata.schedule(labels, n, rng, done(labels))]
    if "continuous" in blocks:
        for label, minutes in zip(selfdata.continuous_labels(),
                                  config.REC_CONTINUOUS_MIN.values()):
            total = minutes * 60
            have = set(selfdata.existing_takes(directory, person, label))
            for chunk in range(1, math.ceil(total / config.REC_CHUNK_SEC) + 1):
                if chunk not in have:
                    items.append(Item("continuous", label, chunk, min(
                        config.REC_CHUNK_SEC, total - (chunk - 1) * config.REC_CHUNK_SEC)))
    return items


class Take:
    """Một lần đang quay: ghi frame vào video và giữ mốc thời gian."""

    def __init__(self, path, item, size, ts):
        self.path, self.item, self.size, self.start = path, item, size, ts
        self.writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*config.REC_FOURCC),
                                      config.CAM_FPS, size)
        if not self.writer.isOpened():
            raise SystemExit(f"OpenCV không mở được bộ ghi {config.REC_FOURCC} cho {path.name}.")
        self.ts, self.present = [], []

    def add(self, frame_bgr, ts, present):
        self.writer.write(frame_bgr)
        self.ts.append(ts)
        self.present.append(present)

    def elapsed(self, ts):
        return ts - self.start

    def finish(self, person, session, tracked):
        """Đóng video và ghi file mốc thời gian. Returns: tỉ lệ frame thấy tay."""
        self.writer.release()
        hand = float(np.mean(self.present)) if tracked and self.present else None
        selfdata.write_sidecar(
            self.path, self.ts or [self.start], person=person, session=session,
            label=self.item.label, take=self.item.take, block=self.item.block,
            trim_sec=config.REC_TRIM_SEC if self.item.block == "gestures" else 0.0,
            stream_ts0=round(float(self.ts[0] if self.ts else self.start), 6),
            w=int(self.size[0]), h=int(self.size[1]), fps_nominal=config.CAM_FPS,
            hand_share=hand, created=datetime.now().isoformat(timespec="seconds"))
        return hand


def screen(item, index, total, state, elapsed, note):
    """Các dòng chữ và chữ lớn của màn hình quay, toàn ASCII."""
    lines = [f"{item.block} {index + 1}/{total}  {item.label} #{item.take:02d}",
             selfdata.PROMPTS[item.label]]
    if state == IDLE:
        big = "SPACE"
        keys = "SPACE bat dau   r quay lai lan vua luu   q thoat"
    elif item.seconds is not None:
        big = f"REC {max(item.seconds - elapsed, 0.0):.0f}s"
        keys = "p nghi   q thoat"
    else:
        big = f"REC {elapsed:.1f}"
        keys = "SPACE luu + lan sau   p luu + nghi   r quay lai   q thoat"
        if elapsed > config.REC_MAX_CLIP_SEC:
            note = f"Qua {config.REC_MAX_CLIP_SEC:.0f}s - SPACE de luu, r de quay lai"
    if note:
        lines.append(note)
    lines.append(keys)
    return lines, big


def run(args, keys=None):
    """Chạy một buổi quay.

    Args:
        keys: hàm ``(ts, trạng thái, số giây đã quay của lần hiện tại) → mã phím``
            thay cho bàn phím — để kiểm thử không cần người bấm. ``None``: đọc
            bàn phím qua cửa sổ.

    Returns:
        list đường dẫn các video đã lưu.
    """
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

    tracker = None if args.no_track else HandTracker()
    saved, low_hand = [], []
    state, index, take, last, note, shown = IDLE, 0, None, None, "", False

    def start(frame_bgr, ts):
        item = queue[index]
        path = directory / f"{selfdata.clip_name(args.person, item.label, item.take)}.mp4"
        h, w = frame_bgr.shape[:2]
        return Take(path, item, (w, h), ts)

    def discard(current):
        current.finish(args.person, session, tracker is not None)
        selfdata.reject(current.path)

    def save(current):
        """Lưu một lần quay; trả về ghi chú cho màn hình."""
        hand = current.finish(args.person, session, tracker is not None)
        saved.append(current.path)
        if (hand is not None and current.item.block != "continuous"
                and hand < config.REC_MIN_HAND_SHARE):
            low_hand.append(current.path.name)
            return f"Lan vua roi chi thay tay {hand:.0%} - bam r de quay lai"
        return ""

    try:
        for frame_bgr, ts in iter_frames(args.source):
            xy, present = empty_landmarks(), False
            if tracker is not None:
                xy, present, _ = tracker.process(frame_bgr, seconds_to_ms(ts))
            if take is not None:
                take.add(frame_bgr, ts, present)
            elapsed = take.elapsed(ts) if take is not None else 0.0
            key = (keys(ts, state, elapsed) if keys is not None
                   else -1 if args.no_display else read_key())
            if key in config.QUIT_KEYS:
                break
            item = queue[index]

            if state == IDLE:
                if key == KEY_SPACE:
                    take, state, note = start(frame_bgr, ts), RECORD, ""
                elif key == KEY_REDO and last is not None:
                    selfdata.reject(last.path)
                    saved.remove(last.path)
                    if last.path.name in low_hand:
                        low_hand.remove(last.path.name)
                    queue.insert(index, last.item)
                    note, last = f"Quay lai {last.item.label} #{last.item.take:02d}: SPACE", None
            elif item.seconds is not None:                       # quay liên tục
                if key in (KEY_SPACE, KEY_PAUSE) and elapsed < config.REC_MIN_CLIP_SEC:
                    discard(take)                                # vừa bắt đầu đã dừng
                    take, state = None, IDLE
                elif elapsed >= item.seconds or key in (KEY_SPACE, KEY_PAUSE):
                    note, last = save(take), take
                    take, index = None, index + 1
                    if index == len(queue):
                        break
                    nxt = queue[index]
                    if key not in (KEY_SPACE, KEY_PAUSE) and nxt.label == item.label:
                        take = start(frame_bgr, ts)              # nối liền file sau
                    else:
                        state = IDLE
            elif key == KEY_REDO:
                discard(take)
                take, note = start(frame_bgr, ts), f"Quay lai {item.label} #{item.take:02d}"
            elif key in (KEY_SPACE, KEY_PAUSE):
                if elapsed < config.REC_MIN_CLIP_SEC:            # bấm nhầm hai lần liền
                    discard(take)
                    take = start(frame_bgr, ts) if key == KEY_SPACE else None
                    state = RECORD if take is not None else IDLE
                    note = f"Bam qua nhanh - quay lai {item.label} #{item.take:02d}"
                else:
                    note, last = save(take), take
                    take, index = None, index + 1
                    if index == len(queue):
                        break
                    nxt = queue[index]
                    if key == KEY_SPACE and nxt.block == item.block:
                        take = start(frame_bgr, ts)
                    else:
                        state = IDLE
                        if nxt.block != item.block:
                            note = f"Xong khoi {item.block}. Tiep: {nxt.block} - SPACE"

            if not args.no_display and index < len(queue):
                lines, big = screen(queue[index], index, len(queue), state,
                                    take.elapsed(ts) if take is not None else 0.0, note)
                colors = [config.COLOR_ALERT if state == RECORD else None] + [None] * (len(lines) - 1)
                cv2.imshow(WINDOW, make_display(frame_bgr, xy, lines, big_text=big,
                                                line_colors=colors))
                if not shown:
                    keep_on_top(WINDOW)
                    shown = True
    finally:
        if take is not None:                     # thoát hay hết nguồn giữa một lần quay
            discard(take)
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
                        help="webcam (số) hoặc file video — file chỉ để thử")
    parser.add_argument("--out", default=None, help="thư mục gốc (mặc định data/raw)")
    parser.add_argument("--no-track", action="store_true",
                        help="không chạy MediaPipe lúc quay (máy yếu)")
    args = parser.parse_args()
    args.no_display = False          # cần cửa sổ để bấm phím
    if isinstance(args.source, str) and args.source.isdigit():
        args.source = int(args.source)
    run(args)


if __name__ == "__main__":
    main()
