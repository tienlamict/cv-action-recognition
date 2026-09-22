"""Tiện ích dùng chung cho các script trong scripts/."""

import argparse
import sys

from src import config


def setup_console():
    """In được tiếng Việt kể cả khi stdout bị chuyển hướng vào file hay pipe.

    Trên Windows, stdout chuyển hướng dùng mã cp1252 và sập ngay ở ký tự có
    dấu đầu tiên.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def parse_source(value):
    """``"0"`` → webcam số 0; mọi chuỗi khác → đường dẫn file video."""
    return int(value) if value.isdigit() else value


def add_source_arg(parser):
    parser.add_argument(
        "--source", type=parse_source, default=config.CAM_INDEX,
        help="chỉ số webcam (mặc định %(default)s) hoặc đường dẫn file video",
    )


def make_parser(description):
    return argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
