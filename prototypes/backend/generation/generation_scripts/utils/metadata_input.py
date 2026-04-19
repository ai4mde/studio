from pathlib import Path


def resolve_metadata_arg(raw: str) -> str:
    """Return metadata JSON, allowing callers to pass '@/path/to/file.json'."""
    if not raw:
        return raw
    if raw.startswith("@"):
        return Path(raw[1:]).read_text(encoding="utf-8")
    return raw