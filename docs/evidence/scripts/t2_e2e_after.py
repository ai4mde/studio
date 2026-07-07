import json
from pathlib import Path

from django.conf import settings

from shared_models.models import BookLoan


baseline = json.loads(Path("/tmp/t2_e2e_baseline.json").read_text(encoding="utf-8"))
log_path = Path(settings.BASE_DIR) / "ai_invocations.jsonl"
lines = (
    [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if log_path.exists()
    else []
)

count = BookLoan.objects.count()
expected_count = baseline["bookloan_count"] + 1
print(f"BookLoan count baseline={baseline['bookloan_count']} after={count}")
if count != expected_count:
    raise AssertionError(f"expected BookLoan count {expected_count}, got {count}")

new_rows = BookLoan.objects.filter(id__gt=baseline["max_bookloan_id"]).order_by("id")
print(f"BookLoan rows newer than baseline max id: {new_rows.count()}")
if new_rows.count() != 1:
    raise AssertionError(f"expected exactly one new BookLoan row, got {new_rows.count()}")

new_bookloan = new_rows.get()
print(f"New BookLoan id={new_bookloan.id} late_risk={new_bookloan.late_risk!r}")
if new_bookloan.late_risk != "LOW":
    raise AssertionError(f"expected new late_risk LOW, got {new_bookloan.late_risk!r}")

expected_jsonl = baseline["jsonl_lines"] + 1
print(f"JSONL lines baseline={baseline['jsonl_lines']} after={len(lines)}")
if len(lines) != expected_jsonl:
    raise AssertionError(f"expected JSONL lines {expected_jsonl}, got {len(lines)}")

record = json.loads(lines[-1])
print(f"Last JSONL record: {json.dumps(record, sort_keys=True)}")
if record.get("model") != "BookLoan":
    raise AssertionError(record)
if record.get("write_back", {}).get("field") != "late_risk":
    raise AssertionError(record)
if record.get("write_back", {}).get("value") != "LOW":
    raise AssertionError(record)
if record.get("mode") != "fake":
    raise AssertionError(record)

print("PASS T2 browser e2e DB/JSONL assertions")
