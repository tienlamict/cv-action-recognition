"""Vẽ boxplot từng đặc trưng theo từng lớp, từ bộ cửa sổ đã dựng.

Viết ở Phase 2, **chạy** ở Phase 4 trên tập train. Ba hình cần nhìn là cổng
kiểm tra của Phase 4 (đổi ngày 2026-10-05, người dùng duyệt):

- pinch_delta: hộp zoom_in hẳn bên dương, zoom_out hẳn bên âm, không chồng nhau
- dx: hai hộp của hai lớp vuốt nằm hai phía của 0
- max_vx: hộp hai lớp vuốt cao hơn hẳn hộp lớp none

Cổng cũ của SPEC dùng open_delta và straightness. Trên IPN, open_delta tách
zoom yếu (zoom của IPN chỉ chụm/mở ba ngón) và straightness không tách cú hất
khỏi none (cú hất có chuẩn bị và thu tay). Hai điều kiện cũ vẫn được in ra
dưới nhóm "tham khảo" để theo dõi, nhưng không quyết định cổng.

Script in kết quả kiểm từng điều bằng phân vị 25/75, nhưng người vẫn phải nhìn
hình. Cũng ghi phân vị 25/75 của mọi đặc trưng theo lớp vào
results/phase4/ipn_feature_ranges.json — Phase 5 dùng file này để kiểm tra bạn
làm cử chỉ có giống IPN không.

Ví dụ:
    python scripts/plot_feature_boxplots.py
    python scripts/plot_feature_boxplots.py --split val
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.features import FEATURE_NAMES, window_features  # noqa: E402
from src.runlog import (next_run_dir, relative_to_root,  # noqa: E402
                        write_manifest)
from src.splits import SPLIT_NAMES, read_splits, split_of  # noqa: E402
from src.viz import plot_boxplots  # noqa: E402

BOX_FEATURES = ("pinch_delta", "dx", "max_vx", "open_delta", "straightness")


def quartiles(F, y):
    """``{lớp: {đặc trưng: {p25, p50, p75}}}``."""
    out = {}
    for k, cls in enumerate(config.CLASSES):
        rows = F[y == k]
        if rows.shape[0] == 0:
            continue
        p25, p50, p75 = np.percentile(rows, [25, 50, 75], axis=0)
        out[cls] = {name: {"p25": float(a), "p50": float(b), "p75": float(c)}
                    for name, a, b, c in zip(FEATURE_NAMES, p25, p50, p75)}
    return out


def _zoom_apart(z, name):
    """Ba điều kiện tách hai hộp zoom trên một đặc trưng có dấu."""
    return [
        (f"{name}: hộp zoom_in hẳn bên dương", z["zoom_in"]["p25"] > 0,
         f"zoom_in p25 = {z['zoom_in']['p25']:+.3f}"),
        (f"{name}: hộp zoom_out hẳn bên âm", z["zoom_out"]["p75"] < 0,
         f"zoom_out p75 = {z['zoom_out']['p75']:+.3f}"),
        (f"{name}: hai hộp zoom không chồng nhau",
         z["zoom_out"]["p75"] < z["zoom_in"]["p25"],
         f"zoom_out p75 {z['zoom_out']['p75']:+.3f} < zoom_in p25 "
         f"{z['zoom_in']['p25']:+.3f}"),
    ]


def gate_checks(q):
    """Kiểm cổng Phase 4 bằng phân vị. Không giả định dấu của ``dx``.

    Returns:
        list ``(nhóm, điều kiện, đạt?, chi tiết)``. Nhóm ``"cổng"`` (năm điều
        kiện: ``pinch_delta`` ×3, ``dx``, ``max_vx``) quyết định cổng. Nhóm
        ``"tham khảo"`` là cổng cũ của SPEC (``open_delta`` ×3,
        ``straightness``), chỉ để theo dõi.
    """
    dx = {c: q[c]["dx"] for c in ("swipe_left", "swipe_right")}
    st = {c: q[c]["straightness"] for c in ("none", "swipe_left", "swipe_right")}
    vx = {c: q[c]["max_vx"] for c in ("none", "swipe_left", "swipe_right")}
    opposite = ((dx["swipe_left"]["p25"] > 0 and dx["swipe_right"]["p75"] < 0)
                or (dx["swipe_left"]["p75"] < 0 and dx["swipe_right"]["p25"] > 0))
    gate = _zoom_apart({c: q[c]["pinch_delta"] for c in ("zoom_in", "zoom_out")},
                       "pinch_delta") + [
        ("dx: hai hộp vuốt nằm hai phía của 0", opposite,
         f"swipe_left [{dx['swipe_left']['p25']:+.3f}, {dx['swipe_left']['p75']:+.3f}], "
         f"swipe_right [{dx['swipe_right']['p25']:+.3f}, {dx['swipe_right']['p75']:+.3f}]"),
        ("max_vx: hộp hai lớp vuốt cao hơn hẳn none",
         min(vx["swipe_left"]["p25"], vx["swipe_right"]["p25"]) > vx["none"]["p75"],
         f"p25 vuốt {vx['swipe_left']['p25']:.2f} / {vx['swipe_right']['p25']:.2f} "
         f"so với p75 none {vx['none']['p75']:.2f}"),
    ]
    reference = _zoom_apart({c: q[c]["open_delta"] for c in ("zoom_in", "zoom_out")},
                            "open_delta") + [
        ("straightness: hộp hai lớp vuốt cao hơn hẳn none",
         min(st["swipe_left"]["p25"], st["swipe_right"]["p25"]) > st["none"]["p75"],
         f"p25 vuốt {st['swipe_left']['p25']:.3f} / {st['swipe_right']['p25']:.3f} "
         f"so với p75 none {st['none']['p75']:.3f}"),
    ]
    return ([("cổng", *c) for c in gate]
            + [("tham khảo", *c) for c in reference])


def gate_passed(checks):
    """Cổng đạt khi mọi điều kiện của nhóm ``"cổng"`` đạt."""
    return all(ok for group, _, ok, _ in checks if group == "cổng")


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ,
                        help="bộ cửa sổ .npz (mặc định %(default)s)")
    parser.add_argument("--split", default="train", choices=SPLIT_NAMES,
                        help="tập để vẽ (mặc định %(default)s)")
    args = parser.parse_args()

    path = Path(args.windows)
    if not path.is_file():
        print(f"Chưa có {relative_to_root(path)}. Bộ cửa sổ được dựng ở "
              "Phase 4 bằng scripts/build_dataset.py.")
        return

    with np.load(path, allow_pickle=False) as data:
        pick = split_of(data["subject"], read_splits()) == args.split
        X, y, presence = data["X"][pick], data["y"][pick], data["presence"][pick]
    F = np.stack([window_features(win, ratio)
                  for win, ratio in zip(X, presence)])

    out_dir = next_run_dir(config.PHASE4_RESULTS_DIR / "boxplots")
    plot_boxplots(F, y, FEATURE_NAMES, out_dir / "features.png")
    for name in BOX_FEATURES:
        column = FEATURE_NAMES.index(name)
        plot_boxplots(F[:, [column]], y, [name], out_dir / f"{name}.png")

    q = quartiles(F, y)
    checks = gate_checks(q)
    if args.split == "train":
        ranges = {"split": "train", "windows": relative_to_root(path),
                  "n_windows": {c: int(np.sum(y == k))
                                for k, c in enumerate(config.CLASSES)},
                  "features": FEATURE_NAMES, "quartiles": q}
        config.IPN_FEATURE_RANGES_JSON.parent.mkdir(parents=True, exist_ok=True)
        config.IPN_FEATURE_RANGES_JSON.write_text(
            json.dumps(ranges, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")

    write_manifest(out_dir, {"script": "plot_feature_boxplots",
                             "windows": relative_to_root(path),
                             "split": args.split, "n_windows": int(X.shape[0]),
                             "gate_passed": gate_passed(checks),
                             "gate": [{"group": g, "check": c, "ok": ok,
                                       "detail": d}
                                      for g, c, ok, d in checks]})

    print(f"{X.shape[0]} cửa sổ tập {args.split} → {relative_to_root(out_dir)}")
    print("\nCổng kiểm tra Phase 4 (theo phân vị 25/75 — vẫn phải nhìn hình):")
    for group, check, ok, detail in checks:
        print(f"  {group:<10}[{'ĐẠT' if ok else 'KHÔNG ĐẠT'}] {check}: {detail}")
    print(f"\nCổng Phase 4: {'ĐẠT' if gate_passed(checks) else 'KHÔNG ĐẠT'} "
          "(chỉ nhóm 'cổng' quyết định; nhóm 'tham khảo' là cổng cũ của SPEC)")
    if args.split == "train":
        print(f"\nPhân vị theo lớp: {relative_to_root(config.IPN_FEATURE_RANGES_JSON)}")


if __name__ == "__main__":
    main()
