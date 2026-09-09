# Kịch bản thuyết trình — Báo cáo buổi 1 (10/09/2026)

**Đề tài:** Nhận dạng hành động người thời gian thực dựa trên ước lượng tư thế
**Nội dung buổi 1:** Lý do lựa chọn đề tài và kế hoạch thực hiện
**Số slide:** 8
**Thời lượng trình bày:** khoảng 12 phút, chưa tính hỏi đáp

---

## Cách dùng file này

Mỗi slide có bốn phần:

- **Mục tiêu** — slide này cần người nghe hiểu điều gì
- **Lời thoại** — nói gần như nguyên văn được; không cần học thuộc, nhưng nên giữ đúng ý và đúng thứ tự
- **Điểm nhấn** — chỗ cần dừng lại, chỉ tay vào slide, hoặc nhấn giọng
- **Câu chuyển** — câu cuối để bắc cầu sang slide sau, giúp bài nói liền mạch

Phần cuối file có bảng phân bổ thời gian, danh sách câu hỏi có thể gặp, và những điều nên tránh nói.

---

## Slide 1 — Trang bìa

**Mục tiêu:** giới thiệu đề tài và nói rõ buổi hôm nay báo cáo cái gì.

**Thời lượng:** 30 giây

**Lời thoại:**

> Em chào thầy cô. Em xin trình bày buổi báo cáo đầu tiên của đồ án chuyên ngành.
>
> Đề tài của em là *Nhận dạng hành động người thời gian thực dựa trên ước lượng tư thế*. Nói ngắn gọn, hệ thống sẽ nhìn qua webcam và cho biết người trước máy đang làm gì, ngay khi họ đang làm.
>
> Buổi hôm nay em chưa có kết quả thực nghiệm. Em xin trình bày hai việc: thứ nhất là vì sao em chọn đề tài này, và thứ hai là kế hoạch thực hiện từ nay đến ngày 12 tháng 11, gắn với năm buổi báo cáo tiến độ còn lại.

**Điểm nhấn:** nói rõ ngay từ đầu rằng buổi này là về kế hoạch, để thầy cô không chờ đợi kết quả thực nghiệm.

**Câu chuyển:** *"Trước hết, em xin nói về lý do chọn đề tài."*

---

## Slide 2 — Vì sao chọn đề tài này

**Mục tiêu:** người nghe thấy đề tài vừa có ý nghĩa thực tế, vừa vừa sức trong 9 tuần.

**Thời lượng:** 2 phút

**Lời thoại:**

> Bài toán đặt ra là: cho một luồng video từ webcam, xác định liên tục theo thời gian rằng người trong khung hình đang thực hiện hành động nào. Điểm quan trọng là *liên tục* — hệ thống phải trả lời ngay trong lúc hành động đang diễn ra, chứ không phải xem xong cả đoạn video rồi mới kết luận.
>
> Em chọn đề tài này vì bốn lý do.
>
> **Thứ nhất, ứng dụng thực tế rất rõ.** Cùng một hệ thống này có thể dùng để giám sát an toàn lao động, phát hiện người cao tuổi bị ngã trong nhà, làm giao diện điều khiển bằng cử chỉ, hoặc phân tích động tác trong thể thao. Trong đó phát hiện ngã là ứng dụng em thấy có giá trị nhất, vì nó liên quan trực tiếp đến an toàn tính mạng.
>
> **Thứ hai, đề tài đi trọn một chuỗi kiến thức thị giác máy tính.** Nó bắt đầu từ ảnh số và video, qua ước lượng tư thế người, đến biểu diễn đặc trưng, rồi mô hình chuỗi thời gian, và kết thúc ở đánh giá phân loại. Đây là năm khối kiến thức nền của lĩnh vực, và đề tài buộc em phải đi qua đủ cả năm chứ không thể bỏ khối nào.
>
> **Thứ ba, mọi khâu đều kiểm chứng được bằng mắt.** Đây là lý do em thấy quan trọng nhất về mặt thực hành. Khi kết quả sai, em chỉ cần vẽ khung xương đè lên video là biết ngay lỗi nằm ở khâu ước lượng tư thế hay ở mô hình phân loại. Nhiều đề tài học máy khác không có được điều này — mô hình sai mà không nhìn thấy sai ở đâu.
>
> **Thứ tư, đề tài khả thi trong 9 tuần với điều kiện hiện có.** Hệ thống chạy trên laptop Windows dùng CPU, GPU RTX 3050 8GB

**Điểm nhấn:**

- Lý do 3 là chỗ nên nhấn giọng — nó cho thấy bạn nghĩ đến việc gỡ lỗi chứ không chỉ nghĩ đến ý tưởng.
- Lý do 4 trả lời trước câu hỏi "liệu có kịp không" mà hội đồng gần như chắc chắn sẽ nghĩ tới.

**Câu chuyển:** *"Về mặt kỹ thuật, hệ thống được tổ chức thành một chuỗi sáu khâu. Em xin trình bày ở slide tiếp theo."*

---

## Slide 3 — Luồng xử lý của hệ thống

**Mục tiêu:** người nghe hình dung được hệ thống chạy như thế nào, và biết phần nào là tự làm, phần nào dùng thư viện.

**Thời lượng:** 2 phút 30 giây — đây là slide kỹ thuật duy nhất, nên dành thời gian cho nó

**Lời thoại:**

> Hệ thống gồm sáu khâu nối tiếp nhau, chạy lặp lại cho từng khung hình.
>
> **Khâu 1 — thu khung hình.** OpenCV mở webcam và đọc từng khung hình, khoảng 30 khung mỗi giây. Đây cũng là chỗ em đặt bộ đếm FPS, vì tên đề tài có chữ *thời gian thực* nên em phải đo được con số đó chứ không thể nói suông.
>
> **Khâu 2 — ước lượng tư thế.** Em chuyển ảnh sang hệ màu RGB rồi đưa vào MediaPipe Pose. Mô hình trả về 33 điểm khớp trên cơ thể, kèm theo điểm tin cậy cho từng điểm. Đây là khâu bản lề: từ đây trở đi hệ thống không còn làm việc với pixel nữa, chỉ còn làm việc với tọa độ.
>
> Chỗ này em xin nói thêm một chút vì nó là ý tưởng cốt lõi của đề tài. Một khung hình màu độ phân giải 1280 nhân 720 có hơn hai triệu bảy trăm nghìn con số. Sau khâu 2, nó chỉ còn khoảng một trăm con số. Nhẹ hơn khoảng hai chục nghìn lần, và đó chính là lý do hệ thống chạy được thời gian thực trên CPU.
>
> **Khâu 3 — chuẩn hóa tọa độ.** Tọa độ thô mà MediaPipe trả về là vị trí trên màn hình. Nếu đưa thẳng vào mô hình, mô hình sẽ học vị trí đứng chứ không học hành động. Nên em dời gốc tọa độ về trung điểm hông để bỏ ảnh hưởng của vị trí, rồi chia cho chiều dài thân để bỏ ảnh hưởng của khoảng cách tới camera. Sau bước này, cùng một tư thế đứng gần hay đứng xa đều cho ra bộ số gần như nhau.
>
> **Khâu 4 — hàng đợi 30 khung hình.** Hệ thống giữ lại 30 khung gần nhất, tương đương khoảng một giây. Mỗi khung mới đẩy khung cũ nhất ra, gọi là cửa sổ trượt. Bước này biến bài toán từ *nhìn một tư thế* thành *nhìn một đoạn chuyển động*. Nó cần thiết vì có những hành động không thể phân biệt bằng một khung hình đơn lẻ — ví dụ ngồi xuống và đứng dậy đi qua đúng những tư thế giống nhau, chỉ khác thứ tự thời gian.
>
> **Khâu 5 — mô hình phân loại chuỗi.** Mô hình nhận cả cửa sổ 30 khung và trả về xác suất cho từng hành động. Giai đoạn đầu em dùng rừng ngẫu nhiên trên đặc trưng thủ công, giai đoạn sau em thay bằng mạng LSTM và so sánh hai bên.
>
> **Khâu 6 — kết xuất nhãn.** Em chọn nhãn có xác suất cao nhất, rồi làm mượt bằng cách bỏ phiếu trên 5 dự đoán gần nhất để nhãn không nhảy loạn, sau đó vẽ nhãn và độ tin cậy đè lên khung hình.
>
> Một điểm em muốn nói rõ: ba khâu 1, 2 và 6 dùng thư viện có sẵn. Ba khâu 3, 4 và 5 là phần em tự viết, và cũng là ba khâu chứa trọng tâm kiến thức của đồ án.

**Điểm nhấn:**

- Chỉ tay lần lượt vào từng ô số trên sơ đồ khi nói.
- Con số **2.764.800 → khoảng 100** nên nói chậm, đây là con số dễ nhớ nhất trong cả bài.
- Câu cuối về "khâu nào tự viết" là câu quan trọng nhất slide — nó trả lời trước câu hỏi *"vậy em làm gì, hay chỉ gọi thư viện?"*.

**Câu chuyển:** *"Đó là hệ thống cần xây. Phần còn lại em xin trình bày kế hoạch để đi từ chỗ chưa có gì đến hệ thống đó, trong 9 tuần."*

---

## Slide 4 — Buổi 2 · 24/09 · Ảnh số và ước lượng tư thế

**Mục tiêu:** giới thiệu cấu trúc chung của kế hoạch, đồng thời trình bày giai đoạn 1.

**Thời lượng:** 1 phút 45 giây — dài hơn các mốc sau vì phải giải thích cấu trúc

**Lời thoại:**

> Kế hoạch của em chia thành năm giai đoạn, ứng với năm buổi báo cáo còn lại. Mỗi giai đoạn em trình bày trên một slide, với cùng một cấu trúc ba cột.
>
> Cột trái là **lý thuyết em tìm hiểu** trong giai đoạn đó. Cột giữa là **phần thực hiện**. Cột phải là **thứ em sẽ mang đến buổi báo cáo** ngày đó. Ba cột này chạy song song, nghĩa là lý thuyết em học ở mỗi giai đoạn chính là lý thuyết mà phần code của giai đoạn đó cần dùng, chứ không phải học lý thuyết trước rồi mới làm sau.
>
> Giai đoạn đầu, từ 11 đến 24 tháng 9, em tìm hiểu tầng 1 và tầng 2: ảnh số, video và ước lượng tư thế. Cụ thể là pixel và kênh màu, vì sao OpenCV đọc ảnh theo thứ tự BGR trong khi MediaPipe cần RGB; khái niệm FPS và độ phân giải; keypoint và bản đồ nhiệt; sự khác nhau giữa hai hướng tiếp cận top-down và bottom-up, và BlazePose của MediaPipe thuộc nhóm nào.
>
> Về thực hiện, em cài môi trường trên Windows, viết chương trình đọc webcam và vẽ 33 khớp đè lên khung hình, hiển thị FPS ở góc màn hình. Sau đó em làm một loạt thí nghiệm để tìm giới hạn của mô hình: che một tay, xoay lưng lại, đứng thật xa, xem mô hình hỏng ở đâu.
>
> Đến ngày 24 tháng 9, em sẽ mang đến ba thứ: video khung xương bám theo người kèm số FPS thực đo, một bản tóm tắt lý thuyết ước lượng tư thế, và danh sách các trường hợp mô hình đoán sai kèm ảnh minh họa.

**Điểm nhấn:**

- Phần giải thích ba cột chỉ nói một lần ở slide này, các slide sau không lặp lại.
- Nhấn ý "học lý thuyết đúng lúc cần dùng" — đây là lý do kế hoạch được thiết kế song song thay vì tuần tự.

**Câu chuyển:** *"Giai đoạn hai."*

---

## Slide 5 — Buổi 3 · 08/10 · Biểu diễn khung xương

**Mục tiêu:** cho thấy giai đoạn này là phần code cốt lõi và có cách kiểm chứng rõ ràng.

**Thời lượng:** 1 phút 15 giây

**Lời thoại:**

> Giai đoạn hai, từ 25 tháng 9 đến 8 tháng 10, em tìm hiểu tầng 3: cách biến tọa độ thô thành đặc trưng dùng được.
>
> Nội dung gồm: vì sao tọa độ pixel thô không dùng được; chuẩn hóa tịnh tiến bằng cách dời gốc về trung điểm hông; chuẩn hóa tỉ lệ bằng cách chia cho chiều dài thân; cách tính góc khớp từ ba điểm và vì sao góc ổn định hơn tọa độ; và vận tốc khớp tính bằng sai phân giữa các khung hình.
>
> Phần thực hiện là viết module tiền xử lý: hàm chuẩn hóa 33 điểm và bỏ 10 điểm trên mặt vì chúng nhiễu và không mang thông tin về hành động; hàm tính góc khuỷu, gối, hông và vận tốc cổ tay, mắt cá.
>
> Điều em muốn nhấn ở giai đoạn này là cách kiểm chứng. Em sẽ đứng cùng một tư thế ở hai khoảng cách khác nhau tới camera, và kiểm tra rằng hai vector đặc trưng thu được gần như trùng nhau. Nếu chúng khác nhau nhiều thì chuẩn hóa của em sai, và em phải sửa trước khi đi tiếp.
>
> Ngày 8 tháng 10 em sẽ mang đến module tiền xử lý chạy được, bảng so sánh vector ở hai khoảng cách để chứng minh chuẩn hóa đúng, và đồ thị đặc trưng theo thời gian của vài hành động.

**Điểm nhấn:** ý "kiểm chứng bằng số liệu chứ không tin là đúng" — nếu chỉ nhớ một câu ở slide này thì nhớ câu đó.

**Câu chuyển:** *"Giai đoạn ba là giai đoạn quan trọng nhất trong kế hoạch."*

---

## Slide 6 — Buổi 4 · 22/10 · Dữ liệu và mô hình đầu tiên

**Mục tiêu:** đây là mốc an toàn của cả đồ án — phải nói rõ điều đó.

**Thời lượng:** 1 phút 30 giây

**Lời thoại:**

> Giai đoạn ba, từ 9 đến 22 tháng 10. Lý thuyết em tìm hiểu là tầng 5, đánh giá phân loại: cửa sổ trượt và cách chọn độ dài cửa sổ, cách đọc ma trận nhầm lẫn, precision và recall của từng lớp, và khái niệm rò rỉ dữ liệu.
>
> Chỗ này em xin nói kỹ hơn một chút, vì đây là cái bẫy lớn nhất của đề tài. Các cửa sổ chồng lấn của cùng một lần diễn gần như giống hệt nhau. Nếu em chia tập huấn luyện và tập kiểm thử một cách ngẫu nhiên theo cửa sổ, thì những cửa sổ gần giống nhau sẽ nằm ở cả hai tập. Mô hình chỉ cần ghi nhớ là đoán đúng, và em sẽ nhận được con số 99 phần trăm hoàn toàn giả. Cách làm đúng là chia theo người: toàn bộ video của một hoặc hai người chỉ nằm ở tập kiểm thử, không xuất hiện trong tập huấn luyện.
>
> Phần thực hiện: em quay 6 hành động với 3 đến 5 người diễn, mỗi hành động lặp 8 đến 10 lần. Sáu hành động gồm ba trạng thái kéo dài là đứng yên, đi bộ tại chỗ, vẫy tay; và ba chuyển tiếp là ngồi xuống ghế, đứng dậy khỏi ghế, và ngã xuống sàn. Sau đó em trích khung xương một lần rồi lưu ra tệp để tái sử dụng, cắt cửa sổ 30 khung, tính khoảng 30 đến 40 đặc trưng cho mỗi cửa sổ, và huấn luyện rừng ngẫu nhiên.
>
> Đến ngày 22 tháng 10 em sẽ có một hệ thống phân loại chạy được từ đầu đến cuối. Đây là mốc an toàn của cả đồ án: từ thời điểm này trở đi em đã có sản phẩm hoàn chỉnh để nộp, và hai giai đoạn cuối là cải tiến chứ không phải làm mới từ đầu.

**Điểm nhấn:**

- Đoạn về rò rỉ dữ liệu nên nói chậm — nó cho thấy bạn hiểu cách đánh giá trung thực, và là điểm cộng lớn với hội đồng.
- Câu cuối về mốc an toàn là câu trả lời sẵn cho câu hỏi rủi ro tiến độ. Nói dứt khoát.
- Đây cũng là chỗ duy nhất trong bài liệt kê đủ sáu hành động, nên đừng bỏ qua.

**Câu chuyển:** *"Giai đoạn bốn."*

---

## Slide 7 — Buổi 5 · 05/11 · Mô hình chuỗi thời gian và demo

**Mục tiêu:** cho thấy bạn không mặc định học sâu tốt hơn, mà đặt nó vào một phép so sánh có kiểm soát.

**Thời lượng:** 1 phút 30 giây

**Lời thoại:**

> Giai đoạn bốn, từ 23 tháng 10 đến 5 tháng 11. Lý thuyết là tầng 4: mô hình chuỗi thời gian. Em tìm hiểu vì sao mạng thông thường khó xử lý chuỗi có độ dài thay đổi, khái niệm trạng thái ẩn trong RNN, vấn đề tiêu biến gradient, và trực giác về ba cổng của LSTM. Em cũng học PyTorch ở mức đủ dùng: tensor, autograd, và cấu trúc một vòng lặp huấn luyện.
>
> Phần thực hiện: em huấn luyện một mạng LSTM hai lớp, đầu vào là 23 khớp nhân 2 tọa độ, kích thước ẩn 128, dropout 0.3. Em khảo sát ba độ dài cửa sổ là 15, 30 và 45 khung hình để xem độ dài nào phù hợp nhất. Sau đó em so sánh với rừng ngẫu nhiên trên đúng cách chia tập, rồi ghép demo thời gian thực.
>
> Ở đây em muốn nói trước một điều. Nếu LSTM không thắng rừng ngẫu nhiên thì đó không phải là thất bại. Với sáu hành động khác biệt rõ về hình học và bộ dữ liệu chỉ vài nghìn mẫu, đặc trưng thủ công tốt hoàn toàn có thể ngang ngửa với học sâu. Nếu điều đó xảy ra, em sẽ báo cáo đúng như vậy và phân tích lý do — đó cũng là một kết luận có giá trị.
>
> Ngày 5 tháng 11 em sẽ mang đến bảng so sánh hai mô hình, đồ thị quá trình huấn luyện, số liệu FPS và độ trễ nhận dạng, và chạy demo trực tiếp trước thầy cô.

**Điểm nhấn:** đoạn "nếu LSTM không thắng thì đó không phải thất bại" — nói bình tĩnh, không phòng thủ. Đây là dấu hiệu của tư duy nghiên cứu.

**Câu chuyển:** *"Và giai đoạn cuối."*

---

## Slide 8 — Buổi 6 · 12/11 · Hoàn thiện và nộp

**Mục tiêu:** khép lại kế hoạch, cho thấy báo cáo không bị dồn vào tuần chót.

**Thời lượng:** 1 phút

**Lời thoại:**

> Giai đoạn cuối, từ 6 đến 12 tháng 11. Em hệ thống hóa ghi chú của cả năm tầng lý thuyết thành chương cơ sở lý thuyết, đối chiếu kết quả thực nghiệm với phần lý thuyết đã trình bày, và nêu hướng phát triển: mạng tích chập đồ thị ST-GCN, xử lý nhiều người trong khung hình, và hình học ba chiều — kèm giải thích vì sao những hướng đó nằm ngoài phạm vi lần này.
>
> Phần thực hiện là ráp báo cáo, dọn repo và viết README để người khác chạy lại được từ đầu, quay video demo, và tập trình bày.
>
> Em xin nhấn mạnh một điểm về cách sắp xếp: nội dung báo cáo được viết dần ngay từ buổi 24 tháng 9. Mỗi buổi báo cáo tiến độ đóng góp một phần vào báo cáo cuối — phần lý thuyết ước lượng tư thế thành một mục, phần chuẩn hóa thành một mục, và cứ như vậy. Giai đoạn cuối chỉ ráp lại và dọn dẹp, chứ em không dồn viết vào tuần chót.
>
> Đó là toàn bộ kế hoạch của em. Em xin cảm ơn thầy cô, và rất mong nhận được góp ý ạ.

**Điểm nhấn:** ý "báo cáo viết dần từ đầu" là câu chốt tốt — nó cho thấy kế hoạch được nghĩ đến tận khâu cuối.

---

## Bảng phân bổ thời gian

| Slide | Nội dung | Thời lượng | Cộng dồn |
|---|---|---|---|
| 1 | Trang bìa | 0:30 | 0:30 |
| 2 | Vì sao chọn đề tài | 2:00 | 2:30 |
| 3 | Luồng xử lý của hệ thống | 2:30 | 5:00 |
| 4 | Buổi 2 · 24/09 | 1:45 | 6:45 |
| 5 | Buổi 3 · 08/10 | 1:15 | 8:00 |
| 6 | Buổi 4 · 22/10 | 1:30 | 9:30 |
| 7 | Buổi 5 · 05/11 | 1:30 | 11:00 |
| 8 | Buổi 6 · 12/11 | 1:00 | 12:00 |

**Nếu bị yêu cầu rút ngắn còn 7–8 phút:** giữ nguyên slide 2 và 3, rút mỗi slide mốc xuống còn hai câu — một câu về lý thuyết, một câu về sản phẩm mang đi báo cáo. Bỏ các đoạn giải thích thêm ở slide 3 và slide 6.

---

## Câu hỏi có thể gặp và hướng trả lời

**1. Vì sao dùng khung xương mà không đưa thẳng video vào mạng nơ-ron?**

Vì ba lý do. Thứ nhất là khối lượng dữ liệu: hơn 2,7 triệu con số mỗi khung hình so với khoảng 100, chênh nhau khoảng hai chục nghìn lần, nên khung xương chạy được thời gian thực trên CPU. Thứ hai là dữ liệu: mạng xử lý trực tiếp video cần lượng dữ liệu huấn luyện lớn hơn nhiều so với vài nghìn mẫu em tự quay. Thứ ba là khả năng gỡ lỗi: với khung xương em nhìn được ngay lỗi nằm ở đâu.

Cái giá phải trả là khung xương vứt bỏ ngoại hình và vật thể trong cảnh, nên nó không phân biệt được "uống nước" với "đánh răng". Đó chính là lý do sáu hành động em chọn đều khác nhau rõ rệt về hình học thân thể.

**2. Vì sao chỉ có 6 hành động, sao không nhiều hơn?**

Vì mỗi hành động cần 3 đến 5 người diễn, mỗi người lặp 8 đến 10 lần, nên chi phí quay dữ liệu tăng tuyến tính theo số hành động. Với quỹ 9 tuần, sáu hành động là con số cân bằng giữa khối lượng công việc và độ phong phú. Sáu hành động này cũng được chọn có chủ ý: ba trạng thái kéo dài và ba chuyển tiếp, trong đó cặp ngồi xuống và đứng dậy buộc mô hình phải học được chiều thời gian.

**3. Nếu MediaPipe ước lượng tư thế sai thì sao?**

Sai ở khâu 2 thì mọi khâu sau đều sai, đó là rủi ro thật. Em xử lý theo ba cách: dùng điểm tin cậy của từng khớp để lọc bỏ khung hình xấu; cố định điều kiện quay để toàn thân luôn nằm trong khung hình; và trong giai đoạn 1 em chủ động thí nghiệm để lập danh sách các trường hợp mô hình hỏng, từ đó biết giới hạn của hệ thống và ghi vào báo cáo.

**4. Nếu đến ngày 5 tháng 11 mà LSTM chưa chạy được thì sao?**

Từ ngày 22 tháng 10 em đã có hệ thống hoàn chỉnh dùng rừng ngẫu nhiên, chạy được từ webcam đến nhãn hành động. Nếu LSTM gặp trục trặc, em vẫn nộp được đồ án đúng hạn với mô hình đó, và phần LSTM trở thành nội dung phân tích về khó khăn gặp phải. Đó là lý do em xếp mô hình đơn giản trước, mô hình phức tạp sau.

**5. Đóng góp mới của đề tài là gì?**

Đề tài này không đặt mục tiêu tạo ra phương pháp mới. Mục tiêu là hiểu và triển khai đúng một chuỗi kỹ thuật đã có, đồng thời đánh giá trung thực — đặc biệt là ở khâu chia tập theo người, chỗ mà rất nhiều báo cáo làm sai và cho ra con số đẹp giả tạo. Phần so sánh giữa đặc trưng thủ công và học sâu trên chính bộ dữ liệu tự thu thập là nội dung thực nghiệm của em.

**6. Vì sao học tầng 5 (đánh giá) trước tầng 4 (LSTM)?**

Vì thứ tự học bám theo thứ tự cần dùng, chứ không theo số thứ tự tầng. Ở giai đoạn 3 em đã huấn luyện rừng ngẫu nhiên, mà để đánh giá mô hình đó em cần ma trận nhầm lẫn và cách chia tập theo người ngay lúc đó. LSTM đến giai đoạn 4 mới dùng nên học sau.

**7. Bộ dữ liệu chỉ 3–5 người thì có đủ tin cậy không?**

Chưa đủ để khẳng định hệ thống tổng quát cho mọi người dùng, và em sẽ nêu rõ hạn chế này trong báo cáo. Nhưng nó đủ để trả lời câu hỏi trọng tâm của đồ án là so sánh hai mô hình trên cùng một bộ dữ liệu, với điều kiện việc chia tập được làm đúng. Nếu còn thời gian ở giai đoạn 4, em sẽ mời thêm người diễn để mở rộng tập kiểm thử.

---

## Những điều nên tránh

- **Đừng hứa con số độ chính xác.** Chưa có dữ liệu thì mọi con số đưa ra đều là đoán, và hội đồng sẽ nhớ con số đó ở buổi sau.
- **Đừng nói "em sẽ dùng deep learning cho chính xác hơn".** Kế hoạch của bạn là *so sánh* hai mô hình, không phải mặc định một bên thắng.
- **Đừng sa vào công thức LSTM** nếu bị hỏi. Trả lời ở mức trực giác ba cổng là đủ cho buổi 1; nói chi tiết mà sai sẽ mất điểm hơn là nói vừa đủ.
- **Đừng đọc slide.** Slide đã có chữ, việc của bạn là bổ sung phần slide không viết: lý do đằng sau mỗi lựa chọn.

---

## Chuẩn bị trước buổi báo cáo

- Điền họ tên, MSSV và tên giảng viên hướng dẫn vào trang bìa
- Tập nói toàn bài ít nhất hai lần có bấm giờ
- Ghi nhớ bốn con số: **2.764.800 → ~100**, **33 điểm khớp**, **30 khung ≈ 1 giây**, **6 hành động**
- Ghi nhớ bốn mốc ngày: **24/09 · 08/10 · 22/10 · 05/11**, nộp cuối **12/11**
- Mở sẵn file slide ở chế độ Presenter View để đọc được ghi chú trong từng slide
