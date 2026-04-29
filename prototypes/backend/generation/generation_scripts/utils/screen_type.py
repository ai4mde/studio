"""
Rule-based screen-type detection for the prototypes generation pipeline.

This mirrors the logic in the API agent's screen_type_node but runs entirely
inside the prototypes container without any LLM dependency.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.definitions.page import Page

_DASHBOARD_KEYWORDS = {"dashboard", "overview", "summary", "home", "kpi", "report", "analytics"}
_FORM_KEYWORDS = {"create", "new", "add", "edit", "update"}
_WIZARD_KEYWORDS = {"wizard", "setup", "registration", "onboarding", "stepper", "steps", "checkout"}
_MODAL_KEYWORDS = {"modal", "dialog", "popup", "overlay"}

# Exported type alias so templates can reference it
SCREEN_TYPES = ("list", "dashboard", "form", "modal", "wizard", "activity")


def detect_screen_type(page: "Page") -> str:
    """
    Classify a Page into one of: list | dashboard | form | modal | wizard | activity.

    Rules (in priority order):
    1. activity page  → 'activity'
    2. name contains dashboard keywords → 'dashboard'
    3. name contains wizard keywords, multiple sections → 'wizard'
    4. name contains modal keywords → 'modal'
    5. single section, only create op  → 'form'
    6. name contains form keywords, single section → 'form'
    7. multiple sections, all only create ops → 'wizard'
    8. default → 'list'
    """
    if getattr(page, "type", "normal") == "activity":
        return "activity"

    active_composition = getattr(page, "active_composition", {}) or {}
    page_archetype = str(active_composition.get("page_archetype") or "").lower()
    if page_archetype in {"dashboard", "analytics-dashboard"}:
        return "dashboard"
    if page_archetype in {"wizard", "checkout-wizard", "onboarding-wizard"}:
        return "wizard"
    if page_archetype in {"modal", "dialog"}:
        return "modal"
    if page_archetype in {"form", "detail-form"}:
        return "form"

    name_lower = page.name.lower()

    if any(kw in name_lower for kw in _DASHBOARD_KEYWORDS):
        return "dashboard"

    sections = page.section_components

    if any(kw in name_lower for kw in _WIZARD_KEYWORDS) and len(sections) > 1:
        return "wizard"

    if any(kw in name_lower for kw in _MODAL_KEYWORDS):
        return "modal"

    only_create = (
        len(sections) == 1
        and sections[0].has_create_operation
        and not sections[0].has_update_operation
        and not sections[0].has_delete_operation
    )
    if only_create:
        return "form"

    if any(kw in name_lower for kw in _FORM_KEYWORDS) and len(sections) == 1:
        return "form"

    # Multiple sections that all only have create → wizard
    if len(sections) > 1 and all(
        s.has_create_operation and not s.has_update_operation and not s.has_delete_operation
        for s in sections
    ):
        return "wizard"

    return "list"
