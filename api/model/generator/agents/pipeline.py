"""
LangGraph pipeline: UML metadata → Parser → UI Designer → Theme.

Graph topology
──────────────────────────────────────────────────────────────────────────────
  parser → ui_designer → theme → END
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from generator.agents.state import PipelineState
from generator.agents.nodes import (
    parser_node,
    ui_designer_node,
    theme_node,
)


def build_pipeline() -> tuple:
    """
    Returns (compiled_graph, checkpointer).
    MemorySaver is suitable for single-process / dev use.
    """
    checkpointer = MemorySaver()

    graph = StateGraph(PipelineState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    graph.add_node("parser",      parser_node)
    graph.add_node("ui_designer", ui_designer_node)
    graph.add_node("theme",       theme_node)

    # ── Edges ─────────────────────────────────────────────────────────────────
    graph.set_entry_point("parser")
    graph.add_edge("parser",      "ui_designer")
    graph.add_edge("ui_designer", "theme")
    graph.add_edge("theme",       END)

    compiled = graph.compile(checkpointer=checkpointer)
    return compiled, checkpointer


# Module-level singletons — one pipeline instance shared across requests
pipeline, _checkpointer = build_pipeline()
