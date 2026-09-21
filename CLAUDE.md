# Quy ước dự án

- Không dùng git. Không chạy lệnh git nào trong project này.
- Một đường ống, ba nguồn: dữ liệu IPN, dữ liệu tự quay và webcam lúc chạy
  thật phải đi qua CÙNG các hàm trong src/. Không bao giờ có hai bản
  "gần giống nhau".
- config.py là nơi duy nhất chứa hằng số. Không số ma thuật ở file khác.
- Quy ước thì ĐO, không đoán. Không viết cứng dấu của dx ở bất kỳ đâu.
- Frame không thấy tay: ghi NaN, KHÔNG bỏ frame.
- Thứ tự đường ống cố định: to_pixels → resample(15Hz) → fill_short_gaps →
  cắt cửa sổ → [tăng cường] → normalize_window → đặc trưng hoặc LSTM.
- Cửa sổ tính bằng GIÂY, không bằng frame.
- Ảnh đưa vào mô hình KHÔNG lật; chỉ lật bản hiển thị cho người xem.
- Chỉ toạ độ 2D. Không z, không hand_world_landmarks.
- Chia tập theo NGƯỜI. Không bao giờ train_test_split ngẫu nhiên trên cửa sổ.
- Không LSTM hai chiều, không làm mượt hai phía (hệ thống thời gian thực).
- Không đường dẫn tuyệt đối, không phụ thuộc CUDA.

# Môi trường

- Mọi lệnh python/pytest/pip chạy trong conda env `action-recognition`
  (Python 3.10). Hook SessionStart ở .claude/settings.json tự kích hoạt env
  cho Bash. Trước khi chạy, kiểm tra `python --version` ra 3.10.x; nếu ra
  bản khác thì dừng và báo, không chạy bằng Python hệ thống.
