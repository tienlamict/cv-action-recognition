"""Vòng dự đoán lúc chạy thật — mọi xử lý của ``scripts/demo.py`` nằm ở đây.

``demo.py`` chỉ nối webcam, màn hình và file log; nó không được định nghĩa hàm
xử lý nào (SPEC Phase 5). Đường đi của một frame::

    TimeBuffer.push → (mỗi STRIDE_SEC) TimeBuffer.window → normalize_window
    → window_features → mô hình                    (rules, rf)
                      → datasets.window_sequence → LSTM   (lstm)

đúng các hàm mà dữ liệu IPN đã đi qua (luật 1). Đặc trưng luôn được tính, kể
cả với LSTM: log và chế độ luyện tập cần chúng.

Phần trước mô hình nằm trong :class:`WindowStream`; đánh giá mức sự kiện của
Phase 8 (``src/events.py``) chạy video IPN qua đúng lớp đó, nên một video được
chấm như thể nó đang đi qua webcam. Sau mô hình, ``activation.ActivationFSM``
(Phase 9) biến nhãn thành lệnh — cũng là bộ lọc ``"fsm"`` của mức sự kiện.
"""

import csv
import json
import time
from collections import namedtuple
from pathlib import Path

import numpy as np

from src import config, rules
from src.buffer import TimeBuffer
from src.forest import ForestClassifier
from src.features import FEATURE_NAMES, EXTENSION_NAMES, finger_extensions, window_features
from src.preprocess import normalize_window

def make_model(name, lstm_path=None):
    """Mô hình của ``demo.py --model``: một hàm ``đầu vào → (label, confidence)``.

    ``rules`` và ``rf`` nhận vector đặc trưng. ``lstm`` nhận cửa sổ đã chuẩn hoá
    — nó khai báo ``input_kind = "window"``. ``hybrid`` (vuốt theo LSTM, zoom
    theo rừng — ``src/hybrid.py``) nhận cả hai, ``input_kind = "both"``. Thư viện
    nặng chỉ nạp khi cần: scikit-learn khi rừng nạp mô hình, torch (~3 giây) khi
    chọn ``lstm`` hay ``hybrid``.

    Args:
        lstm_path: checkpoint LSTM khác ``LSTM_MODEL_PATH`` — để so hai lần
            huấn luyện trên cùng một phiên ghi (``scripts/replay_log.py``).

    Raises:
        ValueError: tên không thuộc ``MODEL_NAMES``.
    """
    if name == "rules":
        return rules.classify
    if name == "rf":
        return ForestClassifier()
    if name == "lstm":
        from src.models import LSTMRunner
        return LSTMRunner(lstm_path)
    if name == "hybrid":
        from src.hybrid import HybridClassifier
        return HybridClassifier(lstm_path)
    raise ValueError(f"Không biết mô hình '{name}' — có: {', '.join(config.MODEL_NAMES)}")

Prediction = namedtuple("Prediction", "ts label confidence presence features win_norm",
                        defaults=(None,))
Prediction.__doc__ = """Một lần dự đoán. ``label`` là ``None`` khi không có
cửa sổ hợp lệ (chưa đủ dữ liệu, mất tay, hay đơn vị lòng bàn tay không tin
được) — màn hình hiện ``—``. ``win_norm`` là cửa sổ đã chuẩn hoá mà mô hình
vừa nhìn; màn hình luyện tập đo độ duỗi ngón trên đó."""

Sample = namedtuple("Sample", "ts win_norm presence features")
Sample.__doc__ = """Đầu vào của mô hình ở một lần dự đoán. ``win_norm`` và
``features`` là ``None`` khi không có cửa sổ hợp lệ; ``presence`` là ``None``
khi bộ đệm không trả cửa sổ nào (chưa đủ dữ liệu, mất tay quá nhiều)."""


class WindowStream:
    """Phần KHÔNG phụ thuộc mô hình của vòng dự đoán: đẩy từng frame vào, nhận
    một :class:`Sample` mỗi ``stride_sec``.

    ``TimeBuffer`` → (mỗi ``stride_sec``) ``TimeBuffer.window`` →
    ``normalize_window`` → ``window_features``.

    Args:
        stride_sec: khoảng cách giữa hai lần dự đoán.
        win_sec: độ dài cửa sổ; ``None`` là ``WIN_SEC``. Khác ``WIN_SEC`` chỉ
            ở bảng khảo sát độ dài cửa sổ (Phase 8, Bảng 3).
        min_presence: ngưỡng tỉ lệ có tay của bộ đệm; ``None`` là
            ``MIN_PRESENCE``. Khác chỉ ở bảng đánh đổi của Phase 9.
    """

    def __init__(self, stride_sec=config.STRIDE_SEC, win_sec=None, min_presence=None):
        win_sec = config.WIN_SEC if win_sec is None else win_sec
        self.stride_sec = stride_sec
        self.buffer = TimeBuffer(keep_sec=win_sec + config.BUFFER_EXTRA_SEC,
                                 steps=config.window_steps(win_sec),
                                 min_presence=min_presence)
        self._due = None

    def push(self, ts, xy_norm, w, h):
        """Đẩy một frame — frame mất tay vẫn đẩy, ``xy_norm`` toàn NaN (luật 4).

        Returns:
            :class:`Sample` nếu đã tới lượt dự đoán, ngược lại ``None``.
        """
        self.buffer.push(ts, xy_norm, w, h)
        if self._due is None:
            self._due = ts + self.stride_sec
            return None
        if ts < self._due:
            return None
        self._due += self.stride_sec * max(1, int((ts - self._due) // self.stride_sec) + 1)
        return self.sample(ts)

    def sample(self, ts):
        found = self.buffer.window()
        if found is None:
            return Sample(ts, None, None, None)
        win, presence = found
        try:
            win_norm = normalize_window(win)
        except ValueError:
            return Sample(ts, None, presence, None)
        return Sample(ts, win_norm, presence, window_features(win_norm, presence))


class LivePredictor:
    """Đẩy từng frame vào, nhận một :class:`Prediction` mỗi ``STRIDE_SEC``.

    ``model`` là hàm ``đầu vào → (label, confidence)`` của :func:`make_model`:
    nhận vector đặc trưng; hoặc cửa sổ đã chuẩn hoá nếu nó khai báo
    ``input_kind = "window"``; hoặc ``(cửa sổ, đặc trưng)`` nếu ``"both"``.

    ``last_timing`` giữ thời gian (giây) của lần ``update`` vừa rồi: ``window``
    — bộ đệm, lưới thời gian, chuẩn hoá và đặc trưng; ``model`` — mô hình. Hai
    phần này chỉ tốn đáng kể ở nhịp dự đoán (``scripts/bench.py`` đọc nó).
    """

    def __init__(self, model, stride_sec=config.STRIDE_SEC):
        self.model = model
        self.stream = WindowStream(stride_sec)
        # Mô hình nạp lười (rừng ngẫu nhiên) thì nạp NGAY bây giờ, trước khi
        # camera chạy — nạp giữa vòng lặp làm demo đứng hình ~2,7 s ở lần đầu thấy tay.
        load = getattr(model, "load", None)
        if callable(load):
            load()
        self.last_timing = {}

    def update(self, ts, xy_norm, w, h):
        """Đẩy một frame.

        Returns:
            :class:`Prediction` nếu đã tới lượt dự đoán, ngược lại ``None``.
        """
        started = time.perf_counter()
        sample = self.stream.push(ts, xy_norm, w, h)
        pushed = time.perf_counter()
        prediction = None if sample is None else self.classify(sample)
        self.last_timing = {"window": pushed - started,
                            "model": time.perf_counter() - pushed}
        return prediction

    def classify(self, sample):
        """Chạy mô hình trên một :class:`Sample`."""
        if sample.features is None:
            return Prediction(sample.ts, None, None, sample.presence, None)
        kind = getattr(self.model, "input_kind", "features")
        if kind == "both":
            label, confidence = self.model(sample.win_norm, sample.features)
        else:
            label, confidence = self.model(sample.win_norm if kind == "window"
                                           else sample.features)
        return Prediction(sample.ts, label, confidence, sample.presence,
                          sample.features, sample.win_norm)


def load_feature_ranges(path=None):
    """Phân vị 25/75 theo lớp của tập train IPN, từ Phase 4 — gồm cả độ duỗi
    các ngón của ``SHOW_FINGERS``."""
    path = path or config.IPN_FEATURE_RANGES_JSON
    rerun = "Chạy python scripts/plot_feature_boxplots.py (Phase 4)"
    if not path.is_file():
        raise FileNotFoundError(f"Chưa có {path.name}. {rerun} trước.")
    ranges = json.loads(path.read_text(encoding="utf-8"))["quartiles"]
    missing = [f"{name}/{EXTENSION_NAMES[finger]}"
               for name, fingers in config.SHOW_FINGERS.items() for finger in fingers
               if EXTENSION_NAMES[finger] not in ranges.get(name, {})]
    if missing:
        raise ValueError(f"{path.name} chưa có độ duỗi ngón ({', '.join(missing)}). "
                         f"{rerun} lại.")
    return ranges


def practice_status(features, ranges, class_name, names=config.SHOW_FEATURES):
    """So đặc trưng của cửa sổ vừa rồi với hộp 25–75 của một lớp trên IPN.

    Returns:
        list ``(tên, giá trị, p25, p75, nằm trong hộp?)`` theo thứ tự ``names``.
    """
    return _in_boxes({name: float(features[FEATURE_NAMES.index(name)]) for name in names},
                     ranges[class_name])


def finger_status(win_norm, ranges, class_name):
    """Như :func:`practice_status`, cho độ duỗi các ngón ``SHOW_FINGERS`` của
    lớp đó — nhẫn và út với hai lớp zoom; lớp khác thì rỗng."""
    return _in_boxes(finger_extensions(win_norm, config.SHOW_FINGERS.get(class_name, ())),
                     ranges[class_name])


def _in_boxes(values, boxes):
    """``(tên, giá trị, p25, p75, nằm trong hộp?)`` cho từng giá trị."""
    return [(name, value, boxes[name]["p25"], boxes[name]["p75"],
             boxes[name]["p25"] <= value <= boxes[name]["p75"])
            for name, value in values.items()]


#: Bốn lớp luyện bằng phím 1–4 trong ``--show-features``.
PRACTICE_CLASSES = [c for c in config.CLASSES if c != "none"]
NO_LABEL = "-"      # màn hình chỉ vẽ được ASCII; "—" của SPEC thành "-"

#: Phím ? của demo (SPEC Phase 10): tóm tắt docs/gestures.md cho người dùng thử.
#: Không dấu, vì cv2.putText chỉ vẽ ASCII; mỗi dòng vừa khung CAM_W.
HELP_LINES = (
    "HUONG DAN (? de dong) - lam nhu nguoi dien IPN",
    "Tay phai, truoc nguc; ban tay ~1/5 chieu cao khung",
    "swipe_left : chum dau ngon, hat ngang sang TRAI ban,",
    "             mo bung tay trong luc hat, roi giu yen",
    "swipe_right: nhu tren, hat sang PHAI cua ban",
    "zoom_in    : cai+tro+giua chum -> mo ra (hinh chu L)",
    "zoom_out   : cai+tro+giua dang mo -> chum lai",
    "             zoom: nhan, ut gap; co tay dung yen",
    "Dong tac chinh ~0.3 s, dut khoat, mot chieu",
    "KHONG lay da: dung keo tay nguoc chieu truoc khi hat",
    "KHONG: chi tro ngon, xoe ca 5 ngon, vay qua lai",
    "Ha tay ra khoi khung = huy",
    "c: bat/tat dieu khien   q: thoat",
    "Bat c xong, bam chuot vao cua so trinh chieu",
)


def help_screen():
    """Màn hình của phím ? — ``(lines, colors, big_text)`` như :func:`screen_lines`."""
    return list(HELP_LINES), [None] * len(HELP_LINES), None


def label_name(label):
    return NO_LABEL if label is None else config.CLASSES[label]


def screen_lines(prediction, fps, ranges=None, practice=None, state=None, command=None,
                 control=None):
    """Nội dung màn hình demo, toàn ASCII.

    Args:
        state: trạng thái máy kích hoạt (Phase 9); ``None`` thì không hiện.
        command: lệnh vừa phát (:func:`recent_command`); ``None`` thì không hiện.
        control: cờ điều khiển đang bật hay tắt (Phase 10); ``None`` thì không hiện.

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
    if state is not None:
        lines.append(f"state {state}")
        colors.append(None)
    if command is not None:
        lines.append(f">> COMMAND {label_name(command)}")
        colors.append(config.COLOR_ALERT)
    if control is not None:
        lines.append(f"control {'ON' if control else 'off'} ({chr(config.CTRL_TOGGLE_KEY)})"
                     "   ? help")
        colors.append(config.COLOR_ALERT if control else None)

    if ranges is not None and practice is not None:
        lines.append(f"practice [{PRACTICE_CLASSES.index(practice) + 1}] "
                     f"{practice}  (keys 1-4)")
        colors.append(None)
        if prediction is not None and prediction.features is not None:
            status = practice_status(prediction.features, ranges, practice)
            if prediction.win_norm is not None:
                status += finger_status(prediction.win_norm, ranges, practice)
            for name, value, lo, hi, ok in status:
                lines.append(f"{name:<12}{value:+7.2f}  IPN [{lo:+.2f}, {hi:+.2f}]")
                colors.append(config.COLOR_IN_RANGE if ok else config.COLOR_OUT_RANGE)
    return lines, colors, big


class CsvLog:
    """File CSV ghi từng dòng trong lúc demo chạy, dòng đầu là ``COLUMNS``."""

    COLUMNS = []

    def __init__(self, path):
        self.path = path
        self._file = open(path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(self.COLUMNS)

    def close(self):
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class PredictionLog(CsvLog):
    """Ghi mỗi lần dự đoán một dòng CSV: thời điểm, nhãn, độ tin, tỉ lệ có
    tay, ``SHOW_FEATURES``, rồi trạng thái máy kích hoạt sau lần dự đoán đó và
    lệnh nó vừa phát (Phase 9). Dùng cho bài đếm báo nhầm và Phase 10."""

    COLUMNS = ["ts", "label", "confidence", "presence", *config.SHOW_FEATURES,
               "state", "command", "sent"]

    def write(self, p, state=None, command=None, sent=None):
        """Một dòng; ``sent`` là tổ hợp phím đã gửi cho ``command`` (Phase 10),
        trống khi điều khiển đang tắt."""
        feats = ([float(p.features[FEATURE_NAMES.index(n)])
                  for n in config.SHOW_FEATURES] if p.features is not None
                 else [""] * len(config.SHOW_FEATURES))
        self._writer.writerow([f"{p.ts:.3f}", label_name(p.label),
                               "" if p.confidence is None else f"{p.confidence:.3f}",
                               "" if p.presence is None else f"{p.presence:.3f}",
                               *feats, state or "",
                               "" if command is None else label_name(command),
                               "+".join(sent or ())])


class TransitionLog(CsvLog):
    """Ghi MỌI lần chuyển trạng thái của ``ActivationFSM`` (SPEC Phase 9) — công
    cụ gỡ lỗi khi hệ thống "thỉnh thoảng phát lệnh lạ" (cẩm nang 18.4). Truyền
    :meth:`write` vào ``ActivationFSM(on_transition=...)``."""

    COLUMNS = ["ts", "from", "to", "reason"]

    def write(self, ts, previous, state, reason):
        self._writer.writerow([f"{ts:.3f}", previous, state, reason])


class LandmarkRecorder:
    """Ghi điểm mốc thô của một phiên demo, theo đúng schema của
    ``data/landmarks`` (``io_data.save_clip``, nguồn ``webcam``, không nhãn).

    Log dự đoán chỉ có vài đặc trưng; điểm mốc thì cho chạy lại CẢ phiên qua bất
    kỳ mô hình nào (``scripts/replay_log.py``) — để biết vì sao một cử chỉ không
    được nhận, và để thử cách sửa trên chính bàn tay người dùng.
    """

    def __init__(self):
        self.ts, self.xy, self.present = [], [], []
        self.w = self.h = None

    def add(self, ts, xy_norm, present, w, h):
        self.ts.append(float(ts))
        self.xy.append(np.asarray(xy_norm, dtype=np.float32).reshape(
            config.NUM_LANDMARKS, 2))
        self.present.append(bool(present))
        self.w, self.h = w, h

    def save(self, path, segments=None, src_labels=None, **meta):
        """Ghi ra ``path`` (.npz). ``ts`` dời về 0 ở frame đầu như mọi clip.

        Args:
            segments, src_labels: đoạn có nhãn ``[frame đầu, frame cuối + 1,
                lớp]`` — lời nhắc của ``bench.py record gestures``; mặc định
                không có đoạn nào.
        """
        from src.io_data import save_clip

        ts = np.asarray(self.ts, dtype=np.float64)
        info = {"w": self.w, "h": self.h, "source": "webcam", "subject": "live",
                "clip_id": Path(path).stem,
                "fps": float((len(ts) - 1) / (ts[-1] - ts[0])) if len(ts) > 1 else 0.0,
                **meta}
        segments = (np.empty((0, 3), dtype=np.int64) if segments is None
                    else np.asarray(segments, dtype=np.int64).reshape(-1, 3))
        return save_clip(path, ts - ts[0], np.stack(self.xy), self.present,
                         segments, list(src_labels or []), info)


def landmarks_path(log_path):
    """File điểm mốc đi kèm một log dự đoán: ``live.csv`` → ``live_landmarks.npz``."""
    log_path = Path(log_path)
    return log_path.with_name(f"{log_path.stem}_landmarks.npz")


def fsm_log_path(log_path):
    """File chuyển trạng thái đi kèm một log dự đoán: ``live.csv`` → ``live_fsm.csv``."""
    log_path = Path(log_path)
    return log_path.with_name(f"{log_path.stem}_fsm.csv")


def recent_command(commands, ts, keep_sec=config.DISPLAY_COMMAND_SEC):
    """Lệnh mới nhất trong ``commands`` (list ``(giây, lớp)``) nếu nó phát chưa
    quá ``keep_sec`` giây trước ``ts`` — màn hình demo hiện lệnh vừa phát."""
    if commands and ts - commands[-1][0] < keep_sec:
        return commands[-1][1]
    return None


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

