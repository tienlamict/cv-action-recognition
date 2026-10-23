"""Đánh giá mức SỰ KIỆN (Phase 8): chạy hệ thống hoàn chỉnh trên các video IPN
LIÊN TỤC của một tập, rồi so chuỗi lệnh phát ra với chuỗi cử chỉ đã gán nhãn.

Vì sao cần mức này (cẩm nang mục 16.d): một cú vuốt sinh vài cửa sổ dương. Mô
hình đoán đúng cả mấy cửa sổ thì mức cửa sổ cho điểm tuyệt đối, nhưng hệ thống
phát mấy lệnh cho một cử chỉ. Hai mức có thể cho hai kết luận ngược nhau.

Đường đi của một video giống hệt webcam lúc chạy thật (luật 1)::

    load_clip → từng frame → live.WindowStream (TimeBuffer, nhịp STRIDE_SEC,
    normalize_window, window_features) → mô hình → BỘ LỌC SỰ KIỆN → lệnh

Phần trước mô hình không phụ thuộc mô hình, nên tách làm hai bước: :func:`clip_stream`
cho dòng thời gian và các cửa sổ của một video; mô hình chấm mọi cửa sổ theo lô;
:func:`evaluate_timelines` cho nhãn đó qua bộ lọc và khớp với nhãn thật.

**Bộ lọc sự kiện** chọn bằng tên trong ``EVENT_FILTERS``. Mỗi bộ lọc có
``update(label, confidence, presence, ts) → lệnh | None`` — đúng giao diện
``ActivationFSM`` của Phase 9, nên Phase 9 chỉ thêm máy trạng thái vào bảng này;
``scripts/evaluate.py`` không phải sửa. Mỗi video dùng một bộ lọc MỚI: không
trạng thái nào lọt từ video này sang video kia.

**Khớp lệnh với cử chỉ** (SPEC Phase 8, sửa 2026-10-22):

- TP — lệnh đúng loại, phát trong VÙNG KHỚP của cử chỉ. ``EVENT_MATCH = "span"``:
  từ lúc cử chỉ bắt đầu tới lúc kết thúc + ``EVENT_TOL_SEC``. ``"end"`` (định
  nghĩa ban đầu của SPEC, giữ để đối chiếu): ±``EVENT_TOL_SEC`` quanh lúc kết
  thúc. Đoạn nhãn IPN gồm cả lúc thu tay, nên lệnh đúng lúc thường phát ở giữa
  đoạn — xa lúc kết thúc hơn 1 giây (lý do đổi, ghi ở ``config.EVENT_MATCH``);
- FP — lệnh không khớp cử chỉ thật nào, GỒM CẢ lệnh thứ hai cho cùng cử chỉ;
- FN — cử chỉ thật không có lệnh nào khớp.

Thêm hai chỉ số: **số lệnh trên một cử chỉ** (lý tưởng 1,0 — mọi lệnh đúng loại
trong vùng khớp của cử chỉ) và **số lệnh nhầm mỗi phút video**. Mỗi lệnh nhầm ghi
kèm đoạn nhãn IPN đang diễn ra lúc đó, để biết LOẠI ``none`` nào gây kích hoạt
nhầm (``src_label``). Lệnh đúng loại phát trong lúc cử chỉ diễn ra nhưng SỚM hơn
vùng khớp được đếm riêng (``early``; luôn 0 với ``"span"``).
"""

import json
from collections import namedtuple

import numpy as np

from src import config
from src.features import FEATURE_NAMES

NONE = 0
#: Chỉ số bốn lớp cử chỉ — những lớp duy nhất thành lệnh.
GESTURES = tuple(range(1, len(config.CLASSES)))


class RawFilter:
    """Không có tầng kích hoạt: MỖI lần dự đoán ra cử chỉ là một lệnh. Cho
    thấy đúng vấn đề mà Phase 9 phải giải — một cú vuốt thành vài lệnh."""

    def update(self, label, confidence, presence, ts):
        return int(label) if label in GESTURES else None


class EdgeFilter:
    """Lệnh ở lần dự đoán ĐẦU của mỗi chuỗi dự đoán liền nhau cùng một lớp cử
    chỉ — cách đếm cụm của ``summarize_log.py``, xấp xỉ tốt nhất khi chưa có
    máy trạng thái. Nhãn nhấp nháy (vuốt, none, vuốt) vẫn thành hai lệnh."""

    def __init__(self):
        self.previous = None

    def update(self, label, confidence, presence, ts):
        command = int(label) if label in GESTURES and label != self.previous else None
        self.previous = label
        return command


#: Tên → lớp bộ lọc; ``evaluate.py --events`` nhận các tên này. Phase 9 thêm
#: ``"fsm"`` (``ActivationFSM``) vào đây.
EVENT_FILTERS = {"raw": RawFilter, "edge": EdgeFilter}


def make_filter(name):
    """Một bộ lọc MỚI — gọi một lần cho mỗi video."""
    if name not in EVENT_FILTERS:
        raise ValueError(f"Không có bộ lọc sự kiện '{name}' — có: "
                         f"{', '.join(EVENT_FILTERS)}")
    return EVENT_FILTERS[name]()


Timeline = namedtuple("Timeline",
                      "clip subject ts presence valid duration gestures spans")
Timeline.__doc__ = """Một video đã chạy qua ``WindowStream``, chưa qua mô hình.

- ``ts`` ``(m,)``: thời điểm của từng lần dự đoán (cuối cửa sổ — nhân quả);
- ``presence`` ``(m,)``: tỉ lệ bước có tay, NaN khi bộ đệm không trả cửa sổ;
- ``valid`` ``(m,)`` bool: có cửa sổ chuẩn hoá được — mô hình chỉ chạy ở đó;
- ``duration``: giây;
- ``gestures``: list ``(lớp, giây đầu, giây cuối, nhãn gốc)`` của các đoạn cử
  chỉ đích;
- ``spans``: list ``(giây đầu, giây cuối, lớp, nhãn gốc)`` của MỌI đoạn có nhãn.
"""


def clip_meta(path):
    """``meta`` của một clip, không nạp điểm mốc."""
    with np.load(path, allow_pickle=False) as data:
        return json.loads(str(data["meta"]))


def clip_paths(subjects, landmarks_dir=None):
    """Video IPN của các người ``subjects``, theo thứ tự tên file. Bỏ video lệch
    nhãn (``length_mismatch``) như ``build_dataset.py``.

    Returns:
        ``(paths, skipped)`` — ``skipped`` là ``clip_id`` các video bị bỏ.
    """
    landmarks_dir = landmarks_dir or config.LANDMARKS_DIR / "ipn"
    subjects = set(map(str, subjects))
    paths, skipped = [], []
    for path in sorted(landmarks_dir.glob("*.npz")):
        meta = clip_meta(path)
        if str(meta["subject"]) not in subjects:
            continue
        if meta.get("length_mismatch"):
            skipped.append(meta["clip_id"])
        else:
            paths.append(path)
    return paths, skipped


def clip_segments(ts, segments, src_labels):
    """Đoạn nhãn của một video theo GIÂY.

    Returns:
        ``(gestures, spans)`` như trong :class:`Timeline`. Đoạn ``[start, end)``
        theo chỉ số frame; giây cuối là của frame cuối thuộc đoạn.
    """
    spans = []
    for (start, end, cls), src in zip(np.asarray(segments).reshape(-1, 3), src_labels):
        last = min(int(end), len(ts)) - 1
        if last < int(start):
            continue
        spans.append((float(ts[int(start)]), float(ts[last]), int(cls), str(src)))
    gestures = [(cls, a, b, src) for a, b, cls, src in spans if cls != NONE]
    return gestures, spans


def clip_stream(path, win_sec=None):
    """Chạy một video qua ``live.WindowStream`` — đúng như frame từ webcam.

    Args:
        win_sec: độ dài cửa sổ; ``None`` là ``WIN_SEC`` (Bảng 3 của Phase 8
            dùng giá trị khác).

    Returns:
        ``(timeline, X, F)`` — ``X`` ``(k, T, 21, 2)`` float32 và ``F``
        ``(k, 15)`` float32 là cửa sổ đã chuẩn hoá và đặc trưng của ``k`` lần
        dự đoán hợp lệ, theo thứ tự thời gian.
    """
    from src.io_data import load_clip
    from src.live import WindowStream

    ts, xy, w, h, segments, src_labels, meta = load_clip(path)
    stream = WindowStream(win_sec=win_sec)
    times, presence, valid, X, F = [], [], [], [], []
    for t, frame in zip(ts, xy):
        sample = stream.push(float(t), frame, w, h)
        if sample is None:
            continue
        times.append(sample.ts)
        presence.append(np.nan if sample.presence is None else sample.presence)
        valid.append(sample.features is not None)
        if sample.features is not None:
            X.append(sample.win_norm)
            F.append(sample.features)
    gestures, spans = clip_segments(ts, segments, src_labels)
    steps = config.window_steps(config.WIN_SEC if win_sec is None else win_sec)
    timeline = Timeline(str(meta["clip_id"]), str(meta["subject"]),
                        np.asarray(times, dtype=np.float64),
                        np.asarray(presence, dtype=np.float64),
                        np.asarray(valid, dtype=bool),
                        float(ts[-1] - ts[0]) if len(ts) else 0.0, gestures, spans)
    X = np.asarray(X, dtype=np.float32).reshape(-1, steps, config.NUM_LANDMARKS, 2)
    F = np.asarray(F, dtype=np.float32).reshape(-1, len(FEATURE_NAMES))
    return timeline, X, F


def clip_streams(paths, win_sec=None):
    """:func:`clip_stream` cho nhiều video; cửa sổ và đặc trưng nối liền theo
    thứ tự video.

    Returns:
        ``(timelines, X, F)``.
    """
    timelines, Xs, Fs = [], [], []
    for path in paths:
        timeline, X, F = clip_stream(path, win_sec)
        timelines.append(timeline)
        Xs.append(X)
        Fs.append(F)
    if not timelines:
        steps = config.window_steps(config.WIN_SEC if win_sec is None else win_sec)
        return ([], np.empty((0, steps, config.NUM_LANDMARKS, 2), np.float32),
                np.empty((0, len(FEATURE_NAMES)), np.float32))
    return timelines, np.concatenate(Xs), np.concatenate(Fs)


def save_streams(path, timelines, X, F):
    """Ghi kết quả của :func:`clip_streams` ra một ``.npz`` không cần pickle —
    để các tiến trình thí nghiệm của Phase 8 không phải chạy lại video."""
    sizes = [t.ts.size for t in timelines]
    segments = [{"gestures": t.gestures, "spans": t.spans} for t in timelines]
    np.savez(path, X=X, F=F,
             clip=np.array([t.clip for t in timelines], dtype="<U64"),
             subject=np.array([t.subject for t in timelines], dtype="<U16"),
             duration=np.array([t.duration for t in timelines], dtype=np.float64),
             offsets=np.concatenate([[0], np.cumsum(sizes)]).astype(np.int64),
             ts=np.concatenate([t.ts for t in timelines]) if timelines else np.empty(0),
             presence=(np.concatenate([t.presence for t in timelines])
                       if timelines else np.empty(0)),
             valid=(np.concatenate([t.valid for t in timelines])
                    if timelines else np.empty(0, dtype=bool)),
             segments=json.dumps(segments, ensure_ascii=False))
    return path


def load_streams(path, windows=True):
    """Đọc file của :func:`save_streams`.

    Args:
        windows: ``False`` thì không nạp ``X`` (nặng) — đủ để chấm lại các dự
            đoán đã có.

    Returns:
        ``(timelines, X, F)`` — ``X`` là ``None`` khi ``windows=False``.
    """
    with np.load(path, allow_pickle=False) as data:
        segments = json.loads(str(data["segments"]))
        offsets, ts, presence, valid = (data[k] for k in ("offsets", "ts", "presence",
                                                           "valid"))
        timelines = [
            Timeline(str(clip), str(subject), ts[a:b], presence[a:b], valid[a:b],
                     float(duration),
                     [tuple(g) for g in seg["gestures"]], [tuple(s) for s in seg["spans"]])
            for clip, subject, duration, a, b, seg in zip(
                data["clip"], data["subject"], data["duration"], offsets[:-1],
                offsets[1:], segments)]
        return timelines, (data["X"] if windows else None), data["F"]


def scatter(timelines, labels, confidences):
    """Nhãn và độ tin của các lần dự đoán HỢP LỆ (nối liền theo thứ tự video)
    → mảng đủ dài cho từng video: nhãn ``-1`` và độ tin NaN ở lần không hợp lệ.

    Returns:
        ``(labels list, confidences list)`` — mỗi video một mảng ``(m,)``.
    """
    labels, confidences = np.asarray(labels), np.asarray(confidences, dtype=np.float64)
    expected = sum(int(t.valid.sum()) for t in timelines)
    if labels.size != expected or confidences.size != expected:
        raise ValueError(f"Cần {expected} dự đoán hợp lệ, nhận {labels.size}")
    out_labels, out_conf, k = [], [], 0
    for timeline in timelines:
        n = int(timeline.valid.sum())
        lab = np.full(timeline.ts.size, -1, dtype=np.int64)
        conf = np.full(timeline.ts.size, np.nan)
        lab[timeline.valid] = labels[k:k + n]
        conf[timeline.valid] = confidences[k:k + n]
        out_labels.append(lab)
        out_conf.append(conf)
        k += n
    return out_labels, out_conf


def commands(timeline, labels, confidences, filter_name=config.EVENT_FILTER):
    """Chuỗi lệnh của một video: mọi lần dự đoán (kể cả không hợp lệ — nhãn
    ``None``) lần lượt qua một bộ lọc MỚI.

    Returns:
        list ``(giây, lớp)``.
    """
    event_filter = make_filter(filter_name)
    out = []
    for t, label, confidence, presence in zip(timeline.ts, labels, confidences,
                                              timeline.presence):
        valid = int(label) >= 0
        command = event_filter.update(
            int(label) if valid else None,
            float(confidence) if valid else None,
            None if np.isnan(presence) else float(presence), float(t))
        if command is not None:
            out.append((float(t), int(command)))
    return out


def match_window(gesture, tol=config.EVENT_TOL_SEC, mode=config.EVENT_MATCH):
    """Vùng khớp ``(từ giây, tới giây)`` của một cử chỉ ``(lớp, đầu, cuối, nhãn
    gốc)``: ``"span"`` là ``[đầu, cuối + tol]``, ``"end"`` là ``[cuối − tol,
    cuối + tol]``."""
    _, start, end, _ = gesture
    if mode == "span":
        return start, end + tol
    if mode == "end":
        return end - tol, end + tol
    raise ValueError(f"Không có cách khớp '{mode}' — có: {config.EVENT_MATCH_MODES}")


def match(cmds, gestures, tol=config.EVENT_TOL_SEC, mode=config.EVENT_MATCH):
    """Khớp lệnh với cử chỉ của MỘT video.

    Mỗi cử chỉ (theo thứ tự lúc kết thúc) nhận lệnh SỚM NHẤT chưa dùng, đúng
    loại, trong vùng khớp của nó (:func:`match_window`). Lệnh không được nhận là
    FP — kể cả lệnh thứ hai cho cùng cử chỉ.

    Returns:
        dict ``tp`` (list ``(lệnh, cử chỉ)``), ``fp`` (list lệnh), ``fn`` (list
        cử chỉ), ``in_tol`` (mỗi cử chỉ: số lệnh đúng loại trong vùng khớp),
        ``early`` (mỗi cử chỉ: số lệnh đúng loại phát trong lúc cử chỉ diễn ra
        nhưng sớm hơn vùng khớp).
    """
    windows = [match_window(g, tol, mode) for g in gestures]
    used, tp = set(), []
    for j in sorted(range(len(gestures)), key=lambda j: gestures[j][2]):
        cls, (lo, hi) = gestures[j][0], windows[j]
        found = [i for i, (t, c) in enumerate(cmds)
                 if c == cls and lo <= t <= hi and i not in used]
        if found:
            i = min(found, key=lambda i: cmds[i][0])
            used.add(i)
            tp.append((i, j))
    matched = {j for _, j in tp}
    return {
        "tp": tp,
        "fp": [i for i in range(len(cmds)) if i not in used],
        "fn": [j for j in range(len(gestures)) if j not in matched],
        "in_tol": [sum(c == g[0] and lo <= t <= hi for t, c in cmds)
                   for g, (lo, hi) in zip(gestures, windows)],
        "early": [sum(c == g[0] and g[1] <= t < lo for t, c in cmds)
                  for g, (lo, _) in zip(gestures, windows)],
    }


def false_kind(t, command, timeline, tol=config.EVENT_TOL_SEC):
    """Lệnh nhầm ở giây ``t`` rơi vào lúc nào.

    Returns:
        ``(loại, nhãn gốc)`` — loại là ``"cùng cử chỉ"`` (lệnh thừa hoặc quá
        sớm cho một cử chỉ đúng loại), ``"cử chỉ khác"`` (đang có cử chỉ đích
        khác loại — nhầm lớp), hay ``"none"`` (không có cử chỉ đích nào; nhãn
        gốc là của đoạn IPN đang diễn ra, ``""`` nếu ngoài mọi đoạn).
    """
    around = [g for g in timeline.gestures if g[1] <= t <= g[2] + tol]
    for cls, _, _, src in around:
        if cls == command:
            return "cùng cử chỉ", src
    if around:
        return "cử chỉ khác", around[0][3]
    covering = [s for s in timeline.spans if s[0] <= t <= s[1]]
    return "none", covering[0][3] if covering else ""


def evaluate_timelines(timelines, labels, confidences, filter_name=config.EVENT_FILTER,
                       tol=config.EVENT_TOL_SEC, mode=config.EVENT_MATCH):
    """Mức sự kiện của cả một tập video.

    Args:
        labels, confidences: mỗi video một mảng ``(m,)`` như :func:`scatter`.
        mode: cách khớp, xem :func:`match_window`.

    Returns:
        list kết quả từng video — đưa vào :func:`summarize_events`.
    """
    results = []
    for timeline, lab, conf in zip(timelines, labels, confidences):
        cmds = commands(timeline, lab, conf, filter_name)
        matched = match(cmds, timeline.gestures, tol, mode)
        false = [(cmds[i][0], cmds[i][1], *false_kind(cmds[i][0], cmds[i][1],
                                                      timeline, tol))
                 for i in matched["fp"]]
        results.append({"clip": timeline.clip, "subject": timeline.subject,
                        "duration": timeline.duration, "gestures": timeline.gestures,
                        "commands": cmds, "match": matched, "false": false,
                        "filter": filter_name, "tol": tol, "mode": mode})
    return results


def _prf(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def summarize_events(results):
    """Gộp kết quả các video thành các chỉ số mức sự kiện.

    Returns:
        dict: ``filter``, ``n_clips``, ``minutes``, ``n_gestures``,
        ``n_commands``, ``tp``/``fp``/``fn``, ``precision``/``recall``/``f1``
        gộp bốn lớp, ``macro_f1`` (trung bình F1 bốn lớp), ``cmds_per_gesture``,
        ``early_per_gesture``, ``false_per_min`` (lệnh nhầm mỗi phút video);
        ``per_class`` — một dòng mỗi lớp cử chỉ; ``false_by_src`` — lệnh nhầm
        theo loại và nhãn gốc, nhiều nhất trước.
    """
    minutes = sum(r["duration"] for r in results) / 60
    rows, in_tol_total = [], 0
    for cls in GESTURES:
        name = config.CLASSES[cls]
        n_g = tp = fn = fp = in_tol = early = n_cmd = 0
        for r in results:
            gestures, m, cmds = r["gestures"], r["match"], r["commands"]
            own = [j for j, g in enumerate(gestures) if g[0] == cls]
            n_g += len(own)
            tp += sum(gestures[j][0] == cls for _, j in m["tp"])
            fn += sum(gestures[j][0] == cls for j in m["fn"])
            fp += sum(cmds[i][1] == cls for i in m["fp"])
            n_cmd += sum(c == cls for _, c in cmds)
            in_tol += sum(m["in_tol"][j] for j in own)
            early += sum(m["early"][j] for j in own)
        precision, recall, f1 = _prf(tp, fp, fn)
        in_tol_total += in_tol
        rows.append({"class": name, "n_gestures": n_g, "n_commands": n_cmd,
                     "tp": tp, "fp": fp, "fn": fn, "precision": precision,
                     "recall": recall, "f1": f1,
                     "cmds_per_gesture": in_tol / n_g if n_g else float("nan"),
                     "early": early})
    tp, fp, fn = (sum(r[k] for r in rows) for k in ("tp", "fp", "fn"))
    precision, recall, f1 = _prf(tp, fp, fn)
    n_gestures = sum(r["n_gestures"] for r in rows)

    false = {}
    for r in results:
        for _, command, kind, src in r["false"]:
            row = false.setdefault((kind, src), {"kind": kind, "src_label": src, "n": 0,
                                                 **{config.CLASSES[c]: 0 for c in GESTURES}})
            row["n"] += 1
            row[config.CLASSES[command]] += 1
    false_rows = sorted(false.values(), key=lambda r: (-r["n"], r["kind"], r["src_label"]))
    for row in false_rows:
        row["per_min"] = row["n"] / minutes if minutes else float("nan")

    first = results[0] if results else {}
    return {"filter": first.get("filter"), "tol": first.get("tol"),
            "mode": first.get("mode"),
            "n_clips": len(results), "minutes": minutes, "n_gestures": n_gestures,
            "n_commands": sum(r["n_commands"] for r in rows),
            "tp": tp, "fp": fp, "fn": fn, "precision": precision,
            "recall": recall, "f1": f1,
            "macro_f1": float(np.mean([r["f1"] for r in rows])),
            "cmds_per_gesture": in_tol_total / n_gestures if n_gestures else float("nan"),
            "early_per_gesture": (sum(r["early"] for r in rows) / n_gestures
                                  if n_gestures else float("nan")),
            "false_per_min": fp / minutes if minutes else float("nan"),
            "per_class": rows, "false_by_src": false_rows}
