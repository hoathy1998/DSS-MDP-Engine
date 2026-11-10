"""CMMN 1.1 XML for optimizable DIPs: the user model (5.1), its MDP structure (5.2), the plan fragment (6.1).

Only the subset the paper's constraints need: stages, human tasks, manual activation, required rules and
entry sentries on task completion. CMMN has no notion of cost or probability, so those stay in the
parameter file; the dip: extension only links a task to the case file item it acquires.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

CMMN_NS = "http://www.omg.org/spec/CMMN/20151109/MODEL"
DIP_NS = "urn:dipmdp:extensions"
ET.register_namespace("cmmn", CMMN_NS)
ET.register_namespace("dip", DIP_NS)

DECISION_TASK = "decide"
REQUEST_RECOMMENDER = "request_mdp_recommender"
INFORMATION_OR_DECISION = "information_or_decision"
MILESTONE_INFORMATION = "information"
MILESTONE_DECISION = "decision"


def _c(tag: str) -> str:
    return f"{{{CMMN_NS}}}{tag}"


def _d(tag: str) -> str:
    return f"{{{DIP_NS}}}{tag}"


def _plan_item(
    parent: ET.Element,
    item_id: str,
    definition: str,
    required: bool = False,
    manual: bool = True,
    repeatable: bool = False,
) -> ET.Element:
    item = ET.SubElement(parent, _c("planItem"), id=f"PI_{item_id}", definitionRef=definition)
    if required or manual or repeatable:
        control = ET.SubElement(item, _c("itemControl"))
        if repeatable:
            ET.SubElement(control, _c("repetitionRule"))
        if required:
            ET.SubElement(control, _c("requiredRule"))
        if manual:
            ET.SubElement(control, _c("manualActivationRule"))
    return item


def _add_sentry(parent: ET.Element, item: ET.Element, owner: str, sources: list[str], event: str = "complete") -> None:
    if not sources:
        return
    sentry_id = f"Sentry_{owner}"
    ET.SubElement(item, _c("entryCriterion"), id=f"EC_{owner}", sentryRef=sentry_id)
    sentry = ET.SubElement(parent, _c("sentry"), id=sentry_id)
    for source in sources:
        part = ET.SubElement(sentry, _c("planItemOnPart"), sourceRef=f"PI_{source}")
        ET.SubElement(part, _c("standardEvent")).text = event


def _serialise(root: ET.Element) -> str:
    """Put each stage's children in the order the CMMN schema requires, then write the XML."""
    rank = {_c("planItem"): 0, _c("sentry"): 1}
    for stage in [*root.iter(_c("casePlanModel")), *root.iter(_c("stage"))]:
        children = sorted(stage, key=lambda child: rank.get(child.tag, 2))
        for child in list(stage):
            stage.remove(child)
        stage.extend(children)
    ET.indent(root)
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def write_user_model(data: dict[str, Any], case_id: str | None = None) -> str:
    """The user-defined CMMN model of a DIP, from the structure in the parameter file."""
    case_id = case_id or data["name"]
    root = ET.Element(_c("definitions"), id=f"Definitions_{case_id}", targetNamespace=DIP_NS)
    case = ET.SubElement(root, _c("case"), id=f"Case_{case_id}", name=case_id)
    file_model = ET.SubElement(case, _c("caseFileModel"), id="CaseFile")
    for attr in data["attributes"]:
        ET.SubElement(file_model, _c("caseFileItem"), id=f"CFI_{attr['id']}", name=attr.get("name", attr["id"]))
    plan = ET.SubElement(case, _c("casePlanModel"), id="CasePlan", name=case_id, autoComplete="false")

    stages = {item["id"]: item for item in data["plan_items"] if item.get("kind") == "stage"}
    tasks = [item for item in data["plan_items"] if item["id"] not in stages] + data["attributes"]
    inner: dict[str, list[dict[str, Any]]] = {stage_id: [] for stage_id in stages}
    outer: list[dict[str, Any]] = []
    for task in tasks:
        home = next((pre for pre in task["preceding"] if pre in stages), None)
        (inner[home] if home else outer).append(task)

    def add_task(parent: ET.Element, task: dict[str, Any]) -> None:
        task_id = task["id"]
        item = _plan_item(parent, task_id, f"T_{task_id}", required=task["required"])
        sources = [pre for pre in task["preceding"] if pre not in stages]
        _add_sentry(parent, item, task_id, sources)
        name = task.get("task") or task.get("name") or task_id
        definition = ET.SubElement(parent, _c("humanTask"), id=f"T_{task_id}", name=name)
        if "values" in task:
            extension = ET.SubElement(definition, _c("extensionElements"))
            ET.SubElement(extension, _d("acquires"), attribute=task_id, taskNumber=str(task.get("task_id", "")))

    for stage_id, stage in stages.items():
        _plan_item(plan, stage_id, f"S_{stage_id}", required=stage["required"])
    for task in outer:
        add_task(plan, task)
    _plan_item(plan, DECISION_TASK, f"T_{DECISION_TASK}", required=False)
    definition = ET.SubElement(plan, _c("humanTask"), id=f"T_{DECISION_TASK}", name="Decision-making task")
    extension = ET.SubElement(definition, _c("extensionElements"))
    ET.SubElement(extension, _d("decisionTask"))
    for stage_id, stage in stages.items():
        definition = ET.SubElement(plan, _c("stage"), id=f"S_{stage_id}", name=stage["name"], autoComplete="false")
        for task in inner[stage_id]:
            add_task(definition, task)
    return _serialise(root)


def retrieve_structure(xml_text: str) -> dict[str, dict[str, Any]]:
    """Step 5.2: tasks, stages, precedence and required flags, keyed by id. Fragment items are skipped."""
    root = ET.fromstring(xml_text)
    plan = root.find(f".//{_c('casePlanModel')}")
    if plan is None:
        raise ValueError("no casePlanModel in the CMMN file")
    skip = {DECISION_TASK, REQUEST_RECOMMENDER, INFORMATION_OR_DECISION, MILESTONE_INFORMATION, MILESTONE_DECISION}
    structure: dict[str, dict[str, Any]] = {}

    def strip(reference: str) -> str:
        return reference.removeprefix("PI_")

    def read_stage(stage: ET.Element, enclosing: str | None) -> None:
        definitions = {element.get("id"): element for element in stage if element.get("id")}
        sentries = {element.get("id"): element for element in stage.findall(_c("sentry"))}
        for item in stage.findall(_c("planItem")):
            item_id = item.get("id").removeprefix("PI_")
            definition = definitions.get(item.get("definitionRef"))
            if definition is None:
                raise ValueError(f"plan item {item_id!r} has no definition in its stage")
            is_stage = definition.tag == _c("stage")
            if item_id not in skip:
                preceding = [enclosing] if enclosing else []
                for criterion in item.findall(_c("entryCriterion")):
                    sentry = sentries[criterion.get("sentryRef")]
                    for part in sentry.findall(_c("planItemOnPart")):
                        event = part.findtext(_c("standardEvent"))
                        if event != "complete":
                            raise ValueError(f"{item_id!r}: only 'complete' sentries are supported, got {event!r}")
                        preceding.append(strip(part.get("sourceRef")))
                control = item.find(_c("itemControl"))
                acquires = definition.find(f"{_c('extensionElements')}/{_d('acquires')}")
                structure[item_id] = {
                    "id": item_id,
                    "name": definition.get("name"),
                    "kind": "stage" if is_stage else "task",
                    "acquires": acquires.get("attribute") if acquires is not None else None,
                    "preceding": preceding,
                    "required": control is not None and control.find(_c("requiredRule")) is not None,
                }
            if is_stage:
                read_stage(definition, item_id)

    read_stage(plan, None)
    return structure


def integrate_plan_fragment(user_xml: str) -> str:
    """Section 6.1: insert the process control plan fragment and return the integrated CMMN model."""
    root = ET.fromstring(user_xml)
    plan = root.find(f".//{_c('casePlanModel')}")
    if plan is None:
        raise ValueError("no casePlanModel in the CMMN file")
    if plan.find(f"{_c('planItem')}[@id='PI_{REQUEST_RECOMMENDER}']") is not None:
        raise ValueError("the plan fragment is already integrated")
    decision_item = plan.find(f"{_c('planItem')}[@id='PI_{DECISION_TASK}']")
    if decision_item is None:
        raise ValueError("the user model has no decision-making task")

    _plan_item(plan, REQUEST_RECOMMENDER, f"T_{REQUEST_RECOMMENDER}", manual=False, repeatable=True)
    choose = _plan_item(plan, INFORMATION_OR_DECISION, f"T_{INFORMATION_OR_DECISION}", manual=False, repeatable=True)
    information = _plan_item(plan, MILESTONE_INFORMATION, f"M_{MILESTONE_INFORMATION}", manual=False, repeatable=True)
    decision = _plan_item(plan, MILESTONE_DECISION, f"M_{MILESTONE_DECISION}", manual=False)
    _add_sentry(plan, choose, INFORMATION_OR_DECISION, [REQUEST_RECOMMENDER])
    _add_sentry(plan, information, MILESTONE_INFORMATION, [INFORMATION_OR_DECISION])
    _add_sentry(plan, decision, MILESTONE_DECISION, [INFORMATION_OR_DECISION])
    _add_sentry(plan, decision_item, DECISION_TASK, [MILESTONE_DECISION], event="occur")
    ET.SubElement(plan, _c("processTask"), id=f"T_{REQUEST_RECOMMENDER}", name="Request MDP recommender")
    ET.SubElement(plan, _c("humanTask"), id=f"T_{INFORMATION_OR_DECISION}", name="Information or Decision")
    ET.SubElement(plan, _c("milestone"), id=f"M_{MILESTONE_INFORMATION}", name="Information")
    ET.SubElement(plan, _c("milestone"), id=f"M_{MILESTONE_DECISION}", name="Decision")
    return _serialise(root)


def has_plan_fragment(xml_text: str) -> bool:
    root = ET.fromstring(xml_text)
    ids = {item.get("id") for item in root.iter(_c("planItem"))}
    needed = (REQUEST_RECOMMENDER, INFORMATION_OR_DECISION, MILESTONE_INFORMATION, MILESTONE_DECISION, DECISION_TASK)
    return all(f"PI_{name}" in ids for name in needed)
