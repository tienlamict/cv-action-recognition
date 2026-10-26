| so_sánh | metric | mean_a | mean_b | delta | std | verdict |
|---|---|---|---|---|---|---|
| LSTM − rừng ngẫu nhiên | macro_f1 | 0.549 | 0.4329 | 0.1162 | 0.02713 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM − rừng ngẫu nhiên | event_f1 | 0.629 | 0.2348 | 0.3942 | 0.05114 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − LSTM | macro_f1 | 0.4918 | 0.549 | -0.05722 | 0.02713 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − LSTM | event_f1 | 0.5162 | 0.629 | -0.1128 | 0.056 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − rừng ngẫu nhiên | macro_f1 | 0.4918 | 0.4329 | 0.05894 | 0.02235 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − rừng ngẫu nhiên | event_f1 | 0.5162 | 0.2348 | 0.2814 | 0.056 | chênh lệch lớn hơn độ lệch chuẩn |
