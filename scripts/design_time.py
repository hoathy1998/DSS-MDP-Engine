"""Design-time phase of Fig. 1: from the CMMN model and parameters to a deployment package.

    python scripts/design_time.py --export-cmmn     # write models/koffer.cmmn from data/koffer.yaml first
    python scripts/design_time.py                   # the chosen Y (assumption A3)
    python scripts/design_time.py --y margin_repair --out results/deploy/koffer_margin_repair
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dipmdp.data import load_koffer
from dipmdp.system.cmmn import write_user_model
from dipmdp.system.design import compile_package

ROOT = Path(__file__).resolve().parents[1]
CMMN = ROOT / "models" / "koffer.cmmn"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--export-cmmn", action="store_true", help="regenerate the CMMN file from the YAML structure")
    parser.add_argument("--y", default="margin_all", help="Y variant in data/koffer.yaml")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "deploy" / "koffer")
    args = parser.parse_args()

    parameters = load_koffer()
    if args.export_cmmn:
        CMMN.parent.mkdir(exist_ok=True)
        CMMN.write_text(write_user_model(parameters), encoding="utf-8", newline="\n")
        print(f"wrote {CMMN}")
    print(json.dumps(compile_package(CMMN, parameters, args.out, args.y), indent=2))


if __name__ == "__main__":
    main()
