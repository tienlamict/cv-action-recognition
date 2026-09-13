# Tầng 2 — Ước lượng tư thế bàn tay

> **Câu hỏi mở đầu:** Làm sao đi từ hơn hai triệu con số cường độ pixel tới 21
> cặp tọa độ chỉ đúng vị trí cổ tay, từng đốt ngón, từng đầu ngón?

Đây là tầng lý thuyết thị giác máy tính quan trọng nhất của đồ án. Bạn sẽ
**dùng** một mô hình có sẵn chứ không tự huấn luyện. Nhưng nếu không hiểu bên
trong nó làm gì, bạn không giải thích được vì sao nó sai ở đúng những chỗ nó
sai, và đó chính là thứ hội đồng sẽ hỏi.

Tài liệu gốc cần đọc kèm: **MediaPipe Hands: On-device Real-time Hand Tracking**
(Zhang và cộng sự, 2020, arXiv:2006.10214). Chỉ 5 trang. Mọi con số cụ thể
trong tài liệu này đều lấy từ đó, trừ chỗ ghi rõ nguồn khác.

> **Ghi chú về bản cập nhật.** Tài liệu này thay thế bản cũ viết cho ước lượng
> tư thế **người**. Khung tư duy giữ nguyên: bài toán là gì, đầu ra thiết kế thế
> nào, kiến trúc hai tầng hoạt động ra sao, mô hình sai ở đâu. Nhưng câu trả lời
> cho từng câu hỏi đó thì khác, và có chỗ khác một cách thú vị — đặc biệt là
> mục 4, nơi mô hình bàn tay chọn ngược lại với mô hình toàn thân.

---

## 1. Bài toán

**Ước lượng tư thế bàn tay** (*hand pose estimation*): cho một ảnh, xác định vị
trí các điểm giải phẫu trên bàn tay xuất hiện trong ảnh.

Đầu vào: mảng `(H, W, 3)`.
Đầu ra: danh sách 21 cặp `(x, y)`, mỗi cặp ứng với một điểm đã định trước.

### 1.1. Điểm mốc và khung xương bàn tay

**Điểm mốc** (*landmark*, *keypoint*) là một vị trí giải phẫu được định nghĩa
trước: "cổ tay", "khớp giữa ngón trỏ", "đầu ngón cái".

**Khung xương** là tập điểm mốc **cộng với** quy ước nối điểm nào với điểm nào.
Bản thân các đoạn nối không được mô hình dự đoán. Chúng chỉ là quy ước để vẽ và
để hiểu cấu trúc.

Bố cục 21 điểm mà MediaPipe dùng không phải do Google nghĩ ra. Bài báo nói rõ họ
dùng lại cùng một *topology* với công trình của Simon và cộng sự (CMU, 2017), và
bố cục đó đã trở thành quy ước chung của lĩnh vực.

### 1.2. Bảng 21 điểm

Mỗi ngón có bốn điểm, đánh số từ gốc ra đầu ngón. Cộng với cổ tay là 21.

| Chỉ số | Tên giải phẫu | Ghi chú |
|---|---|---|
| 0 | Cổ tay (*wrist*) | **Gốc tọa độ khi chuẩn hóa** |
| 1 | Ngón cái — gốc (CMC) | |
| 2 | Ngón cái — MCP | |
| 3 | Ngón cái — IP | |
| 4 | **Đầu ngón cái** | Dùng tính độ xòe |
| 5 | Ngón trỏ — gốc (MCP) | |
| 6 | Ngón trỏ — khớp giữa (PIP) | Dùng tính góc gập |
| 7 | Ngón trỏ — khớp xa (DIP) | |
| 8 | **Đầu ngón trỏ** | Dùng tính độ xòe |
| 9 | **Ngón giữa — gốc (MCP)** | **Cùng điểm 0 tạo đơn vị đo** |
| 10 | Ngón giữa — PIP | |
| 11 | Ngón giữa — DIP | |
| 12 | **Đầu ngón giữa** | Dùng tính độ xòe |
| 13 | Ngón áp út — gốc (MCP) | |
| 14 | Ngón áp út — PIP | |
| 15 | Ngón áp út — DIP | |
| 16 | **Đầu ngón áp út** | Dùng tính độ xòe |
| 17 | Ngón út — gốc (MCP) | |
| 18 | Ngón út — PIP | |
| 19 | Ngón út — DIP | |
| 20 | **Đầu ngón út** | Dùng tính độ xòe |

Viết tắt khớp ngón tay, dùng suốt tài liệu:

- **MCP** — *metacarpophalangeal*, khớp nối bàn tay với ngón, tức là đốt gốc.
- **PIP** — *proximal interphalangeal*, khớp giữa của ngón.
- **DIP** — *distal interphalangeal*, khớp gần đầu ngón nhất.
- **CMC** và **IP** là hai khớp riêng của ngón cái, vì ngón cái chỉ có hai đốt
  chứ không phải ba như bốn ngón còn lại.

Quy ước nối, dùng để vẽ:

```python
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),               # ngón cái
    (0,5),(5,6),(6,7),(7,8),               # ngón trỏ
    (5,9),(9,10),(10,11),(11,12),          # ngón giữa
    (9,13),(13,14),(14,15),(15,16),        # ngón áp út
    (13,17),(0,17),(17,18),(18,19),(19,20) # ngón út và gan bàn tay
]
```

Để ý ba đoạn `(5,9)`, `(9,13)`, `(13,17)`: chúng nối các gốc ngón với nhau, tạo
thành **gan bàn tay**. Cùng với `(0,5)` và `(0,17)`, năm đoạn này tạo thành một
đa giác gần như cứng — không đổi hình khi ngón co duỗi. Tính chất đó là nền tảng
của toàn bộ tầng 3.

### 1.3. Tập điểm mốc là một lựa chọn thiết kế

Không có định luật nào bảo phải dùng 21 điểm. Các bộ dữ liệu khác chọn khác:

| Nguồn | Số điểm | Ghi chú |
|---|---|---|
| **MediaPipe Hand Landmarker** | **21** | Theo bố cục của Simon và cộng sự, CMU 2017 |
| DHG-14/28 và SHREC'17 | 22 | Từ camera độ sâu Intel RealSense, có tọa độ 3D thật |
| NYU Hand Pose | 36 (thường dùng 14) | Từ Kinect |
| InterHand2.6M | 21 mỗi tay | Bố cục giống MediaPipe, dữ liệu hai tay tương tác |

Hệ quả thực tế giống hệt tầng 2 bản cũ: **mô hình hoặc dữ liệu theo bộ này
không dùng thẳng được với bộ kia.** Nếu bạn muốn so sánh với kết quả công bố
trên SHREC'17, phải ánh xạ 22 điểm về 21 điểm và chấp nhận sai lệch. Đây là một
lý do chính đáng để đề tài chọn IPN Hand (video RGB, tự trích điểm mốc bằng
chính công cụ mình dùng) thay vì một bộ dữ liệu khung xương dựng sẵn.

### 1.4. Vì sao bàn tay khó hơn cơ thể

Bài báo nói thẳng một câu đáng nhớ: khuôn mặt có những vùng tương phản cao như
quanh mắt và miệng; bàn tay **không có đặc trưng như thế**, nên phát hiện bàn
tay chỉ từ đặc trưng thị giác khó hơn hẳn.

Cụ thể hơn, sáu khó khăn:

- **Rất nhiều bậc tự do.** Mỗi ngón có ba tới bốn khớp. Cả bàn tay khoảng 27 bậc
  tự do, nhồi trong một vùng ảnh nhỏ. Số cấu hình có thể lớn hơn nhiều so với
  thân người.
- **Tự che khuất, mức độ nặng.** Nắm tay lại thì bốn ngón che nhau hoàn toàn.
  Nhìn nghiêng thì cả bàn tay thành một khối. Đây là khó khăn lớn nhất, và nó
  đánh trực tiếp vào cử chỉ **chụm tay** của đề tài.
- **Các ngón trông giống nhau.** Ngón trỏ, ngón giữa và ngón áp út gần như không
  phân biệt được nếu nhìn riêng lẻ. Mô hình phải dựa vào ngữ cảnh toàn bàn tay
  để biết ngón nào là ngón nào.
- **Dải tỉ lệ rất rộng.** Bài báo ghi nhận bàn tay có thể xuất hiện với tỉ lệ
  chênh nhau khoảng 20 lần trong cùng một ứng dụng.
- **Nhòe chuyển động.** Ngón tay mảnh, nên khi vuốt nhanh chúng nhòe thành vệt
  sớm hơn nhiều so với thân người. Đây là khó khăn thứ hai đánh trực tiếp vào
  đề tài, lần này là cử chỉ **vuốt**.
- **Nhập nhằng độ sâu.** Từ một ảnh 2D không thể biết chắc ngón tay đang chỉ về
  phía trước hay đang gập lại. Hai tư thế đó cho hình chiếu rất giống nhau.

Ba cái cuối bạn sẽ **quan sát trực tiếp** trong thí nghiệm tuần 3 ở mục 12. Ảnh
chụp màn hình những lần mô hình đoán sai là tư liệu tốt cho báo cáo.

---

## 2. Đủ về CNN để hiểu phần còn lại

Bạn không cần biết sâu về mạng tích chập. Nhưng cần đủ để hiểu ba thứ ở các mục
sau: vì sao bộ phát hiện lại có dạng encoder–decoder, vì sao bản đồ nhiệt là
một lựa chọn tự nhiên, và vì sao mô hình bàn tay lại từ chối nó.

### 2.1. Tích chập là gì

Hình dung một **cửa sổ nhỏ**, chẳng hạn 3×3, trượt qua toàn bộ ảnh. Ở mỗi vị
trí, nó nhân từng phần tử của mình với 9 pixel bên dưới, cộng lại, ghi kết quả
ra một ảnh mới.

Cửa sổ đó gọi là **bộ lọc** (*filter*, *kernel*). Các con số trong nó quyết định
nó phát hiện cái gì. Ví dụ bộ lọc phát hiện cạnh dọc:

```
-1   0  +1
-2   0  +2
-1   0  +1
```

Ở vùng ảnh phẳng, tổng có trọng số bằng 0. Ở vùng có cạnh dọc, kết quả lớn. Ảnh
đầu ra vì thế sáng lên đúng ở chỗ có cạnh dọc.

Ba điều cần rút ra:

1. **Đầu ra vẫn là một ảnh.** Tích chập biến ảnh thành ảnh, gọi là **bản đồ đặc
   trưng** (*feature map*). Vị trí trong bản đồ đặc trưng vẫn tương ứng với vị
   trí trong ảnh gốc.
2. **Cùng một bộ lọc dùng cho mọi vị trí.** "Phát hiện cạnh dọc" học một lần,
   dùng ở khắp nơi.
3. **Các con số trong bộ lọc được học từ dữ liệu**, không do người thiết kế.

### 2.2. Xếp chồng nhiều lớp

Một lớp tích chập chỉ thấy được mảng 3×3 pixel, quá nhỏ để nhận ra bất cứ gì có
nghĩa. Nên ta xếp chồng nhiều lớp, xen kẽ các bước **giảm kích thước**
(*downsampling*).

Sau mỗi bước giảm, một ô trong bản đồ đặc trưng tương ứng với một vùng lớn hơn
trong ảnh gốc. Vùng đó gọi là **trường tiếp nhận** (*receptive field*).

Hệ quả là một sự đánh đổi xuyên suốt thị giác máy tính:

| Độ sâu | Độ phân giải | Trường tiếp nhận | Biết gì |
|---|---|---|---|
| Lớp nông | Cao | Nhỏ | "Ở đây có cạnh, có góc" — biết *ở đâu*, không biết *là gì* |
| Lớp sâu | Thấp | Lớn | "Đây là một bàn tay" — biết *là gì*, mất dần *ở đâu* |

Với bài toán định vị, ta cần **cả hai**.

### 2.3. Encoder–decoder và FPN

Cách giải quyết đánh đổi trên là kiến trúc **encoder–decoder**:

```
ảnh ──► [encoder: giảm dần độ phân giải, tăng dần ngữ nghĩa]
                              │
                              ▼
        [decoder: tăng dần độ phân giải trở lại]
                              │
                              ▼
                  đầu ra có độ phân giải cao và có ngữ nghĩa
```

Chưa đủ: sau khi đi qua encoder, thông tin vị trí chi tiết đã mất, decoder không
tự bịa lại được. Nên người ta thêm **kết nối tắt** (*skip connection*): nối
thẳng bản đồ đặc trưng độ phân giải cao ở encoder sang tầng tương ứng ở decoder.

Bài báo MediaPipe Hands nói họ dùng "bộ trích đặc trưng encoder–decoder tương tự
FPN, để có nhận thức ngữ cảnh rộng hơn ngay cả với vật nhỏ". **FPN** (*Feature
Pyramid Network*) chính là dạng encoder–decoder có kết nối tắt, áp dụng cho phát
hiện đối tượng.

Vì sao điều này quan trọng với bàn tay: lòng bàn tay ở xa chỉ chiếm vài pixel.
Nếu chỉ nhìn vài pixel đó, không đủ thông tin. Nhưng nếu biết ngữ cảnh rằng phía
dưới có cẳng tay và phía trên có năm vật mảnh, thì đoán được. FPN cho mạng cả
hai loại thông tin cùng lúc.

---

## 3. Phát hiện đối tượng một giai đoạn

Bộ phát hiện lòng bàn tay của MediaPipe là một *single-shot detector*. Muốn hiểu
ba quyết định thiết kế của nó ở mục 6, cần bốn khái niệm sau. Mỗi khái niệm chỉ
cần hiểu tới mức giải thích được bằng một đoạn văn.

### 3.1. Hai giai đoạn và một giai đoạn

**Hai giai đoạn** (họ R-CNN): bước một đề xuất vài nghìn vùng có thể chứa vật,
bước hai phân loại từng vùng. Chính xác, nhưng chậm.

**Một giai đoạn** (họ SSD, YOLO): một lần chạy mạng cho ra luôn mọi hộp và mọi
điểm số. Nhanh hơn nhiều, thường kém chính xác hơn một chút. Đây là lựa chọn bắt
buộc khi cần chạy thời gian thực trên thiết bị phổ thông.

### 3.2. Hộp mẫu (*anchor*)

Bộ phát hiện một giai đoạn không "tìm" vật. Nó **rải sẵn hàng nghìn hộp mẫu**
khắp ảnh, ở nhiều vị trí, nhiều kích thước, nhiều tỉ lệ khung. Rồi với **mỗi**
hộp mẫu, mạng dự đoán hai thứ:

1. Điểm số: hộp này có chứa vật không?
2. Độ hiệu chỉnh: cần dịch và co giãn hộp bao nhiêu để ôm sát vật thật?

Số hộp mẫu là tích của ba thừa số: số vị trí × số kích thước × số tỉ lệ khung.
Giảm được thừa số nào cũng là giảm chi phí. Ghi nhớ điều này — nó là lý do trực
tiếp cho quyết định thiết kế thứ nhất của BlazePalm.

Trong mô hình MediaPipe hiện hành, đầu ra của bộ phát hiện lòng bàn tay là hai
tensor có chiều 2016, tức khoảng hai nghìn hộp mẫu cho mỗi ảnh.

### 3.3. Triệt tiêu không cực đại (NMS)

Với hàng nghìn hộp mẫu, một bàn tay thật sẽ kích hoạt hàng chục hộp chồng lên
nhau. **NMS** (*non-maximum suppression*) dọn chuyện đó:

```
1. Sắp các hộp theo điểm số giảm dần.
2. Lấy hộp điểm cao nhất, giữ lại.
3. Xóa mọi hộp chồng lấn với nó quá một ngưỡng (thường đo bằng IoU).
4. Lặp lại với các hộp còn lại.
```

**IoU** (*Intersection over Union*) là diện tích phần giao chia cho diện tích
phần hợp của hai hộp. Bằng 1 nghĩa là trùng khít, bằng 0 nghĩa là rời nhau.

Điểm yếu của NMS: khi **hai vật thật sự chồng lên nhau**, nó có thể xóa nhầm một
vật thành hộp thừa. Với bàn tay, tình huống đó là hai người bắt tay, hoặc hai
bàn tay đan vào nhau. Ghi nhớ điều này — nó là lý do phụ cho quyết định thiết kế
thứ nhất.

### 3.4. Focal loss

Trong hai nghìn hộp mẫu, gần như tất cả đều là nền. Có thể chỉ một hoặc hai hộp
chứa bàn tay.

Với hàm mất mát thông thường (*cross-entropy*), mỗi hộp đóng góp như nhau. Hai
nghìn hộp nền "dễ" sẽ áp đảo hoàn toàn vài hộp dương "khó". Mạng học được rằng
cứ đoán "không có gì" là an toàn.

**Focal loss** thêm một thừa số làm **giảm trọng số của các mẫu đã phân loại
đúng và dễ**. Một hộp nền mà mạng đã tự tin là nền thì gần như không đóng góp
gradient nữa. Nhờ vậy mạng buộc phải tập trung vào các mẫu khó.

Bài báo ghi rõ họ tối thiểu hóa focal loss "để hỗ trợ số lượng lớn hộp mẫu sinh
ra từ dải tỉ lệ rộng".

> **Liên hệ với đề tài.** Vấn đề "lớp đa số áp đảo lớp thiểu số" mà focal loss
> giải quyết ở đây chính là vấn đề bạn sẽ gặp lại ở tầng 4 và 5, dưới dạng lớp
> "không cử chỉ" chiếm đa số. Cách giải quyết cũng cùng tinh thần: trọng số lớp
> trong hàm mất mát, và lấy mẫu con lớp đa số. Đây là một mối liên hệ đáng nêu
> trong báo cáo.

---

## 4. Bản đồ nhiệt hay hồi quy trực tiếp

Đây là mục thú vị nhất của tầng này, vì mô hình bàn tay chọn **ngược lại** với
phần lớn mô hình tư thế người.

### 4.1. Hai cách thiết kế đầu ra

Ta muốn mạng cho ra vị trí của, chẳng hạn, đầu ngón trỏ. Có hai cách.

**Cách A — hồi quy trực tiếp.** Mạng in ra đúng hai con số: `x = 0.62`,
`y = 0.31`. Đơn giản, gọn, có vẻ hiển nhiên.

**Cách B — bản đồ nhiệt.** Mạng in ra một **ảnh** cùng kích thước hoặc nhỏ hơn
ảnh vào, trong đó giá trị mỗi pixel là "độ tin rằng đầu ngón trỏ nằm ở đây". Sau
đó lấy pixel có giá trị lớn nhất làm câu trả lời. Một bản đồ nhiệt cho mỗi điểm;
với 21 điểm thì đầu ra là 21 ảnh xếp chồng.

Trực quan, một bản đồ nhiệt trông như đốm sáng mờ quanh vị trí điểm:

```
0.0  0.0  0.0  0.0  0.0
0.0  0.1  0.3  0.1  0.0
0.0  0.3  1.0  0.3  0.0     ← đỉnh ở đây = vị trí điểm mốc
0.0  0.1  0.3  0.1  0.0
0.0  0.0  0.0  0.0  0.0
```

### 4.2. Bốn lý do bản đồ nhiệt thường thắng

**Lý do 1 — Giữ được cấu trúc không gian.** Tích chập có tính *tương đẳng tịnh
tiến*: dịch vật trong ảnh vào thì bản đồ đặc trưng dịch theo đúng như vậy. Bản
đồ nhiệt **khai thác** tính chất đó, vì câu trả lời được biểu diễn ở đúng chỗ nó
nằm. Hồi quy trực tiếp thì **phá vỡ** nó: để cho ra hai con số, mạng phải làm
phẳng bản đồ đặc trưng thành vector rồi đi qua lớp nối đầy đủ, và bước làm phẳng
xóa sạch thông tin "ô này ở góc trên trái, ô kia ở giữa".

**Lý do 2 — Biểu diễn được sự không chắc chắn.** Nếu điểm mốc bị che, cách A vẫn
phải quả quyết in ra hai con số. Cách B in được một đốm **rộng và nhạt**, nghĩa
là "khoảng đâu đây nhưng tôi không chắc", hoặc **hai đốm** ở hai chỗ, nghĩa là
"hoặc đây hoặc kia". Với bàn tay nắm lại, tình huống hai đốm rất thực: mô hình
thật sự phân vân giữa ngón giữa và ngón áp út.

**Lý do 3 — Tín hiệu huấn luyện dày đặc.** Với cách A, mỗi ảnh cho mạng hai con
số để so sánh. Với cách B, **mỗi pixel** của bản đồ nhiệt đều có giá trị đúng để
so sánh, kể cả những pixel phải bằng 0. Mạng học "không, điểm không ở đây" từ
hàng nghìn vị trí cùng lúc.

**Lý do 4 — Bài toán dễ hơn về bản chất.** Hồi quy trực tiếp bắt mạng học một
ánh xạ phi tuyến **toàn cục**: từ toàn bộ ảnh sang một con số, và phải "biết đếm
pixel". Bản đồ nhiệt biến nó thành bài toán **cục bộ, lặp lại**: với mỗi vị trí,
trả lời "đầu ngón trỏ có ở đây không?". Đúng loại câu hỏi tích chập giỏi.

Nhược điểm, để công bằng: tốn bộ nhớ; có sai số lượng tử hóa vì bản đồ nhiệt
thường nhỏ hơn ảnh gốc; phép lấy cực đại không khả vi nên khó huấn luyện đầu
cuối; và cần hậu xử lý.

### 4.3. Vì sao mô hình điểm mốc bàn tay vẫn chọn hồi quy trực tiếp

Bài báo nói thẳng: sau khi chạy bộ phát hiện lòng bàn tay trên toàn ảnh, mô hình
điểm mốc "thực hiện định vị chính xác 21 tọa độ 2,5D bên trong vùng bàn tay đã
phát hiện **bằng hồi quy**".

Đây không phải sơ suất. Nó là hệ quả hợp lý của kiến trúc hai tầng, và lý do nằm
gọn trong một câu khác của bài báo:

> Cung cấp ảnh bàn tay đã cắt chính xác cho mô hình điểm mốc **làm giảm mạnh nhu
> cầu tăng cường dữ liệu** (xoay, tịnh tiến, co giãn) và cho phép mạng dành phần
> lớn năng lực của nó cho độ chính xác định vị.

Đọc lại bốn lý do ở mục 4.2 dưới ánh sáng đó:

| Lý do ủng hộ bản đồ nhiệt | Còn đúng khi đầu vào đã được cắt và căn chỉnh? |
|---|---|
| Giữ cấu trúc không gian | **Yếu đi nhiều.** Bàn tay đã chiếm gần hết vùng cắt, đã được xoay thẳng. Bài toán "ở đâu trong một ảnh nhỏ đã căn chỉnh" gần với "hình dạng bàn tay là gì" hơn là với "tìm vật trong cảnh" |
| Biểu diễn không chắc chắn | **Thay bằng thứ khác.** Mô hình có riêng một đầu ra là cờ xác suất "có bàn tay trong vùng cắt" (mục 7.1), làm đúng việc đó ở mức toàn bàn tay |
| Tín hiệu học dày đặc | **Vẫn đúng** — và đây chính là chỗ giải pháp lai xuất hiện, xem đoạn dưới |
| Bài toán dễ hơn | **Yếu đi.** Với đầu vào đã chuẩn hóa, ánh xạ từ ảnh sang 21 tọa độ không còn "toàn cục và phi tuyến" như trong ảnh toàn cảnh |

Đổi lại, chi phí của bản đồ nhiệt vẫn nguyên: 21 bản đồ nhiệt nặng hơn nhiều so
với 42 con số, trên điện thoại đó là chi phí thật; sai số lượng tử hóa vẫn có;
hậu xử lý vẫn cần.

**Kết luận: khi đầu vào đã được căn chỉnh chặt, cán cân nghiêng về hồi quy trực
tiếp.**

Có một chi tiết đáng nói thêm. Mô hình tư thế người của Google (BlazePose) giải
quyết đánh đổi này bằng cách **lai**: huấn luyện có nhánh bản đồ nhiệt để lấy
tín hiệu học dày đặc, rồi **gỡ nhánh đó đi trước khi triển khai**, chỉ giữ nhánh
hồi quy. Giữ lợi ích lúc học, bỏ chi phí lúc chạy. Nếu bạn đã đọc tài liệu tầng
2 bản cũ, đây chính là mục 5.3 của bản đó, và nó vẫn đáng nhắc trong báo cáo như
một điểm so sánh.

### 4.4. Bài học tổng quát

> Không có câu trả lời đúng tuyệt đối cho "nên thiết kế đầu ra thế nào". Câu trả
> lời phụ thuộc vào **đầu vào đã được chuẩn bị tới đâu**. Cùng một kỹ thuật,
> đúng cho bài toán này, thừa cho bài toán kia.

Đây là bài học lặp lại ở tầng 3 với chuẩn hóa xoay, và ở tầng 4 với lựa chọn mô
hình. Nó cũng là câu trả lời tốt nếu hội đồng hỏi "vì sao chỗ này dùng A mà chỗ
kia dùng B".

---

## 5. Kiến trúc hai tầng

### 5.1. Sơ đồ

```
Toàn bộ ảnh
     │
     ▼
┌──────────────────────────────────────┐
│  Bộ phát hiện lòng bàn tay BlazePalm │   đầu vào 192×192
│  → hộp bao CÓ HƯỚNG quanh lòng bàn   │
└──────────────────────────────────────┘
     │
     ▼  cắt + xoay + co giãn về khung chuẩn
┌──────────────────────────────────────┐
│  Mô hình điểm mốc bàn tay            │   đầu vào 224×224
│  ├─► 21 điểm (x, y, z)               │
│  ├─► xác suất "có tay trong vùng cắt"│
│  └─► tay trái / tay phải             │
└──────────────────────────────────────┘
```

> **Một chi tiết nhỏ đáng biết, và đáng nhắc trong báo cáo nếu bạn muốn chứng tỏ
> đã đọc kỹ.** Bài báo năm 2020 nêu kích thước đầu vào là 256×256. Các file mô
> hình TFLite đang phân phối thì dùng **192×192 cho bộ phát hiện lòng bàn tay**
> và **224×224 cho mô hình điểm mốc**. Đây là sự khác biệt giữa bài báo và bản
> triển khai đã được cộng đồng ghi nhận. Kết luận định tính ở mục 10 không đổi
> theo con số cụ thể, nhưng nếu bạn trích số trong báo cáo thì hãy trích kèm
> nguồn và nói rõ nó là của bản triển khai nào.

### 5.2. Vì sao cắt và căn chỉnh trước lại quan trọng đến thế

Đây là ý trung tâm của cả kiến trúc, và là câu trả lời cho "vì sao không làm một
mạng duy nhất?".

Nếu mô hình điểm mốc phải làm việc trên toàn ảnh, nó phải học cách xử lý bàn tay
**ở mọi vị trí, mọi kích thước, mọi góc xoay**. Đó là ba chiều biến thiên, và
mỗi chiều đòi hỏi hoặc nhiều dữ liệu tăng cường hơn, hoặc nhiều năng lực mạng
hơn, hoặc cả hai.

Khi nhận một vùng cắt đã căn chỉnh, ba chiều biến thiên đó **biến mất khỏi bài
toán của nó**. Bàn tay luôn ở giữa, luôn chiếm khoảng cùng một tỉ lệ, luôn được
xoay về cùng một hướng chuẩn. Toàn bộ năng lực mạng dành cho một việc duy nhất:
định vị chính xác 21 điểm trên một bàn tay đã được đặt ngay ngắn trước mặt nó.

Đây chính là triết lý **top-down** mà bạn đã gặp ở tài liệu tầng 2 bản cũ: tìm
đối tượng trước, tìm điểm sau. Chỉ khác là ở đó đối tượng là người, còn ở đây là
lòng bàn tay.

---

## 6. BlazePalm — bộ phát hiện lòng bàn tay

### 6.1. Ba quyết định thiết kế

Bài báo nêu ba giải pháp cho ba khó khăn. Đây là phần đáng học nhất của cả tầng,
vì nó cho thấy **cách một nhóm kỹ sư biến một khó khăn cụ thể thành một lựa chọn
kiến trúc cụ thể**.

#### Quyết định 1 — Phát hiện *lòng bàn tay*, không phải cả bàn tay

Nghe phản trực giác: ta cần cả bàn tay, sao lại đi tìm mỗi lòng bàn tay?

Ba lý do, bài báo nêu cả ba:

**(a) Lòng bàn tay gần như là vật cứng.** Bàn tay có 27 bậc tự do và thay hình
liên tục khi ngón co duỗi. Lòng bàn tay, hoặc nắm tay, thì **không đổi hình**.
Ước lượng hộp bao cho một vật cứng dễ hơn nhiều so với một vật có khớp.

**(b) Chỉ cần hộp vuông.** Vì lòng bàn tay gần vuông ở mọi tư thế, bộ phát hiện
chỉ cần **một tỉ lệ khung** cho hộp mẫu thay vì ba tới năm. Nhớ lại mục 3.2: số
hộp mẫu là tích của ba thừa số. Bỏ đi thừa số tỉ lệ khung thì **giảm số hộp mẫu
ba tới năm lần**. Đây là tiết kiệm tính toán trực tiếp, và nó là một phần lý do
mô hình chạy được thời gian thực trên điện thoại.

**(c) NMS hoạt động tốt hơn.** Lòng bàn tay là vật nhỏ hơn cả bàn tay, nên hai
hộp lòng bàn tay ít chồng lấn hơn hai hộp bàn tay. Nhờ vậy NMS tách được hai tay
ngay cả khi chúng tự che nhau, ví dụ khi hai người bắt tay.

Ba lý do này độc lập với nhau và cùng chỉ về một hướng. Đó là dấu hiệu của một
quyết định thiết kế tốt.

#### Quyết định 2 — Bộ trích đặc trưng encoder–decoder kiểu FPN

Đã giải thích ở mục 2.3. Mục đích: có nhận thức ngữ cảnh rộng ngay cả với vật
nhỏ. Với bàn tay ở xa, thông tin cục bộ không đủ; ngữ cảnh xung quanh mới cho
biết cái đốm mờ đó là bàn tay.

#### Quyết định 3 — Focal loss

Đã giải thích ở mục 3.4. Mục đích: hỗ trợ số lượng lớn hộp mẫu sinh ra từ dải tỉ
lệ rộng, không để các hộp nền dễ áp đảo.

### 6.2. Bảng khảo sát loại bỏ — mỗi quyết định đáng bao nhiêu

Bài báo có một bảng ngắn cho thấy đóng góp của từng lựa chọn, đo bằng *average
precision* của bộ phát hiện:

| Cấu hình | Average Precision |
|---|---|
| Không decoder + cross-entropy | 86,22% |
| **Có** decoder + cross-entropy | 94,07% |
| Có decoder + **focal loss** | 95,70% |

Đọc bảng này cho ta hai điều. Thêm decoder đáng khoảng 8 điểm phần trăm, đổi
sang focal loss đáng thêm khoảng 1,6 điểm nữa. Và quan trọng hơn: **đây là mẫu
mực của một thí nghiệm loại bỏ**, đúng thứ bạn sẽ tự làm ở tuần 8. Mỗi dòng đổi
đúng một yếu tố, giữ nguyên mọi thứ khác. Bảng thí nghiệm của bạn nên có hình
dạng giống hệt bảng này.

### 6.3. Hộp bao có hướng

Bộ phát hiện không trả về một hộp thẳng đứng thông thường, mà trả về **hộp bao
có hướng** (*oriented bounding box*): ngoài vị trí và kích thước, còn có góc
xoay.

Nhờ vậy bước cắt có thể xoay vùng bàn tay về một hướng chuẩn trước khi đưa vào
mô hình điểm mốc. Đây chính là cơ chế loại bỏ chiều biến thiên "góc xoay" đã nói
ở mục 5.2.

Một hệ quả thực tế cho đề tài: vì mô hình điểm mốc luôn nhìn bàn tay đã xoay
thẳng, nó khá ổn định với việc bạn nghiêng cổ tay. Nhưng tọa độ trả về thì ở hệ
quy chiếu **ảnh gốc**, không phải hệ đã xoay. Nói cách khác, thông tin về góc
nghiêng bàn tay **vẫn còn** trong đầu ra. Tầng 3 sẽ quyết định có dùng nó hay
không.

---

## 7. Mô hình điểm mốc

### 7.1. Ba đầu ra dùng chung một bộ trích đặc trưng

Bài báo liệt kê rõ:

| Đầu ra | Nội dung | Dùng để làm gì trong đề tài |
|---|---|---|
| 21 điểm mốc | `x`, `y`, và độ sâu tương đối | Toàn bộ phần phía sau |
| **Cờ hiện diện** | Xác suất có một bàn tay được căn chỉnh hợp lý trong vùng cắt | Cơ chế bám theo dùng nó; bạn dùng nó gián tiếp qua ngưỡng `min_hand_presence_confidence` |
| **Tay trái / tay phải** | Phân loại nhị phân | Đặc trưng phụ, sau khi đã kiểm chứng quy ước ở mục 9.5 |

Cờ hiện diện là chi tiết tinh tế nhất. Nó không trả lời "ảnh này có bàn tay
không" mà trả lời "**vùng cắt tôi vừa nhận có chứa một bàn tay được căn chỉnh
hợp lý không**". Sự khác biệt đó rất quan trọng: nó cho phép hệ thống phát hiện
rằng cơ chế bám theo đã trượt khỏi bàn tay, và kích hoạt chạy lại bộ phát hiện.
Xem mục 8.

### 7.2. Dữ liệu huấn luyện — ba nguồn, ba mục đích

Bài báo mô tả ba bộ dữ liệu, mỗi bộ bù khuyết điểm của bộ kia:

| Nguồn | Quy mô | Nội dung | Hạn chế |
|---|---|---|---|
| Ảnh thực ngoài đời | ~6.000 ảnh | Đa dạng địa lý, ánh sáng, hình dáng tay | Không có tư thế tay phức tạp |
| Ảnh cử chỉ tự thu | ~10.000 ảnh | Đủ mọi góc của mọi tư thế tay khả dĩ | Chỉ 30 người, nền ít thay đổi |
| Ảnh tổng hợp | ~100.000 ảnh | Dựng từ mô hình bàn tay 3D thương mại, 24 xương, 36 *blendshape*, 5 tông da, phông nền HDR ngẫu nhiên | Không phải ảnh thật |

Ba điều đáng rút ra:

**Một.** Bộ phát hiện lòng bàn tay **chỉ dùng bộ ảnh thực ngoài đời**, vì để
định vị bàn tay thì đa dạng ngoại hình quan trọng hơn đa dạng tư thế. Mô hình
điểm mốc thì dùng cả ba.

**Hai.** Kết quả thực nghiệm của họ, đo bằng MSE chuẩn hóa theo **cỡ lòng bàn
tay**:

| Dữ liệu huấn luyện | MSE chuẩn hóa theo cỡ lòng bàn tay |
|---|---|
| Chỉ ảnh thực | 16,1% |
| Chỉ ảnh tổng hợp | 25,7% |
| **Kết hợp** | **13,4%** |

Kết hợp tốt hơn hẳn từng cái riêng. Và họ ghi nhận thêm rằng huấn luyện với nhiều
ảnh tổng hợp còn làm **giảm hiện tượng rung giữa các frame**, một lợi ích không
hiện lên trong con số MSE.

**Ba, và đây là điều quan trọng nhất với tầng 3.** Để ý đơn vị đo sai số: **MSE
chuẩn hóa theo cỡ lòng bàn tay**. Chính nhóm tác giả mô hình cũng coi cỡ lòng
bàn tay là đơn vị độ dài tự nhiên của bài toán này. Khi tầng 3 chia mọi tọa độ
cho khoảng cách từ điểm 0 tới điểm 9, bạn đang dùng đúng đơn vị mà họ dùng. Đây
là một câu đáng viết vào báo cáo.

> **Lưu ý về phiên bản.** Tài liệu Hand Landmarker hiện hành của Google mô tả
> gói mô hình được huấn luyện trên "khoảng 30.000 ảnh thực cùng với nhiều mô
> hình bàn tay tổng hợp dựng trên các nền khác nhau". Con số đó khác với bài báo
> 2020. Nguyên nhân là mô hình đã được cập nhật qua nhiều phiên bản. Khi trích
> số vào báo cáo, hãy nói rõ bạn đang trích bài báo 2020 hay tài liệu hiện hành.

### 7.3. Ba biến thể mô hình

Bài báo đo ba cỡ mô hình điểm mốc:

| Biến thể | Tham số | MSE | Thời gian trên Pixel 3 |
|---|---|---|---|
| Light | 1,0 triệu | 11,83 | 6,6 ms |
| **Full** | 1,98 triệu | 10,05 | 16,1 ms |
| Heavy | 4,02 triệu | 9,82 | 36,9 ms |

Đọc bảng: từ Light lên Full, tăng gấp đôi tham số đổi lấy giảm MSE khoảng 15%.
Từ Full lên Heavy, tăng gấp đôi tham số nữa chỉ đổi lấy khoảng 2%, trong khi thời
gian tăng hơn gấp đôi. Bài báo kết luận Full là điểm đánh đổi tốt.

**Với đề tài của bạn:** gói `hand_landmarker.task` mặc định đã dùng cấu hình cân
bằng này. Bạn không cần chọn, nhưng nên hiểu rằng có một đường cong đánh đổi phía
sau, và biết chỉ ra điểm mà thêm tham số không còn đáng.

---

## 8. Bám theo giữa các frame

### 8.1. Cơ chế

Chạy bộ phát hiện trên **mọi** frame là lãng phí, vì bàn tay không dịch chuyển
nhiều giữa hai frame cách nhau 33 mili-giây. Bài báo mô tả giải pháp:

> Trong kịch bản theo vết thời gian thực, chúng tôi suy ra hộp bao cho frame hiện
> tại **từ dự đoán điểm mốc của frame trước**, nhờ đó tránh phải chạy bộ phát
> hiện ở mọi frame. Bộ phát hiện chỉ chạy ở frame đầu tiên, hoặc khi dự đoán cho
> thấy đã mất dấu bàn tay.

Nói cách khác: 21 điểm mốc của frame trước đủ để biết bàn tay đang ở đâu, nên
chúng tự sinh ra vùng cắt cho frame sau.

```
frame 1:  [phát hiện] → [điểm mốc] ──┐
                                      │ suy ra hộp
frame 2:              → [điểm mốc] ──┤
                                      │
frame 3:              → [điểm mốc] ──┤
                                      │
frame 4:  cờ hiện diện tụt thấp       │
          [phát hiện] → [điểm mốc] ───┘  ← chạy lại bộ phát hiện
```

Đây chính là **mô hình phát hiện–theo dõi** (*detection–tracking*) mà bạn đã gặp
ở tài liệu tầng 2 bản cũ với BlazePose. Cùng một ý tưởng, cùng một tác dụng, áp
dụng cho bàn tay.

### 8.2. Ba ngưỡng tin cậy, ba vai trò khác nhau

Ba tham số cấu hình của `HandLandmarkerOptions` tương ứng với ba chỗ khác nhau
trong chuỗi trên. Rất nhiều người chỉnh bừa cả ba vì không phân biệt được.

| Tham số | Kiểm soát cái gì | Tăng lên thì sao |
|---|---|---|
| `min_hand_detection_confidence` | Ngưỡng để **bộ phát hiện lòng bàn tay** chấp nhận một phát hiện | Ít phát hiện nhầm vật khác thành tay, nhưng khó bắt được tay lúc ban đầu |
| `min_hand_presence_confidence` | Ngưỡng cho **cờ hiện diện** của mô hình điểm mốc. Dưới ngưỡng thì coi như mất dấu và chạy lại bộ phát hiện | Bỏ dấu sớm hơn, chạy lại bộ phát hiện thường xuyên hơn, tốn CPU hơn nhưng ít bám nhầm vào vùng không có tay |
| `min_tracking_confidence` | Ngưỡng để coi việc **bám từ frame trước** là thành công | Dễ mất bám khi tay di chuyển nhanh |

Giá trị mặc định của cả ba là 0,5. Với đề tài này, mình khuyên **để nguyên mặc
định và đo trước khi chỉnh**. Nếu thí nghiệm ở mục 12 cho thấy tỉ lệ mất tay khi
vuốt nhanh quá cao, thì `min_tracking_confidence` là tham số đầu tiên nên thử hạ.

### 8.3. Hệ quả trực tiếp cho cử chỉ vuốt — đọc kỹ mục này

Cơ chế bám theo dựa trên giả định: **bàn tay ở frame sau nằm gần chỗ nó ở frame
trước**. Cử chỉ vuốt vi phạm chính giả định đó.

Chuỗi sự kiện khi bạn vuốt nhanh:

1. Tay dịch chuyển xa giữa hai frame liên tiếp.
2. Hộp suy ra từ frame trước không còn ôm đúng bàn tay.
3. Mô hình điểm mốc nhận một vùng cắt lệch, cờ hiện diện tụt.
4. Hệ thống coi là mất dấu, chạy lại bộ phát hiện lòng bàn tay trên **toàn ảnh
   đã thu nhỏ về 192 pixel**.
5. Nếu bàn tay lúc đó đang nhòe vì chuyển động, bộ phát hiện có thể không tìm
   thấy. Mất tay vài frame, **đúng vào giữa cử chỉ**.

Hai yếu tố cộng hưởng ở đây: bám thất bại vì dịch chuyển lớn, và phát hiện lại
thất bại vì nhòe chuyển động. Cả hai đều tệ hơn khi thiếu sáng, vì camera kéo dài
thời gian phơi sáng.

> **Đây là dự đoán lý thuyết quan trọng nhất mà bạn tự kiểm chứng được.** Thí
> nghiệm 2 ở mục 12 đo đúng hiện tượng này. Nếu số liệu của bạn xác nhận rằng tỉ
> lệ mất tay khi vuốt nhanh cao hơn hẳn khi tay đứng yên, bạn có một đoạn báo cáo
> hoàn chỉnh: nêu cơ chế từ bài báo, dự đoán hệ quả, đo bằng thực nghiệm, rồi
> giải thích vì sao đường ống của bạn cần bước vá lỗ hổng ở tầng 3.

---

## 9. Đầu ra của Hand Landmarker — đọc kỹ, bạn dùng nó mỗi ngày

### 9.1. Ba trường trả về

`detect_for_video()` trả về một đối tượng có ba trường, mỗi trường là **danh sách
theo từng bàn tay** được phát hiện:

```python
result.hand_landmarks        # [[21 điểm], ...]  tọa độ ẢNH, chuẩn hóa [0,1]
result.hand_world_landmarks  # [[21 điểm], ...]  tọa độ THẾ GIỚI, đơn vị mét
result.handedness            # [[phân loại], ...] nhãn Left/Right kèm điểm số
```

Với `num_hands=1`, mỗi danh sách có nhiều nhất một phần tử. **Luôn kiểm tra danh
sách rỗng trước khi lấy phần tử đầu**, vì frame không có tay sẽ trả về danh sách
rỗng chứ không phải `None`:

```python
if result.hand_landmarks:
    pts = result.hand_landmarks[0]
else:
    ...   # frame không có tay — lưu NaN, đừng bỏ frame (xem tầng 3)
```

### 9.2. Tọa độ chuẩn hóa và cạm bẫy tỉ lệ khung hình

Mỗi phần tử của `hand_landmarks[0]` có các thuộc tính `x`, `y`, `z`.

`x` và `y` được chuẩn hóa về đoạn `[0, 1]`, **nhưng chia cho hai số khác nhau**:

```
x_pixel = lm.x * W        # W = chiều rộng ảnh
y_pixel = lm.y * H        # H = chiều cao ảnh
```

Cạm bẫy: nếu bạn tính khoảng cách hoặc góc **trực tiếp trên `(lm.x, lm.y)`**, hai
trục có thang đo khác nhau, nên hình học bị kéo giãn theo tỉ lệ khung hình.

Cụ thể với ảnh 1280×720, tỉ lệ 16:9. Cùng một đoạn dài 100 pixel:

| Hướng đoạn | Chiều dài trên tọa độ chuẩn hóa |
|---|---|
| Nằm ngang | 100 / 1280 = 0,078 |
| Nằm dọc | 100 / 720 = 0,139 |

Cùng độ dài thật, hai con số chênh nhau gần **1,8 lần**. Mọi khoảng cách, mọi
góc, mọi vận tốc tính ra đều sai.

Tệ hơn nữa cho đề tài: **IPN Hand quay ở 640×480, tỉ lệ 4:3, còn webcam của bạn
chạy ở 1280×720, tỉ lệ 16:9.** Hệ số méo khác nhau giữa hai nguồn. Nếu quên đổi
sang pixel, mô hình huấn luyện trên IPN sẽ nhìn dữ liệu webcam của bạn qua một
phép biến dạng mà nó chưa từng thấy.

**Quy tắc:** nhân với `(W, H)` ngay khi lấy điểm mốc ra, trước mọi phép tính hình
học. Tầng 3 có hàm `to_pixels()` làm đúng việc này, và nó là dòng đầu tiên của
đường ống.

### 9.3. Trường `z` — vì sao không dùng

`z` là **độ sâu tương đối so với cổ tay**, không phải khoảng cách thật tới camera.
Giá trị âm nghĩa là gần camera hơn cổ tay, dương nghĩa là xa hơn.

Bài báo nói rõ một điều quyết định: tọa độ 2D được học từ **cả ảnh thật lẫn ảnh
tổng hợp**, nhưng thành phần độ sâu tương đối **chỉ được học từ ảnh tổng hợp**.

Lý do dễ hiểu: không ai gán nhãn được độ sâu chính xác cho một ảnh chụp thật.
Chỉ ảnh dựng từ mô hình 3D mới có độ sâu đúng. Hệ quả là `z` mang toàn bộ khoảng
cách miền giữa ảnh dựng và ảnh thật, nên kém tin cậy hơn hẳn `x` và `y`.

Ba lý do cụ thể để đề tài bỏ `z`:

1. **Nó là phỏng đoán, không phải phép đo.** Độ sâu từ một camera đơn về bản chất
   nhập nhằng.
2. **Thêm một chiều nhiễu vào dữ liệu vốn ít.** Mỗi lớp đích của IPN chỉ có 200
   cử chỉ. Thêm 21 đặc trưng nhiễu là mời gọi quá khớp.
3. **Bốn cử chỉ của đề tài phân biệt được hoàn toàn bằng hình học 2D.** Vuốt là
   chuyển động ngang trong mặt phẳng ảnh. Xòe và chụm là thay đổi khoảng cách
   giữa các đầu ngón, cũng trong mặt phẳng ảnh.

> **Đây là chỗ đáng viết một đoạn trong báo cáo**, vì nó cho thấy bạn từ chối một
> thông tin có sẵn và miễn phí *sau khi cân nhắc*, chứ không phải vì không biết
> nó tồn tại.
>
> Ngoại lệ đáng nhắc trong phần hướng phát triển: nếu sau này bạn thêm cử chỉ
> "đẩy tay về phía camera" thì `z` trở nên có ích, và lúc đó phải đánh giá lại.

### 9.4. `hand_world_landmarks` — có gì khác

Trường này cho tọa độ 3D theo **mét**, gốc đặt ở tâm hình học của bàn tay, không
phụ thuộc vị trí bàn tay trong ảnh.

Nghe hấp dẫn, nhưng có hai vấn đề với đề tài:

- Nó **đã bỏ mất** thông tin vị trí của bàn tay trong ảnh. Mà vị trí thay đổi
  theo thời gian chính là cú vuốt. Dùng trường này thì mất luôn hai lớp.
- Nó vẫn dựa trên cùng một ước lượng độ sâu kém tin cậy như `z`.

**Kết luận: dùng `hand_landmarks`, không dùng `hand_world_landmarks`.** Việc
chuẩn hóa vị trí và tỉ lệ sẽ do tầng 3 tự làm, với quyền kiểm soát đầy đủ về việc
giữ lại cái gì.

### 9.5. `handedness` và quy ước ảnh gương

`handedness[0][0]` có hai thuộc tính: `category_name` là `"Left"` hoặc `"Right"`,
và `score` là độ tin cậy.

**Cạm bẫy:** tài liệu và code mẫu của MediaPipe giả định ảnh đầu vào **đã được
lật như gương**, tức là kiểu ảnh selfie. Code mẫu chính thức có dòng `cv2.flip(
image, 1)` kèm chú thích "lật quanh trục y để nhãn tay trái/phải cho đúng".

Nhưng quy tắc của đề tài (tầng 1, và mục 5.2 của đề cương) là: **mô hình luôn
nhận ảnh không lật**, cùng quy ước với dữ liệu huấn luyện; chỉ lật bản dùng để
hiển thị. Với ảnh không lật, nhãn `handedness` có thể **ngược**.

Ba lựa chọn, xếp theo mức khuyên dùng:

1. **Không dựa vào nhãn này cho quyết định quan trọng.** Đây là lựa chọn của đề
   tài. Bốn cử chỉ đều làm được bằng một tay bất kỳ, nên không cần biết đó là tay
   nào.
2. Dùng nó như **đặc trưng phụ**, sau khi đã kiểm chứng bằng thực nghiệm ở mục 12
   xem quy ước trên máy bạn là gì.
3. Đảo nhãn bằng tay nếu thí nghiệm cho thấy nó ngược. Chỉ làm khi thật sự cần.

> **Nói rõ điều này trong phần giới hạn của báo cáo.** Nó không phải lỗi của
> MediaPipe mà là một quy ước chưa được nêu đủ rõ trong tài liệu, và việc bạn
> phát hiện ra nó bằng thực nghiệm là một điểm cộng.

---

## 10. Kích thước đầu vào cố định và chuyện khoảng cách

Đây là mục giải thích vì sao đề tài chốt kịch bản **ngồi trước laptop** chứ không
phải đứng thuyết trình.

### 10.1. Ảnh bị thu nhỏ trước khi vào bộ phát hiện

Bộ phát hiện lòng bàn tay nhận ảnh **192×192**. Toàn bộ frame, dù là 1280×720 hay
3840×2160, đều bị thu nhỏ về kích thước đó trước khi phát hiện.

Hệ quả đi ngược trực giác của nhiều người:

> **Đổi sang webcam độ phân giải cao hơn gần như không giúp gì cho bước phát hiện
> bàn tay.** Thứ quyết định là **bàn tay chiếm bao nhiêu phần khung hình**, tức
> là khoảng cách và góc nhìn của camera.

Độ phân giải cao chỉ giúp ở bước thứ hai, khi vùng bàn tay đã được cắt ra và đưa
vào mô hình điểm mốc ở 224×224 — lúc đó nhiều pixel gốc hơn thì vùng cắt nét hơn.
Nhưng nếu bước một đã không tìm thấy tay thì bước hai không bao giờ chạy.

### 10.2. Bảng ước lượng

Giả sử vùng nhìn ngang của webcam laptop rộng khoảng 1,3 lần khoảng cách, và bàn
tay dài khoảng 18 cm:

| Khoảng cách | Bàn tay trong frame 1280 px | Bàn tay trong ảnh 192 px | Lòng bàn tay trong ảnh 192 px |
|---|---|---|---|
| 0,4 m | ~450 px | ~68 px | ~34 px |
| **0,6 m** (ngồi làm việc) | ~300 px | ~45 px | ~22 px |
| 1,0 m | ~180 px | ~27 px | ~13 px |
| 2,0 m | ~90 px | ~13 px | ~7 px |
| 3,0 m (đứng thuyết trình) | ~60 px | ~9 px | ~5 px |

Cột cuối là cột quan trọng, vì bộ phát hiện tìm **lòng bàn tay** chứ không phải
cả bàn tay. Ở 2 tới 3 mét, lòng bàn tay chỉ còn năm tới bảy pixel trong ảnh đầu
vào. Không bộ phát hiện nào làm việc đáng tin ở kích thước đó.

**Các con số trên là ước lượng, không phải số đo.** Chúng dùng để giải thích cơ
chế, không dùng để trích vào báo cáo như kết quả. Thí nghiệm 1 ở mục 12 sẽ cho
bạn số thật trên máy của bạn.

### 10.3. Vì sao mô hình tư thế người không bị nặng như vậy

Câu hỏi tự nhiên: nếu bàn tay ở 3 mét chỉ còn vài pixel, sao MediaPipe Pose vẫn
bám được người ở 3 mét?

Vì bộ phát hiện của mô hình tư thế người tìm **cả người**, một vật lớn hơn lòng
bàn tay hàng chục lần. Ở 3 mét, người vẫn chiếm phần lớn chiều cao khung hình.
Sau khi tìm được người, mô hình tư thế suy ra vị trí cổ tay từ cấu trúc toàn thân
chứ không cần nhìn rõ bàn tay.

Đó là lý do phương án dùng Pose hợp với người đứng xa, còn Hand Landmarker hợp
với người ngồi gần. Và vì cử chỉ xòe, chụm đòi hỏi thông tin từng ngón mà Pose
không có, đề tài chốt kịch bản ngồi gần.

> **Phương án lai, dành cho phần hướng phát triển.** Dùng Pose để định vị cổ tay,
> cắt một vùng vuông quanh bàn tay từ frame gốc, rồi đưa vùng cắt đó vào Hand
> Landmarker. Khi ấy bàn tay lấp gần đầy ảnh 192 px nên bước phát hiện không còn
> là nút thắt; giới hạn chỉ còn là số pixel thật của bàn tay. Ý tưởng "khoanh
> vùng trước, nhận dạng sau" này trùng với chiến lược ước lượng vùng cử chỉ mà
> nhóm LD-ConGR đề xuất cho cử chỉ ở xa, nên bạn trích dẫn được.

---

## 11. Giới hạn cần biết — và nên viết vào báo cáo

**Chỉ một bàn tay.** `num_hands` mặc định là 1, và đề tài giữ nguyên. Nếu có bàn
tay thứ hai vào khung hình, hệ thống có thể nhảy sang bám tay đó. Kiểm soát điều
này khi quay dữ liệu và khi demo.

**Tự che khuất là nguồn lỗi chính.** Khi các ngón chụm lại, chúng che nhau. Mô
hình vẫn cho ra 21 tọa độ, nhưng vị trí các đầu ngón bị che là **phỏng đoán từ
cấu trúc bàn tay**, không dựa trên bằng chứng thị giác tại vị trí đó. Điều này
đánh trực tiếp vào lớp `zoom_out` của đề tài.

**Nhòe chuyển động cộng hưởng với cơ chế bám theo.** Đã phân tích ở mục 8.3. Đây
là lý do kỹ thuật thật của yêu cầu "đủ sáng" trong giao thức quay dữ liệu, và nó
nghe thuyết phục hơn nhiều so với "cho ảnh đẹp".

**Nhập nhằng độ sâu.** Ngón tay chỉ thẳng về phía camera trông rất giống ngón tay
gập lại. Đề tài tránh được bằng cách không dùng cử chỉ nào theo chiều sâu.

**Khoảng cách.** Đã phân tích ở mục 10. Nên giữ khoảng cách quay dữ liệu nhất
quán với khoảng cách demo.

**Nhãn tay trái/phải theo quy ước ảnh gương.** Đã phân tích ở mục 9.5.

**Bàn tay ở rìa khung hình.** Khi bàn tay bị cắt một phần bởi mép ảnh, hộp bao
không đầy đủ và điểm mốc lệch. Với camera laptop, tay đặt trên bàn phím thường
nằm dưới mép dưới khung hình. Đề tài **biến hạn chế này thành tính năng**: hạ tay
xuống là thao tác xóa trạng thái của logic kích hoạt (tầng 6).

---

## 12. Thí nghiệm quan sát cho tuần 3

Đề cương dành tuần 3 cho lý thuyết kèm quan sát. Đây là danh sách thí nghiệm cụ
thể. Viết một script ghi mỗi frame ra CSV: thời điểm, có tay hay không, 21 điểm,
nhãn tay, điểm tin cậy. Mỗi thí nghiệm 10 tới 20 giây.

| # | Thí nghiệm | Đo cái gì | Kiểm chứng ý nào |
|---|---|---|---|
| 1 | Tay đứng yên ở 0,3 / 0,5 / 0,7 / 1,0 m | Tỉ lệ frame phát hiện được tay; độ rung của đầu ngón trỏ tính bằng pixel | Mục 10 |
| 2 | **Vuốt chậm và vuốt nhanh ở cùng khoảng cách** | Tỉ lệ phát hiện *trong lúc* vuốt; số lần mất tay; độ dài đợt mất dài nhất | **Mục 8.3 — thí nghiệm quan trọng nhất** |
| 3 | Xòe và chụm liên tục | Tỉ lệ phát hiện ở tư thế chụm so với tư thế xòe | Mục 1.4, mục 11 |
| 4 | Phòng sáng và phòng tối | FPS xử lý; tỉ lệ phát hiện khi vuốt nhanh | Mục 8.3 |
| 5 | Tay trước mặt, tay trên bàn phím, tay cầm cốc | Có phát hiện không; điểm mốc có hợp lý không | Mục 11, và chuẩn bị cho lớp nền ở tầng 6 |
| 6 | Giơ tay phải rồi tay trái, với ảnh không lật và ảnh đã lật | Nhãn `Left` / `Right` trả về trong bốn trường hợp | **Mục 9.5 — cho ra một hằng số bạn dùng suốt đồ án** |
| 7 | Đưa tay ra khỏi khung rồi vào lại | Mất bao nhiêu frame để điểm mốc xuất hiện lại | Mục 8.1 — quan sát trực tiếp lúc bộ phát hiện chạy lại |
| 8 | Nghiêng cổ tay 45° và 90° | Điểm mốc còn đúng không | Mục 6.3 — hộp bao có hướng |

Với mỗi thí nghiệm, kết quả phải là **một con số hoặc một đồ thị**, không phải
một nhận xét bằng mắt. Đồ thị đáng vẽ nhất: tỉ lệ phát hiện theo khoảng cách, vẽ
hai đường cho tay đứng yên và tay vuốt nhanh trên cùng một hình.

Sản phẩm tuần 3 theo đề cương là bảng số liệu kèm ảnh minh họa các ca đoán sai.
Bảng trên chính là dàn ý cho phần đó.

---

## Tự kiểm tra

Câu 1 và câu 2 là hai câu chính của tầng này. Nếu chỉ trả lời được hai câu, hãy
là hai câu đó.

1. **Nêu ba lý do độc lập vì sao MediaPipe phát hiện *lòng bàn tay* thay vì cả
   bàn tay.** Lý do nào trong ba lý do đó tiết kiệm tính toán trực tiếp, và tiết
   kiệm bằng cơ chế gì?

2. **Vì sao mô hình điểm mốc bàn tay hồi quy trực tiếp ra tọa độ, trong khi nhiều
   mô hình tư thế người dùng bản đồ nhiệt?** Trả lời bằng cách chỉ ra điều gì đã
   thay đổi ở *đầu vào* của nó.

3. Nêu bốn lý do bản đồ nhiệt thường thắng hồi quy trực tiếp, và hai nhược điểm
   của bản đồ nhiệt.

4. Hệ thống làm gì để không phải chạy bộ phát hiện lòng bàn tay ở mọi frame? Bạn
   quan sát được hệ quả của thiết kế này bằng cách nào, chỉ bằng mắt?

5. **Vì sao tỉ lệ mất tay khi vuốt nhanh cao hơn khi xòe tay tại chỗ?** Nêu đủ
   hai cơ chế cộng hưởng.

6. `lm.x = 0.5`, `lm.y = 0.5` trên ảnh 1280×720. Tọa độ pixel là bao nhiêu? Nếu
   bạn tính khoảng cách giữa hai điểm mốc trực tiếp trên `(lm.x, lm.y)` mà không
   nhân `W, H` thì sai ở đâu, và vì sao sai lệch đó **khác nhau** giữa IPN Hand
   và webcam của bạn?

7. Vì sao khuyên không dùng `lm.z` trong đồ án này, dù nó có sẵn và miễn phí? Nêu
   một trường hợp mà lời khuyên đó sẽ phải xem lại.

8. Đổi webcam 720p sang 4K có giúp phát hiện bàn tay ở khoảng cách 3 mét không?
   Giải thích bằng cơ chế, không bằng cảm tính.

9. Ba tham số `min_hand_detection_confidence`, `min_hand_presence_confidence`,
   `min_tracking_confidence` kiểm soát ba chỗ khác nhau. Chỗ nào là chỗ nào?

10. Bạn giơ **tay phải thật** của mình lên trước webcam, ảnh không lật, và
    MediaPipe trả về nhãn `Left`. Đây có phải lỗi không? Bạn nên làm gì?

<details>
<summary>Đáp án gợi ý</summary>

1. (a) **Lòng bàn tay gần như là vật cứng**, không đổi hình khi ngón co duỗi, nên
   ước lượng hộp bao dễ hơn nhiều so với một vật có khớp. (b) **Chỉ cần hộp
   vuông**, tức là chỉ một tỉ lệ khung cho hộp mẫu thay vì ba tới năm — đây là lý
   do tiết kiệm tính toán trực tiếp, và cơ chế là giảm số hộp mẫu ba tới năm lần,
   vì số hộp mẫu bằng tích của số vị trí, số kích thước và số tỉ lệ khung. (c)
   **NMS hoạt động tốt hơn** vì lòng bàn tay nhỏ hơn nên hai hộp ít chồng lấn hơn,
   tách được hai tay ngay cả khi chúng tự che nhau.

2. Điều thay đổi là **đầu vào đã được cắt và căn chỉnh chặt** bởi bộ phát hiện:
   bàn tay luôn ở giữa vùng cắt, luôn chiếm khoảng cùng một tỉ lệ, luôn được xoay
   về hướng chuẩn nhờ hộp bao có hướng. Ba trong bốn lý do ủng hộ bản đồ nhiệt vì
   thế yếu đi: cấu trúc không gian ít quan trọng hơn khi vật đã được đặt ngay
   ngắn; việc biểu diễn không chắc chắn đã có một đầu ra riêng đảm nhận, là cờ
   hiện diện; và bài toán không còn là ánh xạ toàn cục phi tuyến nữa. Trong khi
   đó chi phí của bản đồ nhiệt vẫn nguyên: bộ nhớ, sai số lượng tử hóa, hậu xử
   lý. Cán cân vì thế nghiêng về hồi quy trực tiếp.

3. Bốn lý do: giữ cấu trúc không gian nhờ tính tương đẳng tịnh tiến của tích
   chập; biểu diễn được sự không chắc chắn bằng đốm rộng hoặc hai đốm, và đây
   cũng là nguồn của điểm tin cậy; tín hiệu học dày đặc vì mỗi pixel cho một tín
   hiệu gradient thay vì chỉ hai con số mỗi ảnh; bài toán cục bộ lặp lại dễ hơn
   ánh xạ toàn cục. Hai nhược điểm bất kỳ trong: tốn bộ nhớ, sai số lượng tử hóa,
   phép lấy cực đại không khả vi, cần hậu xử lý.

4. Nó suy ra hộp bao cho frame hiện tại **từ 21 điểm mốc của frame trước**, và
   chỉ chạy lại bộ phát hiện khi cờ hiện diện tụt dưới ngưỡng. Quan sát bằng mắt:
   đưa tay ra khỏi khung rồi vào lại, sẽ thấy một độ trễ ngắn trước khi điểm mốc
   xuất hiện — đó chính là lúc bộ phát hiện phải chạy lại trên toàn ảnh.

5. Cơ chế một: **bám thất bại**. Cơ chế bám giả định bàn tay ở frame sau nằm gần
   chỗ nó ở frame trước; vuốt nhanh vi phạm giả định đó, hộp suy ra không còn ôm
   đúng tay, cờ hiện diện tụt, hệ thống coi là mất dấu. Cơ chế hai: **phát hiện
   lại thất bại**. Khi đó bộ phát hiện phải chạy trên toàn ảnh thu nhỏ về 192 px,
   và bàn tay lúc này đang nhòe vì chuyển động nhanh, ngón tay mảnh nên nhòe sớm.
   Hai cơ chế cộng hưởng, và cả hai đều tệ hơn khi thiếu sáng vì camera kéo dài
   thời gian phơi sáng.

6. `x = 0,5 × 1280 = 640`, `y = 0,5 × 720 = 360`. Nếu không nhân: `x` đã chia cho
   1280 còn `y` chia cho 720, hai thang khác nhau, nên hình học bị kéo giãn theo
   tỉ lệ khung hình; một đoạn nằm ngang và một đoạn nằm dọc cùng độ dài thật cho
   hai giá trị khác nhau, ở đây chênh gần 1,8 lần. Sai lệch khác nhau giữa hai
   nguồn vì **IPN Hand là 4:3 còn webcam của bạn là 16:9**, nên hệ số méo khác
   nhau. Mô hình huấn luyện trên nguồn này sẽ nhìn nguồn kia qua một phép biến
   dạng nó chưa từng thấy.

7. Vì `z` là **phỏng đoán chứ không phải phép đo** — độ sâu từ camera đơn về bản
   chất nhập nhằng, và bài báo nói rõ thành phần độ sâu chỉ được học từ ảnh tổng
   hợp nên mang toàn bộ khoảng cách miền giữa ảnh dựng và ảnh thật. Thêm 21 đặc
   trưng nhiễu vào dữ liệu chỉ có 200 cử chỉ mỗi lớp là mời gọi quá khớp. Và bốn
   cử chỉ của đề tài phân biệt được hoàn toàn bằng hình học 2D. Trường hợp phải
   xem lại: nếu thêm cử chỉ theo chiều sâu, ví dụ đẩy tay về phía camera hoặc kéo
   tay về.

8. **Không giúp đáng kể.** Bộ phát hiện nhận ảnh 192×192, nên mọi frame đều bị
   thu nhỏ về kích thước đó trước khi phát hiện. Thứ quyết định là bàn tay chiếm
   bao nhiêu phần khung hình, tức khoảng cách và góc nhìn. Ở 3 mét, lòng bàn tay
   chỉ còn khoảng năm pixel trong ảnh 192 px, dù camera gốc là 720p hay 4K. Độ
   phân giải cao chỉ giúp ở bước thứ hai, khi vùng tay đã được cắt — nhưng nếu
   bước một không tìm thấy tay thì bước hai không bao giờ chạy.

9. `min_hand_detection_confidence` là ngưỡng để **bộ phát hiện lòng bàn tay**
   chấp nhận một phát hiện. `min_hand_presence_confidence` là ngưỡng cho **cờ hiện
   diện** do mô hình điểm mốc trả về; dưới ngưỡng thì coi như mất dấu và chạy lại
   bộ phát hiện. `min_tracking_confidence` là ngưỡng để coi việc **bám từ frame
   trước** là thành công.

10. **Không phải lỗi.** Tài liệu và code mẫu của MediaPipe giả định ảnh đầu vào đã
    được lật như gương, kiểu selfie; với ảnh không lật, nhãn có thể ngược. Nên
    làm: ghi nhận quy ước thực tế trên máy bạn bằng thí nghiệm 6 ở mục 12, không
    dựa vào nhãn này cho quyết định quan trọng vì bốn cử chỉ đều làm được bằng
    tay bất kỳ, và nêu điều này trong phần giới hạn của báo cáo.

</details>

---

## Đưa gì vào báo cáo

Đây là mục dài nhất và giá trị nhất của chương 2. Khoảng 4 tới 6 trang cho
**2.2 Ước lượng tư thế bàn tay**.

**2.2.1 Bài toán và định nghĩa.** Điểm mốc, khung xương bàn tay, bảng 21 điểm và
bố cục theo Simon và cộng sự, các bộ điểm mốc khác nhau giữa các nguồn dữ liệu,
và sáu khó khăn đặc thù của bàn tay ở mục 1.4. Nhấn mạnh hai khó khăn đánh trực
tiếp vào đề tài: tự che khuất khi chụm tay, và nhòe chuyển động khi vuốt.

**2.2.2 Thiết kế đầu ra: bản đồ nhiệt hay hồi quy.** Mục có giá trị học thuật
cao nhất. Trình bày cả hai cách, bốn lý do bản đồ nhiệt thường thắng, nhược điểm
của nó, rồi **giải thích vì sao mô hình bàn tay vẫn chọn hồi quy trực tiếp** —
bằng bảng đối chiếu ở mục 4.3. Kết bằng bài học tổng quát ở mục 4.4. Nếu viết tốt,
mục này một mình đã cho thấy bạn đọc hiểu bài báo chứ không chép lại.

**2.2.3 BlazePalm và kiến trúc hai tầng.** Sơ đồ hai tầng, ba quyết định thiết kế
với lý do của từng cái, bảng khảo sát loại bỏ ở mục 6.2, hộp bao có hướng, và
mục 5.2 về vì sao cắt trước lại quan trọng.

**2.2.4 Mô hình điểm mốc và cơ chế bám theo.** Ba đầu ra, ba nguồn dữ liệu huấn
luyện và bảng MSE, ba biến thể mô hình, mô hình phát hiện–theo dõi, ba ngưỡng tin
cậy. Kết bằng mục 8.3 về hệ quả với cử chỉ vuốt, nối sang chương 5.

**2.2.5 Định dạng đầu ra và giới hạn.** Ba trường trả về, tọa độ chuẩn hóa và cạm
bẫy tỉ lệ khung hình, vì sao bỏ `z` và `hand_world_landmarks`, quy ước ảnh gương
của `handedness`, và toàn bộ mục 11.

**Hình nên vẽ:**

1. **Sơ đồ kiến trúc hai tầng** — dễ vẽ, và thể hiện ngay rằng bạn nắm được cấu
   trúc hệ thống mình dùng.
2. **Một khung hình từ dữ liệu của bạn**, có khung xương 21 điểm vẽ đè, các điểm
   được đánh số, và đoạn 0–9 được tô đậm. Đây là hình "của bạn", không phải hình
   chép từ bài báo.
3. **Đồ thị tỉ lệ phát hiện theo khoảng cách**, hai đường cho tay đứng yên và tay
   vuốt nhanh, từ thí nghiệm 1 và 2 ở mục 12. Đây là hình lý giải lựa chọn công
   nghệ và lựa chọn kịch bản.
4. Ảnh minh họa các ca đoán sai: tay chụm bị che khuất, tay nhòe khi vuốt, tay ở
   rìa khung hình.

**Ba câu nên có trong báo cáo**, mỗi câu là một lý do kỹ thuật chứ không phải một
lý do tiện lợi:

> "Chúng tôi chọn Hand Landmarker thay vì Pose Landmarker vì bốn cử chỉ của hệ
> thống bao gồm hai cử chỉ dựa trên hình dạng ngón tay, mà biểu diễn 33 điểm toàn
> thân chỉ có ba điểm thô cho mỗi bàn tay nên không mô tả được."

> "Kiến trúc hai tầng phát hiện–theo dõi của MediaPipe Hands cho phép đạt thời
> gian thực trên CPU máy tính phổ thông không GPU, phù hợp với ràng buộc triển
> khai của đề tài."

> "Kịch bản người dùng ngồi trước máy tính được chọn dựa trên số liệu đo được ở
> mục [X]: do bộ phát hiện lòng bàn tay làm việc trên ảnh đã thu nhỏ về 192
> pixel, tỉ lệ phát hiện suy giảm nhanh theo khoảng cách, và mức suy giảm này
> không khắc phục được bằng cách tăng độ phân giải camera."

---

## Nguồn

| Nguồn | Dùng cho mục |
|---|---|
| Zhang F. và cộng sự, *MediaPipe Hands: On-device Real-time Hand Tracking*, arXiv:2006.10214, 2020 | 1, 4, 6, 7, 8 — nguồn của mọi con số trừ chỗ ghi khác |
| Tài liệu *Hand landmarks detection guide*, Google AI Edge | 7.2, 8.2, 9 |
| Simon T. và cộng sự, *Hand Keypoint Detection in Single Images using Multiview Bootstrapping*, CVPR 2017 | 1.1 — bố cục 21 điểm |
| Liu W. và cộng sự, *SSD: Single Shot MultiBox Detector*, 2016 | 3.1, 3.2 |
| Lin T.-Y. và cộng sự, *Focal Loss for Dense Object Detection*, 2017 | 3.4 |
| Lin T.-Y. và cộng sự, *Feature Pyramid Networks for Object Detection*, 2017 | 2.3 |
| Kích thước đầu vào của bản TFLite hiện hành (192×192 và 224×224) | 5.1, 10 — ghi nhận từ kho mã và thảo luận của MediaPipe; khác con số 256×256 trong bài báo |
| Liu D. và cộng sự, *LD-ConGR*, CVPR 2022 | 10.3 — chiến lược khoanh vùng cử chỉ ở xa |
