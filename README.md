# voorberg-mdp-repro

Tái hiện phương pháp CMMN → MDP của Voorberg et al. (2021, *Decision Support Systems* 151:113632) trên bài toán Koffer, kèm thực nghiệm so sánh với cây quyết định và demo bộ khuyến nghị.

Đồ án cuối kỳ CS2208 Hệ hỗ trợ quyết định, UIT. Học viên: Châu Ngọc Hoa Thy. GVHD: Ton That Hoa An, Ph.D.

## Cấu trúc

```
voorberg-mdp-repro/
├── PLAN.md                  kế hoạch, tiêu chí thành công, các pha
├── CLAUDE.md                quy tắc cho Claude Code
├── data/
│   ├── koffer.yaml          Bảng 2–4 và hàm Y của bài
│   ├── decision_tree.yaml   chép lại Fig. 8
│   ├── paper_results.yaml   Bảng 5–6, số liệu để so sánh
│   └── toy.yaml             ví dụ nhỏ ở mục 5.3
├── docs/
│   ├── paper_notes.md       ghi chú và các điểm không nhất quán của bài
│   ├── assumptions.md       nhật ký giả định A1, A2, …
│   ├── progress.md          tiến độ theo pha
│   └── fig8_decision_tree.png
├── src/dipmdp/              mã nguồn
├── scripts/                 các script chạy thực nghiệm
├── tests/                   kiểm thử
├── app/                     demo Streamlit
├── notebooks/               khám phá (tùy chọn)
└── results/                 đầu ra (không commit file lớn); bắt đầu đọc từ summary.md
```

## Chạy lại kết quả

```
python scripts/solve_toy.py            # Pha 1
python scripts/calibrate.py            # Pha 2
python scripts/explore_y_variants.py   # Pha 2
python scripts/solve_koffer.py         # Pha 3
python scripts/run_experiments.py      # Pha 4-5
python scripts/make_summary.py         # Pha 7
streamlit run app/streamlit_app.py     # Pha 6, xem thử bộ khuyến nghị
```

## Bắt đầu

```
conda create -n dss-repro python=3.11 -y
conda activate dss-repro
pip install -r requirements.txt
python scripts/install_editable.py
pytest -q tests/test_data.py
```

Vị trí dự án: `C:\Doris\uit-master\HK3.CS2208-DSS\voorberg-mdp-repro` (đường dẫn chỉ có ký tự ASCII, đổi tên ngày 2026-11-01).

`scripts/install_editable.py` ghi file `dipmdp_dev.pth` chứa **đường dẫn tuyệt đối** tới `src/` vào site-packages của môi trường. Mỗi khi đổi tên hoặc di chuyển thư mục dự án, phải chạy lại lệnh này (file `.pth` sẽ được ghi đè bằng đường dẫn mới), nếu không `import dipmdp` sẽ lỗi. Script này được tạo vì `pip install -e .` lỗi trên Python 3.11/Windows khi đường dẫn có ký tự ngoài cp1252; với đường dẫn ASCII hiện tại thì `pip install -e .` cũng dùng được, nhưng chỉ nên dùng một trong hai cách.

Sau đó mở thư mục trong VS Code và làm theo `PLAN.md` mục 10.
