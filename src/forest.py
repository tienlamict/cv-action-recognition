"""Rừng ngẫu nhiên trên 15 đặc trưng — mô hình học máy đầu tiên (Phase 6).

Cấu hình theo SPEC: ``RF_N_ESTIMATORS`` cây, ``class_weight="balanced_subsample"``,
``random_state=SEED``, phần còn lại để mặc định. Không chuẩn hoá đặc trưng: cây
chỉ so một đặc trưng với một ngưỡng, nên thang đo khác nhau giữa các đặc trưng
không ảnh hưởng — và bỏ hẳn bước chuẩn hoá là cách chắc nhất để không fit nó
trên dữ liệu ngoài train.

Mô hình lưu kèm danh sách đặc trưng và danh sách lớp. Lúc nạp, hai danh sách đó
phải khớp ``FEATURE_NAMES`` và ``CLASSES`` hiện tại — đổi thứ tự đặc trưng mà
dùng mô hình cũ là một lỗi im lặng điển hình, nên ở đây nó là một lỗi ồn ào.
"""

import hashlib
from pathlib import Path

import joblib
import numpy as np

from src import config
from src.features import FEATURE_NAMES


def train_forest(F, y, seed=config.SEED, n_jobs=-1):
    """Huấn luyện rừng ngẫu nhiên. ``n_jobs`` không làm đổi kết quả."""
    # Nạp scikit-learn ở đây, không ở đầu file: nó tốn ~5 giây, và demo.py
    # --model rules không được phải chờ thứ nó không dùng.
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=config.RF_N_ESTIMATORS,
                                   class_weight=config.RF_CLASS_WEIGHT,
                                   random_state=seed, n_jobs=n_jobs)
    return model.fit(np.asarray(F, dtype=np.float32), np.asarray(y))


def save_bundle(model, path=None, **meta):
    """Lưu mô hình cùng danh sách đặc trưng, danh sách lớp và ``meta``."""
    path = Path(path or config.RF_MODEL_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_names": list(FEATURE_NAMES),
                 "classes": list(config.CLASSES), **meta}, path, compress=3)
    return path


def load_bundle(path=None):
    """Nạp mô hình đã lưu.

    Raises:
        FileNotFoundError: chưa huấn luyện.
        ValueError: mô hình lưu với danh sách đặc trưng hoặc lớp khác hiện tại.
    """
    path = Path(path or config.RF_MODEL_PATH)
    if not path.is_file():
        raise FileNotFoundError(
            f"Chưa có mô hình {path.name}. Chạy python scripts/train_rf.py trước.")
    bundle = joblib.load(path)
    if bundle.get("feature_names") != list(FEATURE_NAMES):
        raise ValueError(f"{path.name} huấn luyện với danh sách đặc trưng khác "
                         "FEATURE_NAMES hiện tại — huấn luyện lại.")
    if bundle.get("classes") != list(config.CLASSES):
        raise ValueError(f"{path.name} huấn luyện với danh sách lớp khác "
                         "CLASSES hiện tại — huấn luyện lại.")
    return bundle


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class ForestClassifier:
    """Mô hình rừng dạng hàm ``features → (label, confidence)`` cho ``demo.py``.

    Nạp LƯỜI ở lần gọi đầu, nên tạo đối tượng không tốn gì và không lỗi khi
    chưa có mô hình — chỉ lỗi khi thật sự dùng. ``label`` là lớp có xác suất cao
    nhất, ``confidence`` là xác suất đó.

    Xác suất tính bằng cách gọi thẳng lõi của từng cây rồi lấy trung bình —
    đúng phép tính của ``predict_proba``, cho ra cùng con số (đo trên 300 cửa
    sổ: sai khác 0), nhưng bỏ được phần kiểm tra đầu vào và điều phối song
    song mà scikit-learn làm lại ở mỗi lần gọi: 10,7 ms thay vì 62,6 ms mỗi
    cửa sổ. Demo dự đoán mỗi 0,2 giây ngay trong vòng lặp khung hình, nên 50 ms
    đó là FPS bị mất.
    """

    def __init__(self, path=None):
        self.path = path
        self._trees = None
        self._classes = None

    def load(self):
        """Nạp mô hình ngay (~2,7 s). ``LivePredictor`` gọi hàm này lúc khởi
        tạo, để demo không đứng hình ở lần đầu thấy tay."""
        if self._trees is None:
            model = load_bundle(self.path)["model"]
            self._trees = [estimator.tree_ for estimator in model.estimators_]
            self._classes = model.classes_
        return self

    def __call__(self, features):
        self.load()
        x = np.ascontiguousarray(np.asarray(features, dtype=np.float32).reshape(1, -1))
        proba = np.zeros(len(self._classes))
        for tree in self._trees:
            leaf = tree.predict(x)[0]
            proba += leaf / leaf.sum()
        proba /= len(self._trees)
        k = int(np.argmax(proba))
        return int(self._classes[k]), float(proba[k])
