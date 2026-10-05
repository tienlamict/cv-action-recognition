"""Kiểm thử mô hình luật — ngưỡng đặt bằng monkeypatch, không đụng data/."""

import numpy as np
import pytest

from src import config, rules
from src.features import FEATURE_NAMES, window_features
from src.preprocess import normalize_window
from tests.fixtures import make_static, make_swipe, make_zoom

CLS = {name: i for i, name in enumerate(config.CLASSES)}


@pytest.fixture
def thresholds(monkeypatch):
    monkeypatch.setattr(config, "RULE_VX_HI", 1.5)
    monkeypatch.setattr(config, "RULE_DX_HI", 0.5)
    monkeypatch.setattr(config, "RULE_P_HI", 0.3)
    monkeypatch.setattr(config, "SWIPE_LEFT_SIGN", 1)


def feat(presence=1.0, **values):
    out = np.zeros(len(FEATURE_NAMES), dtype=np.float32)
    out[FEATURE_NAMES.index("presence")] = presence
    for name, value in values.items():
        out[FEATURE_NAMES.index(name)] = value
    return out


def test_rules_tra_ve_none_khi_khong_thoa_mau_hinh_nao(thresholds):
    assert rules.classify(feat()) == (CLS["none"], 1.0)
    # vuốt nhanh nhưng không dời ngang đủ, zoom nhỏ hơn ngưỡng
    assert rules.classify(feat(max_vx=5.0, dx=0.1, pinch_delta=0.2))[0] == CLS["none"]
    assert rules.classify(feat(max_vx=1.0, dx=2.0))[0] == CLS["none"]


def test_rules_dao_khi_dao_SWIPE_LEFT_SIGN(thresholds, monkeypatch):
    """Đảo hằng số → hai nhãn vuốt đổi chỗ. Dấu dx không viết cứng ở đâu."""
    right_in_image = feat(max_vx=3.0, dx=+1.0)
    left_in_image = feat(max_vx=3.0, dx=-1.0)
    assert rules.classify(right_in_image)[0] == CLS["swipe_left"]
    assert rules.classify(left_in_image)[0] == CLS["swipe_right"]

    monkeypatch.setattr(config, "SWIPE_LEFT_SIGN", -1)
    assert rules.classify(right_in_image)[0] == CLS["swipe_right"]
    assert rules.classify(left_in_image)[0] == CLS["swipe_left"]


def test_rules_vuot_duoc_xet_truoc_zoom(thresholds):
    """Cú hất IPN mở bàn tay ra: pinch_delta lớn cũng không được thắng vuốt."""
    both = feat(max_vx=3.0, dx=1.0, pinch_delta=2.0)
    assert rules.classify(both)[0] == CLS["swipe_left"]
    assert rules.classify(feat(pinch_delta=2.0))[0] == CLS["zoom_in"]
    assert rules.classify(feat(pinch_delta=-2.0))[0] == CLS["zoom_out"]


def test_rules_presence_thap_luon_ra_none(thresholds):
    strong = dict(max_vx=9.0, dx=3.0, pinch_delta=3.0)
    low = config.MIN_PRESENCE - 0.01
    assert rules.classify(feat(presence=low, **strong)) == (CLS["none"], 1.0)
    assert rules.classify(feat(presence=1.0, **strong))[0] != CLS["none"]


def test_rules_do_tin_trong_khoang_va_tang_theo_bien_do(thresholds):
    _, at_edge = rules.classify(feat(pinch_delta=0.31))
    _, double = rules.classify(feat(pinch_delta=0.6))
    _, huge = rules.classify(feat(pinch_delta=5.0))
    assert 0.5 <= at_edge < double <= huge == 1.0
    _, swipe = rules.classify(feat(max_vx=3.0, dx=0.55))    # dx vừa chạm ngưỡng
    assert swipe == pytest.approx(0.5 + 0.5 * 0.1, abs=1e-3), "lấy điều kiện yếu nhất"


def test_rules_dung_ngay_khi_chua_hieu_chuan(thresholds, monkeypatch):
    monkeypatch.setattr(config, "RULE_P_HI", None)
    with pytest.raises(RuntimeError, match="RULE_P_HI"):
        rules.classify(feat())


def test_rules_tren_cua_so_tong_hop(thresholds):
    """Đi qua đúng normalize_window + window_features như lúc chạy thật."""
    def predict(win):
        return rules.classify(window_features(normalize_window(win), 1.0))[0]

    assert predict(make_swipe(+1)) == CLS["swipe_left"]     # SWIPE_LEFT_SIGN = +1
    assert predict(make_swipe(-1)) == CLS["swipe_right"]
    assert predict(make_zoom("in")) == CLS["zoom_in"]
    assert predict(make_zoom("out")) == CLS["zoom_out"]
    assert predict(make_static()) == CLS["none"]
