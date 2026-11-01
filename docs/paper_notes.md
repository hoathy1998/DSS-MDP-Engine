# Ghi chú từ bài báo và các điểm không nhất quán đã phát hiện

Số trang theo bản PDF của tạp chí (DSS 151, 113632).

## 1. Những gì bài báo cung cấp

| Nội dung | Vị trí |
|---|---|
| Định nghĩa MDP: trạng thái (σ, s), hành động, ràng buộc (5)(6), phần thưởng, chuyển trạng thái | mục 5.4, tr. 7–8 |
| Ví dụ nhỏ hai thuộc tính | mục 5.3, tr. 6 |
| Tác vụ, chi phí, ràng buộc của Koffer | Bảng 3, tr. 10 |
| Miền giá trị và phân phối 9 thuộc tính | Bảng 4, tr. 10 |
| Hàm Y của Koffer, D ~ N(μ = D, σ = 200), 4 phương án | mục 7.2, tr. 10 |
| Kết quả tổng hợp MDP so với cây quyết định | Bảng 5, tr. 11 |
| Chín trường hợp | Bảng 6, tr. 12 |
| Không gian trạng thái 5⁵·3⁴·2⁵ = 8,1 triệu; 49 phút trên i5-8365U | tr. 12 |
| Cây quyết định 14 nút | Fig. 8, Phụ lục A, tr. 14 |
| Ví dụ giảm không gian trạng thái bằng cột mốc: 10 thuộc tính × 4 giá trị, từ 1.048.576 xuống 2.048 trạng thái | mục 9, tr. 13 |
| Trang demo của tác giả | https://is.ieis.tue.nl/staff/heshuis/OptimizingInformationGathering/ (chưa kiểm tra còn hoạt động không) |

Bài báo **không** công bố mã nguồn và không nêu quy tắc chọn khi các hành động hòa nhau.

## 2. Sai sót trong ví dụ nhỏ (A8)

X₁ ∈ {0, 3}, X₂ ∈ {1, 4}, mỗi giá trị có xác suất 0,5; Y = (X₂ − X₁)·f; chi phí 0,5 mỗi thuộc tính.

- Bài báo: không có thông tin thì chọn f = 1 với lợi nhuận kỳ vọng 0,5; thu thập X₂ "tăng 0,75 > 0,5" nên nên thu thập.
- Tính lại: E[X₂ − X₁] = 2,5 − 1,5 = **1,0**. Sau khi biết X₂: 0,5·2,5 + 0,5·0 = 1,25; trừ chi phí còn 0,75 < 1,0.
- Quy nạp ngược: V(gốc) = 1,0; hành động tối ưu là **quyết định f = 1 ngay**.

## 3. Bảng 5 không nhất quán (A7)

- MDP: 16.011,0 − 143,5 = 15.867,5 ≈ 15.867,6 (khớp).
- Cây quyết định: 8.125,94 − 100,06 = 8.025,88 ≠ 8.226,0.

## 4. Hàm Y và Bảng 6 (A3, A5)

- **Đính chính (Pha 2, đối chiếu ảnh tr. 10):** công thức in là Y = E·B·H·P(D ≥ f)·[f − A(1 − 0,2G) − F − I], ngoặc vuông bao cả phần chi phí. Đây là biến thể `margin_all`. Dòng `Y = E·B·H·P·f − A(1 − 0,2G) − F − I` là chép sai; biến thể này trước đây tên `paper`, nay đổi thành `flat_costs` trong `data/koffer.yaml`.
- Trường hợp 1, 3, 7, 8 có cùng bộ giá trị nhị phân (1, 1, 0) ở ba cột C, E, G, nhưng chi phí của cây là 122, 45, 45 và 207. Trường hợp 4 có cả ba cột bằng 0 mà vẫn có lãi. Vì cây chỉ rẽ nhánh theo giá trị thuộc tính, không thứ tự cột nào của C, E, G giải thích được các dòng này.
- Hiệu chỉnh đầy đủ (`results/calibration.csv`, 900 dòng): tối đa 4/9 dòng Bảng 6 khớp, chủ yếu là các dòng −45.
- Bảng 5 và Fig. 7 xác nhận cấu trúc: cây Fig. 8 với A1, A2 mặc định cho chi phí 100,06 và đúng 1.254 trạng thái kết thúc. Riêng lợi nhuận phụ thuộc Y thì không khớp: dò 108 cách đặt các số hạng chi phí (`results/y_variant_search.csv`) không có cách nào khớp đồng thời các số của Bảng 5.
- Thử nhanh 5 biến thể (có hoặc không nhân E; trừ chi phí một lần hay theo từng lần sửa chữa) trên các trường hợp 1, 2, 4, 8: **không biến thể nào khớp** lợi nhuận của Bảng 6, sai lệch có khi tới vài lần.
- Trường hợp 2 và 4 có E = 0 (nếu thứ tự cột là A..I) nhưng vẫn có lãi, trái với công thức nhân E.
- Các dòng −45 khớp đúng tổng chi phí bắt buộc (10 + 30 + 2 + 3 + 0).
- Trường hợp 1: cây quyết định cho −122 = 45 + (B 8 + H 4 + α 20 + A 10 + F 20 + G 15). Như vậy cây đã đi đường B → H → α → A → F → G → từ chối, khớp với A = 2100, F = 100, G = 0. Điều này lại mâu thuẫn với nhánh H = 1 → từ chối trong cách đọc mặc định.
- Thử mọi thứ tự cột của (C, E, G) cùng 5 cách đọc nhánh H: tối đa khớp **6/9** trường hợp. Các trường hợp 3 và 7 có E = 1 nhưng cây chỉ tốn 45, tức không kiểm tra B và H.

Kết luận tạm: có thể Bảng 6 dùng một phiên bản cây hoặc cách ghi vector khác với Fig. 8. Pha 2 sẽ ghi lại kết quả hiệu chỉnh đầy đủ.

## 5. Định nghĩa dùng trong dự án

- **Lợi nhuận thực hiện** của một kịch bản = Y(giá trị thật của mọi thuộc tính, f) − tổng chi phí các mục đã làm (A6).
- **Lợi nhuận kỳ vọng** của chính sách = trung bình có trọng số trên 16.384 kịch bản.
- **Số trạng thái kết thúc** = số trạng thái (σ, s) khác nhau tại thời điểm ra quyết định, trên mọi kịch bản có xác suất dương.
