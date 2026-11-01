| so_sánh | metric | mean_a | mean_b | delta | std | verdict |
|---|---|---|---|---|---|---|
| LSTM − rừng ngẫu nhiên | macro_f1 | 0.549 | 0.4329 | 0.1162 | 0.02713 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM − rừng ngẫu nhiên | event_f1 | 0.6273 | 0.3046 | 0.3227 | 0.05829 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − LSTM | macro_f1 | 0.4918 | 0.549 | -0.05722 | 0.02713 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − LSTM | event_f1 | 0.5219 | 0.6273 | -0.1053 | 0.05829 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − rừng ngẫu nhiên | macro_f1 | 0.4918 | 0.4329 | 0.05894 | 0.02235 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − rừng ngẫu nhiên | event_f1 | 0.5219 | 0.3046 | 0.2174 | 0.04296 | chênh lệch lớn hơn độ lệch chuẩn |
