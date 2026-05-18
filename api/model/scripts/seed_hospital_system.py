"""
Hospital Management System — full seed script.

Creates from scratch:
  1 Project + 1 System
  14 Classes  |  3 Actors
  Activity nodes: 3 Initial + 3 Final + 16 Action nodes
  21 Use-case nodes
  Relations: 16 class associations + 19 activity control-flow + 21 use-case interactions
  5 Diagrams (class, 3× activity, 1 use-case)
  3 Interfaces: Patient · Doctor · Admin

Run inside the API container:
  python /usr/src/model/scripts/seed_hospital_system.py
"""

import os, sys, uuid

sys.path.insert(0, '/usr/src/model')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'model.settings')

import django
django.setup()

from metadata.models import Project, System, Classifier, Relation, Interface
from diagram.models import Diagram, Node, Edge

# ─── Namespace ────────────────────────────────────────────────────────────────
NS = uuid.UUID('4f53a4d0-cafe-5000-beef-a05510140001')

def sid(*parts):
    return str(uuid.uuid5(NS, ':'.join(str(p) for p in parts)))

# ─── Helpers ──────────────────────────────────────────────────────────────────
def a(name, type_='str', derived=False, enum=None):
    return {'name': name, 'type': type_, 'derived': derived, 'enum': enum}

def ops(create=False, update=False, delete=False):
    return {'create': create, 'update': update, 'delete': delete}

def style(color, density='normal', card_style='elevated', columns='3',
          radius='xl', image_position='top', image_size='md'):
    return {
        'color': color, 'density': density, 'card_style': card_style,
        'columns': columns, 'radius': radius,
        'image_position': image_position, 'image_size': image_size,
    }

def sec(actor, name, class_id, layout, col_span, color, attributes,
        operations=None, query=None, density='normal', columns='3',
        card_style='elevated', radius='xl', text='',
        image_position='top', image_size='md',
        view_detail_page=None, related_to=None, relation_field=None, methods=None):
    out = {
        'id': sid(actor, 'section', name),
        'name': name,
        'class': class_id,
        'layout': layout,
        'col_span': col_span,
        'text': text,
        'style': style(color, density=density, card_style=card_style, columns=columns,
                       radius=radius, image_position=image_position, image_size=image_size),
        'attributes': attributes,
        'operations': operations or ops(),
    }
    if query:             out['query'] = query
    if view_detail_page:  out['view_detail_page'] = view_detail_page
    if related_to:        out['related_to'] = related_to
    if relation_field:    out['relation_field'] = relation_field
    if methods:           out['methods'] = methods
    return out

def opt(label, value):
    return {'label': label, 'value': value}

def page(actor, name, sections, type_='normal', single_record=False,
         layout='vertical', gap='normal', category=None, action=None):
    return {
        'id': sid(actor, 'page', name).replace('-', ''),
        'name': name,
        'type': opt(type_.title(), type_),
        'layout': opt(layout.title(), layout),
        'gap': opt(gap.title(), gap),
        'category': category,
        'action': action,
        'single_record': single_record,
        'sections': [{'label': s['name'], 'value': s['id']} for s in sections],
    }

def pcat(class_id, class_name):
    return {'label': class_name, 'value': {'id': class_id, 'name': class_name}}

def act_action(node_id, name):
    return {'label': name, 'value': node_id}

CF = {'type': 'controlflow', 'guard': '', 'weight': '',
      'condition': None, 'is_directed': True, 'position_handlers': []}

def assoc(mult_s, mult_t, label=''):
    return {'type': 'association', 'label': label, 'navigable': True, 'is_directed': True,
            'multiplicity': {'source': mult_s, 'target': mult_t}}

def upsert_classifier(project, system, cls_id, data):
    obj, created = Classifier.objects.update_or_create(
        id=cls_id,
        defaults={'project': project, 'system': system, 'data': data},
    )
    return obj

def upsert_relation(system, rel_id, source, target, data):
    obj, _ = Relation.objects.update_or_create(
        id=rel_id,
        defaults={'system': system, 'source': source, 'target': target, 'data': data},
    )
    return obj

def upsert_node(diagram, cls_obj, node_id, x, y):
    obj, _ = Node.objects.update_or_create(
        id=node_id,
        defaults={'diagram': diagram, 'cls': cls_obj, 'data': {'position': {'x': x, 'y': y}}},
    )
    return obj

def upsert_edge(diagram, rel_obj, edge_id):
    obj, _ = Edge.objects.update_or_create(
        id=edge_id,
        defaults={'diagram': diagram, 'rel': rel_obj, 'data': {}},
    )
    return obj

# ═══════════════════════════════════════════════════════════════════════════════
# STABLE IDs
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ID = 'a1000001-0000-5000-8000-000000000000'
SYSTEM_ID  = 'a2000001-0000-5000-8000-000000000000'

# Classes
C = {
    'Patient':      'c1000001-0000-5000-8000-000000000000',
    'Doctor':       'c1000002-0000-5000-8000-000000000000',
    'Appointment':  'c1000003-0000-5000-8000-000000000000',
    'Department':   'c1000004-0000-5000-8000-000000000000',
    'MedicalRecord':'c1000005-0000-5000-8000-000000000000',
    'Prescription': 'c1000006-0000-5000-8000-000000000000',
    'LabTest':      'c1000007-0000-5000-8000-000000000000',
    'Bill':         'c1000008-0000-5000-8000-000000000000',
    'Payment':      'c1000009-0000-5000-8000-000000000000',
    'Room':         'c1000010-0000-5000-8000-000000000000',
    'Admission':    'c1000011-0000-5000-8000-000000000000',
    'Nurse':        'c1000012-0000-5000-8000-000000000000',
    'Medication':   'c1000013-0000-5000-8000-000000000000',
    'Staff':        'c1000014-0000-5000-8000-000000000000',
}

# Actors
A = {
    'Patient': 'b1000001-0000-5000-8000-000000000000',
    'Doctor':  'b1000002-0000-5000-8000-000000000000',
    'Admin':   'b1000003-0000-5000-8000-000000000000',
}

# Activity control nodes (Initial + Final per actor)
CTRL = {
    'InitPatient':  'f1000001-0000-5000-8000-000000000000',
    'FinalPatient': 'f1000002-0000-5000-8000-000000000000',
    'InitDoctor':   'f1000003-0000-5000-8000-000000000000',
    'FinalDoctor':  'f1000004-0000-5000-8000-000000000000',
    'InitAdmin':    'f1000005-0000-5000-8000-000000000000',
    'FinalAdmin':   'f1000006-0000-5000-8000-000000000000',
}

# Patient activity actions
PAC = {
    'SearchDoctor':       'ac100001-0000-5000-8000-000000000000',
    'BookAppointment':    'ac100002-0000-5000-8000-000000000000',
    'ConfirmAppointment': 'ac100003-0000-5000-8000-000000000000',
    'ViewLabResults':     'ac100004-0000-5000-8000-000000000000',
    'PayBill':            'ac100005-0000-5000-8000-000000000000',
    'SelectPayment':      'ac100006-0000-5000-8000-000000000000',
    'ConfirmPayment':     'ac100007-0000-5000-8000-000000000000',
}

# Doctor activity actions
DAC = {
    'ViewSchedule':      'ac200001-0000-5000-8000-000000000000',
    'ViewPatientRecord': 'ac200002-0000-5000-8000-000000000000',
    'WriteDiagnosis':    'ac200003-0000-5000-8000-000000000000',
    'IssuePrescription': 'ac200004-0000-5000-8000-000000000000',
    'OrderLabTest':      'ac200005-0000-5000-8000-000000000000',
}

# Admin activity actions
AAC = {
    'RegisterAdmission': 'ac300001-0000-5000-8000-000000000000',
    'AssignRoom':        'ac300002-0000-5000-8000-000000000000',
    'ConfirmAdmission':  'ac300003-0000-5000-8000-000000000000',
    'ProcessDischarge':  'ac300004-0000-5000-8000-000000000000',
}

# Use cases
PUC = {
    'BookAppointment':   'ec100001-0000-5000-8000-000000000000',
    'CancelAppointment': 'ec100002-0000-5000-8000-000000000000',
    'ViewMedicalRecord': 'ec100003-0000-5000-8000-000000000000',
    'ViewLabResults':    'ec100004-0000-5000-8000-000000000000',
    'ViewBill':          'ec100005-0000-5000-8000-000000000000',
    'PayBill':           'ec100006-0000-5000-8000-000000000000',
    'ViewAdmission':     'ec100007-0000-5000-8000-000000000000',
    'UpdateProfile':     'ec100008-0000-5000-8000-000000000000',
}
DUC = {
    'ViewSchedule':      'ec200001-0000-5000-8000-000000000000',
    'ViewPatientRecord': 'ec200002-0000-5000-8000-000000000000',
    'WriteDiagnosis':    'ec200003-0000-5000-8000-000000000000',
    'IssuePrescription': 'ec200004-0000-5000-8000-000000000000',
    'OrderLabTest':      'ec200005-0000-5000-8000-000000000000',
}
AUC = {
    'ManagePatients':    'ec300001-0000-5000-8000-000000000000',
    'ManageDoctors':     'ec300002-0000-5000-8000-000000000000',
    'RegisterAdmission': 'ec300003-0000-5000-8000-000000000000',
    'AssignRoom':        'ec300004-0000-5000-8000-000000000000',
    'ProcessDischarge':  'ec300005-0000-5000-8000-000000000000',
    'ManageBilling':     'ec300006-0000-5000-8000-000000000000',
    'ManageStaff':       'ec300007-0000-5000-8000-000000000000',
    'ManageMedication':  'ec300008-0000-5000-8000-000000000000',
}

# Diagrams
D = {
    'Class':        'd1000001-0000-5000-8000-000000000000',
    'PatientAct':   'd1000002-0000-5000-8000-000000000000',
    'DoctorAct':    'd1000003-0000-5000-8000-000000000000',
    'AdminAct':     'd1000004-0000-5000-8000-000000000000',
    'Usecase':      'd1000005-0000-5000-8000-000000000000',
}

# Interfaces
I = {
    'Patient': 'e9000001-0000-5000-8000-000000000000',
    'Doctor':  'e9000002-0000-5000-8000-000000000000',
    'Admin':   'e9000003-0000-5000-8000-000000000000',
}

# ═══════════════════════════════════════════════════════════════════════════════
# 1. PROJECT + SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
print('── Project + System ─────────────────────────────────────────────────────')

project, _ = Project.objects.update_or_create(
    id=PROJECT_ID,
    defaults={'name': 'Hospital Management System', 'description': 'Full hospital management system demo'},
)
system, _ = System.objects.update_or_create(
    id=SYSTEM_ID,
    defaults={'project': project, 'name': 'Hospital', 'description': 'Core hospital domain system'},
)
print(f'  Project: {project.name}')
print(f'  System:  {system.name}')

# ═══════════════════════════════════════════════════════════════════════════════
# 2. CLASSES
# ═══════════════════════════════════════════════════════════════════════════════
print('\n── Classes ──────────────────────────────────────────────────────────────')

classes_data = {
    'Patient': {
        'type': 'class', 'name': 'Patient', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('patient_id'), a('first_name'), a('last_name'),
            a('date_of_birth', 'datetime'), a('gender'), a('blood_type'),
            a('phone'), a('email'), a('address'),
            a('emergency_contact'), a('insurance_number'),
            a('is_active', 'bool'), a('registered_at', 'datetime'),
        ],
    },
    'Doctor': {
        'type': 'class', 'name': 'Doctor', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('doctor_id'), a('first_name'), a('last_name'),
            a('specialization'), a('department_id'),
            a('phone'), a('email'), a('license_number'),
            a('is_available', 'bool'), a('consultation_fee', 'str'),
            a('years_experience', 'int'), a('rating', 'str'),
        ],
    },
    'Appointment': {
        'type': 'class', 'name': 'Appointment', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('appointment_id'), a('patient_id'), a('doctor_id'),
            a('date', 'datetime'), a('time'), a('status'),
            a('reason'), a('notes'), a('created_at', 'datetime'),
        ],
    },
    'Department': {
        'type': 'class', 'name': 'Department', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('department_id'), a('name'), a('description'),
            a('head_doctor_id'), a('floor', 'int'), a('phone'),
        ],
    },
    'MedicalRecord': {
        'type': 'class', 'name': 'MedicalRecord', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('record_id'), a('patient_id'), a('doctor_id'), a('appointment_id'),
            a('diagnosis'), a('symptoms'), a('treatment_plan'),
            a('notes'), a('created_at', 'datetime'),
        ],
    },
    'Prescription': {
        'type': 'class', 'name': 'Prescription', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('prescription_id'), a('record_id'), a('patient_id'), a('doctor_id'),
            a('medication_name'), a('dosage'), a('frequency'),
            a('duration'), a('notes'), a('issued_at', 'datetime'),
        ],
    },
    'LabTest': {
        'type': 'class', 'name': 'LabTest', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('test_id'), a('patient_id'), a('doctor_id'),
            a('test_name'), a('test_type'), a('status'),
            a('result'), a('result_date', 'datetime'),
            a('notes'), a('ordered_at', 'datetime'),
        ],
    },
    'Bill': {
        'type': 'class', 'name': 'Bill', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('bill_id'), a('patient_id'), a('appointment_id'),
            a('total_amount', 'str'), a('paid_amount', 'str'),
            a('balance', 'str', derived=True), a('payment_status'),
            a('due_date', 'datetime'), a('created_at', 'datetime'),
        ],
    },
    'Payment': {
        'type': 'class', 'name': 'Payment', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('payment_id'), a('bill_id'), a('patient_id'),
            a('amount', 'str'), a('payment_method'), a('status'),
            a('transaction_id'), a('paid_at', 'datetime'),
        ],
    },
    'Room': {
        'type': 'class', 'name': 'Room', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('room_id'), a('department_id'), a('room_number'),
            a('type'), a('capacity', 'int'),
            a('is_available', 'bool'), a('floor', 'int'),
        ],
    },
    'Admission': {
        'type': 'class', 'name': 'Admission', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('admission_id'), a('patient_id'), a('room_id'), a('doctor_id'),
            a('admission_date', 'datetime'), a('discharge_date', 'datetime'),
            a('reason'), a('status'), a('total_cost', 'str'),
        ],
    },
    'Nurse': {
        'type': 'class', 'name': 'Nurse', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('nurse_id'), a('first_name'), a('last_name'),
            a('department_id'), a('phone'), a('email'),
            a('shift'), a('is_available', 'bool'),
        ],
    },
    'Medication': {
        'type': 'class', 'name': 'Medication', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('medication_id'), a('name'), a('generic_name'),
            a('category'), a('unit'), a('stock_quantity', 'int'),
            a('price', 'str'), a('expiry_date', 'datetime'),
            a('requires_prescription', 'bool'),
        ],
    },
    'Staff': {
        'type': 'class', 'name': 'Staff', 'abstract': False, 'leaf': False, 'namespace': '', 'methods': [],
        'attributes': [
            a('staff_id'), a('first_name'), a('last_name'),
            a('role'), a('department_id'),
            a('phone'), a('email'), a('is_active', 'bool'),
        ],
    },
}

cls_objs = {}
for name, data in classes_data.items():
    obj = upsert_classifier(project, system, C[name], data)
    cls_objs[name] = obj
    print(f'  class {name}')

# ═══════════════════════════════════════════════════════════════════════════════
# 3. ACTORS + ACTIVITY NODES + USE-CASE NODES
# ═══════════════════════════════════════════════════════════════════════════════
print('\n── Actors ───────────────────────────────────────────────────────────────')

actor_objs = {}
for actor_name, actor_id in A.items():
    obj = upsert_classifier(project, system, actor_id, {'type': 'actor', 'name': actor_name, 'namespace': ''})
    actor_objs[actor_name] = obj
    print(f'  actor {actor_name}')

print('\n── Activity control nodes ────────────────────────────────────────────────')

ctrl_objs = {}
ctrl_data = {
    'InitPatient':  {'type': 'initial', 'role': 'control', 'activity_scope': 'activity', 'scheduled': False, 'schedule': ''},
    'FinalPatient': {'type': 'final',   'role': 'control', 'activity_scope': 'activity'},
    'InitDoctor':   {'type': 'initial', 'role': 'control', 'activity_scope': 'activity', 'scheduled': False, 'schedule': ''},
    'FinalDoctor':  {'type': 'final',   'role': 'control', 'activity_scope': 'activity'},
    'InitAdmin':    {'type': 'initial', 'role': 'control', 'activity_scope': 'activity', 'scheduled': False, 'schedule': ''},
    'FinalAdmin':   {'type': 'final',   'role': 'control', 'activity_scope': 'activity'},
}
for key, data in ctrl_data.items():
    obj = upsert_classifier(project, system, CTRL[key], data)
    ctrl_objs[key] = obj

print('  InitPatient, FinalPatient, InitDoctor, FinalDoctor, InitAdmin, FinalAdmin')

print('\n── Activity action nodes ────────────────────────────────────────────────')

def action_data(name, actor_key, classes):
    return {
        'type': 'action', 'role': 'action', 'name': name, 'namespace': '',
        'isAutomatic': False, 'customCode': None, 'body': '',
        'localPrecondition': '', 'localPostcondition': '',
        'classes': classes, 'application_models': None, 'page': None,
        'actorNode': A[actor_key], 'actorNodeName': actor_key,
        'publish': None, 'subscribe': None, 'operation': None,
    }

pac_objs, dac_objs, aac_objs = {}, {}, {}

patient_actions = [
    ('SearchDoctor',       'Search Doctor',        ['Patient', 'Doctor', 'Department']),
    ('BookAppointment',    'Book Appointment',     ['Patient', 'Doctor', 'Appointment']),
    ('ConfirmAppointment', 'Confirm Appointment',  ['Appointment']),
    ('ViewLabResults',     'View Lab Results',     ['LabTest']),
    ('PayBill',            'Pay Bill',             ['Bill', 'Payment']),
    ('SelectPayment',      'Select Payment Method',['Payment']),
    ('ConfirmPayment',     'Confirm Payment',      ['Payment', 'Bill']),
]
for key, name, classes in patient_actions:
    obj = upsert_classifier(project, system, PAC[key], action_data(name, 'Patient', classes))
    pac_objs[key] = obj
    print(f'  P: {name}')

doctor_actions = [
    ('ViewSchedule',      'View Today Schedule',  ['Appointment', 'Doctor']),
    ('ViewPatientRecord', 'View Patient Record',  ['Patient', 'MedicalRecord']),
    ('WriteDiagnosis',    'Write Diagnosis',      ['MedicalRecord', 'Appointment']),
    ('IssuePrescription', 'Issue Prescription',   ['Prescription', 'Medication']),
    ('OrderLabTest',      'Order Lab Test',       ['LabTest', 'Patient']),
]
for key, name, classes in doctor_actions:
    obj = upsert_classifier(project, system, DAC[key], action_data(name, 'Doctor', classes))
    dac_objs[key] = obj
    print(f'  D: {name}')

admin_actions = [
    ('RegisterAdmission', 'Register Admission',   ['Admission', 'Patient', 'Doctor']),
    ('AssignRoom',        'Assign Room',          ['Room', 'Admission']),
    ('ConfirmAdmission',  'Confirm Admission',    ['Admission']),
    ('ProcessDischarge',  'Process Discharge',    ['Admission', 'Bill']),
]
for key, name, classes in admin_actions:
    obj = upsert_classifier(project, system, AAC[key], action_data(name, 'Admin', classes))
    aac_objs[key] = obj
    print(f'  A: {name}')

print('\n── Use-case nodes ────────────────────────────────────────────────────────')

def uc_data(name, pre='', post=''):
    return {'type': 'usecase', 'name': name, 'namespace': '', 'precondition': pre, 'postcondition': post,
            'trigger': '', 'scenarios': [], 'activities': [], 'actions': [], 'classes': [], 'application_model': []}

uc_objs = {}
usecases = [
    # Patient
    (PUC['BookAppointment'],   uc_data('Book Appointment',   'Patient is logged in', 'Appointment is scheduled')),
    (PUC['CancelAppointment'], uc_data('Cancel Appointment', 'Appointment is scheduled', 'Appointment is cancelled')),
    (PUC['ViewMedicalRecord'], uc_data('View Medical Record','Patient is logged in', 'Patient views record')),
    (PUC['ViewLabResults'],    uc_data('View Lab Results',   'Lab test is completed', 'Patient views results')),
    (PUC['ViewBill'],          uc_data('View Bill',          'Patient is logged in', 'Patient views bill')),
    (PUC['PayBill'],           uc_data('Pay Bill',           'Bill is pending', 'Payment is completed')),
    (PUC['ViewAdmission'],     uc_data('View Admission Status','Patient is admitted', 'Patient views admission')),
    (PUC['UpdateProfile'],     uc_data('Update Profile',     'Patient is logged in', 'Profile is updated')),
    # Doctor
    (DUC['ViewSchedule'],      uc_data('View Schedule',      'Doctor is logged in', 'Doctor sees today\'s appointments')),
    (DUC['ViewPatientRecord'], uc_data('View Patient Record','Patient appointment is confirmed', 'Doctor views record')),
    (DUC['WriteDiagnosis'],    uc_data('Write Diagnosis',    'Consultation is in progress', 'Diagnosis is recorded')),
    (DUC['IssuePrescription'], uc_data('Issue Prescription', 'Diagnosis is recorded', 'Prescription is issued')),
    (DUC['OrderLabTest'],      uc_data('Order Lab Test',     'Doctor decides test is needed', 'Lab test is ordered')),
    # Admin
    (AUC['ManagePatients'],    uc_data('Manage Patients',    'Admin is logged in', 'Patient records are managed')),
    (AUC['ManageDoctors'],     uc_data('Manage Doctors',     'Admin is logged in', 'Doctor records are managed')),
    (AUC['RegisterAdmission'], uc_data('Register Admission', 'Doctor orders admission', 'Admission is registered')),
    (AUC['AssignRoom'],        uc_data('Assign Room',        'Admission is registered', 'Room is assigned')),
    (AUC['ProcessDischarge'],  uc_data('Process Discharge',  'Doctor writes discharge summary', 'Patient is discharged')),
    (AUC['ManageBilling'],     uc_data('Manage Billing',     'Admin is logged in', 'Bills are managed')),
    (AUC['ManageStaff'],       uc_data('Manage Staff',       'Admin is logged in', 'Staff records are managed')),
    (AUC['ManageMedication'],  uc_data('Manage Medication Stock','Admin is logged in', 'Inventory is updated')),
]
for uc_id, data in usecases:
    obj = upsert_classifier(project, system, uc_id, data)
    uc_objs[uc_id] = obj
    print(f'  usecase {data["name"]}')

# ═══════════════════════════════════════════════════════════════════════════════
# 4. RELATIONS
# ═══════════════════════════════════════════════════════════════════════════════
print('\n── Class associations ────────────────────────────────────────────────────')

class_relations = [
    ('Patient',       'Appointment',   '1', '0..*', 'has'),
    ('Doctor',        'Appointment',   '1', '0..*', 'conducts'),
    ('Appointment',   'MedicalRecord', '1', '0..1', 'generates'),
    ('MedicalRecord', 'Prescription',  '1', '0..*', 'contains'),
    ('MedicalRecord', 'LabTest',       '1', '0..*', 'orders'),
    ('Patient',       'Bill',          '1', '0..*', 'owes'),
    ('Bill',          'Payment',       '1', '0..*', 'settled by'),
    ('Patient',       'Admission',     '1', '0..*', 'admitted via'),
    ('Room',          'Admission',     '1', '0..*', 'hosts'),
    ('Doctor',        'Admission',     '1', '0..*', 'oversees'),
    ('Department',    'Doctor',        '1', '0..*', 'employs'),
    ('Department',    'Nurse',         '1', '0..*', 'staffed by'),
    ('Department',    'Room',          '1', '0..*', 'contains'),
    ('Prescription',  'Medication',    '0..*', '1', 'references'),
    ('Patient',       'MedicalRecord', '1', '0..*', 'has'),
    ('Doctor',        'MedicalRecord', '1', '0..*', 'writes'),
]

class_rel_objs = {}
for src, tgt, ms, mt, label in class_relations:
    rel_id = sid('classrel', src, tgt, label)
    obj = upsert_relation(system, rel_id, cls_objs[src], cls_objs[tgt], assoc(ms, mt, label))
    class_rel_objs[rel_id] = obj
    print(f'  {src} → {tgt}  [{ms}:{mt}]')

print('\n── Activity control-flow relations ──────────────────────────────────────')

# Patient flow: Init→SearchDoctor→Book→Confirm→ViewLab→PayBill→SelectPayment→ConfirmPayment→Final
patient_cf = [
    ('rcf_p01', ctrl_objs['InitPatient'],   pac_objs['SearchDoctor']),
    ('rcf_p02', pac_objs['SearchDoctor'],   pac_objs['BookAppointment']),
    ('rcf_p03', pac_objs['BookAppointment'],pac_objs['ConfirmAppointment']),
    ('rcf_p04', pac_objs['ConfirmAppointment'], pac_objs['ViewLabResults']),
    ('rcf_p05', pac_objs['ViewLabResults'], pac_objs['PayBill']),
    ('rcf_p06', pac_objs['PayBill'],        pac_objs['SelectPayment']),
    ('rcf_p07', pac_objs['SelectPayment'],  pac_objs['ConfirmPayment']),
    ('rcf_p08', pac_objs['ConfirmPayment'], ctrl_objs['FinalPatient']),
]
# Doctor flow: Init→ViewSchedule→ViewPatientRecord→WriteDiagnosis→IssuePrescription→OrderLabTest→Final
doctor_cf = [
    ('rcf_d01', ctrl_objs['InitDoctor'],      dac_objs['ViewSchedule']),
    ('rcf_d02', dac_objs['ViewSchedule'],     dac_objs['ViewPatientRecord']),
    ('rcf_d03', dac_objs['ViewPatientRecord'],dac_objs['WriteDiagnosis']),
    ('rcf_d04', dac_objs['WriteDiagnosis'],   dac_objs['IssuePrescription']),
    ('rcf_d05', dac_objs['IssuePrescription'],dac_objs['OrderLabTest']),
    ('rcf_d06', dac_objs['OrderLabTest'],     ctrl_objs['FinalDoctor']),
]
# Admin flow: Init→RegisterAdmission→AssignRoom→ConfirmAdmission→ProcessDischarge→Final
admin_cf = [
    ('rcf_a01', ctrl_objs['InitAdmin'],       aac_objs['RegisterAdmission']),
    ('rcf_a02', aac_objs['RegisterAdmission'],aac_objs['AssignRoom']),
    ('rcf_a03', aac_objs['AssignRoom'],       aac_objs['ConfirmAdmission']),
    ('rcf_a04', aac_objs['ConfirmAdmission'], aac_objs['ProcessDischarge']),
    ('rcf_a05', aac_objs['ProcessDischarge'], ctrl_objs['FinalAdmin']),
]

act_rel_objs = {}
for rel_id, src, tgt in patient_cf + doctor_cf + admin_cf:
    obj = upsert_relation(system, sid('cf', rel_id), src, tgt, CF)
    act_rel_objs[rel_id] = obj
    print(f'  {src.data.get("name", src.data.get("type","?"))} → {tgt.data.get("name", tgt.data.get("type","?"))}')

print('\n── Use-case interaction relations ────────────────────────────────────────')

uc_interactions = [
    # Patient actor ↔ Patient use cases
    ('uci_p01', actor_objs['Patient'], uc_objs[PUC['BookAppointment']]),
    ('uci_p02', actor_objs['Patient'], uc_objs[PUC['CancelAppointment']]),
    ('uci_p03', actor_objs['Patient'], uc_objs[PUC['ViewMedicalRecord']]),
    ('uci_p04', actor_objs['Patient'], uc_objs[PUC['ViewLabResults']]),
    ('uci_p05', actor_objs['Patient'], uc_objs[PUC['ViewBill']]),
    ('uci_p06', actor_objs['Patient'], uc_objs[PUC['PayBill']]),
    ('uci_p07', actor_objs['Patient'], uc_objs[PUC['ViewAdmission']]),
    ('uci_p08', actor_objs['Patient'], uc_objs[PUC['UpdateProfile']]),
    # Doctor actor ↔ Doctor use cases
    ('uci_d01', actor_objs['Doctor'],  uc_objs[DUC['ViewSchedule']]),
    ('uci_d02', actor_objs['Doctor'],  uc_objs[DUC['ViewPatientRecord']]),
    ('uci_d03', actor_objs['Doctor'],  uc_objs[DUC['WriteDiagnosis']]),
    ('uci_d04', actor_objs['Doctor'],  uc_objs[DUC['IssuePrescription']]),
    ('uci_d05', actor_objs['Doctor'],  uc_objs[DUC['OrderLabTest']]),
    # Admin actor ↔ Admin use cases
    ('uci_a01', actor_objs['Admin'],   uc_objs[AUC['ManagePatients']]),
    ('uci_a02', actor_objs['Admin'],   uc_objs[AUC['ManageDoctors']]),
    ('uci_a03', actor_objs['Admin'],   uc_objs[AUC['RegisterAdmission']]),
    ('uci_a04', actor_objs['Admin'],   uc_objs[AUC['AssignRoom']]),
    ('uci_a05', actor_objs['Admin'],   uc_objs[AUC['ProcessDischarge']]),
    ('uci_a06', actor_objs['Admin'],   uc_objs[AUC['ManageBilling']]),
    ('uci_a07', actor_objs['Admin'],   uc_objs[AUC['ManageStaff']]),
    ('uci_a08', actor_objs['Admin'],   uc_objs[AUC['ManageMedication']]),
]
uc_rel_objs = {}
for rel_id, src, tgt in uc_interactions:
    obj = upsert_relation(system, sid('uci', rel_id), src, tgt,
                          {'type': 'interaction', 'is_directed': True})
    uc_rel_objs[rel_id] = obj
print(f'  {len(uc_interactions)} use-case interaction relations')

# ─── Use-case extension: PayBill extends ViewBill ─────────────────────────────
upsert_relation(system, sid('uci', 'ext01'),
                uc_objs[PUC['PayBill']], uc_objs[PUC['ViewBill']],
                {'type': 'extension', 'is_directed': True})
print('  Extension: PayBill → ViewBill')

# ═══════════════════════════════════════════════════════════════════════════════
# 5. DIAGRAMS
# ═══════════════════════════════════════════════════════════════════════════════
print('\n── Class Diagram ─────────────────────────────────────────────────────────')

diag_class, _ = Diagram.objects.update_or_create(
    id=D['Class'],
    defaults={'type': 'classes', 'name': 'Hospital Class Diagram',
              'description': 'All hospital domain classes', 'system': system},
)

# Grid layout for 14 classes
class_positions = {
    'Patient':       (-500,  -200),
    'Doctor':        (-200,  -200),
    'Department':    ( 100,  -200),
    'Nurse':         ( 400,  -200),
    'Staff':         ( 700,  -200),
    'Appointment':   (-500,     0),
    'MedicalRecord': (-200,     0),
    'Room':          ( 100,     0),
    'Admission':     ( 400,     0),
    'Prescription':  (-500,   200),
    'LabTest':       (-200,   200),
    'Bill':          ( 100,   200),
    'Payment':       ( 400,   200),
    'Medication':    (-500,   400),
}

class_node_objs = {}
for name, (x, y) in class_positions.items():
    node_id = sid('node', 'class', name)
    n = upsert_node(diag_class, cls_objs[name], node_id, x, y)
    class_node_objs[name] = n

for rel_id, obj in class_rel_objs.items():
    upsert_edge(diag_class, obj, sid('edge', 'class', rel_id))

print(f'  {len(class_positions)} nodes, {len(class_rel_objs)} edges')

# ── Patient Activity Diagram ──────────────────────────────────────────────────
print('\n── Patient Activity Diagram ──────────────────────────────────────────────')

diag_p, _ = Diagram.objects.update_or_create(
    id=D['PatientAct'],
    defaults={'type': 'activity', 'name': 'Patient Activity',
              'description': 'Patient appointment and payment flow', 'system': system},
)

p_act_nodes = [
    (ctrl_objs['InitPatient'],          sid('n', 'p', 'init'),    0, -700),
    (pac_objs['SearchDoctor'],          sid('n', 'p', 'sd'),       0, -560),
    (pac_objs['BookAppointment'],       sid('n', 'p', 'ba'),       0, -420),
    (pac_objs['ConfirmAppointment'],    sid('n', 'p', 'ca'),       0, -280),
    (pac_objs['ViewLabResults'],        sid('n', 'p', 'vl'),       0, -140),
    (pac_objs['PayBill'],               sid('n', 'p', 'pb'),       0,    0),
    (pac_objs['SelectPayment'],         sid('n', 'p', 'sp'),       0,  140),
    (pac_objs['ConfirmPayment'],        sid('n', 'p', 'cp'),       0,  280),
    (ctrl_objs['FinalPatient'],         sid('n', 'p', 'fin'),      0,  420),
]
for cls_obj, node_id, x, y in p_act_nodes:
    upsert_node(diag_p, cls_obj, node_id, x, y)

for rel_id, obj in act_rel_objs.items():
    if rel_id.startswith('rcf_p'):
        upsert_edge(diag_p, obj, sid('edge', 'p', rel_id))

print(f'  {len(p_act_nodes)} nodes, 8 edges')

# ── Doctor Activity Diagram ───────────────────────────────────────────────────
print('\n── Doctor Activity Diagram ───────────────────────────────────────────────')

diag_d, _ = Diagram.objects.update_or_create(
    id=D['DoctorAct'],
    defaults={'type': 'activity', 'name': 'Doctor Activity',
              'description': 'Doctor consultation and diagnosis flow', 'system': system},
)

d_act_nodes = [
    (ctrl_objs['InitDoctor'],           sid('n', 'd', 'init'),    0, -560),
    (dac_objs['ViewSchedule'],          sid('n', 'd', 'vs'),       0, -420),
    (dac_objs['ViewPatientRecord'],     sid('n', 'd', 'vpr'),      0, -280),
    (dac_objs['WriteDiagnosis'],        sid('n', 'd', 'wd'),       0, -140),
    (dac_objs['IssuePrescription'],     sid('n', 'd', 'ip'),       0,    0),
    (dac_objs['OrderLabTest'],          sid('n', 'd', 'ol'),       0,  140),
    (ctrl_objs['FinalDoctor'],          sid('n', 'd', 'fin'),      0,  280),
]
for cls_obj, node_id, x, y in d_act_nodes:
    upsert_node(diag_d, cls_obj, node_id, x, y)

for rel_id, obj in act_rel_objs.items():
    if rel_id.startswith('rcf_d'):
        upsert_edge(diag_d, obj, sid('edge', 'd', rel_id))

print(f'  {len(d_act_nodes)} nodes, 6 edges')

# ── Admin Activity Diagram ────────────────────────────────────────────────────
print('\n── Admin Activity Diagram ────────────────────────────────────────────────')

diag_a, _ = Diagram.objects.update_or_create(
    id=D['AdminAct'],
    defaults={'type': 'activity', 'name': 'Admin Activity',
              'description': 'Admission registration and discharge flow', 'system': system},
)

a_act_nodes = [
    (ctrl_objs['InitAdmin'],            sid('n', 'a', 'init'),    0, -420),
    (aac_objs['RegisterAdmission'],     sid('n', 'a', 'ra'),       0, -280),
    (aac_objs['AssignRoom'],            sid('n', 'a', 'ar'),       0, -140),
    (aac_objs['ConfirmAdmission'],      sid('n', 'a', 'ca'),       0,    0),
    (aac_objs['ProcessDischarge'],      sid('n', 'a', 'pd'),       0,  140),
    (ctrl_objs['FinalAdmin'],           sid('n', 'a', 'fin'),      0,  280),
]
for cls_obj, node_id, x, y in a_act_nodes:
    upsert_node(diag_a, cls_obj, node_id, x, y)

for rel_id, obj in act_rel_objs.items():
    if rel_id.startswith('rcf_a'):
        upsert_edge(diag_a, obj, sid('edge', 'a', rel_id))

print(f'  {len(a_act_nodes)} nodes, 5 edges')

# ── Use-case Diagram ──────────────────────────────────────────────────────────
print('\n── Use-case Diagram ──────────────────────────────────────────────────────')

diag_uc, _ = Diagram.objects.update_or_create(
    id=D['Usecase'],
    defaults={'type': 'usecase', 'name': 'Hospital Use-case Diagram',
              'description': 'All actors and use cases', 'system': system},
)

# Actors on left, use cases on right, grouped by actor
uc_positions = [
    # Actors
    (actor_objs['Patient'],  sid('n', 'uc', 'pa'),  -500,  -350),
    (actor_objs['Doctor'],   sid('n', 'uc', 'da'),  -500,   100),
    (actor_objs['Admin'],    sid('n', 'uc', 'aa'),  -500,   500),
    # Patient use cases  (x=100)
    (uc_objs[PUC['BookAppointment']],   sid('n','uc','p1'),  200, -600),
    (uc_objs[PUC['CancelAppointment']], sid('n','uc','p2'),  200, -490),
    (uc_objs[PUC['ViewMedicalRecord']], sid('n','uc','p3'),  200, -380),
    (uc_objs[PUC['ViewLabResults']],    sid('n','uc','p4'),  200, -270),
    (uc_objs[PUC['ViewBill']],          sid('n','uc','p5'),  200, -160),
    (uc_objs[PUC['PayBill']],           sid('n','uc','p6'),  200,  -50),
    (uc_objs[PUC['ViewAdmission']],     sid('n','uc','p7'),  200,   60),
    (uc_objs[PUC['UpdateProfile']],     sid('n','uc','p8'),  200,  170),
    # Doctor use cases  (x=100)
    (uc_objs[DUC['ViewSchedule']],      sid('n','uc','d1'),  200,  300),
    (uc_objs[DUC['ViewPatientRecord']], sid('n','uc','d2'),  200,  390),
    (uc_objs[DUC['WriteDiagnosis']],    sid('n','uc','d3'),  200,  480),
    (uc_objs[DUC['IssuePrescription']], sid('n','uc','d4'),  200,  570),
    (uc_objs[DUC['OrderLabTest']],      sid('n','uc','d5'),  200,  660),
    # Admin use cases  (x=100)
    (uc_objs[AUC['ManagePatients']],    sid('n','uc','a1'),  200,  790),
    (uc_objs[AUC['ManageDoctors']],     sid('n','uc','a2'),  200,  880),
    (uc_objs[AUC['RegisterAdmission']], sid('n','uc','a3'),  200,  970),
    (uc_objs[AUC['AssignRoom']],        sid('n','uc','a4'),  200, 1060),
    (uc_objs[AUC['ProcessDischarge']],  sid('n','uc','a5'),  200, 1150),
    (uc_objs[AUC['ManageBilling']],     sid('n','uc','a6'),  200, 1240),
    (uc_objs[AUC['ManageStaff']],       sid('n','uc','a7'),  200, 1330),
    (uc_objs[AUC['ManageMedication']],  sid('n','uc','a8'),  200, 1420),
]
for cls_obj, node_id, x, y in uc_positions:
    upsert_node(diag_uc, cls_obj, node_id, x, y)

for rel_id, obj in uc_rel_objs.items():
    upsert_edge(diag_uc, obj, sid('edge', 'uc', rel_id))

print(f'  {len(uc_positions)} nodes, {len(uc_rel_objs)+1} edges')

# ═══════════════════════════════════════════════════════════════════════════════
# 6. PATIENT INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════
print('\n── Patient Interface ─────────────────────────────────────────────────────')
PATIENT = 'Patient'

s_upcoming_appt = sec(PATIENT, 'Upcoming Appointments', C['Appointment'], 'card', 12, 'blue',
    [a('date','date'), a('time'), a('doctor_id'), a('status'), a('reason')],
    ops(create=False),
    query={'limit': 3, 'filters': [{'field': 'status', 'operator': 'in', 'value': 'scheduled,confirmed'}],
           'order_by': [{'field': 'date', 'direction': 'asc'}]},
    columns='3', text='Your upcoming visits.')

s_all_appts = sec(PATIENT, 'My Appointments', C['Appointment'], 'table', 12, 'blue',
    [a('date','date'), a('time'), a('doctor_id'), a('status'), a('reason'), a('created_at','datetime')],
    query={'limit': 20, 'order_by': [{'field': 'date', 'direction': 'desc'}]})

s_doctor_list = sec(PATIENT, 'Find a Doctor', C['Doctor'], 'card', 9, 'green',
    [a('first_name'), a('last_name'), a('specialization'), a('consultation_fee','str'),
     a('rating','str'), a('is_available','bool')],
    query={'limit': 12, 'filters': [{'field': 'is_available', 'operator': 'eq', 'value': 'true'}],
           'order_by': [{'field': 'rating', 'direction': 'desc'}]},
    columns='3', view_detail_page='Book Appointment')

s_specialties = sec(PATIENT, 'Specialties', C['Department'], 'list', 3, 'slate',
    [a('name'), a('description')],
    query={'limit': 10, 'order_by': [{'field': 'name', 'direction': 'asc'}]},
    density='compact', card_style='flat')

s_appt_detail = sec(PATIENT, 'Appointment Detail', C['Appointment'], 'detail', 12, 'blue',
    [a('date','date'), a('time'), a('doctor_id'), a('status'), a('reason'), a('notes')],
    ops(update=True), columns='1')

s_med_records = sec(PATIENT, 'Medical Records', C['MedicalRecord'], 'table', 12, 'purple',
    [a('diagnosis'), a('symptoms'), a('created_at','datetime'), a('doctor_id')],
    query={'limit': 10, 'order_by': [{'field': 'created_at', 'direction': 'desc'}]})

s_record_detail = sec(PATIENT, 'Record Detail', C['MedicalRecord'], 'detail', 6, 'purple',
    [a('diagnosis'), a('symptoms'), a('treatment_plan'), a('notes'), a('created_at','datetime')],
    columns='1', card_style='outlined')

s_prescriptions = sec(PATIENT, 'My Prescriptions', C['Prescription'], 'list', 6, 'green',
    [a('medication_name'), a('dosage'), a('frequency'), a('duration'), a('issued_at','datetime')],
    query={'limit': 10, 'order_by': [{'field': 'issued_at', 'direction': 'desc'}]},
    density='compact')

s_lab_tests = sec(PATIENT, 'Lab Test Results', C['LabTest'], 'table', 12, 'orange',
    [a('test_name'), a('test_type'), a('status'), a('result_date','datetime'), a('result')],
    query={'limit': 15, 'order_by': [{'field': 'ordered_at', 'direction': 'desc'}]})

s_lab_detail = sec(PATIENT, 'Lab Test Detail', C['LabTest'], 'detail', 12, 'orange',
    [a('test_name'), a('test_type'), a('status'), a('result'), a('notes'),
     a('ordered_at','datetime'), a('result_date','datetime')],
    columns='1')

s_my_bills = sec(PATIENT, 'My Bills', C['Bill'], 'table', 12, 'rose',
    [a('bill_id'), a('total_amount','str'), a('paid_amount','str'),
     a('balance','str'), a('payment_status'), a('due_date','date')],
    query={'limit': 15, 'order_by': [{'field': 'created_at', 'direction': 'desc'}]},
    view_detail_page='Pay Bill')

s_bill_detail = sec(PATIENT, 'Bill Detail', C['Bill'], 'detail', 8, 'rose',
    [a('bill_id'), a('total_amount','str'), a('paid_amount','str'),
     a('balance','str'), a('payment_status'), a('due_date','date')],
    columns='1', card_style='outlined')

s_pay_method = sec(PATIENT, 'Payment Method', C['Payment'], 'card', 4, 'purple',
    [a('payment_method'), a('amount','str')],
    ops(create=True), columns='1')

s_my_profile = sec(PATIENT, 'My Profile', C['Patient'], 'detail', 12, 'blue',
    [a('first_name'), a('last_name'), a('email'), a('phone'),
     a('date_of_birth','date'), a('gender'), a('blood_type'),
     a('address'), a('emergency_contact')],
    ops(update=True), columns='1')

s_my_admission = sec(PATIENT, 'Admission Status', C['Admission'], 'detail', 8, 'slate',
    [a('admission_date','date'), a('discharge_date','date'), a('status'), a('reason'), a('total_cost','str')],
    query={'limit': 1, 'filters': [{'field': 'status', 'operator': 'eq', 'value': 'admitted'}]},
    columns='1')

s_room_info = sec(PATIENT, 'My Room', C['Room'], 'detail', 4, 'slate',
    [a('room_number'), a('type'), a('floor','int'), a('capacity','int')],
    columns='1', card_style='outlined')

patient_sections = [
    s_upcoming_appt, s_all_appts, s_doctor_list, s_specialties,
    s_appt_detail, s_med_records, s_record_detail, s_prescriptions,
    s_lab_tests, s_lab_detail, s_my_bills, s_bill_detail,
    s_pay_method, s_my_profile, s_my_admission, s_room_info,
]

patient_pages = [
    page(PATIENT, 'My Appointments', [s_upcoming_appt, s_all_appts]),
    page(PATIENT, 'Book Appointment', [s_specialties, s_doctor_list]),
    page(PATIENT, 'Appointment Detail', [s_appt_detail],
         single_record=True, category=pcat(C['Appointment'], 'Appointment')),
    page(PATIENT, 'Confirm Appointment', [s_appt_detail],
         type_='activity', action=act_action(PAC['ConfirmAppointment'], 'Confirm Appointment')),
    page(PATIENT, 'My Medical Records', [s_med_records]),
    page(PATIENT, 'Record Detail', [s_record_detail, s_prescriptions],
         single_record=True, category=pcat(C['MedicalRecord'], 'MedicalRecord')),
    page(PATIENT, 'Lab Results', [s_lab_tests],
         type_='activity', action=act_action(PAC['ViewLabResults'], 'View Lab Results')),
    page(PATIENT, 'Lab Test Detail', [s_lab_detail],
         single_record=True, category=pcat(C['LabTest'], 'LabTest')),
    page(PATIENT, 'My Bills', [s_my_bills]),
    page(PATIENT, 'Pay Bill', [s_bill_detail, s_pay_method],
         type_='activity', action=act_action(PAC['SelectPayment'], 'Select Payment Method')),
    page(PATIENT, 'Confirm Payment', [s_bill_detail],
         type_='activity', action=act_action(PAC['ConfirmPayment'], 'Confirm Payment')),
    page(PATIENT, 'My Profile', [s_my_profile]),
    page(PATIENT, 'Admission Status', [s_my_admission, s_room_info]),
]

iface_p, _ = Interface.objects.update_or_create(
    id=I['Patient'],
    defaults={
        'system': system, 'name': 'Patient', 'description': 'Patient application',
        'actor': actor_objs['Patient'],
        'data': {
            'sections': patient_sections,
            'pages': patient_pages,
            'categories': [
                {'id': sid('cat','Appointment'), 'name': 'Appointment'},
                {'id': sid('cat','MedicalRecord'), 'name': 'MedicalRecord'},
                {'id': sid('cat','LabTest'), 'name': 'LabTest'},
            ],
            'styling': {
                'radius': 8, 'textColor': '#111827',
                'accentColor': '#0D9488', 'selectedStyle': 'modern',
                'backgroundColor': '#F0FDFA',
            },
            'tokens': {
                'region.header.bg': 'bg-teal-700',
                'page.body.bg': 'bg-slate-50',
                'page.body.text': 'text-slate-900',
                'page.container.max_width': 'max-w-7xl',
                'element.button.primary': 'bg-teal-600 text-white',
                'element.text.accent': 'text-teal-700',
            },
        },
    },
)
print(f'  {len(patient_pages)} pages, {len(patient_sections)} sections')
for p in patient_pages:
    print(f'    PAGE  {p["name"]}  type={p["type"]["value"]}')

# ═══════════════════════════════════════════════════════════════════════════════
# 7. DOCTOR INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════
print('\n── Doctor Interface ──────────────────────────────────────────────────────')
DOCTOR = 'Doctor'

s_today_appts = sec(DOCTOR, "Today's Appointments", C['Appointment'], 'table', 12, 'blue',
    [a('date','date'), a('time'), a('patient_id'), a('status'), a('reason')],
    query={'limit': 20,
           'filters': [{'field': 'status', 'operator': 'in', 'value': 'scheduled,confirmed'}],
           'order_by': [{'field': 'time', 'direction': 'asc'}]})

s_patient_overview = sec(DOCTOR, 'Patient Overview', C['Patient'], 'detail', 6, 'blue',
    [a('first_name'), a('last_name'), a('date_of_birth','date'),
     a('gender'), a('blood_type'), a('emergency_contact'), a('insurance_number')],
    columns='1')

s_med_history = sec(DOCTOR, 'Medical History', C['MedicalRecord'], 'list', 6, 'purple',
    [a('diagnosis'), a('symptoms'), a('treatment_plan'), a('created_at','datetime')],
    query={'limit': 5, 'order_by': [{'field': 'created_at', 'direction': 'desc'}]},
    density='compact', card_style='flat')

s_write_diagnosis = sec(DOCTOR, 'Write Diagnosis', C['MedicalRecord'], 'detail', 12, 'purple',
    [a('diagnosis'), a('symptoms'), a('treatment_plan'), a('notes')],
    ops(create=True), columns='1', card_style='elevated')

s_issue_prescription = sec(DOCTOR, 'Issue Prescription', C['Prescription'], 'list', 6, 'green',
    [a('medication_name'), a('dosage'), a('frequency'), a('duration'), a('notes')],
    ops(create=True, delete=True),
    query={'limit': 10})

s_medication_ref = sec(DOCTOR, 'Medication Reference', C['Medication'], 'list', 6, 'slate',
    [a('name'), a('generic_name'), a('unit'), a('price','str'), a('stock_quantity','int')],
    query={'limit': 20, 'filters': [{'field': 'stock_quantity', 'operator': 'gt', 'value': '0'}],
           'order_by': [{'field': 'name', 'direction': 'asc'}]},
    density='compact', card_style='flat')

s_order_lab = sec(DOCTOR, 'Order Lab Test', C['LabTest'], 'list', 12, 'orange',
    [a('test_name'), a('test_type'), a('status'), a('ordered_at','datetime')],
    ops(create=True),
    query={'limit': 10, 'order_by': [{'field': 'ordered_at', 'direction': 'desc'}]})

s_my_patients = sec(DOCTOR, 'My Patients', C['Patient'], 'table', 12, 'blue',
    [a('first_name'), a('last_name'), a('date_of_birth','date'), a('gender'), a('phone'), a('blood_type')],
    query={'limit': 25, 'order_by': [{'field': 'last_name', 'direction': 'asc'}]},
    view_detail_page='Patient Consultation')

s_admitted_patients = sec(DOCTOR, 'My Admitted Patients', C['Admission'], 'table', 12, 'orange',
    [a('patient_id'), a('room_id'), a('admission_date','date'), a('reason'), a('status')],
    query={'limit': 20, 'filters': [{'field': 'status', 'operator': 'eq', 'value': 'admitted'}]})

s_lab_results_review = sec(DOCTOR, 'Lab Results to Review', C['LabTest'], 'table', 12, 'orange',
    [a('test_name'), a('test_type'), a('result'), a('result_date','datetime'), a('patient_id')],
    query={'limit': 20, 'filters': [{'field': 'status', 'operator': 'eq', 'value': 'completed'}],
           'order_by': [{'field': 'result_date', 'direction': 'desc'}]})

s_doctor_profile = sec(DOCTOR, 'Doctor Profile', C['Doctor'], 'detail', 8, 'slate',
    [a('first_name'), a('last_name'), a('specialization'), a('consultation_fee','str'),
     a('years_experience','int'), a('is_available','bool'), a('rating','str')],
    ops(update=True), columns='1', card_style='outlined')

s_dept_info = sec(DOCTOR, 'Department Info', C['Department'], 'detail', 4, 'slate',
    [a('name'), a('description'), a('floor','int'), a('phone')],
    columns='1', card_style='flat')

doctor_sections = [
    s_today_appts, s_patient_overview, s_med_history,
    s_write_diagnosis, s_issue_prescription, s_medication_ref,
    s_order_lab, s_my_patients, s_admitted_patients,
    s_lab_results_review, s_doctor_profile, s_dept_info,
]

doctor_pages = [
    page(DOCTOR, "Today's Schedule", [s_today_appts],
         type_='activity', action=act_action(DAC['ViewSchedule'], 'View Today Schedule')),
    page(DOCTOR, 'Patient Consultation', [s_patient_overview, s_med_history],
         single_record=True, category=pcat(C['Patient'], 'Patient'),
         type_='activity', action=act_action(DAC['ViewPatientRecord'], 'View Patient Record')),
    page(DOCTOR, 'Write Diagnosis', [s_write_diagnosis, s_issue_prescription, s_medication_ref],
         type_='activity', action=act_action(DAC['WriteDiagnosis'], 'Write Diagnosis')),
    page(DOCTOR, 'Issue Prescription', [s_issue_prescription, s_medication_ref],
         type_='activity', action=act_action(DAC['IssuePrescription'], 'Issue Prescription')),
    page(DOCTOR, 'Order Lab Tests', [s_order_lab],
         type_='activity', action=act_action(DAC['OrderLabTest'], 'Order Lab Test')),
    page(DOCTOR, 'My Patients', [s_my_patients]),
    page(DOCTOR, 'Admitted Patients', [s_admitted_patients]),
    page(DOCTOR, 'Lab Results Review', [s_lab_results_review]),
    page(DOCTOR, 'Doctor Profile', [s_doctor_profile, s_dept_info]),
]

iface_d, _ = Interface.objects.update_or_create(
    id=I['Doctor'],
    defaults={
        'system': system, 'name': 'Doctor', 'description': 'Doctor application',
        'actor': actor_objs['Doctor'],
        'data': {
            'sections': doctor_sections,
            'pages': doctor_pages,
            'categories': [
                {'id': sid('cat','Patient'), 'name': 'Patient'},
            ],
            'styling': {
                'radius': 8, 'textColor': '#111827',
                'accentColor': '#2563EB', 'selectedStyle': 'modern',
                'backgroundColor': '#EFF6FF',
            },
            'tokens': {
                'region.header.bg': 'bg-blue-800',
                'page.body.bg': 'bg-slate-50',
                'page.body.text': 'text-slate-900',
                'page.container.max_width': 'max-w-7xl',
                'element.button.primary': 'bg-blue-600 text-white',
                'element.text.accent': 'text-blue-700',
            },
        },
    },
)
print(f'  {len(doctor_pages)} pages, {len(doctor_sections)} sections')
for p in doctor_pages:
    print(f'    PAGE  {p["name"]}  type={p["type"]["value"]}')

# ═══════════════════════════════════════════════════════════════════════════════
# 8. ADMIN INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════
print('\n── Admin Interface ───────────────────────────────────────────────────────')
ADMIN = 'Admin'

s_patient_dir = sec(ADMIN, 'Patient Directory', C['Patient'], 'table', 12, 'blue',
    [a('first_name'), a('last_name'), a('date_of_birth','date'),
     a('gender'), a('phone'), a('insurance_number'), a('is_active','bool')],
    ops(create=True, update=True),
    query={'limit': 25, 'order_by': [{'field': 'last_name', 'direction': 'asc'}]})

s_doctor_dir = sec(ADMIN, 'Doctor Directory', C['Doctor'], 'table', 12, 'green',
    [a('first_name'), a('last_name'), a('specialization'), a('is_available','bool'),
     a('consultation_fee','str'), a('rating','str')],
    ops(create=True, update=True),
    query={'limit': 25, 'order_by': [{'field': 'specialization', 'direction': 'asc'}]})

s_room_status = sec(ADMIN, 'Room Status', C['Room'], 'card', 12, 'orange',
    [a('room_number'), a('type'), a('floor','int'), a('is_available','bool'), a('capacity','int')],
    ops(update=True),
    query={'limit': 40, 'order_by': [{'field': 'room_number', 'direction': 'asc'}]},
    columns='4')

s_admission_list = sec(ADMIN, 'Admissions', C['Admission'], 'table', 8, 'blue',
    [a('patient_id'), a('doctor_id'), a('room_id'), a('admission_date','date'), a('status'), a('reason')],
    ops(create=True, update=True),
    query={'limit': 25, 'order_by': [{'field': 'admission_date', 'direction': 'desc'}]})

s_room_assignment = sec(ADMIN, 'Available Rooms', C['Room'], 'card', 4, 'orange',
    [a('room_number'), a('type'), a('floor','int'), a('capacity','int')],
    ops(update=True),
    query={'limit': 20, 'filters': [{'field': 'is_available', 'operator': 'eq', 'value': 'true'}]},
    columns='2')

s_discharge_summary = sec(ADMIN, 'Discharge Summary', C['Admission'], 'detail', 12, 'blue',
    [a('patient_id'), a('admission_date','date'), a('discharge_date','date'),
     a('reason'), a('total_cost','str'), a('status')],
    ops(update=True), columns='1')

s_bill_table = sec(ADMIN, 'Billing Overview', C['Bill'], 'table', 8, 'rose',
    [a('patient_id'), a('total_amount','str'), a('paid_amount','str'),
     a('balance','str'), a('payment_status'), a('due_date','date')],
    ops(create=True, update=True),
    query={'limit': 25, 'order_by': [{'field': 'created_at', 'direction': 'desc'}]})

s_payment_records = sec(ADMIN, 'Payment Records', C['Payment'], 'table', 4, 'purple',
    [a('patient_id'), a('amount','str'), a('payment_method'), a('status'), a('paid_at','datetime')],
    query={'limit': 25, 'order_by': [{'field': 'paid_at', 'direction': 'desc'}]})

s_staff_list = sec(ADMIN, 'Staff', C['Staff'], 'table', 8, 'slate',
    [a('first_name'), a('last_name'), a('role'), a('phone'), a('is_active','bool')],
    ops(create=True, update=True, delete=True),
    query={'limit': 30, 'order_by': [{'field': 'role', 'direction': 'asc'}]})

s_nurse_list = sec(ADMIN, 'Nurses', C['Nurse'], 'table', 4, 'purple',
    [a('first_name'), a('last_name'), a('shift'), a('is_available','bool')],
    ops(create=True, update=True),
    query={'limit': 25})

s_medication_inv = sec(ADMIN, 'Medication Inventory', C['Medication'], 'table', 8, 'green',
    [a('name'), a('generic_name'), a('category'), a('unit'),
     a('stock_quantity','int'), a('price','str'), a('expiry_date','date')],
    ops(create=True, update=True),
    query={'limit': 50, 'order_by': [{'field': 'name', 'direction': 'asc'}]})

s_low_stock = sec(ADMIN, 'Low Stock Alert', C['Medication'], 'list', 4, 'orange',
    [a('name'), a('stock_quantity','int'), a('expiry_date','date')],
    query={'limit': 10,
           'filters': [{'field': 'stock_quantity', 'operator': 'lte', 'value': '20'}],
           'order_by': [{'field': 'stock_quantity', 'direction': 'asc'}]},
    density='compact', card_style='flat')

s_dept_overview = sec(ADMIN, 'Departments', C['Department'], 'card', 12, 'slate',
    [a('name'), a('description'), a('floor','int'), a('phone')],
    ops(update=True), columns='3')

s_recent_admissions = sec(ADMIN, 'Recent Admissions', C['Admission'], 'list', 12, 'blue',
    [a('patient_id'), a('admission_date','date'), a('status'), a('reason')],
    query={'limit': 5, 'order_by': [{'field': 'admission_date', 'direction': 'desc'}]},
    density='compact', card_style='flat')

admin_sections = [
    s_patient_dir, s_doctor_dir, s_room_status,
    s_admission_list, s_room_assignment, s_discharge_summary,
    s_bill_table, s_payment_records,
    s_staff_list, s_nurse_list,
    s_medication_inv, s_low_stock,
    s_dept_overview, s_recent_admissions,
]

admin_pages = [
    page(ADMIN, 'Dashboard', [s_recent_admissions, s_room_status]),
    page(ADMIN, 'Patient Management', [s_patient_dir]),
    page(ADMIN, 'Doctor Management', [s_doctor_dir, s_dept_overview]),
    page(ADMIN, 'Room Management', [s_room_status, s_dept_overview]),
    page(ADMIN, 'Register Admission', [s_admission_list, s_room_assignment],
         type_='activity', action=act_action(AAC['RegisterAdmission'], 'Register Admission')),
    page(ADMIN, 'Assign Room', [s_discharge_summary, s_room_assignment],
         type_='activity', action=act_action(AAC['AssignRoom'], 'Assign Room')),
    page(ADMIN, 'Confirm Admission', [s_discharge_summary],
         type_='activity', action=act_action(AAC['ConfirmAdmission'], 'Confirm Admission')),
    page(ADMIN, 'Process Discharge', [s_discharge_summary, s_bill_table],
         type_='activity', action=act_action(AAC['ProcessDischarge'], 'Process Discharge')),
    page(ADMIN, 'Billing', [s_bill_table, s_payment_records]),
    page(ADMIN, 'Staff & Inventory', [s_staff_list, s_nurse_list, s_medication_inv, s_low_stock]),
]

iface_a, _ = Interface.objects.update_or_create(
    id=I['Admin'],
    defaults={
        'system': system, 'name': 'Admin', 'description': 'Hospital admin application',
        'actor': actor_objs['Admin'],
        'data': {
            'sections': admin_sections,
            'pages': admin_pages,
            'categories': [],
            'styling': {
                'radius': 6, 'textColor': '#111827',
                'accentColor': '#7C3AED', 'selectedStyle': 'modern',
                'backgroundColor': '#FAF5FF',
            },
            'tokens': {
                'region.header.bg': 'bg-violet-800',
                'page.body.bg': 'bg-slate-50',
                'page.body.text': 'text-slate-900',
                'page.container.max_width': 'max-w-7xl',
                'element.button.primary': 'bg-violet-600 text-white',
                'element.text.accent': 'text-violet-700',
            },
        },
    },
)
print(f'  {len(admin_pages)} pages, {len(admin_sections)} sections')
for p in admin_pages:
    print(f'    PAGE  {p["name"]}  type={p["type"]["value"]}')

# ═══════════════════════════════════════════════════════════════════════════════
print('\n═══ Done ════════════════════════════════════════════════════════════════')
print(f'  Project  {PROJECT_ID}')
print(f'  System   {SYSTEM_ID}')
print(f'  Classes  {len(cls_objs)}')
print(f'  Actors   {len(actor_objs)}')
print(f'  Diagrams {len(D)}')
print(f'  Interfaces: Patient · Doctor · Admin')
print(f'  Patient  {len(patient_pages)} pages / {len(patient_sections)} sections')
print(f'  Doctor   {len(doctor_pages)} pages / {len(doctor_sections)} sections')
print(f'  Admin    {len(admin_pages)} pages / {len(admin_sections)} sections')
