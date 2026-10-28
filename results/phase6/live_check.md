# Phase 6 — Thử trực tiếp và quyết định về Phase 11

> **Trạng thái: NHÁP.** Claude soạn ngày 2026-10-28, gom số liệu thử trực tiếp từ Phase 6 tới
> Phase 10. **Bật hay không bật Phase 11 là quyết định của người dùng**, ghi ở mục 4.
>
> SPEC đặt điểm quyết định ngay sau lần thử trực tiếp ở Phase 6; khi đó file này chưa được
> ghi. Nếu nhu cầu chỉ lộ ra ở Phase 10, SPEC cho làm bản tối giản: chỉ quay tập đánh giá,
> không điều chỉnh gì.

## 1. Các lần thử trực tiếp

| Ngày | Mô hình | Phiên | Kết quả chính |
|---|---|---|---|
| 2026-10-09 (Phase 6) | rừng | `results/phase6/live_rf_work.csv`, `live_rf_swipes.csv` | Zoom nhận khá tốt, vuốt kém. Người dùng vuốt "kiểu thông thường": bàn tay giữ nguyên dáng, đi ra rồi quay về. Cú hất của IPN thì khác (`results/phase6/notes.md` mục 7) |
| 2026-10-25 (Phase 10) | ghép | thử hướng vuốt | Vuốt sang trái của người dùng ra `swipe_left`; giữ `IPN_FLIP_X = 1` |
| 2026-10-25 và 26 (Phase 10) | LSTM `run_08`, cấu hình cuối | `gestures_01`, `gestures_02`: 40 lời nhắc, 10 mỗi lớp | Nhận đúng: `swipe_left` 6/10, `swipe_right` 5/10, `zoom_in` 4/10, `zoom_out` 0/10 |
| 2026-10-25 và 26 (Phase 10) | LSTM `run_08`, cấu hình cuối | `talking_01`, `talking_02` (10,9 phút); `reading_01`, `typing_01` | Khi nói chuyện: 0,18 lệnh nhầm mỗi phút, 0,79 nếu tính trên phút có tay. Khi đọc và gõ phím, camera không thấy tay |

## 2. Bốn dấu hiệu của SPEC

| Dấu hiệu | Bằng chứng | Kết luận |
|---|---|---|
| 1. Đã làm đúng `docs/gestures.md` mà một lớp vẫn đúng dưới 7/10 lần | Cả bốn lớp đều dưới 7/10. Nhưng **cử chỉ chưa làm đúng tài liệu**: nhẫn và út duỗi ở cả 20 cú zoom (0/20 cú nằm trong hộp IPN). Lấy đà ngược chiều làm 2/20 lời nhắc vuốt phát lệnh ngược chiều trước (5/20 ở 0,75 · 3/5) | **Chưa xác định được**, vì vế "đã làm đúng" chưa đạt |
| 2. Kích hoạt nhầm khi làm việc bình thường hơn 0,5 lần mỗi phút | 0,18 mỗi phút khi nói chuyện; 0,79 mỗi phút có tay; đọc và gõ phím 0 vì không thấy tay | **Không**, theo cách đo của SPEC (mỗi phút của phiên). Vượt nếu tính trên phút có tay |
| 3. Môn học đòi đánh giá trong điều kiện thật | — | người dùng biết |
| 4. Có người khác cần dùng hệ thống | — | người dùng biết |

## 3. Hai lựa chọn

- **Không bật.**
  - README đã có đoạn "Chiến lược dữ liệu: chỉ IPN Hand", nêu rõ giới hạn; báo cáo nhắc lại.
  - Bảng 4 của Phase 8 giữ hai hàng.
- **Bật bản tối giản.**
  - Quay tập `real_test`: ít nhất hai buổi khác ngày, theo giao thức bước 12 của cẩm nang.
  - Chạy `evaluate.py --split real_test --final` đúng một lần, cho hàng thứ ba của Bảng 4.
  - Không điều chỉnh gì.

**Đề xuất của Claude:** theo đúng chữ SPEC thì chưa dấu hiệu nào đạt, nên không bật, trừ khi
dấu hiệu 3 hoặc 4 đúng. Nếu muốn đo dấu hiệu 1 cho chắc, ghi thêm một phiên
`bench.py record gestures` khi đã gập nhẫn, út và bỏ lấy đà.

## 4. Quyết định

- [ ] Không bật Phase 11
- [ ] Bật bản tối giản

Người dùng chọn: ……………… Ngày: ………………
