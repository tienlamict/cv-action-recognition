"""Kiểm thử hai script Phase 3 — không đụng tới data/ipn/."""

import numpy as np

from src import config
from src.io_data import save_clip
from tests.fixtures import make_swipe, make_zoom
from tests.scripts_import import load_script

extract = load_script("extract_landmarks")
measure = load_script("measure_direction")

FPS = 30.0
STEPS = 2 * config.T        # 36 frame ở 30 FPS -> 18 bước ở 15 Hz


def save_synthetic(path, win_pixel, label):
    """Lưu một clip tổng hợp: cả clip là một đoạn thuộc ``label``."""
    xy_norm = (win_pixel / np.array([config.CAM_W, config.CAM_H])).astype(
        np.float32)
    ts = np.arange(xy_norm.shape[0], dtype=np.float64) / FPS
    segments = np.array([[0, xy_norm.shape[0], config.CLASSES.index(label)]],
                        dtype=np.int64)
    meta = {"w": config.CAM_W, "h": config.CAM_H, "fps": FPS, "source": "ipn",
            "subject": path.stem, "clip_id": path.stem}
    save_clip(path, ts, xy_norm, np.ones(ts.size, dtype=bool), segments,
              [label], meta)


def test_extract_bo_qua_clip_da_co(tmp_path):
    """Clip đã có .npz thì không làm lại — chạy lại là tiếp tục."""
    done = tmp_path / "a.npz"
    done.write_bytes(b"")
    tasks = [{"clip_id": "a", "out": str(done)},
             {"clip_id": "b", "out": str(tmp_path / "b.npz")},
             {"clip_id": "c", "out": str(tmp_path / "c.npz")}]

    todo = extract.pending(tasks)

    assert [t["clip_id"] for t in todo] == ["b", "c"]
    assert extract.pending([]) == []
    assert extract.pending(todo) == todo, "chưa clip nào xong thì giữ nguyên"


def test_measure_direction_tren_du_lieu_tong_hop(tmp_path):
    """Trên dữ liệu tổng hợp, phép đo phải cho kết luận đúng và dứt khoát."""
    # swipe_left dựng từ chuyển động theo chiều x TĂNG; swipe_right ngược lại.
    save_synthetic(tmp_path / "s_left.npz", make_swipe(+1, steps=STEPS),
                   "swipe_left")
    save_synthetic(tmp_path / "s_right.npz", make_swipe(-1, steps=STEPS),
                   "swipe_right")
    save_synthetic(tmp_path / "z_in.npz", make_zoom("in", steps=STEPS),
                   "zoom_in")
    save_synthetic(tmp_path / "z_out.npz", make_zoom("out", steps=STEPS),
                   "zoom_out")

    values, skipped, n_clips, n_mismatched = measure.collect(
        sorted(tmp_path.glob("*.npz")), include_mismatched=False)
    summary = measure.summarize(values)
    ok, problems = measure.check(summary)

    assert n_clips == 4 and n_mismatched == 0
    assert sum(skipped.values()) == 0
    assert ok, problems

    # Hai lớp vuốt trái dấu nhau, và đây là chỗ dấu được ĐO chứ không viết cứng.
    assert summary["swipe_left"]["median_dx"] > 0
    assert summary["swipe_right"]["median_dx"] < 0
    assert summary["zoom_in"]["median_open_delta"] > 0
    assert summary["zoom_out"]["median_open_delta"] < 0


def test_measure_direction_khong_de_xuat_khi_zoom_nguoc(tmp_path):
    """Nếu zoom_in/zoom_out bị đổi chỗ trong bảng ánh xạ, phải báo và DỪNG."""
    save_synthetic(tmp_path / "s_left.npz", make_swipe(+1, steps=STEPS),
                   "swipe_left")
    save_synthetic(tmp_path / "s_right.npz", make_swipe(-1, steps=STEPS),
                   "swipe_right")
    save_synthetic(tmp_path / "z_in.npz", make_zoom("out", steps=STEPS),
                   "zoom_in")        # cố ý gán nhãn ngược
    save_synthetic(tmp_path / "z_out.npz", make_zoom("in", steps=STEPS),
                   "zoom_out")

    values, _, _, _ = measure.collect(sorted(tmp_path.glob("*.npz")), False)
    ok, problems = measure.check(measure.summarize(values))

    assert not ok
    assert any("zoom_in" in p for p in problems)


def test_measure_direction_bo_qua_clip_lech_do_dai(tmp_path):
    """Clip có length_mismatch bị loại khỏi phép đo theo mặc định."""
    path = tmp_path / "lech.npz"
    save_synthetic(path, make_swipe(+1, steps=STEPS), "swipe_left")
    with np.load(path, allow_pickle=False) as data:
        arrays = {k: data[k] for k in data.files}
    import json
    meta = json.loads(str(arrays["meta"]))
    meta["length_mismatch"] = True
    np.savez_compressed(path, **{**arrays, "meta": json.dumps(meta)})

    _, _, n_clips, n_mismatched = measure.collect([path],
                                                  include_mismatched=False)
    assert (n_clips, n_mismatched) == (0, 1)

    _, _, n_clips, _ = measure.collect([path], include_mismatched=True)
    assert n_clips == 1
