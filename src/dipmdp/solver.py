"""Backward induction solvers. (Phase 1 and Phase 3)

Solution interface (used by tests/test_toy.py):
- solution.model
- solution.root_state, solution.root_value, solution.root_action
- solution.value(state) -> float
- solution.policy(state) -> action
- solution.action_values(state) -> dict[action, float]   # Q(s, a) for all allowed a

Tie-break (assumption A9): prefer "decide", then lower cost, then YAML order.
Q-values within TIE_TOLERANCE count as tied, so rounding noise cannot change the policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from dipmdp.model import Action, DIPModel, State

TIE_TOLERANCE = 1e-9


@dataclass
class Solution:
    model: DIPModel
    root_state: State
    root_value: float
    root_action: Action
    _values: dict[State, float]
    _policies: dict[State, Action]
    _action_values: dict[State, dict[Action, float]]

    def value(self, state: State) -> float:
        return self._values[state]

    def policy(self, state: State) -> Action:
        return self._policies[state]

    def action_values(self, state: State) -> dict[Action, float]:
        return dict(self._action_values[state])


def solve_recursive(model: DIPModel) -> Solution:
    """Exact dynamic-programming reference implementation, over states reachable from the root."""
    values: dict[State, float] = {}
    policies: dict[State, Action] = {}
    action_values: dict[State, dict[Action, float]] = {}

    @lru_cache(maxsize=None)
    def V(state: State) -> float:
        q = {
            action: model.reward(state, action)
            + sum(prob * V(next_state) for prob, next_state in model.transitions(state, action))
            for action in model.allowed_actions(state)
        }
        if not q:
            raise ValueError(f"no allowed action in state {state!r}; check the precedence constraints")
        best_value = max(q.values())
        values[state] = best_value
        policies[state] = min(
            (action for action, value in q.items() if best_value - value <= TIE_TOLERANCE),
            key=model.tie_break_key,
        )
        action_values[state] = q
        return best_value

    root_state = model.root_state
    root_value = V(root_state)
    return Solution(
        model=model,
        root_state=root_state,
        root_value=root_value,
        root_action=policies[root_state],
        _values=values,
        _policies=policies,
        _action_values=action_values,
    )


def solve_array(model: DIPModel) -> Solution:
    raise NotImplementedError("Phase 3")
