from typing import Literal, TypeAlias, TypedDict


# Serialization

ProjectRow: TypeAlias = dict[str, object]
ModelRows: TypeAlias = dict[str, ProjectRow]
ProjectModels: TypeAlias = dict[str, ModelRows]


class ProjectState(TypedDict):
    format: str
    schema_version: int
    project_id: str
    models: ProjectModels


# Delta operations

class FieldChange(TypedDict):
    old: object
    new: object


class BaseOperation(TypedDict):
    model: str
    id: str


class CreateOperation(BaseOperation):
    operation: Literal["CREATE"]
    data: ProjectRow


class UpdateOperation(BaseOperation):
    operation: Literal["UPDATE"]
    changes: dict[str, FieldChange]


class DeleteOperation(BaseOperation):
    operation: Literal["DELETE"]
    data: ProjectRow


DeltaOperation: TypeAlias = (
    CreateOperation | UpdateOperation | DeleteOperation
)

ProjectDelta: TypeAlias = list[DeltaOperation]