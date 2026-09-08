# Tầng 4 — Mô hình chuỗi thời gian

> **Câu hỏi mở đầu:** Vì sao không thể phân biệt "ngồi xuống" với "đứng dậy"
> nếu chỉ nhìn một khung hình duy nhất, dù khung hình đó rõ nét đến đâu?

Vì hai hành động đi qua **đúng cùng những tư thế**. Một bức ảnh người đang ở tư
thế nửa ngồi là bằng chứng cho cả hai — nó không chứa thông tin về việc người
đó đang đi xuống hay đi lên.

Thông tin đó chỉ tồn tại **giữa các frame**, không nằm trong bất kỳ frame nào.
Toàn bộ tầng này là về cách nắm bắt nó.

---

## 1. Cửa sổ trượt

### Ý tưởng

Thay vì phân loại một frame, ta phân loại một **đoạn** gồm `T` frame liên tiếp.
Đoạn đó gọi là một **cửa sổ**.

```
frame:   1  2  3  4  5  6  7  8  9  10 11 12 ...
        └─────── cửa sổ 1 ───────┘
           └─────── cửa sổ 2 ───────┘
              └─────── cửa sổ 3 ───────┘
```

Mỗi cửa sổ là một **mẫu** để huấn luyện, có shape `(T, F)`: `T` bước thời gian,
`F` đặc trưng mỗi bước. Với đồ án này, `T = 30` và `F = 46` (23 khớp × 2 tọa
độ).

### Ba tham số

**Độ dài cửa sổ `T`.** Bao nhiêu frame nhìn cùng lúc.

**Bước trượt (*stride*) `S`.** Cửa sổ tiếp theo bắt đầu cách bao nhiêu frame.

- `S = 1`: cửa sổ chồng lấn tối đa, tạo nhiều mẫu nhất từ cùng lượng video
- `S = T`: không chồng lấn, mỗi frame chỉ thuộc một cửa sổ

**Nhãn.** Cửa sổ này thuộc hành động nào?

### Chọn `T` thế nào

Đây là một đánh đổi thật, và đề cương yêu cầu khảo sát nó ở tuần 8.

| `T` nhỏ (15 frame ≈ 0,5s) | `T` lớn (45 frame ≈ 1,5s) |
|---|---|
| Phản hồi nhanh, độ trễ thấp | Độ trễ cao — phải chờ đủ frame |
| Có thể không đủ để thấy trọn một hành động | Bao trọn hành động chậm |
| Ít nhiễu do trộn lẫn nhiều hành động | Dễ chứa hai hành động khác nhau trong cùng cửa sổ |
| Ít tham số hơn cho LSTM | Nhiều bối cảnh hơn để phân biệt |

Nguyên tắc thực hành: **`T` nên bằng hoặc hơi lớn hơn độ dài của hành động ngắn
nhất**.

Với sáu hành động của đồ án:

- Ngã: khoảng 0,5–1 giây — nhanh nhất
- Ngồi xuống, đứng dậy: 1–2 giây
- Vẫy tay, đi bộ tại chỗ: tuần hoàn, không có độ dài cố định — cần đủ để thấy
  ít nhất một chu kỳ
- Đứng yên: không có độ dài

`T = 30` ở 30 FPS = 1 giây là điểm khởi đầu hợp lý: đủ để chứa một cú ngã trọn
vẹn và ít nhất một chu kỳ vẫy tay.

**Khảo sát 15 / 30 / 45 ở tuần 8 và làm một bảng.** Điều thú vị cần tìm: `T`
tối ưu có thể **khác nhau giữa các lớp**. Ngã có thể tốt hơn ở `T` nhỏ (vì nó
nhanh), đi bộ tại chỗ tốt hơn ở `T` lớn (cần nhiều chu kỳ). Nếu bạn quan sát
được điều này và viết ra, đó là một phát hiện thật từ dữ liệu của bạn — đúng
loại nội dung mà chương Thảo luận cần.

### Chọn bước trượt `S`

**Khi huấn luyện:** `S` nhỏ (1 hoặc 2) để có nhiều mẫu. Video 5 giây ở 30 FPS
cho 150 frame; với `T=30, S=1` được 121 cửa sổ, với `S=30` chỉ được 5.

**Nhưng có cái bẫy:** các cửa sổ chồng lấn **gần như giống hệt nhau**. Cửa sổ
bắt đầu ở frame 1 và cửa sổ bắt đầu ở frame 2 khác nhau đúng 1/30. Chúng không
phải mẫu độc lập.

Hệ quả:

1. **Số mẫu hiệu dụng ít hơn nhiều so với số mẫu danh nghĩa.** Bạn có 121 cửa
   sổ nhưng lượng thông tin chỉ tương đương vài mẫu độc lập.
2. **Nếu chia tập ngẫu nhiên thì rò rỉ dữ liệu nghiêm trọng.** Cửa sổ 1 vào tập
   huấn luyện, cửa sổ 2 vào tập kiểm thử — chúng gần như giống hệt nhau, nên mô
   hình chỉ cần nhớ. Kết quả 99% và hoàn toàn giả.

Điểm 2 là cạm bẫy số một của cả đồ án. Xem tầng 5 để xử lý đúng.

**Khi chạy demo:** `S` là "mỗi bao nhiêu frame thì dự đoán lại". Đề cương khuyên
`S = 5` để tiết kiệm tính toán — hợp lý, vì cửa sổ 30 frame chỉ đổi 1/6 nội
dung sau 5 frame.

### Gán nhãn cho cửa sổ

Nếu video của bạn là "một hành động một file" (theo đúng giao thức quay ở đề
cương) thì mọi cửa sổ trong file đó lấy nhãn của file. Đơn giản.

Chỉ cần cẩn thận: **cắt bỏ vài frame đầu và cuối mỗi đoạn quay**, vì lúc đó bạn
đang đi tới vị trí hoặc đang chuẩn bị, chưa thực sự thực hiện hành động. Những
frame này gán nhãn sai và làm nhiễu tập huấn luyện.

Nếu về sau bạn quay video liên tục nhiều hành động, có hai quy ước:

- **Nhãn frame cuối** — cửa sổ mang nhãn của frame cuối cùng. Đúng với ngữ cảnh
  thời gian thực: ta hỏi "ngay bây giờ đang là hành động gì?"
- **Nhãn đa số** — nhãn xuất hiện nhiều nhất trong cửa sổ. Đúng cho phân đoạn
  ngoại tuyến.

Đồ án này nên dùng **nhãn frame cuối** vì nó khớp với cách hệ thống được dùng.

### Tính nhân quả — không được nhìn về tương lai

Trong hệ thống thời gian thực, ở thời điểm `t` bạn chỉ có các frame từ `t−T+1`
tới `t`. Frame `t+1` chưa tồn tại.

Nghe hiển nhiên, nhưng nó **loại bỏ một số kỹ thuật** mà bạn có thể vô tình
dùng:

- **LSTM hai chiều (bidirectional)** đọc chuỗi cả xuôi lẫn ngược. Cho kết quả
  tốt hơn, nhưng cần biết toàn bộ chuỗi trước. **Không dùng được cho thời gian
  thực.**
- **Làm mượt hai phía** (trung bình trượt căn giữa) dùng cả frame trước và sau.
  Khi chạy thật chỉ được dùng frame trước.
- **Chuẩn hóa theo thống kê của cả video** (trừ trung bình toàn video) là nhìn
  về tương lai. Chuẩn hóa của bạn dùng thống kê **của riêng frame hiện tại**
  (hông và vai của chính frame đó), nên nó hợp lệ — may mắn thay.

**Cảnh báo quan trọng:** nếu bạn huấn luyện với LSTM hai chiều rồi báo cáo con
số đó cho một hệ thống "thời gian thực", đó là sai sót phương pháp nghiêm
trọng. Hội đồng có thể phát hiện. Dùng LSTM một chiều.

---

## 2. Phân loại — nhắc lại khái niệm

Nếu bạn chưa học máy học bao giờ, đọc mục này. Nếu đã học, bỏ qua.

**Học có giám sát:** ta có `N` cặp `(x, y)`, trong đó `x` là đầu vào (một cửa
sổ khung xương) và `y` là nhãn đúng (một trong 6 hành động). Mục tiêu: tìm một
hàm `f` sao cho `f(x) ≈ y`, **và quan trọng hơn**, `f` hoạt động tốt trên những
`x` chưa từng thấy.

Vế thứ hai mới là điều khó. Học thuộc lòng tập huấn luyện là chuyện dễ; **tổng
quát hóa** mới là bài toán thật.

**Phân loại** (khác với hồi quy): đầu ra là một trong `C` lớp rời rạc, không
phải một con số liên tục. Đây là bài toán của bạn với `C = 6`.

**Ba tập dữ liệu, ba vai trò khác nhau:**

| Tập | Dùng để | Được xem bao nhiêu lần |
|---|---|---|
| Huấn luyện (train) | Mô hình học tham số từ đây | Rất nhiều |
| Kiểm định (validation) | Chọn siêu tham số, quyết định khi nào dừng | Nhiều lần, nhưng không dùng để cập nhật tham số |
| Kiểm thử (test) | Báo cáo kết quả cuối cùng | **Đúng một lần, ở cuối** |

**Tham số** là những gì mô hình học (trọng số LSTM). **Siêu tham số** là những
gì bạn chọn (`T`, hidden size, learning rate). Tham số học từ tập huấn luyện;
siêu tham số chọn dựa trên tập kiểm định.

Nếu bạn dùng tập kiểm thử để chọn siêu tham số — thử 20 cấu hình và báo cáo cái
tốt nhất trên tập kiểm thử — thì con số đó đã bị thổi phồng. Bạn đã dùng tập
kiểm thử như tập kiểm định.

---

## 3. Mô hình 1 — Rừng ngẫu nhiên

Đề cương bắt đầu từ đây, và thứ tự này có chủ ý. Bạn thấy bài toán giải được
**trước khi** học sâu xuất hiện, nên hiểu được học sâu thêm vào cái gì.

### 3.1. Cây quyết định

Rừng ngẫu nhiên được xây từ cây quyết định. Bắt đầu từ cây.

Một cây quyết định là một chuỗi câu hỏi có/không:

```
tốc độ cổ tay > 0.05?
├── không → góc gối trung bình > 150°?
│           ├── có → "đứng yên"
│           └── không → "ngồi" (tư thế tĩnh, gối gập)
└── có   → biên độ dao động cổ tay > 0.3?
            ├── có → "vẫy tay"
            └── không → tốc độ cổ chân > 0.04?
                        ├── có → "đi bộ tại chỗ"
                        └── không → ...
```

**Cây học thế nào:** ở mỗi nút, thuật toán duyệt **mọi đặc trưng** và **mọi
ngưỡng có thể**, chọn cặp (đặc trưng, ngưỡng) chia dữ liệu thành hai nhóm
"thuần" nhất — tức là mỗi nhóm càng thiên về một lớp càng tốt. Đo độ thuần bằng
*chỉ số Gini* hoặc *entropy*. Lặp đệ quy cho tới khi nhóm đủ thuần hoặc đạt độ
sâu tối đa.

**Ưu điểm của cây:**

- **Giải thích được hoàn toàn.** In cây ra và đọc được từng quyết định.
- **Không cần chuẩn hóa đặc trưng.** Cây chỉ so sánh với ngưỡng, nên đặc trưng
  có thang khác nhau (góc tính bằng độ, tốc độ tính bằng đơn vị thân/frame) vẫn
  dùng chung được. Đây là lợi thế lớn cho vector đặc trưng thủ công hỗn tạp của
  bạn.
- **Bắt được quan hệ phi tuyến** một cách tự nhiên.

**Nhược điểm chí mạng:** một cây đơn lẻ **quá khớp nặng**. Cho đủ độ sâu, nó sẽ
học thuộc từng mẫu huấn luyện, tạo ra ranh giới quyết định vụn vặt bám sát
nhiễu. Đổi một mẫu trong tập huấn luyện có thể làm cả cây khác hẳn.

### 3.2. Từ một cây thành một rừng

Ý tưởng: **nhiều cây yếu, mỗi cây sai một kiểu, lấy đa số thì các lỗi triệt
tiêu nhau.**

Ẩn dụ: hỏi một chuyên gia thì bạn nhận cả kiến thức lẫn thiên kiến của người
đó. Hỏi 100 người có góc nhìn khác nhau rồi lấy ý kiến đa số thì các thiên kiến
cá nhân triệt tiêu, phần đúng chung còn lại.

Điều kiện để hoạt động: **các cây phải khác nhau**. Nếu 100 cây giống hệt nhau
thì bỏ phiếu vô nghĩa. Rừng ngẫu nhiên tạo sự đa dạng bằng hai nguồn ngẫu
nhiên:

**Nguồn 1 — Bagging (lấy mẫu có hoàn lại).** Mỗi cây được huấn luyện trên một
tập con lấy ngẫu nhiên **có hoàn lại** từ dữ liệu gốc, cùng kích thước. Do có
hoàn lại, khoảng 37% mẫu gốc không xuất hiện trong tập con đó, và một số mẫu
xuất hiện nhiều lần. Mỗi cây vì thế thấy một "phiên bản" dữ liệu hơi khác.

**Nguồn 2 — Không gian con ngẫu nhiên.** Ở mỗi nút, cây chỉ được chọn ngưỡng
trong một **tập con ngẫu nhiên** các đặc trưng (thường là √F trong số F đặc
trưng), không phải toàn bộ.

Nguồn 2 quan trọng hơn người ta tưởng. Không có nó, nếu có một đặc trưng cực
mạnh (chẳng hạn `delta_hip_y`), **mọi** cây sẽ dùng nó ở nút gốc và các cây trở
nên rất giống nhau. Ép cây phải xoay xở khi thiếu đặc trưng mạnh nhất buộc
chúng khám phá các đường khác — và làm rừng đa dạng thật.

### 3.3. Vì sao rừng ngẫu nhiên hợp với đồ án này

- **Hoạt động tốt với ít dữ liệu.** Vài nghìn mẫu là quá đủ. Học sâu thì không.
- **Rất ít siêu tham số phải chỉnh.** `n_estimators=200` và để mặc định phần
  còn lại là gần như tối ưu. Không có learning rate, không có số epoch, không
  có lịch giảm tốc độ học.
- **Không cần chuẩn hóa đặc trưng**, như đã nói.
- **Huấn luyện trong vài giây** trên CPU.
- **Giải thích được** qua `feature_importances_`.

```python
from sklearn.ensemble import RandomForestClassifier

clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train, y_train)            # X_train: (N, ~30)
acc = clf.score(X_test, y_test)
```

Bốn dòng. Đây là toàn bộ mô hình 1.

### 3.4. Độ quan trọng đặc trưng — dùng cẩn thận

```python
import numpy as np
order = np.argsort(clf.feature_importances_)[::-1]
for i in order[:10]:
    print(f"{feature_names[i]:30s} {clf.feature_importances_[i]:.3f}")
```

Biểu đồ xếp hạng đặc trưng là hình đẹp và dễ hiểu cho báo cáo. Nếu `delta_hip_y`
đứng đầu, bạn có bằng chứng thực nghiệm rằng thiết kế đặc trưng ở tầng 3 đã
đúng.

**Nhưng có ba cảnh báo:**

1. **Thiên lệch với đặc trưng nhiều giá trị.** Đặc trưng liên tục có nhiều
   ngưỡng khả dĩ hơn nên dễ được chọn hơn, ngay cả khi không hữu ích thật.
2. **Đặc trưng tương quan chia sẻ điểm.** Nếu góc gối trái và góc gối phải gần
   như giống nhau, độ quan trọng bị chia đôi và cả hai trông kém quan trọng hơn
   thực tế.
3. **Đây là độ quan trọng cho việc *chia dữ liệu*, không phải quan hệ nhân quả.**

Nếu muốn chắc chắn hơn, dùng **hoán vị đặc trưng** (*permutation importance*):
xáo trộn ngẫu nhiên một cột trong tập kiểm thử và đo độ chính xác tụt bao
nhiêu. Cách này đo trực tiếp "mô hình phụ thuộc đặc trưng này bao nhiêu":

```python
from sklearn.inspection import permutation_importance
r = permutation_importance(clf, X_test, y_test, n_repeats=10, random_state=42)
```

Nêu được sự khác biệt giữa hai cách đo này trong báo cáo là một điểm cộng.

---

## 4. Mạng nơ-ron — nền tảng tối thiểu

Trước khi tới LSTM, cần hiểu mạng nơ-ron thường. Phần này viết cho người chưa
biết gì.

### 4.1. Một nơ-ron

Một nơ-ron nhận nhiều số vào, cho một số ra:

```
y = f(w₁x₁ + w₂x₂ + ... + wₙxₙ + b)
```

- `x` là đầu vào
- `w` là **trọng số** — mô hình học chúng
- `b` là **độ chệch** (bias) — cũng học
- `f` là **hàm kích hoạt** — một hàm phi tuyến cố định

Không có `f`, xếp chồng bao nhiêu lớp cũng chỉ tương đương một phép biến đổi
tuyến tính duy nhất — vô dụng. Chính tính phi tuyến làm mạng sâu có ý nghĩa.

Hàm kích hoạt phổ biến nhất là **ReLU**: `f(x) = max(0, x)`. Đơn giản đến mức
đáng ngạc nhiên, nhưng nó hiệu quả và tính đạo hàm rất rẻ.

### 4.2. Lớp và mạng

Một **lớp** là nhiều nơ-ron song song, cùng nhận một đầu vào. Xếp chồng nhiều
lớp thì đầu ra lớp này là đầu vào lớp sau.

```
46 số vào → lớp ẩn (128 nơ-ron) → lớp ẩn (128) → lớp ra (6 nơ-ron)
```

Lớp cuối có đúng 6 nơ-ron, mỗi nơ-ron cho một điểm số ứng với một hành động.

### 4.3. Từ điểm số tới xác suất — softmax

Sáu điểm số thô (gọi là *logit*) có thể là bất kỳ số thực nào. Ta muốn xác suất:
không âm, tổng bằng 1.

```
p_i = exp(z_i) / Σ_j exp(z_j)
```

Ví dụ: logit `[2.0, 1.0, 0.1, -1.0, 0.5, 0.2]` → softmax cho khoảng
`[0.48, 0.18, 0.07, 0.02, 0.11, 0.08]`. Lớp đầu tiên có xác suất 48%.

Con số này chính là "độ tin cậy" bạn hiển thị lên màn hình ở tuần 9.

> **Một lưu ý trung thực:** xác suất softmax **không được hiệu chuẩn tốt**. Mạng
> nơ-ron thường quá tự tin — nó có thể nói 95% khi thực tế chỉ đúng 70% số lần.
> Dùng con số này để làm ngưỡng lọc thì được; diễn giải nó như xác suất thật thì
> không nên. Nêu điều này trong phần Thảo luận là một dấu hiệu của sự cẩn thận.

### 4.4. Hàm mất mát — cross-entropy

Ta cần một con số đo "mô hình sai bao nhiêu" để tối ưu. Với phân loại, dùng
**cross-entropy**:

```
loss = −log(p_đúng)
```

Chỉ nhìn xác suất mà mô hình gán cho lớp **đúng**:

- Gán 0.99 cho lớp đúng → loss = 0.01, gần như không phạt
- Gán 0.50 → loss = 0.69
- Gán 0.01 → loss = 4.6, phạt rất nặng

Tính chất quan trọng: hàm `−log` **phạt cực nặng sự tự tin sai lầm**. Nói chắc
chắn và sai thì tệ hơn nhiều so với nói do dự và sai. Đây đúng là hành vi ta
muốn.

Trong PyTorch, `nn.CrossEntropyLoss()` gộp cả softmax lẫn cross-entropy. **Nên
đầu ra của mô hình phải là logit thô, không được tự áp softmax trước.** Áp
softmax hai lần là lỗi im lặng phổ biến: mô hình vẫn huấn luyện, chỉ là kém hơn
và bạn không biết vì sao.

### 4.5. Học bằng gradient descent

Mô hình bắt đầu với trọng số ngẫu nhiên và loss cao. Cách cải thiện:

1. Đưa một lô dữ liệu qua mạng, tính loss (**lượt thuận**)
2. Tính đạo hàm của loss theo **từng** trọng số (**lượt nghịch**, hay *lan
   truyền ngược*)
3. Dịch mỗi trọng số một chút theo hướng làm giảm loss
4. Lặp lại

Đạo hàm cho biết "nếu tăng trọng số này một chút thì loss thay đổi thế nào".
Lan truyền ngược là thuật toán tính hiệu quả tất cả các đạo hàm đó cùng lúc,
bằng quy tắc chuỗi. PyTorch làm việc này tự động — bạn chỉ cần gọi
`loss.backward()`.

**Tốc độ học** (learning rate) quyết định bước dịch lớn bao nhiêu:

- Quá lớn: loss nhảy loạn hoặc thành `nan`
- Quá nhỏ: học rất chậm, có thể kẹt

Với LSTM trên dữ liệu nhỏ, `1e-3` là điểm khởi đầu tốt, dùng tối ưu hóa
**Adam**.

### 4.6. Từ vựng cần thuộc

| Thuật ngữ | Nghĩa |
|---|---|
| **Batch** | Một nhóm mẫu xử lý cùng lúc (thường 16–64). Nhanh hơn từng mẫu, ổn định hơn |
| **Epoch** | Một lượt đi qua toàn bộ tập huấn luyện |
| **Iteration** | Một lần cập nhật trọng số = một batch |
| **Tối ưu hóa** | Thuật toán quyết định cách cập nhật (SGD, Adam) |
| **Tốc độ học** | Kích thước bước cập nhật |

---

## 5. RNN — mạng có bộ nhớ

### 5.1. Vì sao mạng thường không đủ

Bạn có thể làm phẳng cửa sổ `(30, 46)` thành vector 1380 chiều và đưa vào mạng
nối đầy đủ. Nó **sẽ chạy**. Nhưng có ba vấn đề:

1. **Không chia sẻ tham số theo thời gian.** Mạng học "đặc trưng thứ 5 ở bước
   thời gian 3" như một thứ hoàn toàn tách biệt với "đặc trưng thứ 5 ở bước thời
   gian 20". Nó phải học lại cùng một mẫu hình cho từng vị trí thời gian.
2. **Số tham số lớn.** 1380 × 128 = 176.640 tham số chỉ ở lớp đầu.
3. **Độ dài cố định.** Muốn đổi `T` thì phải xây lại mạng.

Vấn đề 1 nghiêm trọng nhất về mặt khái niệm. Một cái vẫy tay là một cái vẫy tay
dù nó bắt đầu ở frame 3 hay frame 15. Mạng nối đầy đủ không biết điều đó.

### 5.2. Ý tưởng của RNN

**Mạng hồi quy** (*Recurrent Neural Network*) xử lý chuỗi **từng bước một**,
mang theo một **trạng thái ẩn** — một vector tóm tắt mọi thứ đã thấy tới lúc đó.

```
h₀ = 0 (vector khởi tạo)

bước 1:  h₁ = f(x₁, h₀)
bước 2:  h₂ = f(x₂, h₁)
bước 3:  h₃ = f(x₃, h₂)
...
bước 30: h₃₀ = f(x₃₀, h₂₉)

dự đoán = softmax(W · h₃₀)
```

Cùng một hàm `f` với **cùng bộ trọng số** dùng ở mọi bước. Đây là điểm mấu chốt:

- Số tham số **không phụ thuộc `T`**
- Mẫu hình học được ở bước 3 tự động áp dụng ở bước 20
- Xử lý được chuỗi độ dài bất kỳ

Trạng thái ẩn `h` chính là "bộ nhớ". Nó phải nén toàn bộ lịch sử liên quan
thành một vector cố định (chẳng hạn 128 chiều). Với bài toán của bạn, `h` cần
mã hóa những thứ như "hông đang đi xuống liên tục trong 20 frame qua" — đúng
loại thông tin phân biệt ngồi xuống với đứng dậy.

### 5.3. Vấn đề gradient tiêu biến

RNN đơn giản có một khiếm khuyết nghiêm trọng.

Khi lan truyền ngược qua 30 bước thời gian, đạo hàm phải nhân qua 30 lần cùng
một ma trận trọng số. Điều gì xảy ra:

- Nếu các giá trị **nhỏ hơn 1**: `0.9³⁰ ≈ 0.04`. Gradient teo về gần 0 →
  **tiêu biến**
- Nếu các giá trị **lớn hơn 1**: `1.1³⁰ ≈ 17`. Gradient bùng nổ → **bùng nổ**

Gradient bùng nổ dễ chữa: cắt ngưỡng (`clip_grad_norm_`).

Gradient tiêu biến khó hơn nhiều, và hậu quả là: **RNN không học được phụ thuộc
dài.** Nó nhớ được 5–10 bước, còn xa hơn thì tín hiệu học không truyền tới.

Với cửa sổ 30 frame, đây là vấn đề thật. Thông tin ở đầu cửa sổ (tư thế đứng
ban đầu) có thể không ảnh hưởng được tới dự đoán ở cuối.

---

## 6. LSTM

### 6.1. Ý tưởng cốt lõi

**Long Short-Term Memory** giải quyết gradient tiêu biến bằng cách thêm một
đường dẫn thông tin **gần như không bị can thiệp** xuyên qua thời gian.

Ẩn dụ: hình dung một **băng chuyền** chạy thẳng qua toàn bộ chuỗi. Thông tin
đặt lên băng chuyền đi tới cuối gần như nguyên vẹn — không bị nhân với ma trận
trọng số ở mỗi bước. Dọc băng chuyền có ba **van**, quyết định:

1. Xóa cái gì khỏi băng chuyền
2. Đặt thêm cái gì lên
3. Đọc ra cái gì để dùng ngay bây giờ

Băng chuyền đó là **trạng thái ô** (*cell state*), ký hiệu `c`. Ba van là ba
**cổng** (*gate*).

### 6.2. Ba cổng

Mỗi cổng là một mạng nơ-ron nhỏ cho ra một số trong `[0, 1]` cho mỗi chiều —
`0` là đóng hoàn toàn, `1` là mở hoàn toàn. Chúng dùng hàm sigmoid.

**Cổng quên** — bỏ gì khỏi bộ nhớ

```
f_t = σ(W_f · [h_{t−1}, x_t] + b_f)
```

Nhìn đầu vào hiện tại và trạng thái trước, quyết định giữ lại bao nhiêu phần
của bộ nhớ cũ. Ví dụ trực quan cho bài toán của bạn: khi hông bắt đầu đi xuống
sau một giai đoạn đứng yên, cổng quên có thể xóa thông tin "đang đứng yên" vì
nó không còn liên quan.

**Cổng vào** — thêm gì vào bộ nhớ

```
i_t = σ(W_i · [h_{t−1}, x_t] + b_i)      ← thêm bao nhiêu
c̃_t = tanh(W_c · [h_{t−1}, x_t] + b_c)   ← thêm cái gì
```

**Cập nhật băng chuyền:**

```
c_t = f_t ⊙ c_{t−1}  +  i_t ⊙ c̃_t
```

(`⊙` là nhân từng phần tử.) Chú ý: `c_{t−1}` chỉ bị **nhân với một số trong
[0,1]** rồi cộng thêm — không đi qua ma trận trọng số. Đây chính là lý do
gradient không tiêu biến: nếu cổng quên gần bằng 1, gradient chảy ngược qua
nhiều bước gần như không suy giảm.

**Cổng ra** — đọc gì ra để dùng ngay

```
o_t = σ(W_o · [h_{t−1}, x_t] + b_o)
h_t = o_t ⊙ tanh(c_t)
```

Trạng thái ô `c` là bộ nhớ dài hạn đầy đủ; trạng thái ẩn `h` là phần được lọc
ra để dùng ở bước này và truyền sang bước sau.

### 6.3. Điều quan trọng nhất cần hiểu

Đừng cố nhớ bốn công thức. Nhớ điều này:

> **RNN thường buộc thông tin phải đi qua một phép biến đổi ở mỗi bước thời
> gian, nên nó suy giảm theo hàm mũ. LSTM tạo một đường dẫn cộng dồn, chỉ bị
> nhân với một cổng — nên thông tin có thể đi xa mà không suy giảm. Ba cổng học
> cách quyết định giữ gì, thêm gì, đọc gì.**

Nếu bạn viết được đoạn đó bằng lời mình trong báo cáo và trả lời được câu hỏi
"vì sao LSTM tốt hơn RNN", bạn đã nắm đủ tầng này.

### 6.4. GRU — nhắc để biết

*Gated Recurrent Unit* là phiên bản đơn giản hơn: hai cổng thay vì ba, gộp
trạng thái ô và trạng thái ẩn làm một. Ít tham số hơn khoảng 25%, thường cho
kết quả tương đương LSTM, đôi khi tốt hơn trên dữ liệu nhỏ.

**Với dữ liệu ít như đồ án này, GRU đáng thử.** Đổi một dòng:

```python
self.rnn = nn.GRU(input_size=46, hidden_size=128, num_layers=2,
                  batch_first=True, dropout=0.3)
```

Thêm một hàng vào bảng so sánh của bạn với chi phí gần bằng 0.

---

## 7. Mô hình LSTM cho đồ án này

```python
import torch.nn as nn

class ActionLSTM(nn.Module):
    def __init__(self, n_joints=23, n_classes=6, hidden=128):
        super().__init__()
        self.lstm = nn.LSTM(input_size=n_joints * 2,
                            hidden_size=hidden,
                            num_layers=2,
                            batch_first=True,
                            dropout=0.3)
        self.fc = nn.Linear(hidden, n_classes)

    def forward(self, x):              # x: (batch, 30, 46)
        out, _ = self.lstm(x)          # out: (batch, 30, 128)
        return self.fc(out[:, -1, :])  # chỉ lấy bước thời gian cuối
```

### Giải thích từng tham số

**`input_size = 46`** — 23 khớp × 2 tọa độ. Phải khớp với số chiều dữ liệu của
bạn. Sai chỗ này là lỗi shape đầu tiên bạn gặp.

**`hidden_size = 128`** — kích thước vector bộ nhớ. Lớn hơn thì nhớ được nhiều
hơn nhưng nhiều tham số hơn và dễ quá khớp hơn. Với vài nghìn mẫu, **hãy thử
64** — có thể tốt hơn 128.

**`num_layers = 2`** — hai lớp LSTM xếp chồng. Đầu ra lớp một là đầu vào lớp
hai. Lớp trên học mẫu hình trừu tượng hơn. Với dữ liệu ít, một lớp cũng có thể
đủ; đây là một siêu tham số đáng khảo sát.

**`batch_first = True`** — quyết định thứ tự chiều là `(batch, T, F)` thay vì
`(T, batch, F)`. Đặt `True` cho dễ đọc. **Nhớ giữ nhất quán** — quên là nguồn
lỗi shape kinh điển.

**`dropout = 0.3`** — trong huấn luyện, ngẫu nhiên "tắt" 30% nơ-ron mỗi lượt.
Chống quá khớp: mạng không thể phụ thuộc vào một nơ-ron cụ thể vì nơ-ron đó có
thể biến mất, nên nó buộc phải học biểu diễn dư thừa và bền vững hơn. Trong
`nn.LSTM`, dropout chỉ áp dụng **giữa** các lớp, nên nó vô tác dụng khi
`num_layers=1` (PyTorch sẽ cảnh báo).

**`out[:, -1, :]`** — LSTM cho ra một vector `h` ở **mọi** bước thời gian. Ta
chỉ dùng bước cuối, vì `h₃₀` đã tóm tắt cả 30 bước.

### Các cách gộp khác

Lấy bước cuối là mặc định, nhưng không phải lựa chọn duy nhất:

| Cách | Code | Ghi chú |
|---|---|---|
| Bước cuối | `out[:, -1, :]` | Mặc định. Đúng với ngữ cảnh thời gian thực |
| Trung bình mọi bước | `out.mean(dim=1)` | Bền hơn với nhiễu; đôi khi tốt hơn trên dữ liệu ít |
| Cực đại mọi bước | `out.max(dim=1)[0]` | Bắt được "khoảnh khắc quyết định" trong cửa sổ |
| Nối trung bình và cực đại | `torch.cat([mean, max], 1)` | Thường tốt hơn cả hai, gấp đôi chiều vào lớp cuối |

Thử hai cách đầu là một hàng bảng rẻ nữa cho chương thí nghiệm.

### Đếm tham số

```python
n = sum(p.numel() for p in model.parameters())
print(f"{n:,} tham số")
```

Với cấu hình trên: khoảng **220.000 tham số**.

Đặt cạnh nhau: nếu bạn có 3.000 cửa sổ huấn luyện, thì có **73 tham số cho mỗi
mẫu**. Đây là tỉ lệ rất đáng lo. Quá khớp gần như chắc chắn xảy ra nếu không có
biện pháp phòng ngừa.

**Con số này nên có trong báo cáo.** Nó giải thích ngay tại sao bạn cần dropout,
tăng cường dữ liệu, và dừng sớm — và tại sao rừng ngẫu nhiên có thể thắng.

---

## 8. Huấn luyện và quá khớp

### 8.1. Quá khớp là gì

**Quá khớp** (*overfitting*): mô hình học thuộc tập huấn luyện, kể cả nhiễu, và
mất khả năng tổng quát hóa.

Nhận ra qua đường loss:

```
loss
  │
  │ ╲
  │  ╲___                    ← loss kiểm định (val)
  │      ╲___........····
  │           ╲·····
  │  ╲          ╲___
  │    ╲____        ╲____    ← loss huấn luyện (train)
  └──────────┬──────────────► epoch
             │
        điểm này: val bắt đầu tăng còn train tiếp tục giảm
        → từ đây trở đi là quá khớp. DỪNG Ở ĐÂY.
```

**Vẽ cả hai đường trên cùng một biểu đồ là bắt buộc**, và đây là một trong
những hình quan trọng nhất của chương thí nghiệm. Chỉ vẽ đường train thì không
nói lên gì cả — nó luôn giảm.

### 8.2. Các biện pháp chống quá khớp

Xếp theo hiệu quả với đồ án này:

| Biện pháp | Cách làm | Ghi chú |
|---|---|---|
| **Nhiều dữ liệu hơn** | Rủ thêm người diễn, quay thêm lần lặp | Hiệu quả nhất, không gì thay thế được |
| **Tăng cường dữ liệu** | Xem tầng 3 mục 11 | Rẻ và hiệu quả. Lật ngang nhân đôi dữ liệu |
| **Dừng sớm** | Lưu trọng số ở epoch có val loss thấp nhất | Miễn phí, luôn nên làm |
| **Mô hình nhỏ hơn** | `hidden=64`, `num_layers=1` | Rất đáng thử với dữ liệu ít |
| **Dropout** | Đã có `0.3`, thử `0.5` | Có thể tăng khá mạnh |
| **Suy giảm trọng số** | `Adam(..., weight_decay=1e-4)` | Phạt trọng số lớn |

### 8.3. Dừng sớm — mẫu code

```python
best_val = float("inf")
patience, bad_epochs = 10, 0

for epoch in range(200):
    train_one_epoch(model, train_loader, optimizer, criterion)
    val_loss = evaluate(model, val_loader, criterion)

    if val_loss < best_val:
        best_val, bad_epochs = val_loss, 0
        torch.save(model.state_dict(), "best.pth")   # lưu bản tốt nhất
    else:
        bad_epochs += 1
        if bad_epochs >= patience:
            print(f"Dung som o epoch {epoch}")
            break

model.load_state_dict(torch.load("best.pth"))        # ĐỪNG QUÊN dòng này
```

Dòng cuối rất hay bị quên. Không có nó, bạn đánh giá mô hình ở epoch cuối cùng
— tức là mô hình đã quá khớp — chứ không phải mô hình tốt nhất.

### 8.4. Vòng lặp huấn luyện — hai chỗ hay sai

```python
model.train()                 # bật dropout
for xb, yb in train_loader:
    optimizer.zero_grad()     # ← QUÊN LÀ SAI. Gradient tích lũy nếu không xóa
    out = model(xb)
    loss = criterion(out, yb)
    loss.backward()
    optimizer.step()

model.eval()                  # ← TẮT dropout khi đánh giá
with torch.no_grad():         # ← không tính gradient, nhanh hơn và tiết kiệm
    for xb, yb in val_loader:
        ...
```

**`optimizer.zero_grad()`:** PyTorch cộng dồn gradient thay vì ghi đè. Quên xóa
thì gradient của mọi batch cộng lại, và huấn luyện hỏng theo cách rất khó nhận
ra.

**`model.train()` / `model.eval()`:** dropout phải bật khi huấn luyện và tắt khi
đánh giá. Quên `model.eval()` thì kết quả đánh giá bị nhiễu ngẫu nhiên và thấp
hơn thực tế — bạn sẽ nghĩ mô hình dở trong khi nó ổn.

### 8.5. Mất cân bằng lớp

Nếu "ngã" chỉ có 200 mẫu còn "đứng yên" có 800, mô hình sẽ thiên về lớp đông.

Ba cách chữa:

```python
# 1. Trọng số lớp trong hàm mất mát
weights = torch.tensor([1.0, 1.0, 1.0, 1.5, 1.5, 2.0])
criterion = nn.CrossEntropyLoss(weight=weights)

# 2. Lấy mẫu cân bằng (WeightedRandomSampler trong DataLoader)

# 3. Quay thêm dữ liệu cho lớp thiếu  ← luôn là cách tốt nhất
```

Với đồ án này, cách 3 khả thi: bạn kiểm soát việc quay dữ liệu. Hãy cố giữ số
mẫu các lớp gần bằng nhau ngay từ khâu thu thập. Nó tiết kiệm rất nhiều rắc rối
về sau và làm các chỉ số đánh giá dễ diễn giải hơn.

---

## 9. Nếu LSTM không thắng rừng ngẫu nhiên

Đề cương đã nói điều này, và nó đáng nhắc lại vì đây là điểm sư phạm quan trọng
nhất của cả đồ án.

**Chuyện này hoàn toàn có thể xảy ra, và nó không phải thất bại.**

Lý do LSTM có thể thua:

1. **Ít dữ liệu.** LSTM có ~220.000 tham số cần ước lượng từ vài nghìn mẫu.
   Rừng ngẫu nhiên với 30 đặc trưng thủ công thì không.
2. **Đặc trưng thủ công đã mã hóa sẵn tri thức chuyên môn.** Bạn đã *nói cho*
   mô hình biết góc gối quan trọng. LSTM phải tự khám phá điều đó từ tọa độ thô.
3. **Sáu lớp khác nhau rõ rệt.** Bài toán không đủ khó để cần biểu diễn học sâu.
   Học sâu tỏa sáng khi đặc trưng thủ công bất lực — chẳng hạn 60 lớp trong NTU
   RGB+D.
4. **Đặc trưng thống kê của bạn đã bao gồm thông tin thời gian.** `delta_hip_y`
   có dấu chính là thứ mà LSTM lẽ ra phải tự học được.

**Cách viết kết quả này trong báo cáo:**

> "Rừng ngẫu nhiên trên đặc trưng thủ công đạt X%, cao hơn LSTM (Y%). Chúng tôi
> cho rằng nguyên nhân là quy mô dữ liệu: với N mẫu huấn luyện và mô hình LSTM
> có 220.000 tham số, tỉ lệ tham số trên mẫu là quá cao, và đường loss cho thấy
> quá khớp xuất hiện từ epoch thứ Z. Ngoài ra, tập đặc trưng thủ công đã mã hóa
> sẵn tri thức về hình học thân thể — đặc biệt là đặc trưng có dấu về biến thiên
> chiều cao hông — mà LSTM phải tự học từ tọa độ thô. Kết quả này phù hợp với
> nhận định chung rằng lợi thế của học sâu chỉ bộc lộ khi quy mô dữ liệu đủ
> lớn."

Đoạn đó thể hiện sự hiểu biết tốt hơn nhiều so với việc báo cáo "LSTM đạt 94%".
Nhiều đồ án bỏ lỡ đúng bài học này vì họ mặc định học sâu phải thắng và giấu
kết quả ngược lại.

---

## 10. Hướng đi khác — nhắc để có mục Hướng phát triển

### 1D CNN và TCN

Thay vì xử lý tuần tự, dùng tích chập **dọc trục thời gian**. Một bộ lọc kích
thước 5 trượt qua chuỗi 30 bước, phát hiện mẫu hình cục bộ như "hông đi xuống
đều trong 5 frame".

Ưu điểm so với LSTM: **song song hóa được** (không phải chờ bước trước), huấn
luyện nhanh hơn nhiều, và thường ngang hoặc hơn LSTM trên chuỗi ngắn.

Đáng thử nếu còn thời gian ở tuần 8. Nó là một hàng bảng rẻ và có thể cho kết
quả bất ngờ.

### Transformer

Cơ chế **chú ý** cho phép mỗi bước thời gian nhìn thẳng vào mọi bước khác,
không qua trung gian. Rất mạnh, nhưng **cần dữ liệu lớn** — với vài nghìn mẫu
thì gần như chắc chắn thua LSTM. Chỉ nhắc trong hướng phát triển.

### ST-GCN — hướng chính thống của lĩnh vực

Đây là hướng mà nghiên cứu về nhận dạng hành động từ khung xương thực sự đi
theo, và bạn nên nhắc tới nó trong chương Kết luận.

Ý tưởng: LSTM của bạn nhận vector 46 chiều phẳng, **hoàn toàn không biết** rằng
chiều 12 và 13 là hai tọa độ của cùng một khớp, hay rằng khuỷu tay nối với cổ
tay. Nó phải tự học cấu trúc cơ thể từ dữ liệu.

**Mạng tích chập đồ thị không-thời gian** (ST-GCN) đưa cấu trúc đó vào kiến
trúc: khung xương được biểu diễn như một **đồ thị**, mỗi khớp là một đỉnh, mỗi
xương là một cạnh. Tích chập được định nghĩa **trên đồ thị** — mỗi khớp tổng
hợp thông tin từ các khớp lân cận về mặt giải phẫu. Đồng thời có cạnh nối cùng
một khớp qua các frame liên tiếp, cho chiều thời gian.

Kết quả: mô hình biết trước rằng cổ tay liên quan tới khuỷu tay nhiều hơn liên
quan tới mắt cá chân. Đây là **thiên kiến quy nạp** đúng cho bài toán, và nó
làm ST-GCN vượt LSTM đáng kể trên các bộ dữ liệu lớn.

Vì sao ngoài phạm vi đồ án: cần thêm một tầng khái niệm (tích chập trên đồ thị,
ma trận kề, chuẩn hóa Laplace), và lợi thế của nó chỉ bộc lộ với dữ liệu lớn.
Nhưng **nhắc tới nó cho thấy bạn biết lĩnh vực này đi tiếp về đâu** — và đó
chính là mục đích của chương Hướng phát triển.

Bài báo: Yan và cộng sự, *Spatial Temporal Graph Convolutional Networks for
Skeleton-Based Action Recognition*, AAAI 2018. Chỉ cần đọc phần mở đầu.

---

## 11. Ghép vào demo thời gian thực — tuần 9

Lý thuyết gặp thực hành ở đây.

### Hàng đợi

```python
from collections import deque

buffer = deque(maxlen=30)      # tự động bỏ phần tử cũ nhất khi đầy

# mỗi frame:
buffer.append(normalized_frame)

if len(buffer) == 30 and frame_count % 5 == 0:
    window = np.array(buffer)          # (30, 46)
    pred = model(window[None, ...])    # thêm chiều batch → (1, 30, 46)
```

`deque` với `maxlen` là cấu trúc dữ liệu đúng: thêm vào cuối và tự bỏ đầu, chi
phí hằng số.

`frame_count % 5 == 0` là tối ưu hóa từ mục 09 của đề cương: dự đoán mỗi 5
frame thay vì mỗi frame. Cửa sổ chỉ đổi 1/6 nội dung trong 5 frame, nên gần như
không mất gì về độ chính xác mà tiết kiệm 80% chi phí phân loại.

### Làm mượt kết quả

Dự đoán độc lập từng cửa sổ sẽ cho nhãn nhảy loạn — "vẫy tay, vẫy tay, đứng
yên, vẫy tay, vẫy tay". Người dùng thấy chữ nhấp nháy liên tục.

Bỏ phiếu trên vài dự đoán gần nhất:

```python
history = deque(maxlen=5)
history.append(pred)

from collections import Counter
label = Counter(history).most_common(1)[0][0]
```

Có thể nghiêm ngặt hơn: chỉ đổi nhãn khi đa số vượt ngưỡng.

```python
count = Counter(history).most_common(1)[0]
if count[1] >= 4:              # ít nhất 4 trên 5 đồng thuận
    label = count[0]           # còn không thì giữ nhãn cũ
```

**Cái giá là độ trễ.** Bỏ phiếu trên 5 dự đoán cách nhau 5 frame nghĩa là chờ
thêm tới 25 frame ≈ 0,8 giây trước khi nhãn đổi. Với phát hiện ngã, độ trễ này
là chi phí thật cần nêu.

Đây là một đánh đổi kinh điển giữa **độ ổn định** và **độ phản hồi**, và nêu
được nó trong báo cáo là một dấu hiệu tốt.

### Ngưỡng tin cậy

```python
probs = torch.softmax(logits, dim=1)
conf, idx = probs.max(dim=1)

if conf < 0.6:
    label = "khong xac dinh"
```

Hiển thị "không xác định" khi mô hình không chắc thì trung thực hơn là đoán
bừa. Nó cũng xử lý được các trạng thái chuyển tiếp giữa hai hành động, vốn
không thuộc lớp nào.

Nhớ cảnh báo ở mục 4.3: xác suất softmax không được hiệu chuẩn tốt, nên ngưỡng
0.6 là một tham số cần chỉnh bằng thực nghiệm chứ không phải một xác suất thật.

---

## Tự kiểm tra

1. **Vì sao không thể phân biệt "ngồi xuống" với "đứng dậy" nếu chỉ nhìn một
   khung hình duy nhất?** Trả lời không dùng từ "vì cần thông tin thời gian" —
   hãy giải thích cụ thể.

2. Nêu đánh đổi khi chọn `T = 15` so với `T = 45`. Với hành động "ngã" thì `T`
   nào có thể tốt hơn, vì sao?

3. Rừng ngẫu nhiên tạo sự đa dạng giữa các cây bằng hai cơ chế. Nêu cả hai và
   giải thích vì sao cơ chế thứ hai cần thiết.

4. Vì sao mạng nơ-ron cần hàm kích hoạt phi tuyến? Điều gì xảy ra nếu bỏ nó?

5. RNN thường gặp vấn đề gradient tiêu biến. Giải thích nguyên nhân và cách
   LSTM khắc phục.

6. Trong `nn.LSTM(num_layers=2, dropout=0.3)`, dropout được áp ở đâu? Điều gì
   xảy ra nếu đặt `num_layers=1`?

7. Bạn quên `optimizer.zero_grad()` trong vòng lặp. Chương trình có báo lỗi
   không? Hậu quả là gì?

8. LSTM đạt 88%, rừng ngẫu nhiên đạt 91%. Bạn viết gì trong báo cáo? Nêu ít
   nhất ba lý do khả dĩ.

9. Vì sao không dùng LSTM hai chiều cho đồ án này, dù nó thường cho kết quả tốt
   hơn?

<details>
<summary>Đáp án gợi ý</summary>

1. Vì hai hành động đi qua **đúng cùng tập tư thế**, chỉ khác thứ tự. Một ảnh
   người ở tư thế nửa ngồi là bằng chứng ngang nhau cho cả hai giả thuyết — nó
   không chứa thông tin về hướng chuyển động. Thông tin phân biệt nằm trong
   **quan hệ giữa các frame** (hông đang đi lên hay đi xuống), không nằm trong
   bất kỳ frame đơn lẻ nào.

2. `T=15` (0,5s): độ trễ thấp, phản hồi nhanh, ít trộn lẫn hành động; nhưng có
   thể không đủ để thấy trọn một chu kỳ vẫy tay hay một cú ngồi xuống chậm.
   `T=45` (1,5s): nhiều bối cảnh hơn, bao trọn hành động chậm; nhưng độ trễ cao
   và cửa sổ dễ chứa hai hành động khác nhau. Với "ngã" (0,5–1 giây), `T` nhỏ
   có thể tốt hơn vì cửa sổ lớn sẽ pha loãng cú ngã bằng phần đứng yên trước và
   sau đó.

3. (a) **Bagging** — mỗi cây huấn luyện trên một tập con lấy có hoàn lại.
   (b) **Không gian con ngẫu nhiên** — ở mỗi nút chỉ xét một tập con ngẫu nhiên
   các đặc trưng. Cơ chế (b) cần thiết vì nếu có một đặc trưng cực mạnh, mọi cây
   sẽ dùng nó ở nút gốc và trở nên rất giống nhau, làm việc bỏ phiếu mất tác
   dụng.

4. Không có phi tuyến, xếp chồng nhiều lớp tuyến tính vẫn tương đương một phép
   biến đổi tuyến tính duy nhất. Mạng 10 lớp sẽ có cùng khả năng biểu diễn như
   một lớp — không học được ranh giới quyết định phi tuyến.

5. Lan truyền ngược qua `T` bước phải nhân qua cùng ma trận trọng số `T` lần.
   Nếu các giá trị nhỏ hơn 1 thì tích suy giảm theo hàm mũ và tín hiệu học
   không tới được các bước xa. LSTM tạo trạng thái ô `c` được cập nhật bằng phép
   **cộng** (`c_t = f⊙c_{t−1} + i⊙c̃`), chỉ bị nhân với cổng quên trong `[0,1]`
   chứ không qua ma trận trọng số — nên gradient chảy ngược gần như không suy
   giảm khi cổng quên gần 1.

6. Dropout được áp **giữa** các lớp LSTM — tức lên đầu ra của lớp 1 trước khi
   vào lớp 2. Với `num_layers=1` không có chỗ nào để áp, dropout bị bỏ qua và
   PyTorch in cảnh báo.

7. Không báo lỗi. PyTorch cộng dồn gradient thay vì ghi đè, nên gradient của
   mọi batch cộng lại và bước cập nhật trở nên quá lớn và sai hướng. Triệu
   chứng: loss không giảm, nhảy loạn, hoặc thành `nan`. Đây là lỗi im lặng điển
   hình.

8. Ba lý do: (a) LSTM có ~220.000 tham số cần ước lượng từ vài nghìn mẫu — tỉ
   lệ tham số/mẫu quá cao, dẫn tới quá khớp (kiểm chứng bằng đường loss).
   (b) Đặc trưng thủ công đã mã hóa sẵn tri thức chuyên môn (góc khớp,
   `delta_hip_y` có dấu) mà LSTM phải tự học. (c) Sáu lớp khác nhau rõ rệt về
   hình học nên bài toán không đủ khó để cần biểu diễn học sâu. Nên viết kết quả
   này ra như một kết luận có ý nghĩa, kèm bằng chứng từ đường loss.

9. LSTM hai chiều đọc chuỗi cả xuôi lẫn ngược, nên nó cần biết toàn bộ chuỗi —
   bao gồm các frame trong tương lai — trước khi dự đoán. Trong hệ thống thời
   gian thực, frame tương lai chưa tồn tại. Báo cáo kết quả của mô hình hai
   chiều cho một hệ thống "thời gian thực" là sai sót phương pháp.

</details>

---

## Đưa gì vào báo cáo

**Mục 2.4 Mô hình chuỗi thời gian**, khoảng 4–5 trang:

- Bài toán phân loại chuỗi; cơ chế cửa sổ trượt; các tham số `T`, `S`; tính
  nhân quả
- Cây quyết định và rừng ngẫu nhiên: bagging, không gian con ngẫu nhiên, ưu
  điểm với dữ liệu ít
- Mạng nơ-ron: nơ-ron, hàm kích hoạt, softmax, cross-entropy, gradient descent —
  viết ngắn gọn, đây là nền chứ không phải trọng tâm
- RNN: trạng thái ẩn, chia sẻ tham số theo thời gian, vấn đề gradient tiêu biến
- **LSTM: ba cổng và trạng thái ô.** Đây là mục trung tâm. Kèm sơ đồ một ô LSTM
- Nhắc GRU, 1D CNN, và ST-GCN cho phần Hướng phát triển

**Chương 5 (Thí nghiệm):**

- Số tham số của LSTM và số mẫu huấn luyện — đặt cạnh nhau
- Đường loss train và val trên cùng biểu đồ, đánh dấu điểm dừng sớm
- Bảng khảo sát `T` = 15/30/45
- Bảng so sánh rừng ngẫu nhiên và LSTM
- Biểu đồ xếp hạng độ quan trọng đặc trưng
- Nếu có thời gian: GRU, `hidden=64`, một lớp thay vì hai — mỗi cái một hàng
  bảng

**Hình nên vẽ:**

1. **Sơ đồ cửa sổ trượt** — đã có sẵn trong đề cương HTML, vẽ lại cho báo cáo
2. **Sơ đồ một ô LSTM** với ba cổng, có chú thích tiếng Việt
3. **Đường loss train/val** — hình chứng minh bạn có kiểm soát quá khớp

Hình 2 dễ vẽ lại từ bài blog của Christopher Olah. Đừng chép nguyên hình; vẽ lại
với chú thích của bạn thì vừa tránh vấn đề bản quyền vừa chứng tỏ bạn hiểu.
