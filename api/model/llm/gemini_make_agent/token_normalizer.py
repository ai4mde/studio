import re

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

def _text_on_color(value: object) -> str:
    return "#ffffff" if _is_dark_hex(value) else "#111827"

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
    on_accent = _text_on_color(accent)

    tokens.setdefault("page.bg.hex", page_bg)
    tokens.setdefault("page.text.hex", text)
    tokens["page.body.bg"] = f"bg-[{page_bg}]"
    tokens["page.body.text"] = f"text-[{text}]"
    tokens.setdefault("region.header.bg_hex", accent)
    tokens.setdefault("region.header.bg", f"bg-[{accent}]")
    tokens.setdefault("region.header.text_hex", on_accent)
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
    tokens.setdefault("button.primary.text_hex", on_accent)
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
    tokens.setdefault("nav.text_hex", on_accent)
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

__all__ = [
    '_as_list',
    '_contrast_ratio',
    '_ensure_readable_text_tokens',
    '_expand_design_tokens',
    '_hex_to_rgb',
    '_is_dark_hex',
    '_name_id',
    '_needs_contrast_fix',
    '_page_name',
    '_relative_luminance',
    '_section_id',
    '_set_readable_token',
    '_text_on_color',
    '_workflow_page_name',
]
