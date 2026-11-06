# Kịch bản thuyết trình — Phase 8–10: Hệ thống đã được tối ưu như thế nào

**Nguồn:** `docs/tong-ket-phase-8-10.md` (bản cập nhật 03/11/2026, viết cho người chưa học thị giác
máy tính). Số liệu biểu đồ training lấy từ `results/phase7/train_lstm/run_07`, `run_08` và
`results/model_comparison.md`.

**Chủ đề:** hệ thống đã được tối ưu thế nào — sáu vòng, mỗi vòng theo năm bước: chuyện gì không
ổn → tìm nguyên nhân bằng số đo → sửa thế nào → được gì → mất gì.

**Thời lượng dự kiến:** khoảng 21 phút trình bày, 2 phút demo, sau đó hỏi đáp. Nếu người nghe đã
quen thị giác máy tính, có thể lướt nhanh slide 4–6 (kiến thức nền), tiết kiệm khoảng 2 phút.

**Cấu trúc:** 25 slide (slide 25 là phụ lục thuật ngữ, chỉ mở khi được hỏi). Mỗi slide gồm: *trên
slide*, *lời nói*, và *ghi chú*. Bộ slide đi kèm: `docs/thuyet-trinh-phase-8-10.pptx`, dựng bằng
`python slides/build_slides.py`; phần lời nói và ghi chú nằm trong speaker notes.

---

## Chuẩn bị trước buổi

- Mở sẵn PowerPoint có khoảng 8–10 slide để demo, đặt ở chế độ trình chiếu.
- Mở terminal, đã kích hoạt env `action-recognition`, gõ sẵn lệnh:
  `python scripts/demo.py --model hybrid`.
- Sau khi bấm `c` bật điều khiển, **bấm chuột vào cửa sổ trình chiếu** — nếu không, phím sẽ đi vào
  cửa sổ demo (lỗi của lần thử slide đầu tiên, vòng 6).
- Kiểm tra ánh sáng và webcam: tay nằm gọn trong khung, nền không quá rối.
- **Phương án dự phòng:** nếu demo trực tiếp hỏng, chiếu lại log `results/phase10/live_final2.csv`
  (92 giây, 19 lệnh) hoặc video quay trước.
- Tự nhắc nhịp làm cử chỉ: không lấy đà ngược chiều, giơ tay khoảng 1 giây rồi mới làm, zoom xong
  giữ yên khoảng 1 giây, các cử chỉ cách nhau khoảng 2 giây.

---

## Slide 1 — Mở đầu (0:30)

**Trên slide:**
- Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính
- Phase 8–10 · Hệ thống đã được tối ưu như thế nào

**Lời nói:**

> Xin chào thầy cô và các bạn. Đề tài của em là nhận dạng cử chỉ bàn tay thời gian thực để điều
> khiển máy tính. Hôm nay em trình bày Phase 8 đến 10: hệ thống đã được tối ưu như thế nào để từ
> chỗ nhận ra cử chỉ trên màn hình, trở thành công cụ điều khiển được slide thật.

---

## Slide 2 — Đọc nhanh (0:45)

**Trên slide:**
- Hệ thống **điều khiển được PowerPoint bằng cử chỉ tay trước webcam**
  - vuốt trái → slide sau · vuốt phải → slide trước
  - mở ba đầu ngón đang chụm → phóng to · chụm lại → thu nhỏ
- Phase 8–10 **không đổi cách máy "nhìn" bàn tay** — tối ưu mọi thứ xung quanh: khi nào bấm phím ·
  đo cho đúng · mô hình nào lo cử chỉ nào · ngưỡng cho từng loại · cách người dùng làm cử chỉ

**Lời nói:**

> Kết quả trước: hệ thống giờ điều khiển được PowerPoint bằng cử chỉ tay trước webcam. Vuốt trái
> sang slide sau, vuốt phải về slide trước; mở ba đầu ngón cái, trỏ, giữa đang chụm thì phóng to,
> chụm lại thì thu nhỏ.
>
> Điều đáng nói là Phase 8 đến 10 không đổi cách máy tính "nhìn" bàn tay. Chúng tối ưu mọi thứ
> xung quanh: quyết định khi nào bấm phím, đo cho đúng, mô hình nào lo cử chỉ nào, ngưỡng cho từng
> loại cử chỉ, và cả cách người dùng nên làm cử chỉ.

---

## Slide 3 — Lúc bắt đầu và bây giờ (1:00)

**Trên slide:**

| | Lúc bắt đầu | Bây giờ |
|---|---|---|
| Slide tự đổi khi không ai làm gì, trên video thử | 6,6–30 lần/phút | **0,85** lần/phút |
| Slide tự đổi khi người dùng nói chuyện có khua tay | 0,64 lần/phút | **0,18** lần/phút |
| Vuốt một chiều mà slide đi chiều ngược lại | 5 trên 20 | **2** trên 20 |
| Zoom được nhận trên tay người dùng | 0 trên 10 | **10** trên 20 |
| Thử slide thật: cú zoom thành lệnh | 0 trên 12 | **6** trên 12 |

- Điểm F1 trên bộ video chuẩn giữ gần như cũ: 0,559 → 0,561

**Lời nói:**

> Đây là thay đổi tính bằng những thứ người dùng thấy được. Trên video thử, slide tự đổi khi không
> ai làm gì từ 6,6 đến 30 lần mỗi phút xuống còn 0,85. Khi người dùng nói chuyện có khua tay trước
> webcam, từ 0,64 xuống 0,18 lần mỗi phút — tức hơn 5 phút mới có một lần. Vuốt mà slide đi ngược
> chiều giảm từ 5 xuống 2 trên 20 lần. Zoom trên tay người dùng từ không nhận được lần nào lên 10 trên
> 20. Và trên slide thật, cú zoom thành lệnh từ 0 lên 6 trên 12.
>
> Trong lúc đó, điểm F1 trên bộ video chuẩn — em sẽ giải thích con số này ở slide 6 — giữ gần như
> nguyên.

**Ghi chú:** zoom 0/10 là LSTM `run_07` trên 10 lời nhắc; 10/20 là cấu hình cuối trên 20 lời nhắc.
6/12 là chạy lại đúng phiên thử thất bại với cấu hình mới.

---

## Slide 4 — Máy tính "nhìn" bàn tay thế nào (1:00)

**Trên slide:**
- Camera ≈ 30 ảnh/giây → MediaPipe đánh dấu **21 điểm** (cổ tay, khớp, đầu ngón) → **cửa sổ** 1,2
  giây, xét lại mỗi 0,2 giây → mô hình trả lời **nhãn** + **độ tin** (0–1)
- Năm lớp và năm phím: `none` (không gửi) · `swipe_left` (→ slide sau) · `swipe_right` (← slide
  trước) · `zoom_in` (`+`) · `zoom_out` (`−`)
- Lớp `none` quan trọng không kém: phần lớn thời gian tay **không** làm cử chỉ

**Lời nói:**

> Để những phần sau dễ theo dõi, em nói nhanh máy tính "nhìn" bàn tay thế nào. Camera chụp khoảng
> 30 ảnh mỗi giây. Một công cụ có sẵn của Google là MediaPipe tìm bàn tay và đánh dấu 21 điểm: cổ
> tay, các khớp và đầu ngón. Từ đây máy tính chỉ làm việc với toạ độ của 21 điểm đó, như một bộ
> xương.
>
> Cứ mỗi 0,2 giây, hệ thống nhìn lại 1,2 giây gần nhất — gọi là một cửa sổ — và mô hình trả lời hai
> điều: cửa sổ này giống cử chỉ nào, gọi là nhãn, và chắc chắn tới đâu, gọi là độ tin.
>
> Có năm lớp: bốn cử chỉ ứng với bốn phím, và lớp "không có gì". Lớp này quan trọng không kém, vì
> phần lớn thời gian tay người dùng đang nói, gãi đầu, chỉ vào màn hình — và hệ thống phải im lặng.

---

## Slide 5 — Ba "bộ não" và dữ liệu học (1:00)

**Trên slide:**
- **Luật:** vài quy tắc viết tay — mốc so sánh
- **Rừng ngẫu nhiên:** hàng trăm cây quyết định bỏ phiếu trên 15 con số tóm tắt cửa sổ
- **LSTM:** mạng nơ-ron đọc cả chuỗi chuyển động, từng bước một
- **Mô hình ghép:** LSTM lo vuốt, rừng lo zoom
- Dữ liệu: **IPN Hand**, 200 video quay sẵn; **chia theo người** (train / val / test khoá tới lần
  cuối)
- Hệ quả: mô hình học cử chỉ **theo cách người diễn IPN làm** — sợi chỉ đỏ của Phase 10

**Lời nói:**

> Hệ thống có ba "bộ não". Luật là vài quy tắc viết tay, dùng làm mốc. Rừng ngẫu nhiên là hàng trăm
> cây quyết định cùng bỏ phiếu trên 15 con số tóm tắt cửa sổ. LSTM là mạng nơ-ron đọc cả chuỗi
> chuyển động từng bước, như đọc một câu từ trái sang phải. Và mô hình ghép để mỗi bộ não lo phần
> mình giỏi nhất: LSTM lo vuốt, rừng lo zoom.
>
> Các mô hình học từ IPN Hand, 200 video có người diễn làm cử chỉ. Dữ liệu được chia theo người, để
> mô hình phải nhận được tay người lạ. Nhưng có một hệ quả quan trọng: mô hình học cử chỉ theo cách
> người diễn IPN làm. Người dùng làm khác đi thì mô hình có thể không nhận ra. Đây là sợi chỉ đỏ của
> cả Phase 10.

---

## Slide 6 — Đo "tốt" như thế nào (1:00)

**Trên slide:**
- Hai câu hỏi người dùng quan tâm:
  - "Tôi làm cử chỉ, nó có nhận không?" → **recall**
  - "Tôi không làm gì, nó có tự đổi slide không?" → **lệnh nhầm mỗi phút**
- **Precision:** trong các lệnh phát ra, bao nhiêu phần đúng · **F1:** gộp precision và recall
- **Mức cửa sổ:** chấm từng đoạn 1,2 giây · **Mức sự kiện:** đếm lệnh như người dùng thấy, trên 27
  video kiểm định (60 phút, 108 cử chỉ) — thước đo chính từ Phase 8

**Lời nói:**

> Đo "tốt" thế nào? Người dùng thật sự quan tâm hai câu hỏi. Tôi làm cử chỉ, nó có nhận không — đó
> là recall. Tôi không làm gì, nó có tự đổi slide không — đó là lệnh nhầm mỗi phút. Thêm hai con số:
> precision là trong các lệnh phát ra, bao nhiêu phần đúng; F1 gộp precision và recall, chỉ cao khi
> cả hai cùng cao.
>
> Và có hai mức chấm. Mức cửa sổ chấm từng đoạn 1,2 giây, như chấm từng tấm ảnh. Mức sự kiện chấm cả
> hệ thống như người dùng thấy, tức đếm lệnh phát ra, trên 27 video kiểm định dài 60 phút với 108 cử
> chỉ. Từ Phase 8, mức sự kiện là thước đo chính.

---

## Slide 7 — Nếp làm việc: đo trước, sửa sau (1:00)

**Trên slide:**
1. **Ghi một lần, chấm mọi cấu hình** — như hộp đen máy bay; phát lại trùng 316/316 câu trả lời
2. **Tìm nguyên nhân bằng số đo, không đoán** — ngón gập hay duỗi, cái–trỏ cách nhau bao xa, mô hình
   nói gì ở từng nhịp 0,2 giây
3. **Mỗi thay đổi chấm trên bốn nguồn** — 27 video kiểm định · 40 lời nhắc webcam · gần 11 phút nói
   chuyện · các lần thử slide thật
4. **Người dùng chọn điểm đánh đổi** từ bảng số đo

**Lời nói:**

> Mọi vòng tối ưu đều theo bốn nguyên tắc. Một, ghi một lần, chấm mọi cấu hình — như hộp đen trên
> máy bay. Mỗi lần thử, hệ thống ghi lại 21 điểm của từng ảnh; sau đó có thể phát lại qua bất kỳ mô
> hình hay ngưỡng nào, kết quả y như chạy thật — đã kiểm trùng 316 trên 316 câu trả lời.
>
> Hai, tìm nguyên nhân bằng số đo chứ không đoán. Ba, mỗi thay đổi được chấm trên bốn nguồn, để sửa
> chỗ này không làm hỏng chỗ khác. Bốn, thường không có cấu hình tốt nhất về mọi mặt, nên điểm đánh
> đổi được chọn từ bảng số đo.

---

## Slide 8 — Vòng 1: Dạy hệ thống biết im lặng (1:15)

**Trên slide:**
- Mô hình như **bình luận viên** hô 5 lần mỗi giây: "vuốt trái!… vuốt trái!… không có gì!…"
- Phase 8 đo: bắt được **82–94%** cử chỉ, nhưng **6,6–30** lệnh nhầm mỗi phút — chỉ 5–20% lệnh đúng
- Sửa: **người trợ lý cẩn thận** (máy trạng thái) — Chờ tay → Sẵn sàng → Đang cân nhắc → Nghỉ
  1,2 giây
- Bốn quy tắc: đủ chắc mới cân nhắc · đủ tiếng hô cùng ý trong 5 tiếng liền · bấm xong nghỉ 1,2
  giây · hạ tay là huỷ hết

**Lời nói:**

> Vòng một. Hãy hình dung mô hình như một bình luận viên nhìn bàn tay và hô lên 5 lần mỗi giây:
> "vuốt trái, vuốt trái, không có gì, vuốt trái". Nếu mỗi tiếng hô là một lần bấm phím, một cú vuốt
> sẽ lật qua cả chục slide. Phase 8 đo đúng chuyện này: hệ thống bắt được 82 đến 94% cử chỉ, nhưng
> phát 6,6 đến 30 lệnh nhầm mỗi phút.
>
> Em đặt giữa bình luận viên và bàn phím một người trợ lý cẩn thận, tức máy trạng thái, với bốn
> trạng thái: chờ tay, sẵn sàng, đang cân nhắc, và nghỉ. Cùng bốn quy tắc: phải đủ chắc mới bắt đầu
> cân nhắc; phải nghe đủ số tiếng hô cùng ý trong 5 tiếng liền mới bấm; bấm xong thì nghỉ 1,2 giây,
> như chuông cửa chỉ reo một lần dù ấn hơi lâu; và hạ tay ra khỏi khung là huỷ hết.

---

## Slide 9 — Vòng 1: Phiếu phản đối, kết quả và cái giá (1:00)

**Trên slide:**
- Lỗi thiết kế đã tránh: chuỗi *vuốt, không có gì, vuốt, không có gì, vuốt* có 3/5 tiếng "vuốt" →
  cách đếm đầu tiên vẫn bấm. Bản dùng thật: tiếng hô **khác ý mà đủ chắc** là **phiếu phản đối**
- Ngưỡng khởi đầu 0,75 · 3/5, video kiểm định: LSTM F1 0,559 / 1,46 nhầm mỗi phút · ghép 0,490 /
  1,33 · rừng 0,405 / 0,50 · luật 0,130 / 6,82
- Mất gì: chỉ còn **0,77** lệnh mỗi cử chỉ (yêu cầu 0,9–1,1)
- Đánh đổi "phải thấy tay bao nhiêu": 70% → 100% mất 3/54 cú vuốt, nhầm chỉ giảm 3% → giữ 70%

**Lời nói:**

> Có một lỗi thiết kế đã tránh được. Cách hiểu đầu tiên của quy tắc đồng thuận là đếm tiếng hô cùng
> ý trong 5 tiếng gần nhất. Theo cách đó, chuỗi nhấp nháy "vuốt, không có gì, vuốt, không có gì,
> vuốt" có 3 trên 5 tiếng "vuốt" và sẽ bấm phím — một lệnh từ tín hiệu rất yếu. Bản dùng thật coi một
> tiếng hô khác ý mà đủ chắc, kể cả "không có gì", là phiếu phản đối, và huỷ ngay việc cân nhắc.
>
> Kết quả: lệnh nhầm giảm từ hàng chục xuống khoảng 1 đến 1,5 lần mỗi phút với hai bộ não tốt nhất.
> Cái giá: trợ lý cẩn thận thì đôi khi bỏ lỡ cử chỉ thật — chỉ còn 0,77 lệnh mỗi cử chỉ, trong khi
> yêu cầu là 0,9 đến 1,1.
>
> Một đánh đổi nữa: cửa sổ chỉ được xét khi ít nhất 70% số ảnh thấy tay. Nâng lên 100% thì mất 3
> trong 54 cú vuốt, mà lệnh nhầm chỉ giảm 3%, nên giữ 70%.

---

## Slide 10 — Vòng 2: Sửa thước đo trước khi sửa hệ thống (1:00)

**Trên slide:**

| Con số đánh lừa | Cách sửa |
|---|---|
| **Đồng hồ bấm giờ bắt đầu sai lúc:** lời nhắc 4 giây gồm cả lúc thu tay → độ trễ ra số âm | Đo độ trễ trên video IPN, nơi khoảnh khắc chính đã được đánh dấu sẵn |
| **Điểm "hoàn hảo" che giấu hai lỗi:** 1,00 lệnh mỗi cử chỉ nhưng recall chỉ 0,55 | Luôn báo kèm tỉ lệ nhận đúng, lệnh mỗi lời nhắc, lệnh phát trùng |
| **Trung bình sai cách:** đọc và gõ phím luôn ra 0, kéo luật từ 7,39 xuống 2,46 | Cộng tổng lệnh nhầm chia tổng số phút; thêm "nhầm mỗi phút có tay" (17% so với 89%) |

**Lời nói:**

> Vòng hai: khi bắt đầu đo trên webcam, em phát hiện ba con số đánh lừa. Tối ưu theo một thước sai
> thì càng cố càng lệch, nên phải sửa thước trước.
>
> Một, đồng hồ bấm giờ bắt đầu sai lúc: lời nhắc 4 giây gồm cả lúc thu tay về, nên độ trễ ra số âm.
> Em chuyển sang đo trên video IPN, nơi khoảnh khắc chính đã được đánh dấu sẵn. Hai, một điểm số
> "hoàn hảo" — đúng 1,00 lệnh mỗi cử chỉ — thật ra recall chỉ 0,55: gần nửa cử chỉ bị bỏ lỡ và lệnh
> thừa vừa khéo bù lại. Ba, con số nhầm mỗi phút từng là trung bình cộng của ba kịch bản, mà lúc đọc
> và gõ phím tay nằm ngoài khung nên luôn ra 0. Em đổi sang cộng tổng rồi chia tổng số phút, và thêm
> cột nhầm mỗi phút có tay.

---

## Slide 11 — Vòng 3: Mô hình cho bàn tay thật của người dùng (1:30)

**Trên slide:**
- LSTM `run_07` không nhận cú zoom nào: **0/10**; tay chụm đứng yên lại hô "vuốt" (4 lệnh nhầm /
  1,1 phút)
- **Độ duỗi ngón** = (đầu ngón → cổ tay) / (gốc ngón → cổ tay): gập ≈ 0,5, thẳng ≈ 1,3–1,5
- Thang độ duỗi: chấm xanh = người diễn IPN (nhẫn, út **gập** ≈ 0,5); dải đỏ = người dùng (**duỗi**
  1,5–2,1)
- Sửa (`run_08`): thêm **ví dụ biến tấu** — một nửa ví dụ zoom mang dáng ngón phụ của một bàn tay IPN
  khác; thêm bàn tay đứng yên, nhãn "không có gì"
- Bảng "được gì", cùng dữ liệu và cùng ngưỡng: zoom webcam 0/10 → **4/10** · tập zoom: vuốt nhầm 4 →
  **0** · IPN nhẫn, út duỗi: zoom còn nhận 10% / 35% → **95% / 95%** · F1 sự kiện 0,559 → 0,554

**Lời nói:**

> Vòng ba: trên tay em, LSTM lúc đó không nhận được cú zoom nào, 0 trên 10. Tệ hơn, khi bàn tay chỉ
> đang chụm đứng yên, nó lại hô "vuốt".
>
> Để tìm nguyên nhân, em đo độ duỗi của từng ngón: khoảng cách đầu ngón tới cổ tay, chia cho khoảng
> cách gốc ngón tới cổ tay. Ngón gập vào lòng bàn tay cho khoảng 0,5; ngón thẳng khoảng 1,3 đến 1,5.
> Hình nhỏ bên trái là thang đo này, từ 0 đến 2. Chấm xanh là người diễn IPN khi zoom: ngón nhẫn và út
> gập, khoảng 0,5. Dải đỏ là tay em: 1,5 đến 2,1, tức nằm hẳn ở phía duỗi. Hai nhóm không chồng lên
> nhau chút nào. LSTM chỉ từng thấy zoom với nhẫn, út gập, nên với nó "zoom" gắn liền với dáng ngón
> đó; gặp tay em, nó không nhận ra.
>
> Cách sửa là lần học `run_08` với hai loại ví dụ biến tấu tạo từ chính dữ liệu IPN: một nửa ví dụ
> zoom được ghép dáng ngón phụ của một bàn tay IPN khác, để mô hình thấy ngón phụ ở nhiều tư thế; và
> thêm ví dụ bàn tay đứng yên gắn nhãn "không có gì".
>
> Bảng bên phải so hai lần học trên cùng dữ liệu, cùng ngưỡng. Zoom trên webcam từ 0 lên 4 trên 10; hết
> vuốt nhầm khi tập zoom; trên video IPN đã sửa cho nhẫn, út duỗi thì zoom còn được nhận 95%. Và hàng
> cuối quan trọng: F1 sự kiện trên video kiểm định gần như giữ nguyên, 0,559 và 0,554 — tức là sửa cho
> tay em mà không làm hỏng kết quả ở mức lệnh trên IPN. Hai slide sau em giải thích kỹ hai biểu đồ đằng
> sau bảng này.

**Ghi chú:**
- Cách đọc thang độ duỗi: chỉ vào chấm xanh rồi dải đỏ; nhấn "không chồng lên nhau".
- Nếu bị hỏi vì sao tay người dùng duỗi tới 2,1, hơn mức "thẳng" 1,3–1,5: đó là số đo trên tay
  người dùng (mục 5 của tài liệu tổng kết); không cần giải thích sâu — điểm chính là nằm hẳn ở phía
  duỗi, xa vùng gập của IPN.
- Bảng: hàng "IPN sửa cho nhẫn, út duỗi" chính là biểu đồ bên phải của slide sau nữa.

---

## Slide 12 — Đường cong học của LSTM (3:30)

**Trên slide:**
- Biểu đồ trái: loss theo epoch; biểu đồ phải: macro-F1 mức cửa sổ theo epoch
- Đường xanh = tập học · đỏ = tập kiểm định · đỏ đậm = kiểm định, trung bình 10 epoch · gạch đứt
  = epoch 87 được chọn
- 107 epoch · dừng khi macro-F1 kiểm định (TB 10 epoch) 20 epoch không tăng · epoch 87: TB 0,528,
  điểm thô 0,489 · 11 038 cửa sổ kiểm định, hơn 96% là "không có gì"

**Lời nói:**

> Slide trước em giới thiệu LSTM, bộ não đọc cả chuỗi chuyển động. Slide này cho thấy nó "học" như thế
> nào. Đây là lần học thứ tám, `run_08`, cũng là bản đang chạy trong demo.
>
> Trước hết, "học" nghĩa là gì. Mỗi ví dụ học là một cửa sổ 1,2 giây — 18 nhịp, mỗi nhịp là toạ độ của
> 21 điểm trên bàn tay — kèm đáp án do người gán sẵn: đây là "vuốt trái", đây là "không có gì". Mô hình
> đoán, so với đáp án, rồi tự vặn các "núm chỉnh" bên trong một chút để lần sau đoán gần đúng hơn. Giống
> một học sinh làm bài tập rồi xem đáp án. Làm hết một lượt toàn bộ bài tập — khoảng 3 300 ví dụ — gọi
> là một **epoch**. Trục ngang của cả hai biểu đồ là số epoch: mô hình đã làm 107 lượt.
>
> Sau mỗi lượt, em chấm mô hình hai lần. Đường xanh chấm trên chính bộ bài tập nó đã học — tập học.
> Đường đỏ chấm trên video của những người nó chưa bao giờ thấy — tập kiểm định. Đường đỏ mới là thứ
> quan trọng, vì người dùng thật luôn là người lạ.
>
> Biểu đồ trái là **loss**, hiểu nôm na là điểm phạt. Mỗi lần trả lời, mô hình nói nó tin mỗi đáp án bao
> nhiêu phần. Trả lời đúng mà chắc thì bị phạt ít; trả lời sai mà lại rất chắc thì bị phạt nặng. Loss là
> điểm phạt trung bình, nên càng thấp càng tốt.
>
> Biểu đồ phải là **macro-F1**, điểm số chấm xem nó trả lời đúng tới đâu, từ 0 đến 1. F1 gộp hai câu
> hỏi: khi có cử chỉ thật, nó có nhận ra không; và khi nó hô một cử chỉ, nó có hô đúng không. F1 chỉ cao
> khi cả hai cùng tốt. Chữ "macro" nghĩa là tính điểm riêng cho từng lớp trong năm lớp rồi lấy trung
> bình, để cử chỉ hiếm cũng quan trọng ngang lớp "không có gì". Còn "mức cửa sổ" nghĩa là chấm từng đoạn
> 1,2 giây riêng lẻ, như chấm từng tấm ảnh, chưa phải số lệnh bấm phím thật.
>
> Giờ đọc biểu đồ từ trái sang, có ba giai đoạn. Hai mươi epoch đầu, mô hình tiến bộ rất nhanh: điểm
> phạt trên tập học giảm từ 0,88 xuống 0,23, F1 trên người lạ tăng từ 0,10 lên khoảng 0,40. Từ epoch 20
> đến khoảng 70, tiến bộ chậm lại, F1 trên người lạ lên tới khoảng 0,51. Sau đó đường đỏ đi ngang, trong
> khi đường xanh vẫn tiếp tục tốt lên. Nghĩa là mô hình bắt đầu "học thuộc lòng" bài tập, chứ không học
> thêm được điều gì dùng cho người lạ. Đó là lúc nên dừng.
>
> Có một câu hỏi tự nhiên: vì sao trên tập học gần 0,98 mà trên người lạ chỉ quanh 0,5? Một phần vì là
> người lạ. Nhưng lý do chính là tỉ lệ. Trong bài tập, em đã bớt các đoạn "không có gì" xuống còn khoảng
> một nửa. Tập kiểm định thì giữ đúng như đời thật: trong 11 038 đoạn, có 10 650 đoạn "không có gì", chỉ
> 388 đoạn có cử chỉ. Giống tìm kim trong đống rơm: chỉ cần mô hình nhìn nhầm 4% số cọng rơm thành kim,
> số kim giả đã nhiều hơn tất cả số kim thật. Vì vậy điểm "hô có đúng không" bị kéo xuống, và F1 thấp
> theo. Còn điểm phạt trên người lạ không tăng vọt về cuối, nên mô hình không bị hỏng vì học quá lâu.
>
> Cuối cùng là chuyện chọn mô hình. Đường đỏ nhạt là điểm của từng epoch, răng cưa rất mạnh: ở nửa sau,
> có epoch lên 0,57, có epoch chỉ 0,41, vì số đoạn cử chỉ quá ít nên vài chục câu đúng sai đã đổi điểm.
> Nếu chọn theo một đỉnh, em chỉ đang chọn may mắn. Nên em dùng đường đỏ đậm: điểm trung bình của 10 epoch
> liền nhau, giống xét học sinh theo điểm trung bình 10 bài kiểm tra gần nhất chứ không theo một bài
> được điểm cao. Việc học tự dừng khi đường đậm này 20 epoch liền không tăng — dừng ở epoch 107 — và em
> lấy mô hình ở epoch 87, chỗ gạch đứt, nơi đường đậm cao nhất: 0,528. Điểm riêng của chính epoch đó là
> 0,489; đây là con số em dùng để so sánh ở các slide sau.

**Ghi chú:**
- Thứ tự chỉ: trục ngang (epoch) → đường xanh / đỏ → biểu đồ trái (loss) → biểu đồ phải (macro-F1) →
  ba giai đoạn (epoch 1–20, 20–70, sau 70) → ô "11 038" ở dưới → đường đỏ nhạt và đỏ đậm → gạch đứt
  epoch 87 → ô "107 epoch" và "epoch 87".
- Từ khoá, nói một câu là đủ:
  - **Epoch:** một lượt học hết toàn bộ ví dụ học.
  - **Tập học / tập kiểm định:** bài tập để học / đề thi của người lạ; mô hình không học từ tập kiểm
    định, chỉ dùng để chấm.
  - **Loss:** điểm phạt trung bình; sai mà càng chắc càng bị phạt nặng.
  - **Recall:** có cử chỉ thật thì nhận ra được bao nhiêu phần. **Precision:** hô cử chỉ thì đúng bao
    nhiêu phần. **F1:** gộp hai số này, chỉ cao khi cả hai cao.
  - **Macro:** tính riêng từng lớp rồi lấy trung bình, lớp hiếm nặng ngang lớp phổ biến.
  - **Mức cửa sổ:** chấm từng đoạn 1,2 giây, chưa phải lệnh bấm phím thật.
  - **Trung bình trượt 10 epoch:** điểm trung bình của 10 epoch gần nhất, để bớt nhiễu.
  - **Dừng sớm:** ngừng học khi điểm trên người lạ không còn tăng (ở đây: 20 epoch).
  - **Học thuộc lòng (overfitting):** giỏi trên bài đã học nhưng không giỏi thêm trên người lạ.
- Số mốc (`results/phase7/train_lstm/run_08/history.csv`, `manifest.json`): 3 326 ví dụ học, mỗi
  ví dụ 18 nhịp × 42 con số · epoch 1: loss học 0,88, F1 kiểm định 0,10 · epoch 20: loss học 0,23, F1
  kiểm định TB 0,39 · epoch 87: loss học 0,05, F1 tập học 0,98 · F1 kiểm định thô từ epoch 60 dao động
  0,41–0,57, cao nhất 0,572 ở epoch 82 · học trên CPU khoảng 15 phút.
- "Kim trong đống rơm": 4% của 10 650 là 426, nhiều hơn 388 đoạn cử chỉ thật. Thực tế `run_08` gọi
  nhầm 1 061 đoạn "không có gì" thành cử chỉ (khoảng 10%).
- Nếu bị hỏi:
  - **"Có overfit không?"** Có dấu hiệu nhẹ — đường xanh vẫn lên mà đường đỏ đi ngang — nên mới dừng
    sớm theo điểm trên người lạ. Loss kiểm định không tăng vọt.
  - **"Vì sao không chọn epoch 82, điểm cao nhất?"** Vì đó là một đỉnh nhiễu; chọn theo trung bình 10
    epoch thì ổn định hơn.
  - **"F1 0,5 có thấp quá không?"** Đây là điểm chấm từng đoạn 1,2 giây, với rất nhiều đoạn "không có
    gì". Lúc chạy thật còn một bộ lọc quyết định khi nào mới bấm phím, nên điều người dùng thấy được
    chấm riêng ở mức lệnh (slide kết quả sau tối ưu).
  - **"Vì sao loss đỏ cao hơn loss xanh mà không so từng con số?"** Hai tập có tỉ lệ lớp khác nhau, nên
    nhìn hình dạng đường hơn là so trị số.

---

## Slide 13 — Vòng 3: Học lại đổi được gì, mất gì (3:00)

**Trên slide:**
- Biểu đồ trái: F1 từng lớp ở mức cửa sổ trên tập kiểm định, `run_07` (nhạt) so với `run_08` (đậm)
  - vuốt trái 0,40 → **0,57**; thu nhỏ 0,53 → **0,18**; macro-F1 0,556 → 0,489
- Biểu đồ phải: video IPN đã sửa cho nhẫn, út duỗi thẳng — tỉ lệ cú zoom còn được nhận
  - phóng to 10% → **95%** · thu nhỏ 35% → **95%**
- Mất gì: mô hình "dễ dãi" hơn với zoom; khi nói chuyện LSTM một mình thêm 5 lệnh thu nhỏ nhầm (vuốt
  nhầm 8 → 2)

**Lời nói:**

> Slide này so hai lần học của LSTM. Lần học trước, `run_07`, không nhận được cú zoom nào trên tay em,
> vì khi zoom em để duỗi ngón nhẫn và ngón út, còn người diễn trong dữ liệu IPN thì gập hai ngón đó. Lần
> học `run_08` cho mô hình xem thêm hai loại ví dụ: cú zoom với ngón nhẫn, út ở nhiều tư thế khác nhau, và
> bàn tay đứng yên được gắn nhãn "không có gì". Câu hỏi của slide là: đổi như vậy thì được gì, mất gì.
>
> Biểu đồ trái: mỗi cặp cột là một lớp, cột nhạt là lần học cũ, cột đậm là lần học mới; cặp cuối là
> macro-F1, trung bình của năm lớp. Nhìn lướt thì lần học mới tệ hơn: điểm chung giảm từ 0,556 xuống
> 0,489, và cột thu nhỏ tụt từ 0,53 xuống 0,18.
>
> Nhưng F1 gộp hai chuyện: có nhận ra cử chỉ thật không, và có báo nhầm không. Tách ra thì thấy một bức
> tranh khác. Về phần nhận ra, hai lần học gần như ngang nhau: trong 388 đoạn có cử chỉ, lần cũ nhận đúng
> 292, lần mới 296. Riêng thu nhỏ còn tăng nhẹ, từ 60 lên 64 đoạn. Vậy `run_08` không hề quên cử chỉ nào.
>
> Toàn bộ thay đổi nằm ở phần báo nhầm — những đoạn "không có gì" bị gọi thành cử chỉ. Số này tăng từ 616
> lên 1 061, và quan trọng hơn, nó dời chỗ: báo nhầm thành vuốt giảm, từ 475 xuống 382; báo nhầm thành zoom
> tăng vọt, từ 141 lên 679, riêng thu nhỏ từ 52 lên 528. Đó là lý do cột vuốt trái đi lên, còn cột thu
> nhỏ tụt xuống: khi mô hình hô "thu nhỏ", giờ chỉ khoảng 1 trên 10 lần là đúng.
>
> Có một chi tiết cho thấy điểm chung bị kéo xuống vì đâu. Macro-F1 lấy trung bình năm lớp ngang nhau,
> nên một cột tụt mạnh kéo cả điểm chung. Nếu bỏ riêng lớp thu nhỏ ra, trung bình bốn lớp còn lại lại
> nhích lên, từ 0,562 thành 0,566. Tức là gần như toàn bộ phần mất nằm ở một chỗ: mô hình hô "thu nhỏ"
> quá dễ.
>
> Vậy nó hô nhầm vào lúc nào? Em đếm theo loại đoạn trong IPN: 439 trong 445 lần báo nhầm tăng thêm rơi
> vào những đoạn người diễn đang chỉ trỏ bằng một hoặc hai ngón. Điều này dễ hiểu: lần học mới dạy mô hình
> rằng zoom là ngón cái và ngón trỏ cử động, còn các ngón khác ở tư thế nào cũng được. Một bàn tay đang
> chỉ trỏ và di chuyển ngón trỏ thì trông khá giống như vậy.
>
> Biểu đồ phải trả lời câu hỏi em thật sự cần. Em lấy những cú zoom thật mà mô hình đang nhận đúng, giữ
> nguyên cổ tay, ngón cái và ngón trỏ, rồi chỉ sửa ngón nhẫn và út thành duỗi thẳng — đúng kiểu tay của
> em — và xem mô hình còn nhận ra bao nhiêu phần. Lần học cũ chỉ còn nhận 10% cú phóng to và 35% cú thu
> nhỏ; phần còn lại nó coi là "không có gì". Nghĩa là `run_07` đã coi "nhẫn, út gập" là một phần của định
> nghĩa zoom. Lần học mới giữ được 95% cả hai: nó nhận zoom dựa vào chuyển động của ngón cái và ngón trỏ,
> đúng bản chất của cử chỉ.
>
> Đặt hai biểu đồ cạnh nhau thì thấy đó là hai mặt của một đồng xu. Chính sự "dễ tính" với tư thế các
> ngón phụ giúp mô hình nhận được tay em — biểu đồ phải — nhưng cũng làm nó dễ nhầm bàn tay đang chỉ trỏ
> là zoom — biểu đồ trái. Em chấp nhận đánh đổi này vì người dùng thật mới là mục tiêu, còn phần báo nhầm
> được xử lý ở bước sau: lúc chạy thật còn một bộ lọc quyết định khi nào mới bấm phím, và ở cấu hình cuối,
> zoom được giao cho rừng ngẫu nhiên — kết quả ở slide 8.

**Ghi chú:**
- Thứ tự chỉ: biểu đồ trái — cặp macro-F1 (giảm) → cặp thu nhỏ (tụt mạnh nhất) → cặp vuốt trái (tăng);
  biểu đồ phải — cột nhạt (10%, 35%) → cột đỏ (95%); cuối cùng chỉ vào ô "Mất gì".
- Từng lớp, `run_07` → `run_08` (ma trận nhầm lẫn `run_07/confusion.md`, `run_08/confusion.md`; tập
  kiểm định: 10 650 đoạn "không có gì", 388 đoạn cử chỉ). Nhận đúng / hô đúng (precision) / F1:
- Vuốt trái: 93 → 86 trên 104 · 0,26 → 0,44 · 0,40 → 0,57.
- Vuốt phải: 71 → 81 trên 96 · 0,25 → 0,22 · 0,38 → 0,35.
- Phóng to: 68 → 65 trên 94 · 0,39 → 0,28 · 0,51 → 0,40.
- Thu nhỏ: 60 → 64 trên 94 · 0,46 → 0,10 · 0,53 → 0,18.
- Không có gì: 10 034 → 9 589 trên 10 650 · ≈ 1,00 · 0,97 → 0,95.
- Macro-F1 bốn lớp, bỏ thu nhỏ: 0,562 → 0,566.
- Báo nhầm từ đoạn "không có gì" (`none_false_alarms_by_src.md`), tính mọi loại báo nhầm: tổng 616 →
  1 061. Chỉ trỏ một ngón (B0A) 123 → 419 (3,5% → 12,0%); chỉ trỏ hai ngón (B0B) 196 → 339 (5,9% →
  10,2%); "không cử chỉ" thuần (D0X) 208 → 164 (14,5% → 11,4%, giảm). Riêng báo nhầm thành zoom: 141 →
  679.
- Biểu đồ phải là phép đo độ bền, không phải recall: mẫu số là các cú zoom mỗi mô hình vốn đã nhận đúng
  (`run_07`: 68 phóng to, 60 thu nhỏ; `run_08`: 65, 64). Nguồn `results/phase7/probe_zooms/run_03`
  (`run_07`) và `run_04` (`run_08`).
- Cùng phép thử, duỗi thẳng cả ngón giữa, nhẫn, út: `run_07` 7% / 38% → `run_08` 88% / 94%.
- Cùng phép thử, bàn tay đứng yên ở dáng cuối cú phóng to: `run_07` vẫn gọi là phóng to 46% số lần,
  `run_08` 0% — lần học mới cần chuyển động, không đoán zoom từ một dáng tay đứng yên.
- Cùng phép thử, rừng ngẫu nhiên: 63% / 85%.
- Hỏi "95% có phải tự kiểm tra bài mình ra không?": một phần đúng — phép thử nhắm đúng kiểu thay đổi
  mà ví dụ biến tấu dạy, nên nó chứng minh biến tấu có tác dụng như thiết kế. Bằng chứng trên tay thật:
  zoom trên webcam 0/10 → 4/10; trong phiên tập zoom, vuốt nhầm 4 → 0.
- Hỏi "Sao không dùng độ chính xác (accuracy) cho dễ hiểu?": một mô hình lúc nào cũng đoán "không có
  gì" đã đúng 96,5% số đoạn mà không nhận được cử chỉ nào. Macro-F1 cho mỗi lớp nặng ngang nhau nên
  không bị đánh lừa như vậy.
- Hỏi "Vuốt phải sao không tốt lên?": báo nhầm thành vuốt phải tăng nhẹ (207 → 273), có 12 đoạn vuốt
  trái bị gọi thành vuốt phải (trước là 0); nhận đúng tăng 71 → 81, nên F1 gần như đứng yên.
- Hỏi "Phóng to và thu nhỏ có lẫn với nhau nhiều hơn không?": không — phóng to bị gọi thành thu nhỏ 19
  → 20 đoạn, thu nhỏ thành phóng to 15 → 15.

---

## Slide 14 — Vòng 4: Chặn cú "lấy đà" (1:15)

**Trên slide:**
- Cứ 20 lần vuốt thì **5** lần slide đi ngược chiều
- Lời hô từng nhịp 0,2 giây khi vuốt phải: `R R · L L L R R R R R`
  - kéo tay sang trái lấy đà, như vung vợt tennis → mô hình nhận đúng "vuốt trái", độ tin **1,00**
  - trợ lý bấm "vuốt trái" rồi nghỉ 1,2 giây → cú hất thật bị bỏ qua
  - nâng ngưỡng độ tin không giúp gì
- Sửa: lấy đà ≈ 3 nhịp, cú hất thật 4–5 → đòi **4 trên 5** (và ngưỡng 0,75 → 0,85)

| | 0,75 · 3/5 | **0,85 · 4/5** |
|---|---|---|
| Vuốt mà slide đi ngược chiều | 5/20 | **2/20** |
| Slide tự đổi khi nói chuyện (lần/phút) | 0,64 | **0,18** |
| F1 sự kiện · nhầm mỗi phút, video kiểm định | 0,554 · 1,63 | **0,600 · 0,77** |
| Vuốt / zoom được nhận trên webcam | 60% / 40% | 55% / 20% ← cái giá |
| Độ trễ | 0,62 giây | 0,76 giây |

**Lời nói:**

> Vòng bốn: cứ 20 lần vuốt thì 5 lần slide đi ngược chiều. Em in ra lời hô của mô hình ở từng nhịp
> trong một lần vuốt sang phải, và thấy ngay: trước khi hất tay sang phải, em kéo tay sang trái lấy
> đà, như người đánh tennis vung vợt về sau. Bản thân đoạn kéo đó là một cú vuốt trái, và mô hình
> nhận đúng như vậy với độ tin 1,00. Trợ lý nghe ba tiếng "L", đủ đồng thuận, bấm "vuốt trái", rồi
> nghỉ đúng lúc cú vuốt thật tới. Nâng ngưỡng độ tin không giúp gì, vì đoạn lấy đà cũng chắc chắn như
> cú vuốt thật.
>
> Khác biệt nằm ở độ dài: đoạn lấy đà chỉ khoảng 3 nhịp, cú hất thật 4 đến 5. Đòi 4 trên 5 thì đoạn
> lấy đà không đủ phiếu. Kết quả: ngược chiều từ 5 xuống 2 trên 20, nhầm khi nói chuyện từ 0,64
> xuống 0,18. Cái giá là zoom được nhận trên webcam giảm còn 20% — và vòng tiếp theo sinh ra từ chính
> cái giá này.

---

## Slide 15 — Vòng 5: Hai giám khảo (1:15)

**Trên slide:**
- Lần đầu điều khiển slide thật (32 giây): 4/4 vuốt, nhưng **0/12 cú zoom** thành lệnh
- Biểu đồ: độ tin trong năm nhịp liền của một cú thu nhỏ
  - LSTM: 0,52 · 0,47 · 0,61 · **0,88 · 0,96** — chắc quá muộn, chỉ 2 nhịp vượt 0,85, cần 4
  - Rừng: (chưa nhận ra) · 0,61 · 0,62 · 0,61 · 0,67 — luôn đúng, nhưng "nói nhỏ"; phóng to chỉ
    0,33–0,56
- Rừng nhận đúng **12/12** cú zoom · một ngưỡng chung cho hai giám khảo là không công bằng
- Không hạ ngưỡng chung được: về 0,75 · 3/5 thì cú lấy đà lại lọt qua

**Lời nói:**

> Vòng năm đến từ lần đầu điều khiển slide thật. Trong 32 giây, cả 4 lần vuốt đều đổi slide, nhưng 0
> trên 12 cú zoom thành lệnh — màn hình vẫn hiện chữ "zoom" mà slide không phóng to.
>
> Em xem hộp đen của chính lần thử đó. Đây là độ tin trong năm nhịp liền của một cú thu nhỏ. LSTM —
> đường đỏ — chắc chắn quá muộn: chỉ vượt ngưỡng 0,85 ở hai nhịp cuối, trong khi cần 4 phiếu. Rừng
> ngẫu nhiên — đường xanh — từ nhịp thứ hai đã gọi đúng "thu nhỏ" ở mọi nhịp, nhưng không bao giờ chắc
> kiểu 0,9. Tính cả 12 cú, rừng nhận đúng hết.
>
> Hình dung hai giám khảo: một người nói rất to khi đã chắc, nhưng chắc muộn; một người luôn đúng
> nhưng luôn nói nhỏ. Dùng một ngưỡng "độ to" chung cho cả hai là không công bằng. Mà hạ ngưỡng chung
> xuống thì cú lấy đà của vuốt lại lọt qua.

**Ghi chú:** chuỗi độ tin lấy từ mục 7 của tài liệu tổng kết (hộp đen `live_final`).

---

## Slide 16 — Vòng 5: Mỗi loại cử chỉ một luật riêng (1:15)

**Trên slide:**
- **Vuốt:** vẫn nghe LSTM, 0,85 và 4/5 — cú lấy đà vẫn bị chặn · **Zoom:** nghe rừng, ngưỡng riêng

| Zoom theo | Thử slide thật | 20 lời nhắc: đúng / ngược / bỏ lỡ | Lệnh mỗi lời nhắc | Nhầm khi nói chuyện |
|---|---|---|---|---|
| LSTM 0,85 · 4/5 (trước) | 0/12 | 4 / 1 / 15 | 0,62 | 0,18 |
| **Rừng 0,40 · 3/5 (chọn)** | **6/12** | **10 / 4 / 6** | **1,00** | **0,18** |
| Rừng 0,40 · 2/5 | 8/12 | 16 / 4 / 0 | 1,48 | 0,27 |
| Rừng 0,50 · 3/5 | 5/12 | 10 / 2 / 8 | 0,90 | 0,18 |

- Vì sao chỉ 6/12: người dùng đổi chiều mỗi ≈ 1,3 giây, mỗi lệnh cần ≈ 1,8 giây (0,6 gom phiếu + 1,2
  nghỉ); tắt nghỉ thì 9/12
- Được: lần thử hai 92 giây, **19 lệnh** (8 vuốt, 11 zoom) · Mất: F1 kiểm định 0,600 → 0,561; đổi
  thiết kế gốc (một ngưỡng chung)

**Lời nói:**

> Nên em tách luật: vuốt vẫn nghe LSTM với 0,85 và 4 trên 5, để cú lấy đà vẫn bị chặn; zoom nghe
> rừng ngẫu nhiên với ngưỡng riêng hợp với giọng "nói nhỏ" của nó. Bảng này là các mức đã thử trên cả
> bốn nguồn.
>
> Vì sao 0,40 mà không phải 0,50? Với phóng to, rừng thường chỉ chắc 0,33 đến 0,56; ở 0,50 không cú
> phóng to nào thành lệnh khi thử trực tiếp. Vì sao 3 trên 5 mà không phải 2 trên 5? Với 2 trên 5,
> zoom gần như không bị bỏ lỡ nhưng lệnh thừa tăng mạnh, phần lớn lúc đưa tay vào tư thế hoặc thả lỏng
> tay. Còn vì sao chỉ 6 trên 12: em đổi chiều zoom mỗi khoảng 1,3 giây, trong khi mỗi lệnh cần
> khoảng 1,8 giây.
>
> Kết quả: lần thử thứ hai, 92 giây, 19 lệnh, mọi phím đều tới PowerPoint, và lần đầu tiên đạt đúng
> 1,00 lệnh mỗi lời nhắc mà slide không tự đổi nhiều hơn. Cái giá: F1 trên video kiểm định giảm từ
> 0,600 xuống 0,561, và đây là thay đổi so với thiết kế gốc dùng một ngưỡng chung.

---

## Slide 17 — Vòng 6: Cho việc điều khiển dễ dùng hơn (0:45)

**Trên slide:**
- **Phím đi nhầm chỗ:** phím vào cửa sổ demo → demo luôn nằm trên cùng, nhắc bấm vào cửa sổ trình
  chiếu
- **Phím zoom:** `+` / `−` cho PowerPoint; Ctrl + / Ctrl − cho Google Slides, trình đọc PDF
- **Chiều vuốt theo ý người dùng:** vuốt trái → slide sau, như lật trang điện thoại
- **Tay ra vào khung:** 66 lần vào lại, không sinh lệnh lạ
- Nhịp làm cử chỉ: không lấy đà · giơ tay ≈ 1 giây rồi mới làm · zoom xong giữ yên ≈ 1 giây · cách
  nhau ≈ 2 giây

**Lời nói:**

> Vòng cuối là những thứ nhỏ quyết định trải nghiệm. Lần thử slide đầu, không có gì xảy ra vì phím
> đi vào cửa sổ demo; giờ cửa sổ demo luôn nằm trên cùng và nhắc bấm vào cửa sổ trình chiếu. Phím zoom
> là cộng, trừ cho PowerPoint. Chiều vuốt theo ý người dùng, như lật trang điện thoại. Và tay ra vào
> khung không sinh lệnh lạ, đã kiểm trên 66 lần.
>
> Từ các số đo, em thêm bốn lời khuyên: không lấy đà; giơ tay khoảng 1 giây rồi mới làm, vì cửa sổ
> cần 70% số ảnh thấy tay; zoom xong giữ yên, vì mở rồi chụm ngay chỉ tạo khoảng hai nhịp rõ ràng,
> không đủ ba phiếu; và các cử chỉ cách nhau khoảng 2 giây.

---

## Slide 18 — Kết quả sau tối ưu: bốn bộ não ở cấu hình cuối (1:00)

**Trên slide:**
- Biểu đồ: F1 sự kiện và lệnh nhầm mỗi phút trên 27 video kiểm định, cấu hình kích hoạt cuối

| Bộ não | F1 sự kiện | Lệnh nhầm mỗi phút | Macro-F1 mức cửa sổ |
|---|---|---|---|
| Luật | 0,138 | 6,26 | 0,231 |
| Rừng | 0,317 | 0,77 | 0,436 |
| LSTM (`run_08`) | 0,507 | 1,73 | 0,489 |
| **Ghép** | **0,561** | **0,85** | **0,537** |

**Lời nói:**

> Sau tất cả các vòng, đây là bốn bộ não trên cùng 27 video kiểm định, với cấu hình kích hoạt cuối.
> Mô hình ghép có F1 sự kiện cao nhất, 0,561, và lệnh nhầm chỉ 0,85 lần mỗi phút — gần bằng rừng, ít
> hơn một nửa so với LSTM một mình. Ghép lại thì mỗi bên lo phần mình giỏi: LSTM lo vuốt, còn zoom
> giao cho rừng, bộ não ít báo nhầm nhất trong ba bộ não học từ dữ liệu.

**Ghi chú:** số liệu từ `results/model_comparison.md` (`results/phase8/evaluate/run_13`–`run_16`).
Đây là tập kiểm định; tập test vẫn khoá tới lần chạy cuối.

---

## Slide 19 — Những thứ giúp tối ưu nhanh (0:45)

**Trên slide:**
- **Kết quả kèm "tem niêm phong":** 46 thí nghiệm học một lần mất **170 phút**; đổi luật trợ lý thì
  tem còn nguyên, dựng lại bảy bảng chỉ **0,8 phút**; hai lần suýt "rách tem" → nay có kiểm thử chặn
- **Hộp đen của mỗi lần thử:** có "0 thành 6 trên 12" mà không cần thử lại
- **Một lệnh dựng lại tất cả** (`run_all.py`); mô hình demo có chỗ cố định; thư viện ghi rõ phiên bản
- Quyết định: 25/10 ngưỡng khởi đầu · 26/10 `run_08`, 0,85 · 4/5 · 01/11 mô hình ghép, zoom riêng ·
  02/11 chiều vuốt

**Lời nói:**

> Sáu vòng này làm được trong vài ngày là nhờ ba thứ dựng từ trước. Kết quả thí nghiệm được lưu kèm
> một "tem niêm phong" ghi lại công thức đã dùng: khi chỉ đổi luật của người trợ lý, mô hình không
> đổi, tem còn nguyên, nên dựng lại bảy bảng chỉ mất chưa tới một phút thay vì học lại 170 phút. Hộp
> đen của mỗi lần thử cho phép phát lại dưới cấu hình mới. Và một lệnh dựng lại tất cả cho phần bàn
> giao. Bên phải là các quyết định cấu hình theo thời gian.

---

## Slide 20 — Demo trực tiếp (2:00)

**Trên slide:**
- `python scripts/demo.py --model hybrid` → bấm `c` → bấm chuột vào cửa sổ trình chiếu
- Vuốt trái: slide sau · Vuốt phải: slide trước · Mở/chụm ba ngón: phóng to/thu nhỏ

**Lời nói:**

> Bây giờ em xin demo trực tiếp. Em bật chương trình, bấm c để bật điều khiển, rồi bấm vào cửa sổ
> trình chiếu.
>
> (vuốt trái 2 lần) Vuốt trái, slide sang trang sau.
> (vuốt phải 1 lần) Vuốt phải để quay lại.
> (mở ba ngón, giữ yên, chụm lại) Mở ngón cái, trỏ, giữa để phóng to; chụm lại để thu nhỏ.
>
> Ở lần thử ngày 01/11, em dùng liền 92 giây, hệ thống phát 19 lệnh — 8 vuốt và 11 zoom — và mọi phím
> đều tới PowerPoint.

**Ghi chú:**
- Làm vuốt trước, zoom sau cùng. Trong PowerPoint, khi đang phóng to, mũi tên có thể di chuyển trong
  slide thay vì chuyển slide — nếu cần vuốt tiếp thì thu nhỏ về trước.
- Giơ tay khoảng 1 giây rồi mới làm; không lấy đà; zoom xong giữ yên; các cử chỉ cách nhau khoảng 2
  giây.
- Nếu một cử chỉ bị sót, bình tĩnh nói: "Đây đúng là hạn chế em sẽ trình bày ngay sau đây", rồi làm
  lại.
- Nếu demo hỏng hẳn, chuyển sang phương án dự phòng (video hoặc log `live_final2.csv`).

---

## Slide 21 — Những gì tối ưu chưa giải quyết được (1:00)

**Trên slide:**
- Biểu đồ: 40 lời nhắc trên webcam — vuốt 11 đúng · 2 ngược · 7 bỏ lỡ; zoom 10 · 4 · 6
- **Khoảng một nửa cử chỉ vẫn bị bỏ lỡ ở lần làm đầu** — nhẫn, út duỗi; lấy đà; đưa tay vào khung
  muộn → phần còn lại là tập luyện theo `docs/gestures.md`
- **Ngưỡng zoom chọn trên ít dữ liệu** (40 lời nhắc, 12 cú zoom), chấm trên chính dữ liệu đó → hơi
  lạc quan
- **Trên video IPN, bộ não tốt nhất tuỳ cách đo:** học lại nhiều lần theo công thức gốc thì LSTM một
  mình hơn; với mô hình đang dùng thì ghép hơn (0,561 so với 0,507)
- **Yêu cầu Phase 9 chưa đạt:** mô hình ghép phát 0,61 lệnh mỗi cử chỉ trên video IPN, chưa tới 0,9

**Lời nói:**

> Em xin nói thẳng những gì tối ưu chưa giải quyết được. Trên 40 lời nhắc trước webcam, khoảng một
> nửa cử chỉ vẫn bị bỏ lỡ ở lần làm đầu — biểu đồ bên trái. Phần lớn do em làm khác người diễn IPN:
> nhẫn, út duỗi, lấy đà, đưa tay vào khung muộn. Không ngưỡng nào sửa hết được, nên phần còn lại là
> tập luyện.
>
> Ngưỡng zoom được chọn trên ít dữ liệu, và chính dữ liệu đó dùng để chấm, nên con số có phần lạc
> quan. Trên video IPN, bộ não tốt nhất còn tuỳ cách đo: học lại nhiều lần theo công thức gốc thì LSTM
> một mình hơn; với mô hình đang dùng thì mô hình ghép hơn. Em chọn ghép vì kết quả trên webcam. Và
> một yêu cầu của Phase 9 vẫn chưa đạt: 0,61 lệnh mỗi cử chỉ trên video IPN, chưa tới 0,9.

---

## Slide 22 — Bài học về độ tin của con số (0:45)

**Trên slide:**
- Khi chỉ chạy một lần, chênh lệch nhỏ (**dưới ≈ 0,1** F1) thường **đảo chiều** khi đổi luật của
  người trợ lý → chỉ tin kết luận lặp lại qua nhiều lần học hoặc nhiều nhóm người
- Ba kết luận đứng vững qua mọi lần dựng lại bảng:
  - LSTM hơn rừng
  - trộn ngẫu nhiên người vào cả tập học lẫn tập chấm làm điểm đẹp giả thêm **0,10–0,15**
  - rừng cần gốc toạ độ ở cổ tay của ảnh đầu cửa sổ, và cửa sổ dài 1,2 giây

**Lời nói:**

> Một bài học xuyên suốt: khi chỉ chạy một lần, những chênh lệch nhỏ hơn khoảng 0,1 F1 thường đảo
> chiều khi đổi luật của người trợ lý. Nên em chỉ tin những kết luận lặp lại qua nhiều lần học hoặc
> nhiều nhóm người.
>
> Ba kết luận như vậy đứng vững qua mọi lần dựng lại bảng: LSTM hơn rừng; trộn ngẫu nhiên người vào
> cả tập học lẫn tập chấm làm điểm số đẹp giả thêm 0,10 đến 0,15 — nên dự án luôn chia theo người; và
> rừng cần đặt gốc toạ độ ở cổ tay của ảnh đầu cửa sổ, với cửa sổ dài 1,2 giây.

---

## Slide 23 — Việc còn lại và kết luận (0:45)

**Trên slide:**
- Đo tốc độ cả bốn bộ não ở hai mức ánh sáng, rồi đo lại (lần đầu: ≈ 30 ảnh/giây, ≈ 16 ms mỗi ảnh,
  ba phần tư là MediaPipe)
- Đo độ trễ bằng tay (quay webcam lẫn màn hình, đếm khung hình, 10 lần mỗi cử chỉ) · quay video demo
  · quyết định Phase 11, duyệt `docs/gestures.md`
- **Cuối cùng, đúng một lần:** mở khoá tập test; dựng lại toàn bộ môi trường từ README trên máy sạch
- Kết luận: sáu vòng tối ưu, mỗi vòng đo trước rồi mới sửa

**Lời nói:**

> Việc còn lại gồm: đo tốc độ cả bốn bộ não ở hai mức ánh sáng — lần đo đầu được khoảng 30 ảnh mỗi
> giây, ba phần tư thời gian là MediaPipe tìm bàn tay — đo độ trễ bằng tay, quay video demo, và quyết
> định có quay thêm dữ liệu của chính người dùng ở Phase 11 hay không. Cuối cùng, đúng một lần, em sẽ
> mở khoá tập test và thử dựng lại toàn bộ môi trường trên máy sạch.
>
> Tóm lại: qua sáu vòng tối ưu, mỗi vòng đo trước rồi mới sửa, slide tự đổi khi không ai làm gì giảm
> từ 6,6–30 xuống 0,85 lần mỗi phút, và lần đầu hệ thống điều khiển được slide thật. Em xin cảm ơn
> thầy cô và các bạn đã lắng nghe.

---

## Slide 24 — Cảm ơn và hỏi đáp

**Trên slide:**
- XIN CẢM ƠN!
- Mời thầy cô và các bạn đặt câu hỏi

---

## Slide 25 — Phụ lục: Thuật ngữ

**Trên slide:** bảng thuật ngữ rút gọn từ Phụ lục A của tài liệu tổng kết (điểm mốc, cửa sổ, nhãn,
độ tin, lệnh, máy trạng thái, đồng thuận k trên n, recall, precision, F1, mức cửa sổ / sự kiện, độ
duỗi ngón, lấy đà, ví dụ biến tấu, hộp đen).

**Ghi chú:** chỉ mở slide này khi có câu hỏi về thuật ngữ.

---

## Phụ lục — Câu hỏi có thể gặp

**1. Vì sao khoảng một nửa cử chỉ vẫn bị bỏ lỡ?**
Phần lớn do cách làm cử chỉ khác người diễn IPN: nhẫn, út duỗi, lấy đà, tay vào khung muộn. Mô hình
chỉ học từ IPN. Cách khắc phục trực tiếp nhất là Phase 11: quay thêm dữ liệu với dáng tay người dùng.

**2. Vì sao F1 trên tập học gần 0,98 mà trên tập kiểm định chỉ khoảng 0,5?**
Tập kiểm định là người lạ, và hơn 96% cửa sổ là "không có gì"; chỉ vài trăm cửa sổ cử chỉ, nên một
chút báo nhầm đã kéo precision và F1 xuống. Vì vậy epoch được chọn theo trung bình 10 epoch của F1 val,
và thước đo chính là mức sự kiện.

**3. Học lại `run_08` làm macro-F1 mức cửa sổ giảm, sao vẫn dùng?**
Vì cái cần là nhận được tay người dùng thật: zoom trên webcam từ 0/10 lên 4/10, và trên video IPN có
nhẫn, út duỗi thì zoom còn được nhận 95%. Phần báo nhầm zoom của LSTM được tránh bằng cách giao zoom
cho rừng ngẫu nhiên.

**4. Vì sao không hạ một ngưỡng chung cho dễ?**
Quay về 0,75 · 3/5 thì cú lấy đà của vuốt lại lọt qua (5/20 lần ngược chiều). LSTM và rừng có "giọng"
khác nhau, nên mỗi loại cử chỉ cần một ngưỡng.

**5. Vì sao không chia tập ngẫu nhiên?**
Trộn ngẫu nhiên người vào cả tập học lẫn tập chấm làm điểm đẹp giả thêm 0,10–0,15. Khi dùng thật, hệ
thống luôn gặp người mới.

**6. Vì sao chưa chạy tập test?**
Tập test chỉ mở đúng một lần ở cuối. Nếu nhìn test trong lúc còn chỉnh, mọi lựa chọn sau đó đều ngầm
khớp với test và con số không còn khách quan.

**7. 0,18 lần mỗi phút có thấp thật không?**
Đó là con số chia cho tổng số phút. Hệ thống chỉ có thể nhầm khi thấy tay, nên tài liệu thêm cột
"nhầm mỗi phút có tay"; phiên nói chuyện 10 phút chỉ thấy tay 17% thời gian.

**8. Ngưỡng chọn rồi chấm trên cùng dữ liệu, có lạc quan không?**
Có, và tài liệu ghi rõ điều đó. Mỗi lựa chọn được xem trên cả bốn nguồn nên không tối ưu riêng cho một
con số; nhưng cách kiểm chắc hơn là ghi phiên mới rồi chấm lại với cấu hình đã chốt.

**9. Hệ thống có cần GPU không?**
Không. Lần đo đầu khoảng 30 ảnh mỗi giây, khoảng 16 ms mỗi ảnh; ba phần tư thời gian là MediaPipe.
