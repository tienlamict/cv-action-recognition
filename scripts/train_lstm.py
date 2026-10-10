"""Huấn luyện LSTM trên chuỗi 42 chiều, đánh giá trên tập VAL (Phase 7).

- Mỗi cửa sổ đã chuẩn hoá thành chuỗi (T, 42) qua datasets.window_sequence —
  đúng hàm mà demo.py --model lstm dùng. Tập train tăng cường MỚI mỗi epoch
  (augment.augment); val không bao giờ tăng cường.
- LSTMClassifier một chiều: LSTM_HIDDEN, LSTM_LAYERS, LSTM_DROPOUT, LSTM_POOLING.
- Adam (LSTM_LR), CrossEntropyLoss có trọng số lớp "balanced" tính trên train.
- Mỗi epoch đo loss và macro-F1 của train (không tăng cường) và val theo cùng
  một cách. Dừng sớm theo macro-F1 val (LSTM_PATIENCE); checkpoint tốt nhất
  lưu kèm epoch và macro-F1 val vào LSTM_MODEL_PATH.
- Hình đường học; ma trận nhầm lẫn; bảng ba mô hình — luật, rừng ngẫu nhiên,
  LSTM — trên CÙNG tập val, kèm mức sự kiện xấp xỉ và báo nhầm theo nhãn gốc.
- Seed cố định ở random, numpy, torch; ghi vào manifest.

Con số val của LSTM lạc quan hơn so với rừng: epoch được CHỌN theo chính
macro-F1 val, còn rừng không chọn gì trên val. Script in thêm mức trung bình của
LSTM_PATIENCE epoch cuối, và chỗ loss val (đã làm mượt) ngừng giảm.

--no-augment là lần chạy KHẢO SÁT (Phase 8: có so với không tăng cường; và để
thấy rõ điểm bắt đầu quá khớp): checkpoint lưu trong thư mục chạy, không thay
mô hình của demo, không ghi vào bảng so sánh mô hình.

Ví dụ:
    python scripts/train_lstm.py
    python scripts/train_lstm.py --no-augment
    python scripts/train_lstm.py --no-augment --patience 150   # không dừng sớm
    python scripts/train_lstm.py --max-epochs 3      # chạy thử nhanh
"""

import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from torch import nn  # noqa: E402
from torch.utils.data import DataLoader  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.datasets import WindowDataset, window_sequences  # noqa: E402
from src.evaluation import (baselines, event_rows,  # noqa: E402
                            false_alarm_rows, predict_windows, split_features,
                            summarize, upsert_comparison, write_summary)
from src.forest import file_sha256  # noqa: E402
from src.models import (LSTMClassifier, predict_proba,  # noqa: E402
                        save_checkpoint)
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits, split_of  # noqa: E402
from src.tables import write_table  # noqa: E402
from src.training import (class_weights, fit, set_seed,  # noqa: E402
                          smoothed_minimum, tail_stats)
from src.viz import plot_confusion, plot_training_curves  # noqa: E402

MODEL_LABELS = {"rules": "luật (Phase 5)", "rf": "rừng ngẫu nhiên (Phase 6)",
                "lstm": "LSTM (Phase 7)"}


def other_models(F_val):
    """Dự đoán của các mô hình trước trên cùng tập val. Mô hình chưa huấn
    luyện thì bỏ qua, kèm lý do."""
    out, skipped = {}, {}
    for name in config.MODEL_NAMES:
        if name == "lstm":
            continue
        try:
            out[name] = predict_windows(name, F_val)[0]
        except FileNotFoundError as error:
            skipped[name] = str(error)
    return out, skipped


def comparison_rows(y, preds, labels=MODEL_LABELS):
    """Bảng một hàng mỗi mô hình trên CÙNG tập: macro-F1 và F1 từng lớp,
    sau hai đường cơ sở."""
    random_f1, none_f1 = baselines(y)
    rows = [{"model": "ngẫu nhiên đều", "macro_f1": random_f1},
            {"model": "luôn none", "macro_f1": none_f1}]
    for name, pred in preds.items():
        summary = summarize(y, pred)
        rows.append({"model": labels[name], "macro_f1": summary["macro_f1"],
                     **{r["class"]: r["f1"] for r in summary["per_class"]}})
    return rows


def event_table(y, preds, clip, t0):
    """Mức sự kiện xấp xỉ của từng mô hình, một hàng mỗi (lớp, mô hình)."""
    return [{"class": r["class"], "model": name, **{k: v for k, v in r.items()
                                                    if k != "class"}}
            for name, pred in preds.items() for r in event_rows(y, pred, clip, t0)]


def alarm_table(y, preds, src_label):
    """Tỉ lệ cửa sổ none bị báo nhầm theo nhãn gốc, một cột mỗi mô hình."""
    rows = {}
    for name, pred in preds.items():
        for r in false_alarm_rows(y, pred, src_label):
            row = rows.setdefault(r["src_label"], {"src_label": r["src_label"],
                                                   "n_windows": r["n_windows"]})
            row[f"rate_{name}"] = r["rate"]
    return sorted(rows.values(), key=lambda r: -r["n_windows"])


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    parser.add_argument("--max-epochs", type=int, default=config.LSTM_MAX_EPOCHS,
                        help="mặc định %(default)s; dừng sớm vẫn áp dụng")
    parser.add_argument("--no-augment", action="store_true",
                        help="khảo sát: không tăng cường; không thay mô hình của demo")
    parser.add_argument("--patience", type=int, default=config.LSTM_PATIENCE,
                        help="mặc định %(default)s; đặt bằng --max-epochs để chạy "
                             "hết, xem đường học khi không dừng sớm")
    args = parser.parse_args()
    augment = not args.no_augment
    labels = MODEL_LABELS if augment else {**MODEL_LABELS,
                                           "lstm": "LSTM không tăng cường"}

    set_seed(config.SEED)
    splits = read_splits()
    with np.load(args.windows, allow_pickle=False) as data:
        data = {k: data[k] for k in data.files}
    train = split_of(data["subject"], splits) == "train"
    X_tr, y_tr = data["X"][train], data["y"][train]
    # val: đặc trưng cho luật và rừng, cửa sổ cho LSTM — cùng các cửa sổ, cùng thứ tự
    F_va, y_va, val = split_features(data["X"], data["y"], data["presence"],
                                     data["subject"], splits, "val")
    X_va = data["X"][val]
    clip, t0, src = (data[k][val] for k in ("clip", "t0", "src_label"))

    train_set = WindowDataset(X_tr, y_tr, "train", augment=augment,
                              rng=np.random.default_rng(config.SEED))
    loader = DataLoader(train_set, batch_size=config.LSTM_BATCH, shuffle=True,
                        generator=torch.Generator().manual_seed(config.SEED))
    seq_tr, seq_va = window_sequences(X_tr), window_sequences(X_va)

    model = LSTMClassifier()
    weights = class_weights(y_tr)
    loss_fn = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.LSTM_LR)

    print(f"Train {len(y_tr)} cửa sổ ("
          + ("tăng cường mới mỗi epoch" if augment else "KHÔNG tăng cường — khảo sát")
          + f"), val {len(y_va)} cửa sổ. Trọng số lớp: "
          + ", ".join(f"{c} {w:.2f}" for c, w in zip(config.CLASSES, weights.tolist())))
    print("epoch   loss train   val   macro-F1 train   val")

    def report(row, stopper):
        mark = "  *" if stopper.best_epoch == row["epoch"] else ""
        print(f"{row['epoch']:5d}   {row['train_loss']:10.4f} {row['val_loss']:7.4f}"
              f"   {row['train_macro_f1']:14.4f} {row['val_macro_f1']:7.4f}{mark}",
              flush=True)

    started = time.perf_counter()
    history, stopper = fit(model, loader, seq_tr, y_tr, seq_va, y_va, loss_fn,
                           optimizer, max_epochs=args.max_epochs,
                           patience=args.patience, on_epoch=report)
    train_sec = time.perf_counter() - started

    model.load_state_dict(stopper.best_state)
    pred = predict_proba(model, seq_va).argmax(axis=1)
    lstm = summarize(y_va, pred)
    if abs(lstm["macro_f1"] - stopper.best_score) > 1e-9:
        raise SystemExit(f"Nạp lại trọng số tốt nhất ra macro-F1 {lstm['macro_f1']:.6f}, "
                         f"khác lúc chọn {stopper.best_score:.6f} — kiểm tra vòng huấn luyện.")
    min_loss = min(history, key=lambda r: r["val_loss"])
    turn_epoch, turn_loss = smoothed_minimum(history, "val_loss")
    tail_mean, tail_std = tail_stats(history, "val_macro_f1")

    run_dir = next_run_dir(config.PHASE7_RESULTS_DIR / "train_lstm")
    write_summary(lstm, run_dir)
    plot_confusion(lstm["confusion"], lstm["confusion_row"], config.CLASSES,
                   run_dir / "confusion.png",
                   title=f"{labels['lstm']} — tập val ({len(y_va)} cửa sổ), "
                         f"epoch {stopper.best_epoch}")
    plot_training_curves(history, stopper.best_epoch, run_dir / "training_curves.png",
                         title=f"{labels['lstm']} — đường học (đo train không tăng "
                               "cường, cùng cách với val)")
    write_table(history, list(history[0]), run_dir / "history")

    preds, skipped = other_models(F_va)
    preds["lstm"] = pred
    comparison = comparison_rows(y_va, preds, labels)
    write_table(comparison, ["model", "macro_f1", *config.CLASSES], run_dir / "comparison")
    events = event_table(y_va, preds, clip, t0)
    write_table(events, list(events[0]), run_dir / "events_approx")
    alarms = alarm_table(y_va, preds, src)
    write_table(alarms, ["src_label", "n_windows", *(f"rate_{n}" for n in preds)],
                run_dir / "none_false_alarms_by_src")

    # Lần chạy khảo sát không bao giờ thay mô hình của demo hay bảng so sánh.
    model_path = save_checkpoint(
        model, None if augment else run_dir / config.LSTM_MODEL_PATH.name,
        epoch=stopper.best_epoch, val_macro_f1=stopper.best_score,
        epochs_run=len(history), n_train=int(len(y_tr)), seed=config.SEED,
        augment=augment, windows_sha256=file_sha256(args.windows),
        torch_version=torch.__version__,
        created=datetime.now().isoformat(timespec="seconds"))
    if augment:
        random_f1, none_f1 = baselines(y_va)
        upsert_comparison({"model": "lstm", "split": "val", "n_windows": int(len(y_va)),
                           "macro_f1": lstm["macro_f1"], "baseline_random": random_f1,
                           "baseline_none": none_f1, "run": relative_to_root(run_dir)})
    write_manifest(run_dir, {
        "script": "train_lstm", "augment": augment, "patience": args.patience,
        "seeds": {"random": config.SEED, "numpy": config.SEED, "torch": config.SEED},
        "n_train": int(len(y_tr)), "n_val": int(len(y_va)),
        "epochs_run": len(history), "best_epoch": stopper.best_epoch,
        "val_macro_f1": stopper.best_score, "min_val_loss_epoch": min_loss["epoch"],
        "val_loss_smoothed_min_epoch": turn_epoch, "val_loss_smoothed_min": turn_loss,
        "val_macro_f1_tail_mean": tail_mean, "val_macro_f1_tail_std": tail_std,
        "train_seconds": train_sec, "augment_fallbacks": train_set.n_fallback,
        "class_weights": weights.tolist(), "torch_version": torch.__version__,
        "torch_threads": torch.get_num_threads(),
        "model": relative_to_root(model_path), "model_sha256": file_sha256(model_path),
        "skipped_models": skipped})

    print(f"\n{len(history)} epoch trong {train_sec:.0f} s. Tốt nhất: epoch "
          f"{stopper.best_epoch}, macro-F1 val {stopper.best_score:.4f} — đỉnh chọn trên "
          f"val; {min(config.LSTM_PATIENCE, len(history))} epoch cuối trung bình "
          f"{tail_mean:.4f} ± {tail_std:.4f}.")
    print(f"Loss val thô thấp nhất ở epoch {min_loss['epoch']} ({min_loss['val_loss']:.4f}); "
          f"trung bình trượt {config.LSTM_CURVE_SMOOTH} epoch thấp nhất ở epoch "
          f"{turn_epoch} ({turn_loss:.4f}) — sau đó loss val không giảm nữa.")
    if not augment:
        print("Lần chạy khảo sát: mô hình của demo và bảng so sánh không đổi.")
    if train_set.n_fallback:
        print(f"{train_set.n_fallback} lần tăng cường bị normalize_window từ chối — "
              "dùng cửa sổ gốc.")
    print("\nCùng tập val — macro-F1 và F1 từng lớp:")
    print(f"{'mô hình':<27}{'macro-F1':>9}" + "".join(f"{c[:11]:>12}" for c in config.CLASSES))
    for row in comparison:
        cells = "".join(f"{row[c]:>12.3f}" if c in row else f"{'':>12}"
                        for c in config.CLASSES)
        print(f"{row['model']:<27}{row['macro_f1']:>9.4f}{cells}")
    for name, reason in skipped.items():
        print(f"  (bỏ qua {name}: {reason})")
    print("\nclassification_report (LSTM, val):")
    print(lstm["report"])
    print("Mức sự kiện xấp xỉ (val): cử chỉ có >= 1 cửa sổ được nhận đúng")
    for name in preds:
        cells = "  ".join(f"{r['class']} {r['hit_1']:.0%}" for r in events
                          if r["model"] == name)
        print(f"  {name:<6} {cells}")
    print(f"\nMô hình: {relative_to_root(model_path)}")
    print(f"Bảng và hình: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
