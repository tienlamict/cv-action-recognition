| model | conf_fire | k_of_n | zoom | n_commands | total_median | consensus_median | prediction_mean | window_est | processing_ms |
|---|---|---|---|---|---|---|---|---|---|
| rules | 0.6 | 2/5 | chung | 58 | 0.4333 | 0.2002 | 0.1 | 0.1331 | 16.14 |
| rules | 0.75 | 3/5 | chung | 36 | 0.5787 | 0.4004 | 0.1 | 0.07832 | 16.14 |
| rules | 0.85 | 4/5 | chung | 25 | 0.7508 | 0.6006 | 0.1 | 0.0502 | 16.14 |
| rules | 0.85 | 4/5 | 0.4·3/5 | 36 | 0.65 | 0.6 | 0.1 | -0.05 | 16.14 |
| rf | 0.6 | 2/5 | chung | 52 | 0.5167 | 0.2002 | 0.1 | 0.2165 | 15.4 |
| rf | 0.75 | 3/5 | chung | 35 | 0.7333 | 0.4004 | 0.1 | 0.2329 | 15.4 |
| rf | 0.85 | 4/5 | chung | 17 | 0.9594 | 0.6006 | 0.1 | 0.2588 | 15.4 |
| rf | 0.85 | 4/5 | 0.4·3/5 | 29 | 0.7537 | 0.4004 | 0.1 | 0.2533 | 15.4 |
| lstm | 0.6 | 2/5 | chung | 89 | 0.4329 | 0.2002 | 0.1 | 0.1327 |  |
| lstm | 0.75 | 3/5 | chung | 79 | 0.6169 | 0.4004 | 0.1 | 0.1165 |  |
| lstm | 0.85 | 4/5 | chung | 66 | 0.763 | 0.6006 | 0.1 | 0.06235 |  |
| lstm | 0.85 | 4/5 | 0.4·3/5 | 72 | 0.7435 | 0.4004 | 0.1 | 0.2431 |  |
| hybrid | 0.6 | 2/5 | chung | 74 | 0.5333 | 0.2002 | 0.1 | 0.2331 |  |
| hybrid | 0.75 | 3/5 | chung | 63 | 0.6333 | 0.4004 | 0.1 | 0.1329 |  |
| hybrid | 0.85 | 4/5 | chung | 50 | 0.8227 | 0.6006 | 0.1 | 0.1221 |  |
| hybrid | 0.85 | 4/5 | 0.4·3/5 | 62 | 0.7644 | 0.4004 | 0.1 | 0.264 |  |

- Ba cấu hình của FSM_TRADEOFF, một ngưỡng chung cho mọi lớp (zoom = chung), và cấu hình cuối: CONF_FIRE, K_OF_N cho vuốt, ngưỡng riêng ở cột zoom cho zoom. CONF_HOLD = min(0.55, ngưỡng mở), COOLDOWN_SEC 1.2, MIN_PRESENCE 0.7.
- Phiên webcam chạy lại qua đúng đường ống của demo; *_val là 27 video val của IPN.
- Nhầm/phút của từng kịch bản và false_per_min_live (cả ba kịch bản) GỘP theo thời lượng: tổng lệnh nhầm chia tổng số phút. Chỉ số *_live của phiên gestures cũng gộp: cộng dồn lời nhắc và lệnh của mọi phiên.
- Thời lượng và tỉ lệ lần dự đoán có tay (valid_share) theo kịch bản: reading 0.5 phút, 0%; typing 0.5 phút, 0%; talking 10.9 phút, 23%; gestures 4.8 phút, 67%. Kịch bản gần 0% tay thì nhầm/phút gần 0 vì camera không thấy tay, không phải vì mô hình tốt. false_per_hand_min_* chia cho số phút CÓ TAY (mô hình chỉ phát lệnh khi thấy tay); trống = chưa đo.
- Phiên gestures: cmds_per_gesture là lệnh đúng loại trong vùng khớp trên một cử chỉ; commands_per_prompt là MỌI lệnh chia số lời nhắc (định nghĩa của SPEC); duplicates_per_gesture = cmds_per_gesture − recall. Gần 1,0 mà recall thấp nghĩa là cử chỉ bị sót và cử chỉ bị phát trùng bù cho nhau.
- Độ trễ (giây, video val): từ khoảnh khắc chính của cử chỉ tới lúc phát lệnh, trung vị trên các lệnh đúng; processing_ms của lần bench.py speed gần nhất.
- window_est = total − consensus − prediction_mean (dự đoán: trung bình nửa nhịp).
