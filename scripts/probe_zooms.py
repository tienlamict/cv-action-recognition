"""Thăm dò: mỗi mô hình dựa vào phần nào của bàn tay để nhận ra một cú zoom?

Zoom là đầu ngón cái và ngón trỏ rời xa nhau (zoom_in) hay lại gần nhau
(zoom_out). Zoom của IPN làm bằng ba ngón cái–trỏ–giữa, ngón nhẫn và ngón út gập
suốt (docs/gestures.md) — một kiểu riêng, không phải bản chất của zoom. Lấy các
cửa sổ zoom THẬT của tập val mà mô hình đang nhận đúng, giữ nguyên cổ tay, ngón
cái và ngón trỏ, chỉ đổi các ngón còn lại:

- nhẫn và út duỗi thẳng;
- giữa, nhẫn và út duỗi thẳng — chỉ còn cái và trỏ cử động;
- giữa, nhẫn và út đứng yên so với lòng bàn tay (giữ dáng của bước đầu);

và hai phép thử dáng tay TĨNH: cả bàn tay đứng yên ở dáng của bước đầu, hoặc của
bước cuối — mô hình có đoán zoom chỉ từ một dáng tay không cử động không.

"Duỗi thẳng": các khớp nằm trên đường thẳng từ cổ tay qua gốc ngón đó, cách gốc
ngón đúng khoảng cách trung vị đo trên những bàn tay mở hẳn của IPN (bước xòe
nhất của các cửa sổ vuốt tập train) — không tự đặt ra số đo bàn tay.

Chạy cả rừng ngẫu nhiên lẫn LSTM; mọi cửa sổ đã sửa đều cộng rung điểm mốc
AUG_NOISE_SIGMA rồi đi qua đúng normalize_window như lúc chạy thật
(evaluation.probe_windows). Kết quả: results/phase7/notes.md mục 9.

Ví dụ:
    python scripts/probe_zooms.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.augment import (SPARE_FINGERS, SWIPE_LABELS, ZOOM_LABELS,  # noqa: E402
                         finger_joints, from_palm, palm_frame, static_window,
                         to_palm, usable_steps)
from src.cli import make_parser, setup_console  # noqa: E402
from src.evaluation import (batch_predictor, probe_windows,  # noqa: E402
                            split_features)
from src.features import FEATURE_NAMES, openness  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits, split_of  # noqa: E402
from src.tables import write_table  # noqa: E402

W = config.WRIST
COL = {name: i for i, name in enumerate(FEATURE_NAMES)}
OPPOSITE = dict(zip(ZOOM_LABELS, ZOOM_LABELS[::-1]))


def extended_lengths(X_swipe):
    """Khoảng cách trung vị từ gốc ngón tới PIP, DIP, đầu ngón — đơn vị lòng
    bàn tay — ở bước xòe nhất của các cửa sổ vuốt: những bàn tay mở hẳn."""
    out = {f: [] for f in SPARE_FINGERS}
    for win in X_swipe:
        steps = usable_steps(win)
        s = int(steps[np.argmax(openness(win)[steps])])
        palm = np.linalg.norm(win[s, config.MIDDLE_MCP] - win[s, W])
        for finger in out:
            mcp = win[s, config.FINGER_MCPS[finger]]
            out[finger].append(np.linalg.norm(win[s, finger_joints(finger)] - mcp,
                                              axis=-1) / palm)
    return {f: np.median(np.array(v), axis=0) for f, v in out.items()}


def extend_fingers(win, fingers, lengths):
    """Các ngón ``fingers`` duỗi thẳng theo hướng cổ tay → gốc ngón, ở mọi bước."""
    out = np.array(win, dtype=np.float64, copy=True)
    _, scale, _, _ = palm_frame(out)
    for finger in fingers:
        mcp = out[:, config.FINGER_MCPS[finger]]
        ray = mcp - out[:, W]
        ray /= np.linalg.norm(ray, axis=-1, keepdims=True)
        for k, j in enumerate(finger_joints(finger)):
            out[:, j] = mcp + (lengths[finger][k] * scale)[:, None] * ray
    return out


def freeze_fingers(win, fingers):
    """Các ngón ``fingers`` giữ đúng dáng của bước đầu SO VỚI LÒNG BÀN TAY ở mọi
    bước — không cử động, nhưng vẫn theo bàn tay khi nó dời hay xoay."""
    out = np.array(win, dtype=np.float64, copy=True)
    idx = [j for f in fingers for j in finger_joints(f)]
    out[:, idx] = from_palm(out, to_palm(out, 0, idx))
    return out


def summary(pred, F, label):
    F = F[pred >= 0]
    return {"kept": float(np.mean(pred == label)),
            "to_none": float(np.mean(pred == 0)),
            "to_opposite": float(np.mean(pred == OPPOSITE[label])),
            "to_swipe": float(np.mean(np.isin(pred, SWIPE_LABELS))),
            "pinch_range": float(np.median(F[:, COL["pinch_range"]])),
            "open_range": float(np.median(F[:, COL["open_range"]]))}


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    parser.add_argument("--lstm-checkpoint", default=None,
                        help="checkpoint LSTM khác mô hình của demo, ví dụ của một "
                             "lần huấn luyện khảo sát")
    args = parser.parse_args()

    splits = read_splits()
    with np.load(args.windows, allow_pickle=False) as data:
        F, y, pick = split_features(data["X"], data["y"], data["presence"],
                                    data["subject"], splits, "val")
        X, presence = data["X"][pick].astype(np.float64), data["presence"][pick]
        train = split_of(data["subject"], splits) == "train"
        X_swipe = data["X"][train & np.isin(data["y"], SWIPE_LABELS)].astype(np.float64)
    lengths = extended_lengths(X_swipe)

    experiments = [
        ("gốc (chỉ cộng rung)", lambda w: w),
        ("nhẫn, út duỗi thẳng", lambda w: extend_fingers(w, ("ring", "pinky"), lengths)),
        ("giữa, nhẫn, út duỗi thẳng",
         lambda w: extend_fingers(w, ("middle", "ring", "pinky"), lengths)),
        ("giữa, nhẫn, út đứng yên", lambda w: freeze_fingers(w, ("middle", "ring", "pinky"))),
        ("cả bàn tay tĩnh, dáng bước đầu", lambda w: static_window(w, 0)),
        ("cả bàn tay tĩnh, dáng bước cuối", lambda w: static_window(w, -1)),
    ]

    rows = []
    for model_name in ("rf", "lstm"):
        predict, input_kind = batch_predictor(model_name, args.lstm_checkpoint)
        pred = predict(X if input_kind == "window" else F)
        rng = np.random.default_rng(config.SEED)
        for label in ZOOM_LABELS:
            idx = np.flatnonzero((y == label) & (pred == label))
            for name, transform in experiments:
                probed, feats = probe_windows(predict, X[idx], presence[idx], transform,
                                              rng, input_kind=input_kind)
                rows.append({"model": model_name, "class": config.CLASSES[label],
                             "n": int(idx.size), "experiment": name,
                             **summary(probed, feats, label)})

    run_dir = next_run_dir(config.PHASE7_RESULTS_DIR / "probe_zooms")
    write_table(rows, list(rows[0]), run_dir / "probe")
    write_manifest(run_dir, {"script": "probe_zooms", "n_rows": len(rows),
                             "lstm_checkpoint": args.lstm_checkpoint,
                             "extended_lengths": {f: v.tolist() for f, v in lengths.items()}})

    print("Khoảng cách gốc ngón → PIP, DIP, đầu ngón khi duỗi (lòng bàn tay): "
          + "; ".join(f"{f} " + ", ".join(f"{d:.2f}" for d in v) for f, v in lengths.items()))
    for model_name in ("rf", "lstm"):
        for label in ZOOM_LABELS:
            part = [r for r in rows if r["model"] == model_name
                    and r["class"] == config.CLASSES[label]]
            print(f"\n{model_name} — {config.CLASSES[label]}, {part[0]['n']} cửa sổ đang "
                  "được nhận đúng:")
            for r in part:
                print(f"  {r['experiment']:<34} còn nhận đúng {r['kept']:5.0%}   none "
                      f"{r['to_none']:4.0%}   ngược chiều {r['to_opposite']:4.0%}   vuốt "
                      f"{r['to_swipe']:4.0%}   pinch_range {r['pinch_range']:.2f}")
    print(f"\nBảng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
