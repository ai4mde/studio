from typing import Literal, NotRequired, TypeAlias, TypedDict


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

# Merge operations
MergeConflictKind = Literal[
    "FIELD",
    "CREATE_CREATE",
    "DELETE_UPDATE",
    "UPDATE_DELETE",
    "MISSING_REFERENCE",
]


class MergeConflict(TypedDict):
    kind: MergeConflictKind
    model: str
    id: str
    field: str | None
    base: object
    local: object
    incoming: object


class MergeResult(TypedDict):
    state: ProjectState | None
    conflicts: list[MergeConflict]


MergeResolutionChoice = Literal[
    "LOCAL",
    "INCOMING",
    "BASE",
    "CUSTOM",
    "DELETE_OBJECT",
    "RESTORE_TARGET",
]


class MergeResolution(TypedDict):
    """User-selected action for one merge conflict."""

    kind: MergeConflictKind
    model: str
    id: str
    field: str | None
    choice: MergeResolutionChoice
    value: NotRequired[object]  # Required only when choice is CUSTOM.