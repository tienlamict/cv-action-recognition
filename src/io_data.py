"""Đọc và ghi dữ liệu điểm mốc trên đĩa: CSV (webcam) và ``.npz`` (clip).

Đây là lớp mỏng trên ``recording.read_frames_csv`` — nơi biết định dạng CSV của
``scripts/record_csv.py``. Không đọc CSV theo cách nào khác ở chỗ nào khác.

:func:`load_clip` là **chỗ duy nhất trong toàn repo áp dụng ``IPN_FLIP_X``**.
Quy ước hướng phải nằm đúng một chỗ, nếu không sẽ có lúc lật hai lần và không
gì báo lỗi. Có kiểm thử đọc mã nguồn để canh luật đó.
"""

import json

import numpy as np

from src import config
from src.recording import read_frames_csv


def read_record_csv(path):
    """Đọc một CSV điểm mốc.

    Args:
        path: đường dẫn tới ``landmarks.csv``.

    Returns:
        ``(ts, xy_norm, present, w, h)``:

        - ``ts`` float64 ``(N,)`` — giây
        - ``xy_norm`` float32 ``(N, 21, 2)`` — toạ độ chuẩn hoá ``[0, 1]``,
          NaN ở dòng mất tay
        - ``present`` bool ``(N,)``
        - ``w``, ``h`` int — kích thước khung hình

    Raises:
        ValueError: file rỗng, hoặc kích thước khung đổi giữa chừng (hai nguồn
            bị trộn vào một file).
    """
    data = read_frames_csv(path)
    if data["ts"].size == 0:
        raise ValueError(f"{path} không có dòng dữ liệu nào")

    sizes = {(int(w), int(h)) for w, h in zip(data["w"], data["h"])}
    if len(sizes) > 1:
        raise ValueError(f"{path} chứa nhiều kích thước khung hình: {sizes}")
    w, h = sizes.pop()

    return (np.asarray(data["ts"], dtype=np.float64), data["xy"],
            data["present"], w, h)


def save_clip(path, ts, xy_norm, present, segments, src_labels, meta):
    """Lưu điểm mốc của một clip theo schema ở mục Hợp đồng dữ liệu.

    Args:
        path: file ``.npz`` để ghi.
        ts: ``(N,)`` giây, tăng dần, ``ts[0] = 0``.
        xy_norm: ``(N, 21, 2)`` toạ độ CHUẨN HOÁ ``[0, 1]`` của MediaPipe, NaN
            khi mất tay. Không lưu bản đã ``normalize_window`` — chuẩn hoá là
            quyết định thiết kế có thể đổi, còn điểm mốc thô thì không.
        present: ``(N,)`` bool.
        segments: ``(M, 3)`` ``[start_idx, end_idx, class_id]``, chỉ số 0-based
            và ``end_idx`` **không thuộc** đoạn (như lát cắt Python).
        src_labels: ``(M,)`` nhãn gốc của nguồn, trước khi ánh xạ về 5 lớp.
        meta: dict có ``w``, ``h``, ``fps``, ``source``, ``subject``,
            ``clip_id``; ``flip_applied`` do :func:`load_clip` điền.
    """
    ts = np.asarray(ts, dtype=np.float64)
    xy_norm = np.asarray(xy_norm, dtype=np.float32)
    segments = np.asarray(segments, dtype=np.int64).reshape(-1, 3)

    if xy_norm.shape != (ts.size, config.NUM_LANDMARKS, 2):
        raise ValueError(f"xy phải là {(ts.size, config.NUM_LANDMARKS, 2)}, "
                         f"đang là {xy_norm.shape}")
    if segments.shape[0] != len(src_labels):
        raise ValueError("segments và src_labels phải cùng số dòng")

    path = str(path)
    np.savez_compressed(
        path,
        xy=xy_norm,
        ts=ts,
        present=np.asarray(present, dtype=bool),
        segments=segments,
        src_labels=np.asarray(src_labels, dtype="<U32"),
        meta=json.dumps(meta, ensure_ascii=False),
    )
    return path


def load_clip(path):
    """Nạp một clip đã lưu.

    Đây là **chỗ duy nhất** áp dụng ``config.IPN_FLIP_X``: khi clip có nguồn
    ``ipn`` và cờ bằng ``-1``, toạ độ ``x`` được đổi thành ``1 - x`` ngay lúc
    nạp, và ``meta["flip_applied"]`` ghi lại việc đó. Nhờ vậy mọi phần còn lại
    của hệ thống không bao giờ phải biết tới quy ước hướng của nguồn.

    Returns:
        ``(ts, xy_norm, w, h, segments, src_labels, meta)`` — ``xy_norm`` vẫn
        là toạ độ chuẩn hoá ``[0, 1]``; đổi sang pixel là việc của
        ``preprocess.load_sequence``.
    """
    with np.load(path, allow_pickle=False) as data:
        ts = data["ts"]
        xy_norm = data["xy"]
        segments = data["segments"]
        src_labels = data["src_labels"]
        meta = json.loads(str(data["meta"]))

    flip = meta.get("source") == "ipn" and config.IPN_FLIP_X == -1
    if flip:
        xy_norm = xy_norm.copy()
        xy_norm[..., 0] = 1.0 - xy_norm[..., 0]
    meta["flip_applied"] = bool(flip)

    return (ts, xy_norm, int(meta["w"]), int(meta["h"]), segments,
            src_labels, meta)
