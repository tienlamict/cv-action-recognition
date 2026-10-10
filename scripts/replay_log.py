"""Chạy lại một phiên demo đã ghi qua nhiều mô hình — offline, cùng đường ống.

demo.py --log FILE ghi kèm điểm mốc thô vào FILE_landmarks.npz. Script này đẩy
lại từng frame qua đúng LivePredictor của demo (TimeBuffer → normalize_window →
đặc trưng hoặc LSTM), nên mỗi mô hình cho đúng kết quả như khi nó chạy trực tiếp
trên phiên đó. Dùng để biết vì sao một cử chỉ của người dùng không được nhận, và
để so các mô hình — hay hai lần huấn luyện của cùng một mô hình — trên chính bàn
tay người dùng.

Ra một dòng thời gian: mỗi 0,2 giây một hàng, vài đặc trưng và nhãn của từng mô
hình; cùng số cụm nhãn khác none của từng mô hình (như summarize_log.py).

Ví dụ:
    python scripts/replay_log.py results/phase7/live_lstm_landmarks.npz
    python scripts/replay_log.py results/phase7/live_lstm_landmarks.npz --models rf lstm \\
        --extra-lstm lstm_run02=results/phase7/train_lstm/run_02/lstm_model.pt
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.features import FEATURE_NAMES  # noqa: E402
from src.io_data import load_clip  # noqa: E402
from src.live import (LivePredictor, count_clusters, label_name,  # noqa: E402
                      make_model)
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.tables import write_table  # noqa: E402

SHOWN = ("pinch_delta", "open_range", "dx", "max_vx")


def replay(model, ts, xy, w, h):
    """Mọi lần dự đoán của ``model`` trên phiên, đúng nhịp ``STRIDE_SEC``."""
    predictor = LivePredictor(model)
    out = []
    for t, frame in zip(ts, xy):
        prediction = predictor.update(float(t), frame, w, h)
        if prediction is not None:
            out.append(prediction)
    return out


def timeline_rows(runs):
    """Một hàng mỗi lần dự đoán: thời điểm, tỉ lệ có tay, ``SHOWN``, và nhãn
    của từng mô hình. Mọi mô hình dự đoán ở cùng các thời điểm — nhịp chỉ phụ
    thuộc ``ts`` — nên ghép theo thứ tự."""
    first = next(iter(runs.values()))
    rows = []
    for k, p in enumerate(first):
        row = {"ts": round(p.ts, 3),
               "presence": "" if p.presence is None else round(float(p.presence), 3)}
        for name in SHOWN:
            row[name] = ("" if p.features is None
                         else round(float(p.features[FEATURE_NAMES.index(name)]), 3))
        for model, preds in runs.items():
            q = preds[k]
            row[model] = label_name(q.label)
            row[f"{model}_conf"] = "" if q.confidence is None else round(q.confidence, 3)
        rows.append(row)
    return rows


def parse_extra(specs):
    """``tên=đường dẫn checkpoint`` → dict."""
    out = {}
    for spec in specs or []:
        name, _, path = spec.partition("=")
        if not name or not path:
            raise SystemExit(f"--extra-lstm cần dạng tên=đường_dẫn, nhận '{spec}'")
        out[name] = Path(path)
    return out


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("landmarks", help="file _landmarks.npz do demo.py --log ghi")
    parser.add_argument("--models", nargs="+", default=list(config.MODEL_NAMES),
                        choices=config.MODEL_NAMES)
    parser.add_argument("--extra-lstm", action="append", metavar="TÊN=CHECKPOINT",
                        help="thêm một checkpoint LSTM khác, ví dụ của lần huấn luyện trước")
    args = parser.parse_args()

    ts, xy, w, h, _, _, meta = load_clip(args.landmarks)
    models = {name: make_model(name) for name in args.models}
    models.update({name: make_model("lstm", lstm_path=path)
                   for name, path in parse_extra(args.extra_lstm).items()})
    runs = {name: replay(model, ts, xy, w, h) for name, model in models.items()}
    rows = timeline_rows(runs)

    minutes = (ts[-1] - ts[0]) / 60 if len(ts) > 1 else 0.0
    counts = {name: count_clusters([label_name(p.label) for p in preds])
              for name, preds in runs.items()}
    run_dir = next_run_dir(config.PHASE7_RESULTS_DIR / "replay")
    write_table(rows, list(rows[0]), run_dir / "timeline")
    write_manifest(run_dir, {"script": "replay_log", "landmarks": str(args.landmarks),
                             "session": meta, "minutes": minutes, "clusters": counts})

    print(f"{args.landmarks}: {minutes:.1f} phút, {len(rows)} lần dự đoán mỗi mô hình.\n")
    print("Số cụm nhãn khác none:")
    for name, c in counts.items():
        print(f"  {name:<14}" + "  ".join(f"{k} {v:>2}" for k, v in c.items()))
    names = list(runs)
    print("\nNhững lúc có mô hình báo cử chỉ:")
    print(f"{'giây':>6}" + "".join(f"{n:>9}" for n in SHOWN) + "".join(f"  {n:<14}" for n in names))
    for r in rows:
        if any(r[n] not in ("none", "-") for n in names):
            cells = "".join(f"{r[n]:>9.2f}" if r[n] != "" else f"{'':>9}" for n in SHOWN)
            print(f"{r['ts']:6.1f}{cells}" + "".join(f"  {r[n]:<14}" for n in names))
    print(f"\nBảng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
