"""Kiểm thử máy trạng thái kích hoạt (Phase 9) — logic thuần, không cần camera;
cộng phép mô phỏng MIN_PRESENCE của bảng đánh đổi, trên clip tổng hợp."""

import numpy as np
import pytest

from src import config, events
from src.activation import CANDIDATE, COOLDOWN, IDLE, PENDING, READY, ActivationFSM
from tests.fixtures import make_static, save_parts_clip

NONE = config.CLASSES.index("none")
LEFT = config.CLASSES.index("swipe_left")
RIGHT = config.CLASSES.index("swipe_right")
ZOOM_IN = config.CLASSES.index("zoom_in")
GONE = None             # một lần dự đoán không có cửa sổ nào: mất tay


@pytest.fixture(autouse=True)
def spec_params(monkeypatch):
    """Tham số khởi đầu của SPEC — các kiểm thử viết cho chúng, nên không đổi
    theo lúc chọn cấu hình cuối ở Phase 10."""
    monkeypatch.setattr(config, "CONF_FIRE", 0.75)
    monkeypatch.setattr(config, "CONF_HOLD", 0.55)
    monkeypatch.setattr(config, "K_OF_N", (3, 5))
    monkeypatch.setattr(config, "COOLDOWN_SEC", 1.2)
    monkeypatch.setattr(config, "FSM_ZOOM_FIRE", 0.75)
    monkeypatch.setattr(config, "FSM_ZOOM_K", 3)
    monkeypatch.setattr(config, "FSM_ARBITRATE_SEC", 0.0)


def run(windows, fsm=None, ts=None):
    """Đưa một chuỗi cửa sổ qua máy. Mỗi phần tử là ``(nhãn, độ tin)`` hoặc
    ``(nhãn, độ tin, độ mạnh)`` — tay vẫn trong khung — hoặc ``GONE``; mặc định
    cách nhau ``STRIDE_SEC``.

    Returns:
        list ``(giây, lệnh)``.
    """
    fsm = fsm or ActivationFSM()
    ts = ts if ts is not None else [i * config.STRIDE_SEC for i in range(len(windows))]
    out = []
    for t, window in zip(ts, windows):
        command = (fsm.update(None, None, None, t) if window is GONE
                   else fsm.update(window[0], window[1], 1.0, t,
                                   strength=window[2] if len(window) > 2 else None))
        if command is not None:
            out.append((t, command))
    return out


def power(label, value):
    """Độ mạnh của một cửa sổ: ``value`` theo chiều lớp ``label``, 0 ở lớp khác."""
    out = np.zeros(len(config.CLASSES))
    out[label] = value
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


def final_like():
    """Máy kiểu cấu hình cuối: vuốt 0,85 với 4/5, zoom 0,40 với 3/5."""
    return ActivationFSM(conf_fire=0.85, conf_hold=0.55, k_of_n=(4, 5),
                         zoom_fire=0.40, zoom_k=3)


def test_zoom_co_nguong_rieng_vuot_giu_nguyen():
    """Độ tin 0,45 ba cửa sổ: zoom thành lệnh ở cửa sổ thứ ba, vuốt thì không mở
    nổi ứng viên. Ba cửa sổ vuốt rất tự tin — đoạn lấy đà — vẫn không đủ 4/5."""
    weak_zoom = run([(ZOOM_IN, 0.45)] * 3, final_like())
    assert [c for _, c in weak_zoom] == [ZOOM_IN]
    assert weak_zoom[0][0] == pytest.approx(2 * config.STRIDE_SEC)
    assert run([(LEFT, 0.45)] * 5, final_like()) == []
    assert run([(LEFT, 1.0)] * 3 + [(NONE, 0.9)], final_like()) == []
    assert [c for _, c in run([(LEFT, 1.0)] * 4, final_like())] == [LEFT]


def test_nguong_giu_theo_ho_cua_ung_vien():
    """Ứng viên zoom giữ ở mức của zoom: none 0,45 đủ tin để phản đối, none 0,39
    chỉ là do dự. Ứng viên vuốt giữ ở CONF_HOLD: none 0,45 chỉ là do dự."""
    zoom = [(ZOOM_IN, 0.45), (ZOOM_IN, 0.45)]
    assert run(zoom + [(NONE, 0.45), (NONE, 0.1)], final_like()) == []
    assert len(run(zoom + [(NONE, 0.39), (ZOOM_IN, 0.45)], final_like())) == 1
    swipe = [(LEFT, 0.9)] * 2 + [(NONE, 0.45), (LEFT, 0.9), (LEFT, 0.9)]
    assert [c for _, c in run(swipe, final_like())] == [LEFT]


def test_nguong_zoom_mac_dinh_doc_tu_config(monkeypatch):
    monkeypatch.setattr(config, "FSM_ZOOM_FIRE", 0.33)
    monkeypatch.setattr(config, "FSM_ZOOM_K", 2)
    fsm = ActivationFSM()
    assert (fsm.zoom_fire, fsm.zoom_k) == (0.33, 2)
    assert [c for _, c in run([(ZOOM_IN, 0.34)] * 2, ActivationFSM())] == [ZOOM_IN]


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
    with pytest.raises(ValueError):
        ActivationFSM(zoom_k=6)
    with pytest.raises(ValueError):
        ActivationFSM(arbitrate_sec=-0.1)


ZOOM_OUT = config.CLASSES.index("zoom_out")


def test_trong_tai_chuan_bi_yeu_hon_thi_cu_chi_that_thang():
    """Chụm ngón chuẩn bị (zoom_out yếu) đủ phiếu trước cú mở thật (zoom_in mạnh).
    Không trọng tài: lệnh sai phát, cooldown chặn cú thật. Có trọng tài: zoom_in."""
    prep = [(ZOOM_OUT, 0.9, power(ZOOM_OUT, 0.3))] * 3
    real = [(ZOOM_IN, 0.9, power(ZOOM_IN, 0.8))] * 3
    assert [c for _, c in run(prep + real)] == [ZOOM_OUT]
    commands = run(prep + real, ActivationFSM(arbitrate_sec=0.6))
    assert [c for _, c in commands] == [ZOOM_IN]
    assert commands[0][0] == pytest.approx(5 * config.STRIDE_SEC)


def test_trong_tai_thu_tay_yeu_hon_thi_giu_lenh_that():
    """Cú vuốt thật đủ phiếu, rồi lúc thu tay (ngược chiều, yếu hơn) cũng đủ phiếu:
    phát lệnh thật, ngay khi kẻ thách thức thua — không đợi hết giờ."""
    real = [(LEFT, 0.9, power(LEFT, 0.9))] * 3
    back = [(RIGHT, 0.9, power(RIGHT, 0.4))] * 3
    commands = run(real + back, ActivationFSM(arbitrate_sec=1.0))
    assert [c for _, c in commands] == [LEFT]
    assert commands[0][0] == pytest.approx(5 * config.STRIDE_SEC)


def test_trong_tai_khong_ai_thach_thuc_thi_phat_khi_het_gio():
    """Không có lớp ngược chiều: phát lệnh chờ ở lần dự đoán đầu tiên sau hạn chờ.
    none và lớp của họ khác trong lúc chờ không huỷ lệnh đã đủ phiếu."""
    windows = ([(LEFT, 0.9, power(LEFT, 0.9))] * 3
               + [(NONE, 0.9, power(LEFT, 0.0)), (ZOOM_IN, 0.9, power(ZOOM_IN, 0.9))]
               + [(NONE, 0.9, power(LEFT, 0.0))] * 3)
    commands = run(windows, ActivationFSM(arbitrate_sec=0.4))
    assert commands == [(pytest.approx(4 * config.STRIDE_SEC), LEFT)]


def test_trong_tai_mat_tay_khi_cho_van_phat_lenh_da_du_phieu():
    log = []
    fsm = ActivationFSM(arbitrate_sec=0.6, on_transition=lambda *t: log.append(t))
    commands = run([(LEFT, 0.9, power(LEFT, 0.9))] * 3 + [GONE], fsm)
    assert commands == [(pytest.approx(3 * config.STRIDE_SEC), LEFT)]
    assert fsm.state == IDLE
    assert [(a, b) for _, a, b, _ in log][-3:] == [(CANDIDATE, PENDING), (PENDING, COOLDOWN),
                                                   (COOLDOWN, IDLE)]


def test_trong_tai_tat_hoac_thieu_do_manh_thi_phat_ngay_nhu_cu():
    """Chờ 0 giây, hoặc cửa sổ không có độ mạnh (bộ lọc cũ, bản lưu cũ): đủ phiếu là
    phát, đúng máy của Phase 10."""
    with_power = [(LEFT, 0.9, power(LEFT, 0.9))] * 3
    without = [(LEFT, 0.9)] * 3
    for windows, fsm in ((with_power, ActivationFSM(arbitrate_sec=0.0)),
                         (without, ActivationFSM(arbitrate_sec=0.6))):
        assert run(windows, fsm) == [(pytest.approx(2 * config.STRIDE_SEC), LEFT)]


def test_do_manh_theo_chieu_va_khong_doi_khi_chuan_hoa():
    """Cổ tay đi theo chiều vuốt trái (SWIPE_LEFT_SIGN đo trên IPN): độ mạnh vuốt trái
    dương, vuốt phải bằng 0. Mở cái–trỏ: zoom_in dương, zoom_out bằng 0. Cửa sổ pixel
    và cửa sổ đã chuẩn hoá cho cùng độ mạnh. core_signal (gán nhãn) đúng công thức cũ."""
    from src.preprocess import normalize_window
    from src.windows import core_signal, window_strengths
    from tests.fixtures import hand
    win = np.repeat(hand()[None], config.T, axis=0)
    step = np.arange(config.T, dtype=np.float64)[:, None]
    win[:, :, 0] += config.SWIPE_LEFT_SIGN * 4.0 * step
    away = win[0, config.THUMB_TIP] - win[0, config.INDEX_TIP]
    win[:, config.THUMB_TIP] += 4.0 * step * away / np.linalg.norm(away)
    s = window_strengths(win)
    assert s[LEFT] > 0 and s[RIGHT] == 0
    assert s[ZOOM_IN] > 0 and s[ZOOM_OUT] == 0 and s[NONE] == 0
    np.testing.assert_allclose(window_strengths(normalize_window(win)), s, rtol=1e-9)

    steps = np.arange(config.T)
    for name in ("swipe_left", "zoom_in"):
        palm = np.linalg.norm(win[:, config.MIDDLE_MCP] - win[:, config.WRIST], axis=1)
        signal = (win[:, config.WRIST, 0] if name.startswith("swipe")
                  else np.linalg.norm(win[:, config.THUMB_TIP] - win[:, config.INDEX_TIP],
                                      axis=1))
        change = np.abs(np.diff(signal, prepend=signal[0])) / np.nanmedian(palm)
        old = np.convolve(change, np.ones(config.CORE_SMOOTH_STEPS) / config.CORE_SMOOTH_STEPS,
                          mode="same")
        np.testing.assert_array_equal(core_signal(win, steps, name), old)


def test_may_trang_thai_la_bo_loc_fsm_cua_muc_su_kien():
    """evaluate.py --events fsm và các bảng Phase 8 dùng đúng lớp này, mỗi video
    một máy mới; bảng đánh đổi truyền thẳng một hàm tạo máy có tham số riêng."""
    assert isinstance(events.make_filter("fsm"), ActivationFSM)
    assert events.make_filter("fsm") is not events.make_filter("fsm")
    assert events.make_filter(lambda: ActivationFSM(k_of_n=(1, 1), zoom_k=1)).k == 1


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


def test_dong_thoi_gian_mang_do_manh_cua_tung_lan_du_doan(tmp_path):
    """clip_stream ghi window_strengths của từng lần dự đoán qua đúng WindowStream của
    demo: hữu hạn ở lần hợp lệ, NaN ở lần không; lưu rồi đọc lại không mất."""
    from src.windows import window_strengths
    hand = make_static(60)
    hand[20:28] = np.nan
    path = save_parts_clip(tmp_path / "c.npz", [(hand, "D0X", "none")], subject="p")
    timeline, X, F = events.clip_stream(path)
    assert (~timeline.valid).any() and timeline.valid.any()
    assert timeline.strength.shape == (timeline.ts.size, len(config.CLASSES))
    assert np.all(np.isfinite(timeline.strength[timeline.valid]))
    assert np.all(np.isnan(timeline.strength[~timeline.valid]))
    np.testing.assert_allclose(timeline.strength[timeline.valid],
                               np.array([window_strengths(x) for x in X]), rtol=1e-4,
                               atol=1e-6)
    saved = events.save_streams(tmp_path / "s.npz", [timeline], X, F)
    (loaded,), _, _ = events.load_streams(saved, windows=False)
    np.testing.assert_array_equal(loaded.strength, timeline.strength)
