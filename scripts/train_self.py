"""Học lại rừng và LSTM với IPN train CỘNG real_tune tự quay (Phase 11).

Lệch SPEC đã duyệt 2026-11-06: cử chỉ tự quay của real_tune cũng vào tập học, không
chỉ cửa sổ none. real_test không bao giờ vào đây.

- Đúng hàm học và công thức của mô hình demo. Rừng: forest.training_set (kèm bản
  bàn tay cứng AUG_RIGID_SHARE) và train_forest, như train_rf.py. LSTM:
  training.train_lstm với DEPLOY_ZOOM_STYLE_P, DEPLOY_STATIC_SHARE, như
  LSTM_MODEL_PATH. Chỉ khác: cửa sổ real_tune (config.SELF_WINDOWS["real_tune"],
  dựng bằng build_self_dataset.py) nằm phía train.
- --ipn-only: KHÔNG thêm real_tune. Dùng để học mô hình "cũ" với hạt khác, đúng script
  và đúng công thức đó; hạt SEED của bên này chính là mô hình demo, không học lại.
- --seed: LSTM dao động mạnh theo hạt, nên mỗi bên học với SELF_SEEDS (người dùng
  duyệt 2026-11-09). Đường dẫn của từng bên, từng hạt: selfdata.model_paths.
- Dừng sớm của LSTM theo macro-F1 val IPN, như mô hình demo.
- Mô hình demo không bao giờ bị ghi đè. So cũ–mới bằng compare_self.py.
- --max-epochs khác mặc định là chạy thử: checkpoint nằm trong thư mục chạy.

Ví dụ:
    python scripts/train_self.py                       # IPN + real_tune, hạt SEED
    python scripts/train_self.py --seed 43
    python scripts/train_self.py --ipn-only --seed 43  # đối chứng: IPN thuần, hạt 43
    python scripts/train_self.py --only lstm --max-epochs 3       # chạy thử
"""

import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config, selfdata  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.evaluation import model_proba, split_features, summarize  # noqa: E402
from src.forest import file_sha256, save_bundle, train_forest, training_set  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits, split_of  # noqa: E402
from src.windows import FIELDS  # noqa: E402


def load(path):
    with np.load(path, allow_pickle=False) as data:
        return {k: data[k] for k in FIELDS}


def merged(ipn, own, splits):
    """Gộp cửa sổ IPN và real_tune. Tập train mới là người train của IPN cộng các
    người–buổi real_tune; val vẫn là val IPN.

    Raises:
        ValueError: cửa sổ tự quay có người–buổi không thuộc real_tune — nhất là
            real_test, thứ không bao giờ được vào tập học.
    """
    outside = sorted(set(own["subject"]) - set(splits["real_tune"]))
    if outside:
        raise ValueError(f"Cửa sổ tự quay ngoài real_tune: {outside}")
    data = {k: np.concatenate([ipn[k], own[k]]) for k in FIELDS}
    part = {"train": list(splits["train"]) + list(splits["real_tune"]),
            "val": list(splits["val"])}
    return data, part


def targets(ipn_only, seed):
    """Đường dẫn rừng và LSTM sẽ ghi.

    Raises:
        SystemExit: đó là mô hình demo (IPN thuần, hạt SEED) — không bao giờ ghi đè.
    """
    if ipn_only and seed == config.SEED:
        raise SystemExit(f"IPN thuần với hạt {seed} chính là mô hình demo — không học lại, "
                         "không ghi đè.")
    return selfdata.model_paths(not ipn_only, seed)


def macro_f1_val(name, F_va, X_va, y_va, path):
    proba, _ = model_proba(name, F_va, X_va, **{f"{name}_path": path})
    return summarize(y_va, proba.argmax(axis=1))["macro_f1"]


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--only", choices=("rf", "lstm"), default=None)
    parser.add_argument("--seed", type=int, default=config.SEED)
    parser.add_argument("--ipn-only", action="store_true",
                        help="đối chứng: không thêm real_tune (hạt khác SEED)")
    parser.add_argument("--max-epochs", type=int, default=config.LSTM_MAX_EPOCHS)
    args = parser.parse_args()
    trial = args.max_epochs != config.LSTM_MAX_EPOCHS
    rf_path, lstm_path = targets(args.ipn_only, args.seed)

    splits = read_splits()
    ipn = load(config.WINDOWS_NPZ)
    if args.ipn_only:
        data, part = ipn, {"train": list(splits["train"]), "val": list(splits["val"])}
        n_self = Counter()
    else:
        own = load(config.SELF_WINDOWS["real_tune"])
        data, part = merged(ipn, own, splits)
        n_self = Counter(config.CLASSES[k] for k in own["y"])
    train = split_of(data["subject"], part) == "train"
    F_va, y_va, val = split_features(ipn["X"], ipn["y"], ipn["presence"], ipn["subject"],
                                     splits, "val")
    X_va = ipn["X"][val]
    side = "IPN thuần" if args.ipn_only else "IPN + tự quay"
    print(f"{side}, hạt {args.seed}: train {int(train.sum())} cửa sổ (tự quay "
          f"{sum(n_self.values())}: {', '.join(f'{c} {n_self[c]}' for c in config.CLASSES)}); "
          f"val IPN {y_va.size} cửa sổ.")

    run_dir = next_run_dir(config.PHASE11_RESULTS_DIR / "train_self")
    sources = {"seed": args.seed, "with_self": not args.ipn_only,
               "windows_sha256": file_sha256(config.WINDOWS_NPZ),
               "created": datetime.now().isoformat(timespec="seconds")}
    if not args.ipn_only:
        sources.update(self_windows_sha256=file_sha256(config.SELF_WINDOWS["real_tune"]),
                       real_tune=list(splits["real_tune"]))
    manifest = {"script": "train_self", "n_train": int(train.sum()),
                "self_by_class": dict(n_self), **sources}

    if args.only in (None, "rf"):
        import sklearn
        F_tr, y_tr, n_rigid = training_set(data["X"], data["y"], data["presence"],
                                           data["subject"], part, seed=args.seed)
        model = train_forest(F_tr, y_tr, seed=args.seed)
        trained_on = "train" if args.ipn_only else "train+real_tune"
        path = save_bundle(model, rf_path, trained_on=trained_on, n_train=int(y_tr.size),
                           n_rigid=n_rigid, rigid_share=config.AUG_RIGID_SHARE,
                           sklearn_version=sklearn.__version__, **sources)
        old = macro_f1_val("rf", F_va, X_va, y_va, config.RF_MODEL_PATH)
        new = macro_f1_val("rf", F_va, X_va, y_va, path)
        manifest["rf"] = {"model": relative_to_root(path), "n_rigid": n_rigid,
                          "macro_f1_val_demo": old, "macro_f1_val": new}
        print(f"Rừng: macro-F1 val IPN {new:.4f} (demo {old:.4f}) → {relative_to_root(path)}")

    if args.only in (None, "lstm"):
        import torch

        from src.models import save_checkpoint
        from src.training import train_lstm

        def report(row, stopper):
            mark = "  *" if stopper.best_epoch == row["epoch"] else ""
            print(f"{row['epoch']:5d}   {row['train_loss']:10.4f} {row['val_loss']:7.4f}"
                  f"   {row['train_macro_f1']:14.4f} {row['val_macro_f1']:7.4f}{mark}",
                  flush=True)

        print("epoch   loss train   val   macro-F1 train   val")
        trained = train_lstm(data["X"][train], data["y"][train], X_va, y_va,
                             seed=args.seed, augment=True,
                             zoom_style_p=config.DEPLOY_ZOOM_STYLE_P,
                             static_share=config.DEPLOY_STATIC_SHARE,
                             max_epochs=args.max_epochs, patience=config.LSTM_PATIENCE,
                             window=config.LSTM_CURVE_SMOOTH, on_epoch=report)
        stopper = trained.stopper
        target = run_dir / lstm_path.name if trial else lstm_path
        path = save_checkpoint(
            trained.model, target, epoch=stopper.best_epoch, val_macro_f1=stopper.best_raw,
            val_macro_f1_smoothed=stopper.best_score, epochs_run=len(trained.history),
            n_train=int(train.sum()), augment=True,
            zoom_style_p=config.DEPLOY_ZOOM_STYLE_P, static_share=config.DEPLOY_STATIC_SHARE,
            torch_version=torch.__version__, **sources)
        old = macro_f1_val("lstm", F_va, X_va, y_va, config.LSTM_MODEL_PATH)
        new = macro_f1_val("lstm", F_va, X_va, y_va, path)
        manifest["lstm"] = {"model": relative_to_root(path), "trial": trial,
                            "best_epoch": stopper.best_epoch,
                            "epochs_run": len(trained.history),
                            "train_seconds": trained.seconds,
                            "macro_f1_val_demo": old, "macro_f1_val": new}
        print(f"LSTM: {len(trained.history)} epoch trong {trained.seconds:.0f} s, chọn epoch "
              f"{stopper.best_epoch}. macro-F1 val IPN {new:.4f} (demo {old:.4f})"
              f" → {relative_to_root(path)}")

    write_manifest(run_dir, manifest)
    print(f"Manifest: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
