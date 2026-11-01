"""Policies to compare. (Phase 4)

Common interface: policy.act(state) -> action, given the current state only.
"""
from __future__ import annotations

from typing import Any, Protocol

from dipmdp.decision_tree import tree_policy
from dipmdp.model import Action, DIPModel, State
from dipmdp.solver import TIE_TOLERANCE


class Policy(Protocol):
    name: str

    def act(self, state: State) -> Action: ...


def best_decision(model: DIPModel, state: State) -> tuple[Action, float]:
    """The final decision with the highest E[Y(s, f)], ties by assumption A9."""
    q = {("decide", decision): model.reward(state, ("decide", decision)) for decision in model.decisions}
    best = max(q.values())
    action = min((a for a, value in q.items() if best - value <= TIE_TOLERANCE), key=model.tie_break_key)
    return action, best


def _next_required(model: DIPModel, state: State) -> Action | None:
    actions = [
        action
        for action in model.allowed_actions(state)
        if action[0] == "do" and model.is_required(action[1])
    ]
    return min(actions, key=model.tie_break_key) if actions else None


class MDPPolicy:
    name = "mdp"

    def __init__(self, solution: Any):
        self.act = solution.policy


class DecisionTreePolicy:
    name = "decision_tree"

    def __init__(self, tree: dict[str, Any], model: DIPModel):
        self.act = tree_policy(tree, model)


class RequiredOnlyPolicy:
    """Do the required items only, then take the best decision on E[Y]."""

    name = "required_only"

    def __init__(self, model: DIPModel):
        self.model = model

    def act(self, state: State) -> Action:
        return _next_required(self.model, state) or best_decision(self.model, state)[0]


class CollectAllPolicy:
    """Do every plan item and acquire every attribute, then take the best decision."""

    name = "collect_all"

    def __init__(self, model: DIPModel):
        self.model = model

    def act(self, state: State) -> Action:
        tasks = [action for action in self.model.allowed_actions(state) if action[0] == "do"]
        return min(tasks, key=self.model.tie_break_key) if tasks else best_decision(self.model, state)[0]


class MyopicVoIPolicy:
    """One-step lookahead (assumption A12).

    Required items come first, since they must be paid anyway. Then the gain of an unknown attribute is
    E[max_f E[Y]] after observing it, minus max_f E[Y] now, minus its cost and that of its unfinished
    predecessors. While some gain is positive, work towards the best attribute; otherwise decide.
    """

    name = "myopic_voi"

    def __init__(self, model: DIPModel):
        self.model = model
        self._cache: dict[State, Action] = {}

    def _chain(self, state: State, task_id: str) -> list[str]:
        """Unfinished predecessors of task_id, predecessors first, ending with task_id itself."""
        chain: list[str] = []

        def visit(current: str) -> None:
            for pre in self.model.task(current)["preceding"]:
                if not self.model.is_done(state, pre) and pre not in chain:
                    visit(pre)
            chain.append(current)

        visit(task_id)
        return chain

    def _gain(self, state: State, attr_id: str, base: float, chain: list[str]) -> float:
        outcomes = self.model.transitions(state, ("do", attr_id))
        informed = sum(p * best_decision(self.model, next_state)[1] for p, next_state in outcomes)
        return informed - base - sum(float(self.model.task(task_id)["cost"]) for task_id in chain)

    def _choose(self, state: State) -> Action:
        required = _next_required(self.model, state)
        if required is not None:
            return required
        decision, base = best_decision(self.model, state)
        best_gain, best_task = TIE_TOLERANCE, None
        for attr in self.model.attributes:
            if self.model.is_done(state, attr["id"]):
                continue
            chain = self._chain(state, attr["id"])
            gain = self._gain(state, attr["id"], base, chain)
            if gain > best_gain:
                best_gain, best_task = gain, chain[0]
        return ("do", best_task) if best_task is not None else decision

    def act(self, state: State) -> Action:
        if state not in self._cache:
            self._cache[state] = self._choose(state)
        return self._cache[state]
