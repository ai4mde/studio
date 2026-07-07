import json
from pathlib import Path

from django.conf import settings

from shared_models.models import Customer


baseline = json.loads(Path("/tmp/t3_action_baseline.json").read_text(encoding="utf-8"))
log_path = Path(settings.BASE_DIR) / "ai_invocations.jsonl"
lines = (
    [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if log_path.exists()
    else []
)

alice = Customer.objects.get(id=baseline["alice_id"])
print(f"alice id={alice.id}")
print(f"alice reading_plan before={baseline['alice_reading_plan']!r}")
print(f"alice reading_plan after={alice.reading_plan!r}")
if alice.reading_plan in ("", None):
    raise AssertionError("alice.reading_plan did not change to a non-empty summary")

expected_jsonl = baseline["jsonl_lines"] + 1
print(f"JSONL lines baseline={baseline['jsonl_lines']} after={len(lines)}")
if len(lines) != expected_jsonl:
    raise AssertionError(f"expected JSONL lines {expected_jsonl}, got {len(lines)}")

record = json.loads(lines[-1])
print(f"Last JSONL record: {json.dumps(record, sort_keys=True)}")
if record.get("event") != "invoke_chain":
    raise AssertionError(record)
if record.get("mode") != "fake":
    raise AssertionError(record)
if record.get("status") != "success":
    raise AssertionError(record)
if record.get("model") != "Customer":
    raise AssertionError(record)
if record.get("write_back", {}).get("field") != "reading_plan":
    raise AssertionError(record)
if not record.get("write_back", {}).get("value"):
    raise AssertionError(record)

print("PASS T3 reading_plan action DB/JSONL assertions")
