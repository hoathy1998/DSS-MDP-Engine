"""The web demo reimplements the solver in JavaScript, so it must agree with the Python solver."""
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from dipmdp.data import load_decision_tree, load_koffer, load_paper_results
from dipmdp.decision_tree import run_tree
from dipmdp.evaluate import simulate_policy
from dipmdp.model import DIPModel
from dipmdp.solver import UNREACHABLE, solve_array

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="Node.js is not installed")


@pytest.fixture(scope="module")
def node_output(tmp_path_factory):
    out = tmp_path_factory.mktemp("web_demo")
    subprocess.run(
        [NODE, str(ROOT / "tests" / "web_demo_check.js"), str(WEB), str(out)],
        check=True,
        timeout=300,
    )
    return out


@pytest.fixture(scope="module")
def result(node_output):
    return json.loads((node_output / "result.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("variant", ["margin_all", "margin_repair"])
def test_every_reachable_state_matches_python(node_output, variant):
    exported = json.loads((node_output / f"{variant}.json").read_text(encoding="utf-8"))
    solution = solve_array(DIPModel(load_koffer(), y_variant=variant, y_method="plugin"))
    indices = np.array(exported["indices"])
    reachable = np.flatnonzero(solution.policy_codes != UNREACHABLE)
    assert np.array_equal(np.sort(indices), reachable)
    assert len(indices) == 640_224
    assert np.allclose(np.array(exported["values"]), solution.values[indices], atol=1e-6, rtol=0)
    assert np.array_equal(np.array(exported["codes"]), solution.policy_codes[indices])


@pytest.mark.parametrize("variant", ["margin_all", "margin_repair"])
def test_table6_runs_match_python(result, variant):
    model = DIPModel(load_koffer(), y_variant=variant, y_method="plugin")
    solution = solve_array(model)
    tree = load_decision_tree()
    for row, js in zip(load_paper_results()["table6"], result["table6"][variant]):
        truth = dict(zip("ABCDEFGHI", row["final_state"]))
        mdp_run = simulate_policy(model, solution.policy, truth)
        tree_run = run_tree(tree, model, truth)
        assert js["mdp_profit"] == pytest.approx(mdp_run.profit, abs=1e-6)
        assert js["mdp_decision"] == mdp_run.decision
        assert js["tree_profit"] == pytest.approx(tree_run.profit, abs=1e-6)
        assert js["tree_decision"] == tree_run.decision


def test_toy_matches_the_corrected_value(result):
    assert result["toy_root_value"] == pytest.approx(1.0)
    assert result["toy_root_action"]["decision"] == 1


def test_scripted_ui_flow(result):
    ui = result["ui"]
    assert ui.pop("cost_after_alpha") == 20
    failed = [name for name, passed in ui.items() if not passed]
    assert not failed


def test_built_page_is_current_and_self_contained():
    page = (WEB / "koffer_demo.html").read_text(encoding="utf-8")
    assert "<script src" not in page
    assert "/*__" not in page
    for source in ("solver.js", "app.js"):
        body = (WEB / source).read_text(encoding="utf-8").split('\nif (typeof module !== "undefined")')[0]
        assert body in page, f"web/koffer_demo.html is stale; run scripts/build_web_demo.py ({source})"
