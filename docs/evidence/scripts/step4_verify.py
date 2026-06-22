import ast, json
from pathlib import Path

g3 = Path("docs/evidence/step3_generated_models.py").read_text()
m4 = Path("docs/evidence/step4_generated_models.py").read_text()
hk = Path("docs/evidence/step4_generated_ai_hooks.py").read_text()
md = json.loads(Path("docs/evidence/step3_generator_metadata_sent.json").read_text())

def find_attr(md, model, attr):
    for d in md["diagrams"]:
        if d.get("type") != "classes": continue
        for n in d["nodes"]:
            c = n.get("cls", {})
            if c.get("type") == "class" and c.get("name") == model:
                for a in c.get("attributes", []):
                    if a.get("name") == attr: return a
    return None

expected_cfg = find_attr(md, "BookLoan", "late_risk")["ai_config"]

# 1) domain layer untouched
assert m4 == g3, "models.py changed in Step 4 (must be byte-identical to Step 3)"
print("[PASS] models.py unchanged vs Step 3")

# 2) ai_hooks.py is valid Python
tree = ast.parse(hk)
print("[PASS] ai_hooks.py parses as valid Python")

# 3) imports + exactly one BookLoan post_save receiver
assert "from shared_models.models import BookLoan" in hk, "missing BookLoan import"
assert "from django.db.models.signals import post_save" in hk, "missing post_save import"
assert "from django.dispatch import receiver" in hk, "missing receiver import"
assert hk.count("@receiver(post_save, sender=BookLoan)") == 1, "expected exactly one BookLoan post_save receiver"
print("[PASS] imports present; exactly one @receiver(post_save, sender=BookLoan)")

# 4) embedded _AI_CONFIG round-trips to the declared ai_config
cfg_assign = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id.startswith("_AI_CONFIG__") for t in node.targets):
        cfg_assign = node
assert cfg_assign is not None, "no _AI_CONFIG__* assignment found"
embedded = ast.literal_eval(cfg_assign.value)
assert embedded == expected_cfg, f"embedded ai_config != declared ai_config\nembedded={embedded}\nexpected={expected_cfg}"
print("[PASS] embedded _AI_CONFIG matches the declared ai_config exactly")

# 5) single-entry contract + guards + recursion safety
assert "from ai_runtime import invoke" in hk, "missing lazy ai_runtime import"
assert "except ImportError" in hk, "import guard must be except ImportError (not broad Exception)"
assert "if value is None" in hk, "missing None guard"
assert "BookLoan.objects.filter(pk=instance.pk).update(late_risk=value)" in hk, "missing recursion-safe write-back"
assert "instance.save(" not in hk, "must NOT use instance.save() (would recurse)"
print("[PASS] single-entry invoke contract, None guard, recursion-safe .update(), no instance.save()")

print("[DONE] Step 4 ai_hooks generation VERIFIED.")
