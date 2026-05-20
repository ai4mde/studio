"""
Restore Hospital system data.

Usage:
    python manage.py shell < scripts/restore_hospital.py

Or from inside manage.py shell:
    exec(open('scripts/restore_hospital.py').read())
"""

import django
import os

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SYSTEM_ID = "a2000001-0000-5000-8000-000000000000"
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


def _relation(id_, source, target, label, src_mult, tgt_mult):
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


def _node(id_, cls_id, x, y):
    return {
        "id": id_,
        "diagram": "d2000001-0000-5000-8000-000000000000",
        "cls": cls_id,
        "data": {"position": {"x": x, "y": y}},
    }


def _edge(id_, rel_id):
    return {
        "id": id_,
        "diagram": "d2000001-0000-5000-8000-000000000000",
        "rel": rel_id,
        "data": {},
    }


def _section(id_, name, cls_id, layout, attributes, operations=None):
    if operations is None:
        operations = {"create": True, "delete": True, "update": True}
    attrs = [{"enum": None, "name": a[0], "type": a[1], "derived": False} for a in attributes]
    return {
        "id": id_,
        "name": name,
        "text": "",
        "class": cls_id,
        "style": {
            "color": "blue",
            "radius": "xl",
            "columns": "1",
            "density": "normal",
            "card_style": "elevated",
            "image_size": "md",
            "image_position": "top",
        },
        "layout": layout,
        "col_span": 12,
        "attributes": attrs,
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


# ---------------------------------------------------------------------------
# Classifiers
# ---------------------------------------------------------------------------

ACTORS = [
    _classifier("b2000001-0000-5000-8000-000000000000", "Patient", "actor", []),
    _classifier("b2000002-0000-5000-8000-000000000000", "Doctor", "actor", []),
    _classifier("b2000003-0000-5000-8000-000000000000", "Admin", "actor", []),
]

CLASSES = [
    _classifier(
        "c2000001-0000-5000-8000-000000000000", "Department", "class",
        [
            _attr("department_id", "str"),
            _attr("name", "str"),
            _attr("description", "str"),
            _attr("head_doctor_id", "str"),
            _attr("floor", "int"),
            _attr("phone", "str"),
        ],
    ),
    _classifier(
        "c2000002-0000-5000-8000-000000000000", "Room", "class",
        [
            _attr("room_id", "str"),
            _attr("department_id", "str"),
            _attr("room_number", "str"),
            _attr("type", "str"),
            _attr("capacity", "int"),
            _attr("is_available", "bool"),
            _attr("floor", "int"),
        ],
    ),
    _classifier(
        "c2000003-0000-5000-8000-000000000000", "Patient", "class",
        [
            _attr("patient_id", "str"),
            _attr("first_name", "str"),
            _attr("last_name", "str"),
            _attr("gender", "str"),
            _attr("blood_type", "str"),
            _attr("phone", "str"),
            _attr("email", "str"),
            _attr("address", "str"),
            _attr("emergency_contact", "str"),
            _attr("insurance_number", "str"),
            _attr("is_active", "bool"),
        ],
    ),
    _classifier(
        "c2000004-0000-5000-8000-000000000000", "Doctor", "class",
        [
            _attr("doctor_id", "str"),
            _attr("first_name", "str"),
            _attr("last_name", "str"),
            _attr("specialization", "str"),
            _attr("department_id", "str"),
            _attr("phone", "str"),
            _attr("email", "str"),
            _attr("license_number", "str"),
            _attr("is_available", "bool"),
            _attr("consultation_fee", "str"),
            _attr("years_experience", "int"),
            _attr("rating", "str"),
        ],
    ),
    _classifier(
        "c2000005-0000-5000-8000-000000000000", "Nurse", "class",
        [
            _attr("nurse_id", "str"),
            _attr("first_name", "str"),
            _attr("last_name", "str"),
            _attr("department_id", "str"),
            _attr("phone", "str"),
            _attr("email", "str"),
            _attr("shift", "str"),
            _attr("is_available", "bool"),
        ],
    ),
    _classifier(
        "c2000006-0000-5000-8000-000000000000", "Staff", "class",
        [
            _attr("staff_id", "str"),
            _attr("first_name", "str"),
            _attr("last_name", "str"),
            _attr("role", "str"),
            _attr("department_id", "str"),
            _attr("phone", "str"),
            _attr("email", "str"),
            _attr("is_active", "bool"),
        ],
    ),
    _classifier(
        "c2000007-0000-5000-8000-000000000000", "Appointment", "class",
        [
            _attr("appointment_id", "str"),
            _attr("patient_id", "str"),
            _attr("doctor_id", "str"),
            _attr("time", "str"),
            _attr("status", "str"),
            _attr("reason", "str"),
            _attr("notes", "str"),
        ],
    ),
    _classifier(
        "c2000008-0000-5000-8000-000000000000", "MedicalRecord", "class",
        [
            _attr("record_id", "str"),
            _attr("patient_id", "str"),
            _attr("doctor_id", "str"),
            _attr("appointment_id", "str"),
            _attr("diagnosis", "str"),
            _attr("symptoms", "str"),
            _attr("treatment_plan", "str"),
            _attr("notes", "str"),
        ],
    ),
    _classifier(
        "c2000009-0000-5000-8000-000000000000", "LabTest", "class",
        [
            _attr("test_id", "str"),
            _attr("patient_id", "str"),
            _attr("doctor_id", "str"),
            _attr("test_name", "str"),
            _attr("test_type", "str"),
            _attr("status", "str"),
            _attr("result", "str"),
            _attr("notes", "str"),
        ],
    ),
    _classifier(
        "c2000010-0000-5000-8000-000000000000", "Prescription", "class",
        [
            _attr("prescription_id", "str"),
            _attr("record_id", "str"),
            _attr("patient_id", "str"),
            _attr("doctor_id", "str"),
            _attr("medication_name", "str"),
            _attr("dosage", "str"),
            _attr("frequency", "str"),
            _attr("duration", "str"),
            _attr("notes", "str"),
        ],
    ),
    _classifier(
        "c2000011-0000-5000-8000-000000000000", "Admission", "class",
        [
            _attr("admission_id", "str"),
            _attr("patient_id", "str"),
            _attr("room_id", "str"),
            _attr("doctor_id", "str"),
            _attr("reason", "str"),
            _attr("status", "str"),
            _attr("total_cost", "str"),
        ],
    ),
    _classifier(
        "c2000012-0000-5000-8000-000000000000", "Bill", "class",
        [
            _attr("bill_id", "str"),
            _attr("patient_id", "str"),
            _attr("appointment_id", "str"),
            _attr("total_amount", "str"),
            _attr("paid_amount", "str"),
            _attr("balance", "str"),
            _attr("payment_status", "str"),
        ],
    ),
    _classifier(
        "c2000013-0000-5000-8000-000000000000", "Payment", "class",
        [
            _attr("payment_id", "str"),
            _attr("bill_id", "str"),
            _attr("patient_id", "str"),
            _attr("amount", "str"),
            _attr("payment_method", "str"),
            _attr("status", "str"),
            _attr("transaction_id", "str"),
        ],
    ),
    _classifier(
        "c2000014-0000-5000-8000-000000000000", "Medication", "class",
        [
            _attr("medication_id", "str"),
            _attr("name", "str"),
            _attr("generic_name", "str"),
            _attr("category", "str"),
            _attr("unit", "str"),
            _attr("stock_quantity", "int"),
            _attr("price", "str"),
            _attr("requires_prescription", "bool"),
        ],
    ),
]

ALL_CLASSIFIERS = ACTORS + CLASSES

# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------

RELATIONS = [
    _relation("r2000001-0000-5000-8000-000000000000",
              "c2000001-0000-5000-8000-000000000000",
              "c2000002-0000-5000-8000-000000000000",
              "has", "1", "*"),
    _relation("r2000002-0000-5000-8000-000000000000",
              "c2000004-0000-5000-8000-000000000000",
              "c2000007-0000-5000-8000-000000000000",
              "has", "1", "*"),
    _relation("r2000003-0000-5000-8000-000000000000",
              "c2000003-0000-5000-8000-000000000000",
              "c2000007-0000-5000-8000-000000000000",
              "books", "1", "*"),
    _relation("r2000004-0000-5000-8000-000000000000",
              "c2000007-0000-5000-8000-000000000000",
              "c2000008-0000-5000-8000-000000000000",
              "generates", "1", "*"),
    _relation("r2000005-0000-5000-8000-000000000000",
              "c2000003-0000-5000-8000-000000000000",
              "c2000012-0000-5000-8000-000000000000",
              "receives", "1", "*"),
    _relation("r2000006-0000-5000-8000-000000000000",
              "c2000012-0000-5000-8000-000000000000",
              "c2000013-0000-5000-8000-000000000000",
              "has", "1", "*"),
    _relation("r2000007-0000-5000-8000-000000000000",
              "c2000004-0000-5000-8000-000000000000",
              "c2000010-0000-5000-8000-000000000000",
              "writes", "1", "*"),
    _relation("r2000008-0000-5000-8000-000000000000",
              "c2000008-0000-5000-8000-000000000000",
              "c2000010-0000-5000-8000-000000000000",
              "includes", "1", "*"),
    _relation("r2000009-0000-5000-8000-000000000000",
              "c2000003-0000-5000-8000-000000000000",
              "c2000011-0000-5000-8000-000000000000",
              "has", "1", "*"),
    _relation("r2000010-0000-5000-8000-000000000000",
              "c2000002-0000-5000-8000-000000000000",
              "c2000011-0000-5000-8000-000000000000",
              "hosts", "1", "*"),
]

# ---------------------------------------------------------------------------
# Diagram – nodes and edges
# ---------------------------------------------------------------------------

# Grid layout: 4 columns, x-spacing=400, y-spacing=280
# Order: Department, Room, Patient, Doctor, Nurse, Staff, Appointment,
#        MedicalRecord, LabTest, Prescription, Admission, Bill, Payment, Medication

_NODE_POSITIONS = [
    ("n2000001-0000-5000-8000-000000000000", "c2000001-0000-5000-8000-000000000000", 0,    0),
    ("n2000002-0000-5000-8000-000000000000", "c2000002-0000-5000-8000-000000000000", 400,  0),
    ("n2000003-0000-5000-8000-000000000000", "c2000003-0000-5000-8000-000000000000", 800,  0),
    ("n2000004-0000-5000-8000-000000000000", "c2000004-0000-5000-8000-000000000000", 1200, 0),
    ("n2000005-0000-5000-8000-000000000000", "c2000005-0000-5000-8000-000000000000", 0,    280),
    ("n2000006-0000-5000-8000-000000000000", "c2000006-0000-5000-8000-000000000000", 400,  280),
    ("n2000007-0000-5000-8000-000000000000", "c2000007-0000-5000-8000-000000000000", 800,  280),
    ("n2000008-0000-5000-8000-000000000000", "c2000008-0000-5000-8000-000000000000", 1200, 280),
    ("n2000009-0000-5000-8000-000000000000", "c2000009-0000-5000-8000-000000000000", 0,    560),
    ("n2000010-0000-5000-8000-000000000000", "c2000010-0000-5000-8000-000000000000", 400,  560),
    ("n2000011-0000-5000-8000-000000000000", "c2000011-0000-5000-8000-000000000000", 800,  560),
    ("n2000012-0000-5000-8000-000000000000", "c2000012-0000-5000-8000-000000000000", 1200, 560),
    ("n2000013-0000-5000-8000-000000000000", "c2000013-0000-5000-8000-000000000000", 0,    840),
    ("n2000014-0000-5000-8000-000000000000", "c2000014-0000-5000-8000-000000000000", 400,  840),
]

NODES = [_node(nid, cls_id, x, y) for nid, cls_id, x, y in _NODE_POSITIONS]

# Map classifier_id -> node_id for edge lookup
_CLS_TO_NODE = {cls_id: nid for nid, cls_id, x, y in _NODE_POSITIONS}

# Edges correspond 1-to-1 with relations (r2000001 -> e2000001, etc.)
_EDGE_DEFS = [
    ("e2000001-0000-5000-8000-000000000000", "r2000001-0000-5000-8000-000000000000"),
    ("e2000002-0000-5000-8000-000000000000", "r2000002-0000-5000-8000-000000000000"),
    ("e2000003-0000-5000-8000-000000000000", "r2000003-0000-5000-8000-000000000000"),
    ("e2000004-0000-5000-8000-000000000000", "r2000004-0000-5000-8000-000000000000"),
    ("e2000005-0000-5000-8000-000000000000", "r2000005-0000-5000-8000-000000000000"),
    ("e2000006-0000-5000-8000-000000000000", "r2000006-0000-5000-8000-000000000000"),
    ("e2000007-0000-5000-8000-000000000000", "r2000007-0000-5000-8000-000000000000"),
    ("e2000008-0000-5000-8000-000000000000", "r2000008-0000-5000-8000-000000000000"),
    ("e2000009-0000-5000-8000-000000000000", "r2000009-0000-5000-8000-000000000000"),
    ("e2000010-0000-5000-8000-000000000000", "r2000010-0000-5000-8000-000000000000"),
]

EDGES = [_edge(eid, rid) for eid, rid in _EDGE_DEFS]

DIAGRAMS = [
    {
        "id": "d2000001-0000-5000-8000-000000000000",
        "type": "classes",
        "name": "Hospital Domain Model",
        "description": "Core domain classes for the hospital management system",
        "system": SYSTEM_ID,
        "nodes": NODES,
        "edges": EDGES,
    }
]

# ---------------------------------------------------------------------------
# Interfaces
# ---------------------------------------------------------------------------

# --- Patient Interface ---

_patient_sections = [
    _section(
        "s2000001-0000-5000-8000-000000000000",
        "Appointment List",
        "c2000007-0000-5000-8000-000000000000",
        "list",
        [
            ("appointment_id", "str"),
            ("doctor_id", "str"),
            ("time", "str"),
            ("status", "str"),
            ("reason", "str"),
        ],
        operations={"create": False, "delete": False, "update": False},
    ),
    _section(
        "s2000002-0000-5000-8000-000000000000",
        "Doctor List",
        "c2000004-0000-5000-8000-000000000000",
        "list",
        [
            ("first_name", "str"),
            ("last_name", "str"),
            ("specialization", "str"),
            ("is_available", "bool"),
            ("consultation_fee", "str"),
            ("rating", "str"),
        ],
        operations={"create": False, "delete": False, "update": False},
    ),
    _section(
        "s2000003-0000-5000-8000-000000000000",
        "Appointment Form",
        "c2000007-0000-5000-8000-000000000000",
        "detail",
        [
            ("doctor_id", "str"),
            ("time", "str"),
            ("reason", "str"),
            ("notes", "str"),
        ],
        operations={"create": True, "delete": False, "update": False},
    ),
    _section(
        "s2000004-0000-5000-8000-000000000000",
        "MedicalRecord List",
        "c2000008-0000-5000-8000-000000000000",
        "list",
        [
            ("record_id", "str"),
            ("doctor_id", "str"),
            ("diagnosis", "str"),
            ("symptoms", "str"),
            ("treatment_plan", "str"),
        ],
        operations={"create": False, "delete": False, "update": False},
    ),
    _section(
        "s2000005-0000-5000-8000-000000000000",
        "Bill List",
        "c2000012-0000-5000-8000-000000000000",
        "list",
        [
            ("bill_id", "str"),
            ("total_amount", "str"),
            ("paid_amount", "str"),
            ("balance", "str"),
            ("payment_status", "str"),
        ],
        operations={"create": False, "delete": False, "update": False},
    ),
]

_patient_pages = [
    _page(
        "p2000001-0000-5000-8000-000000000000",
        "My Appointments",
        [{"label": "Appointment List", "value": "s2000001-0000-5000-8000-000000000000"}],
    ),
    _page(
        "p2000002-0000-5000-8000-000000000000",
        "Book Appointment",
        [
            {"label": "Doctor List", "value": "s2000002-0000-5000-8000-000000000000"},
            {"label": "Appointment Form", "value": "s2000003-0000-5000-8000-000000000000"},
        ],
    ),
    _page(
        "p2000003-0000-5000-8000-000000000000",
        "My Medical Records",
        [{"label": "MedicalRecord List", "value": "s2000004-0000-5000-8000-000000000000"}],
    ),
    _page(
        "p2000004-0000-5000-8000-000000000000",
        "My Bills",
        [{"label": "Bill List", "value": "s2000005-0000-5000-8000-000000000000"}],
    ),
]

PATIENT_INTERFACE = {
    "id": "i2000001-0000-5000-8000-000000000000",
    "name": "Patient",
    "description": "Patient portal application",
    "system": SYSTEM_ID,
    "actor": "b2000001-0000-5000-8000-000000000000",
    "data": {
        "pages": _patient_pages,
        "sections": _patient_sections,
        "styling": {
            "radius": 0,
            "textColor": "#000000",
            "accentColor": "#F5F5F4",
            "selectedStyle": "modern",
            "backgroundColor": "#FFFFFF",
        },
        "settings": {},
        "categories": [],
    },
}

# --- Doctor Interface ---

_doctor_sections = [
    _section(
        "s2000006-0000-5000-8000-000000000000",
        "Appointment List",
        "c2000007-0000-5000-8000-000000000000",
        "list",
        [
            ("appointment_id", "str"),
            ("patient_id", "str"),
            ("time", "str"),
            ("status", "str"),
            ("reason", "str"),
        ],
        operations={"create": False, "delete": False, "update": True},
    ),
    _section(
        "s2000007-0000-5000-8000-000000000000",
        "Patient List",
        "c2000003-0000-5000-8000-000000000000",
        "list",
        [
            ("first_name", "str"),
            ("last_name", "str"),
            ("gender", "str"),
            ("blood_type", "str"),
            ("phone", "str"),
            ("is_active", "bool"),
        ],
        operations={"create": False, "delete": False, "update": False},
    ),
    _section(
        "s2000008-0000-5000-8000-000000000000",
        "MedicalRecord Form",
        "c2000008-0000-5000-8000-000000000000",
        "detail",
        [
            ("patient_id", "str"),
            ("appointment_id", "str"),
            ("diagnosis", "str"),
            ("symptoms", "str"),
            ("treatment_plan", "str"),
            ("notes", "str"),
        ],
        operations={"create": True, "delete": False, "update": True},
    ),
    _section(
        "s2000009-0000-5000-8000-000000000000",
        "LabTest Form",
        "c2000009-0000-5000-8000-000000000000",
        "detail",
        [
            ("patient_id", "str"),
            ("test_name", "str"),
            ("test_type", "str"),
            ("notes", "str"),
        ],
        operations={"create": True, "delete": False, "update": True},
    ),
]

_doctor_pages = [
    _page(
        "p2000005-0000-5000-8000-000000000000",
        "Today's Schedule",
        [{"label": "Appointment List", "value": "s2000006-0000-5000-8000-000000000000"}],
    ),
    _page(
        "p2000006-0000-5000-8000-000000000000",
        "My Patients",
        [{"label": "Patient List", "value": "s2000007-0000-5000-8000-000000000000"}],
    ),
    _page(
        "p2000007-0000-5000-8000-000000000000",
        "Write Diagnosis",
        [{"label": "MedicalRecord Form", "value": "s2000008-0000-5000-8000-000000000000"}],
        single_record=True,
    ),
    _page(
        "p2000008-0000-5000-8000-000000000000",
        "Order Lab Tests",
        [{"label": "LabTest Form", "value": "s2000009-0000-5000-8000-000000000000"}],
        single_record=True,
    ),
]

DOCTOR_INTERFACE = {
    "id": "i2000002-0000-5000-8000-000000000000",
    "name": "Doctor",
    "description": "Doctor portal application",
    "system": SYSTEM_ID,
    "actor": "b2000002-0000-5000-8000-000000000000",
    "data": {
        "pages": _doctor_pages,
        "sections": _doctor_sections,
        "styling": {
            "radius": 0,
            "textColor": "#000000",
            "accentColor": "#F5F5F4",
            "selectedStyle": "modern",
            "backgroundColor": "#FFFFFF",
        },
        "settings": {},
        "categories": [],
    },
}

# --- Admin Interface ---

_admin_sections = [
    _section(
        "s2000010-0000-5000-8000-000000000000",
        "Patient List",
        "c2000003-0000-5000-8000-000000000000",
        "list",
        [
            ("first_name", "str"),
            ("last_name", "str"),
            ("gender", "str"),
            ("phone", "str"),
            ("email", "str"),
            ("is_active", "bool"),
        ],
        operations={"create": True, "delete": True, "update": True},
    ),
    _section(
        "s2000011-0000-5000-8000-000000000000",
        "Doctor List",
        "c2000004-0000-5000-8000-000000000000",
        "list",
        [
            ("first_name", "str"),
            ("last_name", "str"),
            ("specialization", "str"),
            ("department_id", "str"),
            ("is_available", "bool"),
            ("license_number", "str"),
        ],
        operations={"create": True, "delete": True, "update": True},
    ),
    _section(
        "s2000012-0000-5000-8000-000000000000",
        "Department List",
        "c2000001-0000-5000-8000-000000000000",
        "list",
        [
            ("name", "str"),
            ("description", "str"),
            ("head_doctor_id", "str"),
            ("floor", "int"),
            ("phone", "str"),
        ],
        operations={"create": True, "delete": True, "update": True},
    ),
    _section(
        "s2000013-0000-5000-8000-000000000000",
        "Staff List",
        "c2000006-0000-5000-8000-000000000000",
        "list",
        [
            ("first_name", "str"),
            ("last_name", "str"),
            ("role", "str"),
            ("department_id", "str"),
            ("phone", "str"),
            ("is_active", "bool"),
        ],
        operations={"create": True, "delete": True, "update": True},
    ),
]

_admin_pages = [
    _page(
        "p2000009-0000-5000-8000-000000000000",
        "Patient Management",
        [{"label": "Patient List", "value": "s2000010-0000-5000-8000-000000000000"}],
    ),
    _page(
        "p2000010-0000-5000-8000-000000000000",
        "Doctor Management",
        [{"label": "Doctor List", "value": "s2000011-0000-5000-8000-000000000000"}],
    ),
    _page(
        "p2000011-0000-5000-8000-000000000000",
        "Department Management",
        [{"label": "Department List", "value": "s2000012-0000-5000-8000-000000000000"}],
    ),
    _page(
        "p2000012-0000-5000-8000-000000000000",
        "Staff Management",
        [{"label": "Staff List", "value": "s2000013-0000-5000-8000-000000000000"}],
    ),
]

ADMIN_INTERFACE = {
    "id": "i2000003-0000-5000-8000-000000000000",
    "name": "Admin",
    "description": "Admin portal application",
    "system": SYSTEM_ID,
    "actor": "b2000003-0000-5000-8000-000000000000",
    "data": {
        "pages": _admin_pages,
        "sections": _admin_sections,
        "styling": {
            "radius": 0,
            "textColor": "#000000",
            "accentColor": "#F5F5F4",
            "selectedStyle": "modern",
            "backgroundColor": "#FFFFFF",
        },
        "settings": {},
        "categories": [],
    },
}

INTERFACES = [PATIENT_INTERFACE, DOCTOR_INTERFACE, ADMIN_INTERFACE]

# ---------------------------------------------------------------------------
# Top-level system data dict
# ---------------------------------------------------------------------------

hospital_data = {
    "id": SYSTEM_ID,
    "project": PROJECT_ID,
    "name": "Hospital",
    "description": "Hospital management system",
    "classifiers": ALL_CLASSIFIERS,
    "imported_classifiers": [],
    "relations": RELATIONS,
    "diagrams": DIAGRAMS,
    "interfaces": INTERFACES,
}

# ---------------------------------------------------------------------------
# Run import
# ---------------------------------------------------------------------------

from metadata.models import System

print("Importing Hospital system...")
system = System.import_from_json(hospital_data)
print(f"Hospital system restored successfully: {system.id} — {system.name}")
