"""Start the two-phase system for a recorded demo: a clean case list and the browser opened on the console.

    python scripts/demo.py                  # tasks take 2 s, so each step is visible on screen
    python scripts/demo.py --keep           # keep the cases of the previous run (shows recovery after a restart)

Builds the design-time package first if it is missing. Cases go to results/deploy/demo.sqlite, not to the
database of scripts/run_system.py.
"""
from __future__ import annotations

import argparse
import threading
import webbrowser
from pathlib import Path

from dipmdp.data import load_koffer
from dipmdp.system.design import compile_package, load_package
from dipmdp.system.engine import CaseEngine, EventStore, SimulatedExecutor
from dipmdp.system.recommender import MDPRecommender
from dipmdp.system.server import make_server

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "results" / "deploy" / "koffer"
DATABASE = ROOT / "results" / "deploy" / "demo.sqlite"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8600)
    parser.add_argument("--task-seconds", type=float, default=2.0)
    parser.add_argument("--keep", action="store_true", help="keep cases from the previous demo run")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if not (PACKAGE / "manifest.json").exists():
        print("no deployment package yet: running the design-time phase")
        compile_package(ROOT / "models" / "koffer.cmmn", load_koffer(), PACKAGE, "margin_all")
    if not args.keep:
        DATABASE.unlink(missing_ok=True)

    model, solution, integrated, manifest = load_package(PACKAGE)
    engine = CaseEngine(
        MDPRecommender(model, solution), integrated, SimulatedExecutor(args.task_seconds), EventStore(DATABASE)
    )
    server = make_server(engine, manifest, port=args.port)
    url = f"http://127.0.0.1:{args.port}"
    print(f"package {manifest['case']}/{manifest['y_variant']}, {manifest['n_states']:,} states, V(root) {manifest['root_value']:.2f}")
    print(f"{len(engine.list_cases())} case(s) restored from {DATABASE.name}")
    print(f"{url}  (Ctrl+C to stop)", flush=True)
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
