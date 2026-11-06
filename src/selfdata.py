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
"""

import json
import re
from collections import namedtuple
from pathlib import Path

import numpy as np

from src import config

GESTURES = tuple(config.CLASSES[1:])
NONE_PREFIX = "none-"
TRANSITION = "none-transition"
NAME_RE = re.compile(r"^(p\d{2})_([a-z]+(?:[_-][a-z]+)*)_(\d{2,3})$")
REJECTED = "rejected"           # thư mục con chứa các lần quay hỏng — không xoá

SelfClip = namedtuple("SelfClip", "person label take session")

#: Lời nhắc trên màn hình quay. Không dấu, vì cv2.putText chỉ vẽ ASCII.
PROMPTS = {
    "swipe_left": "VUOT TRAI: hat tay sang trai cua ban, kieu cua ban",
    "swipe_right": "VUOT PHAI: hat tay sang phai cua ban, kieu cua ban",
    "zoom_in": "ZOOM IN: tach ngon cai khoi ngon tro (mo ra)",
    "zoom_out": "ZOOM OUT: chum ngon cai ve ngon tro",
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
