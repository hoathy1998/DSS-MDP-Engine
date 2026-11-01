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

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from numba import njit

from dipmdp.information_structure import MARKET_ATTRIBUTE, accept_probability
from dipmdp.model import Action, DIPModel, State

TIE_TOLERANCE = 1e-9
UNREACHABLE = -1


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


@dataclass
class ArraySolution:
    """V and pi for every encoded state; same interface as Solution, plus action_of_code for saved policies.

    Index = mixed-radix code of (plan_bits, info), YAML order, last digit least significant.
    pi[i] = task position in YAML order, or n_tasks + decision position; UNREACHABLE for an invalid state.
    """

    model: DIPModel
    values: np.ndarray
    policy_codes: np.ndarray

    @property
    def root_state(self) -> State:
        return self.model.root_state

    @property
    def root_value(self) -> float:
        return float(self.values[0])

    @property
    def root_action(self) -> Action:
        return self.policy(self.root_state)

    @property
    def n_reachable(self) -> int:
        return int(np.count_nonzero(self.policy_codes != UNREACHABLE))

    def value(self, state: State) -> float:
        return float(self.values[encode_state(self.model, state)])

    def policy(self, state: State) -> Action:
        return action_of_code(self.model, int(self.policy_codes[encode_state(self.model, state)]))

    def action_values(self, state: State) -> dict[Action, float]:
        return {
            action: self.model.reward(state, action)
            + sum(prob * self.value(next_state) for prob, next_state in self.model.transitions(state, action))
            for action in self.model.allowed_actions(state)
        }


def _strides(model: DIPModel) -> list[int]:
    radices = [2] * len(model.plan_items) + [len(attr["values"]) + 1 for attr in model.attributes]
    strides = [1] * len(radices)
    for position in range(len(radices) - 2, -1, -1):
        strides[position] = strides[position + 1] * radices[position + 1]
    return strides


def encode_state(model: DIPModel, state: State) -> int:
    return sum(digit * stride for digit, stride in zip(state[0] + state[1], _strides(model)))


def action_of_code(model: DIPModel, code: int) -> Action:
    tasks = model.plan_items + model.attributes
    if code == UNREACHABLE:
        raise ValueError("state is not reachable")
    if code < len(tasks):
        return ("do", tasks[code]["id"])
    return ("decide", model.decisions[code - len(tasks)])


def _decision_table(model: DIPModel) -> np.ndarray:
    """E[Y(s, f)] for every information state and decision, by evaluating Y on arrays (PLAN 7.3)."""
    radices = [len(attr["values"]) + 1 for attr in model.attributes]
    grids = np.indices(radices, sparse=True) if radices else ()
    scope_base = {
        attr["id"]: np.array([model.attribute_means[attr["id"]], *map(float, attr["values"])])[grid]
        for attr, grid in zip(model.attributes, grids)
    }
    table = np.zeros((int(np.prod(radices)), len(model.decisions)))
    for column, decision in enumerate(model.decisions):
        if isinstance(decision, str):
            continue
        f = float(decision)
        scope = dict(scope_base, f=f)
        if model.market_price_sigma is not None:
            market = next(attr for attr in model.attributes if attr["id"] == MARKET_ATTRIBUTE)
            accept = [accept_probability(float(value), f, model.market_price_sigma) for value in market["values"]]
            unknown = float(np.dot(model.attribute_probs[MARKET_ATTRIBUTE], accept))
            grid = grids[model.attribute_index[MARKET_ATTRIBUTE]]
            scope["P"] = np.array([unknown, *accept])[grid]
        result = eval(model.y_code, {"__builtins__": {}}, scope)
        table[:, column] = np.broadcast_to(result, radices).ravel()
    return table


@njit(cache=True)
def _backward_induction(
    n_states: int,
    strides: np.ndarray,
    n_info_states: int,
    costs: np.ndarray,
    n_outcomes: np.ndarray,
    outcome_probs: np.ndarray,
    preceding: np.ndarray,
    required: np.ndarray,
    decision_table: np.ndarray,
    rank_tasks: np.ndarray,
    tolerance: float,
) -> tuple[np.ndarray, np.ndarray]:
    n_tasks = len(strides)
    n_decisions = decision_table.shape[1]
    values = np.full(n_states, np.nan)
    policy = np.full(n_states, -1, dtype=np.int8)
    digits = np.zeros(n_tasks, dtype=np.int64)
    done = np.zeros(n_tasks, dtype=np.bool_)
    task_q = np.zeros(n_tasks)
    enabled = np.zeros(n_tasks, dtype=np.bool_)

    # A task's successors always have a larger code, so descending order sees them first.
    for index in range(n_states - 1, -1, -1):
        remainder = index
        for position in range(n_tasks):
            digits[position] = remainder // strides[position]
            remainder -= digits[position] * strides[position]
            done[position] = digits[position] != 0

        # Reachable iff every done task has all its predecessors done.
        valid = True
        for position in range(n_tasks):
            if done[position]:
                for other in range(n_tasks):
                    if preceding[position, other] and not done[other]:
                        valid = False
                        break
                if not valid:
                    break
        if not valid:
            continue

        best = -np.inf
        for position in range(n_tasks):
            enabled[position] = False
            if done[position]:
                continue
            allowed = True
            for other in range(n_tasks):
                if preceding[position, other] and not done[other]:
                    allowed = False
                    break
            if not allowed:
                continue
            q = -costs[position]
            stride = strides[position]
            for outcome in range(n_outcomes[position]):
                q += outcome_probs[position, outcome] * values[index + (outcome + 1) * stride]
            task_q[position] = q
            enabled[position] = True
            best = max(best, q)

        can_decide = True
        for position in range(n_tasks):
            if required[position] and not done[position]:
                can_decide = False
                break

        info_index = index % n_info_states
        if can_decide:
            for decision in range(n_decisions):
                best = max(best, decision_table[info_index, decision])

        # Assumption A9: decisions first in YAML order, then tasks by rank_tasks.
        chosen = -1
        if can_decide:
            for decision in range(n_decisions):
                if best - decision_table[info_index, decision] <= tolerance:
                    chosen = n_tasks + decision
                    break
        if chosen < 0:
            for position in rank_tasks:
                if enabled[position] and best - task_q[position] <= tolerance:
                    chosen = position
                    break
        values[index] = best
        policy[index] = chosen
    return values, policy


def solve_array(model: DIPModel) -> ArraySolution:
    """Backward induction over all encoded states (PLAN 7.4). Y must be multilinear (PLAN 7.3)."""
    tasks = model.plan_items + model.attributes
    positions = {item["id"]: position for position, item in enumerate(tasks)}
    n_tasks = len(tasks)
    preceding = np.zeros((n_tasks, n_tasks), dtype=np.bool_)
    for position, item in enumerate(tasks):
        for pre in item["preceding"]:
            preceding[position, positions[pre]] = True

    max_outcomes = max([len(attr["values"]) for attr in model.attributes], default=1)
    n_outcomes = np.ones(n_tasks, dtype=np.int64)
    outcome_probs = np.zeros((n_tasks, max_outcomes))
    outcome_probs[: len(model.plan_items), 0] = 1.0
    for attr in model.attributes:
        position = positions[attr["id"]]
        n_outcomes[position] = len(attr["values"])
        outcome_probs[position, : len(attr["values"])] = model.attribute_probs[attr["id"]]

    costs = np.array([float(item["cost"]) for item in tasks])
    strides = np.array(_strides(model), dtype=np.int64)
    table = _decision_table(model)
    # Lower cost first, then YAML order (stable sort), as in DIPModel.tie_break_key.
    rank_tasks = np.argsort(costs, kind="stable")
    values, policy_codes = _backward_induction(
        model.state_space_size(),
        strides,
        table.shape[0],
        costs,
        n_outcomes,
        outcome_probs,
        preceding,
        np.array([bool(item["required"]) for item in tasks]),
        table,
        rank_tasks,
        TIE_TOLERANCE,
    )
    return ArraySolution(model, values, policy_codes)


def save_solution(solution: ArraySolution, path: str | Path, config: dict[str, Any]) -> None:
    np.savez_compressed(
        path, values=solution.values, policy_codes=solution.policy_codes, config=json.dumps(config, ensure_ascii=False)
    )


def load_solution(path: str | Path, model: DIPModel) -> tuple[ArraySolution, dict[str, Any]]:
    with np.load(path) as saved:
        return ArraySolution(model, saved["values"], saved["policy_codes"]), json.loads(str(saved["config"]))
