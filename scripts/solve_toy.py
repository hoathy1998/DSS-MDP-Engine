"""Phase 1: solve the toy example of Section 5.3 and save results/toy.json (criterion S1)."""
from __future__ import annotations

import json
from pathlib import Path

from dipmdp.data import DATA_DIR, load_model, load_paper_results
from dipmdp.model import Action
from dipmdp.solver import TIE_TOLERANCE, solve_recursive

OUTPUT = Path(__file__).resolve().parents[1] / "results" / "toy.json"


def action_label(action: Action) -> str:
    kind, value = action
    return f"{kind}:{value}"


def main() -> None:
    model = load_model(DATA_DIR / "toy.yaml")
    solution = solve_recursive(model)
    paper = load_paper_results()["toy_example"]
    q = solution.action_values(solution.root_state)
    after_x2_high = model.observe(solution.root_state, "X2", 4)

    result = {
        "config": {
            "data": "data/toy.yaml",
            "y_variant": model.y_variant,
            "y_expression": model.y_expression,
            "solver": "solve_recursive",
            "tie_break": "A9",
            "tie_tolerance": TIE_TOLERANCE,
            "random_seed": None,
        },
        "root_value": solution.root_value,
        "root_action": action_label(solution.root_action),
        "root_action_values": {action_label(a): value for a, value in q.items()},
        "after_observing_X2_4": {
            "value": solution.value(after_x2_high),
            "action": action_label(solution.policy(after_x2_high)),
        },
        "paper_comparison": {
            "assumption": "A8",
            "paper_value_no_info": paper["claimed"]["value_no_info"],
            "paper_conclusion": paper["claimed"]["conclusion"],
            "difference_root_value": solution.root_value - paper["claimed"]["value_no_info"],
        },
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
