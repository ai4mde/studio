import ast
import json
from pathlib import Path

ev = Path("docs/evidence")

# 1) regression: generated glue + model byte-identical to Step 5C baseline
for new, base in [("step6_app_models.py", "step5c_app_models.py"),
                  ("step6_app_ai_hooks.py", "step5c_app_ai_hooks.py"),
                  ("step6_app_apps.py", "step5c_app_apps.py")]:
    assert (ev / new).read_text() == (ev / base).read_text(), f"{new} changed vs 5C baseline {base}"

# 2) ai_runtime is now the router (and differs from the 5C stub)
rt = (ev / "step6_app_ai_runtime_init.py").read_text()
assert rt != (ev / "step5c_app_ai_runtime_init.py").read_text(), "ai_runtime unchanged - router not emitted"
assert "MODEL_PROFILES" in rt and "def call_model" in rt, "router scaffolding missing"
assert '"groq"' in rt and '"openai"' in rt, "providers missing in MODEL_PROFILES"
assert "llama-3.3-70b-versatile" in rt and "gpt-4o" in rt, "model strings missing"
assert "return None" in rt, "invoke must still return None at Step 6"
# openai/groq must be LAZY (not imported at module top level)
top = " ".join(ast.dump(n) for n in ast.parse(rt).body if isinstance(n, (ast.Import, ast.ImportFrom)))
assert "groq" not in top and "openai" not in top, "openai/groq must be lazy-imported, not at module top"

# 3) 6A record (deterministic fake)
a = json.loads([l for l in (ev / "step6a_ai_invocations.jsonl").read_text().splitlines() if l.strip()][0])
assert a["mode"] == "fake" and a["provider"] == "groq" and a["model_profile"] == "cheap", a
assert a["routed_model"] == "llama-3.3-70b-versatile", a
assert "[DONE] Step 6 routing smoke VERIFIED." in (ev / "step6a_smoke.log").read_text(), "6A smoke incomplete"

# 4) 6B record (real) - present only if the gated real run happened; otherwise the
#    deferral MUST be documented (no silent skip)
p6b = ev / "step6b_ai_invocations.jsonl"
deferred = ev / "step6b_deferred.md"
if p6b.exists() and p6b.read_text().strip():
    b = json.loads([l for l in p6b.read_text().splitlines() if l.strip()][0])
    assert b["mode"] == "real" and b["provider"] == "groq", b
    assert (b.get("response_preview") or "").strip(), "real provider empty content"
    assert "[DONE] Step 6 routing smoke VERIFIED." in (ev / "step6b_smoke.log").read_text(), "6B smoke incomplete"
    print("[PASS] 6B real provider run verified (cheap->groq reachable)")
else:
    assert deferred.exists() and deferred.read_text().strip(), \
        "6B absent but docs/evidence/step6b_deferred.md missing - document the deferral"
    print("[INFO] 6B deferred with documented reason (step6b_deferred.md present)")

print("[PASS] Step 6 (M06) verified: generated hook unchanged; runtime routes by model_profile; late_risk unchanged")
