"""Hình vẽ dùng chung cho các phase. Hình báo cáo dùng màu trong config (FIG_*)."""

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


def _report_axes(ax):
    """Trục kiểu báo cáo: lưới mảnh và lùi về sau, chữ màu mực phụ."""
    ax.set_facecolor(config.FIG_SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(config.FIG_AXIS)
    ax.tick_params(colors=config.FIG_INK_2, labelsize=8)
    ax.set_axisbelow(True)


def plot_importances(names, impurity, perm_mean, perm_std, highlight, out_path):
    """Hai bảng xếp hạng độ quan trọng đặt cạnh nhau.

    Hàng xếp theo độ quan trọng hoán vị (lớn nhất ở trên) ở CẢ HAI ô, để mắt
    so được cùng một đặc trưng giữa hai cách đo. Đặc trưng trong ``highlight``
    (dự đoán quan trọng) tô màu nhấn, phần còn lại màu xám.
    """
    names = list(names)
    order = np.argsort(perm_mean)
    rows = np.arange(len(names))
    colors = [config.FIG_ACCENT if names[i] in highlight else config.FIG_DEEMPH
              for i in order]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5.5), sharey=True,
                             facecolor=config.FIG_SURFACE)
    axes[0].barh(rows, np.asarray(impurity)[order], height=0.5, color=colors)
    axes[1].barh(rows, np.asarray(perm_mean)[order], height=0.5, color=colors,
                 xerr=np.asarray(perm_std)[order],
                 error_kw={"ecolor": config.FIG_INK_2, "elinewidth": 1,
                           "capsize": 2})
    axes[0].set_yticks(rows, [names[i] for i in order])
    titles = ("Theo tạp chất Gini (feature_importances_, train)",
              "Theo hoán vị trên val (macro-F1 giảm, ±1 độ lệch chuẩn)")
    for ax, title in zip(axes, titles):
        _report_axes(ax)
        ax.xaxis.grid(True, color=config.FIG_GRID, linewidth=0.8)
        ax.axvline(0.0, color=config.FIG_AXIS, linewidth=1)
        ax.set_title(title, fontsize=9, color=config.FIG_INK)
    handles = [plt.Rectangle((0, 0), 1, 1, color=config.FIG_ACCENT),
               plt.Rectangle((0, 0), 1, 1, color=config.FIG_DEEMPH)]
    fig.legend(handles, ["dự đoán quan trọng (cổng Phase 4)", "đặc trưng khác"],
               loc="lower center", ncol=2, frameon=False, fontsize=8,
               labelcolor=config.FIG_INK_2)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(out_path, dpi=config.FIG_DPI, facecolor=config.FIG_SURFACE)
    plt.close(fig)
    return out_path


def plot_training_curves(history, best_epoch, out_path, title=""):
    """Đường học của LSTM: loss (trái) và macro-F1 (phải) theo epoch, train và
    val trên CÙNG một khung — hai đại lượng khác thang đo nên tách hai khung,
    không dùng hai trục dọc.

    Cả hai đường đo cùng một cách (chế độ eval, không tăng cường), nên khoảng
    hở giữa chúng là quá khớp. Val tô màu nhấn vì nó là thứ quyết định; vạch dọc
    đánh dấu epoch có macro-F1 val cao nhất — checkpoint được lưu.

    Args:
        history: list dict có ``epoch``, ``train_loss``, ``val_loss``,
            ``train_macro_f1``, ``val_macro_f1``.
    """
    epochs = np.array([r["epoch"] for r in history])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), facecolor=config.FIG_SURFACE)
    panels = ((axes[0], "loss", "Loss (CrossEntropy có trọng số lớp)"),
              (axes[1], "macro_f1", "macro-F1"))
    for ax, key, subtitle in panels:
        _report_axes(ax)
        ax.yaxis.grid(True, color=config.FIG_GRID, linewidth=0.8)
        for split, color, z in (("train", config.FIG_DEEMPH, 2),
                                ("val", config.FIG_ACCENT, 3)):
            values = np.array([r[f"{split}_{key}"] for r in history])
            ax.plot(epochs, values, color=color, linewidth=1.0, zorder=z,
                    label=split)
            ax.annotate(split, (epochs[-1], values[-1]), xytext=(4, 0),
                        textcoords="offset points", va="center", fontsize=8,
                        color=config.FIG_INK_2)
        best = next(r for r in history if r["epoch"] == best_epoch)
        ax.axvline(best_epoch, color=config.FIG_INK_2, linewidth=0.8,
                   linestyle=(0, (3, 3)), zorder=1)
        ax.plot([best_epoch], [best[f"val_{key}"]], marker="o", markersize=5,
                color=config.FIG_ACCENT, markeredgecolor=config.FIG_SURFACE,
                markeredgewidth=1.0, zorder=4)
        ax.set_xlabel("epoch", color=config.FIG_INK_2, fontsize=9)
        ax.set_title(subtitle, fontsize=9, color=config.FIG_INK)
        ax.set_xlim(epochs[0], epochs[-1] + max(1, len(epochs) // 8))
    # Chú giải và chú thích vạch dọc đặt ngoài hai khung: trong khung, chúng đè
    # lên đường cong khi epoch tốt nhất nằm sát mép phải.
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=2,
               frameon=False, fontsize=8, labelcolor=config.FIG_INK_2)
    note = f"vạch đứng và chấm: epoch {best_epoch}, macro-F1 val cao nhất"
    fig.suptitle(f"{title}\n{note}" if title else note, fontsize=10,
                 color=config.FIG_INK)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out_path, dpi=config.FIG_DPI, facecolor=config.FIG_SURFACE)
    plt.close(fig)
    return out_path


def plot_confusion(cm, cm_row, classes, out_path, title=""):
    """Ma trận nhầm lẫn thô (trái) và chuẩn hoá theo hàng (phải).

    Cả hai ô tô màu theo TỈ LỆ HÀNG: tô theo số đếm thô thì lớp ``none`` (hàng
    vạn cửa sổ) nuốt hết thang màu và mọi ô khác trông như nhau. Ô trái ghi số
    cửa sổ, ô phải ghi phần trăm.
    """
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list("seq", config.FIG_SEQ_RAMP)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), facecolor=config.FIG_SURFACE)
    panels = ((axes[0], lambda i, j: f"{int(cm[i, j]):,}", "Số cửa sổ"),
              (axes[1], lambda i, j: f"{cm_row[i, j]:.0%}", "Chuẩn hoá theo hàng"))
    for ax, text, subtitle in panels:
        image = ax.imshow(cm_row, cmap=cmap, vmin=0.0, vmax=1.0)
        for i in range(len(classes)):
            for j in range(len(classes)):
                dark = cm_row[i, j] >= config.FIG_SEQ_DARK_TEXT_BELOW
                ax.text(j, i, text(i, j), ha="center", va="center", fontsize=8,
                        color="white" if dark else config.FIG_INK)
        ax.set_xticks(range(len(classes)), classes, rotation=30, ha="right")
        ax.set_yticks(range(len(classes)), classes)
        ax.set_xlabel("lớp đoán", color=config.FIG_INK_2, fontsize=9)
        if ax is axes[0]:       # hai ô chung trục dọc: chỉ ghi nhãn một lần
            ax.set_ylabel("lớp thật", color=config.FIG_INK_2, fontsize=9)
        ax.set_title(subtitle, fontsize=9, color=config.FIG_INK)
        ax.tick_params(colors=config.FIG_INK_2, labelsize=8, length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
    bar = fig.colorbar(image, ax=axes, fraction=0.025, pad=0.02)
    bar.ax.tick_params(colors=config.FIG_INK_2, labelsize=8)
    bar.outline.set_visible(False)
    if title:
        fig.suptitle(title, fontsize=10, color=config.FIG_INK)
    fig.savefig(out_path, dpi=config.FIG_DPI, facecolor=config.FIG_SURFACE,
                bbox_inches="tight")
    plt.close(fig)
    return out_path
