# Đo quy ước hướng trên IPN

- Số clip đã dùng: 2
- Số clip bị bỏ vì `length_mismatch`: 5 (xem docs/ipn_format.md mục 6)

| Lớp | Số đoạn | Bỏ qua | Trung vị dx | Cùng dấu | Trung vị open_delta | Cùng dấu |
|---|---|---|---|---|---|---|
| swipe_left | 2 | 0 | +0.7275 | 100.0% | +0.8423 | 100.0% |
| swipe_right | 1 | 1 | +0.0000 | 0.0% | +0.0000 | 0.0% |
| zoom_in | 2 | 0 | -0.4124 | 100.0% | +0.2554 | 100.0% |
| zoom_out | 2 | 0 | -0.0185 | 50.0% | -0.3361 | 100.0% |

## Kết luận

Hai điều kiện bắt buộc đều đạt.

```python
SWIPE_LEFT_SIGN = 1
```

Dấu này là dấu của trung vị `dx` ở lớp `swipe_left` (+0.7275), đo trên ảnh không lật của IPN.
