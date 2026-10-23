"""Preflight runs before the generator creates a project/output directory."""
import sys
from pathlib import Path

from utils.ai_generation import validate_metadata

if __name__ == "__main__":
    validate_metadata(Path(sys.argv[1]).read_text())
    print("[AI4MDE] metadata configuration and binding preflight passed")
