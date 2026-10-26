| model | conf_fire | k_of_n | n_commands | total_median | consensus_median | prediction_mean | window_est | processing_ms |
|---|---|---|---|---|---|---|---|---|
| rules | 0.6 | 2/5 | 58 | 0.4333 | 0.2002 | 0.1 | 0.1331 | 16.14 |
| rules | 0.75 | 3/5 | 36 | 0.5787 | 0.4004 | 0.1 | 0.07832 | 16.14 |
| rules | 0.85 | 4/5 | 25 | 0.7508 | 0.6006 | 0.1 | 0.0502 | 16.14 |
| rf | 0.6 | 2/5 | 52 | 0.5167 | 0.2002 | 0.1 | 0.2165 | 15.4 |
| rf | 0.75 | 3/5 | 35 | 0.7333 | 0.4004 | 0.1 | 0.2329 | 15.4 |
| rf | 0.85 | 4/5 | 17 | 0.9594 | 0.6006 | 0.1 | 0.2588 | 15.4 |
| lstm | 0.6 | 2/5 | 89 | 0.4329 | 0.2002 | 0.1 | 0.1327 |  |
| lstm | 0.75 | 3/5 | 79 | 0.6169 | 0.4004 | 0.1 | 0.1165 |  |
| lstm | 0.85 | 4/5 | 66 | 0.763 | 0.6006 | 0.1 | 0.06235 |  |
| hybrid | 0.6 | 2/5 | 74 | 0.5333 | 0.2002 | 0.1 | 0.2331 |  |
| hybrid | 0.75 | 3/5 | 63 | 0.6333 | 0.4004 | 0.1 | 0.1329 |  |
| hybrid | 0.85 | 4/5 | 50 | 0.8227 | 0.6006 | 0.1 | 0.1221 |  |

- Ba cấu hình của FSM_TRADEOFF; CONF_HOLD = min(0.55, CONF_FIRE), COOLDOWN_SEC 1.2, MIN_PRESENCE 0.7.
- Phiên webcam chạy lại qua đúng đường ống của demo; *_val là 27 video val của IPN.
- Nhầm/phút của từng kịch bản và false_per_min_live (cả ba kịch bản) GỘP theo thời lượng: tổng lệnh nhầm chia tổng số phút. Chỉ số *_live của phiên gestures cũng gộp: cộng dồn lời nhắc và lệnh của mọi phiên.
- Thời lượng và tỉ lệ lần dự đoán có tay (valid_share) theo kịch bản: reading 0.5 phút, 0%; typing 0.5 phút, 0%; talking 10.9 phút, 23%; gestures 2.4 phút, 63%. Kịch bản gần 0% tay thì nhầm/phút gần 0 vì camera không thấy tay, không phải vì mô hình tốt.
- Phiên gestures: cmds_per_gesture là lệnh đúng loại trong vùng khớp trên một cử chỉ; commands_per_prompt là MỌI lệnh chia số lời nhắc (định nghĩa của SPEC); duplicates_per_gesture = cmds_per_gesture − recall. Gần 1,0 mà recall thấp nghĩa là cử chỉ bị sót và cử chỉ bị phát trùng bù cho nhau.
- Độ trễ (giây, video val): từ khoảnh khắc chính của cử chỉ tới lúc phát lệnh, trung vị trên các lệnh đúng; processing_ms của lần bench.py speed gần nhất.
- window_est = total − consensus − prediction_mean (dự đoán: trung bình nửa nhịp).
