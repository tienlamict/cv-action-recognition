| model | conf_fire | k_of_n | n_commands | total_median | consensus_median | prediction_mean | window_est | processing_ms |
|---|---|---|---|---|---|---|---|---|
| rules | 0.6 | 2/5 | 58 | 0.4333 | 0.2002 | 0.1 | 0.1331 | 16.14 |
| rules | 0.75 | 3/5 | 36 | 0.5787 | 0.4004 | 0.1 | 0.07832 | 16.14 |
| rules | 0.85 | 4/5 | 25 | 0.7508 | 0.6006 | 0.1 | 0.0502 | 16.14 |
| rf | 0.6 | 2/5 | 52 | 0.5167 | 0.2002 | 0.1 | 0.2165 | 15.4 |
| rf | 0.75 | 3/5 | 35 | 0.7333 | 0.4004 | 0.1 | 0.2329 | 15.4 |
| rf | 0.85 | 4/5 | 17 | 0.9594 | 0.6006 | 0.1 | 0.2588 | 15.4 |
| lstm | 0.6 | 2/5 | 88 | 0.4299 | 0.2001 | 0.1 | 0.1298 |  |
| lstm | 0.75 | 3/5 | 76 | 0.5918 | 0.4 | 0.1 | 0.0918 |  |
| lstm | 0.85 | 4/5 | 70 | 0.7667 | 0.6006 | 0.1 | 0.06607 |  |
| hybrid | 0.6 | 2/5 | 70 | 0.4966 | 0.2 | 0.1 | 0.1966 |  |
| hybrid | 0.75 | 3/5 | 61 | 0.6333 | 0.4 | 0.1 | 0.1333 |  |
| hybrid | 0.85 | 4/5 | 51 | 0.8303 | 0.6 | 0.1 | 0.1303 |  |

- Ba cấu hình của FSM_TRADEOFF; CONF_HOLD = min(0.55, CONF_FIRE), COOLDOWN_SEC 1.2, MIN_PRESENCE 0.7.
- Phiên webcam chạy lại qua đúng đường ống của demo; *_val là 27 video val của IPN.
- Phiên gestures: cmds_per_gesture là lệnh đúng loại trong vùng khớp trên một cử chỉ; commands_per_prompt là MỌI lệnh chia số lời nhắc (định nghĩa của SPEC); duplicates_per_gesture = cmds_per_gesture − recall. Gần 1,0 mà recall thấp nghĩa là cử chỉ bị sót và cử chỉ bị phát trùng bù cho nhau.
- Độ trễ (giây, video val): từ khoảnh khắc chính của cử chỉ tới lúc phát lệnh, trung vị trên các lệnh đúng; processing_ms của lần bench.py speed gần nhất.
- window_est = total − consensus − prediction_mean (dự đoán: trung bình nửa nhịp).
