| model | variant | macro_f1 | f1_none | f1_swipe_left | f1_swipe_right | f1_zoom_in | f1_zoom_out | event_f1 | lr_swaps | swipe_to_none | delta_macro_f1 | verdict | best_epoch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rừng ngẫu nhiên | gốc cổ tay frame đầu | 0.4361 | 0.9511 | 0.2121 | 0.2321 | 0.368 | 0.4174 | 0.2108 | 8 | 72 | 0 | (hàng cơ sở) |  |
| rừng ngẫu nhiên | gốc cổ tay từng frame | 0.348 | 0.9426 | 0.07721 | 0.08796 | 0.275 | 0.3571 | 0.1598 | 21 | 128 | -0.08815 | chênh lệch lớn hơn độ lệch chuẩn |  |
| LSTM | gốc cổ tay frame đầu | 0.556 | 0.9678 | 0.3974 | 0.3757 | 0.5056 | 0.5333 | 0.3344 | 3 | 30 | 0 | (hàng cơ sở) | 86 |
| LSTM | gốc cổ tay từng frame | 0.592 | 0.963 | 0.373 | 0.2709 | 0.6979 | 0.6553 | 0.304 | 5 | 25 | 0.03607 | chênh lệch lớn hơn độ lệch chuẩn | 147 |

- lr_swaps: số cửa sổ vuốt bị đoán ngược hướng; swipe_to_none: cửa sổ vuốt bị đoán none. Đơn vị giữ lòng bàn tay frame đầu ở cả hai hàng — chỉ gốc toạ độ đổi.
