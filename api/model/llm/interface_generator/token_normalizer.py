import re


def _as_list(payload, key: str) -> list:
    """Return a list payload from a raw list or from a keyed wrapper dictionary."""
    if isinstance(payload, dict):
        return payload.get(key, []) or []
    return payload or []


def _name_id(value: str) -> str:
    """Normalize a free-form name into a stable identifier token."""
    value = re.sub(r"[^A-Za-z0-9_\s-]", "", str(value or ""))
    value = re.sub(r"[\s-]+", "_", value.strip())
    return value or "workflow_step"


def _page_name(value: str) -> str:
    """Convert a free-form label into the generated page class/name format."""
    return "_".join(part[:1].upper() + part[1:] for part in _name_id(value).split("_") if part)


def _workflow_page_name(value: str) -> str:
    """Build the generated workflow page name for an activity label."""
    return f"Workflow_{_page_name(value)}"


def _section_id(value: str) -> str:
    """Convert a free-form label into a stable section id."""
    return _name_id(value).lower()


def _sid(name: str) -> str:
    """Build section identifier value."""
    s = re.sub(r"[^a-zA-Z0-9]+", "_", str(name or "").strip()).strip("_").lower()
    return s or "section"


__all__ = [
    '_as_list',
    '_name_id',
    '_page_name',
    '_section_id',
    '_sid',
    '_workflow_page_name',
]
