"""
Step 1 (Phase 1E) — Trigger prototype generation via the OFFICIAL A2 route:

    Studio DB
      -> Django generator API   (POST /api/v1/generator/prototypes/)
        -> studio-prototypes Flask /generate
          -> generator.sh -> generated Django app (shared_models/models.py)

This is the official Step 1 generation route (Decision 3). A direct generate_models.py
dry-run is only a preflight diagnostic and does NOT replace this.

KEY CODEBASE FACTS this script relies on (all verified against the source):
  * Endpoint: POST /api/v1/generator/prototypes/?database_prototype_name=
    (database_prototype_name is a REQUIRED query param; empty string is fine -> skips DB copy)
  * Body schema CreatePrototype = {name, description, system, database_hash, metadata}
    `metadata` is a JSONField -> the resolved generator metadata dict passes straight through;
    create_prototype forwards json.dumps(metadata) to Flask /generate unchanged.
  * Auth: NinjaAPI(auth=[CookieToken, BearerToken]). We mint a short-lived JWT
    (settings.SECRET_KEY) for a superuser and send it as `Authorization: Bearer`.
  * Generator metadata MUST be the RESOLVED/flat shape (NOT the import JSON):
      node.cls      = classifier DATA dict (flat: name/type/attributes/methods/literals)
      node.cls_ptr  = classifier UUID
      edge.rel      = relation DATA dict (flat: type/multiplicity/...)
      edge.rel_ptr  = relation UUID
      edge.source_ptr / edge.target_ptr = NODE UUIDs (node whose cls == rel.source/target)
    and the top level MUST include `interfaces: []`
    (VERIFIED: missing `interfaces` makes generator.sh get_apps raise -> set -e -> exit 1
     BEFORE shared_models/models.py is generated). `useAuthentication` is optional.
  * This resolved shape is exactly what diagram.api.schemas.diagram.FullDiagram /
    NodeSchema.resolve_cls / EdgeSchema.resolve_source_ptr produce; we rebuild it
    inline from the ORM so the script is self-contained and debuggable.

HOW TO RUN (inside studio-api container, after step1_import_library.py succeeded):
    docker compose exec studio-api python manage.py shell
    >>> exec(open('<path>/step1_generate_prototype.py').read())

IDEMPOTENCY WARNING:
    generator.sh aborts with exit 1 if the prototype directory already exists
    ("Directory with project name already exists"). Re-running with the same
    PROTOTYPE_NAME will fail at the Flask layer (HTTP 500 from the Django view).
    Either set a unique name (STEP1_PROTOTYPE_NAME env) or remove the previous
    generated artifact first (DELETE /api/v1/generator/prototypes/{id}/ or rm the dir).
"""
import datetime
import json
import os

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt import encode as jwt_encode

from metadata.models import Project
from diagram.models import Diagram, Edge

# ---- config -----------------------------------------------------------------
# API_BASE: the reachable base URL of the Studio Django API *from wherever this
#   script runs*. Default assumes the dev server listens on localhost:8000 inside
#   the studio-api container. THIS IS A RUNTIME-CONFIRM ITEM, not a code bug:
#   if the POST fails with a connection error, the API is simply reachable under a
#   different base (e.g. http://studio-api:8000 from another container, or the
#   traefik host http://api.ai4mde.localhost). Retry with STEP1_API_BASE set, and
#   do NOT report a connection error as a generator failure.
API_BASE = os.environ.get("STEP1_API_BASE", "http://localhost:8000")
PROTOTYPE_NAME = os.environ.get("STEP1_PROTOTYPE_NAME", "LibraryStep1")
PROJECT_NAME = os.environ.get("STEP1_PROJECT_NAME", "Library")

# ---- locate imported project/system ----------------------------------------
project = Project.objects.filter(name=PROJECT_NAME).order_by("-id").first()
assert project is not None, f"project '{PROJECT_NAME}' not found - run step1_import_library.py first"
system = project.systems.all().first()
assert system is not None, "system not found under project"
print(f"[step1-gen] project={project.id} system={system.id}")

# ---- build RESOLVED generator metadata (shape (3)) from the ORM -------------
diagrams_meta = []
for diagram in Diagram.objects.filter(system=system):
    # one node per (diagram, classifier); map classifier id -> node id for ptr resolution
    nodes = list(diagram.nodes.select_related("cls").all())
    node_id_by_cls = {str(n.cls_id): str(n.id) for n in nodes}

    meta_nodes = [{
        "id": str(n.id),
        "cls": n.cls.data,            # flat classifier data  (== NodeSchema.resolve_cls)
        "cls_ptr": str(n.cls_id),     # == NodeSchema.resolve_cls_ptr
        "data": n.data or {"position": {"x": 0, "y": 0}},
    } for n in nodes]

    meta_edges = []
    for e in Edge.objects.filter(diagram=diagram).select_related("rel"):
        src_node = node_id_by_cls.get(str(e.rel.source_id))
        tgt_node = node_id_by_cls.get(str(e.rel.target_id))
        # both endpoints must have a node in this diagram (FullDiagram would also require this)
        if src_node is None or tgt_node is None:
            print(f"[step1-gen] WARN edge {e.id}: endpoint node missing in diagram; skipping")
            continue
        meta_edges.append({
            "id": str(e.id),
            "rel": e.rel.data,          # flat relation data (== EdgeSchema.resolve_rel)
            "rel_ptr": str(e.rel_id),
            "source_ptr": src_node,     # NODE id (== EdgeSchema.resolve_source_ptr)
            "target_ptr": tgt_node,
            "data": e.data or {},
        })

    diagrams_meta.append({
        "id": str(diagram.id),
        "type": diagram.type,
        "name": diagram.name,
        "description": diagram.description or "",
        "nodes": meta_nodes,
        "edges": meta_edges,
    })

# useAuthentication: Studio's workflow_engine app ALWAYS does
#   `from shared_models.models import User`, but User is only generated when auth is on.
#   So an auth-OFF project can never migrate/run. Set STEP1_USE_AUTH=1 to generate a
#   runnable app (adds only a bare `class User(AbstractUser): pass` to shared_models;
#   the domain models are unchanged). Default stays False to preserve the original
#   pure-structural intent for diffing.
USE_AUTH = os.environ.get("STEP1_USE_AUTH", "0") == "1"

metadata = {
    "diagrams": diagrams_meta,
    "interfaces": [],            # MANDATORY (verified) - empty is fine
    "useAuthentication": USE_AUTH,
}
print(f"[step1-gen] useAuthentication={USE_AUTH}")

# persist the exact payload as evidence (fixed path: exec()-mode has no real __file__)
payload_path = os.environ.get("STEP1_SENT_METADATA", "/tmp/step1_generator_metadata_sent.json")
with open(payload_path, "w", encoding="utf-8") as fh:
    json.dump(metadata, fh, indent=2)
print(f"[step1-gen] wrote resolved metadata -> {payload_path}")

# ---- mint a Bearer token for a superuser (no plaintext password needed) -----
admin = get_user_model().objects.filter(is_superuser=True).order_by("id").first()
assert admin is not None, "no superuser found - create one with manage.py create_admin"
now = datetime.datetime.now(tz=datetime.timezone.utc)
token = jwt_encode(
    {"exp": now + datetime.timedelta(hours=1), "nbf": now, "iss": "urn:ai4mdestudio",
     "iat": now, "uid": admin.id},
    settings.SECRET_KEY,
)
if isinstance(token, bytes):  # PyJWT<2 returns bytes
    token = token.decode()

# ---- POST to the Django generator API (A2) ----------------------------------
# NOTE: database_prototype_name is a REQUIRED query param on the view; empty -> skips DB copy.
# Pass it ONCE via params= (do not also append it to the URL string).
url = f"{API_BASE}/api/v1/generator/prototypes/"
body = {
    "name": PROTOTYPE_NAME,
    "description": "Thesis Step 1 Library prototype",
    "system_id": str(system.id),   # ninja ModelSchema exposes the FK as system_id
    "database_hash": None,
    "metadata": metadata,
}
print(f"[step1-gen] POST {url}?database_prototype_name=\n[step1-gen] name={PROTOTYPE_NAME} system={system.id}")
resp = requests.post(url, params={"database_prototype_name": ""},
                     json=body, headers={"Authorization": f"Bearer {token}"}, timeout=300)
print(f"[step1-gen] HTTP {resp.status_code}")
print(resp.text[:2000])

if resp.status_code == 200:
    print("\n[step1-gen] GENERATION TRIGGERED OK")
    print(f"[step1-gen] Phase 1F: inspect generated models inside studio-prototypes container at")
    print(f"    /usr/src/prototypes/generated_prototypes/{system.id}/{PROTOTYPE_NAME}/shared_models/models.py")
else:
    print("\n[step1-gen] GENERATION FAILED — see response above.")
    print("    If models.py was already produced before a later (non-domain) stage failed,")
    print("    preserve shared_models/models.py as model-layer evidence and STOP (do not edit generator).")
