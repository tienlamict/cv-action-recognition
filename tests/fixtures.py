"""Cửa sổ tổng hợp ở toạ độ PIXEL để kiểm thử.

Không kiểm thử nào được phụ thuộc vào dữ liệu thật hay webcam: một kiểm thử chỉ
chạy được khi có camera là một kiểm thử sẽ bị tắt đi lúc bận.

Bàn tay mẫu dựng quanh ``CENTER``, cỡ lòng bàn tay (khoảng cách điểm 0 → 9)
đúng ``PALM_PX`` pixel — cùng thứ mà ``normalize_window`` dùng làm đơn vị.
Trục ``y`` hướng XUỐNG như hệ toạ độ ảnh, nên ngón tay chĩa lên là ``y`` âm.
"""

import numpy as np

from src import config

PALM_PX = 80.0                  # khoảng cách cổ tay → gốc ngón giữa
CENTER = (320.0, 240.0)         # giữa khung 640x480
OPEN_WIDE, OPEN_TIGHT = 1.0, 0.2    # độ xòe: 1.0 = xòe hết, 0.2 = chụm
SWIPE_PALMS = 3.0               # quãng dời của một cú vuốt, tính theo cỡ lòng bàn tay
WAVE_CYCLES = 2                 # số chu kỳ của một lần vẫy tay
WAVE_PALMS = 1.5                # biên độ vẫy tay
STATIC_NOISE_PX = 0.5           # nhiễu của tay "đứng yên"

# Hướng của 5 ngón, tính bằng độ so với phương thẳng đứng (dương = sang phải).
_FINGER_ANGLES = (-50.0, -15.0, 0.0, 15.0, 30.0)
# Bán kính khớp bàn tay (MCP) của từng ngón, theo đơn vị cỡ lòng bàn tay.
_KNUCKLE_RADII = (0.55, 0.95, 1.00, 0.95, 0.85)
# Ba khớp còn lại của mỗi ngón nằm xa thêm bấy nhiêu, nhân với độ xòe.
_JOINT_STEPS = (0.35, 0.70, 1.05)


def hand(openness=OPEN_WIDE, center=CENTER, palm_px=PALM_PX):
    """Một bàn tay 21 điểm ``(21, 2)`` pixel.

    ``openness`` 0 là nắm lại, 1 là xòe hết. Cổ tay đặt tại ``center``, và
    khoảng cách điểm 0 → 9 luôn đúng bằng ``palm_px`` bất kể độ xòe.
    """
    points = np.zeros((config.NUM_LANDMARKS, 2), dtype=np.float64)
    for finger, (angle, knuckle) in enumerate(zip(_FINGER_ANGLES,
                                                  _KNUCKLE_RADII)):
        radians = np.deg2rad(angle)
        direction = np.array([np.sin(radians), -np.cos(radians)])
        radii = [knuckle] + [knuckle + step * openness for step in _JOINT_STEPS]
        for joint, radius in enumerate(radii):
            points[1 + finger * 4 + joint] = direction * radius * palm_px
    points[config.WRIST] = (0.0, 0.0)
    # Ghi đè cho chắc: cỡ lòng bàn tay (0 → 9) đúng palm_px, không phụ thuộc
    # độ xòe — đây là đơn vị mà normalize_window dùng.
    points[config.MIDDLE_MCP] = (0.0, -palm_px)
    return points + np.asarray(center, dtype=np.float64)


def make_swipe(direction, steps=None):
    """Vuốt ngang: cổ tay dời thẳng, hình dạng bàn tay không đổi.

    Args:
        direction: ``+1`` dời theo chiều ``x`` tăng, ``-1`` chiều ngược lại.
            Đây là chiều TRONG ẢNH, không phải nhãn trái/phải — việc dịch sang
            nhãn là của Phase 3.
    """
    steps = steps or config.T
    shift = np.sign(direction) * SWIPE_PALMS * PALM_PX
    offsets = np.linspace(0.0, shift, steps)
    return np.stack([hand(center=(CENTER[0] + dx, CENTER[1]))
                     for dx in offsets])


def make_zoom(direction, steps=None):
    """Zoom: cổ tay đứng yên, các đầu ngón xòe ra (``"in"``) hoặc chụm lại."""
    steps = steps or config.T
    if direction not in ("in", "out"):
        raise ValueError('direction phải là "in" hoặc "out"')
    start, end = ((OPEN_TIGHT, OPEN_WIDE) if direction == "in"
                  else (OPEN_WIDE, OPEN_TIGHT))
    return np.stack([hand(openness=o) for o in np.linspace(start, end, steps)])


def make_static(steps=None, seed=config.SEED):
    """Tay giữ nguyên chỗ, chỉ rung nhẹ như điểm mốc thật."""
    steps = steps or config.T
    rng = np.random.default_rng(seed)
    base = hand()
    noise = rng.normal(0.0, STATIC_NOISE_PX, size=(steps, *base.shape))
    return base[None, :, :] + noise


def make_wave(steps=None):
    """Vẫy tay qua lại: đi rất xa nhưng dời được rất ít — mẫu âm khó của `none`."""
    steps = steps or config.T
    phase = np.linspace(0.0, WAVE_CYCLES * 2 * np.pi, steps)
    offsets = WAVE_PALMS * PALM_PX * np.sin(phase)
    return np.stack([hand(center=(CENTER[0] + dx, CENTER[1]))
                     for dx in offsets])
