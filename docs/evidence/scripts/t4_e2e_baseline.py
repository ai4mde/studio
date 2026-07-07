import json
from pathlib import Path

from django.conf import settings

from shared_models.models import BookLoan, Customer


log_path = Path(settings.BASE_DIR) / "ai_invocations.jsonl"
lines = (
    [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if log_path.exists()
    else []
)
last_bookloan = BookLoan.objects.order_by("-id").first()
alice = Customer.objects.get(name="alice")
result = {
    "bookloan_count": BookLoan.objects.count(),
    "max_bookloan_id": last_bookloan.id if last_bookloan else None,
    "alice_id": alice.id,
    "alice_reading_plan": alice.reading_plan,
    "jsonl_lines": len(lines),
}
if alice.reading_plan not in ("", None):
    raise AssertionError(f"alice.reading_plan baseline must be empty, got {alice.reading_plan!r}")
print(json.dumps(result, indent=2, sort_keys=True))
