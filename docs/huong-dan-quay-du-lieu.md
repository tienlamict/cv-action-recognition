# Hướng dẫn quay dữ liệu cử chỉ (Phase 11)

**Mục đích:** dạy mô hình nhận cử chỉ **theo cách làm tự nhiên của chính các bạn**. Hiện mô
hình chỉ học từ bộ video IPN Hand, nên kiểu làm khác với người diễn IPN hay bị bỏ lỡ.

Mỗi buổi khoảng **30 phút**. Công cụ quay tự hiện lời nhắc, tự đặt tên file, và tự lưu mốc thời
gian. **Người quay tự quyết nhịp:** làm xong một cử chỉ thì bấm SPACE để lưu và sang cử chỉ tiếp
theo.

---

## 1. Trước khi quay

- **Hỏi ý kiến người quay.** Video có thể thấy mặt người quay. Video chỉ lưu trên máy này và chỉ
  dùng cho đề tài.
- **Mỗi người một mã:** `p01` cho chủ đề tài, rồi `p02`, `p03`, `p04`. Giữ nguyên mã của mỗi người
  qua mọi buổi.
- **Số buổi:**
  - `p01`: **hai buổi, khác ngày.** Buổi đầu quay đủ; buổi sau mỗi cử chỉ 15 lần (`--takes 15`).
  - Người khác: ít nhất một buổi; hai buổi khác ngày nếu được.
- **Chỗ ngồi giống lúc dùng demo thật:**
  - cùng webcam;
  - cách camera 0,4–0,7 m;
  - đủ sáng;
  - dùng tay phải, chỉ một bàn tay trong khung.
- **Tay trái đặt sẵn trên phím SPACE, tay phải làm cử chỉ.** Đừng dùng cùng một tay vừa làm cử
  chỉ vừa bấm phím: cú với tay xuống bàn phím sẽ nằm trong video như một chuyển động lớn.

---

## 2. Lệnh quay

```
conda activate action-recognition
python scripts/record_session.py --person p02
```

- **Buổi thứ hai của `p01`:**
  ```
  python scripts/record_session.py --person p01 --takes 15
  ```
- **Quay dở thì chạy lại đúng lệnh đó** (cùng ngày): công cụ làm tiếp các lần còn thiếu. Khác ngày
  thì thêm `--session <tên thư mục buổi cũ>`, ví dụ `--session 2026-11-07`.
- **Chỉ quay lại một khối:** thêm `--blocks gestures` (hoặc `near`, `transition`, `continuous`).

---

## 3. Trên màn hình

**Nhịp của mỗi lần quay:**

1. Đọc dòng hai trên màn hình, ví dụ "VUOT TRAI…". Màn hình hiện số giây đã quay sau chữ **REC**.
2. Đặt tay vào tư thế, làm cử chỉ **một lần**, rồi giữ yên hoặc hạ tay.
3. Bấm **SPACE**: lần này được lưu, và lần tiếp theo **bắt đầu quay ngay**. Đọc lời nhắc mới, rồi
   làm tiếp. Không cần vội: cứ thong thả đặt tay vào tư thế rồi mới làm.

| Thấy gì | Làm gì |
|---|---|
| Chữ lớn **SPACE** | máy đang nghỉ; bấm SPACE để bắt đầu quay |
| **REC** và số giây | đang quay; làm cử chỉ, xong thì bấm SPACE |
| "Lan vua roi chi thay tay …%" | bấm `r` để quay lại lần đó |
| "Qua 10s…" | quên bấm; bấm SPACE nếu đã làm xong cử chỉ, `r` nếu muốn quay lại |
| "Bam qua nhanh…" | SPACE bị bấm hai lần liền; lần đó được quay lại, cứ làm tiếp |
| "Xong khoi …" | nghỉ một chút, bấm SPACE để sang khối sau |

| Phím | Đang quay | Đang nghỉ |
|---|---|---|
| SPACE | lưu lần này, **bắt đầu ngay lần sau** | bắt đầu quay |
| `p` | lưu lần này rồi nghỉ | — |
| `r` | bỏ lần đang quay, quay lại ngay | quay lại lần vừa lưu |
| `q` | thoát; lần đang quay dở bị bỏ | thoát |

Bản bị bỏ chuyển vào thư mục `rejected/`, không bao giờ bị xoá. Thoát rồi chạy lại lệnh là làm
tiếp đúng chỗ dở.

Màn hình được lật như gương cho dễ nhìn. Video lưu lại thì **không** lật.

---

## 4. Bốn khối của một buổi

| Khối | Làm gì | Số lần | Khoảng |
|---|---|---|---|
| `gestures` | vuốt trái, vuốt phải, zoom in, zoom out, xáo trộn thứ tự | 25 mỗi cử chỉ (buổi sau: 15) | 6–8 phút |
| `near` | vẫy tay, hất lên, hất xuống, xoay cổ tay, xoè cả năm ngón, chỉ trỏ | 10 mỗi động tác | 4–5 phút |
| `transition` | đưa tay vào khung rồi hạ tay xuống | 10 | 1 phút |
| `continuous` | tay để yên; làm việc bình thường; với cốc, gãi đầu; nói chuyện; khung trống | quay liên tục, tự cắt file | 12 phút |

Phần quay liên tục chỉ cần bấm SPACE một lần ở đầu mỗi phần, rồi làm theo lời nhắc tới khi hết giờ
(`p` để nghỉ giữa chừng).

Ba khối sau đều là **"không phải lệnh"**. Chúng dạy mô hình biết im lặng, nên quan trọng không kém
bốn cử chỉ.

---

## 5. Làm cử chỉ thế nào

**Làm theo cách tự nhiên của bạn, như khi trình chiếu thật.** Không cần bắt chước người diễn IPN.
Nhưng giữ phần cốt lõi của mỗi cử chỉ, để nó không trùng với các động tác "không phải lệnh":

| Cử chỉ | Phải có | Tránh |
|---|---|---|
| Vuốt trái, vuốt phải | tay đi **ngang**, một chiều, dứt khoát | hất lên hoặc xuống; vẫy qua lại; lấy đà ngược chiều quá mạnh |
| Zoom in | ngón cái **tách** khỏi ngón trỏ (và ngón giữa); các ngón khác để tự nhiên | xoè **cả năm ngón** từ nắm tay — đó là động tác "không phải lệnh" |
| Zoom out | ngón cái **chụm** về ngón trỏ | nắm cả bàn tay lại |

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
- Báo lại cho Claude: **ai đã quay những buổi nào.** Bước sau là:
  - trích 21 điểm tay bằng đúng hàm đã dùng cho IPN;
  - chia buổi nào để học, buổi nào khoá để chấm;
  - học lại mô hình, rồi so với mô hình hiện tại.
