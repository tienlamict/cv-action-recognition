# Đo quy ước hướng trên IPN

- Số clip đã dùng: 7
- Số clip bị bỏ vì `length_mismatch`: 5 (xem docs/ipn_format.md mục 6)

| Lớp | Số đoạn | Bỏ qua | Trung vị dx | Cùng dấu | Trung vị open_delta | Cùng dấu |
|---|---|---|---|---|---|---|
| swipe_left | 7 | 0 | +0.3116 | 71.4% | +0.7721 | 71.4% |
| swipe_right | 5 | 2 | -0.7633 | 60.0% | -0.1674 | 60.0% |
| zoom_in | 7 | 0 | -0.3868 | 85.7% | +0.4990 | 100.0% |
| zoom_out | 4 | 3 | -0.2165 | 75.0% | -0.2452 | 100.0% |

## Kết luận

Hai điều kiện bắt buộc đều đạt.

```python
SWIPE_LEFT_SIGN = 1
```

Dấu này là dấu của trung vị `dx` ở lớp `swipe_left` (+0.3116), đo trên ảnh không lật của IPN.
