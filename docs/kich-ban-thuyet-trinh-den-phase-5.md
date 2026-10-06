# Kịch bản thuyết trình — Nhận dạng cử chỉ bàn tay thời gian thực (đến Phase 5)

**Dựa trên:** `docs/tong-ket-den-phase-5.md` (cập nhật 2026-10-05) và `docs/SPEC.md`.
**Thời lượng:** khoảng 25 phút trình bày, chưa tính hỏi đáp. Bản rút gọn khoảng 12 phút ở Phụ lục C.
**Số slide:** 18.

**Cách dùng kịch bản**

- Mỗi slide có hai phần chính:
  - *Trên slide*: chữ và hình đưa lên màn chiếu. Càng ít chữ càng tốt.
  - *Lời thoại*: phần nói. Không đọc lại slide.
- Kịch bản xưng "tôi"; đổi thành "em" hoặc "nhóm em" tuỳ bối cảnh.
- Ba nguyên tắc khi nói:
  1. Mỗi kỹ thuật kể theo mạch **vấn đề → cách làm → bằng chứng bằng số**.
  2. Nói thẳng hạn chế: mô hình luật còn yếu, phần thử trên webcam chưa làm.
  3. Mọi con số là trên tập train hoặc val. Tập test **chưa dùng**, và không được nói như đã dùng.

---

## Slide 1 — Tiêu đề · ⏱ 0:30

**Trên slide**

- Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính
- Báo cáo tiến độ: các giải pháp và kỹ thuật đã thực hiện (Phase 0 → Phase 5)
- Người trình bày · lớp/môn · ngày

**Lời thoại**

> Xin chào thầy cô và các bạn. Hôm nay tôi trình bày tiến độ đề tài nhận dạng cử chỉ bàn
> tay thời gian thực để điều khiển máy tính.
>
> Trọng tâm hôm nay không phải một con số độ chính xác cao. Tôi sẽ trình bày các giải pháp
> kỹ thuật đã xây dựng để có một hệ thống chạy được từ đầu đến cuối, và những vấn đề của dữ
> liệu thật mà tôi đã gặp, chẩn đoán và xử lý trên đường đi.

---

## Slide 2 — Bài toán · ⏱ 1:00

**Trên slide**

- Đầu vào: webcam laptop thông thường, chạy trên CPU, không GPU
- Đầu ra: bốn cử chỉ thành bốn lệnh

| Cử chỉ | Lệnh dự kiến |
|---|---|
| Vuốt trái | Slide trước |
| Vuốt phải | Slide sau |
| Zoom in | Phóng to |
| Zoom out | Thu nhỏ |

- Thêm một lớp nền "không cử chỉ", là lớp chiếm phần lớn thời gian khi dùng thật
- Ràng buộc thời gian thực: tại mỗi thời điểm chỉ được dùng quá khứ

**Lời thoại**

> Bài toán là từ hình ảnh webcam, nhận ra bốn cử chỉ (vuốt trái, vuốt phải, zoom in,
> zoom out) để phát phím tắt, ví dụ chuyển slide hay phóng to.
>
> Có ba điểm làm bài toán khó hơn vẻ ngoài.
>
> Thứ nhất, phần lớn thời gian người dùng *không* làm cử chỉ nào: họ gõ phím, cầm chuột,
> khua tay khi nói. Vì vậy lớp "không cử chỉ" là lớp quan trọng nhất, và báo nhầm là lỗi
> nguy hiểm nhất. Một lần chuyển slide sai tệ hơn một lần bỏ sót.
>
> Thứ hai, hệ thống chạy thời gian thực. Tại mỗi thời điểm nó chỉ được nhìn vào quá khứ,
> không được "chờ xem" chuyện gì xảy ra tiếp theo.
>
> Thứ ba, hệ thống phải chạy trên máy tính thông thường, không có GPU.

---

## Slide 3 — Hướng tiếp cận và lộ trình · ⏱ 1:30

**Trên slide**

- Sơ đồ (cần tự vẽ):
  Webcam → 21 điểm mốc bàn tay → cửa sổ 1,2 giây → chuẩn hoá → 15 đặc trưng hoặc chuỗi toạ độ
  → mô hình → máy trạng thái → phím tắt
- Ba mô hình, từ đơn giản tới phức tạp: luật ngưỡng → rừng ngẫu nhiên → LSTM một chiều
- Lộ trình 13 phase. Thanh tiến độ:
  - Phase 0–4: xong
  - Phase 5: xong phần offline
  - Phase 6–12: chưa làm

**Lời thoại**

> Tôi không đưa thẳng ảnh vào mạng nơ-ron. Thay vào đó, MediaPipe rút mỗi khung hình thành
> 21 điểm mốc trên bàn tay, tức là khung xương bàn tay.
>
> Cách này có ba lợi ích:
>
> - Loại bỏ phần lớn khác biệt về nền, ánh sáng và màu da.
> - Dữ liệu rất gọn, chỉ 42 con số mỗi frame, nên chạy được trên CPU.
> - Cho phép thiết kế đặc trưng có ý nghĩa vật lý, như "cổ tay đi ngang bao xa" hay "hai
>   ngón mở ra bao nhiêu".
>
> Chuỗi điểm mốc được cắt thành các cửa sổ 1,2 giây, chuẩn hoá, rồi đưa vào mô hình. Kế
> hoạch có ba mô hình: luật ngưỡng, rừng ngẫu nhiên trên đặc trưng, và LSTM một chiều trên
> chuỗi toạ độ. Mô hình luật đi trước, vừa làm đường cơ sở, vừa để kiểm tra cả đường ống.
> Cuối cùng, một máy trạng thái biến chuỗi dự đoán liên tục thành đúng một lệnh cho mỗi cử
> chỉ.
>
> Dự án chia thành 13 phase. Mỗi phase có tiêu chí hoàn thành kiểm tra được bằng lệnh chạy.
> Hiện tôi đã xong phần offline của Phase 5: hệ thống chạy được đầu-cuối với mô hình luật.

---

## Slide 4 — Dữ liệu IPN Hand và chiến lược "IPN trước" · ⏱ 1:30

**Trên slide**

- IPN Hand:
  - 200 video, 50 người diễn
  - 640×480, khoảng 30 FPS
  - 14 lớp gốc
  - có cách chia train/test chính thức theo người
- Ánh xạ về 5 lớp:
  - Hất trái → vuốt trái; hất phải → vuốt phải; zoom in; zoom out
  - 10 lớp còn lại → "không cử chỉ". Trong đó hất lên, hất xuống, xòe tay hai lần và chỉ trỏ
    là **mẫu âm khó**
- Hai điều kiện đi kèm:
  1. Người dùng làm cử chỉ theo cách của IPN
  2. Quy ước hướng lấy theo IPN, phải đo chứ không đoán
- Cái chấp nhận mất: chưa có dữ liệu điều kiện thật. Bù bằng các phép đo trực tiếp trên
  webcam ở các phase sau

**Lời thoại**

> Dữ liệu chính là IPN Hand: 200 video của 50 người, có sẵn cách chia train/test chính thức
> theo người.
>
> Bộ này có 14 lớp gốc. Tôi giữ bốn lớp trùng với bài toán, mười lớp còn lại quy hết về
> "không cử chỉ". Đây là lựa chọn có chủ đích. Các lớp như hất lên, hất xuống, xòe tay hai
> lần hay chỉ trỏ trông rất giống cử chỉ đích. Chúng là mẫu âm khó, đúng loại mà hệ thống
> phải học để không báo nhầm.
>
> Chiến lược là dùng IPN trước, chỉ tự quay dữ liệu khi có bằng chứng là cần. Biểu diễn bằng
> điểm mốc và phép chuẩn hoá đã loại phần lớn khác biệt hình ảnh giữa IPN và webcam, nên chỉ
> dùng IPN gần như không làm yếu mô hình.
>
> Đổi lại có hai điều kiện. Người dùng phải làm cử chỉ đúng kiểu người diễn IPN. Và quy ước
> trái–phải phải được đo trên chính IPN. Cái mất đi là khả năng đo hệ thống trong điều kiện
> thật; phần này sẽ được bù bằng phép đo trực tiếp trên webcam ở Phase 6 và Phase 10.

---

## Slide 5 — Nguyên tắc kỹ thuật xuyên suốt · ⏱ 1:30

**Trên slide**: "Mỗi nguyên tắc chặn một lỗi im lặng"

| Nguyên tắc | Lỗi im lặng mà nó chặn |
|---|---|
| Một đường ống cho mọi nguồn (IPN, webcam, dữ liệu tự quay) | Offline đẹp, demo loạn |
| Hằng số quy ước phải đo; chưa đo thì chương trình dừng | Vuốt trái mà slide chạy ngược |
| Frame mất tay vẫn giữ lại, ghi toạ độ rỗng | Nội suy âm thầm qua khoảng mất tay |
| Chia tập theo người | Độ chính xác 98–99% giả |
| Chỉ dùng quá khứ; LSTM một chiều | Con số không đạt được khi chạy thật |
| Mọi quyết định chỉ dựa trên train; test khoá tới lần cuối | Kết quả bị thổi phồng |

- Mỗi lần chạy có hồ sơ riêng: lệnh, thời điểm, seed, bản sao hằng số
- 90 kiểm thử tự động đạt, dùng bàn tay tổng hợp dựng bằng hình học

**Lời thoại**

> Trước khi vào kỹ thuật cụ thể, tôi trình bày các nguyên tắc, vì chúng quyết định cách tôi
> xử lý mọi chuyện về sau. Điểm chung của chúng: mỗi nguyên tắc chặn một lỗi *im lặng*, tức
> loại lỗi không làm chương trình sập mà chỉ làm kết quả sai, và rất khó truy.
>
> Quan trọng nhất là "một đường ống cho mọi nguồn". Dữ liệu IPN lúc huấn luyện và hình ảnh
> webcam lúc chạy thật đi qua đúng cùng các hàm, theo cùng thứ tự. Nếu có hai bản xử lý "gần
> giống nhau", kết quả offline sẽ đẹp còn demo thì loạn.
>
> Thứ hai là "đo, không đoán". Các hằng số quy ước như hướng vuốt, mức nhiễu, ngưỡng luật
> đều do script đo trên dữ liệu. Nếu một hằng số chưa đo mà bị dùng, chương trình dừng ngay.
>
> Ngoài ra còn ba nguyên tắc: chia tập theo người; chỉ dùng thông tin quá khứ; mọi quyết
> định chỉ dựa trên tập train, còn tập test khoá lại tới lần đánh giá cuối cùng.
>
> Khi một giả định của kế hoạch không đứng được trên dữ liệu thật, tôi làm theo trình tự:
> thử nghiệm trên train, so các phương án bằng số đo, duyệt, rồi mới sửa và ghi lý do vào
> tài liệu.
>
> Phần mềm có 90 kiểm thử tự động. Chúng dùng bàn tay 21 điểm dựng bằng hình học, nên không
> phụ thuộc dữ liệu thật hay webcam.

---

## Slide 6 — Thu nhận điểm mốc và đường ống tiền xử lý · ⏱ 2:00

**Trên slide**

- MediaPipe Hand Landmarker, chế độ video, một bàn tay
- Chỉ toạ độ 2D; bỏ độ sâu z vì ước lượng không tin cậy
- Ảnh vào mô hình không lật; chỉ bản hiển thị được lật như gương
- Đường ống 7 bước, thứ tự cố định:
  1. Đổi toạ độ sang pixel, hai trục dùng hai hệ số riêng
  2. Đưa về lưới thời gian đều 15 Hz
  3. Vá lỗ hổng ngắn: tối đa 3 bước, phải có đủ hai đầu
  4. Cắt cửa sổ 1,2 giây, trượt mỗi 0,2 giây
  5. Tăng cường (chỉ khi huấn luyện)
  6. Chuẩn hoá cửa sổ
  7. Tính đặc trưng, hoặc đưa vào mô hình chuỗi
- Hình gợi ý (cần tự vẽ): dòng thời gian có hai lỗ mất tay; lỗ ngắn được vá, lỗ dài giữ rỗng

**Lời thoại**

> Ở khâu thu nhận, tôi dùng MediaPipe Hand Landmarker ở chế độ video, theo dõi một bàn tay
> và chỉ lấy toạ độ 2D. Độ sâu mà MediaPipe ước lượng từ một camera thường không đáng tin;
> đưa vào chỉ thêm nhiễu.
>
> Có hai quyết định nhỏ nhưng quan trọng.
>
> Một: frame không thấy tay vẫn được ghi lại với toạ độ rỗng, không bỏ đi. Nếu bỏ, trục
> thời gian bị đứt, và bước nội suy phía sau sẽ âm thầm nối qua khoảng mất tay như thể tay
> vẫn ở đó.
>
> Hai: ảnh đưa vào mô hình không bao giờ lật; chỉ hình hiển thị cho người xem được lật như
> gương. Nếu lật nhầm đầu vào, hệ thống sẽ chạy ngược chiều so với dữ liệu đã học.
>
> Sau đó dữ liệu đi qua đường ống bảy bước với thứ tự cố định. Đáng chú ý nhất là bước đưa
> về lưới 15 Hz. Webcam có FPS dao động, video IPN lại khoảng 30 FPS, nên tôi đưa mọi nguồn
> về cùng một lưới thời gian đều. Phép nội suy chỉ dùng hai frame cùng có tay. Lỗ hổng tối
> đa 3 bước, tức 0,2 giây, thì vá; lỗ dài hơn giữ nguyên, vì mất tay lâu là một tín hiệu thật.
>
> Cũng vì FPS khác nhau mà cửa sổ được tính bằng giây chứ không bằng số frame: 1,2 giây là
> 18 bước, trượt mỗi 0,2 giây.

---

## Slide 7 — Chuẩn hoá cửa sổ · ⏱ 1:15

**Trên slide**

- Gốc toạ độ: cổ tay ở **frame đầu** cửa sổ
- Đơn vị: "lòng bàn tay" (cổ tay tới gốc ngón giữa), đo ở frame đầu
- Hai giá trị dùng chung cho mọi frame → không phụ thuộc vị trí và cỡ tay, nhưng **giữ quỹ đạo**
- Hình gợi ý (cần tự vẽ): hai cách chuẩn hoá đặt cạnh nhau
  - gốc theo từng frame: cú vuốt co lại thành một chấm
  - gốc theo frame đầu: cú vuốt còn nguyên
- Từ chối cửa sổ khi lòng bàn tay frame đầu < 0,5 × trung vị của chính cửa sổ đó
  - loại 2% cửa sổ
  - xoá các ngoại lai lên tới 30 lòng bàn tay

**Lời thoại**

> Chuẩn hoá là chỗ dễ làm sai nhất. Cách thông thường là trừ vị trí cổ tay của từng frame.
> Nhưng như thế cổ tay luôn nằm ở gốc toạ độ, và cú vuốt, vốn là chuyển động của cổ tay,
> biến mất hoàn toàn.
>
> Cách của tôi: lấy cổ tay ở frame đầu cửa sổ làm gốc, lấy chiều dài lòng bàn tay ở frame
> đầu làm đơn vị, rồi dùng chung hai giá trị này cho cả cửa sổ. Kết quả không phụ thuộc tay
> nằm ở đâu trong khung hình hay tay to nhỏ ra sao, nhưng vẫn giữ quỹ đạo. Kiểm thử xác nhận
> điều này: dời tay 137 pixel hay phóng to 1,6 lần, biểu diễn sai khác dưới 10⁻⁵; còn cú vuốt
> tổng hợp vẫn đi hơn hai lòng bàn tay.
>
> Trên dữ liệu thật tôi gặp thêm một vấn đề. Nếu ở frame đầu tay nghiêng cạnh hoặc điểm mốc
> sai, đơn vị đo rất nhỏ, và đặc trưng bị phóng lên tới 30 lòng bàn tay. Giải pháp là từ
> chối cửa sổ khi lòng bàn tay frame đầu ngắn hơn một nửa trung vị của chính cửa sổ đó. Phép
> so chỉ dùng dữ liệu bên trong cửa sổ, nên vẫn tôn trọng tính nhân quả. Ngưỡng 0,5 được chọn
> bằng đo: nó loại khoảng 2% cửa sổ và xoá các giá trị ngoại lai lớn.

---

## Slide 8 — 15 đặc trưng · ⏱ 1:15

**Trên slide**: 5 nhóm đặc trưng

| Nhóm | Đặc trưng | Dùng để bắt |
|---|---|---|
| Độ xòe bàn tay | đầu, cuối, thay đổi, biên độ, xu hướng | Mở hoặc nắm cả bàn tay |
| Độ mở cái–trỏ | thay đổi, biên độ | Chụm hoặc mở ngón (zoom) |
| Chuyển động cổ tay | dời ngang, dời dọc, tốc độ ngang đỉnh, tốc độ ngang trung bình, tốc độ dọc đỉnh | Vuốt |
| Hình dạng quỹ đạo | độ thẳng, tỉ lệ ngang | Vuốt một chiều hay vẫy qua lại |
| Chất lượng | tỉ lệ bước có tay | Độ tin cậy của cửa sổ |

- 5 đặc trưng có dấu mang thông tin hướng. Bản thân đặc trưng không quyết định trái hay phải
- Không bao giờ rỗng, kể cả khi cửa sổ có 30% bước mất tay

**Lời thoại**

> Từ mỗi cửa sổ đã chuẩn hoá, tôi tính 15 đặc trưng, chia thành năm nhóm. "Đầu" và "cuối"
> là trung bình ba bước đầu và ba bước cuối, để bớt nhạy với nhiễu.
>
> Năm đặc trưng có dấu gánh phần lớn việc phân biệt hai cặp lớp: vuốt trái với vuốt phải,
> zoom in với zoom out. Đó là thay đổi độ xòe, xu hướng độ xòe, thay đổi độ mở cái–trỏ, dời
> ngang, và tốc độ ngang trung bình.
>
> Một quyết định thiết kế: phần đặc trưng không tự quyết đâu là trái, đâu là phải. Việc đó
> dành cho mô hình, thông qua một hằng số hướng đã đo trên dữ liệu.
>
> Nhóm độ mở cái–trỏ được thêm vào sau, khi xem dữ liệu thật. Ban đầu tôi đo zoom bằng độ
> xòe trung bình của năm ngón. Nhưng zoom của IPN là chụm và mở ba đầu ngón cái, trỏ, giữa,
> còn ngón nhẫn và ngón út gập suốt, nên độ xòe trung bình đổi rất ít. Khoảng cách từ đầu
> ngón cái tới đầu ngón trỏ tách hai lớp zoom tốt hơn hẳn. Slide về cổng kiểm tra sẽ cho
> thấy con số.

---

## Slide 9 — Câu chuyện dữ liệu: video và nhãn IPN lệch nhau · ⏱ 2:00

**Trên slide**

- Triệu chứng: ở nhiều video, số frame đọc được khác số frame trong file nhãn
- Chẩn đoán bằng ba cách đếm độc lập:
  - số frame khai báo trong header
  - số chunk trong chỉ mục file AVI
  - số frame giải mã được thật
- Kết quả: "frame giải mã + chunk 6 byte = tổng số chunk" đúng ở **mọi** video
  → bộ giải mã âm thầm bỏ các frame "not coded" của XVID
  → 101/200 video bị, tổng 677 frame, nhiều nhất 56 frame một video
- Cách sửa: mốc thời gian lấy theo vị trí frame trong file, không theo số lần đọc
- Nhãn IPN đếm frame không thống nhất → chọn cách đếm cho từng video:

| Số video | Nhãn khớp với |
|---|---|
| 128 | Hai cách đếm như nhau |
| 57 | Số chunk (tính cả frame bị bỏ) |
| 4 | Số frame giải mã |
| 11 | Không khớp cách nào → **loại** |

- Kiểm vị trí bằng điểm mốc:
  - dịch nhãn ±70 frame quanh ranh giới "có tay ↔ không tay"
  - độ nhiễu của phép đo: −2…+6 frame
  - cách đếm sai trôi tới 40–60 frame

**Lời thoại**

> Đây là vấn đề tốn công nhất, và cũng là ví dụ rõ nhất cho nguyên tắc "đo, không đoán".
>
> Ban đầu tôi thấy độ dài nhiều video không khớp với file nhãn. Nếu bỏ qua, nhãn sẽ trượt
> dần khỏi cử chỉ thật dọc theo video, và mô hình sẽ học nhãn sai mà không có thông báo lỗi
> nào.
>
> Tôi đếm số frame theo ba cách độc lập cho cả 200 video, và phát hiện một đẳng thức đúng ở
> mọi video: số frame giải mã được, cộng số chunk 6 byte, đúng bằng tổng số chunk. Chunk 6
> byte là frame "not coded" của chuẩn XVID, nghĩa là "giữ nguyên ảnh trước", và bộ giải mã
> FFmpeg âm thầm bỏ chúng đi. 101 trên 200 video có hiện tượng này, tổng cộng 677 frame.
> Cách sửa: lấy mốc thời gian theo vị trí của frame trong file, thay vì đếm số lần đọc.
>
> Vấn đề thứ hai: chính file nhãn của IPN cũng không thống nhất. Có video đếm cả frame bị
> bỏ, có video không. Tôi phân nhóm các video bằng số đếm, nhưng không dừng ở số đếm mà kiểm
> cả *vị trí*.
>
> Cách kiểm như sau. Tay thường rời khung hình trong đoạn không cử chỉ, nên tín hiệu "có tay"
> đổi trạng thái gần ranh giới nhãn. Tôi dịch nhãn trong khoảng cộng trừ 70 frame và tìm độ
> dịch khớp nhất. Với cách đếm đúng, độ dịch nằm trong độ nhiễu của chính phép đo; với cách
> sai, nó trôi tới 40–60 frame.
>
> 11 video không khớp cách đếm nào bị loại hẳn. Tôi cũng đã thử và loại hai hướng khác: dùng
> tín hiệu tốc độ chuyển động, và bỏ các frame lặp. Cả hai đều sai ngay trên những video đã
> biết là khớp.

---

## Slide 10 — Trích điểm mốc toàn bộ IPN và đo quy ước hướng · ⏱ 1:30

**Trên slide**

- Trích điểm mốc:
  - 200/200 video, 0 lỗi
  - 2,27 giờ với 4 tiến trình song song; chạy lại thì tiếp tục, không làm lại từ đầu
  - lưu toạ độ **thô** chưa chuẩn hoá, kèm mốc thời gian, cờ có tay, đoạn nhãn
  - kiểm lại toàn bộ sau khi trích
  - chạy trên máy, không dùng Colab, để giữ đúng phiên bản thư viện của hệ thống chạy thật
- Quy ước hướng, đo trên 189 đoạn:

| Lớp | Trung vị dời ngang |
|---|---|
| Hất trái | +0,46 lòng bàn tay |
| Hất phải | −0,54 lòng bàn tay |

  → hằng số hướng = +1: "hất trái" là tay đi về bên trái **của chính người làm**
- Zoom: thay đổi độ xòe +0,20 (zoom in), −0,30 (zoom out) → bảng ánh xạ đúng chiều
- Bộ cử chỉ (tài liệu hướng dẫn đang ở bản nháp):
  - mỗi cử chỉ khoảng 2 giây, nhưng động tác chính chỉ khoảng 0,3 giây
  - khoảng 90% cử chỉ dài hơn cửa sổ 1,2 giây
  - tỉ lệ frame mất tay trong cử chỉ: 3–6%

**Lời thoại**

> Sau khi sửa lệch frame, toàn bộ 200 video được trích thành điểm mốc, không lỗi, mất
> khoảng 2,3 giờ với bốn tiến trình song song. Quá trình trích được thiết kế để chạy qua
> đêm: video đã xong thì bỏ qua, video lỗi ghi ra danh sách riêng rồi chạy tiếp.
>
> Tôi lưu toạ độ thô, chưa chuẩn hoá. Chuẩn hoá là một quyết định thiết kế có thể còn đổi,
> còn điểm mốc thô thì không. Tôi cũng chạy trên chính máy sẽ chạy demo, không dùng Colab,
> để phiên bản MediaPipe, OpenCV và bộ giải mã trùng với hệ thống thật.
>
> Tiếp theo là quy ước hướng. "Hất trái" có thể hiểu là trái của người làm, hoặc trái của
> ảnh; thêm nữa, hình hiển thị thường được lật như gương. Thay vì đoán, tôi đo trên 189 đoạn.
> Trung vị dời ngang của hất trái là dương, của hất phải là âm, nên hằng số hướng bằng +1.
> Hằng số này chỉ được dùng ở đúng một nơi, nên không bao giờ bị lật hai lần.
>
> Một chi tiết nhỏ: những đoạn mất tay ở đầu hoặc cuối cho đặc trưng bằng 0, và các số 0 đó
> từng suýt làm sai trung vị. Vì vậy phải loại chúng ra trước khi đo.
>
> Thống kê bộ dữ liệu cho một phát hiện quan trọng. Mỗi cử chỉ kéo dài khoảng 2 giây, nhưng
> động tác chính chỉ khoảng 0,3 giây; phần còn lại là chuẩn bị và thu tay. Phát hiện này dẫn
> tới thay đổi lớn nhất của dự án, ở slide sau.

---

## Slide 11 — Gán nhãn cửa sổ: neo vào khoảnh khắc chính · ⏱ 1:45

**Trên slide**

- Vấn đề: luật ban đầu "lớp chiếm ≥ 60% cửa sổ" cho **49%** cửa sổ dương không chứa động tác
  chính
- Hình gợi ý (cần tự vẽ): dòng thời gian một cử chỉ 2 giây, gồm chuẩn bị, động tác 0,3 giây,
  thu tay. Vài cửa sổ 1,2 giây trượt qua, đánh dấu cửa sổ nào dương, cửa sổ nào bị bỏ, cửa sổ
  nào là "không cử chỉ"
- Giải pháp:
  - Tìm "khoảnh khắc chính": bước mà tín hiệu đổi nhanh nhất
    - vuốt: vị trí ngang của cổ tay
    - zoom: độ mở cái–trỏ
    - làm mượt 3 bước, chỉ xét độ lớn, không xét dấu
  - Cửa sổ dương khi khoảnh khắc chính cách hai mép cửa sổ ít nhất 3 bước
  - Cửa sổ chạm cử chỉ mà không chứa khoảnh khắc chính → **bỏ**, không gán "không cử chỉ"
- Cách chọn luật:
  - so 3 luật bằng 3 chỉ số đo trên train
  - tách nhóm để chẩn đoán lỗi nằm ở nhãn hay ở đặc trưng
  - thử biên 0 và 3 bước
- Cái giá: cửa sổ dương mỗi lớp giảm từ khoảng 950 xuống khoảng 415

**Lời thoại**

> Mỗi cử chỉ dài khoảng hai giây, cửa sổ chỉ 1,2 giây, nên một cử chỉ trải qua nhiều cửa sổ.
> Câu hỏi là: cửa sổ nào nên mang nhãn cử chỉ?
>
> Luật ban đầu trong kế hoạch là "lớp đích chiếm ít nhất 60% số bước của cửa sổ". Khi đo, 49%
> cửa sổ dương theo luật này không chứa động tác chính; chúng chỉ chứa phần chuẩn bị hoặc phần
> thu tay. Nói cách khác, mô hình bị dạy rằng tay đang chuẩn bị cũng là vuốt.
>
> Giải pháp là neo nhãn vào khoảnh khắc chính. Với mỗi đoạn cử chỉ, tôi tìm bước mà tín hiệu
> thay đổi nhanh nhất: vị trí ngang của cổ tay với vuốt, độ mở cái–trỏ với zoom. Tôi chỉ xét
> độ lớn của thay đổi, không xét dấu, để không ngầm cài quy ước hướng vào nhãn. Cửa sổ là
> dương khi khoảnh khắc đó nằm cách hai mép ít nhất ba bước. Cửa sổ chạm vào cử chỉ mà không
> chứa khoảnh khắc chính thì bỏ hẳn, vì gán nó là "không cử chỉ" cũng sai.
>
> Có thể có câu hỏi: tìm khoảnh khắc chính dùng cả đoạn cử chỉ, tức là dùng tương lai, vậy có
> vi phạm tính nhân quả không? Câu trả lời là không. Đây là nhãn, tức chân lý ngoại tuyến,
> giống như chính file nhãn của IPN. Mô hình không bao giờ nhìn thấy nó.
>
> Luật này không chọn theo cảm tính. Tôi so ba luật bằng ba chỉ số đo trên train. Tôi tách
> cửa sổ dương thành hai nhóm, có và không chứa động tác, để biết lỗi nằm ở nhãn hay ở đặc
> trưng. Tôi cũng thử hai mức biên, và chỉ biên 3 bước qua được điều kiện về hướng. Cái giá là
> tập train nhỏ đi: từ khoảng 950 xuống khoảng 415 cửa sổ dương mỗi lớp.

---

## Slide 12 — Chia tập theo người, cân bằng lớp, tăng cường · ⏱ 1:45

**Trên slide**

- Chia theo người: train 30 người, val 7, test 13 (giữ đúng split test chính thức)
- Không ai có mặt ở hai tập
- Bộ cửa sổ: 37 504 cửa sổ, mỗi cửa sổ 18 bước × 21 điểm × 2 toạ độ

| Tập | Số cửa sổ | Tỉ lệ "không cử chỉ" | Mỗi lớp đích |
|---|---|---|---|
| Train (sau lấy mẫu con) | 3 326 | 50% | ~415 |
| Val (phân bố tự nhiên) | 11 038 | 96,5% | ~96 |
| Test (phân bố tự nhiên) | 23 140 | 97,2% | ~160 |

- Lấy mẫu con lớp nền, chỉ ở train: 49 652 → 1 663 cửa sổ, chia đều cho 10 nhãn gốc theo kiểu
  "rót nước"
- Tăng cường, chỉ trên train, tạo mới mỗi epoch:

| Phép biến đổi | Nhãn |
|---|---|
| Lật ngang | **Đổi** vuốt trái ↔ vuốt phải; giữ nguyên nhãn zoom |
| Xoay ±10°, co giãn đổi dần, co giãn thời gian 0,8–1,2×, nhiễu Gauss, xoá 1–3 bước | Giữ nguyên |

- Độ lệch chuẩn nhiễu: 0,0159 lòng bàn tay, đo trên tay nghỉ; khớp ước lượng độc lập 0,0162

**Lời thoại**

> Chia tập theo người là bắt buộc. Các cửa sổ liền nhau chỉ lệch 0,2 giây nên gần như giống
> hệt nhau. Nếu chia ngẫu nhiên, cùng một cử chỉ sẽ rơi vào cả train lẫn test, và độ chính
> xác 98–99% thu được sẽ hoàn toàn giả. Tôi giữ đúng tập test chính thức của IPN để so được với
> các công bố khác, và tách 20% số người của phần train làm tập val.
>
> Về mất cân bằng: lớp nền chiếm tới 97% dữ liệu tự nhiên. Ở train, tôi lấy mẫu con lớp nền
> xuống còn 50%, nhưng không lấy ngẫu nhiên. Ngân sách được chia đều cho mười nhãn gốc theo
> kiểu "rót nước": nhóm nào nhỏ hơn phần chia thì lấy hết, phần dư dồn cho các nhóm còn lại.
> Nhờ vậy các mẫu âm khó như hất lên, hất xuống hay chỉ trỏ đều có mặt, không bị nhóm đông nhất
> lấn át. Val và test giữ phân bố tự nhiên, để con số đánh giá phản ánh đúng thực tế.
>
> Với tăng cường, mỗi phép biến đổi phải trả lời câu hỏi: "có làm đổi lớp không?". Lật ngang
> đổi nhãn hai lớp vuốt cho nhau, nhưng giữ nhãn zoom.
>
> Một phát hiện thú vị: phép co giãn đều mà tôi định dùng bị bước chuẩn hoá triệt tiêu hoàn
> toàn, vì chuẩn hoá chia cho cỡ lòng bàn tay. Kiểm thử đã chứng minh điều này. Nên tôi thay
> bằng co giãn đổi dần dọc cửa sổ, mô phỏng tay tiến lại gần hoặc lùi xa camera.
>
> Mức nhiễu cũng được đo. Lần đo đầu cho 0,054. Nhưng khi kiểm tra, các cửa sổ "cổ tay đứng
> yên" phần lớn là bấm ngón và xòe tay, tức cử động có chủ ý chứ không phải độ rung. Giới hạn
> vào tay nghỉ cho 0,0159, khớp với một ước lượng độc lập bằng sai phân bậc hai là 0,0162.

---

## Slide 13 — Cổng kiểm tra đặc trưng · ⏱ 1:00

**Trên slide**

- Hình: ba boxplot theo lớp, trên train
  - thay đổi độ mở cái–trỏ
  - dời ngang cổ tay
  - tốc độ ngang đỉnh

| Điều kiện | Số đo | Kết quả |
|---|---|---|
| Zoom in nằm hẳn bên dương | phân vị 25 = +0,70 | ✅ |
| Zoom out nằm hẳn bên âm | phân vị 75 = −0,58 | ✅ |
| Hai lớp vuốt nằm ở hai phía của 0 | [+0,13; +1,35] và [−1,12; −0,31] | ✅ |
| Hai lớp vuốt cao hơn hẳn "không cử chỉ" | phân vị 25 là 3,59 và 3,70, so với phân vị 75 là 3,30 | ✅ sát nút |

- "Không mô hình nào cứu được đặc trưng không tách lớp"

**Lời thoại**

> Trước khi huấn luyện bất kỳ mô hình nào, có một cổng kiểm tra bắt buộc: nhìn boxplot các
> đặc trưng chính theo từng lớp trên tập train. Lý do đơn giản: nếu đặc trưng không tách được
> lớp thì không mô hình nào cứu được.
>
> Cổng ban đầu dựa trên độ xòe và độ thẳng của quỹ đạo, và nó không đạt. Tôi không nới điều
> kiện. Thay vào đó, tôi chẩn đoán xem nguyên nhân nằm ở nhãn hay ở đặc trưng, thử từng
> phương án trên train, và chỉ triển khai khi số đo cho thấy cổng đạt. Kết quả là luật nhãn
> mới và đặc trưng độ mở cái–trỏ. Điều kiện cổng mới được duyệt trước khi áp dụng, và điều
> kiện cũ vẫn được in ra để tham khảo.
>
> Hiện cả ba điều kiện đều đạt. Hai hộp zoom tách hẳn về hai phía. Hai hộp vuốt nằm ở hai phía
> của số 0, và điều kiện này không giả định trước lớp nào nằm bên dương. Riêng tốc độ ngang
> đỉnh qua cổng sát nút. Đây là điểm yếu nhất của bộ đặc trưng, và slide kết quả sẽ cho thấy
> hệ quả của nó.

---

## Slide 14 — Mô hình luật · ⏱ 1:00

**Trên slide**

- Ngưỡng hiệu chuẩn tự động, **chỉ trên train**: trung điểm giữa phân vị 90 của nhóm phải ở
  dưới và phân vị 10 của nhóm phải ở trên

| Đặc trưng | Ngưỡng |
|---|---|
| Tốc độ ngang đỉnh | 4,026 lòng bàn tay/giây |
| Dời ngang | 0,1025 lòng bàn tay |
| Thay đổi độ mở cái–trỏ | 0,7209 lòng bàn tay |

- Thứ tự luật:
  1. Thiếu tay → không cử chỉ
  2. Tốc độ ngang **và** dời ngang cùng vượt ngưỡng → vuốt; hướng theo dấu dời ngang so với
     hằng số đã đo
  3. Độ mở cái–trỏ tăng hoặc giảm vượt ngưỡng → zoom in hoặc zoom out
  4. Còn lại → không cử chỉ
- Vuốt được xét trước zoom, vì cú hất của IPN mở bàn tay ra, làm độ mở cái–trỏ cũng đổi
- Độ tin cậy: heuristic theo mức vượt ngưỡng yếu nhất, **không phải xác suất**

**Lời thoại**

> Mô hình đầu tiên là một bộ luật ngưỡng, dựng đúng trên ba đặc trưng của cổng kiểm tra.
>
> Ba ngưỡng được hiệu chuẩn tự động và chỉ trên train. Mỗi ngưỡng là trung điểm giữa phân vị
> 90 của nhóm phải nằm dưới và phân vị 10 của nhóm phải nằm trên. Có kiểm thử chứng minh rằng
> thêm dữ liệu val hay test cực đoan vào cũng không làm ngưỡng thay đổi. Hai trong ba ngưỡng có
> cảnh báo vì hai phân vị chồng lên nhau, tức là hai nhóm không tách sạch.
>
> Thứ tự luật có chủ đích. Vuốt được xét trước zoom, vì cú hất của IPN mở bàn tay ra, làm
> khoảng cách cái–trỏ thay đổi theo; còn zoom thì gần như không dời cổ tay. Hướng vuốt lấy
> theo dấu của dời ngang so với hằng số đã đo, không viết cứng ở đâu.
>
> Độ tin cậy đi kèm chỉ là một heuristic, và tôi không gọi nó là xác suất.

---

## Slide 15 — Kết quả trên tập val · ⏱ 1:45

**Trên slide**

| Lớp | Precision | Recall | F1 |
|---|---|---|---|
| Không cử chỉ | 0,984 | 0,560 | 0,714 |
| Vuốt trái | 0,030 | 0,577 | 0,056 |
| Vuốt phải | 0,023 | 0,438 | 0,043 |
| Zoom in | 0,097 | 0,543 | 0,164 |
| Zoom out | 0,103 | 0,617 | 0,176 |
| **Macro-F1** | | | **0,2305** |
| Đường cơ sở: luôn đoán "không cử chỉ" | | | 0,1964 |
| Đường cơ sở: đoán ngẫu nhiên | | | 0,0796 |

- Từ ma trận nhầm lẫn:
  - 44% cửa sổ "không cử chỉ" bị báo thành cử chỉ; khoảng 80% số đó thành vuốt
  - nhầm hướng vuốt rất ít: 2 cửa sổ (trái → phải) và 9 cửa sổ (phải → trái)

**Lời thoại**

> Đây là kết quả trên tập val. Tôi dùng macro-F1 thay vì độ chính xác, vì val có 96,5% cửa
> sổ không cử chỉ. Một mô hình luôn đoán "không cử chỉ" đã đạt độ chính xác 96,5%, mà không
> nhận ra được cử chỉ nào.
>
> Mô hình luật đạt macro-F1 0,23, vượt cả hai đường cơ sở: luôn đoán "không cử chỉ" được
> 0,196, đoán ngẫu nhiên được 0,08. Như vậy nó đạt tiêu chí của Phase 5. Nhưng phải nói thẳng:
> đây là kết quả yếu.
>
> Đọc kỹ bảng thì thấy recall các lớp cử chỉ khoảng 44 đến 62%, tức luật bắt được khoảng một
> nửa số cử chỉ. Vấn đề nằm ở precision. 44% cửa sổ không cử chỉ bị báo thành cử chỉ, phần
> lớn thành vuốt. Lớp nền đông hơn mỗi lớp đích hơn trăm lần, nên chừng ấy báo nhầm đủ để dìm
> precision xuống vài phần trăm. Nghi phạm chính là động tác chỉ trỏ trong IPN, vốn di chuyển
> nhanh ngang cú hất; điều này khớp với việc tốc độ ngang đỉnh chỉ qua cổng sát nút.
>
> Tin tốt là nhầm *hướng* vuốt rất hiếm, và hai lớp zoom cũng ít khi nhầm lẫn nhau. Tức là
> quy ước hướng và các đặc trưng có dấu hoạt động đúng. Thứ còn thiếu là khả năng tách cử
> chỉ khỏi chuyển động nền, và đó chính là việc của rừng ngẫu nhiên ở Phase 6 và máy trạng
> thái ở Phase 9.

---

## Slide 16 — Demo thời gian thực v0 · ⏱ 1:15

**Trên slide**

- Luồng xử lý:
  1. Webcam → điểm mốc
  2. Bộ đệm giữ 1,7 giây gần nhất, **tính theo thời gian**
  3. Mỗi 0,2 giây, lấy 18 bước cuối qua cùng đường ống với IPN
  4. Chuẩn hoá → đặc trưng → luật
- Mọi xử lý nằm trong thư viện dùng chung. Chương trình demo chỉ nối camera, màn hình và
  file log
- Màn hình hiển thị:
  - ảnh lật gương, vẽ khung xương bàn tay
  - nhãn chữ lớn kèm độ tin cậy, hoặc "–" khi không có cửa sổ hợp lệ
  - tỉ lệ có tay, FPS
- Chế độ luyện tập:
  - so ba đặc trưng của cửa sổ vừa làm với khoảng 25–75% của lớp tương ứng trên IPN
  - xanh là đạt, đỏ là lệch; chọn cử chỉ đang luyện bằng phím 1–4
- Log: mỗi dự đoán một dòng; khi thoát, đếm số "đợt báo"
- Hình gợi ý: ảnh chụp màn hình demo, hoặc video chạy trên một video IPN của tập val

**Lời thoại**

> Hệ thống đã chạy được đầu-cuối. Khi chạy thật, mỗi frame webcam đi qua MediaPipe rồi vào
> một bộ đệm giữ 1,7 giây gần nhất. Bộ đệm tính theo thời gian chứ không theo số frame, vì FPS
> webcam dao động. Cứ 0,2 giây, 18 bước cuối được đưa qua đúng đường ống đã dùng cho IPN: cùng
> hàm nội suy, cùng chuẩn hoá, cùng đặc trưng. Chương trình demo không định nghĩa lại bất kỳ
> hàm xử lý nào. Đó là cách tôi bảo đảm nguyên tắc "một đường ống".
>
> Có một chế độ tôi thấy đặc biệt hữu ích: chế độ luyện tập. Mô hình học cử chỉ theo cách của
> người diễn IPN, nên người dùng cần biết mình làm có giống không. Màn hình hiện ba đặc trưng
> của cửa sổ vừa làm, tô xanh nếu nằm trong khoảng 25–75% của lớp đó trên IPN, tô đỏ nếu lệch.
> Đây là cách kiểm tra việc "làm cử chỉ theo IPN" bằng số, chứ không bằng cảm giác.
>
> Demo đã được kiểm tra mà không cần webcam, bằng cách chạy trên video IPN của tập val: đúng
> nhịp 0,2 giây, log ghi đủ cột. Phần thử trực tiếp trên webcam là bước tiếp theo; tôi sẽ nói ở
> slide sau.
>
> *(Nếu có video demo, chiếu 30–60 giây tại đây.)* Khi xem, xin lưu ý: nhãn nhấp nháy liên tục
> hơn một giây mỗi khi làm cử chỉ là hành vi đúng ở mốc này, vì cứ 0,2 giây lại có một cửa sổ
> mới. Dẹp hiện tượng này là việc của máy trạng thái.

---

## Slide 17 — Hạn chế và kế hoạch tiếp theo · ⏱ 1:30

**Trên slide**

- Hạn chế hiện tại:
  - Báo nhầm cao: 44% cửa sổ nền; tốc độ ngang đỉnh là đặc trưng yếu nhất
  - Train nhỏ: khoảng 415 cửa sổ dương mỗi lớp
  - Nhãn dương phụ thuộc độ lớn chuyển động
  - Còn ngoại lai do điểm mốc nhảy giữa cửa sổ
  - Mới xét tay phải
  - Tập test còn 44 video của 12 người, sau khi loại video lệch nhãn
  - Chưa thử trực tiếp trên webcam (5 hạng mục của Phase 5)
- Kế hoạch:

| Phase | Nội dung |
|---|---|
| 5 (phần còn lại) | Thử trên webcam: hướng vuốt; mỗi cử chỉ đúng ≥ 7/10 lần; đếm báo nhầm trong 2 phút gõ phím |
| 6 | Rừng ngẫu nhiên; quyết định có cần tự quay dữ liệu |
| 7 | LSTM một chiều trên chuỗi 42 chiều |
| 8 | Đánh giá hai mức (cửa sổ và sự kiện) và 7 bảng khảo sát |
| 9 | Máy trạng thái: mỗi cử chỉ đúng một lệnh |
| 10 | Demo phát phím tắt thật; đo FPS, độ trễ, số lần báo nhầm mỗi phút |
| 11 | *(Tuỳ chọn)* Dữ liệu tự quay |
| 12 | Tái lập toàn bộ từ đầu |

**Lời thoại**

> Tôi muốn nêu rõ các hạn chế.
>
> Lớn nhất là báo nhầm.
>
> Thứ hai, tập train khá nhỏ sau khi đổi luật nhãn và loại 11 video. Tăng cường tạo mới ở mỗi
> epoch trong Phase 6 và 7 sẽ là cách bù chính.
>
> Thứ ba, nhãn dương phụ thuộc độ lớn chuyển động; điều này sẽ được nêu rõ trong báo cáo.
>
> Và quan trọng: phần thử trực tiếp trên webcam của Phase 5 chưa làm. Phần này gồm kiểm tra
> vuốt sang trái của tôi có ra vuốt trái không, mỗi cử chỉ đúng ít nhất 7 trên 10 lần, vẫy tay
> không bị nhận thành vuốt, và đếm số lần báo nhầm khi gõ phím, dùng chuột. Nếu hướng bị
> ngược, cách sửa đã được thiết kế sẵn: đổi một hằng số và chạy lại các phép đo, không sửa
> code.
>
> Kế hoạch tiếp theo bắt đầu với rừng ngẫu nhiên trên 15 đặc trưng. Tôi kỳ vọng nó tách nền
> tốt hơn hẳn, vì nó kết hợp được nhiều đặc trưng cùng lúc. Nếu nó không cao hơn hẳn mô hình
> luật, đó là dấu hiệu lỗi nằm trong đường ống chứ không phải ở mô hình. Sau đó là LSTM một
> chiều, đánh giá hai mức, máy trạng thái để mỗi cử chỉ phát đúng một lệnh, và cuối cùng là
> demo điều khiển thật, kèm các phép đo FPS, độ trễ và tỉ lệ báo nhầm mỗi phút.

---

## Slide 18 — Kết luận · ⏱ 0:30

**Trên slide**: Ba điều đã làm được

1. Một đường ống duy nhất, nhân quả, có kiểm thử, chạy được đầu-cuối từ webcam hoặc video tới
   nhãn
2. Dữ liệu IPN đã được làm sạch và hiểu bằng số: sửa lệch frame, đo quy ước hướng, gán nhãn
   theo động tác chính, chia tập theo người
3. Một đường cơ sở trung thực: mô hình luật vượt hai đường cơ sở, và điểm yếu (báo nhầm) đã
   được định vị

**Lời thoại**

> Tóm lại, đến thời điểm này tôi đã có ba thứ:
>
> - một đường ống xử lý duy nhất, tôn trọng tính nhân quả và có kiểm thử;
> - một bộ dữ liệu IPN đã được chẩn đoán, sửa lỗi và chia đúng chuẩn;
> - một mô hình đường cơ sở cùng demo chạy được, với điểm yếu đã được đo và định vị rõ ràng.
>
> Các phase tiếp theo sẽ tập trung đúng vào điểm yếu đó. Cảm ơn thầy cô và các bạn đã lắng
> nghe. Tôi sẵn sàng nhận câu hỏi.

---

## Phụ lục A — Chuẩn bị hỏi đáp

**1. Vì sao dùng điểm mốc thay vì đưa ảnh vào CNN?**

- Dữ liệu nhỏ (vài nghìn cửa sổ train) và phải chạy CPU thời gian thực.
- Điểm mốc loại bỏ nền, ánh sáng, màu da. Đây cũng là lý do huấn luyện trên IPN mà vẫn dùng
  được trên webcam khác.
- Cái giá: phụ thuộc chất lượng MediaPipe. Tỉ lệ frame mất tay trong cử chỉ là 3–6%.

**2. Macro-F1 0,23 thấp như vậy thì có ý nghĩa gì?**

- Mô hình luật là đường cơ sở, không phải sản phẩm cuối.
- Nó cho biết hai điều:
  1. Vượt cả hai đường cơ sở, nên đường ống hoạt động đúng.
  2. Lỗi chính là báo nhầm lớp nền, không phải nhầm hướng.
- Độ chính xác (accuracy) sẽ gây hiểu lầm, vì val có 96,5% cửa sổ nền.

**3. Sao không chọn ngưỡng trên val để F1 cao hơn?**

- Val dùng để đánh giá. Chọn ngưỡng trên val thì con số trên val bị thổi phồng.
- Mọi quyết định dựa trên train; test chỉ chạy đúng một lần ở cuối.

**4. Vì sao chia theo người, không chia ngẫu nhiên?**

- Cửa sổ liền nhau chỉ lệch 0,2 giây, gần như trùng nhau.
- Chia ngẫu nhiên gây rò rỉ, cho 98–99% giả.
- Phase 8 có một bảng đo định lượng khoảng chênh này.

**5. Cửa sổ 1,2 giây mà cử chỉ dài 2 giây, có cắt mất cử chỉ không?**

- Phần cần nhận ra là động tác chính, khoảng 0,3 giây. Cửa sổ 1,2 giây chứa trọn động tác cộng
  ngữ cảnh.
- Cửa sổ dài hơn làm tăng độ trễ.
- Phase 8 sẽ khảo sát 0,8 / 1,2 / 1,6 giây.

**6. Gán nhãn theo khoảnh khắc chính có dùng thông tin tương lai không?**

- Nhãn là chân lý ngoại tuyến; mô hình không thấy nó. Đầu vào của mô hình chỉ có quá khứ.
- Hệ quả cần nói rõ: nhãn dương phụ thuộc độ lớn chuyển động.

**7. Vì sao loại 11 video thay vì cố sửa?**

- Khi kiểm vị trí bằng điểm mốc, không cách đếm nào khớp. Giữ lại tức là giữ nhãn sai một cách
  im lặng.
- Cái giá: tập test mất 8 video, và một người mất cả 4 video.

**8. Vì sao không dùng độ sâu z?**

- Độ sâu ước lượng từ một camera thường không tin cậy.
- Thêm vào chỉ là thêm 21 chiều nhiễu.

**9. Ảnh webcam lật gương thì hướng vuốt có bị ngược không?**

- Ảnh vào mô hình không bao giờ lật; chỉ hình hiển thị được lật.
- Hướng do hằng số đo trên IPN quyết định.
- Nếu thử trên webcam thấy ngược: đổi một hằng số và chạy lại các phép đo, không sửa code.

**10. Độ tin cậy của mô hình luật là gì?**

- Là một heuristic, từ 0,5 tới 1, tăng theo mức vượt ngưỡng của điều kiện yếu nhất.
- Không phải xác suất. Rừng ngẫu nhiên và LSTM sẽ cho xác suất thật.

**11. Làm sao biết tăng cường không làm hỏng nhãn?**

- Mỗi phép biến đổi đi kèm câu hỏi "có đổi lớp không". Lật ngang thì đổi nhãn hai lớp vuốt.
- Có kiểm thử cho việc lật ngang đổi đúng nhãn, và cho việc tăng cường không chạm vào val, test.
- Tăng cường từ chối chạy trên mọi tập khác train.

**12. Vì sao val có 96,5% lớp nền mà train chỉ có 50%?**

- Train được cân bằng để mô hình học được các lớp hiếm.
- Val và test giữ phân bố tự nhiên để con số phản ánh thực tế.
- Không cân bằng 1:1, vì như vậy mô hình sẽ báo nhầm nhiều hơn khi chạy thật.

**13. Lớp nền của IPN có đại diện đủ cho việc dùng thật không?**

- Không đủ. Nó thiếu các chuyển động gõ phím, cầm chuột, khua tay khi nói. Đây là giới hạn đã
  biết và sẽ được nêu trong báo cáo.
- Cách bù:
  - đo báo nhầm trực tiếp trên webcam ở Phase 5 và Phase 10;
  - máy trạng thái ở Phase 9 sẽ coi việc hạ tay khỏi khung hình là thao tác huỷ;
  - nếu báo nhầm vượt 0,5 lần mỗi phút thì bật thu dữ liệu tự quay.

**14. Đã đo tốc độ và giới hạn của MediaPipe trên máy thật chưa?**

- Chưa đo chính thức.
- Thí nghiệm quan sát đã có công cụ nhưng chưa chạy. Nó không chặn phase nào, vì mức nhiễu đã
  được ước lượng trên IPN.
- FPS, phân rã thời gian xử lý và độ trễ sẽ được đo ở Phase 10.

---

## Phụ lục B — Số liệu tra nhanh

| Mục | Giá trị |
|---|---|
| Video IPN | 200 video, 50 người, 14 lớp gốc |
| Frame "not coded" bị bỏ | 101/200 video, 677 frame, tối đa 56 frame/video |
| Video bị loại do lệch nhãn | 11 (8 test, 3 train) |
| Trích điểm mốc | 200/200, 0 lỗi, 2,27 giờ, 4 tiến trình |
| Quy ước hướng | 189 đoạn; trung vị +0,46 / −0,54 → hằng số = +1 |
| Thời lượng cử chỉ | trung vị ~2 s; động tác chính ~0,3 s; ~90% dài hơn 1,2 s |
| Lưới thời gian, cửa sổ | 15 Hz; 1,2 s = 18 bước; trượt 0,2 s; vá lỗ ≤ 3 bước |
| Chia người | train 30 / val 7 / test 13 |
| Số cửa sổ | 37 504 (train 3 326, val 11 038, test 23 140) |
| Nhiễu tăng cường | 0,0159 lòng bàn tay (đối chiếu 0,0162) |
| Ba ngưỡng luật | 4,026 · 0,1025 · 0,7209 |
| Macro-F1 val | luật 0,2305 · luôn "không cử chỉ" 0,1964 · ngẫu nhiên 0,0796 |
| Báo nhầm trên val | 44% cửa sổ nền; ~80% trong số đó thành vuốt |
| Kiểm thử tự động | 90 đạt |

---

## Phụ lục C — Bản rút gọn và chuẩn bị

### Bản rút gọn khoảng 12 phút

Giữ các slide dưới đây, mỗi slide chỉ nói ý chính. Ý của slide 5, 8, 10, 12, 14 lồng vào slide
liền kề bằng một câu.

| Slide | Thời gian | Ghi chú |
|---|---|---|
| 1 Tiêu đề | 0:20 | |
| 2 Bài toán | 0:45 | |
| 3 Hướng tiếp cận | 1:00 | Thêm một câu về dữ liệu IPN (slide 4) |
| 6 Đường ống | 1:15 | Thêm một câu "một đường ống cho mọi nguồn" (slide 5) |
| 7 Chuẩn hoá | 0:50 | |
| 9 Lệch frame IPN | 1:30 | |
| 11 Gán nhãn | 1:15 | Thêm một câu về chia tập theo người (slide 12) |
| 13 Cổng kiểm tra | 0:45 | |
| 15 Kết quả | 1:30 | Nói thứ tự luật trong một câu (slide 14) |
| 16 Demo | 0:50 | |
| 17 Hạn chế, kế hoạch | 1:00 | |
| 18 Kết luận | 0:20 | |

### Nguồn hình có sẵn

| Slide | Hình |
|---|---|
| 10 | Đoạn mẫu có vẽ điểm mốc: `results/phase3/examples/` (ba người mỗi lớp) |
| 11 | Quỹ đạo một cửa sổ mỗi lớp: `results/phase4/window_examples/run_02/windows.png` |
| 13 | `results/phase4/boxplots/run_03/` (pinch_delta, dx, max_vx) |
| 15 | Ma trận nhầm lẫn: `results/phase5/eval_rules/run_01/confusion.md` (cần tự vẽ thành hình nhiệt) |

Các hình sơ đồ ở slide 3, 6, 7, 11 cần tự vẽ.

### Trước buổi thuyết trình

- **Nếu định demo trực tiếp:** làm trước năm hạng mục thử webcam của Phase 5, đặc biệt là kiểm
  tra hướng vuốt. Khi demo:
  - dùng tay phải;
  - ngồi đủ gần để lòng bàn tay chiếm khoảng 1/5 chiều cao khung hình;
  - đủ ánh sáng.
- **Luôn có video demo dự phòng.** Ít nhất là bản chạy trên video IPN của tập val.
- Không nói "hệ thống chính xác x%". Dùng macro-F1 và nói rõ là đo trên val.
- Chưa có số trên test. Nếu bị hỏi, giải thích rằng test được khoá tới lần đánh giá cuối.
