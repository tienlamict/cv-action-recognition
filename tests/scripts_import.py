"""Nạp một script trong scripts/ thành module để kiểm thử.

Thư mục ``scripts/`` không phải package, nên không ``import`` thẳng được. Hàm
này nạp theo đường dẫn; phần ``if __name__ == "__main__"`` không chạy.
"""

import importlib.util
import sys

from src import config


def load_script(name):
    path = config.SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_script_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
