"""
Interface UI Generation API — generate 3 style variants for an interface,
preview them, and refine via human-in-the-loop.

Endpoints:
  POST /interface-gen/generate/                          Start variant generation
  GET  /interface-gen/{session_id}/                      Get session state + variants
  GET  /interface-gen/{session_id}/preview/{variant_id}/ Preview HTML for a variant
  POST /interface-gen/{session_id}/refine/                Refine a selected variant
  POST /interface-gen/{session_id}/apply/                 Apply variant to the interface
"""
import json
import logging
import os
import re
import uuid
from enum import Enum
from types import SimpleNamespace
from typing import Optional

from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from ninja import Router, Schema

from jinja2 import Environment, FileSystemLoader

from llm.handler import call_openai
from llm.prompts.agents import AGENT_INTERFACE_VARIANTS, AGENT_INTERFACE_REFINE

logger = logging.getLogger(__name__)

interface_gen_router = Router()

# ── In-memory session store ──────────────────────────────────────────────────
# For production, replace with Redis or DB-backed storage.
_sessions: dict[str, dict] = {}


# ── Schemas ──────────────────────────────────────────────────────────────────

class GenerateSchema(Schema):
    interface_id: str
    prompt: str


class RefineSchema(Schema):
    variant_id: str
    prompt: str


class ApplySchema(Schema):
    variant_id: str


class ErrorSchema(Schema):
    error: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_json_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(raw)


def _build_page_structure(interface_data: dict) -> str:
    """Summarise the interface's page/section structure for the LLM."""
    pages = interface_data.get("pages", [])
    sections = interface_data.get("sections", [])
    lines = []
    for page in pages:
        name = page.get("name", "Unnamed")
        lines.append(f"Page: {name}")
        # find sections belonging to this page
        page_id = page.get("id", "")
        page_sections = [s for s in sections if str(s.get("page", "")) == str(page_id)]
        if not page_sections:
            # try matching by name
            page_sections = [s for s in sections if s.get("pageName", "") == name]
        for sec in page_sections:
            sec_name = sec.get("name", "Section")
            attrs = sec.get("attributes", [])
            attr_names = [a.get("name", "") for a in attrs if a.get("name")]
            if attr_names:
                lines.append(f"  Section: {sec_name} — Fields: {', '.join(attr_names)}")
            else:
                lines.append(f"  Section: {sec_name}")
    if not lines:
        lines.append("(No page structure defined yet)")
    return "\n".join(lines)


def _get_token(tokens: dict, key: str, fallback: str = "") -> str:
    return tokens.get(key, fallback)


# ── Prototype template rendering (style.css.jinja2) ─────────────────────────
# Mirror the enums from prototypes/generation/definitions/styling.py so that
# style.css.jinja2 can reference StyleType.* / LayoutType.* in conditionals.

class _StyleType(Enum):
    BASIC = 1; MODERN = 2; ABSTRACT = 3; ELEGANT = 4
    BRUTALIST = 5; GLASSMORPHISM = 6; DARK = 7

class _LayoutType(Enum):
    SIDEBAR_LEFT = 1; SIDEBAR_RIGHT = 2; TOP_NAV = 3; TOP_NAV_SIDEBAR = 4

_PROTO_TEMPLATES_DIR = "/usr/src/proto_templates"

# Tailwind named-color palette → hex (covers all standard colors).
_TW_COLORS = {
    "slate":   {50:"#f8fafc",100:"#f1f5f9",200:"#e2e8f0",300:"#cbd5e1",400:"#94a3b8",500:"#64748b",600:"#475569",700:"#334155",800:"#1e293b",900:"#0f172a",950:"#020617"},
    "gray":    {50:"#f9fafb",100:"#f3f4f6",200:"#e5e7eb",300:"#d1d5db",400:"#9ca3af",500:"#6b7280",600:"#4b5563",700:"#374151",800:"#1f2937",900:"#111827",950:"#030712"},
    "zinc":    {50:"#fafafa",100:"#f4f4f5",200:"#e4e4e7",300:"#d4d4d8",400:"#a1a1aa",500:"#71717a",600:"#52525b",700:"#3f3f46",800:"#27272a",900:"#18181b",950:"#09090b"},
    "neutral": {50:"#fafafa",100:"#f5f5f5",200:"#e5e5e5",300:"#d4d4d4",400:"#a3a3a3",500:"#737373",600:"#525252",700:"#404040",800:"#262626",900:"#171717",950:"#0a0a0a"},
    "stone":   {50:"#fafaf9",100:"#f5f5f4",200:"#e7e5e4",300:"#d6d3d1",400:"#a8a29e",500:"#78716c",600:"#57534e",700:"#44403c",800:"#292524",900:"#1c1917",950:"#0c0a09"},
    "red":     {50:"#fef2f2",100:"#fee2e2",200:"#fecaca",300:"#fca5a5",400:"#f87171",500:"#ef4444",600:"#dc2626",700:"#b91c1c",800:"#991b1b",900:"#7f1d1d",950:"#450a0a"},
    "orange":  {50:"#fff7ed",100:"#ffedd5",200:"#fed7aa",300:"#fdba74",400:"#fb923c",500:"#f97316",600:"#ea580c",700:"#c2410c",800:"#9a3412",900:"#7c2d12",950:"#431407"},
    "amber":   {50:"#fffbeb",100:"#fef3c7",200:"#fde68a",300:"#fcd34d",400:"#fbbf24",500:"#f59e0b",600:"#d97706",700:"#b45309",800:"#92400e",900:"#78350f",950:"#451a03"},
    "yellow":  {50:"#fefce8",100:"#fef9c3",200:"#fef08a",300:"#fde047",400:"#facc15",500:"#eab308",600:"#ca8a04",700:"#a16207",800:"#854d0e",900:"#713f12",950:"#422006"},
    "lime":    {50:"#f7fee7",100:"#ecfccb",200:"#d9f99d",300:"#bef264",400:"#a3e635",500:"#84cc16",600:"#65a30d",700:"#4d7c0f",800:"#3f6212",900:"#365314",950:"#1a2e05"},
    "green":   {50:"#f0fdf4",100:"#dcfce7",200:"#bbf7d0",300:"#86efac",400:"#4ade80",500:"#22c55e",600:"#16a34a",700:"#15803d",800:"#166534",900:"#14532d",950:"#052e16"},
    "emerald": {50:"#ecfdf5",100:"#d1fae5",200:"#a7f3d0",300:"#6ee7b7",400:"#34d399",500:"#10b981",600:"#059669",700:"#047857",800:"#065f46",900:"#064e3b",950:"#022c22"},
    "teal":    {50:"#f0fdfa",100:"#ccfbf1",200:"#99f6e4",300:"#5eead4",400:"#2dd4bf",500:"#14b8a6",600:"#0d9488",700:"#0f766e",800:"#115e59",900:"#134e4a",950:"#042f2e"},
    "cyan":    {50:"#ecfeff",100:"#cffafe",200:"#a5f3fc",300:"#67e8f9",400:"#22d3ee",500:"#06b6d4",600:"#0891b2",700:"#0e7490",800:"#155e75",900:"#164e63",950:"#083344"},
    "sky":     {50:"#f0f9ff",100:"#e0f2fe",200:"#bae6fd",300:"#7dd3fc",400:"#38bdf8",500:"#0ea5e9",600:"#0284c7",700:"#0369a1",800:"#075985",900:"#0c4a6e",950:"#082f49"},
    "blue":    {50:"#eff6ff",100:"#dbeafe",200:"#bfdbfe",300:"#93c5fd",400:"#60a5fa",500:"#3b82f6",600:"#2563eb",700:"#1d4ed8",800:"#1e40af",900:"#1e3a8a",950:"#172554"},
    "indigo":  {50:"#eef2ff",100:"#e0e7ff",200:"#c7d2fe",300:"#a5b4fc",400:"#818cf8",500:"#6366f1",600:"#4f46e5",700:"#4338ca",800:"#3730a3",900:"#312e81",950:"#1e1b4b"},
    "violet":  {50:"#f5f3ff",100:"#ede9fe",200:"#ddd6fe",300:"#c4b5fd",400:"#a78bfa",500:"#8b5cf6",600:"#7c3aed",700:"#6d28d9",800:"#5b21b6",900:"#4c1d95",950:"#2e1065"},
    "purple":  {50:"#faf5ff",100:"#f3e8ff",200:"#e9d5ff",300:"#d8b4fe",400:"#c084fc",500:"#a855f7",600:"#9333ea",700:"#7e22ce",800:"#6b21a8",900:"#581c87",950:"#3b0764"},
    "fuchsia": {50:"#fdf4ff",100:"#fae8ff",200:"#f5d0fe",300:"#f0abfc",400:"#e879f9",500:"#d946ef",600:"#c026d3",700:"#a21caf",800:"#86198f",900:"#701a75",950:"#4a044e"},
    "pink":    {50:"#fdf2f8",100:"#fce7f3",200:"#fbcfe8",300:"#f9a8d4",400:"#f472b6",500:"#ec4899",600:"#db2777",700:"#be185d",800:"#9d174d",900:"#831843",950:"#500724"},
    "rose":    {50:"#fff1f2",100:"#ffe4e6",200:"#fecdd3",300:"#fda4af",400:"#fb7185",500:"#f43f5e",600:"#e11d48",700:"#be123c",800:"#9f1239",900:"#881337",950:"#4c0519"},
}
_TW_SPECIAL = {"white": "#ffffff", "black": "#000000", "transparent": "transparent"}
_TW_RADIUS = {
    "rounded-none": 0, "rounded-sm": 2, "rounded": 4, "rounded-md": 6,
    "rounded-lg": 8, "rounded-xl": 12, "rounded-2xl": 16,
    "rounded-3xl": 24, "rounded-full": 999,
}


def _tw_to_hex(classes: str, prefixes: tuple) -> str | None:
    """Extract first hex color from a Tailwind class string matching *prefixes*."""
    if not classes:
        return None
    for cls in classes.split():
        if not any(cls.startswith(p) for p in prefixes):
            continue
        # Arbitrary value: bg-[#1a1a2e]
        arb = re.search(r'\[(#[0-9a-fA-F]{3,8})\]', cls)
        if arb:
            return arb.group(1)
        # Special: bg-white, bg-black
        for sp, hx in _TW_SPECIAL.items():
            if cls.endswith(f"-{sp}"):
                return hx
        # Named: bg-gray-900
        m = re.search(r'-([a-z]+)-(\d+)$', cls)
        if m:
            return _TW_COLORS.get(m.group(1), {}).get(int(m.group(2)))
    return None


def _extract_styling_from_tokens(tokens: dict) -> SimpleNamespace:
    """Build a Styling-compatible object by deriving colours from theme tokens."""
    body = tokens.get("page.body", "")
    btn = tokens.get("component.button.primary", "")

    bg = _tw_to_hex(body, ("bg-", "from-")) or "#FFFFFF"
    text = _tw_to_hex(body, ("text-",)) or "#000000"
    accent = _tw_to_hex(btn, ("bg-", "border-")) or "#2563eb"

    radius = 4
    for cls in btn.split():
        if cls in _TW_RADIUS:
            radius = _TW_RADIUS[cls]
            break

    return SimpleNamespace(
        style_type=_StyleType.BASIC,
        layout_type=_LayoutType.SIDEBAR_LEFT,
        radius=radius,
        text_color=text,
        accent_color=accent,
        background_color=bg,
    )


def _render_style_css(theme: dict) -> str:
    """Render style.css.jinja2 from the prototype templates with variant tokens."""
    tokens = theme.get("tokens", {})
    styling = _extract_styling_from_tokens(tokens)
    try:
        env = Environment(loader=FileSystemLoader(_PROTO_TEMPLATES_DIR))
        tpl = env.get_template("style.css.jinja2")
        tpl.globals["StyleType"] = _StyleType
        tpl.globals["LayoutType"] = _LayoutType
        return tpl.render(
            styling=styling,
            theme=theme,
            theme_summary={},
            global_layout={},
        )
    except Exception as e:
        logger.warning("Failed to render style.css.jinja2: %s", e)
        return ""


def _detect_screen_type(page_name: str, sections: list[dict]) -> str:
    """Detect screen type from page name and sections (mirrors screen_type.py)."""
    name_lower = page_name.lower()
    if any(kw in name_lower for kw in ("dashboard", "overview", "summary", "home", "analytics")):
        return "dashboard"
    if any(kw in name_lower for kw in ("wizard", "setup", "onboarding", "workflow")):
        if len(sections) >= 2:
            return "wizard"
    if any(kw in name_lower for kw in ("modal", "dialog", "popup", "confirm")):
        return "modal"
    # form: single section with create-only ops, or name match
    if any(kw in name_lower for kw in ("form", "register", "signup", "apply", "submit")):
        return "form"
    return "list"


def _render_variant_preview(interface_data: dict, variant: dict, interface_name: str) -> str:
    """Render a standalone HTML preview using the same template structure
    as the generated prototypes, ensuring visual parity."""
    tokens = variant.get("tokens", {})

    pages = interface_data.get("pages", [])
    sections = interface_data.get("sections", [])

    # Resolve first page + its sections
    first_page = pages[0] if pages else {"name": interface_name, "id": ""}
    first_page_name = first_page.get("name", interface_name)
    page_id = first_page.get("id", "")

    page_sections = [s for s in sections if str(s.get("page", "")) == str(page_id)]
    if not page_sections:
        page_sections = [s for s in sections if s.get("pageName", "") == first_page_name]
    if not page_sections:
        page_sections = [
            {"name": "Data Overview", "attributes": [
                {"name": "Name", "type": "str"}, {"name": "Status", "type": "str"},
                {"name": "Created", "type": "date"}, {"name": "Amount", "type": "int"}
            ]},
        ]

    # Normalise attributes to dicts
    for sec in page_sections:
        attrs = sec.get("attributes", [])
        if not attrs:
            sec["attributes"] = [{"name": "Field 1", "type": "str"}, {"name": "Field 2", "type": "str"}]

    screen_type = _detect_screen_type(first_page_name, page_sections)

    # Determine layout type from interface styling
    styling = interface_data.get("styling", {})
    layout_raw = styling.get("selectedLayout", "SIDEBAR_LEFT") or "SIDEBAR_LEFT"
    layout_type = str(layout_raw).replace(" ", "_").upper()

    categories = interface_data.get("categories", [])

    # Render CSS using same style.css.jinja2 as prototypes
    theme = {"name": variant.get("name", ""), "tokens": tokens}
    inline_css = _render_style_css(theme)

    # Render preview using the shared template
    try:
        preview_dir = os.path.dirname(os.path.abspath(__file__))
        env = Environment(loader=FileSystemLoader(preview_dir))
        tpl = env.get_template("preview.html.jinja2")
        return tpl.render(
            variant_name=variant.get("name", "Preview"),
            interface_name=interface_name,
            theme=theme,
            inline_css=inline_css,
            layout_type=layout_type,
            screen_type=screen_type,
            pages=pages,
            categories=categories,
            first_page=first_page,
            page_sections=page_sections,
        )
    except Exception as e:
        logger.error("Failed to render preview template: %s", e, exc_info=True)
        return f"<html><body><h1>Preview render error</h1><pre>{e}</pre></body></html>"


# ── Session persistence helpers ──────────────────────────────────────────────

def _persist_session(session_id: str) -> None:
    """Save in-memory session to Interface.data.designerSession in the DB."""
    from metadata.models import Interface
    session = _sessions.get(session_id)
    if not session:
        return
    try:
        iface = Interface.objects.get(pk=session["interface_id"])
        data = iface.data if isinstance(iface.data, dict) else {}
        data["designerSession"] = {
            "session_id": session["session_id"],
            "original_prompt": session["original_prompt"],
            "variants": session["variants"],
            "selected_variant_id": session["selected_variant_id"],
            "refine_history": session["refine_history"],
            "applied": session.get("applied", False),
        }
        iface.data = data
        iface.save(update_fields=["data"])
    except Exception as e:
        logger.warning("Failed to persist designer session: %s", e)


def _restore_session(interface_id: str) -> Optional[str]:
    """Restore session from DB into memory if not already loaded. Returns session_id or None."""
    from metadata.models import Interface
    # Check if there's already a memory session for this interface
    for sid, sess in _sessions.items():
        if sess.get("interface_id") == interface_id:
            return sid
    # Try to restore from DB
    try:
        iface = Interface.objects.select_related("system", "actor").get(pk=interface_id)
        data = iface.data if isinstance(iface.data, dict) else {}
        saved = data.get("designerSession")
        if not saved or not saved.get("session_id"):
            return None
        session_id = saved["session_id"]
        interface_name = iface.name or "Interface"
        system_name = iface.system.name if iface.system else "System"
        actor_name = (
            iface.actor.data.get("name", "Actor")
            if iface.actor and isinstance(iface.actor.data, dict)
            else "Actor"
        )
        _sessions[session_id] = {
            "session_id": session_id,
            "interface_id": interface_id,
            "interface_name": interface_name,
            "system_name": system_name,
            "actor_name": actor_name,
            "interface_data": data,
            "original_prompt": saved.get("original_prompt", ""),
            "variants": saved.get("variants", []),
            "selected_variant_id": saved.get("selected_variant_id"),
            "refine_history": saved.get("refine_history", []),
            "applied": saved.get("applied", False),
        }
        return session_id
    except Exception as e:
        logger.warning("Failed to restore designer session: %s", e)
        return None


# ── Endpoints ────────────────────────────────────────────────────────────────


@interface_gen_router.post("/generate/", response={200: dict, 400: ErrorSchema})
def generate_variants(request, body: GenerateSchema):
    """Generate 3 UI style variants for an interface based on designer's prompt."""
    from metadata.models import Interface

    try:
        iface = Interface.objects.select_related("system", "actor").get(pk=body.interface_id)
    except Interface.DoesNotExist:
        return 400, {"error": f"Interface {body.interface_id} not found"}

    interface_data = iface.data if isinstance(iface.data, dict) else {}
    system_name = iface.system.name if iface.system else "System"
    actor_name = iface.actor.data.get("name", "Actor") if iface.actor and isinstance(iface.actor.data, dict) else "Actor"
    interface_name = iface.name or "Interface"

    page_structure = _build_page_structure(interface_data)

    prompt = AGENT_INTERFACE_VARIANTS.format(
        designer_prompt=body.prompt,
        system_name=system_name,
        interface_name=interface_name,
        actor_name=actor_name,
        page_structure=page_structure,
    )

    try:
        raw = call_openai("gpt-4o", prompt)
        result = _parse_json_response(raw)
        variants = result.get("variants", [])
    except Exception as exc:
        logger.error("Interface variant generation failed: %s", exc)
        return 400, {"error": f"LLM generation failed: {exc}"}

    if not variants or len(variants) < 3:
        return 400, {"error": "LLM did not produce 3 variants"}

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "session_id": session_id,
        "interface_id": body.interface_id,
        "interface_name": interface_name,
        "system_name": system_name,
        "actor_name": actor_name,
        "interface_data": interface_data,
        "original_prompt": body.prompt,
        "variants": variants,
        "selected_variant_id": None,
        "refine_history": [],
    }

    # Persist session to DB so it survives navigation / server restart
    _persist_session(session_id)

    return {
        "session_id": session_id,
        "variants": [
            {"id": v["id"], "name": v["name"], "description": v["description"]}
            for v in variants
        ],
    }


@interface_gen_router.get("/{session_id}/", response={200: dict, 404: ErrorSchema})
def get_session(request, session_id: str):
    """Get current state of a generation session."""
    session = _sessions.get(session_id)
    if not session:
        return 404, {"error": "Session not found"}

    return {
        "session_id": session_id,
        "interface_id": session["interface_id"],
        "original_prompt": session["original_prompt"],
        "selected_variant_id": session["selected_variant_id"],
        "refine_history": session["refine_history"],
        "variants": [
            {"id": v["id"], "name": v["name"], "description": v["description"]}
            for v in session["variants"]
        ],
    }


@interface_gen_router.get("/{session_id}/preview/{variant_id}/", auth=None)
@xframe_options_exempt
def preview_variant(request, session_id: str, variant_id: str):
    """Render preview HTML for a specific variant."""
    session = _sessions.get(session_id)
    if not session:
        return HttpResponse("<h1>Session not found</h1>", status=404, content_type="text/html")

    variant = next((v for v in session["variants"] if v["id"] == variant_id), None)
    if not variant:
        return HttpResponse("<h1>Variant not found</h1>", status=404, content_type="text/html")

    html = _render_variant_preview(
        session["interface_data"],
        variant,
        session["interface_name"],
    )
    return HttpResponse(html, content_type="text/html")


@interface_gen_router.post("/{session_id}/refine/", response={200: dict, 404: ErrorSchema, 400: ErrorSchema})
def refine_variant(request, session_id: str, body: RefineSchema):
    """Refine a selected variant with a follow-up prompt."""
    session = _sessions.get(session_id)
    if not session:
        return 404, {"error": "Session not found"}

    variant = next((v for v in session["variants"] if v["id"] == body.variant_id), None)
    if not variant:
        return 400, {"error": f"Variant {body.variant_id} not found"}

    prompt = AGENT_INTERFACE_REFINE.format(
        system_name=session["system_name"],
        interface_name=session["interface_name"],
        original_prompt=session["original_prompt"],
        variant_name=variant["name"],
        variant_description=variant.get("description", ""),
        current_tokens=json.dumps(variant["tokens"], indent=2),
        refine_prompt=body.prompt,
    )

    try:
        raw = call_openai("gpt-4o", prompt)
        result = _parse_json_response(raw)
    except Exception as exc:
        logger.error("Interface variant refinement failed: %s", exc)
        return 400, {"error": f"Refinement failed: {exc}"}

    # Update the variant in place
    variant["name"] = result.get("name", variant["name"])
    variant["description"] = result.get("description", variant.get("description", ""))
    variant["tokens"] = result.get("tokens", variant["tokens"])

    session["selected_variant_id"] = body.variant_id
    session["refine_history"].append(body.prompt)

    # Persist updated session to DB
    _persist_session(session_id)

    return {
        "session_id": session_id,
        "variant": {"id": variant["id"], "name": variant["name"], "description": variant["description"]},
        "refine_history": session["refine_history"],
    }


@interface_gen_router.post("/{session_id}/apply/", response={200: dict, 404: ErrorSchema, 400: ErrorSchema})
def apply_variant(request, session_id: str, body: ApplySchema):
    """Apply the selected variant's theme to the interface and persist."""
    from metadata.models import Interface

    session = _sessions.get(session_id)
    if not session:
        return 404, {"error": "Session not found"}

    variant = next((v for v in session["variants"] if v["id"] == body.variant_id), None)
    if not variant:
        return 400, {"error": f"Variant {body.variant_id} not found"}

    try:
        iface = Interface.objects.get(pk=session["interface_id"])
    except Interface.DoesNotExist:
        return 400, {"error": "Interface no longer exists"}

    data = iface.data if isinstance(iface.data, dict) else {}
    data["theme"] = {
        "name": variant["name"],
        "tokens": variant["tokens"],
    }
    # Sync extracted colors into styling so Styling tab reflects the applied theme
    _s = _extract_styling_from_tokens(variant["tokens"])
    existing_styling = data.get("styling", {})
    data["styling"] = {
        "selectedStyle": existing_styling.get("selectedStyle", "modern"),
        "selectedLayout": existing_styling.get("selectedLayout", "sidebar_left"),
        "backgroundColor": _s.background_color,
        "textColor": _s.text_color,
        "accentColor": _s.accent_color,
        "radius": min(10, _s.radius),
    }
    data["designerMeta"] = {
        "generatedFrom": "interface_gen",
        "originalPrompt": session["original_prompt"],
        "variantId": variant["id"],
        "variantName": variant["name"],
        "refineHistory": session["refine_history"],
    }
    # Mark session as applied (keep it so the design page can restore it)
    session["applied"] = True
    session["selected_variant_id"] = body.variant_id
    iface.data = data
    iface.save(update_fields=["data"])

    # Persist the session with applied flag so it survives restart
    _persist_session(session_id)

    return {
        "applied": True,
        "interface_id": session["interface_id"],
        "variant_name": variant["name"],
    }


@interface_gen_router.get("/restore/{interface_id}/", response={200: dict, 404: ErrorSchema})
def restore_session(request, interface_id: str):
    """Restore a previously saved design session for an interface."""
    session_id = _restore_session(interface_id)
    if not session_id:
        return 404, {"error": "No saved session for this interface"}

    session = _sessions[session_id]
    return {
        "session_id": session_id,
        "interface_id": session["interface_id"],
        "original_prompt": session["original_prompt"],
        "selected_variant_id": session["selected_variant_id"],
        "refine_history": session["refine_history"],
        "applied": session.get("applied", False),
        "variants": [
            {"id": v["id"], "name": v["name"], "description": v["description"]}
            for v in session["variants"]
        ],
    }
