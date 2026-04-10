"""
Pipeline API endpoints — expose the LangGraph agent pipeline over REST.

Endpoints:
  POST /generator/pipeline/run/   Start a new pipeline run. Returns thread_id + current state.
  GET  /generator/pipeline/{id}/  Get current state of a pipeline run.
"""
import uuid
from typing import Optional

from ninja import Router
from ninja.schema import Schema

from generator.agents.pipeline import pipeline

pipeline_router = Router()


# ── Schemas ──────────────────────────────────────────────────────────────────

class RunPipelineSchema(Schema):
    project_name: str
    application_name: str
    metadata: str           # raw JSON string
    system_id: str
    authentication_present: bool = True


class PipelineStatusSchema(Schema):
    thread_id: str
    ui_design: Optional[dict]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _state_to_status(thread_id: str, state: dict) -> dict:
    return {
        "thread_id": thread_id,
        "ui_design": state.get("ui_design"),
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@pipeline_router.post("/run/", response=PipelineStatusSchema)
def run_pipeline(request, body: RunPipelineSchema):
    """Kick off a new pipeline run (parser → ui_designer → END)."""
    thread_id = str(uuid.uuid4())

    initial_state = {
        "project_name": body.project_name,
        "application_name": body.application_name,
        "metadata": body.metadata,
        "system_id": body.system_id,
        "authentication_present": body.authentication_present,
        "screens": [],
        "ui_design": None,
    }

    for event in pipeline.stream(initial_state, config=_config(thread_id)):
        pass

    snapshot = pipeline.get_state(_config(thread_id))
    return _state_to_status(thread_id, snapshot.values)


@pipeline_router.get("/{thread_id}/", response=PipelineStatusSchema)
def get_pipeline_status(request, thread_id: str):
    """Return the current state of a pipeline run."""
    snapshot = pipeline.get_state(_config(thread_id))
    if not snapshot.values:
        return 404, {"error": "thread not found"}
    return _state_to_status(thread_id, snapshot.values)
