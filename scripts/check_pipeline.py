"""Chạy load_sequence trên một CSV thật và in các con số kiểm chứng đường ống.

Đây là cách trả lời bằng số cho câu hỏi "lưới thời gian có thật sự đều không,
và việc vá lỗ hổng lấy lại được bao nhiêu bước".

Ví dụ:
    python scripts/check_pipeline.py results/phase1/thu_nghiem/run_01/landmarks.csv
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.io_data import read_record_csv  # noqa: E402
from src.preprocess import load_sequence  # noqa: E402


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("csv", help="đường dẫn landmarks.csv")
    args = parser.parse_args()

    ts, xy_norm, present, w, h = read_record_csv(args.csv)
    grid_ts, xy = load_sequence(ts, xy_norm, w, h)

    # Cùng đường ống, chỉ khác là dừng trước bước vá lỗ hổng.
    _, xy_unfilled = load_sequence(ts, xy_norm, w, h, fill=False)
    missing_before = _missing_ratio(xy_unfilled)
    missing_after = _missing_ratio(xy)

    dt = np.diff(ts)
    grid_dt = np.diff(grid_ts)
    target = 1.0 / config.HZ

    print(f"Nguồn            : {args.csv}")
    print(f"Khung hình       : {w}x{h}")
    print(f"Số frame         : {ts.size}, thấy tay {present.mean():.1%}")
    print(f"Thời lượng       : {ts[-1] - ts[0]:.2f} s")
    if dt.size:
        print(f"FPS thực         : trung bình {1 / dt.mean():.2f}, "
              f"nhỏ nhất {1 / dt.max():.2f}, lớn nhất {1 / dt.min():.2f}")
        print(f"Giãn cách frame  : {dt.min() * 1000:.2f}–{dt.max() * 1000:.2f} ms "
              f"(chênh lệch {(dt.max() - dt.min()) * 1000:.2f} ms)")
    print(f"Số bước lưới     : {grid_ts.size} ở {config.HZ:g} Hz")
    if grid_dt.size:
        print(f"Lệch lưới lớn nhất: {np.abs(grid_dt - target).max():.3e} s "
              f"(so với {target:.6f} s)")
    print(f"Bước NaN trước vá : {missing_before:.1%}")
    print(f"Bước NaN sau vá   : {missing_after:.1%} "
          f"(vá được {missing_before - missing_after:.1%}, "
          f"MAX_GAP = {config.MAX_GAP} bước)")


def _missing_ratio(xy):
    """Tỉ lệ bước còn thiếu toạ độ."""
    if xy.shape[0] == 0:
        return float("nan")
    return float(np.mean(~np.all(np.isfinite(xy.reshape(xy.shape[0], -1)),
                                 axis=1)))


if __name__ == "__main__":
    main()
