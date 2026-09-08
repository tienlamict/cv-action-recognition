# Tầng 2 — Ước lượng tư thế người

> **Câu hỏi mở đầu:** Làm sao đi từ 2,7 triệu con số cường độ pixel tới 33 cặp
> tọa độ chỉ đúng vị trí vai, khuỷu tay, đầu gối?

Đây là tầng lý thuyết thị giác máy tính quan trọng nhất của đồ án. Bạn sẽ
**dùng** một mô hình có sẵn chứ không tự huấn luyện — nhưng nếu không hiểu bên
trong nó làm gì, bạn không giải thích được vì sao nó sai ở những chỗ nó sai, và
đó chính là thứ hội đồng sẽ hỏi.

Đây cũng là chương dài nhất của bộ tài liệu. Hãy đọc chậm.

---

## 1. Bài toán

**Ước lượng tư thế người** (*human pose estimation*): cho một ảnh, xác định vị
trí các bộ phận cơ thể của người trong ảnh.

Đầu vào: mảng `(H, W, 3)`.
Đầu ra: danh sách các cặp `(x, y)`, mỗi cặp ứng với một khớp đã định trước.

### Keypoint và skeleton

**Keypoint** (điểm khớp, điểm mốc, *landmark*) là một vị trí giải phẫu được
định nghĩa trước: "vai trái", "khuỷu tay phải", "mắt cá chân trái"...

**Skeleton** (khung xương) là tập hợp các keypoint **cộng với** quy ước nối
điểm nào với điểm nào. Bản thân các đoạn nối không được mô hình dự đoán — chúng
chỉ là quy ước để vẽ và để hiểu cấu trúc.

Điểm quan trọng dễ bỏ qua: **tập keypoint là một lựa chọn thiết kế, không phải
sự thật khách quan.** Không có định luật nào bảo phải dùng 17 hay 33 điểm.
Từng bộ dữ liệu chọn một bộ khác nhau:

| Bộ | Số điểm | Ghi chú |
|---|---|---|
| COCO | 17 | Chuẩn phổ biến nhất. Mũi, 2 mắt, 2 tai, vai, khuỷu, cổ tay, hông, gối, cổ chân |
| MPII | 16 | Có điểm "đỉnh đầu" và "cổ", không có mắt/tai |
| **MediaPipe (BlazePose)** | **33** | Siêu tập của COCO, thêm chi tiết bàn tay, bàn chân, và nhiều điểm mặt |
| NTU RGB+D (Kinect) | 25 | Từ cảm biến độ sâu, có tọa độ 3D thật |

Hệ quả thực tế: **mô hình huấn luyện trên bộ này không dùng được với bộ kia**
mà không ánh xạ lại. Nếu sau này bạn muốn so sánh với kết quả trên NTU RGB+D,
bạn phải xử lý chuyện 33 điểm và 25 điểm không trùng nhau.

### Vì sao bài toán này khó

Với người thì nhìn ra khuỷu tay là chuyện hiển nhiên. Với máy tính thì không.
Những khó khăn cụ thể:

- **Tự che khuất.** Đứng nghiêng thì một nửa cơ thể bị chính người đó che. Mô
  hình vẫn phải đoán vị trí tay bị khuất.
- **Che khuất bởi vật.** Ngồi sau bàn thì mất nửa dưới cơ thể.
- **Biến dạng lớn.** Cơ thể người có nhiều khớp, tạo ra vô số cấu hình. Khác
  với nhận dạng khuôn mặt, nơi hình dạng gần như cố định.
- **Nhập nhằng trái phải.** Người quay lưng lại thì tay trái ở bên phải ảnh.
  Đây là nguồn lỗi thật và thường xuyên.
- **Quần áo và hình thể.** Váy rộng che chân, áo khoác che vai.
- **Tỉ lệ.** Người có thể chiếm cả khung hình hoặc chỉ 50 pixel.
- **Nhòe chuyển động.** Vẫy tay nhanh thì tay bị nhòe thành vệt.
- **Nhập nhằng độ sâu.** Từ một ảnh 2D, không thể biết chắc tay đang giơ ra
  trước hay giơ lên trên — hai tư thế đó cho hình chiếu giống nhau.

Bốn cái cuối bạn sẽ **quan sát trực tiếp** trong thí nghiệm tuần 3. Ảnh chụp
màn hình những lần mô hình đoán sai là tư liệu tốt cho báo cáo.

---

## 2. Đủ về CNN để hiểu phần còn lại

Bạn không cần biết sâu về mạng tích chập. Nhưng cần đủ để hiểu vì sao bản đồ
nhiệt lại là câu trả lời tự nhiên. Phần này là mức tối thiểu.

### 2.1. Tích chập là gì

Hình dung một **cửa sổ nhỏ** — chẳng hạn 3×3 — trượt qua toàn bộ ảnh. Ở mỗi vị
trí, nó nhân từng phần tử của mình với 9 pixel bên dưới, cộng lại, ghi kết quả
ra một ảnh mới.

Cửa sổ đó gọi là **bộ lọc** (*filter*, *kernel*). Các con số trong nó quyết
định nó phát hiện cái gì.

Ví dụ, bộ lọc này phát hiện cạnh dọc:

```
-1   0  +1
-2   0  +2
-1   0  +2
```

Ở vùng ảnh phẳng (mọi pixel giống nhau), tổng có trọng số bằng 0 → kết quả 0.
Ở vùng có cạnh dọc (bên trái tối, bên phải sáng), kết quả lớn. Ảnh đầu ra vì
thế sáng lên đúng ở những chỗ có cạnh dọc.

Ba điều cần rút ra:

1. **Đầu ra vẫn là một ảnh.** Tích chập biến ảnh thành ảnh, gọi là **bản đồ đặc
   trưng** (*feature map*). Vị trí trong bản đồ đặc trưng vẫn tương ứng với vị
   trí trong ảnh gốc.
2. **Cùng một bộ lọc dùng cho mọi vị trí.** Nên "phát hiện cạnh dọc" học một
   lần dùng ở khắp nơi. Đây là lý do CNN cần ít tham số hơn nhiều so với mạng
   nối đầy đủ.
3. **Trong CNN, các con số trong bộ lọc được học từ dữ liệu**, không do người
   thiết kế. Mạng tự tìm ra bộ lọc nào hữu ích.

### 2.2. Xếp chồng nhiều lớp

Một lớp tích chập chỉ thấy được mảng 3×3 pixel — quá nhỏ để nhận ra bất cứ gì
có nghĩa. Nên ta xếp chồng nhiều lớp, và xen kẽ các bước **giảm kích thước**
(lấy mẫu xuống, *downsampling*): giữ lại một pixel cho mỗi vùng 2×2.

Sau mỗi lần giảm, một pixel ở lớp sau "nhìn thấy" một vùng lớn hơn của ảnh gốc.
Vùng đó gọi là **trường tiếp nhận** (*receptive field*).

```
lớp 1:  mỗi pixel thấy 3×3 pixel gốc    → phát hiện cạnh, đốm sáng
lớp 5:  mỗi pixel thấy ~30×30 pixel gốc → phát hiện góc, kết cấu
lớp 15: mỗi pixel thấy ~200×200 pixel gốc → phát hiện "đây là một khuỷu tay"
```

Sự đánh đổi cốt lõi: **càng sâu thì ngữ nghĩa càng phong phú, nhưng độ phân
giải không gian càng thấp.** Ở lớp cuối, bản đồ đặc trưng có thể chỉ còn
20×15 ô cho một ảnh 640×480.

Với bài toán phân loại ảnh ("ảnh này có con mèo không") thì mất độ phân giải
không sao — ta chỉ cần một câu trả lời cho cả ảnh. Với ước lượng tư thế thì
**vị trí chính là câu trả lời**, nên mất độ phân giải là vấn đề nghiêm trọng.

### 2.3. Encoder–decoder

Giải pháp: sau khi thu nhỏ để có ngữ nghĩa, **phóng to trở lại** để lấy độ chính
xác vị trí.

```
ảnh vào ──► thu nhỏ dần ──► đáy hẹp ──► phóng to dần ──► bản đồ ra
 640×480      encoder       20×15        decoder         160×120
             (hiểu "cái gì")            (định vị "ở đâu")
```

Kiến trúc này có nhiều tên tùy ngữ cảnh: *encoder–decoder*, *hourglass* (đồng
hồ cát), *U-Net*. Ý tưởng giống nhau. Thường có thêm các **kết nối tắt** nối
thẳng lớp thu nhỏ với lớp phóng to tương ứng, để mang chi tiết vị trí sắc nét
từ giai đoạn đầu sang.

Đây là kiến trúc nền của hầu hết mô hình ước lượng tư thế hiện đại.

---

## 3. Bản đồ nhiệt — khái niệm trung tâm của tầng này

Đây là câu hỏi tự kiểm tra chính của tầng 2 trong đề cương. Hãy hiểu thật kỹ.

### 3.1. Hai cách thiết kế đầu ra

Ta muốn mạng cho ra vị trí của, chẳng hạn, khuỷu tay trái. Có hai cách:

**Cách A — hồi quy trực tiếp.** Mạng in ra đúng 2 con số: `x = 0.62`,
`y = 0.31`. Đơn giản, gọn, có vẻ hiển nhiên.

**Cách B — bản đồ nhiệt.** Mạng in ra một **ảnh** cùng kích thước (hoặc nhỏ
hơn) ảnh vào, trong đó giá trị mỗi pixel là "độ tin rằng khuỷu tay trái nằm ở
đây". Sau đó lấy pixel có giá trị lớn nhất làm câu trả lời.

Một bản đồ nhiệt cho mỗi khớp. Với 17 khớp thì đầu ra là 17 ảnh xếp chồng.

Trực quan, một bản đồ nhiệt trông như một đốm sáng mờ quanh vị trí khớp:

```
0.0  0.0  0.0  0.0  0.0
0.0  0.1  0.3  0.1  0.0
0.0  0.3  1.0  0.3  0.0     ← đỉnh ở đây = vị trí khớp
0.0  0.1  0.3  0.1  0.0
0.0  0.0  0.0  0.0  0.0
```

Hầu hết mô hình chính xác cao đều chọn cách B. Vì sao?

### 3.2. Bốn lý do bản đồ nhiệt thắng

**Lý do 1 — Giữ được cấu trúc không gian.**

Tích chập có tính chất gọi là *tương đẳng tịnh tiến*: dịch vật thể trong ảnh
vào thì bản đồ đặc trưng cũng dịch theo đúng như vậy. Nói cách khác, quan hệ
"vị trí ở đầu ra ↔ vị trí ở đầu vào" được giữ nguyên suốt mạng.

Bản đồ nhiệt **khai thác** tính chất đó: câu trả lời được biểu diễn ở đúng chỗ
mà nó nằm.

Hồi quy trực tiếp thì **phá vỡ** nó. Để cho ra 2 con số, mạng phải làm phẳng
bản đồ đặc trưng thành một vector dài rồi đi qua lớp nối đầy đủ. Bước làm phẳng
xóa sạch thông tin "ô này ở góc trên trái, ô kia ở giữa" — mạng phải học lại
quan hệ vị trí từ đầu, qua hàng triệu tham số. Khó hơn nhiều với cùng lượng dữ
liệu.

**Lý do 2 — Biểu diễn được sự không chắc chắn.**

Nếu khuỷu tay bị che khuất, cách A vẫn phải in ra 2 con số. Nó buộc phải quả
quyết, dù không biết. Không có cách nào để nói "tôi không chắc".

Cách B có thể in ra một đốm sáng **rộng và nhạt** — nghĩa là "khoảng đâu đây,
nhưng tôi không chắc". Hoặc **hai đốm sáng** ở hai chỗ — "hoặc đây, hoặc kia".
Loại thứ hai gọi là *đa mốt*, và nó xảy ra thật: khi người quay lưng, mô hình
thực sự phân vân giữa tay trái và tay phải.

Đây cũng là nguồn gốc của **điểm tin cậy** mà bạn dùng để lọc frame hỏng: nó
chính là độ cao của đỉnh trong bản đồ nhiệt.

**Lý do 3 — Tín hiệu huấn luyện dày đặc.**

Với cách A, mỗi ảnh huấn luyện cho mạng 2 con số để so sánh. Tín hiệu rất
loãng.

Với cách B, **mỗi pixel** của bản đồ nhiệt đều có giá trị đúng để so sánh — bao
gồm cả những pixel phải bằng 0. Mạng học được "không, khớp không ở đây" từ hàng
nghìn vị trí cùng lúc. Gradient phong phú hơn, hội tụ nhanh hơn và ổn định hơn.

**Lý do 4 — Bài toán dễ hơn về bản chất.**

Hồi quy trực tiếp yêu cầu mạng học một ánh xạ **phi tuyến toàn cục**: từ toàn
bộ ảnh sang một con số. Dịch người sang phải 10 pixel thì đầu ra phải đổi đúng
10 — mạng phải "biết đếm pixel".

Bản đồ nhiệt biến nó thành một bài toán **cục bộ, lặp lại**: với mỗi vị trí,
hãy trả lời "khuỷu tay có ở đây không?". Đây đúng là loại câu hỏi mà tích chập
được sinh ra để trả lời.

### 3.3. Bản đồ nhiệt đúng được tạo thế nào

Khi huấn luyện, dữ liệu gán nhãn chỉ có tọa độ `(x, y)` do người đánh dấu. Ta
biến nó thành bản đồ nhiệt bằng cách đặt một **hàm Gauss** (chuông) tại vị trí
đó:

```
H(i, j) = exp( −[(i − x)² + (j − y)²] / (2σ²) )
```

Trong đó `σ` (sigma) quyết định đốm sáng rộng bao nhiêu. Đây là một siêu tham
số:

- `σ` nhỏ: đốm nhọn, định vị chính xác hơn, nhưng khó học vì gần như toàn bản
  đồ bằng 0
- `σ` lớn: đốm rộng, dễ học, nhưng định vị mờ

Giá trị điển hình là 2–3 pixel trên bản đồ nhiệt.

Vì sao dùng Gauss thay vì chỉ đặt số 1 tại đúng một pixel? Vì nhãn của con
người vốn không chính xác tuyệt đối — hai người đánh dấu "khuỷu tay" sẽ lệch
nhau vài pixel. Đốm Gauss mã hóa chính sự không chắc chắn đó, và cho mạng tín
hiệu học ở các pixel lân cận thay vì chỉ một pixel duy nhất.

### 3.4. Từ bản đồ nhiệt về tọa độ

Sau khi mạng cho ra bản đồ nhiệt, lấy vị trí giá trị lớn nhất:

```python
idx = np.argmax(heatmap)
y, x = np.unravel_index(idx, heatmap.shape)
confidence = heatmap[y, x]
```

Nhưng có một vấn đề: bản đồ nhiệt thường **nhỏ hơn ảnh gốc** (chẳng hạn 64×48
cho ảnh 256×192). Nên mỗi ô của bản đồ nhiệt tương ứng với một vùng 4×4 pixel
gốc — sai số lượng tử hóa tới ±2 pixel chỉ vì làm tròn.

Cách khắc phục: **tinh chỉnh dưới mức ô** (*sub-pixel refinement*). Nhìn các ô
lân cận đỉnh và dịch ước lượng về phía ô lân cận sáng hơn, hoặc khớp một
parabol qua ba điểm để tìm đỉnh thật.

### 3.5. Nhược điểm của bản đồ nhiệt

Để công bằng và để trả lời được nếu bị hỏi ngược:

- **Tốn bộ nhớ.** 17 bản đồ nhiệt 64×48 nặng hơn nhiều so với 34 con số. Trên
  điện thoại thì đây là chi phí thật.
- **Sai số lượng tử hóa** như vừa nói.
- **`argmax` không khả vi.** Không thể huấn luyện toàn hệ thống đầu-cuối qua
  bước lấy cực đại. Có kỹ thuật khắc phục (*soft-argmax*, *DSNT*) nhưng thêm
  phức tạp.
- **Cần hậu xử lý.** Không phải mạng in ra tọa độ là xong.

Chính những nhược điểm này là lý do BlazePose — mô hình chạy trên điện thoại
bên trong MediaPipe — chọn một con đường lai. Ta sẽ nói ở mục 5.

---

## 4. Top-down so với bottom-up

Đây là hai họ phương pháp cho bài toán **nhiều người trong ảnh**. Câu hỏi cốt
lõi: khi có ba người, làm sao biết cái khuỷu tay này thuộc về ai?

### 4.1. Top-down — "tìm người trước, tìm khớp sau"

```
ảnh ──► bộ phát hiện người ──► N khung bao
             │
             ├── cắt người 1 ──► mô hình tư thế ──► 17 khớp
             ├── cắt người 2 ──► mô hình tư thế ──► 17 khớp
             └── cắt người 3 ──► mô hình tư thế ──► 17 khớp
```

Trước hết chạy một bộ phát hiện đối tượng (YOLO, Faster R-CNN...) để tìm khung
bao quanh mỗi người. Cắt từng người ra, phóng về kích thước chuẩn, rồi chạy mô
hình tư thế trên từng ảnh cắt.

**Ưu điểm:**

- **Chính xác hơn.** Mô hình tư thế luôn thấy đúng một người, chiếm gần hết
  khung hình, ở tỉ lệ chuẩn hóa. Bài toán dễ hơn hẳn.
- **Bài toán gán khớp cho người biến mất.** Mỗi ảnh cắt chỉ có một người, không
  có gì để nhầm.
- **Người nhỏ được xử lý tốt**, vì ảnh cắt được phóng to lên kích thước chuẩn.

**Nhược điểm:**

- **Thời gian tăng tuyến tính theo số người.** 10 người = chạy mô hình tư thế
  10 lần. Không dùng được cho cảnh đông đúc theo thời gian thực.
- **Lỗi dồn.** Nếu bộ phát hiện bỏ sót một người thì người đó biến mất hoàn
  toàn. Nếu khung bao lệch thì tư thế lệch theo.
- **Hai bước, hai mô hình** — nặng hơn về triển khai.

Đại diện: Stacked Hourglass, HRNet, SimpleBaseline.

### 4.2. Bottom-up — "tìm tất cả khớp trước, ghép người sau"

```
ảnh ──► mô hình ──► mọi khuỷu tay trong ảnh
                ──► mọi cổ tay trong ảnh
                ──► ... (mọi khớp, chưa biết của ai)
                     │
                     ▼
              thuật toán ghép nhóm ──► từng người
```

Chạy một lần trên toàn ảnh, phát hiện **mọi** khớp thuộc mọi người cùng lúc.
Sau đó dùng một thuật toán ghép để nhóm chúng thành từng người.

Câu hỏi khó: làm sao biết cổ tay này nối với khuỷu tay nào? OpenPose giải bằng
**Trường ái lực bộ phận** (*Part Affinity Fields*, PAF): ngoài bản đồ nhiệt cho
từng khớp, mạng còn dự đoán, cho mỗi loại xương, một trường vector 2D chỉ hướng
từ khớp này sang khớp kia. Muốn kiểm tra hai điểm có nối nhau không, lấy tích
phân trường vector dọc đoạn thẳng nối chúng — giá trị cao nghĩa là có xương
thật.

**Ưu điểm:**

- **Thời gian gần như không phụ thuộc số người.** Một lượt chạy cho cả ảnh. Với
  20 người thì nhanh hơn top-down rất nhiều.
- **Một mô hình duy nhất**, không phụ thuộc bộ phát hiện.

**Nhược điểm:**

- **Kém chính xác hơn** ở cùng chi phí tính toán, vì mô hình phải xử lý mọi tỉ
  lệ người cùng lúc trong một ảnh.
- **Người nhỏ bị bỏ sót** — họ chỉ chiếm vài pixel trong ảnh gốc.
- **Ghép nhóm sai khi chen chúc.** Hai người ôm nhau thì tay của người này dễ
  bị gán cho người kia.

Đại diện: OpenPose, Associative Embedding, HigherHRNet.

### 4.3. Bảng so sánh

| Tiêu chí | Top-down | Bottom-up |
|---|---|---|
| Độ chính xác | Cao hơn | Thấp hơn |
| Thời gian theo số người | Tuyến tính | Gần như hằng |
| Người nhỏ | Tốt (nhờ cắt và phóng to) | Kém |
| Cảnh đông đúc | Chậm nhưng chính xác | Nhanh nhưng dễ ghép sai |
| Số mô hình | Hai | Một |
| Điểm yếu chính | Phụ thuộc bộ phát hiện | Bài toán ghép nhóm |

### 4.4. MediaPipe nằm ở đâu

MediaPipe Pose về bản chất là **top-down**, nhưng với một mẹo quan trọng: nó
không chạy bộ phát hiện ở mọi frame.

Sẽ nói ở mục tiếp theo — đây là ý tưởng hay nhất của BlazePose và là thứ đáng
viết vào báo cáo.

---

## 5. BlazePose — mô hình bên trong MediaPipe Pose

Bài báo: *BlazePose: On-device Real-time Body Pose Tracking*, Bazarevsky và
cộng sự, 2020. Ngắn, dễ đọc, nên đọc ở tuần 3.

Mục tiêu thiết kế của nó khác các mô hình học thuật: không nhắm điểm số cao
nhất trên bảng xếp hạng, mà nhắm **chạy thời gian thực trên điện thoại**. Mọi
lựa chọn kiến trúc đều xuất phát từ ràng buộc đó — và đó chính là lý do nó phù
hợp với đồ án của bạn.

### 5.1. Mô hình phát hiện–theo dõi

Đây là ý tưởng trung tâm.

Chạy bộ phát hiện người ở mọi frame thì tốn. Nhưng ở 30 FPS, người ta gần như
không dịch chuyển giữa hai frame liên tiếp. Vậy tại sao phải tìm lại từ đầu?

```
Frame 1:   chạy bộ phát hiện → tìm vùng chứa người
           chạy mô hình khớp trên vùng đó → 33 điểm
           từ 33 điểm, TỰ SUY RA vùng cho frame sau

Frame 2:   dùng vùng đã suy ra, bỏ qua bộ phát hiện
           chạy mô hình khớp → 33 điểm
           suy ra vùng cho frame sau

Frame 3..n: như trên

Chỉ khi mất dấu (điểm tin cậy tụt) mới chạy lại bộ phát hiện.
```

Kết quả: chi phí mỗi frame giảm mạnh, vì bộ phát hiện — phần đắt nhất — hầu như
không bao giờ chạy.

**Đây là lý do MediaPipe đạt 30 FPS trên CPU trong khi các mô hình top-down
khác cần GPU.** Câu này rất đáng có trong báo cáo, vì nó giải thích quyết định
công nghệ trung tâm của đồ án bằng lý do kỹ thuật chứ không phải "vì nó dễ
cài".

**Hệ quả bạn sẽ quan sát được:** nếu bạn nhảy ra khỏi khung hình rồi nhảy vào
lại, sẽ có một khoảng trễ ngắn trước khi khung xương xuất hiện — đó là lúc bộ
phát hiện phải chạy lại. Ghi nhận hiện tượng này trong thí nghiệm tuần 3.

### 5.2. Bộ phát hiện dựa trên mặt và thân

BlazePose có một lựa chọn thú vị: bộ phát hiện của nó không tìm khung bao quanh
cả người, mà **định vị vùng đầu/thân người** rồi từ đó suy ra:

- Trung điểm hai hông
- Bán kính đường tròn bao quanh người
- Góc nghiêng của thân

Lý do: khuôn mặt và thân trên là phần có tín hiệu thị giác ổn định nhất và ít
biến dạng nhất trên cơ thể. Chân và tay thì thay đổi liên tục.

Từ ba thông tin đó, MediaPipe **xoay và cắt** vùng ảnh sao cho người luôn ở tư
thế chuẩn hóa (thẳng đứng, chiếm cùng tỉ lệ) trước khi đưa vào mô hình khớp.
Mô hình khớp vì thế chỉ cần học một khoảng biến thiên hẹp hơn nhiều — nên nó
được phép nhỏ hơn và nhanh hơn.

> Chú ý sự trùng lặp thú vị: MediaPipe chuẩn hóa theo hông và theo tỉ lệ thân
> **ở mức ảnh**, và bạn sẽ chuẩn hóa theo hông và tỉ lệ thân **ở mức tọa độ**
> trong tầng 3. Cùng một ý tưởng, áp dụng ở hai chỗ, vì cùng một lý do: loại bỏ
> biến thiên không mang thông tin.

### 5.3. Kiến trúc lai bản đồ nhiệt và hồi quy

Mục 3 đã nói bản đồ nhiệt tốt nhưng tốn. BlazePose dung hòa bằng một mẹo huấn
luyện:

- **Khi huấn luyện:** mạng có cả nhánh bản đồ nhiệt lẫn nhánh hồi quy trực
  tiếp. Nhánh bản đồ nhiệt cung cấp tín hiệu học dày đặc, dạy cho phần thân
  chung của mạng cách định vị tốt.
- **Khi chạy thật:** các lớp đầu ra bản đồ nhiệt **bị gỡ bỏ**. Chỉ giữ nhánh
  hồi quy, cho ra thẳng 33 cặp tọa độ.

Nói cách khác: dùng bản đồ nhiệt như **giàn giáo dạy học**, rồi tháo giàn giáo
đi khi xây xong. Bạn được lợi thế huấn luyện của bản đồ nhiệt mà không chịu chi
phí bộ nhớ và hậu xử lý của nó khi triển khai.

Đây là điểm tinh tế nhất của BlazePose và là chi tiết đáng nhắc trong báo cáo —
nó cho thấy bạn đã đọc bài báo thật, không chỉ đọc trang tài liệu API.

### 5.4. Ba biến thể mô hình

MediaPipe Pose Landmarker có ba file `.task`:

| Biến thể | Kích thước | Tốc độ | Độ chính xác |
|---|---|---|---|
| `pose_landmarker_lite` | Nhỏ nhất | Nhanh nhất | Thấp nhất |
| `pose_landmarker_full` | Trung bình | Trung bình | Trung bình |
| `pose_landmarker_heavy` | Lớn nhất | Chậm nhất | Cao nhất |

Cả ba đều cho ra **cùng 33 điểm** với cùng ý nghĩa — chỉ khác độ sâu mạng.

**Đề cương đề xuất so sánh cả ba** trong bảng thí nghiệm. Đây là một hàng dữ
liệu rẻ mà giá trị cao: nó biến "tôi dùng MediaPipe" thành "tôi đã khảo sát
đánh đổi giữa độ chính xác và tốc độ và chọn có cơ sở". Bảng nên có ba cột: FPS
đo được, độ chính xác cuối cùng của hệ thống, và tỉ lệ frame phát hiện được
người.

---

## 6. Đầu ra của MediaPipe — đọc kỹ, bạn dùng nó mỗi ngày

### 6.1. 33 điểm khớp

```
 0  mũi
 1  mắt trái (trong)      2  mắt trái        3  mắt trái (ngoài)
 4  mắt phải (trong)      5  mắt phải        6  mắt phải (ngoài)
 7  tai trái              8  tai phải
 9  miệng trái           10  miệng phải
───────────────────── 10 điểm trên là VÙNG MẶT ─────────────────────
11  vai trái            12  vai phải
13  khuỷu tay trái      14  khuỷu tay phải
15  cổ tay trái         16  cổ tay phải
17  ngón út trái        18  ngón út phải
19  ngón trỏ trái       20  ngón trỏ phải
21  ngón cái trái       22  ngón cái phải
23  hông trái           24  hông phải
25  đầu gối trái        26  đầu gối phải
27  cổ chân trái        28  cổ chân phải
29  gót trái            30  gót phải
31  mũi bàn chân trái   32  mũi bàn chân phải
```

Các chỉ số cần thuộc lòng cho đồ án này:

- **11, 12** — hai vai
- **23, 24** — hai hông
- **13, 14** — khuỷu tay; **15, 16** — cổ tay
- **25, 26** — đầu gối; **27, 28** — cổ chân

Trung điểm 23 và 24 là **gốc tọa độ** trong hàm chuẩn hóa. Khoảng cách từ trung
điểm vai (11, 12) tới trung điểm hông là **thang tỉ lệ**.

Điểm 0–10 là 10 điểm mặt. Đề cương bỏ chúng, còn lại 23 điểm — chính là
`n_joints=23` trong mã LSTM. Lý do ở tầng 3.

**Lưu ý về trái/phải:** nhãn "trái" của MediaPipe là trái **của người trong
ảnh**, không phải trái của người xem. Người đối diện camera thì vai trái của họ
xuất hiện ở phía **phải** màn hình. Điều này quan trọng khi bạn làm tăng cường
dữ liệu bằng lật ảnh — sẽ nói ở tầng 3.

### 6.2. Mỗi điểm có gì

```python
lm = result.pose_landmarks[0][23]   # người đầu tiên, khớp 23 (hông trái)

lm.x            # 0.0 – 1.0, tỉ lệ theo CHIỀU RỘNG ảnh
lm.y            # 0.0 – 1.0, tỉ lệ theo CHIỀU CAO ảnh
lm.z            # độ sâu tương đối, gốc ở giữa hông
lm.visibility   # 0.0 – 1.0, độ tin rằng điểm này nhìn thấy được
lm.presence     # 0.0 – 1.0, độ tin rằng điểm này có trong khung hình
```

**Về `x` và `y`:** đã được chuẩn hóa theo kích thước ảnh, nên không đổi khi bạn
đổi độ phân giải. Rất tiện. Nhưng có một hệ quả tinh tế và nguy hiểm — xem mục
6.3.

Giá trị **có thể nằm ngoài [0, 1]** khi mô hình ngoại suy vị trí một khớp bị
cắt ra ngoài khung hình. Không phải lỗi, nhưng đừng tin những giá trị đó.

**Về `z`:** độ sâu tương đối so với trung điểm hông. Giá trị âm là gần camera
hơn, dương là xa hơn.

> **Khuyến nghị mạnh: đừng dùng `z` trong đồ án này.**
>
> Ước lượng độ sâu từ một camera đơn là bài toán về bản chất nhập nhằng — không
> có thông tin nào trong ảnh 2D cho biết chắc tay đang giơ ra trước hay lên
> trên. Giá trị `z` của MediaPipe là một phỏng đoán có học, không phải phép đo,
> và tài liệu chính thức cũng lưu ý về độ tin cậy của nó.
>
> Đưa `z` vào tức là thêm 33 chiều nhiễu vào dữ liệu vốn đã ít. Với sáu hành
> động phân biệt được bằng hình học 2D, cái giá lớn hơn cái lợi. Dùng `(x, y)`.
>
> Nếu hội đồng hỏi "sao không dùng 3D", câu trả lời trên là một câu trả lời
> tốt — nó cho thấy bạn đã cân nhắc chứ không bỏ sót.

**Về `visibility`:** đây là công cụ lọc quan trọng nhất của bạn. Điểm bị che
khuất thì mô hình vẫn đoán ra tọa độ, nhưng `visibility` thấp. Quy tắc thực
hành:

```python
if lm.visibility < 0.5:
    # điểm này không đáng tin — nội suy từ frame trước, hoặc bỏ frame
```

Không lọc thì các tọa độ đoán bừa sẽ lọt vào dữ liệu huấn luyện và làm mô hình
học nhiễu.

### 6.3. Cạm bẫy tỉ lệ khung hình — đọc kỹ, ít tài liệu nói

`x` chia cho **chiều rộng**, `y` chia cho **chiều cao**. Với ảnh 1280×720, hai
số chia khác nhau.

Hệ quả: **tọa độ chuẩn hóa của MediaPipe không bảo toàn hình học.** Một đoạn
thẳng dài 100 pixel nằm ngang cho `Δx = 100/1280 = 0.078`. Cũng đoạn 100 pixel
đó nằm dọc cho `Δy = 100/720 = 0.139`. Cùng độ dài thật, hai con số khác nhau
gần gấp đôi.

Nếu bạn tính khoảng cách hay góc trực tiếp trên `(lm.x, lm.y)`, mọi hình học
của bạn bị **kéo giãn theo tỉ lệ khung hình**. Góc khuỷu tay 90° sẽ không ra
90°.

**Cách sửa — nhân lại kích thước ảnh trước khi làm bất cứ phép hình học nào:**

```python
H, W = frame.shape[:2]
pts = np.array([[lm.x * W, lm.y * H] for lm in landmarks])   # đơn vị pixel
```

Sau bước này, `pts` ở đơn vị pixel và hình học đúng. Hàm `normalize()` trong
đề cương sẽ chia cho độ dài thân sau đó, nên kết quả cuối vẫn bất biến với độ
phân giải — nhưng **không bị méo**.

Vì sao vẫn cần chuẩn hóa lại sau khi đã có tọa độ pixel? Vì nhân với `W, H` chỉ
sửa méo hình, chưa loại bỏ vị trí trong khung hình và khoảng cách tới camera.
Đó là việc của tầng 3.

Cách kiểm tra bạn đã làm đúng: đứng thẳng, giơ ngang một cánh tay. Đo độ dài
cánh tay (vai→cổ tay) khi giơ ngang và khi giơ thẳng lên trời. Hai con số phải
gần bằng nhau. Nếu chênh nhau khoảng tỉ lệ 16:9 thì bạn đang quên nhân `W, H`.

### 6.4. World landmarks

MediaPipe còn cho một đầu ra thứ hai:

```python
result.pose_world_landmarks[0]   # tọa độ tính bằng MÉT, gốc ở giữa hông
```

Đây là ước lượng vị trí 3D trong thế giới thực, đã đặt gốc ở hông. Nghe rất
hấp dẫn — nó đã làm sẵn phần chuẩn hóa!

**Nhưng vẫn khuyên dùng `pose_landmarks` 2D**, vì hai lý do:

1. Trục `z` vẫn kém tin cậy như đã nói, mà `pose_world_landmarks` thì bắt buộc
   có `z`.
2. **Bạn tự viết hàm chuẩn hóa là một phần giá trị học thuật của đồ án.** Nó là
   tầng 3 của bản đồ kiến thức, là câu tự kiểm tra quan trọng, và là chỗ bạn
   chứng minh mình hiểu vì sao chuẩn hóa cần thiết. Gọi một hàm có sẵn thì mất
   phần đó.

Có thể nhắc `pose_world_landmarks` trong báo cáo như một lựa chọn đã cân nhắc
và giải thích vì sao không dùng. Đó là dấu hiệu của người đọc tài liệu kỹ.

---

## 7. Giới hạn cần biết — và nên viết vào báo cáo

**Chỉ một người.** Với `PoseLandmarker`, mặc định `num_poses=1`. Đề cương chọn
đúng thế: một người trong khung hình, không cần tracking, không cần gán ID. Nếu
có người thứ hai đi qua, hệ thống có thể nhảy sang bám người đó — hãy kiểm soát
điều này khi quay dữ liệu và khi demo.

**Che khuất là nguồn lỗi chính.** Ngồi sau bàn thì chân bị che, mô hình vẫn
đoán ra tọa độ chân với `visibility` thấp. Đây là lý do giao thức thu thập dữ
liệu yêu cầu **toàn thân trong khung hình**.

**Nhòe chuyển động.** Vẫy tay rất nhanh trong ánh sáng yếu thì tay bị nhòe và
điểm cổ tay nhảy loạn. Ánh sáng đủ mạnh khiến camera dùng thời gian phơi sáng
ngắn hơn, giảm nhòe. Đây là lý do thật của yêu cầu "đủ sáng" trong giao thức
quay.

**Nhập nhằng trái/phải khi quay lưng.** Mô hình đôi khi hoán đổi hai bên. Với
sáu hành động của đồ án thì không nghiêm trọng (không hành động nào phụ thuộc
việc phân biệt tay trái với tay phải), nhưng nên biết và nên nêu trong phần
giới hạn.

**Người ở xa.** Càng nhỏ trong khung hình thì càng ít pixel để mô hình làm việc,
độ chính xác giảm. Nên giữ khoảng cách quay nhất quán.

---

## 8. Thí nghiệm quan sát cho tuần 3

Đề cương yêu cầu một tuần thuần lý thuyết kèm quan sát. Đây là danh sách thí
nghiệm cụ thể. Với mỗi cái, ghi lại `visibility` của các khớp liên quan và chụp
màn hình.

| Thí nghiệm | Quan sát điều gì |
|---|---|
| Che một tay sau lưng | `visibility` của cổ tay, khuỷu tay bên đó tụt bao nhiêu? Tọa độ đoán ra nằm ở đâu? |
| Quay lưng lại camera | Trái/phải có bị hoán đổi không? Sau bao lâu thì ổn định lại? |
| Đứng xa dần: 1m, 2m, 4m | Ở khoảng cách nào thì khung xương bắt đầu giật? |
| Ngồi sau bàn | Điểm chân bị đoán ra ở đâu? `visibility` bằng bao nhiêu? |
| Vẫy tay rất nhanh | Cổ tay có bám kịp không? Thử ở hai mức ánh sáng |
| Ra khỏi khung rồi vào lại | Mất bao nhiêu frame để khung xương xuất hiện lại? (đây là lúc bộ phát hiện chạy lại) |
| Mặc áo rộng / áo bó | Có khác biệt không? |
| So sánh lite / full / heavy | FPS và độ ổn định của khung xương ở cùng điều kiện |

Sản phẩm của tuần 3 theo đề cương là "bản tóm tắt 2 trang + ảnh minh họa các ca
đoán sai". Bảng trên chính là dàn ý cho phần ảnh minh họa đó.

---

## Tự kiểm tra

Câu 1 là câu chính của tầng này. Nếu chỉ trả lời được một câu, hãy là câu đó.

1. **Vì sao hầu hết mô hình ước lượng tư thế dự đoán một bản đồ nhiệt cho mỗi
   khớp rồi mới lấy điểm cực đại, thay vì hồi quy thẳng ra hai con số tọa độ?**
   Nêu ít nhất ba lý do độc lập.

2. Nêu hai ưu điểm và hai nhược điểm của top-down so với bottom-up. Với ảnh có
   30 người thì nên chọn cái nào và vì sao?

3. MediaPipe làm gì để không phải chạy bộ phát hiện người ở mọi frame? Bạn quan
   sát được hệ quả của thiết kế này bằng cách nào?

4. BlazePose huấn luyện với bản đồ nhiệt nhưng khi chạy thật thì không dùng.
   Giải thích logic của lựa chọn này.

5. `lm.x = 0.5, lm.y = 0.5` trên ảnh 1280×720. Tọa độ pixel là bao nhiêu? Nếu
   bạn tính khoảng cách giữa hai khớp trực tiếp trên `(lm.x, lm.y)` mà không
   nhân `W, H` thì sai ở đâu?

6. Vì sao khuyên không dùng `lm.z` trong đồ án này, dù nó có sẵn và miễn phí?

7. Một người ngồi sau bàn. `visibility` của khớp đầu gối là 0.15 nhưng tọa độ
   vẫn có giá trị. Nên làm gì với frame này, và vì sao không nên tin tọa độ đó?

<details>
<summary>Đáp án gợi ý</summary>

1. (a) **Giữ cấu trúc không gian** — tích chập có tính tương đẳng tịnh tiến,
   bản đồ nhiệt khai thác nó; hồi quy phải làm phẳng và đi qua lớp nối đầy đủ,
   phá hủy quan hệ vị trí. (b) **Biểu diễn được sự không chắc chắn** — đốm rộng
   nghĩa là không chắc, hai đốm nghĩa là phân vân giữa hai khả năng; hồi quy
   buộc phải quả quyết. Đây cũng là nguồn của điểm tin cậy. (c) **Tín hiệu học
   dày đặc** — mỗi pixel cho một tín hiệu gradient thay vì chỉ 2 con số mỗi
   ảnh. (d) **Bài toán dễ hơn về bản chất** — trả lời "khớp có ở đây không" tại
   mỗi vị trí, đúng loại việc tích chập giỏi, thay vì học ánh xạ phi tuyến toàn
   cục từ ảnh ra tọa độ.

2. Ưu điểm top-down: chính xác hơn (mô hình luôn thấy một người ở tỉ lệ chuẩn),
   xử lý người nhỏ tốt (được cắt và phóng to). Nhược điểm: thời gian tăng tuyến
   tính theo số người, và lỗi của bộ phát hiện dồn xuống. Với 30 người nên chọn
   bottom-up vì top-down phải chạy mô hình tư thế 30 lần mỗi frame.

3. Mô hình phát hiện–theo dõi: sau khi có 33 khớp ở frame này, nó suy ra vùng
   quan tâm cho frame sau và bỏ qua bộ phát hiện. Chỉ chạy lại bộ phát hiện khi
   mất dấu. Quan sát: bước ra khỏi khung rồi vào lại, sẽ có độ trễ ngắn trước
   khi khung xương xuất hiện — đó là lúc bộ phát hiện chạy lại.

4. Bản đồ nhiệt cho tín hiệu học dày đặc và dạy phần thân mạng định vị tốt,
   nhưng khi chạy thì tốn bộ nhớ, gây sai số lượng tử hóa và cần hậu xử lý.
   Giữ lợi ích huấn luyện, bỏ chi phí triển khai bằng cách gỡ nhánh bản đồ
   nhiệt trước khi suy luận.

5. `x = 0.5 × 1280 = 640`, `y = 0.5 × 720 = 360`. Nếu không nhân: `x` chia cho
   1280, `y` chia cho 720 — hai thang khác nhau, nên hình học bị kéo giãn theo
   tỉ lệ khung hình. Khoảng cách và góc tính ra đều sai; một đoạn nằm ngang và
   một đoạn nằm dọc cùng độ dài thật sẽ cho hai giá trị khác nhau.

6. Độ sâu từ camera đơn về bản chất nhập nhằng; `z` là phỏng đoán chứ không
   phải phép đo. Thêm nó là thêm chiều nhiễu vào dữ liệu vốn ít, tăng nguy cơ
   quá khớp. Sáu hành động đã phân biệt được bằng hình học 2D.

7. Đánh dấu khớp đó là không tin cậy: nội suy từ frame trước, hoặc bỏ cả frame.
   Tọa độ vẫn có giá trị vì mô hình luôn cho ra một con số — nó **đoán** vị trí
   khớp bị che dựa trên phần cơ thể nhìn thấy được. Đoán này không dựa trên
   bằng chứng thị giác nào ở vị trí đó, nên đưa vào huấn luyện là dạy mô hình
   học nhiễu.

</details>

---

## Đưa gì vào báo cáo

Đây là mục dài nhất và giá trị nhất của chương 2. Khoảng 4–6 trang cho **2.2
Ước lượng tư thế người**:

**2.2.1 Bài toán và định nghĩa** — keypoint, skeleton, các bộ keypoint phổ
biến, những khó khăn đặc thù.

**2.2.2 Bản đồ nhiệt** — mục quan trọng nhất. Trình bày cả hai cách thiết kế
đầu ra, lập luận vì sao bản đồ nhiệt thắng, và nêu cả nhược điểm của nó. Kèm
hình minh họa một bản đồ nhiệt.

**2.2.3 Hai họ phương pháp** — top-down và bottom-up, bảng so sánh, ví dụ đại
diện (Stacked Hourglass, HRNet cho top-down; OpenPose với PAF cho bottom-up).

**2.2.4 BlazePose và MediaPipe Pose** — mô hình phát hiện–theo dõi, chuẩn hóa
vùng cắt theo hông, kiến trúc lai bản đồ nhiệt–hồi quy, ba biến thể mô hình.
Kết lại bằng lý do chọn công cụ này cho đồ án.

**2.2.5 Định dạng đầu ra và giới hạn** — 33 điểm, ý nghĩa `x/y/z/visibility`,
vấn đề tỉ lệ khung hình, và phần giới hạn ở mục 7.

**Hình nên vẽ:**

1. Sơ đồ so sánh top-down và bottom-up cạnh nhau — dễ vẽ, dễ hiểu, thể hiện
   ngay bạn nắm được sự phân loại của lĩnh vực.
2. Một khung hình từ dữ liệu của bạn, có khung xương 33 điểm vẽ đè, các điểm
   được đánh số. Đây là hình "của bạn", không phải hình chép từ bài báo.
3. Bảng hoặc ảnh so sánh các ca mô hình đoán sai (che khuất, quay lưng, đứng
   xa) — thu được từ thí nghiệm tuần 3.

**Câu nên có trong báo cáo:** "Chúng tôi chọn MediaPipe Pose vì mô hình phát
hiện–theo dõi của BlazePose cho phép đạt thời gian thực trên CPU, phù hợp với
ràng buộc triển khai trên máy tính phổ thông không GPU." Đây là một lý do kỹ
thuật, khác hẳn với "vì nó dễ cài".
