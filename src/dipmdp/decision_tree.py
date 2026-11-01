"""Human decision tree of Fig. 8, interpreted from data/decision_tree.yaml. (Phase 2)

'check' nodes perform the acquiring task (cost counted once), 'do' nodes perform listed items
(skip already-done items), 'decide' ends the run. Actions go through DIPModel, so a tree that breaks
a precedence or required constraint raises instead of being scored.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from dipmdp.evaluate import PolicyStatistics, Run
from dipmdp.information_structure import realised_y
from dipmdp.model import DIPModel, State

# Alternative readings of the two Attribute H nodes (assumption A5): node -> branches for H = 1, 2, 3, 4.
_DECLINE, _CONTINUE = "decline347", "stageAlpha"
_STRICT = [_DECLINE, _DECLINE, _CONTINUE, _CONTINUE]
_LOOSE = [_DECLINE, _CONTINUE, _CONTINUE, _CONTINUE]
_OPEN = [_CONTINUE] * 4
TREE_READINGS: dict[str, dict[str, list[str]]] = {
    "fig8": {},
    "h_swapped": {"checkH_low": _LOOSE, "checkH_high": _STRICT},
    "h_both_strict": {"checkH_low": _STRICT, "checkH_high": _STRICT},
    "h_both_loose": {"checkH_low": _LOOSE, "checkH_high": _LOOSE},
    "h_no_gate": {"checkH_low": _OPEN, "checkH_high": _OPEN},
}


def apply_reading(tree: dict[str, Any], reading: str) -> dict[str, Any]:
    result = deepcopy(tree)
    for node_id, targets in TREE_READINGS[reading].items():
        node = result["nodes"][node_id]
        node["branches"] = dict(zip(node["branches"], targets))
    return result


def _perform(model: DIPModel, state: State, task_id: str) -> tuple[str, str]:
    action = ("do", task_id)
    if action not in model.allowed_actions(state):
        raise ValueError(f"tree performs {task_id!r}, which is not allowed in state {state!r}")
    return action


def _value(model: DIPModel, state: State, attr_id: str) -> Any:
    k = state[1][model.attribute_index[attr_id]]
    return next(a for a in model.attributes if a["id"] == attr_id)["values"][k - 1]


def _is_known(model: DIPModel, state: State, attr_id: str) -> bool:
    return state[1][model.attribute_index[attr_id]] != 0


def run_tree(tree: dict[str, Any], model: DIPModel, true_values: dict[str, Any]) -> Run:
    """One case with known attribute values; revenue is Y at the true values (assumption A6)."""
    state, cost = model.root_state, 0.0
    node = tree["nodes"][tree["root"]]
    while node["type"] != "decide":
        if node["type"] == "check":
            attr_id = node["attribute"]
            if not _is_known(model, state, attr_id):
                cost -= model.reward(state, _perform(model, state, attr_id))
                state = model.do(state, ("do", attr_id), true_values)
            node = tree["nodes"][node["branches"][_value(model, state, attr_id)]]
        else:
            for task_id in node["items"]:
                if not model.is_done(state, task_id):
                    cost -= model.reward(state, _perform(model, state, task_id))
                    state = model.do(state, ("do", task_id), true_values)
            node = tree["nodes"][node["next"]]
    decision = node["decision"]
    if ("decide", decision) not in model.allowed_actions(state):
        raise ValueError(f"tree decides {decision!r} before every required task is done")
    return Run(decision, cost, realised_y(model, true_values, decision), state)


def tree_statistics(tree: dict[str, Any], model: DIPModel) -> PolicyStatistics:
    """Exact statistics of the tree over all outcomes of the tasks it performs."""
    stats = PolicyStatistics()

    def perform_then_return(node_id: str, state: State, task_id: str, prob: float) -> None:
        action = _perform(model, state, task_id)
        stats.add_task(task_id, prob, -model.reward(state, action))
        for p, next_state in model.transitions(state, action):
            walk(node_id, next_state, prob * p)

    def walk(node_id: str, state: State, prob: float) -> None:
        node = tree["nodes"][node_id]
        if node["type"] == "decide":
            if ("decide", node["decision"]) not in model.allowed_actions(state):
                raise ValueError(f"tree decides {node['decision']!r} before every required task is done")
            stats.add_decision(model, state, node["decision"], prob)
        elif node["type"] == "check":
            attr_id = node["attribute"]
            if _is_known(model, state, attr_id):
                walk(node["branches"][_value(model, state, attr_id)], state, prob)
            else:
                perform_then_return(node_id, state, attr_id, prob)
        else:
            pending = [task_id for task_id in node["items"] if not model.is_done(state, task_id)]
            if pending:
                perform_then_return(node_id, state, pending[0], prob)
            else:
                walk(node["next"], state, prob)

    walk(tree["root"], model.root_state, 1.0)
    return stats
