| model | split | n_train | n_val | macro_f1 | f1_none | f1_swipe_left | f1_swipe_right | f1_zoom_in | f1_zoom_out | delta_macro_f1 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rừng ngẫu nhiên | theo người (split chính thức) | 3326 | 11038 | 0.4361 | 0.9511 | 0.2121 | 0.2321 | 0.368 | 0.4174 | 0 | (hàng cơ sở) |
| rừng ngẫu nhiên | ngẫu nhiên theo cửa sổ (rò rỉ) | 3326 | 11038 | 0.5401 | 0.9579 | 0.2714 | 0.3459 | 0.5739 | 0.5512 | 0.1039 | chênh lệch lớn hơn độ lệch chuẩn |
| LSTM | theo người (split chính thức) | 3326 | 11038 | 0.556 | 0.9678 | 0.3974 | 0.3757 | 0.5056 | 0.5333 | 0 | (hàng cơ sở) |
| LSTM | ngẫu nhiên theo cửa sổ (rò rỉ) | 3326 | 11038 | 0.701 | 0.9798 | 0.6222 | 0.4599 | 0.7256 | 0.7176 | 0.1451 | chênh lệch lớn hơn độ lệch chuẩn |

- Hàng thứ ba — tập tự quay, điều kiện thật — chỉ có nếu bật Phase 11 (chưa bật).
- Hàng rò rỉ chia NGẪU NHIÊN THEO CỬA SỔ kho cửa sổ của người train + val, phân tầng theo lớp với đúng số cửa sổ mỗi lớp của val theo người; train lấy mẫu con none như cấu hình chính. Không có mức sự kiện: tập đánh giá không phải một nhóm video.
