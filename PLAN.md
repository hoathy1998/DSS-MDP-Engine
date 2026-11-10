# Kế hoạch tái hiện Voorberg et al. (2021): CMMN → MDP cho bài toán Koffer

> Bài báo: S. Voorberg, R. Eshuis, W. van Jaarsveld, G.-J. van Houtum, "Decisions for information or information for decisions? Optimizing information gathering in decision-intensive processes," *Decision Support Systems*, vol. 151, 113632, 2021.
> Bản PDF nằm ở `../Paper/`. Mọi số liệu trong `data/` được chép từ bài, có ghi số bảng/trang.

## 1. Bài toán

Bài báo chuyển một quy trình quyết định (DIP) mô hình hóa bằng CMMN thành một MDP. Giải MDP bằng quy nạp ngược cho ra chính sách cho biết tại mỗi trạng thái nên thu thập thêm thông tin nào hay nên ra quyết định. Bài báo áp dụng trên ví dụ Koffer (báo giá bảo trì linh kiện máy bay) và so sánh với cây quyết định do người quản lý xây dựng: lợi nhuận kỳ vọng 15.867,6 so với 8.226,0.

Bài báo không công bố mã nguồn. Khi kiểm tra sơ bộ, chúng ta đã phát hiện một số điểm không nhất quán (xem `docs/paper_notes.md`), nên **không kỳ vọng khớp đúng từng con số**.

## 2. Mục tiêu

1. **Tái hiện phương pháp:** dựng MDP Koffer từ Bảng 3–4, giải chính xác bằng quy nạp ngược, sinh chính sách cho mọi trạng thái.
2. **Tái hiện thực nghiệm:** so sánh MDP với cây quyết định (Fig. 8) theo các chỉ số của Bảng 5 và trên chín trường hợp của Bảng 6.
3. **Mở rộng:** thêm hai mô hình đối chứng và phân tích độ nhạy. Đây là các điểm báo cáo đã phê bình bài báo còn thiếu.
4. **Demo:** ứng dụng Streamlit mô phỏng bộ khuyến nghị (giống Fig. 6), cho phép người dùng làm khác khuyến nghị.
5. **Đầu ra cho báo cáo:** bảng, hình và một bản tóm tắt kết quả để viết mục 4.6 "Thực nghiệm tái hiện".

## 3. Tiêu chí thành công

| # | Tiêu chí | Cách kiểm tra |
|---|---|---|
| S1 | Bộ giải MDP tổng quát cho đúng ví dụ nhỏ của bài (mục 5.3): V(gốc) = 1,0, hành động tối ưu là "quyết định ngay" | `tests/test_toy.py` |
| S2 | Kỳ vọng E[Y(s,f)] tính theo công thức rút gọn bằng kết quả duyệt toàn bộ kịch bản | `tests/test_information_structure.py` |
| S3 | V(gốc) của MDP bằng lợi nhuận kỳ vọng khi mô phỏng chính sách MDP trên toàn bộ 16.384 kịch bản (sai số < 1e-6) | `tests/test_consistency.py` |
| S4 | Cây quyết định chép lại được kiểm tra với 9 trường hợp của Bảng 6; mọi chỗ không khớp được giải thích trong `docs/assumptions.md` | `tests/test_decision_tree.py` |
| S5 | Tái hiện đúng **xu hướng** của Bảng 5: MDP có lợi nhuận kỳ vọng cao hơn, ít trạng thái kết thúc hơn và chi phí thu thập cao hơn cây quyết định | `results/table5_repro.csv` |
| S6 | Ghi lại số trạng thái, thời gian giải, bộ nhớ, cấu hình máy | `results/runtime.json` |
| S7 | Mọi giả định đều có mã (A1, A2, …) trong `docs/assumptions.md` và được nhắc trong tóm tắt kết quả | rà soát thủ công |

Không bắt buộc khớp đúng con số. Báo cáo sẽ ghi chênh lệch tương đối so với bài báo.

## 4. Phạm vi

**Trong phạm vi**
- Ví dụ nhỏ của bài (2 thuộc tính) và mô hình Koffer đầy đủ (9 thuộc tính, 14 mục kế hoạch, 4 phương án).
- Các chính sách: MDP tối ưu, cây quyết định (Fig. 8), "chỉ làm tác vụ bắt buộc rồi quyết định", "thu thập tất cả rồi quyết định", và chính sách tham lam một bước (myopic VoI).
- Phân tích độ nhạy với phân phối xác suất và chi phí.
- Demo Streamlit chạy trên máy cá nhân.

**Ngoài phạm vi**
- Bộ máy CMMN thật (Camunda, Flowable). Cấu trúc CMMN chỉ được biểu diễn dưới dạng dữ liệu (`data/koffer.yaml`).
- Học tăng cường sâu. Hướng này chỉ được nhắc trong báo cáo như hướng mở rộng.
- Khớp chính xác từng con số của bài báo.

## 5. Ràng buộc

- Bài cá nhân, máy Windows, Python 3.11 (conda), không cần GPU.
- Thời gian dự kiến khoảng 12–16 giờ làm việc, chia theo pha bên dưới.
- Không tự tạo số liệu: số liệu đầu vào lấy từ `data/`, số liệu đầu ra phải do mã sinh ra và có thể chạy lại (cố định seed).

## 6. Các điểm mơ hồ phải xử lý (chi tiết ở `docs/paper_notes.md`)

| Mã | Vấn đề | Cách xử lý mặc định | Biến thể để thử |
|---|---|---|---|
| A1 | Thuộc tính B ghi "Binomial(0.2)" trên 4 giá trị {40,60,80,100} | Binomial(n=3, p=0,2) ánh xạ 0→40, 1→60, 2→80, 3→100 | đều; Binomial ngược |
| A2 | Bernoulli(p) trên {a, b}: giá trị nào có xác suất p | p ứng với giá trị thứ hai (1, hoặc 200 với F) | đảo lại |
| A3 | Công thức Y như in trong bài không tính ra lợi nhuận ở Bảng 6 (ví dụ trường hợp 2 có E = 0 nhưng lãi 69.794) | Hiệu chỉnh ở Pha 2: thử các biến thể của Y và chọn biến thể gần Bảng 6 nhất | xem `data/koffer.yaml > information_structure.variants` |
| A4 | P(D ≥ f) với D ~ N(μ = giá trị thuộc tính D, σ = 200) | P = 1 − Φ((f − μ)/200); khi D chưa biết thì lấy kỳ vọng theo phân phối của D | — |
| A5 | Cây quyết định Fig. 8: nhãn "A = 1900, 1200" (có thể là 2100), cách nối nhánh H, thứ tự cột trong Bảng 6 | Đọc theo `data/decision_tree.yaml`, kiểm bằng 9 trường hợp | các cách đọc ghi trong file |
| A6 | "Profit" ở Bảng 6 là lợi nhuận thực hiện = Y(giá trị thật, f) − tổng chi phí tác vụ đã làm | Định nghĩa như vậy | — |
| A7 | Doanh thu và lợi nhuận của cây quyết định ở Bảng 5 không nhất quán (8.125,94 − 100,06 ≠ 8.226,0) | Ghi nhận, không cố khớp | — |
| A8 | Ví dụ nhỏ ở mục 5.3 của bài tính sai: chưa có thông tin thì lợi nhuận kỳ vọng là 1,0, không phải 0,5 | Kiểm thử theo giá trị đúng | — |

## 7. Thiết kế kỹ thuật

### 7.1 Trạng thái và mã hóa
- Trạng thái gồm (σ, s). σ là các bit đã làm hoặc chưa làm của các mục kế hoạch **không** thu thập thông tin (tác vụ 2, 3, 4, giai đoạn α, β). s là giá trị của 9 thuộc tính, trong đó 0 = ⊥ (chưa biết) và 1..|dom| là chỉ số giá trị.
- Với tác vụ thu thập thông tin, "đã làm" tương đương "đã biết giá trị", nên không cần bit riêng.
- Mã hóa hỗn hợp cơ số (mixed radix): 5⁵ · 3⁴ · 2⁵ = **8.100.000** trạng thái, khớp với con số của bài.
- Giá trị V được lưu trong mảng `float64` (khoảng 65 MB), hành động tối ưu trong mảng `int8` (khoảng 8 MB).

### 7.2 Hành động và ràng buộc
- Hành động: một mục kế hoạch chưa làm mà mọi mục đứng trước đã xong (công thức (5)), hoặc một phương án f ∈ {No bid, 1800, 2000, 2200} khi mọi mục bắt buộc đã xong (công thức (6)).
- Phần thưởng: −c_a với tác vụ và giai đoạn; E[Y(s, f)] với quyết định cuối.

### 7.3 Tính E[Y(s, f)] nhanh
- Các thuộc tính độc lập (giả định của bài), và các biến thể Y dự kiến đều **đa tuyến tính** theo các thuộc tính. Do đó E[Y] có thể tính bằng cách thay mỗi thuộc tính chưa biết bằng kỳ vọng của nó; riêng P(D ≥ f) thay bằng kỳ vọng của hàm này theo phân phối của D.
- Bắt buộc có kiểm thử đối chiếu với cách duyệt toàn bộ kịch bản (tiêu chí S2). Nếu một biến thể Y không đa tuyến tính thì phải dùng cách duyệt toàn bộ.

### 7.4 Bộ giải
- Bước 1, bản tham chiếu: đệ quy có ghi nhớ (`functools.lru_cache`) trên ví dụ nhỏ và trên mô hình Koffer rút gọn (3–4 thuộc tính). Dễ đọc, dùng để kiểm tra bản nhanh.
- Bước 2, bản nhanh: quy hoạch động trên mảng, duyệt các trạng thái theo số mục đã làm **giảm dần** (trạng thái kế tiếp luôn có nhiều mục đã làm hơn). Ưu tiên vector hóa bằng numpy, dùng numba nếu cần.
- Trạng thái vi phạm ràng buộc thứ tự vẫn có thể có chỉ số trong mảng; đánh dấu là không đi tới được và bỏ qua.

### 7.5 Đánh giá chính sách
- Có 4⁵ · 2⁴ = **16.384** kịch bản giá trị thật, xác suất mỗi kịch bản là tích các xác suất biên.
- Với mỗi chính sách và mỗi kịch bản, mô phỏng từ trạng thái gốc đến quyết định cuối, ghi lại: tác vụ đã làm, chi phí, trạng thái thông tin cuối, quyết định, doanh thu, lợi nhuận.
- Chỉ số (theo Bảng 5): lợi nhuận kỳ vọng, doanh thu kỳ vọng, chi phí thu thập trung bình, số trạng thái kết thúc khác nhau, phân phối quyết định cuối (Fig. 7a), tỷ lệ mỗi tác vụ được thực hiện (Fig. 7b).

## 8. Các pha thực hiện

Mỗi pha kết thúc bằng: kiểm thử đạt, commit git, cập nhật `docs/progress.md`.

### Pha 0: Thiết lập (khoảng 0,5 giờ)
- Tạo môi trường conda từ `requirements.txt`, khởi tạo git.
- Viết `src/dipmdp/data.py` để đọc 3 file YAML.
- Chạy `tests/test_data.py` (đã viết sẵn): xác suất mỗi phân phối có tổng bằng 1, các ràng buộc tham chiếu tới mục có tồn tại.

### Pha 1: Bộ giải tổng quát và ví dụ nhỏ (khoảng 1,5 giờ)
- `model.py`: lớp `DIPModel` (mục kế hoạch, thuộc tính, hành động được phép, phần thưởng, chuyển trạng thái).
- `solver.py`: `solve_recursive(model)` trả về V và π.
- Chạy `tests/test_toy.py` (đã viết sẵn) → tiêu chí S1. Ghi kết quả vào `results/toy.json`.

### Pha 2: Mô hình Koffer và hiệu chỉnh (khoảng 3 giờ) **← cổng quyết định**
- `information_structure.py`: các biến thể của Y trong `koffer.yaml`, hàm `expected_Y(state, f)`.
- `decision_tree.py`: chép lại Fig. 8 từ `data/decision_tree.yaml`.
- `scripts/calibrate.py`: với từng tổ hợp (biến thể Y, cách đọc A1/A2/A5), tính lợi nhuận MDP và lợi nhuận cây quyết định trên 9 trường hợp, so với Bảng 6, xuất `results/calibration.csv`.
- **Dừng lại để chọn cấu hình mặc định.** Ghi lý do vào `docs/assumptions.md`. Nếu không cấu hình nào khớp tốt, chọn cấu hình hợp lý nhất về kinh tế và ghi rõ.

### Pha 3: Giải Koffer đầy đủ (khoảng 3 giờ)
- `solver.py`: `solve_array(model)` theo mục 7.4.
- Đối chiếu với `solve_recursive` trên Koffer rút gọn (cùng V, cùng π, trừ trường hợp hòa).
- Đo số trạng thái đi tới được, thời gian, bộ nhớ → `results/runtime.json` (S6).
- Lưu `results/policy_koffer.npz` (V, π, cấu hình).

### Pha 4: Chính sách đối chứng và đánh giá (khoảng 2 giờ)
- `policies.py`: `MDPPolicy`, `DecisionTreePolicy`, `RequiredOnlyPolicy`, `CollectAllPolicy`, `MyopicVoIPolicy`.
- `evaluate.py` theo mục 7.5. Kiểm thử nhất quán S3.
- `scripts/run_experiments.py` xuất:
  - `results/table5_repro.csv`: các chỉ số của Bảng 5 cho mọi chính sách, kèm cột số liệu của bài.
  - `results/table6_repro.csv`: 9 trường hợp.
  - `results/fig_decisions.png`, `results/fig_task_usage.png` (giống Fig. 7).

### Pha 5: Mở rộng (khoảng 2–3 giờ)
- **Độ nhạy (E1 trong báo cáo):** nhân từng chi phí hoặc dịch từng phân phối ±10% và ±20%. Với mỗi nhiễu, tính (a) lợi nhuận của chính sách cũ khi mô hình thật đã đổi và (b) lợi nhuận khi giải lại; độ chênh (a − b) là mức thiệt do ước lượng sai. Xuất `results/sensitivity.csv` và biểu đồ tornado.
- **Phụ thuộc giữa thuộc tính (tùy chọn):** cho D phụ thuộc A, mô phỏng dữ liệu thật có phụ thuộc, đánh giá chính sách được giải với giả định độc lập.
- **Giá trị thông tin hiển thị cho người dùng (E3, tùy chọn):** với mỗi trạng thái, tính mức lợi của hành động tốt nhất so với quyết định ngay.

### Pha 6: Demo Streamlit (khoảng 2 giờ)
- `app/streamlit_app.py` đọc `results/policy_koffer.npz`.
- Màn hình 1, mô phỏng hồ sơ: chọn ngẫu nhiên hoặc nhập giá trị thật (ẩn với người dùng). Mỗi bước hiển thị các hành động được phép, lợi nhuận kỳ vọng của từng hành động, hành động được khuyến nghị. Người dùng có thể chọn hành động khác, hệ thống vẫn khuyến nghị tiếp cho trạng thái mới. Cuối cùng so sánh với cây quyết định trên cùng hồ sơ.
- Màn hình 2, ví dụ nhỏ của bài để giải thích giá trị thông tin.
- Nếu tải chính sách đầy đủ quá chậm thì dùng Koffer rút gọn cho demo.

### Pha 7: Tổng hợp cho báo cáo (khoảng 1 giờ)
- `results/summary.md`: cấu hình đã chọn, bảng so với bài báo, các phát hiện, giới hạn của việc tái hiện.
- Gửi `summary.md` và các hình trong `results/` để viết mục 4.6 của báo cáo và làm slide.

## 9. Rủi ro và cách giảm

| Rủi ro | Cách giảm |
|---|---|
| Không cấu hình nào khớp Bảng 6 | Đã dự kiến. Ghi rõ là tái hiện xu hướng, báo cáo chênh lệch. Đây cũng là một phát hiện về khả năng tái hiện của bài |
| Giải 8,1 triệu trạng thái chậm hoặc tốn RAM | Dùng mảng numpy và numba; nếu vẫn chậm thì giảm miền giá trị (ví dụ A còn 2 giá trị) và ghi rõ |
| Cây quyết định chép sai | Kiểm bằng 9 trường hợp; ghi lại các cách đọc khác |
| Kết quả hòa giữa các hành động làm chính sách khác bài | Quy tắc hòa cố định (ưu tiên quyết định, rồi đến chi phí thấp) và ghi vào giả định |

## 10. Quy trình làm việc với Claude Code

Dự án được thực hiện với Claude Code trong VS Code; quy tắc cho công cụ nằm ở `CLAUDE.md`. Mỗi lần chỉ làm một pha, rà soát thay đổi và chạy kiểm thử trước khi commit:

- Pha 0: thiết lập, chạy `tests/test_data.py`.
- Pha 1: viết `DIPModel` và `solve_recursive` cho đến khi `tests/test_toy.py` đạt, không sửa tệp kiểm thử.
- Pha 2: làm đến hết `scripts/calibrate.py`, dừng lại để học viên xem bảng hiệu chỉnh và chọn cấu hình.
- Pha 3: đối chiếu `solve_array` với `solve_recursive` trên Koffer rút gọn trước khi chạy bản đầy đủ.
- Pha 4–7: tương tự, mỗi pha một lần.

Mọi thay đổi dữ liệu trong `data/` hoặc kiểm thử viết sẵn đều phải được học viên đồng ý trước.
