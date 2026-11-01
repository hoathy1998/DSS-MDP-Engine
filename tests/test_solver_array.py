"""solve_array against the reference solve_recursive (PLAN Phase 3)."""
import random

import pytest

from dipmdp.data import load_koffer, load_toy
from dipmdp.information_structure import expected_y
from dipmdp.model import DIPModel, without_free_tasks
from dipmdp.solver import action_of_code, encode_state, solve_array, solve_recursive


def reduced_koffer(y_variant="margin_all"):
    data, _ = without_free_tasks(load_koffer(), y_variant)
    return DIPModel(data, y_variant=y_variant, y_method="plugin")


def assert_same_solution(model):
    reference = solve_recursive(model)
    array = solve_array(model)
    assert array.n_reachable == len(reference._values)
    for state, value in reference._values.items():
        assert array.value(state) == pytest.approx(value, abs=1e-6)
        assert array.policy(state) == reference.policy(state)


def test_toy_matches_recursive():
    assert_same_solution(DIPModel(load_toy(), y_method="plugin"))


@pytest.mark.parametrize("y_variant", ["margin_all", "margin_repair"])
def test_reduced_koffer_matches_recursive(y_variant):
    assert_same_solution(reduced_koffer(y_variant))


def test_reachable_states_of_full_koffer():
    # alpha/A/F/G 38, beta/B/H 26, 2/D 6, 4/I 6, E 3, C 3, task 3 2.
    solution = solve_array(DIPModel(load_koffer(), y_method="plugin"))
    assert solution.n_reachable == 38 * 26 * 6 * 6 * 3 * 3 * 2 == 640_224


def test_full_koffer_value_is_reduced_value_minus_free_costs():
    data = load_koffer()
    reduced_data, free = without_free_tasks(data, "margin_all")
    full = solve_array(DIPModel(data, y_method="plugin"))
    reduced = solve_array(DIPModel(reduced_data, y_method="plugin"))
    assert full.root_value == pytest.approx(reduced.root_value - sum(task["cost"] for task in free))


def test_decision_table_matches_plugin_and_enumeration():
    model = DIPModel(load_koffer(), y_method="plugin")
    solution = solve_array(model)
    rng = random.Random(1)
    plan = tuple(1 for _ in model.plan_items)
    for _ in range(25):
        known = {
            attr["id"]: rng.randint(1, len(attr["values"])) if attr["required"] or rng.random() < 0.5 else 0
            for attr in model.attributes
        }
        # F and G need A; with every plan bit set, the state is then reachable.
        if known["F"] or known["G"]:
            known["A"] = known["A"] or 1
        state = (plan, tuple(known[attr["id"]] for attr in model.attributes))
        q = solution.action_values(state)
        for decision in model.decisions:
            assert q[("decide", decision)] == pytest.approx(expected_y(model, state, decision, "enumerate"), abs=1e-6)
        assert solution.value(state) == pytest.approx(max(q.values()), abs=1e-6)


def test_encoding_is_mixed_radix_with_root_at_zero():
    model = DIPModel(load_koffer(), y_method="plugin")
    assert encode_state(model, model.root_state) == 0
    last = ((1,) * len(model.plan_items), tuple(len(a["values"]) for a in model.attributes))
    assert encode_state(model, last) == model.state_space_size() - 1


def test_action_codes_cover_tasks_and_decisions():
    model = DIPModel(load_toy())
    assert action_of_code(model, 0) == ("do", "X1")
    assert action_of_code(model, 2) == ("decide", 0)
    with pytest.raises(ValueError):
        action_of_code(model, -1)
