"""Kiểm thử phần đánh giá dùng chung và chốt luật 13 — không đụng data/."""

import json
import sys

import numpy as np
import pytest
from sklearn.metrics import f1_score

from src import config, evaluation
from tests.fixtures import labeled_windows
from tests.scripts_import import load_script


def test_chot_luat_13_tu_choi_test_khi_thieu_final(tmp_path):
    log = tmp_path / "TEST_USED.log"
    for split in ("test", "real_test"):
        with pytest.raises(SystemExit, match="luật 13"):
            evaluation.guard_split(split, False, "rf", log_path=log)
    assert not log.exists(), "bị từ chối thì không được tính là đã dùng test"

    for split in ("train", "val", "real_tune"):
        assert evaluation.guard_split(split, False, "rf", log_path=log) is None
    assert not log.exists()


def test_chot_luat_13_ghi_moi_lan_cham_test(tmp_path):
    """Có --final: mỗi lần chạm test là một dòng JSON, kèm tên tập, thời
    điểm, mô hình và cấu hình."""
    log = tmp_path / "TEST_USED.log"
    evaluation.guard_split("test", True, "rf", {"model_sha256": "abc"}, log_path=log)
    evaluation.guard_split("real_test", True, "rules", log_path=log)

    entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [e["split"] for e in entries] == ["test", "real_test"]
    assert [e["model"] for e in entries] == ["rf", "rules"]
    assert entries[0]["details"] == {"model_sha256": "abc"}
    assert entries[0]["time"] and entries[0]["command"]
    assert entries[0]["config"]["SEED"] == config.SEED


def test_evaluate_tu_choi_truoc_khi_doc_du_lieu(monkeypatch, tmp_path):
    """Script dừng ở chốt luật 13 trước cả khi mở file cửa sổ (không tồn tại)."""
    script = load_script("evaluate")
    monkeypatch.setattr(sys, "argv", ["evaluate.py", "--model", "rf", "--split",
                                      "test", "--windows", str(tmp_path / "x.npz")])
    with pytest.raises(SystemExit, match="luật 13"):
        script.main()


def test_tom_tat_ma_tran_nham_lan_va_macro_f1():
    y_true = np.array([0, 0, 0, 1, 1, 2, 3, 4, 4, 4])
    y_pred = np.array([0, 1, 0, 1, 0, 2, 4, 4, 4, 0])
    s = evaluation.summarize(y_true, y_pred)

    assert s["confusion"].sum() == y_true.size
    np.testing.assert_allclose(s["confusion_row"].sum(axis=1), 1.0)
    assert s["confusion_row"][0, 1] == pytest.approx(1 / 3)
    assert s["macro_f1"] == pytest.approx(
        f1_score(y_true, y_pred, labels=range(5), average="macro", zero_division=0))
    assert all(c in s["report"] for c in config.CLASSES)

    empty_row = evaluation.summarize(np.array([0, 0]), np.array([0, 1]))
    np.testing.assert_allclose(empty_row["confusion_row"][2], 0.0)


def test_hai_duong_co_so():
    y = np.array([0] * 90 + [1, 2, 3, 4] * 2 + [0, 0])
    random_f1, none_f1 = evaluation.baselines(y)
    assert none_f1 == pytest.approx(evaluation.macro_f1(y, np.zeros_like(y)))
    assert 0 < random_f1 < none_f1
    assert evaluation.baselines(y) == (random_f1, none_f1), "cùng seed, cùng số"


def test_lay_dac_trung_dung_mot_tap():
    parts = [labeled_windows(s, n=2) for s in ("a", "b", "c")]
    X, y, pres, subj = (np.concatenate(p) for p in zip(*parts))
    splits = {"train": ["a"], "val": ["b"], "test": ["c"]}

    F, y_val, pick = evaluation.split_features(X, y, pres, subj, splits, "val")
    assert F.shape == (10, 15) and np.all(subj[pick] == "b")
    F, _, _ = evaluation.split_features(X, y, pres, subj, splits, "real_test")
    assert F.shape == (0, 15)


def test_bang_so_sanh_thay_dung_hang(tmp_path):
    stem = tmp_path / "comparison"
    row = {"model": "rf", "split": "val", "n_windows": 1, "macro_f1": 0.5,
           "baseline_random": 0.1, "baseline_none": 0.2, "run": "a"}
    evaluation.upsert_comparison(row, stem)
    evaluation.upsert_comparison({**row, "model": "rules", "macro_f1": 0.3}, stem)
    evaluation.upsert_comparison({**row, "macro_f1": 0.6, "run": "b"}, stem)

    lines = stem.with_suffix(".csv").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3, "mỗi (mô hình, tập) một hàng"
    assert lines[1].startswith("rules,val"), "luật luôn là hàng đầu tiên"
    assert lines[2].startswith("rf,val,1,0.6")
    md = stem.with_suffix(".md").read_text(encoding="utf-8")
    assert "0.3000" in md or "| 0.3 |" in md, "hàng đọc lại vẫn định dạng như số"
