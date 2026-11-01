# Tiến độ

| Pha | Trạng thái | Ngày | Ghi chú |
|---|---|---|---|
| 0. Thiết lập | xong | 2026-11-01 | `tests/test_data.py` 5/5, `tests/test_data_loader.py` 7/7. `pip install -e .` lỗi do đường dẫn có ký tự ngoài cp1252, thay bằng `scripts/install_editable.py`. Môi trường `dss-repro`: Python 3.11.18, `pip check` không báo lỗi |
| 1. Bộ giải và ví dụ nhỏ | xong | 2026-11-01 | S1 đạt: `tests/test_toy.py` 4/4, V(gốc) = 1,0, hành động "quyết định f = 1" (`results/toy.json`, sinh bằng `scripts/solve_toy.py`). `tests/test_model.py` 15/15. |
| 2. Koffer và hiệu chỉnh | xong | 2026-11-01 | S2 đạt (`tests/test_information_structure.py`). S4: cây khớp Bảng 5 (chi phí, số trạng thái kết thúc) và Fig. 7, Bảng 6 chỉ khớp dòng 5, 6, 9 (giải thích ở `docs/paper_notes.md` mục 4). `results/calibration.csv`, `results/y_variant_search.csv`. A1, A2, A5 đã có căn cứ; A3: người dùng chọn `margin_all`, đối chứng `margin_repair` |
| 3. Giải đầy đủ | chưa bắt đầu | | |
| 4. Đánh giá | chưa bắt đầu | | |
| 5. Mở rộng | chưa bắt đầu | | |
| 6. Demo Streamlit | chưa bắt đầu | | |
| 7. Tổng hợp | chưa bắt đầu | | |

Ghi chú 2026-11-01: thư mục môn học đổi tên thành `HK3.CS2208-DSS`. Đã chạy lại `python scripts/install_editable.py`; `dipmdp_dev.pth` trỏ đúng thư mục mới.

Ghi chú 2026-11-01: `model.py`, `solver.py` và `load_model` có sẵn từ trước, được ghi lúc 15:49 trong khi đang làm Pha 0; người dùng cho rằng có thể do phiên làm việc trước. Rà soát lại và sửa các lỗi `tests/test_toy.py` không phát hiện được: `observe` nhầm giá trị với chỉ số; biến thể Y không tồn tại cho Y = 0; quy tắc hòa sai so với A9; E[Y] sai với Y không đa tuyến tính (nay duyệt toàn bộ giá trị chưa biết); mô hình không có quyết định hoặc bị khóa vẫn trả về giá trị thay vì báo lỗi.
