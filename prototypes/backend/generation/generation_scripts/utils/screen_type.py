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

# Exported type alias so templates can reference it
SCREEN_TYPES = ("list", "dashboard", "form", "modal", "wizard", "activity")


def detect_screen_type(page: "Page") -> str:
    """
    Classify a Page into one of: list | dashboard | form | modal | wizard | activity.

    Rules (in priority order):
    1. activity page  → 'activity'
    2. name contains dashboard keywords → 'dashboard'
    3. single section, only create op  → 'form'
    4. name contains form keywords, single section → 'form'
    5. any CRUD operation present → 'list'
    6. default → 'list'
    """
    if getattr(page, "type", "normal") == "activity":
        return "activity"

    name_lower = page.name.lower()

    if any(kw in name_lower for kw in _DASHBOARD_KEYWORDS):
        return "dashboard"

    sections = page.section_components
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

    return "list"
