"""Phát phím tắt thật cho lệnh của máy trạng thái (Phase 10), qua pyautogui.

Mặc định TẮT (cẩm nang 19.e): lúc phát triển, demo chạy hàng chục lần, và một hệ
thống tự bấm phím trong lúc đang gõ code là trải nghiệm tệ. Bấm
``CTRL_TOGGLE_KEY`` trong cửa sổ demo để bật hay tắt.

**Zoom chọn cách theo cửa sổ đang có focus** (người dùng yêu cầu 2026-11-12):

- PowerPoint đang trình chiếu (F5) hay Presenter View — lớp cửa sổ thuộc
  ``CTRL_SLIDESHOW_CLASSES``: phím của ``CTRL_HOTKEYS`` (``+`` / ``−``), như trước;
- mọi cửa sổ khác — PowerPoint đang soạn, trình duyệt, Word, trình đọc PDF: giữ Ctrl
  rồi cuộn chuột ``CTRL_ZOOM_SCROLL`` nấc. Lúc soạn, PowerPoint không zoom bằng
  ``+`` / ``−``. Cuộn đi vào cửa sổ DƯỚI CON TRỎ chuột, nên đặt chuột trên slide.

Chỉ Windows đọc được lớp cửa sổ; nơi khác luôn dùng phím, như trước. Vuốt luôn dùng
phím của ``CTRL_HOTKEYS``.

pyautogui chỉ được nạp ở lần đầu bật điều khiển, nên kiểm thử và máy chưa cài nó
vẫn chạy demo được. Kéo chuột vào một góc màn hình là phanh khẩn cấp của pyautogui
(``FAILSAFE``).
"""

from src import config


class Controller:
    """Cờ bật/tắt điều khiển và việc gửi phím của một lệnh.

    Args:
        hotkeys: tên lớp → tổ hợp phím; ``None`` là ``CTRL_HOTKEYS``.
        zoom_scroll: tên lớp zoom → số nấc cuộn kèm Ctrl ngoài lúc trình chiếu;
            ``None`` là ``CTRL_ZOOM_SCROLL``.
        send: hàm ``(*phím)`` gửi một tổ hợp phím; ``None`` là
            ``pyautogui.hotkey``, nạp ở lần đầu bật. Kiểm thử truyền hàm giả.
        scroll: hàm ``(nấc)`` giữ Ctrl và cuộn chuột; ``None`` là bản pyautogui,
            nạp cùng ``send``. Không có thì zoom dùng phím.
        foreground: hàm ``() → lớp cửa sổ đang có focus`` (``None`` khi không đọc
            được); ``None`` là :func:`foreground_class`.
    """

    def __init__(self, hotkeys=None, zoom_scroll=None, send=None, scroll=None,
                 foreground=None):
        self.hotkeys = config.CTRL_HOTKEYS if hotkeys is None else hotkeys
        self.zoom_scroll = config.CTRL_ZOOM_SCROLL if zoom_scroll is None else zoom_scroll
        self.enabled = False
        self.last_window = None
        self._send = send
        self._scroll = scroll
        self._foreground = foreground_class if foreground is None else foreground

    def toggle(self):
        """Bật nếu đang tắt, tắt nếu đang bật.

        Returns:
            trạng thái mới.

        Raises:
            RuntimeError: bật lần đầu mà chưa cài pyautogui; cờ vẫn tắt.
        """
        if not self.enabled and self._send is None:
            self._send, scroll = _pyautogui_actions()
            self._scroll = self._scroll or scroll
        self.enabled = not self.enabled
        return self.enabled

    def handle(self, command):
        """Gửi phím — hay Ctrl và cuộn chuột — của ``command`` (chỉ số lớp) nếu
        điều khiển đang bật.

        Returns:
            tổ hợp đã gửi, mỗi phần một chuỗi (log nối bằng ``+``), hoặc ``None``.
        """
        if command is None or not self.enabled:
            return None
        name = config.CLASSES[command]
        if name in self.zoom_scroll and self._scroll is not None and not self.in_slideshow():
            notches = int(self.zoom_scroll[name])
            self._scroll(notches)
            return ("ctrl", f"cuộn {'lên' if notches > 0 else 'xuống'} {abs(notches)} nấc")
        keys = tuple(self.hotkeys[name])
        self._send(*keys)
        return keys

    def in_slideshow(self):
        """Cửa sổ đang có focus là PowerPoint đang trình chiếu. Không đọc được lớp
        cửa sổ thì coi như đang trình chiếu — zoom dùng phím, như trước. Lớp vừa
        đọc giữ ở ``last_window``."""
        self.last_window = self._foreground()
        return self.last_window is None or self.last_window in config.CTRL_SLIDESHOW_CLASSES


def foreground_class():
    """Lớp của cửa sổ đang có focus, ví dụ ``"screenClass"`` khi PowerPoint đang
    trình chiếu. Chỉ đọc được trên Windows; nơi khác, hay khi không có cửa sổ nào,
    trả ``None``."""
    import ctypes
    try:
        user32 = ctypes.WinDLL("user32")
    except (AttributeError, OSError):       # không phải Windows
        return None
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    user32.GetClassNameW.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int)
    window = user32.GetForegroundWindow()
    if not window:
        return None
    name = ctypes.create_unicode_buffer(config.CTRL_CLASS_NAME_MAX)
    return name.value if user32.GetClassNameW(window, name, len(name)) else None


def _pyautogui_actions():
    """``(gửi tổ hợp phím, giữ Ctrl và cuộn n nấc)`` bằng pyautogui."""
    try:
        import pyautogui
    except ImportError as error:
        raise RuntimeError("Chưa cài pyautogui — chạy: pip install pyautogui") from error
    pyautogui.FAILSAFE = True

    def ctrl_scroll(notches):
        # Không nghỉ giữa các bước: phím Ctrl và cú cuộn vào hàng đợi theo đúng thứ
        # tự, nên ứng dụng thấy Ctrl đang giữ; nghỉ thì vòng lặp demo đứng hình.
        pyautogui.keyDown("ctrl", _pause=False)
        try:
            pyautogui.scroll(int(notches * config.CTRL_WHEEL_DELTA), _pause=False)
        finally:
            pyautogui.keyUp("ctrl", _pause=False)

    return pyautogui.hotkey, ctrl_scroll
