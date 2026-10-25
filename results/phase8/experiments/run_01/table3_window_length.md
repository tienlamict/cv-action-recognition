| model | win_sec | n_windows | macro_f1 | f1_swipes | f1_zooms | event_f1 | event_f1_swipes | event_f1_zooms | cmds_per_gesture | false_per_min | delta_event_f1 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rừng ngẫu nhiên | 0.8 | 11302 | 0.3674 | 0.1523 | 0.292 | 0.2022 | 0.1667 | 0.2937 | 0.8333 | 10.33 | -0.008559 | chênh lệch lớn hơn độ lệch chuẩn |
| rừng ngẫu nhiên | 1.2 | 11038 | 0.4361 | 0.2221 | 0.3927 | 0.2108 | 0.1601 | 0.333 | 0.9444 | 10.63 | 0 | (hàng cơ sở) |
| rừng ngẫu nhiên | 1.6 | 10815 | 0.4515 | 0.2328 | 0.4205 | 0.215 | 0.1646 | 0.3324 | 0.9722 | 9.666 | 0.004247 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM | 0.8 | 11302 | 0.4058 | 0.1841 | 0.3524 | 0.2437 | 0.1964 | 0.3513 | 1.12 | 9.832 | -0.09072 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM | 1.2 | 11038 | 0.556 | 0.3865 | 0.5195 | 0.3344 | 0.2871 | 0.4074 | 1.204 | 6.571 | 0 | (hàng cơ sở) |
| LSTM | 1.6 | 10815 | 0.5745 | 0.4058 | 0.5528 | 0.2672 | 0.208 | 0.3828 | 1.241 | 9.316 | -0.06725 | chênh lệch lớn hơn độ lệch chuẩn |

- Đổi độ dài cửa sổ thì đổi cả tập cửa sổ val (số cửa sổ, nhãn), nên macro-F1 mức cửa sổ của các hàng không cùng một tập; mức sự kiện chấm trên CÙNG các video val nên so được trực tiếp — kết luận dựa trên event_f1.
