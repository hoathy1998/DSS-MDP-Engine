"""Extensions of Phase 5: sensitivity (E1), dependence between attributes, value of information (E3)."""
from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from typing import Any

from dipmdp.data import attribute_probs
from dipmdp.evaluate import policy_statistics, scenarios
from dipmdp.model import DIPModel, State
from dipmdp.policies import best_decision
from dipmdp.solver import ArraySolution, solve_array

DELTAS = (-0.2, -0.1, 0.1, 0.2)


def _position_scores(n: int) -> list[float]:
    """Each value's position on [-1, 1], lowest value first."""
    return [2 * i / (n - 1) - 1 for i in range(n)]


def tilted_probs(probs: list[float], delta: float) -> list[float]:
    """Shift probability mass towards higher values (delta > 0) or lower ones (assumption A13)."""
    weights = [p * (1 + delta * score) for p, score in zip(probs, _position_scores(len(probs)))]
    total = sum(weights)
    return [weight / total for weight in weights]


def perturb_cost(data: dict[str, Any], task_id: str, delta: float) -> dict[str, Any]:
    result = deepcopy(data)
    for item in result["plan_items"] + result["attributes"]:
        if item["id"] == task_id:
            item["cost"] = item["cost"] * (1 + delta)
    return result


def perturb_distribution(data: dict[str, Any], attr_id: str, delta: float) -> dict[str, Any]:
    result = deepcopy(data)
    for attr in result["attributes"]:
        if attr["id"] == attr_id:
            attr["distribution"] = {"type": "categorical", "probs": tilted_probs(attribute_probs(attr), delta)}
    return result


def all_targets(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Every positive cost and every attribute's distribution."""
    targets = [("cost", item["id"]) for item in data["plan_items"] + data["attributes"] if item["cost"]]
    return targets + [("distribution", attr["id"]) for attr in data["attributes"]]


def sensitivity_rows(
    data: dict[str, Any],
    y_variant: str,
    targets: list[tuple[str, str]] | None = None,
    deltas: tuple[float, ...] = DELTAS,
) -> list[dict[str, Any]]:
    """For each perturbation: (a) profit of the old policy under the new truth, (b) profit after re-solving."""
    base_model = DIPModel(data, y_variant=y_variant, y_method="plugin")
    base = solve_array(base_model)

    rows = []
    for kind, target in all_targets(data) if targets is None else targets:
        for delta in deltas:
            perturb = perturb_cost if kind == "cost" else perturb_distribution
            model = DIPModel(perturb(data, target, delta), y_variant=y_variant, y_method="plugin")
            resolved = solve_array(model)
            old_policy_profit = policy_statistics(model, base.policy).expected_profit
            rows.append(
                {
                    "y_variant": y_variant,
                    "kind": kind,
                    "target": target,
                    "delta": delta,
                    "base_profit": round(base.root_value, 2),
                    "old_policy_profit": round(old_policy_profit, 2),
                    "resolved_profit": round(resolved.root_value, 2),
                    "regret": round(old_policy_profit - resolved.root_value, 2),
                    "regret_pct": round(100 * (old_policy_profit - resolved.root_value) / abs(resolved.root_value), 3),
                }
            )
    return rows


def correlated_scenarios(model: DIPModel, strength: float) -> Iterator[tuple[float, dict[str, Any]]]:
    """The model's scenarios with P(D | A) proportional to P(D) * (1 + strength * score(A) * score(D)).

    Scores are symmetric and P(D) of Koffer is symmetric, so both marginals stay as they are.
    """
    a_values = next(attr for attr in model.attributes if attr["id"] == "A")["values"]
    d_values = next(attr for attr in model.attributes if attr["id"] == "D")["values"]
    a_scores = dict(zip(a_values, _position_scores(len(a_values))))
    d_scores = dict(zip(d_values, _position_scores(len(d_values))))
    for prob, values in scenarios(model):
        yield prob * (1 + strength * a_scores[values["A"]] * d_scores[values["D"]]), values


def value_of_gathering(solution: ArraySolution, state: State) -> dict[str, Any]:
    """Each allowed task's expected profit against the best final decision available right now (E3)."""
    model = solution.model
    decision, decide_now = best_decision(model, state)
    q = solution.action_values(state)
    return {
        "decide_now": decide_now,
        "best_decision": decision,
        "value": solution.value(state),
        "gain_by_task": {action[1]: value - decide_now for action, value in q.items() if action[0] == "do"},
    }
