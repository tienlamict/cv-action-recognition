"""Nơi DUY NHẤT chứa hằng số của project.

Mọi file khác trong ``src/`` và ``scripts/`` phải nhập hằng số từ đây, không
được viết lại một con số nào. Xem CLAUDE.md, mục "config.py là nơi duy nhất
chứa hằng số".

Hai hằng số quy ước hướng — ``SWIPE_LEFT_SIGN`` và ``IPN_FLIP_X`` — cố ý để
``None``. Chúng phải được ĐO bằng script chứ không đoán, nên mọi chỗ dùng
chúng phải đi qua :func:`require_measured` để chương trình dừng ngay thay vì
chạy sai một cách im lặng.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Đường dẫn — mọi đường dẫn đều suy ra từ ROOT, không bao giờ viết tuyệt đối
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

SRC_DIR = ROOT / "src"
SCRIPTS_DIR = ROOT / "scripts"
TESTS_DIR = ROOT / "tests"
NOTEBOOKS_DIR = ROOT / "notebooks"
RESULTS_DIR = ROOT / "results"

MODELS_DIR = ROOT / "models"
HAND_LANDMARKER_TASK = MODELS_DIR / "hand_landmarker.task"

DATA_DIR = ROOT / "data"
IPN_DIR = DATA_DIR / "ipn"
RAW_DIR = DATA_DIR / "raw"
LANDMARKS_DIR = DATA_DIR / "landmarks"
WINDOWS_DIR = DATA_DIR / "windows"

WINDOWS_NPZ = WINDOWS_DIR / "windows.npz"
SPLITS_JSON = DATA_DIR / "splits.json"

# --------------------------------------------------------------------------
# Lớp cử chỉ — thứ tự CỐ ĐỊNH, ``none`` luôn là chỉ số 0
# --------------------------------------------------------------------------

CLASSES = ["none", "swipe_left", "swipe_right", "zoom_in", "zoom_out"]

# --------------------------------------------------------------------------
# Chỉ số điểm mốc MediaPipe (21 điểm, 1 bàn tay)
# --------------------------------------------------------------------------

WRIST = 0           # gốc toạ độ khi chuẩn hóa cửa sổ
MIDDLE_MCP = 9      # khoảng cách 0 -> 9 là đơn vị đo
TIPS = [4, 8, 12, 16, 20]   # đầu 5 ngón: cái, trỏ, giữa, nhẫn, út
INDEX_TIP = 8       # đầu ngón trỏ — dùng đo độ rung ở Phase 1
NUM_LANDMARKS = 21

# --------------------------------------------------------------------------
# Trục thời gian và cửa sổ — tính bằng GIÂY, không bằng frame
# --------------------------------------------------------------------------

HZ = 15.0           # lưới thời gian đều sau khi resample
WIN_SEC = 1.2       # độ dài một cửa sổ
STRIDE_SEC = 0.2    # bước trượt giữa hai cửa sổ

T = round(WIN_SEC * HZ)     # số bước trong một cửa sổ = 18

MAX_GAP = 3             # lỗ hổng NaN dài hơn số bước này thì GIỮ NaN
MIN_PRESENCE = 0.7      # tỉ lệ bước có tay tối thiểu của một cửa sổ hợp lệ
LABEL_COVERAGE = 0.6    # ngưỡng phủ nhãn khi gán nhãn cho cửa sổ

# --------------------------------------------------------------------------
# Quy ước hướng — CHƯA ĐO. Dùng require_measured() trước khi đọc
# --------------------------------------------------------------------------

SWIPE_LEFT_SIGN = None      # CHƯA ĐO — đo ở Phase 1
IPN_FLIP_X = None           # CHƯA ĐO — đo ở Phase 4

#: Hằng số nào phải đo ở phase nào. require_measured() đọc bảng này.
MEASURED_IN_PHASE = {
    "SWIPE_LEFT_SIGN": 1,
    "IPN_FLIP_X": 4,
}

# --------------------------------------------------------------------------
# Camera — giữ nguyên suốt dự án để mọi số liệu tốc độ so sánh được với nhau
# --------------------------------------------------------------------------

CAM_W = 640
CAM_H = 480
CAM_FPS = 30
CAM_INDEX = 0           # webcam mặc định của máy

# --------------------------------------------------------------------------
# Logic kích hoạt
# --------------------------------------------------------------------------

CONF_FIRE = 0.75        # ngưỡng tin cậy để bắt đầu xét phát lệnh
CONF_HOLD = 0.55        # ngưỡng trễ, thấp hơn CONF_FIRE
K_OF_N = (3, 5)         # đồng thuận: k cửa sổ đồng ý trên n cửa sổ gần nhất
COOLDOWN_SEC = 1.2      # thời gian câm lặng sau khi phát một lệnh

# --------------------------------------------------------------------------
# Tái lập
# --------------------------------------------------------------------------

SEED = 42               # đặt cho random, numpy, torch


# --------------------------------------------------------------------------
# MediaPipe Hand Landmarker — ba ngưỡng để mặc định 0,5: ĐO trước khi chỉnh
# --------------------------------------------------------------------------

NUM_HANDS = 1
MP_MIN_DETECTION_CONF = 0.5     # bộ phát hiện lòng bàn tay
MP_MIN_PRESENCE_CONF = 0.5      # cờ hiện diện của mô hình điểm mốc
MP_MIN_TRACKING_CONF = 0.5      # bám từ frame trước

# --------------------------------------------------------------------------
# Đo FPS
# --------------------------------------------------------------------------

FPS_WARMUP_SEC = 3.0        # bỏ mấy giây đầu khỏi thống kê (camera còn tự chỉnh)
FPS_ROLLING_FRAMES = 30     # FPS trượt hiển thị trên màn hình
FPS_LOW_PERCENTILE = 1.0    # "1% low": phân vị thấp của FPS tức thời

# --------------------------------------------------------------------------
# Đo SWIPE_LEFT_SIGN (Phase 1) — scripts/measure_swipe_sign.py
# --------------------------------------------------------------------------

SWIPE_MEASURE_REPS = 10             # cẩm nang 4.3: 10 lần vuốt
SWIPE_MEASURE_COUNTDOWN_SEC = 2.0   # nghỉ + chuẩn bị trước mỗi lần
SWIPE_MEASURE_RECORD_SEC = 1.5      # thời gian ghi một lần vuốt
SWIPE_MEASURE_MIN_FRAMES = 5        # số frame có tay tối thiểu của một lần hợp lệ
SWIPE_MEASURE_MIN_DX = 0.10         # |dx| tối thiểu, tính theo tỉ lệ chiều rộng khung
SWIPE_MEASURE_MIN_VALID_FRAC = 0.7  # tỉ lệ số lần hợp lệ tối thiểu để kết luận

# --------------------------------------------------------------------------
# Kết quả Phase 1
# --------------------------------------------------------------------------

PHASE1_RESULTS_DIR = RESULTS_DIR / "phase1"
LANDMARKS_CSV_NAME = "landmarks.csv"
MANIFEST_NAME = "manifest.json"
CSV_FLOAT_DECIMALS = 6

OBS_DEFAULT_SEC = 15.0              # cẩm nang bước 6: mỗi thí nghiệm 10–20 giây
OBS_JITTER_EXPERIMENT = "e9_jitter" # thí nghiệm 6.9 — nguồn của sigma tăng cường
OBS_MIN_RUNS = 3                    # cẩm nang bước 6: lặp ít nhất ba lần

# --------------------------------------------------------------------------
# Hiển thị — chỉ bản cho NGƯỜI XEM được lật; ảnh vào mô hình không bao giờ lật
# --------------------------------------------------------------------------

DISPLAY_FLIP_CODE = 1       # cv2.flip: 1 = lật ngang như gương
DISPLAY_WAIT_MS = 1
QUIT_KEYS = (ord("q"), 27)  # q hoặc Esc

COLOR_POINT = (0, 0, 255)       # BGR
COLOR_LINE = (0, 255, 0)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_SHADOW = (0, 0, 0)
COLOR_ALERT = (0, 200, 255)

POINT_RADIUS = 4
LINE_THICKNESS = 2
FONT_SCALE = 0.6
FONT_SCALE_BIG = 1.2
TEXT_THICKNESS = 1
TEXT_SHADOW_THICKNESS = 3
TEXT_ORIGIN = (10, 25)
TEXT_LINE_HEIGHT = 24


def require_measured(name):
    """Trả về giá trị của một hằng số quy ước, hoặc dừng nếu nó chưa được đo.

    Đây là cái chốt an toàn cho luật "quy ước thì ĐO, không đoán": một hằng số
    chưa đo mà lọt vào tính toán sẽ làm hệ thống chạy ngược chiều mà không có
    thông báo lỗi nào.

    Args:
        name: tên hằng số, ví dụ ``"SWIPE_LEFT_SIGN"``.

    Returns:
        Giá trị đã đo của hằng số đó.

    Raises:
        KeyError: nếu ``name`` không phải một hằng số cần đo.
        RuntimeError: nếu hằng số đó còn là ``None``.
    """
    if name not in MEASURED_IN_PHASE:
        raise KeyError(
            f"{name} không phải hằng số cần đo. "
            f"Các hằng số cần đo: {sorted(MEASURED_IN_PHASE)}"
        )

    value = globals()[name]
    if value is None:
        phase = MEASURED_IN_PHASE[name]
        raise RuntimeError(f"Chưa đo {name} — xem Phase {phase}")

    return value
