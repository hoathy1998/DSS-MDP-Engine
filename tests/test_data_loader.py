"""Checks on dipmdp.data; tests/test_data.py reads the YAML files without using this module."""
import pytest

from dipmdp.data import (
    attribute_probs,
    load_decision_tree,
    load_koffer,
    load_paper_results,
    load_toy,
)


def test_loaders_read_every_data_file():
    assert load_koffer()["name"] == "koffer"
    assert load_toy()["name"] == "toy"
    assert load_decision_tree()["root"] == "checkE"
    assert load_paper_results()["required_cost_total"] == 45


@pytest.mark.parametrize(
    "attr_id, expected",
    [
        ("A", [0.25, 0.25, 0.25, 0.25]),
        ("B", [0.512, 0.384, 0.096, 0.008]),  # A1
        ("C", [0.7, 0.3]),  # A2
        ("D", [0.125, 0.375, 0.375, 0.125]),
        ("F", [0.7, 0.3]),  # A2: P(F = 200) = 0.3
    ],
)
def test_attribute_probs(attr_id, expected):
    attr = next(a for a in load_koffer()["attributes"] if a["id"] == attr_id)
    assert attribute_probs(attr) == pytest.approx(expected)


def test_attribute_probs_rejects_mismatched_input():
    with pytest.raises(ValueError):
        attribute_probs({"id": "X", "values": [1, 2, 3], "distribution": {"type": "bernoulli", "p": 0.5}})
    with pytest.raises(ValueError):
        attribute_probs({"id": "X", "values": [1, 2], "distribution": {"type": "categorical", "probs": [1.0]}})
    with pytest.raises(ValueError):
        attribute_probs({"id": "X", "values": [1, 2], "distribution": {"type": "poisson"}})
