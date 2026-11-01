"""Success criterion S2: the plug-in E[Y(s, f)] equals enumeration of every unknown attribute."""
import random

import pytest

from dipmdp.data import load_koffer
from dipmdp.information_structure import accept_probability, expected_y, realised_y
from dipmdp.model import DIPModel, without_free_tasks
from dipmdp.solver import solve_recursive

VARIANTS = sorted(load_koffer()["information_structure"]["variants"])


def random_states(model, count, seed=0):
    """States with a random subset of attributes known; plan bits do not affect Y."""
    rng = random.Random(seed)
    states = [model.root_state]
    for _ in range(count):
        info = tuple(
            rng.randint(1, len(attr["values"])) if rng.random() < 0.6 else 0 for attr in model.attributes
        )
        states.append((model.root_state[0], info))
    return states


@pytest.mark.parametrize("variant", VARIANTS)
def test_plugin_equals_enumeration(variant):
    model = DIPModel(load_koffer(), y_variant=variant)
    for state in random_states(model, 15):
        for decision in model.decisions:
            assert expected_y(model, state, decision, "plugin") == pytest.approx(
                expected_y(model, state, decision, "enumerate"), abs=1e-6
            )


def test_no_bid_is_worth_zero():
    model = DIPModel(load_koffer(), y_variant="margin_all")
    assert expected_y(model, model.root_state, "No bid") == 0.0
    assert realised_y(model, {}, "No bid") == 0.0


def test_accept_probability():
    assert accept_probability(2000, 2000, 200) == pytest.approx(0.5)
    assert accept_probability(2100, 2000, 200) == pytest.approx(0.6914624612740131)
    assert accept_probability(1900, 2000, 200) == pytest.approx(1 - 0.6914624612740131)


def test_realised_y_matches_printed_formula_by_hand():
    # Formula of Section 7.2 with E=1, B=100, H=4, D=2100, f=2000, A=1500, G=1, F=100, I=100:
    # 400 * P(2100 >= 2000) * (2000 - 1200 - 100 - 100) = 400 * 0.69146 * 600.
    model = DIPModel(load_koffer(), y_variant="margin_all")
    true_values = dict(A=1500, B=100, C=1, D=2100, E=1, F=100, G=1, H=4, I=100)
    assert realised_y(model, true_values, 2000) == pytest.approx(400 * 0.6914624612740131 * 600)


def test_removing_free_tasks_keeps_the_value():
    # A small Koffer so the full model stays cheap. Without B, H and I nothing needs beta or task 4,
    # so they become free as well as task 3 and C.
    data = load_koffer()
    keep = {"A", "C", "E", "D"}
    data["attributes"] = [attr for attr in data["attributes"] if attr["id"] in keep]
    data["information_structure"]["variants"] = {"small": "E*P*(f - A)"}
    data["information_structure"]["default"] = "small"
    full = solve_recursive(DIPModel(data, y_method="plugin"))
    reduced_data, free = without_free_tasks(data)
    assert {task["id"] for task in free} == {"beta", "3", "4", "C"}
    reduced = solve_recursive(DIPModel(reduced_data, y_method="plugin"))
    assert full.root_value == pytest.approx(reduced.root_value - sum(task["cost"] for task in free))
