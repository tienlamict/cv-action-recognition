# MediaPipe Hands
## Theo dõi bàn tay thời gian thực ngay trên thiết bị

**BẢN DIỄN GIẢI CHI TIẾT BẰNG TIẾNG VIỆT**
*Tóm lược và phân tích học thuật theo từng mục của bài báo*

---

**Bài báo gốc:** "MediaPipe Hands: On-device Real-time Hand Tracking"
**Tác giả:** Fan Zhang, Valentin Bazarevsky, Andrey Vakunov, Andrei Tkachenka, George Sung, Chuo-Ling Chang, Matthias Grundmann — Google Research
**Hội nghị:** CVPR 2020 Workshop on Computer Vision for Augmented and Virtual Reality
**Liên kết:** arXiv:2006.10214 — https://arxiv.org/abs/2006.10214

---

## Về tài liệu này

Tài liệu này là bản diễn giải tiếng Việt chi tiết của bài báo khoa học *"MediaPipe Hands: On-device Real-time Hand Tracking"*. Tài liệu bám sát cấu trúc bảy mục của bản gốc và trình bày lại đầy đủ nội dung kỹ thuật: kiến trúc mô hình, cách xây dựng và gán nhãn dữ liệu, toàn bộ số liệu trong ba bảng kết quả, cách triển khai trong khung MediaPipe, các ví dụ ứng dụng và kết luận.

Vì bài báo gốc là tác phẩm có bản quyền của Google Research, tài liệu này không sao chép nguyên văn từng câu mà diễn đạt lại nội dung bằng tiếng Việt, kèm trích dẫn ngắn khi cần. Các số liệu, tên mô hình và kết quả thực nghiệm được giữ nguyên đúng như bản gốc. Bạn nên đọc song song với bản PDF gốc trên arXiv khi cần trích dẫn chính xác cho công trình của mình.

**Quy ước thuật ngữ:** thuật ngữ chuyên ngành được dịch sang tiếng Việt kèm nguyên bản tiếng Anh trong ngoặc ở lần xuất hiện đầu tiên. Bảng đối chiếu thuật ngữ đầy đủ nằm ở cuối tài liệu.

---

## Mục lục

- [Tóm tắt (Abstract)](#tóm-tắt-abstract)
- [1. Giới thiệu (Introduction)](#1-giới-thiệu-introduction)
  - [1.1. Ba đóng góp chính](#11-ba-đóng-góp-chính)
- [2. Kiến trúc hệ thống (Architecture)](#2-kiến-trúc-hệ-thống-architecture)
  - [2.1. BlazePalm — bộ phát hiện lòng bàn tay](#21-blazepalm--bộ-phát-hiện-lòng-bàn-tay)
  - [2.2. Mô hình điểm mốc bàn tay (Hand Landmark Model)](#22-mô-hình-điểm-mốc-bàn-tay-hand-landmark-model)
- [3. Tập dữ liệu và gán nhãn (Dataset and Annotation)](#3-tập-dữ-liệu-và-gán-nhãn-dataset-and-annotation)
- [4. Kết quả thực nghiệm (Results)](#4-kết-quả-thực-nghiệm-results)
- [5. Triển khai trong MediaPipe](#5-triển-khai-trong-mediapipe-implementation-in-mediapipe)
- [6. Ví dụ ứng dụng (Application Examples)](#6-ví-dụ-ứng-dụng-application-examples)
- [7. Kết luận (Conclusion)](#7-kết-luận-conclusion)
- [Phụ lục A — Bảng đối chiếu thuật ngữ](#phụ-lục-a--bảng-đối-chiếu-thuật-ngữ)
- [Phụ lục B — Danh sách hình trong bài báo gốc](#phụ-lục-b--danh-sách-hình-trong-bài-báo-gốc)
- [Phụ lục C — Về phần tài liệu tham khảo](#phụ-lục-c--về-phần-tài-liệu-tham-khảo)

---

## Tóm tắt (Abstract)

Nhóm tác giả giới thiệu một giải pháp theo dõi bàn tay (*hand tracking*) thời gian thực, chạy trực tiếp trên thiết bị, có khả năng dự đoán bộ khung xương bàn tay của con người chỉ từ một camera RGB đơn, hướng tới các ứng dụng thực tại tăng cường và thực tại ảo (AR/VR).

Hệ thống gồm hai mô hình phối hợp: một bộ phát hiện lòng bàn tay (*palm detector*) và một mô hình dự đoán điểm mốc bàn tay (*hand landmark model*). Toàn bộ giải pháp được mã nguồn mở trong khung MediaPipe tại địa chỉ mediapipe.dev, chạy được trên nhiều nền tảng mà không cần phần cứng chuyên dụng.

> **Điểm cốt lõi:** đây không phải là một mô hình đơn lẻ mà là một pipeline (chuỗi xử lý) hai giai đoạn được thiết kế tối ưu cho thiết bị di động — đó chính là lý do giải pháp đạt được tốc độ thời gian thực trên điện thoại phổ thông.

---

## 1. Giới thiệu (Introduction)

Khả năng cảm nhận và theo dõi hình dạng, chuyển động của bàn tay là nền tảng để cải thiện trải nghiệm người dùng trong nhiều lĩnh vực và nền tảng khác nhau. Bàn tay là kênh giao tiếp tự nhiên nhất của con người với thế giới số: nó có thể trở thành thiết bị nhập liệu cho AR/VR, cho phép hiểu ngôn ngữ ký hiệu, hoặc điều khiển cử chỉ từ xa mà không cần chạm.

Tuy nhiên, bài toán này rất khó vì ba lý do chính:

- **Tự che khuất (self-occlusion).** Các ngón tay thường xuyên che lấp lẫn nhau hoặc bị che bởi lòng bàn tay, khiến nhiều điểm khớp biến mất khỏi ảnh.
- **Thiếu đặc trưng thị giác tương phản cao.** Bàn tay có màu sắc và kết cấu khá đồng nhất, không có nhiều mẫu hoa văn đặc trưng để mô hình bám vào, khác hẳn với khuôn mặt (vốn có mắt, mũi, miệng làm mốc rõ ràng).
- **Biên độ biến đổi rất lớn.** Bàn tay có nhiều bậc tự do, dẫn đến vô số tư thế khả dĩ; đồng thời kích thước bàn tay trong ảnh có thể thay đổi tới khoảng 20 lần tuỳ khoảng cách tới camera.

Các công trình trước đó thường phải dựa vào cảm biến chiều sâu (*depth sensor*) chuyên dụng hoặc yêu cầu bộ xử lý mạnh của máy tính để bàn, khiến việc triển khai rộng rãi trên thiết bị di động phổ thông trở nên bất khả thi. Mục tiêu của bài báo là loại bỏ hai ràng buộc đó.

### 1.1. Ba đóng góp chính

1. **Một pipeline hiệu quả gồm hai giai đoạn** (bộ phát hiện lòng bàn tay + mô hình điểm mốc) cho phép theo dõi nhiều bàn tay theo thời gian thực trên thiết bị di động.
2. **Một mô hình ước lượng tư thế bàn tay 2.5D** chỉ dùng đầu vào RGB, không cần cảm biến chiều sâu, nhưng vẫn cho ra thông tin độ sâu tương đối giữa các khớp.
3. **Một giải pháp mã nguồn mở, đa nền tảng,** hỗ trợ Android, iOS, Web (TensorFlow.js) và máy tính để bàn, giúp cộng đồng nghiên cứu và nhà phát triển có thể tái sử dụng ngay.

---

## 2. Kiến trúc hệ thống (Architecture)

Giải pháp được xây dựng từ hai mô hình chạy nối tiếp nhau:

- **Bộ phát hiện lòng bàn tay (palm detector)** — hoạt động trên toàn bộ khung hình và trả về một khung bao có định hướng (*oriented bounding box*) quanh mỗi bàn tay.
- **Mô hình điểm mốc bàn tay (hand landmark model)** — hoạt động trên vùng ảnh đã được cắt theo khung bao đó và trả về 21 điểm mốc 2.5D có độ chính xác cao.

Cách chia việc này mang lại hai lợi ích lớn. Thứ nhất, việc cung cấp cho mô hình điểm mốc một vùng ảnh đã được cắt và căn chỉnh chính xác giúp giảm mạnh nhu cầu tăng cường dữ liệu (*data augmentation*) — chẳng hạn không cần xoay, co giãn hay tịnh tiến quá nhiều trong lúc huấn luyện. Thứ hai, nhờ đó mô hình có thể dành gần như toàn bộ năng lực (*capacity*) của mình cho nhiệm vụ định vị toạ độ chính xác thay vì phải học cách xử lý ảnh đầu vào hỗn loạn.

Trong kịch bản theo dõi liên tục trên video, khung bao của khung hình hiện tại được suy ra từ chính các điểm mốc dự đoán ở khung hình trước. Bộ phát hiện chỉ được kích hoạt ở khung hình đầu tiên hoặc khi hệ thống mất dấu bàn tay. Đây là một trong những yếu tố then chốt giúp giảm chi phí tính toán.

### 2.1. BlazePalm — bộ phát hiện lòng bàn tay

Để phát hiện vị trí ban đầu của bàn tay, nhóm tác giả thiết kế một mô hình dạng *single-shot detector* (bộ phát hiện một lượt) mang tên **BlazePalm**, tối ưu cho suy luận thời gian thực trên di động, tương tự tinh thần của BlazeFace dùng cho khuôn mặt.

Ba quyết định thiết kế đáng chú ý:

#### a) Phát hiện lòng bàn tay thay vì cả bàn tay

Thay vì huấn luyện mô hình phát hiện toàn bộ bàn tay đang gập duỗi, nhóm tác giả huấn luyện nó phát hiện **lòng bàn tay và nắm tay**. Lý do: ước lượng khung bao cho các vật thể cứng (*rigid*) như lòng bàn tay hay nắm tay đơn giản hơn nhiều so với vật thể có khớp linh hoạt với các ngón tay chuyển động. Ngoài ra, vì lòng bàn tay là vật thể nhỏ, thuật toán triệt tiêu không cực đại (*non-maximum suppression*) vẫn hoạt động tốt ngay cả trong trường hợp hai bàn tay bắt chéo nhau. Quan trọng hơn, lòng bàn tay có thể được mô hình hoá chỉ bằng **khung bao vuông** (bỏ qua tỷ lệ khung hình), nhờ đó số lượng anchor (*khung neo*) giảm được từ 3 đến 5 lần.

#### b) Bộ trích xuất đặc trưng kiểu encoder–decoder

Nhóm tác giả dùng một bộ trích xuất đặc trưng dạng *encoder–decoder* tương tự Mạng kim tự tháp đặc trưng (FPN — *Feature Pyramid Network*), giúp mô hình nhận biết ngữ cảnh toàn cảnh (*scene context*) ngay cả với các vật thể nhỏ. Điều này đặc biệt quan trọng khi bàn tay ở xa camera và chiếm rất ít pixel.

#### c) Hàm mất mát focal loss

Vì thiết kế trên sinh ra một lượng anchor rất lớn dẫn tới mất cân bằng nghiêm trọng giữa mẫu dương và mẫu âm, nhóm tác giả áp dụng *focal loss* (hàm mất mát tiêu điểm) trong lúc huấn luyện để hỗ trợ hội tụ.

Bảng dưới đây là nghiên cứu loại bỏ (*ablation study*) đo tác động của từng thành phần, dùng thang đo độ chính xác trung bình (*Average Precision* — AP):

| Biến thể mô hình | Độ chính xác trung bình (AP) |
|---|:---:|
| Không decoder + cross entropy loss | 86,22 % |
| Có decoder + cross entropy loss | 94,07 % |
| Có decoder + focal loss | **95,7 %** |

*Bảng 1 — Nghiên cứu loại bỏ các thành phần thiết kế của bộ phát hiện lòng bàn tay.*

> **Đọc bảng này:** riêng việc thêm decoder đã nâng AP thêm gần 8 điểm phần trăm (86,22 % → 94,07 %), cho thấy ngữ cảnh toàn cảnh là yếu tố quyết định. Focal loss đóng góp thêm khoảng 1,6 điểm phần trăm nữa.

### 2.2. Mô hình điểm mốc bàn tay (Hand Landmark Model)

Sau khi bộ phát hiện xác định được vùng lòng bàn tay trên toàn ảnh, mô hình điểm mốc thực hiện bài toán hồi quy (*regression*) — tức là dự đoán trực tiếp toạ độ liên tục — cho **21 điểm khớp** bên trong vùng ảnh đã cắt. Mô hình học được biểu diễn tư thế bàn tay nhất quán và bền vững ngay cả khi bàn tay bị che khuất một phần hoặc tự che.

Mô hình có **ba đầu ra** (*output head*) dùng chung một bộ trích xuất đặc trưng, mỗi đầu ra được huấn luyện bằng tập dữ liệu tương ứng của nó:

- **21 điểm mốc bàn tay** gồm toạ độ x, y và độ sâu tương đối (*relative depth*). Đây là ý nghĩa của cụm "2.5D": hai chiều đầy đủ trên mặt phẳng ảnh cộng thêm một trục sâu mang tính tương đối chứ không phải độ sâu tuyệt đối theo đơn vị mét.
- **Xác suất có bàn tay (hand presence probability)** — cờ nhị phân cho biết vùng ảnh đầu vào có thực sự chứa bàn tay hay không. Đây chính là cơ chế giúp hệ thống phục hồi khi mất dấu: nếu xác suất này tụt xuống dưới ngưỡng, bộ phát hiện sẽ được kích hoạt lại.
- **Phân loại tay trái / tay phải (handedness)** — đầu ra nhị phân xác định bàn tay đang xét là tay trái hay tay phải. Thông tin này quan trọng với các ứng dụng AR cần gắn hiệu ứng đúng theo từng tay.

Mô hình được phát hành ở nhiều biến thể với dung lượng khác nhau: biến thể nhẹ hơn dành cho các thiết bị di động chỉ có CPU (không tăng tốc GPU), và biến thể nặng hơn dành cho môi trường máy tính để bàn nơi độ chính xác được ưu tiên hơn tốc độ.

> **Một chi tiết quan trọng:** phần giám sát (*supervision*) cho độ sâu tương đối **chỉ đến từ dữ liệu tổng hợp**. Ảnh thật do người gán nhãn không thể cung cấp nhãn độ sâu đáng tin cậy, nên khả năng ước lượng chiều sâu của mô hình hoàn toàn phụ thuộc vào dữ liệu render 3D.

---

## 3. Tập dữ liệu và gán nhãn (Dataset and Annotation)

Nhóm tác giả xây dựng ba tập dữ liệu bổ trợ lẫn nhau, mỗi tập khắc phục một điểm yếu của tập kia:

### 3.1. Ba tập dữ liệu

| Tập dữ liệu | Quy mô | Đặc điểm và hạn chế |
|---|:---:|---|
| Ảnh đời thực (in-the-wild) | 6.000 ảnh | Đa dạng về vị trí địa lý, điều kiện ánh sáng và ngoại hình bàn tay; nhược điểm là ít tư thế ngón tay phức tạp. |
| Cử chỉ thu trong nhà (in-house gesture) | 10.000 ảnh | Bao phủ mọi góc độ cử chỉ tay khả thi về mặt vật lý, thu từ 30 người; nhược điểm là phông nền ít thay đổi. |
| Dữ liệu tổng hợp (synthetic) | 100.000 ảnh | Render từ mô hình tay 3D thương mại có gắn khung xương, cho nhãn chính xác tuyệt đối; nhược điểm là khoảng cách miền (*domain gap*) so với ảnh thật. |

### 3.2. Chi tiết tập dữ liệu tổng hợp

Để bao phủ tốt hơn các tư thế bàn tay khả dĩ và có nguồn giám sát đáng tin cậy cho toạ độ chiều sâu, nhóm tác giả dựng một mô hình bàn tay 3D chất lượng cao dạng thương mại, có:

- **24 xương** (*bones*) trong bộ khung điều khiển;
- **36 blendshape** (dạng biến hình để tạo biểu cảm và biến dạng chi tiết của da);
- **5 kiểu vân da** (*skin textures*) khác nhau nhằm mô phỏng nhiều sắc tố da.

Từ mô hình này, nhóm tác giả tạo ra các chuỗi video mô phỏng quá trình chuyển đổi tư thế, sau đó lấy mẫu ảnh từ các chuỗi đó. Mỗi ảnh được render với **ánh sáng HDR ngẫu nhiên** và **ba góc camera** khác nhau, tổng cộng thu được 100.000 ảnh.

### 3.3. Cách gán nhãn cho từng thành phần

- **Bộ phát hiện lòng bàn tay:** chỉ dùng tập ảnh đời thực, vì nhiệm vụ này chủ yếu cần đa dạng về bối cảnh và ánh sáng chứ không cần đa dạng về tư thế ngón tay.
- **Mô hình điểm mốc:** dùng kết hợp cả ba tập dữ liệu. Với ảnh thật, người gán nhãn đánh dấu thủ công 21 điểm mốc; với ảnh tổng hợp, nhãn được lấy trực tiếp bằng cách chiếu (*project*) các khớp 3D đã biết xuống mặt phẳng ảnh.
- **Đầu ra xác suất có bàn tay:** mẫu dương là các vùng ảnh thật đã được gán nhãn có bàn tay; mẫu âm là các vùng ảnh không chứa bàn tay.
- **Đầu ra tay trái / tay phải:** được gán nhãn trên một tập con của dữ liệu ảnh thật.

---

## 4. Kết quả thực nghiệm (Results)

### 4.1. Ảnh hưởng của việc phối hợp dữ liệu

Nhóm tác giả huấn luyện mô hình điểm mốc theo ba chiến lược dữ liệu khác nhau và đánh giá bằng sai số bình phương trung bình (MSE) được **chuẩn hoá theo kích thước lòng bàn tay**. Việc chuẩn hoá này rất quan trọng: nó giúp so sánh công bằng giữa bàn tay lớn (ở gần camera) và bàn tay nhỏ (ở xa camera). Giá trị càng nhỏ càng tốt.

| Chiến lược dữ liệu huấn luyện | MSE chuẩn hoá theo kích thước lòng bàn tay |
|---|:---:|
| Chỉ dùng ảnh đời thực | 16,1 % |
| Chỉ dùng ảnh tổng hợp | 25,7 % |
| Kết hợp cả hai | **13,4 %** |

*Bảng 2 — Kết quả theo từng loại tập dữ liệu.*

Kết quả cho thấy việc kết hợp dữ liệu thật và dữ liệu tổng hợp cho kết quả tốt nhất (13,4 %), vượt trội so với chỉ dùng ảnh thật (16,1 %) và bỏ xa phương án chỉ dùng ảnh tổng hợp (25,7 %). Ngoài việc giảm sai số, nhóm tác giả còn ghi nhận rằng bổ sung dữ liệu tổng hợp làm **giảm hiện tượng rung giật giữa các khung hình** (*inter-frame jitter*) — một yếu tố ảnh hưởng trực tiếp đến cảm nhận chất lượng của người dùng cuối, dù không thể hiện rõ trong con số MSE.

> **Bài học rút ra:** dữ liệu tổng hợp một mình là không đủ vì khoảng cách miền quá lớn, nhưng nó là chất bổ trợ cực kỳ hiệu quả khi đi cùng dữ liệu thật — đặc biệt cho những nhãn mà con người không thể gán chính xác, như độ sâu.

### 4.2. So sánh ba biến thể mô hình

Nhóm tác giả phát hành ba biến thể mô hình điểm mốc nhằm phục vụ các nhu cầu triển khai khác nhau. Thời gian suy luận được đo trên GPU của từng thiết bị thông qua backend GPU của TensorFlow Lite.

| Mô hình | Số tham số (triệu) | MSE | Pixel 3 (ms) | Samsung S20 (ms) | iPhone 11 (ms) |
|---|:---:|:---:|:---:|:---:|:---:|
| Light (nhẹ) | 1,00 | 11,83 | 6,6 | 5,6 | 1,1 |
| **Full (đầy đủ)** | 1,98 | 10,05 | 16,1 | 11,1 | 5,3 |
| Heavy (nặng) | 4,02 | 9,817 | 36,9 | 25,8 | 7,5 |

*Bảng 3 — Đặc tính hiệu năng của các biến thể mô hình điểm mốc bàn tay.*

Phân tích của nhóm tác giả: mô hình **Full** đạt được sự cân bằng tốt nhất giữa chất lượng và tốc độ cho triển khai thời gian thực trên di động. Khi tăng lên mô hình Heavy, chất lượng chỉ cải thiện rất nhỏ (MSE từ 10,05 xuống 9,817, tức khoảng 2,3 %) trong khi thời gian suy luận trên Pixel 3 tăng hơn gấp đôi (16,1 ms lên 36,9 ms). Đây là biểu hiện điển hình của quy luật lợi ích giảm dần (*diminishing returns*).

Ngược lại, mô hình Light phù hợp cho các thiết bị yếu hoặc các ứng dụng cần ngân sách tính toán cực thấp: nó nhanh gấp khoảng 2,4 lần mô hình Full trên Pixel 3 với cái giá là MSE tăng khoảng 17,7 %.

> **Lưu ý khi đọc con số:** để đạt 30 khung hình/giây, toàn bộ pipeline phải hoàn tất trong khoảng 33 ms mỗi khung hình — và con số trong bảng mới chỉ là phần suy luận của mô hình điểm mốc, chưa tính cắt ảnh, hiển thị và (thỉnh thoảng) chạy bộ phát hiện.

---

## 5. Triển khai trong MediaPipe (Implementation in MediaPipe)

Giải pháp theo dõi bàn tay được hiện thực hoá dưới dạng một **đồ thị có hướng** (*directed graph*) gồm các thành phần mô-đun gọi là *calculator* trong khung MediaPipe. MediaPipe cho phép mô tả toàn bộ pipeline một cách khai báo, đồng thời tự động xử lý việc đồng bộ hoá luồng dữ liệu giữa các nhánh.

### 5.1. Tối ưu hoá then chốt: hạn chế chạy bộ phát hiện

Điểm tối ưu quan trọng nhất nằm ở chỗ bộ phát hiện lòng bàn tay **chỉ được chạy khi thực sự cần thiết**. Cơ chế hoạt động như sau:

1. Ở khung hình đầu tiên, bộ phát hiện chạy để xác định vị trí bàn tay.
2. Ở các khung hình kế tiếp, vị trí bàn tay được suy ra từ chính các điểm mốc đã tính ở khung hình trước — bộ phát hiện được bỏ qua hoàn toàn.
3. Bộ phát hiện chỉ được kích hoạt lại khi đầu ra xác suất có bàn tay của mô hình điểm mốc tụt xuống dưới một ngưỡng nhất định, tức là khi hệ thống mất dấu.

Nhờ vậy, trên phần lớn khung hình của một phiên làm việc, hệ thống chỉ phải chạy mô hình điểm mốc (vốn nhẹ hơn nhiều vì chỉ xử lý một vùng ảnh nhỏ đã cắt) thay vì quét toàn khung hình. Hành vi này được hiện thực bằng các **khối đồng bộ hoá** (*synchronization building blocks*) có sẵn của MediaPipe, giúp kiểm soát chính xác thời điểm kích hoạt nhánh phát hiện.

### 5.2. Tăng tốc bằng GPU

Để đạt hiệu năng tối ưu trên toàn pipeline, nhóm tác giả tối ưu từng calculator riêng lẻ bằng tăng tốc GPU — bao gồm các bước suy luận mô hình, cắt ảnh (*cropping*) và kết xuất hiển thị (*rendering*). Việc giữ dữ liệu nằm trên GPU xuyên suốt pipeline giúp tránh chi phí sao chép qua lại giữa CPU và GPU, vốn là nút cổ chai phổ biến trên thiết bị di động.

---

## 6. Ví dụ ứng dụng (Application Examples)

### 6.1. Nhận dạng cử chỉ (Gesture Recognition)

Trên nền các điểm mốc đã dự đoán, nhóm tác giả xây dựng một thuật toán nhận dạng cử chỉ đơn giản nhưng hiệu quả. Quy trình gồm ba bước:

1. Tính góc tích luỹ của các khớp trên từng ngón tay từ toạ độ các điểm mốc.
2. Ánh xạ tập góc đó thành trạng thái rời rạc của từng ngón: **co** (*bent*) hoặc **duỗi** (*straight*).
3. Đối chiếu tổ hợp trạng thái của cả năm ngón với một tập cử chỉ đã định nghĩa sẵn để suy ra cử chỉ tương ứng.

Phương pháp heuristic (dựa trên quy tắc) này cho phép nhận dạng các cử chỉ tĩnh cơ bản với độ chính xác hợp lý mà gần như không tốn thêm chi phí tính toán. Nhóm tác giả minh hoạ kết quả bằng ảnh chụp màn hình hệ thống chạy thời gian thực với ngữ nghĩa cử chỉ được hiển thị trực tiếp trên khung hình.

> **Cần lưu ý phạm vi:** đây là nhận dạng cử chỉ **tĩnh** (một khung hình), không phải cử chỉ động theo chuỗi thời gian. Việc nhận dạng cử chỉ động sẽ cần thêm một tầng mô hình chuỗi phía trên.

### 6.2. Hiệu ứng thực tại tăng cường (AR Effects)

Ứng dụng thứ hai là kết xuất hiệu ứng AR trực tiếp lên khung xương bàn tay được dự đoán. Nhóm tác giả trình bày ví dụ hiệu ứng theo phong cách **đèn neon** phát sáng bám theo các đốt ngón tay, tận dụng thông tin độ sâu tương đối để các đoạn xương ở gần và ở xa được vẽ với sắc độ khác nhau, tạo cảm giác không gian ba chiều.

---

## 7. Kết luận (Conclusion)

Bài báo trình bày **MediaPipe Hands** — một giải pháp theo dõi bàn tay đầu-cuối (*end-to-end*) đạt hiệu năng thời gian thực trên nhiều nền tảng khác nhau. Hệ thống dự đoán 21 điểm mốc 2.5D chỉ từ ảnh RGB đơn, không đòi hỏi phần cứng chuyên dụng như cảm biến chiều sâu, nhờ đó có thể triển khai dễ dàng trên các thiết bị phổ thông.

Với việc mã nguồn được mở trong khung MediaPipe và hỗ trợ Android, iOS, Web và máy tính để bàn, nhóm tác giả kỳ vọng công trình này sẽ trở thành nền tảng để cộng đồng nghiên cứu và các nhà phát triển xây dựng thêm những ứng dụng và hướng nghiên cứu mới trong lĩnh vực tương tác người–máy dựa trên cử chỉ.

### Nhận xét bổ sung

Nếu tóm lại giá trị kỹ thuật của bài báo trong vài ý, có thể nói:

- **Chia nhỏ bài toán là chìa khoá.** Thay vì huấn luyện một mô hình khổng lồ làm tất cả, nhóm tác giả tách thành hai mô hình nhỏ chuyên biệt, mỗi mô hình giải quyết một bài toán dễ hơn nhiều.
- **Dùng tính chất bất biến của bài toán để giảm chi phí.** Quan sát rằng lòng bàn tay gần như là vật thể cứng cho phép dùng khung bao vuông và giảm số anchor 3–5 lần.
- **Khai thác tính liên tục thời gian.** Việc suy vị trí từ khung hình trước giúp bỏ qua bộ phát hiện trên đa số khung hình — đây là nguồn tiết kiệm tính toán lớn nhất của cả hệ thống.
- **Dữ liệu tổng hợp cho những nhãn con người không gán được.** Toàn bộ khả năng ước lượng độ sâu đến từ ảnh render, thứ mà không người gán nhãn nào có thể tạo ra chính xác.

---

## Phụ lục A — Bảng đối chiếu thuật ngữ

| Tiếng Anh | Tiếng Việt | Giải thích ngắn |
|---|---|---|
| Hand tracking | Theo dõi bàn tay | Xác định và bám theo vị trí, tư thế bàn tay qua các khung hình. |
| Palm detector | Bộ phát hiện lòng bàn tay | Mô hình tìm vị trí lòng bàn tay trên toàn khung hình. |
| Hand landmark model | Mô hình điểm mốc bàn tay | Mô hình hồi quy toạ độ 21 khớp trong vùng ảnh đã cắt. |
| Landmark | Điểm mốc / điểm khớp | Điểm đặc trưng trên bàn tay (đầu ngón, khớp, cổ tay...). |
| Oriented bounding box | Khung bao có định hướng | Khung chữ nhật có góc xoay bám theo hướng bàn tay. |
| Anchor | Khung neo | Các khung tham chiếu định sẵn mà bộ phát hiện dự đoán độ lệch so với chúng. |
| Single-shot detector | Bộ phát hiện một lượt | Kiến trúc phát hiện vật thể chỉ cần một lần truyền xuôi qua mạng. |
| Encoder–decoder | Bộ mã hoá – giải mã | Kiến trúc nén đặc trưng rồi khôi phục độ phân giải để giữ chi tiết nhỏ. |
| Feature Pyramid Network (FPN) | Mạng kim tự tháp đặc trưng | Kiến trúc kết hợp đặc trưng ở nhiều tỷ lệ khác nhau. |
| Focal loss | Hàm mất mát tiêu điểm | Hàm mất mát giảm trọng số mẫu dễ, tập trung vào mẫu khó. |
| Cross entropy loss | Hàm mất mát entropy chéo | Hàm mất mát phân loại tiêu chuẩn. |
| Non-maximum suppression | Triệt tiêu không cực đại | Kỹ thuật loại bỏ các khung bao trùng lặp. |
| Average Precision (AP) | Độ chính xác trung bình | Thước đo chất lượng của bài toán phát hiện vật thể. |
| MSE (Mean Squared Error) | Sai số bình phương trung bình | Thước đo sai lệch toạ độ dự đoán so với nhãn thật. |
| Ablation study | Nghiên cứu loại bỏ | Thí nghiệm bỏ bớt từng thành phần để đo đóng góp của nó. |
| Data augmentation | Tăng cường dữ liệu | Biến đổi ảnh huấn luyện (xoay, co giãn…) để tăng độ đa dạng. |
| Synthetic data | Dữ liệu tổng hợp | Ảnh do máy tính render thay vì chụp thật. |
| Blendshape | Dạng biến hình | Tập biến dạng hình học được pha trộn để tạo chuyển động chi tiết. |
| Relative depth | Độ sâu tương đối | Thứ tự xa–gần giữa các khớp, không phải khoảng cách tuyệt đối. |
| Handedness | Tay trái / tay phải | Phân loại nhị phân xác định bàn tay nào đang được theo dõi. |
| Inter-frame jitter | Rung giật giữa các khung hình | Hiện tượng điểm mốc nhảy loạn giữa các khung hình liên tiếp. |
| Calculator (MediaPipe) | Bộ tính toán | Đơn vị xử lý mô-đun trong đồ thị MediaPipe. |
| Inference | Suy luận | Quá trình chạy mô hình đã huấn luyện để ra dự đoán. |

---

## Phụ lục B — Danh sách hình trong bài báo gốc

Bài báo gốc có bảy hình minh hoạ. Dưới đây là nội dung từng hình để bạn đối chiếu khi đọc bản PDF gốc:

- **Hình 1.** Kết quả theo dõi bàn tay được kết xuất: các điểm mốc bàn tay với độ sâu tương đối thể hiện bằng các sắc độ khác nhau, cùng ảnh chụp theo dõi nhiều bàn tay thời gian thực trên Pixel 3.
- **Hình 2.** Sơ đồ kiến trúc của mô hình phát hiện lòng bàn tay.
- **Hình 3.** Kiến trúc mô hình điểm mốc bàn tay với ba đầu ra dùng chung một bộ trích xuất đặc trưng, mỗi đầu ra được huấn luyện bằng tập dữ liệu tương ứng.
- **Hình 4.** Ví dụ về các tập dữ liệu: ảnh đời thực đã gán nhãn (hàng trên) và ảnh bàn tay tổng hợp được render kèm nhãn chuẩn (hàng dưới).
- **Hình 5.** Cách đầu ra của mô hình điểm mốc điều khiển thời điểm kích hoạt mô hình phát hiện, hiện thực bằng các khối đồng bộ hoá của MediaPipe.
- **Hình 6.** Ảnh chụp màn hình hệ thống nhận dạng cử chỉ thời gian thực với ngữ nghĩa cử chỉ được hiển thị.
- **Hình 7.** Ví dụ hiệu ứng AR thời gian thực dựa trên khung xương bàn tay dự đoán, theo phong cách đèn neon.

---

## Phụ lục C — Về phần tài liệu tham khảo

Bài báo gốc trích dẫn 17 tài liệu. Các nhóm chủ đề chính bao gồm: BlazeFace (mô hình phát hiện khuôn mặt thời gian thực trên di động), tài liệu về tính năng theo dõi bàn tay của Oculus Quest, các công trình ước lượng tư thế bàn tay 3D bền vững, tài liệu backend GPU của TensorFlow Lite, Feature Pyramid Networks, Focal Loss, SSD (*Single Shot MultiBox Detector*), các bài báo về khung MediaPipe, công trình về hình học bề mặt khuôn mặt, cùng các nghiên cứu trước đây về nhận dạng cử chỉ dựa trên cảm biến chiều sâu.

Danh sách trích dẫn đầy đủ với thông tin xuất bản chi tiết có tại trang cuối của bản PDF gốc trên arXiv.

---

*Nguồn: Fan Zhang và cộng sự, "MediaPipe Hands: On-device Real-time Hand Tracking", arXiv:2006.10214, Google Research, 2020. Bản quyền thuộc về các tác giả. Tài liệu này là bản diễn giải phục vụ mục đích học tập và nghiên cứu.*
