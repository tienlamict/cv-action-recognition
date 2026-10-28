# Cấu hình cuối — Phase 10

> **Người dùng chọn ngày 2026-10-26** từ bảng đánh đổi `results/phase10/analyze/run_06`
> (SPEC Phase 10, bước 5–6). Claude ghi lại lý do và cái giá.
>
> Số liệu:
>
> - 40 lời nhắc webcam: `gestures_01`, `gestures_02`;
> - 10,9 phút nói chuyện có khua tay: `talking_01`, `talking_02`;
> - 27 video val của IPN.
>
> Diễn giải chi tiết: `results/phase10/notes.md` mục 4–5.

## Cấu hình

| Thành phần | Giá trị | Hằng số trong `src/config.py` |
|---|---|---|
| Mô hình | LSTM `results/phase10/lstm_model.pt`: bản sao từng byte của `train_lstm/run_08`, checkpoint epoch 87 (sha256 `81c858110be97a04…`). Công thức: công thức chính cộng đổi dáng ngón phụ 0,5 và bàn tay đứng yên 0,1 | `LSTM_MODEL_PATH`, `DEPLOY_ZOOM_STYLE_P`, `DEPLOY_STATIC_SHARE`; chạy `demo.py --model lstm`. `run_all.py` dựng lại file này |
| Cửa sổ | 1,2 s = 18 bước ở 15 Hz; dự đoán mỗi 0,2 s | `WIN_SEC`, `HZ`, `STRIDE_SEC` |
| Ngưỡng có tay | 70% số bước của cửa sổ | `MIN_PRESENCE` |
| Mở ứng viên lệnh | độ tin ≥ **0,85** | `CONF_FIRE` |
| Đồng thuận | **4 trong 5** cửa sổ; cửa sổ đồng ý cần độ tin ≥ 0,55 | `K_OF_N`, `CONF_HOLD` |
| Nghỉ sau lệnh | 1,2 s | `COOLDOWN_SEC` |
| Phím | ← / → / Ctrl + / Ctrl −; phím `c` bật, mặc định tắt | `CTRL_HOTKEYS`, `CTRL_TOGGLE_KEY` |

SPEC khởi đầu ở 0,75 với 3/5; Phase 9 giữ mức đó và để Phase 10 chọn. Cấu hình máy trạng thái
không nằm trong băm của bản ghi Phase 8, nên đổi nó không làm bản ghi nào hết hạn.

## Bảng chọn (`analyze/run_06`)

| Mô hình, `CONF_FIRE`, k/n | F1 sự kiện val | Nhầm/phút val | Nhầm/phút talking (có tay) | Recall vuốt | Lời nhắc vuốt phát ngược chiều trước | Recall zoom | Lệnh/lời nhắc | Trễ val |
|---|---|---|---|---|---|---|---|---|
| lstm 0,60 · 2/5 | 0,389 | 4,33 | 1,37 (5,93) | 0,65 | 6/20 | 0,75 | 1,68 | 0,43 s |
| lstm 0,75 · 3/5 | 0,554 | 1,63 | 0,64 (2,77) | 0,60 | 5/20 | 0,40 | 1,02 | 0,62 s |
| **lstm 0,85 · 4/5** | **0,600** | **0,77** | **0,18 (0,79)** | **0,55** | **2/20** | **0,20** | **0,62** | **0,76 s** |
| hybrid 0,75 · 3/5 | 0,586 | 0,73 | 0,18 (0,79) | 0,60 | 5/20 | 0,10 | 0,72 | 0,63 s |

## Vì sao chọn

**Với điều khiển trình chiếu, lệnh sai tệ hơn lệnh sót.** Cử chỉ bị sót thì người dùng làm
lại. Lệnh sai thì đổi slide ngoài ý muốn giữa lúc trình bày. So với 0,75 · 3/5:

1. **Recall vuốt gần như giữ nguyên:** 0,55 so với 0,60 — một lời nhắc trên 20.
2. **Lệnh vuốt ngược chiều giảm từ 5/20 xuống 2/20.**
   - Nguyên nhân là lấy đà: người dùng kéo tay ngược chiều trước khi hất. Đoạn lấy đà là một
     cú vuốt ngắn mà mô hình gọi đúng chiều với độ tin 1,00, nên không ngưỡng tin cậy nào lọc
     được.
   - Đoạn đó thường chỉ dài khoảng 3 cửa sổ: đủ cho 3/5, không đủ cho 4/5.
   - Mô hình ghép lấy vuốt từ cùng LSTM, nên ở 3/5 nó cũng mắc 5/20.
3. **Lệnh nhầm khi nói chuyện giảm khoảng 3,5 lần:** 0,18 so với 0,64 mỗi phút; 0,79 so với
   2,77 mỗi phút có tay trong khung.
4. **Trên IPN val cũng tốt hơn:** F1 sự kiện 0,600 so với 0,554; lệnh nhầm 0,77 so với 1,63
   mỗi phút. Đây là F1 sự kiện cao nhất trong mọi hàng của bảng.

## Cái giá

- **Zoom trên bàn tay người dùng chỉ nhận 4/20.** Người dùng làm zoom với nhẫn và út duỗi
  (độ duỗi 1,2–2,1, IPN ≈ 0,5). Ở mọi cấu hình, zoom chỉ đáng tin khi gập hai ngón đó như IPN.
  Màn hình luyện tập (`demo.py --show-features`, phím 3 và 4) đo điều này.
- **Trễ thêm khoảng 0,15 s:** trung vị 0,76 s, tính từ khoảnh khắc chính của cử chỉ tới lúc
  phát lệnh, đo trên video val. Chưa gồm thời gian xử lý của camera và MediaPipe.
- **Không đạt điều kiện "số lệnh trên một cử chỉ 0,9–1,1" của DoD.** Ta có 0,62 lệnh mỗi
  lời nhắc.
  - Cấu hình 0,75 · 3/5 cho 1,02, nhưng chỉ vì cử chỉ bị sót (recall 0,50) và lệnh sai loại
    bù cho nhau.
  - Ở cấu hình này, lệnh phát trùng chỉ 0,05 mỗi cử chỉ. Phần thiếu là cử chỉ bị sót, không
    phải lệnh thừa.
  - Báo đúng như vậy, không nới điều kiện.

## Đi kèm cấu hình: cách làm cử chỉ

Hai lỗi lớn nhất là lỗi cách làm, không ngưỡng nào sửa hết:

- **Không lấy đà ngược chiều trước khi hất.** Đã thêm vào màn hình trợ giúp (phím `?`) và
  `docs/gestures.md`, mục `swipe_right`.
- **Zoom: gập nhẫn và út.** Luyện bằng `demo.py --show-features` tới khi `ring_ext` và
  `pinky_ext` xanh.

## Hệ quả cho các bảng khác

- **`results/model_comparison`:** cột mức sự kiện của cả bốn mô hình được tính lại với cấu hình
  này (`evaluate.py --events fsm`). Hàng `lstm` và `hybrid` giờ dùng `run_08`.
- **Bảng Phase 8** dựng lại với cấu hình này ngày 2026-10-26, không học lại:
  `results/phase8/experiments/run_03`. Kết luận nào đứng, kết luận nào đổi:
  `results/phase10/notes.md` mục 7.
- **Lần chạy cuối trên tập test** (`evaluate.py --split test --final`, đúng một lần) dùng cấu
  hình này. Người dùng quyết định lúc chạy.
