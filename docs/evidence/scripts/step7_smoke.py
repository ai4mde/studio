import json
import os
from pathlib import Path
from django.conf import settings

from ai_runtime import invoke
from ai_runtime.context import build_context
from ai_runtime.routing import call_model
from ai_runtime.templates import render_prompt
from ai_runtime.parsers import JsonOutputParser
assert callable(invoke)

from shared_models.models import Author, Book, Customer, Loan, BookLoan

expect_mode = os.environ.get("EXPECT_MODE")  # 'fake' | 'real'

log_path = Path(settings.BASE_DIR) / "ai_invocations.jsonl"
if log_path.exists():
    log_path.unlink()

a = Author.objects.create(name="A. Writer", nationality="NL")
b = Book.objects.create(title="The Test Book", Author=a)
c = Customer.objects.create(name="C. Reader", email="c@example.com")
l = Loan.objects.create(loan_date="2026-01-01", due_date="2026-01-15", return_date="", Customer=c)
bl = BookLoan.objects.create(Loan=l, Book=b)   # post_save -> invoke -> full runtime
bl.refresh_from_db()
print(f"[smoke] BookLoan pk={bl.pk} late_risk={bl.late_risk!r}")

assert log_path.exists(), "ai_invocations.jsonl not created"
lines = [ln for ln in log_path.read_text().splitlines() if ln.strip()]
assert len(lines) == 1, f"expected exactly 1 invocation record, got {len(lines)}"
rec = json.loads(lines[0])
print(f"[smoke] record keys: {sorted(rec)}")
assert rec["event"] == "invoke", rec["event"]
assert rec["trigger"] == "post_save", rec["trigger"]
assert rec["model"] == "BookLoan" and rec["pk"] == bl.pk
assert rec["model_profile"] == "cheap" and rec["provider"] == "groq"
assert rec["template"] == "library_late_risk_v1"
# context (M02) actually grounded from the ORM
assert rec["context"]["loan_date"] == "2026-01-01", rec["context"]
assert rec["context"]["book_title"] == "The Test Book", rec["context"]
assert rec["context"]["customer_name"] == "C. Reader", rec["context"]
# end-to-end success: parsed -> written back
assert rec["status"] == "success", f"status={rec['status']} error={rec.get('error')}"
assert rec["write_back"]["field"] == "late_risk"
assert rec["write_back"]["value"] in ("LOW", "MEDIUM", "HIGH"), rec["write_back"]
assert bl.late_risk == rec["write_back"]["value"], (bl.late_risk, rec["write_back"])
assert bl.late_risk in ("LOW", "MEDIUM", "HIGH"), bl.late_risk
if expect_mode:
    assert rec["mode"] == expect_mode, f"mode {rec['mode']} != {expect_mode}"
if expect_mode == "fake":
    assert bl.late_risk == "LOW", f"fake content should yield LOW, got {bl.late_risk!r}"
if rec["mode"] == "real":
    assert rec["raw_output"].strip(), "real provider returned empty raw_output"

print(f"[smoke] PASS: post_save -> M02 context -> M01 render -> M06 route -> M03 parse -> "
      f"write-back late_risk={bl.late_risk!r} (mode={rec['mode']})")
print("[DONE] Step 7 late_risk end-to-end VERIFIED.")
