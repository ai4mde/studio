from pathlib import Path

apps = Path("docs/evidence/step5c_app_apps.py").read_text()
rt = Path("docs/evidence/step5c_app_ai_runtime_init.py").read_text()
models = Path("docs/evidence/step5c_app_models.py").read_text()
smoke = Path("docs/evidence/step5c_smoke.log").read_text()
check = Path("docs/evidence/step5c_migrate_check.log").read_text()

# migrate: check passed + every target app has applied migrations and none unapplied
assert "System check identified no issues" in check, "manage.py check did not pass cleanly"
for app in ["shared_models", "workflow_engine", "authentication", "librarian"]:
    assert app in check, f"{app} not present in showmigrations output"
assert "[X]" in check, "no applied migrations found"
assert "[ ]" not in check, "some migrations are UNapplied ([ ] present)"
# wiring
assert "def ready(self)" in apps and "import shared_models.ai_hooks" in apps, "apps.py ready() does not import ai_hooks"
assert "def invoke(ai_config, instance)" in rt and "return None" in rt, "ai_runtime stub missing/altered"
for forbidden in ["openai", "groq", "OpenAI", "Groq"]:
    assert forbidden not in rt, f"ai_runtime references {forbidden}"
# auth role field
assert "is_librarian" in models, "User.is_librarian not generated (auth+interface)"
# smoke outcome
assert "[DONE] Step 5C wiring smoke VERIFIED." in smoke, "smoke did not complete"
assert "late_risk unchanged" in smoke, "smoke did not confirm no write-back"
assert "ai_runtime.invoke is not callable" not in smoke, "ai_runtime.invoke import-contract failed"
print("[PASS] Step 5C assembly + migrate + smoke all verified")
