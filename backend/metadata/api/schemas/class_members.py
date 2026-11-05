from uuid import UUID

from ninja import Schema


# Attributes
class AttributeRead(Schema):
    id: UUID
    name: str
    type: str
    derived: bool
    enum: UUID | None = None
    description: str | None = None
    body: str | None = None

    @staticmethod
    def resolve_enum(obj):
        return obj.enum_id


class AttributeCreate(Schema):
    name: str
    type: str
    derived: bool = False
    enum_id: UUID | None = None
    description: str | None = None
    body: str | None = None


class AttributeUpdate(Schema):
    name: str | None = None
    type: str | None = None
    derived: bool | None = None
    enum_id: UUID | None = None
    description: str | None = None
    body: str | None = None


# Operations
class OperationRead(Schema):
    id: UUID
    name: str
    type: str
    description: str | None = None
    body: str | None = None


class OperationCreate(Schema):
    name: str
    type: str
    description: str | None = None
    body: str | None = None


class OperationUpdate(Schema):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    body: str | None = None