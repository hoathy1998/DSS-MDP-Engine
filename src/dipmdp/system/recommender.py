"""MDP recommender of Section 6.2: a look-up from a state to the action set, expected profits and the advice."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dipmdp.model import Action, DIPModel, State
from dipmdp.solver import ArraySolution


def action_to_json(action: Action) -> dict[str, Any]:
    kind, value = action
    return {"kind": "do", "id": value} if kind == "do" else {"kind": "decide", "decision": value}


def action_from_json(payload: dict[str, Any]) -> Action:
    kind = payload.get("kind")
    if kind == "do" and isinstance(payload.get("id"), str):
        return ("do", payload["id"])
    if kind == "decide" and isinstance(payload.get("decision"), (str, int, float)):
        return ("decide", payload["decision"])
    raise ValueError(f"unknown action: {payload!r}")


@dataclass(frozen=True)
class Recommendation:
    state: State
    best: Action
    value: float
    action_values: dict[Action, float]

    def to_json(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "best": action_to_json(self.best),
            "actions": [
                {**action_to_json(action), "expected_profit": q, "recommended": action == self.best}
                for action, q in sorted(self.action_values.items(), key=lambda item: -item[1])
            ],
        }


class MDPRecommender:
    """Holds no case data, so any number of cases can share one instance."""

    def __init__(self, model: DIPModel, solution: ArraySolution):
        self.model = model
        self.solution = solution

    def recommend(self, state: State) -> Recommendation:
        return Recommendation(
            state=state,
            best=self.solution.policy(state),
            value=self.solution.value(state),
            action_values=self.solution.action_values(state),
        )
