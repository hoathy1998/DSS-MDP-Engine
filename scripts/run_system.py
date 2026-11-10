"""Deployment phase of Fig. 1: serve a design-time package to decision makers.

    python scripts/design_time.py --export-cmmn     # once, to create the package
    python scripts/run_system.py                    # then open http://127.0.0.1:8600

Tasks are simulated: each takes --task-seconds and returns the value from the case's hidden scenario.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from dipmdp.system.design import load_package
from dipmdp.system.engine import CaseEngine, EventStore, SimulatedExecutor
from dipmdp.system.recommender import MDPRecommender
from dipmdp.system.server import make_server

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package", type=Path, default=ROOT / "results" / "deploy" / "koffer")
    parser.add_argument("--db", type=Path, default=ROOT / "results" / "deploy" / "cases.sqlite")
    parser.add_argument("--port", type=int, default=8600)
    parser.add_argument("--task-seconds", type=float, default=1.5)
    args = parser.parse_args()

    model, solution, integrated, manifest = load_package(args.package)
    engine = CaseEngine(
        MDPRecommender(model, solution), integrated, SimulatedExecutor(args.task_seconds), EventStore(args.db)
    )
    server = make_server(engine, manifest, port=args.port)
    print(f"http://127.0.0.1:{args.port}  package {manifest['case']}/{manifest['y_variant']}, V(root) {manifest['root_value']:.2f}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
