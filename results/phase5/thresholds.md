# Ngưỡng của mô hình luật

Hiệu chuẩn trên **tập train** của IPN (3326 cửa sổ, `data/windows/windows.npz`) bằng `scripts/calibrate_rules.py`. Không dùng val hay test.

| Ngưỡng | Giá trị | Lý do |
|---|---|---|
| `RULE_VX_HI` | 4.0256 | trung điểm của p90 max_vx lớp none (5.229) và p10 max_vx hai lớp vuốt (2.822) — ⚠ hai phân vị chồng nhau |
| `RULE_DX_HI` | 0.1025 | p10 của |dx| trên hai lớp vuốt |
| `RULE_P_HI` | 0.7209 | trung điểm của p90 |pinch_delta| lớp none cộng hai lớp vuốt (1.081) và p10 |pinch_delta| hai lớp zoom (0.361) — ⚠ hai phân vị chồng nhau |

## Phân vị theo lớp

| Đặc trưng | Lớp | n | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|---|
| max_vx | none | 1663 | 0.602 | 1.084 | 1.999 | 3.298 | 5.229 |
| max_vx | swipe_left | 419 | 2.659 | 3.592 | 5.018 | 6.647 | 8.505 |
| max_vx | swipe_right | 417 | 2.942 | 3.700 | 4.930 | 6.285 | 8.512 |
| max_vx | zoom_in | 409 | 0.549 | 0.818 | 1.204 | 1.841 | 3.079 |
| max_vx | zoom_out | 418 | 0.463 | 0.778 | 1.155 | 2.229 | 3.244 |
| |dx| | none | 1663 | 0.017 | 0.060 | 0.179 | 0.528 | 1.122 |
| |dx| | swipe_left | 419 | 0.082 | 0.327 | 0.868 | 1.362 | 1.981 |
| |dx| | swipe_right | 417 | 0.173 | 0.395 | 0.714 | 1.158 | 1.509 |
| |dx| | zoom_in | 409 | 0.020 | 0.065 | 0.156 | 0.301 | 0.487 |
| |dx| | zoom_out | 418 | 0.021 | 0.070 | 0.151 | 0.341 | 0.669 |
| |pinch_delta| | none | 1663 | 0.026 | 0.097 | 0.280 | 0.610 | 1.018 |
| |pinch_delta| | swipe_left | 419 | 0.041 | 0.135 | 0.330 | 0.632 | 0.966 |
| |pinch_delta| | swipe_right | 417 | 0.068 | 0.233 | 0.579 | 0.943 | 1.286 |
| |pinch_delta| | zoom_in | 409 | 0.292 | 0.873 | 1.458 | 1.818 | 2.220 |
| |pinch_delta| | zoom_out | 418 | 0.472 | 0.867 | 1.314 | 1.589 | 1.918 |

## Cảnh báo

- `RULE_VX_HI`: phân vị 90 của nhóm dưới (5.229) lớn hơn phân vị 10 của nhóm trên (2.822). Một ngưỡng không tách sạch hai nhóm; sai ở cả hai phía là không tránh được với luật.
- `RULE_P_HI`: phân vị 90 của nhóm dưới (1.081) lớn hơn phân vị 10 của nhóm trên (0.361). Một ngưỡng không tách sạch hai nhóm; sai ở cả hai phía là không tránh được với luật.
