"""Kiểm thử mô hình ghép (vuốt theo LSTM, zoom theo rừng) — không đụng data/."""

import numpy as np
import pytest

from src import config, evaluation, forest, models, training
from src.features import window_features
from src.hybrid import HybridClassifier, hybrid_labels
from src.live import LivePredictor
from tests.fixtures import labeled_windows


def test_luat_ghep_vuot_theo_lstm_zoom_theo_rung():
    """Vuốt của LSTM thắng; zoom chỉ lấy từ rừng; zoom của LSTM và vuốt của
    rừng bị bỏ qua."""
    lstm = [1, 2, 3, 0, 4, 0, 1]
    rf = [3, 0, 0, 4, 1, 3, 4]
    np.testing.assert_array_equal(hybrid_labels(lstm, rf), [1, 2, 0, 4, 0, 3, 1])


@pytest.fixture
def saved_models(tmp_path, monkeypatch):
    """Một LSTM nhỏ và một rừng đã lưu ra tmp, config trỏ tới chúng."""
    X, y, pres, _ = labeled_windows("tr", n=6, seed=1)
    F = np.stack([window_features(w, r) for w, r in zip(X, pres)])
    rf_path = forest.save_bundle(forest.train_forest(F, y, n_jobs=1), tmp_path / "rf.joblib")
    training.set_seed(0)
    lstm_path = models.save_checkpoint(models.LSTMClassifier(hidden=16), tmp_path / "m.pt")
    monkeypatch.setattr(config, "RF_MODEL_PATH", rf_path)
    monkeypatch.setattr(config, "LSTM_MODEL_PATH", lstm_path)
    return lstm_path, rf_path


def test_mo_hinh_ghep_cua_demo_khop_danh_gia_theo_lo(saved_models):
    """demo.py dự đoán từng cửa sổ, evaluate.py dự đoán cả lô — cùng nhãn; độ
    tin là xác suất của mô hình đã quyết định nhãn."""
    lstm_path, rf_path = saved_models
    X, _, pres, _ = labeled_windows("va", n=3, seed=2)
    F = np.stack([window_features(w, r) for w, r in zip(X, pres)])

    batch, details = evaluation.predict_windows("hybrid", F, X)
    assert set(details) == {"lstm", "rf"}
    hybrid = HybridClassifier(lstm_path, rf_path).load()
    for k, (win, f) in enumerate(zip(X, F)):
        label, confidence = hybrid(win, f)
        assert label == batch[k]
        p_lstm, p_rf = hybrid.lstm.proba(win), hybrid.forest.proba(f)
        expected = (p_lstm[label] if label in (1, 2) else p_rf[label] if label in (3, 4)
                    else max(p_lstm[0], p_rf[0]))
        assert confidence == pytest.approx(expected)


def test_xac_suat_cua_hai_bo_phan_loai(saved_models):
    lstm_path, rf_path = saved_models
    X, _, pres, _ = labeled_windows("x", n=1, seed=3)
    p_rf = forest.ForestClassifier(rf_path).proba(window_features(X[0], pres[0]))
    p_lstm = models.LSTMRunner(lstm_path).proba(X[0])
    for p in (p_rf, p_lstm):
        assert p.shape == (len(config.CLASSES),) and p.sum() == pytest.approx(1.0)


def test_live_dua_ca_cua_so_lan_dac_trung_cho_mo_hinh_ghep():
    class BothModel:
        input_kind = "both"
        seen = []

        def __call__(self, win, features):
            self.seen.append((win.shape, features.shape))
            return 0, 1.0

    model = BothModel()
    predictor = LivePredictor(model)
    X, _, _, _ = labeled_windows("y", n=1)
    xy = np.concatenate([X[0]] * 5) * 0.1 + 0.5        # toạ độ [0, 1] hợp lệ
    for i, frame in enumerate(xy):
        predictor.update(i / 30, frame, config.CAM_W, config.CAM_H)
    assert model.seen and all(s == ((config.T, 21, 2), (15,)) for s in model.seen)
