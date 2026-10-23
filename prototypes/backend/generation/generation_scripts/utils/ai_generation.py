"""Validate resolved metadata and derive Library bindings before rendering."""
from __future__ import annotations

import json
import sys
from pathlib import Path

GENERATION_ROOT = Path(__file__).resolve().parents[2]
if str(GENERATION_ROOT) not in sys.path:
    sys.path.insert(0, str(GENERATION_ROOT))

from ai_runtime_assets.configuration import ConfigurationError, validate_ai_config
from utils.loading_json_utils import find_parent_models_by_id, get_enum_literals
from utils.sanitization import app_name_sanitization, model_name_sanitization, attribute_name_sanitization


def validate_metadata(metadata):
    raw = json.loads(metadata) if isinstance(metadata, str) else metadata
    serialized = json.dumps(raw)
    models, configs = {}, []
    for diagram in raw.get("diagrams", []):
        if diagram.get("type") != "classes":
            continue
        for node in diagram.get("nodes", []):
            cls = node.get("cls", {})
            if cls.get("type") != "class":
                continue
            name = model_name_sanitization(cls["name"])
            models[name] = node
            for attr in cls.get("attributes", []):
                if attr.get("ai_config") is not None:
                    field = attribute_name_sanitization(attr["name"])
                    if attr.get("derived") or attr.get("type") != "str":
                        raise ConfigurationError(f"{name}.{field}: AI write-back requires a stored string attribute")
                    configs.append((name, field, validate_ai_config(attr["ai_config"], name, field)))
    bindings = {"library_ai_enabled": bool(configs), "ownership": {}, "frozen_parents": {}, "ai_fields": {}, "lifecycle": {}, "model_constraints": {}}
    if not configs:
        return bindings
    if {(model, field) for model, field, _ in configs} != {('BookLoan', 'late_risk'), ('Customer', 'reading_plan')}:
        raise ConfigurationError('Library 1.2 requires both late_risk and reading_plan configurations')
    if raw.get("useAuthentication") is not True:
        raise ConfigurationError("Library AI bindings require useAuthentication=true")
    required = {"BookLoan": ["late_risk", "return_date"], "Loan": ["loan_date", "due_date"],
                "Book": ["title", "category"], "Author": ["name"], "Customer": ["name"]}
    for model, names in required.items():
        fields = {a["name"] for a in models.get(model, {}).get("cls", {}).get("attributes", [])}
        if not set(names) <= fields:
            raise ConfigurationError(f"Library adapter: {model} missing required fields {names}")
    attributes = {name: {a['name']: a for a in node['cls']['attributes']} for name, node in models.items()}
    if 'return_date' in attributes['Loan']:
        raise ConfigurationError('Library 1.2: move Loan.return_date to BookLoan before generating')
    for name, fields in required.items():
        for field in fields:
            attr = attributes[name][field]
            expected = 'enum' if (name, field) == ('Book', 'category') else 'str'
            if attr.get('type') != expected or attr.get('derived'):
                raise ConfigurationError(f'{name}.{field}: expected stored {expected}')
    if not get_enum_literals(serialized, attributes['Book']['category'].get('enum')):
        raise ConfigurationError('Book.category requires a non-empty enum')
    bindings['model_constraints'] = {'BookLoan': [{'fields': ['Loan', 'Book'], 'name': 'bl_bookloan_loan_book_uniq'}]}
    bindings['lifecycle'] = {
        'Loan': {'child_model': 'BookLoan', 'child_fk': 'Loan',
                 'frozen_after_first_child': ['Customer', 'loan_date', 'due_date']},
        'BookLoan': {'loan_fk': 'Loan', 'book_fk': 'Book', 'return_field': 'return_date'},
    }
    for model, parents in {"BookLoan": {"Loan", "Book"}, "Loan": {"Customer"}, "Book": {"Author"}}.items():
        actual = set(find_parent_models_by_id(serialized, models[model]["cls_ptr"]))
        if not parents <= actual:
            raise ConfigurationError(f"Library adapter: {model} requires parent relations {sorted(parents)}")
    for model, field, config in configs:
        bindings["ai_fields"][model] = {"field": field, "format": config["output"]["format"], "on_skip": config["output"]["on_skip"]}
        if model == "BookLoan":
            bindings["frozen_parents"][model] = find_parent_models_by_id(serialized, models[model]["cls_ptr"])
        else:
            customer_fields = {a["name"] for a in models[model]["cls"].get("attributes", [])}
            if "email" not in customer_fields:
                raise ConfigurationError("Customer.reading_plan: trusted demo binding requires Customer.email")
            bindings["ownership"] = {"member": {"Customer": "email"}}
    class_names = {n["cls_ptr"]: name for name, n in models.items()}
    for interface in raw.get("interfaces", []):
        value = interface.get("value", {})
        app = app_name_sanitization(value.get("name", interface.get("label", "")))
        data = value.get("data", {})
        sections = {s["id"]: s for s in data.get("sections", [])}
        for page in data.get("pages", []):
            page_type = page.get("type", {})
            page_type = page_type.get("value") if isinstance(page_type, dict) else page_type
            for ref in page.get("sections", []):
                section = sections.get(ref.get("value"), {})
                model = class_names.get(section.get("class"))
                methods = [m.get("name", "") for m in section.get("methods", [])]
                if any(not method.isidentifier() or method.startswith("_") for method in methods):
                    raise ConfigurationError(f"{app}.{page.get('name')}: invalid declared action name")
                related = set(find_parent_models_by_id(serialized, models[model]["cls_ptr"])) if model in models else set()
                if app == "member" and (model == "Customer" or "Customer" in related):
                    if bindings["ownership"].get(app, {}).get("Customer") != "email":
                        raise ConfigurationError("member.Customer: missing ownership rule")
                if app == "member" and model in bindings["ai_fields"]:
                    if model not in bindings["ownership"].get(app, {}):
                        raise ConfigurationError(f"{app}.{model}: missing ownership rule")
                    if page_type == "activity" and "generate_reading_plan" in methods:
                        raise ConfigurationError("member reading_plan actions on activity pages are unsupported")
    return bindings
