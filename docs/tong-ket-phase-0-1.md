# Tổng kết Phase 0 và Phase 1

**Đề tài:** Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính
**Phạm vi tài liệu:** chỉ những gì đã triển khai ở Phase 0 (khung dự án) và
Phase 1 (thu nhận điểm mốc, hiệu chuẩn quy ước).
**Trạng thái tại thời điểm viết:** 13/13 kiểm thử xanh. Phần code của cả hai
phase đã xong; Phase 1 còn chờ các phép đo do con người thực hiện (mục 7).

---

## 1. Tóm tắt một đoạn

Hai phase đầu dựng xong **nền móng** cho toàn bộ đề tài: một cây thư mục cố
định, một file cấu hình duy nhất chứa mọi hằng số, môi trường Python được kích
hoạt tự động, và một **đường ống thu nhận điểm mốc** dùng chung cho mọi nguồn
ảnh. Chạy `python scripts/live_landmarks.py` là thấy 21 điểm mốc khung xương
bàn tay bám theo tay trên webcam, kèm FPS. Ngoài ra đã có công cụ ghi điểm mốc
ra CSV, công cụ **đo** hằng số quy ước hướng `SWIPE_LEFT_SIGN`, và bộ công cụ
chạy 9 thí nghiệm quan sát để lượng hoá giới hạn của MediaPipe trên máy thật.

Chưa có gì về phân loại cử chỉ — đó là việc từ Phase 2 trở đi.

---

## 2. Phase 0 — Khung dự án

### 2.1. Đã làm

| Hạng mục | Nội dung |
|---|---|
| Cây thư mục | `models/`, `data/{ipn,raw,landmarks,windows}/`, `src/`, `scripts/`, `tests/`, `notebooks/`, `results/`; `data/landmarks/` chia sẵn theo ba nguồn `ipn`, `self`, `webcam` |
| `src/config.py` | Nơi **duy nhất** chứa hằng số. Mọi đường dẫn suy ra từ `ROOT = Path(__file__).resolve().parents[1]` — không có đường dẫn tuyệt đối |
| `require_measured(name)` | Hằng số quy ước còn `None` thì ném `RuntimeError("Chưa đo SWIPE_LEFT_SIGN — xem Phase 1")`. Chặn lỗi "chạy ngược chiều mà không báo gì" |
| `CLAUDE.md` | 12 quy ước bất di bất dịch + mục môi trường |
| `README.md` | Cài đặt, tải mô hình và dữ liệu, bảng hằng số đã đo (còn trống), thứ tự chạy script |
| `requirements.txt`, `pytest.ini` | Chưa ghim phiên bản (ghim ở Phase 11); `testpaths = tests`, `pythonpath = .` |
| Môi trường conda | Env `action-recognition`, Python 3.10.21. Hook `SessionStart` trong `.claude/settings.json` tự kích hoạt env cho mọi lệnh của Claude Code |
| Mô hình | `models/hand_landmarker.task` (7,8 MB) |

### 2.2. Hằng số nền tảng trong `config.py`

| Hằng số | Giá trị | Ý nghĩa |
|---|---|---|
| `CLASSES` | `none, swipe_left, swipe_right, zoom_in, zoom_out` | Thứ tự cố định, `none` luôn là chỉ số 0 |
| `WRIST`, `MIDDLE_MCP` | `0`, `9` | Gốc toạ độ và đơn vị đo "cỡ lòng bàn tay" |
| `TIPS` | `[4, 8, 12, 16, 20]` | Năm đầu ngón |
| `HZ`, `WIN_SEC`, `STRIDE_SEC` | `15.0`, `1.2`, `0.2` | Cửa sổ tính bằng **giây**; `T = round(1.2 × 15) = 18` bước |
| `MAX_GAP`, `MIN_PRESENCE`, `LABEL_COVERAGE` | `3`, `0.7`, `0.6` | Dùng từ Phase 2 và 5 |
| `SWIPE_LEFT_SIGN` | `None` | **Chưa đo** — đo ở Phase 1 |
| `IPN_FLIP_X` | `None` | **Chưa đo** — đo ở Phase 4 |
| `CAM_W`, `CAM_H`, `CAM_FPS` | `640`, `480`, `30` | Trùng độ phân giải và tỉ lệ khung hình với IPN Hand |
| `SEED` | `42` | Tái lập |

### 2.3. Định nghĩa hoàn thành — đạt 5/5

| Mục | Kết quả |
|---|---|
| `import mediapipe, cv2, torch, sklearn` | ✅ |
| `cv2.VideoCapture(0).isOpened()` | ✅ `True` |
| `pytest -q` ≥ 5 kiểm thử | ✅ 5 passed |
| `models/hand_landmarker.task` tồn tại | ✅ và mở ra đúng hai mô hình con |
| Không số ma thuật ngoài `config.py` | ✅ |

---

## 3. Phase 1 — Thu nhận điểm mốc và hiệu chuẩn quy ước

### 3.1. Kiến trúc: một đường ống, ba nguồn

```
 webcam ─┐
         ├─► iter_frames ─► HandTracker ─► (xy, present, score, handedness)
 video ──┘   (frame_bgr,    BGR→RGB,          │
              ts giây)      không lật,         ├─► FrameCsvWriter ─► landmarks.csv
                            NaN khi mất tay    └─► make_display ─► cửa sổ (ảnh gương)
```

Dữ liệu IPN, video tự quay và webcam lúc chạy thật đều đi qua **cùng**
`iter_frames` và **cùng** `HandTracker`. Không có hai bản "gần giống nhau".

### 3.2. Các module trong `src/`

| File | Vai trò |
|---|---|
| `io_video.py` | `iter_frames(source)` — cửa vào duy nhất. Webcam: mốc thời gian từ đồng hồ thật `perf_counter`. Video: `chỉ số frame / FPS`, đọc tuần tự |
| `hands.py` | `HandTracker` — MediaPipe Hand Landmarker, `num_hands=1`, chế độ VIDEO. Đổi BGR→RGB bên trong; không lật ảnh; mất tay trả mảng NaN `(21, 2)` |
| `recording.py` | Ghi/đọc CSV mỗi frame một dòng; vòng lặp ghi dùng chung |
| `display.py` | Nơi **duy nhất** lật ảnh — chỉ bản cho người xem |
| `fps.py` | FPS trượt 30 frame để hiển thị; FPS trung bình và "1% low" sau 3 giây khởi động để báo cáo |
| `calibration.py` | Tính `dx` từng lần vuốt và quyết định dấu `SWIPE_LEFT_SIGN` |
| `observations.py` | Chỉ số thí nghiệm: tỉ lệ phát hiện, đợt mất tay, độ rung, σ |
| `runlog.py` | `results/<phase>/<tên>/run_NN/` + `manifest.json` |
| `tables.py` | Xuất bảng song song `.csv` và `.md` |
| `cli.py` | Tiện ích dòng lệnh, in tiếng Việt an toàn trên Windows |

### 3.3. Các script trong `scripts/`

| Script | Làm gì |
|---|---|
| `live_landmarks.py` | Xem 21 điểm mốc + khung xương + FPS trên webcam |
| `record_csv.py` | Ghi điểm mốc ra CSV |
| `measure_swipe_sign.py` | Quy trình có hướng dẫn: 10 lần vuốt trái → in dòng `SWIPE_LEFT_SIGN = ±1` để dán vào `config.py`. **Không** tự sửa config |
| `observe.py` | Chạy một trong 9 thí nghiệm quan sát, ghi CSV |
| `analyze_observations.py` | Gộp mọi lần chạy thành bảng số liệu và tính σ |

### 3.4. Định dạng CSV điểm mốc

```
ts, present, score, handedness, w, h, x0..x20, y0..y20
```

Ví dụ thật từ video IPN:

```
0.800000,1,0.980344,Right,640,480,0.385719,0.336916,...
0.000000,0,,,640,480,,,,,,...
```

Dòng thứ hai là frame **không thấy tay**: vẫn có mốc thời gian và kích thước
khung, toạ độ để trống. Toạ độ lưu ở dạng chuẩn hoá của MediaPipe kèm `w`, `h`;
đổi sang pixel là bước đầu của đường ống ở Phase 2.

### 3.5. Mỗi lần chạy đều tái lập được

Mỗi lần chạy sinh một `manifest.json`, ví dụ:

```
command   : python scripts/observe.py --exp e9_jitter --source ... --seconds 3 --no-display
started_at: 2026-09-21T21:09:34
seed      : 42
versions  : python 3.10.21, numpy 2.2.6, cv2 5.0.0, mediapipe 1.0.1
config    : 76 hằng số (đường dẫn ghi tương đối)
```

### 3.6. Chín thí nghiệm quan sát

Tám thí nghiệm theo cẩm nang bước 6, cộng thí nghiệm 6.9 tách riêng:

| Tên | Đo gì |
|---|---|
| `e1_distance` | Tỉ lệ phát hiện và độ rung đầu ngón trỏ ở 0,3 / 0,5 / 0,7 / 1,0 m |
| `e2_swipe_speed` | Tỉ lệ phát hiện khi vuốt chậm và nhanh; số lần mất tay; đợt mất dài nhất |
| `e3_open_close` | Phát hiện khi chụm so với khi xòe |
| `e4_lighting` | FPS và tỉ lệ phát hiện ở phòng sáng và phòng tối |
| `e5_context` | Tay trước mặt / trên bàn phím / cầm cốc |
| `e6_handedness` | Nhãn Left/Right trong 4 trường hợp (tay trái/phải × ảnh lật/không lật) |
| `e7_reenter` | Số frame để điểm mốc xuất hiện lại sau khi tay vào lại khung |
| `e8_wrist_tilt` | Cổ tay nghiêng 45° và 90° |
| `e9_jitter` | Tay bất động → σ cho tăng cường nhiễu Gauss ở Phase 5 |

### 3.7. Kiểm thử

| Kiểm thử | Canh giữ điều gì |
|---|---|
| `test_hands_tra_ve_nan_tren_anh_den` | Ảnh đen → `present=False`, xy toàn NaN, không trả `None` |
| `test_iter_frames_ts_tang_don_dieu` | Video tổng hợp: đủ frame, `ts[0]=0`, tăng ngặt đúng `1/FPS` |
| `test_hands_khong_lat_anh_dau_vao` | Đọc mã nguồn `hands.py`: không có phép lật nào |
| `test_record_csv_giu_dong_khi_mat_tay` | Số dòng = số frame; dòng mất tay có `ts`, toạ độ trống |
| `test_iter_frames_bao_loi_khi_thieu_file` | Thiếu file → lỗi rõ ràng |
| `test_decide_sign_chi_ket_luan_khi_dut_khoat` | Chỉ kết luận dấu khi đủ lần hợp lệ và mọi lần cùng dấu |
| `test_rep_dx_bo_qua_frame_mat_tay` | `dx` lấy từ frame có tay đầu và cuối |
| `test_display_khong_sua_frame_goc` | Lật chỉ xảy ra trên bản hiển thị |
| 5 kiểm thử của Phase 0 | Hằng số, `T = 18`, đường dẫn, `require_measured` |

Ngoài kiểm thử, toàn bộ đường đi đã chạy thật trên một video IPN (không cửa
sổ): 121 frame → 121 dòng CSV, thấy tay ở 97 frame; chạy lại cho số liệu giống
hệt.

---

## 4. Lý thuyết thị giác máy tính đã dùng

Chỉ những khái niệm thực sự xuất hiện trong code của hai phase này.

### 4.1. Ảnh số là một mảng số

Một frame màu là mảng `numpy` kích thước `(H, W, 3)`, kiểu `uint8` (0–255).
Với webcam 640×480, `frame.shape == (480, 640, 3)` — **chiều cao đứng trước**.

Hệ toạ độ ảnh có gốc ở góc **trên trái**, trục `x` sang phải, trục `y` đi
**xuống**. Có một chỗ dễ nhầm: mảng được truy cập theo `[y, x]` (hàng trước
cột), còn các hàm vẽ của OpenCV nhận điểm theo `(x, y)`. Trong
`display.py`, mọi điểm vẽ đều là `(int(x * w), int(y * h))`.

### 4.2. BGR và RGB — lỗi im lặng phổ biến nhất

OpenCV lưu kênh màu theo thứ tự **BGR**, MediaPipe cần **RGB**. Quên đổi thì
MediaPipe **không báo lỗi** — nó chỉ phát hiện kém đi, vì với mạng nơ-ron đã
học trên ảnh RGB, da người lúc này mang màu xanh lam. Đề tài đổi kênh màu ở
**đúng một chỗ**, bên trong `HandTracker.process`, và đặt tên biến
`frame_bgr` / `frame_rgb` để mắt tự bắt lỗi.

### 4.3. Video, FPS và mốc thời gian

- **FPS webcam không phải hằng số.** Phòng tối thì camera kéo dài thời gian
  phơi sáng và FPS tụt. Vì vậy mỗi frame webcam được gắn mốc thời gian thật
  bằng `time.perf_counter()` ngay khi đọc xong — việc này không bổ sung được
  sau khi đã quay.
- **File video** thì mốc thời gian là `chỉ số frame / FPS của file`, và phải
  đọc **tuần tự**. Nhảy frame bằng `CAP_PROP_POS_FRAMES` vừa chậm vừa có thể
  lệch với nhiều codec.
- **Đo FPS đúng cách:** bỏ 3 giây đầu (camera còn tự chỉnh), báo cả FPS trung
  bình lẫn "1% low" — phân vị thấp của FPS tức thời. FPS trung bình cao vẫn có
  thể che giấu những lần giật cục.

Mốc thời gian không đều giữa các frame chính là lý do Phase 2 phải lấy mẫu lại
về lưới đều 15 Hz.

### 4.4. Toạ độ chuẩn hoá và tỉ lệ khung hình

MediaPipe trả `x`, `y` trong `[0, 1]`, chia theo chiều rộng và chiều cao ảnh.
Hai trục này có đơn vị **khác nhau** khi ảnh không vuông: với 640×480, một đơn
vị `x` dài 640 px nhưng một đơn vị `y` chỉ dài 480 px. Tính khoảng cách hay góc
trực tiếp trên toạ độ chuẩn hoá vì thế sẽ méo. Vì lý do này:

- CSV lưu toạ độ chuẩn hoá **kèm** `w`, `h`, để Phase 2 đổi sang pixel trước
  mọi phép tính hình học.
- Camera cố định ở 640×480 — trùng tỉ lệ khung hình với IPN Hand (đã kiểm:
  video IPN là 640×480 @ 30 fps), loại bỏ hẳn một nguồn khác biệt giữa hai
  nguồn dữ liệu.

### 4.5. Quy ước lật ảnh

| Ảnh | Lật? | Vì sao |
|---|---|---|
| Đưa **vào mô hình** | **Không** | Phải cùng quy ước với dữ liệu huấn luyện. Đổi quy ước giữa chừng là cách chắc chắn nhất để hệ thống chạy ngược |
| Đưa **ra màn hình** | **Lật gương** | Người dùng cần ảnh gương để điều khiển tự nhiên |

Hệ quả: khi vẽ lên ảnh đã lật, toạ độ `x` cũng phải lật thành `1 − x`. Việc này
nằm gọn trong `make_display`.

### 4.6. Ước lượng tư thế bàn tay và 21 điểm mốc

Bài toán: từ một ảnh, tìm vị trí 21 điểm mốc (keypoint) trên khung xương bàn
tay.

| Ngón | Gốc → đầu ngón | Ghi chú |
|---|---|---|
| Cổ tay | 0 | `WRIST` — gốc toạ độ khi chuẩn hoá |
| Cái | 1, 2, 3, **4** | |
| Trỏ | 5, 6, 7, **8** | `INDEX_TIP = 8` — dùng đo độ rung |
| Giữa | **9**, 10, 11, **12** | `MIDDLE_MCP = 9` — đoạn 0 → 9 là đơn vị "cỡ lòng bàn tay" |
| Nhẫn | 13, 14, 15, **16** | |
| Út | 17, 18, 19, **20** | |

Năm đầu ngón `TIPS = [4, 8, 12, 16, 20]`. Các đoạn nối để vẽ khung xương lấy
từ `HandLandmarksConnections.HAND_CONNECTIONS` của MediaPipe, không tự khai
báo.

MediaPipe Hand Landmarker dùng **kiến trúc hai tầng** — file `.task` chứa đúng
hai mô hình con, `hand_detector.tflite` và `hand_landmarks_detector.tflite`:

1. **Bộ phát hiện lòng bàn tay** tìm vùng chứa bàn tay trong cả ảnh. Nó phát
   hiện lòng bàn tay chứ không phải cả bàn tay, vì lòng bàn tay là vật cứng,
   ít biến dạng hơn các ngón.
2. **Mô hình điểm mốc** chạy trên vùng đã cắt, hồi quy ra 21 điểm.

Ở **chế độ VIDEO**, frame sau dùng vị trí tay của frame trước để cắt vùng,
**bỏ qua** bộ phát hiện — nhanh hơn nhiều. Khi mất dấu (tay ra khỏi khung, hoặc
vuốt quá nhanh làm ảnh nhoè), bộ phát hiện phải chạy lại: đó là lúc điểm mốc
biến mất vài frame. Thí nghiệm `e2` và `e7` đo đúng hiện tượng này. Chế độ VIDEO
đòi mốc thời gian tăng ngặt, nên `HandTracker` tự đẩy mốc lên 1 ms nếu hai frame
trùng mốc.

**Ba ngưỡng tin cậy**, mỗi ngưỡng ứng với một chỗ trong kiến trúc, đều để mặc
định 0,5 cho tới khi có số đo:

| Tham số | Kiểm soát |
|---|---|
| `min_hand_detection_confidence` | Bộ phát hiện lòng bàn tay chấp nhận một phát hiện |
| `min_hand_presence_confidence` | Cờ hiện diện của mô hình điểm mốc; dưới ngưỡng thì chạy lại bộ phát hiện |
| `min_tracking_confidence` | Việc bám từ frame trước được coi là thành công |

**Chỉ dùng toạ độ 2D.** MediaPipe có trả thêm `z` (độ sâu tương đối) và
`hand_world_landmarks` (toạ độ 3D theo mét), nhưng độ sâu từ một camera là ước
lượng không tin cậy. Đề tài bỏ hẳn.

**Handedness.** MediaPipe trả nhãn `Left`/`Right` kèm điểm tin cậy, nhưng giả
định ảnh đầu vào đã lật gương. Vì đề tài không lật, nhãn này có thể **ngược**
với tay thật — thí nghiệm `e6` đo quy ước thực tế. Đề tài không dựa vào nhãn
này cho quyết định nào.

### 4.7. Frame mất tay là một tín hiệu, không phải rác

Khi không thấy tay, đường ống ghi **NaN** chứ không bỏ frame. Bỏ frame làm đứt
trục thời gian: các bước sau sẽ nội suy qua khoảng trống mà không ai biết. Giữ
NaN thì thông tin "lúc này không có tay" còn nguyên, và Phase 2 quyết định vá
(lỗ ngắn) hay giữ (lỗ dài).

### 4.8. Đo lường giới hạn của bộ ước lượng

| Chỉ số | Định nghĩa |
|---|---|
| Tỉ lệ phát hiện | Số frame thấy tay / tổng số frame |
| Đợt mất tay | Số lần chuyển từ thấy sang mất; đợt mất dài nhất (frame và giây) |
| Độ rung `*_std_px` | Độ lệch chuẩn của từng toạ độ theo thời gian (pixel), gộp bằng căn trung bình bình phương. Định nghĩa của cẩm nang 6.9 — chỉ có nghĩa khi tay đứng yên |
| Độ rung `*_diff_px` | `std(chênh lệch giữa hai frame liền nhau) / √2`. Không nhạy với việc cả bàn tay trôi chậm, dùng để đối chiếu |
| `sigma_std_palm` | σ chia cho cỡ lòng bàn tay (khoảng cách điểm 0 → 9) — không phụ thuộc khoảng cách tới camera |

`√2` xuất hiện vì nếu mỗi frame có nhiễu độc lập độ lệch chuẩn σ, thì hiệu của
hai frame có độ lệch chuẩn `σ√2`.

### 4.9. Quy ước thì đo, không đoán — `SWIPE_LEFT_SIGN`

"Vuốt trái" làm `x` tăng hay giảm phụ thuộc hai quy ước: ảnh có lật không, và
"trái" hiểu theo người làm hay theo ảnh. Suy luận cho rằng với ảnh không lật,
tay đi sang trái của người làm sẽ đi về phía **phải của ảnh** (`dx > 0`) —
nhưng đề tài **không dùng suy luận đó**. Quy trình đo:

1. Mỗi lần vuốt: `dx = x_cổ tay(frame có tay cuối) − x_cổ tay(frame có tay đầu)`,
   trên ảnh **không lật**.
2. Một lần hợp lệ khi đủ frame thấy tay và `|dx| ≥ 0,10` chiều rộng khung.
3. Chỉ kết luận khi ít nhất 70% số lần hợp lệ và **mọi** lần hợp lệ cùng dấu;
   dấu của trung vị là `SWIPE_LEFT_SIGN`.
4. Chạy ba lần độc lập; ba lần phải cùng dấu.

Nếu bỏ qua bước này, mô hình học ngược hướng và không có gì báo lỗi.

---

## 5. Thư viện và mô hình

| Thành phần | Phiên bản | Dùng vào việc gì ở Phase 0–1 |
|---|---|---|
| Python | 3.10.21 | Env conda `action-recognition` |
| OpenCV (`opencv-python`) | 5.0.0 | Đọc webcam và video, đổi BGR→RGB, lật ảnh hiển thị, vẽ khung xương, cửa sổ |
| MediaPipe | 1.0.1 | Hand Landmarker (Tasks API): `HandLandmarker`, `RunningMode.VIDEO`, `HandLandmarksConnections` |
| NumPy | 2.2.6 | Mọi mảng điểm mốc, NaN, thống kê |
| pytest | 9.1.1 | Kiểm thử |
| PyTorch | 2.14.0+cpu | **Đã cài, chưa dùng** (LSTM ở Phase 7). Bản CPU, không CUDA |
| scikit-learn | 1.7.2 | **Đã cài, chưa dùng** (rừng ngẫu nhiên ở Phase 6) |
| pandas | 2.3.3 | **Đã cài, chưa dùng** |
| matplotlib | 3.10.9 | **Đã cài, chưa dùng** (đồ thị từ Phase 2) |

**Mô hình:** `hand_landmarker.task`, bản float16 phiên bản 1, tải từ kho mô hình
của MediaPipe, 7,8 MB. Là một file zip chứa `hand_detector.tflite` và
`hand_landmarks_detector.tflite`.

Ghi chú: MediaPipe 1.0.1 là một major version mới. Đã kiểm tra API cần cho
Phase 1 vẫn còn nguyên. Nên ghim đúng phiên bản này ở Phase 11.

---

## 6. Dữ liệu

### 6.1. IPN Hand

Bộ dữ liệu cử chỉ bàn tay cho tương tác không chạm, là dữ liệu huấn luyện chính
của đề tài. Số liệu dưới đây đếm trực tiếp từ các file trên đĩa:

| Thuộc tính | Giá trị |
|---|---|
| Số video | 200 (148 train, 52 test theo `metadata.csv`) |
| Tổng số frame | 800 505 |
| Định dạng video | `.avi`, 640×480 @ 30 fps |
| Số đoạn đã gán nhãn | 5 649 (`Annot_List.txt`); 4 039 train, 1 610 test |
| Số lớp | 14, gồm 1 lớp không-cử-chỉ |
| Điều kiện ghi | Nền `Plain` / `Clutter`; ánh sáng `Stable` / `Light` / `Dark` |

| Nhãn | Cử chỉ | Số đoạn |
|---|---|---|
| D0X | Non-gesture | 1 431 |
| B0A | Pointing with one finger | 1 010 |
| B0B | Pointing with two fingers | 1 007 |
| G01 | Click with one finger | 200 |
| G02 | Click with two fingers | 200 |
| G03 | Throw up | 200 |
| G04 | Throw down | 201 |
| G05 | Throw left | 200 |
| G06 | Throw right | 200 |
| G07 | Open twice | 200 |
| G08 | Double click with one finger | 200 |
| G09 | Double click with two fingers | 200 |
| G10 | Zoom in | 200 |
| G11 | Zoom out | 200 |

File nhãn có dạng `video, label, id, t_start, t_end, frames` — mỗi dòng là một
đoạn cử chỉ trong một video dài.

**Dùng tới đâu ở Phase 0–1:** mới **đặt lên đĩa** ở `data/ipn/` và dùng **một**
video làm phép chạy thử đường ống (thấy tay ở 97/121 frame). Việc trích điểm mốc
toàn bộ, ánh xạ 14 lớp về 5 lớp của đề tài và kiểm chứng `IPN_FLIP_X` thuộc
Phase 4.

### 6.2. Dữ liệu tự quay

Chưa có. Thư mục `data/raw/` đã sẵn sàng với quy ước tên
`p03_swipe_left_07.mp4`. Quay ở Phase 4.

### 6.3. Webcam

Nguồn thời gian thực, 640×480. Đã xác nhận mở được trong env. Dữ liệu webcam ở
Phase 1 là các CSV từ `measure_swipe_sign.py` và `observe.py` — **chưa ghi lần
nào**.

---

## 7. Việc còn mở để đóng Phase 1

Phần code đã xong. Các mục còn lại của Định nghĩa hoàn thành cần người thực
hiện:

| Mục | Trạng thái |
|---|---|
| `live_landmarks.py` vẽ 21 điểm bám theo tay, có FPS | Chưa có người xác nhận bằng mắt trên webcam |
| CSV có tay ra vào khung: số dòng = số frame | ✅ đã chứng minh bằng kiểm thử và chạy thật trên video IPN |
| `measure_swipe_sign.py` cùng dấu qua ba lần chạy | **Chưa chạy** |
| `SWIPE_LEFT_SIGN` điền vào `config.py`; kiểm thử Phase 0 chuyển sang "nhận ±1" | **Chưa** — hiện vẫn là `None` |
| `results/phase1/` có số liệu của các thí nghiệm quan sát | **Chưa có** — `results/` đang trống |
| `pytest -q` xanh | ✅ 13 passed |

Khi dán `SWIPE_LEFT_SIGN`, kiểm thử `test_require_measured_nem_loi` sẽ đỏ theo
đúng dự tính và cần được cập nhật.

---

## 8. Các quyết định đã chốt trong hai phase

| Quyết định | Lý do |
|---|---|
| `HandTracker.process()` trả 4 giá trị (thêm `handedness`) thay vì 3 như spec | Cẩm nang 3.6 và thí nghiệm 6 cần nhãn Left/Right. Người dùng chọn |
| Cờ `--flip-input` **chỉ** trong `observe.py`, chỉ dùng được với `e6_handedness` | Thí nghiệm 6 cần ảnh lật vào mô hình; luật 11 vẫn giữ nguyên ở mọi chỗ khác. Người dùng chọn |
| Mặc định 10 lần vuốt khi đo dấu (spec nói 5) | Theo cẩm nang 4.3; trung vị trên 10 giá trị bền hơn. Người dùng chọn |
| σ báo theo cả pixel lẫn cỡ lòng bàn tay | Spec đòi pixel, cẩm nang 6.9 đòi cỡ lòng bàn tay. Chọn đơn vị ở Phase 5 |
| Thêm thí nghiệm `e9_jitter` | Cẩm nang 6.9 cần một lần ghi tay bất động riêng để lấy σ |
| Chỉ kết luận dấu khi mọi lần hợp lệ cùng dấu | Một lần vuốt trái cho dấu ngược là tín hiệu phải đo lại, không phải nhiễu để bỏ qua |
| README cũ (mục lục tài liệu lý thuyết) chuyển sang `docs/README.md` | Nhường chỗ cho README của code; các liên kết trong đó trỏ tương đối tới `docs/` nên chuyển vào đó mới đúng |
| Kích hoạt conda env bằng hook `SessionStart` | Mọi lệnh của Claude Code tự chạy trong Python 3.10, không lẫn Python 3.11 của hệ thống |
