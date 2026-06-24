"""
Compatibility wrapper for the root restore_hospital script.

The canonical script lives at scripts/restore_hospital.py. Keeping this thin
entry point preserves the old path without duplicating the full restore data.
"""

from pathlib import Path


ROOT_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "restore_hospital.py"

exec(compile(ROOT_SCRIPT.read_text(encoding="utf-8"), str(ROOT_SCRIPT), "exec"), globals())
