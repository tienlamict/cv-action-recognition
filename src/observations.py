"""Chỉ số của các thí nghiệm quan sát (cẩm nang bước 6) trên một CSV điểm mốc.

Mỗi thí nghiệm phải cho ra CON SỐ, không phải nhận xét bằng mắt.

Về độ rung và ``sigma``:

- ``*_std_px``: độ lệch chuẩn của từng toạ độ theo thời gian, đơn vị pixel,
  gộp bằng căn trung bình bình phương (RMS) qua các toạ độ. Đây là định nghĩa
  của cẩm nang 6.9. Chỉ có nghĩa là "độ rung" khi tay ĐỨNG YÊN (thí nghiệm 1
  và 9); với tay đang chuyển động, nó đo chính chuyển động.
- ``*_diff_px``: ước lượng từ chênh lệch giữa hai frame liên tiếp,
  ``std(diff) / sqrt(2)``. Không nhạy với trôi chậm của cả bàn tay, nên dùng
  để đối chiếu.
- ``sigma_std_palm``: ``sigma_std_px`` chia cho cỡ lòng bàn tay — khoảng cách
  cổ tay → gốc ngón giữa (điểm 0 → 9), đúng đơn vị của ``normalize_window``.

Đổi toạ độ chuẩn hoá sang pixel ở đây chỉ phục vụ đo đạc. Đường ống xử lý
chính dùng ``to_pixels`` của Phase 2.
"""

import math

import numpy as np

from src import config


def _longest_true_run(mask):
    """``(độ dài, chỉ số bắt đầu)`` của dãy ``True`` liên tiếp dài nhất."""
    best_len, best_start, run_start = 0, -1, None
    for i, value in enumerate(np.append(mask, False)):
        if value and run_start is None:
            run_start = i
        elif not value and run_start is not None:
            if i - run_start > best_len:
                best_len, best_start = i - run_start, run_start
            run_start = None
    return best_len, best_start


def _rms(values):
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    return float(np.sqrt(np.mean(values ** 2))) if values.size else float("nan")


def _std_per_coordinate(points):
    """``points`` ``(N, K, 2)`` pixel → độ lệch chuẩn của từng toạ độ ``(K, 2)``."""
    if points.shape[0] < 2:
        return np.full(points.shape[1:], np.nan)
    return np.std(points, axis=0, ddof=1)


def _diff_sigma_per_coordinate(points, consecutive):
    """``std(diff) / sqrt(2)`` trên các cặp frame liên tiếp đều thấy tay."""
    if consecutive.sum() < 2:
        return np.full(points.shape[1:], np.nan)
    diffs = (points[1:] - points[:-1])[consecutive]
    return np.std(diffs, axis=0, ddof=1) / math.sqrt(2)


def run_metrics(data):
    """Tính mọi chỉ số của một lần ghi.

    Args:
        data: dict trả về bởi ``recording.read_frames_csv``.

    Returns:
        dict các chỉ số, NaN ở những chỉ số không tính được.
    """
    ts, present = data["ts"], data["present"]
    n_frames = int(ts.size)
    duration = float(ts[-1] - ts[0]) if n_frames > 1 else 0.0

    absent = ~present
    gap_len, gap_start = _longest_true_run(absent)
    gap_sec = (float(ts[gap_start + gap_len - 1] - ts[gap_start])
               if gap_len > 0 else 0.0)

    metrics = {
        "n_frames": n_frames,
        "duration_sec": duration,
        "fps": (n_frames - 1) / duration if duration > 0 else float("nan"),
        "detection_rate": float(present.mean()) if n_frames else float("nan"),
        "n_losses": int(np.sum(present[:-1] & absent[1:])),
        "longest_gap_frames": int(gap_len),
        "longest_gap_sec": gap_sec,
        "mean_score": (float(np.nanmean(data["score"][present]))
                       if present.any() else float("nan")),
    }

    handed = data["handedness"][present]
    for label in ("Left", "Right"):
        metrics[f"frac_{label.lower()}"] = (
            float(np.mean(handed == label)) if handed.size else float("nan")
        )

    size = np.stack([data["w"], data["h"]], axis=1)[:, None, :]
    points_px = (data["xy"].astype(np.float64) * size)[present]
    # Cặp (j, j+1) trong các frame thấy tay có liền nhau trên trục thời gian
    # gốc không — một lần mất tay ở giữa thì không được tính là "rung".
    consecutive = np.diff(np.flatnonzero(present)) == 1

    std_all = _std_per_coordinate(points_px)
    diff_all = _diff_sigma_per_coordinate(points_px, consecutive)
    tip = config.INDEX_TIP
    palm = (np.linalg.norm(points_px[:, config.MIDDLE_MCP]
                           - points_px[:, config.WRIST], axis=1)
            if points_px.shape[0] else np.array([]))
    palm_px = float(np.median(palm)) if palm.size else float("nan")

    metrics.update({
        "jitter_index_std_px": _rms(std_all[tip]),
        "jitter_index_diff_px": _rms(diff_all[tip]),
        "sigma_std_px": _rms(std_all),
        "sigma_diff_px": _rms(diff_all),
        "palm_px": palm_px,
        "sigma_std_palm": (_rms(std_all) / palm_px
                           if palm_px and np.isfinite(palm_px)
                           else float("nan")),
    })
    return metrics


def aggregate(rows, key, metric_names):
    """Gộp các lần chạy cùng ``key``: trung bình và độ lệch chuẩn từng chỉ số."""
    groups = {}
    for row in rows:
        groups.setdefault(row[key], []).append(row)

    summary = []
    for name, group in groups.items():
        out = {key: name, "n_runs": len(group)}
        for metric in metric_names:
            values = np.array([r[metric] for r in group], dtype=np.float64)
            values = values[np.isfinite(values)]
            out[f"{metric}_mean"] = (float(values.mean()) if values.size
                                     else float("nan"))
            out[f"{metric}_std"] = (float(values.std(ddof=1))
                                    if values.size > 1 else float("nan"))
        summary.append(out)
    return summary
