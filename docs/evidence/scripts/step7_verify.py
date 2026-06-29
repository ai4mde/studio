import ast
import json
from pathlib import Path

ev = Path("docs/evidence")

# 1) regression: generated glue + model byte-identical to Step 5C
for new, base in [("step7_app_models.py", "step5c_app_models.py"),
                  ("step7_app_ai_hooks.py", "step5c_app_ai_hooks.py"),
                  ("step7_app_apps.py", "step5c_app_apps.py")]:
    assert (ev / new).read_text() == (ev / base).read_text(), f"{new} changed vs 5C baseline {base}"

# 2) ai_runtime is now a package with the expected files, all parseable
for f in ["__init__.py", "routing.py", "context.py", "templates.py", "parsers.py"]:
    src = (ev / f"step7_app_ai_runtime_{f}").read_text()
    ast.parse(src)
init = (ev / "step7_app_ai_runtime___init__.py").read_text()
assert "build_context" in init and "render_prompt" in init and "call_model" in init and "JsonOutputParser" in init, \
    "invoke does not orchestrate all four mechanisms"
parsers = (ev / "step7_app_ai_runtime_parsers.py").read_text()
assert "JsonOutputParser" in parsers and "_JSON_FENCE_PATTERN" in parsers, "vendored M03 parser/fence-strip missing"
# both vendored mechanism files must be free of Studio/llm/django coupling
for vfile in ["step7_app_ai_runtime_templates.py", "step7_app_ai_runtime_parsers.py"]:
    vsrc = (ev / vfile).read_text()
    for forbidden in ["from llm", "import llm", "django"]:
        assert forbidden not in vsrc, f"vendored file {vfile} leaks {forbidden}"
# M01 evidence: the prompt template actually entered the generated runtime
prompt_tmpl = (ev / "step7_app_prompt_library_late_risk_v1.j2").read_text()
assert "late-return risk" in prompt_tmpl, "prompt template missing task framing"
assert '{"late_risk": "LOW"}' in prompt_tmpl, "prompt template missing exact output shape"

# 3) 7A deterministic end-to-end
a = json.loads([l for l in (ev / "step7a_ai_invocations.jsonl").read_text().splitlines() if l.strip()][0])
assert a["event"] == "invoke" and a["status"] == "success", a
assert a["mode"] == "fake" and a["write_back"] == {"field": "late_risk", "value": "LOW"}, a
assert a["context"]["loan_date"] == "2026-01-01", a["context"]
assert "[DONE] Step 7 late_risk end-to-end VERIFIED." in (ev / "step7a_smoke.log").read_text(), "7A smoke incomplete"

# 4) 7B real end-to-end - present or documented deferral
p7b = ev / "step7b_ai_invocations.jsonl"
deferred = ev / "step7b_deferred.md"
if p7b.exists() and p7b.read_text().strip():
    b = json.loads([l for l in p7b.read_text().splitlines() if l.strip()][0])
    assert b["mode"] == "real" and b["status"] == "success", b
    assert b["provider"] == "groq" and b["write_back"]["value"] in ("LOW", "MEDIUM", "HIGH"), b
    assert b["raw_output"].strip(), "real raw_output empty"
    print("[PASS] 7B real end-to-end verified (late_risk written from a real provider)")
else:
    assert deferred.exists() and deferred.read_text().strip(), \
        "7B absent but step7b_deferred.md missing"
    print("[INFO] 7B deferred with documented reason")

print("[PASS] Step 7 verified: M01+M02+M03+M05+M06+M07 produce late_risk end-to-end; "
      "generated hook/model unchanged vs 5C")
