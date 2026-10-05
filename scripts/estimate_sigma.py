"""Ước lượng AUG_NOISE_SIGMA trên tập train của IPN, khi Phase 1B chưa đo.

Lấy các cửa sổ none của tập train mà cổ tay gần như đứng yên — phân vị
SIGMA_STILL_QUANTILE thấp nhất của quãng dời cổ tay — rồi đo độ lệch chuẩn của
năm đầu ngón quanh vị trí trung bình của chúng, SAU chuẩn hoá (đơn vị lòng bàn
tay — đúng đơn vị mà src/augment.py cộng nhiễu). σ là trung vị trên các cửa sổ
đó.

Con số này là CẬN TRÊN của độ rung điểm mốc: cổ tay đứng yên không có nghĩa
ngón đứng yên. Trên IPN, đo ngày 2026-10-05, phần lớn cửa sổ "đứng yên" là động
tác bấm ngón và xòe tay (G01, G02, G07, G08, G09) — σ của chúng 0,07–0,11 lòng
bàn tay, so với 0,026 của tay nghỉ (D0X). --src-label D0X chỉ lấy tay nghỉ.

Script in dòng để dán vào config.py, KHÔNG tự sửa config.py.

Ví dụ:
    python scripts/estimate_sigma.py
    python scripts/estimate_sigma.py --src-label D0X
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits, split_of  # noqa: E402
from src.tables import write_table  # noqa: E402


def wrist_travel(X):
    """``(N,)`` quãng dời lớn nhất của cổ tay khỏi gốc (cổ tay frame đầu)."""
    wrist = X[:, :, config.WRIST]
    return np.nanmax(np.linalg.norm(wrist, axis=-1), axis=1)


def tip_jitter(X):
    """``(N,)`` độ lệch chuẩn của đầu ngón quanh vị trí trung bình, trung bình
    trên 5 đầu ngón và 2 trục."""
    tips = X[:, :, config.TIPS]
    return np.nanmean(np.nanstd(tips, axis=1), axis=(1, 2))


def estimate(X, quantile=config.SIGMA_STILL_QUANTILE):
    """σ từ những cửa sổ có cổ tay dời ít nhất.

    Returns:
        ``(sigma, still_mask, travel, jitter)``.
    """
    travel = wrist_travel(X)
    still = travel <= np.quantile(travel, quantile)
    jitter = tip_jitter(X)
    return float(np.median(jitter[still])), still, travel, jitter


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--windows", default=config.WINDOWS_NPZ)
    parser.add_argument("--src-label", nargs="+", default=None,
                        help="chỉ dùng cửa sổ none có nhãn gốc này, ví dụ D0X "
                             "(mặc định: mọi cửa sổ none, đúng chữ SPEC)")
    args = parser.parse_args()

    with np.load(args.windows, allow_pickle=False) as data:
        X, y, subject = data["X"], data["y"], data["subject"]
        src = data["src_label"]
    split = split_of(subject, read_splits())
    pick = (split == "train") & (y == 0)
    if args.src_label:
        pick &= np.isin(src, args.src_label)
    sigma, still, travel, jitter = estimate(X[pick].astype(np.float64))
    source = ", ".join(args.src_label) if args.src_label else "mọi nhãn gốc"

    rows = [{"quantity": f"cửa sổ none của train ({source})", "value": int(pick.sum())},
            {"quantity": f"cửa sổ đứng yên (phân vị {config.SIGMA_STILL_QUANTILE:.0%})",
             "value": int(still.sum())},
            {"quantity": "ngưỡng quãng dời cổ tay (lòng bàn tay)",
             "value": float(travel[still].max())},
            {"quantity": "σ đầu ngón — p25", "value": float(np.percentile(jitter[still], 25))},
            {"quantity": "σ đầu ngón — trung vị", "value": sigma},
            {"quantity": "σ đầu ngón — p75", "value": float(np.percentile(jitter[still], 75))}]
    run_dir = next_run_dir(config.PHASE4_RESULTS_DIR / "sigma")
    write_table(rows, ["quantity", "value"], run_dir / "sigma")
    write_manifest(run_dir, {"script": "estimate_sigma", "sigma": sigma,
                             "n_still": int(still.sum()),
                             "src_label": args.src_label})

    for r in rows:
        print(f"{r['quantity']:<45} {r['value']:.4g}")
    print("\nDán dòng sau vào src/config.py, thay cho AUG_NOISE_SIGMA = None:\n")
    print(f"AUG_NOISE_SIGMA = {sigma:.3g}    # lòng bàn tay; estimate_sigma.py, "
          f"{int(still.sum())} cửa sổ none ({source}) đứng yên của train")
    print(f"\nBằng chứng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
