"""Phase 6: Streamlit demo of the MDP recommender (cf. Fig. 6 of the paper).

Page 1 – Koffer case simulation
  - sample or enter hidden true values; show current state (done items, known attributes)
  - table of allowed actions with expected profit, highlight the recommended one
  - user may pick any allowed action (including deviating); recommender continues from new state
  - at the end: realised profit vs the decision tree on the same case
Page 2 – Toy example (Section 5.3) to explain value of information

Run: streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from dipmdp.data import DATA_DIR, load_decision_tree, load_koffer, load_model
from dipmdp.decision_tree import run_tree
from dipmdp.evaluate import scenarios, simulate_policy
from dipmdp.information_structure import realised_y
from dipmdp.model import Action, DIPModel
from dipmdp.solver import ArraySolution, Solution, load_solution, solve_array, solve_recursive

RESULTS = Path(__file__).resolve().parents[1] / "results"
POLICY_FILES = {"margin_all": "policy_koffer.npz", "margin_repair": "policy_koffer_margin_repair.npz"}
VARIANT_LABELS = {
    "margin_all": "margin_all: công thức in trong bài (tr. 10)",
    "margin_repair": "margin_repair: đối chứng, F và I tính một lần cho mỗi hợp đồng",
}
PAGES = ("Mô phỏng hồ sơ Koffer", "Ví dụ nhỏ của bài báo")
UNKNOWN = "chưa biết"
DEFAULT_SEED = 42


@st.cache_resource(show_spinner="Đang tải chính sách MDP...")
def koffer_solution(y_variant: str) -> ArraySolution:
    model = DIPModel(load_koffer(), y_variant=y_variant, y_method="plugin")
    path = RESULTS / POLICY_FILES[y_variant]
    if path.exists():
        solution, config = load_solution(path, model)
        if config["y_expression"] == model.y_expression:
            return solution
    return solve_array(model)


@st.cache_resource
def toy_solution() -> Solution:
    return solve_recursive(load_model(DATA_DIR / "toy.yaml"))


def task_name(model: DIPModel, task_id: str) -> str:
    task = model.task(task_id)
    return task.get("task", task.get("name", task_id))


def action_label(model: DIPModel, action: Action) -> str:
    kind, value = action
    if kind == "decide":
        return "Quyết định: không báo giá" if value == "No bid" else f"Quyết định: báo giá {value}"
    prefix = "Giai đoạn" if model.task(value).get("kind") == "stage" else "Tác vụ"
    return f"{prefix} {model.task(value).get('task_id', value)}: {task_name(model, value)}"


def start_case(true_values: dict[str, Any], model: DIPModel) -> None:
    st.session_state.case = {"true": true_values, "state": model.root_state, "cost": 0.0, "log": [], "decision": None}


def random_case(model: DIPModel, seed: int) -> dict[str, Any]:
    """Draw one scenario with its model probability, so a fixed seed always gives the same case."""
    all_scenarios = list(scenarios(model))
    weights = [prob for prob, _ in all_scenarios]
    return random.Random(seed).choices(all_scenarios, weights=weights)[0][1]


def show_state(model: DIPModel, case: dict[str, Any]) -> None:
    state = case["state"]
    known = [
        {
            "Thuộc tính": f"{attr['id']}. {attr['name']}",
            "Giá trị": UNKNOWN if not k else str(attr["values"][k - 1]),
        }
        for attr, k in zip(model.attributes, state[1])
    ]
    plan = [
        {"Mục kế hoạch": item["name"], "Trạng thái": "đã xong" if bit else "chưa làm"}
        for item, bit in zip(model.plan_items, state[0])
    ]
    left, right = st.columns(2)
    left.dataframe(pd.DataFrame(known), hide_index=True)
    right.dataframe(pd.DataFrame(plan), hide_index=True)


def koffer_page(y_variant: str) -> None:
    solution = koffer_solution(y_variant)
    model = solution.model
    st.header(PAGES[0])
    st.caption(
        "Giá trị thật của hồ sơ được giữ kín cho đến khi bạn quyết định. Bạn có thể làm khác khuyến nghị; "
        "hệ thống vẫn khuyến nghị tiếp từ trạng thái mới."
    )

    with st.expander("Tạo hồ sơ mới", expanded="case" not in st.session_state):
        seed = st.number_input("Seed của hồ sơ ngẫu nhiên", min_value=0, value=DEFAULT_SEED, step=1)
        if st.button("Tạo hồ sơ ngẫu nhiên"):
            start_case(random_case(model, int(seed)), model)
            st.rerun()
        st.markdown("Hoặc tự nhập giá trị thật:")
        columns = st.columns(3)
        chosen = {
            attr["id"]: columns[position % 3].selectbox(attr["name"], attr["values"], key=f"manual_{attr['id']}")
            for position, attr in enumerate(model.attributes)
        }
        if st.button("Tạo hồ sơ từ giá trị đã nhập"):
            start_case(chosen, model)
            st.rerun()

    case = st.session_state.get("case")
    if case is None:
        st.info("Hãy tạo một hồ sơ để bắt đầu.")
        return

    show_state(model, case)
    st.metric("Chi phí thu thập đã bỏ ra", f"{case['cost']:,.1f}")
    if case["decision"] is None:
        action_step(solution, case)
    else:
        result_step(solution, case)


def action_step(solution: ArraySolution, case: dict[str, Any]) -> None:
    model = solution.model
    state = case["state"]
    q = solution.action_values(state)
    recommended = solution.policy(state)
    ordered = sorted(q, key=lambda action: (-q[action], model.tie_break_key(action)))

    st.subheader("Các hành động được phép")
    st.dataframe(
        pd.DataFrame(
            {
                "Hành động": [action_label(model, action) for action in ordered],
                "Lợi nhuận kỳ vọng nếu chọn": [round(q[action], 1) for action in ordered],
                "Khuyến nghị": ["★" if action == recommended else "" for action in ordered],
            }
        ),
        hide_index=True,
    )
    st.caption("Lợi nhuận kỳ vọng tính từ thời điểm này, không gồm chi phí đã bỏ ra.")
    choice = st.radio(
        "Chọn hành động",
        ordered,
        index=ordered.index(recommended),
        format_func=lambda action: action_label(model, action),
    )
    if st.button("Thực hiện", type="primary"):
        case["log"].append(
            {
                "Hành động": action_label(model, choice),
                "Theo khuyến nghị": "có" if choice == recommended else "không",
                "Khuyến nghị lúc đó": action_label(model, recommended),
            }
        )
        if choice[0] == "decide":
            case["decision"] = choice[1]
        else:
            case["cost"] -= model.reward(state, choice)
            case["state"] = model.do(state, choice, case["true"])
        st.rerun()


def result_step(solution: ArraySolution, case: dict[str, Any]) -> None:
    model = solution.model
    true_values = case["true"]
    revenue = realised_y(model, true_values, case["decision"])
    mdp_run = simulate_policy(model, solution.policy, true_values)
    tree_run = run_tree(load_decision_tree(), model, true_values)
    st.subheader("Kết quả trên cùng hồ sơ")
    st.dataframe(
        pd.DataFrame(
            [
                ("Lựa chọn của bạn", case["decision"], case["cost"], revenue, revenue - case["cost"]),
                ("Theo đúng MDP", mdp_run.decision, mdp_run.cost, mdp_run.revenue, mdp_run.profit),
                ("Cây quyết định (Fig. 8)", tree_run.decision, tree_run.cost, tree_run.revenue, tree_run.profit),
            ],
            columns=["Cách làm", "Quyết định", "Chi phí", "Doanh thu kỳ vọng", "Lợi nhuận"],
        ).astype({"Quyết định": str}).round(1),
        hide_index=True,
    )
    st.caption(
        "Doanh thu là Y tại giá trị thật của hồ sơ, vẫn tính theo xác suất báo giá được chấp nhận P(D ≥ f), "
        "vì bản thân giá thị trường là ngẫu nhiên. Vì vậy MDP có thể thua trên một hồ sơ riêng lẻ dù tốt nhất về kỳ vọng."
    )
    with st.expander("Giá trị thật của hồ sơ"):
        st.write({key: value for key, value in true_values.items()})
    with st.expander("Các bước đã làm"):
        st.dataframe(pd.DataFrame(case["log"]), hide_index=True)
    if st.button("Làm lại hồ sơ này"):
        start_case(true_values, model)
        st.rerun()


def toy_page() -> None:
    solution = toy_solution()
    model = solution.model
    st.header(PAGES[1])
    st.markdown(
        "Hai thuộc tính X₁ ∈ {0, 3} và X₂ ∈ {1, 4}, mỗi giá trị xác suất 0,5, chi phí 0,5 cho mỗi lần thu thập. "
        "Lợi nhuận Y = (X₂ − X₁)·f, với f = 1 là nhận và f = 0 là từ chối."
    )
    st.warning(
        "Bài báo (mục 5.3) ghi lợi nhuận khi chưa có thông tin là 0,5 và kết luận nên thu thập X₂. "
        "Tính lại cho thấy giá trị đúng là E[X₂ − X₁] = 1,0, nên quyết định ngay là tối ưu (giả định A8)."
    )
    columns = st.columns(2)
    state = model.root_state
    for column, attr in zip(columns, model.attributes):
        value = column.selectbox(f"{attr['id']} đã biết bằng", [UNKNOWN, *attr["values"]], key=f"toy_{attr['id']}")
        if value != UNKNOWN:
            state = model.observe(state, attr["id"], value)

    q = solution.action_values(state)
    recommended = solution.policy(state)
    st.metric("Lợi nhuận kỳ vọng tốt nhất từ trạng thái này", f"{solution.value(state):.2f}")
    labels = {0: "Quyết định: từ chối (f = 0)", 1: "Quyết định: nhận (f = 1)"}
    st.dataframe(
        pd.DataFrame(
            {
                "Hành động": [
                    labels[value] if kind == "decide" else f"Thu thập {value}, chi phí 0,5" for kind, value in q
                ],
                "Lợi nhuận kỳ vọng nếu chọn": [round(value, 2) for value in q.values()],
                "Khuyến nghị": ["★" if action == recommended else "" for action in q],
            }
        ),
        hide_index=True,
    )
    st.caption("Thông tin chỉ đáng mua khi nó có thể đổi quyết định đủ nhiều để bù chi phí.")


def main() -> None:
    st.set_page_config(page_title="Bộ khuyến nghị MDP", layout="wide")
    st.title("Bộ khuyến nghị MDP cho quy trình ra quyết định")
    st.caption("Tái hiện Voorberg et al. (2021), Decision Support Systems 151, 113632.")
    page = st.sidebar.radio("Màn hình", PAGES)
    if page == PAGES[1]:
        toy_page()
        return
    y_variant = st.sidebar.radio("Công thức Y", list(POLICY_FILES), format_func=VARIANT_LABELS.get)
    if st.session_state.get("y_variant") != y_variant:
        st.session_state.y_variant = y_variant
        st.session_state.pop("case", None)
    koffer_page(y_variant)


main()
