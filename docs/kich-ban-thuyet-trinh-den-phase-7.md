# Kịch bản thuyết trình — Nhận dạng cử chỉ bàn tay thời gian thực (đến Phase 7)

**Dựa trên:** `docs/tong-ket-den-phase-7.md` (cập nhật 2026-10-19), `docs/gestures.md` và
`docs/SPEC.md`.
**Bản trước:** `docs/kich-ban-thuyet-trinh-den-phase-5.md`. Ở bản này Phase 0–5 chỉ còn hai slide
tóm lược (slide 4–5). Muốn kể kỹ hơn thì lấy thêm slide từ bản trước (Phụ lục C).
**Thời lượng:** khoảng 25 phút trình bày, cộng 1,5 phút nếu demo trực tiếp, chưa tính hỏi đáp.
Bản rút gọn khoảng 12 phút ở Phụ lục C.
**Số slide:** 20, trong đó slide 18 (demo) là tuỳ chọn.

**Cách dùng kịch bản**

- Mỗi slide có hai phần chính:
  - *Trên slide*: chữ và hình đưa lên màn chiếu. Càng ít chữ càng tốt, font chữ Time New Roman
  - *Lời thoại*: phần nói. Không đọc lại slide.
- Kịch bản xưng "tôi"; đổi thành "em" hoặc "nhóm em" tuỳ bối cảnh.
- Mạch chính của buổi này: **từ con số trên giấy tới bàn tay thật**. Điểm trên val tăng dần qua
  ba mô hình, nhưng chính hai lần thử trên webcam quyết định mô hình nào được dùng.
- Bốn nguyên tắc khi nói:
  1. Mỗi kỹ thuật kể theo mạch **vấn đề → cách làm → bằng chứng bằng số**.
  2. Nói thẳng hạn chế: báo nhầm còn cao, chưa có máy trạng thái, chưa có phép thử trực tiếp có
     cấu trúc.
  3. Tập test **chưa dùng**, và không được nói như đã dùng.
  4. Nói rõ con số thuộc loại nào:
     - **trên val**: con số báo cáo;
     - **mức sự kiện xấp xỉ**: tỉ lệ cử chỉ có ít nhất một cửa sổ được nhận đúng, chưa qua máy
       trạng thái;
     - **trên phiên webcam**: phép đo nhanh trên log, đếm cụm nhãn, **chưa phải độ chính xác**.

---

## Slide 1 — Tiêu đề · ⏱ 0:30

**Trên slide**

- Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính
- Báo cáo tiến độ đến Phase 7: rừng ngẫu nhiên, LSTM, và hai lần thử trên webcam
- Người trình bày · lớp/môn · ngày

**Lời thoại**

> Xin chào thầy cô và các bạn. Hôm nay tôi trình bày tiến độ đề tài nhận dạng cử chỉ bàn tay
> thời gian thực để điều khiển máy tính, tính đến Phase 7.
>
> Ở mốc trước, hệ thống mới có một mô hình luật. Từ đó đến nay có thêm hai mô hình học máy:
> rừng ngẫu nhiên và LSTM. Nhưng câu chuyện chính hôm nay không nằm ở chỗ điểm trên tập val
> tăng bao nhiêu. Nó nằm ở hai lần thử trên webcam: cả hai lần, mô hình tốt trên giấy lại hỏng
> ở một cử chỉ khi gặp bàn tay thật. Tôi sẽ trình bày cách tìm ra nguyên nhân, và cách đã chọn
> để sửa.

---

## Slide 2 — Bài toán, hướng tiếp cận và tiến độ · ⏱ 1:30

**Trên slide**

- Webcam laptop, CPU, thời gian thực: tại mỗi thời điểm chỉ dùng quá khứ
- Bốn cử chỉ → bốn lệnh dự kiến: vuốt trái → slide trước · vuốt phải → slide sau · zoom in →
  phóng to · zoom out → thu nhỏ
- Cộng lớp nền "không cử chỉ", chiếm gần hết thời gian khi dùng thật
- Sơ đồ (cần tự vẽ):
  - Webcam → 21 điểm mốc → cửa sổ 1,2 giây → chuẩn hoá, rồi tách hai nhánh:
    - 15 đặc trưng → luật ngưỡng hoặc rừng ngẫu nhiên
    - chuỗi toạ độ → LSTM
  - → nhãn trên màn hình ··· *(chưa làm: máy trạng thái → phím tắt)*
- Tiến độ 13 phase:
  - Phase 0–4: xong
  - Phase 5–7: xong phần chính; còn các phép thử trực tiếp có cấu trúc
  - Phase 8–12: chưa bắt đầu

**Lời thoại**

> Nhắc lại bài toán: từ webcam laptop thông thường, nhận ra bốn cử chỉ (vuốt trái, vuốt phải,
> zoom in, zoom out) để sau này phát phím tắt, ví dụ chuyển slide hay phóng to. Mọi chuyển động
> tay khác thuộc lớp "không cử chỉ", và đây là lớp chiếm gần hết thời gian khi dùng thật. Hệ
> thống chạy trên CPU, và tại mỗi thời điểm chỉ được nhìn vào quá khứ.
>
> Hướng tiếp cận không đổi. MediaPipe rút mỗi khung hình thành 21 điểm mốc trên bàn tay. Chuỗi
> điểm mốc được cắt thành cửa sổ 1,2 giây rồi chuẩn hoá. Từ đó có hai nhánh: 15 đặc trưng thiết
> kế bằng tay cho mô hình luật và rừng ngẫu nhiên, hoặc nguyên chuỗi toạ độ cho LSTM.
>
> Về tiến độ: dự án có 13 phase. Phase 0 tới 4 đã xong. Phase 5 tới 7 xong phần chính, còn chờ
> vài phép thử trực tiếp có cấu trúc mà tôi sẽ nói ở cuối. Máy trạng thái và phát phím tắt thật
> thuộc Phase 9 và 10, chưa làm. Vì vậy hôm nay hệ thống mới hiển thị nhãn trên màn hình, chưa
> điều khiển máy tính.

---

## Slide 3 — Kết quả trong một slide · ⏱ 1:30

**Trên slide**

| Mô hình | Đầu vào | Macro-F1 trên val |
|---|---|---|
| Đoán ngẫu nhiên | — | 0,0796 |
| Luôn đoán "không cử chỉ" | — | 0,1964 |
| Luật ngưỡng (Phase 5) | 15 đặc trưng | 0,2305 |
| Rừng ngẫu nhiên (Phase 6) | 15 đặc trưng | 0,4361 |
| LSTM (Phase 7) | chuỗi 18 bước × 42 toạ độ | **0,5560** |
| Ghép: vuốt theo LSTM, zoom theo rừng (Phase 7) | cả hai | 0,5061 |

- Val: 11 038 cửa sổ của 7 người không có trong train; 96,5% là "không cử chỉ"
- Mô hình khuyên dùng cho demo: **mô hình ghép**
- 152 kiểm thử tự động đạt · tập test chưa dùng

**Lời thoại**

> Tôi nói kết quả trước. Hệ thống chạy đầu-cuối trên webcam với bốn mô hình, chọn bằng một tham
> số lúc chạy.
>
> Thước đo là macro-F1 trên tập val, tức trung bình F1 của năm lớp, lớp nào cũng nặng như nhau.
> Tôi không dùng độ chính xác, vì val có 96,5% cửa sổ không cử chỉ: luôn đoán "không cử chỉ" đã
> đạt 96,5% độ chính xác mà không nhận ra được cử chỉ nào.
>
> Từ luật sang rừng ngẫu nhiên, macro-F1 gần gấp đôi, từ 0,23 lên 0,44. LSTM lên 0,56.
>
> Nhưng xin để ý dòng cuối. Mô hình tôi khuyên dùng cho demo là mô hình ghép, có điểm trên val
> thấp hơn LSTM. Lý do nằm ở hai lần thử trên webcam, và đó là phần chính của buổi hôm nay.
>
> Thêm hai điều. Phần mềm có 152 kiểm thử tự động, đều đạt. Và tập test vẫn được khoá: mọi con
> số hôm nay là trên train, trên val, hoặc trên phiên thử trực tiếp của tôi.

---

## Slide 4 — Nền móng Phase 0–5: dữ liệu và đường ống · ⏱ 1:45

**Trên slide**

- IPN Hand: 200 video, 50 người
  - 4 lớp đích lấy từ: hất trái, hất phải, zoom in, zoom out
  - các lớp còn lại → "không cử chỉ", gồm cả mẫu âm khó: chỉ trỏ, hất lên/xuống, xòe tay hai lần
- Chia theo người: train 30 · val 7 · test 13 (đúng split test chính thức)
- Một đường ống cho mọi nguồn (video IPN, webcam): điểm mốc 2D → lưới 15 Hz → vá lỗ ≤ 3 bước →
  cửa sổ 1,2 s, trượt 0,2 s → [tăng cường, chỉ khi huấn luyện] → chuẩn hoá → đặc trưng hoặc chuỗi
  toạ độ
- Chuẩn hoá: gốc = cổ tay ở **frame đầu** cửa sổ; đơn vị = chiều dài lòng bàn tay ở frame đầu →
  giữ nguyên quỹ đạo
- Lỗi im lặng đã sửa:
  - bộ giải mã âm thầm bỏ frame "not coded": 101/200 video, 677 frame → mốc thời gian theo vị trí
    frame trong file
  - nhãn IPN đếm frame không thống nhất → chọn cách đếm cho từng video; loại 11 video
- Hằng số đo, không đoán: hướng vuốt (đo trên 189 đoạn), mức nhiễu tăng cường (0,0159 lòng bàn
  tay)
- Nhãn cửa sổ neo vào **khoảnh khắc chính** của cử chỉ

**Lời thoại**

> Phần này tôi tóm tắt nhanh nền móng đã có từ mốc trước.
>
> Dữ liệu là IPN Hand: 200 video của 50 người. Bốn lớp đích lấy từ hất trái, hất phải, zoom in
> và zoom out; mọi lớp còn lại thành "không cử chỉ", trong đó có những mẫu âm khó như chỉ trỏ
> hay xòe tay hai lần. Dữ liệu được chia theo người: 30 người train, 7 người val, 13 người test
> theo đúng split chính thức. Không bao giờ chia ngẫu nhiên trên cửa sổ, vì hai cửa sổ liền
> nhau gần như trùng nhau.
>
> Nguyên tắc số một là một đường ống cho mọi nguồn: video IPN lúc huấn luyện và webcam lúc chạy
> thật đi qua đúng cùng các hàm, theo cùng thứ tự. Mấu chốt của đường ống là chuẩn hoá: gốc toạ
> độ là cổ tay ở frame đầu cửa sổ, đơn vị là chiều dài lòng bàn tay ở frame đầu. Nhờ vậy biểu
> diễn không phụ thuộc vị trí hay cỡ bàn tay, mà vẫn giữ được quỹ đạo của cú vuốt.
>
> Trên đường đi tôi đã tìm và sửa nhiều lỗi im lặng của dữ liệu, như bộ giải mã âm thầm bỏ 677
> frame ở 101 video, hay file nhãn IPN đếm frame không thống nhất. Các hằng số quy ước, như
> hướng vuốt hay mức nhiễu, đều được đo trên dữ liệu chứ không đoán. Và nhãn của mỗi cửa sổ được
> neo vào khoảnh khắc chính của cử chỉ, tức lúc động tác diễn ra nhanh nhất.

---

## Slide 5 — Nền móng Phase 0–5: mô hình luật và demo v0 · ⏱ 0:45

**Trên slide**

- Luật ngưỡng trên 3 đặc trưng: tốc độ ngang đỉnh, dời ngang, thay đổi độ mở cái–trỏ. Ngưỡng
  hiệu chuẩn tự động, **chỉ trên train**
- Macro-F1 val 0,2305: vượt hai đường cơ sở, nhưng **44%** cửa sổ "không cử chỉ" bị báo thành cử
  chỉ
- Demo v0: mỗi 0,2 giây, đưa 1,2 giây gần nhất qua đúng đường ống của IPN
- Chế độ luyện tập: so đặc trưng của cử chỉ vừa làm với khoảng 25–75% của người diễn IPN; xanh
  là khớp, đỏ là lệch

**Lời thoại**

> Mô hình đầu tiên là bộ luật ba ngưỡng, hiệu chuẩn tự động trên train. Nó vượt hai đường cơ sở
> nhưng còn yếu: 44% cửa sổ không cử chỉ bị báo nhầm. Điểm yếu đã được định vị: luật không tách
> được cử chỉ khỏi chuyển động nền, nhất là tay đang chỉ trỏ.
>
> Cùng lúc, demo thời gian thực đã chạy được, kèm một chế độ luyện tập: màn hình so đặc trưng của
> cử chỉ vừa làm với khoảng giá trị của người diễn IPN. Chế độ này sẽ quay lại ở phần sau.

---

## Slide 6 — Rừng ngẫu nhiên: cách làm và kết quả · ⏱ 1:45

**Trên slide**

- 300 cây trên 15 đặc trưng; trọng số lớp cân lại trong từng mẫu bootstrap; không cần chuẩn hoá
  thang đo; huấn luyện 1,6 giây
- Kiểm trước khi huấn luyện: không người nào, clip nào có mặt ở cả train và val
- Một bộ đánh giá dùng chung cho mọi mô hình → các con số so được với nhau
- Tập test khoá ngay trong code: thiếu cờ "lần cuối" thì từ chối; có cờ thì ghi nhật ký
  **trước** khi đọc dữ liệu

| F1 trên val | Macro-F1 | Không cử chỉ | Vuốt trái | Vuốt phải | Zoom in | Zoom out |
|---|---|---|---|---|---|---|
| Luật | 0,2305 | 0,714 | 0,056 | 0,043 | 0,164 | 0,176 |
| Rừng ngẫu nhiên | **0,4361** | 0,951 | 0,212 | 0,232 | 0,368 | 0,417 |

- Recall các lớp cử chỉ 0,49–0,63 · precision chỉ 0,13–0,35
- 877 cửa sổ nền bị báo nhầm (8,2%), trong khi cả val chỉ có **388** cửa sổ cử chỉ thật
- Cử chỉ có ít nhất một cửa sổ được nhận đúng: vuốt 70% / 70%, zoom 59% / 56%
- Cổng Phase 6: cao hơn hẳn luật ✅ · không vượt 0,97, ngưỡng nghi rò rỉ ✅ · ba đặc trưng đầu
  bảng đúng như dự đoán: chưa đạt theo chữ, có giải thích (slide 7)
- Hình: ma trận nhầm lẫn

**Lời thoại**

> Mô hình thứ hai là rừng ngẫu nhiên 300 cây trên cùng 15 đặc trưng. Trọng số lớp được cân lại
> trong từng mẫu bootstrap, vì lớp nền vẫn chiếm một nửa train. Cây quyết định chia theo ngưỡng
> nên không cần chuẩn hoá thang đo. Huấn luyện chỉ mất 1,6 giây.
>
> Trước khi huấn luyện, script kiểm rằng không người nào, không clip nào có mặt ở cả train lẫn
> val. Mọi mô hình đi qua cùng một bộ hàm đánh giá, nên các con số so được với nhau. Tập test bị
> khoá ngay trong code: thiếu cờ "lần cuối" thì script từ chối; có cờ thì nó ghi một dòng nhật ký
> trước khi đọc dữ liệu. Đến nay chưa có dòng nào.
>
> Kết quả: macro-F1 0,44, gần gấp đôi luật, và F1 của mọi lớp cử chỉ đều tăng mạnh. Recall các
> lớp cử chỉ từ 0,49 tới 0,63. Điểm yếu vẫn là precision, chỉ 0,13 tới 0,35. Lý do nằm ở tỉ lệ
> nền. 8,2% cửa sổ nền bị báo nhầm nghe có vẻ ít, nhưng đó là 877 cửa sổ, trong khi cả tập val
> chỉ có 388 cửa sổ cử chỉ thật. Báo nhầm đông hơn cả số cử chỉ có thật.
>
> Gom các cửa sổ liền nhau của cùng một cử chỉ lại thì 70% cú vuốt, và khoảng 56 tới 59% cú zoom,
> có ít nhất một cửa sổ được nhận đúng.
>
> Phase 6 có cổng ba điều kiện. Rừng cao hơn hẳn luật: đạt. Không vượt 0,97, ngưỡng nghi rò rỉ dữ
> liệu: đạt. Điều kiện thứ ba về độ quan trọng đặc trưng chưa đạt theo đúng chữ; slide sau giải
> thích vì sao.

---

## Slide 7 — Đọc lỗi của rừng: báo nhầm từ đâu, mô hình dựa vào gì · ⏱ 1:30

**Trên slide**

- Báo nhầm, tách theo nhãn gốc của IPN:
  - nguồn chính: tay chỉ trỏ (một ngón, hai ngón) và tay không làm cử chỉ
  - xòe tay hai lần: 19% số cửa sổ bị báo nhầm, chủ yếu thành zoom
- Độ quan trọng đặc trưng, đo hai cách:
  - Gini: lúc dựng cây, trên train
  - Hoán vị: xáo một cột trên val, đo macro-F1 giảm bao nhiêu
- Ba đặc trưng đầu bảng (hoán vị): biên độ độ mở cái–trỏ · thay đổi độ mở cái–trỏ · tốc độ ngang
  đỉnh
  - dự đoán trước: thay đổi độ mở cái–trỏ · **dời ngang** · tốc độ ngang đỉnh
- Dời ngang bị "giấu" vì trùng thông tin với tốc độ ngang trung bình (tương quan hạng Spearman
  0,966). Xáo **cả cặp** thì:
  - macro-F1 giảm 0,042, ngang tốc độ ngang đỉnh
  - số cú vuốt bị đoán **ngược hướng**: 8 → 42,8
- Hình: độ quan trọng đặc trưng

**Lời thoại**

> Con số tổng chưa đủ, nên tôi đọc lỗi theo từng nguồn. Lớp nền được tách theo nhãn gốc của IPN.
> Báo nhầm chủ yếu đến từ tay đang chỉ trỏ và tay không làm cử chỉ. Riêng động tác xòe tay hai
> lần bị báo nhầm 19% số cửa sổ, chủ yếu thành zoom, vì nó cũng là các ngón tay mở ra.
>
> Tiếp theo: mô hình dựa vào đặc trưng nào? Tôi đo theo hai cách. Cách Gini đo lúc dựng cây,
> trên train. Cách hoán vị xáo trộn một cột trên val rồi xem macro-F1 giảm bao nhiêu.
>
> Trước khi huấn luyện, tôi dự đoán ba đặc trưng quan trọng nhất là thay đổi độ mở cái–trỏ, dời
> ngang và tốc độ ngang đỉnh. Thực tế, dời ngang không vào top ba. Nguyên nhân: dời ngang và tốc
> độ ngang trung bình gần như mang cùng một thông tin, tương quan hạng 0,966. Xáo một cột thì cột
> kia vẫn còn, mô hình gần như không mất gì, nên phép hoán vị từng cột đánh giá thấp cả hai.
>
> Để kiểm, tôi xáo cả cặp theo cùng một hoán vị. Macro-F1 giảm 0,042, ngang với tốc độ ngang
> đỉnh. Và số cú vuốt bị đoán ngược hướng tăng từ 8 lên khoảng 43. Tức là cặp đặc trưng này chính
> là nơi mô hình lấy thông tin trái hay phải. Vì vậy tôi ghi điều kiện thứ ba là "chưa đạt theo
> chữ, đã giải thích", chứ không nới điều kiện.

---

## Slide 8 — Thử trực tiếp lần 1: vì sao cú vuốt không được nhận · ⏱ 1:45

**Trên slide**

- Triệu chứng (log webcam, rừng ngẫu nhiên):
  - zoom được nhận đều
  - cú vuốt nhanh (tốc độ đỉnh 3,2–9,3 lòng bàn tay/giây) nhưng dời ròng chỉ 0–0,6 lòng bàn tay
    → "không cử chỉ"
- Thí nghiệm phản thực tế:
  1. Lấy cú vuốt thật của val mà rừng đang nhận đúng
  2. Sửa **đúng một** khía cạnh, giữ nguyên mọi thứ khác
  3. Cộng rung điểm mốc như dữ liệu thật
  4. Cho qua đúng chuẩn hoá và đặc trưng như lúc chạy thật

| Sửa đổi | Còn được nhận (trái / phải) |
|---|---|
| Bàn tay cứng: giữ quỹ đạo và tốc độ cổ tay, không đổi dáng tay | **0% / 0%** |
| Giữ 50% sự đổi dáng tay | 18% / 15% |
| Đi ra rồi quay về trong cùng cửa sổ | 45% / 37% |
| Quãng dời cổ tay × 0,5 | 48% / 47% |
| Cổ tay đứng yên, chỉ đổi dáng tay | 0% / 0% |

- Với rừng, "vuốt" = cú hất của IPN: cổ tay đi ngang **đủ nhanh, đủ xa**, **và** bàn tay đổi từ
  chụm sang mở
- Hình gợi ý (cần tự vẽ): quỹ đạo cổ tay và dáng tay của một cú vuốt gốc, đặt cạnh bản "bàn tay
  cứng" và bản "đi ra rồi quay về"

**Lời thoại**

> Đây là lần thử trực tiếp đầu tiên, với rừng ngẫu nhiên. Zoom được nhận đều. Nhưng nhiều cú vuốt
> của tôi bị coi là không cử chỉ. Log cho thấy đó là những cú vuốt rất nhanh, tốc độ đỉnh 3 tới 9
> lòng bàn tay mỗi giây, nhưng tay hất ra rồi kéo về ngay, nên dời ròng gần như bằng không.
>
> Độ chính xác tổng không trả lời được câu hỏi "vì sao cú vuốt của tôi không được nhận". Nên tôi
> hỏi thẳng mô hình bằng thí nghiệm phản thực tế. Lấy những cú vuốt thật trong val mà rừng đang
> nhận đúng. Sửa đúng một khía cạnh của chuyển động, giữ nguyên mọi thứ khác. Cộng rung điểm mốc
> như dữ liệu thật. Cho đi qua đúng các bước chuẩn hoá và tính đặc trưng như lúc chạy thật. Rồi
> đếm xem còn bao nhiêu phần được nhận.
>
> Kết quả rất rõ. Giữ nguyên quỹ đạo và tốc độ cổ tay, chỉ bỏ sự đổi dáng của bàn tay: không cú
> nào được nhận. Ngược lại, giữ sự đổi dáng mà cổ tay đứng yên: cũng không cú nào. Đi ra rồi quay
> về, hay chỉ đi nửa quãng, thì mất hơn một nửa.
>
> Nghĩa là rừng hiểu "vuốt" đúng như cú hất của người diễn IPN: cổ tay đi ngang đủ nhanh và đủ
> xa, đồng thời bàn tay mở ra từ dáng chụm. Trên chính cú vuốt của IPN, rừng nhận được 70%, cao
> hơn cả zoom. Vấn đề là lệch miền: tôi vuốt khác cách người diễn IPN vuốt.

---

## Slide 9 — Xử lý: luyện theo IPN, và một phép tăng cường bị tắt · ⏱ 1:15

**Trên slide**

- Dạy người theo mô hình: chế độ luyện tập hiện thêm **biên độ độ xòe** (bàn tay mở ra bao nhiêu
  trong 1,2 giây), xanh khi nằm trong khoảng 25–75% của IPN
- Dạy mô hình theo người: tăng cường "bàn tay cứng" cho cú vuốt
  - bản cứng hoàn toàn: biên độ độ xòe 0,06, trong khi tay chỉ trỏ thật đang di chuyển có
    0,2–0,8 → chỉ giúp nhận một thứ không có ở tay thật
  - bản thực tế (giữ ngẫu nhiên 0–100% sự đổi dáng): cú vuốt giữ 50% đổi dáng được nhận
    10% → 38–56%
  - giá: báo nhầm nền 8,2% → 12,5–21,6% (gấp 1,5–2,6 lần)
  - → có trong code, **tắt**; số đo đã ghi để quyết định sau
- Phiên sau khi luyện (1 phút, đo nhanh trên log):
  - 43 cửa sổ chuyển động kiểu vuốt
  - 88% có biên độ độ xòe nằm trong khoảng của IPN
  - rừng nhận **79%** là vuốt

**Lời thoại**

> Có hai hướng xử lý: dạy người theo mô hình, hoặc dạy mô hình theo người.
>
> Hướng thứ nhất rẻ: chế độ luyện tập hiện thêm biên độ độ xòe, tức bàn tay mở ra bao nhiêu trong
> cửa sổ, và tô xanh khi nằm trong khoảng của người diễn IPN.
>
> Hướng thứ hai là tăng cường dữ liệu: tạo thêm những cú vuốt "bàn tay cứng" để rừng học cả kiểu
> vuốt giữ nguyên dáng tay. Ở đây có một bài học. Bản cứng hoàn toàn trông rất hiệu quả, nhưng khi
> so phân bố thì nó không giống tay thật: độ xòe của nó gần như không đổi, còn tay thật đang di
> chuyển thì độ xòe đo được vẫn thay đổi khá nhiều, do góc nhìn đổi, điểm mốc rung và ngón tay hơi
> co duỗi. Bản cứng hoàn toàn chỉ dạy mô hình nhận một thứ không tồn tại.
>
> Bản thực tế hơn thì có giúp: trong phép quét trên val, cú vuốt giữ một nửa sự đổi dáng được nhận
> từ 10% lên 38 tới 56%. Nhưng báo nhầm nền tăng 1,5 tới 2,6 lần. Với một hệ thống mà báo nhầm là
> lỗi nguy hiểm nhất, cái giá đó quá đắt. Phép tăng cường được giữ trong code nhưng tắt, kèm số
> đo, để quyết định sau.
>
> Sau khi luyện theo chế độ mới, ở phiên kế tiếp, 88% chuyển động kiểu vuốt của tôi đã mở bàn tay
> đúng kiểu IPN, và rừng nhận 79% là vuốt. Đây là phép đo nhanh trên log, chưa phải phép thử có
> cấu trúc.

---

## Slide 10 — LSTM: thiết kế · ⏱ 1:30

**Trên slide**

- Đầu vào: cửa sổ đã chuẩn hoá, 18 bước × 21 điểm × 2 toạ độ → chuỗi 18 × 42
- Bước mất tay: lấy bước có tay gần nhất **trước** nó
  - chỉ dùng quá khứ · không bịa quỹ đạo · không tạo cú nhảy giả như khi điền 0
- LSTM **một chiều** (cố định trong code), 2 lớp × 128, dropout 0,3, lấy đầu ra ở bước cuối
- Loss CrossEntropy có trọng số lớp (nền 0,40; cử chỉ 1,59–1,63) · Adam, lr 0,001, lô 64
- 6 phép tăng cường của Phase 4, tạo mới ở mỗi epoch
- Dừng sớm và chọn checkpoint theo trung bình trượt 10 epoch của macro-F1 val (slide 12)
- CPU 4 luồng, không phụ thuộc CUDA: 106 epoch ≈ 13 phút
- Kiểm thử bắt buộc: học thuộc 10 mẫu trong 200 epoch, bằng đúng vòng huấn luyện của script

**Lời thoại**

> Mô hình thứ ba là LSTM. Khác với rừng, nó không dùng đặc trưng thiết kế bằng tay mà đọc thẳng
> chuỗi toạ độ: 18 bước, mỗi bước 21 điểm, mỗi điểm hai toạ độ, tức 42 con số. Dữ liệu IPN và
> webcam đi qua đúng một hàm mã hoá này.
>
> Một chi tiết nhỏ: bước mất tay thì điền gì? Tôi lấy giá trị của bước có tay gần nhất trước nó.
> Có ba lý do: chỉ dùng quá khứ; không bịa ra quỹ đạo, vì nội suy qua lỗ dài là điều bị cấm; và
> không điền 0, vì sau chuẩn hoá, 0 chính là vị trí cổ tay ở bước đầu, nên điền 0 sẽ tạo một cú
> nhảy giả.
>
> LSTM luôn một chiều, cố định trong code chứ không phải tham số. LSTM hai chiều đọc cả tương lai;
> nó có thể cho số đẹp hơn, nhưng là con số không đạt được khi chạy thật.
>
> Hàm loss có trọng số lớp, và sáu phép tăng cường được tạo mới ở mỗi epoch. Huấn luyện trên CPU
> mất khoảng 13 phút. Trước khi tin vòng huấn luyện, có một kiểm thử bắt buộc: mô hình phải học
> thuộc được 10 mẫu. Không thuộc nổi 10 mẫu thì lỗi nằm ở vòng huấn luyện, không ở dữ liệu.

---

## Slide 11 — LSTM: kết quả · ⏱ 1:15

**Trên slide**

| F1 trên val | Macro-F1 | Không cử chỉ | Vuốt trái | Vuốt phải | Zoom in | Zoom out |
|---|---|---|---|---|---|---|
| Rừng ngẫu nhiên | 0,4361 | 0,951 | 0,212 | 0,232 | 0,368 | 0,417 |
| LSTM | **0,5560** | 0,968 | 0,397 | 0,376 | 0,506 | 0,533 |

| | Rừng | LSTM |
|---|---|---|
| Cử chỉ có ≥ 1 cửa sổ đúng: vuốt trái / phải | 70% / 70% | **93% / 85%** |
| … zoom in / out | 59% / 56% | **89% / 80%** |
| Cửa sổ nền bị báo nhầm | 8,2% | 5,8% |
| Cụm báo nhầm mỗi phút nền | 14,8 | 8,6 |
| Báo nhầm khi chỉ trỏ một / hai ngón | 5,8% / 9,7% | 3,5% / 5,9% |
| Báo nhầm khi tay không làm cử chỉ | 10,6% | 14,5% |

- Dự đoán một cửa sổ ≈ 1 ms trên CPU

**Lời thoại**

> LSTM tăng macro-F1 từ 0,44 lên 0,56, và F1 của mọi lớp cử chỉ đều tăng. Ở mức cử chỉ, 93% cú
> vuốt trái và 85% cú vuốt phải có ít nhất một cửa sổ được nhận đúng; với zoom là 89% và 80%.
>
> Báo nhầm cũng giảm: còn 5,8% cửa sổ nền. Nếu tính một chuỗi cửa sổ liền nhau cùng nhãn là một
> cụm, thì đó là khoảng 8,6 cụm báo nhầm mỗi phút thời gian nền của IPN, so với gần 15 của rừng.
> Báo nhầm khi chỉ trỏ giảm khoảng một nửa. Nhưng không phải chỗ nào cũng tốt hơn: với tay không
> làm cử chỉ, LSTM báo nhầm nhiều hơn rừng.
>
> Tốc độ không thành vấn đề: dự đoán một cửa sổ mất khoảng 1 mili giây. Demo chỉ nạp thư viện học
> sâu khi thật sự dùng LSTM, để chạy luật hay rừng không phải chờ.

---

## Slide 12 — Đường học: con số đáng tin tới đâu · ⏱ 1:30

**Trên slide**

- Hai hình đặt cạnh nhau:
  - trái: mô hình chính, có tăng cường
  - phải: bản không tăng cường, chạy đủ 150 epoch
- Hai đường loss đo cùng một cách (chế độ đánh giá, không tăng cường) → khoảng hở chỉ do quá khớp
- Mô hình chính: loss val giảm tới khoảng epoch 20 rồi chững ở 0,43–0,50; loss train 0,25 →
  0,012; khoảng hở nới rộng nhưng loss val **không quay đầu**
- Không tăng cường: loss val (làm mượt) thấp nhất ở epoch 38 (0,490) rồi tăng lên 0,56–0,67 →
  điểm bắt đầu quá khớp hiện rõ
- Macro-F1 val dao động ±0,04 giữa hai epoch liền nhau (mỗi lớp cử chỉ chỉ có 94–104 cửa sổ):
  - chọn epoch có điểm thô cao nhất: 0,6014, một đỉnh nhiễu
  - chọn theo trung bình trượt 10 epoch: checkpoint 0,5560, trung bình trượt 0,5336
- Có / không tăng cường, ở mức thường đạt: 0,532 ± 0,036 so với 0,512 ± 0,020 → **chưa đủ bằng
  chứng để kết luận**
- Tái lập: chạy lại trùng từng chữ số suốt 106 epoch

**Lời thoại**

> Slide này trả lời câu hỏi: con số 0,556 đáng tin tới đâu.
>
> Hình bên trái là mô hình chính. Hai đường loss được đo cùng một cách, ở chế độ đánh giá và không
> tăng cường, nên khoảng hở giữa chúng chỉ phản ánh quá khớp. Loss val giảm nhanh tới khoảng epoch
> 20 rồi đi ngang, còn loss train tiếp tục giảm gần về 0. Khoảng hở nới rộng, nhưng loss val không
> quay đầu đi lên: tăng cường mới ở mỗi epoch và dropout đã giữ nó lại. Để thấy rõ điểm bắt đầu
> quá khớp, tôi chạy thêm bản không tăng cường cho đủ 150 epoch, là hình bên phải: loss val thấp
> nhất quanh epoch 38 rồi đi lên rõ rệt.
>
> Điểm thứ hai là nhiễu. Mỗi lớp cử chỉ trong val chỉ có khoảng 100 cửa sổ, nên macro-F1 nhảy
> khoảng 0,04 giữa hai epoch liền nhau. Lần huấn luyện đầu chọn epoch có điểm cao nhất và báo 0,60.
> Đó là một đỉnh nhiễu. Tôi đổi sang chọn theo trung bình trượt 10 epoch. Con số báo cáo vì vậy
> thấp hơn, 0,556, nhưng trung thực hơn. Vạch dọc trên hình trái là checkpoint chọn theo cách này,
> nên thầy cô sẽ thấy vài điểm thô phía sau cao hơn nó.
>
> Cũng vì nhiễu đó, tôi không khẳng định tăng cường làm tăng macro-F1: chênh lệch nhỏ hơn độ lệch
> chuẩn. Con số không thiên lệch sẽ đến từ năm seed ở Phase 8 và lần chạy duy nhất trên test.
>
> Cuối cùng, kết quả tái lập được: chạy lại cho ra đúng từng chữ số, suốt 106 epoch.

---

## Slide 13 — LSTM nhận cú vuốt theo cách khác rừng · ⏱ 0:45

**Trên slide**

| Sửa đổi (còn được nhận, trái / phải) | Rừng | LSTM |
|---|---|---|
| Bàn tay cứng | 0% / 0% | 8% / 0% |
| Đi ra rồi quay về | 45% / 37% | **96% / 99%** |
| Quãng dời cổ tay × 0,25 | 4% / 0% | **100% / 94%** |
| Cổ tay đứng yên, chỉ đổi dáng tay | 0% / 0% | **100% / 87%** |

- LSTM nhận cú vuốt từ **động tác của các ngón** (chụm rồi mở, ngón chỉ về một bên), không từ
  quãng đường cổ tay đi
- Vẫn đòi bàn tay đổi dáng, nhưng chịu được kiểu hất rồi kéo về

**Lời thoại**

> Chạy cùng phép thăm dò đó với LSTM cho một bức tranh khác hẳn. LSTM vẫn nhận cú vuốt khi tay hất
> ra rồi kéo về, khi cổ tay chỉ đi một phần tư quãng, thậm chí khi cổ tay đứng yên. Nó nhận cú
> vuốt từ động tác của các ngón: chụm rồi mở, ngón chỉ về một bên. Nó vẫn đòi bàn tay đổi dáng,
> nhưng không đòi cổ tay đi xa.
>
> Điều này khớp với lần thử trên webcam: với LSTM, cú vuốt của tôi được nhận tốt hơn hẳn. Nhưng
> zoom thì kém đi.

---

## Slide 14 — Thử trực tiếp lần 2: zoom kém đi với LSTM · ⏱ 1:45

**Trên slide**

- Triệu chứng (log webcam, LSTM):
  - lúc zoom: độ mở cái–trỏ thay đổi ±1,6…2,1 lòng bàn tay, **mạnh hơn** khoảng 25–75% của IPN,
    vậy mà LSTM vẫn trả "không cử chỉ", độ tin cậy 0,89–1,00
  - lúc bàn tay đứng yên: báo zoom out liên tục gần 2 giây
- Loại trừ lỗi đường ống trước: cho demo, qua đúng vòng lặp trực tiếp, chạy trên một video IPN
  của val → hai cú zoom được nhận, độ tin cậy 0,88–1,00
- Thăm dò zoom: giữ cổ tay, ngón cái, ngón trỏ; chỉ đổi các ngón còn lại

| Sửa đổi (zoom in / out) | Rừng | LSTM |
|---|---|---|
| Không sửa | 93% / 98% | 100% / 100% |
| Nhẫn và út duỗi thẳng | 63% / 85% | **10% / 35%** |
| Giữa, nhẫn và út duỗi thẳng (zoom hai ngón) | 52% / 54% | **7% / 38%** |
| Bàn tay đứng yên ở dáng cái–trỏ đang mở | 0% báo zoom | **46–62% vẫn báo zoom** |

- Hai nguyên nhân:
  1. LSTM học **kiểu zoom riêng của người diễn IPN** (ba ngón, nhẫn và út gập), không học bản
     chất "cái và trỏ rời xa hay lại gần"
  2. LSTM đoán zoom từ **một dáng tay tĩnh**

**Lời thoại**

> Lần thử thứ hai, với LSTM. Lúc tôi zoom, độ mở cái–trỏ thay đổi còn mạnh hơn người diễn IPN,
> vậy mà LSTM vẫn trả "không cử chỉ" với độ tin cậy gần tuyệt đối. Ngược lại, lúc tay tôi đứng
> yên, nó báo zoom out liên tục gần hai giây.
>
> Trước khi kết luận là lệch miền, tôi phải loại trừ lỗi đường ống. Tôi cho chính demo đó, qua
> đúng vòng lặp trực tiếp, chạy trên một video IPN của tập val. Hai cú zoom của IPN được nhận với
> độ tin cậy 0,88 tới 1, và độ mở cái–trỏ cùng tầm với của tôi. Vậy đường ống không lỗi; khác biệt
> nằm giữa tay tôi và tay người diễn IPN.
>
> Tôi làm phép thăm dò tương tự cho zoom. Lấy cú zoom thật của IPN, giữ nguyên cổ tay, ngón cái và
> ngón trỏ, chỉ thay đổi các ngón còn lại. Chỉ cần cho ngón nhẫn và út duỗi thẳng, LSTM chỉ còn
> nhận 10% cú zoom in, trong khi rừng vẫn nhận 63%. Và khi bàn tay đứng yên ở dáng cái–trỏ đang
> mở, LSTM vẫn báo zoom trong khoảng một nửa số trường hợp; rừng thì không bao giờ.
>
> Kết luận: LSTM học kiểu zoom riêng của người diễn IPN, ba ngón với nhẫn và út gập, chứ không học
> bản chất của zoom là ngón cái và ngón trỏ rời xa hay lại gần nhau. Nó còn đoán zoom từ một dáng
> tay tĩnh. Rừng nhìn chủ yếu vào khoảng cách cái–trỏ nên ít bị ảnh hưởng. Ai zoom mà không gập
> nhẫn và út, hay zoom bằng hai ngón như trên điện thoại, sẽ gần như không được LSTM nhận ra.

---

## Slide 15 — Sửa ngay trong LSTM: có lợi, nhưng giá quá đắt · ⏱ 1:00

**Trên slide**

- Hai phép tăng cường mới:
  - cú zoom mang dáng ngón phụ của một bàn tay IPN thật khác, giữ đứng yên (kho hơn 58 nghìn dáng
    tay thật lấy từ train)
  - thêm cửa sổ bàn tay đứng yên, nhãn "không cử chỉ"
- Lợi: zoom được nhận ở mọi kiểu ngón (88–98%); hết báo zoom khi tay đứng yên
- Giá:
  - precision zoom out 0,46 → **0,10**
  - báo nhầm khi chỉ trỏ một / hai ngón 3,5% / 5,9% → **12,0% / 10,2%**
- Lý do: kiểu ngón riêng của IPN chính là thứ giúp LSTM tách zoom khỏi tay chỉ trỏ
- → Có trong code, **tắt**

**Lời thoại**

> Cách sửa tự nhiên là dạy LSTM rằng ngón phụ không quan trọng. Tôi thêm hai phép tăng cường: cú
> zoom mang dáng ngón phụ của một bàn tay IPN thật khác, và cửa sổ bàn tay đứng yên mang nhãn
> "không cử chỉ". Dáng ngón lấy từ kho hơn 58 nghìn dáng tay thật của train, không tự bịa ra.
>
> Lợi ích đúng như mong đợi: zoom được nhận ở mọi kiểu ngón, và hết báo zoom khi tay đứng yên.
> Nhưng giá rất đắt: precision của zoom out rơi từ 0,46 xuống 0,10, và báo nhầm khi chỉ trỏ tăng
> lên 10 tới 12%.
>
> Lý do đáng suy nghĩ: chính kiểu ngón riêng của IPN là thứ giúp LSTM phân biệt zoom với tay chỉ
> trỏ. Bỏ nó đi thì mô hình mất luôn khả năng đó, mà bộ đặc trưng hiện tại không đo cấu hình từng
> ngón để thay thế. Phép tăng cường này cũng được giữ trong code nhưng tắt.

---

## Slide 16 — Mô hình ghép: mỗi mô hình làm phần nó vững · ⏱ 1:15

**Trên slide**

- Luật ghép (sơ đồ cần tự vẽ):
  - LSTM đoán vuốt → lấy vuốt
  - rừng đoán zoom → lấy zoom
  - còn lại → "không cử chỉ"
- Vuốt xét trước zoom; độ tin cậy = xác suất của mô hình đã quyết định nhãn
- Định nghĩa ở đúng một chỗ, dùng chung cho đánh giá và demo; kiểm thử bảo đảm hai nơi ra cùng
  nhãn

| Trên val | Rừng | LSTM | Ghép |
|---|---|---|---|
| Macro-F1 | 0,4361 | **0,5560** | 0,5061 |
| Cử chỉ có ≥ 1 cửa sổ đúng: vuốt trái / phải | 70% / 70% | 93% / 85% | 93% / 85% |
| … zoom in / out | 59% / 56% | 89% / 80% | 59% / 56% |
| Cửa sổ nền bị báo nhầm | 8,2% | 5,8% | 6,0% |
| Cụm báo nhầm mỗi phút nền | 14,8 | 8,6 | 8,9 |

- Hình: ma trận nhầm lẫn của mô hình ghép. Hàng "không cử chỉ": 640 cửa sổ báo nhầm, 475 trong số
  đó thành vuốt (phần của LSTM)

**Lời thoại**

> Cách sửa được chọn là mô hình ghép. Nguyên tắc: tin mỗi mô hình ở đúng họ cử chỉ mà phép thăm
> dò cho thấy nó vững. LSTM vững với vuốt, kể cả kiểu vuốt khác IPN. Rừng vững với zoom, vì nó
> nhìn vào khoảng cách cái–trỏ. Nên LSTM đoán vuốt thì lấy vuốt, rừng đoán zoom thì lấy zoom, còn
> lại là không cử chỉ. Cả hai phần này tôi đều đã thấy chạy tốt trên webcam. Luật ghép được định
> nghĩa ở đúng một chỗ, dùng chung cho đánh giá và demo, và có kiểm thử bảo đảm hai nơi cho cùng
> nhãn.
>
> Trên val, mô hình ghép thấp hơn LSTM: 0,51 so với 0,56. Phần vuốt giữ nguyên mức của LSTM, phần
> zoom lùi về mức của rừng. Lý do: người diễn IPN zoom đúng kiểu IPN, và với kiểu đó zoom của
> LSTM giỏi hơn. Với kiểu zoom khác IPN thì ngược lại. Báo nhầm gần như không đổi so với LSTM, và
> phần lớn là vuốt, tức đến từ phần LSTM.
>
> Vậy trên bàn tay của người dùng thật, mô hình nào tốt hơn? Slide sau trả lời.

---

## Slide 17 — Kiểm chứng trên chính bàn tay người dùng · ⏱ 1:15

**Trên slide**

- Hạ tầng mới:
  - demo ghi kèm điểm mốc thô của cả phiên, cùng định dạng với dữ liệu IPN
  - script chạy lại: đẩy từng frame qua đúng vòng dự đoán của demo, với mọi mô hình
  - kiểm chứng: trùng 150/150 dự đoán (LSTM, video IPN) và 316/316 (mô hình ghép, phiên webcam)
- Chạy lại một phiên webcam 1,1 phút qua cả bốn mô hình. Số cụm nhãn khác "không cử chỉ":

| | Luật | Rừng | LSTM | Ghép |
|---|---|---|---|---|
| Vuốt trái / phải | 5 / 4 | 5 / 2 | 7 / 11 | 7 / 11 |
| Zoom in / out | 23 / 25 | 21 / 24 | **10 / 14** | **21 / 24** |

- 205 cửa sổ "trông như zoom" (cái–trỏ đổi rõ, cổ tay chậm): LSTM trả "không cử chỉ" 57% · mô
  hình ghép báo zoom 66% · 6% bị phần vuốt giành mất
- Lưu ý: đây là **số cụm**, chưa phải độ chính xác: phiên chưa ghi tôi định làm cử chỉ nào lúc nào

**Lời thoại**

> Để trả lời, tôi cần chạy nhiều mô hình trên cùng một chuyển động tay. Nên tôi thêm một hạ tầng
> nhỏ: demo ghi lại điểm mốc thô của cả phiên, theo đúng định dạng dữ liệu IPN, và một script đẩy
> lại từng frame qua đúng vòng dự đoán của demo, với bất kỳ mô hình nào. Script này đã được kiểm
> chứng: nó cho lại đúng 150 trên 150 dự đoán của LSTM trên video IPN, và 316 trên 316 dự đoán của
> mô hình ghép trên phiên webcam.
>
> Chạy lại một phiên webcam của tôi qua cả bốn mô hình. Trên cùng chuyển động đó, LSTM chỉ ra 24
> cụm zoom, mô hình ghép ra 45, ngang với rừng và luật. Phần vuốt của mô hình ghép giữ nguyên mức
> của LSTM, nhiều hơn hẳn rừng.
>
> Phải nói rõ: đây là số cụm nhãn, chưa phải độ chính xác, vì phiên này không ghi tôi định làm cử
> chỉ nào lúc nào. Nhưng nếu chỉ xét những cửa sổ trông như zoom, tức ngón cái và ngón trỏ đổi rõ
> trong khi cổ tay chậm, thì LSTM bỏ qua 57%, còn mô hình ghép báo zoom 66%.
>
> Từ giờ, mỗi lần thử trực tiếp đều phân tích lại được offline, và mọi cách sửa đều thử được ngay
> trên chính bàn tay người dùng.

---

## Slide 18 — Demo trực tiếp (tuỳ chọn) · ⏱ 1:30

**Trên slide**

- Mô hình ghép, webcam laptop, chỉ dùng CPU
- Thứ tự: tay để yên → zoom in → zoom out → vuốt trái → vuốt phải → (tuỳ chọn) chỉ trỏ, di tay
  quanh khung

**Lệnh chạy** (không chiếu; bấm `q` hoặc `Esc` để thoát)

```
python scripts/demo.py --model hybrid --show-features
```

Phím 1–4 chọn cử chỉ để so với khoảng của IPN: 1 vuốt trái · 2 vuốt phải · 3 zoom in · 4 zoom
out. Nhãn trên màn hình là tên lớp trong code (`none`, `swipe_left`, …); "-" nghĩa là không có
cửa sổ hợp lệ (chưa đủ 1,2 giây, mất tay, hoặc tay nghiêng cạnh).

**Lời thoại** (vừa làm vừa nói)

> Đây là mô hình ghép chạy trực tiếp trên webcam laptop, chỉ dùng CPU.
>
> *(Tay để yên trong khung.)* Tay đứng yên: nhãn là "không cử chỉ".
>
> *(Bấm 3, zoom in; bấm 4, zoom out. Ba ngón cái, trỏ, giữa; nhẫn và út gập.)* Zoom in là mở ba
> đầu ngón đang chụm; zoom out là chụm lại. Các dòng đặc trưng chuyển xanh nghĩa là động tác của
> tôi nằm trong khoảng của người diễn IPN.
>
> *(Bấm 1, vuốt trái; bấm 2, vuốt phải. Chụm đầu ngón, hất ngang, mở bàn tay trong lúc hất, rồi
> giữ tay ở đó.)* Trái và phải ở đây là trái và phải của chính tôi. Hình trên màn hình được lật
> như gương cho dễ nhìn; ảnh đưa vào mô hình thì không lật.
>
> *(Tuỳ chọn: chỉ trỏ, di tay quanh khung.)* Đây là loại chuyển động dễ gây báo nhầm nhất.
>
> Xin lưu ý: mỗi cử chỉ làm nhãn sáng trong khoảng một giây, vì cứ 0,2 giây lại có một cửa sổ mới.
> Gom chúng thành đúng một lệnh là việc của máy trạng thái ở Phase 9. Hệ thống cũng chưa phát phím
> tắt thật; đó là Phase 10.

**Nếu có sự cố**

- Một cử chỉ không được nhận: nói "Đây chính là lệch miền vừa trình bày", bấm phím của cử chỉ đó,
  chỉ vào dòng đặc trưng bị đỏ, rồi làm lại.
- Báo nhầm khi chỉ trỏ hay khi để tay yên: "Đây là báo nhầm mà máy trạng thái ở Phase 9 phải xử
  lý."
- Camera hoặc máy trục trặc: chuyển ngay sang video dự phòng, không sửa tại chỗ.

---

## Slide 19 — Hạn chế và việc tiếp theo · ⏱ 1:45

**Trên slide**

- Hạn chế:
  - Báo nhầm còn cao: 5,8–8,2% cửa sổ nền, tức 8,6–14,8 cụm mỗi phút nền của IPN. Mốc cần đạt
    khi làm việc bình thường: dưới 0,5 lần mỗi phút
  - Nguồn báo nhầm: tay không làm cử chỉ (10,6–14,7% tuỳ mô hình) · xòe tay hai lần (13–19%, chủ
    yếu thành zoom) · chỉ trỏ
  - Zoom đổi chiều giữa chừng: 12–28% cú zoom có cửa sổ bị đoán ngược chiều
  - Đặc trưng chưa đo cấu hình từng ngón → chưa tách được bàn tay mở với tay chỉ trỏ
  - Val nhỏ (94–104 cửa sổ mỗi lớp cử chỉ): chênh dưới khoảng 0,04 chưa kết luận được
  - Chưa có phép thử trực tiếp có cấu trúc · mới xét tay phải · test còn 44 video của 12 người
- Việc tiếp theo:

| | Nội dung |
|---|---|
| Ngay | Phép thử hướng vuốt · đếm báo nhầm 2 phút gõ phím · mỗi cử chỉ 10 lần + 5 phút làm việc bình thường → quyết định có cần dữ liệu tự quay |
| Phase 8 | Đánh giá hai mức (cửa sổ, sự kiện) · 7 bảng khảo sát · 5 seed · k-fold theo người · chạy test đúng một lần |
| Phase 9 | Máy trạng thái: ngưỡng tin cậy, đồng thuận k trên n, thời gian nghỉ sau lệnh, hạ tay để huỷ |
| Phase 10 | Phát phím tắt thật · đo FPS, độ trễ, báo nhầm mỗi phút ở ba kịch bản · video demo |
| Phase 11 | *(Tuỳ chọn)* Dữ liệu tự quay, nếu phép thử trực tiếp cho thấy cần |
| Phase 12 | Tái lập toàn bộ bằng một lệnh |

**Lời thoại**

> Tôi muốn nêu rõ các hạn chế.
>
> Lớn nhất vẫn là báo nhầm. Trên val còn khoảng 6 tới 8% cửa sổ nền bị báo nhầm, tức khoảng 9 tới
> 15 cụm mỗi phút. Con số của IPN chưa phải con số khi làm việc bình thường, nhưng khoảng cách tới
> mốc 0,5 lần mỗi phút là rất xa. Hướng xử lý chính là máy trạng thái ở Phase 9: chỉ phát lệnh khi
> độ tin cậy vượt ngưỡng và đa số cửa sổ gần nhất đồng ý, nghỉ một khoảng sau mỗi lệnh, và hạ tay
> xuống thì huỷ hết. Những việc này không giải quyết được bằng cách huấn luyện mô hình tốt hơn.
>
> Thứ hai, 12 tới 28% cú zoom có cửa sổ bị đoán ngược chiều. Giả thuyết của tôi: luật gán nhãn
> chọn khoảnh khắc chính theo độ lớn, không theo chiều, nên phần thu tay sau cú zoom mang nhãn của
> cú zoom. Giả thuyết này sẽ được kiểm.
>
> Thứ ba, bộ đặc trưng chưa đo cấu hình từng ngón. Đó là lý do cả hai phép tăng cường liên quan đến
> kiểu ngón tay đều phải tắt. Cách sửa tận gốc là thêm đặc trưng độ duỗi của từng ngón, hoặc thêm
> dữ liệu tự quay.
>
> Thứ tư, val nhỏ, nên chênh lệch dưới khoảng 0,04 chưa kết luận được. Phase 8 sẽ dùng năm seed và
> k-fold theo người.
>
> Việc ngay trước mắt là phần của tôi: phép thử hướng, đếm báo nhầm khi gõ phím, và một lần thử
> trực tiếp có cấu trúc, gồm mỗi cử chỉ mười lần cộng năm phút làm việc bình thường. Từ số liệu đó
> sẽ quyết định có cần thu dữ liệu tự quay hay không. Sau đó là đánh giá hai mức, máy trạng thái,
> demo điều khiển thật kèm đo tốc độ và độ trễ, và cuối cùng là tái lập toàn bộ.

---

## Slide 20 — Kết luận · ⏱ 0:45

**Trên slide**: Ba điều rút ra

1. Hệ thống chạy đầu-cuối, thời gian thực trên CPU, với bốn mô hình. LSTM tốt nhất trên IPN
   (macro-F1 0,556); trên bàn tay người dùng, bằng chứng ban đầu nghiêng về mô hình ghép
2. Con số trên val là cần nhưng không đủ: hai lần thử trên webcam lộ ra lệch miền mà val không
   thấy, và thí nghiệm phản thực tế chỉ ra mô hình thật sự dựa vào gì
3. Mọi thay đổi được đo cả lợi lẫn giá trước khi bật; kết quả tái lập được từng chữ số; tập test
   còn nguyên

**Lời thoại**

> Tóm lại, ba điều.
>
> Một: hệ thống chạy đầu-cuối, thời gian thực trên CPU, với bốn mô hình. LSTM tốt nhất trên dữ
> liệu IPN; trên bàn tay của người dùng thật, bằng chứng ban đầu nghiêng về mô hình ghép.
>
> Hai: con số trên tập val là cần, nhưng không đủ. Cả hai lần, mô hình tốt trên giấy đều hỏng ở
> một cử chỉ khi gặp tay thật. Cách tôi tìm ra nguyên nhân là hỏi thẳng mô hình bằng thí nghiệm
> phản thực tế: sửa đúng một khía cạnh của cử chỉ, rồi xem mô hình còn nhận ra không.
>
> Ba: mọi thay đổi đều được đo cả lợi lẫn giá trước khi bật, kết quả tái lập được từng chữ số, và
> tập test vẫn còn nguyên cho lần đánh giá cuối.
>
> Cảm ơn thầy cô và các bạn đã lắng nghe. Tôi sẵn sàng nhận câu hỏi.

---

## Phụ lục A — Chuẩn bị hỏi đáp

**1. Mô hình ghép có macro-F1 thấp hơn LSTM, sao lại khuyên dùng?**

- Val đo cách làm cử chỉ của người diễn IPN. Họ zoom đúng kiểu ba ngón, nhẫn và út gập, và ở kiểu
  đó zoom của LSTM giỏi hơn.
- Thăm dò cho thấy zoom của LSTM gãy khi ngón phụ khác IPN, và còn báo zoom khi tay đứng yên.
- Trên phiên webcam chạy lại: cụm zoom từ 24 (LSTM) lên 45 (ghép); trong các cửa sổ trông như
  zoom, LSTM bỏ qua 57%.
- Đây mới là bằng chứng sơ bộ. Phép thử có cấu trúc sẽ xác nhận hoặc bác bỏ.

**2. Macro-F1 0,56 có thấp không?**

- Val giữ phân bố tự nhiên: 96,5% nền, mỗi lớp cử chỉ chỉ khoảng 100 cửa sổ. Một tỉ lệ báo nhầm
  nhỏ trên lớp nền cũng kéo precision lớp cử chỉ xuống mạnh.
- Ở mức cử chỉ thì cao hơn nhiều: 80–93% cử chỉ có ít nhất một cửa sổ được nhận đúng.
- Đây là mức cửa sổ, chưa có máy trạng thái.
- Không so trực tiếp được với kết quả công bố trên IPN: số lớp, cách đo và đầu vào đều khác.

**3. "93% cú vuốt trái" nghĩa là hệ thống nhận đúng 93% cú vuốt trái?**

- Chưa. Đó là tỉ lệ cử chỉ có ít nhất một cửa sổ được nhận đúng.
- Một cử chỉ vẫn có thể có thêm cửa sổ sai, hoặc sinh nhiều lệnh. Mức sự kiện đầy đủ (lệnh đúng,
  lệnh thừa, cử chỉ bị bỏ sót, số lệnh trên một cử chỉ) cần máy trạng thái, là việc của Phase 8–9.

**4. Thí nghiệm phản thực tế có đáng tin? Cử chỉ bị sửa có còn giống tay thật?**

- Mỗi phép sửa chỉ đổi đúng một khía cạnh, trên cử chỉ thật, có cộng rung, và đi qua đúng đường
  ống chạy thật.
- Bản tổng hợp được so với tay thật trước khi tin: bàn tay cứng hoàn toàn có biên độ độ xòe 0,06,
  tay chỉ trỏ thật 0,2–0,8, nên phần "lợi" đo trên bản đó bị gạt đi.
- Sửa ngón làm trong hệ toạ độ lòng bàn tay của từng bước; độ dài ngón duỗi lấy trung vị đo trên
  bàn tay mở của IPN, không tự đặt.
- Kết luận của thăm dò khớp với triệu chứng trên webcam ở cả hai lần.

**5. Sao không thu dữ liệu tự quay ngay cho xong?**

- Kế hoạch là IPN trước. Dữ liệu tự quay chỉ bật khi có bằng chứng, ví dụ một lớp đúng dưới 7/10
  lần dù đã làm đúng hướng dẫn, hoặc báo nhầm khi làm việc bình thường hơn 0,5 lần mỗi phút.
- Bằng chứng đó đến từ phép thử trực tiếp có cấu trúc, đang chờ làm.
- Nếu bật, dữ liệu tự quay phải được chia thành phần điều chỉnh và phần đánh giá, theo người hoặc
  theo buổi quay, trước khi nhìn vào.

**6. Có rò rỉ dữ liệu không? Tập test đã dùng chưa?**

- Chia theo người; script kiểm rằng không người nào, clip nào có mặt ở cả train và val.
- Tăng cường chỉ trên train, sau khi chia; ngưỡng luật chỉ chọn trên train.
- Macro-F1 dưới 0,97, ngưỡng nghi rò rỉ của kế hoạch.
- Test chưa dùng lần nào: script từ chối nếu thiếu cờ "lần cuối", và ghi nhật ký trước khi đọc dữ
  liệu. File nhật ký đó chưa tồn tại.

**7. Vì sao không dùng LSTM hai chiều, hay làm mượt hai phía cho nhãn ổn định hơn?**

- Cả hai đều đọc tương lai. Số trên val đẹp hơn nhưng không đạt được khi chạy thật.
- Làm ổn định nhãn là việc của máy trạng thái, chỉ dùng quá khứ.

**8. Lần huấn luyện đầu đạt 0,60, sao chỉ báo 0,556?**

- 0,60 là điểm thô cao nhất, rơi vào một đỉnh nhiễu (val dao động khoảng ±0,04 giữa hai epoch).
- Chọn theo điểm thô còn làm dừng sớm giữa chừng: hai lần chạy dừng ở epoch 40 và 48 vì đỉnh nhiễu
  ở epoch 20 và 28.
- Chọn theo trung bình trượt 10 epoch: checkpoint 0,556, trung bình trượt 0,534.
- Con số không thiên lệch: năm seed ở Phase 8 và lần chạy duy nhất trên test.

**9. Tăng cường có thật sự giúp LSTM?**

- Về macro-F1: chưa đủ bằng chứng (0,532 ± 0,036 so với 0,512 ± 0,020).
- Về quá khớp thì rõ: không tăng cường, loss val quay đầu đi lên sau epoch 38; có tăng cường, loss
  val không quay đầu trong suốt lần chạy.

**10. Các phép tăng cường bị tắt có phải công cốc?**

- Không. Chúng là thí nghiệm có số đo cả lợi lẫn giá, nên quyết định "tắt" có căn cứ.
- Chúng chỉ ra giới hạn thật của bộ đặc trưng: không đo cấu hình ngón thì không tách được bàn tay
  mở với tay chỉ trỏ.
- Vẫn nằm trong code. Mức tăng cường "bàn tay cứng" cho rừng là quyết định còn để ngỏ.

**11. Báo nhầm 8,6 cụm mỗi phút thì dùng thật sao được?**

- Đó là mức cửa sổ, chưa qua máy trạng thái, đo trên lớp nền của IPN, vốn gồm cả những cử chỉ khác
  như chỉ trỏ hay xòe tay.
- Máy trạng thái ở Phase 9: ngưỡng tin cậy (khởi đầu 0,75), đồng thuận 3 trên 5 cửa sổ, nghỉ 1,2
  giây sau mỗi lệnh, hạ tay để huỷ. Phase 10 chọn cấu hình cuối theo bảng đánh đổi.
- Mốc khi làm việc bình thường: dưới 0,5 lần mỗi phút; vượt thì bật dữ liệu tự quay.

**12. Hệ thống chạy nhanh cỡ nào?**

- Mỗi 0,2 giây dự đoán một cửa sổ. Rừng mất 9,2 ms mỗi cửa sổ (trước đó 62,6 ms; nhanh lên nhờ gọi
  thẳng lõi của từng cây); LSTM khoảng 1 ms.
- Mô hình nạp xong trước khi camera chạy. Thư viện học sâu (khoảng 3 giây) chỉ nạp khi chọn LSTM
  hoặc mô hình ghép.
- FPS, phân rã thời gian và độ trễ sẽ đo chính thức ở Phase 10; hiện chưa có số chính thức.

**13. Trong mô hình ghép, vì sao vuốt được xét trước zoom? Có hại không?**

- Theo thứ tự của mô hình luật: cú hất của IPN mở bàn tay, làm độ mở cái–trỏ cũng đổi theo.
- Giá đã đo: trên phiên webcam, 6% cửa sổ có động tác cái–trỏ rõ bị phần vuốt giành thành vuốt.
  Đã ghi là hạn chế.

**14. Mô hình ghép có phải giải pháp tình thế?**

- Phần nào đúng. Nhưng nó dựa trên bằng chứng thăm dò chứ không theo cảm tính, và cả hai phần đều
  đã thấy tốt trên webcam.
- Cách sửa tận gốc: thêm đặc trưng độ duỗi từng ngón, hoặc dữ liệu tự quay.

**15. Sao chọn LSTM mà không phải GRU hay Transformer?**

- LSTM một chiều là mô hình chuỗi trong kế hoạch. Phase 8 có các hàng so GRU thay LSTM, kích thước
  ẩn 64 với 128, và cách gộp đầu ra.
- Train chỉ có 3 326 cửa sổ, nên ưu tiên mô hình nhỏ. Transformer chưa nằm trong kế hoạch.

**16. Tay trái thì sao?**

- Chưa xét riêng; 133/145 clip train là tay phải. Demo dùng tay phải.
- Phép lật ngang trong tăng cường có thể giúp, nhưng chưa đo.

---

## Phụ lục B — Số liệu tra nhanh

| Mục | Giá trị |
|---|---|
| Dữ liệu | IPN Hand, 200 video, 50 người; chia train 30 · val 7 · test 13 người |
| Cửa sổ | 1,2 s = 18 bước ở 15 Hz, trượt 0,2 s · train 3 326 (50% nền) · val 11 038 (96,5% nền) · test 23 140 |
| Cửa sổ cử chỉ trong val | 388, tức 94–104 mỗi lớp |
| Macro-F1 val | ngẫu nhiên 0,0796 · luôn "không cử chỉ" 0,1964 · luật 0,2305 · rừng 0,4361 · LSTM 0,5560 · ghép 0,5061 |
| Cử chỉ có ≥ 1 cửa sổ đúng (vuốt trái/phải; zoom in/out) | rừng 70/70; 59/56 · LSTM 93/85; 89/80 · ghép 93/85; 59/56 (%) |
| Cửa sổ nền bị báo nhầm | luật 44% · rừng 8,2% · LSTM 5,8% · ghép 6,0% |
| Cụm báo nhầm mỗi phút nền | rừng 14,8 · LSTM 8,6 · ghép 8,9 |
| Báo nhầm theo nguồn (rừng → LSTM) | chỉ trỏ một ngón 5,8 → 3,5% · hai ngón 9,7 → 5,9% · không cử chỉ 10,6 → 14,5% · xòe tay hai lần 13–19% tuỳ mô hình |
| Rừng ngẫu nhiên | 300 cây · huấn luyện 1,6 s · 9,2 ms/cửa sổ (trước 62,6 ms) |
| LSTM | một chiều, 2 lớp × 128, dropout 0,3 · 106 epoch ≈ 13 phút CPU · checkpoint epoch 86 · ≈ 1 ms/cửa sổ |
| Độ nhiễu macro-F1 val | ±0,04 giữa hai epoch · điểm thô cao nhất 0,6014 (đỉnh nhiễu) · trung bình trượt 0,5336 |
| Có / không tăng cường (LSTM) | 0,532 ± 0,036 / 0,512 ± 0,020 → chưa đủ bằng chứng |
| Quá khớp, bản không tăng cường | loss val làm mượt thấp nhất ở epoch 38 (0,490), sau đó 0,56–0,67 |
| Thăm dò vuốt, trái/phải (rừng; LSTM) | bàn tay cứng 0/0; 8/0 · đi rồi về 45/37; 96/99 · cổ tay đứng yên 0/0; 100/87 (%) |
| Thăm dò zoom, in/out (rừng; LSTM) | nhẫn, út duỗi 63/85; 10/35 · zoom hai ngón 52/54; 7/38 · tay tĩnh vẫn báo zoom 0; 46–62 (%) |
| Tăng cường bàn tay cứng (rừng, đang tắt) | lợi 10% → 38–56% · báo nhầm 8,2% → 12,5–21,6% |
| Tăng cường đổi ngón phụ (LSTM, đang tắt) | precision zoom out 0,46 → 0,10 · báo nhầm chỉ trỏ 3,5/5,9 → 12,0/10,2% |
| Phiên sau luyện tập (rừng) | 43 cửa sổ kiểu vuốt · 88% đúng độ xòe IPN · 79% nhận là vuốt |
| Phiên chạy lại | cụm zoom: LSTM 24 → ghép 45 · 205 cửa sổ trông như zoom: LSTM bỏ 57%, ghép báo zoom 66% |
| Kiểm chứng chạy lại | 150/150 và 316/316 dự đoán trùng |
| Kiểm thử tự động | 152 đạt |
| Tập test | chưa dùng |

---

## Phụ lục C — Bản rút gọn và chuẩn bị

### Bản rút gọn khoảng 12 phút

Giữ các slide dưới đây, mỗi slide chỉ nói ý chính. Ý của slide 5, 7, 9, 10, 12, 15 lồng vào slide
liền kề bằng một câu.

| Slide | Thời gian | Câu lồng vào |
|---|---|---|
| 1 Tiêu đề | 0:20 | |
| 2 Bài toán, tiến độ | 0:45 | |
| 3 Kết quả trong một slide | 1:00 | |
| 4 Nền móng Phase 0–5 | 1:00 | "Mô hình luật đạt 0,23 nhưng báo nhầm 44% cửa sổ nền; demo và chế độ luyện tập đã chạy được." |
| 6 Rừng ngẫu nhiên | 1:15 | "Báo nhầm chủ yếu đến từ tay chỉ trỏ và tay không làm cử chỉ." |
| 8 Thử trực tiếp lần 1 | 1:30 | "Chế độ luyện tập hiện thêm độ mở bàn tay; sau khi luyện, rừng nhận 79% chuyển động kiểu vuốt." |
| 11 LSTM: kết quả | 1:00 | "LSTM một chiều đọc thẳng chuỗi 42 toạ độ; val nhiễu khoảng ±0,04 nên checkpoint chọn theo trung bình trượt 10 epoch." |
| 13 LSTM nhận vuốt khác rừng | 0:30 | |
| 14 Thử trực tiếp lần 2 | 1:15 | |
| 16 Mô hình ghép | 1:00 | "Sửa thẳng trong LSTM có thử, nhưng báo nhầm khi chỉ trỏ tăng lên 10–12%, nên phải tắt." |
| 17 Kiểm chứng trên tay người dùng | 0:45 | |
| 19 Hạn chế, việc tiếp theo | 1:00 | |
| 20 Kết luận | 0:20 | |

### Muốn kể kỹ Phase 0–5 hơn

Chèn sau slide 4 các slide sau của `docs/kich-ban-thuyet-trinh-den-phase-5.md`:

| Slide của bản trước | Nội dung | Thời gian |
|---|---|---|
| 7 | Chuẩn hoá cửa sổ | 1:15 |
| 9 | Video và nhãn IPN lệch nhau | 2:00 |
| 11 | Gán nhãn cửa sổ theo khoảnh khắc chính | 1:45 |
| 13 | Cổng kiểm tra đặc trưng | 1:00 |

### Nguồn hình có sẵn

| Slide | Hình |
|---|---|
| 2 | Đoạn mẫu bốn cử chỉ có vẽ điểm mốc: `results/phase3/examples/` (ba người mỗi cử chỉ) |
| 3 | Bảng so sánh mô hình: `results/model_comparison.md` |
| 6 | Ma trận nhầm lẫn của rừng: `results/phase6/train_rf/run_07/confusion.png` |
| 7 | Độ quan trọng đặc trưng: `results/phase6/train_rf/run_07/importances.png` |
| 11 | Ma trận nhầm lẫn của LSTM: `results/phase6/evaluate/run_06/confusion.png` |
| 12 | Đường học: `results/phase7/train_lstm/run_07/training_curves.png` (trái) và `results/phase7/train_lstm/run_04/training_curves.png` (phải) |
| 16 | Ma trận nhầm lẫn của mô hình ghép: `results/phase6/evaluate/run_05/confusion.png` |

Cần tự vẽ: sơ đồ đường ống (slide 2), minh hoạ phép thăm dò (slide 8 và 14), sơ đồ luật ghép
(slide 16).

**Lưu ý khi chiếu hình:**

- Tên lớp trên các hình là tên trong code: `none` là "không cử chỉ", `swipe_left` là vuốt trái, …
- Phụ đề hình đường học ghi "macro-F1 val cao nhất", dễ bị hỏi:
  - hình trái: vạch dọc (epoch 86) là checkpoint có **trung bình trượt** 10 epoch cao nhất; vài
    điểm thô phía sau cao hơn nó;
  - hình phải: vạch dọc (epoch 20) là epoch có macro-F1 thô cao nhất, **không** phải điểm bắt đầu
    quá khớp. Khi nói, chỉ vào đường loss val đi lên từ khoảng epoch 40.

### Trước buổi thuyết trình

- **Phép thử hướng, trước khi demo vuốt.** Mở demo, vuốt sang trái *của chính mình*: phải ra
  `swipe_left`. Nếu ra `swipe_right` thì quy ước bị ngược; cách sửa ở `docs/SPEC.md`, mục Cổng
  chất lượng (đổi `IPN_FLIP_X`, chạy lại các phép đo, không sửa code). Chưa sửa xong thì không
  demo vuốt. Việc này cũng đang chặn việc đóng Phase 5, nên làm sớm.
- **Môi trường:** conda env `action-recognition`, `python --version` ra 3.10.x. Chạy thử demo một
  lần trên đúng máy, và nếu được thì ở đúng phòng sẽ trình bày: ánh sáng khác thì điểm mốc khác.
- **Tư thế khi demo** (theo `docs/gestures.md`):
  - tay phải; lòng bàn tay chiếm khoảng 1/5 chiều cao khung hình; đủ sáng;
  - zoom: ba ngón cái–trỏ–giữa, **nhẫn và út gập**;
  - vuốt: chụm đầu ngón, hất ngang một chiều, mở bàn tay trong lúc hất, rồi giữ tay ở đó;
  - giữa hai cử chỉ, để tay yên một nhịp.
- **Luôn có video dự phòng:**
  - quay màn hình một lượt demo mô hình ghép trên webcam. Chạy kèm `--log <file>.csv` thì phiên đó
    còn chạy lại được bằng `scripts/replay_log.py`;
  - bản không cần webcam: chạy mô hình ghép trên một video IPN của tập val:

    ```
    python scripts/demo.py --model hybrid --source data/ipn/videos/videos/1CM42_12_R__157.avi --max-sec 132
    ```

    Theo `results/phase7/notes.md`, mô hình ghép nhận được cả hai cú zoom và cú vuốt trái trong
    video này, nhưng vẫn còn vài cụm báo vuốt nhầm lúc người diễn chỉ tay.
- **Nếu đã làm phép thử có cấu trúc trước buổi thuyết trình:** thay bảng số cụm ở slide 17 bằng số
  lần đúng trên 10 lần mỗi cử chỉ và số báo nhầm mỗi phút, rồi cập nhật slide 19 và câu 1 của Phụ
  lục A.
- **Cách nói số:** không nói "hệ thống chính xác x%"; nói macro-F1 trên val. Chưa có số trên test.
  Nếu bị hỏi, giải thích rằng test được khoá tới lần đánh giá cuối.
