# Tầng 3 — Biểu diễn khung xương

> **Câu hỏi mở đầu:** Bạn đã có 33 cặp tọa độ mỗi frame. Tại sao không đưa
> thẳng chúng vào mô hình và xong việc?

Vì mô hình sẽ học sai thứ. Không phải "học kém" — mà **học đúng một mối tương
quan có thật trong dữ liệu của bạn nhưng vô nghĩa ngoài đời**.

Tầng này ngắn về mặt code — hàm chuẩn hóa chỉ vài dòng — nhưng nó quyết định
toàn bộ chất lượng của mọi thứ phía sau. Nếu bạn chỉ có thời gian làm kỹ một
tầng, hãy chọn tầng này.

---

## 1. Vấn đề: mô hình học vị trí thay vì học hành động

### Thí nghiệm tưởng tượng

Bạn quay dữ liệu trong phòng mình. Vì thói quen, khi diễn "ngã" bạn luôn ngã về
phía tấm đệm bên trái khung hình. Khi diễn "vẫy tay" bạn đứng giữa.

Bạn đưa tọa độ pixel thô vào mô hình. Nó đạt 97% trên tập kiểm thử. Tuyệt vời.

Hôm bảo vệ, bạn dựng camera ở góc khác trong phòng hội đồng. Hệ thống báo "ngã"
liên tục dù bạn chỉ đang đứng.

**Chuyện gì đã xảy ra?** Mô hình phát hiện ra một quy luật hoàn toàn có thật
trong dữ liệu huấn luyện: *khung xương ở nửa trái màn hình → nhãn "ngã"*. Quy
luật đó đúng 97% trên dữ liệu của bạn. Nó chỉ không liên quan gì tới hành động
ngã.

Đây là dạng **tương quan giả** (*spurious correlation*), và nó là một trong
những cách thất bại phổ biến nhất của học máy ứng dụng. Mô hình không "hiểu"
gì — nó tìm đường ngắn nhất từ đầu vào tới nhãn. Nếu vị trí trên màn hình là
đường ngắn nhất, nó sẽ đi đường đó.

### Cách chữa

Nếu ta **loại bỏ thông tin vị trí khỏi đầu vào**, mô hình không còn cách nào để
dùng nó. Nó buộc phải tìm tín hiệu thật.

Đó chính là chuẩn hóa.

---

## 2. Bất biến — khung khái niệm

### Định nghĩa

Một biểu diễn **bất biến** với một phép biến đổi nghĩa là: áp phép biến đổi đó
lên đầu vào thì biểu diễn **không đổi**.

Ta muốn biểu diễn khung xương bất biến với những thứ **không mang thông tin về
hành động**:

| Biến thiên | Có mang thông tin không? | Xử lý |
|---|---|---|
| Vị trí trong khung hình | Không | Loại bỏ — chuẩn hóa tịnh tiến |
| Khoảng cách tới camera | Không | Loại bỏ — chuẩn hóa tỉ lệ |
| Chiều cao người diễn | Không | Loại bỏ — cùng phép chuẩn hóa tỉ lệ |
| Độ phân giải camera | Không | Loại bỏ |
| Góc nghiêng thân | **CÓ** | **Giữ lại!** |
| Tốc độ chuyển động | **CÓ** | **Giữ lại!** |
| Hướng thời gian | **CÓ** | **Giữ lại!** |

### Nguyên tắc đánh đổi

> Mỗi phép chuẩn hóa vứt bỏ thông tin. Vứt bỏ thông tin nhiễu là tốt. Vứt bỏ
> thông tin có ích là hỏng. Bạn phải quyết định từng cái, dựa trên bài toán cụ
> thể.

Ba hàng cuối bảng trên là chỗ nhiều người làm sai. Cụ thể:

- Chuẩn hóa xoay để "khung xương luôn thẳng đứng" nghe rất hợp lý — nhưng nó
  xóa mất chính tín hiệu phân biệt người ngã với người đứng.
- Chuẩn hóa mỗi frame theo `min-max` của riêng frame đó sẽ xóa mất chuyển động
  giữa các frame.

Ta sẽ quay lại cả hai.

---

## 3. Chuẩn hóa tịnh tiến — dời gốc tọa độ

### Cách làm

Chọn một điểm trên cơ thể làm gốc, trừ nó khỏi mọi khớp:

```python
hip = (pts[23] + pts[24]) / 2     # trung điểm hai hông
centered = pts - hip              # broadcasting: trừ khỏi mọi khớp
```

Sau bước này, trung điểm hông luôn ở `(0, 0)`. Mọi khớp khác được mô tả bằng vị
trí **tương đối so với hông**. Người đứng ở đâu trong khung hình cũng cho cùng
kết quả.

### Vì sao chọn hông làm gốc

Bốn lý do, xếp theo tầm quan trọng:

1. **Ổn định nhất.** Hông là điểm gần trọng tâm cơ thể và ít chuyển động độc
   lập nhất. Cổ tay dao động mạnh, đầu quay nghiêng, nhưng hông thì tương đối
   yên.
2. **Ít bị che khuất.** Trừ khi ngồi sau bàn, hông gần như luôn nhìn thấy được.
   Chọn cổ tay làm gốc thì mọi tọa độ hỏng ngay khi tay đưa ra sau lưng.
3. **Trung điểm nên ít nhiễu hơn.** Lấy trung bình hai điểm làm giảm nhiễu ngẫu
   nhiên khoảng √2 lần so với dùng một điểm.
4. **Nhất quán với MediaPipe.** BlazePose tự nó cũng dùng trung điểm hông làm
   tâm khi cắt và xoay vùng ảnh. Ta chỉ làm lại điều tương tự ở mức tọa độ.

### Vì sao không dùng những lựa chọn khác

| Lựa chọn | Vấn đề |
|---|---|
| Mũi (điểm 0) | Đầu quay và cúi độc lập với thân. Gật đầu sẽ làm cả khung xương "dịch chuyển" |
| Trung điểm vai | Được, nhưng vai nhô lên hạ xuống khi vẫy tay hoặc nhún vai |
| Trọng tâm mọi khớp | Nghe hợp lý nhưng gây rắc rối: khi giơ tay lên, trọng tâm dịch lên, làm **cả khung xương** có vẻ dịch xuống. Chuyển động của một bộ phận làm nhiễu toàn bộ biểu diễn |
| Góc dưới trái khung hình | Đây chính là không chuẩn hóa gì cả |

---

## 4. Chuẩn hóa tỉ lệ — chia cho kích thước cơ thể

### Vấn đề còn lại

Sau khi dời gốc, vẫn còn hai nguồn biến thiên:

- Đứng gần camera → khung xương lớn; đứng xa → khung xương nhỏ
- Người cao 1m80 → khung xương lớn; người cao 1m55 → nhỏ

Cả hai đều không liên quan tới hành động. Cách chữa: chia mọi tọa độ cho một
**đại lượng tỉ lệ với kích thước cơ thể trong ảnh**.

### Chọn đại lượng nào

Đề cương dùng khoảng cách từ trung điểm hông tới trung điểm vai — gọi là **độ
dài thân**:

```python
shoulder = (pts[11] + pts[12]) / 2
scale = np.linalg.norm(shoulder - hip)
normalized = (pts - hip) / scale
```

So sánh các lựa chọn:

| Đại lượng | Ưu | Nhược |
|---|---|---|
| **Hông → vai (thân)** | Ổn định nhất — thân là khối cứng, gần như không đổi độ dài dù người làm gì | Ngắn lại khi người nghiêng người về phía camera (rút ngắn phối cảnh) |
| Chiều cao toàn thân (đầu → chân) | Thang lớn, ít nhiễu tương đối | **Hỏng khi ngồi** — chiều cao giảm nửa. Hỏng khi chân bị cắt khỏi khung hình |
| Chiều rộng vai | Là khối cứng | **Hỏng khi quay nghiêng** — vai bị rút ngắn về gần 0 |
| Đường chéo khung bao | Dễ tính | Đổi theo từng tư thế: giơ tay thì khung bao to ra |

Độ dài thân là lựa chọn tốt nhất trong số này, vì nó là đoạn giữ được độ dài
ổn định nhất qua các tư thế thường gặp.

### Cạm bẫy chia cho số gần 0

Nếu MediaPipe cho ra khung xương hỏng — chẳng hạn mọi khớp dồn về một điểm khi
mất dấu — thì `scale` gần 0 và phép chia cho ra những con số khổng lồ. Một
frame như thế lọt vào tập huấn luyện sẽ làm hỏng cả quá trình học, vì hàm mất
mát bị chi phối bởi một mẫu ngoại lai.

Luôn kiểm tra:

```python
if scale < 1e-6:
    return None        # khung xương hỏng — bỏ frame này
```

Đây chính là ba dòng `if scale < 1e-6: return None` trong đề cương. Nó không
phải chi tiết vụn vặt, nó là lớp phòng vệ thật.

### Kiểm chứng bằng mắt — bài tập tuần 4

Đề cương yêu cầu "kiểm chứng bằng mắt: đứng gần và đứng xa camera phải cho ra
tọa độ chuẩn hóa gần giống nhau". Cách làm cụ thể:

```python
# Đứng cách camera 1m, cùng một tư thế, in ra:
print(normalized[15])    # cổ tay trái, chuẩn hóa

# Lùi ra 3m, cùng tư thế, in lại. Hai kết quả phải gần bằng nhau.
```

Nếu chúng chênh nhau nhiều thì có ba khả năng: quên nhân `W, H` (xem tầng 2 mục
6.3), chọn sai điểm gốc, hoặc tư thế của bạn không thực sự giống nhau ở hai lần
đo.

**Bằng chứng này rất đáng đưa vào báo cáo.** Một bảng nhỏ hai cột — tọa độ pixel
thô ở hai khoảng cách, và tọa độ chuẩn hóa ở hai khoảng cách — chứng minh phép
chuẩn hóa của bạn thực sự hoạt động. Nó biến một dòng code thành một kết quả có
kiểm chứng.

---

## 5. Chuẩn hóa xoay — vì sao ĐỀ TÀI NÀY KHÔNG NÊN LÀM

Nhiều bài báo về nhận dạng hành động từ khung xương có bước chuẩn hóa xoay:
xoay khung xương sao cho trục hông→vai luôn thẳng đứng, và/hoặc trục vai
trái→vai phải luôn nằm ngang.

Nghe rất hợp lý: loại bỏ ảnh hưởng của việc camera đặt nghiêng.

**Nhưng với đồ án này, nó sẽ phá hủy hành động quan trọng nhất.**

Lý do: đặc trưng phân biệt rõ nhất của "ngã" là **thân người nằm ngang**. Nếu
bạn xoay mọi khung xương về thẳng đứng, một người đang nằm sẽ trông y hệt một
người đang đứng. Bạn vừa xóa đúng tín hiệu mình cần.

```
Trước chuẩn hóa xoay:          Sau chuẩn hóa xoay:

  đứng:  │                       đứng:  │
  ngã:   ───                     ngã:   │   ← không phân biệt được nữa
```

**Kết luận cho đồ án: không chuẩn hóa xoay. Giữ nguyên hướng thân.**

Đây là một ví dụ hoàn hảo của nguyên tắc ở mục 2: chuẩn hóa vứt bỏ thông tin,
và bạn phải biết mình đang vứt gì. Cùng một kỹ thuật, đúng cho bài toán này,
sai cho bài toán kia.

> **Điểm này rất đáng viết vào báo cáo.** Nêu rằng bạn đã cân nhắc chuẩn hóa
> xoay, giải thích vì sao từ chối nó, và chỉ ra hệ quả với lớp "ngã". Đây là
> dấu hiệu rõ nhất cho thấy bạn hiểu công cụ mình dùng chứ không chép công thức
> từ bài báo.

Ngoại lệ: nếu bạn muốn hệ thống chịu được camera đặt lệch, cách đúng **không
phải** chuẩn hóa xoay, mà là **tăng cường dữ liệu bằng cách xoay nhẹ ngẫu
nhiên** (±10–15°) khi huấn luyện. Cách này dạy mô hình chịu được lệch nhỏ mà
vẫn giữ phân biệt đứng/nằm.

---

## 6. Góc khớp — đặc trưng bất biến nhất

### Vì sao góc tốt

Góc ở một khớp — chẳng hạn góc gập của khuỷu tay — có tính chất rất đẹp: nó bất
biến với **cả ba** phép biến đổi cùng lúc.

- Tịnh tiến: dịch cả người, góc không đổi
- Tỉ lệ: phóng to cả người, góc không đổi
- Xoay: xoay cả người, góc **cũng không đổi**

Nói cách khác, góc khớp cho bạn miễn phí thứ mà chuẩn hóa tọa độ phải làm bằng
tay. Và nó có ý nghĩa vật lý trực tiếp: "gối gập 90°" là một mô tả tư thế mà
con người hiểu được ngay.

### Công thức

Góc tại khớp B, tạo bởi ba điểm A–B–C (ví dụ vai–khuỷu–cổ tay):

```
  A
   \
    \  θ
     B────C
```

Tạo hai vector từ B, rồi dùng tích vô hướng:

```python
def joint_angle(A, B, C):
    """Góc tại B, tính bằng độ."""
    v1 = A - B
    v2 = C - B
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    cos = np.clip(cos, -1.0, 1.0)      # BẮT BUỘC — xem giải thích bên dưới
    return np.degrees(np.arccos(cos))
```

Cơ sở toán: `u · v = |u| |v| cos θ`, nên `cos θ = (u · v) / (|u| |v|)`.

**Vì sao bắt buộc `np.clip`:** về mặt toán học, `cos` luôn nằm trong `[-1, 1]`.
Nhưng số thực dấu phẩy động có sai số làm tròn, nên kết quả thực tế có thể ra
`1.0000000002`. `np.arccos` của giá trị đó trả về `nan`, và một `nan` sẽ lan ra
toàn bộ tính toán phía sau — âm thầm, không báo lỗi, cho tới khi mô hình không
huấn luyện được và bạn không hiểu tại sao. Một dòng `clip` phòng được cả buổi
gỡ lỗi.

**Lưu ý:** góc khớp phải tính trên tọa độ đã nhân `W, H` (đơn vị pixel hoặc
tọa độ chuẩn hóa đúng hình học). Tính trên `(lm.x, lm.y)` thô sẽ ra góc méo —
xem tầng 2 mục 6.3.

### Nhược điểm của góc

Góc **vứt bỏ hướng tuyệt đối**. Một cánh tay giơ lên trời và một cánh tay chỉ
xuống đất có thể cho cùng góc khuỷu tay 180°.

Nên đừng chỉ dùng góc. Kết hợp góc với tọa độ chuẩn hóa: góc cho bạn tư thế
tương đối bền vững, tọa độ cho bạn hướng trong không gian.

### Nên tính góc nào

Cho sáu hành động của đồ án:

| Góc | Ba điểm | Phân biệt được gì |
|---|---|---|
| Khuỷu tay trái/phải | 11–13–15 / 12–14–16 | Vẫy tay so với các hành động khác |
| Đầu gối trái/phải | 23–25–27 / 24–26–28 | Đứng (duỗi) so với ngồi (gập ~90°) |
| Hông trái/phải | 11–23–25 / 12–24–26 | Đứng (~180°) so với ngồi (~90°) |
| Vai trái/phải | 13–11–23 / 14–12–24 | Tay giơ cao hay buông xuôi |

Tám góc. Cộng với góc nghiêng của thân so với phương thẳng đứng — góc này
không phải góc khớp mà là góc tuyệt đối, và nó là **đặc trưng quan trọng nhất
cho lớp "ngã"**:

```python
trunk = shoulder - hip
tilt = np.degrees(np.arctan2(trunk[0], -trunk[1]))
# 0° = thẳng đứng, ±90° = nằm ngang
# Chú ý dấu trừ: trục y ảnh hướng xuống
```

---

## 7. Vận tốc — đưa thời gian vào đặc trưng

### Sai phân bậc một

Vận tốc của một khớp là thay đổi vị trí giữa hai frame liên tiếp:

```python
vel = np.diff(seq, axis=0)      # seq: (T, J, 2) → vel: (T-1, J, 2)
speed = np.linalg.norm(vel, axis=-1)    # độ lớn, bỏ hướng: (T-1, J)
```

Vì sao cần: hai hành động có thể đi qua **cùng những tư thế** nhưng ở tốc độ
khác nhau. "Ngồi xuống" và "ngã" chia sẻ phần lớn quỹ đạo — hông đi xuống, thân
cúi — nhưng ngã nhanh hơn nhiều. Nếu đặc trưng của bạn chỉ mô tả tư thế, mô
hình không có cách nào tách hai lớp này.

### Đơn vị

Sau khi chuẩn hóa, vị trí có đơn vị "độ dài thân". Nên vận tốc có đơn vị **độ
dài thân trên frame**. Muốn đổi sang "độ dài thân trên giây" thì nhân với FPS.

Nên làm rõ điều này trong báo cáo, vì nó gắn với một giới hạn thật: **nếu FPS
lúc chạy demo khác FPS lúc quay dữ liệu thì các đặc trưng vận tốc bị sai thang.**
Hoặc là bạn giữ FPS cố định, hoặc là bạn chia cho khoảng thời gian thật giữa
hai frame.

### Nhiễu và làm mượt

Sai phân **khuếch đại nhiễu**. Nếu vị trí có nhiễu ±0.01 thì hiệu của hai vị
trí có nhiễu tới ±0.02, trong khi tín hiệu thật (chuyển dịch giữa hai frame ở
30 FPS) cũng chỉ cỡ đó. Tỉ số tín hiệu trên nhiễu tệ đi rõ rệt.

Hai cách chữa:

**Làm mượt trước khi lấy sai phân.** Trung bình trượt trên 3–5 frame:

```python
from scipy.ndimage import uniform_filter1d
smooth = uniform_filter1d(seq, size=5, axis=0)
vel = np.diff(smooth, axis=0)
```

**Lấy sai phân trên khoảng dài hơn.** Thay vì `pos[t] − pos[t−1]`, dùng
`pos[t] − pos[t−3]`. Ít nhiễu hơn, nhưng phản ứng chậm hơn.

Cái giá của làm mượt là **độ trễ**: cửa sổ 5 frame thì tín hiệu chậm khoảng 2
frame ≈ 67 ms. Với hệ thống thời gian thực đây là chi phí thật, cần nêu ra.

Nếu muốn tinh vi hơn, có thể dùng **trung bình trượt mũ** (EMA) — chỉ cần nhớ
một giá trị, không cần đệm:

```python
smoothed = alpha * new + (1 - alpha) * smoothed    # alpha ≈ 0.3–0.5
```

### Gia tốc

Sai phân bậc hai. Về lý thuyết nó phân biệt tốt "ngã" (gia tốc lớn, đột ngột)
với "ngồi xuống" (gia tốc nhỏ, có kiểm soát).

Thực tế: gia tốc khuếch đại nhiễu **hai lần**, nên thường gần như toàn nhiễu
với dữ liệu webcam. Thử nếu còn thời gian, nhưng đừng kỳ vọng nhiều, và nhớ
làm mượt kỹ trước.

---

## 8. Đặc trưng có dấu và hướng thời gian

Đây là ý tưởng then chốt cho cặp hành động khó nhất của đồ án.

### Vấn đề

"Ngồi xuống" và "đứng dậy" đi qua **đúng cùng những tư thế**, chỉ khác thứ tự.
Nếu đặc trưng của bạn chỉ gồm các đại lượng như:

- trung bình góc gối trong cửa sổ
- độ lệch chuẩn của chiều cao hông
- tốc độ trung bình của cổ tay

thì cả ba đều **giống hệt nhau** cho hai hành động. Bạn đã vứt bỏ hướng thời
gian.

### Vì sao trung bình và độ lệch chuẩn mất hướng

Cả hai đều **đối xứng theo thời gian**: đảo ngược chuỗi thì giá trị không đổi.

```
Ngồi xuống, chiều cao hông:  [1.0, 0.9, 0.7, 0.5, 0.4]
Đứng dậy,   chiều cao hông:  [0.4, 0.5, 0.7, 0.9, 1.0]

trung bình:  0.70  và  0.70      ← giống nhau
độ lệch chuẩn: 0.24 và 0.24      ← giống nhau
```

Còn tốc độ thì mất dấu vì `np.linalg.norm` lấy độ lớn.

### Giải pháp: đặc trưng có dấu

Thêm những đại lượng **đảo dấu khi đảo chiều thời gian**:

```python
delta_hip_y   = hip_y[-1]  - hip_y[0]       # dương = đi xuống (trục y hướng xuống)
delta_knee    = knee[-1]   - knee[0]        # dương = gối duỗi ra
mean_vel_y    = np.mean(np.diff(hip_y))     # vận tốc trung bình CÓ DẤU
```

Với ví dụ trên:

```
Ngồi xuống:  delta_hip_y = 0.4 − 1.0 = −0.6   ...  chờ đã
```

Cẩn thận với dấu! Ở đây tôi viết "chiều cao hông" theo trực giác (cao = số lớn).
Nhưng tọa độ y của ảnh **hướng xuống**, nên `hip_y` lớn nghĩa là hông **thấp**.
Với `hip_y` thật từ MediaPipe:

```
Ngồi xuống, hip_y:  [0.4, 0.5, 0.7, 0.9, 1.0]  →  delta = +0.6
Đứng dậy,   hip_y:  [1.0, 0.9, 0.7, 0.5, 0.4]  →  delta = −0.6
```

Một con số duy nhất, tách hoàn toàn hai lớp. Đây là toàn bộ nội dung của dòng
"Độ thay đổi chiều cao hông từ đầu tới cuối cửa sổ — **có dấu**" trong đề cương.

Viết chú thích rõ ràng trong code, vì dấu này ngược trực giác và bạn sẽ tự làm
mình rối nếu không ghi:

```python
# LƯU Ý: trục y của ảnh hướng XUỐNG.
# delta_hip_y > 0  ⇒  hông đi xuống  ⇒  đang ngồi xuống hoặc ngã
# delta_hip_y < 0  ⇒  hông đi lên    ⇒  đang đứng dậy
delta_hip_y = hip_y[-1] - hip_y[0]
```

### Bài học tổng quát

> Nếu hai lớp chỉ khác nhau ở **thứ tự** các sự kiện, thì mọi đặc trưng đối
> xứng theo thời gian đều vô dụng để phân biệt chúng. Phải có ít nhất một đặc
> trưng bất đối xứng.

LSTM ở tầng 4 **về nguyên tắc** tự học được điều này từ chuỗi thô, vì nó xử lý
các bước theo đúng thứ tự. Nhưng "về nguyên tắc" không đảm bảo "trên thực tế
với vài nghìn mẫu". Có sẵn đặc trưng có dấu là một bảo hiểm rẻ.

---

## 9. Chọn khớp — vì sao bỏ 10 điểm mặt

Đề cương dùng `n_joints=23`, tức bỏ 10 điểm mặt (chỉ số 0–10). Ba lý do:

**1. Không mang thông tin về hành động.** Bốn góc mắt, hai tai, hai khóe miệng
— không cái nào phân biệt được vẫy tay với ngồi xuống. Hành động toàn thân được
mã hóa bởi thân, tay, chân.

**2. Nhiễu.** Các điểm mặt gần nhau, chỉ cách nhau vài pixel khi người đứng xa.
Nhiễu vị trí tương đối vì thế lớn. Đầu lại quay nghiêng độc lập với thân, thêm
một nguồn biến thiên nữa.

**3. Giảm số tham số.** Đây là lý do quan trọng nhất với dữ liệu ít.

Tính cụ thể: lớp LSTM đầu tiên có số tham số tỉ lệ với kích thước đầu vào.

```
33 khớp × 2 = 66 chiều vào
23 khớp × 2 = 46 chiều vào   →  giảm 30% tham số ở lớp đầu
```

Với vài nghìn mẫu, mỗi tham số bỏ đi là một cơ hội quá khớp bị loại trừ.

### Có nên giữ điểm mũi không

Đề cương giữ nó ngầm (`23 = 33 − 10`, tức bỏ đúng chỉ số 0–10... nhưng như thế
là bỏ cả mũi và còn 22). Hãy tự quyết định rõ ràng và **ghi lại lựa chọn**:

```python
# Phương án A: bỏ toàn bộ 0–10, giữ 11–32  →  22 khớp
BODY_A = list(range(11, 33))

# Phương án B: giữ mũi làm chỉ báo hướng đầu, bỏ 1–10  →  23 khớp
BODY_B = [0] + list(range(11, 33))
```

Phương án B cho đúng 23 như đề cương và có lý do hợp lệ: mũi là điểm mặt duy
nhất mang thông tin toàn thân đáng kể — nó cho biết đầu hướng lên hay cúi
xuống, hữu ích để phân biệt tư thế nằm sau khi ngã.

Điều quan trọng không phải chọn A hay B, mà là **chọn có ý thức và nêu lý do
trong báo cáo**, đồng thời dùng nhất quán ở mọi nơi trong code. Một hằng số ở
một chỗ duy nhất:

```python
# constants.py
BODY_JOINTS = [0] + list(range(11, 33))   # 23 khớp
N_JOINTS = len(BODY_JOINTS)
```

Định nghĩa hai lần ở hai file là công thức chắc chắn cho lỗi `IndexError` và tệ
hơn là lỗi im lặng khi số khớp trùng khớp nhưng thứ tự khác.

### Có nên bỏ các điểm bàn tay và bàn chân

Điểm 17–22 (ngón tay) và 29–32 (gót, mũi bàn chân) cũng đáng cân nhắc bỏ:
chúng nhiễu và đóng góp ít cho sáu hành động này. Bỏ hết thì còn 13 khớp.

Đây là một **thí nghiệm tốt cho chương 5**: so sánh độ chính xác với 33, 23 và
13 khớp. Ba hàng bảng, tốn nửa tiếng chạy, và nó cho thấy bạn kiểm chứng quyết
định thiết kế thay vì mặc định.

---

## 10. Xử lý dữ liệu thiếu và hỏng

Khung xương từ webcam không bao giờ sạch. Ba tình huống và cách xử lý:

### Không phát hiện được người

`result.pose_landmarks` rỗng. Xảy ra khi người ra khỏi khung hình, quá tối,
hoặc bị che.

```python
if not result.pose_landmarks:
    # đánh dấu frame này là thiếu
```

### Khớp có `visibility` thấp

Mô hình vẫn đoán tọa độ nhưng không đáng tin.

```python
MIN_VIS = 0.5
mask = np.array([lm.visibility >= MIN_VIS for lm in landmarks])
```

### Ba cách xử lý

| Cách | Khi nào dùng | Rủi ro |
|---|---|---|
| **Bỏ frame** | Khi trích dữ liệu huấn luyện | Làm đứt chuỗi thời gian — chuỗi còn lại không còn cách đều nhau |
| **Nội suy từ frame lân cận** | Khoảng trống ngắn (1–3 frame) | Tạo dữ liệu giả; đừng nội suy khoảng trống dài |
| **Giữ giá trị frame trước** | Khi chạy demo thời gian thực | Đơn giản, nhưng khung xương "đóng băng" nếu mất dấu lâu |

**Điểm tinh tế quan trọng:** nếu bạn bỏ frame giữa chuỗi, các frame còn lại
không còn cách đều nhau về thời gian nữa. Vận tốc tính bằng `np.diff` sẽ sai vì
nó giả định khoảng cách đều. Với khoảng trống ngắn thì nội suy tốt hơn bỏ:

```python
import pandas as pd
df = pd.DataFrame(seq.reshape(len(seq), -1))
df = df.interpolate(limit=3, limit_direction="both")   # tối đa 3 frame
```

Với khoảng trống dài (trên ~5 frame ≈ 0.17 giây), hãy **cắt chuỗi thành hai
đoạn** thay vì nội suy. Nội suy qua một khoảng dài là bịa dữ liệu.

**Nên báo cáo tỉ lệ frame bị bỏ.** Một dòng trong chương Dữ liệu: "3,2% frame
bị loại do không phát hiện được khung xương hoặc `visibility` dưới ngưỡng". Con
số này cho thấy bạn kiểm soát chất lượng dữ liệu, và nó là thông tin thật mà
người đọc cần để đánh giá kết quả.

---

## 11. Tăng cường dữ liệu ở mức khung xương

Dữ liệu tự quay thì ít. Tăng cường tạo thêm mẫu từ mẫu có sẵn, giúp chống quá
khớp. Ưu điểm lớn của việc làm ở mức khung xương thay vì mức ảnh: cực nhanh,
chỉ là vài phép toán trên mảng nhỏ.

### Lật ngang — cẩn thận, có bẫy

```python
FLIP = 1 - x       # lật tọa độ x quanh trục dọc
```

**Nhưng chưa xong.** Sau khi lật, vai trái của người bây giờ nằm ở phía phải
ảnh. Nếu bạn không hoán đổi chỉ số khớp trái ↔ phải, khung xương sẽ **vặn xoắn
phi vật lý** — vai trái nối với khuỷu tay phải.

```python
# Cặp trái–phải trong bộ 33 điểm MediaPipe
PAIRS = [(1,4),(2,5),(3,6),(7,8),(9,10),(11,12),(13,14),(15,16),
         (17,18),(19,20),(21,22),(23,24),(25,26),(27,28),(29,30),(31,32)]

def flip(pts):
    out = pts.copy()
    out[:, 0] = -out[:, 0]           # đã chuẩn hóa nên lật quanh 0
    for a, b in PAIRS:
        out[[a, b]] = out[[b, a]]    # hoán đổi trái ↔ phải
    return out
```

Lật hợp lệ cho cả sáu hành động của đồ án, vì không hành động nào phụ thuộc vào
việc phân biệt trái với phải. Nó **nhân đôi** dữ liệu — cách tăng cường hiệu
quả nhất trong danh sách này.

### Nhiễu Gauss

```python
noise = np.random.normal(0, 0.01, pts.shape)     # sigma theo đơn vị độ dài thân
augmented = pts + noise
```

Mô phỏng sai số ước lượng tư thế. `sigma` khoảng 1% độ dài thân là hợp lý — đủ
để tạo đa dạng, không đủ để làm hỏng tư thế.

### Co giãn và tịnh tiến ngẫu nhiên

```python
pts = pts * np.random.uniform(0.9, 1.1)
pts = pts + np.random.uniform(-0.05, 0.05, 2)
```

Ít tác dụng nếu bạn đã chuẩn hóa đúng — theo định nghĩa, chuẩn hóa đã làm mô
hình bất biến với hai thứ này. Nhưng chúng dạy mô hình chịu được **chuẩn hóa
không hoàn hảo**, điều luôn xảy ra khi khung xương có nhiễu.

### Xoay nhẹ

```python
theta = np.radians(np.random.uniform(-15, 15))
R = np.array([[np.cos(theta), -np.sin(theta)],
              [np.sin(theta),  np.cos(theta)]])
pts = pts @ R.T
```

Mô phỏng camera đặt hơi nghiêng. **Giữ biên độ nhỏ** (±10–15°) vì lý do ở mục
5: xoay nhiều sẽ làm lẫn "ngã" với "đứng".

### Co giãn thời gian

```python
# Lấy mẫu lại chuỗi để nó nhanh hơn hoặc chậm hơn 10–20%
idx = np.linspace(0, len(seq)-1, int(len(seq) * rate))
warped = np.array([seq[int(round(i))] for i in idx])
```

Mô phỏng người diễn nhanh hoặc chậm hơn. Hữu ích, **nhưng cẩn thận với lớp
"ngã"**: nếu bạn làm chậm một cú ngã xuống 50%, nó bắt đầu trông như "ngồi
xuống". Giới hạn ở ±20% và cân nhắc không áp dụng cho lớp ngã.

### Bỏ khớp ngẫu nhiên

```python
drop = np.random.rand(n_joints) < 0.05
pts[drop] = pts_prev[drop]        # thay bằng giá trị frame trước
```

Mô phỏng che khuất. Dạy mô hình đừng phụ thuộc quá vào một khớp cụ thể.

### Quy tắc vàng

> **Chỉ tăng cường tập huấn luyện. Không bao giờ tăng cường tập kiểm thử.**

Vi phạm quy tắc này thì bạn đang đánh giá trên dữ liệu bịa, và con số kết quả
vô nghĩa.

Áp dụng tăng cường **sau khi đã chia tập theo người**, không phải trước. Nếu
tăng cường trước rồi chia ngẫu nhiên, một mẫu gốc và bản lật của nó có thể rơi
vào hai tập khác nhau — đó chính là rò rỉ dữ liệu (xem tầng 5).

---

## 12. Tổng hợp: đường ống đặc trưng đầy đủ

Đặt tất cả lại với nhau. Đây là mô tả của module tiền xử lý bạn viết ở tuần 4.

```
Một frame:
  33 landmark từ MediaPipe
    │
    ├─ nhân với (W, H)               → sửa méo tỉ lệ khung hình
    ├─ chọn 23 khớp                  → bỏ điểm mặt
    ├─ trừ trung điểm hông           → bất biến vị trí
    ├─ chia độ dài thân              → bất biến tỉ lệ
    └─ kiểm tra scale > 1e-6         → loại frame hỏng
         │
         ▼
    (23, 2) = 46 con số cho mỗi frame

Một cửa sổ T = 30 frame:
    (30, 23, 2) = (30, 46)
         │
         ├────────────► Mô hình 2 (LSTM): đưa thẳng vào, shape (30, 46)
         │
         └─ nén thành vector đặc trưng cố định:
              ├─ trung bình + độ lệch chuẩn của 8 góc khớp      → 16
              ├─ trung bình + độ lệch chuẩn của góc nghiêng thân → 2
              ├─ chiều cao vai và hông so với độ dài thân        →  2
              ├─ tốc độ trung bình của cổ tay và cổ chân         →  4
              ├─ biên độ dao động cổ tay (max − min)             →  2
              ├─ delta_hip_y  (CÓ DẤU)                           →  1
              ├─ delta góc gối (CÓ DẤU)                          →  2
              └─ vận tốc y trung bình của hông (CÓ DẤU)          →  1
                                                          tổng ≈ 30
              │
              ▼
         Mô hình 1 (rừng ngẫu nhiên): vector 30 chiều
```

### Mỗi đặc trưng phân biệt cặp nào

Đây là bảng biện minh cho thiết kế của bạn. Rất đáng đưa vào báo cáo, vì nó
biến "tôi chọn vài đặc trưng" thành "mỗi đặc trưng có lý do".

| Đặc trưng | Tách được cặp nào |
|---|---|
| Tốc độ trung bình cổ tay | đứng yên ↔ vẫy tay |
| Tốc độ trung bình cổ chân | đứng yên ↔ đi bộ tại chỗ |
| Biên độ dao động cổ tay | vẫy tay ↔ đi bộ tại chỗ |
| Góc gối, góc hông (trung bình) | đứng ↔ ngồi |
| Góc nghiêng thân | ngã ↔ mọi hành động khác |
| **delta_hip_y có dấu** | **ngồi xuống ↔ đứng dậy** |
| Tốc độ đi xuống của hông | ngồi xuống ↔ ngã |
| Độ lệch chuẩn của mọi đặc trưng | đứng yên ↔ mọi hành động có chuyển động |

Nếu ma trận nhầm lẫn ở tầng 5 cho thấy một cặp cụ thể hay bị lẫn, hãy quay lại
bảng này và hỏi: đặc trưng nào lẽ ra phải tách được cặp đó, và vì sao nó không
làm được?

---

## Tự kiểm tra

1. **Điều gì xảy ra nếu bạn đưa thẳng tọa độ pixel vào mô hình?** Nêu cụ thể mô
   hình sẽ học gì, và nó sẽ hỏng khi nào.

2. Vì sao chọn trung điểm hông làm gốc chứ không phải mũi hay trọng tâm mọi
   khớp?

3. Vì sao chia cho độ dài thân (hông→vai) chứ không chia cho chiều cao toàn
   thân (đầu→chân)?

4. Bạn định thêm bước chuẩn hóa xoay để khung xương luôn thẳng đứng. Vì sao đây
   là ý tưởng tồi cho đồ án này? Nêu cách thay thế đúng.

5. Đặc trưng của bạn gồm: trung bình góc gối, độ lệch chuẩn chiều cao hông, tốc
   độ trung bình của cổ tay. Vì sao ba đặc trưng này **không thể** phân biệt
   ngồi xuống với đứng dậy? Thêm gì để sửa?

6. Bạn lật ngang khung xương để tăng dữ liệu, chỉ đổi dấu `x`. Chuyện gì xảy
   ra, và thiếu bước gì?

7. `np.arccos` trả về `nan` khi tính góc khớp. Nguyên nhân và cách sửa?

8. Trong 30 frame của một cửa sổ, có 2 frame bị mất khung xương ở giữa. Bạn nội
   suy hay bỏ? Nếu 10 frame liên tiếp bị mất thì sao?

<details>
<summary>Đáp án gợi ý</summary>

1. Mô hình học **vị trí trên màn hình** thay vì học hành động: "khung xương ở
   nửa dưới màn hình = ngã". Quy luật đó có thật trong dữ liệu của bạn (vì bạn
   luôn ngã ở cùng một chỗ) nên độ chính xác rất cao. Nó sập ngay khi đổi góc
   camera, đổi khoảng cách, hoặc đổi người diễn có chiều cao khác.

2. Hông ổn định nhất (gần trọng tâm, ít chuyển động độc lập), ít bị che khuất
   nhất, và lấy trung điểm hai điểm làm giảm nhiễu. Mũi thì đầu quay và cúi độc
   lập với thân. Trọng tâm mọi khớp thì chuyển động của một chi (giơ tay) làm
   dịch chuyển toàn bộ biểu diễn.

3. Vì chiều cao toàn thân **thay đổi mạnh theo tư thế** — giảm gần nửa khi
   ngồi. Chia cho một đại lượng thay đổi theo lớp thì phép chuẩn hóa vô tình mã
   hóa chính lớp đó, và tệ hơn, nó không ổn định. Ngoài ra chân hay bị cắt khỏi
   khung hình. Thân là khối cứng, giữ độ dài gần như không đổi.

4. Vì đặc trưng phân biệt rõ nhất của "ngã" là thân nằm ngang. Xoay mọi khung
   xương về thẳng đứng thì người nằm trông y hệt người đứng — bạn xóa đúng tín
   hiệu mình cần. Cách thay thế: giữ hướng, và **tăng cường dữ liệu bằng xoay
   ngẫu nhiên biên độ nhỏ** (±10–15°) để mô hình chịu được camera đặt lệch.

5. Cả ba đều **đối xứng theo thời gian** — đảo ngược chuỗi thì giá trị không
   đổi. Hai hành động đi qua cùng tập tư thế nên trung bình và độ lệch chuẩn
   giống nhau; tốc độ thì mất dấu do lấy độ lớn. Sửa bằng đặc trưng **có dấu**:
   `hip_y[cuối] − hip_y[đầu]`.

6. Vai trái sẽ nằm ở phía phải ảnh nhưng vẫn mang nhãn chỉ số "vai trái", nên
   khung xương bị vặn xoắn phi vật lý — vai trái nối khuỷu tay phải. Thiếu bước
   **hoán đổi chỉ số các cặp khớp trái ↔ phải** sau khi đổi dấu `x`.

7. Sai số dấu phẩy động làm `cos` ra ngoài `[-1, 1]` một chút (ví dụ
   `1.0000000002`). `arccos` của giá trị đó là `nan`, và `nan` lan ra toàn bộ
   tính toán sau đó mà không báo lỗi. Sửa bằng `np.clip(cos, -1.0, 1.0)` trước
   khi gọi `arccos`.

8. 2 frame: nội suy tuyến tính — khoảng trống ngắn, sai số nhỏ, và giữ được
   khoảng cách thời gian đều cho phép tính vận tốc. 10 frame liên tiếp (≈0,33
   giây): **cắt chuỗi thành hai đoạn** và bỏ phần thiếu. Nội suy qua khoảng dài
   là bịa dữ liệu, và trong 0,33 giây thì hành động có thể đã thay đổi hoàn
   toàn.

</details>

---

## Đưa gì vào báo cáo

**Mục 2.3 Biểu diễn và chuẩn hóa khung xương** trong chương Cơ sở lý thuyết,
khoảng 3–4 trang:

- Khái niệm bất biến; bảng "biến thiên nào cần loại bỏ, biến thiên nào phải
  giữ"
- Chuẩn hóa tịnh tiến: công thức và lý do chọn hông
- Chuẩn hóa tỉ lệ: công thức và lý do chọn độ dài thân, kèm so sánh với các lựa
  chọn khác
- **Chuẩn hóa xoay và lý do từ chối nó** — mục này ghi điểm cao vì nó thể hiện
  tư duy phản biện
- Góc khớp: công thức, tính bất biến, danh sách góc đã chọn
- Vận tốc và đặc trưng có dấu; giải thích vấn đề đối xứng thời gian
- Lựa chọn tập khớp và lý do

**Chương 3 (Hệ thống)** hoặc **chương 4 (Dữ liệu)**:

- Sơ đồ đường ống đặc trưng ở mục 12
- Bảng "mỗi đặc trưng phân biệt cặp nào" — đây là bảng có giá trị cao và ít đồ
  án nào có
- Bằng chứng chuẩn hóa hoạt động: bảng tọa độ thô và tọa độ chuẩn hóa ở hai
  khoảng cách camera
- Tỉ lệ frame bị loại do khung xương hỏng
- Danh sách phép tăng cường dữ liệu, kèm ghi chú rằng chỉ áp dụng cho tập huấn
  luyện

**Hình nên vẽ:** hai khung xương cạnh nhau — một người đứng gần, một người
đứng xa, tọa độ pixel rất khác nhau — rồi cùng hai khung xương đó sau chuẩn hóa,
gần như chồng khít lên nhau. Một hình duy nhất truyền tải toàn bộ ý nghĩa của
tầng này.
