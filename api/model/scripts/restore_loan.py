"""
Restore Loan Application system data.

Usage:
    python manage.py shell < scripts/restore_loan.py

Or from inside manage.py shell:
    exec(open('scripts/restore_loan.py').read())
"""

import django
import os

SYSTEM_ID = os.environ.get("LOAN_SYSTEM_ID", "a3000001-0000-5000-8000-000000000000")
SYSTEM_NAME = os.environ.get("LOAN_SYSTEM_NAME", "Loan Application")
PROJECT_ID = "f3d1c958-af29-45b5-82cd-9145f5912423"


def _attr(name, type_):
    return {"name": name, "type": type_, "derived": False, "description": "", "body": None, "enum": None}


def _classifier(id_, name, type_, attributes):
    return {
        "id": id_,
        "project": PROJECT_ID,
        "system": SYSTEM_ID,
        "original_system_id": SYSTEM_ID,
        "data": {
            "name": name,
            "type": type_,
            "leaf": False,
            "abstract": False,
            "namespace": "",
            "methods": [],
            "attributes": attributes,
        },
    }


def _data_classifier(id_, data):
    return {
        "id": id_,
        "project": PROJECT_ID,
        "system": SYSTEM_ID,
        "original_system_id": SYSTEM_ID,
        "data": data,
    }


def _relation(id_, source, target, label, src_mult, tgt_mult, type_="association"):
    return {
        "id": id_,
        "system": SYSTEM_ID,
        "source": source,
        "target": target,
        "data": {
            "type": type_,
            "label": label,
            "labels": None,
            "derived": False,
            "multiplicity": {"source": src_mult, "target": tgt_mult},
            "position_handlers": [],
        },
    }


def _usecase_relation(id_, source, target):
    return _relation(id_, source, target, "uses", "1", "*")


def _controlflow_relation(id_, source, target):
    return {
        "id": id_,
        "system": SYSTEM_ID,
        "source": source,
        "target": target,
        "data": {
            "type": "controlflow",
            "guard": "",
            "weight": "",
            "condition": None,
            "is_directed": True,
            "position_handlers": [],
        },
    }


def _node(id_, cls_id, x, y, diagram):
    return {"id": id_, "diagram": diagram, "cls": cls_id, "data": {"position": {"x": x, "y": y}}}


def _edge(id_, rel_id, diagram):
    return {"id": id_, "diagram": diagram, "rel": rel_id, "data": {}}


def _usecase(id_, name, actors, classes, actions=None, activities=None, pre="", post="", trigger=""):
    return _data_classifier(
        id_,
        {
            "name": name,
            "type": "usecase",
            "namespace": "",
            "precondition": pre,
            "postcondition": post,
            "trigger": trigger,
            "scenarios": [],
            "actors": actors,
            "actions": actions or [],
            "activities": activities or [],
            "classes": classes,
            "application_model": [],
        },
    )


def _action(id_, name, actor_id, actor_name, classes, pre, post, automatic=False):
    return _data_classifier(
        id_,
        {
            "body": "",
            "name": name,
            "page": None,
            "role": "action",
            "type": "action",
            "classes": classes,
            "publish": None,
            "actorNode": actor_id,
            "namespace": "",
            "operation": None,
            "subscribe": None,
            "customCode": None,
            "isAutomatic": automatic,
            "actorNodeName": actor_name,
            "localPrecondition": pre,
            "application_models": None,
            "localPostcondition": post,
        },
    )


def _control(id_, type_):
    data = {"name": None, "type": type_, "role": "control", "activity_scope": "activity"}
    if type_ == "initial":
        data.update({"scheduled": False, "schedule": ""})
    return _data_classifier(id_, data)


def _swimlane_group(id_, lanes):
    return _data_classifier(
        id_,
        {
            "type": "swimlanegroup",
            "height": 1160,
            "width": 340,
            "horizontal": False,
            "swimlanes": [
                {"type": "swimlane", "role": "swimlane", "actorNode": actor_id, "actorNodeName": actor_name}
                for actor_id, actor_name in lanes
            ],
        },
    )


def _section(id_, name, cls_id, layout, attributes, operations=None):
    if operations is None:
        operations = {"create": True, "delete": True, "update": True}
    return {
        "id": id_,
        "name": name,
        "text": "",
        "class": cls_id,
        "primary_model": "",
        "style": {"color": "blue", "radius": "xl", "columns": "1", "density": "normal"},
        "layout": layout,
        "col_span": 12,
        "attributes": [{"enum": None, "name": name, "type": type_, "derived": False} for name, type_ in attributes],
        "operations": operations,
    }


def _page(id_, name, section_refs, single_record=False):
    return {
        "id": id_,
        "name": name,
        "type": {"label": "Normal", "value": "normal"},
        "layout": {"label": "Vertical", "value": "vertical"},
        "gap": {"label": "Normal", "value": "normal"},
        "action": None,
        "category": None,
        "sections": section_refs,
        "single_record": single_record,
    }


APPLICANT_ACTOR = "b3000001-0000-5000-8000-000000000000"
DOCUMENT_ANALYST_ACTOR = "b3000002-0000-5000-8000-000000000000"
LOAN_OFFICER_ACTOR = "b3000003-0000-5000-8000-000000000000"
SYSTEM_ACTOR = "b3000004-0000-5000-8000-000000000000"

APPLICANT_CLASS = "c3000001-0000-5000-8000-000000000000"
LOAN_APPLICATION_CLASS = "c3000002-0000-5000-8000-000000000000"
DOCUMENT_CLASS = "c3000003-0000-5000-8000-000000000000"
APPLICATION_NOTE_CLASS = "c3000004-0000-5000-8000-000000000000"
RISK_ASSESSMENT_CLASS = "c3000005-0000-5000-8000-000000000000"
LOAN_DECISION_CLASS = "c3000006-0000-5000-8000-000000000000"

ACTORS = [
    _classifier(APPLICANT_ACTOR, "Applicant", "actor", []),
    _classifier(DOCUMENT_ANALYST_ACTOR, "Document analyst", "actor", []),
    _classifier(LOAN_OFFICER_ACTOR, "Loan officer", "actor", []),
    _classifier(SYSTEM_ACTOR, "System", "actor", []),
]

CLASSES = [
    _classifier(APPLICANT_CLASS, "Applicant", "class", [
        _attr("applicant_id", "str"), _attr("first_name", "str"), _attr("last_name", "str"),
        _attr("date_of_birth", "datetime"), _attr("credit_score", "int"),
        _attr("email", "str"), _attr("phone", "str"), _attr("address", "str"),
        _attr("employment_status", "str"), _attr("annual_income", "int"),
    ]),
    _classifier(LOAN_APPLICATION_CLASS, "LoanApplication", "class", [
        _attr("application_id", "str"), _attr("loan_amount", "int"), _attr("amount", "int"),
        _attr("requires_additional_documents", "bool"), _attr("approved", "bool"),
        _attr("reason", "str"), _attr("status", "str"), _attr("risk", "str"),
        _attr("submitted_date", "datetime"), _attr("decision_date", "datetime"),
    ]),
    _classifier(DOCUMENT_CLASS, "Document", "class", [
        _attr("document_id", "str"), _attr("file_conent", "str"), _attr("file_content", "str"),
        _attr("document_type", "str"), _attr("upload_date", "datetime"), _attr("valid", "bool"),
    ]),
    _classifier(APPLICATION_NOTE_CLASS, "ApplicationNote", "class", [
        _attr("note_id", "str"), _attr("comment", "str"), _attr("created_at", "datetime"),
        _attr("author_role", "str"), _attr("loan_application_id", "str"),
    ]),
    _classifier(RISK_ASSESSMENT_CLASS, "RiskAssessment", "class", [
        _attr("assessment_id", "str"), _attr("risk_level", "str"), _attr("score", "int"),
        _attr("summary", "str"), _attr("loan_application_id", "str"),
    ]),
    _classifier(LOAN_DECISION_CLASS, "LoanDecision", "class", [
        _attr("decision_id", "str"), _attr("approved", "bool"), _attr("approved_amount", "int"),
        _attr("reason", "str"), _attr("loan_application_id", "str"),
    ]),
]

FILL_APPLICATION_UC = "a3000101-0000-5000-8000-000000000000"
UPLOAD_DOCUMENTS_UC = "a3000102-0000-5000-8000-000000000000"
TRACK_APPLICATIONS_UC = "a3000103-0000-5000-8000-000000000000"
RECEIVE_RESULTS_UC = "a3000104-0000-5000-8000-000000000000"
ANALYZE_DOCUMENTS_UC = "a3000105-0000-5000-8000-000000000000"
REVIEW_APPLICATIONS_UC = "a3000106-0000-5000-8000-000000000000"
ASSESS_RISK_UC = "a3000107-0000-5000-8000-000000000000"
APPROVE_LOAN_UC = "a3000108-0000-5000-8000-000000000000"

LOAN_ACTIVITY_DIAGRAM_ID = "d3000003-0000-5000-8000-000000000000"
LOAN_SWIMLANE_GROUP = "a3000200-0000-5000-8000-000000000000"
LOAN_INITIAL = "a3000201-0000-5000-8000-000000000000"
FILL_APPLICATION_ACTION = "a3000202-0000-5000-8000-000000000000"
UPLOAD_DOCUMENTS_ACTION = "a3000203-0000-5000-8000-000000000000"
SUBMIT_APPLICATION_ACTION = "a3000204-0000-5000-8000-000000000000"
ANALYZE_DOCUMENTS_ACTION = "a3000205-0000-5000-8000-000000000000"
ASSESS_RISK_ACTION = "a3000206-0000-5000-8000-000000000000"
REVIEW_APPLICATION_ACTION = "a3000207-0000-5000-8000-000000000000"
MAKE_DECISION_ACTION = "a3000208-0000-5000-8000-000000000000"
NOTIFY_APPLICANT_ACTION = "a3000209-0000-5000-8000-000000000000"
RECEIVE_RESULTS_ACTION = "a3000210-0000-5000-8000-000000000000"
LOAN_FINAL = "a3000211-0000-5000-8000-000000000000"

USECASES = [
    _usecase(FILL_APPLICATION_UC, "Fill In Loan Application", [APPLICANT_ACTOR],
             [APPLICANT_CLASS, LOAN_APPLICATION_CLASS],
             [FILL_APPLICATION_ACTION, UPLOAD_DOCUMENTS_ACTION, SUBMIT_APPLICATION_ACTION],
             [LOAN_ACTIVITY_DIAGRAM_ID], "Applicant wants financing", "Loan application is submitted"),
    _usecase(UPLOAD_DOCUMENTS_UC, "Upload Documents", [APPLICANT_ACTOR],
             [DOCUMENT_CLASS, LOAN_APPLICATION_CLASS], [UPLOAD_DOCUMENTS_ACTION], [LOAN_ACTIVITY_DIAGRAM_ID]),
    _usecase(TRACK_APPLICATIONS_UC, "Track Applications", [APPLICANT_ACTOR],
             [LOAN_APPLICATION_CLASS, DOCUMENT_CLASS, APPLICATION_NOTE_CLASS]),
    _usecase(RECEIVE_RESULTS_UC, "Receive Application Results", [APPLICANT_ACTOR],
             [LOAN_APPLICATION_CLASS, LOAN_DECISION_CLASS], [RECEIVE_RESULTS_ACTION], [LOAN_ACTIVITY_DIAGRAM_ID]),
    _usecase(ANALYZE_DOCUMENTS_UC, "Analyze Documents", [DOCUMENT_ANALYST_ACTOR],
             [DOCUMENT_CLASS, LOAN_APPLICATION_CLASS, APPLICATION_NOTE_CLASS],
             [ANALYZE_DOCUMENTS_ACTION], [LOAN_ACTIVITY_DIAGRAM_ID]),
    _usecase(REVIEW_APPLICATIONS_UC, "Review Applications", [LOAN_OFFICER_ACTOR],
             [LOAN_APPLICATION_CLASS, APPLICANT_CLASS, DOCUMENT_CLASS, APPLICATION_NOTE_CLASS]),
    _usecase(ASSESS_RISK_UC, "Assess Risk", [LOAN_OFFICER_ACTOR],
             [LOAN_APPLICATION_CLASS, RISK_ASSESSMENT_CLASS], [ASSESS_RISK_ACTION], [LOAN_ACTIVITY_DIAGRAM_ID]),
    _usecase(APPROVE_LOAN_UC, "Approve Or Reject Loan", [LOAN_OFFICER_ACTOR],
             [LOAN_APPLICATION_CLASS, RISK_ASSESSMENT_CLASS, LOAN_DECISION_CLASS],
             [REVIEW_APPLICATION_ACTION, MAKE_DECISION_ACTION], [LOAN_ACTIVITY_DIAGRAM_ID]),
]

ACTIVITY_CLASSIFIERS = [
    _swimlane_group(LOAN_SWIMLANE_GROUP, [
        (APPLICANT_ACTOR, "Applicant"),
        (DOCUMENT_ANALYST_ACTOR, "Document analyst"),
        (LOAN_OFFICER_ACTOR, "Loan officer"),
        (SYSTEM_ACTOR, "System"),
    ]),
    _control(LOAN_INITIAL, "initial"),
    _action(FILL_APPLICATION_ACTION, "Fill In Loan Application", APPLICANT_ACTOR, "Applicant",
            [APPLICANT_CLASS, LOAN_APPLICATION_CLASS], "Applicant starts application", "Application draft is complete"),
    _action(UPLOAD_DOCUMENTS_ACTION, "Upload Documents", APPLICANT_ACTOR, "Applicant",
            [DOCUMENT_CLASS, LOAN_APPLICATION_CLASS], "Application draft exists", "Documents are uploaded"),
    _action(SUBMIT_APPLICATION_ACTION, "Submit Application", APPLICANT_ACTOR, "Applicant",
            [LOAN_APPLICATION_CLASS, DOCUMENT_CLASS], "Required fields and documents are present", "Application is submitted"),
    _action(ANALYZE_DOCUMENTS_ACTION, "Analyze Documents", DOCUMENT_ANALYST_ACTOR, "Document analyst",
            [DOCUMENT_CLASS, LOAN_APPLICATION_CLASS, APPLICATION_NOTE_CLASS], "Submitted application is waiting", "Documents are validated"),
    _action(ASSESS_RISK_ACTION, "Assess Risk", LOAN_OFFICER_ACTOR, "Loan officer",
            [LOAN_APPLICATION_CLASS, RISK_ASSESSMENT_CLASS], "Documents are validated", "Risk assessment is complete"),
    _action(REVIEW_APPLICATION_ACTION, "Review Application", LOAN_OFFICER_ACTOR, "Loan officer",
            [LOAN_APPLICATION_CLASS, APPLICANT_CLASS, DOCUMENT_CLASS], "Risk assessment is complete", "Officer has reviewed the application"),
    _action(MAKE_DECISION_ACTION, "Approve Or Reject Loan", LOAN_OFFICER_ACTOR, "Loan officer",
            [LOAN_APPLICATION_CLASS, RISK_ASSESSMENT_CLASS, LOAN_DECISION_CLASS], "Application is reviewed", "Decision is recorded"),
    _action(NOTIFY_APPLICANT_ACTION, "Notify Applicant", SYSTEM_ACTOR, "System",
            [LOAN_APPLICATION_CLASS, LOAN_DECISION_CLASS], "Decision is recorded", "Applicant is notified", True),
    _action(RECEIVE_RESULTS_ACTION, "Receive Application Results", APPLICANT_ACTOR, "Applicant",
            [LOAN_APPLICATION_CLASS, LOAN_DECISION_CLASS], "Applicant has been notified", "Applicant has seen the result"),
    _control(LOAN_FINAL, "final"),
]

ALL_CLASSIFIERS = ACTORS + CLASSES + USECASES + ACTIVITY_CLASSIFIERS

RELATIONS = [
    _relation("13000001-0000-5000-8000-000000000000", APPLICANT_CLASS, LOAN_APPLICATION_CLASS, "submits", "1", "*"),
    _relation("13000002-0000-5000-8000-000000000000", LOAN_APPLICATION_CLASS, DOCUMENT_CLASS, "has documents", "1", "*", "composition"),
    _relation("13000003-0000-5000-8000-000000000000", LOAN_APPLICATION_CLASS, APPLICATION_NOTE_CLASS, "has notes", "1", "*", "composition"),
    _relation("13000004-0000-5000-8000-000000000000", LOAN_APPLICATION_CLASS, RISK_ASSESSMENT_CLASS, "has assessment", "1", "1", "composition"),
    _relation("13000005-0000-5000-8000-000000000000", LOAN_APPLICATION_CLASS, LOAN_DECISION_CLASS, "has decision", "1", "1", "composition"),
    _usecase_relation("13000101-0000-5000-8000-000000000000", APPLICANT_ACTOR, FILL_APPLICATION_UC),
    _usecase_relation("13000102-0000-5000-8000-000000000000", APPLICANT_ACTOR, UPLOAD_DOCUMENTS_UC),
    _usecase_relation("13000103-0000-5000-8000-000000000000", APPLICANT_ACTOR, TRACK_APPLICATIONS_UC),
    _usecase_relation("13000104-0000-5000-8000-000000000000", APPLICANT_ACTOR, RECEIVE_RESULTS_UC),
    _usecase_relation("13000105-0000-5000-8000-000000000000", DOCUMENT_ANALYST_ACTOR, ANALYZE_DOCUMENTS_UC),
    _usecase_relation("13000106-0000-5000-8000-000000000000", LOAN_OFFICER_ACTOR, REVIEW_APPLICATIONS_UC),
    _usecase_relation("13000107-0000-5000-8000-000000000000", LOAN_OFFICER_ACTOR, ASSESS_RISK_UC),
    _usecase_relation("13000108-0000-5000-8000-000000000000", LOAN_OFFICER_ACTOR, APPROVE_LOAN_UC),
]

FLOW_RELATIONS = [
    _controlflow_relation("13000201-0000-5000-8000-000000000000", LOAN_INITIAL, FILL_APPLICATION_ACTION),
    _controlflow_relation("13000202-0000-5000-8000-000000000000", FILL_APPLICATION_ACTION, UPLOAD_DOCUMENTS_ACTION),
    _controlflow_relation("13000203-0000-5000-8000-000000000000", UPLOAD_DOCUMENTS_ACTION, SUBMIT_APPLICATION_ACTION),
    _controlflow_relation("13000204-0000-5000-8000-000000000000", SUBMIT_APPLICATION_ACTION, ANALYZE_DOCUMENTS_ACTION),
    _controlflow_relation("13000205-0000-5000-8000-000000000000", ANALYZE_DOCUMENTS_ACTION, ASSESS_RISK_ACTION),
    _controlflow_relation("13000206-0000-5000-8000-000000000000", ASSESS_RISK_ACTION, REVIEW_APPLICATION_ACTION),
    _controlflow_relation("13000207-0000-5000-8000-000000000000", REVIEW_APPLICATION_ACTION, MAKE_DECISION_ACTION),
    _controlflow_relation("13000208-0000-5000-8000-000000000000", MAKE_DECISION_ACTION, NOTIFY_APPLICANT_ACTION),
    _controlflow_relation("13000209-0000-5000-8000-000000000000", NOTIFY_APPLICANT_ACTION, RECEIVE_RESULTS_ACTION),
    _controlflow_relation("13000210-0000-5000-8000-000000000000", RECEIVE_RESULTS_ACTION, LOAN_FINAL),
]
RELATIONS.extend(FLOW_RELATIONS)

CLASS_DIAGRAM_ID = "d3000001-0000-5000-8000-000000000000"
USECASE_DIAGRAM_ID = "d3000002-0000-5000-8000-000000000000"

CLASS_NODES = [
    _node("f3000001-0000-5000-8000-000000000000", APPLICANT_CLASS, 40, 80, CLASS_DIAGRAM_ID),
    _node("f3000002-0000-5000-8000-000000000000", LOAN_APPLICATION_CLASS, 420, 80, CLASS_DIAGRAM_ID),
    _node("f3000003-0000-5000-8000-000000000000", DOCUMENT_CLASS, 800, 40, CLASS_DIAGRAM_ID),
    _node("f3000004-0000-5000-8000-000000000000", APPLICATION_NOTE_CLASS, 800, 240, CLASS_DIAGRAM_ID),
    _node("f3000005-0000-5000-8000-000000000000", RISK_ASSESSMENT_CLASS, 420, 340, CLASS_DIAGRAM_ID),
    _node("f3000006-0000-5000-8000-000000000000", LOAN_DECISION_CLASS, 800, 440, CLASS_DIAGRAM_ID),
]
CLASS_EDGES = [_edge(f"e30000{i:02d}-0000-5000-8000-000000000000", rel["id"], CLASS_DIAGRAM_ID) for i, rel in enumerate(RELATIONS[:5], 1)]

USECASE_NODE_POSITIONS = [
    ("f3000101-0000-5000-8000-000000000000", APPLICANT_ACTOR, -160, 180),
    ("f3000102-0000-5000-8000-000000000000", DOCUMENT_ANALYST_ACTOR, 860, 180),
    ("f3000103-0000-5000-8000-000000000000", LOAN_OFFICER_ACTOR, 860, 440),
    ("f3000111-0000-5000-8000-000000000000", FILL_APPLICATION_UC, 180, 40),
    ("f3000112-0000-5000-8000-000000000000", UPLOAD_DOCUMENTS_UC, 180, 180),
    ("f3000113-0000-5000-8000-000000000000", TRACK_APPLICATIONS_UC, 180, 320),
    ("f3000114-0000-5000-8000-000000000000", RECEIVE_RESULTS_UC, 180, 460),
    ("f3000115-0000-5000-8000-000000000000", ANALYZE_DOCUMENTS_UC, 520, 180),
    ("f3000116-0000-5000-8000-000000000000", REVIEW_APPLICATIONS_UC, 520, 320),
    ("f3000117-0000-5000-8000-000000000000", ASSESS_RISK_UC, 520, 460),
    ("f3000118-0000-5000-8000-000000000000", APPROVE_LOAN_UC, 520, 600),
]
USECASE_NODES = [_node(nid, cls_id, x, y, USECASE_DIAGRAM_ID) for nid, cls_id, x, y in USECASE_NODE_POSITIONS]
USECASE_EDGES = [_edge(f"e30001{i:02d}-0000-5000-8000-000000000000", rel["id"], USECASE_DIAGRAM_ID) for i, rel in enumerate(RELATIONS[5:13], 1)]

ACTIVITY_NODE_POSITIONS = [
    ("f3000200-0000-5000-8000-000000000000", LOAN_SWIMLANE_GROUP, -160, -120),
    ("f3000201-0000-5000-8000-000000000000", LOAN_INITIAL, 60, 0),
    ("f3000202-0000-5000-8000-000000000000", FILL_APPLICATION_ACTION, 60, 140),
    ("f3000203-0000-5000-8000-000000000000", UPLOAD_DOCUMENTS_ACTION, 60, 280),
    ("f3000204-0000-5000-8000-000000000000", SUBMIT_APPLICATION_ACTION, 60, 420),
    ("f3000205-0000-5000-8000-000000000000", ANALYZE_DOCUMENTS_ACTION, 420, 560),
    ("f3000206-0000-5000-8000-000000000000", ASSESS_RISK_ACTION, 780, 700),
    ("f3000207-0000-5000-8000-000000000000", REVIEW_APPLICATION_ACTION, 780, 840),
    ("f3000208-0000-5000-8000-000000000000", MAKE_DECISION_ACTION, 780, 980),
    ("f3000209-0000-5000-8000-000000000000", NOTIFY_APPLICANT_ACTION, 1140, 980),
    ("f3000210-0000-5000-8000-000000000000", RECEIVE_RESULTS_ACTION, 60, 980),
    ("f3000211-0000-5000-8000-000000000000", LOAN_FINAL, 60, 1120),
]
ACTIVITY_NODES = [_node(nid, cls_id, x, y, LOAN_ACTIVITY_DIAGRAM_ID) for nid, cls_id, x, y in ACTIVITY_NODE_POSITIONS]
ACTIVITY_EDGES = [_edge(f"e30002{i:02d}-0000-5000-8000-000000000000", rel["id"], LOAN_ACTIVITY_DIAGRAM_ID) for i, rel in enumerate(FLOW_RELATIONS, 1)]

DIAGRAMS = [
    {"id": CLASS_DIAGRAM_ID, "type": "classes", "name": "Loan Application Domain Model",
     "description": "Applicants, loan applications, documents, risk assessments, and decisions",
     "system": SYSTEM_ID, "nodes": CLASS_NODES, "edges": CLASS_EDGES},
    {"id": USECASE_DIAGRAM_ID, "type": "usecase", "name": "Loan Application Use Cases",
     "description": "Applicant, document analyst, and loan officer use cases",
     "system": SYSTEM_ID, "nodes": USECASE_NODES, "edges": USECASE_EDGES},
    {"id": LOAN_ACTIVITY_DIAGRAM_ID, "type": "activity", "name": "Loan Application Review Flow",
     "description": "End-to-end application review workflow with all swimlanes",
     "system": SYSTEM_ID, "nodes": ACTIVITY_NODES, "edges": ACTIVITY_EDGES},
]

_applicant_sections = [
    _section("s3000001-0000-5000-8000-000000000000", "Loan Applications", LOAN_APPLICATION_CLASS, "list",
             [("application_id", "str"), ("loan_amount", "int"), ("status", "str"), ("risk", "str"), ("submitted_date", "datetime")],
             {"create": True, "delete": False, "update": True}),
    _section("s3000002-0000-5000-8000-000000000000", "Upload Documents", DOCUMENT_CLASS, "detail",
             [("file_conent", "str"), ("document_type", "str"), ("upload_date", "datetime")],
             {"create": True, "delete": True, "update": True}),
    _section("s3000003-0000-5000-8000-000000000000", "Application Results", LOAN_DECISION_CLASS, "detail",
             [("approved", "bool"), ("approved_amount", "int"), ("reason", "str")],
             {"create": False, "delete": False, "update": False}),
]
_applicant_pages = [
    _page("p3000001-0000-5000-8000-000000000000", "Track Applications", [{"label": "Loan Applications", "value": "s3000001-0000-5000-8000-000000000000"}]),
    _page("p3000002-0000-5000-8000-000000000000", "Fill In Loan Application", [{"label": "Loan Applications", "value": "s3000001-0000-5000-8000-000000000000"}, {"label": "Upload Documents", "value": "s3000002-0000-5000-8000-000000000000"}]),
    _page("p3000003-0000-5000-8000-000000000000", "Receive Application Results", [{"label": "Application Results", "value": "s3000003-0000-5000-8000-000000000000"}]),
]

_analyst_sections = [
    _section("s3000004-0000-5000-8000-000000000000", "Documents To Analyze", DOCUMENT_CLASS, "list",
             [("document_id", "str"), ("document_type", "str"), ("upload_date", "datetime"), ("valid", "bool")],
             {"create": False, "delete": False, "update": True}),
    _section("s3000005-0000-5000-8000-000000000000", "Analysis Notes", APPLICATION_NOTE_CLASS, "detail",
             [("comment", "str"), ("created_at", "datetime"), ("author_role", "str")],
             {"create": True, "delete": False, "update": True}),
]
_analyst_pages = [
    _page("p3000004-0000-5000-8000-000000000000", "Document Workflow", [{"label": "Documents To Analyze", "value": "s3000004-0000-5000-8000-000000000000"}, {"label": "Analysis Notes", "value": "s3000005-0000-5000-8000-000000000000"}]),
]

_officer_sections = [
    _section("s3000006-0000-5000-8000-000000000000", "Applications To Review", LOAN_APPLICATION_CLASS, "list",
             [("application_id", "str"), ("loan_amount", "int"), ("status", "str"), ("risk", "str"), ("submitted_date", "datetime")],
             {"create": False, "delete": False, "update": True}),
    _section("s3000007-0000-5000-8000-000000000000", "Risk Assessment", RISK_ASSESSMENT_CLASS, "detail",
             [("risk_level", "str"), ("score", "int"), ("summary", "str")],
             {"create": True, "delete": False, "update": True}),
    _section("s3000008-0000-5000-8000-000000000000", "Loan Decision", LOAN_DECISION_CLASS, "detail",
             [("approved", "bool"), ("approved_amount", "int"), ("reason", "str")],
             {"create": True, "delete": False, "update": True}),
]
_officer_pages = [
    _page("p3000005-0000-5000-8000-000000000000", "Review Applications", [{"label": "Applications To Review", "value": "s3000006-0000-5000-8000-000000000000"}]),
    _page("p3000006-0000-5000-8000-000000000000", "Assess Risk", [{"label": "Applications To Review", "value": "s3000006-0000-5000-8000-000000000000"}, {"label": "Risk Assessment", "value": "s3000007-0000-5000-8000-000000000000"}]),
    _page("p3000007-0000-5000-8000-000000000000", "Approve Or Reject Loan", [{"label": "Applications To Review", "value": "s3000006-0000-5000-8000-000000000000"}, {"label": "Loan Decision", "value": "s3000008-0000-5000-8000-000000000000"}]),
]

def _interface(id_, name, actor, pages, sections):
    return {
        "id": id_,
        "name": name,
        "description": f"{name} loan application portal",
        "system": SYSTEM_ID,
        "actor": actor,
        "data": {
            "pages": pages,
            "sections": sections,
            "styling": {"radius": 0, "textColor": "#000000", "accentColor": "#F5F5F4", "selectedStyle": "modern", "backgroundColor": "#FFFFFF"},
            "settings": {},
            "categories": [],
        },
    }

INTERFACES = [
    _interface("ab300001-0000-5000-8000-000000000000", "Applicant", APPLICANT_ACTOR, _applicant_pages, _applicant_sections),
    _interface("ab300002-0000-5000-8000-000000000000", "Document analyst", DOCUMENT_ANALYST_ACTOR, _analyst_pages, _analyst_sections),
    _interface("ab300003-0000-5000-8000-000000000000", "Loan officer", LOAN_OFFICER_ACTOR, _officer_pages, _officer_sections),
]

loan_data = {
    "id": SYSTEM_ID,
    "project": PROJECT_ID,
    "name": SYSTEM_NAME,
    "description": "Loan application processing system",
    "classifiers": ALL_CLASSIFIERS,
    "imported_classifiers": [],
    "relations": RELATIONS,
    "diagrams": DIAGRAMS,
    "interfaces": INTERFACES,
}

from metadata.models import System

print("Importing Loan Application system...")
system = System.import_from_json(loan_data)
print(f"Loan Application system restored successfully: {system.id} - {system.name}")
