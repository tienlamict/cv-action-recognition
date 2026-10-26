# Phase 7 — Ghi chú LSTM trên chuỗi 42 chiều

> Claude viết ngày 2026-10-09. Số liệu lấy từ:
>
> - `results/phase7/train_lstm/run_02`: mô hình chính, cũng là mô hình của demo;
> - `run_03`, `run_04`: hai lần khảo sát không tăng cường;
> - `results/phase7/probe_swipes/run_01`: thăm dò vuốt.
>
> Tái lập bằng các lệnh `train_lstm.py` và `probe_swipes.py --model lstm` ghi trong README.
>
> Huấn luyện tất định: `run_02` cho đúng từng con số của `run_01`, cả lịch sử 144 epoch lẫn
> ma trận nhầm lẫn. `run_01` là lần chạy đầu. Checkpoint của nó không nạp được vì lỗi lưu
> `torch.__version__` (đã sửa, mục 7), nên đã được thay bằng checkpoint của `run_02`.
>
> **Cập nhật 2026-10-10 (mục 9):**
>
> - Mô hình LSTM của demo giờ là `train_lstm/run_07`. Nó học trên đúng quỹ đạo của `run_02`
>   (trùng từng chữ số suốt 106 epoch), chỉ khác cách chọn checkpoint: theo trung bình trượt
>   10 epoch, nên checkpoint là epoch 86 thay vì 124.
> - Mục 1–8 vẫn là số liệu của `run_02`. Tái tạo bằng `python scripts/train_lstm.py
>   --stop-smooth 1`.
> - Demo nên dùng `--model hybrid`: vuốt theo LSTM, zoom theo rừng ngẫu nhiên.
>
> **Cập nhật 2026-10-26 (Phase 10):** LSTM của demo (`LSTM_MODEL_PATH`) giờ là
> `train_lstm/run_08`, bản mục 9.3 bác vì cái giá trên val. Trên webcam, người dùng làm zoom
> với nhẫn và út duỗi: `run_07` không nhận cú nào, còn `run_08` nhận được. Người dùng chọn
> đổi. `results/phase7/lstm_model.pt` (`PHASE7_LSTM_PATH`) vẫn là `run_07`, mô hình chính
> của các bảng ở đây. Số liệu và cái giá đo trên webcam: `results/phase10/notes.md` mục 1.

## 1. Cấu hình

- **Đầu vào:** cửa sổ đã chuẩn hoá `(18, 21, 2)` reshape thành `(18, 42)` bằng
  `datasets.window_sequence`, cùng hàm demo dùng. Bước mất tay lấy bước có tay gần nhất
  trước nó: 5–8% số cửa sổ có ít nhất một bước như vậy, 1–1,5% số bước.
- **Tăng cường:** đủ sáu phép của Phase 4, tạo mới mỗi epoch, chỉ trên train. 720 bản trong
  144 epoch (0,15%) bị `normalize_window` từ chối và được thay bằng cửa sổ gốc.
- **Mô hình:** LSTM một chiều, 2 lớp × 128, dropout 0,3, lấy đầu ra ở bước cuối, 5 lớp.
- **Học:** Adam (lr 0,001), lô 64, CrossEntropy có trọng số lớp `none` 0,40 và các lớp cử chỉ
  1,59–1,63. Dừng sớm khi macro-F1 val không tăng sau 20 epoch.
- **Chạy:** 144 epoch, 23 phút trên CPU 4 luồng. Epoch tốt nhất là 124.

## 2. Ba mô hình trên cùng tập val

11 038 cửa sổ, cùng các cửa sổ cho cả ba mô hình (`comparison`).

| Mô hình | macro-F1 | F1 none | F1 swipe_left | F1 swipe_right | F1 zoom_in | F1 zoom_out |
|---|---|---|---|---|---|---|
| Đoán ngẫu nhiên đều | 0,0796 | | | | | |
| Luôn đoán `none` | 0,1964 | | | | | |
| Luật (Phase 5) | 0,2305 | 0,714 | 0,056 | 0,043 | 0,164 | 0,176 |
| Rừng ngẫu nhiên (Phase 6) | 0,4361 | 0,951 | 0,212 | 0,232 | 0,368 | 0,417 |
| **LSTM (Phase 7)** | **0,6014** | 0,974 | 0,471 | 0,406 | 0,580 | 0,576 |

**LSTM thắng rừng ngẫu nhiên ở mọi lớp.** Recall các lớp cử chỉ là 0,72–0,90, và báo nhầm
`none` giảm từ 8,2% (877 cửa sổ) xuống 4,7% (495 cửa sổ).

**Nhưng 0,6014 là con số lạc quan.**

- Macro-F1 val dao động mạnh giữa hai epoch liền nhau: ở 40 epoch cuối nó chạy từ 0,39 tới
  0,60. Mỗi lớp cử chỉ của val chỉ có 94–104 cửa sổ, nên vài cửa sổ đổi nhãn là F1 đã đổi
  vài điểm.
- Checkpoint là epoch có macro-F1 val **cao nhất**, tức đỉnh của chuỗi nhiễu đó, chọn trên
  chính tập val. Rừng thì không chọn gì trên val.
- 20 epoch cuối trung bình **0,532 ± 0,036**. Đây là mức LSTM thường đạt, và nó vẫn hơn
  rừng rõ rệt.

Con số không lạc quan sẽ đến từ năm seed (Bảng 6 của Phase 8) và từ lần chạy duy nhất trên
tập test.

## 3. Đường học và điểm bắt đầu quá khớp

(`training_curves.png`, `history`. Cả train lẫn val đo cùng một cách: chế độ eval, không
tăng cường.)

**Mô hình chính (có tăng cường), trung bình trượt 10 epoch:**

| Tới epoch | Loss train | Loss val | macro-F1 val |
|---|---|---|---|
| 10 | 0,500 | 0,925 | 0,302 |
| 20 | 0,252 | 0,523 | 0,425 |
| 40 | 0,110 | 0,470 | 0,459 |
| 80 | 0,036 | 0,443 | 0,525 |
| 140 | 0,012 | 0,448 | 0,535 |

- Loss val giảm nhanh tới khoảng epoch 20, rồi chững lại quanh 0,43–0,50 tới hết.
- Loss train vẫn giảm thêm 20 lần, từ 0,25 xuống 0,012.
- **Từ khoảng epoch 20, khoảng hở bắt đầu nới rộng:** gần như mọi thứ mô hình học thêm trên
  train không còn chuyển sang val.
- Nhưng loss val **không quay đầu đi lên** trong 144 epoch. Trung bình trượt thấp nhất ở
  epoch 128. Tăng cường mới mỗi epoch cùng dropout giữ nó lại, và macro-F1 val vẫn nhích lên
  chậm.

**Bản không tăng cường.** Lệnh `train_lstm.py --no-augment`; checkpoint nằm trong thư mục
chạy, không thay mô hình của demo.

- **`run_03`** dừng sớm như bản chính, ở epoch 40. Nó dừng vì macro-F1 val không vượt được
  đỉnh 0,5615 của epoch 20, mà đỉnh đó là nhiễu: đường làm mượt khi ấy mới 0,445 và còn
  đang lên.
- **`run_04`** chạy đủ 150 epoch, không dừng sớm (`--patience 150`). Trung bình trượt 10
  epoch:

| Tới epoch | Loss train | Loss val | macro-F1 val |
|---|---|---|---|
| 10 | 0,401 | 0,806 | 0,341 |
| 20 | 0,135 | 0,542 | 0,445 |
| 40 | 0,025 | 0,501 | 0,488 |
| 60 | 0,024 | 0,598 | 0,475 |
| 100 | 0,019 | 0,665 | 0,495 |
| 150 | 0,000 | 0,645 | 0,523 |

- **Không tăng cường, điểm bắt đầu quá khớp hiện rõ.** Loss train về gần 0 từ khoảng epoch
  40. Loss val (làm mượt) thấp nhất ở **epoch 38** (0,490), rồi tăng lên 0,56–0,67: mô hình
  ngày càng tự tin vào những cửa sổ nó đoán sai trên người mới.
- macro-F1 val không sụt theo (0,47–0,52). Mô hình vẫn đoán đúng chừng ấy cửa sổ, chỉ tự tin
  quá mức ở những cửa sổ sai.

**So hai bản:**

| | Có tăng cường (`run_02`) | Không tăng cường (`run_04`) |
|---|---|---|
| macro-F1 val ở epoch được chọn | 0,6014 (epoch 124) | 0,5615 (epoch 20) |
| macro-F1 val, 20 epoch cuối | 0,532 ± 0,036 | 0,512 ± 0,020 |
| Loss val làm mượt thấp nhất | 0,414, ở epoch 128 | 0,490, ở epoch 38 |
| Loss val, 10 epoch cuối | 0,468 | 0,645 |

- **Tác dụng rõ nhất của tăng cường là chặn quá khớp:** có nó thì loss val không quay đầu.
- Trên macro-F1 ở mức thường đạt, chênh lệch 0,02 nhỏ hơn độ lệch chuẩn. **Chưa đủ bằng chứng
  để kết luận** tăng cường làm mô hình tốt hơn. Bảng năm seed của Phase 8 sẽ trả lời.

## 4. Mức sự kiện và báo nhầm theo nhãn gốc

**Mức sự kiện xấp xỉ** (`events_approx`): mỗi cử chỉ là một chuỗi cửa sổ dương liền nhau.

| Lớp | Luật | Rừng | LSTM | LSTM: có cửa sổ ngược chiều |
|---|---|---|---|---|
| `swipe_left` | 67% | 70% | **96%** | 7% |
| `swipe_right` | 59% | 70% | **89%** | 15% |
| `zoom_in` | 70% | 59% | **89%** | 26% |
| `zoom_out` | 76% | 56% | **84%** | 20% |

Ba cột đầu là tỉ lệ cử chỉ có ít nhất một cửa sổ được nhận đúng.

- Cột cuối vẫn cao với zoom: trong một cú zoom, thường có cửa sổ bị đoán ngược chiều. Trên
  ma trận nhầm lẫn, đó là `zoom_in` → `zoom_out` 19 và `zoom_out` → `zoom_in` 13.
- Giả thuyết đã nêu ở Phase 6 (`results/phase6/notes.md` mục 4.3) vẫn áp dụng. Luật nhãn
  chọn khoảnh khắc chính theo độ lớn chứ không theo chiều, nên cửa sổ quanh lúc tay "thu
  lại" sau cú zoom mang nhãn của cú zoom.

**Báo nhầm theo nhãn gốc** (`none_false_alarms_by_src`, tỉ lệ cửa sổ `none` bị báo thành cử
chỉ):

| Nhãn gốc | Số cửa sổ | Rừng | LSTM |
|---|---|---|---|
| `B0A` chỉ một ngón | 3491 | 5,8% | 3,0% |
| `B0B` chỉ hai ngón | 3328 | 9,7% | 4,7% |
| `D0X` không cử chỉ | 1433 | 10,6% | 10,5% |
| `G07` xòe tay hai lần | 403 | 19,1% | 13,7% |
| `G01`, `G02`, `G08`, `G09` | 315–371 mỗi nhãn | 6,0–8,3% | 0,3–1,1% |

LSTM giảm một nửa báo nhầm với tay chỉ trỏ, và gần như không còn nhầm các cử chỉ ngón khác
của IPN. `D0X` thì không đổi.

## 5. LSTM coi gì là một cú vuốt

`probe_swipes.py --model lstm` lặp lại đúng các phép thử của Phase 6 (`results/phase6/notes.md`
mục 7.2), cùng seed nên cùng độ rung. Thử trên các cửa sổ vuốt thật của val mà LSTM đang nhận
đúng: 94 cú trái, 71 cú phải. Số ghi dạng trái / phải.

| Sửa đổi | Rừng (Phase 6) | LSTM |
|---|---|---|
| Không sửa (chỉ cộng rung) | 100% / 92% | 100% / 100% |
| Bàn tay cứng | 0% / 0% | 0% / 6% |
| Giữ 50% sự đổi dáng tay | 18% / 15% | 52% / 61% |
| Giữ 75% sự đổi dáng tay | 75% / 62% | 76% / 90% |
| Đi ra rồi quay về | 45% / 37% | **97% / 94%** |
| Quãng dời cổ tay ×0,25 | 4% / 0% | **99% / 90%** |
| Cổ tay đứng yên, chỉ đổi dáng tay | 0% / 0% | **98% / 87%** |

**LSTM nhận ra cú vuốt từ động tác của các ngón** (chụm rồi mở, ngón chỉ về một bên), không từ
quãng đường hay tốc độ của cổ tay:

- **Chịu được kiểu "hất rồi kéo về ngay".** Đây là lý do chính khiến rừng bỏ qua những cú
  vuốt nhanh của người dùng trong log trực tiếp ở Phase 6 (mục 7.3).
- **Vẫn đòi bàn tay đổi dáng.** Bàn tay cứng gần như không bao giờ được nhận. Chế độ luyện
  tập có `open_range` (Phase 6, mục 8.1) vẫn cần thiết.
- **Cái giá có thể có:** mở và chụm tay mà không dời cổ tay cũng được nhận là vuốt. Trên
  val, điều này chưa thành báo nhầm lớn (mục 4), nhưng phải xem lại ở lần thử trực tiếp.

## 6. Chạy thử demo

```
python scripts/demo.py --model lstm --source data/ipn/videos/videos/1CM42_12_R__157.avi --no-display --max-sec 45
```

Video thuộc tập val. Đây chỉ là phép thử nhanh, không thay được lần thử trực tiếp.

- 224 lần dự đoán, 5 cụm nhãn khác `none`. Rừng cho 7 cụm trên cùng đoạn này (Phase 6, mục 6).
- **Đúng:** `swipe_right` ở giây 21,0–21,8 trùng cú G06 *Throw right* (khoảng giây
  20,3–22,0).
- **Không báo, đúng như mong đợi:** G09 và G03 *Throw up*.
- **Báo nhầm:** 4 cụm, đều lúc người diễn chỉ trỏ hai ngón (`B0B`).

**Tốc độ** (đo nhanh khi CPU rảnh, không phải kết quả báo cáo):

- LSTM dự đoán một cửa sổ mất khoảng 1 ms, dù chạy 1 hay 4 luồng.
- Demo nạp `torch` mất khoảng 3 giây, nhưng việc này xảy ra lúc khởi động, trước khi camera
  chạy. Chọn `--model rules` hay `rf` thì không nạp `torch`.

## 7. Sửa đổi ngoài Phase 7

- **`augment.time_warp` làm mất bước đầu cửa sổ** khi bước thứ hai mất tay (0 × NaN = NaN).
  `normalize_window` khi đó từ chối cả cửa sổ. Đã sửa: trúng đúng một bước cũ thì lấy thẳng
  bước đó. Chưa kết quả nào trước đây dùng `augment()`, nên không con số nào bị ảnh hưởng.
- **`preprocess.fill_short_gaps` nhanh hơn khoảng 3 lần, cùng kết quả đến từng bit.** Nó tìm
  đoạn NaN một lần cho mỗi kiểu mất thay vì cho từng cột trong 42 cột. Trước đó hàm này chiếm
  75% thời gian tăng cường; sau khi sửa, tăng cường nhanh gần gấp đôi (đo nhanh bằng
  profiler lúc làm, không phải kết quả báo cáo). `TimeBuffer` của demo cũng gọi hàm này mỗi
  0,2 giây. Kiểm thử so nó với thuật toán cũ trên dữ liệu ngẫu nhiên.
- **`models.save_checkpoint`** đổi mọi giá trị về kiểu Python thuần, rồi nạp lại ngay sau khi
  lưu. Trước đó `torch.__version__` (một lớp con của `str`) làm checkpoint không nạp được ở
  chế độ an toàn.

## 8. Định nghĩa hoàn thành

| Mục | Trạng thái |
|---|---|
| Checkpoint tốt nhất lưu kèm epoch và macro-F1 val | **đạt**: `lstm_model.pt`, epoch 124, 0,6014 |
| Đường loss cho thấy rõ điểm bắt đầu quá khớp | **rõ ở bản không tăng cường** (`run_04`): loss val thấp nhất ở epoch 38 rồi tăng. Ở bản chính chỉ thấy khoảng hở nới rộng từ khoảng epoch 20; loss val không quay đầu trong 144 epoch (mục 3). Người dùng xét xem như vậy đã đủ chưa |
| Bảng một hàng mỗi mô hình trên cùng tập val | **đạt**: mục 2; `results/model_comparison.md` |
| `test_overfit_10_mau` xanh | **đạt** |
| `demo.py --model lstm` chạy trên webcam | **đạt** (người dùng, 2026-10-10): vuốt tốt hơn hẳn rừng, nhưng zoom kém đi — nguyên nhân và cách sửa ở mục 9 |
| `results/TEST_USED.log` vẫn trống | **đạt**: file chưa tồn tại |

## 9. Zoom kém đi khi chạy LSTM trực tiếp (2026-10-10)

**Triệu chứng.** Người dùng chạy `demo.py --model lstm --show-features --log
results/phase7/live_lstm.csv`. Vuốt cải thiện rõ so với rừng, nhưng zoom tệ đi.

### 9.1. Log trực tiếp và kiểm tra đường ống

- **Lúc người dùng zoom:** `pinch_delta` là +1,6…+1,9 (mở ngón) và −1,6…−2,1 (chụm ngón),
  cổ tay gần như đứng yên. Tức là còn mạnh hơn hộp 25–75 của IPN (`zoom_in` +0,70…+1,80).
  LSTM vẫn trả `none`, độ tin 0,89–1,00. Ví dụ ở giây 8,2–8,6 và 10,4–11,0.
- **Giây 14,0–15,8, bàn tay đứng yên:** `pinch_delta` −0,13…+0,18, `max_vx` 0,10–0,34,
  `open_range` 0,02–0,14. LSTM báo `zoom_out` liên tục, độ tin 0,70–0,89.
- **Đường ống không lỗi.** Theo SPEC, khi demo tệ hơn offline thì phải loại trừ lỗi đường ống
  trước. Lệnh `demo.py --model lstm --source data/ipn/videos/videos/1CM42_12_R__157.avi
  --no-display --max-sec 135`, dùng mô hình lúc đó là `run_02`, nhận cả hai cú zoom của IPN
  (khoảng giây 118–121 và 127–130) với độ tin 0,88–1,00. `pinch_delta` của chúng là
  ±1,2…2,3, cùng tầm với của người dùng.

**Kết luận:** cùng một độ mở–chụm cái–trỏ, nhưng LSTM nhận zoom của IPN mà không nhận zoom
của người dùng. Thứ khác nhau nằm ở phần còn lại của bàn tay.

### 9.2. LSTM và rừng dựa vào gì để nhận zoom

`scripts/probe_zooms.py`, bảng `probe_zooms/run_03`, mô hình hiện tại. Thử trên các cửa sổ
zoom thật của val mà mỗi mô hình đang nhận đúng. Cổ tay, ngón cái, ngón trỏ giữ nguyên, chỉ
đổi các ngón còn lại. "Duỗi thẳng" dùng độ dài ngón đo trên những bàn tay mở hẳn của IPN.
Số ghi dạng `zoom_in` / `zoom_out`. Lần chạy `run_01`, với LSTM `run_02`, cho cùng bức tranh.

| Sửa đổi | Rừng | LSTM |
|---|---|---|
| Không sửa (chỉ cộng rung) | 93% / 98% | 100% / 100% |
| Nhẫn, út duỗi thẳng | 63% / 85% | **10% / 35%** |
| Giữa, nhẫn, út duỗi thẳng — zoom hai ngón | 52% / 54% | **7% / 38%** |
| Giữa, nhẫn, út đứng yên | 76% / 98% | 50% / 80% |
| Bàn tay đứng yên ở dáng cái–trỏ đang mở | 0% báo zoom | **46–62% vẫn báo zoom** |

Dòng cuối: dáng cuối của cửa sổ `zoom_in` cho 46% `zoom_in`. Dáng đầu của cửa sổ `zoom_out`
cho 5% `zoom_out` và 57% `zoom_in`.

**Hai nguyên nhân:**

1. **LSTM học kiểu zoom riêng của IPN, không học bản chất zoom.** Người diễn IPN zoom bằng ba
   ngón, nhẫn và út gập (`docs/gestures.md`). Nhẫn và út duỗi ra là LSTM gần như không còn
   nhận zoom. Zoom tự nhiên thì thường để các ngón kia thả lỏng hoặc duỗi.
2. **LSTM đoán zoom từ dáng tay tĩnh.** Đây chính là chuỗi `zoom_out` ở giây 14,0–15,8 của
   log.

Rừng ít bị ảnh hưởng hơn hẳn, vì nó nhìn chủ yếu khoảng cách cái–trỏ (`pinch_range`,
`pinch_delta` đứng đầu bảng độ quan trọng). Nó không bao giờ báo zoom khi bàn tay đứng yên.

### 9.3. Thử sửa ngay trong LSTM: không dùng được

Hai phép tăng cường mới, chỉ trên train (`src/augment.py`, `src/datasets.py`):

- **Đổi dáng ngón phụ:** cửa sổ zoom mang dáng ngón giữa–nhẫn–út, hoặc chỉ nhẫn–út, của một
  bàn tay IPN thật khác, đứng yên.
- **Bàn tay đứng yên:** thêm cửa sổ cả bàn tay đứng yên, nhãn `none`.

Lần chạy tái lập được là `train_lstm/run_08`:
`python scripts/train_lstm.py --zoom-style-p 0.5 --static-share 0.1`. `run_05` và `run_06`
là các lần thử trước bằng code chưa sửa xong (mục 9.4), cho cùng kết luận.

- **Lợi** (`probe_zooms/run_04`): zoom được nhận ở mọi kiểu ngón phụ (88–98%), và bàn tay
  đứng yên không còn bị báo zoom (0%). Phép thăm dò dùng ngón duỗi thẳng tổng hợp, còn tăng
  cường dùng dáng tay thật, nên đây là phép kiểm tra tương đối độc lập.
- **Giá** (`run_08` so với `run_07`, trên val):

| | `run_07` | `run_08` |
|---|---|---|
| Precision `zoom_out` | 0,46 | 0,10 |
| F1 `zoom_out` | 0,53 | 0,18 |
| Báo nhầm với tay chỉ trỏ `B0A` / `B0B` | 3,5% / 5,9% | 12,0% / 10,2% |

**Lý do:** kiểu ngón riêng của IPN chính là thứ giúp LSTM phân biệt zoom với tay chỉ trỏ.
Dạy nó "ngón phụ làm gì cũng được, miễn cái–trỏ chụm lại là `zoom_out`" thì tay chỉ trỏ có
ngón cái nhích lại gần ngón trỏ cũng thành `zoom_out`. Hai phép này được giữ trong code nhưng
**tắt** (`AUG_ZOOM_STYLE_P = AUG_STATIC_SHARE = 0`). Phép "bàn tay đứng yên" riêng lẻ chưa
được tách ra đo; để cho bảng khảo sát của Phase 8.

### 9.4. Đổi cách dừng sớm: theo trung bình trượt

- **Lý do:** macro-F1 val lệch khoảng ±0,04 giữa hai epoch liền nhau. Dừng theo điểm thô thì
  một đỉnh nhiễu đến sớm cắt ngang việc học. `run_05` dừng ở epoch 48 vì một đỉnh ở epoch 28;
  `run_03` dừng ở epoch 40 vì một đỉnh ở epoch 20. Checkpoint cũng rơi đúng vào đỉnh nhiễu:
  0,6014 của `run_02`.
- **Giờ:** dừng sớm và chọn checkpoint theo trung bình trượt 10 epoch (`EarlyStop`; SPEC
  Phase 7, sửa 2026-10-10).
- **Kết quả với mô hình chính (`run_07`):**
  - cùng seed, cùng tăng cường, nên trùng `run_02` từng chữ số suốt 106 epoch;
  - checkpoint ở epoch 86: trung bình trượt 0,5336, chính epoch đó 0,5560;
  - đây là con số đưa vào bảng so sánh, thay cho 0,6014.
- **Cái giá nhỏ:** đường làm mượt của `run_02` còn nhích lên khoảng 0,546 quanh epoch 131,
  nhưng dừng sau 20 epoch không tăng thì không tới được đó. Chênh lệch khoảng 0,01, nằm trong
  mức dao động.
- **Một lỗi phát hiện trên đường đi:** đường dự phòng khi tăng cường bị từ chối từng chuẩn hoá
  lại cửa sổ gốc, làm lệch chữ số cuối và không tái tạo được `run_02`. Đã sửa. Nhờ vậy
  `--stop-smooth 1` cho đúng `run_02`.

### 9.5. Cách sửa được chọn: mô hình ghép `--model hybrid`

Mỗi mô hình được tin ở đúng họ cử chỉ mà các phép thăm dò cho thấy nó vững (`src/hybrid.py`):

- LSTM đoán vuốt → lấy vuốt (mục 5: chịu được hất rồi kéo về, cổ tay đi ngắn);
- rừng đoán zoom → lấy zoom (mục 9.2);
- còn lại → `none`.

Cả hai thành phần đều đã được người dùng thấy tốt trên webcam: vuốt của LSTM (lần thử này),
zoom của rừng (Phase 6).

Trên tập val (`evaluate.py --model {lstm,hybrid}`, bảng `evaluate/run_05`, `run_06`):

| Mô hình | macro-F1 | Mức sự kiện vuốt trái / phải | Zoom in / out | Báo nhầm `none` | Cụm báo nhầm/phút |
|---|---|---|---|---|---|
| Rừng | 0,4361 | 70% / 70% | 59% / 56% | 8,2% | 14,8 |
| LSTM (`run_07`) | 0,5560 | 93% / 85% | 89% / 80% | 5,8% | 8,6 |
| **Ghép** | **0,5061** | 93% / 85% | 59% / 56% | 6,0% | 8,9 |

- **Trên IPN, ghép kém LSTM.** Zoom của LSTM giỏi hơn **khi người làm đúng kiểu IPN**. Với
  kiểu zoom của người dùng thì lần thử trực tiếp cho thấy điều ngược lại.
- **Nếu người dùng zoom đúng kiểu IPN** (ba ngón, nhẫn và út gập), `--model lstm` cũng sẽ
  nhận được.
- **Chạy thử trên video IPN** (`demo.py --model hybrid --source …1CM42_12_R__157.avi
  --no-display --max-sec 132`):
  - nhận được cả hai cú zoom (phần của rừng) và cú vuốt trái G05 (phần của LSTM);
  - các cụm báo vuốt nhầm lúc người diễn chỉ tay vẫn còn, đó là của LSTM;
  - chạy lại phiên đó qua bốn mô hình, số cụm nhãn khác `none` trong 2,2 phút: luật 81, rừng
    29, LSTM 22, ghép 26 (`replay/run_01`).

### 9.6. Ghi điểm mốc để chạy lại phiên trực tiếp

Log của lần thử này chỉ có 4 đặc trưng, nên không kiểm được nguyên nhân trên chính bàn tay
người dùng.

- **Ghi:** `demo.py --log FILE` giờ ghi kèm điểm mốc thô vào `FILE_landmarks.npz`, theo
  schema của `data/landmarks`, nguồn `webcam`.
- **Chạy lại:** `scripts/replay_log.py` đẩy lại từng frame qua đúng `LivePredictor` của demo,
  với mọi mô hình hoặc một checkpoint khác (`--extra-lstm`).
- **Kiểm chứng:** chạy lại trùng 150/150 lần dự đoán của LSTM và 659/659 của mô hình ghép so
  với lúc demo chạy.

### 9.7. Việc tiếp theo

1. **Người dùng thử `--model hybrid` trên webcam**, có ghi log:

   ```
   python scripts/demo.py --model hybrid --show-features --log results/phase7/live_hybrid.csv
   ```

   Mỗi cử chỉ 10 lần, cộng 5 phút làm việc bình thường.
2. **Chạy lại phiên đó qua cả bốn mô hình** bằng `replay_log.py`, trên chính bàn tay người
   dùng. Nếu zoom vẫn kém, điểm mốc sẽ cho thấy cụ thể khác IPN ở đâu.
3. **Bảng khảo sát Phase 8:** đổi dáng ngón phụ và bàn tay đứng yên, đo riêng từng phép.
