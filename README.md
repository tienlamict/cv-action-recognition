# Lý thuyết cho đồ án Nhận dạng hành động từ khung xương

Bộ tài liệu này giải thích toàn bộ phần lý thuyết cần nắm cho đồ án
"Nhận dạng hành động người thời gian thực dựa trên ước lượng tư thế".

Nó được viết cho người **chưa từng học thị giác máy tính**. Không giả định
bạn biết CNN là gì, không giả định bạn biết mạng nơ-ron là gì. Mọi khái niệm
đều được xây từ đầu, theo thứ tự phụ thuộc: khái niệm sau chỉ dùng những gì
khái niệm trước đã giải thích.

---

## Các file

| File | Tầng | Nội dung | Đọc ở tuần |
|---|---|---|---|
| [`00-cong-cu-va-numpy.md`](00-cong-cu-va-numpy.md) | 0 | Môi trường conda, numpy, đọc lỗi, git | 1 |
| [`01-anh-so-va-video.md`](01-anh-so-va-video.md) | 1 | Pixel, kênh màu, BGR/RGB, FPS, đọc webcam | 2 |
| [`02-uoc-luong-tu-the.md`](02-uoc-luong-tu-the.md) | 2 | Keypoint, bản đồ nhiệt, top-down/bottom-up, BlazePose | 3 |
| [`03-bieu-dien-khung-xuong.md`](03-bieu-dien-khung-xuong.md) | 3 | Chuẩn hóa, góc khớp, vận tốc, đặc trưng | 4 |
| [`04-mo-hinh-chuoi-thoi-gian.md`](04-mo-hinh-chuoi-thoi-gian.md) | 4 | Cửa sổ trượt, rừng ngẫu nhiên, RNN, LSTM | 6, 7, 8 |
| [`05-danh-gia-phan-loai.md`](05-danh-gia-phan-loai.md) | 5 | Ma trận nhầm lẫn, precision/recall, rò rỉ dữ liệu | 8, 9 |

---

## Đọc theo thứ tự nào

Đọc tuần tự từ 00 đến 05. Đây không phải lời khuyên hình thức — các tầng thực
sự phụ thuộc nhau:

```
00 Công cụ
   └─ numpy: mọi dữ liệu khung xương đều là mảng numpy
      │
01 Ảnh số ─────────────────────────┐
   └─ ảnh là mảng số               │ đầu vào của
      │                            │ ước lượng tư thế
02 Ước lượng tư thế ───────────────┘
   └─ ảnh → 33 điểm khớp
      │  (đầu ra của tầng 2 là đầu vào của tầng 3)
03 Biểu diễn khung xương
   └─ 33 điểm thô → vector đặc trưng có ý nghĩa
      │
04 Mô hình chuỗi thời gian
   └─ chuỗi vector → nhãn hành động
      │
05 Đánh giá
   └─ nhãn dự đoán + nhãn thật → kết luận đáng tin
```

Nếu bạn nhảy cóc vào tầng 4 (LSTM) mà chưa hiểu tầng 3 (chuẩn hóa), bạn sẽ
huấn luyện một mô hình học đúng thứ sai — và tệ hơn, bạn sẽ không biết là nó
đang học sai, vì con số độ chính xác vẫn đẹp.

---

## Cách dùng khi viết báo cáo

**Chương 2 "Cơ sở lý thuyết" của báo cáo gần như chính là các file này**, viết
lại bằng lời của bạn và cắt bớt phần thực hành.

Ánh xạ gợi ý:

| Mục chương 2 | Lấy từ |
|---|---|
| 2.1 Biểu diễn ảnh số và video | file `01`, phần "Ảnh là gì" đến "FPS" |
| 2.2 Ước lượng tư thế người | file `02`, gần như toàn bộ |
| 2.3 Biểu diễn và chuẩn hóa khung xương | file `03`, phần lý thuyết |
| 2.4 Mô hình chuỗi thời gian | file `04`, phần RNN/LSTM |
| 2.5 Phương pháp đánh giá | file `05`, phần chỉ số |

**Đừng chép nguyên văn.** Hội đồng đọc được văn phong không phải của sinh
viên. Cách dùng đúng: đọc kỹ, đóng file lại, tự viết ra bằng lời mình. Nếu
viết không nổi đoạn nào thì quay lại đọc đoạn đó — đó chính là chỗ bạn chưa
hiểu.

---

## Mỗi file có gì

Cấu trúc thống nhất:

- **Câu hỏi mở đầu** — vấn đề mà tầng này giải quyết
- **Phần lý thuyết** — giải thích từ trực giác đến công thức
- **Nối vào đồ án** — khái niệm này xuất hiện ở đâu trong code của bạn
- **Cạm bẫy** — những chỗ người mới hay sai
- **Tự kiểm tra** — câu hỏi. Nếu trả lời được không cần nhìn tài liệu thì bạn
  đã nắm tầng đó
- **Đưa gì vào báo cáo** — gợi ý cụ thể

Ký hiệu dùng chung trong cả bộ tài liệu:

- `T` — độ dài cửa sổ thời gian, tính bằng số frame (mặc định 30)
- `J` — số khớp dùng (33 điểm MediaPipe, còn 23 sau khi bỏ mặt)
- `C` — số lớp hành động (6)
- `N` — số mẫu
- `H`, `W` — chiều cao và chiều rộng ảnh, tính bằng pixel
