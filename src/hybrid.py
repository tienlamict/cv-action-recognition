"""Mô hình ghép cho demo (thêm 2026-10-10): vuốt theo LSTM, zoom theo rừng ngẫu nhiên.

Mỗi mô hình được tin ở đúng họ cử chỉ mà các phép thăm dò cho thấy nó vững
(``results/phase7/notes.md`` mục 5 và 9):

- **LSTM nhận vuốt** qua động tác của các ngón, nên chịu được kiểu hất rồi kéo
  tay về ngay, hay cổ tay đi ngắn (``probe_swipes.py --model lstm``).
- **Rừng nhận zoom** qua khoảng cách cái–trỏ, nên ít phụ thuộc các ngón còn lại
  và không bao giờ báo zoom khi bàn tay đứng yên. LSTM thì học luôn kiểu zoom
  riêng của IPN — nhẫn và út gập — và trả ``none`` khi người dùng zoom khác đi
  (``probe_zooms.py``).

Luật, theo thứ tự — vuốt xét trước zoom như luật của Phase 5:

1. LSTM đoán một lớp vuốt → lớp đó, độ tin của LSTM;
2. rừng đoán một lớp zoom → lớp đó, độ tin của rừng;
3. còn lại → ``none``.

Dự đoán zoom của LSTM và dự đoán vuốt của rừng bị bỏ qua.

File này không nạp ``torch`` hay scikit-learn khi import: hai mô hình nạp lười
như ở ``demo.py``.
"""

import numpy as np

from src.augment import SWIPE_LABELS, ZOOM_LABELS

NONE = 0


def hybrid_labels(lstm_labels, rf_labels):
    """Luật ghép trên các nhãn đã đoán — một chỗ duy nhất, cho cả đánh giá theo
    lô lẫn demo.

    Returns:
        ``(n,) int64``.
    """
    lstm_labels = np.asarray(lstm_labels, dtype=np.int64)
    rf_labels = np.asarray(rf_labels, dtype=np.int64)
    return np.where(np.isin(lstm_labels, SWIPE_LABELS), lstm_labels,
                    np.where(np.isin(rf_labels, ZOOM_LABELS), rf_labels, NONE)
                    ).astype(np.int64)


class HybridClassifier:
    """Mô hình ghép dạng hàm ``(cửa sổ, đặc trưng) → (label, confidence)``.

    ``input_kind = "both"``: ``LivePredictor`` đưa cả cửa sổ đã chuẩn hoá (cho
    LSTM) lẫn vector đặc trưng (cho rừng). ``confidence`` là xác suất của mô
    hình đã quyết định nhãn; với ``none`` là mức cao hơn trong hai xác suất
    ``none``.
    """

    input_kind = "both"

    def __init__(self, lstm_path=None, rf_path=None):
        from src.forest import ForestClassifier

        self.forest = ForestClassifier(rf_path)
        self.lstm_path = lstm_path
        self.lstm = None

    def load(self):
        if self.lstm is None:
            from src.models import LSTMRunner      # torch: chỉ nạp khi dùng
            self.lstm = LSTMRunner(self.lstm_path).load()
        self.forest.load()
        return self

    def __call__(self, win_norm, features):
        self.load()
        p_lstm, p_rf = self.lstm.proba(win_norm), self.forest.proba(features)
        label = int(hybrid_labels([np.argmax(p_lstm)], [np.argmax(p_rf)])[0])
        if label in SWIPE_LABELS:
            return label, float(p_lstm[label])
        if label in ZOOM_LABELS:
            return label, float(p_rf[label])
        return label, float(max(p_lstm[NONE], p_rf[NONE]))
