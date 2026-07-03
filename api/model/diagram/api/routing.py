"""
Diagram API router configuration.

Aggregates all diagram-related endpoints under `diagram_router`, which is
mounted at `/diagram/` on the top-level API. Combines four sub-routers:
diagram CRUD/import, node management, edge management, and system-scoped
diagram lookup.

Routes (relative to `/diagram/`):

Diagrams (mounted at ""):
    GET    /                                       List all diagrams
    POST   /                                       Create a diagram
    POST   /import                                 Import a full diagram (nodes + edges)
    GET    /specification/node.schema.json         Get JSON schema for nodes
    GET    /specification/edge.schema.json         Get JSON schema for edges
    GET    /{diagram_id}                           Retrieve a diagram (full detail)
    PATCH  /{diagram_id}/                          Update a diagram's name/description
    DELETE /{diagram_id}/                          Delete a diagram
    POST   /{diagram_id}/auto_layout               Auto-layout a diagram

Nodes (mounted at "/{diagram}/node"):
    GET    /{diagram}/node/                                    List nodes in a diagram
    POST   /{diagram}/node/                                    Create a node
    GET    /{diagram}/node/{node_id}/                          Retrieve a node
    GET    /{diagram}/node/{node_id}/classifier-usage/         List other diagrams using this node's classifier
    GET    /{diagram}/node/{node_id}/enums/                    List enum nodes connected via dependency edges
    DELETE /{diagram}/node/{node_id}/                          Remove a node from the diagram
    DELETE /{diagram}/node/{node_id}/hard/                     Delete the underlying classifier everywhere
    PATCH  /{diagram}/node/{node_id}/                          Update a node's classifier/data
    POST   /{diagram}/node/import/{classifier_id}/             Import an existing classifier as a node
    POST   /{diagram}/node/{node_id}/generate_attribute/       Generate a class attribute via LLM
    POST   /{diagram}/node/{node_id}/generate_method/          Generate a class method via LLM

Edges (mounted at "/{diagram}/edge"):
    GET    /{diagram}/edge/                                    List edges in a diagram
    POST   /{diagram}/edge/                                    Create an edge
    GET    /{diagram}/edge/{edge_id}/                          Retrieve an edge
    GET    /{diagram}/edge/{edge_id}/relation-usage/           List other diagrams using this edge's relation
    PATCH  /{diagram}/edge/{edge_id}/                          Update an edge's relation/data
    DELETE /{diagram}/edge/{edge_id}/                          Remove an edge from the diagram
    DELETE /{diagram}/edge/{edge_id}/hard/                     Delete the underlying relation everywhere

System (mounted at "/system/"):
    GET    /system/{system_id}/                                List all diagrams belonging to a system
"""

from ninja import Router, Schema

from diagram.api.diagram import diagrams
from diagram.api.edge import edge
from diagram.api.node import node
from diagram.api.system import system

diagram_router = Router()
diagram_router.add_router("", diagrams, tags=["diagrams"])
diagram_router.add_router("/{uuid:diagram}/node", node, tags=["diagrams"])
diagram_router.add_router("/{uuid:diagram}/edge", edge, tags=["diagrams"])
diagram_router.add_router("/system/", system, tags=["diagrams"])
