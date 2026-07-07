import argparse
import json
from copy import deepcopy
from pathlib import Path

from diagram.models import Node
from metadata.api.schemas import MetaClassifiersSchema
from metadata.models import Classifier, System
from metadata.specification import ClassifierSchema


SYSTEM_ID = "7d735a07-b6cd-409d-9cc7-f3a07cbec983"


def expected_late_risk(
    model_profile="cheap",
    allowed_values=None,
):
    return {
        "ai_config_version": "1.0",
        "context": {
            "fields": ["loan_date", "due_date", "return_date"],
            "relations": ["Book", "Customer", "Loan"],
        },
        "model_profile": model_profile,
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


def raw_attr(class_name: str, attr_name: str):
    system = System.objects.get(id=SYSTEM_ID)
    node = (
        Node.objects.filter(diagram__system=system, cls__data__name=class_name)
        .select_related("cls")
        .first()
    )
    if not node:
        raise AssertionError(f"missing node for {class_name}")
    attrs = node.cls.data.get("attributes", [])
    attr = next((item for item in attrs if item.get("name") == attr_name), None)
    if not attr:
        raise AssertionError(f"missing attr {class_name}.{attr_name}")
    return deepcopy(attr)


def typed_api_attr(class_name: str, attr_name: str):
    classifier = Classifier.objects.get(system_id=SYSTEM_ID, data__name=class_name)
    payload = ClassifierSchema.from_orm(classifier).model_dump(mode="json")
    attrs = payload["data"]["attributes"]
    return next(item for item in attrs if item.get("name") == attr_name)


def assert_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError(
            f"{label} mismatch\nactual={json.dumps(actual, indent=2, sort_keys=True)}\n"
            f"expected={json.dumps(expected, indent=2, sort_keys=True)}"
        )


def check(stage: str):
    late = raw_attr("BookLoan", "late_risk")
    reading = raw_attr("Customer", "reading_plan")
    result = {
        "stage": stage,
        "raw": {
            "BookLoan.late_risk": late,
            "Customer.reading_plan": reading,
        },
    }

    if stage == "bookloan-canonical":
        assert_equal(late.get("ai_config"), expected_late_risk(), "BookLoan.late_risk ai_config")
        assert late["ai_config"]["trigger"]["class"] == "BookLoan"
        assert late["ai_config"]["output"]["write_back"] == "late_risk"
        assert isinstance(late["ai_config"]["output"]["allowed_values"], list)
        result["pass"] = "G-save-on G-dynamic G-values canonical"
    elif stage == "bookloan-safe-risky":
        values = late.get("ai_config", {}).get("output", {}).get("allowed_values")
        assert_equal(values, ["SAFE", "RISKY"], "allowed_values")
        assert isinstance(values, list)
        result["pass"] = "G-values edit array"
    elif stage == "bookloan-model-strong":
        assert_equal(late.get("ai_config", {}).get("model_profile"), "strong", "model_profile")
        result["pass"] = "G-edit model_profile strong"
    elif stage == "bookloan-restored-canonical":
        assert_equal(late.get("ai_config"), expected_late_risk(), "BookLoan.late_risk restored")
        result["pass"] = "G-values restored canonical"
    elif stage == "bookloan-off":
        if "ai_config" in late:
            raise AssertionError("raw BookLoan.late_risk still contains ai_config")
        result["typed_api"] = {
            "BookLoan.late_risk": typed_api_attr("BookLoan", "late_risk"),
        }
        result["pass"] = "G-save-off-DB; typed API observation recorded"
    elif stage == "both-off":
        if "ai_config" in late:
            raise AssertionError("raw BookLoan.late_risk still contains ai_config")
        if "ai_config" in reading:
            raise AssertionError("raw Customer.reading_plan still contains ai_config")
        result["pass"] = "reset state has no target ai_config keys"
    elif stage == "both-canonical":
        assert_equal(late.get("ai_config"), expected_late_risk(), "BookLoan.late_risk final")
        assert_equal(reading.get("ai_config"), expected_reading_plan(), "Customer.reading_plan final")
        result["pass"] = "G-authority final DB raw configs"
    else:
        raise AssertionError(f"unknown stage: {stage}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()

    result = check(args.stage)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


main()
