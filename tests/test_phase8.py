"""Kiểm thử các bảng khảo sát của Phase 8 — dữ liệu tổng hợp, không đụng data/
hay results/ thật."""

import json

import numpy as np
import pytest
import torch

from src import config, evaluation, experiments, forest, models, training
from src.datasets import WindowDataset, window_sequence
from src.features import (ANGLE_NAMES, FEATURE_NAMES, angle_features, joint_angles,
                          openness, window_features)
from src.hybrid import hybrid_predict
from src.preprocess import normalize_window
from src.splits import proportional_quota, subject_folds
from src.variants import landmark_columns, per_frame_origin, select_landmarks
from src.windows import cut_windows
from tests.fixtures import (PALM_PX, SWIPE_PALMS, hand, labeled_windows, make_static,
                            make_swipe, make_zoom, save_parts_clip)


def test_goc_tung_frame_xoa_quy_dao_giu_dang_tay():
    """Bảng 2: gốc cổ tay từng frame — cổ tay ở gốc ở MỌI bước, mọi đặc trưng
    quỹ đạo về 0, dáng tay (độ xòe) giữ nguyên."""
    win = normalize_window(make_swipe(1))
    moved = per_frame_origin(win)
    np.testing.assert_allclose(moved[:, config.WRIST], 0.0, atol=1e-12)
    np.testing.assert_allclose(openness(moved), openness(win))
    before, after = window_features(win, 1.0), window_features(moved, 1.0)
    for name in ("dx", "max_vx", "mean_vx"):
        assert abs(before[FEATURE_NAMES.index(name)]) > 1.0
        assert after[FEATURE_NAMES.index(name)] == 0.0
    gap = win.copy()
    gap[5] = np.nan
    assert np.isnan(per_frame_origin(gap)[5]).all(), "bước mất tay vẫn là NaN"


def test_rut_gon_11_diem_giu_co_tay_goc_ngon_giua_va_dau_ngon():
    idx = config.REDUCED_LANDMARKS
    assert len(idx) == 11 and config.WRIST in idx and config.MIDDLE_MCP in idx
    assert set(config.TIPS) <= set(idx)
    win = normalize_window(make_zoom("in"))
    assert select_landmarks(win).shape == (config.T, 11, 2)
    np.testing.assert_array_equal(window_sequence(win)[:, landmark_columns()],
                                  select_landmarks(win).reshape(config.T, -1)
                                  .astype(np.float32))


def test_goc_khop_duoi_thang_la_pi_va_khong_bao_gio_nan():
    """Ngón duỗi thẳng: góc π; ngón gập: nhỏ hơn hẳn. Điểm trùng nhau hay bước
    mất tay không làm ra NaN (cẩm nang mục 9.c)."""
    win = normalize_window(np.stack([hand()] * config.T))      # không rung
    straight = joint_angles(win)
    assert straight.shape == (config.T, 5)
    np.testing.assert_allclose(straight, np.pi, atol=1e-6)   # bàn tay mẫu: ngón thẳng
    bent = win.copy()
    a, b, c = config.ANGLE_JOINTS["index"]
    bent[:, c] = bent[:, b] + (bent[:, b] - bent[:, a])[:, ::-1] * [1, -1]
    assert joint_angles(bent)[:, 1].max() < 0.6 * np.pi

    broken = win.copy()
    broken[:, 3] = broken[:, 2]                 # ngón cái: hai điểm trùng nhau
    broken[4:7] = np.nan                        # mất tay ba bước
    features = angle_features(broken)
    assert features.shape == (len(ANGLE_NAMES),) and np.all(np.isfinite(features))


def test_chia_ngau_nhien_theo_cua_so_giu_dung_so_cua_so_moi_lop():
    """Bảng 4 — phép chia rò rỉ: phân tầng theo lớp, đúng số cửa sổ val mỗi lớp,
    cùng seed cùng kết quả."""
    y = np.array([0] * 50 + [1] * 10 + [2] * 10)
    part = experiments.leaky_split(y, {0: 20, 1: 4, 2: 3}, np.random.default_rng(0))
    assert [int(np.sum((part == "val") & (y == c))) for c in (0, 1, 2)] == [20, 4, 3]
    again = experiments.leaky_split(y, {0: 20, 1: 4, 2: 3}, np.random.default_rng(0))
    np.testing.assert_array_equal(part, again)
    with pytest.raises(ValueError):
        experiments.leaky_split(y, {1: 11}, np.random.default_rng(0))


def test_k_fold_theo_nguoi_roi_nhau_va_du():
    people = [f"s{i}" for i in range(37)]
    folds = subject_folds(people, 5, seed=1)
    assert sorted(p for f in folds for p in f) == sorted(people)
    assert sum(len(f) for f in folds) == len(set(p for f in folds for p in f))
    assert max(map(len, folds)) - min(map(len, folds)) <= 1
    assert folds == subject_folds(list(reversed(people)), 5, seed=1)
    with pytest.raises(ValueError):
        subject_folds(people[:3], 5)


def test_khong_du_bang_chung_khi_chenh_lech_nho_hon_do_lech_chuan():
    assert experiments.verdict(0.01, 0.02) == "không đủ bằng chứng để kết luận"
    assert experiments.verdict(-0.05, 0.02) == "chênh lệch lớn hơn độ lệch chuẩn"
    assert "Bảng 6" in experiments.verdict(0.05, None)


def test_quota_theo_ty_le_tu_nhien():
    quota = proportional_quota({"B0A": 600, "B0B": 300, "G01": 100}, 100)
    assert quota == {"B0A": 60, "B0B": 30, "G01": 10}
    assert sum(proportional_quota({"a": 7, "b": 5, "c": 1}, 10).values()) == 10
    assert proportional_quota({"a": 2, "b": 3}, 100) == {"a": 2, "b": 3}


def zoom_clip_parts(seed=0):
    return [(make_static(30, seed=seed), "D0X", "none"),
            (make_zoom("in", 15), "G10", "zoom_in"),
            (make_static(30, seed=seed + 1), "D0X", "none")]


def test_cat_cua_so_theo_do_dai_va_bien_tuy_chon(tmp_path):
    """Bảng 3 và bảng phụ: độ dài cửa sổ và biên khoảnh khắc chính là tham số;
    mặc định vẫn là T và CORE_MARGIN_STEPS."""
    from src.io_data import load_clip

    path = save_parts_clip(tmp_path / "c.npz", zoom_clip_parts(), subject="p")
    ts, xy, w, h, seg, src, _ = load_clip(path)
    default, _ = cut_windows(ts, xy, w, h, seg, src)
    same, _ = cut_windows(ts, xy, w, h, seg, src, config.T, config.CORE_MARGIN_STEPS)
    np.testing.assert_array_equal(default["X"], same["X"])
    short, _ = cut_windows(ts, xy, w, h, seg, src, steps=12)
    assert short["X"].shape[1:] == (12, 21, 2)
    zoom = config.CLASSES.index("zoom_in")
    wide, _ = cut_windows(ts, xy, w, h, seg, src, margin=0)
    narrow, _ = cut_windows(ts, xy, w, h, seg, src, margin=6)
    counts = [int(np.sum(x["y"] == zoom)) for x in (wide, default, narrow)]
    assert counts[0] >= counts[1] >= counts[2] and counts[0] > counts[2]


def test_gru_van_mot_chieu_va_luu_nap_duoc(tmp_path):
    model = models.LSTMClassifier(cell="gru", hidden=16)
    assert isinstance(model.lstm, torch.nn.GRU) and model.lstm.bidirectional is False
    assert model(torch.zeros(2, config.T, 42)).shape == (2, len(config.CLASSES))
    path = models.save_checkpoint(model, tmp_path / "gru.pt")
    back, checkpoint = models.load_checkpoint(path)
    assert checkpoint["hparams"]["cell"] == "gru" and isinstance(back.lstm, torch.nn.GRU)
    with pytest.raises(ValueError, match="cell"):
        models.LSTMClassifier(cell="transformer")


def test_ghep_theo_lo_dung_luat_va_do_tin():
    p_lstm = np.array([[0.1, 0.7, 0.1, 0.05, 0.05],     # LSTM vuốt trái → lấy
                       [0.6, 0.0, 0.0, 0.4, 0.0],       # LSTM none, rừng zoom_out
                       [0.2, 0.0, 0.0, 0.8, 0.0]])      # LSTM zoom: bỏ qua
    p_rf = np.array([[0.2, 0.0, 0.0, 0.8, 0.0],
                     [0.3, 0.0, 0.0, 0.0, 0.7],
                     [0.9, 0.05, 0.05, 0.0, 0.0]])
    labels, conf = hybrid_predict(p_lstm, p_rf)
    np.testing.assert_array_equal(labels, [1, 4, 0])
    np.testing.assert_allclose(conf, [0.7, 0.7, 0.9])


@pytest.fixture
def saved(tmp_path, monkeypatch):
    X, y, pres, _ = labeled_windows("tr", n=6, seed=1)
    F = np.stack([window_features(w, r) for w, r in zip(X, pres)])
    rf_path = forest.save_bundle(forest.train_forest(F, y, n_jobs=1), tmp_path / "rf.joblib")
    training.set_seed(0)
    lstm_path = models.save_checkpoint(models.LSTMClassifier(hidden=16), tmp_path / "m.pt")
    monkeypatch.setattr(config, "RF_MODEL_PATH", rf_path)
    monkeypatch.setattr(config, "LSTM_MODEL_PATH", lstm_path)
    return lstm_path, rf_path


def test_nhan_va_do_tin_theo_lo_khop_tung_cua_so_cua_demo(saved):
    """Mức sự kiện chấm cả lô; demo chấm từng cửa sổ — cùng nhãn, cùng độ tin."""
    from src.live import make_model

    X, _, pres, _ = labeled_windows("va", n=2, seed=2)
    F = np.stack([window_features(w, r) for w, r in zip(X, pres)])
    for name in ("rules", "rf", "lstm", "hybrid"):
        labels, conf, _ = evaluation.label_confidence(name, F, X)
        model = make_model(name)
        kind = getattr(model, "input_kind", "features")
        for k in range(len(X)):
            args = ((X[k], F[k]) if kind == "both" else
                    (X[k],) if kind == "window" else (F[k],))
            label, confidence = model(*args)
            assert label == labels[k], name
            assert confidence == pytest.approx(conf[k], abs=1e-6), name


def test_huan_luyen_lstm_tai_lap_va_so_epoch_co_dinh():
    """Cùng seed thì cùng từng chữ số; học số epoch cố định thì không đo, không
    chọn gì trên tập đánh giá (Bảng 7)."""
    X, y, _, _ = labeled_windows("a", n=3, seed=3)
    Xv, yv, _, _ = labeled_windows("b", n=2, seed=4)
    kwargs = {"model_kwargs": {"hidden": 16}, "max_epochs": 3, "patience": 3, "window": 1}
    first = training.train_lstm(X, y, Xv, yv, seed=5, **kwargs)
    second = training.train_lstm(X, y, Xv, yv, seed=5, **kwargs)
    assert first.history == second.history and len(first.history) == 3
    assert "train_loss" in first.history[0]
    quick = training.train_lstm(X, y, Xv, yv, seed=5, measure_train=False, **kwargs)
    assert "train_loss" not in quick.history[0]
    assert [r["val_loss"] for r in quick.history] == [r["val_loss"] for r in first.history]
    fixed = training.train_lstm(X, y, seed=5, fixed_epochs=2, model_kwargs={"hidden": 16})
    assert fixed.stopper is None and [r["epoch"] for r in fixed.history] == [1, 2]
    assert set(fixed.history[0]) == {"epoch", "train_loss_running"}


def test_bien_the_lstm_chay_sau_tang_cuong():
    """Chuỗi của biến thể (11 điểm) dựng SAU tăng cường: 22 chiều mỗi bước."""
    X, y, _, _ = labeled_windows("a", n=1)
    columns = landmark_columns()
    dataset = WindowDataset(X, y, "train", augment=True, rng=np.random.default_rng(0),
                            sigma=0.01, sequence=lambda w: window_sequence(w)[:, columns])
    item, _ = dataset[0]
    assert tuple(item.shape) == (config.T, 22)
    fixed = WindowDataset(X, y, "val", sequence=lambda w: window_sequence(w)[:, columns])
    np.testing.assert_array_equal(fixed[0][0].numpy(), window_sequence(X[0])[:, columns])


def test_moi_thi_nghiem_doi_dung_mot_yeu_to_va_khong_cham_test():
    """Mọi hàng của bảng đổi ĐÚNG MỘT yếu tố so với cấu hình chính (k-fold đổi
    cách chia cùng số fold, và LSTM của nó học số epoch cố định)."""
    from tests.scripts_import import load_script

    runner = load_script("run_experiments")
    exps = runner.registry()
    for table in runner.ALL_TABLES:
        assert set(runner.table_experiments(table)) <= set(exps)
    for name, spec in exps.items():
        full = experiments.full_spec(spec)
        changed = {k for k in full if k != "model"
                   and full[k] != experiments.DEFAULT_SPEC[k]}
        if full["split"] == "fold":
            assert changed <= {"split", "fold", "epochs"}, name
            assert full["model"] != "lstm" or full["epochs"] == config.EXP_KFOLD_EPOCHS
        else:
            assert len(changed) <= 1, (name, changed)
    assert "test" not in json.dumps(exps)
    assert experiments.pool_subjects({"train": ["a"], "val": ["b"], "test": ["c"]}) == ["a", "b"]


def test_so_voi_windows_npz_coi_nan_o_cung_cho_la_trung():
    """Bước mất tay là NaN (luật 4). np.array_equal trơn coi NaN != NaN, nên
    từng báo bộ cửa sổ dựng lại KHÁC windows.npz dù hai bộ trùng từng bit."""
    from tests.scripts_import import load_script

    same = load_script("run_experiments").same_values
    X = np.array([[0.5, np.nan], [1.0, 2.0]], dtype=np.float32)
    assert same(X, X.copy())
    moved = X.copy()
    moved[0] = [np.nan, 0.5]
    assert not same(X, moved), "NaN ở chỗ khác là khác"
    assert same(np.array(["p1", "p2"]), np.array(["p1", "p2"]))
    assert not same(np.array([0, 1]), np.array([0, 2]))


def test_chinh_tang_kich_hoat_khong_lam_ban_ghi_het_han(monkeypatch):
    """Phase 9–10 chỉnh máy trạng thái, chạy SAU mô hình: bản ghi giữ nguyên,
    không phải học lại. Hằng số đổi dữ liệu, hay hằng số mới không có tiền tố
    FSM_, vẫn làm bản ghi hết hạn."""
    spec = experiments.full_spec({"model": "lstm"})

    def key():
        return experiments.record_key(spec, "dữ liệu")

    base = key()
    with monkeypatch.context() as m:
        m.setattr(config, "MIN_PRESENCE", 0.8)
        assert key() != base, "MIN_PRESENCE đổi tập cửa sổ"
    with monkeypatch.context() as m:
        m.setattr(config, "HANG_SO_MOI", 1, raising=False)
        assert key() != base, "hằng số lạ: cho hết hạn, không đoán"
    for name, value in (("CONF_FIRE", 0.6), ("CONF_HOLD", 0.5), ("K_OF_N", (2, 5)),
                        ("COOLDOWN_SEC", 1.0), ("FSM_BAT_KY", 1)):
        monkeypatch.setattr(config, name, value, raising=False)
    assert key() == base


def test_man_hinh_luyen_tap_khong_lam_ban_ghi_het_han(monkeypatch):
    """Hai hằng số của màn hình luyện tập (2026-10-26) từng làm cả 46 bản ghi hết
    hạn. SHOW_FINGERS chỉ đổi màn hình. FINGER_TIPS suy ra từ TIPS và FINGER_MCPS,
    hai hằng số vẫn được băm: đầu ngón thật mà đổi thì bản ghi vẫn hết hạn."""
    spec = experiments.full_spec({"model": "lstm"})
    relevant = experiments.relevant_config()
    assert "SHOW_FINGERS" not in relevant and "FINGER_TIPS" not in relevant
    assert {"TIPS", "FINGER_MCPS"} <= set(relevant)
    assert config.FINGER_TIPS == dict(zip(config.FINGER_MCPS, config.TIPS[1:]))
    base = experiments.record_key(spec, "dữ liệu")
    monkeypatch.setattr(config, "SHOW_FINGERS", {"zoom_in": ("index",)})
    assert experiments.record_key(spec, "dữ liệu") == base
    monkeypatch.setattr(config, "TIPS", [*config.TIPS[:-1], config.TIPS[-1] - 1])
    assert experiments.record_key(spec, "dữ liệu") != base, "đầu ngón đổi: hết hạn qua TIPS"


@pytest.fixture
def tiny_project(tmp_path, monkeypatch):
    """Sáu người (bốn train, hai val, một test không bao giờ được đọc), mỗi người
    một video tổng hợp có vuốt và zoom; config trỏ mọi đường dẫn vào tmp."""
    sign = config.SWIPE_LEFT_SIGN or 1
    shift = [sign * SWIPE_PALMS * PALM_PX, 0.0]
    landmarks = tmp_path / "landmarks" / "ipn"
    landmarks.mkdir(parents=True)
    people = {"train": ["p1", "p2", "p3", "p4"], "val": ["p5", "p6"], "test": ["p9"]}
    for k, subject in enumerate(sum(people.values(), [])):
        save_parts_clip(landmarks / f"{subject}_c.npz", [
            (make_static(30, seed=k), "D0X", "none"),
            (make_swipe(sign, 15), "G05", "swipe_left"),
            (make_static(30, seed=k + 1) + shift, "B0A", "none"),
            (make_swipe(-sign, 15) + shift, "G06", "swipe_right"),
            (make_static(30, seed=k + 2), "D0X", "none"),
            (make_zoom("in", 15), "G10", "zoom_in"),
            (make_static(30, seed=k + 3), "D0X", "none"),
            (make_zoom("out", 15), "G11", "zoom_out"),
            (make_static(30, seed=k + 4), "D0X", "none")], subject=subject)
    splits = tmp_path / "splits.json"
    splits.write_text(json.dumps({**people, "real_tune": [], "real_test": []}),
                      encoding="utf-8")
    monkeypatch.setattr(config, "LANDMARKS_DIR", tmp_path / "landmarks")
    monkeypatch.setattr(config, "SPLITS_JSON", splits)
    monkeypatch.setattr(config, "EXP_DATA_DIR", tmp_path / "experiments")
    monkeypatch.setattr(config, "EXP_RECORD_DIR", tmp_path / "records")
    monkeypatch.setattr(config, "EXP_FOLDS", 3)
    experiments.natural_pool.cache_clear()
    yield tmp_path
    experiments.natural_pool.cache_clear()


def test_thi_nghiem_rung_tu_dau_den_cuoi(tiny_project):
    """Dựng bộ cửa sổ và dòng thời gian video, học rừng, ghi bản ghi; chấm lại
    ở hai mức. Bản ghi hết hạn khi spec đổi. Không cửa sổ nào của người test."""
    data_fp = experiments.data_fingerprint()
    for spec in ({"model": "rf"}, {"model": "rf", "features": "angles"},
                 {"model": "rf", "split": "fold", "fold": 2}):
        spec = experiments.full_spec(spec)
        experiments.prepare_set(spec, data_fp)
        experiments.prepare_stream(spec, data_fp)
        name = f"t_{spec['features']}_{spec['split']}"
        experiments.run_experiment(name, spec, data_fp)
        assert experiments.has_record(name, spec, data_fp)
        assert not experiments.has_record(name, {**spec, "seed": 7}, data_fp)
        meta, arrays = experiments.load_record(name)
        assert "p9" not in set(arrays["subj_va"])
        assert arrays["proba_va"].shape == (arrays["y_va"].size, len(config.CLASSES))
        labels, _ = experiments.predictions(arrays, "va")
        window = experiments.window_metrics(arrays["y_va"], labels, arrays["src_va"])
        assert 0.0 <= window["macro_f1"] <= 1.0
        from src.events import load_streams
        timelines = load_streams(config.EXP_DATA_DIR / meta["stream"], windows=False)[0]
        assert {t.subject for t in timelines} == set(arrays["subj_va"])
        summary, _ = experiments.event_metrics(
            timelines, *experiments.predictions(arrays, "stream"))
        assert summary["n_gestures"] == 4 * len(timelines)
        if spec["features"] == "angles":
            assert meta["train"]["n_features"] == len(FEATURE_NAMES) + len(ANGLE_NAMES)

    data = experiments.load_set(experiments.set_path(experiments.full_spec({}), data_fp))
    assert set(data["subj_va"]) == {"p5", "p6"} and set(data["subj_tr"]) <= {"p1", "p2",
                                                                            "p3", "p4"}
    assert np.mean(data["y_tr"] == 0) <= config.NONE_TRAIN_SHARE + 1e-9
