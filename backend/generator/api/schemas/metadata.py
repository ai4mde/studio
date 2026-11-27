from ninja import Schema

from diagram.api.schemas.diagram import DiagramReadFull
from metadata.api.schemas.interface import InterfaceRead


class GeneratorMetadata(Schema):
    diagrams: list[DiagramReadFull]
    interfaces: list[InterfaceRead]
    use_authentication: bool
