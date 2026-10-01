"""Đọc nhãn IPN Hand và ánh xạ 14 lớp gốc về 5 lớp của đề tài.

Mọi quy ước ở đây đến từ khảo sát thật trên đĩa, ghi trong ``docs/ipn_format.md``:

- Chỉ số frame trong file nhãn **1-based**, và ``t_end`` **thuộc** đoạn. Sang
  chỉ số Python là ``[t_start - 1, t_end)``.
- Mã người diễn là ``IPN_SUBJECT_TOKENS`` token đầu của tên video. Cách này cho
  đúng 50 mã và không mã nào nằm ở cả train lẫn test của split chính thức.
- Các đoạn phủ liên tục cả video: lớp ``D0X`` chính là phần không cử chỉ xen
  giữa, nên không có frame nào "không thuộc đoạn nào".

Mười lớp cử chỉ không dùng **không bị bỏ đi** — chúng thành ``none`` và là mẫu
âm khó. Nhãn gốc được giữ trong ``src_labels`` để Phase 8 trả lời được câu hỏi
"*loại* ``none`` nào bị nhận nhầm".
"""

import csv
from pathlib import Path

import numpy as np

from src import config

#: 14 lớp gốc của IPN → lớp của đề tài. Xem docs/ipn_format.md mục 7.
CLASS_MAP = {
    "G05": "swipe_left",    # Throw left
    "G06": "swipe_right",   # Throw right
    "G10": "zoom_in",       # Zoom in
    "G11": "zoom_out",      # Zoom out
    "D0X": "none",          # Non-gesture
    "B0A": "none",          # Pointing with one finger
    "B0B": "none",          # Pointing with two fingers
    "G01": "none",          # Click with one finger
    "G02": "none",          # Click with two fingers
    "G03": "none",          # Throw up      — mẫu âm khó: vuốt dọc
    "G04": "none",          # Throw down    — mẫu âm khó: vuốt dọc
    "G07": "none",          # Open twice    — mẫu âm khó nhất cho zoom_in
    "G08": "none",          # Double click with one finger
    "G09": "none",          # Double click with two fingers
}

ANNOT_COLUMNS = ["video", "label", "id", "t_start", "t_end", "frames"]


def map_label(label):
    """Nhãn gốc → tên lớp của đề tài.

    Raises:
        KeyError: nhãn không có trong bảng. Thà dừng còn hơn âm thầm bỏ một lớp.
    """
    if label not in CLASS_MAP:
        raise KeyError(
            f"Nhãn IPN '{label}' không có trong CLASS_MAP. Kiểm tra lại "
            "classIdx.txt và docs/ipn_format.md."
        )
    return CLASS_MAP[label]


def class_id(label):
    """Nhãn gốc → chỉ số lớp trong ``config.CLASSES``."""
    return config.CLASSES.index(map_label(label))


def subject_of(video):
    """Mã người diễn suy từ tên video, ví dụ ``1CM1_1_R__217`` → ``1CM1_1``."""
    return "_".join(video.split("_")[:config.IPN_SUBJECT_TOKENS])


def read_class_index(path=None):
    """``classIdx.txt`` → dict ``{nhãn: id}``.

    Raises:
        KeyError: file nhãn có lớp mà ``CLASS_MAP`` chưa phủ.
    """
    path = Path(path or config.IPN_CLASS_IDX)
    with open(path, newline="", encoding="utf-8-sig") as f:
        index = {r["label"]: int(r["id"]) for r in csv.DictReader(f)}

    missing = sorted(set(index) - set(CLASS_MAP))
    if missing:
        raise KeyError(f"{path} có lớp chưa nằm trong CLASS_MAP: {missing}")
    return index


def read_annotations(path=None):
    """``Annot_List.txt`` → dict ``{video: [đoạn, ...]}``.

    Mỗi đoạn là dict ``{label, start, end}`` với ``start``/``end`` đã đổi sang
    chỉ số Python 0-based, nửa mở.
    """
    path = Path(path or config.IPN_ANNOT_LIST)
    clips = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            clips.setdefault(row["video"], []).append({
                "label": row["label"],
                "start": int(row["t_start"]) - 1,
                "end": int(row["t_end"]),
            })
    for segments in clips.values():
        segments.sort(key=lambda s: s["start"])
    return clips


def segments_array(segments, n_frames=None):
    """Danh sách đoạn → ``(segments (M, 3) int64, src_labels (M,) <U32)``.

    Đoạn bị cắt cho vừa ``n_frames`` nếu nhãn vượt quá số frame giải mã được;
    đoạn nằm hoàn toàn ngoài phạm vi bị bỏ.
    """
    rows, labels = [], []
    for s in segments:
        start, end = s["start"], s["end"]
        if n_frames is not None:
            start, end = min(start, n_frames), min(end, n_frames)
        if end <= start:
            continue
        rows.append((start, end, class_id(s["label"])))
        labels.append(s["label"])

    return (np.array(rows, dtype=np.int64).reshape(-1, 3),
            np.array(labels, dtype="<U32"))


def read_video_lists(train_path=None, test_path=None):
    """Split chính thức → dict ``{video: "train" | "test"}``.

    Hai file có hai cột phân tách bằng TAB và không có dòng tiêu đề; cột thứ
    hai là số frame theo nhà cung cấp dữ liệu.
    """
    splits = {}
    for path, name in ((train_path or config.IPN_VIDEO_TRAIN_LIST, "train"),
                       (test_path or config.IPN_VIDEO_TEST_LIST, "test")):
        for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                splits[line.split()[0]] = name
    return splits


def read_metadata(path=None):
    """``metadata.csv`` → dict ``{video: {frames, set, ...}}``."""
    path = Path(path or config.IPN_METADATA_CSV)
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {r["Video Name"]: r for r in csv.DictReader(f)
                if r.get("Video Name")}


def clip_meta(video, w, h, fps, n_frames, expected_frames=None, split=None):
    """Dict ``meta`` để lưu vào ``.npz``.

    ``length_mismatch`` bật khi số frame giải mã được lệch quá
    ``IPN_LENGTH_TOLERANCE`` so với số frame nhà cung cấp khai báo. Xem
    ``docs/ipn_format.md`` mục 6: với 15 video như vậy, chưa xác định được
    frame thừa nằm ở đầu hay cuối, nên nhãn của chúng có thể lệch. Cờ này để
    các bước sau lọc ra, thay vì âm thầm dùng.
    """
    meta = {
        "w": int(w), "h": int(h), "fps": float(fps),
        "source": "ipn", "clip_id": video, "subject": subject_of(video),
        "n_frames": int(n_frames),
    }
    if split is not None:
        meta["official_split"] = split
    if expected_frames is not None:
        meta["expected_frames"] = int(expected_frames)
        meta["length_mismatch"] = (
            abs(int(n_frames) - int(expected_frames))
            > config.IPN_LENGTH_TOLERANCE
        )
    return meta
