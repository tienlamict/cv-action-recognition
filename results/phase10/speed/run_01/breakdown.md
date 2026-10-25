| model | light | component | ms_per_frame | share_of_processing | share_of_loop |
|---|---|---|---|---|---|
| rules | dim | camera | 17.31 |  | 0.5174 |
| rules | dim | color | 0.3399 | 0.02106 | 0.01016 |
| rules | dim | mediapipe | 12.74 | 0.7893 | 0.3809 |
| rules | dim | window | 0.2424 | 0.01501 | 0.007246 |
| rules | dim | model | 0.002289 | 0.0001418 | 6.844e-05 |
| rules | dim | fsm | 0.001078 | 6.677e-05 | 3.222e-05 |
| rules | dim | draw | 2.744 | 0.17 | 0.08203 |
| rules | dim | other | 0.07116 | 0.004409 | 0.002128 |
| rf | dim | camera | 17.93 |  | 0.538 |
| rf | dim | color | 0.3533 | 0.02294 | 0.0106 |
| rf | dim | mediapipe | 11.75 | 0.763 | 0.3525 |
| rf | dim | window | 0.2508 | 0.01629 | 0.007526 |
| rf | dim | model | 0.2757 | 0.0179 | 0.008272 |
| rf | dim | fsm | 0.001131 | 7.343e-05 | 3.393e-05 |
| rf | dim | draw | 2.672 | 0.1735 | 0.08016 |
| rf | dim | other | 0.0978 | 0.006351 | 0.002934 |

- Máy đo: Intel64 Family 6 Model 140 Stepping 1, GenuineIntel, 8 luồng logic, Windows-10-10.0.26300-SP0; camera 640×480 @ 30 FPS.
- Ánh sáng: dim. Bỏ 3 s đầu; FPS thấp là phân vị 1% của FPS tức thời.
- share_of_processing: phần trăm thời gian xử lý — mọi khâu trừ lúc chờ camera; spec_share ở bảng speed là tổng năm khâu của SPEC trên thời gian đó.
