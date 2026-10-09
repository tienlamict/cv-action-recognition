"""Hiệu chuẩn ba ngưỡng của ``rules.py`` — Phase 5. **Chỉ dùng tập train.**

Mỗi ngưỡng là trung điểm giữa phân vị cao (``CALIB_NONE_PCT``) của nhóm phải
nằm DƯỚI ngưỡng và phân vị thấp (``CALIB_TARGET_PCT``) của nhóm phải nằm TRÊN:

- ``RULE_VX_HI`` — ``max_vx``: lớp ``none`` dưới, hai lớp vuốt trên;
- ``RULE_DX_HI`` — phân vị thấp của ``|dx|`` trên hai lớp vuốt (không có nhóm
  dưới: ``dx`` chỉ để lấy hướng và chặn cú dời quá nhỏ);
- ``RULE_P_HI`` — ``|pinch_delta|``: lớp ``none`` cộng hai lớp vuốt dưới, hai
  lớp zoom trên.

Hai phân vị chồng nhau (phân vị cao của nhóm dưới lớn hơn phân vị thấp của
nhóm trên) thì vẫn đề xuất trung điểm nhưng kèm cảnh báo — nghĩa là luật một
ngưỡng không tách sạch hai nhóm, và sai số ở cả hai phía là không tránh được.
"""

import numpy as np

from src import config
from src.evaluation import split_features
from src.features import FEATURE_NAMES

_IDX = {name: i for i, name in enumerate(FEATURE_NAMES)}
_CLS = {name: i for i, name in enumerate(config.CLASSES)}


def train_features(X, y, presence, subject, splits):
    """Đặc trưng của các cửa sổ thuộc tập ``train`` — và CHỈ tập ``train``.

    Returns:
        ``(F, y)`` — ``F`` ``(n, 15)``.
    """
    F, y_train, _ = split_features(X, y, presence, subject, splits, "train")
    return F, y_train


def _midpoint(below, above, name):
    hi = float(np.percentile(below, config.CALIB_NONE_PCT))
    lo = float(np.percentile(above, config.CALIB_TARGET_PCT))
    row = {"threshold": name, "below_pct": hi, "above_pct": lo,
           "value": (hi + lo) / 2, "overlap": hi > lo}
    return row


def propose(F, y):
    """Đề xuất ba ngưỡng từ ma trận đặc trưng của tập train.

    Returns:
        list dict, mỗi ngưỡng một dòng: ``threshold``, ``value``, hai phân vị
        dùng để tính (``below_pct``, ``above_pct``), ``overlap``, và
        ``reason`` — câu giải thích để ghi vào ``thresholds.md``.
    """
    F, y = np.asarray(F, dtype=np.float64), np.asarray(y)
    none = y == _CLS["none"]
    swipe = np.isin(y, [_CLS["swipe_left"], _CLS["swipe_right"]])
    zoom = np.isin(y, [_CLS["zoom_in"], _CLS["zoom_out"]])
    vx = F[:, _IDX["max_vx"]]
    adx = np.abs(F[:, _IDX["dx"]])
    ap = np.abs(F[:, _IDX["pinch_delta"]])
    none_pct, target_pct = config.CALIB_NONE_PCT, config.CALIB_TARGET_PCT

    vx_row = _midpoint(vx[none], vx[swipe], "RULE_VX_HI")
    vx_row["reason"] = (f"trung điểm của p{none_pct} max_vx lớp none "
                        f"({vx_row['below_pct']:.3f}) và p{target_pct} max_vx "
                        f"hai lớp vuốt ({vx_row['above_pct']:.3f})")

    dx_value = float(np.percentile(adx[swipe], target_pct))
    dx_row = {"threshold": "RULE_DX_HI", "below_pct": float("nan"),
              "above_pct": dx_value, "value": dx_value, "overlap": False,
              "reason": f"p{target_pct} của |dx| trên hai lớp vuốt"}

    p_row = _midpoint(ap[none | swipe], ap[zoom], "RULE_P_HI")
    p_row["reason"] = (f"trung điểm của p{none_pct} |pinch_delta| lớp none "
                       f"cộng hai lớp vuốt ({p_row['below_pct']:.3f}) và "
                       f"p{target_pct} |pinch_delta| hai lớp zoom "
                       f"({p_row['above_pct']:.3f})")
    return [vx_row, dx_row, p_row]
