"""Checks on DIPModel and solve_recursive that tests/test_toy.py does not reach."""
from copy import deepcopy

import pytest

from dipmdp.data import load_koffer, load_toy
from dipmdp.model import DIPModel
from dipmdp.solver import solve_recursive


def attribute(attr_id, cost, values, preceding=(), required=False):
    return {
        "id": attr_id,
        "cost": cost,
        "values": list(values),
        "preceding": list(preceding),
        "required": required,
        "distribution": {"type": "uniform"},
    }


def small_model(attributes, y, plan_items=(), decisions=(0, 1)):
    return DIPModel(
        {
            "plan_items": list(plan_items),
            "attributes": attributes,
            "decisions": list(decisions),
            "information_structure": {"default": "y", "variants": {"y": y}},
        }
    )


def test_expected_y_holds_for_non_multilinear_y():
    # E[X^2] = 2 with X in {0, 2}, whereas substituting the mean gives 1.
    model = small_model([attribute("X", 5, [0, 2])], "X * X * f")
    assert model.reward(model.root_state, ("decide", 1)) == pytest.approx(2.0)


def test_expected_y_uses_known_values():
    model = DIPModel(load_toy())
    state = model.observe(model.root_state, "X2", 4)
    assert model.reward(state, ("decide", 1)) == pytest.approx(2.5)


def test_unknown_y_variant_is_rejected():
    with pytest.raises(ValueError):
        DIPModel(load_toy(), y_variant="typo")


def test_model_without_decisions_is_rejected():
    data = deepcopy(load_toy())
    data["decisions"] = []
    with pytest.raises(ValueError):
        DIPModel(data)


@pytest.mark.parametrize("attr_id, value", [("X1", 1), ("X2", 0), ("X2", 2)])
def test_observe_rejects_values_outside_the_domain(attr_id, value):
    model = DIPModel(load_toy())
    with pytest.raises(ValueError):
        model.observe(model.root_state, attr_id, value)


def test_observe_encodes_value_as_one_based_index():
    model = DIPModel(load_toy())
    assert model.observe(model.root_state, "X1", 0) == ((), (1, 0))
    assert model.observe(model.root_state, "X1", 3) == ((), (2, 0))


def test_tie_prefers_decision_over_task():
    # Q(do X) = 0.5 * 1 - 0.5 = 0, equal to deciding either way.
    model = small_model([attribute("X", 0.5, [-1, 1])], "X * f")
    solution = solve_recursive(model)
    assert set(solution.action_values(solution.root_state).values()) == {0.0}
    assert solution.root_action == ("decide", 0)


def test_tie_prefers_lower_cost_over_yaml_order():
    # Q(do X) = Q(do Z) = 1, and X comes first in YAML but costs more.
    model = small_model([attribute("X", 1, [-4, 4]), attribute("Z", 0, [-2, 2])], "(X + Z) * f")
    solution = solve_recursive(model)
    q = solution.action_values(solution.root_state)
    assert q[("do", "X")] == pytest.approx(q[("do", "Z")]) == pytest.approx(1.0)
    assert solution.root_action == ("do", "Z")


def test_gap_below_tolerance_counts_as_tie():
    # Q(do X) = 0.5 - cost is 1e-12 above deciding, which stands in for rounding noise.
    model = small_model([attribute("X", 0.5 - 1e-12, [-1, 1])], "X * f")
    solution = solve_recursive(model)
    assert solution.action_values(solution.root_state)[("do", "X")] > 0.0
    assert solution.root_action == ("decide", 0)


def test_blocked_model_raises_instead_of_returning_a_value():
    # R is required but needs itself, so no state can ever reach a decision.
    model = small_model([attribute("R", 1, [0, 1], preceding=["R"], required=True)], "f")
    with pytest.raises(ValueError):
        solve_recursive(model)


def test_transitions_of_a_task_sum_to_one():
    model = DIPModel(load_koffer())
    outcomes = model.transitions(model.root_state, ("do", "B"))
    assert [state[1][1] for _, state in outcomes] == [1, 2, 3, 4]
    assert sum(prob for prob, _ in outcomes) == pytest.approx(1.0)


def test_koffer_state_space():
    model = DIPModel(load_koffer())
    assert model.state_space_size() == load_koffer()["expected_state_space"]


def test_koffer_precedence_and_required_rules():
    model = DIPModel(load_koffer())
    assert {value for _, value in model.allowed_actions(model.root_state)} == {
        "alpha", "beta", "2", "3", "4", "C", "E",
    }

    # F needs both alpha and A, so alpha alone unlocks A but not F.
    state = model.transitions(model.root_state, ("do", "alpha"))[0][1]
    allowed = model.allowed_actions(state)
    assert ("do", "A") in allowed and ("do", "F") not in allowed
    assert ("do", "alpha") not in allowed

    # Deciding opens only once every required item is done: beta, 3, 4, C, E.
    state = model.root_state
    for task in ("beta", "3", "4", "C"):
        state = model.transitions(state, ("do", task))[0][1]
        assert not any(kind == "decide" for kind, _ in model.allowed_actions(state))
    state = model.transitions(state, ("do", "E"))[0][1]
    assert {value for kind, value in model.allowed_actions(state) if kind == "decide"} == set(model.decisions)
