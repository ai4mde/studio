import argparse
import copy
import json
from pathlib import Path

from diagram.models import Node
from metadata.models import System


SYSTEM_ID = "7d735a07-b6cd-409d-9cc7-f3a07cbec983"


def expected_late_risk(allowed_values=None):
    return {
        "ai_config_version": "1.0",
        "context": {
            "fields": ["loan_date", "due_date", "return_date"],
            "relations": ["Book", "Customer", "Loan"],
        },
        "model_profile": "cheap",
        "output": {
            "allowed_values": allowed_values or ["LOW", "MEDIUM", "HIGH"],
            "format": "risk_label",
            "write_back": "late_risk",
        },
        "template": {"name": "library_late_risk_v1"},
        "trigger": {"class": "BookLoan", "type": "post_save"},
    }


def expected_reading_plan():
    return {
        "ai_config_version": "1.0",
        "context": {
            "relations": ["Loan", "BookLoan", "Book"],
        },
        "model_profile": "strong",
        "output": {
            "format": "reading_plan",
            "write_back": "reading_plan",
        },
        "template": {
            "chain": [
                "reading_plan_analyze_taste_v1",
                "reading_plan_recommend_v1",
                "reading_plan_sequence_v1",
            ],
        },
        "trigger": {"class": "Customer", "type": "user_action"},
    }


UNSUPPORTED_AI_CONFIG = {
    "ai_config_version": "1.0",
    "context": {"fields": ["loan_date"]},
    "model_profile": "cheap",
    "output": {
        "format": "custom_unknown",
        "write_back": "late_risk",
    },
    "template": {"name": "custom_unknown_template_v1"},
    "trigger": {"class": "BookLoan", "type": "post_save"},
}


def class_node(class_name: str):
    system = System.objects.get(id=SYSTEM_ID)
    node = (
        Node.objects.filter(diagram__system=system, cls__data__name=class_name)
        .select_related("cls")
        .first()
    )
    if not node:
        raise AssertionError(f"missing node for {class_name}")
    return node


def get_attr(class_name: str, attr_name: str):
    node = class_node(class_name)
    attrs = node.cls.data.get("attributes", [])
    attr = next((item for item in attrs if item.get("name") == attr_name), None)
    if not attr:
        raise AssertionError(f"missing attr {class_name}.{attr_name}")
    return copy.deepcopy(attr)


def set_ai_config(class_name: str, attr_name: str, ai_config):
    node = class_node(class_name)
    data = copy.deepcopy(node.cls.data)
    for attr in data.get("attributes", []):
        if attr.get("name") == attr_name:
            attr["ai_config"] = copy.deepcopy(ai_config)
            node.cls.data = data
            node.cls.save()
            return get_attr(class_name, attr_name)
    raise AssertionError(f"missing attr {class_name}.{attr_name}")


def all_ai_configs():
    rows = []
    system = System.objects.get(id=SYSTEM_ID)
    nodes = Node.objects.filter(diagram__system=system, cls__data__type="class").select_related("cls")
    for node in nodes:
        class_name = node.cls.data.get("name")
        for attr in node.cls.data.get("attributes", []):
            if "ai_config" in attr:
                rows.append(
                    {
                        "class": class_name,
                        "attribute": attr.get("name"),
                        "ai_config": copy.deepcopy(attr.get("ai_config")),
                    }
                )
    return rows


def clear_stray_ai_configs():
    keep = {("BookLoan", "late_risk"), ("Customer", "reading_plan")}
    removed = []
    system = System.objects.get(id=SYSTEM_ID)
    nodes = Node.objects.filter(diagram__system=system, cls__data__type="class").select_related("cls")
    for node in nodes:
        class_name = node.cls.data.get("name")
        data = copy.deepcopy(node.cls.data)
        changed = False
        for attr in data.get("attributes", []):
            key = (class_name, attr.get("name"))
            if key not in keep and "ai_config" in attr:
                removed.append({"class": class_name, "attribute": attr.get("name")})
                attr.pop("ai_config")
                changed = True
        if changed:
            node.cls.data = data
            node.cls.save()
    return removed


def result_for(action: str):
    before = {
        "BookLoan.late_risk": get_attr("BookLoan", "late_risk"),
        "Customer.reading_plan": get_attr("Customer", "reading_plan"),
    }

    if action == "list-ai-configs":
        return {
            "action": action,
            "ai_configs": all_ai_configs(),
            "pass": "listed ai_config-bearing attributes",
        }

    if action == "clear-stray":
        before_rows = all_ai_configs()
        removed = clear_stray_ai_configs()
        return {
            "action": action,
            "before": before_rows,
            "removed": removed,
            "after": all_ai_configs(),
            "pass": "removed non-target ai_config keys",
        }

    if action == "set-unsupported":
        after = set_ai_config("BookLoan", "late_risk", UNSUPPORTED_AI_CONFIG)
        return {
            "action": action,
            "before": before,
            "after": {"BookLoan.late_risk": after},
            "pass": "B11 unsupported ai_config injected",
        }

    if action == "assert-unsupported":
        late = before["BookLoan.late_risk"]
        if late.get("ai_config") != UNSUPPORTED_AI_CONFIG:
            raise AssertionError("unsupported ai_config changed after UI open")
        return {
            "action": action,
            "after": before,
            "pass": "G-B11 unsupported remained byte-for-byte equal",
        }

    if action == "assert-safe-risky":
        late = before["BookLoan.late_risk"]
        if late.get("ai_config") != expected_late_risk(["SAFE", "RISKY"]):
            raise AssertionError("SAFE/RISKY allowed_values were not saved as array")
        return {
            "action": action,
            "after": before,
            "pass": "G-B08 allowed_values saved as SAFE/RISKY array",
        }

    if action == "restore-canonical":
        late = set_ai_config("BookLoan", "late_risk", expected_late_risk())
        reading = set_ai_config("Customer", "reading_plan", expected_reading_plan())
        return {
            "action": action,
            "before": before,
            "after": {
                "BookLoan.late_risk": late,
                "Customer.reading_plan": reading,
            },
            "pass": "canonical ai_config restored",
        }

    if action == "assert-canonical":
        late = before["BookLoan.late_risk"]
        reading = before["Customer.reading_plan"]
        if late.get("ai_config") != expected_late_risk():
            raise AssertionError("BookLoan.late_risk is not canonical")
        if reading.get("ai_config") != expected_reading_plan():
            raise AssertionError("Customer.reading_plan is not canonical")
        return {
            "action": action,
            "after": before,
            "pass": "G-reg canonical ai_config present",
        }

    raise AssertionError(f"unknown action {action}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()

    result = result_for(args.action)
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


main()
