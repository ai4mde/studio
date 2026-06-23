import json
from pathlib import Path
from django.conf import settings

# explicit import-contract check (the hook imports this lazily at runtime).
# Do NOT import shared_models.ai_hooks here — apps.ready() already registered the
# receiver; a manual re-import could double-register it (no dispatch_uid).
from ai_runtime import invoke
assert callable(invoke), "ai_runtime.invoke is not callable"

from shared_models.models import Author, Book, Customer, Loan, BookLoan

log_path = Path(settings.BASE_DIR) / "ai_invocations.jsonl"
if log_path.exists():
    log_path.unlink()  # count only this smoke's records

a = Author.objects.create()
b = Book.objects.create(Author=a)
c = Customer.objects.create()
l = Loan.objects.create(Customer=c)
bl = BookLoan.objects.create(Loan=l, Book=b)   # triggers post_save -> ai_runtime.invoke (stub)
bl.refresh_from_db()
print(f"[smoke] created BookLoan pk={bl.pk} late_risk={bl.late_risk!r}")

assert log_path.exists(), f"ai_invocations.jsonl not created at {log_path}"
lines = [ln for ln in log_path.read_text().splitlines() if ln.strip()]
assert len(lines) == 1, f"expected exactly 1 JSONL record, got {len(lines)}"
rec = json.loads(lines[0])
print(f"[smoke] jsonl record: {rec}")
assert rec["event"] == "invoke_stub", "record event != invoke_stub"
assert rec["model"] == "BookLoan", f"record model != BookLoan: {rec['model']}"
assert rec["write_back"] == "late_risk", f"record write_back != late_risk: {rec['write_back']}"
assert rec["pk"] == bl.pk, "record pk mismatch"
assert bl.late_risk == "", f"late_risk should be unchanged (''), got {bl.late_risk!r}"
print("[smoke] PASS: receiver fired -> ai_runtime stub logged 1 record -> late_risk unchanged (no write-back)")
print("[DONE] Step 5C wiring smoke VERIFIED.")
