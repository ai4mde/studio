"""
Repair the Hospital Management Demo class diagram.

Usage:
    python manage.py shell < scripts/fix_hospital_structure_diagram.py
"""

from diagram.models import Diagram, Edge, Node
from metadata.models import Classifier, Relation, System

SYSTEM_ID = "20a1a1a1-1111-4aaa-8001-000000000001"
DIAGRAM_ID = "30a1a1a1-2222-4aaa-8001-000000000001"
PROJECT_ID = "f3d1c958-af29-45b5-82cd-9145f5912423"


def attr(name, type_):
    return {"name": name, "type": type_, "derived": False, "description": "", "body": None, "enum": None}


CLASS_IDS = {
    "Patient": "40a1a1a1-1111-4aaa-8001-000000000001",
    "Doctor": "40a1a1a1-1111-4aaa-8001-000000000002",
    "Appointment": "40a1a1a1-1111-4aaa-8001-000000000003",
    "MedicalRecord": "40a1a1a1-1111-4aaa-8001-000000000004",
    "Prescription": "40a1a1a1-1111-4aaa-8001-000000000005",
    "Department": "40a1a1a1-1111-4aaa-8001-000000000007",
    "Room": "40a1a1a1-1111-4aaa-8001-000000000008",
    "Nurse": "40a1a1a1-1111-4aaa-8001-000000000009",
    "Staff": "40a1a1a1-1111-4aaa-8001-000000000010",
    "LabTest": "40a1a1a1-1111-4aaa-8001-000000000011",
    "Admission": "40a1a1a1-1111-4aaa-8001-000000000012",
    "Bill": "40a1a1a1-1111-4aaa-8001-000000000013",
    "Payment": "40a1a1a1-1111-4aaa-8001-000000000014",
    "Medication": "40a1a1a1-1111-4aaa-8001-000000000015",
}

CLASS_ATTRIBUTES = {
    "Department": [
        attr("department_id", "str"), attr("name", "str"), attr("description", "str"),
        attr("head_doctor_id", "str"), attr("floor", "int"), attr("phone", "str"),
    ],
    "Room": [
        attr("room_id", "str"), attr("department_id", "str"), attr("room_number", "str"),
        attr("type", "str"), attr("capacity", "int"), attr("is_available", "bool"), attr("floor", "int"),
    ],
    "Patient": [
        attr("patient_id", "str"), attr("first_name", "str"), attr("last_name", "str"),
        attr("gender", "str"), attr("blood_type", "str"), attr("phone", "str"), attr("email", "str"),
        attr("address", "str"), attr("emergency_contact", "str"), attr("insurance_number", "str"),
        attr("is_active", "bool"),
    ],
    "Doctor": [
        attr("doctor_id", "str"), attr("first_name", "str"), attr("last_name", "str"),
        attr("specialization", "str"), attr("department_id", "str"), attr("phone", "str"),
        attr("email", "str"), attr("license_number", "str"), attr("is_available", "bool"),
        attr("consultation_fee", "str"), attr("years_experience", "int"), attr("rating", "str"),
    ],
    "Nurse": [
        attr("nurse_id", "str"), attr("first_name", "str"), attr("last_name", "str"),
        attr("department_id", "str"), attr("phone", "str"), attr("email", "str"),
        attr("shift", "str"), attr("is_available", "bool"),
    ],
    "Staff": [
        attr("staff_id", "str"), attr("first_name", "str"), attr("last_name", "str"),
        attr("role", "str"), attr("department_id", "str"), attr("phone", "str"),
        attr("email", "str"), attr("is_active", "bool"),
    ],
    "Appointment": [
        attr("appointment_id", "str"), attr("patient_id", "str"), attr("doctor_id", "str"),
        attr("time", "str"), attr("status", "str"), attr("reason", "str"), attr("notes", "str"),
    ],
    "MedicalRecord": [
        attr("record_id", "str"), attr("patient_id", "str"), attr("doctor_id", "str"),
        attr("appointment_id", "str"), attr("diagnosis", "str"), attr("symptoms", "str"),
        attr("treatment_plan", "str"), attr("notes", "str"),
    ],
    "LabTest": [
        attr("test_id", "str"), attr("patient_id", "str"), attr("doctor_id", "str"),
        attr("test_name", "str"), attr("test_type", "str"), attr("status", "str"),
        attr("result", "str"), attr("notes", "str"),
    ],
    "Prescription": [
        attr("prescription_id", "str"), attr("record_id", "str"), attr("patient_id", "str"),
        attr("doctor_id", "str"), attr("medication_id", "str"), attr("medication_name", "str"),
        attr("dosage", "str"), attr("frequency", "str"), attr("duration", "str"), attr("notes", "str"),
    ],
    "Admission": [
        attr("admission_id", "str"), attr("patient_id", "str"), attr("room_id", "str"),
        attr("doctor_id", "str"), attr("reason", "str"), attr("status", "str"), attr("total_cost", "str"),
    ],
    "Bill": [
        attr("bill_id", "str"), attr("patient_id", "str"), attr("appointment_id", "str"),
        attr("admission_id", "str"), attr("total_amount", "str"), attr("paid_amount", "str"),
        attr("balance", "str"), attr("payment_status", "str"),
    ],
    "Payment": [
        attr("payment_id", "str"), attr("bill_id", "str"), attr("patient_id", "str"),
        attr("amount", "str"), attr("payment_method", "str"), attr("status", "str"), attr("transaction_id", "str"),
    ],
    "Medication": [
        attr("medication_id", "str"), attr("name", "str"), attr("generic_name", "str"),
        attr("category", "str"), attr("unit", "str"), attr("stock_quantity", "int"),
        attr("price", "str"), attr("requires_prescription", "bool"),
    ],
}

POSITIONS = {
    "Department": (40, 40),
    "Room": (380, 40),
    "Doctor": (720, 40),
    "Nurse": (1060, 40),
    "Staff": (1400, 40),
    "Patient": (40, 330),
    "Appointment": (380, 330),
    "MedicalRecord": (720, 330),
    "Prescription": (1060, 330),
    "Medication": (1400, 330),
    "Admission": (380, 650),
    "LabTest": (720, 650),
    "Bill": (1060, 650),
    "Payment": (1400, 650),
}

RELATIONS = [
    ("Department", "Room", "contains", "1", "*"),
    ("Department", "Doctor", "employs", "1", "*"),
    ("Department", "Nurse", "employs", "1", "*"),
    ("Department", "Staff", "employs", "1", "*"),
    ("Patient", "Appointment", "books", "1", "*"),
    ("Doctor", "Appointment", "attends", "1", "*"),
    ("Appointment", "MedicalRecord", "produces", "1", "0..1"),
    ("Patient", "MedicalRecord", "has", "1", "*"),
    ("Doctor", "MedicalRecord", "writes", "1", "*"),
    ("MedicalRecord", "Prescription", "includes", "1", "*"),
    ("Prescription", "Medication", "references", "*", "1"),
    ("Patient", "LabTest", "has", "1", "*"),
    ("Doctor", "LabTest", "orders", "1", "*"),
    ("Patient", "Admission", "has", "1", "*"),
    ("Doctor", "Admission", "requests", "1", "*"),
    ("Admission", "Room", "assigned room", "*", "1"),
    ("Appointment", "Bill", "billed by", "0..1", "0..1"),
    ("Admission", "Bill", "billed by", "0..1", "0..1"),
    ("Patient", "Bill", "receives", "1", "*"),
    ("Bill", "Payment", "paid by", "1", "*"),
    ("Patient", "Payment", "makes", "1", "*"),
]

ACTOR_IDS = {
    "Receptionist": "50a1a1a1-1111-4aaa-8001-000000000001",
    "Patient": "50a1a1a1-1111-4aaa-8001-000000000002",
    "Doctor": "50a1a1a1-1111-4aaa-8001-000000000003",
    "Nurse": "50a1a1a1-1111-4aaa-8001-000000000004",
    "System": "50a1a1a1-1111-4aaa-8001-000000000005",
}

ACTIVITY_SEMANTICS = {
    "c1a1a1a1-1111-4aaa-8001-000000000002": (
        "Receptionist",
        ["Patient"],
        "Patient arrives or is created at reception",
        "Patient registration is recorded",
    ),
    "c1a1a1a1-1111-4aaa-8001-000000000006": (
        "Nurse",
        ["Patient", "Appointment", "MedicalRecord"],
        "Patient is waiting for triage",
        "Triage information is available",
    ),
    "c1a1a1a1-1111-4aaa-8001-000000000011": (
        "Nurse",
        ["Patient", "Appointment", "MedicalRecord"],
        "Patient is waiting for vitals",
        "Vitals are recorded in the medical record",
    ),
    "c1a1a1a1-1111-4aaa-8001-000000000008": (
        "Doctor",
        ["Patient", "Appointment", "MedicalRecord"],
        "Patient has completed triage",
        "Doctor examination notes are recorded",
    ),
    "c1a1a1a1-1111-4aaa-8001-000000000012": (
        "Doctor",
        ["Patient", "Appointment", "MedicalRecord", "Prescription", "Medication"],
        "Doctor has examined the patient",
        "Diagnosis and prescription are recorded",
    ),
    "c1a1a1a1-1111-4aaa-8001-000000000020": (
        "Doctor",
        ["Patient", "Appointment", "MedicalRecord", "LabTest"],
        "Additional investigation is required",
        "Lab tests are requested",
    ),
    "c1a1a1a1-1111-4aaa-8001-000000000018": (
        "System",
        ["Patient", "Appointment", "Admission", "Bill"],
        "Patient flow has reached discharge notification",
        "Discharge notification is sent",
    ),
}

USECASE_SEMANTICS = {
    "60a1a1a1-1111-4aaa-8001-000000000002": (
        ["Receptionist"],
        ["Patient"],
        ["c1a1a1a1-1111-4aaa-8001-000000000002"],
        "Register a patient arriving at the hospital",
        "Patient registration exists",
    ),
    "60a1a1a1-1111-4aaa-8001-000000000003": (
        ["Receptionist"],
        ["Patient", "Doctor", "Appointment"],
        [],
        "Choose doctor and appointment details",
        "Appointment is scheduled",
    ),
    "60a1a1a1-1111-4aaa-8001-000000000004": (
        ["Doctor"],
        ["Patient", "Appointment", "MedicalRecord"],
        ["c1a1a1a1-1111-4aaa-8001-000000000008", "c1a1a1a1-1111-4aaa-8001-000000000012"],
        "Patient is ready for diagnosis",
        "Diagnosis is recorded",
    ),
    "60a1a1a1-1111-4aaa-8001-000000000005": (
        ["Doctor"],
        ["Patient", "MedicalRecord", "Prescription", "Medication"],
        ["c1a1a1a1-1111-4aaa-8001-000000000012"],
        "Diagnosis requires medication",
        "Prescription is created",
    ),
    "60a1a1a1-1111-4aaa-8001-000000000006": (
        ["Doctor"],
        ["Patient", "Appointment", "MedicalRecord"],
        ["c1a1a1a1-1111-4aaa-8001-000000000011", "c1a1a1a1-1111-4aaa-8001-000000000012"],
        "Clinical information is available",
        "Medical record is updated",
    ),
    "60a1a1a1-1111-4aaa-8001-000000000007": (
        ["Patient", "Doctor"],
        ["Patient", "LabTest"],
        [],
        "Lab test exists",
        "Lab result is visible",
    ),
    "60a1a1a1-1111-4aaa-8001-000000000008": (
        ["Doctor", "Nurse"],
        ["Patient", "Admission", "Bill"],
        ["c1a1a1a1-1111-4aaa-8001-000000000018"],
        "Patient is ready for discharge",
        "Discharge is completed",
    ),
    "60a1a1a1-1111-4aaa-8001-000000000009": (
        ["Nurse"],
        ["Patient", "Appointment", "MedicalRecord"],
        ["c1a1a1a1-1111-4aaa-8001-000000000011"],
        "Patient is ready for vitals",
        "Vitals are recorded",
    ),
}


system = System.objects.get(id=SYSTEM_ID)
diagram = Diagram.objects.get(id=DIAGRAM_ID)

classifiers = {}
for name, classifier_id in CLASS_IDS.items():
    data = {
        "name": name,
        "type": "class",
        "leaf": False,
        "abstract": False,
        "namespace": "",
        "methods": [],
        "attributes": CLASS_ATTRIBUTES[name],
    }
    classifier, _ = Classifier.objects.update_or_create(
        id=classifier_id,
        defaults={"project_id": PROJECT_ID, "system": system, "original_system_id": SYSTEM_ID, "data": data},
    )
    classifiers[name] = classifier

for name, classifier in classifiers.items():
    x, y = POSITIONS[name]
    Node.objects.update_or_create(
        diagram=diagram,
        cls=classifier,
        defaults={"data": {"position": {"x": x, "y": y}}},
    )

for idx, (source, target, label, source_mult, target_mult) in enumerate(RELATIONS, 1):
    relation_id = f"f2a1a1a1-2222-4aaa-8001-{idx:012d}"
    relation, _ = Relation.objects.update_or_create(
        id=relation_id,
        defaults={
            "system": system,
            "source": classifiers[source],
            "target": classifiers[target],
            "data": {
                "type": "association",
                "label": label,
                "labels": None,
                "derived": False,
                "multiplicity": {"source": source_mult, "target": target_mult},
                "position_handlers": [],
            },
        },
    )
    Edge.objects.update_or_create(
        id=f"e2a1a1a1-2222-4aaa-8001-{idx:012d}",
        defaults={"diagram": diagram, "rel": relation, "data": {}},
    )

valid_class_ids = {classifier.id for classifier in classifiers.values()} | {
    classifier.id for classifier in Classifier.objects.filter(system=system, data__type="enum")
}
diagram.nodes.exclude(cls_id__in=valid_class_ids).delete()

valid_relation_ids = {
    relation.id for relation in Relation.objects.filter(id__startswith="f2a1a1a1-2222-4aaa-8001-")
}
diagram.edges.exclude(rel_id__in=valid_relation_ids).exclude(rel__target__data__type="enum").delete()

print(
    f"Fixed {diagram.name}: "
    f"{diagram.nodes.count()} nodes, {diagram.edges.count()} edges, "
    f"{Classifier.objects.filter(system=system, data__type='class').count()} classes."
)

for action_id, (actor_name, class_names, precondition, postcondition) in ACTIVITY_SEMANTICS.items():
    action = Classifier.objects.get(id=action_id, system=system)
    data = dict(action.data or {})
    data.update(
        {
            "type": "action",
            "role": "action",
            "actorNode": ACTOR_IDS[actor_name],
            "actorNodeName": actor_name,
            "classes": [CLASS_IDS[name] for name in class_names],
            "localPrecondition": precondition,
            "localPostcondition": postcondition,
        }
    )
    action.data = data
    action.save(update_fields=["data"])

for usecase_id, (actor_names, class_names, action_ids, precondition, postcondition) in USECASE_SEMANTICS.items():
    usecase = Classifier.objects.get(id=usecase_id, system=system)
    data = dict(usecase.data or {})
    data.update(
        {
            "type": "usecase",
            "actors": [ACTOR_IDS[name] for name in actor_names],
            "classes": [CLASS_IDS[name] for name in class_names],
            "actions": action_ids,
            "precondition": precondition,
            "postcondition": postcondition,
            "scenarios": data.get("scenarios") or [],
            "application_model": data.get("application_model") or [],
        }
    )
    usecase.data = data
    usecase.save(update_fields=["data"])

print(f"Fixed activity semantics: {len(ACTIVITY_SEMANTICS)} actions.")
print(f"Fixed usecase semantics: {len(USECASE_SEMANTICS)} use cases.")
