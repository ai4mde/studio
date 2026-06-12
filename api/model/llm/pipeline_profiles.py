from __future__ import annotations

from typing import Literal, Optional, TypedDict


PipelineProfile = Literal[
    "stable",
    "sketch_review_only",
    "graph_repair_only",
    "both_agents",
]


class ResolvedPipelineConfig(TypedDict):
    pipeline_profile: PipelineProfile
    enable_sketch_review_agent: bool
    enable_prompted_sketch_repair_agent: bool
    enable_graph_repair_agent: bool


def resolve_pipeline_config(
    *,
    pipeline_profile: PipelineProfile = "stable",
    enable_sketch_review_agent: Optional[bool] = None,
    enable_prompted_sketch_repair_agent: Optional[bool] = None,
    enable_graph_repair_agent: Optional[bool] = None,
) -> ResolvedPipelineConfig:
    if pipeline_profile == "both_agents":
        sketch_review_enabled = True
        prompted_sketch_repair_enabled = False
        graph_repair_enabled = True
    elif pipeline_profile == "sketch_review_only":
        sketch_review_enabled = True
        prompted_sketch_repair_enabled = False
        graph_repair_enabled = False
    elif pipeline_profile == "graph_repair_only":
        sketch_review_enabled = False
        prompted_sketch_repair_enabled = False
        graph_repair_enabled = True
    else:
        sketch_review_enabled = False
        prompted_sketch_repair_enabled = False
        graph_repair_enabled = False

    if enable_sketch_review_agent is not None:
        sketch_review_enabled = enable_sketch_review_agent
    if enable_prompted_sketch_repair_agent is not None:
        prompted_sketch_repair_enabled = enable_prompted_sketch_repair_agent
    if enable_graph_repair_agent is not None:
        graph_repair_enabled = enable_graph_repair_agent

    return {
        "pipeline_profile": pipeline_profile,
        "enable_sketch_review_agent": sketch_review_enabled,
        "enable_prompted_sketch_repair_agent": prompted_sketch_repair_enabled,
        "enable_graph_repair_agent": graph_repair_enabled,
    }


__all__ = [
    "PipelineProfile",
    "ResolvedPipelineConfig",
    "resolve_pipeline_config",
]
