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
APPOINTMENT_LIST_LABEL = "Appointment List"
DOCTOR_LIST_LABEL = "Doctor List"
PATIENT_LIST_LABEL = "Patient List"


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


def _usecase_relation(id_, source, target):
    return {
        "id": id_,
        "system": SYSTEM_ID,
        "source": source,
        "target": target,
        "data": {
            "type": "association",
            "label": "uses",
            "labels": None,
            "derived": False,
            "multiplicity": {"source": "1", "target": "*"},
            "position_handlers": [],
        },
    }


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


def _node(id_, cls_id, x, y, diagram="d2000001-0000-5000-8000-000000000000"):
    return {
        "id": id_,
        "diagram": diagram,
        "cls": cls_id,
        "data": {"position": {"x": x, "y": y}},
    }


def _edge(id_, rel_id, diagram="d2000001-0000-5000-8000-000000000000"):
    return {
        "id": id_,
        "diagram": diagram,
        "rel": rel_id,
        "data": {},
    }


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


def _swimlane_group(id_):
    return _data_classifier(
        id_,
        {
            "type": "swimlanegroup",
            "height": 1160,
            "width": 320,
            "horizontal": False,
            "swimlanes": [
                {
                    "type": "swimlane",
                    "role": "swimlane",
                    "actorNode": "b2000001-0000-5000-8000-000000000000",
                    "actorNodeName": "Patient",
                },
                {
                    "type": "swimlane",
                    "role": "swimlane",
                    "actorNode": "b2000003-0000-5000-8000-000000000000",
                    "actorNodeName": "Admin",
                },
                {
                    "type": "swimlane",
                    "role": "swimlane",
                    "actorNode": "b2000002-0000-5000-8000-000000000000",
                    "actorNodeName": "Doctor",
                },
            ],
        },
    )


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

PATIENT_ACTOR = "b2000001-0000-5000-8000-000000000000"
DOCTOR_ACTOR = "b2000002-0000-5000-8000-000000000000"
ADMIN_ACTOR = "b2000003-0000-5000-8000-000000000000"

DEPARTMENT_CLASS = "c2000001-0000-5000-8000-000000000000"
ROOM_CLASS = "c2000002-0000-5000-8000-000000000000"
PATIENT_CLASS = "c2000003-0000-5000-8000-000000000000"
DOCTOR_CLASS = "c2000004-0000-5000-8000-000000000000"
NURSE_CLASS = "c2000005-0000-5000-8000-000000000000"
STAFF_CLASS = "c2000006-0000-5000-8000-000000000000"
APPOINTMENT_CLASS = "c2000007-0000-5000-8000-000000000000"
MEDICAL_RECORD_CLASS = "c2000008-0000-5000-8000-000000000000"
LAB_TEST_CLASS = "c2000009-0000-5000-8000-000000000000"
PRESCRIPTION_CLASS = "c2000010-0000-5000-8000-000000000000"
ADMISSION_CLASS = "c2000011-0000-5000-8000-000000000000"
BILL_CLASS = "c2000012-0000-5000-8000-000000000000"
PAYMENT_CLASS = "c2000013-0000-5000-8000-000000000000"
MEDICATION_CLASS = "c2000014-0000-5000-8000-000000000000"

USECASE_DIAGRAM_ID = "d2000002-0000-5000-8000-000000000000"
APPOINTMENT_ACTIVITY_DIAGRAM_ID = "d2000003-0000-5000-8000-000000000000"
ADMISSION_ACTIVITY_DIAGRAM_ID = "d2000004-0000-5000-8000-000000000000"

BOOK_APPOINTMENT_UC = "a2000101-0000-5000-8000-000000000000"
VIEW_RECORDS_UC = "a2000102-0000-5000-8000-000000000000"
PAY_BILLS_UC = "a2000103-0000-5000-8000-000000000000"
MANAGE_APPOINTMENTS_UC = "a2000104-0000-5000-8000-000000000000"
MAINTAIN_RECORDS_UC = "a2000105-0000-5000-8000-000000000000"
ORDER_LABS_UC = "a2000106-0000-5000-8000-000000000000"
WRITE_PRESCRIPTIONS_UC = "a2000107-0000-5000-8000-000000000000"
MANAGE_ADMISSIONS_UC = "a2000108-0000-5000-8000-000000000000"
MANAGE_RESOURCES_UC = "a2000109-0000-5000-8000-000000000000"
MANAGE_BILLING_UC = "a2000110-0000-5000-8000-000000000000"
MANAGE_PATIENTS_STAFF_UC = "a2000111-0000-5000-8000-000000000000"

APPOINTMENT_INITIAL = "a2000200-0000-5000-8000-000000000000"
REQUEST_APPOINTMENT_ACTION = "a2000201-0000-5000-8000-000000000000"
SCHEDULE_APPOINTMENT_ACTION = "a2000202-0000-5000-8000-000000000000"
REVIEW_APPOINTMENT_ACTION = "a2000203-0000-5000-8000-000000000000"
CONSULT_PATIENT_ACTION = "a2000204-0000-5000-8000-000000000000"
UPDATE_MEDICAL_RECORD_ACTION = "a2000205-0000-5000-8000-000000000000"
GENERATE_VISIT_BILL_ACTION = "a2000206-0000-5000-8000-000000000000"
PAY_VISIT_BILL_ACTION = "a2000207-0000-5000-8000-000000000000"
APPOINTMENT_FINAL = "a2000208-0000-5000-8000-000000000000"

ADMISSION_INITIAL = "a2000300-0000-5000-8000-000000000000"
REQUEST_ADMISSION_ACTION = "a2000301-0000-5000-8000-000000000000"
ASSIGN_ROOM_ACTION = "a2000302-0000-5000-8000-000000000000"
ADMIT_PATIENT_ACTION = "a2000303-0000-5000-8000-000000000000"
MONITOR_ADMISSION_ACTION = "a2000304-0000-5000-8000-000000000000"
DISCHARGE_PATIENT_ACTION = "a2000305-0000-5000-8000-000000000000"
GENERATE_FINAL_BILL_ACTION = "a2000306-0000-5000-8000-000000000000"
PAY_FINAL_BILL_ACTION = "a2000307-0000-5000-8000-000000000000"
ADMISSION_FINAL = "a2000308-0000-5000-8000-000000000000"

APPOINTMENT_SWIMLANE_GROUP = "a2000401-0000-5000-8000-000000000000"
ADMISSION_SWIMLANE_GROUP = "a2000402-0000-5000-8000-000000000000"

USECASES = [
    _usecase(
        BOOK_APPOINTMENT_UC,
        "Book Appointment",
        [PATIENT_ACTOR],
        [PATIENT_CLASS, DOCTOR_CLASS, APPOINTMENT_CLASS],
        [REQUEST_APPOINTMENT_ACTION, SCHEDULE_APPOINTMENT_ACTION],
        [APPOINTMENT_ACTIVITY_DIAGRAM_ID],
        "Patient needs a consultation",
        "Appointment is scheduled and visible to the doctor",
    ),
    _usecase(
        VIEW_RECORDS_UC,
        "View Medical Records",
        [PATIENT_ACTOR],
        [PATIENT_CLASS, MEDICAL_RECORD_CLASS, LAB_TEST_CLASS, PRESCRIPTION_CLASS],
    ),
    _usecase(
        PAY_BILLS_UC,
        "Pay Bills",
        [PATIENT_ACTOR],
        [PATIENT_CLASS, BILL_CLASS, PAYMENT_CLASS],
        [PAY_VISIT_BILL_ACTION, PAY_FINAL_BILL_ACTION],
        [APPOINTMENT_ACTIVITY_DIAGRAM_ID, ADMISSION_ACTIVITY_DIAGRAM_ID],
    ),
    _usecase(
        MANAGE_APPOINTMENTS_UC,
        "Manage Appointments",
        [ADMIN_ACTOR, DOCTOR_ACTOR],
        [APPOINTMENT_CLASS, PATIENT_CLASS, DOCTOR_CLASS],
        [SCHEDULE_APPOINTMENT_ACTION, REVIEW_APPOINTMENT_ACTION],
        [APPOINTMENT_ACTIVITY_DIAGRAM_ID],
    ),
    _usecase(
        MAINTAIN_RECORDS_UC,
        "Maintain Medical Records",
        [DOCTOR_ACTOR],
        [PATIENT_CLASS, APPOINTMENT_CLASS, MEDICAL_RECORD_CLASS],
        [CONSULT_PATIENT_ACTION, UPDATE_MEDICAL_RECORD_ACTION],
        [APPOINTMENT_ACTIVITY_DIAGRAM_ID],
    ),
    _usecase(
        ORDER_LABS_UC,
        "Order Lab Tests",
        [DOCTOR_ACTOR],
        [PATIENT_CLASS, DOCTOR_CLASS, LAB_TEST_CLASS],
    ),
    _usecase(
        WRITE_PRESCRIPTIONS_UC,
        "Write Prescriptions",
        [DOCTOR_ACTOR],
        [PATIENT_CLASS, DOCTOR_CLASS, MEDICAL_RECORD_CLASS, PRESCRIPTION_CLASS, MEDICATION_CLASS],
    ),
    _usecase(
        MANAGE_ADMISSIONS_UC,
        "Manage Admissions",
        [DOCTOR_ACTOR, ADMIN_ACTOR],
        [PATIENT_CLASS, DOCTOR_CLASS, ROOM_CLASS, ADMISSION_CLASS],
        [
            REQUEST_ADMISSION_ACTION,
            ASSIGN_ROOM_ACTION,
            ADMIT_PATIENT_ACTION,
            MONITOR_ADMISSION_ACTION,
            DISCHARGE_PATIENT_ACTION,
        ],
        [ADMISSION_ACTIVITY_DIAGRAM_ID],
    ),
    _usecase(
        MANAGE_RESOURCES_UC,
        "Manage Hospital Resources",
        [ADMIN_ACTOR],
        [DEPARTMENT_CLASS, ROOM_CLASS, DOCTOR_CLASS, NURSE_CLASS, STAFF_CLASS, MEDICATION_CLASS],
    ),
    _usecase(
        MANAGE_BILLING_UC,
        "Manage Billing",
        [ADMIN_ACTOR],
        [PATIENT_CLASS, APPOINTMENT_CLASS, ADMISSION_CLASS, BILL_CLASS, PAYMENT_CLASS],
        [GENERATE_VISIT_BILL_ACTION, GENERATE_FINAL_BILL_ACTION],
        [APPOINTMENT_ACTIVITY_DIAGRAM_ID, ADMISSION_ACTIVITY_DIAGRAM_ID],
    ),
    _usecase(
        MANAGE_PATIENTS_STAFF_UC,
        "Manage Patients and Staff",
        [ADMIN_ACTOR],
        [PATIENT_CLASS, DOCTOR_CLASS, NURSE_CLASS, STAFF_CLASS, DEPARTMENT_CLASS],
    ),
]

APPOINTMENT_ACTIVITY_CLASSIFIERS = [
    _swimlane_group(APPOINTMENT_SWIMLANE_GROUP),
    _control(APPOINTMENT_INITIAL, "initial"),
    _action(
        REQUEST_APPOINTMENT_ACTION,
        "Request Appointment",
        PATIENT_ACTOR,
        "Patient",
        [PATIENT_CLASS, DOCTOR_CLASS, APPOINTMENT_CLASS],
        "Patient chooses a doctor and reason for visit",
        "Appointment request is submitted",
    ),
    _action(
        SCHEDULE_APPOINTMENT_ACTION,
        "Schedule Appointment",
        ADMIN_ACTOR,
        "Admin",
        [APPOINTMENT_CLASS, DOCTOR_CLASS, PATIENT_CLASS],
        "Appointment request is waiting for scheduling",
        "Appointment time and doctor are confirmed",
    ),
    _action(
        REVIEW_APPOINTMENT_ACTION,
        "Review Appointment",
        DOCTOR_ACTOR,
        "Doctor",
        [APPOINTMENT_CLASS, PATIENT_CLASS],
        "Scheduled appointment is on the doctor's queue",
        "Doctor has prepared for the consultation",
    ),
    _action(
        CONSULT_PATIENT_ACTION,
        "Consult Patient",
        DOCTOR_ACTOR,
        "Doctor",
        [PATIENT_CLASS, APPOINTMENT_CLASS],
        "Patient attends the appointment",
        "Doctor has completed the consultation",
    ),
    _action(
        UPDATE_MEDICAL_RECORD_ACTION,
        "Update Medical Record",
        DOCTOR_ACTOR,
        "Doctor",
        [PATIENT_CLASS, APPOINTMENT_CLASS, MEDICAL_RECORD_CLASS],
        "Consultation outcome is known",
        "Diagnosis and treatment plan are recorded",
    ),
    _action(
        GENERATE_VISIT_BILL_ACTION,
        "Generate Visit Bill",
        ADMIN_ACTOR,
        "Admin",
        [PATIENT_CLASS, APPOINTMENT_CLASS, BILL_CLASS],
        "Medical record is complete",
        "Bill is issued for the visit",
        True,
    ),
    _action(
        PAY_VISIT_BILL_ACTION,
        "Pay Visit Bill",
        PATIENT_ACTOR,
        "Patient",
        [PATIENT_CLASS, BILL_CLASS, PAYMENT_CLASS],
        "Bill is ready for payment",
        "Payment is recorded and bill balance is updated",
    ),
    _control(APPOINTMENT_FINAL, "final"),
]

ADMISSION_ACTIVITY_CLASSIFIERS = [
    _swimlane_group(ADMISSION_SWIMLANE_GROUP),
    _control(ADMISSION_INITIAL, "initial"),
    _action(
        REQUEST_ADMISSION_ACTION,
        "Request Admission",
        DOCTOR_ACTOR,
        "Doctor",
        [PATIENT_CLASS, DOCTOR_CLASS, ADMISSION_CLASS],
        "Doctor determines inpatient care is needed",
        "Admission request is created",
    ),
    _action(
        ASSIGN_ROOM_ACTION,
        "Assign Room",
        ADMIN_ACTOR,
        "Admin",
        [ROOM_CLASS, DEPARTMENT_CLASS, ADMISSION_CLASS],
        "Admission request is awaiting bed assignment",
        "Available room is reserved",
    ),
    _action(
        ADMIT_PATIENT_ACTION,
        "Admit Patient",
        ADMIN_ACTOR,
        "Admin",
        [PATIENT_CLASS, ROOM_CLASS, ADMISSION_CLASS],
        "Room is assigned",
        "Patient is admitted to the room",
    ),
    _action(
        MONITOR_ADMISSION_ACTION,
        "Monitor Admission",
        DOCTOR_ACTOR,
        "Doctor",
        [PATIENT_CLASS, DOCTOR_CLASS, ADMISSION_CLASS, MEDICAL_RECORD_CLASS],
        "Patient is admitted",
        "Care notes and status are maintained",
    ),
    _action(
        DISCHARGE_PATIENT_ACTION,
        "Discharge Patient",
        DOCTOR_ACTOR,
        "Doctor",
        [PATIENT_CLASS, ADMISSION_CLASS, MEDICAL_RECORD_CLASS],
        "Patient is ready for discharge",
        "Admission status is marked discharged",
    ),
    _action(
        GENERATE_FINAL_BILL_ACTION,
        "Generate Final Bill",
        ADMIN_ACTOR,
        "Admin",
        [PATIENT_CLASS, ADMISSION_CLASS, BILL_CLASS],
        "Discharge is approved",
        "Final bill is issued",
        True,
    ),
    _action(
        PAY_FINAL_BILL_ACTION,
        "Pay Final Bill",
        PATIENT_ACTOR,
        "Patient",
        [PATIENT_CLASS, BILL_CLASS, PAYMENT_CLASS],
        "Final bill is ready",
        "Payment is recorded and admission is closed",
    ),
    _control(ADMISSION_FINAL, "final"),
]

ALL_CLASSIFIERS = ACTORS + CLASSES + USECASES + APPOINTMENT_ACTIVITY_CLASSIFIERS + ADMISSION_ACTIVITY_CLASSIFIERS

# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------

CLASS_RELATIONS = [
    _relation("12000001-0000-5000-8000-000000000000",
              "c2000001-0000-5000-8000-000000000000",
              "c2000002-0000-5000-8000-000000000000",
              "contains", "1", "*"),
    _relation("12000002-0000-5000-8000-000000000000",
              "c2000004-0000-5000-8000-000000000000",
              "c2000007-0000-5000-8000-000000000000",
              "attends", "1", "*"),
    _relation("12000003-0000-5000-8000-000000000000",
              "c2000003-0000-5000-8000-000000000000",
              "c2000007-0000-5000-8000-000000000000",
              "books", "1", "*"),
    _relation("12000004-0000-5000-8000-000000000000",
              "c2000007-0000-5000-8000-000000000000",
              "c2000008-0000-5000-8000-000000000000",
              "generates", "1", "*"),
    _relation("12000005-0000-5000-8000-000000000000",
              "c2000003-0000-5000-8000-000000000000",
              "c2000012-0000-5000-8000-000000000000",
              "receives", "1", "*"),
    _relation("12000006-0000-5000-8000-000000000000",
              "c2000012-0000-5000-8000-000000000000",
              "c2000013-0000-5000-8000-000000000000",
              "has", "1", "*"),
    _relation("12000007-0000-5000-8000-000000000000",
              "c2000004-0000-5000-8000-000000000000",
              "c2000010-0000-5000-8000-000000000000",
              "writes", "1", "*"),
    _relation("12000008-0000-5000-8000-000000000000",
              "c2000008-0000-5000-8000-000000000000",
              "c2000010-0000-5000-8000-000000000000",
              "includes", "1", "*"),
    _relation("12000009-0000-5000-8000-000000000000",
              "c2000003-0000-5000-8000-000000000000",
              "c2000011-0000-5000-8000-000000000000",
              "has", "1", "*"),
    _relation("12000010-0000-5000-8000-000000000000",
              "c2000002-0000-5000-8000-000000000000",
              "c2000011-0000-5000-8000-000000000000",
              "hosts", "1", "*"),
    _relation("12000011-0000-5000-8000-000000000000",
              "c2000001-0000-5000-8000-000000000000",
              "c2000004-0000-5000-8000-000000000000",
              "employs", "1", "*"),
    _relation("12000012-0000-5000-8000-000000000000",
              "c2000001-0000-5000-8000-000000000000",
              "c2000005-0000-5000-8000-000000000000",
              "employs", "1", "*"),
    _relation("12000013-0000-5000-8000-000000000000",
              "c2000001-0000-5000-8000-000000000000",
              "c2000006-0000-5000-8000-000000000000",
              "employs", "1", "*"),
    _relation("12000014-0000-5000-8000-000000000000",
              "c2000003-0000-5000-8000-000000000000",
              "c2000008-0000-5000-8000-000000000000",
              "owns", "1", "*"),
    _relation("12000015-0000-5000-8000-000000000000",
              "c2000004-0000-5000-8000-000000000000",
              "c2000008-0000-5000-8000-000000000000",
              "creates", "1", "*"),
    _relation("12000016-0000-5000-8000-000000000000",
              "c2000003-0000-5000-8000-000000000000",
              "c2000009-0000-5000-8000-000000000000",
              "has", "1", "*"),
    _relation("12000017-0000-5000-8000-000000000000",
              "c2000004-0000-5000-8000-000000000000",
              "c2000009-0000-5000-8000-000000000000",
              "orders", "1", "*"),
    _relation("12000018-0000-5000-8000-000000000000",
              "c2000004-0000-5000-8000-000000000000",
              "c2000011-0000-5000-8000-000000000000",
              "supervises", "1", "*"),
    _relation("12000019-0000-5000-8000-000000000000",
              "c2000007-0000-5000-8000-000000000000",
              "c2000012-0000-5000-8000-000000000000",
              "billed by", "1", "*"),
    _relation("12000020-0000-5000-8000-000000000000",
              "c2000014-0000-5000-8000-000000000000",
              "c2000010-0000-5000-8000-000000000000",
              "dispensed in", "1", "*"),
    _relation("12000021-0000-5000-8000-000000000000",
              "c2000003-0000-5000-8000-000000000000",
              "c2000010-0000-5000-8000-000000000000",
              "receives", "1", "*"),
]

USECASE_RELATIONS = [
    _usecase_relation("12000101-0000-5000-8000-000000000000", PATIENT_ACTOR, BOOK_APPOINTMENT_UC),
    _usecase_relation("12000102-0000-5000-8000-000000000000", PATIENT_ACTOR, VIEW_RECORDS_UC),
    _usecase_relation("12000103-0000-5000-8000-000000000000", PATIENT_ACTOR, PAY_BILLS_UC),
    _usecase_relation("12000104-0000-5000-8000-000000000000", DOCTOR_ACTOR, MANAGE_APPOINTMENTS_UC),
    _usecase_relation("12000105-0000-5000-8000-000000000000", DOCTOR_ACTOR, MAINTAIN_RECORDS_UC),
    _usecase_relation("12000106-0000-5000-8000-000000000000", DOCTOR_ACTOR, ORDER_LABS_UC),
    _usecase_relation("12000107-0000-5000-8000-000000000000", DOCTOR_ACTOR, WRITE_PRESCRIPTIONS_UC),
    _usecase_relation("12000108-0000-5000-8000-000000000000", DOCTOR_ACTOR, MANAGE_ADMISSIONS_UC),
    _usecase_relation("12000109-0000-5000-8000-000000000000", ADMIN_ACTOR, MANAGE_APPOINTMENTS_UC),
    _usecase_relation("12000110-0000-5000-8000-000000000000", ADMIN_ACTOR, MANAGE_ADMISSIONS_UC),
    _usecase_relation("12000111-0000-5000-8000-000000000000", ADMIN_ACTOR, MANAGE_RESOURCES_UC),
    _usecase_relation("12000112-0000-5000-8000-000000000000", ADMIN_ACTOR, MANAGE_BILLING_UC),
    _usecase_relation("12000113-0000-5000-8000-000000000000", ADMIN_ACTOR, MANAGE_PATIENTS_STAFF_UC),
]

APPOINTMENT_ACTIVITY_RELATIONS = [
    _controlflow_relation("12000201-0000-5000-8000-000000000000", APPOINTMENT_INITIAL, REQUEST_APPOINTMENT_ACTION),
    _controlflow_relation("12000202-0000-5000-8000-000000000000", REQUEST_APPOINTMENT_ACTION, SCHEDULE_APPOINTMENT_ACTION),
    _controlflow_relation("12000203-0000-5000-8000-000000000000", SCHEDULE_APPOINTMENT_ACTION, REVIEW_APPOINTMENT_ACTION),
    _controlflow_relation("12000204-0000-5000-8000-000000000000", REVIEW_APPOINTMENT_ACTION, CONSULT_PATIENT_ACTION),
    _controlflow_relation("12000205-0000-5000-8000-000000000000", CONSULT_PATIENT_ACTION, UPDATE_MEDICAL_RECORD_ACTION),
    _controlflow_relation("12000206-0000-5000-8000-000000000000", UPDATE_MEDICAL_RECORD_ACTION, GENERATE_VISIT_BILL_ACTION),
    _controlflow_relation("12000207-0000-5000-8000-000000000000", GENERATE_VISIT_BILL_ACTION, PAY_VISIT_BILL_ACTION),
    _controlflow_relation("12000208-0000-5000-8000-000000000000", PAY_VISIT_BILL_ACTION, APPOINTMENT_FINAL),
]

ADMISSION_ACTIVITY_RELATIONS = [
    _controlflow_relation("12000301-0000-5000-8000-000000000000", ADMISSION_INITIAL, REQUEST_ADMISSION_ACTION),
    _controlflow_relation("12000302-0000-5000-8000-000000000000", REQUEST_ADMISSION_ACTION, ASSIGN_ROOM_ACTION),
    _controlflow_relation("12000303-0000-5000-8000-000000000000", ASSIGN_ROOM_ACTION, ADMIT_PATIENT_ACTION),
    _controlflow_relation("12000304-0000-5000-8000-000000000000", ADMIT_PATIENT_ACTION, MONITOR_ADMISSION_ACTION),
    _controlflow_relation("12000305-0000-5000-8000-000000000000", MONITOR_ADMISSION_ACTION, DISCHARGE_PATIENT_ACTION),
    _controlflow_relation("12000306-0000-5000-8000-000000000000", DISCHARGE_PATIENT_ACTION, GENERATE_FINAL_BILL_ACTION),
    _controlflow_relation("12000307-0000-5000-8000-000000000000", GENERATE_FINAL_BILL_ACTION, PAY_FINAL_BILL_ACTION),
    _controlflow_relation("12000308-0000-5000-8000-000000000000", PAY_FINAL_BILL_ACTION, ADMISSION_FINAL),
]

RELATIONS = CLASS_RELATIONS + USECASE_RELATIONS + APPOINTMENT_ACTIVITY_RELATIONS + ADMISSION_ACTIVITY_RELATIONS

# ---------------------------------------------------------------------------
# Diagram – nodes and edges
# ---------------------------------------------------------------------------

# Class diagram layout: 4 columns, x-spacing=400, y-spacing=280.
_CLASS_NODE_POSITIONS = [
    ("f2000001-0000-5000-8000-000000000000", "c2000001-0000-5000-8000-000000000000", 0,    0),
    ("f2000002-0000-5000-8000-000000000000", "c2000002-0000-5000-8000-000000000000", 400,  0),
    ("f2000003-0000-5000-8000-000000000000", "c2000003-0000-5000-8000-000000000000", 800,  0),
    ("f2000004-0000-5000-8000-000000000000", "c2000004-0000-5000-8000-000000000000", 1200, 0),
    ("f2000005-0000-5000-8000-000000000000", "c2000005-0000-5000-8000-000000000000", 0,    280),
    ("f2000006-0000-5000-8000-000000000000", "c2000006-0000-5000-8000-000000000000", 400,  280),
    ("f2000007-0000-5000-8000-000000000000", "c2000007-0000-5000-8000-000000000000", 800,  280),
    ("f2000008-0000-5000-8000-000000000000", "c2000008-0000-5000-8000-000000000000", 1200, 280),
    ("f2000009-0000-5000-8000-000000000000", "c2000009-0000-5000-8000-000000000000", 0,    560),
    ("f2000010-0000-5000-8000-000000000000", "c2000010-0000-5000-8000-000000000000", 400,  560),
    ("f2000011-0000-5000-8000-000000000000", "c2000011-0000-5000-8000-000000000000", 800,  560),
    ("f2000012-0000-5000-8000-000000000000", "c2000012-0000-5000-8000-000000000000", 1200, 560),
    ("f2000013-0000-5000-8000-000000000000", "c2000013-0000-5000-8000-000000000000", 0,    840),
    ("f2000014-0000-5000-8000-000000000000", "c2000014-0000-5000-8000-000000000000", 400,  840),
]

CLASS_NODES = [_node(nid, cls_id, x, y) for nid, cls_id, x, y in _CLASS_NODE_POSITIONS]

# Map classifier_id -> node_id for edge lookup
_CLS_TO_NODE = {cls_id: nid for nid, cls_id, x, y in _CLASS_NODE_POSITIONS}

# Edges correspond 1-to-1 with class relations so
# the diagram cannot silently drop newly added domain relationships.
_EDGE_DEFS = [
    (f"e20000{index:02d}-0000-5000-8000-000000000000", relation["id"])
    for index, relation in enumerate(CLASS_RELATIONS, 1)
]

CLASS_EDGES = [_edge(eid, rid) for eid, rid in _EDGE_DEFS]

_USECASE_NODE_POSITIONS = [
    ("f2000101-0000-5000-8000-000000000000", PATIENT_ACTOR, -120, 140),
    ("f2000102-0000-5000-8000-000000000000", DOCTOR_ACTOR, -120, 440),
    ("f2000103-0000-5000-8000-000000000000", ADMIN_ACTOR, -120, 740),
    ("f2000111-0000-5000-8000-000000000000", BOOK_APPOINTMENT_UC, 300, 20),
    ("f2000112-0000-5000-8000-000000000000", VIEW_RECORDS_UC, 300, 140),
    ("f2000113-0000-5000-8000-000000000000", PAY_BILLS_UC, 300, 260),
    ("f2000114-0000-5000-8000-000000000000", MANAGE_APPOINTMENTS_UC, 720, 80),
    ("f2000115-0000-5000-8000-000000000000", MAINTAIN_RECORDS_UC, 720, 200),
    ("f2000116-0000-5000-8000-000000000000", ORDER_LABS_UC, 720, 320),
    ("f2000117-0000-5000-8000-000000000000", WRITE_PRESCRIPTIONS_UC, 720, 440),
    ("f2000118-0000-5000-8000-000000000000", MANAGE_ADMISSIONS_UC, 720, 560),
    ("f2000119-0000-5000-8000-000000000000", MANAGE_RESOURCES_UC, 300, 620),
    ("f2000120-0000-5000-8000-000000000000", MANAGE_BILLING_UC, 300, 740),
    ("f2000121-0000-5000-8000-000000000000", MANAGE_PATIENTS_STAFF_UC, 300, 860),
]

USECASE_NODES = [_node(nid, cls_id, x, y, USECASE_DIAGRAM_ID) for nid, cls_id, x, y in _USECASE_NODE_POSITIONS]
USECASE_EDGES = [
    _edge(f"e20001{index:02d}-0000-5000-8000-000000000000", relation["id"], USECASE_DIAGRAM_ID)
    for index, relation in enumerate(USECASE_RELATIONS, 1)
]

_APPOINTMENT_ACTIVITY_NODE_POSITIONS = [
    ("f2000200-0000-5000-8000-000000000000", APPOINTMENT_SWIMLANE_GROUP, -120, -120),
    ("f2000201-0000-5000-8000-000000000000", APPOINTMENT_INITIAL, 80, -20),
    ("f2000202-0000-5000-8000-000000000000", REQUEST_APPOINTMENT_ACTION, 80, 120),
    ("f2000203-0000-5000-8000-000000000000", SCHEDULE_APPOINTMENT_ACTION, 440, 240),
    ("f2000204-0000-5000-8000-000000000000", REVIEW_APPOINTMENT_ACTION, 800, 360),
    ("f2000205-0000-5000-8000-000000000000", CONSULT_PATIENT_ACTION, 800, 500),
    ("f2000206-0000-5000-8000-000000000000", UPDATE_MEDICAL_RECORD_ACTION, 800, 640),
    ("f2000207-0000-5000-8000-000000000000", GENERATE_VISIT_BILL_ACTION, 440, 780),
    ("f2000208-0000-5000-8000-000000000000", PAY_VISIT_BILL_ACTION, 80, 920),
    ("f2000209-0000-5000-8000-000000000000", APPOINTMENT_FINAL, 80, 1060),
]

APPOINTMENT_ACTIVITY_NODES = [
    _node(nid, cls_id, x, y, APPOINTMENT_ACTIVITY_DIAGRAM_ID)
    for nid, cls_id, x, y in _APPOINTMENT_ACTIVITY_NODE_POSITIONS
]
APPOINTMENT_ACTIVITY_EDGES = [
    _edge(f"e20002{index:02d}-0000-5000-8000-000000000000", relation["id"], APPOINTMENT_ACTIVITY_DIAGRAM_ID)
    for index, relation in enumerate(APPOINTMENT_ACTIVITY_RELATIONS, 1)
]

_ADMISSION_ACTIVITY_NODE_POSITIONS = [
    ("f2000300-0000-5000-8000-000000000000", ADMISSION_SWIMLANE_GROUP, -120, -120),
    ("f2000301-0000-5000-8000-000000000000", ADMISSION_INITIAL, 800, -20),
    ("f2000302-0000-5000-8000-000000000000", REQUEST_ADMISSION_ACTION, 800, 120),
    ("f2000303-0000-5000-8000-000000000000", ASSIGN_ROOM_ACTION, 440, 260),
    ("f2000304-0000-5000-8000-000000000000", ADMIT_PATIENT_ACTION, 440, 400),
    ("f2000305-0000-5000-8000-000000000000", MONITOR_ADMISSION_ACTION, 800, 540),
    ("f2000306-0000-5000-8000-000000000000", DISCHARGE_PATIENT_ACTION, 800, 680),
    ("f2000307-0000-5000-8000-000000000000", GENERATE_FINAL_BILL_ACTION, 440, 820),
    ("f2000308-0000-5000-8000-000000000000", PAY_FINAL_BILL_ACTION, 80, 960),
    ("f2000309-0000-5000-8000-000000000000", ADMISSION_FINAL, 80, 1100),
]

ADMISSION_ACTIVITY_NODES = [
    _node(nid, cls_id, x, y, ADMISSION_ACTIVITY_DIAGRAM_ID)
    for nid, cls_id, x, y in _ADMISSION_ACTIVITY_NODE_POSITIONS
]
ADMISSION_ACTIVITY_EDGES = [
    _edge(f"e20003{index:02d}-0000-5000-8000-000000000000", relation["id"], ADMISSION_ACTIVITY_DIAGRAM_ID)
    for index, relation in enumerate(ADMISSION_ACTIVITY_RELATIONS, 1)
]

DIAGRAMS = [
    {
        "id": "d2000001-0000-5000-8000-000000000000",
        "type": "classes",
        "name": "Hospital Domain Model",
        "description": "Core domain classes for the hospital management system",
        "system": SYSTEM_ID,
        "nodes": CLASS_NODES,
        "edges": CLASS_EDGES,
    },
    {
        "id": USECASE_DIAGRAM_ID,
        "type": "usecase",
        "name": "Hospital Use Cases",
        "description": "Use cases for patient, doctor, and admin actors",
        "system": SYSTEM_ID,
        "nodes": USECASE_NODES,
        "edges": USECASE_EDGES,
    },
    {
        "id": APPOINTMENT_ACTIVITY_DIAGRAM_ID,
        "type": "activity",
        "name": "Appointment Care Flow",
        "description": "Patient appointment workflow with Patient, Admin, and Doctor swimlanes",
        "system": SYSTEM_ID,
        "nodes": APPOINTMENT_ACTIVITY_NODES,
        "edges": APPOINTMENT_ACTIVITY_EDGES,
    },
    {
        "id": ADMISSION_ACTIVITY_DIAGRAM_ID,
        "type": "activity",
        "name": "Inpatient Admission Flow",
        "description": "Admission and discharge workflow with Patient, Admin, and Doctor swimlanes",
        "system": SYSTEM_ID,
        "nodes": ADMISSION_ACTIVITY_NODES,
        "edges": ADMISSION_ACTIVITY_EDGES,
    },
]

# ---------------------------------------------------------------------------
# Interfaces
# ---------------------------------------------------------------------------

# --- Patient Interface ---

_patient_sections = [
    _section(
        "s2000001-0000-5000-8000-000000000000",
        APPOINTMENT_LIST_LABEL,
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
        DOCTOR_LIST_LABEL,
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
        [{"label": APPOINTMENT_LIST_LABEL, "value": "s2000001-0000-5000-8000-000000000000"}],
    ),
    _page(
        "p2000002-0000-5000-8000-000000000000",
        "Book Appointment",
        [
            {"label": DOCTOR_LIST_LABEL, "value": "s2000002-0000-5000-8000-000000000000"},
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
    "id": "ab000001-0000-5000-8000-000000000000",
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
        APPOINTMENT_LIST_LABEL,
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
        PATIENT_LIST_LABEL,
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
        [{"label": APPOINTMENT_LIST_LABEL, "value": "s2000006-0000-5000-8000-000000000000"}],
    ),
    _page(
        "p2000006-0000-5000-8000-000000000000",
        "My Patients",
        [{"label": PATIENT_LIST_LABEL, "value": "s2000007-0000-5000-8000-000000000000"}],
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
    "id": "ab000002-0000-5000-8000-000000000000",
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
        PATIENT_LIST_LABEL,
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
        DOCTOR_LIST_LABEL,
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
        [{"label": PATIENT_LIST_LABEL, "value": "s2000010-0000-5000-8000-000000000000"}],
    ),
    _page(
        "p2000010-0000-5000-8000-000000000000",
        "Doctor Management",
        [{"label": DOCTOR_LIST_LABEL, "value": "s2000011-0000-5000-8000-000000000000"}],
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
    "id": "ab000003-0000-5000-8000-000000000000",
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
