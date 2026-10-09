"""Vòng dự đoán lúc chạy thật — mọi xử lý của ``scripts/demo.py`` nằm ở đây.

``demo.py`` chỉ nối webcam, màn hình và file log; nó không được định nghĩa hàm
xử lý nào (SPEC Phase 5). Đường đi của một frame::

    TimeBuffer.push → (mỗi STRIDE_SEC) TimeBuffer.window → normalize_window
    → window_features → mô hình

đúng các hàm mà dữ liệu IPN đã đi qua (luật 1).
"""

import csv
import json
from collections import namedtuple

from src import config, rules
from src.buffer import TimeBuffer
from src.forest import ForestClassifier
from src.features import FEATURE_NAMES, window_features
from src.preprocess import normalize_window

#: Mô hình chọn bằng ``demo.py --model``: tên → hàm ``features → (label, confidence)``.
#: Rừng ngẫu nhiên nạp lười ở lần dự đoán đầu (``forest.ForestClassifier``).
MODELS = {"rules": rules.classify, "rf": ForestClassifier()}

Prediction = namedtuple("Prediction", "ts label confidence presence features")
Prediction.__doc__ = """Một lần dự đoán. ``label`` là ``None`` khi không có
cửa sổ hợp lệ (chưa đủ dữ liệu, mất tay, hay đơn vị lòng bàn tay không tin
được) — màn hình hiện ``—``."""


class LivePredictor:
    """Đẩy từng frame vào, nhận một :class:`Prediction` mỗi ``STRIDE_SEC``."""

    def __init__(self, model, stride_sec=config.STRIDE_SEC):
        self.model = model
        self.stride_sec = stride_sec
        self.buffer = TimeBuffer()
        self._due = None
        # Mô hình nạp lười (rừng ngẫu nhiên) thì nạp NGAY bây giờ, trước khi
        # camera chạy — nạp giữa vòng lặp làm demo đứng hình ~2,7 s ở lần đầu thấy tay.
        load = getattr(model, "load", None)
        if callable(load):
            load()

    def update(self, ts, xy_norm, w, h):
        """Đẩy một frame.

        Returns:
            :class:`Prediction` nếu đã tới lượt dự đoán, ngược lại ``None``.
        """
        self.buffer.push(ts, xy_norm, w, h)
        if self._due is None:
            self._due = ts + self.stride_sec
            return None
        if ts < self._due:
            return None
        self._due += self.stride_sec * max(1, int((ts - self._due) // self.stride_sec) + 1)
        return self.predict(ts)

    def predict(self, ts):
        found = self.buffer.window()
        if found is None:
            return Prediction(ts, None, None, None, None)
        win, presence = found
        try:
            win_norm = normalize_window(win)
        except ValueError:
            return Prediction(ts, None, None, presence, None)
        features = window_features(win_norm, presence)
        label, confidence = self.model(features)
        return Prediction(ts, label, confidence, presence, features)


def load_feature_ranges(path=None):
    """Phân vị 25/75 theo lớp của tập train IPN, từ Phase 4."""
    path = path or config.IPN_FEATURE_RANGES_JSON
    if not path.is_file():
        raise FileNotFoundError(
            f"Chưa có {path.name}. Chạy python scripts/plot_feature_boxplots.py "
            "(Phase 4) trước.")
    return json.loads(path.read_text(encoding="utf-8"))["quartiles"]


def practice_status(features, ranges, class_name, names=config.SHOW_FEATURES):
    """So đặc trưng của cửa sổ vừa rồi với hộp 25–75 của một lớp trên IPN.

    Returns:
        list ``(tên, giá trị, p25, p75, nằm trong hộp?)`` theo thứ tự ``names``.
    """
    out = []
    for name in names:
        value = float(features[FEATURE_NAMES.index(name)])
        box = ranges[class_name][name]
        out.append((name, value, box["p25"], box["p75"],
                    box["p25"] <= value <= box["p75"]))
    return out


#: Bốn lớp luyện bằng phím 1–4 trong ``--show-features``.
PRACTICE_CLASSES = [c for c in config.CLASSES if c != "none"]
NO_LABEL = "-"      # màn hình chỉ vẽ được ASCII; "—" của SPEC thành "-"


def label_name(label):
    return NO_LABEL if label is None else config.CLASSES[label]


def screen_lines(prediction, fps, ranges=None, practice=None):
    """Nội dung màn hình demo, toàn ASCII.

    Returns:
        ``(lines, colors, big_text)`` cho ``display.make_display``.
    """
    lines = [f"FPS {fps:5.1f}" if fps else "FPS  ..."]
    colors = [None]
    big = NO_LABEL
    if prediction is not None and prediction.label is not None:
        big = f"{label_name(prediction.label)}  {prediction.confidence:.2f}"
    if prediction is not None and prediction.presence is not None:
        lines.append(f"presence {prediction.presence:.2f}")
    else:
        lines.append("presence  -")
    colors.append(None)

    if ranges is not None and practice is not None:
        lines.append(f"practice [{PRACTICE_CLASSES.index(practice) + 1}] "
                     f"{practice}  (keys 1-4)")
        colors.append(None)
        if prediction is not None and prediction.features is not None:
            for name, value, lo, hi, ok in practice_status(
                    prediction.features, ranges, practice):
                lines.append(f"{name:<12}{value:+7.2f}  IPN [{lo:+.2f}, {hi:+.2f}]")
                colors.append(config.COLOR_IN_RANGE if ok else config.COLOR_OUT_RANGE)
    return lines, colors, big


class PredictionLog:
    """Ghi mỗi lần dự đoán một dòng CSV: thời điểm, nhãn, độ tin, tỉ lệ có
    tay, và ``SHOW_FEATURES``. Dùng cho bài đếm báo nhầm và Phase 10."""

    COLUMNS = ["ts", "label", "confidence", "presence", *config.SHOW_FEATURES]

    def __init__(self, path):
        self.path = path
        self._file = open(path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(self.COLUMNS)

    def write(self, p):
        feats = ([float(p.features[FEATURE_NAMES.index(n)])
                  for n in config.SHOW_FEATURES] if p.features is not None
                 else [""] * len(config.SHOW_FEATURES))
        self._writer.writerow([f"{p.ts:.3f}", label_name(p.label),
                               "" if p.confidence is None else f"{p.confidence:.3f}",
                               "" if p.presence is None else f"{p.presence:.3f}",
                               *feats])

    def close(self):
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def count_episodes(labels):
    """:func:`count_clusters` trên dãy nhãn dạng chỉ số lớp (``None`` = ``-``)."""
    return count_clusters([label_name(label) for label in labels])


def count_clusters(names):
    """Đếm số cụm của từng lớp: một chuỗi dự đoán LIỀN NHAU cùng lớp là một
    cụm. Nhãn nhấp nháy mỗi ``STRIDE_SEC`` là đúng khi chưa có máy trạng thái
    (Phase 9); đếm cụm xấp xỉ số lần hệ thống *sẽ* phát lệnh.

    Bất kỳ nhãn khác — kể cả ``none`` và ``-`` (không có cửa sổ hợp lệ) — đều
    cắt cụm.

    Args:
        names: dãy tên nhãn theo thời gian.

    Returns:
        dict ``{tên lớp: số cụm}`` cho bốn lớp đích.
    """
    out = {c: 0 for c in PRACTICE_CLASSES}
    previous = None
    for name in names:
        if name in out and name != previous:
            out[name] += 1
        previous = name
    return out


def read_prediction_log(path):
    """Đọc file của :class:`PredictionLog`.

    Returns:
        ``(ts (n,) float, names list)`` — tên nhãn đúng như đã ghi.
    """
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    missing = set(PredictionLog.COLUMNS[:2]) - set(rows[0] if rows else {})
    if not rows or missing:
        raise ValueError(f"{path} không phải log của demo.py (thiếu cột {missing})")
    return [float(r["ts"]) for r in rows], [r["label"] for r in rows]

