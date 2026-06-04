"""Small prompt-intent helpers shared by tool guardrails and candidate generation."""


def prompt_layout_traits(prompt: str) -> dict:
    text = str(prompt or "").lower()
    return {
        "full": any(term in text for term in ("full width", "full-width", "edge to edge", "edge-to-edge", "full bleed", "full-bleed")),
        "wide": any(term in text for term in ("wide", "wider", "wide main", "wide content")),
        "contained": any(term in text for term in ("contained", "narrow", "centered", "center aligned")),
        "dashboard": any(term in text for term in ("dashboard", "admin", "analytics", "operational", "dense")),
        "sidebar": any(term in text for term in ("sidebar", "side nav", "left nav", "right nav", "rail")),
        "right_sidebar": any(term in text for term in ("right sidebar", "sidebar right", "right nav", "right rail")),
        "minimal": any(term in text for term in ("minimal", "clean", "simple", "focused")),
        "form": any(term in text for term in ("form", "wizard", "application", "onboarding")),
    }


def page_layout_dict(page: dict) -> dict:
    raw = page.get("layout") or {}
    if isinstance(raw, dict):
        out = dict(raw)
    elif raw:
        out = {"value": raw}
    else:
        out = {"value": "default"}
    return out
