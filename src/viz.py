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


def trailing_mean(values, window):
    """Trung bình của tối đa ``window`` giá trị gần nhất, tính tới từng điểm — đúng
    cách ``training.EarlyStop`` nhìn lại các epoch đã qua. Vài điểm đầu lấy trung bình
    phần đã có."""
    values = np.asarray(values, dtype=np.float64)
    total = np.concatenate([[0.0], np.cumsum(values)])
    end = np.arange(1, len(values) + 1)
    start = np.maximum(end - window, 0)
    return (total[end] - total[start]) / (end - start)


def plot_training_curves(history, best_epoch, out_path, title="", smooth=None):
    """Đường học của LSTM: loss (trái) và macro-F1 mức cửa sổ (phải) theo epoch, tập
    học và kiểm định trên CÙNG một khung — hai đại lượng khác thang đo nên tách hai
    khung, không dùng hai trục dọc.

    Hai tập đo cùng một cách (chế độ eval, không tăng cường), nên khoảng hở giữa
    chúng là quá khớp. Kiểm định tô màu nhấn vì nó là thứ quyết định; vạch đứt đánh
    dấu epoch được chọn — checkpoint được lưu.

    Args:
        history: list dict có ``epoch``, ``train_loss``, ``val_loss``,
            ``train_macro_f1``, ``val_macro_f1``.
        smooth: số epoch của trung bình trượt mà dừng sớm dùng để chọn epoch
            (``window`` của ``train_lstm``). Lớn hơn 1 thì vẽ thêm đường kiểm định đã
            làm mượt — đường quyết định epoch được chọn — và đường thô nhạt đi.
    """
    smooth = smooth if smooth and smooth > 1 else None
    epochs = np.array([r["epoch"] for r in history])
    k = int(np.flatnonzero(epochs == best_epoch)[0])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), facecolor=config.FIG_SURFACE)
    raw_color = config.FIG_SEQ_RAMP[2] if smooth else config.FIG_ACCENT
    marks = {}
    for ax, key, subtitle in ((axes[0], "loss", "Loss"),
                              (axes[1], "macro_f1", "Macro-F1 mức cửa sổ")):
        _report_axes(ax)
        ax.yaxis.grid(True, color=config.FIG_GRID, linewidth=0.8)
        ax.plot(epochs, [r[f"train_{key}"] for r in history], color=config.FIG_DEEMPH,
                linewidth=1.0, zorder=2, label="tập học")
        values = np.array([r[f"val_{key}"] for r in history], dtype=np.float64)
        ax.plot(epochs, values, color=raw_color, linewidth=1.0, zorder=3,
                label="kiểm định")
        marks[key] = values
        if smooth:
            marks[key] = trailing_mean(values, smooth)
            ax.plot(epochs, marks[key], color=config.FIG_ACCENT, linewidth=2.0, zorder=4,
                    label=f"kiểm định, TB {smooth} epoch")
        ax.axvline(best_epoch, color=config.FIG_INK_2, linewidth=0.8,
                   linestyle=(0, (3, 3)), zorder=1, label=f"epoch {best_epoch} được chọn")
        ax.plot([best_epoch], [marks[key][k]], marker="o", markersize=5,
                color=config.FIG_ACCENT, markeredgecolor=config.FIG_SURFACE,
                markeredgewidth=1.0, zorder=5)
        # Tên vạch đặt ngay trên khung: trong khung nó đè lên đường tập học ở gần 1,0.
        ax.annotate(f"epoch {best_epoch}", (best_epoch, 1.0),
                    xycoords=("data", "axes fraction"), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8,
                    color=config.FIG_INK_2)
        ax.set_xlabel("epoch", color=config.FIG_INK_2, fontsize=9)
        ax.set_title(subtitle, fontsize=9, color=config.FIG_INK, pad=16)
        ax.set_xlim(0, epochs[-1] + 1)
    fig.legend(*axes[1].get_legend_handles_labels(), loc="lower center",
               ncol=4 if smooth else 3, frameon=False, fontsize=8,
               labelcolor=config.FIG_INK_2)
    f1 = marks["macro_f1"][k]
    raw = history[k]["val_macro_f1"]
    note = (f"epoch {best_epoch} được chọn: trung bình {smooth} epoch gần nhất của macro-F1 "
            f"kiểm định cao nhất ({f1:.3f}; điểm thô của epoch đó {raw:.3f})" if smooth
            else f"epoch {best_epoch} được chọn: macro-F1 kiểm định cao nhất ({raw:.3f})")
    fig.suptitle(f"{title}\n{note}" if title else note, fontsize=10,
                 color=config.FIG_INK)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out_path, dpi=config.FIG_DPI, facecolor=config.FIG_SURFACE)
    plt.close(fig)
    return out_path


def plot_per_class_f1(f1_by_model, classes, out_path, title=""):
    """F1 từng lớp của vài mô hình: mỗi lớp một nhóm cột, mỗi mô hình một màu.

    Màu đi theo mô hình (``FIG_CATEGORICAL`` theo thứ tự ``MODEL_NAMES``), nên
    hình của các bảng khác nhau tô cùng một mô hình bằng cùng một màu. Cột mỏng,
    cách nhau một khe màu nền; số liệu đầy đủ nằm ở bảng đi kèm.

    Args:
        f1_by_model: dict ``{tên mô hình: [F1 mỗi lớp]}`` — tên thuộc
            ``MODEL_NAMES``.
    """
    models = [m for m in config.MODEL_NAMES if m in f1_by_model]
    colors = dict(zip(config.MODEL_NAMES, config.FIG_CATEGORICAL))
    n = len(models)
    width = 0.8 / max(n, 1)
    fig, ax = plt.subplots(figsize=(10, 4.2), facecolor=config.FIG_SURFACE)
    _report_axes(ax)
    ax.yaxis.grid(True, color=config.FIG_GRID, linewidth=0.8)
    groups = np.arange(len(classes))
    for k, model in enumerate(models):
        ax.bar(groups - 0.4 + width * (k + 0.5), f1_by_model[model], width=width,
               color=colors[model], edgecolor=config.FIG_SURFACE, linewidth=1.5,
               label=model, zorder=3)
    ax.axhline(0.0, color=config.FIG_AXIS, linewidth=1, zorder=4)
    ax.set_xticks(groups, classes)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("F1", color=config.FIG_INK_2, fontsize=9)
    fig.legend(*ax.get_legend_handles_labels(), loc="lower center", ncol=n,
               frameon=False, fontsize=8, labelcolor=config.FIG_INK_2)
    if title:
        ax.set_title(title, fontsize=10, color=config.FIG_INK)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(out_path, dpi=config.FIG_DPI, facecolor=config.FIG_SURFACE)
    plt.close(fig)
    return out_path


def plot_sides(panels, sides, out_path, title="", note=""):
    """Vài bên (ví dụ mô hình cũ và mới) đặt cạnh nhau, mỗi khung một đại lượng.

    Mỗi nhóm có một cột cho mỗi bên: chiều cao là trung bình các hạt, vạch mảnh màu
    mực là thấp nhất–cao nhất. Số trung bình ghi trên đầu vạch, bằng màu mực. Khung
    nào có thang đo riêng thì đứng riêng, không dùng hai trục dọc.

    Args:
        panels: list dict ``title``; ``categories`` (tên nhóm trên trục ngang, ``[""]``
            khi khung chỉ có một nhóm); ``values`` (``{tên bên: [[giá trị từng hạt]
            của mỗi nhóm]}``); ``ylim``; ``fmt`` (định dạng số trên cột); ``yticks``
            (tuỳ chọn).
        sides: list ``(tên bên, nhãn chú giải, màu)`` theo thứ tự vẽ.
    """
    from matplotlib.lines import Line2D

    # Cột và khe tính bằng inch, nên mọi hình dày như nhau dù khung rộng hẹp khác nhau;
    # khe đủ rộng để số trên đầu hai cột cạnh nhau không đè lên nhau. Hình rộng ít nhất
    # 6,5 inch cho dòng tiêu đề và chú giải; trục dọc và lề chiếm khoảng 0,8 inch.
    bar_in, gap_in, axis_in = 0.19, 0.12, 0.8
    sizes = [1.4 + 1.1 * len(p["categories"]) for p in panels]
    total = max(sum(sizes), 6.5)
    fig, axes = plt.subplots(1, len(panels), figsize=(total, 4.3), squeeze=False,
                             gridspec_kw={"width_ratios": sizes},
                             facecolor=config.FIG_SURFACE)
    for ax, panel, size in zip(axes[0], panels, sizes):
        _report_axes(ax)
        ax.yaxis.grid(True, color=config.FIG_GRID, linewidth=0.8)
        groups = np.arange(len(panel["categories"]))
        per_unit = (size * total / sum(sizes) - axis_in) / (len(groups) + 0.2)
        width, gap = bar_in / per_unit, gap_in / per_unit
        for k, (side, _, color) in enumerate(sides):
            x = groups + (k - (len(sides) - 1) / 2) * (width + gap)
            seeds = [np.asarray(v, dtype=float) for v in panel["values"][side]]
            means = np.array([v.mean() for v in seeds])
            ax.bar(x, means, width=width, color=color, zorder=3)
            lows, highs = [v.min() for v in seeds], [v.max() for v in seeds]
            ax.vlines(x, lows, highs, color=config.FIG_INK, linewidth=1, zorder=4)
            ax.hlines(np.r_[lows, highs], np.r_[x, x] - width / 4, np.r_[x, x] + width / 4,
                      color=config.FIG_INK, linewidth=1, zorder=4)
            for xi, mean, high in zip(x, means, highs):
                ax.annotate(panel["fmt"].format(mean), (xi, high), xytext=(0, 3),
                            textcoords="offset points", ha="center", va="bottom",
                            fontsize=7.5, color=config.FIG_INK_2)
        ax.axhline(0.0, color=config.FIG_AXIS, linewidth=1, zorder=5)
        ax.set_xticks(groups, panel["categories"])
        ax.set_xlim(-0.6, len(groups) - 0.4)
        ax.set_ylim(*panel["ylim"])
        if "yticks" in panel:
            ax.set_yticks(panel["yticks"])
        ax.tick_params(axis="x", length=0)
        if panel.get("title"):
            ax.set_title(panel["title"], fontsize=9, color=config.FIG_INK)
    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for _, _, color in sides]
    handles.append(Line2D([], [], color=config.FIG_INK, linewidth=1))
    labels = [label for _, label, _ in sides] + ["thấp nhất–cao nhất của các hạt"]
    fig.legend(handles, labels, loc="lower center", ncol=len(handles), frameon=False,
               fontsize=8, labelcolor=config.FIG_INK_2)
    heading = "\n".join(t for t in (title, note) if t)
    if heading:
        fig.suptitle(heading, fontsize=10, color=config.FIG_INK)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
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
