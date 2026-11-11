# Phase 11 — ghi chú kết quả

> Dữ liệu: real_tune = p01/2026-11-06, p01/thu2, p02/2026-11-07, p03/2026-11-08 (850 cửa sổ sau
> lọc: none 518, swipe_left 82, swipe_right 46, zoom_in 107, zoom_out 97); real_test =
> p01/p01-test, chia trước khi mở (`split_self.py`).
>
> Hai bên, mỗi bên 3 hạt (`SELF_SEEDS` = 42, 43, 44), cùng script và công thức của mô hình demo
> (`train_self.py`):
> - **cũ**: IPN thuần. Hạt 42 chính là mô hình demo.
> - **mới**: IPN cộng real_tune.

## 1. Cũ và mới trên val IPN — 2026-11-09, trước khi chấm real_test

Nguồn: `compare_self/run_02` (11 038 cửa sổ, 27 video val). Trung bình 3 hạt [nhỏ nhất–lớn nhất].

| | cũ | mới |
|---|---|---|
| Rừng, macro-F1 cửa sổ | 0,432 [0,430–0,436] | 0,433 [0,433–0,434] |
| LSTM, macro-F1 cửa sổ | 0,512 [0,488–0,559] | 0,567 [0,532–0,600] |
| Ghép, macro-F1 cửa sổ | 0,493 [0,445–0,537] | 0,512 [0,486–0,529] |
| Ghép + máy trạng thái, F1 lệnh | 0,512 [0,444–0,561] | 0,528 [0,506–0,545] |
| Lệnh nhầm mỗi phút | 1,23 [0,85–1,93] | 0,94 [0,78–1,10] |

- **Dữ liệu tự quay không làm hại IPN.** Mức lệnh và mô hình ghép nhỉnh hơn một chút, nhưng
  nhỏ hơn độ lệch chuẩn giữa các hạt (F1 lệnh: chênh +0,016, độ lệch chuẩn bên cũ 0,061):
  **không đủ bằng chứng để kết luận** là tốt hơn.
- **LSTM tốt lên rõ hơn:** +0,054, lớn hơn độ lệch chuẩn của cả hai bên (0,041 và 0,034). Phần
  tăng nằm ở zoom (zoom_in 0,49 → 0,57; zoom_out 0,39 → 0,50). Mô hình ghép lấy zoom từ rừng,
  nên không hưởng phần này.
- **Lần tụt thấy trước đây** (chỉ hạt 42: ghép 0,537 → 0,486, F1 lệnh 0,561 → 0,506) **là do
  hạt.** Mô hình demo là hạt tốt nhất của bên cũ. Hai hạt cũ còn lại: F1 lệnh 0,444 và 0,532.

**Chốt trước khi chấm real_test (luật 13):**
- real_test báo trung bình và khoảng của mỗi bên. Không dùng real_test để chọn hạt.
- **Cách đo.** real_test có 60 lần quay, 195 cửa sổ: swipe_left 45, swipe_right 52, zoom_in
  50, zoom_out 48. 51 cửa sổ bị bỏ vì mơ hồ, và **không có cửa sổ none nào**, vì lần quay ngắn
  và chỉ có cử chỉ.
  - Mức cửa sổ: so với val bằng trung bình F1 và trung bình recall của bốn lớp cử chỉ
    (`gesture_f1`, `gesture_recall`). macro-F1 năm lớp ở đây tính cả F1 = 0 của none, nên
    không so được.
  - Mức lệnh: lệnh đầu tiên của từng lần quay (đúng / nhầm / sót), đo như quay và đo thêm
    1 giây giữ yên.
- Nếu cần một mô hình mỗi bên, chọn theo F1 lệnh trên val IPN: **cũ s42** (mô hình demo,
  0,561) và **mới s43** (0,545). Cả hai cũng đứng đầu bên mình ở macro-F1 cửa sổ của mô hình
  ghép (0,537 và 0,529).

Cùng lúc, val chạy lại với hai cột mới (`compare_self/run_03`). Mọi con số cũ không đổi.
Trung bình bốn lớp cử chỉ của mô hình ghép trên val: F1 0,377 (cũ) và 0,399 (mới); recall
0,668 và 0,636.

## 2. Chấm real_test — một lần duy nhất, 2026-11-09 22:45

Nguồn: `compare_self/run_04`. `results/TEST_USED.log` có đúng một dòng. 60 lần quay, 195 cửa
sổ, không có none. Trung bình 3 hạt [nhỏ nhất–lớn nhất].

**Mức cửa sổ:**

| | cũ | mới |
|---|---|---|
| Ghép, F1 cử chỉ | 0,916 [0,870–0,945] | 0,971 [0,957–0,982] |
| Ghép, recall cử chỉ | 0,872 [0,810–0,910] | 0,958 [0,933–0,979] |
| LSTM, F1 cử chỉ | 0,793 [0,668–0,956] | 0,969 [0,957–0,982] |
| Rừng, F1 cử chỉ | 0,558 [0,552–0,564] | 0,609 [0,608–0,611] |

**Mức lệnh:** mô hình ghép cộng máy trạng thái. Đếm số lần quay có lệnh đầu tiên đúng, trên 60.

| | cũ | mới |
|---|---|---|
| Như quay | 33,7 [31–37] | 36,7 [35–39] |
| Thêm 1 s giữ yên | 42,3 [39–46] | 46,0 [44–49] |
| F1 lệnh, thêm 1 s giữ yên | 0,821 [0,780–0,868] | 0,859 [0,838–0,891] |

Theo lớp, thêm 1 s giữ yên, số đúng trên 15:

| Lớp | cũ | mới |
|---|---|---|
| swipe_left | 2,0 [0–5] | 6,7 [5–8] |
| swipe_right | 12,0 [10–14] | 10,3 [8–12] |
| zoom_in | 14,7 | 15,0 |
| zoom_out | 13,7 | 14,0 |

- Lệnh đầu tiên sai lớp: nhiều nhất 1 lần mỗi mô hình, đều ở lần quay zoom_out. Các lần hỏng
  còn lại là **sót**, tức không phát lệnh nào.
- **Cặp đã chốt trước khi chấm** (mô hình demo cũ s42 và mới s43):

  | | demo | mới s43 |
  |---|---|---|
  | Như quay | 31 | 35 |
  | Thêm 1 s giữ yên | 39 | 44 |
  | swipe_left, thêm 1 s giữ yên | 0 | 7 |
  | F1 lệnh, thêm 1 s giữ yên | 0,780 | 0,838 |

**Vì sao.** Mọi điểm dưới đây đọc từ manifest của run_04 (ma trận nhầm lẫn, lệnh của từng lần
quay). Không chấm lại.

1. **Mức cửa sổ không thấy tụt so với IPN.** Recall cử chỉ của mô hình ghép bên cũ còn cao
   hơn: 0,668 trên val, 0,872 ở đây.
   - Lần quay sạch, mỗi lần một cử chỉ, cửa sổ mơ hồ đã bị bỏ.
   - Không có none, nên cũng không có báo nhầm.

   **Chỗ tụt là mức lệnh:** như quay, 20–28 trên 60 lần quay không phát lệnh nào; thêm 1 s
   giữ yên còn 10–20.
2. **swipe_left là nút thắt.** LSTM của mô hình demo xếp 25 trên 45 cửa sổ swipe_left vào none,
   nên không lần nào phát lệnh. LSTM bên mới đúng 40–44 trên 45 cửa sổ.
3. **Cửa sổ đã đúng mà vẫn sót nửa số lần vuốt trái.** Luật kích hoạt của vuốt là độ tin
   ≥ 0,85 ở 4 trên 5 lần dự đoán.
   - Đoạn cử chỉ ngắn, trung vị 0,8 s.
   - Ở hai mô hình đã chốt, lệnh vuốt, nếu có, phát 0,1–0,8 s sau khi đoạn kết thúc.

   *Giả thuyết:* chỉ khoảng ba lần dự đoán thấy trọn cú vuốt, nên khó đạt 4 trên 5. Phải kiểm
   trên real_tune, không phải real_test.
4. **Rừng đứng riêng nhầm swipe_right của p01 thành swipe_left (13–30 trên 52 cửa sổ) hoặc
   none.** Mô hình ghép không bị ảnh hưởng, vì lấy vuốt từ LSTM.
5. **Giới hạn.**
   - real_test chỉ có p01. p01 cũng có trong real_tune, ở buổi khác. Kết quả nói về chính
     người dùng, không nói về người lạ.
   - 15 lần quay mỗi lớp, nên 1 lần quay bằng 6,7 điểm phần trăm.
   - Mọi chỉnh sửa từ đây không còn tập chấm độc lập. Muốn có con số không thiên lệch thì
     phải quay một buổi chấm mới.

**Biểu đồ** (2026-11-10, `plot_self/run_01`, chỉ đọc run_03 và run_04):
- `cua_so_va_lenh.png`: theo lớp, cửa sổ nhận đúng và lần quay ra lệnh đúng;
- `lenh_p01_test.png`: số lần quay ra lệnh đúng;
- `val_ipn.png`: val IPN.

**Đường học của mới s43:** `train_self/run_07` (`training_curves.png`, `history.csv`).
- Lần học đầu không lưu lịch sử từng epoch, nên học lại bằng `--trial`. Trọng số trùng
  từng số với `seeds/lstm_self_s43.pt`: cùng epoch 56 trên 76, cùng mã băm dữ liệu.
- Epoch 56 được chọn: trung bình 10 epoch của macro-F1 kiểm định là 0,535, điểm thô 0,568.
  Mô hình demo chọn epoch 87, với 0,528 và 0,489.

## 3. Còn cải thiện được ở đâu — đo trên các phiên Phase 10, 2026-11-10

Nguồn: `analyze/run_01`, chạy `bench.py analyze --models hybrid --self-seed 42 43 44
--swipe-grid`. Đếm lệnh nhầm theo lớp bằng một script tạm, chạy cùng các hàm của bench.py.

Dữ liệu: các phiên ghi của Phase 10 trên tay p01 (tháng 10).
- `gestures_01`, `gestures_02`: 40 lời nhắc, mỗi lớp 10.
- `talking_01`, `talking_02`: 10,9 phút nói chuyện, 23% thời gian thấy tay.

Đây là dữ liệu chỉnh của Phase 10, không có trong tập học của mô hình mới, và không đụng
real_test. Người dùng làm cử chỉ tự nhiên, có động tác chuẩn bị.

**Luật hiện tại** (vuốt 0,85 · 4/5, zoom 0,40 · 3/5), trên 40 lời nhắc:

| | demo | mới s43 |
|---|---|---|
| Vuốt bắt được (trên 20) | 11 | 13 |
| Zoom bắt được (trên 20) | 10 | 10 |
| Lệnh nhầm | 19 | 17 |
| Trong đó: zoom ngược chiều | 7 | 10 |
| Lệnh khi nói chuyện, 10,9 phút | 2 zoom_out | 2 zoom_out |

- **Lỗi lớn nhất là zoom ngược chiều.** Động tác chuẩn bị (chụm ngón trước khi mở) được nhận
  là zoom ngược lại. Luật zoom lỏng (0,40 · 3/5) phát lệnh ngay lúc đó, rồi 1,2 giây im lặng
  chặn cú zoom thật.
- **Nới luật vuốt không lợi** (mới s43, zoom giữ nguyên luật):
  - 3/5: vuốt 12/20, không hơn mà còn thêm 4 lệnh vuốt ngược chiều (do lấy đà);
  - 2/5: vuốt 17/20, nhưng 9 lệnh vuốt ngược chiều.

  Đánh đổi của Phase 10 vẫn đúng với mô hình mới.
- **Siết luật zoom** (0,85 · 4/5): hết zoom nhầm, nhưng zoom chỉ còn 4/20.
- **Đối chiếu với p01-test.** Ở đó các lần quay sạch, vì công cụ quay đã báo và cho quay lại
  khi động tác chuẩn bị mạnh. Zoom đúng 14–15/15 và gần như không có lệnh nhầm. Vậy phần lớn
  lỗi còn lại đến từ cách bắt đầu cử chỉ (chuẩn bị, lấy đà), không phải từ việc nhận cử chỉ.

**Hướng cải thiện.** Khi hai lệnh ngược chiều của cùng một họ tranh nhau trong khoảng
ngắn, chọn chuyển động mạnh hơn thay vì chọn lệnh đến trước. Không cần học lại. Người dùng
duyệt làm; kết quả ở mục 4.

## 4. Trọng tài chiều ngược — 2026-11-10

**Cách làm** (`src/activation.py`, `FSM_ARBITRATE_SEC`):
- Ứng viên đủ phiếu thì không phát ngay mà chờ.
- Trong lúc chờ, lớp ngược chiều cùng họ được mở và bỏ phiếu như ứng viên thường. Nó đủ
  phiếu thì so độ mạnh, và chuyển động mạnh hơn thắng.
- Độ mạnh là `windows.window_strengths`: chuyển động mạnh nhất theo chiều của lớp trên các
  cửa sổ đã đồng ý. Hàm này dùng chung phép tính với `core_signal`. Đã kiểm 200 clip IPN:
  cửa sổ cử chỉ và nhãn trùng `windows.npz` từng byte.
- Mặc định `FSM_ARBITRATE_SEC = 0`, tức phát ngay như Phase 10.

**Đo trên dữ liệu chỉnh**, gồm các phiên Phase 10 và val IPN; không đụng real_test. Nguồn:
`analyze/run_02` (`bench.py analyze --self-seed 42 43 44 --swipe-grid --arbitrate 0 0.2
0.4 0.6`), và một script tạm chấm lại các phiên gestures.

Một lưu ý về cách chấm. Bạn thường làm cử chỉ gần cuối khung lời nhắc 4 giây, nên chờ thêm
đẩy lệnh đúng ra khỏi vùng khớp (cuối lời nhắc + 1 s) và bị đếm là sót. Vì vậy bảng dưới
nới vùng khớp thêm 0,6 s cho MỌI mức chờ: so độ đúng, không so độ chậm.

Luật hiện tại (vuốt 0,85 · 4/5, zoom 0,40 · 3/5), 40 lời nhắc:

| Mô hình, chờ | Vuốt bắt được | Zoom bắt được | Lệnh nhầm | Ngược chiều |
|---|---|---|---|---|
| mới s43, 0 s | 13/20 | 10/20 | 17 | 10 |
| mới s43, 0,4 s | 13/20 | 11/20 | 13 | 6 |
| mới s43, 0,6 s | 13/20 | 12/20 | 11 | 3 |
| demo, 0 s | 13/20 | 11/20 | 16 | 9 |
| demo, 0,4 s | 11/20 | 12/20 | 16 | 3 |
| demo, 0,6 s | 11/20 | 11/20 | 17 | 2 |

Val IPN và nói chuyện, vùng khớp chuẩn:

| Mô hình, chờ | F1 lệnh val | Lệnh nhầm/phút val | Trễ trung vị val | Nhầm/phút nói chuyện |
|---|---|---|---|---|
| mới s43, 0 s | 0,545 | 0,78 | 0,76 s | 0,18 |
| mới s43, 0,4 s | 0,554 | 0,77 | 1,15 s | 0,18 |
| mới s43, 0,6 s | 0,559 | 0,73 | 1,37 s | 0,18 |
| demo, 0 s | 0,561 | 0,85 | 0,76 s | 0,18 |
| demo, 0,4 s | 0,575 | 0,80 | 1,16 s | 0,18 |

- **Với mới s43, trọng tài cắt lệnh ngược chiều từ 10 xuống 3, tổng lệnh nhầm từ 17 xuống
  11.** Zoom bắt thêm 2, vuốt không đổi. Val IPN cũng nhỉnh hơn (F1 0,545 → 0,559, nhầm
  0,78 → 0,73/phút), và nói chuyện không thêm lệnh nhầm.
- **Cái giá là trễ:** trung vị từ khoảnh khắc chính tới lệnh tăng từ 0,76 s lên 1,15 s (chờ
  0,4) và 1,37 s (chờ 0,6).
- **Trọng tài ít khi phải phân xử thật.** Ở chờ 0,4 s, mới s43 vào trạng thái chờ 37 lần;
  33 lần hết giờ mà không có lớp ngược chiều nào đủ phiếu, chỉ 3 lần phải so độ mạnh.
  - Một phần zoom ngược chiều không phải do động tác chuẩn bị thắng trước, mà do cú zoom
    thật không đủ phiếu. Đó là giới hạn nhận dạng: zoom vẫn chỉ bắt được 10–12/20.
- **Nới luật vuốt kèm trọng tài:** với mới s43 không lợi (0,85 · 3/5, chờ 0,6: vuốt 13/20,
  lệnh nhầm 17). Với demo có lợi (3/5, chờ 0,4: vuốt 16/20, lệnh nhầm 15, ngược chiều 4),
  nhưng nhầm khi nói chuyện tăng gấp đôi (0,37/phút).
- **Giới hạn:** 40 lời nhắc; chênh lệch 2–6 lệnh. Chọn mức chờ cần thử trên webcam vì độ trễ
  là cảm giác, rồi đo lại trên một buổi chấm mới.

**F1 mức lệnh với cấu hình hiện tại** (chờ 0,4 s). Nguồn: `analyze/run_03`, cộng một
script tạm tính precision và recall bằng `events.summarize_events`.

| Nơi đo | mới s43 | demo |
|---|---|---|
| Val IPN, 27 video | P 0,562, R 0,546, **F1 0,554** | F1 0,575 |
| Phiên cử chỉ Phase 10, vùng khớp nới 0,4 s | **F1 0,545** | 0,557 |
| Phiên cử chỉ Phase 10, vùng khớp chuẩn | F1 0,442 | 0,506 |

F1 từng lớp của mới s43 trên val: swipe_left 0,58, swipe_right 0,67, zoom_in 0,44, zoom_out
0,54.

**Người dùng chọn mặc định chờ 0,4 s** (2026-11-10, `FSM_ARBITRATE_SEC`). Mức này lấy phần
lớn lợi ích (lệnh ngược chiều 10 → 6) với trễ ít hơn mức 0,6 (1,15 s so với 1,37 s). Lần
chấm real_test (mục 2) và các bảng Phase 8–10 đo trước thay đổi này.

**Bảng 4, hàng thứ ba.** Dùng mô hình demo. So hai tập bằng trung bình bốn lớp cử chỉ.

| Mô hình demo | Tập | F1 cử chỉ | Recall cử chỉ | macro-F1 5 lớp |
|---|---|---|---|---|
| Rừng | val IPN | 0,307 | 0,541 | 0,436 |
| Rừng | real_test | 0,552 | 0,537 | 0,442 |
| LSTM | val IPN | 0,375 | 0,761 | 0,489 |
| LSTM | real_test | 0,755 | 0,660 | 0,604 |

macro-F1 5 lớp trên real_test tính cả F1 = 0 của none, nên không dùng để so.
