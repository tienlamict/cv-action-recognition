"""Nơi DUY NHẤT chứa hằng số của project.

Mọi file khác trong ``src/`` và ``scripts/`` phải nhập hằng số từ đây, không
được viết lại một con số nào. Xem CLAUDE.md, mục "config.py là nơi duy nhất
chứa hằng số".

Một số hằng số cố ý để ``None``: chúng phải được ĐO hoặc HIỆU CHUẨN bằng
script chứ không đoán. Mọi chỗ dùng chúng phải đi qua :func:`require_measured`
để chương trình dừng ngay thay vì chạy sai một cách im lặng.
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
# IPN Hand — bố cục trên đĩa và quy ước đọc (xem docs/ipn_format.md)
# --------------------------------------------------------------------------

IPN_VIDEO_DIR = IPN_DIR / "videos" / "videos"
IPN_ANNOT_DIR = IPN_DIR / "annotations"
IPN_ANNOT_LIST = IPN_ANNOT_DIR / "Annot_List.txt"
IPN_CLASS_IDX = IPN_ANNOT_DIR / "classIdx.txt"
IPN_VIDEO_TRAIN_LIST = IPN_ANNOT_DIR / "Video_TrainList.txt"
IPN_VIDEO_TEST_LIST = IPN_ANNOT_DIR / "Video_TestList.txt"
IPN_METADATA_CSV = IPN_DIR / "metadata.csv"

IPN_VIDEO_SUFFIX = ".avi"
IPN_SUBJECT_TOKENS = 2      # mã người = hai token đầu của tên video (1CM1_1)
IPN_LENGTH_TOLERANCE = 5    # lệch quá bấy nhiêu frame so với metadata thì đánh
                            # dấu nghi vấn: chưa rõ frame thừa ở đầu hay cuối

PHASE3_RESULTS_DIR = RESULTS_DIR / "phase3"
EXAMPLES_PER_CLASS = 3      # số đoạn mẫu mỗi lớp khi xuất video minh hoạ

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
THUMB_TIP = 4       # đầu ngón cái — cùng INDEX_TIP đo độ mở cái–trỏ (zoom IPN)
INDEX_TIP = 8       # đầu ngón trỏ — dùng đo độ rung ở Phase 1
FINGER_MCPS = {"index": 5, "middle": 9, "ring": 13, "pinky": 17}
                    # gốc bốn ngón; ba khớp kế tiếp của mỗi ngón là +1, +2, +3
NUM_LANDMARKS = 21

# --------------------------------------------------------------------------
# Trục thời gian và cửa sổ — tính bằng GIÂY, không bằng frame
# --------------------------------------------------------------------------

HZ = 15.0           # lưới thời gian đều sau khi resample
WIN_SEC = 1.2       # độ dài một cửa sổ
STRIDE_SEC = 0.2    # bước trượt giữa hai cửa sổ



def window_steps(seconds):
    """Số bước của một khoảng ``seconds`` giây trên lưới ``HZ``."""
    return round(seconds * HZ)


T = window_steps(WIN_SEC)   # số bước trong một cửa sổ = 18
STRIDE = window_steps(STRIDE_SEC)   # số bước giữa hai cửa sổ liền nhau = 3

MAX_GAP = 3             # lỗ hổng NaN dài hơn số bước này thì GIỮ NaN
MIN_PRESENCE = 0.7      # tỉ lệ bước có tay tối thiểu của một cửa sổ hợp lệ
CORE_MARGIN_STEPS = 3   # nhãn neo vào khoảnh khắc chính (thay LABEL_COVERAGE
                        # của SPEC, quyết định 2026-10-05): cửa sổ mang lớp
                        # đích khi khoảnh khắc chính của cử chỉ nằm trong
                        # [bước 3, bước T-3) của nó. Xem src/windows.py
CORE_SMOOTH_STEPS = 3   # làm mượt tín hiệu trước khi tìm khoảnh khắc chính

# --------------------------------------------------------------------------
# Bộ cửa sổ (Phase 4) — chia tập theo người, lấy mẫu con lớp none
# --------------------------------------------------------------------------

VAL_FRACTION = 0.2      # phần người của split train chính thức tách làm val
NONE_TRAIN_SHARE = 0.5  # none chiếm bấy nhiêu phần tập train sau lấy mẫu con;
                        # SPEC: 40–50%, KHÔNG BAO GIỜ cân bằng 1:1. Quota chia
                        # đều theo nhãn gốc (quyết định 2026-10-05)

PHASE4_RESULTS_DIR = RESULTS_DIR / "phase4"
IPN_FEATURE_RANGES_JSON = PHASE4_RESULTS_DIR / "ipn_feature_ranges.json"
GATE_FEATURES = ("pinch_delta", "dx", "max_vx")    # ba đặc trưng của cổng Phase 4
                            # (duyệt 2026-10-05): luật Phase 5 dựng trên chúng, và
                            # Phase 6 dự đoán chúng đứng đầu bảng độ quan trọng

# --------------------------------------------------------------------------
# Mô hình luật và demo (Phase 5)
# --------------------------------------------------------------------------

PHASE5_RESULTS_DIR = RESULTS_DIR / "phase5"
MODEL_COMPARISON = RESULTS_DIR / "model_comparison"   # .csv + .md, mỗi mô hình một hàng
CALIB_NONE_PCT = 90         # ngưỡng luật = trung điểm của phân vị 90 lớp nền...
CALIB_TARGET_PCT = 10       # ...và phân vị 10 lớp đích (SPEC Phase 5)
BUFFER_EXTRA_SEC = 0.5      # TimeBuffer giữ WIN_SEC + bấy nhiêu giây gần nhất
SHOW_FEATURES = GATE_FEATURES + ("open_range",)
                            # --show-features: ba đặc trưng của cổng, cộng độ xòe
                            # (thêm 2026-10-09). Với vuốt, rừng ngẫu nhiên đòi bàn
                            # tay mở ra trong lúc hất mà ba đặc trưng kia không
                            # cho thấy (results/phase6/notes.md mục 7)

# --------------------------------------------------------------------------
# Rừng ngẫu nhiên và đánh giá (Phase 6)
# --------------------------------------------------------------------------

PHASE6_RESULTS_DIR = RESULTS_DIR / "phase6"
RF_MODEL_PATH = PHASE6_RESULTS_DIR / "rf_model.joblib"   # demo.py --model rf nạp file này
RF_N_ESTIMATORS = 300               # SPEC Phase 6; phần còn lại để mặc định
RF_CLASS_WEIGHT = "balanced_subsample"
PERM_REPEATS = 10                   # số lần xáo mỗi cột trong permutation_importance
CORRELATED_GROUPS = (("dx", "mean_vx"), ("open_delta", "open_trend"),
                     ("pinch_delta", "pinch_range"))
                                    # cặp đặc trưng đo gần cùng một thứ: xáo riêng
                                    # từng cột thì độ quan trọng bị giấu (cột kia
                                    # gánh thay), nên đo thêm bằng cách xáo cả nhóm
PROFILE_FEATURES = ("max_vx", "dx", "pinch_delta", "pinch_range", "open_range")
                                    # đặc trưng lấy trung vị cho từng ô của ma trận
                                    # nhầm lẫn — bằng chứng cho giả thuyết ở notes.md
PROFILE_MIN_N = 10                  # ô có ít cửa sổ hơn thì không lập hồ sơ
POINTING_SRC_LABELS = ("B0A", "B0B")    # nhãn gốc IPN của tay chỉ trỏ (một / hai
                                    # ngón): bàn tay giữ dáng mà di chuyển nhanh —
                                    # mẫu âm khó nhất của vuốt (notes.md mục 4.1)
PROBE_SHAPE_LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)    # probe_swipes.py: giữ bấy nhiêu
                                    # phần sự đổi dáng tay của cú vuốt thật
PROBE_MOTION_LEVELS = (0.25, 0.5, 0.75, 1.0, 1.5)   # ... nhân quãng dời cổ tay
LEAKAGE_F1 = 0.97                   # macro-F1 trên val cao hơn mức này: gần như
                                    # chắc chắn rò rỉ — dừng, kiểm tra splits.json
TEST_USED_LOG = RESULTS_DIR / "TEST_USED.log"   # mỗi lần chạm test/real_test một dòng (luật 13)
MODEL_NAMES = ("rules", "rf", "lstm", "hybrid")
                                    # demo.py/evaluate.py --model, theo thứ tự ra
                                    # đời — cũng là thứ tự hàng trong bảng so sánh.
                                    # hybrid (2026-10-10): vuốt theo LSTM, zoom theo
                                    # rừng (src/hybrid.py)

# --------------------------------------------------------------------------
# LSTM trên chuỗi 42 chiều (Phase 7) — CPU, một chiều
# --------------------------------------------------------------------------

PHASE7_RESULTS_DIR = RESULTS_DIR / "phase7"
LSTM_MODEL_PATH = PHASE7_RESULTS_DIR / "lstm_model.pt"   # demo.py --model lstm nạp file này
LSTM_INPUT_SIZE = NUM_LANDMARKS * 2     # 42: (21, 2) mỗi bước được reshape — không z
LSTM_HIDDEN = 128           # SPEC Phase 7; Phase 8 so với 64
LSTM_LAYERS = 2
LSTM_DROPOUT = 0.3          # giữa hai lớp LSTM và trước lớp phân loại
LSTM_POOLING = "last"       # last / mean / max — Phase 8 so ba cách gộp
LSTM_BATCH = 64
LSTM_LR = 1e-3              # Adam
LSTM_MAX_EPOCHS = 150
LSTM_PATIENCE = 20          # dừng khi macro-F1 val — trung bình trượt
                            # LSTM_CURVE_SMOOTH epoch — không tăng sau bấy nhiêu epoch
LSTM_EVAL_BATCH = 1024      # cỡ lô khi chỉ dự đoán — không ảnh hưởng kết quả
LSTM_CURVE_SMOOTH = 10      # trung bình trượt bấy nhiêu epoch — để dừng sớm và
                            # chọn checkpoint (từ 2026-10-10), và để tìm chỗ loss val
                            # ngừng giảm: các đại lượng val dao động mạnh giữa epoch

# --------------------------------------------------------------------------
# Tăng cường (Phase 4) — chỉ trên tập train, sau khi chia (luật 9)
# --------------------------------------------------------------------------

AUG_FLIP_P = 0.5            # xác suất lật ngang; lật thì đổi nhãn cặp vuốt
AUG_ROTATE_DEG = 10.0       # xoay đều trong [-10°, +10°]
AUG_SCALE_RAMP = 0.10       # co giãn ĐỔI DẦN từ 1 tới 1 ± 10% dọc cửa sổ —
                            # co giãn đều bị normalize_window triệt tiêu
AUG_TIME_WARP = (0.8, 1.2)  # co giãn thời gian
AUG_DROP_P = 0.5            # xác suất xoá một đoạn bước rồi vá
AUG_DROP_STEPS = (1, 3)     # độ dài đoạn bị xoá; <= MAX_GAP để vá được
SIGMA_STILL_QUANTILE = 0.05 # ước lượng AUG_NOISE_SIGMA trên 5% cửa sổ none
                            # của train có cổ tay dời ít nhất
AUG_RIGID_SHARE = 0.0       # rừng ngẫu nhiên (Phase 6, thêm 2026-10-09): số bản
                            # "bàn tay cứng" trên mỗi cửa sổ vuốt của train;
                            # 0 = tắt. Đo trên val (sweep_rigid.py run_03): cú
                            # vuốt giữ 50% sự đổi dáng tay được nhận 10% → 38%
                            # ở mức 0,25 và → 56% ở mức 1, nhưng báo nhầm none
                            # 8,2% → 12,5% và → 21,6%. Tắt cho tới khi người
                            # dùng chọn (results/phase6/notes.md mục 8)
AUG_RIGID_KEEP = (0.0, 1.0) # mỗi bản giữ k phần sự đổi dáng tay của cú vuốt
                            # gốc, k đều trong khoảng này; (0, 0) = cứng hoàn
                            # toàn. Cứng hoàn toàn tạo chỗ trũng: tay đổi dáng
                            # một phần thì không được nhận (notes.md mục 8)
AUG_RIGID_SWEEP = (0.0, 0.25, 0.5, 1.0)     # các mức sweep_rigid.py thử...
AUG_RIGID_KEEP_SWEEP = ((0.0, 0.0), (0.0, 1.0))  # ...với từng khoảng k này
AUG_ZOOM_STYLE_P = 0.0      # LSTM (thêm 2026-10-10): xác suất một cửa sổ zoom của
                            # train mang dáng ngón giữa–nhẫn–út của một bàn tay
                            # IPN khác, đứng yên (augment.restyle_zoom). TẮT: ở 0,5
                            # (train_lstm run_06) LSTM nhận zoom mọi kiểu ngón,
                            # nhưng tay chỉ trỏ thành zoom_out — báo nhầm B0A/B0B
                            # 3,0/4,7% → 11,6/12,5%. notes.md Phase 7 mục 9
AUG_STATIC_SHARE = 0.0      # LSTM: thêm bấy nhiêu phần (so với số cửa sổ train)
                            # cửa sổ bàn tay đứng yên, nhãn none. TẮT cùng phép trên
                            # (run_06 dùng 0,1; chưa tách được tác dụng riêng)

# --------------------------------------------------------------------------
# Đánh giá hai mức và bảy bảng khảo sát (Phase 8) — mọi khảo sát trên val
# hoặc k-fold của người train + val, không bao giờ trên test (luật 13)
# --------------------------------------------------------------------------

PHASE8_RESULTS_DIR = RESULTS_DIR / "phase8"
EXP_DATA_DIR = DATA_DIR / "experiments"     # bộ cửa sổ và dòng thời gian video đã
                                            # dựng cho từng biến thể — dữ liệu sinh lại được
EXP_RECORD_DIR = PHASE8_RESULTS_DIR / "records"     # mỗi thí nghiệm một bản ghi: mọi
                                            # dự đoán, để dựng bảng không phải học lại
EVENT_TOL_SEC = 1.0         # mức sự kiện: dung sai sau lúc cử chỉ kết thúc
EVENT_MATCH = "span"        # TP = lệnh đúng loại phát từ lúc cử chỉ BẮT ĐẦU tới
                            # lúc kết thúc + EVENT_TOL_SEC (người dùng chọn
                            # 2026-10-22). SPEC ban đầu là ±EVENT_TOL_SEC quanh lúc
                            # kết thúc ("end"), nhưng đoạn nhãn IPN gồm cả lúc thu
                            # tay: trên val, lệnh đúng loại đầu tiên phát trung vị
                            # 1,1–1,4 s trước lúc đoạn kết thúc, và 60–66% lệnh đúng
                            # lúc thành một FP cộng một FN. "end" vẫn tính để đối chiếu
EVENT_MATCH_MODES = ("span", "end")
EVENT_FILTER = "fsm"        # bộ lọc sự kiện của các bảng: máy trạng thái của Phase
                            # 9 (src/activation.py). Bảng Phase 8 run_01 dùng
                            # "edge" — mỗi chuỗi dự đoán liền nhau cùng một lớp cử
                            # chỉ là MỘT lệnh, cách đếm của summarize_log.py
SIGNED_FEATURES = ("open_delta", "open_trend", "pinch_delta", "dx", "mean_vx")
                            # năm đặc trưng có dấu (SPEC, mục Vector đặc trưng):
                            # Bảng 5 bỏ cả nhóm
ANGLE_JOINTS = {"thumb": (2, 3, 4), "index": (5, 6, 7), "middle": (9, 10, 11),
                "ring": (13, 14, 15), "pinky": (17, 18, 19)}
                            # góc gập ở khớp giữa mỗi ngón, (điểm, ĐỈNH, điểm):
                            # khớp IP của ngón cái, PIP của bốn ngón kia. Bảng 5,
                            # dòng "thêm góc khớp" — không thuộc vector 15 chiều
REDUCED_LANDMARKS = (0, 2, 4, 5, 8, 9, 12, 13, 16, 17, 20)
                            # 11 điểm rút gọn của bảng phụ: cổ tay, gốc năm ngón
                            # (ngón cái lấy khớp 2), đầu năm ngón
EXP_SEEDS = (42, 43, 44, 45, 46)    # Bảng 6: năm seed, seed đầu là SEED
EXP_FOLDS = 5               # Bảng 7: k-fold theo nhóm người train + val
EXP_KFOLD_EPOCHS = 86       # Bảng 7: LSTM mỗi fold học đúng bấy nhiêu epoch —
                            # epoch checkpoint của mô hình chính (train_lstm/run_07)
                            # — không chọn gì trên fold giữ lại, nên con số không
                            # lạc quan (người dùng chọn 2026-10-22)
EXP_WIN_SECS = (0.8, 1.2, 1.6)      # Bảng 3: độ dài cửa sổ
EXP_CORE_MARGINS = (0, 3, 6)        # bảng phụ: biên khoảnh khắc chính
EXP_HIDDENS = (64, 128)             # bảng phụ: hidden 64 so với 128
EXP_ZOOM_STYLE_P = 0.5      # bảng phụ: đo RIÊNG từng phép tăng cường của Phase 7
EXP_STATIC_SHARE = 0.1      # (train_lstm/run_08 bật cả hai cùng lúc)
EXP_JOBS = 4                # số tiến trình huấn luyện LSTM chạy song song
EXP_TORCH_THREADS = 1       # luồng torch mỗi tiến trình. Đo 2026-10-22: 1, 2 hay 4
                            # luồng cho cùng từng chữ số loss, và tăng cường (numpy,
                            # một luồng) chiếm ~80% một epoch — nhiều tiến trình một
                            # luồng nhanh hơn một tiến trình nhiều luồng
EXP_LOG_EVERY = 10          # tiến trình huấn luyện in tiến độ mỗi bấy nhiêu epoch
TIMING_WINDOWS = 300        # Bảng 1: đo thời gian suy luận trên bấy nhiêu cửa sổ

# --------------------------------------------------------------------------
# Hằng số phải ĐO hoặc HIỆU CHUẨN. Luôn đọc qua require_measured()
# --------------------------------------------------------------------------

SWIPE_LEFT_SIGN = 1         # đo trên IPN bằng measure_direction.py, 189 clip
                            # (Phase 3, 2026-10-05): trung vị dx swipe_left
                            # +0,46, swipe_right −0,54. results/phase3/direction.md
IPN_FLIP_X = 1              # IPN là chuẩn quy ước hướng. Chỉ đổi thành -1 khi
                            # phép thử trên webcam ở Phase 5 chứng minh ngược
AUG_NOISE_SIGMA = 0.0159    # lòng bàn tay; estimate_sigma.py --src-label D0X,
                            # 18 cửa sổ tay nghỉ đứng yên của train (Phase 4,
                            # 2026-10-05). Khớp ước lượng nhiễu tần số cao 0,0162
RULE_VX_HI = 4.026          # ba ngưỡng của rules.py, hiệu chuẩn trên tập TRAIN
RULE_DX_HI = 0.1025         # của IPN bằng calibrate_rules.py (Phase 5,
RULE_P_HI = 0.7209          # 2026-10-05; lý do: results/phase5/thresholds.md).
                            # Không bao giờ chọn trên val hay test. VX: max_vx
                            # của vuốt; DX: |dx| của vuốt; P: |pinch_delta| của
                            # zoom (thay straightness và open_delta, người dùng chốt)

#: Hằng số nào phải đo hoặc hiệu chuẩn ở phase nào. require_measured() đọc bảng này.
MEASURED_IN_PHASE = {
    "SWIPE_LEFT_SIGN": 3,
    "AUG_NOISE_SIGMA": 4,
    "RULE_VX_HI": 5,
    "RULE_DX_HI": 5,
    "RULE_P_HI": 5,
}

# --------------------------------------------------------------------------
# Camera — giữ nguyên suốt dự án để mọi số liệu tốc độ so sánh được với nhau
# --------------------------------------------------------------------------

CAM_W = 640
CAM_H = 480
CAM_FPS = 30
CAM_INDEX = 0           # webcam mặc định của máy

# --------------------------------------------------------------------------
# Logic kích hoạt — chạy SAU mô hình
# --------------------------------------------------------------------------
# Bản ghi thí nghiệm Phase 8 không băm bốn hằng số dưới đây và mọi hằng số tiền
# tố FSM_ (src/experiments.py, _IRRELEVANT; người dùng chọn 2026-10-23), nên chỉnh
# máy trạng thái không phải học lại. Hằng số mới của Phase 9 đặt tiền tố FSM_;
# hằng số mới không có tiền tố này làm mọi bản ghi hết hạn.

CONF_FIRE = 0.75        # ngưỡng tin cậy để mở một ứng viên lệnh
CONF_HOLD = 0.55        # ngưỡng trễ, thấp hơn CONF_FIRE: cửa sổ đồng ý chỉ cần mức này
K_OF_N = (3, 5)         # đồng thuận: k cửa sổ đồng ý trong n cửa sổ kể từ lúc mở
                        # ứng viên; một cửa sổ phản đối tự tin làm hỏng đồng thuận
                        # ngay (src/activation.py)
COOLDOWN_SEC = 1.2      # thời gian câm lặng sau khi phát một lệnh

PHASE9_RESULTS_DIR = RESULTS_DIR / "phase9"
FSM_CMDS_RANGE = (0.9, 1.1)     # SPEC Phase 9: số lệnh trên một cử chỉ, trên video val
FSM_FIRE_SWEEP = (0.6, 0.75, 0.85)  # sweep_activation.py: lưới CONF_FIRE (ba mức của
FSM_K_SWEEP = (2, 3, 4)             # bảng đánh đổi Phase 10) và k của K_OF_N, n giữ nguyên
FSM_PRESENCE_SWEEP = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
                                # MIN_PRESENCE lúc CHẠY cho results/phase9/tradeoff.md;
                                # mô hình giữ nguyên, học với MIN_PRESENCE
FSM_TRADEOFF = ((0.60, 2), (0.75, 3), (0.85, 4))
                                # bảng đánh đổi chính của Phase 10: (CONF_FIRE, k),
                                # n = K_OF_N[1]

# --------------------------------------------------------------------------
# Demo hoàn chỉnh và đo đạc (Phase 10). Bản ghi Phase 8 không băm các tiền tố
# CTRL_ và BENCH_ (src/experiments.py, _IRRELEVANT)
# --------------------------------------------------------------------------

PHASE10_RESULTS_DIR = RESULTS_DIR / "phase10"
BENCH_SESSIONS_DIR = PHASE10_RESULTS_DIR / "sessions"    # phiên ghi của bench.py record
CTRL_HOTKEYS = {"swipe_left": ("left",), "swipe_right": ("right",),
                "zoom_in": ("ctrl", "+"), "zoom_out": ("ctrl", "-")}
                        # SPEC: swipe_left → slide trước, swipe_right → slide sau
                        # (mũi tên của trình chiếu); zoom → Ctrl + / Ctrl −
CTRL_TOGGLE_KEY = ord("c")      # bật/tắt điều khiển trong cửa sổ demo; mặc định TẮT
BENCH_SPEED_SEC = 30.0          # đo FPS bấy nhiêu giây, sau FPS_WARMUP_SEC (cẩm nang 20)
BENCH_SCENARIOS = ("reading", "typing", "talking")
                                # ba kịch bản kích hoạt nhầm, dễ → khó: ngồi yên đọc
                                # tài liệu; gõ phím và dùng chuột; nói chuyện có khua tay
BENCH_SCENARIO_MIN = 10.0       # mỗi kịch bản bấy nhiêu phút (cẩm nang 20.4)
BENCH_GESTURES_PER_CLASS = 5    # phiên "gestures": 5 × 4 lớp = 20 cử chỉ đã đếm
BENCH_PROMPT_SEC = 4.0          # mỗi lời nhắc hiện bấy nhiêu giây — làm cử chỉ trong lúc đó
BENCH_REST_SEC = 3.0            # nghỉ giữa hai lời nhắc, tay để yên trong khung

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
DISPLAY_COMMAND_SEC = 1.0   # lệnh vừa phát hiện trên màn hình demo bấy nhiêu giây
DISPLAY_HELP_KEYS = (ord("?"), ord("h"))    # hiện/ẩn tóm tắt docs/gestures.md
QUIT_KEYS = (ord("q"), 27)  # q hoặc Esc

COLOR_POINT = (0, 0, 255)       # BGR
COLOR_LINE = (0, 255, 0)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_SHADOW = (0, 0, 0)
COLOR_ALERT = (0, 200, 255)
COLOR_IN_RANGE = (0, 220, 0)     # --show-features: nằm trong hộp 25–75 của IPN
COLOR_OUT_RANGE = (0, 0, 255)    # ... nằm ngoài

POINT_RADIUS = 4
LINE_THICKNESS = 2
FONT_SCALE = 0.6
FONT_SCALE_BIG = 1.2
TEXT_THICKNESS = 1
TEXT_SHADOW_THICKNESS = 3
TEXT_ORIGIN = (10, 25)
TEXT_LINE_HEIGHT = 24


# --------------------------------------------------------------------------
# Biểu diễn (Phase 2) — chuẩn hoá cửa sổ và vector đặc trưng
# --------------------------------------------------------------------------

NORM_MIN_SCALE = 1e-6       # ||p9 - p0|| nhỏ hơn mức này thì coi như không đo được
NORM_MIN_PALM_RATIO = 0.5   # lòng bàn tay frame đầu ngắn hơn bấy nhiêu lần
                            # trung vị của cả cửa sổ thì đơn vị không tin được
                            # (tay nghiêng cạnh, điểm mốc sai). Đo trên train
                            # IPN 2026-10-05: loại 2% cửa sổ, xoá các đặc
                            # trưng ngoại lai tới 30 lòng bàn tay
FEATURE_EDGE_STEPS = 3      # "đầu" và "cuối" của cửa sổ = trung bình 3 bước
FEATURE_EPS = 1e-8          # chặn chia cho 0 trong horiz_ratio và straightness

FIG_DPI = 150               # mọi hình xuất ra .png

# Màu cho hình báo cáo (bảng màu tham chiếu của skill dataviz, chế độ sáng).
# Ý nghĩa theo vai trò, không theo thứ hạng: ACCENT là nhóm đang được nói tới,
# DEEMPH là phần còn lại; SEQ_RAMP là dải một màu nhạt → đậm cho độ lớn.
FIG_SURFACE = "#fcfcfb"
FIG_INK = "#0b0b0b"
FIG_INK_2 = "#52514e"
FIG_GRID = "#e1e0d9"
FIG_AXIS = "#c3c2b7"
FIG_ACCENT = "#2a78d6"
FIG_DEEMPH = "#898781"
FIG_SEQ_RAMP = ("#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5",
                "#256abf", "#184f95", "#0d366b")
FIG_SEQ_DARK_TEXT_BELOW = 0.45   # ô có giá trị chuẩn hoá dưới mức này viết chữ
                                 # màu mực, từ mức này trở lên viết chữ trắng
FIG_CATEGORICAL = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")
                                 # bốn ô đầu của bảng màu hạng mục, thứ tự CỐ ĐỊNH
                                 # theo MODEL_NAMES (màu đi theo mô hình, không theo
                                 # thứ hạng). Kiểm bằng validate_palette.js 2026-10-22:
                                 # đạt mọi ngưỡng; aqua, vàng dưới 3:1 trên nền sáng
                                 # nên hình luôn đi kèm bảng số


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
