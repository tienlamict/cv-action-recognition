# Lộ trình phát triển chi tiết
## Điều khiển trình chiếu bằng cử chỉ bàn tay qua webcam — MediaPipe Hand Landmarker + IPN Hand

> **Tài liệu này là gì.** Một chuỗi **23 bước tuần tự** trong 10 tuần, thay thế
> cẩm nang cũ (nhận dạng hành động toàn thân) sau khi đề tài chuyển hướng theo
> góp ý của giảng viên. Mỗi bước nói rõ phải hiểu gì trước khi làm, làm gì,
> kiểm chứng thế nào, và để lại sản phẩm gì.
>
> **Quan hệ với tài liệu cũ.** Tài liệu tầng 1 (ảnh số), tầng 4 (mô hình chuỗi)
> và tầng 5 (đánh giá) **dùng nguyên**. Tầng 2 (ước lượng tư thế) và tầng 3
> (biểu diễn khung xương) được **viết lại cho bàn tay** ngay trong tài liệu này.
> Có thêm một tầng mới — tầng 6: nhận dạng cử chỉ trong luồng liên tục.
>
> Đọc theo thứ tự. Mỗi bước giả định các bước trước đã xong.

---

## 0. Tổng quan

### 0.1. Cấu trúc một bước

| Mục | Ý nghĩa |
|---|---|
| **Mục tiêu** | Một câu: sau bước này bạn có gì mà trước đó chưa có |
| **Lý thuyết cần nắm** | Khái niệm phải hiểu *trước khi* gõ dòng code đầu tiên, kèm câu tự kiểm tra |
| **Việc cụ thể** | Hành động theo thứ tự |
| **Kiểm chứng** | Cách tự chứng minh bước này làm đúng |
| **Sản phẩm** | Thứ để lại cho báo cáo hoặc cho bước sau |
| **Cạm bẫy** | Lỗi phổ biến ở đúng bước này |

### 0.2. Phạm vi đã chốt

| Hạng mục | Quyết định |
|---|---|
| Kịch bản | Một người **ngồi trước laptop** như làm việc bình thường, cách camera khoảng 0,4–0,7 m |
| Phần cứng | ThinkPad X1 Carbon Gen 9, webcam 720p lấy nét cố định, CPU Intel thế hệ 11, Windows, không GPU rời |
| Ước lượng tư thế | MediaPipe **Hand Landmarker** — 21 điểm mốc, một bàn tay |
| Dữ liệu chính | **IPN Hand** (50 người, 640×480, 30 FPS, video liên tục có gán nhãn thời gian) |
| Dữ liệu kiểm thử | Tự quay: 4–6 người, đúng laptop và tư thế sẽ demo |
| Dữ liệu bổ sung (tùy chọn) | Jester — chỉ dùng như một thí nghiệm ở tuần 8 |
| Lớp nhận dạng | 5 lớp: vuốt trái, vuốt phải, xòe tay, chụm tay, không cử chỉ |
| Lệnh | Vuốt trái → slide tiếp (→), vuốt phải → slide trước (←), xòe → phóng to (+), chụm → thu nhỏ (−) |
| Không làm | Nhiều người, hai tay cùng lúc, đứng xa, cử chỉ tĩnh, điều khiển con trỏ chuột |

### 0.3. Kiến trúc hệ thống đích

```
Webcam 30 FPS
  → BGR→RGB → Hand Landmarker (VIDEO, 1 tay) → 21 điểm (x, y) + có tay / không
  → đổi sang pixel → lấy mẫu lại 15 Hz theo thời gian → vá lỗ hổng ngắn
  → hàng đợi T bước gần nhất (≈ 1 giây)
  → chuẩn hóa cửa sổ (gốc = cổ tay frame đầu, đơn vị = cỡ lòng bàn tay)
  → bộ phân loại 5 lớp (luật / RF / LSTM), chạy mỗi 2 bước
  → logic kích hoạt (ngưỡng + liên tiếp + nhả + khóa chiều ngược)
  → pyautogui gửi phím → PowerPoint đang trình chiếu
```

Ba khối có nội dung học thuật chính: **ước lượng tư thế bàn tay** (bạn phải
hiểu mô hình có sẵn làm gì), **biểu diễn và mô hình chuỗi** (bạn tự thiết kế và
huấn luyện), **phát hiện cử chỉ trong luồng liên tục** (bạn tự thiết kế và đánh
giá). Các khối còn lại là kỹ thuật.

### 0.4. Bản đồ tầng lý thuyết

| Tầng | Nội dung | Tài liệu |
|---|---|---|
| 0 | Công cụ: conda, git, numpy, đọc traceback | Bước 2 |
| 1 | Ảnh số, video, camera | `01-anh-so-va-video.md` + Bước 5 |
| 2 | Ước lượng tư thế **bàn tay** | Bước 6, 7 (thay `02`) |
| 3 | Biểu diễn khung xương **bàn tay**, đặc trưng | Bước 9, 10 (thay `03`) |
| 4 | Mô hình chuỗi: cửa sổ trượt, RF, RNN, LSTM | `04-mo-hinh-chuoi-thoi-gian.md` + Bước 13, 15, 18 |
| 5 | Đánh giá phân loại, rò rỉ dữ liệu | `05-danh-gia-phan-loai.md` + Bước 16 |
| 6 | **Mới:** nhận dạng cử chỉ liên tục, kích hoạt, đánh giá mức sự kiện, tương tác người–máy | Bước 1, 20, 22 |

### 0.5. Bản đồ: 23 bước ↔ tầng ↔ tuần

| Bước | Nội dung | Tầng | Tuần |
|---|---|---|---|
| 1 | Đóng khung bài toán, định nghĩa cử chỉ | 6 | 1 |
| 2 | Môi trường và cấu trúc dự án | 0 | 1 |
| 3 | Hand Landmarker chạy trên webcam | 1, 2 | 1 |
| 4 | Chuỗi đầu–cuối: từ bàn tay tới PowerPoint | 6 | 1 |
| 5 | Ảnh số, video và camera của bạn | 1 | 2 |
| 6 | Lý thuyết ước lượng tư thế bàn tay | 2 | 2–3 |
| 7 | Thí nghiệm quan sát Hand Landmarker | 2 | 3 |
| 8 | Làm quen IPN Hand, chốt ánh xạ lớp | 5 | 3 |
| 9 | Chuẩn hóa chuỗi điểm mốc | 3 | 4 |
| 10 | Thiết kế đặc trưng | 3 | 4 |
| 11 | Mô hình 0 — luật, và demo đầu tiên | 3, 6 | 4 |
| 12 | Trích điểm mốc từ IPN Hand | 2, 3 | 5 |
| 13 | Tiền xử lý chuỗi, cắt cửa sổ, gán nhãn, chia tập | 4, 5 | 5 |
| 14 | Tự quay dữ liệu kiểm thử | 5 | 5 |
| 15 | Mô hình 1 — rừng ngẫu nhiên | 4 | 6 |
| 16 | Đánh giá mức cửa sổ đúng cách | 5 | 6 |
| 17 | PyTorch và đường ống dữ liệu | 4 | 7 |
| 18 | Mô hình 2 — LSTM và tăng cường dữ liệu | 4 | 7–8 |
| 19 | Các thí nghiệm khảo sát | 4, 5 | 8 |
| 20 | Logic kích hoạt | 6 | 9 |
| 21 | Tích hợp, đo FPS và độ trễ | 1, 6 | 9 |
| 22 | Đánh giá mức sự kiện và thử nghiệm người dùng | 5, 6 | 9 |
| 23 | Báo cáo, repo, bảo vệ | tất cả | 10 |

**Ba mốc an toàn.** Cuối tuần 1: chuỗi bàn tay → phím chạy được. Cuối tuần 4:
demo điều khiển slide bằng luật. Cuối tuần 6: hệ thống học máy hoàn chỉnh có
đánh giá. Từ mốc tuần 6, dù có chuyện gì xảy ra bạn vẫn có thứ để nộp.

### 0.6. Cấu trúc thư mục dự án

```
gesture-slides/
├── models/
│   └── hand_landmarker.task
├── data/
│   ├── ipn/
│   │   ├── videos/            # 200 file .mp4 gốc
│   │   ├── annotations/       # các file .txt/.csv của IPN
│   │   └── landmarks/         # .npz trích ra ở bước 12
│   ├── own/
│   │   ├── raw/               # video tự quay
│   │   ├── labels/            # nhãn thời gian tự gán
│   │   └── landmarks/
│   └── windows/               # cửa sổ đã cắt, sẵn sàng huấn luyện
├── src/
│   ├── config.py              # hằng số: tên lớp, tần số, độ dài cửa sổ...
│   ├── camera.py
│   ├── landmarks.py           # gọi Hand Landmarker, vẽ
│   ├── preprocess.py          # lấy mẫu lại, vá lỗ, chuẩn hóa
│   ├── features.py
│   ├── windows.py
│   ├── models_rule.py
│   ├── models_rf.py
│   ├── models_lstm.py
│   ├── trigger.py
│   ├── actions.py             # gửi phím
│   └── app.py                 # chương trình demo
├── scripts/                   # 01_extract_ipn.py, 02_make_windows.py, ...
├── notebooks/                 # khám phá dữ liệu, vẽ hình
├── reports/figures/
├── notes/                     # ghi chú lý thuyết theo từng bước
└── README.md
```

### 0.7. Bốn nguyên tắc xuyên suốt

**Nguyên tắc 1 — Mọi khâu đều phải nhìn thấy được.** Khi có lỗi, luôn hỏi
trước: *hỏng ở điểm mốc hay ở phân loại?* Vẽ 21 điểm lên video là cách trả lời
nhanh nhất. Nếu điểm mốc đã sai, không mô hình nào cứu được.

**Nguyên tắc 2 — Một hàm tiền xử lý duy nhất cho mọi nguồn.** Dữ liệu IPN, dữ
liệu tự quay và luồng webcam lúc chạy thật phải đi qua **cùng một đoạn code**
lấy mẫu lại, vá lỗ, chuẩn hóa. Hai phiên bản code "gần giống nhau" là nguồn lỗi
âm thầm số một của các hệ thống kiểu này: mô hình đạt 90% khi đánh giá nhưng
chạy thật thì loạn.

**Nguyên tắc 3 — Viết ghi chú lý thuyết ngay khi học.** Mỗi bước có phần lý
thuyết nên để lại 1–3 trang trong `notes/`. Tới tuần 10, chương 2 của báo cáo
chỉ còn việc ráp lại.

**Nguyên tắc 4 — Tập kiểm thử là bất khả xâm phạm.** Mọi ngưỡng, siêu tham số,
lựa chọn thiết kế đều chọn trên tập kiểm định (validation). Tập kiểm thử của IPN
và dữ liệu tự quay chỉ mở ra để đo con số cuối cùng. Nhìn vào tập kiểm thử rồi
chỉnh tham số là một dạng rò rỉ dữ liệu.

---

# GIAI ĐOẠN A — CHUẨN BỊ (Tuần 1)

---

## Bước 1. Đóng khung bài toán và định nghĩa cử chỉ

**Mục tiêu.** Một bản đặc tả cử chỉ một trang, đủ rõ để người khác đọc xong làm
đúng mà không cần hỏi lại, và một danh sách những gì đề tài *không* làm.

### Lý thuyết cần nắm

**Cử chỉ tĩnh và cử chỉ động.** Cử chỉ tĩnh được xác định bởi *hình dạng* bàn
tay tại một thời điểm (giơ ngón cái, nắm tay). Cử chỉ động được xác định bởi
*sự thay đổi* theo thời gian. Cả bốn cử chỉ của đề tài đều là cử chỉ động, và
chúng đi thành hai cặp có tính chất đặc biệt:

- Xòe tay và chụm tay đi qua **cùng những hình dạng bàn tay** nhưng theo thứ tự
  ngược nhau.
- Vuốt trái và vuốt phải đi qua **cùng những vị trí** nhưng theo chiều ngược nhau.

Nhìn một frame đơn lẻ, dù rõ nét đến đâu, cũng không thể biết bàn tay đang mở
ra hay khép lại. Đây chính là lý do đề tài cần mô hình chuỗi thời gian — cùng
lập luận "ngồi xuống / đứng dậy" của đề cương cũ, giờ áp dụng cho bàn tay.

**Nhận dạng cô lập và nhận dạng liên tục.** *Cô lập* (isolated): cho sẵn một
đoạn video chứa đúng một cử chỉ, hỏi đó là cử chỉ gì. *Liên tục* (continuous):
cho một luồng video dài, hệ thống phải tự tìm cử chỉ bắt đầu và kết thúc ở đâu,
rồi mới phân loại. Bước "tìm" gọi là **gesture spotting**. Hệ thống điều khiển
slide là bài toán liên tục. Phần lớn độ khó thực tế nằm ở đó, không nằm ở phân
loại.

**Vấn đề "Midas touch".** Thuật ngữ từ tương tác người–máy, xuất phát từ nghiên
cứu giao diện điều khiển bằng ánh mắt (Jacob, 1990): khi mọi chuyển động của
người dùng đều có thể bị hiểu là lệnh, hệ thống sẽ kích hoạt liên tục ngoài ý
muốn — như vua Midas chạm vào gì cũng hóa vàng. Người ngồi làm việc cử động tay
hàng trăm lần mỗi phút: gõ phím, cầm chuột, chạm mặt, cầm cốc. Chỉ vài lần trong
đó là lệnh. Mọi quyết định thiết kế ở bước 20 đều nhằm giải quyết vấn đề này.

**Ánh xạ cử chỉ → lệnh.** Hai tiêu chí: *tự nhiên* (giống thói quen có sẵn —
vuốt trái để sang trang tiếp như trên điện thoại, xòe để phóng to) và *khó nhầm
với động tác thường ngày*. Phần nhận dạng và phần ánh xạ độc lập với nhau: đổi
ánh xạ chỉ là đổi một dòng trong `config.py`.

> **Tự kiểm tra.** Vì sao "vẫy tay qua lại" không dùng được để phân biệt next và
> prev, còn "vuốt một chiều" thì được? Vì sao một hệ thống đạt 98% độ chính xác
> phân loại cô lập vẫn có thể không dùng được trong thực tế?

### Việc cụ thể

**1.1. Viết đặc tả cho từng cử chỉ** theo mẫu: tư thế bắt đầu, chuyển động, tư
thế kết thúc, thời lượng ước chừng, tay nào. Ví dụ:

| Cử chỉ | Bắt đầu | Chuyển động | Kết thúc | Thời lượng |
|---|---|---|---|---|
| Vuốt trái | Bàn tay mở, lòng bàn tay hướng camera, ở giữa khung | Quét ngang sang trái, gần thẳng | Tay ở mép trái | 0,3–1 s |
| Vuốt phải | Như trên | Quét ngang sang phải | Tay ở mép phải | 0,3–1 s |
| Xòe tay | Các ngón chụm lại quanh ngón cái | Mở rộng các ngón | Bàn tay xòe hết | 0,4–1,5 s |
| Chụm tay | Bàn tay xòe | Khép các ngón về ngón cái | Các ngón chụm | 0,4–1,5 s |

Ghi rõ "trái" nghĩa là trái **theo góc nhìn của người làm** hay **theo ảnh
camera**. Quy ước này sẽ được kiểm tra bằng số liệu ở bước 8 và 12.

**1.2. Viết danh sách "không làm"** (bảng 0.2) và lý do của từng mục. Danh sách
này là phần "phạm vi và giới hạn" của chương 1 báo cáo.

**1.3. Ghi chú tạm:** định nghĩa xòe/chụm chỉ là bản nháp cho tới bước 8, khi
bạn xem video mẫu của IPN Hand và quyết định khớp định nghĩa theo bộ dữ liệu.

### Kiểm chứng

Đưa bản đặc tả cho một người bạn, không giải thích gì thêm, nhờ họ làm từng cử
chỉ trước webcam. Nếu có cử chỉ họ làm khác ý bạn, đặc tả đó chưa đủ rõ.

### Sản phẩm

`notes/01-dac-ta-cu-chi.md`: bảng đặc tả, danh sách không làm, ảnh chụp minh họa
từng cử chỉ. Đây là nội dung mục 1.3 và 3.1 của báo cáo.

### Cạm bẫy

| Cạm bẫy | Hậu quả | Xử lý |
|---|---|---|
| Định nghĩa mơ hồ kiểu "vẫy tay" | Người thu dữ liệu mỗi người làm một kiểu | Mô tả tư thế đầu, chuyển động, tư thế cuối |
| Thêm cử chỉ cho "đầy đủ" | Mỗi lớp thêm là thêm một nguồn nhầm lẫn | Giữ đúng 4 lệnh + lớp nền |
| Chọn cử chỉ giống động tác thường ngày | Kích hoạt nhầm liên tục | Hỏi: "khi làm việc bình thường, tôi có vô tình làm động tác này không?" |

---

## Bước 2. Dựng môi trường và cấu trúc dự án

**Mục tiêu.** Một môi trường conda sạch, cài đủ thư viện, tải xong mô hình
`hand_landmarker.task`, thư mục dự án theo mục 0.6, và kho git đầu tiên.

### Lý thuyết cần nắm

**Môi trường ảo** tách thư viện của từng dự án, để cập nhật dự án này không làm
hỏng dự án khác. **Khả năng tái lập**: người khác (hoặc chính bạn ba tháng sau)
phải dựng lại được đúng môi trường từ `requirements.txt` và chạy ra đúng kết
quả — nghĩa là phải cố định phiên bản thư viện và hạt giống ngẫu nhiên (seed).

**MediaPipe có hai bộ API.** Bộ cũ `mp.solutions.hands` đã bị loại khỏi các bản
MediaPipe mới; code mẫu cũ trên mạng sẽ báo lỗi `module 'mediapipe' has no
attribute 'solutions'`. Đề tài dùng bộ **Tasks API** (`mp.tasks.vision.HandLandmarker`)
— cùng kiểu với code Pose trong đề cương cũ.

### Việc cụ thể

**2.1. Tạo môi trường** (Anaconda Prompt):

```bash
conda create -n gesture -y python=3.10
conda activate gesture
pip install mediapipe opencv-python numpy pandas matplotlib
pip install scikit-learn pyautogui tqdm
pip install torch            # bản CPU là đủ
pip freeze > requirements.txt
```

**2.2. Tải mô hình** `hand_landmarker.task` từ trang tài liệu Hand Landmarker
của Google (mục *Models*), đặt vào `models/`. Tại thời điểm viết, đường dẫn
thường dùng là
`https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task`
— nếu hỏng, lấy lại từ trang tài liệu.

**2.3. Tạo cây thư mục** theo mục 0.6 và file `src/config.py`:

```python
CLASSES = ["none", "swipe_left", "swipe_right", "zoom_in", "zoom_out"]
KEYMAP = {"swipe_left": "right", "swipe_right": "left", "zoom_in": "+", "zoom_out": "-"}
TARGET_HZ = 15          # tần số chung sau khi lấy mẫu lại
WINDOW_S = 1.0          # độ dài cửa sổ (giây) — sẽ khảo sát ở bước 19
STRIDE_STEPS = 2        # dự đoán mỗi 2 bước
SWIPE_LEFT_SIGN = +1    # dấu của dx khi vuốt trái — đo lại ở bước 5.3
SEED = 42
```

Để các script trong `scripts/` import được `src/`, thêm hai dòng này ở đầu mỗi
script (hoặc đặt biến môi trường `PYTHONPATH` trỏ tới thư mục gốc dự án):

```python
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
```

**2.4. Khởi tạo git**, thêm `.gitignore` bỏ qua `data/`, `models/*.task`,
`__pycache__/`. Dữ liệu và mô hình không đưa lên git.

### Kiểm chứng

```python
import mediapipe as mp, cv2, sklearn, torch
print(mp.__version__, cv2.__version__, sklearn.__version__, torch.__version__)
print(mp.tasks.vision.HandLandmarker)   # không báo lỗi là được
```

### Sản phẩm

Môi trường chạy được, `requirements.txt`, commit đầu tiên.

### Cạm bẫy

| Hiện tượng | Nguyên nhân | Xử lý |
|---|---|---|
| `AttributeError: ... 'solutions'` | Code mẫu dùng API cũ | Dùng `mp.tasks.vision.HandLandmarker` |
| `pip` cài vào môi trường khác | Quên `conda activate gesture` | Luôn kiểm tra tên môi trường ở đầu dòng lệnh |
| Không cài được mediapipe | Phiên bản Python quá mới hoặc quá cũ so với bản mediapipe | Dùng Python 3.10 hoặc 3.11 |
| Đặt tên file `mediapipe.py` | Python import nhầm file của bạn | Không đặt tên file trùng tên thư viện |

---

## Bước 3. Hand Landmarker chạy trên webcam

**Mục tiêu.** 21 điểm mốc vẽ đè lên bàn tay, bám theo chuyển động, kèm FPS thực
tế và nhãn tay trái/phải hiển thị trên màn hình.

### Lý thuyết cần nắm

**Cấu trúc một Task của MediaPipe.** Ba lớp: `BaseOptions` (đường dẫn mô hình),
`HandLandmarkerOptions` (chế độ chạy, số tay, các ngưỡng), `HandLandmarker`
(đối tượng thực thi). Tạo **một lần** ngoài vòng lặp; tạo trong vòng lặp là
nạp lại mô hình mỗi frame.

**Ba chế độ chạy.** `IMAGE`: mỗi ảnh độc lập, luôn chạy bộ phát hiện. `VIDEO`:
các frame nối tiếp, cho phép **bám theo** tay từ frame trước (nhanh và mượt
hơn), đòi hỏi mốc thời gian **tăng nghiêm ngặt**. `LIVE_STREAM`: như VIDEO nhưng
bất đồng bộ qua hàm gọi lại. Đề tài dùng `VIDEO` vì luồng điều khiển tuần tự,
dễ gỡ lỗi.

**Kết quả trả về** gồm ba phần, mỗi phần là danh sách theo từng bàn tay:

| Trường | Nội dung | Dùng cho |
|---|---|---|
| `hand_landmarks` | 21 điểm, `x`, `y` chuẩn hóa theo **chiều rộng / chiều cao ảnh** về [0, 1]; `z` là độ sâu tương đối so với cổ tay | Mọi thứ phía sau |
| `hand_world_landmarks` | 21 điểm theo mét, gốc ở tâm hình học của bàn tay | Tham khảo, không dùng chính |
| `handedness` | Nhãn `Left` / `Right` kèm điểm tin cậy | Kiểm tra ở bước 7 |

**Camera của ThinkPad.** OpenCV trên Windows thường mở mặc định ở 640×480; bản
máy có camera hồng ngoại sẽ có hai thiết bị camera, chỉ số 0 hoặc 1 có thể là
camera IR cho ảnh xám. Nắp che ThinkShutter phải mở. BGR→RGB như cẩm nang cũ.

> **Tự kiểm tra.** Vì sao chế độ `VIDEO` báo lỗi nếu hai frame liên tiếp có cùng
> mốc thời gian? Gợi ý: nó dùng mốc thời gian để quyết định có bám theo được từ
> kết quả frame trước hay không.

### Việc cụ thể

**3.1. Viết `src/landmarks.py`** với danh sách nối xương và hàm vẽ:

```python
HAND_CONNECTIONS = [(0,1),(1,2),(2,3),(3,4),            # ngón cái
                    (0,5),(5,6),(6,7),(7,8),            # ngón trỏ
                    (5,9),(9,10),(10,11),(11,12),       # ngón giữa
                    (9,13),(13,14),(14,15),(15,16),     # ngón áp út
                    (13,17),(0,17),(17,18),(18,19),(19,20)]  # ngón út + gan tay
```

**3.2. Vòng lặp webcam** (`scripts/00_webcam_demo.py`):

```python
import cv2, time
from collections import deque
import mediapipe as mp
from src.landmarks import HAND_CONNECTIONS

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="models/hand_landmarker.task"),
    running_mode=RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)          # thử 1 nếu ra ảnh xám (camera IR)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
dts, t0 = deque(maxlen=30), time.perf_counter()
last, prev_ts = t0, -1
try:
    with HandLandmarker.create_from_options(options) as landmarker:
        while True:
            ok, frame_bgr = cap.read()
            if not ok:
                break
            now = time.perf_counter()
            dts.append(now - last); last = now
            ts_ms = max(int((now - t0) * 1000), prev_ts + 1)   # bảo đảm tăng nghiêm ngặt
            prev_ts = ts_ms
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            result = landmarker.detect_for_video(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb), ts_ms)
            h, w = frame_bgr.shape[:2]
            if result.hand_landmarks:
                pts = [(int(p.x * w), int(p.y * h)) for p in result.hand_landmarks[0]]
                for a, b in HAND_CONNECTIONS:
                    cv2.line(frame_bgr, pts[a], pts[b], (0, 255, 0), 2)
                for p in pts:
                    cv2.circle(frame_bgr, p, 4, (0, 0, 255), -1)
                hd = result.handedness[0][0]
                cv2.putText(frame_bgr, f"{hd.category_name} {hd.score:.2f}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(frame_bgr, f"FPS {len(dts)/sum(dts):.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.imshow("hand", frame_bgr)
            if cv2.waitKey(1) & 0xFF == 27:
                break
finally:
    cap.release()
    cv2.destroyAllWindows()
```

**3.3. In ra độ phân giải thực** camera trả về (`frame_bgr.shape`) — đừng tin
lệnh `set` đã thành công.

**3.4. Bấm giờ từng khâu**: đọc frame, đổi màu, gọi landmarker, vẽ. Ghi lại bảng
phân rã thời gian — dùng lại ở bước 21.

### Kiểm chứng

- Điểm mốc bám tay, không giật khi tay đứng yên.
- FPS ổn định quanh 25–30 ở điều kiện đủ sáng.
- Giơ **tay phải thật** của bạn lên: nhãn hiển thị là `Left` hay `Right`? Ghi lại
  — bước 7 sẽ giải thích.
- Nhấn ESC thoát sạch, chạy lại lần hai không báo camera bận.

### Sản phẩm

Video quay màn hình 30 giây: điểm mốc bám tay, kèm FPS. Sản phẩm tuần 1 và hình
minh họa đầu tiên cho chương 4.

### Cạm bẫy

| Hiện tượng | Nguyên nhân | Xử lý |
|---|---|---|
| Lỗi về timestamp phải tăng dần | Hai frame cùng mốc ms | Dùng `max(ts, prev + 1)` như code trên |
| Ảnh xám nhấp nháy | Mở nhầm camera IR | Đổi chỉ số camera |
| Màn hình đen | Nắp ThinkShutter đang đóng | Mở nắp |
| Tay phát hiện chập chờn, không báo lỗi | Quên đổi BGR→RGB | Đổi ngay sau khi đọc frame |
| FPS tụt mạnh trong phòng tối | Camera tự kéo dài thời gian phơi sáng | Bật đèn; ghi nhận hiện tượng cho bước 5 |

---

## Bước 4. Chuỗi đầu–cuối: từ bàn tay tới PowerPoint

**Mục tiêu.** Một luật đơn giản nhất có thể (xòe tay giữ yên 1 giây → slide tiếp)
điều khiển được PowerPoint thật. Nhận dạng còn thô, nhưng **toàn bộ chuỗi** đã
chạy từ tuần 1.

### Lý thuyết cần nắm

**Giả lập bàn phím và tiêu điểm cửa sổ.** `pyautogui.press()` sinh sự kiện phím
ở mức hệ điều hành. Sự kiện đi tới **cửa sổ đang có tiêu điểm** (focus). Cửa sổ
`cv2.imshow` vừa tạo sẽ giành tiêu điểm, nên phím sẽ rơi vào cửa sổ camera chứ
không vào PowerPoint — lỗi mà gần như ai cũng gặp lần đầu.

**Phím trong chế độ trình chiếu PowerPoint:** mũi tên phải / trái để chuyển
slide, phím `+` / `-` để phóng to / thu nhỏ.

**Vì sao làm bước này sớm.** Nó phơi ra các vấn đề tích hợp (tiêu điểm, bố cục
phím, quyền của hệ điều hành) khi dự án còn nhỏ. Và nó cho bạn thứ để trình bày
ngay buổi báo cáo tiến độ tiếp theo.

### Việc cụ thể

**4.1. Viết `src/actions.py`:**

```python
import pyautogui
from src.config import KEYMAP
pyautogui.FAILSAFE = True      # đưa chuột lên góc trên trái để dừng khẩn cấp

def send(cmd: str):
    pyautogui.press(KEYMAP[cmd])
```

**4.2. Tính "độ xòe" thô** trong vòng lặp bước 3: khoảng cách trung bình từ 5
đầu ngón (4, 8, 12, 16, 20) tới cổ tay (0), chia cho khoảng cách cổ tay – gốc
ngón giữa (0–9). Nhớ đổi sang **pixel** trước khi tính (lý do ở bước 9).

**4.3. Luật "hello world":** nếu độ xòe vượt ngưỡng liên tục 1 giây → `send("swipe_left")`,
sau đó bỏ qua 2 giây. Ngưỡng chọn bằng cách in giá trị ra khi xòe và khi nắm.

**4.4. Thử với PowerPoint:** mở một bài trình chiếu, bấm F5, chạy script, **bấm
chuột vào cửa sổ trình chiếu** để trả tiêu điểm, rồi giơ tay.

**4.5. Thử phím `+` và `-`** riêng: nếu `pyautogui.press("+")` không có tác dụng,
thử `pyautogui.press("add")` / `"subtract"` (phím trên bàn số) và ghi lại cái
nào hoạt động trên máy bạn.

### Kiểm chứng

Xòe tay giữ yên → slide chuyển đúng một lần. Nắm tay → không có gì xảy ra.

### Sản phẩm

Video 20 giây: bàn tay điều khiển slide. Chưa thông minh, nhưng là bằng chứng
chuỗi đầu–cuối hoạt động.

### Cạm bẫy

| Hiện tượng | Nguyên nhân | Xử lý |
|---|---|---|
| Slide không chuyển, không báo lỗi | Tiêu điểm đang ở cửa sổ camera | Bấm vào cửa sổ trình chiếu sau khi chạy script |
| Slide nhảy liền 5–6 trang | Luật bắn mỗi frame khi điều kiện đúng | Thêm thời gian nghỉ sau mỗi lệnh |
| Chương trình dừng đột ngột | FAILSAFE kích hoạt do chuột ở góc màn hình | Đó là tính năng; để chuột ở giữa |

---

# GIAI ĐOẠN B — NỀN TẢNG LÝ THUYẾT (Tuần 2–3)

---

## Bước 5. Ảnh số, video và camera của bạn

**Mục tiêu.** Nắm tầng 1 và hiểu cụ thể camera ThinkPad ảnh hưởng thế nào tới
cử chỉ nhanh.

### Lý thuyết cần nắm

Toàn bộ `01-anh-so-va-video.md` vẫn áp dụng: pixel và kênh màu, BGR/RGB, gốc tọa
độ ở góc trên trái với trục y hướng **xuống**, FPS quay và FPS xử lý. Bổ sung ba
điểm riêng cho đề tài này:

**Thời gian phơi sáng và nhòe chuyển động.** Mỗi frame là ánh sáng tích lũy
trong một khoảng thời gian phơi sáng. Phòng tối → camera tự kéo dài phơi sáng
để ảnh đủ sáng → (a) FPS tụt vì không thể chụp 30 frame/giây nếu mỗi frame cần
hơn 33 ms, và (b) vật chuyển động nhanh bị nhòe thành vệt. Cử chỉ vuốt là
chuyển động nhanh nhất trong đề tài, nên nó bị ảnh hưởng đầu tiên. Cảm biến
camera laptop nhỏ nên hiện tượng này rõ hơn camera rời.

**Ảnh gương và quy ước trái/phải.** Camera trước **không** tự lật ảnh. Khi bạn
đưa tay phải sang phía phải của *bạn*, bàn tay đi về phía **trái của ảnh** (x
giảm). Các ứng dụng gọi video thường lật ảnh để hiển thị như gương, nhưng dữ
liệu bên dưới thì không. Quy tắc của đề tài:

> Mô hình luôn nhận ảnh **không lật**, cùng quy ước với dữ liệu huấn luyện. Chỉ
> lật khi *hiển thị* cho người dùng xem.

**Tỉ lệ khung hình và trường nhìn.** IPN Hand quay 640×480 (4:3), webcam của bạn
có thể mở 1280×720 (16:9). Hai chế độ này có thể cắt trường nhìn khác nhau từ
cùng cảm biến. Hệ quả cho tọa độ chuẩn hóa: một đơn vị theo x và một đơn vị theo
y **không cùng độ dài thật** (xem bước 9).

> **Tự kiểm tra.** Nếu bạn lật ảnh trước khi đưa vào mô hình nhưng dữ liệu huấn
> luyện không lật, mô hình sẽ nhầm cặp lớp nào với nhau?

### Việc cụ thể

**5.1.** Đọc lại `01-anh-so-va-video.md`, làm các bài tập trong đó nếu chưa làm.

**5.2. Thí nghiệm nhòe:** quay cùng một cú vuốt nhanh trong phòng sáng và phòng
tối. Tách frame giữa cú vuốt, đặt cạnh nhau. Ghi FPS thực của hai điều kiện.

**5.3. Thí nghiệm quy ước:** in tọa độ x của cổ tay khi bạn đưa tay phải sang
phải. Xác nhận x giảm. Ghi vào ghi chú — con số này là "chìa khóa" để kiểm tra
quy ước của IPN ở bước 12.

**5.4.** So sánh ảnh 640×480 và 1280×720 từ camera của bạn: trường nhìn có bị cắt
khác nhau không?

### Kiểm chứng

Bạn giải thích được bằng lời, không nhìn ghi chú: vì sao phòng tối làm hỏng cử
chỉ vuốt nhiều hơn cử chỉ xòe.

### Sản phẩm

`notes/05-anh-so-camera.md` + cặp ảnh sáng/tối minh họa nhòe — hình cho mục 2.1
và 6 (thảo luận) của báo cáo.

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Lật ảnh "cho đẹp" ngay sau khi đọc frame, trước khi đưa vào mô hình | Chỉ lật bản dùng để hiển thị |
| Nhầm FPS camera báo (`CAP_PROP_FPS`) với FPS thật | Luôn đo bằng đồng hồ |

---

## Bước 6. Lý thuyết ước lượng tư thế bàn tay

**Mục tiêu.** Hiểu Hand Landmarker làm gì bên trong đủ sâu để viết 4–5 trang
chương 2 và trả lời được mọi câu hỏi "vì sao nó sai ở đây".

Đây là phần kiến thức thị giác máy tính đáng giá nhất của đồ án. Bước này thuần
lý thuyết. Tài liệu gốc cần đọc: bài báo *MediaPipe Hands: On-device Real-time
Hand Tracking* (Zhang và cộng sự, 2020, arXiv:2006.10214) — ngắn, chỉ 5 trang.

### Lý thuyết cần nắm

#### 6.a. Bài toán và 21 điểm mốc

Đầu vào: một ảnh RGB. Đầu ra: vị trí 21 điểm trên bàn tay — cổ tay và 4 khớp
cho mỗi ngón (bảng đầy đủ ở Phụ lục A). Bố cục 21 điểm này theo công trình của
Simon và cộng sự (CMU, 2017) và đã thành quy ước chung của lĩnh vực.

Tọa độ là **2,5D**: `x`, `y` là vị trí trên ảnh; `z` là độ sâu **tương đối so
với cổ tay**, không phải khoảng cách thật tới camera. Theo bài báo, thành phần
độ sâu chỉ được học từ ảnh tổng hợp — nên nó kém tin cậy hơn nhiều so với x, y.
Đề tài chỉ dùng x, y.

#### 6.b. Vì sao bàn tay khó hơn cơ thể

- **Nhiều bậc tự do**: mỗi ngón có 3–4 khớp, bàn tay có khoảng 27 bậc tự do, trong
  một vùng ảnh nhỏ.
- **Tự che khuất**: khi nắm tay, các ngón che lẫn nhau; nhìn nghiêng, cả bàn tay
  thành một khối.
- **Các ngón giống nhau**: ngón trỏ, giữa, áp út trông gần như nhau; mô hình phải
  dựa vào ngữ cảnh để biết ngón nào là ngón nào.
- **Ít đặc trưng tương phản**: khuôn mặt có mắt, miệng rất đặc trưng; bàn tay thì
  không. Bài báo nói rõ điều này khiến phát hiện bàn tay chỉ từ đặc trưng thị
  giác khó hơn nhiều so với phát hiện mặt.

#### 6.c. Kiến trúc hai tầng: phát hiện rồi định vị

```
Toàn bộ ảnh ──► Bộ phát hiện lòng bàn tay (BlazePalm, đầu vào 192×192)
                    │ hộp bao có hướng
                    ▼
               Cắt + xoay vùng bàn tay ──► Mô hình điểm mốc (đầu vào 224×224)
                                                │
                                                ├─► 21 điểm (x, y, z)
                                                ├─► xác suất "có tay trong vùng cắt"
                                                └─► tay trái / tay phải
```

Vì sao không làm một mạng duy nhất? Vì khi mô hình điểm mốc nhận một vùng cắt
**đã căn chỉnh sẵn** (đúng vị trí, đúng tỉ lệ, đã xoay thẳng), nó không phải học
cách xử lý bàn tay ở mọi vị trí, mọi cỡ, mọi góc xoay. Toàn bộ năng lực của mạng
dành cho việc định vị chính xác. Đây là cùng triết lý "top-down" bạn đã học với
tư thế người: tìm đối tượng trước, tìm điểm sau.

#### 6.d. BlazePalm — vì sao phát hiện *lòng bàn tay* chứ không phải bàn tay

Bộ phát hiện thuộc họ **single-shot detector (SSD)**: đặt sẵn hàng nghìn hộp mẫu
(*anchor*) ở mọi vị trí và kích thước trên ảnh, mạng dự đoán với mỗi hộp mẫu
"có vật không" và "cần dịch hộp bao nhiêu". Sau đó **non-maximum suppression
(NMS)** gộp các hộp chồng lấn lên cùng một vật, giữ hộp tin cậy nhất.

Ba lựa chọn thiết kế, mỗi cái giải quyết một khó khăn:

1. **Phát hiện lòng bàn tay thay vì cả bàn tay.** Lòng bàn tay (hoặc nắm tay) là
   vật gần như **cứng** — không thay đổi hình dạng khi ngón co duỗi. Nó vừa với
   **hộp vuông**, nên chỉ cần một tỉ lệ khung cho hộp mẫu, giảm số hộp mẫu 3–5
   lần. Và vì lòng bàn tay nhỏ, NMS vẫn tách được hai tay khi chúng chồng lên
   nhau (như bắt tay).
2. **Bộ trích đặc trưng encoder–decoder kiểu FPN**: kết hợp đặc trưng thô ở độ
   phân giải cao với đặc trưng ngữ nghĩa ở độ phân giải thấp, để nhận ra vật nhỏ
   nhờ ngữ cảnh xung quanh.
3. **Focal loss**: với hàng nghìn hộp mẫu, gần như tất cả là nền. Hàm mất mát
   thường sẽ bị các hộp nền "dễ" áp đảo. Focal loss giảm trọng số các mẫu đã
   phân loại dễ, buộc mạng tập trung vào mẫu khó.

Bài báo có bảng khảo sát: thêm decoder tăng độ chính xác trung bình từ khoảng 86%
lên 94%, đổi sang focal loss lên gần 96%. Đây là ví dụ đẹp để đưa vào báo cáo
khi giải thích "mỗi lựa chọn thiết kế đóng góp bao nhiêu".

#### 6.e. Mô hình điểm mốc — hồi quy trực tiếp

Khác với phần lớn mô hình tư thế người dùng **bản đồ nhiệt** (tài liệu `02`, mục 3),
mô hình điểm mốc bàn tay **hồi quy trực tiếp** 21 bộ tọa độ. Lý do có thể hiểu
được: vùng cắt đầu vào đã được căn chỉnh chặt, bàn tay chiếm gần hết vùng cắt,
nên bài toán "tìm điểm ở đâu trong một ảnh nhỏ đã căn chỉnh" đơn giản hơn nhiều
so với "tìm điểm trong ảnh toàn cảnh". Hồi quy trực tiếp cũng nhẹ hơn. Đây là
một điểm so sánh hay giữa chương 2 cũ và mới: cùng bài toán ước lượng tư thế,
hai chiến lược đầu ra khác nhau, và lựa chọn phụ thuộc vào việc đầu vào đã được
căn chỉnh tới đâu.

Mô hình có **ba đầu ra dùng chung một bộ trích đặc trưng**: 21 điểm; một cờ xác
suất "có bàn tay căn chỉnh hợp lý trong vùng cắt"; và phân loại tay trái/phải.

**Dữ liệu huấn luyện** gồm ba nguồn: khoảng 6.000 ảnh thực đa dạng, khoảng
10.000 ảnh tự thu với đủ kiểu tư thế tay, và khoảng 100.000 ảnh tổng hợp dựng từ
mô hình bàn tay 3D. Kết quả của bài báo: kết hợp thực + tổng hợp cho sai số thấp
nhất, và đáng chú ý là **sai số được đo bằng MSE chia cho cỡ lòng bàn tay** —
chính là đơn vị chuẩn hóa bạn sẽ dùng ở bước 9.

#### 6.f. Theo dõi thay vì phát hiện lại mỗi frame

Ở chế độ VIDEO, sau khi tìm thấy tay, hệ thống **suy ra hộp của frame sau từ các
điểm mốc của frame trước**, bỏ qua bộ phát hiện. Bộ phát hiện chỉ chạy lại khi cờ
"có tay" tụt dưới ngưỡng. Ba tham số cấu hình tương ứng:

| Tham số | Kiểm soát |
|---|---|
| `min_hand_detection_confidence` | Ngưỡng để bộ phát hiện lòng bàn tay chấp nhận một phát hiện |
| `min_hand_presence_confidence` | Ngưỡng cờ "có tay" — dưới ngưỡng thì chạy lại bộ phát hiện |
| `min_tracking_confidence` | Ngưỡng độ chồng lấn hộp giữa frame trước và frame sau để coi là bám thành công |

**Hệ quả trực tiếp cho đề tài:** khi vuốt nhanh, tay dịch chuyển lớn giữa hai
frame, hộp suy ra từ frame trước không còn chứa tay → bám thất bại → phải phát
hiện lại từ đầu → có thể mất tay vài frame **đúng giữa cử chỉ**. Kết hợp với nhòe
chuyển động (bước 5), đây là lý do cử chỉ vuốt có tỉ lệ frame thiếu tay cao nhất.
Bước 7 sẽ đo hiện tượng này.

#### 6.g. Đầu vào cố định và khoảng cách

Bộ phát hiện nhận ảnh 192×192: toàn bộ frame bị thu nhỏ còn 192 pixel chiều
ngang trước khi phát hiện. Do đó yếu tố quyết định là **bàn tay chiếm bao nhiêu
phần khung hình**, không phải độ phân giải camera. Ngồi trước laptop 0,5 m, bàn
tay chiếm khoảng 1/4 chiều rộng ảnh — thoải mái. Đứng cách 2–3 m thì lòng bàn
tay chỉ còn vài pixel trong ảnh 192. Đây là lý do đề tài chốt kịch bản ngồi.

#### 6.h. Nhãn tay trái / tay phải

Tài liệu và code mẫu của MediaPipe giả định ảnh đầu vào **đã lật như gương**
(camera selfie). Với ảnh không lật — như quy tắc của đề tài — nhãn có thể bị
**ngược**. Đề tài không dựa vào nhãn này cho quyết định quan trọng; chỉ dùng nó
như một đặc trưng phụ sau khi đã kiểm chứng ở bước 7.

> **Tự kiểm tra.**
> 1. Vì sao phát hiện lòng bàn tay dễ hơn phát hiện cả bàn tay? Nêu hai lý do.
> 2. Vì sao mô hình điểm mốc bàn tay có thể dùng hồi quy trực tiếp, trong khi
>    nhiều mô hình tư thế người cần bản đồ nhiệt?
> 3. Vì sao tỉ lệ mất tay khi vuốt nhanh cao hơn khi xòe tay tại chỗ?
> 4. Đổi webcam 720p sang 4K có giúp phát hiện tay ở 3 m không? Vì sao?

### Việc cụ thể

**6.1.** Đọc bài báo MediaPipe Hands (arXiv:2006.10214), tóm tắt từng mục.

**6.2.** Đọc lại `02-uoc-luong-tu-the.md` mục 3 (bản đồ nhiệt) và 4 (top-down /
bottom-up) để viết đoạn so sánh ở mục 6.e.

**6.3.** Tìm hiểu nhanh SSD, anchor, NMS, focal loss — đủ để giải thích bằng một
đoạn văn mỗi khái niệm. Không cần đọc toàn văn các bài gốc.

**6.4.** Vẽ lại sơ đồ kiến trúc hai tầng bằng tay hoặc công cụ vẽ — hình cho
chương 2.

### Kiểm chứng

Trả lời được bốn câu tự kiểm tra ở trên mà không nhìn tài liệu.

### Sản phẩm

`notes/06-uoc-luong-tu-the-ban-tay.md`: 4–5 trang, là mục 2.2 của báo cáo.

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Sa đà vào chi tiết kiến trúc mạng (số lớp, số kênh) | Đề tài không huấn luyện mô hình này; hiểu *vì sao thiết kế như vậy* là đủ |
| Chép lại bài báo | Viết theo cấu trúc câu hỏi: vấn đề gì → giải pháp gì → vì sao hiệu quả |

---

## Bước 7. Thí nghiệm quan sát Hand Landmarker

**Mục tiêu.** Một bộ số liệu thực đo trên **máy của bạn** cho thấy Hand Landmarker
hoạt động tốt ở đâu và hỏng ở đâu — căn cứ cho mọi quyết định thiết kế phía sau.

### Lý thuyết cần nắm

**Tỉ lệ phát hiện** = số frame có tay / tổng số frame khi tay thực sự trong khung
hình. **Độ rung** (jitter) = độ lệch chuẩn vị trí một điểm khi tay đứng yên, đo
bằng pixel. Độ rung quyết định ngưỡng tối thiểu cho mọi luật dựa trên chuyển
động: một luật "cổ tay dịch hơn 5 pixel" vô nghĩa nếu độ rung đã là 4 pixel.

**Thí nghiệm có kiểm soát**: mỗi lần chỉ thay đổi một yếu tố (khoảng cách, tốc
độ, ánh sáng), giữ nguyên các yếu tố khác.

### Việc cụ thể

Viết một script ghi mỗi frame ra CSV: thời điểm, có tay hay không, 21 điểm, nhãn
tay, điểm tin cậy. Rồi làm sáu thí nghiệm, mỗi thí nghiệm 10–20 giây:

| # | Thí nghiệm | Đo |
|---|---|---|
| 1 | Tay đứng yên ở 0,3 / 0,5 / 0,7 / 1,0 m | Tỉ lệ phát hiện, độ rung đầu ngón trỏ |
| 2 | Vuốt chậm và vuốt nhanh | Tỉ lệ phát hiện trong lúc vuốt, số lần mất tay |
| 3 | Xòe – chụm liên tục | Tỉ lệ phát hiện ở tư thế chụm (ngón che nhau) |
| 4 | Phòng sáng và phòng tối | FPS, tỉ lệ phát hiện khi vuốt |
| 5 | Tay trước mặt, tay trên bàn phím, tay cầm cốc | Có phát hiện nhầm không, điểm mốc có hợp lý không |
| 6 | Giơ tay phải, rồi tay trái, ảnh không lật và ảnh lật | Nhãn `Left`/`Right` trả về |

### Kiểm chứng

Mỗi thí nghiệm có một con số hoặc một đồ thị, không chỉ nhận xét bằng mắt.

### Sản phẩm

Bảng số liệu và 2–3 đồ thị (tỉ lệ phát hiện theo khoảng cách; theo tốc độ vuốt).
Đây là mục "Khảo sát công cụ" của chương 5 và là câu trả lời cho câu hỏi hội
đồng "vì sao em chọn Hand Landmarker và kịch bản ngồi".

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Kết luận "nhãn tay bị sai" | Đó là quy ước ảnh gương (6.h), không phải lỗi — ghi rõ trong báo cáo |
| Chỉ đo khi tay đứng yên | Cử chỉ thật là chuyển động; thí nghiệm 2 quan trọng nhất |

---

## Bước 8. Làm quen IPN Hand và chốt ánh xạ lớp

**Mục tiêu.** Bộ dữ liệu IPN Hand đã tải về, bạn hiểu cấu trúc nhãn, đã xem tận
mắt các cử chỉ liên quan, và chốt **bảng ánh xạ lớp** cuối cùng.

### Lý thuyết cần nắm

**Vì sao IPN Hand hợp với đề tài.** Người tham gia tự quay bằng máy tính hoặc
laptop của mình, ngồi ở tư thế thoải mái để điều khiển màn hình — đúng kịch bản
của bạn. Video 640×480, 30 FPS. Mỗi video là một phiên liên tục khoảng 21 cử chỉ
xen giữa các đoạn cử động tự nhiên, frame bắt đầu và kết thúc của từng cử chỉ
được gán nhãn tay. Tổng cộng 50 người, 200 video, hơn 4.000 cử chỉ, chia tập
theo người. Giấy phép dữ liệu là CC BY 4.0 — dùng tự do, chỉ cần trích dẫn.

**13 lớp cử chỉ của IPN** (cộng lớp không cử chỉ):

| Mã | Cử chỉ | Số mẫu | Thời lượng TB (frame) |
|---|---|---|---|
| D0X | Không cử chỉ | 1431 | 147 |
| B0A / B0B | Trỏ một ngón / hai ngón | ~1000 mỗi lớp | ~220 |
| G01 / G02 | Click một ngón / hai ngón | 200 | ~58 |
| G03 / G04 | Hất lên / xuống | 200 | ~63 |
| **G05 / G06** | **Hất trái / phải** | 200 | ~65 |
| G07 | Mở tay hai lần | 200 | 76 |
| G08 / G09 | Double-click một ngón / hai ngón | 200 | ~69 |
| **G10 / G11** | **Zoom in / Zoom out** | 200 | ~65 |

Thời lượng trung bình khoảng 65 frame, tức **hơn 2 giây** — dài hơn bạn nghĩ,
vì nhãn gồm cả pha đưa tay lên và hạ tay xuống. Con số này quyết định dải độ dài
cửa sổ cần khảo sát ở bước 19.

**Tư duy ánh xạ lớp.** Bạn không dùng lại bài toán 14 lớp của IPN. Bạn *chiếu*
nó về bài toán 5 lớp của mình. Mỗi lớp IPN rơi vào một trong ba nhóm: **lớp đích**
(khớp một lớp của bạn), **lớp nền** (trở thành "không cử chỉ" — mẫu âm khó miễn
phí), hoặc **bỏ qua** (quá giống lớp đích, để vào đâu cũng gây nhiễu nhãn).

### Việc cụ thể

**8.1. Tải dữ liệu** từ trang dự án `gibranbenitez.github.io/IPN_Hand`:

- **Video MP4 gốc** 640×480, 30 FPS (khoảng 4,6 GB, 5 file `.tgz` × 40 video).
  Chọn bản này, không chọn bản frame đã thu nhỏ 320×240.
- **Annotations** (khoảng 364 KB: sáu file `.txt` và một file `.csv`).
- Giải nén `.tgz` trên Windows bằng 7-Zip.

**8.2. Đọc file nhãn** bằng pandas. File danh sách nhãn thường có các cột kiểu
`video, label, id, t_start, t_end, frames` — **mở ra kiểm tra tên cột thực tế**.
Xác định: frame đánh số từ 0 hay từ 1? Danh sách video train/test nằm ở file
nào? File `.csv` chứa thông tin gì về người quay?

**8.3. Xem tận mắt.** Trang *Classes* của dự án có ảnh GIF từng lớp. Xem kỹ G05,
G06, G10, G11 và G07. Rồi mở 3–4 video, tua tới đúng frame của các cử chỉ này.
Trả lời:

- Zoom in / out của IPN làm bằng **cả bàn tay** hay **ngón cái + ngón trỏ**?
- "Hất trái" là trái theo người làm hay theo ảnh?
- Người quay dùng tay phải hay cả hai tay?

**8.4. Chốt bảng ánh xạ.** Bản đề xuất (điều chỉnh theo kết quả 8.3):

| Nhóm | Lớp IPN | Lớp của bạn |
|---|---|---|
| Đích | G05 Hất trái | `swipe_left` |
| Đích | G06 Hất phải | `swipe_right` |
| Đích | G10 Zoom in | `zoom_in` |
| Đích | G11 Zoom out | `zoom_out` |
| Nền | D0X, B0A, B0B, G01, G02, G03, G04, G08, G09 | `none` |
| Bỏ qua (phiên bản 1) | G07 Mở tay hai lần | — |

G07 để "bỏ qua" ở phiên bản đầu vì nó chứa **cả một pha mở lẫn một pha đóng** —
một cửa sổ chỉ nhìn thấy pha mở sẽ trông y hệt zoom in. Ở bước 19, đưa G07 vào
lớp nền và xem mô hình có phân biệt được không: đó là một kết quả thảo luận hay.

Nếu ở 8.3 bạn thấy zoom của IPN làm bằng hai ngón còn bạn muốn dùng cả bàn tay,
chọn một trong hai: đổi định nghĩa của bạn theo IPN (khuyên dùng — tận dụng được
dữ liệu), hoặc giữ định nghĩa của bạn và chỉ lấy zoom từ dữ liệu tự quay.

**8.5. Thống kê:** số mẫu mỗi lớp đích, phân bố thời lượng (histogram), số người
trong tập train/test chính thức.

### Kiểm chứng

- Chồng nhãn lên video: viết script hiện tên lớp lên frame theo `t_start`/`t_end`,
  xem một video. Nhãn phải trùng khớp với lúc cử chỉ thực sự diễn ra. Nếu lệch
  một frame đều đặn → bạn đang nhầm đánh số từ 0 và từ 1.
- Tổng số mẫu mỗi lớp khớp với bảng của tác giả.

### Sản phẩm

`notes/08-ipn-hand.md`: mô tả bộ dữ liệu, bảng ánh xạ lớp kèm lý do từng quyết
định, histogram thời lượng. Đây là mục 3.1–3.2 của báo cáo.

### Cạm bẫy

| Cạm bẫy | Hậu quả | Xử lý |
|---|---|---|
| Tải bản frame 320×240 thay vì MP4 gốc | Mất độ phân giải, điểm mốc kém hơn | Tải MP4 |
| Không xem video, chỉ đọc tên lớp | Định nghĩa của bạn và của IPN lệch nhau mà không biết | Bắt buộc làm 8.3 |
| Nhầm frame đánh số từ 0 và từ 1 | Nhãn lệch một frame — nhỏ nhưng tích lũy | Kiểm chứng bằng cách chồng nhãn lên video |
| Tự chia lại train/test ngẫu nhiên | Mất khả năng so sánh với công trình khác, dễ rò rỉ | Dùng danh sách chia chính thức |

---

# GIAI ĐOẠN C — BIỂU DIỄN (Tuần 4)

---

## Bước 9. Chuẩn hóa chuỗi điểm mốc

**Mục tiêu.** Một hàm chuẩn hóa duy nhất, dùng chung cho IPN, dữ liệu tự quay và
webcam, biến chuỗi điểm mốc thô thành biểu diễn **bất biến với vị trí và tỉ lệ
nhưng giữ nguyên chuyển động**.

Đây là bước lý thuyết quan trọng nhất của tầng 3, và là chỗ đề tài này khác đề
cương cũ một cách có ý nghĩa.

### Lý thuyết cần nắm

#### 9.a. Tọa độ thô phụ thuộc vào những gì không liên quan tới cử chỉ

Cùng một cú vuốt trái, tọa độ thô sẽ khác nhau tùy: bàn tay ở góc nào của ảnh
(vị trí), tay gần hay xa camera và tay to hay nhỏ (tỉ lệ), độ phân giải và tỉ lệ
khung của camera. Mô hình học trên tọa độ thô sẽ học những yếu tố này thay vì
học cử chỉ — y như ví dụ "ngã = khung xương ở nửa dưới màn hình" trong tài liệu
`03`.

#### 9.b. Chọn bất biến là một quyết định thiết kế

Nguyên tắc từ tài liệu `03`, mục 2: **chỉ loại bỏ những biến thiên không mang
thông tin về lớp.** Áp dụng cho bàn tay:

| Biến thiên | Có mang thông tin cử chỉ? | Quyết định |
|---|---|---|
| Vị trí tuyệt đối của tay trong ảnh | Không | Loại bỏ |
| Cỡ bàn tay trong ảnh | Không | Loại bỏ |
| **Vị trí tay thay đổi trong cửa sổ** | **Có** — đó chính là cú vuốt | **Giữ** |
| **Hình dạng bàn tay thay đổi** | **Có** — đó chính là xòe/chụm | **Giữ** |
| Góc xoay bàn tay trong mặt phẳng ảnh | Một phần — xoay ảnh đi 180° thì vuốt trái thành vuốt phải | **Không** chuẩn hóa xoay |
| Tay trái hay tay phải | Không (với đề tài này) | Xử lý bằng tăng cường dữ liệu (bước 18) |

#### 9.c. Chọn gốc tọa độ: cổ tay **frame đầu cửa sổ**

Hai lựa chọn tự nhiên:

- **Gốc = cổ tay của từng frame.** Mỗi frame dời về cổ tay của chính nó. Hình
  dạng bàn tay giữ nguyên, nhưng **quỹ đạo bị xóa sạch**: cổ tay luôn ở (0, 0),
  vuốt trái và vuốt phải trông giống hệt đứng yên.
- **Gốc = cổ tay của frame đầu tiên trong cửa sổ.** Mọi frame dời cùng một vector.
  Hình dạng giữ nguyên, **quỹ đạo cũng giữ nguyên**, và vẫn bất biến với vị trí
  tay trong ảnh.

Lựa chọn thứ hai đúng cho đề tài. Có bằng chứng thực nghiệm trực tiếp: một
nghiên cứu năm 2025 dùng điểm mốc MediaPipe trên chính IPN Hand báo độ chính xác
84,66% khi lấy cổ tay frame đầu làm gốc, so với 83,67% khi lấy cổ tay từng frame.
Khác biệt nhỏ trên 14 lớp, nhưng với bài toán của bạn — nơi hai trong bốn lớp
chỉ khác nhau ở hướng di chuyển — nó sẽ lớn hơn nhiều. Bước 19 kiểm chứng điều này.

#### 9.d. Chọn đơn vị đo: cỡ lòng bàn tay

Chia mọi tọa độ cho **khoảng cách cổ tay (0) – gốc ngón giữa (9)**. Lý do chọn
đoạn này: nó nằm trên phần **gần như cứng** của bàn tay, **không đổi khi các
ngón co duỗi**. Nếu chia cho chiều dài cả bàn tay (cổ tay – đầu ngón giữa), thì
lúc chụm tay đơn vị đo co lại, tọa độ bị phóng to giả — và chính thông tin xòe/chụm
bị triệt tiêu. Lấy trung vị trên cả cửa sổ để đơn vị ổn định, không rung theo
từng frame. Đây cũng chính là đơn vị các tác giả MediaPipe dùng để đo sai số
(bước 6.e).

#### 9.e. Đổi sang pixel trước khi đo khoảng cách

`x` được chia cho chiều rộng ảnh, `y` chia cho chiều cao. Với ảnh 1280×720, 0,1
đơn vị theo x là 128 pixel, còn 0,1 đơn vị theo y chỉ là 72 pixel. Tính khoảng
cách trên tọa độ chuẩn hóa là **cộng hai đại lượng khác đơn vị** — và sai lệch
khác nhau giữa IPN (4:3) và webcam của bạn (16:9). Luôn nhân với `(W, H)` trước.

> **Tự kiểm tra.** (1) Nếu chuẩn hóa xoay mỗi cửa sổ sao cho trục cổ tay – ngón
> giữa luôn thẳng đứng, lớp nào sẽ bị hỏng? (2) Vì sao không chia cho chiều dài
> cả bàn tay?

### Việc cụ thể

**9.1. Viết `src/preprocess.py`:**

```python
import numpy as np
WRIST, MIDDLE_MCP = 0, 9

def to_pixels(seq_norm, w, h):
    """(T,21,2) tọa độ [0,1] → pixel, để hai trục cùng đơn vị."""
    return seq_norm * np.array([w, h], dtype=np.float32)

def normalize_window(seq_px):
    """(T,21,2) pixel → bất biến vị trí và tỉ lệ, GIỮ quỹ đạo trong cửa sổ.
    Giả định frame đầu có tay (đã vá lỗ ở bước 13)."""
    ref = seq_px[0, WRIST]                                    # cổ tay frame đầu
    palm = np.linalg.norm(seq_px[:, MIDDLE_MCP] - seq_px[:, WRIST], axis=1)
    scale = np.nanmedian(palm)
    if not np.isfinite(scale) or scale < 1e-6:
        return None
    return (seq_px - ref) / scale
```

**9.2. Viết thêm phiên bản "gốc từng frame"** (`normalize_window_per_frame`) —
dùng cho thí nghiệm so sánh ở bước 19.

**9.3. Viết hàm vẽ quỹ đạo:** vẽ đường đi của cổ tay và của đầu ngón trỏ trong
một cửa sổ đã chuẩn hóa. Hình này sẽ dùng rất nhiều lần.

### Kiểm chứng

- **Bất biến vị trí:** làm cùng một cú vuốt ở góc trái ảnh và góc phải ảnh →
  quỹ đạo chuẩn hóa gần trùng nhau.
- **Bất biến tỉ lệ:** làm cùng một cú xòe ở 0,4 m và 0,7 m → đường độ xòe theo
  thời gian gần trùng nhau.
- **Giữ quỹ đạo:** vuốt trái cho quỹ đạo cổ tay đi về một phía, vuốt phải về
  phía ngược lại.

Đặt ba cặp hình này cạnh nhau — đó là hình bằng chứng cho mục 4.3 của báo cáo.

### Sản phẩm

`src/preprocess.py` có kiểm thử, `notes/09-chuan-hoa.md`, ba cặp hình kiểm chứng.

### Cạm bẫy

| Cạm bẫy | Hậu quả | Xử lý |
|---|---|---|
| Lấy gốc cổ tay từng frame | Vuốt trái = vuốt phải = đứng yên | Gốc cổ tay frame đầu |
| Chia cho chiều dài cả bàn tay | Xòe/chụm bị triệt tiêu | Chia cho đoạn 0–9 |
| Đo khoảng cách trên tọa độ [0,1] | Méo khác nhau giữa 4:3 và 16:9 | Đổi sang pixel trước |
| Viết hai bản chuẩn hóa cho offline và online | Mô hình chạy thật khác lúc đánh giá | Một hàm duy nhất trong `src/` |

---

## Bước 10. Thiết kế đặc trưng

**Mục tiêu.** Một hàm biến mỗi cửa sổ đã chuẩn hóa thành một vector khoảng 20
con số, mỗi con số có ý nghĩa vật lý rõ ràng, và bằng chứng hình ảnh rằng các
đặc trưng này tách được các lớp.

### Lý thuyết cần nắm

**Vì sao tự thiết kế đặc trưng dù sẽ dùng LSTM.** Như tài liệu `04`: việc tự trả
lời "điều gì *thực sự* phân biệt các cử chỉ này?" là bài tập tư duy giá trị nhất
của đồ án. Và đặc trưng tốt cho phép một mô hình rất đơn giản đạt kết quả tốt,
dễ giải thích trước hội đồng.

**Bốn nhóm đặc trưng, mỗi nhóm trả lời một câu hỏi:**

| Nhóm | Câu hỏi | Đặc trưng |
|---|---|---|
| Hình dạng | Tay đang mở hay đóng, và đang mở ra hay khép lại? | Độ xòe đầu cửa sổ, cuối cửa sổ, **hiệu có dấu**, biên độ |
| Chuyển động | Tay đi về đâu, nhanh cỡ nào? | Độ dời cổ tay **có dấu** theo x và y, tốc độ ngang lớn nhất, vận tốc ngang trung bình có dấu |
| Hình học quỹ đạo | Chuyển động thẳng hay qua lại? | **Độ thẳng** = độ dời tổng / quãng đường đi |
| Chất lượng | Có đủ dữ liệu không? | Tỉ lệ frame có tay trong cửa sổ |

**Đặc trưng có dấu là ý tưởng then chốt** (tài liệu `03`, mục 7.d cũ). "Độ xòe
thay đổi 0,8" không phân biệt được xòe với chụm; "độ xòe thay đổi **+**0,8" và
"**−**0,8" thì có. Tương tự với độ dời cổ tay cho vuốt trái/phải.

**Độ thẳng tách vuốt khỏi vẫy.** Vuốt: đi một mạch về một phía → độ dời tổng
gần bằng quãng đường → độ thẳng gần 1. Vẫy qua lại: đi nhiều nhưng về gần chỗ cũ
→ độ thẳng gần 0. Một đặc trưng, giải quyết đúng câu hỏi "vẫy hay vuốt" ở bước 1.

### Việc cụ thể

**10.1. Viết `src/features.py`:**

```python
import numpy as np
WRIST, TIPS = 0, [4, 8, 12, 16, 20]

def openness(seq):
    """Độ xòe mỗi frame: khoảng cách TB từ 5 đầu ngón tới cổ tay CÙNG frame."""
    return np.linalg.norm(seq[:, TIPS] - seq[:, [WRIST]], axis=2).mean(axis=1)

def window_features(seq, presence_ratio):
    """seq: (T,21,2) đã chuẩn hóa ở bước 9."""
    o = openness(seq)
    wr = seq[:, WRIST]
    v = np.diff(wr, axis=0)
    net = wr[-1] - wr[0]
    path = np.linalg.norm(v, axis=1).sum() + 1e-6
    half = len(o) // 2
    return np.array([
        o[0], o[-1], o[-1] - o[0], o.max() - o.min(),        # hình dạng
        o[half:].mean() - o[:half].mean(),                   # xu hướng xòe, bền hơn với nhiễu
        net[0], net[1],                                      # độ dời có dấu
        np.abs(v[:, 0]).max(), v[:, 0].mean(),               # tốc độ ngang
        np.abs(v[:, 1]).max(),                               # tốc độ dọc (vuốt thường ít)
        np.linalg.norm(net) / path,                          # độ thẳng
        abs(net[0]) / (abs(net[1]) + 1e-6),                  # ngang hay dọc
        presence_ratio,                                      # chất lượng
    ], dtype=np.float32)

FEATURE_NAMES = ["open_start", "open_end", "open_delta", "open_range", "open_trend",
                 "dx", "dy", "max_vx", "mean_vx", "max_vy", "straightness",
                 "horiz_ratio", "presence"]
```

**10.2. Bổ sung tùy chọn:** góc gập ở khớp PIP của bốn ngón (công thức góc giữa
hai vector ở tài liệu `03`, mục 6) — đặc trưng hình dạng bất biến với xoay.

**10.3. Kiểm tra sơ bộ trên vài cử chỉ tự làm** trước webcam (chưa cần IPN):
in vector đặc trưng cho mỗi lớp, xem dấu của `open_delta` và `dx` có đúng như
kỳ vọng.

Bước 13 sẽ tính đặc trưng cho toàn bộ IPN; khi đó quay lại vẽ **boxplot từng đặc
trưng theo lớp**.

### Kiểm chứng

- Xòe: `open_delta > 0`. Chụm: `open_delta < 0`.
- Vuốt trái và vuốt phải: `dx` trái dấu nhau, `straightness` gần 1.
- Vẫy qua lại: `straightness` nhỏ.

### Sản phẩm

`src/features.py`, `notes/10-dac-trung.md` giải thích ý nghĩa từng đặc trưng.

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Dùng giá trị tuyệt đối cho độ dời, độ xòe | Giữ dấu — dấu chính là thông tin |
| Tính độ xòe so với cổ tay frame đầu | Phải so với cổ tay **cùng frame** — nếu không, độ xòe lẫn với độ dời |
| Hàng trăm đặc trưng "cho chắc" | Mỗi đặc trưng phải trả lời được "nó phân biệt cặp lớp nào" |

---

## Bước 11. Mô hình 0 — luật, và demo đầu tiên

**Mục tiêu.** Một bộ phân loại dựa trên vài luật if/else trên đặc trưng, gắn vào
webcam và PowerPoint: **demo điều khiển slide thật đầu tiên**, trước khi có
bất kỳ mô hình học máy nào.

### Lý thuyết cần nắm

**Luật là một cây quyết định viết bằng tay.** Mỗi luật là một nhánh; ngưỡng là
điểm chia. Rừng ngẫu nhiên ở bước 15 làm đúng việc này, nhưng tự tìm ngưỡng và
kết hợp hàng trăm cây.

**Vì sao cần mô hình luật dù sẽ bị thay thế.** (1) Là **đường cơ sở**: một mô
hình học máy không vượt được luật thì không đáng dùng. (2) Cho demo sớm. (3) Và
nó sẽ **thất bại theo cách có ích**: luật thường bắt được cử chỉ chuẩn nhưng
bắn nhầm khi người dùng cử động tự nhiên — chính là lý do cần học từ dữ liệu có
lớp nền.

**Chọn ngưỡng từ dữ liệu, không đoán.** Sau bước 13 bạn có phân bố đặc trưng
theo lớp trên IPN; ngưỡng tốt nằm ở chỗ hai phân bố tách nhau. Tạm thời ở tuần 4,
chọn ngưỡng từ vài chục lần tự làm trước webcam, rồi chỉnh lại sau.

### Việc cụ thể

**11.1. Viết `src/models_rule.py`:**

```python
def rule_classify(f, th):
    """f: dict đặc trưng của một cửa sổ; th: dict ngưỡng."""
    if f["presence"] < th["presence"]:
        return "none"
    if (abs(f["dx"]) > th["dx"] and f["straightness"] > th["straight"]
            and f["horiz_ratio"] > th["horiz"]):
        return "swipe_left" if f["dx"] * th["left_sign"] > 0 else "swipe_right"
    if f["open_trend"] > th["open"] and abs(f["dx"]) < th["dx_still"]:
        return "zoom_in"
    if f["open_trend"] < -th["open"] and abs(f["dx"]) < th["dx_still"]:
        return "zoom_out"
    return "none"
```

`th["left_sign"]` là dấu của `dx` khi làm vuốt trái, **đo bằng thực nghiệm** ở
bước 5.3. Với ảnh không lật và "trái" hiểu theo người làm, tay đi về phía phải
của ảnh nên `left_sign = +1`. Đừng viết cứng dấu vào code: đặt nó trong
`config.py`, và bước 12.4 sẽ dùng lại đúng hằng số này để kiểm tra IPN.

**11.2. Ghép vào vòng lặp webcam:** hàng đợi `deque` giữ các frame gần nhất,
mỗi 2 bước lấy cửa sổ, chuẩn hóa, tính đặc trưng, chạy luật. Tạm dùng logic
kích hoạt đơn giản: bắn lệnh khi 3 dự đoán liên tiếp giống nhau, nghỉ 1 giây.
(Tạm thời chưa lấy mẫu lại 15 Hz — sẽ thay bằng đường ống chuẩn ở bước 13.)

**11.3. Hiển thị trên màn hình:** nhãn dự đoán hiện tại, các đặc trưng chính,
lệnh vừa bắn.

**11.4. Thử điều khiển một bài trình chiếu 10 slide.** Ghi lại: bao nhiêu lần
đúng, bao nhiêu lần sai chiều, bao nhiêu lần bắn nhầm khi bạn chỉ gõ phím hoặc
chạm mặt.

### Kiểm chứng

Điều khiển được slide tiến, lùi, phóng to, thu nhỏ trong điều kiện "làm mẫu".
Và có một danh sách cụ thể các tình huống luật thất bại.

### Sản phẩm

**Video demo điều khiển slide đầu tiên** — thứ để trình bày ở buổi báo cáo tiến
độ tiếp theo. Danh sách tình huống thất bại — động lực cho chương mô hình học máy.

### Cạm bẫy

| Hiện tượng | Nguyên nhân | Xử lý |
|---|---|---|
| Vuốt trái ra lệnh vuốt phải | Chưa xác định quy ước dấu (bước 5.3) | Kiểm lại dấu `dx` bằng thực nghiệm |
| Mỗi cử chỉ bắn 2 lệnh | Chưa có thời gian nghỉ / cơ chế nhả | Tạm dùng thời gian nghỉ; giải quyết triệt để ở bước 20 |
| Sau khi xòe, muốn xòe tiếp thì phải chụm lại → bắn lệnh thu nhỏ | Vấn đề cố hữu của cặp cử chỉ ngược nhau | Ghi nhận; giải quyết ở bước 20 |

---

# GIAI ĐOẠN D — DỮ LIỆU (Tuần 5)

---

## Bước 12. Trích điểm mốc từ IPN Hand

**Mục tiêu.** 200 file `.npz`, mỗi file chứa chuỗi điểm mốc của một video IPN,
kèm thống kê tỉ lệ phát hiện theo video và theo lớp, và **quy ước hướng đã được
kiểm chứng bằng số liệu**.

### Lý thuyết cần nắm

**Trích một lần, dùng mãi.** Chạy Hand Landmarker trên 800.000 frame mất vài
giờ. Làm một lần, lưu lại, mọi thí nghiệm sau đó chạy trên file đã lưu trong vài
giây. Cùng triết lý với đề cương cũ.

**Trạng thái bám theo phải được khởi tạo lại cho mỗi video.** Ở chế độ VIDEO,
landmarker nhớ vị trí tay của frame trước. Nếu dùng chung một landmarker cho hai
video, frame đầu của video thứ hai sẽ được "bám" từ vị trí tay cuối video thứ
nhất. Thêm nữa, mốc thời gian phải tăng nghiêm ngặt — video thứ hai lại bắt đầu
từ 0. Tạo landmarker mới cho mỗi video giải quyết cả hai.

**Mốc thời gian từ chỉ số frame**, không từ đồng hồ: `ts_ms = int(i * 1000 / fps)`.
Với video đã quay, thời gian thật là thời gian trong video, không phải thời gian
máy tính xử lý.

**Frame thiếu tay lưu dưới dạng NaN**, không bỏ đi. Bỏ đi làm lệch chỉ số frame
so với file nhãn — mọi nhãn phía sau sẽ sai.

### Việc cụ thể

**12.1. Viết `scripts/01_extract_ipn.py`:**

```python
import cv2, numpy as np, mediapipe as mp
from pathlib import Path
from tqdm import tqdm

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

def extract_video(path, model_path="models/hand_landmarker.task"):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    opts = HandLandmarkerOptions(base_options=BaseOptions(model_asset_path=model_path),
                                 running_mode=RunningMode.VIDEO, num_hands=1)
    lms, hand, score = [], [], []
    with HandLandmarker.create_from_options(opts) as lm:       # MỚI cho mỗi video
        i = 0
        while True:
            ok, bgr = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            res = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb),
                                      int(i * 1000 / fps))
            if res.hand_landmarks:
                lms.append([[p.x, p.y] for p in res.hand_landmarks[0]])
                c = res.handedness[0][0]
                hand.append(1 if c.category_name == "Right" else 0); score.append(c.score)
            else:
                lms.append(np.full((21, 2), np.nan)); hand.append(-1); score.append(0.0)
            i += 1
    cap.release()
    return dict(lms=np.asarray(lms, np.float32), hand=np.asarray(hand, np.int8),
                score=np.asarray(score, np.float32), wh=np.array([w, h]), fps=fps)

if __name__ == "__main__":
    out = Path("data/ipn/landmarks"); out.mkdir(parents=True, exist_ok=True)
    for vp in tqdm(sorted(Path("data/ipn/videos").glob("*.mp4"))):
        dst = out / (vp.stem + ".npz")
        if dst.exists():
            continue                                 # chạy lại được sau khi bị ngắt
        np.savez_compressed(dst, **extract_video(vp))
```

**12.2. Chạy qua đêm.** Nếu muốn nhanh hơn, chạy 2–3 tiến trình song song, mỗi
tiến trình một phần danh sách video (CPU của bạn có 4 nhân). Dòng `if dst.exists()`
cho phép chạy tiếp sau khi bị ngắt.

**12.3. Thống kê tỉ lệ phát hiện:** theo video, theo lớp (dùng file nhãn để biết
frame nào thuộc lớp nào), theo cảnh quay. Để có mốc so sánh: một nhóm nghiên cứu
chạy MediaPipe trên Jester (ảnh chỉ cao 100 pixel) báo khoảng 36% bước thời gian
không tìm thấy tay. IPN có độ phân giải cao hơn nhiều, nên tỉ lệ thiếu kỳ vọng
thấp hơn rõ — nhưng các cảnh tối và các lớp vuốt sẽ cao hơn trung bình.

**12.4. Kiểm chứng quy ước hướng — việc bắt buộc.** Với mỗi mẫu G05 và G06, tính
độ dời ngang của cổ tay từ đầu tới cuối cử chỉ (đổi sang pixel). Lấy trung vị
theo lớp. Rồi **tự làm "hất trái" theo đúng cách IPN làm** trước webcam của bạn
(ảnh không lật), tính cùng đại lượng. Hai dấu phải trùng nhau. Nếu ngược: IPN
được quay với ảnh đã lật → khi nạp dữ liệu IPN, lật ngang tọa độ (`x → 1 − x`)
**trước mọi bước khác**.

### Kiểm chứng

- Số frame trong mỗi `.npz` bằng số frame video và khớp với cột frame trong
  file nhãn.
- Vẽ điểm mốc từ `.npz` lên lại video cho 2–3 video ngẫu nhiên: điểm phải nằm
  đúng trên tay.
- Bước 12.4 có kết luận rõ ràng, ghi vào `notes/`.

### Sản phẩm

`data/ipn/landmarks/*.npz`; bảng tỉ lệ phát hiện theo lớp và theo cảnh; kết
luận quy ước hướng. Bảng tỉ lệ phát hiện là một bảng của chương 3.

### Cạm bẫy

| Cạm bẫy | Hậu quả | Xử lý |
|---|---|---|
| Dùng chung landmarker cho nhiều video | Lỗi timestamp, hoặc bám nhầm giữa hai video | Tạo mới cho mỗi video |
| Bỏ frame không có tay | Lệch chỉ số với nhãn | Lưu NaN |
| Lưu float64 và cả `z`, world landmarks | File to gấp nhiều lần, không dùng tới | `float32`, chỉ `x, y` |
| Bỏ qua 12.4 | Mô hình học ngược hướng, không báo lỗi | Bắt buộc kiểm chứng |

---

## Bước 13. Tiền xử lý chuỗi, cắt cửa sổ, gán nhãn, chia tập

**Mục tiêu.** Một đường ống duy nhất biến `.npz` + file nhãn thành các mảng
`X_seq (N, T, 21, 2)`, `X_feat (N, F)`, `y (N,)`, `groups (N,)` sẵn sàng huấn
luyện — và cũng chính đường ống đó chạy được trên luồng webcam.

### Lý thuyết cần nắm

#### 13.a. Lấy mẫu lại về một tần số chung

IPN quay 30 FPS; webcam lúc chạy thật dao động 20–30 FPS tùy ánh sáng. Nếu cửa
sổ định nghĩa bằng **số frame**, cùng 30 frame sẽ là 1 giây ở IPN nhưng 1,5 giây
ở webcam lúc tối — mô hình thấy cử chỉ "chậm hơn" bình thường. Giải pháp: nội
suy mọi chuỗi về **một lưới thời gian đều 15 Hz** trước khi làm bất cứ gì. 15 Hz
đủ để bắt cử chỉ tay (IPN có cử chỉ ngắn nhất khoảng 9 frame ở 30 FPS) và giảm
một nửa khối lượng tính toán.

#### 13.b. Vá lỗ hổng ngắn, đánh dấu lỗ hổng dài

Mất tay 1–3 bước (≤ 0,2 s) thường do nhòe hoặc bám thất bại thoáng qua — nội suy
tuyến tính giữa hai frame có tay là hợp lý. Mất lâu hơn nghĩa là tay thực sự rời
khung hoặc bị che — không được bịa dữ liệu. Giữ NaN; cửa sổ nào thiếu quá 30%
thì loại khỏi huấn luyện, và lúc chạy thật thì trả về "không cử chỉ".

#### 13.c. Cửa sổ trượt có tính nhân quả

Như tài liệu `04`, mục 1: mỗi cửa sổ chỉ gồm các bước **đã xảy ra**. Độ dài `T`
(mặc định 1 giây = 15 bước) và bước trượt `S` (mặc định 2 bước).

#### 13.d. Gán nhãn cho cửa sổ: quy tắc chồng lấn và vùng xám

Một cửa sổ có thể chồng lên một phần cử chỉ. Quy tắc ba vùng:

| Tỉ lệ cửa sổ bị một cử chỉ đích chiếm | Nhãn cửa sổ |
|---|---|
| ≥ 60% | Lớp của cử chỉ đó |
| ≤ 20% | `none` |
| Giữa 20% và 60% | **Bỏ khỏi tập huấn luyện** (vùng xám) |

Vùng xám tồn tại vì một cửa sổ chỉ chạm mép cử chỉ là **mơ hồ thật sự** — ép
nó thành lớp nào cũng dạy mô hình điều sai. Các frame thuộc lớp "bỏ qua" (G07)
cũng làm cửa sổ bị loại.

#### 13.e. Mất cân bằng lớp

Lớp `none` sẽ nhiều hơn các lớp đích hàng chục lần (các lớp nền của IPN dài và
nhiều). Hai cách, dùng cả hai: **lấy mẫu con** lớp `none` trong tập huấn luyện
(ví dụ tối đa gấp 3 lần lớp đích lớn nhất), và **trọng số lớp** trong hàm mất mát.
Tập kiểm thử **giữ nguyên phân bố thật** — không lấy mẫu con.

#### 13.f. Chia tập theo người

Tài liệu `05`, mục 4: các cửa sổ chồng lấn của cùng một cử chỉ gần như giống
hệt nhau; chia ngẫu nhiên theo cửa sổ cho kết quả cao giả tạo. IPN đã chia sẵn
train/test theo người — dùng nguyên. Trong tập train, tách thêm một số người
làm tập kiểm định (hoặc dùng `GroupKFold` với nhóm = người) để chọn siêu tham số.

> **Tự kiểm tra.** Vì sao lấy mẫu con lớp `none` ở tập huấn luyện thì được, còn ở
> tập kiểm thử thì không?

### Việc cụ thể

**13.1. Hàm lấy mẫu lại và vá lỗ** trong `src/preprocess.py`:

```python
def resample(ts, pts, hz=15.0):
    """ts: (N,) giây; pts: (N,21,2) pixel, có thể NaN → lưới thời gian đều."""
    grid = np.arange(ts[0], ts[-1] + 1e-9, 1.0 / hz)
    out = np.empty((len(grid), 21, 2), np.float32)
    for j in range(21):
        for c in range(2):
            out[:, j, c] = np.interp(grid, ts, pts[:, j, c])   # NaN lan sang lân cận: chấp nhận
    return grid, out

def fill_short_gaps(x, max_gap=3):
    """Nội suy tuyến tính các đoạn NaN dài ≤ max_gap bước; đoạn dài hơn giữ NaN."""
    x = x.copy(); miss = np.isnan(x[:, 0, 0]); n = len(x); i = 0
    while i < n:
        if not miss[i]:
            i += 1; continue
        j = i
        while j < n and miss[j]:
            j += 1
        if i > 0 and j < n and (j - i) <= max_gap:
            w = (np.arange(i, j) - (i - 1)) / (j - (i - 1))
            x[i:j] = x[i - 1] + w[:, None, None] * (x[j] - x[i - 1])
        i = j
    return x
```

**13.2. Nhãn theo frame → theo bước 15 Hz.** Từ file nhãn IPN, dựng mảng nhãn
cho từng frame 30 FPS (theo bảng ánh xạ bước 8, dùng mã `IGNORE` cho G07), rồi
lấy nhãn tại mốc thời gian gần nhất của mỗi bước trên lưới 15 Hz.

**13.3. Cắt cửa sổ** trong `src/windows.py`:

```python
def label_window(lab, none_id, ignore_id, pos=0.6, neg=0.2):
    """lab: nhãn của T bước trong cửa sổ. Trả về nhãn hoặc None (bỏ cửa sổ)."""
    T = len(lab)
    if (lab == ignore_id).mean() > neg:
        return None
    g = lab[(lab != none_id) & (lab != ignore_id)]
    if len(g) == 0:
        return none_id
    vals, cnt = np.unique(g, return_counts=True)
    frac = cnt.max() / T
    if frac >= pos:
        return vals[cnt.argmax()]
    return none_id if frac <= neg else None           # None = vùng xám

def make_windows(seq_px, lab, T, S, none_id, ignore_id, max_missing=0.3):
    for end in range(T, len(seq_px) + 1, S):
        w = seq_px[end - T:end]
        miss = np.isnan(w[:, 0, 0]).mean()
        if miss > max_missing or np.isnan(w[0, 0, 0]):
            continue
        y = label_window(lab[end - T:end], none_id, ignore_id)
        if y is None:
            continue
        yield end, w, 1.0 - miss, y
```

Với mỗi cửa sổ giữ lại: vá NaN còn sót bằng giá trị hợp lệ gần nhất, chuẩn hóa
(bước 9), tính đặc trưng (bước 10), lưu kèm mã người quay (`groups`) và vị trí
kết thúc (để bước 22 dựng lại chuỗi dự đoán theo thời gian).

**13.4. Lưu** `data/windows/ipn_T15_S2.npz` gồm `X_seq`, `X_feat`, `y`, `groups`,
`video`, `end`. Tên file ghi rõ `T` và `S` — bước 19 sẽ tạo nhiều phiên bản.

**13.5. Vẽ boxplot từng đặc trưng theo lớp** trên tập train. Quay lại bước 11,
chỉnh ngưỡng của mô hình luật theo các phân bố này.

**13.6. Đưa đường ống vào luồng webcam:** thay phần xử lý tạm ở bước 11 bằng
`resample` → `fill_short_gaps` → `normalize_window` → `window_features`. Từ giờ
offline và online dùng chung code.

### Kiểm chứng

- Bảng số cửa sổ theo lớp × train/test. Lớp đích mỗi lớp nên có vài trăm tới vài
  nghìn cửa sổ.
- Không có mã người nào xuất hiện ở cả train và test (`set(groups_train) & set(groups_test)` rỗng).
- Boxplot `open_trend` tách rõ `zoom_in` / `zoom_out`; boxplot `dx` tách rõ hai
  lớp vuốt. Nếu không tách, quay lại kiểm tra bước 9–12 trước khi đi tiếp.

### Sản phẩm

`data/windows/*.npz`, bảng thống kê cửa sổ, boxplot đặc trưng — hình cho mục
3.3 và 4.4 của báo cáo.

### Cạm bẫy

| Cạm bẫy | Hậu quả | Xử lý |
|---|---|---|
| Cửa sổ định nghĩa bằng số frame, không lấy mẫu lại | Lệch tốc độ giữa IPN và webcam | Lấy mẫu lại 15 Hz theo thời gian |
| Nội suy qua lỗ hổng dài | Bịa ra chuyển động không có thật | Chỉ vá ≤ 3 bước |
| Chia ngẫu nhiên theo cửa sổ | Độ chính xác giả 95–99% | Chia theo người |
| Lấy mẫu con lớp `none` ở tập kiểm thử | Số kích hoạt nhầm bị đánh giá thấp | Tập kiểm thử giữ nguyên |
| Tính trung bình / độ lệch chuẩn để chuẩn hóa đặc trưng trên toàn bộ dữ liệu | Rò rỉ qua chuẩn hóa (tài liệu `05`, mục 4) | Chỉ tính trên tập train |

---

## Bước 14. Tự quay dữ liệu kiểm thử

**Mục tiêu.** Bộ dữ liệu nhỏ quay trên **chính ThinkPad của bạn** theo đúng tư
thế sẽ demo, gồm hai phần: cử chỉ cô lập có nhãn, và phiên làm việc tự nhiên
có nhãn thời gian.

### Lý thuyết cần nắm

**Chuyển miền (domain shift).** IPN do 50 người khác quay bằng 50 camera khác,
ở 28 cảnh khác. Mô hình học tốt trên IPN chưa chắc tốt trên camera, ánh sáng,
góc ngồi của bạn. Chỉ có một cách biết: đo trên dữ liệu thật của môi trường
đích. Bộ dữ liệu tự quay chính là "môi trường đích" thu nhỏ — và là thứ hội
đồng thực sự quan tâm.

**Hai loại dữ liệu, hai mục đích.** *Cử chỉ cô lập* đo "nhận có đúng không khi
người dùng cố ý ra lệnh". *Phiên làm việc tự nhiên* đo "có bắn nhầm khi người
dùng **không** ra lệnh không" — thứ quyết định hệ thống có dùng được hay không.

**Đồng ý tham gia.** Quay video người khác cần sự đồng ý. Một tờ giấy đồng ý
đơn giản (dùng cho mục đích đồ án, không công bố video) là đủ và thể hiện sự
chuyên nghiệp.

### Việc cụ thể

**14.1. Giao thức quay:**

| Hạng mục | Quy định |
|---|---|
| Người tham gia | 4–6 người, khác nhau về cỡ tay, màu da, có người đeo kính / đồng hồ |
| Tư thế | Ngồi trước ThinkPad như làm việc, laptop trên bàn, màn hình mở góc bình thường |
| Ánh sáng | Hai điều kiện: đèn phòng đầy đủ, và hơi tối (chỉ đèn bàn hoặc ánh sáng màn hình) |
| Cử chỉ cô lập | Mỗi lớp 10–15 lần, tay thuận; thêm 5 lần bằng tay không thuận |
| Phiên tự nhiên | 5 phút mỗi người: gõ một đoạn văn, dùng chuột, uống nước, chạm mặt, chỉnh kính; script nhắc "làm lệnh X" khoảng 10 lần xen giữa |
| Lưu | Video gốc (để trích lại được) + điểm mốc + mốc thời gian mỗi frame |

**14.2. Script quay có nhắc lệnh** (`scripts/03_record_own.py`): hiển thị
"VUỐT TRÁI sau 3…2…1", ghi thời điểm nhắc vào file nhãn. Người diễn làm cử chỉ
trong vài giây sau lời nhắc.

**14.3. Công cụ gán nhãn:** script mở video, tua từng frame bằng phím mũi tên,
phím `s` đánh dấu bắt đầu, `e` kết thúc, số `1`–`4` chọn lớp. Dùng lời nhắc ở
14.2 để nhảy nhanh tới gần cử chỉ, rồi chỉnh ranh giới chính xác. Lưu cùng định
dạng với nhãn IPN (video, lớp, frame bắt đầu, frame kết thúc) để dùng lại toàn
bộ đường ống bước 13.

**14.4. Chạy trích điểm mốc** (dùng lại hàm của bước 12) và cắt cửa sổ (bước 13).

### Kiểm chứng

- Chồng nhãn lên video như bước 8 cho vài đoạn.
- Mỗi người có đủ mẫu của cả bốn lớp.

### Sản phẩm

`data/own/`, giấy đồng ý, bảng thống kê. Mục 3.4 của báo cáo.

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Chỉ quay bản thân | Ít nhất 4 người; chia theo người khi đánh giá |
| Người diễn làm cử chỉ "quá chuẩn" vì biết đang bị quay | Phiên tự nhiên quay trước, cử chỉ cô lập quay sau |
| Quên lưu mốc thời gian mỗi frame | Không lấy mẫu lại đúng được; FPS webcam dao động |
| Dùng dữ liệu tự quay để chỉnh ngưỡng rồi lại đo trên chính nó | Tách người: một phần để chỉnh, phần còn lại để đo |

---

# GIAI ĐOẠN E — MÔ HÌNH (Tuần 6–8)

---

## Bước 15. Mô hình 1 — rừng ngẫu nhiên

**Mục tiêu.** Bộ phân loại RF trên vector đặc trưng, huấn luyện trên IPN, chọn
siêu tham số bằng kiểm định chéo theo người, gắn vào demo thay cho mô hình luật.

### Lý thuyết cần nắm

Toàn bộ tài liệu `04`, mục 3: cây quyết định (chia theo đặc trưng và ngưỡng làm
giảm độ hỗn tạp nhiều nhất), từ một cây thành một rừng (mỗi cây học trên một mẫu
bootstrap và một tập con đặc trưng ngẫu nhiên, rồi bỏ phiếu), vì sao rừng giảm
quá khớp so với một cây. Bổ sung ba điểm:

**Trọng số lớp.** `class_weight="balanced"` nhân trọng số mỗi mẫu tỉ lệ nghịch
với tần suất lớp, để lớp đích hiếm không bị lớp `none` áp đảo.

**Kiểm định chéo theo nhóm.** `GroupKFold(n_splits=5)` với nhóm = người quay:
mỗi lượt, một phần người làm tập kiểm định. Chọn siêu tham số theo **macro-F1**
trung bình, không theo độ chính xác (lý do ở bước 16).

**Độ quan trọng đặc trưng — dùng cẩn thận.** `feature_importances_` của RF thiên
vị đặc trưng liên tục và chia điểm tầm quan trọng giữa các đặc trưng tương quan
(ví dụ `open_delta` và `open_trend`). **Permutation importance** trên tập kiểm
định đáng tin hơn: xáo trộn một cột, đo độ tụt của macro-F1.

### Việc cụ thể

**15.1.** Chuẩn hóa đặc trưng (StandardScaler — thật ra RF không cần, nhưng giữ
đường ống đồng nhất với các mô hình khác) **chỉ fit trên train**.

**15.2.** Tìm siêu tham số trên lưới nhỏ: `n_estimators ∈ {200, 500}`,
`max_depth ∈ {None, 12, 20}`, `min_samples_leaf ∈ {1, 3, 5}`, bằng
`GroupKFold` trên tập train IPN.

**15.3.** Huấn luyện lại trên toàn bộ train với siêu tham số tốt nhất, lưu mô
hình bằng `joblib`.

**15.4.** Tính permutation importance, vẽ biểu đồ xếp hạng.

**15.5.** Thay mô hình luật trong demo bằng RF. Chơi thử: nó bắn nhầm ít hơn
luật không?

### Kiểm chứng

- Macro-F1 kiểm định chéo có độ lệch chuẩn nhỏ giữa các lượt — nếu một lượt tụt
  hẳn, xem người nào nằm trong lượt đó (có thể cảnh quay rất tối).
- Đặc trưng quan trọng nhất có hợp lý không? Kỳ vọng: nhóm độ xòe có dấu và độ
  dời có dấu đứng đầu.

### Sản phẩm

Mô hình RF đã lưu; biểu đồ độ quan trọng đặc trưng — hình đẹp cho chương 5.
**Mốc an toàn tuần 6**: từ đây bạn đã có hệ thống học máy hoàn chỉnh.

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Dùng `KFold` thường thay vì `GroupKFold` | Rò rỉ theo người, kết quả kiểm định chéo quá lạc quan |
| Chọn siêu tham số theo độ chính xác | Mô hình "đoán none hết" cũng đạt độ chính xác cao; dùng macro-F1 |
| Tin tuyệt đối vào `feature_importances_` | Đối chiếu với permutation importance |

---

## Bước 16. Đánh giá mức cửa sổ đúng cách

**Mục tiêu.** Một bộ số liệu đánh giá trung thực cho RF (và sau này LSTM) trên
tập test IPN và trên dữ liệu tự quay, với ma trận nhầm lẫn đọc được thành phát
hiện có ý nghĩa.

### Lý thuyết cần nắm

Toàn bộ tài liệu `05`. Ba điểm áp dụng riêng:

**Macro-F1 là chỉ số chính.** Với lớp `none` chiếm đa số, độ chính xác tổng thể
bị lớp này chi phối. Macro-F1 lấy trung bình F1 của từng lớp với trọng số bằng
nhau — lớp đích hiếm được tính ngang lớp `none`.

**Không phải mọi lỗi đều như nhau.** Trong ma trận nhầm lẫn 5×5, phân biệt:

| Loại lỗi | Ví dụ | Hậu quả với người dùng | Mức nghiêm trọng |
|---|---|---|---|
| **Sai chiều** | `swipe_left` → `swipe_right` | Slide lùi khi muốn tiến | Cao nhất |
| **Bắn nhầm** | `none` → bất kỳ lớp đích | Slide nhảy khi đang nói | Cao |
| Sai loại | `swipe_left` → `zoom_in` | Lệnh sai, dễ nhận ra | Trung bình |
| **Bỏ sót** | lớp đích → `none` | Phải làm lại cử chỉ | Thấp nhất |

Một hệ thống có recall hơi thấp nhưng gần như không bao giờ bắn nhầm hay sai
chiều **dùng được tốt hơn** hệ thống ngược lại. Viết điều này ra trong báo cáo
— nó cho thấy bạn hiểu bài toán từ phía người dùng.

**Hai tập kiểm thử, hai câu hỏi.** Test IPN: "mô hình tổng quát hóa sang người
lạ trong điều kiện đa dạng ra sao?". Dữ liệu tự quay: "mô hình chạy trong môi
trường thật của demo ra sao?". Báo cáo cả hai, không gộp.

### Việc cụ thể

**16.1.** Viết `src/evaluate.py`: classification report, macro-F1, ma trận nhầm
lẫn chuẩn hóa theo hàng (vẽ dạng hình nhiệt), và hai con số riêng: **tỉ lệ sai
chiều** (trên các cửa sổ vuốt và zoom) và **tỉ lệ bắn nhầm ở mức cửa sổ** (tỉ lệ
cửa sổ `none` bị dự đoán thành lớp đích).

**16.2.** Đánh giá RF trên test IPN và trên dữ liệu tự quay.

**16.3.** Mở ra xem 10–20 cửa sổ bị phân loại sai: vẽ quỹ đạo và đường độ xòe.
Chúng sai vì gì? Phân nhóm nguyên nhân.

### Kiểm chứng

Con số trên dữ liệu tự quay thấp hơn trên test IPN là **bình thường** — chuyển
miền. Nếu nó cao hơn hẳn, nghi ngờ rò rỉ (ví dụ vô tình dùng dữ liệu tự quay khi
chọn ngưỡng).

### Sản phẩm

Bảng kết quả RF, hai ma trận nhầm lẫn, phân tích lỗi — phần cốt lõi của chương 5
và 6.

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Chỉ báo độ chính xác | Báo macro-F1, P/R từng lớp, tỉ lệ sai chiều |
| Gộp hai tập kiểm thử thành một con số | Báo riêng |
| Chỉ nhìn con số, không xem mẫu sai | Mục 16.3 là nơi nghiên cứu thật sự diễn ra |

---

## Bước 17. PyTorch và đường ống dữ liệu

**Mục tiêu.** Bạn viết được vòng huấn luyện PyTorch từ đầu và có `Dataset` /
`DataLoader` cho dữ liệu cửa sổ.

### Lý thuyết cần nắm

Tài liệu `04`, mục 4 (nơ-ron, lớp, softmax, cross-entropy, gradient descent).
Thêm các khái niệm PyTorch:

| Khái niệm | Ý nghĩa |
|---|---|
| Tensor | Mảng nhiều chiều, như numpy, nhưng tính được đạo hàm |
| Autograd | Ghi lại phép tính, gọi `loss.backward()` là có gradient của mọi tham số |
| `nn.Module` | Lớp chứa tham số và hàm `forward` |
| Optimizer | Cập nhật tham số từ gradient (`Adam` là lựa chọn mặc định tốt) |
| `model.train()` / `model.eval()` | Bật / tắt dropout; quên `eval()` khi đánh giá thì kết quả dao động |
| `torch.no_grad()` | Tắt ghi đạo hàm khi đánh giá, tiết kiệm bộ nhớ |
| Early stopping | Dừng khi loss kiểm định không giảm sau N epoch, giữ mô hình tốt nhất |

**Vòng huấn luyện năm dòng cốt lõi** — thuộc lòng:

```python
for xb, yb in train_loader:
    optimizer.zero_grad()
    loss = criterion(model(xb), yb)
    loss.backward()
    optimizer.step()
```

### Việc cụ thể

**17.1.** Làm hướng dẫn "Learn the Basics" chính thức của PyTorch (khoảng 2–3 giờ).

**17.2.** Viết `WindowDataset`: nhận `X_seq (N, T, 21, 2)`, trả về tensor
`(T, 42)` và nhãn. Chuẩn hóa từng kênh bằng trung bình/độ lệch chuẩn **của tập
train**.

**17.3.** Viết hàm `train_one_epoch`, `evaluate`, vòng lặp có early stopping, và
cố định seed (`torch.manual_seed`, `numpy`, `random`).

**17.4.** Chạy thử với một mô hình tầm thường (làm phẳng + một lớp tuyến tính)
để kiểm tra toàn bộ đường ống.

### Kiểm chứng

**Phép thử quá khớp một batch:** huấn luyện trên đúng một batch 32 mẫu nhiều
epoch — loss phải về gần 0. Nếu không, đường ống có lỗi (nhãn lệch, quên
`zero_grad`, sai chiều tensor).

### Sản phẩm

`src/models_lstm.py` phần dữ liệu và vòng huấn luyện; `notes/17-pytorch.md`.

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Quên `optimizer.zero_grad()` | Gradient cộng dồn qua các batch, huấn luyện loạn |
| Nhãn kiểu float thay vì `long` | `CrossEntropyLoss` báo lỗi |
| Chuẩn hóa bằng thống kê toàn bộ dữ liệu | Rò rỉ — chỉ dùng train |

---

## Bước 18. Mô hình 2 — LSTM và tăng cường dữ liệu

**Mục tiêu.** Mô hình LSTM (hoặc GRU) học trực tiếp từ chuỗi điểm mốc đã chuẩn
hóa, có tăng cường dữ liệu phù hợp với bài toán, so sánh được với RF.

### Lý thuyết cần nắm

**RNN, gradient tiêu biến, LSTM** — tài liệu `04`, mục 5 trở đi. Tóm tắt: RNN
mang một trạng thái ẩn qua các bước thời gian, nhưng gradient qua nhiều bước bị
nhân liên tiếp nên tiêu biến. LSTM thêm một "băng chuyền" trạng thái ô nhớ với
ba cổng (quên, vào, ra) điều tiết thông tin, cho gradient đi qua nhiều bước. GRU
là phiên bản gọn hơn với hai cổng — ít tham số hơn, thường ngang LSTM trên chuỗi
ngắn.

**Cỡ mô hình so với cỡ dữ liệu.** Mỗi lớp đích của IPN chỉ có 200 cử chỉ (vài
trăm tới vài nghìn cửa sổ chồng lấn — nhưng cửa sổ chồng lấn **không** phải dữ
liệu độc lập). Một LSTM 2 lớp × 128 chiều có hơn 200.000 tham số — dư sức học
thuộc lòng. Bắt đầu nhỏ: 1 lớp × 64 chiều, dropout 0,3.

**Tăng cường dữ liệu — phải tôn trọng ngữ nghĩa lớp.** Mỗi phép biến đổi phải
trả lời: "biến đổi này có làm đổi lớp không?"

| Phép tăng cường | Mô phỏng điều gì | Chú ý |
|---|---|---|
| **Lật ngang** (x → −x sau chuẩn hóa) | Tay trái ↔ tay phải | **Đổi nhãn** `swipe_left` ↔ `swipe_right`; zoom giữ nguyên |
| Co giãn ±10% | Tay to/nhỏ, chuẩn hóa chưa hoàn hảo | Không đổi nhãn |
| Xoay nhỏ ±10° | Camera hơi nghiêng, tay hơi nghiêng | Không xoay lớn — xoay lớn biến vuốt ngang thành vuốt chéo |
| Co giãn thời gian 0,8–1,2× | Người làm nhanh / chậm (IPN có độ biến thiên tốc độ rất lớn) | Nội suy lại về đúng T bước |
| Nhiễu Gauss nhỏ | Độ rung của điểm mốc (đo ở bước 7) | Độ lệch chuẩn theo số đo thật |
| Xóa ngẫu nhiên vài bước | Frame mất tay | Xóa rồi vá như bước 13 |

**Tăng cường chỉ áp dụng cho tập train**, tạo mới mỗi epoch.

### Việc cụ thể

**18.1. Mô hình:**

```python
import torch.nn as nn

class GestureGRU(nn.Module):
    def __init__(self, in_dim=42, hidden=64, n_classes=5, layers=1, dropout=0.3):
        super().__init__()
        self.rnn = nn.GRU(in_dim, hidden, num_layers=layers, batch_first=True)
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden, n_classes)

    def forward(self, x):                 # x: (batch, T, 42)
        out, _ = self.rnn(x)
        return self.fc(self.drop(out[:, -1]))   # trạng thái ở bước cuối
```

Viết cả phiên bản `nn.LSTM` — thay một dòng — để so sánh.

**18.2.** Hàm mất mát `CrossEntropyLoss(weight=...)` với trọng số lớp tính từ
tập train. Adam, learning rate 1e-3, batch 64, early stopping theo macro-F1 kiểm
định, kiên nhẫn 10 epoch.

**18.3.** Viết các hàm tăng cường ở bảng trên. **Viết kiểm thử** cho phép lật:
một cửa sổ vuốt trái sau khi lật phải có `dx` đổi dấu và nhãn thành vuốt phải.

**18.4.** Vẽ đường loss và macro-F1 của train và kiểm định theo epoch. Nhận diện
thời điểm quá khớp.

**18.5.** Tùy chọn: đầu vào 42 kênh tọa độ + thêm vài kênh đặc trưng theo từng
bước (độ xòe, vận tốc cổ tay). Đây là cách ghép tri thức thủ công vào học sâu.

### Kiểm chứng

- Phép thử quá khớp một batch (bước 17) vẫn qua với mô hình thật.
- Loss kiểm định có điểm cực tiểu rõ; mô hình lưu lại là mô hình ở điểm đó.
- Kiểm thử phép lật qua.

### Sản phẩm

Mô hình GRU/LSTM đã lưu; đồ thị huấn luyện; `notes/18-lstm.md`.

### Cạm bẫy

| Cạm bẫy | Hậu quả | Xử lý |
|---|---|---|
| Lật ngang mà không đổi nhãn vuốt | Mô hình học rằng vuốt trái = vuốt phải | Kiểm thử ở 18.3 |
| Mô hình quá lớn | Train 99%, kiểm định 70% | Bắt đầu 1 lớp × 64 |
| Tăng cường cả tập test | Kết quả không còn đo điều kiện thật | Chỉ tăng cường train |
| Nếu GRU không thắng RF | **Không phải thất bại** | Đó là một kết luận đáng viết (tài liệu `04`) |

---

## Bước 19. Các thí nghiệm khảo sát

**Mục tiêu.** Bốn đến năm bảng kết quả trả lời các câu hỏi thiết kế cốt lõi —
nội dung chính của chương 5.

### Lý thuyết cần nắm

**Thí nghiệm loại bỏ (ablation).** Thay đổi **đúng một** yếu tố, giữ nguyên mọi
thứ khác (cùng dữ liệu, cùng chia tập, cùng seed), đo sự thay đổi. Mỗi bảng trả
lời một câu hỏi "yếu tố X đóng góp bao nhiêu?".

**Độ bất định của kết quả.** Với dữ liệu nhỏ, kết quả dao động theo seed. Chạy
mỗi cấu hình học sâu 3 lần với 3 seed, báo trung bình ± độ lệch chuẩn. Hai cấu
hình chênh nhau ít hơn độ lệch chuẩn thì **không** kết luận được cái nào hơn.

### Việc cụ thể

| # | Câu hỏi | Cấu hình so sánh | Đo trên |
|---|---|---|---|
| E1 | Mô hình nào tốt nhất? | Luật / RF / GRU (/ LSTM) | Test IPN + dữ liệu tự quay |
| E2 | Chuẩn hóa có quan trọng không? | Không chuẩn hóa / gốc cổ tay từng frame / gốc cổ tay frame đầu | Test IPN, riêng hai cặp lớp ngược chiều |
| E3 | Cửa sổ dài bao nhiêu? | 0,67 / 1,0 / 1,33 / 2,0 giây | Macro-F1 và độ trễ nhận dạng |
| E4 | Dữ liệu công khai giúp bao nhiêu? | Chỉ IPN / chỉ tự quay (loại từng người) / IPN rồi tinh chỉnh bằng tự quay | Dữ liệu tự quay, chia theo người |
| E5 | Mẫu âm khó có giúp không? | Lớp nền chỉ D0X / thêm các lớp nền khác / thêm cả G07 | Tỉ lệ bắn nhầm ở mức cửa sổ |

**Về E3:** cửa sổ dài hơn thấy trọn cử chỉ (IPN trung bình hơn 2 giây) nhưng
phản hồi chậm hơn và dễ trộn hai cử chỉ. Đây là đánh đổi độ chính xác – độ trễ,
vẽ thành một đồ thị hai trục.

**Về E4 — thí nghiệm quan trọng nhất cho câu hỏi "vì sao dùng dataset có sẵn".**
Với "chỉ tự quay", dùng leave-one-person-out: huấn luyện trên 3–5 người, kiểm
thử trên người còn lại, lặp lại cho mọi người.

**Tùy chọn E6 — Jester:** nếu còn thời gian và dữ liệu IPN tỏ ra không đủ cho
GRU, thêm các lớp *Swiping Left/Right*, *Zooming In/Out With Full Hand*, *No
gesture*, *Doing other things* từ Jester (sau khi trích điểm mốc và lọc clip
thiếu tay, lấy mẫu lại từ 12 FPS lên 15 Hz). Chỉ thêm vào **train**.

**Đặt kết quả vào bối cảnh:** nghiên cứu năm 2025 dùng điểm mốc MediaPipe trên
IPN Hand đạt khoảng 80–85% trên bài toán 14 lớp đầy đủ. Bài toán của bạn khác
(5 lớp, có vùng xám), nên không so sánh trực tiếp — nhưng con số này cho biết
"khung xương bàn tay + mô hình chuỗi nhẹ" nằm ở mức nào.

### Kiểm chứng

Mỗi bảng có một câu kết luận một dòng, và câu đó đúng với độ bất định.

### Sản phẩm

4–5 bảng và 2–3 đồ thị cho chương 5.

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Đổi nhiều yếu tố cùng lúc | Mỗi thí nghiệm đổi một yếu tố |
| Chọn cấu hình tốt nhất dựa trên tập test | Chọn trên kiểm định, test chỉ để báo cáo |
| Chạy một seed rồi kết luận | 3 seed, báo trung bình ± độ lệch chuẩn |

---

# GIAI ĐOẠN F — HỆ THỐNG THỜI GIAN THỰC (Tuần 9)

---

## Bước 20. Logic kích hoạt

**Mục tiêu.** Một bộ máy trạng thái biến chuỗi dự đoán liên tục thành các lệnh
rời rạc: mỗi cử chỉ sinh **đúng một** lệnh, nhịp quay tay về không sinh lệnh
ngược, và người dùng lặp lại được cùng một lệnh.

### Lý thuyết cần nắm

#### 20.a. Từ phân loại sang kích hoạt

Bộ phân loại chạy mỗi 2 bước (khoảng 7 lần mỗi giây). Một cử chỉ kéo dài 1–2
giây sẽ sinh ra 7–14 dự đoán liên tiếp cùng lớp. Nếu mỗi dự đoán là một lệnh,
slide nhảy chục trang. Cần một tầng quyết định nằm giữa bộ phân loại và bàn
phím. Trong tài liệu nhận dạng cử chỉ liên tục, ý tưởng này gọi là **kích hoạt
một lần** (single-time activation): hệ thống của Köpüklü và cộng sự (2019) — mà
chính các tác giả IPN Hand dùng làm đường cơ sở — tách một bộ phát hiện "có cử
chỉ hay không" và một bộ phân loại, rồi đảm bảo mỗi cử chỉ chỉ kích hoạt một lần.

#### 20.b. Hai vấn đề cố hữu của cặp cử chỉ ngược nhau

1. **Nhịp quay về.** Vuốt trái xong, tay tự nhiên quay về giữa — chuyển động
   này trông y như vuốt phải → slide tiến rồi lùi ngay.
2. **Lặp lại lệnh.** Muốn phóng to hai lần: xòe (phóng to), rồi phải **chụm lại**
   để xòe lần hai — nhưng chụm chính là lệnh thu nhỏ.

Cả hai có chung cấu trúc: **ngay sau lệnh C, lệnh ngược của C gần như luôn là
động tác chuẩn bị hoặc quay về, không phải ý định thật.** Giải pháp: **khóa lệnh
ngược** trong một khoảng thời gian ngắn sau mỗi lệnh. Người dùng muốn ra lệnh
ngược ngay thì hạ tay ra khỏi khung hình — thao tác đó xóa khóa.

#### 20.c. Bốn cơ chế, mỗi cơ chế chặn một loại lỗi

| Cơ chế | Tham số | Chặn lỗi gì |
|---|---|---|
| Thời gian vũ trang | `arm_time` ≈ 0,2 s | Chuyển động khi tay vừa đưa vào khung bị hiểu nhầm là cử chỉ |
| Ngưỡng + liên tiếp | `thr` ≈ 0,8, `k` = 3 | Dự đoán lẻ tẻ, không chắc chắn |
| Chờ nhả | — | Một cử chỉ kéo dài bắn nhiều lệnh |
| Khóa lệnh ngược | `lock_time` ≈ 1,5 s | Nhịp quay về, chụm lại để xòe tiếp |

Lưu ý: "có tay" phải được **chống dội** — mất tay 1–2 frame do nhòe không được
tính là tay rời khung, nếu không khóa sẽ bị xóa đúng lúc nhịp quay về đang diễn
ra. Coi là tay rời khung khi mất liên tục ≥ 0,3 giây.

#### 20.d. Làm mượt xác suất

Thay vì dùng dự đoán thô, có thể lấy trung bình xác suất của 3 lần dự đoán gần
nhất trước khi so ngưỡng. Làm mượt giảm dao động nhưng thêm độ trễ — một đánh
đổi nữa để khảo sát.

> **Tự kiểm tra.** Nếu bỏ cơ chế "chờ nhả" nhưng giữ khóa lệnh ngược, một cú xòe
> dài 2 giây sẽ gây ra điều gì?

### Việc cụ thể

**20.1. Viết `src/trigger.py`:**

```python
OPPOSITE = {"swipe_left": "swipe_right", "swipe_right": "swipe_left",
            "zoom_in": "zoom_out", "zoom_out": "zoom_in"}

class GestureTrigger:
    def __init__(self, thr=0.8, k=3, arm_time=0.2, lock_time=1.5):
        self.thr, self.k, self.arm_time, self.lock_time = thr, k, arm_time, lock_time
        self.reset()

    def reset(self):
        self.hand_since = None           # lúc tay xuất hiện
        self.holding = None              # lệnh vừa bắn, đang chờ "nhả"
        self.last_cmd, self.last_fire = None, -1e9
        self.streak, self.prev = 0, None

    def update(self, now, hand_present, label, prob):
        """hand_present phải đã được chống dội. Trả về tên lệnh hoặc None."""
        if not hand_present:                          # tay rời khung → xóa mọi khóa
            self.reset()
            return None
        if self.hand_since is None:
            self.hand_since = now
        if now - self.hand_since < self.arm_time:     # tay vừa vào khung
            return None
        confident = label != "none" and prob >= self.thr
        if self.holding is not None:                  # cử chỉ vừa bắn còn đang diễn ra?
            if confident and label == self.holding:
                return None
            self.holding = None                       # đã nhả
        if not confident:
            self.streak, self.prev = 0, None
            return None
        self.streak = self.streak + 1 if label == self.prev else 1
        self.prev = label
        if self.streak < self.k:
            return None
        if self.last_cmd == OPPOSITE[label] and now - self.last_fire < self.lock_time:
            return None                               # nhịp quay về / chụm lại để xòe tiếp
        self.holding, self.last_cmd, self.last_fire = label, label, now
        self.streak = 0
        return label
```

**20.2. Kiểm thử đơn vị** bằng chuỗi dự đoán giả: (a) 10 dự đoán `zoom_in` liên
tiếp → đúng 1 lệnh; (b) `swipe_left` × 5 rồi `swipe_right` × 5 trong 1 giây →
chỉ 1 lệnh; (c) như (b) nhưng cách nhau 2 giây → 2 lệnh; (d) như (b) nhưng tay
rời khung ở giữa → 2 lệnh.

**20.3. Chọn tham số trên video kiểm định IPN** (không phải video test): chạy
bộ phân loại + trigger trên cả video, dùng hàm đánh giá mức sự kiện của bước 22,
quét `thr` và `lock_time`.

### Kiểm chứng

Bốn kiểm thử ở 20.2 qua. Trong demo: xòe – hạ tay – xòe lại phóng to hai lần;
vuốt trái rồi tay tự nhiên quay về chỉ tiến một slide.

### Sản phẩm

`src/trigger.py` có kiểm thử; sơ đồ bộ máy trạng thái cho mục 4.5 báo cáo.

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Chọn tham số bằng cách chơi thử demo đến khi "thấy ổn" | Chọn bằng số liệu trên video kiểm định |
| Không chống dội tín hiệu có tay | Khóa bị xóa giữa chừng bởi một frame mất tay |
| Khóa quá dài | Người dùng thấy hệ thống "lì"; kiểm tra ở thử nghiệm người dùng |

---

## Bước 21. Tích hợp, đo FPS và độ trễ

**Mục tiêu.** Chương trình `src/app.py` hoàn chỉnh, và bảng số liệu thời gian
chứng minh nó chạy thời gian thực trên ThinkPad.

### Lý thuyết cần nắm

**Ba đại lượng thời gian khác nhau:**

| Đại lượng | Định nghĩa | Cách đo |
|---|---|---|
| FPS xử lý | Số frame xử lý xong mỗi giây | Trung bình trượt như bước 3 |
| Độ trễ xử lý | Thời gian từ lúc có frame tới lúc có dự đoán cho frame đó | Bấm giờ từng khâu |
| **Độ trễ nhận dạng** | Từ lúc cử chỉ **kết thúc** tới lúc phím được gửi | Trên dữ liệu có nhãn thời gian (bước 22) |

Độ trễ nhận dạng thường bị chi phối bởi **cửa sổ và logic kích hoạt** (phải chờ
đủ `k` dự đoán liên tiếp), không phải bởi tốc độ tính toán. Hiểu điều này giúp
bạn tối ưu đúng chỗ.

Có thể hệ thống bắn lệnh **trước** khi cử chỉ kết thúc (độ trễ âm) — với cửa sổ
1 giây và cử chỉ 2 giây, điều này là bình thường và tốt cho trải nghiệm.

### Việc cụ thể

**21.1. Ghép toàn bộ:** camera → landmarker → bộ đệm có mốc thời gian → lấy mẫu
lại 15 Hz → vá lỗ → mỗi 2 bước: chuẩn hóa → mô hình → trigger → `send()`.

**21.2. Giao diện phản hồi:** một cửa sổ nhỏ hiển thị ảnh camera đã **lật như
gương** (chỉ để hiển thị), điểm mốc, trạng thái trigger, lệnh vừa bắn. Phản hồi
cho người dùng biết hệ thống đang "thấy" gì — rất quan trọng cho thử nghiệm
người dùng. Nhớ vấn đề tiêu điểm (bước 4).

**21.3. Tham số dòng lệnh:** chọn mô hình (`--model rule|rf|gru`), bật/tắt gửi
phím (`--dry-run` chỉ in lệnh), ghi log mọi dự đoán và lệnh ra file.

**21.4. Đo:** bảng phân rã thời gian mỗi khâu (đọc frame, landmarker, tiền xử lý,
mô hình, trigger), FPS trong phòng sáng và tối, mức dùng CPU.

### Kiểm chứng

FPS xử lý ≥ 20 trong phòng sáng. Chế độ `--dry-run` chạy 10 phút không lỗi, không
rò bộ nhớ.

### Sản phẩm

`src/app.py`; bảng thời gian — mục 5.x "Hiệu năng thời gian thực".

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Tiền xử lý trong `app.py` viết lại khác `src/preprocess.py` | Import đúng hàm đã dùng khi huấn luyện (nguyên tắc 2) |
| Lật ảnh trước khi đưa vào landmarker | Chỉ lật bản hiển thị |
| Chạy mô hình mỗi frame | Mỗi 2 bước 15 Hz là đủ, giảm tải CPU |

---

## Bước 22. Đánh giá mức sự kiện và thử nghiệm người dùng

**Mục tiêu.** Những con số trả lời câu hỏi thực tế: "trong một phiên dùng thật,
hệ thống bắt đúng bao nhiêu lệnh, bắn nhầm bao nhiêu lần mỗi phút, phản hồi
nhanh cỡ nào, và người dùng thấy thế nào?"

### Lý thuyết cần nắm

#### 22.a. Vì sao đánh giá mức cửa sổ chưa đủ

Macro-F1 mức cửa sổ đo bộ phân loại. Người dùng không trải nghiệm bộ phân loại —
họ trải nghiệm **lệnh**. Một cử chỉ gồm 10 cửa sổ, sai 3 cửa sổ vẫn có thể ra
đúng một lệnh nhờ trigger; ngược lại, một cửa sổ `none` bị nhầm có thể bị trigger
lọc mất hoặc không. Chỉ đánh giá trên chuỗi lệnh cuối cùng mới đo đúng trải
nghiệm.

#### 22.b. So khớp sự kiện

Cho danh sách cử chỉ thật `(bắt đầu, kết thúc, lớp)` và danh sách lệnh bắn
`(thời điểm, lệnh)`. Một lệnh **khớp** một cử chỉ nếu thời điểm bắn nằm trong
`[bắt đầu, kết thúc + dung sai]`. Mỗi cử chỉ khớp tối đa một lệnh. Từ đó:

| Kết quả | Định nghĩa |
|---|---|
| Đúng | Khớp và cùng lớp |
| Sai lệnh | Khớp nhưng khác lớp (tách riêng số **sai chiều**) |
| Bỏ sót | Cử chỉ không có lệnh nào khớp |
| Bắn nhầm | Lệnh không khớp cử chỉ nào |

Chỉ số: **tỉ lệ phát hiện** = đúng / số cử chỉ; **số lần bắn nhầm mỗi phút**;
**tỉ lệ sai chiều**; **độ trễ** = thời điểm bắn − thời điểm kết thúc cử chỉ
(trung vị và phân vị 90).

#### 22.c. Độ chính xác Levenshtein

Chỉ số chính của IPN Hand cho nhận dạng liên tục: coi chuỗi lệnh thật và chuỗi
lệnh dự đoán như hai chuỗi ký tự, đếm số phép chèn, xóa, thay tối thiểu để biến
chuỗi này thành chuỗi kia (khoảng cách Levenshtein), rồi quy ra phần trăm theo
độ dài chuỗi thật. Báo chỉ số này trên các video test IPN (chỉ xét 4 lớp đích)
để có một con số cùng tinh thần với bài báo gốc.

#### 22.d. Đường đánh đổi

Quét ngưỡng `thr` từ 0,5 đến 0,95: tỉ lệ phát hiện giảm dần, số bắn nhầm mỗi
phút cũng giảm dần. Vẽ **tỉ lệ phát hiện theo số bắn nhầm mỗi phút** cho RF và
GRU trên cùng một hình — hình đáng giá nhất của báo cáo, vì nó cho thấy toàn bộ
dải điểm vận hành chứ không chỉ một điểm được chọn.

#### 22.e. Thử nghiệm người dùng

Đo hệ thống bằng người thật làm việc thật. Thiết kế tối thiểu nhưng nghiêm túc:
người tham gia **chưa từng dùng** hệ thống (không phải những người đã quay dữ
liệu), hướng dẫn chuẩn hóa như nhau, nhiệm vụ cụ thể, đo khách quan (thời gian,
lỗi) kèm đánh giá chủ quan (thang Likert 5 mức, hoặc bảng SUS 10 câu nếu muốn
chuẩn hơn).

### Việc cụ thể

**22.1. Viết hàm so khớp** trong `src/evaluate.py`:

```python
def match_events(gt, fires, tol=0.5):
    """gt: [(start_s, end_s, label)], fires: [(t_s, label)], đã sắp theo thời gian."""
    used, res = set(), {"correct": 0, "wrong": 0, "wrong_dir": 0, "latency": []}
    for s, e, lab in gt:
        cand = [i for i, (t, _) in enumerate(fires) if i not in used and s <= t <= e + tol]
        if not cand:
            continue
        i = cand[0]; used.add(i)
        if fires[i][1] == lab:
            res["correct"] += 1; res["latency"].append(fires[i][0] - e)
        else:
            res["wrong"] += 1
            res["wrong_dir"] += int(fires[i][1] == OPPOSITE.get(lab))
    res["missed"] = len(gt) - res["correct"] - res["wrong"]
    res["false_trig"] = len(fires) - len(used)
    return res
```

**22.2. Chạy offline** toàn bộ hệ thống (tiền xử lý + mô hình + trigger) trên:
các video test IPN, và các phiên làm việc tự nhiên tự quay. Báo các chỉ số ở
22.b và 22.c cho luật, RF, GRU.

**22.3. Vẽ đường đánh đổi** ở 22.d.

**22.4. Thử nghiệm người dùng:** 5 người mới. Hướng dẫn 2 phút. Nhiệm vụ: một
bài trình chiếu 10 slide có ghi chú kiểu "tới slide 5 → phóng to → thu nhỏ →
lùi về slide 3". Đo: thời gian hoàn thành, số lệnh sai, số lần bắn nhầm; so với
làm cùng nhiệm vụ bằng bàn phím. Cuối buổi: 3–5 câu hỏi Likert (dễ học, đáng
tin, mệt tay, có muốn dùng thật không) và một câu hỏi mở.

### Kiểm chứng

Các con số mức sự kiện nhất quán với mức cửa sổ: mô hình có tỉ lệ bắn nhầm mức
cửa sổ thấp hơn thì số bắn nhầm mỗi phút cũng thấp hơn. Nếu không nhất quán, xem
lại trigger.

### Sản phẩm

Bảng mức sự kiện, đường đánh đổi, kết quả thử nghiệm người dùng — phần "thực
tiễn" mà giảng viên yêu cầu, và là mục 5.5–5.6 của báo cáo.

### Cạm bẫy

| Cạm bẫy | Xử lý |
|---|---|
| Chỉ báo mức cửa sổ | Mức sự kiện mới là trải nghiệm thật |
| Thử nghiệm người dùng với người đã quay dữ liệu | Người mới hoàn toàn |
| Tự hướng dẫn thêm cho người thấy khó | Kịch bản hướng dẫn giống hệt nhau cho mọi người |
| Giấu kết quả xấu | Bắn nhầm mỗi phút cao ở phiên tự nhiên là **phát hiện**, viết vào thảo luận |

---

# GIAI ĐOẠN G — HOÀN THIỆN (Tuần 10)

---

## Bước 23. Báo cáo, repo và bảo vệ

**Mục tiêu.** Báo cáo hoàn chỉnh, repo chạy lại được, demo trực tiếp ổn định.

### Việc cụ thể

**23.1. Ráp báo cáo** từ `notes/` theo cấu trúc Phụ lục C.

**23.2. Dọn repo:** `README.md` với các lệnh chạy theo thứ tự (`scripts/01_…`,
`02_…`), `requirements.txt`, seed cố định, đường dẫn tương đối, không có dữ liệu
trong git. Thử clone ra thư mục mới và chạy lại từ đầu.

**23.3. Chuẩn bị demo:**

- Tập ở đúng phòng bảo vệ, kiểm tra ánh sáng (bước 5, 7).
- Video demo quay sẵn làm phương án dự phòng.
- Bàn phím hoặc bút trình chiếu bên cạnh.
- Cân nhắc **trình bày bài bảo vệ bằng chính hệ thống** — ấn tượng nhất, nhưng chỉ
  khi thử nghiệm người dùng cho thấy nó đủ ổn định.

**23.4. Luyện trả lời câu hỏi** ở Phụ lục D.

### Sản phẩm

Báo cáo, slide, repo, video demo.

---

# PHỤ LỤC

## Phụ lục A. 21 điểm mốc bàn tay

| Chỉ số | Điểm | Chỉ số | Điểm |
|---|---|---|---|
| 0 | Cổ tay | 11 | Ngón giữa — khớp xa (DIP) |
| 1 | Ngón cái — gốc (CMC) | 12 | **Đầu ngón giữa** |
| 2 | Ngón cái — MCP | 13 | Ngón áp út — gốc (MCP) |
| 3 | Ngón cái — IP | 14 | Ngón áp út — PIP |
| 4 | **Đầu ngón cái** | 15 | Ngón áp út — DIP |
| 5 | Ngón trỏ — gốc (MCP) | 16 | **Đầu ngón áp út** |
| 6 | Ngón trỏ — khớp giữa (PIP) | 17 | Ngón út — gốc (MCP) |
| 7 | Ngón trỏ — khớp xa (DIP) | 18 | Ngón út — PIP |
| 8 | **Đầu ngón trỏ** | 19 | Ngón út — DIP |
| 9 | **Ngón giữa — gốc (MCP)** — dùng cho đơn vị chuẩn hóa | 20 | **Đầu ngón út** |
| 10 | Ngón giữa — PIP | | |

Các điểm hay dùng: cổ tay `0`; gốc ngón giữa `9` (cùng `0` tạo đơn vị cỡ lòng
bàn tay); năm đầu ngón `4, 8, 12, 16, 20` (tính độ xòe).

## Phụ lục B. Lịch theo tuần và mốc kiểm tra

| Tuần | Bước | Cuối tuần phải có |
|---|---|---|
| 1 | 1–4 | Đặc tả cử chỉ; điểm mốc trên webcam; **bàn tay điều khiển được slide** |
| 2 | 5, bắt đầu 6 | Ghi chú tầng 1; thí nghiệm nhòe và quy ước hướng |
| 3 | 6–8 | Ghi chú tầng 2; bảng thí nghiệm quan sát; IPN đã tải, **bảng ánh xạ lớp đã chốt** |
| 4 | 9–11 | Hàm chuẩn hóa có hình kiểm chứng; đặc trưng; **demo luật** |
| 5 | 12–14 | Điểm mốc IPN; quy ước hướng đã kiểm chứng; cửa sổ + boxplot; dữ liệu tự quay |
| 6 | 15–16 | **RF có đánh giá đầy đủ trên hai tập** — mốc an toàn |
| 7 | 17, bắt đầu 18 | Đường ống PyTorch qua phép thử quá khớp một batch |
| 8 | 18–19 | GRU/LSTM; các bảng E1–E5 |
| 9 | 20–22 | Trigger có kiểm thử; `app.py`; kết quả mức sự kiện; thử nghiệm người dùng |
| 10 | 23 | Báo cáo, repo, slide, demo |

## Phụ lục C. Cấu trúc báo cáo đề xuất

| Chương | Nội dung | Lấy từ bước |
|---|---|---|
| 1. Mở đầu | Bài toán điều khiển trình chiếu không chạm, ứng dụng, phạm vi, danh sách không làm | 1 |
| 2. Cơ sở lý thuyết | 2.1 Ảnh số và video · 2.2 Ước lượng tư thế bàn tay · 2.3 Biểu diễn khung xương bàn tay · 2.4 Mô hình chuỗi thời gian · 2.5 Nhận dạng cử chỉ liên tục và kích hoạt · 2.6 Đánh giá | 5, 6, 9, 10, 15, 18, 20, 22 |
| 3. Dữ liệu | IPN Hand, ánh xạ lớp, trích điểm mốc, tỉ lệ phát hiện, dữ liệu tự quay, chia tập | 8, 12, 13, 14 |
| 4. Hệ thống | Kiến trúc, chuẩn hóa, đặc trưng, ba mô hình, logic kích hoạt, giao diện | 9–11, 15, 18, 20, 21 |
| 5. Thí nghiệm | Khảo sát công cụ, E1–E5, mức sự kiện, hiệu năng, thử nghiệm người dùng | 7, 16, 19, 21, 22 |
| 6. Thảo luận | Phân tích lỗi, chuyển miền, giới hạn của điểm mốc 2D, vấn đề Midas touch | 16, 19, 22 |
| 7. Kết luận | Tổng kết; hướng phát triển: hai tay, ST-GCN cho bàn tay, cử chỉ tùy biến, điều khiển liên tục mức zoom | — |

## Phụ lục D. Câu hỏi hội đồng hay hỏi

1. Vì sao dùng Hand Landmarker mà không dùng Pose? *(Bước 6.g, 7 — số liệu tỉ lệ
   phát hiện, cần thông tin ngón tay cho xòe/chụm.)*
2. Vì sao không huấn luyện mạng 3D-CNN trực tiếp trên video như bài báo IPN?
   *(Nhẹ hơn hàng trăm lần, chạy CPU thời gian thực, dễ giải thích; điểm mốc đã
   loại bỏ nền và ánh sáng.)*
3. Em đã tránh rò rỉ dữ liệu thế nào? *(Chia theo người; chuẩn hóa chỉ fit trên
   train; chọn tham số trên kiểm định; vùng xám.)*
4. Vì sao chuẩn hóa theo cổ tay frame đầu? *(Bước 9.c, thí nghiệm E2.)*
5. Nếu LSTM không hơn RF thì sao? *(Dữ liệu nhỏ, đặc trưng tốt; đó là kết luận.)*
6. Hệ thống xử lý thế nào khi người dùng chỉ đang gõ phím? *(Lớp nền với mẫu âm
   khó, thời gian vũ trang, số bắn nhầm mỗi phút đo được.)*
7. Vì sao vuốt trái xong tay quay về không làm lùi slide? *(Khóa lệnh ngược, bước 20.)*
8. Kết quả trên dữ liệu tự quay thấp hơn trên IPN — vì sao? *(Chuyển miền, E4.)*
9. Nhãn tay trái/phải của MediaPipe có đáng tin không? *(Quy ước ảnh gương, bước 6.h, 7.)*
10. Giới hạn lớn nhất của hệ thống là gì? *(Trả lời trung thực từ phân tích lỗi.)*

## Phụ lục E. Tài liệu tham khảo chính

| Tài liệu | Dùng cho |
|---|---|
| Zhang F. và cộng sự, *MediaPipe Hands: On-device Real-time Hand Tracking*, arXiv:2006.10214, 2020 | Bước 6 |
| Tài liệu Google AI Edge — *Hand landmarks detection guide* (Hand Landmarker) | Bước 2, 3 |
| Benitez-Garcia G. và cộng sự, *IPN Hand: A Video Dataset and Benchmark for Real-Time Continuous Hand Gesture Recognition*, ICPR 2020 (arXiv:2005.02134); trang dữ liệu `gibranbenitez.github.io/IPN_Hand` | Bước 8, 12, 22 |
| Köpüklü O. và cộng sự, *Real-time Hand Gesture Detection and Classification Using Convolutional Neural Networks*, FG 2019 (arXiv:1901.10323) | Bước 20 |
| Nghiên cứu nhận dạng cử chỉ bằng điểm mốc MediaPipe trên IPN Hand, SciTePress 2025 | Bước 9, 19 |
| Materzynska J. và cộng sự, *The Jester Dataset*, ICCV Workshops 2019 | Bước 19 (tùy chọn) |
| Simon T. và cộng sự, *Hand Keypoint Detection in Single Images using Multiview Bootstrapping*, CVPR 2017 (arXiv:1704.07809) | Bước 6.a |
| Liu W. và cộng sự, *SSD: Single Shot MultiBox Detector*, 2016; Lin T.-Y. và cộng sự, *Focal Loss for Dense Object Detection*, 2017 | Bước 6.d |
| Hochreiter S., Schmidhuber J., *Long Short-Term Memory*, 1997 | Bước 18 |
| Jacob R., *What You Look At Is What You Get: Eye Movement-Based Interaction Techniques*, CHI 1990 | Bước 1 (Midas touch) |
| Tài liệu tầng 1, 4, 5 trong project | Xuyên suốt |
