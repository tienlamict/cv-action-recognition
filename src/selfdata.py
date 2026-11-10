"""Dữ liệu tự quay (Phase 11): tên file là nhãn, và lịch quay của một buổi.

Mỗi buổi quay là một thư mục ``data/raw/<buổi>/``, mặc định đặt theo ngày. Mỗi
lần quay là hai file cùng tên:

- ``p03_swipe_left_07.mp4`` — video KHÔNG lật, đúng như camera thấy;
- ``p03_swipe_left_07.json`` — mốc thời gian thật của từng frame và thông tin
  buổi quay.

Tên file cho đủ ba điều (cẩm nang 12.5): mã người ``p03``, nhãn ``swipe_left``,
số thứ tự ``07``. Nhãn là một trong bốn cử chỉ, hoặc ``none-<nhóm>`` cho những
gì phải ra ``none``: động tác gần giống (``none-wave``…), đưa tay vào khung
(``none-transition``), và các phần quay liên tục (``none-work``…).

Mốc thời gian lấy từ đồng hồ thật lúc quay, không từ FPS ghi trong file. FPS
webcam không phải hằng số — nó tụt khi phòng tối — nên chia số thứ tự frame cho
FPS danh nghĩa sẽ làm cử chỉ nhanh hay chậm hơn thật, trong khi đặc trưng và
LSTM đều đo tốc độ.

Mỗi lần quay cử chỉ được kiểm tra ngay lúc quay (:func:`check_take`) bằng đúng
các hàm gán nhãn của bộ cửa sổ, để người quay làm lại ngay những lần sẽ dạy sai.
"""

import json
import re
from collections import namedtuple
from pathlib import Path

import numpy as np

from src import config
from src.preprocess import load_sequence
from src.windows import (DIRECTION, DTYPES, core_signal, core_steps, cut_windows,
                         motion_signal, step_labels)

GESTURES = tuple(config.CLASSES[1:])
NONE_PREFIX = "none-"
TRANSITION = "none-transition"
NAME_RE = re.compile(r"^(p\d{2})_([a-z]+(?:[_-][a-z]+)*)_(\d{2,3})$")
REJECTED = "rejected"           # thư mục con chứa các lần quay hỏng — không xoá
KEY_LEN = np.dtype(DTYPES["subject"]).itemsize // np.dtype("<U1").itemsize
                                # mã người–buổi phải vừa cột subject của bộ cửa sổ

SelfClip = namedtuple("SelfClip", "person label take session")

#: Lời nhắc trên màn hình quay. Không dấu, vì cv2.putText chỉ vẽ ASCII.
PROMPTS = {
    "swipe_left": "VUOT TRAI: tay yen, roi hat ro sang trai cua ban",
    "swipe_right": "VUOT PHAI: tay yen, roi hat ro sang phai cua ban",
    "zoom_in": "ZOOM IN: chum san cai-tro, roi tach ra nhanh",
    "zoom_out": "ZOOM OUT: mo san cai-tro, roi chum lai nhanh",
    "none-wave": "VAY TAY qua lai",
    "none-throwup": "HAT TAY LEN tren",
    "none-throwdown": "HAT TAY XUONG duoi",
    "none-rotate": "XOAY CO TAY",
    "none-spread": "XOE CA NAM NGON tu nam tay",
    "none-point": "CHI TRO vao man hinh",
    TRANSITION: "DUA TAY VAO KHUNG roi HA TAY XUONG",
    "none-rest": "DE TAY YEN trong khung",
    "none-work": "LAM VIEC BINH THUONG: go phim, chuot, doc",
    "none-incidental": "VOI COC, GAI DAU, CHINH KINH...",
    "none-talk": "NOI CHUYEN, khua tay tu nhien",
    "none-empty": "KHONG DE TAY trong khung",
}


def none_label(group):
    return NONE_PREFIX + group


def near_labels():
    """Nhãn của các động tác gần giống — quay từng lần như cử chỉ."""
    return tuple(none_label(g) for g in config.REC_NEAR_GROUPS)


def continuous_labels():
    """Nhãn của các phần quay liên tục, theo thứ tự quay."""
    return tuple(none_label(g) for g in config.REC_CONTINUOUS_MIN)


def class_of(label):
    """Nhãn trong tên file → chỉ số lớp trong ``CLASSES``.

    Raises:
        ValueError: nhãn không thuộc bốn cử chỉ và không có tiền tố ``none-``.
    """
    if label in GESTURES:
        return config.CLASSES.index(label)
    if label.startswith(NONE_PREFIX) and label in PROMPTS:
        return config.CLASSES.index("none")
    raise ValueError(f"Nhãn lạ '{label}' — có: {', '.join(PROMPTS)}")


def clip_name(person, label, take):
    """``p03_swipe_left_07`` — tên chung của file video và file mốc thời gian."""
    name = f"{person}_{label}_{take:02d}"
    parse_name(name)        # tên không tự đọc lại được thì đừng ghi
    return name


def parse_name(path):
    """Tên file → ``SelfClip``; buổi quay là tên thư mục chứa file.

    Raises:
        ValueError: tên sai quy ước, hay nhãn lạ.
    """
    path = Path(path)
    match = NAME_RE.match(path.stem)
    if match is None:
        raise ValueError(f"'{path.name}' sai quy ước tên p03_swipe_left_07")
    person, label, take = match.groups()
    class_of(label)
    return SelfClip(person, label, int(take), path.parent.name)


def session_key(person, session):
    """``p01/2026-11-06``: một người trong một buổi. Đây là đơn vị chia
    ``real_tune``/``real_test`` (luật 15), và là cột ``subject`` của cửa sổ tự quay.
    p01 có buổi ở cả hai phía, nên mã người thôi là không đủ.

    Raises:
        ValueError: dài quá cột ``subject`` của bộ cửa sổ.
    """
    key = f"{person}/{session}"
    if len(key) > KEY_LEN:
        raise ValueError(f"Mã '{key}' dài quá {KEY_LEN} ký tự — đặt tên buổi ngắn hơn")
    return key


def sessions(raw_dir=None):
    """Mọi người–buổi có lần quay dùng được. Bỏ ``rejected/`` và file thiếu mốc
    thời gian.

    Returns:
        dict ``mã người–buổi → list video``, đã sắp xếp.
    """
    raw_dir = Path(raw_dir or config.RAW_DIR)
    out = {}
    for folder in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        for video in sorted(folder.glob("*.mp4")):
            try:
                clip = parse_name(video)
            except ValueError:
                continue
            if video.with_suffix(".json").is_file():
                out.setdefault(session_key(clip.person, clip.session), []).append(video)
    return out


def existing_takes(directory, person, label):
    """Số thứ tự các lần quay đã có của một người và một nhãn, trong một buổi.
    Lần quay hỏng đã chuyển vào ``rejected/`` không tính."""
    out = []
    for path in Path(directory).glob(f"{person}_{label}_*.mp4"):
        try:
            clip = parse_name(path)
        except ValueError:
            continue
        if clip.label == label and path.with_suffix(".json").is_file():
            out.append(clip.take)
    return sorted(out)


def schedule(labels, takes, rng, done=None):
    """Lịch quay các lần còn thiếu: mỗi nhãn ``takes`` lần, xáo trộn lẫn nhau
    để người quay không làm một cử chỉ nhiều lần liền theo quán tính.

    Args:
        done: ``nhãn → tập số thứ tự đã có`` — buổi quay dở được làm tiếp, và
            một lần đã chuyển vào ``rejected/`` được quay lại đúng số đó.

    Returns:
        list ``(nhãn, số thứ tự)``.
    """
    done = done or {}
    items = [(label, take) for label in labels for take in range(1, takes + 1)
             if take not in done.get(label, ())]
    order = rng.permutation(len(items))
    return [items[i] for i in order]


def reject(video_path):
    """Chuyển một lần quay hỏng (video và file mốc thời gian) vào ``rejected/``.
    Không xoá gì: số thứ tự đó được quay lại, bản hỏng vẫn còn để xem.

    Returns:
        đường dẫn mới của video.
    """
    video_path = Path(video_path)
    target_dir = video_path.parent / REJECTED
    target_dir.mkdir(exist_ok=True)
    stem, n = video_path.stem, 1
    while (target_dir / f"{stem}~{n}.mp4").exists():
        n += 1
    moved = target_dir / f"{stem}~{n}.mp4"
    video_path.rename(moved)
    sidecar = video_path.with_suffix(".json")
    if sidecar.is_file():
        sidecar.rename(moved.with_suffix(".json"))
    return moved


def clip_segments(label, ts, trim_sec):
    """Đoạn gán nhãn của một lần quay, đúng dạng ``segments``/``src_labels`` của
    file ``.npz``. Kiểm tra lúc quay và trích điểm mốc dùng chung hàm này.

    - Cử chỉ: một đoạn, bỏ ``trim_sec`` giây đầu và cuối (cẩm nang 12.6). Lúc
      vừa bắt đầu quay, người quay chưa làm; lúc sắp bấm SPACE, đã làm xong.
    - ``none``: cả lần quay.

    Args:
        ts: ``(N,)`` giây của từng frame, tăng dần.

    Returns:
        ``(segments, src_labels)``: ``(1, 3)`` int64 ``[start, end, class_id]``
        theo chỉ số frame, và ``(1,)`` nhãn trong tên file.
    """
    ts = np.asarray(ts, dtype=np.float64)
    cls = class_of(label)
    start, end = 0, ts.size
    if cls != 0:
        start = int(np.searchsorted(ts, ts[0] + trim_sec))
        end = max(start, int(np.searchsorted(ts, ts[-1] - trim_sec, side="right")))
    return np.array([[start, end, cls]], dtype=np.int64), np.array([label])


TakeCheck = namedtuple("TakeCheck", "problem core_sec rival_sec ratio n_windows")
TakeCheck.__doc__ = """Kết quả kiểm tra một lần quay cử chỉ (:func:`check_take`).

- ``problem``: ``None`` nếu ổn, hoặc một khoá của :data:`CHECK_NOTES`;
- ``core_sec``: khoảnh khắc chính mà việc gán nhãn sẽ chọn, giây từ frame đầu;
- ``rival_sec``, ``ratio``: chuyển động mạnh nhất ở chỗ khác trong lần quay,
  cách khoảnh khắc chính ít nhất ``REC_CORE_SEP_SEC``, và độ mạnh của nó chia
  cho độ mạnh của khoảnh khắc chính;
- ``n_windows``: số cửa sổ mang nhãn cử chỉ mà lần quay này cho bộ dữ liệu."""

#: Lời báo trên màn hình quay khi một lần quay cử chỉ nên làm lại. ASCII, một dòng.
CHECK_NOTES = {
    "no_hand": "Lan vua roi: khong thay tay luc lam cu chi",
    "no_window": "Lan vua roi: mat tay quanh cu chi, hoac qua ngan",
    "early": "Lan vua roi: lam som qua - doi 1 giay roi hay lam",
    "late": "Lan vua roi: bam SPACE som qua - giu yen 1 giay",
    "unclear": "Lan vua roi: chua ro - chuan bi cham, lam dut khoat",
}


def check_take(ts, xy_norm, w, h, label, trim_sec):
    """Lần quay cử chỉ này có dạy đúng cử chỉ không. Đo bằng đúng các hàm gán
    nhãn của bộ cửa sổ (``src/windows.py``), không phải một bản "gần giống".

    Theo thứ tự:

    1. ``no_hand``: không tìm được khoảnh khắc chính, vì mất tay cả đoạn.
    2. ``no_window``: không cắt được cửa sổ nào mang nhãn cử chỉ. Lần quay quá
       ngắn, hoặc mất tay quanh khoảnh khắc chính.
    3. Có một chuyển động khác, cách khoảnh khắc chính ít nhất
       ``REC_CORE_SEP_SEC``, mạnh từ ``REC_CORE_RATIO_MAX`` lần khoảnh khắc chính
       trở lên. Độ mạnh là :func:`windows.core_signal`, đo trên CẢ lần quay:

       - nằm trong phần bỏ ĐẦU → ``early``: cử chỉ làm ngay khi vừa bắt đầu
         quay, rơi ra ngoài đoạn gán nhãn;
       - nằm trong phần bỏ CUỐI → ``late``: bấm SPACE quá sớm sau cử chỉ;
       - nằm trong đoạn → ``unclear``: chuẩn bị hay thu tay mạnh ngang động tác
         chính. Lần trích sau, điểm mốc lệch một chút là chọn nhầm nó làm
         khoảnh khắc chính, và cử chỉ thật bị bỏ.

    Args:
        ts: ``(N,)`` giây của từng frame, tăng dần.
        xy_norm: ``(N, 21, 2)`` toạ độ chuẩn hoá của MediaPipe, NaN khi mất tay.
        w, h: cỡ frame.
        label: một trong bốn cử chỉ.
        trim_sec: như :func:`clip_segments`.

    Returns:
        ``TakeCheck``.

    Raises:
        ValueError: ``label`` là ``none`` — không có khoảnh khắc chính để kiểm.
    """
    ts = np.asarray(ts, dtype=np.float64)
    ts = ts - ts[0]
    cls = class_of(label)
    if cls == 0:
        raise ValueError(f"'{label}' là none: chỉ kiểm tra lần quay cử chỉ")
    segments, src = clip_segments(label, ts, trim_sec)
    grid, xy = load_sequence(ts, xy_norm, w, h)
    _, segment = step_labels(ts, segments, src, grid)
    core = core_steps(xy, segment, segments).get(0)
    windows, _ = cut_windows(ts, xy_norm, w, h, segments, src)
    n_windows = int(np.sum(windows["y"] == cls))
    if core is None:
        return TakeCheck("no_hand", None, None, None, n_windows)
    core_sec = round(float(grid[core]), 3)
    if n_windows == 0:
        return TakeCheck("no_window", core_sec, None, None, 0)

    curve = core_signal(xy, np.arange(grid.size), label)
    steps = np.arange(grid.size)
    far = np.abs(steps - core) >= config.window_steps(config.REC_CORE_SEP_SEC)
    if not far.any():
        return TakeCheck(None, core_sec, None, 0.0, n_windows)
    rival = int(steps[far][np.argmax(curve[far])])
    peak, other = float(curve[core]), float(curve[rival])
    rival_sec = round(float(grid[rival]), 3)
    if peak <= 0 and other <= 0:                    # không gì chuyển động
        return TakeCheck("unclear", core_sec, rival_sec, None, n_windows)
    ratio = other / peak if peak > 0 else np.inf
    problem = None
    if ratio >= config.REC_CORE_RATIO_MAX:
        inside = np.flatnonzero(segment == 0)
        problem = ("early" if rival < inside[0] else "late" if rival > inside[-1]
                   else "unclear")
    return TakeCheck(problem, core_sec, rival_sec, round(min(ratio, 99.0), 3), n_windows)


def model_paths(with_self, seed):
    """Rừng và LSTM của một bên, một hạt (Phase 11).

    Bên IPN thuần với hạt ``SEED`` là chính mô hình demo (``RF_MODEL_PATH``,
    ``LSTM_MODEL_PATH``). Bên học thêm ``real_tune`` với hạt ``SEED`` là
    ``SELF_RF_PATH``, ``SELF_LSTM_PATH``. Các hạt còn lại nằm trong ``SELF_SEED_DIR``.

    Returns:
        ``(đường dẫn rừng, đường dẫn LSTM)``.
    """
    if seed == config.SEED:
        return ((config.SELF_RF_PATH, config.SELF_LSTM_PATH) if with_self
                else (config.RF_MODEL_PATH, config.LSTM_MODEL_PATH))
    side = "self" if with_self else "ipn"
    return (config.SELF_SEED_DIR / f"rf_{side}_s{seed}.joblib",
            config.SELF_SEED_DIR / f"lstm_{side}_s{seed}.pt")


def window_progress(label, win):
    """Quãng đi theo chiều của cử chỉ trên MỘT cửa sổ đã chuẩn hoá ``(T, 21, 2)``,
    tính từ bước đầu. Vuốt: vị trí ngang cổ tay; zoom: độ mở cái–trỏ
    (``windows.motion_signal``, chiều theo ``windows.DIRECTION``).

    Returns:
        ``(ròng, xa nhất)`` — độ dời ở bước cuối, và quãng đi xa nhất theo đúng chiều.
    """
    signal = motion_signal(win, label)
    s = DIRECTION[label] * (signal - signal[0])
    s = s[np.isfinite(s)]
    return float(s[-1]), float(s.max())


def window_ok(label, win):
    """Một đoạn học tự quay có dạy đúng cử chỉ không: đi đúng chiều, ít nhất
    ``SELF_MIN_NET``, và không kéo ngược lại quá ``SELF_MAX_BACK`` quãng đã đi.

    Dấu chuyển động dùng để LOẠI đoạn học, không để gán nhãn. Chỉ áp cho
    ``real_tune``: tập chấm giữ nguyên như quay (results/phase11/qa_p02.md).
    """
    net, ahead = window_progress(label, win)
    return net >= config.SELF_MIN_NET[label] and ahead - net <= config.SELF_MAX_BACK * ahead


def write_sidecar(video_path, ts, **meta):
    """Ghi file mốc thời gian cạnh video: ``ts`` tính bằng giây từ frame đầu."""
    ts = np.asarray(ts, dtype=np.float64)
    ts = ts - ts[0]
    span = ts[-1] if ts.size > 1 else 0.0
    payload = {**meta, "n_frames": int(ts.size),
               "fps_measured": (ts.size - 1) / span if span > 0 else None,
               "ts": [round(float(t), 6) for t in ts]}
    path = Path(video_path).with_suffix(".json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def read_sidecar(video_path):
    return json.loads(Path(video_path).with_suffix(".json").read_text(encoding="utf-8"))
