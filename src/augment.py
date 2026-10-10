"""Tăng cường dữ liệu — Phase 4. Mỗi phép trả lời một câu hỏi: **biến đổi này
có làm đổi lớp không?**

| Phép | Tham số | Đổi nhãn? |
|---|---|---|
| Lật ngang | — | **Có** với cặp vuốt, **không** với cặp zoom |
| Co giãn đổi dần | 1 → 1 ± ``AUG_SCALE_RAMP`` | Không |
| Xoay nhẹ | ± ``AUG_ROTATE_DEG`` | Không |
| Co giãn thời gian | ``AUG_TIME_WARP`` | Không |
| Nhiễu Gauss | ``AUG_NOISE_SIGMA`` | Không |
| Xoá bước ngẫu nhiên | ``AUG_DROP_STEPS`` rồi ``fill_short_gaps`` | Không |
| Bàn tay cứng — chỉ cặp vuốt, Phase 6 | ``AUG_RIGID_SHARE``, ``AUG_RIGID_KEEP`` | Không |

**Bàn tay cứng** (thêm 2026-10-09): quỹ đạo cổ tay giữ nguyên, sự đổi dáng tay
chỉ giữ lại một phần ngẫu nhiên — từ không còn gì (bàn tay cứng hẳn) tới đầy đủ
như IPN. Cú hất ``Throw`` của IPN luôn mở bàn tay trong lúc hất, nên rừng ngẫu
nhiên học rằng không đổi dáng tay thì không phải vuốt, và bỏ qua cú vuốt kiểu
thông thường (bàn tay mở sẵn lướt ngang). Phép này dạy điều ngược lại: vuốt là
cổ tay đi ngang đủ nhanh và đủ xa, dáng tay không quyết định. Chỉ dùng bản cứng
hẳn thì không đủ: mô hình học hai "đảo" — cứng hẳn, hoặc đổi dáng như IPN — và
bỏ qua khoảng giữa, đúng chỗ cú vuốt thật nằm. Cái giá là tay chỉ trỏ cũng là
một bàn tay gần như cứng đang di chuyển; mức dùng được chọn trên val bằng
``scripts/sweep_rigid.py`` (``results/phase6/notes.md`` mục 8).

**Đầu vào là cửa sổ ĐÃ chuẩn hoá** (gốc tại cổ tay frame đầu, đơn vị lòng bàn
tay — đúng thứ ``windows.npz`` lưu), và **kết quả phải đi qua
``normalize_window`` lần nữa**. Luật 5 đặt tăng cường trước chuẩn hoá; cách làm
này tương đương vì ``normalize_window`` của một cửa sổ đã chuẩn hoá là phép đồng
nhất, và lật, xoay, co giãn thời gian, vá lỗ đều giao hoán với phép dời và
co giãn đều mà chuẩn hoá thực hiện. Nhiễu và co giãn đổi dần thì phải đo bằng
đơn vị lòng bàn tay — ``AUG_NOISE_SIGMA`` được ước lượng SAU chuẩn hoá.

**Co giãn đều bị bỏ:** nhân mọi điểm với cùng một hệ số rồi chuẩn hoá thì hệ số
đó bị chia mất. Thay bằng co giãn đổi dần dọc cửa sổ — mô phỏng tay tiến hoặc
lùi so với camera, thứ chuẩn hoá theo frame đầu không khử được.

Mọi phép không sửa mảng đầu vào và giữ bước đầu hữu hạn, để ``normalize_window``
luôn chạy được.
"""

import numpy as np

from src import config
from src.preprocess import fill_short_gaps, normalize_window

_SWAP = {"swipe_left": "swipe_right", "swipe_right": "swipe_left"}
#: Lớp sau khi lật ngang, theo chỉ số trong ``config.CLASSES``.
FLIP_LABEL = {i: config.CLASSES.index(_SWAP.get(name, name))
              for i, name in enumerate(config.CLASSES)}
#: Chỉ số hai lớp vuốt — những lớp duy nhất có bản bàn tay cứng.
SWIPE_LABELS = tuple(config.CLASSES.index(name) for name in _SWAP)


def flip_horizontal(win, label):
    """Lật ngang quanh cổ tay frame đầu: ``x → -x``.

    Returns:
        ``(cửa sổ mới, nhãn mới)`` — cặp vuốt đổi nhãn cho nhau, zoom và
        ``none`` giữ nguyên. Không cần hoán đổi chỉ số điểm mốc: 21 điểm của
        một bàn tay không có cặp trái — phải.
    """
    out = np.array(win, dtype=np.float64, copy=True)
    out[..., 0] = -out[..., 0]
    return out, FLIP_LABEL[int(label)]


def rotate(win, degrees):
    """Xoay quanh cổ tay frame đầu một góc ``degrees`` trong mặt phẳng ảnh."""
    theta = np.deg2rad(degrees)
    c, s = np.cos(theta), np.sin(theta)
    matrix = np.array([[c, -s], [s, c]])
    return np.asarray(win, dtype=np.float64) @ matrix.T


def scale_ramp(win, end_scale):
    """Co giãn đổi dần: hệ số đi từ 1 ở bước đầu tới ``end_scale`` ở bước cuối,
    quanh cổ tay frame đầu."""
    win = np.asarray(win, dtype=np.float64)
    factors = np.linspace(1.0, end_scale, win.shape[0])
    return win * factors[:, None, None]


def time_warp(win, factor):
    """Co giãn thời gian, neo ở bước đầu.

    Bước ``i`` mới lấy nội suy tuyến tính tại bước cũ ``i * factor``.
    ``factor > 1``: cử chỉ nhanh hơn — phần vượt quá cuối cửa sổ giữ bằng bước
    cuối, vì cửa sổ không có dữ liệu sau nó. ``factor < 1``: chậm hơn — phần
    cuối của cửa sổ cũ bị cắt. Nội suy cạnh một bước NaN cho NaN: không bịa dữ
    liệu qua chỗ mất tay.
    """
    win = np.asarray(win, dtype=np.float64)
    n = win.shape[0]
    tau = np.minimum(np.arange(n) * factor, n - 1)
    left = np.floor(tau).astype(int)
    right = np.minimum(left + 1, n - 1)
    alpha = (tau - left)[:, None, None]
    blend = (1 - alpha) * win[left] + alpha * win[right]
    # Trúng đúng một bước cũ (alpha = 0) thì lấy thẳng bước đó: 0 × NaN vẫn là
    # NaN, nên công thức nội suy làm cả bước đầu thành NaN khi bước 1 mất tay.
    return np.where(alpha > 0, blend, win[left])


def add_noise(win, sigma, rng):
    """Nhiễu Gauss độc lập trên mọi toạ độ, ``sigma`` theo đơn vị lòng bàn tay."""
    win = np.asarray(win, dtype=np.float64)
    return win + rng.normal(0.0, sigma, size=win.shape)


def drop_steps(win, start, length):
    """Xoá ``length`` bước liền nhau từ ``start`` rồi vá bằng ``fill_short_gaps``
    — mô phỏng MediaPipe mất tay vài frame."""
    out = np.array(win, dtype=np.float64, copy=True)
    out[start:start + length] = np.nan
    return fill_short_gaps(out)


def shape_scaled(win, k, ref=0):
    """Giữ ``k`` phần sự đổi dáng tay so với dáng của bước ``ref``; quỹ đạo cổ
    tay giữ nguyên. ``k = 1`` là phép đồng nhất, ``k = 0`` là bàn tay cứng.

    Dáng tay của một bước là 21 điểm trừ đi cổ tay của chính bước đó. Bước mất
    tay (NaN) vẫn là NaN.
    """
    win = np.asarray(win, dtype=np.float64)
    wrist = win[:, config.WRIST:config.WRIST + 1]
    pose = win - wrist
    return wrist + pose[ref][None] + k * (pose - pose[ref][None])


def rigid_hand(win, ref=0):
    """Bàn tay cứng: mọi bước dùng dáng tay của bước ``ref``, đặt tại vị trí cổ
    tay của chính bước đó — quỹ đạo, tốc độ, quãng dời cổ tay giữ y nguyên."""
    return shape_scaled(win, 0.0, ref)


def usable_steps(win):
    """Chỉ số các bước có lòng bàn tay dùng làm đơn vị được: không ngắn hơn
    ``NORM_MIN_PALM_RATIO`` lần trung vị của cửa sổ — đúng tiêu chí mà
    ``normalize_window`` áp cho bước đầu. Bước mất tay bị loại."""
    win = np.asarray(win, dtype=np.float64)
    palms = np.linalg.norm(win[:, config.MIDDLE_MCP] - win[:, config.WRIST], axis=-1)
    with np.errstate(invalid="ignore"):     # NaN so với ngưỡng ra False: bị loại
        return np.flatnonzero(palms >= config.NORM_MIN_PALM_RATIO * np.nanmedian(palms))


def rigid_swipes(X, y, split, rng, share=None, keep=None, sigma=None):
    """Bản bàn tay cứng của các cửa sổ vuốt — CHỈ cho tập train (luật 9).

    Mỗi cửa sổ vuốt cho ``⌊share⌋`` bản, cộng một bản nữa ở một phần
    ``share − ⌊share⌋`` số cửa sổ chọn ngẫu nhiên. Mỗi bản:

    - giữ ``k`` phần sự đổi dáng tay của cú vuốt gốc (:func:`shape_scaled`),
      ``k`` đều trong ``keep``: từ cứng hẳn tới đổi dáng như IPN, vì cú vuốt
      thật của người dùng nằm đâu đó ở giữa;
    - lấy dáng tay của một bước chọn ngẫu nhiên làm mốc — từ chụm lúc đầu cú
      hất tới xòe hẳn giữa cú hất;
    - cộng nhiễu ``sigma`` (bàn tay cứng thật vẫn rung), rồi qua
      ``normalize_window``. Nhãn giữ nguyên.

    Bước làm mốc phải có lòng bàn tay dùng làm đơn vị được (:func:`usable_steps`):
    giữa cú hất bàn tay hay nghiêng cạnh về phía camera, lòng bàn tay chỉ còn
    vài phần trăm, và dáng tay của bước đó không phải một bàn tay thật. Bản nào
    ``normalize_window`` vẫn từ chối thì bỏ — hiếm, khi dáng nội suy giữa hai
    dáng tay quay ngược nhau làm lòng bàn tay bước đầu gần bằng 0.

    Args:
        X: ``(N, T, 21, 2)`` cửa sổ đã chuẩn hoá.
        y: ``(N,)`` chỉ số lớp.
        split: phải là ``"train"``.
        rng: ``np.random.Generator``.
        share: số bản trên mỗi cửa sổ vuốt; ``None`` thì đọc ``AUG_RIGID_SHARE``.
        keep: khoảng ``(thấp, cao)`` của ``k``; ``None`` thì đọc
            ``AUG_RIGID_KEEP``. ``(0, 0)`` là cứng hoàn toàn.
        sigma: độ lệch chuẩn của nhiễu; ``None`` thì đọc ``AUG_NOISE_SIGMA``
            qua ``require_measured``.

    Returns:
        ``(X_rigid float32, y_rigid int64, source int64)`` — ``source`` là chỉ
        số trong ``X`` của cửa sổ gốc, để lấy ``presence`` của nó. Mảng MỚI,
        ``X`` và ``y`` không đổi.

    Raises:
        ValueError: ``split`` không phải ``"train"``.
    """
    if split != "train":
        raise ValueError(
            f"Tăng cường chỉ cho tập train, không cho '{split}' (luật 9).")
    share = config.AUG_RIGID_SHARE if share is None else share
    low, high = config.AUG_RIGID_KEEP if keep is None else keep
    if sigma is None:
        sigma = config.require_measured("AUG_NOISE_SIGMA")

    y = np.asarray(y)
    swipes = np.flatnonzero(np.isin(y, SWIPE_LABELS))
    whole, part = divmod(float(share), 1.0)
    source = np.concatenate([
        np.repeat(swipes, int(whole)),
        rng.choice(swipes, size=int(round(part * swipes.size)), replace=False)
    ]).astype(np.int64)

    out, made = [], []
    for i in source:
        win = np.asarray(X[i], dtype=np.float64)
        k = rng.uniform(low, high) if high > low else low
        changed = shape_scaled(win, k, int(rng.choice(usable_steps(win))))
        try:
            out.append(normalize_window(add_noise(changed, sigma, rng)))
        except ValueError:
            continue
        made.append(i)
    made = np.asarray(made, dtype=np.int64)
    X_rigid = np.asarray(out, dtype=np.float32).reshape(-1, *np.shape(X)[1:])
    return X_rigid, y[made].astype(np.int64), made


def augment(win, label, rng, sigma=None):
    """Một bản tăng cường ngẫu nhiên của một cửa sổ đã chuẩn hoá.

    Args:
        win: ``(T, 21, 2)`` cửa sổ đã chuẩn hoá.
        label: chỉ số lớp.
        rng: ``np.random.Generator``.
        sigma: độ lệch chuẩn của nhiễu; ``None`` thì đọc
            ``AUG_NOISE_SIGMA`` qua ``require_measured``.

    Returns:
        ``(cửa sổ, nhãn)`` — cửa sổ ĐÃ chuẩn hoá lại.
    """
    if sigma is None:
        sigma = config.require_measured("AUG_NOISE_SIGMA")

    out = np.asarray(win, dtype=np.float64)
    if rng.random() < config.AUG_FLIP_P:
        out, label = flip_horizontal(out, label)
    out = rotate(out, rng.uniform(-config.AUG_ROTATE_DEG, config.AUG_ROTATE_DEG))
    out = scale_ramp(out, 1.0 + rng.uniform(-config.AUG_SCALE_RAMP,
                                            config.AUG_SCALE_RAMP))
    out = time_warp(out, rng.uniform(*config.AUG_TIME_WARP))
    out = add_noise(out, sigma, rng)
    if rng.random() < config.AUG_DROP_P:
        lo, hi = config.AUG_DROP_STEPS
        length = int(rng.integers(lo, hi + 1))
        # tránh bước đầu (gốc toạ độ) và bước cuối (fill_short_gaps không vá
        # được lỗ chạm mép)
        start = int(rng.integers(1, out.shape[0] - length))
        out = drop_steps(out, start, length)
    return normalize_window(out), label


def augment_windows(X, y, split, rng, sigma=None):
    """Tăng cường cả một lô — CHỈ cho tập train (luật 9).

    Raises:
        ValueError: ``split`` không phải ``"train"``. Tăng cường val hay test
            là làm sai con số đánh giá, nên chặn ngay ở đây.

    Returns:
        ``(X_aug float32, y_aug int64)`` — mảng MỚI, ``X`` và ``y`` không đổi.
    """
    if split != "train":
        raise ValueError(
            f"Tăng cường chỉ cho tập train, không cho '{split}' (luật 9).")
    pairs = [augment(win, label, rng, sigma) for win, label in zip(X, y)]
    X_aug = np.stack([p[0] for p in pairs]).astype(np.float32)
    y_aug = np.array([p[1] for p in pairs], dtype=np.int64)
    return X_aug, y_aug
