| model | conf_fire | k_of_n | event_f1_val | recall_val | false_per_min_val | false_per_min_reading | false_per_min_typing | false_per_min_talking | false_per_min_live | cmds_per_gesture_live | latency_val | latency_live | processing_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rules | 0.6 | 2/5 | 0.1239 | 0.537 | 12.81 |  |  |  |  |  | 0.4333 |  |  |
| rules | 0.75 | 3/5 | 0.13 | 0.3333 | 6.821 |  |  |  |  |  | 0.5787 |  |  |
| rules | 0.85 | 4/5 | 0.1276 | 0.2315 | 4.309 |  |  |  |  |  | 0.7508 |  |  |
| rf | 0.6 | 2/5 | 0.3537 | 0.4815 | 2.229 |  |  |  |  |  | 0.5167 |  |  |
| rf | 0.75 | 3/5 | 0.4046 | 0.3241 | 0.4991 |  |  |  |  |  | 0.7333 |  |  |
| rf | 0.85 | 4/5 | 0.2537 | 0.1574 | 0.1497 |  |  |  |  |  | 0.9594 |  |  |
| lstm | 0.6 | 2/5 | 0.4757 | 0.8148 | 2.895 |  |  |  |  |  | 0.4299 |  |  |
| lstm | 0.75 | 3/5 | 0.5588 | 0.7037 | 1.464 |  |  |  |  |  | 0.5918 |  |  |
| lstm | 0.85 | 4/5 | 0.625 | 0.6481 | 0.7653 |  |  |  |  |  | 0.7667 |  |  |
| hybrid | 0.6 | 2/5 | 0.4142 | 0.6481 | 2.662 |  |  |  |  |  | 0.4966 |  |  |
| hybrid | 0.75 | 3/5 | 0.49 | 0.5648 | 1.331 |  |  |  |  |  | 0.6333 |  |  |
| hybrid | 0.85 | 4/5 | 0.5285 | 0.4722 | 0.5656 |  |  |  |  |  | 0.8303 |  |  |

- Ba cấu hình của FSM_TRADEOFF; CONF_HOLD = min(0.55, CONF_FIRE), COOLDOWN_SEC 1.2, MIN_PRESENCE 0.7.
- Phiên webcam chạy lại qua đúng đường ống của demo; *_val là 27 video val của IPN.
- Độ trễ (giây): từ khoảnh khắc chính của cử chỉ tới lúc phát lệnh, trung vị trên các lệnh đúng; processing_ms của lần bench.py speed gần nhất.
