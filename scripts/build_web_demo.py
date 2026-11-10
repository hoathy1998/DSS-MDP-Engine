"""Build web/koffer_demo.html: one self-contained page whose numbers all come from data/ and results/."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from dipmdp.data import load_decision_tree, load_koffer, load_paper_results, load_toy
from dipmdp.information_structure import accept_probability
from dipmdp.model import DIPModel, without_free_tasks

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
OUTPUT = WEB / "koffer_demo.html"
KOFFER_VARIANTS = ("margin_all", "margin_repair")  # as chosen in docs/assumptions.md, A3
SAFE_EXPRESSION = re.compile(r"^[A-Za-z0-9_*+\-/(). ]+$")


def model_spec(data: dict[str, Any], variants: tuple[str, ...]) -> dict[str, Any]:
    model = DIPModel(data, y_variant=variants[0], y_method="plugin")
    spec: dict[str, Any] = {
        "default_variant": variants[0],
        "decisions": list(model.decisions),
        "plan_items": [
            {key: item[key] for key in ("id", "cost", "preceding", "required")} for item in model.plan_items
        ],
        "attributes": [
            {
                "id": attr["id"],
                "task_id": attr["task_id"],
                "cost": attr["cost"],
                "preceding": attr["preceding"],
                "required": attr["required"],
                "values": attr["values"],
                "probs": model.attribute_probs[attr["id"]],
                "mean": model.attribute_means[attr["id"]],
            }
            for attr in model.attributes
        ],
        "variants": {
            variant: {
                "expression": data["information_structure"]["variants"][variant],
                "free": [task["id"] for task in without_free_tasks(data, variant)[1]],
            }
            for variant in variants
        },
        "accept": None,
    }
    sigma = model.market_price_sigma
    if sigma is not None:
        market = next(attr for attr in model.attributes if attr["id"] == "D")
        probs = model.attribute_probs["D"]
        spec["accept"] = {}
        for decision in model.decisions:
            if isinstance(decision, str):
                continue
            by_value = [accept_probability(float(value), float(decision), sigma) for value in market["values"]]
            spec["accept"][str(decision)] = {
                "by_value": by_value,
                "unknown": sum(p * value for p, value in zip(probs, by_value)),
            }
    return spec


def y_function(spec: dict[str, Any], variant: str) -> str:
    expression = spec["variants"][variant]["expression"]
    if not SAFE_EXPRESSION.match(expression):
        raise ValueError(f"unexpected characters in Y expression: {expression!r}")
    names = [attr["id"] for attr in spec["attributes"]] + ["f"] + (["P"] if spec["accept"] else [])
    return f"({{{', '.join(names)}}}) => ({expression})"


def table5_rows() -> list[dict[str, str]]:
    with open(ROOT / "results" / "table5_repro.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(line for line in f if not line.startswith("#")))

    def lookup(variant: str, policy: str, column: str) -> float:
        return float(next(r[column] for r in rows if r["y_variant"] == variant and r["policy"] == policy))

    def vn(value: float, digits: int) -> str:
        return f"{value:,.{digits}f}".replace(",", "§").replace(".", ",").replace("§", ".")

    table5 = load_paper_results()["table5"]
    result = []
    for policy, label in (("mdp", "MDP"), ("decision_tree", "Cây")):
        for name, paper_key, column, digits in (
            ("lợi nhuận kỳ vọng", "expected_profit", "expected_profit", 2),
            ("chi phí trung bình", "avg_retrieval_cost", "avg_retrieval_cost", 2),
            ("số trạng thái kết thúc", "final_states", "n_final_states", 0),
        ):
            result.append(
                {
                    "label": f"{label}: {name}",
                    "paper": vn(float(table5[policy][paper_key]), digits),
                    "margin_all": vn(lookup("margin_all", policy, column), digits),
                    "margin_repair": vn(lookup("margin_repair", policy, column), digits),
                }
            )
    return result


def build_data() -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    paper = load_paper_results()
    koffer = model_spec(load_koffer(), KOFFER_VARIANTS)
    toy = model_spec(load_toy(), ("toy",))
    data = {
        "koffer": koffer,
        "toy": toy,
        "tree": load_decision_tree(),
        "table6": paper["table6"],
        "table5": table5_rows(),
        "paper_toy": paper["toy_example"]["claimed"],
    }
    functions = {
        "koffer": {variant: y_function(koffer, variant) for variant in KOFFER_VARIANTS},
        "toy": {"toy": y_function(toy, "toy")},
    }
    return data, functions


def functions_source(functions: dict[str, dict[str, str]]) -> str:
    groups = ",\n".join(
        f"  {model}: {{\n"
        + ",\n".join(f"    {variant}: {code}" for variant, code in variants.items())
        + "\n  }"
        for model, variants in functions.items()
    )
    return f"const Y_FUNCTIONS = {{\n{groups}\n}};"


def main() -> None:
    data, functions = build_data()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    module_tail = re.compile(r'\nif \(typeof module !== "undefined"\).*\n')
    page = (
        (WEB / "template.html").read_text(encoding="utf-8")
        .replace("/*__DATA__*/", f"const DEMO_DATA = {payload};\n{functions_source(functions)}")
        .replace("/*__SOLVER__*/", module_tail.sub("\n", (WEB / "solver.js").read_text(encoding="utf-8")))
        .replace("/*__APP__*/", module_tail.sub("\n", (WEB / "app.js").read_text(encoding="utf-8")))
    )
    OUTPUT.write_text(page, encoding="utf-8", newline="\n")
    # A copy of the data for tests/web_demo_check.js, which runs the same code in Node.
    (WEB / "demo_data.json").write_text(
        json.dumps({"data": data, "functions": functions}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
