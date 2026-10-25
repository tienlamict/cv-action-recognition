"""Kiểm thử máy trạng thái kích hoạt (Phase 9) — logic thuần, không cần camera;
cộng phép mô phỏng MIN_PRESENCE của bảng đánh đổi, trên clip tổng hợp."""

import numpy as np
import pytest

from src import config, events
from src.activation import CANDIDATE, COOLDOWN, IDLE, READY, ActivationFSM
from tests.fixtures import make_static, save_parts_clip

NONE = config.CLASSES.index("none")
LEFT = config.CLASSES.index("swipe_left")
RIGHT = config.CLASSES.index("swipe_right")
GONE = None             # một lần dự đoán không có cửa sổ nào: mất tay


@pytest.fixture(autouse=True)
def spec_params(monkeypatch):
    """Tham số khởi đầu của SPEC — các kiểm thử viết cho chúng, nên không đổi
    theo lúc chọn cấu hình cuối ở Phase 10."""
    monkeypatch.setattr(config, "CONF_FIRE", 0.75)
    monkeypatch.setattr(config, "CONF_HOLD", 0.55)
    monkeypatch.setattr(config, "K_OF_N", (3, 5))
    monkeypatch.setattr(config, "COOLDOWN_SEC", 1.2)


def run(windows, fsm=None, ts=None):
    """Đưa một chuỗi cửa sổ qua máy. Mỗi phần tử là ``(nhãn, độ tin)`` — tay vẫn
    trong khung — hoặc ``GONE``; mặc định cách nhau ``STRIDE_SEC``.

    Returns:
        list ``(giây, lệnh)``.
    """
    fsm = fsm or ActivationFSM()
    ts = ts if ts is not None else [i * config.STRIDE_SEC for i in range(len(windows))]
    out = []
    for t, window in zip(ts, windows):
        command = (fsm.update(None, None, None, t) if window is GONE
                   else fsm.update(window[0], window[1], 1.0, t))
        if command is not None:
            out.append((t, command))
    return out


def test_mot_cu_chi_mot_lenh():
    """8 cửa sổ swipe_left liên tiếp → đúng 1 lệnh, phát ở cửa sổ đồng ý thứ k."""
    commands = run([(LEFT, 0.9)] * 8)
    assert [c for _, c in commands] == [LEFT]
    assert commands[0][0] == pytest.approx(2 * config.STRIDE_SEC)


def test_nhan_nhay_khong_phat():
    """swipe, none, swipe, none, swipe → 0 lệnh. Đếm phiếu trên cửa sổ trượt thì
    chuỗi này có 3/5 phiếu; ở đây một none tự tin là phiếu phản đối."""
    assert run([(LEFT, 0.9), (NONE, 0.9)] * 2 + [(LEFT, 0.9)]) == []


def test_cooldown():
    """Hai cụm cách nhau 0,5 s → 1 lệnh; bỏ cooldown thì thành 2 lệnh."""
    bursts = [(LEFT, 0.9)] * 8
    ts = [0.0, 0.2, 0.4, 0.6, 1.1, 1.3, 1.5, 1.7]
    assert len(run(bursts, ts=ts)) == 1
    assert len(run(bursts, ActivationFSM(cooldown_sec=0.0), ts)) == 2


def test_ha_tay_xoa_trang_thai():
    """2 cửa sổ swipe, mất tay, 2 cửa sổ swipe → 0 lệnh; không mất tay thì bốn
    cửa sổ đó phát lệnh. Mất tay xoá cả cooldown."""
    swipe = [(LEFT, 0.9)] * 2
    assert run(swipe + [GONE] + swipe) == []
    assert len(run(swipe + swipe)) == 1
    fsm = ActivationFSM()
    run([(LEFT, 0.9)] * 3 + [GONE], fsm)
    assert fsm.state == IDLE and fsm.fired_at is None


def test_nguong_tin_cay():
    """5 cửa sổ swipe độ tin 0,6 với CONF_FIRE 0,75 → 0 lệnh; hạ CONF_FIRE xuống
    0,6 thì chính chuỗi đó phát lệnh."""
    weak = [(LEFT, 0.6)] * 5
    assert run(weak) == []
    assert len(run(weak, ActivationFSM(conf_fire=0.6))) == 1


def test_cua_so_do_du_khong_la_phieu_nhung_chiem_cho_trong_n():
    """Cửa sổ độ tin dưới CONF_HOLD hay không có dự đoán không phá đồng thuận,
    nhưng chiếm chỗ trong n: k = 3 trên n = 5 chịu được hai cửa sổ do dự, không
    chịu được ba."""
    two = [(LEFT, 0.9), (LEFT, 0.4), (None, None), (LEFT, 0.9), (LEFT, 0.9)]
    assert [c for _, c in run(two)] == [LEFT]
    three = [(LEFT, 0.9), (LEFT, 0.4), (None, None), (NONE, 0.5), (LEFT, 0.9), (LEFT, 0.9)]
    assert run(three) == []


def test_cu_chi_khac_tu_tin_mo_ngay_ung_vien_moi():
    """Đang chờ swipe_left mà ra swipe_right tự tin: đồng thuận thất bại, và chính
    cửa sổ đó mở ứng viên swipe_right."""
    commands = run([(LEFT, 0.9)] * 2 + [(RIGHT, 0.9)] * 3)
    assert [c for _, c in commands] == [RIGHT]


def test_ghi_moi_chuyen_trang_thai():
    log = []
    fsm = ActivationFSM(on_transition=lambda *transition: log.append(transition))
    run([(LEFT, 0.9)] * 3 + [GONE], fsm)
    assert [(a, b) for _, a, b, _ in log] == [(IDLE, READY), (READY, CANDIDATE),
                                             (CANDIDATE, COOLDOWN), (COOLDOWN, IDLE)]
    assert "PHÁT swipe_left" in log[2][3]


def test_tham_so_sai_bi_tu_choi():
    with pytest.raises(ValueError):
        ActivationFSM(k_of_n=(6, 5))
    with pytest.raises(ValueError):
        ActivationFSM(conf_fire=0.5, conf_hold=0.6)


def test_may_trang_thai_la_bo_loc_fsm_cua_muc_su_kien():
    """evaluate.py --events fsm và các bảng Phase 8 dùng đúng lớp này, mỗi video
    một máy mới; bảng đánh đổi truyền thẳng một hàm tạo máy có tham số riêng."""
    assert isinstance(events.make_filter("fsm"), ActivationFSM)
    assert events.make_filter("fsm") is not events.make_filter("fsm")
    assert events.make_filter(lambda: ActivationFSM(k_of_n=(1, 1))).k == 1


def test_nang_min_presence_tren_dong_thoi_gian_trung_chay_lai_video(tmp_path):
    """Bảng đánh đổi chạy video MỘT lần với ngưỡng thấp rồi chặn dần
    (events.gate_presence): phải trùng việc chạy lại video với từng ngưỡng."""
    hand = make_static(70)
    hand[20:25] = np.nan        # mất tay 5 bước và 4 bước: dài hơn MAX_GAP nên
    hand[45:49] = np.nan        # còn NaN, cho cửa sổ có tỉ lệ có tay 0,72–0,94
    path = save_parts_clip(tmp_path / "c.npz", [(hand, "D0X", "none")], subject="p")
    low, X_low, _ = events.clip_stream(path, min_presence=0.6)
    high, X_high, _ = events.clip_stream(path, min_presence=0.8)
    assert high.valid.sum() < low.valid.sum(), "ngưỡng 0,8 phải chặn bớt cửa sổ"

    n = int(low.valid.sum())
    labels, confidences = events.scatter([low], np.arange(n) % 5, np.full(n, 0.9))
    (gated,), (lab,), _ = events.gate_presence([low], labels, confidences, 0.8)
    np.testing.assert_array_equal(gated.ts, high.ts)
    np.testing.assert_array_equal(gated.presence, high.presence)
    np.testing.assert_array_equal(gated.valid, high.valid)
    kept = np.nan_to_num(low.presence[low.valid], nan=-1.0) >= 0.8
    np.testing.assert_array_equal(X_high, X_low[kept])
    np.testing.assert_array_equal(lab[gated.valid], (np.arange(n) % 5)[kept])
