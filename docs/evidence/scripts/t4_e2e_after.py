import json
from pathlib import Path

from django.conf import settings

from shared_models.models import BookLoan, Customer


baseline = json.loads(Path("/tmp/t4_e2e_baseline.json").read_text(encoding="utf-8"))
log_path = Path(settings.BASE_DIR) / "ai_invocations.jsonl"
lines = (
    [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if log_path.exists()
    else []
)

bookloan_count = BookLoan.objects.count()
expected_count = baseline["bookloan_count"] + 1
print(f"BookLoan count baseline={baseline['bookloan_count']} after={bookloan_count}")
if bookloan_count != expected_count:
    raise AssertionError(f"expected BookLoan count {expected_count}, got {bookloan_count}")

new_bookloans = BookLoan.objects.filter(id__gt=baseline["max_bookloan_id"]).order_by("id")
print(f"BookLoan rows newer than baseline max id: {new_bookloans.count()}")
if new_bookloans.count() != 1:
    raise AssertionError(f"expected exactly one new BookLoan row, got {new_bookloans.count()}")
new_bookloan = new_bookloans.get()
print(f"New BookLoan id={new_bookloan.id} late_risk={new_bookloan.late_risk!r}")
if new_bookloan.late_risk != "LOW":
    raise AssertionError(f"expected new late_risk LOW, got {new_bookloan.late_risk!r}")

alice = Customer.objects.get(id=baseline["alice_id"])
print(f"alice reading_plan before={baseline['alice_reading_plan']!r}")
print(f"alice reading_plan after={alice.reading_plan!r}")
if alice.reading_plan in ("", None):
    raise AssertionError("alice.reading_plan did not change")

expected_jsonl = baseline["jsonl_lines"] + 2
print(f"JSONL lines baseline={baseline['jsonl_lines']} after={len(lines)}")
if len(lines) != expected_jsonl:
    raise AssertionError(f"expected JSONL lines {expected_jsonl}, got {len(lines)}")

new_records = [json.loads(line) for line in lines[baseline["jsonl_lines"] :]]
print(f"New JSONL records: {json.dumps(new_records, sort_keys=True)}")
bookloan_records = [
    record
    for record in new_records
    if record.get("model") == "BookLoan"
    and record.get("mode") == "fake"
    and record.get("status") == "success"
    and record.get("write_back", {}).get("field") == "late_risk"
    and record.get("write_back", {}).get("value") == "LOW"
]
customer_records = [
    record
    for record in new_records
    if record.get("model") == "Customer"
    and record.get("event") == "invoke_chain"
    and record.get("mode") == "fake"
    and record.get("status") == "success"
    and record.get("write_back", {}).get("field") == "reading_plan"
]
if len(bookloan_records) != 1:
    raise AssertionError(f"expected one BookLoan late_risk record, got {bookloan_records}")
if len(customer_records) != 1:
    raise AssertionError(f"expected one Customer reading_plan record, got {customer_records}")

print("PASS T4 browser e2e DB/JSONL assertions")
