# Tầng 0 — Công cụ và numpy

> **Câu hỏi mở đầu:** Tại sao không cài thẳng thư viện vào Python có sẵn trong
> máy? Và tại sao mọi tài liệu về thị giác máy tính đều giả định bạn biết numpy?

Tầng này không có gì "thị giác máy tính" cả. Nhưng nếu bỏ qua, bạn sẽ mất
nhiều buổi tối cho những lỗi không liên quan gì tới đề tài. Đọc một lần, nắm
chắc, rồi quên nó đi.

---

## 1. Môi trường ảo — vì sao cần

### Vấn đề

Giả sử bạn có hai dự án trên cùng một máy:

- Dự án A cần `numpy` phiên bản 1.24
- Dự án B cần `numpy` phiên bản 2.0

Python mặc định chỉ cho phép **một** phiên bản của mỗi gói tồn tại. Cài cái
này là đè cái kia. Dự án A vừa chạy được hôm qua, hôm nay cài gói cho dự án B
xong thì dự án A chết — mà bạn không đụng gì vào code của A cả.

Tình huống này có tên riêng trong giới lập trình: *dependency hell*. Nó phổ
biến đến mức mọi ngôn ngữ đều phải phát minh ra cách chống.

### Giải pháp

**Môi trường ảo** là một thư mục chứa một bản Python riêng cùng bộ thư viện
riêng. Mỗi dự án một môi trường. Cài gói vào môi trường nào chỉ ảnh hưởng môi
trường đó.

Hãy hình dung: thay vì một tủ thuốc chung cho cả nhà, mỗi người một hộp thuốc
riêng. Bạn uống thuốc gì cũng không ảnh hưởng người khác.

### conda so với venv và pip

Ba cái tên này hay bị lẫn. Phân biệt:

| Công cụ | Làm gì |
|---|---|
| `pip` | **Trình cài gói.** Tải thư viện Python từ internet về và cài vào môi trường đang bật |
| `venv` | **Trình tạo môi trường** có sẵn trong Python. Nhẹ, chỉ quản lý gói Python |
| `conda` | **Vừa tạo môi trường vừa cài gói.** Nặng hơn, nhưng cài được cả thứ không phải Python (thư viện C, CUDA...) |

Đồ án này dùng `conda` để tạo môi trường và `pip` để cài gói bên trong. Đây là
cách phổ biến và hoàn toàn hợp lệ: conda lo phần Python và các thư viện hệ
thống, pip lo các gói thuần Python.

### Các lệnh cần thuộc

```bash
conda create -n action -y python=3.10   # tạo môi trường tên "action"
conda activate action                    # bật nó lên
conda deactivate                         # tắt
conda env list                           # xem có những môi trường nào
conda env remove -n action               # xóa (khi muốn làm lại từ đầu)
```

Sau khi `activate`, dòng lệnh của bạn sẽ có tiền tố `(action)`. **Nếu không
thấy tiền tố đó, bạn đang cài gói vào chỗ khác.** Đây là lỗi số một của người
mới: cài xong, chạy `import mediapipe`, báo `ModuleNotFoundError`, và không
hiểu tại sao.

Cách kiểm tra chắc chắn bạn đang ở đúng môi trường:

```bash
python -c "import sys; print(sys.executable)"
```

Đường dẫn in ra phải chứa tên môi trường (`...\envs\action\python.exe`). Nếu
không, bạn đang dùng Python khác.

### Vì sao Python 3.10 chứ không phải bản mới nhất

MediaPipe, PyTorch, OpenCV là các thư viện lớn, được biên dịch sẵn cho từng
phiên bản Python cụ thể. Bản Python mới nhất thường **chưa** có gói dựng sẵn,
nên `pip install` sẽ cố biên dịch từ mã nguồn và thất bại với một trang lỗi C++
mà bạn không có cách nào đọc hiểu.

Nguyên tắc: với dự án dùng thư viện học máy, chọn phiên bản Python **cũ hơn
bản mới nhất khoảng một tới hai đời**. Chậm một nhịp là an toàn.

### Ghi lại môi trường

Trước khi nộp, chạy:

```bash
pip freeze > requirements.txt
```

File này liệt kê chính xác phiên bản mọi gói bạn dùng. Người chấm (hoặc chính
bạn sáu tháng sau) có thể dựng lại y hệt môi trường bằng:

```bash
pip install -r requirements.txt
```

Đây là một tiêu chí ngầm của "đồ án làm nghiêm túc": **người khác chạy lại
được**.

---

## 2. numpy — ngôn ngữ chung của dữ liệu số

Toàn bộ dữ liệu trong đồ án này là mảng numpy:

- Một ảnh là mảng `(H, W, 3)`
- Khung xương một frame là mảng `(33, 2)`
- Một đoạn video đã trích khung xương là mảng `(số_frame, 33, 2)`
- Một cửa sổ đưa vào LSTM là mảng `(30, 46)`

Không hiểu numpy thì mọi dòng code sau này đều là phép thuật.

### 2.1. Mảng là gì

Mảng numpy (`ndarray`) là một khối số **cùng kiểu**, xếp thành lưới nhiều
chiều. Khác với `list` của Python ở hai điểm quan trọng:

1. **Đồng nhất kiểu.** Cả mảng cùng là số thực 32 bit, hoặc cùng là số nguyên
   không dấu 8 bit. Không trộn lẫn.
2. **Liên tục trong bộ nhớ.** Toàn bộ mảng nằm trong một dải ô nhớ liền nhau.

Nhờ hai tính chất đó, numpy có thể xử lý cả mảng bằng mã máy tối ưu thay vì
vòng lặp Python. Chênh lệch tốc độ thường là **50–100 lần**.

```python
import numpy as np

a = np.array([[1, 2, 3],
              [4, 5, 6]])

a.shape    # (2, 3)  — 2 hàng, 3 cột
a.ndim     # 2       — số chiều
a.dtype    # int64   — kiểu dữ liệu
a.size     # 6       — tổng số phần tử
```

### 2.2. shape — thứ bạn phải luôn biết

**90% lỗi khi làm học máy là lỗi shape.** Thói quen cần rèn ngay từ tuần 1:
sau mỗi phép biến đổi, in shape ra kiểm tra.

```python
print("sau khi trích khung xương:", skeletons.shape)  # (450, 33, 2)
print("sau khi bỏ điểm mặt:      ", skeletons.shape)  # (450, 23, 2)
print("sau khi làm phẳng:        ", X.shape)          # (450, 46)
```

Quy ước đọc shape: **chiều ngoài cùng viết trước**. `(450, 33, 2)` nghĩa là
450 frame, mỗi frame 33 khớp, mỗi khớp 2 số. Đọc từ trái sang: "một mảng gồm
450 phần tử, mỗi phần tử là mảng 33×2".

### 2.3. dtype — kiểu dữ liệu, và cái bẫy uint8

Các kiểu bạn sẽ gặp:

| dtype | Nghĩa | Gặp ở đâu |
|---|---|---|
| `uint8` | số nguyên 0–255 | ảnh đọc từ OpenCV |
| `float32` | số thực, 4 byte | dữ liệu đưa vào mô hình |
| `float64` | số thực, 8 byte | mặc định của numpy khi tính toán |
| `int64` | số nguyên | nhãn lớp |

**Cạm bẫy `uint8`:** kiểu này chỉ chứa được 0 đến 255. Cộng quá 255 thì nó
**quay vòng về 0**, không báo lỗi:

```python
x = np.array([250], dtype=np.uint8)
x + 10        # array([4], dtype=uint8)   ← 260 quay vòng thành 4
```

Nếu bạn định tăng độ sáng ảnh bằng cách cộng thêm 50, những pixel vốn đã sáng
sẽ đột nhiên thành đen. Cách đúng: đổi sang `float`, tính, cắt về khoảng
`[0, 255]`, rồi đổi lại `uint8`.

**Cạm bẫy `float32` với PyTorch:** PyTorch mặc định dùng `float32`, numpy mặc
định `float64`. Đưa mảng `float64` vào mô hình sẽ báo lỗi kiểu. Cứ ép sẵn:

```python
X = X.astype(np.float32)
```

### 2.4. Chỉ mục và lát cắt

```python
pts = np.zeros((33, 2))   # 33 khớp, mỗi khớp (x, y)

pts[23]           # khớp số 23 — mảng 2 phần tử [x, y]
pts[23, 0]        # tọa độ x của khớp 23 — một số
pts[:, 0]         # tọa độ x của TẤT CẢ khớp — mảng 33 phần tử
pts[11:13]        # khớp 11 và 12 (không bao gồm 13)
pts[[11, 12, 23, 24]]   # chọn đúng 4 khớp theo danh sách chỉ số
pts[-1]           # khớp cuối cùng
```

Hai điều dễ nhầm:

- **Đếm từ 0.** Khớp "số 1" trong tài liệu MediaPipe là `pts[0]`.
- **Lát cắt loại trừ đầu cuối.** `pts[11:13]` cho 2 phần tử, không phải 3.

Dấu `:` nghĩa là "toàn bộ chiều này". Nên `pts[:, 0]` đọc là: mọi hàng, cột 0.

Chọn theo danh sách chỉ số (*fancy indexing*) là cách bạn sẽ dùng để bỏ 10
điểm trên mặt:

```python
BODY = [0] + list(range(11, 33))   # mũi + từ vai trở xuống → 23 điểm
body_pts = pts[BODY]               # shape (23, 2)
```

### 2.5. Vector hóa — viết code không dùng vòng lặp

Đây là thay đổi tư duy lớn nhất khi học numpy. So sánh hai cách tính khoảng
cách từ mỗi khớp tới gốc:

```python
# Cách của người mới — vòng lặp Python
d = []
for i in range(33):
    d.append((pts[i,0]**2 + pts[i,1]**2) ** 0.5)

# Cách numpy — một dòng, nhanh hơn ~50 lần
d = np.linalg.norm(pts, axis=1)
```

Cách thứ hai không chỉ nhanh hơn. Nó **ngắn hơn nên ít chỗ để sai hơn**, và
đọc gần với công thức toán hơn.

Nguyên tắc: nếu bạn đang viết `for` để duyệt qua các phần tử của một mảng
numpy, gần như chắc chắn có cách viết không cần vòng lặp.

### 2.6. Broadcasting — quy tắc quan trọng nhất và khó nhất

Broadcasting cho phép cộng/trừ/nhân hai mảng **khác shape**, bằng cách numpy
tự động "kéo giãn" mảng nhỏ hơn.

Ví dụ trực tiếp từ đồ án — dời gốc tọa độ về hông:

```python
pts = ...            # shape (33, 2)  — 33 khớp
hip = (pts[23] + pts[24]) / 2    # shape (2,)  — một điểm

centered = pts - hip # shape (33, 2)
```

`pts` có 33 hàng, `hip` chỉ có 1 điểm. numpy tự hiểu là: trừ `hip` khỏi **từng
hàng** của `pts`. Đúng thứ ta muốn, và không cần vòng lặp.

**Quy tắc:** numpy so shape từ **chiều cuối cùng ngược về trước**. Hai chiều
tương thích nếu chúng bằng nhau, hoặc một trong hai bằng 1.

```
pts:  (33, 2)
hip:      (2,)   ← được xem như (1, 2)
          ↓
     2 khớp 2 ✓ ;  33 khớp 1 → giãn ra 33 ✓
kết quả: (33, 2)
```

**Cạm bẫy nguy hiểm:** broadcasting đôi khi "thành công" khi bạn không muốn.
Nếu bạn vô tình có shape `(33, 1)` thay vì `(33,)`, numpy vẫn tính được nhưng
cho ra `(33, 33)` — im lặng, không báo lỗi, và sai hoàn toàn. Đây là lý do
thói quen in shape rất đáng giá.

### 2.7. Các hàm gặp thường xuyên trong đồ án

```python
np.mean(x, axis=0)        # trung bình theo chiều 0
np.std(x, axis=0)         # độ lệch chuẩn
np.diff(x, axis=0)        # sai phân — dùng để tính vận tốc
np.linalg.norm(v)         # độ dài vector
np.dot(u, v)              # tích vô hướng — dùng để tính góc
np.arccos(c)              # arc cosine, trả về radian
np.degrees(r)             # radian → độ
np.clip(x, -1, 1)         # cắt về khoảng — bắt buộc trước arccos
np.concatenate([a, b])    # nối mảng
np.stack([a, b])          # xếp chồng, tạo chiều mới
x.reshape(-1)             # làm phẳng; -1 nghĩa là "tự tính"
np.save("f.npy", x)       # lưu mảng
np.load("f.npy")          # đọc lại
```

**Về `axis`:** đây là khái niệm hay gây bối rối. `axis=k` nghĩa là "gộp lại
theo chiều thứ k, làm chiều đó biến mất".

```python
x.shape                   # (30, 46)  — 30 frame, 46 đặc trưng
np.mean(x, axis=0).shape  # (46,)  — trung bình QUA CÁC FRAME
np.mean(x, axis=1).shape  # (30,)  — trung bình QUA CÁC ĐẶC TRƯNG
```

Trong đồ án, khi nén một cửa sổ 30 frame thành một vector đặc trưng, bạn dùng
`axis=0`: gộp chiều thời gian lại.

### 2.8. Lưu và đọc `.npy`

Định dạng `.npy` là cách lưu mảng numpy nguyên vẹn — giữ cả shape lẫn dtype,
đọc lại rất nhanh.

```python
np.save("data/skeletons/p01_vaytay_01.npy", arr)
arr = np.load("data/skeletons/p01_vaytay_01.npy")
```

Đây là lý do đề cương yêu cầu **trích khung xương một lần rồi lưu ra `.npy`**.
Chạy MediaPipe trên toàn bộ video mất vài phút; đọc file `.npy` mất vài phần
trăm giây. Bạn sẽ huấn luyện lại mô hình hàng chục lần trong tuần 6 và tuần 8 —
chênh lệch này cộng dồn thành nhiều giờ.

---

## 3. Đọc traceback

Khi Python gặp lỗi, nó in ra một khối chữ đỏ gọi là *traceback*. Người mới
thường hoảng và bỏ qua. Nhưng traceback là thứ **dễ đọc nhất** trong lập trình,
nếu biết đọc đúng chỗ.

### Đọc từ dưới lên

```
Traceback (most recent call last):
  File "train.py", line 42, in <module>
    X = build_features(skeletons)
  File "features.py", line 18, in build_features
    hip = (pts[23] + pts[24]) / 2
IndexError: index 24 is out of bounds for axis 0 with size 23
```

Ba phần cần đọc, **theo thứ tự ngược từ dưới lên**:

1. **Dòng cuối cùng** — loại lỗi và mô tả. Đây là câu trả lời.
   `IndexError: index 24 is out of bounds for axis 0 with size 23`
   → Bạn đang truy cập phần tử 24 của một mảng chỉ có 23 phần tử.

2. **Dòng ngay trên nó** — dòng code gây lỗi.
   `hip = (pts[23] + pts[24]) / 2` trong `features.py` dòng 18.

3. **Các dòng phía trên nữa** — chuỗi hàm đã gọi tới đó. Chỉ cần khi lỗi nằm
   sâu trong thư viện.

Trong ví dụ này, nguyên nhân đã rõ: bạn đã bỏ 10 điểm mặt (còn 23 khớp) nhưng
hàm chuẩn hóa vẫn dùng chỉ số 23, 24 của bộ 33 điểm gốc. Đây là một lỗi thật
và rất hay xảy ra trong đồ án này.

### Bảng lỗi thường gặp

| Lỗi | Nghĩa | Nguyên nhân hay gặp |
|---|---|---|
| `ModuleNotFoundError` | Không tìm thấy thư viện | Quên `conda activate`, hoặc cài nhầm môi trường |
| `AttributeError: 'NoneType' object has no attribute ...` | Bạn đang dùng `None` như một đối tượng | Hàm trả về `None` (webcam không mở được, khung xương không phát hiện được) mà bạn không kiểm tra |
| `IndexError` | Chỉ số vượt kích thước | Nhầm 33 khớp với 23 khớp |
| `ValueError: shapes (a,b) and (c,d) not aligned` | Shape không khớp | Quên reshape, hoặc nhầm thứ tự chiều |
| `RuntimeError: expected scalar type Float but found Double` | PyTorch nhận `float64` | Thiếu `.astype(np.float32)` |
| `cv2.error: ... !_src.empty()` | OpenCV nhận ảnh rỗng | Đường dẫn sai, hoặc video đã hết frame |

### Lỗi im lặng — nguy hiểm hơn nhiều

Loại lỗi tệ nhất **không** ném traceback. Chương trình chạy trơn tru, cho ra
kết quả, và kết quả sai.

Ví dụ kinh điển của đồ án này: đưa ảnh BGR vào MediaPipe thay vì RGB.
MediaPipe không báo lỗi — nó chỉ phát hiện người kém hơn, hoặc không phát hiện
được. Bạn sẽ nghĩ mô hình dở, trong khi thật ra dữ liệu vào đã hỏng.

Phòng chống bằng **khẳng định** (`assert`) — viết ra điều bạn tin là đúng, để
chương trình dừng ngay khi nó sai:

```python
assert pts.shape == (33, 2), f"shape sai: {pts.shape}"
assert 0 <= lm.x <= 1, f"x ngoài khoảng [0,1]: {lm.x}"
```

Tốn ba giây để viết, tiết kiệm ba tiếng để gỡ.

---

## 4. git — mức tối thiểu

Bạn làm cá nhân nên không cần nhánh, không cần merge. Chỉ cần git để:

- Quay lại được phiên bản chạy đúng khi bạn làm hỏng thứ gì đó
- Có một repo sạch để nộp

### Vòng lặp hằng ngày

```bash
git init                       # một lần duy nhất, lúc bắt đầu
git add .                      # đánh dấu các file đã đổi
git commit -m "them ham chuan hoa toa do"    # lưu một mốc
git log --oneline              # xem lịch sử
```

Commit sau mỗi lần làm xong một việc có nghĩa, không phải sau mỗi dòng. Thông
điệp commit nên nói **bạn đã làm gì**, không phải "update" hay "fix".

### `.gitignore` — quan trọng với đồ án này

Đừng bao giờ đưa video và file dữ liệu vào git. Video vài GB sẽ làm repo phình
ra và không thể sửa lại được sau này. Tạo file `.gitignore`:

```
data/raw/          # video gốc
data/skeletons/    # file .npy
*.mp4
*.npy
__pycache__/
*.pth              # trọng số mô hình
.ipynb_checkpoints/
```

Repo chỉ chứa **code**. Dữ liệu nộp riêng qua Drive hoặc USB.

### Repo cuối cùng nên trông thế nào

```
action-recognition/
├── README.md          # cách cài, cách chạy, cách quay lại kết quả
├── requirements.txt
├── .gitignore
├── src/
│   ├── extract.py     # video → .npy
│   ├── features.py    # chuẩn hóa + trích đặc trưng
│   ├── train_rf.py    # rừng ngẫu nhiên
│   ├── train_lstm.py  # LSTM
│   └── demo.py        # webcam thời gian thực
└── notebooks/         # thí nghiệm, biểu đồ
```

Một README chạy lại được là điểm cộng rẻ nhất trong toàn đồ án. Nhiều người bỏ
qua nó.

---

## Tự kiểm tra

Trả lời được không cần nhìn lại tài liệu:

1. Bạn chạy `pip install mediapipe`, thành công. Chạy `python demo.py`, báo
   `ModuleNotFoundError: No module named 'mediapipe'`. Nguyên nhân khả dĩ nhất
   là gì, và kiểm tra thế nào?

2. `pts` có shape `(33, 2)`. Viết một dòng tính tọa độ y trung bình của tất cả
   khớp.

3. `pts` shape `(33, 2)`, `hip` shape `(2,)`. `pts - hip` cho ra shape gì? Giải
   thích theo quy tắc broadcasting.

4. `X` shape `(30, 46)` là một cửa sổ 30 frame với 46 đặc trưng mỗi frame. Bạn
   muốn giá trị trung bình của **từng đặc trưng** qua cả cửa sổ. Dùng `axis` mấy,
   kết quả shape gì?

5. Đọc traceback này và nói nguyên nhân:
   ```
   File "demo.py", line 31, in <module>
       rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
   cv2.error: OpenCV(4.9.0) error: (-215:Assertion failed) !_src.empty()
   ```

6. Vì sao đề cương yêu cầu lưu khung xương ra `.npy` thay vì chạy lại MediaPipe
   mỗi lần huấn luyện?

<details>
<summary>Đáp án gợi ý</summary>

1. Bạn cài gói khi chưa `conda activate action`, nên nó vào môi trường base;
   hoặc bạn chạy `python` bằng một Python khác. Kiểm tra bằng
   `python -c "import sys; print(sys.executable)"` và xem đường dẫn có chứa
   `envs\action` không.

2. `pts[:, 1].mean()`

3. `(33, 2)`. numpy so từ chiều cuối: 2 với 2 khớp; chiều còn lại của `hip`
   được coi là 1 nên giãn thành 33. Kết quả: `hip` bị trừ khỏi từng khớp.

4. `axis=0`, vì ta gộp chiều thời gian. Kết quả shape `(46,)`.

5. `_src.empty()` nghĩa là ảnh đưa vào rỗng. `cap.read()` đã trả về `None` —
   webcam không mở được, hoặc video đã hết frame mà bạn không kiểm tra giá trị
   `ok` trả về.

6. Chạy MediaPipe trên toàn bộ video mất vài phút mỗi lần; đọc `.npy` mất chưa
   tới một giây. Bạn sẽ huấn luyện lại hàng chục lần khi thử các cấu hình khác
   nhau, nên chênh lệch cộng dồn rất lớn. Ngoài ra tách hai bước còn giúp gỡ
   lỗi: nếu kết quả sai, bạn biết ngay là lỗi ở khâu trích hay khâu học.

</details>

---

## Đưa gì vào báo cáo

Tầng này **gần như không xuất hiện** trong chương lý thuyết — nó là công cụ,
không phải kiến thức chuyên môn. Chỗ duy nhất nó nên xuất hiện:

- Một đoạn ngắn trong chương 3 (Hệ thống) hoặc phụ lục: liệt kê môi trường,
  phiên bản Python và các thư viện chính, kèm `requirements.txt`.
- Câu "toàn bộ hệ thống chạy trên CPU, không yêu cầu GPU" là một điểm đáng nêu,
  vì nó cho thấy hệ thống triển khai được trên máy phổ thông.

Đừng viết một chương về conda. Không ai muốn đọc.
