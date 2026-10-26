"""Bảy bảng khảo sát của Phase 8, cộng bảng phụ — trên val hoặc k-fold của người
train + val, KHÔNG BAO GIỜ trên test (luật 13).

  Bảng 1  so sánh mô hình: luật, rừng, LSTM, ghép — mô hình ĐÃ LƯU của demo
  Bảng 2  chuẩn hoá: gốc cổ tay từng frame so với gốc cổ tay frame đầu
  Bảng 3  độ dài cửa sổ EXP_WIN_SECS
  Bảng 4  cách chia tập: theo người so với ngẫu nhiên theo cửa sổ (đo rò rỉ)
  Bảng 5  loại bỏ đặc trưng, và vòng cải tiến: ô lớn nhất ngoài đường chéo
  Bảng 6  năm seed EXP_SEEDS: trung bình ± độ lệch chuẩn
  Bảng 7  k-fold theo nhóm người, EXP_FOLDS fold; LSTM học đúng EXP_KFOLD_EPOCHS epoch
  phụ     11 điểm, GRU, hidden, cách gộp, tăng cường, biên khoảnh khắc chính, quota none

Mỗi hàng đổi ĐÚNG MỘT yếu tố so với cấu hình chính (src/experiments.py). Mỗi
bảng có hai mức: cửa sổ (macro-F1, F1 từng lớp) và sự kiện (cả hệ thống chạy
trên video liên tục, bộ lọc EVENT_FILTER, vùng khớp EVENT_MATCH — src/events.py).
So sánh nào có chênh lệch nhỏ hơn độ lệch chuẩn giữa năm seed của Bảng 6 được
ghi "không đủ bằng chứng để kết luận".

Cách chạy: dựng dữ liệu cho từng biến thể (data/experiments/, một lần); học rừng
ngay trong tiến trình này; học LSTM ở --jobs tiến trình song song, mỗi tiến
trình EXP_TORCH_THREADS luồng (kết quả không đổi theo số luồng). Mỗi thí nghiệm
ghi một bản ghi — mọi xác suất dự đoán — vào results/phase8/records/; chạy lại
thì bản ghi còn khớp spec, hằng số và dữ liệu được dùng lại, không học lại.
Bảng ra results/phase8/experiments/run_NN/.

Ví dụ:
    python scripts/run_experiments.py                  # đủ bảy bảng và bảng phụ
    python scripts/run_experiments.py --tables 1 5     # vài bảng
    python scripts/run_experiments.py --list           # thí nghiệm và trạng thái
    python scripts/run_experiments.py --jobs 2
    python scripts/run_experiments.py --max-epochs 2 --records <tạm> --out <tạm>   # chạy thử
"""

import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src import config  # noqa: E402
from src import experiments as ex  # noqa: E402
from src.cli import make_parser, setup_console  # noqa: E402
from src.runlog import next_run_dir, relative_to_root, write_manifest  # noqa: E402
from src.splits import read_splits, subject_folds  # noqa: E402
from src.tables import write_table  # noqa: E402

GESTURE_NAMES = config.CLASSES[1:]
SWIPES, ZOOMS = ("swipe_left", "swipe_right"), ("zoom_in", "zoom_out")
F1_COLUMNS = [f"f1_{c}" for c in config.CLASSES]
EVENT_COLUMNS = ["event_f1", "event_precision", "event_recall", "cmds_per_gesture",
                 "false_per_min"]
MODEL_LABELS = {"rules": "luật", "rf": "rừng ngẫu nhiên", "lstm": "LSTM",
                "hybrid": "ghép (vuốt LSTM, zoom rừng)"}
ALL_TABLES = ("1", "2", "3", "4", "5", "6", "7", "extra")


# --------------------------------------------------------------------------
# Thí nghiệm và bảng
# --------------------------------------------------------------------------

def registry():
    """Mọi thí nghiệm: tên → phần spec khác cấu hình chính."""
    from src.models import POOLINGS

    exps = {}
    for model in ("rf", "lstm"):
        base = {"model": model}
        exps[f"{model}_base"] = base
        exps[f"{model}_per_frame"] = {**base, "origin": "per_frame"}
        for win in config.EXP_WIN_SECS:
            if win != config.WIN_SEC:
                exps[f"{model}_win{win:g}"] = {**base, "win_sec": win}
        exps[f"{model}_leaky"] = {**base, "split": "leaky"}
        for seed in config.EXP_SEEDS:
            if seed != config.SEED:
                exps[f"{model}_seed{seed}"] = {**base, "seed": seed}
        for fold in range(1, config.EXP_FOLDS + 1):
            exps[f"{model}_fold{fold}"] = {
                **base, "split": "fold", "fold": fold,
                **({"epochs": config.EXP_KFOLD_EPOCHS} if model == "lstm" else {})}
        for margin in config.EXP_CORE_MARGINS:
            if margin != config.CORE_MARGIN_STEPS:
                exps[f"{model}_margin{margin}"] = {**base, "margin": margin}
        exps[f"{model}_quota_natural"] = {**base, "quota": "natural"}
    for features in ("no_signed", "no_straightness", "no_presence", "angles"):
        exps[f"rf_{features}"] = {"model": "rf", "features": features}
    lstm = {"model": "lstm"}
    exps["lstm_reduced"] = {**lstm, "landmarks": "reduced"}
    exps["lstm_gru"] = {**lstm, "cell": "gru"}
    for hidden in config.EXP_HIDDENS:
        if hidden != config.LSTM_HIDDEN:
            exps[f"lstm_hidden{hidden}"] = {**lstm, "hidden": hidden}
    for pooling in POOLINGS:
        if pooling != config.LSTM_POOLING:
            exps[f"lstm_pool_{pooling}"] = {**lstm, "pooling": pooling}
    exps["lstm_no_augment"] = {**lstm, "augment": False}
    exps["lstm_zoom_style"] = {**lstm, "zoom_style_p": config.EXP_ZOOM_STYLE_P}
    exps["lstm_static"] = {**lstm, "static_share": config.EXP_STATIC_SHARE}
    return exps


def seed_names(model):
    return [f"{model}_base" if s == config.SEED else f"{model}_seed{s}"
            for s in config.EXP_SEEDS]


def fold_names(model):
    return [f"{model}_fold{k}" for k in range(1, config.EXP_FOLDS + 1)]


def win_names(model):
    return [f"{model}_base" if w == config.WIN_SEC else f"{model}_win{w:g}"
            for w in config.EXP_WIN_SECS]


def margin_names(model):
    return [f"{model}_margin{m}" for m in config.EXP_CORE_MARGINS
            if m != config.CORE_MARGIN_STEPS]


EXTRA_LABELS = {
    "lstm_base": "cơ sở LSTM: 21 điểm, LSTM, hidden 128, gộp last, có tăng cường",
    "lstm_reduced": "11 điểm rút gọn (REDUCED_LANDMARKS)",
    "lstm_gru": "GRU thay LSTM",
    "lstm_no_augment": "không tăng cường",
    "lstm_zoom_style": f"thêm đổi dáng ngón phụ, p = {config.EXP_ZOOM_STYLE_P:g}",
    "lstm_static": f"thêm bàn tay đứng yên, {config.EXP_STATIC_SHARE:g} × train",
    "lstm_quota_natural": "quota none theo tỉ lệ tự nhiên",
    "rf_base": "cơ sở rừng: 15 đặc trưng, biên 3, quota đều",
    "rf_quota_natural": "quota none theo tỉ lệ tự nhiên",
}


def extra_names():
    from src.models import POOLINGS

    lstm = (["lstm_base", "lstm_reduced", "lstm_gru"]
            + [f"lstm_hidden{h}" for h in config.EXP_HIDDENS if h != config.LSTM_HIDDEN]
            + [f"lstm_pool_{p}" for p in POOLINGS if p != config.LSTM_POOLING]
            + ["lstm_no_augment", "lstm_zoom_style", "lstm_static"]
            + margin_names("lstm") + ["lstm_quota_natural"])
    return lstm + ["rf_base"] + margin_names("rf") + ["rf_quota_natural"]


def extra_label(name):
    if name in EXTRA_LABELS:
        return EXTRA_LABELS[name]
    if "_hidden" in name:
        return f"hidden {name.split('hidden')[1]}"
    if "_pool_" in name:
        return f"gộp {name.split('_pool_')[1]}"
    if "_margin" in name:
        return (f"biên khoảnh khắc chính {name.split('margin')[1]} bước "
                "(nhãn val đổi theo — so mức sự kiện)")
    return name


def table_experiments(table):
    """Thí nghiệm mà một bảng cần (Bảng 1 dùng mô hình đã lưu, không thí nghiệm)."""
    return {
        "1": [],
        "2": ["rf_base", "rf_per_frame", "lstm_base", "lstm_per_frame"],
        "3": win_names("rf") + win_names("lstm"),
        "4": ["rf_base", "rf_leaky", "lstm_base", "lstm_leaky"],
        "5": ["rf_base", "rf_no_signed", "rf_no_straightness", "rf_no_presence",
              "rf_angles"],
        "6": seed_names("rf") + seed_names("lstm"),
        "7": fold_names("rf") + fold_names("lstm"),
        "extra": extra_names(),
    }[table]


# --------------------------------------------------------------------------
# Chạy
# --------------------------------------------------------------------------

def same_values(a, b):
    """Hai mảng trùng nhau, kể cả NaN ở đúng chỗ NaN. Bước mất tay của cửa sổ
    là NaN (luật 4), mà NaN != NaN, nên ``np.array_equal`` trơn báo khác cả khi
    trùng từng bit. Cột chuỗi không nhận ``equal_nan`` — cờ chỉ bật cho số thực."""
    a, b = np.asarray(a), np.asarray(b)
    return bool(np.array_equal(a, b, equal_nan=a.dtype.kind == b.dtype.kind == "f"))


def check_against_windows_npz(data_fp):
    """Bộ cửa sổ dựng lại với cấu hình chính phải trùng ``windows.npz`` từng bit
    — bằng chứng các bảng khảo sát đi đúng đường ống của build_dataset.py."""
    data = ex.load_set(ex.prepare_set(ex.full_spec({}), data_fp))
    splits = read_splits()
    with np.load(config.WINDOWS_NPZ, allow_pickle=False) as npz:
        from src.splits import split_of
        part = split_of(npz["subject"], splits)
        checks = {}
        for name, suffix in (("train", "tr"), ("val", "va")):
            pick = part == name
            for key, ours in (("X", "X"), ("y", "y"), ("presence", "pres"),
                              ("subject", "subj"), ("clip", "clip"), ("t0", "t0")):
                checks[f"{name}.{key}"] = same_values(npz[key][pick],
                                                      data[f"{ours}_{suffix}"])
    return all(checks.values()), checks


def prepare_data(names, specs, data_fp, pool):
    """Dựng mọi bộ cửa sổ (tiến trình này, nhóm theo kho cửa sổ để dùng lại) và
    mọi dòng thời gian video (song song) mà các thí nghiệm cần."""
    sets = {}
    for name in names:
        sets.setdefault(ex.set_path(specs[name], data_fp), specs[name])
    for path, spec in sorted(sets.items(), key=lambda kv: (kv[1]["win_sec"],
                                                           kv[1]["margin"])):
        if not path.is_file():
            started = time.perf_counter()
            ex.prepare_set(spec, data_fp)
            print(f"  bộ cửa sổ {path.name}: {time.perf_counter() - started:.0f} s",
                  flush=True)
    splits = read_splits()
    streams = {}
    for name in names:
        path = ex.stream_path(specs[name], splits, data_fp)
        if path is not None and not path.is_file():
            streams.setdefault(path, specs[name])
    futures = {pool.submit(ex.prepare_stream, spec, data_fp): path
               for path, spec in streams.items()}
    for future in as_completed(futures):
        future.result()
        print(f"  dòng thời gian video {futures[future].name}", flush=True)


def run_all(todo, specs, data_fp, record_dir, pool, threads):
    """LSTM chạy song song trong ``pool``; trong lúc đó rừng chạy ngay ở đây."""
    failed = {}
    futures = {pool.submit(ex.run_experiment, name, specs[name], data_fp, record_dir,
                           threads): name
               for name in todo if specs[name]["model"] == "lstm"}
    for name in [n for n in todo if specs[n]["model"] == "rf"]:
        try:
            ex.run_experiment(name, specs[name], data_fp, record_dir)
        except Exception as error:      # một thí nghiệm hỏng không dừng cả loạt
            failed[name] = repr(error)
            print(f"[{name}] LỖI: {error!r}", flush=True)
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as error:
            failed[futures[future]] = repr(error)
            print(f"[{futures[future]}] LỖI: {error!r}", flush=True)
    return failed


# --------------------------------------------------------------------------
# Bảng 1: mô hình đã lưu của demo
# --------------------------------------------------------------------------

def model_files(model):
    from src.forest import file_sha256
    files = {"rf": [config.RF_MODEL_PATH], "lstm": [config.LSTM_MODEL_PATH],
             "hybrid": [config.LSTM_MODEL_PATH, config.RF_MODEL_PATH]}.get(model, [])
    return {p.name: file_sha256(p) for p in files}


def inference_ms(model_name, X, F, n=config.TIMING_WINDOWS):
    """Trung vị thời gian một lần gọi mô hình của demo trên MỘT cửa sổ, ms —
    đúng cách demo gọi; không gồm chuẩn hoá và đặc trưng (chung cho mọi mô hình)."""
    from src.live import make_model

    model = make_model(model_name)
    load = getattr(model, "load", None)
    if callable(load):
        load()
    kind = getattr(model, "input_kind", "features")
    pick = np.linspace(0, len(X) - 1, min(n, len(X))).astype(int)

    def call(i):
        if kind == "both":
            return model(X[i].astype(np.float64), F[i])
        return model(X[i].astype(np.float64) if kind == "window" else F[i])

    call(pick[0])                       # lần đầu nạp/khởi động, không tính
    times = []
    for i in pick:
        started = time.perf_counter()
        call(i)
        times.append(time.perf_counter() - started)
    return float(np.median(times) * 1000)


def production_record(model, data_fp, record_dir):
    """Bản ghi của mô hình ĐÃ LƯU ``model`` trên val: nhãn và độ tin mức cửa sổ
    (windows.npz) và mức sự kiện (video val), cộng thời gian suy luận."""
    import json

    from src.evaluation import label_confidence, split_features
    from src.events import load_streams

    name = f"prod_{model}"
    key = ex.fingerprint([model, model_files(model), ex.relevant_config(), data_fp])
    json_path, npz_path = ex.record_paths(name, record_dir)
    if json_path.is_file() and npz_path.is_file():
        if json.loads(json_path.read_text(encoding="utf-8")).get("key") == key:
            return name
    splits = read_splits()
    with np.load(config.WINDOWS_NPZ, allow_pickle=False) as data:
        F, y, pick = split_features(data["X"], data["y"], data["presence"],
                                    data["subject"], splits, "val")
        X = data["X"][pick]
        extra = {f"{k}_va": data[c][pick] for k, c in (("src", "src_label"),
                                                       ("subj", "subject"),
                                                       ("clip", "clip"), ("t0", "t0"))}
    labels, conf, details = label_confidence(model, F, X)
    stream = ex.stream_path(ex.full_spec({}), splits, data_fp)
    _, X_st, F_st = load_streams(stream)
    labels_st, conf_st, _ = label_confidence(model, F_st, X_st)
    ms = inference_ms(model, X, F)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(npz_path, labels_va=labels, conf_va=conf, y_va=y, labels_stream=labels_st,
             conf_stream=conf_st, **extra)
    json_path.write_text(json.dumps({
        "name": name, "key": key, "stream": stream.name, "model": model,
        "details": details, "inference_ms": ms, "files": model_files(model),
        "spec": {"model": model}}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")
    print(f"[{name}] xong — {ms:.2f} ms mỗi cửa sổ", flush=True)
    return name


# --------------------------------------------------------------------------
# Chỉ số
# --------------------------------------------------------------------------

@lru_cache(maxsize=None)
def timelines_of(stream_name):
    from src.events import load_streams
    return load_streams(config.EXP_DATA_DIR / stream_name, windows=False)[0]


class Results:
    """Bản ghi → chỉ số, nhớ lại để mỗi bản ghi chỉ chấm một lần."""

    def __init__(self, record_dir):
        self.record_dir = record_dir
        self._cache = {}

    def exists(self, name):
        return all(p.is_file() for p in ex.record_paths(name, self.record_dir))

    def predictions(self, name):
        """``(meta, arrays)``; ``hybrid:<rừng>+<lstm>`` ghép hai bản ghi."""
        if name.startswith("hybrid:"):
            from src.hybrid import hybrid_predict
            rf_name, lstm_name = name[len("hybrid:"):].split("+")
            rf_meta, rf = ex.load_record(rf_name, self.record_dir)
            lstm_meta, lstm = ex.load_record(lstm_name, self.record_dir)
            if rf_meta.get("stream") != lstm_meta.get("stream"):
                raise ValueError(f"{rf_name} và {lstm_name} chấm trên hai tập video khác nhau")
            arrays = {k: rf[k] for k in ("y_va", "src_va", "subj_va")}
            for part in ("va", "stream"):
                if f"proba_{part}" in rf:
                    labels, conf = hybrid_predict(lstm[f"proba_{part}"], rf[f"proba_{part}"])
                    arrays[f"labels_{part}"], arrays[f"conf_{part}"] = labels, conf
            return {**lstm_meta, "name": name}, arrays
        return ex.load_record(name, self.record_dir)

    def metrics(self, name, subject=None):
        """Chỉ số phẳng của một bản ghi: mức cửa sổ và mức sự kiện; ``subject``
        thì chỉ tính trên cửa sổ và video của người đó."""
        if (name, subject) in self._cache:
            return self._cache[(name, subject)]
        meta, arrays = self.predictions(name)
        labels, _ = ex.predictions(arrays, "va")
        pick = (np.ones(labels.size, bool) if subject is None
                else arrays["subj_va"] == subject)
        out = ex.window_metrics(arrays["y_va"][pick], labels[pick], arrays["src_va"][pick])
        out["meta"] = meta
        if meta.get("stream"):
            timelines = timelines_of(meta["stream"])
            st_labels, st_conf = ex.predictions(arrays, "stream")
            if subject is not None:
                keep, k = [], 0
                for t in timelines:
                    n = int(t.valid.sum())
                    keep.append(np.full(n, t.subject == subject))
                    k += n
                keep = np.concatenate(keep)
                timelines = [t for t in timelines if t.subject == subject]
                st_labels, st_conf = st_labels[keep], st_conf[keep]
            summary, _ = ex.event_metrics(timelines, st_labels, st_conf)
            out.update(event_f1=summary["f1"], event_precision=summary["precision"],
                       event_recall=summary["recall"],
                       cmds_per_gesture=summary["cmds_per_gesture"],
                       false_per_min=summary["false_per_min"],
                       event_summary=summary,
                       **{f"event_f1_{r['class']}": r["f1"] for r in summary["per_class"]})
            if subject is None:
                end, _ = ex.event_metrics(timelines, st_labels, st_conf, mode="end")
                raw, _ = ex.event_metrics(timelines, st_labels, st_conf, "raw")
                out.update(event_f1_end=end["f1"],
                           raw_cmds_per_gesture=raw["cmds_per_gesture"],
                           raw_false_per_min=raw["false_per_min"])
        self._cache[(name, subject)] = out
        return out


def pick(metrics, columns):
    return {c: metrics.get(c, float("nan")) for c in columns}


def mean_of(values, keys):
    return float(np.mean([values[k] for k in keys]))


def seed_stats(results, model):
    """Trung bình và độ lệch chuẩn (mẫu, ddof = 1) giữa năm seed của Bảng 6,
    cho macro-F1 và event-F1. ``None`` khi chưa đủ bản ghi."""
    names = seed_names(model) if model != "hybrid" else [
        f"hybrid:{r}+{lstm}" for r, lstm in zip(seed_names("rf"), seed_names("lstm"))]
    needed = names if model != "hybrid" else seed_names("rf") + seed_names("lstm")
    if not all(results.exists(n) for n in needed):
        return None
    out = {}
    for key in ("macro_f1", "event_f1"):
        values = np.array([results.metrics(n).get(key, np.nan) for n in names])
        out[key] = (float(np.mean(values)), float(np.std(values, ddof=1)))
    return out


def std_of(stats, model, key):
    return None if stats.get(model) is None else stats[model][key][1]


def confusion_cells(cm):
    return {"lr_swaps": int(cm[1, 2] + cm[2, 1]), "inout_swaps": int(cm[3, 4] + cm[4, 3]),
            "none_to_swipe": int(cm[0, 1] + cm[0, 2]), "swipe_to_none": int(cm[1, 0] + cm[2, 0])}


# --------------------------------------------------------------------------
# Dựng từng bảng: mỗi hàm trả về (hàng, cột, ghi chú)
# --------------------------------------------------------------------------

def table1(results, run_dir):
    """Bảng 1 và các bảng, hình đi kèm."""
    from src.evaluation import false_alarm_rows
    from src.viz import plot_confusion, plot_per_class_f1

    rows, f1s, none_rows, false_rows = [], {}, {}, {}
    for model in config.MODEL_NAMES:
        name = f"prod_{model}"
        m = results.metrics(name)
        meta, arrays = results.predictions(name)
        cm = m["confusion"]
        rows.append({"model": MODEL_LABELS[model], **pick(m, ["macro_f1", *F1_COLUMNS,
                                                             "none_alarm"]),
                     **pick(m, EVENT_COLUMNS), "event_f1_end": m["event_f1_end"],
                     "raw_cmds_per_gesture": m["raw_cmds_per_gesture"],
                     "raw_false_per_min": m["raw_false_per_min"],
                     "inference_ms": meta["inference_ms"]})
        f1s[model] = [m[f"f1_{c}"] for c in config.CLASSES]
        totals = cm.sum(axis=1, keepdims=True)
        plot_confusion(cm, np.divide(cm, totals, out=np.zeros(cm.shape), where=totals > 0),
                       config.CLASSES, run_dir / f"table1_confusion_{model}.png",
                       title=f"{MODEL_LABELS[model]} — tập val ({int(cm.sum())} cửa sổ)")
        labels, _ = ex.predictions(arrays, "va")
        for r in false_alarm_rows(arrays["y_va"], labels, arrays["src_va"]):
            row = none_rows.setdefault(r["src_label"], {"src_label": r["src_label"],
                                                        "n_windows": r["n_windows"]})
            row[f"rate_{model}"] = r["rate"]
        for r in m["event_summary"]["false_by_src"]:
            row = false_rows.setdefault((r["kind"], r["src_label"]),
                                        {"kind": r["kind"], "src_label": r["src_label"]})
            row[f"per_min_{model}"] = r["per_min"]
    plot_per_class_f1(f1s, config.CLASSES, run_dir / "table1_per_class_f1.png",
                      title="F1 từng lớp trên tập val — mức cửa sổ")
    none_rows = sorted(none_rows.values(), key=lambda r: -r["n_windows"])
    write_table(none_rows, ["src_label", "n_windows",
                            *(f"rate_{m}" for m in config.MODEL_NAMES)],
                run_dir / "table1_none_by_src")
    false_rows = sorted(false_rows.values(),
                        key=lambda r: -max(v for k, v in r.items() if k.startswith("per_min")))
    write_table(false_rows, ["kind", "src_label",
                             *(f"per_min_{m}" for m in config.MODEL_NAMES)],
                run_dir / "table1_false_by_src")
    columns = ["model", "macro_f1", *F1_COLUMNS, "none_alarm", *EVENT_COLUMNS,
               "event_f1_end", "raw_cmds_per_gesture", "raw_false_per_min",
               "inference_ms"]
    notes = [f"Mức sự kiện: bộ lọc '{config.EVENT_FILTER}', vùng khớp "
             f"'{config.EVENT_MATCH}'; event_f1_end theo vùng khớp ban đầu của SPEC "
             "(±1 s quanh lúc kết thúc); raw_* là khi không có tầng kích hoạt nào.",
             f"Máy trạng thái: CONF_FIRE {config.CONF_FIRE:g}, K_OF_N "
             f"{config.K_OF_N[0]}/{config.K_OF_N[1]}, CONF_HOLD {config.CONF_HOLD:g}, "
             f"COOLDOWN_SEC {config.COOLDOWN_SEC:g} — áp cho cột mức sự kiện của mọi bảng.",
             "Bảng này chấm mô hình ĐÃ LƯU của demo; LSTM và mô hình ghép dùng "
             f"{relative_to_root(config.LSTM_MODEL_PATH)}. Bảng 2–7 học lại theo công "
             "thức chính của config, không dùng file đó.",
             "inference_ms: trung vị một lần gọi mô hình của demo trên một cửa sổ "
             f"({platform.processor() or platform.machine()}, "
             f"{os.cpu_count()} luồng logic)."]
    return rows, columns, notes


def compare_rows(results, stats, names, base_of, columns, key="macro_f1"):
    """Hàng của một bảng so sánh: chỉ số, chênh lệch so với hàng cơ sở của
    cùng mô hình, và kết luận theo độ lệch chuẩn của Bảng 6."""
    rows = []
    for name, label in names:
        m = results.metrics(name)
        model = m["meta"]["spec"]["model"]
        base = results.metrics(base_of[model])
        delta = m.get(key, np.nan) - base.get(key, np.nan)
        row = {"model": MODEL_LABELS[model], "variant": label, **pick(m, columns),
               **confusion_cells(m["confusion"]), f"delta_{key}": delta,
               "verdict": "(hàng cơ sở)" if name == base_of[model]
               else ex.verdict(delta, std_of(stats, model, key))}
        train = m["meta"].get("train", {})
        if train.get("best_epoch") is not None:
            row["best_epoch"] = train["best_epoch"]
        rows.append(row)
    return rows


BASE_OF = {"rf": "rf_base", "lstm": "lstm_base"}


def table2(results, stats):
    names = [("rf_base", "gốc cổ tay frame đầu"), ("rf_per_frame", "gốc cổ tay từng frame"),
             ("lstm_base", "gốc cổ tay frame đầu"), ("lstm_per_frame", "gốc cổ tay từng frame")]
    columns = ["macro_f1", *F1_COLUMNS, "event_f1"]
    rows = compare_rows(results, stats, names, BASE_OF, columns)
    return rows, ["model", "variant", *columns, "lr_swaps", "swipe_to_none",
                  "delta_macro_f1", "verdict", "best_epoch"], [
        "lr_swaps: số cửa sổ vuốt bị đoán ngược hướng; swipe_to_none: cửa sổ vuốt bị "
        "đoán none. Đơn vị giữ lòng bàn tay frame đầu ở cả hai hàng — chỉ gốc toạ độ đổi."]


def table3(results, stats):
    rows = []
    for model in ("rf", "lstm"):
        base = results.metrics(BASE_OF[model])
        for name, win in zip(win_names(model), config.EXP_WIN_SECS):
            m = results.metrics(name)
            delta = m["event_f1"] - base["event_f1"]
            rows.append({"model": MODEL_LABELS[model], "win_sec": win,
                         "n_windows": m["n_windows"], "macro_f1": m["macro_f1"],
                         "f1_swipes": mean_of(m, [f"f1_{c}" for c in SWIPES]),
                         "f1_zooms": mean_of(m, [f"f1_{c}" for c in ZOOMS]),
                         "event_f1": m["event_f1"],
                         "event_f1_swipes": mean_of(m, [f"event_f1_{c}" for c in SWIPES]),
                         "event_f1_zooms": mean_of(m, [f"event_f1_{c}" for c in ZOOMS]),
                         "cmds_per_gesture": m["cmds_per_gesture"],
                         "false_per_min": m["false_per_min"], "delta_event_f1": delta,
                         "verdict": "(hàng cơ sở)" if win == config.WIN_SEC
                         else ex.verdict(delta, std_of(stats, model, "event_f1"))})
    return rows, list(rows[0]), [
        "Đổi độ dài cửa sổ thì đổi cả tập cửa sổ val (số cửa sổ, nhãn), nên macro-F1 "
        "mức cửa sổ của các hàng không cùng một tập; mức sự kiện chấm trên CÙNG các "
        "video val nên so được trực tiếp — kết luận dựa trên event_f1."]


def table4(results, stats):
    rows = []
    for model in ("rf", "lstm"):
        for name, label in ((BASE_OF[model], "theo người (split chính thức)"),
                            (f"{model}_leaky", "ngẫu nhiên theo cửa sổ (rò rỉ)")):
            m = results.metrics(name)
            base = results.metrics(BASE_OF[model])
            delta = m["macro_f1"] - base["macro_f1"]
            info = m["meta"].get("set_info", {})
            rows.append({"model": MODEL_LABELS[model], "split": label,
                         "n_train": info.get("n_train"), "n_val": info.get("n_val"),
                         **pick(m, ["macro_f1", *F1_COLUMNS]), "delta_macro_f1": delta,
                         "verdict": "(hàng cơ sở)" if name == BASE_OF[model]
                         else ex.verdict(delta, std_of(stats, model, "macro_f1"))})
    return rows, list(rows[0]), [
        "Hàng thứ ba — tập tự quay, điều kiện thật — chỉ có nếu bật Phase 11 (chưa bật).",
        "Hàng rò rỉ chia NGẪU NHIÊN THEO CỬA SỔ kho cửa sổ của người train + val, phân "
        "tầng theo lớp với đúng số cửa sổ mỗi lớp của val theo người; train lấy mẫu con "
        "none như cấu hình chính. Không có mức sự kiện: tập đánh giá không phải một nhóm "
        "video."]


def table5(results, stats):
    base = results.metrics("rf_base")
    cm = base["confusion"].copy()
    np.fill_diagonal(cm, -1)
    i, j = np.unravel_index(np.argmax(cm), cm.shape)
    cell = f"{config.CLASSES[i]} → {config.CLASSES[j]}"
    names = [("rf_base", "đủ 15 đặc trưng"),
             ("rf_no_signed", "bỏ nhóm có dấu (" + ", ".join(config.SIGNED_FEATURES) + ")"),
             ("rf_no_straightness", "bỏ straightness"), ("rf_no_presence", "bỏ presence"),
             ("rf_angles", "thêm 10 đặc trưng góc khớp")]
    columns = ["macro_f1", *F1_COLUMNS, "none_alarm", "alarm_B0A", "alarm_B0B",
               "event_f1", "false_per_min"]
    rows = compare_rows(results, stats, names, BASE_OF, columns)
    for row, (name, _) in zip(rows, names):
        m = results.metrics(name)
        row["n_features"] = m["meta"]["train"].get("n_features")
        row["largest_cell"] = int(m["confusion"][i, j])
    return rows, ["variant", "n_features", *columns, "lr_swaps", "inout_swaps",
                  "none_to_swipe", "largest_cell", "delta_macro_f1", "verdict"], [
        f"Vòng cải tiến: ô lớn nhất ngoài đường chéo của rừng cơ sở là {cell} "
        f"({int(base['confusion'][i, j])} cửa sổ); cột largest_cell là ô đó ở mỗi hàng."]


def table6(results, stats):
    rows = []
    for model in ("rf", "lstm", "hybrid"):
        if model == "hybrid":
            names = [f"hybrid:{r}+{lstm}" for r, lstm in zip(seed_names("rf"),
                                                            seed_names("lstm"))]
        else:
            names = seed_names(model)
        metrics = [results.metrics(n) for n in names]
        for seed, m in zip(config.EXP_SEEDS, metrics):
            rows.append({"model": MODEL_LABELS[model], "seed": seed,
                         **pick(m, ["macro_f1", *F1_COLUMNS, *EVENT_COLUMNS]),
                         "best_epoch": "" if model == "hybrid" else
                         m["meta"].get("train", {}).get("best_epoch", "")})
        for label, fn in (("trung bình", np.mean),
                          ("độ lệch chuẩn", lambda v: np.std(v, ddof=1))):
            rows.append({"model": MODEL_LABELS[model], "seed": label,
                         **{c: float(fn([m[c] for m in metrics]))
                            for c in ["macro_f1", *F1_COLUMNS, *EVENT_COLUMNS]}})
    compare = []
    for a, b in (("lstm", "rf"), ("hybrid", "lstm"), ("hybrid", "rf")):
        for key in ("macro_f1", "event_f1"):
            (mean_a, std_a), (mean_b, std_b) = stats[a][key], stats[b][key]
            compare.append({"so_sánh": f"{MODEL_LABELS[a]} − {MODEL_LABELS[b]}",
                            "metric": key, "mean_a": mean_a, "mean_b": mean_b,
                            "delta": mean_a - mean_b, "std": max(std_a, std_b),
                            "verdict": ex.verdict(mean_a - mean_b, max(std_a, std_b))})
    return rows, ["model", "seed", "macro_f1", *F1_COLUMNS, *EVENT_COLUMNS,
                  "best_epoch"], compare


def table7(results):
    splits = read_splits()
    folds = subject_folds(ex.pool_subjects(splits), config.EXP_FOLDS)
    rows, by_subject = [], {}
    for model in ("rf", "lstm", "hybrid"):
        names = (fold_names(model) if model != "hybrid" else
                 [f"hybrid:{r}+{lstm}" for r, lstm in zip(fold_names("rf"),
                                                          fold_names("lstm"))])
        metrics = []
        for k, name in enumerate(names):
            m = results.metrics(name)
            metrics.append(m)
            rows.append({"model": MODEL_LABELS[model], "fold": k + 1,
                         "subjects": " ".join(folds[k]), "n_windows": m["n_windows"],
                         **pick(m, ["macro_f1", *EVENT_COLUMNS])})
            for subject in folds[k]:
                s = results.metrics(name, subject)
                row = by_subject.setdefault(subject, {"subject": subject, "fold": k + 1,
                                                      "n_windows": s["n_windows"]})
                row[f"macro_f1_{model}"] = s["macro_f1"]
                row[f"event_f1_{model}"] = s.get("event_f1", float("nan"))
        for label, fn in (("trung bình", np.mean), ("độ lệch chuẩn",
                                                    lambda v: np.std(v, ddof=1)),
                          ("thấp nhất", np.min), ("cao nhất", np.max)):
            rows.append({"model": MODEL_LABELS[model], "fold": label,
                         **{c: float(fn([m[c] for m in metrics]))
                            for c in ["macro_f1", *EVENT_COLUMNS]}})
    subject_rows = sorted(by_subject.values(), key=lambda r: (r["fold"], r["subject"]))
    return rows, ["model", "fold", "subjects", "n_windows", "macro_f1", *EVENT_COLUMNS], \
        subject_rows


def table_extra(results, stats):
    rows = []
    for name in extra_names():
        m = results.metrics(name)
        model = m["meta"]["spec"]["model"]
        base = results.metrics(BASE_OF[model])
        d_window = m["macro_f1"] - base["macro_f1"]
        d_event = m["event_f1"] - base["event_f1"]
        is_base = name == BASE_OF[model]
        rows.append({"model": MODEL_LABELS[model], "variant": extra_label(name),
                     **pick(m, ["macro_f1", *F1_COLUMNS, "none_alarm", "alarm_B0A",
                                "alarm_B0B", *EVENT_COLUMNS]),
                     "delta_macro_f1": d_window,
                     "verdict_window": "(hàng cơ sở)" if is_base else (
                         "(nhãn val khác — xem mức sự kiện)" if "_margin" in name
                         else ex.verdict(d_window, std_of(stats, model, "macro_f1"))),
                     "delta_event_f1": d_event,
                     "verdict_event": "(hàng cơ sở)" if is_base
                     else ex.verdict(d_event, std_of(stats, model, "event_f1")),
                     "best_epoch": m["meta"].get("train", {}).get("best_epoch", "")})
    return rows, list(rows[0]), [
        "Mỗi hàng đổi đúng một yếu tố so với hàng cơ sở cùng mô hình, một seed; kết "
        "luận so chênh lệch với độ lệch chuẩn giữa năm seed của Bảng 6."]


# --------------------------------------------------------------------------
# Ghi và in
# --------------------------------------------------------------------------

def write_with_notes(rows, columns, stem, notes):
    """Bảng .csv + .md; ``.md`` có thêm các dòng ghi chú bên dưới."""
    _, md = write_table(rows, columns, stem)
    if notes:
        with open(md, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(f"- {line}" for line in notes) + "\n")
    return md


def print_table(title, rows, columns, width=11):
    print(f"\n{title}")
    shown = [c for c in columns if any(c in r for r in rows)]
    print("  " + "".join(f"{c[:width]:>{width + 1}}" for c in shown))
    for r in rows:
        cells = []
        for c in shown:
            v = r.get(c, "")
            text = f"{v:.3f}" if isinstance(v, float) else str(v)
            cells.append(f"{text[:width]:>{width + 1}}")
        print("  " + "".join(cells))


def main():
    setup_console()
    parser = make_parser(__doc__)
    parser.add_argument("--tables", nargs="+", default=list(ALL_TABLES), choices=ALL_TABLES)
    parser.add_argument("--only", nargs="+", default=None, metavar="TÊN",
                        help="chỉ chạy các thí nghiệm này (xem --list), không dựng bảng")
    parser.add_argument("--jobs", type=int, default=config.EXP_JOBS,
                        help="số tiến trình LSTM song song (mặc định %(default)s)")
    parser.add_argument("--max-epochs", type=int, default=None,
                        help="giới hạn epoch của mọi LSTM — chỉ để chạy thử")
    parser.add_argument("--records", default=config.EXP_RECORD_DIR,
                        help="thư mục bản ghi (mặc định %(default)s)")
    parser.add_argument("--out", default=config.PHASE8_RESULTS_DIR / "experiments",
                        help="thư mục chứa run_NN của các bảng (mặc định %(default)s) "
                             "— lần chạy thử nên ghi ra chỗ khác")
    parser.add_argument("--list", action="store_true", help="liệt kê thí nghiệm và trạng thái")
    args = parser.parse_args()
    record_dir = Path(args.records)
    threads = config.EXP_TORCH_THREADS

    exps = registry()
    if args.only:
        unknown = sorted(set(args.only) - set(exps))
        if unknown:
            raise SystemExit(f"Không có thí nghiệm {unknown} — xem --list")
        names = list(dict.fromkeys(args.only))
    else:
        names = list(dict.fromkeys(n for t in args.tables for n in table_experiments(t)))
        # Năm seed của Bảng 6 cho độ lệch chuẩn mà các bảng khác dùng để kết luận
        if any(t not in ("1", "7") for t in args.tables):
            for model in sorted({exps[n]["model"] for n in names}):
                names += [n for n in seed_names(model) if n not in names]
    specs = {}
    for name in names:
        spec = dict(exps[name])
        if args.max_epochs and spec.get("model") == "lstm":
            spec["max_epochs"] = args.max_epochs
        specs[name] = ex.full_spec(spec)
    data_fp = ex.data_fingerprint()
    todo = [n for n in names if not ex.has_record(n, specs[n], data_fp, record_dir)]

    if args.list:
        for name in registry():
            state = ("chưa cần" if name not in specs else
                     "chưa chạy" if name in todo else "có bản ghi")
            print(f"  {name:<22}{state}")
        return

    target = "được chọn" if args.only else f"cần cho bảng {', '.join(args.tables)}"
    print(f"{len(names)} thí nghiệm {target}; {len(todo)} chưa có bản ghi "
          f"({sum(specs[n]['model'] == 'lstm' for n in todo)} LSTM).")
    # Tiến trình con thừa hưởng môi trường: một luồng mỗi thư viện, và in được
    # tiếng Việt kể cả khi stdout chuyển hướng vào file.
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[var] = str(threads)
    os.environ["PYTHONIOENCODING"] = "utf-8"
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        print("Dựng dữ liệu cho các biến thể:", flush=True)
        default = "1" in args.tables and not args.only
        # cả thí nghiệm đã có bản ghi: bảng cần dòng thời gian video của nó
        prepare_data(names + (["rf_base"] if default else []),
                     {**specs, "rf_base": ex.full_spec({"model": "rf"})}, data_fp, pool)
        failed = run_all(todo, specs, data_fp, record_dir, pool, threads)
    if default:
        for model in config.MODEL_NAMES:
            production_record(model, data_fp, record_dir)
    print(f"\nChạy xong sau {(time.perf_counter() - started) / 60:.1f} phút.")
    if failed:
        print("Thí nghiệm lỗi:", failed)
    if args.only:
        return

    same, checks = check_against_windows_npz(data_fp)
    print("Bộ cửa sổ dựng lại với cấu hình chính "
          + ("TRÙNG windows.npz từng bit." if same else f"KHÁC windows.npz: {checks}"))

    results = Results(record_dir)
    stats = {m: seed_stats(results, m) for m in ("rf", "lstm", "hybrid")}
    run_dir = next_run_dir(args.out)
    written = {}
    for table in args.tables:
        missing = [n for n in table_experiments(table) if not results.exists(n)]
        if table == "1":
            missing = [m for m in config.MODEL_NAMES if not results.exists(f"prod_{m}")]
        if missing:
            print(f"\nBảng {table}: thiếu bản ghi {missing} — bỏ qua.")
            continue
        if table == "1":
            rows, columns, notes = table1(results, run_dir)
            stem, title = "table1_models", "Bảng 1 — so sánh mô hình (val)"
        elif table == "6":
            rows, columns, compare = table6(results, stats)
            notes = [f"{r['so_sánh']}, {r['metric']}: {r['delta']:+.4f} "
                     f"(độ lệch chuẩn {r['std']:.4f}) — {r['verdict']}" for r in compare]
            write_table(compare, list(compare[0]), run_dir / "table6_compare")
            stem, title = "table6_seeds", "Bảng 6 — năm seed (val)"
        elif table == "7":
            rows, columns, subject_rows = table7(results)
            write_table(subject_rows, list(subject_rows[0]), run_dir / "table7_by_subject")
            notes = [f"Fold là nhóm người (subject_folds, seed {config.SEED}); LSTM học "
                     f"đúng {config.EXP_KFOLD_EPOCHS} epoch, không chọn gì trên fold giữ lại.",
                     "Bảng theo từng người: table7_by_subject."]
            stem, title = "table7_kfold", "Bảng 7 — k-fold theo nhóm người"
        else:
            builder = {"2": table2, "3": table3, "4": table4, "5": table5,
                       "extra": table_extra}[table]
            rows, columns, notes = builder(results, stats)
            stem = {"2": "table2_normalization", "3": "table3_window_length",
                    "4": "table4_split", "5": "table5_features",
                    "extra": "table_extra"}[table]
            title = {"2": "Bảng 2 — chuẩn hoá", "3": "Bảng 3 — độ dài cửa sổ",
                     "4": "Bảng 4 — cách chia tập", "5": "Bảng 5 — loại bỏ đặc trưng",
                     "extra": "Bảng phụ"}[table]
        write_with_notes(rows, columns, run_dir / stem, notes)
        written[table] = stem
        print_table(title, rows, columns)
        for line in notes:
            print(f"  - {line}")

    import torch
    write_manifest(run_dir, {
        "script": "run_experiments", "tables": written, "experiments": {
            n: {"spec": specs[n], "key": ex.record_key(specs[n], data_fp)} for n in names},
        "data_fingerprint": data_fp, "records": relative_to_root(record_dir),
        "matches_windows_npz": same, "windows_npz_checks": checks,
        "failed": failed, "jobs": args.jobs, "torch_threads_per_job": threads,
        "max_epochs_override": args.max_epochs,
        "machine": {"processor": platform.processor(), "cpu_count": os.cpu_count(),
                    "platform": platform.platform(), "torch": torch.__version__,
                    "torch_threads_main": torch.get_num_threads()},
        "seed_stats": stats})
    print(f"\nBảng: {relative_to_root(run_dir)}")


if __name__ == "__main__":
    main()
