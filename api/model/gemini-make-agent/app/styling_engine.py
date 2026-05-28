import os
import re

DESIGN_SPECS_DIR = os.getenv("DESIGN_SPECS_DIR", "/design_specs")

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



__all__ = [
    'DESIGN_SPECS_DIR',
    '_COLOR_KEYWORDS',
    '_PROMPT_COLOR_THEMES',
    '_ZH_COLOR_KEYWORDS',
    '_apply_scoped_color',
    '_as_list',
    '_color_word_to_hex',
    '_contrast_ratio',
    '_design_spec_files',
    '_ensure_readable_text_tokens',
    '_expand_design_tokens',
    '_find_color_near',
    '_first_token_value',
    '_hex_to_rgb',
    '_is_dark_hex',
    '_name_id',
    '_needs_contrast_fix',
    '_normalize_radius',
    '_page_name',
    '_parse_design_md_to_tokens',
    '_parse_prose_colors',
    '_parse_prose_radius',
    '_prompt_color_scope_lock',
    '_prompt_color_theme',
    '_prompt_is_button_only_color',
    '_prompt_scoped_color_overrides',
    '_read_design_spec',
    '_relative_luminance',
    '_section_id',
    '_set_readable_token',
    '_workflow_page_name',
    '_yaml_block_objects',
    '_yaml_block_values',
]
