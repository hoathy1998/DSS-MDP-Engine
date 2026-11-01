# Nhật ký giả định

Mỗi giả định có mã, nội dung, lý do, ảnh hưởng và trạng thái. Khi đổi một giả định, thêm dòng mới chứ không xóa dòng cũ.

| Mã | Giả định | Lý do | Ảnh hưởng | Trạng thái |
|---|---|---|---|---|
| A1 | B ~ Binomial(n=3, p=0,2) trên chỉ số 0..3 → {40, 60, 80, 100} | Bài chỉ ghi "Binomial(0.2)" trên 4 giá trị | Phân phối B | mặc định, chờ Pha 2 |
| A2 | Bernoulli(p) cho xác suất p ở giá trị thứ hai | Quy ước thông thường | C, E, F, G | mặc định, chờ Pha 2 |
| A3 | Biến thể Y: `paper` | Theo bài; sẽ hiệu chỉnh | Toàn bộ kết quả | **chờ Pha 2** |
| A4 | P(D ≥ f) = 1 − Φ((f − D)/200) | Theo mục 7.2 | Doanh thu | cố định |
| A5 | Cây quyết định theo `data/decision_tree.yaml`; vector Bảng 6 theo thứ tự A..I | Đọc Fig. 8 | Kết quả cây quyết định | **chờ Pha 2** |
| A6 | Lợi nhuận thực hiện = Y(giá trị thật, f) − chi phí đã bỏ ra | Định nghĩa hợp lý nhất | Bảng 6 | cố định |
| A7 | Không cố khớp doanh thu của cây quyết định ở Bảng 5 | Số liệu của bài tự mâu thuẫn | — | cố định |
| A8 | Ví dụ nhỏ dùng giá trị đúng V = 1,0 | Bài tính sai | Kiểm thử S1 | cố định |
| A9 | Quy tắc hòa: ưu tiên quyết định cuối, rồi đến hành động chi phí thấp hơn, rồi đến thứ tự trong file | Bài không nêu | Chính sách khi hòa | mặc định |
| A1 (cập nhật) | Giữ Binomial(n=3, p=0,2) | Cùng A2 và cây Fig. 8 cho chi phí 100,06 và 1.254 trạng thái kết thúc, khớp Bảng 5; sai lệch trung bình với Fig. 7 là 0,002. Các cách đọc khác lệch rõ | Phân phối B | **đã có căn cứ** |
| A2 (cập nhật) | Giữ p ứng với giá trị thứ hai | Cùng căn cứ với A1 | C, E, F, G | **đã có căn cứ** |
| A3 (cập nhật) | `data/koffer.yaml` chép sai công thức: biến thể tên `paper` không phải công thức in trong bài. Công thức in (tr. 10) có ngoặc vuông bao cả `f − A(1−0,2G) − F − I`, tức là biến thể `margin_all`. Không biến thể nào khớp Bảng 5 | Đối chiếu ảnh trang 10; `results/calibration.csv`, `results/y_variant_search.csv` | Toàn bộ kết quả | **đã chọn, xem A3 (quyết định)** |
| A3 (quyết định) | Người dùng chọn `margin_all` (công thức in trong bài) làm mặc định và `margin_repair` (F, I tính một lần cho mỗi hợp đồng) làm đối chứng. Với sự đồng ý của người dùng, `data/koffer.yaml` đổi `default` sang `margin_all`, đổi tên `paper` thành `flat_costs`, `no_E_paper` thành `no_E_flat`; không đổi giá trị số nào | Ưu tiên tài liệu gốc; không biến thể nào khớp Bảng 5 nên không chỉnh mô hình cho khớp. So với Bảng 5: `margin_all` thấp hơn 45% (MDP) và 56% (cây); `margin_repair` cao hơn 10% và 26% | Toàn bộ kết quả | **đã chốt** |
| A5 (cập nhật) | Cây đọc theo `fig8`. Không cách đọc hoặc thứ tự cột nào giải thích được Bảng 6 (tối đa 4/9 dòng khớp), xem `docs/paper_notes.md` mục 4 | Bảng 5 và Fig. 7 xác nhận cây; Bảng 6 tự mâu thuẫn | Không dùng Bảng 6 để chọn cấu hình | **đã có căn cứ** |
| A11 | Hiệu chỉnh giải trên mô hình đã bỏ các tác vụ bắt buộc mà không gì phụ thuộc vào và Y không dùng (3 và C), rồi cộng lại chi phí và số trạng thái | Cách rút gọn chính xác, có kiểm thử; giảm trạng thái đi tới được từ 640.224 xuống 106.704 | Chỉ ảnh hưởng thời gian chạy | cố định |
| A12 | Chính sách tham lam một bước: làm các mục bắt buộc trước; giá trị của một thuộc tính chưa biết = E[max_f E[Y]] sau khi biết nó − max_f E[Y] hiện tại − chi phí của nó và các mục đứng trước chưa làm; nếu dương thì làm mục đầu tiên trên chuỗi đó, nếu không thì quyết định | Kế hoạch chỉ nêu "myopic VoI"; không tính chi phí mục đứng trước thì chính sách không bao giờ mở được α và tác vụ 2 | Chỉ ảnh hưởng chính sách đối chứng | mặc định |
| A10 | Hai giá trị Q chênh nhau không quá 1e-9 được coi là hòa và xử lý theo A9 | Tránh để sai số làm tròn số thực quyết định chính sách | Chính sách khi gần hòa; không đổi V quá 1e-9 | mặc định |
