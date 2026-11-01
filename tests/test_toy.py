"""Success criterion S1: the generic solver reproduces the (corrected) toy example of Section 5.3.

Paper claims V(no info) = 0.5 and that acquiring X2 pays off. Correct values (assumption A8):
  V(root) = 1.0, optimal action = decide f=1 now,
  value of 'acquire X2' (net of its cost) = 0.75, same for X1.
"""
from pathlib import Path

import pytest

from dipmdp.data import load_model
from dipmdp.solver import solve_recursive

TOY = Path(__file__).resolve().parents[1] / "data" / "toy.yaml"


@pytest.fixture(scope="module")
def solution():
    return solve_recursive(load_model(TOY))


def test_root_value(solution):
    assert solution.root_value == pytest.approx(1.0)


def test_root_action_is_decide_accept(solution):
    assert solution.root_action == ("decide", 1)


def test_action_values_at_root(solution):
    q = solution.action_values(solution.root_state)
    assert q[("decide", 1)] == pytest.approx(1.0)
    assert q[("decide", 0)] == pytest.approx(0.0)
    assert q[("do", "X1")] == pytest.approx(0.75)
    assert q[("do", "X2")] == pytest.approx(0.75)


def test_after_observing_x2_high(solution):
    # X2 = 4 (value index 2): accept, E[Y] = 0.5*(4-0) + 0.5*(4-3) = 2.5
    s = solution.model.observe(solution.root_state, "X2", 4)
    assert solution.value(s) == pytest.approx(2.5)
    assert solution.policy(s) == ("decide", 1)
