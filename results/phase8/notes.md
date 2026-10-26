# Phase 8 — Ghi chú đánh giá hai mức và bảy bảng khảo sát

> Claude viết ngày 2026-10-25. Số liệu lấy từ:
>
> - `results/phase8/experiments/run_01`: bảy bảng và bảng phụ, 46 thí nghiệm; mọi dự đoán
>   nằm trong bản ghi `results/phase8/records/`;
> - `results/phase8/evaluate/run_01`–`run_04`: bốn mô hình đã lưu (luật, rừng, LSTM, ghép) ở
>   cả hai mức.
>
> Tái lập bằng `python scripts/run_experiments.py` (170 phút trên máy 8 luồng logic, kể cả dựng
> lại dữ liệu) và `python scripts/evaluate.py --model <tên> --events edge`, ghi trong README.
> Mọi khảo sát chạy trên val, hoặc k-fold trên 37 người của train và val. Tập test chưa bị chạm:
> `results/TEST_USED.log` chưa tồn tại.
>
> **Cập nhật 2026-10-26:** bảy bảng được dựng lại với cấu hình cuối của Phase 10 (máy
> trạng thái 0,85 · 4/5; LSTM của Bảng 1 là `run_08`) ở `results/phase8/experiments/run_03`.
> Kết luận nào đứng, kết luận nào đổi: `results/phase10/notes.md` mục 7.
>
> **Ba phép kiểm đường ống đều đạt:**
>
> - bộ cửa sổ dựng lại cho các bảng trùng `windows.npz` từng giá trị (manifest:
>   `matches_windows_npz: true`);
> - Bảng 1 dựng từ bản ghi, và `evaluate.py` chạy thẳng trên video, cho cùng từng chữ số;
> - rừng học lại trong đường ống thí nghiệm trùng rừng của demo (macro-F1 0,4361).

**Cách đọc.**

- **Mức cửa sổ** chấm 11 038 cửa sổ val.
- **Mức sự kiện** chạy cả hệ thống trên 27 video val liên tục: 60,1 phút, 108 cử chỉ, mỗi lớp
  27. Video đi qua đúng `live.WindowStream` của demo, với bộ lọc `edge`: mỗi chuỗi dự đoán
  liền nhau cùng một lớp là một lệnh.
- **Lệnh đúng** là lệnh đúng loại, phát từ lúc cử chỉ bắt đầu tới lúc kết thúc + 1 giây
  (`EVENT_MATCH = "span"`).
- So sánh nào có chênh lệch nhỏ hơn độ lệch chuẩn giữa năm seed (Bảng 6) được ghi "không đủ
  bằng chứng để kết luận". Giới hạn của quy tắc này ở mục 6.

## 1. Kết luận chính

- **LSTM hơn rừng ngẫu nhiên một cách chắc chắn:** +0,116 macro-F1 và +0,104 F1 sự kiện,
  trung bình năm seed, hơn 4 lần độ lệch chuẩn (Bảng 6).
- **Hệ thống đã bắt được cử chỉ, nhưng chưa biết im lặng.** Recall mức sự kiện 0,82–0,94, mà
  precision chỉ 0,05–0,20: 6,6–30 lệnh nhầm mỗi phút (Bảng 1). Đây là việc của máy trạng thái
  ở Phase 9.
- **Vòng cải tiến thành công.** Thêm 10 đặc trưng góc khớp làm ô nhầm lớn nhất của rừng
  (`none` → `swipe_left`) giảm từ 366 xuống 190 cửa sổ, và lệnh nhầm từ 10,6 xuống 6,3 mỗi
  phút. Giả thuyết A của Phase 6 đứng vững (mục 3.1).
- **Chia ngẫu nhiên theo cửa sổ thổi phồng macro-F1 thêm 0,10–0,15**, nhiều hơn cả khoảng cách
  giữa LSTM và rừng (Bảng 4).
- **Ngoài góc khớp, không biến thể đổi một yếu tố nào hơn cấu hình hiện tại ở mức sự kiện.**
  Cấu hình đó là: gốc toạ độ frame đầu, cửa sổ 1,2 giây, biên khoảnh khắc chính 3 bước, gộp
  `last`, có tăng cường, đủ 21 điểm.
- **Mô hình ghép kém LSTM trên val chính thức, nhưng ít tụt hơn ở nhóm người khó** (Bảng 7).

## 2. Bảng 1 — bốn mô hình ở hai mức

| Mô hình | macro-F1 cửa sổ | F1 sự kiện | Precision | Recall | Lệnh / cử chỉ | Lệnh nhầm / phút | Không tầng kích hoạt: lệnh / cử chỉ | Không tầng kích hoạt: lệnh nhầm / phút | ms / cửa sổ |
|---|---|---|---|---|---|---|---|---|---|
| Luật | 0,231 | 0,094 | 0,050 | 0,870 | 1,06 | 29,8 | 3,24 | 90,5 | 0,007 |
| Rừng ngẫu nhiên | 0,436 | 0,211 | 0,121 | 0,815 | 0,94 | 10,6 | 2,94 | 22,4 | 2,97 |
| LSTM | 0,556 | 0,334 | 0,204 | 0,935 | 1,20 | 6,6 | 5,47 | 21,0 | 1,49 |
| Ghép (vuốt LSTM, zoom rừng) | 0,506 | 0,308 | 0,188 | 0,852 | 1,03 | 6,6 | 4,35 | 20,0 | 6,44 |

- **Hai mức cùng xếp hạng:** luật < rừng < ghép < LSTM.
- **Mức sự kiện cho thấy điều mức cửa sổ giấu.** Cứ một lệnh đúng thì có 4–19 lệnh sai. Lớp
  `none` chiếm 96% thời gian, nên một tỉ lệ báo nhầm nhỏ theo cửa sổ vẫn thành nhiều lệnh nhầm
  mỗi phút.
- **Bộ lọc `edge` đã gánh một phần.** So với khi không có tầng kích hoạt nào (`raw`):
  - lệnh nhầm giảm 2–3 lần;
  - số lệnh trên một cử chỉ từ 2,9–5,5 về 0,94–1,20.
  
  Phần còn lại là việc của máy trạng thái.
- **Định nghĩa khớp ban đầu của SPEC** (±1 giây quanh lúc kết thúc) cho F1 sự kiện chỉ khoảng
  một nửa: 0,053 / 0,108 / 0,176 / 0,158. Lệnh đúng lúc thường phát ở giữa đoạn nhãn; đây là
  lý do đổi sang `"span"` (SPEC Phase 8, 2026-10-22).
- **Tốc độ mô hình không phải vấn đề.** Mô hình chậm nhất (ghép) mất 6,4 ms mỗi cửa sổ, so với
  200 ms giữa hai lần dự đoán. Phân rã thời gian của cả vòng lặp đo ở Phase 10.

**Từng lớp, mức sự kiện** (`results/phase8/evaluate/run_02`, `run_03`):

| Lớp | Rừng: recall | LSTM: recall | Rừng: lệnh / cử chỉ | LSTM: lệnh / cử chỉ |
|---|---|---|---|---|
| `swipe_left` | 0,89 | 1,00 | 1,11 | 1,41 |
| `swipe_right` | 0,85 | 0,89 | 1,00 | 1,04 |
| `zoom_in` | 0,74 | 0,96 | 0,89 | 1,33 |
| `zoom_out` | 0,78 | 0,89 | 0,78 | 1,04 |

- **Câu hỏi để ngỏ ở Phase 6** (`results/phase6/notes.md` mục 4.2) đã có câu trả lời.
  - Ở mức cửa sổ, rừng bỏ sót 39% và 32% cửa sổ vuốt (`swipe_left` → `none` 41/104,
    `swipe_right` → `none` 31/96).
  - Vậy mà ở mức sự kiện nó vẫn phát lệnh cho 85–89% số cú vuốt.
  - Phần lớn cửa sổ bị bỏ sót không thành cử chỉ bị bỏ sót: các cửa sổ khác của cùng cú vuốt
    vẫn được nhận.
- **LSTM phát lệnh thừa nhiều nhất ở `swipe_left` (1,41) và `zoom_in` (1,33).** Đó là lệnh thứ
  hai cho cùng một cử chỉ, thứ mà cooldown của Phase 9 dẹp.

## 3. Các ô lớn ngoài đường chéo

Ma trận nhầm lẫn: `results/phase8/experiments/run_01/table1_confusion_<mô hình>.png`, có cả số
cửa sổ lẫn tỉ lệ theo hàng trong từng ô.

| Ô (số cửa sổ) | Luật | Rừng | LSTM | Ghép |
|---|---|---|---|---|
| `none` → hai lớp vuốt (trên 10 650 cửa sổ `none`) | 3 750 | 710 | 475 | 475 |
| `none` → hai lớp zoom | 939 | 167 | 141 | 165 |
| `zoom_in` ↔ `zoom_out` (trên 188 cửa sổ zoom) | 21 | 27 | 34 | 27 |
| hai lớp vuốt → `none` (trên 200 cửa sổ vuốt) | 62 | 72 | 30 | 31 |
| `swipe_left` ↔ `swipe_right` | 11 | 8 | 3 | 3 |

### 3.1. `none` → vuốt: tay chỉ trỏ di chuyển như một cú hất

Đây là ô lớn nhất của mọi mô hình. Tay chỉ trỏ (`B0A`, `B0B`) chiếm 64% số cửa sổ `none` của val
(6 819 / 10 650). Tỉ lệ báo nhầm của nó không cao (rừng 5,8% và 9,7%; LSTM 3,5% và 5,9%),
nhưng tính theo số cửa sổ nó vẫn là nguồn báo nhầm lớn nhất.

**Giả thuyết A** (`results/phase6/notes.md` mục 4.1): bộ 15 đặc trưng không mô tả cấu hình ngón.
Vì vậy một bàn tay chỉ trỏ di chuyển nhanh trông như một cú hất mở bàn tay.

**Kiểm chứng ở Bảng 5 — đây là vòng cải tiến của Phase 8.** Thêm vào rừng 10 đặc trưng góc
khớp, các thứ khác giữ nguyên. Đó là góc gập trung bình và mức đổi góc gập ở khớp giữa của
từng ngón (`features.angle_features`).

| | 15 đặc trưng | + 10 góc khớp |
|---|---|---|
| Ô lớn nhất `none` → `swipe_left` | 366 | **190** |
| `none` → hai lớp vuốt | 710 | 393 |
| Báo nhầm `B0A` / `B0B` | 5,8% / 9,7% | 1,8% / 4,8% |
| macro-F1 | 0,436 | 0,492 |
| F1 sự kiện | 0,211 | 0,283 |
| Lệnh nhầm mỗi phút | 10,6 | 6,3 |

- Ô nhỏ đi gần một nửa, và mọi chỉ số khác cùng tốt lên. **Giả thuyết A đứng vững.**
- Có góc khớp, rừng báo nhầm còn ít hơn LSTM hiện tại: 6,3 so với 6,6 lệnh mỗi phút.

**Bằng chứng thứ hai, từ LSTM (bảng phụ).** Bỏ các khớp giữa của ngón, chỉ giữ 11 điểm (cổ tay,
gốc và đầu năm ngón): báo nhầm tay chỉ trỏ tăng gấp đôi, `B0A` 3,5% → 7,9% và `B0B` 5,9% →
11,7%. LSTM đang dùng chính các khớp đó để tách tay chỉ trỏ khỏi cú hất.

**Giả thuyết B** (cùng mục): quota `none` chia đều theo nhãn gốc, nên tay chỉ trỏ chỉ chiếm 20%
lớp `none` của train, so với 64% ở val. Bảng phụ kiểm bằng quota theo tỉ lệ tự nhiên:

- báo nhầm tay chỉ trỏ giảm mạnh: LSTM `B0A` 3,5% → 1,1% và `B0B` 5,9% → 3,9%; rừng 5,8% → 4,1%
  và 9,7% → 7,3%;
- nhưng F1 hai lớp zoom tụt: LSTM 0,51 / 0,53 → 0,38 / 0,46; rừng 0,37 / 0,42 → 0,27 / 0,34;
- nên macro-F1 không khá lên: LSTM −0,002 (không đủ bằng chứng), rừng −0,017.

Giả thuyết B **đúng một nửa**. Lệch phân bố là có thật, nhưng đổi quota chỉ chuyển lỗi từ vuốt
sang zoom.

- **Giải thích có thể kiểm:** quota tự nhiên bớt các loại `none` hiếm như `G07` "xòe tay hai
  lần" — đúng loại hay bị nhận thành zoom (mục 4). Mô hình vì thế còn ít ví dụ âm cho zoom.
- **Phép thử:** dùng quota tự nhiên nhưng giữ đủ cửa sổ `G07`. Nếu giải thích đúng, F1 zoom
  phải trở lại.

### 3.2. `zoom_in` ↔ `zoom_out`: nhiều khả năng là lỗi của nhãn

27 cửa sổ với rừng và 34 với LSTM, trên 188 cửa sổ zoom của val (14% và 18%).

- Ở mức sự kiện, lệnh sai loại phát ra trong lúc người diễn đang zoom là 0,50 + 0,53 lệnh mỗi
  phút với rừng, 0,27 + 0,27 với LSTM. Đó là loại "cử chỉ khác" của `G10`, `G11` trong
  `table1_false_by_src`.
- Theo ma trận nhầm lẫn, phần lớn số lệnh đó là zoom đảo chiều.

**Giả thuyết** (`results/phase6/notes.md` mục 4.3): luật nhãn của Phase 4 chọn khoảnh khắc chính
của cú zoom theo **độ lớn** thay đổi khoảng cách cái–trỏ, không xét dấu.

- Người diễn IPN hay mở rồi chụm trong cùng một đoạn `zoom_in`, nên các cửa sổ quanh pha chụm
  mang nhãn `zoom_in` dù ngón đang chụm.
- Phase 6 đã đo: cửa sổ `zoom_in` bị đoán `zoom_out` có `pinch_delta` trung vị −1,74, ngược hẳn
  với +1,49 của cửa sổ nhận đúng.

**Bằng chứng mới ở Bảng 5:** số cửa sổ zoom đảo chiều gần như không nhúc nhích khi đổi đặc trưng.

- Năm hàng cho 27, 29, 27, 27, 28, trong khi ô `none` → vuốt chạy từ 393 tới 914.
- Bỏ hẳn nhóm có dấu, gồm cả `pinch_delta` và `open_delta`, cũng chỉ thêm 2 cửa sổ.

Lỗi mà không thay đổi đặc trưng nào đụng tới được thì nhiều khả năng nằm ở nhãn.

**Phép thử:**

- chọn khoảnh khắc chính của zoom theo đúng chiều tên lớp nói: mở với `zoom_in`, chụm với
  `zoom_out`;
- dựng lại cửa sổ, chạy lại rừng cơ sở;
- dự đoán: ô đảo chiều giảm phần lớn, các ô khác gần như giữ nguyên.

Đây là thay đổi luật nhãn của Phase 4: cần người dùng quyết, và phải ghi trong báo cáo.

### 3.3. `D0X` → cử chỉ: chỗ duy nhất LSTM kém rừng

`D0X` ("không cử chỉ") là loại `none` duy nhất mà LSTM báo nhầm **nhiều hơn** rừng: 14,5% so
với 10,6% cửa sổ. Ở mức sự kiện, nó là nguồn lệnh nhầm lớn nhất của LSTM: 1,75 lệnh mỗi phút,
ngang `B0B` (1,71) và gần gấp đôi `B0A` (0,90).

**Giả thuyết C** (`results/phase6/notes.md` mục 4.1): báo nhầm `D0X` là lúc tay đưa vào hoặc ra
khỏi khung hình. Đó là chuyển động nhanh, và tay chỉ có mặt ở một phần cửa sổ.

- Phase 6 đo được: cửa sổ `D0X` bị báo nhầm có tốc độ ngang đỉnh 7,1–8,5 lòng bàn tay mỗi giây,
  so với 2,9 của cửa sổ `D0X` nhận đúng.
- LSTM đọc thẳng chuyển động của 21 điểm, nên có thể nhạy với các cú đưa tay này hơn rừng.

**Phép thử, nằm sẵn trong Phase 9:**

- cơ chế "hạ tay xuống xoá trạng thái" của `ActivationFSM`;
- bảng đánh đổi `MIN_PRESENCE` (`results/phase9/tradeoff.md`).

Nếu giả thuyết C đúng, khi nâng `MIN_PRESENCE` thì lệnh nhầm `D0X` phải giảm nhanh hơn hẳn lệnh
nhầm tay chỉ trỏ, vì tay chỉ trỏ thường nằm trọn trong khung hình.

## 4. Loại `none` nào gây báo nhầm

**Mức cửa sổ** — tỉ lệ cửa sổ `none` bị đoán thành cử chỉ (`table1_none_by_src`):

| Nhãn gốc | Số cửa sổ | Luật | Rừng | LSTM | Ghép |
|---|---|---|---|---|---|
| `B0A` chỉ một ngón | 3 491 | 51,6% | 5,8% | 3,5% | 4,1% |
| `B0B` chỉ hai ngón | 3 328 | 51,7% | 9,7% | 5,9% | 5,2% |
| `D0X` không cử chỉ | 1 433 | 40,9% | 10,6% | **14,5%** | **14,7%** |
| `G07` xòe tay hai lần | 403 | 34,7% | **19,1%** | 13,4% | **18,4%** |
| `G03`, `G04` hất lên, hất xuống | 322, 299 | 24,8%, 21,1% | 6,2%, 2,7% | 4,0%, 2,3% | 1,9%, 1,7% |
| `G01`, `G02`, `G08`, `G09` bấm ngón | 315–371 mỗi nhãn | 14–29% | 6,0–8,3% | 0,3–2,2% | 1,1–3,2% |

**Mức sự kiện** — lệnh nhầm mỗi phút video, theo đoạn nhãn đang diễn ra lúc phát lệnh
(`table1_false_by_src`):

| Lúc phát lệnh | Luật | Rừng | LSTM | Ghép |
|---|---|---|---|---|
| `B0A` | 9,07 | 1,91 | 0,90 | 1,13 |
| `B0B` | 8,54 | 3,31 | 1,71 | 1,28 |
| `D0X` | 3,84 | 1,51 | 1,75 | 1,71 |
| `G07` | 1,28 | 0,68 | 0,40 | 0,68 |
| sáu loại `none` còn lại, cộng lại | 3,69 | 1,35 | 0,35 | 0,43 |
| lúc một cử chỉ khác loại đang diễn ra | 3,06 | 1,63 | 0,98 | 1,05 |
| lệnh thừa cho cùng cử chỉ | 0,33 | 0,23 | 0,48 | 0,32 |
| **Tổng** | **29,8** | **10,6** | **6,6** | **6,6** |

- **Với LSTM và mô hình ghép, tay chỉ trỏ và `D0X` gây khoảng hai phần ba số lệnh nhầm:** 4,4
  trên 6,6 lệnh mỗi phút với LSTM, 4,1 trên 6,6 với ghép.
- **`G07` có tỉ lệ cao nhất với rừng** (19,1%), gần như toàn bộ thành zoom
  (`results/phase6/notes.md` mục 4.4). Mô hình ghép lấy zoom từ rừng nên thừa hưởng lỗi này
  (18,4%).
- **Các cử chỉ ngón khác của IPN gần như hết là vấn đề với LSTM** (bấm ngón, hất lên, hất
  xuống): cộng lại 0,35 lệnh mỗi phút.
- **Mô hình luật không dùng được để điều khiển:** riêng tay chỉ trỏ đã cho 17,6 lệnh nhầm mỗi
  phút. Nó chỉ còn là hàng đường cơ sở.

## 5. Bảng 2–7 và bảng phụ

### 5.1. Bảng 2 — chuẩn hoá: gốc cổ tay frame đầu so với từng frame

| | Rừng: frame đầu | Rừng: từng frame | LSTM: frame đầu | LSTM: từng frame |
|---|---|---|---|---|
| F1 `swipe_left` / `swipe_right` | 0,212 / 0,232 | **0,077 / 0,088** | 0,397 / 0,376 | 0,373 / 0,271 |
| F1 `zoom_in` / `zoom_out` | 0,368 / 0,417 | 0,275 / 0,357 | 0,506 / 0,533 | **0,698 / 0,655** |
| Cửa sổ vuốt bị đoán ngược hướng | 8 | 21 | 3 | 5 |
| Cửa sổ vuốt bị đoán `none` | 72 | 128 | 30 | 25 |
| macro-F1 | 0,436 | 0,348 | 0,556 | 0,592 |
| F1 sự kiện | 0,211 | 0,160 | 0,334 | 0,304 |

- **Với rừng, dự đoán của SPEC đúng.** Gốc từng frame xoá quỹ đạo cổ tay:
  - F1 hai lớp vuốt sập còn khoảng một phần ba;
  - số cửa sổ vuốt bị đoán ngược hướng tăng gần gấp ba.
- **Với LSTM thì không.** Vuốt chỉ giảm nhẹ, còn zoom tốt lên hẳn (+0,19 và +0,12).
  - Hai mức cho hai kết luận ngược nhau: macro-F1 +0,036, nhưng F1 sự kiện −0,030.
  - Mỗi chênh lệch chỉ cỡ 1,3 lần độ lệch chuẩn giữa các seed.
- **Giả thuyết:**
  - Khi cổ tay bị ghim ở gốc, LSTM vẫn đọc được chiều vuốt từ cách các ngón chuyển động so với
    cổ tay trong cú hất: ngón trễ sau cổ tay, bàn tay xoay.
  - Bỏ chuyển động tịnh tiến thì cú chụm–mở của zoom nổi rõ hơn.
- **Phép thử:**
  - Cho LSTM gốc từng frame chấm các cú vuốt tổng hợp "bàn tay cứng" (`augment.rigid_swipes`,
    k = 0: giữ quỹ đạo cổ tay, bỏ mọi đổi dáng tay).
  - Nếu nó không nhận được những cú vuốt đó trong khi LSTM gốc frame đầu nhận được, thì chiều
    vuốt của nó đến từ dáng tay.
- **Lưu ý:** LSTM gốc từng frame chọn checkpoint ở epoch 147 trên tối đa 150, tức còn đang học.
  Con số của nó chưa phải mức cuối.
- **Kết luận: giữ gốc frame đầu (luật 6).** Nó là điều kiện sống còn của rừng, và với LSTM cũng
  tốt hơn ở mức sự kiện.
- **Một ý cho sau này:** LSTM nhận zoom tốt hơn ở gốc từng frame, nên có thể đưa **cả hai** biểu
  diễn vào LSTM. Việc này đổi đầu vào 42 chiều, nằm ngoài Phase 8.

### 5.2. Bảng 3 — độ dài cửa sổ

Kết luận dựa trên mức sự kiện. Đổi độ dài cửa sổ thì đổi cả tập cửa sổ val, nhưng video val
giữ nguyên.

| | 0,8 s | 1,2 s | 1,6 s |
|---|---|---|---|
| Rừng: F1 sự kiện (vuốt / zoom) | 0,202 (0,167 / 0,294) | 0,211 (0,160 / 0,333) | 0,215 (0,165 / 0,332) |
| LSTM: F1 sự kiện (vuốt / zoom) | 0,244 (0,196 / 0,351) | **0,334** (0,287 / 0,407) | 0,267 (0,208 / 0,383) |
| LSTM: lệnh nhầm mỗi phút | 9,8 | **6,6** | 9,3 |

- **LSTM tốt nhất ở 1,2 giây, cho cả hai cặp lớp.** Nó hơn hai độ dài kia 3–4 lần độ lệch chuẩn.
  Độ dài tối ưu không khác nhau giữa vuốt và zoom.
- **Rừng gần như không nhạy với độ dài:** chênh lệch tối đa 0,013. Chỉ zoom chịu thiệt ở 0,8
  giây.
- **Ý tưởng "cửa sổ ngắn hơn cho vuốt" không được ủng hộ** (`results/phase6/notes.md` mục 7.6).
  Ở 0,8 giây, F1 sự kiện của vuốt không tăng với rừng (0,167 so với 0,160) và giảm với LSTM.
- `WIN_SEC = 1,2` giữ nguyên.

### 5.3. Bảng 4 — chia theo người so với ngẫu nhiên theo cửa sổ

| | Rừng | LSTM |
|---|---|---|
| Theo người (split chính thức) | 0,436 | 0,556 |
| Ngẫu nhiên theo cửa sổ (rò rỉ) | 0,540 | 0,701 |
| Chênh lệch | **+0,104** | **+0,145** |

- **Phép chia sai thổi phồng macro-F1 nhiều hơn cả việc đổi từ rừng sang LSTM** (+0,12 ở split
  chính thức).
- **Phần thổi phồng dồn vào các lớp cử chỉ:** LSTM `swipe_left` 0,40 → 0,62, `zoom_in` 0,51 →
  0,73. Lớp `none` gần như không đổi (0,95 → 0,96 với rừng).
  - Mỗi cử chỉ sinh vài cửa sổ chồng lấn nhau 1,0 trên 1,2 giây.
  - Chia ngẫu nhiên thì gần như mọi cửa sổ cử chỉ của val có "anh em sinh đôi" trong train.
- **Không tới 98–99% như cẩm nang cảnh báo.** Hàng rò rỉ giữ đúng phân bố lớp của val (96%
  `none`), và lấy mẫu con `none` của train như cấu hình chính.
  - Vì vậy phần lớn cửa sổ `none` của val không có anh em trong train.
  - Báo nhầm `none` vẫn kìm precision của các lớp cử chỉ.
  - Mức rò rỉ ở đây vì thế là cận dưới.
- Hàng thứ ba (tập tự quay) chỉ có khi bật Phase 11.

### 5.4. Bảng 5 — loại bỏ và thêm đặc trưng (rừng)

| Biến thể | Số đặc trưng | macro-F1 | F1 vuốt trái / phải | Vuốt đoán ngược hướng | Zoom đoán ngược chiều | `none` → vuốt |
|---|---|---|---|---|---|---|
| Đủ 15 | 15 | 0,436 | 0,212 / 0,232 | 8 | 27 | 710 |
| Bỏ nhóm có dấu | 10 | 0,407 | 0,103 / 0,200 | **53** | 29 | 914 |
| Bỏ `straightness` | 14 | 0,425 | 0,217 / 0,219 | 8 | 27 | 740 |
| Bỏ `presence` | 14 | 0,431 | 0,209 / 0,217 | 8 | 27 | 719 |
| Thêm góc khớp | 25 | **0,492** | 0,283 / 0,275 | 2 | 28 | **393** |

- **Bỏ nhóm có dấu chỉ làm cặp vuốt sập, không làm cặp zoom sập.** SPEC đã dự đoán "hai cặp
  lớp sập hoàn toàn", nhưng:
  - với vuốt: cửa sổ bị đoán ngược hướng tăng 6,6 lần (8 → 53), F1 `swipe_left` giảm một nửa;
  - với zoom: gần như không đổi (F1 0,39 / 0,39, đảo chiều 29).
- **Giả thuyết:**
  - Rừng dựng lại chiều của zoom từ `open_start` và `open_end`. Hai đặc trưng này vẫn còn, và
    hiệu của chúng chính là `open_delta`.
  - Với vuốt thì không đặc trưng nào còn lại mang chiều ngang: `max_vx`, `horiz_ratio`,
    `straightness` đều không dấu.
- **Phép thử:** bỏ thêm `open_start` và `open_end`. Nếu giả thuyết đúng, số cửa sổ zoom đảo chiều
  phải tăng vọt.
- **`straightness` và `presence` gần như không đóng góp** (−0,011 và −0,005). Với rừng, chênh lệch
  cỡ này nhỏ hơn mức dao động giữa các nhóm người (mục 6), nên đọc là "không ảnh hưởng".
- **Thêm góc khớp là cải thiện lớn nhất của cả loạt khảo sát cho rừng** (mục 3.1).

### 5.5. Bảng 6 — năm seed

| Mô hình | macro-F1 | F1 sự kiện | Lệnh nhầm mỗi phút |
|---|---|---|---|
| Rừng | 0,433 ± 0,003 | 0,209 ± 0,004 | 10,6 ± 0,1 |
| LSTM | 0,549 ± 0,027 | 0,313 ± 0,023 | 7,5 ± 0,9 |
| Ghép | 0,492 ± 0,022 | 0,286 ± 0,015 | 7,4 ± 0,5 |

- **LSTM − rừng:** +0,116 macro-F1 và +0,104 F1 sự kiện, hơn 4 lần độ lệch chuẩn. Kết luận chắc
  chắn.
- **Ghép − LSTM trên val chính thức:** −0,057 macro-F1 (2,1 lần độ lệch chuẩn) và −0,026 F1 sự
  kiện (1,2 lần).
  - Ghép kém hơn, nhưng ở mức sự kiện thì chỉ vừa vượt ngưỡng.
  - Mô hình ghép tồn tại vì bàn tay của người dùng (`results/phase7/notes.md` mục 9). Val của
    IPN không đo được điều đó.
- **Con số LSTM "không lạc quan" mà Phase 7 hẹn là 0,549 ± 0,027.**
  - Ở mức cửa sổ, mô hình của demo (seed 42) gần trung bình: 0,556.
  - Ở mức sự kiện, nó lại là seed tốt nhất trong năm: 0,334 so với trung bình 0,313.
- **LSTM dao động mạnh theo từng lớp:** F1 `swipe_left` ± 0,08, `zoom_in` ± 0,09 giữa các seed.
  So từng lớp giữa hai lần học LSTM đơn lẻ phải rất thận trọng.

### 5.6. Bảng 7 — k-fold theo nhóm người

Năm fold trên 37 người của train và val. LSTM mỗi fold học đúng 86 epoch, không chọn gì trên fold
giữ lại.

| Mô hình | macro-F1 (thấp nhất – cao nhất) | F1 sự kiện (thấp nhất – cao nhất) | Lệnh nhầm mỗi phút |
|---|---|---|---|
| Rừng | 0,477 ± 0,016 (0,464 – 0,500) | 0,220 ± 0,022 (0,190 – 0,244) | 10,8 ± 2,1 |
| LSTM | 0,559 ± 0,069 (0,443 – 0,609) | 0,285 ± 0,060 (0,181 – 0,326) | 9,3 ± 3,8 |
| Ghép | 0,555 ± 0,029 (0,519 – 0,586) | 0,301 ± 0,045 (0,246 – 0,364) | 7,8 ± 1,8 |

- **Hệ thống hoạt động khác nhau nhiều tuỳ người.**
  - Dao động giữa các nhóm người lớn hơn giữa các seed: LSTM 0,069 so với 0,027, rừng 0,016 so
    với 0,003.
  - Theo từng người (`table7_by_subject`), macro-F1 chạy từ 0,23 tới 0,81 với rừng, từ 0,40 tới
    0,86 với LSTM.
- **Mô hình ghép ít tụt hơn ở nhóm người khó.**
  - Ở fold 3, LSTM tụt còn 0,443 macro-F1, 0,181 F1 sự kiện và 16 lệnh nhầm mỗi phút. Mô hình
    ghép giữ được 0,552, 0,246 và 10,5.
  - Trung bình năm fold, ghép ngang LSTM ở mức cửa sổ (0,555 so với 0,559) và nhỉnh hơn ở mức
    sự kiện (0,301 so với 0,285). Từng fold thì lúc hơn lúc kém, nên **không đủ bằng chứng** để
    nói ghép hơn LSTM.
  - Điều chắc hơn là độ dao động: ghép dao động ít hơn LSTM ở cả hai mức.
- **Val chính thức khó hơn trung bình với rừng:** 0,436, so với 0,477 ± 0,016 qua năm fold.
- Mỗi người chỉ có khoảng 15 cử chỉ, nên con số từng người còn nhiễu.

### 5.7. Bảng phụ

Mỗi hàng một seed, so với độ lệch chuẩn giữa năm seed của Bảng 6.

| Biến thể LSTM | Δ macro-F1 | Δ F1 sự kiện | Đọc là |
|---|---|---|---|
| GRU thay LSTM | +0,024 | +0,007 | không đủ bằng chứng: hai loại ô như nhau |
| hidden 64 | −0,015 | −0,041 | giữ 128 |
| Gộp mean / max | −0,034 / −0,076 | −0,050 / −0,099 | giữ `last`: với mô hình nhân quả, bước cuối mang quyết định |
| Không tăng cường | −0,063 | −0,032 | tăng cường có ích; câu hỏi Phase 7 để ngỏ đã có câu trả lời |
| Chỉ đổi dáng ngón phụ, p = 0,5 | −0,053 | −0,078 | giữ tắt |
| Chỉ thêm bàn tay đứng yên, 0,1 × train | −0,043 | −0,083 | giữ tắt |
| 11 điểm rút gọn | −0,007 | −0,061 | giữ 21 điểm; báo nhầm tay chỉ trỏ tăng gấp đôi (mục 3.1) |
| Biên khoảnh khắc chính 0 / 6 bước | (nhãn val khác) | −0,031 / −0,077 | giữ 3 bước |
| Quota `none` theo tỉ lệ tự nhiên | −0,002 | +0,013 | không đủ bằng chứng (mục 3.1) |

| Biến thể rừng | Δ macro-F1 | Δ F1 sự kiện | Đọc là |
|---|---|---|---|
| Biên khoảnh khắc chính 0 / 6 bước | (nhãn val khác) | −0,025 / +0,004 | giữ 3 bước |
| Quota `none` theo tỉ lệ tự nhiên | −0,017 | −0,007 | giữ quota đều |

- **Hai phép tăng cường của Phase 7, giờ đo riêng từng phép** (`results/phase7/notes.md` mục
  9.7): mỗi phép, một mình, đều làm LSTM kém đi trên val của IPN.
  - Lợi ích có thể có của chúng nằm ở bàn tay của người dùng, thứ val của IPN không đo được.
  - Giữ tắt như hiện tại.
- **Ba biến thể LSTM chọn checkpoint sát epoch tối đa:** 11 điểm ở epoch 150, biên 0 ở 141, gốc
  từng frame (Bảng 2) ở 147. Chúng còn đang học, nên con số có thể còn lên.

## 6. Giới hạn khi đọc các bảng

- **Quy tắc "không đủ bằng chứng" chỉ đo độ ngẫu nhiên của việc học.**
  - Với rừng, năm seed gần như trùng nhau (độ lệch chuẩn 0,003 macro-F1). Vì vậy gần như mọi
    chênh lệch của rừng đều "lớn hơn độ lệch chuẩn", kể cả −0,005 khi bỏ `presence`.
  - Độ bất định thật khi suy ra người mới lớn hơn nhiều: dao động giữa các nhóm người ở Bảng 7
    là 0,016 với rừng và 0,069 với LSTM.
  - Chênh lệch dưới khoảng 0,02 nên đọc là "không ảnh hưởng thực tế".
- **Mức cửa sổ không so được giữa các hàng đổi nhãn** (độ dài cửa sổ, biên khoảnh khắc chính),
  vì tập cửa sổ val đổi theo. Các hàng đó kết luận bằng mức sự kiện.
- **Mỗi hàng của bảng phụ chỉ là một seed.** Với LSTM, một seed lệch ± 0,027 macro-F1.
- **Mọi con số là trên IPN.** Webcam, bàn tay và cách làm cử chỉ của người dùng chỉ đo được ở
  Phase 10, và ở Phase 11 nếu bật.
- **Mức sự kiện dùng bộ lọc `edge`, chưa có máy trạng thái.** Số lệnh nhầm mỗi phút ở đây là
  cận trên của hệ thống cuối.

## 7. Hệ quả cho Phase 9, và các quyết định đang chờ

**Cho máy trạng thái:**

- **Khoảng cách cần thu hẹp còn rất lớn.** LSTM và mô hình ghép đang phát khoảng 6,6 lệnh nhầm
  mỗi phút trên video IPN.
  - SPEC lấy 0,5 lần mỗi phút làm mốc chấp nhận được khi làm việc bình thường trên webcam. Hai
    kịch bản không giống nhau, nhưng cách nhau khoảng 13 lần.
  - Trong lúc đó phải giữ recall (đang 0,85–0,94), và đưa số lệnh trên một cử chỉ về 0,9–1,1
    (đang 1,03–1,20).
- **Hai phần ba số lệnh nhầm đến từ tay chỉ trỏ và `D0X`** (mục 4).
  - Đồng thuận k trên n chỉ dẹp được các cụm báo nhầm ngắn.
  - Báo nhầm kéo dài khi tay chỉ trỏ lướt ngang thì cần đặc trưng góc khớp (mục 3.1).
- **Chấm máy trạng thái không phải học lại.** Bản ghi giữ mọi xác suất. Từ sửa đổi 2026-10-23,
  dấu vân tay của bản ghi không tính tầng kích hoạt.
  - Mọi cấu hình máy trạng thái chấm lại được trên val mà không phải học lại.
  - Dựng lại Bảng 1 với `EVENT_FILTER = "fsm"` là đủ cho mục "Bảng 1 có cột F1 mức sự kiện"
    của Phase 9.

**Quyết định của người dùng:**

1. **Có thêm góc khớp vào mô hình chính không?**
   - Đây là quyết định "thêm đặc trưng cấu hình ngón" đang chờ từ Phase 6
     (`results/phase6/notes.md` mục 8.6). Giờ đã có số liệu: rừng +0,055 macro-F1, lệnh nhầm
     10,6 → 6,3 mỗi phút.
   - Nó đổi vector đặc trưng 15 chiều của SPEC (Phase 2), nên rừng và mô hình ghép phải học lại.
     LSTM không bị ảnh hưởng.
   - Khi đã có góc khớp, nên chạy lại `sweep_rigid.py`: tăng cường "bàn tay cứng" chỉ đáng bật
     khi mô hình có cách khác để nhận ra tay chỉ trỏ.
   - **Lưu ý khi làm:** dấu vân tay của bản ghi tính spec, hằng số `config.py` và dữ liệu,
     nhưng **không tính mã nguồn**. Đổi `FEATURE_NAMES` thì phải xoá
     `results/phase8/records/rf_*` trước khi chạy lại `run_experiments.py`; nếu không, các bảng
     dùng lại dự đoán của rừng 15 đặc trưng mà không báo gì. Bản ghi `prod_*` thì tự hết hạn,
     vì khoá của chúng có mã băm của file mô hình.
2. **Có gán nhãn zoom theo đúng chiều không?** Phép thử ở mục 3.2. Việc này đổi luật nhãn của
   Phase 4 và phải ghi trong báo cáo.
3. **Mô hình của demo.** Val chính thức nghiêng về LSTM. Năm fold người và lần thử trực tiếp của
   Phase 7 nghiêng về mô hình ghép. Nên giữ `--model hybrid`.
4. **Lần chạy duy nhất trên test** vẫn hoãn, tới khi chốt máy trạng thái (Phase 9) và cấu hình cuối
   (Phase 10).

## 8. Định nghĩa hoàn thành

| Mục | Trạng thái |
|---|---|
| Cả bảy bảng có mặt trong `results/phase8/`, mỗi bảng kèm ít nhất một câu diễn giải | **đạt:** `experiments/run_01`; diễn giải ở mục 2 và 5 |
| Hình nhiệt ma trận nhầm lẫn có số trong ô, cho cả ba mô hình | **đạt:** `table1_confusion_{rules,rf,lstm,hybrid}.png`, có cả số cửa sổ lẫn tỉ lệ theo hàng |
| Ít nhất hai ô ngoài đường chéo có phân tích bằng lời, kèm giả thuyết kiểm chứng được | **đạt:** ba ô, mục 3 |
| Phân tích loại `none` nào bị nhận nhầm nhiều nhất, theo `src_label` | **đạt:** mục 4 |
| Đã chạy vòng cải tiến ít nhất một lần | **đạt:** ô lớn nhất `none` → `swipe_left` giảm 366 → 190 khi thêm góc khớp (mục 3.1) |
| `results/TEST_USED.log` chỉ có dòng của lần chạy cuối | **chưa tới lượt:** file chưa tồn tại, test chưa bị chạm; lần chạy cuối hoãn theo quyết định 2026-10-22 |
