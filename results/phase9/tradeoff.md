# Phase 9 — Đánh đổi của `MIN_PRESENCE`

> Claude viết ngày 2026-10-25. Số liệu lấy từ `results/phase9/sweep_activation/run_02`, tái lập
> bằng `python scripts/sweep_activation.py`.
>
> - Dữ liệu: 27 video val, 60,1 phút, 108 cử chỉ (27 mỗi lớp).
> - Mô hình: các mô hình đã lưu, không học lại.
> - Máy trạng thái: tham số trong `config.py` — `CONF_FIRE` 0,75, `K_OF_N` 3/5, `COOLDOWN_SEC`
>   1,2 giây.
> - Chỉ ngưỡng **lúc chạy** đổi. Mô hình học với `MIN_PRESENCE` = 0,7, nên cửa sổ dưới ngưỡng đó
>   là thứ chúng chưa từng thấy.

**Điều SPEC dự đoán.** Nâng `MIN_PRESENCE` để chống kích hoạt nhầm thì đồng thời bỏ sót đúng
những cú vuốt nhanh, vì cửa sổ vuốt nhanh là cửa sổ hay mất tay nhất.

**Cách đo.**

- Video val chạy một lần qua đúng `WindowStream` của demo, với ngưỡng thấp nhất (0,5). Mỗi mô
  hình chấm mọi cửa sổ một lần.
- Mỗi ngưỡng cao hơn chỉ chặn bớt các lần dự đoán (`events.gate_presence`). Bộ đệm chỉ dùng
  ngưỡng để chặn, không đổi nội dung cửa sổ hay nhịp dự đoán, nên cách này trùng việc chạy lại
  video với ngưỡng mới.
- Có hai bằng chứng cho điều đó:
  - kiểm thử `test_nang_min_presence_tren_dong_thoi_gian_trung_chay_lai_video`;
  - trên dữ liệu thật, hàng 0,7 trùng từng chữ số Bảng 1 của `results/phase8/experiments/run_02`,
    vốn dựng thẳng ở 0,7.

## 1. Cửa sổ nào hay mất tay

Phần cửa sổ val bị chặn nếu nâng ngưỡng (`presence_by_class`):

| Lớp | Số cửa sổ | Trung vị tỉ lệ có tay | Bị chặn ở 0,8 | ở 0,9 | ở 1,0 |
|---|---|---|---|---|---|
| `none` | 10 650 | 1,00 | 4,8% | 7,0% | 8,1% |
| `swipe_left` | 104 | 1,00 | 0% | 0% | 0% |
| `swipe_right` | 96 | 1,00 | 2,1% | 3,1% | 3,1% |
| `zoom_in` | 94 | 1,00 | 2,1% | 2,1% | 2,1% |
| `zoom_out` | 94 | 1,00 | 1,1% | 1,1% | 2,1% |

- **Trên IPN, cửa sổ vuốt không hay mất tay hơn cửa sổ khác.** Phần bị chặn của chúng (0–3,1%)
  còn thấp hơn của `none` (4,8–8,1%).
- **Bảng này không thấy hết.** `windows.npz` chỉ chứa cửa sổ có tỉ lệ có tay từ 0,7 trở lên. Cửa
  sổ vuốt mất tay nặng hơn thế đã bị loại từ Phase 4.

## 2. Hệ thống ở từng ngưỡng

`presence_sweep`. "Có cửa sổ" là phần các lần dự đoán có cửa sổ hợp lệ. Recall tính trên 54 cú
vuốt và 54 cú zoom.

**LSTM:**

| `MIN_PRESENCE` | Có cửa sổ | F1 sự kiện | Recall vuốt | Recall zoom | Lệnh nhầm / phút | … lúc `D0X` | … lúc chỉ trỏ |
|---|---|---|---|---|---|---|---|
| 0,5 | 72,3% | 0,551 | 0,759 | 0,648 | 1,53 | 0,40 | 0,65 |
| 0,6 | 70,7% | 0,555 | 0,759 | 0,648 | 1,50 | 0,40 | 0,63 |
| **0,7** | **68,7%** | **0,559** | **0,759** | **0,648** | **1,46** | **0,37** | **0,63** |
| 0,8 | 65,5% | 0,558 | 0,741 | 0,648 | 1,43 | 0,33 | 0,63 |
| 0,9 | 63,7% | 0,558 | 0,741 | 0,648 | 1,43 | 0,32 | 0,63 |
| 1,0 | 61,8% | 0,549 | 0,704 | 0,648 | 1,41 | 0,33 | 0,63 |

**Mô hình ghép (mô hình của demo):**

| `MIN_PRESENCE` | F1 sự kiện | Recall vuốt | Recall zoom | Lệnh nhầm / phút |
|---|---|---|---|---|
| 0,5 | 0,484 | 0,778 | 0,352 | 1,38 |
| 0,6 | 0,486 | 0,778 | 0,352 | 1,36 |
| **0,7** | **0,490** | **0,778** | **0,352** | **1,33** |
| 0,8 | 0,488 | 0,759 | 0,352 | 1,30 |
| 0,9 | 0,486 | 0,759 | 0,333 | 1,26 |
| 1,0 | 0,475 | 0,722 | 0,333 | 1,25 |

Rừng ngẫu nhiên gần như không đổi: F1 sự kiện 0,395–0,405, lệnh nhầm 0,48–0,50 mỗi phút.

- **Đánh đổi có thật và đúng chiều SPEC nói, nhưng rất nhỏ trên IPN.** Nâng từ 0,7 lên 1,0:
  - LSTM mất 3 trong 54 cú vuốt (recall vuốt 0,759 → 0,704), zoom không đổi;
  - đổi lại, lệnh nhầm chỉ giảm 3% (1,46 → 1,41 mỗi phút);
  - F1 sự kiện giảm nhẹ (0,559 → 0,549).
- **Hạ dưới 0,7 không được gì.** Recall không tăng, còn lệnh nhầm tăng nhẹ (1,53 ở 0,5). Các
  cửa sổ thêm vào là thứ mô hình chưa từng thấy lúc học.
- **Giả thuyết C của Phase 8** cho rằng báo nhầm `D0X` là lúc tay vào hoặc ra khỏi khung hình
  (`results/phase8/notes.md` mục 3.3). Khi nâng ngưỡng:
  - lệnh nhầm lúc `D0X` giảm 17% (0,40 → 0,33);
  - lệnh nhầm lúc chỉ trỏ gần như không đổi (0,65 → 0,63).
  
  Đó là đúng chiều giả thuyết dự đoán, nhưng phần giảm chỉ 0,07 lệnh mỗi phút. Phần lớn báo nhầm
  `D0X` còn lại không do cửa sổ thiếu tay.
- **Vì sao đánh đổi nhỏ:** người diễn IPN giữ tay trong khung. Trung vị tỉ lệ có tay là 1,0 ở mọi
  lớp, và 69% thời gian có cửa sổ hợp lệ. Trên webcam laptop, tay đi vào đi ra ở mép dưới khung
  hình liên tục. Đánh đổi thật sẽ lộ ra khi đo kích hoạt nhầm ở ba kịch bản của Phase 10.

**Kết luận: giữ `MIN_PRESENCE` = 0,7.** Trên IPN, mọi ngưỡng khác hoặc không được gì, hoặc mất cú
vuốt mà gần như không bớt báo nhầm. Ngưỡng này cũng quyết định thao tác huỷ của máy trạng thái:
tay phải vắng quá 30% cửa sổ (khoảng 0,4 giây) thì máy mới về `IDLE`. Nên đo lại trên webcam ở
Phase 10 trước khi chốt.
