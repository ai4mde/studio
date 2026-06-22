import json, uuid
from pathlib import Path

SRC = Path("docs/evidence/step2_library_model.json")
OUT = Path("docs/evidence/step5_library_model.json")

art = json.loads(SRC.read_text())
system = art["systems"][0]
system_id = system["id"]
project_id = art["id"]

# locate BookLoan classifier + its late_risk attribute (to mirror into the section)
bookloan = next(c for c in system["classifiers"]
                if c["data"].get("name") == "BookLoan" and c["data"].get("type") == "class")
late_risk_attr = next(a for a in bookloan["data"].get("attributes", []) if a["name"] == "late_risk")
# section.attributes uses the editor-facing attribute fields only (no ai_config)
section_attr = {k: late_risk_attr.get(k) for k in ("body", "enum", "name", "type", "derived", "description")}

actor_id   = str(uuid.uuid4())
iface_id   = str(uuid.uuid4())
page_id    = str(uuid.uuid4())
section_id = str(uuid.uuid4())

# 1) actor classifier (mirror the key shape of an existing classifier)
sample = system["classifiers"][0]
actor_clf = {
    "id": actor_id,
    "project": sample.get("project", project_id),
    "system": system_id,
    "original_system_id": None,
    "data": {"name": "librarian", "type": "actor"},
}

# 2) librarian interface (normal CRUD page over BookLoan)
interface = {
    "id": iface_id,
    "system": system_id,
    "name": "librarian",
    "description": "Librarian application",
    "actor": actor_id,
    "data": {
        "pages": [{
            "id": page_id,
            "name": "loans",
            "type": {"label": "Normal", "value": "normal"},
            "action": None,
            "category": None,
            "sections": [{"label": "book_loans", "value": section_id}],
        }],
        "styling": {"radius": 0, "textColor": "#000000", "accentColor": "#F5F5F4",
                    "selectedStyle": "modern", "backgroundColor": "#FFFFFF"},
        "sections": [{
            "id": section_id,
            "name": "book_loans",
            "text": "Book loans",
            "class": bookloan["id"],
            "attributes": [section_attr],
            "operations": {"create": True, "delete": False, "update": True},
        }],
        "settings": {"managerAccess": False},
        "categories": [],
    },
}

system.setdefault("classifiers", []).append(actor_clf)
system.setdefault("interfaces", []).append(interface)

OUT.write_text(json.dumps(art, indent=2, ensure_ascii=False))
print(f"[step5a-build] wrote {OUT}")
print(f"[step5a-build] actor={actor_id} interface={iface_id} section.class(BookLoan)={bookloan['id']}")
