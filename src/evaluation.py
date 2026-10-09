"""Đánh giá mức cửa sổ dùng chung cho mọi mô hình — và chốt kỹ thuật của luật 13.

Mọi script đánh giá (``eval_rules.py``, ``train_rf.py``, ``evaluate.py``) đi qua
đây, nên cả ba tính macro-F1, hai đường cơ sở và ma trận nhầm lẫn theo đúng một
cách, và ghi chung một bảng so sánh mô hình.

**Luật 13 — tập test và real_test chạy đúng một lần, ở cuối.** :func:`guard_split`
từ chối hai tập này nếu không có ``--final``; khi có, nó ghi một dòng vào
``TEST_USED_LOG`` (tên tập, thời điểm, mô hình, dòng lệnh, toàn bộ hằng số) TRƯỚC
khi tính bất cứ thứ gì — chạm vào test là phải để lại dấu vết, kể cả khi lần chạy
đó lỗi giữa chừng.
"""

import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.metrics import (classification_report, confusion_matrix,
                             f1_score, precision_recall_fscore_support)

from src import config
from src.features import FEATURE_NAMES, window_features
from src.runlog import config_snapshot
from src.splits import split_of
from src.tables import write_table

LABELS = list(range(len(config.CLASSES)))
FINAL_ONLY = ("test", "real_test")
COMPARISON_COLUMNS = ["model", "split", "n_windows", "macro_f1",
                      "baseline_random", "baseline_none", "run"]


def split_features(X, y, presence, subject, splits, split):
    """Đặc trưng của các cửa sổ thuộc đúng một tập — lọc theo cột người.

    Returns:
        ``(F (n, 15) float32, y (n,), pick (N,) bool)``.
    """
    pick = split_of(subject, splits) == split
    if not pick.any():
        return (np.empty((0, len(FEATURE_NAMES)), dtype=np.float32),
                np.asarray(y)[pick], pick)
    F = np.stack([window_features(win, ratio)
                  for win, ratio in zip(X[pick], presence[pick])])
    return F, np.asarray(y)[pick], pick


def macro_f1(y_true, y_pred):
    return float(f1_score(y_true, y_pred, labels=LABELS, average="macro",
                          zero_division=0))


def baselines(y_true, seed=config.SEED):
    """Macro-F1 của hai đường cơ sở: đoán ngẫu nhiên đều 5 lớp, và luôn none."""
    rng = np.random.default_rng(seed)
    random_pred = rng.integers(0, len(LABELS), size=np.asarray(y_true).size)
    return (macro_f1(y_true, random_pred),
            macro_f1(y_true, np.zeros_like(y_true)))


def summarize(y_true, y_pred):
    """Mọi con số mức cửa sổ của một lần dự đoán.

    Returns:
        dict: ``macro_f1``; ``confusion`` (thô, hàng = thật, cột = đoán);
        ``confusion_row`` (chuẩn hoá theo hàng — mỗi hàng là recall phân theo
        lớp đoán, hàng không có mẫu để 0); ``per_class`` (list dict
        precision/recall/f1/support); ``report`` (``classification_report``
        dạng chữ, 4 chữ số).
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=LABELS)
    totals = cm.sum(axis=1, keepdims=True)
    cm_row = np.divide(cm, totals, out=np.zeros(cm.shape), where=totals > 0)
    p, r, f, n = precision_recall_fscore_support(y_true, y_pred, labels=LABELS,
                                                 zero_division=0)
    return {
        "macro_f1": macro_f1(y_true, y_pred),
        "confusion": cm,
        "confusion_row": cm_row,
        "per_class": [{"class": c, "precision": float(p[i]), "recall": float(r[i]),
                       "f1": float(f[i]), "support": int(n[i])}
                      for i, c in enumerate(config.CLASSES)],
        "report": classification_report(y_true, y_pred, labels=LABELS,
                                        target_names=config.CLASSES, digits=4,
                                        zero_division=0),
    }


def write_summary(summary, run_dir, prefix=""):
    """Ghi ma trận nhầm lẫn thô và chuẩn hoá theo hàng, bảng từng lớp, và
    ``classification_report`` vào ``run_dir``."""
    run_dir = Path(run_dir)
    corner = "true \\ pred"
    for name, matrix, fmt in (("confusion", summary["confusion"], int),
                              ("confusion_row", summary["confusion_row"], float)):
        write_table([{corner: config.CLASSES[i],
                      **{config.CLASSES[j]: fmt(matrix[i, j]) for j in LABELS}}
                     for i in LABELS],
                    [corner, *config.CLASSES], run_dir / f"{prefix}{name}")
    write_table(summary["per_class"], ["class", "precision", "recall", "f1", "support"],
                run_dir / f"{prefix}per_class")
    (run_dir / f"{prefix}classification_report.txt").write_text(
        summary["report"], encoding="utf-8")


def upsert_comparison(row, stem=config.MODEL_COMPARISON):
    """Thêm hoặc thay hàng ``(model, split)`` trong bảng so sánh mô hình."""
    csv_path = Path(stem).with_suffix(".csv")
    rows = []
    if csv_path.is_file():
        with open(csv_path, newline="", encoding="utf-8") as f:
            rows = [_numeric(r) for r in csv.DictReader(f)
                    if (r["model"], r["split"]) != (row["model"], row["split"])]
    rows.append(row)
    rows.sort(key=_comparison_order)
    write_table(rows, COMPARISON_COLUMNS, stem)
    return csv_path


#: Thứ tự hàng trong bảng so sánh: mô hình theo thứ tự ra đời, rồi theo tập.
MODEL_ORDER = ("rules", "rf", "lstm")


def _comparison_order(row):
    from src.splits import SPLIT_NAMES
    model = row["model"]
    rank = MODEL_ORDER.index(model) if model in MODEL_ORDER else len(MODEL_ORDER)
    split = SPLIT_NAMES.index(row["split"]) if row["split"] in SPLIT_NAMES else len(SPLIT_NAMES)
    return rank, model, split


def _numeric(row):
    """Hàng đọc lại từ CSV: đổi các cột số về số, để bảng .md định dạng đồng
    nhất với hàng mới thêm."""
    out = dict(row)
    out["n_windows"] = int(out["n_windows"])
    for key in ("macro_f1", "baseline_random", "baseline_none"):
        out[key] = float(out[key])
    return out


def guard_split(split, final, model, details=None, log_path=None):
    """Chốt luật 13. Gọi TRƯỚC khi đọc bất cứ thứ gì của tập đang đánh giá.

    Với ``train``, ``val``, ``real_tune``: không làm gì. Với ``test``,
    ``real_test``: dừng nếu thiếu ``final``; có ``final`` thì ghi một dòng JSON
    vào ``log_path`` (mặc định ``TEST_USED_LOG``) rồi cho chạy tiếp.

    Raises:
        SystemExit: tập chỉ-chạy-một-lần mà không có ``final``.
    """
    if split not in FINAL_ONLY:
        return None
    if not final:
        raise SystemExit(
            f"Tập {split} chỉ chạy ĐÚNG MỘT LẦN ở cuối dự án (luật 13). Thêm "
            "--final nếu đúng là lúc đó — lần chạy sẽ được ghi vào "
            f"{Path(log_path or config.TEST_USED_LOG).name}.")
    log_path = Path(log_path or config.TEST_USED_LOG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"time": datetime.now().isoformat(timespec="seconds"),
             "split": split, "model": model,
             "command": subprocess.list2cmdline(["python", *sys.argv]),
             "details": details or {}, "config": config_snapshot()}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    return log_path


def predict_windows(model_name, F):
    """Dự đoán cả một tập đặc trưng bằng một mô hình đã có.

    ``rules`` gọi luật từng cửa sổ; ``rf`` nạp mô hình đã lưu và dự đoán cả lô
    một lần — cùng kết quả với ``ForestClassifier`` của demo (lớp có xác suất
    cao nhất), chỉ nhanh hơn.

    Returns:
        ``(pred (n,) int64, details)`` — ``details`` mô tả mô hình đã dùng, để
        ghi vào manifest và ``TEST_USED_LOG``.
    """
    from src import forest, rules     # nạp lười: rf kéo theo scikit-learn

    if model_name == "rules":
        details = {k: getattr(config, k) for k in ("RULE_VX_HI", "RULE_DX_HI",
                                                   "RULE_P_HI", "SWIPE_LEFT_SIGN")}
        return np.array([rules.classify(f)[0] for f in F], dtype=np.int64), details
    if model_name == "rf":
        bundle = forest.load_bundle()
        details = {"model_file": config.RF_MODEL_PATH.name,
                   "model_sha256": forest.file_sha256(config.RF_MODEL_PATH),
                   "created": bundle.get("created")}
        if len(F) == 0:
            return np.empty(0, dtype=np.int64), details
        return bundle["model"].predict(np.asarray(F, dtype=np.float32)).astype(np.int64), details
    raise ValueError(f"Không biết mô hình '{model_name}' — có: rules, rf")
