| model | conf_fire | k_of_n | event_f1_val | recall_val | false_per_min_val | false_per_min_reading | false_per_min_typing | false_per_min_talking | false_per_min_live | recall_live | recall_swipes_live | recall_zooms_live | cmds_per_gesture_live | commands_per_prompt_live | duplicates_per_gesture_live | latency_val | processing_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rules | 0.6 | 2/5 | 0.1239 | 0.537 | 12.81 | 0 | 0 | 1.827 | 1.669 | 0.75 | 0.7 | 0.8 | 0.9 | 1.55 | 0.15 | 0.4333 | 16.14 |
| rules | 0.75 | 3/5 | 0.13 | 0.3333 | 6.821 | 0 | 0 | 0.9135 | 0.8347 | 0.4 | 0.3 | 0.5 | 0.4 | 0.7 | 0 | 0.5787 | 16.14 |
| rules | 0.85 | 4/5 | 0.1276 | 0.2315 | 4.309 | 0 | 0 | 0.5481 | 0.5008 | 0.4 | 0.2 | 0.6 | 0.4 | 0.45 | 0 | 0.7508 | 16.14 |
| rf | 0.6 | 2/5 | 0.3537 | 0.4815 | 2.229 | 0 | 0 | 0.5481 | 0.5008 | 0.4 | 0.4 | 0.4 | 0.5 | 1 | 0.1 | 0.5167 | 15.4 |
| rf | 0.75 | 3/5 | 0.4046 | 0.3241 | 0.4991 | 0 | 0 | 0 | 0 | 0.2 | 0.3 | 0.1 | 0.2 | 0.2 | 0 | 0.7333 | 15.4 |
| rf | 0.85 | 4/5 | 0.2537 | 0.1574 | 0.1497 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.9594 | 15.4 |
| lstm | 0.6 | 2/5 | 0.3895 | 0.8241 | 4.326 | 0 | 0 | 1.37 | 1.252 | 0.8 | 0.8 | 0.8 | 1.15 | 1.8 | 0.35 | 0.4329 |  |
| lstm | 0.75 | 3/5 | 0.5544 | 0.7315 | 1.63 | 0 | 0 | 0.6394 | 0.5843 | 0.5 | 0.6 | 0.4 | 0.6 | 1 | 0.1 | 0.6169 |  |
| lstm | 0.85 | 4/5 | 0.6 | 0.6111 | 0.7653 | 0 | 0 | 0.1827 | 0.1669 | 0.4 | 0.5 | 0.3 | 0.45 | 0.55 | 0.05 | 0.763 |  |
| hybrid | 0.6 | 2/5 | 0.4654 | 0.6852 | 2.263 | 0 | 0 | 0.5481 | 0.5008 | 0.6 | 0.8 | 0.4 | 0.95 | 1.65 | 0.35 | 0.5333 |  |
| hybrid | 0.75 | 3/5 | 0.586 | 0.5833 | 0.732 | 0 | 0 | 0.1827 | 0.1669 | 0.35 | 0.6 | 0.1 | 0.45 | 0.7 | 0.1 | 0.6333 |  |
| hybrid | 0.85 | 4/5 | 0.5714 | 0.463 | 0.2828 | 0 | 0 | 0 | 0 | 0.25 | 0.5 | 0 | 0.3 | 0.4 | 0.05 | 0.8227 |  |

- Ba cấu hình của FSM_TRADEOFF; CONF_HOLD = min(0.55, CONF_FIRE), COOLDOWN_SEC 1.2, MIN_PRESENCE 0.7.
- Phiên webcam chạy lại qua đúng đường ống của demo; *_val là 27 video val của IPN.
- Nhầm/phút của từng kịch bản và false_per_min_live (cả ba kịch bản) GỘP theo thời lượng: tổng lệnh nhầm chia tổng số phút. Chỉ số *_live của phiên gestures cũng gộp: cộng dồn lời nhắc và lệnh của mọi phiên.
- Thời lượng và tỉ lệ lần dự đoán có tay (valid_share) theo kịch bản: reading 0.5 phút, 0%; typing 0.5 phút, 0%; talking 10.9 phút, 23%; gestures 2.4 phút, 63%. Kịch bản gần 0% tay thì nhầm/phút gần 0 vì camera không thấy tay, không phải vì mô hình tốt.
- Phiên gestures: cmds_per_gesture là lệnh đúng loại trong vùng khớp trên một cử chỉ; commands_per_prompt là MỌI lệnh chia số lời nhắc (định nghĩa của SPEC); duplicates_per_gesture = cmds_per_gesture − recall. Gần 1,0 mà recall thấp nghĩa là cử chỉ bị sót và cử chỉ bị phát trùng bù cho nhau.
- Độ trễ (giây, video val): từ khoảnh khắc chính của cử chỉ tới lúc phát lệnh, trung vị trên các lệnh đúng; processing_ms của lần bench.py speed gần nhất.
