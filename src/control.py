"""Phát phím tắt thật cho lệnh của máy trạng thái (Phase 10), qua pyautogui.

Mặc định TẮT (cẩm nang 19.e): lúc phát triển, demo chạy hàng chục lần, và một hệ
thống tự bấm phím trong lúc đang gõ code là trải nghiệm tệ. Bấm
``CTRL_TOGGLE_KEY`` trong cửa sổ demo để bật hay tắt.

pyautogui chỉ được nạp ở lần đầu bật điều khiển, nên kiểm thử và máy chưa cài nó
vẫn chạy demo được. Kéo chuột vào một góc màn hình là phanh khẩn cấp của pyautogui
(``FAILSAFE``).
"""

from src import config


class Controller:
    """Cờ bật/tắt điều khiển và việc gửi phím của một lệnh.

    Args:
        hotkeys: tên lớp → tổ hợp phím; ``None`` là ``CTRL_HOTKEYS``.
        send: hàm ``(*phím)`` gửi một tổ hợp phím; ``None`` là
            ``pyautogui.hotkey``, nạp ở lần đầu bật. Kiểm thử truyền hàm giả.
    """

    def __init__(self, hotkeys=None, send=None):
        self.hotkeys = config.CTRL_HOTKEYS if hotkeys is None else hotkeys
        self.enabled = False
        self._send = send

    def toggle(self):
        """Bật nếu đang tắt, tắt nếu đang bật.

        Returns:
            trạng thái mới.

        Raises:
            RuntimeError: bật lần đầu mà chưa cài pyautogui; cờ vẫn tắt.
        """
        if not self.enabled and self._send is None:
            self._send = _pyautogui_hotkey()
        self.enabled = not self.enabled
        return self.enabled

    def handle(self, command):
        """Gửi phím của ``command`` (chỉ số lớp) nếu điều khiển đang bật.

        Returns:
            tổ hợp phím đã gửi, hoặc ``None``.
        """
        if command is None or not self.enabled:
            return None
        keys = tuple(self.hotkeys[config.CLASSES[command]])
        self._send(*keys)
        return keys


def _pyautogui_hotkey():
    try:
        import pyautogui
    except ImportError as error:
        raise RuntimeError("Chưa cài pyautogui — chạy: pip install pyautogui") from error
    pyautogui.FAILSAFE = True
    return pyautogui.hotkey
