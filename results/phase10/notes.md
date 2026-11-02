# Phase 10 — Ghi chú demo hoàn chỉnh và đo đạc

> Claude viết ngày 2026-10-26. Số liệu lấy từ:
>
> - `results/phase10/analyze/run_06`: bảng đánh đổi trên sáu phiên webcam và 27 video val;
>   `run_01`–`run_03` là các lần chấm trước, với LSTM `run_07` và cách gộp cũ (mục 3);
> - `results/phase10/sessions/`: `gestures_01` (trước luyện), `gestures_02` (sau luyện), mỗi
>   phiên 20 lời nhắc; `talking_01`, `talking_02`, `reading_01`, `typing_01`;
> - `results/phase10/zoom_practice*`: phiên luyện zoom bằng `demo.py --show-features`;
> - `results/phase7/probe_zooms/run_03`, `run_04`: thăm dò zoom trên video IPN với LSTM
>   `run_07` và `run_08`.
>
> Cấu hình cuối: `final_config.md` (người dùng chọn 2026-10-26, sửa 2026-11-01 sau lần thử slide
> thật, mục 7); bảng Phase 8 dựng lại ở `experiments/run_04`. Chưa xong: tốc độ đủ bốn
> mô hình × hai mức ánh sáng, thử điều khiển slide thật, độ trễ thủ công, video demo (mục 8).

## 1. LSTM của demo đổi sang `train_lstm/run_08` — người dùng chọn 2026-10-26

**Vấn đề trên bàn tay người dùng.** Người dùng làm zoom với ngón nhẫn và út duỗi: độ duỗi
1,5–1,7, so với ≈ 0,5 của IPN (nhẫn, út gập, `docs/gestures.md`). LSTM `run_07` học đúng
kiểu ngón của IPN, nên gặp kiểu zoom này thì:

- `gestures_01`, 10 lời nhắc zoom: `run_07` nhận **0/10** ở cả ba cấu hình (`analyze/run_03`);
- phiên luyện zoom (1,1 phút, chỉ làm zoom), ở 0,75 với 3/5: `run_07` phát 0 `zoom_in`,
  2 `zoom_out` và **4 lệnh vuốt nhầm** khi bàn tay chụm đứng yên.

**`run_08`** là lần khảo sát của Phase 7 (`--zoom-style-p 0.5 --static-share 0.1`). Nó học
thêm hai thứ: zoom mang dáng ngón phụ của bàn tay IPN khác, và bàn tay đứng yên là `none`.

| Trên cùng dữ liệu, 0,75 với 3/5 | `run_07` | `run_08` |
|---|---|---|
| `gestures_01`: zoom được nhận | 0/10 | 4/10 (8/10 ở 0,60 với 2/5) |
| `gestures_01`: vuốt được nhận | 7/10 | 6/10 |
| Phiên luyện zoom: `zoom_in` / `zoom_out` / vuốt nhầm | 0 / 2 / 4 | 5 / 5 / 0 |
| IPN, nhẫn và út duỗi thẳng tổng hợp: `zoom_in` / `zoom_out` còn được nhận (`probe_zooms/run_03`, `run_04`) | 10% / 35% | 95% / 95% |
| F1 sự kiện val | 0,559 | 0,554 |
| Lệnh nhầm mỗi phút val | 1,46 | 1,63 |

**Cái giá, Phase 7 đã đo** (mục 9.3 của `results/phase7/notes.md`). Ở mức cửa sổ trên val,
precision `zoom_out` giảm từ 0,46 xuống 0,10, và báo nhầm với tay chỉ trỏ tăng từ 3,5–5,9%
lên 10–12%. Khi đó Phase 7 bác `run_08`. Qua máy trạng thái, F1 sự kiện val gần như không đổi.
Trên webcam, cái giá hiện ra ở kịch bản nói chuyện (mục 4): lệnh nhầm đổi từ vuốt sang
`zoom_out`.

**Cách đổi.**

- `config.LSTM_MODEL_PATH` ban đầu trỏ thẳng vào `results/phase7/train_lstm/run_08/lstm_model.pt`.
- **Sửa 2026-10-28 (Phase 12):** số `run_NN` không tái lập được. Dựng lại từ đầu thì cùng lần
  học đó rơi vào số khác, và demo mất mô hình. Giờ:
  - `LSTM_MODEL_PATH` là đường dẫn cố định `results/phase10/lstm_model.pt`;
  - công thức nằm trong config: `DEPLOY_ZOOM_STYLE_P`, `DEPLOY_STATIC_SHARE`;
  - `run_all.py` chép lần khảo sát mới nhất đúng công thức đó, học trên đúng bộ cửa sổ hiện
    tại, sang `LSTM_MODEL_PATH`. Chưa có lần nào như vậy thì nó học trước.
  - File hiện tại trùng `run_08` từng byte, nên mọi bảng và bản ghi giữ nguyên.
- `train_lstm.py` ghi mô hình chính vào `PHASE7_LSTM_PATH` (vẫn là `run_07`).
- `save_checkpoint` bắt buộc đường dẫn, nên không lần huấn luyện nào ghi đè được mô hình của
  demo. `test_huan_luyen_khong_bao_gio_ghi_de_mo_hinh_cua_demo` giữ điều đó.
- Tham số huấn luyện mặc định không đổi (`AUG_ZOOM_STYLE_P = AUG_STATIC_SHARE = 0`), nên các
  bảng Phase 8 vẫn mô tả đúng công thức chính.
- Bản ghi "prod" của `lstm` và `hybrid` trong `results/phase8/records` sẽ tính lại ở lần chạy
  `run_experiments.py` tới, vì băm của mô hình đổi.
- `results/model_comparison` vẫn ghi `run_07` cho `lstm` và `hybrid`. Hai hàng này cập nhật
  bằng `evaluate.py --events fsm` khi chốt cấu hình cuối.

## 2. Luyện gập nhẫn và út theo IPN

Trong `demo.py --show-features`, bấm phím 3 (`zoom_in`) hoặc 4 (`zoom_out`). Màn hình có
thêm hai dòng `ring_ext` và `pinky_ext`: độ duỗi nhẫn và út của cửa sổ vừa rồi, so với hộp
25–75 của IPN. Xanh là gập như IPN; đỏ là còn duỗi.

| Hộp IPN (train) | `ring_ext` | `pinky_ext` |
|---|---|---|
| `zoom_in` | 0,53 [0,42; 0,71] | 0,50 [0,36; 0,66] |
| `zoom_out` | 0,51 [0,40; 0,71] | 0,51 [0,37; 0,66] |
| vuốt, để so (trung vị hai lớp) | 1,34–1,59 | 1,30–1,56 |

- **Định nghĩa:** "Duỗi ngón" của `docs/gestures.md` — khoảng cách đầu ngón → cổ tay chia
  khoảng cách gốc ngón → cổ tay. Mỗi cửa sổ lấy trung vị theo thời gian
  (`features.finger_extension`, `finger_extensions`). Độ duỗi không thuộc vector 15 chiều,
  nên không mô hình nào đổi.
- **Hộp IPN:** `plot_feature_boxplots.py` tính trên các cửa sổ train, ghi vào
  `results/phase4/ipn_feature_ranges.json` (hình: `results/phase4/boxplots/run_04/finger_extension.png`).
  Hộp của 15 đặc trưng cũ giữ nguyên từng chữ số.
- **Chỉ hai lớp zoom** có dòng này (`SHOW_FINGERS`). Với vuốt, IPN để ngón mở trong lúc
  hất, nên hiện độ duỗi chỉ làm người dùng phân tâm.

## 3. Cách chấm đổi: gộp theo thời lượng, thêm nhầm mỗi phút có tay

- **Gộp theo thời lượng.** Nhầm/phút của một kịch bản là tổng lệnh nhầm chia tổng số phút.
  Trước đây là trung bình các phiên, nên phiên 0,9 phút nặng ngang phiên 10 phút. Chỉ số của
  các phiên `gestures` cũng cộng dồn lời nhắc và lệnh.
- **Nhầm mỗi phút có tay** (`false_per_hand_min_*`). Lệnh chỉ phát được khi camera thấy tay.
  Phiên `talking_02` thấy tay 17% thời gian, `talking_01` thấy 89%. Vì vậy nhầm/phút của phiên
  phụ thuộc người dùng giơ tay bao lâu, không chỉ phụ thuộc mô hình. Hai cách đọc:
  - nhầm/phút thường là tần suất khi dùng thật với thói quen giơ tay của người dùng;
  - nhầm/phút có tay là trường hợp xấu nhất: tay luôn trong khung.
- **`reading` và `typing`:** mỗi phiên 0,5 phút, camera không thấy tay lần nào. Người dùng
  quyết định không ghi lại (2026-10-26): lúc đọc và gõ phím, tay nằm ngoài khung, nên hệ
  thống không thể phát nhầm. Con số 0 ở hai cột đó nghĩa là **chưa đo với tay trong khung**,
  không phải mô hình không bao giờ nhầm. Điều kiện "ba con số tăng dần theo độ khó" của DoD
  chỉ đạt theo nghĩa yếu: 0 = 0 < talking.

## 4. Bảng đánh đổi (`analyze/run_06`)

- `lstm` = `run_08`; `hybrid` = vuốt theo `run_08`, zoom theo rừng ngẫu nhiên.
- Phiên webcam:
  - `gestures_01` và `gestures_02`, gộp: 40 lời nhắc, 4,8 phút;
  - `talking`: 10,9 phút, thấy tay 23%.
- `analyze/run_05` là cùng bảng khi mới có `gestures_01`.

| Mô hình | `CONF_FIRE`, k/n | F1 sự kiện val | Nhầm/phút val | Nhầm/phút talking | Nhầm/phút có tay | Recall vuốt | Recall zoom | Lệnh/lời nhắc | Trễ val (s) |
|---|---|---|---|---|---|---|---|---|---|
| lstm | 0,60, 2/5 | 0,389 | 4,33 | 1,37 | 5,93 | 0,65 | 0,75 | 1,68 | 0,43 |
| lstm | 0,75, 3/5 | 0,554 | 1,63 | 0,64 | 2,77 | 0,60 | 0,40 | 1,02 | 0,62 |
| lstm | 0,85, 4/5 | 0,600 | 0,77 | 0,18 | 0,79 | 0,55 | 0,20 | 0,62 | 0,76 |
| hybrid | 0,60, 2/5 | 0,465 | 2,26 | 0,55 | 2,37 | 0,65 | 0,55 | 1,55 | 0,53 |
| hybrid | 0,75, 3/5 | 0,586 | 0,73 | 0,18 | 0,79 | 0,60 | 0,10 | 0,72 | 0,63 |
| hybrid | 0,85, 4/5 | 0,571 | 0,28 | 0,00 | 0,00 | 0,55 | 0,00 | 0,47 | 0,82 |
| rf | 0,75, 3/5 | 0,405 | 0,50 | 0,00 | 0,00 | 0,15 | 0,10 | 0,15 | 0,73 |

Lệnh nhầm trong hai phiên talking, theo lớp lệnh (cộng cả hai phiên, ở 0,75 với 3/5):

| | `swipe_left` | `swipe_right` | `zoom_in` | `zoom_out` |
|---|---|---|---|---|
| lstm `run_07` | 1 | 7 | 0 | 0 |
| lstm `run_08` | 0 | 2 | 0 | **5** |
| hybrid với `run_07` | 1 | 7 | 0 | 0 |
| hybrid với `run_08` | 0 | 2 | 0 | 0 |

Đọc bảng:

1. **`run_08` bớt vuốt nhầm khi nói chuyện**, từ 8 xuống 2 lệnh: nó học bàn tay đứng yên là
   `none`. Nhưng **LSTM một mình thêm 5 `zoom_out` nhầm**, đúng như Phase 7 dự đoán với tay
   chỉ trỏ. Mô hình ghép lấy zoom từ rừng nên không mắc lỗi này.
2. **Mô hình ghép tốt nhất trên IPN và khi nói chuyện** (F1 val 0,586, 0,18 nhầm/phút
   talking ở 0,75 với 3/5). Nhưng trên bàn tay người dùng nó chỉ nhận **2/20** zoom: độ tin
   của rừng hiếm khi tới 0,75.
3. **Recall trên bàn tay người dùng là nút thắt.** LSTM 0,60 với 2/5 nhận 70% cử chỉ, nhưng
   phát 1,68 lệnh mỗi lời nhắc và 5,9 lệnh nhầm mỗi phút có tay.
4. **Điều kiện "lệnh/lời nhắc 0,9–1,1" là chỉ số có thể đánh lừa.** LSTM 0,75 với 3/5 cho
   1,02 lệnh mỗi lời nhắc, nhưng recall chỉ 0,50: cử chỉ bị sót và lệnh sai loại bù cho nhau.
   Phần lớn lệnh sai loại có nguyên nhân ở mục 5.

## 5. Hai phiên `gestures`: lỗi nằm ở cách làm, không ở ngưỡng

Ở 0,75 với 3/5, LSTM nhận đúng 10/20 lời nhắc ở **cả hai** phiên:

| Phiên | `swipe_left` | `swipe_right` | `zoom_in` | `zoom_out` | Lệnh |
|---|---|---|---|---|---|
| `gestures_01` | 4/5 | 2/5 | 3/5 | 1/5 | 20 |
| `gestures_02` | 4/5 | 2/5 | 2/5 | 2/5 | 21 |

Ba nguyên nhân, đo trên điểm mốc đã ghi:

1. **Nhẫn và út vẫn duỗi ở `gestures_02`.** Ở cửa sổ có `pinch_delta` lớn nhất của mỗi lời
   nhắc zoom:
   - độ duỗi trung vị của `zoom_in` là 2,10 / 1,98 (nhẫn / út), so với 2,04 / 1,95 ở
     `gestures_01`. Không cú nào trong số 20 cú zoom của hai phiên nằm trong hộp IPN
     (≈ 0,4–0,7);
   - thước đo độc lập là góc khớp PIP (π là thẳng). Nhẫn của người dùng ≈ 2,75 rad ở cả hai
     phiên, của zoom IPN ≈ 1,7 rad.

   Luyện tập chưa chuyển vào lúc ghi.
2. **Lấy đà ngược chiều trước khi vuốt.** Để hất sang phải, người dùng kéo tay sang trái
   trước:
   - LSTM gọi đúng chiều từng đoạn. Ví dụ `gestures_01` lúc 24,0 s:
     `R R · L L L R R R R R`, với độ tin 1,00 ở cả đoạn lấy đà.
   - Ba cửa sổ `L` của đoạn lấy đà phát `swipe_left` trước. Cú hất thật (dx tới −1,7) rơi
     vào 1,2 s nghỉ của máy trạng thái nên bị bỏ.
   - 5/20 lời nhắc vuốt phát lệnh ngược chiều trước, 4 trong số đó là `swipe_right`.
   - Không ngưỡng nào sửa được lỗi này, vì đoạn lấy đà cũng cho độ tin 1,00.
3. **Cử chỉ đến muộn trong lời nhắc 4 giây.** Phần lớn lệnh đúng phát ở giây thứ 3–4,5 của
   lời nhắc. Cử chỉ làm sau giây thứ 5 bị tính là sót cộng một lệnh thừa.

Nguyên nhân 1 và 2 là lỗi cách làm. Tài liệu đã nói "dứt khoát, một chiều" nhưng chưa nói rõ
"không lấy đà".

## 6. Bảng Phase 8 dựng lại với 0,85 · 4/5 (`results/phase8/experiments/run_03`)

**Cách dựng.**

- Cùng 46 bản ghi với `run_02`: không học lại, 0,8 phút. Bộ cửa sổ dựng lại vẫn trùng
  `windows.npz` từng bit.
- Chỉ máy trạng thái đổi: 0,75 · 3/5 thành 0,85 · 4/5.
- Riêng Bảng 1 chấm mô hình đã lưu của demo, nên hàng LSTM và ghép đổi cả checkpoint
  (`run_07` thành `run_08`). Bảng 2–7 học lại theo công thức chính, nên vẫn tương đương
  `run_07`.
- **Một cái bẫy đã gỡ:** hai hằng số mới của màn hình luyện tập (`FINGER_TIPS`,
  `SHOW_FINGERS`) từng làm cả 46 bản ghi hết hạn. Chạy như vậy sẽ học lại hết, khoảng 170 phút.
  Cả hai giờ nằm ngoài băm (`src/experiments.py`, `_IRRELEVANT`), có kiểm thử
  `test_man_hinh_luyen_tap_khong_lam_ban_ghi_het_han` giữ. `FINGER_TIPS` suy ra từ `TIPS` và
  `FINGER_MCPS`, hai hằng số vẫn được băm, nên bỏ nó không che được thay đổi nào.

**F1 sự kiện, năm seed (Bảng 6) và năm fold người (Bảng 7):**

| | 0,75 · 3/5 (`run_02`) | 0,85 · 4/5 (`run_03`) |
|---|---|---|
| Rừng, năm seed | 0,413 ± 0,011 | 0,235 ± 0,024 |
| LSTM, năm seed | 0,587 ± 0,058 | **0,629 ± 0,051** |
| Ghép, năm seed | 0,521 ± 0,068 | 0,516 ± 0,056 |
| LSTM, k-fold: F1 / lệnh mỗi cử chỉ / nhầm mỗi phút | 0,654 / 0,90 / 1,33 | **0,722 ± 0,016 / 0,77 / 0,57** |
| Ghép, k-fold | 0,603 / 0,67 / 0,89 | 0,597 / 0,53 / 0,37 |

**Vẫn đứng:**

- **LSTM hơn rừng,** nay xa hơn: +0,394 F1 sự kiện (độ lệch chuẩn 0,051), trước là +0,173.
  Ngưỡng 0,85 làm recall của rừng sụp: độ tin của rừng hiếm khi tới mức đó.
- **Gốc toạ độ frame đầu là điều kiện sống còn của rừng:** 0,254 so với 0,176.
- **Cửa sổ 1,2 giây tốt nhất cho rừng:** 0,254, so với 0,016 và 0,145.
- **Bỏ nhóm đặc trưng có dấu làm rừng sập:** 0,070. **Biên khoảnh khắc chính 6 bước kém** với
  cả hai mô hình.
- **LSTM với gốc từng frame (+0,036) và cửa sổ 1,6 giây (+0,042):** vẫn "không đủ bằng chứng".

**Đổi:**

- **Ghép kém LSTM, nay đủ bằng chứng:** −0,113 F1 sự kiện, độ lệch chuẩn 0,056. Trước là
  −0,066, không đủ bằng chứng.
- **Ba ứng viên cải tiến của Phase 9 biến mất ở cấu hình cuối** (một seed, độ lệch chuẩn của
  LSTM 0,051):
  - quota `none` theo tỉ lệ tự nhiên: từ +0,108 xuống +0,012;
  - `hidden` 64: từ +0,062 xuống −0,021;
  - 11 điểm rút gọn: từ −0,092 thành −0,035, giờ không còn kém 21 điểm một cách đủ bằng chứng.
- **Hai phép tăng cường của `run_08` trên val:**
  - đổi dáng ngón phụ: −0,063, đủ bằng chứng là thiệt trên IPN;
  - bàn tay đứng yên: +0,007, không đủ bằng chứng.

  Đúng cái giá Phase 7 đã đo. LSTM của demo (`run_08`) đạt 0,600 ở Bảng 1, so với 0,625 của
  hàng cơ sở (≈ `run_07`). Chênh lệch nằm trong một độ lệch chuẩn: trên IPN, đổi sang `run_08`
  gần như không mất gì ở mức sự kiện.
- **Không tăng cường** (−0,066) và **gộp `mean`** (−0,088) giờ kém đủ bằng chứng; **gộp `max`**
  (−0,027) thì không còn.

**Bài học.** Qua máy trạng thái, kết luận một seed về chênh lệch dưới khoảng 0,1 F1 sự kiện
lật theo cấu hình kích hoạt. Chỉ kết luận năm seed (Bảng 6), năm fold (Bảng 7) hay chênh lệch
lớn mới đứng qua cả hai cấu hình. Vì vậy không nên đổi quota `none` hay `hidden` dựa trên
`run_02`.

**Một lưu ý về `inference_ms` của Bảng 1:**

- Hàng luật và rừng dùng lại số đo ngày 2026-10-25, vì bản ghi được dùng lại. Hàng LSTM và ghép
  đo lại hôm nay, lúc máy chậm hơn hẳn: đo lại ngay sau đó, rừng mất 8,8–9,5 ms mỗi cửa sổ, so
  với 2,97 ms trước kia.
- Cột này trong `run_03` vì vậy không so được giữa các hàng. Số tốc độ chính thức lấy từ
  `bench.py speed`, có ghi cấu hình máy.

## 7. Thử slide thật (2026-11-01): zoom không phát lệnh, đổi nguồn và ngưỡng của zoom

**Triệu chứng.** Người dùng chạy `demo.py --model lstm` ở 0,85 · 4/5: "nhận diện được hành động
nhưng nhiều lúc không phát lệnh; zoom hoàn toàn không phát lệnh". Log `results/phase10/live_final.csv`
(32 giây, chỉ giữ lần chạy cuối): 4 lệnh vuốt, cả 4 đã gửi phím; 12 cú zoom, **0 lệnh**.

**Nguyên nhân**, đo trên điểm mốc của phiên đó:

- **Động tác zoom sạch.** Khoảng cách cái–trỏ đi giữa 0,1 và 1,7 lòng bàn tay, chuyển trong
  0,2–0,4 giây rồi giữ yên hơn 1 giây. `pinch_delta` ±1,4–1,8, đúng vùng zoom của IPN.
- **Nhẫn và út vẫn duỗi:** độ duỗi 1,4–2,1, góc PIP của nhẫn 2,4–3,1 rad. IPN là ≈ 0,5 và
  ≈ 1,7 rad.
- **LSTM thiếu tự tin.** Với `zoom_out`, nhãn thường đúng nhưng độ tin 0,4–0,7 ở đầu chuỗi và chỉ
  vượt 0,85 ở 1–3 cửa sổ cuối. Máy trạng thái mở ứng viên ở 0,85 rồi cần 4/5, nên không đủ cửa
  sổ. Với `zoom_in`, nhiều cửa sổ bị đoán `none`.
- **Rừng gán đúng lớp cả 12/12 cú, chỉ thang độ tin thấp hơn:** `zoom_in` 0,33–0,56, `zoom_out`
  0,5–0,75. Đây chính là điều `results/phase9/notes.md` mục 8 đã nêu và để người dùng quyết.
- **Người dùng đổi chiều mỗi khoảng 1,3 giây,** nhanh hơn khoảng 1,8 giây mỗi lệnh (đồng thuận
  cộng thời gian nghỉ), nên cấu hình nào cũng mất một phần số cú ở phiên này.

**Phương án.** Vuốt theo LSTM, giữ 0,85 · 4/5; chỉ nguồn và ngưỡng của zoom đổi. Chạy lại trên
phiên trên, 40 lời nhắc, hai phiên talking và 27 video val:

| Zoom | Live có nghỉ / bỏ nghỉ | 20 lời nhắc zoom: đúng / ngược / sót | Lệnh/lời nhắc | Nhầm/phút talking | Val: F1, nhầm/phút |
|---|---|---|---|---|---|
| LSTM 0,85 · 4/5 (trước đây) | 0/12, — | 4 / 1 / 15 | 0,62 | 0,18 | 0,600, 0,77 |
| **Rừng 0,40 · 3/5 (chọn)** | 6/12, 9/12 | 10 / 4 / 6 | **1,00** | 0,18 | 0,561, 0,85 |
| Rừng 0,40 · 2/5 | 8/12, 11/12 | 16 / 4 / 0 | 1,48 | 0,27 | 0,525, 1,33 |
| Rừng 0,50 · 3/5 | 5/12, 5/12 | 10 / 2 / 8 | 0,90 | 0,18 | 0,581, 0,68 |
| LSTM 0,50 · 3/5 | 6/12, — | 9 / — / — | 0,95 | 0,46 | 0,514, 1,66 |

Trên phiên live, cột "bỏ nghỉ" tắt thời gian nghỉ để xem riêng khả năng nhận từng cú. Rừng
0,50 · 3/5 cho 0/6 `zoom_in`, vì độ tin `zoom_in` trên tay người dùng chủ yếu dưới 0,50.

**Người dùng chọn 2026-11-01:** mô hình ghép, zoom theo rừng ở 0,40 · 3/5, vuốt giữ 0,85 · 4/5,
và phím `+` / `−` vì trình chiếu bằng PowerPoint. Đây là **đổi thiết kế** so với một `CONF_FIRE`
chung của SPEC.

**Cách làm.**

- `FSM_ZOOM_FIRE`, `FSM_ZOOM_K` trong `config.py`; ngưỡng giữ của ứng viên zoom là
  `min(CONF_HOLD, FSM_ZOOM_FIRE)`. Tiền tố `FSM_` nằm ngoài băm bản ghi, nên cả 46 bản ghi Phase 8
  vẫn hợp lệ.
- Áp cho mọi mô hình, vì mọi mô hình dùng chung một máy trạng thái. Vì vậy các hàng khác của
  bảng cũng đổi.
- `sweep_activation.py` và ba hàng `FSM_TRADEOFF` của `bench.py analyze` vẫn quét một ngưỡng chung;
  `analyze` có thêm một hàng cho cấu hình cuối.

**Kết quả với code thật** (`analyze/run_07`, `evaluate/run_13`–`run_16`), khớp phép thử nháp:

- Mô hình ghép: F1 sự kiện val 0,561, 0,85 nhầm/phút val, 0,18 nhầm/phút talking (0,79 mỗi phút
  có tay), recall vuốt 0,55, recall zoom 0,50, **1,00 lệnh mỗi lời nhắc**, trễ val 0,76 s.
- Replay phiên `live_final`: 4 lệnh vuốt như cũ, **6 cú zoom thành lệnh, cả 6 đúng chiều**.
- "0,9–1,1 lệnh" trên webcam giờ đạt theo định nghĩa của SPEC, nhưng vẫn có bù trừ: recall chung
  chỉ 0,525. Trên video val, mô hình ghép đạt 0,61 lệnh mỗi cử chỉ, tức mục của Phase 9 vẫn chưa
  đạt.

**Bảng Phase 8 dựng lại** (`experiments/run_04`, không học lại, bộ cửa sổ vẫn trùng từng bit):

| F1 sự kiện | `run_03` (0,85 · 4/5 chung) | `run_04` (cấu hình cuối) |
|---|---|---|
| LSTM, năm seed | 0,629 ± 0,051 | 0,627 ± 0,058 |
| Ghép, năm seed | 0,516 ± 0,056 | 0,522 ± 0,043 |
| Rừng, năm seed | 0,235 ± 0,024 | 0,305 ± 0,010 |
| LSTM, k-fold: F1 / nhầm mỗi phút | 0,722 / 0,57 | 0,677 / 1,08 |
| Ghép, k-fold: F1 / nhầm mỗi phút | 0,597 / 0,37 | **0,677 / 0,63** |

- **Với công thức chính, LSTM vẫn hơn mô hình ghép trên val:** −0,105 F1 sự kiện, độ lệch chuẩn
  0,058. Qua năm fold người, hai bên bằng nhau và mô hình ghép ít nhầm hơn. Với mô hình đã lưu
  (Bảng 1, `run_08`), mô hình ghép đạt 0,561, LSTM 0,507.
- **Lý do chọn mô hình ghép đến từ webcam,** không từ IPN: trên tay người dùng nó phát được zoom
  mà không nhầm thêm khi nói chuyện.
- Ba kết luận một seed của bảng phụ lại lật: 11 điểm rút gọn (−0,067, nay đủ bằng chứng), biên
  khoảnh khắc chính 6 bước của rừng (−0,008, nay không đủ), quota tự nhiên của rừng (−0,052, nay đủ).
  Đúng bài học ở mục 6.

**Giới hạn.**

- Ngưỡng chọn trên ít dữ liệu (40 lời nhắc, 12 cú zoom), và chính dữ liệu đó dùng để chấm, nên
  con số lạc quan. **Phải xác nhận bằng một phiên thử mới.**
- Phím `+` / `−` chưa được kiểm chứng trên PowerPoint. Khi đang phóng to, mũi tên có thể di chuyển
  trong slide thay vì chuyển slide.
- Với 3/5, cú mở rồi chụm lại ngay chỉ tạo khoảng 2 cửa sổ rõ, không đủ phiếu: nên giữ yên khoảng
  1 giây sau khi mở hoặc chụm, và cách nhau khoảng 2 giây giữa hai cử chỉ.

## 8. Bước tiếp

1. **Đã xong.**
   - 2026-10-26: chọn 0,85 · 4/5; thêm "không lấy đà ngược chiều" vào màn hình trợ giúp và
     `docs/gestures.md`.
   - 2026-11-01: mô hình ghép, zoom 0,40 · 3/5, phím `+` / `−` (mục 7);
   - 2026-11-02: người dùng đổi ánh xạ vuốt — vuốt trái sang slide sau, vuốt phải về slide trước
     (`CTRL_HOTKEYS`; SPEC gốc ngược lại);
     `results/model_comparison` và bảng Phase 8 đã tính lại.
2. **Còn lại của Phase 10.**
   - Thử lại slide thật với cấu hình mới, xác nhận con số ở mục 7 và phím zoom.
   - Tốc độ đủ bốn mô hình × hai mức ánh sáng: `run_01` mới có `rules` và `rf`, ánh sáng
     tối. Thêm một lần đo lại để kiểm "đo lại lần hai gần giống".
   - Độ trễ thủ công.
   - Video demo.
