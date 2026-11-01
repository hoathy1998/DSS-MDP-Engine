"""DIPModel: the MDP of Section 5.4. (Phase 1)

State
-----
Immutable tuple (plan_bits, info) where
- plan_bits: tuple[int, ...] of 0/1 for non-information plan items (stages, procedural tasks), YAML order;
- info: tuple[int, ...], one entry per attribute in YAML order; 0 = unknown (⊥), k = k-th value (1-based).
An information-acquiring task is "done" iff its attribute is known.

Actions
-------
("do", item_id)  item_id is a plan item id (e.g. "alpha", "2") or an attribute id (e.g. "A") meaning
                 "perform the task that acquires this attribute";
("decide", f)    f is a decision from `decisions`.

Rules (paper eqs. (5)-(9))
- ("do", x) allowed iff x not done and every id in x.preceding is done.
- ("decide", f) allowed iff every required item/attribute task is done.
- reward: -cost for "do"; E[Y(s, f)] for "decide" (see information_structure.py).
- transition: plan item -> its bit becomes 1 (prob 1); attribute -> each value with its marginal prob.
"""
from __future__ import annotations

from math import prod
from typing import Any

from dipmdp.data import attribute_probs
from dipmdp.information_structure import MARKET_ATTRIBUTE, expected_y

State = tuple[tuple[int, ...], tuple[int, ...]]
Action = tuple[str, Any]


def without_free_tasks(data: dict[str, Any], y_variant: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Remove required tasks that nothing depends on and Y ignores; also return the removed tasks.

    Such a task is always done exactly once and reveals nothing useful, so its timing cannot matter:
    V(full root) = V(reduced root) - sum of removed costs. Koffer loses tasks 3 and C this way, which
    takes the reachable states from 640,224 to 106,704.
    """
    info = data["information_structure"]
    variant = info["default"] if y_variant is None else y_variant
    used = set(compile(info["variants"][variant], "<Y>", "eval").co_names)
    if "P" in used:
        used.add(MARKET_ATTRIBUTE)
    tasks = data["plan_items"] + data["attributes"]
    needed = {pre for item in tasks for pre in item["preceding"]} | used
    free = [item for item in tasks if item["required"] and item["id"] not in needed]
    free_ids = {item["id"] for item in free}
    reduced = data | {
        "plan_items": [item for item in data["plan_items"] if item["id"] not in free_ids],
        "attributes": [item for item in data["attributes"] if item["id"] not in free_ids],
    }
    return reduced, free


class DIPModel:
    """Minimal generic MDP for the toy example and the Koffer model."""

    def __init__(self, data: dict[str, Any], y_variant: str | None = None, y_method: str = "enumerate"):
        self.data = data
        self.y_method = y_method
        self.plan_items = tuple(data["plan_items"])
        self.attributes = tuple(data["attributes"])
        self.decisions = tuple(data["decisions"])
        if not self.decisions:
            raise ValueError("model has no decisions")

        tasks = self.plan_items + self.attributes
        self._tasks = {item["id"]: item for item in tasks}
        self._task_index = {item["id"]: idx for idx, item in enumerate(tasks)}
        self._plan_index = {item["id"]: idx for idx, item in enumerate(self.plan_items)}
        self.attribute_index = {attr["id"]: idx for idx, attr in enumerate(self.attributes)}
        self._decision_index = {decision: idx for idx, decision in enumerate(self.decisions)}
        self._attribute_values = {attr["id"]: tuple(attr["values"]) for attr in self.attributes}
        self.attribute_probs = {attr["id"]: attribute_probs(attr) for attr in self.attributes}
        self.attribute_means = {
            attr["id"]: sum(p * float(v) for p, v in zip(self.attribute_probs[attr["id"]], attr["values"]))
            for attr in self.attributes
        }
        self._required_tasks = tuple(item["id"] for item in tasks if item["required"])

        info = data["information_structure"]
        self.y_variant = info["default"] if y_variant is None else y_variant
        if self.y_variant not in info["variants"]:
            raise ValueError(f"unknown Y variant {self.y_variant!r}; allowed: {sorted(info['variants'])}")
        self.y_expression = info["variants"][self.y_variant]
        self.y_code = compile(self.y_expression, f"<Y:{self.y_variant}>", "eval")
        self.market_price_sigma: float | None = info.get("market_price_sigma")

        self.root_state: State = (tuple(0 for _ in self.plan_items), tuple(0 for _ in self.attributes))

    def state_space_size(self) -> int:
        return 2 ** len(self.plan_items) * prod(len(attr["values"]) + 1 for attr in self.attributes)

    def is_done(self, state: State, task_id: str) -> bool:
        if task_id in self._plan_index:
            return state[0][self._plan_index[task_id]] == 1
        return state[1][self.attribute_index[task_id]] != 0

    def task(self, task_id: str) -> dict[str, Any]:
        return self._tasks[task_id]

    def is_required(self, task_id: str) -> bool:
        return bool(self._tasks[task_id]["required"])

    def _task_cost(self, task_id: str) -> float:
        return float(self._tasks[task_id]["cost"])

    def do(self, state: State, action: Action, true_values: dict[str, Any]) -> State:
        """The state after a task when the attribute values are known in advance (simulation)."""
        _, task_id = action
        if task_id in self.attribute_index:
            return self.observe(state, task_id, true_values[task_id])
        return self.transitions(state, action)[0][1]

    def tie_break_key(self, action: Action) -> tuple[int, float, int]:
        """Assumption A9: final decisions first, then lower cost, then YAML order."""
        kind, value = action
        if kind == "decide":
            return (0, 0.0, self._decision_index[value])
        return (1, self._task_cost(value), self._task_index[value])

    def allowed_actions(self, state: State) -> list[Action]:
        actions: list[Action] = [
            ("do", task_id)
            for task_id, item in self._tasks.items()
            if not self.is_done(state, task_id)
            and all(self.is_done(state, pre) for pre in item["preceding"])
        ]
        if all(self.is_done(state, task_id) for task_id in self._required_tasks):
            actions.extend(("decide", decision) for decision in self.decisions)
        return actions

    def reward(self, state: State, action: Action) -> float:
        kind, value = action
        if kind == "do":
            return -self._task_cost(value)
        if kind == "decide":
            return expected_y(self, state, value, self.y_method)
        raise ValueError(f"unsupported action: {action!r}")

    def transitions(self, state: State, action: Action) -> list[tuple[float, State]]:
        kind, value = action
        if kind == "decide":
            return []
        if kind != "do":
            raise ValueError(f"unsupported action: {action!r}")
        if self.is_done(state, value):
            raise ValueError(f"task {value!r} is already done")

        plan_bits, info = state
        if value in self._plan_index:
            idx = self._plan_index[value]
            return [(1.0, (plan_bits[:idx] + (1,) + plan_bits[idx + 1 :], info))]

        idx = self.attribute_index[value]
        return [
            (float(prob), (plan_bits, info[:idx] + (k,) + info[idx + 1 :]))
            for k, prob in enumerate(self.attribute_probs[value], start=1)
        ]

    def observe(self, state: State, attr_id: str, value: Any) -> State:
        """Set attribute attr_id to the domain value `value` (a value, not an index)."""
        values = self._attribute_values[attr_id]
        if value not in values:
            raise ValueError(f"{value!r} is not in the domain of {attr_id!r}: {values!r}")
        idx = self.attribute_index[attr_id]
        return (state[0], state[1][:idx] + (values.index(value) + 1,) + state[1][idx + 1 :])
