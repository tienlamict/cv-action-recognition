"""Mô hình luật — hệ thống chạy được đầu tiên (Phase 5).

Ba ngưỡng chọn trên tập train của IPN bằng ``scripts/calibrate_rules.py``, dựa
trên đúng ba đặc trưng của cổng Phase 4 (quyết định 2026-10-05):

- ``max_vx`` — tốc độ ngang đỉnh của cổ tay: tách cú hất khỏi lớp nền;
- ``dx`` — dời ngang: hướng của cú hất, đọc qua ``SWIPE_LEFT_SIGN``;
- ``pinch_delta`` — độ mở cái–trỏ cuối − đầu: zoom in dương, zoom out âm.

Thứ tự kiểm tra CỐ ĐỊNH::

    presence < MIN_PRESENCE                       → none
    max_vx > RULE_VX_HI và |dx| > RULE_DX_HI      → swipe_left nếu sign(dx) == SWIPE_LEFT_SIGN,
                                                    ngược lại swipe_right
    pinch_delta > RULE_P_HI                       → zoom_in
    pinch_delta < -RULE_P_HI                      → zoom_out
    còn lại                                       → none

Vuốt xét TRƯỚC zoom: cú hất của IPN mở bàn tay ra, nên ``pinch_delta`` của
cửa sổ vuốt có khi lớn (trung vị +0,56 ở ``swipe_right`` trên train), còn zoom
gần như không dời cổ tay (``max_vx`` của zoom thấp hơn hẳn).

Mọi hằng số đọc qua ``config.require_measured`` LÚC GỌI HÀM, nên kiểm thử
``monkeypatch`` được và chưa hiệu chuẩn thì dừng ngay.
"""

import numpy as np

from src import config
from src.features import FEATURE_NAMES

_IDX = {name: i for i, name in enumerate(FEATURE_NAMES)}
_CLS = {name: i for i, name in enumerate(config.CLASSES)}


def _confidence(values, thresholds):
    """``0.5 + 0.5 × min_i clip(v_i/θ_i − 1, 0, 1)`` — heuristic, không phải
    xác suất: vừa chạm ngưỡng là 0,5, gấp đôi ngưỡng trở lên là 1,0."""
    ratios = [np.clip(v / t - 1.0, 0.0, 1.0) for v, t in zip(values, thresholds)]
    return float(0.5 + 0.5 * min(ratios))


def classify(feat):
    """Phân loại một vector đặc trưng.

    Args:
        feat: ``(15,)`` theo thứ tự ``FEATURE_NAMES``.

    Returns:
        ``(label, confidence)`` — ``label`` là chỉ số trong ``config.CLASSES``;
        ``confidence`` theo :func:`_confidence` trên các điều kiện của luật vừa
        khớp. Lớp ``none`` trả về ``1.0`` (cũng là heuristic).
    """
    feat = np.asarray(feat, dtype=np.float64)
    if feat[_IDX["presence"]] < config.MIN_PRESENCE:
        return _CLS["none"], 1.0

    vx_hi = config.require_measured("RULE_VX_HI")
    dx_hi = config.require_measured("RULE_DX_HI")
    p_hi = config.require_measured("RULE_P_HI")
    sign = config.require_measured("SWIPE_LEFT_SIGN")

    max_vx, dx = feat[_IDX["max_vx"]], feat[_IDX["dx"]]
    if max_vx > vx_hi and abs(dx) > dx_hi:
        label = "swipe_left" if np.sign(dx) == sign else "swipe_right"
        return _CLS[label], _confidence((max_vx, abs(dx)), (vx_hi, dx_hi))

    pinch_delta = feat[_IDX["pinch_delta"]]
    if pinch_delta > p_hi:
        return _CLS["zoom_in"], _confidence((pinch_delta,), (p_hi,))
    if pinch_delta < -p_hi:
        return _CLS["zoom_out"], _confidence((-pinch_delta,), (p_hi,))
    return _CLS["none"], 1.0
