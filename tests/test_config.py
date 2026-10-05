"""Kiểm thử hợp đồng của src/config.py.

Các kiểm thử này canh những giả định mà mọi phase sau đều dựa vào. Chúng chạy
được ngay khi chưa có dòng code xử lý ảnh nào.
"""

from pathlib import Path

import numpy as np
import pytest

from src import config


def test_classes_du_nam_lop_va_none_o_dau():
    """Đúng năm lớp, thứ tự cố định, ``none`` phải là chỉ số 0."""
    assert config.CLASSES == [
        "none",
        "swipe_left",
        "swipe_right",
        "zoom_in",
        "zoom_out",
    ]
    assert len(config.CLASSES) == 5
    assert config.CLASSES[0] == "none"
    assert len(set(config.CLASSES)) == 5, "có lớp bị lặp"


def test_T_la_so_nguyen_duong():
    """``T = round(WIN_SEC * HZ)`` phải ra đúng 18 bước."""
    assert config.T == round(config.WIN_SEC * config.HZ)
    assert config.T == 18
    assert isinstance(config.T, int)
    assert config.T > 0


def test_tips_du_nam_dau_ngon():
    """Năm đầu ngón, không trùng nhau, nằm trong dải 21 điểm mốc."""
    assert config.TIPS == [4, 8, 12, 16, 20]
    assert len(config.TIPS) == 5
    assert len(set(config.TIPS)) == 5
    assert all(0 <= i < 21 for i in config.TIPS)
    assert config.WRIST == 0
    assert config.MIDDLE_MCP == 9


def test_require_measured_nem_loi(monkeypatch):
    """Hằng số chưa đo phải làm chương trình dừng ngay, kèm tên phase; đã đo
    thì trả đúng giá trị. Không phụ thuộc hằng số nào hiện đã được dán."""
    for name, phase in config.MEASURED_IN_PHASE.items():
        monkeypatch.setattr(config, name, None)
        with pytest.raises(RuntimeError, match=f"Phase {phase}"):
            config.require_measured(name)

    monkeypatch.setattr(config, "SWIPE_LEFT_SIGN", -1)
    assert config.require_measured("SWIPE_LEFT_SIGN") == -1

    # IPN là chuẩn quy ước hướng, nên hằng số này có sẵn giá trị chứ không đo.
    assert config.IPN_FLIP_X in (-1, 1)
    assert "IPN_FLIP_X" not in config.MEASURED_IN_PHASE

    with pytest.raises(KeyError):
        config.require_measured("KHONG_TON_TAI")


def test_hang_so_da_do_co_gia_tri_hop_le():
    """Hằng số nào đã được dán vào config.py thì phải có giá trị dùng được."""
    if config.SWIPE_LEFT_SIGN is not None:
        assert config.SWIPE_LEFT_SIGN in (-1, 1)
    if config.AUG_NOISE_SIGMA is not None:
        assert 0 < config.AUG_NOISE_SIGMA < 1, "đơn vị là lòng bàn tay"
    for name in ("RULE_VX_HI", "RULE_DX_HI", "RULE_P_HI"):
        value = getattr(config, name)
        assert value is None or np.isfinite(value)


def test_moi_duong_dan_deu_tuong_doi_tu_ROOT():
    """Mọi hằng số kiểu Path phải nằm dưới ROOT — không đường dẫn tuyệt đối."""
    paths = {
        name: value
        for name, value in vars(config).items()
        if isinstance(value, Path) and name != "ROOT"
    }

    assert paths, "không tìm thấy hằng số đường dẫn nào"

    for name, path in paths.items():
        assert config.ROOT in path.parents, (
            f"{name} = {path} không suy ra từ ROOT"
        )

    assert config.ROOT == Path(config.__file__).resolve().parents[1]
    assert config.SRC_DIR.is_dir()
    assert config.TESTS_DIR.is_dir()
