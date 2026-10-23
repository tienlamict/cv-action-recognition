"""Huấn luyện LSTM trên chuỗi 42 chiều, đánh giá trên tập VAL (Phase 7).

- Mỗi cửa sổ đã chuẩn hoá thành chuỗi (T, 42) qua datasets.window_sequence —
  đúng hàm mà demo.py --model lstm dùng. Tập train tăng cường MỚI mỗi epoch
  (augment.augment), cộng hai phép riêng cho LSTM (thêm 2026-10-10): cửa sổ
  zoom đổi dáng ngón phụ (AUG_ZOOM_STYLE_P) và cửa sổ bàn tay đứng yên nhãn
  none (AUG_STATIC_SHARE). Val không bao giờ tăng cường.
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

Lệch khỏi config ở bất kỳ tham số nào (--no-augment, --max-epochs, --patience,
--zoom-style-p, --static-share, --stop-smooth) là một lần KHẢO SÁT: checkpoint
lưu trong thư mục chạy, không thay mô hình của demo, không ghi vào bảng so sánh.

Ví dụ:
    python scripts/train_lstm.py
    python scripts/train_lstm.py --no-augment
    python scripts/train_lstm.py --no-augment --patience 150   # không dừng sớm
    python scripts/train_lstm.py --zoom-style-p 0.5 --static-share 0.1
    python scripts/train_lstm.py --stop-smooth 1     # dừng theo điểm thô, như run_02
    python scripts/train_lstm.py --max-epochs 3      # chạy thử nhanh
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.datasets import window_sequences  # noqa: E402
from src.evaluation import (baselines, event_rows,  # noqa: E402
                            false_alarm_rows, predict_windows, split_features,
                            summarize, upsert_comparison, write_summary)
from src.forest import file_sha256  # noqa: E402
from src.models import predict_proba, save_checkpoint  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits, split_of  # noqa: E402
from src.tables import write_table  # noqa: E402
from src.training import smoothed_minimum, tail_stats, train_lstm  # noqa: E402
from src.viz import plot_confusion, plot_training_curves  # noqa: E402

MODEL_LABELS = {"rules": "luật (Phase 5)", "rf": "rừng ngẫu nhiên (Phase 6)",
                "lstm": "LSTM (Phase 7)"}


#: Mô hình ra đời trước LSTM, đặt cạnh nó trong bảng so sánh. ``hybrid`` dùng
#: chính LSTM đang huấn luyện nên không thuộc nhóm này — đánh giá nó bằng
#: ``evaluate.py --model hybrid`` sau khi huấn luyện xong.
EARLIER_MODELS = ("rules", "rf")


def other_models(F_val):
    """Dự đoán của các mô hình trước trên cùng tập val. Mô hình chưa huấn
    luyện thì bỏ qua, kèm lý do."""
    out, skipped = {}, {}
    for name in EARLIER_MODELS:
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
    parser.add_argument("--zoom-style-p", type=float, default=config.AUG_ZOOM_STYLE_P,
                        help="mặc định %(default)s (AUG_ZOOM_STYLE_P)")
    parser.add_argument("--static-share", type=float, default=config.AUG_STATIC_SHARE,
                        help="mặc định %(default)s (AUG_STATIC_SHARE)")
    parser.add_argument("--stop-smooth", type=int, default=config.LSTM_CURVE_SMOOTH,
                        help="trung bình trượt bấy nhiêu epoch khi dừng sớm; 1 = "
                             "theo điểm thô như run_01–05. Mặc định %(default)s")
    args = parser.parse_args()
    augment = not args.no_augment
    # Lệch khỏi config ở bất kỳ tham số nào là một lần KHẢO SÁT: checkpoint nằm
    # trong thư mục chạy, mô hình của demo và bảng so sánh không đổi.
    deviations = {name: value for name, value, default in (
        ("no_augment", args.no_augment, False),
        ("max_epochs", args.max_epochs, config.LSTM_MAX_EPOCHS),
        ("patience", args.patience, config.LSTM_PATIENCE),
        ("zoom_style_p", args.zoom_style_p, config.AUG_ZOOM_STYLE_P),
        ("static_share", args.static_share, config.AUG_STATIC_SHARE),
        ("stop_smooth", args.stop_smooth, config.LSTM_CURVE_SMOOTH)) if value != default}
    survey = bool(deviations)
    labels = {**MODEL_LABELS, "lstm": "LSTM không tăng cường"} if not augment else (
        {**MODEL_LABELS, "lstm": "LSTM khảo sát"} if survey else MODEL_LABELS)

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

    print(f"Train {len(y_tr)} cửa sổ ("
          + ("tăng cường mới mỗi epoch" if augment else "KHÔNG tăng cường — khảo sát")
          + f"), val {len(y_va)} cửa sổ.")
    print("epoch   loss train   val   macro-F1 train   val")

    def report(row, stopper):
        mark = "  *" if stopper.best_epoch == row["epoch"] else ""
        print(f"{row['epoch']:5d}   {row['train_loss']:10.4f} {row['val_loss']:7.4f}"
              f"   {row['train_macro_f1']:14.4f} {row['val_macro_f1']:7.4f}{mark}",
              flush=True)

    # Seed (ba chỗ), tăng cường, trọng số lớp, Adam, dừng sớm: src/training.py —
    # đúng quy trình mà các bảng khảo sát của Phase 8 dùng.
    trained = train_lstm(X_tr, y_tr, X_va, y_va, seed=config.SEED, augment=augment,
                         zoom_style_p=args.zoom_style_p,
                         static_share=args.static_share,
                         max_epochs=args.max_epochs, patience=args.patience,
                         window=args.stop_smooth, on_epoch=report)
    model, history, stopper = trained.model, trained.history, trained.stopper
    train_set, pool, weights = trained.dataset, trained.finger_pool, trained.weights
    train_sec = trained.seconds
    print("Trọng số lớp: " + ", ".join(f"{c} {w:.2f}" for c, w in
                                        zip(config.CLASSES, weights.tolist())))

    pred = predict_proba(model, window_sequences(X_va)).argmax(axis=1)
    lstm = summarize(y_va, pred)
    if abs(lstm["macro_f1"] - stopper.best_raw) > 1e-9:
        raise SystemExit(f"Nạp lại trọng số tốt nhất ra macro-F1 {lstm['macro_f1']:.6f}, "
                         f"khác lúc chọn {stopper.best_raw:.6f} — kiểm tra vòng huấn luyện.")
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
        model, run_dir / config.LSTM_MODEL_PATH.name if survey else None,
        epoch=stopper.best_epoch, val_macro_f1=stopper.best_raw,
        val_macro_f1_smoothed=stopper.best_score,
        epochs_run=len(history), n_train=int(len(y_tr)), seed=config.SEED,
        augment=augment, windows_sha256=file_sha256(args.windows),
        torch_version=torch.__version__,
        created=datetime.now().isoformat(timespec="seconds"))
    if not survey:
        random_f1, none_f1 = baselines(y_va)
        upsert_comparison({"model": "lstm", "split": "val", "n_windows": int(len(y_va)),
                           "macro_f1": lstm["macro_f1"], "baseline_random": random_f1,
                           "baseline_none": none_f1, "run": relative_to_root(run_dir)})
    write_manifest(run_dir, {
        "script": "train_lstm", "augment": augment, "survey": deviations,
        "patience": args.patience, "stop_smooth": args.stop_smooth,
        "seeds": {"random": config.SEED, "numpy": config.SEED, "torch": config.SEED},
        "n_train": int(len(y_tr)), "n_val": int(len(y_va)),
        "epochs_run": len(history), "best_epoch": stopper.best_epoch,
        "val_macro_f1": stopper.best_raw, "val_macro_f1_smoothed": stopper.best_score,
        "min_val_loss_epoch": min_loss["epoch"],
        "val_loss_smoothed_min_epoch": turn_epoch, "val_loss_smoothed_min": turn_loss,
        "val_macro_f1_tail_mean": tail_mean, "val_macro_f1_tail_std": tail_std,
        "train_seconds": train_sec, "augment_fallbacks": train_set.n_fallback,
        "static_windows_per_epoch": train_set.n_static,
        "zoom_style_p": train_set.zoom_style_p,
        "finger_pool_size": 0 if pool is None else int(len(pool[0])),
        "class_weights": weights.tolist(), "torch_version": torch.__version__,
        "torch_threads": torch.get_num_threads(),
        "model": relative_to_root(model_path), "model_sha256": file_sha256(model_path),
        "skipped_models": skipped})

    print(f"\n{len(history)} epoch trong {train_sec:.0f} s. Checkpoint: epoch "
          f"{stopper.best_epoch}, nơi macro-F1 val trung bình trượt "
          f"{stopper.window} epoch cao nhất ({stopper.best_score:.4f}); chính epoch đó "
          f"{stopper.best_raw:.4f}. {min(config.LSTM_PATIENCE, len(history))} epoch "
          f"cuối trung bình {tail_mean:.4f} ± {tail_std:.4f}.")
    print(f"Loss val thô thấp nhất ở epoch {min_loss['epoch']} ({min_loss['val_loss']:.4f}); "
          f"trung bình trượt {config.LSTM_CURVE_SMOOTH} epoch thấp nhất ở epoch "
          f"{turn_epoch} ({turn_loss:.4f}) — sau đó loss val không giảm nữa.")
    if survey:
        print(f"Lần chạy khảo sát {deviations}: mô hình của demo và bảng so sánh "
              "không đổi.")
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
