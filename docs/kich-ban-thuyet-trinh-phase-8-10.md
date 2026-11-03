# Kịch bản thuyết trình — Phase 8–10: Tối ưu hệ thống

**Nguồn:** `docs/tong-ket-phase-8-10.md` (bản cập nhật 02/11/2026).

**Chủ đề:** từ nhãn trên màn hình tới lệnh điều khiển slide — sáu vòng tối ưu, mỗi vòng gồm vấn
đề, chẩn đoán bằng số đo, cách sửa, kết quả và cái giá.

**Thời lượng dự kiến:** khoảng 18 phút trình bày, 2 phút demo trực tiếp, sau đó hỏi đáp.

**Cấu trúc:** 18 slide. Mỗi slide gồm: *trên slide* (nội dung hiển thị), *lời nói* (đọc hoặc nói
theo ý), và *ghi chú* (nhắc riêng cho người trình bày). Bộ slide đi kèm:
`docs/thuyet-trinh-phase-8-10.pptx` — phần lời nói và ghi chú nằm trong speaker notes.

---

## Chuẩn bị trước buổi

- Mở sẵn PowerPoint có khoảng 8–10 slide để demo, đặt ở chế độ trình chiếu.
- Mở terminal, đã kích hoạt env `action-recognition`, gõ sẵn lệnh:
  `python scripts/demo.py --model hybrid`.
- Sau khi bấm `c` bật điều khiển, **bấm chuột vào cửa sổ trình chiếu** — nếu không, phím sẽ đi vào
  cửa sổ demo (đây chính là lỗi của lần thử slide đầu tiên, vòng 6).
- Kiểm tra ánh sáng và webcam: tay phải nằm gọn trong khung, nền không quá rối.
- **Phương án dự phòng:** nếu demo trực tiếp hỏng, chiếu lại log `results/phase10/live_final2.csv`
  (92 giây, 19 lệnh) hoặc video quay trước. Nên quay video dự phòng trước buổi — việc này cũng nằm
  trong danh sách còn lại.
- Tự nhắc nhịp làm cử chỉ: không lấy đà ngược chiều, giơ tay khoảng 1 giây rồi mới làm, zoom xong
  giữ yên khoảng 1 giây, các cử chỉ cách nhau khoảng 2 giây.

---

## Slide 1 — Mở đầu (0:30)

**Trên slide:**
- Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính
- Phase 8–10 · Tối ưu hệ thống: từ nhãn trên màn hình tới lệnh điều khiển slide

**Lời nói:**

> Xin chào thầy cô và các bạn. Đề tài của em là nhận dạng cử chỉ bàn tay thời gian thực để điều
> khiển máy tính. Buổi trước em đã trình bày đến Phase 7, khi các mô hình đã gán nhãn được cử chỉ.
> Hôm nay em kể ba phase tiếp theo dưới một góc nhìn: hệ thống đã được tối ưu lại thế nào để đi từ
> nhãn hiện trên màn hình tới lệnh điều khiển slide thật.

---

## Slide 2 — Nhãn chưa phải là lệnh (1:00)

**Trên slide:**
- Hết Phase 7: mô hình **gán nhãn** cho từng cửa sổ 1,2 giây
- Người dùng cần **lệnh**: mỗi cử chỉ đúng một lần đổi slide; không lệnh nào khi chỉ nói chuyện
- Phase 8 đo khoảng cách → Phase 9–10 thu hẹp qua **sáu vòng tối ưu**:
  1. Máy trạng thái · 2. Sửa thước đo · 3. LSTM `run_08` · 4. Chặn lấy đà · 5. Tách ngưỡng zoom ·
  6. Trải nghiệm điều khiển

**Lời nói:**

> Hết Phase 7, mô hình đã gán nhãn được cho từng cửa sổ 1,2 giây. Nhưng người dùng không cần nhãn,
> họ cần lệnh: mỗi cử chỉ đúng một lần đổi slide, và không có lệnh nào khi họ chỉ đang nói chuyện.
>
> Phase 8 đo khoảng cách giữa hai việc đó. Phase 9 và 10 thu hẹp nó qua sáu vòng tối ưu: thêm máy
> trạng thái, sửa thước đo, đổi mô hình cho hợp bàn tay thật, chặn động tác lấy đà, tách ngưỡng
> riêng cho zoom, và cuối cùng là trải nghiệm điều khiển.

---

## Slide 3 — Tối ưu được bao nhiêu (1:15)

**Trên slide:**

| Chỉ số | Điểm xuất phát | Hiện tại |
|---|---|---|
| Lệnh nhầm mỗi phút, video val IPN | 6,6–30 | **0,85** |
| Lệnh nhầm mỗi phút khi nói chuyện có khua tay | 0,64 | **0,18** |
| Lời nhắc vuốt phát ngược chiều trước | 5/20 | **2/20** |
| Zoom nhận đúng trên tay người dùng | 0/10 | **10/20** |
| Thử slide thật: cú zoom thành lệnh | 0/12 | **6/12** |
| F1 sự kiện trên video val | 0,559 | 0,561 — giữ ngang |

- Cấu hình đang dùng: vuốt ← LSTM (0,85 · 4/5), zoom ← rừng ngẫu nhiên (0,40 · 3/5)

**Lời nói:**

> Em đưa kết quả lên trước. Trên video val của IPN, lệnh nhầm giảm từ 6,6–30 lệnh mỗi phút xuống
> 0,85. Khi nói chuyện có khua tay trước webcam, từ 0,64 xuống 0,18 mỗi phút, tức hơn 5 phút mới có
> một lệnh nhầm. Vuốt phát ngược chiều giảm từ 5 xuống 2 trên 20 lời nhắc. Zoom trên tay em đi từ
> không nhận được cú nào lên 10 trên 20. Khi thử slide thật, số cú zoom thành lệnh từ 0 lên 6 trên
> 12. Và trong lúc đó, F1 sự kiện trên video val được giữ ngang, 0,559 và 0,561.
>
> Cấu hình đang dùng là một mô hình ghép: vuốt theo LSTM, zoom theo rừng ngẫu nhiên, mỗi họ cử chỉ
> một ngưỡng riêng. Phần còn lại của bài là câu chuyện sáu vòng tối ưu dẫn tới đây.

**Ghi chú:** zoom 0/10 là LSTM `run_07` trên 10 lời nhắc; 10/20 là cấu hình cuối trên 20 lời nhắc
zoom. `pytest -q`: 215 passed.

---

## Slide 4 — Cách làm: đo trước, sửa sau (1:15)

**Trên slide:**
- **Ghi một lần, chấm mọi cấu hình:** phiên webcam ghi thành điểm mốc thô, chạy lại qua đúng đường
  ống của demo (trùng 316/316 câu trả lời lúc chạy thật)
- **Chẩn đoán bằng số đo trên điểm mốc:** khoảng cách cái–trỏ, độ duỗi ngón, góc khớp, chuỗi nhãn
  và độ tin từng nhịp 0,2 giây
- **Mỗi thay đổi chấm trên bốn nguồn:** 27 video val IPN (60 phút, 108 cử chỉ) · 40 lời nhắc cử chỉ
  · 10,9 phút nói chuyện · các lần thử slide thật
- **Người dùng chọn điểm đánh đổi** từ bảng số đo

**Lời nói:**

> Mọi vòng tối ưu đều theo cùng một nếp: đo trước, sửa sau.
>
> Thứ nhất, ghi một lần, chấm mọi cấu hình. Phiên webcam được ghi thành điểm mốc bàn tay thô, rồi
> chạy lại qua đúng đường ống của demo. Ở Phase 7 em đã kiểm: chạy lại trùng 316 trên 316 câu trả
> lời lúc chạy thật. Nhờ vậy một lần ghi đủ để so mọi mô hình và mọi ngưỡng.
>
> Thứ hai, chẩn đoán bằng số đo chứ không đoán: khoảng cách ngón cái–ngón trỏ theo thời gian, độ
> duỗi ngón tay, góc khớp, và chuỗi nhãn kèm độ tin của từng nhịp 0,2 giây.
>
> Thứ ba, mỗi thay đổi được chấm trên bốn nguồn: video val của IPN, 40 lời nhắc cử chỉ, gần 11 phút
> nói chuyện có khua tay, và các lần thử slide thật. Cuối cùng, mỗi điểm đánh đổi đều được chọn từ
> bảng số đo, không chọn theo cảm giác.

---

## Slide 5 — Vòng 1: Dạy hệ thống biết im lặng (1:30)

**Trên slide:**
- Vấn đề (Phase 8): recall **0,82–0,94** nhưng precision **0,05–0,20** → **6,6–30** lệnh nhầm mỗi
  phút
- Nguyên nhân: mỗi 0,2 giây một nhãn mới → một cú vuốt sinh cả chục nhãn, có lúc nhấp nháy
- Cách sửa: máy trạng thái `IDLE → READY → CANDIDATE → COOLDOWN`
  - ngưỡng tin cậy · đồng thuận k/5 · nghỉ 1,2 giây · mất tay thì quên hết
- Tối ưu trong thiết kế: cửa sổ khác lớp mà đủ tin là **phiếu phản đối**, huỷ ngay ứng viên

**Lời nói:**

> Vòng một bắt đầu từ Phase 8: em chạy cả hệ thống trên video val. Hệ thống bắt được cử chỉ rất tốt,
> recall 0,82 đến 0,94, nhưng không biết im lặng: precision chỉ 0,05 đến 0,20, tức 6,6 đến 30 lệnh
> nhầm mỗi phút. Lý do là mỗi 0,2 giây mô hình cho một nhãn mới, nên một cú vuốt sinh cả chục nhãn,
> và nhãn còn nhấp nháy.
>
> Cách sửa là một máy trạng thái nằm giữa mô hình và bàn phím. Phải đủ tin mới mở ứng viên lệnh; cần
> đủ số cửa sổ đồng ý trong 5 cửa sổ; phát lệnh xong thì nghỉ 1,2 giây; và mất tay thì quên hết.
>
> Có một chỗ tối ưu trong thiết kế. Cách hiểu đầu tiên của "đồng thuận" là đếm phiếu trên cửa sổ
> trượt. Theo cách đó, chuỗi nhấp nháy "vuốt, none, vuốt, none, vuốt" vẫn có 3 trên 5 phiếu và phát
> lệnh. Bản dùng thật coi một cửa sổ khác lớp mà đủ tin là phiếu phản đối, và huỷ ứng viên ngay.

---

## Slide 6 — Vòng 1: Kết quả và cái giá (1:00)

**Trên slide:**

| Ngưỡng khởi đầu 0,75 · 3/5 | F1 sự kiện | Lệnh nhầm mỗi phút |
|---|---|---|
| LSTM | 0,559 | 1,46 |
| Ghép | 0,490 | 1,33 |
| Rừng | 0,405 | 0,50 |
| Luật | 0,130 | 6,82 |

- `MIN_PRESENCE` 0,7 → 1,0: mất 3/54 cú vuốt, lệnh nhầm chỉ giảm 3% → giữ 0,7
- Cái giá: **0,77 lệnh mỗi cử chỉ**, chưa vào khoảng 0,9–1,1 của SPEC — phần thiếu là cử chỉ bị sót

**Lời nói:**

> Với ngưỡng khởi đầu 0,75 và 3 trên 5, lệnh nhầm trên video val giảm xuống khoảng 1,5 mỗi phút với
> LSTM, và LSTM có F1 sự kiện cao nhất, 0,559. Luật viết tay vẫn nhầm gần 7 lệnh mỗi phút.
>
> Em cũng thử nâng yêu cầu tỉ lệ có tay của cửa sổ từ 70% lên 100%. Kết quả mất 3 trong 54 cú vuốt
> mà lệnh nhầm chỉ giảm 3%, nên em giữ 70%.
>
> Cái giá của vòng này: chỉ còn 0,77 lệnh mỗi cử chỉ, chưa vào khoảng 0,9 đến 1,1 mà SPEC yêu cầu.
> Phần thiếu là cử chỉ bị sót, không phải lệnh thừa.

---

## Slide 7 — Vòng 2: Sửa thước đo trước khi tối ưu tiếp (1:15)

**Trên slide:**

| Con số đánh lừa | Cách sửa |
|---|---|
| **Độ trễ ra số âm:** chuyển động lớn nhất trong khung 4 giây nhiều khi là lúc thu tay | Đo từ khoảnh khắc chính trên video val, dùng đúng hàm đã gán nhãn dữ liệu |
| **"1,00 lệnh mỗi cử chỉ" nhưng recall 0,55:** sót và thừa bù cho nhau | Luôn báo kèm recall, lệnh mỗi lời nhắc, lệnh phát trùng |
| **Nhầm mỗi phút bị pha loãng:** hai kịch bản không thấy tay kéo luật từ 7,39 xuống 2,46 | Gộp theo thời lượng; thêm "nhầm mỗi phút có tay" (17% so với 89%) |

**Lời nói:**

> Lần chấm đầu tiên trên webcam lộ ra ba con số đánh lừa. Nếu không sửa, mọi vòng sau sẽ tối ưu theo
> hướng sai.
>
> Thứ nhất, độ trễ ra số âm. Khung lời nhắc 4 giây chứa cả động tác chuẩn bị và lúc thu tay, nên
> "khoảnh khắc chính" bị đặt sau lệnh. Em chuyển sang đo độ trễ trên video val, dùng đúng hàm đã dùng
> để gán nhãn dữ liệu.
>
> Thứ hai, "1,00 lệnh mỗi cử chỉ" trông hoàn hảo nhưng recall chỉ 0,55, vì cử chỉ bị sót và lệnh
> phát thừa bù cho nhau. Từ đó em luôn báo kèm recall và số lệnh phát trùng.
>
> Thứ ba, lệnh nhầm mỗi phút bị pha loãng. Hai kịch bản đọc và gõ phím không thấy tay nên bằng 0,
> kéo con số của luật từ 7,39 xuống 2,46. Em gộp theo thời lượng và thêm chỉ số nhầm mỗi phút có tay:
> phiên 10 phút chỉ thấy tay 17% thời gian, phiên ngắn thấy tới 89%.

---

## Slide 8 — Vòng 3: Mô hình cho bàn tay thật (1:30)

**Trên slide:**
- Vấn đề: LSTM `run_07` nhận **0/10** cú zoom; báo vuốt khi tay chụm đứng yên (4 lệnh nhầm / 1,1
  phút)
- Chẩn đoán: người dùng zoom với nhẫn, út **duỗi** (1,5–2,1); người diễn IPN gập (≈ 0,5)
- Cách sửa — `run_08` học thêm: một nửa cửa sổ zoom mang dáng ngón phụ của bàn tay IPN khác; 10%
  cửa sổ tay đứng yên, nhãn `none`

| Cùng dữ liệu, 0,75 · 3/5 | `run_07` | `run_08` |
|---|---|---|
| Zoom trên webcam | 0/10 | 4/10 |
| Luyện zoom: `zoom_in` / `zoom_out` / vuốt nhầm | 0 / 2 / 4 | 5 / 5 / 0 |
| IPN nhẫn, út duỗi tổng hợp: zoom còn nhận | 10% / 35% | 95% / 95% |
| F1 sự kiện val | 0,559 | 0,554 |

- Cái giá: precision `zoom_out` mức cửa sổ giảm; khi nói chuyện thêm 5 lệnh `zoom_out` nhầm (vuốt
  nhầm 8 → 2)

**Lời nói:**

> Vòng ba: trên tay em, LSTM `run_07` không nhận cú zoom nào, 0 trên 10. Nó còn báo vuốt khi bàn tay
> đang chụm đứng yên: 4 lệnh vuốt nhầm trong hơn một phút luyện zoom.
>
> Đo trên điểm mốc thì thấy nguyên nhân: em zoom với ngón nhẫn và ngón út duỗi, độ duỗi 1,5 đến 2,1,
> trong khi người diễn IPN gập hai ngón này, khoảng 0,5. LSTM học đúng dáng ngón của IPN nên gặp kiểu
> khác thì không nhận ra.
>
> Cách sửa là lần học `run_08`: một nửa số cửa sổ zoom được mang dáng ngón phụ của một bàn tay IPN
> khác, và thêm 10% cửa sổ bàn tay đứng yên với nhãn none. Kết quả: zoom trên webcam từ 0 lên 4
> trên 10, hết vuốt nhầm khi luyện zoom, và trên dữ liệu IPN có nhẫn, út duỗi tổng hợp thì zoom còn
> nhận 95%. F1 sự kiện val gần như giữ nguyên.
>
> Cái giá: precision `zoom_out` ở mức cửa sổ giảm — đây chính là lý do Phase 7 từng bác `run_08`. Và
> khi nói chuyện, LSTM một mình phát thêm 5 lệnh `zoom_out` nhầm, đổi lại vuốt nhầm giảm từ 8 xuống 2.

**Ghi chú:** đi kèm vòng này là màn hình luyện tập (`--show-features`, phím 3 và 4) hiện độ duỗi
nhẫn, út so với hộp của IPN để người dùng tập gập ngón.

---

## Slide 9 — Vòng 4: Chặn "lấy đà" (1:30)

**Trên slide:**
- Vấn đề: **5/20** lời nhắc vuốt phát lệnh **ngược chiều** trước
- Chuỗi nhãn của một lời nhắc vuốt phải: `R R · L L L R R R R R`
  - đoạn lấy đà `L L L`: mô hình gọi đúng chiều, độ tin **1,00** → phát `swipe_left`
  - cú hất thật `R × 5` rơi vào 1,2 giây nghỉ → bị bỏ
  - không ngưỡng tin cậy nào lọc được
- Cách sửa: lấy đà ≈ 3 cửa sổ, cú hất thật 4–5 → đòi **4 trong 5**

| | 0,75 · 3/5 | **0,85 · 4/5** |
|---|---|---|
| Vuốt phát ngược chiều trước | 5/20 | **2/20** |
| Nhầm khi nói chuyện (mỗi phút; mỗi phút có tay) | 0,64; 2,77 | **0,18; 0,79** |
| F1 sự kiện val; nhầm mỗi phút val | 0,554; 1,63 | **0,600; 0,77** |
| Recall vuốt trên webcam | 0,60 | 0,55 |
| Recall zoom trên webcam | 0,40 | 0,20 ← cái giá |
| Độ trễ trung vị | 0,62 s | 0,76 s |

**Lời nói:**

> Vòng bốn: 5 trên 20 lời nhắc vuốt phát lệnh ngược chiều trước. Nhìn chuỗi nhãn từng nhịp của một
> lời nhắc vuốt phải thì thấy ngay: trước khi hất sang phải, em kéo tay sang trái để lấy đà. Mô hình
> gọi đúng chiều của đoạn đó, với độ tin 1,00, nên phát lệnh vuốt trái. Cú hất thật đến sau thì rơi
> vào 1,2 giây nghỉ và bị bỏ. Mô hình không sai — và vì đoạn lấy đà tự tin như cú hất thật, không
> ngưỡng tin cậy nào lọc được.
>
> Điểm khác nhau nằm ở độ dài: đoạn lấy đà chỉ khoảng 3 cửa sổ, cú hất thật kéo dài 4 đến 5. Đòi 4
> trong 5 cửa sổ đồng ý thì đoạn lấy đà không đủ phiếu.
>
> Kết quả: vuốt ngược chiều từ 5 xuống 2 trên 20, nhầm khi nói chuyện từ 0,64 xuống 0,18 mỗi phút, và
> trên video val F1 sự kiện còn tăng lên 0,600. Cái giá là recall zoom trên webcam giảm một nửa, từ
> 0,40 xuống 0,20 — và vòng tiếp theo sinh ra từ chính cái giá này.

---

## Slide 10 — Vòng 5: Thử slide thật, 0/12 cú zoom (1:30)

**Trên slide:**
- Lần thử slide thật đầu (32 giây): 4/4 lệnh vuốt, **0/12 cú zoom**, dù nhãn zoom hiện đúng trên
  màn hình
- Chẩn đoán từ log của chính phiên đó:
  - động tác zoom sạch: cái–trỏ đi 0,1 ↔ 1,7 lòng bàn tay, đổi trong 0,2–0,4 giây rồi giữ yên
  - LSTM tự tin quá muộn: 0,4–0,7 ở đầu chuỗi, vượt 0,85 chỉ ở 1–3 cửa sổ cuối
  - rừng ngẫu nhiên gán đúng **12/12**, chỉ là thang độ tin thấp hơn (`zoom_in` 0,33–0,56)
  - không hạ được ngưỡng chung: quay về 0,75 · 3/5 thì lấy đà trở lại (5/20)
- Cách sửa: **mỗi họ cử chỉ một ngưỡng** — vuốt giữ nguyên, zoom lấy từ rừng
- Kết quả: chạy lại đúng phiên đó **0/12 → 6/12**, cả 6 đúng chiều; lần thử hai 92 giây, 19 lệnh

**Lời nói:**

> Vòng năm đến từ lần thử slide thật đầu tiên. Trong 32 giây, cả 4 lệnh vuốt đều chạy, nhưng 0 trên
> 12 cú zoom thành lệnh — dù nhãn zoom vẫn hiện đúng trên màn hình.
>
> Em chẩn đoán từ log của chính phiên đó. Động tác zoom rất sạch: khoảng cách cái–trỏ đổi trong 0,2
> đến 0,4 giây rồi giữ yên. Vấn đề là LSTM tự tin quá muộn: độ tin chỉ 0,4 đến 0,7 ở đầu chuỗi, và
> chỉ vượt 0,85 ở 1 đến 3 cửa sổ cuối, nên không bao giờ gom đủ 4 phiếu. Trong khi đó rừng ngẫu nhiên
> gán đúng lớp cả 12 cú, chỉ là thang độ tin của nó thấp hơn. Còn hạ ngưỡng chung thì không được, vì
> vấn đề lấy đà của vuốt sẽ quay lại.
>
> Nên em tách ngưỡng: mỗi họ cử chỉ một ngưỡng. Vuốt giữ nguyên, zoom lấy từ rừng với ngưỡng riêng.
> Chạy lại đúng phiên thử đó: từ 0 lên 6 trên 12 cú zoom, cả 6 đúng chiều. Lần thử thứ hai, 92 giây,
> hệ thống phát 19 lệnh, 8 vuốt và 11 zoom, mọi phím đều được gửi.

---

## Slide 11 — Vòng 5: Chọn ngưỡng cho zoom (1:15)

**Trên slide:**

| Zoom | Thử slide (có nghỉ / bỏ nghỉ) | 20 lời nhắc: đúng / ngược / sót | Lệnh mỗi lời nhắc | Nhầm khi nói chuyện | Val: F1; nhầm/phút |
|---|---|---|---|---|---|
| LSTM 0,85 · 4/5 (trước) | 0/12, — | 4 / 1 / 15 | 0,62 | 0,18 | 0,600; 0,77 |
| **Rừng 0,40 · 3/5 (chọn)** | **6/12, 9/12** | **10 / 4 / 6** | **1,00** | **0,18** | 0,561; 0,85 |
| Rừng 0,40 · 2/5 | 8/12, 11/12 | 16 / 4 / 0 | 1,48 | 0,27 | 0,525; 1,33 |
| Rừng 0,50 · 3/5 | 5/12, 5/12 | 10 / 2 / 8 | 0,90 | 0,18 | 0,581; 0,68 |

- 0,40 chứ không 0,50: độ tin `zoom_in` phần lớn dưới 0,50 → ở 0,50 không cú `zoom_in` nào thành lệnh
- 3/5 chứ không 2/5: 2/5 gần như không sót nhưng 1,48 lệnh mỗi lời nhắc
- Cái giá: F1 sự kiện val 0,600 → 0,561; đổi thiết kế so với một ngưỡng chung của SPEC

**Lời nói:**

> Đây là bảng em dùng để chọn ngưỡng cho zoom, chấm trên cả bốn nguồn.
>
> Vì sao 0,40 mà không phải 0,50? Độ tin `zoom_in` trên tay em phần lớn dưới 0,50; ở 0,50, khi thử
> trực tiếp không cú `zoom_in` nào thành lệnh. Vì sao 3 trên 5 mà không phải 2 trên 5? Với 2 trên 5,
> zoom gần như không sót, nhưng lệnh thừa tăng mạnh, 1,48 lệnh mỗi lời nhắc, phần lớn là động tác
> chuẩn bị và thu tay.
>
> Cột "bỏ nghỉ" tắt thời gian nghỉ để xem riêng khả năng nhận từng cú: 9 trên 12. Phần chênh lệch là
> vì em đổi chiều zoom mỗi khoảng 1,3 giây, nhanh hơn 1,8 giây mà một lệnh cần.
>
> Với lựa chọn này, lần đầu tiên hệ thống đạt đúng 1,00 lệnh mỗi lời nhắc mà không tăng nhầm khi nói
> chuyện. Cái giá là F1 sự kiện val giảm từ 0,600 xuống 0,561, và đây là một thay đổi thiết kế so
> với SPEC, vốn dùng một ngưỡng chung.

---

## Slide 12 — Vòng 6: Trải nghiệm điều khiển (1:00)

**Trên slide:**
- **Phím gửi nhầm cửa sổ:** lần thử đầu, phím đi vào cửa sổ demo → demo luôn nằm trên cùng, nhắc
  bấm chuột vào cửa sổ trình chiếu
- **Phím zoom:** `+` / `−` cho PowerPoint; Ctrl + / Ctrl − cho Google Slides và trình đọc PDF
- **Ánh xạ theo người dùng:** vuốt trái → slide sau, vuốt phải → slide trước (SPEC gốc ngược lại)
- **Tay ra vào khung không sinh lệnh lạ:** 66 lần vào lại trong các phiên đã ghi
- Nhịp làm cử chỉ: không lấy đà · giơ tay ≈ 1 giây rồi mới làm · zoom xong giữ yên ≈ 1 giây · cách
  nhau ≈ 2 giây

**Lời nói:**

> Vòng cuối là những thứ nhỏ nhưng quyết định trải nghiệm. Lần thử slide đầu tiên, không có gì xảy
> ra trên slide, vì phím đi vào cửa sổ demo đang được chọn. Giờ cửa sổ demo luôn nằm trên cùng, và
> màn hình nhắc bấm chuột vào cửa sổ trình chiếu sau khi bật điều khiển.
>
> Phím zoom là cộng và trừ khi trình chiếu PowerPoint. Ánh xạ vuốt theo ý người dùng: vuốt trái sang
> slide sau, như lật trang trên màn hình cảm ứng. Đưa tay ra khỏi khung rồi vào lại không sinh lệnh
> lạ, đã kiểm trên 66 lần vào lại.
>
> Và nhịp làm cử chỉ được ghi lên màn hình trợ giúp: không lấy đà, giơ tay khoảng 1 giây rồi mới làm
> — vì cửa sổ 1,2 giây cần 70% số bước có tay — zoom xong giữ yên, và các cử chỉ cách nhau khoảng 2
> giây.

---

## Slide 13 — Hạ tầng: để mỗi vòng chỉ mất vài phút (1:00)

**Trên slide:**
- Bản ghi thí nghiệm Phase 8: 46 thí nghiệm học một lần (**170 phút**); đổi máy trạng thái chỉ dựng
  lại bảng (**0,8 phút**)
- Bản ghi "băm" theo cấu hình; hai lần suýt hết hạn cả 46 bản ghi → nay có kiểm thử chặn
- `bench.py analyze`: 4 mô hình × 4 cấu hình trên mọi phiên trong 1–2,5 phút
- Log của demo kèm điểm mốc → chạy lại lần thử thật dưới cấu hình mới (0/12 → 6/12)
- `run_all.py` dựng lại toàn bộ; `requirements.txt` ghim phiên bản
- Quyết định: 25/10 ngưỡng khởi đầu · 26/10 `run_08`, 0,85 · 4/5 · 01/11 mô hình ghép · 02/11 ánh
  xạ vuốt

**Lời nói:**

> Sáu vòng này làm được trong vài ngày là nhờ hạ tầng. 46 thí nghiệm của Phase 8 chỉ học một lần, mất
> 170 phút; sau đó đổi máy trạng thái chỉ cần dựng lại bảng trong chưa tới một phút. Bản ghi được gắn
> với cấu hình; đã hai lần một hằng số mới suýt làm hết hạn cả 46 bản ghi, nên giờ có kiểm thử chặn.
>
> `bench.py analyze` chấm 4 mô hình nhân 4 cấu hình trên mọi phiên trong một đến hai phút rưỡi. Log
> của demo lưu kèm điểm mốc, nên một lần thử thật có thể chạy lại dưới cấu hình mới — đó là cách em
> có con số 0 trên 12 thành 6 trên 12.
>
> Bên phải là các quyết định cấu hình theo thời gian; mỗi quyết định đều chọn từ bảng số đo.

---

## Slide 14 — Demo trực tiếp (2:00)

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
> đều được gửi.

**Ghi chú:**
- Làm vuốt trước, zoom sau cùng. Trong PowerPoint, khi đang phóng to, mũi tên có thể di chuyển trong
  slide thay vì chuyển slide — nếu cần vuốt tiếp thì thu nhỏ về trước.
- Giơ tay khoảng 1 giây rồi mới làm; không lấy đà; zoom xong giữ yên; các cử chỉ cách nhau khoảng 2
  giây.
- Nếu một cử chỉ bị sót, bình tĩnh nói: "Đây đúng là hạn chế em sẽ trình bày ngay sau đây", rồi làm
  lại.
- Nếu demo hỏng hẳn, chuyển sang phương án dự phòng (video hoặc log `live_final2.csv`).

---

## Slide 15 — Những gì tối ưu chưa giải quyết được (1:15)

**Trên slide:**
- **Khoảng một nửa cử chỉ bị sót ở lần làm đầu** (40 lời nhắc): vuốt 11 đúng · 2 ngược · 7 sót; zoom
  10 đúng · 4 ngược · 6 sót — do nhẫn, út duỗi, lấy đà, tay vào khung muộn
- **Ngưỡng chọn trên ít dữ liệu** (40 lời nhắc, 12 cú zoom), chấm trên chính dữ liệu đó → hơi lạc
  quan
- **"0,9–1,1 lệnh mỗi cử chỉ" trên video val** vẫn chưa đạt: 0,61
- **Trên IPN, lựa chọn tốt nhất tuỳ phép đo:** học lại, trung bình 5 seed, LSTM một mình hơn ghép
  0,105 F1 sự kiện; với `run_08` thì ngược lại, 0,561 so với 0,507 → chọn ghép vì kết quả webcam

**Lời nói:**

> Em xin nói thẳng những gì tối ưu chưa giải quyết được.
>
> Thứ nhất, khoảng một nửa cử chỉ vẫn bị sót ở lần làm đầu. Trên 40 lời nhắc, vuốt có 11 đúng, 2
> ngược, 7 sót; zoom 10 đúng, 4 ngược, 6 sót. Phần lớn do cách làm khác người diễn IPN, và không
> ngưỡng nào sửa hết được.
>
> Thứ hai, ngưỡng được chọn trên ít dữ liệu, và chính dữ liệu đó dùng để chấm, nên con số có phần lạc
> quan. Thứ ba, mục tiêu 0,9 đến 1,1 lệnh mỗi cử chỉ trên video val vẫn chưa đạt, mới 0,61.
>
> Thứ tư, trên IPN lựa chọn tốt nhất tuỳ phép đo. Nếu học lại theo công thức chính và lấy trung bình
> năm seed, LSTM một mình hơn mô hình ghép 0,105 F1 sự kiện. Với mô hình đang dùng thì ngược lại,
> 0,561 so với 0,507. Em chọn mô hình ghép vì kết quả trên webcam.

---

## Slide 16 — Bài học về độ tin của con số (0:45)

**Trên slide:**
- Chênh lệch **dưới ≈ 0,1** F1 sự kiện trong một seed thường **lật chiều** khi đổi cấu hình kích
  hoạt → chỉ tin kết luận nhiều seed, nhiều fold
- Kết luận đứng qua cả bốn lần dựng bảng:
  - LSTM hơn rừng ngẫu nhiên
  - chia ngẫu nhiên theo cửa sổ thổi phồng macro-F1 thêm **0,10–0,15** → luôn chia theo người
  - rừng cần gốc toạ độ ở cổ tay frame đầu và cửa sổ 1,2 giây

**Lời nói:**

> Một bài học xuyên suốt: những chênh lệch nhỏ hơn khoảng 0,1 F1 sự kiện trong một seed thường đổi
> chiều khi chỉnh cấu hình kích hoạt. Nên em chỉ tin những kết luận có nhiều seed hoặc nhiều fold.
>
> Có ba kết luận đứng vững qua cả bốn lần dựng bảng: LSTM hơn rừng ngẫu nhiên; chia tập ngẫu nhiên
> theo cửa sổ thổi phồng macro-F1 thêm 0,10 đến 0,15, nên dự án luôn chia theo người; và rừng ngẫu
> nhiên cần gốc toạ độ ở cổ tay frame đầu cùng cửa sổ 1,2 giây.

---

## Slide 17 — Việc còn lại và kết luận (0:45)

**Trên slide:**
- Đo tốc độ đủ 4 mô hình ở 2 mức ánh sáng, đo lại lần hai (lần đầu: ≈ 30 FPS, ≈ 16 ms mỗi khung,
  MediaPipe chiếm 76–79%)
- Đo độ trễ thủ công, 10 lần mỗi cử chỉ · quay video demo · quyết định Phase 11, duyệt
  `docs/gestures.md`
- **Cuối cùng, đúng một lần:** chạy tập test; thử tái lập từ đầu bằng `run_all.py`
- Kết luận: sáu vòng tối ưu, mỗi vòng đo trước rồi mới sửa

**Lời nói:**

> Việc còn lại gồm: đo tốc độ đủ bốn mô hình ở hai mức ánh sáng — lần đo đầu được khoảng 30 khung
> hình mỗi giây, phần lớn thời gian là của MediaPipe — đo độ trễ thủ công, quay video demo, và quyết
> định có tự quay thêm dữ liệu ở Phase 11 hay không. Cuối cùng, đúng một lần, em sẽ chạy tập test và
> thử tái lập toàn bộ dự án từ môi trường trống.
>
> Tóm lại: qua sáu vòng tối ưu, mỗi vòng đo trước rồi mới sửa, hệ thống đi từ 6,6–30 lệnh nhầm mỗi
> phút xuống 0,85, và lần đầu điều khiển được slide thật. Em xin cảm ơn thầy cô và các bạn đã lắng
> nghe.

---

## Slide 18 — Cảm ơn và hỏi đáp

**Trên slide:**
- XIN CẢM ƠN!
- Mời thầy cô và các bạn đặt câu hỏi

---

## Phụ lục — Câu hỏi có thể gặp

**1. Vì sao khoảng một nửa cử chỉ vẫn bị sót?**
Phần lớn do cách làm cử chỉ khác người diễn IPN: nhẫn, út duỗi, lấy đà, tay vào khung muộn. Mô hình
chỉ học từ IPN. Cách khắc phục trực tiếp nhất là Phase 11: tự quay thêm dữ liệu với dáng tay người
dùng.

**2. Vì sao không hạ một ngưỡng chung cho dễ?**
Quay về 0,75 · 3/5 thì vấn đề lấy đà của vuốt trở lại (5/20 lời nhắc ngược chiều). Vuốt và zoom có
thang độ tin khác nhau, nên mỗi họ cần một ngưỡng.

**3. Vì sao không chia tập ngẫu nhiên?**
Chia ngẫu nhiên theo cửa sổ thổi phồng macro-F1 thêm 0,10–0,15. Khi dùng thật, hệ thống luôn gặp
người mới, nên phải chấm trên người chưa thấy khi học.

**4. Vì sao không dùng LSTM hai chiều hay làm mượt hai phía?**
Hệ thống chạy thời gian thực. Hai chiều nghĩa là phải chờ dữ liệu tương lai, làm tăng độ trễ.

**5. Vì sao chưa chạy tập test?**
Tập test chỉ chạy đúng một lần ở cuối. Nếu nhìn test trong lúc còn chỉnh, mọi lựa chọn sau đó đều
ngầm khớp với test và con số không còn khách quan.

**6. 0,18 lệnh nhầm mỗi phút có thấp thật không?**
Đó là con số gộp theo thời lượng. Nếu chỉ tính lúc tay trong khung thì là 0,79 mỗi phút. Phiên đọc
và gõ phím không thấy tay nên 0 lệnh nhầm ở đó chưa nói được nhiều.

**7. Ngưỡng chọn rồi chấm trên cùng dữ liệu, có phải "học vẹt" không?**
Có phần lạc quan, và tài liệu ghi rõ điều đó. Mỗi lựa chọn được xem đồng thời trên cả bốn nguồn,
nên không tối ưu riêng cho một con số; nhưng cách kiểm chắc hơn là ghi phiên mới rồi chấm lại với
cấu hình đã chốt.

**8. Vì sao vuốt trái lại sang slide sau?**
Theo lựa chọn của người dùng ngày 02/11, giống thao tác lật trang trên màn hình cảm ứng. SPEC gốc quy
ước ngược lại. Ánh xạ nằm trong `CTRL_HOTKEYS` của `src/config.py`, đổi được mà không cần học lại.

**9. Hệ thống có cần GPU không?**
Không. Lần đo đầu khoảng 30 FPS, khoảng 16 ms mỗi khung hình; phần nặng nhất là MediaPipe (76–79%).
