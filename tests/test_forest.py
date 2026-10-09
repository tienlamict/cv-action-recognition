"""Kiểm thử rừng ngẫu nhiên — dữ liệu tổng hợp, không đụng data/ hay results/."""

import joblib
import numpy as np
import pytest

from src import config, evaluation, forest
from src.features import FEATURE_NAMES, window_features
from tests.fixtures import labeled_windows


def features(parts):
    X, y, pres, _ = (np.concatenate(p) for p in zip(*parts))
    return np.stack([window_features(w, r) for w, r in zip(X, pres)]), y


@pytest.fixture(scope="module")
def trained():
    F, y = features([labeled_windows("tr", n=20, seed=1)])
    return forest.train_forest(F, y, n_jobs=1)


def test_rung_hoc_duoc_du_lieu_tong_hop(trained):
    F, y = features([labeled_windows("va", n=8, seed=2)])
    assert evaluation.macro_f1(y, trained.predict(F)) > 0.9
    assert trained.n_estimators == config.RF_N_ESTIMATORS
    assert trained.class_weight == config.RF_CLASS_WEIGHT


def test_luu_nap_va_chan_lech_danh_sach_dac_trung(trained, tmp_path):
    path = forest.save_bundle(trained, tmp_path / "rf.joblib", trained_on="train")
    bundle = forest.load_bundle(path)
    assert bundle["feature_names"] == FEATURE_NAMES and bundle["trained_on"] == "train"

    bundle["feature_names"] = FEATURE_NAMES[::-1]
    joblib.dump(bundle, path)
    with pytest.raises(ValueError, match="đặc trưng"):
        forest.load_bundle(path)


def test_bo_phan_loai_cho_demo_nap_luoi_va_tra_xac_suat_cao_nhat(trained, tmp_path):
    missing = forest.ForestClassifier(tmp_path / "chua_co.joblib")    # không lỗi
    with pytest.raises(FileNotFoundError, match="train_rf.py"):
        missing(np.zeros(len(FEATURE_NAMES)))

    path = forest.save_bundle(trained, tmp_path / "rf.joblib")
    classify = forest.ForestClassifier(path)
    F, _ = features([labeled_windows("x", n=1, seed=3)])
    for f in F:
        label, confidence = classify(f)
        proba = trained.predict_proba(f.reshape(1, -1))[0]
        assert label == trained.classes_[np.argmax(proba)]
        assert confidence == pytest.approx(proba.max())
        assert 1 / len(config.CLASSES) <= confidence <= 1.0


def test_danh_gia_theo_lo_khop_voi_demo(trained, tmp_path, monkeypatch):
    """evaluate.py dự đoán cả lô; demo dự đoán từng cửa sổ — phải ra cùng nhãn."""
    path = forest.save_bundle(trained, tmp_path / "rf.joblib")
    monkeypatch.setattr(config, "RF_MODEL_PATH", path)
    F, _ = features([labeled_windows("y", n=3, seed=4)])

    batch, details = evaluation.predict_windows("rf", F)
    one_by_one = [forest.ForestClassifier(path)(f)[0] for f in F]
    np.testing.assert_array_equal(batch, one_by_one)
    assert details["model_sha256"] == forest.file_sha256(path)
