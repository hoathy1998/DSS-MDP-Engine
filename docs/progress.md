# Tiến độ

| Pha | Trạng thái | Ngày | Ghi chú |
|---|---|---|---|
| 0. Thiết lập | xong | 2026-11-01 | `tests/test_data.py` 5/5, `tests/test_data_loader.py` 7/7. `pip install -e .` lỗi do đường dẫn có ký tự ngoài cp1252, thay bằng `scripts/install_editable.py`. Môi trường `dss-repro`: Python 3.11.18, `pip check` không báo lỗi |
| 1. Bộ giải và ví dụ nhỏ | xong | 2026-11-01 | S1 đạt: `tests/test_toy.py` 4/4, V(gốc) = 1,0, hành động "quyết định f = 1" (`results/toy.json`, sinh bằng `scripts/solve_toy.py`). `tests/test_model.py` 15/15. |
| 2. Koffer và hiệu chỉnh | xong | 2026-11-01 | S2 đạt (`tests/test_information_structure.py`). S4: cây khớp Bảng 5 (chi phí, số trạng thái kết thúc) và Fig. 7, Bảng 6 chỉ khớp dòng 5, 6, 9 (giải thích ở `docs/paper_notes.md` mục 4). `results/calibration.csv`, `results/y_variant_search.csv`. A1, A2, A5 đã có căn cứ; A3: người dùng chọn `margin_all`, đối chứng `margin_repair` |
| 3. Giải đầy đủ | xong | 2026-11-01 | `solve_array` cho cùng V và π với `solve_recursive` trên Koffer rút gọn. 8.100.000 trạng thái, 640.224 đi tới được; dưới 1 giây khi đã có cache numba (`results/runtime.json`, S6). V(gốc): `margin_all` 8.762,62; `margin_repair` 17.506,47 |
| 4. Đánh giá | xong | 2026-11-01 | S3 đạt (sai số khoảng 1e-11 trên 16.384 kịch bản). S5 đạt ở cả hai biến thể Y. `results/table5_repro.csv`, `table6_repro.csv`, `fig_decisions*.png`, `fig_task_usage*.png` |
| 5. Mở rộng | xong | 2026-11-01 | Độ nhạy: mức thiệt khi không giải lại tối đa 0,05 (0,001%) với `margin_all`; phép thử căng thẳng xác nhận cách tính. Phụ thuộc D theo A (`results/dependence.csv`), giá trị thông tin (`results/value_of_information.csv`) |
| 6. Demo Streamlit | xong | 2026-11-01 | pp/streamlit_app.py: mô phỏng hồ sơ Koffer và ví dụ nhỏ; 	ests/test_app.py chạy cả hai màn hình bằng AppTest. Server khởi động được, nhưng chưa xem giao diện bằng trình duyệt vì tiện ích Chrome không kết nối |
| 7. Tổng hợp | chưa bắt đầu | | |

Ghi chú 2026-11-01: thư mục môn học đổi tên thành `HK3.CS2208-DSS`. Đã chạy lại `python scripts/install_editable.py`; `dipmdp_dev.pth` trỏ đúng thư mục mới.

Ghi chú 2026-11-01: `model.py`, `solver.py` và `load_model` có sẵn từ trước, được ghi lúc 15:49 trong khi đang làm Pha 0; người dùng cho rằng có thể do phiên làm việc trước. Rà soát lại và sửa các lỗi `tests/test_toy.py` không phát hiện được: `observe` nhầm giá trị với chỉ số; biến thể Y không tồn tại cho Y = 0; quy tắc hòa sai so với A9; E[Y] sai với Y không đa tuyến tính (nay duyệt toàn bộ giá trị chưa biết); mô hình không có quyết định hoặc bị khóa vẫn trả về giá trị thay vì báo lỗi.
