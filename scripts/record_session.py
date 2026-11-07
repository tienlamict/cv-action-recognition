"""Phiên quay dữ liệu tự quay có hướng dẫn (Phase 11, cẩm nang bước 12).

Một buổi gồm bốn khối, theo thứ tự:

1. ``gestures`` — bốn cử chỉ, mỗi cử chỉ ``--takes`` lần, xáo trộn lẫn nhau.
   Làm theo KIỂU CỦA BẠN, nhưng giữ phần cốt lõi (docs/huong-dan-quay-du-lieu.md).
2. ``near`` — động tác gần giống (``REC_NEAR_GROUPS``), đều là ``none``.
3. ``transition`` — đưa tay vào khung rồi hạ xuống, cũng là ``none``.
4. ``continuous`` — các phần quay liên tục (``REC_CONTINUOUS_MIN``): tay yên, làm
   việc bình thường, với cốc, nói chuyện, khung trống. Tự cắt thành file
   ``REC_CHUNK_SEC`` giây.

Chủ đề tài (``REC_MAIN_PERSON``) mặc định quay đủ bốn khối. Người khác (p02…) mặc
định chỉ quay ``REC_HELPER_BLOCKS``, mỗi cử chỉ ``REC_HELPER_TAKES`` lần (người dùng
chốt 2026-11-06/07 để buổi quay ngắn). ``--takes`` và ``--blocks`` vẫn đè được.

**Một phím bắt đầu, SPACE kết thúc** (người dùng đổi 2026-11-07). Kết thúc xong,
máy luôn nghỉ và chờ lần bắt đầu sau, không tự quay tiếp:

- ``REC_START_KEY`` (``b``): bắt đầu lần quay sắp tới. Ở khối quay liên tục, các
  file của một phần tự nối liền nhau tới khi hết giờ;
- ``REC_STOP_KEY`` (SPACE): kết thúc và lưu lần đang quay; ở khối quay liên tục,
  dừng phần đang quay;
- ``REC_REDO_KEY`` (``r``): đang quay thì bỏ lần này; đang nghỉ thì quay lại lần
  vừa lưu. Bản bỏ đi chuyển vào ``rejected/``, không bao giờ bị xoá;
- ``q``: thoát. Lần đang quay dở vào ``rejected/``; chạy lại cùng ``--person`` và
  ``--session`` là làm tiếp chỗ dở.

Kết thúc sớm hơn ``REC_MIN_CLIP_SEC`` sau khi bắt đầu là bấm nhầm: bỏ đoạn đó,
lần ấy vẫn chờ quay. Quá ``REC_MAX_CLIP_SEC`` thì màn hình nhắc kết thúc.

**Kiểm tra từng lần quay cử chỉ** (thêm 2026-11-06: hai trong bốn lần quay thử có
động tác chuẩn bị mạnh ngang cử chỉ). Lúc lưu, ``selfdata.check_take`` chạy đúng
các hàm gán nhãn trên điểm mốc vừa theo dõi được. Lần nào sẽ dạy sai thì màn hình
báo lý do: ``r`` quay lại đúng lần đó, ``b`` giữ lần đó rồi quay tiếp. Lời báo thấy
tay ít cũng vậy. Kết quả kiểm tra ghi vào file mốc thời gian (``live_check``), để
bước trích điểm mốc so lại.

Video ghi KHÔNG lật, kèm mốc thời gian thật của từng frame (``src/selfdata.py``).
Màn hình là bản lật gương, có khung xương tay, để thấy ngay lần nào mất tay.

Ví dụ:
    python scripts/record_session.py --person p01                  # đủ bốn khối
    python scripts/record_session.py --person p01 --takes 15       # buổi chỉ để chấm
    python scripts/record_session.py --person p02                  # chỉ bốn cử chỉ, 5 lần mỗi cử chỉ
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

BLOCKS = ("gestures", "near", "transition", "continuous")
START, STOP, REDO = config.REC_START_KEY, config.REC_STOP_KEY, config.REC_REDO_KEY
IDLE, RECORD = "idle", "record"


def key_name(code):
    """Tên phím in lên màn hình: ``SPACE``, hay chính ký tự."""
    return "SPACE" if code == ord(" ") else chr(code)


WINDOW = (f"record ({key_name(START)} bat dau, {key_name(STOP)} ket thuc, "
          f"{key_name(REDO)} quay lai, q thoat)")

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
    """Một lần đang quay: ghi frame vào video, giữ mốc thời gian và điểm mốc tay."""

    def __init__(self, path, item, size, ts):
        self.path, self.item, self.size, self.start = path, item, size, ts
        self.writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*config.REC_FOURCC),
                                      config.CAM_FPS, size)
        if not self.writer.isOpened():
            raise SystemExit(f"OpenCV không mở được bộ ghi {config.REC_FOURCC} cho {path.name}.")
        self.ts, self.xy, self.present = [], [], []

    def add(self, frame_bgr, ts, xy, present):
        self.writer.write(frame_bgr)
        self.ts.append(ts)
        self.xy.append(xy)
        self.present.append(present)

    def elapsed(self, ts):
        return ts - self.start

    def finish(self, person, session, tracked, check=False):
        """Đóng video và ghi file mốc thời gian.

        Args:
            tracked: có điểm mốc tay (MediaPipe chạy lúc quay).
            check: kiểm tra lần quay cử chỉ (``selfdata.check_take``) và ghi kết
                quả vào file mốc thời gian. Cần ``tracked``.

        Returns:
            ``(tỉ lệ frame thấy tay, TakeCheck)``; ``None`` cho thứ không đo.
        """
        self.writer.release()
        hand = float(np.mean(self.present)) if tracked and self.present else None
        trim = config.REC_TRIM_SEC if self.item.block == "gestures" else 0.0
        result = None
        if check and tracked and self.item.block == "gestures" and len(self.ts) >= 2:
            result = selfdata.check_take(self.ts, np.asarray(self.xy), self.size[0],
                                         self.size[1], self.item.label, trim)
        selfdata.write_sidecar(
            self.path, self.ts or [self.start], person=person, session=session,
            label=self.item.label, take=self.item.take, block=self.item.block,
            trim_sec=trim, stream_ts0=round(float(self.ts[0] if self.ts else self.start), 6),
            w=int(self.size[0]), h=int(self.size[1]), fps_nominal=config.CAM_FPS,
            hand_share=hand, live_check=result._asdict() if result is not None else None,
            created=datetime.now().isoformat(timespec="seconds"))
        return hand, result


def screen(item, index, total, state, elapsed, note, alert=False):
    """Các dòng chữ, chữ lớn và màu từng dòng của màn hình quay, toàn ASCII.

    Args:
        item: lần quay sắp tới hay đang quay. ``None``: đã hết buổi nhưng lần
            cuối vừa bị báo, máy chờ người quay kết thúc buổi (SPACE) hay làm lại
            (``r``).
        alert: ``note`` là lời báo nên làm lại, vẽ bằng màu cảnh báo.

    Returns:
        ``(các dòng, chữ lớn, màu từng dòng)``.
    """
    begin, stop, redo = key_name(START), key_name(STOP), key_name(REDO)
    if item is None:
        lines = ["Het buoi", note, f"{stop} ket thuc buoi   {redo} quay lai lan do"]
        return lines, stop, [None, config.COLOR_ALERT if alert else None, None]
    lines = [f"{item.block} {index + 1}/{total}  {item.label} #{item.take:02d}",
             selfdata.PROMPTS[item.label]]
    if state == IDLE:
        big = f"Bam {begin.upper()}"
        keys = (f"{redo} quay lai lan do   {begin} giu lan do, quay tiep" if alert
                else f"{begin} bat dau   {redo} quay lai lan vua luu   q thoat")
    elif item.seconds is not None:
        big = f"REC {max(item.seconds - elapsed, 0.0):.0f}s"
        keys = f"{stop} dung   q thoat"
    else:
        big = f"REC {elapsed:.1f}"
        keys = f"{stop} ket thuc   {redo} bo lan nay   q thoat"
        if elapsed > config.REC_MAX_CLIP_SEC:
            note = f"Qua {config.REC_MAX_CLIP_SEC:.0f}s - {stop} de ket thuc, {redo} de bo"
            alert = True
    colors = [config.COLOR_ALERT if state == RECORD else None, None]
    if note:
        lines.append(note)
        colors.append(config.COLOR_ALERT if alert else None)
    lines.append(keys)
    colors.append(None)
    return lines, big, colors


def run(args, keys=None, tracker=None):
    """Chạy một buổi quay.

    Args:
        keys: hàm ``(ts, trạng thái, số giây đã quay của lần hiện tại) → mã phím``
            thay cho bàn phím — để kiểm thử không cần người bấm. ``None``: đọc
            bàn phím qua cửa sổ.
        tracker: thay cho ``HandTracker`` (cần ``process`` và ``close``) — để
            kiểm thử phép kiểm tra từng lần quay mà không cần camera. ``None``:
            tạo ``HandTracker``, trừ khi ``--no-track``.

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

    if tracker is None and not args.no_track:
        tracker = HandTracker()
    saved, low_hand, flagged = [], [], []
    state, index, take, last, note, alert, shown = IDLE, 0, None, None, "", False, False

    def start(frame_bgr, ts):
        item = queue[index]
        path = directory / f"{selfdata.clip_name(args.person, item.label, item.take)}.mp4"
        h, w = frame_bgr.shape[:2]
        return Take(path, item, (w, h), ts)

    def discard(current):
        current.finish(args.person, session, tracker is not None)
        selfdata.reject(current.path)

    def save(current):
        """Lưu một lần quay. Returns: lời báo nếu lần này nên làm lại, không thì ``""``."""
        hand, check = current.finish(args.person, session, tracker is not None, check=True)
        saved.append(current.path)
        if check is not None and check.problem is not None:
            flagged.append(current.path.name)
            return selfdata.CHECK_NOTES[check.problem]
        if (hand is not None and current.item.block != "continuous"
                and hand < config.REC_MIN_HAND_SHARE):
            low_hand.append(current.path.name)
            return f"Lan vua roi: chi thay tay {hand:.0%}"
        return ""

    try:
        for frame_bgr, ts in iter_frames(args.source):
            xy, present = empty_landmarks(), False
            if tracker is not None:
                xy, present, _ = tracker.process(frame_bgr, seconds_to_ms(ts))
            if take is not None:
                take.add(frame_bgr, ts, xy, present)
            elapsed = take.elapsed(ts) if take is not None else 0.0
            key = (keys(ts, state, elapsed) if keys is not None
                   else -1 if args.no_display else read_key())
            if 0 <= key < 128:
                key = ord(chr(key).lower())                      # Caps Lock bật vẫn nhận phím
            if key in config.QUIT_KEYS:
                break
            item = queue[index] if index < len(queue) else None   # None: hết buổi, lần cuối bị báo
            again = f"bam {key_name(START)} de quay lai"

            if state == IDLE:
                if key == REDO and last is not None:
                    selfdata.reject(last.path)
                    saved.remove(last.path)
                    for names in (low_hand, flagged):
                        if last.path.name in names:
                            names.remove(last.path.name)
                    queue.insert(index, last.item)
                    note = f"Quay lai {last.item.label} #{last.item.take:02d}: bam {key_name(START)}"
                    alert, last = False, None
                elif item is None:
                    if key in (START, STOP):
                        break                                    # giữ lần cuối, xong buổi
                elif key == START:
                    take, state, note, alert = start(frame_bgr, ts), RECORD, "", False
                elif key == STOP and not alert:                  # quen tay bấm SPACE lúc nghỉ
                    note = f"Dang nghi - bam {key_name(START)} de bat dau"
            elif item.seconds is not None:                       # quay liên tục
                if key == STOP and elapsed < config.REC_MIN_CLIP_SEC:
                    discard(take)                                # vừa bắt đầu đã dừng
                    take, state, note = None, IDLE, f"Qua ngan, da bo - {again}"
                elif elapsed >= item.seconds or key == STOP:
                    note, last = save(take), take
                    take, index = None, index + 1
                    if index == len(queue):
                        break
                    if key != STOP and queue[index].label == item.label:
                        take = start(frame_bgr, ts)              # nối liền file sau
                    else:
                        state = IDLE
            elif key == REDO:                                    # bỏ lần đang quay, chờ bắt đầu lại
                discard(take)
                take, state, alert = None, IDLE, False
                note = f"Da bo {item.label} #{item.take:02d} - {again}"
            elif key == STOP:
                if elapsed < config.REC_MIN_CLIP_SEC:            # vừa bắt đầu đã kết thúc: bấm nhầm
                    discard(take)
                    take, state, alert, note = None, IDLE, False, f"Qua ngan, da bo - {again}"
                else:
                    note, last = save(take), take
                    alert = bool(note)               # lần vừa lưu nên làm lại: chờ r hay b
                    take, state, index = None, IDLE, index + 1
                    nxt = queue[index] if index < len(queue) else None
                    if nxt is None and not alert:
                        break
                    if not alert:
                        note = (f"Xong khoi {item.block}. Tiep: {nxt.block}"
                                if nxt.block != item.block
                                else f"Da luu {item.label} #{item.take:02d}")

            if not args.no_display:
                lines, big, colors = screen(
                    queue[index] if index < len(queue) else None, index, len(queue), state,
                    take.elapsed(ts) if take is not None else 0.0, note, alert)
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
    if flagged:
        print("Bị báo nên làm lại nhưng vẫn giữ — nên xem lại: " + ", ".join(flagged))
    if low_hand:
        print("Thấy tay ít — nên xem lại: " + ", ".join(low_hand))
    return saved


def default_plan(person):
    """Số lần mỗi cử chỉ và các khối mặc định của một người.

    Chủ đề tài (``REC_MAIN_PERSON``) quay đủ bốn khối. Người khác chỉ quay
    ``REC_HELPER_BLOCKS``, mỗi cử chỉ ``REC_HELPER_TAKES`` lần.

    Returns:
        ``(số lần mỗi cử chỉ, list khối)``.
    """
    if person == config.REC_MAIN_PERSON:
        return config.REC_GESTURE_TAKES, list(BLOCKS)
    return config.REC_HELPER_TAKES, list(config.REC_HELPER_BLOCKS)


def parse_args(argv=None):
    """Tham số dòng lệnh; ``--takes`` và ``--blocks`` bỏ trống thì lấy
    :func:`default_plan` của ``--person``."""
    parser = make_parser(__doc__)
    parser.add_argument("--person", required=True, help="mã người quay, ví dụ p01")
    parser.add_argument("--session", default=None,
                        help="tên buổi quay (thư mục con của data/raw); mặc định là ngày hôm nay")
    parser.add_argument("--takes", type=int, default=None,
                        help=f"số lần mỗi cử chỉ (mặc định: {config.REC_MAIN_PERSON} "
                             f"{config.REC_GESTURE_TAKES}, người khác {config.REC_HELPER_TAKES})")
    parser.add_argument("--near-takes", type=int, default=config.REC_NEAR_TAKES,
                        help="số lần mỗi động tác gần giống (mặc định %(default)s)")
    parser.add_argument("--transition-takes", type=int, default=config.REC_TRANSITION_TAKES,
                        help="số lần đưa tay vào khung rồi hạ xuống (mặc định %(default)s)")
    parser.add_argument("--blocks", nargs="+", default=None, choices=BLOCKS,
                        help=f"các khối cần quay (mặc định: {config.REC_MAIN_PERSON} đủ bốn khối, "
                             f"người khác chỉ {' '.join(config.REC_HELPER_BLOCKS)})")
    parser.add_argument("--source", default=config.CAM_INDEX,
                        help="webcam (số) hoặc file video — file chỉ để thử")
    parser.add_argument("--out", default=None, help="thư mục gốc (mặc định data/raw)")
    parser.add_argument("--no-track", action="store_true",
                        help="không chạy MediaPipe lúc quay (máy yếu)")
    args = parser.parse_args(argv)
    takes, blocks = default_plan(args.person)
    args.takes = takes if args.takes is None else args.takes
    args.blocks = blocks if args.blocks is None else args.blocks
    args.no_display = False          # cần cửa sổ để bấm phím
    if isinstance(args.source, str) and args.source.isdigit():
        args.source = int(args.source)
    return args


def main():
    setup_console()
    run(parse_args())


if __name__ == "__main__":
    main()
