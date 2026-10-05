# Tổng kết đến Phase 5

**Đề tài:** Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính
**Cập nhật:** 2026-10-05
**Đọc kèm:** `CLAUDE.md` (quy ước) → `docs/SPEC.md` (13 phase, đã sửa 2026-10-05)
→ `docs/ipn_format.md` (dữ liệu IPN) → `docs/gestures.md` (bộ cử chỉ) → file này.
Bản tổng kết trước: `docs/tong-ket-phase-0-1.md` (viết theo SPEC cũ 12 phase).

---

## 1. Tóm tắt

Hệ thống đã **chạy được đầu-cuối**: webcam → 21 điểm mốc MediaPipe → cửa sổ 1,2 giây
→ 15 đặc trưng → mô hình luật → nhãn trên màn hình
(`python scripts/demo.py --model rules`). Toàn bộ 200 video IPN Hand đã thành điểm mốc,
bộ cửa sổ đã dựng và chia theo người, cổng kiểm tra đặc trưng của Phase 4 đã đạt, ba
ngưỡng luật đã hiệu chuẩn trên tập train.

Mô hình luật **vượt hai đường cơ sở nhưng còn yếu**: macro-F1 trên val 0,2305 so với
0,1964 (luôn đoán `none`). Điểm yếu chính là báo nhầm: 44% cửa sổ không có cử chỉ bị gán
thành một cử chỉ. Phần thử trực tiếp trên webcam của Phase 5 chưa làm.

`pytest -q`: **90 passed**.

---

## 2. Trạng thái các phase

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 0 | Khung dự án, `config.py`, `require_measured` | ✅ xong |
| 1A | `iter_frames`, `HandTracker`, `live_landmarks`, `record_csv` | ✅ code xong — chưa có biên bản xác nhận bằng mắt trên webcam |
| 1B | `observe.py`, `analyze_observations.py` (thí nghiệm quan sát) | ⬜ code xong, **chưa chạy thí nghiệm nào** (`results/phase1/` chưa tồn tại). Không chặn phase nào |
| 2 | Tiền xử lý, chuẩn hoá, đặc trưng | ✅ xong; sửa lại 2026-10-05 (15 đặc trưng, kiểm tra lòng bàn tay) |
| 3 | Trích điểm mốc IPN, đo quy ước hướng | ✅ xong 5/6 mục; `docs/gestures.md` là **bản nháp chờ người dùng review** |
| 4 | Cửa sổ, tăng cường, chia tập theo người | ✅ xong, cổng boxplot **đạt** (cổng đã đổi, người dùng duyệt) |
| 5 | Mô hình luật và demo v0 | 🟡 phần code và đo offline xong; **5 mục thử trên webcam còn chờ người dùng** |
| 6–12 | Rừng ngẫu nhiên, LSTM, đánh giá, máy trạng thái, demo hoàn chỉnh, tái lập | ⬜ chưa bắt đầu |

---

## 3. Kết quả chính

### 3.1. Dữ liệu IPN — sửa lỗi lệch số frame (Phase 3)

Câu hỏi "15 video lệch độ dài" từng chặn Phase 3 hoá ra có nguyên nhân khác:

- **Bộ giải mã FFmpeg âm thầm bỏ frame "not coded" của XVID** (chunk 6 byte, nghĩa là
  "giữ nguyên ảnh trước"): 101/200 video có, tổng 677 frame, nhiều nhất 56 frame một video.
  `iter_frames` cũ đếm số lần `read()` nên `ts` và chỉ số frame lệch sau mỗi frame bị bỏ.
  **Đã sửa:** `ts` lấy theo vị trí frame trong container (`CAP_PROP_POS_MSEC`).
- **Nhãn IPN đếm frame không thống nhất giữa các video.** `ipn.match_label_frames` chọn cách
  đếm cho từng video bằng số đo, kiểm chứng bằng điểm mốc:

| Nhãn khớp với | Số video | Xử lý |
|---|---|---|
| Hai cách như nhau (≤ 1 frame bị bỏ) | 128 | dùng bình thường |
| Số chunk (tính cả frame bị bỏ) | 57 | ánh xạ theo vị trí container |
| Số frame giải mã (không tính) | 4 | ánh xạ theo chỉ số hàng |
| Không khớp cách nào | 11 | **loại** (`length_mismatch=True`) |

- 11 video bị loại: 8 thuộc test, 3 thuộc train. Người `1CM1_2` mất cả 4 video test.
- Danh sách "15 video" cũ sai vì lập bằng `CAP_PROP_FRAME_COUNT`; các "dấu hiệu sớm" về
  hướng khi đó cũng sai vì tính trên 5 video lệch.

Chi tiết: `docs/ipn_format.md` mục 6.

### 3.2. Trích điểm mốc và thống kê (Phase 3)

- 200/200 file `.npz`, 0 lỗi; lượt chạy chính 2,27 giờ với 4 tiến trình
  (`results/phase3/extract/run_04`). Kiểm toàn bộ: đúng schema, đúng cách đếm frame,
  đoạn nhãn nối liền.
- **Quy ước hướng** (`results/phase3/direction/run_05`, 189 clip): trung vị `dx` của
  `swipe_left` +0,46, `swipe_right` −0,54 → **`SWIPE_LEFT_SIGN = 1`**. `swipe_left` (G05
  "Throw left") là tay đi về phía **bên trái của chính người làm**. Trung vị `open_delta`
  `zoom_in` +0,20, `zoom_out` −0,30: bảng ánh xạ nhãn đúng chiều.
- **Thống kê** (`results/phase3/dataset_stats/run_02`):

| Lớp | Tỉ lệ mất tay | Trung vị thời lượng | p90 | Dài hơn 1,2 s |
|---|---|---|---|---|
| swipe_left | 5,3% | 2,00 s | 3,56 s | 92% |
| swipe_right | 6,4% | 1,93 s | 3,42 s | 89% |
| zoom_in | 5,5% | 2,00 s | 3,40 s | 89% |
| zoom_out | 3,3% | 1,97 s | 3,48 s | 91% |

- **Đoạn mẫu:** 12 video, 3 người mỗi lớp (`results/phase3/examples/`).
- **Bộ cử chỉ** (`docs/gestures.md`, bản nháp):
  - zoom của IPN là chụm/mở **ba đầu ngón cái, trỏ, giữa**, nhẫn và út gập suốt;
  - vuốt là **cú hất ngắn**: chuẩn bị, động tác chính ~0,3 s, thu tay;
  - mỗi cử chỉ ~2 s.

### 3.3. Bộ cửa sổ (Phase 4)

- **Chia theo người** (`data/splits.json`): train 30 người, val 7 (chọn từ split train chính
  thức, seed 42), test 13 (đúng split chính thức). Phép giao giữa mọi cặp tập rỗng.
- **`data/windows/windows.npz`**, X `(37504, 18, 21, 2)`, nạp trong 0,43 s
  (`results/phase4/build_dataset/run_02`):

| Tập | Cửa sổ | none | Mỗi lớp đích |
|---|---|---|---|
| train (sau lấy mẫu con) | 3 326 | 50,0% | ~415 |
| val (phân bố tự nhiên) | 11 038 | 96,5% | ~96 |
| test (phân bố tự nhiên) | 23 140 | 97,2% | ~160 |

- **`AUG_NOISE_SIGMA = 0.0159`** lòng bàn tay, đo trên tay nghỉ `D0X`
  (`results/phase4/sigma/run_02`).
- **Cổng boxplot — ĐẠT** (`results/phase4/boxplots/run_03`):

| Điều kiện | Kết quả |
|---|---|
| `pinch_delta`: zoom_in hẳn bên dương | p25 = +0,703 |
| `pinch_delta`: zoom_out hẳn bên âm | p75 = −0,579 |
| `pinch_delta`: hai hộp zoom không chồng nhau | −0,579 < +0,703 |
| `dx`: hai hộp vuốt ở hai phía của 0 | swipe_left [+0,13; +1,35], swipe_right [−1,12; −0,31] |
| `max_vx`: hai lớp vuốt cao hơn hẳn none | p25 3,59 / 3,70 so với p75 none 3,30 — **sát nút** |

- Cửa sổ ngẫu nhiên mỗi lớp xem bằng mắt đều đúng cử chỉ
  (`results/phase4/window_examples/run_02`).

### 3.4. Mô hình luật (Phase 5)

- **Ngưỡng hiệu chuẩn trên train** (`results/phase5/thresholds.md`):
  - `RULE_VX_HI = 4.026` (`max_vx`);
  - `RULE_DX_HI = 0.1025` (`|dx|`);
  - `RULE_P_HI = 0.7209` (`|pinch_delta|`).

  Hai ngưỡng `max_vx` và `pinch_delta` có cảnh báo chồng phân vị 90/10.
- **Đánh giá trên val** (`results/phase5/eval_rules/run_01`):

| Lớp | Precision | Recall | F1 |
|---|---|---|---|
| none | 0,984 | 0,560 | 0,714 |
| swipe_left | 0,030 | 0,577 | 0,056 |
| swipe_right | 0,023 | 0,438 | 0,043 |
| zoom_in | 0,097 | 0,543 | 0,164 |
| zoom_out | 0,103 | 0,617 | 0,176 |
| **macro-F1** | | | **0,2305** |
| Đường cơ sở luôn `none` | | | 0,1964 |
| Đường cơ sở ngẫu nhiên | | | 0,0796 |

  Hàng đầu tiên của bảng so sánh mô hình: `results/model_comparison.md`.
- **Demo:** đã chạy thử đầu-cuối trên video IPN tập val (không mở cửa sổ) và đã dựng thử
  màn hình. Đã sửa lỗi chữ trên màn hình bị nhân đôi, có từ Phase 1.

---

## 4. Giải pháp thực hiện

Mục này mô tả **cách** đi tới các kết quả ở mục 3 và **vì sao** chọn cách đó.

### 4.1. Nguyên tắc làm việc xuyên suốt

- **Một đường ống cho mọi nguồn.** Dữ liệu IPN, webcam lúc chạy thật, và dữ liệu tự quay
  nếu có, đi qua đúng cùng các bước theo thứ tự cố định:
  1. đổi toạ độ sang pixel;
  2. đưa về lưới thời gian đều 15 Hz;
  3. vá lỗ hổng ngắn;
  4. cắt cửa sổ;
  5. tăng cường, chỉ khi huấn luyện;
  6. chuẩn hoá cửa sổ;
  7. tính đặc trưng hoặc đưa vào mô hình.

  Không bao giờ có hai bản xử lý "gần giống nhau" cho hai nguồn.
- **Đo trước, quyết sau.** Hằng số quy ước (hướng vuốt, độ lệch chuẩn nhiễu, ba ngưỡng luật)
  đều do script đo trên dữ liệu rồi in ra để dán; chương trình dừng ngay nếu một hằng số
  chưa đo mà bị dùng.
- **Khi một giả định của SPEC không đứng được trên dữ liệu thật**, làm theo trình tự:
  1. dựng bản thử nghiệm trên tập train;
  2. so các phương án bằng số đo;
  3. trình người dùng duyệt;
  4. sau đó mới sửa code và ghi lý do vào SPEC.
- **Mọi quyết định chỉ dựa trên tập train.** Val dùng để đánh giá trong quá trình làm; test
  khoá lại tới lần đánh giá cuối cùng.
- **Mỗi lần chạy script có hồ sơ riêng:** một thư mục kết quả đánh số, kèm dòng lệnh, thời
  điểm, seed và bản sao toàn bộ hằng số. Bảng xuất song song hai dạng, hình xuất 150 dpi.
- **Kiểm thử không phụ thuộc dữ liệu thật hay webcam.** Dùng bàn tay 21 điểm dựng bằng hình
  học, với các mẫu vuốt, zoom, đứng yên và vẫy tay có tính chất biết trước.

### 4.2. Thu nhận điểm mốc

- MediaPipe Hand Landmarker (Tasks API), chế độ video, tối đa một bàn tay. Chỉ dùng toạ độ
  2D chuẩn hoá: độ sâu `z` ước lượng không tin cậy nên bỏ.
- Frame không thấy tay vẫn được ghi lại với toạ độ rỗng, **không bỏ frame**. Nếu bỏ, trục
  thời gian bị đứt và bước nội suy sẽ âm thầm nối qua khoảng mất tay.
- Ảnh đưa vào mô hình **không lật**; chỉ bản hiển thị cho người xem được lật như gương.
- Mốc thời gian: webcam dùng đồng hồ thật vì FPS webcam dao động; file video dùng vị trí
  của frame trong file (mục 4.3).

### 4.3. Chẩn đoán và sửa lệch frame giữa video và nhãn IPN

1. **Đếm số frame theo ba cách độc lập** cho cả 200 video:
   - số khai báo trong header;
   - số chunk video trong chỉ mục của file AVI, kèm kích thước từng chunk;
   - số frame giải mã tuần tự thật.

   Phát hiện đẳng thức "số frame giải mã + số chunk 6 byte = tổng số chunk" đúng ở mọi
   video. Kết luận: bộ giải mã bỏ đúng các frame "not coded".
2. **Xác nhận vị trí frame bị bỏ** bằng vị trí mà OpenCV báo sau mỗi lần đọc: dãy vị trí
   tăng ngặt, có khoảng trống đúng tại các chunk 6 byte. Từ đó đổi mốc thời gian của video
   sang vị trí trong file, thay cho cách đếm số lần đọc.
3. **Phân nhóm video bằng số đếm.** So số frame mà nhãn phủ với hai cách đếm (tính hoặc
   không tính frame bị bỏ), ra bốn nhóm như bảng ở mục 3.1.
4. **Kiểm vị trí, không chỉ kiểm số đếm**, bằng điểm mốc:
   - Tay thường rời khỏi khung hình trong đoạn không cử chỉ, nên tín hiệu "có tay" đổi trạng
     thái gần các ranh giới giữa đoạn nghỉ và đoạn cử chỉ.
   - Tại mỗi ranh giới, dịch nhãn trong khoảng ±70 frame và tìm độ dịch làm tín hiệu khớp
     nhãn nhất.
   - Trước hết đo độ nhiễu của chính phép đo trên video đã biết khớp: −2…+6 frame.
   - Rồi áp lên video đại diện của từng nhóm. Cách ánh xạ đúng cho độ dịch nằm trong độ
     nhiễu; cách sai trôi dần tới 40–60 frame dọc video.
5. **Thử và loại hai hướng không đạt:**
   - Tín hiệu tốc độ chuyển động: không phân biệt được cử chỉ với tay chỉ trỏ, nên sai ngay
     cả trên video đã biết khớp.
   - "Bỏ frame lặp lại": không thành quy tắc chung, vì video khớp nhãn cũng có frame lặp.
6. **Triển khai:**
   - Với mỗi video, chọn cách đếm cho tổng số frame gần số frame nhãn nhất.
   - Lệch quá 5 frame thì gắn cờ, và mọi bước dùng nhãn bỏ qua video đó.
   - Quét lại cả 200 video bằng code mới: không lỗi, phân nhóm đúng như dự kiến.

### 4.4. Trích điểm mốc toàn bộ IPN

- **Cách đọc và cấu trúc dữ liệu:**
  - Đọc tuần tự, mỗi video một bộ bám tay mới, vì chế độ video giữ trạng thái giữa các frame.
  - Mỗi video lưu thành một file gồm:
    - toạ độ thô, **chưa chuẩn hoá**: chuẩn hoá là quyết định thiết kế có thể đổi, điểm mốc
      thô thì không;
    - mốc thời gian và cờ có tay;
    - các đoạn nhãn đã quy về chỉ số hàng, và nhãn gốc;
    - thông tin về cách đếm frame.
- **Chạy được qua đêm:**
  - Video đã có file thì bỏ qua, nên chạy lại là tiếp tục, không làm lại từ đầu.
  - Video lỗi ghi ra danh sách riêng rồi chạy tiếp.
  - Chạy 4 tiến trình song song. Tốc độ được đo thật chứ không nhân tuyến tính, vì MediaPipe
    vốn đã dùng nhiều luồng.
- **Chạy trên máy, không dùng Colab,** để giữ đúng phiên bản MediaPipe, OpenCV và bộ giải mã
  của hệ thống chạy thật.
- **Kiểm lại toàn bộ sau khi trích.** Với từng file:
  - nạp được, đúng kiểu dữ liệu;
  - mốc thời gian bắt đầu từ 0 và tăng ngặt;
  - cờ có tay khớp với toạ độ rỗng;
  - cách đếm frame khớp lượt quét;
  - đoạn nhãn nối liền nhau và phủ cả clip.

### 4.5. Đo quy ước hướng trên IPN

- **Cách tính:** với mỗi đoạn cử chỉ đích, đưa qua đường ống, chuẩn hoá theo frame đầu đoạn,
  rồi tính dời ngang của cổ tay và thay đổi độ xòe.
- **Loại các đoạn mất tay ở đầu hoặc cuối.** Đặc trưng không tính được sẽ trả về 0, và những
  số 0 đó đã từng suýt làm sai trung vị.
- **Kết luận theo trung vị từng lớp:** hai lớp vuốt phải trái dấu, zoom in phải dương, zoom
  out phải âm. Không đạt thì không đề xuất giá trị nào. Báo kèm tỉ lệ đoạn cùng dấu với
  trung vị lớp mình, để thấy độ nhiễu của từng đoạn.
- **Hằng số lật trục ngang cho IPN chỉ được áp ở đúng một chỗ:** lúc nạp clip. Như vậy không
  bao giờ lật hai lần.

### 4.6. Thống kê, đoạn mẫu và mô tả bộ cử chỉ

- **Thời lượng** đoạn tính theo mốc thời gian thật, không theo số hàng, để frame bị bộ giải
  mã bỏ không làm cử chỉ ngắn đi.
- **Clip lệch nhãn** vẫn có trong bảng theo clip, nhưng không góp vào số liệu theo lớp.
- **Đoạn mẫu:** ba người khác nhau mỗi lớp, ảnh không lật, có vẽ điểm mốc. Chỗ frame bị bỏ
  được lặp frame trước cho kín, như trình phát video vẫn làm, để đoạn mẫu phát đúng tốc độ.
- **Mô tả bộ cử chỉ dựa trên số đo của tập train**, theo đơn vị "lòng bàn tay" (cổ tay tới
  gốc ngón giữa):
  - vị trí bắt đầu trong khung hình;
  - dời ngang và dọc, biên độ;
  - tốc độ cổ tay đỉnh;
  - thời gian của động tác chính (từ 10% tới 90% thay đổi);
  - độ duỗi từng ngón: khoảng cách đầu ngón tới cổ tay chia khoảng cách gốc ngón tới cổ tay.
    Thang đo này được hiệu chuẩn bằng lớp "chỉ một ngón", vì đã biết ngón nào duỗi;
  - khoảng cách cái–trỏ.

  Đối chiếu bằng mắt trên ảnh cắt quanh bàn tay ở 8 thời điểm của mỗi đoạn mẫu, và so với
  các lớp dễ nhầm.

### 4.7. Tiền xử lý, chuẩn hoá và đặc trưng

- **Đưa về lưới đều 15 Hz:** chỉ nội suy giữa hai frame **cùng có tay**, không bao giờ nối
  qua khoảng mất tay. Lỗ hổng tối đa 3 bước và có đủ hai đầu thì vá; lỗ dài hơn giữ rỗng,
  vì mất tay lâu là tín hiệu thật.
- **Chuẩn hoá cửa sổ:**
  - Gốc là cổ tay ở frame đầu, đơn vị là khoảng cách cổ tay tới gốc ngón giữa ở frame đầu.
  - Hai thứ này dùng chung cho mọi frame trong cửa sổ, nhờ vậy giữ nguyên quỹ đạo chuyển
    động. Trừ cổ tay của từng frame sẽ xoá mất cú vuốt.
  - Cửa sổ bị từ chối khi lòng bàn tay ở frame đầu ngắn hơn một nửa trung vị của chính cửa
    sổ đó (tay nghiêng cạnh, hoặc điểm mốc sai). Phép so chỉ dùng các frame trong cửa sổ nên
    vẫn nhân quả. Ngưỡng 0,5 chọn bằng đo: loại 2% cửa sổ và xoá các đặc trưng ngoại lai lớn
    tới 30 lòng bàn tay.
- **15 đặc trưng**, chia năm nhóm:
  - độ xòe (trung bình khoảng cách năm đầu ngón tới cổ tay);
  - độ mở cái–trỏ;
  - quỹ đạo và vận tốc cổ tay;
  - độ thẳng và tỉ lệ ngang;
  - tỉ lệ bước có tay.

  "Đầu" và "cuối" là trung bình 3 bước đầu và 3 bước cuối. Đặc trưng không bao giờ rỗng.
  Năm đặc trưng có dấu mang thông tin hướng; phần đặc trưng không suy ra trái hay phải, việc
  đó dành cho mô hình qua hằng số hướng đã đo.

### 4.8. Cắt cửa sổ và gán nhãn

- **Cắt cửa sổ:**
  - Cửa sổ dài 1,2 giây (18 bước), trượt mỗi 0,2 giây (3 bước). Tính bằng giây, không bằng
    frame, để IPN 30 FPS và webcam tốc độ khác vẫn cho cùng một cửa sổ thời gian.
  - Cắt trong phạm vi từng clip, nên không cửa sổ nào bắc cầu qua hai video.
  - Loại cửa sổ có tay ở dưới 70% số bước, hoặc mất tay ngay bước đầu.
- **Gán nhãn neo vào khoảnh khắc chính:**
  - Với mỗi đoạn cử chỉ, tìm bước mà tín hiệu thay đổi nhanh nhất: vị trí ngang cổ tay với
    vuốt, khoảng cách cái–trỏ với zoom. Tín hiệu được làm mượt 3 bước, chia cho cỡ lòng bàn
    tay trung vị của đoạn, và chỉ xét độ lớn, không xét dấu.
  - Cửa sổ là dương khi khoảnh khắc chính nằm cách hai mép cửa sổ ít nhất 3 bước.
  - Cửa sổ chạm vào đoạn cử chỉ mà không chứa khoảnh khắc đó thì bỏ hẳn, không gán `none`.
  - Cửa sổ không chạm cử chỉ nào là `none`.
- **Cách đi tới luật này:**
  1. So ba luật bằng ba chỉ số đo trên train: số cửa sổ dương, số cử chỉ có ít nhất một cửa
     sổ dương, và tỉ lệ cửa sổ dương chứa khoảnh khắc chính. Ba luật gồm: luật SPEC (lớp
     chiếm 60% cửa sổ), luật cẩm nang (cửa sổ phủ 60% cử chỉ), và một luật hợp nhất hai cái.
  2. Khi cổng không đạt, tách cửa sổ dương thành hai nhóm có và không chứa khoảnh khắc chính,
     rồi kiểm cổng riêng từng nhóm. Cách này chỉ ra nguyên nhân là nhãn hay là đặc trưng.
  3. Thử hai biên 0 và 3 bước, chọn 3 vì chỉ biên này qua được điều kiện hướng.
- **Không phạm luật nhân quả:** nhãn là chân lý ngoại tuyến, như chính file nhãn của IPN; mô
  hình không bao giờ thấy nó.

### 4.9. Chia tập theo người và lấy mẫu con lớp nền

- **Mã người:**
  - Lấy hai token đầu của tên video.
  - Đã kiểm trên file split chính thức: ra 50 người, mỗi người 4 video, không ai có video ở cả
    hai tập. Lấy một token đầu thì sai.
- **Chia tập:**
  - Test giữ đúng split test chính thức, để so được với công bố khác.
  - Val là 20% số người của split train, chọn ngẫu nhiên có seed.
  - Chia tập là phép lọc theo cột người, không bao giờ chia ngẫu nhiên trên cửa sổ, vì các
    cửa sổ liền nhau gần như giống hệt nhau.
- **Lấy mẫu con lớp nền, chỉ ở tập train:**
  1. Ngân sách cửa sổ `none` tính từ số cửa sổ dương sao cho `none` chiếm 50%.
  2. Ngân sách chia đều cho các nhóm nhãn gốc theo kiểu "rót nước": nhóm nhỏ hơn phần chia
     thì lấy hết, phần dư dồn cho các nhóm còn lại.
  3. Trong mỗi nhóm, chọn ngẫu nhiên có seed.
- **Val và test giữ nguyên phân bố tự nhiên,** để con số đánh giá phản ánh đúng thực tế.

### 4.10. Tăng cường dữ liệu

- **Mỗi phép trả lời câu hỏi "có làm đổi lớp không":**
  - lật ngang đổi nhãn cặp vuốt cho nhau và giữ nhãn zoom;
  - xoay nhẹ, co giãn, co giãn thời gian, nhiễu và xoá bước đều giữ nhãn.
- **Áp trên cửa sổ đã chuẩn hoá rồi chuẩn hoá lại.** Cách này tương đương thứ tự của SPEC
  (tăng cường trước chuẩn hoá), vì:
  - chuẩn hoá một cửa sổ đã chuẩn hoá không đổi gì;
  - các phép hình học giao hoán với phép dời và phép co giãn đều mà chuẩn hoá thực hiện.
- **Co giãn đều bị chuẩn hoá triệt tiêu hoàn toàn;** một kiểm thử đã chứng minh điều này. Vì
  vậy thay bằng co giãn đổi dần dọc cửa sổ, mô phỏng tay tiến hoặc lùi so với camera.
- **Các phép còn lại:**
  - co giãn thời gian neo ở bước đầu;
  - xoá 1–3 bước không chạm hai mép, rồi vá;
  - nhiễu Gauss tính theo đơn vị lòng bàn tay.

  Mọi phép đều giữ bước đầu hữu hạn để chuẩn hoá luôn chạy được.
- **Chặn ở mức hàm:** tăng cường từ chối mọi tập khác train, và tạo mới ở mỗi epoch (dùng từ
  Phase 6).
- **Ước lượng σ nhiễu:**
  1. Lấy 5% cửa sổ `none` của train có cổ tay dời ít nhất, đo độ lệch chuẩn của đầu ngón quanh
     vị trí trung bình, lấy trung vị.
  2. Kiểm thành phần các cửa sổ được chọn: phần lớn là động tác bấm ngón và xòe tay, tức cử
     động có chủ ý chứ không phải độ rung. Vì vậy giới hạn lại vào tay nghỉ.
  3. Đối chiếu với một ước lượng độc lập, nhiễu tần số cao tính bằng sai phân bậc hai: hai số
     khớp nhau (0,0159 và 0,0162).

### 4.11. Cổng kiểm tra đặc trưng

- **Cách kiểm:** dùng phân vị 25/75 trên tập train sau lấy mẫu con, kèm xem hình boxplot.
  Điều kiện về hướng chỉ yêu cầu hai hộp nằm ở hai phía của 0, không giả định lớp nào bên
  dương.
- **Khi cổng không đạt:**
  1. Chẩn đoán nguyên nhân bằng cách tách nhóm (mục 4.8).
  2. Dựng bản thử nghiệm trên train cho từng phương án: luật nhãn, biên, đặc trưng mới,
     ngưỡng lòng bàn tay.
  3. Chỉ triển khai khi số đo cho thấy cổng đạt.
  4. Đổi điều kiện cổng khi có người dùng duyệt. Điều kiện cũ vẫn được in dưới nhóm "tham
     khảo" để theo dõi.
- **Xem bằng mắt** quỹ đạo cổ tay, độ xòe và độ mở cái–trỏ của một cửa sổ ngẫu nhiên mỗi lớp.

### 4.12. Mô hình luật, hiệu chuẩn và đánh giá

- **Ngưỡng:**
  - Mỗi ngưỡng là trung điểm giữa phân vị 90 của nhóm phải nằm dưới và phân vị 10 của nhóm
    phải nằm trên.
  - Riêng dời ngang lấy phân vị 10 của hai lớp vuốt.
  - Hai phân vị chồng nhau thì vẫn đề xuất trung điểm nhưng cảnh báo.
  - Chỉ tính trên train. Kiểm thử chứng minh: thêm dữ liệu val/test cực đoan vào cũng không
    làm ngưỡng đổi.
- **Thứ tự luật:**
  1. Thiếu tay thì là `none`.
  2. Xét vuốt trước: tốc độ ngang đỉnh và dời ngang đều phải vượt ngưỡng. Hướng lấy theo dấu
     dời ngang so với hằng số đã đo, không viết cứng ở đâu.
  3. Rồi mới xét zoom, theo dấu thay đổi độ mở cái–trỏ. Vuốt phải đứng trước vì cú hất của
     IPN mở bàn tay ra, làm khoảng cách cái–trỏ thay đổi.
  - Độ tin là một heuristic theo mức vượt ngưỡng yếu nhất, không phải xác suất.
- **Đánh giá ở mức cửa sổ trên val:**
  - ma trận nhầm lẫn, precision/recall/F1 từng lớp, macro-F1;
  - hai đường cơ sở: đoán ngẫu nhiên đều 5 lớp, và luôn đoán `none`;
  - kết quả ghi thành một hàng trong bảng so sánh mô hình;
  - tập test chỉ chạy được khi chỉ định rõ đó là lần chạy cuối cùng.

### 4.13. Demo thời gian thực

- **Đường đi của dữ liệu:**
  1. Bộ đệm giữ 1,7 giây gần nhất **theo thời gian**, không theo số frame, vì FPS webcam dao
     động.
  2. Mỗi 0,2 giây, lấy 18 bước cuối qua đúng đường ống của IPN.
  3. Chuẩn hoá, tính đặc trưng, đưa vào luật.

  Mọi xử lý nằm trong thư viện; script demo chỉ nối camera, màn hình và file log.
- **Màn hình:**
  - lật gương, vẽ khung xương bàn tay;
  - nhãn lớn kèm độ tin, hoặc "-" khi không có cửa sổ hợp lệ;
  - chế độ luyện tập so ba đặc trưng của cửa sổ vừa rồi với hộp 25–75 của lớp tương ứng trên
    IPN, tô xanh hoặc đỏ, chọn lớp bằng phím 1–4.
- **Log và đếm báo nhầm:**
  - mỗi lần dự đoán ghi một dòng;
  - khi thoát, đếm "đợt báo": một chuỗi dự đoán liền nhau cùng nhãn là một đợt.
- **Kiểm tra không cần webcam:**
  - chạy không mở cửa sổ trên video IPN tập val: đúng nhịp 0,2 giây, log đủ cột;
  - dựng thử màn hình từ khung hình thật để xem bằng mắt;
  - sửa lỗi chữ nhân đôi bằng cách vẽ nền tối phía sau chữ, thay cho viền chữ dày. Với font
    của OpenCV, độ dày làm ký tự rộng ra, nên viền trôi dần khỏi chữ.

---

## 5. Quyết định đã chốt (người dùng duyệt)

| Ngày | Quyết định | Lý do |
|---|---|---|
| 2026-10-01 | `iter_frames`: `ts` theo vị trí frame trong container | Bộ giải mã bỏ frame "not coded" |
| 2026-10-01 | Chọn cách đếm frame của nhãn cho từng video; loại 11 video không khớp | Nhãn IPN không thống nhất; vị trí đã kiểm bằng điểm mốc |
| 2026-10-05 | Trích điểm mốc chạy trên máy, không dùng Colab | Giữ đúng phiên bản MediaPipe/OpenCV/FFmpeg của đường ống |
| 2026-10-05 | Lấy mẫu con `none` chia đều theo nhãn gốc, none = 50% train | Không thể vừa giữ hết mẫu âm khó vừa giữ none ở 40–50% |
| 2026-10-05 | Co giãn ±10% thành co giãn **đổi dần** theo thời gian | Co giãn đều bị `normalize_window` triệt tiêu |
| 2026-10-05 | `AUG_NOISE_SIGMA = 0.0159` (tay nghỉ D0X) thay 0,054 | 0,054 chủ yếu đo cử động ngón có chủ ý |
| 2026-10-05 | Nhãn cửa sổ **neo vào khoảnh khắc chính** (`CORE_MARGIN_STEPS = 3`), bỏ cửa sổ mơ hồ | Luật 60% của SPEC: 49% cửa sổ dương không chứa động tác |
| 2026-10-05 | Thêm `pinch_delta`, `pinch_range` → 15 đặc trưng | Zoom IPN là chụm/mở ba ngón; `open_delta` tách yếu |
| 2026-10-05 | `normalize_window` từ chối lòng bàn tay frame đầu < 0,5 × trung vị cửa sổ | Đặc trưng ngoại lai tới 30 lòng bàn tay |
| 2026-10-05 | Cổng Phase 4: `pinch_delta`, `dx`, `max_vx` (bỏ `open_delta`, `straightness`) | Hai đặc trưng cũ không tách lớp trên IPN |
| 2026-10-05 | Luật Phase 5 dùng `max_vx` và `pinch_delta`; đổi tên `RULE_S_HI` → `RULE_VX_HI`, `RULE_O_HI` → `RULE_P_HI` | Theo cổng mới |

Mọi thay đổi trên đã ghi vào `docs/SPEC.md` kèm ngày và lý do tại chỗ.

---

## 6. Vấn đề còn phải xử lý

### 6.1. Đang chặn việc đóng Phase 5 — việc của người dùng

1. `python scripts/demo.py --model rules` chạy mượt trên webcam.
2. Vuốt sang trái **của bạn** ra `swipe_left`. Nếu ngược: đặt `IPN_FLIP_X = -1` và chạy lại
   phép đo Phase 3–5 (mục Cổng chất lượng trong SPEC), **không sửa code**.
3. `--show-features`: ba đặc trưng xanh ít nhất 7/10 lần cho mỗi cử chỉ.
4. Làm mỗi cử chỉ 10 lần theo `docs/gestures.md`: đúng ít nhất 7; vẫy tay không ra `swipe`.
5. Gõ phím và dùng chuột 2 phút với `--log`, ghi `results/phase5/misfires.md` (số đợt báo
   nhầm — đường cơ sở để so ở Phase 6 và 10).

### 6.2. Chất lượng mô hình và dữ liệu

- **Báo nhầm cao:** 44% cửa sổ `none` trên val bị gán thành cử chỉ, chủ yếu thành vuốt.
  Tay chỉ trỏ (`B0A`/`B0B`) của IPN di chuyển nhanh ngang cú hất.
  Hướng xử lý: Phase 6 (rừng ngẫu nhiên) và Phase 9 (máy trạng thái).
- **`max_vx` là chỗ yếu nhất của bộ đặc trưng:** qua cổng sát nút (3,59 so với 3,30).
- **Tập train nhỏ:** ~415 cửa sổ dương mỗi lớp, sau khi đổi luật nhãn (trước là ~950) và
  loại 11 video. Tăng cường mỗi epoch ở Phase 6–7 là cách bù chính.
- **Nhãn dương phụ thuộc tín hiệu chuyển động** (độ lớn, không dấu). Báo cáo phải nói rõ.
- **Còn sót ngoại lai do điểm mốc nhảy giữa cửa sổ** (ví dụ một cửa sổ `max_vx` = 124).
  Kiểm tra lòng bàn tay ở frame đầu không bắt được loại này.
- **Tay trái:** 12/145 clip dùng được của split train chính thức là tay trái. Chưa đo riêng;
  nên dùng tay phải khi demo.
- **Mất 8 video test:** test còn 44 video, 12 người.

### 6.3. Tài liệu và tái lập (luật 14)

- `docs/gestures.md` là **bản nháp do Claude viết** — người dùng phải review; SPEC giao việc
  này cho người.
- Các số đo trong `docs/gestures.md` (bảng thứ hai) và các phép chẩn đoán lệch frame IPN
  được tính bằng **script tạm, không nằm trong repo**. Muốn tái lập được cho báo cáo thì
  phải đưa vào `scripts/`.
- `README.md` chưa cập nhật giá trị các hằng số đã đo, cách đo, và thứ tự chạy script mới
  (việc của Phase 12, nhưng nên ghi dần).
- Phase 1B (thí nghiệm quan sát) chưa chạy. Không chặn gì, vì σ đã ước lượng trên IPN, nhưng
  báo cáo sẽ thiếu số đo giới hạn của MediaPipe trên máy thật.
- `docs/ban-giao-ngu-canh.md` (bàn giao ngữ cảnh ngày 2026-10-01) đã bị xoá khỏi `docs/`;
  file này thay vai trò đó.

### 6.4. Ghi chú kỹ thuật nhỏ

- Co giãn thời gian khi tăng tốc (hệ số > 1) giữ nguyên bước cuối cho đủ `T` bước, vì cửa sổ
  không có dữ liệu phía sau.
- Khảo sát "ngưỡng phủ nhãn 40/60/80%" ở Phase 8 đã đổi thành khảo sát biên khoảnh khắc chính
  0/3/6 bước.

---

## 7. Kết quả trên đĩa — bản nào là hiện hành

| Thư mục | Hiện hành | Cũ, đừng dùng |
|---|---|---|
| `results/phase3/direction/` | `run_05` (và `direction.md`) | `run_01`–`run_03` tính trên clip lệch; `run_04` trước khi sửa `normalize_window` |
| `results/phase3/dataset_stats/` | `run_02` | `run_01` (7 clip cũ) |
| `results/phase4/build_dataset/` | `run_02` | `run_01` (luật nhãn 60%) |
| `results/phase4/boxplots/` | `run_03` | `run_01` (luật cũ, 0/5), `run_02` (trước khi duyệt cổng) |
| `results/phase4/sigma/` | `run_02` (D0X, 0,0159) | `run_01` (mọi none, 0,054) |
| `results/phase4/window_examples/` | `run_02` | `run_01` |
| `results/phase5/` | `calibrate/run_01`, `eval_rules/run_01`, `thresholds.md` | — |

---

## 8. Lệnh tái lập từ điểm mốc tới mô hình luật

```
python scripts/extract_landmarks.py --source ipn --workers 4   # ~2,3 giờ, chạy lại là tiếp tục
python scripts/measure_direction.py                            # → SWIPE_LEFT_SIGN
python scripts/dataset_stats.py
python scripts/export_examples.py
python scripts/make_splits.py                                  # → data/splits.json
python scripts/build_dataset.py                                # → data/windows/windows.npz
python scripts/estimate_sigma.py --src-label D0X               # → AUG_NOISE_SIGMA
python scripts/plot_feature_boxplots.py                        # cổng Phase 4, ipn_feature_ranges.json
python scripts/plot_window_examples.py
python scripts/calibrate_rules.py                              # → ba ngưỡng RULE_*
python scripts/eval_rules.py                                   # val; test cần --final
python scripts/demo.py --model rules [--show-features] [--log FILE]
```
