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


def equal_quota(available, budget):
    """Chia ``budget`` đều cho các nhóm, không nhóm nào vượt số nó có.

    Nhóm nhỏ hơn phần chia thì lấy hết; phần dư dồn đều cho các nhóm còn lại.
    Phần lẻ cuối cùng đi cho các nhóm lớn nhất. Tổng quota bằng
    ``min(budget, tổng số có)``.
    """
    quota = {k: 0 for k in available}
    remaining = min(int(budget), sum(available.values()))
    open_groups = sorted(available, key=lambda k: (available[k], k))
    while open_groups and remaining > 0:
        share = remaining // len(open_groups)
        smallest = open_groups[0]
        if available[smallest] <= share:
            quota[smallest] = available[smallest]
            remaining -= available[smallest]
            open_groups.pop(0)
            continue
        for k in open_groups:
            quota[k] = share
        remaining -= share * len(open_groups)
        for k in reversed(open_groups[-remaining:] if remaining else []):
            quota[k] += 1
        remaining = 0
    return quota


def proportional_quota(available, budget):
    """Chia ``budget`` theo tỉ lệ tự nhiên của các nhóm — phần nguyên trước,
    phần lẻ cho các nhóm có phần dư lớn nhất. Tổng bằng ``min(budget, tổng)``.

    Chỉ dùng ở bảng phụ của Phase 8, để thử giả thuyết B của Phase 6: quota
    chia đều cho tay chỉ trỏ (``B0A``, ``B0B``) quá ít so với tỉ lệ của nó
    trong val (``results/phase6/notes.md`` mục 4.1).
    """
    total = sum(available.values())
    budget = min(int(budget), total)
    if total == 0:
        return {k: 0 for k in available}
    exact = {k: budget * v / total for k, v in available.items()}
    quota = {k: int(np.floor(x)) for k, x in exact.items()}
    by_remainder = sorted(available, key=lambda k: (-(exact[k] - quota[k]), k))
    for k in by_remainder[:budget - sum(quota.values())]:
        quota[k] += 1
    return quota


def subsample_none(y, src_label, split, rng, share=config.NONE_TRAIN_SHARE,
                   quota_fn=equal_quota):
    """Mặt nạ giữ lại: mọi cửa sổ dương, mọi cửa sổ ngoài train, và một phần
    lớp none của train theo ``quota_fn`` trên ``src_label``.

    ``none`` của train còn ``share`` phần tập train — KHÔNG BAO GIỜ cân bằng
    1:1. Quota mặc định chia ĐỀU theo nhãn gốc (quyết định 2026-10-05).

    Returns:
        ``(keep (N,) bool, quota dict)``.
    """
    keep = np.ones(y.size, dtype=bool)
    in_train = split == "train"
    n_pos = int(np.sum((y != 0) & in_train))
    budget = int(np.floor(n_pos * share / (1.0 - share)))

    none_idx = np.flatnonzero((y == 0) & in_train)
    groups = {str(k): none_idx[src_label[none_idx] == k]
              for k in np.unique(src_label[none_idx])}
    quota = quota_fn({k: v.size for k, v in groups.items()}, budget)

    keep[none_idx] = False
    for k, idx in groups.items():
        keep[rng.choice(idx, size=quota[k], replace=False)] = True
    return keep, quota


def subject_folds(subjects, k, seed=config.SEED):
    """Chia NGƯỜI thành ``k`` nhóm gần bằng nhau cho k-fold (Phase 8, Bảng 7):
    xáo danh sách người với ``seed`` rồi chia vòng.

    Returns:
        list ``k`` danh sách mã người, rời nhau, hợp lại đủ ``subjects``.

    Raises:
        ValueError: ít người hơn ``k``.
    """
    subjects = sorted(set(map(str, subjects)))
    if len(subjects) < k:
        raise ValueError(f"Cần ít nhất {k} người cho {k}-fold, có {len(subjects)}")
    order = np.random.default_rng(seed).permutation(len(subjects))
    return [sorted(subjects[i] for i in order[f::k]) for f in range(k)]
