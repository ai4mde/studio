import json
from pathlib import Path

from django.conf import settings

from shared_models.models import BookLoan


log_path = Path(settings.BASE_DIR) / "ai_invocations.jsonl"
lines = (
    [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if log_path.exists()
    else []
)
last_bookloan = BookLoan.objects.order_by("-id").first()
print(
    json.dumps(
        {
            "bookloan_count": BookLoan.objects.count(),
            "max_bookloan_id": last_bookloan.id if last_bookloan else None,
            "jsonl_lines": len(lines),
        },
        indent=2,
        sort_keys=True,
    )
)
