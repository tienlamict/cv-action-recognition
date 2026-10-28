"""Chạy lại toàn bộ đường ống bằng một lệnh (Phase 12): điểm mốc → cửa sổ → ba
mô hình (luật, rừng, LSTM) → bảng kết quả.

- **Bỏ qua bước đã xong.** Bước nào đã có đầu ra thì không chạy lại. Đổi config
  hay mô hình mà muốn bảng đi theo thì chạy lại đúng bước đó bằng --force.
- **Thứ tự** đúng như bảng "Thứ tự chạy script" của README; mỗi bước gọi đúng
  script mà README ghi, nên không có bản "gần giống" nào của đường ống.
- **Hằng số đã đo** (SWIPE_LEFT_SIGN, AUG_NOISE_SIGMA, ba ngưỡng luật) nằm sẵn
  trong config.py. Các bước đo chỉ chạy lại để so; script không tự sửa
  config.py.
- **LSTM của demo** (LSTM_MODEL_PATH) là một lần khảo sát của train_lstm.py với
  DEPLOY_ZOOM_STYLE_P và DEPLOY_STATIC_SHARE, chép sang LSTM_MODEL_PATH.
  - Đã có lần khảo sát đúng công thức đó, trên đúng bộ cửa sổ hiện tại, thì
    chép luôn, không học lại.
  - Không dùng số thứ tự run_NN: dựng lại từ đầu thì số đó đổi.

Không nằm ở đây:

- việc cần webcam hay con người: demo, quay phiên (bench.py record), đo tốc độ
  (bench.py speed), thí nghiệm quan sát của Phase 1;
- các phép thăm dò và khảo sát phụ của Phase 6–7 (probe_*, sweep_rigid, các
  lần khảo sát khác của train_lstm.py);
- **lần chạy cuối trên tập test.** `evaluate.py --split test --final` chạy đúng
  một lần, do người dùng tự chạy khi mọi cấu hình đã chốt (SPEC, luật 13).

Ví dụ:
    python scripts/run_all.py --list        # các bước, bước nào đã xong
    python scripts/run_all.py               # chạy mọi bước chưa xong
    python scripts/run_all.py --force evaluate experiments
    python scripts/run_all.py --only lstm_deployed
"""

import json
import os
import shutil
import subprocess
import sys
import time
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402

PYTHON = (3, 10)        # README: conda env action-recognition, Python 3.10

Step = namedtuple("Step", "name phase what run done")
Step.__doc__ = """Một bước của đường ống.

- ``run``: list lệnh (mỗi lệnh một list đối số) hoặc một hàm không đối số;
- ``done``: hàm trả về ``(xong?, ghi chú)`` — xong khi đầu ra đã có."""


def script(name, *args):
    """Lệnh gọi ``scripts/<name>.py`` bằng đúng trình thông dịch đang chạy."""
    return [sys.executable, str(config.SCRIPTS_DIR / f"{name}.py"), *map(str, args)]


def exists(*paths):
    """``done`` của bước mà đầu ra là các file cố định."""
    def check():
        missing = [p for p in paths if not Path(p).exists()]
        return (not missing,
                "thiếu " + ", ".join(relative_to_root(p) for p in missing) if missing
                else ", ".join(relative_to_root(p) for p in paths))
    return check


def has_runs(directory):
    """``done`` của bước mà đầu ra là các thư mục ``run_NN``."""
    def check():
        runs = sorted(Path(directory).glob("run_*/manifest.json"))
        return bool(runs), (f"{relative_to_root(directory)}: {len(runs)} lần chạy" if runs
                            else f"chưa có {relative_to_root(directory)}/run_NN")
    return check


def landmarks_done():
    """Mọi video IPN đã có ``.npz``. Không có video (chỉ mang điểm mốc theo) thì
    điểm mốc sẵn có là đủ."""
    have = {p.stem for p in (config.LANDMARKS_DIR / "ipn").glob("*.npz")}
    videos = {p.stem for p in config.IPN_VIDEO_DIR.glob(f"*{config.IPN_VIDEO_SUFFIX}")}
    if not videos:
        return bool(have), (f"{len(have)} clip, không có video IPN để so" if have
                            else "không có video IPN lẫn điểm mốc — tải IPN Hand trước (README)")
    missing = videos - have
    return not missing, f"{len(videos) - len(missing)}/{len(videos)} video đã có điểm mốc"


def ranges_done():
    """``ipn_feature_ranges.json`` có, và có đủ độ duỗi ngón mà màn hình luyện
    tập cần (``live.load_feature_ranges`` từ chối file cũ)."""
    from src.live import load_feature_ranges
    try:
        load_feature_ranges()
    except (FileNotFoundError, ValueError) as error:
        return False, str(error)
    return True, relative_to_root(config.IPN_FEATURE_RANGES_JSON)


def comparison_done():
    """Bảng so sánh có hàng val của mọi mô hình, chấm qua ``EVENT_FILTER``."""
    import csv
    path = Path(config.MODEL_COMPARISON).with_suffix(".csv")
    rows = []
    if path.is_file():
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    ok = {r["model"] for r in rows
          if r["split"] == "val" and r.get("event_filter") == config.EVENT_FILTER}
    missing = [m for m in config.MODEL_NAMES if m not in ok]
    return not missing, (f"thiếu hàng {', '.join(missing)} ('{config.EVENT_FILTER}')" if missing
                         else f"{relative_to_root(path)}: {len(ok)} mô hình")


def deploy_recipe():
    """Độ lệch so với config mà ``train_lstm.py`` ghi vào manifest của lần khảo
    sát dựng LSTM của demo."""
    return {"zoom_style_p": config.DEPLOY_ZOOM_STYLE_P,
            "static_share": config.DEPLOY_STATIC_SHARE}


def deploy_candidates(train_dir=None):
    """Checkpoint của các lần khảo sát đúng công thức LSTM của demo, học trên
    ĐÚNG bộ cửa sổ hiện tại — mới nhất trước."""
    from src.forest import file_sha256
    from src.models import load_checkpoint

    train_dir = Path(train_dir or config.PHASE7_RESULTS_DIR / "train_lstm")
    windows_sha = file_sha256(config.WINDOWS_NPZ)
    runs = [p for p in train_dir.glob("run_*") if p.name[4:].isdigit()]
    out = []
    for run in sorted(runs, key=lambda p: int(p.name[4:]), reverse=True):
        manifest, checkpoint = run / "manifest.json", run / config.PHASE7_LSTM_PATH.name
        if not (manifest.is_file() and checkpoint.is_file()):
            continue
        if json.loads(manifest.read_text(encoding="utf-8")).get("survey") != deploy_recipe():
            continue
        if load_checkpoint(checkpoint)[1].get("windows_sha256") == windows_sha:
            out.append(checkpoint)
    return out


def deploy_lstm(train=None):
    """Dựng LSTM_MODEL_PATH: chép checkpoint của lần khảo sát đúng công thức; chưa
    có thì học (``train_lstm.py`` với hai phép tăng cường DEPLOY_) rồi chép.

    Args:
        train: hàm chạy một lệnh — mặc định :func:`run_command`.

    Returns:
        đường dẫn checkpoint nguồn.
    """
    from src.forest import file_sha256

    found = deploy_candidates()
    if not found:
        recipe = deploy_recipe()
        (train or run_command)(script("train_lstm", "--zoom-style-p", recipe["zoom_style_p"],
                                      "--static-share", recipe["static_share"]))
        found = deploy_candidates()
    if not found:
        raise SystemExit(f"train_lstm.py chạy xong mà không thấy lần khảo sát {deploy_recipe()} "
                         "— công thức DEPLOY_ có trùng tham số mặc định AUG_ không?")
    source, target = found[0], Path(config.LSTM_MODEL_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if file_sha256(source) != file_sha256(target):
        raise SystemExit(f"Chép {relative_to_root(source)} sang {relative_to_root(target)} "
                         "không trùng từng byte.")
    print(f"LSTM của demo: {relative_to_root(source)} → {relative_to_root(target)}")
    return source


def steps():
    """Các bước, theo thứ tự README."""
    return [
        Step("landmarks", 3, "điểm mốc mọi video IPN (cả đêm nếu làm từ đầu)",
             [script("extract_landmarks", "--source", "ipn")], landmarks_done),
        Step("direction", 3, "đo SWIPE_LEFT_SIGN", [script("measure_direction")],
             exists(config.PHASE3_RESULTS_DIR / "direction.md")),
        Step("dataset_stats", 3, "thống kê bộ dữ liệu", [script("dataset_stats")],
             has_runs(config.PHASE3_RESULTS_DIR / "dataset_stats")),
        Step("splits", 4, "splits.json theo người — make_splits.py ghi đè, nên có rồi thì "
             "không bao giờ chạy lại", [script("make_splits")], exists(config.SPLITS_JSON)),
        Step("windows", 4, "windows.npz", [script("build_dataset")], exists(config.WINDOWS_NPZ)),
        # đúng lệnh đã đo AUG_NOISE_SIGMA trong config.py (README, bảng hằng số)
        Step("sigma", 4, "đo AUG_NOISE_SIGMA", [script("estimate_sigma", "--src-label", "D0X")],
             has_runs(config.PHASE4_RESULTS_DIR / "sigma")),
        Step("boxplots", 4, "boxplot và ipn_feature_ranges.json", [script("plot_feature_boxplots")],
             ranges_done),
        Step("thresholds", 5, "đo ba ngưỡng luật", [script("calibrate_rules")],
             exists(config.PHASE5_RESULTS_DIR / "thresholds.md")),
        Step("eval_rules", 5, "luật trên val", [script("eval_rules")],
             has_runs(config.PHASE5_RESULTS_DIR / "eval_rules")),
        Step("rf", 6, "rừng ngẫu nhiên", [script("train_rf")], exists(config.RF_MODEL_PATH)),
        Step("lstm", 7, "LSTM chính (PHASE7_LSTM_PATH)", [script("train_lstm")],
             exists(config.PHASE7_LSTM_PATH)),
        Step("lstm_deployed", 10, "LSTM của demo (LSTM_MODEL_PATH)", deploy_lstm,
             exists(config.LSTM_MODEL_PATH)),
        Step("evaluate", 10, "bốn mô hình trên val, qua máy trạng thái → model_comparison",
             [script("evaluate", "--model", m, "--split", "val", "--events", config.EVENT_FILTER)
              for m in config.MODEL_NAMES], comparison_done),
        Step("experiments", 8, "bảy bảng khảo sát (170 phút nếu học từ đầu)",
             [script("run_experiments")], has_runs(config.PHASE8_RESULTS_DIR / "experiments")),
        Step("sweep_activation", 9, "đánh đổi của máy trạng thái", [script("sweep_activation")],
             has_runs(config.PHASE9_RESULTS_DIR / "sweep_activation")),
        Step("bench_analyze", 10, "bảng đánh đổi trên phiên webcam đã ghi và video val",
             [script("bench", "analyze")], has_runs(config.PHASE10_RESULTS_DIR / "analyze")),
    ]


def run_command(command):
    """Chạy một lệnh, hiện thẳng đầu ra; lỗi thì dừng cả đường ống."""
    print("$ " + " ".join(command[1:]), flush=True)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    code = subprocess.run(command, cwd=config.ROOT, env=env).returncode
    if code != 0:
        raise SystemExit(code)


def main():
    setup_console()
    parser = make_parser(__doc__)
    all_steps = steps()
    names = [s.name for s in all_steps]
    parser.add_argument("--list", action="store_true", help="liệt kê các bước và trạng thái")
    parser.add_argument("--force", nargs="+", default=[], choices=names, metavar="BƯỚC",
                        help="chạy lại các bước này dù đã có đầu ra")
    parser.add_argument("--only", nargs="+", default=None, choices=names, metavar="BƯỚC",
                        help="chỉ xét các bước này")
    args = parser.parse_args()

    if sys.version_info[:2] != PYTHON:
        print(f"Cảnh báo: đang chạy Python {sys.version.split()[0]}; README dựng mọi con số "
              f"bằng Python {PYTHON[0]}.{PYTHON[1]} (conda env action-recognition).")
    chosen = [s for s in all_steps if args.only is None or s.name in args.only]
    if args.list:
        for s in chosen:
            done, note = s.done()
            print(f"  [{'xong' if done else 'chưa'}] {s.phase:>2}  {s.name:<17}{s.what} — {note}")
        return

    started, report = time.perf_counter(), []
    for s in chosen:
        done, note = s.done()
        if done and s.name not in args.force:
            print(f"[{s.name}] bỏ qua — {note}")
            report.append({"step": s.name, "status": "bỏ qua", "note": note})
            continue
        print(f"\n[{s.name}] Phase {s.phase}: {s.what}", flush=True)
        step_started = time.perf_counter()
        try:
            if callable(s.run):
                s.run()
            else:
                for command in s.run:
                    run_command(command)
        except SystemExit as error:
            report.append({"step": s.name, "status": "lỗi", "code": str(error.code)})
            write_report(report, started)
            print(f"\nDừng ở bước {s.name}. Sửa lỗi rồi chạy lại: các bước trước đã xong "
                  "sẽ được bỏ qua.")
            raise
        report.append({"step": s.name, "status": "đã chạy",
                       "seconds": round(time.perf_counter() - step_started, 1)})
    run_dir = write_report(report, started)
    print(f"\nXong sau {(time.perf_counter() - started) / 60:.1f} phút: "
          f"{sum(r['status'] == 'đã chạy' for r in report)} bước chạy, "
          f"{sum(r['status'] == 'bỏ qua' for r in report)} bỏ qua. "
          f"Manifest: {relative_to_root(run_dir)}")
    print("Lần chạy cuối trên tập test KHÔNG nằm trong run_all.py: khi mọi cấu hình đã chốt, "
          "chạy đúng một lần python scripts/evaluate.py --model <mô hình> --split test --final.")


def write_report(report, started):
    run_dir = next_run_dir(config.RUN_ALL_RESULTS_DIR)
    write_manifest(run_dir, {"script": "run_all", "steps": report,
                             "seconds": time.perf_counter() - started})
    return run_dir


if __name__ == "__main__":
    main()
