SNAPSHOT_FORMAT = "ai4mde-project-data"
SNAPSHOT_SCHEMA_VERSION = 1

# Model label -> query path back to the project
# Multiple paths are allowed for models that can be reached through different foreign key chains.
# E.G. metadata.Multiplicity can be reached through either an Association or a Composition.
PROJECT_MODEL_SCOPES: dict[str, tuple[str, ...]] = {
    "metadata.Project": ("pk",),
    "metadata.System": ("project_id",),
    "metadata.Classifier": ("system__project_id",),
    "metadata.Relation": ("system__project_id",),
    # Class diagram classifier data and dependent rows
    "metadata.ClassClassifier": ("classifier__system__project_id",),
    "metadata.Enum": ("classifier__system__project_id",),
    "metadata.EnumLiteral": ("enum__classifier__system__project_id",),
    "metadata.Attribute": ("uml_class__classifier__system__project_id",),
    "metadata.Operation": ("uml_class__classifier__system__project_id",),
    "metadata.InterfaceClassifier": ("classifier__system__project_id",),
    "metadata.Signal": ("classifier__system__project_id",),
    # Class diagram relation data and associated detail tables
    "metadata.Association": ("relation__system__project_id",),
    "metadata.Composition": ("relation__system__project_id",),
    "metadata.Dependency": ("relation__system__project_id",),
    "metadata.Multiplicity": (
        "association__relation__system__project_id",
        "composition__relation__system__project_id",
    ),
    "metadata.EndpointLabel": (
        "association__relation__system__project_id",
        "composition__relation__system__project_id",
    ),
    # Activity diagram
    "metadata.Swimlane": ("classifier__system__project_id",),
    "metadata.Action": ("classifier__system__project_id",),
    "metadata.Object": ("classifier__system__project_id",),
    "metadata.Event": ("classifier__system__project_id",),
    "metadata.Final": ("classifier__system__project_id",),
    "metadata.Initial": ("classifier__system__project_id",),
    "metadata.ControlFlow": ("relation__system__project_id",),
    # Component diagram
    "metadata.SystemClassifier": ("classifier__system__project_id",),
    "metadata.Container": ("classifier__system__project_id",),
    "metadata.Component": ("classifier__system__project_id",),
    "metadata.InterfaceRelation": ("relation__system__project_id",),
    # Use-case diagram
    "metadata.SystemBoundary": ("classifier__system__project_id",),
    "metadata.Actor": ("classifier__system__project_id",),
    "metadata.Usecase": ("classifier__system__project_id",),
    # UI interface models
    "metadata.Interface": ("system__project_id",),
    "metadata.Page": ("interface__system__project_id",),
    "metadata.Category": ("interface__system__project_id",),
    "metadata.SectionComponent": ("interface__system__project_id",),
    "metadata.PageSection": ("page__interface__system__project_id",),
    "metadata.SectionAttribute": ("section__interface__system__project_id",),
    # Diagram models live in the separate 'diagram' Django app
    "diagram.Diagram": ("system__project_id",),
    "diagram.Node": ("diagram__system__project_id",),
    "diagram.Edge": ("diagram__system__project_id",),
    "diagram.EdgeControlPoint": ("edge__diagram__system__project_id",),
}


# Version metadata is not part of the project state being versioned.
EXCLUDED_FIELDS: dict[str, frozenset[str]] = {
    "metadata.Project": frozenset({"current_version_id"}),
}

# Version metadata models are not part of the project state being versioned.
VERSION_METADATA_MODELS = frozenset({"metadata.ProjectVersion"})

# Create a checkpoint every CHECKPOINT_INTERVAL versions to speed up reconstruction.
CHECKPOINT_INTERVAL = 20