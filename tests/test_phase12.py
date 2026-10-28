"""Kiểm thử Phase 12 — run_all.py dựng lại đường ống. Không chạy script nào, không
đụng data/ hay results/ thật."""

import json

import pytest

from src import config, experiments, models
from tests.scripts_import import load_script

run_all = load_script("run_all")


def args_of(step):
    return [] if callable(step.run) else [a for command in step.run for a in command]


def test_thu_tu_dung_va_khong_bao_gio_cham_tap_test():
    """Điểm mốc → cửa sổ → mô hình → bảng. eval_rules, train_rf, train_lstm ghi
    hàng chưa có mức sự kiện vào bảng so sánh, nên phải chạy trước evaluate.
    Không bước nào chạy test hay real_test (luật 13)."""
    order = [s.name for s in run_all.steps()]
    at = order.index
    assert at("landmarks") < at("splits") < at("windows") < at("rf") < at("lstm")
    assert max(at("eval_rules"), at("rf"), at("lstm"), at("lstm_deployed")) < at("evaluate")
    assert at("lstm_deployed") < min(at("experiments"), at("sweep_activation"),
                                     at("bench_analyze"))
    for step in run_all.steps():
        args = args_of(step)
        assert "--final" not in args, step.name
        assert all(args[i + 1] not in ("test", "real_test")
                   for i, a in enumerate(args[:-1]) if a == "--split"), step.name


def test_splits_co_roi_thi_khong_chay_lai(tmp_path, monkeypatch):
    """make_splits.py ghi đè splits.json — Phase 11 thêm real_tune/real_test vào
    đó, nên run_all không bao giờ được chạy lại nó khi file đã có."""
    path = tmp_path / "splits.json"
    monkeypatch.setattr(config, "SPLITS_JSON", path)
    splits = next(s for s in run_all.steps() if s.name == "splits")
    assert splits.done()[0] is False
    path.write_text("{}", encoding="utf-8")
    assert splits.done()[0] is True


def fake_run(train_dir, name, survey, windows_sha):
    """Một lần chạy train_lstm.py giả: manifest với ``survey`` và một checkpoint
    học trên bộ cửa sổ có băm ``windows_sha``."""
    run = train_dir / name
    run.mkdir(parents=True)
    (run / "manifest.json").write_text(json.dumps({"survey": survey}), encoding="utf-8")
    return models.save_checkpoint(models.LSTMClassifier(hidden=16),
                                  run / config.PHASE7_LSTM_PATH.name,
                                  windows_sha256=windows_sha, epoch=int(name[4:]))


@pytest.fixture
def deploy_tree(tmp_path, monkeypatch):
    from src.forest import file_sha256

    windows = tmp_path / "windows.npz"
    windows.write_bytes(b"bo cua so")
    monkeypatch.setattr(config, "WINDOWS_NPZ", windows)
    monkeypatch.setattr(config, "PHASE7_RESULTS_DIR", tmp_path / "phase7")
    monkeypatch.setattr(config, "LSTM_MODEL_PATH", tmp_path / "phase10" / "lstm_model.pt")
    return tmp_path / "phase7" / "train_lstm", file_sha256(windows)


def test_lstm_cua_demo_chep_lan_khao_sat_moi_nhat_dung_cong_thuc_va_du_lieu(deploy_tree):
    """Không theo số run_NN (dựng lại từ đầu thì số đổi): lấy lần khảo sát mới
    nhất có ĐÚNG công thức DEPLOY_ và học trên ĐÚNG bộ cửa sổ hiện tại; chép từng
    byte, không học lại."""
    from src.forest import file_sha256

    train_dir, sha = deploy_tree
    recipe = run_all.deploy_recipe()
    fake_run(train_dir, "run_02", recipe, sha)
    newest = fake_run(train_dir, "run_09", recipe, sha)
    fake_run(train_dir, "run_10", recipe, "bo cua so khac")      # mới hơn nhưng khác dữ liệu
    fake_run(train_dir, "run_11", {}, sha)                       # mô hình chính
    fake_run(train_dir, "run_12", {**recipe, "patience": 5}, sha)  # công thức khác

    assert run_all.deploy_candidates()[0] == newest

    def no_training(command):
        raise AssertionError("đã có lần khảo sát đúng công thức — không được học lại")

    assert run_all.deploy_lstm(train=no_training) == newest
    assert file_sha256(config.LSTM_MODEL_PATH) == file_sha256(newest)


def test_lstm_cua_demo_chua_co_thi_hoc_dung_cong_thuc_roi_chep(deploy_tree):
    train_dir, sha = deploy_tree
    commands = []

    def train(command):
        commands.append(command)
        fake_run(train_dir, "run_01", run_all.deploy_recipe(), sha)

    source = run_all.deploy_lstm(train=train)
    (command,) = commands
    assert command[1].endswith("train_lstm.py")
    assert command[2:] == ["--zoom-style-p", str(config.DEPLOY_ZOOM_STYLE_P),
                           "--static-share", str(config.DEPLOY_STATIC_SHARE)]
    assert config.LSTM_MODEL_PATH.read_bytes() == source.read_bytes()


def test_bang_so_sanh_chi_xong_khi_du_moi_mo_hinh_qua_may_trang_thai(tmp_path, monkeypatch):
    """train_rf.py hay train_lstm.py ghi hàng KHÔNG có mức sự kiện: bảng chưa xong
    tới khi evaluate.py --events đã chạy cho mọi mô hình."""
    from src.evaluation import upsert_comparison

    stem = tmp_path / "model_comparison"
    monkeypatch.setattr(config, "MODEL_COMPARISON", stem)
    base = {"split": "val", "n_windows": 1, "macro_f1": 0.5, "baseline_random": 0.1,
            "baseline_none": 0.2, "run": "x"}
    for model in config.MODEL_NAMES:
        upsert_comparison({**base, "model": model, "event_filter": config.EVENT_FILTER,
                           "event_f1": 0.5, "cmds_per_gesture": 1.0, "false_per_min": 1.0},
                          stem)
    assert run_all.comparison_done()[0] is True
    upsert_comparison({**base, "model": "rf"}, stem)      # train_rf.py ghi lại hàng rf
    done, note = run_all.comparison_done()
    assert done is False and "rf" in note


def test_cong_thuc_lstm_cua_demo_khong_lam_ban_ghi_het_han(monkeypatch):
    """Bản ghi của mô hình đã lưu băm thẳng file mô hình; DEPLOY_ chỉ quyết định
    file đó học thế nào, nên không băm vào bản ghi Phase 8."""
    spec = experiments.full_spec({"model": "lstm"})
    assert not any(k.startswith("DEPLOY_") for k in experiments.relevant_config())
    base = experiments.record_key(spec, "dữ liệu")
    monkeypatch.setattr(config, "DEPLOY_ZOOM_STYLE_P", 0.9)
    assert experiments.record_key(spec, "dữ liệu") == base


def test_moi_goi_trong_requirements_deu_ghim_phien_ban():
    """DoD Phase 12: mọi gói trong requirements.txt đều có ==."""
    lines = [line.split("#")[0].strip()
             for line in (config.ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()]
    packages = [line for line in lines if line]
    assert packages and all("==" in p for p in packages), packages
