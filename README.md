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
| `SWIPE_LEFT_SIGN` | `1` | 3 | `scripts/measure_direction.py` trên 189 clip IPN, ảnh không lật (2026-10-05): trung vị `dx` của `swipe_left` +0,456, của `swipe_right` −0,534 — trái dấu như phải có. Bằng chứng: `results/phase3/direction.md` |
| `IPN_FLIP_X` | `1` | 5 | IPN là chuẩn quy ước hướng; chỉ đổi thành `-1` khi phép thử webcam chứng minh ngược. Thử 2026-10-25 (người dùng, `demo.py --model hybrid`): vuốt sang trái của người dùng ra `swipe_left`, đúng chiều — giữ `1` |
| `AUG_NOISE_SIGMA` | `0.0159` | 4 | `scripts/estimate_sigma.py --src-label D0X` (2026-10-05): trung vị độ lệch chuẩn đầu ngón trên 18 cửa sổ tay nghỉ đứng yên của train, đơn vị lòng bàn tay. Lấy mọi cửa sổ `none` thì ra 0,054, vì phần lớn là cử động ngón có chủ ý. Bằng chứng: `results/phase4/sigma/run_02/` |
| `RULE_VX_HI`, `RULE_DX_HI`, `RULE_P_HI` | `4.026`, `0.1025`, `0.7209` | 5 | `scripts/calibrate_rules.py` trên tập `train` của IPN (2026-10-05). `RULE_VX_HI`: trung điểm của p90 `max_vx` lớp `none` và p10 của hai lớp vuốt; `RULE_DX_HI`: p10 `\|dx\|` của hai lớp vuốt; `RULE_P_HI`: trung điểm của p90 `\|pinch_delta\|` (`none` cộng hai lớp vuốt) và p10 của hai lớp zoom. Bằng chứng: `results/phase5/thresholds.md` |

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
| 2 | `python scripts/check_pipeline.py <landmarks.csv>` | Chạy `load_sequence` trên một CSV của Phase 1, in số frame, FPS thực, số bước lưới, độ lệch lưới lớn nhất, tỉ lệ bước `NaN` trước và sau khi vá (không ghi file) |
| 3 | `python scripts/extract_landmarks.py --source ipn` | Điểm mốc của mọi video IPN: `data/landmarks/ipn/<clip_id>.npz`. Bỏ qua clip đã có nên chạy lại là chạy tiếp; clip lỗi ghi vào `results/phase3/failed.txt`; `--workers N` chạy song song. Chạy qua đêm |
| 3 | `python scripts/measure_direction.py` | Đo `SWIPE_LEFT_SIGN` trên IPN: `results/phase3/direction.md` và `results/phase3/direction/run_NN/`; in dòng để dán vào `config.py` |
| 3 | `python scripts/dataset_stats.py` | Thống kê theo lớp, người, clip và nhãn gốc — tỉ lệ frame mất tay, thời lượng trung vị từng lớp: `results/phase3/dataset_stats/run_NN/` |
| 3 | `python scripts/export_examples.py` | Ba đoạn mẫu mỗi lớp đích, vẽ điểm mốc, không lật: `results/phase3/examples/*.mp4` — tư liệu viết `docs/gestures.md` |
| 4 | `python scripts/make_splits.py` | `data/splits.json` theo người, từ split chính thức của IPN (val là `VAL_FRACTION` số người của train, chọn với `SEED`); in phép giao giữa các tập, phải rỗng: `results/phase4/splits/run_NN/` |
| 4 | `python scripts/build_dataset.py` | `data/windows/windows.npz`; lớp `none` của train lấy mẫu con xuống `NONE_TRAIN_SHARE`. Bảng số cửa sổ theo tập và lớp: `results/phase4/build_dataset/run_NN/` |
| 4 | `python scripts/estimate_sigma.py --src-label D0X` | Ước lượng `AUG_NOISE_SIGMA` trên cửa sổ tay nghỉ của train: `results/phase4/sigma/run_NN/`; in dòng để dán vào `config.py` |
| 4 | `python scripts/plot_feature_boxplots.py` | Boxplot từng đặc trưng theo lớp trên train — cổng kiểm tra Phase 4: `results/phase4/boxplots/run_NN/`; phân vị 25/75 vào `results/phase4/ipn_feature_ranges.json`, mà `demo.py --show-features` dùng — từ 2026-10-26 gồm cả độ duỗi bốn ngón (`finger_extension.png`) |
| 4 | `python scripts/plot_window_examples.py` | Quỹ đạo cổ tay, độ xòe và độ mở cái–trỏ của một cửa sổ ngẫu nhiên mỗi lớp: `results/phase4/window_examples/run_NN/` |
| 5 | `python scripts/calibrate_rules.py` | Ba ngưỡng luật trên train: `results/phase5/thresholds.md` và `results/phase5/calibrate/run_NN/`; in ba dòng để dán vào `config.py` |
| 5 | `python scripts/eval_rules.py` | Luật trên val: ma trận nhầm lẫn, macro-F1, hai đường cơ sở: `results/phase5/eval_rules/run_NN/`; ghi hàng `rules` vào `results/model_comparison` |
| 5 | `python scripts/demo.py --model rules [--show-features] [--log <file.csv>]` | Demo webcam v0; `--show-features` là chế độ luyện cử chỉ theo IPN |
| 6 | `python scripts/train_rf.py` | Rừng ngẫu nhiên học trên train, đánh giá trên val: `results/phase6/train_rf/run_NN/` (ma trận nhầm lẫn, độ quan trọng, mức sự kiện, báo nhầm theo nhãn gốc); lưu `results/phase6/rf_model.joblib`; cập nhật `results/model_comparison` |
| 6 | `python scripts/sweep_rigid.py` | Quét tăng cường "bàn tay cứng" trên val: `results/phase6/sweep_rigid/run_NN/` (bảng `sweep`: lợi và giá của từng mức; bảng `shape_spread`: độ đổi dáng của tay thật so với bản tổng hợp) |
| 6 | `python scripts/probe_swipes.py` | Mô hình đang lưu coi gì là vuốt: `results/phase6/probe_swipes/run_NN/probe` |
| 6 | `python scripts/evaluate.py --model rf --split val` | Đánh giá mô hình đã lưu; `--split test` bắt buộc `--final` và ghi `results/TEST_USED.log` (luật 13) |
| 6 | `python scripts/demo.py --model rf --show-features --log <file.csv>` | Demo webcam; `--show-features` là chế độ luyện tập (bốn đặc trưng so với hộp IPN) |
| 6 | `python scripts/summarize_log.py <file.csv>` | Số cụm nhãn khác `none` và số cụm mỗi phút của một log demo |
| 7 | `python scripts/train_lstm.py` | LSTM học trên train (tăng cường mới mỗi epoch), dừng sớm theo macro-F1 val: `results/phase7/train_lstm/run_NN/` (đường học `training_curves.png`, lịch sử từng epoch, ma trận nhầm lẫn, bảng ba mô hình trên cùng tập val); lưu `results/phase7/lstm_model.pt` (`PHASE7_LSTM_PATH`, mô hình chính); cập nhật `results/model_comparison`. LSTM của demo là `LSTM_MODEL_PATH` — từ 2026-10-26 trỏ vào `train_lstm/run_08`; script này không bao giờ ghi vào đó |
| 7 | `python scripts/train_lstm.py --no-augment` | Khảo sát không tăng cường, dừng sớm như bản chính (`run_03`); không thay mô hình của demo, không ghi bảng so sánh |
| 7 | `python scripts/train_lstm.py --no-augment --patience 150` | Khảo sát không tăng cường, chạy đủ 150 epoch (`run_04`): đường học cho thấy điểm bắt đầu quá khớp |
| 7 | `python scripts/probe_swipes.py --model lstm` | LSTM coi gì là vuốt — cùng các phép thử như rừng: `results/phase7/probe_swipes/run_NN/probe` |
| 7 | `python scripts/probe_zooms.py` | Rừng và LSTM dựa vào phần nào của bàn tay để nhận zoom (ngón phụ duỗi / đứng yên, dáng tay tĩnh): `results/phase7/probe_zooms/run_NN/probe` |
| 7 | `python scripts/replay_log.py <file>_landmarks.npz` | Chạy lại một phiên demo đã ghi (`demo.py --log` ghi kèm điểm mốc) qua mọi mô hình, cùng đường ống: `results/phase7/replay/run_NN/timeline` |
| 7 | `python scripts/evaluate.py --model lstm --split val` | Đánh giá checkpoint LSTM đã lưu |
| 7 | `python scripts/demo.py --model lstm --log <file.csv>` | Demo webcam bằng LSTM (CPU); `--log` ghi kèm điểm mốc thô vào `<file>_landmarks.npz` |
| 7 | `python scripts/train_lstm.py --zoom-style-p 0.5 --static-share 0.1` | Khảo sát đổi dáng ngón phụ của zoom và bàn tay đứng yên (`run_08`); không thay mô hình của demo |
| 7 | `python scripts/train_lstm.py --stop-smooth 1` | Tái tạo `run_02`: dừng sớm theo điểm thô, cách cũ (khảo sát, không thay mô hình của demo) |
| 7 | `python scripts/evaluate.py --model hybrid --split val` | Mô hình ghép — vuốt theo LSTM, zoom theo rừng ngẫu nhiên: thêm hàng vào `results/model_comparison` |
| 7 | `python scripts/demo.py --model hybrid --show-features --log <file.csv>` | Demo webcam bằng mô hình ghép |
| 8 | `python scripts/evaluate.py --model <rules\|rf\|lstm\|hybrid> --events edge` | Đánh giá hai mức trên val. Mức cửa sổ: ma trận nhầm lẫn (hình nhiệt có số), F1 từng lớp, none bị báo nhầm theo nhãn gốc. Mức sự kiện: cả hệ thống chạy trên video val liên tục (`src/events.py`) — F1 sự kiện, số lệnh trên một cử chỉ, lệnh nhầm mỗi phút, lệnh nhầm theo nhãn gốc: `results/phase8/evaluate/run_NN/`; cập nhật `results/model_comparison`. `--events raw` là khi không có tầng kích hoạt |
| 8 | `python scripts/run_experiments.py` | Bảy bảng khảo sát và bảng phụ, trên val hoặc k-fold của người train + val: `results/phase8/experiments/run_NN/` (`table1_models` … `table7_kfold`, `table_extra`, hình nhiệt ba mô hình). Dữ liệu biến thể dựng vào `data/experiments/`; mỗi thí nghiệm một bản ghi dự đoán trong `results/phase8/records/` — chạy lại không học lại. LSTM chạy `EXP_JOBS` tiến trình song song (170 phút trên máy 8 luồng logic, kể cả dựng lại dữ liệu — đo 2026-10-25). Diễn giải các bảng: `results/phase8/notes.md` |
| 8 | `python scripts/run_experiments.py --list` | Danh sách thí nghiệm và thí nghiệm nào đã có bản ghi |
| 9 | `python scripts/evaluate.py --model <rules\|rf\|lstm\|hybrid> --events fsm` | Mức sự kiện với máy trạng thái kích hoạt (`src/activation.py`, tham số trong `config.py`): `results/phase8/evaluate/run_NN/`; cập nhật `results/model_comparison` |
| 9 | `python scripts/run_experiments.py` | Khi đã có bản ghi: dựng lại bảy bảng Phase 8 với `EVENT_FILTER = "fsm"`, không học lại (vài phút): `results/phase8/experiments/run_NN/` |
| 9 | `python scripts/sweep_activation.py` | Hai bảng đánh đổi trên video val, không học lại — `MIN_PRESENCE` lúc chạy (số liệu của `results/phase9/tradeoff.md`) và lưới `CONF_FIRE` × `K_OF_N`: `results/phase9/sweep_activation/run_NN/` |
| 9 | `python scripts/demo.py --model hybrid --log <file.csv>` | Demo có máy trạng thái: màn hình hiện trạng thái và lệnh vừa phát; log ghi trạng thái, lệnh, và mọi lần chuyển trạng thái vào `<file>_fsm.csv` |
| 10 | `pip install pyautogui` | Một lần: `demo.py` gửi phím tắt thật qua `pyautogui`, chỉ nạp khi bật điều khiển |
| 10 | `python scripts/demo.py --model lstm --log <file.csv>` | Demo hoàn chỉnh, cấu hình cuối (`results/phase10/final_config.md`, người dùng chọn 2026-10-26): LSTM `train_lstm/run_08` (`LSTM_MODEL_PATH`), `CONF_FIRE` 0,85, `K_OF_N` 4/5. Phím `c` bật/tắt điều khiển (mặc định **tắt**; `swipe_left` → mũi tên trái = slide trước, `swipe_right` → mũi tên phải = slide sau, zoom → Ctrl + / Ctrl −); `?` hiện tóm tắt `docs/gestures.md`; log ghi thêm phím đã gửi |
| 10 | `python scripts/demo.py --model lstm --show-features` | Luyện zoom kiểu IPN: phím 3 (`zoom_in`) hoặc 4 (`zoom_out`) hiện thêm `ring_ext`, `pinky_ext` — độ duỗi nhẫn, út so với hộp IPN (≈ 0,4–0,7); xanh là đã gập như IPN |
| 10 | `python scripts/bench.py speed --light bright` rồi `--light dim` | FPS (bỏ 3 s đầu, đo 30 s) và phân rã thời gian từng khâu cho bốn mô hình, mỗi mức ánh sáng một lần: `results/phase10/speed/run_NN/` (`speed`, `breakdown`, kèm cấu hình máy) |
| 10 | `python scripts/bench.py record <reading\|typing\|talking>` | Ghi 10 phút làm việc bình thường, KHÔNG làm cử chỉ: ngồi yên đọc tài liệu; gõ phím và dùng chuột; nói chuyện có khua tay. Phiên ở `results/phase10/sessions/`; không gửi phím nào |
| 10 | `python scripts/bench.py record gestures` | Ghi 20 cử chỉ theo lời nhắc trên màn hình, 5 mỗi lớp (~2,5 phút); lời nhắc lưu thành đoạn có nhãn |
| 10 | `python scripts/bench.py analyze` | Chạy lại mọi phiên đã ghi và video val qua bốn mô hình × ba cấu hình của bảng đánh đổi (`FSM_TRADEOFF`): kích hoạt nhầm mỗi phút theo kịch bản (gộp theo thời lượng, kèm nhầm mỗi phút có tay), số lệnh trên một cử chỉ, độ trễ, bảng đánh đổi — `results/phase10/analyze/run_NN/` |

---

## Tái lập

- Seed cố định: `config.SEED = 42`, đặt cho `random`, `numpy` và `torch`.
- Camera dùng suốt dự án: 640×480 @ 30 FPS (`CAM_W`, `CAM_H`, `CAM_FPS`).
- Cấu hình máy đã dùng để đo tốc độ: *(điền ở Phase 10)*.
-----------------------------------------------------------------

conda activate action-recognition

cd /d D:\Project\Python\cv-action-recognition

python scripts/demo.py --model hybrid