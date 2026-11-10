# Hệ hỗ trợ quyết định thu thập thông tin: tái hiện Voorberg et al. (2021)

Đồ án cuối kỳ CS2208 Hệ hỗ trợ quyết định, UIT. Học viên: Châu Ngọc Hoa Thy. GVHD: Ton That Hoa An, Ph.D.

Bài báo gốc: S. Voorberg, R. Eshuis, W. van Jaarsveld, G.-J. van Houtum, "Decisions for information or information for decisions? Optimizing information gathering in decision-intensive processes," *Decision Support Systems*, vol. 151, 113632, 2021.

Bài báo chuyển một quy trình ra quyết định mô hình hóa bằng CMMN thành một quá trình quyết định Markov (MDP), giải bằng quy nạp ngược để biết ở mỗi trạng thái nên thu thập thêm thông tin nào hay nên quyết định ngay, rồi đưa chính sách vào một bộ khuyến nghị theo kiến trúc hai pha (Fig. 1). Đồ án gồm hai phần:

1. **Tái hiện phương pháp và thực nghiệm** trên bài toán Koffer (báo giá hợp đồng bảo trì linh kiện máy bay): giải chính xác 8.100.000 trạng thái, so sánh với cây quyết định (Bảng 5, Bảng 6), thêm các chính sách đối chứng và phân tích độ nhạy.
2. **Hệ thống quyết định hai pha theo Fig. 1**: pha thiết kế đi từ mô hình CMMN XML đến chính sách đã giải; pha triển khai là máy chủ web điều phối hồ sơ, hỏi bộ khuyến nghị ở mỗi bước, kiểm soát quy định quy trình và cho người quyết định làm khác khuyến nghị kèm lý do.

## Kết quả chính

- Phương pháp tái hiện được: giá trị gốc của MDP bằng lợi nhuận mô phỏng trên toàn bộ 16.384 kịch bản.
- Xu hướng của Bảng 5 tái hiện được: MDP có lợi nhuận cao hơn, ít trạng thái kết thúc hơn và chi phí thu thập cao hơn cây quyết định.
- Con số tuyệt đối không tái hiện được: với công thức lợi nhuận in trong bài, MDP đạt 8.762,62 so với 15.867,6 của bài. Cây quyết định khớp đúng chi phí 100,06 và 1.254 trạng thái kết thúc, nên chênh lệch nằm ở hàm lợi nhuận bài không công bố đủ.
- Hệ thống hai pha: giải và đóng gói trong dưới một giây; mỗi khuyến nghị là một phép tra bảng, trung vị 0,073 ms.

Chi tiết ở `results/summary.md` (sinh bằng `scripts/make_summary.py`). Mọi lựa chọn khi bài báo mơ hồ được ghi thành giả định A1–A15 trong `docs/assumptions.md`.

## Cấu trúc

```
├── data/                    số liệu chép từ bài: Bảng 2–4, cây Fig. 8, Bảng 5–6, ví dụ nhỏ mục 5.3
├── models/koffer.cmmn       mô hình CMMN 1.1 của bài toán Koffer, đầu vào của pha thiết kế
├── src/dipmdp/
│   ├── model.py             MDP: trạng thái, hành động được phép, phần thưởng, chuyển trạng thái
│   ├── information_structure.py   hàm lợi nhuận Y và E[Y]
│   ├── solver.py            quy nạp ngược: bản đệ quy (tham chiếu) và bản mảng (numba)
│   ├── policies.py, evaluate.py, decision_tree.py, sensitivity.py   chính sách và đánh giá
│   └── system/              hệ thống hai pha: cmmn, design, recommender, engine, server, ui.html
├── scripts/                 các lệnh chạy thực nghiệm và hệ thống
├── tests/                   kiểm thử (pytest)
├── app/streamlit_app.py     demo Streamlit
├── web/koffer_demo.html     demo web tự chứa, không cần Python
├── results/                 kết quả do mã sinh ra; đọc `summary.md` trước
└── docs/                    ghi chú về bài báo, giả định, kiến trúc hệ thống, tiến độ
```

## Cài đặt

Cần Python 3.11 (đã thử trên Windows với conda).

```
conda create -n dss-repro python=3.11 -y
conda activate dss-repro
pip install -r requirements.txt
pip install -e .
pytest -q
```

Nếu `pip install -e .` lỗi do đường dẫn thư mục có ký tự ngoài ASCII, thay bằng `python scripts/install_editable.py`.

## Chạy lại thực nghiệm

```
python scripts/solve_toy.py            # ví dụ nhỏ mục 5.3
python scripts/calibrate.py            # hiệu chỉnh với Bảng 6
python scripts/explore_y_variants.py   # thử các dạng hàm lợi nhuận
python scripts/solve_koffer.py         # giải MDP Koffer đầy đủ
python scripts/run_experiments.py      # Bảng 5, Bảng 6, độ nhạy, phụ thuộc, giá trị thông tin
python scripts/make_summary.py         # results/summary.md
```

## Hệ thống hai pha

```
python scripts/design_time.py                 # pha thiết kế: models/koffer.cmmn + tham số -> gói triển khai
python scripts/demo.py                        # pha triển khai: mở http://127.0.0.1:8600 trên trình duyệt
python scripts/demo_rule_check.py             # (terminal khác) máy chủ từ chối hành động sai quy định
```

Giữ cửa sổ chạy `demo.py` mở trong lúc dùng; nhấn Ctrl+C để tắt. `scripts/run_system.py` là bản chạy thường, giữ hồ sơ giữa các lần khởi động. Kiến trúc, đối chiếu với Fig. 1, số đo độ trễ và giới hạn nằm trong `docs/system.md`.

## Demo khác

```
streamlit run app/streamlit_app.py     # mô phỏng hồ sơ và ví dụ nhỏ
python scripts/build_web_demo.py       # dựng lại web/koffer_demo.html
```

`web/koffer_demo.html` mở trực tiếp bằng trình duyệt; bộ giải JavaScript trong trang được kiểm tra khớp với bộ giải Python trên mọi trạng thái đi tới được (`tests/test_web_demo.py`, cần Node.js).

## Tài liệu

| Tệp | Nội dung |
|---|---|
| `PLAN.md` | kế hoạch, tiêu chí thành công S1–S7, các pha |
| `docs/paper_notes.md` | vị trí số liệu trong bài và các điểm không nhất quán |
| `docs/assumptions.md` | nhật ký giả định A1–A15 |
| `docs/system.md` | hệ thống hai pha: kiến trúc, màn hình, độ trễ, giới hạn |
| `docs/progress.md` | tiến độ theo pha |
| `results/summary.md` | tóm tắt toàn bộ kết quả |

## Công cụ hỗ trợ

Mã nguồn được viết với sự hỗ trợ của Claude Code. Quy tắc làm việc đặt cho công cụ (không bịa số liệu, ghi mọi giả định, mỗi lần làm một pha) nằm trong `CLAUDE.md`.
