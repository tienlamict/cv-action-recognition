"""Dựng bộ slide thuyết trình Phase 8–10 từ mẫu HUST.

Không thuộc đường ống nhận dạng: script chỉ đọc file kịch bản, file mẫu trong
docs/ và vài bảng kết quả trong results/, rồi ghi file .pptx. Toạ độ và màu dưới
đây là bố cục slide, không phải hằng số của hệ thống, nên không nằm trong
src/config.py.

- **Notes lấy từ kịch bản.** Lời nói, ghi chú và thời lượng của slide N được
  đọc từ mục "## Slide N — ..." của file kịch bản; phần "## Phụ lục — Câu hỏi
  có thể gặp" vào notes của slide cảm ơn. Sửa kịch bản rồi chạy lại là notes khớp.
- **Số liệu biểu đồ training đọc thẳng từ results/** (history.csv, per_class.csv
  của train_lstm run_07, run_08; model_comparison.csv). Chỉ những số chỉ có
  trong tài liệu tổng kết (phiên webcam, chuỗi độ tin của hộp đen) mới viết
  trong code.
- **Số trên biểu đồ ghi dấu phẩy thập phân** bằng nhãn tự đặt, không phụ thuộc
  locale của máy chiếu.
- **Nội dung chữ trên slide nằm trong code** (hàm build).
- **Font:** mọi chữ, kể cả layout và theme của mẫu, đổi sang Times New Roman.

Cần python-pptx (xem slides/requirements.txt); gói này không có trong
requirements.txt của dự án.

Ví dụ:
    python slides/build_slides.py
    python slides/build_slides.py --out docs/thuyet-trinh-phase-8-10.pptx
"""
import argparse
import copy
import csv
import json
import os
import re
import zipfile
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import (XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION,
                             XL_MARKER_STYLE, XL_TICK_LABEL_POSITION)
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Pt

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = ROOT / "docs" / "HUST_PPT_template_2022_Blue_16x9.pptx"
DEFAULT_SCRIPT = ROOT / "docs" / "kich-ban-thuyet-trinh-phase-8-10.md"
DEFAULT_OUT = ROOT / "docs" / "thuyet-trinh-phase-8-10.pptx"
LSTM_RUNS = ROOT / "results" / "phase7" / "train_lstm"
MODEL_COMPARISON = ROOT / "results" / "model_comparison.csv"

FONT = "Times New Roman"

NAVY = "00376F"
NAVY_MID = "0B4A8A"
NAVY_SOFT = "8FA6C4"
RED = "C00000"
RED_SOFT = "E8A0A0"
NAVY_TINT = "E8EEF6"
RED_TINT = "FBEAEA"
GRAY_TINT = "F2F4F7"
GRAY_BAR = "B8C2CF"
GRID = "E3E7ED"
DARK = "1F2937"
MUTED = "5F6B7A"
WHITE = "FFFFFF"
SOFT_WHITE = "D9E3F0"
NBSP = "\u00a0"

L, C, R = PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.RIGHT
TOP, MID, BOT = MSO_ANCHOR.TOP, MSO_ANCHOR.MIDDLE, MSO_ANCHOR.BOTTOM

QA_SLIDE = 24          # slide cảm ơn: notes kèm phần hỏi đáp của kịch bản


def rgb(h):
    return RGBColor.from_string(h)


def vn(v, nd=2):
    """Số thập phân kiểu Việt: 0.489 → '0,49'."""
    return f"{v:.{nd}f}".replace(".", ",")


def keep_together(t):
    """Không cho ngắt dòng giữa số và đơn vị, hay sau dấu ≈."""
    t = t.replace("≈ ", "≈" + NBSP)
    return re.sub(r"(\d) (?=giây|phút|s\b|ms|FPS|lệnh|lần)", lambda m: m.group(1) + NBSP, t)


# ---------------------------------------------------------------- text helpers
def fill_tf(tf, paras, size=16, color=DARK, bold=False, italic=False, align=L,
            anchor=TOP, margin=0, space_after=0, line_spacing=None):
    """paras: list of paragraphs. A paragraph is a str, a list of runs, or a dict
    {"runs": [...], "align", "size", "space_after", "space_before", "bold", "color"}.
    A run is a str or (text, {size, color, bold, italic})."""
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    if margin is not None:
        for side in ("left", "right", "top", "bottom"):
            setattr(tf, f"margin_{side}", Pt(margin))
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        popt = p if isinstance(p, dict) else {}
        runs = popt.get("runs", p) if isinstance(p, dict) else p
        if isinstance(runs, (str, tuple)):
            runs = [runs]
        para.alignment = popt.get("align", align)
        para.space_after = Pt(popt.get("space_after", space_after))
        if "space_before" in popt:
            para.space_before = Pt(popt["space_before"])
        if line_spacing:
            para.line_spacing = line_spacing
        psize = popt.get("size", size)
        for r in runs:
            t, ro = (r, {}) if isinstance(r, str) else r
            run = para.add_run()
            run.text = keep_together(t)
            f = run.font
            f.name = FONT
            f.size = Pt(ro.get("size", psize))
            f.bold = ro.get("bold", popt.get("bold", bold))
            f.italic = ro.get("italic", popt.get("italic", italic))
            f.color.rgb = rgb(ro.get("color", popt.get("color", color)))
    return tf


def text(slide, x, y, w, h, paras, name=None, **kw):
    shp = slide.shapes.add_textbox(Pt(x), Pt(y), Pt(w), Pt(h))
    if name:
        shp.name = name
    fill_tf(shp.text_frame, paras, **kw)
    return shp


def shape(slide, x, y, w, h, fill=None, line=None, line_w=1.25,
          kind=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08, paras=None, name=None, **kw):
    s = slide.shapes.add_shape(kind, Pt(x), Pt(y), Pt(w), Pt(h))
    if name:
        s.name = name
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(line_w)
    else:
        s.line.fill.background()
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.shadow.inherit = False
    if paras is not None:
        kw.setdefault("margin", 10)
        fill_tf(s.text_frame, paras, **kw)
    return s


def badge(slide, x, y, d, label, fill=RED, color=WHITE, size=16):
    return shape(slide, x, y, d, d, fill=fill, kind=MSO_SHAPE.OVAL,
                 paras=[label], size=size, bold=True, color=color, align=C,
                 anchor=MID, margin=0)


def table(slide, x, y, col_w, rows, row_h=32, head_h=None, size=14, hl=(), hl_fill=NAVY_TINT,
          red_rows=(), left_cols=(0,), name=None):
    """rows[0] là hàng tiêu đề. hl: các hàng tô đậm; red_rows: các hàng tô đỏ nhạt;
    left_cols: các cột căn trái (còn lại căn giữa)."""
    head_h = head_h or row_h
    gf = slide.shapes.add_table(len(rows), len(rows[0]), Pt(x), Pt(y),
                                Pt(sum(col_w)), Pt(head_h + row_h * (len(rows) - 1)))
    if name:
        gf.name = name
    tbl = gf.table
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Pt(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Pt(head_h if i == 0 else row_h)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            head = i == 0
            if head:
                fill = NAVY
            elif i in red_rows:
                fill = RED_TINT
            elif i in hl:
                fill = hl_fill
            else:
                fill = WHITE if i % 2 else GRAY_TINT
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(fill)
            cell.margin_left = cell.margin_right = Pt(8)
            cell.margin_top = cell.margin_bottom = Pt(2)
            cell.vertical_anchor = MID
            fill_tf(cell.text_frame, [val], size=size, margin=None, anchor=MID,
                    bold=head or i in hl, color=WHITE if head else (RED if i in red_rows else DARK),
                    align=L if j in left_cols else C)
    return gf


# --------------------------------------------------------------- chart helpers
def _font(font, size=13, color=MUTED, bold=False):
    font.name = FONT
    font.size = Pt(size)
    font.bold = bold
    font.color.rgb = rgb(color)


def plot_layout(chart, x, y, w, h):
    """Đặt vùng vẽ (không tính nhãn trục) theo tỉ lệ khung biểu đồ, để biết chính
    xác chỗ đặt nhãn trục tự ghi."""
    plot_area = chart._chartSpace.find(qn("c:chart")).find(qn("c:plotArea"))
    old = plot_area.find(qn("c:layout"))
    if old is not None:
        plot_area.remove(old)
    layout = etree.Element(qn("c:layout"))
    manual = etree.SubElement(layout, qn("c:manualLayout"))
    for tag, val in (("layoutTarget", "inner"), ("xMode", "edge"), ("yMode", "edge"),
                     ("x", x), ("y", y), ("w", w), ("h", h)):
        etree.SubElement(manual, qn(f"c:{tag}")).set("val", str(val))
    plot_area.insert(0, layout)


def base_chart(gf, legend=True, legend_size=13):
    ch = gf.chart
    ch.font.name = FONT
    ch.font.size = Pt(13)
    ch.has_title = False
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        _font(ch.legend.font, legend_size, DARK)
    return ch


def label_point(point, s, size=12, color=DARK, bold=True, pos=None):
    dl = point.data_label
    tf = dl.text_frame
    tf.text = s
    _font(tf.paragraphs[0].runs[0].font, size, color, bold)
    if pos is not None:
        dl.position = pos


class Plot:
    """Khung biểu đồ XY với vùng vẽ cố định; tự ghi nhãn trục tung (dấu phẩy)."""

    def __init__(self, slide, x, y, w, h, frac=(0.11, 0.05, 0.86, 0.68)):
        self.slide, self.x, self.y, self.w, self.h = slide, x, y, w, h
        self.fx, self.fy, self.fw, self.fh = frac

    def px(self, v, vmin, vmax):
        return self.x + self.w * (self.fx + self.fw * (v - vmin) / (vmax - vmin))

    def py(self, v, vmin, vmax):
        return self.y + self.h * (self.fy + self.fh * (1 - (v - vmin) / (vmax - vmin)))

    def y_labels(self, vmin, vmax, step, nd):
        n = int(round((vmax - vmin) / step))
        for k in range(n + 1):
            v = vmin + k * step
            yy = self.py(v, vmin, vmax)
            text(self.slide, self.x + self.w * self.fx - 46, yy - 9, 40, 18, [vn(v, nd)],
                 size=12, color=MUTED, align=R)


def xy_chart(slide, x, y, w, h, series, xr, yr, name, frac=(0.11, 0.05, 0.86, 0.68),
             x_labels=True, legend=True):
    """series: dict(name, pts, color, width, dash, marker). xr, yr: (min, max, step)."""
    cd = XyChartData()
    for s in series:
        ser = cd.add_series(s["name"])
        for a, b in s["pts"]:
            ser.add_data_point(a, b)
    gf = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS,
                                Pt(x), Pt(y), Pt(w), Pt(h), cd)
    gf.name = name
    ch = base_chart(gf, legend)
    plot_layout(ch, *frac)
    for ser, s in zip(ch.plots[0].series, series):
        ser.smooth = False
        ln = ser.format.line
        ln.color.rgb = rgb(s["color"])
        ln.width = Pt(s.get("width", 1.5))
        if s.get("dash"):
            ln.dash_style = MSO_LINE.DASH
        if s.get("marker"):
            ser.marker.style = XL_MARKER_STYLE.CIRCLE
            ser.marker.size = 8
            ser.marker.format.fill.solid()
            ser.marker.format.fill.fore_color.rgb = rgb(s["color"])
            ser.marker.format.line.color.rgb = rgb(s["color"])
        else:
            ser.marker.style = XL_MARKER_STYLE.NONE
    xa, ya = ch.category_axis, ch.value_axis
    xa.minimum_scale, xa.maximum_scale, xa.major_unit = xr
    ya.minimum_scale, ya.maximum_scale, ya.major_unit = yr
    xa.has_major_gridlines = False
    xa.format.line.color.rgb = rgb(GRAY_BAR)
    if x_labels:
        _font(xa.tick_labels.font, 12)
    else:
        xa.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    ya.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    ya.has_major_gridlines = True
    ya.major_gridlines.format.line.color.rgb = rgb(GRID)
    ya.format.line.fill.background()
    plot = Plot(slide, x, y, w, h, frac)
    return ch, plot


def bar_chart(slide, x, y, w, h, cats, series, name, kind=XL_CHART_TYPE.COLUMN_CLUSTERED,
              fmt=lambda v: vn(v), vmax=None, gap=60, overlap=0, legend=True,
              label_pos=XL_LABEL_POSITION.OUTSIDE_END, label_size=12, point_fill=None,
              reverse=False, cat_size=13):
    """series: list of (tên, giá trị, màu, màu chữ nhãn). point_fill: {(s, i): màu}."""
    cd = CategoryChartData()
    cd.categories = cats
    for nm, vals, _, _ in series:
        cd.add_series(nm, vals)
    gf = slide.shapes.add_chart(kind, Pt(x), Pt(y), Pt(w), Pt(h), cd)
    gf.name = name
    ch = base_chart(gf, legend)
    plot = ch.plots[0]
    plot.gap_width = gap
    plot.overlap = overlap
    for si, (ser, (_, vals, col, lcol)) in enumerate(zip(plot.series, series)):
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = rgb(col)
        for i, v in enumerate(vals):
            pt = ser.points[i]
            if point_fill and (si, i) in point_fill:
                pt.format.fill.solid()
                pt.format.fill.fore_color.rgb = rgb(point_fill[(si, i)])
            if v:
                label_point(pt, fmt(v), label_size, lcol, True, label_pos)
    ca, va = ch.category_axis, ch.value_axis
    ca.has_major_gridlines = False
    ca.format.line.color.rgb = rgb(GRAY_BAR)
    _font(ca.tick_labels.font, cat_size, DARK, True)
    ca.reverse_order = reverse
    va.visible = False
    va.has_major_gridlines = False
    va.minimum_scale = 0
    if vmax is not None:
        va.maximum_scale = vmax
    return ch


# --------------------------------------------------------------- slide helpers
def set_title(slide, title, size=24, color=WHITE):
    tf = slide.shapes.title.text_frame
    tf.clear()
    fill_tf(tf, [title], size=size, bold=True, color=color, anchor=MID)
    tf.margin_left = tf.margin_right = Pt(7)


def strip_placeholders(slide):
    for ph in list(slide.placeholders):
        if ph.placeholder_format.type not in (1, 3):  # TITLE, CENTER_TITLE
            ph._element.getparent().remove(ph._element)


def add_slide_number(slide):
    for ph in slide.slide_layout.placeholders:
        if ph.placeholder_format.type == 13:  # SLIDE_NUMBER
            slide.shapes._spTree.append(copy.deepcopy(ph._element))
            return


def new_slide(prs, layout_name, title, title_size=24, title_color=WHITE):
    s = prs.slides.add_slide(prs.slide_layouts.get_by_name(layout_name))
    strip_placeholders(s)
    add_slide_number(s)
    set_title(s, title, title_size, title_color)
    return s


def header_slide(prs, title):
    return new_slide(prs, "Section Header", title)


def fsm_row(s, y, states, h=66):
    bw, bg = 186, 45
    for i, (nm, desc, hot) in enumerate(states):
        bx = 40 + i * (bw + bg)
        shape(s, bx, y, bw, h, fill=RED if hot else NAVY_TINT, line=None if hot else NAVY,
              name=f"State {i+1}",
              paras=[{"runs": [(nm, {"bold": True, "size": 17, "color": WHITE if hot else NAVY})],
                      "space_after": 1},
                     {"runs": [(desc, {"size": 14, "color": WHITE if hot else DARK})]}],
              align=C, anchor=MID, margin=4)
        if i < len(states) - 1:
            shape(s, bx + bw + 7, y + h / 2 - 10, bg - 14, 20, fill=MUTED,
                  kind=MSO_SHAPE.RIGHT_ARROW, name=f"Edge {i+1}")


def card(s, x, y, w, h, head, body, fill=GRAY_TINT, head_color=NAVY, line=None, size=15,
         head_size=17, name=None, anchor=TOP):
    return shape(s, x, y, w, h, fill=fill, line=line, line_w=1.5, name=name,
                 paras=[{"runs": [(head, {"bold": True, "size": head_size, "color": head_color})],
                         "space_after": 4}] + ([body] if isinstance(body, str) else body),
                 size=size, color=DARK if fill not in (NAVY, NAVY_MID) else WHITE,
                 margin=14, anchor=anchor)


# ------------------------------------------------------- notes từ file kịch bản
def unwrap(block):
    """Gỡ '> ', backtick, '**'; nối các dòng bị ngắt; giữ ranh giới đoạn, gạch đầu
    dòng và các dòng chỉ dẫn sân khấu '(...)'."""
    out, cur = [], ""
    for raw in block.strip().splitlines():
        line = raw[2:] if raw.startswith("> ") else raw.lstrip(">")
        line = line.replace("`", "").replace("**", "")
        if not line.strip():
            if cur:
                out.append(cur)
                cur = ""
            out.append("")
        elif line.startswith(("- ", "(")) or re.match(r"^\d+\. ", line):
            if cur:
                out.append(cur)
            cur = line
        else:
            cur = (cur + " " + line.strip()) if cur else line.strip()
    if cur:
        out.append(cur)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def load_notes(path):
    md = open(path, encoding="utf-8").read()
    parts = re.split(r"\n## Slide (\d+) — ([^\n]*)\n", md)
    res = {}
    for k in range(1, len(parts), 3):
        n, title, body = int(parts[k]), parts[k + 1], parts[k + 2].split("\n---")[0]
        dur = re.search(r"\((\d+:\d+)\)", title)
        loi = re.search(r"\*\*Lời nói:\*\*\n(.*?)(?=\n\*\*Ghi chú:\*\*|\Z)", body, re.S)
        ghi = re.search(r"\*\*Ghi chú:\*\*(.*)", body, re.S)
        chunks = []
        if dur:
            chunks.append(f"Thời lượng: {dur.group(1)}")
        if loi:
            chunks.append("LỜI NÓI:\n" + unwrap(loi.group(1)))
        if ghi:
            chunks.append("GHI CHÚ:\n" + unwrap(ghi.group(1)))
        res[n] = "\n\n".join(chunks)
    qa = md.split("## Phụ lục — Câu hỏi có thể gặp", 1)
    if len(qa) == 2:
        res["qa"] = "CÂU HỎI CÓ THỂ GẶP:\n\n" + unwrap(qa[1])
    return res


NOTES = {}


def notes(slide, n):
    body = NOTES.get(n, "")
    if n == QA_SLIDE and "qa" in NOTES:
        body = (body + "\n\n" + NOTES["qa"]).strip()
    slide.notes_slide.notes_text_frame.text = body


# ------------------------------------------------------ số liệu từ results/
def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lstm_history(run):
    rows = read_csv(LSTM_RUNS / run / "history.csv")
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def lstm_manifest(run):
    return json.loads((LSTM_RUNS / run / "manifest.json").read_text(encoding="utf-8"))


def per_class_f1(run):
    return {r["class"]: float(r["f1"]) for r in read_csv(LSTM_RUNS / run / "per_class.csv")}


def trailing_mean(xs, k):
    return [sum(xs[max(0, i - k + 1):i + 1]) / len(xs[max(0, i - k + 1):i + 1])
            for i in range(len(xs))]


# ======================================================================= build
def build(template, script_md, out):
    """Dựng 25 slide vào out; notes đọc từ script_md."""
    NOTES.clear()
    NOTES.update(load_notes(script_md))

    prs = Presentation(str(template))
    tpl = list(prs.slides)  # 0 bìa, 1 nền chấm, 2 trang tiêu đề, ..., 8 cảm ơn
    built = []

    # ------------------------------------------------------------ 1. Mở đầu
    s = tpl[2]
    t_main, t_sub = sorted([sh for sh in s.shapes if sh.name == "Title 6"], key=lambda sh: sh.top)
    t_main.top, t_main.width, t_main.height = Pt(118), Pt(560), Pt(120)
    t_main.text_frame.clear()
    fill_tf(t_main.text_frame,
            ["Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính"],
            size=36, bold=True, color=RED, line_spacing=0.95)
    t_sub.top, t_sub.width, t_sub.height = Pt(248), Pt(540), Pt(100)
    t_sub.text_frame.clear()
    fill_tf(t_sub.text_frame,
            [{"runs": [("PHASE 8–10", {"bold": True})], "space_after": 4},
             "Hệ thống đã được tối ưu như thế nào"],
            size=20, color=NAVY)
    notes(s, 1)
    built.append(s)

    # ------------------------------------------------------------ 2. Đọc nhanh
    s = new_slide(prs, "Title Only", "Đọc nhanh", 28, NAVY)
    text(s, 372, 84, 560, 26,
         [[("Hệ thống ", {}), ("điều khiển được PowerPoint", {"bold": True, "color": RED}),
           (" bằng cử chỉ tay trước webcam", {})]], size=17, color=DARK)
    gest = [("Vuốt trái", "slide sau"), ("Vuốt phải", "slide trước"),
            ("Mở ba đầu ngón", "phóng to"), ("Chụm ba đầu ngón", "thu nhỏ")]
    for i, (g, a) in enumerate(gest):
        cx = 372 + (i % 2) * 286
        cy = 118 + (i // 2) * 64
        shape(s, cx, cy, 274, 54, fill=NAVY, name=f"Gesture {i+1}",
              paras=[[(g, {"bold": True}), ("  →  " + a, {"color": SOFT_WHITE})]],
              size=17, color=WHITE, anchor=MID, margin=14)
    text(s, 372, 254, 560, 50,
         [[("Phase 8–10 ", {"bold": True, "color": NAVY}),
           ("không đổi cách máy “nhìn” bàn tay", {"bold": True}),
           (" — tối ưu mọi thứ xung quanh:", {})]], size=17, color=DARK)
    around = ["Khi nào bấm phím", "Đo cho đúng", "Mô hình nào lo cử chỉ nào",
              "Ngưỡng cho từng loại cử chỉ", "Cách người dùng làm cử chỉ"]
    for i, a in enumerate(around):
        cx = 372 + (i % 2) * 286
        cy = 300 + (i // 2) * 54
        shape(s, cx, cy, 274, 44, fill=NAVY_TINT, radius=0.5, name=f"Around {i+1}",
              paras=[a], size=16, bold=True, color=NAVY, anchor=MID, margin=14)
    notes(s, 2)
    built.append(s)

    # --------------------------------------------- 3. Lúc bắt đầu và bây giờ
    s = header_slide(prs, "Lúc bắt đầu và bây giờ")
    deltas = [("Slide tự đổi khi không ai làm gì, trên video thử", "6,6–30", "0,85", "lần/phút"),
              ("Slide tự đổi khi người dùng nói chuyện có khua tay", "0,64", "0,18", "lần/phút"),
              ("Vuốt một chiều mà slide đi chiều ngược lại", "5/20", "2/20", ""),
              ("Zoom được nhận trên tay người dùng", "0/10", "10/20", ""),
              ("Thử slide thật: cú zoom thành lệnh", "0/12", "6/12", "")]
    for i, (lab, before, after, unit) in enumerate(deltas):
        cx = 40 + (i % 3) * 297
        cy = 82 + (i // 3) * 160
        shape(s, cx, cy, 286, 148, fill=GRAY_TINT, name=f"Delta {i+1}")
        text(s, cx + 18, cy + 12, 250, 44, [lab], size=15, bold=True, color=DARK)
        runs = [(before, {"size": 22, "color": MUTED}), ("  →  ", {"size": 22, "color": MUTED}),
                (after, {"size": 38, "bold": True, "color": RED})]
        if unit:
            runs.append(("  " + unit, {"size": 14, "color": MUTED}))
        text(s, cx + 18, cy + 62, 262, 76, [runs], anchor=BOT)
    shape(s, 634, 242, 286, 148, fill=NAVY, name="F1 note",
          paras=[{"runs": [("Điểm F1 trên bộ video chuẩn", {"bold": True, "color": SOFT_WHITE})],
                  "space_after": 6},
                 [("0,559", {"size": 22, "color": SOFT_WHITE}), ("  →  ", {"size": 22, "color": SOFT_WHITE}),
                  ("0,561", {"size": 38, "bold": True})],
                 {"runs": [("giữ gần như cũ", {"italic": True, "color": SOFT_WHITE})]}],
          size=15, color=WHITE, anchor=MID, margin=18)
    shape(s, 40, 406, 880, 56, fill=NAVY_TINT, name="Config strip",
          paras=[[("Đang dùng — mô hình ghép:  ", {"color": MUTED}),
                  ("vuốt ← LSTM", {"bold": True, "color": NAVY}), (" 0,85 · 4/5   ·   ", {}),
                  ("zoom ← rừng ngẫu nhiên", {"bold": True, "color": NAVY}), (" 0,40 · 3/5", {})]],
          size=16, color=DARK, anchor=MID, margin=18)
    notes(s, 3)
    built.append(s)

    # --------------------------------------- 4. Máy tính nhìn bàn tay thế nào
    s = header_slide(prs, "Máy tính “nhìn” bàn tay thế nào")
    steps = [("Camera", "≈ 30 ảnh mỗi giây"),
             ("MediaPipe", "21 điểm: cổ tay, khớp, đầu ngón"),
             ("Cửa sổ", "1,2 giây gần nhất, xét lại mỗi 0,2 giây"),
             ("Mô hình", "nhãn (cử chỉ nào) + độ tin (0–1)")]
    for i, (hd, body) in enumerate(steps):
        bx = 40 + i * 228
        shape(s, bx, 84, 196, 104, fill=NAVY if i == 3 else NAVY_TINT, name=f"Step {i+1}",
              paras=[{"runs": [(hd, {"bold": True, "size": 19,
                                     "color": WHITE if i == 3 else NAVY})], "space_after": 4},
                     {"runs": [(body, {"color": SOFT_WHITE if i == 3 else DARK})]}],
              size=15, align=C, anchor=MID, margin=10)
        if i < 3:
            shape(s, bx + 201, 124, 22, 24, fill=RED, kind=MSO_SHAPE.CHEVRON, name=f"Flow {i+1}")
    text(s, 40, 202, 880, 24, [[("Năm lớp và năm phím", {"bold": True, "color": NAVY})]], size=17)
    classes = [("none", "không có cử chỉ", "không gửi gì"),
               ("swipe_left", "vuốt sang trái", "→  slide sau"),
               ("swipe_right", "vuốt sang phải", "←  slide trước"),
               ("zoom_in", "mở ba đầu ngón", "+  phóng to"),
               ("zoom_out", "chụm ba đầu ngón", "−  thu nhỏ")]
    for i, (code, mean, key) in enumerate(classes):
        cx = 40 + i * 178
        shape(s, cx, 232, 168, 112, fill=GRAY_TINT, line=RED if i == 0 else None, name=f"Class {code}",
              paras=[{"runs": [(code, {"bold": True, "size": 16, "color": RED if i == 0 else NAVY})],
                      "space_after": 4},
                     {"runs": [(mean, {})], "space_after": 6},
                     {"runs": [(key, {"bold": True})]}],
              size=15, color=DARK, align=C, anchor=MID, margin=6)
    shape(s, 40, 360, 880, 102, fill=RED_TINT, name="None matters",
          paras=[{"runs": [("Lớp none quan trọng không kém bốn lớp kia", {"bold": True, "color": RED})],
                  "space_after": 4},
                 "Phần lớn thời gian tay người dùng không làm cử chỉ: đang nói, gãi đầu, chỉ vào "
                 "màn hình. Hệ thống phải im lặng lúc đó."],
          size=16, color=DARK, anchor=MID, margin=18)
    notes(s, 4)
    built.append(s)

    # ---------------------------------------------- 5. Ba bộ não và dữ liệu
    s = header_slide(prs, "Ba “bộ não” và dữ liệu học")
    brains = [("Luật", "vài quy tắc viết tay — mốc so sánh", GRAY_TINT),
              ("Rừng ngẫu nhiên", "hàng trăm cây quyết định bỏ phiếu trên 15 con số tóm tắt cửa sổ", GRAY_TINT),
              ("LSTM", "mạng nơ-ron đọc cả chuỗi chuyển động, từng bước một", GRAY_TINT),
              ("Mô hình ghép", "LSTM lo vuốt, rừng lo zoom", NAVY)]
    for i, (hd, body, fill) in enumerate(brains):
        card(s, 40, 82 + i * 96, 430, 86, hd, body, fill=fill,
             head_color=WHITE if fill == NAVY else NAVY, name=f"Brain {i+1}", anchor=MID)
    shape(s, 490, 82, 430, 220, fill=GRAY_TINT, name="IPN panel")
    text(s, 508, 94, 396, 54,
         [{"runs": [("IPN Hand", {"bold": True, "size": 19, "color": NAVY})], "space_after": 2},
          "200 video quay sẵn, có người diễn và nhãn sẵn"], size=15, color=DARK)
    for k, (lab, fill, col) in enumerate([("Tập học", NAVY_TINT, NAVY), ("Kiểm định (val)", NAVY_TINT, NAVY),
                                          ("Test — khoá tới lần cuối", RED_TINT, RED)]):
        shape(s, 508 + k * 132, 160, 126, 54, fill=fill, radius=0.2, paras=[lab], size=14,
              bold=True, color=col, align=C, anchor=MID, margin=4, name=f"Split {k+1}")
    text(s, 508, 226, 396, 66,
         [[("Chia theo người: ", {"bold": True}),
           "người của tập học không bao giờ xuất hiện ở tập chấm — mô hình phải nhận tay người lạ"]],
         size=15, color=DARK)
    shape(s, 490, 316, 430, 146, fill=RED_TINT, line=RED, line_w=1.5, name="Red thread",
          paras=[{"runs": [("Hệ quả — sợi chỉ đỏ của Phase 10", {"bold": True, "color": RED})],
                  "space_after": 6},
                 "Mô hình học cử chỉ theo cách người diễn IPN làm. Người dùng làm khác đi thì mô "
                 "hình có thể không nhận ra."],
          size=16, color=DARK, anchor=MID, margin=18)
    notes(s, 5)
    built.append(s)

    # ---------------------------------------------- 6. Đo tốt như thế nào
    s = header_slide(prs, "Đo “tốt” như thế nào")
    qs = [("“Tôi làm cử chỉ, nó có nhận không?”", "RECALL", "tỉ lệ cử chỉ thật được nhận"),
          ("“Tôi không làm gì, nó có tự đổi slide không?”", "LỆNH NHẦM MỖI PHÚT",
           "số lần tự phát lệnh khi không có cử chỉ")]
    for i, (q, term, d) in enumerate(qs):
        cx = 40 + i * 446
        shape(s, cx, 82, 434, 112, fill=NAVY, name=f"Question {i+1}",
              paras=[{"runs": [(q, {"italic": True, "color": SOFT_WHITE})], "space_after": 4},
                     {"runs": [(term, {"bold": True, "size": 22})], "space_after": 2},
                     {"runs": [(d, {"color": SOFT_WHITE, "size": 14})]}],
              size=16, color=WHITE, anchor=MID, margin=16)
    card(s, 40, 206, 434, 66, "Precision", "trong các lệnh phát ra, bao nhiêu phần là đúng",
         name="Precision", anchor=MID, head_size=16)
    card(s, 486, 206, 434, 66, "F1", "gộp precision và recall, từ 0 đến 1 — chỉ cao khi cả hai cùng cao",
         name="F1", anchor=MID, head_size=16)
    shape(s, 40, 286, 330, 176, fill=GRAY_TINT, name="Window level",
          paras=[{"runs": [("MỨC CỬA SỔ", {"bold": True, "color": MUTED, "size": 14})], "space_after": 6},
                 {"runs": [("Chấm từng đoạn 1,2 giây", {"bold": True, "size": 18})], "space_after": 6},
                 "như chấm từng tấm ảnh chụp"],
          size=15, color=DARK, anchor=MID, margin=18)
    shape(s, 378, 360, 24, 30, fill=RED, kind=MSO_SHAPE.CHEVRON, name="Level arrow")
    shape(s, 410, 286, 510, 176, fill=NAVY, name="Event level")
    text(s, 430, 298, 470, 24, [[("MỨC SỰ KIỆN — thước đo chính từ Phase 8", {"bold": True, "color": SOFT_WHITE})]],
         size=14)
    text(s, 430, 322, 470, 30, ["Đếm lệnh phát ra, như người dùng thấy"], size=18, bold=True, color=WHITE)
    for k, (big, lab) in enumerate([("27", "video kiểm định"), ("60", "phút"), ("108", "cử chỉ")]):
        text(s, 430 + k * 156, 358, 150, 50, [big], size=36, bold=True, color=WHITE)
        text(s, 430 + k * 156, 408, 150, 22, [lab], size=14, color=SOFT_WHITE)
    text(s, 430, 432, 470, 24, ["lệnh đúng = đúng loại, trong lúc cử chỉ diễn ra hoặc tới 1 giây sau"],
         size=13, italic=True, color=SOFT_WHITE)
    notes(s, 6)
    built.append(s)

    # ---------------------------------------------- 7. Đo trước, sửa sau
    s = header_slide(prs, "Nếp làm việc: đo trước, sửa sau")
    quad = [(40, 82), (486, 82), (40, 278), (486, 278)]
    heads = ["Ghi một lần, chấm mọi cấu hình", "Tìm nguyên nhân bằng số đo, không đoán",
             "Mỗi thay đổi chấm trên bốn nguồn", "Người dùng chọn điểm đánh đổi"]
    for i, ((cx, cy), hd) in enumerate(zip(quad, heads)):
        shape(s, cx, cy, 434, 184, fill=GRAY_TINT, name=f"Method {i+1}")
        badge(s, cx + 16, cy + 14, 32, str(i + 1), fill=NAVY, size=15)
        text(s, cx + 58, cy + 14, 360, 32, [hd], size=18, bold=True, color=NAVY, anchor=MID)
    cx, cy = quad[0]
    text(s, cx + 18, cy + 56, 220, 120,
         ["Như hộp đen máy bay: ghi 21 điểm của từng ảnh, rồi “phát lại” qua bất kỳ mô hình hay "
          "ngưỡng nào"], size=15, color=DARK)
    text(s, cx + 246, cy + 52, 176, 60, ["316/316"], size=36, bold=True, color=RED, align=C, anchor=MID)
    text(s, cx + 246, cy + 112, 176, 50, ["câu trả lời trùng lúc chạy thật"], size=14, color=MUTED, align=C)
    cx, cy = quad[1]
    for k, chip in enumerate(["ngón gập hay duỗi", "cái–trỏ cách bao xa", "mô hình nói gì",
                              "ở từng nhịp 0,2 giây"]):
        shape(s, cx + 18 + (k % 2) * 203, cy + 62 + (k // 2) * 56, 194, 46, fill=WHITE,
              line=NAVY_TINT, radius=0.5, paras=[chip], size=15, bold=True, color=NAVY,
              align=C, anchor=MID, margin=4, name=f"Probe {k+1}")
    cx, cy = quad[2]
    for k, (big, lab) in enumerate([("27", "video kiểm định"), ("40", "lời nhắc webcam"),
                                    ("≈ 11", "phút nói chuyện"), ("2", "lần thử slide")]):
        sx = cx + 18 + k * 101
        text(s, sx, cy + 64, 96, 50, [big], size=30, bold=True, color=RED, align=C, anchor=MID)
        text(s, sx, cy + 116, 96, 50, [lab], size=14, color=DARK, align=C)
    cx, cy = quad[3]
    text(s, cx + 18, cy + 58, 398, 120,
         ["Thường không có cấu hình tốt nhất về mọi mặt.",
          "Đo và bày bảng: mỗi vòng ghi rõ được gì, mất gì — rồi mới chọn."],
         size=15, color=DARK, space_after=8)
    notes(s, 7)
    built.append(s)

    # ------------------------------------------------ 8. Vòng 1: trợ lý
    s = header_slide(prs, "Vòng 1 — Dạy hệ thống biết im lặng")
    shape(s, 40, 80, 880, 46, fill=GRAY_TINT, name="Commentator",
          paras=[[("Mô hình như bình luận viên hô 5 lần mỗi giây:  ", {"bold": True, "color": NAVY}),
                  ("“vuốt trái!… vuốt trái!… không có gì!… vuốt trái!…”", {"italic": True})]],
          size=16, color=DARK, anchor=MID, margin=16)
    probs = [("82–94%", "cử chỉ được bắt", NAVY), ("6,6–30", "lệnh nhầm mỗi phút", RED),
             ("5–20%", "số lệnh là đúng", RED)]
    for i, (big, lab, col) in enumerate(probs):
        cx = 40 + i * 297
        shape(s, cx, 136, 286, 58, fill=WHITE, line=GRAY_BAR, line_w=1, name=f"Problem {i+1}")
        text(s, cx + 14, 136, 130, 58, [big], size=26, bold=True, color=col, anchor=MID)
        text(s, cx + 146, 136, 132, 58, [lab], size=15, color=DARK, anchor=MID)
    text(s, 40, 204, 880, 24,
         [[("Sửa: ", {"bold": True, "color": NAVY}),
           "đặt giữa bình luận viên và bàn phím một ", ("người trợ lý cẩn thận", {"bold": True}),
           " (máy trạng thái)"]], size=16)
    fsm_row(s, 232, [("Chờ tay", "chưa thấy bàn tay", False),
                     ("Sẵn sàng", "thấy tay, đang lắng nghe", False),
                     ("Đang cân nhắc", "chờ thêm tiếng hô cùng ý", True),
                     ("Nghỉ", "1,2 giây sau khi bấm", False)])
    shape(s, 40, 306, 880, 28, fill=RED_TINT, kind=MSO_SHAPE.LEFT_ARROW, name="Reset arrow",
          paras=[[("Hạ tay ra khỏi khung → quên hết, về “Chờ tay”", {"bold": True})]],
          size=14, color=RED, align=C, anchor=MID, margin=2)
    rules = [("Đủ chắc mới cân nhắc", "ngưỡng độ tin"),
             ("Đủ tiếng hô cùng ý", "trong 5 tiếng liền (đồng thuận)"),
             ("Bấm xong nghỉ 1,2 giây", "như chuông cửa chỉ reo một lần"),
             ("Hạ tay là huỷ hết", "trợ lý quên mọi thứ đang cân nhắc")]
    for i, (hd, body) in enumerate(rules):
        cx = 40 + i * 223
        shape(s, cx, 346, 211, 116, fill=NAVY_TINT, name=f"Rule {i+1}")
        badge(s, cx + 12, 358, 28, str(i + 1), fill=NAVY, size=14)
        text(s, cx + 48, 354, 156, 44, [hd], size=15, bold=True, color=NAVY, anchor=MID)
        text(s, cx + 14, 402, 186, 54, [body], size=14, color=DARK)
    notes(s, 8)
    built.append(s)

    # ------------------------------------------- 9. Vòng 1: kết quả, cái giá
    s = header_slide(prs, "Vòng 1 — Phiếu phản đối, kết quả và cái giá")
    shape(s, 40, 80, 430, 184, fill=GRAY_TINT, name="Veto panel")
    text(s, 58, 90, 400, 24, [[("Lỗi thiết kế đã tránh", {"bold": True, "color": NAVY})]], size=16)
    for k, lab in enumerate(["vuốt", "không", "vuốt", "không", "vuốt"]):
        v = lab == "vuốt"
        shape(s, 58 + k * 78, 120, 70, 34, fill=NAVY if v else GRAY_BAR, radius=0.15,
              paras=[lab], size=14, bold=True, color=WHITE if v else DARK, align=C, anchor=MID,
              margin=0, name=f"Flicker {k+1}")
    text(s, 58, 162, 396, 96,
         [{"runs": [("Đếm 3/5 tiếng “vuốt” → ", {}), ("vẫn bấm phím", {"bold": True, "color": RED})],
           "space_after": 6},
          [("Bản dùng thật: tiếng hô ", {}), ("khác ý mà đủ chắc", {"bold": True}),
           (" là ", {}), ("phiếu phản đối", {"bold": True, "color": NAVY}), (" → huỷ ngay", {})]],
         size=15, color=DARK)
    shape(s, 40, 278, 430, 184, fill=RED_TINT, line=RED, line_w=1.5, name="Cost panel")
    text(s, 58, 290, 200, 22, [[("MẤT GÌ", {"bold": True, "color": RED})]], size=14)
    text(s, 58, 312, 170, 70, ["0,77"], size=52, bold=True, color=RED)
    text(s, 58, 384, 170, 70, ["lệnh mỗi cử chỉ — trợ lý cẩn thận đôi khi bỏ lỡ"], size=14, color=DARK)
    x0, x1, ys = 240, 452, 360

    def sx(v):
        return x0 + v / 1.2 * (x1 - x0)
    shape(s, x0, ys, x1 - x0, 4, fill=GRAY_BAR, kind=MSO_SHAPE.RECTANGLE, name="Scale")
    shape(s, sx(0.9), ys - 12, sx(1.1) - sx(0.9), 28, fill=NAVY, kind=MSO_SHAPE.RECTANGLE,
          name="Target band")
    shape(s, sx(0.77) - 8, ys - 6, 16, 16, fill=RED, kind=MSO_SHAPE.OVAL, name="Marker")
    for v, lab in ((0, "0"), (0.77, "0,77"), (1.2, "1,2")):
        text(s, sx(v) - 24, ys + 20, 48, 20, [lab], size=12, color=MUTED, align=C)
    text(s, sx(0.9) - 34, ys - 40, sx(1.1) - sx(0.9) + 68, 22, ["yêu cầu 0,9–1,1"], size=12,
         bold=True, color=NAVY, align=C)
    text(s, 490, 80, 430, 22, [[("Ngưỡng khởi đầu 0,75 · 3/5, trên video kiểm định",
                                 {"bold": True, "color": NAVY})]], size=15)
    table(s, 490, 106, [170, 130, 130],
          [["Bộ não", "F1 sự kiện", "Nhầm mỗi phút"],
           ["LSTM", "0,559", "1,46"], ["Mô hình ghép", "0,490", "1,33"],
           ["Rừng", "0,405", "0,50"], ["Luật", "0,130", "6,82"]],
          row_h=32, size=15, hl=(1,), name="Round1 table")
    shape(s, 490, 286, 430, 176, fill=GRAY_TINT, name="Min presence",
          paras=[{"runs": [("Đánh đổi: “phải thấy tay bao nhiêu”", {"bold": True, "color": NAVY})],
                  "space_after": 6},
                 {"runs": ["Cửa sổ chỉ được xét khi ≥ 70% số ảnh thấy tay"], "space_after": 6},
                 [("70% → 100%: ", {"bold": True}), "mất 3/54 cú vuốt, lệnh nhầm chỉ giảm 3%"],
                 {"runs": [("→ giữ 70%", {"bold": True, "color": RED})], "space_before": 4}],
          size=15, color=DARK, anchor=MID, margin=18)
    notes(s, 9)
    built.append(s)

    # ---------------------------------------------- 10. Vòng 2: sửa thước đo
    s = header_slide(prs, "Vòng 2 — Sửa thước đo trước khi sửa hệ thống")
    text(s, 40, 78, 400, 24, [[("Con số đánh lừa", {"bold": True, "color": RED})]], size=16)
    text(s, 486, 78, 434, 24, [[("Cách sửa", {"bold": True, "color": NAVY})]], size=16)
    fixes = [
        ("Đồng hồ bấm giờ bắt đầu sai lúc",
         "Lời nhắc 4 giây gồm cả lúc thu tay → độ trễ ra số âm",
         "Đo độ trễ trên video IPN, nơi khoảnh khắc chính đã được đánh dấu sẵn"),
        ("Điểm “hoàn hảo” che giấu hai lỗi",
         "1,00 lệnh mỗi cử chỉ, nhưng recall chỉ 0,55 — bỏ lỡ và lệnh thừa bù cho nhau",
         "Luôn báo kèm tỉ lệ nhận đúng, số lệnh mỗi lời nhắc, số lệnh phát trùng"),
        ("Trung bình sai cách",
         "Đọc và gõ phím luôn ra 0 (tay ngoài khung), kéo luật từ 7,39 xuống 2,46",
         "Cộng tổng lệnh nhầm chia tổng số phút; thêm “nhầm mỗi phút có tay” (17% so với 89%)"),
    ]
    for i, (hd, why, fix) in enumerate(fixes):
        y = 106 + i * 120
        card(s, 40, y, 400, 108, hd, why, fill=RED_TINT, head_color=RED, name=f"Trap {i+1}",
             anchor=MID)
        shape(s, 450, y + 40, 26, 28, fill=MUTED, kind=MSO_SHAPE.RIGHT_ARROW, name=f"To fix {i+1}")
        shape(s, 486, y, 434, 108, fill=NAVY_TINT, name=f"Fix {i+1}",
              paras=[fix], size=16, color=DARK, anchor=MID, margin=16)
    notes(s, 10)
    built.append(s)

    # ------------------------------------------- 11. Vòng 3: bàn tay thật
    s = header_slide(prs, "Vòng 3 — Mô hình cho bàn tay thật của người dùng")
    card(s, 40, 80, 410, 82, "Chuyện gì không ổn",
         [[("LSTM run_07 nhận ", {}), ("0/10", {"bold": True}),
           (" cú zoom; tay chụm đứng yên lại hô “vuốt”", {})]],
         fill=RED_TINT, head_color=RED, name="Problem", anchor=MID)
    shape(s, 40, 172, 410, 150, fill=GRAY_TINT, name="Diagnosis")
    text(s, 54, 180, 386, 44,
         [[("Độ duỗi ngón", {"bold": True, "color": NAVY}),
           (" = (đầu ngón → cổ tay) / (gốc ngón → cổ tay)", {"size": 14})],
          [("gập ≈ 0,5 · thẳng ≈ 1,3–1,5", {"size": 14, "color": MUTED})]], size=15)
    a0, a1, ay = 64, 426, 266

    def ax(v):
        return a0 + v / 2.2 * (a1 - a0)
    shape(s, a0, ay, a1 - a0, 3, fill=GRAY_BAR, kind=MSO_SHAPE.RECTANGLE, name="Ext axis")
    shape(s, ax(0.5) - 7, ay - 6, 14, 14, fill=NAVY, kind=MSO_SHAPE.OVAL, name="IPN mark")
    shape(s, ax(1.5), ay - 8, ax(2.1) - ax(1.5), 18, fill=RED, kind=MSO_SHAPE.RECTANGLE,
          name="User range")
    text(s, ax(0.5) - 70, ay - 30, 140, 20, ["IPN: nhẫn, út gập ≈ 0,5"], size=12, bold=True,
         color=NAVY, align=C)
    text(s, ax(1.5) - 50, ay - 30, ax(2.1) - ax(1.5) + 100, 20, ["người dùng: duỗi 1,5–2,1"],
         size=12, bold=True, color=RED, align=C)
    for v in (0, 1, 2):
        text(s, ax(v) - 15, ay + 12, 30, 18, [str(v)], size=12, color=MUTED, align=C)
    text(s, 54, 296, 390, 22, ["LSTM học “zoom = nhẫn, út gập” nên không nhận ra tay người dùng"],
         size=13, italic=True, color=MUTED)
    shape(s, 40, 332, 410, 130, fill=NAVY, name="Fix",
          paras=[{"runs": [("Sửa: run_08 học thêm ví dụ biến tấu", {"bold": True, "color": SOFT_WHITE})],
                  "space_after": 6},
                 {"runs": ["• 1/2 ví dụ zoom mang dáng ngón phụ của một bàn tay IPN khác"],
                  "space_after": 4},
                 "• bàn tay đứng yên, nhãn “không có gì”"],
          size=15, color=WHITE, anchor=MID, margin=16)
    text(s, 470, 80, 450, 22, [[("Được gì — cùng dữ liệu, cùng ngưỡng", {"bold": True, "color": NAVY})]],
         size=15)
    table(s, 470, 106, [222, 110, 118],
          [["", "run_07", "run_08"],
           ["Zoom trên webcam", "0/10", "4/10"],
           ["Tập zoom: phóng to / thu nhỏ / vuốt nhầm", "0 / 2 / 4", "5 / 5 / 0"],
           ["IPN sửa cho nhẫn, út duỗi: zoom còn nhận", "10% / 35%", "95% / 95%"],
           ["F1 sự kiện, video kiểm định", "0,559", "0,554"]],
          row_h=44, head_h=32, size=14, name="Run table")
    shape(s, 470, 352, 450, 110, fill=GRAY_TINT, name="Practice screen",
          paras=[{"runs": [("Đi kèm: màn hình tập luyện", {"bold": True, "color": NAVY})], "space_after": 4},
                 "--show-features (phím 3, 4) hiện độ duỗi nhẫn, út của người dùng cạnh khoảng của "
                 "IPN (0,4–0,7); màu xanh là đã gập như IPN"],
          size=14, color=DARK, anchor=MID, margin=16)
    notes(s, 11)
    built.append(s)

    # ------------------------------------------- 12. Vòng 3: đường cong học
    hist = lstm_history("run_08")
    man = lstm_manifest("run_08")
    best, smooth_k = man["best_epoch"], man["stop_smooth"]
    epochs = [int(e) for e in hist["epoch"]]
    val_smooth = trailing_mean(hist["val_macro_f1"], smooth_k)
    s = header_slide(prs, "Vòng 3 — Đường cong học của LSTM run_08")
    xr = (0, 110, 20)
    for k, (title, ser, yr, nd) in enumerate([
        ("Loss (càng thấp càng tốt)",
         [dict(name="tập học", pts=list(zip(epochs, hist["train_loss"])), color=NAVY, width=1.75),
          dict(name="kiểm định", pts=list(zip(epochs, hist["val_loss"])), color=RED, width=1.75)],
         (0, 1.6, 0.4), 1),
        ("Macro-F1 mức cửa sổ (càng cao càng tốt)",
         [dict(name="tập học", pts=list(zip(epochs, hist["train_macro_f1"])), color=NAVY, width=1.75),
          dict(name="kiểm định", pts=list(zip(epochs, hist["val_macro_f1"])), color=RED_SOFT, width=1.25),
          dict(name=f"kiểm định, TB {smooth_k} epoch", pts=list(zip(epochs, val_smooth)), color=RED,
               width=2.75)],
         (0, 1.0, 0.2), 1)]):
        gx = 40 + k * 446
        text(s, gx, 78, 434, 24, [[(title, {"bold": True, "color": NAVY})]], size=15)
        lo, hi, _ = yr
        ser.append(dict(name=f"epoch {best} được chọn", pts=[(best, lo), (best, hi)], color=MUTED,
                        width=1.25, dash=True))
        _, plot = xy_chart(s, gx, 102, 434, 272, ser, xr, yr, name=f"Curve {k+1}")
        plot.y_labels(lo, hi, yr[2], nd)
        text(s, plot.px(best, 0, 110) - 40, 104, 80, 18, [f"epoch {best}"], size=12, bold=True,
             color=MUTED, align=C)
    stats = [(f"{len(epochs)} epoch", f"dừng khi macro-F1 kiểm định (TB {smooth_k} epoch) "
                                      f"{man['patience']} epoch không tăng"),
             (f"epoch {best}", f"macro-F1 kiểm định TB {smooth_k} epoch {vn(man['val_macro_f1_smoothed'], 3)}"
                               f" · điểm thô {vn(man['val_macro_f1'], 3)}"),
             (f"{man['n_val']:,}".replace(",", " "),
              "cửa sổ kiểm định, hơn 96% là “không có gì” → F1 thấp hơn tập học")]
    for i, (big, lab) in enumerate(stats):
        cx = 40 + i * 297
        shape(s, cx, 388, 286, 74, fill=GRAY_TINT, name=f"Train stat {i+1}")
        text(s, cx + 14, 388, 112, 74, [big], size=22, bold=True, color=NAVY, anchor=MID)
        text(s, cx + 126, 388, 152, 74, [lab], size=13, color=DARK, anchor=MID)
    notes(s, 12)
    built.append(s)

    # ------------------------------------------- 13. Vòng 3: đổi gì, mất gì
    f7, f8 = per_class_f1("run_07"), per_class_f1("run_08")
    order = ["none", "swipe_left", "swipe_right", "zoom_in", "zoom_out"]
    vi = ["không có gì", "vuốt trái", "vuốt phải", "phóng to", "thu nhỏ"]
    m7 = sum(f7[c] for c in order) / len(order)
    m8 = sum(f8[c] for c in order) / len(order)
    s = header_slide(prs, "Vòng 3 — Học lại đổi được gì, mất gì")
    text(s, 40, 78, 520, 24, [[("F1 từng lớp, mức cửa sổ, tập kiểm định", {"bold": True, "color": NAVY})]],
         size=15)
    bar_chart(s, 40, 102, 540, 262, vi + ["macro-F1"],
              [("run_07", [f7[c] for c in order] + [m7], NAVY_SOFT, DARK),
               ("run_08 (đang dùng)", [f8[c] for c in order] + [m8], NAVY, NAVY)],
              name="Per-class F1", vmax=1.12, gap=70, overlap=-5, label_size=11, cat_size=13)
    text(s, 600, 78, 320, 24, [[("IPN sửa cho nhẫn, út duỗi thẳng", {"bold": True, "color": NAVY})]],
         size=15)
    text(s, 600, 100, 320, 20, ["tỉ lệ cú zoom còn được nhận"], size=13, italic=True, color=MUTED)
    bar_chart(s, 600, 122, 320, 242, ["phóng to", "thu nhỏ"],
              [("run_07", [0.10, 0.35], NAVY_SOFT, DARK),
               ("run_08 (đang dùng)", [0.95, 0.95], RED, RED)],
              name="Zoom robustness", fmt=lambda v: f"{round(v * 100)}%", vmax=1.12, gap=60,
              overlap=-5, label_size=14, cat_size=14)
    shape(s, 40, 376, 880, 86, fill=RED_TINT, line=RED, line_w=1.5, name="Cost",
          paras=[[("Mất gì: ", {"bold": True, "color": RED}),
                  f"macro-F1 trên tay người diễn IPN giảm {vn(m7, 3)} → {vn(m8, 3)}; thu nhỏ "
                  f"{vn(f7['zoom_out'])} → {vn(f8['zoom_out'])} vì mô hình “dễ dãi” hơn với zoom. "
                  "Khi nói chuyện, LSTM một mình thêm 5 lệnh thu nhỏ nhầm (vuốt nhầm 8 → 2) — "
                  "vòng 5 giao zoom cho rừng."]],
          size=15, color=DARK, anchor=MID, margin=18)
    notes(s, 13)
    built.append(s)

    # ------------------------------------------------ 14. Vòng 4: lấy đà
    s = header_slide(prs, "Vòng 4 — Chặn cú “lấy đà”")
    text(s, 40, 78, 660, 22, ["Lời hô từng nhịp 0,2 giây khi người dùng vuốt sang phải"],
         size=14, italic=True, color=MUTED)
    seq = ["R", "R", "·", "L", "L", "L", "R", "R", "R", "R", "R"]
    cw, gap, sx0 = 54, 7, 40
    for k, lab in enumerate(seq):
        if lab == "L":
            fill, col = RED, WHITE
        elif lab == "·":
            fill, col = WHITE, MUTED
        elif k >= 6:
            fill, col = NAVY, WHITE
        else:
            fill, col = GRAY_BAR, DARK
        shape(s, sx0 + k * (cw + gap), 104, cw, 46, fill=fill, line=GRAY_BAR if lab == "·" else None,
              radius=0.15, paras=[lab], size=20, bold=True, color=col, align=C, anchor=MID,
              margin=0, name=f"Tick {k+1}")
    text(s, sx0 + 3 * (cw + gap) - 20, 154, 3 * (cw + gap) + 40, 40,
         ["lấy đà, như vung vợt · độ tin 1,00 → bấm “vuốt trái”"], size=13, bold=True, color=RED, align=C)
    text(s, sx0 + 6 * (cw + gap), 154, 5 * (cw + gap), 40,
         ["cú hất thật → rơi vào 1,2 giây nghỉ, bị bỏ qua"], size=13, bold=True, color=NAVY, align=C)
    shape(s, 724, 82, 196, 112, fill=RED_TINT, name="Problem",
          paras=[{"runs": [("5/20", {"size": 34, "bold": True, "color": RED})], "align": C},
                 {"runs": ["lần vuốt mà slide đi ngược chiều"], "align": C}],
          size=14, color=DARK, anchor=MID, margin=8)
    shape(s, 40, 206, 300, 256, fill=NAVY, name="Fix")
    text(s, 58, 220, 266, 24, [[("Sửa: đòi đồng thuận lâu hơn", {"bold": True, "color": SOFT_WHITE})]], size=15)
    text(s, 58, 246, 266, 60, ["Nâng ngưỡng độ tin không giúp gì — đoạn lấy đà cũng “chắc chắn”"],
         size=15, color=WHITE)
    text(s, 58, 304, 266, 70, [[("4/5", {"size": 50, "bold": True})]], color=WHITE)
    text(s, 58, 378, 266, 76, ["lấy đà ≈ 3 nhịp, cú hất thật 4–5 → đoạn lấy đà không đủ phiếu "
                               "(ngưỡng cũng 0,75 → 0,85)"], size=14, color=SOFT_WHITE)
    table(s, 356, 206, [270, 140, 154],
          [["", "0,75 · 3/5", "0,85 · 4/5"],
           ["Vuốt mà slide đi ngược chiều", "5/20", "2/20"],
           ["Slide tự đổi khi nói chuyện (lần/phút)", "0,64", "0,18"],
           ["Kiểm định: F1 · nhầm mỗi phút", "0,554 · 1,63", "0,600 · 0,77"],
           ["Vuốt / zoom được nhận trên webcam", "60% / 40%", "55% / 20% ← cái giá"],
           ["Độ trễ", "0,62 giây", "0,76 giây"]],
          row_h=40, head_h=40, size=14, red_rows=(4,), name="Op table")
    notes(s, 14)
    built.append(s)

    # ---------------------------------------------- 15. Vòng 5: hai giám khảo
    s = header_slide(prs, "Vòng 5 — Hai giám khảo")
    shape(s, 40, 80, 880, 44, fill=RED_TINT, name="Problem",
          paras=[[("Lần đầu điều khiển slide thật (32 giây): ", {"bold": True}), "4/4 vuốt, nhưng ",
                  ("0/12 cú zoom", {"bold": True, "color": RED}),
                  " thành lệnh — màn hình vẫn hiện “zoom”"]],
          size=16, color=DARK, anchor=MID, margin=16)
    text(s, 40, 134, 540, 22, [[("Độ tin trong năm nhịp liền của một cú thu nhỏ (hộp đen)",
                                 {"bold": True, "color": NAVY})]], size=15)
    lstm_conf = [(1, 0.52), (2, 0.47), (3, 0.61), (4, 0.88), (5, 0.96)]
    rf_conf = [(2, 0.61), (3, 0.62), (4, 0.61), (5, 0.67)]
    frac = (0.10, 0.05, 0.86, 0.72)
    ch, plot = xy_chart(
        s, 40, 158, 540, 304,
        [dict(name="LSTM", pts=lstm_conf, color=RED, width=2.5, marker=True),
         dict(name="Rừng ngẫu nhiên", pts=rf_conf, color=NAVY, width=2.5, marker=True),
         dict(name="ngưỡng vuốt 0,85", pts=[(0.6, 0.85), (5.4, 0.85)], color=RED, width=1.25, dash=True),
         dict(name="ngưỡng zoom mới 0,40", pts=[(0.6, 0.40), (5.4, 0.40)], color=NAVY, width=1.25,
              dash=True)],
        (0.5, 5.5, 1), (0, 1.0, 0.2), name="Two judges", frac=frac, x_labels=False)
    plot.y_labels(0, 1.0, 0.2, 1)
    for k in range(1, 6):
        text(s, plot.px(k, 0.5, 5.5) - 30, plot.py(0, 0, 1) + 4, 60, 18, [f"nhịp {k}"], size=12,
             color=MUTED, align=C)
    # nhãn của đường nằm trên đặt phía trên, đường nằm dưới đặt phía dưới, để không đè nhau
    rf_at = dict(rf_conf)
    for si, pts in ((0, lstm_conf), (1, rf_conf)):
        ser = ch.plots[0].series[si]
        for i, (k, v) in enumerate(pts):
            other = rf_at.get(k) if si == 0 else dict(lstm_conf)[k]
            upper = other is None or v >= other
            label_point(ser.points[i], vn(v), 12, RED if si == 0 else NAVY, True,
                        XL_LABEL_POSITION.ABOVE if upper else XL_LABEL_POSITION.BELOW)
    text(s, plot.px(1, 0.5, 5.5) - 40, plot.py(0.74, 0, 1) - 10, 80, 20, ["rừng: chưa nhận ra"],
         size=11, italic=True, color=NAVY, align=C)
    card(s, 600, 158, 320, 96, "LSTM: nói to, nhưng chắc muộn",
         "chỉ 2 nhịp vượt 0,85 trong khi cần 4 phiếu → không bao giờ đủ", fill=RED_TINT,
         head_color=RED, name="Judge LSTM", size=14, head_size=16)
    card(s, 600, 264, 320, 96, "Rừng: luôn đúng, nhưng nói nhỏ",
         "đúng 12/12 cú; không bao giờ chắc kiểu 0,9 — phóng to chỉ 0,33–0,56", fill=NAVY_TINT,
         head_color=NAVY, name="Judge RF", size=14, head_size=16)
    card(s, 600, 370, 320, 92, "Hạ ngưỡng chung?",
         "về 0,75 · 3/5 thì cú lấy đà của vuốt lại lọt qua", fill=GRAY_TINT,
         name="No common", size=14, head_size=16)
    notes(s, 15)
    built.append(s)

    # ------------------------------------------- 16. Vòng 5: luật riêng
    s = header_slide(prs, "Vòng 5 — Mỗi loại cử chỉ một luật riêng")
    cfg = [("VUỐT", "LSTM", "0,85 · 4/5 — cú lấy đà vẫn bị chặn"),
           ("ZOOM", "Rừng ngẫu nhiên", "0,40 · 3/5 — hợp giọng “nói nhỏ”")]
    for i, (fam, model, thr) in enumerate(cfg):
        shape(s, 40 + i * 446, 80, 434, 48, fill=NAVY_TINT, name=f"Config {fam}",
              paras=[[(fam, {"bold": True, "color": RED}), ("  ←  ", {"color": MUTED}),
                      (model, {"bold": True, "color": NAVY}), ("   " + thr, {"color": DARK})]],
              size=15, anchor=MID, margin=14)
    table(s, 40, 138, [196, 120, 216, 150, 198],
          [["Zoom theo", "Thử slide thật", "20 lời nhắc: đúng / ngược / bỏ lỡ", "Lệnh mỗi lời nhắc",
            "Nhầm khi nói chuyện (lần/phút)"],
           ["LSTM 0,85 · 4/5 (trước)", "0/12", "4 / 1 / 15", "0,62", "0,18"],
           ["Rừng 0,40 · 3/5 (chọn)", "6/12", "10 / 4 / 6", "1,00", "0,18"],
           ["Rừng 0,40 · 2/5", "8/12", "16 / 4 / 0", "1,48", "0,27"],
           ["Rừng 0,50 · 3/5", "5/12", "10 / 2 / 8", "0,90", "0,18"]],
          row_h=32, head_h=44, size=14, hl=(2,), hl_fill="D6E2F2", name="Zoom table")
    whys = [("Vì sao 0,40 · 3/5",
             "0,50: không cú phóng to nào thành lệnh. 2/5: gần như không bỏ lỡ nhưng 1,48 lệnh mỗi "
             "lời nhắc — lúc đưa tay vào, lúc thả lỏng", NAVY_TINT, NAVY),
            ("Vì sao chỉ 6/12",
             "Đổi chiều mỗi ≈ 1,3 giây; mỗi lệnh cần ≈ 1,8 giây (0,6 gom phiếu + 1,2 nghỉ). "
             "Tắt nghỉ thì 9/12", NAVY_TINT, NAVY),
            ("Được / mất",
             "Lần thử hai: 92 giây, 19 lệnh (8 vuốt, 11 zoom). Mất: F1 kiểm định 0,600 → 0,561; "
             "đổi thiết kế gốc (một ngưỡng chung)", RED_TINT, RED)]
    for i, (hd, body, fill, col) in enumerate(whys):
        card(s, 40 + i * 297, 330, 286, 132, hd, body, fill=fill, head_color=col,
             line=RED if col == RED else None, name=f"Why {i+1}", size=14, head_size=16)
    notes(s, 16)
    built.append(s)

    # ---------------------------------------------- 17. Vòng 6: dễ dùng hơn
    s = header_slide(prs, "Vòng 6 — Cho việc điều khiển dễ dùng hơn")
    ux = [("Phím đi nhầm chỗ",
           "Phím vào cửa sổ demo → demo luôn nằm trên cùng; màn hình nhắc bấm vào cửa sổ trình chiếu"),
          ("Phím zoom theo ứng dụng",
           "+ / − cho PowerPoint khi trình chiếu; Ctrl + / Ctrl − cho Google Slides, trình đọc PDF"),
          ("Chiều vuốt theo ý người dùng",
           "Vuốt trái → slide sau, như lật trang điện thoại (thiết kế gốc ngược lại)"),
          ("Tay ra vào khung",
           "66 lần tay vào lại khung trong các phiên đã ghi, không sinh lệnh lạ")]
    for i, (hd, body) in enumerate(ux):
        cx = 40 + (i % 2) * 446
        cy = 80 + (i // 2) * 130
        shape(s, cx, cy, 434, 120, fill=GRAY_TINT, name=f"UX {i+1}")
        badge(s, cx + 16, cy + 16, 32, str(i + 1), fill=NAVY, size=15)
        text(s, cx + 60, cy + 14, 360, 34, [hd], size=18, bold=True, color=NAVY, anchor=MID)
        text(s, cx + 60, cy + 50, 360, 64, [body], size=15, color=DARK)
    text(s, 40, 346, 880, 24,
         [[("Nhịp làm cử chỉ ", {"bold": True, "color": NAVY}),
           ("— màn hình trợ giúp (phím ?) và docs/gestures.md", {"color": MUTED})]], size=16)
    rhythm = [("Không lấy đà ngược chiều", "vòng 4"),
              ("Giơ tay ≈ 1 giây rồi mới làm", "cửa sổ cần 70% ảnh thấy tay"),
              ("Zoom xong giữ yên ≈ 1 giây", "mở rồi chụm ngay: chưa đủ 3 phiếu"),
              ("Cách nhau ≈ 2 giây", "mỗi lệnh chiếm ≈ 1,8 giây")]
    for k, (chip, why) in enumerate(rhythm):
        shape(s, 40 + k * 223, 376, 211, 86, fill=NAVY, radius=0.15, name=f"Rhythm {k+1}",
              paras=[{"runs": [(chip, {"bold": True})], "space_after": 2},
                     {"runs": [(why, {"size": 13, "color": SOFT_WHITE})]}],
              size=15, color=WHITE, align=C, anchor=MID, margin=8)
    notes(s, 17)
    built.append(s)

    # ------------------------------------ 18. Kết quả sau tối ưu: bốn bộ não
    cmp_rows = {r["model"]: r for r in read_csv(MODEL_COMPARISON) if r["split"] == "val"}
    mk = ["rules", "rf", "lstm", "hybrid"]
    mv = ["Luật", "Rừng", "LSTM", "Ghép"]
    ev = [float(cmp_rows[m]["event_f1"]) for m in mk]
    fp = [float(cmp_rows[m]["false_per_min"]) for m in mk]
    mf = [float(cmp_rows[m]["macro_f1"]) for m in mk]
    s = header_slide(prs, "Kết quả sau tối ưu: bốn bộ não ở cấu hình cuối")
    hyb = {(0, 3): RED}
    for k, (title, vals, fmt, vmax) in enumerate([
            ("F1 sự kiện (càng cao càng tốt)", ev, lambda v: vn(v, 3), 0.7),
            ("Lệnh nhầm mỗi phút (càng thấp càng tốt)", fp, lambda v: vn(v), 7.3)]):
        gx = 40 + k * 446
        text(s, gx, 78, 434, 24, [[(title, {"bold": True, "color": NAVY})]], size=15)
        bar_chart(s, gx, 102, 434, 262, mv, [("", vals, NAVY_SOFT, DARK)], name=f"Final {k+1}",
                  fmt=fmt, vmax=vmax, gap=55, legend=False, label_size=15, point_fill=hyb, cat_size=15)
    shape(s, 40, 376, 880, 86, fill=GRAY_TINT, name="Window macro",
          paras=[[("Macro-F1 mức cửa sổ: ", {"bold": True, "color": NAVY})] +
                 [(f"{n} {vn(v, 3)}" + ("   ·   " if i < 3 else ""), {"bold": n == "Ghép"})
                  for i, (n, v) in enumerate(zip(mv, mf))],
                 {"runs": [("27 video kiểm định, cấu hình kích hoạt cuối; LSTM là run_08. "
                            "Tập test vẫn khoá tới lần chạy cuối.", {"italic": True, "color": MUTED,
                                                                    "size": 14})],
                  "space_before": 4}],
          size=16, color=DARK, anchor=MID, margin=18)
    notes(s, 18)
    built.append(s)

    # ------------------------------------------- 19. Những thứ giúp tối ưu nhanh
    s = header_slide(prs, "Những thứ giúp tối ưu nhanh")
    text(s, 40, 80, 520, 22, [[("Học lại 46 thí nghiệm của Phase 8", {"bold": True})]], size=15)
    shape(s, 40, 104, 520, 32, fill=NAVY, kind=MSO_SHAPE.RECTANGLE, paras=["170 phút"],
          size=17, bold=True, color=WHITE, align=R, anchor=MID, margin=10, name="Bar retrain")
    text(s, 40, 146, 520, 22, [[("Đổi luật trợ lý: “tem niêm phong” còn nguyên, chỉ dựng lại bảng",
                                 {"bold": True})]], size=15)
    shape(s, 40, 170, 6, 32, fill=RED, kind=MSO_SHAPE.RECTANGLE, name="Bar replay")
    text(s, 54, 170, 200, 32, [[("0,8 phút", {"bold": True, "size": 20, "color": RED})]], anchor=MID)
    infra = [
        [("Tem niêm phong: ", {"bold": True}),
         "hai lần suýt “rách tem” cả 46 kết quả → nay có kiểm thử tự động chặn"],
        [("Hộp đen của mỗi lần thử: ", {"bold": True}),
         "có “0 thành 6 trên 12” mà không cần người dùng thử lại"],
        [("Một lệnh dựng lại tất cả (run_all.py): ", {"bold": True}),
         "mô hình demo có chỗ cố định; thư viện ghi rõ phiên bản"],
    ]
    for i, it in enumerate(infra):
        y = 226 + i * 78
        badge(s, 40, y + 14, 24, "✓", fill=NAVY, size=12)
        text(s, 76, y, 484, 60, [it], size=15, color=DARK, anchor=MID)
    shape(s, 590, 80, 330, 382, fill=GRAY_TINT, name="Decisions")
    text(s, 608, 92, 300, 24, [[("Quyết định của người dùng", {"bold": True, "color": NAVY})]], size=16)
    dec = [("25/10", "Giữ ngưỡng khởi đầu; chọn cấu hình cuối bằng số đo webcam"),
           ("26/10", "Đổi sang LSTM run_08; tập gập nhẫn, út"),
           ("26/10", "Không ghi lại phiên đọc và gõ phím"),
           ("26/10", "Ngưỡng 0,85 và 4 trên 5 (vòng 4)"),
           ("01/11", "Mô hình ghép; zoom 0,40 và 3 trên 5; phím + / −"),
           ("02/11", "Vuốt trái → slide sau, vuốt phải → slide trước")]
    shape(s, 637, 132, 2, 314, fill=GRAY_BAR, kind=MSO_SHAPE.RECTANGLE, name="Timeline")
    for i, (d, t) in enumerate(dec):
        y = 124 + i * 54
        shape(s, 632, y + 8, 12, 12, fill=RED if i >= 4 else NAVY, kind=MSO_SHAPE.OVAL, name=f"Dot {i+1}")
        text(s, 652, y, 256, 52, [[(d + "  ", {"bold": True, "color": NAVY}), t]], size=14, color=DARK)
    notes(s, 19)
    built.append(s)

    # ---------------------------------------------------- 20. Demo trực tiếp
    s = tpl[1]
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Pt(300), Pt(78), Pt(360), Pt(56)
    t.text_frame.clear()
    fill_tf(t.text_frame, ["DEMO TRỰC TIẾP"], size=36, bold=True, color=WHITE, align=C, anchor=MID)
    text(s, 290, 134, 380, 40,
         ["python scripts/demo.py --model hybrid", "bấm c  ·  bấm chuột vào cửa sổ trình chiếu"],
         size=14, color=SOFT_WHITE, align=C)
    maps = [("Vuốt trái", "slide sau"), ("Vuốt phải", "slide trước"),
            ("Mở ba ngón", "phóng to"), ("Chụm ba ngón", "thu nhỏ")]
    for i, (g, a) in enumerate(maps):
        mx = 318 + (i % 2) * 166
        my = 184 + (i // 2) * 66
        shape(s, mx, my, 158, 56, fill=NAVY_MID, line=SOFT_WHITE, line_w=0.75, name=f"Map {i+1}",
              paras=[[(g, {"bold": True})], [("→ " + a, {"color": SOFT_WHITE, "size": 14})]],
              size=16, color=WHITE, align=C, anchor=MID, margin=4)
    text(s, 300, 326, 360, 44, ["Lần thử 01/11: 92 giây · 19 lệnh", "mọi phím đều tới PowerPoint"],
         size=14, italic=True, color=SOFT_WHITE, align=C)
    notes(s, 20)
    built.append(s)

    # ------------------------------------------- 21. Chưa giải quyết được
    s = header_slide(prs, "Những gì tối ưu chưa giải quyết được")
    text(s, 40, 78, 430, 24, [[("40 lời nhắc trên webcam, lần làm đầu", {"bold": True, "color": NAVY})]],
         size=15)
    bar_chart(s, 40, 102, 430, 210, ["Vuốt", "Zoom"],
              [("Đúng", [11, 10], NAVY, WHITE), ("Ngược chiều", [2, 4], RED, WHITE),
               ("Bỏ lỡ", [7, 6], GRAY_BAR, DARK)],
              name="Webcam outcome", kind=XL_CHART_TYPE.BAR_STACKED, fmt=lambda v: str(int(v)),
              vmax=20, gap=50, overlap=100, label_pos=XL_LABEL_POSITION.CENTER, label_size=16,
              reverse=True, cat_size=16)
    shape(s, 40, 324, 430, 138, fill=RED_TINT, line=RED, line_w=1.5, name="Half missed",
          paras=[{"runs": [("Khoảng một nửa cử chỉ vẫn bị bỏ lỡ", {"bold": True, "color": RED})],
                  "space_after": 4},
                 "Nhẫn, út duỗi; lấy đà; đưa tay vào khung muộn. Không ngưỡng nào sửa hết được → "
                 "phần còn lại là tập luyện theo docs/gestures.md"],
          size=15, color=DARK, anchor=MID, margin=16)
    lims = [("Ngưỡng zoom chọn trên ít dữ liệu",
             "40 lời nhắc, 12 cú zoom — chính dữ liệu đó dùng để chấm → con số hơi lạc quan"),
            ("Trên video IPN, bộ não tốt nhất tuỳ cách đo",
             "Học lại nhiều lần theo công thức gốc: LSTM một mình hơn. Mô hình đang dùng: ghép hơn, "
             "0,561 so với 0,507 → chọn ghép vì kết quả webcam"),
            ("Một yêu cầu của Phase 9 chưa đạt",
             "Mô hình ghép phát 0,61 lệnh mỗi cử chỉ trên video IPN, chưa tới 0,9")]
    for i, (hd, body) in enumerate(lims):
        card(s, 490, 80 + i * 130, 430, 120, hd, body, name=f"Limit {i+1}", size=14, head_size=16)
    notes(s, 21)
    built.append(s)

    # ---------------------------------------------- 22. Bài học về con số
    s = header_slide(prs, "Bài học về độ tin của con số")
    shape(s, 40, 82, 400, 380, fill=RED_TINT, line=RED, line_w=1.5, name="Warning")
    text(s, 64, 100, 352, 90, ["< 0,1"], size=64, bold=True, color=RED)
    text(s, 64, 196, 352, 100,
         ["Khi chỉ chạy một lần, chênh lệch F1 nhỏ thường đảo chiều khi đổi luật của người trợ lý"],
         size=19, bold=True, color=DARK)
    text(s, 64, 310, 352, 110,
         [[("→ chỉ tin kết luận lặp lại qua ", {}),
           ("nhiều lần học hoặc nhiều nhóm người", {"bold": True, "color": RED})]],
         size=17, color=DARK)
    text(s, 466, 82, 454, 26, [[("Đứng vững qua mọi lần dựng lại bảng", {"bold": True, "color": NAVY})]],
         size=17)
    stand = [("LSTM hơn rừng", "→ LSTM là bộ não chính cho vuốt"),
             ("Trộn ngẫu nhiên người: điểm đẹp giả 0,10–0,15",
              "khi cùng người có mặt ở cả tập học lẫn tập chấm → dự án luôn chia theo người"),
             ("Rừng cần gốc toạ độ ở cổ tay", "của ảnh đầu cửa sổ, và cửa sổ dài 1,2 giây")]
    for i, (hd, body) in enumerate(stand):
        y = 116 + i * 118
        shape(s, 466, y, 454, 106, fill=GRAY_TINT, name=f"Stand {i+1}")
        badge(s, 484, y + 16, 30, "✓", fill=NAVY, size=14)
        text(s, 528, y + 12, 376, 32, [hd], size=17, bold=True, color=NAVY, anchor=MID)
        text(s, 528, y + 48, 376, 52, [body], size=15, color=DARK)
    notes(s, 22)
    built.append(s)

    # ------------------------------------------- 23. Việc còn lại, kết luận
    s = header_slide(prs, "Việc còn lại và kết luận")
    text(s, 40, 78, 440, 26, [[("Việc còn lại", {"bold": True, "color": NAVY})]], size=18)
    todo = ["Đo tốc độ 4 bộ não, 2 mức ánh sáng, đo lại lần hai",
            "Đo độ trễ bằng tay: đếm khung hình, 10 lần mỗi cử chỉ",
            "Quay video demo, ghi chú lúc hệ thống làm sai",
            "Quyết định Phase 11; duyệt docs/gestures.md"]
    for i, it in enumerate(todo):
        ty = 110 + i * 36
        shape(s, 40, ty + 7, 16, 16, fill=WHITE, line=NAVY, line_w=1.5, kind=MSO_SHAPE.RECTANGLE,
              name=f"Todo box {i+1}")
        text(s, 66, ty, 420, 30, [it], size=15, color=DARK, anchor=MID)
    shape(s, 40, 262, 440, 76, fill=RED_TINT, line=RED, line_w=1.5, name="Final once",
          paras=[{"runs": [("Cuối cùng, đúng một lần", {"bold": True, "color": RED})], "space_after": 2},
                 "mở khoá tập test · dựng lại môi trường trên máy sạch"],
          size=16, color=DARK, anchor=MID, margin=14)
    shape(s, 500, 80, 420, 258, fill=GRAY_TINT, name="Speed panel")
    text(s, 520, 92, 380, 24, [[("Lần đo tốc độ đầu", {"bold": True, "color": NAVY})]], size=16)
    for k, (big, lab) in enumerate([("≈ 30", "ảnh mỗi giây"), ("≈ 16 ms", "xử lý một ảnh"),
                                    ("3/4", "thời gian là MediaPipe tìm bàn tay")]):
        y = 124 + k * 64
        text(s, 520, y, 150, 56, [big], size=30, bold=True, color=NAVY, anchor=MID)
        text(s, 676, y, 230, 56, [lab], size=15, color=DARK, anchor=MID)
    shape(s, 40, 354, 880, 108, fill=NAVY, name="Conclusion",
          paras=[[("Sáu vòng tối ưu, mỗi vòng ", {"color": SOFT_WHITE}),
                  ("đo trước rồi mới sửa", {"bold": True}),
                  (": slide tự đổi khi không ai làm gì từ 6,6–30 xuống ", {"color": SOFT_WHITE}),
                  ("0,85 lần mỗi phút", {"bold": True}),
                  (", và lần đầu ", {"color": SOFT_WHITE}),
                  ("điều khiển được slide thật", {"bold": True}), (".", {"color": SOFT_WHITE})]],
          size=19, color=WHITE, anchor=MID, margin=22)
    notes(s, 23)
    built.append(s)

    # ------------------------------------------------------------ 24. Cảm ơn
    s = tpl[8]
    t = [sh for sh in s.shapes if sh.name == "Title 6"][0]
    t.left, t.top, t.width, t.height = Pt(420), Pt(200), Pt(510), Pt(80)
    t.text_frame.clear()
    fill_tf(t.text_frame, ["XIN CẢM ƠN!"], size=54, bold=True, color=RED)
    text(s, 420, 286, 510, 34, ["Mời thầy cô và các bạn đặt câu hỏi"], size=20, color=NAVY, margin=7)
    notes(s, 24)
    built.append(s)

    # ------------------------------------------------------ 25. Phụ lục thuật ngữ
    s = header_slide(prs, "Phụ lục — Thuật ngữ")
    terms = [("Điểm mốc", "21 điểm: cổ tay, khớp, đầu ngón, do MediaPipe tìm"),
             ("Cửa sổ", "1,2 giây gần nhất; cứ 0,2 giây xét một cửa sổ mới"),
             ("Nhãn", "câu trả lời của mô hình: cử chỉ nào, hay “không có gì”"),
             ("Độ tin", "mô hình chắc tới đâu về nhãn đó, từ 0 đến 1"),
             ("Lệnh", "một lần thật sự bấm phím, do máy trạng thái quyết định"),
             ("Máy trạng thái", "“người trợ lý” giữa mô hình và bàn phím"),
             ("Đồng thuận k trên n", "cần k nhịp đồng ý trong n nhịp liền mới phát lệnh"),
             ("Recall", "tỉ lệ cử chỉ thật được nhận"),
             ("Precision", "tỉ lệ lệnh phát ra là đúng"),
             ("F1", "một con số gộp precision và recall, từ 0 đến 1"),
             ("Mức cửa sổ / sự kiện", "chấm từng đoạn 1,2 giây / chấm từng lệnh"),
             ("Độ duỗi ngón", "đầu ngón → cổ tay chia gốc ngón → cổ tay; gập ≈ 0,5"),
             ("Ví dụ biến tấu", "ví dụ học tạo bằng cách sửa ví dụ thật"),
             ("Hộp đen", "lưu 21 điểm của một phiên để phát lại qua mọi cấu hình")]
    for k in range(2):
        rows = [["Từ", "Nghĩa"]] + [list(r) for r in terms[k * 7:(k + 1) * 7]]
        table(s, 40 + k * 446, 82, [140, 294], rows, row_h=50, head_h=30, size=14,
              left_cols=(0, 1), name=f"Terms {k+1}")
    notes(s, 25)
    built.append(s)

    # --------------------------------------------- sắp xếp, bỏ slide mẫu thừa
    sldIdLst = prs.slides._sldIdLst
    keep = {id(sl) for sl in built}
    by_slide = {}
    for sldId in list(sldIdLst):
        sl = prs.part.related_slide(sldId.rId)
        by_slide[id(sl)] = sldId
        sldIdLst.remove(sldId)
    for sl in built:
        sldIdLst.append(by_slide[id(sl)])
    for sl_id, sldId in by_slide.items():
        if sl_id not in keep:
            prs.part.drop_rel(sldId.rId)

    prs.save(str(out))

    # ----------------------------------- hậu xử lý: Times New Roman toàn bộ
    face = re.compile(r'<a:(latin|ea|cs) typeface="(?!\+)[^"]*"[^>]*/>')
    parts = ("ppt/slides/", "ppt/slideLayouts/", "ppt/slideMasters/", "ppt/theme/",
             "ppt/notesMasters/", "ppt/notesSlides/", "ppt/charts/", "ppt/presentation.xml")
    tmp = str(out) + ".tmp"
    with zipfile.ZipFile(str(out)) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith(".xml") and item.filename.startswith(parts):
                xml = face.sub(lambda m: f'<a:{m.group(1)} typeface="{FONT}"/>', data.decode("utf-8"))
                data = xml.encode("utf-8")
            zout.writestr(item, data)
    os.replace(tmp, str(out))
    print("saved", out, "slides:", len(built), "notes:", sorted(k for k in NOTES if k != "qa"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="file mẫu .pptx")
    ap.add_argument("--script", type=Path, default=DEFAULT_SCRIPT, help="file kịch bản .md")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="file .pptx ghi ra")
    args = ap.parse_args()
    build(args.template, args.script, args.out)


if __name__ == "__main__":
    main()
