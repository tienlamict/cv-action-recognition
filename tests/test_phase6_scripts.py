"""Kiểm thử script Phase 6 — không đụng data/ hay results/."""

import numpy as np
import pytest

from src import config
from src.live import Prediction, PredictionLog, count_clusters, read_prediction_log
from tests.scripts_import import load_script

summarize = load_script("summarize_log")
sweep = load_script("sweep_rigid")
train_rf = load_script("train_rf")


def test_gom_cum_du_doan_lien_tiep_cung_nhan():
    names = ["-", "none", "swipe_left", "swipe_left", "none", "swipe_left",
             "zoom_in", "-", "zoom_in", "zoom_in"]
    assert count_clusters(names) == {"swipe_left": 2, "swipe_right": 0,
                                     "zoom_in": 2, "zoom_out": 0}


def test_tom_tat_log_dem_cum_moi_phut(tmp_path):
    """Log 2 phút, 3 cụm khác none → 1,5 cụm mỗi phút."""
    path = tmp_path / "log.csv"
    labels = [0] * 300 + [1] * 5 + [0] * 100 + [3] * 3 + [None] * 2 + [3] * 2 + [0] * 189
    feats = np.zeros(15, dtype=np.float32)
    with PredictionLog(path) as log:
        for i, label in enumerate(labels):
            log.write(Prediction(i * config.STRIDE_SEC, label,
                                 None if label is None else 0.9, 1.0, feats))
    ts, names = read_prediction_log(path)
    rows, totals = summarize.summarize_log(ts, names)

    assert totals["n_predictions"] == len(labels)
    assert totals["n_valid"] == len(labels) - 2
    assert totals["clusters"] == 3
    assert totals["minutes"] == pytest.approx((len(labels) - 1) * config.STRIDE_SEC / 60)
    assert totals["per_minute"] == pytest.approx(3 / totals["minutes"])
    assert {r["label"]: r["clusters"] for r in rows}["zoom_in"] == 2


def test_bang_do_quan_trong_xep_hang_va_danh_dau_du_doan():
    impurity = np.linspace(0.15, 0.01, 15)
    perm = np.zeros(15)
    perm[[5, 7, 9]] = [0.3, 0.2, 0.1]       # pinch_delta, dx, max_vx
    rows = train_rf.importance_rows(impurity, perm, np.zeros(15))

    assert [r["feature"] for r in rows[:3]] == ["pinch_delta", "dx", "max_vx"]
    assert all(r["predicted_important"] for r in rows[:3])
    assert sorted(r["impurity_rank"] for r in rows) == list(range(1, 16))
    checks = train_rf.gate(0.6, 0.3, rows)
    assert all(ok for _, ok, _ in checks)
    assert not train_rf.gate(0.98, 0.3, rows)[1][1], "trên 0,97 là dấu hiệu rò rỉ"
    assert not train_rf.gate(0.3, 0.3, rows)[0][1], "không hơn luật là không đạt"


def test_phat_hien_ro_ri_giua_train_va_val():
    subject = np.array(["a", "a", "b", "c"])
    clip = np.array(["a1", "a2", "b1", "c1"])
    split = np.array(["train", "train", "val", "val"])
    assert train_rf.leakage_report(subject, clip, split) == ([], [])
    split = np.array(["train", "val", "val", "val"])
    people, _ = train_rf.leakage_report(subject, clip, split)
    assert people == ["a"]


def test_xao_theo_nhom_lo_ra_do_quan_trong_bi_cot_tuong_quan_giau_di():
    """Hai cột giống hệt nhau cùng mang thông tin: xáo riêng một cột thì có
    cột vẫn không làm mô hình giảm gì, xáo cả nhóm thì mô hình sập."""
    from sklearn.ensemble import RandomForestClassifier
    from src.features import FEATURE_NAMES

    rng = np.random.default_rng(0)
    F = rng.normal(size=(400, len(FEATURE_NAMES)))
    dx, mean_vx = FEATURE_NAMES.index("dx"), FEATURE_NAMES.index("mean_vx")
    F[:, mean_vx] = F[:, dx]
    # đủ 5 lớp theo ngũ phân vị của dx — macro-F1 tính trên cả 5 lớp
    y = np.digitize(F[:, dx], np.quantile(F[:, dx], [0.2, 0.4, 0.6, 0.8]))
    model = RandomForestClassifier(n_estimators=50, random_state=0).fit(F, y)

    rows = {r["group"]: r for r in train_rf.grouped_permutation(
        model, F, y, [("dx",), ("mean_vx",), ("dx", "mean_vx")], repeats=3)}
    assert rows["(không xáo)"]["drop_mean"] == 0.0
    both = rows["dx + mean_vx"]["drop_mean"]
    assert max(rows["dx"]["drop_mean"], rows["mean_vx"]["drop_mean"]) < both / 2
    assert both > 0.3


def test_ho_so_dac_trung_tung_o_cua_ma_tran_nham_lan():
    from src.features import FEATURE_NAMES

    F = np.zeros((25, len(FEATURE_NAMES)))
    F[:, FEATURE_NAMES.index("dx")] = np.r_[-np.ones(12), np.ones(13)]
    F[:, FEATURE_NAMES.index("max_vx")] = np.arange(25)
    y_true = np.array([1] * 12 + [0] * 13)
    y_pred = np.array([1] * 12 + [1] * 10 + [0] * 3)
    src = np.array(["G05"] * 12 + ["B0B"] * 13)

    rows = train_rf.profile_rows(F, y_true, y_pred, src, min_n=10)
    cells = {(r["true"], r["src_label"], r["predicted"]): r for r in rows}
    assert set(cells) == {("swipe_left", "G05", "swipe_left"),
                          ("none", "B0B", "swipe_left")}, "ô dưới min_n bị bỏ"
    assert cells[("swipe_left", "G05", "swipe_left")]["dx"] == 1.0, "dx lấy trị tuyệt đối"
    assert cells[("none", "B0B", "swipe_left")]["max_vx"] == np.median(np.arange(12, 22))


def test_quet_ban_tay_cung_chay_muc_0_mot_lan():
    """Mức 0 không có bản nào nên không phụ thuộc khoảng k: chỉ huấn luyện một lần."""
    variants = sweep.variants(shares=(0.0, 0.5), keeps=((0.0, 0.0), (0.0, 1.0)))
    assert variants == [(0.0, (0.0, 0.0)), (0.5, (0.0, 0.0)), (0.5, (0.0, 1.0))]


def test_hang_quet_tinh_ca_loi_lan_gia():
    y = np.array([0, 0, 0, 0, 1, 1, 2, 2, 3, 4])
    pred = np.array([1, 0, 0, 0, 1, 0, 2, 2, 3, 4])
    src = np.array(["B0A", "B0A", "D0X", "D0X"] + ["G"] * 6)
    clip = np.array([f"c{i}" for i in range(10)])     # mỗi cửa sổ một cử chỉ
    hits = {"shape_0": np.array([True, False, True, True])}
    row = sweep.variant_row(0.5, (0.0, 1.0), 4, y, pred, src, clip, np.zeros(10), hits)

    assert row["keep"] == "0–1" and row["n_rigid"] == 4
    assert row["swipe_recall"] == 0.75 and row["shape_0"] == 0.75
    assert row["swipe_events"] == 0.75, "trái 1/2 cú, phải 2/2 cú"
    assert row["none_alarm"] == 0.25 and row["pointing_alarm"] == 0.5
    assert row["alarm_per_min"] == pytest.approx(1 / (4 * config.STRIDE_SEC / 60))
    assert sweep.variant_row(0.0, (0.0, 0.0), 0, y, pred, src, clip, np.zeros(10),
                             hits)["keep"] == ""


def test_bang_do_doi_dang_chi_lay_none_chuyen_dong_nhu_vuot():
    from src.features import FEATURE_NAMES

    F = np.zeros((4, len(FEATURE_NAMES)))
    F[:, FEATURE_NAMES.index("max_vx")] = [9.0, 1.0, 9.0, 9.0]
    F[:, FEATURE_NAMES.index("dx")] = 1.0
    F[:, FEATURE_NAMES.index("open_range")] = [0.1, 0.2, 0.3, 0.9]
    y = np.array([0, 0, 0, 1])
    src = np.array(["B0A", "B0A", "D0X", "G05"])
    probe_F = {"shape_0": np.vstack([np.full(len(FEATURE_NAMES), np.nan), F[3]])}

    rows = {r["group"]: r for r in sweep.shape_rows(F, y, src, probe_F)}
    assert rows["none B0A, chuyển động như vuốt"]["n"] == 1, "cửa sổ chậm bị loại"
    assert rows["vuốt thật, shape_0"]["n"] == 1, "cửa sổ không chuẩn hoá được bị loại"
    assert rows["vuốt thật"]["open_p50"] == pytest.approx(0.9)
