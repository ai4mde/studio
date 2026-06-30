import ast, json
from pathlib import Path

ev = Path("docs/evidence")

# 1) late_risk (Step 7) regression: post_save glue + BookLoan model unchanged.
#    routing.py is ALLOWED to differ (superset fake); we check ai_hooks.py + BookLoan only.
assert (ev / "step8_app_ai_hooks.py").read_text() == (ev / "step7_app_ai_hooks.py").read_text(), \
    "ai_hooks.py (late_risk post_save glue) changed vs Step 7"
def bookloan_block(src):
    lines = src.splitlines()
    out, grab = [], False
    for ln in lines:
        if ln.startswith("class BookLoan"):
            grab = True
        elif ln.startswith("class ") and grab:
            break
        if grab:
            out.append(ln)
    return "\n".join(out)
assert bookloan_block((ev / "step8_app_models.py").read_text()) == \
       bookloan_block((ev / "step7_app_models.py").read_text()), "BookLoan model changed vs Step 7"

# 2) trigger split: reading_plan must NOT have produced a post_save receiver on Customer
hooks_src = (ev / "step8_app_ai_hooks.py").read_text()
assert "sender=Customer" not in hooks_src, "user_action attribute wrongly produced a Customer post_save receiver"
assert "reading_plan" not in hooks_src, "reading_plan leaked into post_save hooks"

# 3) ai_actions.py present, parseable, attaches a bound method (not staticmethod)
actions = (ev / "step8_app_ai_actions.py").read_text()
ast.parse(actions)
assert "def generate_reading_plan(instance):" in actions, "action function missing"
assert "Customer.generate_reading_plan = generate_reading_plan" in actions, "method not attached as plain function"
assert "staticmethod" not in actions, "should attach plain function (bound method), not staticmethod"

# 4) vendored M04 chains.py: pure python, no llm/django
chains = (ev / "step8_app_ai_runtime_chains.py").read_text()
ast.parse(chains)
assert "ChainRunner" in chains
for forbidden in ["from llm", "import llm", "from django", "import django"]:
    assert forbidden not in chains, f"vendored chains.py leaks {forbidden}"

# 4b) templates.py registry knows the three chain prompts (else render_prompt raises Invalid prompt name)
templates_py = (ev / "step8_app_ai_runtime_templates.py").read_text()
for key in ["reading_plan_analyze_taste_v1", "reading_plan_recommend_v1", "reading_plan_sequence_v1"]:
    assert key in templates_py, f"templates.py registry missing {key}"

# 4b) M01 evidence: each chain step's prompt template entered the generated runtime
for tname in ["reading_plan_analyze_taste_v1.j2", "reading_plan_recommend_v1.j2", "reading_plan_sequence_v1.j2"]:
    t = (ev / f"step8_app_prompt_{tname}").read_text()
    assert t.strip(), f"chain template {tname} missing/empty"
    assert "ONLY JSON" in t or "Return ONLY" in t, f"chain template {tname} missing strict-output instruction"

# 5) 8B deterministic chain end-to-end
b = json.loads([l for l in (ev / "step8b_ai_invocations.jsonl").read_text().splitlines() if l.strip()][0])
assert b["event"] == "invoke_chain" and b["status"] == "success", b
assert b["trigger"] == "user_action" and b["mode"] == "fake", b
assert [s["step"] for s in b["step_details"]] == ["analyze_taste", "recommend", "sequence"], b["step_details"]
assert b["write_back"]["field"] == "reading_plan" and b["write_back"]["value"], b
assert "[DONE] Step 8 reading_plan chain end-to-end VERIFIED." in (ev / "step8b_smoke.log").read_text()

# 5b) M02 substrate proven at runtime (the chain consumed the member's real borrow history).
#     Fake content is context-independent, so this marker is the only proof the M02 ORM traversal is
#     live; the smoke asserts _build_taste_context returns exactly the seeded books before printing it.
assert "[smoke] M02 substrate OK:" in (ev / "step8b_smoke.log").read_text(), \
    "8B did not prove M02 substrate (empty/incorrect borrowed_books)"

# 6) 8C real chain end-to-end — present or documented deferral
p8c = ev / "step8c_ai_invocations.jsonl"
deferred = ev / "step8c_deferred.md"
if p8c.exists() and p8c.read_text().strip():
    c = json.loads([l for l in p8c.read_text().splitlines() if l.strip()][0])
    assert c["mode"] == "real" and c["status"] == "success", c
    assert len(c["step_details"]) == 3 and c["write_back"]["value"], c
    assert "[smoke] M02 substrate OK:" in (ev / "step8c_smoke.log").read_text(), \
        "8C real run did not prove M02 substrate"
    print("[PASS] 8C real strong-model chain verified")
else:
    assert deferred.exists() and deferred.read_text().strip(), "8C absent but step8c_deferred.md missing"
    print("[INFO] 8C deferred with documented reason")

print("[PASS] Step 8 verified: M04 user-action chain produces reading_plan end-to-end; "
      "late_risk post_save path unchanged vs Step 7")
