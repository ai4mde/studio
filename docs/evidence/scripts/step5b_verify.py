import ast
import re
from pathlib import Path

m4 = Path("docs/evidence/step4_generated_models.py").read_text()
h4 = Path("docs/evidence/step4_generated_ai_hooks.py").read_text()
m5 = Path("docs/evidence/step5b_generated_models.py").read_text()
h5 = Path("docs/evidence/step5b_generated_ai_hooks.py").read_text()
apps = Path("docs/evidence/step5b_generated_apps.py").read_text()
rt = Path("docs/evidence/step5b_generated_ai_runtime_init.py").read_text()

# 1) regression: models.py and ai_hooks.py unchanged vs Step 4 (auth=False)
def parse_classes(src):
    return {m.group(1): m.group(2).strip() for m in
            re.finditer(r"class (\w+)\(models\.Model\):(.*?)(?=\nclass |\Z)", src, re.S)}

c4, c5 = parse_classes(m4), parse_classes(m5)
assert set(c4) == set(c5), f"model class SET changed vs Step 4: {set(c4) ^ set(c5)}"
body_diff = [n for n in c4 if c4[n] != c5[n]]
assert not body_diff, f"class body changed vs Step 4 (not just ordering): {body_diff}"
assert m4.split("class ", 1)[0] == m5.split("class ", 1)[0], "module header (imports) changed vs Step 4"
assert h5 == h4, "ai_hooks.py changed vs Step 4 (single hook -> byte-identical expected)"
print("[PASS] models.py & ai_hooks.py content unchanged vs Step 4 (class reorder is a benign metadata-ordering effect)")

# 2) apps.py wiring
ast.parse(apps)
assert "class SharedModelsConfig(AppConfig)" in apps, "missing SharedModelsConfig(AppConfig)"
assert 'name = "shared_models"' in apps, "AppConfig.name != shared_models"
assert "def ready(self)" in apps and "import shared_models.ai_hooks" in apps, "ready() must import shared_models.ai_hooks"
print("[PASS] apps.py: SharedModelsConfig.ready() imports shared_models.ai_hooks")

# 3) ai_runtime stub: contract + JSONL + NO LLM
ast.parse(rt)
assert "def invoke(ai_config, instance)" in rt, "stub must expose invoke(ai_config, instance)"
assert 'Path(settings.BASE_DIR) / "ai_invocations.jsonl"' in rt, "JSONL path must be settings.BASE_DIR/ai_invocations.jsonl"
assert "return None" in rt, "stub must return None"
for forbidden in ["openai", "groq", "OpenAI", "Groq", "import requests"]:
    assert forbidden not in rt, f"ai_runtime stub must not reference {forbidden}"
print("[PASS] ai_runtime stub: invoke()->None, JSONL at settings.BASE_DIR, no LLM deps")

print("[DONE] Step 5B generator assembly VERIFIED.")
