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

def _first_token_value(mapping: dict, keys: list[str], default: str | None = None) -> str | None:
    for key in keys:
        if mapping.get(key):
            return mapping[key]
    return default

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

_PROMPT_COLOR_THEMES = {
    "purple": {"accent": "#7c3aed", "secondary": "#c084fc", "page": "#faf5ff", "surface": "#ffffff", "border": "#ddd6fe"},
    "violet": {"accent": "#7c3aed", "secondary": "#c084fc", "page": "#faf5ff", "surface": "#ffffff", "border": "#ddd6fe"},
    "indigo": {"accent": "#4f46e5", "secondary": "#818cf8", "page": "#eef2ff", "surface": "#ffffff", "border": "#c7d2fe"},
    "blue": {"accent": "#2563eb", "secondary": "#60a5fa", "page": "#eff6ff", "surface": "#ffffff", "border": "#bfdbfe"},
    "sky": {"accent": "#0284c7", "secondary": "#7dd3fc", "page": "#f0f9ff", "surface": "#ffffff", "border": "#bae6fd"},
    "cyan": {"accent": "#0891b2", "secondary": "#67e8f9", "page": "#ecfeff", "surface": "#ffffff", "border": "#a5f3fc"},
    "aqua": {"accent": "#0891b2", "secondary": "#67e8f9", "page": "#ecfeff", "surface": "#ffffff", "border": "#a5f3fc"},
    "teal": {"accent": "#0d9488", "secondary": "#5eead4", "page": "#f0fdfa", "surface": "#ffffff", "border": "#99f6e4"},
    "turquoise": {"accent": "#0d9488", "secondary": "#5eead4", "page": "#f0fdfa", "surface": "#ffffff", "border": "#99f6e4"},
    "green": {"accent": "#16a34a", "secondary": "#86efac", "page": "#f0fdf4", "surface": "#ffffff", "border": "#bbf7d0"},
    "emerald": {"accent": "#059669", "secondary": "#6ee7b7", "page": "#ecfdf5", "surface": "#ffffff", "border": "#a7f3d0"},
    "lime": {"accent": "#84cc16", "secondary": "#bef264", "page": "#f7fee7", "surface": "#ffffff", "border": "#d9f99d", "text": "#111827", "muted": "#365314"},
    "yellow": {"accent": "#facc15", "secondary": "#fde68a", "page": "#fefce8", "surface": "#ffffff", "border": "#fde68a", "text": "#111827", "muted": "#713f12"},
    "amber": {"accent": "#f59e0b", "secondary": "#fcd34d", "page": "#fffbeb", "surface": "#ffffff", "border": "#fde68a", "text": "#111827", "muted": "#78350f"},
    "gold": {"accent": "#f59e0b", "secondary": "#fcd34d", "page": "#fffbeb", "surface": "#ffffff", "border": "#fde68a", "text": "#111827", "muted": "#78350f"},
    "orange": {"accent": "#f97316", "secondary": "#fdba74", "page": "#fff7ed", "surface": "#ffffff", "border": "#fed7aa"},
    "rose": {"accent": "#e11d48", "secondary": "#fb7185", "page": "#fff1f2", "surface": "#ffffff", "border": "#fecdd3"},
    "pink": {"accent": "#db2777", "secondary": "#f9a8d4", "page": "#fdf2f8", "surface": "#ffffff", "border": "#fbcfe8"},
    "red": {"accent": "#dc2626", "secondary": "#f87171", "page": "#fef2f2", "surface": "#ffffff", "border": "#fecaca"},
    "navy": {"accent": "#1e3a8a", "secondary": "#60a5fa", "page": "#eff6ff", "surface": "#ffffff", "border": "#bfdbfe"},
    "brown": {"accent": "#92400e", "secondary": "#d97706", "page": "#fffbeb", "surface": "#ffffff", "border": "#fed7aa"},
    "beige": {"accent": "#d6b68a", "secondary": "#ead7bb", "page": "#faf7f0", "surface": "#ffffff", "border": "#ead7bb", "text": "#1f2937", "muted": "#6b4f2a"},
    "tan": {"accent": "#c08457", "secondary": "#e7c6a3", "page": "#faf7f0", "surface": "#ffffff", "border": "#e7c6a3", "text": "#1f2937", "muted": "#6b4f2a"},
    "cream": {"accent": "#d6b68a", "secondary": "#ead7bb", "page": "#fffaf0", "surface": "#ffffff", "border": "#ead7bb", "text": "#1f2937", "muted": "#6b4f2a"},
    "dark": {"accent": "#8b5cf6", "secondary": "#22d3ee", "page": "#0f172a", "surface": "#111827", "border": "#334155", "text": "#f8fafc", "muted": "#cbd5e1"},
    "black": {"accent": "#111827", "secondary": "#6b7280", "page": "#f9fafb", "surface": "#ffffff", "border": "#d1d5db"},
    "slate": {"accent": "#475569", "secondary": "#94a3b8", "page": "#f8fafc", "surface": "#ffffff", "border": "#cbd5e1"},
    "zinc": {"accent": "#52525b", "secondary": "#a1a1aa", "page": "#fafafa", "surface": "#ffffff", "border": "#d4d4d8"},
    "neutral": {"accent": "#525252", "secondary": "#a3a3a3", "page": "#fafafa", "surface": "#ffffff", "border": "#d4d4d4"},
}

_COLOR_KEYWORDS = {
    "purple": "#7c3aed",
    "violet": "#7c3aed",
    "indigo": "#4f46e5",
    "blue": "#2563eb",
    "sky": "#0284c7",
    "cyan": "#0891b2",
    "aqua": "#0891b2",
    "teal": "#0d9488",
    "turquoise": "#0d9488",
    "green": "#16a34a",
    "emerald": "#059669",
    "lime": "#84cc16",
    "yellow": "#facc15",
    "amber": "#f59e0b",
    "gold": "#f59e0b",
    "orange": "#f97316",
    "rose": "#e11d48",
    "pink": "#db2777",
    "red": "#dc2626",
    "navy": "#1e3a8a",
    "brown": "#92400e",
    "beige": "#d6b68a",
    "tan": "#c08457",
    "cream": "#d6b68a",
    "dark": "#111827",
    "black": "#111827",
    "slate": "#475569",
    "zinc": "#52525b",
    "neutral": "#525252",
    "gray": "#6b7280",
    "grey": "#6b7280",
    "white": "#ffffff",
}

_ZH_COLOR_KEYWORDS = {
    "\u9ec4": "yellow",
    "\u7d2b": "purple",
    "\u84dd": "blue",
    "\u85cd": "blue",
    "\u7eff": "green",
    "\u7da0": "green",
    "\u9752": "teal",
    "\u975b": "indigo",
    "\u6a59": "orange",
    "\u7c89": "pink",
    "\u7ea2": "red",
    "\u7d05": "red",
    "\u767d": "white",
    "\u9ed1": "black",
    "\u7070": "slate",
    "\u68d5": "brown",
    "\u7c73": "beige",
    "\u91d1": "gold",
    "紫": "purple",
    "蓝": "blue",
    "绿": "green",
    "橙": "orange",
    "粉": "pink",
    "红": "red",
    "黑": "black",
    "灰": "slate",
}

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
    on_color = _text_on_color(color_hex)
    surface_color = page if theme else color_hex
    if scope == "button":
        overrides.update({
            "button.primary.bg_hex": color_hex,
            "button.primary.border_hex": color_hex,
            "button.primary.text_hex": on_color,
        })
        if color_name == "red":
            overrides.update({
                "button.danger.bg_hex": color_hex,
                "button.danger.border_hex": color_hex,
            })
    elif scope == "nav":
        overrides.update({
            "nav.bg_hex": color_hex,
            "nav.text_hex": on_color,
        })
    elif scope == "header":
        overrides.update({
            "region.header.bg_hex": color_hex,
            "region.header.text_hex": on_color,
        })
    elif scope == "footer":
        overrides.update({
            "region.footer.bg_hex": color_hex,
            "region.footer.text_hex": on_color,
        })
    elif scope == "sidebar":
        overrides.update({
            "region.sidebar.bg_hex": surface_color,
            "region.sidebar.text_hex": "#ffffff" if color_name in {"black", "dark", "slate"} else overrides.get("page.body.text_hex", "#111827"),
        })
    elif scope == "background":
        overrides.update({
            "page.body.bg_hex": page,
            "page.bg.hex": page,
            "region.main.bg_hex": page,
        })
    elif scope == "main":
        overrides.update({"region.main.bg_hex": surface_color})
    elif scope == "card":
        overrides.update({
            "component.card.bg_hex": surface_color,
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
            "input.bg_hex": color_hex,
            "input.border_focus_hex": color_hex,
            "input.border_hex": border,
            "input.text_hex": on_color,
        })
    elif scope == "table":
        overrides.update({
            "table.header.bg_hex": surface_color,
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
            "badge.info.text_hex": on_color,
        })
    elif scope == "accent":
        overrides.update({
            "accent.hex": color_hex,
            "color.secondary.hex": secondary,
            "region.header.bg_hex": color_hex,
            "region.header.text_hex": on_color,
            "region.footer.bg_hex": color_hex,
            "region.footer.text_hex": on_color,
            "nav.bg_hex": color_hex,
            "nav.text_hex": on_color,
            "input.border_focus_hex": color_hex,
            "badge.info.bg_hex": color_hex,
            "badge.info.text_hex": on_color,
        })
        overrides.setdefault("button.primary.bg_hex", color_hex)
        overrides.setdefault("button.primary.border_hex", color_hex)
        overrides.setdefault("button.primary.text_hex", on_color)
        overrides.setdefault("button.ghost.text_hex", color_hex)
        overrides.setdefault("button.link.text_hex", color_hex)

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
        ("input", ("input", "field", "form field", "search", "searchbar", "search bar")),
        ("table", ("table", "grid")),
        ("link", ("link", "links")),
        ("badge", ("badge", "tag", "pill")),
        ("accent", ("accent", "primary color", "theme color")),
    )
    color_words = "|".join(re.escape(name) for name in _COLOR_KEYWORDS)
    direct_scopes = (
        ("button", ("button", "buttons", "cta", "action")),
        ("nav", ("nav", "navbar", "navigation", "menu")),
        ("header", ("header", "topbar", "top bar")),
        ("footer", ("footer",)),
        ("sidebar", ("sidebar", "side nav", "side bar")),
        ("background", ("background", "page background", "body")),
        ("main", ("main", "content")),
        ("card", ("card", "cards", "panel", "tile")),
        ("input", ("input", "field", "form field", "search", "searchbar", "search bar")),
        ("table", ("table", "grid")),
        ("link", ("link", "links")),
        ("badge", ("badge", "tag", "pill")),
    )
    clauses = [c.strip() for c in re.split(r"[,.;\n]|(?:\s+\b(?:and|but|while|whereas)\b\s+)", text) if c.strip()]
    for scope, terms in direct_scopes:
        target_words = "|".join(re.escape(term) for term in terms)
        matched = False
        for clause in clauses:
            for pattern in (
                rf"\b(?:make|set|turn|use)?\s*(?:the\s+)?(?:{target_words})s?\s+(?:bar\s+)?(?:to\s+|as\s+)?(?P<color>{color_words}|#[0-9a-fA-F]{{6}})\b",
                rf"\b(?P<color>{color_words}|#[0-9a-fA-F]{{6}})\s+(?:{target_words})s?\b",
            ):
                match = re.search(pattern, clause)
                if match:
                    color_name = match.group("color")
                    _apply_scoped_color(overrides, scope, color_name, _color_word_to_hex(color_name))
                    matched = True
                    break
            if matched:
                break

    for scope, terms in scopes:
        if (
            (scope == "button" and "button.primary.bg_hex" in overrides)
            or (scope == "header" and "region.header.bg_hex" in overrides)
            or (scope == "input" and "input.bg_hex" in overrides)
            or (scope == "nav" and "nav.bg_hex" in overrides)
            or (scope == "footer" and "region.footer.bg_hex" in overrides)
            or (scope == "sidebar" and "region.sidebar.bg_hex" in overrides)
            or (scope == "background" and "page.body.bg_hex" in overrides)
            or (scope == "main" and "region.main.bg_hex" in overrides)
            or (scope == "card" and "component.card.bg_hex" in overrides)
            or (scope == "table" and "table.header.bg_hex" in overrides)
            or (scope == "link" and "button.link.text_hex" in overrides)
            or (scope == "badge" and "badge.info.bg_hex" in overrides)
        ):
            continue
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
        on_color = _text_on_color(other_hex)
        overrides.update({
            "accent.hex": other_hex,
            "color.secondary.hex": secondary,
            "region.header.bg_hex": other_hex,
            "region.header.text_hex": on_color,
            "region.footer.bg_hex": other_hex,
            "region.footer.text_hex": on_color,
            "nav.bg_hex": other_hex,
            "nav.text_hex": on_color,
            "button.ghost.text_hex": other_hex,
            "button.link.text_hex": other_hex,
            "input.border_focus_hex": other_hex,
            "badge.info.bg_hex": other_hex,
            "badge.info.text_hex": on_color,
        })
        if page:
            overrides.setdefault("page.body.bg_hex", page)
            overrides.setdefault("page.bg.hex", page)
        if border:
            overrides.setdefault("region.border_hex", border)
            overrides.setdefault("region.border_strong_hex", border)
    return {key: value for key, value in overrides.items() if value}




__all__ = [
    '_COLOR_KEYWORDS',
    '_PROMPT_COLOR_THEMES',
    '_ZH_COLOR_KEYWORDS',
    '_apply_scoped_color',
    '_as_list',
    '_color_word_to_hex',
    '_contrast_ratio',
    '_ensure_readable_text_tokens',
    '_expand_design_tokens',
    '_find_color_near',
    '_first_token_value',
    '_hex_to_rgb',
    '_is_dark_hex',
    '_name_id',
    '_needs_contrast_fix',
    '_page_name',
    '_prompt_scoped_color_overrides',
    '_relative_luminance',
    '_section_id',
    '_set_readable_token',
    '_text_on_color',
    '_workflow_page_name',
]
