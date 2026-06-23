# GENERATED - M07 event-driven LLM invocation glue (do not edit by hand).
# Mechanisms M01-M06 live in ai_runtime; this module only wires domain post_save
# events to ai_runtime.invoke(ai_config, instance). Wiring (import via apps.ready)
# is added at Step 5.
from django.db.models.signals import post_save
from django.dispatch import receiver

from shared_models.models import BookLoan


_AI_CONFIG__BookLoan__late_risk = {'ai_config_version': '1.0',
 'context': {'fields': ['loan_date', 'due_date', 'return_date'],
             'relations': ['Book', 'Customer', 'Loan']},
 'model_profile': 'cheap',
 'output': {'allowed_values': ['LOW', 'MEDIUM', 'HIGH'],
            'format': 'risk_label',
            'write_back': 'late_risk'},
 'template': {'name': 'library_late_risk_v1'},
 'trigger': {'class': 'BookLoan', 'type': 'post_save'}}


@receiver(post_save, sender=BookLoan)
def _ai__BookLoan__late_risk(sender, instance, created, **kwargs):
    try:
        from ai_runtime import invoke  # provided at Step 5; absent before that
    except ImportError:
        return  # ai_runtime not present yet: safe no-op
    value = invoke(_AI_CONFIG__BookLoan__late_risk, instance)
    if value is None:
        return
    # recursion-safe: QuerySet.update() does NOT emit post_save
    BookLoan.objects.filter(pk=instance.pk).update(late_risk=value)
