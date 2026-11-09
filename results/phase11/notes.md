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

**Bảng 4, hàng thứ ba.** Dùng mô hình demo. So hai tập bằng trung bình bốn lớp cử chỉ.

| Mô hình demo | Tập | F1 cử chỉ | Recall cử chỉ | macro-F1 5 lớp |
|---|---|---|---|---|
| Rừng | val IPN | 0,307 | 0,541 | 0,436 |
| Rừng | real_test | 0,552 | 0,537 | 0,442 |
| LSTM | val IPN | 0,375 | 0,761 | 0,489 |
| LSTM | real_test | 0,755 | 0,660 | 0,604 |

macro-F1 5 lớp trên real_test tính cả F1 = 0 của none, nên không dùng để so.
