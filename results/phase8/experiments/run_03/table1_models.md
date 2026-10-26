| model | macro_f1 | f1_none | f1_swipe_left | f1_swipe_right | f1_zoom_in | f1_zoom_out | none_alarm | event_f1 | event_precision | event_recall | cmds_per_gesture | false_per_min | event_f1_end | raw_cmds_per_gesture | raw_false_per_min | inference_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| luật | 0.2305 | 0.7135 | 0.05621 | 0.04308 | 0.164 | 0.1758 | 0.4403 | 0.1276 | 0.08803 | 0.2315 | 0.2315 | 4.309 | 0.07653 | 3.241 | 90.52 | 0.00695 |
| rừng ngẫu nhiên | 0.4361 | 0.9511 | 0.2121 | 0.2321 | 0.368 | 0.4174 | 0.08235 | 0.2537 | 0.6538 | 0.1574 | 0.1574 | 0.1497 | 0.1493 | 2.935 | 22.36 | 2.965 |
| LSTM | 0.4893 | 0.9458 | 0.5733 | 0.3476 | 0.3988 | 0.1808 | 0.09962 | 0.6 | 0.5893 | 0.6111 | 0.6296 | 0.7653 | 0.3273 | 5.278 | 28.93 | 1.038 |
| ghép (vuốt LSTM, zoom rừng) | 0.5366 | 0.9698 | 0.5733 | 0.3476 | 0.371 | 0.4211 | 0.05146 | 0.5714 | 0.7463 | 0.463 | 0.4722 | 0.2828 | 0.3314 | 4.287 | 18.45 | 14.6 |

- Mức sự kiện: bộ lọc 'fsm', vùng khớp 'span'; event_f1_end theo vùng khớp ban đầu của SPEC (±1 s quanh lúc kết thúc); raw_* là khi không có tầng kích hoạt nào.
- Máy trạng thái: CONF_FIRE 0.85, K_OF_N 4/5, CONF_HOLD 0.55, COOLDOWN_SEC 1.2 — áp cho cột mức sự kiện của mọi bảng.
- Bảng này chấm mô hình ĐÃ LƯU của demo; LSTM và mô hình ghép dùng results/phase7/train_lstm/run_08/lstm_model.pt. Bảng 2–7 học lại theo công thức chính của config, không dùng file đó.
- inference_ms: trung vị một lần gọi mô hình của demo trên một cửa sổ (Intel64 Family 6 Model 140 Stepping 1, GenuineIntel, 8 luồng logic).
