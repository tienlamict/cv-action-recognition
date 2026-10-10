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


def test_su_kien_xap_xi_gom_cua_so_lien_nhau():
    """Hai cú vuốt trái (3 + 2 cửa sổ liền nhau) trong một clip: cú đầu được
    nhận đúng 2 lần, cú sau có một cửa sổ bị đoán ngược chiều."""
    y = np.array([1, 1, 1, 1, 1, 2, 3, 4])
    pred = np.array([1, 0, 1, 2, 0, 2, 3, 4])
    clip = np.array(["c"] * 8)
    t0 = np.array([0.0, 0.2, 0.4, 5.0, 5.2, 9.0, 12.0, 15.0])
    rows = {r["class"]: r for r in evaluation.event_rows(y, pred, clip, t0)}
    left = rows["swipe_left"]
    assert left["n_events"] == 2
    assert left["hit_1"] == 0.5 and left["hit_2"] == 0.5
    assert left["any_opposite"] == 0.5


def test_ty_le_bao_nham_theo_nhan_goc():
    y_true = np.array([0, 0, 0, 0, 1])
    y_pred = np.array([1, 0, 2, 0, 1])
    src = np.array(["B0B", "B0B", "D0X", "D0X", "G05"])
    rows = {r["src_label"]: r for r in evaluation.false_alarm_rows(y_true, y_pred, src)}
    assert set(rows) == {"B0B", "D0X"}, "chỉ xét cửa sổ none"
    assert rows["B0B"]["rate"] == 0.5 and rows["B0B"]["swipe_left"] == 1
    assert rows["D0X"]["swipe_right"] == 1


def test_bao_nham_tinh_theo_cum():
    """Cửa sổ none liền nhau bị đoán cùng một lớp là một cụm; đổi lớp, đứt
    quãng thời gian hay sang clip khác thì sang cụm mới. Cửa sổ cử chỉ thật
    không tính."""
    y = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
    pred = np.array([1, 1, 2, 0, 1, 1, 1, 3, 3, 1])
    clip = np.array(["a"] * 5 + ["b"] * 5)
    t0 = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 0.0, 5.0, 5.2, 5.4, 5.6])
    n, minutes = evaluation.alarm_clusters(y, pred, clip, t0)
    assert n == 6       # a: [1 1] [2] [1]; b: [1] [1] (đứt quãng) [3 3]
    assert minutes == pytest.approx(9 * config.STRIDE_SEC / 60)


def test_tham_do_phan_thuc_te_di_qua_dung_duong_ong():
    """Phép đồng nhất không rung: đặc trưng đúng bằng window_features của cửa
    sổ gốc. Cửa sổ normalize_window từ chối ra nhãn -1 và hàng NaN, và không
    được đưa vào mô hình."""
    from src.features import window_features
    from src.preprocess import normalize_window

    X, _, pres, _ = labeled_windows("a", n=1)
    seen = []

    def predict(F):
        seen.append(len(F))
        return np.full(len(F), 3)

    pred, F = evaluation.probe_windows(predict, X, pres, lambda w: w,
                                       np.random.default_rng(0), sigma=0.0)
    expected = np.stack([window_features(normalize_window(w), r) for w, r in zip(X, pres)])
    np.testing.assert_allclose(F, expected, rtol=1e-6, atol=1e-6)
    assert np.all(pred == 3) and seen == [len(X)]

    def first_step_lost(win):
        out = win.copy()
        out[0] = np.nan
        return out

    pred, F = evaluation.probe_windows(predict, X, pres, first_step_lost,
                                       np.random.default_rng(0), sigma=0.0)
    assert np.all(pred == -1) and np.all(np.isnan(F)) and seen == [len(X)]


def test_tham_do_mo_hinh_doc_cua_so_nhan_cung_cua_so_da_rung():
    """LSTM nhận cửa sổ đã chuẩn hoá; cùng seed thì cùng rung như rừng nhận
    qua đặc trưng — hai mô hình bị thử trên đúng các cửa sổ như nhau."""
    from src.features import window_features

    X, _, pres, _ = labeled_windows("a", n=1)
    got = {}

    def by_window(W):
        got["W"] = W.copy()
        return np.zeros(len(W), dtype=np.int64)

    _, F_window = evaluation.probe_windows(by_window, X, pres, lambda w: w,
                                           np.random.default_rng(5), sigma=0.01,
                                           input_kind="window")
    _, F_features = evaluation.probe_windows(lambda F: np.zeros(len(F)), X, pres,
                                             lambda w: w, np.random.default_rng(5),
                                             sigma=0.01)
    assert got["W"].shape == X.shape
    np.testing.assert_array_equal(F_window, F_features)
    np.testing.assert_allclose(
        np.stack([window_features(w, r) for w, r in zip(got["W"], pres)]), F_window,
        rtol=1e-6)
