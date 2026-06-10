"""Prompts for candidate generation and regeneration."""

import json

from llm.interface_generator.interface_schemas import (
    _CANDIDATE_FULL_SCHEMA,
    _CANDIDATE_TOKENS_EXAMPLE,
)


GENERATE_CANDIDATES_SYSTEM_PROMPT = (
    "You are a UI designer creating 3 structurally and visually distinct "
    "interface layout candidates. Follow the schema and role rules exactly.\n\n"
    f"{_CANDIDATE_FULL_SCHEMA}"
)


REGENERATE_CANDIDATES_SYSTEM_PROMPT = (
    "You are a UI designer creating visual refinements of a selected interface "
    "design. Follow the schema and role rules exactly.\n\n"
    f"{_CANDIDATE_FULL_SCHEMA}"
)


def build_generate_candidates_prompt(
    page_skeleton: list,
    section_skeleton: list,
    designer_prompt: str,
) -> str:
    diversity_rules = (
        "Generate exactly 3 structurally and visually distinct candidates.\n"
        "Each candidate MUST follow user requirement:\n"
        "Each candidate MUST also differ in axes that user did not specify:\n"
        "Every page must have navigation unless user requires otherwise.\n"
        "When the designer prompt does not specify width, vary page widths across the 3 candidates: contained, wide, and full. "
        "When the designer prompt specifies contained/wide/full, obey that exact width preference.\n"
        "Respect the designer prompt and choose colors as a UI designer. Do not use hard-coded color mappings unless the prompt provides exact hex values.\n"
        "Candidate names/descriptions must describe layout, navigation, density, or workflow emphasis; do not mention color names unless the designer prompt explicitly asks for colors.\n"
        "Keep object_form -> form, object_detail -> detail, activity_* layouts unchanged.\n"
    )

    prompt_text = designer_prompt or "(no specific requirements - explore freely)"
    return (
        f"Pages: {json.dumps(page_skeleton, ensure_ascii=False)}\n"
        f"Sections: {json.dumps(section_skeleton, ensure_ascii=False)}\n\n"
        f"DESIGNER PROMPT: {prompt_text}\n\n"
        f"{diversity_rules}\n\n"
        "Output exactly 3 candidates as JSON. Use ONLY the section/page ids provided above.\n"
        '{"candidates": [{"name": "...", "pages": [{"id": "...", "layout": {"value": "vertical", "main_width": "...", "header_width": "...", "footer_width": "..."}, "gap": {"value": "..."}}], '
        '"sections": [{"id": "...", "layout": "...", "component": "...", "position": "...", "col_span": 12, "style": {"color": "accent", "density": "...", "columns": "...", "shadow": "...", "bg": "...", "nav_height": "...", "sidebar_side": "...", "sidebar_width": 3}}], '
        '"styling": {"fontFamily": "...", "textSize": "xs|sm|md|lg|xl", "accentColor": "#hex", "accentSecondary": "#hex", "backgroundColor": "#hex", "textColor": "#hex", "radius": 8, "buttonStyle": "...", "cardHover": "...", "divider": "...", "pageMaxWidth": "..."}, '
        f'{_CANDIDATE_TOKENS_EXAMPLE}' + '}]}'
    )


def build_regenerate_candidates_prompt(
    page_skeleton: list,
    section_skeleton: list,
    designer_requirements: str,
    base_styling: dict,
) -> str:
    base_ctx = ", ".join(
        f"{key}={value}"
        for key, value in {
            "fontFamily": base_styling.get("fontFamily", "inter"),
            "textSize": base_styling.get("textSize", "md"),
            "accentColor": base_styling.get("accentColor", "#2563eb"),
            "backgroundColor": base_styling.get("backgroundColor", "#f9fafb"),
            "textColor": base_styling.get("textColor", "#111827"),
            "radius": base_styling.get("radius", 8),
            "buttonStyle": base_styling.get("buttonStyle", "solid"),
            "cardHover": base_styling.get("cardHover", "none"),
        }.items()
    )

    diversity_rules = (
        "Generate exactly 3 meaningfully different refinements of the base candidate.\n"
        "Each variant MUST differ from the others on structural or interaction axes that user did not lock:\n"
        "  - typography (fontFamily, textSize)\n"
        "  - density (compact vs normal vs spacious)\n"
        "  - border radius (0 vs 8 vs 16 vs 24)\n"
        "  - button style (solid vs outline vs ghost vs gradient)\n"
        "  - card hover effect (lift vs glow vs border vs none)\n"
        "  - page width (contained vs wide vs full; obey exact width requests when provided)\n"
        "  - nav placement (header vs sidebar)\n"
        "Apply the DESIGNER REQUIREMENTS to all 3 variants. "
        "When the designer requirements do not specify width, vary page widths across the 3 candidates: contained, wide, and full. "
        "When the designer requirements specify contained/wide/full, obey that exact width preference. "
        "Preserve the base candidate's section roles and data bindings. "
        "You may change layout/component/position for collection sections (object_collection, child_collection) "
        "but must keep object_form as form, object_detail as detail, activity_* layouts unchanged.\n"
        "Candidate names/descriptions must describe layout, navigation, density, or workflow emphasis; do not mention color names unless the designer requirements explicitly ask for colors.\n"
        "Choose colors as a UI designer. Do not use hard-coded color mappings unless the requirements provide exact hex values."
    )

    requirements_text = designer_requirements or "(explore visual variations of the base candidate)"
    return (
        f"Pages: {json.dumps(page_skeleton, ensure_ascii=False)}\n"
        f"Sections: {json.dumps(section_skeleton, ensure_ascii=False)}\n\n"
        f"BASE CANDIDATE STYLING (starting point - inherit unless requirements override): {base_ctx}\n"
        f"DESIGNER REQUIREMENTS: {requirements_text}\n\n"
        f"{diversity_rules}\n\n"
        "Output exactly 3 candidates as JSON. Use ONLY the section/page ids provided above.\n"
        '{"candidates": [{"name": "...", "pages": [{"id": "...", "layout": {"value": "vertical", "main_width": "...", "header_width": "...", "footer_width": "..."}, "gap": {"value": "..."}}], '
        '"sections": [{"id": "...", "layout": "...", "component": "...", "position": "...", "col_span": 12, "style": {"color": "accent", "density": "...", "columns": "...", "shadow": "...", "bg": "...", "nav_height": "...", "sidebar_side": "...", "sidebar_width": 3}}], '
        '"styling": {"fontFamily": "...", "textSize": "xs|sm|md|lg|xl", "accentColor": "#hex", "accentSecondary": "#hex", "backgroundColor": "#hex", "textColor": "#hex", "radius": 8, "buttonStyle": "...", "cardHover": "...", "divider": "...", "pageMaxWidth": "..."}, '
        f'{_CANDIDATE_TOKENS_EXAMPLE}' + '}]}'
    )
