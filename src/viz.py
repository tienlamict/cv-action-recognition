"""Hình vẽ dùng chung. Phase 3 và Phase 5 dùng lại các hàm ở đây."""

import math

import matplotlib

matplotlib.use("Agg")   # không cần màn hình; script chạy được cả khi không có GUI

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from src import config  # noqa: E402


def plot_boxplots(F, y, names, out_path, classes=None):
    """Boxplot từng đặc trưng theo từng lớp — mỗi đặc trưng một ô.

    Đây là cổng kiểm tra của Phase 5: nhìn ba hình ``open_delta``, ``dx`` và
    ``straightness`` là biết thiết kế đặc trưng có tách lớp hay không, trước
    khi huấn luyện bất kỳ mô hình nào.

    Args:
        F: ``(N, D)`` ma trận đặc trưng.
        y: ``(N,)`` chỉ số lớp trong ``classes``.
        names: ``D`` tên đặc trưng.
        out_path: file ``.png`` để ghi.
        classes: danh sách tên lớp; mặc định ``config.CLASSES``.

    Returns:
        Đường dẫn đã ghi.
    """
    F = np.asarray(F, dtype=np.float64)
    y = np.asarray(y)
    classes = list(classes if classes is not None else config.CLASSES)

    n_cols = 3
    n_rows = math.ceil(len(names) / n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 3 * n_rows))
    axes = np.atleast_1d(axes).ravel()

    for ax, column, name in zip(axes, F.T, names):
        data = [column[y == k] for k in range(len(classes))]
        ax.boxplot([d[np.isfinite(d)] for d in data], tick_labels=classes)
        ax.set_title(name)
        ax.tick_params(axis="x", labelrotation=45, labelsize=8)
        ax.axhline(0.0, linewidth=0.8, alpha=0.4)

    for ax in axes[len(names):]:
        ax.set_visible(False)

    fig.tight_layout()
    fig.savefig(out_path, dpi=config.FIG_DPI)
    plt.close(fig)
    return out_path
