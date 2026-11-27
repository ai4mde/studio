from uuid import UUID

from django.core.exceptions import ValidationError

from diagram.models import Diagram
from diagram.api.schemas.diagram import DiagramReadFull

from metadata.models import Interface, System
from metadata.api.schemas.interface import InterfaceRead

from generator.api.schemas.metadata import GeneratorMetadata


def build_generator_metadata(
    system: System,
    interface_ids: list[UUID],
    use_authentication: bool,
) -> GeneratorMetadata:
    diagrams = Diagram.objects.filter(system=system)
    interfaces = Interface.objects.filter(system=system, id__in=interface_ids)

    if interfaces.count() != len(interface_ids):
        raise ValidationError("One or more selected interfaces do not belong to this system.")

    return GeneratorMetadata.model_validate({
        "diagrams": list(diagrams),
        "interfaces": list(interfaces),
        "use_authentication": use_authentication,
    })
