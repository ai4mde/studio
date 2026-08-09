from __future__ import annotations

import os

import pytest

from llm.converter import unwrap_ai4mde_systems_export, validate_ai4mde_json

_TEST_PROJECT_DESCRIPTION = (
    "Auto-created for baseline or refinement experiment (test)"
)


def setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
    django = pytest.importorskip(
        "django",
        reason="Django is required for DB import verification. Install project dependencies with Poetry.",
    )
    from django.apps import apps

    if not apps.ready:
        django.setup()


def create_test_project():
    setup_django()
    from metadata.models import Project

    return Project.objects.create(
        name="Generated Modelling Session",
        description=_TEST_PROJECT_DESCRIPTION,
    )


def import_and_validate_system(project, systems_export):
    setup_django()
    from metadata.models import System

    validate_ai4mde_json(systems_export)
    system_json = unwrap_ai4mde_systems_export(systems_export)
    systems_before = project.systems.count()

    prepared = dict(system_json)
    prepared["project"] = str(project.id)
    project.import_systems_from_json([prepared])

    imported = System.objects.prefetch_related("diagrams").get(pk=system_json["id"])
    assert str(imported.project_id) == str(project.id)
    assert project.systems.count() >= systems_before + 1
    return system_json, imported
