# Nhận dạng cử chỉ bàn tay thời gian thực để điều khiển máy tính

Nhận dạng bốn cử chỉ bàn tay từ webcam bằng MediaPipe Hand Landmarker
(21 điểm mốc, một bàn tay), rồi phát phím tắt điều khiển máy tính không chạm.

Năm lớp, thứ tự cố định — `none` luôn là chỉ số 0:

| Chỉ số | Lớp | Lệnh phát ra |
|---|---|---|
| 0 | `none` | không phát gì |
| 1 | `swipe_left` | slide trước |
| 2 | `swipe_right` | slide sau |
| 3 | `zoom_in` | phóng to |
| 4 | `zoom_out` | thu nhỏ |

Môi trường: Windows, Python 3.10, **CPU**. Không GPU, không CUDA, không WSL2.

Quy ước bắt buộc của project nằm ở [CLAUDE.md](CLAUDE.md). Spec đầy đủ 12 phase
nằm ở [docs/SPEC.md](docs/SPEC.md). Lý thuyết nền nằm ở [docs/](docs/README.md).

---

## Cài môi trường

```bat
conda create -n action-recognition python=3.10 -y
conda activate action-recognition
pip install -r requirements.txt
```

Khi làm việc qua Claude Code, env này được kích hoạt tự động lúc mở phiên nhờ
hook `SessionStart` trong [.claude/settings.json](.claude/settings.json)
(script: [.claude/hooks/conda-env.sh](.claude/hooks/conda-env.sh)). Miniconda
cài ở chỗ khác `%USERPROFILE%\miniconda3` thì đặt biến môi trường `CONDA_ROOT`.

Kiểm tra môi trường đã đủ:

```bat
python -c "import mediapipe, cv2, torch, sklearn; print('OK')"
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

Lệnh thứ hai phải in ra `True`. Nếu in `False`: webcam đang bị ứng dụng khác
chiếm, hoặc Windows đang chặn quyền camera (Settings → Privacy → Camera).

Chạy kiểm thử:

```bat
pytest -q
```

---

## Tải mô hình và dữ liệu

### `hand_landmarker.task`

Tải file mô hình MediaPipe và đặt vào `models/hand_landmarker.task`:

```bat
curl -L -o models/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

Đường dẫn tới file này đọc từ `config.HAND_LANDMARKER_TASK`, không viết lại
ở đâu khác.

### IPN Hand

Bộ dữ liệu huấn luyện chính, nạp ở Phase 4. Đăng ký và tải tại trang chính
thức của IPN Hand, rồi giải nén vào `data/ipn/` sao cho có cả video lẫn file
nhãn gốc. Dữ liệu tự quay đặt ở `data/raw/` theo quy ước tên
`p03_swipe_left_07.mp4` — tên file phải suy ra được cả mã người lẫn nhãn.

---

## Cấu trúc thư mục

```
cv-action-recognition/
├─ CLAUDE.md              quy ước bất di bất dịch của project
├─ README.md              file này
├─ requirements.txt       phụ thuộc (ghim phiên bản ở Phase 11)
├─ pytest.ini
├─ src/                   thư viện dùng chung — MỘT đường ống cho cả ba nguồn
│  └─ config.py           nơi DUY NHẤT chứa hằng số
├─ scripts/               script chạy được, mỗi script dùng argparse
├─ tests/
├─ notebooks/
├─ models/                hand_landmarker.task
├─ results/               bảng .csv/.md và hình .png của từng phase
└─ data/
   ├─ ipn/                IPN Hand: video và nhãn gốc
   ├─ raw/                video tự quay
   ├─ landmarks/          điểm mốc đã trích, .npz theo nguồn
   └─ windows/            windows.npz — bộ cửa sổ đã chuẩn hóa
```

---

## Bảng hằng số đã đo

Hai hằng số quy ước hướng phải **đo**, không đoán. Chừng nào còn `None`, mọi
chỗ dùng chúng sẽ dừng ngay nhờ `config.require_measured()`.

| Hằng số | Giá trị | Đo ở phase | Đo bằng cách nào |
|---|---|---|---|
| `SWIPE_LEFT_SIGN` | *(chưa đo)* | 3 | `scripts/measure_direction.py` trên dữ liệu IPN |
| `IPN_FLIP_X` | `1` | — | IPN là chuẩn quy ước hướng; chỉ đổi thành `-1` khi phép thử webcam ở Phase 5 chứng minh ngược |
| `AUG_NOISE_SIGMA` | *(chưa đo)* | 1B hoặc 4 | `analyze_observations.py`, hoặc ước lượng trên IPN |
| `RULE_S_HI`, `RULE_DX_HI`, `RULE_O_HI` | *(chưa hiệu chuẩn)* | 5 | `scripts/calibrate_rules.py` trên tập `train` của IPN |

Điền giá trị **và** một câu mô tả cách đo vào bảng này ngay khi đo xong.

---

## Thứ tự chạy script

Mỗi dòng là một lệnh chạy lại được để tái tạo con số trong báo cáo. Mọi
script nhận `--help`. Kết quả ghi vào `results/<phase>/<tên>/run_NN/` kèm
`manifest.json` (dòng lệnh, thời điểm, seed, phiên bản thư viện, hằng số).

| Phase | Lệnh | Sinh ra gì |
|---|---|---|
| 1 | `python scripts/live_landmarks.py` | Xem điểm mốc + FPS trên webcam (không ghi gì) |
| 1 | `python scripts/observe.py --exp <tên> [--condition <đk>]` | `results/phase1/<tên>[_<đk>]/run_NN/landmarks.csv`. `--list` để xem 9 thí nghiệm; mỗi thí nghiệm ≥ 3 lần |
| 1 | `python scripts/analyze_observations.py` | `results/phase1/analysis/run_NN/`: bảng `runs` và `summary` (.csv + .md), và dòng `AUG_NOISE_SIGMA` để dán vào `config.py` |
| 1 | `python scripts/record_csv.py --name <tên>` | CSV điểm mốc mỗi frame một dòng, dùng tự do |
| 4 | | |
| 5 | | |
| 6 | `python scripts/train_rf.py` | Rừng ngẫu nhiên học trên train, đánh giá trên val: `results/phase6/train_rf/run_NN/` (ma trận nhầm lẫn, độ quan trọng, mức sự kiện, báo nhầm theo nhãn gốc); lưu `results/phase6/rf_model.joblib`; cập nhật `results/model_comparison` |
| 6 | `python scripts/sweep_rigid.py` | Quét tăng cường "bàn tay cứng" trên val: `results/phase6/sweep_rigid/run_NN/` (bảng `sweep`: lợi và giá của từng mức; bảng `shape_spread`: độ đổi dáng của tay thật so với bản tổng hợp) |
| 6 | `python scripts/probe_swipes.py` | Mô hình đang lưu coi gì là vuốt: `results/phase6/probe_swipes/run_NN/probe` |
| 6 | `python scripts/evaluate.py --model rf --split val` | Đánh giá mô hình đã lưu; `--split test` bắt buộc `--final` và ghi `results/TEST_USED.log` (luật 13) |
| 6 | `python scripts/demo.py --model rf --show-features --log <file.csv>` | Demo webcam; `--show-features` là chế độ luyện tập (bốn đặc trưng so với hộp IPN) |
| 6 | `python scripts/summarize_log.py <file.csv>` | Số cụm nhãn khác `none` và số cụm mỗi phút của một log demo |
| 7 | | |
| 8 | | |
| 10 | | |

---

## Tái lập

- Seed cố định: `config.SEED = 42`, đặt cho `random`, `numpy` và `torch`.
- Camera dùng suốt dự án: 640×480 @ 30 FPS (`CAM_W`, `CAM_H`, `CAM_FPS`).
- Cấu hình máy đã dùng để đo tốc độ: *(điền ở Phase 10)*.
-----------------------------------------------------------------

conda activate action-recognition

cd /d D:\Project\Python\cv-action-recognition

1.python scripts/live_landmarks.py

2. python scripts/demo.py --model rules

3. python scripts/demo.py --model rf --log results/phase6/live_rf_work.csv

4. python scripts/demo.py --model rf --show-features --log results/phase6/live_rf_swipes.csv