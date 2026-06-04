"""Metadata context helpers for the Django-hosted UML mapping flow."""

from diagram.models import Diagram
from metadata.models import System

from ..token_normalizer import _as_list
from .usecase_workflow import _build_activity_diagrams


def _fetch_system_context_data(system_id: str) -> dict:
    system = System.objects.get(id=system_id)
    system_data = {
        "id": str(system.id),
        "name": system.name,
        "description": system.description,
        "project": str(system.project_id),
        "classifiers": [
            {
                "id": str(classifier.id),
                "project": str(classifier.project_id) if classifier.project_id else None,
                "system": str(classifier.system_id) if classifier.system_id else None,
                "original_system_id": (
                    str(classifier.original_system_id)
                    if classifier.original_system_id
                    else None
                ),
                "data": classifier.data or {},
            }
            for classifier in system.classifiers.all()
        ],
        "relations": [
            {
                "id": str(relation.id),
                "system": str(relation.system_id),
                "source": str(relation.source_id),
                "target": str(relation.target_id),
                "data": relation.data or {},
            }
            for relation in system.relations.all()
        ],
        "diagrams": [
            {
                "id": str(diagram.id),
                "name": diagram.name,
                "description": diagram.description,
                "type": diagram.type,
                "system": str(diagram.system_id),
            }
            for diagram in Diagram.objects.filter(system=system)
        ],
    }
    system_data["activity_diagrams"] = _build_activity_diagrams(system_data)
    return system_data


def _actor_name_from_context(system_context: dict, actor_id: str | None) -> str | None:
    for classifier in _as_list(system_context.get("classifiers"), "classifiers"):
        if str(classifier.get("id")) == str(actor_id):
            return (classifier.get("data") or {}).get("name")
    return None
