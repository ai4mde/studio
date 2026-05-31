from app.token_normalizer import (
    _expand_design_tokens,
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


def test_section_id_is_stable_and_safe():
    assert _section_id("Product Detail: Images!") == "product_detail_images"
