"""
Pick an interface from DB, auto-compose it, emit HTML, start prototype server.
No LLM required.

Run:
  docker exec studio-studio-api-1 bash -c "cd /usr/src/model && python /tmp/emit_from_db.py [interface_id]"
"""
import os, sys, uuid, json, shutil
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
import django; django.setup()

import requests as http_requests
from generator.composition import (
    SKELETON_REGISTRY, REGION_LAYOUT_ROLE,
    infer_section_capability, RegionSpec,
)
from generator.api.views.pipeline import (
    _preview_source_from_final_metadata,
    _render_emit_page_body,
    _preview_surface_class,
    _page_body_class,
    _page_main_class,
)

# ── Pick interface ────────────────────────────────────────────────────────────

from metadata.models import Interface

iface_id = sys.argv[1] if len(sys.argv) > 1 else None
if iface_id:
    iface = Interface.objects.get(pk=iface_id)
else:
    # Prefer interfaces that have pages + sections
    candidates = [
        i for i in Interface.objects.select_related("system", "actor").all()
        if isinstance(i.data, dict)
        and len(i.data.get("pages", [])) >= 1
        and len(i.data.get("sections", [])) >= 1
    ]
    if not candidates:
        print("No suitable interfaces found in DB")
        sys.exit(1)
    # Pick the one with most sections
    iface = max(candidates, key=lambda i: len(i.data.get("sections", [])))

data = iface.data if isinstance(iface.data, dict) else {}
print(f"Selected: '{iface.name}' ({iface.id})")
print(f"  pages={len(data.get('pages',[]))} sections={len(data.get('sections',[]))}")


# ── Auto-compose pages that have no composition ──────────────────────────────

def _auto_compose(page: dict, sections_by_id: dict) -> dict:
    """Build a composition for a page from its section refs using deterministic inference."""
    page_section_refs = page.get("sections") or []
    page_sections = []
    for ref in page_section_refs:
        sid = (ref.get("value") or ref.get("id", "")) if isinstance(ref, dict) else str(ref)
        if sid and sid in sections_by_id:
            page_sections.append(sections_by_id[sid])

    if not page_sections:
        return {}

    # Infer a capability profile for each section
    profiles = []
    for sec in page_sections:
        ops = sec.get("operations") or {}
        has_create = bool(ops.get("create")) if isinstance(ops, dict) else False
        has_update = bool(ops.get("update")) if isinstance(ops, dict) else False
        has_list   = bool(ops.get("list"))   if isinstance(ops, dict) else False
        roles      = [a.get("semantic_role", "") for a in sec.get("attributes", []) if a.get("semantic_role")]
        profile    = infer_section_capability(
            section_id=sec["id"],
            section_name=sec.get("name", ""),
            semantic_roles=roles,
            has_list_op=has_list,
            has_create_op=has_create,
            has_update_op=has_update,
        )
        profiles.append(profile)

    # Pick skeleton by dominant capability
    caps = [p.capability for p in profiles]
    if "gallery" in caps:
        skeleton_id = "product-detail/buybox-right"
    elif "form-fields" in caps and "data-table" in caps:
        skeleton_id = "account/tabbed"
    elif "form-fields" in caps:
        skeleton_id = "detail-form/card"
    elif "data-table" in caps:
        skeleton_id = "data-list/standard"
    elif "stat-cards" in caps:
        skeleton_id = "dashboard/full-width"
    elif "filters" in caps:
        skeleton_id = "data-list/filter-sidebar"
    else:
        skeleton_id = "detail-form/card"

    skeleton = SKELETON_REGISTRY[skeleton_id]

    # Place each section into the best-fitting region
    region_fill: dict[str, int] = {r: 0 for r in skeleton.region_order}
    bindings = []

    for profile in profiles:
        placed = False
        for region_id in skeleton.region_order:
            spec = skeleton.region_specs.get(region_id, RegionSpec(region_id))
            if region_fill[region_id] >= spec.max_sections:
                continue
            pref = spec.preferred_capabilities
            if not pref or profile.capability in pref:
                bindings.append({
                    "region_id":          region_id,
                    "section_id":         profile.section_id,
                    "capability":         profile.capability,
                    "component_variant":  profile.component_variant,
                })
                region_fill[region_id] += 1
                placed = True
                break

        if not placed:
            # Overflow into detail_main or first region with capacity
            fallback = next(
                (r for r in skeleton.region_order
                 if region_fill[r] < (skeleton.region_specs.get(r, RegionSpec(r)).max_sections)),
                skeleton.region_order[0],
            )
            bindings.append({
                "region_id":         fallback,
                "section_id":        profile.section_id,
                "capability":        profile.capability,
                "component_variant": profile.component_variant,
            })
            region_fill[fallback] = region_fill.get(fallback, 0) + 1

    return {
        "page_archetype": skeleton.archetype,
        "skeleton_id":    skeleton_id,
        "region_order":   list(skeleton.region_order),
        "bindings":       bindings,
    }


# Apply auto-composition to pages that have no composition yet
sections_by_id = {
    s.get("id", ""): s
    for s in (data.get("sections") or [])
    if isinstance(s, dict) and s.get("id")
}

pages = data.get("pages") or []
for page in pages:
    if not page.get("composition"):
        comp = _auto_compose(page, sections_by_id)
        if comp:
            page["composition"] = comp
            sk = comp["skeleton_id"]
            n_bindings = len(comp["bindings"])
            print(f"  Auto-composed '{page.get('name','')}': skeleton={sk} bindings={n_bindings}")
            for b in comp["bindings"]:
                print(f"    {b['region_id']:18s} ← {b['section_id'][:20]:20s} [{b['capability']}]")


# ── Build final_metadata and resolve inputs ───────────────────────────────────

actor_id   = str(iface.actor_id) if iface.actor_id else str(iface.id)
actor_name = iface.name or "Actor"

final_metadata = {
    "interfaces": [{
        "actor":  actor_id,
        "name":   actor_name,
        "data":   data,
    }]
}

state = {"final_metadata": final_metadata, "theme": data.get("theme")}
apps, preview_theme, preview_layout = _preview_source_from_final_metadata(state)

print()
print(f"Apps: {[a.get('actor_name','?') for a in apps]}")
total_pages = sum(len(a.get("pages", [])) for a in apps)
print(f"Total pages to emit: {total_pages}")


# ── Write HTML files ─────────────────────────────────────────────────────────

new_proto_id  = str(uuid.uuid4())
root          = "/usr/src/generated_prototypes"
new_base      = os.path.join(root, new_proto_id, "ui")
os.makedirs(new_base, exist_ok=True)

written = []

for app in apps:
    actor_dir     = (app.get("actor_name") or "Actor").replace(" ", "_")
    app_path      = os.path.join(new_base, actor_dir)
    templates_dir = os.path.join(app_path, "templates")
    os.makedirs(templates_dir, exist_ok=True)

    app_pages = app.get("pages", [])
    print()
    print(f"Emitting actor '{actor_dir}' ({len(app_pages)} pages)...")

    for i, page in enumerate(app_pages):
        page_name  = page.get("name", "page")
        body_html  = _render_emit_page_body(page, theme=preview_theme)
        surface_cl = _preview_surface_class(page, theme=preview_theme)
        body_cl    = _page_body_class(preview_theme)
        main_cl    = _page_main_class(preview_theme, page)

        # Inline top nav between pages
        nav_links = []
        for j, p in enumerate(app_pages):
            href  = f"/{actor_dir}/" + ("" if j == 0 else f"{p['name']}/")
            style = "color:#4f46e5;font-weight:600;" if p["name"] == page_name else "color:#6b7280;"
            nav_links.append(f'<a href="{href}" style="{style}text-decoration:none;padding:6px 12px;">{p["name"]}</a>')
        nav_html = "".join(nav_links)

        def _els(pos):
            return "\n".join(
                v["html"] for v in preview_layout.values()
                if isinstance(v, dict) and v.get("position") == pos and v.get("html")
            )

        left_html = _els("left"); right_html = _els("right")
        top_html  = _els("top");  bottom_html = _els("bottom")

        nav_bar = (
            f'<div style="background:#fff;border-bottom:1px solid #e5e7eb;padding:0 20px;">'
            f'<div style="max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:4px;height:48px;">'
            f'<span style="font-weight:700;color:#1f2937;margin-right:16px;">{iface.name}</span>'
            f'{nav_html}'
            f'</div></div>'
        )

        if left_html or right_html:
            page_shell = (
                f"{top_html}\n"
                f'<div style="display:flex;min-height:calc(100vh - 48px);">'
                f'{left_html}'
                f'<div class="{main_cl}" style="flex:1;padding:24px;">'
                f'<div class="{surface_cl}">{body_html}</div>'
                f'</div>'
                f'{right_html}</div>'
                f'{bottom_html}'
            )
        else:
            page_shell = (
                f"{top_html}\n"
                f'<div class="{main_cl}" style="padding:24px;">'
                f'<div class="{surface_cl}">{body_html}</div>'
                f'</div>'
                f'{bottom_html}'
            )

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{page_name} — {iface.name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>body{{margin:0;padding:0;font-family:system-ui,sans-serif;}}</style>
</head>
<body class="{body_cl}">
{nav_bar}
{page_shell}
</body>
</html>"""

        tpl_path = os.path.join(templates_dir, f"{page_name}.html")
        with open(tpl_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        written.append((actor_dir, page_name, len(full_html)))
        print(f"  [{i+1}/{len(app_pages)}] {page_name}.html — {len(full_html):,} bytes")

    # views.py + urls.py
    with open(os.path.join(app_path, "views.py"), "w") as f:
        f.write("from django.views.generic import TemplateView\n\n")
        for p in app_pages:
            n = p.get("name", "page")
            f.write(f"class {n}View(TemplateView):\n    template_name = '{n}.html'\n\n")

    with open(os.path.join(app_path, "urls.py"), "w") as f:
        lines = [f'    path("{"" if i==0 else p["name"]+"/"}",  views.{p["name"]}View.as_view(), name="render_{p["name"]}"),\n'
                 for i, p in enumerate(app_pages)]
        f.write(
            "from django.urls import path\nfrom . import views\n\n"
            f'app_name="{actor_dir}"\nurlpatterns=[\n{"".join(lines)}]\n'
        )


# ── Start prototype server ────────────────────────────────────────────────────

print()
print("Starting prototype server...")
try:
    resp = http_requests.post(
        "http://studio-studio-prototypes-1:8010/run",
        json={"id": new_proto_id, "name": "ui", "system": new_proto_id},
        timeout=15,
        allow_redirects=False,
    )
    started = resp.status_code in (200, 307)
    print(f"  Server response: {resp.status_code}")
except Exception as exc:
    started = False
    print(f"  Server not reachable: {exc}")

# ── Summary ───────────────────────────────────────────────────────────────────

print()
print("=" * 60)
print(f"Interface : {iface.name}")
print(f"Proto ID  : {new_proto_id}")
print(f"Files     : {len(written)}")
print()
if started:
    print("Open in browser:")
    for app in apps:
        actor_dir = (app.get("actor_name") or "Actor").replace(" ", "_")
        for j, p in enumerate(app.get("pages", [])):
            path = f"/{actor_dir}/" + ("" if j == 0 else f"{p['name']}/")
            print(f"  http://localhost:8010/{new_proto_id}{path}")
else:
    print("Prototype server not started. HTML files at:")
    print(f"  {new_base}/")
print("=" * 60)

# Also print proto_id alone so the caller can grab it
print(f"\nPROTO_ID={new_proto_id}")
