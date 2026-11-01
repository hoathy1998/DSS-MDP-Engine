"""Checks on the Phase 5 extensions."""
import pytest

from dipmdp.data import attribute_probs, load_koffer
from dipmdp.evaluate import evaluate, policy_statistics
from dipmdp.model import DIPModel
from dipmdp.sensitivity import (
    all_targets,
    correlated_scenarios,
    perturb_cost,
    perturb_distribution,
    sensitivity_rows,
    tilted_probs,
    value_of_gathering,
)
from dipmdp.solver import solve_array


def koffer_model(data=None):
    return DIPModel(load_koffer() if data is None else data, y_variant="margin_all", y_method="plugin")


def test_tilt_moves_mass_up_or_down_and_stays_a_distribution():
    probs = [0.25, 0.25, 0.25, 0.25]
    up, down = tilted_probs(probs, 0.2), tilted_probs(probs, -0.2)
    assert sum(up) == pytest.approx(1.0) and sum(down) == pytest.approx(1.0)
    assert up[-1] > probs[-1] > down[-1]
    assert tilted_probs(probs, 0.0) == pytest.approx(probs)


def test_perturbations_do_not_touch_the_input():
    data = load_koffer()
    perturb_cost(data, "D", 0.2)
    perturb_distribution(data, "E", 0.2)
    assert data == load_koffer()


def test_perturb_cost_and_distribution():
    cost_data = perturb_cost(load_koffer(), "D", 0.2)
    assert next(a for a in cost_data["attributes"] if a["id"] == "D")["cost"] == pytest.approx(120.0)
    dist_data = perturb_distribution(load_koffer(), "E", 0.1)
    e = next(a for a in dist_data["attributes"] if a["id"] == "E")
    assert attribute_probs(e)[1] > 0.6


def test_all_targets_cover_costs_and_distributions():
    assert len(all_targets(load_koffer())) == 13 + 9


def test_old_policy_never_beats_resolving():
    targets = [("cost", "G"), ("distribution", "E")]
    rows = sensitivity_rows(load_koffer(), "margin_all", targets)
    assert len(rows) == len(targets) * 4
    assert all(row["regret"] <= 0.011 for row in rows)


def test_stale_policy_loses_under_a_large_shock():
    # D costing 21 times as much makes acquiring it wasteful, and the old policy still acquires it,
    # so the tiny regrets at +-20% are not an artefact of how regret is computed.
    row = sensitivity_rows(load_koffer(), "margin_all", [("cost", "D")], (20.0,))[0]
    assert row["regret"] < -100


def test_zero_strength_recovers_the_independent_value():
    model = koffer_model()
    solution = solve_array(model)
    assert evaluate(model, solution.policy, correlated_scenarios(model, 0.0)).expected_profit == pytest.approx(
        solution.root_value
    )


def test_correlation_keeps_probabilities_and_marginals():
    model = koffer_model()
    weighted = list(correlated_scenarios(model, 0.8))
    assert sum(prob for prob, _ in weighted) == pytest.approx(1.0)
    for attr_id in ("A", "D"):
        attr = next(a for a in model.attributes if a["id"] == attr_id)
        for value, marginal in zip(attr["values"], model.attribute_probs[attr_id]):
            assert sum(p for p, v in weighted if v[attr_id] == value) == pytest.approx(marginal)


def test_value_of_gathering_matches_the_policy():
    model = koffer_model()
    solution = solve_array(model)
    state = model.root_state
    for task in ("beta", "3", "4", "C"):
        state = model.transitions(state, ("do", task))[0][1]
    state = model.observe(state, "E", 1)
    voi = value_of_gathering(solution, state)
    assert voi["value"] == pytest.approx(max(voi["decide_now"], voi["decide_now"] + max(voi["gain_by_task"].values())))
    assert voi["value"] >= voi["decide_now"]
    assert policy_statistics(model, solution.policy).expected_profit == pytest.approx(solution.root_value)
