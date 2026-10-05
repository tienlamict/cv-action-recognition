# Bộ cử chỉ — làm theo cách của IPN Hand

> **Trạng thái:** bản nháp, Claude viết ngày 2026-10-05 từ số đo điểm mốc và ảnh
> các đoạn mẫu. **Chờ người dùng review.**

Mô hình học cử chỉ **theo cách người diễn IPN làm**, không theo cách bạn hình
dung. Nếu bạn làm khác, hệ thống sẽ không nhận ra dù bạn thấy mình làm "đúng".
Tài liệu này mô tả từng cử chỉ theo năm điều: tay bắt đầu ở đâu, đi hướng nào,
biên độ bao xa, nhanh chậm ra sao, và các ngón xếp thế nào.

**Trái / phải trong tài liệu này luôn là trái / phải của chính bạn.** Trên màn
hình demo, ảnh được lật như gương, nên tay bạn đi về bên trái thì trên màn hình
cũng đi sang trái. Ảnh gốc đưa vào mô hình thì không lật — ở đó hướng ngược lại,
và đã được tính sẵn qua `SWIPE_LEFT_SIGN = +1` (đo trên IPN ở Phase 3).

Xem tận mắt: `results/phase3/examples/<cử chỉ>_<người>.mp4` — mỗi cử chỉ ba
người, ảnh không lật, có vẽ điểm mốc.

---

## Tóm tắt

| Cử chỉ | Mã IPN | Ngón tay: đầu → cuối | Cổ tay | Cả cử chỉ |
|---|---|---|---|---|
| `swipe_left` | G05 *Throw left* | chụm đầu ngón → **mở duỗi**, ngón chỉ sang trái | hất **sang trái của bạn**, ngang thân | ≈ 2 s |
| `swipe_right` | G06 *Throw right* | chụm đầu ngón → **mở duỗi**, ngón chỉ sang phải | hất **sang phải của bạn** | ≈ 2 s |
| `zoom_in` | G10 *Zoom in* | cái + trỏ + giữa **chụm** → **mở ra**; nhẫn, út gập suốt | gần như đứng yên | ≈ 2 s |
| `zoom_out` | G11 *Zoom out* | cái + trỏ + giữa **mở** → **chụm lại**; nhẫn, út gập suốt | gần như đứng yên | ≈ 2 s |

Zoom giống thao tác trên điện thoại: **mở ngón ra là zoom in, chụm lại là zoom
out**. Tên gọi của IPN khớp với hình dung thông thường; số đo xác nhận điều này
(độ xòe tăng ở `zoom_in` 78% số đoạn, giảm ở `zoom_out` 80% số đoạn).

---

## Tư thế chung

- **Tay phải.** 133/145 clip train dùng tay phải. Tay trái chưa được xét riêng.
- **Bàn tay giơ trước ngực, phía bên phải thân**, khuỷu tay gập. Trong khung
  hình IPN, cổ tay nằm ở khoảng 3/4 chiều cao khung (nửa dưới), lệch về phía
  tay đang dùng.
- **Bàn tay khá to trong khung:** đoạn cổ tay → gốc ngón giữa chiếm khoảng
  **1/5 chiều cao khung hình** (≈ 90 px ở 480 px). Ngồi xa quá thì bàn tay nhỏ,
  MediaPipe dễ mất dấu.
- **Một cử chỉ ≈ 2 giây, nhưng phần động tác chính chỉ ≈ 0,2–0,3 giây.** Hai
  giây đó gồm: đưa tay vào tư thế → động tác dứt khoát → giữ hoặc thả tay. Đừng
  làm chậm rãi kéo dài cả hai giây; cũng đừng làm vội đến mức bỏ bước chuẩn bị.
- Giữa hai cử chỉ, hạ tay hoặc để tay yên một nhịp.

---

## `swipe_left` — G05 *Throw left*

Giống động tác **hất một vật nhỏ sang bên trái của bạn**.

- **Bắt đầu:** tay phải giơ trước ngực, lệch về bên phải thân (gần vai phải).
  Các đầu ngón **chụm lại** như đang cầm một vật nhỏ.
- **Hướng:** hất **ngang sang trái của bạn**, cắt ngang trước ngực về phía giữa
  thân. Chủ yếu là chiều ngang: dịch ngang lớn hơn dịch dọc ở 71% số đoạn.
- **Biên độ:** vừa phải — cổ tay đi khoảng **1–2 lần chiều dài lòng bàn tay**
  (lòng bàn tay = cổ tay → gốc ngón giữa). Đây là cú hất cẳng tay và cổ tay,
  **không phải vung cả cánh tay**. Cuối động tác tay hơi thu về, nên điểm cuối
  chỉ cách điểm đầu khoảng 0,7 lòng bàn tay.
- **Nhanh chậm:** cả cử chỉ ≈ 2,0 s (trung vị; 90% đoạn dưới 3,6 s). Cú hất
  chính chỉ ≈ 0,3 s. Cổ tay đi nhanh nhất trong bốn cử chỉ: đỉnh ≈ 6 lòng bàn
  tay/giây, gấp đôi hai cử chỉ zoom.
- **Ngón tay:** từ chụm → **mở duỗi trong lúc hất** (độ xòe đạt đỉnh giữa cú
  hất). Lúc mở hết, bàn tay duỗi gần thẳng, nằm ngang, các ngón chỉ về phía
  trái — phía vừa hất tới. Sau đó tay thường thả lỏng lại.
- **Dễ sai:** vẫy tay qua lại (hai chiều) — mô hình cần một chiều dứt khoát;
  hất chéo lên hoặc xuống quá nhiều thì giống `G03`/`G04` (hất lên/xuống, thuộc
  lớp `none`).

## `swipe_right` — G06 *Throw right*

Đối xứng với `swipe_left`: **hất một vật nhỏ sang bên phải của bạn**.

- **Bắt đầu:** tay phải chụm đầu ngón, giơ trước ngực, **gần giữa thân hơn**
  so với lúc bắt đầu `swipe_left`.
- **Hướng:** hất **ngang ra phía phải của bạn** — với tay phải là hất ra ngoài,
  xa thân. Chiều ngang trội hơn chiều dọc ở 73% số đoạn.
- **Biên độ:** như `swipe_left` — khoảng 1–2 lòng bàn tay; điểm cuối cách điểm
  đầu ≈ 0,6 lòng bàn tay.
- **Nhanh chậm:** cả cử chỉ ≈ 1,9 s (90% đoạn dưới 3,4 s); cú hất chính
  ≈ 0,3 s.
- **Ngón tay:** từ chụm → mở duỗi giữa cú hất, bàn tay nằm ngang (thường úp
  xuống), các ngón chỉ về phía phải; sau đó thả lỏng lại.
- **Dễ sai:** như `swipe_left`.

## `zoom_in` — G10 *Zoom in*

**Mở ba đầu ngón đang chụm ra**, như kéo giãn ảnh trên màn hình cảm ứng.

- **Bắt đầu:** bàn tay giơ trước ngực, lòng bàn tay hướng về camera. Đầu
  **ngón cái, trỏ và giữa chụm sát vào nhau** (khoảng cách đầu ngón cái – đầu
  ngón trỏ chỉ ≈ 0,25 lòng bàn tay). **Ngón nhẫn và ngón út gập vào lòng bàn
  tay.**
- **Hướng:** cổ tay **gần như đứng yên** (chỉ xê dịch ≈ 0,4 lòng bàn tay, so
  với ≈ 1,3 ở cú hất). Chỉ các ngón chuyển động.
- **Biên độ:** ngón cái bật **ra một bên**, ngón trỏ và ngón giữa **duỗi thẳng
  lên, sát nhau**. Cuối động tác đầu ngón cái cách đầu ngón trỏ ≈ 1,3 lòng bàn
  tay — bàn tay thành hình chữ "L" với hai ngón trỏ + giữa.
- **Nhanh chậm:** cả cử chỉ ≈ 2,0 s (90% đoạn dưới 3,4 s); động tác mở
  ≈ 0,2 s. Một số người mở rồi chụm lại ngay cuối đoạn.
- **Ngón tay:** **nhẫn và út gập suốt từ đầu đến cuối.** Ngón trỏ và giữa đi
  cùng nhau, không tách khỏi nhau; chỗ mở ra là giữa ngón cái và cặp trỏ – giữa.
- **Dễ sai — quan trọng nhất:** xòe **cả năm ngón** từ nắm tay thành bàn tay
  mở. Đó là `G07` *Open twice*, thuộc lớp `none` — xem mục dưới.

## `zoom_out` — G11 *Zoom out*

Ngược hoàn toàn với `zoom_in`: **chụm ba đầu ngón đang mở lại**.

- **Bắt đầu:** tư thế cuối của `zoom_in` — lòng bàn tay hướng camera, ngón cái
  bật ra một bên, **trỏ và giữa duỗi thẳng sát nhau**, nhẫn và út gập.
- **Hướng:** cổ tay gần như đứng yên.
- **Biên độ:** đầu ngón cái, trỏ, giữa chụm về một điểm: khoảng cách đầu ngón
  cái – đầu ngón trỏ từ ≈ 1,4 xuống ≈ 0,3 lòng bàn tay.
- **Nhanh chậm:** cả cử chỉ ≈ 2,0 s (90% đoạn dưới 3,5 s); động tác chụm
  ≈ 0,2 s.
- **Ngón tay:** nhẫn và út gập suốt; trỏ và giữa co lại khi chụm.
- **Dễ sai:** nắm cả bàn tay lại thành nắm đấm thay vì chụm ba đầu ngón.

---

## Những động tác phải ra `none` — đừng làm khi không định ra lệnh

IPN có mười lớp cử chỉ khác, tất cả được gộp thành `none` và mô hình **học để
bỏ qua chúng**. Bốn lớp dưới đây dễ nhầm nhất với cử chỉ của ta:

| Động tác IPN | Giống cử chỉ nào | Khác ở đâu |
|---|---|---|
| `G07` *Open twice* — xòe tay hai lần | `zoom_in` | Từ nắm tay xòe **cả năm ngón**, làm **hai lần**. Độ xòe đỉnh ≈ 2,0 lòng bàn tay, so với ≈ 1,4 ở `zoom_in`; nhẫn và út cũng duỗi ra, trong khi `zoom_in` giữ chúng gập |
| `G03` / `G04` *Throw up / down* | `swipe_left`, `swipe_right` | Hất **theo chiều dọc**: biên độ dọc ≈ 1,1–1,4 lòng bàn tay, ngang chỉ ≈ 0,5 |
| `B0A` / `B0B` — chỉ bằng một / hai ngón | — | Duỗi ngón trỏ (hoặc trỏ + giữa) rồi **di khắp nơi** trong nhiều giây (trung vị 7 s). Rê tay lâu không phải cử chỉ |
| `D0X` — không cử chỉ | — | Tay thả lỏng, hạ xuống, hoặc ra khỏi khung |

---

## Số liệu và cách đo

**Thời lượng** lấy từ `results/phase3/dataset_stats/run_02/by_class.md` (189
clip không lệch nhãn, cả train lẫn test):

| Lớp | Trung vị | p90 | Dài hơn `WIN_SEC` = 1,2 s |
|---|---|---|---|
| `swipe_left` | 2,00 s | 3,56 s | 92% |
| `swipe_right` | 1,93 s | 3,42 s | 89% |
| `zoom_in` | 2,00 s | 3,40 s | 89% |
| `zoom_out` | 1,97 s | 3,48 s | 91% |

**Các số còn lại** đo trên **tập train** (145 clip không lệch nhãn, 145 đoạn
mỗi lớp; 119–126 đoạn mỗi lớp đủ dữ liệu, số còn lại mất tay ở đầu hoặc cuối
đoạn). Chuỗi đi qua đúng đường ống của mô hình: `load_sequence` (15 Hz, vá lỗ
ngắn) rồi `normalize_window`. Báo trung vị, trong ngoặc là phân vị 25–75.

| Đại lượng | `swipe_left` | `swipe_right` | `zoom_in` | `zoom_out` |
|---|---|---|---|---|
| `dx` ròng của cổ tay | +0,67 [+0,09; +1,30] | −0,57 [−1,02; −0,06] | −0,07 | +0,08 |
| Biên độ ngang của cổ tay | 1,30 [0,80; 1,94] | 1,21 [0,83; 1,68] | 0,39 | 0,36 |
| Tốc độ cổ tay lớn nhất (lòng bàn tay/s) | 6,0 | 5,9 | 2,9 | 2,8 |
| Độ xòe đầu → cuối | 1,24 → 1,20 (đỉnh 1,88) | 1,21 → 1,10 (đỉnh 1,78) | 0,89 → 1,17 | 1,17 → 0,89 |
| Đầu cái – đầu trỏ, đầu → cuối | 0,46 → 0,57 | 0,48 → 0,97 | **0,25 → 1,28** | **1,43 → 0,33** |
| Duỗi nhẫn / út, cuối đoạn | 1,33 / 1,37 | 0,81 / 0,83 | **0,54 / 0,51** | **0,50 / 0,51** |
| Thời gian động tác chính (10→90%) | 0,27 s | 0,33 s | 0,20 s | 0,20 s |

Định nghĩa:

- **Lòng bàn tay** — đơn vị đo: khoảng cách cổ tay → gốc ngón giữa (điểm 0 → 9)
  ở frame đầu đoạn, đúng như `normalize_window`.
- **`dx`** — dịch ngang của cổ tay giữa ba bước đầu và ba bước cuối, trên ảnh
  **không lật**. Dương = sang phải ảnh gốc = sang **trái của người làm**.
- **Độ xòe** — trung bình khoảng cách năm đầu ngón tới cổ tay (`features.openness`).
- **Duỗi ngón** — khoảng cách đầu ngón → cổ tay chia khoảng cách gốc ngón →
  cổ tay. Thang tham chiếu đo trên `B0A` (chỉ một ngón): ngón trỏ duỗi ≈ 1,5,
  ngón nhẫn gập ≈ 0,5.
- **Thời gian động tác chính** — thời gian để đi từ 10% tới 90% thay đổi ròng
  (vị trí cổ tay với hai lớp vuốt, độ xòe với hai lớp zoom). Lưới 15 Hz nên độ
  phân giải là 0,07 s.

Mô tả tư thế ngón tay đối chiếu thêm bằng mắt trên ảnh cắt từ 12 đoạn mẫu ở
`results/phase3/examples/` và hai đoạn `G07`.

---

## Giới hạn của bản này

- **Chưa thử trên webcam của bạn.** Ở Phase 5, `demo.py --show-features` sẽ
  kiểm bằng số: giá trị đặc trưng khi bạn làm cử chỉ phải nằm trong khoảng
  phân vị 25–75 của lớp đó trên IPN (`results/phase4/ipn_feature_ranges.json`).
  Báo đỏ liên tục nghĩa là bạn làm khác IPN — sửa tài liệu này và luyện lại.
- **Từng đoạn IPN khá nhiễu:** chỉ 78–81% đoạn vuốt có `dx` cùng dấu với lớp
  của mình, và 74–80% đoạn zoom có độ xòe đổi đúng chiều. Mô tả ở đây là cách
  làm **điển hình**, không phải cách mọi người diễn IPN đều làm.
- **Ảnh đối chiếu chỉ từ ba người cùng nhóm quay `1CM1`.** Số đo thì phủ toàn
  bộ 145 clip train.
- **Script tính các số ở bảng thứ hai chưa nằm trong repo** (viết tạm trong
  phiên làm việc). Bảng thời lượng thì tái lập được bằng
  `scripts/dataset_stats.py`.
- **Tay trái** chưa xét. Phép lật ngang ở Phase 4 có thể giúp, nhưng nên dùng
  tay phải cho đến khi đo được.
