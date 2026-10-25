| so_sánh | metric | mean_a | mean_b | delta | std | verdict |
|---|---|---|---|---|---|---|
| LSTM − rừng ngẫu nhiên | macro_f1 | 0.549 | 0.4329 | 0.1162 | 0.02713 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM − rừng ngẫu nhiên | event_f1 | 0.5865 | 0.4134 | 0.1731 | 0.05771 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − LSTM | macro_f1 | 0.4918 | 0.549 | -0.05722 | 0.02713 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − LSTM | event_f1 | 0.5209 | 0.5865 | -0.06564 | 0.06769 | không đủ bằng chứng để kết luận |
| ghép (vuốt LSTM, zoom rừng) − rừng ngẫu nhiên | macro_f1 | 0.4918 | 0.4329 | 0.05894 | 0.02235 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − rừng ngẫu nhiên | event_f1 | 0.5209 | 0.4134 | 0.1075 | 0.06769 | chênh lệch lớn hơn độ lệch chuẩn |
