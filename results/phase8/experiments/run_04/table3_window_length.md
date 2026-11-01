| model | win_sec | n_windows | macro_f1 | f1_swipes | f1_zooms | event_f1 | event_f1_swipes | event_f1_zooms | cmds_per_gesture | false_per_min | delta_event_f1 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rừng ngẫu nhiên | 0.8 | 11302 | 0.3674 | 0.1523 | 0.292 | 0.2171 | 0 | 0.3654 | 0.1944 | 0.7986 | -0.0998 | chênh lệch lớn hơn độ lệch chuẩn |
| rừng ngẫu nhiên | 1.2 | 11038 | 0.4361 | 0.2221 | 0.3927 | 0.3169 | 0.1273 | 0.42 | 0.2963 | 0.7653 | 0 | (hàng cơ sở) |
| rừng ngẫu nhiên | 1.6 | 10815 | 0.4515 | 0.2328 | 0.4205 | 0.2874 | 0 | 0.4403 | 0.2222 | 0.5823 | -0.02951 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM | 0.8 | 11302 | 0.4058 | 0.1841 | 0.3524 | 0.5302 | 0.5676 | 0.4389 | 0.5648 | 0.8318 | -0.1111 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM | 1.2 | 11038 | 0.556 | 0.3865 | 0.5195 | 0.6414 | 0.6377 | 0.6367 | 0.7407 | 0.8817 | 0 | (hàng cơ sở) |
| LSTM | 1.6 | 10815 | 0.5745 | 0.4058 | 0.5528 | 0.6236 | 0.655 | 0.6077 | 0.7963 | 1.214 | -0.01778 | không đủ bằng chứng để kết luận |

- Đổi độ dài cửa sổ thì đổi cả tập cửa sổ val (số cửa sổ, nhãn), nên macro-F1 mức cửa sổ của các hàng không cùng một tập; mức sự kiện chấm trên CÙNG các video val nên so được trực tiếp — kết luận dựa trên event_f1.
