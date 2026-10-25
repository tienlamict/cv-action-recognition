| model | conf_fire | k_of_n | event_f1_val | recall_val | false_per_min_val | false_per_min_reading | false_per_min_typing | false_per_min_talking | false_per_min_live | recall_live | recall_swipes_live | recall_zooms_live | cmds_per_gesture_live | commands_per_prompt_live | duplicates_per_gesture_live | latency_val | processing_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rules | 0.6 | 2/5 | 0.1239 | 0.537 | 12.81 | 0 | 0 | 7.389 | 2.463 | 0.75 | 0.7 | 0.8 | 0.9 | 1.55 | 0.15 | 0.4333 | 16.14 |
| rules | 0.75 | 3/5 | 0.13 | 0.3333 | 6.821 | 0 | 0 | 4.222 | 1.407 | 0.4 | 0.3 | 0.5 | 0.4 | 0.7 | 0 | 0.5787 | 16.14 |
| rules | 0.85 | 4/5 | 0.1276 | 0.2315 | 4.309 | 0 | 0 | 2.111 | 0.7037 | 0.4 | 0.2 | 0.6 | 0.4 | 0.45 | 0 | 0.7508 | 16.14 |
| rf | 0.6 | 2/5 | 0.3537 | 0.4815 | 2.229 | 0 | 0 | 1.056 | 0.3519 | 0.4 | 0.4 | 0.4 | 0.5 | 1 | 0.1 | 0.5167 | 15.4 |
| rf | 0.75 | 3/5 | 0.4046 | 0.3241 | 0.4991 | 0 | 0 | 0 | 0 | 0.2 | 0.3 | 0.1 | 0.2 | 0.2 | 0 | 0.7333 | 15.4 |
| rf | 0.85 | 4/5 | 0.2537 | 0.1574 | 0.1497 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.9594 | 15.4 |
| lstm | 0.6 | 2/5 | 0.4757 | 0.8148 | 2.895 | 0 | 0 | 3.167 | 1.056 | 0.45 | 0.9 | 0 | 0.85 | 1.25 | 0.4 | 0.4299 |  |
| lstm | 0.75 | 3/5 | 0.5588 | 0.7037 | 1.464 | 0 | 0 | 0 | 0 | 0.35 | 0.7 | 0 | 0.5 | 0.85 | 0.15 | 0.5918 |  |
| lstm | 0.85 | 4/5 | 0.625 | 0.6481 | 0.7653 | 0 | 0 | 0 | 0 | 0.4 | 0.8 | 0 | 0.45 | 0.5 | 0.05 | 0.7667 |  |
| hybrid | 0.6 | 2/5 | 0.4142 | 0.6481 | 2.662 | 0 | 0 | 4.222 | 1.407 | 0.55 | 0.9 | 0.2 | 1 | 1.65 | 0.45 | 0.4966 |  |
| hybrid | 0.75 | 3/5 | 0.49 | 0.5648 | 1.331 | 0 | 0 | 0 | 0 | 0.4 | 0.7 | 0.1 | 0.55 | 0.9 | 0.15 | 0.6333 |  |
| hybrid | 0.85 | 4/5 | 0.5285 | 0.4722 | 0.5656 | 0 | 0 | 0 | 0 | 0.4 | 0.8 | 0 | 0.45 | 0.5 | 0.05 | 0.8303 |  |

- Ba cấu hình của FSM_TRADEOFF; CONF_HOLD = min(0.55, CONF_FIRE), COOLDOWN_SEC 1.2, MIN_PRESENCE 0.7.
- Phiên webcam chạy lại qua đúng đường ống của demo; *_val là 27 video val của IPN.
- Phiên gestures: cmds_per_gesture là lệnh đúng loại trong vùng khớp trên một cử chỉ; commands_per_prompt là MỌI lệnh chia số lời nhắc (định nghĩa của SPEC); duplicates_per_gesture = cmds_per_gesture − recall. Gần 1,0 mà recall thấp nghĩa là cử chỉ bị sót và cử chỉ bị phát trùng bù cho nhau.
- Độ trễ (giây, video val): từ khoảnh khắc chính của cử chỉ tới lúc phát lệnh, trung vị trên các lệnh đúng; processing_ms của lần bench.py speed gần nhất.
