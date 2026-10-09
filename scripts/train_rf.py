"""Huấn luyện rừng ngẫu nhiên trên tập TRAIN, đánh giá trên tập VAL (Phase 6).

- Mỗi cửa sổ nén thành vector 15 đặc trưng; RandomForestClassifier với
  RF_N_ESTIMATORS cây, class_weight="balanced_subsample", random_state=SEED.
  Không chuẩn hoá đặc trưng.
- Tập train có thêm AUG_RIGID_SHARE bản "bàn tay cứng" trên mỗi cửa sổ vuốt
  (src/augment.py; 0 = tắt). Mức này chọn trên val bằng sweep_rigid.py.
- Đánh giá trên val: macro-F1, classification_report, ma trận nhầm lẫn thô và
  chuẩn hoá theo hàng — in cùng bảng với hai đường cơ sở và mô hình luật.
- Độ quan trọng đặc trưng theo tạp chất (feature_importances_) và theo hoán vị
  trên val, vẽ cạnh nhau, kèm bảng xếp hạng đối chiếu với ba đặc trưng dự đoán
  quan trọng (GATE_FEATURES).
- Cổng kiểm tra: rừng phải cao hơn hẳn luật; macro-F1 trên LEAKAGE_F1 là dấu
  hiệu rò rỉ; ba đặc trưng đầu bảng so với GATE_FEATURES.
- Lưu mô hình vào RF_MODEL_PATH cho demo.py --model rf.

Ví dụ:
    python scripts/train_rf.py
"""

import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import sklearn  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402

from src import config, rules  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.evaluation import (baselines, event_rows,  # noqa: E402
                            false_alarm_rows, macro_f1, split_features,
                            summarize, upsert_comparison, write_summary)
from src.features import FEATURE_NAMES  # noqa: E402
from src.forest import (file_sha256, save_bundle, train_forest,  # noqa: E402
                        training_set)
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits, split_of  # noqa: E402
from src.tables import write_table  # noqa: E402
from src.viz import plot_confusion, plot_importances  # noqa: E402


def leakage_report(subject, clip, split):
    """Người và clip chung giữa train và val — phải rỗng cả hai."""
    tr, va = split == "train", split == "val"
    return (sorted(set(subject[tr]) & set(subject[va])),
            sorted(set(clip[tr]) & set(clip[va])))


def importance_rows(impurity, perm_mean, perm_std):
    """Bảng đối chiếu: hạng theo hai cách đo, và đặc trưng nào đã được dự đoán."""
    rank_imp = np.argsort(np.argsort(-impurity)) + 1
    rank_perm = np.argsort(np.argsort(-perm_mean)) + 1
    rows = [{"feature": name, "predicted_important": name in config.GATE_FEATURES,
             "impurity": float(impurity[i]), "impurity_rank": int(rank_imp[i]),
             "perm_mean": float(perm_mean[i]), "perm_std": float(perm_std[i]),
             "perm_rank": int(rank_perm[i])}
            for i, name in enumerate(FEATURE_NAMES)]
    return sorted(rows, key=lambda r: r["perm_rank"])


def error_rows(y_true, y_pred, src_label):
    """Các ô ngoài đường chéo, tách theo nhãn gốc IPN của cửa sổ thật."""
    rows = {}
    for t, p, s in zip(y_true, y_pred, src_label):
        if t != p:
            key = (config.CLASSES[t], str(s), config.CLASSES[p])
            rows[key] = rows.get(key, 0) + 1
    return [{"true": k[0], "src_label": k[1], "predicted": k[2], "n": n}
            for k, n in sorted(rows.items(), key=lambda kv: -kv[1])]


def grouped_permutation(model, F, y, groups, repeats=config.PERM_REPEATS,
                        seed=config.SEED):
    """Độ quan trọng hoán vị của cả NHÓM đặc trưng: mọi cột trong nhóm xáo
    theo cùng một hoán vị, nên mô hình không còn cột nào trong nhóm để dựa vào.

    Returns:
        list dict ``group``, ``drop_mean``, ``drop_std`` (macro-F1 giảm).
    """
    rng = np.random.default_rng(seed)
    base_pred = model.predict(F)
    base = macro_f1(y, base_pred)
    columns = {name: i for i, name in enumerate(FEATURE_NAMES)}
    rows = [{"group": "(không xáo)", "drop_mean": 0.0, "drop_std": 0.0,
             "left_right_swaps": float(_left_right_swaps(y, base_pred))}]
    for group in groups:
        drops, swaps = [], []
        for _ in range(repeats):
            shuffled = F.copy()
            order = rng.permutation(len(F))
            for name in group:
                shuffled[:, columns[name]] = F[order, columns[name]]
            pred = model.predict(shuffled)
            drops.append(base - macro_f1(y, pred))
            swaps.append(_left_right_swaps(y, pred))
        rows.append({"group": " + ".join(group), "drop_mean": float(np.mean(drops)),
                     "drop_std": float(np.std(drops)),
                     "left_right_swaps": float(np.mean(swaps))})
    return rows


def _left_right_swaps(y_true, y_pred):
    """Số cửa sổ vuốt bị đoán NGƯỢC hướng — thước đo riêng cho thông tin hướng."""
    left, right = config.CLASSES.index("swipe_left"), config.CLASSES.index("swipe_right")
    return int(np.sum((y_true == left) & (y_pred == right))
               + np.sum((y_true == right) & (y_pred == left)))


def profile_rows(F, y_true, y_pred, src_label, names=config.PROFILE_FEATURES,
                 min_n=config.PROFILE_MIN_N):
    """Trung vị của vài đặc trưng cho từng ô (lớp thật, nhãn gốc, lớp đoán) —
    cả ô đúng lẫn ô sai — để so cửa sổ bị nhầm với cửa sổ được nhận đúng.
    ``dx`` lấy trị tuyệt đối: độ lớn của cú dời, không phải hướng."""
    columns = {name: i for i, name in enumerate(FEATURE_NAMES)}
    rows = []
    keys = sorted({(int(t), str(s), int(p)) for t, s, p in zip(y_true, src_label, y_pred)})
    for t, s, p in keys:
        pick = (y_true == t) & (src_label == s) & (y_pred == p)
        if pick.sum() < min_n:
            continue
        row = {"true": config.CLASSES[t], "src_label": s,
               "predicted": config.CLASSES[p], "n": int(pick.sum())}
        for name in names:
            values = F[pick, columns[name]]
            row[name] = float(np.median(np.abs(values) if name == "dx" else values))
        rows.append(row)
    return rows


def group_correlation_rows(F, groups):
    """Tương quan Spearman giữa hai cột của mỗi nhóm, trên tập train."""
    columns = {name: i for i, name in enumerate(FEATURE_NAMES)}
    return [{"group": " + ".join(g),
             "spearman": float(spearmanr(F[:, columns[g[0]]],
                                         F[:, columns[g[1]]]).statistic)}
            for g in groups]


def gate(rf_f1, rules_f1, rows):
    """Ba điều kiện của cổng Phase 6."""
    top_perm = [r["feature"] for r in rows[:3]]
    top_imp = [r["feature"] for r in sorted(rows, key=lambda r: r["impurity_rank"])[:3]]
    expected = set(config.GATE_FEATURES)
    return [
        ("rừng cao hơn luật", rf_f1 > rules_f1,
         f"{rf_f1:.4f} so với {rules_f1:.4f} (+{rf_f1 - rules_f1:.4f})"),
        (f"macro-F1 không vượt {config.LEAKAGE_F1} (dấu hiệu rò rỉ)",
         rf_f1 <= config.LEAKAGE_F1, f"{rf_f1:.4f}"),
        ("ba đặc trưng đầu bảng hoán vị là ba đặc trưng của cổng",
         set(top_perm) == expected, f"hoán vị: {top_perm}; tạp chất: {top_imp}"),
    ]


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    args = parser.parse_args()

    splits = read_splits()
    with np.load(args.windows, allow_pickle=False) as data:
        data = {k: data[k] for k in data.files}
    shared_people, shared_clips = leakage_report(
        data["subject"], data["clip"], split_of(data["subject"], splits))
    if shared_people or shared_clips:
        raise SystemExit(f"RÒ RỈ: train và val chung người {shared_people} "
                         f"hoặc clip {shared_clips}")

    F_tr, y_tr, n_rigid = training_set(data["X"], data["y"], data["presence"],
                                       data["subject"], splits)
    n_real = y_tr.size - n_rigid
    F_va, y_va, pick_va = split_features(data["X"], data["y"], data["presence"],
                                         data["subject"], splits, "val")

    started = time.perf_counter()
    model = train_forest(F_tr, y_tr)
    train_sec = time.perf_counter() - started

    pred_rf = model.predict(F_va)
    rf = summarize(y_va, pred_rf)
    pred_rules = np.array([rules.classify(f)[0] for f in F_va])
    rl = summarize(y_va, pred_rules)
    random_f1, none_f1 = baselines(y_va)

    perm = permutation_importance(model, F_va, y_va, scoring="f1_macro",
                                  n_repeats=config.PERM_REPEATS,
                                  random_state=config.SEED, n_jobs=-1)
    imp_rows = importance_rows(model.feature_importances_,
                               perm.importances_mean, perm.importances_std)
    checks = gate(rf["macro_f1"], rl["macro_f1"], imp_rows)
    singles = [(name,) for group in config.CORRELATED_GROUPS for name in group]
    grouped = grouped_permutation(model, F_va, y_va,
                                  [*config.CORRELATED_GROUPS, *singles, ("max_vx",)])
    correlations = {r["group"]: r["spearman"]      # chỉ cửa sổ thật, không bản cứng
                    for r in group_correlation_rows(F_tr[:n_real],
                                                    config.CORRELATED_GROUPS)}
    for row in grouped:
        row["spearman_train"] = correlations.get(row["group"], float("nan"))
    profiles = profile_rows(F_va, y_va, pred_rf, data["src_label"][pick_va])
    alarms = false_alarm_rows(y_va, pred_rf, data["src_label"][pick_va])

    run_dir = next_run_dir(config.PHASE6_RESULTS_DIR / "train_rf")
    write_summary(rf, run_dir)
    plot_confusion(rf["confusion"], rf["confusion_row"], config.CLASSES,
                   run_dir / "confusion.png",
                   title=f"Rừng ngẫu nhiên — tập val ({y_va.size} cửa sổ)")
    plot_importances(FEATURE_NAMES, model.feature_importances_,
                     perm.importances_mean, perm.importances_std,
                     config.GATE_FEATURES, run_dir / "importances.png")
    write_table(imp_rows, list(imp_rows[0]), run_dir / "importances")
    write_table(error_rows(y_va, pred_rf, data["src_label"][pick_va]),
                ["true", "src_label", "predicted", "n"], run_dir / "errors_by_src_label")
    write_table(grouped, ["group", "spearman_train", "drop_mean", "drop_std",
                          "left_right_swaps"], run_dir / "importances_grouped")
    write_table(profiles, list(profiles[0]), run_dir / "cell_profiles")
    events = event_rows(y_va, pred_rf, data["clip"][pick_va], data["t0"][pick_va])
    write_table(events, list(events[0]), run_dir / "events_approx")
    write_table(alarms, list(alarms[0]), run_dir / "none_false_alarms_by_src")

    f1_of = {name: {r["class"]: r["f1"] for r in s["per_class"]}
             for name, s in (("rules", rl), ("rf", rf))}
    comparison = [{"model": "ngẫu nhiên đều", "macro_f1": random_f1},
                  {"model": "luôn none", "macro_f1": none_f1},
                  {"model": "luật (Phase 5)", "macro_f1": rl["macro_f1"],
                   **f1_of["rules"]},
                  {"model": "rừng ngẫu nhiên", "macro_f1": rf["macro_f1"],
                   **f1_of["rf"]}]
    write_table(comparison, ["model", "macro_f1", *config.CLASSES],
                run_dir / "comparison")

    model_path = save_bundle(model, trained_on="train", n_train=int(y_tr.size),
                             n_rigid=n_rigid, rigid_share=config.AUG_RIGID_SHARE,
                             windows_sha256=file_sha256(args.windows),
                             sklearn_version=sklearn.__version__,
                             created=datetime.now().isoformat(timespec="seconds"))
    upsert_comparison({"model": "rf", "split": "val", "n_windows": int(y_va.size),
                       "macro_f1": rf["macro_f1"], "baseline_random": random_f1,
                       "baseline_none": none_f1, "run": relative_to_root(run_dir)})
    write_manifest(run_dir, {
        "script": "train_rf", "n_train": int(y_tr.size), "n_val": int(y_va.size),
        "n_rigid": n_rigid, "rigid_share": config.AUG_RIGID_SHARE,
        "train_seconds": train_sec, "model": relative_to_root(model_path),
        "model_sha256": file_sha256(model_path),
        "macro_f1_val": rf["macro_f1"], "macro_f1_rules_val": rl["macro_f1"],
        "gate": [{"check": c, "ok": ok, "detail": d} for c, ok, d in checks]})

    print(f"Train {y_tr.size} cửa sổ ({n_rigid} trong đó là bản bàn tay cứng, "
          f"AUG_RIGID_SHARE = {config.AUG_RIGID_SHARE:g}), val {y_va.size} cửa sổ; "
          f"huấn luyện {train_sec:.1f} s. Người/clip chung giữa train và val: "
          "không có.\n")
    print("macro-F1 trên val và F1 từng lớp:")
    print(f"{'mô hình':<18}{'macro-F1':>9}" + "".join(f"{c[:11]:>12}" for c in config.CLASSES))
    for row in comparison:
        cells = "".join(f"{row[c]:>12.3f}" if c in row else f"{'':>12}"
                        for c in config.CLASSES)
        print(f"{row['model']:<18}{row['macro_f1']:>9.4f}{cells}")
    print("\nclassification_report (rừng ngẫu nhiên, val):")
    print(rf["report"])
    print("Ma trận nhầm lẫn (hàng = thật, cột = đoán):")
    print(" " * 13 + "".join(f"{c[:11]:>12}" for c in config.CLASSES))
    for i, c in enumerate(config.CLASSES):
        print(f"{c:<13}" + "".join(f"{v:>12}" for v in rf["confusion"][i]))
    print("\nĐộ quan trọng (xếp theo hoán vị trên val):")
    for r in imp_rows:
        mark = "*" if r["predicted_important"] else " "
        print(f"  {mark} {r['feature']:<13} hoán vị #{r['perm_rank']:<3}"
              f"{r['perm_mean']:+.4f} ±{r['perm_std']:.4f}   tạp chất #"
              f"{r['impurity_rank']:<3}{r['impurity']:.4f}")
    print("  (* = dự đoán quan trọng: ba đặc trưng của cổng Phase 4)")
    print("\nXáo theo NHÓM đặc trưng tương quan (val):")
    for r in grouped:
        print(f"  {r['group']:<26} macro-F1 giảm {r['drop_mean']:+.4f} "
              f"±{r['drop_std']:.4f}   nhầm trái<->phải {r['left_right_swaps']:5.1f}")
    print("\nMức sự kiện xấp xỉ (val):")
    for r in events:
        print(f"  {r['class']:<12} {r['n_events']} cử chỉ: >=1 cửa sổ đúng {r['hit_1']:.0%}, "
              f">=2 {r['hit_2']:.0%}; có cửa sổ ngược chiều {r['any_opposite']:.0%}")
    print("\nCửa sổ none bị báo nhầm, theo nhãn gốc IPN (val):")
    for r in alarms[:6]:
        print(f"  {r['src_label']:<5} {r['false_alarms']:>4}/{r['n_windows']:<6} "
              f"({r['rate']:.1%})")
    print("\nCổng kiểm tra Phase 6:")
    for check, ok, detail in checks:
        print(f"  [{'ĐẠT' if ok else 'KHÔNG ĐẠT'}] {check}: {detail}")
    print(f"\nMô hình: {relative_to_root(model_path)}")
    print(f"Bảng và hình: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
