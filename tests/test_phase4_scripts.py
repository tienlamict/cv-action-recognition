"""Kiểm thử các script Phase 4 — dữ liệu tổng hợp, không đụng data/."""

import numpy as np
import pytest

from src import config
from src.preprocess import normalize_window
from tests.fixtures import make_static, make_swipe, make_zoom, save_parts_clip
from tests.scripts_import import load_script

build = load_script("build_dataset")
sigma_script = load_script("estimate_sigma")
boxplots = load_script("plot_feature_boxplots")


def test_shape_X_dung_N_18_21_2(tmp_path):
    """windows.npz đúng schema: X (N, 18, 21, 2) float32 đã chuẩn hoá."""
    paths = [save_parts_clip(tmp_path / f"c{i}.npz", [
        (make_static(30, seed=i), "D0X", "none"),
        (make_zoom("in", 30), "G10", "zoom_in"),
        (make_static(30, seed=i + 10), "B0A", "none")], subject=f"p{i}")
        for i in range(2)]

    windows, _ = build.collect(paths)
    out = build.save_windows(tmp_path / "windows.npz", windows)

    with np.load(out, allow_pickle=False) as data:
        assert set(data.files) == set(build.FIELDS)
        X = data["X"]
        assert X.ndim == 4 and X.shape[1:] == (config.T, 21, 2) == (18, 21, 2)
        assert X.dtype == np.float32
        assert data["y"].dtype == np.int64
        for k in ("presence", "t0"):
            assert data[k].dtype == np.float32
        assert data["subject"].dtype.str.endswith("U16")
        assert data["clip"].dtype.str.endswith("U64")
        assert data["src_label"].dtype.str.endswith("U32")
    np.testing.assert_allclose(X[:, 0, config.WRIST], 0.0, atol=1e-6)
    assert set(windows["y"]) == {0, config.CLASSES.index("zoom_in")}


def test_bo_clip_lech_do_dai(tmp_path):
    import json
    path = save_parts_clip(tmp_path / "lech.npz",
                           [(make_static(30), "D0X", "none")], subject="p")
    with np.load(path) as data:
        arrays = {k: data[k] for k in data.files}
    meta = json.loads(str(arrays["meta"]))
    meta["length_mismatch"] = True
    np.savez_compressed(path, **{**arrays, "meta": json.dumps(meta)})

    windows, info = build.collect([path])
    assert windows["y"].size == 0 and info["mismatched"] == ["lech"]


def test_equal_quota_chia_deu_nhom_nho_lay_het():
    assert build.equal_quota({"a": 2, "b": 10, "c": 10}, 12) == {"a": 2, "b": 5, "c": 5}
    q = build.equal_quota({"a": 2, "b": 10, "c": 10}, 13)
    assert q["a"] == 2 and sorted([q["b"], q["c"]]) == [5, 6]
    assert build.equal_quota({"a": 3, "b": 4}, 100) == {"a": 3, "b": 4}
    for budget in range(0, 30):
        q = build.equal_quota({"a": 1, "b": 7, "c": 9, "d": 2}, budget)
        assert sum(q.values()) == min(budget, 19)
        assert all(q[k] <= v for k, v in {"a": 1, "b": 7, "c": 9, "d": 2}.items())


def test_lay_mau_con_none_chi_o_train_va_dung_ty_le():
    """Train: giữ mọi cửa sổ dương, none còn đúng NONE_TRAIN_SHARE, nhóm nhỏ
    giữ hết. Val/test không bị đụng tới."""
    y = np.array([1] * 10 + [0] * 63 + [0] * 50)
    src = np.array(["G05"] * 10 + ["D0X"] * 30 + ["G07"] * 3 + ["B0A"] * 30
                   + ["D0X"] * 50)
    split = np.array(["train"] * 73 + ["val"] * 50)

    keep, quota = build.subsample_none(y, src, split,
                                       np.random.default_rng(0), share=0.5)

    assert keep[:10].all(), "giữ mọi cửa sổ dương"
    assert keep[73:].all(), "val không bị lấy mẫu con"
    assert quota == {"B0A": 3, "D0X": 4, "G07": 3} or quota == {"B0A": 4, "D0X": 3, "G07": 3}
    train_kept = keep[:73]
    assert np.sum(train_kept & (y[:73] == 0)) == 10
    assert np.mean(y[:73][train_kept] == 0) == pytest.approx(0.5)


def test_estimate_sigma_tren_du_lieu_tong_hop():
    """Cửa sổ tay đứng yên có rung đã biết: σ ước lượng khớp; cửa sổ vuốt bị
    loại vì cổ tay dời xa."""
    rng = np.random.default_rng(0)
    base = normalize_window(make_static())[0]
    true_sigma = 0.02
    still = []
    for _ in range(40):
        win = np.repeat(base[None], config.T, axis=0)
        win[:, config.TIPS] += rng.normal(0, true_sigma, size=(config.T, 5, 2))
        still.append(win)
    moving = [normalize_window(make_swipe(+1)) for _ in range(760)]
    X = np.stack(still + moving)

    sigma, chosen, _, _ = sigma_script.estimate(X, quantile=0.05)

    assert chosen[:40].all() and not chosen[40:].any()
    assert sigma == pytest.approx(true_sigma, rel=0.15)


def quart(p25, p75):
    return {"p25": p25, "p50": (p25 + p75) / 2, "p75": p75}


def gate_input(dx_left, dx_right):
    q = {c: {"open_delta": quart(-0.1, 0.1), "pinch_delta": quart(-0.1, 0.1),
             "dx": quart(-0.1, 0.1), "straightness": quart(0.1, 0.3),
             "max_vx": quart(1.0, 2.0)} for c in config.CLASSES}
    for name in ("open_delta", "pinch_delta"):
        q["zoom_in"][name] = quart(0.2, 0.5)
        q["zoom_out"][name] = quart(-0.5, -0.2)
    q["swipe_left"]["dx"], q["swipe_right"]["dx"] = dx_left, dx_right
    for c in ("swipe_left", "swipe_right"):
        q[c]["straightness"] = quart(0.6, 0.9)
        q[c]["max_vx"] = quart(3.0, 6.0)
    return q


def test_cong_boxplot_khong_gia_dinh_dau_cua_dx():
    """Hai hộp dx ở hai phía của 0 là đạt, bất kể lớp nào bên dương."""
    for left, right in ((quart(0.2, 0.8), quart(-0.8, -0.2)),
                        (quart(-0.8, -0.2), quart(0.2, 0.8))):
        checks = boxplots.gate_checks(gate_input(left, right))
        assert all(ok for _, _, ok, _ in checks), checks

    checks = boxplots.gate_checks(gate_input(quart(-0.1, 0.8), quart(-0.8, -0.2)))
    assert [ok for _, c, ok, _ in checks if c.startswith("dx")] == [False]


def test_cong_dung_pinch_delta_dx_max_vx_con_spec_cu_chi_tham_khao():
    """Cổng (duyệt 2026-10-05): pinch_delta ×3, dx, max_vx. open_delta và
    straightness chỉ tham khảo — chúng hỏng không làm hỏng cổng."""
    q = gate_input(quart(0.2, 0.8), quart(-0.8, -0.2))
    checks = boxplots.gate_checks(q)
    gate = [c for g, c, _, _ in checks if g == "cổng"]
    reference = [c for g, c, _, _ in checks if g == "tham khảo"]
    assert len(gate) == 5 and len(reference) == 4
    assert all(c.startswith(("pinch_delta", "dx", "max_vx")) for c in gate)
    assert all(c.startswith(("open_delta", "straightness")) for c in reference)
    assert boxplots.gate_passed(checks)

    q["zoom_out"]["open_delta"] = quart(-0.1, 0.3)       # cổng cũ hỏng
    q["none"]["straightness"] = quart(0.5, 0.95)
    assert boxplots.gate_passed(boxplots.gate_checks(q))

    q["none"]["max_vx"] = quart(2.0, 4.0)                # cổng mới hỏng
    assert not boxplots.gate_passed(boxplots.gate_checks(q))
