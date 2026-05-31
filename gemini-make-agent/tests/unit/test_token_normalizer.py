from app.token_normalizer import (
    _expand_design_tokens,
    _prompt_scoped_color_overrides,
    _section_id,
)


def test_expand_design_tokens_fills_renderable_defaults():
    tokens = _expand_design_tokens({
        "accent.hex": "#2563eb",
        "page.body.bg_hex": "#ffffff",
        "page.body.text_hex": "#111827",
    })

    assert tokens["region.header.bg_hex"] == "#2563eb"
    assert tokens["button.primary.bg_hex"] == "#2563eb"
    assert tokens["input.border_focus_hex"] == "#2563eb"
    assert tokens["component.card.bg"].startswith("bg-[")


def test_expand_design_tokens_preserves_fine_grained_llm_tokens():
    tokens = _expand_design_tokens({
        "accent.hex": "#111827",
        "region.header.bg_hex": "#2563eb",
        "input.bg_hex": "#16a34a",
        "button.primary.bg_hex": "#db2777",
    })

    assert tokens["region.header.bg_hex"] == "#2563eb"
    assert tokens["input.bg_hex"] == "#16a34a"
    assert tokens["button.primary.bg_hex"] == "#db2777"


def test_prompt_scoped_color_overrides_for_header_search_and_button():
    overrides = _prompt_scoped_color_overrides(
        "make header blue, search bar green, button pink"
    )

    assert overrides["region.header.bg_hex"] == "#2563eb"
    assert overrides["input.bg_hex"] == "#16a34a"
    assert overrides["button.primary.bg_hex"] == "#db2777"


def test_prompt_scoped_color_keeps_button_separate_from_accent():
    overrides = _prompt_scoped_color_overrides("green accent, purple button")

    assert overrides["accent.hex"] == "#16a34a"
    assert overrides["region.header.bg_hex"] == "#16a34a"
    assert overrides["button.primary.bg_hex"] == "#7c3aed"


def test_prompt_scoped_color_handles_accent_before_button_with_and():
    overrides = _prompt_scoped_color_overrides("make accent green and button purple")

    assert overrides["accent.hex"] == "#16a34a"
    assert overrides["button.primary.bg_hex"] == "#7c3aed"


def test_prompt_scoped_color_handles_button_before_accent():
    overrides = _prompt_scoped_color_overrides("purple button, green accent")

    assert overrides["accent.hex"] == "#16a34a"
    assert overrides["button.primary.bg_hex"] == "#7c3aed"


def test_prompt_scoped_color_overrides_supports_hex_values():
    overrides = _prompt_scoped_color_overrides(
        "set the header to #123456 and buttons #abcdef"
    )

    assert overrides["region.header.bg_hex"] == "#123456"
    assert overrides["button.primary.bg_hex"] == "#abcdef"


def test_section_id_is_stable_and_safe():
    assert _section_id("Product Detail: Images!") == "product_detail_images"
