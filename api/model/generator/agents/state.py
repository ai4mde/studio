from typing import TypedDict, List, Optional, Any


class ScreenInfo(TypedDict):
    page_id: str
    page_name: str
    screen_type: str          # list | dashboard | form | modal | wizard | activity
    has_create: bool
    has_update: bool
    has_delete: bool
    models: List[str]
    sections_count: int


class UIDesign(TypedDict):
    """Output of UI Designer Agent."""
    ui_ir: dict               # {apps: [{actor_id, pages: [{name, components}]}], routing: {auth_role_map}}


class DiagramSummary(TypedDict):
    """Structured UML diagram data extracted by parser_node."""
    usecase: List[dict]    # [{name, actors, usecases: [{name, precondition, postcondition, trigger, scenarios}]}]
    activity: List[dict]   # [{name, actors, steps: [{name, actor, automatic, body, precondition, postcondition}]}]
    classes: List[dict]    # [{name, classes: [{name, attributes: [{name, type}]}]}]


class PipelineState(TypedDict):
    # ── Inputs ──────────────────────────────────────────────────────────────
    project_name: str
    application_name: str
    metadata: str             # raw JSON string from the frontend
    system_id: str
    authentication_present: bool

    # ── Parser node output ───────────────────────────────────────────────────
    screens: List[ScreenInfo]
    diagram_summary: DiagramSummary   # structured usecase/activity/class data
    parser_dsl: Optional[dict]        # canonical DSL: {domain, actors, entities, actions, workflow}

    # ── Page synthesis output (deterministic, pre-LLM) ───────────────────────
    page_ir: Optional[dict]           # ui_ir format: {apps: [{actor_id, pages: [{name, components}]}], routing}

    # ── UI Designer Agent output ─────────────────────────────────────────────
    ui_design: Optional[UIDesign]
