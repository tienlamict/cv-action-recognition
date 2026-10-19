# Tổng kết đến Phase 7

**Đề tài:** Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính

**Cập nhật:** 2026-10-19

**Đọc kèm**, theo thứ tự:

1. `CLAUDE.md` (quy ước)
2. `docs/SPEC.md` (13 phase, sửa tới 2026-10-10)
3. `docs/gestures.md` (bộ cử chỉ)
4. `results/phase6/notes.md` (phân tích rừng ngẫu nhiên)
5. `results/phase7/notes.md` (phân tích LSTM)
6. file này

**Bản tổng kết trước:** `docs/tong-ket-den-phase-5.md`. Bản đó ghi chi tiết Phase 0–5: kết quả, cách làm, các quyết định. File này chỉ tóm lược lại phần đó, rồi đi sâu vào Phase 6 và 7.

---

## 1. Tóm tắt

Hệ thống chạy đầu-cuối trên webcam với **bốn mô hình** chọn bằng `demo.py --model`:

| Mô hình | Cách chạy | macro-F1 trên val |
|---|---|---|
| Luật ngưỡng (Phase 5) | `rules` | 0,2305 |
| Rừng ngẫu nhiên trên 15 đặc trưng (Phase 6) | `rf` | 0,4361 |
| LSTM trên chuỗi toạ độ 42 chiều (Phase 7) | `lstm` | **0,5560** |
| Mô hình ghép: vuốt theo LSTM, zoom theo rừng (Phase 7) | `hybrid` | 0,5061 |

Hai đường cơ sở trên cùng tập val: luôn đoán `none` 0,1964; đoán ngẫu nhiên 0,0796.

**Ba lần thử trực tiếp của người dùng đã định hướng phần lớn công việc:**

1. **Rừng ngẫu nhiên:** zoom tốt, vuốt kém.
   - Nguyên nhân: mô hình học cú vuốt theo kiểu "hất" của IPN (bàn tay mở ra trong lúc
     hất), và không chịu kiểu hất rồi kéo tay về ngay.
   - Xử lý: chế độ luyện tập hiện thêm độ xòe `open_range`.
   - Ở phiên sau, có 43 cửa sổ chuyển động kiểu vuốt. Trong 88% số đó, người dùng đã mở bàn
     tay đúng kiểu IPN, và rừng nhận 79% trong 43 cửa sổ đó là vuốt.
2. **LSTM:** vuốt tốt hơn hẳn, nhưng zoom kém đi.
   - Nguyên nhân: LSTM học kiểu zoom riêng của người diễn IPN (ngón nhẫn và út gập), và còn
     đoán zoom từ một dáng tay đứng yên.
   - Xử lý: mô hình ghép `hybrid`.
3. **Mô hình ghép**, chạy lại trên chính phiên của người dùng: số cụm zoom được nhận tăng từ
   24 (LSTM đứng một mình) lên **45**.

**Demo nên dùng `--model hybrid`.**

**Còn mở:**

- Chưa có phép thử trực tiếp có cấu trúc (mỗi cử chỉ 10 lần, cộng 5 phút làm việc bình
  thường), nên chưa có số liệu để quyết định có cần dữ liệu tự quay (Phase 11) hay không.
- Báo nhầm vẫn cao. Máy trạng thái của Phase 9 là bước xử lý chính.

`pytest -q`: **152 passed**. Tập test chưa bị chạm tới: `results/TEST_USED.log` chưa tồn tại.

---

## 2. Trạng thái các phase

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 0 | Khung dự án, `config.py`, `require_measured` | ✅ xong |
| 1A | Đọc video, bám tay, xem điểm mốc trực tiếp | ✅ code xong; chưa có biên bản xác nhận bằng mắt |
| 1B | Thí nghiệm quan sát MediaPipe | ⬜ code xong, **chưa chạy**; không chặn phase nào |
| 2 | Tiền xử lý, chuẩn hoá, 15 đặc trưng | ✅ xong. Lần này vá lỗ hổng nhanh hơn khoảng 3 lần, cùng kết quả đến từng bit |
| 3 | Trích điểm mốc IPN, đo quy ước hướng | ✅ xong; `docs/gestures.md` vẫn là **bản nháp chờ người dùng review** |
| 4 | Cửa sổ, tăng cường, chia tập theo người | ✅ xong. Lần này sửa một lỗi của co giãn thời gian (mục 4.7) |
| 5 | Mô hình luật và demo v0 | 🟡 code và đo offline xong; demo đã chạy trên webcam; **phép thử hướng và đếm báo nhầm chưa làm** |
| 6 | Rừng ngẫu nhiên, demo học máy, quyết định Phase 11 | 🟡 huấn luyện, đánh giá, phân tích xong; cổng đạt 2/3, điều kiện thứ 3 đã giải thích; **`live_check.md` (quyết định Phase 11) chưa có** |
| 7 | LSTM trên chuỗi 42 chiều | 🟡 5/6 mục hoàn thành đạt; mục "đường loss cho thấy rõ điểm bắt đầu quá khớp" **chờ người dùng xét** (mục 3.4) |
| 8–12 | Đánh giá hai mức, máy trạng thái, demo hoàn chỉnh, dữ liệu tự quay, tái lập | ⬜ chưa bắt đầu |

---

## 3. Kết quả chính

### 3.1. Phase 0–5 — tóm lược

Chi tiết và số liệu đầy đủ: `docs/tong-ket-den-phase-5.md`, mục 3.

- **Dữ liệu IPN.**
  - Bộ giải mã bỏ âm thầm các frame "not coded" của XVID: 101/200 video có hiện tượng này,
    tổng 677 frame. Đã sửa: mốc thời gian lấy theo vị trí frame trong file.
  - Nhãn IPN đếm frame không thống nhất, nên cách đếm được chọn riêng cho từng video. 11 video
    không khớp cách nào bị loại.
- **Điểm mốc:** 200/200 video đã trích.
- **Quy ước hướng:** `SWIPE_LEFT_SIGN = 1`, đo trên 189 clip.
- **Bộ cửa sổ** `windows.npz`:
  - cửa sổ 1,2 s, trượt 0,2 s;
  - nhãn neo vào khoảnh khắc chính của cử chỉ;
  - chia theo người: train 30, val 7, test 13;
  - train có 3 326 cửa sổ, `none` chiếm 50%; val có 11 038 cửa sổ, test 23 140, cả hai giữ
    phân bố tự nhiên.
- **Nhiễu tăng cường:** `AUG_NOISE_SIGMA = 0,0159`.
- **Cổng boxplot Phase 4:** đạt trên `pinch_delta`, `dx`, `max_vx`.
- **Mô hình luật:** ba ngưỡng hiệu chuẩn trên train; macro-F1 val 0,2305; 44% cửa sổ `none`
  bị báo nhầm.

### 3.2. Rừng ngẫu nhiên (Phase 6)

Mô hình theo SPEC: 300 cây, trọng số lớp cân theo từng mẫu bootstrap, không chuẩn hoá đặc
trưng. Huấn luyện trên 3 326 cửa sổ train mất 1,6 giây. Bản hiện hành là
`results/phase6/train_rf/run_07`.

**Trên val** (11 038 cửa sổ, `none` chiếm 96,5%):

| Mô hình | macro-F1 | F1 none | swipe_left | swipe_right | zoom_in | zoom_out |
|---|---|---|---|---|---|---|
| Luật | 0,2305 | 0,714 | 0,056 | 0,043 | 0,164 | 0,176 |
| **Rừng ngẫu nhiên** | **0,4361** | 0,951 | 0,212 | 0,232 | 0,368 | 0,417 |

- **Recall** các lớp cử chỉ 0,49–0,63. **Precision** chỉ 0,13–0,35: 877 cửa sổ `none` (8,2%)
  bị báo thành cử chỉ, trong khi cả tập val chỉ có 388 cửa sổ cử chỉ thật.
- **Mức sự kiện xấp xỉ:** cử chỉ có ít nhất một cửa sổ được nhận đúng chiếm 70% / 70% (vuốt
  trái / phải) và 59% / 56% (zoom in / out).
- **Độ quan trọng đặc trưng:**
  - Ba đặc trưng đầu bảng theo hoán vị là `pinch_range`, `pinch_delta`, `max_vx`. Dự đoán
    trước đó là `pinch_delta`, `dx`, `max_vx`.
  - `dx` bị độ quan trọng hoán vị giấu đi vì gần trùng thông tin với `mean_vx` (tương quan
    Spearman 0,966). Xáo cả cặp thì macro-F1 giảm 0,042, ngang `max_vx`, và số cửa sổ vuốt bị
    đoán ngược hướng tăng từ 8 lên 42,8.
- **Cổng Phase 6:** đạt 2/3.
  - Rừng cao hơn hẳn luật: đạt.
  - Không vượt 0,97 (dấu hiệu rò rỉ): đạt.
  - Ba đặc trưng đầu bảng: chưa đạt theo đúng chữ, đã có lời giải thích như trên.
- **Nguồn báo nhầm chính:** tay chỉ trỏ (`B0A`, `B0B`) và tay không làm cử chỉ (`D0X`).
  `G07` (xòe tay hai lần) bị báo nhầm 19% số cửa sổ, chủ yếu thành zoom.
- **Đánh giá trên test** chỉ chạy được khi gắn cờ "lần cuối", và mỗi lần chạy như vậy để lại
  một dòng nhật ký. Đến nay chưa lần nào.

### 3.3. Vuốt kém khi thử trực tiếp với rừng — nguyên nhân và xử lý (2026-10-09)

**Triệu chứng.** Trong log trực tiếp đầu tiên (`results/phase6/live_rf_work.csv`), zoom được
nhận đều. Những cú vuốt nhanh (tốc độ đỉnh 3,2–9,3 lòng bàn tay/giây) mà dời ròng chỉ 0,0–0,6
lòng bàn tay thì bị đoán `none`.

**Thăm dò** (`probe_swipes.py`, trên cú vuốt thật của val mà rừng đang nhận đúng; số ghi dạng
trái / phải):

| Sửa đổi | Còn được nhận |
|---|---|
| Bàn tay cứng — quỹ đạo, tốc độ cổ tay giữ nguyên | **0% / 0%** |
| Giữ 50% sự đổi dáng tay | 18% / 15% |
| Đi ra rồi quay về trong cùng cửa sổ | 45% / 37% |
| Quãng dời cổ tay ×0,5 | 48% / 47% |
| Cổ tay đứng yên, chỉ đổi dáng tay | 0% / 0% |

Rừng hiểu "vuốt" là cú hất `Throw` của IPN: cổ tay dời ngang đủ nhanh và đủ xa, **và** bàn
tay đổi dáng từ chụm sang mở. Trên vuốt của IPN thì nó không kém zoom; đây là lệch miền giữa
cách người dùng vuốt và cách người diễn IPN vuốt.

**Xử lý:**

1. **Chế độ luyện tập** (`demo.py --show-features`) hiện thêm `open_range` cạnh ba đặc trưng
   của cổng, tô xanh khi nằm trong hộp 25–75% của IPN. Log trực tiếp cũng ghi thêm cột này.
2. **Tăng cường "bàn tay cứng"** cho cú vuốt khi huấn luyện rừng: đã làm, đã đo, **đang tắt**.
   - Bản cứng hoàn toàn chỉ giúp bàn tay cứng tổng hợp, thứ không có ở tay thật: tay chỉ trỏ
     thật di chuyển như vuốt vẫn có độ xòe biến thiên 0,2–0,8, còn bản tổng hợp chỉ 0,06.
   - Bản thực tế (giữ ngẫu nhiên 0–100% sự đổi dáng) giúp được cú vuốt giữ 50% sự đổi dáng:
     10% → 38–56%. Đổi lại, báo nhầm `none` tăng 1,5–2,6 lần (8,2% → 12,5–21,6%).
   - Mức bật là quyết định của người dùng.

**Sau khi luyện** (phiên `results/phase6/live_rf_swipes.csv`, 1,0 phút; đây là phép đo nhanh
trên log):

- 43 cửa sổ có chuyển động kiểu vuốt;
- 88% trong số đó có `open_range` trong hộp IPN (trung vị 1,2);
- rừng nhận 79% là vuốt.

### 3.4. LSTM (Phase 7)

**Cấu hình:**

- **Đầu vào:** cửa sổ đã chuẩn hoá `(18, 21, 2)` trải thành `(18, 42)`.
- **Mô hình:** LSTM một chiều 2 lớp × 128, dropout 0,3, lấy đầu ra ở bước cuối.
- **Học:** Adam lr 0,001, lô 64. CrossEntropy có trọng số lớp: `none` 0,40, các lớp cử chỉ
  1,59–1,63.
- **Tăng cường:** sáu phép của Phase 4, tạo mới ở mỗi epoch.
- **Dừng sớm:** khi trung bình trượt 10 epoch của macro-F1 val không tăng sau 20 epoch.
- **Chạy:** CPU 4 luồng. Mô hình hiện hành là `train_lstm/run_07`: 106 epoch, khoảng 13 phút,
  checkpoint ở epoch 86.

**Trên val:**

| Mô hình | macro-F1 | F1 none | swipe_left | swipe_right | zoom_in | zoom_out |
|---|---|---|---|---|---|---|
| Rừng ngẫu nhiên | 0,4361 | 0,951 | 0,212 | 0,232 | 0,368 | 0,417 |
| **LSTM** | **0,5560** | 0,968 | 0,397 | 0,376 | 0,506 | 0,533 |

| | Rừng | LSTM |
|---|---|---|
| Mức sự kiện, vuốt trái / phải | 70% / 70% | **93% / 85%** |
| Mức sự kiện, zoom in / out | 59% / 56% | **89% / 80%** |
| Cửa sổ `none` bị báo nhầm | 8,2% | 5,8% |
| Cụm báo nhầm mỗi phút `none` | 14,8 | 8,6 |
| Báo nhầm với tay chỉ trỏ `B0A` / `B0B` | 5,8% / 9,7% | 3,5% / 5,9% |
| Báo nhầm với `D0X` | 10,6% | 14,5% |

**Về độ tin cậy của con số:**

- macro-F1 val dao động khoảng ±0,04 giữa hai epoch liền nhau, vì mỗi lớp cử chỉ của val chỉ
  có 94–104 cửa sổ.
- Lần huấn luyện đầu (`run_02`) chọn epoch có điểm thô cao nhất và báo 0,6014. Đó là một
  đỉnh nhiễu.
- Cách chọn hiện tại (trung bình trượt) cho checkpoint có điểm 0,5560, và trung bình trượt
  0,5336.
- Con số không thiên lệch sẽ đến từ năm seed ở Phase 8 và từ lần chạy duy nhất trên test.

**Đường học:**

- **Mô hình chính:** loss val giảm nhanh tới khoảng epoch 20, rồi chững lại ở 0,43–0,50.
  Loss train tiếp tục giảm từ 0,25 xuống 0,012. Khoảng hở nới rộng từ khoảng epoch 20, nhưng
  loss val **không quay đầu đi lên** trong 144 epoch: tăng cường mới mỗi epoch và dropout giữ
  nó lại.
- **Bản không tăng cường, chạy đủ 150 epoch** (`run_04`): điểm bắt đầu quá khớp hiện rõ. Loss
  val (làm mượt) thấp nhất ở epoch 38 (0,490), rồi tăng lên 0,56–0,67.
- Ở mức thường đạt, tăng cường hơn không tăng cường 0,532 ± 0,036 so với 0,512 ± 0,020.
  Chênh lệch nhỏ hơn độ lệch chuẩn, nên **chưa đủ bằng chứng để kết luận**.

**LSTM nhận vuốt khác rừng** (`probe_swipes.py --model lstm`; trái / phải):

| Sửa đổi | Rừng | LSTM |
|---|---|---|
| Bàn tay cứng | 0% / 0% | 8% / 0% |
| Đi ra rồi quay về | 45% / 37% | **96% / 99%** |
| Quãng dời cổ tay ×0,25 | 4% / 0% | **100% / 94%** |
| Cổ tay đứng yên, chỉ đổi dáng tay | 0% / 0% | **100% / 87%** |

LSTM nhận cú vuốt từ **động tác của các ngón** (chụm rồi mở, ngón chỉ về một bên), không từ
quãng đường cổ tay đi. Nó chịu được kiểu hất rồi kéo về mà rừng bỏ qua, nhưng vẫn đòi bàn tay
đổi dáng.

**Tốc độ:** dự đoán một cửa sổ mất khoảng 1 ms. Demo chỉ nạp `torch` (khoảng 3 giây) khi chọn
`lstm` hay `hybrid`.

**Tái lập:**

- `run_02` cho đúng từng chữ số của `run_01`.
- `run_07` trùng `run_02` từng chữ số suốt 106 epoch; hai lần chỉ khác cách chọn checkpoint.

### 3.5. Zoom kém khi thử trực tiếp với LSTM — nguyên nhân và xử lý (2026-10-10)

**Triệu chứng** (`results/phase7/live_lstm.csv`):

- Lúc người dùng zoom, `pinch_delta` là ±1,6…2,1, còn mạnh hơn hộp 25–75 của IPN. LSTM vẫn
  trả `none`, độ tin 0,89–1,00.
- Lúc bàn tay đứng yên, LSTM báo `zoom_out` liên tục gần 2 giây.

**Đường ống không lỗi.** Cho demo LSTM chạy trên một video IPN của tập val: hai cú zoom của
IPN được nhận với độ tin 0,88–1,00, và `pinch_delta` cùng tầm với của người dùng.

**Thăm dò zoom** (`probe_zooms.py`). Trên cú zoom thật của IPN, giữ nguyên cổ tay, ngón cái,
ngón trỏ, chỉ đổi các ngón còn lại; số ghi dạng zoom in / out:

| Sửa đổi | Rừng | LSTM |
|---|---|---|
| Không sửa | 93% / 98% | 100% / 100% |
| Nhẫn và út duỗi thẳng | 63% / 85% | **10% / 35%** |
| Giữa, nhẫn và út duỗi thẳng (zoom hai ngón) | 52% / 54% | **7% / 38%** |
| Bàn tay đứng yên ở dáng cái–trỏ đang mở | 0% báo zoom | **46–62% vẫn báo zoom** |

Hai nguyên nhân:

1. **LSTM học kiểu zoom riêng của người diễn IPN** (ba ngón, nhẫn và út gập), không học bản
   chất của zoom là cái–trỏ rời xa hay lại gần nhau.
2. **LSTM đoán zoom từ một dáng tay tĩnh.**

Rừng nhìn chủ yếu khoảng cách cái–trỏ, nên ít bị ảnh hưởng.

**Thử sửa ngay trong LSTM: không dùng được** (`run_08`).

- Hai phép tăng cường mới:
  - cú zoom mang dáng ngón phụ của một bàn tay IPN thật khác, đứng yên;
  - thêm cửa sổ bàn tay đứng yên, nhãn `none`.
- Lợi: zoom được nhận ở mọi kiểu ngón (88–98%), hết báo zoom khi tay đứng yên.
- Giá: precision `zoom_out` rơi từ 0,46 xuống 0,10, và báo nhầm với tay chỉ trỏ tăng từ
  3,5% / 5,9% lên 12,0% / 10,2%.
- Lý do: kiểu ngón riêng của IPN chính là thứ giúp LSTM phân biệt zoom với tay chỉ trỏ.
- Hai phép này vẫn trong code nhưng **tắt**.

**Cách sửa được chọn: mô hình ghép `hybrid`.** Mỗi mô hình được tin ở đúng họ cử chỉ mà các
phép thăm dò cho thấy nó vững:

- LSTM đoán vuốt → lấy vuốt;
- rừng đoán zoom → lấy zoom;
- còn lại → `none`.

Cả hai phần đều đã được người dùng thấy tốt trên webcam.

| Trên val | Rừng | LSTM | **Ghép** |
|---|---|---|---|
| macro-F1 | 0,4361 | 0,5560 | 0,5061 |
| Mức sự kiện vuốt trái / phải | 70% / 70% | 93% / 85% | 93% / 85% |
| Mức sự kiện zoom in / out | 59% / 56% | 89% / 80% | 59% / 56% |
| Cửa sổ `none` bị báo nhầm | 8,2% | 5,8% | 6,0% |
| Cụm báo nhầm mỗi phút | 14,8 | 8,6 | 8,9 |

Trên IPN, mô hình ghép kém LSTM, vì zoom của LSTM giỏi hơn **khi người làm đúng kiểu IPN**.
Với kiểu zoom của người dùng thì ngược lại.

**Trên chính bàn tay người dùng.** Chạy lại phiên `live_hybrid.csv` (1,1 phút) qua cả bốn
mô hình (`replay/run_02`):

| Số cụm nhãn khác `none` | Luật | Rừng | LSTM | Ghép |
|---|---|---|---|---|
| Vuốt trái / phải | 5 / 4 | 5 / 2 | 7 / 11 | 7 / 11 |
| Zoom in / out | 23 / 25 | 21 / 24 | **10 / 14** | **21 / 24** |

Phép đo nhanh trên bảng chạy lại: chọn 205 cửa sổ có cái–trỏ đổi rõ (`|pinch_delta|` >
`RULE_P_HI`) và cổ tay chậm (`max_vx` < `RULE_VX_HI`).

- LSTM trả `none` cho 57% số cửa sổ này.
- Mô hình ghép báo zoom 66%.
- 13 cửa sổ (6%) bị phần vuốt của LSTM giành thành vuốt.

### 3.6. Bảng so sánh mô hình hiện hành

`results/model_comparison.md`, tất cả trên cùng 11 038 cửa sổ val:

| Mô hình | macro-F1 | Lần chạy |
|---|---|---|
| `rules` | 0,2305 | `results/phase6/evaluate/run_02` |
| `rf` | 0,4361 | `results/phase6/train_rf/run_07` |
| `lstm` | 0,5560 | `results/phase6/evaluate/run_06` (mô hình `train_lstm/run_07`) |
| `hybrid` | 0,5061 | `results/phase6/evaluate/run_05` |

---

## 4. Giải pháp thực hiện

Mục này mô tả **cách** đi tới các kết quả ở mục 3 và **vì sao** chọn cách đó. Nguyên tắc
chung và cách làm của Phase 0–5 xem `docs/tong-ket-den-phase-5.md` mục 4. Ở đây chỉ ghi những
gì thêm vào từ Phase 6.

### 4.1. Nguyên tắc bổ sung

- **Hỏi mô hình "nó dựa vào gì" bằng thí nghiệm phản thực tế.**
  1. Lấy những cửa sổ thật mà mô hình đang nhận đúng.
  2. Sửa **đúng một khía cạnh** của chuyển động hay dáng tay, giữ nguyên mọi thứ khác.
  3. Cộng rung điểm mốc như dữ liệu thật.
  4. Cho đi qua đúng các bước chuẩn hoá và tính đặc trưng như lúc chạy thật.

  Đo xem còn bao nhiêu phần được nhận. Cách này trả lời câu hỏi mà độ chính xác tổng không
  trả lời được: vì sao một cử chỉ của người thật không được nhận.
- **So bản tổng hợp với tay thật trước khi tin nó.** Bàn tay "cứng hoàn toàn" tổng hợp có độ
  xòe gần như không đổi; tay thật đang di chuyển thì không bao giờ như vậy. So hai phân bố
  trước khi đọc con số "lợi" của một phép tăng cường.
- **Đo cả lợi lẫn giá trên val trước khi bật một thay đổi.** Thay đổi có giá đáng kể thì
  giữ trong code nhưng tắt, ghi số đo, và để người dùng quyết.
- **Loại trừ lỗi đường ống trước khi kết luận lệch miền.** Chạy demo, qua đúng vòng lặp trực
  tiếp, trên một video IPN có cử chỉ đã biết. Nếu nó nhận đúng ở đó thì vấn đề nằm ở khác
  biệt giữa người dùng và IPN.
- **Mỗi lần sửa code, kiểm tra kết quả cũ còn tái lập được đến từng chữ số.** Tái lập bằng
  cách chạy lại phép đo cũ trong thư mục tạm và so với bảng đã lưu. Cách này đã bắt được hai
  lỗi làm hỏng khả năng tái lập (mục 4.7).
- **Không tin một epoch lẻ.** Với val nhỏ, đọc đường đã làm mượt, và báo cả mức lạc quan lẫn
  mức thường đạt.

### 4.2. Rừng ngẫu nhiên: huấn luyện, đánh giá và phân tích

- **Kiểm rò rỉ trước khi huấn luyện:** giao giữa người và clip của train và val phải rỗng.
- **Đánh giá dùng chung cho mọi mô hình:**
  - cùng hàm tính macro-F1, hai đường cơ sở, ma trận nhầm lẫn thô và chuẩn hoá theo hàng;
  - cùng một bảng so sánh mô hình, mỗi cặp (mô hình, tập) một hàng.
- **Độ quan trọng đặc trưng theo hai cách:**
  - Gini: đo lúc dựng cây, trên train.
  - Hoán vị: xáo một cột trên val, xem macro-F1 giảm bao nhiêu.

  Hai cách bất đồng ở các cặp đặc trưng gần trùng nhau. Để kiểm, xáo **cả nhóm** theo cùng
  một hoán vị, và đếm riêng số cú vuốt bị đoán ngược hướng: đó là thước đo thông tin hướng.
- **Phân tích lỗi:**
  - mỗi ô lớn ngoài đường chéo được tách theo nhãn gốc IPN;
  - lập hồ sơ trung vị đặc trưng của từng ô, để so cửa sổ bị nhầm với cửa sổ được nhận đúng;
  - tỉ lệ báo nhầm tính theo từng nhãn gốc của lớp `none`.
- **Mức sự kiện xấp xỉ.** Các cửa sổ dương liền nhau của cùng một clip được gom thành một cử
  chỉ, rồi đếm cử chỉ có ít nhất một, hai cửa sổ được nhận đúng, và cử chỉ có cửa sổ bị đoán
  ngược chiều. Mức sự kiện đầy đủ, qua máy trạng thái, là việc của Phase 8.
- **Demo nhanh và không đứng hình:**
  - Dự đoán một cửa sổ bằng cách gọi thẳng lõi của từng cây rồi lấy trung bình, cho đúng xác
    suất của thư viện. Mất 9,2 ms thay vì 62,6 ms.
  - Mô hình được nạp sẵn trước khi camera chạy. Trước đó, demo đứng hình khoảng 2,7 giây ở
    lần đầu thấy tay.
- **Chốt tập test.** Script đánh giá từ chối tập test nếu thiếu cờ "lần cuối". Khi có cờ, nó
  ghi một dòng nhật ký (thời điểm, mô hình, dòng lệnh, toàn bộ hằng số) **trước** khi đọc dữ
  liệu.

### 4.3. Điều tra cú vuốt và chế độ luyện tập (Phase 6)

- **Đọc log trực tiếp theo dòng thời gian.** Đối chiếu tốc độ đỉnh, dời ròng và nhãn của từng
  cửa sổ trong các đoạn người dùng vuốt.
- **Thiết kế phép thăm dò vuốt:**
  - bàn tay cứng: mọi bước dùng dáng tay của bước đầu, đặt tại vị trí cổ tay của chính bước
    đó;
  - giữ một phần sự đổi dáng tay theo các liều lượng;
  - nhân quãng dời cổ tay theo các hệ số;
  - đi ra rồi quay về: sau bước nhanh nhất, cổ tay đi ngược lại đúng đường cũ;
  - cổ tay đứng yên.

  Kết quả được viết thành ba điều kiện cho cú vuốt trong `docs/gestures.md`.
- **Tăng cường bàn tay cứng cho rừng:**
  - Mỗi bản giữ quỹ đạo cổ tay, giữ ngẫu nhiên một phần sự đổi dáng tay, lấy dáng của một
    bước ngẫu nhiên làm mốc, cộng rung, chuẩn hoá lại.
  - Bước làm mốc phải có lòng bàn tay dùng làm đơn vị được, theo đúng tiêu chí mà chuẩn hoá
    áp cho bước đầu. Giữa cú hất, bàn tay hay nghiêng cạnh, và dáng tay của bước đó không phải
    một bàn tay thật.
- **Quét mức tăng cường trên val:**
  - Lợi: cú vuốt thật giữ 0–75% sự đổi dáng còn được nhận bao nhiêu.
  - Giá: báo nhầm `none`, riêng với tay chỉ trỏ, và số cụm báo nhầm mỗi phút.
  - Thêm một bảng so độ đổi dáng của bản tổng hợp với tay chỉ trỏ thật. Bảng này cho biết
    cột "lợi" nào đáng tin.

### 4.4. LSTM

- **Mã hoá đầu vào.** Mỗi bước là 21 điểm (x, y) trải phẳng, đúng 42 chiều. Bước mất tay lấy
  giá trị của bước có tay gần nhất **trước** nó, vì ba lẽ:
  - chỉ dùng quá khứ;
  - không bịa quỹ đạo, vì nội suy lỗ dài bị cấm;
  - không tạo cú nhảy giả như điền 0, vì sau chuẩn hoá 0 là vị trí cổ tay ở bước đầu.

  Dữ liệu IPN và webcam đi qua đúng một hàm mã hoá này.
- **Bộ dữ liệu:**
  - Tăng cường chỉ bật được cho tập train, và tạo một bản **mới** mỗi lần lấy mẫu, tức mỗi
    epoch.
  - Phép lật đổi nhãn cặp vuốt nên nhãn trả về là nhãn sau tăng cường.
  - Bản tăng cường hiếm khi bị chuẩn hoá từ chối (0,15%); khi đó dùng cửa sổ gốc, và đếm số
    lần vào hồ sơ chạy.
- **Mô hình.** Lớp LSTM luôn một chiều, cố định bên trong, không phải tham số đặt được: LSTM
  hai chiều đọc cả tương lai, và con số báo cáo sẽ không đạt được khi chạy thật.
- **Vòng huấn luyện tách thành thư viện riêng,** để kiểm thử "học thuộc 10 mẫu trong 200
  epoch" chạy đúng vòng mà script dùng.
- **Đo loss của train và val theo cùng một cách:** chế độ đánh giá, không tăng cường, cùng hàm
  loss có trọng số. Loss chạy trong lúc học lẫn cả tác dụng của tăng cường và dropout, nên
  không đặt cạnh loss val được; nó vẫn được ghi lại.
- **Dừng sớm và chọn checkpoint theo trung bình trượt 10 epoch của macro-F1 val:**
  - Chọn theo điểm thô thì một đỉnh nhiễu đến sớm cắt ngang việc học: hai lần chạy đã dừng ở
    epoch 40 và 48 vì đỉnh ở epoch 20 và 28. Checkpoint cũng rơi vào đỉnh nhiễu.
  - Chưa đủ 10 epoch thì chưa chọn và chưa đếm thời gian chờ, vì trung bình của vài epoch đầu
    vẫn để đỉnh nhiễu thắng. Kiểm thử đã bắt được đúng lỗi này.
  - Checkpoint lưu cả điểm thô của epoch được chọn lẫn trung bình trượt.
- **Checkpoint an toàn.**
  - Mọi giá trị đi kèm được đổi về kiểu dữ liệu thuần, rồi nạp lại ngay sau khi lưu ở chế độ
    nạp an toàn. Lỗi vì thế hiện ra lúc lưu, không phải lúc chạy demo.
  - Lúc nạp, danh sách lớp, độ dài cửa sổ và tần số lấy mẫu phải khớp cấu hình hiện tại.
- **Lần chạy khảo sát.** Mọi tham số lệch khỏi cấu hình (không tăng cường, số epoch, độ kiên
  nhẫn, các phép tăng cường mới, cách dừng sớm) đều biến lần chạy thành khảo sát:
  - checkpoint nằm trong thư mục của lần chạy;
  - mô hình của demo và bảng so sánh không đổi;
  - mọi lần chạy tái lập được bằng một lệnh, không phải sửa cấu hình.
- **Thấy rõ điểm bắt đầu quá khớp.** Mô hình chính không có điểm quay đầu, nên chạy thêm bản
  không tăng cường cho hết 150 epoch. Điểm thấp nhất của loss val tìm trên đường đã làm mượt,
  không trên một epoch lẻ.
- **Chạy trên CPU, nạp lười.** Không phụ thuộc CUDA. Demo chỉ nạp thư viện học sâu khi thật sự
  dùng LSTM, để chạy với luật hay rừng không phải chờ.

### 4.5. Điều tra zoom và mô hình ghép (Phase 7)

- **Kiểm đường ống trước:** cho demo chạy, qua đúng vòng lặp trực tiếp, trên đoạn video IPN có
  hai cú zoom đã biết.
- **Phép thăm dò zoom.**
  - Mọi phép sửa làm trong **hệ toạ độ lòng bàn tay** của từng bước: gốc ở cổ tay, trục dọc
    từ cổ tay tới gốc ngón giữa. Nhờ vậy ngón được sửa vẫn theo bàn tay khi bàn tay dời hay
    xoay.
  - "Ngón duỗi thẳng": các khớp đặt trên đường từ cổ tay qua gốc ngón, cách gốc ngón đúng
    khoảng cách trung vị đo trên những bàn tay mở hẳn của IPN. Không tự đặt ra số đo bàn tay.
  - "Ngón đứng yên": giữ dáng của bước đầu so với lòng bàn tay.
  - "Bàn tay tĩnh": cả bàn tay đứng yên ở dáng của một bước.
- **Thử sửa trong LSTM.**
  - Kho dáng ngón phụ lấy từ mọi bước của các cửa sổ train: hơn 58 nghìn dáng tay thật.
  - Dáng của bàn tay bên kia được lật qua trục lòng bàn tay, để ngón không mọc sang phía bên
    kia.
  - Cửa sổ "bàn tay đứng yên" lấy dáng từ một bước bất kỳ và mang nhãn `none`.
  - Phép thăm dò dùng ngón duỗi thẳng tổng hợp, còn tăng cường dùng dáng tay thật. Vì vậy chạy
    lại phép thăm dò sau khi huấn luyện vẫn là một phép kiểm tra tương đối độc lập.
- **Mô hình ghép.** Luật ghép nằm ở đúng một chỗ, dùng chung cho đánh giá theo lô và cho demo.
  Kiểm thử bảo đảm demo (từng cửa sổ) và đánh giá (cả lô) ra cùng nhãn.
  - Độ tin là xác suất của mô hình đã quyết định nhãn.
  - Vuốt xét trước zoom, như luật của Phase 5.
- **Kiểm tra trên ba nguồn:** tập val, video IPN qua demo, và phiên trực tiếp của người dùng
  chạy lại (mục 4.6).

### 4.6. Ghi điểm mốc và chạy lại phiên trực tiếp

- **Ghi.** Khi có `--log`, demo ghi kèm điểm mốc thô của cả phiên, theo đúng định dạng của dữ
  liệu IPN, với nguồn là "webcam".
- **Chạy lại.** Một script đẩy lại từng frame qua đúng vòng dự đoán của demo, với mọi mô hình,
  hoặc với một checkpoint khác.
- **Ra:** một dòng thời gian mỗi 0,2 giây, gồm vài đặc trưng và nhãn của từng mô hình, cùng số
  cụm nhãn khác `none`.
- **Kiểm chứng:** chạy lại trùng 150/150 dự đoán của LSTM trên video IPN, và 316/316 dự đoán
  của mô hình ghép trên phiên của người dùng.
- **Tác dụng:** từ giờ mỗi lần thử trực tiếp có thể được phân tích lại offline, và mọi cách
  sửa được thử ngay trên chính bàn tay người dùng.

### 4.7. Lỗi tìm ra và cải tiến hạ tầng

| Vấn đề | Hệ quả | Cách xử lý |
|---|---|---|
| Co giãn thời gian nội suy với một bước rỗng: 0 × rỗng vẫn là rỗng | Bước đầu cửa sổ thành rỗng khi bước 2 mất tay, và cả cửa sổ bị chuẩn hoá từ chối | Trúng đúng một bước cũ thì lấy thẳng bước đó. Chưa kết quả nào trước đó dùng phép này |
| Vá lỗ hổng tìm đoạn rỗng riêng cho từng cột trong 42 cột | Chiếm 75% thời gian tăng cường, và chạy mỗi 0,2 giây trong demo | Tìm một lần cho mỗi kiểu mất. Nhanh khoảng 3 lần, kiểm thử so với thuật toán cũ đến từng bit |
| Đường dự phòng của tăng cường chuẩn hoá lại cửa sổ gốc | Lệch chữ số cuối; code không còn tái tạo được lần huấn luyện cũ | Dùng nguyên cửa sổ gốc. Kiểm lại: trùng `run_02` từng chữ số |
| Checkpoint lưu số phiên bản thư viện ở kiểu không thuần | File ghi được nhưng không nạp được ở chế độ an toàn | Đổi về kiểu thuần, và nạp lại ngay sau khi lưu |
| Demo nạp rừng ở lần dự đoán đầu | Đứng hình khoảng 2,7 giây khi lần đầu thấy tay | Nạp sẵn trước khi camera chạy |
| Hình đường học: chú thích đè lên đường cong | Khó đọc khi epoch tốt nhất sát mép phải | Chú giải đặt dưới hình, epoch tốt nhất ghi trên tiêu đề |

---

## 5. Quyết định từ 2026-10-05

Các quyết định trước đó: `docs/tong-ket-den-phase-5.md` mục 5. Mọi thay đổi dưới đây đã ghi
vào `docs/SPEC.md` kèm ngày và lý do, hoặc vào ghi chú của phase.

| Ngày | Quyết định | Lý do | Ai quyết |
|---|---|---|---|
| 2026-10-08 | Điều kiện 3 của cổng Phase 6 "chưa đạt theo chữ, đã giải thích" | `dx` bị giấu vì trùng thông tin với `mean_vx`; xáo cả cặp cho thấy nó quan trọng ngang `max_vx` | Claude giải thích; người dùng đi tiếp |
| 2026-10-09 | Chế độ luyện tập và log hiện thêm `open_range` | Với rừng, cú vuốt chỉ được nhận khi bàn tay mở ra trong lúc hất | Người dùng chọn |
| 2026-10-09 | Tăng cường "bàn tay cứng" cho rừng: có trong code, **tắt** | Giúp được cú vuốt giữ dáng nhưng báo nhầm tăng 1,5–2,6 lần | Người dùng chọn làm; Claude để tắt sau khi đo; **chờ người dùng chọn mức** |
| 2026-10-09 | LSTM: bước mất tay lấy bước có tay gần nhất trước nó | Đầu vào phải đúng 42 chiều; nội suy lỗ dài bị cấm; điền 0 tạo cú nhảy giả | Claude, ghi vào SPEC |
| 2026-10-09 | Loss train trên hình đo ở chế độ đánh giá, không tăng cường | Để khoảng hở giữa hai đường chỉ là quá khớp | Claude, ghi vào SPEC |
| 2026-10-10 | Dừng sớm và chọn checkpoint theo trung bình trượt 10 epoch | Đỉnh nhiễu làm dừng giữa chừng và làm con số lạc quan | Claude, ghi vào SPEC |
| 2026-10-10 | Tăng cường đổi dáng ngón phụ của zoom và bàn tay đứng yên cho LSTM: có trong code, **tắt** | Tay chỉ trỏ thành `zoom_out`; precision `zoom_out` 0,46 → 0,10 | Claude, sau khi đo |
| 2026-10-10 | Thêm mô hình ghép `hybrid`; khuyến nghị cho demo | Mỗi phần đã được người dùng thấy tốt trên webcam; zoom trên phiên của người dùng 24 → 45 cụm | Claude đề xuất khi người dùng yêu cầu sửa zoom; người dùng đã chạy thử, **chưa phản hồi** |
| 2026-10-10 | Demo ghi kèm điểm mốc; thêm script chạy lại phiên | Không kiểm được nguyên nhân trên tay người dùng khi log chỉ có vài đặc trưng | Claude |

---

## 6. Vấn đề còn phải xử lý

### 6.1. Việc của người dùng — đang chặn việc đóng Phase 5–7

1. **Phép thử hướng (Phase 5):** vuốt sang **trái của bạn** phải ra `swipe_left`. Nếu ngược,
   đặt `IPN_FLIP_X = -1` và chạy lại phép đo của Phase 3–5; **không sửa code**. Lật ảnh chỉ
   đổi chỗ hai nhãn vuốt, zoom không bị ảnh hưởng, nên đến giờ vẫn chưa ai kiểm việc này.
2. **Đếm báo nhầm (Phase 5):** gõ phím và dùng chuột 2 phút với `--log`, ghi
   `results/phase5/misfires.md`.
3. **Lần thử trực tiếp có cấu trúc (Phase 6), dùng `--model hybrid`, và `--model rf` để so:**
   - mỗi cử chỉ 10 lần, đếm số lần đúng;
   - 5 phút làm việc bình thường (gõ phím, dùng chuột, nói chuyện có khua tay), đếm số cụm
     báo nhầm.

   Các phiên đã ghi chưa cho biết bạn định làm cử chỉ gì lúc nào, nên chưa tính được độ chính
   xác. Nên làm theo thứ tự cố định, có nghỉ giữa các lượt. Từ số liệu đó Claude viết
   `results/phase6/live_check.md`, gồm cả quyết định có bật Phase 11 hay không.
4. **Xét mục "đường loss cho thấy rõ điểm bắt đầu quá khớp" (Phase 7)** theo mục 3.4. Quá khớp
   hiện rõ ở bản không tăng cường; ở bản chính chỉ thấy khoảng hở nới rộng.
5. **Review `docs/gestures.md`.** Đây là bản nháp do Claude viết, đã thêm hai khung số đo cho
   vuốt và zoom theo từng mô hình.
6. **Các quyết định đang chờ:**
   - mức tăng cường bàn tay cứng cho rừng;
   - chọn khoảnh khắc chính của zoom theo đúng chiều tên lớp (mục 6.2);
   - quota `none` cho tay chỉ trỏ;
   - thêm đặc trưng cấu hình ngón.

### 6.2. Chất lượng mô hình

- **Báo nhầm còn cao.**
  - Trên val: 5,8–8,2% cửa sổ `none` bị báo nhầm, tức 8,6–14,8 cụm mỗi phút thời gian `none`
    của IPN.
  - SPEC coi hơn 0,5 lần báo nhầm mỗi phút khi làm việc bình thường là dấu hiệu bật Phase 11.
    Con số của IPN chưa phải con số làm việc bình thường, nhưng khoảng cách rất xa.
  - Hướng xử lý chính: máy trạng thái của Phase 9 (ngưỡng độ tin, đồng thuận k trên n, thời
    gian nghỉ sau mỗi lệnh).
- **Nguồn báo nhầm:**
  - tay chỉ trỏ (`B0A`, `B0B`): LSTM giảm được một nửa so với rừng;
  - tay không làm cử chỉ (`D0X`): 10,6–14,7%, LSTM không cải thiện;
  - xòe tay hai lần (`G07`): 13–19%, chủ yếu thành zoom.
- **Zoom đổi chiều giữa cử chỉ.** Tuỳ mô hình, 12–28% cú zoom có cửa sổ bị đoán ngược chiều
  (LSTM 26% / 28%, rừng 22% / 12%). Giả thuyết: luật nhãn chọn khoảnh khắc chính theo độ lớn
  chứ không theo chiều, nên phần "thu tay" sau cú zoom mang nhãn của cú zoom.
- **Bộ đặc trưng không đo cấu hình ngón.** Vì vậy không tách được bàn tay mở với tay chỉ trỏ,
  và đó là lý do cả hai phép tăng cường "kiểu ngón" đều phải tắt. Cách sửa tận gốc là thêm
  đặc trưng độ duỗi từng ngón, hoặc thêm dữ liệu tự quay.
- **Val nhỏ ở các lớp cử chỉ** (94–104 cửa sổ mỗi lớp): chênh lệch dưới khoảng 0,04 macro-F1
  không kết luận được. Cần năm seed và k-fold theo người (Phase 8).
- **Trong mô hình ghép, vuốt của LSTM thắng zoom của rừng.** Trên phiên của người dùng, 6% cửa
  sổ có động tác cái–trỏ rõ bị thành vuốt.
- **Tay trái:** chưa xét. Demo nên dùng tay phải.
- **Mất 8 video test:** test còn 44 video, 12 người.

### 6.3. Tài liệu và tái lập (luật 14)

- **`README.md` lệch so với hiện trạng.**
  - Bảng "hằng số đã đo" vẫn ghi `SWIPE_LEFT_SIGN`, `AUG_NOISE_SIGMA` "(chưa đo)" và dùng tên
    ngưỡng cũ `RULE_S_HI`, `RULE_O_HI`.
  - Bảng lệnh của Phase 3–5 còn trống. Phase 6–7 đã điền.
- **Script tạm, không nằm trong repo:** bảng số đo thứ hai trong `docs/gestures.md` và các
  phép chẩn đoán lệch frame IPN.
- **Phép đo nhanh trên log, không phải kết quả báo cáo:** một số con số trong ghi chú được ghi
  rõ là đo nhanh, ví dụ tốc độ dự đoán, hay tỉ lệ trên các cửa sổ lọc từ bảng chạy lại ở mục
  3.3 và 3.5.
- **`train_lstm/run_05` và `run_06`** được chạy bằng code trước khi sửa đường dự phòng (mục
  4.7), nên không tái tạo được đến từng chữ số. `run_08` là bản tái lập được của cùng thí
  nghiệm.
- **`results/phase7/replay/run_01`** trỏ tới một file điểm mốc ở thư mục tạm. Tái tạo bằng cách
  chạy lại demo trên đúng video IPN đó (lệnh ở `results/phase7/notes.md` mục 9.5).
- **Phase 1B chưa chạy,** nên báo cáo sẽ thiếu số đo giới hạn của MediaPipe trên máy thật.

---

## 7. Kết quả trên đĩa — bản nào là hiện hành

Phase 3–5 không đổi so với `docs/tong-ket-den-phase-5.md` mục 7.

| Thư mục | Hiện hành | Còn lại |
|---|---|---|
| `results/phase6/train_rf/` | `run_07` (mô hình của demo; giống hệt `run_05`, nguồn của ghi chú Phase 6 mục 1–7) | `run_01`–`run_04`: cùng mô hình, chạy khi đang viết phần phân tích; `run_06`: rừng có tăng cường bàn tay cứng hoàn toàn |
| `results/phase6/rf_model.joblib` | = `run_07` | |
| `results/phase6/sweep_rigid/` | `run_03` | `run_01`: chỉ bản cứng hoàn toàn; `run_02`: chưa có bảng so với tay thật |
| `results/phase6/probe_swipes/` | `run_01` (rừng hiện hành) | `run_02`: rừng `run_06` |
| `results/phase6/evaluate/` | `run_02` (luật), `run_05` (ghép), `run_06` (LSTM) — các hàng của bảng so sánh | `run_01`, `run_03`: rừng, cùng số với `train_rf`; `run_04`: ghép, chưa có bảng sự kiện |
| `results/phase7/train_lstm/` | `run_07` (mô hình của demo) | `run_01`: trùng `run_02`; `run_02`: nguồn của ghi chú Phase 7 mục 1–8, checkpoint trong thư mục; `run_03`, `run_04`: không tăng cường; `run_05`, `run_06`: thử đổi dáng ngón bằng code cũ; `run_08`: thử đổi dáng ngón, tái lập được |
| `results/phase7/lstm_model.pt` | = `run_07` | |
| `results/phase7/probe_swipes/` | `run_02` (LSTM `run_07`) | `run_01`: LSTM `run_02` |
| `results/phase7/probe_zooms/` | `run_03` (rừng và LSTM `run_07`), `run_04` (LSTM `run_08`) | `run_01`: LSTM `run_02`; `run_02`: LSTM `run_05`, mô hình không còn |
| `results/phase7/replay/` | `run_02`: phiên `live_hybrid` của người dùng | `run_01`: phiên demo trên video IPN |
| Log trực tiếp của người dùng | `phase6/live_rf_work.csv`, `phase6/live_rf_swipes.csv`, `phase7/live_lstm.csv`, `phase7/live_hybrid.csv` kèm `_landmarks.npz` | |

---

## 8. Lệnh tái lập, từ bộ cửa sổ tới các mô hình

Các lệnh từ trích điểm mốc tới mô hình luật: `docs/tong-ket-den-phase-5.md` mục 8.

```
# Phase 6 — rừng ngẫu nhiên
python scripts/train_rf.py                    # → rf_model.joblib, results/phase6/train_rf/run_NN
python scripts/probe_swipes.py                # rừng coi gì là một cú vuốt
python scripts/sweep_rigid.py                 # tăng cường bàn tay cứng: lợi và giá trên val
python scripts/evaluate.py --model rf --split val
python scripts/summarize_log.py <log.csv>     # số cụm nhãn của một log demo

# Phase 7 — LSTM và mô hình ghép
python scripts/train_lstm.py                  # → lstm_model.pt (run_07); ~13–25 phút trên CPU
python scripts/train_lstm.py --stop-smooth 1  # tái tạo run_02 (khảo sát)
python scripts/train_lstm.py --no-augment                      # run_03
python scripts/train_lstm.py --no-augment --patience 150       # run_04
python scripts/train_lstm.py --zoom-style-p 0.5 --static-share 0.1   # run_08
python scripts/probe_swipes.py --model lstm
python scripts/probe_zooms.py
python scripts/probe_zooms.py --lstm-checkpoint results/phase7/train_lstm/run_08/lstm_model.pt
python scripts/evaluate.py --model lstm --split val
python scripts/evaluate.py --model hybrid --split val
python scripts/replay_log.py results/phase7/live_hybrid_landmarks.npz

# Demo — nên dùng mô hình ghép
python scripts/demo.py --model hybrid --show-features --log results/phase7/live_hybrid.csv
```

Tập test và `real_test` chỉ chạy **đúng một lần** ở cuối dự án, bằng
`python scripts/evaluate.py --model <tên> --split test --final`.
