import argparse
import json
from copy import deepcopy
from pathlib import Path

from diagram.models import Node
from metadata.models import System


TARGETS = {
    "BookLoan": "late_risk",
    "Customer": "reading_plan",
}


def load_targets(system_id: str):
    system = System.objects.get(id=system_id)
    nodes = (
        Node.objects.filter(diagram__system=system, cls__data__type="class")
        .select_related("cls", "diagram")
        .order_by("cls__data__name")
    )
    by_class = {node.cls.data.get("name"): node for node in nodes}
    missing = [name for name in TARGETS if name not in by_class]
    if missing:
        raise AssertionError(f"missing target class nodes: {missing}")
    return {name: by_class[name] for name in TARGETS}


def snapshot(system_id: str):
    result = {
        "system_id": system_id,
        "classifiers": {},
    }
    for class_name, node in load_targets(system_id).items():
        result["classifiers"][class_name] = {
            "node_id": str(node.id),
            "classifier_id": str(node.cls_id),
            "data": deepcopy(node.cls.data),
        }
    return result


def write_json(path: str | None, payload):
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def reset(system_id: str):
    changed = []
    for class_name, attr_name in TARGETS.items():
        node = load_targets(system_id)[class_name]
        data = deepcopy(node.cls.data)
        for attr in data.get("attributes", []):
            if attr.get("name") == attr_name and "ai_config" in attr:
                attr.pop("ai_config")
                changed.append(f"{class_name}.{attr_name}")
        node.cls.data = data
        node.cls.save()
    return changed


def restore(system_id: str, snapshot_path: str):
    saved = json.loads(Path(snapshot_path).read_text())
    if saved["system_id"] != system_id:
        raise AssertionError(f"snapshot system mismatch: {saved['system_id']} != {system_id}")

    targets = load_targets(system_id)
    for class_name, node in targets.items():
        saved_data = deepcopy(saved["classifiers"][class_name]["data"])
        node.cls.data = saved_data
        node.cls.save()

    restored = snapshot(system_id)
    expected = {
        "system_id": saved["system_id"],
        "classifiers": {
            name: {
                "node_id": saved["classifiers"][name]["node_id"],
                "classifier_id": saved["classifiers"][name]["classifier_id"],
                "data": saved["classifiers"][name]["data"],
            }
            for name in TARGETS
        },
    }
    if restored != expected:
        raise AssertionError("restored data does not deep-match snapshot")
    return restored


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--system-id",
        default="7d735a07-b6cd-409d-9cc7-f3a07cbec983",
    )
    parser.add_argument("--snapshot")
    parser.add_argument("--after")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--restore")
    args = parser.parse_args()

    if args.reset and args.restore:
        raise SystemExit("--reset and --restore are mutually exclusive")
    if not args.reset and not args.restore:
        raise SystemExit("use --reset or --restore")

    before = snapshot(args.system_id)
    write_json(args.snapshot, before)
    print(f"before target classes: {list(before['classifiers'])}")

    if args.restore:
        restored = restore(args.system_id, args.restore)
        write_json(args.after, restored)
        print("PASS restore deep-matches snapshot")
        return

    changed = reset(args.system_id)
    after = snapshot(args.system_id)
    write_json(args.after, after)
    print(f"reset removed ai_config from: {changed}")
    for class_name, attr_name in TARGETS.items():
        attrs = after["classifiers"][class_name]["data"].get("attributes", [])
        attr = next(item for item in attrs if item.get("name") == attr_name)
        if "ai_config" in attr:
            raise AssertionError(f"{class_name}.{attr_name} still has ai_config")
    print("PASS reset removed target ai_config keys")


main()
