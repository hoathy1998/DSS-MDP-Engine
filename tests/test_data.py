"""Sanity checks on the data transcribed from the paper. Runs before any model code exists."""
from math import comb, prod
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[1] / "data"


def load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def probs(attr):
    d, n = attr["distribution"], len(attr["values"])
    t = d["type"]
    if t == "uniform":
        return [1 / n] * n
    if t == "categorical":
        return d["probs"]
    if t == "bernoulli":
        assert n == 2
        return [1 - d["p"], d["p"]]
    if t == "binomial":  # assumption A1: Binomial(n-1, p) over value index
        k = n - 1
        return [comb(k, i) * d["p"] ** i * (1 - d["p"]) ** (k - i) for i in range(n)]
    raise ValueError(t)


def test_distributions_sum_to_one():
    for file in ("koffer.yaml", "toy.yaml"):
        for a in load(file)["attributes"]:
            p = probs(a)
            assert len(p) == len(a["values"]), a["id"]
            assert abs(sum(p) - 1) < 1e-9, a["id"]


def test_precedence_references_exist():
    m = load("koffer.yaml")
    ids = {p["id"] for p in m["plan_items"]} | {a["id"] for a in m["attributes"]}
    for item in m["plan_items"] + m["attributes"]:
        for pre in item["preceding"]:
            assert pre in ids, (item["id"], pre)


def test_required_cost_matches_table6_losses():
    m = load("koffer.yaml")
    req = sum(i["cost"] for i in m["plan_items"] + m["attributes"] if i["required"])
    assert req == load("paper_results.yaml")["required_cost_total"] == 45


def test_state_space_matches_paper():
    m = load("koffer.yaml")
    size = prod(len(a["values"]) + 1 for a in m["attributes"]) * 2 ** len(m["plan_items"])
    assert size == m["expected_state_space"] == 8_100_000


def test_decision_tree_is_well_formed():
    tree = load("decision_tree.yaml")
    m = load("koffer.yaml")
    domains = {a["id"]: set(a["values"]) for a in m["attributes"]}
    nodes = tree["nodes"]
    assert tree["root"] in nodes
    for nid, node in nodes.items():
        if node["type"] == "check":
            assert set(node["branches"]) == domains[node["attribute"]], nid
            assert all(n in nodes for n in node["branches"].values()), nid
        elif node["type"] == "do":
            assert node["next"] in nodes, nid
        else:
            assert node["type"] == "decide", nid
