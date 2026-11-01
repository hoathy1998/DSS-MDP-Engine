"""Exact evaluation of a policy. (Phases 2 and 4)

Metrics (Table 5): expected_profit, expected_revenue, avg_retrieval_cost, n_final_states,
decision distribution (Fig. 7a), task usage share (Fig. 7b).

policy_statistics walks every outcome the policy can reach and scores each final state by E[Y | state].
evaluate simulates all 16,384 true-value scenarios and scores each by Y at the true values (A6).
The two agree because attributes the policy never acquires only enter through their expectation;
criterion S3 checks this against the solver's root value.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from itertools import product
from math import prod
from typing import Any

from dipmdp.information_structure import realised_y
from dipmdp.model import Action, DIPModel, State


@dataclass
class PolicyStatistics:
    expected_revenue: float = 0.0
    avg_retrieval_cost: float = 0.0
    final_states: set[State] = field(default_factory=set)
    decision_probs: dict[Any, float] = field(default_factory=lambda: defaultdict(float))
    task_usage: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def expected_profit(self) -> float:
        return self.expected_revenue - self.avg_retrieval_cost

    def add_task(self, task_id: str, prob: float, cost: float) -> None:
        self.task_usage[task_id] += prob
        self.avg_retrieval_cost += prob * cost

    def add_decision(self, model: DIPModel, state: State, decision: Any, prob: float) -> None:
        self.expected_revenue += prob * model.reward(state, ("decide", decision))
        self.decision_probs[decision] += prob
        self.final_states.add(state)


def policy_statistics(model: DIPModel, act: Callable[[State], Action]) -> PolicyStatistics:
    """Exact statistics of the deterministic policy `act` from the root state."""
    stats = PolicyStatistics()

    def walk(state: State, prob: float) -> None:
        action = act(state)
        kind, value = action
        if kind == "decide":
            stats.add_decision(model, state, value, prob)
            return
        stats.add_task(value, prob, -model.reward(state, action))
        for p, next_state in model.transitions(state, action):
            walk(next_state, prob * p)

    walk(model.root_state, 1.0)
    return stats


@dataclass(frozen=True)
class Run:
    decision: Any
    cost: float
    revenue: float
    final_state: State
    tasks: tuple[str, ...] = ()

    @property
    def profit(self) -> float:
        return self.revenue - self.cost


def simulate_policy(model: DIPModel, act: Callable[[State], Action], true_values: dict[str, Any]) -> Run:
    """One case with known attribute values; revenue is Y at the true values (assumption A6)."""
    state, cost = model.root_state, 0.0
    tasks: list[str] = []
    while True:
        action = act(state)
        if action[0] == "decide":
            return Run(action[1], cost, realised_y(model, true_values, action[1]), state, tuple(tasks))
        cost -= model.reward(state, action)
        tasks.append(action[1])
        state = model.do(state, action, true_values)


def scenarios(model: DIPModel) -> Iterator[tuple[float, dict[str, Any]]]:
    """Every combination of true attribute values, with its probability."""
    ids = [attr["id"] for attr in model.attributes]
    outcomes = [list(zip(attr["values"], model.attribute_probs[attr["id"]])) for attr in model.attributes]
    for combo in product(*outcomes):
        yield prod(p for _, p in combo), {attr_id: value for attr_id, (value, _) in zip(ids, combo)}


def evaluate(
    model: DIPModel,
    act: Callable[[State], Action],
    weighted_scenarios: Iterator[tuple[float, dict[str, Any]]] | None = None,
) -> PolicyStatistics:
    """Statistics of `act` over the scenarios; by default the independent ones of the model."""
    stats = PolicyStatistics()
    for prob, true_values in scenarios(model) if weighted_scenarios is None else weighted_scenarios:
        run = simulate_policy(model, act, true_values)
        stats.expected_revenue += prob * run.revenue
        stats.avg_retrieval_cost += prob * run.cost
        stats.decision_probs[run.decision] += prob
        stats.final_states.add(run.final_state)
        for task_id in run.tasks:
            stats.task_usage[task_id] += prob
    return stats
