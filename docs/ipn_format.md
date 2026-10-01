# Định dạng IPN Hand — khảo sát trên dữ liệu thật

Khảo sát ngày 2026-09-29 trên `data/ipn/` đã giải nén. Mọi con số dưới đây đếm
trực tiếp từ file trên đĩa, không lấy từ tài liệu hay trí nhớ.

---

## 1. Có gì trên đĩa

```
data/ipn/
├─ metadata.csv                     200 dòng + tiêu đề
├─ videos/videos/*.avi              200 video
└─ annotations/
   ├─ Annot_List.txt                5 649 đoạn + dòng tiêu đề
   ├─ Annot_TrainList.txt           4 039 đoạn (không có tiêu đề)
   ├─ Annot_TestList.txt            1 610 đoạn (không có tiêu đề)
   ├─ Video_TrainList.txt           148 dòng
   ├─ Video_TestList.txt            52 dòng
   ├─ classIdx.txt                  14 lớp + tiêu đề
   ├─ class_details.txt             mô tả từng lớp
   └─ metadata.xlsx                 bản Excel của metadata.csv
```

**Dữ liệu là VIDEO, không phải thư mục ảnh từng frame.** Đã tìm `*.jpg`,
`*.png` và thư mục tên chứa "frame" — không có. Hệ quả: `iter_frames` hiện tại
đã đọc được, **không cần mở rộng** cho thư mục ảnh (việc 1 của Phần B thành
không cần làm, và kiểm thử `test_iter_frames_thu_muc_anh` không áp dụng).

---

## 2. Video

| Thuộc tính | Giá trị |
|---|---|
| Số video | 200 |
| Định dạng | `.avi` |
| Độ phân giải | **640×480** ở mọi video đã kiểm |
| FPS | **Không đồng nhất**: 126 video ở 30.0, 74 video ở 29.97 |

FPS khác nhau giữa các video **không gây vấn đề** cho đường ống: `iter_frames`
đọc FPS của từng file và tính `ts = chỉ số frame / fps của chính file đó`, rồi
`resample` đưa mọi thứ về lưới 15 Hz. Nhưng nó là lý do không được viết cứng số
30 ở bất kỳ đâu.

---

## 3. File nhãn

`Annot_List.txt` có dòng tiêu đề, phân tách bằng dấu phẩy:

```
video,label,id,t_start,t_end,frames
1CM1_4_R__229,D0X,1,1,17,17
1CM1_4_R__229,G11,14,18,55,38
1CM1_4_R__229,B0B,3,56,284,229
1CM1_4_R__229,G04,7,285,308,24
1CM1_4_R__229,B0B,3,309,502,194
1CM1_4_R__229,G05,8,503,544,42
```

| Cột | Nghĩa |
|---|---|
| `video` | tên video, không có đuôi `.avi` |
| `label` | mã lớp gốc (`D0X`, `B0A`, `G01`…) |
| `id` | chỉ số lớp 1–14, khớp `classIdx.txt` |
| `t_start`, `t_end` | frame đầu và cuối của đoạn |
| `frames` | độ dài đoạn |

**Chỉ số frame bắt đầu từ 1.** `t_start` nhỏ nhất trong toàn bộ 5 649 đoạn là 1,
không có giá trị 0.

**`t_end` THUỘC đoạn.** Bằng chứng: `frames == t_end - t_start + 1` đúng ở
**5 649/5 649** đoạn; công thức nửa mở (`t_end - t_start`) đúng ở **0** đoạn.
Vậy khi chuyển sang chỉ số Python 0-based, đoạn là `[t_start - 1, t_end)`.

**Các đoạn phủ liên tục cả video.** Cả 200 video đều bắt đầu từ frame 1 và
không có lỗ giữa các đoạn. Lớp `D0X` (non-gesture) chính là phần "không cử chỉ"
nằm xen giữa — nên **không có frame nào không thuộc đoạn nào**, trừ đúng 1 frame
cuối ở 14 video (tổng độ dài các đoạn ít hơn số frame trong metadata 1 đơn vị).

`Annot_TrainList.txt` và `Annot_TestList.txt` có cùng cấu trúc nhưng **không có
dòng tiêu đề**, và là tập con của `Annot_List.txt` (4 039 + 1 610 = 5 649).

---

## 4. Danh sách lớp gốc

Theo `classIdx.txt` và `class_details.txt`, kèm số đoạn đếm từ `Annot_List.txt`:

| id | Mã | Nghĩa ghi trong class_details | Số đoạn |
|---|---|---|---|
| 1 | `D0X` | Non-gesture | 1 431 |
| 2 | `B0A` | Pointing with one finger | 1 010 |
| 3 | `B0B` | Pointing with two fingers | 1 007 |
| 4 | `G01` | Click with one finger | 200 |
| 5 | `G02` | Click with two fingers | 200 |
| 6 | `G03` | Throw up | 200 |
| 7 | `G04` | Throw down | 201 |
| 8 | `G05` | Throw left | 200 |
| 9 | `G06` | Throw right | 200 |
| 10 | `G07` | Open twice | 200 |
| 11 | `G08` | Double click with one finger | 200 |
| 12 | `G09` | Double click with two fingers | 200 |
| 13 | `G10` | Zoom in | 200 |
| 14 | `G11` | Zoom out | 200 |

Thời lượng bốn lớp đích, tính từ `frames` chia FPS của từng video:

| Lớp | Trung vị | Ngắn nhất | Dài nhất |
|---|---|---|---|
| `G05` Throw left | 2,00 s | 0,70 s | 5,51 s |
| `G06` Throw right | 1,90 s | 0,73 s | 5,80 s |
| `G10` Zoom in | 1,97 s | 0,60 s | 6,14 s |
| `G11` Zoom out | 1,94 s | 0,63 s | 6,03 s |

**Trung vị khoảng 2 giây, dài hơn `WIN_SEC = 1,2 s`.** Nghĩa là một cử chỉ IPN
điển hình trải ra nhiều cửa sổ, và ngưỡng phủ nhãn `LABEL_COVERAGE = 0,6` sẽ
quyết định cửa sổ nào mang nhãn cử chỉ. Đây là con số cần nhớ khi viết
`docs/gestures.md`: làm cử chỉ **chậm hơn** bạn tưởng.

---

## 5. Chia train/test và mã người diễn

`Video_TrainList.txt` và `Video_TestList.txt` có hai cột **phân tách bằng TAB**,
không có dòng tiêu đề:

```
1CM1_4_R__229	3751
1CM1_4_R__230	3684
1CM1_4_R__231	3747
```

Cột hai là số frame, khớp cột `Frames` của `metadata.csv`.

| | Số video |
|---|---|
| Train | 148 |
| Test | 52 |
| Giao nhau | rỗng |
| Tổng | 200 = số video trên đĩa |

### Mã người diễn

Tên video có 5 token khi tách theo `_`, ví dụ `1CM1_1_R__217` →
`['1CM1', '1', 'R', '', '217']` (dấu `__` tạo một token rỗng).

**Mã người = hai token đầu**, ví dụ `1CM1_1`. Bằng chứng:

| Cách nhóm | Số nhóm | Giao nhau train/test |
|---|---|---|
| Token đầu (`1CM1`) | 4 | **4 nhóm bị chia đôi** → sai |
| **Hai token đầu (`1CM1_1`)** | **50** | **rỗng** ✅ |
| Ba token đầu (`1CM1_1_R`) | 50 | rỗng (tương đương, token 3 không đổi trong nhóm) |

Mỗi mã có **đúng 4 video**, 50 × 4 = 200. Split chính thức chia 37 người vào
train và 13 người vào test, không người nào xuất hiện ở cả hai. Đây chính là
thứ luật 8 cần, và nó dùng trực tiếp được ở Phase 4.

`metadata.csv` **không** có cột mã người; nó có `Sex`, `Hand`, `Background`,
`Illumination`, `People in Scene`, `Background Motion` và `Set` (train/test,
khớp với hai file danh sách).

---

## 6. Số frame của video và của nhãn — đã giải quyết 2026-10-01

Bản cũ của mục này (2026-09-29) có danh sách "15 video lệch" và câu hỏi "frame
thừa ở đầu hay ở cuối". **Cả hai đều sai**, và có một lỗi thứ ba mà bản cũ không
thấy. Mọi con số dưới đây đo trên cả 200 video.

### 6.1. Ba cách đếm frame cho cùng một file

| Cách đếm | Lấy từ đâu | Tin được? |
|---|---|---|
| Header AVI | `CAP_PROP_FRAME_COUNT` | = số chunk video trong `idx1`. Danh sách 15 video cũ lập bằng cách này |
| Số chunk trong container | đọc `idx1` của AVI | đúng, nhưng gồm cả chunk "not coded" |
| Số lần `cap.read()` thành công | giải mã tuần tự | **thiếu** đúng các chunk "not coded" |

**Bộ giải mã FFmpeg âm thầm bỏ các chunk 6 byte** — frame "not coded" của XVID,
nghĩa là "giữ nguyên ảnh trước". Đẳng thức `số lần read() + số chunk 6 byte =
số chunk` đúng ở **200/200** video. **101/200** video có loại chunk này, tổng
677 chunk, nhiều nhất 56 chunk một video (`1CM1_4_R__229`).

Hệ quả cho code cũ: `iter_frames` tính `ts = số lần read() / fps`, nên sau mỗi
frame bị bỏ, `ts` của mọi frame sau sớm đi 1/FPS, và chỉ số hàng lệch với chỉ
số frame thật. `CAP_PROP_POS_MSEC` đọc sau mỗi `read()` cho đúng vị trí của
frame trong container (tăng ngặt, có khoảng trống đúng tại chunk 6 byte);
`CAP_PROP_POS_FRAMES` thì chỉ đếm số lần `read()`, cũng sai.

### 6.2. Nhãn IPN đếm frame KHÔNG thống nhất giữa các video

So `t_end` lớn nhất của nhãn với hai cách đếm, cho từng video:

| Nhãn khớp (±1 frame) với | Số video | Ví dụ |
|---|---|---|
| Cả hai — video có ≤ 1 chunk "not coded" | 128 | `1CM1_1_R__219` |
| **Số chunk** (tính cả frame "not coded") | 57 | `1CV12_22_R__115`: 4 445 chunk, 48 bị bỏ, nhãn tới 4 445 |
| **Số lần `read()`** (không tính) | 4 | `1CM1_4_R__229–232`: 3 807 chunk, 56 bị bỏ, nhãn tới 3 751 |
| Không khớp cách nào | 11 | xem 6.3 |

Khớp số đếm chưa phải khớp vị trí, nên đã kiểm vị trí bằng điểm mốc: quanh mỗi
ranh giới `D0X` ↔ cử chỉ, tìm độ dịch `k` làm tín hiệu "có tay" khớp nhãn nhất.
Trên video đã biết khớp (`__219`, `__220`) phép đo cho `k` trong −2…+6 frame —
đó là độ nhiễu của chính phép đo.

| Video | Ánh xạ theo chỉ số hàng | Ánh xạ theo chỉ số container |
|---|---|---|
| `1CV12_22_R__115` | trôi dần 0 → **−42** | **−1…+6** ✅ |
| `1CM1_4_R__229` | **0…+5** ✅ | trôi tới **+61** |

**Quyết định:** `iter_frames` trả `ts` theo vị trí trong container;
`ipn.match_label_frames` chọn cách đếm cho từng video bằng số đo (cách nào cho
tổng số frame gần `t_end` lớn nhất hơn), rồi `ipn.segments_array` đổi chỉ số
frame của nhãn sang chỉ số hàng. Cách đã chọn ghi vào `meta` của `.npz`:
`label_frame_space`, `n_dropped_frames`, `label_frame_diff`.

### 6.3. Mười một video không khớp cách đếm nào — LOẠI

| Video | Split | Số chunk − `t_end` |
|---|---|---|
| `1CM1_1_R__217` | test | +132 |
| `1CM1_1_R__218` | test | +128 |
| `1CM42_3_R__195` | train | +46 |
| `1CM1_2_R__221` | test | +27 |
| `1CM1_2_R__222` | test | +25 |
| `1CM1_2_R__223` | test | +23 |
| `1CM1_2_R__224` | test | +20 |
| `1CM1_3_R__227` | test | +17 |
| `1CM1_3_R__228` | test | +14 |
| `1CM42_13_R__141` | train | +9 |
| `1CM42_11_R__207` | train | +6 |

Ở hai video kiểm được bằng điểm mốc (`__217`, `__218`), **frame thừa không nằm
ở đầu cũng không ở cuối**: độ lệch gần 0 ở đầu video rồi tăng dần tới ~130 frame
ở cuối. Phần lớn frame thừa là frame lặp lại ảnh trước (giống máy quay tụt
FPS). Bỏ K frame giống frame trước nhất thì `__217` còn lệch −6…+10 frame — chưa
đủ tốt, và không kiểm được cho nhóm `1CM1_2` vì ở đó tay hiện gần như suốt
video. Video khớp nhãn cũng có frame lặp, nên đây không thành quy tắc chung.

Phép kiểm "xem frame 1–28 của `__217`" từng được đề xuất sẽ cho **kết luận
sai**: đầu video khớp nhãn thật, nên dễ suy ra "frame thừa ở cuối", trong khi
nửa sau lệch hơn 4 giây.

**Quyết định (người dùng chốt 2026-10-01): loại 11 video này khỏi train/test.**
Chúng vẫn được trích điểm mốc, nhưng `length_mismatch=True` trong `meta`, và
mọi bước dùng nhãn phải bỏ qua chúng. Mất 8 video test (`1CM1_1` ×2, `1CM1_2`
×4, `1CM1_3` ×2) và 3 video train. Test còn 44 video, 12 người; split theo người
vẫn sạch vì loại cả video chứ không tách người.

Ngưỡng `IPN_LENGTH_TOLERANCE = 5` vẫn giữ: 189 video còn lại khớp tới ±1 frame,
11 video bị loại lệch ít nhất 6.

---

## 7. Bảng ánh xạ đề xuất: 14 lớp gốc → 5 lớp của đề tài

| Lớp gốc | Nghĩa | → Lớp đề tài | Chắc chắn? |
|---|---|---|---|
| `G05` Throw left | hất trái | `swipe_left` | ⚠ **cần xác nhận bằng mắt** |
| `G06` Throw right | hất phải | `swipe_right` | ⚠ **cần xác nhận bằng mắt** |
| `G10` Zoom in | zoom in | `zoom_in` | ⚠ **cần xác nhận bằng mắt** |
| `G11` Zoom out | zoom out | `zoom_out` | ⚠ **cần xác nhận bằng mắt** |
| `D0X` Non-gesture | không cử chỉ | `none` | chắc |
| `B0A` Pointing with one finger | chỉ một ngón | `none` | chắc |
| `B0B` Pointing with two fingers | chỉ hai ngón | `none` | chắc |
| `G01` Click with one finger | bấm một ngón | `none` | chắc |
| `G02` Click with two fingers | bấm hai ngón | `none` | chắc |
| `G03` Throw up | hất lên | `none` | chắc — **mẫu âm khó**, vuốt dọc |
| `G04` Throw down | hất xuống | `none` | chắc — **mẫu âm khó**, vuốt dọc |
| `G07` Open twice | xòe tay hai lần | `none` | chắc — **mẫu âm khó nhất cho `zoom_in`** |
| `G08` Double click with one finger | bấm đúp một ngón | `none` | chắc |
| `G09` Double click with two fingers | bấm đúp hai ngón | `none` | chắc |

Không lớp nào bị bỏ: 14/14 lớp gốc đều có chỗ trong bảng, và 10 lớp không dùng
trở thành mẫu âm khó của `none`. Nhãn gốc vẫn được giữ trong `src_labels` để
Phase 8 trả lời được câu hỏi "*loại* `none` nào bị nhận nhầm".

### Bốn chỗ cần bạn xác nhận bằng mắt

**1 và 2 — `G05`/`G06` hướng theo ai?** "Throw left" có thể là tay đi sang trái
**của người diễn**, hoặc sang trái **trên màn hình** — hai thứ ngược nhau. Điều
này không làm sai dấu `SWIPE_LEFT_SIGN` (vì ta đo dấu từ chính dữ liệu IPN),
nhưng nó quyết định cử chỉ nào bạn phải làm để hệ thống hiểu là `swipe_left`.

**3 và 4 — `G10`/`G11` là động tác gì?** Nếu "Zoom in" là **xòe** các ngón ra
thì `open_delta` dương và bảng trên đúng. Nếu "Zoom in" lại là **chụm** các ngón
lại (như thao tác pinch trên điện thoại) thì `open_delta` âm, và hai dòng
`G10`/`G11` phải đổi chỗ cho nhau. Đây là cạm bẫy mà spec cảnh báo riêng. Phép
thử ở Phase 3 sẽ bắt được: trung vị `open_delta` của `zoom_in` **phải dương**.

### Đoạn mẫu để xem — chỉ lấy từ video không bị lệch độ dài

| Lớp gốc | Nghĩa | Video | Frame | Thời điểm | Dài |
|---|---|---|---|---|---|
| G05 | Throw left | `1CM42_11_R__205` | 3658–3686 | 02:01.90–02:02.87 | 1,0 s |
| G05 | Throw left | `1CM42_12_R__157` | 2686–2841 | 01:29.50–01:34.70 | 5,2 s |
| G05 | Throw left | `1CM42_13_R__142` | 1208–1235 | 00:40.23–00:41.17 | 0,9 s |
| G06 | Throw right | `1CM42_11_R__205` | 2546–2612 | 01:24.83–01:27.07 | 2,2 s |
| G06 | Throw right | `1CM42_12_R__157` | 609–660 | 00:20.27–00:22.00 | 1,7 s |
| G06 | Throw right | `1CM42_13_R__142` | 901–937 | 00:30.00–00:31.23 | 1,2 s |
| G10 | Zoom in | `1CM42_11_R__205` | 3472–3532 | 01:55.70–01:57.73 | 2,0 s |
| G10 | Zoom in | `1CM42_12_R__157` | 3814–3897 | 02:07.10–02:09.90 | 2,8 s |
| G10 | Zoom in | `1CM42_13_R__142` | 52–102 | 00:01.70–00:03.40 | 1,7 s |
| G11 | Zoom out | `1CM42_11_R__205` | 587–629 | 00:19.53–00:20.97 | 1,4 s |
| G11 | Zoom out | `1CM42_12_R__157` | 3536–3635 | 01:57.83–02:01.17 | 3,3 s |
| G11 | Zoom out | `1CM42_13_R__142` | 291–340 | 00:09.67–00:11.33 | 1,7 s |

File nằm ở `data/ipn/videos/videos/<tên>.avi`. Mở bằng trình phát bất kỳ và tua
tới mốc thời gian trong bảng.

---

## 8. Kết luận dùng cho Phần B

1. Đọc video bằng `iter_frames` sẵn có; **không** cần mở rộng cho thư mục ảnh.
2. Chỉ số frame trong nhãn là **1-based** và `t_end` **thuộc** đoạn; sang Python
   là `[t_start - 1, t_end)`.
3. Mọi frame đều có nhãn — `D0X` phủ phần xen giữa — nên không cần quy tắc riêng
   cho "frame không thuộc đoạn nào".
4. Mã người diễn = hai token đầu của tên video; split chính thức sạch theo người.
5. FPS đọc theo từng file, không viết cứng.
6. `ts` theo vị trí frame trong container, không theo số lần `read()`; cách
   đếm frame của nhãn chọn theo từng video; 11 video không khớp bị loại
   (mục 6).
