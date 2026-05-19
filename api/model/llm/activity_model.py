from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator


NodeType = Literal["initial", "action", "decision", "merge", "fork", "join", "final", "object"]
EdgeType = Literal["control", "object"]


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: NodeType
    name: Optional[str] = None
    label: Optional[str] = None
    partition: Optional[str] = None


class Edge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    type: EdgeType = "control"
    label: Optional[str] = None
    condition: Optional[str] = None


class ActivityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: List[Node]
    edges: List[Edge]

    @model_validator(mode="after")
    def validate_graph_structure(self) -> "ActivityModel":
        node_ids = [node.id for node in self.nodes]
        duplicate_ids = sorted({node_id for node_id in node_ids if node_ids.count(node_id) > 1})
        if duplicate_ids:
            raise ValueError(f"duplicate node ids are not allowed: {duplicate_ids}")

        known_node_ids = set(node_ids)
        missing_endpoints = []
        for edge in self.edges:
            missing = []
            if edge.source not in known_node_ids:
                missing.append(f"unknown source '{edge.source}'")
            if edge.target not in known_node_ids:
                missing.append(f"unknown target '{edge.target}'")
            if missing:
                missing_endpoints.append(
                    f"{edge.source}->{edge.target} ({', '.join(missing)})"
                )

        if missing_endpoints:
            raise ValueError(
                "edges must reference existing node ids: "
                + "; ".join(missing_endpoints)
            )

        return self


__all__ = ["ActivityModel", "Edge", "Node", "ValidationError"]
