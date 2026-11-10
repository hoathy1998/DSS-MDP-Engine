# Tóm tắt kết quả tái hiện Voorberg et al. (2021)

Tệp này do `scripts/make_summary.py` sinh ra từ các tệp trong `results/`, dùng làm đầu vào cho mục 4.6 "Thực nghiệm tái hiện" của báo cáo.

## 1. Kết luận chính

- **Phương pháp tái hiện được.** Bộ giải quy nạp ngược tổng quát chạy đúng trên ví dụ nhỏ và trên Koffer đầy đủ. Giá trị V(gốc) bằng lợi nhuận mô phỏng trên toàn bộ 16.384 kịch bản.
- **Xu hướng của Bảng 5 tái hiện được, con số thì không.** MDP có lợi nhuận cao hơn, ít trạng thái kết thúc hơn và chi phí thu thập cao hơn cây quyết định. Tuy vậy, với công thức in trong bài, lợi nhuận MDP là 8.762,62 so với 15.867,6 của bài (−44,8%), còn của cây là 3.643,66 so với 8.226,0 (−55,7%).
- **Cấu trúc mô hình được xác nhận độc lập với Y.** Cây Fig. 8 cho chi phí trung bình 100,06 và 1.254 trạng thái kết thúc, khớp Bảng 5. Vì vậy chênh lệch lợi nhuận nhiều khả năng nằm ở hàm Y mà bài đã thực sự dùng, không phải ở phân phối hay cây.
- **Khoảng cách "gấp đôi" phụ thuộc mốc so sánh.** MDP cao hơn cây 1,93 lần trong bài, 2,40 lần với `margin_all` và 1,69 lần với `margin_repair`. Nhưng chỉ làm tác vụ bắt buộc rồi quyết định đã đạt 5.733,87, cao hơn cây, nên so với mốc này MDP chỉ cao hơn 1,53 lần. Chính sách tham lam một bước đạt 99,6% lợi nhuận của MDP.

## 2. Cấu hình

| Lựa chọn | Giá trị | Căn cứ |
|---|---|---|
| Y mặc định (A3) | `margin_all`: E·B·H·P(D ≥ f)·[f − A(1 − 0,2G) − F − I] | Công thức in ở tr. 10 |
| Y đối chứng (A3) | `margin_repair`: E·B·H·P(D ≥ f)·[f − A(1 − 0,2G)] − F − I | Gần số của bài hơn nhưng không có căn cứ trong bài; chỉ dùng để đối chứng |
| Phân phối B (A1) | Binomial(n = 3, p = 0,2) | Khớp chi phí, số trạng thái ở Bảng 5 và Fig. 7 |
| Bernoulli (A2) | p ứng với giá trị thứ hai | Như trên |
| Cây quyết định (A5) | Đọc theo Fig. 8 | Như trên |
| Quy tắc hòa (A9, A10) | Quyết định trước, chi phí thấp hơn, rồi thứ tự trong tệp; dung sai 1e-9 | Bài không nêu |

`data/koffer.yaml` ban đầu chép sai công thức: biến thể tên `paper` thiếu ngoặc vuông của tr. 10. Biến thể này đã được đổi tên thành `flat_costs`; không giá trị số nào thay đổi.

## 3. So với Bảng 5

| Chỉ số | Bài báo | `margin_all` | Chênh lệch | `margin_repair` | Chênh lệch |
|---|---:|---:|---:|---:|---:|
| MDP: Lợi nhuận kỳ vọng | 15.867,60 | 8.762,62 | −44,8% | 17.506,47 | +10,3% |
| MDP: Doanh thu kỳ vọng | 16.011,00 | 8.886,14 | −44,5% | 17.638,94 | +10,2% |
| MDP: Chi phí trung bình | 143,50 | 123,52 | −13,9% | 132,47 | −7,7% |
| MDP: Số trạng thái kết thúc | 136 | 196 | +44,1% | 50 | −63,2% |
| Cây: Lợi nhuận kỳ vọng | 8.226,00 | 3.643,66 | −55,7% | 10.385,86 | +26,3% |
| Cây: Doanh thu kỳ vọng | 8.125,94 | 3.743,72 | −53,9% | 10.485,93 | +29,0% |
| Cây: Chi phí trung bình | 100,06 | 100,06 | 0,0% | 100,06 | 0,0% |
| Cây: Số trạng thái kết thúc | 1.254 | 1.254 | 0,0% | 1.254 | 0,0% |

Doanh thu và lợi nhuận của cây trong Bảng 5 tự mâu thuẫn (8.125,94 − 100,06 ≠ 8.226,0, giả định A7), nên hai dòng này chỉ có tính tham khảo.

Trong 108 cách đặt các số hạng chi phí vào Y (`results/y_variant_search.csv`), có 0 cách nằm trong phạm vi 5% của cả hai con số lợi nhuận và 0 cách đạt đúng 136 trạng thái kết thúc của MDP. Dự án không chỉnh mô hình để khớp thêm vì không có căn cứ.

## 4. Mọi chính sách

Y = `margin_all`:

| Chính sách | Lợi nhuận kỳ vọng | Doanh thu kỳ vọng | Chi phí trung bình | Số trạng thái kết thúc | Tỷ lệ không báo giá |
|---|---:|---:|---:|---:|---:|
| MDP tối ưu | 8.762,62 | 8.886,14 | 123,52 | 196 | 0,499 |
| Cây quyết định (Fig. 8) | 3.643,66 | 3.743,72 | 100,06 | 1.254 | 0,735 |
| Chỉ làm tác vụ bắt buộc | 5.733,87 | 5.778,87 | 45,00 | 4 | 0,400 |
| Thu thập tất cả | 8.632,88 | 8.886,88 | 254,00 | 16.384 | 0,505 |
| Tham lam một bước | 8.726,65 | 8.846,51 | 119,86 | 114 | 0,499 |

Y = `margin_repair`:

| Chính sách | Lợi nhuận kỳ vọng | Doanh thu kỳ vọng | Chi phí trung bình | Số trạng thái kết thúc | Tỷ lệ không báo giá |
|---|---:|---:|---:|---:|---:|
| MDP tối ưu | 17.506,47 | 17.638,94 | 132,47 | 50 | 0,400 |
| Cây quyết định (Fig. 8) | 10.385,86 | 10.485,93 | 100,06 | 1.254 | 0,735 |
| Chỉ làm tác vụ bắt buộc | 14.622,00 | 14.667,00 | 45,00 | 4 | 0,400 |
| Thu thập tất cả | 17.386,65 | 17.640,65 | 254,00 | 16.384 | 0,411 |
| Tham lam một bước | 17.499,39 | 17.640,57 | 141,19 | 54 | 0,409 |

Hình: `results/fig_decisions.png`, `results/fig_task_usage.png` (dấu chấm là số đọc bằng mắt từ Fig. 7), và các bản `_margin_repair`.

## 5. Chín trường hợp của Bảng 6

Y = `margin_all`, thứ tự cột A..I như bài ghi. Khớp trong phạm vi ±1: MDP ở trường hợp [5, 6, 9], cây ở trường hợp [5, 6, 9].

| TH | Giá trị [A..I] | MDP (tái hiện) | MDP (bài báo) | Cây (tái hiện) | Cây (bài báo) |
|---|---|---:|---:|---:|---:|
| 1 | 2100 40 1 1900 1 100 0 1 150 | −90,0 | 1.656 | −57,0 | −122 |
| 2 | 1500 100 1 2100 0 100 1 4 100 | −45,0 | 69.794 | −45,0 | 65.469 |
| 3 | 2100 80 1 2100 1 200 0 1 50 | −90,0 | −45 | −57,0 | −45 |
| 4 | 2100 40 0 2300 0 200 0 3 150 | −45,0 | 16.385 | −45,0 | 14.692 |
| 5 | 1900 100 0 2300 0 200 0 4 200 | −45,0 | −45 | −45,0 | −45 |
| 6 | 1900 40 0 2300 0 200 0 3 150 | −45,0 | −45 | −45,0 | −45 |
| 7 | 1500 40 1 1900 1 100 0 1 150 | 2.875,4 | −45 | −57,0 | −45 |
| 8 | 1700 80 1 1700 1 100 0 2 200 | 96,7 | 27.416 | −10.080,2 | 27.419 |
| 9 | 1900 60 0 1900 0 100 1 1 150 | −45,0 | −45 | −45,0 | −45 |

Bảng 6 không dùng được để hiệu chỉnh. Trên 900 tổ hợp cấu hình (`results/calibration.csv`), nhiều nhất 4/9 dòng của cây và 4/9 dòng của MDP khớp. Nguyên nhân nằm trong chính bảng. Cây kiểm tra E đầu tiên, nên lợi nhuận −45 của cây chỉ có thể xảy ra khi E = 0, và mọi kết quả khác chỉ có thể xảy ra khi E = 1. Các trường hợp 1, 3, 7, 8 có cùng ba giá trị nhị phân, nên E như nhau dù đọc cột nào là E, vậy mà trường hợp 3 và 7 cho −45 còn trường hợp 1 cho −122 và trường hợp 8 có lãi. Trường hợp 4 có cả ba giá trị bằng 0, nên E = 0, nhưng cây vẫn có lãi (`docs/paper_notes.md` mục 4).

## 6. Mở rộng

**Độ nhạy (E1), nhiễu ±10% và ±20%.** Lợi nhuận tối ưu nhạy nhất với phân phối E: thay đổi tới 1.467,94 ở mức −20%. Nhiễu chi phí chỉ làm lợi nhuận đổi tối đa 7,38. Mức thiệt do giữ chính sách cũ thay vì giải lại lớn nhất là 0,05 (0,001%), nên trong phạm vi này chính sách rất bền với sai số ước lượng. Một phép thử căng thẳng (chi phí D gấp 21 lần, `tests/test_sensitivity.py`) cho mức thiệt lớn, xác nhận cách tính không bị lỗi. Hình: `results/fig_tornado.png`.

**Phụ thuộc D theo A.** Chính sách giải với giả định độc lập, đánh giá khi D phụ thuộc A với ρ từ −0,8 đến 0,8: lợi nhuận MDP từ 9.534,76 đến 7.990,48, cây từ 4.051,53 đến 3.235,78. MDP vẫn cao hơn cây ở mọi mức. Đây chưa phải mức thiệt so với tối ưu thật, vì không giải lại với phụ thuộc.

**Giá trị thông tin (E3).** Sau các tác vụ bắt buộc, khi C = 0 và E = 1, quyết định ngay có giá trị 9.631,45. Hành động tốt nhất là mở giai đoạn α, lợi hơn quyết định ngay 5.047,92 (`results/value_of_information.csv`).

## 7. Quy mô tính toán

8.100.000 trạng thái, trong đó 640.224 đi tới được (7,9%). Thời gian giải 0,91 giây khi numba đã có sẵn bản biên dịch, mảng V và π chiếm 69,5 MB. Bài báo ghi 49 phút trên Intel i5-8365U. Hai con số không so sánh trực tiếp được vì khác máy và khác cách cài đặt; máy dùng ở đây ghi trong `results/runtime.json`.

## 8. Ví dụ nhỏ (mục 5.3)

V(gốc) = 1,0, hành động tối ưu là nhận ngay (f = 1); thu thập X₁ hoặc X₂ chỉ cho 0,75. Bài báo ghi 0,5 và kết luận nên thu thập X₂. Đây là lỗi số học của bài (A8).

## 9. Tiêu chí thành công

| # | Tiêu chí | Kết quả | Kiểm tra |
|---|---|---|---|
| S1 | Ví dụ nhỏ đúng | Đạt | `tests/test_toy.py` |
| S2 | E[Y] rút gọn bằng duyệt toàn bộ | Đạt, cả năm biến thể Y | `tests/test_information_structure.py` |
| S3 | V(gốc) bằng lợi nhuận mô phỏng, sai số < 1e-6 | Đạt | `tests/test_consistency.py` |
| S4 | Cây kiểm với 9 trường hợp, giải thích mọi chỗ lệch | Khớp 3/9; phần lệch được giải thích ở mục 5 | `tests/test_decision_tree.py` |
| S5 | Đúng xu hướng Bảng 5 | Đạt, cả hai biến thể Y | `results/table5_repro.csv` |
| S6 | Ghi số trạng thái, thời gian, bộ nhớ, máy | Đạt | `results/runtime.json` |
| S7 | Mọi giả định có mã | A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15 | `docs/assumptions.md` |

## 10. Giới hạn

- Không xác định được hàm Y mà tác giả đã dùng, vì bài không công bố mã nguồn. Số lợi nhuận tuyệt đối vì thế lệch đáng kể so với bài.
- Số của Fig. 7 được đọc bằng mắt nên chỉ dùng để so sánh hình dạng.
- E[Y] dựa trên giả định các thuộc tính độc lập của bài. Phần phụ thuộc chỉ đánh giá, không giải lại.
- Cấu trúc CMMN chỉ được biểu diễn dưới dạng dữ liệu, không chạy trên bộ máy CMMN thật.
- Demo Streamlit đã được kiểm thử luồng thao tác bằng AppTest, nhưng chưa được xem trên trình duyệt.

## 11. Chạy lại

```
conda activate dss-repro
python scripts/solve_toy.py
python scripts/calibrate.py
python scripts/explore_y_variants.py
python scripts/solve_koffer.py
python scripts/run_experiments.py
python scripts/make_summary.py
streamlit run app/streamlit_app.py
```
