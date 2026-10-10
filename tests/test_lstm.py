"""Kiểm thử LSTM (Phase 7) — dữ liệu tổng hợp, không đụng data/ hay results/."""

import numpy as np
import pytest
import torch
from torch import nn
from torch.utils.data import DataLoader

from src import config, evaluation, models, training
from src.datasets import WindowDataset, window_sequence, window_sequences
from tests.fixtures import labeled_windows

SIGMA = 0.01


def small_model(**kwargs):
    training.set_seed(0)
    return models.LSTMClassifier(**{"hidden": 16, **kwargs})


def test_model_khong_bao_gio_bidirectional():
    """bidirectional cố định bên trong: không có tham số để bật (luật 10)."""
    model = models.LSTMClassifier()
    assert model.lstm.bidirectional is False
    with pytest.raises(TypeError):
        models.LSTMClassifier(bidirectional=True)
    for pooling in models.POOLINGS:
        assert models.LSTMClassifier(pooling=pooling).lstm.bidirectional is False


def test_dau_vao_dung_42_chieu():
    """Mỗi bước là đúng 21 điểm × 2 toạ độ trải phẳng — reshape, không thêm gì;
    mô hình từ chối đầu vào khác 42 chiều."""
    X, y, _, _ = labeled_windows("a", n=1)
    seq = window_sequence(X[0])
    assert seq.shape == (config.T, 42) == (config.T, config.LSTM_INPUT_SIZE)
    np.testing.assert_array_equal(seq, X[0].reshape(config.T, 42))
    assert seq[0, 2] == X[0][0, 1, 0], "điểm 1, toạ độ x nằm ở cột 2"

    item, label = WindowDataset(X, y, "val")[3]
    assert tuple(item.shape) == (config.T, 42) and item.dtype == torch.float32
    assert label == y[3]

    model = small_model()
    assert model(torch.zeros(4, config.T, 42)).shape == (4, len(config.CLASSES))
    with pytest.raises(ValueError, match="42"):
        model(torch.zeros(4, config.T, 63))     # thêm z: cấm (luật 12)
    with pytest.raises(ValueError):
        window_sequence(np.zeros((config.T, 21, 3)))


def test_buoc_mat_tay_lay_buoc_co_tay_gan_nhat_truoc_no():
    """Không nội suy, không điền 0, không dùng bước sau (luật 10)."""
    X, _, _, _ = labeled_windows("a", n=1)
    win = X[1].copy()
    win[5:9] = np.nan
    seq = window_sequence(win)
    assert np.all(np.isfinite(seq))
    for t in range(5, 9):
        np.testing.assert_array_equal(seq[t], win[4].reshape(-1))
    np.testing.assert_array_equal(seq[9], win[9].reshape(-1))

    win[0] = np.nan
    with pytest.raises(ValueError, match="Bước đầu"):
        window_sequence(win)


def test_augment_chi_bat_o_tap_train():
    """Tăng cường chỉ bật được cho train (luật 9), và tạo bản MỚI mỗi lần lấy —
    tức mỗi epoch. Không tăng cường thì mẫu không bao giờ đổi."""
    X, y, _, _ = labeled_windows("a", n=2)
    for split in ("val", "test", "real_tune", "real_test"):
        with pytest.raises(ValueError, match="train"):
            WindowDataset(X, y, split, augment=True, sigma=SIGMA)
        WindowDataset(X, y, split)      # không tăng cường thì được

    fixed = WindowDataset(X, y, "train")
    np.testing.assert_array_equal(fixed[0][0], fixed[0][0])
    np.testing.assert_array_equal(fixed[0][0], window_sequence(X[0]))

    augmented = WindowDataset(X, y, "train", augment=True,
                              rng=np.random.default_rng(0), sigma=SIGMA)
    first, second = augmented[0][0], augmented[0][0]
    assert not torch.equal(first, second), "hai lần lấy (hai epoch) phải khác nhau"
    np.testing.assert_array_equal(X, labeled_windows("a", n=2)[0],
                                  err_msg="tăng cường không được sửa X")


def test_overfit_10_mau():
    """Phép thử vòng huấn luyện: 10 mẫu, 200 epoch → học thuộc gần 100%.
    Không học thuộc nổi thì lỗi ở vòng huấn luyện, mọi kết quả sau vô nghĩa."""
    X, y, _, _ = labeled_windows("a", n=2, seed=3)      # 10 mẫu, 2 mỗi lớp
    assert len(y) == 10
    training.set_seed(config.SEED)
    model = models.LSTMClassifier()
    dataset = WindowDataset(X, y, "train")
    loader = DataLoader(dataset, batch_size=10, shuffle=True,
                        generator=torch.Generator().manual_seed(config.SEED))
    loss_fn = nn.CrossEntropyLoss(weight=training.class_weights(y))
    optimizer = torch.optim.Adam(model.parameters(), lr=config.LSTM_LR)
    losses = [training.train_epoch(model, loader, loss_fn, optimizer)
              for _ in range(200)]

    loss, pred = training.evaluate(model, window_sequences(X), y, loss_fn)
    assert np.mean(pred == y) >= 0.9
    assert losses[-1] < 0.1 * losses[0] and loss < 0.1


def test_trong_so_lop_balanced():
    y = np.array([0] * 6 + [1, 2, 3, 4] * 1 + [1, 2])
    w = training.class_weights(y).numpy()
    counts = np.bincount(y)
    np.testing.assert_allclose(w * counts, len(y) / len(config.CLASSES))
    with pytest.raises(ValueError, match="zoom_out"):
        training.class_weights(np.array([0, 1, 2, 3]))


def test_dung_som_giu_epoch_tot_nhat():
    model = small_model()
    stopper = training.EarlyStop(patience=2)
    scores = [0.1, 0.3, 0.3, 0.2, 0.25, 0.9]
    for epoch, score in enumerate(scores, start=1):
        stopper.update(epoch, score, model)
        if stopper.should_stop:
            break
    assert (stopper.best_epoch, stopper.best_score) == (2, 0.3), "bằng điểm: giữ epoch sớm"
    assert stopper.last_epoch == 4, "dừng sau 2 epoch không tăng"
    assert stopper.best_state is not None


def test_tom_tat_duong_hoc_chiu_duoc_nhieu():
    """Điểm thấp nhất của loss val tìm trên đường đã làm mượt, không trên một
    epoch lẻ; mức của các epoch cuối đo độ lạc quan của checkpoint."""
    val = [1.0, 0.8, 0.6, 0.5, 0.45, 0.2, 0.5, 0.55, 0.6, 0.7, 0.8]   # 0.2: nhiễu
    history = [{"epoch": e, "val_loss": v, "val_macro_f1": 1 - v}
               for e, v in enumerate(val, start=1)]
    epoch, value = training.smoothed_minimum(history, "val_loss", window=3)
    assert epoch == 6 and value == pytest.approx((0.5 + 0.45 + 0.2) / 3)
    assert training.smoothed_minimum(history, "val_loss", window=1)[0] == 6
    mean, std = training.tail_stats(history, "val_macro_f1", n=3)
    assert mean == pytest.approx(1 - 0.7) and std == pytest.approx(np.std([0.4, 0.3, 0.2]))


def test_fit_ghi_lich_su_va_dung_dung_luc():
    X, y, _, _ = labeled_windows("a", n=3)
    seq = window_sequences(X)
    model = small_model()
    loader = DataLoader(WindowDataset(X, y, "train"), batch_size=8, shuffle=False)
    loss_fn = nn.CrossEntropyLoss(weight=training.class_weights(y))
    optimizer = torch.optim.Adam(model.parameters(), lr=config.LSTM_LR)
    seen = []
    history, stopper = training.fit(model, loader, seq, y, seq, y, loss_fn, optimizer,
                                    max_epochs=3, patience=10,
                                    on_epoch=lambda row, s: seen.append(row["epoch"]))
    assert [r["epoch"] for r in history] == seen == [1, 2, 3]
    assert set(history[0]) == {"epoch", "train_loss_running", "train_loss", "val_loss",
                               "train_macro_f1", "val_macro_f1"}
    assert 1 <= stopper.best_epoch <= 3


def test_luu_nap_checkpoint_va_chan_lech_cau_hinh(tmp_path, monkeypatch):
    """Meta kiểu "gần như thuần" — torch.__version__ (lớp con của str), số
    numpy — vẫn nạp được ở chế độ an toàn weights_only."""
    model = small_model(pooling="mean")
    path = models.save_checkpoint(model, tmp_path / "m.pt", epoch=np.int64(7),
                                  val_macro_f1=np.float64(0.5),
                                  torch_version=torch.__version__,
                                  weights=[np.float32(0.4)])
    loaded, checkpoint = models.load_checkpoint(path)
    assert checkpoint["epoch"] == 7 and checkpoint["val_macro_f1"] == 0.5
    assert type(checkpoint["torch_version"]) is str
    assert loaded.hparams == model.hparams and not loaded.training
    x = torch.randn(3, config.T, 42)
    model.eval()
    torch.testing.assert_close(loaded(x), model(x))

    with pytest.raises(FileNotFoundError, match="train_lstm.py"):
        models.load_checkpoint(tmp_path / "chua_co.pt")
    monkeypatch.setattr(config, "T", config.T + 1)      # cửa sổ dài hơn lúc huấn luyện
    with pytest.raises(ValueError, match="T"):
        models.load_checkpoint(path)


def test_bo_phan_loai_cho_demo_khop_du_doan_theo_lo(tmp_path, monkeypatch):
    """demo.py dự đoán từng cửa sổ, evaluate.py dự đoán cả lô — cùng nhãn;
    confidence là xác suất softmax cao nhất."""
    path = models.save_checkpoint(small_model(), tmp_path / "m.pt", epoch=1)
    monkeypatch.setattr(config, "LSTM_MODEL_PATH", path)
    X, _, _, _ = labeled_windows("b", n=2)

    runner = models.LSTMRunner(path)
    assert runner.input_kind == "window"
    batch, details = evaluation.predict_windows("lstm", np.zeros((len(X), 15)), X)
    proba = models.predict_proba(runner.load().model, window_sequences(X))
    for k, win in enumerate(X):
        label, confidence = runner(win)
        assert label == batch[k] == int(np.argmax(proba[k]))
        assert confidence == pytest.approx(float(proba[k].max()))
    assert details["epoch"] == 1
    with pytest.raises(ValueError, match="X"):
        evaluation.predict_windows("lstm", np.zeros((2, 15)))
