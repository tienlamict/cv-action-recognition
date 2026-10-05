"""Kiểm thử chia tập theo người — split giả, không đụng data/."""

import pytest

from src import splits as sp


def official(n_train=10, n_test=3):
    out = {f"tr{i:02d}": "train" for i in range(n_train)}
    out.update({f"te{i:02d}": "test" for i in range(n_test)})
    return out


def test_khong_ma_nguoi_nao_xuat_hien_o_hai_tap():
    """Phép giao giữa mọi cặp tập là tập rỗng; hợp lại đủ mọi người."""
    splits = sp.make_splits(official())

    names = sp.SPLIT_NAMES
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert set(splits[a]) & set(splits[b]) == set(), (a, b)
    assert set().union(*map(set, splits.values())) == set(official())

    with pytest.raises(ValueError, match="hai tập"):
        sp.check_disjoint({"train": ["x"], "val": ["x"], "test": []})


def test_val_lay_tu_train_chinh_thuc_test_giu_nguyen():
    splits = sp.make_splits(official(), val_fraction=0.2, seed=1)
    assert len(splits["val"]) == 2
    assert all(s.startswith("tr") for s in splits["val"])
    assert splits["test"] == ["te00", "te01", "te02"]
    assert splits["real_tune"] == [] and splits["real_test"] == []
    assert sp.make_splits(official(), seed=1) == splits, "cùng seed, cùng kết quả"


def test_mot_nguoi_o_ca_train_lan_test_thi_dung():
    with pytest.raises(ValueError, match="cả train lẫn test"):
        sp.official_subject_splits({"1CM1_1_R__1": "train",
                                    "1CM1_1_R__2": "test"})


def test_split_of_loc_theo_cot_subject(tmp_path):
    splits = sp.make_splits(official())
    path = sp.write_splits(splits, tmp_path / "splits.json")
    loaded = sp.read_splits(path)
    names = sp.split_of(["te01", splits["val"][0], "khong_co"], loaded)
    assert names.tolist() == ["test", "val", ""]
