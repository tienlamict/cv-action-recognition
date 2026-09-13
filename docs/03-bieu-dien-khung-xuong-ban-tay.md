# Tầng 3 — Biểu diễn khung xương bàn tay

> **Câu hỏi mở đầu:** Bạn đã có 21 cặp tọa độ mỗi frame. Tại sao không đưa thẳng
> chúng vào mô hình và xong việc?

Vì mô hình sẽ học sai thứ. Không phải "học kém", mà **học đúng một mối tương quan
có thật trong dữ liệu của bạn nhưng vô nghĩa ngoài đời**.

Tầng này ngắn về mặt code — hàm chuẩn hóa chỉ khoảng mười dòng — nhưng nó quyết
định toàn bộ chất lượng của mọi thứ phía sau. Nếu bạn chỉ có thời gian làm kỹ một
tầng, hãy chọn tầng này.

> **Ghi chú về bản cập nhật.** Tài liệu này thay thế bản cũ viết cho khung xương
> **toàn thân**. Khung tư duy giữ nguyên hoàn toàn: bất biến là gì, chuẩn hóa vứt
> bỏ thông tin nên phải biết mình vứt gì, đặc trưng phải có dấu. Nhưng **câu trả
> lời cho từng câu hỏi thì khác**, và mục 4 là chỗ khác nhiều nhất — với toàn
> thân, việc chọn gốc tọa độ gần như là chuyện hiển nhiên; với bàn tay, chọn sai
> gốc sẽ xóa sạch hai trong bốn lớp.

---

## 1. Vấn đề: mô hình học vị trí thay vì học cử chỉ

### 1.1. Thí nghiệm tưởng tượng

Bạn quay dữ liệu ở bàn làm việc của mình. Vì thói quen, khi diễn "vuốt trái" bạn
luôn bắt đầu từ phía bên phải khung hình. Khi diễn "xòe tay" bạn luôn để tay ở
giữa, ngay trước mặt.

Bạn đưa tọa độ pixel thô vào mô hình. Nó đạt 96% trên tập kiểm thử. Tuyệt vời.

Hôm bảo vệ, bạn ngồi hơi lệch sang trái so với laptop. Hệ thống báo "vuốt trái"
liên tục dù bạn chỉ đang gõ phím.

**Chuyện gì đã xảy ra?** Mô hình phát hiện ra một quy luật hoàn toàn có thật
trong dữ liệu huấn luyện: *bàn tay ở nửa phải khung hình → nhãn "vuốt trái"*. Quy
luật đó đúng 96% trên dữ liệu của bạn. Nó chỉ không liên quan gì tới cử chỉ vuốt.

Đây là dạng **tương quan giả** (*spurious correlation*), và nó là một trong những
cách thất bại phổ biến nhất của học máy ứng dụng. Mô hình không "hiểu" gì. Nó tìm
đường ngắn nhất từ đầu vào tới nhãn. Nếu vị trí trên màn hình là đường ngắn nhất,
nó sẽ đi đường đó.

### 1.2. Với bàn tay, còn một biến nữa

So với toàn thân, bài toán bàn tay có thêm một nguồn tương quan giả: **cỡ bàn tay
trong ảnh**.

Bàn tay của bạn cách camera 0,4 mét trông to gấp rưỡi bàn tay của bạn cách camera
0,6 mét. Và bàn tay người khác vốn đã to nhỏ khác nhau. Nếu một người quay dữ
liệu ngồi gần hơn những người khác, mô hình có thể học "bàn tay to → người này →
cử chỉ người này hay làm".

Với dữ liệu IPN Hand, nơi 50 người tự quay bằng 50 chiếc máy khác nhau ở khoảng
cách khác nhau, biến này rất mạnh. Nếu không chuẩn hóa tỉ lệ, mô hình gần như
chắc chắn sẽ học một phần thông tin về *người quay* thay vì về *cử chỉ*.

### 1.3. Cách chữa

Nếu ta **loại bỏ thông tin vị trí và tỉ lệ khỏi đầu vào**, mô hình không còn cách
nào để dùng chúng. Nó buộc phải tìm tín hiệu thật.

Đó chính là chuẩn hóa. Nhưng như sẽ thấy ở mục 4, với bàn tay thì "loại bỏ thông
tin vị trí" có hai cách làm, và một trong hai cách phá hỏng bài toán.

---

## 2. Bất biến — khung khái niệm

### 2.1. Định nghĩa

Một biểu diễn **bất biến** với một phép biến đổi nghĩa là: áp phép biến đổi đó
lên đầu vào thì biểu diễn **không đổi**.

Ta muốn biểu diễn bất biến với những thứ **không mang thông tin về cử chỉ**:

| Biến thiên | Có mang thông tin cử chỉ? | Xử lý |
|---|---|---|
| Vị trí bàn tay trong khung hình | Không | Loại bỏ — chuẩn hóa tịnh tiến |
| Khoảng cách tay tới camera | Không | Loại bỏ — chuẩn hóa tỉ lệ |
| Cỡ bàn tay của người dùng | Không | Loại bỏ — cùng phép chuẩn hóa tỉ lệ |
| Độ phân giải và tỉ lệ khung của camera | Không | Loại bỏ — đổi sang pixel rồi chia cho đơn vị |
| **Vị trí tay thay đổi trong cửa sổ** | **CÓ** — đó chính là cú vuốt | **Giữ lại!** |
| **Hình dạng bàn tay thay đổi** | **CÓ** — đó chính là xòe và chụm | **Giữ lại!** |
| **Tốc độ chuyển động** | **CÓ** | **Giữ lại!** |
| **Hướng thời gian** | **CÓ** | **Giữ lại!** |
| Góc xoay bàn tay trong mặt phẳng ảnh | Một phần | Không chuẩn hóa — xem mục 6 |
| Tay trái hay tay phải | Không, với đề tài này | Xử lý bằng tăng cường dữ liệu, mục 13 |

### 2.2. Nguyên tắc đánh đổi

> Mỗi phép chuẩn hóa vứt bỏ thông tin. Vứt bỏ thông tin nhiễu là tốt. Vứt bỏ
> thông tin có ích là hỏng. Bạn phải quyết định từng cái, dựa trên bài toán cụ
> thể.

Bốn hàng in đậm trong bảng trên là chỗ nhiều người làm sai. Cụ thể với đề tài
này, có **ba cái bẫy**, và tài liệu sẽ quay lại từng cái:

1. Chọn gốc tọa độ là cổ tay **của từng frame** — xóa sạch quỹ đạo, mất hai lớp
   vuốt. Mục 4.
2. Chia cho **chiều dài cả bàn tay** thay vì cỡ lòng bàn tay — xóa thông tin xòe
   chụm, mất hai lớp zoom. Mục 5.
3. Chuẩn hóa **xoay** cho bàn tay luôn thẳng đứng — nghe hợp lý, nhưng thêm rủi
   ro mà không giải quyết vấn đề nào của đề tài. Mục 6.

Điều đáng chú ý: mỗi cái bẫy phá hỏng đúng một cặp lớp. Đó không phải trùng hợp,
mà vì mỗi cặp lớp của đề tài được định nghĩa bởi đúng một loại thông tin.

---

## 3. Bước 0 — đổi sang pixel trước mọi thứ

Trước khi nói tới chuẩn hóa, có một bước bắt buộc và rất dễ quên.

MediaPipe trả về `x` chia cho **chiều rộng** ảnh và `y` chia cho **chiều cao**
ảnh. Hai số chia khác nhau, nên hai trục có thang đo khác nhau.

```python
def to_pixels(seq_norm, w, h):
    """(T, 21, 2) tọa độ [0,1] → pixel. Gọi ĐẦU TIÊN, trước mọi phép tính."""
    return seq_norm * np.array([w, h], dtype=np.float32)
```

Hậu quả nếu quên, minh họa bằng số. Ảnh 1280×720, hai đoạn cùng dài 100 pixel:

| Hướng đoạn | Độ dài trên tọa độ chuẩn hóa | Sai lệch |
|---|---|---|
| Nằm ngang | 100 / 1280 = 0,078 | |
| Nằm dọc | 100 / 720 = 0,139 | chênh **1,78 lần** |

Và với ảnh 640×480 của IPN Hand, tỉ lệ 4:3, hệ số chênh chỉ là **1,33 lần**.

Nghĩa là: nếu quên bước này, dữ liệu IPN và dữ liệu webcam của bạn bị **biến dạng
theo hai hệ số khác nhau**. Mô hình huấn luyện trên IPN sẽ nhìn dữ liệu của bạn
qua một phép kéo giãn nó chưa từng thấy. Đây là một trong những lỗi khó tìm nhất,
vì nó không gây ra lỗi chương trình, chỉ làm kết quả tệ đi một cách khó hiểu.

> **Quy tắc:** `to_pixels()` là dòng đầu tiên của đường ống, chạy ngay sau khi
> lấy điểm mốc ra khỏi MediaPipe. Mọi thứ sau đó làm việc trên pixel.

---

## 4. Chuẩn hóa tịnh tiến — chọn gốc tọa độ

Đây là mục quan trọng nhất của tầng này, và là chỗ bài toán bàn tay khác hẳn bài
toán toàn thân.

### 4.1. Hai lựa chọn tự nhiên

Ta muốn biểu diễn không phụ thuộc vị trí bàn tay trong ảnh. Cách làm là dời gốc
tọa độ về một điểm trên chính bàn tay. Nhưng "một điểm" đó lấy ở frame nào?

**Cách A — gốc là cổ tay của TỪNG frame.**

```python
seq_norm = seq - seq[:, [0]]     # mỗi frame trừ đi cổ tay của chính nó
```

**Cách B — gốc là cổ tay của FRAME ĐẦU cửa sổ.**

```python
seq_norm = seq - seq[0, 0]       # mọi frame trừ đi CÙNG một vector
```

Hai dòng code khác nhau một ký tự. Hệ quả thì khác nhau hoàn toàn.

### 4.2. Cách A xóa sạch quỹ đạo

Với cách A, cổ tay **luôn nằm ở gốc tọa độ, ở mọi frame**. Theo định nghĩa.

Nghĩa là mọi thông tin về việc bàn tay đã di chuyển đi đâu trong cửa sổ đều biến
mất. Ba cử chỉ sau trở nên không phân biệt được:

```
Trước chuẩn hóa (cách A):        Sau chuẩn hóa (cách A):

vuốt trái:   ✋ ← ✋ ← ✋            vuốt trái:   ✋
vuốt phải:   ✋ → ✋ → ✋            vuốt phải:   ✋   ← giống hệt nhau
tay đứng yên: ✋   ✋   ✋           tay đứng yên: ✋
```

Hình dạng bàn tay vẫn còn nguyên, nên cách A vẫn phân biệt được xòe với chụm.
Nhưng **hai trong bốn lớp của đề tài đã mất**.

Đây chính xác là cùng một cái bẫy với chuẩn hóa xoay trong tài liệu tầng 3 bản
cũ: một phép chuẩn hóa nghe rất hợp lý, và nó xóa đúng tín hiệu bạn cần.

### 4.3. Cách B giữ được cả hai

Với cách B, **mọi frame trong cửa sổ được dời đi cùng một vector**. Phép dời đó
là một phép tịnh tiến cứng của cả cửa sổ.

Kết quả:

- **Vẫn bất biến với vị trí bàn tay trong ảnh.** Làm cùng một cú vuốt ở góc trái
  hay góc phải khung hình đều cho cùng một biểu diễn, vì cả hai đều được dời về
  sao cho cổ tay ở frame đầu nằm tại gốc.
- **Quỹ đạo được giữ nguyên.** Cổ tay ở frame cuối nằm ở đâu so với gốc chính là
  độ dời của cú vuốt.
- **Hình dạng bàn tay cũng giữ nguyên**, vì phép tịnh tiến không đổi hình.

### 4.4. Bằng chứng thực nghiệm

Đây không phải chỉ là lập luận trên giấy. Một nghiên cứu năm 2025 dùng điểm mốc
MediaPipe trên **chính bộ IPN Hand** đã so sánh hai cách chuẩn hóa này, đánh giá
chia tập theo người:

| Cách chọn gốc | Độ chính xác |
|---|---|
| Cổ tay của từng frame | 83,67% |
| **Cổ tay của frame đầu cửa sổ** | **84,66%** |

Chênh lệch khoảng một điểm phần trăm — nghe nhỏ. Nhưng cần đọc con số này cho
đúng: bài toán của họ có 14 lớp, trong đó **phần lớn là cử chỉ tĩnh hoặc cử chỉ
mà hình dạng bàn tay đủ để phân biệt**. Các lớp phụ thuộc quỹ đạo, tức hất trái,
hất phải, hất lên, hất xuống, chỉ chiếm một phần nhỏ.

Bài toán của bạn thì **hai trong bốn lớp đích phụ thuộc hoàn toàn vào quỹ đạo**.
Chênh lệch sẽ lớn hơn nhiều.

> **Đây là một thí nghiệm bạn phải tự làm.** Ở tuần 8, chạy cả hai cách chuẩn
> hóa, và báo cáo kết quả không chỉ ở mức macro-F1 tổng mà **riêng cho hai lớp
> vuốt**. Dự đoán: với cách A, hai lớp vuốt sẽ có F1 rất thấp và ma trận nhầm lẫn
> cho thấy chúng lẫn vào nhau và lẫn vào lớp nền. Nếu số liệu xác nhận dự đoán,
> bạn có một đoạn báo cáo hoàn chỉnh với đủ lập luận, dự đoán và bằng chứng.

### 4.5. Vì sao toàn thân không gặp vấn đề này

Câu hỏi tự nhiên: tài liệu tầng 3 bản cũ lấy gốc là trung điểm hai hông của từng
frame, và không có vấn đề gì. Sao bàn tay lại khác?

Vì **bản chất các lớp khác nhau**. Sáu hành động của đề cương cũ — đứng yên, đi
tại chỗ, vẫy tay, ngồi xuống, đứng dậy, ngã — đều được định nghĩa bởi **tư thế
tương đối của các chi so với thân**, không phải bởi việc cả người dịch chuyển đi
đâu trong khung hình. Ngồi xuống là đầu gối gập lại và hông hạ xuống *so với thân
người*, dù bạn ngồi ở góc nào của phòng.

Bốn cử chỉ của đề tài mới thì chia đôi: hai lớp định nghĩa bởi **hình dạng tương
đối** (xòe, chụm), hai lớp định nghĩa bởi **chuyển động tuyệt đối của cả bàn tay**
(vuốt trái, vuốt phải). Cách B là cách duy nhất giữ được cả hai loại.

> **Bài học tổng quát, đáng viết vào báo cáo:** phép chuẩn hóa đúng phụ thuộc vào
> **cách các lớp được định nghĩa**, không phải vào loại dữ liệu. Cùng là khung
> xương, cùng là chuẩn hóa tịnh tiến, nhưng đáp án khác nhau vì bài toán khác
> nhau. Đây cũng chính là bài học ở tầng 2 mục 4.4 với bản đồ nhiệt và hồi quy.

---

## 5. Chuẩn hóa tỉ lệ — chia cho cỡ lòng bàn tay

### 5.1. Vấn đề còn lại sau bước 4

Sau chuẩn hóa tịnh tiến, biểu diễn đã không phụ thuộc vị trí. Nhưng nó vẫn phụ
thuộc **kích thước**: bàn tay gần camera cho mọi khoảng cách lớn gấp rưỡi bàn tay
xa camera, dù làm cùng một cử chỉ. Và bàn tay to của người này khác bàn tay nhỏ
của người kia.

Cách chữa: chia mọi tọa độ cho một **đại lượng tỉ lệ với kích thước bàn tay
trong ảnh**.

### 5.2. Chọn đại lượng nào — đây là cái bẫy thứ hai

Có bốn ứng viên. Chỉ một cái đúng.

| Ứng viên | Công thức | Vấn đề |
|---|---|---|
| Chiều dài cả bàn tay | khoảng cách điểm 0 → điểm 12 | **Co lại khi chụm tay** — xem dưới |
| Khoảng cách ngón cái → ngón út | điểm 4 → điểm 20 | Co lại còn mạnh hơn nữa |
| Đường chéo hộp bao | từ min/max của 21 điểm | Cũng co lại khi chụm; thêm nữa rất nhạy với một điểm mốc lệch |
| **Cỡ lòng bàn tay** | **khoảng cách điểm 0 → điểm 9** | **Đúng** |

Vì sao ba ứng viên đầu sai? Hãy theo dõi điều gì xảy ra trong một cú **chụm tay**.

Gọi `d` là đại lượng chia. Khi bạn khép các ngón lại:

1. Các đầu ngón tiến lại gần cổ tay. Đây chính là tín hiệu cần đo.
2. Nhưng nếu `d` cũng co lại theo, thì khi chia, tọa độ bị **phóng to giả**.
3. Hai hiệu ứng triệt tiêu nhau. Độ xòe tính ra gần như không đổi.

Nói cách khác: **bạn dùng chính đại lượng đang thay đổi làm đơn vị đo nó**. Giống
như đo chiều dài một thanh cao su bằng một cái thước cũng làm bằng cao su và cũng
co giãn cùng nhịp.

Trong khi đó, đoạn **0 → 9** nối cổ tay với gốc ngón giữa. Nó nằm trên **gan bàn
tay**, phần gần như cứng đã nói ở tầng 2 mục 1.2. Độ dài của nó gần như không đổi
khi các ngón co duỗi. Nó chỉ đổi khi bàn tay thật sự lại gần hoặc ra xa camera,
tức là đúng thứ ta muốn loại bỏ.

Có một lập luận thẩm quyền ủng hộ lựa chọn này: chính nhóm tác giả MediaPipe Hands
đo sai số mô hình bằng **MSE chuẩn hóa theo cỡ lòng bàn tay**. Họ coi đó là đơn vị
độ dài tự nhiên của bài toán bàn tay. Đây là một câu đáng trích vào báo cáo.

### 5.3. Lấy trung vị trên cả cửa sổ

Điểm mốc có độ rung. Nếu tính `d` riêng cho từng frame, đơn vị đo sẽ nhấp nháy
theo, làm nhiễu toàn bộ chuỗi.

Cách làm: tính `d` ở mọi frame trong cửa sổ, rồi lấy **trung vị**.

Vì sao trung vị chứ không phải trung bình? Vì trung vị bền với giá trị ngoại lai.
Một frame mà điểm mốc nhảy loạn sẽ kéo trung bình lệch đi, nhưng gần như không
ảnh hưởng trung vị.

### 5.4. Cạm bẫy chia cho số gần 0

Nếu bàn tay chỉ có vài pixel, hoặc nếu điểm 0 và điểm 9 vô tình trùng nhau vì lỗi
phát hiện, thì `d` gần bằng 0 và phép chia cho ra vô cực hoặc `NaN`. Những giá
trị đó lan ra toàn bộ mảng và làm hỏng cả quá trình huấn luyện theo cách rất khó
lần ra.

Luôn kiểm tra trước khi chia, và trả về `None` để bên gọi loại bỏ cửa sổ đó.

### 5.5. Hàm chuẩn hóa hoàn chỉnh

```python
import numpy as np

WRIST, MIDDLE_MCP = 0, 9

def normalize_window(seq_px):
    """seq_px: (T, 21, 2) đơn vị PIXEL, đã vá lỗ hổng ngắn.
    Trả về (T, 21, 2) bất biến vị trí và tỉ lệ, GIỮ quỹ đạo trong cửa sổ.
    Trả về None nếu cửa sổ không dùng được."""
    if np.isnan(seq_px[0, WRIST]).any():
        return None                                  # frame đầu phải có tay
    ref   = seq_px[0, WRIST]                          # gốc: cổ tay FRAME ĐẦU
    palm  = np.linalg.norm(seq_px[:, MIDDLE_MCP] - seq_px[:, WRIST], axis=1)
    scale = np.nanmedian(palm)                        # đơn vị: cỡ lòng bàn tay
    if not np.isfinite(scale) or scale < 1e-6:
        return None
    return (seq_px - ref) / scale
```

Mười dòng. Và ba dòng trong đó — `ref`, `palm`, kiểm tra `scale` — là ba quyết
định thiết kế đã tốn bốn mục để giải thích.

### 5.6. Kiểm chứng bằng mắt — bài tập tuần 4

Đừng tin hàm trên chỉ vì nó chạy không lỗi. Ba phép thử, mỗi phép thử kiểm tra
một tính chất:

**Thử bất biến vị trí.** Làm cùng một cú vuốt ở góc trái và ở góc phải khung
hình. Vẽ quỹ đạo cổ tay đã chuẩn hóa của hai lần. Hai đường phải gần trùng nhau.

**Thử bất biến tỉ lệ.** Làm cùng một cú xòe ở 0,4 mét và ở 0,7 mét. Vẽ đường độ
xòe theo thời gian của hai lần. Hai đường phải gần trùng nhau.

**Thử giữ quỹ đạo.** Vuốt trái và vuốt phải. Vẽ quỹ đạo cổ tay đã chuẩn hóa. Hai
đường phải đi về hai phía ngược nhau, rõ rệt.

Ba cặp hình này chính là hình bằng chứng cho mục 4.3 của báo cáo. Và nếu phép thử
thứ ba **không** cho hai đường ngược nhau, bạn đã vô tình viết cách A.

---

## 6. Chuẩn hóa xoay — vì sao đề tài này không nên làm

Nhiều bài báo về nhận dạng cử chỉ từ khung xương có bước chuẩn hóa xoay: xoay
khung xương bàn tay sao cho trục cổ tay → gốc ngón giữa luôn thẳng đứng.

Nghe hợp lý: loại bỏ ảnh hưởng của việc người dùng nghiêng cổ tay.

**Với đồ án này, đừng làm.** Ba lý do, xếp theo mức quan trọng.

**Một — nó không giải quyết vấn đề nào bạn đang có.** Kiến trúc hai tầng của
MediaPipe đã xoay vùng cắt về hướng chuẩn trước khi đưa vào mô hình điểm mốc
(tầng 2, mục 6.3). Mô hình điểm mốc vì thế đã khá ổn định với cổ tay nghiêng. Bạn
không cần làm lại việc đó.

**Hai — nó có thể xóa tín hiệu.** Xoay cho bàn tay thẳng đứng ở **từng frame** sẽ
xóa mất thông tin bàn tay xoay trong cửa sổ. Nếu sau này bạn thêm cử chỉ "xoay cổ
tay để chỉnh âm lượng", phép chuẩn hóa này sẽ giết nó. Kể cả với bốn cử chỉ hiện
tại, xoay từng frame cũng làm quỹ đạo cổ tay bị biến dạng theo cách khó lường.

**Ba — nếu xoay theo cả cửa sổ thì còn nguy hiểm hơn.** Giả sử bạn xoay cả cửa sổ
một góc dựa trên hướng bàn tay ở frame đầu. Một cú vuốt ngang khi bàn tay nghiêng
45° sẽ trở thành một cú vuốt chéo sau khi xoay. Hai lần vuốt giống hệt nhau về ý
định sẽ cho hai biểu diễn khác nhau.

**Kết luận: không chuẩn hóa xoay. Giữ nguyên hướng bàn tay.**

Đây là ví dụ thứ ba của cùng một nguyên tắc, sau mục 4 và mục 5. Cùng một kỹ
thuật, đúng cho bài toán này, sai cho bài toán kia.

> **Điểm này rất đáng viết vào báo cáo.** Nêu rằng bạn đã cân nhắc chuẩn hóa xoay,
> giải thích vì sao từ chối nó, và chỉ ra hệ quả với cặp lớp vuốt. Đây là dấu
> hiệu rõ nhất cho thấy bạn hiểu công cụ mình dùng chứ không chép công thức từ
> bài báo.

**Cách đúng nếu muốn hệ thống chịu được cổ tay nghiêng:** không phải chuẩn hóa
xoay, mà là **tăng cường dữ liệu bằng xoay nhẹ ngẫu nhiên**, khoảng ±10°, khi
huấn luyện. Cách này dạy mô hình chịu được lệch nhỏ mà vẫn giữ phân biệt hướng.
Xem mục 13.

---

## 7. Độ xòe — đặc trưng trung tâm của hai lớp zoom

### 7.1. Định nghĩa

**Độ xòe** (*openness*) của một frame là khoảng cách trung bình từ năm đầu ngón
tới cổ tay:

```python
TIPS = [4, 8, 12, 16, 20]      # đầu ngón cái, trỏ, giữa, áp út, út

def openness(seq):
    """seq: (T, 21, 2) đã chuẩn hóa. Trả về (T,) — một giá trị mỗi frame."""
    return np.linalg.norm(seq[:, TIPS] - seq[:, [WRIST]], axis=2).mean(axis=1)
```

Bàn tay xòe hết cho giá trị lớn. Bàn tay chụm lại cho giá trị nhỏ. Sau chuẩn hóa,
giá trị này nằm trong khoảng chừng 1,5 đến 3 lần cỡ lòng bàn tay, tùy người.

### 7.2. Một chi tiết nhỏ nhưng quyết định

Để ý kỹ dòng code: khoảng cách tính từ đầu ngón tới cổ tay **của cùng frame đó**
(`seq[:, [WRIST]]`), chứ không phải tới gốc tọa độ.

Vì sao quan trọng? Vì sau chuẩn hóa cách B, gốc tọa độ là cổ tay **ở frame đầu**.
Nếu bạn tính khoảng cách tới gốc, thì khi bàn tay vuốt sang ngang, mọi điểm đều
xa gốc hơn, và "độ xòe" sẽ tăng lên dù bàn tay không hề mở ra.

Nói cách khác: **tính sai một chút ở đây sẽ làm cử chỉ vuốt bị nhận nhầm thành
xòe tay**. Đây là một lỗi thật, dễ mắc, và khó phát hiện vì mô hình vẫn chạy.

> Đây là hệ quả trực tiếp của việc chuẩn hóa giữ lại quỹ đạo. Cái giá phải trả
> cho việc giữ thông tin là bạn phải cẩn thận hơn khi tính đặc trưng hình dạng.

### 7.3. Từ độ xòe tới đặc trưng của cửa sổ

Độ xòe cho một giá trị mỗi frame. Cần rút thành vài con số cho cả cửa sổ:

| Đặc trưng | Công thức | Phân biệt cái gì |
|---|---|---|
| `open_start` | `o[0]` | Tay bắt đầu ở trạng thái nào |
| `open_end` | `o[-1]` | Tay kết thúc ở trạng thái nào |
| **`open_delta`** | **`o[-1] - o[0]`** | **Dấu dương là xòe, âm là chụm** |
| `open_range` | `o.max() - o.min()` | Biên độ — cử chỉ có dứt khoát không |
| **`open_trend`** | **`o[nửa sau].mean() - o[nửa đầu].mean()`** | **Như `open_delta` nhưng bền hơn với nhiễu** |

`open_delta` và `open_trend` đo cùng một thứ nhưng khác độ bền. `open_delta` chỉ
dùng hai frame, nên một điểm mốc nhảy ở frame đầu hoặc frame cuối sẽ làm hỏng nó.
`open_trend` lấy trung bình nửa cửa sổ nên chịu được nhiễu tốt hơn. Giữ cả hai và
để mô hình tự chọn; permutation importance ở tuần 6 sẽ cho biết cái nào hữu ích
hơn.

---

## 8. Góc khớp — đặc trưng bất biến nhất

### 8.1. Vì sao góc tốt

Góc giữa hai đoạn xương **tự nó đã bất biến** với tịnh tiến, tỉ lệ và cả xoay.
Không cần chuẩn hóa gì thêm.

Với bàn tay, góc gập ở khớp PIP của mỗi ngón là một mô tả rất gọn của "ngón này
đang duỗi hay đang co". Bốn góc PIP cộng một góc của ngón cái cho một mô tả hình
dạng bàn tay chỉ bằng năm con số, thay vì 42 tọa độ.

### 8.2. Công thức

Góc tại đỉnh `b` giữa hai đoạn `b→a` và `b→c`:

```python
def joint_angle(a, b, c):
    """Ba điểm (2,). Trả về góc tại b, đơn vị radian, trong [0, π]."""
    u, v = a - b, c - b
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu < 1e-6 or nv < 1e-6:
        return np.nan
    cos = np.clip(np.dot(u, v) / (nu * nv), -1.0, 1.0)
    return np.arccos(cos)
```

Hai chi tiết bắt buộc, cả hai đều là lỗi thật:

- **`np.clip` là bắt buộc.** Sai số dấu phẩy động có thể cho `cos` bằng 1,0000001,
  và `arccos` của số đó là `NaN`. Giá trị `NaN` đó sẽ lan ra toàn bộ pipeline.
- **Kiểm tra độ dài gần 0.** Nếu hai điểm mốc trùng nhau vì lỗi phát hiện, phép
  chia cho ra vô cực.

### 8.3. Nên tính góc nào

```python
PIP_ANGLES = [
    (0,  5,  6),    # gập ở gốc ngón trỏ
    (5,  6,  8),    # gập ở khớp giữa ngón trỏ
    (0,  9,  10),   # gốc ngón giữa
    (9,  10, 12),   # khớp giữa ngón giữa
    (0,  13, 14),   # gốc ngón áp út
    (13, 14, 16),   # khớp giữa ngón áp út
    (0,  17, 18),   # gốc ngón út
    (17, 18, 20),   # khớp giữa ngón út
    (0,  1,  2),    # gốc ngón cái
    (2,  3,  4),    # khớp ngón cái
]
```

Mười góc. Có thể rút gọn còn năm (chỉ lấy khớp giữa mỗi ngón) nếu muốn vector đặc
trưng gọn hơn.

### 8.4. Nhược điểm của góc — và vì sao đề tài không dùng góc làm chính

Góc bất biến với xoay. Với hình dạng bàn tay thì đó là ưu điểm. Nhưng:

- **Góc mất hoàn toàn thông tin quỹ đạo.** Một tập góc khớp không cho biết bàn
  tay đang ở đâu hay đi về đâu. Hai lớp vuốt vô hình với góc.
- **Góc nhạy với điểm mốc lệch.** Ba điểm gần nhau, chỉ một điểm lệch vài pixel
  là góc đổi nhiều độ.

**Kết luận cho đề tài:** góc là đặc trưng **bổ sung** cho hai lớp zoom, không phải
đặc trưng chính. Thêm chúng vào vector đặc trưng của rừng ngẫu nhiên và xem
permutation importance ở tuần 6 có xếp chúng cao không. Nếu không, bỏ đi cho gọn.

---

## 9. Vận tốc và hình học quỹ đạo

### 9.1. Sai phân bậc một

Vận tốc của cổ tay giữa hai bước liên tiếp:

```python
wrist = seq[:, WRIST]          # (T, 2)
v = np.diff(wrist, axis=0)     # (T-1, 2) — đơn vị: cỡ lòng bàn tay mỗi bước
```

Mảng vận tốc ngắn hơn mảng vị trí đúng một phần tử. Nếu bạn cần chúng cùng độ
dài, chèn thêm một hàng 0 ở đầu — nhưng thường không cần, vì ta chỉ rút vài con
số từ mảng vận tốc chứ không đưa cả mảng vào mô hình.

### 9.2. Đơn vị — chỗ rất dễ sai

Sau chuẩn hóa, đơn vị của vận tốc là **cỡ lòng bàn tay trên mỗi bước thời gian**.
Không phải pixel trên giây, không phải mét trên giây.

Điều này chỉ có nghĩa nếu **bước thời gian là hằng số**. Và đó chính là lý do
tầng này bắt buộc phải có bước lấy mẫu lại về lưới đều ở mục 12. Nếu bạn tính
vận tốc trên chuỗi frame thô của webcam, nơi FPS dao động từ 20 tới 30 tùy ánh
sáng, thì cùng một cú vuốt sẽ cho hai giá trị vận tốc khác nhau.

### 9.3. Đặc trưng vận tốc nên lấy

| Đặc trưng | Công thức | Phân biệt cái gì |
|---|---|---|
| **`dx`** | `wrist[-1,0] - wrist[0,0]` | **Độ dời ngang có dấu — đây là đặc trưng quan trọng nhất của hai lớp vuốt** |
| `dy` | `wrist[-1,1] - wrist[0,1]` | Độ dời dọc có dấu |
| `max_vx` | `np.abs(v[:,0]).max()` | Cử chỉ có dứt khoát không |
| `mean_vx` | `v[:,0].mean()` | Xu hướng ngang, bền hơn `dx` với nhiễu ở hai đầu |
| `max_vy` | `np.abs(v[:,1]).max()` | Vuốt thường ít chuyển động dọc |

### 9.4. Độ thẳng quỹ đạo — đặc trưng tách vuốt khỏi vẫy

Đây là đặc trưng đắt giá nhất của mục này, và nó giải quyết đúng câu hỏi đã đặt
ra từ đầu đề tài: làm sao phân biệt **vuốt** với **vẫy tay qua lại**.

```python
net  = wrist[-1] - wrist[0]                     # độ dời tổng, dạng vector
path = np.linalg.norm(v, axis=1).sum() + 1e-6   # tổng quãng đường đã đi
straightness = np.linalg.norm(net) / path       # trong [0, 1]
```

Ý nghĩa:

```
vuốt:          ✋ ──────────► ✋      net lớn, path ≈ net  →  độ thẳng ≈ 1
vẫy qua lại:   ✋ ◄──►◄──►◄──► ✋      net ≈ 0, path lớn   →  độ thẳng ≈ 0
tay rung nhẹ:  ✋ ∿∿∿ ✋              net ≈ 0, path nhỏ    →  độ thẳng ≈ 0
```

Một đặc trưng duy nhất, ba trường hợp phân biệt được. Và nó cũng lý giải bằng số
cho quyết định thiết kế ở đề cương: vì sao đề tài dùng "vuốt một chiều" chứ không
dùng "vẫy tay".

Thêm một đặc trưng bổ trợ, phân biệt vuốt ngang với vuốt dọc:

```python
horiz_ratio = abs(net[0]) / (abs(net[1]) + 1e-6)
```

### 9.5. Gia tốc — có nên thêm không

Sai phân bậc hai cho gia tốc. Về lý thuyết nó phân biệt được cử chỉ dứt khoát với
cử chỉ đều đều.

Trong thực tế, **mỗi lần lấy sai phân là một lần khuếch đại nhiễu**. Độ rung của
điểm mốc vốn đã có ở vị trí; lấy sai phân bậc một thì nhiễu tăng, bậc hai thì
tăng nữa. Với dữ liệu ở quy mô này, gia tốc thường lợi bất cập hại.

**Khuyến nghị: không dùng gia tốc ở phiên bản đầu.** Nếu muốn thử, hãy làm mượt
chuỗi vị trí trước bằng trung bình trượt ba bước, rồi mới lấy sai phân hai lần.
Và so sánh có với không bằng một thí nghiệm loại bỏ.

---

## 10. Đặc trưng có dấu và hướng thời gian

### 10.1. Vấn đề

Giả sử bạn rút đặc trưng theo cách quen thuộc của xử lý tín hiệu: lấy trung bình
và độ lệch chuẩn của mỗi kênh trên cả cửa sổ.

Thử với hai lớp `zoom_in` và `zoom_out`:

```
zoom_in  (xòe):   độ xòe 1.2 → 1.5 → 1.9 → 2.4 → 2.8
zoom_out (chụm):  độ xòe 2.8 → 2.4 → 1.9 → 1.5 → 1.2
```

| Thống kê | zoom_in | zoom_out |
|---|---|---|
| Trung bình | 1,96 | 1,96 |
| Độ lệch chuẩn | 0,58 | 0,58 |
| Nhỏ nhất | 1,2 | 1,2 |
| Lớn nhất | 2,8 | 2,8 |

**Bốn thống kê, giống hệt nhau.** Mô hình không có cách nào phân biệt.

Điều tương tự xảy ra với cặp `swipe_left` và `swipe_right` nếu bạn lấy giá trị
tuyệt đối của độ dời.

### 10.2. Vì sao thống kê tóm tắt mất hướng

Vì trung bình, độ lệch chuẩn, min, max đều là **hàm đối xứng theo thứ tự**: đảo
ngược thứ tự các phần tử không làm chúng đổi. Mà thứ tự chính là hướng thời gian,
và hướng thời gian chính là thứ phân biệt hai lớp trong mỗi cặp.

Đây là cùng một vấn đề đã gặp ở tài liệu tầng 3 bản cũ với cặp "ngồi xuống" và
"đứng dậy". Cấu trúc bài toán giống hệt; chỉ có đại lượng thay đổi khác nhau.

### 10.3. Giải pháp: đặc trưng có dấu

Một đặc trưng **có dấu** là một hiệu giữa cuối và đầu, giữ nguyên dấu:

```python
open_delta = o[-1] - o[0]          # + là xòe,      − là chụm
dx         = wrist[-1,0] - wrist[0,0]   # dấu cho biết chiều vuốt
```

| Đặc trưng | zoom_in | zoom_out | swipe_left | swipe_right |
|---|---|---|---|---|
| `open_delta` | **+1,6** | **−1,6** | ≈ 0 | ≈ 0 |
| `dx` | ≈ 0 | ≈ 0 | **dấu này** | **dấu kia** |
| `straightness` | thấp | thấp | **cao** | **cao** |

Bốn lớp tách nhau bằng ba con số.

### 10.4. Về dấu của `dx` — đừng viết cứng vào code

Chiều nào là "trái" phụ thuộc vào hai quy ước: ảnh có bị lật hay không, và "trái"
hiểu theo người làm hay theo ảnh.

Với ảnh **không lật** và "trái" hiểu theo **người làm**: khi bạn đưa tay sang trái
của bạn, bàn tay đi về phía **phải của ảnh**, nên `dx` dương.

Nhưng đừng tin câu trên. **Đo nó.** Và đặt kết quả thành một hằng số:

```python
# config.py
SWIPE_LEFT_SIGN = +1    # dấu của dx khi làm cử chỉ "vuốt trái"
                        # ĐO bằng thực nghiệm ở tuần 2, KIỂM CHỨNG lại trên IPN ở tuần 5
```

Rồi dùng hằng số đó ở mọi nơi. Lý do: bạn sẽ phải kiểm tra lại quy ước này một
lần nữa khi nạp dữ liệu IPN, vì không có gì đảm bảo họ dùng cùng quy ước với bạn.
Nếu dấu được rải rác trong code thì bạn sẽ sửa sót.

> **Cách kiểm chứng quy ước của IPN.** Với mỗi mẫu lớp G05 (hất trái), tính độ
> dời ngang của cổ tay từ đầu tới cuối cử chỉ. Lấy trung vị theo lớp. Rồi tự làm
> đúng cử chỉ đó trước webcam và tính cùng đại lượng. Hai dấu phải trùng nhau.
> Nếu ngược, lật ngang tọa độ IPN ngay khi nạp, trước mọi bước khác.
>
> **Bỏ qua bước này thì mô hình học ngược hướng và không có gì báo lỗi.** Ma trận
> nhầm lẫn chỉ trông "hơi kém", còn hệ thống chạy thật thì mỗi lần vuốt lại làm
> slide đi ngược. Đây là lỗi im lặng tốn nhiều ngày nhất của đề tài này.

### 10.5. Bài học tổng quát

> Khi hai lớp là **đảo ngược thời gian của nhau**, mọi thống kê đối xứng theo thứ
> tự đều vô dụng. Bạn cần hoặc đặc trưng có dấu, hoặc một mô hình đọc được thứ tự
> như LSTM.

Đây chính là lý do đề tài có cả hai: rừng ngẫu nhiên với đặc trưng có dấu, và
LSTM đọc thẳng chuỗi. Hai con đường khác nhau tới cùng một đích, và so sánh chúng
là một phần của chương kết quả.

---

## 11. Chọn điểm mốc — có nên bỏ bớt không

Tài liệu tầng 3 bản cũ dành hẳn một mục cho việc bỏ 10 điểm mặt trong bộ 33 điểm
toàn thân, vì chúng không mang thông tin về hành động.

**Với 21 điểm bàn tay, câu trả lời ngắn hơn nhiều: giữ hết.**

Lý do:

- **21 điểm đã rất gọn.** 42 con số mỗi frame. Bỏ đi vài điểm không tiết kiệm
  đáng kể.
- **Không có điểm nào thừa rõ ràng.** Mọi điểm đều nằm trên một ngón, và cả năm
  ngón đều tham gia vào cử chỉ xòe, chụm.
- **Cấu trúc bàn tay là thông tin.** Các điểm gốc ngón (5, 9, 13, 17) không đổi
  nhiều khi ngón co duỗi, nhưng chúng cho mạng biết mặt phẳng bàn tay đang hướng
  về đâu.

Một phương án rút gọn đáng cân nhắc, chỉ dùng khi bạn muốn một mô hình rất nhẹ:

```python
# Phương án rút gọn: cổ tay + 5 gốc ngón + 5 đầu ngón = 11 điểm
REDUCED = [0, 1, 5, 9, 13, 17, 4, 8, 12, 16, 20]
```

Nghiên cứu trên IPN Hand đã nhắc ở mục 4.4 có làm thí nghiệm tương tự: họ báo rằng
chỉ dùng 6 điểm cho 82,15% và 4 điểm cho 81,46%, so với 84,66% khi dùng cả 21
điểm. Nghĩa là **rút gọn mạnh chỉ mất khoảng hai tới ba điểm phần trăm**.

**Khuyến nghị:** giữ đủ 21 điểm ở phiên bản chính, và để phương án rút gọn làm một
dòng trong bảng thí nghiệm loại bỏ ở tuần 8. Nếu kết quả của bạn cũng cho thấy
rút gọn chỉ mất ít, đó là một kết luận thú vị về lượng thông tin dư thừa trong
biểu diễn khung xương bàn tay.

---

## 12. Lưới thời gian đều và xử lý dữ liệu thiếu

Mục này không có trong tài liệu tầng 3 bản cũ ở dạng đầy đủ, vì bài toán cũ ít
nhạy với thời gian hơn. Với cử chỉ thì nó bắt buộc.

### 12.1. Vì sao phải lấy mẫu lại

Ba nguồn dữ liệu, ba tần số:

| Nguồn | Tần số |
|---|---|
| IPN Hand | 30 FPS, ổn định |
| Webcam lúc chạy thật, phòng sáng | khoảng 28–30 FPS |
| Webcam lúc chạy thật, phòng tối | có thể tụt xuống 15–20 FPS |

Nếu cửa sổ được định nghĩa bằng **số frame**, thì 30 frame là một giây ở IPN
nhưng là hai giây ở webcam lúc tối. Mô hình sẽ thấy cùng một cử chỉ "chậm đi gấp
đôi" — một biến dạng nó chưa từng gặp lúc huấn luyện.

Giải pháp: nội suy mọi chuỗi về một **lưới thời gian đều**, đề tài chọn 15 Hz.
Cửa sổ được định nghĩa bằng **thời gian**, không bằng frame.

Vì sao 15 Hz là đủ: cử chỉ ngắn nhất trong IPN Hand khoảng 9 frame ở 30 FPS, tức
khoảng 0,3 giây. Lấy mẫu ở 15 Hz vẫn cho 4–5 điểm dữ liệu cho cử chỉ ngắn nhất,
đủ để mô tả. Đổi lại, khối lượng tính toán giảm một nửa.

```python
def resample(ts, pts, hz=15.0):
    """ts: (N,) mốc thời gian tính bằng giây. pts: (N, 21, 2) pixel, có thể NaN.
    Trả về lưới thời gian đều và chuỗi đã nội suy."""
    grid = np.arange(ts[0], ts[-1] + 1e-9, 1.0 / hz)
    out = np.empty((len(grid), 21, 2), np.float32)
    for j in range(21):
        for c in range(2):
            out[:, j, c] = np.interp(grid, ts, pts[:, j, c])
    return grid, out
```

**Bắt buộc ghi mốc thời gian cho mỗi frame khi quay dữ liệu.** Không có nó thì
không lấy mẫu lại đúng được. Với video IPN thì mốc thời gian suy từ chỉ số frame
chia cho FPS; với webcam thì phải đọc đồng hồ thật.

### 12.2. Vá lỗ hổng ngắn, giữ lỗ hổng dài

Frame không tìm thấy tay được lưu là `NaN` (tầng 2, mục 9.1). Hai loại lỗ hổng,
hai cách xử lý:

| Độ dài lỗ hổng | Nguyên nhân thường gặp | Xử lý |
|---|---|---|
| 1–3 bước, tức ≤ 0,2 giây | Nhòe chuyển động, bám thất bại thoáng qua | **Nội suy tuyến tính** giữa hai bước có tay |
| Dài hơn | Tay thật sự rời khung hình hoặc bị che | **Giữ NaN**, không bịa dữ liệu |

Ranh giới ở ba bước không phải con số thiêng. Lý do chọn nó: 0,2 giây là khoảng
thời gian mà bàn tay không thể đi quá xa, nên nội suy tuyến tính là xấp xỉ hợp
lý. Dài hơn thì bàn tay có thể đã làm bất cứ điều gì, và nội suy sẽ **bịa ra một
chuyển động thẳng đều không hề xảy ra**.

```python
def fill_short_gaps(x, max_gap=3):
    """Nội suy các đoạn NaN dài ≤ max_gap bước. Đoạn dài hơn giữ nguyên NaN."""
    x = x.copy()
    miss = np.isnan(x[:, 0, 0])
    n = len(x)
    i = 0
    while i < n:
        if not miss[i]:
            i += 1
            continue
        j = i
        while j < n and miss[j]:
            j += 1
        if i > 0 and j < n and (j - i) <= max_gap:
            w = (np.arange(i, j) - (i - 1)) / (j - (i - 1))
            x[i:j] = x[i - 1] + w[:, None, None] * (x[j] - x[i - 1])
        i = j
    return x
```

Để ý hai điều kiện `i > 0` và `j < n`: lỗ hổng ở đầu chuỗi hoặc cuối chuỗi không
nội suy được vì thiếu một đầu mút. Chúng được giữ nguyên `NaN`.

### 12.3. Tỉ lệ có tay là một đặc trưng

Sau khi vá, một cửa sổ vẫn có thể còn `NaN`. Quy tắc của đề tài:

- Cửa sổ thiếu quá **30%** số bước thì loại khỏi tập huấn luyện.
- Cửa sổ có frame đầu thiếu tay thì loại, vì frame đầu là gốc tọa độ.
- Lúc chạy thật, cửa sổ như vậy trả về ngay `none` mà không cần chạy mô hình.

Và quan trọng: **tỉ lệ bước có tay được đưa vào vector đặc trưng**. Nó nói cho mô
hình biết nên tin cửa sổ này tới đâu. Nó cũng là một tín hiệu thật: cử chỉ vuốt
nhanh có tỉ lệ thiếu cao hơn tay đứng yên (tầng 2, mục 8.3), nên đặc trưng này
mang một chút thông tin về lớp.

---

## 13. Tăng cường dữ liệu ở mức điểm mốc

Tăng cường ở mức khung xương rẻ hơn nhiều so với ở mức ảnh: không phải chạy lại
MediaPipe, chỉ biến đổi vài mảng số. Nhưng mỗi phép biến đổi phải trả lời được
một câu hỏi:

> **Biến đổi này có làm đổi lớp không?**

Trả lời sai câu đó là cách nhanh nhất để dạy mô hình điều ngược lại sự thật.

### 13.1. Lật ngang — phép quan trọng nhất, và có bẫy

Mục đích: một người thuận tay trái làm cử chỉ bằng tay trái. Nếu dữ liệu chỉ có
tay phải, mô hình sẽ hỏng với họ. Lật ngang tạo ra dữ liệu tay kia miễn phí.

Áp dụng **sau** chuẩn hóa, trên tọa độ đã chuẩn hóa:

```python
def flip_horizontal(seq, label):
    """seq: (T, 21, 2) đã chuẩn hóa. Trả về (seq_lật, nhãn_mới)."""
    out = seq.copy()
    out[:, :, 0] *= -1                       # đảo trục ngang
    FLIP = {"swipe_left": "swipe_right",
            "swipe_right": "swipe_left"}     # zoom_in, zoom_out, none GIỮ NGUYÊN
    return out, FLIP.get(label, label)
```

**Cái bẫy nằm ở dòng `FLIP`.** Ba nhận xét:

- Cặp **vuốt phải đổi nhãn cho nhau.** Lật một cú vuốt trái sẽ ra một cú vuốt
  phải. Quên đổi nhãn thì bạn đang dạy mô hình rằng hai lớp này là một.
- Cặp **xòe chụm giữ nguyên nhãn.** Lật một bàn tay đang xòe vẫn ra một bàn tay
  đang xòe. Độ xòe là khoảng cách, không phụ thuộc chiều.
- **Không cần hoán đổi chỉ số điểm mốc.** Đây là điểm khác so với khung xương
  toàn thân, nơi bạn phải hoán đổi vai trái với vai phải, khuỷu trái với khuỷu
  phải. Với bàn tay, 21 điểm không có cặp trái phải — chúng là các ngón của cùng
  một bàn tay. Lật một bàn tay phải ra đúng hình chiếu của một bàn tay trái, với
  cùng thứ tự chỉ số.

**Viết kiểm thử đơn vị cho phép này.** Đây là lỗi im lặng nguy hiểm nhất của cả
đồ án, vì nó không gây lỗi chương trình và chỉ làm kết quả tệ đi một cách mơ hồ:

```python
def test_flip():
    seq, lab = load_one_window("swipe_left")
    f = window_features(seq, 1.0)
    seq2, lab2 = flip_horizontal(seq, lab)
    f2 = window_features(seq2, 1.0)
    assert lab2 == "swipe_right"
    assert np.sign(f2[IDX_DX]) == -np.sign(f[IDX_DX])       # dx đổi dấu
    assert np.isclose(f2[IDX_OPEN_DELTA], f[IDX_OPEN_DELTA]) # open_delta giữ nguyên
```

### 13.2. Các phép còn lại

| Phép | Mô phỏng điều gì | Tham số | Đổi nhãn? |
|---|---|---|---|
| Co giãn | Tay to nhỏ khác nhau, chuẩn hóa chưa hoàn hảo | ±10% | Không |
| Xoay nhẹ | Camera hơi nghiêng, cổ tay nghiêng | ±10° | Không |
| **Co giãn thời gian** | Người làm nhanh hoặc chậm | 0,8–1,2× rồi nội suy về đúng T bước | Không |
| Nhiễu Gauss | Độ rung của điểm mốc | σ lấy theo số đo thật ở tầng 2 mục 12 | Không |
| Xóa bước ngẫu nhiên | Frame mất tay | Xóa 1–3 bước rồi vá bằng `fill_short_gaps` | Không |

Hai ghi chú:

**Co giãn thời gian là phép đáng giá nhất sau lật ngang.** Bài báo IPN Hand ghi
nhận bộ dữ liệu của họ có **độ biến thiên tốc độ lớn nhất** trong các bộ cùng
loại, tức là cùng một cử chỉ được các người khác nhau làm với tốc độ rất khác
nhau. Phép này dạy mô hình chịu được điều đó.

**Xoay nhẹ là cách đúng để xử lý cổ tay nghiêng**, thay cho chuẩn hóa xoay đã bị
từ chối ở mục 6. Giới hạn ở ±10°: xoay lớn hơn sẽ biến một cú vuốt ngang thành cú
vuốt chéo và làm nhiễu nhãn.

### 13.3. Quy tắc vàng

> Tăng cường **chỉ áp dụng cho tập huấn luyện**, tạo mới ở mỗi epoch, và không
> bao giờ chạm vào tập kiểm định hay tập kiểm thử.

Tăng cường tập kiểm thử làm mất ý nghĩa của con số đo được: bạn không còn đo hiệu
năng trong điều kiện thật nữa.

---

## 14. Tổng hợp — đường ống hoàn chỉnh

### 14.1. Thứ tự các bước

```
Điểm mốc thô từ MediaPipe, tọa độ [0,1], có thể NaN
        │
        ▼  to_pixels(w, h)                    ← mục 3. Bắt buộc, làm đầu tiên
   tọa độ pixel
        │
        ▼  resample(ts, hz=15)                ← mục 12.1
   lưới thời gian đều
        │
        ▼  fill_short_gaps(max_gap=3)         ← mục 12.2
   đã vá lỗ hổng ngắn, lỗ hổng dài vẫn NaN
        │
        ▼  cắt cửa sổ T bước, bước trượt S
   (T, 21, 2) + tỉ lệ có tay
        │
        ├──► [nếu huấn luyện] tăng cường      ← mục 13
        │
        ▼  normalize_window()                 ← mục 4, 5. Gốc = cổ tay frame đầu
   bất biến vị trí và tỉ lệ, GIỮ quỹ đạo
        │
        ├──────────────────────────► vào thẳng LSTM, dạng (T, 42)
        │
        ▼  window_features()                  ← mục 7–10
   vector ~15 đặc trưng ──────────► vào rừng ngẫu nhiên hoặc mô hình luật
```

**Một hàm duy nhất cho cả ba nguồn.** Dữ liệu IPN, dữ liệu tự quay và luồng
webcam lúc chạy thật phải đi qua **cùng đoạn code này**, import từ `src/`. Hai
phiên bản "gần giống nhau" là nguồn lỗi âm thầm số một: mô hình đạt kết quả đẹp
lúc đánh giá nhưng chạy thật thì loạn, và bạn sẽ mất nhiều ngày để tìm ra vì sao.

### 14.2. Vector đặc trưng đầy đủ

```python
WRIST, TIPS = 0, [4, 8, 12, 16, 20]

def openness(seq):
    return np.linalg.norm(seq[:, TIPS] - seq[:, [WRIST]], axis=2).mean(axis=1)

def window_features(seq, presence_ratio):
    """seq: (T, 21, 2) đã chuẩn hóa. presence_ratio: tỉ lệ bước có tay."""
    o    = openness(seq)
    wr   = seq[:, WRIST]
    v    = np.diff(wr, axis=0)
    net  = wr[-1] - wr[0]
    path = np.linalg.norm(v, axis=1).sum() + 1e-6
    half = len(o) // 2
    return np.array([
        o[0], o[-1],                              # trạng thái đầu và cuối
        o[-1] - o[0],                             # open_delta   — CÓ DẤU
        o.max() - o.min(),                        # open_range
        o[half:].mean() - o[:half].mean(),        # open_trend   — CÓ DẤU
        net[0], net[1],                           # dx, dy       — CÓ DẤU
        np.abs(v[:, 0]).max(),                    # max_vx
        v[:, 0].mean(),                           # mean_vx      — CÓ DẤU
        np.abs(v[:, 1]).max(),                    # max_vy
        np.linalg.norm(net) / path,               # straightness
        abs(net[0]) / (abs(net[1]) + 1e-6),       # horiz_ratio
        presence_ratio,                           # chất lượng dữ liệu
    ], dtype=np.float32)

FEATURE_NAMES = ["open_start", "open_end", "open_delta", "open_range",
                 "open_trend", "dx", "dy", "max_vx", "mean_vx", "max_vy",
                 "straightness", "horiz_ratio", "presence"]
```

Mười ba đặc trưng. **Bốn trong số đó có dấu**, và chính bốn cái đó gánh phần lớn
việc phân biệt.

### 14.3. Mỗi đặc trưng phân biệt cặp nào

Bảng này là bài kiểm tra cuối cùng cho thiết kế của bạn. Nếu có một đặc trưng
không điền được vào cột phải, hãy cân nhắc bỏ nó.

| Đặc trưng | Phân biệt cặp nào |
|---|---|
| `open_delta`, `open_trend` | `zoom_in` ↔ `zoom_out`, và cả hai ↔ `none` |
| `open_range` | zoom dứt khoát ↔ cử động tay lặt vặt |
| `open_start`, `open_end` | ngữ cảnh: tay đang mở hay đang nắm |
| `dx` | `swipe_left` ↔ `swipe_right` |
| `dy` | vuốt ngang ↔ hất lên xuống, nếu sau này thêm lệnh |
| `straightness` | vuốt ↔ vẫy tay, và vuốt ↔ tay rung |
| `horiz_ratio` | vuốt ngang ↔ chuyển động dọc |
| `max_vx`, `max_vy` | cử chỉ có chủ ý ↔ tay dịch chậm không chủ ý |
| `mean_vx` | như `dx` nhưng bền hơn với nhiễu ở hai đầu cửa sổ |
| `presence` | cửa sổ đáng tin ↔ cửa sổ thiếu dữ liệu |

### 14.4. Kiểm chứng bằng boxplot

Sau khi cắt cửa sổ ở tuần 5, vẽ **boxplot của từng đặc trưng theo từng lớp** trên
tập huấn luyện. Đây là bước kiểm chứng quan trọng nhất của cả tầng.

Ba hình bắt buộc phải nhìn thấy:

- `open_delta`: hộp của `zoom_in` nằm hẳn bên dương, hộp của `zoom_out` nằm hẳn
  bên âm, hai hộp gần như không chồng nhau.
- `dx`: hai hộp của hai lớp vuốt nằm ở hai phía.
- `straightness`: hộp của hai lớp vuốt cao hơn hẳn hộp của lớp `none`.

**Nếu ba hình này không như mô tả, dừng lại và quay về kiểm tra tầng 2 và mục 3
tới 5 của tầng này trước khi đi tiếp.** Không mô hình nào cứu được đặc trưng
không tách lớp, và phát hiện lỗi ở đây rẻ hơn rất nhiều so với phát hiện nó ở
tuần 8.

Các boxplot này cũng là cách chọn ngưỡng cho mô hình luật ở tuần 4: ngưỡng tốt
nằm ở chỗ hai hộp tách nhau.

---

## Tự kiểm tra

Câu 1 là câu chính của tầng này. Nếu chỉ trả lời được một câu, hãy là câu đó.

1. **Vì sao lấy gốc tọa độ là cổ tay của TỪNG frame sẽ phá hỏng bài toán, còn lấy
   cổ tay của FRAME ĐẦU cửa sổ thì không?** Chỉ rõ lớp nào bị mất và vì sao.

2. Vì sao chia tọa độ cho khoảng cách điểm 0 → điểm 9, mà không chia cho chiều dài
   cả bàn tay (điểm 0 → điểm 12)? Dùng cử chỉ chụm tay để giải thích.

3. Vì sao phải đổi sang pixel trước khi tính bất cứ khoảng cách nào? Vì sao lỗi
   này **tệ hơn** khi bạn trộn dữ liệu IPN Hand với dữ liệu webcam của mình?

4. Bạn tính độ xòe bằng khoảng cách từ năm đầu ngón tới **gốc tọa độ** thay vì tới
   cổ tay của cùng frame. Lỗi gì sẽ xảy ra, và với cặp lớp nào?

5. Một bạn đề xuất: "rút đặc trưng bằng trung bình, độ lệch chuẩn, min, max của
   mỗi kênh trên cả cửa sổ". Cặp lớp nào sẽ không phân biệt được, và vì sao?

6. Vì sao đề tài **không** chuẩn hóa xoay, dù nó nghe hợp lý? Nếu muốn hệ thống
   chịu được cổ tay nghiêng thì làm cách nào?

7. Bạn lật ngang một cửa sổ `zoom_in` để tăng cường dữ liệu. Nhãn mới là gì? Còn
   nếu lật một cửa sổ `swipe_left`? Vì sao hai trường hợp khác nhau?

8. Vì sao phải lấy mẫu lại về lưới 15 Hz thay vì dùng thẳng chuỗi frame? Nêu một
   tình huống cụ thể mà bỏ bước này gây hỏng.

9. Lỗ hổng mất tay dài 2 bước thì nội suy, dài 10 bước thì không. Vì sao có ranh
   giới, và điều gì sai nếu nội suy qua lỗ hổng dài?

10. Bạn huấn luyện trên IPN Hand, đạt macro-F1 tốt, nhưng khi chạy thật thì mỗi
    lần vuốt trái slide lại đi lùi. Nguyên nhân nhiều khả năng nhất là gì, và bạn
    kiểm tra thế nào?

<details>
<summary>Đáp án gợi ý</summary>

1. Với gốc là cổ tay từng frame, cổ tay **luôn nằm tại gốc tọa độ ở mọi frame**
   theo định nghĩa, nên mọi thông tin về việc bàn tay đã di chuyển đi đâu trong
   cửa sổ đều biến mất. Hai lớp `swipe_left` và `swipe_right` trở nên không phân
   biệt được với nhau và với tay đứng yên. Với gốc là cổ tay frame đầu, mọi frame
   được dời đi **cùng một vector**, tức một phép tịnh tiến cứng của cả cửa sổ:
   vẫn bất biến với vị trí bàn tay trong ảnh, nhưng quỹ đạo bên trong cửa sổ được
   giữ nguyên. Hình dạng bàn tay giữ nguyên trong cả hai cách, nên cặp zoom không
   bị ảnh hưởng.

2. Vì chiều dài cả bàn tay **co lại khi chụm tay**, tức là chính đại lượng đang
   thay đổi lại được dùng làm đơn vị đo nó. Khi chụm, các đầu ngón tiến gần cổ
   tay (tín hiệu ta cần) nhưng đơn vị chia cũng nhỏ đi, nên sau khi chia tọa độ bị
   phóng to giả và hai hiệu ứng triệt tiêu nhau — độ xòe tính ra gần như không
   đổi, mất luôn cặp zoom. Đoạn 0 → 9 nằm trên gan bàn tay, phần gần như cứng, độ
   dài không đổi khi ngón co duỗi, chỉ đổi khi tay ra xa hay lại gần camera.

3. Vì MediaPipe chia `x` cho chiều rộng và `y` cho chiều cao, hai số khác nhau,
   nên hai trục có thang đo khác nhau và hình học bị kéo giãn theo tỉ lệ khung
   hình. Tệ hơn khi trộn hai nguồn vì **IPN là 4:3 (hệ số méo 1,33) còn webcam
   của bạn là 16:9 (hệ số 1,78)**: hai nguồn bị biến dạng theo hai hệ số khác
   nhau, nên mô hình huấn luyện trên nguồn này sẽ nhìn nguồn kia qua một phép kéo
   giãn nó chưa từng thấy.

4. Sau chuẩn hóa, gốc tọa độ là cổ tay ở **frame đầu**. Khi bàn tay vuốt sang
   ngang, mọi điểm mốc đều xa gốc hơn, nên "độ xòe" tính kiểu đó sẽ tăng dù bàn
   tay không mở ra. Hậu quả: **cử chỉ vuốt bị nhận nhầm thành xòe tay**, tức là
   `swipe_left` và `swipe_right` lẫn vào `zoom_in`.

5. Cặp `zoom_in` ↔ `zoom_out`, và cặp `swipe_left` ↔ `swipe_right` nếu lấy giá
   trị tuyệt đối. Vì trung bình, độ lệch chuẩn, min và max đều là **hàm đối xứng
   theo thứ tự**: đảo ngược thứ tự các phần tử không làm chúng đổi. Mà thứ tự
   chính là hướng thời gian, và hướng thời gian chính là thứ phân biệt hai lớp
   trong mỗi cặp. Cách chữa: đặc trưng có dấu, hoặc mô hình đọc được thứ tự.

6. Ba lý do. Kiến trúc hai tầng của MediaPipe **đã** xoay vùng cắt về hướng chuẩn
   nên mô hình điểm mốc vốn đã ổn định với cổ tay nghiêng. Xoay từng frame xóa
   mất thông tin bàn tay xoay trong cửa sổ. Xoay cả cửa sổ theo hướng bàn tay ở
   frame đầu sẽ biến một cú vuốt ngang lúc cổ tay nghiêng thành cú vuốt chéo, nên
   hai lần vuốt cùng ý định cho hai biểu diễn khác nhau. Cách đúng: **tăng cường
   dữ liệu bằng xoay nhẹ ngẫu nhiên ±10°** khi huấn luyện.

7. Lật `zoom_in` vẫn là `zoom_in`; lật `swipe_left` thành `swipe_right`. Khác
   nhau vì độ xòe là một **khoảng cách**, không phụ thuộc chiều, nên phép lật
   không đổi nó; còn hướng vuốt là một **vector có chiều**, và lật đảo chiều đó.
   Ghi chú thêm: với bàn tay không cần hoán đổi chỉ số điểm mốc như với khung
   xương toàn thân, vì 21 điểm không có cặp trái phải.

8. Vì cửa sổ định nghĩa bằng số frame sẽ có **độ dài thời gian khác nhau** khi
   FPS khác nhau. Tình huống cụ thể: IPN quay ổn định 30 FPS, còn webcam của bạn
   trong phòng tối tụt xuống 15 FPS vì camera kéo dài thời gian phơi sáng. Cùng
   30 frame, ở IPN là một giây còn ở webcam là hai giây, nên mô hình thấy cùng
   một cử chỉ "chậm đi gấp đôi" — một biến dạng nó chưa gặp lúc huấn luyện.

9. Ranh giới tồn tại vì với lỗ hổng ngắn (≤ 0,2 giây) bàn tay không thể đi quá
   xa, nên nội suy tuyến tính là xấp xỉ hợp lý. Với lỗ hổng dài, bàn tay có thể đã
   làm bất cứ điều gì, và nội suy sẽ **bịa ra một chuyển động thẳng đều chưa hề
   xảy ra**. Dữ liệu bịa đó vào tập huấn luyện là dạy mô hình học thứ không có
   thật; vào lúc chạy thật thì có thể sinh ra một lệnh không ai ra.

10. Nguyên nhân nhiều khả năng nhất: **quy ước hướng của IPN ngược với quy ước
    của webcam bạn**, hoặc bạn đã lật ảnh trước khi đưa vào mô hình lúc chạy thật
    nhưng không lật lúc huấn luyện. Kiểm tra: với mỗi mẫu lớp G05 của IPN, tính
    độ dời ngang của cổ tay từ đầu tới cuối cử chỉ và lấy trung vị; rồi tự làm
    đúng cử chỉ đó trước webcam và tính cùng đại lượng. Hai dấu phải trùng nhau.
    Nếu ngược, lật ngang tọa độ IPN ngay khi nạp, trước mọi bước khác.

</details>

---

## Đưa gì vào báo cáo

Khoảng 3 tới 4 trang cho **2.3 Biểu diễn khung xương bàn tay**. Mục này ngắn hơn
mục ước lượng tư thế nhưng **mật độ lập luận riêng của bạn thì cao hơn**, vì đây
là phần bạn tự thiết kế chứ không phải mô tả công cụ có sẵn.

**2.3.1 Vấn đề tương quan giả.** Thí nghiệm tưởng tượng ở mục 1, khái niệm bất
biến, bảng ở mục 2.1 và nguyên tắc đánh đổi. Nhấn mạnh rằng chuẩn hóa là một
chuỗi quyết định, mỗi quyết định vứt bỏ một thứ.

**2.3.2 Chọn gốc tọa độ.** Mục có giá trị cao nhất. Trình bày cả hai cách, hình
minh họa ba cử chỉ bị gộp thành một ở cách A, con số thực nghiệm 83,67% so với
84,66% từ nghiên cứu trên IPN Hand, và lập luận vì sao chênh lệch sẽ lớn hơn với
bài toán của bạn. Kết bằng mục 4.5 về việc vì sao toàn thân không gặp vấn đề này.

**2.3.3 Chọn đơn vị đo.** Bảng bốn ứng viên ở mục 5.2 và lập luận "thước cao su".
Trích việc nhóm tác giả MediaPipe cũng đo sai số theo cỡ lòng bàn tay.

**2.3.4 Các phép chuẩn hóa bị từ chối.** Chuẩn hóa xoay ở mục 6. Viết mục này là
cách rẻ nhất để chứng tỏ bạn hiểu công cụ chứ không chép công thức.

**2.3.5 Thiết kế đặc trưng.** Bốn nhóm đặc trưng, nguyên tắc đặc trưng có dấu ở
mục 10, độ thẳng quỹ đạo ở mục 9.4, và bảng "mỗi đặc trưng phân biệt cặp nào" ở
mục 14.3.

**2.3.6 Tiền xử lý chuỗi.** Lấy mẫu lại về lưới đều, vá lỗ hổng ngắn, tỉ lệ có
tay như một đặc trưng. Nối lại với mục 8.3 của tầng 2 để giải thích vì sao lỗ
hổng xuất hiện nhiều nhất ở đúng cử chỉ vuốt.

**Hình nên vẽ:**

1. **Hình hai cách chọn gốc tọa độ** đặt cạnh nhau, với ba cử chỉ bị gộp thành
   một ở bên trái. Đây là hình giải thích tốt nhất của cả chương.
2. **Ba cặp hình kiểm chứng ở mục 5.6**: bất biến vị trí, bất biến tỉ lệ, giữ quỹ
   đạo. Hình "của bạn", từ dữ liệu của bạn.
3. **Boxplot `open_delta` và `dx` theo lớp** — bằng chứng trực quan rằng thiết kế
   đặc trưng hoạt động, trước cả khi huấn luyện mô hình nào.
4. Sơ đồ đường ống ở mục 14.1.

**Câu nên có trong báo cáo:**

> "Phép chuẩn hóa tịnh tiến được thực hiện bằng cách dời toàn bộ cửa sổ theo vị
> trí cổ tay tại khung hình đầu tiên, thay vì chuẩn hóa từng khung hình theo cổ
> tay của chính nó. Lựa chọn này giữ lại quỹ đạo chuyển động bên trong cửa sổ,
> vốn là đặc trưng phân biệt duy nhất giữa hai lớp vuốt trái và vuốt phải, trong
> khi vẫn đạt được tính bất biến với vị trí bàn tay trong khung hình."

---

## Nguồn

| Nguồn | Dùng cho mục |
|---|---|
| Nghiên cứu nhận dạng cử chỉ bằng điểm mốc MediaPipe trên IPN Hand, SciTePress 2025 | 4.4, 11 — con số so sánh hai cách chuẩn hóa và thí nghiệm rút gọn số điểm |
| Zhang F. và cộng sự, *MediaPipe Hands*, arXiv:2006.10214, 2020 | 5.2 — MSE chuẩn hóa theo cỡ lòng bàn tay |
| Benitez-Garcia G. và cộng sự, *IPN Hand*, ICPR 2020 | 13.2 — độ biến thiên tốc độ giữa người thực hiện |
| Tài liệu tầng 2 (ước lượng tư thế bàn tay) | 3, 12 — định dạng đầu ra và nguồn gốc của lỗ hổng dữ liệu |
| Tài liệu tầng 3 bản cũ (khung xương toàn thân) | 1, 2, 10 — khung khái niệm giữ nguyên |
