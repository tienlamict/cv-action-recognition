# Hướng dẫn quay dữ liệu cử chỉ (Phase 11)

**Mục đích:** dạy mô hình nhận cử chỉ **theo cách làm tự nhiên của chính các bạn**. Hiện mô
hình chỉ học từ bộ video IPN Hand, nên kiểu làm khác với người diễn IPN hay bị bỏ lỡ.

Buổi của `p01` (chủ đề tài) khoảng **30 phút**. Người khác chỉ quay bốn cử chỉ, mỗi cử chỉ 5
lần, khoảng **2 phút**. Công cụ quay tự hiện lời nhắc, tự đặt tên file, và tự lưu mốc thời gian.
**Mỗi lần quay: bấm `b` để bắt đầu, làm cử chỉ, bấm SPACE để kết thúc.** Máy tự kiểm tra từng lần
quay cử chỉ, và báo khi nên quay lại (mục 3).

---

## 1. Trước khi quay

- **Hỏi ý kiến người quay.** Video có thể thấy mặt người quay. Video chỉ lưu trên máy này và chỉ
  dùng cho đề tài.
- **Mỗi người một mã:** `p01` cho chủ đề tài, rồi `p02`, `p03`, `p04`. Giữ nguyên mã của mỗi người
  qua mọi buổi.
- **Số buổi và nội dung:**
  - `p01`: **hai buổi, khác ngày.** Buổi đầu quay đủ bốn khối; buổi sau mỗi cử chỉ 15 lần
    (`--takes 15`).
  - Người khác (`p02`, `p03`…): **chỉ quay bốn cử chỉ**, mỗi cử chỉ 5 lần. Công cụ tự làm vậy
    khi mã người không phải `p01`. Một buổi là đủ; hai buổi khác ngày nếu được.
- **Chỗ ngồi giống lúc dùng demo thật:**
  - cùng webcam;
  - cách camera 0,4–0,7 m;
  - đủ sáng;
  - dùng tay phải, chỉ một bàn tay trong khung.
- **Tay trái đặt sẵn trên bàn phím, tay phải làm cử chỉ.** Phím `b` và SPACE nằm cạnh nhau,
  tay trái bấm được cả hai. Đừng dùng cùng một tay vừa làm cử chỉ vừa bấm phím: cú với tay xuống
  bàn phím sẽ nằm trong video như một chuyển động lớn.

---

## 2. Lệnh quay

```
conda activate action-recognition
python scripts/record_session.py --person p02
```

- Với `p02` trở đi, lệnh trên chỉ quay bốn cử chỉ, mỗi cử chỉ 5 lần. Muốn khác thì thêm
  `--takes`, ví dụ `--takes 10`.
- **Buổi thứ hai của `p01`:**
  ```
  python scripts/record_session.py --person p01 --takes 15
  ```
- **Quay dở thì chạy lại đúng lệnh đó** (cùng ngày): công cụ làm tiếp các lần còn thiếu. Khác ngày
  thì thêm `--session <tên thư mục buổi cũ>`, ví dụ `--session 2026-11-07`.
- **Chỉ quay lại một khối:** thêm `--blocks gestures` (hoặc `near`, `transition`, `continuous`).
- **Đừng thêm `--no-track`** khi quay cử chỉ. Không theo dõi tay thì máy không tự kiểm tra được.

---

## 3. Trên màn hình

**Nhịp của mỗi lần quay:**

1. Đọc dòng hai trên màn hình, ví dụ "VUOT TRAI…". Máy đang nghỉ, giữa màn hình là chữ lớn
   **Bam B**.
2. Bấm **`b`** để bắt đầu quay. Màn hình hiện số giây đã quay sau chữ **REC**.
3. **Đợi khoảng 1 giây.** Đặt tay vào tư thế bắt đầu, làm cử chỉ **một lần**, rồi **giữ yên
   khoảng 1 giây**.
4. Bấm **SPACE** để kết thúc. Lần này được lưu; máy nghỉ và hiện lời nhắc của lần sau. Sẵn sàng
   thì bấm `b`. Không cần vội.

Nửa giây đầu và nửa giây cuối của mỗi lần quay cử chỉ không được dùng để dạy mô hình. Vì vậy
cần đợi 1 giây trước khi làm, và giữ yên 1 giây trước khi bấm.

### Máy tự kiểm tra từng lần quay cử chỉ

Ngay khi bấm SPACE, máy xem lại lần vừa quay **đúng theo cách mà bước dạy mô hình sẽ dùng**.
Lần đó ổn thì màn hình hiện "Da luu …". Nếu lần đó dễ dạy sai, màn hình hiện một dòng màu cam bắt
đầu bằng "Lan vua roi: …". Khi đó:

- bấm `r` để quay lại đúng lần đó (nên làm);
- hoặc bấm `b` để giữ lần đó và quay lần sau, nếu chắc mình đã làm đúng.

| Lời báo | Nghĩa là | Lần sau |
|---|---|---|
| "chua ro - chuan bi cham, lam dut khoat" | Động tác chuẩn bị (kéo tay lấy đà, mở hay chụm ngón trước) nhanh gần bằng cử chỉ. Máy có thể tưởng lúc chuẩn bị là cử chỉ. | chuẩn bị thật chậm, cử chỉ nhanh và rõ (mục 5) |
| "lam som qua - doi 1 giay roi hay lam" | Làm cử chỉ ngay sau khi bấm `b`, rơi vào nửa giây đầu không dùng được. | đợi khoảng 1 giây rồi mới làm |
| "bam SPACE som qua - giu yen 1 giay" | Bấm SPACE ngay sau cử chỉ, cử chỉ rơi vào nửa giây cuối. | làm xong, giữ yên 1 giây rồi mới bấm |
| "khong thay tay luc lam cu chi", "mat tay quanh cu chi, hoac qua ngan" | Máy không thấy tay đúng lúc làm, hoặc lần quay quá ngắn. | để cả bàn tay trong khung, lòng bàn tay hướng về camera |
| "chi thay tay …%" | Máy thấy tay chưa tới một nửa thời gian. | như trên |

### Màn hình và phím

| Thấy gì | Làm gì |
|---|---|
| Chữ lớn **Bam B** | máy đang nghỉ; bấm `b` để bắt đầu quay |
| **REC** và số giây | đang quay; làm cử chỉ, xong thì bấm SPACE |
| "Da luu …" | lần vừa rồi đã lưu, không có gì phải sửa |
| Dòng cam "Lan vua roi: …" | `r` quay lại lần đó, `b` giữ lần đó và quay lần sau |
| "Qua 10s…" | quên bấm; bấm SPACE nếu đã làm xong cử chỉ, `r` để bỏ lần đó |
| "Qua ngan, da bo…" | SPACE bấm ngay sau `b`; lần đó bị bỏ, bấm `b` để quay lại |
| "Dang nghi…" | vừa bấm SPACE lúc máy đang nghỉ; muốn quay thì bấm `b` |
| "Xong khoi …" | nghỉ một chút, bấm `b` để sang khối sau |
| "Het buoi" | lần cuối vừa bị báo: `r` quay lại, SPACE giữ và kết thúc buổi |

| Phím | Đang quay | Đang nghỉ |
|---|---|---|
| `b` | — | bắt đầu quay; sau lời báo: giữ lần vừa rồi |
| SPACE | kết thúc và lưu lần này | — |
| `r` | bỏ lần đang quay | quay lại lần vừa lưu |
| `q` | thoát; lần đang quay dở bị bỏ | thoát |

Caps Lock bật cũng không sao: `B` hay `b` đều được.

Bản bị bỏ chuyển vào thư mục `rejected/`, không bao giờ bị xoá. Thoát rồi chạy lại lệnh là làm
tiếp đúng chỗ dở.

Màn hình được lật như gương cho dễ nhìn. Video lưu lại thì **không** lật.

---

## 4. Bốn khối của một buổi

`p01` quay cả bốn khối. Người khác chỉ quay khối `gestures`, mỗi cử chỉ 5 lần.

| Khối | Làm gì | Số lần | Khoảng |
|---|---|---|---|
| `gestures` | vuốt trái, vuốt phải, zoom in, zoom out, xáo trộn thứ tự | 25 mỗi cử chỉ (buổi sau của `p01`: 15; người khác: 5) | 6–8 phút (5 lần: khoảng 2 phút) |
| `near` | vẫy tay, hất lên, hất xuống, xoay cổ tay, xoè cả năm ngón, chỉ trỏ | 10 mỗi động tác | 4–5 phút |
| `transition` | đưa tay vào khung rồi hạ tay xuống | 10 | 1 phút |
| `continuous` | tay để yên; làm việc bình thường; với cốc, gãi đầu; nói chuyện; khung trống | quay liên tục, tự cắt file | 12 phút |

Phần quay liên tục chỉ cần bấm `b` một lần ở đầu mỗi phần, rồi làm theo lời nhắc tới khi hết
giờ. **Đừng bấm SPACE giữa chừng:** SPACE dừng phần đó lại.

Ba khối sau đều là **"không phải lệnh"**. Chúng dạy mô hình biết im lặng, nên quan trọng không kém
bốn cử chỉ.

---

## 5. Làm cử chỉ thế nào

**Làm theo cách tự nhiên của bạn, như khi trình chiếu thật.** Không cần bắt chước người diễn IPN.
Nhưng giữ phần cốt lõi của mỗi cử chỉ, để nó không trùng với các động tác "không phải lệnh":

| Cử chỉ | Phải có | Tránh |
|---|---|---|
| Vuốt trái, vuốt phải | tay đi **ngang**, một chiều, dứt khoát | hất lên hoặc xuống; vẫy qua lại; kéo tay ngược chiều lấy đà |
| Zoom in | ngón cái **tách** khỏi ngón trỏ (và ngón giữa); các ngón khác để tự nhiên | xoè **cả năm ngón** từ nắm tay — đó là động tác "không phải lệnh"; chụm nhanh ngay trước khi tách |
| Zoom out | ngón cái **chụm** về ngón trỏ | nắm cả bàn tay lại; mở nhanh ngay trước khi chụm |

**Chuẩn bị chậm, cử chỉ dứt khoát.** Máy tìm cử chỉ ở **lúc tay chuyển động nhanh nhất** trong lần
quay. Nếu động tác chuẩn bị cũng nhanh như cử chỉ, máy có thể tưởng lúc chuẩn bị là cử chỉ. Khi
đó nó học sai: lúc mở tay để chuẩn bị bị dạy là zoom out. Ở buổi quay thử, 2 trên 4 lần có động
tác chuẩn bị nhanh gần bằng cử chỉ. Nên làm:

| Cử chỉ | Tư thế bắt đầu (đặt thong thả) | Cử chỉ (nhanh, rõ) |
|---|---|---|
| Vuốt trái, vuốt phải | tay giơ yên trong khung | hất ngang một lần, rõ ràng |
| Zoom in | ngón cái **chụm sẵn** vào ngón trỏ | tách ngón cái ra |
| Zoom out | ngón cái và ngón trỏ **mở sẵn** | chụm ngón cái về ngón trỏ |

- **Mỗi lần chỉ làm một cử chỉ,** rồi bấm SPACE. Không lặp lại cử chỉ trong cùng một lần quay.
- **Khác nhau một chút giữa các lần là tốt:** nhanh chậm, rộng hẹp, vị trí tay. Đừng làm như máy.
- **Trái, phải là trái, phải của chính bạn,** không phải của màn hình.

**Trong các phần quay liên tục**, cứ làm tự nhiên theo lời nhắc:

- **Tay để yên:** đặt tay trong khung, không làm gì.
- **Làm việc bình thường:** gõ phím, dùng chuột, đọc tài liệu.
- **Với cốc, gãi đầu, chỉnh kính:** các cử động lớn nhưng vô tình.
- **Nói chuyện:** nói như đang thuyết trình, khua tay tự nhiên.
- **Khung trống:** để tay ra ngoài khung.

---

## 6. Sau khi quay

- Video nằm ở `data/raw/<ngày>/`, ví dụ `p02_swipe_left_07.mp4`, kèm file `.json` cùng tên chứa
  mốc thời gian.
- **Không đổi tên, không xoá file:** tên file chính là nhãn. Bản quay hỏng nằm trong `rejected/`.
- Cuối buổi, màn hình lệnh liệt kê những lần **bị báo nhưng vẫn giữ**. Không cần làm gì thêm: bước
  trích điểm mốc sẽ kiểm tra lại các lần đó trên video.
- Báo lại cho Claude: **ai đã quay những buổi nào.** Bước sau là:
  - trích 21 điểm tay bằng đúng hàm đã dùng cho IPN;
  - chia buổi nào để học, buổi nào khoá để chấm;
  - học lại mô hình, rồi so với mô hình hiện tại.
