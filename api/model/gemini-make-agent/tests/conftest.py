"""Stub google.adk so unit tests can run without the full SDK installed."""
import sys
from unittest.mock import MagicMock

for _mod in [
    "google.adk",
    "google.adk.agents",
    "google.adk.tools",
    "google.adk.apps",
]:
    sys.modules.setdefault(_mod, MagicMock())
