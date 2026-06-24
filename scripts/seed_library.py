"""
Seed Library Management System (图书管理系统) data.

Creates a project with one system and three diagrams:
  - Class diagram (5 classes)
  - Usecase diagram (2 actors, 6 usecases)
  - Activity diagram (borrowing workflow with swimlanes)

Usage:
    python manage.py shell < scripts/seed_library.py
"""

# ---------------------------------------------------------------------------
# IDs
# ---------------------------------------------------------------------------

PROJECT_ID           = "44000001-0000-5000-8000-000000000000"
SYSTEM_ID            = "44000002-0000-5000-8000-000000000000"
DIAGRAM_CLASS_ID     = "44000003-0000-5000-8000-000000000000"
DIAGRAM_USECASE_ID   = "44000004-0000-5000-8000-000000000000"
DIAGRAM_ACTIVITY_ID  = "44000005-0000-5000-8000-000000000000"
SYSTEM_NAME          = "Library Management System"

# Actors
ACTOR_READER_ID      = "44100001-0000-5000-8000-000000000000"
ACTOR_LIBRARIAN_ID   = "44100002-0000-5000-8000-000000000000"

# Classes
CLS_BOOK_ID          = "44200001-0000-5000-8000-000000000000"
CLS_MEMBER_ID        = "44200002-0000-5000-8000-000000000000"
CLS_LOAN_ID          = "44200003-0000-5000-8000-000000000000"
CLS_AUTHOR_ID        = "44200004-0000-5000-8000-000000000000"
CLS_CATEGORY_ID      = "44200005-0000-5000-8000-000000000000"

# Usecases + boundary
UC_BOUNDARY_ID       = "44300000-0000-5000-8000-000000000000"
UC_SEARCH_ID         = "44300001-0000-5000-8000-000000000000"
UC_BORROW_ID         = "44300002-0000-5000-8000-000000000000"
UC_RETURN_ID         = "44300003-0000-5000-8000-000000000000"
UC_RENEW_ID          = "44300004-0000-5000-8000-000000000000"
UC_MGT_MEMBERS_ID    = "44300005-0000-5000-8000-000000000000"
UC_MGT_BOOKS_ID      = "44300006-0000-5000-8000-000000000000"

# Class diagram relations
REL_LOAN_BOOK_ID     = "44400001-0000-5000-8000-000000000000"
REL_LOAN_MEMBER_ID   = "44400002-0000-5000-8000-000000000000"
REL_BOOK_AUTHOR_ID   = "44400003-0000-5000-8000-000000000000"
REL_BOOK_CAT_ID      = "44400004-0000-5000-8000-000000000000"

# Usecase diagram relations
REL_R_SEARCH_ID      = "44500001-0000-5000-8000-000000000000"
REL_R_BORROW_ID      = "44500002-0000-5000-8000-000000000000"
REL_R_RETURN_ID      = "44500003-0000-5000-8000-000000000000"
REL_R_RENEW_ID       = "44500004-0000-5000-8000-000000000000"
REL_L_MGT_MEM_ID     = "44500005-0000-5000-8000-000000000000"
REL_L_MGT_BOOK_ID    = "44500006-0000-5000-8000-000000000000"
REL_L_SEARCH_ID      = "44500007-0000-5000-8000-000000000000"

# Activity classifiers
ACT_SWG_ID           = "44600000-0000-5000-8000-000000000000"  # swimlanegroup
ACT_INITIAL_ID       = "44600001-0000-5000-8000-000000000000"
ACT_SEARCH_ID        = "44600002-0000-5000-8000-000000000000"  # action
ACT_CHECK_ID         = "44600003-0000-5000-8000-000000000000"  # action (auto)
ACT_DECISION_ID      = "44600004-0000-5000-8000-000000000000"  # decision
ACT_CREATE_LOAN_ID   = "44600005-0000-5000-8000-000000000000"  # action
ACT_UPDATE_BOOK_ID   = "44600006-0000-5000-8000-000000000000"  # action (auto)
ACT_SUCCESS_ID       = "44600007-0000-5000-8000-000000000000"  # final
ACT_NOT_AVAIL_ID     = "44600008-0000-5000-8000-000000000000"  # action
ACT_FAIL_FINAL_ID    = "44600009-0000-5000-8000-000000000000"  # final

# Activity controlflow relations
CF_INIT_SEARCH_ID    = "44700001-0000-5000-8000-000000000000"
CF_SEARCH_CHECK_ID   = "44700002-0000-5000-8000-000000000000"
CF_CHECK_DEC_ID      = "44700003-0000-5000-8000-000000000000"
CF_DEC_CREATE_ID     = "44700004-0000-5000-8000-000000000000"
CF_CREATE_UPDATE_ID  = "44700005-0000-5000-8000-000000000000"
CF_UPDATE_SUCC_ID    = "44700006-0000-5000-8000-000000000000"
CF_DEC_NOTAVAIL_ID   = "44700007-0000-5000-8000-000000000000"
CF_NOTAVAIL_FAIL_ID  = "44700008-0000-5000-8000-000000000000"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _attr(name, type_):
    return {"name": name, "type": type_, "derived": False, "description": "", "body": None, "enum": None}


def _cls(id_, name, attributes):
    return {
        "id": id_,
        "project": PROJECT_ID,
        "system": SYSTEM_ID,
        "original_system_id": SYSTEM_ID,
        "data": {
            "name": name,
            "type": "class",
            "leaf": False,
            "abstract": False,
            "namespace": "",
            "methods": [],
            "attributes": attributes,
        },
    }


def _dc(id_, data):
    """Raw data classifier (non-class types)."""
    return {"id": id_, "project": PROJECT_ID, "system": SYSTEM_ID, "original_system_id": SYSTEM_ID, "data": data}


def _actor(id_, name):
    return _dc(id_, {"name": name, "type": "actor"})


def _usecase(id_, name, classes=None, pre="", post=""):
    return _dc(id_, {
        "name": name,
        "type": "usecase",
        "namespace": "",
        "precondition": pre,
        "postcondition": post,
        "trigger": "",
        "scenarios": [],
        "activities": [],
        "actions": [],
        "classes": classes or [],
        "application_model": [],
    })


def _boundary(id_, name):
    return _dc(id_, {"name": name, "type": "system_boundary", "height": 800, "width": 600})


def _action(id_, name, actor_id, actor_name, cls_input=None, cls_output=None, automatic=False, pre="", post=""):
    return _dc(id_, {
        "body": "",
        "name": name,
        "page": None,
        "role": "action",
        "type": "action",
        "classes": {"input": cls_input or [], "output": cls_output or []},
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
    })


def _control(id_, type_):
    data = {"name": None, "type": type_, "role": "control", "activity_scope": "activity"}
    if type_ == "initial":
        data.update({"scheduled": False, "schedule": ""})
    return _dc(id_, data)


def _decision(id_):
    return _dc(id_, {"type": "decision", "role": "control", "decisionInput": "", "decisionInputFlow": "", "page": ""})


def _swimlane_group(id_, lanes):
    return _dc(id_, {
        "type": "swimlanegroup",
        "height": 800,
        "width": 320,
        "horizontal": False,
        "swimlanes": lanes,
    })


def _swimlane(actor_id, actor_name):
    return {"type": "swimlane", "role": "swimlane", "actorNode": actor_id, "actorNodeName": actor_name}


def _assoc(id_, source, target, label, src_mult="1", tgt_mult="*"):
    return {
        "id": id_,
        "system": SYSTEM_ID,
        "source": source,
        "target": target,
        "data": {
            "type": "association",
            "label": label,
            "labels": None,
            "derived": False,
            "multiplicity": {"source": src_mult, "target": tgt_mult},
            "position_handlers": [],
        },
    }


def _interaction(id_, source, target):
    return {
        "id": id_,
        "system": SYSTEM_ID,
        "source": source,
        "target": target,
        "data": {"type": "interaction", "position_handlers": []},
    }


def _controlflow(id_, source, target, guard=""):
    return {
        "id": id_,
        "system": SYSTEM_ID,
        "source": source,
        "target": target,
        "data": {"type": "controlflow", "guard": guard, "weight": "", "condition": None, "is_directed": True, "position_handlers": []},
    }


def _node(id_, cls_id, x, y, diagram):
    return {"id": id_, "diagram": diagram, "cls": cls_id, "data": {"position": {"x": x, "y": y}}}


def _edge(id_, rel_id, diagram):
    return {"id": id_, "diagram": diagram, "rel": rel_id, "data": {}}


# ---------------------------------------------------------------------------
# Classifiers
# ---------------------------------------------------------------------------

CLASSIFIERS = [
    # Actors
    _actor(ACTOR_READER_ID, "Reader"),
    _actor(ACTOR_LIBRARIAN_ID, "Librarian"),

    # Domain classes
    _cls(CLS_BOOK_ID, "Book", [
        _attr("isbn", "str"),
        _attr("title", "str"),
        _attr("publisher", "str"),
        _attr("year", "int"),
        _attr("copies_total", "int"),
        _attr("copies_available", "int"),
    ]),
    _cls(CLS_MEMBER_ID, "Member", [
        _attr("member_id", "str"),
        _attr("name", "str"),
        _attr("email", "str"),
        _attr("phone", "str"),
        _attr("registered_at", "str"),
        _attr("is_active", "bool"),
    ]),
    _cls(CLS_LOAN_ID, "Loan", [
        _attr("loan_id", "str"),
        _attr("loan_date", "str"),
        _attr("due_date", "str"),
        _attr("return_date", "str"),
        _attr("status", "str"),
        _attr("renewed_count", "int"),
    ]),
    _cls(CLS_AUTHOR_ID, "Author", [
        _attr("author_id", "str"),
        _attr("name", "str"),
        _attr("bio", "str"),
    ]),
    _cls(CLS_CATEGORY_ID, "Category", [
        _attr("category_id", "str"),
        _attr("name", "str"),
        _attr("description", "str"),
    ]),

    # Usecases
    _boundary(UC_BOUNDARY_ID, SYSTEM_NAME),
    _usecase(UC_SEARCH_ID,      "Search Books",    [CLS_BOOK_ID]),
    _usecase(UC_BORROW_ID,      "Borrow Book",     [CLS_BOOK_ID, CLS_LOAN_ID]),
    _usecase(UC_RETURN_ID,      "Return Book",     [CLS_LOAN_ID]),
    _usecase(UC_RENEW_ID,       "Renew Book",      [CLS_LOAN_ID]),
    _usecase(UC_MGT_MEMBERS_ID, "Manage Members",  [CLS_MEMBER_ID]),
    _usecase(UC_MGT_BOOKS_ID,   "Manage Books",    [CLS_BOOK_ID, CLS_AUTHOR_ID, CLS_CATEGORY_ID]),

    # Activity classifiers
    _swimlane_group(ACT_SWG_ID, [
        _swimlane(ACTOR_READER_ID,    "Reader"),
        _swimlane(ACTOR_LIBRARIAN_ID, "Librarian"),
    ]),
    _control(ACT_INITIAL_ID, "initial"),
    _action(ACT_SEARCH_ID,    "Search Books",       ACTOR_READER_ID,    "Reader",
            cls_input=[],  cls_output=[CLS_BOOK_ID]),
    _action(ACT_CHECK_ID,     "Check Availability", ACTOR_LIBRARIAN_ID, "Librarian",
            cls_input=[CLS_BOOK_ID], automatic=True),
    _decision(ACT_DECISION_ID),
    _action(ACT_CREATE_LOAN_ID, "Create Loan Record", ACTOR_LIBRARIAN_ID, "Librarian",
            cls_input=[CLS_BOOK_ID, CLS_MEMBER_ID], cls_output=[CLS_LOAN_ID]),
    _action(ACT_UPDATE_BOOK_ID, "Update Book Status",  ACTOR_LIBRARIAN_ID, "Librarian",
            cls_input=[CLS_LOAN_ID], automatic=True),
    _control(ACT_SUCCESS_ID,  "final"),
    _action(ACT_NOT_AVAIL_ID, "Notify Unavailable", ACTOR_LIBRARIAN_ID, "Librarian",
            cls_input=[CLS_BOOK_ID], automatic=True),
    _control(ACT_FAIL_FINAL_ID, "final"),
]

# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------

RELATIONS = [
    # Class diagram
    _assoc(REL_LOAN_BOOK_ID,   CLS_LOAN_ID,   CLS_BOOK_ID,     "borrows",      "1", "1"),
    _assoc(REL_LOAN_MEMBER_ID, CLS_LOAN_ID,   CLS_MEMBER_ID,   "belongs to",   "*", "1"),
    _assoc(REL_BOOK_AUTHOR_ID, CLS_BOOK_ID,   CLS_AUTHOR_ID,   "written by",   "*", "*"),
    _assoc(REL_BOOK_CAT_ID,    CLS_BOOK_ID,   CLS_CATEGORY_ID, "categorized",  "*", "1"),

    # Usecase diagram — reader interactions
    _interaction(REL_R_SEARCH_ID, ACTOR_READER_ID, UC_SEARCH_ID),
    _interaction(REL_R_BORROW_ID, ACTOR_READER_ID, UC_BORROW_ID),
    _interaction(REL_R_RETURN_ID, ACTOR_READER_ID, UC_RETURN_ID),
    _interaction(REL_R_RENEW_ID,  ACTOR_READER_ID, UC_RENEW_ID),
    # Usecase diagram — librarian interactions
    _interaction(REL_L_MGT_MEM_ID,  ACTOR_LIBRARIAN_ID, UC_MGT_MEMBERS_ID),
    _interaction(REL_L_MGT_BOOK_ID, ACTOR_LIBRARIAN_ID, UC_MGT_BOOKS_ID),
    _interaction(REL_L_SEARCH_ID,   ACTOR_LIBRARIAN_ID, UC_SEARCH_ID),

    # Activity diagram — control flows
    _controlflow(CF_INIT_SEARCH_ID,   ACT_INITIAL_ID,    ACT_SEARCH_ID),
    _controlflow(CF_SEARCH_CHECK_ID,  ACT_SEARCH_ID,     ACT_CHECK_ID),
    _controlflow(CF_CHECK_DEC_ID,     ACT_CHECK_ID,      ACT_DECISION_ID),
    _controlflow(CF_DEC_CREATE_ID,    ACT_DECISION_ID,   ACT_CREATE_LOAN_ID,  guard="[available]"),
    _controlflow(CF_CREATE_UPDATE_ID, ACT_CREATE_LOAN_ID, ACT_UPDATE_BOOK_ID),
    _controlflow(CF_UPDATE_SUCC_ID,   ACT_UPDATE_BOOK_ID, ACT_SUCCESS_ID),
    _controlflow(CF_DEC_NOTAVAIL_ID,  ACT_DECISION_ID,   ACT_NOT_AVAIL_ID,   guard="[unavailable]"),
    _controlflow(CF_NOTAVAIL_FAIL_ID, ACT_NOT_AVAIL_ID,  ACT_FAIL_FINAL_ID),
]

# ---------------------------------------------------------------------------
# Diagrams
# ---------------------------------------------------------------------------

# --- Class diagram nodes & edges ---
N = lambda id_, cls_id, x, y, diag: _node(id_, cls_id, x, y, diag)
E = lambda id_, rel_id, diag: _edge(id_, rel_id, diag)

CLASS_NODES = [
    N("44800001-0000-5000-8000-000000000000", CLS_BOOK_ID,      200, 300, DIAGRAM_CLASS_ID),
    N("44800002-0000-5000-8000-000000000000", CLS_MEMBER_ID,    550, 300, DIAGRAM_CLASS_ID),
    N("44800003-0000-5000-8000-000000000000", CLS_LOAN_ID,      370, 500, DIAGRAM_CLASS_ID),
    N("44800004-0000-5000-8000-000000000000", CLS_AUTHOR_ID,    100,  80, DIAGRAM_CLASS_ID),
    N("44800005-0000-5000-8000-000000000000", CLS_CATEGORY_ID,  550,  80, DIAGRAM_CLASS_ID),
]

CLASS_EDGES = [
    E("44900001-0000-5000-8000-000000000000", REL_LOAN_BOOK_ID,   DIAGRAM_CLASS_ID),
    E("44900002-0000-5000-8000-000000000000", REL_LOAN_MEMBER_ID, DIAGRAM_CLASS_ID),
    E("44900003-0000-5000-8000-000000000000", REL_BOOK_AUTHOR_ID, DIAGRAM_CLASS_ID),
    E("44900004-0000-5000-8000-000000000000", REL_BOOK_CAT_ID,    DIAGRAM_CLASS_ID),
]

# --- Usecase diagram nodes & edges ---
USECASE_NODES = [
    N("44a00001-0000-5000-8000-000000000000", ACTOR_READER_ID,    50,  350, DIAGRAM_USECASE_ID),
    N("44a00002-0000-5000-8000-000000000000", ACTOR_LIBRARIAN_ID, 730, 300, DIAGRAM_USECASE_ID),
    N("44a00003-0000-5000-8000-000000000000", UC_BOUNDARY_ID,     250, 200, DIAGRAM_USECASE_ID),
    N("44a00004-0000-5000-8000-000000000000", UC_SEARCH_ID,       380, 100, DIAGRAM_USECASE_ID),
    N("44a00005-0000-5000-8000-000000000000", UC_BORROW_ID,       380, 210, DIAGRAM_USECASE_ID),
    N("44a00006-0000-5000-8000-000000000000", UC_RETURN_ID,       380, 320, DIAGRAM_USECASE_ID),
    N("44a00007-0000-5000-8000-000000000000", UC_RENEW_ID,        380, 430, DIAGRAM_USECASE_ID),
    N("44a00008-0000-5000-8000-000000000000", UC_MGT_MEMBERS_ID,  560, 200, DIAGRAM_USECASE_ID),
    N("44a00009-0000-5000-8000-000000000000", UC_MGT_BOOKS_ID,    560, 360, DIAGRAM_USECASE_ID),
]

USECASE_EDGES = [
    E("44b00001-0000-5000-8000-000000000000", REL_R_SEARCH_ID,     DIAGRAM_USECASE_ID),
    E("44b00002-0000-5000-8000-000000000000", REL_R_BORROW_ID,     DIAGRAM_USECASE_ID),
    E("44b00003-0000-5000-8000-000000000000", REL_R_RETURN_ID,     DIAGRAM_USECASE_ID),
    E("44b00004-0000-5000-8000-000000000000", REL_R_RENEW_ID,      DIAGRAM_USECASE_ID),
    E("44b00005-0000-5000-8000-000000000000", REL_L_MGT_MEM_ID,    DIAGRAM_USECASE_ID),
    E("44b00006-0000-5000-8000-000000000000", REL_L_MGT_BOOK_ID,   DIAGRAM_USECASE_ID),
    E("44b00007-0000-5000-8000-000000000000", REL_L_SEARCH_ID,     DIAGRAM_USECASE_ID),
]

# --- Activity diagram nodes & edges ---
# Swimlane: Reader x=0-320, Librarian x=320-640
ACTIVITY_NODES = [
    N("44c00000-0000-5000-8000-000000000000", ACT_SWG_ID,        0,   0,   DIAGRAM_ACTIVITY_ID),
    N("44c00001-0000-5000-8000-000000000000", ACT_INITIAL_ID,    160,  60,  DIAGRAM_ACTIVITY_ID),
    N("44c00002-0000-5000-8000-000000000000", ACT_SEARCH_ID,     160, 180,  DIAGRAM_ACTIVITY_ID),
    N("44c00003-0000-5000-8000-000000000000", ACT_CHECK_ID,      480, 300,  DIAGRAM_ACTIVITY_ID),
    N("44c00004-0000-5000-8000-000000000000", ACT_DECISION_ID,   320, 420,  DIAGRAM_ACTIVITY_ID),
    N("44c00005-0000-5000-8000-000000000000", ACT_CREATE_LOAN_ID, 480, 540, DIAGRAM_ACTIVITY_ID),
    N("44c00006-0000-5000-8000-000000000000", ACT_UPDATE_BOOK_ID, 480, 660, DIAGRAM_ACTIVITY_ID),
    N("44c00007-0000-5000-8000-000000000000", ACT_SUCCESS_ID,    320, 780,  DIAGRAM_ACTIVITY_ID),
    N("44c00008-0000-5000-8000-000000000000", ACT_NOT_AVAIL_ID,  160, 540,  DIAGRAM_ACTIVITY_ID),
    N("44c00009-0000-5000-8000-000000000000", ACT_FAIL_FINAL_ID, 160, 680,  DIAGRAM_ACTIVITY_ID),
]

ACTIVITY_EDGES = [
    E("44d00001-0000-5000-8000-000000000000", CF_INIT_SEARCH_ID,   DIAGRAM_ACTIVITY_ID),
    E("44d00002-0000-5000-8000-000000000000", CF_SEARCH_CHECK_ID,  DIAGRAM_ACTIVITY_ID),
    E("44d00003-0000-5000-8000-000000000000", CF_CHECK_DEC_ID,     DIAGRAM_ACTIVITY_ID),
    E("44d00004-0000-5000-8000-000000000000", CF_DEC_CREATE_ID,    DIAGRAM_ACTIVITY_ID),
    E("44d00005-0000-5000-8000-000000000000", CF_CREATE_UPDATE_ID, DIAGRAM_ACTIVITY_ID),
    E("44d00006-0000-5000-8000-000000000000", CF_UPDATE_SUCC_ID,   DIAGRAM_ACTIVITY_ID),
    E("44d00007-0000-5000-8000-000000000000", CF_DEC_NOTAVAIL_ID,  DIAGRAM_ACTIVITY_ID),
    E("44d00008-0000-5000-8000-000000000000", CF_NOTAVAIL_FAIL_ID, DIAGRAM_ACTIVITY_ID),
]

DIAGRAMS = [
    {
        "id": DIAGRAM_CLASS_ID,
        "name": "Class Diagram",
        "description": f"{SYSTEM_NAME} class diagram",
        "type": "classes",
        "system": SYSTEM_ID,
        "nodes": CLASS_NODES,
        "edges": CLASS_EDGES,
    },
    {
        "id": DIAGRAM_USECASE_ID,
        "name": "Use Case Diagram",
        "description": f"{SYSTEM_NAME} use case diagram",
        "type": "usecase",
        "system": SYSTEM_ID,
        "nodes": USECASE_NODES,
        "edges": USECASE_EDGES,
    },
    {
        "id": DIAGRAM_ACTIVITY_ID,
        "name": "Activity Diagram (Borrowing)",
        "description": "Book borrowing workflow",
        "type": "activity",
        "system": SYSTEM_ID,
        "nodes": ACTIVITY_NODES,
        "edges": ACTIVITY_EDGES,
    },
]

# ---------------------------------------------------------------------------
# Project payload
# ---------------------------------------------------------------------------

PROJECT_DATA = {
    "id": PROJECT_ID,
    "name": SYSTEM_NAME,
    "description": f"{SYSTEM_NAME} — seed data",
    "systems": [
        {
            "id": SYSTEM_ID,
            "name": SYSTEM_NAME,
            "description": "Core library system",
            "project": PROJECT_ID,
            "diagrams": DIAGRAMS,
            "classifiers": CLASSIFIERS,
            "relations": RELATIONS,
            "interfaces": [],
        }
    ],
}

# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

from metadata.models import Project

print(f"Importing {SYSTEM_NAME} project...")
project = Project.import_from_json(PROJECT_DATA)
print(f"Done: project {project.id} — {project.name}")
