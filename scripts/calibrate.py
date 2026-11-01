"""Phase 2: calibrate ambiguous choices (A1, A2, A3, A5) against Table 5, Fig. 7 and Table 6.

For every combination of Y variant x B-distribution reading x Bernoulli reading x tree reading x
column order of Table 6: solve the MDP, evaluate the tree, and compare both with the paper.
Write results/calibration.csv and print a ranked summary. Do NOT pick a configuration automatically.
"""
from __future__ import annotations

import csv
import itertools
import time
from copy import deepcopy
from math import prod
from pathlib import Path
from typing import Any

from dipmdp.data import attribute_probs, load_decision_tree, load_koffer, load_paper_results
from dipmdp.decision_tree import TREE_READINGS, apply_reading, run_tree, tree_statistics
from dipmdp.evaluate import PolicyStatistics, policy_statistics, simulate_policy
from dipmdp.model import DIPModel, without_free_tasks
from dipmdp.paper_figures import FIG7_DECISIONS, FIG7_TASKS
from dipmdp.solver import solve_recursive

OUTPUT = Path(__file__).resolve().parents[1] / "results" / "calibration.csv"

B_READINGS = ("binomial", "uniform", "binomial_reversed")  # assumption A1
BERNOULLI_READINGS = ("p_on_second", "p_on_first")  # assumption A2
BINARY_ATTRIBUTES = ("C", "E", "G")  # the columns of Table 6 that share the domain {0, 1} (A5)
COLUMN_ORDERS = tuple(itertools.permutations(BINARY_ATTRIBUTES))
TABLE6_MATCH_TOLERANCE = 1.0


def apply_data_readings(data: dict[str, Any], b_reading: str, bernoulli_reading: str) -> dict[str, Any]:
    result = deepcopy(data)
    for attr in result["attributes"]:
        if attr["id"] == "B" and b_reading != "binomial":
            probs = attribute_probs(attr)
            if b_reading == "uniform":
                attr["distribution"] = {"type": "uniform"}
            else:
                attr["distribution"] = {"type": "categorical", "probs": probs[::-1]}
        if attr["distribution"]["type"] == "bernoulli" and bernoulli_reading == "p_on_first":
            attr["distribution"] = {"type": "bernoulli", "p": 1 - attr["distribution"]["p"]}
    return result


def fig7_distance(stats: PolicyStatistics, who: str) -> float:
    """Mean absolute gap between the model's shares and the bars of Fig. 7."""
    gaps = [abs(stats.decision_probs.get(d, 0.0) - v) for d, v in FIG7_DECISIONS[who].items()]
    gaps += [abs(stats.task_usage.get(t, 0.0) - v) for t, v in FIG7_TASKS[who].items()]
    return sum(gaps) / len(gaps)


def instance_values(final_state: list[Any], order: tuple[str, ...]) -> dict[str, Any]:
    columns = dict(zip("ABCDEFGHI", final_state))
    binary = [columns[attr] for attr in BINARY_ATTRIBUTES]
    return columns | dict(zip(order, binary))


def table6_scores(rows: list[dict[str, Any]], profits: list[float], key: str) -> tuple[int, float]:
    gaps = [abs(profit - row[key]) for profit, row in zip(profits, rows)]
    return sum(gap <= TABLE6_MATCH_TOLERANCE for gap in gaps), sum(gaps) / len(gaps)


def main() -> None:
    data = load_koffer()
    tree = load_decision_tree()
    paper = load_paper_results()
    table5, table6 = paper["table5"], paper["table6"]
    variants = sorted(data["information_structure"]["variants"])

    rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    for y_variant, b_reading, bernoulli_reading in itertools.product(variants, B_READINGS, BERNOULLI_READINGS):
        config = apply_data_readings(data, b_reading, bernoulli_reading)
        full = DIPModel(config, y_variant=y_variant, y_method="plugin")

        # Solve without the free tasks (assumption-free reduction, see without_free_tasks), then add them back.
        reduced_data, free = without_free_tasks(config, y_variant)
        free_cost = sum(task["cost"] for task in free)
        free_final_states = prod(len(task["values"]) for task in free if "values" in task)
        reduced = DIPModel(reduced_data, y_variant=y_variant, y_method="plugin")
        solution = solve_recursive(reduced)
        mdp = policy_statistics(reduced, solution.policy)
        for task in free:
            mdp.add_task(task["id"], 1.0, task["cost"])

        mdp_runs = {
            order: [
                simulate_policy(reduced, solution.policy, instance_values(row["final_state"], order))
                for row in table6
            ]
            for order in COLUMN_ORDERS
        }
        for tree_reading in TREE_READINGS:
            read_tree = apply_reading(tree, tree_reading)
            tree_stats = tree_statistics(read_tree, full)
            for order in COLUMN_ORDERS:
                tree_runs = [run_tree(read_tree, full, instance_values(r["final_state"], order)) for r in table6]
                mdp_exact, mdp_mae = table6_scores(
                    table6, [run.profit - free_cost for run in mdp_runs[order]], "profit_mdp"
                )
                tree_exact, tree_mae = table6_scores(table6, [run.profit for run in tree_runs], "profit_tree")
                rows.append(
                    {
                        "y_variant": y_variant,
                        "a1_b": b_reading,
                        "a2_bernoulli": bernoulli_reading,
                        "a5_tree": tree_reading,
                        "a5_columns": "".join(order),
                        "mdp_profit": round(mdp.expected_profit, 2),
                        "mdp_revenue": round(mdp.expected_revenue, 2),
                        "mdp_cost": round(mdp.avg_retrieval_cost, 2),
                        "mdp_final_states": len(mdp.final_states) * free_final_states,
                        "mdp_fig7_gap": round(fig7_distance(mdp, "mdp"), 4),
                        "tree_profit": round(tree_stats.expected_profit, 2),
                        "tree_revenue": round(tree_stats.expected_revenue, 2),
                        "tree_cost": round(tree_stats.avg_retrieval_cost, 2),
                        "tree_final_states": len(tree_stats.final_states),
                        "tree_fig7_gap": round(fig7_distance(tree_stats, "tree"), 4),
                        "t6_mdp_exact": mdp_exact,
                        "t6_mdp_mae": round(mdp_mae, 1),
                        "t6_tree_exact": tree_exact,
                        "t6_tree_mae": round(tree_mae, 1),
                    }
                )
        print(
            f"{y_variant:14s} {b_reading:18s} {bernoulli_reading:12s} "
            f"V={mdp.expected_profit:12.2f} root_check={solution.root_value - free_cost:12.2f} "
            f"t={time.perf_counter() - started:6.1f}s",
            flush=True,
        )

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        f.write("# Phase 2 calibration. Generated by scripts/calibrate.py; deterministic, no random seed used.\n")
        f.write("# Inputs: data/koffer.yaml, data/decision_tree.yaml, data/paper_results.yaml.\n")
        f.write(f"# Table 5 target: {table5['mdp']} | {table5['decision_tree']}\n")
        f.write("# fig7_gap compares with bar heights read by eye from Fig. 7. t6_*_exact counts rows within +-1 of Table 6.\n")
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUTPUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
