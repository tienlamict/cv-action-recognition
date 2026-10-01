"""ĐO quy ước hướng trên chính dữ liệu IPN — không đoán.

Với mỗi đoạn thuộc bốn lớp đích: load_clip → load_sequence trên đoạn →
normalize_window trên cả đoạn → window_features. Rồi kiểm hai điều PHẢI đúng:

- trung vị dx của swipe_left và swipe_right TRÁI DẤU nhau;
- trung vị open_delta của zoom_in DƯƠNG, của zoom_out ÂM.

Nếu một trong hai không đạt thì bảng ánh xạ nhãn sai (rất có thể zoom_in và
zoom_out bị đổi chỗ), và script KHÔNG đề xuất giá trị nào.

Script không tự sửa config.py — nó in ra đúng dòng để bạn dán.

Ví dụ:
    python scripts/measure_direction.py
    python scripts/measure_direction.py --include-mismatched
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.features import FEATURE_NAMES, window_features  # noqa: E402
from src.io_data import load_clip  # noqa: E402
from src.preprocess import load_sequence, normalize_window  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402

TARGETS = ["swipe_left", "swipe_right", "zoom_in", "zoom_out"]


def segment_features(ts, xy_norm, w, h, start, end):
    """Đặc trưng của một đoạn, hoặc ``None`` nếu đoạn không dùng được.

    Loại đoạn thiếu dữ liệu ở hai đầu: ``window_features`` trả về 0 cho đặc
    trưng không tính được, và số 0 đó sẽ lọt vào trung vị và làm hỏng phép đo
    dấu. Đây là phép ĐO quy ước, nên thà bỏ đoạn còn hơn đo bừa.
    """
    _, win = load_sequence(ts[start:end], xy_norm[start:end], w, h)
    k = config.FEATURE_EDGE_STEPS
    if win.shape[0] < 2 * k:
        return None
    finite = np.all(np.isfinite(win.reshape(win.shape[0], -1)), axis=1)
    if (finite.mean() < config.MIN_PRESENCE
            or not finite[:k].any() or not finite[-k:].any()):
        return None
    win_norm = normalize_window(win)        # ném ValueError nếu bước đầu mất tay
    return dict(zip(FEATURE_NAMES,
                    window_features(win_norm, float(finite.mean()))))


def collect(clip_paths, include_mismatched):
    """Quét mọi clip, gom dx và open_delta theo lớp."""
    values = {name: {"dx": [], "open_delta": []} for name in TARGETS}
    skipped = {name: 0 for name in TARGETS}
    n_clips = n_mismatched = 0

    for path in clip_paths:
        ts, xy_norm, w, h, segments, _, meta = load_clip(path)
        if meta.get("length_mismatch"):
            n_mismatched += 1
            if not include_mismatched:
                continue
        n_clips += 1

        for start, end, class_id in segments:
            name = config.CLASSES[class_id]
            if name not in values:
                continue
            try:
                feats = segment_features(ts, xy_norm, w, h, start, end)
            except ValueError:
                feats = None                # bước đầu mất tay
            if feats is None:
                skipped[name] += 1
                continue
            values[name]["dx"].append(feats["dx"])
            values[name]["open_delta"].append(feats["open_delta"])

    return values, skipped, n_clips, n_mismatched


def summarize(values):
    """Trung vị và tỉ lệ đoạn cùng dấu với trung vị, theo từng lớp."""
    out = {}
    for name, series in values.items():
        row = {"n": len(series["dx"])}
        for key in ("dx", "open_delta"):
            data = series[key]
            if data:
                median = statistics.median(data)
                agree = sum(1 for v in data
                            if v != 0 and (v > 0) == (median > 0)) / len(data)
            else:
                median, agree = float("nan"), float("nan")
            row[f"median_{key}"] = float(median)
            row[f"agree_{key}"] = float(agree)
        out[name] = row
    return out


def check(summary):
    """Hai điều PHẢI đúng. Trả về ``(đạt, danh sách lý do không đạt)``."""
    problems = []
    left = summary["swipe_left"]["median_dx"]
    right = summary["swipe_right"]["median_dx"]
    if not (np.isfinite(left) and np.isfinite(right)):
        problems.append("không đủ đoạn hợp lệ cho hai lớp vuốt")
    elif min(abs(left), abs(right)) < config.FEATURE_EPS:
        problems.append(
            f"trung vị dx của một lớp vuốt gần như bằng 0 "
            f"(swipe_left {left:+.4f}, swipe_right {right:+.4f}) — không đủ "
            "đoạn hợp lệ để kết luận"
        )
    elif (left > 0) == (right > 0):
        problems.append(
            f"trung vị dx của swipe_left ({left:+.3f}) và swipe_right "
            f"({right:+.3f}) CÙNG DẤU — hai lớp vuốt không phân biệt được"
        )

    zin = summary["zoom_in"]["median_open_delta"]
    zout = summary["zoom_out"]["median_open_delta"]
    if not (np.isfinite(zin) and np.isfinite(zout)):
        problems.append("không đủ đoạn hợp lệ cho hai lớp zoom")
    else:
        if abs(zin) < config.FEATURE_EPS or abs(zout) < config.FEATURE_EPS:
            problems.append(
                f"trung vị open_delta gần như bằng 0 (zoom_in {zin:+.4f}, "
                f"zoom_out {zout:+.4f}) — không đủ đoạn hợp lệ để kết luận"
            )
        if zin <= 0:
            problems.append(
                f"trung vị open_delta của zoom_in là {zin:+.3f}, KHÔNG dương "
                "— nhiều khả năng G10/G11 bị đổi chỗ trong CLASS_MAP"
            )
        if zout >= 0:
            problems.append(
                f"trung vị open_delta của zoom_out là {zout:+.3f}, KHÔNG âm"
            )
    return not problems, problems


def render(summary, skipped, n_clips, n_mismatched, ok, problems, sign):
    """Bảng kết quả dạng markdown, dùng cho cả màn hình lẫn direction.md."""
    lines = [
        "# Đo quy ước hướng trên IPN",
        "",
        f"- Số clip đã dùng: {n_clips}",
        f"- Số clip bị bỏ vì `length_mismatch`: {n_mismatched} "
        "(xem docs/ipn_format.md mục 6)",
        "",
        "| Lớp | Số đoạn | Bỏ qua | Trung vị dx | Cùng dấu | "
        "Trung vị open_delta | Cùng dấu |",
        "|---|---|---|---|---|---|---|",
    ]
    for name in TARGETS:
        r = summary[name]
        lines.append(
            f"| {name} | {r['n']} | {skipped[name]} | {r['median_dx']:+.4f} | "
            f"{r['agree_dx']:.1%} | {r['median_open_delta']:+.4f} | "
            f"{r['agree_open_delta']:.1%} |"
        )

    lines += ["", "## Kết luận", ""]
    if ok:
        lines += [
            "Hai điều kiện bắt buộc đều đạt.",
            "",
            "```python",
            f"SWIPE_LEFT_SIGN = {sign}",
            "```",
            "",
            f"Dấu này là dấu của trung vị `dx` ở lớp `swipe_left` "
            f"({summary['swipe_left']['median_dx']:+.4f}), đo trên ảnh không "
            "lật của IPN.",
        ]
    else:
        lines += ["**KHÔNG ĐẠT — không đề xuất giá trị nào.**", ""]
        lines += [f"- {p}" for p in problems]
    return "\n".join(lines) + "\n"


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--landmarks", default=None,
                        help="thư mục .npz (mặc định data/landmarks/ipn)")
    parser.add_argument("--include-mismatched", action="store_true",
                        help="dùng cả clip có length_mismatch=True")
    args = parser.parse_args()

    landmarks_dir = Path(args.landmarks or config.LANDMARKS_DIR / "ipn")
    clip_paths = sorted(landmarks_dir.glob("*.npz"))
    if not clip_paths:
        raise SystemExit(
            f"Chưa có .npz nào trong {relative_to_root(landmarks_dir)}. "
            "Chạy scripts/extract_landmarks.py --source ipn trước."
        )

    values, skipped, n_clips, n_mismatched = collect(clip_paths,
                                                     args.include_mismatched)
    summary = summarize(values)
    ok, problems = check(summary)
    sign = (1 if summary["swipe_left"]["median_dx"] > 0 else -1) if ok else None

    report = render(summary, skipped, n_clips, n_mismatched, ok, problems, sign)
    print(report)

    run_dir = next_run_dir(config.PHASE3_RESULTS_DIR / "direction")
    (run_dir / "direction.md").write_text(report, encoding="utf-8")
    (config.PHASE3_RESULTS_DIR / "direction.md").write_text(report,
                                                            encoding="utf-8")
    write_manifest(run_dir, {"script": "measure_direction", "ok": ok,
                             "sign": sign, "n_clips": n_clips,
                             "summary": summary})

    if ok:
        print("Dán dòng sau vào src/config.py, thay cho SWIPE_LEFT_SIGN = None:\n")
        print(f"SWIPE_LEFT_SIGN = {sign}    # đo trên IPN bằng "
              f"measure_direction.py, {n_clips} clip")
    else:
        print("DỪNG: kiểm tra lại CLASS_MAP trong src/ipn.py và xem lại đoạn "
              "mẫu — xem docs/SPEC.md mục Cổng chất lượng.")
    print(f"\nBằng chứng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
