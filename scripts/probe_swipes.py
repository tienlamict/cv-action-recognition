"""Thăm dò: rừng ngẫu nhiên coi cái gì là một cú vuốt?

Lấy các cửa sổ vuốt THẬT của tập val mà mô hình đang nhận đúng, sửa đúng một
khía cạnh của chuyển động, rồi xem mô hình còn nhận ra không:

- phản thực tế: bàn tay cứng (giữ nguyên quỹ đạo cổ tay, dáng tay không đổi);
  đi ra rồi quay về (sau bước cổ tay nhanh nhất, cổ tay đi ngược lại đường cũ);
  cổ tay đứng yên (dáng tay vẫn đổi như thật);
- liều lượng: giữ k phần sự đổi dáng tay (PROBE_SHAPE_LEVELS), hoặc nhân quãng
  dời cổ tay với a (PROBE_MOTION_LEVELS).

Mọi cửa sổ đã sửa đều cộng rung điểm mốc AUG_NOISE_SIGMA, rồi đi qua đúng
normalize_window và window_features như lúc chạy thật. Kết quả cho biết vì sao
một cú vuốt "kiểu thông thường" có thể không được nhận — xem results/phase6/notes.md.

Ví dụ:
    python scripts/probe_swipes.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.evaluation import split_features  # noqa: E402
from src.features import FEATURE_NAMES, window_features  # noqa: E402
from src.forest import load_bundle  # noqa: E402
from src.preprocess import normalize_window  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits  # noqa: E402
from src.tables import write_table  # noqa: E402

W = config.WRIST
COL = {name: i for i, name in enumerate(FEATURE_NAMES)}
SWIPES = (config.CLASSES.index("swipe_left"), config.CLASSES.index("swipe_right"))


def rigid_hand(win):
    """Mọi frame dùng dáng tay của frame đầu, đặt tại vị trí cổ tay hiện tại."""
    return shape_scaled(win, 0.0)


def shape_scaled(win, k):
    """Giữ ``k`` phần sự đổi dáng tay (so với frame đầu); quỹ đạo cổ tay giữ nguyên."""
    pose0 = win[0] - win[0, W]
    pose = win - win[:, W:W + 1]
    return win[:, W:W + 1] + pose0[None] + k * (pose - pose0[None])


def motion_scaled(win, a):
    """Nhân quãng dời của cổ tay (so với frame đầu) với ``a``; dáng tay giữ nguyên."""
    wrist = win[:, W]
    return win - wrist[:, None] + (wrist[0] + a * (wrist - wrist[0]))[:, None]


def static_wrist(win):
    """Cổ tay đứng yên ở vị trí frame đầu; dáng tay vẫn đổi như thật."""
    return motion_scaled(win, 0.0)


def out_and_back(win):
    """Sau bước cổ tay đi nhanh nhất, cổ tay đi ngược lại theo đúng đường vừa
    đi (đối xứng thời gian quanh bước đó) — kiểu "vuốt rồi kéo tay về ngay"."""
    wrist = win[:, W]
    peak = int(np.nanargmax(np.linalg.norm(np.diff(wrist, axis=0), axis=1))) + 1
    new = wrist.copy()
    for t in range(peak + 1, len(win)):
        new[t] = wrist[max(0, 2 * peak - t)]
    return win - wrist[:, None] + new[:, None]


def probe(model, windows, ratios, label, transform, rng):
    """Áp ``transform`` lên từng cửa sổ, cộng rung, chuẩn hoá, dự đoán.

    Returns:
        dict: tỉ lệ còn nhận đúng, tỉ lệ từng lớp đoán, và trung vị vài đặc trưng.
    """
    feats, preds = [], []
    for win, ratio in zip(windows, ratios):
        changed = transform(win)
        changed = changed + rng.normal(0.0, config.AUG_NOISE_SIGMA, changed.shape)
        try:
            f = window_features(normalize_window(changed), ratio)
        except ValueError:
            preds.append(-1)
            continue
        feats.append(f)
        preds.append(int(model.predict(f.reshape(1, -1))[0]))
    preds, feats = np.array(preds), np.stack(feats)
    out = {"kept": float(np.mean(preds == label))}
    out.update({f"to_{c}": float(np.mean(preds == k)) for k, c in enumerate(config.CLASSES)})
    for name in ("open_range", "pinch_range"):
        out[name] = float(np.median(feats[:, COL[name]]))
    out["abs_dx"] = float(np.median(np.abs(feats[:, COL["dx"]])))
    out["max_vx"] = float(np.median(feats[:, COL["max_vx"]]))
    return out


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    args = parser.parse_args()

    with np.load(args.windows, allow_pickle=False) as data:
        F, y, pick = split_features(data["X"], data["y"], data["presence"],
                                    data["subject"], read_splits(), "val")
        X, presence = data["X"][pick].astype(np.float64), data["presence"][pick]
    model = load_bundle()["model"]
    pred = model.predict(F)
    rng = np.random.default_rng(config.SEED)

    experiments = [("gốc (chỉ cộng rung)", lambda w: w),
                   ("bàn tay cứng", rigid_hand),
                   ("đi ra rồi quay về", out_and_back),
                   ("cổ tay đứng yên", static_wrist)]
    experiments += [(f"giữ {k:.0%} đổi dáng tay", lambda w, k=k: shape_scaled(w, k))
                    for k in config.PROBE_SHAPE_LEVELS]
    experiments += [(f"quãng dời ×{a:g}", lambda w, a=a: motion_scaled(w, a))
                    for a in config.PROBE_MOTION_LEVELS]

    rows = []
    for label in SWIPES:
        idx = np.flatnonzero((y == label) & (pred == label))
        for name, transform in experiments:
            result = probe(model, X[idx], presence[idx], label, transform, rng)
            rows.append({"class": config.CLASSES[label], "n": int(idx.size),
                         "experiment": name, **result})

    run_dir = next_run_dir(config.PHASE6_RESULTS_DIR / "probe_swipes")
    write_table(rows, list(rows[0]), run_dir / "probe")
    write_manifest(run_dir, {"script": "probe_swipes", "n_rows": len(rows)})

    for label in SWIPES:
        name = config.CLASSES[label]
        print(f"\n{name} — {[r for r in rows if r['class'] == name][0]['n']} cửa sổ "
              "vuốt thật đang được nhận đúng:")
        for r in (r for r in rows if r["class"] == name):
            print(f"  {r['experiment']:<26} còn nhận đúng {r['kept']:5.0%}   "
                  f"none {r['to_none']:4.0%}   open_range {r['open_range']:.2f}  "
                  f"pinch_range {r['pinch_range']:.2f}  |dx| {r['abs_dx']:.2f}  "
                  f"max_vx {r['max_vx']:.2f}")
    print(f"\nBảng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
