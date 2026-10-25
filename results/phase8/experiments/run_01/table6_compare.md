| so_sánh | metric | mean_a | mean_b | delta | std | verdict |
|---|---|---|---|---|---|---|
| LSTM − rừng ngẫu nhiên | macro_f1 | 0.549 | 0.4329 | 0.1162 | 0.02713 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM − rừng ngẫu nhiên | event_f1 | 0.3125 | 0.2087 | 0.1038 | 0.0225 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − LSTM | macro_f1 | 0.4918 | 0.549 | -0.05722 | 0.02713 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − LSTM | event_f1 | 0.2864 | 0.3125 | -0.02609 | 0.0225 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − rừng ngẫu nhiên | macro_f1 | 0.4918 | 0.4329 | 0.05894 | 0.02235 | chênh lệch lớn hơn độ lệch chuẩn |
| ghép (vuốt LSTM, zoom rừng) − rừng ngẫu nhiên | event_f1 | 0.2864 | 0.2087 | 0.07768 | 0.01467 | chênh lệch lớn hơn độ lệch chuẩn |
