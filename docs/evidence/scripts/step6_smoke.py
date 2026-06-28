import json
import os
from pathlib import Path
from django.conf import settings

from ai_runtime import invoke, call_model, MODEL_PROFILES
assert callable(invoke) and callable(call_model), "ai_runtime entrypoints missing"
# routing table sanity (M06)
assert MODEL_PROFILES["cheap"]["provider"] == "groq", MODEL_PROFILES
assert MODEL_PROFILES["strong"]["provider"] == "openai", MODEL_PROFILES

from shared_models.models import Author, Book, Customer, Loan, BookLoan

expect_mode = os.environ.get("EXPECT_MODE")  # 'fake' | 'real' | None

log_path = Path(settings.BASE_DIR) / "ai_invocations.jsonl"
if log_path.exists():
    log_path.unlink()  # count only this smoke's records

a = Author.objects.create()
b = Book.objects.create(Author=a)
c = Customer.objects.create()
l = Loan.objects.create(Customer=c)
bl = BookLoan.objects.create(Loan=l, Book=b)   # post_save -> invoke -> router (cheap)
bl.refresh_from_db()
print(f"[smoke] BookLoan pk={bl.pk} late_risk={bl.late_risk!r} (expect '' - no write-back at Step 6)")

assert log_path.exists(), "ai_invocations.jsonl not created"
lines = [ln for ln in log_path.read_text().splitlines() if ln.strip()]
assert len(lines) == 1, f"expected exactly 1 record, got {len(lines)}"
rec = json.loads(lines[0])
print(f"[smoke] cheap record: {rec}")
assert rec["event"] == "invoke_routed", rec["event"]
assert rec["model_profile"] == "cheap", rec["model_profile"]
assert rec["provider"] == "groq", rec["provider"]                      # routing decision (M06)
assert rec["routed_model"] == "llama-3.3-70b-versatile", rec["routed_model"]
assert bl.late_risk == "", f"late_risk must stay '' at Step 6, got {bl.late_risk!r}"
if expect_mode:
    assert rec["mode"] == expect_mode, f"cheap mode {rec['mode']} != {expect_mode}"
if rec["mode"] == "real":
    assert (rec.get("response_preview") or "").strip(), "real groq returned empty content"

# both-route coverage (M06): strong path via direct router call (does not touch JSONL)
strong = call_model("strong", "Reply with the single word OK.")
print(f"[smoke] strong route: mode={strong['mode']} provider={strong['provider']} model={strong['model']}")
assert strong["provider"] == "openai" and strong["model"] == "gpt-4o", strong
if expect_mode:
    assert strong["mode"] == expect_mode, f"strong mode {strong['mode']} != {expect_mode}"
if strong["mode"] == "real":
    assert (strong.get("content") or "").strip(), "real openai returned empty content"

print(f"[smoke] PASS: cheap->groq/llama + strong->openai/gpt-4o; mode={rec['mode']}; late_risk unchanged")
print("[DONE] Step 6 routing smoke VERIFIED.")
