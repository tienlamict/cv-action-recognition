# Phase 8–10 — Hệ thống đã được tối ưu như thế nào

*Giải thích cho người chưa học thị giác máy tính*

**Đề tài:** Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính.

**Cập nhật:** 2026-11-03

**Phạm vi:**

- **Phase 8:** chấm mọi mô hình theo cách người dùng thật sự cảm nhận.
- **Phase 9:** thêm bộ phận quyết định khi nào phát lệnh.
- **Phase 10:** chạy thật trên slide và đo trên webcam.
- **Phần đầu Phase 12:** chuẩn bị bàn giao.

Tài liệu kể từng vòng tối ưu theo năm bước: chuyện gì không ổn → tìm nguyên nhân bằng số đo →
sửa thế nào → được gì → mất gì.

**Đọc kèm:**

- bản tổng kết trước, giải thích rừng ngẫu nhiên và LSTM từ đầu: `docs/tong-ket-den-phase-7.md`;
- cách làm cử chỉ: `docs/gestures.md`;
- số liệu chi tiết: `results/phase10/notes.md`, `results/phase10/final_config.md`.

Từ chuyên môn được giải thích ở Phụ lục A.

---

## 0. Đọc nhanh

Hệ thống giờ **điều khiển được PowerPoint bằng cử chỉ tay trước webcam**:

- vuốt sang trái thì sang slide sau, vuốt sang phải thì về slide trước;
- mở các đầu ngón cái, trỏ, giữa đang chụm thì phóng to; chụm chúng lại thì thu nhỏ.

Phase 8 đến 10 không đổi cách máy tính "nhìn" bàn tay. Chúng tối ưu **mọi thứ xung quanh**:

- cách quyết định khi nào bấm phím;
- cách đo cho đúng;
- mô hình nào lo cử chỉ nào;
- ngưỡng nào cho từng loại cử chỉ;
- cách người dùng nên làm cử chỉ.

| | Lúc bắt đầu | Bây giờ |
|---|---|---|
| Slide tự đổi khi không ai làm gì, trên video thử | 6,6–30 lần mỗi phút | **0,85** lần mỗi phút |
| Slide tự đổi khi người dùng nói chuyện có khua tay | 0,64 lần mỗi phút | **0,18** lần mỗi phút |
| Vuốt một chiều mà slide đi chiều ngược lại | 5 trên 20 lần | **2** trên 20 lần |
| Zoom được nhận trên tay người dùng | 0 trên 10 lần | **10** trên 20 lần |
| Thử trên slide thật: cú zoom thành lệnh | 0 trên 12 | **6** trên 12 (chạy lại cùng phiên) |

Điểm số trên bộ video chuẩn (F1, xem mục 1.5) giữ gần như cũ: 0,559 lúc bắt đầu, 0,561 bây giờ.

---

## 1. Vài điều cần biết trước

### 1.1. Máy tính "nhìn" bàn tay như thế nào

1. **Camera chụp khoảng 30 ảnh mỗi giây.**
2. **Một công cụ có sẵn của Google, MediaPipe,** tìm bàn tay trong mỗi ảnh và đánh dấu **21
   điểm**: cổ tay, các khớp và đầu năm ngón. Từ đây máy tính không làm việc với ảnh nữa, chỉ với
   toạ độ của 21 điểm. Bàn tay thành một **bộ xương gồm 21 chấm**.
3. **Mỗi 0,2 giây, hệ thống nhìn lại 1,2 giây gần nhất** của bộ xương đó. Một đoạn 1,2 giây như
   vậy gọi là một **cửa sổ**. Một cử chỉ thật (khoảng 2 giây) vì thế được nhìn qua nhiều cửa sổ
   chồng lên nhau.
4. **Mô hình xem cửa sổ và trả lời hai điều:** cửa sổ này giống cử chỉ nào (gọi là **nhãn**), và
   chắc chắn tới đâu, từ 0 đến 1 (gọi là **độ tin**).

### 1.2. Năm lớp và năm phím

| Lớp | Nghĩa | Phím gửi đi |
|---|---|---|
| `none` | không có cử chỉ nào | không gửi gì |
| `swipe_left` | vuốt sang trái | mũi tên phải: slide sau |
| `swipe_right` | vuốt sang phải | mũi tên trái: slide trước |
| `zoom_in` | mở ba đầu ngón đang chụm | `+`: phóng to |
| `zoom_out` | chụm ba đầu ngón đang mở | `−`: thu nhỏ |

Lớp `none` quan trọng không kém bốn lớp kia. Phần lớn thời gian tay người dùng **không** làm cử
chỉ: đang nói, gãi đầu, chỉ vào màn hình. Hệ thống phải im lặng lúc đó.

### 1.3. Ba "bộ não" và một bộ ghép

- **Luật:** vài quy tắc viết tay, kiểu "cổ tay đi ngang nhanh hơn X thì là vuốt". Đơn giản, dùng
  làm mốc so sánh.
- **Rừng ngẫu nhiên:** hàng trăm "cây quyết định" cùng bỏ phiếu. Mỗi cây hỏi một chuỗi câu hỏi
  có/không trên 15 con số tóm tắt cửa sổ, ví dụ "ngón cái và ngón trỏ có tách xa nhau ra không?".
- **LSTM:** một mạng nơ-ron đọc **cả chuỗi chuyển động** từng bước một, như đọc một câu từ trái
  sang phải. Nó học được những chi tiết mà 15 con số tóm tắt bỏ sót.
- **Mô hình ghép:** để mỗi bộ não lo phần mình giỏi nhất. LSTM lo vuốt, rừng lo zoom (mục 7).

### 1.4. Dữ liệu học: IPN Hand

- Các mô hình học từ **IPN Hand**, một bộ 200 video quay sẵn, có người diễn làm cử chỉ và có ghi
  sẵn đoạn nào là cử chỉ gì.
- Dữ liệu được **chia theo người**:
  - người của tập học (train) không bao giờ xuất hiện trong tập dùng để chấm khi đang làm (val);
  - tập kiểm tra cuối (test) bị khoá tới lần chạy cuối cùng.
- Chia theo người để con số không "ăn gian": mô hình phải nhận được tay của **người lạ**, không
  phải tay của người nó đã gặp.
- **Hệ quả quan trọng:** mô hình học cử chỉ **theo cách người diễn IPN làm**. Người dùng làm khác
  đi thì mô hình có thể không nhận ra. Đây là sợi chỉ đỏ của cả Phase 10.

### 1.5. Đo "tốt" như thế nào

**Hai câu hỏi người dùng thật sự quan tâm:**

- Tôi làm cử chỉ, nó có nhận không? Đó là **recall**: tỉ lệ cử chỉ thật được nhận.
- Tôi không làm gì, nó có tự đổi slide không? Đó là **lệnh nhầm mỗi phút**.

Ngoài ra còn hai con số:

- **Precision:** trong các lệnh phát ra, bao nhiêu phần là đúng.
- **F1:** một con số gộp precision và recall, từ 0 đến 1. Nó chỉ cao khi cả hai cùng cao.

**Hai mức chấm:**

- **Mức cửa sổ:** chấm từng đoạn 1,2 giây, như chấm từng tấm ảnh chụp.
- **Mức sự kiện:** chấm cả hệ thống như người dùng thấy, tức đếm **lệnh** phát ra.
  - Lệnh đúng là lệnh đúng loại, phát trong lúc cử chỉ diễn ra hoặc tới 1 giây sau đó.
  - Phép chấm chạy trên 27 video kiểm định của IPN: 60 phút, 108 cử chỉ.

Từ Phase 8, mức sự kiện là thước đo chính.

---

## 2. Nếp làm việc: đo trước, sửa sau

Mọi vòng tối ưu bên dưới đều theo bốn nguyên tắc.

1. **Ghi một lần, chấm mọi cấu hình**, như hộp đen trên máy bay.
   - Mỗi lần thử trên webcam, hệ thống ghi lại 21 chấm của từng ảnh.
   - Sau đó có thể "phát lại" phiên đó qua bất kỳ mô hình hay ngưỡng nào, kết quả y như chạy
     thật. Phase 7 đã kiểm: phát lại trùng 316 trên 316 câu trả lời.
   - Nhờ vậy, so mười cấu hình không cần người dùng làm lại mười lần.
2. **Tìm nguyên nhân bằng số đo, không đoán.** Khi có gì sai, mình đo trực tiếp trên 21 chấm:
   - ngón tay gập hay duỗi;
   - ngón cái cách ngón trỏ bao xa theo thời gian;
   - mô hình nói gì ở từng nhịp 0,2 giây.
3. **Mỗi thay đổi chấm trên bốn nguồn**, để sửa chỗ này không làm hỏng chỗ khác:
   - 27 video kiểm định của IPN;
   - 40 lời nhắc cử chỉ người dùng làm trước webcam: màn hình hiện "vuốt trái", người dùng làm;
   - gần 11 phút người dùng nói chuyện có khua tay, không làm cử chỉ nào;
   - các lần thử trên slide thật.
4. **Người dùng chọn điểm đánh đổi.** Thường không có cấu hình tốt nhất về mọi mặt. Mình đo và
   bày bảng, người dùng quyết.

---

## 3. Vòng 1 — Dạy hệ thống biết im lặng (Phase 8–9)

### Chuyện gì không ổn

Hình dung mô hình như **một bình luận viên** nhìn bàn tay và hô lên 5 lần mỗi giây:

> "vuốt trái!… vuốt trái!… không có gì!… vuốt trái!… vuốt trái!…"

Nếu mỗi tiếng hô là một lần bấm phím, một cú vuốt sẽ lật qua cả chục slide. Phase 8 đo đúng
chuyện này trên video kiểm định:

- hệ thống **bắt được** 82–94% cử chỉ;
- nhưng phát **6,6 đến 30 lệnh nhầm mỗi phút**: chỉ 5–20% số lệnh là đúng.

### Sửa thế nào: máy trạng thái

Mình đặt giữa bình luận viên và bàn phím **một người trợ lý cẩn thận**. Người này có bốn trạng
thái, giống đèn giao thông chỉ có vài màu:

| Trạng thái | Nghĩa |
|---|---|
| Chờ tay | chưa thấy bàn tay nào |
| Sẵn sàng | thấy tay, đang lắng nghe |
| Đang cân nhắc | vừa nghe một tiếng hô đủ chắc; đang chờ thêm tiếng hô cùng ý |
| Nghỉ | vừa bấm phím, nghỉ 1,2 giây |

Và bốn quy tắc:

1. **Phải đủ chắc mới bắt đầu cân nhắc** (ngưỡng độ tin). Tiếng hô ngập ngừng thì bỏ qua.
2. **Phải nghe đủ số tiếng hô cùng ý trong 5 tiếng liền** mới bấm phím (đồng thuận). Ví dụ "4
   trên 5": 4 trong 5 cửa sổ liền nhau phải đồng ý.
3. **Bấm xong thì nghỉ 1,2 giây**, như chuông cửa chỉ reo một lần dù bạn ấn hơi lâu.
4. **Hạ tay ra khỏi khung là huỷ hết.** Trợ lý quên mọi thứ đang cân nhắc.

### Một lỗi thiết kế đã tránh

- Cách hiểu đầu tiên của quy tắc 2 là "đếm số tiếng hô cùng ý trong 5 tiếng gần nhất".
- Theo cách đó, chuỗi nhấp nháy *vuốt, không có gì, vuốt, không có gì, vuốt* có 3 trên 5 tiếng
  "vuốt", và sẽ bấm phím. Đó là một lệnh từ tín hiệu rất yếu.
- Bản dùng thật coi một tiếng hô **khác ý mà đủ chắc**, kể cả "không có gì", là **phiếu phản đối**.
  Nó huỷ ngay việc cân nhắc.

### Được gì

Ở ngưỡng khởi đầu (độ tin 0,75, đồng thuận 3 trên 5), trên video kiểm định:

| Bộ não | F1 sự kiện | Lệnh nhầm mỗi phút |
|---|---|---|
| LSTM | 0,559 | 1,46 |
| Mô hình ghép | 0,490 | 1,33 |
| Rừng | 0,405 | 0,50 |
| Luật | 0,130 | 6,82 |

Lệnh nhầm giảm từ hàng chục xuống khoảng 1–1,5 lần mỗi phút với hai bộ não tốt nhất.

### Mất gì

Trợ lý cẩn thận thì đôi khi **bỏ lỡ** cử chỉ thật. Chỉ còn 0,77 lệnh trên mỗi cử chỉ, trong khi
yêu cầu đặt ra là 0,9–1,1.

### Một đánh đổi nữa: "phải thấy tay bao nhiêu"

- Cửa sổ 1,2 giây chỉ được xét khi ít nhất 70% số ảnh trong đó thấy bàn tay.
- Đòi 100% thì bớt được lệnh nhầm lúc tay đang đưa vào khung. Nhưng cú vuốt nhanh lại hay làm mất
  tay vài ảnh, nên bị bỏ lỡ.
- Đo trên video: nâng lên 100% mất 3 trong 54 cú vuốt, mà lệnh nhầm chỉ giảm 3%. Vì vậy giữ 70%.

---

## 4. Vòng 2 — Sửa thước đo trước khi sửa hệ thống (Phase 10)

Khi bắt đầu đo trên webcam, mình phát hiện **ba con số đánh lừa**. Tối ưu theo một thước sai thì
càng cố càng lệch, nên phải sửa thước trước.

**1. Đồng hồ bấm giờ bắt đầu sai lúc.**

- Để đo độ trễ (từ lúc làm cử chỉ tới lúc slide đổi), ta cần biết chính xác lúc cử chỉ diễn ra.
- Trên webcam, mỗi lời nhắc dài 4 giây, gồm cả lúc đưa tay lên chuẩn bị và lúc thu tay về. Chuyển
  động lớn nhất trong đó nhiều khi là lúc **thu tay**, nên đồng hồ bấm muộn và độ trễ ra số âm.
- **Sửa:** đo độ trễ trên video IPN, nơi người ta đã đánh dấu sẵn khoảnh khắc chính của từng cử
  chỉ.

**2. Một điểm số "hoàn hảo" che giấu hai lỗi.**

- Lần chấm đầu cho đúng **1,00 lệnh trên mỗi cử chỉ**, nghe như lý tưởng.
- Nhưng recall chỉ 0,55: gần một nửa số cử chỉ bị bỏ lỡ, và số lệnh thừa (phát nhầm, phát trùng)
  vừa khéo bù lại.
- **Sửa:** luôn báo kèm tỉ lệ nhận đúng, số lệnh trên mỗi lời nhắc, và số lệnh phát trùng.

**3. Trung bình sai cách, và chia cho số phút sai.**

- Con số "nhầm mỗi phút" chung từng là trung bình cộng của ba kịch bản: đọc tài liệu, gõ phím, nói
  chuyện. Lúc đọc và gõ phím, tay nằm ngoài khung nên luôn ra 0, kéo cả con số xuống. Với bộ
  luật: 7,39 thành 2,46.
- Một phiên nói chuyện 0,9 phút lại được tính nặng ngang một phiên 10 phút.
- **Sửa:**
  - cộng tổng số lệnh nhầm rồi chia cho tổng số phút;
  - thêm cột **nhầm mỗi phút có tay**, vì hệ thống chỉ có thể nhầm khi thấy tay. Phiên 10 phút
    thấy tay 17% thời gian, phiên 0,9 phút thấy tay 89%.

---

## 5. Vòng 3 — Mô hình cho bàn tay thật của người dùng (Phase 10)

### Chuyện gì không ổn

Trên tay người dùng, bộ não LSTM lúc đó (`run_07`) **không nhận được cú zoom nào**: 0 trên 10.
Tệ hơn, khi bàn tay chỉ đang chụm đứng yên, nó lại hô "vuốt": 4 lệnh vuốt nhầm trong 1,1 phút tập
zoom.

### Tìm nguyên nhân

- Mình đo **độ duỗi** của từng ngón: khoảng cách đầu ngón tới cổ tay, chia cho khoảng cách gốc
  ngón tới cổ tay. Ngón gập vào lòng bàn tay cho khoảng 0,5; ngón duỗi thẳng cho khoảng 1,3–1,5.
- Người diễn IPN khi zoom **gập ngón nhẫn và ngón út**: độ duỗi khoảng 0,5.
- Người dùng để hai ngón đó **duỗi**: độ duỗi 1,5–2,1.
- LSTM học rằng "zoom là ngón cái, trỏ, giữa cử động, còn nhẫn và út gập". Gặp bàn tay có nhẫn, út
  duỗi, nó không nhận ra đó là zoom.

### Sửa thế nào: cho mô hình học thêm nhiều kiểu tay

Dùng một lần học khác của LSTM (`run_08`). Lần này mô hình được học thêm hai loại **ví dụ biến
tấu**, tạo ra từ chính dữ liệu IPN:

- **Đổi dáng ngón phụ:** lấy một nửa số ví dụ zoom, ghép vào đó dáng ngón giữa, nhẫn, út của
  **một bàn tay IPN khác**. Mô hình học rằng ngón phụ có thể ở nhiều tư thế.
- **Bàn tay đứng yên:** thêm ví dụ bàn tay giữ nguyên một tư thế, gắn nhãn "không có gì". Mô hình
  học rằng tay chụm đứng yên không phải là vuốt.

### Được gì

| Cùng dữ liệu, cùng ngưỡng | Trước (`run_07`) | Sau (`run_08`) |
|---|---|---|
| Zoom trên webcam | 0 trên 10 | 4 trên 10 |
| Phiên tập zoom: phóng to / thu nhỏ / vuốt nhầm | 0 / 2 / 4 | 5 / 5 / **0** |
| Video IPN, sửa cho nhẫn, út duỗi thẳng: zoom còn được nhận | 10% / 35% | 95% / 95% |
| F1 sự kiện trên video kiểm định | 0,559 | 0,554, gần như giữ nguyên |

### Mất gì

- Mô hình giờ "dễ dãi" hơn với zoom, nên đôi khi tưởng bàn tay đang chỉ trỏ là zoom.
- Khi người dùng nói chuyện, LSTM một mình phát thêm 5 lệnh thu nhỏ nhầm. Bù lại, vuốt nhầm giảm
  từ 8 xuống 2 lệnh.

### Đi kèm: màn hình tập luyện

Chế độ `--show-features` (bấm phím 3 hoặc 4) hiện độ duỗi nhẫn, út của chính người dùng, đặt cạnh
khoảng của người diễn IPN (0,4–0,7). Màu xanh là đã gập như IPN.

---

## 6. Vòng 4 — Chặn cú "lấy đà" (Phase 10)

### Chuyện gì không ổn

Cứ 20 lần vuốt thì 5 lần slide đi **ngược chiều**.

### Tìm nguyên nhân

Mình in ra lời hô của mô hình ở từng nhịp 0,2 giây trong một lần người dùng vuốt sang phải (R là
"vuốt phải", L là "vuốt trái", chấm là "không có gì"):

```
R R · L L L R R R R R
```

- Trước khi hất tay sang phải, người dùng **kéo tay sang trái lấy đà**, như người đánh tennis vung
  vợt về sau trước khi đánh.
- Bản thân đoạn kéo đó **là một cú vuốt trái**, và mô hình nhận đúng như vậy, với độ tin **1,00**.
- Trợ lý nghe ba tiếng "L" liền nhau, đủ đồng thuận, nên bấm "vuốt trái". Rồi nó vào 1,2 giây
  nghỉ, đúng lúc người dùng hất tay thật sang phải. Cú vuốt thật bị bỏ qua.
- **Nâng ngưỡng độ tin không giúp gì,** vì đoạn lấy đà cũng "chắc chắn" như cú vuốt thật.

### Sửa thế nào: đòi đồng thuận lâu hơn

- Đoạn lấy đà **ngắn**, chỉ khoảng 3 nhịp. Cú hất thật dài hơn: 4–5 nhịp.
- Đòi **4 trên 5 nhịp** đồng ý (thay vì 3 trên 5) thì đoạn lấy đà không đủ phiếu, còn cú hất thật
  vẫn đủ. Ngưỡng độ tin cũng nâng từ 0,75 lên 0,85.

| | Trước: 0,75 và 3 trên 5 | **Sau: 0,85 và 4 trên 5** |
|---|---|---|
| Vuốt mà slide đi ngược chiều | 5 trên 20 | **2 trên 20** |
| Slide tự đổi khi nói chuyện | 0,64 lần mỗi phút | **0,18 lần mỗi phút** |
| F1 sự kiện trên video kiểm định | 0,554 | **0,600** |
| Lệnh nhầm mỗi phút trên video kiểm định | 1,63 | **0,77** |
| Vuốt được nhận trên webcam | 60% | 55% |
| Zoom được nhận trên webcam | 40% | 20% ← cái giá |
| Độ trễ | 0,62 giây | 0,76 giây |

Màn hình trợ giúp và tài liệu cử chỉ thêm câu **"không lấy đà ngược chiều"**.

---

## 7. Vòng 5 — Ngưỡng riêng cho zoom (Phase 10)

### Chuyện gì không ổn

Lần đầu điều khiển slide thật, 32 giây: 4 trên 4 lần vuốt đổi slide được, nhưng **0 trên 12 cú
zoom** thành lệnh. Màn hình vẫn hiện chữ "zoom" mà slide không phóng to.

### Tìm nguyên nhân (từ hộp đen của chính lần thử đó)

**Động tác của người dùng rất sạch.** Khoảng cách ngón cái – ngón trỏ đi giữa 0,1 và 1,7 lòng bàn
tay: chụm sát rồi mở rộng, đổi trong 0,2–0,4 giây rồi giữ yên.

**LSTM chắc chắn quá muộn.** Độ tin của nó trong năm nhịp liền của một cú thu nhỏ:

```
0,52  0,47  0,61  0,88  0,96
```

Ngưỡng là 0,85, nên trợ lý chỉ bắt đầu cân nhắc từ nhịp thứ tư. Nó cần 4 phiếu nhưng chỉ còn hai
nhịp, nên không bao giờ đủ.

**Rừng ngẫu nhiên nhận đúng cả 12 trên 12 cú, nhưng "nói nhỏ".** Trên cùng cú đó, rừng nói:

```
(chưa nhận ra)  0,61  0,62  0,61  0,67
```

Từ nhịp thứ hai trở đi, nó gọi đúng "thu nhỏ" ở mọi nhịp, nhưng không bao giờ "chắc" kiểu 0,9. Với
phóng to, độ tin còn thấp hơn: 0,33–0,56.

Hình dung **hai giám khảo**:

- một người (LSTM) nói rất to khi đã chắc, nhưng chắc muộn;
- một người (rừng) luôn đúng nhưng luôn nói nhỏ.

Dùng **một** ngưỡng "độ to" chung cho cả hai là không công bằng.

**Không thể đơn giản hạ ngưỡng chung xuống.** Quay về 0,75 và 3 trên 5 thì cú lấy đà của vuốt
(vòng 4) lại lọt qua.

### Sửa thế nào: mỗi loại cử chỉ một luật riêng

- **Vuốt:** vẫn nghe LSTM, vẫn đòi 0,85 và 4 trên 5. Cú lấy đà vẫn bị chặn.
- **Zoom:** nghe rừng ngẫu nhiên, với ngưỡng riêng hợp với giọng "nói nhỏ" của nó.

Mình thử nhiều mức trên cả bốn nguồn dữ liệu trước khi người dùng chọn:

| Zoom theo | Thử slide thật | 20 lời nhắc zoom: đúng / ngược / bỏ lỡ | Lệnh mỗi lời nhắc | Nhầm khi nói chuyện, mỗi phút |
|---|---|---|---|---|
| LSTM, 0,85 và 4/5 (trước) | 0 trên 12 | 4 / 1 / 15 | 0,62 | 0,18 |
| **Rừng, 0,40 và 3/5 (chọn)** | 6 trên 12 | **10 / 4 / 6** | **1,00** | **0,18** |
| Rừng, 0,40 và 2/5 | 8 trên 12 | 16 / 4 / 0 | 1,48 | 0,27 |
| Rừng, 0,50 và 3/5 | 5 trên 12 | 10 / 2 / 8 | 0,90 | 0,18 |

- **Vì sao 0,40 mà không phải 0,50:** với phóng to, rừng thường chỉ chắc khoảng 0,33–0,56. Ở
  ngưỡng 0,50, không cú phóng to nào thành lệnh khi thử trực tiếp.
- **Vì sao 3 trên 5 mà không phải 2 trên 5:** với 2 trên 5, zoom gần như không bị bỏ lỡ, nhưng lệnh
  thừa tăng mạnh (1,48 lệnh mỗi lời nhắc). Phần lớn là lúc người dùng đưa tay vào tư thế chuẩn bị,
  hoặc lúc thả lỏng tay sau cử chỉ.
- **Vì sao chỉ 6 trên 12:** người dùng đổi chiều zoom mỗi khoảng 1,3 giây, trong khi mỗi lệnh cần
  khoảng 1,8 giây (khoảng 0,6 giây gom phiếu, cộng 1,2 giây nghỉ). Tắt thời gian nghỉ thì cùng cấu
  hình nhận được 9 trên 12.

### Được gì

- Phát lại đúng lần thử thất bại: **6 cú zoom thành lệnh, cả 6 đúng chiều**.
- Lần thử thứ hai, 92 giây: **19 lệnh** (8 vuốt, 11 zoom), mọi phím đều tới PowerPoint. Người dùng
  đánh giá "tạm ổn".
- Lần đầu tiên số lệnh trên mỗi lời nhắc vào khoảng yêu cầu 0,9–1,1 (đạt 1,00), mà slide không tự
  đổi nhiều hơn khi người dùng nói chuyện.

### Mất gì

- Điểm F1 trên video kiểm định giảm từ 0,600 xuống 0,561.
- Thiết kế gốc của dự án dùng **một** ngưỡng chung cho mọi cử chỉ. Đây là một thay đổi thiết kế,
  và người dùng đã chọn nó.

---

## 8. Vòng 6 — Cho việc điều khiển dễ dùng hơn (Phase 10)

- **Phím đi nhầm chỗ.**
  - Lần thử slide đầu, không có gì xảy ra trên slide, vì phím được gửi vào cửa sổ đang được chọn,
    mà đó là cửa sổ của demo.
  - Sửa: cửa sổ demo luôn nằm trên cùng, để người dùng bấm chuột vào cửa sổ trình chiếu mà vẫn
    thấy demo. Màn hình nhắc việc đó ngay khi bật điều khiển.
- **Phím zoom cho PowerPoint:** lúc trình chiếu, PowerPoint phóng to bằng `+` và thu nhỏ bằng `−`.
  Google Slides và trình đọc PDF thì dùng Ctrl + và Ctrl −.
- **Chiều vuốt theo ý người dùng:** vuốt trái sang slide sau, như lật trang trên điện thoại. Thiết
  kế gốc làm ngược lại.
- **Nhịp làm cử chỉ.** Từ các số đo trên, màn hình trợ giúp (phím `?`) và `docs/gestures.md` thêm
  bốn lời khuyên:
  - **không lấy đà ngược chiều** (vòng 4);
  - **giơ tay lên khoảng 1 giây rồi mới làm.** Cửa sổ 1,2 giây chỉ được xét khi 70% số ảnh trong
    đó thấy tay; làm ngay lúc tay vừa vào khung thì hệ thống chưa kịp thấy;
  - **zoom xong giữ yên khoảng 1 giây.** Mở rồi chụm lại ngay chỉ tạo khoảng hai nhịp rõ ràng,
    không đủ ba phiếu;
  - **các cử chỉ cách nhau khoảng 2 giây,** vì mỗi lệnh chiếm khoảng 1,8 giây.
- **Đưa tay ra khỏi khung rồi vào lại không sinh lệnh lạ:** kiểm trên 66 lần tay vào lại khung
  trong các phiên đã ghi.

---

## 9. Những thứ giúp tối ưu nhanh

Sáu vòng trên làm được trong vài ngày là nhờ ba thứ dựng từ trước.

- **Kết quả thí nghiệm được lưu lại kèm "tem niêm phong".**
  - Phase 8 có 46 thí nghiệm, học một lần mất 170 phút.
  - Mỗi kết quả lưu kèm một "tem" ghi lại công thức đã dùng. Khi chỉ đổi luật của người trợ lý (vòng
    1, 4, 5), mô hình không đổi, tem còn nguyên, nên dựng lại bảy bảng kết quả chỉ mất **0,8 phút**.
  - Hai lần, một thông số mới không liên quan suýt làm "rách tem" cả 46 kết quả, tức phải học lại
    170 phút. Cả hai lần đều bị phát hiện trước khi chạy, và nay có kiểm thử tự động chặn.
- **Hộp đen của mỗi lần thử.** Phiên webcam và lần thử slide đều lưu 21 chấm. Đó là cách mình có
  con số "0 thành 6 trên 12" ở vòng 5 mà không cần người dùng thử lại.
- **Một lệnh dựng lại tất cả** (`scripts/run_all.py`), cho phần bàn giao. Đi kèm:
  - mô hình của demo có chỗ cố định;
  - danh sách thư viện ghi rõ từng phiên bản.

### Các quyết định của người dùng

| Ngày | Quyết định |
|---|---|
| 25/10 | Giữ ngưỡng khởi đầu cho Phase 9; chọn cấu hình cuối ở Phase 10 bằng số đo trên webcam |
| 26/10 | Đổi sang LSTM `run_08`; tập gập nhẫn, út |
| 26/10 | Không ghi lại phiên đọc tài liệu và gõ phím: lúc đó camera không thấy tay |
| 26/10 | Ngưỡng 0,85 và 4 trên 5 (vòng 4) |
| 01/11 | Mô hình ghép; ngưỡng riêng cho zoom 0,40 và 3 trên 5; phím `+` / `−` (vòng 5) |
| 02/11 | Vuốt trái sang slide sau, vuốt phải về slide trước |

---

## 10. Những gì tối ưu chưa giải quyết được

- **Khoảng một nửa số cử chỉ vẫn bị bỏ lỡ ở lần làm đầu.** Trên 40 lời nhắc:
  - vuốt: 11 đúng, 2 ngược chiều, 7 bỏ lỡ;
  - zoom: 10 đúng, 4 ngược chiều, 6 bỏ lỡ.

  Phần lớn do người dùng làm khác người diễn IPN: nhẫn, út duỗi; lấy đà; đưa tay vào khung muộn.
  Không ngưỡng nào sửa hết được, nên phần còn lại là tập luyện theo `docs/gestures.md`.
- **Ngưỡng zoom được chọn trên ít dữ liệu:** 40 lời nhắc và 12 cú zoom. Chính dữ liệu đó lại dùng
  để chấm, nên các con số có phần lạc quan.
- **Trên video IPN, bộ não tốt nhất tuỳ cách đo.**
  - Học lại nhiều lần từ đầu, theo công thức gốc, LSTM một mình hơn mô hình ghép.
  - Với mô hình đang dùng thì mô hình ghép hơn: 0,561 so với 0,507.
  - Mô hình ghép được chọn vì kết quả trên webcam của người dùng.
- **Một yêu cầu của Phase 9 vẫn chưa đạt:** trên video IPN, mô hình ghép phát 0,61 lệnh mỗi cử chỉ,
  chưa tới 0,9.
- **Bài học về độ tin của con số.**
  - Khi chỉ chạy một lần, chênh lệch nhỏ (dưới khoảng 0,1 F1) thường đảo chiều khi đổi luật của
    người trợ lý.
  - Chỉ những kết luận lặp lại qua nhiều lần học, hoặc nhiều nhóm người, mới đáng tin. Ba kết luận
    như vậy đứng vững qua mọi lần dựng lại bảng:
    - LSTM hơn rừng;
    - trộn ngẫu nhiên người vào cả tập học lẫn tập chấm làm điểm số đẹp giả thêm 0,10–0,15;
    - rừng cần đặt gốc toạ độ ở cổ tay của ảnh đầu cửa sổ, và cửa sổ dài 1,2 giây.

---

## 11. Việc còn lại

1. **Đo tốc độ** cho cả bốn bộ não, ở hai mức ánh sáng, rồi đo lại lần hai. Lần đo đầu: khoảng 30
   ảnh mỗi giây; xử lý một ảnh mất khoảng 16 mili-giây, ba phần tư trong đó là MediaPipe tìm bàn
   tay.
2. **Đo độ trễ bằng tay:** quay video cả webcam lẫn màn hình, đếm từng khung hình, 10 lần mỗi cử
   chỉ.
3. **Quay video demo**, kèm ghi chú những lúc hệ thống làm sai.
4. **Quyết định có quay thêm dữ liệu của chính người dùng không** (Phase 11,
   `results/phase6/live_check.md`), và duyệt `docs/gestures.md`.
5. **Cuối cùng, đúng một lần:**
   - mở khoá tập test để chấm lần cuối;
   - thử dựng lại toàn bộ môi trường từ README trên máy sạch.

---

## Phụ lục A — Thuật ngữ

| Từ | Nghĩa trong tài liệu này |
|---|---|
| Điểm mốc, 21 điểm | toạ độ cổ tay, các khớp và đầu ngón, do MediaPipe tìm trong mỗi ảnh |
| Cửa sổ | đoạn 1,2 giây gần nhất của 21 điểm; cứ 0,2 giây xét một cửa sổ mới |
| Nhãn | câu trả lời của mô hình cho một cửa sổ: cử chỉ nào, hay "không có gì" |
| Độ tin | mô hình chắc tới đâu về nhãn đó, từ 0 đến 1 |
| Lệnh | một lần thật sự bấm phím; do máy trạng thái quyết định |
| Máy trạng thái | "người trợ lý" giữa mô hình và bàn phím (mục 3) |
| Ngưỡng độ tin | độ tin tối thiểu để bắt đầu cân nhắc một lệnh |
| Đồng thuận k trên n | cần k nhịp đồng ý trong n nhịp liền nhau mới phát lệnh |
| Thời gian nghỉ | 1,2 giây sau mỗi lệnh, không phát lệnh mới |
| Recall | tỉ lệ cử chỉ thật được nhận |
| Precision | tỉ lệ lệnh phát ra là đúng |
| F1 | một con số gộp precision và recall, từ 0 đến 1 |
| Lệnh nhầm mỗi phút | số lần hệ thống tự phát lệnh khi không có cử chỉ |
| Mức cửa sổ / mức sự kiện | chấm từng đoạn 1,2 giây / chấm từng lệnh như người dùng thấy |
| IPN Hand | bộ 200 video cử chỉ quay sẵn mà các mô hình học theo |
| Tập học / kiểm định / test | dữ liệu để học / để chấm khi đang làm / khoá tới lần chấm cuối; chia theo người |
| Rừng ngẫu nhiên | hàng trăm cây quyết định bỏ phiếu trên 15 con số tóm tắt cửa sổ |
| LSTM | mạng nơ-ron đọc cả chuỗi chuyển động, từng bước một |
| Mô hình ghép | LSTM lo vuốt, rừng lo zoom |
| Độ duỗi ngón | khoảng cách đầu ngón tới cổ tay, chia khoảng cách gốc ngón tới cổ tay; gập ≈ 0,5, thẳng ≈ 1,3–1,5 |
| Lấy đà | kéo tay ngược chiều trước khi vuốt, như vung vợt về sau |
| Ví dụ biến tấu (tăng cường dữ liệu) | ví dụ học tạo ra bằng cách sửa ví dụ thật, để mô hình gặp nhiều kiểu hơn |
| Hộp đen (ghi và phát lại) | lưu 21 điểm của một phiên để chạy lại qua mọi cấu hình |

---

## Phụ lục B — Dành cho người làm kỹ thuật

### Cấu hình cuối (`src/config.py`)

| Hằng số | Giá trị |
|---|---|
| Mô hình | `demo.py --model hybrid`: vuốt theo LSTM `results/phase10/lstm_model.pt` (bản sao của `train_lstm/run_08`), zoom theo `results/phase6/rf_model.joblib` |
| `CONF_FIRE`, `K_OF_N`, `CONF_HOLD` (vuốt) | 0,85; (4, 5); 0,55 |
| `FSM_ZOOM_FIRE`, `FSM_ZOOM_K` (zoom) | 0,40; 3 |
| `COOLDOWN_SEC`, `MIN_PRESENCE` | 1,2 giây; 0,7 |
| `CTRL_HOTKEYS` | vuốt trái → mũi tên phải; vuốt phải → mũi tên trái; zoom `+` / `−` |

### Số liệu lấy từ đâu

| Nội dung | Ở đâu |
|---|---|
| Bảy bảng Phase 8, cấu hình cuối | `results/phase8/experiments/run_04` |
| Bảng so sánh bốn mô hình | `results/model_comparison.md` |
| Bảng đánh đổi trên webcam và video kiểm định | `results/phase10/analyze/run_07` |
| Lý do và cái giá của cấu hình cuối | `results/phase10/final_config.md` |
| Diễn biến chi tiết từng vòng | `results/phase10/notes.md` |
| Các phiên webcam và lần thử slide | `results/phase10/sessions/`, `results/phase10/live_final*.csv` |

### Lệnh chính

```
python scripts/demo.py --model hybrid --log <file.csv>   # demo, ghi hộp đen để phát lại
python scripts/demo.py --model hybrid --show-features    # tập cử chỉ theo IPN
python scripts/bench.py record gestures                  # ghi 20 lời nhắc
python scripts/bench.py analyze                          # chấm mọi cấu hình
python scripts/run_all.py --list                         # trạng thái toàn bộ đường ống
```
