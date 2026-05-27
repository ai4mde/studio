import os
import requests
import json
import re
import copy
from google.adk.tools import FunctionTool
from .ooui_planner import DATA_SECTION_ROLES, build_ooui_plan_from_navigation

METADATA_API_BASE = os.getenv("METADATA_API_BASE", "http://studio-api:8000/api/v1/metadata")
PROTOTYPE_API_BASE = os.getenv("PROTOTYPE_API_BASE", "http://studio-prototypes:8010")
_METADATA_API_KEY = os.getenv("METADATA_API_KEY")
_AUTH_HEADERS = {"Authorization": f"Bearer {_METADATA_API_KEY}"} if _METADATA_API_KEY else {}
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

def _hex_to_rgb(value: object) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw.startswith("#"):
        return None
    raw = raw[1:]
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", raw):
        return None
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)

def _relative_luminance(value: object) -> float | None:
    rgb = _hex_to_rgb(value)
    if rgb is None:
        return None
    channels = []
    for channel in rgb:
        normalized = channel / 255
        channels.append(normalized / 12.92 if normalized <= 0.03928 else ((normalized + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

def _contrast_ratio(fg: object, bg: object) -> float | None:
    fg_lum = _relative_luminance(fg)
    bg_lum = _relative_luminance(bg)
    if fg_lum is None or bg_lum is None:
        return None
    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)
    return (lighter + 0.05) / (darker + 0.05)

def _needs_contrast_fix(fg: object, bg: object, minimum: float) -> bool:
    ratio = _contrast_ratio(fg, bg)
    return ratio is not None and ratio < minimum

def _is_dark_hex(value: object) -> bool:
    luminance = _relative_luminance(value)
    return luminance is not None and luminance < 0.28

def _set_readable_token(tokens: dict, keys: tuple[str, ...], fallback: str, bg: str, minimum: float) -> str:
    current = next((tokens.get(key) for key in keys if tokens.get(key)), fallback)
    value = fallback if _needs_contrast_fix(current, bg, minimum) else current
    for key in keys:
        tokens[key] = value
    return value

def _ensure_readable_text_tokens(tokens: dict) -> None:
    page_bg = tokens.get("page.bg.hex") or tokens.get("page.body.bg_hex") or tokens.get("region.main.bg_hex") or "#ffffff"
    main_bg = tokens.get("region.main.bg_hex") or page_bg
    card_bg = tokens.get("component.card.bg_hex") or main_bg
    if not any(_is_dark_hex(value) for value in (page_bg, main_bg, card_bg)):
        return

    main_text = "#f8fafc" if _is_dark_hex(main_bg) else "#111827"
    main_muted = "#cbd5e1" if _is_dark_hex(main_bg) else "#4b5563"
    main_subtle = "#94a3b8" if _is_dark_hex(main_bg) else "#6b7280"
    card_text = "#f8fafc" if _is_dark_hex(card_bg) else "#111827"
    card_muted = "#cbd5e1" if _is_dark_hex(card_bg) else "#4b5563"

    text = _set_readable_token(tokens, ("page.body.text_hex", "page.text.hex", "text.primary.hex"), main_text, main_bg, 4.5)
    muted = _set_readable_token(tokens, ("color.text.muted_hex", "text.muted.hex", "table.header.text_hex"), main_muted, main_bg, 3.0)
    _set_readable_token(tokens, ("color.text.subtle_hex", "text.subtle.hex", "input.placeholder_hex"), main_subtle, main_bg, 2.4)
    _set_readable_token(tokens, ("region.main.text_hex",), main_text, main_bg, 4.5)
    _set_readable_token(tokens, ("component.card.text_hex",), card_text, card_bg, 4.5)
    _set_readable_token(tokens, ("component.card.muted_text_hex",), card_muted, card_bg, 3.0)

    if _needs_contrast_fix(tokens.get("region.footer.text_hex", text), tokens.get("region.footer.bg_hex", page_bg), 4.5):
        tokens["region.footer.text_hex"] = "#f8fafc" if _is_dark_hex(tokens.get("region.footer.bg_hex", page_bg)) else "#111827"
    if _needs_contrast_fix(tokens.get("button.secondary.text_hex", text), tokens.get("button.secondary.bg_hex", card_bg), 4.5):
        tokens["button.secondary.text_hex"] = "#f8fafc" if _is_dark_hex(tokens.get("button.secondary.bg_hex", card_bg)) else "#111827"
    if _needs_contrast_fix(tokens.get("input.text_hex", text), tokens.get("input.bg_hex", card_bg), 4.5):
        tokens["input.text_hex"] = "#f8fafc" if _is_dark_hex(tokens.get("input.bg_hex", card_bg)) else "#111827"
    if _needs_contrast_fix(tokens.get("badge.neutral.text_hex", muted), tokens.get("badge.neutral.bg_hex", page_bg), 3.0):
        tokens["badge.neutral.text_hex"] = "#cbd5e1" if _is_dark_hex(tokens.get("badge.neutral.bg_hex", page_bg)) else "#4b5563"
    if _needs_contrast_fix(tokens.get("component.card.border_hex", tokens.get("region.border_hex")), card_bg, 1.5):
        tokens["component.card.border_hex"] = "#334155" if _is_dark_hex(card_bg) else "#e5e7eb"
    if _needs_contrast_fix(tokens.get("region.border_hex"), main_bg, 1.5):
        tokens["region.border_hex"] = "#334155" if _is_dark_hex(main_bg) else "#e5e7eb"
    tokens.setdefault("region.border_hex", "#334155")
    tokens.setdefault("border.default.hex", tokens["region.border_hex"])
    tokens.setdefault("component.card.border_hex", tokens["region.border_hex"])
    tokens["page.body.text"] = f"text-[{text}]"

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
    _ensure_readable_text_tokens(tokens)
    return tokens

_PROMPT_COLOR_THEMES = {
    "purple": {"accent": "#7c3aed", "secondary": "#c084fc", "page": "#faf5ff", "surface": "#ffffff", "border": "#ddd6fe"},
    "violet": {"accent": "#7c3aed", "secondary": "#c084fc", "page": "#faf5ff", "surface": "#ffffff", "border": "#ddd6fe"},
    "blue": {"accent": "#2563eb", "secondary": "#60a5fa", "page": "#eff6ff", "surface": "#ffffff", "border": "#bfdbfe"},
    "green": {"accent": "#16a34a", "secondary": "#86efac", "page": "#f0fdf4", "surface": "#ffffff", "border": "#bbf7d0"},
    "orange": {"accent": "#f97316", "secondary": "#fdba74", "page": "#fff7ed", "surface": "#ffffff", "border": "#fed7aa"},
    "rose": {"accent": "#e11d48", "secondary": "#fb7185", "page": "#fff1f2", "surface": "#ffffff", "border": "#fecdd3"},
    "pink": {"accent": "#db2777", "secondary": "#f9a8d4", "page": "#fdf2f8", "surface": "#ffffff", "border": "#fbcfe8"},
    "red": {"accent": "#dc2626", "secondary": "#f87171", "page": "#fef2f2", "surface": "#ffffff", "border": "#fecaca"},
    "dark": {"accent": "#8b5cf6", "secondary": "#22d3ee", "page": "#0f172a", "surface": "#111827", "border": "#334155", "text": "#f8fafc", "muted": "#cbd5e1"},
    "black": {"accent": "#111827", "secondary": "#6b7280", "page": "#f9fafb", "surface": "#ffffff", "border": "#d1d5db"},
    "slate": {"accent": "#475569", "secondary": "#94a3b8", "page": "#f8fafc", "surface": "#ffffff", "border": "#cbd5e1"},
}

_COLOR_KEYWORDS = {
    "purple": "#7c3aed",
    "violet": "#7c3aed",
    "blue": "#2563eb",
    "green": "#16a34a",
    "orange": "#f97316",
    "rose": "#e11d48",
    "pink": "#db2777",
    "red": "#dc2626",
    "dark": "#111827",
    "black": "#111827",
    "slate": "#475569",
    "gray": "#6b7280",
    "grey": "#6b7280",
    "white": "#ffffff",
}

_ZH_COLOR_KEYWORDS = {
    "紫": "purple",
    "蓝": "blue",
    "绿": "green",
    "橙": "orange",
    "粉": "pink",
    "红": "red",
    "黑": "black",
    "灰": "slate",
}

def _prompt_color_theme(prompt: str = "") -> tuple[str | None, dict]:
    text = str(prompt or "").lower()
    if not text:
        return None, {}
    for name, theme in _PROMPT_COLOR_THEMES.items():
        if re.search(rf"\b{re.escape(name)}\b", text):
            return name, theme
    hex_match = re.search(r"#[0-9a-fA-F]{6}\b", text)
    if hex_match:
        return "custom", {"accent": hex_match.group(0), "secondary": hex_match.group(0), "page": "#f9fafb", "surface": "#ffffff", "border": "#e5e7eb"}
    return None, {}

def _color_word_to_hex(word: str | None) -> str | None:
    if not word:
        return None
    value = str(word).strip().lower()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return value
    return _COLOR_KEYWORDS.get(value)

def _find_color_near(text: str, target_terms: tuple[str, ...]) -> tuple[str | None, str | None]:
    color_words = "|".join(re.escape(name) for name in _COLOR_KEYWORDS)
    target_words = "|".join(re.escape(term) for term in target_terms)
    patterns = (
        rf"\b(?P<color>{color_words}|#[0-9a-fA-F]{{6}})\b(?:\W+\w+){{0,4}}\W+\b(?P<target>{target_words})s?\b",
        rf"\b(?P<target>{target_words})s?\b(?:\W+\w+){{0,6}}\W+\b(?P<color>{color_words}|#[0-9a-fA-F]{{6}})\b",
    )
    clauses = re.split(r"[,.;\n]|(?:\s+\b(?:and|but|while|whereas)\b\s+)", text)
    for clause in [c.strip() for c in clauses if c.strip()]:
        for pattern in patterns:
            match = re.search(pattern, clause)
            if match:
                return match.group("color"), _color_word_to_hex(match.group("color"))
    return None, None

def _apply_scoped_color(overrides: dict, scope: str, color_name: str | None, color_hex: str | None) -> None:
    if not color_hex:
        return
    theme = _PROMPT_COLOR_THEMES.get(str(color_name or ""), {})
    secondary = theme.get("secondary", color_hex)
    page = theme.get("page", color_hex)
    border = theme.get("border", color_hex)
    if scope == "button":
        overrides.update({
            "button.primary.bg_hex": color_hex,
            "button.primary.border_hex": color_hex,
            "button.primary.text_hex": "#ffffff",
        })
        if color_name == "red":
            overrides.update({
                "button.danger.bg_hex": color_hex,
                "button.danger.border_hex": color_hex,
            })
    elif scope == "nav":
        overrides.update({
            "nav.bg_hex": color_hex,
            "nav.text_hex": "#ffffff",
        })
    elif scope == "header":
        overrides.update({
            "region.header.bg_hex": color_hex,
            "region.header.text_hex": "#ffffff",
        })
    elif scope == "footer":
        overrides.update({
            "region.footer.bg_hex": color_hex,
            "region.footer.text_hex": "#ffffff",
        })
    elif scope == "sidebar":
        overrides.update({
            "region.sidebar.bg_hex": page if color_name in {"blue", "purple", "pink", "rose", "green", "orange"} else color_hex,
            "region.sidebar.text_hex": "#ffffff" if color_name in {"black", "dark", "slate"} else overrides.get("page.body.text_hex", "#111827"),
        })
    elif scope == "background":
        overrides.update({
            "page.body.bg_hex": page,
            "page.bg.hex": page,
            "region.main.bg_hex": page,
        })
    elif scope == "main":
        overrides.update({"region.main.bg_hex": page if color_name in {"blue", "purple", "pink", "rose", "green", "orange"} else color_hex})
    elif scope == "card":
        overrides.update({
            "component.card.bg_hex": page if color_name in {"blue", "purple", "pink", "rose", "green", "orange"} else color_hex,
            "component.card.border_hex": border,
        })
    elif scope == "border":
        overrides.update({
            "region.border_hex": border,
            "region.border_strong_hex": color_hex,
            "component.card.border_hex": border,
            "input.border_hex": border,
            "table.border_hex": border,
        })
    elif scope == "text":
        overrides.update({
            "page.body.text_hex": color_hex,
            "text.primary.hex": color_hex,
        })
    elif scope == "muted":
        overrides.update({
            "color.text.muted_hex": color_hex,
            "text.muted.hex": color_hex,
        })
    elif scope == "input":
        overrides.update({
            "input.border_focus_hex": color_hex,
            "input.border_hex": border,
        })
    elif scope == "table":
        overrides.update({
            "table.header.bg_hex": page if color_name in {"blue", "purple", "pink", "rose", "green", "orange"} else color_hex,
            "table.border_hex": border,
            "table.row.hover_hex": page,
        })
    elif scope == "link":
        overrides.update({
            "button.link.text_hex": color_hex,
            "button.ghost.text_hex": color_hex,
        })
    elif scope == "badge":
        overrides.update({
            "badge.info.bg_hex": color_hex,
            "badge.info.text_hex": "#ffffff",
        })
    elif scope == "accent":
        overrides.update({
            "accent.hex": color_hex,
            "color.secondary.hex": secondary,
            "input.border_focus_hex": color_hex,
            "button.ghost.text_hex": color_hex,
            "button.link.text_hex": color_hex,
            "badge.info.bg_hex": color_hex,
        })

def _prompt_scoped_color_overrides(prompt: str = "") -> dict:
    text = str(prompt or "").lower()
    original = str(prompt or "")
    if not text and not original:
        return {}
    overrides: dict[str, str] = {}

    scopes = (
        ("button", ("button", "cta", "action")),
        ("nav", ("nav", "navbar", "navigation", "menu")),
        ("header", ("header", "topbar", "top bar")),
        ("footer", ("footer",)),
        ("sidebar", ("sidebar", "side nav", "side bar")),
        ("background", ("background", "page background", "body")),
        ("main", ("main", "content")),
        ("card", ("card", "cards", "panel", "tile")),
        ("border", ("border", "outline", "stroke")),
        ("text", ("text", "font", "copy")),
        ("muted", ("muted", "secondary text", "subtle text")),
        ("input", ("input", "field", "form field")),
        ("table", ("table", "grid")),
        ("link", ("link", "links")),
        ("badge", ("badge", "tag", "pill")),
        ("accent", ("accent", "primary color", "theme color")),
    )
    for scope, terms in scopes:
        color_name, color_hex = _find_color_near(text, terms)
        _apply_scoped_color(overrides, scope, color_name, color_hex)

    zh_scopes = {
        "按钮": "button",
        "按鈕": "button",
        "导航": "nav",
        "導覽": "nav",
        "菜单": "nav",
        "頁首": "header",
        "页首": "header",
        "头部": "header",
        "顶部": "header",
        "footer": "footer",
        "页脚": "footer",
        "頁腳": "footer",
        "侧边栏": "sidebar",
        "側邊欄": "sidebar",
        "背景": "background",
        "卡片": "card",
        "边框": "border",
        "邊框": "border",
        "文字": "text",
        "输入框": "input",
        "輸入框": "input",
        "表格": "table",
        "链接": "link",
        "連結": "link",
        "标签": "badge",
        "標籤": "badge",
    }
    for zh_term, scope in zh_scopes.items():
        if zh_term not in original:
            continue
        for zh_color, color_name in _ZH_COLOR_KEYWORDS.items():
            if zh_color in original:
                _apply_scoped_color(overrides, scope, color_name, _color_word_to_hex(color_name))
                break

    other_color_name = None
    other_hex = None
    color_words = "|".join(re.escape(name) for name in _COLOR_KEYWORDS)
    other_patterns = (
        rf"\b(?:other|rest|everything else|non[-\s]?button|not buttons?)\b(?:\W+\w+){{0,6}}\W+\b(?P<color>{color_words}|#[0-9a-fA-F]{{6}})\b",
        rf"\b(?P<color>{color_words}|#[0-9a-fA-F]{{6}})\b(?:\W+\w+){{0,6}}\W+\b(?:other|rest|everything else|non[-\s]?button|not buttons?)\b",
    )
    for pattern in other_patterns:
        match = re.search(pattern, text)
        if match:
            other_color_name = match.group("color")
            other_hex = _color_word_to_hex(other_color_name)
            break
    if not other_hex:
        for zh, color_name in _ZH_COLOR_KEYWORDS.items():
            if ("其他" in original or "其它" in original) and zh in original:
                other_color_name = color_name
                other_hex = _color_word_to_hex(color_name)
                break
    if other_hex:
        theme = _PROMPT_COLOR_THEMES.get(str(other_color_name), {})
        secondary = theme.get("secondary", other_hex)
        page = theme.get("page")
        border = theme.get("border")
        overrides.update({
            "accent.hex": other_hex,
            "color.secondary.hex": secondary,
            "region.header.bg_hex": other_hex,
            "region.footer.bg_hex": other_hex,
            "nav.bg_hex": other_hex,
            "button.ghost.text_hex": other_hex,
            "button.link.text_hex": other_hex,
            "input.border_focus_hex": other_hex,
            "badge.info.bg_hex": other_hex,
        })
        if page:
            overrides.setdefault("page.body.bg_hex", page)
            overrides.setdefault("page.bg.hex", page)
        if border:
            overrides.setdefault("region.border_hex", border)
            overrides.setdefault("region.border_strong_hex", border)
    return {key: value for key, value in overrides.items() if value}

def _prompt_is_button_only_color(prompt: str = "") -> bool:
    text = str(prompt or "").lower()
    if not text:
        return False
    if _prompt_color_scope_lock(prompt) == "button":
        return True
    _, button_hex = _find_color_near(text, ("button", "cta", "action"))
    if not button_hex:
        return False
    has_global_target = any(term in text for term in (
        "theme", "page", "background", "header", "footer", "nav", "navbar",
        "sidebar", "all colors", "whole", "entire", "everything", "other",
        "rest", "non-button", "not button",
    ))
    return not has_global_target

def _prompt_color_scope_lock(prompt: str = "") -> str | None:
    """Detect prompts that intentionally constrain a color change to one scope.

    This is intentionally conservative: when the user says "keep other colors the
    same" and asks only for button color, variant planning must not recolor the
    global accent/header/nav/footer tokens later in the pipeline.
    """
    text = str(prompt or "").lower()
    original = str(prompt or "")
    if not text and not original:
        return None

    _, button_hex = _find_color_near(text, ("button", "buttons", "cta", "action"))
    has_button_term = any(term in text for term in ("button", "buttons", "cta", "action")) or ("\u6309\u94ae" in original)
    if not button_hex or not has_button_term:
        return None

    preserve_other = any(phrase in text for phrase in (
        "keep other color",
        "keep other colors",
        "keep the other color",
        "keep the other colors",
        "other color the same",
        "other colors the same",
        "other colours the same",
        "rest color the same",
        "rest colors the same",
        "everything else the same",
        "leave other colors",
        "leave the other colors",
        "do not change other",
        "don't change other",
        "dont change other",
        "without changing other",
    ))
    only_button = bool(re.search(
        r"\b(?:only|just)\b(?:\W+\w+){0,8}\W+\b(?:button|buttons|cta|action)s?\b"
        r"|\b(?:button|buttons|cta|action)s?\b(?:\W+\w+){0,8}\W+\b(?:only|just)\b",
        text,
    ))
    preserve_other = preserve_other or (
        ("\u5176\u4ed6" in original or "\u5176\u5b83" in original)
        and ("\u4e0d\u53d8" in original or "\u4fdd\u6301" in original or "\u4e00\u6837" in original)
    )
    only_button = only_button or ("\u53ea" in original and "\u6309\u94ae" in original)
    return "button" if preserve_other or only_button else None

def compile_prompt_intent(prompt: str = "") -> dict:
    text = str(prompt or "").lower()
    original_prompt = str(prompt or "")
    has_image_word = any(term in text for term in ("image", "picture", "photo", "media", "banner")) or any(
        term in original_prompt for term in ("\u56fe\u7247", "\u56fe\u50cf", "\u7167\u7247", "\u6d77\u62a5")
    )
    has_header_word = any(term in text for term in ("header", "top bar", "banner")) or any(
        term in original_prompt for term in ("\u9875\u5934", "\u5934\u90e8", "\u9876\u90e8", "\u6a2a\u5e45")
    )
    header_media = has_image_word and has_header_word
    color_overrides = _prompt_scoped_color_overrides(prompt)
    color_scope_lock = _prompt_color_scope_lock(prompt)
    layout_intent = _prompt_layout_traits(prompt)
    component_intent: dict[str, str] = {}
    data_intent = {
        "hide_id_fields": any(term in text for term in (
            "hide id", "hide ids", "hide internal", "no id fields", "without ids", "不要id", "隐藏id", "隱藏id",
        )),
        "table_targets": [],
        "single_card_media": header_media or any(term in text for term in (
            "single card", "one card", "single image card", "image only", "only image", "media only",
            "limit 1 card", "limit one card",
        )) or (
            ("card" in text or "卡片" in str(prompt or ""))
            and ("image" in text or "media" in text or "图片" in str(prompt or "") or "照片" in str(prompt or ""))
            and ("single" in text or "one" in text or "only" in text or "单个" in str(prompt or "") or "一张" in str(prompt or "") or "只" in str(prompt or ""))
        ),
        "media_position": "header" if header_media else "",
    }
    data_intent["query_hints"] = {}
    interaction_intent = {
        "delete": "default",
        "multi_delete": False,
        "navigation_required": any(term in text for term in ("navigate", "navigation", "link to", "go to", "跳转", "导航")),
    }

    data_layouts = ("table", "card", "cards", "gallery", "list", "form", "detail")
    target_patterns = (
        r"\b(?P<target>[a-zA-Z][\w\s-]{1,40}?)\s+(?:as|in|with|use|using|into|to)\s+(?P<layout>table|cards?|gallery|list|form|detail)\b",
        r"\b(?P<layout>table|cards?|gallery|list|form|detail)\s+(?:for|on|of)\s+(?P<target>[a-zA-Z][\w\s-]{1,40}?)\b",
    )
    for pattern in target_patterns:
        for match in re.finditer(pattern, text):
            target = re.sub(r"\s+", " ", match.group("target")).strip(" .,:;")
            layout = match.group("layout")
            if layout == "cards":
                layout = "card"
            if target and layout in data_layouts:
                component_intent[target] = layout
                if layout == "table":
                    data_intent["table_targets"].append(target)

    if any(term in text for term in ("all sections table", "everything table", "all data as table", "所有表格")):
        component_intent["*"] = "table"
    elif any(term in text for term in ("all cards", "everything card", "all data as cards", "所有卡片")):
        component_intent["*"] = "card"

    if any(term in text for term in ("no delete", "disable delete", "hide delete", "without delete", "不要删除", "禁用删除")):
        interaction_intent["delete"] = "disabled"
    elif any(term in text for term in ("enable delete", "allow delete", "show delete", "可以删除")):
        interaction_intent["delete"] = "enabled"
    if any(term in text for term in ("multi delete", "bulk delete", "delete selected", "batch delete", "多选删除", "批量删除")):
        interaction_intent["multi_delete"] = True
        interaction_intent["delete"] = "enabled"

    if any(term in text for term in ("sidebar left", "left sidebar", "left nav", "左侧栏", "左侧导航")):
        layout_intent["sidebar"] = True
        layout_intent["sidebar_side"] = "left"
    elif any(term in text for term in ("sidebar right", "right sidebar", "right nav", "右侧栏", "右侧导航")):
        layout_intent["sidebar"] = True
        layout_intent["sidebar_side"] = "right"
    if any(term in text for term in ("main full", "full main", "main full width", "full-width main", "主区域全宽")):
        layout_intent["full"] = True
        layout_intent["main_width"] = "full"
    if any(term in text for term in ("header full", "full header", "页首全宽")):
        layout_intent["header_width"] = "full"
    if any(term in text for term in ("footer full", "full footer", "页脚全宽")):
        layout_intent["footer_width"] = "full"

    query_hints = data_intent["query_hints"]
    if any(term in text for term in ("latest", "newest", "recent", "most recent", "last item")):
        query_hints["order"] = "latest"
    elif any(term in text for term in ("oldest", "first item", "earliest")):
        query_hints["order"] = "oldest"
    if any(term in text for term in ("active only", "only active", "enabled only")):
        query_hints.setdefault("filters", []).append({"kind": "active", "value": "true"})
    for status_value in ("approved", "pending", "rejected", "accepted", "completed", "open", "closed"):
        if re.search(rf"\b(?:only\s+)?{status_value}\b", text):
            query_hints.setdefault("filters", []).append({"kind": "status", "value": status_value})
    for match in re.finditer(r"\b(?P<field>[a-zA-Z_][\w]*)\s*(?:=|equals|is)\s*['\"]?(?P<value>[a-zA-Z0-9_. -]{1,40})['\"]?", text):
        field = match.group("field").strip()
        value = match.group("value").strip(" .,'\"")
        if field and value and field not in {"button", "color", "style", "layout", "card", "image"}:
            query_hints.setdefault("filters", []).append({"kind": "field", "field": field, "value": value})

    return {
        "version": 1,
        "source": prompt or "",
        "colorIntent": color_overrides,
        "colorPolicy": {
            "scope_lock": color_scope_lock,
            "preserve_other_colors": bool(color_scope_lock),
        },
        "layoutIntent": layout_intent,
        "componentIntent": component_intent,
        "dataIntent": data_intent,
        "interactionIntent": interaction_intent,
    }

def _intent_target_matches(section: dict, target: str) -> bool:
    if target == "*":
        return bool(section.get("primary_model")) or section.get("layout") in {"card", "list", "table", "detail", "gallery", "form"}
    haystack = " ".join(str(section.get(key, "")) for key in ("id", "name", "primary_model", "class", "role", "layout")).lower()
    needle = re.sub(r"[\s_-]+", "", str(target or "").lower())
    compact_haystack = re.sub(r"[\s_-]+", "", haystack)
    return bool(needle and (needle in compact_haystack or str(target).lower() in haystack))

def apply_hard_constraints(pages: list, sections: list, tokens: dict, styling: dict, prompt_intent: dict) -> tuple[list, list, dict, dict]:
    pages = copy.deepcopy(pages or [])
    sections = copy.deepcopy(sections or [])
    tokens = dict(tokens or {})
    styling = dict(styling or {})
    intent = prompt_intent or {}

    color_intent = intent.get("colorIntent") or {}
    if color_intent:
        tokens.update(color_intent)

    layout_intent = intent.get("layoutIntent") or {}
    if layout_intent:
        for page in pages:
            layout = _page_layout_dict(page)
            if layout_intent.get("main_width"):
                layout["main_width"] = layout_intent["main_width"]
            elif layout_intent.get("full"):
                layout["main_width"] = "full"
            if layout_intent.get("header_width"):
                layout["header_width"] = layout_intent["header_width"]
            if layout_intent.get("footer_width"):
                layout["footer_width"] = layout_intent["footer_width"]
            if layout_intent.get("hero_width"):
                layout["hero_width"] = layout_intent["hero_width"]
            page["layout"] = layout
        if layout_intent.get("sidebar") and layout_intent.get("sidebar_side"):
            side = layout_intent.get("sidebar_side") or "left"
            nav_sections = [s for s in sections if _normalize_layout_alias(s.get("layout")) in {"site-nav", "nav-links", "nav-bar"} or s.get("component") == "NavBar"]
            for nav in nav_sections[:1]:
                nav["position"] = "sidebar"
                nav["layout"] = "site-nav"
                nav["component"] = "NavBar"
                style = dict(nav.get("style") or {})
                style["sidebar_side"] = side
                style.setdefault("sidebar_width", 3)
                nav["style"] = style

    component_intent = intent.get("componentIntent") or {}
    if component_intent:
        for section in sections:
            for target, layout in component_intent.items():
                if _intent_target_matches(section, target):
                    section["layout"] = layout
                    section["component"] = _component_for_layout(section, layout)
                    if layout == "table":
                        section["col_span"] = 12
                    style = dict(section.get("style") or {})
                    if layout in {"gallery", "card"}:
                        style.setdefault("columns", "3" if layout == "gallery" else "2")
                    section["style"] = style

    data_intent = intent.get("dataIntent") or {}
    hide_ids = data_intent.get("hide_id_fields")
    if data_intent.get("single_card_media"):
        converted_media_card = False
        for section in sections:
            if converted_media_card or not section.get("primary_model"):
                continue
            attrs = section.get("attributes") or []
            media_attr = next(
                (
                    _attr_name(attr)
                    for attr in attrs
                    if _attr_name(attr) and _field_kind(_attr_name(attr), _attr_type(attr)) == "media"
                ),
                "",
            )
            if not media_attr:
                continue
            attr_names = [_attr_name(attr) for attr in attrs if _attr_name(attr)]
            section["layout"] = "card"
            section["component"] = "ImageCard"
            if data_intent.get("media_position") == "header":
                section["position"] = "header"
                section["col_span"] = 12
            else:
                section["col_span"] = int(section.get("col_span") or 12)
            query = dict(section.get("query") or {})
            query["limit"] = 1
            query_hints = data_intent.get("query_hints") or {}
            attr_lookup = {name.lower(): name for name in attr_names}

            def _first_attr(candidates: tuple[str, ...]) -> str:
                for exact in candidates:
                    if exact in attr_lookup:
                        return attr_lookup[exact]
                for attr_name in attr_names:
                    low = attr_name.lower()
                    if any(candidate in low for candidate in candidates):
                        return attr_name
                return ""

            if query_hints.get("order"):
                order_field = _first_attr(("created_at", "updated_at", "date", "time", "timestamp", "id"))
                if order_field:
                    direction = "asc" if query_hints.get("order") == "oldest" else "desc"
                    query["order_by"] = [{"field": order_field, "direction": direction}]

            query_filters = list(query.get("filters") or [])

            def _append_filter(field: str, value: str, operator: str = "eq") -> None:
                if not field:
                    return
                item = {"field": field, "operator": operator, "value": str(value)}
                if item not in query_filters:
                    query_filters.append(item)

            for filter_hint in query_hints.get("filters") or []:
                kind = filter_hint.get("kind")
                if kind == "field":
                    field = attr_lookup.get(str(filter_hint.get("field") or "").lower())
                    _append_filter(field, filter_hint.get("value", ""))
                elif kind == "active":
                    field = _first_attr(("is_active", "active", "enabled", "is_enabled"))
                    _append_filter(field, filter_hint.get("value", "true"))
                elif kind == "status":
                    field = _first_attr(("status", "state", "decision"))
                    _append_filter(field, filter_hint.get("value", ""))
            if query_filters:
                query["filters"] = query_filters
            section["query"] = query
            style = dict(section.get("style") or {})
            style.update({
                "display_mode": "banner" if data_intent.get("media_position") == "header" else "grid",
                "card_style": "default",
                "columns": "1",
                "image_position": "top",
                "image_size": "lg",
            })
            if data_intent.get("media_position") == "header":
                style["header_style"] = "hidden"
            section["style"] = style
            hidden = [name for name in attr_names if name != media_attr]
            section["field_layout"] = {
                "image": media_attr,
                "hidden": hidden,
                "field_styles": {
                    media_attr: {"col_span": 12, "height": "lg", "label": "hidden"},
                    **{name: {"visible": "hidden"} for name in hidden},
                },
            }
            ops = _normalize_section_operations(section.get("operations"))
            ops["create"] = False
            ops["update"] = False
            ops["delete"] = False
            section["operations"] = ops
            converted_media_card = True
    interaction_intent = intent.get("interactionIntent") or {}
    for section in sections:
        if hide_ids and section.get("attributes"):
            attrs = [a.get("name", a) if isinstance(a, dict) else a for a in section.get("attributes", [])]
            hidden = [field for field in attrs if re.search(r"(^id$|_id$|id$|uuid|pk|internal)", str(field), re.I)]
            if hidden:
                layout = dict(section.get("field_layout") or {})
                layout["hidden"] = sorted(set([*(layout.get("hidden") or []), *hidden]))
                field_styles = dict(layout.get("field_styles") or {})
                for field in hidden:
                    field_styles[field] = {**(field_styles.get(field) or {}), "visible": "hidden"}
                layout["field_styles"] = field_styles
                section["field_layout"] = layout
        ops = _normalize_section_operations(section.get("operations"))
        if interaction_intent.get("delete") == "disabled":
            ops["delete"] = False
        elif interaction_intent.get("delete") == "enabled" and section.get("primary_model"):
            ops["delete"] = True
        if interaction_intent.get("multi_delete") and section.get("primary_model"):
            ops["select"] = True
            ops["delete"] = True
            style = dict(section.get("style") or {})
            style["multi_select"] = True
            section["style"] = style
        section["operations"] = ops
        if intent.get("interactionIntent", {}).get("navigation_required") and section.get("layout") in {"card", "list", "table", "gallery"}:
            section.setdefault("behavior", {})

    return pages, sections, tokens, styling

def _apply_prompt_style_overrides(tokens: dict, prompt: str = "") -> dict:
    color_name, theme = _prompt_color_theme(prompt)
    scoped_overrides = _prompt_scoped_color_overrides(prompt)
    if not theme or _prompt_is_button_only_color(prompt):
        if scoped_overrides:
            tokens = dict(tokens or {})
            tokens.update(scoped_overrides)
            _expand_design_tokens(tokens)
        return tokens
    if not theme:
        return tokens
    tokens = dict(tokens or {})
    variant_index = str(tokens.get("design.variant_index", ""))
    accent = theme["accent"]
    secondary = theme.get("secondary", accent)
    page = theme.get("page", tokens.get("page.body.bg_hex", "#f9fafb"))
    surface = theme.get("surface", tokens.get("region.main.bg_hex", "#ffffff"))
    border = theme.get("border", tokens.get("region.border_hex", "#e5e7eb"))
    text = theme.get("text", tokens.get("page.body.text_hex", "#111827"))
    muted = theme.get("muted", tokens.get("color.text.muted_hex", "#6b7280"))

    tokens.update({
        "accent.hex": accent,
        "color.secondary.hex": secondary,
        "page.body.bg_hex": page,
        "page.bg.hex": page,
        "region.main.bg_hex": surface,
        "region.sidebar.bg_hex": surface,
        "region.footer.bg_hex": accent,
        "region.border_hex": border,
        "region.border_strong_hex": border,
        "page.body.text_hex": text,
        "color.text.muted_hex": muted,
        "region.header.bg_hex": accent,
        "region.header.bg": f"bg-[{accent}]",
        "nav.bg_hex": accent,
        "nav.text_hex": "#ffffff",
        "button.primary.bg_hex": accent,
        "button.primary.border_hex": accent,
        "button.ghost.text_hex": accent,
        "button.link.text_hex": accent,
        "input.border_focus_hex": accent,
        "badge.info.bg_hex": accent,
        "design.prompt_color": color_name or "",
    })
    if variant_index in {"1", "2"}:
        if color_name in {"pink", "rose"}:
            accent = {"1": "#be185d", "2": "#ec4899"}[variant_index]
            secondary = {"1": "#f472b6", "2": "#fbcfe8"}[variant_index]
        elif color_name in {"purple", "violet"}:
            accent = {"1": "#6d28d9", "2": "#a855f7"}[variant_index]
            secondary = {"1": "#a78bfa", "2": "#ddd6fe"}[variant_index]
        else:
            accent = {"1": theme.get("accent", "#2563eb"), "2": theme.get("secondary", theme.get("accent", "#2563eb"))}[variant_index]
            secondary = theme.get("secondary", accent)
        tokens.update({
            "accent.hex": accent,
            "color.secondary.hex": secondary,
            "region.header.bg_hex": accent,
            "region.footer.bg_hex": accent,
            "nav.bg_hex": accent,
            "button.primary.bg_hex": accent,
            "button.primary.border_hex": accent,
            "button.ghost.text_hex": accent,
            "input.border_focus_hex": accent,
            "design.variant_index": variant_index,
        })
    if scoped_overrides:
        tokens.update(scoped_overrides)
    _expand_design_tokens(tokens)
    return tokens

def _prompt_styling_overrides(prompt: str = "") -> dict:
    if _prompt_color_scope_lock(prompt):
        return {}
    color_name, theme = _prompt_color_theme(prompt)
    if not theme:
        return {}
    return {
        "accentColor": theme["accent"],
        "backgroundColor": theme.get("page", "#f9fafb"),
        "textColor": theme.get("text", "#111827"),
        "selectedStyle": color_name or "custom",
    }

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

def apply_design_system_to_interface_tool_func(interface_id: str, spec_name: str = "minimal.md", prompt: str = "") -> str:
    """
    Updates the specified Interface with design tokens from a template in the library.
    Ideal for quickly switching between themes (e.g. switching to ecommerce.md).
    Pass the original user prompt so explicit color requests like "purple style" override the spec palette.
    """
    try:
        safe_name = os.path.basename(spec_name)
        content = _read_design_spec(safe_name)
        tokens = _apply_prompt_style_overrides(_parse_design_md_to_tokens(content), prompt)
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
    return spec_name, _apply_prompt_style_overrides(
        _tokens_for_design_spec(spec_name, iface.get("name") or "App"),
        prompt,
    )

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
            result.append({
                "spec_name": spec,
                "tokens": _apply_prompt_style_overrides(
                    _tokens_for_design_spec(spec, iface.get("name") or "App"),
                    prompt,
                ),
            })
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

def _name_tokens(value: str) -> set[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value or ""))
    tokens = {
        token
        for token in re.split(r"[^A-Za-z0-9]+", spaced.lower())
        if len(token) > 1
    }
    singulars = {token[:-1] for token in tokens if len(token) > 3 and token.endswith("s")}
    return tokens | singulars

def _rank_models_for_text(text: str, models: list[str], prefer_collections: bool = False) -> list[str]:
    text_tokens = _name_tokens(text)
    ranked = []
    for index, model in enumerate(models or []):
        model_tokens = _name_tokens(model)
        if not model_tokens:
            continue
        overlap = len(text_tokens & model_tokens)
        compact_model = re.sub(r"[^a-z0-9]+", "", str(model).lower())
        compact_text = re.sub(r"[^a-z0-9]+", "", str(text).lower())
        substring = 2 if compact_model and compact_model in compact_text else 0
        collection_bonus = 1 if prefer_collections and _is_child_collection_model(model, text) else 0
        ranked.append((overlap + substring + collection_bonus, -index, model))
    ranked.sort(reverse=True)
    return [model for score, _index, model in ranked if score > 0]

def _infer_usecase_model(name: str, explicit_classes: list[str], classifiers: dict[str, dict], model_names: set[str]) -> str:
    for ref in explicit_classes:
        cls = classifiers.get(ref, {})
        cname = cls.get("name") or ref
        if cname in model_names:
            return cname
    ranked = _rank_models_for_text(name, sorted(model_names, key=len, reverse=True))
    return ranked[0] if ranked else ""

def _humanize_action_label(name: str, fallback: str = "Start") -> str:
    raw = re.sub(r"[_-]+", " ", str(name or "")).strip()
    if not raw:
        return fallback
    cleaned = re.sub(r"^(manage|view|track|write|browse|search|review)\s+", "", raw, flags=re.I).strip()
    if re.search(r"\b(apply|application|request|submit|onboard|register|book|schedule|reserve|approval|claim|ticket|case|workflow|process)\b", raw, re.I):
        return "Start"
    return cleaned[:1].upper() + cleaned[1:] if cleaned else fallback

def _is_child_collection_model(model_name: str, page_terms: str = "") -> bool:
    name_l = str(model_name or "").lower()
    if not name_l:
        return False
    if any(term in _name_tokens(name_l) for term in ("item", "line", "entry", "row", "detail", "selection", "membership", "mapping", "association")):
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
    ranked_models = _rank_models_for_text(name, class_names)

    def best_model(default: str = "") -> str:
        return primary or (ranked_models[0] if ranked_models else (class_names[0] if class_names else default))

    if any(term in name_l for term in ("system process", "background", "automated", "notification")):
        return {"role": "background", "page_id": "", "page_name": "", "page_model": primary, "operation_kind": "background"}

    if workflow_entry:
        page_model = best_model()
        page_id = _section_id(page_model or name)
        return {
            "role": "workflow_entry",
            "page_id": page_id,
            "page_name": _page_name(page_id),
            "page_model": page_model,
            "operation_kind": "start_workflow",
        }

    inline_terms = ("add", "remove", "delete", "update", "select", "write", "review", "rate")
    if any(term in name_l for term in inline_terms) and "manage" not in name_l:
        page_model = best_model()
        target_model = next((m for m in ranked_models + class_names if m and m != page_model), page_model)
        operation_kind = "delete" if any(term in name_l for term in ("remove", "delete")) else (
            "create_related" if target_model and target_model != page_model and any(term in name_l for term in ("add", "write", "create", "select")) else "object_operation"
        )
        return {
            "role": "inline_operation",
            "page_id": _section_id(page_model or name),
            "page_name": _page_name(page_model or name),
            "page_model": page_model,
            "operation_kind": operation_kind,
            "target_model": target_model,
        }

    if any(term in name_l for term in ("browse", "search", "catalog", "list", "overview", "directory")):
        page_model = best_model()
        page_id = _plural_page_id(page_model) if page_model else _section_id(name)
        return {"role": "collection_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_collection"}

    if "detail" in name_l or name_l.startswith("view "):
        page_model = best_model()
        page_id = f"{_section_id(page_model)}_detail" if page_model else _section_id(name)
        return {"role": "detail_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_detail"}

    if "track" in name_l or "history" in name_l:
        page_model = best_model()
        page_id = _plural_page_id(page_model) if page_model else _section_id(name)
        return {"role": "collection_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_collection"}

    if any(term in name_l for term in ("account", "profile", "settings")):
        page_model = best_model()
        page_id = _section_id(page_model or name)
        return {"role": "object_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "manage_object"}

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
        "apply", "application", "request", "submit", "book", "schedule",
        "reserve", "register", "onboard", "approve", "approval", "claim", "ticket", "case",
        "process", "workflow"
    }
    if any(term in name_l for term in intent_terms):
        return True
    return False

def _infer_usecase_permissions(name: str) -> list[str]:
    name_l = str(name or "").lower()
    perms = {"view"}
    if any(term in name_l for term in ("add", "create", "write", "submit")):
        perms.add("create")
    if any(term in name_l for term in ("manage", "update", "edit", "select", "enter", "process", "confirm", "track")):
        perms.add("update")
    if "manage" in name_l and not any(term in name_l for term in ("account", "profile", "settings", "password")):
        if any(term in name_l for term in ("item", "items", "record", "records", "entry", "entries", "line", "lines")):
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
    icon_actions = [pid for pid in nav_pages if any(term in pid for term in ("account", "profile", "settings", "search"))]
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
        ranked = _rank_models_for_text(name_l, explicit_step_models, prefer_collections=True)
        return (ranked + [m for m in explicit_step_models if m not in ranked])[:2]
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

    prefer_collections = any(term in _name_tokens(name_l) for term in ("add", "select", "choose", "list", "review", "manage"))
    ranked = _rank_models_for_text(name_l, related, prefer_collections=prefer_collections)
    return ranked[:2] or related[:1]

def _activity_layout_for_step(step_name: str, model: str) -> str:
    name_tokens = _name_tokens(step_name)
    if any(term in name_tokens for term in ("enter", "select", "choose", "provide", "submit", "create", "update", "edit", "write", "upload")):
        return "form"
    if _is_child_collection_model(model, step_name) or any(term in name_tokens for term in ("list", "browse", "review", "manage", "track", "history")):
        return "list"
    if any(term in name_tokens for term in ("confirmation", "confirm", "detail", "summary")):
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

_LAYOUT_ALIASES = {
    "nav": "nav-links",
    "navigation": "nav-links",
    "navbar": "nav-links",
    "side-nav": "nav-links",
    "top-nav": "nav-links",
    "footer-links": "link-grid",
    "footer-brand": "brand-strip",
    "service-strip": "service-bar",
}

_HEADER_TEMPLATE_LAYOUTS = {
    "promo-bar", "logo", "search-bar", "icon-actions", "nav-links", "main-header", "minimal-header",
    "commerce-header", "dashboard-header", "split-header", "app-header", "compact-header", "mega-header",
    "hero-header", "tabbed-header", "glass-header", "command-header", "site-nav",
}
_HEADER_SHELL_LAYOUTS = {
    "main-header", "minimal-header", "commerce-header", "dashboard-header",
    "split-header", "app-header", "compact-header", "mega-header", "hero-header", "tabbed-header",
    "glass-header", "command-header",
}
_HEADER_ELEMENT_LAYOUTS = {"logo", "search-bar", "icon-actions"}
_HEADER_NAV_LAYOUTS = {
    "nav-links", "site-nav", "nav-bar", "main-header", "commerce-header", "dashboard-header",
    "split-header", "app-header", "compact-header", "mega-header", "hero-header", "tabbed-header",
    "glass-header", "command-header",
}
_PAGE_NAV_LAYOUTS = {"nav-links", "site-nav", "nav-bar", "tabbed-header", "mega-header"}
_FOOTER_TEMPLATE_LAYOUTS = {
    "service-bar", "link-grid", "brand-strip", "compact-footer", "legal-footer",
    "newsletter-footer", "social-footer", "mega-footer", "site-footer", "split-footer", "app-footer",
    "cta-footer", "minimal-footer",
}
_CHROME_TEMPLATE_LAYOUTS = _HEADER_TEMPLATE_LAYOUTS | _FOOTER_TEMPLATE_LAYOUTS

def _normalize_layout_alias(layout) -> str:
    if isinstance(layout, list):
        raw_values = layout
    else:
        raw_values = re.split(r"[,|/]+", str(layout or ""))
    values = [str(value or "").strip() for value in raw_values if str(value or "").strip()]
    for value in values:
        normalized = _LAYOUT_ALIASES.get(value, value)
        if normalized in _CHROME_TEMPLATE_LAYOUTS or normalized in {"card", "list", "table", "detail", "gallery", "filter", "form", "activity_action", "activity_start", "activity_tasks"}:
            return normalized
    value = values[0] if values else ""
    return _LAYOUT_ALIASES.get(value, value)

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
        style["list_style"] = "default"
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
        "query": {},
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

def _normalize_chrome_sections(sections: list) -> list:
    """Keep header/footer/navigation chrome out of workflow/action rendering paths."""
    normalized = []
    for section in sections or []:
        section = dict(section)
        layout = _normalize_layout_alias(section.get("layout"))
        role = str(section.get("role") or "").lower()
        position = section.get("position")
        is_chrome = (
            layout in _CHROME_TEMPLATE_LAYOUTS
            or position in {"header", "footer"}
            or role in {"header", "footer", "navigation", "nav", "brand"}
        )
        if is_chrome:
            # If the agent assigned a data/action layout to a chrome position, replace with
            # the positional default so _infer_section_component returns the right component.
            if layout not in _CHROME_TEMPLATE_LAYOUTS:
                layout = "site-footer" if position == "footer" else "main-header"
            section["layout"] = layout
            section["primary_model"] = ""
            section["class"] = ""
            section["attributes"] = []
            section["operations"] = {"create": False, "update": False, "delete": False, "select": False}
            section.pop("type", None)
            for key in ("workflow", "workflow_action", "target_page", "targetPage"):
                section.pop(key, None)
            # Clear any stale component so _infer_section_component runs fresh from layout.
            section.pop("component", None)
            section["component"] = _infer_section_component(section)
        normalized.append(section)
    return normalized

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
    sections = _normalize_chrome_sections(_normalize_activity_action_sections(pages, sections)); data["pages"] = pages; data["sections"] = sections
    return data

def _page_type_value(page: dict) -> str:
    page_type = page.get("type")
    if isinstance(page_type, dict):
        return str(page_type.get("value") or "").strip().lower()
    return str(page_type or "").strip().lower()

def _infer_page_type_value(page: dict) -> str:
    explicit = _page_type_value(page)
    if explicit in {"normal", "activity"}:
        return explicit
    action = page.get("action")
    page_key = f"{page.get('id', '')} {page.get('name', '')} {page.get('display_name', '')}".lower()
    if action or "workflow" in page_key:
        return "activity"
    return "normal"

def _canonical_page_type(value: str) -> dict:
    if value == "activity":
        return {"value": "activity", "label": "Activity"}
    return {"value": "normal", "label": "Normal"}

def _ref_id(ref) -> str:
    return str(ref.get("value") if isinstance(ref, dict) else ref or "")

def _navigation_methods(names: list[str]) -> list[dict]:
    return [
        {"name": str(name), "label": str(name).replace("_", " "), "action": "navigate"}
        for name in names
        if name
    ]

def _workflow_icon_links(usecase_navigation: dict, page_by_id: dict | None = None) -> list[dict]:
    links = []
    seen = set()
    page_by_id = page_by_id or {}
    for entry in (usecase_navigation or {}).get("workflow_entry_points") or []:
        page_id = _section_id(entry.get("page_id") or entry.get("page_name"))
        if not page_id or page_id in seen:
            continue
        page = page_by_id.get(page_id) or {}
        page_name = page.get("name") or entry.get("page_name") or _page_name(page_id)
        label = entry.get("button_label") or entry.get("label") or entry.get("usecase_name") or "Start"
        links.append({"page": page_name, "label": label, "icon": "task"})
        seen.add(page_id)
    return links

def _infer_section_component(section: dict) -> str:
    """
    Generically infers a suitable high-fidelity component name based on 
    layout and model characteristics, avoiding app-specific hardcoding.
    """
    component = section.get("component")
    if component:
        return str(component)
    
    layout = _normalize_layout_alias(section.get("layout"))
    role = str(section.get("role") or "")
    model_name = str(section.get("primary_model") or section.get("class") or "").lower()
    attrs = {str(a.get("name") if isinstance(a, dict) else a).lower() for a in section.get("attributes", [])}
    
    # Generic rules based on data traits
    has_image = any(term in attrs for term in ("image", "img", "url", "avatar", "photo", "media"))
    is_person = any(term in model_name for term in ("user", "customer", "employee", "doctor", "member", "actor"))
    
    if layout == "logo": return "Logo"
    if layout == "search-bar": return "SearchBar"
    if layout == "icon-actions": return "IconActions"
    if layout in _FOOTER_TEMPLATE_LAYOUTS: return "FooterTemplate"
    if layout in _HEADER_TEMPLATE_LAYOUTS and layout not in {"logo", "search-bar", "icon-actions", "site-nav", "nav-links"}:
        return "HeaderTemplate"
    if layout in {"site-nav", "nav-links", "nav-bar"}: return "NavBar"
    
    if layout == "form":
        if any(term in model_name for term in ("address", "location")): return "AddressForm"
        if any(term in model_name for term in ("payment", "card", "billing")): return "PaymentForm"
        return "ObjectForm"
        
    if layout == "gallery" or layout == "card":
        if has_image: return "ImageCardGrid" if layout == "gallery" else "ImageCard"
        if is_person: return "PersonCardGrid"
        return "ObjectCardGrid"
        
    if layout == "detail":
        return "ObjectDetailPanel" if not has_image else "MediaDetailPanel"
        
    if layout == "table": return "DataTable"
    if layout == "list": return "ObjectList"
    
    return "SectionPanel"

def _field_layout_field_refs(field_layout) -> set[str]:
    refs = set()
    if not isinstance(field_layout, dict):
        return refs
    slot_keys = {"image", "video", "media", "avatar", "hero", "title", "subtitle", "primary", "price", "description", "count"}
    list_keys = {"secondary", "badges", "meta", "facts", "fields", "hidden"}
    for key, value in field_layout.items():
        if key in slot_keys and isinstance(value, str) and value:
            refs.add(value)
        elif key in list_keys and isinstance(value, list):
            refs.update(str(v) for v in value if isinstance(v, str) and v)
        elif key == "columns" and isinstance(value, list):
            for column in value:
                if isinstance(column, dict) and column.get("field"):
                    refs.add(str(column["field"]))
        elif key == "groups" and isinstance(value, list):
            for group in value:
                if isinstance(group, dict) and isinstance(group.get("fields"), list):
                    refs.update(str(v) for v in group["fields"] if isinstance(v, str) and v)
        elif key == "field_styles" and isinstance(value, dict):
            refs.update(str(field) for field in value.keys() if field)
    return refs

_FIELD_SLOT_MAP = {
    "card": {"image", "video", "media", "title", "subtitle", "primary", "secondary", "hidden"},
    "gallery": {"image", "video", "media", "title", "subtitle", "primary", "secondary", "hidden"},
    "list": {"columns", "hidden"},
    "table": {"columns", "hidden"},
    "detail": {"image", "video", "media", "title", "hero", "fields", "hidden"},
    "form": {"fields", "hidden"},
    "filter": {"fields", "hidden"},
}
_COMPONENT_FIELD_SLOT_MAP = {
    "ProductCardGrid": _FIELD_SLOT_MAP["card"],
    "CategoryTileGrid": {"image", "title", "subtitle", "secondary", "hidden"},
    "PersonCardGrid": {"image", "title", "subtitle", "secondary", "hidden"},
    "CardGrid": _FIELD_SLOT_MAP["card"],
    "DataTable": _FIELD_SLOT_MAP["table"],
    "ObjectList": _FIELD_SLOT_MAP["list"],
    "LineItemList": _FIELD_SLOT_MAP["list"],
    "RelatedObjectList": _FIELD_SLOT_MAP["list"],
    "ProductDetailPanel": _FIELD_SLOT_MAP["detail"],
    "DetailPanel": _FIELD_SLOT_MAP["detail"],
    "SummaryPanel": {"title", "fields", "hidden"},
    "ObjectForm": _FIELD_SLOT_MAP["form"],
    "AddressForm": _FIELD_SLOT_MAP["form"],
    "PaymentMethodForm": _FIELD_SLOT_MAP["form"],
    "ReviewForm": _FIELD_SLOT_MAP["form"],
    "FilterPanel": _FIELD_SLOT_MAP["filter"],
    "SearchBar": _FIELD_SLOT_MAP["filter"],
    "Logo": set(),
    "BrandLockup": set(),
    "ImageLogo": set(),
    "IconActions": set(),
    "SiteFooter": set(),
    "FooterLinkGrid": set(),
}

def _attr_name(attr) -> str:
    return str(attr.get("name") if isinstance(attr, dict) else attr or "")

def _attr_type(attr) -> str:
    return str(attr.get("type") if isinstance(attr, dict) else "").lower()

def _field_kind(name: str, type_name: str = "") -> str:
    low = name.lower()
    if type_name in {"image", "video"} or any(term in low for term in ("image", "img", "photo", "avatar", "thumbnail", "media", "video", "poster")):
        return "media"
    if low in {"id", "uuid"} or low.endswith("_id") or any(term in low for term in ("internal", "password", "token", "secret")):
        return "hidden"
    if any(term in low for term in ("name", "title", "code", "number", "label", "subject")):
        return "title"
    if any(term in low for term in ("price", "amount", "total", "status", "state", "date", "created", "updated", "count", "quantity")):
        return "primary"
    if any(term in low for term in ("description", "summary", "body", "content", "note", "comment", "message")):
        return "body"
    return "secondary"

def _supported_field_slots(section: dict) -> set[str]:
    component = str(section.get("component") or "")
    layout = str(section.get("layout") or "")
    return set(_COMPONENT_FIELD_SLOT_MAP.get(component) or _FIELD_SLOT_MAP.get(layout) or set())

def _field_list(value) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, dict) and item.get("field"):
            result.append(str(item["field"]))
        elif isinstance(item, str) and item:
            result.append(item)
    return result

def _normalize_field_layout(section: dict) -> dict:
    attrs = section.get("attributes") or []
    attr_names = [_attr_name(attr) for attr in attrs if _attr_name(attr)]
    if not attr_names or not section.get("primary_model"):
        return {}
    attr_set = set(attr_names)
    supported = _supported_field_slots(section)
    if not supported:
        return {}

    raw = section.get("field_layout") if isinstance(section.get("field_layout"), dict) else {}
    existing_styles = raw.get("field_styles") if isinstance(raw.get("field_styles"), dict) else {}
    cleaned_styles = {}
    for fname, cfg in existing_styles.items():
        if fname not in attr_set or not isinstance(cfg, dict):
            continue
        clean = {}
        if isinstance(cfg.get("order"), int) or str(cfg.get("order", "")).isdigit():
            clean["order"] = int(cfg.get("order"))
        if str(cfg.get("col_span", "")) in {"3", "4", "6", "8", "12"}:
            clean["col_span"] = int(cfg.get("col_span"))
        if cfg.get("height") in {"sm", "md", "lg", "xl"}:
            clean["height"] = cfg.get("height")
        if cfg.get("text_size") in {"xs", "sm", "md", "lg", "xl"}:
            clean["text_size"] = cfg.get("text_size")
        if cfg.get("align") in {"left", "center", "right"}:
            clean["align"] = cfg.get("align")
        if cfg.get("label") in {"show", "hidden"}:
            clean["label"] = cfg.get("label")
        if cfg.get("visible") in {"show", "hidden"}:
            clean["visible"] = cfg.get("visible")
        if clean:
            cleaned_styles[fname] = clean

    hidden = [f for f in _field_list(raw.get("hidden")) if f in attr_set]
    for attr in attrs:
        name = _attr_name(attr)
        if name and _field_kind(name, _attr_type(attr)) == "hidden" and name not in hidden:
            hidden.append(name)
    for name, cfg in cleaned_styles.items():
        if cfg.get("visible") == "hidden" and name not in hidden:
            hidden.append(name)
    visible_names = [name for name in attr_names if name not in set(hidden)]

    def first_existing(keys: list[str]) -> str:
        for key in keys:
            value = raw.get(key)
            if isinstance(value, str) and value in visible_names:
                return value
        return ""

    media = first_existing(["media", "image", "video", "avatar"])
    title = first_existing(["title"])
    subtitle = first_existing(["subtitle"])
    primary = first_existing(["primary", "price", "count"])
    secondary = [f for f in (_field_list(raw.get("secondary")) + _field_list(raw.get("meta")) + _field_list(raw.get("facts"))) if f in visible_names]
    fields = [f for f in (_field_list(raw.get("fields")) + _field_list(raw.get("columns"))) if f in visible_names]
    hero = [f for f in _field_list(raw.get("hero")) if f in visible_names]

    by_kind = {name: _field_kind(name, _attr_type(attr)) for name, attr in zip(attr_names, attrs)}
    if not media:
        media = next((n for n in visible_names if by_kind.get(n) == "media"), "")
    if not title:
        title = next((n for n in visible_names if by_kind.get(n) == "title"), "")
    if not primary:
        primary = next((n for n in visible_names if by_kind.get(n) == "primary" and n != title), "")
    if not secondary:
        secondary = [n for n in visible_names if n not in {media, title, primary} and by_kind.get(n) in {"secondary", "body", "primary"}][:4]
    if not fields:
        fields = visible_names
    if not hero:
        hero = [n for n in visible_names if n in {title, primary} or by_kind.get(n) == "body"][:4]

    out = {}
    if "image" in supported and media:
        media_attr = next((a for a in attrs if _attr_name(a) == media), None)
        if _attr_type(media_attr) == "video":
            if "video" in supported:
                out["video"] = media
            elif "media" in supported:
                out["media"] = media
        else:
            out["image"] = media
    elif "media" in supported and media:
        out["media"] = media
    if "title" in supported and title:
        out["title"] = title
    if "subtitle" in supported and subtitle:
        out["subtitle"] = subtitle
    if "primary" in supported and primary:
        out["primary"] = primary
    if "secondary" in supported:
        out["secondary"] = [f for f in secondary if f not in {media, title, primary}]
    if "columns" in supported:
        out["columns"] = fields
    if "fields" in supported:
        out["fields"] = fields
    if "hero" in supported:
        out["hero"] = hero
    if "hidden" in supported and hidden:
        out["hidden"] = hidden
    if cleaned_styles:
        out["field_styles"] = cleaned_styles
    return out

def _model_field_names(model_attrs: dict, model: str, limit: int = 6) -> list[str]:
    preferred = ["name", "title", "status", "price", "total", "quantity", "description", "created_at"]
    attrs = list(model_attrs.get(model) or [])
    selected = [name for name in preferred if name in attrs]
    selected.extend([name for name in attrs if name and name not in selected and name.lower() != "id"])
    return selected[:limit] or attrs[:limit]

def _finalize_data_section_bindings(sections: list, model_attrs: dict, limit: int = 8) -> list:
    data_layouts = {"card", "list", "table", "detail", "gallery", "filter", "form"}
    model_names = set(model_attrs.keys())
    model_names_fuzzy = {re.sub(r"[\s_-]", "", str(name or "")).lower(): name for name in model_names}

    def canonical_model(name: str) -> str:
        if name in model_attrs:
            return name
        return model_names_fuzzy.get(re.sub(r"[\s_-]", "", str(name or "")).lower(), "")

    fixed = []
    for section in sections:
        section = dict(section)
        section["layout"] = _normalize_layout_alias(section.get("layout"))
        layout = section.get("layout", "")
        component = str(section.get("component") or "")
        if component == "NavBar" and layout in {"", "nav", "navigation", "navbar"}:
            section["layout"] = "nav-links"
            layout = "nav-links"

        pm = canonical_model(str(section.get("primary_model") or section.get("class") or ""))
        if pm:
            section["primary_model"] = pm
            section["class"] = pm

        if pm and layout in data_layouts:
            valid_attrs = set(model_attrs.get(pm) or [])
            normalized_attrs = []
            for attr in section.get("attributes") or []:
                attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                attr_name = str(attr_name or "")
                if not attr_name:
                    continue
                if "." in attr_name:
                    first, rest = attr_name.split(".", 1)
                    related_model = canonical_model(first)
                    if related_model and rest in set(model_attrs.get(related_model) or []):
                        normalized = dict(attr) if isinstance(attr, dict) else {"name": attr_name}
                        normalized["name"] = f"{related_model}.{rest}"
                        normalized.setdefault("source", "related")
                        normalized.setdefault("readonly", True)
                        normalized_attrs.append(normalized)
                    continue
                if attr_name in valid_attrs:
                    normalized_attrs.append(attr)
            if not normalized_attrs:
                normalized_attrs = _model_field_names(model_attrs, pm, limit)
            section["attributes"] = normalized_attrs
        section["component"] = _infer_section_component(section)
        section["field_layout"] = _normalize_field_layout(section)
        fixed.append(section)
    return fixed

def _infer_section_layout(page: dict, candidate_index: int = 0) -> str:
    tokens = _name_tokens(f"{page.get('name', '')} {page.get('id', '')}")
    if tokens & {"detail", "view", "profile", "summary"}:
        return "detail"
    if tokens & {"form", "enter", "submit", "create", "edit", "update", "provide", "select", "choose"}:
        return "form"
    if tokens & {"list", "manage", "track", "history", "item", "line", "entry", "row"}:
        return "list"
    if tokens & {"browse", "catalog", "gallery", "showcase", "discover"}:
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

def _default_category_for_model(model: str, model_id_by_name: dict[str, str] | None = None) -> dict | None:
    model = str(model or "").strip()
    if not model:
        return None
    model_id_by_name = model_id_by_name or {}
    return {
        "label": model,
        "value": {
            "id": str(model_id_by_name.get(model) or model),
            "name": model,
        },
    }

def _model_for_page_category(page: dict, sections_by_id: dict[str, dict], known_models: set[str]) -> str:
    explicit = str(page.get("primary_model") or "").strip()
    if explicit in known_models:
        return explicit
    for ref in page.get("sections") or []:
        section = sections_by_id.get(_ref_id(ref) or "")
        model = str((section or {}).get("primary_model") or "").strip()
        if model in known_models:
            return model
    fallback = _fallback_model_for_page(page, known_models)
    return fallback if fallback in known_models else ""

def _assign_default_page_categories(pages: list, sections: list, model_id_by_name: dict[str, str] | None = None) -> list:
    model_id_by_name = model_id_by_name or {}
    known_models = set(model_id_by_name.keys())
    sections_by_id = {str(s.get("id")): s for s in sections or [] if s.get("id")}
    next_pages = []
    for raw in pages or []:
        page = dict(raw)
        if _page_type_value(page) == "activity":
            page["category"] = None
            next_pages.append(page)
            continue
        if page.get("category"):
            next_pages.append(page)
            continue
        model = _model_for_page_category(page, sections_by_id, known_models)
        page["category"] = _default_category_for_model(model, model_id_by_name)
        next_pages.append(page)
    return next_pages

def _merge_page_categories(categories: list, pages: list) -> list:
    merged = []
    seen = set()
    for category in categories or []:
        if not isinstance(category, dict):
            continue
        cid = str(category.get("id") or ((category.get("value") or {}).get("id") if isinstance(category.get("value"), dict) else "") or "")
        name = str(category.get("name") or ((category.get("value") or {}).get("name") if isinstance(category.get("value"), dict) else "") or category.get("label") or "")
        if not cid and not name:
            continue
        key = cid or name
        seen.add(key)
        merged.append(category)
    for page in pages or []:
        category = page.get("category")
        if not isinstance(category, dict):
            continue
        value = category.get("value") if isinstance(category.get("value"), dict) else {}
        cid = str(value.get("id") or category.get("id") or "")
        name = str(value.get("name") or category.get("name") or category.get("label") or "")
        key = cid or name
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append({"id": cid or name, "name": name or cid})
    return merged

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
        style.update({"display_mode": "grid", "card_style": "default", "columns": "3"})
    elif layout == "list":
        style.update({"list_style": "default"})
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
        "query": {},
        "col_span": 12,
        "position": "main",
        "style": style,
    }

def _header_sections_for_candidate(normal_pages: list, candidate_index: int = 0, model_attrs: dict | None = None) -> list[dict]:
    """Create a single editable header template section with deterministic variation."""
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    variant = candidate_index % 3
    ops = {"create": False, "update": False, "delete": False}
    templates = ("main-header", "split-header", "dashboard-header", "commerce-header", "app-header", "compact-header", "mega-header", "minimal-header", "hero-header", "tabbed-header", "glass-header", "command-header")
    layout = templates[candidate_index % len(templates)]
    style = {
        "color": "accent",
        "density": ("normal", "compact", "spacious")[variant],
        "shadow": ("sm", "md", "lg")[variant],
        "border": "light",
        "bg": "white",
        "header_variant": {
            "main-header": "commerce",
            "commerce-header": "commerce",
            "split-header": "split-dark",
            "dashboard-header": "dashboard",
            "app-header": "app",
            "compact-header": "compact",
            "mega-header": "mega",
            "minimal-header": "minimal",
            "hero-header": "hero",
            "tabbed-header": "tabs",
            "glass-header": "glass",
            "command-header": "command",
        }.get(layout, "commerce"),
        "nav_height": ("normal", "compact", "tall")[variant],
    }
    return [{
        "id": "app_header_template",
        "name": "Header",
        "role": "header",
        "layout": layout,
        "component": "HeaderTemplate",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": ops,
        "methods": nav_methods,
        "text": "Search",
        "col_span": 12,
        "position": "header",
        "style": style,
    }]

def _footer_sections_for_candidate(candidate_index: int = 0, normal_pages: list | None = None) -> list[dict]:
    ops = {"create": False, "update": False, "delete": False}
    templates = ("site-footer", "mega-footer", "legal-footer", "newsletter-footer", "compact-footer", "social-footer", "split-footer", "app-footer", "cta-footer", "minimal-footer")
    layout = templates[candidate_index % len(templates)]
    nav_methods = _navigation_methods([p.get("name") for p in (normal_pages or []) if p.get("name")])
    return [{
        "id": "app_footer_template",
        "name": "Footer",
        "role": "footer",
        "layout": layout,
        "component": "FooterTemplate",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": ops,
        "methods": nav_methods or ["Help", "Privacy", "Terms", "Contact"],
        "col_span": 12,
        "position": "footer",
        "style": {
            "color": "accent",
            "density": ("normal", "compact", "spacious")[candidate_index % 3],
            "shadow": "sm",
            "border": "light",
            "bg": "white",
            "footer_variant": layout,
        },
    }]

def _top_nav_section_for_candidate(normal_pages: list, candidate_index: int = 0) -> dict:
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    return {
        "id": "app_page_nav",
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
        "style": {
            "color": "accent",
            "density": ("normal", "compact", "spacious")[int(candidate_index or 0) % 3],
            "shadow": "sm",
            "border": "light",
            "bg": "white",
            "variant": "page-nav",
            "nav_height": ("compact", "normal", "tall")[int(candidate_index or 0) % 3],
        },
    }

def _sidebar_nav_section_for_candidate(normal_pages: list, candidate_index: int = 0) -> dict:
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    side = "left" if int(candidate_index or 0) % 2 == 0 else "right"
    return {
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
        "position": "sidebar",
        "style": {
            "color": "accent",
            "density": ("normal", "compact", "spacious")[int(candidate_index or 0) % 3],
            "shadow": "sm",
            "border": "light",
            "bg": "white",
            "variant": "rail",
            "sidebar_side": side,
            "sidebar_width": 3,
            "nav_height": "tall",
            "full_height": True,
        },
    }

def _ensure_normal_page_navigation(pages: list, sections: list, normal_pages: list, candidate_index: int = 0) -> tuple[list, list]:
    if not normal_pages:
        return pages, sections
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    for section in sections:
        if section.get("position") == "footer" or _normalize_layout_alias(section.get("layout")) in _FOOTER_TEMPLATE_LAYOUTS:
            existing = section.get("methods") or []
            existing_names = {
                str(m.get("name") if isinstance(m, dict) else m).strip().lower()
                for m in existing
            }
            if nav_methods and (not existing_names or existing_names.issubset({"help", "privacy", "terms", "contact"})):
                section["methods"] = nav_methods
    nav_ids = [
        sid for sid, section in section_map.items()
        if (
            _normalize_layout_alias(section.get("layout")) in {"site-nav", "nav-links", "nav-bar"}
            or str(section.get("component") or "") == "NavBar"
            or str(section.get("role") or "").lower() == "navigation"
        )
    ]
    header_nav_ids = [
        sid for sid, section in section_map.items()
        if section.get("position") == "header"
        and _normalize_layout_alias(section.get("layout")) in _PAGE_NAV_LAYOUTS
    ]
    sidebar_nav_ids = [
        sid for sid in nav_ids
        if (section_map.get(sid) or {}).get("position") == "sidebar"
    ]
    keep_nav_id = header_nav_ids[0] if header_nav_ids else (sidebar_nav_ids[0] if sidebar_nav_ids else "")
    duplicate_nav_ids = set(nav_ids)
    if keep_nav_id:
        duplicate_nav_ids.discard(keep_nav_id)
    if duplicate_nav_ids:
        sections = [s for s in sections if str(s.get("id") or "") not in duplicate_nav_ids]
        section_map = {str(s.get("id")): s for s in sections if s.get("id")}
        for page in pages:
            page["sections"] = [
                ref for ref in (page.get("sections") or [])
                if _ref_id(ref) not in duplicate_nav_ids
            ]

    if not keep_nav_id:
        nav_section = (
            _sidebar_nav_section_for_candidate(normal_pages, candidate_index)
            if int(candidate_index or 0) % 3 == 2
            else _top_nav_section_for_candidate(normal_pages, candidate_index)
        )
        sid = nav_section["id"]
        suffix = 2
        while sid in section_map:
            sid = f"{nav_section['id']}_{suffix}"
            suffix += 1
        nav_section["id"] = sid
        sections.append(nav_section)
        section_map[sid] = nav_section
        keep_nav_id = sid
    elif int(candidate_index or 0) % 3 != 2 and keep_nav_id in sidebar_nav_ids and not header_nav_ids:
        nav_section = section_map.get(keep_nav_id) or {}
        nav_section["position"] = "header"
        nav_section["layout"] = "nav-links"
        nav_section["component"] = "NavBar"
        style = dict(nav_section.get("style") or {})
        style.pop("sidebar_side", None)
        style.pop("sidebar_width", None)
        style["variant"] = "page-nav"
        nav_section["style"] = style

    if keep_nav_id:
        for page in normal_pages:
            refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
            ref_ids = {_ref_id(ref) for ref in refs}
            if keep_nav_id not in ref_ids:
                keep_nav_section = section_map.get(keep_nav_id) or {}
                if keep_nav_section.get("position") == "sidebar":
                    page["sections"] = [{"value": keep_nav_id}] + refs
                else:
                    page["sections"] = refs
    return pages, sections

def _resolve_single_chrome_value(value, valid_set: set) -> str | None:
    """Return the first valid layout name from a raw LLM output that may be a list or comma string."""
    if not value:
        return None
    candidates: list[str] = []
    if isinstance(value, list):
        candidates = [str(v).strip() for v in value]
    else:
        candidates = [v.strip() for v in str(value).split(",")]
    for candidate in candidates:
        norm = _normalize_layout_alias(candidate)
        if norm in valid_set:
            return norm
    return None

def _apply_chrome_style(sections: list, header_layout, footer_layout) -> list:
    """Replace the header shell and/or footer layout with the explicitly requested style."""
    header_layout = _resolve_single_chrome_value(header_layout, _HEADER_SHELL_LAYOUTS)
    footer_layout = _resolve_single_chrome_value(footer_layout, _FOOTER_TEMPLATE_LAYOUTS)
    if not header_layout and not footer_layout:
        return sections
    result = []
    for raw in sections:
        section = dict(raw)
        layout = _normalize_layout_alias(section.get("layout"))
        pos = section.get("position")
        if header_layout and pos == "header" and layout in _HEADER_SHELL_LAYOUTS:
            section["layout"] = header_layout
            section["component"] = "HeaderTemplate"
        elif footer_layout and pos == "footer" and layout in _FOOTER_TEMPLATE_LAYOUTS:
            section["layout"] = footer_layout
            section["component"] = "FooterTemplate"
        result.append(section)
    return result

def _dedupe_agent_header_shells(pages: list, sections: list) -> tuple[list, list]:
    """Agent output may compose many header elements, but only one header/nav shell."""
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    header_shell_ids = [
        sid for sid, section in section_map.items()
        if section.get("position") == "header"
        and _normalize_layout_alias(section.get("layout")) in _HEADER_SHELL_LAYOUTS
    ]
    if len(header_shell_ids) <= 1:
        return pages, sections
    duplicate_ids = set(header_shell_ids[1:])
    next_sections = [section for section in sections if str(section.get("id")) not in duplicate_ids]
    next_pages = []
    for page in pages:
        page = dict(page)
        page["sections"] = [
            ref for ref in (page.get("sections") or [])
            if _ref_id(ref) and _ref_id(ref) not in duplicate_ids
        ]
        next_pages.append(page)
    return next_pages, next_sections

def _ensure_candidate_content_structure(pages: list, sections: list, model_attrs: dict, candidate_index: int = 0, prompt: str = "") -> tuple[list, list]:
    known_models = set(model_attrs.keys())
    sections = [dict(s) for s in sections]
    for section in sections:
        section["layout"] = _normalize_layout_alias(section.get("layout"))
        if section.get("component") == "NavBar" and not section.get("layout"):
            section["layout"] = "nav-links"
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    activity_section_ids = {sid for sid, s in section_map.items() if s.get("type") == "activity_action" or s.get("layout") == "activity_action"}
    chrome_layouts = _CHROME_TEMPLATE_LAYOUTS | {"activity_start", "activity_tasks"}

    sections_pages = _dedupe_agent_header_shells([], sections)
    sections = sections_pages[1]
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    keep_header_shell_id = next(
        (
            sid for sid, section in section_map.items()
            if section.get("position") == "header"
            and _normalize_layout_alias(section.get("layout")) in _HEADER_SHELL_LAYOUTS
        ),
        "",
    )

    fixed_pages = []
    normal_pages = []
    activity_pages = []
    normal_pages_by_key = {}
    for page in pages:
        page = dict(page)
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        if keep_header_shell_id:
            seen_header_shell = False
            deduped_refs = []
            for ref in refs:
                section = section_map.get(ref["value"]) or {}
                is_header_shell_ref = (
                    section.get("position") == "header"
                    and _normalize_layout_alias(section.get("layout")) in _HEADER_SHELL_LAYOUTS
                )
                if is_header_shell_ref:
                    if seen_header_shell:
                        continue
                    seen_header_shell = True
                deduped_refs.append(ref)
            refs = deduped_refs
        if _page_type_value(page) != "activity":
            refs = [ref for ref in refs if ref["value"] not in activity_section_ids]
            page["sections"] = refs
            page_key = _section_id(page.get("name") or page.get("id") or page.get("display_name"))
            if page_key and page_key in normal_pages_by_key:
                existing = normal_pages_by_key[page_key]
                existing_refs = [{"value": _ref_id(ref)} for ref in existing.get("sections") or [] if _ref_id(ref)]
                existing_ids = {_ref_id(ref) for ref in existing_refs}
                existing["sections"] = existing_refs + [ref for ref in refs if ref["value"] not in existing_ids]
                continue
            normal_pages_by_key[page_key] = page
            normal_pages.append(page)
        else:
            page["sections"] = refs
            activity_pages.append(page)

    normal_page_ids = {_section_id(p.get("id") or p.get("name")) for p in normal_pages}
    has_header_region = any(
        s.get("id") and s.get("position") == "header"
        for s in sections
    )
    if normal_pages and not has_header_region:
        header_sections = _header_sections_for_candidate(normal_pages, candidate_index, model_attrs)
        for header_section in header_sections:
            sid = header_section["id"]
            suffix = 2
            while sid in section_map:
                sid = f"{header_section['id']}_{suffix}"
                suffix += 1
            header_section["id"] = sid
            sections.append(header_section)
            section_map[sid] = header_section
        for page in normal_pages:
            refs = page.get("sections") or []
            ref_ids = {_ref_id(ref) for ref in refs}
            missing_header_refs = [{"value": s["id"]} for s in header_sections if s["id"] not in ref_ids]
            if missing_header_refs:
                page["sections"] = missing_header_refs + refs

    has_footer_region = any(s.get("id") and s.get("position") == "footer" for s in sections)
    if normal_pages and not has_footer_region:
        footer_sections = _footer_sections_for_candidate(candidate_index, normal_pages)
        for footer_section in footer_sections:
            sid = footer_section["id"]
            suffix = 2
            while sid in section_map:
                sid = f"{footer_section['id']}_{suffix}"
                suffix += 1
            footer_section["id"] = sid
            sections.append(footer_section)
            section_map[sid] = footer_section
        for page in normal_pages:
            refs = page.get("sections") or []
            ref_ids = {_ref_id(ref) for ref in refs}
            missing_footer_refs = [{"value": s["id"]} for s in footer_sections if s["id"] not in ref_ids]
            if missing_footer_refs:
                page["sections"] = refs + missing_footer_refs

    _all_pages_for_nav = normal_pages + activity_pages
    _all_pages_for_nav, sections = _ensure_normal_page_navigation(_all_pages_for_nav, sections, normal_pages, candidate_index)
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}

    def _is_global_region_section(section: dict) -> bool:
        position = section.get("position")
        if position not in {"header", "sidebar", "footer"} or not section.get("id"):
            return False
        layout = section.get("layout")
        style = section.get("style") or {}
        role = str(section.get("role") or "").lower()
        scope = str(section.get("scope") or style.get("scope") or "").lower()
        if scope == "global":
            return True
        if layout in chrome_layouts:
            return True
        if not section.get("primary_model"):
            return True
        return role in {
            "brand", "navigation", "search", "actions", "action", "promo", "utility",
            "status", "summary", "kpi", "stats", "legal", "contact", "help", "footer",
        }

    header_region_ids = [
        str(s.get("id")) for s in sections
        if _is_global_region_section(s) and s.get("position") == "header"
    ]
    sidebar_region_ids = [
        str(s.get("id")) for s in sections
        if _is_global_region_section(s) and s.get("position") == "sidebar"
    ]
    footer_region_ids = [
        str(s.get("id")) for s in sections
        if _is_global_region_section(s) and s.get("position") == "footer"
    ]
    if header_region_ids or sidebar_region_ids or footer_region_ids:
        for page in normal_pages:
            refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
            ref_ids = {_ref_id(ref) for ref in refs}
            header_refs = [{"value": sid} for sid in header_region_ids if sid not in ref_ids]
            sidebar_refs = [{"value": sid} for sid in sidebar_region_ids if sid not in ref_ids]
            footer_refs = [{"value": sid} for sid in footer_region_ids if sid not in ref_ids]
            if header_refs or sidebar_refs or footer_refs:
                page["sections"] = header_refs + sidebar_refs + refs + footer_refs

    referenced_region_ids = {
        _ref_id(ref)
        for page in normal_pages
        for ref in (page.get("sections") or [])
        if _ref_id(ref)
    }

    def _best_page_for_region_section(section: dict) -> dict | None:
        if not normal_pages:
            return None
        pm = str(section.get("primary_model") or "")
        if pm:
            pm_key = _section_id(pm)
            for page in normal_pages:
                page_pm = str(page.get("primary_model") or "")
                page_text = f"{page.get('id', '')} {page.get('name', '')}"
                if page_pm == pm or pm_key in _section_id(page_text):
                    return page
        return normal_pages[0]

    for section in sections:
        sid = str(section.get("id") or "")
        position = section.get("position")
        if not sid or sid in referenced_region_ids or position not in {"header", "sidebar", "footer"}:
            continue
        page = _best_page_for_region_section(section)
        if not page:
            continue
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        if position == "footer":
            page["sections"] = refs + [{"value": sid}]
        else:
            page["sections"] = [{"value": sid}] + refs
        referenced_region_ids.add(sid)

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
            "type": {"value": "normal", "label": "Normal"},
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
            and (section_map.get(sid) or {}).get("layout") in {"card", "list", "table", "detail", "gallery", "form"}
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
            style["list_style"] = "default"
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
            "query": {},
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
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}
    nav_names = [
        (page_by_id.get(pid) or {}).get("name") or _page_name(pid)
        for pid in usecase_navigation.get("nav_bar_pages") or []
        if _section_id(pid) in page_by_id
    ]
    workflow_icon_links = _workflow_icon_links(usecase_navigation, page_by_id)
    if not nav_names and not workflow_icon_links:
        return sections
    fixed = []
    for section in sections:
        section = dict(section)
        layout = _normalize_layout_alias(section.get("layout"))
        if nav_ids and (layout in (_HEADER_NAV_LAYOUTS | {"nav-bar"}) or (section.get("position") in {"header", "sidebar"} and layout in {"site-nav", "nav-links", "nav-bar"})):
            section["layout"] = layout
            section["methods"] = _navigation_methods(nav_names)
        if section.get("position") == "header" or layout in _HEADER_TEMPLATE_LAYOUTS or layout == "icon-actions":
            style = dict(section.get("style") or {})
            if workflow_icon_links and not style.get("icon_links"):
                style["icon_links"] = workflow_icon_links[:2]
            section["style"] = style
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
            "role": section_plan.get("role"),
            "layout": section_plan.get("layout") or "detail",
            "component": section_plan.get("component") or _infer_section_component(section_plan),
            "primary_model": model,
            "class": model,
            "attributes": attrs,
            "field_layout": section_plan.get("field_layout") or {},
            "behavior": section_plan.get("behavior") or {},
            "operations": operations,
            "data_source": section_plan.get("data_source") or {},
            "query": section_plan.get("query") or {},
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
        def _norm_refs(refs: list) -> list:
            out = []
            for ref in refs or []:
                sid = ref.get("value") if isinstance(ref, dict) else ref
                if sid:
                    out.append({"value": str(sid)})
            return out

        if "sections" in patch:
            section_map = {str(s["id"]): s for s in data.get("sections", [])}
            for ps in patch["sections"]:
                sid = str(ps.get("id", ""))
                if not sid:
                    continue
                is_new = sid not in section_map
                if is_new:
                    section_map[sid] = {
                        "id": sid,
                        "name": ps.get("name") or sid,
                        "role": ps.get("role", ""),
                        "layout": ps.get("layout", "card"),
                        "component": ps.get("component") or _infer_section_component(ps),
                        "position": ps.get("position", "main"),
                        "col_span": ps.get("col_span", 12),
                        "primary_model": ps.get("primary_model", ""),
                        "class": ps.get("class") or ps.get("primary_model", ""),
                        "attributes": ps.get("attributes", []),
                        "field_layout": ps.get("field_layout", {}),
                        "behavior": ps.get("behavior", {}),
                        "operations": ps.get("operations", {"create": False, "update": False, "delete": False, "select": False}),
                        "data_source": ps.get("data_source", {}),
                        "query": ps.get("query", {}),
                        "style": ps.get("style", {}),
                    }
                for field in ("role", "layout", "component", "col_span", "position", "attributes", "field_layout", "behavior", "data_source", "query", "workflow", "label", "target_page", "workflow_action", "primary_model", "class", "text", "methods", "min_height"):
                    if field in ps:
                        section_map[sid][field] = ps[field]
                if "style" in ps:
                    section_map[sid]["style"] = {**(section_map[sid].get("style") or {}), **ps["style"]}
            data["sections"] = list(section_map.values())
        if "pages" in patch:
            page_map = {str(p["id"]): p for p in data.get("pages", [])}
            for pp in patch["pages"]:
                pid = str(pp.get("id", ""))
                if not pid:
                    continue
                if pid not in page_map:
                    page_map[pid] = {
                        "id": pid,
                        "name": pp.get("name") or pid,
                        "sections": _norm_refs(pp.get("sections") or []),
                        "primary_model": pp.get("primary_model", ""),
                        "category": pp.get("category", None),
                    }
                for field in ("layout", "gap", "name", "primary_model", "category", "type"):
                    if field in pp:
                        page_map[pid][field] = pp[field]
                if "sections" in pp:
                    page_map[pid]["sections"] = _norm_refs(pp["sections"])
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
        if os.environ.get("ADK_FULL_CONTEXT", "").lower() not in {"1", "true", "yes"}:
            current_data = iface.get("data") or {}
            usecase_navigation = system_ctx.get("usecase_navigation") or {}
            activity_steps = [
                {
                    "activity_node_id": step.get("activity_node_id"),
                    "activity_node_name": step.get("activity_node_name"),
                    "actor": step.get("actor"),
                    "page_name": step.get("page_name"),
                    "primary_models": step.get("primary_models", []),
                    "next_activity_node_ids": step.get("next_activity_node_ids", []),
                }
                for step in system_ctx.get("workflow_plan", [])
            ]
            ooui_plan = usecase_navigation.get("ooui_plan") or {}
            return json.dumps({
                "ATTRIBUTE_REFERENCE": {
                    "_note": "USE ONLY these exact field names as section attributes. DO NOT invent new names.",
                    "models": attr_ref,
                },
                "interface": iface_clean,
                "current_interface": {
                    "pages": current_data.get("pages", []),
                    "sections": current_data.get("sections", []),
                    "styling": current_data.get("styling", {}),
                },
                "usecase_navigation": {
                    "pages": usecase_navigation.get("pages", []),
                    "nav_bar_pages": usecase_navigation.get("nav_bar_pages", []),
                    "icon_actions": usecase_navigation.get("icon_actions", []),
                    "workflow_entry_points": usecase_navigation.get("workflow_entry_points", []),
                    "actor_permissions": usecase_navigation.get("actor_permissions", {}),
                    "ooui_plan": {
                        "pages": ooui_plan.get("pages", []),
                        "sections": ooui_plan.get("sections", []),
                        "operations": ooui_plan.get("operations", []),
                        "workflows": ooui_plan.get("workflows", []),
                    },
                },
                "workflow_plan": activity_steps,
            }, separators=(",", ":"))
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
               Pages do NOT contain section data — they only reference section IDs.
        sections: JSON string containing a list of ALL section definition objects. Each section must have:
                  id, name, layout, position, col_span, primary_model, attributes, operations, style.
                  This is SEPARATE from pages. Both pages[] and sections[] are required.
        tokens: Optional JSON string with design tokens from select_design_specs_for_interface.
        styling: Optional JSON string with global styling overrides.
        prompt: Original user design prompt (optional, for logging).
        derived_from: Optional source candidate index/id when regenerating from a selected candidate.
        designer_requirements: Optional human-in-the-loop requirements used for regeneration.
        variation_strategy: Optional short label for how this candidate differs from the source.
    """
    try:
        if isinstance(pages, str):
            pages = json.loads(pages)
        if isinstance(sections, str):
            sections = json.loads(sections)
        prompt_for_style = designer_requirements or prompt
        prompt_intent = compile_prompt_intent(prompt_for_style)
        if styling:
            if isinstance(styling, str):
                try:
                    styling = json.loads(styling)
                except Exception:
                    styling = {}
            styling = dict(styling); alias_map = {"accent_color": "accentColor", "background_color": "backgroundColor", "text_color": "textColor", "selected_style": "selectedStyle"}
            for old_key, new_key in alias_map.items():
                if old_key in styling and new_key not in styling: styling[new_key] = styling.pop(old_key)
            if isinstance(styling.get("radius"), str):
                radius_map = {"none": 0, "sm": 4, "md": 8, "lg": 12, "xl": 16, "2xl": 24}; styling["radius"] = radius_map.get(styling["radius"], 8)
        else:
            styling = {}
        prompt_styling = _prompt_styling_overrides(prompt_for_style)
        if prompt_styling:
            styling = {**styling, **prompt_styling}
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
            tokens = _apply_prompt_style_overrides(tokens, prompt_for_style)
        if prompt_intent.get("colorIntent"):
            tokens = {**(tokens or {}), **prompt_intent["colorIntent"]}
        cls_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/classifiers/", headers=_AUTH_HEADERS); classifiers_data = cls_resp.json() if cls_resp.ok else {}; raw_classifiers = classifiers_data.get("classifiers", []) if isinstance(classifiers_data, dict) else classifiers_data; model_attrs = {}; model_id_by_name = {}
        for c in raw_classifiers:
            cdata = c.get("data", {}); cname = cdata.get("name", ""); attrs = {a.get("name", "") for a in cdata.get("attributes", []) if a.get("name")}
            if cname:
                model_attrs[cname] = attrs
                model_id_by_name[cname] = str(c.get("id") or cdata.get("id") or cname)
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
        sections = _normalize_chrome_sections(sections)
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
        errors = []; _VALID_LAYOUTS = {"card", "list", "table", "detail", "gallery", "filter", "form", "activity_action", "activity_start", "activity_tasks"} | _CHROME_TEMPLATE_LAYOUTS
        _VALID_STYLE = {"color": {"blue", "green", "purple", "orange", "rose", "slate", "accent", "accent-secondary"},"density": {"compact", "normal", "spacious"}, "nav_height": {"compact", "normal", "tall", "xl"}, "shadow": {"none", "sm", "md", "lg", "xl"}, "border": {"none", "light", "colored", "strong"}, "bg": {"white", "light", "gray", "dark"}, "header_style": {"default", "large", "small", "colored", "hidden"}, "display_mode": {"grid", "carousel", "banner"}, "card_style": {"default", "product", "category", "compact"}, "list_style": {"default", "product", "cart-item"}, "form_style": {"default", "auth", "step", "summary"}, "image_position": {"left", "top", "right"}, "image_size": {"sm", "md", "lg"}, "banner_height": {"sm", "md", "lg", "xl"}, "image_ratio": {"wide", "16:9", "4:3", "1:1", "portrait"}, "logo_size": {"sm", "md", "lg", "xl"}, "logo_shape": {"rounded", "circle", "square"}}
        for s in sections:
            s["layout"] = _normalize_layout_alias(s.get("layout"))
            s["operations"] = _normalize_section_operations(s.get("operations"))
            s["component"] = _infer_section_component(s)
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
            available_field_layout_attrs = {
                (attr.get("name", attr) if isinstance(attr, dict) else attr)
                for attr in s.get("attributes", [])
            }
            s["field_layout"] = _normalize_field_layout(s)
            for field_ref in _field_layout_field_refs(s.get("field_layout")):
                if field_ref not in available_field_layout_attrs:
                    errors.append(f"section '{sname}': field_layout references '{field_ref}' which is not in attributes")
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
            s["layout"] = _normalize_layout_alias(s.get("layout"))
            s["operations"] = _normalize_section_operations(s.get("operations"))
            s["component"] = _infer_section_component(s)
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
                attr_renames = {}
                for attr in s.get("attributes", []):
                    attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                    if "." in attr_name:
                        first, rest = attr_name.split(".", 1)
                        canonical = _canonical_model_name(first)
                        if canonical and rest in model_attrs.get(canonical, set()):
                            normalized = dict(attr) if isinstance(attr, dict) else {"name": attr_name}
                            canonical_attr_name = f"{canonical}.{rest}"
                            normalized["name"] = canonical_attr_name
                            normalized.setdefault("source", "related")
                            normalized.setdefault("readonly", True)
                            if canonical_attr_name != attr_name:
                                attr_renames[attr_name] = canonical_attr_name
                            new_attrs.append(normalized)
                    elif not pm or attr_name in model_attrs.get(pm, set()):
                        new_attrs.append(attr)
                # If all attrs were invalid, auto-populate from actual model fields
                if not new_attrs and s.get("layout") in _data_layouts_set:
                    new_attrs = list(_model_field_names(model_attrs, pm, 6))
                s["attributes"] = new_attrs
                if attr_renames and isinstance(s.get("field_layout"), dict):
                    def _rename_field_layout_value(value):
                        if isinstance(value, str):
                            return attr_renames.get(value, value)
                        if isinstance(value, list):
                            return [_rename_field_layout_value(item) for item in value]
                        if isinstance(value, dict):
                            return {key: _rename_field_layout_value(item) for key, item in value.items()}
                        return value
                    s["field_layout"] = {
                        key: _rename_field_layout_value(value)
                        for key, value in (s.get("field_layout") or {}).items()
                    }
                s["field_layout"] = _normalize_field_layout(s)
            else:
                s["field_layout"] = _normalize_field_layout(s)
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
            p = dict(p)
            page_type = _infer_page_type_value(p)
            p["type"] = _canonical_page_type(page_type)
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
            s["component"] = _infer_section_component(s)
            s["field_layout"] = _normalize_field_layout(s)
        fixed_sections = _normalize_chrome_sections(fixed_sections)
        fixed_pages, fixed_sections = _ensure_workflow_entry_sections(fixed_pages, fixed_sections, usecase_navigation)
        fixed_pages, fixed_sections = _ensure_candidate_content_structure(fixed_pages, fixed_sections, model_attrs, int(candidate_index or 0), prompt_for_style)
        fixed_pages, fixed_sections = _ensure_pre_workflow_content_sections(fixed_pages, fixed_sections, usecase_navigation, model_attrs, int(candidate_index or 0))
        fixed_sections = _apply_ooui_navigation_methods(fixed_pages, fixed_sections, usecase_navigation)
        fixed_pages, fixed_sections, tokens, styling = apply_hard_constraints(fixed_pages, fixed_sections, tokens or {}, styling or {}, prompt_intent)
        fixed_pages, fixed_sections = _apply_candidate_region_composition(
            fixed_pages,
            fixed_sections,
            int(candidate_index or 0),
            prompt_for_style,
            preserve_layout=(derived_from != "" and not _prompt_requests_layout_change(prompt_for_style)),
        )
        fixed_pages, fixed_sections = _dedupe_agent_header_shells(fixed_pages, fixed_sections)
        fixed_sections = _finalize_data_section_bindings(fixed_sections, model_attrs)
        for s in fixed_sections:
            s["component"] = _infer_section_component(s)
        chrome_positions = {"header", "hero", "footer", "sidebar"}
        assignable_layouts = {"card", "list", "table", "detail", "gallery", "form"}
        content_sections = [
            s for s in fixed_sections
            if s.get("position", "main") not in chrome_positions
            and s.get("layout") in assignable_layouts
        ]
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
                page_type = _page_type_value(p)
                page_key = f"{p.get('id', '')} {p.get('name', '')}".lower()
                if page_type == "activity" or "workflow" in page_key:
                    rebuilt_pages.append(p)
                    continue
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
        section_ids = {s["id"] for s in fixed_sections}
        for p in fixed_pages:
            p["sections"] = [
                ref for ref in (p.get("sections") or [])
                if (_ref_id(ref) in section_ids)
            ]
        fixed_pages = _assign_default_page_categories(fixed_pages, fixed_sections, model_id_by_name)
        orphans = []
        for p in fixed_pages:
            for ref in p.get("sections", []):
                sid = ref.get("value") if isinstance(ref, dict) else str(ref)
                if sid and sid not in section_ids: orphans.append(f"page '{p.get('name')}' references section '{sid}' which is not in sections[]")
        if orphans: return f"INCOMPLETE: pages reference section IDs that are missing from sections[]. Missing: {'; '.join(orphans[:5])}."
        canonical_schema = {
            "version": 1,
            "pages": fixed_pages,
            "sections": fixed_sections,
            "tokens": tokens or {},
            "styling": styling or {},
            "prompt_intent": prompt_intent,
        }
        data = dict(iface.get("data") or {}); data["categories"] = _merge_page_categories(data.get("categories") or [], fixed_pages); candidates = list(data.get("candidates") or []); candidate = {"id": f"c{candidate_index}", "name": name, "description": description, "pages": fixed_pages, "sections": fixed_sections, "generated_by": "gemini_make_agent", "prompt": prompt or designer_requirements, "prompt_intent": prompt_intent, "canonical_schema": canonical_schema, "fallback": False, **({"tokens": tokens} if tokens else {}), **({"design_spec": design_spec_name} if design_spec_name else {}), **({"styling": styling} if styling else {})}
        if derived_from != "":
            candidate["derived_from"] = derived_from
        if designer_requirements:
            candidate["designer_requirements"] = designer_requirements
        if variation_strategy:
            candidate["variation_strategy"] = variation_strategy
        while len(candidates) <= candidate_index: candidates.append(None)
        candidates[candidate_index] = candidate; data["candidates"] = candidates; payload = {"id": interface_id, "name": iface["name"], "description": iface.get("description", ""), "system_id": system_id, "actor_id": iface.get("actor"), "data": data}; put_resp = requests.put(f"{METADATA_API_BASE}/interfaces/{interface_id}/", json=payload, headers=_AUTH_HEADERS); put_resp.raise_for_status()
        return f"OK: candidate {candidate_index} '{name}' saved successfully."
    except Exception as e: return f"Error saving candidate: {e}"

def get_candidate_regeneration_context(interface_id: str, candidate_index: int, designer_requirements: str = "") -> str:
    """Return the selected candidate as the baseline for human-guided regeneration."""
    try:
        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS, timeout=30)
        iface_resp.raise_for_status()
        iface = iface_resp.json()
        data = dict(iface.get("data") or {})
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
                "design_spec": base.get("design_spec"),
                "variation_strategy": base.get("variation_strategy"),
            },
        }
        return json.dumps(context, indent=2)
    except Exception as e:
        return f"Error fetching candidate regeneration context: {e}"

def _candidate_variant_name(prompt: str, index: int) -> str:
    color_name, _ = _prompt_color_theme(prompt)
    prefix = (color_name or "Agent").replace("_", " ").title()
    suffixes = ("Card Gallery", "Data Table", "Showcase")
    return f"{prefix} {suffixes[index % len(suffixes)]}"

def _variant_tokens(tokens: dict, prompt: str, index: int) -> dict:
    tokens = _apply_prompt_style_overrides(dict(tokens or {}), prompt)
    scoped_overrides = _prompt_scoped_color_overrides(prompt)
    if _prompt_color_scope_lock(prompt):
        if scoped_overrides:
            tokens.update(scoped_overrides)
        tokens["design.variant_index"] = str(index)
        _expand_design_tokens(tokens)
        return tokens
    color_name, theme = _prompt_color_theme(prompt)
    if color_name in {"pink", "rose"}:
        accents = ("#db2777", "#be185d", "#ec4899")
        secondaries = ("#f9a8d4", "#f472b6", "#fbcfe8")
    elif color_name in {"purple", "violet"}:
        accents = ("#7c3aed", "#6d28d9", "#a855f7")
        secondaries = ("#c084fc", "#a78bfa", "#ddd6fe")
    elif theme:
        accents = (theme.get("accent", "#2563eb"), theme.get("accent", "#2563eb"), theme.get("secondary", theme.get("accent", "#2563eb")))
        secondaries = (theme.get("secondary", accents[0]), theme.get("border", accents[1]), theme.get("secondary", accents[2]))
    else:
        accents = ("#2563eb", "#111827", "#f97316")
        secondaries = ("#60a5fa", "#64748b", "#fdba74")
    accent = accents[index % 3]
    secondary = secondaries[index % 3]
    tokens.update({
        "accent.hex": accent,
        "color.secondary.hex": secondary,
        "region.header.bg_hex": accent,
        "region.footer.bg_hex": accent,
        "nav.bg_hex": accent,
        "button.primary.bg_hex": accent,
        "button.primary.border_hex": accent,
        "button.ghost.text_hex": accent,
        "input.border_focus_hex": accent,
        "design.variant_index": str(index),
    })
    if scoped_overrides:
        tokens.update(scoped_overrides)
    _expand_design_tokens(tokens)
    return tokens

def _prompt_layout_traits(prompt: str) -> dict:
    text = str(prompt or "").lower()
    return {
        "full": any(term in text for term in ("full width", "full-width", "edge to edge", "edge-to-edge", "full bleed", "full-bleed")),
        "dashboard": any(term in text for term in ("dashboard", "admin", "analytics", "operational", "dense")),
        "sidebar": any(term in text for term in ("sidebar", "side nav", "left nav", "rail")),
        "minimal": any(term in text for term in ("minimal", "clean", "simple", "focused")),
        "form": any(term in text for term in ("form", "wizard", "application", "onboarding")),
    }

def _page_layout_dict(page: dict) -> dict:
    raw = page.get("layout") or {}
    if isinstance(raw, dict):
        out = dict(raw)
    elif raw:
        out = {"value": raw}
    else:
        out = {"value": "default"}
    return out

def _baseline_layout_intent(pages: list, sections: list) -> dict:
    first_page = next((p for p in pages or [] if isinstance(p, dict)), {})
    layout = _page_layout_dict(first_page)
    nav_sections = [
        s for s in sections or []
        if _normalize_layout_alias(s.get("layout")) in {"site-nav", "nav-links", "nav-bar"} or str(s.get("component") or "") == "NavBar"
    ]
    sidebar_nav = next((s for s in nav_sections if s.get("position") == "sidebar"), None)
    sidebar_section = next((s for s in sections or [] if s.get("position") == "sidebar"), None)
    data_sections = [s for s in sections or [] if s.get("primary_model") and s.get("layout") in {"card", "gallery", "table", "list", "detail", "form"}]
    dominant_data_layout = (data_sections[0].get("layout") if data_sections else "card") or "card"
    dominant_density = ((data_sections[0].get("style") or {}).get("density") if data_sections else "normal") or "normal"
    return {
        "name": "selected-baseline",
        "main_width": layout.get("main_width", "contained"),
        "header_width": layout.get("header_width", "contained"),
        "hero_width": layout.get("hero_width", "contained"),
        "footer_width": layout.get("footer_width", "full"),
        "nav": "sidebar-left" if sidebar_nav or sidebar_section else "top",
        "sidebar_side": ((sidebar_nav or sidebar_section).get("style") or {}).get("sidebar_side", "left") if (sidebar_nav or sidebar_section) else "left",
        "sidebar_width": int(((sidebar_nav or sidebar_section).get("style") or {}).get("sidebar_width", 3)) if (sidebar_nav or sidebar_section) else 3,
        "density": dominant_density,
        "data_layout": dominant_data_layout,
        "data_columns": str(((data_sections[0].get("style") or {}).get("columns")) if data_sections else "3") or "3",
    }

def _layout_intent_for_candidate(mode: str, prompt: str, index: int, base_pages: list | None = None, base_sections: list | None = None) -> dict:
    traits = _prompt_layout_traits(prompt)
    if mode == "refine":
        base = _baseline_layout_intent(base_pages or [], base_sections or [])
        variants = [
            {"density": base["density"], "shadow": "sm", "spacing": "steady"},
            {"density": "compact" if base["density"] != "compact" else "normal", "shadow": "none", "spacing": "dense"},
            {"density": "spacious" if base["density"] != "spacious" else "normal", "shadow": "md", "spacing": "airy"},
        ]
        intent = {**base, **variants[index % 3], "mode": "refine", "name": f"refine-{index}"}
        forced = _prompt_forced_layout(prompt, {"id": "all", "name": "all", "role": "data", "primary_model": "all"})
        if forced:
            intent["forced_data_layout"] = forced
        if traits["full"] or traits["dashboard"]:
            intent["main_width"] = "full" if index != 0 else "wide"
            intent["header_width"] = "full"
            intent["footer_width"] = "full"
        if traits["sidebar"]:
            intent["nav"] = "sidebar-left"
        return intent

    presets = [
        {"name": "balanced-contained", "main_width": "contained", "header_width": "contained", "hero_width": "contained", "footer_width": "full", "nav": "top", "density": "normal", "data_layout": "card", "data_columns": "2", "shadow": "sm"},
        {"name": "wide-sidebar", "main_width": "wide", "header_width": "full", "hero_width": "contained", "footer_width": "full", "nav": "sidebar-left", "sidebar_side": "left", "sidebar_width": 3, "density": "compact", "data_layout": "table", "data_columns": "1", "shadow": "none"},
        {"name": "full-showcase", "main_width": "full", "header_width": "full", "hero_width": "full", "footer_width": "full", "nav": "top", "density": "spacious", "data_layout": "gallery", "data_columns": "3", "shadow": "md"},
    ]
    intent = {**presets[index % 3], "mode": "explore"}
    forced = _prompt_forced_layout(prompt, {"id": "all", "name": "all", "role": "data", "primary_model": "all"})
    if forced:
        intent["forced_data_layout"] = forced
    if traits["full"] or traits["dashboard"]:
        widths = ("wide", "full", "full")
        intent["main_width"] = widths[index % 3]
        intent["header_width"] = "full"
        intent["footer_width"] = "full"
        intent["data_layout"] = "table" if traits["dashboard"] and index != 2 else intent["data_layout"]
        intent["density"] = "compact" if traits["dashboard"] and index != 2 else intent["density"]
    if traits["sidebar"] and index % 3 == 2:
        intent["nav"] = "sidebar-left"
        intent["main_width"] = "wide" if intent["main_width"] == "contained" else intent["main_width"]
    if traits["minimal"]:
        intent["main_width"] = "contained" if index == 0 else "wide"
        intent["header_width"] = "contained"
        intent["density"] = "compact" if index == 1 else "normal"
        intent["shadow"] = "none"
    if traits["form"]:
        intent["data_layout"] = "form" if index == 0 else ("detail" if index == 1 else "card")
        intent["main_width"] = "contained" if index == 0 else "wide"
    return intent

def _apply_layout_intent_to_pages(pages: list, intent: dict) -> list:
    next_pages = copy.deepcopy(pages or [])
    for page in next_pages:
        layout = _page_layout_dict(page)
        layout.update({
            "main_width": intent.get("main_width", layout.get("main_width", "contained")),
            "header_width": intent.get("header_width", layout.get("header_width", "contained")),
            "hero_width": intent.get("hero_width", layout.get("hero_width", "contained")),
            "footer_width": intent.get("footer_width", layout.get("footer_width", "full")),
        })
        page["layout"] = layout
    return next_pages

def _prompt_forced_layout(prompt: str, section: dict) -> str | None:
    text = str(prompt or "").lower()
    if not text:
        return None
    layout = None
    if "table" in text:
        layout = "table"
    elif "gallery" in text or "showcase" in text:
        layout = "gallery"
    elif "card" in text or "cards" in text:
        layout = "card"
    if not layout:
        return None

    section_text = " ".join(
        str(section.get(key, ""))
        for key in ("id", "name", "role", "layout", "component", "primary_model", "class")
    ).lower()
    target_terms = []
    for term in ("item", "line", "entry", "record", "detail", "summary", "account", "profile"):
        if term in text:
            target_terms.append(term)
    if "all" in text or not target_terms:
        if "card" in text or "cards" in text or layout in {"table", "gallery"}:
            return layout
    if any(term in section_text for term in target_terms):
        return layout
    return None

def _component_for_layout(section: dict, layout: str) -> str:
    if layout == "table":
        return "DataTable"
    if layout == "gallery":
        section = {**section, "layout": "gallery"}
        return _infer_section_component(section)
    if layout == "card":
        section = {**section, "layout": "card"}
        return _infer_section_component(section)
    return _infer_section_component(section)

def _apply_layout_intent_to_sections(sections: list, intent: dict, prompt: str = "") -> list:
    next_sections = []
    mode = intent.get("mode", "explore")
    for raw in sections or []:
        section = copy.deepcopy(raw)
        layout = _normalize_layout_alias(section.get("layout"))
        section["layout"] = layout
        role = str(section.get("role") or "")
        style = dict(section.get("style") or {})
        section_id = str(section.get("id") or "")
        explicit_region_position = str(section.get("position") or "main")
        if layout in {"site-nav", "nav-links", "nav-bar"}:
            section["component"] = "NavBar"
            style["density"] = intent.get("density", style.get("density", "normal"))
            if intent.get("nav") == "sidebar-left":
                section["position"] = "sidebar"
                section["layout"] = "site-nav"
                section["col_span"] = 12
                style["sidebar_side"] = intent.get("sidebar_side", "left")
                style["sidebar_width"] = intent.get("sidebar_width", style.get("sidebar_width", 3))
                style["variant"] = "rail"
                style["bg"] = "white"
                style["shadow"] = "sm"
            else:
                section["position"] = "header"
                if layout == "site-nav":
                    section["layout"] = "nav-links"
                style.pop("sidebar_side", None)
        elif layout == "icon-actions":
            section["component"] = "IconActions"
            style["align"] = "right"
            section["position"] = "header"
        elif layout in _HEADER_TEMPLATE_LAYOUTS:
            section["position"] = "header"
            if mode == "explore" and intent.get("name") == "full-showcase" and layout == "main-header":
                section["layout"] = "minimal-header"
                section["component"] = "HeaderTemplate"
            if layout in {"logo", "search-bar"} and intent.get("density") == "compact":
                style["density"] = "compact"
        elif layout in _FOOTER_TEMPLATE_LAYOUTS:
            section["position"] = "footer"
            section["component"] = "FooterTemplate"
            style["density"] = intent.get("density", style.get("density", "normal"))
            if mode == "explore" and intent.get("nav") == "sidebar-left":
                section["layout"] = "link-grid"
                section["component"] = "FooterLinkGrid"
            elif intent.get("footer_width") == "full":
                style["surface_level"] = "elevated"
        elif explicit_region_position == "sidebar" or (intent.get("nav") == "sidebar-left" and (layout == "filter" or role in {"filter", "navigation", "summary", "kpi", "stats", "tasklist", "help"})):
            section["position"] = "sidebar"
            section["col_span"] = 12
            style["sidebar_side"] = style.get("sidebar_side", intent.get("sidebar_side", "left"))
            style["sidebar_width"] = style.get("sidebar_width", intent.get("sidebar_width", 3))
            style.setdefault("bg", "white")
        elif explicit_region_position in {"header", "footer", "hero"}:
            section["position"] = explicit_region_position
        if role in {"data", "collection", "child_collection"} or section.get("primary_model"):
            forced_layout = intent.get("forced_data_layout") or _prompt_forced_layout(prompt, section)
            if forced_layout:
                section["layout"] = forced_layout
                section["component"] = _component_for_layout(section, forced_layout)
                section["col_span"] = 12 if forced_layout == "table" else section.get("col_span", 12)
                if forced_layout in {"gallery", "card"}:
                    style["columns"] = "3" if forced_layout == "gallery" else "2"
            elif mode == "explore" and section.get("layout") in {"card", "gallery", "table", "list", "detail", "form"}:
                target_layout = intent.get("data_layout") or section.get("layout")
                section["layout"] = target_layout
                section["component"] = _component_for_layout(section, target_layout)
                section["col_span"] = 12 if target_layout in {"table", "gallery"} else (6 if target_layout == "card" and intent.get("main_width") != "full" else section.get("col_span", 12))
                style["columns"] = intent.get("data_columns", style.get("columns", "3"))
                if target_layout == "gallery":
                    style["surface_level"] = "elevated"
                    style["text_class"] = "si-text-display"
            elif mode == "refine" and section.get("layout") in {"card", "gallery", "table", "list", "detail", "form"}:
                style.setdefault("columns", intent.get("data_columns", style.get("columns", "3")))
        style["density"] = intent.get("density", style.get("density", "normal"))
        style["shadow"] = intent.get("shadow", style.get("shadow", "sm"))
        style.setdefault("color", "accent")
        section["style"] = style
        if section.get("layout") in {"table", "gallery", "card", "list", "detail", "form"}:
            section["component"] = _infer_section_component(section)
        next_sections.append(section)
    return next_sections

def _parse_generation_intent(prompt: str) -> dict:
    """Use Gemini to extract explicit color anchors and layout constraints from an initial design prompt.
    Only extracts what the designer *explicitly* stated — unspecified dimensions remain free for variation."""
    _default = {"colors": [], "layout": {}}
    if not prompt:
        return _default
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        _model_name = os.getenv("ADK_AGENT_MODEL", "gemini-2.0-flash-lite")
        if "/" in _model_name:
            _model_name = _model_name.split("/", 1)[1]
        _header_shells = "main-header|minimal-header|commerce-header|dashboard-header|split-header|app-header|compact-header|mega-header|hero-header|tabbed-header|glass-header|command-header"
        _footer_styles = "site-footer|compact-footer|legal-footer|newsletter-footer|social-footer|mega-footer|split-footer|app-footer|cta-footer|minimal-footer|link-grid|brand-strip"
        _prompt = (
            f'Analyze this UI design brief and extract only the color and layout constraints the designer explicitly stated.\n'
            f'Brief: "{prompt}"\n\n'
            'Output JSON only (no markdown):\n'
            '{{\n'
            '  "colors": [\n'
            '    {{"scope": "<button|nav|header|footer|sidebar|background|card|border|text|badge|input|table|link|accent>",\n'
            '      "hex": "<#rrggbb or null>", "name": "<english color name>"}}\n'
            '  ],\n'
            '  "layout": {{\n'
            '    "nav": "<top|sidebar-left|sidebar-right or null>",\n'
            '    "data_display": "<table|gallery|card|list or null>",\n'
            '    "density": "<compact|normal|spacious or null>",\n'
            '    "full_width": <true|false|null>,\n'
            f'    "header_style": "<ONE of: {_header_shells} — or null>",\n'
            f'    "footer_style": "<ONE of: {_footer_styles} — or null>"\n'
            '  }}\n'
            '}}\n\n'
            'Rules: Leave null/empty for anything NOT explicitly mentioned. header_style and footer_style must be a single exact token from the list above, never comma-separated.\n'
            'If multiple footer/header styles are mentioned, pick the most specific one.\n'
            'Examples:\n'
            '"patient management dashboard with blue header" → {{"colors":[{{"scope":"header","hex":"#1d4ed8","name":"blue"}}],"layout":{{}}}}\n'
            '"inventory system, left sidebar, table view" → {{"colors":[],"layout":{{"nav":"sidebar-left","data_display":"table"}}}}\n'
            '"green compact enterprise dashboard" → {{"colors":[{{"scope":"accent","hex":"#16a34a","name":"green"}}],"layout":{{"density":"compact"}}}}\n'
            '"glass header with newsletter footer" → {{"colors":[],"layout":{{"header_style":"glass-header","footer_style":"newsletter-footer"}}}}\n'
            '"commerce shop, mega header, social footer, blue accent" → {{"colors":[{{"scope":"accent","hex":"#2563eb","name":"blue"}}],"layout":{{"header_style":"commerce-header","footer_style":"social-footer"}}}}\n'
            '"order management" → {{"colors":[],"layout":{{}}}}'
        )
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{_model_name}:generateContent?key={api_key}",
                json={"contents": [{"parts": [{"text": _prompt}]}],
                      "generationConfig": {"temperature": 0, "maxOutputTokens": 512}},
                timeout=8,
            )
            resp.raise_for_status()
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
            result = json.loads(text)
            return {
                "colors": result.get("colors") or [],
                "layout": result.get("layout") or {},
            }
        except Exception:
            pass
    return _default

def _parse_regeneration_intent(designer_requirements: str) -> dict:
    """Use Gemini to parse designer_requirements into structured intent with specific color targets and layout specs."""
    _default = {"change_color": False, "change_layout": False, "colors": [], "layout": {}}
    if not designer_requirements:
        return _default
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        _model_name = os.getenv("ADK_AGENT_MODEL", "gemini-2.0-flash-lite")
        if "/" in _model_name:
            _model_name = _model_name.split("/", 1)[1]
        _header_shells = "main-header|minimal-header|commerce-header|dashboard-header|split-header|app-header|compact-header|mega-header|hero-header|tabbed-header|glass-header|command-header"
        _footer_styles = "site-footer|compact-footer|legal-footer|newsletter-footer|social-footer|mega-footer|split-footer|app-footer|cta-footer|minimal-footer|link-grid|brand-strip"
        _prompt = (
            f'Analyze this UI design change request. Output JSON only (no markdown, no explanation).\n'
            f'Request: "{designer_requirements}"\n\n'
            'Output schema:\n'
            '{{\n'
            '  "change_color": <bool - true if any colors/themes/backgrounds change>,\n'
            '  "change_layout": <bool - true if structure/nav position/section arrangement/header-footer style changes>,\n'
            '  "colors": [\n'
            '    {{"scope": "<button|nav|header|footer|sidebar|background|card|border|text|badge|input|table|link|accent>",\n'
            '      "hex": "<#rrggbb or null>", "name": "<english color name>"}}\n'
            '  ],\n'
            '  "layout": {{\n'
            '    "nav": "<top|sidebar-left|sidebar-right or null>",\n'
            '    "data_display": "<table|gallery|card|list or null>",\n'
            '    "density": "<compact|normal|spacious or null>",\n'
            '    "full_width": <true|false|null>,\n'
            f'    "header_style": "<ONE of: {_header_shells} — or null>",\n'
            f'    "footer_style": "<ONE of: {_footer_styles} — or null>"\n'
            '  }}\n'
            '}}\n\n'
            'Rules: header_style and footer_style must be a single exact token from the list, never comma-separated. If multiple are mentioned, pick the most specific one.\n'
            'Examples:\n'
            '"change header color to navy" → {{"change_color":true,"change_layout":false,"colors":[{{"scope":"header","hex":"#1e3a5f","name":"navy"}}],"layout":{{}}}}\n'
            '"left sidebar navigation" → {{"change_color":false,"change_layout":true,"colors":[],"layout":{{"nav":"sidebar-left"}}}}\n'
            '"switch to glass header" → {{"change_color":false,"change_layout":true,"colors":[],"layout":{{"header_style":"glass-header"}}}}\n'
            '"commerce header with newsletter footer" → {{"change_color":false,"change_layout":true,"colors":[],"layout":{{"header_style":"commerce-header","footer_style":"newsletter-footer"}}}}\n'
            '"compact green table with left nav" → {{"change_color":true,"change_layout":true,"colors":[{{"scope":"accent","hex":"#16a34a","name":"green"}}],"layout":{{"data_display":"table","density":"compact","nav":"sidebar-left"}}}}\n'
            '"purple buttons and red badges" → {{"change_color":true,"change_layout":false,"colors":[{{"scope":"button","hex":"#7c3aed","name":"purple"}},{{"scope":"badge","hex":"#dc2626","name":"red"}}],"layout":{{}}}}\n'
            '"dark background blue accent" → {{"change_color":true,"change_layout":false,"colors":[{{"scope":"background","hex":"#111827","name":"dark"}},{{"scope":"accent","hex":"#2563eb","name":"blue"}}],"layout":{{}}}}'
        )
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{_model_name}:generateContent?key={api_key}",
                json={"contents": [{"parts": [{"text": _prompt}]}],
                      "generationConfig": {"temperature": 0, "maxOutputTokens": 512}},
                timeout=8,
            )
            resp.raise_for_status()
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
            result = json.loads(text)
            return {
                "change_color": bool(result.get("change_color", False)),
                "change_layout": bool(result.get("change_layout", False)),
                "colors": result.get("colors") or [],
                "layout": result.get("layout") or {},
            }
        except Exception:
            pass
    # Fallback: string matching (no specific color/layout details)
    return {
        "change_color": _prompt_requests_color_change(designer_requirements),
        "change_layout": _prompt_requests_layout_change(designer_requirements),
        "colors": [],
        "layout": {},
    }

def _apply_intent_colors_to_tokens(tokens: dict, colors: list) -> dict:
    """Apply LLM-extracted structured color intents using the existing scope→token mapping."""
    overrides: dict = {}
    for ci in colors or []:
        scope = str(ci.get("scope") or "")
        hex_val = ci.get("hex")
        name = str(ci.get("name") or "")
        if not scope:
            continue
        if hex_val and not re.match(r"^#[0-9a-fA-F]{6}$", str(hex_val)):
            hex_val = _color_word_to_hex(hex_val) or _color_word_to_hex(name)
        elif not hex_val:
            hex_val = _color_word_to_hex(name)
        if hex_val:
            _apply_scoped_color(overrides, scope, name, hex_val)
    result = dict(tokens)
    result.update(overrides)
    return result

def _prompt_requests_color_change(prompt: str) -> bool:
    text = str(prompt or "").lower()
    return any(term in text for term in (
        "color", "colour", "顔色", "颜色", "背景色",
        "#", "hex", "tint", "shade",
        "red", "blue", "green", "purple", "orange", "yellow", "pink", "cyan", "teal",
        "white", "black", "grey", "gray", "dark mode", "light mode",
        "红", "蓝", "绿", "紫", "橙", "黄", "粉", "白", "黑", "灰",
    ))

def _prompt_requests_layout_change(prompt: str) -> bool:
    text = str(prompt or "").lower()
    # Unambiguous layout terms always count
    if any(term in text for term in (
        "layout", "排版", "布局", "region", "sidebar", "side bar", "left nav", "right nav",
        "split", "rail", "左侧", "右侧", "侧边栏", "full width", "full-width",
        "compact", "spacious", "table", "gallery",
    )):
        return True
    # "nav", "header", "footer" etc. also appear in color requests ("change header color").
    # Only treat them as layout requests when there is no color context in the prompt.
    color_context = any(c in text for c in (
        "color", "colour", "顔色", "颜色", "背景", "background", "#", "hex",
        "red", "blue", "green", "purple", "orange", "yellow", "pink",
        "白", "黑", "灰", "红", "蓝", "绿", "紫", "橙", "黄", "粉",
        "white", "black", "grey", "gray",
    ))
    if color_context:
        return False
    return any(term in text for term in (
        "nav", "navigation", "navbar", "header", "footer", "hero", "main", "wide",
        "card", "导航", "页头", "页脚",
    ))

def _is_content_region_section(section: dict) -> bool:
    layout = _normalize_layout_alias(section.get("layout"))
    if layout in _CHROME_TEMPLATE_LAYOUTS or layout in {"activity_action", "activity_start", "activity_tasks"}:
        return False
    if section.get("position") in {"header", "footer"}:
        return False
    return layout in {"card", "list", "table", "detail", "gallery", "filter", "form"} and (
        section.get("primary_model") or section.get("attributes") or section.get("role") in {"data", "collection", "summary", "filter"}
    )

def _apply_candidate_region_composition(pages: list, sections: list, candidate_index: int, prompt: str = "", preserve_layout: bool = False) -> tuple[list, list]:
    """Give first-generation candidates meaningfully different region placement.

    Regeneration keeps the selected candidate's section placement unless the user
    explicitly asks for layout/chrome/region changes.
    """
    if preserve_layout:
        return pages, sections
    pages = copy.deepcopy(pages or [])
    sections = copy.deepcopy(sections or [])
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    normal_pages = [p for p in pages if _page_type_value(p) != "activity"]
    if not normal_pages:
        return pages, sections

    # Work page-by-page so a candidate keeps each page's domain content, but the
    # regions differ across candidates. Never move the only content section off main.
    for page in normal_pages:
        refs = [_ref_id(ref) for ref in (page.get("sections") or []) if _ref_id(ref)]
        content_ids = [sid for sid in refs if _is_content_region_section(section_map.get(sid) or {})]
        if len(content_ids) < 2:
            continue
        idx = int(candidate_index or 0) % 3
        if idx == 0:
            # Editorial/executive direction: one lead section in hero, the rest in main.
            hero_id = content_ids[0]
            hero = section_map.get(hero_id)
            if hero and hero.get("layout") not in {"table", "form", "filter"}:
                style = dict(hero.get("style") or {})
                hero["position"] = "hero"
                hero["col_span"] = 12
                style.setdefault("surface_level", "elevated")
                style.setdefault("text_class", "si-text-display")
                hero["style"] = style
        elif idx == 1:
            # Operational direction: left rail for filters/summaries/navigation, main for work.
            sidebar_id = next(
                (sid for sid in content_ids if (section_map.get(sid) or {}).get("layout") in {"filter", "detail", "card", "list"}),
                content_ids[0],
            )
            sidebar = section_map.get(sidebar_id)
            if sidebar:
                style = dict(sidebar.get("style") or {})
                sidebar["position"] = "sidebar"
                sidebar["col_span"] = 12
                if sidebar.get("layout") in {"table", "gallery", "form"}:
                    sidebar["layout"] = "list"
                    sidebar["component"] = _component_for_layout(sidebar, "list")
                style["sidebar_side"] = "left"
                style["sidebar_width"] = 3
                style.setdefault("bg", "white")
                style.setdefault("shadow", "sm")
                sidebar["style"] = style
        else:
            # Showcase/detail direction: hero lead plus a right utility/detail rail.
            hero_id = content_ids[0]
            right_id = content_ids[-1] if content_ids[-1] != hero_id else ""
            hero = section_map.get(hero_id)
            if hero and hero.get("layout") not in {"table", "form", "filter"}:
                style = dict(hero.get("style") or {})
                hero["position"] = "hero"
                hero["col_span"] = 12
                style.setdefault("surface_level", "elevated")
                style.setdefault("text_class", "si-text-display")
                hero["style"] = style
            right = section_map.get(right_id) if right_id else None
            if right:
                style = dict(right.get("style") or {})
                right["position"] = "sidebar"
                right["col_span"] = 12
                if right.get("layout") in {"table", "gallery", "form"}:
                    right["layout"] = "list"
                    right["component"] = _component_for_layout(right, "list")
                style["sidebar_side"] = "right"
                style["sidebar_width"] = 3
                style.setdefault("bg", "white")
                style.setdefault("shadow", "md")
                right["style"] = style

    # Keep at least one data/work section in main on every normal page.
    for page in normal_pages:
        refs = [_ref_id(ref) for ref in (page.get("sections") or []) if _ref_id(ref)]
        content = [section_map.get(sid) for sid in refs if _is_content_region_section(section_map.get(sid) or {})]
        if content and not any((s or {}).get("position", "main") == "main" for s in content):
            content[-1]["position"] = "main"
            content[-1]["col_span"] = 12
    return pages, sections

def generate_candidate_set(interface_id: str, prompt: str = "") -> str:
    """Generate and save exactly 3 candidates from the current interface DSL and designer prompt."""
    try:
        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS, timeout=30)
        iface_resp.raise_for_status()
        iface = iface_resp.json()
        data = dict(iface.get("data") or {})
        pages = data.get("pages") or []
        sections = data.get("sections") or []
        if not pages or not sections:
            return "ERROR: Interface has no pages/sections to generate candidates from."

        # Parse prompt for explicit color anchors and layout constraints.
        # Unspecified dimensions remain free — explore mode still generates 3 distinct structures.
        gen_intent = _parse_generation_intent(prompt)
        intent_colors = gen_intent.get("colors") or []
        intent_layout = gen_intent.get("layout") or {}

        raw_base_tokens = dict(data.get("tokens") or {})
        if intent_colors:
            # Designer specified explicit colors — anchor all 3 variants to them
            anchored_tokens = _apply_intent_colors_to_tokens(
                _apply_prompt_style_overrides(raw_base_tokens, prompt), intent_colors
            )
            _expand_design_tokens(anchored_tokens)
        else:
            # No explicit colors — let _variant_tokens produce 3 distinct color themes
            anchored_tokens = None
            raw_base_tokens = _apply_prompt_style_overrides(raw_base_tokens, prompt)
            if not raw_base_tokens:
                _, raw_base_tokens = _candidate_design_spec(interface_id, 0, prompt=prompt)

        base_styling = {**dict(data.get("styling") or {}), **_prompt_styling_overrides(prompt)}
        results = []
        for index in range(3):
            layout_intent = _layout_intent_for_candidate("explore", prompt, index, pages, sections)
            # Apply explicit layout constraints on top of explore variation
            if intent_layout:
                _nav = intent_layout.get("nav")
                if _nav == "sidebar-left":
                    layout_intent.update({"nav": "sidebar-left", "sidebar_side": "left"})
                elif _nav == "sidebar-right":
                    layout_intent.update({"nav": "sidebar-right", "sidebar_side": "right"})
                elif _nav == "top":
                    layout_intent["nav"] = "top"
                if intent_layout.get("data_display"):
                    layout_intent["data_layout"] = intent_layout["data_display"]
                    layout_intent["forced_data_layout"] = intent_layout["data_display"]
                if intent_layout.get("density"):
                    layout_intent["density"] = intent_layout["density"]
                if intent_layout.get("full_width") is True:
                    layout_intent.update({"main_width": "full", "header_width": "full"})
            variant_pages = _apply_layout_intent_to_pages(pages, layout_intent)
            variant_sections = _apply_layout_intent_to_sections(sections, layout_intent, prompt)
            variant_pages, variant_sections = _apply_candidate_region_composition(variant_pages, variant_sections, index, prompt)
            variant_pages, variant_sections = _dedupe_agent_header_shells(variant_pages, variant_sections)
            variant_sections = _apply_chrome_style(variant_sections, intent_layout.get("header_style"), intent_layout.get("footer_style"))
            if anchored_tokens is not None:
                tokens = copy.deepcopy(anchored_tokens)
                tokens["design.variant_index"] = str(index)
                _expand_design_tokens(tokens)
            else:
                tokens = _variant_tokens(raw_base_tokens, prompt, index)
            styling = dict(base_styling or {})
            styling["variantIndex"] = index
            styling["variantName"] = layout_intent.get("name") or ("Card Gallery", "Data Table", "Showcase")[index]
            styling["layoutIntent"] = layout_intent
            result = validate_and_save_candidate(
                interface_id=interface_id,
                candidate_index=index,
                name=_candidate_variant_name(prompt, index),
                description=f"Agent-generated candidate {index + 1} using '{prompt or 'current'}' as the designer requirement.",
                pages=json.dumps(variant_pages),
                sections=json.dumps(variant_sections),
                tokens=json.dumps(tokens) if tokens else "",
                styling=json.dumps(styling) if styling else "",
                prompt=prompt,
                variation_strategy=layout_intent.get("name", ("balanced", "dense table-oriented", "expressive gallery-oriented")[index]),
            )
            results.append(result)
            if not str(result).startswith("OK:"):
                return f"ERROR: candidate {index} failed: {result}"
            render_candidate_preview_func(interface_id, index)
        return "OK: generated and saved 3 candidates. " + " | ".join(results)
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
        intent = _parse_regeneration_intent(designer_requirements)
        layout_change_requested = intent["change_layout"]
        color_change_requested = intent["change_color"]
        intent_colors = intent.get("colors") or []
        intent_layout = intent.get("layout") or {}
        # Compute shared tokens once — same color applied to all 3 variants so
        # layout-only and color-only requests don't bleed into each other.
        raw_base_tokens = copy.deepcopy(base.get("tokens") or {})
        if color_change_requested:
            if intent_colors:
                # LLM returned specific component targets — apply them directly
                shared_tokens = _apply_intent_colors_to_tokens(raw_base_tokens, intent_colors)
            else:
                # LLM detected color change but no specifics — fall back to string matching
                shared_tokens = _apply_prompt_style_overrides(raw_base_tokens, designer_requirements)
                scoped = _prompt_scoped_color_overrides(designer_requirements)
                if scoped:
                    shared_tokens.update(scoped)
            _expand_design_tokens(shared_tokens)
        else:
            shared_tokens = raw_base_tokens
        base_styling = {**dict(base.get("styling") or {}), **_prompt_styling_overrides(designer_requirements)}
        results = []
        for index in range(3):
            layout_intent = _layout_intent_for_candidate("refine", designer_requirements, index, pages, sections)
            # Merge LLM-extracted layout spec — overrides string-matching defaults with specific values
            if intent_layout:
                _nav = intent_layout.get("nav")
                if _nav == "sidebar-left":
                    layout_intent.update({"nav": "sidebar-left", "sidebar_side": "left"})
                elif _nav == "sidebar-right":
                    layout_intent.update({"nav": "sidebar-right", "sidebar_side": "right"})
                elif _nav == "top":
                    layout_intent["nav"] = "top"
                if intent_layout.get("data_display"):
                    layout_intent["data_layout"] = intent_layout["data_display"]
                    layout_intent["forced_data_layout"] = intent_layout["data_display"]
                if intent_layout.get("density"):
                    layout_intent["density"] = intent_layout["density"]
                if intent_layout.get("full_width") is True:
                    layout_intent.update({"main_width": "full", "header_width": "full"})
            if layout_change_requested:
                variant_pages = _apply_layout_intent_to_pages(pages, layout_intent)
                variant_sections = _apply_layout_intent_to_sections(sections, layout_intent, designer_requirements)
                variant_pages, variant_sections = _apply_candidate_region_composition(variant_pages, variant_sections, index, designer_requirements)
            else:
                variant_pages = copy.deepcopy(pages)
                variant_sections = copy.deepcopy(sections)
            variant_pages, variant_sections = _dedupe_agent_header_shells(variant_pages, variant_sections)
            variant_sections = _apply_chrome_style(variant_sections, intent_layout.get("header_style"), intent_layout.get("footer_style"))
            tokens = copy.deepcopy(shared_tokens)
            tokens["design.variant_index"] = str(index)
            _expand_design_tokens(tokens)
            styling = dict(base_styling or {})
            styling["variantIndex"] = index
            styling["variantName"] = layout_intent.get("name") or ("Selected Refinement", "Selected Table", "Selected Showcase")[index]
            styling["layoutIntent"] = layout_intent
            result = validate_and_save_candidate(
                interface_id=interface_id,
                candidate_index=index,
                name=f"{_candidate_variant_name(designer_requirements, index)} Regen",
                description=f"Regenerated from candidate {selected_candidate_index + 1} with {styling['variantName']} structure.",
                pages=json.dumps(variant_pages),
                sections=json.dumps(variant_sections),
                tokens=json.dumps(tokens) if tokens else "",
                styling=json.dumps(styling) if styling else "",
                prompt=designer_requirements,
                derived_from=str(selected_candidate_index),
                designer_requirements=designer_requirements,
                variation_strategy=layout_intent.get("name", styling["variantName"]),
            )
            results.append(result)
            if not str(result).startswith("OK:"):
                return f"ERROR: regenerated candidate {index} failed: {result}"
            render_candidate_preview_func(interface_id, index)
        return "OK: regenerated and saved 3 candidates. " + " | ".join(results)
    except Exception as e:
        return f"ERROR: regenerate_candidate_set failed: {e}"

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
get_candidate_regeneration_context_tool = FunctionTool(func=get_candidate_regeneration_context)
generate_candidate_set_tool = FunctionTool(func=generate_candidate_set)
regenerate_candidate_set_tool = FunctionTool(func=regenerate_candidate_set)
validate_save_candidate_tool = FunctionTool(func=validate_and_save_candidate)
render_candidate_preview_tool = FunctionTool(func=render_candidate_preview_func)
list_design_specs_tool = FunctionTool(func=list_design_specs_tool_func)
get_design_system_tool = FunctionTool(func=get_design_system_tool_func)
apply_design_system_to_interface_tool = FunctionTool(func=apply_design_system_to_interface_tool_func)
select_design_specs_for_interface_func.__name__ = "select_design_specs_for_interface"
select_design_specs_for_interface_tool = FunctionTool(func=select_design_specs_for_interface_func)
