# Kiểm tra dữ liệu p02 (buổi `data/raw/2026-11-07`)

*2026-11-07.* p02 quay 20 lần, mỗi cử chỉ 5 lần. p02 sẽ không quay lại, nên người dùng
giao: lần nào dùng được thì giữ, còn lại bỏ. **Giữ 3 lần, chuyển 17 lần vào `rejected/`**
bằng `selfdata.reject`. Không file nào bị xoá.

## Vì sao phần lớn không dùng được

- **p02 làm đi làm lại trong một lần quay.** Zoom là mở–chụm–mở, 2–4 cú mỗi lần. Vuốt là
  lấy đà, vuốt, rồi kéo về.
- **Vuốt gần như không dời ngang**, chủ yếu là búng ngón.
- Việc gán nhãn lấy cú nhanh nhất làm khoảnh khắc chính, không xét chiều. Nhiều lần, cú
  nhanh nhất lại là cú quay về.
- Phép kiểm tra lúc quay báo 24/30 lần. p02 quay lại 10 lần, nhưng bấm `b` giữ 14 lần bị
  báo.

## Tiêu chí

Mỗi **đoạn học** là một cửa sổ sẽ mang nhãn cử chỉ. Các đoạn này lấy từ điểm mốc trích lại
từ video, bằng đúng hàm của bước trích, và được cắt bằng đúng `cut_windows`. Một lần quay
được giữ khi **mọi** đoạn học của nó:

1. **đi đúng chiều và đủ rõ:** độ dời ròng theo chiều cử chỉ (vuốt: cổ tay theo
   `SWIPE_LEFT_SIGN` đã đo; zoom: độ mở cái–trỏ) ít nhất bằng mức phân vị 25 của IPN cùng
   lớp. Các mức là: vuốt trái +0,10, vuốt phải +0,27, zoom in +0,34, zoom out +0,50;
2. **không chứa cú quay về:** phần kéo ngược lại sau khi đã đi xa nhất không quá nửa quãng.

Lấy đà nhẹ trước cử chỉ không bị tính lỗi: IPN cũng có, và lấy đà mạnh thì phép kiểm tra
lúc quay đã bắt.

Độ khắt khe của tiêu chí:
- trên IPN, 65–74% đoạn học đạt (vuốt trái 65%, vuốt phải 68%, zoom in 67%, zoom out 74%);
- 8 lần quay sạch của p01 ở buổi thử `thu2` đạt 7.

Tiêu chí **dùng dấu của chuyển động để loại lần quay, không phải để gán nhãn**; cách gán nhãn
không đổi. Đây là lựa chọn của Claude khi người dùng giao việc chọn.

## Kết quả

| Lần quay | Quyết định | Độ dời ròng các đoạn học | Lý do |
|---|---|---|---|
| swipe_left_01 | bỏ | +0,12 +0,14 +0,13 +0,02 | gần như không dời ngang (búng ngón) |
| swipe_left_02 | bỏ | −0,03 −0,52 −0,94 −1,03 | ngược chiều |
| swipe_left_03 | bỏ | +0,20 +0,05 +0,19 +0,12 | gần như không dời ngang |
| swipe_left_04 | bỏ | −0,03 −0,01 −0,12 | ngược chiều |
| swipe_left_05 | bỏ | −0,14 −0,14 +0,00 +0,10 | ngược chiều |
| swipe_right_01 | bỏ | +0,01 −0,12 −0,27 −0,25 | ngược chiều |
| swipe_right_02 | bỏ | −0,21 −0,49 −0,48 | ngược chiều |
| swipe_right_03 | bỏ | +0,25 +0,21 −0,00 +0,17 | gần như không dời ngang, có cú kéo về |
| **swipe_right_04** | **giữ** | +0,40 +0,65 +0,50 +0,35 | |
| swipe_right_05 | bỏ | −0,21 +0,08 −0,16 | ngược chiều |
| zoom_in_01 | bỏ | −1,71 −2,08 −2,05 −1,36 | ngược chiều: neo vào cú chụm |
| **zoom_in_02** | **giữ** | +1,75 +1,82 +1,74 +1,53 | lúc quay bị báo "chưa rõ" vì có cú mở thứ hai, **cùng chiều**, nên không làm sai nhãn |
| zoom_in_03 | bỏ | +1,80 +1,67 +0,06 | đoạn cuối chứa cú chụm lại |
| **zoom_in_04** | **giữ** | +1,40 +1,83 +1,76 +1,78 | |
| zoom_in_05 | bỏ | +1,74 +1,79 +1,48 +0,39 | đoạn cuối chứa cú chụm lại |
| zoom_out_01 | bỏ | −1,87 −2,05 −2,06 −1,93 | ngược chiều: neo vào cú mở |
| zoom_out_02 | bỏ | +1,75 +0,46 +0,13 | hai đoạn chứa cú mở lại |
| zoom_out_03 | bỏ | −1,62 −1,95 −2,16 −2,08 | ngược chiều |
| zoom_out_04 | bỏ | −0,87 −1,56 −1,76 −1,76 | ngược chiều |
| zoom_out_05 | bỏ | +1,98 +1,86 +0,91 | đoạn cuối chứa cú mở lại (kéo về 0,98, quá nửa quãng 1,89) |

Tổng hợp:
- **Bỏ 17 lần:** 10 lần ngược chiều; 3 lần vuốt gần như không dời ngang; 4 lần có đoạn học
  chứa cú quay về.
- **Giữ 3 lần, 12 đoạn học:** 1 vuốt phải, 2 zoom in. p02 không còn vuốt trái hay zoom out.
  Vì vậy p02 chỉ nên vào phía **học** (`real_tune`), không dùng để chấm.

Các bước kiểm tra nằm trong thư mục nháp của phiên làm việc; con số trong bảng trên chính là
kết quả của chúng. Khi làm bước trích dữ liệu tự quay, tiêu chí này nên được viết vào
`src/` và áp cho mọi người, kể cả p01.
