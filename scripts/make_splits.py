"""Dựng data/splits.json theo NGƯỜI từ split chính thức của IPN.

- test: đúng split test chính thức.
- val: VAL_FRACTION số người của split train chính thức, chọn với SEED.
- train: phần còn lại.
- real_tune, real_test: để trống tới Phase 11.

In phép giao giữa các tập — phải là tập rỗng.

Ví dụ:
    python scripts/make_splits.py
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import (SPLIT_NAMES, make_splits,  # noqa: E402
                        official_subject_splits, write_splits)


def session_of(subject):
    """Nhóm quay — token đầu của mã người, ví dụ ``1CM42_13`` → ``1CM42``."""
    return subject.split("_")[0]


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.parse_args()

    splits = make_splits(official_subject_splits())
    path = write_splits(splits)

    for name in SPLIT_NAMES:
        sessions = Counter(session_of(s) for s in splits[name])
        print(f"{name:<10} {len(splits[name]):>3} người  {dict(sorted(sessions.items()))}")

    sets = {name: set(splits[name]) for name in SPLIT_NAMES}
    print("\nPhép giao giữa các tập (phải rỗng):")
    for i, a in enumerate(SPLIT_NAMES):
        for b in SPLIT_NAMES[i + 1:]:
            print(f"  {a} ∩ {b} = {sorted(sets[a] & sets[b])}")

    run_dir = next_run_dir(config.PHASE4_RESULTS_DIR / "splits")
    write_manifest(run_dir, {"script": "make_splits", "splits": splits})
    print(f"\nĐã ghi {relative_to_root(path)}")


if __name__ == "__main__":
    main()
