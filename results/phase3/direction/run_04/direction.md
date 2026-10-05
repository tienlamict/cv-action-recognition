# Đo quy ước hướng trên IPN

- Số clip đã dùng: 189
- Số clip bị bỏ vì `length_mismatch`: 11 (xem docs/ipn_format.md mục 6)

| Lớp | Số đoạn | Bỏ qua | Trung vị dx | Cùng dấu | Trung vị open_delta | Cùng dấu |
|---|---|---|---|---|---|---|
| swipe_left | 165 | 24 | +0.5092 | 77.6% | +0.0149 | 51.5% |
| swipe_right | 162 | 27 | -0.5360 | 77.8% | -0.1283 | 60.5% |
| zoom_in | 165 | 24 | -0.0673 | 60.6% | +0.2125 | 76.4% |
| zoom_out | 168 | 21 | +0.0619 | 65.5% | -0.2877 | 75.6% |

## Kết luận

Hai điều kiện bắt buộc đều đạt.

```python
SWIPE_LEFT_SIGN = 1
```

Dấu này là dấu của trung vị `dx` ở lớp `swipe_left` (+0.5092), đo trên ảnh không lật của IPN.
