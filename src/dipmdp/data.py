"""Load the YAML files in data/ and derive attribute marginals."""
from __future__ import annotations

from math import comb
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from dipmdp.model import DIPModel

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_koffer() -> dict[str, Any]:
    return load_yaml(DATA_DIR / "koffer.yaml")


def load_toy() -> dict[str, Any]:
    return load_yaml(DATA_DIR / "toy.yaml")


def load_decision_tree() -> dict[str, Any]:
    return load_yaml(DATA_DIR / "decision_tree.yaml")


def load_paper_results() -> dict[str, Any]:
    return load_yaml(DATA_DIR / "paper_results.yaml")


def attribute_probs(attr: dict[str, Any]) -> list[float]:
    """Marginal probability of each value in attr["values"], in YAML order (assumptions A1, A2)."""
    dist, n = attr["distribution"], len(attr["values"])
    kind = dist["type"]
    if kind == "uniform":
        return [1 / n] * n
    if kind == "categorical":
        if len(dist["probs"]) != n:
            raise ValueError(f"{attr['id']}: {len(dist['probs'])} probs for {n} values")
        return list(dist["probs"])
    if kind == "bernoulli":
        if n != 2:
            raise ValueError(f"{attr['id']}: bernoulli needs 2 values, got {n}")
        return [1 - dist["p"], dist["p"]]
    if kind == "binomial":
        p, k = dist["p"], n - 1
        return [comb(k, i) * p**i * (1 - p) ** (k - i) for i in range(n)]
    raise ValueError(f"{attr['id']}: unknown distribution type {kind!r}")


def load_model(path: str | Path, y_variant: str | None = None, y_method: str = "enumerate") -> DIPModel:
    from dipmdp.model import DIPModel  # model.py imports this module

    return DIPModel(load_yaml(path), y_variant=y_variant, y_method=y_method)
