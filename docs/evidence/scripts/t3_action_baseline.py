import json
from pathlib import Path

from django.conf import settings

from shared_models.models import Customer


log_path = Path(settings.BASE_DIR) / "ai_invocations.jsonl"
lines = (
    [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if log_path.exists()
    else []
)
alice = Customer.objects.get(name="alice")
payload = {
    "alice_id": alice.id,
    "alice_reading_plan": alice.reading_plan,
    "jsonl_lines": len(lines),
}
if alice.reading_plan not in ("", None):
    raise AssertionError(f"alice.reading_plan baseline must be empty, got {alice.reading_plan!r}")
print(json.dumps(payload, indent=2, sort_keys=True))
