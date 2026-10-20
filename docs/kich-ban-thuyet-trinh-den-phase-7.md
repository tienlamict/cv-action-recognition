# Kịch bản thuyết trình — Nhận dạng cử chỉ bàn tay thời gian thực (Phase 6 và Phase 7)

**Dựa trên:** `docs/tong-ket-den-phase-7.md` (cập nhật 2026-10-20).
**Người nghe:** không cần biết trước về học máy. Mỗi khái niệm được giải thích ngay lần đầu xuất
hiện, bằng đúng các ví dụ đời thường của bản tổng kết.
**Thời lượng:** khoảng 25 phút, cộng 1,5 phút nếu demo trực tiếp, chưa tính hỏi đáp. Bản rút gọn
khoảng 12 phút ở Phụ lục C.
**Số slide:** 22, trong đó slide 20 (demo) là tuỳ chọn.
**Phase 0–5** chỉ còn trong phần bối cảnh (slide 3–4). Bản kể kỹ, cho người nghe có nền kỹ thuật:
`docs/kich-ban-thuyet-trinh-den-phase-5.md`.

**Cách dùng kịch bản**

- Mỗi slide có hai phần:
  - *Trên slide*: chữ và hình đưa lên màn chiếu. Càng ít chữ càng tốt.
  - *Lời thoại*: phần nói. Không đọc lại slide.
- Kịch bản xưng "tôi"; đổi thành "em" hoặc "nhóm em" tuỳ bối cảnh.
- Mạch chính: **từ điểm số trên giấy tới bàn tay thật**. Hai mô hình học máy lần lượt cho điểm cao
  hơn, nhưng mỗi lần đem ra thử trên webcam lại lộ một vấn đề mà điểm số không cho thấy.
- Năm nguyên tắc khi nói:
  1. Khái niệm mới: một câu định nghĩa, rồi một ví dụ đời thường. Từ tiếng Anh chỉ nhắc một lần,
     ở lần đầu.
  2. Mỗi slide chỉ nhấn một hai con số. Số còn lại để trên slide cho ai muốn đọc.
  3. Kể theo mạch **vấn đề → cách làm → bằng chứng bằng số**.
  4. Nói thẳng hạn chế. Đề thi thật (tập kiểm tra) **chưa mở**, và không được nói như đã mở.
  5. Nói rõ con số thuộc loại nào:
     - **trên đề thi thử** (tập kiểm định): con số báo cáo;
     - **theo cử chỉ**: cử chỉ có ít nhất một cửa sổ được nhận đúng, chưa qua máy trạng thái;
     - **trên phiên webcam**: đếm số lần báo trong log, **chưa phải độ chính xác**, vì log không ghi
       lúc nào tôi định làm cử chỉ gì.

---

## Slide 1 — Tiêu đề · ⏱ 0:30

**Trên slide**

- Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính
- Phase 6 và 7: hai mô hình học máy, và hai lần thử trên webcam
- Người trình bày · lớp/môn · ngày

**Lời thoại**

> Xin chào thầy cô và các bạn. Hôm nay tôi trình bày hai giai đoạn gần nhất của đề tài nhận dạng
> cử chỉ bàn tay thời gian thực để điều khiển máy tính: Phase 6 và Phase 7.
>
> Trong hai giai đoạn này, tôi dạy máy tính nhận cử chỉ bằng hai mô hình học máy: rừng ngẫu
> nhiên, rồi một mô hình mạnh hơn tên là LSTM. Mỗi mô hình đều được đem ra thử trên webcam, và mỗi
> lần thử lại lộ ra một vấn đề mà điểm số trên giấy không cho thấy. Không cần biết trước về học
> máy: khái niệm nào cần, tôi sẽ giải thích ngay khi gặp.

---

## Slide 2 — Bài toán: năm lớp cần nhận · ⏱ 1:00

**Trên slide**

| Lớp | Cử chỉ | Lệnh muốn phát |
|---|---|---|
| `swipe_left` | Hất tay sang trái | Slide trước |
| `swipe_right` | Hất tay sang phải | Slide sau |
| `zoom_in` | Mở ngón cái và ngón trỏ ra | Phóng to |
| `zoom_out` | Chụm ngón cái và ngón trỏ lại | Thu nhỏ |
| `none` | Mọi thứ khác: tay nghỉ, gõ phím, chỉ trỏ, gãi đầu… | Không làm gì |

- `none` là lớp khó nhất: gồm **mọi** chuyển động khác, và chiếm phần lớn thời gian
- Hình gợi ý: đoạn mẫu bốn cử chỉ (Phụ lục C)

**Lời thoại**

> Mục tiêu của đề tài: dùng webcam laptop nhận ra bốn cử chỉ để điều khiển máy tính. Hất tay sang
> trái là về slide trước, hất sang phải là sang slide sau. Mở ngón cái và ngón trỏ ra là phóng to,
> chụm lại là thu nhỏ, như trên điện thoại.
>
> Còn một lớp thứ năm, gọi là `none`: mọi thứ khác, như tay nghỉ, gõ phím, chỉ trỏ, gãi đầu. Đây là
> lớp khó nhất, vì nó gồm mọi chuyển động không phải bốn cử chỉ kia, và phần lớn thời gian ta không
> làm cử chỉ nào. Một hệ thống tự chuyển slide khi bạn chỉ đang gãi đầu thì không ai dùng được.

---

## Slide 3 — Hệ thống "nhìn" bàn tay thế nào · ⏱ 1:15

**Trên slide**

- Hình (cần tự vẽ, hoặc cắt từ đoạn mẫu): bàn tay với 21 điểm nối thành hình que
- MediaPipe (công cụ có sẵn của Google) → **21 điểm mốc** mỗi khung hình: cổ tay, các khớp, đầu
  năm ngón
- **Cửa sổ 1,2 giây** = 18 thời điểm. Cứ 0,2 giây hỏi một lần: "trong 1,2 giây vừa rồi có cử chỉ
  nào không?" → 5 câu trả lời mỗi giây
- Mỗi cửa sổ tóm tắt thành **15 con số** (đặc trưng), ví dụ:
  - cổ tay dời ngang bao xa, nhanh nhất bao nhiêu
  - khoảng cách đầu ngón cái – đầu ngón trỏ thay đổi bao nhiêu
  - bàn tay xòe ra hay khép lại bao nhiêu
- Đơn vị đo: **"lòng bàn tay"** (cổ tay → gốc ngón giữa) → tay gần hay xa camera đều đo như nhau

**Lời thoại**

> Hệ thống không xử lý trực tiếp từng điểm ảnh của camera. Một công cụ có sẵn của Google tên là
> MediaPipe tìm bàn tay trong mỗi khung hình, rồi trả về 21 điểm mốc: cổ tay, các khớp và đầu năm
> ngón. Từ đây trở đi, với hệ thống, bàn tay chỉ còn là 21 điểm chuyển động theo thời gian, giống
> một hình que đang cử động.
>
> Một cử chỉ là một chuyển động, nên không thể nhận ra từ một khung hình. Hệ thống xét từng cửa sổ
> dài 1,2 giây. Cứ mỗi 0,2 giây, nó lấy 1,2 giây gần nhất và hỏi: trong đoạn này có cử chỉ nào
> không? Tức là mỗi giây có năm câu trả lời.
>
> Với mô hình luật và rừng ngẫu nhiên, mỗi cửa sổ còn được tóm tắt thành 15 con số, gọi là đặc
> trưng: cổ tay đi ngang bao xa, khoảng cách đầu ngón cái tới đầu ngón trỏ thay đổi bao nhiêu, bàn
> tay xòe ra hay khép lại bao nhiêu… Mọi khoảng cách đo bằng đơn vị "lòng bàn tay", tức từ cổ tay
> tới gốc ngón giữa, nên tay gần hay xa camera đều đo như nhau.

---

## Slide 4 — Từ luật do người viết đến học từ ví dụ · ⏱ 1:00

**Trên slide**

- Điểm xuất phát (Phase 5): **luật do người viết**
  - "cổ tay đi ngang đủ nhanh, đủ xa → vuốt; cái–trỏ mở ra đủ nhiều → zoom in"
  - chạy được nhưng yếu: gần **một nửa** số lúc không có cử chỉ bị báo nhầm thành cử chỉ
- **Học máy:** cho máy xem rất nhiều ví dụ có đáp án, để máy **tự tìm ra quy luật**
  - thứ máy tìm ra = **mô hình**: nhận một cửa sổ, trả một lớp kèm **độ tin** (0 → 1)
  - quá trình cho máy xem ví dụ = **huấn luyện**
- Ví dụ có đáp án: bộ dữ liệu công khai **IPN Hand**
  - 200 video, 50 người, 14 loại động tác đã gán sẵn
  - 4 loại → bốn cử chỉ; 10 loại còn lại (có cả chỉ trỏ bằng một ngón, hai ngón) → `none`

**Lời thoại**

> Trước Phase 6, hệ thống đã chạy được bằng luật do người viết, kiểu "cổ tay đi ngang đủ nhanh và
> đủ xa thì là vuốt". Nó chạy được nhưng rất yếu: gần một nửa số lúc không có cử chỉ bị báo nhầm
> thành cử chỉ.
>
> Học máy làm ngược lại: thay vì người viết luật, ta cho máy xem rất nhiều ví dụ có đáp án và để máy
> tự tìm ra quy luật. Thứ máy tìm ra gọi là mô hình: đưa vào một cửa sổ mới, nó trả ra một lớp, kèm
> độ tin từ 0 đến 1. Quá trình cho máy xem ví dụ gọi là huấn luyện.
>
> Ví dụ có đáp án lấy từ bộ dữ liệu công khai IPN Hand: 200 video của 50 người, mỗi đoạn đã gán sẵn
> tên động tác. Bốn loại thành bốn cử chỉ của tôi; mười loại còn lại, trong đó có chỉ trỏ bằng một
> ngón và hai ngón, gộp vào `none`. Hai kiểu chỉ trỏ này sẽ còn được nhắc nhiều.

---

## Slide 5 — Bài tập về nhà, đề thi thử, đề thi thật · ⏱ 1:00

**Trên slide**

| Tập dữ liệu | Ví như | Số người | Dùng để |
|---|---|---|---|
| Huấn luyện (*train*) | Bài tập về nhà | 30 | Máy học từ đây |
| Kiểm định (*val*) | Đề thi thử | 7 | Chấm điểm, chọn cách làm |
| Kiểm tra (*test*) | Đề thi thật, **niêm phong** | 13 | Mở đúng một lần, ở cuối dự án |

- **Chia theo người:** mô hình phải đúng với người nó chưa từng thấy
- **Khoá kỹ thuật:** script từ chối mở đề thi thật nếu không ghi rõ "lần cuối"; mỗi lần mở để lại một
  dòng nhật ký → **đến nay chưa mở lần nào**
- Đề thi thử giữ tỉ lệ ngoài đời: 11 038 cửa sổ, **96,5%** là `none`, mỗi cử chỉ chỉ khoảng **100**
  cửa sổ

**Lời thoại**

> Dữ liệu được chia làm ba phần, giống việc học ở trường. Tập huấn luyện là bài tập về nhà: máy học
> từ đây. Tập kiểm định là đề thi thử: dùng để chấm điểm trong lúc phát triển. Tập kiểm tra là đề
> thi thật, được niêm phong, chỉ mở đúng một lần ở cuối dự án; nhìn đề thật rồi sửa cho hợp đề thì
> điểm sẽ đẹp giả. Dự án có một cái khoá kỹ thuật cho việc này, và đến nay đề thi thật chưa bị mở lần
> nào.
>
> Dữ liệu chia theo người: nếu cùng một người có mặt ở cả bài tập lẫn đề thi, máy có thể "nhận ra
> người quen" thay vì nhận ra cử chỉ. Đề thi thử giữ đúng tỉ lệ ngoài đời: 96,5% số cửa sổ là không
> có cử chỉ, mỗi cử chỉ chỉ khoảng 100 cửa sổ. Con số 100 này sẽ quan trọng ở phần sau.

---

## Slide 6 — Đo mô hình tốt tới đâu · ⏱ 1:45

**Trên slide**

- Như một **chuông báo cháy**:
  - **Tỉ lệ bắt được** (*recall*): trong các đám cháy thật, chuông kêu được bao nhiêu phần?
  - **Tỉ lệ báo đúng** (*precision*): trong các lần chuông kêu, bao nhiêu lần là cháy thật?
- Ví dụ thật: vuốt trái, rừng ngẫu nhiên, đề thi thử
  - 104 cửa sổ vuốt trái thật, bắt được 56 → **bắt được 54%**
  - mô hình nói "vuốt trái" 424 lần, chỉ 56 lần đúng (366 lần là `none`) → **báo đúng 13%**
- **F1**: gộp hai tỉ lệ, chỉ cao khi **cả hai** cao (ví dụ trên: 0,21) · **macro-F1**: trung bình F1
  của năm lớp → điểm chính để so mô hình
- **Đường cơ sở**: luôn đoán `none` 0,196 · đoán ngẫu nhiên 0,080
- **Theo cử chỉ**: bắt được nếu **ít nhất một** cửa sổ của cử chỉ được nhận đúng
- **Cụm báo nhầm**: chuỗi câu trả lời nhầm liền nhau ≈ một lần hệ thống *sẽ* phát lệnh sai

**Lời thoại**

> Để biết mô hình tốt tới đâu, hãy nghĩ tới một chuông báo cháy. Trong các đám cháy thật, chuông kêu
> được bao nhiêu phần: đó là tỉ lệ bắt được. Trong các lần chuông kêu, bao nhiêu lần là cháy thật: đó
> là tỉ lệ báo đúng. Chuông lúc nào cũng kêu thì bắt được hết nhưng gần như không bao giờ báo đúng;
> chuông không bao giờ kêu thì vô dụng. Cần cả hai.
>
> Ví dụ thật, với vuốt trái và rừng ngẫu nhiên. Đề thi thử có 104 cửa sổ vuốt trái, mô hình bắt được
> 56, tức 54%. Nhưng nó nói "vuốt trái" tổng cộng 424 lần mà chỉ đúng 56 lần; 366 lần là lúc không có
> cử chỉ nào. Tỉ lệ báo đúng chỉ 13%.
>
> Điểm F1 gộp hai tỉ lệ này thành một số từ 0 đến 1, chỉ cao khi cả hai cùng cao; ví dụ trên có F1 là
> 0,21. Macro-F1 là trung bình F1 của năm lớp, và là điểm chính để so các mô hình. Tôi không dùng tỉ
> lệ đoán đúng thông thường, vì một mô hình lười lúc nào cũng đoán "không có cử chỉ" đã đúng 96,5%.
> Mô hình lười đó chỉ được macro-F1 0,196, đoán ngẫu nhiên được 0,08: đó là hai mốc để so.
>
> Thêm hai cách đếm gần với trải nghiệm thật. Đếm theo cử chỉ: bạn vuốt một lần, máy chỉ cần nhận ra
> một lần. Và cụm báo nhầm: một chuỗi câu trả lời nhầm liền nhau, tương đương một lần hệ thống sẽ tự
> ý chuyển slide.

---

## Slide 7 — Rừng ngẫu nhiên: cách hoạt động và kết quả · ⏱ 1:45

**Trên slide**

- **Cây quyết định** = trò "20 câu hỏi": máy tự chọn chuỗi câu hỏi có/không về 15 con số
  ("khoảng cái–trỏ có đổi hơn 1,2 lòng bàn tay không?" → "tăng hay giảm?" → …)
- **Rừng ngẫu nhiên** = 300 cây, mỗi cây học từ một phần ví dụ rút ngẫu nhiên → **cùng biểu quyết**
- Coi trọng các lớp cử chỉ hơn cho cân bằng · huấn luyện trên 3 326 cửa sổ: **1,6 giây**

| Trên đề thi thử | macro-F1 | Bắt được (bốn cử chỉ) | Báo đúng (bốn cử chỉ) |
|---|---|---|---|
| Luôn đoán `none` | 0,196 | 0% | — |
| Luật (Phase 5) | 0,231 | 44–62% | 2–10% |
| **Rừng ngẫu nhiên** | **0,436** | 49–63% | 13–35% |

- Báo nhầm: **877** cửa sổ `none` (8,2%) bị báo thành cử chỉ, gấp hơn hai lần toàn bộ **388** cửa sổ
  cử chỉ thật của đề
- Theo cử chỉ: vuốt trái 70% · vuốt phải 70% · zoom in 59% · zoom out 56%
- Nhầm nhiều nhất: **tay đang chỉ trỏ** và **tay không làm cử chỉ**, thường thành **vuốt**
- Hình: ma trận nhầm lẫn (hàng = lớp thật, cột = lớp đoán)

**Lời thoại**

> Mô hình học máy đầu tiên là rừng ngẫu nhiên. Hãy nghĩ tới trò chơi "20 câu hỏi": một cây quyết
> định là một chuỗi câu hỏi có hoặc không về 15 con số, ví dụ "khoảng cách cái–trỏ có thay đổi hơn
> 1,2 lòng bàn tay không?", rồi "nó tăng hay giảm?", cho tới khi trả lời được "đây là zoom in". Câu
> hỏi và ngưỡng do máy tự chọn. Một cây đơn lẻ dễ học tủ, nên rừng ngẫu nhiên trồng 300 cây, mỗi cây
> học từ một phần ví dụ rút ngẫu nhiên, rồi cả 300 cây cùng biểu quyết. Huấn luyện cả rừng chỉ mất
> 1,6 giây.
>
> Kết quả: macro-F1 0,436, gần gấp đôi mô hình luật. Điểm yếu là báo nhầm: 877 cửa sổ không có cử chỉ
> bị báo thành cử chỉ, gấp hơn hai lần toàn bộ 388 cửa sổ cử chỉ thật của đề. Đếm theo cử chỉ thì 70%
> cú vuốt được nhận ra ít nhất một lần.
>
> Hình bên là ma trận nhầm lẫn: hàng là lớp thật, cột là lớp mô hình đoán. Ô "thật là `none`, đoán
> là vuốt trái" chính là con số 366 vừa rồi. Phần lớn báo nhầm đến từ tay đang chỉ trỏ và tay không
> làm cử chỉ, và thường thành vuốt: khi chỉ trỏ, người ta cũng di tay nhanh và xa, có khi còn nhanh
> hơn một cú vuốt.

---

## Slide 8 — Mô hình dựa vào con số nào · ⏱ 1:00

**Trên slide**

- **Độ quan trọng của đặc trưng:** xáo trộn một trong 15 cột trên đề thi thử, xem điểm tụt bao nhiêu
- Ba con số quan trọng nhất:
  - khoảng cái–trỏ có thay đổi nhiều không
  - cái–trỏ mở ra hay chụm lại
  - cổ tay đi ngang nhanh nhất bao nhiêu
- Bất ngờ: "cổ tay dời ngang bao xa", dự đoán là top 3, chỉ đứng **thứ 13**
  - vì có **"người sinh đôi"**: vận tốc ngang trung bình (tương quan 0,97)
  - xáo **cả cặp**: điểm tụt ngang "cổ tay đi nhanh nhất"; cửa sổ vuốt bị đoán **ngược hướng**
    8 → khoảng 43
  - → thông tin "vuốt về bên nào" nằm ở cặp này
- Hình: độ quan trọng đặc trưng

**Lời thoại**

> Muốn biết mô hình dựa vào con số nào, có một cách rất trực quan: xáo trộn một cột trong 15 cột trên
> đề thi thử, rồi xem điểm tụt bao nhiêu. Tụt nhiều thì mô hình dựa nhiều vào con số đó.
>
> Ba con số quan trọng nhất là hai con số về động tác cái–trỏ, và tốc độ đi ngang lớn nhất của cổ
> tay. Điều bất ngờ: con số "cổ tay dời ngang bao xa", mà tôi đoán sẽ vào top ba, chỉ đứng thứ 13. Lý
> do là nó có một "người sinh đôi", vận tốc ngang trung bình: hai con số gần như luôn tăng giảm cùng
> nhau. Xáo một mình nó thì mô hình vẫn dùng được người sinh đôi, nên điểm không tụt. Xáo cả cặp thì
> điểm tụt ngang con số quan trọng thứ ba, và số cửa sổ vuốt bị đoán ngược hướng tăng từ 8 lên khoảng
> 43. Vậy thông tin "vuốt về bên nào" nằm ở cặp này.

---

## Slide 9 — Thử trực tiếp lần 1: vì sao vuốt kém · ⏱ 2:00

**Trên slide**

- Webcam, rừng ngẫu nhiên: **zoom khá tốt, vuốt kém**
  - vuốt chậm, đi xa → được nhận
  - vuốt nhanh rồi kéo tay về ngay → `none` (sau 1,2 giây cổ tay gần như về chỗ cũ)
- Trên IPN, vuốt **không** kém zoom (70% so với 56–59%) → **lệch miền**: tôi vuốt khác người diễn IPN
- **Thí nghiệm "đổi đúng một thứ"** (phản thực tế): lấy cú vuốt thật của IPN mà mô hình đang nhận
  đúng → sửa đúng một khía cạnh → cộng độ rung như tay thật → còn được nhận không?

| Sửa đổi | Còn được nhận (trái / phải) |
|---|---|
| Không sửa | 100% / 92% |
| **Bàn tay giữ nguyên dáng**, cổ tay vẫn đi y như cũ | **0% / 0%** |
| Đi ra rồi quay về ngay | 45% / 37% |
| Cổ tay chỉ đi nửa quãng đường | 48% / 47% |

- Với rừng, "vuốt" = cú **hất** của IPN: cổ tay đi ngang đủ nhanh, đủ xa rồi **dừng ở đó**, **và** bàn
  tay **mở ra trong lúc hất**
- Hình gợi ý (cần tự vẽ): cú vuốt gốc đặt cạnh bản "giữ nguyên dáng" và bản "đi ra rồi quay về"

**Lời thoại**

> Tôi chạy demo bằng rừng ngẫu nhiên trên webcam. Zoom được nhận khá tốt, nhưng vuốt thì kém. Log cho
> thấy: cú vuốt chậm, đi xa thì được nhận; cú vuốt nhanh rồi kéo tay về ngay thì bị coi là không có
> cử chỉ, vì sau 1,2 giây cổ tay gần như về chỗ cũ.
>
> Trên dữ liệu IPN, vuốt không hề kém zoom. Vậy vấn đề nằm ở chỗ tôi làm khác người diễn IPN. Hiện
> tượng này gọi là lệch miền: giống người học lái xe ở một thành phố, sang thành phố khác có biển báo
> khác thì lúng túng.
>
> Để biết mô hình thật sự coi cái gì là một cú vuốt, tôi làm thí nghiệm "đổi đúng một thứ". Muốn biết
> một người nhận ra bạn qua giọng nói hay khuôn mặt, ta đổi đúng một thứ rồi xem họ còn nhận ra không.
> Ở đây cũng vậy: lấy cú vuốt thật của IPN mà mô hình đang nhận đúng, sửa đúng một khía cạnh, cộng chút
> độ rung như tay thật, rồi xem còn được nhận không.
>
> Giữ nguyên đường đi của cổ tay, chỉ bắt bàn tay giữ nguyên dáng: không cú nào được nhận. Đi ra rồi
> quay về, hay chỉ đi nửa quãng: mất hơn một nửa. Vậy với rừng, "vuốt" là cú hất của người diễn IPN:
> cổ tay đi ngang đủ nhanh, đủ xa rồi dừng ở đó, và bàn tay mở ra trong lúc hất. Sự mở tay giúp nó
> phân biệt cú hất với tay chỉ trỏ, vì tay chỉ trỏ di chuyển mà không đổi dáng.

---

## Slide 10 — Hai cách sửa · ⏱ 1:30

**Trên slide**

- **Cách 1, sửa cách làm của người:** chế độ luyện tập hiện thêm độ mở bàn tay, xanh nếu giống người
  diễn IPN, đỏ nếu khác
  - phiên thử sau (1 phút): 43 cửa sổ có chuyển động kiểu vuốt · **88%** đã mở tay đúng kiểu IPN ·
    rừng nhận **79%** là vuốt
- **Cách 2, sửa mô hình:** **tăng cường dữ liệu** = tạo thêm ví dụ bằng biến đổi không làm đổi đáp án
  (xoay nhẹ, lật ngang, nhanh chậm, rung)
  - ý tưởng: giữ đường đi cổ tay, "làm cứng" bàn tay, vẫn dạy là "vuốt"
  - bản cứng hoàn toàn là giả tạo: độ mở bàn tay 0,06, trong khi tay chỉ trỏ thật vẫn dao động 0,2–0,8
  - bản thực tế hơn: cú vuốt chỉ đổi dáng một nửa được nhận 10% → 38–56%; **giá**: báo nhầm tăng
    1,5–2,6 lần
  - → nằm trong code, **đang tắt**

**Lời thoại**

> Có hai cách sửa: sửa cách làm của người, hoặc sửa mô hình.
>
> Cách thứ nhất: demo có sẵn một chế độ luyện tập, hiện vài con số của cửa sổ vừa rồi, tô xanh nếu
> giống người diễn IPN, đỏ nếu khác. Tôi thêm con số cho biết bàn tay có mở ra trong lúc làm cử chỉ
> không. Ở phiên thử sau, trong 43 cửa sổ có chuyển động kiểu vuốt, 88% tôi đã mở tay đúng kiểu IPN,
> và rừng nhận 79% là vuốt.
>
> Cách thứ hai là tăng cường dữ liệu: tạo thêm ví dụ bằng cách biến đổi ví dụ có sẵn mà không đổi đáp
> án, như cho học sinh xem một bài toán viết theo nhiều cách. Ở đây là giữ đường đi của cổ tay nhưng
> "làm cứng" bàn tay, rồi vẫn dạy là vuốt. Bản cứng hoàn toàn hoá ra giả tạo, vì tay thật đang di
> chuyển không bao giờ cứng hẳn. Bản thực tế hơn thì có giúp: cú vuốt chỉ đổi dáng một nửa được nhận
> từ 10% lên 38 đến 56%. Nhưng báo nhầm tăng 1,5 đến 2,6 lần, vì tay chỉ trỏ giờ cũng bị coi là vuốt.
> Cách này vẫn nằm trong code nhưng đang tắt; đánh đổi bao nhiêu là quyết định còn để ngỏ.

---

## Slide 11 — Mạng nơ-ron, LSTM và cách dạy · ⏱ 1:45

**Trên slide**

- Rừng ngẫu nhiên chỉ thấy **15 con số tóm tắt do người chọn**
- **Mạng nơ-ron:** một công thức rất lớn với nhiều **"núm vặn"** (trọng số). LSTM của dự án có khoảng
  **220 nghìn** núm; huấn luyện = vặn dần từng núm cho đoán sai ít đi
- **LSTM:** đọc lần lượt 18 thời điểm, mỗi thời điểm đủ 21 điểm (42 con số), vừa đọc vừa **ghi nhớ**
  - đọc **một chiều**: không bao giờ "nhìn trước" tương lai
- Cách dạy:
  - **epoch** = một lượt xem hết bài tập về nhà · **loss** = mức sai
  - mỗi epoch, một **bản biến đổi mới** của mỗi ví dụ → không thể thuộc lòng
  - lỗi trên cử chỉ tính nặng gấp khoảng **4 lần** lỗi trên `none`
  - mất dấu tay → giữ vị trí cuối cùng còn thấy
  - CPU thường: huấn luyện 13–25 phút; mỗi câu trả lời khi chạy demo ≈ **1 mili-giây**

**Lời thoại**

> Rừng ngẫu nhiên chỉ thấy 15 con số tóm tắt do người chọn; nếu thứ quyết định một cử chỉ không nằm
> trong đó, nó chịu. Phase 7 dùng một mô hình xem được toàn bộ chuyển động.
>
> Mạng nơ-ron là một công thức rất lớn với nhiều "núm vặn"; LSTM của dự án có khoảng 220 nghìn núm.
> Lúc đầu các núm ở vị trí ngẫu nhiên và công thức đoán bừa. Huấn luyện là vặn dần từng núm cho số lần
> đoán sai giảm xuống. Không ai chỉ định núm nào làm gì; mạng tự tìm ra dấu hiệu có ích.
>
> LSTM là loại mạng chuyên đọc chuỗi theo thời gian. Nó đọc lần lượt 18 thời điểm của cửa sổ, mỗi thời
> điểm đủ 21 điểm của bàn tay, vừa đọc vừa ghi nhớ, như ta đọc một câu từng chữ mà vẫn nhớ đầu câu. Nó
> chỉ đọc một chiều, từ quá khứ tới hiện tại, vì khi chạy thật thì tương lai chưa xảy ra.
>
> Mỗi lượt xem hết bài tập về nhà gọi là một epoch, và mức sai gọi là loss. Mỗi epoch, mạng thấy một
> bản biến đổi mới của mỗi ví dụ, nên không thể thuộc lòng. Lỗi trên cử chỉ được tính nặng gấp khoảng
> bốn lần lỗi trên `none`, vì cử chỉ hiếm hơn. Tất cả chạy trên CPU thường: huấn luyện mất 13 đến 25
> phút, và mỗi câu trả lời khi chạy demo mất khoảng 1 mili-giây.

---

## Slide 12 — LSTM: kết quả · ⏱ 0:45

**Trên slide**

| | Rừng ngẫu nhiên | **LSTM** |
|---|---|---|
| macro-F1 (đề thi thử) | 0,436 | **0,556** |
| Vuốt trái: bắt được / báo đúng | 54% / 13% | **89% / 26%** |
| Theo cử chỉ: vuốt trái / phải | 70% / 70% | **93% / 85%** |
| Theo cử chỉ: zoom in / out | 59% / 56% | **89% / 80%** |
| Cửa sổ `none` bị báo nhầm | 8,2% | **5,8%** |
| Cụm báo nhầm mỗi phút không cử chỉ | 14,8 | **8,6** |
| Báo nhầm khi chỉ trỏ (một / hai ngón) | 5,8% / 9,7% | **3,5% / 5,9%** |

- Ngoại lệ: tay nghỉ không làm cử chỉ, LSTM không khá hơn (14,5% so với 10,6%)

**Lời thoại**

> LSTM tốt hơn rừng ở gần như mọi mặt: macro-F1 tăng từ 0,436 lên 0,556. Lấy lại ví dụ vuốt trái:
> bắt được tăng từ 54 lên 89%, báo đúng tăng gấp đôi, từ 13 lên 26%. Đếm theo cử chỉ, 93% cú vuốt
> trái và 89% cú zoom in được nhận ra ít nhất một lần. Báo nhầm khi chỉ trỏ giảm khoảng một nửa. Riêng
> với tay nghỉ không làm cử chỉ thì LSTM không khá hơn rừng.

---

## Slide 13 — Học thuộc lòng, và con số đáng tin tới đâu · ⏱ 1:45

**Trên slide**

- **Quá khớp** = học thuộc lòng: mức sai trên bài tập về nhà vẫn giảm, trên đề thi thử thì thôi giảm
  hoặc tăng lên
- Hai đường học đặt cạnh nhau:
  - **mô hình chính:** mức sai trên đề thi thử giảm nhanh ~20 epoch đầu rồi đứng yên, **không quay
    đầu tăng**
  - **bản không tăng cường:** thấp nhất ở **epoch 38**, rồi tăng dần khoảng 30% → điểm bắt đầu quá
    khớp
- Điểm thi thử **dao động ±0,04** giữa hai epoch liền nhau (mỗi cử chỉ chỉ ~100 cửa sổ)
- **Lạc quan do chọn lọc:** lần dạy đầu báo epoch có điểm cao nhất, **0,601**, một đỉnh may mắn
- Cách làm hiện tại: chọn theo **trung bình 10 epoch liền nhau** → **0,556**, mức thường đạt
  khoảng **0,53**
  - còn sửa một lỗi thật: hai lần dạy trước dừng quá sớm (epoch 40 và 48) vì đỉnh may mắn đến sớm
- Con số không thiên lệch: dạy lại với 5 cách xáo dữ liệu (Phase 8), và lần mở đề thi thật duy nhất

**Lời thoại**

> Một nguy cơ của mạng nơ-ron là học thuộc lòng, gọi là quá khớp: như học sinh thuộc đáp án bài tập
> về nhà, gặp đề mới thì kém. Dấu hiệu là mức sai trên bài tập tiếp tục giảm, còn trên đề thi thử thì
> thôi giảm hoặc tăng lên.
>
> Hình trái là mô hình chính: mức sai trên đề thi thử giảm nhanh trong khoảng 20 epoch đầu rồi đứng
> yên, không quay đầu tăng; ví dụ biến đổi mới mỗi epoch đã ngăn mạng học thuộc lòng. Hình phải là bản
> không biến đổi, chạy riêng để thấy rõ: mức sai thấp nhất ở epoch 38, rồi tăng dần khoảng 30%. Đó là
> điểm bắt đầu quá khớp.
>
> Con số 0,556 có đáng tin không? Mỗi cử chỉ trong đề thi thử chỉ khoảng 100 cửa sổ, nên giữa hai
> epoch liền nhau, macro-F1 dao động khoảng 0,04 dù mạng gần như không đổi. Lần dạy đầu chọn đúng epoch
> có điểm cao nhất và báo 0,601, giống thi thử 100 lần rồi chỉ khoe điểm cao nhất: một phần là do may.
> Giờ tôi chọn theo trung bình 10 epoch liền nhau: 0,556, mức thường đạt khoảng 0,53, thấp hơn nhưng
> trung thực hơn. Cách chọn này còn sửa một lỗi thật: hai lần dạy trước bị dừng quá sớm, chỉ vì một
> đỉnh may mắn đến sớm.

---

## Slide 14 — LSTM nhìn cú vuốt khác rừng · ⏱ 0:45

**Trên slide**

| Sửa đổi (cú vuốt trái / phải) | Rừng ngẫu nhiên | LSTM |
|---|---|---|
| Bàn tay giữ nguyên dáng | 0% / 0% | 8% / 0% |
| Đi ra rồi quay về ngay | 45% / 37% | **96% / 99%** |
| Cổ tay chỉ đi một phần tư quãng | 4% / 0% | **100% / 94%** |
| Cổ tay đứng yên, chỉ các ngón chuyển động | 0% / 0% | **100% / 87%** |

- LSTM nhận vuốt từ **động tác của các ngón** (chụm lại rồi mở ra, ngón chỉ về một bên), không từ
  quãng đường cổ tay đi
- Chịu được kiểu "hất rồi kéo về", nhưng vẫn đòi bàn tay mở ra

**Lời thoại**

> Lặp lại đúng các thí nghiệm "đổi một thứ" với LSTM cho một bức tranh khác hẳn. LSTM vẫn nhận cú vuốt
> khi tay hất ra rồi kéo về, khi cổ tay chỉ đi một phần tư quãng, thậm chí khi cổ tay đứng yên. Nó nhận
> vuốt từ động tác của các ngón: chụm lại rồi mở ra, ngón chỉ về một bên. Nhưng nó vẫn đòi bàn tay phải
> mở ra. Đúng như vậy, trên webcam, vuốt với LSTM tốt hơn hẳn. Nhưng zoom lại kém đi.

---

## Slide 15 — Thử trực tiếp lần 2: zoom kém đi · ⏱ 1:45

**Trên slide**

- Triệu chứng (log webcam, LSTM):
  - tôi zoom, cái–trỏ mở ra chụm lại rất rõ, **còn mạnh hơn** người diễn IPN → LSTM vẫn trả "không
    có cử chỉ", độ tin gần tuyệt đối
  - tay **đứng yên** → LSTM báo `zoom_out` liên tục gần 2 giây
- **Loại trừ lỗi đường ống:** cho chính chương trình demo chạy trên video IPN có cú zoom → nhận đúng
  cả hai, độ tin 0,88–1,00 → phần mềm ổn
- Thí nghiệm "đổi một thứ" trên cú zoom thật: giữ cổ tay, ngón cái, ngón trỏ; chỉ đổi các ngón còn lại

| Sửa đổi (zoom in / zoom out) | Rừng ngẫu nhiên | LSTM |
|---|---|---|
| Không sửa | 93% / 98% | 100% / 100% |
| **Ngón nhẫn và ngón út duỗi thẳng** | 63% / 85% | **10% / 35%** |
| Chỉ còn ngón cái và trỏ cử động (zoom hai ngón) | 52% / 54% | **7% / 38%** |
| **Bàn tay đứng yên** ở dáng cái–trỏ đang mở | 0% báo zoom | **46–62% vẫn báo zoom** |

- Hai nguyên nhân:
  1. LSTM học **"kiểu zoom của người diễn IPN"** (ba ngón, nhẫn và út **luôn gập**), không học "zoom
     là gì"
  2. LSTM đoán zoom từ **dáng tay đứng yên**

**Lời thoại**

> Lần thử thứ hai, với LSTM. Lúc tôi zoom, khoảng cách cái–trỏ mở ra, chụm lại rất rõ, còn mạnh hơn
> người diễn IPN, vậy mà LSTM trả "không có cử chỉ" với độ tin gần như tuyệt đối. Còn lúc tay tôi đứng
> yên, nó lại báo zoom out liên tục gần hai giây.
>
> Trước khi đổ cho chuyện tôi làm khác IPN, phải chắc phần mềm không có lỗi. Tôi cho chính chương trình
> demo chạy trên một video IPN có cú zoom đã biết. Demo nhận đúng cả hai cú zoom, độ tin 0,88 đến 1.
> Vậy phần mềm ổn.
>
> Lại làm thí nghiệm "đổi một thứ", lần này trên cú zoom thật của IPN: giữ nguyên cổ tay, ngón cái,
> ngón trỏ, chỉ đổi các ngón còn lại. Chỉ cần ngón nhẫn và út duỗi thẳng, điều rất tự nhiên khi zoom,
> LSTM chỉ còn nhận 10% cú zoom in; rừng vẫn nhận 63%. Và khi bàn tay đứng yên ở dáng cái–trỏ đang mở,
> LSTM vẫn báo zoom khoảng một nửa số lần; rừng thì không bao giờ.
>
> Hai nguyên nhân. Một: LSTM học "kiểu zoom của người diễn IPN", ba ngón, nhẫn và út luôn gập, chứ
> không học "zoom là gì". Hai: nó coi dáng tay cái–trỏ đang mở là dấu hiệu của zoom, dù không có
> chuyển động nào; đó chính là chuỗi báo nhầm lúc tay tôi đứng yên. Rừng ít bị ảnh hưởng, vì nó nhìn
> chủ yếu khoảng cách cái–trỏ thay đổi, đúng bản chất của zoom.

---

## Slide 16 — Thử sửa ngay trong LSTM, và vì sao không dùng · ⏱ 1:00

**Trên slide**

- Dạy lại bằng hai kiểu ví dụ biến đổi mới:
  - cú zoom với ngón giữa, nhẫn, út **"của người khác"** (dáng tay thật lấy từ hơn 58 nghìn dáng tay
    trong IPN), giữ yên → "zoom là động tác cái–trỏ; ngón khác làm gì cũng được"
  - bàn tay đứng yên, đáp án "không có cử chỉ" → "không có chuyển động thì không có cử chỉ"
- **Lợi:** nhận zoom ở mọi kiểu ngón (88–98%); hết báo zoom khi tay đứng yên
- **Giá rất đắt:**
  - cửa sổ không cử chỉ bị báo nhầm thành `zoom_out`: **52 → 528** (gấp 10 lần)
  - báo nhầm khi chỉ trỏ: 3,5% / 5,9% → **12,0% / 10,2%**
  - báo đúng của `zoom_out`: 46% → **10%**
- **Vì sao:** khi chỉ trỏ, ngón cái cũng hay nhích lại gần ngón trỏ → chính "kiểu ngón riêng" của IPN
  giúp tách zoom khỏi chỉ trỏ
- → nằm trong code, **đang tắt**

**Lời thoại**

> Cách sửa tự nhiên là dạy lại LSTM bằng hai kiểu ví dụ mới. Một: cú zoom mà ngón giữa, nhẫn, út được
> thay bằng dáng tay thật của người khác, lấy từ hơn 58 nghìn dáng tay trong IPN, với thông điệp "zoom
> là động tác cái–trỏ, ngón khác làm gì cũng được". Hai: bàn tay đứng yên, đáp án "không có cử chỉ".
>
> Lợi đúng như mong đợi: nhận zoom ở mọi kiểu ngón, hết báo zoom khi tay đứng yên. Nhưng số cửa sổ
> không cử chỉ bị báo nhầm thành zoom out tăng từ 52 lên 528, gấp mười lần. Lý do: khi chỉ trỏ, ngón
> cái cũng hay nhích lại gần ngón trỏ, và chính kiểu ngón riêng của IPN là thứ giúp LSTM phân biệt zoom
> với chỉ trỏ. Xoá nó đi là xoá luôn khả năng phân biệt. Cách sửa này vẫn nằm trong code, nhưng đang
> tắt.

---

## Slide 17 — Lời giải: mô hình ghép · ⏱ 1:15

**Trên slide**

- **Hai chuyên gia,** mỗi người lo đúng việc mình giỏi (sơ đồ cần tự vẽ):
  - **LSTM lo vuốt:** nhận qua động tác ngón tay, chịu được kiểu "hất rồi kéo về"
  - **Rừng ngẫu nhiên lo zoom:** nhận qua khoảng cách cái–trỏ, ít phụ thuộc ngón khác, không báo zoom
    khi tay đứng yên
- Luật ghép: LSTM nói "vuốt" → vuốt; nếu không, rừng nói "zoom" → zoom; còn lại → không có cử chỉ
- Trên đề thi thử: macro-F1 **0,506**, hơn rừng (0,436), kém LSTM (0,556)
- Trên chính bàn tay tôi (phát lại một phiên webcam):

| Số lần báo zoom trong 1,1 phút | |
|---|---|
| LSTM đứng một mình | 24 |
| **Mô hình ghép** | **45** |

- Số lần báo vuốt giữ nguyên · **demo dùng mô hình ghép**

**Lời thoại**

> Lời giải là mô hình ghép: thay vì một mô hình làm mọi việc, dùng hai chuyên gia, mỗi người lo đúng
> việc mình giỏi. LSTM lo vuốt, vì nó nhận vuốt qua động tác ngón tay và chịu được kiểu hất rồi kéo
> về. Rừng ngẫu nhiên lo zoom, vì nó nhìn khoảng cách cái–trỏ và không báo zoom khi tay đứng yên. Luật
> ghép rất đơn giản: LSTM nói vuốt thì là vuốt; nếu không, rừng nói zoom thì là zoom; còn lại là không
> có cử chỉ. Cả hai chuyên gia đều đã chạy tốt trên webcam, ở đúng phần việc của mình.
>
> Trên đề thi thử, mô hình ghép được 0,506: hơn rừng, kém LSTM. Điều này hợp lý: người diễn IPN zoom
> đúng kiểu IPN, nên ở đó zoom của LSTM giỏi hơn. Với bàn tay của tôi thì ngược lại. Phát lại một phiên
> webcam của tôi, LSTM chỉ báo zoom 24 lần, mô hình ghép báo 45 lần, còn số lần báo vuốt giữ nguyên.
> Đây là số lần báo, chưa phải độ chính xác. Nhưng đó là lý do demo dùng mô hình ghép.

---

## Slide 18 — "Hộp đen" và tái lập · ⏱ 1:00

**Trên slide**

- **Ghi và phát lại**, như hộp đen máy bay: mỗi lần chạy demo có ghi log, lưu luôn 21 điểm của bàn tay
  ở mọi khung hình → phát lại cả phiên qua **bất kỳ** mô hình nào
  - kiểm chứng: phát lại khớp **316/316** câu trả lời so với lúc chạy thật
- **Tái lập:** cố định "hạt giống" ngẫu nhiên, như xáo bài theo đúng một cách → chạy lại cùng lệnh
  ra **đúng từng chữ số**
  - lần dạy LSTM hiện hành trùng lần trước **từng chữ số suốt 106 epoch**
  - việc kiểm này bắt được vài lỗi "im lặng": một phép biến đổi làm mất khoảnh khắc đầu cửa sổ · một
    bước chạy chậm gấp 3 lần · một thay đổi làm lệch chữ số cuối · một file mô hình lưu xong không mở
    lại được

**Lời thoại**

> Con số 24 và 45 có được nhờ một "hộp đen", giống hộp đen máy bay. Lúc chẩn đoán zoom, log chỉ ghi vài
> con số tóm tắt, nên không kiểm được nguyên nhân trên chính bàn tay tôi. Giờ mỗi lần chạy demo có ghi
> log, chương trình lưu luôn 21 điểm của bàn tay ở mọi khung hình, để phát lại cả phiên qua bất kỳ mô
> hình nào. Phát lại khớp đúng 316 trên 316 câu trả lời so với lúc chạy thật.
>
> Kết quả cũng tái lập được. Dự án cố định "hạt giống" ngẫu nhiên, như xáo bài theo đúng một cách mỗi
> lần, nên chạy lại cùng lệnh cho đúng từng chữ số, suốt 106 epoch. Việc kiểm này còn bắt được vài lỗi
> mà chương trình không hề báo, ví dụ một file mô hình lưu xong nhưng không mở lại được.

---

## Slide 19 — Bốn mô hình đặt cạnh nhau · ⏱ 0:30

**Trên slide**

| Mô hình | Nhìn vào gì | macro-F1 (đề thi thử) | Điểm mạnh | Điểm yếu |
|---|---|---|---|---|
| Luật (Phase 5) | 3 con số, ngưỡng do người đặt | 0,231 | Đơn giản, dễ hiểu | Báo nhầm gần một nửa thời gian |
| Rừng ngẫu nhiên (Phase 6) | 15 con số tóm tắt | 0,436 | Zoom vững với nhiều kiểu tay | Đòi cú vuốt kiểu IPN, nhiều báo nhầm |
| LSTM (Phase 7) | Toàn bộ chuyển động 21 điểm | **0,556** | Vuốt rất tốt, ít báo nhầm hơn | Zoom phụ thuộc kiểu tay của IPN |
| **Ghép** (Phase 7) | Vuốt theo LSTM, zoom theo rừng | 0,506 | Hợp với cách làm cử chỉ của người dùng | Kém LSTM trên dữ liệu IPN |

- Cùng 11 038 cửa sổ của đề thi thử · đề thi thật vẫn niêm phong

**Lời thoại**

> Đặt bốn mô hình cạnh nhau: luật đơn giản nhưng báo nhầm nhiều; rừng vững với zoom nhưng đòi vuốt
> kiểu IPN; LSTM vuốt rất tốt nhưng zoom phụ thuộc kiểu tay IPN; mô hình ghép lấy phần mạnh của hai mô
> hình sau. Mọi con số đo trên cùng một đề thi thử; đề thi thật vẫn niêm phong.

---

## Slide 20 — Demo trực tiếp (tuỳ chọn) · ⏱ 1:30

**Trên slide**

- Mô hình ghép, webcam laptop, chỉ dùng CPU
- Thứ tự: tay để yên → zoom in → zoom out → vuốt trái → vuốt phải → (tuỳ chọn) chỉ trỏ, di tay quanh
  khung

**Lệnh chạy** (không chiếu; bấm `q` hoặc `Esc` để thoát)

```
python scripts/demo.py --model hybrid --show-features
```

Phím 1–4 chọn cử chỉ để so với người diễn IPN: 1 vuốt trái · 2 vuốt phải · 3 zoom in · 4 zoom out.
Nhãn trên màn hình là tên lớp trong code (`none`, `swipe_left`, …); "-" nghĩa là không có cửa sổ hợp
lệ (chưa đủ 1,2 giây, mất tay, hoặc tay nghiêng cạnh).

**Lời thoại** (vừa làm vừa nói)

> Đây là mô hình ghép chạy trực tiếp trên webcam laptop, chỉ dùng CPU.
>
> *(Tay để yên trong khung.)* Tay đứng yên: câu trả lời là `none`, không có cử chỉ.
>
> *(Bấm 3, zoom in; bấm 4, zoom out. Ba ngón cái, trỏ, giữa; nhẫn và út gập.)* Zoom in là mở ba đầu
> ngón đang chụm; zoom out là chụm lại. Các con số chuyển xanh nghĩa là tôi đang làm giống người diễn
> IPN: đây là chế độ luyện tập vừa kể.
>
> *(Bấm 1, vuốt trái; bấm 2, vuốt phải. Chụm đầu ngón, hất ngang, mở bàn tay trong lúc hất, rồi giữ
> tay ở đó.)* Trái và phải ở đây là trái và phải của chính tôi. Hình trên màn hình được lật như gương
> cho dễ nhìn; ảnh đưa vào mô hình thì không lật.
>
> *(Tuỳ chọn: chỉ trỏ, di tay quanh khung.)* Đây là loại chuyển động dễ gây báo nhầm nhất.
>
> Xin lưu ý: mỗi cử chỉ làm câu trả lời sáng lên trong khoảng một giây, vì cứ 0,2 giây lại có một câu
> trả lời mới. Gom chúng thành đúng một lệnh là việc của máy trạng thái ở Phase 9. Hiện hệ thống mới
> hiển thị câu trả lời, chưa phát lệnh thật.

**Nếu có sự cố**

- Một cử chỉ không được nhận: nói "Đây chính là lệch miền vừa kể", bấm phím của cử chỉ đó, chỉ vào
  con số bị đỏ, rồi làm lại.
- Báo nhầm khi chỉ trỏ hay khi để tay yên: "Đây là báo nhầm mà máy trạng thái ở Phase 9 phải xử lý."
- Camera hoặc máy trục trặc: chuyển ngay sang video dự phòng, không sửa tại chỗ.

---

## Slide 21 — Hạn chế và việc tiếp theo · ⏱ 1:30

**Trên slide**

- Hạn chế:
  - **Báo nhầm vẫn cao:** mô hình tốt nhất vẫn báo nhầm khoảng **9 lần mỗi phút** không làm cử chỉ
    (trên IPN); mục tiêu khi dùng thật: **dưới 0,5 lần mỗi phút**
    → Phase 9: **máy trạng thái** chỉ phát lệnh khi vài câu trả lời liền nhau cùng đồng ý, và nghỉ
    một chút sau mỗi lệnh
  - **15 con số không mô tả từng ngón tay** → không tách được "bàn tay mở đang lướt" với "tay đang
    chỉ trỏ" → lý do hai cách sửa kiểu tay đều phải tắt
  - **Zoom đôi khi bị đoán ngược chiều giữa chừng** (12–28% số cú zoom)
  - **Đề thi thử nhỏ:** chênh dưới khoảng 0,04 chưa đủ kết luận · **tay trái** chưa xét riêng
- Việc tiếp theo:
  - thử hướng vuốt · đếm báo nhầm 2 phút gõ phím, dùng chuột
  - thử có cấu trúc: mỗi cử chỉ 10 lần + 5 phút làm việc bình thường → có cần quay dữ liệu riêng
    (Phase 11) không
  - Phase 8: dạy lại với 5 cách xáo dữ liệu · Phase 9: máy trạng thái
  - cân nhắc thêm con số đo độ duỗi từng ngón

**Lời thoại**

> Tôi muốn nói thẳng các hạn chế.
>
> Lớn nhất là báo nhầm: trên dữ liệu IPN, cứ mỗi phút không làm cử chỉ, mô hình tốt nhất vẫn báo nhầm
> khoảng 9 lần, trong khi mục tiêu khi dùng thật là dưới 0,5 lần. Bước xử lý chính là máy trạng thái ở
> Phase 9: chỉ phát lệnh khi vài câu trả lời liền nhau cùng đồng ý, và nghỉ một chút sau mỗi lệnh, giống
> người bấm thang máy, đã bấm thì không bấm lại liên tục.
>
> Thứ hai, bộ 15 con số không mô tả từng ngón tay, nên không tách được bàn tay mở đang lướt với tay
> đang chỉ trỏ; đó là lý do hai cách sửa kia đều phải tắt. Cách sửa tận gốc là thêm con số đo độ duỗi
> từng ngón, hoặc quay thêm dữ liệu của chính người dùng. Ngoài ra, zoom đôi khi bị đoán ngược chiều
> giữa chừng, đề thi thử còn nhỏ, và tay trái chưa được xét.
>
> Việc tiếp theo trước hết là của tôi: thử hướng vuốt, đếm báo nhầm khi gõ phím, và một lần thử có cấu
> trúc, mỗi cử chỉ mười lần cộng năm phút làm việc bình thường, để có độ chính xác thật và quyết định có
> cần quay dữ liệu riêng hay không. Sau đó là Phase 8, dạy lại với năm cách xáo dữ liệu, và Phase 9,
> máy trạng thái.

---

## Slide 22 — Kết luận · ⏱ 0:45

**Trên slide**: Ba điều rút ra

1. Hai mô hình học máy nâng macro-F1 từ 0,23 (luật) lên 0,436 (rừng) và 0,556 (LSTM). Demo dùng mô
   hình ghép, vì theo bằng chứng ban đầu nó hợp với bàn tay người dùng hơn
2. Điểm trên đề thi thử là cần nhưng chưa đủ: cả hai lần thử trên webcam đều lộ ra lệch miền, và thí
   nghiệm "đổi đúng một thứ" chỉ ra mô hình thật sự dựa vào gì
3. Làm có kiểm chứng: đo cả lợi lẫn giá trước khi bật một thay đổi; kết quả tái lập được từng chữ số;
   đề thi thật vẫn niêm phong

**Lời thoại**

> Tóm lại, ba điều.
>
> Một: hai mô hình học máy đã nâng macro-F1 từ 0,23 của mô hình luật lên 0,436 rồi 0,556. Demo dùng mô
> hình ghép, vì theo bằng chứng ban đầu, nó hợp với cách người dùng thật làm cử chỉ.
>
> Hai: điểm trên đề thi thử là cần, nhưng chưa đủ. Cả hai lần, mô hình tốt trên giấy đều hỏng ở một cử
> chỉ khi gặp tay thật, và tôi tìm ra nguyên nhân bằng cách hỏi thẳng mô hình qua thí nghiệm "đổi đúng
> một thứ".
>
> Ba: mọi thay đổi đều được đo cả lợi lẫn giá trước khi bật, kết quả tái lập được từng chữ số, và đề
> thi thật vẫn còn niêm phong cho lần đánh giá cuối.
>
> Cảm ơn thầy cô và các bạn đã lắng nghe. Tôi sẵn sàng nhận câu hỏi.

---

## Phụ lục A — Chuẩn bị hỏi đáp

Câu trả lời dùng số của bản tổng kết hiện hành. Dòng đánh dấu *(sâu)* dùng số ở Phụ lục B.2, chỉ nói
khi người hỏi muốn đi sâu.

**1. Hệ thống đã điều khiển được máy tính chưa?**

- Chưa phát lệnh thật. Demo hiện hiển thị câu trả lời trên màn hình, 5 lần mỗi giây.
- Muốn phát lệnh cần máy trạng thái (Phase 9), để mỗi cử chỉ ra đúng một lệnh. Nối thẳng bây giờ thì
  báo nhầm sẽ làm slide tự chuyển.

**2. Mô hình ghép điểm thấp hơn LSTM, sao lại dùng nó?**

- Đề thi thử đo cách làm của người diễn IPN. Họ zoom đúng kiểu ba ngón, và ở kiểu đó LSTM giỏi hơn.
- Thí nghiệm cho thấy zoom của LSTM gãy khi nhẫn và út duỗi ra, và nó còn báo zoom khi tay đứng yên.
- Phát lại phiên webcam: báo zoom 24 lần (LSTM) → 45 lần (ghép), số lần báo vuốt giữ nguyên.
- *(sâu)* Trong 205 cửa sổ "trông như zoom" của phiên đó (cái–trỏ đổi rõ, cổ tay chậm), LSTM trả
  "không có cử chỉ" 57%, mô hình ghép báo zoom 66%.
- Đây vẫn là bằng chứng sơ bộ; lần thử có cấu trúc sẽ xác nhận hoặc bác bỏ.

**3. Macro-F1 0,556 nghe thấp, vậy có dùng được không?**

- Đề thi thử giữ tỉ lệ ngoài đời: 96,5% không có cử chỉ, mỗi cử chỉ chỉ khoảng 100 cửa sổ. Vài phần
  trăm báo nhầm trên lớp đông nhất cũng kéo tỉ lệ báo đúng xuống mạnh.
- Đếm theo cử chỉ thì 80–93% cử chỉ được nhận ra ít nhất một lần.
- Phần còn thiếu là báo nhầm, việc của máy trạng thái.

**4. "93% cú vuốt trái" nghĩa là nhận đúng 93% cú vuốt?**

- Chưa hẳn. Đó là tỉ lệ cử chỉ có ít nhất một cửa sổ được nhận đúng.
- Một cử chỉ vẫn có thể có thêm câu trả lời sai, hoặc sinh nhiều lệnh. Đếm đầy đủ cần máy trạng thái
  (Phase 8–9).

**5. Thí nghiệm "đổi đúng một thứ" có đáng tin? Cử chỉ bị sửa có còn giống tay thật?**

- Làm trên cử chỉ thật của IPN, chỉ đổi đúng một khía cạnh, có cộng độ rung như tay thật, và đi qua
  đúng các bước xử lý như lúc chạy thật.
- Bản sửa được so với tay thật trước khi tin: bàn tay "cứng hoàn toàn" có độ mở 0,06, tay chỉ trỏ thật
  0,2–0,8, nên bản đó bị coi là giả tạo.
- Kết luận của thí nghiệm khớp với triệu chứng trên webcam ở cả hai lần.

**6. Sao không quay luôn dữ liệu của chính bạn?**

- Kế hoạch là dùng IPN trước, chỉ quay dữ liệu riêng (Phase 11) khi có bằng chứng là cần.
- Bằng chứng đến từ lần thử có cấu trúc: mỗi cử chỉ 10 lần, cộng 5 phút làm việc bình thường. Lần thử
  này đang chờ làm.
- *(sâu)* Theo `docs/SPEC.md`, dấu hiệu cần bật: một lớp đúng dưới 7/10 lần dù làm đúng hướng dẫn, hoặc
  báo nhầm khi làm việc bình thường hơn 0,5 lần mỗi phút.

**7. Có "ăn gian" đề thi không? Đề thi thật đã mở chưa?**

- Chia theo người: không ai có mặt ở cả bài tập về nhà lẫn đề thi.
- Biến đổi dữ liệu chỉ áp lên bài tập về nhà.
- Đề thi thật có khoá kỹ thuật, mỗi lần mở để lại nhật ký. Đến nay chưa mở lần nào.

**8. Lần đầu đạt 0,601, sao chỉ báo 0,556?**

- 0,601 là đỉnh may mắn: chọn đúng epoch có điểm cao nhất, trong khi điểm dao động ±0,04 giữa hai
  epoch.
- Chọn theo trung bình 10 epoch: 0,556, mức thường đạt khoảng 0,53.
- Con số không thiên lệch: dạy lại với 5 cách xáo dữ liệu (Phase 8), và lần mở đề thi thật.

**9. Tăng cường dữ liệu có làm LSTM giỏi hơn không?**

- Tác dụng rõ nhất là chống học thuộc lòng: không tăng cường thì mức sai trên đề thi thử quay đầu tăng
  sau epoch 38; có tăng cường thì không.
- *(sâu)* Về macro-F1, mức thường đạt có và không tăng cường là 0,532 ± 0,036 và 0,512 ± 0,020. Chênh
  lệch nhỏ hơn độ dao động, nên chưa đủ bằng chứng để kết luận.

**10. Sao LSTM không đọc cả hai chiều cho chính xác hơn?**

- Đọc hai chiều là đọc cả tương lai. Khi chạy trên webcam, tương lai chưa xảy ra, nên con số đạt được
  trên giấy sẽ không đạt được khi dùng thật.

**11. Báo nhầm khoảng 9 lần mỗi phút thì dùng thật sao được?**

- Đó là đếm trên IPN, chưa qua máy trạng thái; lớp không cử chỉ của IPN còn chứa nhiều động tác khó như
  chỉ trỏ.
- Máy trạng thái (Phase 9) chỉ phát lệnh khi vài câu trả lời liền nhau đồng ý, và nghỉ sau mỗi lệnh.
- Mục tiêu: dưới 0,5 lần mỗi phút khi làm việc bình thường. Không đạt thì quay dữ liệu riêng.

**12. Hai cách sửa bị tắt có phải công cốc?**

- Không. Chúng được đo cả lợi lẫn giá, nên quyết định tắt có căn cứ.
- Chúng chỉ ra chỗ thiếu thật: bộ 15 con số không mô tả từng ngón tay.
- Vẫn nằm trong code. Có bật cách "chấp nhận vuốt giữ dáng" không, ở mức nào, là lựa chọn còn để ngỏ.

**13. Mô hình ghép có phải giải pháp chữa cháy?**

- Phần nào đúng. Nhưng nó dựa trên kết quả thí nghiệm, không theo cảm tính, và cả hai phần đều đã chạy
  tốt trên webcam.
- Cách sửa tận gốc: thêm con số đo độ duỗi từng ngón, hoặc dữ liệu riêng.

**14. Hệ thống có chạy kịp thời gian thực không?**

- Mỗi 0,2 giây trả lời một lần. Rừng mất khoảng 9 mili-giây mỗi câu trả lời (trước khi tăng tốc là
  63), LSTM khoảng 1 mili-giây.
- Mô hình được nạp sẵn trước khi bật camera; trước đó demo đứng hình gần 3 giây lần đầu thấy tay.
- Số khung hình mỗi giây và độ trễ sẽ được đo đầy đủ ở giai đoạn sau.

**15. Phase 6 có đạt tiêu chí đề ra không?**

- Bộ kiểm tra Phase 6 có ba điều kiện. Hai điều kiện đạt: rừng cao hơn hẳn luật, và điểm không cao bất
  thường (dấu hiệu rò rỉ dữ liệu).
- Điều kiện thứ ba, "ba con số quan trọng nhất đúng như dự đoán", không đúng theo chữ vì chuyện "người
  sinh đôi" (slide 8). Kết quả đó được ghi lại làm lời giải thích.

**16. Sao chọn LSTM mà không phải mô hình mới hơn?**

- Bài tập về nhà chỉ có 3 326 cửa sổ, nên ưu tiên mô hình nhỏ.
- LSTM một chiều là mô hình chuỗi trong kế hoạch. Các phương án nhỏ khác, như GRU, sẽ được so ở Phase 8.

**17. Tay trái thì sao?**

- Chưa xét riêng. Demo dùng tay phải.
- *(sâu)* 133/145 clip trong bài tập về nhà là tay phải (`docs/gestures.md`).

---

## Phụ lục B — Số liệu tra nhanh

### B.1. Theo bản tổng kết hiện hành (2026-10-20)

| Mục | Giá trị |
|---|---|
| Dữ liệu | IPN Hand: 200 video, 50 người, 14 loại động tác; chia 30 / 7 / 13 người |
| Cửa sổ | 1,2 giây = 18 thời điểm; hỏi mỗi 0,2 giây (5 câu trả lời mỗi giây) |
| Bài tập về nhà | 3 326 cửa sổ, `none` chiếm một nửa |
| Đề thi thử | 11 038 cửa sổ, 96,5% `none`; 388 cửa sổ cử chỉ, khoảng 100 mỗi cử chỉ |
| macro-F1 trên đề thi thử | ngẫu nhiên 0,080 · luôn `none` 0,196 · luật 0,231 · rừng 0,436 · LSTM 0,556 · ghép 0,506 |
| Ví dụ vuốt trái (rừng → LSTM) | bắt được 54% → 89% · báo đúng 13% → 26% · rừng: 56/104 bắt được, 424 lần báo, 366 lần là `none` |
| Theo cử chỉ (vuốt trái / phải; zoom in / out) | rừng 70 / 70; 59 / 56 · LSTM 93 / 85; 89 / 80 (%) |
| Cửa sổ `none` bị báo nhầm | luật gần một nửa · rừng 8,2% (877 cửa sổ) · LSTM 5,8% |
| Cụm báo nhầm mỗi phút | rừng 14,8 · LSTM 8,6 |
| Báo nhầm khi chỉ trỏ (một / hai ngón) | rừng 5,8 / 9,7% · LSTM 3,5 / 5,9% |
| Báo nhầm khi tay nghỉ | rừng 10,6% · LSTM 14,5% |
| Rừng ngẫu nhiên | 300 cây · huấn luyện 1,6 giây · 9 ms mỗi câu trả lời (trước 63 ms) |
| LSTM | khoảng 220 nghìn núm vặn · một chiều · huấn luyện 13–25 phút trên CPU · khoảng 1 ms mỗi câu trả lời · lỗi trên cử chỉ nặng gấp khoảng 4 lần |
| Độ quan trọng | top 3: `pinch_range`, `pinch_delta`, `max_vx` · `dx` thứ 13 · cặp `dx` + `mean_vx` tương quan 0,97; xáo cả cặp → cửa sổ vuốt ngược hướng 8 → khoảng 43 |
| Thí nghiệm vuốt, trái / phải (rừng; LSTM) | không sửa 100 / 92 · giữ dáng 0 / 0; 8 / 0 · đi rồi về 45 / 37; 96 / 99 · nửa quãng 48 / 47 · một phần tư quãng 4 / 0; 100 / 94 · cổ tay đứng yên 0 / 0; 100 / 87 (%) |
| Thí nghiệm zoom, in / out (rừng; LSTM) | không sửa 93 / 98; 100 / 100 · nhẫn, út duỗi 63 / 85; 10 / 35 · zoom hai ngón 52 / 54; 7 / 38 · tay tĩnh vẫn báo zoom 0; 46–62 (%) |
| Tăng cường "bàn tay cứng" (đang tắt) | độ mở bản giả 0,06, tay chỉ trỏ thật 0,2–0,8 · lợi 10% → 38–56% · báo nhầm × 1,5–2,6 |
| Thử sửa zoom trong LSTM (đang tắt) | nhận zoom 88–98% · báo nhầm thành `zoom_out` 52 → 528 · chỉ trỏ 3,5 / 5,9 → 12,0 / 10,2% · báo đúng `zoom_out` 46% → 10% · kho hơn 58 nghìn dáng tay |
| Phiên sau luyện tập (rừng) | 43 cửa sổ kiểu vuốt · 88% mở tay đúng kiểu IPN · 79% nhận là vuốt |
| Đường học | mô hình chính đứng yên sau khoảng epoch 20, không quay đầu · không tăng cường: thấp nhất ở epoch 38, rồi tăng khoảng 30% |
| Độ tin của con số | dao động ±0,04 · đỉnh may mắn 0,601 · trung bình 10 epoch: 0,556, thường đạt khoảng 0,53 · dừng quá sớm ở epoch 40 và 48 trước khi sửa |
| Mô hình ghép | 0,506 · phát lại 1,1 phút: báo zoom 24 → 45, báo vuốt giữ nguyên |
| Hộp đen, tái lập | phát lại khớp 316/316 · LSTM trùng từng chữ số suốt 106 epoch |
| Đề thi thật | chưa mở |

### B.2. Số liệu thêm, từ bản tổng kết trước (2026-10-19)

Bản tổng kết hiện hành không còn ghi các số dưới đây. Chúng vẫn là kết quả của cùng các lần chạy;
chỉ dùng khi bị hỏi sâu.

| Mục | Giá trị |
|---|---|
| Có / không tăng cường (LSTM), mức thường đạt | 0,532 ± 0,036 / 0,512 ± 0,020 → chưa đủ bằng chứng để kết luận |
| Mô hình ghép trên đề thi thử | theo cử chỉ: vuốt 93 / 85%, zoom 59 / 56% · báo nhầm 6,0% cửa sổ `none`, 8,9 cụm mỗi phút |
| Phát lại phiên webcam, bốn mô hình (vuốt trái / phải; zoom in / out) | luật 5 / 4; 23 / 25 · rừng 5 / 2; 21 / 24 · LSTM 7 / 11; 10 / 14 · ghép 7 / 11; 21 / 24 |
| 205 cửa sổ "trông như zoom" trong phiên đó | LSTM trả `none` 57% · ghép báo zoom 66% · 6% bị phần vuốt giành thành vuốt |
| Phát lại trên video IPN | khớp 150/150 câu trả lời của LSTM |
| Đường học | checkpoint LSTM ở epoch 86 (vạch dọc hình trái) · bản không tăng cường: mức sai (làm mượt) thấp nhất 0,490 ở epoch 38, sau đó 0,56–0,67 |
| Báo nhầm với "xòe tay hai lần" | 13–19% tuỳ mô hình, chủ yếu thành zoom |
| Đề thi thật | 44 video của 12 người (8 video bị loại vì lệch nhãn) |
| Kiểm thử tự động | 152 đạt (ngày 2026-10-19) |

---

## Phụ lục C — Bản rút gọn và chuẩn bị

### C.1. Bản rút gọn khoảng 12 phút

Giữ các slide dưới đây, mỗi slide chỉ nói ý chính. Ý của các slide bị bỏ lồng vào slide liền kề bằng
một câu.

| Slide | Thời gian | Câu lồng vào |
|---|---|---|
| 1 Tiêu đề | 0:20 | |
| 2 Bài toán | 0:45 | |
| 3 Hệ thống nhìn bàn tay | 0:45 | |
| 5 Ba tập dữ liệu | 0:45 | "Thay vì người viết luật như ở Phase 5, máy tự tìm quy luật từ ví dụ có đáp án: 200 video IPN của 50 người." |
| 6 Đo tốt tới đâu | 1:15 | |
| 7 Rừng ngẫu nhiên | 1:00 | "Mô hình dựa nhiều nhất vào động tác cái–trỏ và tốc độ cổ tay." |
| 9 Thử trực tiếp lần 1 | 1:30 | "Cách sửa: chế độ luyện tập hiện thêm độ mở bàn tay; sau khi luyện, rừng nhận 79% chuyển động kiểu vuốt." |
| 11 LSTM | 0:45 | |
| 12 Kết quả LSTM | 0:45 | "Điểm 0,556 chọn theo trung bình 10 epoch, vì điểm dao động ±0,04; con số 0,601 lần đầu là đỉnh may mắn." |
| 14 LSTM nhìn vuốt khác rừng | 0:30 | |
| 15 Thử trực tiếp lần 2 | 1:15 | |
| 17 Mô hình ghép | 1:00 | "Sửa thẳng trong LSTM có thử, nhưng báo nhầm thành zoom out tăng gấp 10 lần, nên phải tắt." · "Con số 24 và 45 có được nhờ ghi rồi phát lại phiên webcam, khớp 316/316 câu trả lời." |
| 21 Hạn chế, việc tiếp theo | 1:00 | |
| 22 Kết luận | 0:20 | |

### C.2. Nguồn hình có sẵn

| Slide | Hình |
|---|---|
| 2, 3 | Đoạn mẫu bốn cử chỉ có vẽ điểm mốc: `results/phase3/examples/` (ba người mỗi cử chỉ). Cắt một khung làm hình que 21 điểm cho slide 3 |
| 7 | Ma trận nhầm lẫn của rừng: `results/phase6/train_rf/run_07/confusion.png` (ô `none` → `swipe_left` = 366) |
| 8 | Độ quan trọng đặc trưng: `results/phase6/train_rf/run_07/importances.png` |
| 12 | Ma trận nhầm lẫn của LSTM: `results/phase6/evaluate/run_06/confusion.png` |
| 13 | Đường học: `results/phase7/train_lstm/run_07/training_curves.png` (trái) và `results/phase7/train_lstm/run_04/training_curves.png` (phải) |
| 17 | Ma trận nhầm lẫn của mô hình ghép: `results/phase6/evaluate/run_05/confusion.png` |
| 19 | Bảng so sánh mô hình: `results/model_comparison.md` |

Cần tự vẽ: hình que 21 điểm và cửa sổ 1,2 giây (slide 3), chuông báo cháy (slide 6, tuỳ chọn), minh
hoạ thí nghiệm "đổi một thứ" (slide 9 và 15), sơ đồ hai chuyên gia (slide 17).

**Slide dự phòng:** bảng thuật ngữ ở Phụ lục A của `docs/tong-ket-den-phase-7.md`, để mở ra khi người
nghe hỏi lại một từ.

**Lưu ý khi chiếu hình:**

- Hình ghi tên lớp trong code (`none`, `swipe_left`, …) và "tập val", tức đề thi thử.
- Ma trận nhầm lẫn có hai bảng: số cửa sổ (trái) và tỉ lệ theo hàng (phải). Với người không chuyên,
  chỉ cần chỉ vào một ô.
- Hình đường học có hai khung: Loss (mức sai) và macro-F1. Với người không chuyên, chỉ cần chỉ vào khung
  Loss. Phụ đề "macro-F1 val cao nhất" dễ bị hỏi:
  - hình trái: vạch dọc (epoch 86) là checkpoint chọn theo trung bình 10 epoch, nên vài điểm phía sau
    cao hơn nó;
  - hình phải: vạch dọc (epoch 20) là epoch có điểm cao nhất, **không** phải điểm bắt đầu quá khớp.
    Khi nói, chỉ vào đường mức sai đi lên sau epoch 38.

### C.3. Trước buổi thuyết trình

- **Phép thử hướng, trước khi demo vuốt.** Mở demo, vuốt sang trái *của chính mình*: phải ra
  `swipe_left`. Nếu ra `swipe_right` thì quy ước bị ngược; cách sửa ở `docs/SPEC.md`, mục Cổng chất
  lượng (đổi một hằng số rồi chạy lại các phép đo, không sửa code). Chưa sửa xong thì không demo vuốt.
- **Môi trường:** conda env `action-recognition`, `python --version` ra 3.10.x. Chạy thử demo một lần
  trên đúng máy, và nếu được thì ở đúng phòng sẽ trình bày: ánh sáng khác thì điểm mốc khác.
- **Tư thế khi demo** (theo `docs/gestures.md`):
  - tay phải; lòng bàn tay chiếm khoảng 1/5 chiều cao khung hình; đủ sáng;
  - zoom: ba ngón cái–trỏ–giữa, **nhẫn và út gập**;
  - vuốt: chụm đầu ngón, hất ngang một chiều, mở bàn tay trong lúc hất, rồi giữ tay ở đó;
  - giữa hai cử chỉ, để tay yên một nhịp.
- **Luôn có video dự phòng:**
  - quay màn hình một lượt demo mô hình ghép trên webcam. Muốn phát lại được thì chạy kèm `--log` với
    **tên file mới**, ví dụ `--log results/phase7/demo_thuyet_trinh.csv`. **Đừng** chạy lại lệnh demo
    cuối ở mục B.2 của `docs/tong-ket-den-phase-7.md`: lệnh đó ghi vào `results/phase7/live_hybrid.csv`,
    và demo sẽ ghi đè cả file này lẫn `live_hybrid_landmarks.npz`, tức phiên làm ra con số 24 → 45;
  - bản không cần webcam: chạy mô hình ghép trên một video IPN của đề thi thử:

    ```
    python scripts/demo.py --model hybrid --source data/ipn/videos/videos/1CM42_12_R__157.avi --max-sec 132
    ```

    Theo `results/phase7/notes.md`, mô hình ghép nhận được cả hai cú zoom và cú vuốt trái trong video
    này, nhưng vẫn còn vài cụm báo vuốt nhầm lúc người diễn chỉ tay.
- **Nếu đã làm lần thử có cấu trúc trước buổi thuyết trình:** thay bảng số lần báo ở slide 17 bằng số
  lần đúng trên 10 lần mỗi cử chỉ và số báo nhầm mỗi phút, rồi cập nhật slide 21 và câu 2 của Phụ lục A.
- **Cách nói số:** không nói "hệ thống chính xác x%"; nói macro-F1 trên đề thi thử. Chưa có số trên đề
  thi thật. Nếu bị hỏi, giải thích rằng đề đó được niêm phong tới lần đánh giá cuối.
