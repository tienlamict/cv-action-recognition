| model | macro_f1 | f1_none | f1_swipe_left | f1_swipe_right | f1_zoom_in | f1_zoom_out | none_alarm | event_f1 | event_precision | event_recall | cmds_per_gesture | false_per_min | event_f1_end | raw_cmds_per_gesture | raw_false_per_min | inference_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| luật | 0.2305 | 0.7135 | 0.05621 | 0.04308 | 0.164 | 0.1758 | 0.4403 | 0.13 | 0.08072 | 0.3333 | 0.3704 | 6.821 | 0.06137 | 3.241 | 90.52 | 0.00695 |
| rừng ngẫu nhiên | 0.4361 | 0.9511 | 0.2121 | 0.2321 | 0.368 | 0.4174 | 0.08235 | 0.4046 | 0.5385 | 0.3241 | 0.3241 | 0.4991 | 0.2081 | 2.935 | 22.36 | 2.965 |
| LSTM | 0.556 | 0.9678 | 0.3974 | 0.3757 | 0.5056 | 0.5333 | 0.05784 | 0.5588 | 0.4634 | 0.7037 | 0.7685 | 1.464 | 0.3235 | 5.472 | 21.03 | 1.494 |
| ghép (vuốt LSTM, zoom rừng) | 0.5061 | 0.9646 | 0.3974 | 0.3757 | 0.368 | 0.4248 | 0.06009 | 0.49 | 0.4326 | 0.5648 | 0.6111 | 1.331 | 0.2651 | 4.352 | 19.98 | 6.436 |

- Mức sự kiện: bộ lọc 'fsm', vùng khớp 'span'; event_f1_end theo vùng khớp ban đầu của SPEC (±1 s quanh lúc kết thúc); raw_* là khi không có tầng kích hoạt nào.
- inference_ms: trung vị một lần gọi mô hình của demo trên một cửa sổ (Intel64 Family 6 Model 140 Stepping 1, GenuineIntel, 8 luồng logic).
