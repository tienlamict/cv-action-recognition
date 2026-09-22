"""Kiểm thử ghi CSV điểm mốc — dùng tracker giả, không cần camera."""

import csv

import numpy as np

from src import config
from src.hands import empty_landmarks
from src.recording import CSV_COLUMNS, read_frames_csv, record_session

# Tay xuất hiện, mất, rồi quay lại — có cả đoạn mất dài hơn một frame.
PRESENCE = [True, True, False, False, False, True, False, True]
FPS = 15.0
W, H = 64, 48


class FakeTracker:
    """Trả về tay theo PRESENCE, lần lượt từng frame."""

    def __init__(self, presence):
        self._presence = iter(presence)

    def process(self, frame_bgr, ts_ms):
        if next(self._presence):
            xy = np.linspace(0.1, 0.9, config.NUM_LANDMARKS * 2,
                             dtype=np.float32).reshape(-1, 2)
            return xy, True, 0.9, "Right"
        return empty_landmarks(), False, float("nan"), ""


def fake_frames(n):
    black = np.zeros((H, W, 3), dtype=np.uint8)
    for i in range(n):
        yield black, i / FPS


def test_record_csv_giu_dong_khi_mat_tay(tmp_path):
    """Mỗi frame một dòng; frame mất tay vẫn có dòng, toạ độ để trống."""
    csv_path = tmp_path / "landmarks.csv"
    stats = record_session(fake_frames(len(PRESENCE)), FakeTracker(PRESENCE),
                           csv_path, show=False)

    assert stats["n_frames"] == len(PRESENCE)
    assert stats["n_present"] == sum(PRESENCE)

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0].keys()) == CSV_COLUMNS
    assert len(rows) == len(PRESENCE), "số dòng phải bằng số frame"

    for row, present in zip(rows, PRESENCE):
        assert row["ts"] != "", "mọi dòng đều có mốc thời gian"
        assert row["present"] == ("1" if present else "0")
        coords = [row[c] for c in CSV_COLUMNS if c[0] in "xy" and c[1:].isdigit()]
        if present:
            assert all(v != "" for v in coords)
        else:
            assert all(v == "" for v in coords)

    data = read_frames_csv(csv_path)
    assert data["xy"].shape == (len(PRESENCE), config.NUM_LANDMARKS, 2)
    np.testing.assert_array_equal(data["present"], PRESENCE)
    assert np.all(np.isnan(data["xy"][~data["present"]]))
    assert np.all(np.isfinite(data["xy"][data["present"]]))
    np.testing.assert_allclose(data["ts"], np.arange(len(PRESENCE)) / FPS,
                               atol=1e-6)
