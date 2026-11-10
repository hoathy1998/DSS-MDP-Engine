"""Case engine of Fig. 1: runs the loop of the integrated model and pushes every change to subscribers.

Request MDP recommender -> Information or Decision -> (Information: launch task -> result -> again)
                                                   -> (Decision: close the case)

The decision maker stays in control (Section 6.3): any allowed action is accepted, and the recommender
is asked again from the resulting state. Each case is a list of events in SQLite, and its state is rebuilt
from them, so a restart resumes open cases. This is a small engine for a CMMN subset, not a full one.
"""
from __future__ import annotations

import json
import queue
import sqlite3
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from dipmdp.information_structure import realised_y
from dipmdp.model import Action, State
from dipmdp.system.cmmn import has_plan_fragment
from dipmdp.system.recommender import MDPRecommender, action_to_json

REQUEST = "request_recommender"
CHOOSE = "information_or_decision"
RUNNING = "task_running"
CLOSED = "closed"
_LATENCY_WINDOW = 2000


class EngineError(Exception):
    """A request the current case state does not allow; the server answers it with 409."""


class TaskExecutor(Protocol):
    """Runs a task and reports back. A real deployment connects this to the systems that do the work."""

    def launch(
        self, case_id: str, task_id: str, scenario: dict[str, Any] | None, done: Callable[[Any, str | None], None]
    ) -> None: ...


class SimulatedExecutor:
    """Takes `latency` seconds, then returns the attribute's value from the case's hidden scenario."""

    def __init__(self, latency: float = 0.0):
        self.latency = latency

    def launch(
        self, case_id: str, task_id: str, scenario: dict[str, Any] | None, done: Callable[[Any, str | None], None]
    ) -> None:
        def finish() -> None:
            if scenario is None:
                done(None, f"case {case_id} has no scenario to simulate task {task_id}")
            else:
                done(scenario.get(task_id), None)

        if self.latency <= 0:
            finish()
        else:
            timer = threading.Timer(self.latency, finish)
            timer.daemon = True
            timer.start()


class EventStore:
    """Append-only event log."""

    def __init__(self, path: str | Path = ":memory:"):
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS events (case_id TEXT, seq INTEGER, event TEXT, PRIMARY KEY (case_id, seq))"
        )
        self._connection.commit()

    def append(self, case_id: str, seq: int, event: dict[str, Any]) -> None:
        self._connection.execute(
            "INSERT INTO events VALUES (?, ?, ?)", (case_id, seq, json.dumps(event, ensure_ascii=False))
        )
        self._connection.commit()

    def all_cases(self) -> dict[str, list[dict[str, Any]]]:
        cases: dict[str, list[dict[str, Any]]] = {}
        for case_id, event in self._connection.execute("SELECT case_id, event FROM events ORDER BY rowid"):
            cases.setdefault(case_id, []).append(json.loads(event))
        return cases

    def close(self) -> None:
        self._connection.close()


@dataclass
class Case:
    case_id: str
    state: State
    scenario: dict[str, Any] | None
    phase: str = REQUEST
    cost: float = 0.0
    running_task: str | None = None
    decision: Any = None
    recommendation: dict[str, Any] | None = None
    outcome: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


class CaseEngine:
    def __init__(
        self,
        recommender: MDPRecommender,
        integrated_cmmn: str,
        executor: TaskExecutor,
        store: EventStore | None = None,
        clock: Callable[[], float] = time.time,
    ):
        if not has_plan_fragment(integrated_cmmn):
            raise ValueError("the CMMN model has no process control plan fragment (Section 6.1)")
        self.recommender = recommender
        self.model = recommender.model
        self.executor = executor
        self.store = store or EventStore()
        self.clock = clock
        self._lock = threading.RLock()
        self._cases: dict[str, Case] = {}
        self._subscribers: dict[str, list[queue.Queue]] = {}
        self._latencies: deque[float] = deque(maxlen=_LATENCY_WINDOW)
        self._replay()

    # Event log. Every change of a case goes through _record, and _apply is the only code that changes it.

    def _record(self, case: Case, kind: str, **payload: Any) -> dict[str, Any]:
        event = {"seq": len(case.events) + 1, "type": kind, "time": self.clock(), **payload}
        self.store.append(case.case_id, event["seq"], event)
        self._apply(case, event)
        case.events.append(event)
        public = self._public_event(event)
        for subscriber in self._subscribers.get(case.case_id, []):
            subscriber.put(public)
        return event

    def _apply(self, case: Case, event: dict[str, Any]) -> None:
        kind = event["type"]
        if kind == "recommendation":
            case.recommendation = event["recommendation"]
            case.phase = CHOOSE
        elif kind == "task_launched":
            case.running_task = event["task"]
            case.phase = RUNNING
        elif kind == "task_completed":
            task_id = event["task"]
            case.cost += float(self.model.task(task_id)["cost"])
            if task_id in self.model.attribute_index:
                case.state = self.model.observe(case.state, task_id, event["value"])
            else:
                case.state = self.model.transitions(case.state, ("do", task_id))[0][1]
            case.running_task = None
            case.phase = REQUEST
        elif kind == "task_failed":
            case.running_task = None
            case.phase = REQUEST
        elif kind == "case_closed":
            case.decision = event["decision"]
            case.outcome = event["outcome"]
            case.phase = CLOSED

    def _replay(self) -> None:
        """Rebuild cases after a restart, then resume whatever was in progress."""
        for case_id, events in self.store.all_cases().items():
            case = Case(case_id, self.model.root_state, events[0].get("scenario"))
            for event in events:
                self._apply(case, event)
                case.events.append(event)
            self._cases[case_id] = case
        for case in self._cases.values():
            if case.phase == REQUEST:
                self._request_recommendation(case)
            elif case.phase == RUNNING:
                self._launch(case, case.running_task)

    @staticmethod
    def _public_event(event: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in event.items() if key != "scenario"}

    # The control loop.

    def _request_recommendation(self, case: Case) -> None:
        started = time.perf_counter()
        recommendation = self.recommender.recommend(case.state)
        self._latencies.append(time.perf_counter() - started)
        self._record(case, "recommendation", recommendation=recommendation.to_json())

    def _launch(self, case: Case, task_id: str) -> None:
        def done(value: Any, error: str | None) -> None:
            self._task_result(case.case_id, task_id, value, error)

        self.executor.launch(case.case_id, task_id, case.scenario, done)

    def _task_result(self, case_id: str, task_id: str, value: Any, error: str | None) -> None:
        with self._lock:
            case = self._cases[case_id]
            if case.phase != RUNNING or case.running_task != task_id:
                return  # a duplicate report of a task that has already finished
            if error is None and task_id in self.model.attribute_index:
                domain = next(a["values"] for a in self.model.attributes if a["id"] == task_id)
                if value not in domain:
                    error = f"task {task_id} returned {value!r}, outside its domain {domain!r}"
            if error is not None:
                self._record(case, "task_failed", task=task_id, error=error)
            else:
                self._record(case, "task_completed", task=task_id, value=value, state=_state_digits(case.state))
            self._request_recommendation(case)

    # Public interface.

    def open_case(self, scenario: dict[str, Any] | None = None, case_id: str | None = None) -> str:
        with self._lock:
            case_id = case_id or uuid.uuid4().hex[:12]
            if case_id in self._cases:
                raise EngineError(f"case {case_id} already exists")
            if scenario is not None:
                self._check_scenario(scenario)
            case = Case(case_id, self.model.root_state, scenario)
            self._cases[case_id] = case
            self._record(case, "case_opened", scenario=scenario)
            self._request_recommendation(case)
            return case_id

    def _check_scenario(self, scenario: dict[str, Any]) -> None:
        for attr in self.model.attributes:
            if scenario.get(attr["id"]) not in attr["values"]:
                raise ValueError(f"scenario value of {attr['id']} must be one of {attr['values']}")

    def select_action(
        self, case_id: str, action: Action, actor: str = "decision_maker", reason: str | None = None
    ) -> None:
        """The decision maker's choice in the Information or Decision task.

        A choice other than the advice is accepted (Section 6.3). The event keeps the decision maker's reason,
        for instance experience the model does not hold, and the expected profit given up against the advice.
        """
        with self._lock:
            case = self._get(case_id)
            if case.phase != CHOOSE:
                raise EngineError(f"case {case_id} is in phase {case.phase}, not waiting for a choice")
            allowed = self.recommender.solution.action_values(case.state)
            if action not in allowed:
                raise EngineError(f"{action!r} is not allowed in case {case_id}: {self._blocked_reason(case, action)}")
            best = case.recommendation["best"]
            followed = action_to_json(action) == best
            expected_loss = max(allowed.values()) - allowed[action]
            self._record(
                case, "action_selected", action=action_to_json(action), followed=followed, recommended=best,
                actor=actor, expected_loss=expected_loss, reason=(reason or "").strip() or None,
            )
            if action[0] == "decide":
                self._record(case, "case_closed", decision=action[1], outcome=self._outcome(case, action, allowed[action]))
                return
            self._record(case, "task_launched", task=action[1])
            self._launch(case, action[1])

    def _blocked_reason(self, case: Case, action: Action) -> str:
        """Which process rule forbids the action: a required task still open, a predecessor not done, or a repeat."""
        task_ids = [item["id"] for item in self.model.plan_items] + [attr["id"] for attr in self.model.attributes]
        if action[0] == "decide":
            missing = [t for t in task_ids if self.model.is_required(t) and not self.model.is_done(case.state, t)]
            if missing:
                return f"required tasks not done yet: {', '.join(missing)}"
            return f"{action[1]!r} is not one of the decisions {self.model.decisions!r}"
        if action[1] not in task_ids:
            return f"unknown task {action[1]!r}"
        if self.model.is_done(case.state, action[1]):
            return f"task {action[1]} is already done"
        waiting = [p for p in self.model.task(action[1])["preceding"] if not self.model.is_done(case.state, p)]
        return f"task {action[1]} must wait for {', '.join(waiting)}"

    def _outcome(self, case: Case, action: Action, expected: float) -> dict[str, Any]:
        outcome: dict[str, Any] = {
            "cost": case.cost,
            "expected_revenue": expected,
            "expected_profit": expected - case.cost,
        }
        if case.scenario is not None:
            revenue = realised_y(self.model, case.scenario, action[1])
            outcome |= {"realised_revenue": revenue, "realised_profit": revenue - case.cost}
        return outcome

    def _get(self, case_id: str) -> Case:
        if case_id not in self._cases:
            raise KeyError(case_id)
        return self._cases[case_id]

    def view(self, case_id: str) -> dict[str, Any]:
        """What the decision maker may see: hidden values appear only after the case closes."""
        with self._lock:
            case = self._get(case_id)
            known = {
                attr["id"]: attr["values"][digit - 1] if digit else None
                for attr, digit in zip(self.model.attributes, case.state[1])
            }
            plan = {item["id"]: bool(bit) for item, bit in zip(self.model.plan_items, case.state[0])}
            view = {
                "case_id": case_id,
                "phase": case.phase,
                "cost": case.cost,
                "running_task": case.running_task,
                "attributes": known,
                "plan_items": plan,
                "recommendation": case.recommendation if case.phase == CHOOSE else None,
                "decision": case.decision,
                "outcome": case.outcome,
                "deviations": [
                    {key: event.get(key) for key in ("seq", "action", "recommended", "expected_loss", "reason")}
                    for event in case.events
                    if event["type"] == "action_selected" and not event["followed"]
                ],
                "last_seq": len(case.events),
            }
            if case.phase == CLOSED:
                view["scenario"] = case.scenario
            return view

    def list_cases(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {"case_id": case.case_id, "phase": case.phase, "cost": case.cost, "decision": case.decision}
                for case in self._cases.values()
            ]

    def subscribe(self, case_id: str, after_seq: int = 0) -> tuple[queue.Queue, list[dict[str, Any]]]:
        """A queue of future events and the events already missed, taken atomically so none is lost."""
        with self._lock:
            case = self._get(case_id)
            subscriber: queue.Queue = queue.Queue()
            self._subscribers.setdefault(case_id, []).append(subscriber)
            return subscriber, [self._public_event(e) for e in case.events if e["seq"] > after_seq]

    def unsubscribe(self, case_id: str, subscriber: queue.Queue) -> None:
        with self._lock:
            self._subscribers.get(case_id, []).remove(subscriber)

    def latency_stats(self) -> dict[str, float | int]:
        """Recommender latency in milliseconds over the most recent requests."""
        with self._lock:
            samples = sorted(self._latencies)
        if not samples:
            return {"count": 0}
        return {
            "count": len(samples),
            "median_ms": round(1000 * samples[len(samples) // 2], 3),
            "p99_ms": round(1000 * samples[min(len(samples) - 1, int(0.99 * len(samples)))], 3),
            "max_ms": round(1000 * samples[-1], 3),
        }


def _state_digits(state: State) -> list[int]:
    return list(state[0] + state[1])
