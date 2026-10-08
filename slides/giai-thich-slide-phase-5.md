# Giải thích chi tiết bộ slide "Nhận dạng cử chỉ bàn tay thời gian thực" (Phase 0–5)

Tài liệu đi kèm bộ slide `Report_phase_5.pptx` (11 slide), viết cho người **chưa học computer vision hay học máy**.

*Cập nhật 08/10/2026: sắp lại theo bản slide 11 trang, bổ sung các mục "Hỏi đáp" ở slide 4, 5 và 6, và khớp với hai dòng đã sửa trên slide 6 và 7.*

## Cách đọc tài liệu này

- **Phần 0** là kiến thức nền: pixel, frame, mô hình học máy là gì, và bức tranh tổng thể của hệ thống. Nếu bạn chưa quen các khái niệm này, hãy đọc phần này trước, mất khoảng 10 phút.
- Mỗi slide được giải thích theo ba phần:
  - **Ý chính**: slide muốn nói gì, trong một câu.
  - **Giải thích**: đi qua từng mục trên slide và trong lời thoại. File slide không còn phần ghi chú; "lời thoại" ở đây là lời thoại trong file kịch bản `kich-ban-thuyet-trinh-den-phase-5.md`.
  - **Thuật ngữ**: các từ chuyên môn xuất hiện lần đầu ở slide đó.
- Các mục **Hỏi đáp** đi sâu vào những câu hỏi hay gặp, ví dụ "bước là gì", "vì sao 18 bước", "189 đoạn là gì".
- **Phụ lục A–E** giải thích năm slide đã bỏ khỏi bản trình chiếu: chuẩn hoá, lệch frame, chia tập, cổng kiểm tra, demo. Lời thoại và slide kết luận vẫn nhắc tới các nội dung này, nên bạn vẫn cần nắm để trả lời câu hỏi.
- Thuật ngữ đã giải thích ở slide trước sẽ không giải thích lại. Bạn có thể tra ở **Bảng thuật ngữ** cuối file.
- Tên tiếng Anh được ghi trong ngoặc để bạn tra thêm tài liệu.
- Mọi con số đều lấy từ slide hoặc lời thoại. Chỗ nào là phép tính minh hoạ thêm của tài liệu này, sẽ ghi rõ "minh hoạ".

---

## Phần 0 — Kiến thức nền

### 0.1. Máy tính "nhìn" ảnh như thế nào

Một bức ảnh số là một bảng gồm rất nhiều ô vuông nhỏ. Mỗi ô gọi là một **pixel** (điểm ảnh). Ảnh 640×480 có 640 cột và 480 hàng, tức 307 200 pixel. Mỗi pixel lưu màu bằng ba con số (đỏ, xanh lá, xanh dương), mỗi số từ 0 đến 255.

Với máy tính, bức ảnh chỉ là một bảng số khổng lồ. Nó không tự "biết" trong ảnh có bàn tay hay cái cốc.

**Video** là một chuỗi ảnh chiếu liên tiếp. Mỗi ảnh trong chuỗi gọi là một **frame** (khung hình). **FPS** (frames per second) là số frame mỗi giây. Video 30 FPS nghĩa là cứ khoảng 0,033 giây lại có một ảnh mới.

**Thị giác máy tính** (computer vision) là lĩnh vực dạy máy tính rút ra ý nghĩa từ những bảng số đó: trong ảnh có gì, nằm ở đâu, đang làm gì.

### 0.2. Học máy trong vài dòng

Muốn máy nhận ra cử chỉ, có hai cách. Cách thứ nhất là tự viết luật, ví dụ "nếu tay đi sang trái nhanh thì là vuốt trái". Cách thứ hai là cho máy xem rất nhiều ví dụ có sẵn đáp án, rồi để máy tự tìm quy luật. Cách thứ hai gọi là **học máy** (machine learning). Dự án này dùng cả hai: mô hình đầu tiên là luật, các mô hình sau sẽ là học máy.

Vài từ cần biết:

- **Dữ liệu**: các ví dụ. Ở đây là video người làm cử chỉ.
- **Nhãn** (label): đáp án đúng gắn với mỗi ví dụ, ví dụ "đoạn này là vuốt trái".
- **Lớp** (class): các loại đáp án có thể có. Dự án này có 5 lớp: vuốt trái, vuốt phải, zoom in, zoom out, không cử chỉ.
- **Phân loại** (classification): bài toán chọn một lớp cho mỗi đầu vào.
- **Mô hình** (model): chương trình nhận đầu vào và đưa ra dự đoán.
- **Huấn luyện** (training): quá trình chỉnh mô hình cho khớp với dữ liệu có nhãn.
- **Đánh giá** (evaluation): đo xem mô hình đoán đúng đến đâu, trên dữ liệu nó **chưa từng thấy** khi huấn luyện.

### 0.3. Bức tranh tổng thể của hệ thống

Bộ slide không có trang tổng quan, nên phần dưới tóm tắt lại toàn bộ hệ thống để bạn có khung trước khi đọc từng slide.

```
Webcam → MediaPipe → 21 điểm mốc → Cắt cửa sổ → Chuẩn hoá → Đặc trưng → Mô hình → Máy trạng thái → Phím tắt
 (ảnh)   (tìm tay)   (42 số/frame)  (1,2 giây)               (15 số)     (đoán lớp)  (Phase 9, chưa làm)
```

1. **Webcam** cho ra ảnh.
2. Thư viện **MediaPipe** tìm bàn tay trong ảnh và trả về vị trí 21 khớp tay. Từ đây hệ thống bỏ ảnh đi, chỉ làm việc với toạ độ các khớp. Nhờ vậy dữ liệu rất gọn và chạy được trên máy tính thường.
3. Chuỗi toạ độ được cắt thành từng đoạn ngắn 1,2 giây, gọi là **cửa sổ**.
4. Mỗi cửa sổ được **chuẩn hoá**, để kết quả không phụ thuộc tay to hay nhỏ, gần hay xa camera. Sau bước này, mọi khoảng cách được đo bằng đơn vị **"lòng bàn tay"**: khoảng cách từ cổ tay tới gốc ngón giữa (Phụ lục A). Đơn vị này xuất hiện trong nhiều con số ở slide 6 và slide 8.
5. Từ mỗi cửa sổ, hệ thống tính ra 15 con số mô tả chuyển động, gọi là **đặc trưng**.
6. **Mô hình** đọc 15 đặc trưng và đoán cửa sổ đó thuộc lớp nào.
7. Sau này, một **máy trạng thái** sẽ gộp các dự đoán liên tiếp thành đúng một lệnh, rồi phát phím tắt (ví dụ phím chuyển slide).

Dự án chia thành 13 giai đoạn, gọi là **phase**, đánh số 0 đến 12. Bộ slide báo cáo đến hết Phase 5. Ở mốc này, hệ thống đã chạy được từ đầu đến cuối với mô hình đơn giản nhất (mô hình luật). Phần thử trực tiếp trên webcam của Phase 5 chưa làm.

### 0.4. Hai ý xuyên suốt cần nhớ

- **Tính nhân quả** (causality). Khi chạy thật, tại mỗi thời điểm hệ thống chỉ biết những gì đã xảy ra, không biết tương lai. Mọi bước xử lý phải tôn trọng điều này. Nếu một bước lén dùng thông tin tương lai, con số đo trên máy sẽ đẹp hơn những gì hệ thống làm được khi chạy thật.
- **Lỗi im lặng** (silent error). Đây là loại lỗi không làm chương trình báo lỗi hay dừng lại, nhưng làm kết quả sai. Nó nguy hiểm vì bạn không biết mình đang sai. Rất nhiều quyết định trong bộ slide nhằm chặn loại lỗi này.

---

## Slide 1 — Tiêu đề

**Ý chính:** Đề tài là nhận ra cử chỉ bàn tay từ webcam ngay lúc người dùng làm, để điều khiển máy tính. Đây là báo cáo tiến độ, tập trung vào các kỹ thuật đã làm, không phải một con số độ chính xác.

**Giải thích**

- **"Thời gian thực"** (real-time): hệ thống phản hồi ngay trong lúc người dùng đang làm cử chỉ, đủ nhanh để người dùng thấy tự nhiên. Ngược lại là xử lý **ngoại tuyến** (offline): quay video xong rồi mới phân tích, không cần vội.
- **Hình khung xương bàn tay** bên phải gồm 21 chấm. Mỗi chấm là một **điểm mốc** (landmark), tức một khớp trên bàn tay. Các đường nối chỉ để dễ nhìn. Hai chấm tô cam là đầu ngón cái và đầu ngón trỏ, vì khoảng cách giữa chúng được dùng để nhận ra cử chỉ zoom (slide 5).
- **"21 điểm mốc · 42 con số mỗi frame"**: mỗi điểm mốc có hai toạ độ, x (ngang) và y (dọc), nên 21 × 2 = 42 con số. Đây là toàn bộ thông tin hệ thống giữ lại từ một bức ảnh hơn 300 nghìn pixel.

Vị trí 21 điểm mốc theo cách đánh số của MediaPipe (sơ đồ đơn giản hoá):

```
              8     12    16    20      ← đầu ngón (trỏ, giữa, nhẫn, út)
              7     11    15    19
       4      6     10    14    18
        3     5     9     13    17      ← gốc ngón
          2
            1
                  0                     ← cổ tay

  ngón cái: 1–4 · ngón trỏ: 5–8 · ngón giữa: 9–12 · ngón nhẫn: 13–16 · ngón út: 17–20
```

Bạn sẽ gặp lại mấy điểm này nhiều lần:

- điểm 0 (cổ tay): dùng để đo chuyển động của cả bàn tay;
- điểm 9 (gốc ngón giữa): khoảng cách 0–9 là đơn vị đo "lòng bàn tay" ở Phụ lục A;
- điểm 4 và 8 (đầu ngón cái và đầu ngón trỏ): khoảng cách giữa chúng dùng cho zoom.

**Thuật ngữ**

- **Thời gian thực / ngoại tuyến** (real-time / offline): xem ở trên.
- **Điểm mốc** (landmark, keypoint): một vị trí cố định trên cơ thể mà máy xác định được, ở đây là các khớp bàn tay.
- **Khung xương bàn tay** (hand skeleton): tập 21 điểm mốc cùng các đường nối.

---

## Slide 2 — Bài toán

**Ý chính:** Từ hình ảnh webcam, hệ thống phải nhận ra 4 cử chỉ để phát 4 lệnh, và quan trọng không kém, phải biết khi nào người dùng **không** làm cử chỉ nào. Có ba ràng buộc làm bài toán khó hơn vẻ ngoài.

**Giải thích**

*Đầu vào.* Đầu vào là webcam laptop thông thường. Hệ thống chạy trên **CPU**, không cần **GPU**:

- CPU là bộ xử lý chính, máy tính nào cũng có.
- GPU là chip đồ hoạ, tính song song rất nhanh. GPU thường cần cho các mạng nơ-ron lớn xử lý ảnh, nhưng nhiều laptop không có GPU đủ mạnh.

Vì chỉ có CPU, hệ thống phải chọn cách xử lý nhẹ. Đây là lý do nó làm việc với 42 con số toạ độ thay vì đưa nguyên bức ảnh vào một mạng nơ-ron.

*Đầu ra.* Mỗi cử chỉ ứng với một lệnh:

| Cử chỉ | Làm thế nào | Lệnh |
|---|---|---|
| Vuốt trái | Hất tay nhanh sang trái | Slide trước |
| Vuốt phải | Hất tay nhanh sang phải | Slide sau |
| Zoom in | Mở đầu ngón cái và ngón trỏ ra xa nhau | Phóng to |
| Zoom out | Chụm đầu ngón cái và ngón trỏ lại | Thu nhỏ |
| Không cử chỉ | Mọi thứ còn lại | Không làm gì |

Zoom ở đây giống thao tác phóng to, thu nhỏ bằng hai ngón trên điện thoại, nhưng làm trên không.

Lớp thứ năm, "không cử chỉ", gọi là **lớp nền** (background class). Nó gồm mọi chuyển động không phải cử chỉ đích: gõ phím, cầm chuột, khua tay khi nói, đưa tay gãi đầu.

*Ba điểm khó.*

1. **Lớp nền là lớp quan trọng nhất.** Khi dùng thật, phần lớn thời gian người dùng không làm cử chỉ nào. Có hai kiểu sai:
   - **Báo nhầm** (false positive, false alarm): người dùng không làm gì mà hệ thống tưởng có cử chỉ.
   - **Bỏ sót** (false negative, miss): người dùng làm cử chỉ mà hệ thống không nhận ra.

   Ở bài toán này, báo nhầm nguy hiểm hơn. Đang thuyết trình mà slide tự chuyển là rất phiền; còn bỏ sót thì người dùng chỉ cần vuốt lại.
2. **Ràng buộc thời gian thực.** Tại mỗi thời điểm, hệ thống chỉ được dùng những gì đã xảy ra. Khi xem lại cả video, con người có thể thấy "tay sắp rút về, vậy đây là cú vuốt". Khi chạy thật, hệ thống không thể "chờ xem" như vậy.
3. **Máy tính thông thường.** Hệ thống chạy trên CPU, như đã nói ở trên.

**Thuật ngữ**

- **CPU / GPU**: bộ xử lý chính / chip đồ hoạ tính song song.
- **Lớp nền** (background class): lớp "không cử chỉ".
- **Báo nhầm / bỏ sót** (false positive / false negative): xem ở trên. Hai từ này còn xuất hiện ở slide 9.
- **Phím tắt** (keyboard shortcut): tổ hợp phím ra lệnh cho máy, ví dụ mũi tên phải để sang slide sau. Hệ thống sẽ "giả lập" việc bấm các phím này.

---

## Slide 3 — Dữ liệu IPN Hand

**Ý chính:** Dự án huấn luyện bằng một bộ dữ liệu công khai có sẵn là IPN Hand. Nó gom 14 loại cử chỉ của bộ này về 5 lớp của bài toán, và chấp nhận một số đánh đổi.

**Giải thích**

*IPN Hand là gì.* Đây là một **bộ dữ liệu** (dataset) công khai về cử chỉ bàn tay, do một nhóm nghiên cứu công bố năm 2020 cho bài toán nhận dạng cử chỉ liên tục, thời gian thực. Bốn con số trên slide:

- **200 video**;
- **50 người diễn**, tức người được quay làm cử chỉ;
- **14 lớp gốc**, tức 14 loại cử chỉ mà bộ dữ liệu gán nhãn;
- **640×480**, khoảng **30 FPS**: độ phân giải và tốc độ khung hình của video.

Bộ dữ liệu có sẵn **cách chia train/test chính thức theo người**: nhóm tác giả đã định trước người nào dùng để huấn luyện, người nào để kiểm tra. Phụ lục C giải thích vì sao điều này quan trọng.

*Ánh xạ 14 lớp về 5 lớp.* Dưới đây là 14 lớp gốc. Tên tiếng Anh lấy theo bài báo của IPN Hand; tên tiếng Việt theo slide.

| Lớp gốc IPN (tiếng Anh) | Tên trong slide | Lớp của hệ thống |
|---|---|---|
| Throw left | Hất trái | Vuốt trái |
| Throw right | Hất phải | Vuốt phải |
| Zoom in | Zoom in | Zoom in |
| Zoom out | Zoom out | Zoom out |
| Throw up | Hất lên | Không cử chỉ (mẫu âm khó) |
| Throw down | Hất xuống | Không cử chỉ (mẫu âm khó) |
| Open twice | Xòe tay hai lần | Không cử chỉ (mẫu âm khó) |
| Pointing with one finger | Chỉ trỏ một ngón | Không cử chỉ (mẫu âm khó) |
| Pointing with two fingers | Chỉ trỏ hai ngón | Không cử chỉ (mẫu âm khó) |
| Click with one / two fingers | Bấm một / hai ngón | Không cử chỉ |
| Double click with one / two fingers | Bấm đúp một / hai ngón | Không cử chỉ |
| Non-gesture | Không cử chỉ | Không cử chỉ |

Bốn lớp trùng với bài toán được giữ nguyên. Mười lớp còn lại gom hết về "không cử chỉ".

*Mẫu âm khó* (hard negatives) là những ví dụ thuộc lớp "không" nhưng trông rất giống lớp cần tìm. Hất lên chỉ khác hất trái ở hướng. Chỉ trỏ cũng là tay di chuyển nhanh. Giữ những mẫu này trong lớp nền là có chủ đích: mô hình phải học phân biệt chúng, nếu không nó sẽ báo nhầm mỗi khi người dùng chỉ tay.

*Chiến lược "IPN trước".* Dự án dùng dữ liệu có sẵn trước, chỉ tự quay thêm khi có bằng chứng là cần. Cách này hợp lý vì hệ thống chỉ dùng điểm mốc chứ không dùng ảnh. Khác biệt về phông nền, ánh sáng, màu da, loại camera giữa video IPN và webcam của bạn hầu như biến mất khi chỉ còn 21 toạ độ khớp tay.

*Hai điều kiện đi kèm.*

1. **Người dùng làm cử chỉ theo cách của IPN.** Mô hình chỉ học được kiểu vuốt, kiểu zoom của 50 người diễn IPN. Người dùng làm khác kiểu quá thì mô hình có thể không nhận ra. Phụ lục E có chế độ luyện tập để hỗ trợ việc này.
2. **Quy ước hướng lấy theo IPN, phải đo chứ không đoán.** "Hất trái" là trái của ai thì phải xác định bằng số liệu (slide 6).

*Cái chấp nhận mất.* Dự án chưa có dữ liệu trong điều kiện thật, ví dụ người ngồi trước laptop vừa gõ phím vừa nói. Phần này sẽ được bù bằng các phép đo trực tiếp trên webcam ở các phase sau.

**Thuật ngữ**

- **Bộ dữ liệu** (dataset): tập ví dụ có nhãn dùng để huấn luyện và đánh giá.
- **Người diễn** (subject): người xuất hiện trong video.
- **Độ phân giải** (resolution): số pixel theo chiều ngang × chiều dọc.
- **Mẫu âm khó** (hard negative): xem ở trên.
- **Train / test**: tập để huấn luyện / tập để kiểm tra (giải thích kỹ ở Phụ lục C).

---

## Slide 4 — Thu nhận điểm mốc và pipeline tiền xử lý

**Ý chính:** Slide mô tả cách lấy điểm mốc từ video, và chuỗi 7 bước biến dữ liệu thô thành dạng mô hình dùng được. Thứ tự các bước cố định, và giống hệt nhau cho mọi nguồn dữ liệu.

**Giải thích**

*Pipeline là gì.* **Pipeline** là một dây chuyền xử lý: dữ liệu đi qua từng trạm theo thứ tự, đầu ra trạm trước là đầu vào trạm sau. **Tiền xử lý** (preprocessing) là các bước làm sạch, sắp xếp dữ liệu trước khi đưa vào mô hình.

Một nguyên tắc quan trọng của dự án là **một pipeline cho mọi nguồn**. Video IPN lúc huấn luyện và hình ảnh webcam lúc chạy thật đi qua đúng cùng các hàm, theo cùng thứ tự. Nếu có hai bản xử lý "gần giống nhau", kết quả đo trên máy sẽ đẹp nhưng demo thật thì loạn, vì mô hình gặp dữ liệu hơi khác thứ nó đã học.

*Cột trái: thu nhận.*

- **MediaPipe Hand Landmarker** là một thư viện của Google. Nó nhận một ảnh và trả về 21 điểm mốc của bàn tay.
  - **Chế độ video**: thư viện dùng kết quả của frame trước để **theo dõi** (tracking) bàn tay sang frame sau, thay vì tìm lại từ đầu ở mỗi ảnh. Cách này nhanh hơn và ổn định hơn.
  - **Một bàn tay**: chỉ theo dõi một tay.
- **Chỉ lấy toạ độ 2D.** MediaPipe còn ước lượng một con số thứ ba là độ sâu z (tay gần hay xa camera). Nhưng một camera thường không đo được độ sâu thật; thư viện chỉ đoán từ hình dáng bàn tay, nên con số này rất nhiễu. Đưa vào chỉ thêm nhiễu, nên dự án bỏ nó.
- **Ảnh vào mô hình không lật.** Webcam thường hiển thị như soi gương: bạn giơ tay phải thì thấy tay ở bên phải màn hình, cho tự nhiên. Đó chỉ là phép lật **để hiển thị**. Ảnh đưa vào xử lý thì giữ nguyên như camera chụp, giống hệt video IPN. Nếu lỡ lật ảnh đầu vào, mọi cú vuốt trái sẽ thành vuốt phải.
- **Giữ frame mất tay.** Đôi khi MediaPipe không thấy tay, ví dụ khi tay ra khỏi khung hình hoặc bị mờ do chuyển động nhanh. Frame đó vẫn được ghi lại, với toạ độ để rỗng. Nếu xoá frame đi, hai frame trước và sau khoảng mất tay sẽ đứng liền nhau, như thể không có khoảng trống nào. Bước nội suy phía sau sẽ âm thầm nối qua, như thể tay vẫn ở đó. Đây chính là một lỗi im lặng.

*Cột phải: pipeline 7 bước.*

1. **Đổi toạ độ sang pixel, hai trục dùng hai hệ số riêng.** MediaPipe trả toạ độ dạng tỉ lệ từ 0 đến 1, trong đó 0 là mép trái hoặc mép trên, 1 là mép phải hoặc mép dưới. Vì ảnh 640×480 không vuông, cùng giá trị 0,1 nhưng theo chiều ngang là 64 pixel, theo chiều dọc chỉ là 48 pixel. Nhân x với chiều rộng và y với chiều cao thì hai trục mới có cùng thước đo. Nếu không, một vòng tròn vẽ bằng tay sẽ thành hình bầu dục trong dữ liệu.
2. **Đưa về lưới thời gian đều 15 Hz.** Hz (hertz) là số lần mỗi giây. Lưới 15 Hz nghĩa là cứ 1/15 giây (khoảng 0,067 giây) lấy một **bước** (time step). Lý do: webcam có FPS dao động (lúc 30, lúc 20 khi máy bận), còn video IPN khoảng 30 FPS. Đưa mọi nguồn về cùng một nhịp đều thì dữ liệu mới so sánh được. Giá trị tại mỗi bước được tính bằng **nội suy** (interpolation), tức ước lượng giá trị ở giữa hai điểm đã biết. Ví dụ tay ở x = 100 lúc 0,00 giây và x = 110 lúc 0,10 giây, thì lúc 0,05 giây ước lượng tay ở x = 105. Phép nội suy chỉ dùng hai frame cùng có tay. Ví dụ đầy đủ và đầu ra của bước này: xem các mục Hỏi đáp ở cuối phần slide 4.
3. **Vá lỗ hổng ngắn: tối đa 3 bước, phải có đủ hai đầu.** "Lỗ hổng" là một chuỗi bước liền nhau bị mất tay. Lỗ ngắn, tối đa 3 bước (0,2 giây), và hai đầu lỗ đều có tay, thì được vá bằng nội suy. Lỗ dài hơn thì giữ rỗng, vì mất tay lâu là một tín hiệu thật, ví dụ người dùng đã hạ tay xuống.
4. **Cắt cửa sổ 1,2 giây, trượt mỗi 0,2 giây.** Hình dung một khung nhìn dài 1,2 giây trượt dọc dòng thời gian, mỗi lần dịch 0,2 giây. Mỗi vị trí của khung là một **cửa sổ**, và mô hình đưa ra một dự đoán cho mỗi cửa sổ. Ở lưới 15 Hz, 1,2 giây là 18 bước, 0,2 giây là 3 bước. Hai cửa sổ liền nhau dùng chung 15 trên 18 bước.

   ```
   giây      0,0   0,2   0,4   0,6   0,8   1,0   1,2   1,4   1,6
   cửa sổ 1  [───────────────────────────────────]
   cửa sổ 2        [───────────────────────────────────]
   cửa sổ 3              [───────────────────────────────────]
   ```

   Cửa sổ được tính bằng giây chứ không bằng số frame. Lý do vẫn là FPS mỗi nguồn khác nhau: 36 frame ở 30 FPS là 1,2 giây, nhưng ở 20 FPS là 1,8 giây. Vì sao chọn 1,2 giây và 0,2 giây, và đầu ra là gì: xem các mục Hỏi đáp ở cuối phần slide 4.
5. **Tăng cường**: tạo thêm biến thể của dữ liệu. Bước này chỉ chạy khi huấn luyện, không chạy khi đánh giá hay khi chạy thật (Phụ lục C).
6. **Chuẩn hoá cửa sổ** (Phụ lục A).
7. **Tính đặc trưng** (slide 5), hoặc đưa thẳng chuỗi toạ độ vào một mô hình chuỗi như LSTM (Phase 7, slide 10).

*Hình dòng thời gian ở cuối slide* minh hoạ bước 3. Mỗi ô là một bước:

```
■■■■■■▒▒■■■■■■······■■■■
■ có tay   ▒ lỗ ngắn (≤ 3 bước), đã vá bằng nội suy   · lỗ dài, giữ rỗng
```

Vì sao ngưỡng là 3 bước: theo tài liệu `03-bieu-dien-khung-xuong-ban-tay.md` trong project Computer Vision (mục 12.2), trong 0,2 giây bàn tay không thể đi quá xa, nên nối thẳng hai đầu lỗ là một ước lượng hợp lý. Lỗ dài hơn thì tay có thể đã làm bất cứ điều gì, và nội suy sẽ bịa ra một chuyển động không hề xảy ra.

### Hỏi đáp: Đưa về lưới 15 Hz có ý nghĩa gì, và cho ra kết quả gì?

**Ý nghĩa: đưa mọi nguồn dữ liệu về cùng một "đồng hồ" đều đặn.**

Sau bước 1, dữ liệu là một danh sách các frame. Mỗi frame có một mốc thời gian, kèm 42 toạ độ pixel, hoặc để rỗng nếu không thấy tay. Vấn đề là khoảng cách giữa các frame **không đều**:

- Video IPN chạy khoảng 30 FPS, tức cứ khoảng 0,033 giây một frame.
- Webcam thì dao động: lúc 0,033 giây, lúc 0,05 giây, lúc máy bận hay phòng tối còn chậm hơn.

Nếu để nguyên, những thứ phía sau sẽ sai lệch theo nguồn dữ liệu:

- "30 frame" là 1 giây ở IPN, nhưng có thể là 2 giây ở webcam trong phòng tối (15 FPS). Mô hình sẽ thấy cùng một cử chỉ "chậm đi gấp đôi", một biến dạng nó chưa từng gặp khi huấn luyện.
- Tốc độ tay tính giữa hai frame liên tiếp không so sánh được, vì khoảng thời gian giữa chúng mỗi lúc một khác.

Bước này chọn các thời điểm cố định 0, 1/15, 2/15, 3/15 giây…, rồi tính vị trí tay **tại đúng các thời điểm đó** bằng nội suy giữa frame thật ngay trước và frame thật ngay sau. Sau bước này, mọi nguồn trông như được quay bằng một camera 15 FPS hoàn hảo, nhịp tuyệt đối đều. Mô hình không còn phải biết dữ liệu đến từ IPN hay từ webcam.

*Ví dụ (minh hoạ): webcam với nhịp không đều.* Để đơn giản, chỉ xét toạ độ x của cổ tay:

| Frame thật | Thời điểm | x cổ tay |
|---|---|---|
| 1 | 0,000 s | 200 |
| 2 | 0,045 s | 206 |
| 3 | 0,080 s | 212 |
| 4 | 0,140 s | mất tay |
| 5 | 0,170 s | 230 |
| 6 | 0,215 s | 238 |

Đưa về lưới 15 Hz:

| Bước | Thời điểm | Nằm giữa | Kết quả |
|---|---|---|---|
| 0 | 0,000 s | trùng frame 1 | 200 |
| 1 | 0,067 s | frame 2 và 3, cả hai có tay | 209,7 |
| 2 | 0,133 s | frame 3 và 4, frame 4 mất tay | **rỗng** |
| 3 | 0,200 s | frame 5 và 6, cả hai có tay | 235,3 |

Bước 2 để rỗng vì quy tắc: chỉ nội suy giữa hai frame **cùng có tay**. Ngay sau đó, bước 3 của pipeline (vá lỗ hổng ngắn) thấy lỗ chỉ dài 1 bước, hai đầu đều có tay, nên vá thành 222,5. Trong thực tế, phép tính này làm cho cả 42 con số chứ không riêng x cổ tay.

**Đầu ra:** một chuỗi các bước cách đều nhau đúng 1/15 giây. Mỗi bước là một trong hai dạng:

- 21 điểm mốc × 2 toạ độ = 42 con số, hoặc
- rỗng, nếu không nội suy được (cờ "có tay" = không).

Ví dụ, một video IPN 10 giây gồm khoảng 300 frame sẽ thành đúng 150 bước. Một đoạn webcam 10 giây cũng ra 150 bước, dù webcam đã quay bao nhiêu frame.

Lưu ý: ở thời điểm này dữ liệu **vẫn là toạ độ pixel** (chuẩn hoá ở bước 6), **vẫn còn lỗ hổng** (bước 3 vá lỗ ngắn), và **chưa cắt thành cửa sổ** (bước 4).

**Vì sao chọn 15 Hz mà không phải 30 Hz?** Slide không ghi lý do, nhưng tài liệu `03-bieu-dien-khung-xuong-ban-tay.md` (mục 12.1) và cẩm nang `06-cam-nang-thuc-hien-tung-buoc.md` (bước 7) trong project Computer Vision có giải thích. Cử chỉ ngắn nhất trong IPN Hand dài khoảng 9 frame ở 30 FPS, tức khoảng 0,3 giây. Lấy mẫu ở 15 Hz vẫn cho 4–5 điểm dữ liệu cho cử chỉ ngắn nhất, đủ để mô tả nó. Đổi lại, khối lượng tính toán giảm một nửa so với 30 Hz.

### Hỏi đáp: "Bước" là gì, và vì sao mỗi cửa sổ có 18 bước?

**Bước là một điểm trên lưới 15 Hz.** Cứ 1/15 giây (khoảng 0,067 giây) có một bước. Mỗi bước là một bức ảnh chụp nhanh khung xương bàn tay tại đúng thời điểm đó, gồm 21 điểm mốc × 2 toạ độ = 42 con số. Nếu không thấy tay thì bước đó để rỗng.

Dự án dùng chữ "bước" thay vì "frame" để phân biệt hai thứ:

- **Frame** là ảnh thật do camera chụp. Thời điểm của frame không đều: webcam lúc nhanh lúc chậm, IPN khoảng 30 FPS.
- **Bước** là điểm đã được đưa về lưới đều. Giá trị của nó được tính bằng nội suy từ các frame thật xung quanh, nên hai bước liền nhau luôn cách nhau đúng 1/15 giây, dù dữ liệu đến từ nguồn nào.

Nói gọn: frame là dữ liệu thô từ camera, bước là dữ liệu đã chuẩn hoá về thời gian.

**Vì sao là 18 bước.** Con số 18 không được chọn riêng. Nó là kết quả của hai lựa chọn khác:

> độ dài cửa sổ × tần số lưới = 1,2 giây × 15 bước/giây = **18 bước**

Nếu đổi một trong hai, số bước đổi theo. Lưới 30 Hz thì cửa sổ 1,2 giây có 36 bước. Cửa sổ 0,8 giây ở lưới 15 Hz thì có 12 bước. Vì vậy, khi trình bày, nên nói "cửa sổ 1,2 giây, tức 18 bước", để người nghe thấy 18 đến từ đâu.

**Hình dung khối 18 × 21 × 2.** Một cửa sổ giống một bảng có 18 dòng và 42 cột:

| Bước | Thời điểm | Điểm 0 (cổ tay) x, y | Điểm 1 x, y | … | Điểm 20 x, y |
|---|---|---|---|---|---|
| 1 | 0,000 s | 42 số trên cùng một dòng | | | |
| 2 | 0,067 s | | | | |
| … | … | | | | |
| 18 | 1,133 s | | | | |

- **18** là trục thời gian: xem tay ở thời điểm nào.
- **21** là xem điểm mốc nào: cổ tay, đầu ngón cái, đầu ngón trỏ…
- **2** là toạ độ x (ngang) và y (dọc).

Tổng cộng 18 × 42 = 756 con số. Nếu dựng lại thành hình, đây là một đoạn phim ngắn gồm 18 khung xương bàn tay liên tiếp.

*Một chi tiết nhỏ, phòng khi bị hỏi.* Bảng trên cho thấy bước cuối nằm ở 1,133 giây chứ không phải 1,2 giây. Lý do là 18 điểm chỉ tạo ra 17 khoảng cách giữa chúng: 17 × 1/15 ≈ 1,133 giây. Cửa sổ vẫn được gọi là "1,2 giây" vì mỗi bước đại diện cho một khoảng 1/15 giây, và 18 khoảng như vậy cộng lại là đúng 1,2 giây.

### Hỏi đáp: Cửa sổ trượt mỗi 0,2 giây có ý nghĩa gì, và cho ra kết quả gì?

**Ý nghĩa: cứ 0,2 giây, hệ thống lại nhìn 1,2 giây gần nhất và hỏi "có cử chỉ không?".** Bước này gồm hai con số, mỗi số có lý do riêng.

*Vì sao cần cửa sổ (1,2 giây).* Nhìn một frame đơn lẻ thì không biết tay đang vuốt hay đứng yên: ảnh chụp bàn tay giữa cú vuốt trông giống hệt bàn tay đặt yên ở đó. Cử chỉ là chuyển động, nên mô hình phải được xem một đoạn lịch sử. Cửa sổ chính là "đoạn quá khứ gần nhất" mà mô hình được nhìn mỗi lần quyết định. Độ dài 1,2 giây là một thoả hiệp:

- Nó đủ dài để chứa trọn động tác chính (khoảng 0,3 giây) cộng một ít ngữ cảnh trước và sau.
- Nó đủ ngắn để hệ thống không phản ứng chậm. Cửa sổ dài hơn thì phải chờ lâu hơn mới đủ dữ liệu. Phase 8 sẽ thử 0,8 / 1,2 / 1,6 giây để kiểm tra lựa chọn này.

*Vì sao trượt mỗi 0,2 giây.* Người dùng có thể bắt đầu cử chỉ vào bất kỳ lúc nào, nên hệ thống phải kiểm tra lại đều đặn. Bước trượt quyết định tần suất kiểm tra: 0,2 giây là 5 lần mỗi giây. Đây cũng là một thoả hiệp:

- **Trượt quá thưa**, ví dụ 1,2 giây (các cửa sổ nối đuôi, không chồng nhau): tính toán ít hơn. Nhưng một cử chỉ có thể bị cắt đôi, động tác chính rơi đúng chỗ giao giữa hai cửa sổ, và không cửa sổ nào chứa trọn nó. Hệ thống bỏ sót, và phải chờ tới 1,2 giây mới kiểm tra lại.
- **Trượt quá dày**, ví dụ mỗi bước (0,067 giây): phản ứng nhanh hơn chút ít, nhưng tốn gấp ba lần tính toán, và các cửa sổ gần như trùng nhau.
- **Với 0,2 giây**, mỗi cử chỉ được "bắt" ở vài cửa sổ liên tiếp. Theo luật gán nhãn ở slide 7 (khoảnh khắc chính cách hai mép ít nhất 3 bước), khoảnh khắc chính nằm gọn trong khoảng 4 cửa sổ liền nhau. Hệ thống có nhiều cơ hội nhận ra cử chỉ, nên không phụ thuộc vào một lần duy nhất. Đây cũng là lý do nhãn trong demo nhấp nháy liên tục hơn một giây (Phụ lục E), và lý do cần máy trạng thái để gom lại thành một lệnh.

*Một tác dụng phụ khi huấn luyện.* Trượt dày tạo ra rất nhiều cửa sổ từ mỗi video. Mô hình thấy cùng một cử chỉ ở nhiều vị trí khác nhau trong cửa sổ, lúc ở giữa, lúc lệch về một bên. Cái giá là hai cửa sổ liền nhau chung 15 trên 18 bước, gần như giống hệt nhau. Vì thế bắt buộc phải chia tập theo người, nếu không sẽ bị rò rỉ dữ liệu (Phụ lục C).

**Đầu vào:** chuỗi bước đều nhịp 15 Hz, đã vá lỗ ngắn (kết quả của bước 2 và 3). Ví dụ, một video 10 giây cho 150 bước.

**Đầu ra:** một danh sách cửa sổ. Mỗi cửa sổ là 18 bước liên tiếp, mỗi bước 21 điểm × 2 toạ độ, tức một khối **18 × 21 × 2 = 756 con số**. Mỗi cửa sổ đi kèm vị trí của nó trên dòng thời gian, để sau này gán nhãn (slide 7). Với video 10 giây:

```
cửa sổ  1: bước   0 → 17     (0,0 s → 1,2 s)
cửa sổ  2: bước   3 → 20     (0,2 s → 1,4 s)
cửa sổ  3: bước   6 → 23     (0,4 s → 1,6 s)
...
cửa sổ 45: bước 132 → 149    (8,8 s → 10,0 s)
```

Tổng cộng 45 cửa sổ. Công thức chung: số cửa sổ ≈ (thời lượng − 1,2) / 0,2 + 1.

Lưu ý về đầu ra ở thời điểm này:

- **vẫn là toạ độ pixel**: mỗi cửa sổ sẽ được chuẩn hoá riêng ở bước 6, lấy cổ tay frame đầu làm gốc (Phụ lục A);
- **có thể còn lỗ dài để rỗng**: cửa sổ mất tay quá nhiều sẽ bị luật "thiếu tay" xếp vào "không cử chỉ" (slide 8);
- **chưa có nhãn**: nhãn được gán sau, dựa trên vị trí của cửa sổ so với khoảnh khắc chính (slide 7).

*Khác biệt giữa huấn luyện và chạy thật.* Khi huấn luyện, bước này cắt cả video thành một danh sách cửa sổ một lượt. Khi chạy demo, nó không tạo danh sách: cứ 0,2 giây, hệ thống lấy 18 bước cuối trong bộ đệm ra làm **một** cửa sổ mới (Phụ lục E). Cách cắt hoàn toàn giống nhau, chỉ khác là làm dần theo thời gian thực.

### Hỏi đáp: Lưới 15 Hz liên hệ gì với việc trượt mỗi 0,2 giây?

Hai bước liên hệ chặt chẽ, nhưng làm hai việc khác nhau:

- **Lưới 15 Hz** quyết định dữ liệu được chia nhỏ đến mức nào theo thời gian. Nhờ nó, dù webcam chạy 20 FPS hay 30 FPS, dữ liệu vào pipeline luôn có cùng nhịp.
- **Trượt 0,2 giây** quyết định bao lâu hệ thống đưa ra một dự đoán: 5 dự đoán mỗi giây, cũng không phụ thuộc FPS của webcam.

*Chỗ chúng khớp với nhau.* Mọi độ dài thời gian của cửa sổ đều là số nguyên lần của một bước:

- 1,2 giây × 15 = đúng **18 bước**
- 0,2 giây × 15 = đúng **3 bước**

Vì vậy cửa sổ luôn bắt đầu và kết thúc đúng trên một điểm của lưới, và mỗi lần trượt là dịch đúng 3 bước (xem danh sách cửa sổ ở mục Hỏi đáp trên). Hai cửa sổ liền nhau dùng chung 15 trên 18 bước, nên chỉ có 3 bước mới.

Điều này quan trọng vì hai lý do:

1. **Mọi cửa sổ có đúng 18 bước.** Mô hình nhận một khối dữ liệu cùng kích thước mỗi lần (18 × 21 × 2). Với LSTM ở Phase 7 thì đây là yêu cầu bắt buộc.
2. **Không phải nội suy thêm ở mép cửa sổ.** Nếu số bước không chẵn, mép cửa sổ sẽ rơi vào giữa hai điểm lưới. Ví dụ ở 12 Hz, 0,2 giây là 2,4 bước; khi đó các cửa sổ sẽ lúc dịch 2 bước, lúc dịch 3 bước, không đều.

Trong demo, mối liên hệ này thể hiện trực tiếp: cứ 0,2 giây thời gian thật trôi qua thì bộ đệm nhận thêm đúng 3 bước mới, và hệ thống lấy 18 bước cuối ra làm cửa sổ.

*Lưu ý nếu bị hỏi.* Trượt 0,2 giây không bắt buộc phải dùng 15 Hz. Điều kiện chỉ là tần số nhân với 0,2 và với 1,2 đều ra số nguyên, nên 10 Hz hay 30 Hz cũng khớp. Lý do chọn 15 Hz là chuyện khác, đã nêu ở mục Hỏi đáp đầu tiên: đủ điểm cho cử chỉ ngắn nhất, và tính toán chỉ bằng một nửa 30 Hz.

**Thuật ngữ**

- **Pipeline**: dây chuyền xử lý nhiều bước theo thứ tự cố định.
- **Tiền xử lý** (preprocessing): các bước chuẩn bị dữ liệu trước khi vào mô hình.
- **Theo dõi** (tracking): bám theo một đối tượng qua các frame liên tiếp.
- **Hz** (hertz): số lần mỗi giây.
- **Bước** (time step): một điểm trên lưới thời gian đều. Ở đây 1 bước = 1/15 giây. Khác với frame: frame là ảnh thật từ camera, thời điểm không đều; bước luôn cách đều.
- **Nội suy** (interpolation): ước lượng giá trị nằm giữa hai giá trị đã biết.
- **Cửa sổ trượt** (sliding window): đoạn dữ liệu có độ dài cố định, dịch dần theo thời gian.

---

## Slide 5 — 15 đặc trưng, chia thành 5 nhóm

**Ý chính:** Từ mỗi cửa sổ, hệ thống tính 15 con số tóm tắt chuyển động. Mỗi con số có ý nghĩa vật lý dễ hiểu, như "cổ tay đi ngang bao xa" hay "hai ngón mở ra bao nhiêu".

**Giải thích**

*Đặc trưng là gì.* Mỗi cửa sổ chứa 18 bước × 21 điểm × 2 toạ độ = 756 con số. **Đặc trưng** (feature) là một con số tóm tắt một khía cạnh của dữ liệu. Giống như mô tả một người bằng chiều cao, cân nặng, tuổi thay vì đưa cả tấm ảnh. Rút 756 con số xuống 15 con số có ý nghĩa giúp các mô hình đơn giản (luật, rừng ngẫu nhiên) làm việc tốt, và giúp con người hiểu được mô hình đang dựa vào gì. Cách rút cụ thể, kèm ví dụ tính tay: xem mục Hỏi đáp cuối slide này.

Một quy ước nhỏ: "đầu" và "cuối" là **trung bình của ba bước đầu và ba bước cuối**, thay vì chỉ lấy một bước, để bớt nhạy với rung tay.

*Năm nhóm đặc trưng.*

| Nhóm | Đặc trưng | Ý nghĩa | Dùng để bắt |
|---|---|---|---|
| Độ xòe bàn tay (5) | đầu, cuối, thay đổi, biên độ, xu hướng | Các ngón đang duỗi xa ra hay co lại | Mở hoặc nắm cả bàn tay |
| Độ mở cái–trỏ (2) | thay đổi, biên độ | Khoảng cách đầu ngón cái (điểm 4) tới đầu ngón trỏ (điểm 8) | Chụm hoặc mở ngón (zoom) |
| Chuyển động cổ tay (5) | dời ngang, dời dọc, tốc độ ngang đỉnh, tốc độ ngang trung bình, tốc độ dọc đỉnh | Cổ tay đi bao xa, nhanh cỡ nào | Vuốt |
| Hình dạng quỹ đạo (2) | độ thẳng, tỉ lệ ngang | Đường đi thẳng hay vòng vèo, ngang hay dọc | Vuốt một chiều hay vẫy qua lại |
| Chất lượng (1) | tỉ lệ bước có tay | Cửa sổ bị mất tay nhiều hay ít | Độ tin cậy của cửa sổ |

Ý nghĩa từng từ trong cột "Đặc trưng":

- **Thay đổi**: chênh lệch giữa cuối và đầu cửa sổ. Ví dụ độ mở cái–trỏ tăng thêm 0,8 lòng bàn tay.
- **Biên độ**: khoảng cách giữa giá trị lớn nhất và nhỏ nhất trong cửa sổ, cho biết đại lượng dao động mạnh cỡ nào.
- **Xu hướng**: nhìn chung cả cửa sổ đang tăng dần hay giảm dần.
- **Dời ngang / dời dọc**: cổ tay dịch chuyển bao xa theo chiều ngang / dọc, từ đầu đến cuối cửa sổ.
- **Tốc độ ngang đỉnh**: tốc độ ngang lớn nhất trong cửa sổ, đơn vị lòng bàn tay mỗi giây. Cú vuốt có một khoảnh khắc tay lao rất nhanh.
- **Tốc độ ngang trung bình**: tốc độ ngang tính trung bình, có dấu (xem bên dưới).
- **Độ thẳng**: về ý nghĩa, so sánh khoảng cách từ điểm đầu đến điểm cuối với tổng quãng đường tay đã đi. Vuốt thẳng một chiều cho giá trị gần 1; vẫy qua lại thì điểm cuối gần điểm đầu, giá trị gần 0.
- **Tỉ lệ ngang**: phần chuyển động theo chiều ngang so với tổng chuyển động. Nó giúp tách vuốt ngang khỏi hất lên, hất xuống.

*Đặc trưng có dấu.* Có 5 đặc trưng mang dấu dương hoặc âm, và dấu cho biết hướng:

- thay đổi độ xòe và xu hướng độ xòe (mở ra hay nắm lại);
- thay đổi độ mở cái–trỏ (zoom in hay zoom out);
- dời ngang và tốc độ ngang trung bình (sang trái hay sang phải của ảnh).

Trong ảnh, trục x tăng từ trái sang phải, trục y tăng từ trên xuống dưới. Dời ngang dương nghĩa là tay đi về phía bên phải **của ảnh**.

*Đặc trưng không tự quyết đâu là trái, đâu là phải.* Phần tính đặc trưng chỉ trả về một con số có dấu. Việc dấu dương nghĩa là "vuốt trái" hay "vuốt phải" do một **hằng số hướng** quyết định, và hằng số này được đo trên dữ liệu (slide 6). Tách riêng như vậy để quy ước hướng chỉ nằm ở một chỗ, không bị lật hai lần ở hai nơi khác nhau.

*Không bao giờ rỗng.* Đặc trưng luôn tính được, kể cả khi cửa sổ có tới 30% số bước mất tay. Mô hình không bao giờ nhận một đầu vào thiếu.

*Một câu chuyện trong lời thoại.* Ban đầu, zoom được đo bằng độ xòe trung bình của năm ngón. Nhưng khi xem dữ liệu thật, cử chỉ zoom của IPN chỉ chụm và mở ba đầu ngón cái, trỏ, giữa; ngón nhẫn và ngón út gập suốt. Vì vậy độ xòe trung bình thay đổi rất ít. Khoảng cách đầu ngón cái tới đầu ngón trỏ tách hai lớp zoom tốt hơn hẳn, nên nhóm "độ mở cái–trỏ" được thêm vào (số liệu ở Phụ lục D).

### Hỏi đáp: Làm sao rút 756 con số xuống 15? 15 con số đó có phải là đặc trưng không?

Đúng, 15 con số đó chính là 15 đặc trưng. Mỗi đặc trưng là một công thức: nó nhận cả khối 756 số của một cửa sổ và trả về đúng một số. Có 15 công thức nên ra 15 số. Đây không phải nén dữ liệu, mà là **chọn lọc**: phần lớn trong 756 số không được dùng, và việc bỏ đi là có chủ ý. Cách làm này gọi là **thiết kế đặc trưng** (feature engineering).

**Rút gọn theo hai tầng**

```
756 số = 18 bước × 42 số
   │  Tầng 1: ở mỗi bước, chỉ giữ vài đại lượng có ý nghĩa
   ▼
18 bước × 4 tín hiệu + cờ có tay   (cổ tay x, cổ tay y, độ xòe, độ mở cái–trỏ)
   │  Tầng 2: mỗi tín hiệu có 18 giá trị → tóm thành vài con số
   ▼
15 đặc trưng
```

*Tầng 1.* Trong 21 điểm mốc, chỉ vài điểm được dùng trực tiếp:

- điểm 0 (cổ tay), để đo chuyển động của cả bàn tay;
- điểm 4 và 8 (đầu ngón cái và đầu ngón trỏ), để đo độ mở cái–trỏ;
- các đầu ngón, để đo độ xòe.

Ở mỗi bước, 42 số rút còn khoảng 4 số, cộng một cờ có tay hay không.

*Tầng 2.* Mỗi tín hiệu là một dãy 18 giá trị theo thời gian, và được tóm lại như sau:

| Tín hiệu (18 giá trị) | Lấy từ | Tóm thành | Số đặc trưng |
|---|---|---|---|
| Độ xòe bàn tay | các đầu ngón | đầu, cuối, thay đổi, biên độ, xu hướng | 5 |
| Độ mở cái–trỏ | điểm 4 và 8 | thay đổi, biên độ | 2 |
| Cổ tay theo chiều ngang | điểm 0 (x) | dời ngang, tốc độ ngang đỉnh, tốc độ ngang trung bình | 3 |
| Cổ tay theo chiều dọc | điểm 0 (y) | dời dọc, tốc độ dọc đỉnh | 2 |
| Đường đi của cổ tay | điểm 0 (x và y) | độ thẳng, tỉ lệ ngang | 2 |
| Cờ có tay | — | tỉ lệ bước có tay | 1 |
| **Tổng** | | | **15** |

Slide và lời thoại chỉ mô tả ý nghĩa của các đặc trưng. Công thức chính xác của độ xòe, xu hướng và độ thẳng nằm trong code của dự án.

**Ví dụ (minh hoạ): tóm 18 giá trị của một cú vuốt**

Vị trí ngang của cổ tay sau chuẩn hoá, đơn vị lòng bàn tay, qua 18 bước:

```
0,00  0,00  0,01  0,02  0,05  0,10  0,25  0,60  1,10  1,55  1,85  2,00  2,05  2,06  2,06  2,05  2,06  2,06
```

Từ 18 số này, tính ra ba đặc trưng:

- **Dời ngang** = cuối − đầu ≈ 2,06 lòng bàn tay.
- **Tốc độ ngang đỉnh**: chênh lệch lớn nhất giữa hai bước liền nhau là 0,50 (từ 0,60 lên 1,10). Mỗi bước dài 1/15 giây, nên tốc độ là 0,50 × 15 = **7,5 lòng bàn tay/giây**, vượt ngưỡng 4,026 của mô hình luật (slide 8).
- **Tốc độ ngang trung bình** ≈ 2,06 / 1,13 giây ≈ 1,8 lòng bàn tay/giây, dấu dương. Dương nghĩa là tay đi về phía phải của ảnh. Với hằng số hướng +1 (slide 6), đây là **vuốt trái**.

18 con số đã thành 3 con số trả lời ba câu hỏi: tay đi bao xa, nhanh cỡ nào, và theo hướng nào.

**Vì sao cần nhiều đặc trưng cùng lúc** (minh hoạ)

| | Vuốt | Vẫy qua lại | Gõ phím |
|---|---|---|---|
| Dời ngang | lớn (≈ 2) | gần 0 | gần 0 |
| Tốc độ ngang đỉnh | cao | cao | thấp |
| Độ thẳng | gần 1 | gần 0 | thấp |

Vẫy tay nhanh không kém vuốt. Nếu chỉ dựa vào tốc độ, hai cử chỉ này không tách được. Phải thêm dời ngang và độ thẳng thì mới phân biệt được: vẫy qua lại thì tay quay về gần chỗ cũ, còn vuốt thì đi thẳng một chiều.

**Bỏ đi nhiều như vậy có sao không?** Có đánh đổi:

- **Lợi:** mô hình đơn giản như luật hay rừng ngẫu nhiên làm việc tốt với ít số. Con người hiểu được mô hình đang dựa vào gì. Mô hình cũng cần ít dữ liệu hơn, điều quan trọng khi train chỉ có khoảng 415 cửa sổ dương mỗi lớp.
- **Rủi ro:** nếu 15 số này bỏ mất đúng thông tin cần để phân biệt hai lớp, thì không mô hình nào lấy lại được. Đây là lý do có cổng kiểm tra (Phụ lục D). Nó cũng có thể là nguyên nhân của 44% báo nhầm (slide 9): động tác chỉ trỏ và cú hất trông khá giống nhau khi chỉ nhìn qua 15 con số này.

Vì vậy pipeline còn một nhánh thứ hai, ghi ở bước 7 của slide 4: "hoặc đưa vào mô hình chuỗi". Ở Phase 7, LSTM sẽ nhận thẳng 18 bước × 42 số, không qua 15 đặc trưng, để tự học xem điều gì là quan trọng.

**Thuật ngữ**

- **Đặc trưng** (feature): con số tóm tắt một khía cạnh của dữ liệu.
- **Thiết kế đặc trưng** (feature engineering): việc con người tự nghĩ ra các đặc trưng có ý nghĩa, như ở slide này.
- **Biên độ** (range, amplitude): chênh lệch giữa giá trị lớn nhất và nhỏ nhất.
- **Đặc trưng có dấu** (signed feature): đặc trưng có thể âm hoặc dương, dấu mang thông tin hướng.
- **Hằng số hướng**: một con số (+1 hoặc −1) quyết định dấu dương ứng với trái hay phải (slide 6).

---

## Slide 6 — Trích điểm mốc toàn bộ IPN và đo quy ước hướng

**Ý chính:** Dự án chạy MediaPipe trên toàn bộ 200 video, rồi dùng chính dữ liệu để xác định "trái" nghĩa là gì, và thống kê đặc điểm của các cử chỉ. Một phát hiện ở đây dẫn tới thay đổi lớn nhất của dự án.

**Giải thích**

*Cột 1: trích điểm mốc.* "Trích" (extract) nghĩa là chạy MediaPipe trên từng frame của từng video và lưu lại toạ độ 21 điểm mốc. Trên slide có:

- **200/200 video.** Theo lời thoại, không video nào lỗi.
- **Lưu toạ độ thô, chưa chuẩn hoá.** Chạy MediaPipe mất hơn 2 giờ, còn cách chuẩn hoá có thể còn thay đổi. Giữ dữ liệu thô thì sau này đổi cách chuẩn hoá cũng không phải trích lại. Mỗi frame được lưu kèm **mốc thời gian** (timestamp), **cờ có tay** (một giá trị có/không cho biết frame này thấy tay hay không) và đoạn nhãn tương ứng.
- **Kiểm lại toàn bộ sau khi trích.**
- **189 đoạn hất trái / hất phải, dùng để đo quy ước hướng.** Đây là các đoạn của phép đo ở cột 2. "Đoạn" là gì và đo thế nào: xem mục Hỏi đáp cuối slide.

Lời thoại nói thêm ba ý không còn trên slide:

- **2,27 giờ với 4 tiến trình song song.** Máy chạy 4 video cùng lúc trên 4 lõi CPU, nhanh hơn chạy lần lượt.
- **Chạy lại thì tiếp tục, không làm lại từ đầu.** Video đã xong thì bỏ qua, video lỗi được ghi ra một danh sách riêng. Nếu máy tắt giữa chừng thì không mất công.
- **Chạy trên máy, không dùng Colab.** Google Colab là dịch vụ cho chạy chương trình Python trên máy chủ của Google, rất tiện. Nhưng phiên bản thư viện trên đó có thể khác máy chạy demo, và điểm mốc có thể lệch nhẹ. Chạy trên chính máy sẽ chạy demo thì phiên bản MediaPipe, OpenCV và bộ giải mã trùng với hệ thống thật.

*Cột 2: quy ước hướng.* Câu hỏi là: "hất trái" là trái của ai? Có thể là trái của người làm, hoặc trái của bức ảnh. Thêm nữa, hình hiển thị thường bị lật như gương. Rất dễ nhầm.

Hãy hình dung camera như một người ngồi đối diện bạn. Bạn đưa tay sang **trái của bạn**, thì người đối diện thấy tay bạn đi sang **phải của họ**. Trong ảnh camera chưa lật, tay bạn đi về phía bên phải của ảnh, tức x tăng, dời ngang dương.

Thay vì đoán, dự án đo trên 189 đoạn hất trái và hất phải:

| Lớp | Trung vị dời ngang | Nghĩa là |
|---|---|---|
| Hất trái | +0,46 lòng bàn tay | Tay đi về phía phải của ảnh |
| Hất phải | −0,54 lòng bàn tay | Tay đi về phía trái của ảnh |

Kết luận: "hất trái" là tay đi về bên trái **của chính người làm**. Hằng số hướng được đặt bằng **+1**. Hằng số này chỉ được dùng ở đúng một nơi trong chương trình, nên không bao giờ bị lật hai lần. Nếu sau này thử trên webcam mà thấy hướng bị ngược, chỉ cần đổi hằng số thành −1, không phải sửa code.

Một chi tiết trong lời thoại: những đoạn bị mất tay ở đầu hoặc cuối cho đặc trưng bằng 0. Các số 0 này kéo trung vị về gần 0 và suýt làm sai kết luận, nên phải loại chúng ra trước khi đo.

*Zoom cũng được kiểm.* Thay đổi độ xòe trung bình là +0,20 với zoom in (tay mở ra) và −0,30 với zoom out (tay chụm lại). Như vậy bảng ánh xạ zoom in / zoom out đúng chiều.

*Cột 3: bộ cử chỉ.* Thống kê trên toàn bộ dữ liệu cho bốn con số:

- Mỗi cử chỉ kéo dài khoảng **2 giây**,
- nhưng **động tác chính** chỉ khoảng **0,3 giây**. Phần còn lại là **chuẩn bị** (đưa tay lên, vào tư thế) và **thu tay**.
- Khoảng **90%** cử chỉ dài hơn cửa sổ 1,2 giây, nên một cửa sổ thường không chứa trọn một cử chỉ.
- Khoảng **3–6%** frame trong lúc làm cử chỉ bị mất tay, chủ yếu do tay chuyển động nhanh nên ảnh bị mờ.

Phát hiện "2 giây nhưng động tác chính chỉ 0,3 giây" dẫn tới cách gán nhãn mới ở slide 7. Tài liệu hướng dẫn cách làm bộ cử chỉ hiện đang ở bản nháp.

### Hỏi đáp: "189 đoạn" là gì?

**189 đoạn** là số lần làm cử chỉ hất trái và hất phải trong IPN mà dự án đã dùng để đo quy ước hướng.

*"Đoạn" là gì.* Mỗi video IPN được quay liền một mạch. Người diễn làm nhiều cử chỉ nối tiếp nhau, xen giữa là những khoảng không cử chỉ. File nhãn chia video thành các **đoạn**. Mỗi đoạn là một dòng ghi: lớp gì, từ frame nào đến frame nào. Ví dụ minh hoạ:

```
video X:  … không cử chỉ | hất trái (frame 1520–1580) | không cử chỉ | zoom in (frame 1700–1760) | …
```

Một đoạn là trọn một lần làm cử chỉ, dài khoảng 2 giây. Nó khác với **cửa sổ** (lát cắt 1,2 giây). Phép đo này dùng nguyên các đoạn, vì nó diễn ra trước bước cắt cửa sổ và gán nhãn ở slide 7.

*Cách đo trên 189 đoạn.* Theo cẩm nang `06-cam-nang-thuc-hien-tung-buoc.md` trong project (mục 11.3), quy trình như sau:

1. Với mỗi đoạn hất trái hoặc hất phải, tính **dời ngang của cổ tay từ đầu tới cuối đoạn**, đơn vị lòng bàn tay. Mỗi đoạn cho ra đúng một con số.
2. Gom các con số theo lớp, được hai danh sách: một cho hất trái, một cho hất phải.
3. Lấy **trung vị** của từng danh sách: hất trái ra +0,46, hất phải ra −0,54.
4. Hất trái có dấu dương, nghĩa là tay đi về phía phải của ảnh. Vậy "trái" là trái của người làm, và hằng số hướng bằng +1.

Có hai chi tiết đáng chú ý:

- **Dùng trung vị, không dùng trung bình.** Vài đoạn có điểm mốc nhảy bất thường hoặc người diễn làm lệch kiểu. Trung vị ít bị những đoạn này kéo lệch.
- **Loại các đoạn cho kết quả bằng 0.** Đoạn bị mất tay ở đầu hoặc cuối cho dời ngang bằng 0, không phải vì tay đứng yên mà vì không đo được. Các số 0 này suýt kéo trung vị về gần 0, nên phải loại trước khi đo.

*Vì sao 189 đoạn là đủ.* Phép đo chỉ cần trả lời một câu: dấu dương hay âm. Hai trung vị nằm rõ ở hai phía của 0, độ lớn khoảng 0,5 lòng bàn tay. Con số này gấp khoảng 30 lần mức rung tay đo được (0,016 lòng bàn tay, Phụ lục C). Vì vậy kết luận không phụ thuộc vào vài đoạn lẻ, và thêm dữ liệu cũng không làm nó đổi.

*Đừng hiểu nhầm 189 là toàn bộ dữ liệu.* 200 video, mỗi video có nhiều cử chỉ nối tiếp, nên tổng số đoạn cử chỉ lớn hơn 189 rất nhiều. 189 chỉ là số đoạn hất trái và hất phải dùng cho phép đo hướng.

*Những gì slide và kịch bản không ghi.* Nếu bị hỏi kỹ, nên kiểm tra kết quả đo trong code hoặc log của dự án trước. Có ba điều chưa được ghi:

- mỗi lớp có bao nhiêu đoạn trong 189;
- phép đo dùng cả bộ dữ liệu hay chỉ tập train;
- 189 là số đoạn trước hay sau khi loại các đoạn cho kết quả bằng 0.

**Thuật ngữ**

- **Đoạn** (segment): một lần làm cử chỉ trong file nhãn IPN, gồm lớp, frame bắt đầu và frame kết thúc.
- **Trích điểm mốc** (landmark extraction): chạy MediaPipe trên video và lưu toạ độ.
- **Tiến trình song song** (parallel processes): nhiều phần việc chạy cùng lúc trên các lõi CPU khác nhau.
- **Dữ liệu thô** (raw data): dữ liệu chưa qua xử lý.
- **Mốc thời gian** (timestamp): thời điểm của một frame, tính bằng giây.
- **Cờ** (flag): một giá trị đúng/sai đánh dấu một trạng thái.
- **Google Colab**: dịch vụ chạy Python trên máy chủ của Google.
- **Quy ước hướng / hằng số hướng**: cách hiểu "trái/phải", và con số +1 hoặc −1 mã hoá cách hiểu đó.
- **Động tác chính**: phần ngắn nhất, nhanh nhất của cử chỉ, nơi tay thực sự hất hoặc chụm.

---

## Slide 7 — Rule gán nhãn cửa sổ

**Ý chính:** Một cử chỉ kéo dài qua nhiều cửa sổ. Chỉ cửa sổ chứa trọn động tác chính mới được gán nhãn cử chỉ. Nhờ vậy mô hình không học nhầm rằng "tay đang chuẩn bị" cũng là cử chỉ.

**Giải thích**

*Vì sao phải gán nhãn lại.* Nhãn của IPN gắn cho cả một **đoạn** video, ví dụ "từ giây 10,0 đến giây 12,0 là hất trái". Nhưng mô hình học và dự đoán trên từng **cửa sổ** 1,2 giây. Mỗi cử chỉ dài khoảng 2 giây, nên nó trải qua nhiều cửa sổ. Câu hỏi là: cửa sổ nào nên mang nhãn "hất trái"?

Cửa sổ mang nhãn cử chỉ gọi là **cửa sổ dương** (positive). Cửa sổ mang nhãn "không cử chỉ" gọi là **cửa sổ âm** (negative). Slide dùng nguyên hai từ tiếng Anh này.

*Luật ban đầu và vấn đề của nó.* Slide nhắc tới luật cũ này và lý do bỏ nó. Kế hoạch ban đầu đặt luật: cửa sổ là dương nếu cử chỉ chiếm ít nhất 60% số bước của cửa sổ. Khi đo, **49%** cửa sổ dương theo luật này không chứa động tác chính. Chúng chỉ chứa phần chuẩn bị hoặc phần thu tay. Nói cách khác, gần một nửa số ví dụ "vuốt" đang dạy mô hình rằng tay đang đưa lên chuẩn bị cũng là vuốt.

*Giải pháp: neo nhãn vào khoảnh khắc chính.*

- **Khoảnh khắc chính** là bước mà tín hiệu thay đổi nhanh nhất trong đoạn cử chỉ:
  - với vuốt, tín hiệu là vị trí ngang của cổ tay;
  - với zoom, tín hiệu là độ mở cái–trỏ.
- Tín hiệu được **làm mượt** qua 3 bước trước khi tìm. Làm mượt (smoothing) là lấy trung bình mỗi bước với các bước lân cận, để một cú giật do nhiễu không bị nhầm là khoảnh khắc chính.
- Chỉ xét **độ lớn** của thay đổi, không xét dấu. Nếu xét dấu, cách gán nhãn sẽ ngầm phụ thuộc vào quy ước hướng, và quy ước hướng lại được đo bằng chính dữ liệu đã gán nhãn. Bỏ dấu để tránh vòng luẩn quẩn này.
- Cửa sổ là **dương** khi khoảnh khắc chính nằm bên trong và cách hai mép cửa sổ ít nhất **3 bước** (0,2 giây). Khoảng cách này gọi là **biên**, để cửa sổ chứa được cả một ít trước và sau động tác.
- Cửa sổ có chạm vào cử chỉ mà không chứa khoảnh khắc chính thì **bỏ hẳn**, không dùng để huấn luyện. Nó không được gán "không cử chỉ", vì nó chứa một phần cử chỉ thật. Gán nó là nền cũng sai, và sẽ dạy mô hình những điều mâu thuẫn.

*Hình dòng thời gian trên slide.* Trong sơ đồ dưới, mỗi ký tự là một bước (1/15 giây), mỗi cửa sổ dài 18 ký tự:

```
cử chỉ    ──────────░░░░░░░░░░░░░█████░░░░░░░░░░░░────────────────────
cửa sổ A       [────────────────]
cửa sổ B                  [════════════════]
cửa sổ C                         [────────────────]
cửa sổ D                                           [────────────────]

─ không cử chỉ    ░ chuẩn bị / thu tay    █ động tác chính (~0,3 giây)
A: bỏ (chạm phần chuẩn bị, chưa tới động tác chính)
B: DƯƠNG / positive (chứa động tác chính, cách hai mép ít nhất 3 bước)
C: bỏ (động tác chính nằm sát mép trái)
D: không cử chỉ (không chạm cử chỉ nào)
```

*Có vi phạm tính nhân quả không?* Để tìm khoảnh khắc chính, chương trình nhìn cả đoạn cử chỉ, tức là dùng cả "tương lai". Điều này không vi phạm tính nhân quả, vì đây là **nhãn**, không phải đầu vào. Nhãn là **chân lý tham chiếu** (ground truth), được chuẩn bị ngoại tuyến, giống như chính file nhãn IPN do con người xem lại video và ghi. Mô hình không bao giờ nhìn thấy nhãn khi dự đoán; đầu vào của nó vẫn chỉ là quá khứ. Giống như đáp án đề thi: giáo viên soạn đáp án sau khi biết cả đề, nhưng học sinh làm bài thì không thấy đáp án.

*Luật không chọn theo cảm tính.* Dự án:

- so ba luật gán nhãn bằng ba chỉ số đo trên tập train;
- tách cửa sổ dương thành hai nhóm, có và không chứa động tác chính, để biết lỗi nằm ở nhãn hay ở đặc trưng;
- thử hai mức biên, 0 bước và 3 bước. Chỉ biên 3 bước qua được điều kiện về hướng.

*Cái giá (theo lời thoại).* Số cửa sổ dương mỗi lớp giảm từ khoảng 950 xuống khoảng 415. Ít dữ liệu hơn, nhưng dữ liệu đúng hơn.

**Thuật ngữ**

- **Gán nhãn** (labeling): quyết định nhãn cho từng ví dụ.
- **Cửa sổ dương / âm** (positive / negative window): cửa sổ mang nhãn cử chỉ / mang nhãn "không cử chỉ".
- **Khoảnh khắc chính** (peak moment): bước tín hiệu đổi nhanh nhất trong cử chỉ.
- **Làm mượt** (smoothing): lấy trung bình với các giá trị lân cận để bớt nhiễu.
- **Biên** (margin): khoảng cách tối thiểu từ khoảnh khắc chính tới mép cửa sổ.
- **Chân lý tham chiếu** (ground truth): đáp án được coi là đúng, dùng để huấn luyện và chấm điểm.

---

## Slide 8 — Mô hình luật ngưỡng

**Ý chính:** Mô hình đầu tiên là một bộ luật "nếu… thì…" trên ba đặc trưng đã qua cổng kiểm tra (Phụ lục D), với các ngưỡng tính tự động từ tập train. Nó là đường cơ sở, đồng thời là phép thử cho cả pipeline.

**Giải thích**

*Mô hình luật.* Đây là mô hình đơn giản nhất: con người viết luật, máy chỉ tính các **ngưỡng** (threshold), tức mức cắt. Vượt ngưỡng thì coi là "có". Mô hình luật không cần học máy phức tạp, dễ hiểu, và rất hợp để kiểm tra pipeline: nếu cả luật đơn giản cũng không chạy được, lỗi chắc chắn nằm ở dữ liệu hay xử lý chứ không phải ở mô hình.

*Hiệu chuẩn ngưỡng tự động, chỉ trên train.* **Hiệu chuẩn** (calibration) ở đây là việc chọn giá trị ngưỡng. Mỗi ngưỡng tách hai nhóm: một nhóm phải nằm **dưới** ngưỡng (ví dụ cửa sổ nền với tốc độ ngang đỉnh), một nhóm phải nằm **trên** (ví dụ cửa sổ vuốt). Cách tính:

> ngưỡng = trung điểm giữa (phân vị 90 của nhóm phải ở dưới) và (phân vị 10 của nhóm phải ở trên)

Nói cách khác, bỏ 10% giá trị cao nhất của nhóm dưới và 10% giá trị thấp nhất của nhóm trên, rồi đặt ngưỡng ở giữa hai mốc còn lại. Nếu phân vị 90 của nhóm dưới lại lớn hơn phân vị 10 của nhóm trên, tức hai nhóm chồng lên nhau, chương trình đưa ra cảnh báo. Theo lời thoại, hai trong ba ngưỡng có cảnh báo này.

Ngưỡng chỉ tính trên train. Một kiểm thử chứng minh rằng thêm dữ liệu val hay test, kể cả giá trị cực đoan, cũng không làm ngưỡng thay đổi. Như vậy không có rò rỉ dữ liệu.

| Đặc trưng | Ngưỡng | Hình dung (minh hoạ, với lòng bàn tay cao khoảng 96 pixel) |
|---|---|---|
| Tốc độ ngang đỉnh | 4,026 lòng bàn tay/giây | Khoảng 390 pixel/giây, tức trong một giây tay lướt hơn nửa bề ngang khung hình 640 pixel |
| Dời ngang | 0,1025 lòng bàn tay | Rất nhỏ, khoảng 10 pixel. Ngưỡng này chủ yếu để chắc tay có dời đi thật và lấy được hướng |
| Thay đổi độ mở cái–trỏ | 0,7209 lòng bàn tay | Hai đầu ngón mở ra hoặc chụm lại khoảng 70% chiều dài lòng bàn tay |

*Thứ tự luật.* Luật được xét lần lượt từ trên xuống; khớp luật nào thì dừng ở đó:

```
Cửa sổ mới
  │
  ├─ 1. Thiếu tay (quá ít bước thấy tay)? ─────────────────→ Không cử chỉ
  │
  ├─ 2. Tốc độ ngang đỉnh > 4,026  VÀ  độ lớn dời ngang > 0,1025?
  │        └─ có → VUỐT. Dấu của dời ngang, đối chiếu hằng số hướng → trái hay phải
  │
  ├─ 3. Độ mở cái–trỏ tăng hoặc giảm quá 0,7209?
  │        └─ có → ZOOM. Tăng → zoom in, giảm → zoom out
  │
  └─ 4. Còn lại ───────────────────────────────────────────→ Không cử chỉ
```

*Vì sao xét vuốt trước zoom?* Cú hất của IPN làm bàn tay mở ra, nên khoảng cách cái–trỏ cũng thay đổi theo. Nếu xét zoom trước, nhiều cú vuốt sẽ bị nhận nhầm thành zoom. Ngược lại, zoom gần như không làm cổ tay dời đi, nên xét vuốt trước không làm hỏng zoom.

*Hướng vuốt không viết cứng.* Hướng được lấy theo dấu của dời ngang so với hằng số hướng đã đo ở slide 6, không có chỗ nào trong code ghi cứng "dương là trái".

*Độ tin cậy: không phải xác suất.* Mỗi dự đoán kèm một con số "độ tin cậy" từ 0,5 đến 1. Nó tăng theo mức vượt ngưỡng của điều kiện yếu nhất: vượt ngưỡng càng nhiều thì càng chắc. Đây chỉ là một **heuristic**, tức một cách ước lượng theo kinh nghiệm. Nó không phải **xác suất**: xác suất 0,8 có nghĩa thống kê là "đúng khoảng 8 trên 10 lần", còn con số này không được đảm bảo như vậy. Rừng ngẫu nhiên và LSTM ở các phase sau mới cho xác suất thật.

**Thuật ngữ**

- **Mô hình luật** (rule-based model): mô hình gồm các luật do con người viết.
- **Ngưỡng** (threshold): mức cắt để quyết định "có" hay "không".
- **Hiệu chuẩn** (calibration): chọn giá trị ngưỡng từ dữ liệu.
- **Heuristic**: cách làm theo kinh nghiệm, hợp lý nhưng không có bảo đảm toán học.
- **Xác suất** (probability): con số từ 0 đến 1 có nghĩa thống kê về khả năng đúng.
- **Đường cơ sở** (baseline): một cách làm đơn giản dùng làm mốc so sánh. Mô hình tốt hơn phải vượt nó.

---

## Slide 9 — Kết quả trên tập val

**Ý chính:** Mô hình luật vượt cả hai đường cơ sở, nên đạt tiêu chí của Phase 5. Nhưng nó báo nhầm rất nhiều, nên kết quả vẫn yếu. Điểm tốt là nó hầu như không nhầm hướng.

**Giải thích**

### Bốn khái niệm để đọc bảng

Xét riêng một lớp, ví dụ vuốt trái. Mỗi cửa sổ rơi vào một trong các trường hợp:

- **Dương thật** (true positive, TP): thật sự là vuốt trái, mô hình đoán vuốt trái.
- **Dương giả** (false positive, FP): không phải vuốt trái, nhưng mô hình đoán vuốt trái. Đây là **báo nhầm**.
- **Âm giả** (false negative, FN): thật sự là vuốt trái, nhưng mô hình đoán lớp khác. Đây là **bỏ sót**.

Từ đó có ba chỉ số:

- **Precision** (độ chuẩn xác) = TP / (TP + FP). Trong những lần mô hình nói "vuốt trái", bao nhiêu phần là đúng?
- **Recall** (độ phủ) = TP / (TP + FN). Trong những cú vuốt trái thật, mô hình bắt được bao nhiêu phần?
- **F1** = 2 × Precision × Recall / (Precision + Recall). Đây là một kiểu trung bình của hai chỉ số trên, chỉ cao khi **cả hai** cùng cao. Một chỉ số rất thấp sẽ kéo F1 xuống.

Hình dung bằng chuông báo cháy. Precision cao: chuông kêu là gần như chắc có cháy. Recall cao: có cháy là gần như chắc chuông kêu. Chuông kêu suốt ngày thì recall cao nhưng precision thấp; chuông không bao giờ kêu thì không bao giờ báo nhầm nhưng recall bằng 0.

**Macro-F1** là trung bình cộng F1 của 5 lớp, mỗi lớp nặng như nhau. Nhờ vậy lớp hiếm (từng cử chỉ) quan trọng ngang lớp đông (nền).

*Kiểm tra lại:* (0,714 + 0,056 + 0,043 + 0,164 + 0,176) / 5 = 0,2306, khớp với 0,2305 trên slide (chênh do làm tròn).

### Vì sao không dùng độ chính xác

**Độ chính xác** (accuracy) là tỉ lệ cửa sổ đoán đúng trên tổng số cửa sổ. Tập val có 96,5% cửa sổ nền. Một "mô hình" lúc nào cũng đoán "không cử chỉ" đã đạt độ chính xác 96,5%, mà không nhận ra được cử chỉ nào. Con số này nghe rất cao nhưng vô nghĩa. Vì vậy dự án dùng macro-F1.

### Hai đường cơ sở

Mô hình luật được so với hai cách làm "ngốc" nhất. Có thể tự tính lại cả hai từ tỉ lệ 96,5% nền:

- **Luôn đoán "không cử chỉ"**: lớp nền có precision 0,965 và recall 1, nên F1 ≈ 0,982. Bốn lớp cử chỉ không bao giờ được đoán, F1 = 0. Macro-F1 = 0,982 / 5 ≈ **0,196**.
- **Đoán ngẫu nhiên**: nếu đoán đều một trong 5 lớp, mỗi lớp có recall 20%, còn precision bằng tỉ lệ của lớp đó trong dữ liệu. F1 nền ≈ 0,331, F1 mỗi lớp cử chỉ ≈ 0,017. Macro-F1 ≈ **0,080**, khớp với 0,0796 trên slide.

Mô hình luật đạt **0,2305**, vượt cả hai. Đây là tiêu chí của Phase 5. Nhưng chỉ nhỉnh hơn "luôn đoán nền" một chút, nên lời thoại nói thẳng: kết quả yếu.

### Đọc bảng kết quả

- **Recall** các lớp cử chỉ từ 44% đến 62%: mô hình bắt được khoảng một nửa số cử chỉ.
- **Precision** các lớp vuốt chỉ 2–3%, zoom khoảng 10%: phần lớn các lần mô hình báo "có cử chỉ" là báo nhầm.

*Vì sao precision thấp đến vậy? (ước lượng minh hoạ, giả định báo nhầm chia đều cho hai lớp vuốt)*

- Tập val có khoảng 10 650 cửa sổ nền và khoảng 96 cửa sổ mỗi lớp cử chỉ.
- 44% cửa sổ nền bị báo thành cử chỉ, tức khoảng 4 690 cửa sổ. 80% trong số đó thành vuốt, tức khoảng 3 750, chia cho hai lớp vuốt là khoảng 1 875 mỗi lớp.
- Số vuốt trái bắt đúng: 57,7% × 96 ≈ 56 cửa sổ.
- Precision vuốt trái ≈ 56 / (56 + 1 875) ≈ 0,03, khớp với bảng.

Bài học: lớp nền đông hơn mỗi lớp cử chỉ hơn trăm lần. Chỉ cần một phần nhỏ của nó bị báo nhầm là đã đè bẹp số cửa sổ đoán đúng.

### Ma trận nhầm lẫn

**Ma trận nhầm lẫn** (confusion matrix) là bảng đếm: mỗi hàng là lớp thật, mỗi cột là lớp mô hình đoán. Đường chéo là các ô đoán đúng; mọi ô khác là một kiểu nhầm. Một phần của bảng, để minh hoạ cách đọc:

| Thật \ Đoán | Không cử chỉ | Vuốt trái | Vuốt phải |
|---|---|---|---|
| **Không cử chỉ** | đúng | báo nhầm | báo nhầm |
| **Vuốt trái** | bỏ sót | đúng | nhầm hướng: **2** cửa sổ |
| **Vuốt phải** | bỏ sót | nhầm hướng: **9** cửa sổ | đúng |

Hai điều rút ra từ ma trận:

- **44%** cửa sổ "không cử chỉ" bị báo thành cử chỉ, khoảng 80% trong số đó thành vuốt. Đây là điểm yếu chính. Nghi phạm là động tác **chỉ trỏ** của IPN, vốn di chuyển tay nhanh ngang cú hất. Điều này khớp với việc tốc độ ngang đỉnh chỉ qua cổng sát nút (Phụ lục D).
- Nhầm **hướng** vuốt rất hiếm: 2 cửa sổ trái thành phải, 9 cửa sổ phải thành trái. Hai lớp zoom cũng ít khi nhầm sang nhau. Vậy quy ước hướng và các đặc trưng có dấu hoạt động đúng.

Thứ còn thiếu là khả năng tách cử chỉ khỏi chuyển động nền. Đó là việc của rừng ngẫu nhiên (Phase 6) và máy trạng thái (Phase 9).

Nhắc lại: mọi con số ở đây đo trên **val**. Tập test chưa được dùng.

**Thuật ngữ**

- **TP / FP / FN**: dương thật / dương giả (báo nhầm) / âm giả (bỏ sót).
- **Precision, Recall, F1, Macro-F1**: xem ở trên.
- **Độ chính xác** (accuracy): tỉ lệ đoán đúng trên tổng số. Dễ gây hiểu lầm khi các lớp mất cân bằng.
- **Ma trận nhầm lẫn** (confusion matrix): xem ở trên.

---

## Slide 10 — Hạn chế và kế hoạch tiếp theo

**Ý chính:** Slide nêu thẳng các điểm yếu hiện tại, và lộ trình các phase tiếp theo để khắc phục.

**Giải thích**

### Hạn chế hiện tại

- **Báo nhầm cao: 44% cửa sổ nền.** Tốc độ ngang đỉnh là đặc trưng yếu nhất (slide 9 và Phụ lục D).
- **Train nhỏ: khoảng 415 cửa sổ dương mỗi lớp**, do đổi luật gán nhãn (slide 7) và loại 11 video (Phụ lục B). Cách bù chính là tăng cường dữ liệu tạo mới ở mỗi epoch trong Phase 6 và 7.
- **Nhãn dương phụ thuộc độ lớn chuyển động.** Cửa sổ nào là dương được quyết định dựa trên chính tín hiệu chuyển động (bước thay đổi nhanh nhất, slide 7), nên cử chỉ làm mạnh hay nhẹ sẽ ảnh hưởng tới việc gán nhãn. Điều này cần ghi rõ trong báo cáo.
- **Còn ngoại lai do điểm mốc nhảy giữa cửa sổ.** MediaPipe đôi khi đặt một điểm mốc lệch đột ngột ở một frame. Quy tắc từ chối ở Phụ lục A chỉ xét frame đầu, nên những cú nhảy ở giữa cửa sổ vẫn có thể lọt qua.
- **Mới xét tay phải.**
- **Tập test còn 44 video của 12 người.** Theo cách chia chính thức, test có 13 người, mỗi người 4 video, tức 52 video. Trong 11 video bị loại ở Phụ lục B có 8 video thuộc test, nên còn 44. Một người mất cả 4 video, nên chỉ còn 12 người có dữ liệu.

**Chưa thử trực tiếp trên webcam.** Đây là phần còn lại của Phase 5. Theo lời thoại, nó gồm:

- kiểm tra vuốt sang trái có ra "vuốt trái" không;
- mỗi cử chỉ đúng ít nhất 7 trên 10 lần;
- vẫy tay không bị nhận thành vuốt;
- đếm số lần báo nhầm khi gõ phím, dùng chuột.

Nếu hướng bị ngược, cách sửa đã thiết kế sẵn: đổi hằng số hướng và chạy lại các phép đo, không sửa code.

### Kế hoạch các phase tiếp theo

| Phase | Nội dung | Giải thích |
|---|---|---|
| 5 (còn lại) | Thử trên webcam | Như trên. Đếm báo nhầm trong 2 phút gõ phím. |
| 6 | Rừng ngẫu nhiên; quyết định có cần tự quay dữ liệu | Xem bên dưới. |
| 7 | LSTM một chiều trên chuỗi 42 chiều | Xem bên dưới. |
| 8 | Đánh giá hai mức và 7 bảng khảo sát | Xem bên dưới. |
| 9 | Máy trạng thái | Mỗi cử chỉ phát đúng một lệnh (Phụ lục E). |
| 10 | Demo phát phím tắt thật | Đo FPS, độ trễ, số lần báo nhầm mỗi phút. |
| 11 | *(Tuỳ chọn)* Dữ liệu tự quay | Chỉ làm nếu các phép đo cho thấy cần. |
| 12 | Tái lập toàn bộ từ đầu | Xem bên dưới. |

*Rừng ngẫu nhiên* (random forest, Phase 6). Một **cây quyết định** (decision tree) là một chuỗi câu hỏi có/không, ví dụ "tốc độ ngang đỉnh > 3,8?" rồi "dời ngang > 0,2?", nhưng các câu hỏi và ngưỡng được **học từ dữ liệu** chứ không do người viết. **Rừng ngẫu nhiên** gồm nhiều cây, mỗi cây học trên một phần dữ liệu hơi khác nhau, rồi cả rừng bỏ phiếu. Nó kết hợp được nhiều đặc trưng cùng lúc, nên được kỳ vọng tách nền tốt hơn hẳn mô hình luật, và cho ra xác suất thật. Nếu nó không tốt hơn hẳn mô hình luật, đó là dấu hiệu lỗi nằm trong pipeline chứ không phải ở mô hình.

*LSTM một chiều trên chuỗi 42 chiều* (Phase 7).

- **Mạng nơ-ron** (neural network) là loại mô hình gồm rất nhiều phép tính nhỏ nối với nhau, tự học cách biến đầu vào thành đầu ra.
- **LSTM** (Long Short-Term Memory) là một loại mạng nơ-ron dành cho chuỗi. Nó đọc dữ liệu lần lượt từng bước, và có "trí nhớ" để giữ lại những gì quan trọng ở các bước trước.
- **Một chiều** (unidirectional): chỉ đọc từ quá khứ tới hiện tại. Loại hai chiều đọc cả ngược từ tương lai về, nên không dùng được khi chạy thật.
- **Chuỗi 42 chiều**: mỗi bước đưa vào đủ 42 toạ độ, không qua 15 đặc trưng tự thiết kế. Mô hình tự tìm ra điều gì quan trọng.

*Đánh giá hai mức và 7 bảng khảo sát* (Phase 8).

- **Mức cửa sổ** là cách đánh giá ở slide 9: chấm từng cửa sổ.
- **Mức sự kiện** (event-level): mỗi cử chỉ trọn vẹn tính là một sự kiện. Câu hỏi là hệ thống có nhận ra cú vuốt đó không, có phát thừa lệnh không. Mức này gần với trải nghiệm người dùng hơn.
- **Bảng khảo sát** (ablation / sensitivity study) là các thí nghiệm thay đổi từng lựa chọn một để xem nó ảnh hưởng thế nào, ví dụ thử cửa sổ dài 0,8 / 1,2 / 1,6 giây.

*Demo thật và các phép đo* (Phase 10).

- **FPS**: hệ thống xử lý được bao nhiêu frame mỗi giây.
- **Độ trễ** (latency): thời gian từ lúc người dùng làm xong cử chỉ đến lúc lệnh được phát.
- **Số lần báo nhầm mỗi phút**: thước đo trực tiếp cho điểm yếu lớn nhất. Theo kế hoạch, nếu con số này vượt 0,5 lần mỗi phút thì sẽ bật việc thu dữ liệu tự quay (Phase 11).

*Tái lập* (reproducibility, Phase 12): chạy lại toàn bộ dự án từ đầu, trên dữ liệu gốc, và ra cùng kết quả. Điều này chứng minh kết quả không phụ thuộc may rủi hay thao tác tay nào đó không ghi lại.

**Thuật ngữ**

- **Cây quyết định / rừng ngẫu nhiên** (decision tree / random forest): xem ở trên.
- **Mạng nơ-ron / LSTM** (neural network / LSTM): xem ở trên.
- **Một chiều** (unidirectional): chỉ dùng thông tin quá khứ.
- **Đánh giá mức sự kiện** (event-level evaluation): chấm theo từng cử chỉ trọn vẹn.
- **Bảng khảo sát** (ablation study): thí nghiệm thay từng lựa chọn để đo ảnh hưởng.
- **Độ trễ** (latency): thời gian từ hành động tới phản hồi.
- **Tái lập** (reproducibility): chạy lại ra cùng kết quả.

---

## Slide 11 — Kết luận: Ba điều đã làm được

**Ý chính:** Đến hết Phase 5, dự án có ba thành quả. Các phase tiếp theo sẽ tập trung vào đúng điểm yếu đã đo được.

**Giải thích**

1. **Một pipeline duy nhất.** Nó có ba tính chất:
   - **nhân quả**: chỉ dùng quá khứ;
   - **có kiểm thử**: 90 kiểm thử tự động;
   - **chạy được đầu–cuối**: từ webcam hoặc video tới nhãn dự đoán.

   Cùng một bộ hàm phục vụ cả huấn luyện lẫn demo (slide 4 và Phụ lục E).
2. **Dữ liệu IPN được làm sạch và hiểu bằng số.** Bốn việc chính:
   - sửa lệch frame (Phụ lục B);
   - đo quy ước hướng (slide 6);
   - gán nhãn theo động tác chính (slide 7);
   - chia tập theo người (Phụ lục C).
3. **Một đường cơ sở trung thực.** Mô hình luật vượt hai đường cơ sở, và điểm yếu (báo nhầm) đã được đo và chỉ ra nguyên nhân (slide 9). "Trung thực" nghĩa là không thổi phồng: con số đo trên val, test vẫn khoá, và điểm yếu được nói thẳng.

Hai trong bốn việc ở ý 2 (sửa lệch frame, chia tập theo người) và phần demo ở ý 1 không còn slide riêng trong bản này. Nếu người nghe hỏi, nội dung nằm ở Phụ lục B, C và E.

*Ghi nhớ khi trình bày và khi bị hỏi:*

- Không nói "hệ thống chính xác x%". Dùng macro-F1 và nói rõ là đo trên val.
- Chưa có con số trên tập test. Nếu bị hỏi, giải thích rằng test được khoá tới lần đánh giá cuối cùng.

---

## Phụ lục — Các slide đã bỏ khỏi bản trình chiếu

Năm phụ lục dưới đây giải thích các slide có trong bản trước nhưng đã bỏ khỏi bản 11 trang. Chúng vẫn đáng đọc vì ba lý do:

- Lời thoại trong kịch bản của các slide còn lại vẫn nhắc tới chúng, ví dụ "cổng kiểm tra" ở slide 5 và 8, "sửa lệch frame" ở slide 6, "demo" ở slide 11.
- Slide kết luận liệt kê "sửa lệch frame" và "chia tập theo người" là thành quả.
- Đây là các chủ đề dễ bị hỏi: vì sao chia tập theo người, chuẩn hoá thế nào, độ chính xác 98–99% giả là gì.

| Phụ lục | Nội dung | Liên quan tới slide |
|---|---|---|
| A | Chuẩn hoá cửa sổ, đơn vị "lòng bàn tay" | 4 (bước 6), 5, 6, 8 |
| B | Video và nhãn IPN lệch nhau | 6, 10, 11 |
| C | Chia tập theo người, cân bằng lớp, tăng cường | 3, 4 (bước 5), 9, 11 |
| D | Cổng kiểm tra đặc trưng | 5, 8, 9 |
| E | Demo thời gian thực v0 | 4, 11 |

---

## Phụ lục A — Chuẩn hoá cửa sổ

**Ý chính:** Chuẩn hoá đưa mọi cửa sổ về cùng một hệ quy chiếu, để vị trí tay trong khung hình và cỡ tay không còn ảnh hưởng, nhưng đường đi của tay vẫn giữ nguyên.

**Giải thích**

*Vì sao cần chuẩn hoá.* Hai người cùng làm một cú vuốt trái. Người A ngồi gần, tay to, nằm bên trái khung hình. Người B ngồi xa, tay nhỏ, nằm bên phải. Toạ độ pixel thô của hai người khác nhau hoàn toàn, dù cử chỉ giống nhau. Ta muốn mô hình thấy hai cú vuốt này giống nhau. Chuẩn hoá làm hai việc: dời gốc toạ độ và đổi đơn vị đo.

*Gốc toạ độ: cổ tay ở frame đầu cửa sổ.* Lấy vị trí cổ tay ở bước đầu tiên của cửa sổ làm điểm (0, 0), rồi trừ điểm này khỏi mọi toạ độ trong cửa sổ. Sau đó, con số ở các bước sau cho biết tay đã đi bao xa so với lúc bắt đầu, bất kể tay nằm ở góc nào của khung hình.

*Đơn vị: "lòng bàn tay".* Đo khoảng cách từ cổ tay (điểm 0) đến gốc ngón giữa (điểm 9) ở frame đầu, rồi chia mọi toạ độ cho số này. Sau phép chia, "tay đi được 2 lòng bàn tay" có cùng ý nghĩa dù tay ở gần hay xa camera. Từ đây về sau, mọi khoảng cách trong các slide đều tính bằng đơn vị lòng bàn tay.

*Dùng chung cho mọi frame.* Đây là điểm mấu chốt. Gốc và đơn vị lấy **một lần** ở frame đầu, rồi dùng chung cho cả 18 bước. So sánh hai cách làm:

- **Gốc theo từng frame** (cách thường gặp): mỗi frame trừ vị trí cổ tay của chính frame đó. Kết quả là cổ tay lúc nào cũng nằm ở (0, 0). Cú vuốt chính là chuyển động của cổ tay, nên nó biến mất hoàn toàn, co lại thành một chấm. Chỉ còn lại hình dáng bàn tay.
- **Gốc theo frame đầu** (cách đang dùng): cổ tay xuất phát từ (0, 0) rồi đi dần ra xa. **Quỹ đạo**, tức đường đi theo thời gian, vẫn còn nguyên.

Lời thoại nhắc đến một **kiểm thử** chứng minh cách làm này đúng. Dời tay đi 137 pixel, hoặc phóng to 1,6 lần, thì kết quả sau chuẩn hoá sai khác dưới 10⁻⁵ (0,00001), gần như giống hệt nhau. Trong khi đó, một cú vuốt tổng hợp vẫn cho thấy tay đi hơn hai lòng bàn tay.

*Từ chối cửa sổ xấu.* Trên dữ liệu thật có một vấn đề. Nếu ở frame đầu tay đang nghiêng cạnh (nhìn từ cạnh thì lòng bàn tay trông ngắn lại), hoặc MediaPipe đặt điểm mốc sai, thì đơn vị đo sẽ rất nhỏ. Chia cho một số rất nhỏ thì kết quả phình to: có đặc trưng vọt lên tới 30 lòng bàn tay, một con số vô lý.

Giải pháp là bỏ cửa sổ nếu lòng bàn tay ở frame đầu **ngắn hơn một nửa trung vị** lòng bàn tay của chính cửa sổ đó.

- **Trung vị** (median): sắp xếp các số từ nhỏ đến lớn rồi lấy số ở giữa. Nó ít bị ảnh hưởng bởi vài giá trị bất thường. Ví dụ với dãy 5, 6, 6, 7, 100: trung bình cộng là 24,8, bị kéo lên bởi số 100, còn trung vị là 6.
- Phép so chỉ dùng dữ liệu bên trong cửa sổ, tức quá khứ gần nhất. Khi chạy thật, lúc cần quyết định thì cả cửa sổ đã có đủ, nên quy tắc này vẫn **tôn trọng tính nhân quả**.
- Ngưỡng 0,5 được chọn bằng đo: nó loại khoảng 2% cửa sổ và xoá được các **ngoại lai** lớn.

**Thuật ngữ**

- **Chuẩn hoá** (normalization): biến đổi dữ liệu về một thang đo chung.
- **Gốc toạ độ** (origin): điểm (0, 0) của hệ toạ độ.
- **Quỹ đạo** (trajectory): đường đi của một điểm theo thời gian.
- **Bất biến với vị trí và tỉ lệ** (translation and scale invariance): kết quả không đổi khi dời hoặc phóng to dữ liệu. Đây là tính chất mà chuẩn hoá tạo ra.
- **Trung vị** (median): xem ở trên.
- **Ngoại lai** (outlier): giá trị khác thường, lệch xa phần còn lại, thường do lỗi đo.
- **Kiểm thử tự động** (automated test): đoạn chương trình tự kiểm tra một phần khác của chương trình có chạy đúng không. Dự án có 90 kiểm thử, dùng bàn tay giả dựng bằng hình học nên không cần video hay webcam.

---

## Phụ lục B — Câu chuyện dữ liệu: video và nhãn IPN lệch nhau

**Ý chính:** Đây là ví dụ rõ nhất về một lỗi im lặng. Phần mềm đọc video âm thầm bỏ qua một số frame, làm nhãn trượt dần khỏi cử chỉ thật. Slide kể cách phát hiện lỗi, chẩn đoán nguyên nhân bằng số đo, và sửa.

**Giải thích**

*Nền tảng: nhãn gắn với số thứ tự frame.* File nhãn của IPN ghi kiểu "từ frame số A đến frame số B là hất trái". Nếu chương trình đếm frame lệch đi, nhãn sẽ dán vào sai đoạn video. Mô hình sẽ học "đoạn tay đứng yên này là hất trái" mà không có thông báo lỗi nào.

*Một file video gồm những gì.* Một số khái niệm cần biết để hiểu phần này:

- **AVI** là một loại "vỏ" (container) chứa dữ liệu video. Bên trong, dữ liệu của mỗi frame được lưu thành một khối gọi là **chunk**.
- **Header** là phần đầu file, khai báo thông tin chung như tổng số frame.
- **Chỉ mục** (index) giống mục lục của sách, ghi vị trí từng chunk trong file.
- **Codec** là cách nén ảnh để file nhỏ lại. **XVID** là một codec.
- **Bộ giải mã** (decoder) biến dữ liệu nén thành ảnh. **FFmpeg** là bộ giải mã rất phổ biến; thư viện OpenCV dùng nó để đọc video.

*Triệu chứng.* Ở nhiều video, số frame đọc được khác với số frame trong file nhãn.

*Chẩn đoán bằng ba cách đếm độc lập.* Với cả 200 video, dự án đếm số frame theo ba cách:

1. số frame khai báo trong header;
2. số chunk trong chỉ mục file AVI;
3. số frame giải mã được thật (đọc từng frame và đếm).

Kết quả cho thấy một đẳng thức đúng ở **mọi** video:

> số frame giải mã được + số chunk 6 byte = tổng số chunk

*Giải nghĩa.* Khi một ảnh không thay đổi so với frame trước, XVID không lưu lại cả ảnh. Nó ghi một chunk rất nhỏ, chỉ 6 byte, nghĩa là "giữ nguyên ảnh trước", để tiết kiệm dung lượng. Loại frame này gọi là **frame "not coded"**. FFmpeg gặp chunk này thì bỏ qua, không trả ra ảnh nào. Mỗi lần như vậy, mọi frame phía sau bị đánh số lùi đi một.

*Mức độ.* 101 trên 200 video bị ảnh hưởng, tổng cộng 677 frame bị bỏ, nhiều nhất 56 frame trong một video. Ở 30 FPS, 56 frame là gần 2 giây, dài bằng cả một cử chỉ.

*Cách sửa.* Thời điểm của mỗi frame được lấy theo **vị trí của nó trong file** (nó là chunk thứ mấy), không theo "đây là lần đọc thứ mấy".

*Vấn đề thứ hai: file nhãn IPN đếm frame không thống nhất.* Có video được gán nhãn theo cách đếm tính cả frame bị bỏ, có video thì không. Vì vậy phải chọn cách đếm cho từng video:

| Số video | Nhãn khớp với | Giải thích |
|---|---|---|
| 128 | Hai cách đếm như nhau | Các video này không có frame bị bỏ, nên cách đếm nào cũng ra một số |
| 57 | Số chunk | Nhãn đếm cả frame bị bỏ |
| 4 | Số frame giải mã | Nhãn không đếm frame bị bỏ |
| 11 | Không khớp cách nào | **Loại** khỏi dữ liệu |

*Kiểm vị trí bằng điểm mốc.* Số đếm khớp chưa chắc vị trí đã đúng, nên dự án kiểm thêm vị trí. Ý tưởng: trong đoạn không cử chỉ, tay người diễn thường để ngoài khung hình; khi bắt đầu cử chỉ, tay đưa vào. Vì vậy tín hiệu "có tay / không tay" thường đổi trạng thái gần ranh giới nhãn. Cách kiểm như sau:

- Thử dịch nhãn đi từ −70 đến +70 frame, tìm độ dịch khớp nhất với tín hiệu "có tay".
- Với cách đếm đúng, độ dịch tốt nhất nằm trong khoảng −2 đến +6 frame. Đây là **sai số tự nhiên** của chính phép đo, vì tay không bao giờ vào khung đúng khung hình bắt đầu nhãn.
- Với cách đếm sai, độ dịch trôi tới 40–60 frame, lệch rõ ràng.

Lời thoại còn nhắc hai hướng khác đã thử và bỏ: dùng tín hiệu tốc độ chuyển động, và bỏ các frame lặp. Cả hai đều cho kết quả sai ngay trên những video đã biết chắc là khớp.

Bài học ở đây là nguyên tắc **"đo, không đoán"**: không giả định dữ liệu đúng, mà kiểm bằng nhiều phép đo độc lập.

**Thuật ngữ**

- **File nhãn** (annotation file): file ghi đoạn nào trong video là cử chỉ gì.
- **Container / AVI**: định dạng "vỏ" chứa dữ liệu video.
- **Chunk**: một khối dữ liệu trong file, ở đây mỗi chunk ứng với một frame.
- **Header / chỉ mục** (header / index): phần khai báo đầu file / mục lục vị trí các chunk.
- **Codec / XVID**: cách nén video / một codec cụ thể.
- **Bộ giải mã / FFmpeg** (decoder): phần mềm giải nén video / một bộ giải mã phổ biến.
- **Frame "not coded"**: frame chỉ có nghĩa "giữ nguyên ảnh trước", bị FFmpeg bỏ qua.
- **Sai số đo** (measurement noise): độ lệch tự nhiên của một phép đo, không phải do lỗi.

---

## Phụ lục C — Chia tập theo người, cân bằng lớp, tăng cường

**Ý chính:** Phần này trình bày ba kỹ thuật dữ liệu:

- chia dữ liệu theo người, để con số đánh giá trung thực;
- giảm bớt lớp nền ở tập huấn luyện, để mô hình học được các cử chỉ hiếm;
- tạo thêm biến thể của dữ liệu, để mô hình chịu được những khác biệt nhỏ.

**Giải thích**

### Phần 1: ba tập dữ liệu

Dữ liệu được chia thành ba phần, mỗi phần một vai trò:

| Tập | Vai trò | Ví dụ đời thường |
|---|---|---|
| **Train** (huấn luyện) | Mô hình học từ đây | Bài tập về nhà |
| **Val** (validation, kiểm định) | Đánh giá trong lúc phát triển, so sánh các phương án | Đề thi thử |
| **Test** (kiểm tra) | Khoá lại, chỉ dùng **một lần** ở cuối dự án | Đề thi thật |

Nếu bạn xem đề thi thật nhiều lần rồi chỉnh cách học cho hợp với nó, điểm thi sẽ không còn phản ánh năng lực thật. Vì vậy, mọi quyết định của dự án chỉ dựa trên train, các con số báo cáo lấy từ val, còn test chưa được dùng.

*Chia theo người.* Train 30 người, val 7 người, test 13 người. Không ai có mặt ở hai tập.

Lý do là **rò rỉ dữ liệu** (data leakage). Hai cửa sổ liền nhau dùng chung 15 trên 18 bước, nên gần như giống hệt nhau. Nếu chia ngẫu nhiên từng cửa sổ, cùng một cú vuốt sẽ có cửa sổ nằm ở train và cửa sổ gần như y hệt nằm ở test. Mô hình chỉ cần "nhớ bài" là đúng, và đạt độ chính xác 98–99%, một con số hoàn toàn giả. Chia theo người còn kiểm tra đúng tình huống thật: hệ thống phải làm việc với một người nó chưa từng thấy.

Tập test giữ đúng cách chia chính thức của IPN, để so sánh được với các nghiên cứu khác. Tập val lấy 20% số người của phần train chính thức (7 trên 37 người).

*Kích thước dữ liệu.* Tổng cộng 37 504 cửa sổ. Mỗi cửa sổ là 18 bước × 21 điểm × 2 toạ độ.

| Tập | Số cửa sổ | Tỉ lệ "không cử chỉ" | Số cửa sổ mỗi lớp cử chỉ |
|---|---|---|---|
| Train (sau lấy mẫu con) | 3 326 | 50% | khoảng 415 |
| Val (phân bố tự nhiên) | 11 038 | 96,5% | khoảng 96 |
| Test (phân bố tự nhiên) | 23 140 | 97,2% | khoảng 160 |

### Phần 2: mất cân bằng lớp

Trong dữ liệu tự nhiên, lớp nền chiếm khoảng 97%. Đây gọi là **mất cân bằng lớp** (class imbalance). Nếu huấn luyện trên dữ liệu như vậy, mô hình dễ học được một mẹo lười: cứ đoán "không cử chỉ" là đúng 97% số lần.

*Lấy mẫu con lớp nền, chỉ ở train.* **Lấy mẫu con** (undersampling) là chỉ giữ lại một phần lớp đông. Ở train, số cửa sổ nền giảm từ 49 652 xuống 1 663, để nền chỉ còn chiếm 50%.

*Kiểu "rót nước".* 1 663 cửa sổ không được chọn ngẫu nhiên, mà chia đều cho 10 nhãn gốc đã gom vào lớp nền (hất lên, chỉ trỏ, không cử chỉ gốc...). Mỗi nhãn được phần chia khoảng 166 cửa sổ. Nhãn nào có ít hơn phần chia thì lấy hết, phần còn thừa dồn sang các nhãn còn lại. Giống như rót một bình nước vào 10 cốc to nhỏ khác nhau: cốc nhỏ đầy trước, nước thừa chảy sang cốc lớn.

Nhờ vậy, các mẫu âm khó đều có mặt trong train, không bị nhãn "không cử chỉ" gốc (rất đông) chiếm hết chỗ.

Val và test **giữ phân bố tự nhiên**, vì con số đánh giá phải phản ánh đúng tình huống thật, nơi lớp nền chiếm áp đảo. Train cũng không cân bằng hẳn 1:1 giữa nền và từng lớp cử chỉ, vì như vậy mô hình sẽ quá dễ dãi đoán "có cử chỉ" và báo nhầm nhiều hơn khi chạy thật.

### Phần 3: tăng cường dữ liệu

**Tăng cường dữ liệu** (data augmentation) là tạo thêm biến thể từ dữ liệu có sẵn bằng những biến đổi nhỏ, để mô hình thấy nhiều kiểu hơn và không quá phụ thuộc vào chi tiết vụn vặt. Hai quy tắc:

- **Chỉ trên train.** Val và test phải là dữ liệu thật, nguyên vẹn. Chương trình từ chối chạy tăng cường trên mọi tập khác train.
- **Tạo mới mỗi epoch.** Một **epoch** là một lượt mô hình học qua toàn bộ tập train. Mỗi epoch, các biến thể được tạo ngẫu nhiên lại, nên mô hình không gặp cùng một biến thể hai lần.

Với mỗi phép biến đổi, phải trả lời câu hỏi: **"nó có làm đổi lớp không?"**

| Phép biến đổi | Mô phỏng điều gì | Nhãn |
|---|---|---|
| Lật ngang (như soi gương) | Người làm bằng tay đối diện | **Đổi** vuốt trái ↔ vuốt phải; zoom giữ nguyên |
| Xoay ±10° | Tay hơi nghiêng | Giữ nguyên |
| Co giãn đổi dần | Tay tiến lại gần hoặc lùi xa camera trong lúc làm | Giữ nguyên |
| Co giãn thời gian 0,8–1,2× | Làm nhanh hơn hoặc chậm hơn | Giữ nguyên |
| Nhiễu Gauss | Tay rung nhẹ, MediaPipe đặt điểm hơi lệch | Giữ nguyên |
| Xoá 1–3 bước | Mất tay trong khoảnh khắc | Giữ nguyên |

*Một phát hiện.* Ban đầu dự án định dùng phép **co giãn đều** (phóng to cả cửa sổ). Kiểm thử cho thấy phép này vô tác dụng: bước chuẩn hoá chia cho cỡ lòng bàn tay, nên phóng to bao nhiêu cũng bị triệt tiêu (Phụ lục A). Vì vậy nó được thay bằng co giãn **đổi dần** dọc theo cửa sổ.

*Mức nhiễu được đo, không đoán.*

- **Nhiễu Gauss** (Gaussian noise) là các sai lệch ngẫu nhiên nhỏ, phân bố theo hình chuông: sai lệch nhỏ thì hay gặp, sai lệch lớn thì hiếm.
- **Độ lệch chuẩn** (standard deviation) đo mức phân tán của các sai lệch đó. Dự án dùng 0,0159 lòng bàn tay. *Minh hoạ:* nếu lòng bàn tay cao khoảng 96 pixel (1/5 chiều cao khung hình), mức nhiễu này khoảng 1,5 pixel.
- Con số này đo trên **tay nghỉ**. Lần đo đầu cho 0,054, lớn gấp ba. Khi kiểm tra, các cửa sổ "cổ tay đứng yên" dùng để đo phần lớn là lúc người diễn bấm ngón hay xòe tay, tức cử động có chủ ý, không phải độ rung. Giới hạn vào tay nghỉ thì được 0,0159.
- Một cách đo độc lập khác, dùng **sai phân bậc hai**, cho 0,0162, rất khớp. Sai phân bậc hai là lấy hiệu của hiệu giữa các bước liên tiếp. Chuyển động mượt cho kết quả gần 0, nên phần còn lại chủ yếu là rung. Hai cách đo độc lập cho cùng một kết quả thì con số đáng tin.

**Thuật ngữ**

- **Train / val / test**: xem bảng ở Phần 1.
- **Rò rỉ dữ liệu** (data leakage): thông tin từ tập đánh giá lọt vào lúc huấn luyện, làm kết quả đẹp giả.
- **Mất cân bằng lớp** (class imbalance): một lớp đông hơn hẳn các lớp khác.
- **Lấy mẫu con** (undersampling): chỉ giữ lại một phần của lớp đông.
- **Phân bố tự nhiên**: tỉ lệ các lớp đúng như ngoài đời, không chỉnh sửa.
- **Tăng cường dữ liệu** (data augmentation): xem Phần 3.
- **Epoch**: một lượt học qua toàn bộ tập train.
- **Nhiễu Gauss / độ lệch chuẩn**: xem Phần 3.
- **Sai phân** (difference): hiệu giữa hai giá trị liên tiếp.

---

## Phụ lục D — Cổng kiểm tra đặc trưng

**Ý chính:** Trước khi xây mô hình, dự án kiểm tra bằng hình và bằng số rằng các đặc trưng thật sự tách được các lớp. Cả ba điều kiện đều đạt, nhưng tốc độ ngang đỉnh chỉ đạt sát nút.

**Giải thích**

*Cổng kiểm tra là gì.* Đây là một điểm kiểm tra bắt buộc: phải qua thì mới được đi tiếp. Lý do được tóm trong một câu: **"Không mô hình nào cứu được đặc trưng không tách lớp."** Nếu các con số của vuốt trái và của "không cử chỉ" trông giống hệt nhau, thì mô hình thông minh cỡ nào cũng không phân biệt được.

*Boxplot (biểu đồ hộp).* Cổng kiểm tra dựa trên ba boxplot, vẽ trên tập train, cho ba đặc trưng: thay đổi độ mở cái–trỏ, dời ngang cổ tay, tốc độ ngang đỉnh. Hình gốc nằm ở `results/phase4/boxplots/run_03/`. Mỗi boxplot tóm tắt cả một tập giá trị của một đặc trưng, cho một lớp:

```
    o       |--------[==========|==========]--------|       o
    1       2        3          4          5        6       7
```

- **1, 7 — ngoại lai**: các giá trị nằm quá xa phần còn lại.
- **2, 6 — râu**: kéo tới các giá trị xa nhất chưa bị coi là ngoại lai.
- **3 — phân vị 25**: 25% giá trị nhỏ hơn mốc này.
- **4 — trung vị** (phân vị 50): một nửa nhỏ hơn, một nửa lớn hơn.
- **5 — phân vị 75**: 75% giá trị nhỏ hơn mốc này.
- **Hộp** (từ 3 đến 5) chứa 50% giá trị ở giữa.

Đặt hộp của các lớp cạnh nhau: hai hộp càng xa nhau, đặc trưng càng tách lớp tốt; hai hộp chồng lên nhau là dấu hiệu đáng lo.

*Đọc bảng điều kiện.*

| Điều kiện | Đặc trưng | Số đo | Nghĩa là |
|---|---|---|---|
| Zoom in nằm hẳn bên dương | Thay đổi độ mở cái–trỏ | Phân vị 25 = +0,70 | Ít nhất 75% cửa sổ zoom in có hai ngón mở thêm từ 0,70 lòng bàn tay trở lên. Cả hộp nằm bên dương. **Đạt.** |
| Zoom out nằm hẳn bên âm | Thay đổi độ mở cái–trỏ | Phân vị 75 = −0,58 | Ít nhất 75% cửa sổ zoom out có hai ngón chụm lại từ 0,58 lòng bàn tay trở lên. **Đạt.** |
| Hai lớp vuốt nằm ở hai phía của 0 | Dời ngang cổ tay | Hộp [+0,13; +1,35] và [−1,12; −0,31] | Hộp hất trái nằm trọn bên dương, hộp hất phải nằm trọn bên âm. **Đạt.** |
| Hai lớp vuốt cao hơn hẳn "không cử chỉ" | Tốc độ ngang đỉnh | Phân vị 25 của hai lớp vuốt là 3,59 và 3,70; phân vị 75 của nền là 3,30 | Đáy hộp vuốt vẫn cao hơn đỉnh hộp nền, nên hai hộp không chồng nhau, nhưng khoảng cách rất nhỏ. **Đạt, sát nút.** |

Hai điểm đáng chú ý:

- Điều kiện thứ ba chỉ đòi hai lớp vuốt nằm ở **hai phía** của 0. Nó không giả định trước lớp nào phải nằm bên dương; việc đó để cho hằng số hướng (slide 6).
- Điều kiện thứ tư đạt sát nút có nghĩa là khoảng một phần tư số cửa sổ nền có tốc độ đỉnh trên 3,30 lòng bàn tay/giây, rất gần với nhiều cú vuốt thật. Đây là điểm yếu nhất của bộ đặc trưng, và slide 9 sẽ cho thấy hệ quả của nó: báo nhầm nhiều.

*Câu chuyện trong lời thoại.* Cổng ban đầu dựa trên độ xòe và độ thẳng quỹ đạo, và nó **không đạt**. Dự án không hạ điều kiện cho dễ qua. Thay vào đó, nó chẩn đoán xem lỗi nằm ở nhãn hay ở đặc trưng, thử từng phương án trên train, và chỉ áp dụng khi số đo cho thấy cổng đạt. Hai thay đổi ra đời từ đây là luật gán nhãn mới (slide 7) và đặc trưng độ mở cái–trỏ (slide 5).

Ba đặc trưng của cổng này cũng chính là ba đặc trưng mà mô hình luật ở slide 8 dùng.

**Thuật ngữ**

- **Cổng kiểm tra** (gate): điều kiện bắt buộc phải đạt trước khi đi tiếp.
- **Boxplot** (biểu đồ hộp): xem ở trên.
- **Phân vị** (percentile): phân vị p là mốc mà p% giá trị nhỏ hơn nó.
- **Tách lớp** (class separability): mức độ các lớp có giá trị khác nhau rõ ràng trên một đặc trưng.

---

## Phụ lục E — Demo thời gian thực v0

**Ý chính:** Hệ thống đã chạy được từ webcam tới nhãn, dùng đúng cùng pipeline với lúc huấn luyện. Ngoài ra có một chế độ luyện tập giúp người dùng làm cử chỉ giống người diễn IPN.

**Giải thích**

"v0" là phiên bản đầu tiên. Nó hiển thị nhãn dự đoán trên màn hình, chưa phát phím tắt thật.

*Luồng xử lý 4 bước.*

1. **Webcam → điểm mốc.** Mỗi frame webcam đi qua MediaPipe để lấy 21 điểm mốc.
2. **Bộ đệm giữ 1,7 giây gần nhất, tính theo thời gian.** **Bộ đệm** (buffer) là vùng nhớ giữ dữ liệu mới nhất; dữ liệu cũ hơn 1,7 giây tự bị bỏ. Bộ đệm dài hơn cửa sổ 1,2 giây một chút để luôn dư dữ liệu khi cắt cửa sổ. Nó tính theo giây chứ không theo số frame, vì FPS webcam dao động.
3. **Mỗi 0,2 giây, lấy 18 bước cuối qua cùng pipeline với IPN.** Đây chính là cửa sổ trượt của slide 4, nhưng làm ngay lúc chạy: cứ 0,2 giây, hệ thống cắt ra cửa sổ 1,2 giây mới nhất.
4. **Chuẩn hoá → đặc trưng → luật**, như Phụ lục A, slide 5 và slide 8.

*Mọi xử lý nằm trong thư viện dùng chung.* Các hàm nội suy, chuẩn hoá, tính đặc trưng chỉ được viết một lần, và cả phần huấn luyện lẫn demo đều gọi lại chúng. Chương trình demo không định nghĩa lại hàm xử lý nào; nó chỉ nối camera, màn hình và file log. Đó là cách bảo đảm nguyên tắc "một pipeline" đã nói ở slide 4.

*Màn hình hiển thị.*

- Ảnh lật như gương cho tự nhiên, có vẽ khung xương bàn tay.
- Nhãn chữ lớn kèm độ tin cậy, hoặc dấu "–" khi không có cửa sổ hợp lệ, ví dụ thiếu tay hoặc cửa sổ bị từ chối ở bước chuẩn hoá.
- Tỉ lệ có tay và FPS.

*Chế độ luyện tập.* Mô hình học cử chỉ theo cách của người diễn IPN, nên người dùng cần biết mình làm có giống không. Màn hình hiện ba đặc trưng chính của cửa sổ vừa làm:

- tô **xanh** nếu giá trị nằm trong khoảng 25–75% của lớp đó trên IPN, tức nằm trong "hộp" của boxplot ở Phụ lục D;
- tô **đỏ** nếu lệch ra ngoài.

Người dùng chọn cử chỉ đang luyện bằng phím 1–4. Nhờ vậy, điều kiện "làm cử chỉ theo cách IPN" ở slide 3 được kiểm bằng số, không bằng cảm giác.

*Log.* **Log** là file ghi lại hoạt động của chương trình, mỗi dự đoán một dòng. Khi thoát, chương trình đếm số **"đợt báo"**: các dự đoán cử chỉ liền nhau được gom thành một đợt, gần với số lần hệ thống sẽ phát lệnh nếu có máy trạng thái.

*Đã kiểm tra thế nào.* Demo đã chạy trên video IPN của tập val, dùng video thay cho webcam: đúng nhịp 0,2 giây, log ghi đủ các cột. Phần thử trực tiếp trên webcam là bước tiếp theo.

*Hiện tượng nhãn nhấp nháy.* Khi xem demo, mỗi lần làm cử chỉ, nhãn sẽ hiện liên tục hơn một giây, có thể nhảy qua lại. Đây là hành vi đúng ở mốc này: cứ 0,2 giây có một cửa sổ mới, và nhiều cửa sổ liên tiếp cùng chứa cử chỉ. Việc gom chúng thành đúng một lệnh là của **máy trạng thái** (Phase 9).

*Máy trạng thái là gì.* Đó là một cơ chế có vài trạng thái và luật chuyển giữa chúng, giống đèn giao thông chuyển xanh, vàng, đỏ. Một ví dụ minh hoạ (thiết kế cụ thể là việc của Phase 9):

```
[Chờ] ──thấy vuốt trái đủ chắc──→ [Phát lệnh "slide trước"] ──→ [Nghỉ: bỏ qua dự đoán, chờ tay về] ──→ [Chờ]
```

**Thuật ngữ**

- **Demo v0**: phiên bản chạy thử đầu tiên.
- **Bộ đệm** (buffer): vùng nhớ giữ dữ liệu gần nhất.
- **Thư viện dùng chung** (shared library): bộ hàm viết một lần, nhiều chương trình cùng gọi.
- **Log**: file ghi lại hoạt động của chương trình.
- **Khoảng 25–75%** (interquartile range, khoảng tứ phân vị): khoảng giữa phân vị 25 và phân vị 75, tức "hộp" của boxplot.
- **Máy trạng thái** (state machine): xem ở trên.

---

## Bảng thuật ngữ

Cột cuối cho biết thuật ngữ được giải thích ở đâu: số là slide, chữ cái A–E là phụ lục, 0 là Phần 0.

| Thuật ngữ | Tiếng Anh | Nghĩa ngắn | Slide / Phụ lục |
|---|---|---|---|
| Báo nhầm | False positive, false alarm | Không có cử chỉ mà hệ thống tưởng có | 2, 9 |
| Biên | Margin | Khoảng cách tối thiểu từ khoảnh khắc chính tới mép cửa sổ | 7 |
| Biên độ | Range, amplitude | Chênh lệch giữa giá trị lớn nhất và nhỏ nhất | 5 |
| Bộ dữ liệu | Dataset | Tập ví dụ có nhãn | 3 |
| Bộ đệm | Buffer | Vùng nhớ giữ dữ liệu gần nhất | E |
| Bộ giải mã | Decoder | Phần mềm biến video nén thành ảnh (ví dụ FFmpeg) | B |
| Bỏ sót | False negative | Có cử chỉ mà hệ thống không nhận ra | 2, 9 |
| Boxplot | Box plot | Biểu đồ hộp tóm tắt phân bố một đặc trưng | D |
| Bước | Time step | Một điểm trên lưới thời gian đều, cách nhau 1/15 giây; khác frame ở chỗ luôn cách đều | 4 |
| Cây quyết định | Decision tree | Chuỗi câu hỏi có/không học từ dữ liệu | 10 |
| Chân lý tham chiếu | Ground truth | Đáp án được coi là đúng | 7 |
| Chuẩn hoá | Normalization | Đưa dữ liệu về thang đo chung | A |
| Chunk | Chunk | Một khối dữ liệu trong file video | B |
| Codec | Codec | Cách nén video (ví dụ XVID) | B |
| Cổng kiểm tra | Gate | Điều kiện bắt buộc đạt trước khi đi tiếp | D |
| CPU / GPU | CPU / GPU | Bộ xử lý chính / chip đồ hoạ tính song song | 2 |
| Cửa sổ (trượt) | Sliding window | Đoạn 1,2 giây, dịch mỗi 0,2 giây | 4 |
| Cửa sổ dương / âm | Positive / negative window | Cửa sổ mang nhãn cử chỉ / không cử chỉ | 7 |
| Đặc trưng | Feature | Con số tóm tắt một khía cạnh của dữ liệu | 5 |
| Đặc trưng có dấu | Signed feature | Đặc trưng có thể âm/dương, dấu chỉ hướng | 5 |
| Điểm mốc | Landmark | Vị trí một khớp tay do MediaPipe xác định | 1 |
| Đoạn | Segment | Một lần làm cử chỉ trong file nhãn: lớp, frame bắt đầu, frame kết thúc | 6 |
| Độ chính xác | Accuracy | Tỉ lệ đoán đúng trên tổng số; dễ hiểu lầm khi lớp mất cân bằng | 9 |
| Độ lệch chuẩn | Standard deviation | Mức phân tán của các giá trị | C |
| Độ phân giải | Resolution | Số pixel ngang × dọc | 3 |
| Độ tin cậy | Confidence | Mức chắc chắn kèm dự đoán; ở mô hình luật chỉ là heuristic | 8 |
| Độ trễ | Latency | Thời gian từ hành động tới phản hồi | 10 |
| Đường cơ sở | Baseline | Cách làm đơn giản dùng làm mốc so sánh | 8, 9 |
| Epoch | Epoch | Một lượt học qua toàn bộ tập train | C |
| F1 / Macro-F1 | F1 / Macro-F1 | Kết hợp precision và recall / trung bình F1 các lớp | 9 |
| Frame | Frame | Một ảnh trong video | 0 |
| FPS | Frames per second | Số frame mỗi giây | 0, 3 |
| Heuristic | Heuristic | Cách làm theo kinh nghiệm, không có bảo đảm toán học | 8 |
| Hiệu chuẩn | Calibration | Chọn giá trị ngưỡng từ dữ liệu | 8 |
| Hz | Hertz | Số lần mỗi giây | 4 |
| Kiểm thử tự động | Automated test | Chương trình tự kiểm tra chương trình khác | A |
| Làm mượt | Smoothing | Lấy trung bình với giá trị lân cận để bớt nhiễu | 7 |
| Lấy mẫu con | Undersampling | Chỉ giữ một phần lớp đông | C |
| Lòng bàn tay (đơn vị) | Palm length | Khoảng cách cổ tay → gốc ngón giữa ở frame đầu cửa sổ; đơn vị đo mọi khoảng cách sau chuẩn hoá | 0, A |
| Lỗi im lặng | Silent error | Lỗi không báo gì nhưng làm kết quả sai | 0, B |
| Lớp / lớp nền | Class / background class | Loại đáp án / lớp "không cử chỉ" | 0, 2 |
| LSTM | Long Short-Term Memory | Mạng nơ-ron đọc chuỗi, có "trí nhớ" | 10 |
| Ma trận nhầm lẫn | Confusion matrix | Bảng đếm lớp thật × lớp đoán | 9 |
| Máy trạng thái | State machine | Cơ chế chuyển giữa các trạng thái theo luật | 10, E |
| Mất cân bằng lớp | Class imbalance | Một lớp đông hơn hẳn các lớp khác | C |
| Mẫu âm khó | Hard negative | Ví dụ "không cử chỉ" trông giống cử chỉ | 3 |
| Mô hình | Model | Chương trình nhận đầu vào, đưa ra dự đoán | 0 |
| Mô hình luật | Rule-based model | Mô hình gồm luật do người viết | 8 |
| Ngoại lai | Outlier | Giá trị lệch xa bất thường | A |
| Ngưỡng | Threshold | Mức cắt để quyết định có/không | 8 |
| Nhãn | Label | Đáp án đúng gắn với ví dụ | 0 |
| Nhân quả | Causality | Chỉ dùng thông tin quá khứ | 0, 2 |
| Nhiễu Gauss | Gaussian noise | Sai lệch ngẫu nhiên nhỏ, phân bố hình chuông | C |
| Nội suy | Interpolation | Ước lượng giá trị giữa hai giá trị đã biết | 4 |
| Phân vị | Percentile | Mốc mà p% giá trị nhỏ hơn nó | D |
| Pipeline | Pipeline | Dây chuyền xử lý nhiều bước theo thứ tự cố định | 4 |
| Pixel | Pixel | Một ô điểm ảnh | 0 |
| Precision | Precision | Trong các lần báo, bao nhiêu phần đúng | 9 |
| Quỹ đạo | Trajectory | Đường đi theo thời gian | A |
| Recall | Recall | Trong các trường hợp thật, bắt được bao nhiêu phần | 9 |
| Rò rỉ dữ liệu | Data leakage | Thông tin tập đánh giá lọt vào lúc huấn luyện | C |
| Rừng ngẫu nhiên | Random forest | Nhiều cây quyết định cùng bỏ phiếu | 10 |
| Tái lập | Reproducibility | Chạy lại ra cùng kết quả | 10 |
| Tăng cường dữ liệu | Data augmentation | Tạo biến thể từ dữ liệu có sẵn | C |
| Theo dõi | Tracking | Bám theo đối tượng qua các frame | 4 |
| Thiết kế đặc trưng | Feature engineering | Con người tự nghĩ ra các đặc trưng có ý nghĩa, rút 756 số xuống 15 số | 5 |
| Thời gian thực | Real-time | Phản hồi ngay khi người dùng đang làm | 1 |
| Tiền xử lý | Preprocessing | Các bước chuẩn bị dữ liệu trước mô hình | 4 |
| Train / Val / Test | Train / Validation / Test | Tập học / tập đánh giá trong lúc phát triển / tập kiểm tra cuối | C |
| Trung vị | Median | Giá trị ở giữa khi sắp xếp | 6, A |
