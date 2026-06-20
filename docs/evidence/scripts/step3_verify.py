import re, json
from pathlib import Path

g1  = Path("docs/evidence/step1_generated_models.py").read_text()
g3  = Path("docs/evidence/step3_generated_models.py").read_text()
log = Path("docs/evidence/step3_detection.log").read_text()
md  = json.loads(Path("docs/evidence/step3_generator_metadata_sent.json").read_text())

LATE = "late_risk = models.CharField(max_length=255, default='', null=True, blank=True)"

def find_attr(md, model, attr):
    for d in md["diagrams"]:
        if d.get("type") != "classes": continue
        for n in d["nodes"]:
            c = n.get("cls", {})
            if c.get("type") == "class" and c.get("name") == model:
                for a in c.get("attributes", []):
                    if a.get("name") == attr: return a
    return None

def parse_classes(src):
    return {m.group(1): m.group(2) for m in
            re.finditer(r"class (\w+)\(models\.Model\):(.*?)(?=\nclass |\Z)", src, re.S)}

def lineset(body):
    return {l.strip() for l in body.splitlines() if l.strip()}

# 1) ai_config reached the resolved metadata
la = find_attr(md, "BookLoan", "late_risk")
assert la and la.get("ai_config", {}).get("ai_config_version") == "1.0", "ai_config missing in metadata"
print("[PASS] resolved metadata carries BookLoan.late_risk.ai_config")

# 2) generator emitted the detection log
assert "[AI4MDE][ai_config]" in log and "attribute=late_risk" in log, "detection log line missing"
assert "detected 1 AI-managed attribute(s)" in log, "detection count line missing or != 1"
print("[PASS] generator logged ai_config detection for BookLoan.late_risk")

c1, c3 = parse_classes(g1), parse_classes(g3)

# 3) late_risk rendered as a stored CharField on BookLoan (which already carries its two FKs)
assert "late_risk = models.CharField" in c3.get("BookLoan", ""), "late_risk CharField not generated on BookLoan"
assert "late_risk" not in c1.get("BookLoan", ""), "Step 1 BookLoan unexpectedly already had late_risk"
print("[PASS] BookLoan.late_risk rendered as stored CharField (FKs preserved)")

# 4) detection-only: no NEW hook/AI artifact anywhere (count vs Step 1; robust to any pre-existing token)
for tok in ["ai_config", "post_save", "@receiver", "receiver(", "signals", ".update("]:
    assert g3.count(tok) == g1.count(tok), \
        f"'{tok}' occurrences changed {g1.count(tok)}->{g3.count(tok)} (possible Step 4 leakage)"
print("[PASS] no new hook/AI code in generated models.py (detection-only)")

# 5) order-insensitive: header identical, same class set, only BookLoan changed, and only by +late_risk
assert g1.split("class ", 1)[0] == g3.split("class ", 1)[0], "module header (imports) changed"
assert set(c1) == set(c3), f"model class set changed: {set(c1) ^ set(c3)}"
changed = [n for n in c1 if n != "BookLoan" and c1[n] != c3[n]]
assert not changed, f"classes changed beyond BookLoan: {changed}"
added   = lineset(c3["BookLoan"]) - lineset(c1["BookLoan"])
removed = lineset(c1["BookLoan"]) - lineset(c3["BookLoan"])
expected_added = {
    "late_risk = models.CharField(max_length=255, default='', null=True, blank=True)",
    "return str(self.late_risk)",
}
expected_removed = {"return str(self.Loan)"}
assert added == expected_added and removed == expected_removed, (
    f"BookLoan changed beyond the expected late_risk field + __str__ reselection "
    f"(added={added}, removed={removed}); run "
    "`diff docs/evidence/step1_generated_models.py docs/evidence/step3_generated_models.py`, "
    "confirm by inspection, and do NOT modify the generator to force a pass.")
print("[PASS] BookLoan delta == {late_risk CharField} + {__str__ self.Loan -> self.late_risk} (order-insensitive)")

print("[DONE] Step 3 ai_config detection VERIFIED.")
