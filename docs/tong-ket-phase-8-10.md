# Phase 8, 9 và 10 — đã làm được gì

**Đề tài:** Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính.

**Cập nhật:** 2026-11-02

**Phạm vi:** ba giai đoạn sau Phase 7, cộng phần đầu của Phase 12.

- **Phase 8** chấm mọi mô hình ở hai mức và chạy bảy bảng khảo sát.
- **Phase 9** thêm *máy trạng thái*: biến chuỗi nhãn nhấp nháy thành lệnh rời rạc.
- **Phase 10** hoàn chỉnh demo điều khiển slide thật và đo hệ thống trên webcam.

**Đọc kèm:**

- bản tổng kết trước: `docs/tong-ket-den-phase-7.md`;
- quy ước và kế hoạch: `CLAUDE.md`, `docs/SPEC.md`;
- cách làm cử chỉ: `docs/gestures.md`;
- ghi chú chi tiết: `results/phase8/notes.md`, `results/phase9/notes.md`,
  `results/phase10/notes.md`, `results/phase10/final_config.md`.

---

## 1. Tóm tắt

Hệ thống **điều khiển được PowerPoint bằng cử chỉ**:

```
python scripts/demo.py --model hybrid
```

Bấm `c` để bật điều khiển. Vuốt trái sang slide sau, vuốt phải về slide trước; mở hay chụm ngón
cái–trỏ–giữa thì phóng to, thu nhỏ.

- **Mô hình ghép:** vuốt theo LSTM, zoom theo rừng ngẫu nhiên.
- **Máy trạng thái có ngưỡng riêng cho từng họ cử chỉ:** vuốt cần độ tin 0,85 và 4/5 cửa sổ
  đồng ý; zoom cần 0,40 và 3/5.
- **Thử trực tiếp lần cuối** (01/11): 92 giây, 19 lệnh, mọi phím đều được gửi. Người dùng đánh
  giá "tạm ổn".

Trên 40 lời nhắc đã ghi, hệ thống nhận đúng khoảng **một nửa số cử chỉ**. Khi nói chuyện có
khua tay, nó phát nhầm **0,18 lệnh mỗi phút**. Nguyên nhân chính của phần còn lại là cách làm
cử chỉ khác người diễn IPN (mục 5.3), không phải lỗi đường ống.

`pytest -q`: **215 passed**.

---

## 2. Trạng thái các phase

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 8 | Đánh giá hai mức, bảy bảng khảo sát | ✅ xong; còn lần chạy cuối trên tập test, cố ý để sau cùng |
| 9 | Máy trạng thái kích hoạt | ✅ xong; mục "0,9–1,1 lệnh mỗi cử chỉ trên video val" chưa đạt (0,61), người dùng chấp nhận |
| 10 | Demo hoàn chỉnh và đo đạc | 🟡 đã chọn cấu hình cuối, đã thử slide thật; còn đo tốc độ đủ, độ trễ thủ công, video demo |
| 11 | Dữ liệu tự quay (tuỳ chọn) | ⬜ chưa bật; quyết định chờ người dùng trong `results/phase6/live_check.md` |
| 12 | Tái lập và bàn giao | 🟡 đã bắt đầu: `run_all.py`, ghim phiên bản, README |

---

## 3. Phase 8 — Chấm hai mức và bảy bảng khảo sát

### 3.1. Hai mức chấm

- **Mức cửa sổ:** mỗi cửa sổ 1,2 giây được gán đúng lớp hay không. Đây là con số quen thuộc của
  học máy (macro-F1), nhưng người dùng không cảm nhận trực tiếp được nó.
- **Mức sự kiện:** cả hệ thống chạy trên 27 video val liên tục của IPN (60 phút, 108 cử chỉ),
  qua **đúng đường ống của demo**. Lệnh đúng là lệnh đúng loại, phát từ lúc cử chỉ bắt đầu tới
  1 giây sau khi kết thúc. Từ đó đo F1 sự kiện, số lệnh trên một cử chỉ, và lệnh nhầm mỗi phút.

### 3.2. Bảy bảng khảo sát

`scripts/run_experiments.py` chạy **46 thí nghiệm**. Mỗi thí nghiệm đổi đúng một yếu tố: cách
chuẩn hoá, độ dài cửa sổ, cách chia tập, bộ đặc trưng, seed, k-fold theo người, biến thể LSTM.

- Mỗi thí nghiệm lưu thành **bản ghi** dự đoán.
- Chỉnh máy trạng thái thì dựng lại bảng trong khoảng 1 phút, thay vì học lại 170 phút.
- Bản ghi được "băm" theo cấu hình. Đổi hằng số ảnh hưởng tới kết quả thì bản ghi tự hết hạn;
  hằng số của máy trạng thái và màn hình thì không.

### 3.3. Kết luận đứng vững

Các kết luận này đứng qua cả bốn lần dựng bảng (`run_01`–`run_04`):

- **LSTM hơn rừng ngẫu nhiên một cách chắc chắn:** +0,116 macro-F1 trung bình năm seed. Ở mức
  sự kiện với cấu hình cuối: +0,323.
- **Chia ngẫu nhiên theo cửa sổ thổi phồng macro-F1 thêm 0,10–0,15,** nhiều hơn cả khoảng cách
  giữa LSTM và rừng. Vì vậy dự án luôn chia theo người.
- **Rừng ngẫu nhiên cần gốc toạ độ ở cổ tay frame đầu** và cửa sổ 1,2 giây.
- **Vòng cải tiến thành công:** thêm góc khớp ngón tay làm ô nhầm lớn nhất (`none` → `swipe_left`)
  giảm từ 366 xuống 190 cửa sổ.

### 3.4. Bài học về độ tin của con số

Qua máy trạng thái, chênh lệch dưới khoảng 0,1 F1 sự kiện trong **một seed** thường lật chiều
khi đổi cấu hình kích hoạt. Ví dụ, quota `none` tự nhiên từng cho +0,108 (`run_02`), rồi chỉ còn
+0,012 (`run_03`). Chỉ những kết luận có năm seed, năm fold người hay chênh lệch lớn mới đáng
tin.

---

## 4. Phase 9 — Máy trạng thái: từ nhãn thành lệnh

Mô hình trả lời "cửa sổ vừa rồi giống cử chỉ gì", mỗi 0,2 giây một lần. Một cú vuốt vì vậy
sinh ra cả chục nhãn liên tiếp, có lúc nhấp nháy. Máy trạng thái (`src/activation.py`) trả lời
câu hỏi khác: **có nên phát lệnh bây giờ không**.

| Trạng thái | Nghĩa |
|---|---|
| `IDLE` | chưa thấy tay |
| `READY` | thấy tay, đang chờ |
| `CANDIDATE` | một cửa sổ đủ tin vừa mở ứng viên; đang gom phiếu |
| `COOLDOWN` | vừa phát lệnh, nghỉ 1,2 giây |

- **Ngưỡng tin cậy:** phải đủ tin mới mở được ứng viên.
- **Đồng thuận:** cần đủ số cửa sổ đồng ý trong 5 cửa sổ. Một cửa sổ đủ tin mà nói khác đi thì
  huỷ ứng viên.
- **Nghỉ sau lệnh:** tránh phát trùng.
- **Hạ tay để huỷ:** mất tay thì quên hết.

Phase 9 còn có `evaluate.py --events fsm`, `sweep_activation.py` (quét ngưỡng), và đánh đổi của
`MIN_PRESENCE`: nâng từ 0,7 lên 1,0 mất 3 trong 54 cú vuốt mà lệnh nhầm chỉ giảm 3%, nên giữ 0,7
(`results/phase9/tradeoff.md`).

**Mục chưa đạt:** "0,9–1,1 lệnh mỗi cử chỉ trên video val". Với cấu hình cuối, mô hình ghép đạt
0,61, phần thiếu là cử chỉ bị sót. Người dùng chấp nhận và để Phase 10 chọn cấu hình bằng số đo
trên webcam.

---

## 5. Phase 10 — Demo hoàn chỉnh và đo trên webcam

### 5.1. Đã xây dựng

- **`demo.py`:**
  - phát phím thật qua `pyautogui`, bấm `c` để bật, mặc định tắt;
  - trang trợ giúp `?` tóm tắt cách làm cử chỉ;
  - cửa sổ demo luôn nằm trên cùng;
  - log ghi mọi dự đoán, trạng thái, lệnh, phím đã gửi, kèm điểm mốc thô để phân tích lại.
- **`bench.py`:**
  - `speed` đo FPS và phân rã thời gian từng khâu;
  - `record` ghi phiên theo kịch bản, có lời nhắc cử chỉ trên màn hình;
  - `analyze` chấm **mọi cấu hình từ một lần ghi**: nhầm mỗi phút gộp theo thời lượng, thêm cột
    "nhầm mỗi phút có tay", độ trễ đo trên video val.
- **Màn hình luyện tập** (`--show-features`, phím 3 và 4): hiện độ duỗi nhẫn và út so với hộp của
  IPN (≈ 0,4–0,7).

### 5.2. Dữ liệu đã ghi

| Phiên | Thời lượng | Ghi chú |
|---|---|---|
| `gestures_01`, `gestures_02` | 2 × 2,4 phút | 40 lời nhắc, 10 mỗi lớp |
| `talking_01`, `talking_02` | 10,9 phút | nói chuyện có khua tay; camera thấy tay 23% thời gian |
| `reading_01`, `typing_01` | 2 × 0,5 phút | camera không thấy tay; người dùng quyết định không ghi lại |
| `live_final`, `live_final2` | 32 giây, 92 giây | hai lần thử slide thật, 01/11 |

### 5.3. Bốn phát hiện về cách làm cử chỉ

1. **Nhẫn và út duỗi khi zoom.** Độ duỗi 1,4–2,1, trong khi người diễn IPN gập hai ngón này
   (≈ 0,5). LSTM vì thế thiếu tự tin.
2. **Lấy đà ngược chiều trước khi vuốt.** Đoạn kéo tay ngược lại cũng là một cú vuốt, và mô hình
   nhận đúng chiều của nó với độ tin 1,00, nên phát lệnh ngược.
3. **Cử chỉ đến muộn:** tay thường vào khung ở giây thứ 2–4 của lời nhắc 4 giây.
4. **Đổi chiều quá nhanh:** mỗi lệnh chiếm khoảng 1,8 giây (gom phiếu cộng thời gian nghỉ),
   trong khi người dùng đổi chiều zoom mỗi khoảng 1,3 giây.

Tài liệu và màn hình trợ giúp đã bổ sung: không lấy đà ngược chiều, giơ tay khoảng 1 giây rồi
mới làm, giữ yên khoảng 1 giây sau cú zoom, các cử chỉ cách nhau khoảng 2 giây.

### 5.4. Các quyết định của người dùng

| Ngày | Quyết định | Lý do chính |
|---|---|---|
| 25/10 | Giữ `IPN_FLIP_X = 1` | vuốt sang trái của người dùng ra `swipe_left` |
| 26/10 | LSTM của demo đổi sang `train_lstm/run_08` | học thêm zoom với dáng ngón khác; hết báo vuốt khi tay chụm đứng yên |
| 26/10 | Không ghi lại phiên đọc và gõ phím | lúc đó camera không thấy tay |
| 26/10 | Ngưỡng 0,85 · 4/5 | vuốt ngược chiều giảm từ 5/20 xuống 2/20; nhầm khi nói chuyện từ 0,64 xuống 0,18 mỗi phút |
| 01/11 | Mô hình ghép, zoom 0,40 · 3/5, phím `+` / `−` | lần thử slide thật: 0/12 cú zoom thành lệnh, trong khi rừng gán đúng cả 12 cú, chỉ thang độ tin thấp hơn |
| 02/11 | Vuốt trái → slide sau, vuốt phải → slide trước | như lật trang trên màn hình cảm ứng; SPEC gốc ngược lại |

### 5.5. Cấu hình cuối, đo trên dữ liệu đã ghi

| | Kết quả |
|---|---|
| Vuốt (20 lời nhắc) | 11 đúng, 2 ngược chiều, 7 sót |
| Zoom (20 lời nhắc) | 10 đúng, 4 ngược chiều, 6 sót (trước khi đổi: 4 đúng) |
| Lệnh mỗi lời nhắc | 1,00 |
| Nhầm khi nói chuyện | 0,18 lệnh mỗi phút (0,79 mỗi phút có tay trong khung) |
| Video val của IPN | F1 sự kiện 0,561; 0,85 lệnh nhầm mỗi phút; độ trễ trung vị 0,76 giây |
| Tốc độ (một lần đo, ánh sáng tối, luật và rừng) | khoảng 30 FPS; xử lý khoảng 16 ms mỗi khung hình, MediaPipe chiếm 76–79% |

**Hai lần thử slide thật** (01/11):

- Lần đầu, cấu hình cũ: 4/4 lệnh vuốt, **0/12** cú zoom.
- Chạy lại đúng phiên đó với cấu hình mới: 6/12 cú zoom thành lệnh, cả 6 đúng chiều. Phần lớn
  số còn lại bị thời gian nghỉ che, vì người dùng đổi chiều quá nhanh.
- Lần hai, cấu hình mới: 92 giây, 19 lệnh (8 vuốt, 11 zoom), mọi phím đều được gửi.

### 5.6. Định nghĩa hoàn thành của Phase 10

| Mục | Trạng thái |
|---|---|
| Vuốt trái thì slide đi đúng chiều | ✅ người dùng đã thử trên PowerPoint, đánh giá tạm ổn. Từ 02/11 "đúng chiều" là vuốt trái sang slide sau, theo lựa chọn của người dùng |
| Một cử chỉ, đúng một lệnh | ⚠️ rất ít khi phát trùng, nhưng recall chỉ khoảng 52% |
| Tay ra khỏi khung rồi vào lại không sinh lệnh lạ | ✅ 66 lần vào lại trong các phiên đã ghi |
| Phân rã thời gian xấp xỉ 100% | ✅ 99,5% |
| Kích hoạt nhầm tăng dần theo độ khó kịch bản | ⚠️ chỉ theo nghĩa yếu: 0 = 0 < 0,18, vì lúc đọc và gõ phím camera không thấy tay |
| Số lệnh trên một cử chỉ 0,9–1,1 | ✅ trên webcam 1,00, có bù trừ giữa cử chỉ sót và lệnh sai loại |
| Đo lại lần hai cho kết quả gần giống | ❌ chưa làm |
| Video demo hoàn chỉnh | ❌ chưa làm |

---

## 6. Phase 12 — Bàn giao: đã bắt đầu

- **`scripts/run_all.py`:** dựng lại toàn bộ đường ống bằng một lệnh, 16 bước, bước nào đã có
  đầu ra thì bỏ qua. Không bao giờ chạy tập test.
- **Mô hình của demo dựng lại được.**
  - Đường dẫn cố định `results/phase10/lstm_model.pt`, trùng từng byte với `run_08`.
  - Công thức học nằm trong config (`DEPLOY_ZOOM_STYLE_P`, `DEPLOY_STATIC_SHARE`).
  - Trước đây config trỏ vào số thư mục `run_08`; dựng lại từ đầu thì số đó đổi.
- **`requirements.txt` ghim đúng phiên bản** của môi trường đã cho mọi con số. Bỏ `pandas` (không
  dùng), thêm `scipy` và `joblib`.
- **README:**
  - liên kết `docs/gestures.md` ở đầu;
  - đoạn chiến lược dữ liệu: chỉ IPN, kèm giới hạn;
  - cấu hình máy đo tốc độ.
- **Hai lần chặn được cái bẫy học lại 170 phút:** hằng số mới trong config suýt làm hết hạn cả 46
  bản ghi. Nay có kiểm thử giữ.
- **Hai bản nháp chờ người dùng xác nhận:** `results/phase5/misfires.md`,
  `results/phase6/live_check.md`.

---

## 7. Hạn chế và việc còn lại

### 7.1. Hệ thống còn yếu ở đâu

- **Khoảng một nửa cử chỉ bị sót ở lần làm đầu.** Vuốt thường sót vì hất nhanh, hoặc tay vào
  khung muộn. Zoom sót vì nhẫn và út duỗi.
- **Zoom có thể phát ngược chiều** khi tay chuẩn bị (mở trước khi chụm): 4/20 lời nhắc.
- **Ngưỡng zoom chọn trên ít dữ liệu** (40 lời nhắc, 12 cú zoom), và chính dữ liệu đó dùng để
  chấm, nên con số có phần lạc quan.
- **Trên IPN, mô hình ghép không phải lựa chọn tốt nhất ở mọi phép đo.**
  - Học lại theo công thức chính, trung bình năm seed, LSTM một mình hơn mô hình ghép 0,105 F1
    sự kiện.
  - Với mô hình đang dùng (`run_08`) thì ngược lại: 0,561 so với 0,507.
  - Lý do chọn mô hình ghép đến từ webcam: nó phát được zoom trên tay người dùng mà không nhầm
    thêm.
- **Trong PowerPoint, khi đang phóng to,** mũi tên có thể di chuyển trong slide thay vì chuyển
  slide.

### 7.2. Việc của người dùng

1. Đo tốc độ đủ bốn mô hình ở hai mức ánh sáng, rồi đo lại lần hai:
   `python scripts/bench.py speed --light bright`, rồi `--light dim`.
2. Đo độ trễ thủ công, 10 lần mỗi cử chỉ.
3. Quay video demo, kèm ghi chú các trường hợp hệ thống làm sai.
4. Quyết định có bật Phase 11 không (`results/phase6/live_check.md`); duyệt `docs/gestures.md`.
5. **Cuối cùng, đúng một lần:**
   - chạy `evaluate.py --split test --final`;
   - làm phép thử tái lập: xoá môi trường, cài lại theo README, chạy `python scripts/run_all.py`.

---

## Phụ lục — Dành cho người làm kỹ thuật

### Số liệu lấy từ đâu

| Nội dung | Thư mục |
|---|---|
| Bảy bảng Phase 8, cấu hình cuối | `results/phase8/experiments/run_04` |
| Bảng so sánh bốn mô hình | `results/model_comparison.md` (`results/phase8/evaluate/run_13`–`run_16`) |
| Bảng đánh đổi trên webcam và video val | `results/phase10/analyze/run_07` |
| Tốc độ | `results/phase10/speed/run_01` |
| Phiên webcam | `results/phase10/sessions/`, `results/phase10/live_final*.csv` |
| Lý do và cái giá của cấu hình cuối | `results/phase10/final_config.md` |

### Lệnh chính

```
python scripts/demo.py --model hybrid --log <file.csv>
python scripts/demo.py --model hybrid --show-features
python scripts/bench.py record gestures
python scripts/bench.py analyze
python scripts/run_all.py --list
```

### Hằng số của cấu hình cuối (`src/config.py`)

| Hằng số | Giá trị |
|---|---|
| `CONF_FIRE`, `K_OF_N`, `CONF_HOLD` (vuốt) | 0,85; (4, 5); 0,55 |
| `FSM_ZOOM_FIRE`, `FSM_ZOOM_K` (zoom) | 0,40; 3 |
| `COOLDOWN_SEC`, `MIN_PRESENCE` | 1,2 giây; 0,7 |
| `LSTM_MODEL_PATH` | `results/phase10/lstm_model.pt` |
| `CTRL_HOTKEYS` | vuốt trái → mũi tên phải (slide sau), vuốt phải → mũi tên trái (slide trước); zoom `+` / `−` |
