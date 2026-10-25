| model | conf_fire | k_of_n | source | n_commands | total_median | consensus_median | prediction_mean | window_est | processing_ms |
|---|---|---|---|---|---|---|---|---|---|
| rules | 0.6 | 2/5 | val | 58 | 0.4333 | 0.2002 | 0.1 | 0.1331 | 16.14 |
| rules | 0.6 | 2/5 | webcam | 15 | 0.6853 | 0.2072 | 0.1 | 0.3781 | 16.14 |
| rules | 0.75 | 3/5 | val | 36 | 0.5787 | 0.4004 | 0.1 | 0.07832 | 16.14 |
| rules | 0.75 | 3/5 | webcam | 8 | 0.6194 | 0.3999 | 0.1 | 0.1194 | 16.14 |
| rules | 0.85 | 4/5 | val | 25 | 0.7508 | 0.6006 | 0.1 | 0.0502 | 16.14 |
| rules | 0.85 | 4/5 | webcam | 8 | 0.88 | 0.6069 | 0.1 | 0.1731 | 16.14 |
| rf | 0.6 | 2/5 | val | 52 | 0.5167 | 0.2002 | 0.1 | 0.2165 | 15.4 |
| rf | 0.6 | 2/5 | webcam | 8 | 0.8443 | 0.1945 | 0.1 | 0.5498 | 15.4 |
| rf | 0.75 | 3/5 | val | 35 | 0.7333 | 0.4004 | 0.1 | 0.2329 | 15.4 |
| rf | 0.75 | 3/5 | webcam | 4 | 1.639 | 0.3997 | 0.1 | 1.14 | 15.4 |
| rf | 0.85 | 4/5 | val | 17 | 0.9594 | 0.6006 | 0.1 | 0.2588 | 15.4 |
| rf | 0.85 | 4/5 | webcam | 0 |  |  | 0.1 |  | 15.4 |
| lstm | 0.6 | 2/5 | val | 88 | 0.4299 | 0.2001 | 0.1 | 0.1298 |  |
| lstm | 0.6 | 2/5 | webcam | 9 | -0.8639 | 0.1932 | 0.1 | -1.157 |  |
| lstm | 0.75 | 3/5 | val | 76 | 0.5918 | 0.4 | 0.1 | 0.0918 |  |
| lstm | 0.75 | 3/5 | webcam | 7 | 0.5353 | 0.4003 | 0.1 | 0.03504 |  |
| lstm | 0.85 | 4/5 | val | 70 | 0.7667 | 0.6006 | 0.1 | 0.06607 |  |
| lstm | 0.85 | 4/5 | webcam | 8 | 0.8394 | 0.5924 | 0.1 | 0.1469 |  |
| hybrid | 0.6 | 2/5 | val | 70 | 0.4966 | 0.2 | 0.1 | 0.1966 |  |
| hybrid | 0.6 | 2/5 | webcam | 11 | -0.3894 | 0.1947 | 0.1 | -0.6841 |  |
| hybrid | 0.75 | 3/5 | val | 61 | 0.6333 | 0.4 | 0.1 | 0.1333 |  |
| hybrid | 0.75 | 3/5 | webcam | 8 | 0.5808 | 0.4003 | 0.1 | 0.08049 |  |
| hybrid | 0.85 | 4/5 | val | 51 | 0.8303 | 0.6 | 0.1 | 0.1303 |  |
| hybrid | 0.85 | 4/5 | webcam | 8 | 0.8394 | 0.5924 | 0.1 | 0.1469 |  |

- Ba cấu hình của FSM_TRADEOFF; CONF_HOLD = min(0.55, CONF_FIRE), COOLDOWN_SEC 1.2, MIN_PRESENCE 0.7.
- Phiên webcam chạy lại qua đúng đường ống của demo; *_val là 27 video val của IPN.
- Độ trễ (giây): từ khoảnh khắc chính của cử chỉ tới lúc phát lệnh, trung vị trên các lệnh đúng; processing_ms của lần bench.py speed gần nhất.
- window_est = total − consensus − prediction_mean (dự đoán: trung bình nửa nhịp).
