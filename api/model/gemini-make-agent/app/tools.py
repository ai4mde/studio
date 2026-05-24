import os
import requests
import json
import re
from google.adk.tools import FunctionTool
from .ooui_planner import DATA_SECTION_ROLES, build_ooui_plan_from_navigation

METADATA_API_BASE = os.getenv("METADATA_API_BASE", "http://studio-api:8000/api/v1/metadata")
PROTOTYPE_API_BASE = os.getenv("PROTOTYPE_API_BASE", "http://studio-prototypes:8010")
_METADATA_API_KEY = os.getenv("METADATA_API_KEY")
_AUTH_HEADERS = {"Authorization": f"Bearer {_METADATA_API_KEY}"} if _METADATA_API_KEY else {}
TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../prototypes/backend/generation/templates"))
DESIGN_SPECS_DIR = os.getenv("DESIGN_SPECS_DIR", "/design_specs")

_DESIGN_DOMAIN_PRIORITIES = {
    "commerce": ["ecommerce.md", "shopify.md", "airbnb.md", "apple.md", "nike.md"],
    "finance": ["stripe.md", "monzo.md", "coinbase.md", "binance.md", "kraken.md"],
    "devtool": ["vercel.md", "supabase.md", "clickhouse.md", "expo.md", "hashicorp.md"],
    "creative": ["figma.md", "framer.md", "notion.md", "miro.md", "linear.app.md"],
    "enterprise": ["ibm.md", "salesforce.md", "airtable.md", "intercom.md", "minimal.md"],
    "luxury": ["apple.md", "ferrari.md", "lamborghini.md", "bmw.md", "bugatti.md"],
}

_DOMAIN_KEYWORDS = {
    "commerce": {"product", "cart", "order", "customer", "seller", "inventory", "catalog", "checkout", "shipment", "address", "review"},
    "finance": {"payment", "transaction", "invoice", "subscription", "account", "balance", "payout", "refund", "card", "wallet", "price",
                "loan", "credit", "application", "applicant", "approval", "disbursement", "interest", "amount", "collateral", "assessment", "lender", "borrower", "banking", "finance", "financial"},
    "devtool": {"api", "deployment", "repository", "query", "log", "event", "metric", "cluster", "database", "pipeline", "build"},
    "creative": {"design", "canvas", "prototype", "board", "asset", "frame", "comment", "project", "workspace"},
    "enterprise": {"organization", "employee", "team", "role", "permission", "ticket", "case", "contract", "report", "dashboard",
                   "form", "submission", "review", "status", "workflow", "request", "assignment", "task", "document", "approval"},
    "luxury": {"vehicle", "car", "model", "configuration", "dealer", "lifestyle", "event"},
}

def _as_list(payload, key: str) -> list:
    if isinstance(payload, dict):
        return payload.get(key, []) or []
    return payload or []

def _name_id(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_\s-]", "", str(value or ""))
    value = re.sub(r"[\s-]+", "_", value.strip())
    return value or "workflow_step"

def _page_name(value: str) -> str:
    return "_".join(part[:1].upper() + part[1:] for part in _name_id(value).split("_") if part)

def _workflow_page_name(value: str) -> str:
    return f"Workflow_{_page_name(value)}"

def _section_id(value: str) -> str:
    return _name_id(value).lower()

def _design_spec_files() -> list[str]:
    if not os.path.exists(DESIGN_SPECS_DIR):
        return []
    return sorted(f for f in os.listdir(DESIGN_SPECS_DIR) if f.endswith(".md"))

def _read_design_spec(spec_name: str) -> str:
    safe_name = os.path.basename(spec_name)
    design_path = os.path.join(DESIGN_SPECS_DIR, safe_name)
    if not os.path.exists(design_path):
        raise FileNotFoundError(f"Design spec '{safe_name}' not found.")
    with open(design_path, "r", encoding="utf-8") as f:
        return f.read()

def _yaml_block_values(content: str, block_name: str) -> dict:
    match = re.search(rf"(?m)^{re.escape(block_name)}:\s*\n(.*?)(?=\n[A-Za-z0-9_-]+:\s*\n|\n---|\Z)", content, re.S)
    if not match:
        return {}
    values = {}
    # Improved regex to allow # inside values and handle quotes better
    for key, value in re.findall(r"(?m)^  ([A-Za-z0-9_.-]+):\s*[\"']?([^\"'\n]+)[\"']?", match.group(1)):
        # Remove trailing comments if any
        clean_value = value.split(" #")[0].strip()
        values[key.strip()] = clean_value
    return values

def _first_token_value(mapping: dict, keys: list[str], default: str | None = None) -> str | None:
    for key in keys:
        if mapping.get(key):
            return mapping[key]
    return default

def _normalize_radius(value: str | None, default: str = "8") -> str:
    if not value:
        return default
    if value == "0":
        return "0"
    match = re.search(r"(\d+)", str(value))
    return match.group(1) if match else default

def _yaml_block_objects(content: str, block_name: str) -> dict:
    """Parses a YAML-like block into a nested dictionary (2 levels)."""
    match = re.search(rf"(?m)^{re.escape(block_name)}:\s*\n(.*?)(?=\n[A-Za-z0-9_-]+:\s*\n|\n---|\Z)", content, re.S)
    if not match:
        return {}
    block_content = match.group(1)
    result = {}
    current_key = None
    for line in block_content.splitlines():
        if line.startswith("  ") and not line.startswith("    "):
            key_match = re.match(r"  ([A-Za-z0-9_.-]+):\s*(.*)", line)
            if key_match:
                current_key = key_match.group(1).strip()
                val = key_match.group(2).strip().strip("\"'")
                if val:
                    result[current_key] = val
                else:
                    result[current_key] = {}
        elif line.startswith("    ") and current_key and isinstance(result[current_key], dict):
            val_match = re.match(r"    ([A-Za-z0-9_.-]+):\s*[\"']?([^\"'\n]+)[\"']?", line)
            if val_match:
                result[current_key][val_match.group(1).strip()] = val_match.group(2).strip()
    return result

def _parse_prose_colors(content: str) -> dict:
    """Fallback: extract colors from Markdown table rows or inline bold/backtick format."""
    _ROLE_MAP = {
        "primary": "primary", "accent": "primary", "brand": "primary",
        "secondary": "secondary", "brand-secondary": "secondary",
        "background": "canvas", "bg": "canvas", "canvas": "canvas",
        "surface": "surface-card", "card": "surface-card",
        "border": "border",
        "text base": "ink", "text-base": "ink", "text color": "ink", "foreground": "ink", "base text": "ink",
        "text muted": "muted", "muted": "muted", "secondary text": "muted",
        "success": "success", "error": "error", "danger": "error",
        "warning": "warning", "caution": "warning",
    }
    colors: dict = {}
    # Format 1: Markdown table rows | Role | #hex |
    for row in re.finditer(r'\|\s*([^|]+?)\s*\|\s*(#[0-9a-fA-F]{3,8})\s*\|', content):
        role = row.group(1).strip().lower()
        hex_val = row.group(2).strip()
        for pattern, key in _ROLE_MAP.items():
            if pattern in role and key not in colors:
                colors[key] = hex_val
                break
    # Format 2: **Name** (`#hex`): description OR **Name** (#hex): description
    for m in re.finditer(r'\*\*([^*]+)\*\*\s*[(`]+(#[0-9a-fA-F]{3,8})[)`]+\s*:?\s*([^\n]*)', content):
        name = m.group(1).strip().lower(); hex_val = m.group(2); desc = m.group(3).lower()
        combined = name + " " + desc
        for pattern, key in _ROLE_MAP.items():
            if pattern in combined and key not in colors:
                colors[key] = hex_val; break
    # Format 3: prose sentences — hex values near role keywords
    if "primary" not in colors:
        for kw in ("primary", "accent", "brand accent", "cta"):
            m = re.search(rf'(?i)\b{re.escape(kw)}\b[^.#\n]{{0,60}}(#[0-9a-fA-F]{{6}})', content)
            if m: colors["primary"] = m.group(1); break
    if "canvas" not in colors:
        for kw in ("background", "canvas", "page background", "body background"):
            m = re.search(rf'(?i)\b{re.escape(kw)}\b[^.#\n]{{0,60}}(#[0-9a-fA-F]{{6}})', content)
            if m: colors["canvas"] = m.group(1); break
    return colors


def _parse_prose_radius(content: str) -> dict:
    """Fallback: extract radius values from lines like 'Radius: 8px' or 'border-radius: 12px'"""
    rounded: dict = {}
    for m in re.finditer(r'(?i)radius[:\s]+(\d+)px', content):
        px = int(m.group(1))
        if "DEFAULT" not in rounded:
            rounded["DEFAULT"] = f"{px}px"
            rounded["md"] = f"{px}px"
    # Check for card/button specific radius in context
    card_m = re.search(r'(?i)(?:card[^.]*|container[^.]*)\s*\n[^.]*radius[:\s]+(\d+)px', content)
    if card_m and "lg" not in rounded:
        rounded["lg"] = f"{card_m.group(1)}px"
    return rounded


def _parse_design_md_to_tokens(content: str) -> dict:
    tokens = {}
    colors = _yaml_block_values(content, "colors")
    typography_objs = _yaml_block_objects(content, "typography")
    rounded = _yaml_block_values(content, "rounded")
    spacing = _yaml_block_values(content, "spacing")
    shadows = _yaml_block_values(content, "shadows") or _yaml_block_values(content, "elevation")

    # ── Fallback: prose/table format specs (e.g. ecommerce.md, minimal.md) ──
    if not colors:
        colors = _parse_prose_colors(content)
    if not rounded:
        rounded = _parse_prose_radius(content)

    # ── Base Colors ──────────────────────────────────────────────────────────
    primary = _first_token_value(colors, ["primary", "accent", "accent-blue", "text-link", "product-terraform"], "#2563eb")
    canvas = _first_token_value(colors, ["canvas", "background", "page", "canvas-soft"], "#f9fafb")
    surface = _first_token_value(colors, ["surface-card", "surface-1", "surface", "canvas", "surface-soft-light"], "#ffffff")
    surface_2 = _first_token_value(colors, ["surface-2", "surface-tile-1", "surface-pearl"], surface)
    surface_3 = _first_token_value(colors, ["surface-3", "surface-strong", "surface-tile-2"], surface_2)
    border = _first_token_value(colors, ["hairline", "hairline-strong", "border", "surface-3", "border-subtle"], "#e5e7eb")
    border_strong = _first_token_value(colors, ["border-strong", "hairline-strong", "border-emphasis"], border)
    text = _first_token_value(colors, ["ink", "body-strong", "text", "body", "foreground"], "#111827")
    text_muted = _first_token_value(colors, ["muted", "body", "text-secondary", "foreground-muted", "muted-soft"], "#6b7280")
    text_subtle = _first_token_value(colors, ["muted-soft", "text-tertiary", "foreground-subtle", "placeholder"], "#9ca3af")

    # ── Semantic Colors ───────────────────────────────────────────────────────
    color_success = _first_token_value(colors, ["success", "positive", "green", "status-success"], "#16a34a")
    color_error = _first_token_value(colors, ["error", "danger", "negative", "destructive", "status-error"], "#dc2626")
    color_warning = _first_token_value(colors, ["warning", "caution", "status-warning"], "#d97706")
    color_info = _first_token_value(colors, ["info", "informational", "status-info"], primary)
    color_secondary = _first_token_value(colors, ["secondary", "accent-2", "brand-secondary", "plus", "luxe"], primary)

    tokens["accent.hex"] = primary
    tokens["color.secondary.hex"] = color_secondary
    tokens["color.success.hex"] = color_success
    tokens["color.error.hex"] = color_error
    tokens["color.warning.hex"] = color_warning
    tokens["color.info.hex"] = color_info
    tokens["page.body.bg_hex"] = canvas
    tokens["region.main.bg_hex"] = surface
    tokens["region.main.bg_elevated_hex"] = surface_2
    tokens["region.main.bg_sunken_hex"] = surface_3
    tokens["region.border_hex"] = border
    tokens["region.border_strong_hex"] = border_strong
    tokens["page.body.text_hex"] = text
    tokens["color.text.muted_hex"] = text_muted
    tokens["color.text.subtle_hex"] = text_subtle

    # ── Typography ────────────────────────────────────────────────────────────
    for scale in ["hero", "display", "display-xl", "display-lg", "display-md", "lead", "title-md", "title-sm", "body", "body-md", "body-sm", "caption", "caption-sm", "label"]:
        obj = typography_objs.get(scale) or typography_objs.get(scale.replace("-", "_"))
        if isinstance(obj, dict):
            prefix = f"typography.{scale}"
            if obj.get("fontSize"): tokens[f"{prefix}.size"] = obj["fontSize"]
            if obj.get("fontWeight"): tokens[f"{prefix}.weight"] = obj["fontWeight"]
            if obj.get("lineHeight"): tokens[f"{prefix}.line_height"] = obj["lineHeight"]
            if obj.get("letterSpacing"): tokens[f"{prefix}.letter_spacing"] = obj["letterSpacing"]
            if obj.get("fontFamily"): tokens[f"{prefix}.family"] = obj["fontFamily"].split(",")[0].strip().strip("\"'")

    # ── Font ──────────────────────────────────────────────────────────────────
    font_match = (
        re.search(r"fontFamily:\s*[\"']*([A-Za-z][^\"',\n]+)", content)
        or re.search(r'Font Family:\s*[\"\']*([A-Za-z][^\"\'\\n,]+)', content)
    )
    if font_match:
        raw_font = font_match.group(1).split(',')[0].strip().strip("'\" ")
        if raw_font and len(raw_font) > 1:
            tokens["page.font.family"] = raw_font
    if "page.font.family" not in tokens:
        for scale_key in ("typography.body.family", "typography.body-md.family", "typography.display.family"):
            if scale_key in tokens:
                tokens["page.font.family"] = tokens[scale_key]
                break

    # ── Radius ────────────────────────────────────────────────────────────────
    radius_md = _normalize_radius(_first_token_value(rounded, ["md", "lg", "sm", "DEFAULT"], "8"))
    radius_sm = _normalize_radius(_first_token_value(rounded, ["sm", "xs", "DEFAULT"], str(max(0, int(radius_md) - 4))))
    radius_lg = _normalize_radius(_first_token_value(rounded, ["lg", "xl", "2xl"], str(int(radius_md) + 4)))
    radius_full = _normalize_radius(_first_token_value(rounded, ["full", "pill"], "9999"))
    tokens["page.radius.px"] = radius_md
    tokens["radius.sm.px"] = radius_sm
    tokens["radius.lg.px"] = radius_lg
    tokens["radius.full.px"] = radius_full

    # ── Shadows ───────────────────────────────────────────────────────────────
    shadow_sm = _first_token_value(shadows, ["sm", "1", "level-1", "low"], "0 1px 2px 0 rgb(0 0 0 / 0.05)")
    shadow_md = _first_token_value(shadows, ["md", "2", "level-2", "medium", "DEFAULT"], "0 4px 6px -1px rgb(0 0 0 / 0.10)")
    shadow_lg = _first_token_value(shadows, ["lg", "3", "level-3", "high"], "0 10px 15px -3px rgb(0 0 0 / 0.10)")
    tokens["shadow.sm"] = shadow_sm
    tokens["shadow.md"] = shadow_md
    tokens["shadow.lg"] = shadow_lg

    # ── Spacing ───────────────────────────────────────────────────────────────
    tokens["spacing.xs"] = _first_token_value(spacing, ["xs", "1", "4"], "4px")
    tokens["spacing.sm"] = _first_token_value(spacing, ["sm", "2", "8"], "8px")
    tokens["spacing.md"] = _first_token_value(spacing, ["md", "4", "16"], "16px")
    tokens["spacing.lg"] = _first_token_value(spacing, ["lg", "6", "24"], "24px")
    tokens["spacing.xl"] = _first_token_value(spacing, ["xl", "8", "32"], "32px")

    # ── Theme Hints ───────────────────────────────────────────────────────────
    tokens.setdefault("brand.name", "App")
    tokens.setdefault("theme.button.style", "solid")
    is_light_bg = tokens.get("page.body.bg_hex", "#ffffff").lower() in {"#ffffff", "#fafafa", "#f9fafb", "#f8f9fa"}
    tokens.setdefault("theme.card.hover", "lift" if is_light_bg else "border")
    tokens.setdefault("theme.image.ratio", "4/3")
    tokens.setdefault("theme.divider", "line")

    _expand_design_tokens(tokens)
    return tokens

def _expand_design_tokens(tokens: dict) -> dict:
    """Derive stable page/region/component/button tokens from the base palette."""
    accent = tokens.get("accent.hex", "#2563eb")
    secondary = tokens.get("color.secondary.hex", accent)
    page_bg = tokens.get("page.body.bg_hex", "#f9fafb")
    surface = tokens.get("region.main.bg_hex") or tokens.get("component.card.bg_hex", "#ffffff")
    surface_2 = tokens.get("region.main.bg_elevated_hex", surface)
    surface_3 = tokens.get("region.main.bg_sunken_hex", page_bg)
    text = tokens.get("page.body.text_hex", "#111827")
    text_muted = tokens.get("color.text.muted_hex", "#6b7280")
    text_subtle = tokens.get("color.text.subtle_hex", "#9ca3af")
    border = tokens.get("region.border_hex", "#e5e7eb")
    border_strong = tokens.get("region.border_strong_hex", border)
    radius = tokens.get("page.radius.px", "8")
    shadow_sm = tokens.get("shadow.sm", "0 1px 2px 0 rgb(0 0 0 / 0.05)")
    shadow_md = tokens.get("shadow.md", "0 4px 6px -1px rgb(0 0 0 / 0.10)")
    shadow_lg = tokens.get("shadow.lg", "0 10px 15px -3px rgb(0 0 0 / 0.10)")
    color_success = tokens.get("color.success.hex", "#16a34a")
    color_error = tokens.get("color.error.hex", "#dc2626")
    color_warning = tokens.get("color.warning.hex", "#d97706")

    tokens.setdefault("page.bg.hex", page_bg)
    tokens.setdefault("page.text.hex", text)
    tokens["page.body.bg"] = f"bg-[{page_bg}]"
    tokens["page.body.text"] = f"text-[{text}]"
    tokens.setdefault("region.header.bg_hex", accent)
    tokens.setdefault("region.header.bg", f"bg-[{accent}]")
    tokens.setdefault("region.header.text_hex", "#ffffff")
    tokens.setdefault("page.header.text", "text-white")
    tokens.setdefault("region.main.bg_hex", surface)
    tokens.setdefault("region.sidebar.bg_hex", surface)
    tokens.setdefault("region.footer.bg_hex", page_bg)
    tokens.setdefault("region.footer.text_hex", text)
    tokens.setdefault("region.border_hex", border)

    # Surface levels (for card elevation hierarchy)
    tokens.setdefault("surface.1.hex", surface)
    tokens.setdefault("surface.2.hex", surface_2)
    tokens.setdefault("surface.3.hex", surface_3)

    # Text hierarchy
    tokens.setdefault("text.primary.hex", text)
    tokens.setdefault("text.muted.hex", text_muted)
    tokens.setdefault("text.subtle.hex", text_subtle)

    # Border hierarchy
    tokens.setdefault("border.default.hex", border)
    tokens.setdefault("border.strong.hex", border_strong)

    # Shadows
    tokens.setdefault("component.card.bg_hex", surface)
    tokens["component.card.bg"] = f"bg-[{surface}]"
    tokens.setdefault("component.card.border_hex", border)
    tokens.setdefault("component.card.shadow", shadow_sm)
    tokens.setdefault("component.card.shadow.hover", shadow_md)
    for layout in ("form", "table", "list", "detail", "filter", "workflow"):
        tokens.setdefault(f"component.{layout}.bg_hex", surface)
        tokens.setdefault(f"component.{layout}.border_hex", border)

    # Semantic badge colors
    tokens.setdefault("badge.success.bg_hex", color_success)
    tokens.setdefault("badge.success.text_hex", "#ffffff")
    tokens.setdefault("badge.error.bg_hex", color_error)
    tokens.setdefault("badge.error.text_hex", "#ffffff")
    tokens.setdefault("badge.warning.bg_hex", color_warning)
    tokens.setdefault("badge.warning.text_hex", "#ffffff")
    tokens.setdefault("badge.info.bg_hex", accent)
    tokens.setdefault("badge.info.text_hex", "#ffffff")
    tokens.setdefault("badge.neutral.bg_hex", surface_3)
    tokens.setdefault("badge.neutral.text_hex", text_muted)
    tokens.setdefault("component.badge.bg_hex", surface_3)
    tokens.setdefault("component.badge.text_hex", text_muted)

    # Buttons
    tokens.setdefault("button.primary.bg_hex", accent)
    tokens.setdefault("button.primary.text_hex", "#ffffff")
    tokens.setdefault("button.primary.border_hex", accent)
    tokens.setdefault("button.secondary.bg_hex", surface)
    tokens.setdefault("button.secondary.text_hex", text)
    tokens.setdefault("button.secondary.border_hex", border_strong)
    tokens.setdefault("button.ghost.text_hex", accent)
    tokens.setdefault("button.ghost.hover_bg_hex", surface_3)
    tokens.setdefault("button.danger.bg_hex", color_error)
    tokens.setdefault("button.danger.text_hex", "#ffffff")
    tokens.setdefault("button.danger.border_hex", color_error)
    tokens.setdefault("button.link.text_hex", accent)
    tokens.setdefault("button.radius.px", radius)

    # Inputs
    tokens.setdefault("input.bg_hex", surface)
    tokens.setdefault("input.border_hex", border)
    tokens.setdefault("input.border_focus_hex", accent)
    tokens.setdefault("input.text_hex", text)
    tokens.setdefault("input.placeholder_hex", text_subtle)
    tokens.setdefault("input.radius.px", radius)

    # Table
    tokens.setdefault("table.header.bg_hex", surface_3)
    tokens.setdefault("table.header.text_hex", text_muted)
    tokens.setdefault("table.row.hover_hex", surface_3)
    tokens.setdefault("table.border_hex", border)

    # Nav
    tokens.setdefault("nav.bg_hex", accent)
    tokens.setdefault("nav.text_hex", "#ffffff")
    tokens.setdefault("nav.border_hex", border)

    # Secondary accent
    tokens.setdefault("color.secondary.hex", secondary)
    tokens.setdefault("button.secondary.accent_hex", secondary)

    # Shadow levels
    tokens.setdefault("shadow.sm", shadow_sm)
    tokens.setdefault("shadow.md", shadow_md)
    tokens.setdefault("shadow.lg", shadow_lg)
    tokens.setdefault("--button-primary-bg", f"var(--accent)")
    tokens.setdefault("--button-primary-text", "#ffffff")
    return tokens

def list_design_specs_tool_func() -> str:
    """Lists all available design specification templates (e.g. ecommerce.md, minimal.md)."""
    return json.dumps(_design_spec_files())

def get_design_system_tool_func(spec_name: str = "minimal.md") -> str:
    """
    Reads a specific DESIGN specification from the library and returns the tokens.
    Use list_design_specs_tool to see available options.
    """
    try:
        safe_name = os.path.basename(spec_name)
        content = _read_design_spec(safe_name)
        tokens = _parse_design_md_to_tokens(content)
        return json.dumps({"spec_name": safe_name, "tokens": tokens, "raw_design_doc": content}, indent=2)
    except Exception as exc:
        return f"Error: {exc}"

def apply_design_system_to_interface_tool_func(interface_id: str, spec_name: str = "minimal.md") -> str:
    """
    Updates the specified Interface with design tokens from a template in the library.
    Ideal for quickly switching between themes (e.g. switching to ecommerce.md).
    """
    try:
        safe_name = os.path.basename(spec_name)
        content = _read_design_spec(safe_name)
        tokens = _parse_design_md_to_tokens(content)
        tokens["design.spec_name"] = safe_name
    except Exception as exc:
        return f"Error: {exc}"
    patch_resp = requests.patch(
        f"{METADATA_API_BASE}/interfaces/{interface_id}/data/",
        json={"tokens": tokens, "design_spec": safe_name},
        headers=_AUTH_HEADERS
    )
    if patch_resp.status_code == 200:
        return f"Successfully applied '{safe_name}' tokens to interface {interface_id}."
    else:
        return f"Failed to update interface data: {patch_resp.text}"

def _collect_domain_terms(interface_id: str) -> tuple[list[str], dict]:
    iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS)
    iface_resp.raise_for_status()
    iface = iface_resp.json()
    system_id = iface.get("system")
    system_ctx = _fetch_system_context_data(system_id) if system_id else {}
    data = iface.get("data") or {}
    terms = [
        iface.get("name", ""),
        iface.get("description", ""),
        str(iface.get("actor_name") or iface.get("actor") or ""),
    ]
    for page in data.get("pages") or []:
        terms.extend([page.get("name", ""), str(page.get("primary_model") or "")])
    for section in data.get("sections") or []:
        terms.extend([section.get("name", ""), str(section.get("primary_model") or ""), str(section.get("layout") or "")])
    for classifier in _as_list(system_ctx.get("classifiers"), "classifiers"):
        cdata = classifier.get("data") or {}
        terms.extend([cdata.get("name", ""), cdata.get("type", "")])
        for attr in cdata.get("attributes") or []:
            terms.append(attr.get("name", ""))
    for diagram in system_ctx.get("activity_diagrams") or []:
        terms.append(diagram.get("name", ""))
        for node in diagram.get("nodes") or []:
            terms.append(((node.get("cls") or {}).get("name") or ""))
    return [str(term).lower() for term in terms if term], {"interface": iface, "system": system_ctx}

def _domain_scores(terms: list[str]) -> dict:
    text = " ".join(terms)
    scores = {domain: 0 for domain in _DOMAIN_KEYWORDS}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            scores[domain] += len(re.findall(rf"\b{re.escape(keyword.lower())}\b", text))
    return scores

def _pick_design_specs_for_terms(terms: list[str], count: int = 3) -> list[str]:
    available = _design_spec_files()
    if not available:
        return []
    available_set = set(available)
    scores = _domain_scores(terms)
    ranked_domains = sorted(scores, key=lambda d: scores[d], reverse=True)
    selected = []
    for domain in ranked_domains:
        for spec in _DESIGN_DOMAIN_PRIORITIES.get(domain, []):
            if spec in available_set and spec not in selected:
                selected.append(spec)
                if len(selected) >= count:
                    return selected
    for fallback in ("minimal.md", "notion.md", "apple.md"):
        if fallback in available_set and fallback not in selected:
            selected.append(fallback)
            if len(selected) >= count:
                return selected
    for spec in available:
        if spec not in selected:
            selected.append(spec)
            if len(selected) >= count:
                break
    return selected

def _tokens_for_design_spec(spec_name: str, brand_name: str = "App") -> dict:
    safe_name = os.path.basename(spec_name)
    tokens = _parse_design_md_to_tokens(_read_design_spec(safe_name))
    tokens["brand.name"] = brand_name or "App"
    tokens["design.spec_name"] = safe_name
    return tokens

def _candidate_design_spec(interface_id: str, candidate_index: int = 0, prompt: str = "") -> tuple[str | None, dict]:
    terms, context = _collect_domain_terms(interface_id)
    if prompt:
        terms.extend(re.findall(r"\w+", prompt.lower()))
    selected = _pick_design_specs_for_terms(terms, max(3, int(candidate_index) + 1))
    if not selected:
        return None, {}
    spec_name = selected[int(candidate_index) % len(selected)]
    iface = context.get("interface") or {}
    return spec_name, _tokens_for_design_spec(spec_name, iface.get("name") or "App")

def select_design_specs_for_interface_func(interface_id: str, count: int = 3, prompt: str = "") -> str:
    """Deterministically maps interface/system metadata and designer prompt to design specs and resolved tokens."""
    try:
        terms, context = _collect_domain_terms(interface_id)
        if prompt:
            terms.extend(re.findall(r"\w+", prompt.lower()))
        specs = _pick_design_specs_for_terms(terms, max(1, min(int(count or 3), 6)))
        iface = context.get("interface") or {}
        scores = _domain_scores(terms)
        result = []
        for spec in specs:
            result.append({"spec_name": spec, "tokens": _tokens_for_design_spec(spec, iface.get("name") or "App")})
        return json.dumps({"domain_scores": scores, "selected": result}, indent=2)
    except Exception as exc:
        return f"Error selecting design specs: {exc}"

def _build_activity_diagrams(system_data: dict) -> list:
    diagrams = system_data.get("diagrams") or []
    classifiers = {str(c.get("id")): c for c in _as_list(system_data.get("classifiers"), "classifiers")}
    relations = {str(r.get("id")): r for r in _as_list(system_data.get("relations"), "relations")}
    out = []
    for diagram in diagrams:
        if diagram.get("type") != "activity": continue
        raw_nodes = diagram.get("nodes") or []; raw_edges = diagram.get("edges") or []; nodes = []; node_by_cls = {}
        for node in raw_nodes:
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or ""); classifier = classifiers.get(cls_id, {}); nodes.append({"id": str(node.get("id")), "cls_ptr": cls_id, "cls": classifier.get("data", {}), "data": node.get("data", {})})
            if cls_id: node_by_cls[cls_id] = str(node.get("id"))
        edges = []
        for edge in raw_edges:
            rel_id = str(edge.get("rel") or edge.get("rel_id") or edge.get("rel_ptr") or ""); relation = relations.get(rel_id, {}); source_cls = str(relation.get("source") or relation.get("source_id") or ""); target_cls = str(relation.get("target") or relation.get("target_id") or ""); source_ptr = node_by_cls.get(source_cls); target_ptr = node_by_cls.get(target_cls)
            if not source_ptr or not target_ptr: continue
            edges.append({"id": str(edge.get("id")), "source_ptr": source_ptr, "target_ptr": target_ptr, "rel_ptr": rel_id, "rel": relation.get("data", {}), "data": edge.get("data", {})})
        out.append({"id": str(diagram.get("id")), "name": diagram.get("name", ""), "type": "activity", "nodes": nodes, "edges": edges})
    return out

def _actor_refs(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> set[str]:
    refs = {str(actor_id)} if actor_id else set()
    actor_name_norm = str(actor_name or "").lower()
    classifiers = {
        str(c.get("id")): c.get("data", {})
        for c in _as_list(system_data.get("classifiers"), "classifiers")
    }
    for diagram in system_data.get("diagrams", []):
        if diagram.get("type") != "usecase":
            continue
        for node in diagram.get("nodes", []):
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or "")
            cls = classifiers.get(cls_id, {})
            if cls.get("type") == "actor" and (
                cls_id == str(actor_id)
                or str(cls.get("name", "")).lower() == actor_name_norm
            ):
                refs.add(str(node.get("id")))
                refs.add(cls_id)
    return {ref for ref in refs if ref and ref != "None"}

def _ref_values(values) -> set[str]:
    out = set()
    for value in values or []:
        if isinstance(value, dict):
            ref = value.get("id") or value.get("value") or value.get("classifier") or value.get("node")
        else:
            ref = value
        if ref:
            out.add(str(ref))
    return out

def _ref_list(values) -> list[str]:
    out = []
    seen = set()
    for value in values or []:
        if isinstance(value, dict):
            ref = value.get("id") or value.get("value") or value.get("classifier") or value.get("node")
        else:
            ref = value
        if ref and str(ref) not in seen:
            out.append(str(ref))
            seen.add(str(ref))
    return out

def _infer_usecase_model(name: str, explicit_classes: list[str], classifiers: dict[str, dict], model_names: set[str]) -> str:
    for ref in explicit_classes:
        cls = classifiers.get(ref, {})
        cname = cls.get("name") or ref
        if cname in model_names:
            return cname
    name_l = str(name or "").lower()
    hints = [
        (("review",), "Review"),
        (("cart",), "Cart"),
        (("order", "purchase", "checkout", "confirmation"), "Order"),
        (("payment",), "Payment"),
        (("account", "customer", "profile"), "Customer"),
        (("product", "catalog", "listing", "search", "browse"), "Product"),
        (("seller",), "Seller"),
        (("inventory", "stock"), "Product"),
    ]
    for terms, model in hints:
        if any(term in name_l for term in terms) and model in model_names:
            return model
    for model in sorted(model_names, key=len, reverse=True):
        if model.lower() in name_l:
            return model
    return ""

def _humanize_action_label(name: str, fallback: str = "Start") -> str:
    raw = re.sub(r"[_-]+", " ", str(name or "")).strip()
    if not raw:
        return fallback
    cleaned = re.sub(r"^(manage|view|track|write|browse|search|review)\s+", "", raw, flags=re.I).strip()
    if re.search(r"\b(purchase|checkout|cart)\b", raw, re.I):
        return "Checkout"
    if re.search(r"\b(apply|application|request|submit|onboard|register|book|schedule|reserve|purchase|checkout|payment|approval|claim|ticket|case|workflow|process)\b", raw, re.I):
        return "Start"
    return cleaned[:1].upper() + cleaned[1:] if cleaned else fallback

def _is_child_collection_model(model_name: str, page_terms: str = "") -> bool:
    name_l = str(model_name or "").lower()
    terms_l = str(page_terms or "").lower()
    if not name_l:
        return False
    if any(term in name_l for term in ("item", "line", "entry", "row", "detail", "selection")):
        return True
    if any(term in terms_l for term in ("cart", "basket", "checkout", "quote", "order", "request", "application")) and any(term in name_l for term in ("product", "service", "option")):
        return True
    return False

def _plural_page_id(model: str) -> str:
    base = _section_id(model or "items")
    if base.endswith("y"):
        return f"{base[:-1]}ies"
    if base.endswith("s"):
        return base
    return f"{base}s"

def _ooui_mapping_for_usecase(usecase: dict, workflow_entry: bool = False) -> dict:
    name = str(usecase.get("name") or "")
    name_l = name.lower()
    primary = usecase.get("primary_model") or ""
    class_names = [m for m in usecase.get("class_names") or [] if m]

    def first_model(*terms: str) -> str:
        return next((m for m in class_names if any(term in m.lower() for term in terms)), "")

    if any(term in name_l for term in ("process payment", "send confirmation", "system process", "background")):
        return {"role": "background", "page_id": "", "page_name": "", "page_model": primary, "operation_kind": "background"}

    if workflow_entry:
        page_model = first_model("cart") or primary
        page_id = "cart" if page_model.lower() == "cart" else _section_id(page_model or name)
        return {
            "role": "workflow_entry",
            "page_id": page_id,
            "page_name": _page_name(page_id),
            "page_model": page_model,
            "operation_kind": "start_workflow",
        }

    inline_terms = ("add", "remove", "delete", "update", "select", "write", "review", "rate")
    if any(term in name_l for term in inline_terms) and "manage" not in name_l:
        if "cart" in name_l and "product" in name_l:
            page_model = first_model("product") or primary
            target_model = first_model("cartitem", "cart item", "item", "line") or first_model("cart") or primary
            return {
                "role": "inline_operation",
                "page_id": f"{_section_id(page_model)}_catalog" if page_model else "",
                "page_name": _page_name(f"{_section_id(page_model)}_catalog") if page_model else "",
                "page_model": page_model,
                "operation_kind": "create_related",
                "target_model": target_model,
            }
        if "review" in name_l or "write" in name_l:
            page_model = first_model("product") or first_model("order") or primary
            target_model = first_model("review") or primary
            return {
                "role": "inline_operation",
                "page_id": f"{_section_id(page_model)}_detail" if page_model else "",
                "page_name": _page_name(f"{_section_id(page_model)}_detail") if page_model else "",
                "page_model": page_model,
                "operation_kind": "create_related" if target_model != page_model else "update",
                "target_model": target_model,
            }
        return {
            "role": "inline_operation",
            "page_id": _section_id(primary or name),
            "page_name": _page_name(primary or name),
            "page_model": primary,
            "operation_kind": "object_operation",
        }

    if any(term in name_l for term in ("browse", "search", "catalog", "list")):
        page_model = first_model("product") or primary
        page_id = f"{_section_id(page_model)}_catalog" if page_model else _section_id(name)
        return {"role": "collection_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_collection"}

    if "detail" in name_l or name_l.startswith("view "):
        page_model = first_model("product") or primary
        page_id = f"{_section_id(page_model)}_detail" if page_model else _section_id(name)
        return {"role": "detail_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_detail"}

    if "track" in name_l or "order" in name_l:
        page_model = first_model("order") or primary
        page_id = _plural_page_id(page_model) if page_model else _section_id(name)
        return {"role": "collection_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_collection"}

    if any(term in name_l for term in ("account", "profile", "settings")):
        page_model = first_model("customer", "user", "account") or primary
        page_id = "account"
        return {"role": "object_workspace", "page_id": page_id, "page_name": "Account", "page_model": page_model, "operation_kind": "manage_object"}

    page_id = _section_id(primary or name)
    return {"role": "object_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": primary, "operation_kind": "manage_object"}

def _activity_action_indexes(system_data: dict) -> tuple[dict[str, dict], set[str], set[str]]:
    by_id = {}
    first_ids = set()
    all_ids = set()
    for diagram in system_data.get("activity_diagrams") or []:
        incoming = {}
        outgoing = {}
        action_ids = set()
        for node in diagram.get("nodes") or []:
            cls = node.get("cls") or {}
            if cls.get("type") == "action":
                nid = str(node.get("id"))
                cid = str(node.get("cls_ptr") or "")
                action_ids.add(nid)
                all_ids.update({nid, cid})
                by_id[nid] = {"node_id": nid, "classifier_id": cid, "name": cls.get("name", ""), "diagram_id": diagram.get("id"), "diagram_name": diagram.get("name", "")}
                if cid:
                    by_id[cid] = by_id[nid]
        for edge in diagram.get("edges") or []:
            source = str(edge.get("source_ptr") or "")
            target = str(edge.get("target_ptr") or "")
            if source and target:
                incoming.setdefault(target, []).append(source)
                outgoing.setdefault(source, []).append(target)
        for aid in action_ids:
            source_nodes = incoming.get(aid, [])
            if not source_nodes or any(((next((n for n in diagram.get("nodes") or [] if str(n.get("id")) == src), {}).get("cls") or {}).get("type") == "initial") for src in source_nodes):
                first_ids.add(aid)
                cls_id = by_id.get(aid, {}).get("classifier_id")
                if cls_id:
                    first_ids.add(cls_id)
    return by_id, first_ids, all_ids

def _usecase_has_workflow_entry(usecase: dict, has_activity_workflow: bool, activity_first_ids: set[str], activity_all_ids: set[str]) -> bool:
    if not has_activity_workflow:
        return False
    refs = set(usecase.get("activities") or []) | set(usecase.get("actions") or [])
    if refs:
        return bool(refs & (activity_first_ids or activity_all_ids))
    name_l = usecase.get("name", "").lower()
    passive_terms = {"browse", "search", "view", "track", "receive", "manage account", "settings", "profile", "history", "status"}
    if any(term in name_l for term in passive_terms):
        return False
    intent_terms = {
        "apply", "application", "request", "submit", "purchase", "checkout", "book", "schedule",
        "reserve", "register", "onboard", "approve", "approval", "claim", "ticket", "case",
        "payment", "process", "workflow"
    }
    if any(term in name_l for term in intent_terms):
        return True
    return False

def _infer_usecase_permissions(name: str) -> list[str]:
    name_l = str(name or "").lower()
    perms = {"view"}
    if any(term in name_l for term in ("add", "create", "write", "purchase", "checkout", "place", "submit")):
        perms.add("create")
    if any(term in name_l for term in ("manage", "update", "edit", "select", "enter", "process", "confirm", "track")):
        perms.add("update")
    if "manage" in name_l and not any(term in name_l for term in ("account", "profile", "settings", "password")):
        if any(term in name_l for term in ("listing", "listings", "catalog", "inventory", "product", "products", "item", "items", "record", "records")):
            perms.update({"create", "delete"})
    if any(term in name_l for term in ("delete", "remove", "cancel")):
        perms.add("delete")
    return [p for p in ("view", "create", "update", "delete") if p in perms]

def _build_usecase_navigation(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> dict:
    refs = _actor_refs(system_data, actor_id, actor_name)
    classifiers = {
        str(c.get("id")): (c.get("data") or {})
        for c in _as_list(system_data.get("classifiers"), "classifiers")
    }
    model_names = {
        cdata.get("name")
        for cdata in classifiers.values()
        if cdata.get("name") and cdata.get("type") in {"class", "entity", "model"}
    }
    model_attrs = {
        cdata.get("name"): {a.get("name") for a in cdata.get("attributes", []) if a.get("name")}
        for cdata in classifiers.values()
        if cdata.get("name") and cdata.get("type") in {"class", "entity", "model"}
    }
    relations = {str(r.get("id")): r for r in _as_list(system_data.get("relations"), "relations")}
    usecases = {}
    includes = {}
    for diagram in system_data.get("diagrams", []):
        if diagram.get("type") != "usecase":
            continue
        node_by_cls = {}
        for node in diagram.get("nodes", []):
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or "")
            if cls_id:
                node_by_cls[cls_id] = str(node.get("id"))
        for edge in diagram.get("edges", []):
            rel_id = str(edge.get("rel") or edge.get("rel_id") or edge.get("rel_ptr") or "")
            rel = relations.get(rel_id, {})
            rdata = rel.get("data") or {}
            source = str(rel.get("source") or rel.get("source_id") or "")
            target = str(rel.get("target") or rel.get("target_id") or "")
            if rdata.get("type") == "interaction":
                source_cls = classifiers.get(source, {})
                target_cls = classifiers.get(target, {})
                uc_id = ""
                if source in refs and target_cls.get("type") == "usecase":
                    uc_id = target
                elif target in refs and source_cls.get("type") == "usecase":
                    uc_id = source
                if uc_id and uc_id not in usecases:
                    uc = classifiers.get(uc_id, {})
                    explicit_classes = _ref_list(uc.get("classes"))
                    model = _infer_usecase_model(uc.get("name", ""), explicit_classes, classifiers, model_names)
                    page_id = _section_id(uc.get("name") or "usecase")
                    class_names = [
                        classifiers.get(cid, {}).get("name")
                        for cid in explicit_classes
                        if classifiers.get(cid, {}).get("name") in model_names
                    ]
                    page_terms = f"{uc.get('name', '')} {uc.get('trigger', '')} {uc.get('precondition', '')}"
                    usecases[uc_id] = {
                        "id": uc_id,
                        "node_id": node_by_cls.get(uc_id, ""),
                        "name": uc.get("name", ""),
                        "page_id": page_id,
                        "page_name": _page_name(uc.get("name") or page_id),
                        "primary_model": model,
                        "permissions": _infer_usecase_permissions(uc.get("name", "")),
                        "classes": explicit_classes,
                        "class_names": class_names,
                        "pre_workflow_collections": [m for m in class_names if m != model and _is_child_collection_model(m, page_terms)],
                        "activities": sorted(_ref_values(uc.get("activities"))),
                        "actions": sorted(_ref_values(uc.get("actions"))),
                        "trigger": uc.get("trigger", ""),
                        "precondition": uc.get("precondition", ""),
                        "postcondition": uc.get("postcondition", ""),
                    }
            elif rdata.get("type") in {"inclusion", "extension"}:
                includes.setdefault(source, []).append({"type": rdata.get("type"), "usecase_id": target, "name": classifiers.get(target, {}).get("name", "")})
    activity_by_id, activity_first_ids, activity_all_ids = _activity_action_indexes(system_data)
    has_activity_workflow = bool(system_data.get("activity_diagrams"))
    actor_permissions = {}
    for uc_id, uc in usecases.items():
        uc["related_usecases"] = includes.get(uc_id, [])
        has_workflow_entry = _usecase_has_workflow_entry(uc, has_activity_workflow, activity_first_ids, activity_all_ids)
        ui_mapping = _ooui_mapping_for_usecase(uc, has_workflow_entry)
        uc["ui_mapping"] = ui_mapping
        if ui_mapping.get("page_id"):
            uc["page_id"] = ui_mapping["page_id"]
            uc["page_name"] = ui_mapping.get("page_name") or _page_name(ui_mapping["page_id"])
        if ui_mapping.get("page_model"):
            uc["page_model"] = ui_mapping["page_model"]
        model = uc.get("primary_model")
        if model:
            current = set(actor_permissions.get(model, []))
            current.update(uc.get("permissions") or [])
            actor_permissions[model] = [p for p in ("view", "create", "update", "delete") if p in current]
        for related_model in uc.get("class_names") or []:
            if not related_model:
                continue
            current = set(actor_permissions.get(related_model, []))
            current.add("view")
            if _is_child_collection_model(related_model, f"{uc.get('name', '')} {uc.get('trigger', '')}"):
                current.update({"update", "delete"})
            actor_permissions[related_model] = [p for p in ("view", "create", "update", "delete") if p in current]
    page_entries = {}
    for uc in usecases.values():
        mapping = uc.get("ui_mapping") or {}
        page_id = mapping.get("page_id") or uc.get("page_id")
        if not page_id or mapping.get("role") == "background":
            continue
        current = page_entries.setdefault(page_id, {
            "page_id": page_id,
            "page_name": mapping.get("page_name") or uc.get("page_name") or _page_name(page_id),
            "primary_model": mapping.get("page_model") or uc.get("page_model") or uc.get("primary_model", ""),
            "roles": [],
            "usecases": [],
        })
        if mapping.get("role") and mapping["role"] not in current["roles"]:
            current["roles"].append(mapping["role"])
        current["usecases"].append(uc.get("name"))
    nav_pages = [
        entry["page_id"]
        for entry in page_entries.values()
        if any(role in entry["roles"] for role in ("collection_workspace", "object_workspace", "workflow_entry"))
    ]
    icon_actions = [pid for pid in nav_pages if any(term in pid for term in ("cart", "account", "order", "search"))]
    workflow_entry_points = []
    for uc in usecases.values():
        if _usecase_has_workflow_entry(uc, has_activity_workflow, activity_first_ids, activity_all_ids):
            refs = set(uc.get("activities") or []) | set(uc.get("actions") or [])
            linked_actions = [activity_by_id[ref] for ref in refs if ref in activity_by_id]
            first_linked = next((a for a in linked_actions if a.get("node_id") in activity_first_ids or a.get("classifier_id") in activity_first_ids), None)
            first_action = first_linked or (linked_actions[0] if linked_actions else None)
            label = _humanize_action_label(uc.get("name", ""), "Start")
            workflow_entry_points.append({
                "page_id": uc.get("page_id"),
                "page_name": uc.get("page_name"),
                "usecase_name": uc.get("name"),
                "section_layout": "activity_start",
                "label": label,
                "button_label": label,
                "primary_model": uc.get("primary_model", ""),
                "related_models": uc.get("class_names") or [],
                "pre_workflow_collections": uc.get("pre_workflow_collections") or [],
                "starts_activity_node_id": first_action.get("node_id") if first_action else "",
                "starts_activity_name": first_action.get("name") if first_action else "",
                "reason": "Starts the executable workflow for this use case; downstream activity pages stay gated by active_process_node_id.",
            })
    nav = {
        "actor_refs": sorted(refs),
        "usecases": list(usecases.values()),
        "pages": list(page_entries.values()),
        "nav_bar_pages": nav_pages,
        "icon_actions": icon_actions,
        "actor_permissions": actor_permissions,
        "workflow_entry_points": workflow_entry_points,
        "_note": "Use usecases for high-level pages, navigation entries, icon buttons, and actor permissions; use activity_diagrams/workflow_plan only for executable workflow tasks.",
    }
    nav["ooui_plan"] = build_ooui_plan_from_navigation(nav, model_attrs)
    return nav

def _workflow_plan(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> list:
    refs = _actor_refs(system_data, actor_id, actor_name)
    classifiers = {
        str(c.get("id")): (c.get("data") or {})
        for c in _as_list(system_data.get("classifiers"), "classifiers")
    }

    def _class_name(ref) -> str:
        if isinstance(ref, dict):
            ref = ref.get("id") or ref.get("value") or ref.get("name")
        ref = str(ref or "")
        return classifiers.get(ref, {}).get("name") or ref

    def _class_refs(raw_classes) -> list:
        if isinstance(raw_classes, dict):
            refs = []
            for values in raw_classes.values():
                refs.extend(values or [])
            return refs
        return list(raw_classes or [])

    steps = []
    for diagram in system_data.get("activity_diagrams", []):
        nodes = {str(n.get("id")): n for n in diagram.get("nodes", [])}
        outgoing = {}
        for edge in diagram.get("edges", []):
            outgoing.setdefault(str(edge.get("source_ptr")), []).append(str(edge.get("target_ptr")))
        for node in diagram.get("nodes", []):
            cls = node.get("cls", {})
            if cls.get("type") != "action":
                continue
            actor_node = str(cls.get("actorNode") or "")
            if refs and actor_node not in refs:
                continue
            name = cls.get("name") or "Workflow Step"
            page_name = _workflow_page_name(name)
            page_id = _section_id(page_name)
            next_action_ids = [
                target
                for target in outgoing.get(str(node.get("id")), [])
                if (nodes.get(target, {}).get("cls") or {}).get("type") == "action"
            ]
            steps.append({
                "activity_node_id": str(node.get("id")),
                "activity_node_name": name,
                "actor_node": actor_node,
                "classes": [_class_name(ref) for ref in _class_refs(cls.get("classes")) if _class_name(ref)],
                "diagram_id": diagram.get("id"),
                "diagram_name": diagram.get("name"),
                "page_id": page_id,
                "page_name": page_name,
                "next_activity_node_ids": next_action_ids,
            })
    return steps

def _activity_models_for_step(step: dict, workflow_entries: list, known_models: set[str]) -> list[str]:
    name_l = str(step.get("activity_node_name") or step.get("page_name") or "").lower()
    explicit_step_models = [m for m in step.get("classes") or [] if m in known_models]
    if explicit_step_models:
        if "confirmation" in name_l or "confirm" in name_l or "order" in name_l:
            return [
                m for m in [
                    next((model for model in explicit_step_models if any(term in model.lower() for term in ("orderline", "order line", "item", "line"))), ""),
                    next((model for model in explicit_step_models if model.lower() == "order" or "order" in model.lower()), ""),
                ]
                if m
            ] or explicit_step_models[:2]
        return explicit_step_models[:2]
    entries = [e for e in workflow_entries if not e.get("diagram_id") or e.get("diagram_id") == step.get("diagram_id")]
    related = []
    for entry in entries or workflow_entries:
        related.extend(entry.get("pre_workflow_collections") or [])
        related.extend(entry.get("related_models") or [])
        if entry.get("primary_model"):
            related.append(entry.get("primary_model"))
    related = [m for m in dict.fromkeys(related) if m in known_models]
    if not related:
        return []

    def first_matching(*terms: str) -> str:
        return next((m for m in related if any(term in m.lower() for term in terms)), "")

    if "cart" in name_l or "basket" in name_l:
        return [m for m in [first_matching("cartitem", "cart item", "item", "line"), first_matching("cart")] if m]
    if "shipping" in name_l or "address" in name_l:
        return [m for m in [first_matching("address")] if m]
    if "payment" in name_l or "method" in name_l:
        return [m for m in [first_matching("payment")] if m]
    if "confirmation" in name_l or "confirm" in name_l or "order" in name_l:
        return [m for m in [first_matching("orderline", "order line", "item", "line"), first_matching("order")] if m]
    explicit = [m for m in related if m.lower() in name_l]
    return explicit[:1] or related[:1]

def _activity_layout_for_step(step_name: str, model: str) -> str:
    name_l = str(step_name or "").lower()
    if any(term in name_l for term in ("enter", "select", "payment", "shipping", "address", "method")):
        return "form"
    if any(term in name_l for term in ("cart", "basket")) or _is_child_collection_model(model, step_name):
        return "list"
    if any(term in name_l for term in ("confirmation", "confirm", "detail")):
        return "detail"
    return "detail"

def _normalize_section_operations(operations) -> dict:
    defaults = {"create": False, "update": False, "delete": False, "select": False}
    if isinstance(operations, dict):
        normalized = dict(defaults)
        normalized.update({
            "create": bool(operations.get("create", False)),
            "update": bool(operations.get("update", False) or operations.get("edit", False)),
            "delete": bool(operations.get("delete", False) or operations.get("remove", False)),
            "select": bool(operations.get("select", False) or operations.get("view", False)),
        })
        return normalized
    if isinstance(operations, list):
        values = {str(value).strip().lower() for value in operations}
        return {
            "create": "create" in values,
            "update": bool({"update", "edit"} & values),
            "delete": bool({"delete", "remove"} & values),
            "select": bool({"select", "view"} & values),
        }
    return defaults.copy()

def _workflow_task_section(step: dict, model: str, model_attrs: dict) -> dict:
    page_id = _section_id(step.get("page_id") or step.get("page_name") or "workflow")
    model_id = _section_id(model)
    layout = _activity_layout_for_step(step.get("activity_node_name", ""), model)
    name_l = f"{step.get('activity_node_name', '')} {model}".lower()
    style = {
        "color": "accent",
        "density": "compact" if layout in {"list", "table"} else "normal",
        "shadow": "sm",
        "border": "light",
        "bg": "white",
    }
    if layout == "list":
        style["list_style"] = "cart-item" if any(term in name_l for term in ("cart", "basket", "item", "line")) else "default"
    if layout == "form":
        style["form_style"] = "step"
        style["cta_label"] = "Save"
    return {
        "id": f"{page_id}_{model_id}_task_content",
        "name": f"{step.get('activity_node_name') or 'Task'} {model}",
        "layout": layout,
        "primary_model": model,
        "class": model,
        "attributes": _model_field_names(model_attrs, model, 8),
        "operations": {
            "create": layout == "form",
            "update": layout in {"form", "list", "table", "detail"},
            "delete": layout in {"list", "table"},
        },
        "query": {"limit": 12, "order_by": []},
        "col_span": 12,
        "position": "main",
        "style": style,
    }

def _ensure_workflow_pages(pages: list, sections: list, workflow_steps: list, model_attrs: dict | None = None, usecase_navigation: dict | None = None) -> tuple[list, list]:
    if not workflow_steps:
        return pages, sections
    model_attrs = model_attrs or {}
    known_models = set(model_attrs.keys())
    workflow_entries = (usecase_navigation or {}).get("workflow_entry_points") or []
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_ids = {str(s.get("id")) for s in sections}
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}

    def page_action_id(p: dict) -> str:
        action = p.get("action") or {}
        if isinstance(action, dict):
            return str(action.get("value") or action.get("id") or "")
        return ""

    page_by_action = {page_action_id(p): p for p in pages if page_action_id(p)}
    for step in workflow_steps:
        node_id = step["activity_node_id"]
        page = page_by_action.get(node_id)
        if not page:
            page = {
                "id": step["page_id"],
                "name": step["page_name"],
                "primary_model": "",
                "type": {"value": "activity", "label": "Activity"},
                "action": {"value": node_id, "label": step["activity_node_name"]},
                "sections": [],
                "category": None,
            }
            pages.append(page)
            page_by_action[node_id] = page
        else:
            page["type"] = {"value": "activity", "label": "Activity"}
            page["action"] = {"value": node_id, "label": step["activity_node_name"]}
            page.setdefault("category", None)
            page.setdefault("sections", [])
        refs = page.get("sections") or []
        ref_ids = {str(ref.get("value") if isinstance(ref, dict) else ref) for ref in refs}
        for model in _activity_models_for_step(step, workflow_entries, known_models):
            content = _workflow_task_section(step, model, model_attrs)
            if any((section_map.get(sid) or {}).get("primary_model") == model and (section_map.get(sid) or {}).get("layout") != "filter" for sid in ref_ids):
                continue
            sid = content["id"]
            suffix = 2
            base_sid = sid
            while sid in section_ids:
                sid = f"{base_sid}_{suffix}"
                suffix += 1
            content["id"] = sid
            sections.append(content)
            section_ids.add(sid)
            section_map[sid] = content
            refs.append({"value": sid})
            ref_ids.add(sid)
        button_id = f"{_section_id(page.get('id') or page.get('name'))}_workflow_action"
        if button_id not in section_ids:
            sections.append({
                "id": button_id,
                "name": f"{page.get('name', step['page_name']).replace('_', ' ')} Continue",
                "label": "Continue",
                "type": "activity_action",
                "layout": "activity_action",
                "primary_model": "",
                "class": "",
                "operations": {"create": False, "update": False, "delete": False},
                "attributes": [],
                "methods": [],
                "col_span": 12,
                "position": "main",
                "style": {"variant": "wizard_next", "align": "right", "size": "lg"},
                "workflow": {"action": "complete"},
            })
            section_ids.add(button_id)
        if button_id not in ref_ids:
            refs.append({"value": button_id})
            page["sections"] = refs
        else:
            page["sections"] = refs
    return pages, sections

def _normalize_activity_action_sections(pages: list, sections: list) -> list:
    activity_page_section_ids = set()
    for page in pages:
        page_type = page.get("type", {}); page_type_value = page_type.get("value") if isinstance(page_type, dict) else page_type
        if page_type_value != "activity": continue
        for ref in page.get("sections") or []: activity_page_section_ids.add(str(ref.get("value") if isinstance(ref, dict) else ref))
    for section in sections:
        sid = str(section.get("id", "")); is_activity_action = section.get("type") == "activity_action" or section.get("layout") == "activity_action"
        if not is_activity_action: continue
        operations = _normalize_section_operations(section.get("operations"))
        section["operations"] = operations
        has_data_shape = bool(section.get("primary_model")) or bool(section.get("attributes")) or any(operations.values())
        if has_data_shape and sid not in activity_page_section_ids:
            section["layout"] = "list"; section.pop("type", None); section.pop("workflow", None); section.pop("workflow_action", None); section.pop("target_page", None); section.pop("targetPage", None); style = section.get("style") or {}
            if style.get("variant") in {"button", "link", "fab", "wizard_next", "auto"}: style.pop("variant", None)
            section["style"] = style; continue
        section["type"] = "activity_action"; section["layout"] = "activity_action"; section["primary_model"] = ""; section["class"] = ""; section["attributes"] = []; section["operations"] = {"create": False, "update": False, "delete": False}; section.setdefault("label", section.get("name") or "Continue"); workflow = section.get("workflow") or {}; workflow.setdefault("action", section.get("workflow_action") or "complete"); section["workflow"] = workflow
    return sections

def _actor_name_from_context(system_context: dict, actor_id: str | None) -> str | None:
    for classifier in _as_list(system_context.get("classifiers"), "classifiers"):
        if str(classifier.get("id")) == str(actor_id): return (classifier.get("data") or {}).get("name")
    return None

def _apply_builtin_workflow_logic(interface_data: dict, system_id: str | None, actor_id: str | None) -> dict:
    data = dict(interface_data or {}); pages = list(data.get("pages") or []); sections = list(data.get("sections") or [])
    if system_id:
        system_context = _fetch_system_context_data(system_id)
        actor_name = _actor_name_from_context(system_context, actor_id)
        model_attrs = {}
        for c in _as_list(system_context.get("classifiers"), "classifiers"):
            cdata = c.get("data") or {}
            cname = cdata.get("name")
            if cname:
                model_attrs[cname] = {a.get("name") for a in cdata.get("attributes", []) if a.get("name")}
        usecase_navigation = _build_usecase_navigation(system_context, str(actor_id or ""), actor_name)
        workflow_steps = _workflow_plan(system_context, str(actor_id or ""), actor_name)
        pages, sections = _ensure_workflow_pages(pages, sections, workflow_steps, model_attrs, usecase_navigation)
    sections = _normalize_activity_action_sections(pages, sections); data["pages"] = pages; data["sections"] = sections
    return data

def _page_type_value(page: dict) -> str:
    page_type = page.get("type")
    if isinstance(page_type, dict):
        return str(page_type.get("value") or "")
    return str(page_type or "")

def _ref_id(ref) -> str:
    return str(ref.get("value") if isinstance(ref, dict) else ref or "")

def _navigation_methods(names: list[str]) -> list[dict]:
    return [
        {"name": str(name), "label": str(name).replace("_", " "), "action": "navigate"}
        for name in names
        if name
    ]

def _model_field_names(model_attrs: dict, model: str, limit: int = 6) -> list[str]:
    preferred = ["name", "title", "status", "price", "total", "quantity", "description", "created_at"]
    attrs = list(model_attrs.get(model) or [])
    selected = [name for name in preferred if name in attrs]
    selected.extend([name for name in attrs if name and name not in selected and name.lower() != "id"])
    return selected[:limit] or attrs[:limit]

def _infer_section_layout(page: dict, candidate_index: int = 0) -> str:
    name = f"{page.get('name', '')} {page.get('id', '')}".lower()
    if any(term in name for term in ("detail", "view_", "account", "profile")):
        return "detail"
    if any(term in name for term in ("shipping", "payment", "checkout", "address", "form", "enter_")):
        return "form"
    if any(term in name for term in ("cart", "order", "tracking")):
        return "list"
    if any(term in name for term in ("browse", "products", "catalog", "gallery", "shop")):
        return "gallery" if candidate_index % 2 == 0 else "card"
    return ("card", "table", "list")[candidate_index % 3]

def _fallback_model_for_page(page: dict, known_models: set[str]) -> str:
    if page.get("primary_model"):
        return str(page.get("primary_model"))
    page_name = f"{page.get('name', '')} {page.get('id', '')}".lower()
    for model in sorted(known_models):
        if model.lower() in page_name:
            return model
    non_process = [m for m in sorted(known_models) if m.lower() not in {"user", "group", "permission"}]
    return non_process[0] if non_process else ""

def _default_section_for_page(page: dict, model: str, model_attrs: dict, candidate_index: int) -> dict:
    layout = _infer_section_layout(page, candidate_index)
    page_id = _section_id(page.get("id") or page.get("name") or "page")
    sid = f"{page_id}_{_section_id(model or 'content')}_{layout}"
    attrs = _model_field_names(model_attrs, model, 8 if layout in {"table", "detail"} else 5)
    operations = {"create": layout == "form", "update": layout in {"detail", "form"}, "delete": False}
    style = {
        "color": "accent",
        "density": ("normal", "compact", "spacious")[candidate_index % 3],
        "shadow": "md" if layout in {"card", "gallery", "detail"} else "sm",
        "border": "light",
        "bg": "white",
        "header_style": "large" if layout in {"gallery", "detail"} else "default",
    }
    if layout in {"card", "gallery"}:
        style.update({"display_mode": "grid", "card_style": "product" if model.lower() == "product" else "default", "columns": "3"})
    elif layout == "list":
        style.update({"list_style": "cart-item" if "cart" in page_id else "default"})
    elif layout == "form":
        style.update({"form_style": "step", "cta_label": "Continue"})
    elif layout == "detail":
        style.update({"image_position": "left", "image_size": "md"})
    return {
        "id": sid,
        "name": page.get("name", sid).replace("_", " "),
        "layout": layout,
        "primary_model": model,
        "class": model,
        "attributes": attrs,
        "operations": operations,
        "query": {"limit": 12, "order_by": ["name"] if "name" in attrs else []},
        "col_span": 12,
        "position": "main",
        "style": style,
    }

def _ensure_candidate_content_structure(pages: list, sections: list, model_attrs: dict, candidate_index: int = 0) -> tuple[list, list]:
    known_models = set(model_attrs.keys())
    sections = [dict(s) for s in sections]
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    activity_section_ids = {sid for sid, s in section_map.items() if s.get("type") == "activity_action" or s.get("layout") == "activity_action"}
    chrome_layouts = {"promo-bar", "logo", "search-bar", "icon-actions", "nav-links", "main-header", "minimal-header", "site-nav", "site-footer", "service-bar", "link-grid", "brand-strip", "activity_start", "activity_tasks"}

    fixed_pages = []
    normal_pages = []
    activity_pages = []
    for page in pages:
        page = dict(page)
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        if _page_type_value(page) != "activity":
            refs = [ref for ref in refs if ref["value"] not in activity_section_ids]
            page["sections"] = refs
            normal_pages.append(page)
        else:
            page["sections"] = refs
            activity_pages.append(page)

    normal_page_ids = {_section_id(p.get("id") or p.get("name")) for p in normal_pages}
    if normal_pages and not any((s.get("layout") in {"site-nav", "nav-links", "main-header"} or s.get("position") == "header") and s.get("layout") in chrome_layouts for s in sections):
        nav_id = "app_site_nav"
        sections.append({
            "id": nav_id,
            "name": "Site Navigation",
            "layout": "site-nav",
            "primary_model": "",
            "class": "",
            "attributes": [],
            "operations": {"create": False, "update": False, "delete": False},
            "col_span": 12,
            "position": "header",
            "style": {"color": "accent", "density": "normal", "shadow": "none", "border": "light", "bg": "white"},
            "methods": _navigation_methods([p.get("name") for p in normal_pages if p.get("name")]),
        })
        section_map[nav_id] = sections[-1]
        for page in normal_pages:
            refs = page.get("sections") or []
            if nav_id not in {_ref_id(ref) for ref in refs}:
                page["sections"] = [{"value": nav_id}] + refs

    for page in normal_pages:
        model = _fallback_model_for_page(page, known_models)
        if model and not page.get("primary_model"):
            page["primary_model"] = model
        ref_ids = {_ref_id(ref) for ref in page.get("sections") or []}
        has_content = False
        for sid in ref_ids:
            section = section_map.get(sid) or {}
            if section.get("position", "main") == "main" and section.get("layout") not in chrome_layouts and section.get("layout") != "activity_action":
                has_content = True
                if model and not section.get("primary_model"):
                    section["primary_model"] = model
                    section["class"] = model
                if section.get("primary_model") in model_attrs and not section.get("attributes"):
                    section["attributes"] = _model_field_names(model_attrs, section["primary_model"])
                section.setdefault("operations", {"create": False, "update": False, "delete": False})
        if not has_content and model:
            section = _default_section_for_page(page, model, model_attrs, candidate_index)
            dedupe_id = section["id"]
            suffix = 2
            while dedupe_id in section_map:
                dedupe_id = f"{section['id']}_{suffix}"
                suffix += 1
            section["id"] = dedupe_id
            sections.append(section)
            section_map[dedupe_id] = section
            page.setdefault("sections", [])
            page["sections"].append({"value": dedupe_id})
    fixed_pages = normal_pages + activity_pages
    return fixed_pages, sections

def _ensure_usecase_pages(pages: list, usecase_navigation: dict) -> list:
    if not usecase_navigation:
        return pages
    pages = [dict(p) for p in pages]
    existing = {_section_id(p.get("id") or p.get("name")) for p in pages}
    page_entries = usecase_navigation.get("pages") or []
    if not page_entries:
        page_entries = [
            {
                "page_id": usecase.get("page_id"),
                "page_name": usecase.get("page_name"),
                "primary_model": usecase.get("page_model") or usecase.get("primary_model", ""),
                "usecases": [usecase.get("name")],
            }
            for usecase in usecase_navigation.get("usecases") or []
            if (usecase.get("ui_mapping") or {}).get("role") != "background"
        ]
    for page_entry in page_entries:
        page_id = _section_id(page_entry.get("page_id") or page_entry.get("page_name"))
        if not page_id or page_id in existing:
            continue
        pages.append({
            "id": page_id,
            "name": page_entry.get("page_name") or _page_name(page_id),
            "primary_model": page_entry.get("primary_model", ""),
            "type": {"value": "content", "label": "Content"},
            "sections": [],
            "category": None,
            "source_usecases": page_entry.get("usecases") or [],
        })
        existing.add(page_id)
    return pages

def _ensure_workflow_entry_sections(pages: list, sections: list, usecase_navigation: dict) -> tuple[list, list]:
    entries = usecase_navigation.get("workflow_entry_points") or []
    if not entries:
        return pages, sections
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_ids = {str(s.get("id")) for s in sections if s.get("id")}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}
    for entry in entries:
        page = page_by_id.get(_section_id(entry.get("page_id") or entry.get("page_name")))
        if not page:
            continue
        sid = f"{_section_id(page.get('id') or page.get('name'))}_workflow_start"
        if sid not in section_ids:
            sections.append({
                "id": sid,
                "name": entry.get("label") or "Start Workflow",
                "label": entry.get("label") or "Start Workflow",
                "type": "activity_start",
                "layout": "activity_start",
                "primary_model": "",
                "class": "",
                "operations": {"create": False, "update": False, "delete": False},
                "attributes": [],
                "methods": [],
                "col_span": 12,
                "position": "main",
                "style": {"color": "accent", "density": "normal", "shadow": "sm", "bg": "white", "columns": "1", "cta_label": entry.get("button_label") or "Start"},
            })
            section_ids.add(sid)
        refs = page.get("sections") or []
        if sid not in {_ref_id(ref) for ref in refs}:
            page["sections"] = refs + [{"value": sid}]
    return pages, sections

def _ensure_pre_workflow_content_sections(pages: list, sections: list, usecase_navigation: dict, model_attrs: dict, candidate_index: int = 0) -> tuple[list, list]:
    entries = usecase_navigation.get("workflow_entry_points") or []
    if not entries:
        return pages, sections
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}
    known_models = set(model_attrs.keys())

    for entry in entries:
        page_id = _section_id(entry.get("page_id") or entry.get("page_name"))
        page = page_by_id.get(page_id)
        if not page:
            continue
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        ref_ids = {_ref_id(ref) for ref in refs}
        main_data_sections = [
            section_map.get(sid) or {}
            for sid in ref_ids
            if (section_map.get(sid) or {}).get("position", "main") == "main"
            and (section_map.get(sid) or {}).get("layout") in {"card", "list", "table", "detail", "gallery", "filter", "form"}
        ]
        preferred_models = [
            m for m in (entry.get("pre_workflow_collections") or [])
            if m in known_models
        ]
        if not preferred_models:
            preferred_models = [
                m for m in (entry.get("related_models") or [])
                if m in known_models and _is_child_collection_model(m, f"{entry.get('page_name', '')} {entry.get('usecase_name', '')}")
            ]
        if not preferred_models:
            preferred_models = [m for m in [entry.get("primary_model")] if m in known_models]
        model = preferred_models[0] if preferred_models else ""
        if not model:
            continue
        has_model_section = any(s.get("primary_model") == model for s in main_data_sections)
        if has_model_section:
            continue
        sid = f"{page_id}_{_section_id(model)}_pre_workflow"
        suffix = 2
        base_sid = sid
        while sid in section_map:
            sid = f"{base_sid}_{suffix}"
            suffix += 1
        layout = "list" if _is_child_collection_model(model, f"{entry.get('page_name', '')} {entry.get('usecase_name', '')}") else _infer_section_layout({"id": page_id, "name": page.get("name", "")}, candidate_index)
        style = {
            "color": "accent",
            "density": "compact" if layout in {"list", "table"} else "normal",
            "shadow": "sm",
            "border": "light",
            "bg": "white",
        }
        if layout == "list":
            style["list_style"] = "cart-item" if any(t in f"{page_id} {model}".lower() for t in ("cart", "basket", "item", "line")) else "default"
        section = {
            "id": sid,
            "name": f"{model} Items" if _is_child_collection_model(model, page_id) else f"{model} Overview",
            "layout": layout,
            "primary_model": model,
            "class": model,
            "attributes": _model_field_names(model_attrs, model, 8),
            "operations": {
                "create": False,
                "update": layout in {"list", "table", "detail", "form"},
                "delete": layout in {"list", "table", "card", "gallery"},
            },
            "query": {"limit": 12, "order_by": []},
            "col_span": 12,
            "position": "main",
            "style": style,
        }
        sections.append(section)
        section_map[sid] = section
        activity_start_refs = [ref for ref in refs if (section_map.get(_ref_id(ref)) or {}).get("layout") == "activity_start"]
        other_refs = [ref for ref in refs if ref not in activity_start_refs]
        page["sections"] = other_refs + [{"value": sid}] + activity_start_refs
    return pages, sections

def _apply_ooui_navigation_methods(pages: list, sections: list, usecase_navigation: dict) -> list:
    nav_ids = {_section_id(pid) for pid in (usecase_navigation.get("nav_bar_pages") or []) if pid}
    if not nav_ids:
        return sections
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}
    nav_names = [
        (page_by_id.get(pid) or {}).get("name") or _page_name(pid)
        for pid in usecase_navigation.get("nav_bar_pages") or []
        if _section_id(pid) in page_by_id
    ]
    if not nav_names:
        return sections
    fixed = []
    for section in sections:
        section = dict(section)
        if section.get("layout") in {"site-nav", "nav-links", "main-header"} or section.get("position") == "header" and section.get("layout") in {"site-nav", "nav-links"}:
            section["methods"] = _navigation_methods(nav_names)
        fixed.append(section)
    return fixed

def _materialize_ooui_plan_sections(pages: list, sections: list, ooui_plan: dict, model_attrs: dict) -> tuple[list, list]:
    if not ooui_plan:
        return pages, sections
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}

    for section_plan in ooui_plan.get("sections") or []:
        if section_plan.get("role") not in DATA_SECTION_ROLES:
            continue
        sid = section_plan.get("id")
        page_id = _section_id(section_plan.get("page_id"))
        model = section_plan.get("primary_model") or ""
        if not sid or not page_id or not model or sid in section_map:
            continue
        if model not in model_attrs:
            continue
        editable = set(section_plan.get("editable_fields") or [])
        operations = {
            "create": "create" in section_plan.get("operations", []),
            "update": bool(editable) or "update" in section_plan.get("operations", []),
            "delete": "delete" in section_plan.get("operations", []),
            "select": bool({"view", "select"} & set(section_plan.get("operations", []))),
        }
        attrs = list(section_plan.get("visible_fields") or [])
        attrs.extend([
            {"name": name, "source": "related", "readonly": True}
            for name in section_plan.get("related_visible_fields") or []
        ])
        if not attrs:
            attrs = _model_field_names(model_attrs, model, 8)
        section = {
            "id": sid,
            "name": section_plan.get("name") or sid,
            "layout": section_plan.get("layout") or "detail",
            "primary_model": model,
            "class": model,
            "attributes": attrs,
            "operations": operations,
            "query": {"limit": 12, "order_by": []},
            "col_span": section_plan.get("col_span", 12),
            "position": "main",
            "style": section_plan.get("style") or {"color": "accent", "density": "normal", "shadow": "sm", "bg": "white"},
        }
        sections.append(section)
        section_map[sid] = section
        page = page_by_id.get(page_id)
        if page:
            refs = page.get("sections") or []
            if sid not in {_ref_id(ref) for ref in refs}:
                page["sections"] = refs + [{"value": sid}]
    return pages, sections

def _fetch_system_context_data(system_id: str) -> dict:
    response = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/", headers=_AUTH_HEADERS); response.raise_for_status(); system_data = response.json(); classifiers_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/classifiers/", headers=_AUTH_HEADERS); relations_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/relations/", headers=_AUTH_HEADERS); system_data["classifiers"] = classifiers_resp.json() if classifiers_resp.ok else []; system_data["relations"] = relations_resp.json() if relations_resp.ok else []; export_resp = requests.get(f"{METADATA_API_BASE}/systems/export/", params=[("system_ids", system_id)], headers=_AUTH_HEADERS)
    if export_resp.ok:
        exported = export_resp.json()
        if exported: system_data["diagrams"] = exported[0].get("diagrams", [])
    system_data["activity_diagrams"] = _build_activity_diagrams(system_data)
    return system_data

def get_system_context(system_id: str) -> str:
    try:
        system_data = _fetch_system_context_data(system_id); system_data["workflow_plan"] = _workflow_plan(system_data, None); system_data["usecase_navigation"] = _build_usecase_navigation(system_data, None)
        return json.dumps(system_data, indent=2)
    except Exception as e: return f"Error fetching system context: {e}"

def get_interface_config(interface_id: str) -> str:
    try:
        response = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS); response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e: return f"Error fetching interface config: {e}"

def list_existing_templates() -> list:
    try:
        if not os.path.exists(TEMPLATES_DIR): return [f"Templates directory not found at {TEMPLATES_DIR}"]
        return os.listdir(TEMPLATES_DIR)
    except Exception as e: return [f"Error listing templates: {e}"]

def read_template_file(filename: str) -> str:
    try:
        path = os.path.join(TEMPLATES_DIR, filename)
        if not os.path.exists(path): return f"File {filename} not found."
        with open(path, "r", encoding="utf-8") as f: return f.read()
    except Exception as e: return f"Error reading template: {e}"

def write_prototype_template(filename: str, content: str) -> str:
    try:
        if not filename.endswith((".html", ".jinja2")): return "Error: File must be .html or .jinja2"
        os.makedirs(TEMPLATES_DIR, exist_ok=True); path = os.path.join(TEMPLATES_DIR, filename)
        with open(path, "w", encoding="utf-8") as f: f.write(content)
        return f"Successfully wrote {filename} to {TEMPLATES_DIR}"
    except Exception as e: return f"Error writing template: {e}"

def update_interface_data(interface_id: str, data: dict) -> str:
    try:
        resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS); resp.raise_for_status(); current = resp.json(); payload = {"id": interface_id, "name": current["name"], "description": current["description"], "system_id": current["system"], "actor_id": current["actor"], "data": data}; response = requests.put(f"{METADATA_API_BASE}/interfaces/{interface_id}/", json=payload, headers=_AUTH_HEADERS); response.raise_for_status()
        return f"Successfully updated interface {interface_id} data."
    except Exception as e: return f"Error updating interface data: {e}"

def _build_known_attrs(system_id: str) -> dict[str, set[str]]:
    """Returns {ModelName: {attr_name, ...}} for validation. Empty on error."""
    try:
        ctx = _fetch_system_context_data(system_id)
        result = {}
        for c in _as_list(ctx, "classifiers"):
            name = (c.get("data") or {}).get("name", "")
            attrs = {a.get("name") for a in ((c.get("data") or {}).get("attributes") or []) if a.get("name")}
            if name:
                result[name] = attrs
        return result
    except Exception:
        return {}

def apply_interface_patch(interface_id: str, patch: dict) -> str:
    try:
        resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS)
        resp.raise_for_status()
        current = resp.json()
        data = dict(current.get("data") or {})
        if "sections" in patch:
            section_map = {str(s["id"]): s for s in data.get("sections", [])}
            for ps in patch["sections"]:
                sid = str(ps.get("id", ""))
                if sid not in section_map:
                    continue
                for field in ("layout", "col_span", "position", "attributes", "query", "workflow", "label", "target_page", "workflow_action"):
                    if field in ps:
                        section_map[sid][field] = ps[field]
                if "style" in ps:
                    section_map[sid]["style"] = {**(section_map[sid].get("style") or {}), **ps["style"]}
            data["sections"] = list(section_map.values())
        if "pages" in patch:
            page_map = {str(p["id"]): p for p in data.get("pages", [])}
            for pp in patch["pages"]:
                pid = str(pp.get("id", ""))
                if pid not in page_map:
                    continue
                for field in ("layout", "gap"):
                    if field in pp:
                        page_map[pid][field] = pp[field]
            data["pages"] = list(page_map.values())
        if "styling" in patch:
            data["styling"] = {**(data.get("styling") or {}), **patch["styling"]}
        if "tokens" in patch:
            data["tokens"] = {**(data.get("tokens") or {}), **patch["tokens"]}
        # Validate attribute names against real classifier fields; warn agent so it can self-correct
        if "sections" in patch:
            known_attrs = _build_known_attrs(current.get("system", ""))
            warnings = []
            for sec in patch["sections"]:
                model = sec.get("primary_model") or sec.get("class", "")
                raw_attrs = sec.get("attributes") or []
                attr_names = [a if isinstance(a, str) else (a.get("name") if isinstance(a, dict) else "") for a in raw_attrs]
                valid = known_attrs.get(model, set())
                if valid:
                    bad = [a for a in attr_names if a and a not in valid and "." not in a]
                    if bad:
                        warnings.append(f"section '{sec.get('id')}': unknown attributes {bad} for model '{model}' — valid: {sorted(valid)}")
            if warnings:
                return "WARNING — patch rejected due to invented attribute names. Fix these and retry:\n" + "\n".join(warnings)
        try:
            data = _apply_builtin_workflow_logic(data, current.get("system"), current.get("actor"))
        except Exception:
            data["sections"] = _normalize_activity_action_sections(data.get("pages") or [], data.get("sections") or [])
        payload = {
            "id": interface_id,
            "name": current["name"],
            "description": current["description"],
            "system_id": current["system"],
            "actor_id": current["actor"],
            "data": data,
        }
        put_resp = requests.put(f"{METADATA_API_BASE}/interfaces/{interface_id}/", json=payload, headers=_AUTH_HEADERS)
        put_resp.raise_for_status()
        return f"Patched interface {interface_id} successfully."
    except Exception as e: return f"Error patching interface: {e}"

def run_seed_script(python_code: str) -> str:
    try:
        resp = requests.post(f"{PROTOTYPE_API_BASE}/seed_script", json={"script": python_code}, timeout=120)
        if resp.ok: return resp.text or "Seeded OK"
        return f"Seed failed ({resp.status_code}): {resp.text}"
    except Exception as e: return f"Error calling seed_script endpoint: {e}"

def get_available_paths(system_id: str, class_id: str, depth=2) -> str:
    try:
        system_json = get_system_context(system_id)
        if system_json.startswith("Error"): return system_json
        system_data = json.loads(system_json); classifiers = {c["id"]: c for c in system_data.get("classifiers", [])}; relations = system_data.get("relations", [])
        def traverse(cid, current_path, current_depth):
            if current_depth > depth: return []
            paths = []; cls = classifiers.get(cid)
            if not cls: return []
            for attr in cls.get("data", {}).get("attributes", []): attr_name = attr.get("name"); paths.append(f"{current_path}{attr_name}".lstrip("."))
            for rel in relations:
                source_id = rel.get("source"); target_id = rel.get("target"); rel_name = rel.get("name", "").lower()
                if source_id == cid: new_path = f"{current_path}{rel_name}."; paths.extend(traverse(target_id, new_path, current_depth + 1))
            return paths
        return json.dumps(list(set(traverse(class_id, "", 0))))
    except Exception as e: return f"Error computing paths: {e}"

def get_interface_full_context(interface_id: str) -> str:
    try:
        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS); iface_resp.raise_for_status(); iface = iface_resp.json(); system_id = iface.get("system"); system_ctx = _fetch_system_context_data(system_id) if system_id else {}; actor_id = iface.get("actor"); actor_name = None
        for classifier in _as_list(system_ctx.get("classifiers"), "classifiers"):
            if str(classifier.get("id")) == str(actor_id): actor_name = (classifier.get("data") or {}).get("name"); break
        system_ctx["workflow_plan"] = _workflow_plan(system_ctx, str(actor_id or ""), actor_name); system_ctx["usecase_navigation"] = _build_usecase_navigation(system_ctx, str(actor_id or ""), actor_name); iface_clean = {k: v for k, v in iface.items() if k != "data"}; iface_clean["actor_name"] = actor_name or iface.get("actor_name") or iface.get("actor")
        # Build an explicit model→attributes quick reference to prevent LLM from inventing field names
        attr_ref = {}
        for c in _as_list(system_ctx.get("classifiers"), "classifiers"):
            cdata = c.get("data") or {}
            cname = cdata.get("name", "")
            if cname and cdata.get("type") not in ("actor",):
                attr_ref[cname] = [a.get("name") for a in cdata.get("attributes", []) if a.get("name")]
        return json.dumps({
            "ATTRIBUTE_REFERENCE": {
                "_note": "USE ONLY these exact field names as section attributes. DO NOT invent new names.",
                "models": attr_ref,
            },
            "interface": iface_clean,
            "system": system_ctx,
        }, indent=2)
    except Exception as e: return f"Error fetching full context: {e}"

def validate_and_save_candidate(
    interface_id: str,
    candidate_index: int,
    name: str,
    description: str,
    pages: list,
    sections: list,
    tokens: dict = None,
    styling: dict = None,
    prompt: str = "",
) -> str:
    """Validate and save one interface candidate (call once per candidate index 0, 1, 2).

    Args:
        interface_id: The interface UUID (from the message).
        candidate_index: 0, 1, or 2.
        name: Short display name for this design direction (e.g. "Card-forward Commerce").
        description: One sentence describing this candidate's visual approach.
        pages: List of page objects. Each page: {id, name, type?, sections: [{value: section_id}, ...]}.
               Pages do NOT contain section data — they only reference section IDs.
        sections: List of ALL section definition objects. Each section must have:
                  id, name, layout, position, col_span, primary_model, attributes, operations, style.
                  This is SEPARATE from pages. Both pages[] and sections[] are required.
        tokens: Design token dict from select_design_specs_for_interface (optional but strongly recommended).
        styling: Global styling overrides dict (optional).
        prompt: Original user design prompt (optional, for logging).
    """
    try:
        if styling:
            styling = dict(styling); alias_map = {"accent_color": "accentColor", "background_color": "backgroundColor", "text_color": "textColor", "selected_style": "selectedStyle"}
            for old_key, new_key in alias_map.items():
                if old_key in styling and new_key not in styling: styling[new_key] = styling.pop(old_key)
            if isinstance(styling.get("radius"), str):
                radius_map = {"none": 0, "sm": 4, "md": 8, "lg": 12, "xl": 16, "2xl": 24}; styling["radius"] = radius_map.get(styling["radius"], 8)
        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS); iface_resp.raise_for_status(); iface = iface_resp.json(); system_id = iface.get("system")
        design_spec_name = None
        if not tokens:
            design_spec_name, tokens = _candidate_design_spec(interface_id, int(candidate_index or 0), prompt=prompt)
        elif isinstance(tokens, str):
            try:
                tokens = json.loads(tokens)
            except Exception:
                tokens = {}
        if tokens:
            tokens = dict(tokens)
            design_spec_name = design_spec_name or tokens.get("design.spec_name") or tokens.get("spec_name")
            if design_spec_name:
                tokens["design.spec_name"] = design_spec_name
        cls_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/classifiers/", headers=_AUTH_HEADERS); classifiers_data = cls_resp.json() if cls_resp.ok else {}; raw_classifiers = classifiers_data.get("classifiers", []) if isinstance(classifiers_data, dict) else classifiers_data; model_attrs = {}
        for c in raw_classifiers:
            cdata = c.get("data", {}); cname = cdata.get("name", ""); attrs = {a.get("name", "") for a in cdata.get("attributes", []) if a.get("name")}
            if cname: model_attrs[cname] = attrs
        known_models = set(model_attrs.keys())
        usecase_navigation = {}
        try:
            system_context = _fetch_system_context_data(system_id)
            actor_name = _actor_name_from_context(system_context, iface.get("actor"))
            usecase_navigation = _build_usecase_navigation(system_context, str(iface.get("actor") or ""), actor_name)
            pages = _ensure_usecase_pages(pages, usecase_navigation)
        except Exception:
            usecase_navigation = {}
        try: completed_data = _apply_builtin_workflow_logic({"pages": pages, "sections": sections}, system_id, iface.get("actor")); pages = completed_data.get("pages") or []; sections = completed_data.get("sections") or []; pages, sections = _ensure_workflow_entry_sections(pages, sections, usecase_navigation)
        except Exception: sections = _normalize_activity_action_sections(pages, sections)
        page_names = {p.get("name", "") for p in pages}; page_ref_to_name = {}
        for p in pages:
            pname = p.get("name", ""); pid = p.get("id", "")
            if pname: page_ref_to_name[pname] = pname; page_ref_to_name[pname.lower()] = pname
            if pid: page_ref_to_name[pid] = pname; page_ref_to_name[pid.lower()] = pname
        def _norm_model(n: str) -> str:
            return re.sub(r'[\s_-]', '', str(n or '')).lower()
        model_names_fuzzy = {_norm_model(m): m for m in known_models}
        def _canonical_model_name(name: str) -> str:
            return name if name in known_models else model_names_fuzzy.get(_norm_model(name), "")
        errors = []; _VALID_LAYOUTS = {"card", "list", "table", "detail", "gallery", "filter", "form", "activity_action", "activity_start", "activity_tasks", "promo-bar", "logo", "search-bar", "icon-actions", "nav-links", "main-header", "minimal-header", "site-nav", "site-footer", "service-bar", "link-grid", "brand-strip"}
        _VALID_STYLE = {"color": {"blue", "green", "purple", "orange", "rose", "slate", "accent", "accent-secondary"},"density": {"compact", "normal", "spacious"}, "shadow": {"none", "sm", "md", "lg", "xl"}, "border": {"none", "light", "colored", "strong"}, "bg": {"white", "light", "gray", "dark"}, "header_style": {"default", "large", "small", "colored", "hidden"}, "display_mode": {"grid", "carousel", "banner"}, "card_style": {"default", "product", "category", "compact"}, "list_style": {"default", "product", "cart-item"}, "form_style": {"default", "auth", "step", "summary"}, "image_position": {"left", "top", "right"}, "image_size": {"sm", "md", "lg"}}
        for s in sections:
            s["operations"] = _normalize_section_operations(s.get("operations"))
            sname = s.get("name", "?"); layout = s.get("layout", "")
            if layout and layout not in _VALID_LAYOUTS: errors.append(f"section '{sname}': invalid layout '{layout}'")
            pm = s.get("primary_model", "")
            if pm and pm not in known_models:
                errors.append(f"section '{sname}': unknown primary_model '{pm}'")
            for attr in s.get("attributes", []):
                attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                if "." in attr_name:
                    first, rest = attr_name.split(".", 1)
                    canonical = _canonical_model_name(first)
                    if not canonical:
                        errors.append(f"section '{sname}': dot-notation prefix '{first}' not a known model")
                    elif rest not in model_attrs.get(canonical, set()):
                        errors.append(f"section '{sname}': related attribute '{rest}' not found on {canonical}")
                elif pm and pm in model_attrs and attr_name and attr_name not in model_attrs[pm]: errors.append(f"section '{sname}': attribute '{attr_name}' not found on {pm}")
            vdp = s.get("view_detail_page", "")
            if vdp and vdp not in page_names:
                errors.append(f"section '{sname}': view_detail_page '{vdp}' not in pages")
            sp = (s.get("style") or {}).get("success_page", "")
            if sp and sp not in page_names:
                errors.append(f"section '{sname}': success_page '{sp}' not in pages")
            workflow = s.get("workflow") or {}; workflow_action = workflow.get("action") or s.get("workflow_action", "")
            if workflow_action and workflow_action not in {"complete", "complete_then_page", "complete_then_target", "navigate", "none"}: errors.append(f"section '{sname}': invalid workflow.action '{workflow_action}'")
            workflow_target = workflow.get("target_page") or workflow.get("targetPage") or s.get("target_page") or s.get("targetPage") or ""
            if workflow_target and workflow_target in page_ref_to_name: workflow["target_page"] = page_ref_to_name[workflow_target]; s["workflow"] = workflow
            if workflow_target and workflow_target not in page_names:
                normalized_workflow_target = page_ref_to_name.get(str(workflow_target).lower())
                if normalized_workflow_target: workflow["target_page"] = normalized_workflow_target; s["workflow"] = workflow
                else: errors.append(f"section '{sname}': workflow target_page '{workflow_target}' not in pages")
            for field, valid_vals in _VALID_STYLE.items():
                val = (s.get("style") or {}).get(field, "")
                if val and val not in valid_vals:
                    errors.append(f"section '{sname}': invalid style.{field} '{val}'")
        # Build a fuzzy lookup: "LoanApplication" / "loan_application" / "Loan Application" all → canonical
        _data_layouts_set = {"card", "list", "table", "detail", "gallery", "filter", "form"}

        fixed_sections = []
        for s in sections:
            s = dict(s)
            s["operations"] = _normalize_section_operations(s.get("operations"))
            pm = s.get("primary_model", "")
            # Normalize primary_model name: handles CamelCase / snake_case / space variants
            if pm and pm not in model_attrs:
                canonical = model_names_fuzzy.get(_norm_model(pm))
                if canonical:
                    s["primary_model"] = canonical
                    s["class"] = canonical
                    pm = canonical
            if pm and pm in model_attrs:
                new_attrs = []
                for attr in s.get("attributes", []):
                    attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                    if "." in attr_name:
                        first, rest = attr_name.split(".", 1)
                        canonical = _canonical_model_name(first)
                        if canonical and rest in model_attrs.get(canonical, set()):
                            normalized = dict(attr) if isinstance(attr, dict) else {"name": attr_name}
                            normalized["name"] = f"{canonical}.{rest}"
                            normalized.setdefault("source", "related")
                            normalized.setdefault("readonly", True)
                            new_attrs.append(normalized)
                    elif not pm or attr_name in model_attrs.get(pm, set()):
                        new_attrs.append(attr)
                # If all attrs were invalid, auto-populate from actual model fields
                if not new_attrs and s.get("layout") in _data_layouts_set:
                    new_attrs = list(_model_field_names(model_attrs, pm, 6))
                s["attributes"] = new_attrs
            fixed_sections.append(s)
        # Auto-correct hardcoded Tailwind color names → "accent" so sections inherit
        # the design spec brand color via CSS variables instead of being locked to one color.
        _DATA_LAYOUTS = {"card", "list", "table", "detail", "gallery", "filter", "form"}
        _AUTO_CORRECT_COLORS = {"blue", "green", "purple"}
        for s in fixed_sections:
            if s.get("layout") in _DATA_LAYOUTS:
                style = dict(s.get("style") or {})
                if not style.get("color") or style.get("color") in _AUTO_CORRECT_COLORS:
                    style["color"] = "accent"
                    s["style"] = style

        fixed_pages = []
        for i, p in enumerate(pages):
            if not p.get("id"): p = {**p, "id": f"page_{candidate_index}_{i}"}
            if "category" not in p: p = {**p, "category": None}
            fixed_pages.append(p)
        for i, s in enumerate(fixed_sections):
            if not s.get("id"): layout = s.get("layout", "section"); model = (s.get("primary_model") or "chrome").lower().replace(" ", "_"); fixed_sections[i] = {**s, "id": f"{model}_{layout}_{candidate_index}_{i}"}
            if not fixed_sections[i].get("name"): fixed_sections[i] = {**fixed_sections[i], "name": fixed_sections[i]["id"]}
        fixed_pages = _ensure_usecase_pages(fixed_pages, usecase_navigation)
        fixed_pages, fixed_sections = _materialize_ooui_plan_sections(fixed_pages, fixed_sections, usecase_navigation.get("ooui_plan") or {}, model_attrs)
        for s in fixed_sections:
            s["operations"] = _normalize_section_operations(s.get("operations"))
        fixed_pages, fixed_sections = _ensure_workflow_entry_sections(fixed_pages, fixed_sections, usecase_navigation)
        fixed_pages, fixed_sections = _ensure_candidate_content_structure(fixed_pages, fixed_sections, model_attrs, int(candidate_index or 0))
        fixed_pages, fixed_sections = _ensure_pre_workflow_content_sections(fixed_pages, fixed_sections, usecase_navigation, model_attrs, int(candidate_index or 0))
        fixed_sections = _apply_ooui_navigation_methods(fixed_pages, fixed_sections, usecase_navigation)
        chrome_positions = {"header", "hero", "footer", "sidebar"}; content_sections = [s for s in fixed_sections if s.get("position", "main") not in chrome_positions]
        def _norm_section_refs(refs: list) -> list:
            result = []
            for r in refs:
                if isinstance(r, dict): result.append(r)
                elif isinstance(r, str): result.append({"value": r})
            return result
        for i, p in enumerate(fixed_pages):
            if p.get("sections") is not None: fixed_pages[i] = {**p, "sections": _norm_section_refs(p["sections"])}
        pages_need_sections = any(not p.get("sections") for p in fixed_pages)
        if pages_need_sections and content_sections:
            from collections import defaultdict; model_to_sections = defaultdict(list)
            for s in content_sections: model_to_sections[s.get("primary_model", "")].append(s["id"])
            rebuilt_pages = []; model_assigned = defaultdict(int)
            for p in fixed_pages:
                if p.get("sections"): rebuilt_pages.append(p); continue
                pm = p.get("primary_model", ""); candidates_for_page = model_to_sections.get(pm, []); start = model_assigned[pm]; assigned = []
                if start < len(candidates_for_page): assigned = [{"value": candidates_for_page[start]}]; model_assigned[pm] += 1
                if not assigned and model_to_sections.get("", []):
                    fallback = model_to_sections[""]
                    fb_start = model_assigned[""]
                    if fb_start < len(fallback):
                        assigned = [{"value": fallback[fb_start]}]
                        model_assigned[""] += 1
                rebuilt_pages.append({**p, "sections": assigned})
            fixed_pages = rebuilt_pages
        section_ids = {s["id"] for s in fixed_sections}; orphans = []
        for p in fixed_pages:
            for ref in p.get("sections", []):
                sid = ref.get("value") if isinstance(ref, dict) else str(ref)
                if sid and sid not in section_ids: orphans.append(f"page '{p.get('name')}' references section '{sid}' which is not in sections[]")
        if orphans: return f"INCOMPLETE: pages reference section IDs that are missing from sections[]. Missing: {'; '.join(orphans[:5])}."
        data = dict(iface.get("data") or {}); candidates = list(data.get("candidates") or []); candidate = {"id": f"c{candidate_index}", "name": name, "description": description, "pages": fixed_pages, "sections": fixed_sections, **({"tokens": tokens} if tokens else {}), **({"design_spec": design_spec_name} if design_spec_name else {}), **({"styling": styling} if styling else {})}
        while len(candidates) <= candidate_index: candidates.append(None)
        candidates[candidate_index] = candidate; data["candidates"] = candidates; payload = {"id": interface_id, "name": iface["name"], "description": iface.get("description", ""), "system_id": system_id, "actor_id": iface.get("actor"), "data": data}; put_resp = requests.put(f"{METADATA_API_BASE}/interfaces/{interface_id}/", json=payload, headers=_AUTH_HEADERS); put_resp.raise_for_status()
        return f"OK: candidate {candidate_index} '{name}' saved successfully."
    except Exception as e: return f"Error saving candidate: {e}"

def render_candidate_preview_func(interface_id: str, candidate_index: int) -> str:
    try:
        resp = requests.post(f"{METADATA_API_BASE}/interfaces/{interface_id}/candidates/{candidate_index}/render/", headers=_AUTH_HEADERS, timeout=60)
        if resp.ok: return f"OK: preview rendered for candidate {candidate_index}."
        return f"Render failed ({resp.status_code}): {resp.text}"
    except Exception as e: return f"Error rendering preview: {e}"

system_context_tool = FunctionTool(func=get_system_context)
interface_config_tool = FunctionTool(func=get_interface_config)
update_interface_patch_tool = FunctionTool(func=apply_interface_patch)
run_seed_script_tool = FunctionTool(func=run_seed_script)
get_available_paths_tool = FunctionTool(func=get_available_paths)
get_interface_full_context_tool = FunctionTool(func=get_interface_full_context)
validate_save_candidate_tool = FunctionTool(func=validate_and_save_candidate)
render_candidate_preview_tool = FunctionTool(func=render_candidate_preview_func)
list_design_specs_tool = FunctionTool(func=list_design_specs_tool_func)
get_design_system_tool = FunctionTool(func=get_design_system_tool_func)
apply_design_system_to_interface_tool = FunctionTool(func=apply_design_system_to_interface_tool_func)
select_design_specs_for_interface_func.__name__ = "select_design_specs_for_interface"
select_design_specs_for_interface_tool = FunctionTool(func=select_design_specs_for_interface_func)
