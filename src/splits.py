"""Chia tập theo NGƯỜI — Phase 4 (luật 8).

``splits.json`` chỉ chứa danh sách mã người. Chia tập là một phép LỌC theo cột
``subject`` của bộ cửa sổ, không bao giờ là một phép chia ngẫu nhiên trên cửa
sổ: các cửa sổ liền nhau chồng lấn gần hết, chia ngẫu nhiên thì mô hình chỉ cần
nhớ chứ không cần học.

- ``test``: đúng split test chính thức của IPN, để so được với công bố khác.
- ``val``: một nhóm người tách ra từ split train chính thức, chọn ngẫu nhiên
  có seed.
- ``real_tune``, ``real_test``: để trống tới Phase 11.
"""

import json

import numpy as np

from src import config, ipn

SPLIT_NAMES = ("train", "val", "test", "real_tune", "real_test")


def official_subject_splits(video_splits=None):
    """Split chính thức theo NGƯỜI: ``{subject: "train" | "test"}``.

    Raises:
        ValueError: một người có video ở cả train lẫn test.
    """
    video_splits = video_splits or ipn.read_video_lists()
    subjects = {}
    for video, split in video_splits.items():
        subject = ipn.subject_of(video)
        if subjects.setdefault(subject, split) != split:
            raise ValueError(f"Người {subject} có video ở cả train lẫn test")
    return subjects


def make_splits(subject_splits, val_fraction=config.VAL_FRACTION,
                seed=config.SEED):
    """Dựng dict ``splits`` từ split chính thức theo người.

    ``val`` gồm ``round(val_fraction * số người train)`` người của split train,
    chọn ngẫu nhiên với ``seed``; phần còn lại là ``train``.
    """
    train = sorted(s for s, v in subject_splits.items() if v == "train")
    test = sorted(s for s, v in subject_splits.items() if v == "test")

    rng = np.random.default_rng(seed)
    n_val = round(val_fraction * len(train))
    val = sorted(rng.choice(train, size=n_val, replace=False).tolist())
    train = [s for s in train if s not in set(val)]

    splits = {"train": train, "val": val, "test": test,
              "real_tune": [], "real_test": []}
    check_disjoint(splits)
    return splits


def check_disjoint(splits):
    """Không người nào ở hai tập.

    Returns:
        Tập các người bị trùng — rỗng nếu hợp lệ.

    Raises:
        ValueError: có người nằm ở hai tập trở lên.
    """
    seen, overlap = {}, set()
    for name in SPLIT_NAMES:
        for subject in splits.get(name, []):
            if subject in seen:
                overlap.add(subject)
            seen[subject] = name
    if overlap:
        raise ValueError(f"Người nằm ở hai tập: {sorted(overlap)}")
    return overlap


def write_splits(splits, path=None):
    path = path or config.SPLITS_JSON
    check_disjoint(splits)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(splits, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path


def read_splits(path=None):
    """Đọc ``splits.json``.

    Raises:
        FileNotFoundError: chưa chạy ``scripts/make_splits.py``.
    """
    path = path or config.SPLITS_JSON
    if not path.is_file():
        raise FileNotFoundError(
            f"Chưa có {path.name}. Chạy python scripts/make_splits.py trước.")
    splits = json.loads(path.read_text(encoding="utf-8"))
    check_disjoint(splits)
    return splits


def split_of(subjects, splits):
    """``(N,)`` tên tập của từng người; ``""`` nếu người đó không ở tập nào."""
    lookup = {s: name for name in SPLIT_NAMES for s in splits.get(name, [])}
    return np.array([lookup.get(str(s), "") for s in subjects], dtype="<U16")
