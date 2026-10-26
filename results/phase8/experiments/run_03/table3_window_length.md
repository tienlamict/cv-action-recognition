| model | win_sec | n_windows | macro_f1 | f1_swipes | f1_zooms | event_f1 | event_f1_swipes | event_f1_zooms | cmds_per_gesture | false_per_min | delta_event_f1 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rừng ngẫu nhiên | 0.8 | 11302 | 0.3674 | 0.1523 | 0.292 | 0.01587 | 0.02222 | 0 | 0.009259 | 0.2828 | -0.2379 | chênh lệch lớn hơn độ lệch chuẩn |
| rừng ngẫu nhiên | 1.2 | 11038 | 0.4361 | 0.2221 | 0.3927 | 0.2537 | 0.1549 | 0.3306 | 0.1574 | 0.1497 | 0 | (hàng cơ sở) |
| rừng ngẫu nhiên | 1.6 | 10815 | 0.4515 | 0.2328 | 0.4205 | 0.1452 | 0 | 0.2645 | 0.08333 | 0.1165 | -0.1086 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM | 0.8 | 11302 | 0.4058 | 0.1841 | 0.3524 | 0.4894 | 0.5676 | 0.2885 | 0.4537 | 0.5656 | -0.1356 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM | 1.2 | 11038 | 0.556 | 0.3865 | 0.5195 | 0.625 | 0.6377 | 0.5885 | 0.6759 | 0.7653 | 0 | (hàng cơ sở) |
| LSTM | 1.6 | 10815 | 0.5745 | 0.4058 | 0.5528 | 0.6667 | 0.655 | 0.6865 | 0.7037 | 0.6987 | 0.04167 | không đủ bằng chứng để kết luận |

- Đổi độ dài cửa sổ thì đổi cả tập cửa sổ val (số cửa sổ, nhãn), nên macro-F1 mức cửa sổ của các hàng không cùng một tập; mức sự kiện chấm trên CÙNG các video val nên so được trực tiếp — kết luận dựa trên event_f1.
