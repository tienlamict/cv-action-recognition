| variant | n_features | macro_f1 | f1_none | f1_swipe_left | f1_swipe_right | f1_zoom_in | f1_zoom_out | none_alarm | alarm_B0A | alarm_B0B | event_f1 | false_per_min | lr_swaps | inout_swaps | none_to_swipe | largest_cell | delta_macro_f1 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| đủ 15 đặc trưng | 15 | 0.4361 | 0.9511 | 0.2121 | 0.2321 | 0.368 | 0.4174 | 0.08235 | 0.05758 | 0.09736 | 0.2537 | 0.1497 | 8 | 27 | 710 | 366 | 0 | (hàng cơ sở) |
| bỏ nhóm có dấu (open_delta, open_trend, pinch_delta, dx, mean_vx) | 10 | 0.4065 | 0.9425 | 0.1026 | 0.2 | 0.3925 | 0.3947 | 0.0984 | 0.07304 | 0.1235 | 0.06957 | 0.04991 | 53 | 29 | 914 | 638 | -0.02966 | chênh lệch lớn hơn độ lệch chuẩn |
| bỏ straightness | 14 | 0.4253 | 0.9489 | 0.2165 | 0.2185 | 0.3492 | 0.3932 | 0.0861 | 0.05729 | 0.1001 | 0.2734 | 0.1996 | 8 | 27 | 740 | 380 | -0.01089 | chênh lệch lớn hơn độ lệch chuẩn |
| bỏ presence | 14 | 0.4314 | 0.9503 | 0.2093 | 0.2171 | 0.3548 | 0.4255 | 0.08347 | 0.057 | 0.09766 | 0.2537 | 0.1497 | 8 | 27 | 719 | 373 | -0.00472 | chênh lệch lớn hơn độ lệch chuẩn |
| thêm 10 đặc trưng góc khớp | 25 | 0.4915 | 0.9685 | 0.2832 | 0.2751 | 0.4425 | 0.488 | 0.04761 | 0.01776 | 0.04778 | 0.2344 | 0.08318 | 2 | 28 | 393 | 190 | 0.05532 | chênh lệch lớn hơn độ lệch chuẩn |

- Vòng cải tiến: ô lớn nhất ngoài đường chéo của rừng cơ sở là none → swipe_left (366 cửa sổ); cột largest_cell là ô đó ở mỗi hàng.
