from django.db import models

from ..relation import RelationDataModel
from ..types import AggregatorType, OperatorType


class ControlFlow(RelationDataModel):
    guard = models.CharField(max_length=255, blank=True, default="")
    weight = models.FloatField(null=True, blank=True, default=None)
    is_else = models.BooleanField(default=False)
    attribute = models.ForeignKey(
        "Attribute",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="control_flows",   
    )
    operator = models.CharField(
        max_length=8,
        choices=OperatorType.choices,
        blank=True,
        default="",
    )
    aggregator = models.CharField(
        max_length=8,
        choices=AggregatorType.choices,
        blank=True,
        default="",
    )
    comparison_value = models.CharField(max_length=255, blank=True, default="")
    
    # TODO add method to autoamatically parse the comparision value to the correct data type
    # Based on the attribute's data type
