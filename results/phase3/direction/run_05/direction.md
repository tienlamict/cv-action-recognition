# Đo quy ước hướng trên IPN

- Số clip đã dùng: 189
- Số clip bị bỏ vì `length_mismatch`: 11 (xem docs/ipn_format.md mục 6)

| Lớp | Số đoạn | Bỏ qua | Trung vị dx | Cùng dấu | Trung vị open_delta | Cùng dấu |
|---|---|---|---|---|---|---|
| swipe_left | 162 | 27 | +0.4561 | 77.2% | +0.0097 | 50.6% |
| swipe_right | 159 | 30 | -0.5343 | 77.4% | -0.1344 | 60.4% |
| zoom_in | 156 | 33 | -0.0679 | 60.3% | +0.1969 | 76.3% |
| zoom_out | 163 | 26 | +0.0628 | 66.3% | -0.2969 | 77.3% |

## Kết luận

Hai điều kiện bắt buộc đều đạt.

```python
SWIPE_LEFT_SIGN = 1
```

Dấu này là dấu của trung vị `dx` ở lớp `swipe_left` (+0.4561), đo trên ảnh không lật của IPN.
