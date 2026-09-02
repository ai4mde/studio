import ast
import re

from django.core.exceptions import ValidationError
from django.db import models



def validate_python_code(value: str):
    if not value:
        return

    try:
        ast.parse(value)
    except SyntaxError as exc:
        raise ValidationError(
            f"Invalid Python syntax: {exc.msg}"
        )


class PythonField(models.TextField):
    default_validators = [validate_python_code]


_CRON_PART = re.compile(r"^[\d*/,\-]+$")


def validate_cron_expression(value: str):
    if not value:
        return

    parts = value.split()

    if len(parts) != 5:
        raise ValidationError(
            "Cron expression must contain 5 fields."
        )

    if not all(_CRON_PART.fullmatch(part) for part in parts):
        raise ValidationError(
            "Invalid cron expression."
        )


class CronField(models.CharField):
    default_validators = [validate_cron_expression]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 100)
        super().__init__(*args, **kwargs)
    