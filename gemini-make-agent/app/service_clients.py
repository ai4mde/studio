"""Shared service endpoints and small API helpers."""

import os

import requests


METADATA_API_BASE = os.getenv("METADATA_API_BASE", "http://studio-api:8000/api/v1/metadata")
PROTOTYPE_API_BASE = os.getenv("PROTOTYPE_API_BASE", "http://studio-prototypes:8010")
_METADATA_API_KEY = os.getenv("METADATA_API_KEY")
_AUTH_HEADERS = {"Authorization": f"Bearer {_METADATA_API_KEY}"} if _METADATA_API_KEY else {}


def render_candidate_preview_func(interface_id: str, candidate_index: int) -> str:
    try:
        resp = requests.post(
            f"{METADATA_API_BASE}/interfaces/{interface_id}/candidates/{candidate_index}/render/",
            headers=_AUTH_HEADERS,
            timeout=60,
        )
        if resp.ok:
            return f"OK: preview rendered for candidate {candidate_index}."
        return f"Render failed ({resp.status_code}): {resp.text}"
    except Exception as e:
        return f"Error rendering preview: {e}"
