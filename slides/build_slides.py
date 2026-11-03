"""Dựng bộ slide thuyết trình Phase 8–10 từ mẫu HUST.

Không thuộc đường ống nhận dạng: script chỉ đọc file kịch bản và file mẫu trong
docs/, rồi ghi file .pptx. Toạ độ và màu dưới đây là bố cục slide, không phải
hằng số của hệ thống, nên không nằm trong src/config.py.

- **Notes lấy từ kịch bản.** Lời nói, ghi chú và thời lượng của slide N được
  đọc từ mục "## Slide N — ..." của file kịch bản; phần "## Phụ lục — Câu hỏi
  có thể gặp" vào notes của slide cuối. Sửa kịch bản rồi chạy lại là notes khớp.
- **Nội dung trên slide nằm trong code** (hàm build). Đổi số liệu trên slide thì
  sửa ở đó.
- **Font:** mọi chữ, kể cả layout và theme của mẫu, đổi sang Times New Roman.

Cần python-pptx (xem slides/requirements.txt); gói này không có trong
requirements.txt của dự án.

Ví dụ:
    python slides/build_slides.py
    python slides/build_slides.py --out docs/thuyet-trinh-phase-8-10.pptx
"""
import argparse
from pathlib import Path
import copy
import os
import re
import zipfile

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Pt

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = ROOT / "docs" / "HUST_PPT_template_2022_Blue_16x9.pptx"
DEFAULT_SCRIPT = ROOT / "docs" / "kich-ban-thuyet-trinh-phase-8-10.md"
DEFAULT_OUT = ROOT / "docs" / "thuyet-trinh-phase-8-10.pptx"
FONT = "Times New Roman"

NAVY = "00376F"
NAVY_MID = "0B4A8A"
RED = "C00000"
NAVY_TINT = "E8EEF6"
RED_TINT = "FBEAEA"
GRAY_TINT = "F2F4F7"
GRAY_BAR = "B8C2CF"
DARK = "1F2937"
MUTED = "5F6B7A"
WHITE = "FFFFFF"
SOFT_WHITE = "D9E3F0"
NBSP = "\u00a0"

L, C, R = PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.RIGHT
TOP, MID, BOT = MSO_ANCHOR.TOP, MSO_ANCHOR.MIDDLE, MSO_ANCHOR.BOTTOM


def rgb(h):
    return RGBColor.from_string(h)


def keep_together(t):
    """Không cho ngắt dòng giữa số và đơn vị, hay sau dấu ≈."""
    t = t.replace("≈ ", "≈" + NBSP)
    return re.sub(r"(\d) (?=giây|phút|s\b|ms|FPS|lệnh)", lambda m: m.group(1) + NBSP, t)


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
          red_rows=(), name=None):
    """rows[0] là hàng tiêu đề. hl: các hàng tô đậm; red_rows: các hàng tô đỏ nhạt."""
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
                    align=L if j == 0 else C)
    return gf


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


# ------------------------------------------------------- notes từ file kịch bản
def unwrap(block):
    """Gỡ '> ', backtick, '**'; nối các dòng bị ngắt; giữ ranh giới đoạn và gạch đầu dòng."""
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
    if n == 18 and "qa" in NOTES:
        body = (body + "\n\n" + NOTES["qa"]).strip()
    slide.notes_slide.notes_text_frame.text = body


def fsm_row(s, y, h=70, descs=None):
    states = [("IDLE", "chưa thấy tay"), ("READY", "thấy tay, chờ cửa sổ đủ tin"),
              ("CANDIDATE", "gom phiếu k/5"), ("COOLDOWN", "nghỉ 1,2 s sau lệnh")]
    bw, bg = 186, 45
    for i, (nm, desc) in enumerate(states):
        bx = 40 + i * (bw + bg)
        hot = nm == "CANDIDATE"
        shape(s, bx, y, bw, h, fill=RED if hot else NAVY_TINT, line=None if hot else NAVY,
              name=f"State {nm}",
              paras=[{"runs": [(nm, {"bold": True, "size": 17, "color": WHITE if hot else NAVY})],
                      "space_after": 1},
                     {"runs": [(desc, {"size": 14, "color": WHITE if hot else DARK})]}],
              align=C, anchor=MID, margin=4)
        if i < 3:
            shape(s, bx + bw + 7, y + h / 2 - 10, bg - 14, 20, fill=MUTED,
                  kind=MSO_SHAPE.RIGHT_ARROW, name=f"Edge {i+1}")


# ======================================================================= build
def build(template, script_md, out):
    """Dựng 18 slide vào out; notes đọc từ script_md."""
    NOTES.clear()
    NOTES.update(load_notes(script_md))

    prs = Presentation(str(template))
    tpl = list(prs.slides)  # 0 bìa, 1 nền chấm, 2 trang tiêu đề, ..., 8 cảm ơn
    built = []

    # ---------------------------------------------------------------- 1. Mở đầu
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
             "Tối ưu hệ thống: từ nhãn trên màn hình tới lệnh điều khiển slide"],
            size=20, color=NAVY)
    notes(s, 1)
    built.append(s)

    # ---------------------------------------------------- 2. Nhãn chưa phải là lệnh
    s = new_slide(prs, "Title Only", "Nhãn chưa phải là lệnh", 28, NAVY)
    shape(s, 372, 92, 270, 112, fill=GRAY_TINT, name="Model gives",
          paras=[{"runs": [("MÔ HÌNH CHO", {"size": 13, "bold": True, "color": MUTED})], "space_after": 2},
                 {"runs": [("NHÃN", {"size": 26, "bold": True, "color": NAVY})], "space_after": 2},
                 "cho từng cửa sổ 1,2 giây, mỗi 0,2 giây một lần"],
          size=15, color=DARK, margin=14)
    shape(s, 650, 138, 22, 22, fill=RED, kind=MSO_SHAPE.CHEVRON, name="Gap arrow")
    shape(s, 680, 92, 252, 112, fill=NAVY, name="User needs",
          paras=[{"runs": [("NGƯỜI DÙNG CẦN", {"size": 13, "bold": True, "color": SOFT_WHITE})],
                  "space_after": 2},
                 {"runs": [("LỆNH", {"size": 26, "bold": True})], "space_after": 2},
                 "mỗi cử chỉ đúng một lần đổi slide; im lặng khi chỉ nói chuyện"],
          size=15, color=WHITE, margin=14)
    text(s, 372, 216, 560, 26,
         [[("Phase 8 ", {"bold": True, "color": NAVY}), "đo khoảng cách  →  ",
           ("Phase 9–10 ", {"bold": True, "color": NAVY}), "thu hẹp qua ", ("sáu vòng tối ưu", {"bold": True, "color": RED})]],
         size=16)
    rounds = ["Máy trạng thái", "Sửa thước đo", "LSTM run_08", "Chặn lấy đà",
              "Tách ngưỡng zoom", "Trải nghiệm điều khiển"]
    for i, r in enumerate(rounds):
        cx = 372 + (i % 2) * 286
        cy = 252 + (i // 2) * 68
        shape(s, cx, cy, 274, 58, fill=NAVY_TINT, name=f"Round {i+1}")
        badge(s, cx + 12, cy + 12, 34, str(i + 1), size=16)
        text(s, cx + 56, cy, 210, 58, [r], size=17, bold=True, color=NAVY, anchor=MID)
    notes(s, 2)
    built.append(s)

    # ---------------------------------------------------- 3. Tối ưu được bao nhiêu
    s = header_slide(prs, "Tối ưu được bao nhiêu")
    cards = [
        ("Lệnh nhầm mỗi phút, video val IPN", "6,6–30", "0,85", None),
        ("Lệnh nhầm mỗi phút khi nói chuyện có khua tay", "0,64", "0,18", None),
        ("Lời nhắc vuốt phát ngược chiều trước", "5/20", "2/20", None),
        ("Zoom nhận đúng trên tay người dùng", "0/10", "10/20", None),
        ("Thử slide thật: cú zoom thành lệnh", "0/12", "6/12", None),
        ("F1 sự kiện trên video val", "0,559", "0,561", "giữ ngang"),
    ]
    for i, (lab, before, after, tag) in enumerate(cards):
        cx = 40 + (i % 3) * 297
        cy = 82 + (i // 3) * 160
        shape(s, cx, cy, 286, 148, fill=GRAY_TINT, name=f"Delta {i+1}")
        text(s, cx + 18, cy + 12, 250, 44, [lab], size=15, bold=True, color=DARK)
        runs = [(before, {"size": 22, "color": MUTED}), ("  →  ", {"size": 22, "color": MUTED}),
                (after, {"size": 38, "bold": True, "color": NAVY if tag else RED})]
        if tag:
            runs.append(("  " + tag, {"size": 15, "italic": True, "color": MUTED}))
        text(s, cx + 18, cy + 62, 260, 76, [runs], anchor=BOT)
    shape(s, 40, 406, 880, 56, fill=NAVY, name="Config strip",
          paras=[[("Đang dùng — mô hình ghép:  ", {"color": SOFT_WHITE}),
                  ("vuốt ← LSTM", {"bold": True}), (" 0,85 · 4/5   ·   ", {}),
                  ("zoom ← rừng ngẫu nhiên", {"bold": True}), (" 0,40 · 3/5   ·   ", {}),
                  ("pytest: 215 passed", {"color": SOFT_WHITE})]],
          size=16, color=WHITE, anchor=MID, margin=18)
    notes(s, 3)
    built.append(s)

    # ---------------------------------------------------- 4. Đo trước, sửa sau
    s = header_slide(prs, "Cách làm: đo trước, sửa sau")
    quad = [(40, 82), (486, 82), (40, 278), (486, 278)]
    heads = ["Ghi một lần, chấm mọi cấu hình", "Chẩn đoán bằng số đo, không đoán",
             "Mỗi thay đổi chấm trên bốn nguồn", "Chọn điểm đánh đổi từ bảng số đo"]
    for i, ((cx, cy), hd) in enumerate(zip(quad, heads)):
        shape(s, cx, cy, 434, 184, fill=GRAY_TINT, name=f"Method {i+1}")
        badge(s, cx + 16, cy + 14, 32, str(i + 1), fill=NAVY, size=15)
        text(s, cx + 58, cy + 14, 360, 32, [hd], size=18, bold=True, color=NAVY, anchor=MID)
    # 1
    cx, cy = quad[0]
    text(s, cx + 18, cy + 56, 220, 120,
         ["Phiên webcam ghi thành điểm mốc thô, chạy lại qua đúng đường ống của demo"],
         size=15, color=DARK)
    text(s, cx + 246, cy + 52, 176, 60, ["316/316"], size=36, bold=True, color=RED, align=C, anchor=MID)
    text(s, cx + 246, cy + 112, 176, 50, ["câu trả lời trùng lúc chạy thật"],
         size=14, color=MUTED, align=C)
    # 2
    cx, cy = quad[1]
    for k, chip in enumerate(["khoảng cách cái–trỏ", "độ duỗi ngón tay", "góc khớp",
                              "nhãn + độ tin mỗi 0,2 s"]):
        shape(s, cx + 18 + (k % 2) * 203, cy + 62 + (k // 2) * 56, 194, 46, fill=WHITE,
              line=NAVY_TINT, radius=0.5, paras=[chip], size=15, bold=True, color=NAVY,
              align=C, anchor=MID, margin=4, name=f"Probe {k+1}")
    # 3
    cx, cy = quad[2]
    for k, (big, lab) in enumerate([("27", "video val IPN"), ("40", "lời nhắc cử chỉ"),
                                    ("10,9", "phút nói chuyện"), ("2", "lần thử slide")]):
        sx = cx + 18 + k * 101
        text(s, sx, cy + 64, 96, 50, [big], size=30, bold=True, color=RED, align=C, anchor=MID)
        text(s, sx, cy + 116, 96, 50, [lab], size=14, color=DARK, align=C)
    # 4
    cx, cy = quad[3]
    text(s, cx + 18, cy + 58, 398, 120,
         ["Mỗi vòng ghi rõ kết quả và cái giá phải trả.",
          "Các quyết định cấu hình được ghi lại theo ngày (slide 13)."],
         size=15, color=DARK, space_after=8)
    notes(s, 4)
    built.append(s)

    # ---------------------------------------------------- 5. Vòng 1: máy trạng thái
    s = header_slide(prs, "Vòng 1 — Dạy hệ thống biết im lặng")
    probs = [("0,82–0,94", "recall: bắt được cử chỉ", NAVY),
             ("0,05–0,20", "precision: không biết im lặng", RED),
             ("6,6–30", "lệnh nhầm mỗi phút trên video val", RED)]
    for i, (big, lab, col) in enumerate(probs):
        cx = 40 + i * 297
        shape(s, cx, 80, 286, 74, fill=GRAY_TINT, name=f"Problem {i+1}")
        text(s, cx + 14, 80, 130, 74, [big], size=26, bold=True, color=col, anchor=MID)
        text(s, cx + 146, 80, 132, 74, [lab], size=14, color=DARK, anchor=MID)
    text(s, 40, 164, 880, 24,
         [[("Cách sửa: ", {"bold": True, "color": NAVY}),
           "máy trạng thái nằm giữa mô hình và bàn phím"]], size=16)
    fsm_row(s, 194)
    shape(s, 40, 274, 880, 30, fill=RED_TINT, kind=MSO_SHAPE.LEFT_ARROW, name="Reset arrow",
          paras=[[("Mất tay ở bất kỳ trạng thái nào → quên hết, về IDLE", {"bold": True})]],
          size=14, color=RED, align=C, anchor=MID, margin=2)
    shape(s, 40, 318, 880, 144, fill=GRAY_TINT, name="Veto panel")
    text(s, 58, 328, 400, 26, [[("Một chỗ tối ưu trong thiết kế", {"bold": True, "color": NAVY})]],
         size=16)
    seq = ["vuốt", "none", "vuốt", "none", "vuốt"]
    for k, lab in enumerate(seq):
        v = lab == "vuốt"
        shape(s, 58 + k * 70, 366, 62, 40, fill=NAVY if v else GRAY_BAR, radius=0.15,
              paras=[lab], size=15, bold=True, color=WHITE if v else DARK, align=C, anchor=MID,
              margin=0, name=f"Flicker {k+1}")
    text(s, 58, 414, 360, 40, ["chuỗi nhãn nhấp nháy"], size=14, italic=True, color=MUTED)
    text(s, 440, 352, 464, 104,
         [{"runs": [("Đếm phiếu trên cửa sổ trượt: ", {"bold": True}),
                    ("3/5 phiếu → vẫn phát lệnh", {"color": RED, "bold": True})], "space_after": 10},
          [("Bản dùng thật: ", {"bold": True}),
           "cửa sổ khác lớp mà đủ tin là ", ("phiếu phản đối", {"bold": True, "color": NAVY}),
           " → huỷ ngay ứng viên"]],
         size=16, color=DARK, anchor=MID)
    notes(s, 5)
    built.append(s)

    # ---------------------------------------------------- 6. Vòng 1: kết quả
    s = header_slide(prs, "Vòng 1 — Kết quả và cái giá")
    text(s, 40, 80, 470, 26,
         [[("Ngưỡng khởi đầu 0,75 · 3/5, trên video val", {"bold": True, "color": NAVY})]], size=16)
    table(s, 40, 112, [190, 140, 140],
          [["Mô hình", "F1 sự kiện", "Nhầm mỗi phút"],
           ["LSTM", "0,559", "1,46"], ["Ghép", "0,490", "1,33"],
           ["Rừng", "0,405", "0,50"], ["Luật", "0,130", "6,82"]],
          row_h=36, size=16, hl=(1,), name="Round1 table")
    shape(s, 40, 312, 470, 150, fill=GRAY_TINT, name="Min presence",
          paras=[{"runs": [("Đánh đổi MIN_PRESENCE", {"bold": True, "color": NAVY})], "space_after": 6},
                 {"runs": [("Tỉ lệ có tay tối thiểu của cửa sổ", {"color": MUTED, "size": 14})],
                  "space_after": 6},
                 [("0,7 → 1,0: ", {"bold": True}), "mất 3/54 cú vuốt, lệnh nhầm chỉ giảm 3%"],
                 {"runs": [("→ giữ 0,7", {"bold": True, "color": RED})], "space_before": 4}],
          size=16, color=DARK, anchor=MID, margin=18)
    shape(s, 540, 80, 380, 382, fill=RED_TINT, line=RED, line_w=1.5, name="Cost panel")
    text(s, 562, 98, 340, 24, [[("CÁI GIÁ", {"bold": True, "color": RED})]], size=14)
    text(s, 562, 124, 340, 80, ["0,77"], size=60, bold=True, color=RED)
    text(s, 562, 204, 340, 30, ["lệnh mỗi cử chỉ trên video val"], size=17, bold=True, color=DARK)
    # thang 0 → 1,2
    x0, x1, ys = 572, 888, 288
    def sx(v):
        return x0 + v / 1.2 * (x1 - x0)
    shape(s, x0, ys, x1 - x0, 4, fill=GRAY_BAR, kind=MSO_SHAPE.RECTANGLE, name="Scale")
    shape(s, sx(0.9), ys - 12, sx(1.1) - sx(0.9), 28, fill=NAVY, kind=MSO_SHAPE.RECTANGLE,
          name="Target band")
    shape(s, sx(0.77) - 8, ys - 6, 16, 16, fill=RED, kind=MSO_SHAPE.OVAL, name="Marker")
    for v, lab in ((0, "0"), (0.77, "0,77"), (1.2, "1,2")):
        text(s, sx(v) - 30, ys + 20, 60, 20, [lab], size=13, color=MUTED, align=C)
    text(s, sx(0.9) - 20, ys - 40, sx(1.1) - sx(0.9) + 40, 22, ["SPEC 0,9–1,1"], size=13,
         bold=True, color=NAVY, align=C)
    text(s, 562, 344, 340, 100,
         ["Phần thiếu là cử chỉ bị sót, không phải lệnh thừa."],
         size=17, color=DARK)
    notes(s, 6)
    built.append(s)

    # ---------------------------------------------------- 7. Vòng 2: sửa thước đo
    s = header_slide(prs, "Vòng 2 — Sửa thước đo trước khi tối ưu tiếp")
    text(s, 40, 78, 400, 24, [[("Con số đánh lừa", {"bold": True, "color": RED})]], size=16)
    text(s, 486, 78, 434, 24, [[("Cách sửa", {"bold": True, "color": NAVY})]], size=16)
    fixes = [
        ("Độ trễ ra số âm",
         "Chuyển động lớn nhất trong khung 4 giây nhiều khi là lúc thu tay",
         "Đo từ khoảnh khắc chính trên video val, dùng đúng hàm đã gán nhãn dữ liệu"),
        ("“1,00 lệnh mỗi cử chỉ” nhưng recall 0,55",
         "Cử chỉ bị sót và lệnh phát thừa bù cho nhau",
         "Luôn báo kèm recall, số lệnh mỗi lời nhắc và số lệnh phát trùng"),
        ("Nhầm mỗi phút bị pha loãng",
         "Hai kịch bản không thấy tay kéo con số của luật từ 7,39 xuống 2,46",
         "Gộp theo thời lượng; thêm “nhầm mỗi phút có tay” (phiên 10 phút thấy tay 17%, phiên ngắn 89%)"),
    ]
    for i, (hd, why, fix) in enumerate(fixes):
        y = 106 + i * 120
        shape(s, 40, y, 400, 108, fill=RED_TINT, name=f"Trap {i+1}",
              paras=[{"runs": [(hd, {"bold": True, "size": 17, "color": RED})], "space_after": 4},
                     why], size=15, color=DARK, anchor=MID, margin=16)
        shape(s, 450, y + 40, 26, 28, fill=MUTED, kind=MSO_SHAPE.RIGHT_ARROW, name=f"To fix {i+1}")
        shape(s, 486, y, 434, 108, fill=NAVY_TINT, name=f"Fix {i+1}",
              paras=[fix], size=16, color=DARK, anchor=MID, margin=16)
    notes(s, 7)
    built.append(s)

    # ---------------------------------------------------- 8. Vòng 3: run_08
    s = header_slide(prs, "Vòng 3 — Mô hình cho bàn tay thật: LSTM run_08")
    shape(s, 40, 82, 400, 84, fill=RED_TINT, name="Problem",
          paras=[{"runs": [("Vấn đề", {"bold": True, "color": RED})], "space_after": 2},
                 [("run_07 nhận ", {}), ("0/10", {"bold": True}),
                  (" cú zoom; báo vuốt khi tay chụm đứng yên (4 lệnh nhầm / 1,1 phút)", {})]],
          size=15, color=DARK, anchor=MID, margin=14)
    shape(s, 40, 178, 400, 132, fill=GRAY_TINT, name="Diagnosis")
    text(s, 54, 186, 370, 24, [[("Chẩn đoán: độ duỗi nhẫn, út khi zoom", {"bold": True, "color": NAVY})]],
         size=15)
    a0, a1, ay = 64, 416, 252
    def ax(v):
        return a0 + v / 2.2 * (a1 - a0)
    shape(s, a0, ay, a1 - a0, 3, fill=GRAY_BAR, kind=MSO_SHAPE.RECTANGLE, name="Ext axis")
    shape(s, ax(0.5) - 7, ay - 6, 14, 14, fill=NAVY, kind=MSO_SHAPE.OVAL, name="IPN mark")
    shape(s, ax(1.5), ay - 8, ax(2.1) - ax(1.5), 18, fill=RED, kind=MSO_SHAPE.RECTANGLE,
          name="User range")
    text(s, ax(0.5) - 60, ay - 32, 120, 22, ["IPN gập ≈ 0,5"], size=13, bold=True, color=NAVY, align=C)
    text(s, ax(1.5) - 30, ay - 32, ax(2.1) - ax(1.5) + 60, 22, ["người dùng 1,5–2,1"], size=13,
         bold=True, color=RED, align=C)
    for v in (0, 1, 2):
        text(s, ax(v) - 15, ay + 14, 30, 18, [str(v)], size=12, color=MUTED, align=C)
    text(s, 54, 280, 380, 24, ["LSTM chỉ biết dáng ngón của IPN"], size=14, italic=True, color=MUTED)
    shape(s, 40, 322, 400, 140, fill=NAVY, name="Fix",
          paras=[{"runs": [("Cách sửa: run_08 học thêm", {"bold": True, "color": SOFT_WHITE})],
                  "space_after": 6},
                 {"runs": [("• 1/2 cửa sổ zoom mang dáng ngón phụ của bàn tay IPN khác", {})],
                  "space_after": 4},
                 "• 10% cửa sổ bàn tay đứng yên, nhãn none"],
          size=16, color=WHITE, anchor=MID, margin=16)
    table(s, 460, 82, [220, 115, 125],
          [["Cùng dữ liệu, 0,75 · 3/5", "run_07", "run_08"],
           ["Zoom trên webcam", "0/10", "4/10"],
           ["Luyện zoom: in / out / vuốt nhầm", "0 / 2 / 4", "5 / 5 / 0"],
           ["IPN nhẫn, út duỗi: zoom còn nhận", "10% / 35%", "95% / 95%"],
           ["F1 sự kiện val", "0,559", "0,554"]],
          row_h=44, head_h=36, size=14, name="Run table")
    shape(s, 460, 322, 460, 140, fill=RED_TINT, line=RED, line_w=1.5, name="Cost",
          paras=[{"runs": [("Cái giá", {"bold": True, "color": RED})], "space_after": 4},
                 {"runs": ["Precision zoom_out mức cửa sổ giảm — lý do Phase 7 từng bác run_08"],
                  "space_after": 4},
                 "Nói chuyện: thêm 5 lệnh zoom_out nhầm; đổi lại vuốt nhầm 8 → 2"],
          size=15, color=DARK, anchor=MID, margin=16)
    notes(s, 8)
    built.append(s)

    # ---------------------------------------------------- 9. Vòng 4: chặn lấy đà
    s = header_slide(prs, "Vòng 4 — Chọn điểm làm việc: chặn “lấy đà”")
    text(s, 40, 78, 660, 22, ["Chuỗi nhãn từng nhịp 0,2 giây của một lời nhắc vuốt phải"],
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
    lx = sx0 + 3 * (cw + gap)
    text(s, lx - 20, 154, 3 * (cw + gap) + 40, 40, ["lấy đà · độ tin 1,00 → phát swipe_left"],
         size=13, bold=True, color=RED, align=C)
    rx = sx0 + 6 * (cw + gap)
    text(s, rx, 154, 5 * (cw + gap), 40, ["cú hất thật → rơi vào 1,2 s nghỉ, bị bỏ"],
         size=13, bold=True, color=NAVY, align=C)
    shape(s, 724, 82, 196, 112, fill=RED_TINT, name="Problem",
          paras=[{"runs": [("5/20", {"size": 34, "bold": True, "color": RED})], "align": C},
                 {"runs": ["lời nhắc vuốt phát lệnh ngược chiều trước"], "align": C}],
          size=14, color=DARK, anchor=MID, margin=8)
    shape(s, 40, 206, 300, 256, fill=NAVY, name="Fix")
    text(s, 58, 220, 266, 24, [[("Cách sửa", {"bold": True, "color": SOFT_WHITE})]], size=15)
    text(s, 58, 246, 266, 64, ["Không ngưỡng tin cậy nào lọc được — lọc bằng độ dài"],
         size=15, color=WHITE)
    text(s, 58, 304, 266, 70, [[("4/5", {"size": 50, "bold": True})]], color=WHITE)
    text(s, 58, 378, 266, 76,
         ["lấy đà ≈ 3 cửa sổ, cú hất thật 4–5 → đoạn lấy đà không đủ phiếu"],
         size=15, color=SOFT_WHITE)
    table(s, 356, 206, [276, 140, 148],
          [["", "0,75 · 3/5", "0,85 · 4/5"],
           ["Vuốt phát ngược chiều trước", "5/20", "2/20"],
           ["Nói chuyện: nhầm/phút; /phút có tay", "0,64; 2,77", "0,18; 0,79"],
           ["Val: F1 sự kiện; nhầm/phút", "0,554; 1,63", "0,600; 0,77"],
           ["Recall vuốt trên webcam", "0,60", "0,55"],
           ["Recall zoom trên webcam", "0,40", "0,20 ← cái giá"],
           ["Độ trễ trung vị", "0,62 s", "0,76 s"]],
          row_h=36, head_h=40, size=14, red_rows=(5,), name="Op table")
    notes(s, 9)
    built.append(s)

    # ---------------------------------------------------- 10. Vòng 5: chẩn đoán
    s = header_slide(prs, "Vòng 5 — Thử slide thật: 0/12 cú zoom")
    shape(s, 40, 80, 880, 46, fill=RED_TINT, name="Problem",
          paras=[[("Lần thử đầu (32 giây): ", {"bold": True}), "4/4 lệnh vuốt, nhưng ",
                  ("0/12 cú zoom", {"bold": True, "color": RED}),
                  " thành lệnh — dù nhãn zoom hiện đúng trên màn hình"]],
          size=16, color=DARK, anchor=MID, margin=16)
    diag = [
        ("Động tác zoom sạch", "cái–trỏ đi 0,1 ↔ 1,7 lòng bàn tay, đổi trong 0,2–0,4 s rồi giữ yên"),
        ("LSTM tự tin quá muộn", "0,4–0,7 ở đầu chuỗi; vượt 0,85 chỉ ở 1–3 cửa sổ cuối → không đủ 4/5"),
        ("Rừng gán đúng 12/12", "chỉ là thang độ tin thấp hơn: zoom_in 0,33–0,56, zoom_out 0,5–0,75"),
        ("Không hạ được ngưỡng chung", "về 0,75 · 3/5 thì lấy đà của vuốt trở lại: 5/20"),
    ]
    for i, (hd, body) in enumerate(diag):
        cx = 40 + (i % 2) * 302
        cy = 138 + (i // 2) * 124
        shape(s, cx, cy, 292, 114, fill=GRAY_TINT, name=f"Diag {i+1}",
              paras=[{"runs": [(hd, {"bold": True, "size": 17, "color": NAVY})], "space_after": 4},
                     body], size=15, color=DARK, margin=14)
    shape(s, 40, 392, 594, 70, fill=NAVY, name="Fix",
          paras=[{"runs": [("Cách sửa: mỗi họ cử chỉ một ngưỡng", {"bold": True})], "space_after": 2},
                 {"runs": [("vuốt giữ nguyên LSTM 0,85 · 4/5; zoom lấy từ rừng với ngưỡng riêng",
                            {"color": SOFT_WHITE})]}],
          size=16, color=WHITE, anchor=MID, margin=16)
    shape(s, 650, 138, 270, 324, fill=GRAY_TINT, line=NAVY, line_w=1.5, name="Result")
    text(s, 668, 150, 236, 22, [[("KẾT QUẢ", {"bold": True, "color": NAVY})]], size=14)
    text(s, 668, 174, 236, 50,
         [[("0/12", {"color": MUTED, "size": 24}), (" → ", {"color": MUTED, "size": 24}),
           ("6/12", {"bold": True, "size": 36, "color": RED})]], anchor=BOT)
    text(s, 668, 228, 236, 50, ["chạy lại đúng phiên thử; cả 6 cú đúng chiều"], size=14, color=DARK)
    text(s, 668, 300, 236, 50, [[("92 s · 19 lệnh", {"bold": True, "size": 28, "color": NAVY})]],
         anchor=BOT)
    text(s, 668, 354, 236, 96, ["lần thử thứ hai: 8 vuốt, 11 zoom, mọi phím đều được gửi"],
         size=14, color=DARK)
    notes(s, 10)
    built.append(s)

    # ---------------------------------------------------- 11. Vòng 5: chọn ngưỡng
    s = header_slide(prs, "Vòng 5 — Chọn ngưỡng cho zoom")
    table(s, 40, 80, [160, 140, 160, 110, 110, 200],
          [["Zoom", "Thử slide (có nghỉ / bỏ nghỉ)", "20 lời nhắc: đúng / ngược / sót",
            "Lệnh mỗi lời nhắc", "Nhầm khi nói chuyện", "Val: F1; nhầm/phút"],
           ["LSTM 0,85 · 4/5 (trước)", "0/12, —", "4 / 1 / 15", "0,62", "0,18", "0,600; 0,77"],
           ["Rừng 0,40 · 3/5 (chọn)", "6/12, 9/12", "10 / 4 / 6", "1,00", "0,18", "0,561; 0,85"],
           ["Rừng 0,40 · 2/5", "8/12, 11/12", "16 / 4 / 0", "1,48", "0,27", "0,525; 1,33"],
           ["Rừng 0,50 · 3/5", "5/12, 5/12", "10 / 2 / 8", "0,90", "0,18", "0,581; 0,68"]],
          row_h=36, head_h=48, size=14, hl=(2,), hl_fill="D6E2F2", name="Zoom table")
    whys = [
        ("Vì sao 0,40, không 0,50", "độ tin zoom_in trên tay người dùng phần lớn dưới 0,50 → ở 0,50 "
                                   "không cú zoom_in nào thành lệnh khi thử trực tiếp", NAVY_TINT, NAVY),
        ("Vì sao 3/5, không 2/5", "2/5 gần như không sót, nhưng 1,48 lệnh mỗi lời nhắc — phần lớn là "
                                 "động tác chuẩn bị và thu tay", NAVY_TINT, NAVY),
        ("Cái giá", "F1 sự kiện val 0,600 → 0,561; đổi thiết kế so với một ngưỡng chung của SPEC "
                    "(người dùng đã chọn)", RED_TINT, RED),
    ]
    for i, (hd, body, fill, col) in enumerate(whys):
        cx = 40 + i * 297
        shape(s, cx, 282, 286, 180, fill=fill, line=RED if col == RED else None, line_w=1.5,
              name=f"Why {i+1}",
              paras=[{"runs": [(hd, {"bold": True, "size": 17, "color": col})], "space_after": 6},
                     body], size=15, color=DARK, margin=16)
    notes(s, 11)
    built.append(s)

    # ---------------------------------------------------- 12. Vòng 6: trải nghiệm
    s = header_slide(prs, "Vòng 6 — Trải nghiệm điều khiển")
    ux = [("Phím gửi nhầm cửa sổ",
           "Lần thử đầu, phím đi vào cửa sổ demo → demo luôn nằm trên cùng; nhắc bấm vào cửa sổ trình chiếu"),
          ("Phím zoom theo ứng dụng",
           "+ / − cho PowerPoint khi trình chiếu; Ctrl + / Ctrl − cho Google Slides, trình đọc PDF"),
          ("Ánh xạ theo người dùng",
           "Vuốt trái → slide sau, vuốt phải → slide trước, như lật trang cảm ứng (SPEC gốc ngược lại)"),
          ("Tay ra vào khung",
           "66 lần vào lại trong các phiên đã ghi, không sinh lệnh lạ")]
    for i, (hd, body) in enumerate(ux):
        cx = 40 + (i % 2) * 446
        cy = 80 + (i // 2) * 130
        shape(s, cx, cy, 434, 120, fill=GRAY_TINT, name=f"UX {i+1}")
        badge(s, cx + 16, cy + 16, 32, str(i + 1), fill=NAVY, size=15)
        text(s, cx + 60, cy + 14, 360, 34, [hd], size=18, bold=True, color=NAVY, anchor=MID)
        text(s, cx + 60, cy + 50, 360, 64, [body], size=15, color=DARK)
    text(s, 40, 346, 880, 24,
         [[("Nhịp làm cử chỉ ", {"bold": True, "color": NAVY}),
           ("— ghi lên màn hình trợ giúp và docs/gestures.md", {"color": MUTED})]], size=16)
    for k, chip in enumerate(["Không lấy đà ngược chiều", "Giơ tay ≈ 1 s rồi mới làm",
                              "Zoom xong giữ yên ≈ 1 s", "Các cử chỉ cách nhau ≈ 2 s"]):
        shape(s, 40 + k * 223, 378, 211, 58, fill=NAVY, radius=0.3, paras=[chip], size=16,
              bold=True, color=WHITE, align=C, anchor=MID, margin=6, name=f"Rhythm {k+1}")
    text(s, 40, 440, 880, 22, ["“Giơ tay trước” vì cửa sổ 1,2 giây cần 70% số bước có tay"],
         size=13, italic=True, color=MUTED)
    notes(s, 12)
    built.append(s)

    # ---------------------------------------------------- 13. Hạ tầng
    s = header_slide(prs, "Hạ tầng: để mỗi vòng chỉ mất vài phút")
    text(s, 40, 80, 520, 22, [[("Học lại 46 thí nghiệm của Phase 8", {"bold": True})]], size=15)
    shape(s, 40, 104, 520, 32, fill=NAVY, kind=MSO_SHAPE.RECTANGLE, paras=["170 phút"],
          size=17, bold=True, color=WHITE, align=R, anchor=MID, margin=10, name="Bar retrain")
    text(s, 40, 146, 520, 22, [[("Đổi máy trạng thái: chỉ dựng lại bảng từ bản ghi", {"bold": True})]],
         size=15)
    shape(s, 40, 170, 6, 32, fill=RED, kind=MSO_SHAPE.RECTANGLE, name="Bar replay")
    text(s, 54, 170, 200, 32, [[("0,8 phút", {"bold": True, "size": 20, "color": RED})]], anchor=MID)
    infra = [
        [("bench.py analyze: ", {"bold": True}), "4 mô hình × 4 cấu hình, mọi phiên, trong 1–2,5 phút"],
        [("Log của demo kèm điểm mốc: ", {"bold": True}), "chạy lại lần thử thật dưới cấu hình mới (0/12 → 6/12)"],
        [("Bản ghi băm theo cấu hình: ", {"bold": True}), "hai lần suýt hết hạn cả 46 bản ghi → nay có kiểm thử chặn"],
        [("run_all.py ", {"bold": True}), "dựng lại toàn bộ; requirements.txt ghim phiên bản"],
    ]
    for i, it in enumerate(infra):
        y = 222 + i * 60
        badge(s, 40, y + 12, 24, "✓", fill=NAVY, size=12)
        text(s, 76, y, 484, 52, [it], size=15, color=DARK, anchor=MID)
    shape(s, 590, 80, 330, 382, fill=GRAY_TINT, name="Decisions")
    text(s, 608, 92, 300, 24, [[("Quyết định của người dùng", {"bold": True, "color": NAVY})]], size=16)
    dec = [("25/10", "Ngưỡng khởi đầu 0,75 · 3/5; chốt cấu hình bằng số đo webcam"),
           ("26/10", "LSTM của demo đổi sang run_08; luyện gập nhẫn, út"),
           ("26/10", "Không ghi lại phiên đọc và gõ phím"),
           ("26/10", "Ngưỡng 0,85 · 4/5"),
           ("01/11", "Mô hình ghép, zoom 0,40 · 3/5, phím + / −"),
           ("02/11", "Vuốt trái → slide sau, vuốt phải → slide trước")]
    shape(s, 637, 132, 2, 314, fill=GRAY_BAR, kind=MSO_SHAPE.RECTANGLE, name="Timeline")
    for i, (d, t) in enumerate(dec):
        y = 124 + i * 54
        shape(s, 632, y + 8, 12, 12, fill=RED if i >= 4 else NAVY, kind=MSO_SHAPE.OVAL,
              name=f"Dot {i+1}")
        text(s, 652, y, 256, 52, [[(d + "  ", {"bold": True, "color": NAVY}), t]], size=14, color=DARK)
    notes(s, 13)
    built.append(s)

    # ---------------------------------------------------- 14. Demo trực tiếp
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
    text(s, 300, 326, 360, 44, ["Lần thử 01/11: 92 giây · 19 lệnh", "mọi phím đều được gửi"],
         size=14, italic=True, color=SOFT_WHITE, align=C)
    notes(s, 14)
    built.append(s)

    # ---------------------------------------------------- 15. Chưa giải quyết được
    s = header_slide(prs, "Những gì tối ưu chưa giải quyết được")
    lims = [
        ("≈ 1/2 cử chỉ bị sót ở lần làm đầu",
         "40 lời nhắc — vuốt 11 đúng · 2 ngược · 7 sót; zoom 10 · 4 · 6. Do nhẫn, út duỗi, lấy đà, tay vào muộn"),
        ("Ngưỡng chọn trên ít dữ liệu",
         "40 lời nhắc, 12 cú zoom, chấm trên chính dữ liệu đó → con số hơi lạc quan"),
        ("“0,9–1,1 lệnh mỗi cử chỉ” trên video val",
         "Mục tiêu của Phase 9 vẫn chưa đạt: 0,61"),
    ]
    for i, (hd, body) in enumerate(lims):
        y = 84 + i * 126
        badge(s, 40, y + 4, 36, "!", size=18)
        text(s, 90, y, 380, 30, [hd], size=18, bold=True, color=DARK)
        text(s, 90, y + 34, 380, 80, [body], size=15, color=MUTED)
    shape(s, 500, 84, 420, 378, fill=NAVY, name="IPN caveat")
    text(s, 524, 100, 372, 60, ["Trên IPN, lựa chọn tốt nhất tuỳ phép đo"], size=19, bold=True,
         color=WHITE)
    shape(s, 524, 160, 372, 88, fill=NAVY_MID, name="Caveat a",
          paras=[{"runs": [("Học lại, trung bình 5 seed", {"color": SOFT_WHITE, "size": 14})],
                  "space_after": 2},
                 [("LSTM một mình hơn ghép ", {}), ("+0,105", {"bold": True, "size": 22})],
                 [("F1 sự kiện", {"color": SOFT_WHITE, "size": 14})]],
          size=16, color=WHITE, anchor=MID, margin=14)
    shape(s, 524, 260, 372, 88, fill=NAVY_MID, name="Caveat b",
          paras=[{"runs": [("Mô hình đang dùng (run_08)", {"color": SOFT_WHITE, "size": 14})],
                  "space_after": 2},
                 [("Ghép ", {}), ("0,561", {"bold": True, "size": 22}),
                  ("  so với LSTM ", {}), ("0,507", {"bold": True, "size": 22})]],
          size=16, color=WHITE, anchor=MID, margin=14)
    text(s, 524, 364, 372, 80,
         [[("Mô hình ghép được chọn vì kết quả trên webcam: ", {"bold": True}),
           "phát được zoom trên tay người dùng mà không tăng nhầm khi nói chuyện."]],
         size=15, color=WHITE)
    notes(s, 15)
    built.append(s)

    # ---------------------------------------------------- 16. Bài học về con số
    s = header_slide(prs, "Bài học về độ tin của con số")
    shape(s, 40, 82, 400, 380, fill=RED_TINT, line=RED, line_w=1.5, name="Warning")
    text(s, 64, 100, 352, 90, ["< 0,1"], size=64, bold=True, color=RED)
    text(s, 64, 196, 352, 120,
         ["Chênh lệch F1 sự kiện trong một seed thường lật chiều khi đổi cấu hình kích hoạt"],
         size=19, bold=True, color=DARK)
    text(s, 64, 300, 352, 110,
         [[("→ chỉ tin kết luận có ", {}), ("nhiều seed, nhiều fold", {"bold": True, "color": RED}),
           (" hoặc chênh lệch thật lớn", {})]],
         size=17, color=DARK)
    text(s, 466, 82, 454, 26, [[("Đứng qua cả bốn lần dựng bảng", {"bold": True, "color": NAVY})]],
         size=17)
    stand = [("LSTM hơn rừng ngẫu nhiên", "→ LSTM là mô hình chính cho vuốt"),
             ("Chia ngẫu nhiên thổi phồng 0,10–0,15", "macro-F1 khi chia theo cửa sổ → dự án luôn chia theo người"),
             ("Rừng cần gốc toạ độ ở cổ tay frame đầu", "và cửa sổ 1,2 giây")]
    for i, (hd, body) in enumerate(stand):
        y = 116 + i * 118
        shape(s, 466, y, 454, 106, fill=GRAY_TINT, name=f"Stand {i+1}")
        badge(s, 484, y + 16, 30, "✓", fill=NAVY, size=14)
        text(s, 528, y + 12, 376, 32, [hd], size=18, bold=True, color=NAVY, anchor=MID)
        text(s, 528, y + 48, 376, 52, [body], size=15, color=DARK)
    notes(s, 16)
    built.append(s)

    # ---------------------------------------------------- 17. Việc còn lại, kết luận
    s = header_slide(prs, "Việc còn lại và kết luận")
    text(s, 40, 78, 440, 26, [[("Việc còn lại", {"bold": True, "color": NAVY})]], size=18)
    todo = ["Đo tốc độ đủ 4 mô hình, 2 mức ánh sáng, đo lại lần hai",
            "Đo độ trễ thủ công, 10 lần mỗi cử chỉ",
            "Quay video demo, ghi chú các trường hợp sai",
            "Quyết định Phase 11; duyệt docs/gestures.md"]
    for i, it in enumerate(todo):
        ty = 110 + i * 36
        shape(s, 40, ty + 7, 16, 16, fill=WHITE, line=NAVY, line_w=1.5, kind=MSO_SHAPE.RECTANGLE,
              name=f"Todo box {i+1}")
        text(s, 66, ty, 420, 30, [it], size=15, color=DARK, anchor=MID)
    shape(s, 40, 262, 440, 76, fill=RED_TINT, line=RED, line_w=1.5, name="Final once",
          paras=[{"runs": [("Cuối cùng, đúng một lần", {"bold": True, "color": RED})], "space_after": 2},
                 "chạy tập test · thử tái lập từ đầu bằng run_all.py"],
          size=16, color=DARK, anchor=MID, margin=14)
    shape(s, 500, 80, 420, 258, fill=GRAY_TINT, name="Speed panel")
    text(s, 520, 92, 380, 24, [[("Lần đo tốc độ đầu", {"bold": True, "color": NAVY})]], size=16)
    for k, (big, lab) in enumerate([("≈ 30", "FPS"), ("≈ 16 ms", "mỗi khung hình"),
                                    ("76–79%", "thời gian là MediaPipe")]):
        y = 124 + k * 58
        text(s, 520, y, 150, 52, [big], size=28, bold=True, color=NAVY, anchor=MID)
        text(s, 676, y, 230, 52, [lab], size=15, color=DARK, anchor=MID)
    text(s, 520, 300, 380, 30, [[("pytest -q: ", {"bold": True}), "215 passed"]], size=15, color=DARK)
    shape(s, 40, 354, 880, 108, fill=NAVY, name="Conclusion",
          paras=[[("Sáu vòng tối ưu, mỗi vòng ", {"color": SOFT_WHITE}),
                  ("đo trước rồi mới sửa", {"bold": True}),
                  (": lệnh nhầm trên video val từ 6,6–30 xuống ", {"color": SOFT_WHITE}),
                  ("0,85 mỗi phút", {"bold": True}),
                  (", và lần đầu ", {"color": SOFT_WHITE}),
                  ("điều khiển được slide thật", {"bold": True}), (".", {"color": SOFT_WHITE})]],
          size=19, color=WHITE, anchor=MID, margin=22)
    notes(s, 17)
    built.append(s)

    # ---------------------------------------------------- 18. Cảm ơn
    s = tpl[8]
    t = [sh for sh in s.shapes if sh.name == "Title 6"][0]
    t.left, t.top, t.width, t.height = Pt(420), Pt(200), Pt(510), Pt(80)
    t.text_frame.clear()
    fill_tf(t.text_frame, ["XIN CẢM ƠN!"], size=54, bold=True, color=RED)
    text(s, 420, 286, 510, 34, ["Mời thầy cô và các bạn đặt câu hỏi"], size=20, color=NAVY, margin=7)
    notes(s, 18)
    built.append(s)

    # ------------------------------------------------- sắp xếp, bỏ slide mẫu thừa
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

    # --------------------------------------- hậu xử lý: Times New Roman toàn bộ
    FACE = re.compile(r'<a:(latin|ea|cs) typeface="(?!\+)[^"]*"[^>]*/>')
    PARTS = ("ppt/slides/", "ppt/slideLayouts/", "ppt/slideMasters/", "ppt/theme/",
             "ppt/notesMasters/", "ppt/notesSlides/", "ppt/charts/", "ppt/presentation.xml")
    tmp = str(out) + ".tmp"
    with zipfile.ZipFile(str(out)) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith(".xml") and item.filename.startswith(PARTS):
                xml = FACE.sub(lambda m: f'<a:{m.group(1)} typeface="{FONT}"/>', data.decode("utf-8"))
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
