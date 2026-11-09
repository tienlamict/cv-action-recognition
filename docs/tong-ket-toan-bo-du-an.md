# Tổng kết toàn bộ đồ án: đã làm gì, đã học được gì

*Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính, viết cho người chưa học thị giác
máy tính hay học máy*

**Cập nhật:** 2026-11-09. Phạm vi từ Phase 0 tới buổi quay dữ liệu ngày 2026-11-08 (Phase 11).

**Tài liệu này dành cho ai.** Cho người chưa từng học thị giác máy tính (*computer vision*) hay
học máy (*machine learning*). Tài liệu không giả định bạn biết "mạng nơ-ron" hay "pixel" là gì.
Mỗi khái niệm được giải thích ngay chỗ nó xuất hiện lần đầu, trong khung **Khái niệm**, và đi
kèm ví dụ lấy từ chính đồ án này.

**Cách đọc.**

- **Phần 0** tóm tắt cả dự án trong một trang. Đọc phần này nếu bạn chỉ có 5 phút.
- **Phần 1–2** nói bài toán là gì và dự án đã đi qua những giai đoạn nào.
- **Phần 3–9** là phần chính: những kiến thức đã học, xếp theo thứ tự của đường ống xử lý, từ
  ảnh camera tới lệnh bấm phím.
- **Phần 10–12** nói về kết quả cuối, hạn chế, và những bài học lớn nhất.
- **Phụ lục A** là bảng thuật ngữ. **Phụ lục B** chỉ chỗ tìm tài liệu chi tiết hơn.

Mọi con số trong tài liệu đều đo thật trên máy của dự án. Nguồn của từng con số nằm trong các
bản tổng kết theo giai đoạn ở Phụ lục B.

---

## Mục lục

0. [Tóm tắt một trang](#0-tóm-tắt-một-trang)
1. [Bài toán](#1-bài-toán)
2. [Hành trình 13 giai đoạn](#2-hành-trình-13-giai-đoạn)
3. [Ảnh số và video](#3-ảnh-số-và-video-máy-tính-thấy-gì)
4. [Ước lượng tư thế bàn tay](#4-ước-lượng-tư-thế-bàn-tay-từ-ảnh-tới-21-điểm)
5. [Biến 21 điểm thành dữ liệu dùng được](#5-biến-21-điểm-thành-dữ-liệu-dùng-được)
6. [Dữ liệu: IPN Hand, cửa sổ, nhãn, chia tập](#6-dữ-liệu-ipn-hand-cửa-sổ-nhãn-và-chia-tập)
7. [Ba loại mô hình](#7-ba-loại-mô-hình-luật-rừng-ngẫu-nhiên-lstm)
8. [Đánh giá: đo cho đúng](#8-đánh-giá-đo-cho-đúng)
9. [Từ mô hình tới hệ thống thời gian thực](#9-từ-mô-hình-tới-hệ-thống-thời-gian-thực)
10. [Dữ liệu tự quay (Phase 11, đang làm)](#10-dữ-liệu-tự-quay-phase-11-đang-làm)
11. [Kỹ thuật làm dự án học máy](#11-kỹ-thuật-làm-dự-án-học-máy-cho-đáng-tin)
12. [Kết quả cuối, hạn chế, bài học](#12-kết-quả-cuối-hạn-chế-và-bài-học)

---

## 0. Tóm tắt một trang

**Hệ thống làm gì.** Bạn ngồi trước webcam, giơ tay lên và làm cử chỉ. Máy tính nhận ra cử chỉ
rồi bấm phím thay bạn, ví dụ để điều khiển PowerPoint:

| Cử chỉ | Phím | Tác dụng |
|---|---|---|
| Vuốt (hất tay) sang trái | mũi tên phải | slide sau |
| Vuốt sang phải | mũi tên trái | slide trước |
| Mở ba đầu ngón cái, trỏ, giữa đang chụm | `+` | phóng to |
| Chụm ba đầu ngón đó lại | `−` | thu nhỏ |
| Mọi thứ khác | không gì cả | |

**Hệ thống hoạt động thế nào**, trong một hình:

```
 Camera ──► MediaPipe ──► 21 điểm ──► Tiền xử lý ──► Cửa sổ 1,2 giây ──► Mô hình ──► Máy trạng thái ──► Phím
 30 ảnh/s   tìm bàn tay   (x, y) mỗi   lưới 15 Hz,    mỗi 0,2 giây        nhãn +     chỉ bấm khi
                          ảnh          vá lỗ ngắn     chuẩn hoá           độ tin     chắc chắn
```

**Dự án đã làm được gì.**

- Biến 200 video của bộ dữ liệu công khai **IPN Hand** thành chuỗi điểm mốc bàn tay, cắt thành
  37 504 đoạn 1,2 giây có đáp án.
- Dạy và so sánh bốn "bộ não": mô hình luật, rừng ngẫu nhiên, mạng LSTM, và mô hình ghép (LSTM
  lo vuốt, rừng lo zoom).
- Dựng một **máy trạng thái** quyết định khi nào thật sự bấm phím. Nhờ nó, số lệnh nhầm giảm từ
  6,6–30 lần mỗi phút xuống dưới 1 lần mỗi phút.
- Điều khiển được PowerPoint thật: trong 92 giây thử, 19 lệnh đều tới PowerPoint.
- Chạy 46 thí nghiệm có kiểm soát để trả lời câu hỏi "cái gì thật sự có ích".
- Đang quay thêm dữ liệu của người thật (Phase 11) để mô hình hợp với cách làm cử chỉ của người
  dùng.

**Ba điều quan trọng nhất đã học.**

1. **Con số đẹp trên dữ liệu chưa chắc là hệ thống tốt.** Chia dữ liệu sai cách làm điểm đẹp giả
   thêm 0,10–0,15. Chấm theo từng đoạn ngắn thì giấu mất việc hệ thống bấm nhầm 30 lần mỗi phút.
   Phải đo đúng thứ người dùng cảm nhận.
2. **Mô hình học đúng thứ có trong dữ liệu, kể cả những chi tiết ta không muốn.** Người diễn IPN
   luôn gập ngón nhẫn và ngón út khi zoom, nên mô hình học rằng "zoom thì nhẫn, út phải gập". Người
   dùng để hai ngón đó duỗi, và mô hình không nhận ra.
3. **Đo, đừng đoán.** Mọi quy ước (vuốt trái làm toạ độ tăng hay giảm?), mọi ngưỡng, mọi giả
   thuyết về nguyên nhân lỗi đều được đo bằng script. Nhiều lần, số đo cho kết quả ngược với điều
   ai cũng tưởng.

---

## 1. Bài toán

### 1.1. Nhận dạng cử chỉ là gì

> **Khái niệm — Thị giác máy tính.** Lĩnh vực dạy máy tính "hiểu" hình ảnh: trong ảnh có gì, ở
> đâu, đang làm gì. Với con người, nhìn là việc dễ. Với máy tính, một bức ảnh chỉ là một bảng số
> khổng lồ, và rút ra ý nghĩa từ bảng số đó là việc khó.

> **Khái niệm — Học máy.** Thay vì lập trình viên viết từng quy tắc ("nếu tay đi sang trái nhanh
> hơn X thì là vuốt trái"), ta cho máy xem thật nhiều **ví dụ có đáp án** và để máy **tự tìm ra quy
> luật**. Thứ máy tìm ra gọi là **mô hình**. Quá trình cho máy xem ví dụ gọi là **huấn luyện**
> (hay **học**).

Bài toán của dự án là **phân loại**: mỗi lúc, xếp chuyển động của bàn tay vào một trong năm
**lớp** (năm đáp án có thể):

| Chỉ số | Lớp | Nghĩa |
|---|---|---|
| 0 | `none` | không có cử chỉ nào |
| 1 | `swipe_left` | vuốt sang trái |
| 2 | `swipe_right` | vuốt sang phải |
| 3 | `zoom_in` | phóng to |
| 4 | `zoom_out` | thu nhỏ |

### 1.2. Vì sao bài toán này khó hơn tưởng tượng

1. **Cử chỉ là chuyển động, không phải tư thế.** Một tấm ảnh bàn tay mở không cho biết tay đang mở
   ra (zoom in) hay chụm lại (zoom out). Phải nhìn một **đoạn thời gian**.
2. **Lớp `none` khổng lồ và đa dạng.** Phần lớn thời gian tay người dùng không làm cử chỉ: đang
   nói, gãi đầu, chỉ vào màn hình, cầm cốc. Trong dữ liệu đánh giá, 96,5% thời gian là `none`.
   Hệ thống phải **im lặng** trong suốt thời gian đó, và chỉ lên tiếng đúng lúc.
3. **Thời gian thực.** Hệ thống phải trả lời ngay khi cử chỉ vừa xong, không được "chờ xem tương
   lai". Điều này cấm một số kỹ thuật vốn rất hiệu quả khi xử lý video đã quay xong (mục 7.3).
4. **Người dùng làm khác người trong dữ liệu.** Mô hình học từ cách 30 người diễn của IPN làm cử
   chỉ. Người dùng thật làm hơi khác, và mô hình có thể không nhận ra. Đây là sợi chỉ đỏ của cả
   nửa sau dự án (mục 9.3).
5. **Chỉ có CPU.** Dự án chạy trên laptop Windows, không card đồ hoạ. Mọi thứ phải đủ nhanh để xử
   lý 30 ảnh mỗi giây.

### 1.3. Hướng tiếp cận: khung xương thay vì ảnh

Có hai cách lớn để nhận dạng cử chỉ từ video:

- **Cách 1 — học thẳng từ ảnh.** Đưa từng điểm ảnh vào một mạng nơ-ron rất lớn. Mạnh, nhưng cần
  hàng trăm nghìn video để học, cần card đồ hoạ, và dễ học nhầm những thứ không liên quan như màu
  nền hay màu áo.
- **Cách 2 — hai bước** (dự án chọn cách này):
  1. dùng một công cụ có sẵn (MediaPipe) tìm **21 điểm mốc** trên bàn tay trong mỗi ảnh;
  2. chỉ học từ chuyển động của 21 điểm đó.

Cách 2 bỏ đi mọi thứ không liên quan: màu da, nền phòng, ánh sáng. Dữ liệu nhỏ đi hàng nghìn lần:
mỗi ảnh còn 42 con số thay vì 921 600. Nhờ vậy học được trên CPU với vài nghìn ví dụ.

---

## 2. Hành trình 13 giai đoạn

Dự án chia làm 13 giai đoạn (phase), đánh số 0–12, theo chiến lược "**dữ liệu IPN trước, dữ liệu
tự quay khi cần**".

| Phase | Nội dung | Kết quả chính | Trạng thái |
|---|---|---|---|
| 0 | Khung dự án | Cây thư mục, `config.py` chứa mọi hằng số, môi trường Python tự kích hoạt | ✅ |
| 1 | Thu nhận điểm mốc | 21 điểm bám theo tay trên webcam; ghi ra file | ✅ |
| 2 | Tiền xử lý, chuẩn hoá, đặc trưng | Lưới 15 Hz, vá lỗ, chuẩn hoá theo lòng bàn tay, 15 đặc trưng | ✅ |
| 3 | Trích điểm mốc IPN, đo quy ước hướng | 200/200 video; phát hiện và sửa lỗi lệch frame; đo dấu của vuốt trái | ✅ |
| 4 | Cửa sổ, tăng cường, chia tập theo người | 37 504 cửa sổ; chia 30/7/13 người | ✅ |
| 5 | Mô hình luật, demo đầu tiên | Chạy được từ webcam tới màn hình; macro-F1 0,231 | ✅ |
| 6 | Rừng ngẫu nhiên | macro-F1 0,436; tìm ra "mô hình coi gì là cú vuốt" | ✅ |
| 7 | LSTM | macro-F1 0,556; mô hình ghép | ✅ |
| 8 | Đánh giá hai mức, 46 thí nghiệm | Bảy bảng khảo sát; đo đúng thứ người dùng cảm nhận | ✅ |
| 9 | Máy trạng thái kích hoạt | Lệnh nhầm từ hàng chục xuống khoảng 1 mỗi phút | ✅ |
| 10 | Demo hoàn chỉnh, đo trên webcam | Điều khiển PowerPoint thật; sáu vòng tối ưu | ✅ phần lớn; còn đo độ trễ thủ công, video demo |
| 11 | Dữ liệu tự quay | Bật 2026-11-06; đã quay p01, p02, p03 | 🟡 đang làm |
| 12 | Tái lập và bàn giao | `run_all.py`, ghim phiên bản thư viện, README | 🟡 phần lớn; còn phép thử tái lập trên máy sạch |

**Tập kiểm tra cuối (test) chưa bị mở lần nào.** File nhật ký `results/TEST_USED.log` chưa tồn
tại. Lý do của việc giữ nguyên tắc này ở mục 6.5.

---

## 3. Ảnh số và video: máy tính thấy gì

### 3.1. Ảnh là một bảng số

> **Khái niệm — Pixel và ảnh số.** Ảnh số là một lưới các ô vuông nhỏ gọi là **pixel** (điểm ảnh).
> Mỗi pixel có ba con số từ 0 đến 255, cho biết độ đậm của ba màu cơ bản: đỏ, xanh lá, xanh lam.
> Trộn ba màu theo tỉ lệ khác nhau cho ra mọi màu khác.

Webcam của dự án chụp ảnh 640 × 480 pixel. Trong Python, một ảnh là một **mảng** (bảng số nhiều
chiều) kích thước `(480, 640, 3)`:

- 480 hàng (chiều cao) — **chiều cao đứng trước**;
- 640 cột (chiều rộng);
- 3 kênh màu.

Tổng cộng 921 600 con số cho một ảnh.

**Hệ toạ độ ảnh** có gốc ở **góc trên bên trái**: trục `x` đi sang phải, trục `y` đi **xuống**
(ngược với đồ thị toán học ở trường). Một chỗ dễ nhầm: khi đọc mảng ta viết `[y, x]` (hàng trước,
cột sau), nhưng khi vẽ bằng thư viện OpenCV ta truyền `(x, y)`.

### 3.2. BGR và RGB: lỗi im lặng phổ biến nhất

Thư viện đọc camera OpenCV lưu ba kênh màu theo thứ tự **Xanh lam – Xanh lá – Đỏ** (BGR).
MediaPipe lại cần thứ tự **Đỏ – Xanh lá – Xanh lam** (RGB).

Quên đổi thì **không có thông báo lỗi nào**. MediaPipe vẫn chạy, chỉ là nó nhìn thấy làn da màu
xanh lam và tìm bàn tay kém đi. Đây là kiểu lỗi nguy hiểm nhất trong học máy: chương trình không
hỏng, chỉ âm thầm kém đi.

**Cách dự án phòng lỗi:** đổi kênh màu ở **đúng một chỗ** trong toàn bộ mã nguồn, và đặt tên biến
`frame_bgr` / `frame_rgb` để nhìn là thấy đang cầm loại nào.

### 3.3. Video và tốc độ khung hình

> **Khái niệm — Video và FPS.** Video là một dãy ảnh chiếu nhanh liên tiếp. **FPS** (*frames per
> second*) là số ảnh mỗi giây. Webcam của dự án chạy khoảng 30 FPS: cứ khoảng 33 mili-giây có một
> ảnh mới.

**Bài học 1 — FPS của webcam không phải hằng số.** Phòng tối thì camera phải mở cửa sập lâu hơn
cho đủ sáng, và FPS tụt. Nếu tính thời gian bằng "số thứ tự ảnh chia 30", một cử chỉ quay trong
phòng tối sẽ trông nhanh hơn thật. Mà mô hình lại đo tốc độ tay. Vì vậy:

- mỗi ảnh webcam được gắn **mốc thời gian thật** (đọc đồng hồ máy tính) ngay lúc nhận;
- việc này không thể bổ sung sau khi đã quay, nên phải làm từ đầu.

**Bài học 2 — đo FPS cho đúng.** Bỏ 3 giây đầu (camera còn tự chỉnh sáng), rồi báo hai con số:

- **FPS trung bình;**
- **FPS "1% thấp nhất"**: mức FPS mà chỉ 1% thời gian tệ hơn. FPS trung bình cao vẫn có thể giấu
  những lần hình bị giật.

**Bài học 3 — bộ giải mã video có thể âm thầm bỏ ảnh.** Đây là phát hiện lớn ở Phase 3, kể chi
tiết ở mục 6.2.

### 3.4. Lật ảnh: gương cho người, nguyên bản cho máy

Khi nhìn webcam, ai cũng muốn thấy ảnh **như soi gương**: giơ tay phải thì tay trên màn hình cũng
ở bên phải. Nhưng ảnh camera gốc thì ngược lại.

Dự án đặt một quy ước cứng:

| Ảnh | Lật? | Vì sao |
|---|---|---|
| Đưa **vào mô hình** | **Không** | Phải cùng quy ước với dữ liệu huấn luyện. Lật ở chỗ này mà không lật ở chỗ kia là cách chắc chắn nhất để hệ thống chạy ngược chiều |
| Đưa **ra màn hình** | **Lật gương** | Người dùng cần ảnh gương để điều khiển tự nhiên |

Hệ quả: khi vẽ điểm lên ảnh đã lật, toạ độ ngang cũng phải lật thành `1 − x`. Việc lật chỉ xảy ra
ở đúng một hàm, và có kiểm thử tự động đảm bảo ảnh gốc không bao giờ bị sửa.

---

## 4. Ước lượng tư thế bàn tay: từ ảnh tới 21 điểm

### 4.1. Điểm mốc là gì

> **Khái niệm — Ước lượng tư thế (pose estimation).** Bài toán tìm vị trí các **điểm mốc**
> (*keypoint, landmark*) trên cơ thể trong ảnh: khớp vai, khuỷu tay, đầu ngón tay… Kết quả là một
> "hình que" mô tả tư thế. Với bàn tay, MediaPipe tìm 21 điểm.

```
            8   12  16  20        ← đầu ngón (TIPS = 4, 8, 12, 16, 20)
            |   |   |   |
            7   11  15  19
            |   |   |   |
     4      6   10  14  18
      \     |   |   |   |
       3    5---9---13--17        ← gốc ngón (5, 9, 13, 17)
        \   |  /       /
         2  | /       /
          \ |/       /
           1        /
            \      /
             \    /
               0                  ← cổ tay (WRIST)
```

| Ngón | Các điểm, từ gốc tới đầu ngón |
|---|---|
| Cổ tay | 0 |
| Cái | 1, 2, 3, **4** |
| Trỏ | 5, 6, 7, **8** |
| Giữa | **9**, 10, 11, **12** |
| Nhẫn | 13, 14, 15, **16** |
| Út | 17, 18, 19, **20** |

Đoạn từ cổ tay (0) tới gốc ngón giữa (9) được dùng làm **thước đo "một lòng bàn tay"** (mục 5.3).

### 4.2. MediaPipe tìm bàn tay thế nào: kiến trúc hai tầng

MediaPipe Hand Landmarker (của Google) là một file mô hình 7,8 MB chứa **hai mạng nơ-ron con**:

1. **Bộ phát hiện lòng bàn tay** quét cả ảnh, tìm vùng có bàn tay. Nó tìm **lòng bàn tay** chứ
   không tìm cả bàn tay, vì lòng bàn tay là phần cứng, ít đổi hình. Năm ngón tay thì co duỗi đủ
   kiểu nên khó tìm hơn nhiều.
2. **Mô hình điểm mốc** chỉ nhìn vào vùng đã cắt quanh bàn tay, và tính ra vị trí 21 điểm.

**Chế độ VIDEO.** Ở chế độ này, ảnh sau dùng vị trí bàn tay của ảnh trước để cắt vùng, **bỏ qua**
bộ phát hiện. Như vậy nhanh hơn nhiều. Khi mất dấu (tay ra khỏi khung, hoặc vuốt quá nhanh làm ảnh
nhoè), bộ phát hiện phải chạy lại, và đó là lúc điểm mốc biến mất vài ảnh. Cú vuốt nhanh vì thế hay
bị "mất tay" vài khoảnh khắc, và điều này ảnh hưởng tới thiết kế ở mục 9.2.

**Ba ngưỡng tin cậy**, mỗi ngưỡng ứng với một chỗ trong kiến trúc trên:

| Ngưỡng | Quyết định điều gì |
|---|---|
| Phát hiện | Bộ phát hiện lòng bàn tay chấp nhận một vùng là bàn tay |
| Hiện diện | Mô hình điểm mốc tin là vẫn còn bàn tay trong vùng; dưới ngưỡng thì chạy lại bộ phát hiện |
| Bám | Việc bám theo từ ảnh trước được coi là thành công |

**Một chi tiết kỹ thuật:** chế độ VIDEO đòi mốc thời gian **tăng ngặt** (không bao giờ hai ảnh
trùng mốc). Dự án tự đẩy mốc lên 1 mili-giây khi gặp hai ảnh trùng.

### 4.3. Chỉ dùng toạ độ 2D

MediaPipe còn trả thêm độ sâu `z` và toạ độ 3D tính bằng mét. Nhưng **đoán độ sâu từ một camera là
việc không đáng tin**: một bàn tay nhỏ có thể là tay ở xa, hoặc tay nhỏ thật. Dự án bỏ hẳn, chỉ
dùng `(x, y)`.

**Nhãn tay trái/phải** của MediaPipe cũng không được dùng, vì nó giả định ảnh đã lật gương, mà dự
án không lật (mục 3.4).

### 4.4. Toạ độ chuẩn hoá và tỉ lệ khung hình

MediaPipe trả `x` và `y` trong khoảng 0 tới 1: `x = 0,5` nghĩa là giữa chiều ngang ảnh. Nhưng ảnh
640 × 480 **không vuông**: một đơn vị `x` dài 640 pixel, còn một đơn vị `y` chỉ dài 480 pixel. Tính
khoảng cách hay góc trên toạ độ này sẽ bị méo, như vẽ hình tròn trên giấy kẻ ô chữ nhật.

**Cách làm:** lưu toạ độ chuẩn hoá kèm kích thước ảnh, rồi **đổi sang pixel trước mọi phép tính
hình học**. Đây là bước đầu tiên của đường ống xử lý (mục 5.1). Camera của dự án cũng được đặt cố
định ở 640 × 480, trùng tỉ lệ với video IPN, để loại hẳn một nguồn khác biệt.

### 4.5. Khi không thấy tay: ghi NaN, không bỏ ảnh

> **Khái niệm — NaN.** Viết tắt của *Not a Number*, một giá trị đặc biệt nghĩa là "không có số
> liệu". Khác với số 0: toạ độ 0 nghĩa là "tay ở mép ảnh", còn NaN nghĩa là "không biết tay ở
> đâu".

Khi MediaPipe không thấy tay trong một ảnh, dự án **vẫn ghi dòng đó**, kèm mốc thời gian, toạ độ
để NaN. Nếu bỏ hẳn ảnh đó, trục thời gian bị đứt và các bước sau sẽ âm thầm nối liền hai đầu khoảng
trống như thể tay đã đi thẳng từ chỗ này sang chỗ kia. Giữ NaN thì thông tin "lúc này không thấy
tay" còn nguyên, và bước sau tự quyết vá hay không (mục 5.2).

### 4.6. Đo giới hạn của bộ ước lượng: độ rung

Ngay cả khi tay đứng yên hoàn toàn, điểm mốc vẫn **rung** nhẹ từ ảnh này sang ảnh khác, vì mạng nơ-ron
không cho ra đúng một con số mỗi lần. Đo độ rung này để làm gì? Để biết **bao nhiêu chuyển động là
nhiễu**, và để tạo nhiễu giả có cùng độ lớn khi tăng cường dữ liệu (mục 6.7).

> **Khái niệm — Độ lệch chuẩn (σ, sigma).** Đo mức "tản mát" của một dãy số quanh giá trị trung
> bình. Dãy 5, 5, 5, 5 có σ = 0. Dãy 1, 9, 2, 8 có σ lớn.

Hai cách đo độ rung:

- **Độ lệch chuẩn của toạ độ theo thời gian**, khi tay đứng yên.
- **Độ lệch chuẩn của chênh lệch giữa hai ảnh liền nhau, chia cho √2.** Vì sao √2: nếu mỗi ảnh có
  nhiễu độc lập độ lệch chuẩn σ, thì hiệu của hai ảnh có độ lệch chuẩn σ√2. Cách này không bị ảnh
  hưởng khi cả bàn tay trôi chậm.

Kết quả đo trên IPN: **σ = 0,0159 lòng bàn tay** (mục 6.7 kể cách đo và một cái bẫy đã tránh).

---

## 5. Biến 21 điểm thành dữ liệu dùng được

### 5.1. Một đường ống cố định cho mọi nguồn

Dữ liệu đến từ ba nguồn: video IPN, video tự quay, và webcam lúc chạy thật. Quy tắc quan trọng
nhất của dự án: **cả ba đi qua CÙNG các hàm, theo CÙNG thứ tự**:

```
1. đổi toạ độ sang pixel
2. đưa về lưới thời gian đều 15 Hz
3. vá lỗ hổng ngắn
4. cắt cửa sổ 1,2 giây
5. [tăng cường dữ liệu — chỉ khi huấn luyện]
6. chuẩn hoá cửa sổ
7. tính đặc trưng, hoặc đưa thẳng vào LSTM
```

**Vì sao quan trọng.** Nếu có hai bản "gần giống nhau", một cho dữ liệu học và một cho webcam, thì
sớm muộn chúng sẽ lệch nhau một chút. Mô hình học trên một kiểu dữ liệu và chạy trên kiểu khác, và
không có gì báo lỗi. Trong học máy, lỗi này có tên: **lệch giữa lúc học và lúc dùng**
(*training–serving skew*).

### 5.2. Lấy mẫu lại về lưới đều và vá lỗ

Ảnh từ webcam đến không đều nhau (mục 3.3). Mô hình lại cần các bước thời gian cách đều. Vì vậy
mọi chuỗi được **lấy mẫu lại** về lưới đều 15 bước mỗi giây (15 Hz).

> **Khái niệm — Nội suy.** Ước lượng giá trị ở giữa hai điểm đã biết. Ví dụ: lúc 0,00 giây cổ tay
> ở x = 100, lúc 0,10 giây ở x = 120, thì lúc 0,05 giây ước lượng ở x = 110.

Ba quy tắc:

1. **Chỉ nội suy giữa hai ảnh cùng có tay.** Không bao giờ nối qua khoảng mất tay.
2. **Lỗ hổng ngắn (tối đa 3 bước, tức 0,2 giây) và có đủ hai đầu thì vá.** Mất tay một chút khi vuốt
   nhanh là chuyện thường; vá lại thì cú vuốt liền mạch.
3. **Lỗ dài hơn giữ nguyên NaN**, vì mất tay lâu là tín hiệu thật (tay đã ra khỏi khung).

Vì sao 15 Hz mà không phải 30? Một cử chỉ kéo dài khoảng 2 giây. 15 bước mỗi giây đủ mô tả chuyển
động, chuỗi ngắn hơn nên học nhanh hơn, và webcam ở phòng tối (FPS tụt) vẫn theo kịp.

### 5.3. Chuẩn hoá: làm cho tay gần và tay xa trông như nhau

**Vấn đề.** Cùng một cú vuốt, tay ở gần camera thì đi 300 pixel, tay ở xa chỉ đi 100 pixel. Tay ở
góc trái ảnh và tay ở giữa ảnh có toạ độ khác hẳn nhau. Mô hình không nên phải học lại cú vuốt cho
từng khoảng cách và từng vị trí.

> **Khái niệm — Chuẩn hoá.** Biến đổi dữ liệu để loại bỏ những khác biệt **không liên quan** tới
> đáp án, giữ lại những khác biệt **có liên quan**.

**Cách dự án chuẩn hoá một cửa sổ 1,2 giây:**

- **Gốc toạ độ** đặt ở **cổ tay của bước đầu tiên** trong cửa sổ.
- **Đơn vị đo** là **khoảng cách cổ tay → gốc ngón giữa ở bước đầu tiên**: "một lòng bàn tay".
- Cùng một gốc và một đơn vị cho **mọi bước** trong cửa sổ.

Sau chuẩn hoá, câu "cổ tay đi 2 lòng bàn tay sang trái" có cùng nghĩa dù tay ở gần hay xa, ở góc
nào của ảnh.

**Vì sao gốc ở bước đầu, không ở từng bước?** Nếu mỗi bước đều trừ đi vị trí cổ tay **của chính
bước đó**, cổ tay luôn nằm ở gốc, và **cú vuốt biến mất**: chuyển động của cổ tay chính là cú vuốt.
Phase 8 đã đo điều này (Bảng 2, mục 8.6): với rừng ngẫu nhiên, gốc từng bước làm F1 của hai lớp vuốt
sập còn khoảng một phần ba, và số cú vuốt bị đoán ngược hướng tăng gần gấp ba.

**Kiểm tra lòng bàn tay.** Khi bàn tay nghiêng cạnh về phía camera, khoảng cách cổ tay → gốc ngón
giữa trên ảnh trở nên rất ngắn. Dùng nó làm đơn vị thì mọi khoảng cách khác phình to bất thường
(từng gặp đặc trưng lớn tới 30 lòng bàn tay). Dự án từ chối cửa sổ có lòng bàn tay ở bước đầu ngắn
hơn một nửa trung vị của chính cửa sổ đó. Ngưỡng 0,5 được chọn bằng đo: loại 2% cửa sổ và xoá các
giá trị ngoại lai.

### 5.4. Đặc trưng: tóm tắt một cửa sổ bằng vài con số

> **Khái niệm — Đặc trưng (feature).** Một con số tóm tắt một khía cạnh có ý nghĩa của dữ liệu.
> Thay vì đưa cho mô hình 18 bước × 21 điểm × 2 toạ độ = 756 con số thô, ta tính sẵn vài con số mà
> con người biết là quan trọng: "cổ tay đi ngang bao xa", "ngón cái và trỏ mở ra bao nhiêu". Việc
> chọn và tính đặc trưng gọi là **trích xuất đặc trưng** (*feature engineering*).

Mô hình luật và rừng ngẫu nhiên dùng **15 đặc trưng**, chia năm nhóm. "Đầu" và "cuối" là trung bình
của 3 bước đầu và 3 bước cuối, để bớt nhạy với nhiễu.

| Nhóm | Đặc trưng | Ý nghĩa |
|---|---|---|
| **Độ xòe bàn tay** | `open_start`, `open_end`, `open_delta`, `open_range`, `open_trend` | Trung bình khoảng cách 5 đầu ngón tới cổ tay **của cùng bước**: lúc đầu, lúc cuối, thay đổi, biên độ, xu hướng |
| **Độ mở cái–trỏ** | `pinch_delta`, `pinch_range` | Khoảng cách đầu ngón cái tới đầu ngón trỏ: thay đổi (mở ra dương, chụm lại âm), biên độ |
| **Quỹ đạo cổ tay** | `dx`, `dy`, `max_vx`, `mean_vx`, `max_vy` | Dời ngang, dời dọc; tốc độ ngang lớn nhất, trung bình; tốc độ dọc lớn nhất |
| **Hình dạng đường đi** | `straightness`, `horiz_ratio` | Đường đi thẳng hay vòng vèo; đi ngang nhiều hay dọc nhiều |
| **Chất lượng** | `presence` | Tỉ lệ bước có thấy tay |

**Vài nguyên tắc khi thiết kế đặc trưng:**

- **Bất biến với thứ không liên quan.** Độ xòe đo tới cổ tay **của cùng bước**, nên không đổi khi cả
  bàn tay dời đi. Nhờ vậy nó tách được zoom (tay đứng chỗ, ngón đổi) với vuốt (cả tay dời).
- **Không bao giờ rỗng.** Đặc trưng không tính được thì thay bằng một giá trị an toàn, vì mô hình
  không xử lý được NaN.
- **Không viết cứng chiều.** Đặc trưng `dx` có dấu, nhưng phần tính đặc trưng **không quyết định**
  dấu dương là trái hay phải. Việc đó dành cho một hằng số đã đo (mục 5.5).

**Hai loại đặc trưng bổ sung, dùng cho phân tích:**

- **Độ duỗi từng ngón** = khoảng cách đầu ngón → cổ tay, chia khoảng cách gốc ngón → cổ tay. Ngón
  gập vào lòng bàn tay cho khoảng 0,5; ngón duỗi thẳng cho khoảng 1,3–1,5. Đây là công cụ tìm ra
  nguyên nhân zoom thất bại trên tay người dùng (mục 9.3).
- **Góc khớp:** góc gập ở khớp giữa của từng ngón. Thêm 10 đặc trưng góc khớp giúp rừng ngẫu nhiên
  giảm gần một nửa lỗi lớn nhất (mục 8.7).

### 5.5. Quy ước thì đo, không đoán

**Câu hỏi.** "Vuốt sang trái" làm toạ độ `x` tăng hay giảm?

Câu trả lời phụ thuộc hai quy ước: ảnh có lật không, và "trái" là trái của người làm hay trái của
ảnh. Suy luận thì ra: với ảnh không lật, tay đi sang trái của người làm sẽ đi về phía bên phải của
ảnh, tức `x` tăng. Nhưng **dự án không dùng suy luận đó**. Nếu suy luận sai, mô hình học ngược
chiều, và không có gì báo lỗi.

**Cách làm.**

1. Hằng số `SWIPE_LEFT_SIGN` để trống (`None`) từ đầu. Mọi chỗ dùng nó **dừng chương trình ngay** nếu
   nó chưa được đo.
2. Script `measure_direction.py` đo trên 189 đoạn vuốt của IPN: trung vị `dx` của `swipe_left` là
   **+0,456**, của `swipe_right` là **−0,534**. Hai lớp trái dấu, đúng như phải có.
3. Điền `SWIPE_LEFT_SIGN = 1` vào cấu hình, kèm một câu mô tả cách đo trong README.
4. Phase 10 kiểm lại trên webcam: vuốt sang trái của người dùng ra `swipe_left`. Đúng chiều.

Cùng tinh thần đó, mọi hằng số khác (độ nhiễu σ, ba ngưỡng của mô hình luật) đều do script đo rồi in
ra để dán vào cấu hình. Không hằng số nào là "số ma thuật" tự đặt.

---

## 6. Dữ liệu: IPN Hand, cửa sổ, nhãn và chia tập

### 6.1. Bộ dữ liệu IPN Hand

> **Khái niệm — Bộ dữ liệu có nhãn.** Một tập ví dụ, mỗi ví dụ kèm **nhãn** là đáp án đúng do con
> người gán. Học máy kiểu "học từ ví dụ có đáp án" gọi là **học có giám sát** (*supervised
> learning*).

IPN Hand là bộ dữ liệu công khai về cử chỉ bàn tay cho tương tác không chạm:

| Thuộc tính | Giá trị |
|---|---|
| Số video | 200 (50 người, mỗi người 4 video) |
| Tổng số ảnh | 800 505 |
| Định dạng | `.avi`, 640 × 480, 30 FPS |
| Số đoạn đã gán nhãn | 5 649 |
| Số loại cử chỉ | 14, gồm một loại "không cử chỉ" |
| Điều kiện quay | nền trơn / nền rối; ánh sáng ổn định / sáng / tối |

**Ánh xạ 14 loại về 5 lớp của dự án:** "hất trái" (`G05`) thành `swipe_left`, "hất phải" (`G06`)
thành `swipe_right`, `G10` thành `zoom_in`, `G11` thành `zoom_out`. Mười loại còn lại (chỉ trỏ một
ngón, hai ngón, bấm, hất lên, hất xuống, xòe tay hai lần, không cử chỉ…) đều gộp vào `none`. Nhờ
vậy lớp `none` có sẵn rất nhiều **mẫu âm khó**: những chuyển động trông gần giống cử chỉ nhưng
không phải.

### 6.2. Câu chuyện thám tử: video và nhãn lệch nhau

Khi bắt đầu dùng IPN, có 15 video mà số ảnh không khớp với nhãn. Điều tra cho ra kết quả bất ngờ:

1. **Đếm số ảnh theo ba cách độc lập** cho cả 200 video: số ghi trong đầu file, số "khối dữ liệu"
   trong chỉ mục file AVI, và số ảnh giải mã được thật.
2. **Phát hiện một đẳng thức đúng ở mọi video:** số ảnh giải mã + số khối 6 byte = tổng số khối.
3. **Kết luận:** chuẩn nén XVID có loại khối 6 byte nghĩa là "giữ nguyên ảnh trước". Bộ giải mã
   FFmpeg **âm thầm bỏ qua** những khối đó. 101 trên 200 video có, tổng cộng 677 ảnh bị bỏ.
4. Chương trình cũ đếm số lần đọc ảnh để tính thời gian, nên sau mỗi ảnh bị bỏ, thời gian lệch thêm
   một chút. **Sửa:** lấy thời gian theo vị trí của ảnh trong file.
5. **Nhãn của IPN lại không thống nhất:** có video đếm cả ảnh bị bỏ, có video không. Dự án chọn cách
   đếm cho từng video bằng số đo, rồi **kiểm vị trí bằng điểm mốc**: tay thường rời khung trong đoạn
   không cử chỉ, nên tín hiệu "có tay" đổi trạng thái gần ranh giới các đoạn nhãn. Cách đếm đúng
   cho độ lệch nằm trong mức nhiễu của phép đo (−2…+6 ảnh); cách sai trôi dần tới 40–60 ảnh.
6. **11 video không khớp cách nào bị loại.** Danh sách "15 video" ban đầu hoá ra sai, vì lập bằng một
   con số không đáng tin trong đầu file.

**Bài học:** dữ liệu "chuẩn" công khai cũng có lỗi. Phải kiểm bằng nhiều cách độc lập, và kiểm **vị
trí** chứ không chỉ kiểm **số đếm**.

### 6.3. Cửa sổ trượt tính bằng giây

> **Khái niệm — Cửa sổ trượt.** Cắt chuỗi dài thành các đoạn ngắn cố định, chồng lên nhau. Như nhìn
> qua một khe hở trượt dọc cuộn phim.

- Mỗi cửa sổ dài **1,2 giây**, tức 18 bước ở 15 Hz.
- Cửa sổ trượt mỗi **0,2 giây** (3 bước). Lúc chạy thật, cứ 0,2 giây hệ thống hỏi một lần: "1,2 giây
  vừa qua có cử chỉ không?" Mỗi giây có 5 câu trả lời.
- **Tính bằng giây, không bằng số ảnh**, để video 30 FPS và webcam ở FPS khác vẫn cho cùng một cửa sổ
  thời gian.
- Cửa sổ chỉ cắt trong từng video, không bao giờ bắc cầu qua hai video.
- Loại cửa sổ có tay ở dưới 70% số bước, hoặc mất tay ngay bước đầu (không chuẩn hoá được).

Vì sao 1,2 giây? Phase 8 đã so 0,8 / 1,2 / 1,6 giây (Bảng 3, mục 8.6). LSTM tốt nhất ở 1,2 giây cho
cả vuốt lẫn zoom.

### 6.4. Gán nhãn cho cửa sổ: neo vào khoảnh khắc chính

Nhãn của IPN đánh dấu cả đoạn cử chỉ, khoảng 2 giây, gồm chuẩn bị, động tác chính (chừng 0,3 giây
với cú vuốt) và thu tay. Một cửa sổ 1,2 giây cắt qua đoạn đó có thể chỉ chứa phần chuẩn bị. Gán nhãn
"vuốt" cho cửa sổ ấy là dạy sai.

**Luật đầu tiên trong thiết kế** ("cửa sổ mang nhãn của lớp chiếm 60% thời gian") cho kết quả tệ: đo
trên train, 49% cửa sổ dương **không chứa động tác chính**.

**Luật dự án dùng:**

1. Với mỗi đoạn cử chỉ, tìm **khoảnh khắc chính**: bước mà tín hiệu thay đổi nhanh nhất. Với vuốt là
   vị trí ngang của cổ tay; với zoom là khoảng cách cái–trỏ.
2. Cửa sổ là **dương** (mang nhãn cử chỉ) khi khoảnh khắc chính nằm cách hai mép cửa sổ ít nhất 3
   bước.
3. Cửa sổ chạm vào đoạn cử chỉ mà **không** chứa khoảnh khắc chính thì **bỏ hẳn**, không gán `none`,
   vì nó mơ hồ.
4. Cửa sổ không chạm cử chỉ nào là `none`.

**Một điều cần nhớ:** nhãn được tính từ cả đoạn video đã quay xong, tức "nhìn thấy tương lai". Điều
đó **không vi phạm** yêu cầu thời gian thực, vì nhãn chỉ là đáp án để chấm, giống chính file nhãn
của IPN. Mô hình không bao giờ thấy nó.

### 6.5. Ba tập dữ liệu và vì sao chia theo người

> **Khái niệm — Tập huấn luyện, kiểm định, kiểm tra.** Dữ liệu chia làm ba phần, giống việc học ở
> trường:
>
> - **Tập huấn luyện** (*train*): **bài tập về nhà**. Máy học từ đây.
> - **Tập kiểm định** (*validation, val*): **đề thi thử**. Dùng để chấm điểm và chọn cách làm trong
>   quá trình phát triển.
> - **Tập kiểm tra** (*test*): **đề thi thật, niêm phong**. Chỉ mở **đúng một lần**, ở cuối dự án.

**Vì sao test phải niêm phong.** Nếu nhìn kết quả trên test rồi sửa mô hình, rồi lại nhìn, rồi lại
sửa, thì mô hình dần "hợp đề", và con số cuối đẹp giả. Dự án có **khoá kỹ thuật**: script đánh giá
từ chối mở test nếu không ghi rõ `--final`, và mỗi lần mở để lại một dòng nhật ký. Đến nay chưa mở
lần nào.

**Vì sao chia theo người, không chia ngẫu nhiên.**

- Mỗi người làm cử chỉ theo một kiểu riêng. Nếu cùng một người có mặt ở cả bài tập lẫn đề thi, máy có
  thể "nhận ra người quen" thay vì nhận ra cử chỉ.
- Tệ hơn: các cửa sổ liền nhau chồng lên nhau 1,0 trên 1,2 giây, gần như giống hệt nhau. Chia ngẫu
  nhiên theo cửa sổ thì gần như mọi cửa sổ trong đề thi có "anh em sinh đôi" trong bài tập.

> **Khái niệm — Rò rỉ dữ liệu (data leakage).** Khi thông tin của đề thi lọt vào bài tập về nhà, dù
> vô tình. Điểm thi cao giả tạo, và mô hình thất bại khi gặp dữ liệu thật.

**Dự án đã đo mức rò rỉ** (Bảng 4 của Phase 8):

| | Rừng ngẫu nhiên | LSTM |
|---|---|---|
| Chia theo người (đúng) | 0,436 | 0,556 |
| Chia ngẫu nhiên theo cửa sổ (rò rỉ) | 0,540 | 0,701 |
| Điểm đẹp giả thêm | **+0,104** | **+0,145** |

Chia sai làm điểm tăng **nhiều hơn cả việc đổi từ rừng sang LSTM**. Đây là một trong những bài học
quan trọng nhất của dự án.

**Cách chia thật:** 30 người train, 7 người val (chọn ngẫu nhiên có cố định "hạt giống" từ phần
train chính thức của IPN), 13 người test (đúng phần test chính thức, để so được với công bố khác).
Kiểm tra tự động: không người nào có mặt ở hai tập.

### 6.6. Mất cân bằng lớp

> **Khái niệm — Mất cân bằng lớp.** Khi một lớp có nhiều ví dụ hơn hẳn các lớp khác. Mô hình dễ
> "lười": đoán lớp đông nhất là đã đúng phần lớn thời gian.

Trong IPN, lớp `none` chiếm khoảng 96–97% số cửa sổ.

| Tập | Số cửa sổ | Tỉ lệ `none` | Mỗi lớp cử chỉ |
|---|---|---|---|
| train (sau lấy mẫu con) | 3 326 | 50% | ~415 |
| val (giữ nguyên tự nhiên) | 11 038 | 96,5% | ~96 |
| test (giữ nguyên tự nhiên) | 23 140 | 97,2% | ~160 |

Ba cách xử lý:

1. **Lấy mẫu con lớp `none`, chỉ ở train**, xuống còn 50%. Ngân sách được chia đều cho các loại `none`
   gốc theo kiểu "rót nước": loại nào ít hơn phần chia thì lấy hết, phần dư dồn cho loại khác. Nhờ vậy
   các loại `none` hiếm mà khó (xòe tay, hất lên) không bị lấn át bởi loại đông (chỉ trỏ).
2. **Val và test giữ nguyên tỉ lệ tự nhiên**, để con số đánh giá phản ánh đúng thực tế: ngoài đời,
   phần lớn thời gian ta không làm cử chỉ.
3. **Trọng số lớp** khi học: một lỗi trên ví dụ cử chỉ bị tính nặng hơn (khoảng 4 lần với LSTM) một
   lỗi trên ví dụ `none`.

Phase 8 đã thử chia ngân sách `none` theo tỉ lệ tự nhiên thay vì chia đều: báo nhầm khi chỉ trỏ giảm
mạnh, nhưng zoom kém đi, và tổng điểm không khá hơn. Lỗi chỉ chuyển từ chỗ này sang chỗ khác.

### 6.7. Tăng cường dữ liệu

> **Khái niệm — Tăng cường dữ liệu (data augmentation).** Tạo thêm ví dụ huấn luyện bằng cách
> **biến đổi** ví dụ có sẵn **mà không làm đổi đáp án**. Giống cho học sinh xem cùng một bài toán
> viết theo nhiều cách, để các em hiểu bản chất thay vì thuộc lòng.

Mỗi phép biến đổi phải trả lời câu hỏi: **"có làm đổi lớp không?"**

| Phép | Đổi lớp? | Mô phỏng điều gì |
|---|---|---|
| Lật ngang | Vuốt trái ↔ vuốt phải; zoom giữ nguyên | Người làm bằng tay kia, hướng ngược lại |
| Xoay nhẹ | Không | Camera hoặc cổ tay hơi nghiêng |
| Co giãn **đổi dần** theo thời gian | Không | Tay tiến lại gần hoặc lùi xa camera trong lúc làm |
| Co giãn thời gian | Không | Người làm nhanh hơn hoặc chậm hơn |
| Xoá 1–3 bước rồi vá | Không | MediaPipe mất tay vài khoảnh khắc |
| Nhiễu Gauss σ = 0,0159 | Không | Độ rung của điểm mốc |

**Ba bài học từ tăng cường:**

1. **Co giãn đều bị chuẩn hoá triệt tiêu.** Phép "phóng to cả bàn tay 10%" vô dụng, vì bước chuẩn hoá
   chia mọi thứ cho cỡ lòng bàn tay, và hai thao tác triệt tiêu nhau. Một kiểm thử tự động đã chứng
   minh điều này. Dự án thay bằng co giãn **đổi dần** dọc cửa sổ, thứ mà chuẩn hoá không xoá được.
2. **Đo σ nhiễu cho đúng thứ cần đo.** Lần đo đầu lấy mọi cửa sổ `none` ít di chuyển, ra 0,054. Kiểm
   lại thì phần lớn là động tác bấm ngón và xòe tay, tức **cử động có chủ ý**, không phải độ rung. Giới
   hạn vào cửa sổ tay nghỉ (`D0X`) ra 0,0159, và một phép đo độc lập (nhiễu tần số cao) ra 0,0162.
   Hai số khớp nhau.
3. **Chỉ tăng cường tập train, và tạo bản mới mỗi lượt học.** Có chặn ở mức hàm: tăng cường từ chối
   mọi tập khác train. Mỗi lượt học (epoch, mục 7.3) mô hình thấy một biến thể mới, nên không thể học
   thuộc lòng từng ví dụ.

Phase 8 đo được: bỏ tăng cường thì LSTM kém đi 0,063 macro-F1. Tăng cường có ích thật.

**Bài học về tăng cường "quá giả".** Ở Phase 6, dự án thử tạo cú vuốt mà bàn tay **cứng hoàn toàn**
(không đổi dáng), để mô hình chấp nhận kiểu vuốt của người dùng. Đo trên tay chỉ trỏ thật của IPN, độ
xòe bàn tay vẫn dao động 0,2–0,8 trong khi bản giả tạo chỉ dao động 0,06. **Bản giả tạo giả hơn thực
tế**: tay thật đang di chuyển không bao giờ cứng hẳn. Mô hình học từ bản quá giả sẽ không giúp được
tay thật.

---

## 7. Ba loại mô hình: luật, rừng ngẫu nhiên, LSTM

### 7.1. Mô hình luật: mốc khởi đầu

Trước khi dùng học máy, dự án dựng một mô hình **luật viết tay**:

1. Thiếu tay → `none`.
2. Xét vuốt trước: tốc độ ngang đỉnh `max_vx` **và** dời ngang `|dx|` đều vượt ngưỡng → vuốt. Chiều
   lấy theo dấu của `dx` so với hằng số đã đo.
3. Rồi mới xét zoom: `|pinch_delta|` vượt ngưỡng → zoom in hoặc zoom out theo dấu.

Vuốt phải xét trước, vì cú hất của IPN mở bàn tay ra, làm khoảng cách cái–trỏ cũng đổi theo.

**Ngưỡng được hiệu chuẩn từ dữ liệu train, không tự đặt.** Mỗi ngưỡng là trung điểm giữa phân vị 90
của nhóm phải nằm dưới và phân vị 10 của nhóm phải nằm trên.

> **Khái niệm — Phân vị.** Phân vị 90 của một dãy số là giá trị mà 90% số trong dãy nhỏ hơn nó. Ví dụ
> phân vị 90 của tốc độ tay khi không cử chỉ là "tốc độ mà 90% lúc không cử chỉ chậm hơn".

Ba ngưỡng đo được: `RULE_VX_HI = 4,026`, `RULE_DX_HI = 0,1025`, `RULE_P_HI = 0,7209`.

**Kết quả:** macro-F1 0,231 trên val. Hơn hai mô hình "ngốc" (mục 8.2), nhưng **44% lúc không có cử chỉ
bị báo thành cử chỉ**. Mô hình luật vẫn có giá trị: nó là **đường cơ sở** để biết học máy giỏi hơn bao
nhiêu.

### 7.2. Rừng ngẫu nhiên

> **Khái niệm — Cây quyết định.** Giống trò chơi **"20 câu hỏi"**. Máy học ra một chuỗi câu hỏi có/không
> về các đặc trưng. Ví dụ: "khoảng cách cái–trỏ có thay đổi hơn 1,2 lòng bàn tay không?" → nếu có:
> "nó tăng hay giảm?" → … cho tới khi trả lời được "đây là zoom in". Câu hỏi và ngưỡng đều do máy tự
> chọn, sao cho mỗi câu hỏi tách các lớp tốt nhất trên dữ liệu train.

> **Khái niệm — Rừng ngẫu nhiên (random forest).** Một cây đơn lẻ dễ "học tủ". Rừng ngẫu nhiên trồng
> **300 cây**. Mỗi cây học từ một phần ví dụ rút ngẫu nhiên, và ở mỗi câu hỏi chỉ được xét một phần đặc
> trưng chọn ngẫu nhiên. Khi gặp cửa sổ mới, 300 cây cùng **bỏ phiếu**. Tỉ lệ phiếu của lớp thắng chính
> là **độ tin**. Giống hỏi ý kiến 300 người, mỗi người đọc một phần tài liệu khác nhau: ý kiến chung
> đáng tin hơn ý kiến một người.

**Kết quả:** macro-F1 **0,436**, gần gấp đôi mô hình luật. Học cả rừng trên 3 326 cửa sổ chỉ mất 1,6 giây.

**Mô hình dựa vào con số nào?**

> **Khái niệm — Độ quan trọng hoán vị (permutation importance).** Xáo trộn ngẫu nhiên giá trị của một
> đặc trưng giữa các cửa sổ trong đề thi thử, rồi xem điểm tụt bao nhiêu. Tụt nhiều thì mô hình dựa
> nhiều vào đặc trưng đó.

Ba đặc trưng quan trọng nhất: `pinch_range`, `pinch_delta`, `max_vx`.

**Bài học về đặc trưng "sinh đôi".** Trước khi học, dự án đoán `dx` (cổ tay dời ngang bao xa) sẽ nằm
trong top 3. Nó đứng thứ 13. Lý do: `dx` có một người sinh đôi là `mean_vx` (vận tốc ngang trung bình),
hai con số tăng giảm cùng nhau với hệ số tương quan 0,97. Xáo một mình `dx` thì mô hình vẫn dùng được
`mean_vx`, nên điểm không tụt, và **cả hai đều trông như vô dụng**. Xáo cả cặp cùng lúc thì số cú vuốt
bị đoán ngược hướng tăng từ 8 lên khoảng 43. **Bài học:** độ quan trọng hoán vị đánh giá thấp các đặc
trưng có tương quan mạnh với nhau. Phải xáo theo nhóm.

### 7.3. Mạng nơ-ron và LSTM

Rừng ngẫu nhiên chỉ thấy **15 con số do người chọn**. Nếu thứ quyết định một cử chỉ không nằm trong 15
con số đó, nó chịu. LSTM thì xem **toàn bộ chuyển động** của 21 điểm.

> **Khái niệm — Mạng nơ-ron.** Một công thức toán rất lớn với rất nhiều **"núm vặn"**, gọi là **trọng
> số**. Đầu vào đi qua nhiều **lớp**; mỗi lớp nhân với trọng số, cộng lại, rồi qua một hàm phi tuyến
> đơn giản. Lúc đầu các núm ở vị trí ngẫu nhiên, và công thức đoán bừa. Huấn luyện là **vặn dần từng núm**
> sao cho số lần đoán sai giảm xuống. Không ai chỉ định núm nào làm gì; mạng tự tìm ra những dấu hiệu
> có ích.

> **Khái niệm — Hàm mất mát (loss).** Con số đo mạng còn sai nhiều tới đâu trên một ví dụ. Dự án dùng
> **entropy chéo** (*cross-entropy*): nếu đáp án là "vuốt trái" mà mạng chỉ cho "vuốt trái" độ tin 0,1,
> loss lớn; độ tin 0,99 thì loss gần 0. Càng nhỏ càng tốt.

> **Khái niệm — Hạ dốc (gradient descent).** Cách vặn núm. Hình dung bạn đứng trên sườn đồi trong
> sương mù, muốn xuống thung lũng (loss thấp nhất). Bạn không thấy đường, nhưng cảm được dưới chân dốc
> về phía nào. Bước một bước nhỏ theo hướng dốc xuống, rồi lặp lại. Toán học cho phép tính chính xác
> "hướng dốc" cho từng núm cùng lúc. Dự án dùng **Adam**, một biến thể tự điều chỉnh độ dài bước cho
> từng núm, với tốc độ học 0,001.

> **Khái niệm — Epoch và lô (batch).** Mỗi lần vặn núm dựa trên một **lô** 64 ví dụ, không phải từng ví
> dụ một (ổn định hơn) và không phải toàn bộ dữ liệu (chậm hơn). Một **epoch** là một lượt cho mạng xem
> hết toàn bộ dữ liệu train. Mạng được dạy qua hàng trăm epoch.

> **Khái niệm — Mạng hồi quy và LSTM.** Mạng nơ-ron thông thường nhận một đầu vào cố định. **Mạng hồi
> quy** (*RNN*) đọc **chuỗi** từng bước, và mang theo một "trí nhớ" từ bước trước sang bước sau, giống
> ta đọc một câu từng chữ mà vẫn nhớ đầu câu. **LSTM** (*Long Short-Term Memory*) là loại mạng hồi quy
> có ba "cổng" điều khiển trí nhớ:
>
> - **cổng quên**: bỏ bớt thông tin cũ không còn cần;
> - **cổng vào**: quyết định ghi thêm gì từ bước hiện tại;
> - **cổng ra**: quyết định dùng phần nào của trí nhớ để trả lời.
>
> Nhờ các cổng, LSTM nhớ được chuyện xảy ra từ nhiều bước trước, điều mà mạng hồi quy đơn giản làm kém.

**LSTM của dự án:**

| Thành phần | Giá trị | Ý nghĩa |
|---|---|---|
| Đầu vào mỗi bước | 42 số | 21 điểm × 2 toạ độ, đã chuẩn hoá |
| Số bước | 18 | một cửa sổ 1,2 giây |
| Số lớp LSTM | 2 | chồng lên nhau |
| Số đơn vị ẩn | 128 | "kích thước trí nhớ" mỗi lớp |
| Dropout | 0,3 | xem dưới |
| Gộp | `last` | đọc hết cửa sổ, dùng trạng thái ở bước cuối để quyết định |
| Đầu ra | 5 số | độ tin cho 5 lớp |
| Tổng số trọng số | khoảng 220 nghìn | |

> **Khái niệm — Dropout.** Trong lúc học, mỗi lần tắt ngẫu nhiên 30% số đơn vị. Mạng không thể dựa vào
> một vài đơn vị cụ thể, nên phải học những dấu hiệu bền vững hơn. Khi chạy thật thì bật hết.

**Một chiều, không bao giờ nhìn tương lai.** LSTM có biến thể **hai chiều** đọc chuỗi cả xuôi lẫn ngược,
thường chính xác hơn khi xử lý video đã quay xong. Dự án **cấm** biến thể đó, vì khi chạy thật trên
webcam, tương lai chưa xảy ra. Tương tự, không dùng làm mượt hai phía.

**Khoảnh khắc mất tay:** LSTM không nhận được NaN. Dự án cho nó **giữ nguyên vị trí cuối cùng còn
thấy**, không bịa ra chuyển động, không dùng thông tin tương lai.

**Chạy trên CPU thường.** Một lần học mất khoảng 13–25 phút. Mỗi câu trả lời khi chạy demo mất khoảng 1
mili-giây.

**Kết quả:** macro-F1 **0,556**, vượt rừng 0,436. Phase 8 xác nhận qua năm lần học với hạt giống khác
nhau: LSTM hơn rừng +0,116, gấp hơn 4 lần độ dao động. Đây là kết luận chắc chắn.

### 7.4. Quá khớp, đường học và dừng sớm

> **Khái niệm — Quá khớp (overfitting).** Học sinh thuộc lòng đáp án bài tập về nhà thì điểm bài tập rất
> cao, nhưng gặp đề mới thì làm kém. Mạng nơ-ron cũng vậy. Dấu hiệu: loss trên train tiếp tục giảm,
> nhưng loss trên val thôi giảm hoặc tăng lên.

> **Khái niệm — Đường học, dừng sớm, checkpoint.**
>
> - **Đường học:** đồ thị loss của train và val theo từng epoch.
> - **Dừng sớm:** ngừng dạy khi điểm val không tiến bộ thêm một thời gian (20 epoch).
> - **Checkpoint:** bản lưu của mạng ở thời điểm tốt nhất.

**Đã quan sát được:**

- **Có tăng cường:** loss val giảm nhanh trong khoảng 20 epoch đầu rồi đứng yên, còn loss train tiếp tục
  giảm tới gần 0. Nhưng loss val **không quay đầu tăng**: việc đưa biến thể mới mỗi epoch đã ngăn mạng học
  thuộc lòng.
- **Không tăng cường** (chạy riêng để thấy rõ): loss val thấp nhất ở **epoch 38**, rồi tăng dần khoảng 30%.
  Đó là điểm bắt đầu quá khớp, hiện rõ trên đồ thị.

### 7.5. Lạc quan do chọn lọc

> **Khái niệm — Lạc quan do chọn lọc.** Nếu thi thử 100 lần rồi chỉ báo điểm cao nhất, con số đó lạc
> quan: một phần là do may.

Mỗi cử chỉ trong val chỉ có khoảng 100 cửa sổ. Chỉ cần vài cửa sổ đổi câu trả lời là điểm lên xuống vài
phần trăm. Giữa hai epoch liền nhau, macro-F1 của LSTM dao động khoảng ±0,04 dù mạng gần như không đổi.

Lần dạy LSTM đầu tiên chọn đúng epoch có điểm cao nhất và báo **0,601**. Đó là một đỉnh may mắn. Hai lần
dạy khác còn bị dừng quá sớm, ở epoch 40 và 48, chỉ vì một đỉnh may mắn đến sớm.

**Cách sửa:** dừng sớm và chọn checkpoint theo **trung bình 10 epoch liền nhau**, thay vì một epoch lẻ.
Mô hình được chọn có điểm 0,556. Con số không thiên lệch hơn đến từ năm lần học với hạt giống khác nhau
ở Phase 8: **0,549 ± 0,027**.

### 7.6. Mô hình ghép

Thử trực tiếp trên webcam lộ ra rằng **mỗi mô hình giỏi một việc** (chi tiết ở mục 9.3):

- **LSTM giỏi vuốt.** Nó nhận cú vuốt qua động tác của các ngón tay, chịu được kiểu "hất rồi kéo tay về"
  mà rừng bỏ qua.
- **Rừng giỏi zoom trên tay người dùng.** Nó nhìn chủ yếu vào khoảng cách cái–trỏ thay đổi, đúng bản chất
  của zoom, ít phụ thuộc các ngón khác, và không báo zoom khi tay đứng yên.

> **Khái niệm — Mô hình ghép (ensemble theo chuyên môn).** Dùng nhiều mô hình, mỗi mô hình phụ trách
> phần việc mình giỏi.

Luật ghép: LSTM nói "vuốt" thì là vuốt; nếu không, rừng nói "zoom" thì là zoom; còn lại là `none`.

Trên val của IPN, mô hình ghép kém LSTM đứng một mình một chút, vì người diễn IPN zoom đúng "kiểu IPN"
mà LSTM đã học. Nhưng trên tay người dùng thì ngược lại. **Demo dùng mô hình ghép**, vì người dùng thật
quan trọng hơn điểm trên video quay sẵn.

---

## 8. Đánh giá: đo cho đúng

Đây là phần dự án đầu tư nhiều nhất, và cũng là phần học được nhiều nhất.

### 8.1. Vì sao "tỉ lệ đoán đúng" là thước đo tồi

Một mô hình lười, lúc nào cũng đoán `none`, đã đúng **96,5%** số cửa sổ val. Nghe rất tốt, mà hoàn toàn
vô dụng: nó không bao giờ nhận ra cử chỉ nào. Khi các lớp mất cân bằng, **tỉ lệ đúng** (*accuracy*) gần
như không nói lên gì.

### 8.2. Precision, recall, F1

> **Khái niệm — Recall và precision**, qua ví dụ **chuông báo cháy**:
>
> - **Recall** (tỉ lệ bắt được): trong các đám cháy thật, chuông kêu được bao nhiêu phần? Bỏ sót đám
>   cháy là tệ.
> - **Precision** (tỉ lệ báo đúng): trong các lần chuông kêu, bao nhiêu lần là cháy thật? Kêu bừa là
>   phiền.
>
> Chuông lúc nào cũng kêu có recall 100%, precision gần 0%. Chuông không bao giờ kêu không bao giờ báo
> nhầm, nhưng vô dụng. Cần cả hai.

**Ví dụ thật** — lớp `swipe_left` của rừng ngẫu nhiên trên val:

- Có 104 cửa sổ vuốt trái thật; mô hình bắt được 56 → **recall 54%**.
- Mô hình nói "vuốt trái" 424 lần, chỉ 56 lần đúng → **precision 13%**.

> **Khái niệm — F1 và macro-F1.**
>
> - **F1** gộp precision và recall thành một điểm từ 0 đến 1 (trung bình điều hoà). F1 chỉ cao khi **cả
>   hai** cùng cao. Vuốt trái ở ví dụ trên có F1 = 0,21.
> - **macro-F1** là trung bình F1 của năm lớp, mỗi lớp nặng như nhau. Mô hình lười "luôn `none`" có F1
>   bằng 0 ở bốn lớp cử chỉ, nên macro-F1 chỉ 0,196. Đây là điểm chính dùng để so mô hình ở mức cửa sổ.

> **Khái niệm — Đường cơ sở.** Mô hình "ngốc" làm mốc: **luôn đoán `none`** (macro-F1 0,196) và **đoán
> ngẫu nhiên** (0,080). Mô hình nào không vượt hai mốc này thì chưa học được gì.

> **Khái niệm — Ma trận nhầm lẫn.** Bảng 5 × 5: hàng là lớp thật, cột là lớp mô hình đoán. Ô trên đường
> chéo là đoán đúng; ô ngoài đường chéo cho biết **lớp nào bị nhầm thành lớp nào**. Đây là công cụ tìm
> lỗi quan trọng nhất: nó chỉ đúng chỗ cần sửa.

### 8.3. Hai mức chấm: cửa sổ và sự kiện

Người dùng không quan tâm tới từng cửa sổ 0,2 giây. Họ quan tâm: **"tôi vuốt một lần, slide có đổi đúng
một lần không?"** và **"tôi không làm gì, slide có tự đổi không?"**

- **Mức cửa sổ:** chấm từng đoạn 1,2 giây, như chấm từng tấm ảnh.
- **Mức sự kiện:** cho **cả hệ thống** chạy trên 27 video val liên tục (60 phút, 108 cử chỉ), đúng như
  chạy trên webcam, rồi đếm **lệnh** phát ra.
  - Lệnh đúng là lệnh đúng loại, phát trong lúc cử chỉ diễn ra hoặc tới 1 giây sau.
  - Các chỉ số: F1 sự kiện, **số lệnh trên một cử chỉ** (lý tưởng là 1), **lệnh nhầm mỗi phút**.

**Mức sự kiện cho thấy điều mức cửa sổ giấu.** Bảng 1 của Phase 8, khi chưa có máy trạng thái:

| Mô hình | macro-F1 cửa sổ | Recall sự kiện | Precision sự kiện | Lệnh nhầm mỗi phút |
|---|---|---|---|---|
| Luật | 0,231 | 0,870 | 0,050 | 29,8 |
| Rừng | 0,436 | 0,815 | 0,121 | 10,6 |
| LSTM | 0,556 | 0,935 | 0,204 | 6,6 |
| Ghép | 0,506 | 0,852 | 0,188 | 6,6 |

Hệ thống bắt được 82–94% cử chỉ, nhưng **cứ một lệnh đúng thì có 4–19 lệnh sai**. Lớp `none` chiếm 96%
thời gian, nên một tỉ lệ báo nhầm nhỏ theo cửa sổ vẫn thành rất nhiều lệnh nhầm mỗi phút. Từ Phase 8,
mức sự kiện là thước đo chính.

**Một bài học nhỏ về định nghĩa:** định nghĩa khớp ban đầu ("lệnh trong khoảng ±1 giây quanh lúc cử chỉ
kết thúc") cho F1 sự kiện chỉ khoảng một nửa, vì lệnh đúng thường phát ở **giữa** cử chỉ. Đổi định nghĩa
thành "từ lúc bắt đầu tới lúc kết thúc + 1 giây". Cách chấm phải mô tả đúng điều mình muốn đo.

### 8.4. Ba con số đánh lừa đã bắt được (Phase 10)

Tối ưu theo một thước sai thì càng cố càng lệch. Dự án đã phải sửa thước ba lần:

1. **Đồng hồ bấm giờ bắt đầu sai lúc.** Trên webcam, mỗi lời nhắc dài 4 giây, gồm cả lúc chuẩn bị và lúc
   thu tay. Chuyển động lớn nhất nhiều khi là lúc **thu tay**, nên "lúc cử chỉ diễn ra" bị đặt muộn, và
   độ trễ ra số âm. **Sửa:** đo độ trễ trên video IPN, nơi khoảnh khắc chính đã được đánh dấu.
2. **Một điểm "hoàn hảo" che giấu hai lỗi.** Lần chấm đầu cho đúng **1,00 lệnh trên mỗi cử chỉ**. Nhưng
   recall chỉ 0,55: gần một nửa cử chỉ bị bỏ lỡ, và số lệnh thừa vừa khéo bù lại. **Sửa:** luôn báo kèm
   recall, lệnh trên mỗi lời nhắc, và số lệnh trùng.
3. **Trung bình sai cách.** Con số "nhầm mỗi phút" chung từng là trung bình cộng của ba kịch bản. Lúc đọc
   và gõ phím, tay nằm ngoài khung nên luôn ra 0, kéo cả con số xuống. Một phiên 0,9 phút lại nặng ngang
   một phiên 10 phút. **Sửa:** cộng tổng số lệnh nhầm rồi chia cho tổng số phút, và thêm cột **nhầm mỗi
   phút có tay**.

### 8.5. Con số có đáng tin không?

Một kết luận chỉ đáng tin khi chênh lệch lớn hơn mức dao động ngẫu nhiên.

> **Khái niệm — Hạt giống ngẫu nhiên (seed).** Học máy có nhiều bước ngẫu nhiên: trộn ví dụ, khởi tạo
> trọng số, biến đổi dữ liệu. Cố định hạt giống thì chạy lại cho đúng kết quả cũ. Đổi hạt giống thì thấy
> kết quả dao động bao nhiêu chỉ do may rủi.

> **Khái niệm — Kiểm định chéo k-fold theo nhóm người.** Chia người thành 5 nhóm. Lần lượt để mỗi nhóm
> làm đề thi, bốn nhóm kia làm bài tập. Được 5 điểm số; độ dao động giữa chúng cho biết hệ thống khác
> nhau bao nhiêu tuỳ người.

**Đo được ở Phase 8:**

| | Dao động giữa 5 hạt giống | Dao động giữa 5 nhóm người |
|---|---|---|
| Rừng (macro-F1) | ± 0,003 | ± 0,016 |
| LSTM (macro-F1) | ± 0,027 | ± 0,069 |

- **Dao động theo người lớn hơn dao động theo hạt giống.** Theo từng người, macro-F1 của LSTM chạy từ
  0,40 tới 0,86. Hệ thống hoạt động rất khác nhau tuỳ người.
- **Quy tắc làm việc:** chênh lệch nhỏ hơn độ dao động thì ghi "**không đủ bằng chứng để kết luận**".
  Chênh lệch dưới khoảng 0,02 đọc là "không ảnh hưởng thực tế".
- Khi chỉ chạy một lần, chênh lệch dưới khoảng 0,1 F1 thường **đảo chiều** khi đổi một thiết lập nhỏ.

**Ba kết luận đứng vững qua mọi lần dựng lại bảng:**

1. LSTM hơn rừng ngẫu nhiên.
2. Chia ngẫu nhiên theo cửa sổ làm điểm đẹp giả thêm 0,10–0,15.
3. Rừng cần gốc toạ độ ở cổ tay của bước đầu, và cửa sổ 1,2 giây là tốt nhất.

### 8.6. Thí nghiệm có kiểm soát: bảy bảng của Phase 8

> **Khái niệm — Thí nghiệm có kiểm soát (ablation).** Đổi **đúng một yếu tố**, giữ nguyên mọi thứ khác,
> rồi đo. Như thế mới biết yếu tố đó có ích hay không.

Phase 8 chạy **46 thí nghiệm**, xếp thành bảy bảng:

| Bảng | Câu hỏi | Kết luận |
|---|---|---|
| 1 | Bốn mô hình ở hai mức | luật < rừng < ghép < LSTM; cần tầng kích hoạt (mục 9.2) |
| 2 | Gốc toạ độ: bước đầu hay từng bước? | Giữ bước đầu: điều kiện sống còn của rừng, và LSTM cũng tốt hơn ở mức sự kiện |
| 3 | Cửa sổ 0,8 / 1,2 / 1,6 giây? | 1,2 giây tốt nhất với LSTM; rừng gần như không nhạy |
| 4 | Chia theo người hay ngẫu nhiên? | Chia ngẫu nhiên thổi phồng 0,10–0,15 (mục 6.5) |
| 5 | Bỏ hay thêm đặc trưng? | Thêm 10 góc khớp: cải thiện lớn nhất cho rừng (mục 8.7) |
| 6 | Năm hạt giống | LSTM hơn rừng một cách chắc chắn |
| 7 | k-fold theo người | Hệ thống khác nhau nhiều tuỳ người; mô hình ghép ít tụt hơn ở nhóm người khó |

**Bảng phụ** (một lần học mỗi hàng): GRU (một loại mạng hồi quy khác) thay LSTM không khác biệt đủ bằng
chứng; giảm kích thước trí nhớ còn 64 làm kém đi; gộp kiểu trung bình hay lớn nhất kém hơn gộp `last`;
chỉ dùng 11 điểm (bỏ các khớp giữa) làm báo nhầm khi chỉ trỏ tăng gấp đôi.

### 8.7. Phân tích lỗi: đặt giả thuyết rồi kiểm

**Lỗi lớn nhất của mọi mô hình:** cửa sổ `none` bị đoán thành vuốt. Phần lớn đến từ **tay đang chỉ trỏ**
(chiếm 64% số cửa sổ `none` của val). Khi chỉ trỏ, người ta di chuyển tay nhanh và xa, có khi còn nhanh
hơn một cú vuốt.

**Giả thuyết A:** bộ 15 đặc trưng không mô tả từng ngón tay, nên một bàn tay chỉ trỏ di chuyển nhanh trông
như cú hất.

**Kiểm:** thêm 10 đặc trưng góc khớp (góc gập ở khớp giữa của từng ngón), các thứ khác giữ nguyên.

| | 15 đặc trưng | + 10 góc khớp |
|---|---|---|
| Ô lớn nhất `none` → `swipe_left` | 366 | **190** |
| Báo nhầm khi chỉ một ngón / hai ngón | 5,8% / 9,7% | 1,8% / 4,8% |
| macro-F1 | 0,436 | 0,492 |
| Lệnh nhầm mỗi phút | 10,6 | 6,3 |

Ô lỗi nhỏ đi gần một nửa, mọi chỉ số khác cùng tốt lên. **Giả thuyết A đứng vững.** Bằng chứng thứ hai,
từ phía LSTM: bỏ các khớp giữa của ngón thì LSTM báo nhầm khi chỉ trỏ tăng gấp đôi. LSTM đang dùng chính
các khớp đó.

**Lỗi zoom đảo chiều** (zoom in bị đoán zoom out và ngược lại) gần như không nhúc nhích dù đổi bất kỳ đặc
trưng nào. **Lỗi mà không thay đổi đặc trưng nào đụng tới được thì nhiều khả năng nằm ở nhãn:** luật gán
nhãn chọn khoảnh khắc chính theo **độ lớn** thay đổi, không xét chiều. Người diễn IPN hay mở rồi chụm trong
cùng một đoạn `zoom_in`, nên có cửa sổ mang nhãn `zoom_in` dù ngón đang chụm.

**Bài học:** khi một lỗi không phản ứng với bất kỳ thay đổi nào ở mô hình, hãy nghi ngờ dữ liệu.

---

## 9. Từ mô hình tới hệ thống thời gian thực

### 9.1. Vòng lặp chạy thật

1. Camera đưa ảnh vào; mỗi ảnh gắn mốc thời gian thật.
2. MediaPipe tìm 21 điểm.
3. Một **bộ đệm** giữ 1,7 giây gần nhất **theo thời gian**, không theo số ảnh, vì FPS dao động.
4. Mỗi 0,2 giây, lấy 18 bước cuối qua **đúng đường ống** của dữ liệu học: lấy mẫu lại, vá, chuẩn hoá.
5. Mô hình trả nhãn và độ tin.
6. Máy trạng thái quyết định có bấm phím không.
7. Màn hình hiện ảnh lật gương, khung xương, nhãn, trạng thái.

**Tốc độ** đo ở Phase 10 (ánh sáng tối, máy 8 luồng logic):

| Khâu | Thời gian mỗi ảnh |
|---|---|
| Chờ camera | khoảng 17–18 ms |
| MediaPipe tìm 21 điểm | khoảng 12 ms (khoảng **76–79%** thời gian xử lý) |
| Vẽ màn hình | khoảng 2,7 ms |
| Đổi màu, cắt cửa sổ | dưới 1 ms |
| Mô hình rừng | khoảng 0,3 ms |
| Máy trạng thái | khoảng 0,001 ms |

Hệ thống chạy khoảng **30 FPS**, tức bằng tốc độ camera. Nút cổ chai là camera và MediaPipe, **không phải
mô hình phân loại**. Mô hình chậm nhất (ghép) cũng chỉ mất 6,4 ms mỗi cửa sổ, trong khi có 200 ms giữa hai
lần dự đoán.

**Hai việc nhỏ cho demo mượt:** nạp sẵn mô hình trước khi bật camera (trước đó demo đứng hình gần 3 giây
lần đầu thấy tay), và cho rừng dự đoán từng cửa sổ một cách nhẹ hơn (9 ms thay vì 63 ms).

### 9.2. Máy trạng thái: dạy hệ thống biết im lặng

Hình dung mô hình như **một bình luận viên** hô lên 5 lần mỗi giây: "vuốt trái!… vuốt trái!… không có
gì!… vuốt trái!…" Nếu mỗi tiếng hô là một lần bấm phím, một cú vuốt sẽ lật qua cả chục slide.

> **Khái niệm — Máy trạng thái hữu hạn (finite state machine).** Một cơ chế chỉ ở **một trong vài trạng
> thái** tại mỗi lúc, và chuyển trạng thái theo quy tắc rõ ràng. Giống đèn giao thông: chỉ có xanh, vàng,
> đỏ, và thứ tự chuyển cố định.

Máy trạng thái của dự án là **một người trợ lý cẩn thận** giữa bình luận viên và bàn phím:

| Trạng thái | Nghĩa |
|---|---|
| Chờ tay | chưa thấy bàn tay |
| Sẵn sàng | thấy tay, đang lắng nghe |
| Đang cân nhắc | vừa nghe một tiếng hô đủ chắc; đang chờ thêm tiếng hô cùng ý |
| Nghỉ | vừa bấm phím, nghỉ 1,2 giây |

**Bốn quy tắc:**

1. **Đủ chắc mới bắt đầu cân nhắc** (ngưỡng độ tin). Tiếng hô ngập ngừng thì bỏ qua.
2. **Đủ đồng thuận mới bấm:** cần **k trên n** tiếng hô liền nhau cùng ý.
3. **Bấm xong thì nghỉ 1,2 giây**, như chuông cửa chỉ reo một lần dù ấn hơi lâu.
4. **Hạ tay ra khỏi khung là huỷ hết.**

**Một lỗi thiết kế đã tránh.** Cách hiểu đầu tiên của quy tắc 2 là "đếm số tiếng hô cùng ý trong 5 tiếng
gần nhất". Theo đó, chuỗi nhấp nháy *vuốt, không, vuốt, không, vuốt* có 3 trên 5 tiếng "vuốt", và sẽ bấm
phím: một lệnh từ tín hiệu rất yếu. Bản dùng thật coi một tiếng hô **khác ý mà đủ chắc**, kể cả "không có
gì", là **phiếu phản đối**, và huỷ ngay việc cân nhắc.

**Được gì:** lệnh nhầm giảm từ 6,6–30 xuống khoảng 1–1,5 lần mỗi phút với hai mô hình tốt nhất.

**Mất gì:** trợ lý cẩn thận thì đôi khi bỏ lỡ cử chỉ thật. Đây là **đánh đổi** cơ bản của mọi hệ thống phát
hiện: muốn ít báo nhầm thì phải chịu bỏ sót nhiều hơn, và ngược lại. Không có cấu hình tốt nhất về mọi mặt.
Dự án đo và bày bảng, **người dùng chọn điểm đánh đổi**.

**Một đánh đổi nữa: phải thấy tay bao nhiêu.** Đòi 100% số bước thấy tay (thay vì 70%) bớt được lệnh nhầm
lúc tay đang đưa vào khung, nhưng cú vuốt nhanh hay làm mất tay vài ảnh. Đo trên video: mất 3 trong 54 cú
vuốt, mà lệnh nhầm chỉ giảm 3%. Giữ 70%.

### 9.3. Lệch miền: người dùng làm khác người diễn IPN

> **Khái niệm — Lệch miền (domain shift).** Dữ liệu lúc dùng khác dữ liệu lúc học. Mô hình học từ cách
> 30 người diễn IPN làm cử chỉ; nếu bạn làm khác họ, mô hình không nhận ra, dù bạn thấy mình làm "đúng".
> Giống người học lái xe ở một thành phố, sang thành phố khác có biển báo khác thì lúng túng.

Mỗi lần thử trên webcam đều lộ ra một kiểu lệch miền. Công cụ chính để tìm nguyên nhân là:

> **Khái niệm — Thí nghiệm phản thực tế (counterfactual probe).** Muốn biết mô hình dựa vào cái gì, ta
> lấy những ví dụ thật mà nó đang nhận đúng, **sửa đúng một khía cạnh**, rồi xem nó còn nhận ra không. Như
> muốn biết một người nhận ra bạn qua giọng hay qua mặt, ta đổi đúng một thứ. Cách này trả lời câu hỏi mà
> điểm số tổng không trả lời được: **mô hình thật sự coi cái gì là một cú vuốt?**

**Phát hiện 1 — rừng ngẫu nhiên coi "vuốt" là cú hất mở bàn tay** (Phase 6).

| Sửa cú vuốt IPN (trái / phải) | Rừng còn nhận | LSTM còn nhận |
|---|---|---|
| Không sửa | 100% / 92% | |
| Bàn tay giữ nguyên dáng, cổ tay đi như cũ | **0% / 0%** | 8% / 0% |
| Đi ra rồi quay về ngay | 45% / 37% | **96% / 99%** |
| Cổ tay chỉ đi một phần tư quãng | 4% / 0% | **100% / 94%** |
| Cổ tay đứng yên, chỉ các ngón chuyển động | 0% / 0% | **100% / 87%** |

- Với rừng, "vuốt" là cổ tay đi ngang đủ nhanh, đủ xa, **và** bàn tay mở ra trong lúc hất. Sự mở tay giúp
  nó tách cú hất khỏi tay chỉ trỏ. Người dùng vuốt "kiểu thông thường" (bàn tay mở sẵn, lướt ngang, rồi
  kéo về) nên bị coi là `none`.
- LSTM nhận cú vuốt từ **động tác của các ngón tay**, không từ quãng đường cổ tay. Vì vậy nó chịu được kiểu
  "hất rồi kéo về". Đây là lý do LSTM được giao lo vuốt.

**Phát hiện 2 — LSTM học "kiểu zoom của IPN", không học "zoom là gì"** (Phase 7, 10).

| Sửa cú zoom IPN (in / out) | Rừng còn nhận | LSTM còn nhận |
|---|---|---|
| Không sửa | 93% / 98% | 100% / 100% |
| Ngón nhẫn và út duỗi thẳng | 63% / 85% | **10% / 35%** |
| Bàn tay đứng yên ở dáng cái–trỏ đang mở | 0% báo zoom | **46–62% vẫn báo zoom** |

- Người diễn IPN zoom bằng ba ngón, **nhẫn và út luôn gập**. LSTM học luôn cả chi tiết đó. Đo độ duỗi trên
  tay người dùng: nhẫn và út **duỗi**, độ duỗi 1,5–2,1, trong khi IPN khoảng 0,5. Kết quả: trên tay người
  dùng, LSTM lúc đó nhận **0 trên 10** cú zoom.
- LSTM còn đoán zoom từ **dáng tay đứng yên**, nên báo nhầm khi tay chỉ đang giữ yên.

**Bài học lớn:** mô hình học **mọi quy luật có trong dữ liệu**, kể cả những trùng hợp ta không hề muốn dạy.
Không có cách nào biết trước điều đó chỉ bằng nhìn điểm số trên dữ liệu cùng nguồn.

**Ba cách đã dùng để thu hẹp lệch miền:**

1. **Dạy người dùng làm giống IPN.** Chế độ luyện tập `--show-features` hiện vài đặc trưng của cửa sổ vừa
   rồi, tô xanh nếu nằm trong khoảng của người diễn IPN, đỏ nếu không: độ mở bàn tay khi vuốt, độ duỗi
   nhẫn, út khi zoom. Sau một phút luyện, 88% cú vuốt của người dùng đã mở tay đúng kiểu IPN, và rừng
   nhận 79%. Tài liệu `docs/gestures.md` mô tả cách làm từng cử chỉ.
2. **Dạy mô hình chấp nhận nhiều kiểu hơn**, bằng tăng cường dữ liệu đặc biệt (LSTM `run_08`):
   - **đổi dáng ngón phụ:** một nửa số ví dụ zoom được ghép dáng ngón giữa, nhẫn, út của **một bàn tay
     IPN khác** (lấy từ hơn 58 nghìn dáng tay thật);
   - **bàn tay đứng yên:** thêm ví dụ tay giữ nguyên tư thế, nhãn `none`.

   Kết quả trên webcam: zoom từ 0/10 lên 4/10, vuốt nhầm khi tập zoom từ 4 xuống 0. Trên video IPN có nhẫn,
   út duỗi: zoom được nhận từ 10%/35% lên 95%/95%. Cái giá: mô hình "dễ dãi" hơn với zoom, đôi khi tưởng
   tay chỉ trỏ là zoom.
3. **Ghép mô hình**, mỗi mô hình lo phần nó vững nhất trên tay người dùng (mục 7.6).
4. **Quay dữ liệu của chính người dùng** (Phase 11, mục 10): cách sửa tận gốc nhất.

### 9.4. Ghi và phát lại: hộp đen

Mỗi lần thử trên webcam, demo lưu **vị trí 21 điểm ở mọi ảnh**. Sau đó có thể **phát lại** cả phiên qua
bất kỳ mô hình hay ngưỡng nào, như thể mô hình đó đã chạy trực tiếp lúc người dùng làm cử chỉ.

**Kiểm chứng:** phát lại cho đúng **316 trên 316** câu trả lời so với lúc demo chạy thật.

Nhờ vậy, so mười cấu hình không cần người dùng làm lại mười lần. Đây là cách dự án có con số "từ 0 thành
6 trên 12 cú zoom" ở mục 9.6 mà không cần thử lại.

### 9.5. Vòng tối ưu: chặn cú "lấy đà"

**Triệu chứng:** cứ 20 lần vuốt thì 5 lần slide đi **ngược chiều**.

**Tìm nguyên nhân:** in lời hô của mô hình ở từng nhịp 0,2 giây trong một lần vuốt sang phải (R là vuốt
phải, L là vuốt trái, chấm là không có gì):

```
R R · L L L R R R R R
```

Trước khi hất tay sang phải, người dùng **kéo tay sang trái lấy đà**, như vung vợt tennis về sau. Bản thân
đoạn kéo đó **là một cú vuốt trái**, và mô hình nhận đúng như vậy, độ tin 1,00. Trợ lý nghe ba tiếng "L"
liền nhau, đủ đồng thuận 3/5, bấm "vuốt trái", rồi nghỉ 1,2 giây đúng lúc cú vuốt thật diễn ra.

**Nâng ngưỡng độ tin không giúp**, vì đoạn lấy đà cũng "chắc chắn" như cú vuốt thật.

**Sửa:** đoạn lấy đà ngắn, khoảng 3 nhịp; cú hất thật dài 4–5 nhịp. Đòi **4 trên 5** nhịp đồng ý thì đoạn
lấy đà không đủ phiếu.

| | 0,75 và 3/5 | **0,85 và 4/5** |
|---|---|---|
| Vuốt mà slide đi ngược chiều | 5 trên 20 | **2 trên 20** |
| Slide tự đổi khi nói chuyện | 0,64 lần/phút | **0,18 lần/phút** |
| F1 sự kiện trên video val | 0,554 | **0,600** |
| Zoom được nhận trên webcam | 40% | 20% ← cái giá |

**Bài học:** đôi khi mô hình **không sai**, mà câu hỏi ta đặt cho hệ thống chưa đủ rõ. Cú lấy đà đúng là một
cú vuốt trái; cách sửa nằm ở tầng quyết định, không ở mô hình.

### 9.6. Vòng tối ưu: mỗi loại cử chỉ một ngưỡng riêng

**Triệu chứng:** thử điều khiển slide thật lần đầu, 4/4 lần vuốt đổi được slide, nhưng **0/12 cú zoom**
thành lệnh.

**Tìm nguyên nhân từ hộp đen của chính lần thử đó.** Động tác của người dùng rất sạch. Nhưng:

- **LSTM chắc chắn quá muộn.** Độ tin trong năm nhịp liền của một cú thu nhỏ: `0,52 0,47 0,61 0,88 0,96`.
  Ngưỡng 0,85 chỉ được vượt từ nhịp thứ tư; cần 4 phiếu mà chỉ còn hai nhịp.
- **Rừng nhận đúng 12/12 cú, nhưng "nói nhỏ".** Độ tin của rừng: `– 0,61 0,62 0,61 0,67`. Đúng ở mọi nhịp,
  nhưng không bao giờ chắc kiểu 0,9. Với phóng to còn thấp hơn: 0,33–0,56.

> **Khái niệm — Độ tin chưa hiệu chuẩn.** "Độ tin" mà mô hình trả ra **không phải** xác suất thật. Rừng
> ngẫu nhiên là tỉ lệ phiếu của 300 cây; LSTM là đầu ra của một hàm toán học. Độ tin 0,6 của rừng có thể
> đáng tin hơn độ tin 0,9 của LSTM. Hai mô hình nói hai "thang đo" khác nhau.

Như **hai giám khảo**: một người nói rất to khi đã chắc nhưng chắc muộn; một người luôn đúng nhưng luôn
nói nhỏ. Dùng một ngưỡng "độ to" chung cho cả hai là không công bằng.

**Sửa:** vuốt vẫn nghe LSTM với 0,85 và 4/5; zoom nghe rừng với ngưỡng riêng **0,40 và 3/5**. Người dùng
chọn sau khi xem bảng đo trên cả bốn nguồn dữ liệu:

| Zoom theo | Thử slide thật | 20 lời nhắc zoom: đúng / ngược / bỏ lỡ | Lệnh mỗi lời nhắc | Nhầm khi nói chuyện |
|---|---|---|---|---|
| LSTM, 0,85 · 4/5 | 0/12 | 4 / 1 / 15 | 0,62 | 0,18/phút |
| **Rừng, 0,40 · 3/5 (chọn)** | 6/12 | **10 / 4 / 6** | **1,00** | **0,18/phút** |
| Rừng, 0,40 · 2/5 | 8/12 | 16 / 4 / 0 | 1,48 | 0,27/phút |
| Rừng, 0,50 · 3/5 | 5/12 | 10 / 2 / 8 | 0,90 | 0,18/phút |

Lần thử thứ hai, 92 giây: **19 lệnh** (8 vuốt, 11 zoom), mọi phím đều tới PowerPoint.

**Vì sao chỉ 6/12 cú zoom:** người dùng đổi chiều zoom mỗi khoảng 1,3 giây, trong khi mỗi lệnh chiếm khoảng
1,8 giây (0,6 giây gom phiếu + 1,2 giây nghỉ). Từ đó có lời khuyên "các cử chỉ cách nhau khoảng 2 giây".

### 9.7. Những lời khuyên cho người dùng, rút từ số đo

- **Không lấy đà ngược chiều** (mục 9.5).
- **Giơ tay lên khoảng 1 giây rồi mới làm.** Cửa sổ chỉ được xét khi 70% số bước thấy tay.
- **Zoom xong giữ yên khoảng 1 giây.** Mở rồi chụm lại ngay chỉ tạo khoảng hai nhịp rõ, không đủ ba phiếu.
- **Các cử chỉ cách nhau khoảng 2 giây.**
- **Zoom như IPN:** chụm hoặc mở ba ngón cái, trỏ, giữa; nhẫn và út gập.

Mỗi lời khuyên là hệ quả của một con số đo được, không phải cảm tính.

---

## 10. Dữ liệu tự quay (Phase 11, đang làm)

### 10.1. Vì sao bật

Đến cuối Phase 10, trên 40 lời nhắc cử chỉ trước webcam, chỉ khoảng một nửa được nhận đúng ở lần làm đầu.
Phần lớn lỗi do người dùng làm khác người diễn IPN. Người dùng quyết định ngày 2026-11-06: **quay dữ liệu
của người thật**, làm cử chỉ theo kiểu tự nhiên nhưng giữ phần cốt lõi, và đưa cả cử chỉ tự quay vào tập
học.

Thử thêm nhiều loại cử chỉ hơn (rừng học cả 14 lớp của IPN) không giúp trên tay người dùng. Nguyên nhân là
cách làm, không phải số lớp.

### 10.2. Thiết kế quay

- **3–4 người quay.** Một phần dữ liệu (`real_test`) **khoá lại để chấm**, không bao giờ vào tập học; phần
  còn lại (`real_tune`) dùng để học. Chia theo người hoặc theo buổi, ghi xuống **trước khi chạy bất kỳ
  phân tích nào**, để không ai vô tình chọn cách chia có lợi.
- **Tên file là nhãn:** `p03_swipe_left_07.mp4` cho biết người `p03`, cử chỉ `swipe_left`, lần thứ 7.
- **Video không lật**, kèm file mốc thời gian thật của từng ảnh, vì FPS webcam không cố định (mục 3.3).
- **Lớp `none` tự quay** gồm nhiều nhóm: tay đứng yên, động tác gần giống (chỉ trỏ, xoay tay, xòe tay),
  đưa tay vào khung, quay liên tục khi làm việc bình thường.
- **Đi qua đúng đường ống của IPN.** Không có bản xử lý riêng cho dữ liệu tự quay.

### 10.3. Kiểm tra ngay lúc quay

**Vấn đề phát hiện khi quay thử:** 2 trong 4 lần quay có động tác chuẩn bị mạnh ngang cử chỉ. Luật gán nhãn
(mục 6.4) chọn bước thay đổi nhanh nhất làm khoảnh khắc chính, không xét chiều, nên có thể chọn nhầm lúc
chuẩn bị. Đo trên IPN: 13% đoạn cử chỉ cũng có tình trạng này. Nhãn IPN cũng có phần mơ hồ.

**Cách làm:** công cụ quay kiểm tra mỗi lần quay **bằng đúng các hàm gán nhãn** của bộ cửa sổ. Lần nào sẽ
dạy sai (không cắt được cửa sổ dương, hoặc có chuyển động khác mạnh ngang khoảnh khắc chính) thì máy dừng và
báo, người quay chọn làm lại hay giữ.

### 10.4. Kiểm tra chất lượng: bài học từ dữ liệu của p02

p02 quay 20 lần (mỗi cử chỉ 5 lần) ngày 2026-11-07. Kiểm tra cho kết quả: **giữ 3, loại 17** (chuyển vào thư
mục `rejected/`, không xoá).

**Vì sao phần lớn không dùng được:**

- p02 làm đi làm lại trong một lần quay: zoom là mở–chụm–mở; vuốt là lấy đà, vuốt, kéo về.
- Vuốt gần như không dời ngang, chủ yếu là búng ngón.
- Luật gán nhãn lấy cú nhanh nhất làm khoảnh khắc chính, mà nhiều lần cú nhanh nhất lại là cú **quay về**.
  Kết quả: 10 lần có đoạn học mang nhãn ngược với chuyển động thật.

**Tiêu chí giữ** — mọi đoạn học của lần quay phải:

1. **đi đúng chiều và đủ rõ:** độ dời ròng theo chiều cử chỉ ít nhất bằng phân vị 25 của IPN cùng lớp;
2. **không chứa cú quay về** quá nửa quãng.

Kiểm độ khắt khe: trên IPN, 65–74% đoạn học đạt; 8 lần quay sạch của p01 đạt 7.

**Bài học:** một ví dụ có nhãn sai còn tệ hơn không có ví dụ. Dữ liệu tự quay phải được kiểm bằng **cùng
thước đo** đã dùng cho dữ liệu chuẩn, và tiêu chí kiểm phải được thử độ khắt khe trên dữ liệu đã biết tốt.

### 10.5. Hiện trạng

| Buổi | Người | Số lần quay | Ghi chú |
|---|---|---|---|
| `thu2` | p01 | 8 | buổi thử |
| 2026-11-06 | p01 | 182 | đủ bốn cử chỉ và các nhóm `none` |
| 2026-11-07 | p02 | 3 giữ lại (17 loại) | chỉ dùng để học: còn thiếu vuốt trái và zoom out |
| 2026-11-08 | p03 | 20 | bốn cử chỉ, mỗi cử chỉ 5 lần; chưa kiểm |

**Việc còn lại của Phase 11:** trích điểm mốc toàn bộ video tự quay; đưa tiêu chí kiểm chất lượng vào mã
nguồn chung và áp cho mọi người; chia `real_tune` / `real_test`; so hình dạng đặc trưng với IPN; học lại;
chấm `real_test` đúng một lần cho hàng thứ ba của Bảng 4 ("kết quả tụt bao nhiêu khi chuyển từ IPN sang
webcam thật").

---

## 11. Kỹ thuật làm dự án học máy cho đáng tin

Phần này không phải thị giác máy tính hay thuật toán học máy, nhưng là phần quyết định các con số có đáng
tin hay không.

### 11.1. Những quy ước bất di bất dịch

| Quy ước | Chặn lỗi gì |
|---|---|
| Một đường ống cho cả ba nguồn | Lệch giữa lúc học và lúc dùng |
| `config.py` là nơi duy nhất chứa hằng số | Hai chỗ dùng hai giá trị khác nhau của cùng một hằng số |
| Quy ước thì đo, không đoán; hằng số chưa đo thì chương trình dừng | Mô hình chạy ngược chiều mà không báo |
| Mất tay ghi NaN, không bỏ ảnh | Nội suy âm thầm qua khoảng mất tay |
| Thứ tự đường ống cố định | Tăng cường hay chuẩn hoá nhầm thứ tự |
| Cửa sổ tính bằng giây | Webcam FPS khác cho cửa sổ thời gian khác |
| Ảnh vào mô hình không lật | Hướng vuốt bị đảo |
| Chỉ toạ độ 2D | Dựa vào độ sâu không tin cậy |
| Chia tập theo người | Rò rỉ dữ liệu, điểm đẹp giả |
| Không LSTM hai chiều, không làm mượt hai phía | Dùng thông tin tương lai, không chạy được thời gian thực |
| Không đường dẫn tuyệt đối, không phụ thuộc card đồ hoạ | Không chạy được trên máy khác |

### 11.2. Mỗi lần chạy có hồ sơ riêng

Mỗi script ghi kết quả vào một thư mục đánh số `results/<phase>/<tên>/run_NN/`, kèm `manifest.json` ghi dòng
lệnh, thời điểm, hạt giống, phiên bản mọi thư viện, và bản sao toàn bộ hằng số. Bảng xuất song song hai dạng
`.csv` (cho máy) và `.md` (cho người). Sáu tháng sau vẫn biết con số nào đến từ đâu.

### 11.3. Tái lập đến từng chữ số

> **Khái niệm — Tái lập.** Chạy lại cùng lệnh cho đúng kết quả cũ.

Hạt giống ngẫu nhiên cố định (`SEED = 42`) cho mọi thư viện. Dự án đã kiểm thật: lần dạy LSTM hiện hành trùng
lần dạy trước **từng chữ số suốt 106 epoch**. Chính việc kiểm này bắt được vài lỗi mà chương trình không báo:
một phép tăng cường làm mất bước đầu cửa sổ khi tay mất dấu ngay sau đó; một bước chạy chậm gấp 3 lần cần
thiết; một file mô hình lưu xong nhưng không mở lại được.

### 11.4. Kiểm thử tự động

> **Khái niệm — Kiểm thử tự động (unit test).** Đoạn mã nhỏ kiểm một tính chất phải luôn đúng, chạy lại sau
> mỗi thay đổi. Như còi báo động: sửa chỗ này làm hỏng chỗ kia thì còi kêu ngay.

Dự án có **236 kiểm thử**. Chúng **không phụ thuộc dữ liệu thật hay webcam**: dùng bàn tay 21 điểm dựng bằng
hình học, với các mẫu vuốt, zoom, đứng yên, vẫy tay có tính chất biết trước. Ví dụ những gì được canh giữ:

- ảnh đen → không thấy tay, toạ độ toàn NaN, không trả `None`;
- mã nguồn bộ bám tay không chứa phép lật ảnh nào;
- co giãn đều bị chuẩn hoá triệt tiêu;
- thêm dữ liệu val/test cực đoan vào cũng không làm ngưỡng luật đổi (ngưỡng chỉ học từ train);
- tăng cường từ chối mọi tập khác train;
- máy trạng thái bấm phím đúng một lần cho một cú vuốt, và không bấm khi tín hiệu nhấp nháy.

### 11.5. Lưu kết quả kèm "tem niêm phong"

Phase 8 có 46 thí nghiệm; học hết mất 170 phút. Mỗi kết quả được lưu kèm một "tem" ghi lại **công thức đã
dùng**. Khi chỉ đổi luật của máy trạng thái, mô hình không đổi, tem còn nguyên, nên dựng lại bảy bảng chỉ mất
0,8 phút thay vì 170. Hai lần, một thông số mới không liên quan suýt làm "rách tem" cả 46 kết quả; nay có kiểm
thử tự động chặn.

### 11.6. Một lệnh dựng lại tất cả

`python scripts/run_all.py` chạy lại toàn bộ: điểm mốc → cửa sổ → luật, rừng, LSTM → bảng kết quả. Bước nào đã
có đầu ra thì bỏ qua. Mọi thư viện được ghim đúng phiên bản trong `requirements.txt`.

### 11.7. Cách xử lý khi một giả định không đứng được trên dữ liệu thật

Bản thiết kế ban đầu (SPEC) có nhiều giả định hoá ra sai khi gặp dữ liệu: luật nhãn 60%, co giãn đều, σ = 0,054,
một ngưỡng chung cho mọi cử chỉ, chiều vuốt của slide. Mỗi lần, dự án làm theo cùng trình tự:

1. dựng bản thử nghiệm trên **tập train**;
2. so các phương án bằng số đo;
3. trình người dùng duyệt;
4. sau đó mới sửa mã nguồn, và ghi lý do kèm ngày vào SPEC.

---

## 12. Kết quả cuối, hạn chế và bài học

### 12.1. Cấu hình cuối

| Thành phần | Giá trị |
|---|---|
| Mô hình | Ghép: vuốt theo LSTM (`run_08`, có tăng cường đổi dáng ngón phụ và tay đứng yên), zoom theo rừng ngẫu nhiên |
| Máy trạng thái, vuốt | ngưỡng 0,85; đồng thuận 4/5 |
| Máy trạng thái, zoom | ngưỡng 0,40; đồng thuận 3/5 |
| Thời gian nghỉ sau lệnh | 1,2 giây |
| Tỉ lệ thấy tay tối thiểu | 70% |
| Phím | vuốt trái → mũi tên phải; vuốt phải → mũi tên trái; zoom `+` / `−` |

### 12.2. Bốn mô hình trên val, có máy trạng thái

| Mô hình | macro-F1 cửa sổ | F1 sự kiện | Lệnh / cử chỉ | Lệnh nhầm / phút |
|---|---|---|---|---|
| Luật | 0,231 | 0,139 | 0,37 | 6,26 |
| Rừng | 0,436 | 0,317 | 0,30 | 0,77 |
| LSTM (`run_08`) | 0,489 | 0,507 | 0,70 | 1,73 |
| **Ghép (dùng cho demo)** | **0,537** | **0,561** | 0,61 | 0,85 |

Mọi con số trên cùng 11 038 cửa sổ và 27 video val. Tập test vẫn niêm phong.

### 12.3. Từ lúc bắt đầu tới giờ

| | Lúc bắt đầu tối ưu | Bây giờ |
|---|---|---|
| Lệnh nhầm khi không ai làm gì, trên video val | 6,6–30 lần/phút | **0,85 lần/phút** |
| Lệnh nhầm khi người dùng nói chuyện có khua tay | 0,64 lần/phút | **0,18 lần/phút** |
| Vuốt mà slide đi ngược chiều | 5/20 | **2/20** |
| Zoom được nhận trên tay người dùng | 0/10 | **10/20** |
| Thử slide thật: cú zoom thành lệnh | 0/12 | **6/12** |

### 12.4. Hạn chế, nói thẳng

- **Khoảng một nửa số cử chỉ vẫn bị bỏ lỡ ở lần làm đầu** trên tay người dùng (40 lời nhắc: vuốt 11 đúng,
  2 ngược, 7 bỏ lỡ; zoom 10 đúng, 4 ngược, 6 bỏ lỡ). Phần lớn do làm khác IPN.
- **Ngưỡng zoom được chọn trên ít dữ liệu** (40 lời nhắc, 12 cú zoom), và chính dữ liệu đó lại dùng để chấm.
  Các con số có phần lạc quan.
- **Trên video IPN, mô hình ghép phát 0,61 lệnh mỗi cử chỉ**, chưa đạt mục tiêu 0,9–1,1.
- **Lớp `none` của IPN thiếu** gõ phím, dùng chuột, khua tay khi nói. Phase 11 đang bù.
- **Tay trái chưa được xét riêng.** Nên dùng tay phải khi demo.
- **Mọi kết quả offline chỉ nói về người, camera và bối cảnh của IPN.** Con số trên webcam thật sẽ có khi
  chấm `real_test`.

### 12.5. Mười lăm bài học lớn nhất

**Về thị giác máy tính:**

1. **Ảnh là bảng số, và thứ tự kênh màu, thứ tự trục, gốc toạ độ đều là quy ước.** Sai quy ước thì thường
   không có lỗi nào hiện ra, chỉ có kết quả âm thầm kém đi.
2. **Đổi bài toán ảnh thành bài toán khung xương** loại bỏ màu, nền, ánh sáng, và giảm dữ liệu hàng nghìn
   lần. Đó là lý do học được trên CPU với vài nghìn ví dụ.
3. **Thời gian là dữ liệu.** FPS dao động, bộ giải mã bỏ ảnh. Phải gắn mốc thời gian thật và làm việc theo
   giây, không theo số ảnh.
4. **"Không thấy" là một thông tin.** Ghi NaN, giữ trục thời gian, quyết định vá hay không ở bước sau.
5. **Chuẩn hoá phải giữ đúng thứ cần giữ.** Đặt gốc ở cổ tay từng bước thì xoá mất cú vuốt.

**Về học máy:**

6. **Chia tập theo người.** Chia sai làm điểm đẹp giả thêm 0,10–0,15, lớn hơn cả khoảng cách giữa hai loại
   mô hình.
7. **Niêm phong tập test**, và chỉ mở đúng một lần.
8. **Tỉ lệ đúng vô nghĩa khi lớp mất cân bằng.** Dùng precision, recall, F1, macro-F1, và luôn so với đường
   cơ sở.
9. **Đo đúng thứ người dùng cảm nhận.** Chấm theo cửa sổ giấu việc hệ thống bấm nhầm 30 lần mỗi phút.
10. **Mô hình học mọi quy luật có trong dữ liệu**, kể cả những trùng hợp ta không muốn dạy (nhẫn, út gập khi
    zoom). Thí nghiệm "đổi đúng một thứ" là cách tìm ra mô hình thật sự dựa vào gì.
11. **Tăng cường dữ liệu phải giữ đáp án và phải giống thật.** Biến đổi bị chuẩn hoá triệt tiêu là vô dụng;
    biến đổi giả hơn thực tế còn có hại.
12. **Một con số đơn lẻ có thể là may mắn.** Báo kèm độ dao động qua nhiều hạt giống, nhiều nhóm người. Chọn
    epoch tốt nhất trên val là lạc quan.
13. **Mỗi mô hình có điểm mạnh riêng.** Rừng nhìn đúng bản chất zoom; LSTM thấy chi tiết ngón tay. Ghép
    chúng theo chuyên môn tốt hơn ép một mô hình làm mọi việc.
14. **Mô hình tốt chưa phải hệ thống tốt.** Tầng quyết định (máy trạng thái) giảm lệnh nhầm hàng chục lần mà
    không đổi mô hình. Độ tin của các mô hình khác nhau không cùng thang đo.
15. **Một ví dụ có nhãn sai tệ hơn không có ví dụ.** Dữ liệu, kể cả dữ liệu công khai, phải được kiểm bằng
    nhiều cách độc lập.

---

## Phụ lục A — Bảng thuật ngữ

| Thuật ngữ | Tiếng Anh | Nghĩa trong tài liệu này |
|---|---|---|
| Thị giác máy tính | computer vision | Dạy máy tính hiểu hình ảnh |
| Học máy | machine learning | Máy tự tìm quy luật từ ví dụ có đáp án |
| Học có giám sát | supervised learning | Học từ ví dụ kèm nhãn đúng |
| Pixel | pixel | Một ô màu nhỏ của ảnh; ba số 0–255 |
| BGR / RGB | | Hai thứ tự lưu ba kênh màu |
| FPS | frames per second | Số ảnh mỗi giây |
| Điểm mốc | landmark, keypoint | 21 điểm trên bàn tay do MediaPipe tìm |
| Ước lượng tư thế | pose estimation | Tìm vị trí các điểm mốc trong ảnh |
| NaN | Not a Number | Giá trị "không có số liệu" |
| Nội suy | interpolation | Ước lượng giá trị giữa hai điểm đã biết |
| Lấy mẫu lại | resampling | Đưa chuỗi về lưới thời gian đều |
| Chuẩn hoá | normalization | Loại khác biệt không liên quan (vị trí, khoảng cách tới camera) |
| Lòng bàn tay | | Đơn vị đo: khoảng cách cổ tay → gốc ngón giữa |
| Cửa sổ | window | Đoạn 1,2 giây, xét mỗi 0,2 giây |
| Đặc trưng | feature | Con số tóm tắt một khía cạnh của cửa sổ |
| Độ duỗi ngón | finger extension | Đầu ngón → cổ tay chia gốc ngón → cổ tay; gập ≈ 0,5, thẳng ≈ 1,3–1,5 |
| Lớp | class | Một trong năm đáp án |
| Nhãn | label | Đáp án đúng gắn với một ví dụ |
| Khoảnh khắc chính | core moment | Bước thay đổi nhanh nhất của một cử chỉ, dùng để gán nhãn cửa sổ |
| Tập train / val / test | | Bài tập về nhà / đề thi thử / đề thi thật niêm phong |
| Rò rỉ dữ liệu | data leakage | Thông tin của đề thi lọt vào bài tập |
| Mất cân bằng lớp | class imbalance | Một lớp đông hơn hẳn |
| Lấy mẫu con | subsampling | Bớt ví dụ của lớp đông |
| Trọng số lớp | class weight | Tính lỗi ở lớp hiếm nặng hơn |
| Tăng cường dữ liệu | data augmentation | Biến đổi ví dụ mà không đổi đáp án |
| Phân vị | percentile | Giá trị mà một tỉ lệ cho trước của dãy nhỏ hơn nó |
| Độ lệch chuẩn | standard deviation, σ | Mức tản mát quanh trung bình |
| Cây quyết định | decision tree | Chuỗi câu hỏi có/không do máy tự chọn |
| Rừng ngẫu nhiên | random forest | 300 cây cùng bỏ phiếu |
| Độ quan trọng hoán vị | permutation importance | Xáo một đặc trưng thì điểm tụt bao nhiêu |
| Mạng nơ-ron | neural network | Công thức lớn với nhiều trọng số được vặn dần khi học |
| Trọng số | weight | Một "núm vặn" của mạng |
| Hàm mất mát | loss | Đo mức sai; càng nhỏ càng tốt |
| Hạ dốc | gradient descent | Cách vặn trọng số theo hướng giảm loss |
| Adam | | Một biến thể hạ dốc tự điều chỉnh bước |
| Epoch | | Một lượt xem hết dữ liệu train |
| Lô | batch | Nhóm ví dụ dùng cho một lần vặn trọng số |
| Dropout | | Tắt ngẫu nhiên một phần đơn vị khi học |
| RNN, LSTM, GRU | | Mạng đọc chuỗi theo thời gian, có trí nhớ |
| Quá khớp | overfitting | Học thuộc lòng bài tập, kém với đề mới |
| Đường học | learning curve | Loss train và val theo từng epoch |
| Dừng sớm | early stopping | Ngừng dạy khi val hết tiến bộ |
| Checkpoint | | Bản lưu mạng ở thời điểm tốt nhất |
| Lạc quan do chọn lọc | selection bias | Báo điểm cao nhất trong nhiều lần thử |
| Mô hình ghép | ensemble | Mỗi mô hình lo phần nó giỏi |
| Độ tin | confidence | Mô hình chắc tới đâu, 0–1; không phải xác suất đã hiệu chuẩn |
| Accuracy | | Tỉ lệ đúng; vô nghĩa khi lớp mất cân bằng |
| Precision | | Trong các lần báo, bao nhiêu lần đúng |
| Recall | | Trong các trường hợp thật, bắt được bao nhiêu |
| F1, macro-F1 | | Điểm gộp precision và recall; trung bình năm lớp |
| Ma trận nhầm lẫn | confusion matrix | Bảng lớp thật × lớp đoán |
| Đường cơ sở | baseline | Mô hình "ngốc" làm mốc |
| Mức cửa sổ / mức sự kiện | window / event level | Chấm từng đoạn / chấm từng lệnh như người dùng thấy |
| Lệnh nhầm mỗi phút | false activations per minute | Số lệnh phát ra khi không có cử chỉ |
| Hạt giống | seed | Cố định để tái lập; đổi để đo độ dao động |
| k-fold theo nhóm người | group k-fold | Lần lượt để mỗi nhóm người làm đề thi |
| Thí nghiệm có kiểm soát | ablation | Đổi đúng một yếu tố rồi đo |
| Thí nghiệm phản thực tế | counterfactual probe | Sửa đúng một khía cạnh của ví dụ thật để xem mô hình dựa vào gì |
| Lệch miền | domain shift | Dữ liệu lúc dùng khác lúc học |
| Máy trạng thái | finite state machine | "Người trợ lý" quyết định khi nào bấm phím |
| Đồng thuận k trên n | k-of-n | Cần k nhịp đồng ý trong n nhịp |
| Thời gian nghỉ | cooldown | Không phát lệnh mới trong 1,2 giây sau một lệnh |
| Lấy đà | | Kéo tay ngược chiều trước khi vuốt |
| Ghi và phát lại | record & replay | Lưu 21 điểm của một phiên để chạy lại qua mọi cấu hình |
| Tái lập | reproducibility | Chạy lại cùng lệnh ra đúng kết quả cũ |
| Kiểm thử tự động | unit test | Đoạn mã kiểm một tính chất phải luôn đúng |

---

## Phụ lục B — Tìm hiểu thêm ở đâu

**Lý thuyết nền, viết cho người mới** (thư mục `docs/`, đọc theo thứ tự):

| File | Nội dung |
|---|---|
| [00-cong-cu-va-numpy.md](00-cong-cu-va-numpy.md) | Môi trường, numpy, đọc lỗi |
| [01-anh-so-va-video.md](01-anh-so-va-video.md) | Pixel, kênh màu, FPS, đọc webcam |
| [02-uoc-luong-tu-the-ban-tay.md](02-uoc-luong-tu-the-ban-tay.md) | Điểm mốc, MediaPipe |
| [03-bieu-dien-khung-xuong-ban-tay.md](03-bieu-dien-khung-xuong-ban-tay.md) | Chuẩn hoá, góc khớp, vận tốc, đặc trưng |
| [04-mo-hinh-chuoi-thoi-gian.md](04-mo-hinh-chuoi-thoi-gian.md) | Cửa sổ trượt, rừng ngẫu nhiên, RNN, LSTM |
| [05-danh-gia-phan-loai.md](05-danh-gia-phan-loai.md) | Ma trận nhầm lẫn, precision/recall, rò rỉ dữ liệu |
| [MediaPipe_Hands_Ban_Tieng_Viet.md](MediaPipe_Hands_Ban_Tieng_Viet.md) | Bài báo MediaPipe Hands, bản tiếng Việt |

**Tổng kết theo giai đoạn, nhiều số liệu hơn:**

| File | Phạm vi |
|---|---|
| [tong-ket-phase-0-1.md](tong-ket-phase-0-1.md) | Khung dự án, thu nhận điểm mốc |
| [tong-ket-den-phase-5.md](tong-ket-den-phase-5.md) | Dữ liệu IPN, cửa sổ, mô hình luật |
| [tong-ket-den-phase-7.md](tong-ket-den-phase-7.md) | Rừng ngẫu nhiên, LSTM, mô hình ghép |
| [tong-ket-phase-8-10.md](tong-ket-phase-8-10.md) | Đánh giá hai mức, máy trạng thái, demo |

**Ghi chú kỹ thuật chi tiết:** `results/phase6/notes.md`, `results/phase7/notes.md`,
`results/phase8/notes.md`, `results/phase9/notes.md`, `results/phase10/notes.md`,
`results/phase10/final_config.md`, `results/phase11/qa_p02.md`.

**Thiết kế và quy ước:** [SPEC.md](SPEC.md) (13 phase, kèm mọi thay đổi có ngày và lý do),
[../CLAUDE.md](../CLAUDE.md) (quy ước bắt buộc), [gestures.md](gestures.md) (cách làm cử chỉ),
[ipn_format.md](ipn_format.md) (định dạng dữ liệu IPN), [huong-dan-quay-du-lieu.md](huong-dan-quay-du-lieu.md)
(giao thức quay Phase 11).

**Chạy thử:** xem [README.md](../README.md). Lệnh demo:

```bash
python scripts/demo.py --model hybrid
```
