| model | conf_fire | k_of_n | zoom | arbitrate | event_f1_val | recall_val | false_per_min_val | false_per_min_reading | false_per_min_typing | false_per_min_talking | false_per_min_live | false_per_hand_min_reading | false_per_hand_min_typing | false_per_hand_min_talking | false_per_hand_min_live | recall_live | recall_swipes_live | recall_zooms_live | cmds_per_gesture_live | commands_per_prompt_live | duplicates_per_gesture_live | wrong_per_prompt_live | latency_val | processing_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hybrid | 0.6 | 2/5 | chung | 0.4 | 0.4667 | 0.6481 | 2.03 | 0 | 0 | 0.5481 | 0.5008 |  |  | 2.372 | 2.372 | 0.6 | 0.65 | 0.55 | 0.725 | 1.425 | 0.125 | 0.825 | 0.8501 |  |
| hybrid | 0.75 | 3/5 | chung | 0.4 | 0.5634 | 0.5556 | 0.7486 | 0 | 0 | 0.1827 | 0.1669 |  |  | 0.7906 | 0.7906 | 0.425 | 0.75 | 0.1 | 0.45 | 0.65 | 0.025 | 0.225 | 1.073 |  |
| hybrid | 0.85 | 4/5 | chung | 0.4 | 0.5486 | 0.4444 | 0.3161 | 0 | 0 | 0 | 0 |  |  | 0 | 0 | 0.25 | 0.5 | 0 | 0.25 | 0.475 | 0 | 0.225 | 1.229 |  |
| hybrid | 0.85 | 4/5 | 0.4·3/5 | 0.4 | 0.5753 | 0.5833 | 0.7986 | 0 | 0 | 0.1827 | 0.1669 |  |  | 0.7906 | 0.7906 | 0.5 | 0.5 | 0.5 | 0.5 | 0.975 | 0 | 0.475 | 1.16 |  |
| hybrid_s43 | 0.6 | 2/5 | chung | 0.4 | 0.4742 | 0.6389 | 1.897 | 0 | 0 | 0.4567 | 0.4174 |  |  | 1.977 | 1.977 | 0.75 | 0.75 | 0.75 | 0.9 | 1.725 | 0.15 | 0.975 | 0.9 |  |
| hybrid_s43 | 0.75 | 3/5 | chung | 0.4 | 0.5646 | 0.5463 | 0.6987 | 0 | 0 | 0.1827 | 0.1669 |  |  | 0.7906 | 0.7906 | 0.475 | 0.6 | 0.35 | 0.525 | 0.875 | 0.05 | 0.4 | 1.087 |  |
| hybrid_s43 | 0.85 | 4/5 | chung | 0.4 | 0.5059 | 0.3981 | 0.3161 | 0 | 0 | 0 | 0 |  |  | 0 | 0 | 0.275 | 0.35 | 0.2 | 0.275 | 0.5 | 0 | 0.225 | 1.228 |  |
| hybrid_s43 | 0.85 | 4/5 | 0.4·3/5 | 0.4 | 0.554 | 0.5463 | 0.7653 | 0 | 0 | 0.1827 | 0.1669 |  |  | 0.7906 | 0.7906 | 0.425 | 0.35 | 0.5 | 0.425 | 0.925 | 0 | 0.5 | 1.154 |  |

- Ba cấu hình của FSM_TRADEOFF, một ngưỡng chung cho mọi lớp (zoom = chung), và cấu hình cuối: CONF_FIRE, K_OF_N cho vuốt, ngưỡng riêng ở cột zoom cho zoom. CONF_HOLD = min(0.55, ngưỡng mở), COOLDOWN_SEC 1.2, MIN_PRESENCE 0.7.
- Phiên webcam chạy lại qua đúng đường ống của demo; *_val là 27 video val của IPN.
- Nhầm/phút của từng kịch bản và false_per_min_live (cả ba kịch bản) GỘP theo thời lượng: tổng lệnh nhầm chia tổng số phút. Chỉ số *_live của phiên gestures cũng gộp: cộng dồn lời nhắc và lệnh của mọi phiên.
- Thời lượng và tỉ lệ lần dự đoán có tay (valid_share) theo kịch bản: reading 0.5 phút, 0%; typing 0.5 phút, 0%; talking 10.9 phút, 23%; gestures 4.8 phút, 67%. Kịch bản gần 0% tay thì nhầm/phút gần 0 vì camera không thấy tay, không phải vì mô hình tốt. false_per_hand_min_* chia cho số phút CÓ TAY (mô hình chỉ phát lệnh khi thấy tay); trống = chưa đo.
- Phiên gestures: cmds_per_gesture là lệnh đúng loại trong vùng khớp trên một cử chỉ; commands_per_prompt là MỌI lệnh chia số lời nhắc (định nghĩa của SPEC); duplicates_per_gesture = cmds_per_gesture − recall. Gần 1,0 mà recall thấp nghĩa là cử chỉ bị sót và cử chỉ bị phát trùng bù cho nhau.
- Độ trễ (giây, video val): từ khoảnh khắc chính của cử chỉ tới lúc phát lệnh, trung vị trên các lệnh đúng; processing_ms của lần bench.py speed gần nhất.
- wrong_per_prompt_live: lệnh nhầm (sai loại, ngược chiều, hay ngoài vùng khớp) trong các phiên gestures, chia số lời nhắc. hybrid_s<hạt>: mô hình ghép học thêm dữ liệu tự quay (Phase 11, train_self.py).
- arbitrate: giây chờ của trọng tài chiều ngược (FSM_ARBITRATE_SEC); 0 là phát ngay như Phase 10.
