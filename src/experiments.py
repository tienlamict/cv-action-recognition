"""Thí nghiệm của các bảng khảo sát Phase 8 — mỗi thí nghiệm đổi ĐÚNG MỘT yếu tố
so với cấu hình chính (cẩm nang mục 17: "mỗi dòng đổi đúng một yếu tố").

Một thí nghiệm là một dict ``spec``, phần nào không ghi lấy theo
:data:`DEFAULT_SPEC` — tức cấu hình chính của dự án. :func:`run_experiment` dựng
dữ liệu, học một mô hình (rừng hoặc LSTM), dự đoán trên tập đánh giá ở cả hai
mức, rồi ghi MỌI xác suất dự đoán vào một bản ghi trên đĩa. Bảng được dựng từ
bản ghi (:func:`record_metrics`), nên đổi cách tính chỉ số — hay cắm máy trạng
thái của Phase 9 vào mức sự kiện — không phải học lại.

Ba quy tắc an toàn:

- **Không bao giờ chạm test.** Mọi tập đều dựng từ người của train và val
  (:func:`pool_subjects`) — kể cả k-fold và phép chia rò rỉ của Bảng 4.
- **Cùng một đường ống** (luật 1): cửa sổ qua ``windows.collect_windows`` và
  ``splits.subsample_none`` như ``build_dataset.py`` — với cấu hình mặc định, bộ
  dựng lại trùng ``windows.npz`` từng bit (``scripts/run_experiments.py`` kiểm
  tra); video qua ``events.clip_streams``, tức ``live.WindowStream`` của demo;
  rừng qua ``forest.train_forest``; LSTM qua ``training.train_lstm`` — đúng
  quy trình của ``train_lstm.py``.
- **Bản ghi gắn với dấu vân tay** của spec, của hằng số trong ``config.py`` và
  của dữ liệu. Đổi bất kỳ thứ gì trong đó thì bản ghi cũ không được dùng lại.

Phép chia ngẫu nhiên theo cửa sổ (:func:`leaky_split`) là phép chia mà luật 8
cấm. Nó chỉ tồn tại để Bảng 4 đo rò rỉ lớn tới đâu (người dùng duyệt
2026-10-22), không bao giờ dùng để chọn hay huấn luyện mô hình nào khác.
"""

import hashlib
import json
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np

from src import config
from src.features import ANGLE_NAMES, FEATURE_NAMES, angle_features, window_features
from src.splits import (equal_quota, proportional_quota, read_splits, split_of,
                        subject_folds, subsample_none)
from src.variants import landmark_columns, per_frame_origin
from src.windows import collect_windows

#: Cấu hình chính của dự án. Một spec chỉ ghi phần khác đi.
DEFAULT_SPEC = {
    "model": "rf",              # rf | lstm
    "seed": config.SEED,
    "win_sec": config.WIN_SEC,  # Bảng 3
    "margin": config.CORE_MARGIN_STEPS,     # bảng phụ
    "split": "official",        # official | leaky (Bảng 4) | fold (Bảng 7)
    "fold": None,               # 1..EXP_FOLDS khi split = "fold"
    "quota": "equal",           # quota none của train: equal | natural (bảng phụ)
    "origin": "first",          # first | per_frame (Bảng 2)
    "landmarks": "all",         # all | reduced (bảng phụ, LSTM)
    "features": "full",         # full | no_signed | no_straightness | no_presence
                                # | angles (Bảng 5, rừng)
    "cell": "lstm",             # lstm | gru (bảng phụ)
    "hidden": config.LSTM_HIDDEN,
    "pooling": config.LSTM_POOLING,
    "augment": True,
    "zoom_style_p": config.AUG_ZOOM_STYLE_P,
    "static_share": config.AUG_STATIC_SHARE,
    "epochs": None,             # None: dừng sớm trên val; số: học đúng bấy nhiêu
                                # epoch, không chọn gì trên tập đánh giá (Bảng 7)
    "max_epochs": config.LSTM_MAX_EPOCHS,
}
DATA_KEYS = ("win_sec", "margin", "split", "fold", "quota")
QUOTAS = {"equal": equal_quota, "natural": proportional_quota}
DROPPED = {"full": (), "angles": (), "no_signed": config.SIGNED_FEATURES,
           "no_straightness": ("straightness",), "no_presence": ("presence",)}
#: Hằng số không ảnh hưởng kết quả — đổi chúng không làm bản ghi cũ hết hạn.
#: Tầng kích hoạt (``CONF_FIRE``, ``CONF_HOLD``, ``K_OF_N``, ``COOLDOWN_SEC`` và
#: mọi hằng số ``FSM_`` của Phase 9) chạy SAU mô hình, lúc dựng bảng từ bản ghi,
#: nên chỉnh máy trạng thái không phải học lại (người dùng chọn 2026-10-23); phím
#: tắt và đo đạc của Phase 10 (``CTRL_``, ``BENCH_``) cũng vậy. Màn hình luyện tập
#: của Phase 10 (2026-10-26): ``SHOW_FINGERS`` chỉ đổi màn hình; ``FINGER_TIPS``
#: suy ra hoàn toàn từ ``TIPS`` và ``FINGER_MCPS``, hai hằng số vẫn được băm, nên
#: bỏ nó không che được thay đổi nào. Hằng số mới ngoài danh sách này vẫn làm bản
#: ghi hết hạn: tốn thời gian học lại, nhưng không bao giờ dùng lại một bản ghi sai.
_IRRELEVANT = ("EXP_JOBS", "EXP_TORCH_THREADS", "EXP_LOG_EVERY", "TIMING_WINDOWS",
               "EVENT_", "COLOR_", "FIG_", "FONT_", "TEXT_", "POINT_", "LINE_",
               "DISPLAY_", "QUIT_", "FPS_", "OBS_", "MP_", "CAM_", "EXAMPLES_",
               "PROFILE_", "PROBE_", "PERM_", "LEAKAGE_", "CALIB_",
               "CONF_FIRE", "CONF_HOLD", "K_OF_N", "COOLDOWN_SEC", "FSM_",
               "CTRL_", "BENCH_", "SHOW_FINGERS", "FINGER_TIPS")


def full_spec(spec):
    """Spec đầy đủ: mặc định của :data:`DEFAULT_SPEC`, đè bằng ``spec``."""
    unknown = set(spec) - set(DEFAULT_SPEC)
    if unknown:
        raise ValueError(f"Spec có khoá lạ: {sorted(unknown)}")
    return {**DEFAULT_SPEC, **spec}


def fingerprint(obj):
    """Dấu vân tay ngắn của một đối tượng ghi được ra JSON."""
    text = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def relevant_config():
    """Các hằng số của ``config.py`` có thể làm đổi kết quả một thí nghiệm.

    Đường dẫn bị bỏ: file nằm ở đâu không đổi kết quả, còn NỘI DUNG dữ liệu đã
    có :func:`data_fingerprint` canh.
    """
    return {k: list(v) if isinstance(v, tuple) else v
            for k, v in vars(config).items()
            if k.isupper() and not k.startswith(_IRRELEVANT) and not isinstance(v, Path)}


def data_fingerprint(landmarks_dir=None):
    """Dấu vân tay của dữ liệu vào: tên và cỡ từng file điểm mốc, và
    ``splits.json``."""
    landmarks_dir = Path(landmarks_dir or config.LANDMARKS_DIR / "ipn")
    files = [(p.name, p.stat().st_size) for p in sorted(landmarks_dir.glob("*.npz"))]
    return fingerprint({"landmarks": files, "splits": read_splits()})


def pool_subjects(splits):
    """Người dùng được cho MỌI khảo sát: train và val. Không bao giờ test."""
    return sorted(set(splits["train"]) | set(splits["val"]))


def leaky_split(y, val_counts, rng):
    """Bảng 4 — chia NGẪU NHIÊN THEO CỬA SỔ, đúng phép chia mà luật 8 cấm.

    Chỉ để đo rò rỉ: các cửa sổ liền nhau chồng lấn 1,0/1,2 giây, nên chia
    ngẫu nhiên thì gần như mọi cửa sổ val có một "anh em sinh đôi" trong train.
    Phân tầng theo lớp với ĐÚNG số cửa sổ mỗi lớp của val theo người, để hai
    hàng của Bảng 4 chỉ khác nhau ở cách chia (người dùng duyệt 2026-10-22).

    Args:
        y: ``(N,)`` nhãn của mọi cửa sổ trong kho (người train + val).
        val_counts: ``{lớp: số cửa sổ}`` của val theo người.
        rng: ``np.random.Generator``.

    Returns:
        ``(N,)`` mảng ``"train"`` / ``"val"``.
    """
    y = np.asarray(y)
    part = np.full(y.size, "train", dtype="<U16")
    for cls, n in sorted(val_counts.items()):
        idx = np.flatnonzero(y == cls)
        if n > idx.size:
            raise ValueError(f"Lớp {cls} chỉ có {idx.size} cửa sổ, cần {n} cho val")
        part[rng.choice(idx, size=int(n), replace=False)] = "val"
    return part


# --------------------------------------------------------------------------
# Dữ liệu: bộ cửa sổ và dòng thời gian video của một biến thể — dựng một lần,
# ghi vào EXP_DATA_DIR, mọi tiến trình đọc lại
# --------------------------------------------------------------------------

def data_spec(spec):
    return {k: spec[k] for k in DATA_KEYS}


def stream_group(spec, splits):
    """Tập video dùng cho mức sự kiện: ``(tên, danh sách người)``; ``None`` với
    phép chia rò rỉ — tập đánh giá của nó không phải là một nhóm video."""
    if spec["split"] == "official":
        return "val", sorted(splits["val"])
    if spec["split"] == "fold":
        folds = subject_folds(pool_subjects(splits), config.EXP_FOLDS)
        return f"fold{spec['fold']}", folds[spec["fold"] - 1]
    return None


def set_path(spec, data_fp):
    d = data_spec(spec)
    name = (f"set_{d['split']}{d['fold'] or ''}_w{d['win_sec']:g}_m{d['margin']}"
            f"_{d['quota']}")
    return config.EXP_DATA_DIR / f"{name}_{fingerprint([d, relevant_config(), data_fp])}.npz"


def stream_path(spec, splits, data_fp):
    group = stream_group(spec, splits)
    if group is None:
        return None
    key = fingerprint([group, spec["win_sec"], relevant_config(), data_fp])
    return config.EXP_DATA_DIR / f"stream_{group[0]}_w{spec['win_sec']:g}_{key}.npz"


@lru_cache(maxsize=2)
def natural_pool(win_sec, margin):
    """MỌI cửa sổ (chưa lấy mẫu con) của người train + val, đã chuẩn hoá."""
    from src.events import clip_paths
    paths, _ = clip_paths(pool_subjects(read_splits()))
    windows, info = collect_windows(paths, config.window_steps(win_sec), margin)
    return windows, info


def build_set(spec):
    """Bộ train/val của một biến thể dữ liệu.

    - ``official``: train và val theo ``splits.json``;
    - ``fold``: fold ``spec["fold"]`` của ``subject_folds`` là tập đánh giá,
      các người còn lại là train;
    - ``leaky``: :func:`leaky_split` trên kho cửa sổ.

    Rồi lấy mẫu con lớp none CỦA TRAIN như ``build_dataset.py`` (quota theo
    ``spec["quota"]``, seed ``SEED``); tập đánh giá giữ phân bố tự nhiên.

    Returns:
        dict mảng: ``X_tr``, ``y_tr``, ``pres_tr``; ``X_va``, ``y_va``,
        ``pres_va``, ``src_va``, ``subj_va``, ``clip_va``, ``t0_va``; và
        ``info`` (JSON: số cửa sổ, quota).
    """
    splits = read_splits()
    pool, info = natural_pool(spec["win_sec"], spec["margin"])
    part = split_of(pool["subject"], splits)
    if spec["split"] == "fold":
        held = set(subject_folds(pool_subjects(splits), config.EXP_FOLDS)[spec["fold"] - 1])
        part = np.where(np.isin(pool["subject"], list(held)), "val", "train")
    elif spec["split"] == "leaky":
        official_val = pool["y"][part == "val"]
        counts = {int(c): int(np.sum(official_val == c)) for c in np.unique(official_val)}
        part = leaky_split(pool["y"], counts, np.random.default_rng(config.SEED))
    elif spec["split"] != "official":
        raise ValueError(f"Không có cách chia '{spec['split']}'")
    keep, quota = subsample_none(pool["y"], pool["src_label"], part,
                                 np.random.default_rng(config.SEED),
                                 quota_fn=QUOTAS[spec["quota"]])
    tr, va = (part == "train") & keep, part == "val"
    return {"X_tr": pool["X"][tr], "y_tr": pool["y"][tr], "pres_tr": pool["presence"][tr],
            "subj_tr": pool["subject"][tr], "clip_tr": pool["clip"][tr],
            "t0_tr": pool["t0"][tr],
            "X_va": pool["X"][va], "y_va": pool["y"][va], "pres_va": pool["presence"][va],
            "src_va": pool["src_label"][va], "subj_va": pool["subject"][va],
            "clip_va": pool["clip"][va], "t0_va": pool["t0"][va],
            "info": json.dumps({"n_train": int(tr.sum()), "n_val": int(va.sum()),
                                "quota": quota, "pool_clips": info["n_clips"]})}


def prepare_set(spec, data_fp):
    """Dựng và ghi bộ cửa sổ của ``spec`` nếu chưa có. Returns: đường dẫn."""
    path = set_path(spec, data_fp)
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp.npz")
        np.savez(tmp, **build_set(spec))
        tmp.replace(path)
    return path


def prepare_stream(spec, data_fp):
    """Chạy các video của tập đánh giá qua ``WindowStream`` và ghi lại, nếu
    chưa có. Returns: đường dẫn, hoặc ``None`` với phép chia rò rỉ."""
    from src.events import clip_paths, clip_streams, save_streams
    splits = read_splits()
    path = stream_path(spec, splits, data_fp)
    if path is None or path.is_file():
        return path
    paths, _ = clip_paths(stream_group(spec, splits)[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.npz")
    save_streams(tmp, *clip_streams(paths, spec["win_sec"]))
    tmp.replace(path)
    return path


def load_set(path):
    with np.load(path, allow_pickle=False) as data:
        out = {k: data[k] for k in data.files}
    out["info"] = json.loads(str(out["info"]))
    return out


# --------------------------------------------------------------------------
# Biểu diễn: đặc trưng cho rừng, chuỗi cho LSTM — theo spec
# --------------------------------------------------------------------------

def feature_names(spec):
    """Tên các cột đặc trưng mà rừng của ``spec`` nhận."""
    dropped = DROPPED[spec["features"]]
    names = [n for n in FEATURE_NAMES if n not in dropped]
    return names + (ANGLE_NAMES if spec["features"] == "angles" else [])


def feature_matrix(X, presence, spec, F=None):
    """Đặc trưng của các cửa sổ ĐÃ chuẩn hoá ``X`` theo ``spec``.

    Args:
        F: đặc trưng 15 chiều đã tính sẵn của đúng ``X`` (mức sự kiện tính lúc
            chạy video) — dùng lại khi biểu diễn là mặc định.
    """
    if spec["origin"] == "per_frame" or F is None:
        transform = per_frame_origin if spec["origin"] == "per_frame" else None
        F = (np.stack([window_features(transform(w) if transform else w, p)
                       for w, p in zip(X, presence)]) if len(X)
             else np.empty((0, len(FEATURE_NAMES)), np.float32))
    columns = [FEATURE_NAMES.index(n) for n in feature_names(spec) if n in FEATURE_NAMES]
    F = np.asarray(F, dtype=np.float32)[:, columns]
    if spec["features"] == "angles":
        A = (np.stack([angle_features(w) for w in X]) if len(X)
             else np.empty((0, len(ANGLE_NAMES)), np.float32))
        F = np.hstack([F, A])
    return F


def sequence_fn(spec):
    """Hàm ``cửa sổ đã chuẩn hoá → chuỗi`` cho LSTM theo ``spec``; ``None`` là
    ``datasets.window_sequence`` mặc định."""
    from src.datasets import window_sequence

    if spec["origin"] == "per_frame":
        return lambda win: window_sequence(per_frame_origin(win))
    if spec["landmarks"] == "reduced":
        columns = landmark_columns()
        return lambda win: window_sequence(win)[:, columns]
    return None


def input_size(spec):
    return (len(landmark_columns()) if spec["landmarks"] == "reduced"
            else config.LSTM_INPUT_SIZE)


# --------------------------------------------------------------------------
# Một thí nghiệm
# --------------------------------------------------------------------------

def record_key(spec, data_fp):
    return fingerprint([full_spec(spec), relevant_config(), data_fp])


def record_paths(name, record_dir=None):
    record_dir = Path(record_dir or config.EXP_RECORD_DIR)
    return record_dir / f"{name}.json", record_dir / f"{name}.npz"


def has_record(name, spec, data_fp, record_dir=None):
    """Bản ghi của thí nghiệm ``name`` có, và còn đúng với spec, hằng số, dữ liệu."""
    json_path, npz_path = record_paths(name, record_dir)
    if not (json_path.is_file() and npz_path.is_file()):
        return False
    meta = json.loads(json_path.read_text(encoding="utf-8"))
    return meta.get("key") == record_key(spec, data_fp)


def load_record(name, record_dir=None):
    """Returns: ``(meta, arrays)``."""
    json_path, npz_path = record_paths(name, record_dir)
    meta = json.loads(json_path.read_text(encoding="utf-8"))
    with np.load(npz_path, allow_pickle=False) as data:
        arrays = {k: data[k] for k in data.files}
    return meta, arrays


def _log(name, text):
    print(f"[{name}] {text}", flush=True)


def run_experiment(name, spec, data_fp, record_dir=None, threads=None):
    """Chạy một thí nghiệm và ghi bản ghi. Dữ liệu của nó phải đã được dựng
    (:func:`prepare_set`, :func:`prepare_stream`).

    Args:
        threads: số luồng torch (tiến trình con của ``run_experiments.py``).

    Returns:
        đường dẫn file JSON của bản ghi.
    """
    spec = full_spec(spec)
    started = time.perf_counter()
    splits = read_splits()
    data = load_set(set_path(spec, data_fp))
    s_path = stream_path(spec, splits, data_fp)
    stream_X = stream_F = None
    n_stream = 0
    if s_path is not None:
        from src.events import load_streams
        timelines, stream_X, stream_F = load_streams(s_path)
        n_stream = sum(int(t.valid.sum()) for t in timelines)

    train_info = {}
    if spec["model"] == "rf":
        from src.forest import class_proba, train_forest
        X_tr, y_tr, pres_tr = data["X_tr"], data["y_tr"], data["pres_tr"]
        if config.AUG_RIGID_SHARE > 0:      # cùng tập huấn luyện với train_rf.py
            from src.augment import rigid_swipes
            X_r, y_r, source = rigid_swipes(X_tr, y_tr, "train",
                                            np.random.default_rng(spec["seed"]))
            X_tr, y_tr = np.concatenate([X_tr, X_r]), np.concatenate([y_tr, y_r])
            pres_tr = np.concatenate([pres_tr, pres_tr[source]])
        model = train_forest(feature_matrix(X_tr, pres_tr, spec), y_tr, seed=spec["seed"])
        proba_va = class_proba(model, feature_matrix(data["X_va"], data["pres_va"], spec))
        proba_st = None
        if s_path is not None:
            proba_st = class_proba(model, feature_matrix(
                stream_X, _stream_presence(timelines), spec, F=stream_F))
        train_info = {"n_train": int(y_tr.size), "n_features": int(model.n_features_in_)}
    elif spec["model"] == "lstm":
        import torch

        from src.datasets import window_sequences
        from src.models import predict_proba
        from src.training import train_lstm
        if threads:
            torch.set_num_threads(threads)
        sequence = sequence_fn(spec)

        def progress(row, stopper):
            if row["epoch"] % config.EXP_LOG_EVERY == 0:
                score = "" if stopper is None else (
                    f", macro-F1 val {row['val_macro_f1']:.3f} (tốt nhất trượt "
                    f"{stopper.best_score:.3f} ở epoch {stopper.best_epoch})")
                _log(name, f"epoch {row['epoch']}{score}, "
                           f"{time.perf_counter() - started:.0f} s")

        trained = train_lstm(
            data["X_tr"], data["y_tr"], data["X_va"], data["y_va"], seed=spec["seed"],
            augment=spec["augment"], zoom_style_p=spec["zoom_style_p"],
            static_share=spec["static_share"], max_epochs=spec["max_epochs"],
            fixed_epochs=(min(spec["epochs"], spec["max_epochs"]) if spec["epochs"]
                          else None),
            measure_train=False, sequence=sequence, on_epoch=progress,
            model_kwargs={"input_size": input_size(spec), "hidden": spec["hidden"],
                          "pooling": spec["pooling"], "cell": spec["cell"]})
        proba_va = predict_proba(trained.model, window_sequences(data["X_va"], sequence))
        proba_st = (predict_proba(trained.model, window_sequences(stream_X, sequence))
                    if s_path is not None else None)
        stopper = trained.stopper
        train_info = {"n_train": int(data["y_tr"].size), "epochs_run": len(trained.history),
                      "best_epoch": None if stopper is None else stopper.best_epoch,
                      "best_raw": None if stopper is None else stopper.best_raw,
                      "best_smoothed": None if stopper is None else stopper.best_score,
                      "train_seconds": trained.seconds,
                      "augment_fallbacks": trained.dataset.n_fallback,
                      "torch_threads": torch.get_num_threads()}
    else:
        raise ValueError(f"Không có mô hình thí nghiệm '{spec['model']}'")

    json_path, npz_path = record_paths(name, record_dir)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    arrays = {"proba_va": np.asarray(proba_va, dtype=np.float32),
              "y_va": data["y_va"], "src_va": data["src_va"],
              "subj_va": data["subj_va"], "clip_va": data["clip_va"], "t0_va": data["t0_va"]}
    if proba_st is not None:
        arrays["proba_stream"] = np.asarray(proba_st, dtype=np.float32)
    tmp = npz_path.with_suffix(".tmp.npz")
    np.savez(tmp, **arrays)
    tmp.replace(npz_path)
    meta = {"name": name, "spec": spec, "key": record_key(spec, data_fp),
            "data_fingerprint": data_fp, "set": Path(set_path(spec, data_fp)).name,
            "stream": None if s_path is None else Path(s_path).name,
            "n_stream_windows": n_stream, "set_info": data["info"],
            "train": train_info, "seconds": time.perf_counter() - started,
            "created": datetime.now().isoformat(timespec="seconds")}
    json_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str),
                         encoding="utf-8")
    _log(name, f"xong sau {meta['seconds']:.0f} s")
    return json_path


def _stream_presence(timelines):
    """Tỉ lệ có tay của các lần dự đoán hợp lệ, nối liền theo thứ tự video."""
    return np.concatenate([t.presence[t.valid] for t in timelines]).astype(np.float32)


# --------------------------------------------------------------------------
# Chỉ số từ bản ghi
# --------------------------------------------------------------------------

NO_EVIDENCE = "không đủ bằng chứng để kết luận"


def verdict(delta, std):
    """Câu kết luận cho một so sánh (SPEC Phase 8 mục 7): chênh lệch nhỏ hơn
    độ lệch chuẩn giữa các seed thì không kết luận được gì."""
    if std is None or not np.isfinite(std) or not np.isfinite(delta):
        return "chưa có độ lệch chuẩn (Bảng 6)"
    return NO_EVIDENCE if abs(delta) < std else "chênh lệch lớn hơn độ lệch chuẩn"


def predictions(arrays, part):
    """Nhãn và độ tin của một phần bản ghi (``"va"`` hay ``"stream"``): từ
    xác suất (thí nghiệm) hoặc ghi sẵn (mô hình đã lưu, có cả luật)."""
    if f"proba_{part}" in arrays:
        proba = arrays[f"proba_{part}"]
        return proba.argmax(axis=1).astype(np.int64), proba.max(axis=1, initial=0.0)
    return arrays[f"labels_{part}"], arrays[f"conf_{part}"]

def window_metrics(y, labels, src):
    """Mức cửa sổ: macro-F1, F1 từng lớp, ma trận nhầm lẫn, báo nhầm lớp none
    (tổng và với tay chỉ trỏ)."""
    from src.evaluation import summarize

    summary = summarize(y, labels)
    none = y == 0
    out = {"n_windows": int(y.size), "macro_f1": summary["macro_f1"],
           **{f"f1_{r['class']}": r["f1"] for r in summary["per_class"]},
           "none_alarm": float(np.mean(labels[none] != 0)) if none.any() else float("nan"),
           "confusion": summary["confusion"]}
    for code in config.POINTING_SRC_LABELS:
        pick = none & (src == code)
        out[f"alarm_{code}"] = float(np.mean(labels[pick] != 0)) if pick.any() else float("nan")
    return out


def event_metrics(timelines, labels, confidences, filter_name=config.EVENT_FILTER,
                  mode=config.EVENT_MATCH):
    """Mức sự kiện từ dự đoán của các lần hợp lệ (nối liền theo thứ tự video).

    Returns:
        ``(summary, results)`` của ``events.summarize_events`` /
        ``events.evaluate_timelines``.
    """
    from src.events import evaluate_timelines, scatter, summarize_events

    results = evaluate_timelines(timelines, *scatter(timelines, labels, confidences),
                                 filter_name, mode=mode)
    return summarize_events(results), results
