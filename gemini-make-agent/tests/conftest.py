"""Stub google.adk so unit tests can run without the full SDK installed."""
import importlib.util
import os
import sys
from unittest.mock import MagicMock

try:
    _has_adk = importlib.util.find_spec("google.adk") is not None
except ModuleNotFoundError:
    _has_adk = False

if not _has_adk:
    os.environ["ADK_STUBBED_FOR_TESTS"] = "1"
    for _mod in [
        "google.adk",
        "google.adk.agents",
        "google.adk.tools",
        "google.adk.apps",
        "google.adk.models",
        "google.adk.models.lite_llm",
        "google.adk.tools.mcp_tool",
        "mcp",
    ]:
        sys.modules.setdefault(_mod, MagicMock())
