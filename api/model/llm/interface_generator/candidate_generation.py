"""Candidate generation and regeneration logic for interface variants."""

import copy
import json
import os
import re
from collections import defaultdict
from pathlib import Path

import requests
from metadata.models import Interface
from llm.template_renderer import render_layout

from llm.prompts.candidates import (
    GENERATE_CANDIDATES_SYSTEM_PROMPT,
    REGENERATE_CANDIDATES_SYSTEM_PROMPT,
    build_generate_candidates_prompt,
    build_regenerate_candidates_prompt,
)
from .section_utils import (
    _DATA_SECTION_LAYOUTS,
    _FOOTER_TEMPLATE_LAYOUTS,
    _HEADER_NAV_LAYOUTS,
    _HEADER_TEMPLATE_LAYOUTS,
    _VALID_SECTION_LAYOUTS,
    _VALID_SECTION_STYLE,
    _canonical_page_type,
    _finalize_data_section_bindings,
    _ensure_logical_related_sections,
    _normalize_select_existing_sections,
    _infer_page_type_value,
    _infer_section_component,
    _model_field_names,
    _normalize_activity_action_sections,
    _normalize_chrome_sections,
    _normalize_field_layout,
    _normalize_layout_alias,
    _normalize_section_operations,
    _page_type_value,
    _ref_id,
)
from .uml_mapping.usecase_workflow import _build_usecase_navigation
from .uml_mapping.uml_extractor import extract_uml_intelligence
from .uml_mapping.metadata_context import _actor_name_from_context, _fetch_system_context_data
from .candidate_defaults import (
    _assign_default_page_categories,
    _merge_page_categories,
)
from .uml_mapping.mapping_sections import (
    _apply_nav_methods,
    _dedupe_agent_header_shells,
    _ensure_usecase_pages,
)

BUTTON_PRIMARY_BG_HEX = "button.primary.bg_hex"
BUTTON_PRIMARY_TEXT_HEX = "button.primary.text_hex"


def _render_candidate_preview_local(interface_id: str, candidate_index: int) -> str:
    """Render candidate preview local."""
    interface = Interface.objects.get(id=interface_id)
    candidates = (interface.data or {}).get("candidates", [])
    if candidate_index < 0 or candidate_index >= len(candidates):
        return f"Render failed: candidate {candidate_index} not found."
    candidate = candidates[candidate_index]
    system = interface.system
    classifiers = [{"id": str(c.id), "data": c.data} for c in system.classifiers.all()]
    relations = [
        {
            "id": str(r.id),
            "source": str(r.source_id),
            "target": str(r.target_id),
            "data": r.data,
        }
        for r in system.relations.all()
    ]
    files = render_layout(
        interface_data={
            "pages": candidate.get("pages", []),
            "sections": candidate.get("sections", []),
            "styling": candidate.get("styling", {}),
            "tokens": candidate.get("tokens", {}),
        },
        classifiers=classifiers,
        layout_config=None,
        interface_name=interface.name,
        inject_click_handlers=False,
        relations=relations,
    )
    tab_buttons = "".join(
        f'<button class="tab-btn" onclick="showPage({i})" id="tab-{i}">Page {i + 1}</button>'
        for i in range(len(files))
    )
    page_divs = "".join(
        f'<div class="page-frame" id="page-{i}" style="display:{"block" if i == 0 else "none"}">'
        f'<iframe srcdoc="{files[i]["content"].replace(chr(34), "&quot;").replace(chr(10), "&#10;")}" '
        f'style="width:100%;height:calc(100vh - 50px);border:none;"></iframe></div>'
        for i in range(len(files))
    )
    preview_html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>body{margin:0;padding-top:50px;}"
        ".tab-btn{background:#334155;color:#e2e8f0;border:none;padding:6px 14px;"
        "border-radius:6px;cursor:pointer;font-size:13px;white-space:nowrap;}"
        ".tab-btn:hover,.tab-btn.active{background:#3b82f6;color:#fff;}</style></head>"
        "<body><nav style='position:fixed;top:0;left:0;right:0;height:50px;background:#1e293b;"
        f"display:flex;align-items:center;padding:0 12px;gap:8px;z-index:999;overflow-x:auto;'>{tab_buttons}</nav>"
        f"{page_divs}<script>function showPage(i){{"
        "document.querySelectorAll('.page-frame').forEach((el,j)=>el.style.display=j===i?'block':'none');"
        "document.querySelectorAll('.tab-btn').forEach((el,j)=>el.classList.toggle('active',j===i));}"
        "showPage(0);</script></body></html>"
    )
    data = dict(interface.data or {})
    updated_candidates = list(data.get("candidates", []))
    updated_candidates[candidate_index] = dict(updated_candidates[candidate_index])
    updated_candidates[candidate_index]["preview_html"] = preview_html
    updated_candidates[candidate_index]["preview_files"] = files
    data["candidates"] = updated_candidates
    Interface.objects.filter(id=interface_id).update(data=data)
    return f"OK: preview rendered for candidate {candidate_index}."


def _norm_candidate_styling(styling) -> dict:
    """Normalize candidate styling."""
    if styling:
        if isinstance(styling, str):
            try: styling = json.loads(styling)
            except Exception: styling = {}
        styling = dict(styling)
        for old, new in (("accent_color", "accentColor"), ("background_color", "backgroundColor"), ("text_color", "textColor"), ("selected_style", "selectedStyle")):
            if old in styling and new not in styling: styling[new] = styling.pop(old)
        if isinstance(styling.get("radius"), str):
            styling["radius"] = {"none": 0, "sm": 4, "md": 8, "lg": 12, "xl": 16, "2xl": 24}.get(styling["radius"], 8)
    else:
        styling = {}
    # LLM-generated styling is the source of truth.
    return styling


_STYLING_TOKEN_KEYS = frozenset({
    "region.header.bg_hex", "region.header.text_hex",
    "region.footer.bg_hex", "region.footer.text_hex",
    "region.main.bg_hex", "region.sidebar.bg_hex", "region.border_hex",
    "component.card.bg_hex", "component.card.border_hex",
    BUTTON_PRIMARY_BG_HEX, BUTTON_PRIMARY_TEXT_HEX,
    "button.secondary.bg_hex", "button.secondary.text_hex",
    "button.ghost.text_hex", "button.danger.bg_hex", "button.link.text_hex",
    "input.bg_hex", "input.border_hex", "input.border_focus_hex", "input.text_hex",
    "nav.bg_hex", "nav.text_hex",
    "table.header.bg_hex", "table.header.text_hex",
    "badge.info.bg_hex", "text.muted.hex",
})

def _norm_candidate_tokens(tokens, styling: dict | None = None) -> dict:
    """Normalize candidate tokens."""
    if not tokens:
        tokens = {}
    if isinstance(tokens, str):
        try: tokens = json.loads(tokens)
        except Exception: tokens = {}
    tokens = dict(tokens)
    # Pre-populate fine-grained overrides from styling.
    for key in _STYLING_TOKEN_KEYS:
        if key not in tokens and isinstance(styling, dict) and styling.get(key):
            tokens[key] = styling[key]
    # LLM-generated tokens/styling are the source of truth.
    return tokens


def _drop_deprecated_section_fields(section: dict) -> dict:
    """Remove deprecated section fields that should not be emitted by candidates."""
    section = dict(section or {})
    section.pop("item_actions", None)
    return section


def _intent_text(*values) -> str:
    """Normalize design intent text for requirement detection."""
    return " ".join(str(value or "").lower() for value in values if value is not None)


def _mentions(text: str, *patterns: str) -> bool:
    """Return true when any regex pattern is present in text."""
    return any(re.search(pattern, text, re.I) for pattern in patterns)


def _is_nav_section(section: dict) -> bool:
    """Return true when a section represents navigation."""
    layout = _normalize_layout_alias(section.get("layout"))
    return (
        str(section.get("role") or "").lower() in {"navigation", "nav"}
        or str(section.get("component") or "") == "NavBar"
        or layout in {"site-nav", "nav-links", "nav-bar"}
    )


def _page_ref_ids(page: dict) -> set[str]:
    """Collect referenced section ids from a page."""
    return {_ref_id(ref) for ref in (page.get("sections") or []) if _ref_id(ref)}


def _ensure_nav_section(pages: list, sections: list) -> dict:
    """Return an existing navigation section or create a minimal one."""
    for section in sections:
        if _is_nav_section(section):
            return section
    nav_methods = [p.get("name") or p.get("id") for p in pages if p.get("name") or p.get("id")]
    nav_section = {
        "id": "app_sidebar_nav",
        "name": "Navigation",
        "role": "navigation",
        "layout": "site-nav",
        "component": "NavBar",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": {"create": False, "update": False, "delete": False, "select": False},
        "methods": nav_methods,
        "col_span": 12,
        "position": "header",
        "style": {"color": "accent", "density": "normal", "shadow": "sm", "border": "light", "bg": "white"},
    }
    sections.append(nav_section)
    return nav_section


def _apply_design_intent_patch(
    pages: list,
    sections: list,
    tokens: dict,
    styling: dict,
    prompt: str = "",
    description: str = "",
    name: str = "",
) -> tuple[list, list, dict, dict]:
    """Apply deterministic DSL patches for explicit designer requirements."""
    text = _intent_text(prompt, description, name)
    patched_pages = copy.deepcopy(pages or [])
    patched_sections = copy.deepcopy(sections or [])
    patched_tokens = dict(tokens or {})
    patched_styling = dict(styling or {})

    wants_contained = _mentions(text, r"\bcontained\b", r"\bmax[- ]?width\b", r"\bcentered\b")
    wants_left_sidebar_nav = _mentions(text, r"\bleft\s+sidebar\s+nav", r"\bsidebar\s+navigation\b", r"\bleft\s+nav")
    wants_sidebar_nav = wants_left_sidebar_nav or _mentions(text, r"\bside\s*bar\s+nav", r"\bsidebar\s+nav")
    wants_top_nav = _mentions(text, r"\btop\s+(horizontal\s+)?nav", r"\bhorizontal\s+navigation\b")
    wants_navy_header = _mentions(text, r"\bnavy\s+header\b", r"\bdark\s+blue\s+header\b")
    wants_beige_cards = _mentions(text, r"\bbeige\s+cards?\b", r"\bcream\s+cards?\b")
    wants_gold_buttons = _mentions(text, r"\bgold(en)?\s+buttons?\b", r"\byellow\s+buttons?\b")
    wants_table = _mentions(text, r"\btable\b", r"\bdata\s*table\b", r"\btabular\b")
    wants_small_table_text = wants_table and _mentions(text, r"\bsmall(er)?\s+table\s+text\b", r"\bcompact\s+table\b")
    wants_big_hero = _mentions(text, r"\bbig(ger)?\s+hero\s+title\b", r"\blarge\s+hero\b", r"\bhero\s+title\b")

    if wants_contained:
        for page in patched_pages:
            layout = dict(page.get("layout") or {})
            layout["main_width"] = "contained"
            page["layout"] = layout

    if wants_sidebar_nav or wants_top_nav:
        nav = _ensure_nav_section(patched_pages, patched_sections)
        nav["layout"] = "site-nav"
        nav["component"] = "NavBar"
        nav["role"] = "navigation"
        style = dict(nav.get("style") or {})
        if wants_sidebar_nav and not wants_top_nav:
            nav["position"] = "sidebar"
            style["variant"] = "rail"
            style["sidebar_side"] = "left" if wants_left_sidebar_nav else style.get("sidebar_side", "left")
            style["sidebar_width"] = style.get("sidebar_width", 3)
            style["nav_height"] = "tall"
            for page in patched_pages:
                refs = list(page.get("sections") or [])
                if nav.get("id") and nav.get("id") not in _page_ref_ids(page):
                    page["sections"] = [{"value": nav["id"]}] + refs
        elif wants_top_nav:
            nav["position"] = "header"
            style.pop("sidebar_side", None)
            style.pop("sidebar_width", None)
            style["variant"] = "page-nav"
        nav["style"] = style

    if wants_navy_header:
        patched_tokens["page.bg.hex"] = "#f9fafb"
        patched_tokens["page.body.bg_hex"] = "#f9fafb"
        patched_tokens["page.text.hex"] = "#111827"
        patched_tokens["page.body.text_hex"] = "#111827"
        patched_tokens["region.main.bg_hex"] = "#ffffff"
        patched_tokens["region.main.bg_sunken_hex"] = "#f9fafb"
        patched_tokens["color.secondary.hex"] = "#9ca3af"
        patched_tokens["text.muted.hex"] = "#6b7280"
        patched_tokens["region.header.bg_hex"] = "#061756"
        patched_tokens["region.header.text_hex"] = "#ffffff"
        patched_tokens["nav.bg_hex"] = "#061756"
        patched_tokens["nav.text_hex"] = "#ffffff"
        if wants_sidebar_nav:
            patched_tokens["region.sidebar.bg_hex"] = "#061756"

    if wants_beige_cards:
        patched_tokens["component.card.bg_hex"] = "#f4ead7"
        patched_tokens["component.card.border_hex"] = "#d8c7a6"
        patched_tokens["component.card.text_hex"] = patched_tokens.get("component.card.text_hex") or "#111827"
        patched_tokens["component.card.muted_hex"] = patched_tokens.get("component.card.muted_hex") or "#6b7280"
        for section in patched_sections:
            if section.get("layout") in {"card", "gallery", "detail"}:
                style = dict(section.get("style") or {})
                style["bg"] = "beige"
                section["style"] = style

    if wants_gold_buttons:
        for prefix in ("button.primary", "button.secondary"):
            patched_tokens[f"{prefix}.bg_hex"] = "#d4a017"
            patched_tokens[f"{prefix}.text_hex"] = "#061756"
            patched_tokens[f"{prefix}.border_hex"] = "#b8870d"

    if wants_table:
        for section in patched_sections:
            if section.get("position", "main") != "main":
                continue
            if not section.get("primary_model"):
                continue
            if section.get("layout") in {"card", "gallery", "list", "table"} or section.get("role") in {"object_collection", "object_summary"}:
                section["layout"] = "table"
                section["component"] = "DataTable"
                style = dict(section.get("style") or {})
                if wants_small_table_text:
                    style["density"] = "compact"
                section["style"] = style
                section["field_layout"] = _normalize_field_layout(section)
        if wants_small_table_text:
            patched_tokens["typography.body.size"] = "13px"
            patched_tokens["typography.label.size"] = "12px"
            patched_tokens["typography.caption.size"] = "11px"

    if wants_big_hero:
        patched_tokens["typography.hero.size"] = "72px"
        patched_tokens["typography.display.size"] = "52px"
        for section in patched_sections:
            if str(section.get("role") or "").lower() == "header" or section.get("position") == "header":
                if section.get("layout") in _HEADER_TEMPLATE_LAYOUTS or str(section.get("component") or "") == "HeaderTemplate":
                    section["layout"] = "hero-header"
                    section["component"] = "HeaderTemplate"
                    style = dict(section.get("style") or {})
                    style["header_variant"] = "hero"
                    section["style"] = style
                    break

    patched_styling.update({key: val for key, val in patched_tokens.items() if key in _STYLING_TOKEN_KEYS})
    return patched_pages, patched_sections, patched_tokens, patched_styling


def _hex_rgb(value: str) -> tuple[int, int, int] | None:
    """Parse #rgb or #rrggbb colors."""
    value = str(value or "").strip()
    if not value.startswith("#"):
        return None
    raw = value[1:]
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", raw):
        return None
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def _is_dark_blue(value: str) -> bool:
    """Heuristic for navy/dark blue token validation."""
    rgb = _hex_rgb(value)
    if not rgb:
        return False
    r, g, b = rgb
    return b >= r and b >= g and max(rgb) <= 120


def _is_gold(value: str) -> bool:
    """Heuristic for gold/yellow button validation."""
    rgb = _hex_rgb(value)
    if not rgb:
        return False
    r, g, b = rgb
    return r >= 160 and g >= 110 and b <= 90


def _is_beige(value: str) -> bool:
    """Heuristic for beige/cream surface validation."""
    rgb = _hex_rgb(value)
    if not rgb:
        return False
    r, g, b = rgb
    return r >= 210 and g >= 190 and b >= 150 and abs(r - g) <= 45 and r >= b


def _px_number(value: str) -> float | None:
    """Extract a px number from a CSS size token."""
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)px", str(value or ""))
    return float(match.group(1)) if match else None


def _candidate_compliance_report(
    pages: list,
    sections: list,
    tokens: dict,
    prompt: str = "",
    description: str = "",
    name: str = "",
) -> dict:
    """Check whether candidate metadata satisfies explicit prompt/description claims."""
    text = _intent_text(prompt, description, name)
    requirements: list[dict] = []

    def add(key: str, required: bool, passed: bool, detail: str):
        if required:
            requirements.append({"key": key, "passed": bool(passed), "detail": detail})

    nav_sections = [s for s in sections or [] if _is_nav_section(s)]
    data_sections = [
        s for s in sections or []
        if s.get("position", "main") == "main" and s.get("primary_model") and s.get("layout") in _DATA_SECTION_LAYOUTS
    ]
    wants_sidebar = _mentions(text, r"\bsidebar\s+nav", r"\bsidebar\s+navigation\b", r"\bleft\s+nav")
    wants_left_sidebar = _mentions(text, r"\bleft\s+sidebar\s+nav", r"\bleft\s+nav")
    wants_table = _mentions(text, r"\btable\b", r"\bdata\s*table\b", r"\btabular\b")
    wants_small_table = wants_table and _mentions(text, r"\bsmall(er)?\s+table\s+text\b", r"\bcompact\s+table\b")
    wants_contained = _mentions(text, r"\bcontained\b", r"\bmax[- ]?width\b", r"\bcentered\b")
    wants_navy_header = _mentions(text, r"\bnavy\s+header\b", r"\bdark\s+blue\s+header\b")
    wants_beige_cards = _mentions(text, r"\bbeige\s+cards?\b", r"\bcream\s+cards?\b")
    wants_gold_buttons = _mentions(text, r"\bgold(en)?\s+buttons?\b", r"\byellow\s+buttons?\b")
    wants_big_hero = _mentions(text, r"\bbig(ger)?\s+hero\s+title\b", r"\blarge\s+hero\b", r"\bhero\s+title\b")

    add(
        "left_sidebar_navigation" if wants_left_sidebar else "sidebar_navigation",
        wants_sidebar,
        any(s.get("position") == "sidebar" and (not wants_left_sidebar or (s.get("style") or {}).get("sidebar_side") == "left") for s in nav_sections),
        "Navigation must be rendered as a sidebar, left-sided when requested.",
    )
    add(
        "table_layout",
        wants_table,
        any(s.get("layout") == "table" or s.get("component") == "DataTable" for s in data_sections),
        "At least one data section must render as DataTable/table.",
    )
    add(
        "small_table_text",
        wants_small_table,
        any((s.get("style") or {}).get("density") == "compact" for s in data_sections)
        or (_px_number(tokens.get("typography.body.size")) or 99) <= 14,
        "Compact table density or small typography token is required.",
    )
    add(
        "contained_main_layout",
        wants_contained,
        all((p.get("layout") or {}).get("main_width") == "contained" for p in pages or []),
        "Every page should use layout.main_width='contained'.",
    )
    add(
        "navy_header",
        wants_navy_header,
        _is_dark_blue(tokens.get("region.header.bg_hex")) or _is_dark_blue(tokens.get("nav.bg_hex")),
        "Header/nav background token must be a dark blue/navy hex color.",
    )
    add(
        "beige_cards",
        wants_beige_cards,
        _is_beige(tokens.get("component.card.bg_hex")),
        "Card background token must be beige/cream.",
    )
    add(
        "gold_buttons",
        wants_gold_buttons,
        _is_gold(tokens.get(BUTTON_PRIMARY_BG_HEX)) and _is_gold(tokens.get("button.secondary.bg_hex")),
        "Primary and secondary button background tokens must be gold.",
    )
    add(
        "large_hero_title",
        wants_big_hero,
        (_px_number(tokens.get("typography.hero.size")) or 0) >= 64
        or any(s.get("layout") == "hero-header" for s in sections or []),
        "Hero title must use a large hero typography token or hero-header layout.",
    )

    issues = [req["detail"] for req in requirements if not req["passed"]]
    return {
        "passed": not issues,
        "checked": len(requirements),
        "requirements": requirements,
        "issues": issues,
    }


_VISUAL_METRICS_SCRIPT = """
() => {
  const css = getComputedStyle(document.documentElement);
  const cssVar = (name) => (css.getPropertyValue(name) || '').trim();
  const rect = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {x: r.x, y: r.y, width: r.width, height: r.height};
  };
  const sections = Array.from(document.querySelectorAll('[data-section-id]')).map((el) => ({
    id: el.getAttribute('data-section-id') || '',
    name: el.getAttribute('data-section-name') || '',
    position: el.getAttribute('data-position') || '',
    layout: el.getAttribute('data-layout') || '',
    rect: rect(el),
  }));
  const buttons = Array.from(document.querySelectorAll('button, a.si-btn, .si-btn')).map((el) => {
    const s = getComputedStyle(el);
    return {
      text: (el.textContent || '').trim().slice(0, 40),
      backgroundColor: s.backgroundColor,
      color: s.color,
      rect: rect(el),
    };
  });
  const main = document.querySelector('main, .si-main');
  const header = document.querySelector('header, [data-position="header"]');
  const contentRects = sections
    .filter((section) => !['header', 'footer'].includes(section.position) && section.rect && section.rect.width > 0)
    .map((section) => section.rect);
  const contentBounds = contentRects.length ? {
    x: Math.min(...contentRects.map((r) => r.x)),
    y: Math.min(...contentRects.map((r) => r.y)),
    width: Math.max(...contentRects.map((r) => r.x + r.width)) - Math.min(...contentRects.map((r) => r.x)),
    height: Math.max(...contentRects.map((r) => r.y + r.height)) - Math.min(...contentRects.map((r) => r.y)),
  } : rect(main);
  return {
    title: document.title,
    viewport: {width: innerWidth, height: innerHeight},
    document: {
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      bodyTextLength: (document.body.innerText || '').trim().length,
    },
    cssVars: {
      regionHeaderBg: cssVar('--region-header-bg'),
      navBg: cssVar('--nav-bg'),
      cardBg: cssVar('--card-bg'),
      buttonPrimaryBg: cssVar('--button-primary-bg'),
      buttonSecondaryBg: cssVar('--button-secondary-bg'),
      heroSize: cssVar('--text-hero-size'),
      bodySize: cssVar('--text-body-size'),
      labelSize: cssVar('--text-label-size'),
    },
    main: rect(main),
    mainContent: contentBounds,
    header: rect(header),
    sections,
    buttons,
    tableCount: document.querySelectorAll('table, .si-table, [data-layout="table"]').length,
    sidebarCount: sections.filter((section) => section.position === 'sidebar').length,
    heroCount: sections.filter((section) => section.layout === 'hero-header' || section.position === 'hero').length,
  };
}
"""


def _css_rgb(value: str) -> tuple[int, int, int] | None:
    """Parse rgb()/rgba() CSS colors."""
    match = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", str(value or ""))
    if not match:
        return _hex_rgb(str(value or ""))
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _visual_color_is_dark_blue(value: str) -> bool:
    """Validate rendered CSS dark blue/navy colors."""
    rgb = _css_rgb(value)
    if not rgb:
        return False
    r, g, b = rgb
    return b >= r and b >= g and max(rgb) <= 120


def _visual_color_is_gold(value: str) -> bool:
    """Validate rendered CSS gold/yellow colors."""
    rgb = _css_rgb(value)
    if not rgb:
        return False
    r, g, b = rgb
    return r >= 160 and g >= 110 and b <= 90


def _visual_color_is_beige(value: str) -> bool:
    """Validate rendered CSS beige/cream colors."""
    rgb = _css_rgb(value)
    if not rgb:
        return False
    r, g, b = rgb
    return r >= 210 and g >= 190 and b >= 150 and abs(r - g) <= 45 and r >= b


def _visual_requirements_from_intent(prompt: str, description: str = "", name: str = "") -> dict:
    """Return visual checks implied by the designer intent."""
    text = _intent_text(prompt, description, name)
    wants_table = _mentions(text, r"\btable\b", r"\bdata\s*table\b", r"\btabular\b")
    return {
        "sidebar": _mentions(text, r"\bsidebar\s+nav", r"\bsidebar\s+navigation\b", r"\bleft\s+nav"),
        "table": wants_table,
        "small_table_text": wants_table and _mentions(text, r"\bsmall(er)?\s+table\s+text\b", r"\bcompact\s+table\b"),
        "contained": _mentions(text, r"\bcontained\b", r"\bmax[- ]?width\b", r"\bcentered\b"),
        "navy_header": _mentions(text, r"\bnavy\s+header\b", r"\bdark\s+blue\s+header\b"),
        "beige_cards": _mentions(text, r"\bbeige\s+cards?\b", r"\bcream\s+cards?\b"),
        "gold_buttons": _mentions(text, r"\bgold(en)?\s+buttons?\b", r"\byellow\s+buttons?\b"),
        "large_hero_title": _mentions(text, r"\bbig(ger)?\s+hero\s+title\b", r"\blarge\s+hero\b", r"\bhero\s+title\b"),
    }


def _visual_report_from_metrics(metrics: dict, requirements: dict, page_name: str = "") -> dict:
    """Compare rendered screenshot/DOM metrics with explicit visual requirements."""
    issues: list[str] = []
    css_vars = metrics.get("cssVars") or {}
    viewport_width = ((metrics.get("viewport") or {}).get("width") or 0)
    main_width = ((metrics.get("mainContent") or metrics.get("main") or {}).get("width") or 0)
    page_label = str(page_name or "").lower()
    is_data_page = bool(re.search(r"(product|categor|gallery|collection|list|table|overview)", page_label))

    if ((metrics.get("document") or {}).get("bodyTextLength") or 0) <= 0:
        issues.append("Rendered page appears blank.")
    if ((metrics.get("document") or {}).get("scrollWidth") or 0) > viewport_width + 2:
        issues.append("Rendered page has horizontal overflow.")
    if requirements.get("sidebar") and (metrics.get("sidebarCount") or 0) <= 0:
        issues.append("Screenshot DOM has no sidebar navigation region.")
    if requirements.get("table") and is_data_page and (metrics.get("tableCount") or 0) <= 0:
        issues.append("Screenshot DOM has no rendered table/DataTable.")
    if requirements.get("small_table_text") and is_data_page:
        body_px = _px_number(css_vars.get("bodySize")) or 99
        label_px = _px_number(css_vars.get("labelSize")) or 99
        if min(body_px, label_px) > 14:
            issues.append("Rendered table/body typography is not compact.")
    if requirements.get("contained") and viewport_width and main_width and main_width >= viewport_width - 24:
        issues.append("Main content is rendered full-width, not contained.")
    if requirements.get("navy_header") and not (
        _visual_color_is_dark_blue(css_vars.get("regionHeaderBg")) or _visual_color_is_dark_blue(css_vars.get("navBg"))
    ):
        issues.append("Rendered header/nav CSS is not navy.")
    if requirements.get("beige_cards") and not _visual_color_is_beige(css_vars.get("cardBg")):
        issues.append("Rendered card CSS is not beige.")
    if requirements.get("gold_buttons") and not (
        _visual_color_is_gold(css_vars.get("buttonPrimaryBg")) and _visual_color_is_gold(css_vars.get("buttonSecondaryBg"))
    ):
        issues.append("Rendered primary/secondary button CSS is not gold.")
    if requirements.get("large_hero_title") and (_px_number(css_vars.get("heroSize")) or 0) < 64 and (metrics.get("heroCount") or 0) <= 0:
        issues.append("Rendered hero title is not large or hero-header is absent.")

    return {"passed": not issues, "issues": issues}


def _run_candidate_visual_check(interface_id: str, candidate_index: int) -> dict:
    """Screenshot rendered candidate previews and verify visual consistency."""
    def _save_visual_report(report: dict) -> dict:
        try:
            interface_obj = Interface.objects.get(id=interface_id)
            data = dict(interface_obj.data or {})
            updated_candidates = list(data.get("candidates", []))
            if 0 <= candidate_index < len(updated_candidates) and updated_candidates[candidate_index]:
                updated_candidates[candidate_index] = dict(updated_candidates[candidate_index])
                updated_candidates[candidate_index]["visual_check"] = report
                data["candidates"] = updated_candidates
                Interface.objects.filter(id=interface_id).update(data=data)
        except Exception:
            pass
        return report

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return _save_visual_report({"passed": None, "skipped": True, "reason": f"playwright unavailable: {exc}", "pages": []})

    interface = Interface.objects.get(id=interface_id)
    candidates = (interface.data or {}).get("candidates", [])
    if candidate_index < 0 or candidate_index >= len(candidates) or not candidates[candidate_index]:
        return _save_visual_report({"passed": False, "skipped": False, "reason": "candidate not found", "pages": []})

    candidate = candidates[candidate_index]
    files = [f for f in candidate.get("preview_files") or [] if str(f.get("path") or "").endswith(".html")]
    requirements = _visual_requirements_from_intent(
        candidate.get("prompt", ""),
        candidate.get("description", ""),
        candidate.get("name", ""),
    )
    out_root = Path(os.environ.get("CANDIDATE_VISUAL_CHECK_DIR", "/usr/src/app/candidate-visual-check"))
    out_dir = out_root / str(interface_id) / f"candidate_{candidate_index}"
    out_dir.mkdir(parents=True, exist_ok=True)

    page_reports: list[dict] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": 1440, "height": 1100})
            page = context.new_page()
            for page_idx, file_obj in enumerate(files[:8]):
                html = str(file_obj.get("content") or "")
                path_name = Path(str(file_obj.get("path") or f"page_{page_idx}.html")).stem
                shot_path = out_dir / f"{page_idx:02d}_{re.sub(r'[^A-Za-z0-9_.-]+', '_', path_name)}.png"
                try:
                    page.set_content(html, wait_until="networkidle")
                    page.screenshot(path=str(shot_path), full_page=True)
                    metrics = page.evaluate(_VISUAL_METRICS_SCRIPT)
                    visual = _visual_report_from_metrics(metrics, requirements, path_name)
                    page_reports.append({
                        "page": path_name,
                        "screenshot": str(shot_path),
                        "passed": visual["passed"],
                        "issues": visual["issues"],
                        "metrics": metrics,
                    })
                except Exception as exc:
                    page_reports.append({
                        "page": path_name,
                        "screenshot": str(shot_path),
                        "passed": False,
                        "issues": [f"screenshot check failed: {exc}"],
                        "metrics": {},
                    })
            context.close()
            browser.close()
    except Exception as exc:
        return _save_visual_report({"passed": None, "skipped": True, "reason": f"playwright failed: {exc}", "pages": []})

    report = {
        "passed": all(page_report.get("passed") for page_report in page_reports) if page_reports else False,
        "skipped": False,
        "requirements": requirements,
        "pages": page_reports,
    }
    return _save_visual_report(report)


def validate_and_save_candidate(
    interface_id: str,
    candidate_index: int,
    name: str,
    description: str,
    pages: str,
    sections: str,
    tokens: str = "",
    styling: str = "",
    prompt: str = "",
    derived_from: str = "",
    designer_requirements: str = "",
    variation_strategy: str = "",
) -> str:
    """Validate and save one interface candidate (call once per candidate index 0, 1, 2).

    Args:
        interface_id: The interface UUID (from the message).
        candidate_index: 0, 1, or 2.
        name: Short display name for this design direction (e.g. "Card-forward Commerce").
        description: One sentence describing this candidate's visual approach.
        pages: JSON string containing a list of page objects. Each page: {id, name, type, sections: [{value: section_id}, ...]}.
               type is required and must be {"value":"normal","label":"Normal"} or {"value":"activity","label":"Activity"}.
               Pages do NOT contain section data ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â they only reference section IDs.
        sections: JSON string containing a list of ALL section definition objects. Each section must have:
                  id, name, layout, position, col_span, primary_model, attributes, operations, style.
                  This is SEPARATE from pages. Both pages[] and sections[] are required.
        tokens: Optional JSON string with design tokens.
        styling: Optional JSON string with global styling overrides.
        prompt: Original user design prompt (optional, for logging).
        derived_from: Optional source candidate index/id when regenerating from a selected candidate.
        designer_requirements: Optional human-in-the-loop requirements used for regeneration.
        variation_strategy: Optional short label for how this candidate differs from the source.
    """
    try:
        if isinstance(pages, str): pages = json.loads(pages)
        if isinstance(sections, str): sections = json.loads(sections)
        input_section_ids = {str(s.get("id")) for s in (sections or []) if isinstance(s, dict) and s.get("id")}
        styling_dict = _norm_candidate_styling(styling)

        interface = Interface.objects.get(id=interface_id)
        iface = {
            "id": str(interface.id),
            "name": interface.name,
            "description": interface.description,
            "system": str(interface.system_id),
            "actor": str(interface.actor_id) if interface.actor_id else None,
            "data": interface.data or {},
        }
        system_id = iface.get("system")
        tokens_d: dict = _norm_candidate_tokens(tokens, styling_dict)

        raw_classifiers = [
            {"id": str(c.id), "data": c.data or {}}
            for c in interface.system.classifiers.all()
        ]
        model_attrs: dict = {}; model_id_by_name: dict = {}
        for c in raw_classifiers:
            cdata = c.get("data", {}); cname = cdata.get("name", "")
            attrs = {a.get("name", "") for a in cdata.get("attributes", []) if a.get("name")}
            if cname:
                model_attrs[cname] = attrs
                model_id_by_name[cname] = str(c.get("id") or cdata.get("id") or cname)
        known_models = set(model_attrs.keys())

        usecase_navigation: dict = {}
        model_graph: dict = {}
        try:
            system_context = _fetch_system_context_data(system_id)
            actor_name = _actor_name_from_context(system_context, iface.get("actor"))
            model_graph = extract_uml_intelligence(
                system_context,
                str(iface.get("actor") or ""),
                actor_name or "",
            ).get("model_graph") or {}
            usecase_navigation = _build_usecase_navigation(system_context, str(iface.get("actor") or ""), actor_name)
            pages = _ensure_usecase_pages(pages, usecase_navigation)
        except Exception:
            usecase_navigation = {}
            model_graph = {}
        sections = _normalize_activity_action_sections(pages, sections)
        sections = _normalize_chrome_sections(sections)

        def _norm_model(n):
            """Normalize model names for fuzzy comparison."""
            return re.sub(r'[\s_-]', '', str(n or '')).lower()
        model_names_fuzzy = {_norm_model(m): m for m in known_models}

        def _canonical_model_name(name):
            """Return the canonical known model name for a fuzzy model reference."""
            return name if name in known_models else model_names_fuzzy.get(_norm_model(name), "")

        page_names = {p.get("name", "") for p in pages}
        page_ref_to_name: dict = {}
        for p in pages:
            pname, pid = p.get("name", ""), p.get("id", "")
            if pname: page_ref_to_name[pname] = pname; page_ref_to_name[pname.lower()] = pname
            if pid: page_ref_to_name[pid] = pname; page_ref_to_name[pid.lower()] = pname

        # Normalize sections with a small guardrail layer:
        # supported layouts/styles, UML-bound attributes, and valid workflow targets.
        fixed_sections = []
        for s in sections:
            s = _drop_deprecated_section_fields(s)
            s["layout"] = _normalize_layout_alias(s.get("layout"))
            s["operations"] = _normalize_section_operations(s.get("operations"))
            s["component"] = _infer_section_component(s)
            pm = s.get("primary_model", "")
            if pm and pm not in model_attrs:
                canon = model_names_fuzzy.get(_norm_model(pm))
                if canon: s["primary_model"] = s["class"] = pm = canon
            if s.get("layout") not in _VALID_SECTION_LAYOUTS:
                s["layout"] = "card" if pm else "main-header"
                s["component"] = _infer_section_component(s)
            if pm and pm in model_attrs:
                new_attrs: list = []
                for attr in s.get("attributes", []):
                    attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                    if "." not in attr_name and (not pm or attr_name in model_attrs.get(pm, set())):
                        new_attrs.append(attr)
                if not new_attrs and s.get("layout") in _DATA_SECTION_LAYOUTS:
                    new_attrs = list(_model_field_names(model_attrs, pm, 6))
                s["attributes"] = new_attrs
            workflow = dict(s.get("workflow") or {})
            workflow_action = workflow.get("action") or s.get("workflow_action", "")
            if workflow_action and workflow_action not in {"complete", "complete_then_page", "complete_then_target", "navigate", "none"}:
                workflow.pop("action", None)
            workflow_target = workflow.get("target_page") or workflow.get("targetPage") or s.get("target_page") or s.get("targetPage") or ""
            normalized_target = page_ref_to_name.get(str(workflow_target), "") or page_ref_to_name.get(str(workflow_target).lower(), "")
            if workflow_target and normalized_target:
                workflow["target_page"] = normalized_target
            elif workflow_target and workflow_target not in page_names:
                workflow.pop("target_page", None); workflow.pop("targetPage", None)
            if workflow:
                s["workflow"] = workflow
            style = dict(s.get("style") or {})
            for field, valid_vals in _VALID_SECTION_STYLE.items():
                if style.get(field) and style[field] not in valid_vals:
                    style.pop(field, None)
            s["style"] = style
            s["field_layout"] = _normalize_field_layout(s)
            fixed_sections.append(s)
        for s in fixed_sections:
            if s.get("layout") in _DATA_SECTION_LAYOUTS:
                style = dict(s.get("style") or {})
                if not style.get("color"):
                    style["color"] = "accent"; s["style"] = style

        # Normalize pages
        fixed_pages = []
        for i, p in enumerate(pages):
            p = dict(p)
            p["type"] = _canonical_page_type(_infer_page_type_value(p))
            if not p.get("id"): p["id"] = f"page_{candidate_index}_{i}"
            p.setdefault("category", None)
            fixed_pages.append(p)
        for i, s in enumerate(fixed_sections):
            if not s.get("id"):
                model = (s.get("primary_model") or "chrome").lower().replace(" ", "_")
                fixed_sections[i] = {**s, "id": f"{model}_{s.get('layout', 'section')}_{candidate_index}_{i}"}
            if not fixed_sections[i].get("name"):
                fixed_sections[i]["name"] = fixed_sections[i]["id"]

        fixed_pages = _ensure_usecase_pages(fixed_pages, usecase_navigation)
        fixed_sections = _normalize_select_existing_sections(fixed_pages, fixed_sections)
        for s in fixed_sections:
            s["operations"] = _normalize_section_operations(s.get("operations"))
            s["component"] = _infer_section_component(s)
            s["field_layout"] = _normalize_field_layout(s)
        fixed_sections = _normalize_chrome_sections(fixed_sections)
        fixed_sections = _apply_nav_methods(fixed_pages, fixed_sections, usecase_navigation)
        styling_d = styling_dict or {}
        fixed_pages, fixed_sections = _dedupe_agent_header_shells(fixed_pages, fixed_sections)
        fixed_sections = _finalize_data_section_bindings(fixed_sections, model_attrs)
        for s in fixed_sections:
            s["component"] = _infer_section_component(s)
        auto_allowed_layouts = (
            _HEADER_TEMPLATE_LAYOUTS
            | _FOOTER_TEMPLATE_LAYOUTS
            | _HEADER_NAV_LAYOUTS
            | {"site-nav", "nav-links", "nav-bar", "activity_action", "activity_start", "activity_tasks"}
        )
        fixed_sections = [
            s for s in fixed_sections
            if str(s.get("id") or "") in input_section_ids
            or _normalize_layout_alias(s.get("layout")) in auto_allowed_layouts
            or s.get("position") in {"header", "footer"}
        ]
        fixed_pages, fixed_sections = _ensure_logical_related_sections(fixed_pages, fixed_sections, model_graph)
        for s in fixed_sections:
            s["component"] = _infer_section_component(s)
            s["field_layout"] = _normalize_field_layout(s)

        # Normalize section refs and assign sections to pages that have none
        for i, p in enumerate(fixed_pages):
            if p.get("sections") is not None:
                fixed_pages[i] = {**p, "sections": [
                    {**r, "sections": [s if isinstance(s, dict) else {"value": s} for s in (r.get("sections") or [])]}
                    if isinstance(r, dict) and r.get("type") == "card"
                    else (r if isinstance(r, dict) else {"value": r})
                    for r in p["sections"]
                ]}
        assignable = [s for s in fixed_sections if s.get("position", "main") not in {"header", "hero", "footer", "sidebar"} and s.get("layout") in {"card", "list", "table", "detail", "gallery", "form"}]
        if any(not p.get("sections") for p in fixed_pages) and assignable:
            model_to_secs: dict = defaultdict(list)
            for s in assignable: model_to_secs[s.get("primary_model", "")].append(s["id"])
            rebuilt: list = []; model_assigned: dict = defaultdict(int)
            for p in fixed_pages:
                if p.get("sections"): rebuilt.append(p); continue
                if _page_type_value(p) == "activity" or "workflow" in f"{p.get('id', '')} {p.get('name', '')}".lower():
                    rebuilt.append(p); continue
                pm = p.get("primary_model", "")
                cands = model_to_secs.get(pm, []); start = model_assigned[pm]
                assigned = [{"value": cands[start]}] if start < len(cands) else []
                if assigned: model_assigned[pm] += 1
                if not assigned and model_to_secs.get("", []):
                    fb = model_to_secs[""]
                    if model_assigned[""] < len(fb):
                        assigned = [{"value": fb[model_assigned[""]]}]; model_assigned[""] += 1
                rebuilt.append({**p, "sections": assigned})
            fixed_pages = rebuilt

        section_ids = {s["id"] for s in fixed_sections}
        for p in fixed_pages:
            filtered = []
            for ref in (p.get("sections") or []):
                if isinstance(ref, dict) and ref.get("type") == "card":
                    valid_nested = [s for s in (ref.get("sections") or []) if _ref_id(s) in section_ids]
                    if valid_nested:
                        filtered.append({**ref, "sections": valid_nested})
                elif _ref_id(ref) in section_ids:
                    filtered.append(ref)
            p["sections"] = filtered
        fixed_pages = _assign_default_page_categories(fixed_pages, fixed_sections, model_id_by_name)

        label_prompt = prompt or designer_requirements
        name = name or _candidate_variant_name(label_prompt, candidate_index)
        variation_strategy = variation_strategy or name
        fixed_pages, fixed_sections, tokens_d, styling_d = _apply_design_intent_patch(
            fixed_pages,
            fixed_sections,
            tokens_d,
            styling_dict or {},
            prompt=label_prompt,
            description=description,
            name=name,
        )
        compliance = _candidate_compliance_report(
            fixed_pages,
            fixed_sections,
            tokens_d,
            prompt=label_prompt,
            description=description,
            name=name,
        )

        data = dict(iface.get("data") or {})
        data["categories"] = _merge_page_categories(data.get("categories") or [], fixed_pages)
        candidates = list(data.get("candidates") or [])
        candidate = {
            "id": f"c{candidate_index}", "name": name, "description": description,
            "pages": fixed_pages, "sections": fixed_sections,
            "generated_by": "interface_generator", "prompt": prompt or designer_requirements,
            "compliance": compliance,
            **({"tokens": tokens_d} if tokens_d else {}),
            **({"styling": styling_d} if styling_d else {}),
        }
        if derived_from != "": candidate["derived_from"] = derived_from
        if designer_requirements: candidate["designer_requirements"] = designer_requirements
        if variation_strategy: candidate["variation_strategy"] = variation_strategy
        while len(candidates) <= candidate_index: candidates.append(None)
        candidates[candidate_index] = candidate
        data["candidates"] = candidates
        Interface.objects.filter(id=interface_id).update(data=data)
        warning_suffix = "" if compliance.get("passed") else f" with {len(compliance.get('issues') or [])} compliance warning(s)"
        return f"OK: candidate {candidate_index} '{name}' saved successfully{warning_suffix}."
    except Interface.DoesNotExist:
        return f"Error saving candidate: Interface {interface_id} not found."
    except Exception as e:
        return f"Error saving candidate: {e}"

def get_candidate_regeneration_context(interface_id: str, candidate_index: int, designer_requirements: str = "") -> str:
    """Return the selected candidate as the baseline for human-guided regeneration."""
    try:
        interface = Interface.objects.get(id=interface_id)
        iface = {
            "name": interface.name,
            "description": interface.description,
            "system": str(interface.system_id),
            "actor": str(interface.actor_id) if interface.actor_id else None,
        }
        data = dict(interface.data or {})
        candidates = list(data.get("candidates") or [])
        idx = int(candidate_index)
        regeneration_base = data.get("regeneration_base_candidate") or {}
        if idx < 0 or idx >= len(candidates) or not candidates[idx]:
            if int(regeneration_base.get("selected_candidate_index", -1)) != idx or not regeneration_base.get("candidate"):
                return f"ERROR: candidate {candidate_index} not found."
            base = dict(regeneration_base.get("candidate") or {})
        else:
            base = dict(candidates[idx])
        context = {
            "interface_id": interface_id,
            "selected_candidate_index": idx,
            "designer_requirements": designer_requirements,
            "regeneration_contract": {
                "overwrite_candidate_indices": [0, 1, 2],
                "derive_from_selected_candidate": True,
                "preserve_page_semantics": True,
                "preserve_workflow_sections": [
                    "activity_start",
                    "activity_tasks",
                    "activity_action",
                ],
                "keep_task_pages_as_activity_pages": True,
                "keep_normal_pages_as_normal_pages": True,
            },
            "current_interface": {
                "name": iface.get("name"),
                "description": iface.get("description", ""),
                "system": iface.get("system"),
                "actor": iface.get("actor"),
            },
            "base_candidate": {
                "id": base.get("id"),
                "name": base.get("name"),
                "description": base.get("description", ""),
                "pages": base.get("pages", []),
                "sections": base.get("sections", []),
                "tokens": base.get("tokens", data.get("tokens", {})),
                "styling": base.get("styling", data.get("styling", {})),
                "variation_strategy": base.get("variation_strategy"),
            },
        }
        return json.dumps(context, indent=2)
    except Interface.DoesNotExist:
        return f"ERROR: interface {interface_id} not found."
    except Exception as e:
        return f"Error fetching candidate regeneration context: {e}"

def _candidate_variant_name(prompt: str, index: int) -> str:
    """Build candidate variant name."""
    prefix = "Agent"
    suffixes = ("Gallery", "Table", "Showcase")
    return f"{prefix} {suffixes[index % len(suffixes)]}"


def _parse_llm_json(text: str):
    """Parse llm json."""
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        pass

    decoder = json.JSONDecoder()
    candidates_pattern = re.search(r'"candidates"\s*:\s*\[', raw)
    preferred_starts = []
    if candidates_pattern:
        container_start = raw.rfind("{", 0, candidates_pattern.start())
        preferred_starts.append(container_start if container_start >= 0 else 0)
    starts = [i for i, ch in enumerate(raw) if ch in "[{"]
    fallback_obj = None
    for start in [*preferred_starts, *starts]:
        try:
            obj, _end = decoder.raw_decode(raw[start:])
            if isinstance(obj, dict) and isinstance(obj.get("candidates"), list):
                return obj
            if isinstance(obj, list):
                return obj
            if fallback_obj is None:
                fallback_obj = obj
        except Exception:
            continue
    if fallback_obj is not None:
        return fallback_obj

    repaired = raw
    while repaired.endswith("}") and repaired.count("{") < repaired.count("}"):
        repaired = repaired[:-1].rstrip()
        try:
            return json.loads(repaired)
        except Exception:
            continue
    raise ValueError("LLM response was not valid JSON")


def _candidate_list_from_llm_response(text: str) -> list:
    """Build candidate list from LLM response."""
    result = _parse_llm_json(text)
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and isinstance(result.get("candidates"), list):
        return result["candidates"]
    return []


_FULL_WIDTH_PROMPT_RE = re.compile(
    r"(?:\b(?:full[- ]?width|fullscreen|full[- ]?screen|edge[- ]?to[- ]?edge|immersive|kiosk)\b|全宽|全屏|通栏|沉浸)",
    re.I,
)
_WIDTH_PROMPT_RE = re.compile(
    r"(?:\b(?:contained|wide|full[- ]?width|fullscreen|full[- ]?screen|edge[- ]?to[- ]?edge|immersive|kiosk)\b|居中|宽版|全宽|全屏|通栏|沉浸)",
    re.I,
)
_DEFAULT_WIDTH_VARIANTS = (
    {"main_width": "contained", "header_width": "contained", "footer_width": "contained"},
    {"main_width": "wide", "header_width": "contained", "footer_width": "contained"},
    {"main_width": "full", "header_width": "full", "footer_width": "full"},
)


def _guard_generated_page_widths(candidate: dict, prompt: str, candidate_index: int = 0) -> dict:
    """Distribute candidate widths unless the prompt explicitly specifies width."""
    guarded = copy.deepcopy(candidate)
    if _WIDTH_PROMPT_RE.search(prompt or ""):
        return guarded

    width_variant = _DEFAULT_WIDTH_VARIANTS[candidate_index % len(_DEFAULT_WIDTH_VARIANTS)]
    for page in guarded.get("pages") or []:
        if not isinstance(page, dict):
            continue
        layout = page.get("layout") or {}
        if not isinstance(layout, dict):
            continue
        layout["main_width"] = width_variant["main_width"]
        layout["header_width"] = width_variant["header_width"]
        layout["footer_width"] = width_variant["footer_width"]
        page["layout"] = layout
    return guarded


def _llm_generate_3_candidates(pages: list, sections: list, prompt: str) -> list | None:
    """Call Gemini to generate 3 layout/style variants. Returns list of 3 candidate dicts or None on failure."""
    try:
        import google.genai as _genai
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        client = _genai.Client(api_key=api_key)

        # Skeleton: semantic context only, no current layout values (avoids LLM anchoring to old state)
        section_skeleton = [
            {
                "id": s.get("id", ""),
                "name": s.get("name", ""),
                "primary_model": s.get("primary_model", ""),
                "role": s.get("role", ""),
            }
            for s in sections if s.get("id")
        ]
        page_skeleton = [
            {"id": p.get("id", ""), "name": p.get("name", ""), "type": p.get("type", "")}
            for p in pages if p.get("id")
        ]

        user_prompt_text = build_generate_candidates_prompt(
            page_skeleton=page_skeleton,
            section_skeleton=section_skeleton,
            designer_prompt=prompt,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_prompt_text,
            config={
                "system_instruction": GENERATE_CANDIDATES_SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "max_output_tokens": 65536,
            },
        )
        print(f"[llm_generate_3_candidates] raw response:\n{response.text}", flush=True)
        candidates = _candidate_list_from_llm_response(response.text)
        if len(candidates) < 3:
            print(f"[llm_generate_3_candidates] only got {len(candidates)} candidates, falling back", flush=True)
            return None
        return [_guard_generated_page_widths(candidate, prompt, idx) for idx, candidate in enumerate(candidates[:3])]
    except Exception as e:
        import traceback
        print(f"[llm_generate_3_candidates] failed: {e}\n{traceback.format_exc()}", flush=True)
        return None


def _llm_regenerate_3_candidates(pages: list, sections: list, designer_requirements: str, base_styling: dict) -> list | None:
    """Like _llm_generate_3_candidates but anchored to the selected candidate's existing layout and styling."""
    try:
        import google.genai as _genai
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        client = _genai.Client(api_key=api_key)

        # Include current layout as context so LLM knows what to preserve vs. what to vary
        section_skeleton = [
            {
                "id": s.get("id", ""),
                "name": s.get("name", ""),
                "primary_model": s.get("primary_model", ""),
                "role": s.get("role", ""),
                "current_layout": s.get("layout", ""),
                "current_component": s.get("component", ""),
                "current_position": s.get("position", ""),
            }
            for s in sections if s.get("id")
        ]
        page_skeleton = [
            {
                "id": p.get("id", ""),
                "name": p.get("name", ""),
                "current_main_width": (p.get("layout") or {}).get("main_width", "contained"),
                "current_header_width": (p.get("layout") or {}).get("header_width", "contained"),
            }
            for p in pages if p.get("id")
        ]

        user_prompt_text = build_regenerate_candidates_prompt(
            page_skeleton=page_skeleton,
            section_skeleton=section_skeleton,
            designer_requirements=designer_requirements,
            base_styling=base_styling,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_prompt_text,
            config={
                "system_instruction": REGENERATE_CANDIDATES_SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "max_output_tokens": 65536,
            },
        )
        candidates = _candidate_list_from_llm_response(response.text)
        if len(candidates) < 3:
            return None
        return [_guard_generated_page_widths(candidate, designer_requirements, idx) for idx, candidate in enumerate(candidates[:3])]
    except Exception as e:
        import traceback
        print(f"[llm_regenerate_3_candidates] failed: {e}\n{traceback.format_exc()}", flush=True)
        return None


_COLLECTION_LAYOUTS = {"card", "table", "gallery", "list"}

def _allowed_layout(role: str, base_layout: str, proposed: str) -> str:
    """Return the layout to actually apply after LLM merge, protecting role-locked sections."""
    if role == "object_form" and proposed != "form":
        return base_layout
    if role in {"object_detail", "object_summary"} and proposed in _COLLECTION_LAYOUTS:
        return base_layout
    if role == "navigation" and proposed not in {"site-nav", "nav-links"}:
        return base_layout
    if role and role.startswith("activity_"):
        return base_layout
    return proposed


def _merge_llm_candidate(base_pages: list, base_sections: list, llm_candidate: dict) -> tuple[list, list]:
    """Merge LLM layout/style decisions onto base pages/sections, preserving all data fields."""
    pages = copy.deepcopy(base_pages)
    sections = [_drop_deprecated_section_fields(s) for s in copy.deepcopy(base_sections)]

    llm_sec_map = {str(s.get("id", "")): s for s in (llm_candidate.get("sections") or []) if s.get("id")}
    llm_page_map = {str(p.get("id", "")): p for p in (llm_candidate.get("pages") or []) if p.get("id")}

    for sec in sections:
        sid = str(sec.get("id", ""))
        llm = llm_sec_map.get(sid)
        if not llm:
            continue
        role = str(sec.get("role") or "")
        # Layout: enforce role-based constraints to prevent LLM from breaking form/detail/activity sections
        if llm.get("layout") is not None:
            safe = _allowed_layout(role, str(sec.get("layout") or ""), llm["layout"])
            sec["layout"] = safe
            # Only apply component if layout was accepted
            if safe == llm["layout"] and llm.get("component") is not None:
                sec["component"] = llm["component"]
        for field in ("position", "col_span"):
            if llm.get(field) is not None:
                sec[field] = llm[field]
        if llm.get("style"):
            merged = dict(sec.get("style") or {})
            merged.update(llm["style"])
            sec["style"] = merged

    for page in pages:
        pid = str(page.get("id", ""))
        llm = llm_page_map.get(pid)
        if not llm:
            continue
        if llm.get("layout"):
            merged = dict(page.get("layout") or {})
            merged.update(llm["layout"])
            page["layout"] = merged
        if llm.get("gap"):
            page["gap"] = llm["gap"]

    return pages, sections


_TEXT_SIZE_TOKENS = {
    "xs": {"typography.hero.size": "44px", "typography.display.size": "32px", "typography.title-md.size": "17px", "typography.lead.size": "15px", "typography.body.size": "13px", "typography.caption.size": "10px", "typography.label.size": "12px"},
    "sm": {"typography.hero.size": "48px", "typography.display.size": "34px", "typography.title-md.size": "18px", "typography.lead.size": "16px", "typography.body.size": "14px", "typography.caption.size": "11px", "typography.label.size": "13px"},
    "md": {"typography.hero.size": "56px", "typography.display.size": "40px", "typography.title-md.size": "20px", "typography.lead.size": "18px", "typography.body.size": "16px", "typography.caption.size": "12px", "typography.label.size": "14px"},
    "lg": {"typography.hero.size": "64px", "typography.display.size": "46px", "typography.title-md.size": "24px", "typography.lead.size": "20px", "typography.body.size": "18px", "typography.caption.size": "13px", "typography.label.size": "15px"},
    "xl": {"typography.hero.size": "72px", "typography.display.size": "52px", "typography.title-md.size": "28px", "typography.lead.size": "22px", "typography.body.size": "20px", "typography.caption.size": "14px", "typography.label.size": "16px"},
}


def _tokens_from_llm_styling(llm_styling: dict, base_tokens: dict, prompt: str, index: int) -> dict:
    """Build color and typography tokens seeded from LLM styling output."""
    tokens = dict(base_tokens or {})
    accent = llm_styling.get("accentColor") or ""
    secondary = llm_styling.get("accentSecondary") or ""
    if accent:
        tokens["accent.hex"] = accent
    if secondary:
        tokens["color.secondary.hex"] = secondary
    bg = llm_styling.get("backgroundColor") or ""
    if bg:
        tokens["page.body.bg_hex"] = bg
        tokens["page.bg.hex"] = bg
    text_color = llm_styling.get("textColor") or ""
    if text_color:
        tokens["page.body.text_hex"] = text_color
        tokens["text.primary.hex"] = text_color
    # Preserve fine-grained color tokens when the LLM provides them.
    _FINE_GRAINED_HEX = (
        "region.header.bg_hex", "region.header.text_hex",
        "region.footer.bg_hex", "region.footer.text_hex",
        "region.main.bg_hex", "region.sidebar.bg_hex", "region.border_hex",
        "component.card.bg_hex", "component.card.border_hex",
        BUTTON_PRIMARY_BG_HEX, BUTTON_PRIMARY_TEXT_HEX,
        "button.secondary.bg_hex", "button.secondary.text_hex",
        "button.ghost.text_hex", "button.danger.bg_hex", "button.link.text_hex",
        "input.bg_hex", "input.border_hex", "input.border_focus_hex", "input.text_hex",
        "nav.bg_hex", "nav.text_hex",
        "table.header.bg_hex", "table.header.text_hex",
        "badge.info.bg_hex", "text.muted.hex",
    )
    for key in _FINE_GRAINED_HEX:
        val = llm_styling.get(key) or ""
        if val:
            tokens[key] = val
    text_size = llm_styling.get("textSize") or ""
    if text_size in _TEXT_SIZE_TOKENS:
        tokens.update(_TEXT_SIZE_TOKENS[text_size])
    tokens["design.variant_index"] = str(index)
    return tokens


def _tokens_from_llm_schema(llm_candidate: dict, base_tokens: dict, prompt: str, index: int) -> dict:
    """Prefer the LLM's complete top-level tokens; use styling only as a fallback seed."""
    llm_styling = llm_candidate.get("styling") or {}
    if isinstance(llm_styling, str):
        try:
            llm_styling = json.loads(llm_styling)
        except Exception:
            llm_styling = {}

    tokens = _tokens_from_llm_styling(llm_styling, base_tokens, prompt, index)
    llm_tokens = llm_candidate.get("tokens") or {}
    if isinstance(llm_tokens, str):
        try:
            llm_tokens = json.loads(llm_tokens)
        except Exception:
            llm_tokens = {}

    if isinstance(llm_tokens, dict):
        for key, value in llm_tokens.items():
            if value is not None and value != "":
                tokens[str(key)] = value

    tokens["design.variant_index"] = str(index)
    return tokens


def generate_candidate_set(interface_id: str, prompt: str = "") -> str:
    """Generate and save exactly 3 candidates from the current interface DSL and designer prompt."""
    try:
        interface = Interface.objects.get(id=interface_id)
        data = dict(interface.data or {})
        pages = data.get("pages") or []
        sections = data.get("sections") or []
        if not pages or not sections:
            return "ERROR: Interface has no pages/sections to generate candidates from."

        raw_base_tokens = dict(data.get("tokens") or {})
        # Do not merge regex parser styling overrides here. The LLM candidate
        # schema should decide fine-grained styling/token values.
        base_styling = dict(data.get("styling") or {})

        llm_candidates = _llm_generate_3_candidates(pages, sections, prompt)

        if not llm_candidates:
            return "ERROR: LLM failed to generate candidates."
        results = []
        for index in range(3):
            llm_cand = llm_candidates[index]
            variant_pages, variant_sections = _merge_llm_candidate(pages, sections, llm_cand)
            variant_pages, variant_sections = _dedupe_agent_header_shells(variant_pages, variant_sections)

            llm_styling = llm_cand.get("styling") or {}
            llm_tokens = llm_cand.get("tokens") or {}
            tokens = _tokens_from_llm_schema(llm_cand, raw_base_tokens, prompt, index)

            styling = dict(base_styling or {})
            for key in (
                "fontFamily", "radius", "buttonStyle", "cardHover", "imageRatio", "divider",
                "pageMaxWidth", "accentColor", "accentSecondary", "backgroundColor", "textColor",
                *_STYLING_TOKEN_KEYS,
            ):
                if llm_styling.get(key) is not None:
                    styling[key] = llm_styling[key]
                elif isinstance(llm_tokens, dict) and llm_tokens.get(key) is not None:
                    styling[key] = llm_tokens[key]
            fallback_name = _candidate_variant_name(prompt, index)
            variant_name = llm_cand.get("name") or fallback_name
            styling["variantIndex"] = index
            styling["variantName"] = variant_name
            variation_strategy = variant_name

            result = validate_and_save_candidate(
                interface_id=interface_id,
                candidate_index=index,
                name=variant_name,
                description=f"Agent-generated candidate {index + 1} using '{prompt or 'current'}' as the designer requirement.",
                pages=json.dumps(variant_pages),
                sections=json.dumps(variant_sections),
                tokens=json.dumps(tokens) if tokens else "",
                styling=json.dumps(styling) if styling else "",
                prompt=prompt,
                variation_strategy=variation_strategy,
            )
            results.append(result)
            if not str(result).startswith("OK:"):
                return f"ERROR: candidate {index} failed: {result}"
            _render_candidate_preview_local(interface_id, index)
            _run_candidate_visual_check(interface_id, index)
        return "OK: generated and saved 3 candidates. " + " | ".join(results)
    except Interface.DoesNotExist:
        return f"ERROR: interface {interface_id} not found."
    except Exception as e:
        return f"ERROR: generate_candidate_set failed: {e}"

def regenerate_candidate_set(interface_id: str, selected_candidate_index: int, designer_requirements: str = "") -> str:
    """Regenerate exactly 3 candidates from a selected/base candidate using deterministic variants."""
    try:
        context_raw = get_candidate_regeneration_context(interface_id, selected_candidate_index, designer_requirements)
        if str(context_raw).startswith("ERROR") or str(context_raw).startswith("Error"):
            return context_raw
        context = json.loads(context_raw)
        base = context.get("base_candidate") or {}
        pages = base.get("pages") or []
        sections = base.get("sections") or []
        if not pages or not sections:
            return "ERROR: selected candidate has no pages/sections."
        raw_base_tokens = copy.deepcopy(base.get("tokens") or {})
        base_styling_raw = dict(base.get("styling") or {})
        # Do not merge regex parser styling overrides here. The LLM candidate
        # schema should decide fine-grained styling/token values.
        base_styling = dict(base_styling_raw or {})

        llm_candidates = _llm_regenerate_3_candidates(pages, sections, designer_requirements, base_styling_raw)
        if not llm_candidates:
            return "ERROR: LLM failed to regenerate candidates."

        results = []
        for index in range(3):
            llm_cand = llm_candidates[index]
            variant_pages, variant_sections = _merge_llm_candidate(pages, sections, llm_cand)
            variant_pages, variant_sections = _dedupe_agent_header_shells(variant_pages, variant_sections)

            llm_styling = llm_cand.get("styling") or {}
            llm_tokens = llm_cand.get("tokens") or {}
            tokens = _tokens_from_llm_schema(llm_cand, raw_base_tokens, designer_requirements, index)

            styling = dict(base_styling or {})
            for key in (
                "fontFamily", "radius", "buttonStyle", "cardHover", "imageRatio", "divider",
                "pageMaxWidth", "accentColor", "accentSecondary", "backgroundColor", "textColor",
                *_STYLING_TOKEN_KEYS,
            ):
                if llm_styling.get(key) is not None:
                    styling[key] = llm_styling[key]
                elif isinstance(llm_tokens, dict) and llm_tokens.get(key) is not None:
                    styling[key] = llm_tokens[key]
            fallback_name = _candidate_variant_name(designer_requirements, index)
            base_variant_name = llm_cand.get("name") or fallback_name
            styling["variantIndex"] = index
            styling["variantName"] = base_variant_name
            variant_name = f"{base_variant_name} Regen"
            variation_strategy = base_variant_name

            result = validate_and_save_candidate(
                interface_id=interface_id,
                candidate_index=index,
                name=variant_name,
                description=f"Regenerated from candidate {selected_candidate_index + 1} with {styling.get('variantName', '')} structure.",
                pages=json.dumps(variant_pages),
                sections=json.dumps(variant_sections),
                tokens=json.dumps(tokens) if tokens else "",
                styling=json.dumps(styling) if styling else "",
                prompt=designer_requirements,
                derived_from=str(selected_candidate_index),
                designer_requirements=designer_requirements,
                variation_strategy=variation_strategy,
            )
            results.append(result)
            if not str(result).startswith("OK:"):
                return f"ERROR: regenerated candidate {index} failed: {result}"
            _render_candidate_preview_local(interface_id, index)
            _run_candidate_visual_check(interface_id, index)
        return "OK: regenerated and saved 3 candidates. " + " | ".join(results)
    except Exception as e:
        return f"ERROR: regenerate_candidate_set failed: {e}"
