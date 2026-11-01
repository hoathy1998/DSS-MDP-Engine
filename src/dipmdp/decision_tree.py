"""Human decision tree of Fig. 8, interpreted from data/decision_tree.yaml. (Phase 2)

'check' nodes perform the acquiring task (cost counted once), 'do' nodes perform listed items
(skip already-done items), 'decide' ends the run. tree_policy turns the tree into a function of the
state, so a tree that breaks a precedence or required constraint raises instead of being scored.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from dipmdp.evaluate import PolicyStatistics, Run, policy_statistics, simulate_policy
from dipmdp.model import Action, DIPModel, State

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


def tree_policy(tree: dict[str, Any], model: DIPModel) -> Callable[[State], Action]:
    """The tree as a function of the state: walk from the root along what is already known."""
    attribute_values = {attr["id"]: attr["values"] for attr in model.attributes}

    def checked(state: State, action: Action) -> Action:
        if action not in model.allowed_actions(state):
            raise ValueError(f"tree takes {action!r}, which is not allowed in state {state!r}")
        return action

    def act(state: State) -> Action:
        node = tree["nodes"][tree["root"]]
        while True:
            if node["type"] == "decide":
                return checked(state, ("decide", node["decision"]))
            if node["type"] == "check":
                attr_id = node["attribute"]
                k = state[1][model.attribute_index[attr_id]]
                if not k:
                    return checked(state, ("do", attr_id))
                node = tree["nodes"][node["branches"][attribute_values[attr_id][k - 1]]]
            else:
                for task_id in node["items"]:
                    if not model.is_done(state, task_id):
                        return checked(state, ("do", task_id))
                node = tree["nodes"][node["next"]]

    return act


def run_tree(tree: dict[str, Any], model: DIPModel, true_values: dict[str, Any]) -> Run:
    """One case with known attribute values; revenue is Y at the true values (assumption A6)."""
    return simulate_policy(model, tree_policy(tree, model), true_values)


def tree_statistics(tree: dict[str, Any], model: DIPModel) -> PolicyStatistics:
    """Exact statistics of the tree over all outcomes of the tasks it performs."""
    return policy_statistics(model, tree_policy(tree, model))
