"""
Step 1 (Phase 1C/1D) — Import the Library project into Studio via the ORM.

WHY ORM (not the HTTP import endpoint):
    Step 1 tests the import schema + generator, not HTTP auth. Project.import_from_json
    is the real callable behind POST /api/v1/metadata/projects/import/, so calling it
    directly is the most stable, reproducible path and avoids cookie/token handling.

HOW TO RUN (inside the studio-api container, repo mounted at /usr/src/model):
    # copy step1_library_model.json next to this script, or pass an absolute path
    docker compose exec studio-api \
        python manage.py shell -c "exec(open('/usr/src/model/../docs/evidence/scripts/step1_import_library.py').read())"
    # simpler: open a shell and run
    #   docker compose exec studio-api python manage.py shell
    #   >>> exec(open('<path>/step1_import_library.py').read())

IDEMPOTENCY:
    Project.import_from_json upserts by fixed UUIDs and reconciles children
    (delete_missing), so re-running this is safe and converges to the same DB state.

This script does NOT modify Studio source code. It lives under docs/evidence/scripts/.
"""
import json
import os

from metadata.models import Project, Classifier, Relation

# ---- locate the model JSON (env override, else alongside this file) --------
JSON_PATH = os.environ.get(
    "STEP1_LIBRARY_JSON",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "step1_library_model.json"),
)
JSON_PATH = os.path.abspath(JSON_PATH)
print(f"[step1-import] loading {JSON_PATH}")

with open(JSON_PATH, "r", encoding="utf-8") as fh:
    data = json.load(fh)

# ---- import -----------------------------------------------------------------
project = Project.import_from_json(data)
print(f"[step1-import] imported project: {project.name} ({project.id})")

# ---- verify (Phase 1D) ------------------------------------------------------
# NOTE: related_name on System.project is 'systems' -> use project.systems.all()
systems = list(project.systems.all())
assert len(systems) == 1, f"expected 1 system, got {len(systems)}"
system = systems[0]

classifiers = list(Classifier.objects.filter(system=system))
relations = list(Relation.objects.filter(system=system))
diagrams = list(system.diagrams.all())
interfaces = list(system.interfaces.all())

class_count = sum(1 for c in classifiers if (c.data or {}).get("type") == "class")
enum_count = sum(1 for c in classifiers if (c.data or {}).get("type") == "enum")
classes_diagrams = [d for d in diagrams if d.type == "classes"]

print("\n[step1-import] ===== DB STATE =====")
print(f"  System         : {system.name} ({system.id})")
print(f"  Classifiers    : {len(classifiers)}  (classes={class_count}, enum={enum_count})")
for c in classifiers:
    d = c.data or {}
    print(f"      - {d.get('name'):<14} type={d.get('type')}")
print(f"  Relations      : {len(relations)}")
for r in relations:
    rd = r.data or {}
    src = (Classifier.objects.get(pk=r.source_id).data or {}).get("name")
    tgt = (Classifier.objects.get(pk=r.target_id).data or {}).get("name")
    print(f"      - {src} -> {tgt}  ({rd.get('type')}, mult={rd.get('multiplicity')})")
print(f"  Diagrams       : {len(diagrams)} (classes={len(classes_diagrams)})")
for d in classes_diagrams:
    # Phase 1E builds the generator metadata from these nodes/edges, so report them here.
    print(f"      - {d.name:<12} type=classes nodes={d.nodes.count()} edges={d.edges.count()}")
print(f"  Interfaces     : {len(interfaces)} (expected 0 for Step 1 pure class-model generation)")

# ---- assertions (the Phase 1D gate) ----------------------------------------
assert len(classifiers) == 6, f"expected 6 classifiers, got {len(classifiers)}"
assert class_count == 5, f"expected 5 classes, got {class_count}"
assert enum_count == 1, f"expected 1 enum, got {enum_count}"
assert len(relations) == 4, f"expected 4 relations, got {len(relations)}"
assert len(classes_diagrams) >= 1, "expected at least 1 classes diagram"
print("\n[step1-import] PHASE 1D GATE PASSED: 6 classifiers (5 class + 1 enum) + 4 relations")
print(f"[step1-import] SYSTEM_ID for Phase 1E = {system.id}")
