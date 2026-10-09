# Phase 6 — Ghi chú phân tích rừng ngẫu nhiên

> Claude viết ngày 2026-10-08 từ lần chạy `results/phase6/train_rf/run_04`. Mọi con số ở đây
> lấy từ các bảng trong thư mục lần chạy đó, nên tái lập được bằng
> `python scripts/train_rf.py`: mô hình có seed cố định và cho ra cùng kết quả mỗi lần
> chạy. Tên bảng nguồn ghi trong ngoặc ở mỗi mục.

## 1. Kết quả trên tập val

11 038 cửa sổ. Tập val giữ phân bố tự nhiên: `none` chiếm 96,5%. (`comparison`,
`classification_report.txt`)

| Mô hình | macro-F1 | F1 none | F1 swipe_left | F1 swipe_right | F1 zoom_in | F1 zoom_out |
|---|---|---|---|---|---|---|
| Đoán ngẫu nhiên đều | 0,0796 | | | | | |
| Luôn đoán `none` | 0,1964 | | | | | |
| Luật (Phase 5) | 0,2305 | 0,714 | 0,056 | 0,043 | 0,164 | 0,176 |
| **Rừng ngẫu nhiên** | **0,4361** | 0,951 | 0,212 | 0,232 | 0,368 | 0,417 |

- **Recall** các lớp cử chỉ của rừng ngẫu nhiên là 0,49–0,63.
- **Precision** của chúng thấp (0,13–0,35). 877 cửa sổ `none` (8,2%) bị báo thành cử chỉ,
  trong khi cả tập val chỉ có 388 cửa sổ cử chỉ thật.

Hình: `confusion.png` (ma trận nhầm lẫn thô và chuẩn hoá theo hàng), `importances.png`.

## 2. So sánh hai bảng xếp hạng độ quan trọng

**Hai cách đo đồng ý ở nhóm đầu:** `pinch_range`, `pinch_delta`, `max_vx` chiếm ba vị trí
đầu ở cả hai, chỉ khác thứ tự. (`importances`)

**Bất đồng lớn nhất nằm ở các cặp đặc trưng đo gần cùng một thứ:**

| Đặc trưng | Hạng Gini | Hạng hoán vị | Hoán vị (macro-F1 giảm) |
|---|---|---|---|
| `dx` | 4 | 13 | −0,007 ± 0,007 |
| `mean_vx` | 5 | 12 | −0,004 ± 0,004 |
| `open_trend` | 7 | 10 | +0,002 ± 0,008 |
| `open_delta` | 10 | 15 | −0,009 ± 0,002 |

**Vì sao:**

- **Độ quan trọng Gini** đo trên tập train, lúc dựng cây. Hai cột gần như trùng nhau thay
  phiên nhau được chọn làm điểm chia, nên **cả hai đều được ghi công**.
- **Độ quan trọng hoán vị** đo trên val, bằng cách xáo một cột và xem mô hình kém đi bao
  nhiêu. Xáo một cột thì cột "sinh đôi" vẫn còn nguyên, nên mô hình gần như không kém đi: độ
  quan trọng của **cả hai bị giấu**. Đây đúng là cảnh báo "đặc trưng tương quan chia sẻ
  điểm" trong cẩm nang, bước 14.d.

**Kiểm chứng bằng cách xáo CẢ NHÓM theo cùng một hoán vị**, cùng một quy trình cho mọi dòng
(`importances_grouped`):

| Xáo | Tương quan Spearman (train) | macro-F1 giảm | Số cửa sổ vuốt bị đoán ngược hướng |
|---|---|---|---|
| (không xáo) | | 0 | 8 |
| chỉ `dx` | | −0,009 ± 0,007 | 17,5 |
| chỉ `mean_vx` | | −0,006 ± 0,004 | 8,9 |
| **`dx` + `mean_vx`** | +0,966 | **+0,042 ± 0,005** | **42,8** |
| `max_vx` (để so) | | +0,038 ± 0,006 | 9,1 |
| `open_delta` + `open_trend` | +0,944 | +0,015 ± 0,005 | 10,3 |
| `pinch_delta` + `pinch_range` | +0,141 | +0,171 ± 0,004 | 7,6 |

- Thông tin hướng của cú vuốt nằm trong cặp `dx` + `mean_vx`. Mất cả cặp thì số cửa sổ vuốt
  bị đoán ngược hướng tăng hơn 5 lần.
- Xét theo nhóm, cặp này quan trọng ngang `max_vx`.

Hoán vị **âm** ở một đặc trưng đơn lẻ (như `open_delta`) nghĩa là xáo cột đó còn làm mô hình
tốt lên chút ít. Đặc trưng ấy không giúp gì thêm khi cột sinh đôi của nó vẫn còn, và có thể
góp một chút quá khớp. Không nên đọc nó thành "đặc trưng có hại" khi xét cả nhóm.

## 3. Bảng đối chiếu: dự đoán và thực tế

Dự đoán lập trước khi huấn luyện, từ cổng boxplot của Phase 4: ba đặc trưng của cổng là
`pinch_delta`, `dx`, `max_vx`. (`importances`, `importances_grouped`)

| Đặc trưng | Dự đoán quan trọng | Hạng Gini | Hạng hoán vị | Ghi chú |
|---|---|---|---|---|
| `pinch_delta` | có | 1 | 2 | đúng như dự đoán |
| `max_vx` | có | 3 | 3 | đúng như dự đoán |
| `dx` | có | 4 | 13 | quan trọng **theo nhóm** cùng `mean_vx` (mục 2) |
| `pinch_range` | không | 2 | **1** | ngoài dự đoán — xem dưới |
| `open_range` | không | 6 | 4 | giúp tách `G07` "xòe tay hai lần" khỏi zoom (mục 4.4) |
| `max_vy` | không | 8 | 5 | chuyển động dọc là dấu hiệu của `none` (hất lên/xuống) |
| `straightness` | (bị bỏ khỏi cổng ở Phase 4) | 14 | 8 | đúng như cổng đã cho thấy: tách lớp kém |

**Vì sao `pinch_range` đứng đầu mà không được dự đoán:**

- Phần khó nhất của bài toán trên val là phân biệt **cử chỉ với `none`**, không phải hướng
  của cử chỉ.
- `pinch_range` trả lời câu hỏi "ngón cái và ngón trỏ có đổi khoảng cách nhiều không". Câu
  này tách zoom khỏi mọi thứ khác: hộp zoom nằm hẳn trên hộp `none` trong hình boxplot của
  Phase 4.
- `pinch_delta` chỉ thêm thông tin "mở hay chụm" khi đã biết là zoom.

**Kết luận cho điều kiện thứ ba của cổng Phase 6:** chưa đạt theo đúng chữ. Hai trong ba
đặc trưng dự đoán đứng đầu; đặc trưng thứ ba (`dx`) bị độ quan trọng hoán vị giấu đi vì trùng
thông tin với `mean_vx`, và phép xáo theo nhóm cho thấy nó quan trọng ngang `max_vx`. SPEC
yêu cầu có lời giải thích trước khi đi tiếp; lời giải thích là mục này.

## 4. Các ô lớn ngoài đường chéo

Bảng nguồn: `errors_by_src_label`, `none_false_alarms_by_src`, `cell_profiles`. Tốc độ tính
bằng lòng bàn tay/giây, dời ngang (trị tuyệt đối) và khoảng cách tính bằng lòng bàn tay; mọi
số là trung vị trên các cửa sổ của ô.

### 4.1. `none` → `swipe_left` (366) và `none` → `swipe_right` (344)

Đây là nguồn báo nhầm chính. Trong 710 cửa sổ:

- `B0B` (chỉ hai ngón): 282;
- `B0A` (chỉ một ngón): 176;
- `D0X` (không cử chỉ): 148.

Tính theo tỉ lệ thì khác: `D0X` 10,6%, `B0B` 9,7%, `B0A` 5,8%.

| Ô | Số cửa sổ | Tốc độ ngang đỉnh | Dời ngang | Khoảng biến thiên độ xòe |
|---|---|---|---|---|
| `B0A` → `swipe_left` / `swipe_right` | 83 / 93 | 5,51 / 5,41 | 1,98 / 1,35 | 0,81 / 0,67 |
| `B0B` → `swipe_left` / `swipe_right` | 162 / 120 | 5,23 / 5,59 | 1,59 / 1,37 | 0,80 / 0,83 |
| `D0X` → `swipe_left` / `swipe_right` | 90 / 58 | 7,07 / 8,51 | 1,14 / 1,07 | 0,87 / 1,16 |
| *đối chứng:* vuốt thật nhận đúng (trái / phải) | 56 / 60 | 5,12 / 4,94 | 0,81 / 0,88 | 1,08 / 0,90 |
| *đối chứng:* `B0A` / `B0B` / `D0X` nhận đúng là `none` | | 3,81 / 3,57 / 2,86 | | |

- **Giả thuyết A — tay chỉ trỏ di chuyển như một cú hất.**
  - Cửa sổ chỉ trỏ bị báo nhầm có tốc độ ngang đỉnh 5,2–5,6. Con số này ngang, thậm chí
    hơn, cú vuốt thật (4,9–5,1), và còn dời xa hơn.
  - Riêng tốc độ và quãng dời thì không phân biệt được hai loại. Bộ đặc trưng không mô tả
    **hình dạng bàn tay trong lúc di chuyển** (ngón trỏ duỗi khi chỉ, cả bàn tay mở khi hất);
    chỉ có độ xòe và khoảng cách cái–trỏ.
- **Giả thuyết B — lệch phân bố lớp nền giữa train và val.**
  - Do quota `none` chia đều theo nhãn gốc ở Phase 4, tay chỉ trỏ chỉ chiếm 20% lớp `none`
    của train: `B0A` và `B0B` mỗi loại 167/1 663 (`results/phase4/build_dataset/run_02`).
  - Ở val nó chiếm 64%: `B0A` 3 491 và `B0B` 3 328 trên 10 650 cửa sổ `none`.
  - Mô hình thấy quá ít ví dụ về đúng loại chuyển động hay gặp nhất.
- **Giả thuyết C — `D0X` là lúc tay đưa vào hoặc ra khỏi khung hình.** Cửa sổ `D0X` bị báo
  nhầm có tốc độ ngang đỉnh 7,1–8,5, nhanh hơn hẳn cú hất thật. Cửa sổ `D0X` được nhận đúng
  chỉ có 2,9.

**Hướng thử:**

- Ở Phase 8, khảo sát lại quota `none`: cho tay chỉ trỏ nhiều hơn để kiểm giả thuyết B.
- Bổ sung đặc trưng hình dạng ngón (ví dụ "chỉ ngón trỏ duỗi"). Đây là thay đổi của Phase 2,
  phải được người dùng duyệt.
- Máy trạng thái ở Phase 9 (đồng thuận k trên n cửa sổ, ngưỡng `CONF_FIRE`) sẽ lọc bớt các
  cửa sổ báo lẻ.

### 4.2. `swipe_left` → `none` (41/104) và `swipe_right` → `none` (31/96)

| Ô | Số cửa sổ | Tốc độ ngang đỉnh | Dời ngang |
|---|---|---|---|
| `swipe_left` nhận đúng / bỏ sót | 56 / 41 | 5,12 / 3,71 | 0,81 / 0,25 |
| `swipe_right` nhận đúng / bỏ sót | 60 / 31 | 4,94 / 2,77 | 0,88 / 0,32 |

- **Giả thuyết:** một số người trong val hất nhẹ và chậm hơn mức mô hình học được.
- **Hoặc:** cửa sổ chỉ chứa một phần cú hất, vì khoảnh khắc chính nằm sát biên 3 bước.

Bỏ sót ở **mức cửa sổ** chưa chắc là bỏ sót ở **mức sự kiện**: các cửa sổ khác của cùng cú
vuốt có thể vẫn được nhận đúng. Đánh giá mức sự kiện ở Phase 8 sẽ trả lời.

### 4.3. `zoom_in` → `zoom_out` (17) và `zoom_out` → `zoom_in` (10)

| Ô | Số cửa sổ | `pinch_delta` |
|---|---|---|
| `zoom_in` nhận đúng / bị đoán `zoom_out` | 46 / 17 | +1,49 / **−1,74** |
| `zoom_out` nhận đúng / bị đoán `zoom_in` | 48 / 10 | −1,57 / **+1,63** |

Cửa sổ bị đảo chiều có độ mở cái–trỏ đổi **mạnh theo chiều ngược với nhãn**.

**Giả thuyết: đây là lỗi của nhãn, không phải của mô hình.**

- Người diễn IPN hay mở rồi chụm lại trong cùng một đoạn nhãn `zoom_in` (thấy rõ trong đoạn
  mẫu `zoom_in_1CM1_3.mp4`).
- Luật nhãn của Phase 4 chọn khoảnh khắc chính theo **độ lớn** thay đổi của khoảng cách
  cái–trỏ, không xét dấu. Với đoạn mà pha chụm nhanh hơn pha mở, khoảnh khắc chính rơi vào
  pha chụm, và các cửa sổ quanh đó mang nhãn `zoom_in` dù ngón đang chụm.

**Hướng thử:** với zoom, chọn khoảnh khắc chính theo đúng chiều mà tên lớp nói (mở với
`zoom_in`, chụm với `zoom_out`). Cách này dùng nghĩa của nhãn chứ không dùng dữ liệu của lớp
khác, nhưng sẽ làm hai hộp zoom tách đẹp hơn một phần "nhờ cách gán nhãn". Cần người dùng
quyết, và nếu làm thì phải ghi rõ trong báo cáo.

### 4.4. `none` (`G07` "xòe tay hai lần") → zoom (61)

- `G07` có **tỉ lệ** báo nhầm cao nhất trong các nhãn gốc: 77/403 = **19,1%**. Gần như toàn
  bộ bị đoán thành zoom: 30 thành `zoom_in`, 31 thành `zoom_out`.

| Ô | Số cửa sổ | Khoảng biến thiên cái–trỏ | Khoảng biến thiên độ xòe |
|---|---|---|---|
| `G07` → `zoom_in` / `zoom_out` | 30 / 31 | 1,99 / 1,90 | 0,81 / 0,93 |
| *đối chứng:* zoom thật nhận đúng (in / out) | 46 / 48 | 1,97 / 1,90 | 0,66 / 0,55 |

- Khoảng cách cái–trỏ thay đổi y như zoom thật. Khác biệt duy nhất là **độ xòe của cả năm
  ngón** biến thiên nhiều hơn: `G07` mở cả bàn tay, còn zoom của IPN giữ nhẫn và út gập.
- Mô hình có dùng tới khác biệt này (`open_range` hạng 4 theo hoán vị), nhưng chưa đủ.

### 4.5. `zoom_in` → `none` (25/94) và `zoom_out` → `none` (31/94)

Cùng kiểu với 4.2: các cửa sổ bị bỏ sót có `pinch_delta` nhỏ hơn hẳn cửa sổ nhận đúng (0,41 so
với 1,49 ở `zoom_in`; −0,72 so với −1,57 ở `zoom_out`). Đây là cử chỉ yếu, hoặc cửa sổ chỉ
chứa một phần động tác.

## 5. Cổng kiểm tra Phase 6

| Điều kiện | Kết quả |
|---|---|
| Rừng cao hơn hẳn luật | **đạt**: 0,4361 so với 0,2305 (+0,206) |
| macro-F1 không vượt 0,97 (dấu hiệu rò rỉ) | **đạt**: 0,4361; train và val không chung người hay clip nào |
| Ba đặc trưng đầu bảng là ba đặc trưng của cổng | **chưa đạt theo chữ, đã giải thích** (mục 2–3) |

## 6. Ghi chú cho lần thử trực tiếp

Hai số đo trong mục này **không** nằm trong bảng của `train_rf.py`. Chúng là phép đo nhanh
lúc kiểm tra demo, chỉ để định hướng, không đưa vào báo cáo.

- Demo dự đoán bằng rừng mất **9,2 ms mỗi cửa sổ**. Cách gọi thẳng lõi của cây cho đúng xác
  suất của scikit-learn; cách gọi qua `predict_proba` thì mất 62,6 ms và sẽ làm tụt FPS.
- **Chỉ để tham khảo**, không thay được lần thử trực tiếp: trên 45 giây đầu video
  `1CM42_12_R__157` (tập val), rừng cho 7 cụm nhãn khác `none`, luật cho 29 đợt.
