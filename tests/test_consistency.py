"""Success criterion S3 and the comparison policies of Phase 4."""
import pytest

from dipmdp.data import load_decision_tree, load_koffer
from dipmdp.evaluate import evaluate, policy_statistics, scenarios
from dipmdp.model import DIPModel
from dipmdp.policies import CollectAllPolicy, DecisionTreePolicy, MDPPolicy, MyopicVoIPolicy, RequiredOnlyPolicy
from dipmdp.solver import solve_array


@pytest.fixture(scope="module", params=["margin_all", "margin_repair"])
def setup(request):
    model = DIPModel(load_koffer(), y_variant=request.param, y_method="plugin")
    return model, solve_array(model)


def test_scenarios_cover_all_cases(setup):
    model, _ = setup
    all_scenarios = list(scenarios(model))
    assert len(all_scenarios) == 16_384
    assert sum(prob for prob, _ in all_scenarios) == pytest.approx(1.0)


def test_simulated_profit_equals_root_value(setup):
    model, solution = setup
    assert abs(evaluate(model, MDPPolicy(solution).act).expected_profit - solution.root_value) < 1e-6


def test_walk_and_simulation_agree(setup):
    model, solution = setup
    tree = load_decision_tree()
    for act in (MDPPolicy(solution).act, DecisionTreePolicy(tree, model).act):
        walked, simulated = policy_statistics(model, act), evaluate(model, act)
        assert walked.expected_profit == pytest.approx(simulated.expected_profit, abs=1e-6)
        assert walked.avg_retrieval_cost == pytest.approx(simulated.avg_retrieval_cost, abs=1e-9)
        assert walked.final_states == simulated.final_states


def test_no_policy_beats_the_mdp(setup):
    model, solution = setup
    for policy in (
        DecisionTreePolicy(load_decision_tree(), model),
        RequiredOnlyPolicy(model),
        CollectAllPolicy(model),
        MyopicVoIPolicy(model),
    ):
        assert policy_statistics(model, policy.act).expected_profit <= solution.root_value + 1e-6, policy.name


def test_required_only_pays_exactly_the_required_cost(setup):
    model, _ = setup
    stats = policy_statistics(model, RequiredOnlyPolicy(model).act)
    assert stats.avg_retrieval_cost == pytest.approx(45.0)
    assert set(stats.task_usage) == {"beta", "3", "4", "C", "E"}


def test_collect_all_pays_every_cost(setup):
    model, _ = setup
    stats = policy_statistics(model, CollectAllPolicy(model).act)
    assert stats.avg_retrieval_cost == pytest.approx(254.0)
    assert all(share == pytest.approx(1.0) for share in stats.task_usage.values())
    assert len(stats.task_usage) == 14


def test_myopic_is_valid_and_pays_at_least_the_required_cost(setup):
    model, _ = setup
    stats = policy_statistics(model, MyopicVoIPolicy(model).act)
    assert sum(stats.decision_probs.values()) == pytest.approx(1.0)
    assert stats.avg_retrieval_cost >= 45.0 - 1e-9
