# Phase 6 và Phase 7 — đã làm được gì, giải thích cho người không chuyên

**Đề tài:** Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính.

**Cập nhật:** 2026-10-20

**Phạm vi:** hai giai đoạn gần nhất.

- **Phase 6** dạy máy tính nhận cử chỉ bằng mô hình học máy đầu tiên, gọi là *rừng ngẫu
  nhiên*.
- **Phase 7** dạy một mô hình mạnh hơn, gọi là *LSTM*.

Cả hai đều được đem ra thử trực tiếp trên webcam. Mỗi lần thử lộ ra một vấn đề, và tài liệu
kể lại vấn đề đó đã được tìm ra và xử lý thế nào.

**Cách đọc:**

- Tài liệu viết cho người **chưa biết gì về học máy**. Mỗi khái niệm được giải thích ngay chỗ
  nó xuất hiện lần đầu, trong một khung "**Khái niệm**".
- Bảng thuật ngữ ở Phụ lục A.
- Phụ lục B dành cho người làm kỹ thuật: số liệu lấy ở đâu, lệnh nào tạo ra chúng.

**Tài liệu liên quan:**

- Các giai đoạn trước (Phase 0–5): `docs/tong-ket-den-phase-5.md`.
- Phân tích chi tiết, nhiều số liệu hơn: `results/phase6/notes.md` và `results/phase7/notes.md`.

---

## 1. Bối cảnh: hệ thống "nhìn" bàn tay như thế nào

Trước khi vào Phase 6, cần biết hệ thống đã có gì.

### 1.1. Từ hình ảnh camera đến 21 điểm trên bàn tay

Hệ thống không xử lý trực tiếp từng điểm ảnh của camera. Một công cụ có sẵn của Google là
**MediaPipe** tìm bàn tay trong mỗi khung hình, rồi trả về **21 điểm mốc**: cổ tay, các khớp
và đầu của năm ngón tay. Mỗi điểm chỉ là một cặp toạ độ (ngang, dọc) trên ảnh.

Từ đây trở đi, "bàn tay" với hệ thống chỉ còn là **21 điểm chuyển động theo thời gian**, giống
một hình que đang cử động.

### 1.2. Cửa sổ 1,2 giây

Một cử chỉ là một chuyển động, nên không thể nhận ra từ một khung hình. Hệ thống xét từng
**cửa sổ** dài 1,2 giây, tức là 18 thời điểm cách nhau đều đặn.

Cứ mỗi 0,2 giây, nó lấy 1,2 giây gần nhất và hỏi: "trong đoạn này có cử chỉ nào không?" Vì
vậy mỗi giây có 5 câu trả lời.

### 1.3. Năm lớp cần nhận

Mỗi cửa sổ được xếp vào một trong năm **lớp**:

| Lớp | Cử chỉ | Lệnh muốn phát |
|---|---|---|
| `swipe_left` | Hất tay sang trái | Slide trước |
| `swipe_right` | Hất tay sang phải | Slide sau |
| `zoom_in` | Mở ngón cái và ngón trỏ ra | Phóng to |
| `zoom_out` | Chụm ngón cái và ngón trỏ lại | Thu nhỏ |
| `none` | Mọi thứ khác: tay nghỉ, gõ phím, chỉ trỏ, gãi đầu… | Không làm gì |

Lớp `none` là lớp khó nhất. Nó gồm **mọi** chuyển động không phải bốn cử chỉ trên, và trong
thực tế phần lớn thời gian người dùng không làm cử chỉ nào.

### 1.4. Dữ liệu IPN Hand

Để học, hệ thống cần **ví dụ có đáp án**. Dự án dùng bộ dữ liệu công khai **IPN Hand**:

- 200 video của 50 người;
- mỗi đoạn trong video đã được gán sẵn tên cử chỉ (14 loại);
- 4 loại được dự án dùng làm bốn cử chỉ ở trên, 10 loại còn lại gộp vào `none`. Trong 10 loại
  đó có cả "chỉ trỏ bằng một ngón" và "chỉ trỏ bằng hai ngón", sẽ được nhắc nhiều ở dưới.

Từ dữ liệu này, hệ thống cắt ra hàng chục nghìn cửa sổ 1,2 giây, mỗi cửa sổ kèm đáp án.

### 1.5. Mười lăm con số tóm tắt một cửa sổ

Với mô hình luật (Phase 5) và rừng ngẫu nhiên (Phase 6), mỗi cửa sổ được tóm tắt thành **15
con số**, gọi là **đặc trưng**. Ví dụ:

- cổ tay dời ngang bao xa (`dx`) và nhanh nhất là bao nhiêu (`max_vx`);
- khoảng cách giữa đầu ngón cái và đầu ngón trỏ thay đổi bao nhiêu (`pinch_delta`,
  `pinch_range`);
- bàn tay xòe ra hay khép lại bao nhiêu (`open_range`).

Mọi khoảng cách được đo bằng đơn vị **"lòng bàn tay"**: khoảng cách từ cổ tay tới gốc ngón
giữa. Nhờ vậy, tay ở gần hay xa camera đều đo như nhau.

### 1.6. Trước Phase 6: mô hình luật

Phase 5 đã có một hệ thống chạy được từ đầu đến cuối, dùng **luật do người viết**. Ví dụ:
"nếu cổ tay đi ngang đủ nhanh và đủ xa thì là vuốt; nếu ngón cái–trỏ mở ra đủ nhiều thì là
zoom in". Các ngưỡng "đủ nhanh, đủ xa" được chọn từ dữ liệu.

Mô hình luật chạy được nhưng rất yếu: điểm macro-F1 (giải thích ở mục 2.3) chỉ **0,23**, và
gần một nửa số lúc không có cử chỉ bị báo nhầm thành cử chỉ.

---

## 2. Ba khái niệm nền của học máy

### 2.1. Học máy là học từ ví dụ

> **Khái niệm — Học máy và mô hình.** Thay vì người viết luật, ta cho máy xem rất nhiều ví dụ
> có đáp án ("cửa sổ này là vuốt trái", "cửa sổ này là `none`"…) và để máy **tự tìm ra quy
> luật**. Thứ máy tìm ra gọi là **mô hình**: đưa vào một cửa sổ mới, mô hình trả ra một lớp,
> kèm **độ tin** (từ 0 đến 1) cho biết nó chắc chắn đến đâu.
>
> Quá trình cho máy xem ví dụ gọi là **huấn luyện**.

### 2.2. Ba tập dữ liệu, và vì sao phải chia theo người

> **Khái niệm — Tập huấn luyện, tập kiểm định, tập kiểm tra.** Dữ liệu được chia làm ba phần,
> giống việc học ở trường:
>
> - **Tập huấn luyện** (*train*, 30 người) là **bài tập về nhà**: máy học từ đây.
> - **Tập kiểm định** (*val*, 7 người) là **đề thi thử**: dùng để chấm điểm và chọn cách làm
>   trong quá trình phát triển.
> - **Tập kiểm tra** (*test*, 13 người) là **đề thi thật, được niêm phong**: chỉ mở đúng một
>   lần, ở cuối dự án. Nếu nhìn đề thi thật rồi sửa mô hình cho hợp đề, điểm cuối kỳ sẽ đẹp
>   giả. Dự án có một **cái khoá kỹ thuật**: script đánh giá từ chối mở tập kiểm tra nếu không
>   ghi rõ đây là lần cuối, và mỗi lần mở đều để lại một dòng nhật ký.
>
> **Đến nay, tập kiểm tra chưa bị mở lần nào.**

**Vì sao chia theo người, không chia ngẫu nhiên.** Mỗi người làm cử chỉ theo một kiểu riêng.
Nếu cùng một người có mặt ở cả bài tập về nhà lẫn đề thi, máy có thể "nhận ra người quen" thay
vì nhận ra cử chỉ, và điểm thi sẽ cao một cách giả tạo. Chia theo người buộc mô hình phải đúng
với **người nó chưa từng thấy**, giống như khi bạn dùng nó.

**Tập kiểm định giữ đúng tỉ lệ ngoài đời.** Trong 11 038 cửa sổ của tập kiểm định, 96,5% là
`none`, đúng như thực tế: phần lớn thời gian ta không làm cử chỉ. Mỗi cử chỉ chỉ có khoảng
**100 cửa sổ**. Con số nhỏ này quan trọng ở mục 4.5.

### 2.3. Đo xem mô hình tốt tới đâu

> **Khái niệm — Bắt được và báo đúng (recall và precision).** Hãy nghĩ tới một **chuông báo
> cháy**:
>
> - **Tỉ lệ bắt được** (*recall*): trong các đám cháy thật, chuông kêu được bao nhiêu phần? Bỏ
>   sót đám cháy là tệ.
> - **Tỉ lệ báo đúng** (*precision*): trong các lần chuông kêu, bao nhiêu lần là cháy thật?
>   Chuông kêu bừa là phiền.
>
> Một chuông lúc nào cũng kêu thì bắt được 100% đám cháy, nhưng báo đúng gần 0%. Một chuông
> không bao giờ kêu thì không bao giờ báo nhầm, nhưng vô dụng. Cần cả hai.

**Ví dụ thật,** với lớp `swipe_left` trên tập kiểm định của rừng ngẫu nhiên (Phase 6):

- Có 104 cửa sổ vuốt trái thật. Mô hình bắt được 56, tức **tỉ lệ bắt được 54%**.
- Mô hình nói "vuốt trái" tổng cộng 424 lần, nhưng chỉ 56 lần đúng: 366 lần còn lại thực ra
  là `none`. Vậy **tỉ lệ báo đúng chỉ 13%**.

> **Khái niệm — Điểm F1 và macro-F1.**
>
> - **F1** gộp hai tỉ lệ trên thành một điểm từ 0 đến 1. Muốn F1 cao thì phải cao **cả hai**:
>   chỉ cần một tỉ lệ thấp là F1 thấp. Vuốt trái ở ví dụ trên có F1 là 0,21.
> - **macro-F1** là **trung bình F1 của năm lớp**, mỗi lớp nặng như nhau. Đây là điểm chính
>   dùng để so các mô hình trong dự án.
>
> Vì sao không dùng "tỉ lệ đoán đúng" thông thường? Vì một mô hình lười, lúc nào cũng đoán
> `none`, đã đúng 96,5% cửa sổ, mà hoàn toàn vô dụng. macro-F1 phạt mô hình đó nặng, vì F1
> của bốn lớp cử chỉ đều bằng 0.

> **Khái niệm — Đường cơ sở.** Hai mô hình "ngốc" để làm mốc: **luôn đoán `none`** (macro-F1
> 0,196) và **đoán ngẫu nhiên** (0,080). Mô hình nào không vượt hai mốc này thì chưa học được
> gì.

> **Khái niệm — Ma trận nhầm lẫn.** Một bảng 5 × 5: hàng là lớp thật, cột là lớp mô hình đoán.
> Ô trên đường chéo là đoán đúng, ô ngoài đường chéo cho biết **lớp nào bị nhầm thành lớp
> nào**. Ví dụ ô "thật là `none`, đoán là `swipe_left`" của rừng ngẫu nhiên là 366.

### 2.4. Đo theo cửa sổ và đo theo cử chỉ

Mỗi cử chỉ kéo dài vài cửa sổ liền nhau, vì cứ 0,2 giây lại có một cửa sổ mới. Nên có hai
cách đếm:

- **Theo cửa sổ:** từng câu trả lời 0,2 giây một. Các điểm F1 ở trên tính theo cách này.
- **Theo cử chỉ** (*mức sự kiện*): một cử chỉ được tính là "bắt được" nếu **ít nhất một** cửa
  sổ của nó được nhận đúng. Cách này gần với trải nghiệm thật hơn: bạn vuốt một lần, máy chỉ
  cần nhận ra một lần.

> **Khái niệm — Cụm báo nhầm.** Khi chưa có cử chỉ, mô hình vẫn có thể nói "vuốt trái" vài
> lần liền nhau. Một chuỗi câu trả lời giống nhau liền nhau gọi là một **cụm**, tương đương
> một lần hệ thống *sẽ* phát lệnh. **Số cụm báo nhầm mỗi phút** cho biết hệ thống sẽ tự ý
> chuyển slide bao nhiêu lần khi bạn không làm gì.

---

## 3. Phase 6 — Rừng ngẫu nhiên: mô hình học máy đầu tiên

### 3.1. Cây quyết định và rừng ngẫu nhiên

> **Khái niệm — Cây quyết định.** Giống trò chơi **"20 câu hỏi"**. Máy học ra một chuỗi câu hỏi
> có/không về 15 con số. Ví dụ: "khoảng cách cái–trỏ có thay đổi hơn 1,2 lòng bàn tay không?"
> → nếu có: "nó tăng hay giảm?" → … cho tới khi trả lời được "đây là zoom in". Câu hỏi và
> ngưỡng đều do máy tự chọn, sao cho tách các lớp tốt nhất trên bài tập về nhà.

> **Khái niệm — Rừng ngẫu nhiên.** Một cây đơn lẻ dễ "học tủ". **Rừng ngẫu nhiên** trồng 300
> cây, mỗi cây học từ một phần ví dụ rút ngẫu nhiên và xét các câu hỏi theo thứ tự ngẫu nhiên.
> Khi gặp cửa sổ mới, **300 cây cùng biểu quyết**; tỉ lệ phiếu của lớp thắng chính là độ tin.
> Giống hỏi ý kiến 300 người, mỗi người được học từ một phần tài liệu khác nhau: ý kiến chung
> đáng tin hơn ý kiến của một người.

Mỗi cây cần biết lớp nào hiếm. Trong bài tập về nhà, `none` chiếm một nửa, nên mô hình được
dặn **coi trọng các lớp cử chỉ hơn** cho cân bằng. Huấn luyện cả rừng trên 3 326 cửa sổ chỉ
mất **1,6 giây**.

### 3.2. Kết quả trên tập kiểm định

| Mô hình | macro-F1 | Bắt được (bốn cử chỉ) | Báo đúng (bốn cử chỉ) |
|---|---|---|---|
| Luôn đoán `none` | 0,196 | 0% | — |
| Luật (Phase 5) | 0,231 | 44–62% | 2–10% |
| **Rừng ngẫu nhiên** | **0,436** | 49–63% | 13–35% |

- **Rừng gần gấp đôi điểm của luật,** và vượt xa hai đường cơ sở.
- **Điểm yếu là báo nhầm:** 877 cửa sổ `none` (8,2%) bị báo thành cử chỉ, trong khi cả tập chỉ
  có 388 cửa sổ cử chỉ thật. Nghĩa là cứ một lần báo đúng thì có hơn hai lần báo nhầm.
- **Theo cử chỉ:** 70% cú vuốt trái, 70% cú vuốt phải, 59% cú zoom in và 56% cú zoom out được
  nhận ra ít nhất một lần.

### 3.3. Mô hình dựa vào những con số nào

> **Khái niệm — Độ quan trọng của đặc trưng.** Muốn biết mô hình dựa vào con số nào, có một
> cách rất trực quan: **xáo trộn một cột** trong 15 cột trên đề thi thử, như tráo ngẫu nhiên
> giá trị của một câu hỏi giữa các cửa sổ, rồi xem điểm tụt bao nhiêu. Tụt nhiều thì mô hình
> dựa nhiều vào con số đó; không tụt thì con số đó không quan trọng.

**Kết quả:** ba con số quan trọng nhất là `pinch_range` (khoảng cái–trỏ thay đổi nhiều không),
`pinch_delta` (mở ra hay chụm lại), và `max_vx` (cổ tay đi ngang nhanh nhất bao nhiêu). Lý do
dễ hiểu: phần khó nhất của bài toán là tách **cử chỉ** khỏi **không cử chỉ**, và động tác
cái–trỏ tách zoom khỏi mọi thứ khác.

**Một điều bất ngờ, và cách giải thích.**

- Trước khi huấn luyện, dự án đã đoán ba con số quan trọng nhất sẽ là `pinch_delta`, `dx`,
  `max_vx`. Vậy mà `dx` (cổ tay dời ngang bao xa) chỉ đứng thứ 13.
- Nguyên nhân là `dx` có một **"người sinh đôi"**: `mean_vx` (vận tốc ngang trung bình) mang
  gần như cùng thông tin. Hai con số gần như luôn tăng giảm cùng nhau (hệ số tương quan 0,97,
  với 1 là trùng khít). Xáo một mình `dx` thì mô hình vẫn dùng được `mean_vx`, nên điểm không
  tụt, và cả hai trông như vô dụng.
- **Xáo cả cặp** cùng lúc thì điểm tụt ngang `max_vx`, và số cửa sổ vuốt bị đoán **ngược
  hướng** tăng từ 8 lên khoảng 43.
- Vậy thông tin "vuốt về bên nào" nằm ở cặp này. Kết quả được ghi lại như lời giải thích cho
  điều kiện thứ ba của bộ kiểm tra Phase 6 (hai điều kiện kia đều đạt).

### 3.4. Mô hình hay nhầm ở đâu

Phần lớn báo nhầm thuộc về **tay đang chỉ trỏ** và **tay không làm cử chỉ** của IPN, và chúng
thường bị nhầm thành **vuốt**.

Lý do: khi chỉ trỏ, người ta di chuyển tay nhanh và xa, có khi còn nhanh hơn một cú vuốt. Chỉ
nhìn quãng đường cổ tay đi thì hai việc này rất giống nhau.

### 3.5. Lần thử trực tiếp đầu tiên: zoom tốt, vuốt kém

Người dùng chạy demo bằng rừng ngẫu nhiên trên webcam. **Zoom được nhận khá tốt, nhưng vuốt thì
kém.** Đọc log (bản ghi từng câu trả lời của demo) thì thấy:

- những cú vuốt **chậm, đi xa** thì được nhận;
- những cú vuốt **nhanh rồi kéo tay về ngay** thì bị đoán `none`. Cổ tay đi nhanh, nhưng sau
  1,2 giây nó gần như về chỗ cũ.

Điều đáng chú ý là trên dữ liệu IPN, vuốt **không** kém zoom (70% so với 56–59%). Vậy vấn đề
không nằm ở mô hình nói chung.

> **Khái niệm — Lệch miền.** Mô hình học từ cách 30 người diễn IPN làm cử chỉ. Nếu bạn làm khác
> họ, mô hình sẽ không nhận ra, dù bạn thấy mình làm "đúng". Giống người học lái xe ở một thành
> phố, sang thành phố khác có biển báo khác thì lúng túng. Hiện tượng này gọi là **lệch miền**:
> dữ liệu lúc dùng khác dữ liệu lúc học.

### 3.6. Tìm nguyên nhân bằng thí nghiệm "đổi đúng một thứ"

> **Khái niệm — Thí nghiệm phản thực tế.** Muốn biết một người nhận ra bạn qua giọng nói hay qua
> khuôn mặt, ta đổi **đúng một thứ** rồi xem họ còn nhận ra không. Ở đây làm y như vậy:
>
> 1. Lấy những cú vuốt thật của IPN mà mô hình đang nhận đúng.
> 2. Sửa đúng một khía cạnh của chuyển động, giữ nguyên mọi thứ khác.
> 3. Cộng thêm độ rung nhỏ như tay thật.
> 4. Xem mô hình còn nhận ra không.
>
> Cách này trả lời câu hỏi mà điểm số tổng không trả lời được: **mô hình thật sự coi cái gì là
> một cú vuốt?**

| Sửa đổi (cú vuốt trái / phải) | Còn được nhận |
|---|---|
| Không sửa | 100% / 92% |
| **Bàn tay giữ nguyên dáng**, cổ tay vẫn đi y như cũ | **0% / 0%** |
| Đi ra rồi quay về ngay | 45% / 37% |
| Cổ tay chỉ đi nửa quãng đường | 48% / 47% |

**Kết luận.** Với rừng ngẫu nhiên, "vuốt" nghĩa là cú **hất** của người diễn IPN:

- cổ tay đi ngang đủ nhanh và đủ xa, rồi **dừng ở đó**;
- **và** bàn tay **mở ra trong lúc hất**, từ các đầu ngón chụm lại thành bàn tay mở.

Sự mở tay chính là thứ giúp mô hình phân biệt cú hất với tay đang chỉ trỏ, vì tay chỉ trỏ di
chuyển mà không đổi dáng. Một cú vuốt "kiểu thông thường" (bàn tay mở sẵn, lướt ngang) vì thế
bị coi là `none`.

### 3.7. Hai cách sửa và kết quả

**Cách 1 — Chế độ luyện tập hiển thị thêm độ mở bàn tay.** Demo có sẵn một chế độ luyện tập: nó
hiện vài con số của cửa sổ vừa rồi, tô xanh nếu giống người diễn IPN, đỏ nếu khác. Dự án thêm
con số `open_range`, cho biết bàn tay có mở ra trong lúc làm cử chỉ không.

**Kết quả** (phiên thử thứ hai của người dùng, 1 phút):

- có 43 cửa sổ có chuyển động kiểu vuốt;
- trong **88%** số đó, bàn tay đã mở ra đúng kiểu IPN;
- rừng nhận **79%** trong 43 cửa sổ đó là vuốt.

Tức là người dùng đã chỉnh cách vuốt theo IPN, và mô hình nhận ra.

**Cách 2 — Dạy mô hình chấp nhận cú vuốt giữ nguyên dáng tay.**

> **Khái niệm — Tăng cường dữ liệu.** Tạo thêm ví dụ huấn luyện bằng cách **biến đổi** ví dụ có
> sẵn mà không làm đổi đáp án: xoay nhẹ, lật ngang (vuốt trái lật thành vuốt phải), cho nhanh
> hay chậm hơn một chút, thêm độ rung. Giống cho học sinh xem cùng một bài toán viết theo nhiều
> cách, để các em hiểu bản chất chứ không thuộc lòng một cách viết.

- **Ý tưởng:** lấy các cú vuốt của IPN, giữ đường đi của cổ tay, nhưng "làm cứng" bàn tay (bỏ
  bớt hoặc bỏ hết sự đổi dáng), rồi vẫn dạy là "vuốt".
- **Phát hiện quan trọng:** bản "cứng hoàn toàn" giả tạo hơn thực tế. Tay thật đang di chuyển
  không bao giờ cứng hẳn, vì ngón tay hơi co duỗi và góc nhìn thay đổi. Đo trên tay chỉ trỏ
  thật của IPN, độ mở bàn tay vẫn dao động 0,2–0,8, trong khi bản giả tạo chỉ 0,06. Mô hình
  học từ bản giả tạo sẽ không giúp được tay thật.
- **Bản thực tế hơn** (giữ ngẫu nhiên một phần sự đổi dáng) **có giúp**: cú vuốt chỉ đổi dáng
  một nửa được nhận từ 10% lên 38–56%. Nhưng **giá rất đắt**: báo nhầm tăng 1,5–2,6 lần, vì
  tay chỉ trỏ giờ cũng bị coi là vuốt.
- **Quyết định:** cách này vẫn nằm trong code nhưng **đang tắt**. Đánh đổi bao nhiêu báo nhầm
  để lấy vuốt là việc người dùng chọn.

### 3.8. Những việc nền tảng khác của Phase 6

- **Khoá tập kiểm tra** (mục 2.2).
- **Demo nhanh:** mỗi câu trả lời của rừng mất 9 mili-giây thay vì 63, để không làm giật hình.
  Mô hình được nạp sẵn trước khi bật camera; trước đó demo đứng hình gần 3 giây lần đầu thấy
  tay.

---

## 4. Phase 7 — LSTM: đọc thẳng chuyển động của bàn tay

### 4.1. Mạng nơ-ron và LSTM

Rừng ngẫu nhiên chỉ thấy **15 con số tóm tắt** do người chọn. Nếu thứ quyết định một cử chỉ
không nằm trong 15 con số đó, nó chịu.

> **Khái niệm — Mạng nơ-ron.** Một công thức rất lớn với nhiều **"núm vặn"** (gọi là *trọng
> số*); LSTM của dự án có khoảng 220 nghìn núm. Lúc đầu các núm ở vị trí ngẫu nhiên và công
> thức đoán bừa. Huấn luyện là quá
> trình **vặn dần từng núm** sao cho số lần đoán sai trên bài tập về nhà giảm xuống. Không ai
> chỉ định núm nào làm gì; mạng tự tìm ra những dấu hiệu có ích.

> **Khái niệm — LSTM.** Một loại mạng nơ-ron chuyên đọc **chuỗi theo thời gian**. Nó đọc lần
> lượt 18 thời điểm của cửa sổ, mỗi thời điểm là đủ 21 điểm của bàn tay (42 con số). Vừa đọc
> vừa **ghi nhớ** những gì quan trọng, giống như ta đọc một câu từng chữ mà vẫn nhớ đầu câu.
> Đọc hết cửa sổ, nó đưa ra câu trả lời.
>
> LSTM ở đây chỉ đọc **một chiều**, từ quá khứ tới hiện tại. Nó không bao giờ "nhìn trước"
> tương lai, vì khi chạy thật trên webcam thì tương lai chưa xảy ra.

**Khác biệt cốt lõi:**

- Rừng ngẫu nhiên đọc **bản tóm tắt 15 con số** do người viết.
- LSTM xem **toàn bộ chuyển động** của 21 điểm, và tự tìm ra dấu hiệu.

### 4.2. LSTM được dạy như thế nào

> **Khái niệm — Epoch và loss.**
>
> - **Một epoch** là một lượt cho mạng xem hết toàn bộ bài tập về nhà. Mạng được dạy qua hàng
>   trăm epoch.
> - **Loss** (*mức sai*) là con số đo mạng còn sai nhiều tới đâu. Càng nhỏ càng tốt. Sau mỗi
>   epoch, dự án đo loss trên cả bài tập về nhà lẫn đề thi thử.

Vài điểm trong cách dạy:

- **Mỗi epoch, mạng thấy một bản biến đổi mới** của mỗi ví dụ: xoay, lật, nhanh chậm, rung
  (tăng cường dữ liệu, mục 3.7). Như vậy nó không thể thuộc lòng từng ví dụ.
- **Coi trọng lớp hiếm hơn:** trong bài tập về nhà, một lỗi trên ví dụ cử chỉ bị tính nặng gấp
  khoảng bốn lần một lỗi trên ví dụ `none`.
- **Khoảnh khắc mất tay:** đôi khi MediaPipe mất dấu bàn tay vài khoảnh khắc. Lúc đó LSTM được
  cho "giữ nguyên vị trí cuối cùng còn thấy", không bịa ra chuyển động và không dùng thông tin
  tương lai.
- **Chạy trên CPU thường**, không cần card đồ hoạ. Một lần huấn luyện mất khoảng 13–25 phút.
  Mỗi câu trả lời khi chạy demo mất khoảng **1 mili-giây**.

### 4.3. Kết quả

| | Rừng ngẫu nhiên | **LSTM** |
|---|---|---|
| macro-F1 trên tập kiểm định | 0,436 | **0,556** |
| Vuốt trái: bắt được / báo đúng | 54% / 13% | **89% / 26%** |
| Bắt được ít nhất một lần, theo cử chỉ (vuốt trái / phải) | 70% / 70% | **93% / 85%** |
| Bắt được ít nhất một lần, theo cử chỉ (zoom in / out) | 59% / 56% | **89% / 80%** |
| Cửa sổ `none` bị báo nhầm | 8,2% | **5,8%** |
| Cụm báo nhầm mỗi phút không cử chỉ | 14,8 | **8,6** |
| Báo nhầm khi tay chỉ trỏ (một ngón / hai ngón) | 5,8% / 9,7% | **3,5% / 5,9%** |

LSTM tốt hơn rừng ở gần như mọi mặt: bắt được nhiều hơn **và** báo nhầm ít hơn. Riêng với tay
nghỉ không làm cử chỉ thì nó không khá hơn (14,5% so với 10,6%).

### 4.4. Học thuộc lòng và đường học

> **Khái niệm — Quá khớp (học thuộc lòng).** Học sinh thuộc lòng đáp án bài tập về nhà thì
> điểm bài tập rất cao, nhưng gặp đề mới thì làm kém. Mạng nơ-ron cũng vậy. Dấu hiệu nhận
> biết: **mức sai trên bài tập về nhà tiếp tục giảm, nhưng mức sai trên đề thi thử thôi giảm,
> hoặc tăng lên.**

> **Khái niệm — Đường học, dừng sớm và checkpoint.**
>
> - **Đường học:** vẽ mức sai của cả hai tập theo từng epoch.
> - **Dừng sớm:** ngừng dạy khi điểm đề thi thử không còn tiến bộ thêm một thời gian.
> - **Checkpoint:** bản lưu của mạng ở thời điểm tốt nhất.

**Kết quả quan sát:**

- **Mô hình chính:** mức sai trên đề thi thử giảm nhanh trong khoảng 20 epoch đầu, rồi đứng
  yên. Mức sai trên bài tập về nhà vẫn tiếp tục giảm, tới gần 0. Từ khoảng epoch 20, khoảng
  cách giữa hai đường bắt đầu nới rộng. Nhưng mức sai trên đề thi thử **không quay đầu tăng
  lên**: việc thay ví dụ biến đổi mới mỗi epoch đã ngăn mạng học thuộc lòng.
- **Bản không tăng cường** (chạy riêng để thấy rõ): mạng thuộc lòng bài tập về nhà rất nhanh.
  Mức sai trên đề thi thử thấp nhất ở **epoch 38**, rồi tăng dần khoảng 30%. Đây là điểm bắt
  đầu quá khớp, hiện rõ trên hình.

### 4.5. Con số có đáng tin không?

> **Khái niệm — Dao động của điểm thi thử.** Mỗi cử chỉ trong đề thi thử chỉ có khoảng 100 cửa
> sổ. Chỉ cần vài cửa sổ đổi câu trả lời là điểm đã lên xuống vài phần trăm. Giữa hai epoch
> liền nhau, macro-F1 của LSTM dao động khoảng ±0,04, dù mạng gần như không đổi.

> **Khái niệm — Lạc quan do chọn lọc.** Nếu thi thử 100 lần rồi chỉ báo **điểm cao nhất**, con
> số đó lạc quan: một phần là do may. Lần dạy LSTM đầu tiên chọn đúng epoch có điểm cao nhất và
> báo **0,601**. Đó là một đỉnh may mắn.

**Cách làm hiện tại:**

- Dừng sớm và chọn checkpoint theo **trung bình 10 epoch liền nhau**, thay vì một epoch lẻ.
- Mô hình được chọn có điểm **0,556**. Mức thường đạt của nó vào khoảng 0,53.
- Con số không thiên lệch sẽ đến từ việc dạy lại với 5 cách xáo dữ liệu khác nhau (Phase 8), và
  từ lần mở tập kiểm tra duy nhất ở cuối dự án.

Cách chọn mới cũng sửa một lỗi thật. Hai lần dạy trước đã bị dừng quá sớm, ở epoch 40 và 48, chỉ
vì một đỉnh may mắn đến sớm.

### 4.6. LSTM nhìn cú vuốt khác rừng ngẫu nhiên

Lặp lại đúng các thí nghiệm "đổi một thứ" ở mục 3.6:

| Sửa đổi (cú vuốt trái / phải) | Rừng ngẫu nhiên | LSTM |
|---|---|---|
| Bàn tay giữ nguyên dáng | 0% / 0% | 8% / 0% |
| Đi ra rồi quay về ngay | 45% / 37% | **96% / 99%** |
| Cổ tay chỉ đi một phần tư quãng | 4% / 0% | **100% / 94%** |
| Cổ tay đứng yên, chỉ các ngón chuyển động | 0% / 0% | **100% / 87%** |

**LSTM nhận cú vuốt từ động tác của các ngón tay** (chụm lại rồi mở ra, ngón chỉ về một bên),
không từ quãng đường cổ tay đi. Đây chính là lý do nó chịu được kiểu "hất rồi kéo tay về" mà
rừng bỏ qua. Nhưng nó vẫn đòi bàn tay phải mở ra.

### 4.7. Lần thử trực tiếp với LSTM: vuốt tốt hơn hẳn, zoom lại kém đi

**Triệu chứng** đọc từ log:

- Lúc người dùng zoom, khoảng cách cái–trỏ mở ra và chụm lại rất rõ, **còn mạnh hơn** người
  diễn IPN. Vậy mà LSTM trả "không có cử chỉ", với độ tin gần như tuyệt đối.
- Lúc bàn tay **đứng yên**, LSTM lại báo `zoom_out` liên tục gần 2 giây.

> **Khái niệm — Loại trừ lỗi đường ống.** Trước khi đổ cho "người dùng làm khác IPN", phải chắc
> phần mềm demo không có lỗi. Cách kiểm: cho **chính chương trình demo** chạy trên một video IPN
> mà ta biết chắc có cú zoom. Nếu demo nhận đúng ở đó thì phần mềm ổn, và vấn đề nằm ở khác biệt
> giữa người dùng và IPN.

Demo nhận đúng hai cú zoom trong video IPN, với độ tin 0,88–1,00. Vậy phần mềm ổn.

**Tìm nguyên nhân,** lại bằng thí nghiệm "đổi một thứ", lần này trên các cú zoom thật của IPN:
giữ nguyên cổ tay, ngón cái và ngón trỏ, chỉ thay đổi **các ngón còn lại**.

| Sửa đổi (zoom in / zoom out) | Rừng ngẫu nhiên | LSTM |
|---|---|---|
| Không sửa | 93% / 98% | 100% / 100% |
| **Ngón nhẫn và ngón út duỗi thẳng** | 63% / 85% | **10% / 35%** |
| Chỉ còn ngón cái và trỏ cử động (zoom hai ngón) | 52% / 54% | **7% / 38%** |
| **Bàn tay đứng yên** ở dáng cái–trỏ đang mở | 0% báo zoom | **46–62% vẫn báo zoom** |

**Hai nguyên nhân:**

1. **LSTM học "kiểu zoom của người diễn IPN", không học "zoom là gì".** Người diễn IPN zoom
   bằng ba ngón, ngón nhẫn và út **luôn gập**. LSTM học luôn cả chi tiết đó. Chỉ cần nhẫn và út
   duỗi ra, điều rất tự nhiên khi zoom, là nó không còn nhận ra.
2. **LSTM đoán zoom từ dáng tay đứng yên.** Nó coi "bàn tay đang ở dáng cái–trỏ mở" là dấu hiệu
   của zoom, dù không có chuyển động nào. Đây chính là chuỗi báo nhầm lúc tay đứng yên trong
   log.

Rừng ngẫu nhiên ít bị ảnh hưởng hơn nhiều, vì nó nhìn chủ yếu **khoảng cách cái–trỏ thay
đổi**, đúng bản chất của zoom, và không bao giờ báo zoom khi tay đứng yên.

### 4.8. Thử sửa ngay trong LSTM — và vì sao không dùng

**Ý tưởng:** dạy lại LSTM bằng hai kiểu ví dụ biến đổi mới.

- **Cú zoom với ngón phụ "của người khác":** ngón giữa, nhẫn, út được thay bằng dáng tay thật
  lấy từ hơn 58 nghìn dáng tay khác trong dữ liệu IPN, và giữ yên. Thông điệp: "zoom là động
  tác cái–trỏ; các ngón khác làm gì cũng được."
- **Bàn tay đứng yên, đáp án "không có cử chỉ":** thông điệp "không có chuyển động thì không có
  cử chỉ."

**Kết quả:**

- **Lợi:** LSTM mới nhận zoom ở mọi kiểu ngón (88–98%) và không còn báo zoom khi tay đứng yên.
- **Giá rất đắt:** số cửa sổ không cử chỉ bị báo nhầm thành `zoom_out` tăng từ 52 lên 528,
  gấp 10 lần. Báo nhầm khi tay chỉ trỏ tăng từ 3,5% / 5,9% lên 12,0% / 10,2%. Tỉ lệ báo đúng
  của `zoom_out` rơi từ 46% xuống 10%.

**Vì sao:** chính "kiểu ngón riêng" của người diễn IPN là thứ giúp LSTM phân biệt cú zoom với
tay đang chỉ trỏ, vì khi chỉ trỏ, ngón cái cũng hay nhích lại gần ngón trỏ. Xoá kiểu ngón đi
là xoá luôn khả năng phân biệt. Cách sửa này vẫn nằm trong code nhưng **đang tắt**.

### 4.9. Lời giải: mô hình ghép

> **Khái niệm — Mô hình ghép.** Thay vì một mô hình làm mọi việc, dùng **hai chuyên gia**, mỗi
> người phụ trách đúng việc mình giỏi:
>
> - **LSTM lo vuốt.** Nó nhận vuốt qua động tác ngón tay, chịu được kiểu "hất rồi kéo về".
> - **Rừng ngẫu nhiên lo zoom.** Nó nhận zoom qua khoảng cách cái–trỏ, ít phụ thuộc các ngón
>   khác, không báo zoom khi tay đứng yên.
>
> Luật ghép rất đơn giản: LSTM nói "vuốt" thì là vuốt; nếu không, rừng nói "zoom" thì là zoom;
> còn lại là "không có cử chỉ". Cả hai chuyên gia đều đã được người dùng thấy tốt trên webcam
> ở đúng phần việc của mình.

**Trên tập kiểm định**, mô hình ghép đạt macro-F1 **0,506**: hơn rừng (0,436), kém LSTM đứng
một mình (0,556). Điều này hợp lý. Trên dữ liệu IPN, người diễn zoom đúng "kiểu IPN", nên zoom
của LSTM giỏi hơn. Còn với bàn tay của người dùng thì ngược lại.

**Trên chính bàn tay người dùng.** Người dùng đã chạy thử mô hình ghép trên webcam. Phiên đó
được phát lại qua cả bốn mô hình (mục 4.10):

| Số lần báo zoom trong 1,1 phút | |
|---|---|
| LSTM đứng một mình | 24 lần |
| **Mô hình ghép** | **45 lần** |

Số lần báo vuốt giữ nguyên, vì phần vuốt vẫn do LSTM đảm nhận. **Demo nên dùng mô hình ghép**:
`--model hybrid`.

### 4.10. "Hộp đen": ghi lại và phát lại một phiên thử

Lúc chẩn đoán zoom, log chỉ ghi vài con số tóm tắt, nên không kiểm được nguyên nhân trên chính
bàn tay người dùng.

> **Khái niệm — Ghi và phát lại.** Giống **hộp đen máy bay**. Giờ mỗi lần chạy demo có ghi log,
> chương trình lưu luôn vị trí 21 điểm của bàn tay ở mọi khung hình. Sau đó có thể **phát lại**
> cả phiên qua bất kỳ mô hình nào, như thể mô hình đó đã chạy trực tiếp lúc bạn làm cử chỉ.

**Kiểm chứng:** phát lại cho đúng **316/316** câu trả lời so với lúc demo chạy thật. Nhờ vậy,
mỗi cách sửa từ nay có thể thử ngay trên bàn tay của chính người dùng, không phải đoán.

### 4.11. Tính tái lập và những lỗi được phát hiện

> **Khái niệm — Tái lập.** Huấn luyện có nhiều bước ngẫu nhiên: trộn ví dụ, khởi tạo núm vặn,
> biến đổi dữ liệu. Dự án **cố định "hạt giống" ngẫu nhiên**, như xáo bài theo đúng một cách mỗi
> lần, nên chạy lại cùng lệnh sẽ cho **đúng từng chữ số** kết quả cũ. Nhờ vậy mọi con số trong
> báo cáo đều kiểm chứng được.

Dự án đã kiểm điều này thật: lần dạy LSTM hiện hành trùng lần dạy trước **từng chữ số suốt 106
epoch**. Chính việc kiểm này đã bắt được vài lỗi nhỏ mà không làm chương trình báo lỗi:

- một phép biến đổi dữ liệu làm mất khoảnh khắc đầu cửa sổ khi tay mất dấu ngay sau đó;
- một bước xử lý chạy chậm gấp 3 lần mức cần thiết. Đã sửa, kết quả không đổi một chữ số nào;
- một thay đổi nhỏ làm kết quả lệch ở chữ số cuối, khiến lần dạy cũ không tái tạo được nữa;
- một file mô hình lưu xong nhưng không mở lại được.

---

## 5. Bốn mô hình đặt cạnh nhau

| Mô hình | Nhìn vào gì | macro-F1 (đề thi thử) | Điểm mạnh | Điểm yếu |
|---|---|---|---|---|
| Luật (Phase 5) | 3 con số, ngưỡng do người đặt | 0,231 | Đơn giản, dễ hiểu | Báo nhầm gần một nửa thời gian |
| Rừng ngẫu nhiên (Phase 6) | 15 con số tóm tắt | 0,436 | Zoom vững với nhiều kiểu tay | Đòi cú vuốt kiểu IPN, nhiều báo nhầm |
| LSTM (Phase 7) | Toàn bộ chuyển động 21 điểm | **0,556** | Vuốt rất tốt, ít báo nhầm hơn | Zoom phụ thuộc kiểu tay của IPN |
| **Ghép** (Phase 7) | Vuốt theo LSTM, zoom theo rừng | 0,506 | Hợp với cách làm cử chỉ của người dùng | Kém LSTM trên dữ liệu IPN |

Mọi con số đo trên **cùng** 11 038 cửa sổ của tập kiểm định. Tập kiểm tra vẫn niêm phong.

---

## 6. Hạn chế và việc còn lại

### 6.1. Hệ thống còn yếu ở đâu

- **Báo nhầm vẫn cao.** Trên dữ liệu IPN, cứ mỗi phút không làm cử chỉ, mô hình tốt nhất vẫn
  báo nhầm khoảng 9 lần. Mục tiêu khi dùng thật là dưới 0,5 lần mỗi phút. Bước xử lý chính
  nằm ở Phase 9: một **"máy trạng thái"** chỉ phát lệnh khi vài câu trả lời liền nhau cùng đồng
  ý, và nghỉ một chút sau mỗi lệnh. Giống người bấm thang máy: đã bấm thì không bấm lại liên
  tục.
- **Bộ 15 con số không mô tả từng ngón tay.** Vì vậy không tách được "bàn tay mở đang lướt"
  với "tay đang chỉ trỏ". Đó là lý do cả hai cách "dạy chấp nhận kiểu tay khác" đều phải tắt.
  Cách sửa tận gốc là thêm con số đo độ duỗi từng ngón, hoặc quay thêm dữ liệu của chính người
  dùng (Phase 11).
- **Zoom đôi khi bị đoán ngược chiều giữa chừng.** Ví dụ phần "thu tay về" sau cú zoom in bị
  đoán là zoom out, ở 12–28% số cú zoom.
- **Đề thi thử nhỏ.** Khoảng 100 cửa sổ mỗi cử chỉ, nên chênh lệch dưới khoảng 0,04 điểm chưa
  đủ để kết luận mô hình nào hơn.
- **Tay trái** chưa được xét riêng. Nên dùng tay phải khi demo.

### 6.2. Việc của người dùng

1. **Thử hướng vuốt:** vuốt sang **trái của bạn** phải ra `swipe_left`. Nếu ngược, đổi một
   hằng số trong cấu hình rồi chạy lại các phép đo; **không sửa code**.
2. **Đếm báo nhầm:** gõ phím và dùng chuột 2 phút, có ghi log.
3. **Thử trực tiếp có cấu trúc** với mô hình ghép, và với rừng để so:
   - mỗi cử chỉ 10 lần, theo thứ tự cố định, có nghỉ giữa các lượt;
   - cộng 5 phút làm việc bình thường.

   Các phiên đã ghi chưa cho biết bạn định làm cử chỉ gì lúc nào, nên chưa tính được độ chính
   xác thật. Từ số liệu này sẽ quyết được có cần quay dữ liệu riêng (Phase 11) hay không.
4. **Xét hình đường học** (mục 4.4) có đủ cho yêu cầu "thấy rõ điểm bắt đầu quá khớp" chưa.
5. **Đọc và góp ý `docs/gestures.md`:** hướng dẫn làm cử chỉ theo kiểu IPN.
6. **Các lựa chọn đang chờ:**
   - có bật cách "dạy chấp nhận vuốt giữ dáng" không, và ở mức nào;
   - có thêm con số mô tả từng ngón tay không.

---

## Phụ lục A — Bảng thuật ngữ

| Thuật ngữ | Nghĩa trong tài liệu này |
|---|---|
| Điểm mốc | 21 điểm trên bàn tay (cổ tay, khớp, đầu ngón) mà MediaPipe tìm được ở mỗi khung hình |
| Cửa sổ | Đoạn 1,2 giây chuyển động, xét mỗi 0,2 giây |
| Lớp | Một trong năm đáp án: bốn cử chỉ và `none` |
| Đặc trưng | Một con số tóm tắt một cửa sổ; có 15 con số |
| Lòng bàn tay | Đơn vị đo: khoảng cách cổ tay → gốc ngón giữa |
| Mô hình | Thứ máy học được: nhận cửa sổ, trả lớp và độ tin |
| Độ tin | Từ 0 đến 1: mô hình chắc chắn tới đâu |
| Huấn luyện | Cho máy học từ ví dụ có đáp án |
| Tập huấn luyện / kiểm định / kiểm tra | Bài tập về nhà / đề thi thử / đề thi thật niêm phong |
| Tỉ lệ bắt được (recall) | Trong các cử chỉ thật, bắt được bao nhiêu phần |
| Tỉ lệ báo đúng (precision) | Trong các lần báo, bao nhiêu lần đúng |
| F1, macro-F1 | Điểm cân bằng hai tỉ lệ trên; trung bình của năm lớp |
| Đường cơ sở | Mô hình "ngốc" làm mốc: luôn đoán `none`, đoán ngẫu nhiên |
| Ma trận nhầm lẫn | Bảng: lớp thật × lớp đoán |
| Mức sự kiện | Đếm theo cử chỉ, không theo cửa sổ |
| Cụm báo nhầm | Một chuỗi câu trả lời nhầm liền nhau ≈ một lệnh phát nhầm |
| Cây quyết định | Chuỗi câu hỏi có/không do máy tự chọn |
| Rừng ngẫu nhiên | 300 cây cùng biểu quyết |
| Độ quan trọng đặc trưng | Xáo một con số thì điểm tụt bao nhiêu |
| Lệch miền | Cách làm lúc dùng khác cách làm trong dữ liệu học |
| Thí nghiệm phản thực tế | Đổi đúng một thứ để xem mô hình dựa vào gì |
| Tăng cường dữ liệu | Tạo thêm ví dụ bằng biến đổi không làm đổi đáp án |
| Mạng nơ-ron, trọng số | Công thức lớn với nhiều "núm vặn" được vặn dần khi học |
| LSTM | Mạng nơ-ron đọc chuỗi theo thời gian, có trí nhớ |
| Epoch | Một lượt xem hết bài tập về nhà |
| Loss | Mức sai, càng nhỏ càng tốt |
| Quá khớp | Học thuộc lòng bài tập, kém với đề mới |
| Đường học | Mức sai của hai tập theo từng epoch |
| Dừng sớm, checkpoint | Ngừng dạy khi hết tiến bộ; bản lưu tốt nhất |
| Lạc quan do chọn lọc | Báo điểm cao nhất trong nhiều lần thử thì con số đẹp hơn thực tế |
| Mô hình ghép | Mỗi mô hình lo phần việc mình giỏi |
| Tái lập | Chạy lại cùng lệnh ra đúng kết quả cũ |
| Máy trạng thái (Phase 9) | Bộ lọc chỉ phát lệnh khi các câu trả lời đồng thuận |

---

## Phụ lục B — Dành cho người làm kỹ thuật

### B.1. Số liệu lấy từ đâu

| Nội dung | Nguồn |
|---|---|
| Rừng ngẫu nhiên, mục 3.2–3.4 | `results/phase6/train_rf/run_07` (= `run_05`); phân tích ở `results/phase6/notes.md` mục 1–5 |
| Thí nghiệm vuốt với rừng, mục 3.6 | `results/phase6/probe_swipes/run_01` |
| Tăng cường "bàn tay cứng", mục 3.7 | `results/phase6/sweep_rigid/run_03` |
| Phiên thử trực tiếp với rừng | `results/phase6/live_rf_work.csv`, `live_rf_swipes.csv`; phép đo nhanh trên log |
| LSTM, mục 4.3–4.5 | `results/phase7/train_lstm/run_07` (mô hình của demo), `run_02` (lần dạy đầu, điểm 0,601), `run_04` (không tăng cường, 150 epoch); `results/phase6/evaluate/run_06` |
| Thí nghiệm vuốt với LSTM, mục 4.6 | `results/phase7/probe_swipes/run_02` |
| Thí nghiệm zoom, mục 4.7 | `results/phase7/probe_zooms/run_03` |
| Thử sửa trong LSTM, mục 4.8 | `results/phase7/train_lstm/run_08`, `probe_zooms/run_04` |
| Mô hình ghép, mục 4.9 | `results/phase6/evaluate/run_05`; phát lại phiên người dùng: `results/phase7/replay/run_02` |
| Bảng so sánh mô hình | `results/model_comparison.md` |

Các lần chạy khác trong cùng thư mục là bản thử trung gian. `results/phase7/notes.md` mục 9 ghi rõ
bản nào hiện hành.

### B.2. Lệnh tái lập

```
python scripts/train_rf.py
python scripts/probe_swipes.py
python scripts/sweep_rigid.py
python scripts/train_lstm.py                                        # → lstm_model.pt (run_07)
python scripts/train_lstm.py --stop-smooth 1                        # tái tạo run_02
python scripts/train_lstm.py --no-augment --patience 150            # run_04
python scripts/train_lstm.py --zoom-style-p 0.5 --static-share 0.1  # run_08
python scripts/probe_swipes.py --model lstm
python scripts/probe_zooms.py
python scripts/evaluate.py --model hybrid --split val
python scripts/replay_log.py results/phase7/live_hybrid_landmarks.npz
python scripts/demo.py --model hybrid --show-features --log results/phase7/live_hybrid.csv
```

### B.3. Quyết định đã ghi vào `docs/SPEC.md`

- **2026-10-09:**
  - chế độ luyện tập hiện thêm `open_range`;
  - tăng cường "bàn tay cứng" có trong code, tắt;
  - LSTM xử lý khoảnh khắc mất tay bằng vị trí cuối cùng còn thấy;
  - đo loss của train và val theo cùng một cách.
- **2026-10-10:**
  - dừng sớm theo trung bình 10 epoch;
  - tăng cường đổi dáng ngón phụ và bàn tay đứng yên có trong code, tắt;
  - thêm mô hình ghép `hybrid`;
  - demo ghi kèm điểm mốc, kèm script phát lại.
