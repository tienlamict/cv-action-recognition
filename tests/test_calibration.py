"""Kiểm thử hiệu chuẩn ngưỡng — cửa sổ tổng hợp, không đụng data/."""

import numpy as np
import pytest

from src import calibration, config, rules
from src.features import window_features
from src.preprocess import normalize_window
from tests.fixtures import make_static, make_swipe, make_wave, make_zoom

CLS = {name: i for i, name in enumerate(config.CLASSES)}


JITTER_PX = 0.5     # rung điểm mốc, để các cửa sổ cùng lớp không giống hệt nhau


def dataset(subject, n=12, none_maker=None, seed=0):
    """Cửa sổ đã chuẩn hoá của một người: none, hai lớp vuốt, hai lớp zoom."""
    none_maker = none_maker or (lambda i: make_static(seed=i))
    rng = np.random.default_rng(seed)
    X, y = [], []
    for i in range(n):
        X += [none_maker(i), make_swipe(+1), make_swipe(-1),
              make_zoom("in"), make_zoom("out")]
        y += [CLS["none"], CLS["swipe_left"], CLS["swipe_right"],
              CLS["zoom_in"], CLS["zoom_out"]]
    X = np.stack([normalize_window(w + rng.normal(0, JITTER_PX, w.shape))
                  for w in X]).astype(np.float32)
    return X, np.array(y), np.ones(len(y), np.float32), np.full(len(y), subject)


def test_calibration_chi_doc_tap_train():
    """Cửa sổ none của val/test là cú vuốt rất nhanh: nếu lọt vào thì ngưỡng
    max_vx bị kéo lên. Ngưỡng phải y hệt khi chỉ có dữ liệu train."""
    parts = [dataset("tr1"), dataset("va1", none_maker=lambda i: make_swipe(+1)),
             dataset("te1", none_maker=lambda i: make_swipe(-1))]
    X, y, pres, subj = (np.concatenate(p) for p in zip(*parts))
    splits = {"train": ["tr1"], "val": ["va1"], "test": ["te1"],
              "real_tune": [], "real_test": []}

    F, y_train = calibration.train_features(X, y, pres, subj, splits)
    assert F.shape[0] == y_train.size == np.sum(subj == "tr1")

    X0, y0, p0, s0 = dataset("tr1")
    F0, _ = calibration.train_features(X0, y0, p0, s0, splits)
    got = {r["threshold"]: r["value"] for r in calibration.propose(F, y_train)}
    want = {r["threshold"]: r["value"] for r in calibration.propose(F0, y0)}
    assert got == want


def test_calibration_de_xuat_hop_ly_tren_du_lieu_tong_hop(monkeypatch):
    """Dữ liệu tách sạch: ngưỡng nằm giữa hai nhóm, không cảnh báo chồng nhau.
    Với ngưỡng đề xuất, none và zoom đúng hết; vuốt mất khoảng 10% vì
    RULE_DX_HI đặt ĐÚNG ở phân vị 10 của |dx| (công thức SPEC)."""
    X, y, pres, subj = dataset("tr1")
    F, y = calibration.train_features(X, y, pres, subj, {"train": ["tr1"]})
    proposals = {r["threshold"]: r for r in calibration.propose(F, y)}

    assert set(proposals) == {"RULE_VX_HI", "RULE_DX_HI", "RULE_P_HI"}
    for name in ("RULE_VX_HI", "RULE_P_HI"):
        r = proposals[name]
        assert not r["overlap"]
        assert r["below_pct"] < r["value"] < r["above_pct"]
        assert r["reason"]

    for name, r in proposals.items():
        monkeypatch.setattr(config, name, r["value"])
    monkeypatch.setattr(config, "SWIPE_LEFT_SIGN", 1)
    pred = np.array([rules.classify(f)[0] for f in F])
    still_or_zoom = np.isin(y, [CLS["none"], CLS["zoom_in"], CLS["zoom_out"]])
    np.testing.assert_array_equal(pred[still_or_zoom], y[still_or_zoom])
    swipe = ~still_or_zoom
    assert np.mean(pred[swipe] == y[swipe]) >= 0.85
    assert set(pred[swipe]) <= {CLS["swipe_left"], CLS["swipe_right"], CLS["none"]}


def test_calibration_canh_bao_khi_hai_nhom_chong_nhau():
    """Vẫy tay (lớp none) nhanh hơn cú vuốt: hai phân vị chồng nhau."""
    X, y, pres, subj = dataset("tr1", none_maker=lambda i: make_wave())
    F, y = calibration.train_features(X, y, pres, subj, {"train": ["tr1"]})
    vx = {r["threshold"]: r for r in calibration.propose(F, y)}["RULE_VX_HI"]
    assert vx["overlap"]
    assert vx["value"] == pytest.approx((vx["below_pct"] + vx["above_pct"]) / 2)


def test_dac_trung_tong_hop_dung_nhu_luat_mong_doi():
    """Tiền đề của hai kiểm thử trên: vuốt nhanh hơn hẳn tay đứng yên."""
    vx = lambda w: window_features(normalize_window(w), 1.0)[  # noqa: E731
        list(calibration.FEATURE_NAMES).index("max_vx")]
    assert vx(make_swipe(+1)) > 5 * vx(make_static())
