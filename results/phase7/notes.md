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
| `demo.py --model lstm` chạy trên webcam | **chờ người dùng**; đã chạy trên video IPN (mục 6) |
| `results/TEST_USED.log` vẫn trống | **đạt**: file chưa tồn tại |
