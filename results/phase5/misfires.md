# Phase 5 — Báo nhầm khi làm việc bình thường

> **Trạng thái: NHÁP.** Claude soạn ngày 2026-10-28 từ các phiên đã ghi. **Chờ người dùng xác
> nhận, hoặc thay bằng phép đo đúng SPEC** (mục 3).
>
> SPEC Phase 5 yêu cầu: gõ phím và dùng chuột 2 phút với `demo.py --model rules --log`, đếm số
> đợt báo nhầm. Đó là đường cơ sở để so ở Phase 6 và 10.

## 1. Chưa có phép đo đúng như SPEC

- Ở Phase 5 không có phiên 2 phút gõ phím và dùng chuột nào được ghi.
- Phiên gần nhất là `results/phase10/sessions/typing_01.npz` (`bench.py record typing`). Nó
  chỉ dài 0,5 phút, và camera không thấy tay lần nào. Vì vậy mọi mô hình báo nhầm 0 lần.
- Con số 0 đó chỉ nói một điều: lúc gõ phím, tay nằm ngoài khung nên hệ thống không thể báo
  nhầm. Nó không nói gì về mô hình.

## 2. Đường cơ sở thay thế: các phiên không làm cử chỉ, có tay trong khung

Cụm nhãn khác `none` **chưa qua máy trạng thái**, đếm như `summarize_log.py`: một chuỗi dự
đoán liền nhau cùng lớp là một cụm. Chạy lại các phiên `bench.py record` qua đúng đường ống
của demo.

| Phiên | Phút | Có tay | Luật | Rừng | LSTM (`run_08`) |
|---|---|---|---|---|---|
| `reading_01` | 0,5 | 0% | 0 | 0 | 0 |
| `typing_01` | 0,5 | 0% | 0 | 0 | 0 |
| `talking_01` | 0,9 | 89% | 13 (13,7/phút) | 5 (5,3/phút) | 10 (10,6/phút) |
| `talking_02` | 10,0 | 17% | 40 (4,0/phút) | 21 (2,1/phút) | 29 (2,9/phút) |
| **Gộp** | 12,0 | 21% | **53 (4,4/phút)** | 26 (2,2/phút) | 39 (3,3/phút) |
| Mỗi phút có tay | | | 21,0 | 10,3 | 15,4 |

**Qua máy trạng thái ở cấu hình cuối** (0,85 · 4/5), cùng hai phiên talking, số lệnh nhầm mỗi
phút (`results/phase10/analyze/run_06`):

- luật 0,55;
- rừng 0,00;
- LSTM 0,18;
- mô hình ghép 0,00.

Luật báo nhầm nhiều nhất, đúng vai trò đường cơ sở của nó.

## 3. Để hoàn tất đúng SPEC

Gõ phím và dùng chuột 2 phút như bình thường, demo chạy bên cạnh:

```
python scripts/demo.py --model rules --log results/phase5/misfires_typing.csv
python scripts/summarize_log.py results/phase5/misfires_typing.csv
```

Ghi số cụm và số cụm mỗi phút vào đây, rồi xoá dòng "NHÁP" ở đầu file.
