"""Quyết định dấu ``SWIPE_LEFT_SIGN`` từ các lần vuốt trái đã đo.

Quy trình (cẩm nang 4.3): với mỗi lần vuốt, lấy ``x`` của cổ tay ở frame có tay
CUỐI trừ ``x`` ở frame có tay ĐẦU, trên ảnh KHÔNG lật. Dấu của trung vị các
``dx`` là ``SWIPE_LEFT_SIGN``.

``dx`` ở đây tính theo toạ độ chuẩn hoá (tỉ lệ chiều rộng khung). Nhân với
chiều rộng ``w > 0`` để ra pixel không đổi dấu, nên kết luận về dấu là như nhau.

Chỉ kết luận khi kết quả DỨT KHOÁT: đủ số lần hợp lệ và mọi lần hợp lệ cùng dấu.
Một lần vuốt trái cho dấu ngược là tín hiệu phải đo lại, không phải nhiễu để
bỏ qua.
"""

import math

import numpy as np

from src import config


def rep_dx(wrist_x, min_frames=config.SWIPE_MEASURE_MIN_FRAMES):
    """``dx`` của một lần vuốt từ chuỗi ``x`` cổ tay (NaN ở frame mất tay).

    Returns:
        ``(dx, n_present)``; ``dx`` là NaN nếu có ít hơn ``min_frames`` frame
        thấy tay.
    """
    wrist_x = np.asarray(wrist_x, dtype=np.float64)
    seen = np.flatnonzero(np.isfinite(wrist_x))
    if seen.size < min_frames:
        return float("nan"), int(seen.size)
    return float(wrist_x[seen[-1]] - wrist_x[seen[0]]), int(seen.size)


def decide_sign(dxs, min_dx=config.SWIPE_MEASURE_MIN_DX,
                min_valid_frac=config.SWIPE_MEASURE_MIN_VALID_FRAC):
    """Kết luận dấu từ ``dx`` của các lần vuốt trái.

    Một lần là hợp lệ khi ``dx`` hữu hạn và ``|dx| >= min_dx``.

    Returns:
        dict với ``sign`` (``1``, ``-1`` hoặc ``None`` khi không dứt khoát),
        ``median_dx``, ``n_reps``, ``n_valid``, ``n_agree`` và ``reason``.
    """
    dxs = np.asarray(dxs, dtype=np.float64)
    n_reps = int(dxs.size)
    valid = np.isfinite(dxs) & (np.abs(dxs) >= min_dx)
    n_valid = int(valid.sum())
    n_needed = math.ceil(min_valid_frac * n_reps)

    result = {"sign": None, "median_dx": float("nan"), "n_reps": n_reps,
              "n_valid": n_valid, "n_agree": 0, "reason": ""}

    if n_valid == 0 or n_valid < n_needed:
        result["reason"] = (f"chỉ {n_valid}/{n_reps} lần hợp lệ, cần ít nhất "
                            f"{n_needed}")
        return result

    median_dx = float(np.median(dxs[valid]))
    sign = 1 if median_dx > 0 else -1
    n_agree = int((np.sign(dxs[valid]) == sign).sum())
    result.update(median_dx=median_dx, n_agree=n_agree)

    if n_agree < n_valid:
        result["reason"] = (f"{n_valid - n_agree}/{n_valid} lần hợp lệ cho dấu "
                            "ngược với trung vị")
        return result

    result["sign"] = sign
    result["reason"] = f"cả {n_valid} lần hợp lệ cùng dấu"
    return result
