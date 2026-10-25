# Phase 9 — Ghi chú logic kích hoạt

> Claude viết ngày 2026-10-25. Số liệu lấy từ:
>
> - `results/phase8/experiments/run_02`: bảy bảng Phase 8 dựng lại với máy trạng thái
>   (`EVENT_FILTER = "fsm"`), từ đúng các bản ghi của `run_01` — không học lại;
> - `results/phase8/evaluate/run_05`–`run_08`: `evaluate.py --events fsm`, bốn mô hình đã lưu;
> - `results/phase9/sweep_activation/run_02`: đánh đổi `MIN_PRESENCE`, thang độ tin của từng mô
>   hình, lưới tham số máy trạng thái.
>
> Tái lập bằng các lệnh Phase 9 ghi trong README. Tập test chưa bị chạm.
>
> **Kiểm chứng:** `evaluate.py` chạy thẳng trên video và Bảng 1 dựng từ bản ghi cho cùng từng chữ
> số. Hàng `MIN_PRESENCE` 0,7 của bảng đánh đổi cũng trùng, dù nó dựng dòng thời gian ở ngưỡng
> 0,5 rồi chặn bớt.

## 1. Máy trạng thái

`src/activation.py`, lớp `ActivationFSM` với một phương thức `update(label, confidence,
presence, ts)`. Bốn trạng thái và năm cơ chế đúng như SPEC; tham số lấy từ `config.py`:
`CONF_FIRE` 0,75, `CONF_HOLD` 0,55, `K_OF_N` 3/5, `COOLDOWN_SEC` 1,2 giây.

- **Đồng thuận.** Một cửa sổ cử chỉ có độ tin ≥ `CONF_FIRE` mở ứng viên. Mỗi cửa sổ sau đó
  thuộc một trong ba loại:
  - *đồng ý*: cùng lớp, độ tin ≥ `CONF_HOLD`;
  - *phản đối*: lớp khác, kể cả `none`, độ tin ≥ `CONF_HOLD`. Đồng thuận thất bại ngay;
  - *do dự*: chỉ chiếm một chỗ trong `n`.

  Lệnh phát khi đủ `k` phiếu đồng ý trong `n` cửa sổ kể từ lúc mở. Đếm phiếu trên cửa sổ trượt
  theo nghĩa đen thì chuỗi nhấp nháy vuốt, none, vuốt, none, vuốt phát lệnh — đúng điều kiểm thử
  bắt buộc của SPEC cấm. Lý do đầy đủ ở SPEC Phase 9, ghi chú 2026-10-25.
- **Mất tay** là khi bộ đệm không trả cửa sổ nào:
  - tay vắng quá 30% cửa sổ, khoảng 0,4 giây, thì máy về `IDLE` và quên hết, kể cả cooldown;
  - khi đưa tay vào, phải đủ 1,2 giây mới có cửa sổ, nên cửa sổ chuyển tiếp tự bị chặn.
- **Kiểm thử** (`tests/test_activation.py`, 11 kiểm thử):
  - năm kiểm thử bắt buộc, mỗi cái kèm một phép đối chứng cho thấy nó phân biệt được (ví dụ bỏ
    cooldown thì hai cụm thành hai lệnh);
  - cửa sổ do dự, cử chỉ khác mở ngay ứng viên mới, log chuyển trạng thái, tham số sai;
  - phép mô phỏng `MIN_PRESENCE`.
- **Demo.** `demo.py` nối máy trạng thái cho cả bốn mô hình.
  - Màn hình hiện trạng thái và lệnh vừa phát.
  - `--log FILE` ghi trạng thái và lệnh vào từng dòng, và mọi lần chuyển trạng thái vào
    `FILE_fsm.csv`.
  - Đã chạy thử trên một video val (`--source`, `--no-display`): log chuyển trạng thái đi đúng
    vòng `IDLE → READY → CANDIDATE → COOLDOWN → READY`, có cả "mất tay" và "none phản đối".

## 2. Bảng 1 — trước và sau máy trạng thái

`edge` là bộ lọc của Phase 8 (`run_01`): mỗi chuỗi dự đoán liền nhau là một lệnh. `fsm` là máy
trạng thái (`run_02`).

| Mô hình | F1 sự kiện | Precision | Recall | Lệnh / cử chỉ | Lệnh nhầm / phút |
|---|---|---|---|---|---|
| Luật | 0,094 → 0,130 | 0,050 → 0,081 | 0,870 → 0,333 | 1,06 → 0,37 | 29,8 → 6,8 |
| Rừng ngẫu nhiên | 0,211 → **0,405** | 0,121 → 0,539 | 0,815 → 0,324 | 0,94 → 0,32 | 10,6 → **0,50** |
| LSTM | 0,334 → **0,559** | 0,204 → 0,463 | 0,935 → 0,704 | 1,20 → 0,77 | 6,6 → **1,46** |
| Ghép | 0,308 → **0,490** | 0,188 → 0,433 | 0,852 → 0,565 | 1,03 → 0,61 | 6,6 → **1,33** |

- **Máy trạng thái làm đúng việc của nó.**
  - Lệnh nhầm giảm 4,4–21 lần, precision tăng 1,6–4,5 lần.
  - F1 sự kiện tăng 1,4–1,9 lần ở mọi mô hình.
  - Lệnh thừa cho cùng một cử chỉ gần như hết: 0,12 lệnh mỗi phút với LSTM (mục 4).
- **Giá phải trả là recall.** LSTM bỏ sót 30% cử chỉ (trước là 6%), mô hình ghép 43%, rừng 68%.
  Mục 5 giải thích vì sao.
- **Xếp hạng giữ nguyên:** LSTM > ghép > rừng > luật.
- **Rừng giờ ít lệnh nhầm nhất** (0,50 mỗi phút, đúng mốc 0,5 của SPEC), nhưng chỉ bắt được một
  phần ba số cử chỉ.
- Với vùng khớp ban đầu của SPEC (±1 giây quanh lúc kết thúc), F1 sự kiện là 0,061 / 0,208 /
  0,324 / 0,265.

## 3. Từng lớp

Mức sự kiện qua máy trạng thái (`evaluate/run_06`–`run_08`):

| Lớp | Rừng: recall | LSTM: recall | LSTM: precision | Ghép: recall | Ghép: precision |
|---|---|---|---|---|---|
| `swipe_left` | 0,26 | 0,85 | 0,31 | 0,85 | 0,31 |
| `swipe_right` | 0,33 | 0,67 | 0,51 | 0,70 | 0,53 |
| `zoom_in` | 0,26 | 0,81 | 0,56 | 0,26 | 0,47 |
| `zoom_out` | 0,44 | 0,48 | 0,81 | 0,44 | 0,80 |

- **Hơn nửa số lệnh nhầm của LSTM là `swipe_left`:** 51 trong 74 lệnh `swipe_left` là nhầm.
  Đây đúng là ô `none` → `swipe_left`, ô lớn nhất từ Phase 6 (`results/phase8/notes.md` mục 3.1).
- **Lớp yếu nhất của LSTM là `zoom_out`:** chỉ bắt được 48%.
- **Mô hình ghép vuốt như LSTM nhưng zoom như rừng:** chỉ bắt được 26% `zoom_in` và 44%
  `zoom_out`. Nguyên nhân ở mục 5.

## 4. Lệnh nhầm còn lại, theo nhãn gốc

Lệnh nhầm mỗi phút qua máy trạng thái (`run_02/table1_false_by_src`):

| Lúc phát lệnh | Luật | Rừng | LSTM | Ghép |
|---|---|---|---|---|
| `B0A` chỉ một ngón | 2,58 | 0,08 | 0,25 | 0,28 |
| `B0B` chỉ hai ngón | 2,16 | 0,12 | 0,38 | 0,35 |
| `D0X` không cử chỉ | 0,93 | 0,08 | 0,37 | 0,37 |
| lúc một cử chỉ khác loại đang diễn ra | 0,53 | 0,15 | 0,25 | 0,18 |
| lệnh thừa cho cùng cử chỉ | 0,07 | 0 | 0,12 | 0,08 |
| các loại `none` khác | 0,55 | 0,07 | 0,10 | 0,07 |
| **Tổng** | **6,8** | **0,50** | **1,46** | **1,33** |

- **Tay chỉ trỏ và `D0X` vẫn là hai phần ba số lệnh nhầm**: 1,0 trên 1,46 lệnh mỗi phút với LSTM.
  Đồng thuận không dẹp được chúng, vì mô hình tự tin và đồng ý liên tục trong cả một đoạn tay
  chỉ trỏ lướt ngang.
- **Phần đồng thuận và cooldown dẹp được thì đã dẹp gần hết.** Lệnh thừa cho cùng cử chỉ còn
  0,12 mỗi phút; các cử chỉ ngón khác của IPN còn 0,10.

## 5. Số lệnh trên một cử chỉ, và thang độ tin của từng mô hình

**Mục này của Định nghĩa hoàn thành chưa đạt với tham số khởi đầu.** Số lệnh trên một cử chỉ
trên video val: luật 0,37, rừng 0,32, LSTM 0,77, ghép 0,61 — yêu cầu 0,9–1,1.

**Nguyên nhân là bỏ sót, không phải lệnh thừa.** Cần đủ 3 cửa sổ tự tin liền nhau, mà mô hình
không luôn cho được 3 cửa sổ như vậy trong một cú vuốt ngắn.

**Thang độ tin của các mô hình khác nhau** (`confidence_by_class`, cửa sổ cử chỉ val được đoán
đúng):

| | LSTM | Rừng |
|---|---|---|
| Trung vị độ tin | 0,999–1,000 | 0,69–0,88 |
| Phần đạt `CONF_FIRE` 0,75 | 87–97% | 37–69% |
| Phần đạt 0,85 | 85–96% | 7–56% |

- Riêng `zoom_in` của rừng chỉ 37% cửa sổ đúng đạt 0,75 và 7% đạt 0,85.
- Mô hình ghép lấy zoom từ rừng, nên với một `CONF_FIRE` chung, zoom của nó hiếm khi mở được ứng
  viên.

**Lưới tham số** (`fsm_grid`, `MIN_PRESENCE` 0,7). Ba hàng của bảng đánh đổi Phase 10:

| `CONF_FIRE`, `K_OF_N` | LSTM: F1 | LSTM: recall | LSTM: lệnh / cử chỉ | LSTM: nhầm / phút | Ghép: F1 | Ghép: lệnh / cử chỉ | Ghép: nhầm / phút |
|---|---|---|---|---|---|---|---|
| 0,60, 2/5 | 0,476 | 0,815 | **0,963** | 2,90 | 0,414 | 0,741 | 2,66 |
| 0,75, 3/5 (hiện tại) | 0,559 | 0,704 | 0,769 | 1,46 | 0,490 | 0,611 | 1,33 |
| 0,85, 4/5 | **0,625** | 0,648 | 0,676 | **0,77** | 0,528 | 0,481 | 0,57 |

- **Chỉ LSTM với đồng thuận 2/5 vào được khoảng 0,9–1,1:** 0,963 với `CONF_FIRE` 0,6 và 0,926
  với 0,75.
  - Đổi lại, lệnh nhầm lên 2,6–2,9 mỗi phút, gấp đôi cấu hình hiện tại.
  - Mô hình ghép, rừng và luật không vào được ở bất kỳ ô nào của lưới.
- **Trên val của IPN, không cấu hình nào vừa đạt 0,9 lệnh mỗi cử chỉ vừa dưới 0,5 lệnh nhầm mỗi
  phút.** Đây là đánh đổi precision–recall thật, và chọn điểm nào là quyết định của người dùng
  (mục 8).
- **Trên người khác thì gần đạt hơn.** Qua năm fold người của Bảng 7, với tham số hiện tại, LSTM
  đạt 0,90 ± 0,05 lệnh mỗi cử chỉ. Nhóm val chính thức khó hơn trung bình.

## 6. Kết luận nào của Phase 8 đổi khi có máy trạng thái

`run_02` so với `run_01`, cùng bản ghi. Một điều cần biết trước khi đọc: máy trạng thái biến
khác biệt nhỏ về độ tin thành có hay không có cả một lệnh. Vì vậy độ lệch chuẩn F1 sự kiện của
LSTM giữa năm seed tăng từ 0,023 lên 0,058, và một hàng đơn seed phải đọc thận trọng hơn.

- **Vẫn đứng:**
  - LSTM hơn rừng (+0,173 F1 sự kiện, 3 lần độ lệch chuẩn);
  - gốc toạ độ frame đầu là điều kiện sống còn của rừng (F1 sự kiện 0,405 so với 0,276);
  - cửa sổ 1,2 giây tốt nhất cho rừng (0,405, so với 0,260 và 0,289);
  - 11 điểm kém 21 điểm (−0,092).
- **Đổi:**
  - **Ghép so với LSTM:** −0,066 F1 sự kiện, nay **không đủ bằng chứng**. Qua năm fold người,
    LSTM 0,654 ± 0,034 và ghép 0,603 ± 0,019; ghép ít lệnh nhầm hơn (0,89 so với 1,33 mỗi phút).
  - **Góc khớp (Bảng 5):** rừng có góc khớp giảm một nửa lệnh nhầm (0,27 so với 0,50 mỗi phút),
    nhưng F1 sự kiện không tăng (0,390 so với 0,405). Qua máy trạng thái, chỗ nghẽn của rừng là
    recall, mà góc khớp không giúp recall.
  - **Quota `none` theo tỉ lệ tự nhiên:** LSTM +0,108 F1 sự kiện (1,9 lần độ lệch chuẩn), rừng
    +0,036. Ở mức `edge` nó "không đủ bằng chứng". Nhiều khả năng vì máy trạng thái dẹp được
    lệnh nhầm ngắn nhưng không dẹp được báo nhầm kéo dài của tay chỉ trỏ, mà quota tự nhiên
    giảm đúng loại đó (`results/phase8/notes.md` mục 3.1). Mới một seed: cần năm seed trước khi
    dùng.
  - **Cửa sổ 1,6 giây với LSTM:** 0,592 so với 0,559 ở 1,2 giây — không đủ bằng chứng. Ở mức
    `edge`, 1,2 giây hơn hẳn.

## 7. Đánh đổi `MIN_PRESENCE`

Chi tiết ở `results/phase9/tradeoff.md`.

- **Đánh đổi có thật và đúng chiều SPEC nói, nhưng nhỏ trên IPN.** Nâng từ 0,7 lên 1,0: LSTM mất
  3 trong 54 cú vuốt, mà lệnh nhầm chỉ giảm 3%. Hạ dưới 0,7 không được gì.
- **Giữ 0,7, và đo lại trên webcam ở Phase 10.** Người diễn IPN giữ tay trong khung; tay trên
  webcam laptop thì đi vào đi ra ở mép dưới khung hình.

## 8. Định nghĩa hoàn thành và các quyết định đang chờ

| Mục | Trạng thái |
|---|---|
| Năm kiểm thử bắt buộc xanh | **đạt:** `tests/test_activation.py`, cùng 6 kiểm thử thêm; 188 kiểm thử của project xanh |
| `evaluate.py --events` chạy được với máy trạng thái, cho F1 sự kiện, số lệnh trên một cử chỉ, tỉ lệ kích hoạt nhầm | **đạt:** `--events fsm`, `evaluate/run_05`–`run_08`; `evaluate.py` không phải sửa |
| Số lệnh trên một cử chỉ trên video val trong khoảng 0,9–1,1 | **chưa đạt** với tham số khởi đầu (LSTM 0,77, ghép 0,61). Chỉ đạt với LSTM khi đồng thuận 2/5 (mục 5) |
| Bảng 1 của Phase 8 có cột F1 mức sự kiện cho cả ba mô hình | **đạt:** `run_02/table1_models`, cả bốn mô hình, qua máy trạng thái |
| Đánh đổi `MIN_PRESENCE` ghi vào `results/phase9/tradeoff.md` | **đạt** |

**Quyết định của người dùng:**

1. **Điểm làm việc của máy trạng thái**, để đóng mục "0,9–1,1". *Người dùng chọn (a) ngày
   2026-10-25 và coi Phase 9 là xong.*
   - **(a)** Giữ 0,75 với 3/5, chấp nhận mục này chưa đạt, và chọn cấu hình cuối ở Phase 10 bằng
     bảng đánh đổi có đo trên webcam — đúng thứ tự của SPEC.
   - **(b)** Đổi `K_OF_N` sang 2/5 và dùng LSTM cho demo: đạt 0,93 trên val, nhưng 2,65 lệnh nhầm
     mỗi phút, gấp đôi hiện tại.
2. **Zoom của mô hình ghép dưới một `CONF_FIRE` chung.** Thang độ tin của rừng thấp hơn LSTM
   (mục 5), nên zoom của mô hình ghép hiếm khi thành lệnh: recall zoom 0,35, so với 0,65 của
   LSTM. Có ba hướng:
   - ngưỡng riêng cho từng mô hình;
   - hiệu chuẩn xác suất của rừng trên train;
   - quay về LSTM cho demo.
   
   Hai hướng đầu đổi thiết kế một `CONF_FIRE` của SPEC.
3. **Quota `none` tự nhiên cho LSTM** (mục 6): chạy đủ năm seed để xác nhận +0,108 trước khi đổi
   cấu hình chính.
