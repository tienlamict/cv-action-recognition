# Kịch bản thuyết trình — Phase 8, 9 và 10

**Nguồn:** `docs/tong-ket-phase-8-10.md` (cập nhật 02/11/2026).

**Thời lượng dự kiến:** khoảng 15 phút trình bày, 2 phút demo trực tiếp, sau đó hỏi đáp.

**Cấu trúc:** 13 slide. Mỗi slide gồm: *trên slide* (nội dung hiển thị), *lời nói* (đọc hoặc nói
theo ý), và *ghi chú* (nhắc riêng cho người trình bày).

---

## Chuẩn bị trước buổi

- Mở sẵn PowerPoint có khoảng 8–10 slide để demo, đặt ở chế độ trình chiếu.
- Mở terminal, đã kích hoạt env `action-recognition`, gõ sẵn lệnh:
  `python scripts/demo.py --model hybrid`.
- Kiểm tra ánh sáng và webcam: tay phải nằm gọn trong khung, nền không quá rối.
- **Phương án dự phòng:** nếu demo trực tiếp hỏng, chiếu lại log `results/phase10/live_final2.csv`
  (92 giây, 19 lệnh) hoặc video quay trước. Nên quay video dự phòng trước buổi — việc này cũng nằm
  trong danh sách còn lại của Phase 10.
- Tự nhắc cách làm cử chỉ khi demo: giơ tay khoảng 1 giây rồi mới làm, không lấy đà ngược chiều,
  giữ yên khoảng 1 giây sau cú zoom, các cử chỉ cách nhau khoảng 2 giây.

---

## Slide 1 — Mở đầu (0:30)

**Trên slide:**
- Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính
- Phần trình bày: Phase 8, 9, 10 — từ mô hình đến hệ thống dùng được

**Lời nói:**

> Xin chào thầy cô và các bạn. Đề tài của em là nhận dạng cử chỉ bàn tay thời gian thực để điều
> khiển máy tính. Ở buổi trước em đã trình bày cách xây dựng dữ liệu và mô hình đến Phase 7. Hôm nay
> em trình bày ba giai đoạn tiếp theo: làm sao biết mô hình thực sự tốt, làm sao biến dự đoán của
> mô hình thành lệnh, và cuối cùng là dùng nó để điều khiển PowerPoint thật.

---

## Slide 2 — Câu hỏi của giai đoạn này (1:00)

**Trên slide:**
- Đến Phase 7: đã có mô hình phân loại cửa sổ 1,2 giây (LSTM, rừng ngẫu nhiên)
- Câu hỏi mới: *mô hình phân loại tốt* có nghĩa là *hệ thống dùng được* không?
- Kết quả hôm nay: điều khiển được PowerPoint bằng cử chỉ

**Lời nói:**

> Đến cuối Phase 7, em đã có các mô hình nhìn một đoạn 1,2 giây chuyển động của bàn tay và nói đó là
> cử chỉ gì. Nhưng người dùng không quan tâm đến từng đoạn 1,2 giây. Họ quan tâm: tôi vuốt một cái,
> slide có sang đúng một trang không; tôi đang nói chuyện và khua tay, máy có tự nhảy slide không.
>
> Ba phase hôm nay trả lời đúng câu hỏi đó. Và kết quả cuối cùng là hệ thống đã điều khiển được
> PowerPoint: vuốt trái sang slide sau, vuốt phải về slide trước, mở hay chụm ba ngón để phóng to,
> thu nhỏ.

---

## Slide 3 — Lộ trình ba phase (0:45)

**Trên slide:**

| Phase | Câu hỏi | Trạng thái |
|---|---|---|
| 8 | Mô hình nào tốt, và tin con số đến đâu? | ✅ (còn lần chạy test cuối) |
| 9 | Khi nào thì phát lệnh? | ✅ |
| 10 | Chạy thật trên webcam có ổn không? | 🟡 đã thử slide thật |

**Lời nói:**

> Phase 8 là đánh giá: chấm mọi mô hình và chạy bảy bảng khảo sát. Phase 9 thêm một máy trạng thái
> để biến chuỗi nhãn của mô hình thành lệnh rời rạc. Phase 10 là demo hoàn chỉnh và đo đạc trên
> webcam. Riêng tập test em cố ý để chạy đúng một lần cuối cùng, để con số trên test không bị ảnh
> hưởng bởi các lần chỉnh sửa.

---

## Slide 4 — Phase 8: chấm ở hai mức (1:30)

**Trên slide:**
- **Mức cửa sổ:** từng cửa sổ 1,2 giây có đúng lớp không → macro-F1
- **Mức sự kiện:** chạy cả hệ thống trên 27 video val liên tục của IPN (60 phút, 108 cử chỉ),
  qua đúng đường ống của demo
  - Lệnh đúng = đúng loại, phát trong khoảng từ lúc cử chỉ bắt đầu đến 1 giây sau khi kết thúc
  - Đo: F1 sự kiện, số lệnh mỗi cử chỉ, lệnh nhầm mỗi phút

**Lời nói:**

> Điểm đầu tiên của Phase 8 là em chấm ở hai mức. Mức cửa sổ là con số quen thuộc của học máy,
> macro-F1. Nhưng người dùng không cảm nhận trực tiếp con số này.
>
> Nên em thêm mức sự kiện: lấy 27 video liên tục của tập val, tổng cộng 60 phút với 108 cử chỉ, cho
> chạy qua đúng đường ống mà demo dùng. Một lệnh được tính là đúng nếu đúng loại và phát ra trong
> khoảng từ lúc cử chỉ bắt đầu đến 1 giây sau khi nó kết thúc. Từ đó em đo được những thứ người dùng
> thật sự cảm nhận: bao nhiêu cử chỉ thành lệnh, một cử chỉ ra mấy lệnh, và mỗi phút máy phát nhầm
> bao nhiêu lần.

**Ghi chú:** nhấn mạnh "đúng đường ống của demo" — dữ liệu IPN và webcam đi qua cùng các hàm, không
có hai bản gần giống nhau.

---

## Slide 5 — Bảy bảng khảo sát (1:00)

**Trên slide:**
- 46 thí nghiệm, mỗi thí nghiệm đổi **đúng một yếu tố**: chuẩn hoá, độ dài cửa sổ, cách chia tập,
  bộ đặc trưng, seed, k-fold theo người, biến thể LSTM
- Lưu dự đoán thành bản ghi → chỉnh máy trạng thái chỉ mất khoảng 1 phút thay vì học lại 170 phút
- Bản ghi tự hết hạn khi đổi hằng số ảnh hưởng đến kết quả

**Lời nói:**

> Script `run_experiments.py` chạy 46 thí nghiệm, mỗi cái chỉ đổi đúng một yếu tố để so sánh công
> bằng. Một chi tiết kỹ thuật quan trọng: mỗi thí nghiệm lưu lại toàn bộ dự đoán. Khi em chỉnh máy
> trạng thái ở Phase 9, em chỉ cần dựng lại bảng trong khoảng một phút, thay vì học lại mọi mô hình
> mất 170 phút. Bản ghi được gắn với cấu hình, nên nếu em đổi một hằng số có ảnh hưởng đến mô hình
> thì bản ghi tự hết hạn, không bao giờ dùng nhầm kết quả cũ.

---

## Slide 6 — Kết luận đứng vững và bài học về con số (1:30)

**Trên slide:**
- LSTM hơn rừng ngẫu nhiên: **+0,116 macro-F1** (trung bình 5 seed); mức sự kiện: **+0,323**
- Chia ngẫu nhiên theo cửa sổ **thổi phồng 0,10–0,15** → luôn chia theo người
- Thêm góc khớp ngón tay: nhầm `none` → `swipe_left` giảm **366 → 190** cửa sổ
- ⚠️ Chênh lệch < 0,1 F1 sự kiện trong một seed thường **lật chiều** khi đổi cấu hình

**Lời nói:**

> Từ bốn lần dựng bảng, có những kết luận đứng vững qua tất cả.
>
> Thứ nhất, LSTM hơn rừng ngẫu nhiên một cách chắc chắn, hơn 0,116 macro-F1 trung bình năm seed, và
> ở mức sự kiện thì khoảng cách còn lớn hơn, 0,323.
>
> Thứ hai, và đây là điều em muốn nhấn mạnh: nếu chia tập ngẫu nhiên theo cửa sổ, con số bị thổi
> phồng thêm 0,10 đến 0,15. Mức thổi phồng này còn lớn hơn khoảng cách giữa hai mô hình. Lý do là
> các cửa sổ của cùng một người rất giống nhau, mô hình "đã gặp" người đó khi học. Vì vậy toàn bộ dự
> án luôn chia theo người.
>
> Thứ ba là một vòng cải tiến thành công: ô nhầm lớn nhất là nhầm "không có cử chỉ" thành "vuốt
> trái". Thêm đặc trưng góc khớp ngón tay làm ô này giảm gần một nửa, từ 366 xuống 190 cửa sổ.
>
> Và một bài học về độ tin của con số: khi đi qua máy trạng thái, những chênh lệch nhỏ hơn khoảng
> 0,1 trong một seed thường đổi chiều khi chỉnh cấu hình kích hoạt. Có một thay đổi từng cho +0,108,
> lần dựng sau chỉ còn +0,012. Nên em chỉ tin những kết luận có năm seed, năm fold người, hoặc chênh
> lệch thật lớn.

---

## Slide 7 — Phase 9: máy trạng thái (2:00)

**Trên slide:**
- Mô hình: "0,2 giây vừa rồi giống cử chỉ gì?" → một cú vuốt sinh cả chục nhãn, có lúc nhấp nháy
- Máy trạng thái: "**có nên phát lệnh bây giờ không?**"

```
IDLE ──thấy tay──▶ READY ──cửa sổ đủ tin──▶ CANDIDATE ──đủ phiếu──▶ COOLDOWN (1,2 s)
  ▲                  ▲                         │ bất đồng → huỷ          │
  └──── mất tay: quên hết ◀──────────────────────────────────────────────┘
```

- Ngưỡng tin cậy · đồng thuận k/5 cửa sổ · nghỉ sau lệnh · hạ tay để huỷ

**Lời nói:**

> Mô hình cứ 0,2 giây trả lời một lần, "cửa sổ vừa rồi giống cử chỉ gì". Nên một cú vuốt sinh ra cả
> chục nhãn liên tiếp, có lúc nhấp nháy giữa các lớp. Nếu phát lệnh theo từng nhãn thì một cú vuốt
> sẽ nhảy mười slide.
>
> Máy trạng thái trả lời một câu hỏi khác: có nên phát lệnh bây giờ không. Nó có bốn trạng thái.
> IDLE là chưa thấy tay. READY là thấy tay và đang chờ. Khi một cửa sổ đủ tin cậy, máy chuyển sang
> CANDIDATE và bắt đầu gom phiếu: cần đủ số cửa sổ đồng ý trong năm cửa sổ. Nếu một cửa sổ đủ tin
> mà lại nói khác đi, ứng viên bị huỷ. Phát lệnh xong thì nghỉ 1,2 giây để không phát trùng. Và bất
> cứ lúc nào mất tay, máy quên hết — tức là người dùng có thể hạ tay xuống để huỷ.
>
> Một ví dụ về đánh đổi: em thử nâng yêu cầu "tay phải có mặt" từ 70% lên 100% thời gian của cửa
> sổ. Kết quả mất 3 trong 54 cú vuốt mà lệnh nhầm chỉ giảm 3%, nên em giữ 70%.

**Ghi chú:** nếu bị hỏi về mục chưa đạt — trên video val, số lệnh mỗi cử chỉ là 0,61, thấp hơn mục
tiêu 0,9–1,1, phần thiếu là cử chỉ bị sót. Quyết định là để Phase 10 chọn cấu hình bằng số đo trên
webcam.

---

## Slide 8 — Phase 10: công cụ demo và đo đạc (1:00)

**Trên slide:**
- `demo.py`: phát phím thật, bấm `c` để bật (mặc định tắt), trang trợ giúp `?`, luôn nằm trên cùng,
  log mọi dự đoán và phím đã gửi
- `bench.py`: `speed` (FPS, thời gian từng khâu) · `record` (ghi theo lời nhắc) · `analyze` (chấm
  mọi cấu hình từ một lần ghi)
- Dữ liệu ghi: 40 lời nhắc cử chỉ · 10,9 phút nói chuyện có khua tay · 2 lần thử slide thật

**Lời nói:**

> Phase 10 có hai công cụ chính. `demo.py` phát phím thật ra hệ điều hành. Điều khiển mặc định tắt,
> phải bấm `c` mới bật, để tránh máy tự nhảy slide khi chưa sẵn sàng. Mọi dự đoán và mọi phím đã gửi
> đều được ghi log để phân tích lại.
>
> `bench.py` dùng để đo: đo tốc độ, ghi phiên theo kịch bản có lời nhắc trên màn hình, và quan trọng
> nhất là chấm được mọi cấu hình từ một lần ghi. Em ghi 40 lời nhắc cử chỉ, mỗi lớp 10 lần, và gần
> 11 phút nói chuyện có khua tay để đo kích hoạt nhầm.

---

## Slide 9 — Bốn phát hiện về cách làm cử chỉ (1:30)

**Trên slide:**
1. **Nhẫn và út duỗi khi zoom** (độ duỗi 1,4–2,1; người diễn IPN ≈ 0,5)
2. **Lấy đà ngược chiều** trước khi vuốt → mô hình nhận đúng cú kéo ngược, độ tin 1,00
3. **Cử chỉ đến muộn:** tay vào khung ở giây 2–4 của lời nhắc 4 giây
4. **Đổi chiều quá nhanh:** mỗi lệnh chiếm ≈ 1,8 giây, người dùng đổi chiều zoom mỗi ≈ 1,3 giây

**Lời nói:**

> Khi chạy trên webcam, em phát hiện phần lớn lỗi không đến từ đường ống mà đến từ việc em làm cử chỉ
> khác người diễn trong IPN.
>
> Thứ nhất, khi zoom em để duỗi ngón nhẫn và ngón út, trong khi người diễn IPN gập hai ngón này. LSTM
> chưa thấy dáng tay đó nên thiếu tự tin.
>
> Thứ hai, rất thú vị: trước khi vuốt, em có thói quen kéo tay ngược lại để lấy đà. Đoạn kéo ngược đó
> cũng là một cú vuốt, và mô hình nhận đúng chiều của nó với độ tin 1,00 — tức là mô hình đúng, nhưng
> lệnh phát ra lại ngược ý người dùng.
>
> Thứ ba, tay thường vào khung muộn. Thứ tư, em đổi chiều zoom nhanh hơn thời gian một lệnh cần để
> gom phiếu và nghỉ.
>
> Từ đó em bổ sung hướng dẫn và màn hình luyện tập: hiện độ duỗi của ngón nhẫn và út so với khoảng
> của IPN để người dùng tự chỉnh.

---

## Slide 10 — Cấu hình cuối và kết quả (1:30)

**Trên slide:**
- **Mô hình ghép:** vuốt theo LSTM (0,85 · 4/5), zoom theo rừng ngẫu nhiên (0,40 · 3/5)

| | Kết quả |
|---|---|
| Vuốt (20 lời nhắc) | 11 đúng · 2 ngược · 7 sót |
| Zoom (20 lời nhắc) | 10 đúng · 4 ngược · 6 sót (trước khi đổi: 4 đúng) |
| Lệnh mỗi lời nhắc | 1,00 |
| Nhầm khi nói chuyện | 0,18 lệnh/phút |
| Video val IPN | F1 sự kiện 0,561 · độ trễ trung vị 0,76 s |
| Tốc độ | ≈ 30 FPS · ≈ 16 ms/khung, MediaPipe chiếm 76–79% |

**Lời nói:**

> Cấu hình cuối là một mô hình ghép. Vuốt lấy từ LSTM với ngưỡng cao, 0,85 và cần 4 trong 5 cửa sổ
> đồng ý. Zoom lấy từ rừng ngẫu nhiên với ngưỡng 0,40 và 3 trong 5.
>
> Vì sao lại ghép? Ở lần thử slide thật đầu tiên, không cú zoom nào trong 12 cú thành lệnh. Nhưng
> khi xem lại log, rừng ngẫu nhiên gán đúng cả 12 cú, chỉ là thang độ tin của nó thấp hơn. Nên em
> cho zoom đi theo rừng với ngưỡng riêng. Còn ngưỡng 0,85 của vuốt giảm vuốt ngược chiều từ 5 xuống
> 2 trên 20 lời nhắc, và giảm lệnh nhầm khi nói chuyện từ 0,64 xuống 0,18 mỗi phút.
>
> Kết quả: khoảng một nửa số cử chỉ thành lệnh đúng ngay lần làm đầu. Rất ít khi phát trùng. Khi nói
> chuyện có khua tay, trung bình hơn 5 phút mới có một lệnh nhầm. Hệ thống chạy khoảng 30 khung hình
> mỗi giây, trong đó phần lớn thời gian là của MediaPipe chứ không phải của mô hình của em.

**Ghi chú:** con số 0,18/phút tính trên toàn bộ thời gian; nếu chỉ tính lúc tay trong khung thì là
0,79/phút (camera thấy tay 23% thời gian). Nói thẳng nếu bị hỏi.

---

## Slide 11 — Demo trực tiếp (2:00)

**Trên slide:**
- `python scripts/demo.py --model hybrid` → bấm `c`
- Vuốt trái: slide sau · Vuốt phải: slide trước · Mở/chụm ba ngón: phóng to/thu nhỏ

**Lời nói:**

> Bây giờ em xin demo trực tiếp. Em bật chương trình, bấm `c` để bật điều khiển.
>
> *(vuốt trái 2 lần)* Vuốt trái, slide sang trang sau — giống lật trang trên màn hình cảm ứng.
> *(vuốt phải 1 lần)* Vuốt phải để quay lại.
> *(mở ba ngón, chờ, chụm lại)* Mở ngón cái, trỏ, giữa để phóng to; chụm lại để thu nhỏ.
>
> Ở lần thử cuối ngày 01/11, em dùng liền 92 giây, hệ thống phát 19 lệnh — 8 vuốt và 11 zoom — và mọi
> phím đều được gửi.

**Ghi chú:**
- Làm vuốt trước, zoom sau cùng. Trong PowerPoint, khi đang phóng to, mũi tên có thể di chuyển trong
  slide thay vì chuyển slide — nếu cần vuốt tiếp thì thu nhỏ về trước.
- Giơ tay khoảng 1 giây rồi mới làm; không lấy đà; các cử chỉ cách nhau khoảng 2 giây.
- Nếu một cử chỉ bị sót, bình tĩnh nói: "Đây đúng là hạn chế em sẽ trình bày ngay sau đây", rồi làm
  lại.
- Nếu demo hỏng hẳn, chuyển sang phương án dự phòng (video hoặc log `live_final2.csv`).

---

## Slide 12 — Hạn chế (1:00)

**Trên slide:**
- Khoảng **một nửa cử chỉ bị sót** ở lần làm đầu (vuốt hất nhanh, tay vào muộn; zoom do duỗi nhẫn–út)
- Zoom có thể **ngược chiều** khi tay chuẩn bị: 4/20 lời nhắc
- Ngưỡng zoom chọn trên **ít dữ liệu** (12 cú zoom), chấm trên chính dữ liệu đó → hơi lạc quan
- Trên IPN, mô hình ghép **không thắng ở mọi phép đo**
- Đo lại lần hai và video demo: chưa làm

**Lời nói:**

> Em xin nói thẳng các hạn chế. Thứ nhất, khoảng một nửa cử chỉ bị sót ở lần làm đầu. Thứ hai, zoom
> đôi khi phát ngược chiều khi tay chuẩn bị. Thứ ba, ngưỡng zoom được chọn trên ít dữ liệu, và chính
> dữ liệu đó dùng để chấm, nên con số có phần lạc quan.
>
> Thứ tư, trên IPN mô hình ghép không phải lúc nào cũng tốt nhất. Nếu học lại theo công thức chính và
> lấy trung bình năm seed, LSTM một mình hơn mô hình ghép 0,105 F1 sự kiện. Với mô hình đang dùng thì
> ngược lại, 0,561 so với 0,507. Em chọn mô hình ghép vì lý do từ webcam: nó phát được zoom trên tay
> người dùng thật mà không nhầm thêm.

---

## Slide 13 — Việc còn lại và kết luận (0:45)

**Trên slide:**
- Đo tốc độ đủ bốn mô hình ở hai mức ánh sáng; đo độ trễ thủ công; quay video demo
- Quyết định Phase 11 (dữ liệu tự quay)
- **Cuối cùng, đúng một lần:** chạy tập test; thử tái lập từ đầu bằng `run_all.py`
- Đã có: `run_all.py` (16 bước), ghim phiên bản, README · `pytest`: 215 passed

**Lời nói:**

> Việc còn lại gồm: đo tốc độ đầy đủ, đo độ trễ thủ công, quay video demo, và quyết định có tự quay
> thêm dữ liệu ở Phase 11 hay không. Cuối cùng, đúng một lần, em sẽ chạy tập test và thử tái lập
> toàn bộ dự án từ một môi trường trống bằng một lệnh `run_all.py`.
>
> Tóm lại: từ một mô hình phân loại, em đã có một hệ thống điều khiển được PowerPoint bằng cử chỉ,
> đo được ở mức người dùng cảm nhận, và biết rõ nó còn yếu ở đâu. Em xin cảm ơn thầy cô và các bạn
> đã lắng nghe.

---

## Phụ lục — Câu hỏi có thể gặp

**1. Vì sao recall chỉ khoảng 52%?**
Phần lớn do cách làm cử chỉ khác người diễn IPN (slide 9), không phải lỗi đường ống. Mô hình chỉ học
từ IPN. Cách khắc phục trực tiếp nhất là Phase 11: tự quay thêm dữ liệu với dáng tay của người dùng.

**2. Vì sao không chia tập ngẫu nhiên?**
Vì chia ngẫu nhiên theo cửa sổ thổi phồng macro-F1 thêm 0,10–0,15. Khi dùng thật, hệ thống luôn gặp
người mới, nên phải chấm trên người chưa thấy khi học.

**3. Vì sao không dùng LSTM hai chiều hay làm mượt hai phía?**
Hệ thống chạy thời gian thực. Hai chiều nghĩa là phải chờ dữ liệu tương lai, làm tăng độ trễ.

**4. Vì sao chưa chạy tập test?**
Tập test chỉ chạy đúng một lần ở cuối. Nếu nhìn test trong lúc còn chỉnh, mọi lựa chọn sau đó đều
ngầm khớp với test và con số không còn khách quan.

**5. 0,18 lệnh nhầm mỗi phút có thấp thật không?**
Tính trên toàn bộ thời gian nói chuyện thì là 0,18. Camera chỉ thấy tay 23% thời gian; nếu chỉ tính
lúc tay trong khung thì là 0,79 mỗi phút. Ngoài ra, ở phiên đọc và gõ phím, camera không thấy tay nên
kết quả 0 lệnh nhầm ở đó chưa nói được nhiều.

**6. Vì sao vuốt trái lại sang slide sau?**
Theo lựa chọn của người dùng ngày 02/11, giống thao tác lật trang trên màn hình cảm ứng. SPEC gốc
quy ước ngược lại. Ánh xạ nằm trong `CTRL_HOTKEYS` của `src/config.py`, đổi được mà không cần học lại.

**7. Vì sao chỉ dùng toạ độ 2D?**
Toạ độ z của MediaPipe ước lượng từ một camera nên nhiễu. Dùng 2D giúp dữ liệu IPN, dữ liệu tự quay
và webcam đi qua cùng một đường ống, cùng một cách chuẩn hoá.

**8. Hệ thống có cần GPU không?**
Không. Chạy khoảng 30 FPS, khoảng 16 ms mỗi khung hình; phần nặng nhất là MediaPipe (76–79%).
