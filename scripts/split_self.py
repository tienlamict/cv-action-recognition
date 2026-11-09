"""Chia dữ liệu tự quay thành real_tune và real_test (Phase 11, bước 3; luật 15).

Đơn vị chia là một NGƯỜI TRONG MỘT BUỔI, mã ``người/buổi`` (selfdata.session_key),
ví dụ ``p01/2026-11-06``. p01 có buổi ở cả hai phía, quay khác ngày; người khác chỉ
ở một phía.

``--test`` liệt kê các người–buổi để CHẤM. Mọi người–buổi còn lại có trong
``data/raw`` là ``real_tune``. Script ghi vào ``splits.json`` trước khi phân tích
buổi chấm, và từ chối ghi đè khi ``real_tune`` hay ``real_test`` đã có dữ liệu: chia
lại sau khi đã nhìn dữ liệu là phạm luật 15.

Ví dụ:
    python scripts/split_self.py --test p01/p01-test
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config, selfdata  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.runlog import relative_to_root  # noqa: E402
from src.splits import check_self_split, read_splits, write_splits  # noqa: E402


def plan(keys, test):
    """``{"real_tune": [...], "real_test": [...]}`` từ các người–buổi đang có.

    Raises:
        ValueError: một người–buổi trong ``test`` không có trong ``keys``.
    """
    unknown = sorted(set(test) - set(keys))
    if unknown:
        raise ValueError(f"Không có người–buổi nào tên {unknown} — có: {sorted(keys)}")
    part = {"real_tune": sorted(set(keys) - set(test)), "real_test": sorted(set(test))}
    check_self_split(part)
    return part


def main(argv=None):
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--test", nargs="+", required=True,
                        help="các người–buổi để chấm, dạng người/buổi")
    parser.add_argument("--raw", default=None, help="thư mục dữ liệu thô (mặc định data/raw)")
    args = parser.parse_args(argv)

    splits = read_splits()
    if splits.get("real_tune") or splits.get("real_test"):
        raise SystemExit(f"{config.SPLITS_JSON.name} đã có real_tune/real_test — không ghi "
                         "đè (luật 15: chia một lần, trước khi nhìn dữ liệu chấm).")
    found = selfdata.sessions(args.raw)
    try:
        part = plan(found, args.test)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    if not part["real_tune"]:
        raise SystemExit("Không còn người–buổi nào để học.")
    path = write_splits({**splits, **part})

    for name in ("real_tune", "real_test"):
        print(f"{name}:")
        for key in part[name]:
            print(f"  {key:<16} {len(found[key]):>4} lần quay")
    print(f"→ {relative_to_root(path)}")


if __name__ == "__main__":
    main()
