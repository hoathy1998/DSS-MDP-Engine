"""Design-time phase of Fig. 1: CMMN model -> MDP structure -> information structure -> filter -> solve.

The output is a deployment package: the integrated CMMN model, the model the recommender needs, the solved
policy, and a manifest with hashes. Deployment reads only this package, so the two phases stay separate.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from dipmdp.model import DIPModel
from dipmdp.solver import ArraySolution, load_solution, save_solution, solve_array
from dipmdp.system.cmmn import integrate_plan_fragment, retrieve_structure

PACKAGE_FILES = ("integrated.cmmn", "model.json", "policy.npz")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def filter_model(cmmn_xml: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Steps 5.2 and 5.4: take precedence and required flags from CMMN, costs and distributions from parameters.

    The two sources must describe the same tasks; a mismatch means the model and parameters have diverged.
    Attribute order stays that of the parameter file, because the state encoding depends on it.
    """
    structure = retrieve_structure(cmmn_xml)
    expected = {item["id"] for item in parameters["plan_items"] + parameters["attributes"]}
    if set(structure) != expected:
        raise ValueError(
            f"CMMN and parameters disagree: only in CMMN {sorted(set(structure) - expected)}, "
            f"only in parameters {sorted(expected - set(structure))}"
        )
    model = json.loads(json.dumps(parameters))
    for item in model["plan_items"] + model["attributes"]:
        found = structure[item["id"]]
        item["preceding"] = found["preceding"]
        item["required"] = found["required"]
    for attr in model["attributes"]:
        if structure[attr["id"]]["acquires"] != attr["id"]:
            raise ValueError(f"CMMN task {attr['id']!r} does not acquire its case file item")
    return model


def compile_package(cmmn_path: Path, parameters: dict[str, Any], out_dir: Path, y_variant: str) -> dict[str, Any]:
    """Run the whole design-time phase and write the package. Returns the manifest."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cmmn_xml = cmmn_path.read_text(encoding="utf-8")
    model_data = filter_model(cmmn_xml, parameters)
    model = DIPModel(model_data, y_variant=y_variant, y_method="plugin")

    started = time.perf_counter()
    solution = solve_array(model)
    seconds = time.perf_counter() - started

    (out_dir / "integrated.cmmn").write_text(integrate_plan_fragment(cmmn_xml), encoding="utf-8", newline="\n")
    (out_dir / "model.json").write_text(
        json.dumps(model_data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    save_solution(solution, out_dir / "policy.npz", {"y_variant": y_variant, "y_expression": model.y_expression})
    manifest = {
        "case": model_data["name"],
        "y_variant": y_variant,
        "y_expression": model.y_expression,
        "n_states": model.state_space_size(),
        "n_reachable": solution.n_reachable,
        "root_value": solution.root_value,
        "solve_seconds": round(seconds, 3),
        "source_cmmn_sha256": _sha256(cmmn_path),
        "files": {name: _sha256(out_dir / name) for name in PACKAGE_FILES},
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def load_package(package_dir: Path) -> tuple[DIPModel, ArraySolution, str, dict[str, Any]]:
    """Open a package for deployment, refusing it if any file differs from the manifest."""
    manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        if _sha256(package_dir / name) != digest:
            raise ValueError(f"{name} does not match the manifest; run the design-time phase again")
    data = json.loads((package_dir / "model.json").read_text(encoding="utf-8"))
    model = DIPModel(data, y_variant=manifest["y_variant"], y_method="plugin")
    solution, _ = load_solution(package_dir / "policy.npz", model)
    return model, solution, (package_dir / "integrated.cmmn").read_text(encoding="utf-8"), manifest
