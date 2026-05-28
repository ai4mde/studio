import json
import time

import requests

from app.tools import METADATA_API_BASE, _AUTH_HEADERS


iface_id = "26608863-59e7-41eb-bc17-5221c6d2ea38"
api = METADATA_API_BASE.rsplit("/metadata", 1)[0]

r = requests.post(
    f"{METADATA_API_BASE}/interfaces/{iface_id}/candidates/0/apply/",
    headers=_AUTH_HEADERS,
    timeout=30,
)
print("apply", r.status_code, r.text[:120])
r.raise_for_status()

iface = requests.get(
    f"{METADATA_API_BASE}/interfaces/{iface_id}/",
    headers=_AUTH_HEADERS,
    timeout=30,
).json()
system_id = iface.get("system") or iface.get("system_id")
diagrams = requests.get(
    f"{api}/diagram/system/{system_id}/",
    headers=_AUTH_HEADERS,
    timeout=30,
).json()
all_ifaces = requests.get(
    f"{METADATA_API_BASE}/interfaces/",
    headers=_AUTH_HEADERS,
    params={"system": system_id},
    timeout=30,
).json()
if not isinstance(all_ifaces, list):
    all_ifaces = all_ifaces.get("items", [])

name = "sync_codex_nav_check_" + str(int(time.time()))
body = {
    "name": name,
    "description": "Codex preview/live nav check",
    "system_id": system_id,
    "database_hash": f"sync-{system_id}-{iface_id}-codex-nav-check",
    "metadata": {
        "diagrams": diagrams,
        "interfaces": [
            {"label": it.get("name"), "value": iface if it.get("id") == iface_id else it}
            for it in all_ifaces
        ],
        "useAuthentication": True,
        "layout_config": {"source": "codex-preview-live-check"},
    },
}

r = requests.post(
    f"{api}/generator/prototypes/",
    headers=_AUTH_HEADERS,
    params={"database_prototype_name": ""},
    json=body,
    timeout=120,
)
print("create", r.status_code, r.text[:300])
r.raise_for_status()
proto = r.json()

r = requests.post(
    f"{api}/generator/prototypes/run/{proto['id']}",
    headers=_AUTH_HEADERS,
    timeout=60,
)
print("run", r.status_code, r.text[:200])
r.raise_for_status()

r = requests.post(
    f"{api}/generator/prototypes/seed/",
    headers=_AUTH_HEADERS,
    params={"system_id": system_id},
    timeout=120,
)
print("seed", r.status_code, r.text[:200])
print(json.dumps({"prototype": proto, "system_id": system_id, "name": name}, indent=2))
