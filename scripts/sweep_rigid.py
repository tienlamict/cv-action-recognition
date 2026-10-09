"""Quét mức tăng cường "bàn tay cứng" của rừng ngẫu nhiên, đo trên tập VAL (Phase 6).

Rừng học vuốt từ cú hất Throw của IPN, luôn mở bàn tay trong lúc hất, nên không
nhận cú vuốt bằng bàn tay giữ nguyên dáng (results/phase6/notes.md mục 7). Thêm
bản "bàn tay cứng" của các cửa sổ vuốt vào tập train sửa được điều đó, nhưng
tay chỉ trỏ cũng là một bàn tay gần như cứng đang di chuyển. Script huấn luyện
lại rừng với từng mức trong AUG_RIGID_SWEEP (số bản trên mỗi cửa sổ vuốt của
train; 0 = không tăng cường) và từng khoảng k trong AUG_RIGID_KEEP_SWEEP (phần
sự đổi dáng tay được giữ lại; (0, 0) = cứng hoàn toàn), rồi đo trên val cả lợi
lẫn giá:

- lợi: cửa sổ vuốt thật của val, giữ k = 0; 0,25; 0,5; 0,75 phần sự đổi dáng
  tay (dáng mốc là bước đầu cửa sổ, tay còn chụm), và bàn tay cứng theo dáng
  xòe nhất (bàn tay mở), còn được nhận đúng bao nhiêu phần. Đo ở mọi mức k là
  để bắt "chỗ trũng": mô hình nhận cả hai đầu mà bỏ khoảng giữa.
  Rung điểm mốc giống hệt nhau cho mọi mô hình (evaluation.probe_windows);
- giá: cửa sổ none bị báo thành cử chỉ — cả lớp none, riêng tay chỉ trỏ
  (POINTING_SRC_LABELS), và số cụm báo nhầm mỗi phút như summarize_log.py;
- cú vuốt tự nhiên của IPN: macro-F1, F1 từng lớp, recall vuốt, mức sự kiện.

Bảng thứ hai (shape_spread) so độ đổi dáng tay của tay THẬT với của các bản
tổng hợp: tay chỉ trỏ di chuyển như vuốt là bàn tay giữ dáng thật, nên nó cho
biết một cú vuốt bàn tay mở thật nằm ở mức k nào — và cột lợi nào đáng tin.

Chọn trên val là hợp lệ (luật 13). Script không lưu mô hình và không sửa
config.py: chọn xong thì đặt AUG_RIGID_SHARE, AUG_RIGID_KEEP rồi chạy lại
train_rf.py.

Ví dụ:
    python scripts/sweep_rigid.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.augment import (SWIPE_LABELS, rigid_hand, shape_scaled,  # noqa: E402
                         usable_steps)
from src.cli import make_parser, setup_console  # noqa: E402
from src.evaluation import (alarm_clusters, event_rows,  # noqa: E402
                            probe_windows, split_features, summarize)
from src.features import FEATURE_NAMES, openness  # noqa: E402
from src.forest import train_forest, training_set  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits  # noqa: E402
from src.tables import write_table  # noqa: E402


def rigid_open(win):
    """Bàn tay cứng theo dáng xòe nhất trong cửa sổ — gần cú vuốt bàn tay mở.
    Chỉ xét các bước có lòng bàn tay bình thường (``augment.usable_steps``)."""
    steps = usable_steps(win)
    return rigid_hand(win, int(steps[np.argmax(openness(win)[steps])]))


#: Phép thăm dò: tên cột → hàm sửa cửa sổ. ``shape_K``: giữ K% sự đổi dáng tay.
PROBES = {**{f"shape_{round(k * 100)}": (lambda w, k=k: shape_scaled(w, k))
             for k in config.PROBE_SHAPE_LEVELS if k < 1},
          "rigid_open": rigid_open}


def variants(shares=config.AUG_RIGID_SWEEP, keeps=config.AUG_RIGID_KEEP_SWEEP):
    """Các cặp ``(share, keep)`` cần huấn luyện; mức 0 không phụ thuộc ``keep``
    nên chỉ chạy một lần."""
    out = []
    for share in shares:
        for keep in (keeps[:1] if share == 0 else keeps):
            out.append((float(share), tuple(float(v) for v in keep)))
    return out


def variant_row(share, keep, n_rigid, y, pred, src_label, clip, t0, probe_hits):
    """Một hàng của bảng quét: mọi số đo trên val của một mô hình.

    Args:
        probe_hits: dict tên phép thăm dò → ``(n,) bool`` cửa sổ vuốt đã sửa
            còn được nhận đúng.
    """
    summary = summarize(y, pred)
    f1 = {r["class"]: r["f1"] for r in summary["per_class"]}
    hits = {r["class"]: r["hit_1"] for r in event_rows(y, pred, clip, t0)}
    swipe = np.isin(y, SWIPE_LABELS)
    none = y == 0
    pointing = none & np.isin(src_label, config.POINTING_SRC_LABELS)
    clusters, minutes = alarm_clusters(y, pred, clip, t0)
    return {"share": share,
            "keep": "" if share == 0 else f"{keep[0]:g}–{keep[1]:g}",
            "n_rigid": int(n_rigid), "macro_f1": summary["macro_f1"],
            **{f"f1_{c}": f1[c] for c in config.CLASSES if c != "none"},
            "swipe_recall": float(np.mean(pred[swipe] == y[swipe])),
            "swipe_events": float(np.mean([hits[config.CLASSES[k]]
                                           for k in SWIPE_LABELS])),
            **{name: float(np.mean(hit)) for name, hit in probe_hits.items()},
            "none_alarm": float(np.mean(pred[none] != 0)),
            "pointing_alarm": float(np.mean(pred[pointing] != 0)),
            "alarm_per_min": clusters / minutes}


def shape_rows(F, y, src_label, probe_features):
    """Độ đổi dáng tay trong một cửa sổ — ``open_range``, ``pinch_range`` — của
    tay THẬT và của các bản tổng hợp, để biết bản tổng hợp nào giống tay thật.

    Tay thật không bao giờ cứng hẳn: điểm mốc rung mạnh hơn khi tay chạy nhanh,
    góc nhìn đổi, ngón tay hơi co duỗi. Lớp none tách theo nhãn gốc, chỉ lấy cửa
    sổ có chuyển động như một cú vuốt theo đúng điều kiện vuốt của luật Phase 5
    (``max_vx > RULE_VX_HI`` và ``|dx| > RULE_DX_HI``): tay chỉ trỏ ở đây chính là
    một bàn tay giữ dáng mà di chuyển như vuốt.

    Args:
        probe_features: dict tên phép thăm dò → ``(n, 15)`` đặc trưng của cửa
            sổ vuốt đã sửa (NaN ở cửa sổ không chuẩn hoá được).

    Returns:
        list dict ``group``, ``n``, ``open_p10/25/50/75``, ``pinch_p50``.
    """
    col = {name: i for i, name in enumerate(FEATURE_NAMES)}
    swipe_motion = ((F[:, col["max_vx"]] > config.require_measured("RULE_VX_HI"))
                    & (np.abs(F[:, col["dx"]]) > config.require_measured("RULE_DX_HI")))
    groups = [("vuốt thật", F[np.isin(y, SWIPE_LABELS)])]
    groups += [(f"vuốt thật, {name}", G[np.isfinite(G).all(axis=1)])
               for name, G in probe_features.items()]
    groups += [(f"none {s}, chuyển động như vuốt",
                F[(y == 0) & (src_label == s) & swipe_motion])
               for s in sorted(set(src_label[y == 0]))]
    rows = []
    for name, G in groups:
        row = {"group": name, "n": int(len(G))}
        if len(G):
            p = np.percentile(G[:, col["open_range"]], [10, 25, 50, 75])
            row.update({f"open_p{q}": float(v) for q, v in zip((10, 25, 50, 75), p)})
            row["pinch_p50"] = float(np.median(G[:, col["pinch_range"]]))
        rows.append(row)
    return rows


COLUMNS = ["share", "keep", "n_rigid", "macro_f1", "f1_swipe_left",
           "f1_swipe_right", "f1_zoom_in", "f1_zoom_out", "swipe_recall",
           "swipe_events", *PROBES, "none_alarm", "pointing_alarm",
           "alarm_per_min"]


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    args = parser.parse_args()

    splits = read_splits()
    with np.load(args.windows, allow_pickle=False) as data:
        data = {k: data[k] for k in data.files}
    F_va, y_va, pick = split_features(data["X"], data["y"], data["presence"],
                                      data["subject"], splits, "val")
    src, clip, t0 = (data[k][pick] for k in ("src_label", "clip", "t0"))
    swipe = np.isin(y_va, SWIPE_LABELS)
    X_swipe = data["X"][pick][swipe].astype(np.float64)
    presence_swipe = data["presence"][pick][swipe]

    rows = []
    for share, keep in variants():
        started = time.perf_counter()
        F_tr, y_tr, n_rigid = training_set(data["X"], data["y"], data["presence"],
                                           data["subject"], splits, share=share,
                                           keep=keep)
        model = train_forest(F_tr, y_tr)
        pred = model.predict(F_va)
        probe_hits, probe_features = {}, {}
        for name, transform in PROBES.items():
            probed, probe_features[name] = probe_windows(
                model.predict, X_swipe, presence_swipe, transform,
                np.random.default_rng(config.SEED))
            probe_hits[name] = probed == y_va[swipe]
        rows.append(variant_row(share, keep, n_rigid, y_va, pred, src, clip, t0,
                                probe_hits))
        print(f"  mức {share:g}, k {rows[-1]['keep'] or '-'}: {n_rigid} bản, "
              f"{time.perf_counter() - started:.1f} s")

    # đặc trưng của cửa sổ đã sửa không phụ thuộc mô hình (cùng rung cho mọi mức)
    shapes = shape_rows(F_va, y_va, src, probe_features)
    run_dir = next_run_dir(config.PHASE6_RESULTS_DIR / "sweep_rigid")
    write_table(rows, COLUMNS, run_dir / "sweep")
    write_table(shapes, ["group", "n", "open_p10", "open_p25", "open_p50",
                         "open_p75", "pinch_p50"], run_dir / "shape_spread")
    write_manifest(run_dir, {
        "script": "sweep_rigid", "variants": variants(),
        "n_val": int(y_va.size), "n_val_swipes": int(swipe.sum()),
        "n_val_pointing": int(np.sum((y_va == 0)
                                     & np.isin(src, config.POINTING_SRC_LABELS)))})

    print(f"\nVal: {y_va.size} cửa sổ, {int(swipe.sum())} cửa sổ vuốt. Cột 'giữ K%': "
          "cú vuốt thật chỉ giữ K% sự đổi dáng tay, còn được nhận bao nhiêu.")
    probe_names = [n.replace("shape_", "giữ ") + ("%" if n.startswith("shape_") else "")
                   for n in PROBES]
    print("  mức  k     macro-F1  sự kiện vuốt | " + "  ".join(
        f"{n:>9}" for n in probe_names) + " | báo nhầm none  tay chỉ trỏ  cụm/phút")
    for r in rows:
        cells = "  ".join(f"{r[n]:>9.0%}" for n in PROBES)
        print(f"  {r['share']:>4g}  {r['keep'] or '-':<5} {r['macro_f1']:8.4f}  "
              f"{r['swipe_events']:12.0%} | {cells} | {r['none_alarm']:13.1%}  "
              f"{r['pointing_alarm']:11.1%}  {r['alarm_per_min']:8.2f}")
    print("\nĐộ xòe biến thiên trong cửa sổ (open_range), p10 / p25 / p50 / p75 — "
          "tay thật so với bản tổng hợp:")
    for r in shapes:
        if r["n"] and (not r["group"].startswith("none ")
                       or any(s in r["group"] for s in config.POINTING_SRC_LABELS)):
            print(f"  {r['group']:<40} {r['open_p10']:5.2f} {r['open_p25']:5.2f} "
                  f"{r['open_p50']:5.2f} {r['open_p75']:5.2f}   (n={r['n']})")
    print(f"\nBảng: {relative_to_root(run_dir)}")
    print("Chọn xong: đặt AUG_RIGID_SHARE và AUG_RIGID_KEEP trong src/config.py, "
          "rồi chạy python scripts/train_rf.py")


if __name__ == "__main__":
    main()
