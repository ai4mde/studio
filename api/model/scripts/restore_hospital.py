"""
Compatibility wrapper for the root restore_hospital script.

The canonical script lives at scripts/restore_hospital.py. Keeping this thin
entry point preserves the old path without duplicating the full restore data.
"""

from pathlib import Path


ROOT_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "restore_hospital.py"

import runpy
runpy.run_path(str(ROOT_SCRIPT), init_globals=globals(), run_name="__main__")
