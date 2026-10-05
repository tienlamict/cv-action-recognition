"""Hình vẽ dùng chung. Phase 3 và Phase 5 dùng lại các hàm ở đây."""

import math

import matplotlib

matplotlib.use("Agg")   # không cần màn hình; script chạy được cả khi không có GUI

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from src import config  # noqa: E402


def plot_window_traces(windows, titles, traces, out_path):
    """Mỗi cửa sổ một cột: quỹ đạo cổ tay (trên) và các đường theo thời gian
    (dưới), ví dụ độ xòe và độ mở cái–trỏ.

    Args:
        windows: list các cửa sổ ``(T, 21, 2)`` ĐÃ chuẩn hoá.
        titles: tiêu đề mỗi cột.
        traces: dict ``{tên: hàm (T, 21, 2) → (T,)}`` — ví dụ
            ``{"độ xòe": features.openness, "cái–trỏ": features.pinch}``.
        out_path: file ``.png``.

    Trục ``y`` hướng XUỐNG như ảnh gốc, và ảnh KHÔNG lật: ``x`` dương là sang
    phải ảnh gốc, tức sang trái của người làm.
    """
    n = len(windows)
    fig, axes = plt.subplots(2, n, figsize=(3.2 * n, 6.0), squeeze=False)
    for col, (win, title) in enumerate(zip(windows, titles)):
        wrist = np.asarray(win)[:, config.WRIST]
        ax = axes[0, col]
        ax.plot(wrist[:, 0], wrist[:, 1], marker=".")
        ax.plot(wrist[0, 0], wrist[0, 1], "go", label="đầu")
        ax.plot(wrist[-1, 0], wrist[-1, 1], "rs", label="cuối")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("x (lòng bàn tay)")
        ax.set_ylabel("y (xuống)")
        ax.invert_yaxis()
        ax.set_aspect("equal", adjustable="datalim")
        ax.legend(fontsize=7)
        ax = axes[1, col]
        seconds = np.arange(len(win)) / config.HZ
        for name, trace in traces.items():
            ax.plot(seconds, trace(win), marker=".", label=name)
        ax.set_xlabel("giây")
        ax.set_ylabel("lòng bàn tay")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out_path, dpi=config.FIG_DPI)
    plt.close(fig)
    return out_path


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
