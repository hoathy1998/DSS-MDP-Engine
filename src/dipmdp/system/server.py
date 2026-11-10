"""HTTP interface of the deployment phase, standard library only.

GET  /                         the decision maker's screen
GET  /api/meta                 case model, package manifest, recommender latency
GET  /api/cases                all cases
POST /api/cases                open a case: {"seed": 1} or {"scenario": {...}}
GET  /api/cases/<id>           current view of one case
POST /api/cases/<id>/actions   the decision maker's choice: {"kind": "do", "id": "A", "reason": "optional"}
GET  /api/cases/<id>/events    server-sent events; resumes from Last-Event-ID
"""
from __future__ import annotations

import json
import queue
import random
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from dipmdp.system.engine import CLOSED, CaseEngine, EngineError
from dipmdp.system.recommender import action_from_json

UI_FILE = Path(__file__).with_name("ui.html")
HEARTBEAT_SECONDS = 15.0
MAX_BODY_BYTES = 1_000_000
MAX_REASON_CHARS = 500


def random_scenario(engine: CaseEngine, seed: int | None) -> dict[str, Any]:
    rng = random.Random(seed)
    return {
        attr["id"]: rng.choices(attr["values"], weights=engine.model.attribute_probs[attr["id"]])[0]
        for attr in engine.model.attributes
    }


def make_server(engine: CaseEngine, manifest: dict[str, Any], host: str = "127.0.0.1", port: int = 8600) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        server_version = "dipmdp"

        def log_message(self, *args: Any) -> None:
            pass

        def _json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _error(self, status: HTTPStatus, message: str) -> None:
            self._json({"error": message}, status)

        def _body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY_BYTES:
                raise ValueError("request body is too large")
            payload = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(payload, dict):
                raise ValueError("the request body must be a JSON object")
            return payload

        def _path_parts(self) -> list[str]:
            return [part for part in self.path.split("?")[0].split("/") if part]

        def do_GET(self) -> None:
            parts = self._path_parts()
            try:
                if not parts:
                    body = UI_FILE.read_bytes()
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif parts == ["api", "meta"]:
                    self._json(
                        {
                            "manifest": manifest,
                            "latency": engine.latency_stats(),
                            "attributes": [
                                {
                                    "id": a["id"], "name": a.get("name"), "cost": a["cost"],
                                    "preceding": a["preceding"], "required": a["required"],
                                }
                                for a in engine.model.attributes
                            ],
                            "plan_items": [
                                {
                                    "id": i["id"], "name": i.get("name"), "cost": i["cost"], "kind": i.get("kind"),
                                    "preceding": i["preceding"], "required": i["required"],
                                }
                                for i in engine.model.plan_items
                            ],
                        }
                    )
                elif parts == ["api", "cases"]:
                    self._json(engine.list_cases())
                elif len(parts) == 3 and parts[:2] == ["api", "cases"]:
                    self._json(engine.view(parts[2]))
                elif len(parts) == 4 and parts[:2] == ["api", "cases"] and parts[3] == "events":
                    self._stream(parts[2])
                else:
                    self._error(HTTPStatus.NOT_FOUND, "no such resource")
            except KeyError:
                self._error(HTTPStatus.NOT_FOUND, "no such case")

        def do_POST(self) -> None:
            parts = self._path_parts()
            try:
                if parts == ["api", "cases"]:
                    body = self._body()
                    scenario = body.get("scenario") or random_scenario(engine, body.get("seed"))
                    self._json(engine.view(engine.open_case(scenario)), HTTPStatus.CREATED)
                elif len(parts) == 4 and parts[:2] == ["api", "cases"] and parts[3] == "actions":
                    body = self._body()
                    reason = body.get("reason")
                    if reason is not None and (not isinstance(reason, str) or len(reason) > MAX_REASON_CHARS):
                        raise ValueError(f"reason must be text of at most {MAX_REASON_CHARS} characters")
                    engine.select_action(parts[2], action_from_json(body), reason=reason)
                    self._json(engine.view(parts[2]))
                else:
                    self._error(HTTPStatus.NOT_FOUND, "no such resource")
            except KeyError as missing:
                self._error(HTTPStatus.NOT_FOUND, f"not found: {missing}")
            except EngineError as conflict:
                self._error(HTTPStatus.CONFLICT, str(conflict))
            except ValueError as invalid:
                self._error(HTTPStatus.BAD_REQUEST, str(invalid))

        def _stream(self, case_id: str) -> None:
            last_seen = self.headers.get("Last-Event-ID", "0")
            after = int(last_seen) if last_seen.isdigit() else 0
            subscriber, missed = engine.subscribe(case_id, after)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            def send(event: dict[str, Any]) -> None:
                text = f"id: {event['seq']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                self.wfile.write(text.encode("utf-8"))
                self.wfile.flush()

            try:
                for event in missed:
                    send(event)
                while engine.view(case_id)["phase"] != CLOSED or not subscriber.empty():
                    try:
                        send(subscriber.get(timeout=HEARTBEAT_SECONDS))
                    except queue.Empty:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionError):
                pass
            finally:
                engine.unsubscribe(case_id, subscriber)

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server
