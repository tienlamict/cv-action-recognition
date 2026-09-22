"""Bọc MediaPipe Hand Landmarker: một bàn tay, chế độ VIDEO, chỉ toạ độ 2D.

Ba quy ước của file này, mỗi quy ước chặn một lỗi im lặng:

- **BGR → RGB ở đây, và chỉ ở đây.** OpenCV đọc BGR, MediaPipe cần RGB. Quên
  chuyển thì MediaPipe không báo lỗi, chỉ phát hiện kém đi.
- **Không bao giờ lật ảnh đầu vào.** Ảnh vào mô hình phải cùng quy ước với dữ
  liệu huấn luyện. Chỉ bản hiển thị cho người xem mới được lật (xem
  ``src/display.py``). Có kiểm thử đọc mã nguồn file này để canh luật đó.
- **Không thấy tay thì trả về mảng NaN, không trả về None.** Frame mất tay vẫn
  là một frame thật trên trục thời gian.

Chỉ lấy ``x``, ``y``. Không đọc ``z`` và không dùng ``hand_world_landmarks``.
"""

from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision

from src import config


def empty_landmarks():
    """Mảng ``(21, 2)`` toàn NaN — biểu diễn của một frame không thấy tay."""
    return np.full((config.NUM_LANDMARKS, 2), np.nan, dtype=np.float32)


def seconds_to_ms(ts_sec):
    """Đổi mốc thời gian giây sang mili giây nguyên, dạng MediaPipe cần."""
    return int(round(ts_sec * 1000))


class HandTracker:
    """MediaPipe Hand Landmarker với ``num_hands=1``, chế độ VIDEO.

    Dùng như một context manager để chắc chắn giải phóng tài nguyên::

        with HandTracker() as tracker:
            xy, present, score, handedness = tracker.process(frame_bgr, ts_ms)
    """

    def __init__(self, model_path=config.HAND_LANDMARKER_TASK):
        model_path = Path(model_path)
        if not model_path.is_file():
            raise FileNotFoundError(
                f"Chưa có mô hình {model_path}. Xem README, mục "
                "'Tải mô hình và dữ liệu'."
            )

        options = vision.HandLandmarkerOptions(
            base_options=mp_tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=config.NUM_HANDS,
            min_hand_detection_confidence=config.MP_MIN_DETECTION_CONF,
            min_hand_presence_confidence=config.MP_MIN_PRESENCE_CONF,
            min_tracking_confidence=config.MP_MIN_TRACKING_CONF,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_ts_ms = None

    def process(self, frame_bgr, ts_ms):
        """Chạy mô hình trên một frame.

        Args:
            frame_bgr: ảnh BGR ``(H, W, 3)`` đúng như OpenCV đọc được.
            ts_ms: mốc thời gian mili giây. Chế độ VIDEO đòi hỏi mốc tăng ngặt;
                nếu hai frame trùng mốc, mốc đưa cho MediaPipe được đẩy lên 1 ms.
                Mốc thật của frame vẫn do người gọi giữ.

        Returns:
            ``(xy_norm, present, score, handedness)``:

            - ``xy_norm``: ``(21, 2)`` float32, toạ độ chuẩn hoá của MediaPipe
              trong ``[0, 1]`` theo chiều rộng và chiều cao ảnh; NaN nếu không
              thấy tay.
            - ``present``: ``True`` nếu thấy tay.
            - ``score``: điểm tin cậy của phân loại tay trái/phải; NaN nếu không
              thấy tay.
            - ``handedness``: ``"Left"`` hoặc ``"Right"`` theo MediaPipe; chuỗi
              rỗng nếu không thấy tay. Vì ảnh vào không lật, nhãn này có thể
              ngược với tay thật — thí nghiệm 6 đo quy ước đó.
        """
        ts_ms = int(ts_ms)
        if self._last_ts_ms is not None and ts_ms <= self._last_ts_ms:
            ts_ms = self._last_ts_ms + 1
        self._last_ts_ms = ts_ms

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = self._landmarker.detect_for_video(image, ts_ms)

        if not result.hand_landmarks:
            return empty_landmarks(), False, float("nan"), ""

        landmarks = result.hand_landmarks[0]
        xy_norm = np.array([(lm.x, lm.y) for lm in landmarks], dtype=np.float32)
        category = result.handedness[0][0]
        return xy_norm, True, float(category.score), category.category_name

    def close(self):
        self._landmarker.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
