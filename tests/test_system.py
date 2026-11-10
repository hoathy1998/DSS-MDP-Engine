"""The two phases of Fig. 1, end to end: design time produces a package, deployment runs cases from it."""
import json
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from dipmdp.data import load_koffer
from dipmdp.evaluate import simulate_policy
from dipmdp.model import DIPModel
from dipmdp.solver import solve_array
from dipmdp.system.cmmn import (
    has_plan_fragment,
    integrate_plan_fragment,
    retrieve_structure,
    write_user_model,
)
from dipmdp.system.design import compile_package, filter_model, load_package
from dipmdp.system.engine import CLOSED, RUNNING, CaseEngine, EngineError, EventStore, SimulatedExecutor
from dipmdp.system.recommender import MDPRecommender
from dipmdp.system.server import make_server

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = dict(A=1500, B=100, C=1, D=2100, E=1, F=100, G=1, H=4, I=100)


@pytest.fixture(scope="module")
def package(tmp_path_factory):
    out = tmp_path_factory.mktemp("package")
    cmmn = out / "koffer.cmmn"
    cmmn.write_text(write_user_model(load_koffer()), encoding="utf-8")
    manifest = compile_package(cmmn, load_koffer(), out / "pkg", "margin_all")
    return out / "pkg", manifest


def make_engine(package, executor=None, store=None):
    model, solution, integrated, _ = load_package(package[0])
    return CaseEngine(MDPRecommender(model, solution), integrated, executor or SimulatedExecutor(), store)


def follow_to_end(engine, case_id):
    for _ in range(40):
        view = engine.view(case_id)
        if view["phase"] == CLOSED:
            return view
        best = view["recommendation"]["best"]
        action = ("do", best["id"]) if best["kind"] == "do" else ("decide", best["decision"])
        engine.select_action(case_id, action)
    raise AssertionError("the case did not close")


# Design time.


def test_cmmn_round_trip_recovers_the_structure_of_the_paper():
    data = load_koffer()
    structure = retrieve_structure(write_user_model(data))
    assert set(structure) == {item["id"] for item in data["plan_items"] + data["attributes"]}
    for item in data["plan_items"] + data["attributes"]:
        assert set(structure[item["id"]]["preceding"]) == set(item["preceding"]), item["id"]
        assert structure[item["id"]]["required"] == item["required"], item["id"]
    assert structure["alpha"]["kind"] == "stage"
    assert structure["F"]["acquires"] == "F"


@pytest.mark.parametrize("integrated", [False, True])
def test_stage_children_follow_the_schema_order(integrated):
    xml = write_user_model(load_koffer())
    root = ET.fromstring(integrate_plan_fragment(xml) if integrated else xml)
    ns = "{http://www.omg.org/spec/CMMN/20151109/MODEL}"
    for stage in [*root.iter(f"{ns}casePlanModel"), *root.iter(f"{ns}stage")]:
        order = [{f"{ns}planItem": 0, f"{ns}sentry": 1}.get(child.tag, 2) for child in stage]
        assert order == sorted(order)


def test_checked_in_model_is_the_one_the_parameters_describe():
    assert retrieve_structure((ROOT / "models" / "koffer.cmmn").read_text(encoding="utf-8")) == retrieve_structure(
        write_user_model(load_koffer())
    )


def test_filter_refuses_a_cmmn_that_disagrees_with_the_parameters():
    data = load_koffer()
    xml = write_user_model(data)
    data["attributes"] = [attr for attr in data["attributes"] if attr["id"] != "I"]
    with pytest.raises(ValueError, match="only in CMMN"):
        filter_model(xml, data)


def test_precedence_comes_from_the_cmmn_file():
    # Editing the model changes the MDP without touching the parameters.
    data = load_koffer()
    next(attr for attr in data["attributes"] if attr["id"] == "D")["preceding"] = []
    xml = write_user_model(data)
    filtered = filter_model(xml, load_koffer())
    assert next(attr for attr in filtered["attributes"] if attr["id"] == "D")["preceding"] == []


def test_plan_fragment_is_integrated_once_and_keeps_the_structure():
    xml = write_user_model(load_koffer())
    assert not has_plan_fragment(xml)
    integrated = integrate_plan_fragment(xml)
    assert has_plan_fragment(integrated)
    assert retrieve_structure(integrated) == retrieve_structure(xml)
    with pytest.raises(ValueError):
        integrate_plan_fragment(integrated)


def test_package_matches_solving_directly(package):
    _, manifest = package
    direct = solve_array(DIPModel(load_koffer(), y_variant="margin_all", y_method="plugin"))
    assert manifest["root_value"] == pytest.approx(direct.root_value)
    assert manifest["n_reachable"] == 640_224


def test_tampered_package_is_refused(package, tmp_path):
    import shutil

    copy = tmp_path / "pkg"
    shutil.copytree(package[0], copy)
    with open(copy / "model.json", "a", encoding="utf-8") as f:
        f.write(" ")
    with pytest.raises(ValueError, match="manifest"):
        load_package(copy)


# Deployment.


def test_engine_refuses_a_model_without_the_plan_fragment(package):
    model, solution, _, _ = load_package(package[0])
    with pytest.raises(ValueError, match="plan fragment"):
        CaseEngine(MDPRecommender(model, solution), write_user_model(load_koffer()), SimulatedExecutor())


def test_following_every_recommendation_equals_the_mdp_policy(package):
    engine = make_engine(package)
    view = follow_to_end(engine, engine.open_case(SCENARIO))
    model, solution, _, _ = load_package(package[0])
    run = simulate_policy(model, solution.policy, SCENARIO)
    assert view["decision"] == run.decision
    assert view["outcome"]["realised_profit"] == pytest.approx(run.profit)
    assert view["cost"] == pytest.approx(run.cost)


def test_advice_continues_after_a_deviation(package):
    engine = make_engine(package)
    case_id = engine.open_case(SCENARIO)
    assert engine.view(case_id)["recommendation"]["best"] == {"kind": "do", "id": "beta"}
    engine.select_action(case_id, ("do", "alpha"))
    view = engine.view(case_id)
    assert view["cost"] == 20
    assert view["recommendation"] is not None
    selected = [e for e in engine.subscribe(case_id)[1] if e["type"] == "action_selected"]
    assert selected[0]["followed"] is False
    assert follow_to_end(engine, case_id)["phase"] == CLOSED


def test_deviation_keeps_the_reason_and_the_expected_loss(package):
    engine = make_engine(package)
    case_id = engine.open_case(SCENARIO)
    values = {(a["kind"], a.get("id")): a["expected_profit"] for a in engine.view(case_id)["recommendation"]["actions"]}
    engine.select_action(case_id, ("do", "2"), reason="  Kinh nghiệm với khách hàng này ")
    first = engine.view(case_id)["deviations"][0]
    assert first["reason"] == "Kinh nghiệm với khách hàng này"
    assert first["action"] == {"kind": "do", "id": "2"} and first["recommended"] == {"kind": "do", "id": "beta"}
    assert first["expected_loss"] == pytest.approx(values[("do", "beta")] - values[("do", "2")])
    assert first["expected_loss"] > 0
    engine.select_action(case_id, ("do", "3"))  # required tasks tie with the advice, so nothing is given up
    second = engine.view(case_id)["deviations"][1]
    assert second["expected_loss"] == pytest.approx(0, abs=1e-9) and second["reason"] is None

    followed = engine.open_case(SCENARIO)
    assert follow_to_end(engine, followed)["deviations"] == []


def test_illegal_actions_are_rejected(package):
    engine = make_engine(package)
    case_id = engine.open_case(SCENARIO)
    with pytest.raises(EngineError):
        engine.select_action(case_id, ("decide", 2000))  # required tasks are not done
    with pytest.raises(EngineError):
        engine.select_action(case_id, ("do", "F"))  # needs alpha and A first
    follow_to_end(engine, case_id)
    with pytest.raises(EngineError):
        engine.select_action(case_id, ("do", "alpha"))  # closed


def test_rejections_name_the_broken_rule(package):
    engine = make_engine(package)
    case_id = engine.open_case(SCENARIO)
    with pytest.raises(EngineError, match=r"required tasks not done yet: beta, 3, 4, C, E"):
        engine.select_action(case_id, ("decide", 2000))
    with pytest.raises(EngineError, match=r"task F must wait for alpha, A"):
        engine.select_action(case_id, ("do", "F"))
    with pytest.raises(EngineError, match=r"unknown task"):
        engine.select_action(case_id, ("do", "Z"))
    engine.select_action(case_id, ("do", "C"))
    with pytest.raises(EngineError, match=r"task C is already done"):
        engine.select_action(case_id, ("do", "C"))


def test_second_choice_while_a_task_runs_is_rejected(package):
    captured = {}

    class Manual:
        def launch(self, case_id, task_id, scenario, done):
            captured["done"] = done

    engine = make_engine(package, Manual())
    case_id = engine.open_case(SCENARIO)
    engine.select_action(case_id, ("do", "C"))
    assert engine.view(case_id)["phase"] == RUNNING
    assert engine.view(case_id)["recommendation"] is None
    with pytest.raises(EngineError):
        engine.select_action(case_id, ("do", "E"))

    captured["done"](1, None)
    captured["done"](1, None)  # a duplicate report must not charge the cost twice
    assert engine.view(case_id)["cost"] == 2
    assert engine.view(case_id)["attributes"]["C"] == 1


def test_failed_and_invalid_task_results_keep_the_case_alive(package):
    captured = {}

    class Manual:
        def launch(self, case_id, task_id, scenario, done):
            captured["done"] = done

    engine = make_engine(package, Manual())
    case_id = engine.open_case(SCENARIO)
    engine.select_action(case_id, ("do", "C"))
    captured["done"](None, "the credit bureau timed out")
    engine.select_action(case_id, ("do", "C"))
    captured["done"](99, None)  # outside dom(C)
    view = engine.view(case_id)
    assert view["cost"] == 0 and view["attributes"]["C"] is None
    assert ("do", "C") in {("do", a.get("id")) for a in view["recommendation"]["actions"]}


def test_hidden_values_stay_hidden_until_the_case_closes(package):
    engine = make_engine(package)
    case_id = engine.open_case(SCENARIO)
    assert "scenario" not in engine.view(case_id)
    assert all("scenario" not in event for event in engine.subscribe(case_id)[1])
    assert follow_to_end(engine, case_id)["scenario"] == SCENARIO


def test_restart_resumes_open_cases_from_the_event_log(package, tmp_path):
    db = tmp_path / "cases.sqlite"
    first = make_engine(package, store=EventStore(db))
    open_id = first.open_case(SCENARIO, case_id="open")
    first.select_action(open_id, ("do", "alpha"))
    first.select_action(open_id, ("do", "E"))
    closed_id = first.open_case(SCENARIO, case_id="closed")
    follow_to_end(first, closed_id)
    before_open, before_closed = first.view(open_id), first.view(closed_id)
    first.store.close()

    second = make_engine(package, store=EventStore(db))
    assert second.view(open_id) == before_open
    assert second.view(closed_id) == before_closed
    assert follow_to_end(second, open_id)["phase"] == CLOSED


def test_restart_relaunches_a_task_that_was_running(package, tmp_path):
    db = tmp_path / "cases.sqlite"

    class Never:
        def launch(self, case_id, task_id, scenario, done):
            pass

    first = make_engine(package, Never(), EventStore(db))
    first.open_case(SCENARIO, case_id="c")
    first.select_action("c", ("do", "E"))
    first.store.close()
    second = make_engine(package, SimulatedExecutor(), EventStore(db))
    view = second.view("c")
    assert view["attributes"]["E"] == 1 and view["cost"] == 3


def test_many_cases_at_once_stay_separate(package):
    engine = make_engine(package, SimulatedExecutor(latency=0.001))
    scenarios = {f"c{i}": dict(SCENARIO, A=[1500, 1700, 1900, 2100][i % 4]) for i in range(40)}
    errors = []

    def run(case_id, scenario):
        try:
            engine.open_case(scenario, case_id=case_id)
            deadline = time.time() + 30
            while time.time() < deadline:
                view = engine.view(case_id)
                if view["phase"] == CLOSED:
                    return
                if view["recommendation"]:
                    best = view["recommendation"]["best"]
                    action = ("do", best["id"]) if best["kind"] == "do" else ("decide", best["decision"])
                    engine.select_action(case_id, action)
                else:
                    time.sleep(0.001)
            errors.append(f"{case_id} timed out")
        except Exception as error:  # a test thread must report, not vanish
            errors.append(repr(error))

    threads = [threading.Thread(target=run, args=item) for item in scenarios.items()]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors
    model, solution, _, _ = load_package(package[0])
    for case_id, scenario in scenarios.items():
        run_result = simulate_policy(model, solution.policy, scenario)
        assert engine.view(case_id)["outcome"]["realised_profit"] == pytest.approx(run_result.profit)


def test_recommender_answers_in_real_time(package):
    engine = make_engine(package)
    for _ in range(10):
        follow_to_end(engine, engine.open_case(SCENARIO))
    stats = engine.latency_stats()
    assert stats["count"] > 50
    assert stats["p99_ms"] < 50  # far below a person's reaction time, with room for a slow test machine


# HTTP and live push.


@pytest.fixture()
def live_server(package):
    engine = make_engine(package, SimulatedExecutor(latency=0.05))
    server = make_server(engine, package[1], port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def call(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, json.loads(response.read())


def test_http_case_with_live_events(live_server):
    status, view = call(f"{live_server}/api/cases", {"scenario": SCENARIO})
    assert status == 201 and "scenario" not in view
    case_id = view["case_id"]

    received = []

    def listen():
        with urllib.request.urlopen(f"{live_server}/api/cases/{case_id}/events", timeout=20) as stream:
            for raw in stream:
                line = raw.decode("utf-8").strip()
                if line.startswith("data: "):
                    received.append(json.loads(line[6:]))
                    if received[-1]["type"] == "case_closed":
                        return

    listener = threading.Thread(target=listen, daemon=True)
    listener.start()

    while True:
        _, view = call(f"{live_server}/api/cases/{case_id}")
        if view["phase"] == CLOSED:
            break
        if view["recommendation"]:
            best = view["recommendation"]["best"]
            call(f"{live_server}/api/cases/{case_id}/actions", best)
        else:
            time.sleep(0.01)
    listener.join(timeout=10)
    assert not listener.is_alive()
    kinds = [event["type"] for event in received]
    assert kinds[0] == "case_opened" and kinds[-1] == "case_closed"
    assert {"recommendation", "action_selected", "task_launched", "task_completed"} <= set(kinds)
    assert [event["seq"] for event in received] == list(range(1, len(received) + 1))
    assert all("scenario" not in event for event in received)


def test_http_errors_are_clear(live_server):
    _, view = call(f"{live_server}/api/cases", {"seed": 1})
    url = f"{live_server}/api/cases/{view['case_id']}/actions"
    for target, body, expected in (
        (url, {"kind": "decide", "decision": 2000}, 409),
        (url, {"kind": "nonsense"}, 400),
        (url, {"kind": "do"}, 400),
        (url, {"kind": "do", "id": ["A"]}, 400),
        (url, {"kind": "do", "id": "beta", "reason": 5}, 400),
        (url, {"kind": "do", "id": "beta", "reason": "x" * 501}, 400),
        (f"{live_server}/api/cases", {"scenario": dict(SCENARIO, A=1)}, 400),
        (f"{live_server}/api/cases/nope/actions", {"kind": "do", "id": "A"}, 404),
    ):
        with pytest.raises(urllib.error.HTTPError) as caught:
            call(target, body)
        assert caught.value.code == expected
    with pytest.raises(urllib.error.HTTPError) as caught:
        call(f"{live_server}/api/cases/nope")
    assert caught.value.code == 404


def test_seeded_case_is_reproducible(live_server):
    first = call(f"{live_server}/api/cases", {"seed": 5})[1]["case_id"]
    second = call(f"{live_server}/api/cases", {"seed": 5})[1]["case_id"]
    closed = []
    for case_id in (first, second):
        while True:
            view = call(f"{live_server}/api/cases/{case_id}")[1]
            if view["phase"] == CLOSED:
                closed.append(view["scenario"])
                break
            if view["recommendation"]:
                call(f"{live_server}/api/cases/{case_id}/actions", view["recommendation"]["best"])
            else:
                time.sleep(0.01)
    assert closed[0] == closed[1]


def test_ui_is_served(live_server):
    with urllib.request.urlopen(f"{live_server}/", timeout=5) as response:
        page = response.read().decode("utf-8")
    assert "Bàn điều phối Koffer" in page


def test_meta_carries_the_process_rules(live_server, package):
    _, meta = call(f"{live_server}/api/meta")
    model = load_package(package[0])[0]
    items = {i["id"]: i for i in meta["plan_items"] + meta["attributes"]}
    for source in model.plan_items + model.attributes:
        assert items[source["id"]]["preceding"] == source["preceding"]
        assert items[source["id"]]["required"] == source["required"]
    assert {i["id"] for i in meta["plan_items"] if i["kind"] == "stage"} == {"alpha", "beta"}
