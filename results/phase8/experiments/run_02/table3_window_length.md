| model | win_sec | n_windows | macro_f1 | f1_swipes | f1_zooms | event_f1 | event_f1_swipes | event_f1_zooms | cmds_per_gesture | false_per_min | delta_event_f1 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rừng ngẫu nhiên | 0.8 | 11302 | 0.3674 | 0.1523 | 0.292 | 0.26 | 0.2758 | 0.295 | 0.2407 | 1.098 | -0.1446 | chênh lệch lớn hơn độ lệch chuẩn |
| rừng ngẫu nhiên | 1.2 | 11038 | 0.4361 | 0.2221 | 0.3927 | 0.4046 | 0.3628 | 0.4485 | 0.3241 | 0.4991 | 0 | (hàng cơ sở) |
| rừng ngẫu nhiên | 1.6 | 10815 | 0.4515 | 0.2328 | 0.4205 | 0.2895 | 0.205 | 0.3477 | 0.2037 | 0.366 | -0.1152 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM | 0.8 | 11302 | 0.4058 | 0.1841 | 0.3524 | 0.4904 | 0.5036 | 0.4153 | 0.6574 | 1.481 | -0.0684 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM | 1.2 | 11038 | 0.556 | 0.3865 | 0.5195 | 0.5588 | 0.518 | 0.6357 | 0.7685 | 1.464 | 0 | (hàng cơ sở) |
| LSTM | 1.6 | 10815 | 0.5745 | 0.4058 | 0.5528 | 0.5915 | 0.5588 | 0.6423 | 0.8148 | 1.531 | 0.03273 | không đủ bằng chứng để kết luận |

- Đổi độ dài cửa sổ thì đổi cả tập cửa sổ val (số cửa sổ, nhãn), nên macro-F1 mức cửa sổ của các hàng không cùng một tập; mức sự kiện chấm trên CÙNG các video val nên so được trực tiếp — kết luận dựa trên event_f1.
