"""Show that the running server, not only the screen, enforces the process rules.

    python scripts/demo_rule_check.py            # against http://127.0.0.1:8600 (start scripts/demo.py first)

Opens a case over the API and sends three actions the rules forbid; each answer names the rule.
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def post(url: str, body: dict) -> tuple[int, dict]:
    request = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="http://127.0.0.1:8600")
    args = parser.parse_args()

    status, view = post(f"{args.base}/api/cases", {"seed": 1})
    case_id = view["case_id"]
    print(f"opened case {case_id} (HTTP {status}); recommended first step: {view['recommendation']['best']}")
    for label, action in (
        ("bid 2000 before the required tasks", {"kind": "decide", "decision": 2000}),
        ("task F before stage alpha and task A", {"kind": "do", "id": "F"}),
        ("task D before task 2", {"kind": "do", "id": "D"}),
    ):
        status, answer = post(f"{args.base}/api/cases/{case_id}/actions", action)
        print(f"\n{label}: {json.dumps(action)}\n  HTTP {status}: {answer.get('error', answer)}")


if __name__ == "__main__":
    main()
