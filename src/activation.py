"""Logic kích hoạt — máy trạng thái biến chuỗi dự đoán thành lệnh rời rạc (Phase 9).

Mô hình trả lời "cửa sổ vừa rồi trông giống cử chỉ gì"; hệ thống điều khiển cần
trả lời "có nên phát lệnh ngay bây giờ không". Bốn khoảng cách giữa hai câu hỏi
không sửa được bằng một mô hình tốt hơn (cẩm nang bước 18): một cử chỉ sinh
nhiều cửa sổ, nhãn nhấp nháy, cửa sổ chuyển tiếp lúc đưa tay vào, và không có
cách huỷ.

Bốn trạng thái (SPEC Phase 9)::

    IDLE ──có tay──► READY ──cử chỉ, độ tin ≥ CONF_FIRE──► CANDIDATE
                      ▲  ▲                                    │
                      │  └──────── đồng thuận thất bại ───────┤
                      │                                       │ k cửa sổ đồng ý:
                      └── hết COOLDOWN_SEC ── COOLDOWN ◄──────┘ PHÁT LỆNH
    mất tay, từ mọi trạng thái ──► IDLE

Năm cơ chế, tham số đọc từ ``config.py`` lúc tạo máy:

1. **Ngưỡng tin cậy** ``CONF_FIRE``: chỉ một cửa sổ cử chỉ đủ tin mới mở ứng viên.
2. **Đồng thuận** ``K_OF_N = (k, n)``: ứng viên thành lệnh khi có ``k`` cửa sổ
   đồng ý trong ``n`` cửa sổ kể từ lúc mở, tính cả cửa sổ mở.
3. **Cooldown** ``COOLDOWN_SEC``: sau một lệnh, không nhận lệnh mới.
4. **Trễ** ``CONF_HOLD < CONF_FIRE``: mở ứng viên cần ``CONF_FIRE``, đồng ý chỉ
   cần ``CONF_HOLD``.
5. **Hạ tay để huỷ**: không có cửa sổ (``presence`` là ``None``: tay vắng quá
   ``1 − MIN_PRESENCE`` cửa sổ, hay vừa đưa tay vào chưa đủ ``WIN_SEC``) thì về
   ``IDLE`` và quên hết, kể cả cooldown.

**Họ zoom có ngưỡng riêng** ``FSM_ZOOM_FIRE``, ``FSM_ZOOM_K`` (người dùng chọn
2026-11-01; ``results/phase10/notes.md`` mục 7). Ứng viên zoom mở ở ``FSM_ZOOM_FIRE``,
cần ``FSM_ZOOM_K`` phiếu, và ngưỡng giữ là ``min(CONF_HOLD, FSM_ZOOM_FIRE)``. Lý do:
zoom của mô hình ghép đi theo rừng ngẫu nhiên, mà thang độ tin của rừng thấp hơn
LSTM. Vuốt vẫn dùng ``CONF_FIRE``, ``K_OF_N``, ``CONF_HOLD``: đoạn lấy đà ngược
chiều cũng có độ tin 1,00, nên chỉ đòi nhiều phiếu mới chặn được nó.

**Một cửa sổ khi đang có ứng viên** (cách hiểu "đồng thuận", 2026-10-25):

- *đồng ý*: cùng lớp với ứng viên, độ tin ≥ ``CONF_HOLD``;
- *phản đối*: lớp khác — kể cả ``none`` — với độ tin ≥ ``CONF_HOLD``. Đồng thuận
  thất bại ngay, và cửa sổ đó được xét lại như ở ``READY``: một cử chỉ khác đủ
  tin mở luôn ứng viên mới;
- *do dự*: không có dự đoán, hoặc độ tin < ``CONF_HOLD``. Không phải phiếu nào,
  nhưng chiếm một chỗ trong ``n``.

Hiểu "k trong n cửa sổ gần nhất" theo nghĩa đen — đếm phiếu trên cửa sổ trượt —
thì chuỗi nhấp nháy vuốt, none, vuốt, none, vuốt có 3/5 phiếu và PHÁT lệnh,
đúng điều kiểm thử bắt buộc của SPEC cấm. Ở đây một ``none`` tự tin là phiếu
phản đối, còn ``n`` là dung sai cho các cửa sổ do dự.

**Trọng tài chiều ngược** ``FSM_ARBITRATE_SEC`` (Phase 11, 2026-11-10). Động tác
chuẩn bị là một cử chỉ ngắn NGƯỢC chiều: chụm ngón trước khi mở (zoom), kéo tay
ngược lại trước khi hất (vuốt). Mô hình gọi nó đúng chiều của nó, với độ tin cao.
Khi nó đủ phiếu trước, lệnh sai phát ra, rồi cooldown chặn cử chỉ thật
(``results/phase11/notes.md`` mục 3). Với ``FSM_ARBITRATE_SEC`` > 0::

    CANDIDATE ──đủ phiếu──► PENDING ──hết giờ, không ai thách──► COOLDOWN: phát lệnh chờ
                              │
                              └── lớp NGƯỢC chiều cùng họ đủ phiếu ──► COOLDOWN: phát
                                  lệnh có chuyển động mạnh hơn

- Đủ phiếu thì không phát ngay mà CHỜ ``FSM_ARBITRATE_SEC`` giây.
- Trong lúc chờ, lớp ngược chiều cùng họ (``OPPOSITE``) được mở và bỏ phiếu như một
  ứng viên thường — kẻ thách thức. Nó đủ phiếu thì so độ mạnh: chuyển động mạnh nhất
  theo chiều của mỗi lớp trên các cửa sổ đã đồng ý với nó (``strength``, từ
  ``windows.window_strengths``). Mạnh hơn thì thắng; bằng nhau thì lệnh chờ thắng.
- Kẻ thách thức đang đếm phiếu khi hết giờ thì được đếm cho xong ``n`` cửa sổ.
- Mất tay khi đang chờ thì PHÁT lệnh chờ: nó đã đủ phiếu — với máy cũ nó đã phát rồi.
- Không có ``strength`` (bộ lọc cũ, bản lưu cũ) hoặc ``FSM_ARBITRATE_SEC`` = 0 thì
  phát ngay như trước.
- Người dùng chọn mặc định 0,4 s (2026-11-10): lệnh ngược chiều giảm, trễ trung vị từ
  0,76 lên 1,15 s (``results/phase11/notes.md`` mục 4).

Chọn "mạnh hơn" chứ không "đến sau": động tác chuẩn bị đứng TRƯỚC cử chỉ thật, lúc
thu tay đứng SAU — cả hai thường yếu hơn cử chỉ thật, đúng giả định khoảnh khắc
chính của việc gán nhãn. Cái giá: mọi lệnh trễ thêm tới ``FSM_ARBITRATE_SEC``.
"""

from src import config

IDLE, READY, CANDIDATE, PENDING, COOLDOWN = ("IDLE", "READY", "CANDIDATE", "PENDING",
                                             "COOLDOWN")
STATES = (IDLE, READY, CANDIDATE, PENDING, COOLDOWN)
#: Chỉ số bốn lớp cử chỉ — những lớp duy nhất thành lệnh.
GESTURES = tuple(range(1, len(config.CLASSES)))
#: Hai lớp zoom — họ có ngưỡng riêng.
ZOOMS = tuple(config.CLASSES.index(name) for name in ("zoom_in", "zoom_out"))
#: Lớp ngược chiều cùng họ — trọng tài chỉ phân xử giữa hai lớp này.
OPPOSITE = {config.CLASSES.index(a): config.CLASSES.index(b)
            for pair in (("swipe_left", "swipe_right"), ("zoom_in", "zoom_out"))
            for a, b in (pair, pair[::-1])}


class ActivationFSM:
    """Máy trạng thái kích hoạt. Toàn bộ trạng thái nằm trong đối tượng: mỗi
    phiên demo và mỗi video đánh giá dùng một máy mới (``events.make_filter``).

    Args:
        conf_fire, conf_hold, k_of_n, cooldown_sec, zoom_fire, zoom_k,
            arbitrate_sec: ``None`` là giá trị trong ``config.py``. Khác ``None``
            chỉ khi quét tham số (``scripts/sweep_activation.py``,
            ``scripts/bench.py``) và trong kiểm thử. Quét một ngưỡng chung cho mọi
            lớp thì truyền cả ``zoom_fire``, ``zoom_k``.
        on_transition: hàm ``(ts, từ, tới, lý do)``, gọi ở MỌI lần chuyển trạng
            thái — ``demo.py --log`` ghi chúng ra file.

    Raises:
        ValueError: ``conf_hold > conf_fire``, ``k``, ``zoom_k`` ngoài ``[1, n]``,
            hay ``arbitrate_sec`` âm.
    """

    def __init__(self, conf_fire=None, conf_hold=None, k_of_n=None, cooldown_sec=None,
                 zoom_fire=None, zoom_k=None, arbitrate_sec=None, on_transition=None):
        self.conf_fire = config.CONF_FIRE if conf_fire is None else conf_fire
        self.conf_hold = config.CONF_HOLD if conf_hold is None else conf_hold
        self.k, self.n = config.K_OF_N if k_of_n is None else k_of_n
        self.cooldown_sec = config.COOLDOWN_SEC if cooldown_sec is None else cooldown_sec
        self.zoom_fire = config.FSM_ZOOM_FIRE if zoom_fire is None else zoom_fire
        self.zoom_k = config.FSM_ZOOM_K if zoom_k is None else zoom_k
        self.arbitrate_sec = (config.FSM_ARBITRATE_SEC if arbitrate_sec is None
                              else arbitrate_sec)
        if self.conf_hold > self.conf_fire:
            raise ValueError(f"CONF_HOLD {self.conf_hold} phải ≤ CONF_FIRE {self.conf_fire}")
        if not 1 <= self.k <= self.n:
            raise ValueError(f"K_OF_N = ({self.k}, {self.n}): cần 1 ≤ k ≤ n")
        if not 1 <= self.zoom_k <= self.n:
            raise ValueError(f"FSM_ZOOM_K = {self.zoom_k}, n = {self.n}: cần 1 ≤ k ≤ n")
        if self.arbitrate_sec < 0:
            raise ValueError(f"FSM_ARBITRATE_SEC = {self.arbitrate_sec}: không được âm")
        self.on_transition = on_transition
        self.state = IDLE
        self.fired_at = None
        self._forget()

    def update(self, label, confidence, presence, ts, strength=None):
        """Một lần dự đoán, theo thứ tự thời gian.

        Args:
            label: chỉ số lớp, hoặc ``None`` khi không có cửa sổ hợp lệ.
            confidence: độ tin của ``label``; ``None`` khi ``label`` là ``None``.
            presence: tỉ lệ bước có tay của cửa sổ; ``None`` khi bộ đệm không trả
                cửa sổ nào — với máy trạng thái, đó là mất tay.
            ts: giây.
            strength: ``windows.window_strengths`` của cửa sổ, cho trọng tài chiều
                ngược; ``None`` thì cửa sổ này không góp độ mạnh.

        Returns:
            chỉ số lớp của lệnh vừa phát, hoặc ``None``.
        """
        if presence is None:
            command = None
            if self.state == PENDING:
                command = self._fire(ts, self.pending, "mất tay khi đang chờ")
            if self.state != IDLE:
                self._forget()
                self.fired_at = None
                self._go(IDLE, ts, "mất tay")
            return command
        if self.state == IDLE:
            self._go(READY, ts, "có tay")
        if self.state == COOLDOWN:
            if ts - self.fired_at < self.cooldown_sec:
                return None
            self.fired_at = None
            self._go(READY, ts, "hết cooldown")
        if self.state == PENDING:
            return self._wait(label, confidence, ts, strength)
        if self.state == CANDIDATE:
            command = self._vote(label, confidence, ts, strength)
            if self.state != READY:
                return command
        return self._open(label, confidence, ts, strength)

    def _open(self, label, confidence, ts, strength=None):
        """``READY``: một cửa sổ cử chỉ đủ tin mở ứng viên."""
        if label not in GESTURES or confidence is None:
            return None
        fire, need, hold = self._family(label)
        if not confidence >= fire:
            return None
        self.candidate, self.agree, self.seen = int(label), 1, 1
        self.need, self.hold = need, hold
        self.power = _stronger(None, label, strength)
        self._go(CANDIDATE, ts, f"mở {config.CLASSES[label]} {confidence:.2f}")
        return self._agreed(ts) if self.agree >= self.need else None

    def _family(self, label):
        """``(ngưỡng mở, số phiếu cần, ngưỡng giữ)`` của họ cử chỉ chứa ``label``."""
        if label in ZOOMS:
            return self.zoom_fire, self.zoom_k, min(self.conf_hold, self.zoom_fire)
        return self.conf_fire, self.k, self.conf_hold

    def _vote(self, label, confidence, ts, strength=None):
        """``CANDIDATE``: cửa sổ này đồng ý, phản đối, hay do dự."""
        self.seen += 1
        confident = (label is not None and confidence is not None
                     and confidence >= self.hold)
        if confident and label == self.candidate:
            self.agree += 1
            self.power = _stronger(self.power, label, strength)
            if self.agree >= self.need:
                return self._agreed(ts)
        elif confident:
            reason = f"{config.CLASSES[label]} phản đối {config.CLASSES[self.candidate]}"
            self._forget()
            self._go(READY, ts, reason)
            return None
        if self.seen >= self.n:
            reason = f"{self.agree}/{self.need} đồng ý sau {self.n} cửa sổ"
            self._forget()
            self._go(READY, ts, reason)
        return None

    def _agreed(self, ts):
        """Ứng viên đủ phiếu: phát ngay, hoặc chờ trọng tài chiều ngược."""
        if self.arbitrate_sec <= 0 or self.power is None:
            return self._fire(ts)
        self.pending, self.pending_power = self.candidate, self.power
        self.pending_hold, self.deadline = self.hold, ts + self.arbitrate_sec
        self._clear_candidate()
        self._go(PENDING, ts, f"chờ {config.CLASSES[self.pending]} "
                              f"(mạnh {self.pending_power:.2f})")
        return None

    def _wait(self, label, confidence, ts, strength):
        """``PENDING``: lớp chờ thêm độ mạnh; lớp ngược chiều cùng họ thách thức."""
        if (label == self.pending and confidence is not None
                and confidence >= self.pending_hold):
            self.pending_power = _stronger(self.pending_power, label, strength)
        if self.candidate is None:
            rival = OPPOSITE[self.pending]
            fire, need, hold = self._family(rival)
            if (label == rival and confidence is not None and confidence >= fire
                    and strength is not None):
                self.candidate, self.agree, self.seen = rival, 1, 1
                self.need, self.hold = need, hold
                self.power = _stronger(None, rival, strength)
                self._go(PENDING, ts, f"{config.CLASSES[rival]} thách thức "
                                      f"{confidence:.2f}")
                if self.agree >= self.need:
                    return self._settle(ts)
        else:
            self.seen += 1
            confident = (label is not None and confidence is not None
                         and confidence >= self.hold)
            if confident and label == self.candidate:
                self.agree += 1
                self.power = _stronger(self.power, label, strength)
                if self.agree >= self.need:
                    return self._settle(ts)
            elif confident:
                self._clear_candidate()
                self._go(PENDING, ts, f"{config.CLASSES[label]} phản đối kẻ thách thức")
            if self.candidate is not None and self.seen >= self.n:
                self._clear_candidate()
                self._go(PENDING, ts, f"kẻ thách thức không đủ phiếu sau {self.n} cửa sổ")
        if self.candidate is None and ts >= self.deadline:
            return self._fire(ts, self.pending, "hết giờ chờ")
        return None

    def _settle(self, ts):
        """Kẻ thách thức đủ phiếu: chuyển động mạnh hơn thắng, bằng nhau thì lệnh chờ."""
        mine, theirs = config.CLASSES[self.pending], config.CLASSES[self.candidate]
        if self.power > self.pending_power:
            return self._fire(ts, self.candidate, f"{theirs} {self.power:.2f} mạnh hơn "
                                                  f"{mine} {self.pending_power:.2f}")
        return self._fire(ts, self.pending, f"{mine} {self.pending_power:.2f} không yếu hơn "
                                            f"{theirs} {self.power:.2f}")

    def _fire(self, ts, command=None, why=""):
        command = self.candidate if command is None else command
        self._forget()
        self.fired_at = ts
        self._go(COOLDOWN, ts, f"PHÁT {config.CLASSES[command]}" + (f": {why}" if why else ""))
        return command

    def _clear_candidate(self):
        self.candidate, self.agree, self.seen = None, 0, 0
        self.need, self.hold, self.power = None, None, None

    def _forget(self):
        self._clear_candidate()
        self.pending, self.pending_power, self.pending_hold, self.deadline = (None, None,
                                                                              None, None)

    def _go(self, state, ts, reason):
        previous, self.state = self.state, state
        if self.on_transition is not None:
            self.on_transition(ts, previous, state, reason)


def _stronger(power, label, strength):
    """Độ mạnh lớn nhất tới giờ của một ứng viên lớp ``label``: ``power`` hay
    ``strength[label]`` của cửa sổ mới; cửa sổ không có ``strength`` thì giữ nguyên."""
    if strength is None:
        return power
    value = float(strength[label])
    return value if power is None else max(power, value)
