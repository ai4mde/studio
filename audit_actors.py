"""Audit all actor operations in the generated prototype."""
import re, os

base = '/usr/src/prototypes/generated_prototypes/8ac86bfe-ec5d-4b2e-b381-d84392dc9f08/applicants'
actors = ['Applicant', 'Loan_Officer', 'Document_analyst', 'System']

# Expected operations per actor per model
EXPECTED = {
    "Applicant": {
        "LoanApplication":  {"allowed_ops": {"CREATE", "UPDATE"}, "allowed_fields": {"loan_amount"}},
        "Applicant":         {"allowed_ops": {"CREATE", "UPDATE"}, "allowed_fields": {"name", "email", "credit_score"}},
        "Document":          {"allowed_ops": {"CREATE", "UPDATE", "DELETE"}, "allowed_fields": {"document_type", "file_content", "upload_date"}},
        "ApplicationNote":   {"allowed_ops": set(), "allowed_fields": {"comment"}},  # read-only
    },
    "Loan_Officer": {
        "LoanApplication":  {"allowed_ops": {"UPDATE"}, "allowed_fields": {"loan_amount", "requires_additional_documents", "status", "risk"}},
        "Applicant":         {"allowed_ops": set(), "allowed_fields": set()},  # read-only, no write views
        "Document":          {"allowed_ops": set(), "allowed_fields": set()},  # read-only
        "ApplicationNote":   {"allowed_ops": {"CREATE", "UPDATE", "DELETE"}, "allowed_fields": {"comment"}},
    },
    "Document_analyst": {
        "LoanApplication":  {"allowed_ops": set(), "allowed_fields": set()},  # read-only
        "Applicant":         {"allowed_ops": set(), "allowed_fields": set()},  # read-only
        "Document":          {"allowed_ops": {"UPDATE"}, "allowed_fields": {"document_type", "file_content", "upload_date", "valid"}},
        "ApplicationNote":   {"allowed_ops": {"CREATE"}, "allowed_fields": {"comment"}},
    },
    "System": {
        "LoanApplication":  {"allowed_ops": {"UPDATE"}, "allowed_fields": {"loan_amount", "requires_additional_documents", "status", "risk"}},
        "Applicant":         {"allowed_ops": set(), "allowed_fields": set()},
        "Document":          {"allowed_ops": set(), "allowed_fields": set()},
        "ApplicationNote":   {"allowed_ops": set(), "allowed_fields": set()},
    },
}

VIOLATIONS = []

for actor in actors:
    vpath = os.path.join(base, actor, 'views.py')
    if not os.path.exists(vpath):
        print(f'=== {actor}: NO views.py ===')
        continue
    with open(vpath) as f:
        content = f.read()

    blocks = re.split(r'(?=^class )', content, flags=re.MULTILINE)

    print(f'=== {actor} ===')
    actual_ops = {}  # model -> set of ops
    actual_fields = {}  # model -> set of fields

    for block in blocks:
        m = re.match(r'class (\w+)\((Generic\w+)\):', block)
        if not m:
            continue
        cls_name = m.group(1)
        view_type = m.group(2)

        model_m = re.search(r'model = (\w+)', block)
        model = model_m.group(1) if model_m else '?'

        fields_m = re.search(r"fields = \[([^\]]*)\]", block)
        fields_str = fields_m.group(1).strip() if fields_m else ''
        fields = set(f.strip().strip("'\"") for f in fields_str.split(',') if f.strip().strip("'\""))

        if 'CreateView' in view_type:
            op = 'CREATE'
        elif 'UpdateView' in view_type:
            op = 'UPDATE'
        elif 'DeleteView' in view_type:
            op = 'DELETE'
        elif 'ListView' in view_type:
            op = 'LIST'
        elif 'DetailView' in view_type:
            op = 'DETAIL'
        elif 'TemplateView' in view_type:
            op = 'TEMPLATE'
        else:
            op = view_type

        if op in ('LIST', 'DETAIL', 'TEMPLATE'):
            print(f'  [READ] {model}')
        else:
            print(f'  [{op}] {model} -> {sorted(fields)}')
            actual_ops.setdefault(model, set()).add(op)
            actual_fields.setdefault(model, set()).update(fields)

    # Check against expected
    expected = EXPECTED.get(actor, {})
    for model, rules in expected.items():
        real_ops = actual_ops.get(model, set())
        real_fields = actual_fields.get(model, set())
        allowed_ops = rules["allowed_ops"]
        allowed_fields = rules["allowed_fields"]

        # Check for forbidden operations
        forbidden_ops = real_ops - allowed_ops
        if forbidden_ops:
            msg = f"  !! VIOLATION: {actor} has {forbidden_ops} on {model} (allowed: {allowed_ops})"
            print(msg)
            VIOLATIONS.append(msg)

        # Check for forbidden fields (only in write views)
        if allowed_fields:
            forbidden_fields = real_fields - allowed_fields
            if forbidden_fields:
                msg = f"  !! VIOLATION: {actor} exposes forbidden fields {forbidden_fields} on {model} (allowed: {allowed_fields})"
                print(msg)
                VIOLATIONS.append(msg)
        elif real_fields and not allowed_ops:
            msg = f"  !! VIOLATION: {actor} has write fields {real_fields} on {model} but should be read-only"
            print(msg)
            VIOLATIONS.append(msg)

    # Check for unexpected models
    for model in actual_ops:
        if model not in expected:
            msg = f"  !! VIOLATION: {actor} has write ops on unexpected model {model}"
            print(msg)
            VIOLATIONS.append(msg)

    print()

print("=" * 60)
if VIOLATIONS:
    print(f"FOUND {len(VIOLATIONS)} VIOLATION(S):")
    for v in VIOLATIONS:
        print(v)
else:
    print("ALL CLEAR - No violations found!")
