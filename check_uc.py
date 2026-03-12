import os, sys, django
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()
from metadata.models import Classifier, Relation, System
system_id = "8ac86bfe-ec5d-4b2e-b381-d84392dc9f08"
system = System.objects.get(id=system_id)

# Check use cases for Applicant
actor_ucs = set()
for rel in system.relations.filter(data__type="interaction").select_related("source", "target"):
    src = rel.source.data
    tgt = rel.target.data
    if src.get("type") == "actor" and src.get("name") == "Applicant":
        actor_ucs.add(tgt.get("name", "").lower())
    elif tgt.get("type") == "actor" and tgt.get("name") == "Applicant":
        actor_ucs.add(src.get("name", "").lower())
print(f"Applicant use cases: {actor_ucs}")

# Check which classes match
for uc_name in actor_ucs:
    for c in system.classifiers.filter(data__type="class"):
        cls_name = c.data.get("name", "")
        if cls_name.lower() in uc_name:
            print(f"  UC '{uc_name}' matches class '{cls_name}'")

# Check composition groups
rels = list(system.relations.filter(data__type__in=["composition", "association"]))
print(f"\nComposition/Association relations:")
for rel in rels:
    src = rel.source.data.get("name", "?")
    tgt = rel.target.data.get("name", "?")
    rtype = rel.data.get("type", "?")
    print(f"  {src} --[{rtype}]--> {tgt}")
