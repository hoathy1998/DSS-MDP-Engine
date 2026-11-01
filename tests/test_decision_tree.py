"""Success criterion S4: the transcribed tree against Fig. 7, Table 5 and the 9 instances of Table 6.

Table 6 cannot be matched by any reading (see docs/assumptions.md, A3 and A5), so the instance test
pins exactly which rows match rather than demanding all nine.
"""
import pytest

from dipmdp.data import load_decision_tree, load_koffer, load_paper_results
from dipmdp.decision_tree import TREE_READINGS, apply_reading, run_tree, tree_statistics
from dipmdp.model import DIPModel


@pytest.fixture(scope="module")
def model():
    return DIPModel(load_koffer(), y_variant="margin_all", y_method="plugin")


@pytest.fixture(scope="module")
def stats(model):
    return tree_statistics(load_decision_tree(), model)


def instance_values(row):
    return dict(zip("ABCDEFGHI", row["final_state"]))


def test_probabilities_add_up(stats):
    assert sum(stats.decision_probs.values()) == pytest.approx(1.0)


def test_required_tasks_always_done(stats):
    for task in ("beta", "3", "4", "C", "E"):
        assert stats.task_usage[task] == pytest.approx(1.0)


@pytest.mark.parametrize(
    "task, figure_7b",
    [("alpha", 0.32), ("A", 0.32), ("B", 0.60), ("H", 0.60), ("F", 0.16), ("G", 0.11), ("2", 0.26), ("D", 0.26), ("I", 0.13)],
)
def test_task_usage_matches_fig_7b(stats, task, figure_7b):
    # Bar heights read off the figure, hence the tolerance.
    assert stats.task_usage[task] == pytest.approx(figure_7b, abs=0.01)


@pytest.mark.parametrize(
    "decision, figure_7a", [("No bid", 0.73), (1800, 0.13), (2000, 0.065), (2200, 0.065)]
)
def test_decision_shares_match_fig_7a(stats, decision, figure_7a):
    assert stats.decision_probs[decision] == pytest.approx(figure_7a, abs=0.01)


def test_average_retrieval_cost_matches_table_5(stats):
    assert stats.avg_retrieval_cost == pytest.approx(
        load_paper_results()["table5"]["decision_tree"]["avg_retrieval_cost"], abs=0.1
    )


@pytest.mark.parametrize("reading", sorted(TREE_READINGS))
def test_every_reading_respects_the_constraints(model, reading):
    # tree_statistics raises if a reading performs a task or decides before it is allowed.
    tree_statistics(apply_reading(load_decision_tree(), reading), model)


def test_run_tree_agrees_with_statistics(model, stats):
    row = load_paper_results()["table6"][7]
    run = run_tree(load_decision_tree(), model, instance_values(row))
    assert run.decision in stats.decision_probs
    assert run.final_state in stats.final_states


def test_table_6_rows_that_match_the_fig_8_tree(model):
    tree = load_decision_tree()
    rows = load_paper_results()["table6"]
    matching = {
        row["instance"]
        for row in rows
        if abs(run_tree(tree, model, instance_values(row)).profit - row["profit_tree"]) <= 1
    }
    assert matching == {5, 6, 9}
