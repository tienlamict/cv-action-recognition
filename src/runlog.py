"""Thư mục kết quả và ``manifest.json`` cho mỗi lần chạy.

Mỗi lần chạy ghi vào ``results/<phase>/<tên>/run_NN/`` kèm ``manifest.json``
chứa dòng lệnh đầy đủ, thời điểm chạy, seed, phiên bản thư viện và bản sao các
hằng số của ``config.py``. Nhờ đó mọi con số trong báo cáo đều truy ngược được
về đúng lệnh đã sinh ra nó.
"""

import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from src import config

_RUN_PREFIX = "run_"


def next_run_dir(base):
    """Tạo và trả về ``base/run_NN`` với NN là số kế tiếp chưa dùng."""
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    used = [
        int(p.name[len(_RUN_PREFIX):])
        for p in base.glob(f"{_RUN_PREFIX}*")
        if p.is_dir() and p.name[len(_RUN_PREFIX):].isdigit()
    ]
    run_dir = base / f"{_RUN_PREFIX}{max(used, default=0) + 1:02d}"
    run_dir.mkdir()
    return run_dir


def config_snapshot():
    """Mọi hằng số VIẾT HOA của ``config.py``, ở dạng ghi được ra JSON.

    Đường dẫn được ghi tương đối so với ``ROOT`` để manifest không chứa đường
    dẫn tuyệt đối của máy đo.
    """
    snapshot = {}
    for name, value in vars(config).items():
        if not name.isupper():
            continue
        if isinstance(value, Path):
            value = (value.relative_to(config.ROOT).as_posix()
                     if value != config.ROOT else ".")
        elif isinstance(value, tuple):
            value = list(value)
        snapshot[name] = value
    return snapshot


def _library_versions():
    versions = {"python": platform.python_version()}
    for module in ("numpy", "cv2", "mediapipe"):
        try:
            versions[module] = __import__(module).__version__
        except ImportError:
            versions[module] = None
    return versions


def write_manifest(run_dir, extra=None):
    """Ghi ``manifest.json`` vào ``run_dir`` và trả về đường dẫn của nó."""
    manifest = {
        "command": subprocess.list2cmdline(["python", *sys.argv]),
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "seed": config.SEED,
        "versions": _library_versions(),
        "config": config_snapshot(),
    }
    if extra:
        manifest.update(extra)
    path = Path(run_dir) / config.MANIFEST_NAME
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2,
                               default=_jsonable), encoding="utf-8")
    return path


def _jsonable(value):
    """Số và mảng của numpy không ghi thẳng ra JSON được."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return relative_to_root(value)
    raise TypeError(f"Không ghi ra JSON được: {type(value).__name__}")


def relative_to_root(path):
    """Đường dẫn để in cho người đọc — tương đối so với ROOT khi có thể."""
    path = Path(path).resolve()
    try:
        return path.relative_to(config.ROOT).as_posix()
    except ValueError:
        return str(path)
