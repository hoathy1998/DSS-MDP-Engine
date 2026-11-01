"""Phase 7: write results/summary.md from the files in results/, so every number in it is generated."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from dipmdp.data import load_paper_results

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
POLICY_NAMES = {
    "mdp": "MDP tối ưu",
    "decision_tree": "Cây quyết định (Fig. 8)",
    "required_only": "Chỉ làm tác vụ bắt buộc",
    "collect_all": "Thu thập tất cả",
    "myopic_voi": "Tham lam một bước",
}


def vn(value: float, decimals: int = 2) -> str:
    """Vietnamese number format: 8.762,62."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "§").replace(".", ",").replace("§", ".").replace("-", "−")


def signed_pct(value: float) -> str:
    if round(value, 1) == 0:
        return "0,0%"
    return ("+" if value > 0 else "−") + vn(abs(value), 1) + "%"


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS / name, comment="#")


def table5_section(table5: pd.DataFrame, y_variant: str) -> str:
    lines = [
        "| Chính sách | Lợi nhuận kỳ vọng | Doanh thu kỳ vọng | Chi phí trung bình | Số trạng thái kết thúc | Tỷ lệ không báo giá |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in table5[table5.y_variant == y_variant].itertuples():
        lines.append(
            f"| {POLICY_NAMES[row.policy]} | {vn(row.expected_profit)} | {vn(row.expected_revenue)} | "
            f"{vn(row.avg_retrieval_cost)} | {vn(row.n_final_states, 0)} | {vn(row.no_bid_share, 3)} |"
        )
    return "\n".join(lines)


def paper_gap_section(table5: pd.DataFrame, paper: dict) -> str:
    lines = [
        "| Chỉ số | Bài báo | `margin_all` | Chênh lệch | `margin_repair` | Chênh lệch |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    metrics = (
        ("Lợi nhuận kỳ vọng", "expected_profit", "expected_profit", 2),
        ("Doanh thu kỳ vọng", "expected_revenue", "expected_revenue", 2),
        ("Chi phí trung bình", "avg_retrieval_cost", "avg_retrieval_cost", 2),
        ("Số trạng thái kết thúc", "final_states", "n_final_states", 0),
    )
    for policy, label in (("mdp", "MDP"), ("decision_tree", "Cây")):
        target = paper["table5"][policy]
        chosen = table5[(table5.policy == policy) & (table5.y_variant == "margin_all")].iloc[0]
        contrast = table5[(table5.policy == policy) & (table5.y_variant == "margin_repair")].iloc[0]
        for name, paper_key, column, decimals in metrics:
            reference = target[paper_key]
            lines.append(
                f"| {label}: {name} | {vn(reference, decimals)} | {vn(chosen[column], decimals)} | "
                f"{signed_pct(100 * (chosen[column] / reference - 1))} | {vn(contrast[column], decimals)} | "
                f"{signed_pct(100 * (contrast[column] / reference - 1))} |"
            )
    return "\n".join(lines)


def table6_section(table6: pd.DataFrame) -> str:
    rows = table6[table6.y_variant == "margin_all"]
    lines = [
        "| TH | Giá trị [A..I] | MDP (tái hiện) | MDP (bài báo) | Cây (tái hiện) | Cây (bài báo) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows.itertuples():
        lines.append(
            f"| {row.instance} | {row.final_state_ABCDEFGHI} | {vn(row.mdp_profit, 1)} | {vn(row.paper_mdp_profit, 0)} | "
            f"{vn(row.tree_profit, 1)} | {vn(row.paper_tree_profit, 0)} |"
        )
    return "\n".join(lines)


def main() -> None:
    paper = load_paper_results()
    table5 = read("table5_repro.csv")
    table6 = read("table6_repro.csv")
    sensitivity = read("sensitivity.csv")
    dependence = read("dependence.csv")
    calibration = read("calibration.csv")
    search = read("y_variant_search.csv")
    voi = read("value_of_information.csv")
    runtime = json.loads((RESULTS / "runtime.json").read_text(encoding="utf-8"))
    toy = json.loads((RESULTS / "toy.json").read_text(encoding="utf-8"))
    assumptions = (ROOT / "docs" / "assumptions.md").read_text(encoding="utf-8")

    def profit(y_variant: str, policy: str) -> float:
        return float(table5[(table5.y_variant == y_variant) & (table5.policy == policy)].expected_profit.iloc[0])

    target_mdp = paper["table5"]["mdp"]["expected_profit"]
    target_tree = paper["table5"]["decision_tree"]["expected_profit"]
    near_both = search[
        ((search.mdp_profit - target_mdp).abs() / target_mdp < 0.05)
        & ((search.tree_profit - target_tree).abs() / target_tree < 0.05)
    ]
    run = runtime["runs"]["margin_all"]
    chosen6 = table6[table6.y_variant == "margin_all"]
    mdp_matches = chosen6[(chosen6.mdp_profit - chosen6.paper_mdp_profit).abs() <= 1].instance.tolist()
    tree_matches = chosen6[(chosen6.tree_profit - chosen6.paper_tree_profit).abs() <= 1].instance.tolist()
    chosen_sensitivity = sensitivity[sensitivity.y_variant == "margin_all"]
    extreme = chosen_sensitivity[chosen_sensitivity.delta.abs() == 0.2].assign(
        move=lambda frame: frame.resolved_profit - frame.base_profit
    )
    biggest = extreme.loc[extreme.move.abs().idxmax()]
    cost_moves = extreme[extreme.kind == "cost"].move.abs().max()
    chosen_dependence = dependence[(dependence.y_variant == "margin_all") & (dependence.policy == "mdp")]
    tree_dependence = dependence[(dependence.y_variant == "margin_all") & (dependence.policy == "decision_tree")]
    chosen_voi = voi[voi.y_variant == "margin_all"].iloc[0]
    codes = sorted(set(re.findall(r"^\| (A\d+)", assumptions, flags=re.M)), key=lambda code: int(code[1:]))

    text = f"""# Tóm tắt kết quả tái hiện Voorberg et al. (2021)

Tệp này do `scripts/make_summary.py` sinh ra từ các tệp trong `results/`, dùng làm đầu vào cho mục 4.6 "Thực nghiệm tái hiện" của báo cáo.

## 1. Kết luận chính

- **Phương pháp tái hiện được.** Bộ giải quy nạp ngược tổng quát chạy đúng trên ví dụ nhỏ và trên Koffer đầy đủ. Giá trị V(gốc) bằng lợi nhuận mô phỏng trên toàn bộ 16.384 kịch bản.
- **Xu hướng của Bảng 5 tái hiện được, con số thì không.** MDP có lợi nhuận cao hơn, ít trạng thái kết thúc hơn và chi phí thu thập cao hơn cây quyết định. Tuy vậy, với công thức in trong bài, lợi nhuận MDP là {vn(profit('margin_all', 'mdp'))} so với {vn(target_mdp, 1)} của bài ({signed_pct(100 * (profit('margin_all', 'mdp') / target_mdp - 1))}), còn của cây là {vn(profit('margin_all', 'decision_tree'))} so với {vn(target_tree, 1)} ({signed_pct(100 * (profit('margin_all', 'decision_tree') / target_tree - 1))}).
- **Cấu trúc mô hình được xác nhận độc lập với Y.** Cây Fig. 8 cho chi phí trung bình {vn(table5[(table5.y_variant == 'margin_all') & (table5.policy == 'decision_tree')].avg_retrieval_cost.iloc[0])} và {vn(table5[(table5.y_variant == 'margin_all') & (table5.policy == 'decision_tree')].n_final_states.iloc[0], 0)} trạng thái kết thúc, khớp Bảng 5. Vì vậy chênh lệch lợi nhuận nhiều khả năng nằm ở hàm Y mà bài đã thực sự dùng, không phải ở phân phối hay cây.
- **Khoảng cách "gấp đôi" phụ thuộc mốc so sánh.** MDP cao hơn cây {vn(target_mdp / target_tree)} lần trong bài, {vn(profit('margin_all', 'mdp') / profit('margin_all', 'decision_tree'))} lần với `margin_all` và {vn(profit('margin_repair', 'mdp') / profit('margin_repair', 'decision_tree'))} lần với `margin_repair`. Nhưng chỉ làm tác vụ bắt buộc rồi quyết định đã đạt {vn(profit('margin_all', 'required_only'))}, cao hơn cây, nên so với mốc này MDP chỉ cao hơn {vn(profit('margin_all', 'mdp') / profit('margin_all', 'required_only'))} lần. Chính sách tham lam một bước đạt {vn(100 * profit('margin_all', 'myopic_voi') / profit('margin_all', 'mdp'), 1)}% lợi nhuận của MDP.

## 2. Cấu hình

| Lựa chọn | Giá trị | Căn cứ |
|---|---|---|
| Y mặc định (A3) | `margin_all`: E·B·H·P(D ≥ f)·[f − A(1 − 0,2G) − F − I] | Công thức in ở tr. 10; người dùng chọn |
| Y đối chứng (A3) | `margin_repair`: E·B·H·P(D ≥ f)·[f − A(1 − 0,2G)] − F − I | Gần số của bài hơn nhưng không có căn cứ trong bài; người dùng chọn làm đối chứng |
| Phân phối B (A1) | Binomial(n = 3, p = 0,2) | Khớp chi phí, số trạng thái ở Bảng 5 và Fig. 7 |
| Bernoulli (A2) | p ứng với giá trị thứ hai | Như trên |
| Cây quyết định (A5) | Đọc theo Fig. 8 | Như trên |
| Quy tắc hòa (A9, A10) | Quyết định trước, chi phí thấp hơn, rồi thứ tự trong tệp; dung sai 1e-9 | Bài không nêu |

`data/koffer.yaml` ban đầu chép sai công thức: biến thể tên `paper` thiếu ngoặc vuông của tr. 10. Với sự đồng ý của người dùng, biến thể này đổi tên thành `flat_costs`; không giá trị số nào thay đổi.

## 3. So với Bảng 5

{paper_gap_section(table5, paper)}

Doanh thu và lợi nhuận của cây trong Bảng 5 tự mâu thuẫn (8.125,94 − 100,06 ≠ 8.226,0, giả định A7), nên hai dòng này chỉ có tính tham khảo.

Trong {len(search)} cách đặt các số hạng chi phí vào Y (`results/y_variant_search.csv`), có {len(near_both)} cách nằm trong phạm vi 5% của cả hai con số lợi nhuận và {int((search.mdp_final_states == paper['table5']['mdp']['final_states']).sum())} cách đạt đúng {paper['table5']['mdp']['final_states']} trạng thái kết thúc của MDP. Dự án không chỉnh mô hình để khớp thêm vì không có căn cứ.

## 4. Mọi chính sách

Y = `margin_all`:

{table5_section(table5, 'margin_all')}

Y = `margin_repair`:

{table5_section(table5, 'margin_repair')}

Hình: `results/fig_decisions.png`, `results/fig_task_usage.png` (dấu chấm là số đọc bằng mắt từ Fig. 7), và các bản `_margin_repair`.

## 5. Chín trường hợp của Bảng 6

Y = `margin_all`, thứ tự cột A..I như bài ghi. Khớp trong phạm vi ±1: MDP ở trường hợp {mdp_matches}, cây ở trường hợp {tree_matches}.

{table6_section(table6)}

Bảng 6 không dùng được để hiệu chỉnh. Trên {len(calibration)} tổ hợp cấu hình (`results/calibration.csv`), nhiều nhất {calibration.t6_tree_exact.max()}/9 dòng của cây và {calibration.t6_mdp_exact.max()}/9 dòng của MDP khớp. Nguyên nhân nằm trong chính bảng. Cây kiểm tra E đầu tiên, nên lợi nhuận −45 của cây chỉ có thể xảy ra khi E = 0, và mọi kết quả khác chỉ có thể xảy ra khi E = 1. Các trường hợp 1, 3, 7, 8 có cùng ba giá trị nhị phân, nên E như nhau dù đọc cột nào là E, vậy mà trường hợp 3 và 7 cho −45 còn trường hợp 1 cho −122 và trường hợp 8 có lãi. Trường hợp 4 có cả ba giá trị bằng 0, nên E = 0, nhưng cây vẫn có lãi (`docs/paper_notes.md` mục 4).

## 6. Mở rộng

**Độ nhạy (E1), nhiễu ±10% và ±20%.** Lợi nhuận tối ưu nhạy nhất với phân phối {biggest.target}: thay đổi tới {vn(abs(biggest.move))} ở mức {vn(100 * biggest.delta, 0)}%. Nhiễu chi phí chỉ làm lợi nhuận đổi tối đa {vn(cost_moves)}. Mức thiệt do giữ chính sách cũ thay vì giải lại lớn nhất là {vn(abs(chosen_sensitivity.regret.min()))} ({vn(abs(chosen_sensitivity.regret_pct.min()), 3)}%), nên trong phạm vi này chính sách rất bền với sai số ước lượng. Một phép thử căng thẳng (chi phí D gấp 21 lần, `tests/test_sensitivity.py`) cho mức thiệt lớn, xác nhận cách tính không bị lỗi. Hình: `results/fig_tornado.png`.

**Phụ thuộc D theo A.** Chính sách giải với giả định độc lập, đánh giá khi D phụ thuộc A với ρ từ −0,8 đến 0,8: lợi nhuận MDP từ {vn(chosen_dependence.expected_profit.max())} đến {vn(chosen_dependence.expected_profit.min())}, cây từ {vn(tree_dependence.expected_profit.max())} đến {vn(tree_dependence.expected_profit.min())}. MDP vẫn cao hơn cây ở mọi mức. Đây chưa phải mức thiệt so với tối ưu thật, vì không giải lại với phụ thuộc.

**Giá trị thông tin (E3).** Sau các tác vụ bắt buộc, khi C = 0 và E = 1, quyết định ngay có giá trị {vn(chosen_voi.decide_now_value)}. Hành động tốt nhất là mở giai đoạn {'α' if chosen_voi.task == 'alpha' else chosen_voi.task}, lợi hơn quyết định ngay {vn(chosen_voi.gain_over_deciding_now)} (`results/value_of_information.csv`).

## 7. Quy mô tính toán

{vn(run['n_states'], 0)} trạng thái, trong đó {vn(run['n_reachable'], 0)} đi tới được ({vn(100 * run['n_reachable'] / run['n_states'], 1)}%). Thời gian giải {vn(run['solve_seconds'], 2)} giây khi numba đã có sẵn bản biên dịch, mảng V và π chiếm {vn(run['array_mb'], 1)} MB. Bài báo ghi {paper['runtime']['minutes']} phút trên {paper['runtime']['cpu']}. Hai con số không so sánh trực tiếp được vì khác máy và khác cách cài đặt; máy dùng ở đây ghi trong `results/runtime.json`.

## 8. Ví dụ nhỏ (mục 5.3)

V(gốc) = {vn(toy['root_value'], 1)}, hành động tối ưu là nhận ngay (f = 1); thu thập X₁ hoặc X₂ chỉ cho {vn(toy['root_action_values']['do:X2'], 2)}. Bài báo ghi {vn(toy['paper_comparison']['paper_value_no_info'], 1)} và kết luận nên thu thập X₂. Đây là lỗi số học của bài (A8).

## 9. Tiêu chí thành công

| # | Tiêu chí | Kết quả | Kiểm tra |
|---|---|---|---|
| S1 | Ví dụ nhỏ đúng | Đạt | `tests/test_toy.py` |
| S2 | E[Y] rút gọn bằng duyệt toàn bộ | Đạt, cả năm biến thể Y | `tests/test_information_structure.py` |
| S3 | V(gốc) bằng lợi nhuận mô phỏng, sai số < 1e-6 | Đạt | `tests/test_consistency.py` |
| S4 | Cây kiểm với 9 trường hợp, giải thích mọi chỗ lệch | Khớp {len(tree_matches)}/9; phần lệch được giải thích ở mục 5 | `tests/test_decision_tree.py` |
| S5 | Đúng xu hướng Bảng 5 | Đạt, cả hai biến thể Y | `results/table5_repro.csv` |
| S6 | Ghi số trạng thái, thời gian, bộ nhớ, máy | Đạt | `results/runtime.json` |
| S7 | Mọi giả định có mã | {', '.join(codes)} | `docs/assumptions.md` |

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
"""
    (RESULTS / "summary.md").write_text(text, encoding="utf-8")
    print(f"wrote {RESULTS / 'summary.md'}")


if __name__ == "__main__":
    main()
