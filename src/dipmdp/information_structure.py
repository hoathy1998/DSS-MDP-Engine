"""Information structure Y and E[Y(s, f)]. (Phase 2)

Variants are listed in data/koffer.yaml > information_structure.variants (assumption A3).
P = P(market price >= f) = 1 - Phi((f - D) / sigma) (assumption A4). A decision that is not a number
is "No bid", with Y = 0 (Section 7.2).

Fast expectation (PLAN 7.3): attributes are independent and every variant is multilinear in them,
so E[Y | known] = Y evaluated with each unknown attribute replaced by its mean, except P which is
replaced by E_D[P(D >= f)]. tests/test_information_structure.py compares this with enumeration (S2).
"""
from __future__ import annotations

from itertools import product
from math import erfc, prod, sqrt
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dipmdp.model import DIPModel, State

MARKET_ATTRIBUTE = "D"


def accept_probability(market_mean: float, f: float, sigma: float) -> float:
    """P(market price >= f) for a market price ~ Normal(market_mean, sigma)."""
    return 0.5 * erfc((f - market_mean) / (sigma * sqrt(2)))


def _evaluate(model: DIPModel, scope: dict[str, float]) -> float:
    return float(eval(model.y_code, {"__builtins__": {}}, scope))


def realised_y(model: DIPModel, true_values: dict[str, Any], decision: Any) -> float:
    """Y at the true attribute values (assumption A6). The market price itself stays random."""
    if isinstance(decision, str):
        return 0.0
    f = float(decision)
    scope = {attr_id: float(value) for attr_id, value in true_values.items()} | {"f": f}
    if model.market_price_sigma is not None:
        scope["P"] = accept_probability(scope[MARKET_ATTRIBUTE], f, model.market_price_sigma)
    return _evaluate(model, scope)


def _enumerate_y(model: DIPModel, state: State, f: float) -> float:
    known: dict[str, float] = {"f": f}
    unknown: list[dict[str, Any]] = []
    for attr, k in zip(model.attributes, state[1]):
        if k:
            known[attr["id"]] = float(attr["values"][k - 1])
        else:
            unknown.append(attr)

    outcomes = [list(zip(attr["values"], model.attribute_probs[attr["id"]])) for attr in unknown]
    total = 0.0
    for combo in product(*outcomes):
        scope = known | {attr["id"]: float(value) for attr, (value, _) in zip(unknown, combo)}
        if model.market_price_sigma is not None:
            scope["P"] = accept_probability(scope[MARKET_ATTRIBUTE], f, model.market_price_sigma)
        total += prod(p for _, p in combo) * _evaluate(model, scope)
    return total


def _plugin_y(model: DIPModel, state: State, f: float) -> float:
    scope: dict[str, float] = {"f": f}
    for attr, k in zip(model.attributes, state[1]):
        scope[attr["id"]] = float(attr["values"][k - 1]) if k else model.attribute_means[attr["id"]]
    if model.market_price_sigma is not None:
        attr = next(a for a in model.attributes if a["id"] == MARKET_ATTRIBUTE)
        k = state[1][model.attribute_index[MARKET_ATTRIBUTE]]
        sigma = model.market_price_sigma
        if k:
            scope["P"] = accept_probability(float(attr["values"][k - 1]), f, sigma)
        else:
            scope["P"] = sum(
                p * accept_probability(float(value), f, sigma)
                for value, p in zip(attr["values"], model.attribute_probs[MARKET_ATTRIBUTE])
            )
    return _evaluate(model, scope)


def expected_y(model: DIPModel, state: State, decision: Any, method: str = "enumerate") -> float:
    """E[Y(s, f)]. "enumerate" holds for any Y; "plugin" needs a multilinear Y (PLAN 7.3)."""
    if isinstance(decision, str):
        return 0.0
    if method == "enumerate":
        return _enumerate_y(model, state, float(decision))
    if method == "plugin":
        return _plugin_y(model, state, float(decision))
    raise ValueError(f"unknown method {method!r}")
