"""Biểu đồ so mô hình cũ (IPN thuần) với mô hình mới (IPN + dữ liệu tự quay), Phase 11.

Chỉ đọc kết quả đã lưu của compare_self.py, không chạy lại mô hình nào:
- lần chấm real_test duy nhất: manifest có split real_test và final;
- lần chạy val mới nhất có cột gesture_f1.

Mỗi bên SELF_SEEDS hạt; cột là trung bình, vạch là thấp nhất–cao nhất. Ba hình:

1. cua_so_va_lenh.png: trên real_test, theo lớp. Bên trái là phần trăm cửa sổ nhận
   đúng (mức cửa sổ, mô hình ghép); bên phải là phần trăm lần quay ra lệnh đầu tiên
   đúng, khi thêm SELF_HOLD_SEC giây giữ yên.
2. lenh_p01_test.png: số lần quay ra lệnh đúng trên tổng số, như lúc quay và khi
   thêm giữ yên.
3. val_ipn.png: trên val IPN, macro-F1 cửa sổ của LSTM, F1 lệnh và lệnh nhầm mỗi phút
   của mô hình ghép cộng máy trạng thái.

Ví dụ:
    python scripts/plot_self.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config, selfdata  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.viz import plot_sides  # noqa: E402

SIDES = (("cũ", "cũ: IPN thuần", config.FIG_DEEMPH),
         ("mới", "mới: IPN + dữ liệu tự quay", config.FIG_ACCENT))
AS_RECORDED = "như quay"                          # tên cách đo trong compare_self.py
HOLD = f"+{config.SELF_HOLD_SEC:g} s giữ yên"
PERCENT_TICKS = range(0, 101, 20)


def find_runs(base):
    """``((thư mục, manifest) val, (thư mục, manifest) real_test)``: lần val mới nhất
    có cột gesture_f1, và lần chấm real_test duy nhất.

    Raises:
        SystemExit: thiếu một trong hai, hoặc real_test không có đúng một lần chấm.
    """
    runs = [(path.parent, json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(Path(base).glob(f"run_*/{config.MANIFEST_NAME}"))]
    val = [(d, m) for d, m in runs if m.get("split") == "val" and m.get("windows")
           and "gesture_f1" in m["windows"][0]]
    test = [(d, m) for d, m in runs if m.get("split") == "real_test" and m.get("final")]
    if not val:
        raise SystemExit("Chưa có lần chạy val có cột gesture_f1 — chạy compare_self.py.")
    if len(test) != 1:
        raise SystemExit(f"Cần đúng một lần chấm real_test, thấy {len(test)}.")
    return val[-1], test[0]


def by_side(rows, value, **match):
    """``value(hàng)`` của các hàng khớp ``match``, gom theo bên: ``{bên: [mỗi hạt]}``."""
    out = {side: [] for side, _, _ in SIDES}
    for row in rows:
        if all(row[k] == v for k, v in match.items()):
            out[row["variant"].split()[0]].append(value(row))
    return out


def collect(categories, values_of):
    """``{bên: [[giá trị mỗi hạt] của mỗi nhóm]}`` từ ``values_of(nhóm) → by_side``."""
    out = {side: [] for side, _, _ in SIDES}
    for category in categories:
        for side, values in values_of(category).items():
            out[side].append(values)
    return out


def recall(cls):
    """Hàm ``hàng → phần trăm cửa sổ lớp cls đoán đúng``, từ ma trận nhầm lẫn của hàng."""
    k = config.CLASSES.index(cls)
    return lambda row: 100.0 * row["confusion"][k][k] / sum(row["confusion"][k])


def correct_share(row):
    """Phần trăm lần quay có lệnh đầu tiên đúng."""
    return 100.0 * row["đúng"] / (row["đúng"] + row["nhầm"] + row["sót"])


def figure_data(val, test):
    """Giá trị của ba hình, theo :func:`collect`."""
    gestures = list(selfdata.GESTURES)
    takes = test["takes"]
    return {
        "windows_ok": collect(gestures, lambda c: by_side(test["windows"], recall(c),
                                                          model="hybrid")),
        "takes_ok": collect(gestures, lambda c: by_side(takes, correct_share, how=HOLD,
                                                        **{"class": c})),
        "totals": collect((AS_RECORDED, HOLD), lambda h: by_side(
            takes, lambda r: r["đúng"], how=h, **{"class": "tất cả"})),
        "lstm_f1": collect([""], lambda _: by_side(val["windows"], lambda r: r["macro_f1"],
                                                   model="lstm")),
        "event_f1": collect([""], lambda _: by_side(val["events"], lambda r: r["f1"])),
        "false_per_min": collect([""], lambda _: by_side(val["events"],
                                                         lambda r: r["false_per_min"])),
    }


def take_total(test, variant, how):
    """Số lần quay ra lệnh đúng của một mô hình."""
    return next(r["đúng"] for r in test["takes"] if r["variant"] == variant
                and r["how"] == how and r["class"] == "tất cả")


def upper(*groups):
    """Mức trên của trục dọc: cao hơn giá trị lớn nhất 25% để có chỗ ghi số."""
    return 1.25 * max(v for g in groups for side in g.values() for c in side for v in c)


def main(argv=None):
    setup_console()
    parser = make_parser(__doc__)
    parser.parse_args(argv)
    (val_dir, val), (test_dir, test) = find_runs(config.PHASE11_RESULTS_DIR / "compare_self")
    data = figure_data(val, test)
    run_dir = next_run_dir(config.PHASE11_RESULTS_DIR / "plot_self")
    n_takes, n_seeds = test["n_clips"], len(config.SELF_SEEDS)
    hold = f"thêm {config.SELF_HOLD_SEC:g} s giữ yên"
    demo, pick = f"cũ s{config.SEED}", f"mới s{config.SELF_CANDIDATE_SEED}"
    gestures = list(selfdata.GESTURES)
    percent = {"categories": gestures, "ylim": (0, 112), "yticks": PERCENT_TICKS,
               "fmt": "{:.0f}%"}

    figures = [
        plot_sides(
            [{"title": "Cửa sổ nhận đúng (mức cửa sổ, mô hình ghép)",
              "values": data["windows_ok"], **percent},
             {"title": f"Lần quay ra lệnh đầu tiên đúng ({hold})",
              "values": data["takes_ok"], **percent}],
            SIDES, run_dir / "cua_so_va_lenh.png",
            title="p01-test: mô hình mới nhận vuốt trái tốt hơn hẳn, nhưng lệnh vuốt "
                  "vẫn sót nhiều",
            note=f"{n_takes} lần quay của buổi chưa học, mỗi bên {n_seeds} hạt"),
        plot_sides(
            [{"title": "", "categories": ["như lúc quay", hold], "values": data["totals"],
              "ylim": (0, n_takes * 1.12), "yticks": range(0, n_takes + 1, 10),
              "fmt": "{:.1f}"}],
            SIDES, run_dir / "lenh_p01_test.png",
            title=f"p01-test: số lần quay ra lệnh đầu tiên đúng, trên {n_takes}",
            note=(f"demo đang chạy ({demo}): {take_total(test, demo, AS_RECORDED)} / "
                  f"{take_total(test, demo, HOLD)} · ứng viên {pick}: "
                  f"{take_total(test, pick, AS_RECORDED)} / {take_total(test, pick, HOLD)}")),
        plot_sides(
            [{"title": "LSTM: macro-F1 cửa sổ", "categories": [""],
              "values": data["lstm_f1"], "ylim": (0, upper(data["lstm_f1"], data["event_f1"])),
              "fmt": "{:.3f}"},
             {"title": "Ghép + máy trạng thái: F1 lệnh", "categories": [""],
              "values": data["event_f1"],
              "ylim": (0, upper(data["lstm_f1"], data["event_f1"])), "fmt": "{:.3f}"},
             {"title": "Lệnh nhầm mỗi phút (thấp là tốt)", "categories": [""],
              "values": data["false_per_min"], "ylim": (0, upper(data["false_per_min"])),
              "fmt": "{:.2f}"}],
            SIDES, run_dir / "val_ipn.png",
            title="Val IPN: thêm dữ liệu tự quay không làm hại IPN",
            note=f"{val['windows'][0]['n_windows']} cửa sổ, {val['n_clips']} video "
                 "của những người không có trong tập học"),
    ]

    write_manifest(run_dir, {"script": "plot_self", "val_run": relative_to_root(val_dir),
                             "real_test_run": relative_to_root(test_dir),
                             "figures": [relative_to_root(f) for f in figures],
                             "values": data})
    print(f"Nguồn: {relative_to_root(val_dir)} (val), {relative_to_root(test_dir)} (real_test)")
    for f in figures:
        print(f"  {relative_to_root(f)}")


if __name__ == "__main__":
    main()
