# GENERATED - M07 user-action LLM invocation glue (do not edit by hand).
# Mirrors ai_hooks.py for the post_save case; here the trigger is an explicit user action.
import json
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings

from shared_models.models import Customer

LOG_PATH = Path(settings.BASE_DIR) / "ai_invocations.jsonl"


_AI_CONFIG__Customer__reading_plan = {'ai_config_version': '1.0',
 'context': {'relations': ['Loan', 'BookLoan', 'Book']},
 'model_profile': 'strong',
 'output': {'format': 'reading_plan', 'write_back': 'reading_plan'},
 'template': {'chain': ['reading_plan_analyze_taste_v1',
                        'reading_plan_recommend_v1',
                        'reading_plan_sequence_v1']},
 'trigger': {'class': 'Customer', 'type': 'user_action'}}


def generate_reading_plan(instance):
    from ai_runtime.reading_plan import run_reading_plan  # chain orchestration (Step 8)
    summary, result, mode = run_reading_plan(_AI_CONFIG__Customer__reading_plan, instance)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "invoke_chain",
        "trigger": "user_action",
        "model": instance.__class__.__name__,
        "pk": instance.pk,
        "model_profile": _AI_CONFIG__Customer__reading_plan.get("model_profile"),
        "mode": mode,
        "write_back": {"field": "reading_plan", "value": summary},
        "status": "success" if result.success else "chain_error",
        "failed_step": result.failed_step,
        "step_details": result.step_details,
        "ai_config_version": _AI_CONFIG__Customer__reading_plan.get("ai_config_version"),
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    if summary is not None:
        Customer.objects.filter(pk=instance.pk).update(reading_plan=summary)
    return summary



def attach_actions():
    # called from apps.ready(): attach each action as a plain function on the model class.
    # Assigning a module-level function as a class attribute makes it a *bound method*, so
    # `customer.generate_reading_plan()` calls generate_reading_plan(customer) with instance=customer.

    Customer.generate_reading_plan = generate_reading_plan
