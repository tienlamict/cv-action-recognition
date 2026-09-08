# Tầng 1 — Ảnh số và video

> **Câu hỏi mở đầu:** Máy tính "nhìn thấy" gì khi bạn đưa cho nó một tấm ảnh?

Câu trả lời ngắn: **một bảng số**. Không có gì khác. Không có khái niệm "người",
"tay", "ghế". Chỉ là một lưới các con số cường độ sáng.

Toàn bộ ngành thị giác máy tính là nỗ lực đi từ bảng số đó tới ý nghĩa. Tầng
này nói về đầu bảng số — điểm xuất phát.

---

## 1. Ảnh xám — trường hợp đơn giản nhất

Hãy bắt đầu với ảnh đen trắng.

Một ảnh xám là một **lưới ô vuông**, mỗi ô chứa một con số cho biết ô đó sáng
bao nhiêu:

- `0` = đen tuyệt đối
- `255` = trắng tuyệt đối
- `128` = xám giữa

Mỗi ô đó gọi là một **pixel** (viết tắt của *picture element*).

Ví dụ, một ảnh 4×5 pixel trông như thế này với máy tính:

```
[[  0,  40,  80, 120, 160],
 [ 40,  80, 120, 160, 200],
 [ 80, 120, 160, 200, 240],
 [120, 160, 200, 240, 255]]
```

Với mắt người, đó là một dải chuyển màu từ tối (góc trên trái) sang sáng (góc
dưới phải).

### Vì sao 0–255

Vì mỗi pixel được lưu bằng **một byte** = 8 bit = 2⁸ = 256 giá trị khác nhau.
Đây là kiểu `uint8` mà bạn đã gặp ở tầng 0.

256 mức xám đủ để mắt người không thấy các bậc nhảy. Ảnh chuyên nghiệp (y tế,
thiên văn) đôi khi dùng 16 bit, nhưng với webcam thì 8 bit là chuẩn.

---

## 2. Ảnh màu — ba lớp chồng lên nhau

### Vì sao ba màu

Mắt người có ba loại tế bào cảm thụ màu, nhạy nhất với vùng đỏ, xanh lá và xanh
lam. Mọi màu bạn nhìn thấy đều là một tổ hợp kích thích của ba loại này.

Nên để tái tạo màu, chỉ cần ba con số. Đây là **mô hình màu cộng RGB**:

- Đỏ + Xanh lá = Vàng
- Đỏ + Xanh lam = Hồng cánh sen
- Cả ba tối đa = Trắng
- Cả ba bằng 0 = Đen

(Lưu ý: đây là màu **cộng**, dùng cho nguồn sáng — màn hình, cảm biến camera.
Khác với màu **trừ** của mực in, nơi trộn nhiều màu ra đen.)

### Cấu trúc dữ liệu

Ảnh màu là **ba ảnh xám chồng lên nhau**: một lớp cho đỏ, một cho xanh lá, một
cho xanh lam. Mỗi lớp gọi là một **kênh** (*channel*).

```python
img.shape    # (720, 1280, 3)
```

Đọc là: 720 hàng, 1280 cột, 3 kênh. Tức là:

- Ảnh cao 720 pixel, rộng 1280 pixel
- Mỗi pixel có 3 con số

Tổng số con số: 720 × 1280 × 3 = **2.764.800**.

Con số này chính là lý do đề cương chọn khung xương thay vì pixel. Ta sẽ quay
lại điểm này ở cuối file.

### Truy cập pixel

```python
img[100, 200]        # pixel ở hàng 100, cột 200 → mảng 3 phần tử
img[100, 200, 0]     # kênh đầu tiên của pixel đó
img[:, :, 0]         # toàn bộ kênh đầu tiên → một ảnh xám
```

---

## 3. Hai cạm bẫy về thứ tự — đọc kỹ phần này

Đây là hai chỗ làm sai kết quả của rất nhiều người mới, và cả hai đều **không
báo lỗi**.

### 3.1. Thứ tự (hàng, cột) chứ không phải (x, y)

Trong toán học, ta quen viết điểm là `(x, y)` — hoành độ trước, tung độ sau.

Trong numpy và OpenCV, ảnh được đánh chỉ số theo **(hàng, cột)** = **(y, x)**.
Ngược lại.

```python
img[y, x]     # ĐÚNG
img[x, y]     # SAI — nhưng vẫn chạy nếu ảnh vuông!
```

Với ảnh 720×1280 thì nhầm sẽ gây `IndexError` — may cho bạn. Với ảnh vuông thì
nó chạy êm và cho kết quả sai.

Cách nhớ: `shape` là `(H, W, 3)` — cao trước rộng sau. Chỉ mục theo đúng thứ tự
đó.

### 3.2. Gốc tọa độ ở góc trên bên trái, và trục y hướng XUỐNG

```
(0,0) ──────────────► x tăng
  │
  │      ● điểm (x=400, y=300)
  │
  ▼
y tăng
```

Khác với hệ tọa độ Descartes ở trường phổ thông (gốc dưới trái, y hướng lên).
Quy ước này đến từ cách màn hình CRT quét ảnh: từ trên xuống, từ trái sang.

**Hệ quả cho đồ án của bạn:** y **lớn** nghĩa là **thấp** trong ảnh.

- Người đứng: hông có y nhỏ hơn (cao hơn trên màn hình)
- Người ngồi: hông có y lớn hơn (thấp hơn)
- Ngồi xuống: y của hông **tăng** dần
- Đứng dậy: y của hông **giảm** dần

Khi bạn viết đặc trưng "độ thay đổi chiều cao hông" ở tuần 6, dấu của nó ngược
với trực giác. Ghi chú rõ trong code, kẻo tự làm mình rối:

```python
# LƯU Ý: y tăng = đi xuống trong ảnh.
# delta > 0 nghĩa là hông ĐI XUỐNG = đang ngồi xuống.
delta_hip_y = hip_y[-1] - hip_y[0]
```

---

## 4. BGR so với RGB — lỗi phổ biến nhất trong đồ án này

### Chuyện gì xảy ra

OpenCV lưu ảnh theo thứ tự kênh **BGR**: xanh lam, xanh lá, đỏ. Gần như mọi
thư viện khác — MediaPipe, matplotlib, PIL, PyTorch — dùng **RGB**.

Đây là di sản lịch sử. OpenCV ra đời cuối thập niên 1990, khi các camera và
định dạng ảnh phổ biến trên Windows dùng thứ tự BGR. Khi cộng đồng chuẩn hóa
sang RGB thì OpenCV đã có quá nhiều mã nguồn phụ thuộc để đổi được.

### Hậu quả nếu quên chuyển

**Nếu chỉ hiển thị:** ảnh trông kỳ quặc — trời xanh thành cam, da người thành
xanh lam. Dễ nhận ra.

**Nếu đưa vào MediaPipe:** đây mới là vấn đề. MediaPipe **không báo lỗi**. Nó
vẫn chạy, vẫn trả về kết quả. Chỉ là:

- Tỉ lệ phát hiện được người giảm mạnh
- Khi phát hiện được thì điểm khớp lệch và giật
- Điểm tin cậy thấp

Bạn sẽ ngồi chỉnh mô hình LSTM cả tuần trong khi dữ liệu vào đã hỏng từ đầu.

### Vì sao MediaPipe không hoạt động với BGR

MediaPipe được huấn luyện trên hàng triệu ảnh RGB. Mạng nơ-ron bên trong học
được rằng "da người có kênh đỏ mạnh". Khi bạn đưa BGR vào, giá trị kênh đỏ nằm
ở vị trí kênh lam. Với mạng, da người bây giờ là màu xanh lam — một thứ nó chưa
từng thấy trong huấn luyện. Nó cố đoán, và đoán sai.

### Cách sửa

Một dòng, ngay sau khi đọc frame:

```python
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
```

Quy tắc thực hành để không bao giờ quên:

> **Ngay khi frame ra khỏi OpenCV và đi vào bất cứ thư viện nào khác, chuyển
> sang RGB. Ngay khi nó quay lại OpenCV để hiển thị hoặc ghi file, dùng bản BGR
> gốc.**

Cách đặt tên biến giúp ích rất nhiều:

```python
ok, frame_bgr = cap.read()
frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
result = landmarker.detect_for_video(mp.Image(..., data=frame_rgb), ts)
cv2.imshow("pose", frame_bgr)     # hiển thị bản BGR
```

Đặt tên có hậu tố `_bgr` / `_rgb` thì mắt bạn tự bắt lỗi khi đọc code.

### Cách kiểm tra nhanh

Chèn tạm dòng này và xem cửa sổ hiện ra:

```python
cv2.imshow("kiem tra", frame_rgb)   # nếu người trông XANH LAM thì frame_rgb
                                     # đúng là RGB (vì imshow tưởng nó là BGR)
```

Nghe ngược đời nhưng đúng: `imshow` luôn giả định đầu vào là BGR. Đưa ảnh RGB
vào nó thì màu bị hoán đổi. Thấy màu sai ở đây tức là bạn đã chuyển đúng.

---

## 5. Các không gian màu khác

RGB không phải cách duy nhất mã hóa màu. Hai cái khác đáng biết:

### Ảnh xám (grayscale)

Gộp ba kênh thành một, theo công thức có trọng số phản ánh độ nhạy của mắt
người:

```
Y = 0.299·R + 0.587·G + 0.114·B
```

Xanh lá có trọng số cao nhất vì mắt người nhạy nhất với vùng này.

```python
gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)   # shape (H, W)
```

Dùng khi nào: các thuật toán chỉ quan tâm hình dạng và cạnh, không quan tâm
màu. Giảm dữ liệu ba lần. **Đồ án này không dùng** — MediaPipe cần ảnh màu.

### HSV — Hue, Saturation, Value

Ba chiều: sắc màu (góc 0–360°), độ bão hòa, độ sáng.

Ưu điểm: tách được "màu gì" khỏi "sáng bao nhiêu". Nếu muốn tìm mọi vật màu đỏ
bất kể trong bóng râm hay nắng, lọc theo H dễ hơn nhiều so với RGB.

**Đồ án này không dùng**, nhưng biết để trả lời nếu hội đồng hỏi "sao không
dùng màu để phân biệt hành động" — câu trả lời là ta chọn cách tiếp cận dựa
trên khung xương, cố tình vứt bỏ mọi thông tin màu.

---

## 6. Video

### Video là chuỗi ảnh

Một video chỉ là nhiều ảnh (**frame**) xếp nối tiếp, phát đủ nhanh để mắt người
thấy chuyển động liên tục.

Ngưỡng đó khoảng 24 hình/giây — nên phim điện ảnh dùng 24 FPS. Webcam thường
30 FPS. Game thủ muốn 60 FPS hoặc hơn để cảm giác mượt và độ trễ thấp.

Với một video 30 FPS:

- Mỗi frame cách nhau **1/30 giây ≈ 33 mili-giây**
- 1 giây = 30 frame
- Một hành động kéo dài 3 giây = 90 frame

**Đây chính là gốc của con số `T = 30` trong đồ án.** Cửa sổ 30 frame ≈ 1 giây
— đủ dài để nhìn thấy một cái vẫy tay hay một động tác ngồi xuống, đủ ngắn để
hệ thống phản hồi nhanh.

### FPS quay và FPS xử lý — hai thứ khác nhau

Nhầm lẫn phổ biến. Phân biệt rõ:

| | Nghĩa |
|---|---|
| **FPS quay** | Camera sinh ra bao nhiêu frame mỗi giây. Do phần cứng quyết định, thường 30 |
| **FPS xử lý** | Chương trình của bạn xử lý xong bao nhiêu frame mỗi giây. Do code quyết định |

Nếu chương trình chỉ xử lý được 10 FPS trong khi camera cho 30 FPS, thì hai
trong ba frame bị bỏ. Hệ quả trực tiếp:

- Chuyển động trông giật
- **Cửa sổ 30 frame của bạn không còn là 1 giây nữa mà là 3 giây** — làm hỏng
  hoàn toàn giả định về thời gian, và mô hình huấn luyện ở 30 FPS sẽ hoạt động
  sai ở 10 FPS

Đây là lý do mục 06 của đề cương yêu cầu **đo FPS thực tế**, và mục 09 khuyên
chỉ chạy mô hình phân loại mỗi 5 frame thay vì mỗi frame.

### Đo FPS đúng cách

Cách ngây thơ (in mỗi frame) cho ra con số nhảy loạn không đọc được. Dùng
trung bình trượt:

```python
import time
from collections import deque

times = deque(maxlen=30)
prev = time.perf_counter()

while True:
    # ... xử lý một frame ...
    now = time.perf_counter()
    times.append(now - prev)
    prev = now
    fps = len(times) / sum(times)     # trung bình 30 frame gần nhất
```

Ba lưu ý khi báo cáo FPS:

1. **Bỏ qua vài giây đầu.** Lần gọi MediaPipe đầu tiên phải nạp mô hình, chậm
   hơn nhiều lần các lần sau. Đừng tính vào trung bình.
2. **Dùng `time.perf_counter()`**, không dùng `time.time()`. Cái đầu chính xác
   hơn nhiều cho việc đo khoảng thời gian ngắn.
3. **Nêu cấu hình máy.** "30 FPS" vô nghĩa nếu không biết chạy trên CPU gì.

### Đo thời gian từng khâu

Khi FPS thấp, phải biết chậm ở đâu. Đo riêng từng phần:

```python
t0 = time.perf_counter()
rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
t1 = time.perf_counter()
result = landmarker.detect_for_video(mp_image, ts)
t2 = time.perf_counter()
label = classifier.predict(window)
t3 = time.perf_counter()

print(f"chuyen mau {(t1-t0)*1000:.1f}ms | "
      f"pose {(t2-t1)*1000:.1f}ms | "
      f"phan loai {(t3-t2)*1000:.1f}ms")
```

Kết quả điển hình: MediaPipe chiếm 80–90% thời gian. Phân loại gần như miễn phí.
**Bảng phân rã thời gian này rất đáng đưa vào chương thí nghiệm** — nó cho thấy
bạn hiểu hệ thống mình xây, chứ không chỉ đo một con số tổng.

### Độ phân giải và đánh đổi

| Độ phân giải | Số pixel | Ghi chú |
|---|---|---|
| 640×480 (VGA) | 307.200 | Đủ cho MediaPipe, nhanh nhất |
| 1280×720 (HD) | 921.600 | Mặc định của nhiều webcam |
| 1920×1080 (Full HD) | 2.073.600 | Chậm, không cần thiết cho đồ án này |

Giảm độ phân giải là cách nhanh nhất để tăng FPS. MediaPipe dù sao cũng thu nhỏ
ảnh về kích thước cố định trước khi xử lý, nên đưa vào ảnh 1080p phần lớn là
lãng phí.

```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
```

**Nhưng cẩn thận:** phải dùng **cùng độ phân giải** khi quay dữ liệu và khi chạy
demo. Nếu quay ở 1280×720 rồi demo ở 640×480, tỉ lệ khung hình đổi thì tọa độ
chuẩn hóa cũng đổi theo (xem tầng 3, mục về tỉ lệ khung hình). Ghi cấu hình
camera vào README và giữ nguyên.

### Nén video và chuyện seek chậm

Video không lưu từng frame riêng lẻ — như thế sẽ quá nặng. Thay vào đó nó lưu:

- **Keyframe** (I-frame): một frame đầy đủ, cách vài chục frame một lần
- **Frame chênh lệch** (P-frame, B-frame): chỉ lưu *khác biệt* so với frame
  trước

Hệ quả thực tế: để lấy frame thứ 1000, trình giải mã phải tìm keyframe gần nhất
rồi giải mã tuần tự tới đó. Nên **nhảy tới một frame bất kỳ thì chậm, đọc tuần
tự thì nhanh**.

Trong đồ án: khi trích khung xương, hãy đọc video **tuần tự từ đầu tới cuối**
bằng vòng `while cap.read()`, đừng dùng `cap.set(CAP_PROP_POS_FRAMES, i)` trong
vòng lặp. Cách thứ hai chậm hơn hàng chục lần và đôi khi cho ra frame sai.

---

## 7. Đọc webcam bằng OpenCV

Khung chương trình tối thiểu, giải thích từng dòng:

```python
import cv2

cap = cv2.VideoCapture(0)     # 0 = webcam mặc định. 1, 2... nếu có nhiều camera
                              # Thay bằng "video.mp4" để đọc từ file

if not cap.isOpened():        # LUÔN kiểm tra. Nếu bỏ qua, lỗi sẽ hiện ở
    raise RuntimeError(       # tận dòng cvtColor với thông báo khó hiểu
        "Khong mo duoc webcam")

while True:
    ok, frame_bgr = cap.read()    # ok=False khi hết video hoặc camera lỗi
    if not ok:
        break

    # ... xử lý ở đây ...

    cv2.imshow("webcam", frame_bgr)

    # waitKey(1) làm HAI việc:
    #   1. Chờ 1ms — và đây là lúc cửa sổ imshow thực sự được vẽ
    #   2. Trả về mã phím bấm; 27 là phím ESC
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()              # trả webcam lại cho hệ thống
cv2.destroyAllWindows()
```

### Ba chỗ hay sai

**Quên `waitKey`.** Không có nó, `imshow` không vẽ gì cả — cửa sổ hiện ra xám
trắng hoặc treo. Đây không phải lỗi của bạn, đó là cách OpenCV được thiết kế:
`waitKey` là lúc vòng lặp sự kiện giao diện được chạy.

**Quên `cap.release()`.** Webcam bị chương trình cũ giữ, lần chạy sau
`VideoCapture(0)` thất bại. Trên Windows đôi khi phải rút cắm lại camera hoặc
khởi động lại máy. Dùng `try/finally` để chắc chắn:

```python
try:
    while True:
        ...
finally:
    cap.release()
    cv2.destroyAllWindows()
```

**Không kiểm tra `ok`.** Khi đọc từ file video, `ok` thành `False` ở cuối file
và `frame` là `None`. Mọi thao tác sau đó ném lỗi khó hiểu
(`!_src.empty()`).

### Vẽ chú thích lên frame

Ở tuần 1 và tuần 9 bạn cần vẽ khung xương và nhãn lên ảnh:

```python
cv2.circle(frame_bgr, (x, y), 4, (0, 255, 0), -1)        # điểm khớp
cv2.line(frame_bgr, (x1, y1), (x2, y2), (255, 0, 0), 2)  # xương nối
cv2.putText(frame_bgr, "vay tay 0.92", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
```

Ba điều cần nhớ:

- Tọa độ truyền vào là **`(x, y)`** — ngược với thứ tự chỉ mục mảng `[y, x]`.
  OpenCV nhất quán trong việc thiếu nhất quán này.
- Màu là **`(B, G, R)`**. `(0, 255, 0)` là xanh lá.
- Tọa độ phải là **số nguyên**. MediaPipe trả về số thực trong `[0, 1]`, phải
  nhân với `W`, `H` rồi ép `int`:

```python
x = int(lm.x * W)
y = int(lm.y * H)
```

- `putText` của OpenCV **không hiển thị được tiếng Việt có dấu**. Dùng nhãn
  không dấu (`"vay tay"`, `"nga"`) hoặc tiếng Anh trong demo.

---

## 8. Nối vào đồ án — vì sao khung xương chứ không phải pixel

Bây giờ ta có đủ số liệu để hiểu quyết định trung tâm của đề tài.

| Cách biểu diễn một frame | Số con số |
|---|---|
| Ảnh màu 1280×720 | 2.764.800 |
| Ảnh màu 640×480 | 921.600 |
| Khung xương 33 khớp × (x, y) | **66** |
| Khung xương 23 khớp × (x, y) sau khi bỏ mặt | **46** |

Tỉ lệ: khoảng **60.000 lần nhẹ hơn** so với ảnh HD.

Với một cửa sổ 30 frame:

- Dạng pixel: 30 × 2.764.800 ≈ 83 triệu con số
- Dạng khung xương: 30 × 46 = **1.380 con số**

1.380 con số là kích thước mà một chiếc laptop không GPU xử lý được thoải mái,
và là kích thước mà vài nghìn mẫu dữ liệu tự quay đủ để huấn luyện. 83 triệu
con số thì không — bạn sẽ cần GPU, cần hàng chục nghìn video, và cần vài tuần
huấn luyện.

### Cái giá phải trả

Khung xương vứt bỏ **toàn bộ ngoại hình**: quần áo, khuôn mặt, vật thể trong
tay, bối cảnh xung quanh.

Hệ quả: hệ thống không bao giờ phân biệt được "uống nước" với "đánh răng" —
cả hai đều là đưa tay lên mặt, quỹ đạo khớp gần như y hệt. Sự khác biệt nằm ở
vật cầm trong tay, mà khung xương không thấy.

Đây là lý do sáu hành động của đồ án được chọn theo tiêu chí **khác nhau về
hình học thân thể**, không phải khác nhau về vật thể:

| Hành động | Đặc trưng hình học phân biệt |
|---|---|
| Đứng yên | Thân thẳng, mọi khớp gần như bất động |
| Đi bộ tại chỗ | Thân thẳng, chân dao động tuần hoàn |
| Vẫy tay | Thân thẳng, cổ tay dao động biên độ lớn |
| Ngồi xuống | Hông đi xuống, gối gập, kết thúc ở tư thế thấp |
| Đứng dậy | Hông đi lên, gối duỗi, kết thúc ở tư thế cao |
| Ngã | Hông đi xuống rất nhanh, thân nghiêng ngang |

Cột bên phải chính là dàn ý cho phần thiết kế đặc trưng ở tầng 3.

**Câu này nên có trong báo cáo:** việc chọn tập hành động không phải tùy tiện,
mà là hệ quả trực tiếp của giới hạn thông tin trong biểu diễn khung xương. Nói
được điều đó cho thấy bạn hiểu phương pháp mình chọn, chứ không chỉ dùng nó.

---

## Tự kiểm tra

1. Một webcam cho ảnh 1280×720. `img.shape` trả về gì? Giải thích từng số.

2. Vì sao `img[300, 500]` và `img[500, 300]` là hai pixel khác nhau, và cái nào
   ứng với điểm "cách trái 500, cách trên 300"?

3. Bạn quên `cv2.cvtColor` trước khi đưa frame vào MediaPipe. Chương trình có
   ném lỗi không? Triệu chứng bạn sẽ quan sát được là gì?

4. Camera quay 30 FPS nhưng chương trình chỉ xử lý được 10 FPS. Cửa sổ 30 frame
   của bạn thực tế bao phủ bao nhiêu giây? Vì sao điều này làm hỏng mô hình đã
   huấn luyện ở 30 FPS?

5. Một người đang ngồi xuống. Tọa độ y của hông tăng hay giảm? Vì sao?

6. Tính số con số trong một cửa sổ 30 frame theo hai cách biểu diễn: ảnh
   640×480 và khung xương 23 khớp 2 chiều. Tỉ lệ chênh lệch bao nhiêu?

7. Vì sao khi trích khung xương từ video nên đọc tuần tự thay vì nhảy tới từng
   frame bằng `cap.set()`?

<details>
<summary>Đáp án gợi ý</summary>

1. `(720, 1280, 3)` — 720 hàng (chiều cao), 1280 cột (chiều rộng), 3 kênh màu.
   Chiều cao đứng trước vì numpy đánh chỉ số theo hàng trước.

2. numpy đánh chỉ số `[hàng, cột]` = `[y, x]`. Điểm "cách trái 500, cách trên
   300" là `x=500, y=300`, nên viết là `img[300, 500]`.

3. Không ném lỗi. MediaPipe nhận ảnh BGR như thể nó là RGB, mọi màu bị hoán
   đổi. Triệu chứng: tỉ lệ phát hiện người giảm mạnh, khung xương giật hoặc
   không xuất hiện, điểm tin cậy thấp. Lỗi hoàn toàn im lặng — đây là điều làm
   nó nguy hiểm.

4. 30 frame ở 10 FPS = 3 giây, thay vì 1 giây. Mô hình đã học rằng "một cái vẫy
   tay chiếm khoảng 15 frame"; giờ cùng cái vẫy tay đó chỉ chiếm 5 frame. Phân
   bố dữ liệu vào khác hoàn toàn dữ liệu huấn luyện, nên dự đoán sai.

5. **Tăng.** Trục y trong ảnh hướng xuống, nên đi xuống trong thực tế = y tăng.

6. Ảnh: 30 × 640 × 480 × 3 = 27.648.000. Khung xương: 30 × 23 × 2 = 1.380.
   Tỉ lệ ≈ 20.000 lần.

7. Video được nén theo kiểu chỉ lưu chênh lệch giữa các frame liên tiếp. Nhảy
   tới frame bất kỳ buộc trình giải mã quay về keyframe gần nhất rồi giải mã
   tuần tự tới đó — chậm hơn nhiều lần và đôi khi trả về frame lệch.

</details>

---

## Đưa gì vào báo cáo

Mục **2.1 Biểu diễn ảnh số và video** trong chương Cơ sở lý thuyết, khoảng
1,5–2 trang:

- Ảnh số là mảng pixel; ảnh xám và ảnh màu ba kênh; khoảng giá trị 0–255
- Hệ tọa độ ảnh, gốc trên trái, trục y hướng xuống — kèm một hình minh họa
- Video là chuỗi frame; FPS; quan hệ giữa FPS và độ dài cửa sổ thời gian
- **Một đoạn ngắn về BGR/RGB.** Nghe có vẻ chi tiết kỹ thuật vụn vặt, nhưng nó
  cho thấy bạn thực sự đã cài đặt hệ thống chứ không chỉ đọc lý thuyết

Ở **chương 3 (Hệ thống)** hoặc **chương 5 (Thí nghiệm)**:

- Bảng phân rã thời gian xử lý từng khâu ở mục 6 — chuyển màu, ước lượng tư
  thế, phân loại
- Cấu hình camera dùng khi quay dữ liệu và khi demo (độ phân giải, FPS)

**Một hình đáng vẽ:** sơ đồ đơn giản gồm ba khối cạnh nhau — một ô lưới pixel
phóng to với các con số bên trong, mũi tên sang một ảnh người, mũi tên sang một
khung xương 33 điểm. Kèm số lượng con số ở mỗi bước (2.764.800 → 66). Hình này
truyền đạt quyết định thiết kế trung tâm của đồ án chỉ trong một cái nhìn.
