| model | conf_fire | k_of_n | zoom | arbitrate | n_commands | total_median | consensus_median | prediction_mean | window_est | processing_ms |
|---|---|---|---|---|---|---|---|---|---|---|
| hybrid | 0.6 | 2/5 | chung | 0.4 | 70 | 0.8501 | 0.6006 | 0.1 | 0.1495 |  |
| hybrid | 0.75 | 3/5 | chung | 0.4 | 60 | 1.073 | 0.8008 | 0.1 | 0.1725 |  |
| hybrid | 0.85 | 4/5 | chung | 0.4 | 48 | 1.229 | 1.001 | 0.1 | 0.1277 |  |
| hybrid | 0.85 | 4/5 | 0.4·3/5 | 0.4 | 63 | 1.16 | 0.8008 | 0.1 | 0.2588 |  |
| hybrid_s43 | 0.6 | 2/5 | chung | 0.4 | 69 | 0.9 | 0.6006 | 0.1 | 0.1994 |  |
| hybrid_s43 | 0.75 | 3/5 | chung | 0.4 | 59 | 1.087 | 0.8008 | 0.1 | 0.1866 |  |
| hybrid_s43 | 0.85 | 4/5 | chung | 0.4 | 43 | 1.228 | 1.001 | 0.1 | 0.1268 |  |
| hybrid_s43 | 0.85 | 4/5 | 0.4·3/5 | 0.4 | 59 | 1.154 | 0.8008 | 0.1 | 0.2533 |  |

- Ba cấu hình của FSM_TRADEOFF, một ngưỡng chung cho mọi lớp (zoom = chung), và cấu hình cuối: CONF_FIRE, K_OF_N cho vuốt, ngưỡng riêng ở cột zoom cho zoom. CONF_HOLD = min(0.55, ngưỡng mở), COOLDOWN_SEC 1.2, MIN_PRESENCE 0.7.
- Phiên webcam chạy lại qua đúng đường ống của demo; *_val là 27 video val của IPN.
- Nhầm/phút của từng kịch bản và false_per_min_live (cả ba kịch bản) GỘP theo thời lượng: tổng lệnh nhầm chia tổng số phút. Chỉ số *_live của phiên gestures cũng gộp: cộng dồn lời nhắc và lệnh của mọi phiên.
- Thời lượng và tỉ lệ lần dự đoán có tay (valid_share) theo kịch bản: reading 0.5 phút, 0%; typing 0.5 phút, 0%; talking 10.9 phút, 23%; gestures 4.8 phút, 67%. Kịch bản gần 0% tay thì nhầm/phút gần 0 vì camera không thấy tay, không phải vì mô hình tốt. false_per_hand_min_* chia cho số phút CÓ TAY (mô hình chỉ phát lệnh khi thấy tay); trống = chưa đo.
- Phiên gestures: cmds_per_gesture là lệnh đúng loại trong vùng khớp trên một cử chỉ; commands_per_prompt là MỌI lệnh chia số lời nhắc (định nghĩa của SPEC); duplicates_per_gesture = cmds_per_gesture − recall. Gần 1,0 mà recall thấp nghĩa là cử chỉ bị sót và cử chỉ bị phát trùng bù cho nhau.
- Độ trễ (giây, video val): từ khoảnh khắc chính của cử chỉ tới lúc phát lệnh, trung vị trên các lệnh đúng; processing_ms của lần bench.py speed gần nhất.
- wrong_per_prompt_live: lệnh nhầm (sai loại, ngược chiều, hay ngoài vùng khớp) trong các phiên gestures, chia số lời nhắc. hybrid_s<hạt>: mô hình ghép học thêm dữ liệu tự quay (Phase 11, train_self.py).
- arbitrate: giây chờ của trọng tài chiều ngược (FSM_ARBITRATE_SEC); 0 là phát ngay như Phase 10.
- window_est = total − consensus − prediction_mean (dự đoán: trung bình nửa nhịp).
