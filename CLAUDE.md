# Hướng dẫn cho Claude Code

## Bối cảnh
Đồ án cá nhân môn CS2208 Hệ hỗ trợ quyết định (UIT). Mục tiêu là tái hiện phương pháp và thực nghiệm của Voorberg et al. (2021): chuyển mô hình CMMN của bài toán Koffer thành MDP, giải bằng quy nạp ngược và so sánh với cây quyết định. Kế hoạch đầy đủ nằm ở `PLAN.md`; luôn đọc file này trước khi làm một pha.

## Quy tắc làm việc
1. Làm **đúng một pha** mỗi lần theo `PLAN.md` mục 8. Kết thúc pha: chạy `pytest`, cập nhật `docs/progress.md`, rồi dừng lại báo cáo. Không tự chuyển sang pha tiếp theo.
2. **Không sửa** file trong `data/` và các kiểm thử đã viết sẵn (`tests/test_data.py`, `tests/test_toy.py`) nếu chưa hỏi người dùng. Nếu thấy dữ liệu sai, báo lại kèm trang hoặc bảng của bài báo.
3. **Không bịa số liệu.** Mọi con số trong `results/` phải do mã sinh ra. Mọi lựa chọn khi gặp chỗ mơ hồ phải ghi vào `docs/assumptions.md` với mã A#.
4. Pha 2 là **cổng quyết định**: chạy hiệu chỉnh, trình bày bảng, chờ người dùng chọn cấu hình.
5. Kết quả phải chạy lại được: cố định seed, ghi cấu hình vào đầu mỗi file kết quả (JSON hoặc chú thích CSV).
6. Khi một kết quả khác bài báo, ghi chênh lệch rõ ràng thay vì chỉnh mô hình cho khớp mà không có căn cứ.

## Quy ước mã
- Python 3.11, gói nguồn trong `src/dipmdp/`, cài bằng `python scripts/install_editable.py` (ghi đường dẫn tuyệt đối vào `dipmdp_dev.pth`; chạy lại sau khi đổi tên hoặc di chuyển thư mục dự án).
- Tên biến, hàm, chú thích trong mã bằng tiếng Anh. Tài liệu trong `docs/` và `results/summary.md` bằng tiếng Việt.
- Có type hint, hàm thuần khi có thể, không có biến toàn cục mang trạng thái.
- Thứ tự thuộc tính luôn là thứ tự trong YAML. Giá trị chưa biết (⊥) mã hóa là chỉ số 0, giá trị thứ k mã hóa là k (1-based) trong mảng trạng thái.
- Mô hình được tạo từ YAML, không hard-code số liệu Koffer trong mã.

## Lệnh thường dùng
```
conda activate dss-repro
python scripts/install_editable.py
pytest -q
python scripts/calibrate.py          # Pha 2
python scripts/solve_koffer.py       # Pha 3
python scripts/run_experiments.py    # Pha 4-5
streamlit run app/streamlit_app.py   # Pha 6
```

## Tài liệu tham chiếu nhanh
- `docs/paper_notes.md`: vị trí số liệu trong bài, các điểm không nhất quán đã biết.
- `docs/assumptions.md`: nhật ký giả định.
- `docs/fig8_decision_tree.png`: ảnh cây quyết định gốc.
- Bài báo PDF: `../Paper/`.
