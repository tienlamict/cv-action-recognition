# Tầng 5 — Đánh giá bài toán phân loại

> **Câu hỏi mở đầu:** Mô hình của bạn đạt 99%. Vì sao đó gần như chắc chắn là
> một con số giả?

Tầng này không khó về toán. Nhưng nó là tầng **dễ làm sai nhất**, và làm sai ở
đây khiến mọi thứ phía trước trở nên vô nghĩa — bạn không biết hệ thống của
mình thật sự tốt hay dở.

Nó cũng là tầng mà hội đồng chấm sẽ soi kỹ nhất, vì đánh giá sai là dấu hiệu rõ
nhất của một đồ án làm ẩu.

---

## 1. Vì sao một con số độ chính xác không đủ

### Định nghĩa

```
Độ chính xác = số dự đoán đúng / tổng số dự đoán
```

Đơn giản, dễ hiểu, và **gần như luôn không đủ để kết luận gì**.

### Vấn đề 1: nó che giấu lớp nào sai

Giả sử hệ thống của bạn đạt 90% trên 600 mẫu, mỗi lớp 100 mẫu. Nghe tốt. Nhưng
60 mẫu sai đó nằm ở đâu?

**Kịch bản A** — sai rải đều:

```
mỗi lớp sai 10 mẫu  →  mọi lớp đều 90%
```

**Kịch bản B** — sai dồn một chỗ:

```
5 lớp đầu:  đúng 100/100   →  100%
lớp "ngã":  đúng 40/100    →  40%
```

**Cả hai đều cho độ chính xác tổng 90%.** Nhưng kịch bản B là một hệ thống phát
hiện ngã **hoàn toàn vô dụng** — nó bỏ sót 6 trên 10 cú ngã. Con số tổng hợp
che giấu điều đó hoàn toàn.

### Vấn đề 2: mất cân bằng lớp làm nó vô nghĩa

Nếu tập kiểm thử có 90% mẫu là "đứng yên", thì một mô hình luôn luôn đoán "đứng
yên" — không cần học gì cả — cũng đạt 90%.

Vì thế **luôn phải nêu đường cơ sở** để người đọc biết con số của bạn có ý
nghĩa không:

- **Đoán ngẫu nhiên đều:** 1/6 ≈ **16,7%**
- **Luôn đoán lớp đông nhất:** bằng tỉ lệ lớp đó trong tập kiểm thử

Nếu bạn đạt 91% trong khi đường cơ sở đa số là 88%, thì mô hình của bạn gần như
không học được gì. Nếu đường cơ sở là 17% thì 91% là kết quả thật.

Một dòng trong báo cáo: "Đường cơ sở đoán ngẫu nhiên là 16,7%; đường cơ sở lớp
đa số là X%." Rẻ và tăng độ tin cậy đáng kể.

---

## 2. Ma trận nhầm lẫn — hình quan trọng nhất của báo cáo

### Cách đọc

Bảng `C × C`. **Hàng là nhãn thật, cột là nhãn dự đoán.** Ô `(i, j)` là số mẫu
thật thuộc lớp `i` nhưng bị đoán thành lớp `j`.

```
                    ĐOÁN LÀ →
             đứng  đibộ  vẫy  ngồi  dậy   ngã
THẬT   đứng   95     2     3     0     0     0
LÀ     đibộ    4    88     5     1     2     0
↓      vẫy     6     3    89     0     2     0
       ngồi    1     0     0    72     9    18
       dậy     0     1     1    11    85     2
       ngã     0     0     0    14     1    85
```

Đường chéo là số đúng. Mọi ô ngoài đường chéo là một lỗi cụ thể, và **mỗi lỗi
kể một câu chuyện**.

### Chuẩn hóa theo hàng

Nếu các lớp có số mẫu khác nhau, con số tuyệt đối khó so sánh. Chia mỗi hàng
cho tổng của nó để được tỉ lệ:

```python
cm = confusion_matrix(y_true, y_pred)
cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
```

Bây giờ mỗi hàng cộng lại bằng 1, và đường chéo chính là **recall của từng
lớp**.

### Đọc ma trận trên là đọc gì

Đây là phần quan trọng nhất của mục này. Từ ma trận ví dụ, ta rút ra:

**Phát hiện 1 — Ba lớp tĩnh tách tốt khỏi ba lớp chuyển tiếp.** Góc trên phải
và góc dưới trái gần như bằng 0. Hệ thống không bao giờ nhầm "đi bộ tại chỗ"
với "ngã". Hợp lý: chúng khác nhau ở mọi đặc trưng.

**Phát hiện 2 — "ngồi xuống" bị nhầm thành "ngã" 18 lần.** Đây là lỗi nghiêm
trọng nhất và cũng thú vị nhất.

*Vì sao?* Hai hành động chia sẻ phần lớn quỹ đạo: hông đi xuống, thân cúi về
trước, gối gập. Điểm khác biệt chỉ nằm ở **tốc độ** và **tư thế cuối** (ngồi
thì thân vẫn thẳng đứng, ngã thì thân nằm ngang).

*Suy ra gì?* Đặc trưng phân biệt tốc độ và góc nghiêng thân chưa đủ mạnh, hoặc
dữ liệu "ngồi xuống" của bạn có những lần diễn quá nhanh nên trông giống ngã.

**Phát hiện 3 — "ngã" bị nhầm thành "ngồi xuống" 14 lần**, tức nhầm lẫn hai
chiều. Điều này khẳng định phát hiện 2: không phải mô hình thiên về một lớp, mà
là hai lớp thực sự chồng lấn trong không gian đặc trưng.

**Phát hiện 4 — "ngồi xuống" và "đứng dậy" lẫn nhau 9 và 11 lần.** Đúng cặp mà
tầng 3 dự đoán là khó. Kiểm tra ngay: đặc trưng có dấu `delta_hip_y` đã được
đưa vào chưa? Nếu rồi mà vẫn lẫn, có thể cửa sổ 30 frame chưa bao trọn hành
động, nên nó chỉ thấy phần giữa nơi hai hành động giống nhau nhất.

### Vì sao đây là chỗ nghiên cứu thật sự diễn ra

Một con số "90%" không cho bạn hành động nào tiếp theo. Ma trận nhầm lẫn cho
bạn một danh sách vấn đề cụ thể và một giả thuyết cho mỗi vấn đề.

Quy trình cải tiến:

```
1. Nhìn ma trận, tìm ô ngoài đường chéo lớn nhất
2. Đặt giả thuyết: hai lớp này chia sẻ đặc điểm gì?
3. Thiết kế một đặc trưng hoặc thay đổi tách chúng ra
4. Chạy lại, xem ô đó có nhỏ đi không
5. Quay về bước 1
```

**Câu này nên có trong báo cáo, gần như nguyên văn:**

> "Chúng tôi phát hiện 'ngồi xuống' hay bị nhầm với 'ngã' vì hai hành động chia
> sẻ quỹ đạo hông đi xuống và chỉ khác nhau ở tốc độ và tư thế cuối."

Một câu như thế chứng minh sự hiểu biết tốt hơn bất kỳ con số độ chính xác nào,
vì nó cho thấy bạn đã nhìn vào **hành vi** của hệ thống chứ không chỉ đọc chỉ
số tổng hợp.

---

## 3. Precision, recall và F1

### Định nghĩa cho một lớp

Xét lớp "ngã". Bốn khả năng cho mỗi mẫu:

| | Thật là ngã | Thật không phải ngã |
|---|---|---|
| **Đoán là ngã** | TP (đúng dương) | FP (dương giả — báo động nhầm) |
| **Đoán không ngã** | FN (âm giả — bỏ sót) | TN (đúng âm) |

**Precision (độ chính xác của dự đoán dương):**

```
Precision = TP / (TP + FP)
```

*"Trong tất cả những lần hệ thống kêu 'ngã', bao nhiêu lần đúng?"*

Precision thấp = báo động nhầm nhiều. Với hệ thống giám sát người già, precision
thấp làm người chăm sóc mệt mỏi và cuối cùng bỏ qua cảnh báo.

**Recall (độ bao phủ):**

```
Recall = TP / (TP + FN)
```

*"Trong tất cả những cú ngã thật, hệ thống bắt được bao nhiêu?"*

Recall thấp = bỏ sót. Với phát hiện ngã, đây là loại lỗi **nguy hiểm** — một
người già ngã và không ai được báo.

**F1 — trung bình điều hòa:**

```
F1 = 2 · (P · R) / (P + R)
```

Vì sao trung bình điều hòa chứ không phải trung bình cộng? Vì nó **phạt sự mất
cân bằng**:

```
P = 1.0, R = 0.0:   trung bình cộng = 0.50   nhưng   F1 = 0.00
P = 0.5, R = 0.5:   trung bình cộng = 0.50   và      F1 = 0.50
```

Một mô hình có precision hoàn hảo nhưng recall bằng 0 (nó chỉ báo "ngã" đúng
một lần trong cả tập, và lần đó đúng) là vô dụng. F1 phản ánh điều đó, trung
bình cộng thì không.

### Đánh đổi precision và recall

Hai chỉ số này thường đối nghịch. Hạ ngưỡng tin cậy để báo "ngã" dễ hơn thì bạn
bắt được nhiều cú ngã hơn (recall tăng) nhưng cũng báo nhầm nhiều hơn
(precision giảm).

Với ứng dụng phát hiện ngã, **recall quan trọng hơn precision**. Một báo động
nhầm gây phiền; một cú ngã bị bỏ sót có thể gây hậu quả nghiêm trọng.

Cách hiện thực hóa lựa chọn đó:

```python
probs = model.predict_proba(X)
# Hạ ngưỡng cho lớp "ngã" để tăng recall
pred_fall = probs[:, FALL_IDX] > 0.35     # thay vì 0.5
```

**Một bảng precision–recall của lớp "ngã" ở các ngưỡng khác nhau là nội dung
rất tốt cho chương thí nghiệm.** Nó cho thấy bạn hiểu rằng chọn ngưỡng là một
quyết định ứng dụng, không phải một hằng số mặc định.

| Ngưỡng | Precision | Recall | F1 |
|---|---|---|---|
| 0.30 | 0.71 | 0.94 | 0.81 |
| 0.50 | 0.85 | 0.85 | 0.85 |
| 0.70 | 0.93 | 0.68 | 0.79 |

### Macro, micro và weighted

Với 6 lớp, ta có 6 giá trị precision. Gộp lại thế nào?

| Cách | Công thức | Khi nào dùng |
|---|---|---|
| **Macro** | Trung bình cộng của 6 giá trị | Mọi lớp quan trọng như nhau. **Dùng cái này** |
| **Weighted** | Trung bình có trọng số theo số mẫu | Khi lớp đông quan trọng hơn |
| **Micro** | Gộp mọi TP/FP/FN rồi tính một lần | Với phân loại đơn nhãn, bằng đúng độ chính xác |

**Macro-F1 là chỉ số tóm tắt tốt nhất cho đồ án này**, vì nó không cho phép các
lớp dễ (đứng yên) che lấp các lớp khó (ngã).

Chú ý: nếu bạn báo cáo micro-F1 cho bài toán phân loại đơn nhãn, nó bằng đúng
độ chính xác — bạn đang báo cáo cùng một con số hai lần dưới hai cái tên. Một
số đồ án mắc lỗi này.

### Code

```python
from sklearn.metrics import classification_report, confusion_matrix

names = ["dung yen", "di bo", "vay tay", "ngoi xuong", "dung day", "nga"]
print(classification_report(y_true, y_pred, target_names=names, digits=3))
print(confusion_matrix(y_true, y_pred))
```

`classification_report` cho precision, recall, F1 và support (số mẫu) cho từng
lớp, cộng với các trung bình macro và weighted. **Bảng này nên đưa nguyên vào
báo cáo.**

---

## 4. Rò rỉ dữ liệu — cạm bẫy lớn nhất

Đây là mục quan trọng nhất của tầng này. Đọc kỹ.

### Định nghĩa

**Rò rỉ dữ liệu** (*data leakage*): thông tin từ tập kiểm thử lọt vào quá trình
huấn luyện, làm kết quả đánh giá cao hơn thực tế.

Triệu chứng: độ chính xác cao đến mức đáng ngờ (97–99%) trên một bài toán khó,
với dữ liệu ít.

**Nguyên tắc phát hiện:** nếu kết quả tốt hơn bạn kỳ vọng một cách khó hiểu, thì
gần như chắc chắn có rò rỉ. Trong học máy ứng dụng, may mắn hiếm hơn lỗi nhiều.

### Dạng 1: chia theo cửa sổ — dạng nguy hiểm nhất ở đồ án này

```python
# SAI — đừng làm thế này
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
```

Vì sao sai: với bước trượt `S = 1`, các cửa sổ liên tiếp **chồng lấn 29/30
frame**. Cửa sổ bắt đầu ở frame 100 và cửa sổ bắt đầu ở frame 101 gần như giống
hệt nhau.

Chia ngẫu nhiên thì cửa sổ 100 vào tập huấn luyện, cửa sổ 101 vào tập kiểm thử.
Mô hình đã thấy gần đúng mẫu kiểm thử đó rồi. **Nó chỉ cần nhớ, không cần học.**

Kết quả điển hình: 99%. Hoàn toàn giả.

### Dạng 2: chia theo đoạn quay

Khá hơn — mỗi lần diễn nằm trọn ở một tập. Nhưng vẫn rò rỉ: cùng một người,
cùng buổi quay, cùng quần áo, cùng góc camera, cùng thói quen diễn.

Mô hình có thể học "cách người này ngồi xuống" thay vì "ngồi xuống trông thế
nào".

### Dạng 3 (đúng): chia theo người

```json
{"train": ["p01", "p02", "p03"], "test": ["p04", "p05"]}
```

**Toàn bộ video của một người chỉ nằm ở một tập.** Đây là giao thức
**cross-subject**, chuẩn trong lĩnh vực nhận dạng hành động — NTU RGB+D và
các bộ dữ liệu lớn khác đều dùng nó.

Nó trả lời đúng câu hỏi mà người dùng quan tâm: **hệ thống có hoạt động với
người nó chưa từng thấy không?** Đây là câu hỏi thật, vì khi triển khai, hệ
thống luôn gặp người mới.

Kết quả sẽ **thấp hơn nhiều**. Đó là điều tốt. Nếu 99% tụt xuống 82% sau khi
chia lại, thì 82% mới là con số thật — và con số thật mới đáng đưa vào báo cáo.

### Dạng 4: rò rỉ qua chuẩn hóa

Tinh vi hơn và ít người biết:

```python
# SAI
scaler = StandardScaler().fit(X)          # tính trung bình trên TOÀN BỘ dữ liệu
X_train, X_test = split(scaler.transform(X))

# ĐÚNG
X_train, X_test = split(X)
scaler = StandardScaler().fit(X_train)    # chỉ từ tập huấn luyện
X_test = scaler.transform(X_test)
```

Trung bình và độ lệch chuẩn tính trên toàn bộ dữ liệu đã chứa thông tin của tập
kiểm thử. Rò rỉ nhỏ, nhưng là rò rỉ.

**Đồ án này may mắn ít bị:** phép chuẩn hóa của bạn dùng thống kê **của riêng
từng frame** (hông và vai của chính frame đó), không dùng thống kê toàn tập.
Nhưng nếu bạn thêm một bước `StandardScaler` trên vector đặc trưng trước khi đưa
vào rừng ngẫu nhiên, hãy fit nó chỉ trên tập huấn luyện.

### Dạng 5: rò rỉ qua tăng cường dữ liệu

```python
# SAI
X_aug = augment(X)                    # tạo bản lật, thêm nhiễu
split(X_aug)                          # rồi mới chia

# ĐÚNG
X_train, X_test = split(X)
X_train = augment(X_train)            # chỉ tăng cường tập huấn luyện
```

Nếu tăng cường trước khi chia, một mẫu gốc và bản lật của nó rơi vào hai tập
khác nhau. Mô hình học mẫu gốc rồi được kiểm tra trên chính nó, chỉ lật ngang.

### Dạng 6: rò rỉ qua chọn siêu tham số

Bạn thử 20 cấu hình LSTM, báo cáo cấu hình tốt nhất trên **tập kiểm thử**. Con
số đó đã bị thổi phồng — bạn đã dùng tập kiểm thử 20 lần để ra quyết định.

Cách đúng: dùng tập kiểm định để chọn, tập kiểm thử chỉ chạy **một lần** ở cuối
cùng.

Với dữ liệu ít, khả thi hơn là dùng **kiểm định chéo bỏ một người**
(*leave-one-subject-out*, LOSO):

```
Vòng 1: huấn luyện p02–p05, kiểm thử p01
Vòng 2: huấn luyện p01,p03–p05, kiểm thử p02
...
Vòng 5: huấn luyện p01–p04, kiểm thử p05

Báo cáo: trung bình ± độ lệch chuẩn của 5 vòng
```

Ưu điểm: dùng được mọi dữ liệu, và **độ lệch chuẩn cho biết kết quả ổn định tới
đâu**. Nếu độ chính xác dao động từ 68% tới 91% giữa các vòng, đó là thông tin
quan trọng — nó nghĩa là hệ thống hoạt động rất khác nhau tùy người.

Với 5 người và mô hình huấn luyện trong vài giây tới vài phút, LOSO hoàn toàn
khả thi và làm chương thí nghiệm của bạn mạnh hơn hẳn.

### Bảng tóm tắt cách chia

| Cách chia | Trả lời câu hỏi gì | Kết quả điển hình |
|---|---|---|
| Ngẫu nhiên theo cửa sổ | Không câu nào có ý nghĩa | 97–99% (giả) |
| Theo đoạn quay | Có tổng quát hóa sang lần diễn mới không? | 88–95% |
| **Theo người (cross-subject)** | **Có tổng quát hóa sang người mới không?** | **75–88%** |
| Theo góc camera (cross-view) | Có tổng quát hóa sang góc đặt mới không? | Thấp hơn nữa |

Báo cáo **ít nhất** kết quả cross-subject. Nếu quay được thêm một góc camera
khác, thêm cross-view — nó cho thấy bạn kiểm tra một chiều tổng quát hóa nữa mà
ít đồ án nào làm.

### Một thí nghiệm rất đáng làm

Báo cáo **cả hai** con số cạnh nhau:

| Cách chia | Độ chính xác |
|---|---|
| Ngẫu nhiên theo cửa sổ | 98,7% |
| Theo người (cross-subject) | 82,3% |

Rồi giải thích khoảng cách. Đây là một trong những nội dung có giá trị nhất bạn
có thể đưa vào báo cáo, vì:

- Nó chứng minh bạn **hiểu** rò rỉ dữ liệu, không chỉ tránh nó
- Nó cho thấy bạn **trung thực** — bạn nêu ra con số đẹp hơn và giải thích vì
  sao không dùng nó
- Nó là một kết quả thực nghiệm thật từ dữ liệu của bạn

Hội đồng đánh giá cao sự trung thực này hơn nhiều so với một con số cao không
có bối cảnh.

---

## 5. Đánh giá ở ba mức

Có ba câu hỏi khác nhau, và chúng cần ba cách đo khác nhau. Nhiều đồ án chỉ đo
mức đầu tiên và nghĩ thế là đủ.

### Mức 1 — Cửa sổ

*"Cho một cửa sổ 30 frame, mô hình đoán đúng nhãn không?"*

Đây là cái bạn đo bằng `classification_report`. Dễ nhất, và là cái duy nhất
nhiều người báo cáo.

### Mức 2 — Đoạn video

*"Cho một đoạn video 4 giây của một hành động, hệ thống có nhận đúng không?"*

Gần với cách người dùng cảm nhận hơn. Cách tính: lấy nhãn xuất hiện nhiều nhất
trong tất cả cửa sổ của đoạn đó.

```python
from collections import Counter
seg_pred = Counter(window_preds).most_common(1)[0][0]
```

Kết quả thường **cao hơn** mức 1, vì bỏ phiếu trên nhiều cửa sổ triệt tiêu các
lỗi lẻ tẻ. Báo cáo cả hai cho thấy bạn phân biệt được chúng.

### Mức 3 — Thời gian thực

*"Trong một video liên tục, hệ thống phản ứng nhanh và ổn định tới đâu?"*

Hai đại lượng cần đo:

**Độ trễ nhận dạng:** từ lúc hành động thật sự bắt đầu tới lúc nhãn đúng xuất
hiện ổn định trên màn hình.

Cách đo thủ công, hoàn toàn khả thi:

```
1. Quay một video demo, có tính năng ghi màn hình
2. Xem lại từng frame, ghi frame số mấy hành động bắt đầu
3. Ghi frame số mấy nhãn đúng xuất hiện và giữ ổn định
4. Độ trễ = hiệu hai số, chia cho FPS → ra giây
5. Lặp lại 10 lần cho mỗi hành động, báo cáo trung bình
```

Độ trễ có ba thành phần cộng dồn, và nên phân tích rõ:

```
độ trễ tổng = độ trễ cửa sổ  +  độ trễ dự đoán  +  độ trễ làm mượt

  độ trễ cửa sổ:    phải chờ đủ 30 frame  →  tới 1,0 giây
  độ trễ dự đoán:   chỉ dự đoán mỗi 5 frame →  tới 0,17 giây
  độ trễ làm mượt:  bỏ phiếu 5 dự đoán    →  tới 0,83 giây
                                   tổng   ≈  tới 2,0 giây
```

**Phân tích này rất đáng đưa vào báo cáo.** Nó cho thấy bạn hiểu rằng mỗi lựa
chọn thiết kế đều có chi phí, và bạn định lượng được chi phí đó. Với ứng dụng
phát hiện ngã, độ trễ 2 giây là một giới hạn thật cần thảo luận.

**Độ ổn định nhãn:** số lần nhãn đổi trong một đoạn mà hành động không đổi. Càng
thấp càng tốt. Đây là cách định lượng hiệu quả của bước làm mượt:

| Cấu hình | Số lần nhãn đổi / 10 giây |
|---|---|
| Không làm mượt | 23 |
| Bỏ phiếu 3 | 7 |
| Bỏ phiếu 5 | 2 |

---

## 6. Đo tốc độ và tài nguyên

Tên đề tài có chữ "thời gian thực", nên **bắt buộc** phải có số liệu tốc độ.

### FPS — đo đúng cách

Bốn nguyên tắc:

1. **Bỏ qua 2–3 giây đầu.** Lần gọi MediaPipe đầu tiên nạp mô hình, chậm hơn
   nhiều lần. Tính vào trung bình sẽ làm kết quả sai lệch.
2. **Đo trên ít nhất 30 giây** để có mẫu đủ lớn.
3. **Báo cả trung bình và phân vị.** Trung bình 28 FPS nghe tốt, nhưng nếu phân
   vị 5% là 12 FPS thì hệ thống giật rõ rệt lúc dùng thật.
4. **Nêu cấu hình phần cứng.** "30 FPS" vô nghĩa nếu không biết CPU gì.

```python
import numpy as np
ts = np.array(frame_times[90:])      # bỏ 3 giây đầu ở 30 FPS
print(f"FPS trung binh: {1/ts.mean():.1f}")
print(f"FPS phan vi 5%: {1/np.percentile(ts, 95):.1f}")
```

### Bảng cần có

| Cấu hình | FPS TB | FPS p5 | Macro-F1 |
|---|---|---|---|
| MediaPipe lite + rừng ngẫu nhiên | 29,4 | 24,1 | 0,84 |
| MediaPipe lite + LSTM | 28,1 | 22,7 | 0,81 |
| MediaPipe full + rừng ngẫu nhiên | 21,3 | 17,2 | 0,86 |
| MediaPipe heavy + rừng ngẫu nhiên | 12,8 | 9,4 | 0,87 |

*Máy đo: Intel Core i5-1135G7, 16 GB RAM, không GPU, Windows 11.*

Bảng này là **hình ảnh của một đồ án kỹ thuật nghiêm túc**. Nó cho thấy hai
chiều đánh đổi cùng lúc và cho phép người đọc tự rút kết luận: heavy chỉ hơn
lite 3 điểm F1 nhưng chậm hơn hơn hai lần, nên lite là lựa chọn đúng cho thời
gian thực.

### Phân rã thời gian

Từ tầng 1 mục 6. Nêu MediaPipe chiếm bao nhiêu phần trăm thời gian, phân loại
chiếm bao nhiêu. Kết luận điển hình: **chi phí gần như hoàn toàn nằm ở ước lượng
tư thế, còn phân loại gần như miễn phí** — điều này biện minh cho việc chọn mô
hình phân loại dựa trên độ chính xác chứ không phải tốc độ.

---

## 7. Báo cáo trung thực

Vài quy tắc phân biệt một đồ án nghiêm túc với một đồ án làm cho xong.

### Nêu độ biến thiên

Một lần chạy không nói lên gì. Mạng nơ-ron khởi tạo ngẫu nhiên, rừng ngẫu nhiên
lấy mẫu ngẫu nhiên — chạy lại cho kết quả khác.

```python
accs = []
for seed in [0, 1, 2, 3, 4]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    accs.append(train_and_evaluate())

print(f"{np.mean(accs):.3f} ± {np.std(accs):.3f}")
```

Báo cáo `0.834 ± 0.021` thay vì `0.851` (lần chạy may mắn nhất). Nếu độ lệch
chuẩn là 0.02 thì chênh lệch 1 điểm giữa hai mô hình **không có ý nghĩa** — và
bạn phải nói ra điều đó thay vì tuyên bố mô hình A thắng mô hình B.

### Cố định seed và ghi lại

```python
SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
```

Để người khác chạy lại được. Ghi seed vào README.

### Báo cáo cả kết quả xấu

Nếu LSTM thua rừng ngẫu nhiên, viết ra và giải thích. Nếu một đặc trưng bạn kỳ
vọng lại vô dụng, viết ra. Nếu một lớp có recall 60%, viết ra.

Ẩn kết quả xấu là hành vi mà người chấm có kinh nghiệm nhận ra ngay — thường
qua việc bảng thí nghiệm chỉ có những hàng đẹp một cách đáng ngờ.

### Nêu giới hạn rõ ràng

Danh sách cho đồ án này, dùng làm dàn ý cho một mục trong chương Thảo luận:

- Chỉ 3–5 người diễn, đều là người trẻ, khỏe mạnh, chiều cao trong khoảng hẹp
- Chỉ một góc camera cho phần lớn dữ liệu
- Chỉ một môi trường (trong nhà, đủ sáng)
- Hành động ngã là **diễn**, không phải ngã thật — quỹ đạo có thể khác cú ngã
  thật đáng kể
- Chỉ một người trong khung hình
- Biểu diễn khung xương không phân biệt được các hành động khác nhau ở vật thể
  cầm trong tay
- Độ trễ nhận dạng tới ~2 giây, có thể quá chậm cho một số ứng dụng thật

Nêu giới hạn **không làm giảm điểm**. Nó làm tăng, vì nó cho thấy bạn biết
chính xác mình đã chứng minh được gì và chưa chứng minh được gì.

---

## 8. Danh sách kiểm tra trước khi báo cáo kết quả

Đi qua từng dòng trước khi viết bất kỳ con số nào vào báo cáo:

- [ ] Tập kiểm thử chia **theo người**, không theo cửa sổ hay đoạn quay
- [ ] Không có người nào xuất hiện ở cả tập huấn luyện lẫn kiểm thử
- [ ] Tăng cường dữ liệu chỉ áp dụng **sau khi chia** và chỉ cho tập huấn luyện
- [ ] Siêu tham số chọn trên tập kiểm định, không phải tập kiểm thử
- [ ] Tập kiểm thử chỉ được chạy ở cuối cùng
- [ ] Có nêu đường cơ sở (ngẫu nhiên 16,7% và lớp đa số)
- [ ] Có ma trận nhầm lẫn, và có **phân tích bằng lời** ít nhất hai ô ngoài
      đường chéo
- [ ] Có precision, recall, F1 **cho từng lớp**, không chỉ trung bình
- [ ] Có macro-F1, không chỉ độ chính xác
- [ ] Có FPS đo thật, kèm cấu hình máy
- [ ] Có độ trễ nhận dạng đo thật
- [ ] Có kết quả nhiều lần chạy với độ lệch chuẩn
- [ ] Có mục giới hạn trung thực
- [ ] Nếu LSTM thua rừng ngẫu nhiên, có giải thích thay vì giấu

---

## Tự kiểm tra

1. **Vì sao gom tất cả frame lại rồi chia ngẫu nhiên 80/20 sẽ cho kết quả cao
   giả tạo?** Giải thích cơ chế cụ thể.

2. Hai mô hình cùng đạt 90% trên 600 mẫu chia đều 6 lớp. Một mô hình sai đều,
   một mô hình sai dồn vào lớp "ngã". Vì sao độ chính xác không phân biệt được
   chúng, và chỉ số nào phân biệt được?

3. Với hệ thống phát hiện ngã cho người già, precision hay recall quan trọng
   hơn? Giải thích bằng hậu quả cụ thể của từng loại lỗi.

4. Vì sao F1 dùng trung bình điều hòa thay vì trung bình cộng? Cho một ví dụ số
   minh họa.

5. Bạn chuẩn hóa đặc trưng bằng `StandardScaler().fit(X)` trên toàn bộ dữ liệu
   rồi mới chia tập. Đây có phải rò rỉ không? Cách sửa?

6. Kết quả chia theo cửa sổ là 98,7%, chia theo người là 82,3%. Bạn báo cáo con
   số nào, và bạn viết gì về con số kia?

7. Nêu ba thành phần của độ trễ nhận dạng trong hệ thống của bạn và ước lượng
   mỗi thành phần.

8. Bạn chạy mô hình 5 lần với seed khác nhau, được `[0.81, 0.84, 0.79, 0.86,
   0.83]`. Mô hình khác cho `[0.85, 0.82, 0.87, 0.84, 0.83]`. Kết luận gì?

<details>
<summary>Đáp án gợi ý</summary>

1. Các cửa sổ liên tiếp chồng lấn tới 29/30 frame nên gần như giống hệt nhau.
   Chia ngẫu nhiên làm cửa sổ 100 vào tập huấn luyện và cửa sổ 101 vào tập kiểm
   thử — mô hình đã thấy gần đúng mẫu kiểm thử rồi, nên nó chỉ cần **nhớ** chứ
   không cần **học** một quy luật tổng quát.

2. Độ chính xác là một con số tổng hợp, cộng gộp mọi lỗi bất kể chúng ở đâu.
   Ma trận nhầm lẫn và recall theo từng lớp phân biệt được: kịch bản B sẽ lộ ra
   recall 40% cho lớp "ngã" trong khi các lớp khác 100%. Macro-F1 cũng phản ánh
   được vì nó trung bình đều qua các lớp.

3. **Recall.** Bỏ sót một cú ngã (FN) nghĩa là một người già nằm dưới sàn mà
   không ai được báo — hậu quả có thể nghiêm trọng. Báo động nhầm (FP) chỉ gây
   phiền cho người chăm sóc. Nên hạ ngưỡng để tăng recall, chấp nhận precision
   thấp hơn.

4. Vì trung bình điều hòa phạt sự mất cân bằng. Với `P=1.0, R=0.0`: trung bình
   cộng cho 0.50, nhưng F1 cho 0.00 — phản ánh đúng rằng mô hình vô dụng. Trung
   bình cộng sẽ cho một mô hình chỉ báo dương đúng một lần trong cả tập điểm số
   giống như một mô hình cân bằng.

5. **Có, là rò rỉ.** Trung bình và độ lệch chuẩn tính trên toàn bộ dữ liệu đã
   chứa thông tin của tập kiểm thử. Sửa: chia tập trước, `fit` scaler chỉ trên
   `X_train`, rồi `transform` cả hai tập bằng scaler đó.

6. Báo cáo **82,3%** làm kết quả chính. Nêu 98,7% trong một bảng riêng kèm giải
   thích rằng chia theo cửa sổ gây rò rỉ do các cửa sổ chồng lấn, nên con số đó
   không phản ánh khả năng tổng quát hóa. Trình bày cả hai cạnh nhau chứng minh
   bạn hiểu rò rỉ chứ không chỉ tránh nó.

7. (a) **Độ trễ cửa sổ** — chờ đủ 30 frame ≈ 1,0 giây. (b) **Độ trễ dự đoán** —
   chỉ dự đoán mỗi 5 frame ≈ tới 0,17 giây. (c) **Độ trễ làm mượt** — bỏ phiếu
   trên 5 dự đoán cách nhau 5 frame ≈ tới 0,83 giây. Tổng tới khoảng 2 giây.

8. Mô hình A: `0.826 ± 0.024`. Mô hình B: `0.842 ± 0.017`. Chênh lệch trung bình
   1,6 điểm nhỏ hơn độ lệch chuẩn, và hai khoảng chồng lấn nhiều. **Kết luận:
   không đủ bằng chứng để nói mô hình B tốt hơn.** Nên viết đúng như vậy thay vì
   tuyên bố B thắng.

</details>

---

## Đưa gì vào báo cáo

**Mục 2.5 Phương pháp đánh giá** trong chương Cơ sở lý thuyết, khoảng 2–3 trang:

- Vì sao độ chính xác một mình không đủ; hai vấn đề ở mục 1
- Ma trận nhầm lẫn: cách đọc, chuẩn hóa theo hàng
- Precision, recall, F1; ý nghĩa của từng loại lỗi trong ngữ cảnh phát hiện
  ngã; macro so với weighted
- Rò rỉ dữ liệu và giao thức chia tập cross-subject

**Chương 5 (Thí nghiệm)** — đây là nơi mục này phát huy:

- Bảng `classification_report` đầy đủ
- **Ma trận nhầm lẫn dạng hình nhiệt** — hình quan trọng nhất
- Bảng so sánh chia theo cửa sổ và chia theo người
- Bảng khảo sát `T` = 15/30/45
- Bảng so sánh ba biến thể MediaPipe theo cặp F1–FPS
- Bảng precision–recall của lớp "ngã" ở các ngưỡng khác nhau
- Kết quả nhiều lần chạy với độ lệch chuẩn
- Độ trễ nhận dạng đo thật

**Chương 6 (Thảo luận):**

- Phân tích **bằng lời** ít nhất hai ô ngoài đường chéo của ma trận nhầm lẫn,
  nêu giả thuyết nguyên nhân
- Danh sách giới hạn ở mục 7
- Nếu LSTM thua rừng ngẫu nhiên, phần giải thích ở tầng 4 mục 9

**Hình nên vẽ:**

1. **Ma trận nhầm lẫn dạng hình nhiệt**, chuẩn hóa theo hàng, có số trong từng
   ô. Dùng `seaborn.heatmap(cm_norm, annot=True, fmt=".2f", xticklabels=names,
   yticklabels=names)`.
2. **Biểu đồ cột precision/recall/F1 theo từng lớp** — cho thấy lớp nào yếu chỉ
   trong một cái nhìn.
3. **Biểu đồ FPS so với F1** cho ba biến thể MediaPipe — trực quan hóa đường
   đánh đổi.
