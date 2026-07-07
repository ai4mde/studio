import argparse
import json
from pathlib import Path


def expected_late_risk():
    return {
        "ai_config_version": "1.0",
        "context": {
            "fields": ["loan_date", "due_date", "return_date"],
            "relations": ["Book", "Customer", "Loan"],
        },
        "model_profile": "cheap",
        "output": {
            "allowed_values": ["LOW", "MEDIUM", "HIGH"],
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


def find_attr(metadata, class_name, attr_name):
    for diagram in metadata.get("diagrams", []):
        for node in diagram.get("nodes", []):
            data = node.get("cls", {})
            if data.get("name") != class_name:
                continue
            for attr in data.get("attributes", []):
                if attr.get("name") == attr_name:
                    return attr
    raise AssertionError(f"missing {class_name}.{attr_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()

    metadata = json.loads(Path(args.metadata).read_text())
    late = find_attr(metadata, "BookLoan", "late_risk")
    reading = find_attr(metadata, "Customer", "reading_plan")
    if late.get("ai_config") != expected_late_risk():
        raise AssertionError("BookLoan.late_risk metadata ai_config mismatch")
    if reading.get("ai_config") != expected_reading_plan():
        raise AssertionError("Customer.reading_plan metadata ai_config mismatch")
    if late["ai_config"]["output"]["allowed_values"] != ["LOW", "MEDIUM", "HIGH"]:
        raise AssertionError("allowed_values canonical three-value array missing")

    result = {
        "metadata": args.metadata,
        "pass": "G-authority metadata canonical ai_config",
        "BookLoan.late_risk": late["ai_config"],
        "Customer.reading_plan": reading["ai_config"],
    }
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


main()
