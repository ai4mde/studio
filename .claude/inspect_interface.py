"""Inspect the Customer interface sections to understand current state."""
import sys, json
from pathlib import Path

def dotenv_values(path):
    result = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return result

ROOT = Path(__file__).parent.parent
cfg = {}
for env_file in ["config/api.env", "config/secrets.env"]:
    cfg.update(dotenv_values(str(ROOT / env_file)))

import psycopg2, psycopg2.extras
conn = psycopg2.connect(
    host="localhost", port=int(cfg.get("POSTGRES_PORT", "5432")),
    dbname=cfg.get("POSTGRES_DB", "ai4mdestudio"),
    user=cfg.get("POSTGRES_USER", "ai4mdestudio"),
    password=cfg.get("POSTGRES_PASSWORD", "") or "",
)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT id, name, data,
           jsonb_array_length(COALESCE(data->'sections', '[]'::jsonb)) AS sec_count
    FROM metadata_interface WHERE name = 'Customer'
    ORDER BY sec_count DESC LIMIT 1
""")
iface = cur.fetchone()
print(f"Interface: {iface['name']} id={iface['id']} sections={iface['sec_count']}")

data = iface['data'] or {}
sections = data.get('sections', [])
pages = data.get('pages', [])

print(f"\n=== SECTIONS ({len(sections)}) ===")
for s in sections:
    pos = s.get('position', 'main')
    lay = s.get('layout', 'table')
    methods = s.get('methods', [])
    print(f"  [{pos}] [{lay}] '{s.get('name','')}' id={s.get('id','')} methods={len(methods)}")

print(f"\n=== PAGES ({len(pages)}) ===")
for p in pages:
    p_secs = p.get('sections', [])
    print(f"  Page '{p.get('name','')}': {len(p_secs)} section refs")
    for ref in p_secs[:3]:
        sid = ref.get('value') if isinstance(ref, dict) else ref
        matched = next((s for s in sections if s.get('id') == sid), None)
        pos = matched.get('position', 'main') if matched else '?'
        name = matched.get('name', '?') if matched else '?'
        print(f"    -> {sid} [{pos}] '{name}'")
    if len(p_secs) > 3:
        print(f"    ... and {len(p_secs)-3} more")

conn.close()
