"""
Interface UI Generation API — generate 3 style variants for an interface,
preview them, and refine via human-in-the-loop.

Endpoints:
  POST /interface-gen/generate/                                  Start variant generation
  GET  /interface-gen/{session_id}/                              Get session state + variants
  GET  /interface-gen/{session_id}/preview/{variant_id}/         Preview HTML for a variant
  POST /interface-gen/{session_id}/refine/                       Refine a selected variant
  POST /interface-gen/{session_id}/apply/                        Apply variant to the interface
  GET  /interface-gen/restore/{interface_id}/                    Restore saved session
  POST /interface-gen/{interface_id}/composition/override/       Manual region/binding override
"""
import json
import logging
import os
import re
import sys
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

# Make the prototype generator's utils package importable
_PROTO_SCRIPTS_DIR = "/usr/src/proto_scripts"
if _PROTO_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _PROTO_SCRIPTS_DIR)

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


class CompositionOverrideSchema(Schema):
    page_id: str
    section_id: Optional[str] = None          # required for binding-level changes
    new_region_id: Optional[str] = None       # move section to this region
    new_component_variant: Optional[str] = None  # change component variant
    new_skeleton_id: Optional[str] = None     # swap entire page skeleton


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
    """Summarise the interface's page/section structure for the LLM, including IDs."""
    pages = interface_data.get("pages", [])
    sections = interface_data.get("sections", [])
    sections_by_id = {s.get("id", ""): s for s in sections if isinstance(s, dict) and s.get("id")}
    lines = []
    for page in pages:
        name = page.get("name", "Unnamed")
        page_id = page.get("id", "")
        lines.append(f"Page: {name} [id: {page_id}]")

        # Collect section IDs for this page: prefer explicit sections[] refs, then fallback matches
        page_section_ids: list[str] = []
        for ref in page.get("sections", []):
            if isinstance(ref, dict):
                sec_id = ref.get("value") or ref.get("id", "")
                if sec_id:
                    page_section_ids.append(sec_id)
        if not page_section_ids:
            matched = [s for s in sections if str(s.get("page", "")) == str(page_id)]
            if not matched:
                matched = [s for s in sections if s.get("pageName", "") == name]
            page_section_ids = [s.get("id", "") for s in matched if s.get("id")]

        for sec_id in page_section_ids:
            sec = sections_by_id.get(sec_id)
            if not sec:
                continue
            sec_name = sec.get("name", "Section")
            ops = sec.get("operations") or {}
            op_list = [k for k, v in ops.items() if v]
            attrs = sec.get("attributes", [])
            attr_names = [a.get("name", "") for a in attrs if a.get("name")]
            line = f"  Section: {sec_name} [id: {sec_id}]"
            if op_list:
                line += f" — Operations: {', '.join(op_list)}"
            if attr_names:
                line += f" — Fields: {', '.join(attr_names)}"
            lines.append(line)

    if not lines:
        lines.append("(No page structure defined yet)")
    return "\n".join(lines)


def _extract_variant_structure_payload(variant: dict, session: dict) -> dict:
    payload: dict = {
        "selectedVariantId": variant.get("id"),
    }

    candidate_variants = session.get("variants") or []
    if isinstance(candidate_variants, list):
        payload["candidateVariants"] = [v for v in candidate_variants if isinstance(v, dict)]

    composition = variant.get("composition")
    if isinstance(composition, dict) and composition:
        # Start with the selected variant's pagesById
        merged_composition: dict = dict(composition)

        # Build candidateVariantsByPageId so the pipeline can show the full
        # set of layout options per page in preview/composition-preview.
        candidates_by_page: dict = {}
        for v in payload["candidateVariants"]:
            v_id = v.get("id", "")
            v_comp = v.get("composition") or {}
            if not isinstance(v_comp, dict):
                continue
            for page_id, page_comp in (v_comp.get("pagesById") or {}).items():
                if not isinstance(page_comp, dict):
                    continue
                if page_id not in candidates_by_page:
                    candidates_by_page[page_id] = []
                candidates_by_page[page_id].append({"id": v_id, "composition": page_comp})
        if candidates_by_page:
            merged_composition["candidateVariantsByPageId"] = candidates_by_page

        payload["composition"] = merged_composition

    return payload


def _apply_structure_payload(interface_data: dict, structure_payload: dict) -> dict:
    merged = dict(interface_data) if isinstance(interface_data, dict) else {}

    selected_variant_id = structure_payload.get("selectedVariantId")
    if selected_variant_id:
        merged["selectedVariantId"] = selected_variant_id
        # Also stamp each page dict so the pipeline can resolve composition per-page
        pages = merged.get("pages")
        if isinstance(pages, list):
            merged["pages"] = [
                {**p, "selectedVariantId": selected_variant_id}
                if isinstance(p, dict) else p
                for p in pages
            ]

    candidate_variants = structure_payload.get("candidateVariants")
    if isinstance(candidate_variants, list):
        merged["candidateVariants"] = candidate_variants

    composition = structure_payload.get("composition")
    if isinstance(composition, dict) and composition:
        merged["composition"] = composition

    return merged


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


class _MockObj:
    """Mock model instance for the second-pass Django template rendering."""
    def __init__(self, id, label, **attrs):
        self.id = id
        self._label = label
        for k, v in attrs.items():
            setattr(self, k, v)
    def __str__(self):
        return self._label

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


def _build_metadata_json(interface_id: str, interface_data: dict) -> str:
    """Build the full metadata JSON string from the DB, matching the format
    expected by the prototype generator's loading_json_utils."""
    from metadata.models import Interface
    from diagram.models import Diagram

    iface = Interface.objects.select_related("system").get(pk=interface_id)
    system = iface.system

    # Build diagrams with nodes and edges (same structure as FullDiagram schema)
    diagrams = []
    for diagram in Diagram.objects.filter(system=system).prefetch_related(
        "nodes__cls", "edges__rel"
    ):
        nodes = []
        for node in diagram.nodes.select_related("cls").all():
            nodes.append({
                "id": str(node.id),
                "cls": node.cls.data,
                "cls_ptr": str(node.cls.id),
            })

        edges = []
        for edge in diagram.edges.select_related("rel").all():
            edge_dict = {
                "id": str(edge.id),
                "rel": edge.rel.data,
                "rel_ptr": str(edge.rel.id),
            }
            src = edge.source
            tgt = edge.target
            if src:
                edge_dict["source_ptr"] = str(src.id)
            if tgt:
                edge_dict["target_ptr"] = str(tgt.id)
            edges.append(edge_dict)

        diagrams.append({
            "id": str(diagram.id),
            "name": diagram.name,
            "type": diagram.type,
            "nodes": nodes,
            "edges": edges,
        })

    # Build the interface entry (flat format: {name, data})
    metadata = {
        "diagrams": diagrams,
        "interfaces": [
            {"name": iface.name, "data": interface_data},
        ],
        "useAuthentication": False,
    }
    return json.dumps(metadata)


def _build_sample_context(section_components) -> dict:
    """Build sample Django template context with mock model instances."""
    from datetime import date, datetime
    from utils.definitions.model import AttributeType

    ctx: dict = {"update_instance": None, "active_process_node_id": None}
    for sc in section_components:
        model_key = str(sc.primary_model) if sc.primary_model else "item"
        mock_list = []
        for i in range(3):
            kw = {}
            for attr in sc.attributes:
                attr_name = str(attr.name)
                if attr.type == AttributeType.INTEGER:
                    kw[attr_name] = 10 + i * 5
                elif attr.type == AttributeType.FLOAT:
                    kw[attr_name] = round(10.5 + i * 3.14, 2)
                elif attr.type == AttributeType.BOOLEAN:
                    kw[attr_name] = i % 2 == 0
                elif attr.type == AttributeType.DATE:
                    kw[attr_name] = date(2024, 1, 10 + i)
                elif attr.type == AttributeType.DATETIME:
                    kw[attr_name] = datetime(2024, 1, 10 + i, 9, 0)
                elif attr.type == AttributeType.EMAIL:
                    kw[attr_name] = f"user{i + 1}@example.com"
                elif attr.type == AttributeType.ENUM:
                    lits = attr.enum_literals or ["Option A", "Option B", "Option C"]
                    kw[attr_name] = lits[i % len(lits)]
                else:
                    kw[attr_name] = f"Sample {i + 1}"
            mock_list.append(_MockObj(i + 1, f"{sc.display_name} #{i + 1}", **kw))
        ctx[f"{model_key}_list"] = mock_list
        for pm in (sc.parent_models or []):
            pm_key = str(pm).lower().replace(" ", "_")
            ctx[f"parent_{pm_key}_list"] = [
                _MockObj(j + 1, f"{pm} #{j + 1}") for j in range(3)
            ]
    return ctx


def _sanitize_django_template(tpl_str: str) -> str:
    """Strip Django tags that need URL resolver, CSRF, or staticfiles."""
    tpl_str = re.sub(r'{%\s*load\s+\w+\s*%}', '', tpl_str)
    tpl_str = re.sub(r"""{%\s*url\s+['\"][^'"]*['"](?:\s+[^%]*)?\s*%}""", '#', tpl_str)
    tpl_str = re.sub(r'{%\s*csrf_token\s*%}', '', tpl_str)
    tpl_str = re.sub(r"""{%\s*static\s+['\"][^'"]*['"]\s*%}""", '', tpl_str)
    return tpl_str


def _combine_django_templates(base_html: str, page_html: str) -> str:
    """Inline page block contents into base template, avoiding Django inheritance."""
    for block_name in ("breadcrumbs", "content"):
        # Extract block content from page template
        m = re.search(
            r'{%\s*block\s+' + block_name + r'\s*%}(.*?){%\s*endblock\s*%}',
            page_html, re.DOTALL,
        )
        block_content = m.group(1) if m else ''
        # Replace the empty block placeholder in the base (use lambda to avoid
        # backslash interpretation in replacement string)
        base_html = re.sub(
            r'{%\s*block\s+' + block_name + r'\s*%}\s*{%\s*endblock\s*%}',
            lambda _m, c=block_content: c, base_html,
        )
    return base_html


def _composition_summary(variant: dict) -> dict:
    """Return a compact structural summary of a variant's composition for the frontend."""
    comp = variant.get("composition") or {}
    pages_by_id = comp.get("pagesById") or {}
    pages = []
    for page_id, page_comp in pages_by_id.items():
        if not isinstance(page_comp, dict):
            continue
        pages.append({
            "page_id": page_id,
            "skeleton_id": page_comp.get("skeleton_id", ""),
            "page_archetype": page_comp.get("page_archetype", ""),
            "region_count": len(page_comp.get("region_order") or []),
            "binding_count": len(page_comp.get("bindings") or []),
        })
    return {"pages": pages}


def _render_variant_preview(interface_data: dict, variant: dict,
                            interface_name: str, interface_id: str,
                            page_index: int = 0) -> str:
    """Render a standalone HTML preview using the prototype generator's own
    data path (loading_json_utils → ApplicationComponent) and templates
    (base.html.jinja2 + page.html.jinja2) via two-pass rendering:
      Pass 1 (Jinja2): real generator objects → Django template string
      Pass 2 (Django): sample data            → final HTML
    """
    from django.template import Template as DjangoTemplate, Context
    from utils.loading_json_utils import get_application_component
    from utils.sanitization import app_name_sanitization
    from utils.screen_type import detect_screen_type
    from utils.definitions.styling import Styling, StyleType, LayoutType
    from utils.definitions.model import Attribute, AttributeType, CustomMethod, Cardinality
    from utils.definitions.section_component import SectionComponent, SectionCustomMethod
    from utils.definitions.page import Page
    from utils.definitions.category import Category
    from utils.definitions.application_component import ApplicationComponent
    from utils.definitions.settings import Settings

    tokens = variant.get("tokens", {})

    # Inject variant theme into interface data before building metadata
    preview_data = _apply_structure_payload(
        interface_data,
        _extract_variant_structure_payload(variant, {"variants": [variant]}),
    )
    preview_data["theme"] = {"name": variant.get("name", ""), "tokens": tokens}

    # Build metadata JSON from DB (diagrams + interface) and get real objects
    try:
        metadata_json = _build_metadata_json(interface_id, preview_data)
        app_name = app_name_sanitization(interface_name)
        app_component = get_application_component(
            project_name="preview",
            application_name=app_name,
            metadata=metadata_json,
            authentication_present=False,
        )
    except Exception as e:
        logger.error("Failed to build ApplicationComponent: %s", e, exc_info=True)
        return f"<html><body><h1>Preview error (data path)</h1><pre>{e}</pre></body></html>"

    if not app_component.pages:
        return "<html><body><h1>No pages defined</h1></body></html>"

    # Detect screen types for each page
    for page in app_component.pages:
        if not hasattr(page, 'screen_type'):
            page.screen_type = detect_screen_type(page)

    safe_index = max(0, min(page_index, len(app_component.pages) - 1))
    first_page = app_component.pages[safe_index]
    theme = app_component.theme or {}
    inline_css = _render_style_css(theme)

    # ── FIRST PASS: Jinja2 renders generator templates → Django template strings ──
    try:
        env = Environment(loader=FileSystemLoader(_PROTO_TEMPLATES_DIR))

        base_tpl = env.get_template("base.html.jinja2")
        for cls in (Styling, StyleType, LayoutType, Attribute, AttributeType,
                    SectionComponent, Page, Category, ApplicationComponent,
                    CustomMethod, SectionCustomMethod, Cardinality, Settings):
            base_tpl.globals[cls.__name__] = cls
        base_django = base_tpl.render(
            application_name=app_name,
            styling=app_component.styling,
            theme=theme,
            pages=app_component.pages,
            categories=app_component.categories,
            settings=app_component.settings,
            authentication_present=False,
            logo="",
            global_layout=app_component.global_layout,
        )

        page_tpl = env.get_template("page.html.jinja2")
        for cls in (Styling, StyleType, LayoutType, Attribute, AttributeType,
                    SectionComponent, Page, Category, ApplicationComponent,
                    CustomMethod, SectionCustomMethod, Cardinality, Settings):
            page_tpl.globals[cls.__name__] = cls
        page_django = page_tpl.render(
            project_name="preview",
            application_name=app_name,
            page=first_page,
            theme=theme,
        )
    except Exception as e:
        logger.error("Jinja2 first-pass failed: %s", e, exc_info=True)
        return f"<html><body><h1>Preview error (Jinja2 pass)</h1><pre>{e}</pre></body></html>"

    # ── COMBINE & SANITIZE ──
    combined = _combine_django_templates(base_django, page_django)
    combined = _sanitize_django_template(combined)

    # Inject inline CSS (replace the now-empty static link)
    combined = combined.replace("</head>", f"<style>{inline_css}</style>\n</head>")

    # ── SECOND PASS: Django template engine renders with sample data ──
    sample_ctx = _build_sample_context(first_page.section_components)
    try:
        django_tpl = DjangoTemplate(combined)
        return django_tpl.render(Context(sample_ctx))
    except Exception as e:
        logger.error("Django second-pass failed: %s", e, exc_info=True)
        return f"<html><body><h1>Preview error (Django pass)</h1><pre>{e}</pre></body></html>"


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

    # Convert composition_pages list into {pagesById} dict that the pipeline reads
    for variant in variants:
        comp_pages = variant.pop("composition_pages", None)
        if isinstance(comp_pages, list) and comp_pages:
            pages_by_id = {}
            for cp in comp_pages:
                if not isinstance(cp, dict):
                    continue
                page_id = cp.get("page_id", "")
                if not page_id:
                    continue
                pages_by_id[page_id] = {
                    "page_archetype": cp.get("page_archetype", ""),
                    "skeleton_id": cp.get("skeleton_id", ""),
                    "region_order": cp.get("region_order") or [],
                    "bindings": cp.get("bindings") or [],
                }
            if pages_by_id:
                variant["composition"] = {"pagesById": pages_by_id}

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
    """Get current state of a generation session, including composition summaries."""
    session = _sessions.get(session_id)
    if not session:
        return 404, {"error": "Session not found"}

    # Collect page names for multi-page preview navigation
    iface_data = session.get("interface_data") or {}
    page_names = [
        {"id": p.get("id", ""), "name": p.get("name", "")}
        for p in (iface_data.get("pages") or [])
        if isinstance(p, dict) and p.get("id")
    ]

    return {
        "session_id": session_id,
        "interface_id": session["interface_id"],
        "original_prompt": session["original_prompt"],
        "selected_variant_id": session["selected_variant_id"],
        "refine_history": [h["prompt"] if isinstance(h, dict) else h for h in session["refine_history"]],
        "applied": session.get("applied", False),
        "pages": page_names,
        "variants": [
            {
                "id": v["id"],
                "name": v["name"],
                "description": v["description"],
                "composition_summary": _composition_summary(v),
            }
            for v in session["variants"]
        ],
    }


@interface_gen_router.get("/{session_id}/variant/{variant_id}/", response={200: dict, 404: ErrorSchema})
def get_variant_tokens(request, session_id: str, variant_id: str):
    """Return full variant data including tokens and composition for the Styling editor."""
    session = _sessions.get(session_id)
    if not session:
        return 404, {"error": "Session not found"}
    variant = next((v for v in session["variants"] if v["id"] == variant_id), None)
    if not variant:
        return 404, {"error": "Variant not found"}
    return {
        "id": variant["id"],
        "name": variant["name"],
        "description": variant.get("description", ""),
        "tokens": variant.get("tokens", {}),
        "composition": variant.get("composition"),
        "composition_summary": _composition_summary(variant),
    }


@interface_gen_router.get("/{session_id}/preview/{variant_id}/", auth=None)
@xframe_options_exempt
def preview_variant(request, session_id: str, variant_id: str, page_index: int = 0):
    """Render preview HTML for a specific variant and optional page index."""
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
        session["interface_id"],
        page_index=page_index,
    )
    return HttpResponse(html, content_type="text/html")


@interface_gen_router.post("/{session_id}/refine/", response={200: dict, 404: ErrorSchema, 400: ErrorSchema})
def refine_variant(request, session_id: str, body: RefineSchema):
    """Refine a selected variant — supports both style and structural composition changes."""
    session = _sessions.get(session_id)
    if not session:
        return 404, {"error": "Session not found"}

    variant = next((v for v in session["variants"] if v["id"] == body.variant_id), None)
    if not variant:
        return 400, {"error": f"Variant {body.variant_id} not found"}

    # Snapshot state before refinement for undo history
    before_snapshot = {
        "tokens": dict(variant.get("tokens") or {}),
        "composition": json.loads(json.dumps(variant.get("composition"))) if variant.get("composition") else None,
        "name": variant.get("name", ""),
        "description": variant.get("description", ""),
    }

    # Build composition context for the LLM
    current_comp = variant.get("composition") or {}
    pages_by_id = current_comp.get("pagesById") or {}
    comp_lines = []
    for pid, pc in pages_by_id.items():
        if not isinstance(pc, dict):
            continue
        skel = pc.get("skeleton_id", "?")
        bindings = pc.get("bindings") or []
        comp_lines.append(f"  Page {pid}: skeleton={skel}")
        for b in bindings:
            comp_lines.append(f"    {b.get('region_id','?')} ← {b.get('section_id','?')} [{b.get('capability','?')}]")
    current_composition_str = "\n".join(comp_lines) if comp_lines else "(no composition)"

    current_skeleton_ids = ", ".join(
        pc.get("skeleton_id", "") for pc in pages_by_id.values() if isinstance(pc, dict)
    ) or "(none)"

    iface_data = session.get("interface_data") or {}
    page_structure = _build_page_structure(iface_data)

    prompt = AGENT_INTERFACE_REFINE.format(
        system_name=session["system_name"],
        interface_name=session["interface_name"],
        original_prompt=session["original_prompt"],
        variant_name=variant["name"],
        variant_description=variant.get("description", ""),
        current_skeleton_id=current_skeleton_ids,
        current_tokens=json.dumps(variant["tokens"], indent=2),
        current_composition=current_composition_str,
        page_structure=page_structure,
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

    # Apply structural composition changes if the LLM returned them
    structural_changed = False
    new_comp_pages = result.get("composition_pages")
    if isinstance(new_comp_pages, list) and new_comp_pages:
        pages_by_id_new = {}
        for cp in new_comp_pages:
            if not isinstance(cp, dict):
                continue
            pid = cp.get("page_id", "")
            if not pid:
                continue
            pages_by_id_new[pid] = {
                "page_archetype": cp.get("page_archetype", ""),
                "skeleton_id": cp.get("skeleton_id", ""),
                "region_order": cp.get("region_order") or [],
                "bindings": cp.get("bindings") or [],
            }
        if pages_by_id_new:
            variant["composition"] = {"pagesById": pages_by_id_new}
            structural_changed = True

    session["selected_variant_id"] = body.variant_id

    # Store snapshot in history (text prompt + before/after state)
    after_snapshot = {
        "tokens": dict(variant.get("tokens") or {}),
        "composition": json.loads(json.dumps(variant.get("composition"))) if variant.get("composition") else None,
        "name": variant.get("name", ""),
        "description": variant.get("description", ""),
    }
    session["refine_history"].append({
        "prompt": body.prompt,
        "variant_id": body.variant_id,
        "structural_changed": structural_changed,
        "before": before_snapshot,
        "after": after_snapshot,
    })

    # Persist updated session to DB
    _persist_session(session_id)

    return {
        "session_id": session_id,
        "variant": {
            "id": variant["id"],
            "name": variant["name"],
            "description": variant["description"],
            "composition_summary": _composition_summary(variant),
        },
        "structural_changed": structural_changed,
        "refine_history": [h["prompt"] if isinstance(h, dict) else h for h in session["refine_history"]],
    }


@interface_gen_router.post("/{session_id}/apply/", response={200: dict, 404: ErrorSchema, 400: ErrorSchema})
def apply_variant(request, session_id: str, body: ApplySchema):
    """Apply the selected variant's theme and structure metadata to the interface and persist."""
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
    structure_payload = _extract_variant_structure_payload(variant, session)
    data = _apply_structure_payload(data, structure_payload)
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
        "selectedVariantId": structure_payload.get("selectedVariantId"),
    }

    # Write composition directly onto each page.composition as well (robustness:
    # retrieve_page_composition() prefers page.composition over the top-level pagesById)
    comp_pages_by_id = (structure_payload.get("composition") or {}).get("pagesById") or {}
    if comp_pages_by_id:
        updated_pages = []
        for p in data.get("pages") or []:
            if isinstance(p, dict):
                pid = p.get("id", "")
                if pid in comp_pages_by_id:
                    p = {**p, "composition": comp_pages_by_id[pid]}
            updated_pages.append(p)
        data["pages"] = updated_pages

    # Mark session as applied (keep it so the design page can restore it)
    session["applied"] = True
    session["selected_variant_id"] = body.variant_id
    session_interface_data: dict = {}
    if isinstance(session.get("interface_data"), dict):
        session_interface_data = session["interface_data"]
    session_interface_data = _apply_structure_payload(session_interface_data, structure_payload)
    session_interface_data.update({
        "theme": data["theme"],
        "styling": data["styling"] if "styling" in data else data.get("styling"),
        "designerMeta": data["designerMeta"],
        "selectedVariantId": data.get("selectedVariantId"),
    })
    # Mirror page.composition into session data too
    if data.get("pages"):
        session_interface_data["pages"] = data["pages"]
    session["interface_data"] = session_interface_data
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
    iface_data_r = session.get("interface_data") or {}
    page_names_r = [
        {"id": p.get("id", ""), "name": p.get("name", "")}
        for p in (iface_data_r.get("pages") or [])
        if isinstance(p, dict) and p.get("id")
    ]
    return {
        "session_id": session_id,
        "interface_id": session["interface_id"],
        "original_prompt": session["original_prompt"],
        "selected_variant_id": session["selected_variant_id"],
        "refine_history": [h["prompt"] if isinstance(h, dict) else h for h in session["refine_history"]],
        "applied": session.get("applied", False),
        "pages": page_names_r,
        "variants": [
            {
                "id": v["id"],
                "name": v["name"],
                "description": v["description"],
                "composition_summary": _composition_summary(v),
            }
            for v in session["variants"]
        ],
    }


@interface_gen_router.post("/{interface_id}/composition/override/", response={200: dict, 400: ErrorSchema, 404: ErrorSchema})
def override_composition(request, interface_id: str, body: CompositionOverrideSchema):
    """Manually override region/section placement or component variant in the applied composition.

    - Move a section to a different region: provide section_id + new_region_id.
    - Change a binding's component variant: provide section_id + new_component_variant.
    - Swap the entire page skeleton: provide new_skeleton_id (resets region_order).
    Changes are persisted directly to Interface.data without going through the LLM.
    """
    from metadata.models import Interface
    from generator.composition import SKELETON_REGISTRY

    try:
        iface = Interface.objects.get(pk=interface_id)
    except Interface.DoesNotExist:
        return 404, {"error": f"Interface {interface_id} not found"}

    data = iface.data if isinstance(iface.data, dict) else {}

    pages = data.get("pages") or []
    page = next((p for p in pages if isinstance(p, dict) and p.get("id") == body.page_id), None)
    if not page:
        return 400, {"error": f"Page {body.page_id} not found in this interface"}

    # Resolve the active composition: page-level first, then top-level pagesById
    composition = page.get("composition") or {}
    top_comp = data.get("composition") or {}
    if not composition and isinstance(top_comp, dict):
        composition = (top_comp.get("pagesById") or {}).get(body.page_id) or {}
    if not composition:
        return 400, {"error": "No composition found for this page — apply a variant first"}

    composition = dict(composition)

    # ── Skeleton swap ─────────────────────────────────────────────────────────
    if body.new_skeleton_id:
        sk = SKELETON_REGISTRY.get(body.new_skeleton_id)
        if not sk:
            return 400, {"error": f"Skeleton {body.new_skeleton_id!r} is not in the registry"}
        composition["skeleton_id"] = body.new_skeleton_id
        composition["page_archetype"] = sk.archetype
        composition["region_order"] = list(sk.region_order)

    # ── Binding-level override ────────────────────────────────────────────────
    if body.section_id:
        if not body.new_region_id and not body.new_component_variant:
            return 400, {"error": "Provide new_region_id and/or new_component_variant when specifying section_id"}

        bindings = list(composition.get("bindings") or [])
        idx = next(
            (i for i, b in enumerate(bindings) if isinstance(b, dict) and b.get("section_id") == body.section_id),
            None,
        )
        if idx is None:
            return 400, {"error": f"Section {body.section_id} not found in composition bindings"}

        binding = dict(bindings[idx])
        if body.new_region_id:
            binding["region_id"] = body.new_region_id
        if body.new_component_variant:
            binding["component_variant"] = body.new_component_variant
        bindings[idx] = binding
        composition["bindings"] = bindings

    # ── Persist back ─────────────────────────────────────────────────────────
    updated_pages = [
        {**p, "composition": composition} if isinstance(p, dict) and p.get("id") == body.page_id else p
        for p in pages
    ]
    pages_by_id = dict((top_comp.get("pagesById") or {}))
    pages_by_id[body.page_id] = composition
    updated_top_comp = {**top_comp, "pagesById": pages_by_id}

    iface.data = {**data, "pages": updated_pages, "composition": updated_top_comp}
    iface.save(update_fields=["data"])

    return {
        "page_id": body.page_id,
        "composition": composition,
    }
