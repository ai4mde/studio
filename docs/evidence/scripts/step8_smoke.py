import json, os
from pathlib import Path
from django.conf import settings
from shared_models.models import Author, Book, Customer, Loan, BookLoan

expect_mode = os.environ.get("EXPECT_MODE")  # 'fake' | 'real'
log_path = Path(settings.BASE_DIR) / "ai_invocations.jsonl"
if log_path.exists():
    log_path.unlink()

# member with borrow history (M02 substrate for analyze_taste).
# NOTE: creating BookLoans fires the Step 7 post_save -> late_risk invoke (expected: late_risk
# path is unchanged). In real mode (8C) that invoke would make a real cheap/Groq call, which would
# wrongly require GROQ_API_KEY just for setup. So force setup into FAKE mode regardless of
# expect_mode, then restore env before the reading_plan call. Two separate concerns:
#   - clearing the log (below) removes late_risk *records* from the assertion;
#   - forcing setup-fake removes the late_risk *provider dependency* (no Groq needed in 8C).
_original_fake = os.environ.get("AI_RUNTIME_FAKE")
os.environ["AI_RUNTIME_FAKE"] = "1"
try:
    cust = Customer.objects.create(name="M. Member", email="m@example.com")
    auth = Author.objects.create(name="A. Writer", nationality="NL")
    for t in ["Dune", "Neuromancer", "Foundation"]:
        bk = Book.objects.create(title=t, Author=auth)
        ln = Loan.objects.create(loan_date="2026-01-01", due_date="2026-01-15", return_date="2026-01-10", Customer=cust)
        BookLoan.objects.create(Loan=ln, Book=bk)   # late_risk post_save runs FAKE here
finally:
    if _original_fake is None:
        os.environ.pop("AI_RUNTIME_FAKE", None)
    else:
        os.environ["AI_RUNTIME_FAKE"] = _original_fake

# isolate: discard setup's late_risk records so the chain record is the only line
if log_path.exists():
    log_path.unlink()

# M02 substrate check (deterministic, MODE-INDEPENDENT): the chain's context builder MUST pull the
# member's real borrow history. Fake content is context-independent, so without this assertion
# NEITHER 8B nor 8C would catch a broken _build_taste_context (empty borrowed_books) — the chain
# would still "succeed" on fake/hallucinated output. Assert the ORM traversal returns exactly the
# seeded books; the printed marker is the only host-visible proof that M02 wiring is live.
from ai_runtime.reading_plan import _build_taste_context
_m02 = _build_taste_context(cust)["borrowed_books"]
_m02_titles = sorted(b["title"] for b in _m02)
assert _m02_titles == ["Dune", "Foundation", "Neuromancer"], f"M02 context wrong: {_m02}"
print(f"[smoke] M02 substrate OK: {len(_m02)} borrowed books -> {_m02_titles}")

# user-action trigger (M): plain-function attach => bound method.
# reading_plan now runs under the caller's mode (fake in 8B; real/strong->OpenAI in 8C).
assert hasattr(cust, "generate_reading_plan"), "Customer.generate_reading_plan not attached (attach_actions/apps.ready)"
returned = cust.generate_reading_plan()          # bound: instance == cust
cust.refresh_from_db()
print(f"[smoke] reading_plan={cust.reading_plan!r}")

assert log_path.exists(), "ai_invocations.jsonl not created"
lines = [ln for ln in log_path.read_text().splitlines() if ln.strip()]
assert len(lines) == 1, f"expected exactly 1 chain record, got {len(lines)}"
rec = json.loads(lines[0])
print(f"[smoke] event={rec['event']} status={rec['status']} mode={rec.get('mode')} steps={len(rec.get('step_details', []))}")
assert rec["event"] == "invoke_chain", rec["event"]
assert rec["trigger"] == "user_action", rec["trigger"]
assert rec["model"] == "Customer" and rec["pk"] == cust.pk
assert rec["model_profile"] == "strong", rec["model_profile"]
assert rec["status"] == "success", f"status={rec['status']} failed_step={rec.get('failed_step')}"
assert len(rec["step_details"]) == 3, rec["step_details"]
assert [s["step"] for s in rec["step_details"]] == ["analyze_taste", "recommend", "sequence"], rec["step_details"]
assert rec["write_back"]["field"] == "reading_plan"
assert cust.reading_plan and len(cust.reading_plan) <= 255, repr(cust.reading_plan)
assert cust.reading_plan == rec["write_back"]["value"] == returned, (cust.reading_plan, rec["write_back"], returned)
if expect_mode:
    assert rec["mode"] == expect_mode, f"mode {rec['mode']} != {expect_mode}"
if rec["mode"] == "real":
    assert all(s.get("raw_response", "").strip() for s in rec["step_details"]), "real chain has empty step raw_response"

print(f"[smoke] PASS: user_action -> M04 chain (analyze_taste -> recommend -> sequence) "
      f"-> reading_plan written ({len(cust.reading_plan)} chars, mode={rec['mode']})")
print("[DONE] Step 8 reading_plan chain end-to-end VERIFIED.")
