"""Kiểm thử bảng ánh xạ nhãn IPN — dùng file nhãn giả, không đụng data/ipn/."""

import numpy as np
import pytest

from src import config, ipn

# Đúng 14 lớp gốc của IPN, chép từ classIdx.txt (xem docs/ipn_format.md).
ALL_LABELS = ["D0X", "B0A", "B0B", "G01", "G02", "G03", "G04",
              "G05", "G06", "G07", "G08", "G09", "G10", "G11"]
TARGET_LABELS = {"G05": "swipe_left", "G06": "swipe_right",
                 "G10": "zoom_in", "G11": "zoom_out"}


def write_class_idx(tmp_path, labels):
    path = tmp_path / "classIdx.txt"
    lines = ["id,label"] + [f"{i},{label}" for i, label in enumerate(labels, 1)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_anh_xa_nhan_ipn_phu_het_moi_lop_goc(tmp_path):
    """Không lớp gốc nào rơi ra ngoài bảng ánh xạ."""
    assert set(ALL_LABELS) == set(ipn.CLASS_MAP), "CLASS_MAP phải phủ đúng 14 lớp"
    for label in ALL_LABELS:
        assert ipn.map_label(label) in config.CLASSES

    # File nhãn đúng 14 lớp: đọc được.
    assert set(ipn.read_class_index(write_class_idx(tmp_path, ALL_LABELS))) \
        == set(ALL_LABELS)

    # File nhãn có lớp lạ: phải DỪNG, không âm thầm bỏ qua.
    with pytest.raises(KeyError):
        ipn.read_class_index(write_class_idx(tmp_path, ALL_LABELS + ["G99"]))
    with pytest.raises(KeyError):
        ipn.map_label("G99")


def test_lop_cu_chi_khac_anh_xa_ve_none():
    """Mười lớp không dùng thành mẫu âm khó, không bị bỏ đi."""
    others = set(ALL_LABELS) - set(TARGET_LABELS)
    assert len(others) == 10
    for label in others:
        assert ipn.map_label(label) == "none", label

    for label, expected in TARGET_LABELS.items():
        assert ipn.map_label(label) == expected
        assert ipn.class_id(label) == config.CLASSES.index(expected)

    assert ipn.class_id("G03") == 0, "none luôn là chỉ số 0"


def test_doc_nhan_doi_ve_chi_so_0_based_nua_mo(tmp_path):
    """t_start 1-based và t_end THUỘC đoạn → [start-1, end) trong Python."""
    path = tmp_path / "Annot_List.txt"
    path.write_text(
        "video,label,id,t_start,t_end,frames\n"
        "v1,D0X,1,1,17,17\n"
        "v1,G11,14,18,55,38\n"
        "v2,G05,8,3,4,2\n", encoding="utf-8")

    clips = ipn.read_annotations(path)
    assert set(clips) == {"v1", "v2"}
    assert clips["v1"][0] == {"label": "D0X", "start": 0, "end": 17}
    assert clips["v1"][1] == {"label": "G11", "start": 17, "end": 55}

    segments, src_labels = ipn.segments_array(clips["v1"])
    assert segments.dtype == np.int64 and segments.shape == (2, 3)
    assert segments[1].tolist() == [17, 55, config.CLASSES.index("zoom_out")]
    assert src_labels.tolist() == ["D0X", "G11"]

    # Nhãn vượt quá số frame giải mã được thì cắt cho vừa.
    cut, _ = ipn.segments_array(clips["v1"], n_frames=20)
    assert cut[1].tolist() == [17, 20, config.CLASSES.index("zoom_out")]


def test_ma_nguoi_dien_va_split(tmp_path):
    """Mã người = hai token đầu; danh sách split phân tách bằng TAB."""
    assert ipn.subject_of("1CM1_1_R__217") == "1CM1_1"
    assert ipn.subject_of("1CM42_13_R__142") == "1CM42_13"

    train = tmp_path / "train.txt"
    test = tmp_path / "test.txt"
    train.write_text("1CM1_4_R__229\t3751\n1CM1_4_R__230\t3684\n",
                     encoding="utf-8")
    test.write_text("1CM1_1_R__217\t3855\n", encoding="utf-8")

    splits = ipn.read_video_lists(train, test)
    assert splits == {"1CM1_4_R__229": "train", "1CM1_4_R__230": "train",
                      "1CM1_1_R__217": "test"}


def test_clip_meta_danh_dau_lech_do_dai():
    """Clip lệch quá IPN_LENGTH_TOLERANCE bị đánh dấu, không bị âm thầm dùng."""
    ok = ipn.clip_meta("1CM1_1_R__217", 640, 480, 30.0, 3855,
                       expected_frames=3855, split="test")
    assert ok["length_mismatch"] is False
    assert ok["subject"] == "1CM1_1" and ok["source"] == "ipn"

    bad = ipn.clip_meta("1CM1_1_R__217", 640, 480, 30.0, 3983,
                        expected_frames=3855)
    assert bad["length_mismatch"] is True
