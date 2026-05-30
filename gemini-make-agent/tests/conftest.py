"""Stub google.adk so unit tests can run without the full SDK installed."""
import sys
from unittest.mock import MagicMock

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
