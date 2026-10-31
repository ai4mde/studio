"""Tests for checking out saved project versions."""

from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase

from metadata.models import Project, ProjectVersion, System
from metadata.services.versioning import (
    create_version,
    reconstruct_version,
    serialize_project,
)
from metadata.services.versioning.checkout import (
    ProjectCheckoutError,
    checkout_version,
)


class ProjectCheckoutTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Example", description="Original")
        self.system = System.objects.create(project=self.project, name="Main")

    def _change_system(self, name: str) -> None:
        self.system.name = name
        self.system.save(update_fields=["name"])

    def test_checkout_older_version_restores_data_and_moves_head(self):
        a = create_version(self.project.pk)
        state_a = reconstruct_version(a.pk)
        self._change_system("Changed")
        b = create_version(self.project.pk)
        count_before = ProjectVersion.objects.count()

        checked_out = checkout_version(self.project.pk, a.pk)

        self.project.refresh_from_db()
        self.system.refresh_from_db()
        self.assertEqual(checked_out.pk, a.pk)
        self.assertEqual(self.project.current_version_id, a.pk)
        self.assertEqual(self.system.name, "Main")
        self.assertEqual(serialize_project(self.project.pk), state_a)
        self.assertEqual(ProjectVersion.objects.count(), count_before)
        self.assertTrue(ProjectVersion.objects.filter(pk=b.pk).exists())

    def test_checkout_newer_version_restores_data(self):
        a = create_version(self.project.pk)
        self._change_system("Changed")
        b = create_version(self.project.pk)
        state_b = reconstruct_version(b.pk)
        checkout_version(self.project.pk, a.pk)

        checkout_version(self.project.pk, b.pk)

        self.project.refresh_from_db()
        self.system.refresh_from_db()
        self.assertEqual(self.project.current_version_id, b.pk)
        self.assertEqual(self.system.name, "Changed")
        self.assertEqual(serialize_project(self.project.pk), state_b)

    def test_checkout_restores_created_and_deleted_objects(self):
        a = create_version(self.project.pk)
        second = System.objects.create(project=self.project, name="Second")
        b = create_version(self.project.pk)
        second_id = second.pk

        checkout_version(self.project.pk, a.pk)
        self.assertFalse(System.objects.filter(pk=second_id).exists())

        checkout_version(self.project.pk, b.pk)
        self.assertTrue(System.objects.filter(pk=second_id).exists())
        self.assertEqual(
            serialize_project(self.project.pk), reconstruct_version(b.pk)
        )

    def test_checkout_another_branch(self):
        a = create_version(self.project.pk)
        self._change_system("Branch B")
        b = create_version(self.project.pk)

        checkout_version(self.project.pk, a.pk)
        self.system.refresh_from_db()
        self._change_system("Branch E")
        e = create_version(self.project.pk)

        checkout_version(self.project.pk, b.pk)
        self.system.refresh_from_db()
        self.assertEqual(self.system.name, "Branch B")
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_version_id, b.pk)

        checkout_version(self.project.pk, e.pk)
        self.system.refresh_from_db()
        self.assertEqual(self.system.name, "Branch E")
        self.assertEqual(e.parent_id, a.pk)
        self.assertEqual(b.parent_id, a.pk)

    def test_checkout_rejects_uncommitted_changes(self):
        a = create_version(self.project.pk)
        self._change_system("Saved")
        b = create_version(self.project.pk)
        self._change_system("Unsaved")

        with self.assertRaisesRegex(ProjectCheckoutError, "uncommitted changes"):
            checkout_version(self.project.pk, a.pk)

        self.project.refresh_from_db()
        self.system.refresh_from_db()
        self.assertEqual(self.project.current_version_id, b.pk)
        self.assertEqual(self.system.name, "Unsaved")

    def test_checkout_current_version_still_checks_for_changes(self):
        a = create_version(self.project.pk)
        self._change_system("Unsaved")

        with self.assertRaisesRegex(ProjectCheckoutError, "uncommitted changes"):
            checkout_version(self.project.pk, a.pk)

        self.system.refresh_from_db()
        self.assertEqual(self.system.name, "Unsaved")

    def test_checkout_current_version_without_changes_is_noop(self):
        a = create_version(self.project.pk)
        state = serialize_project(self.project.pk)
        count_before = ProjectVersion.objects.count()

        result = checkout_version(self.project.pk, a.pk)

        self.assertEqual(result.pk, a.pk)
        self.assertEqual(serialize_project(self.project.pk), state)
        self.assertEqual(ProjectVersion.objects.count(), count_before)

    def test_checkout_same_state_on_different_version_moves_head(self):
        a = create_version(self.project.pk)
        b = ProjectVersion.objects.create(project=self.project, parent=a, delta=[])

        result = checkout_version(self.project.pk, b.pk)

        self.project.refresh_from_db()
        self.assertEqual(result.pk, b.pk)
        self.assertEqual(self.project.current_version_id, b.pk)
        self.assertEqual(serialize_project(self.project.pk), reconstruct_version(a.pk))

    def test_checkout_refuses_version_from_another_project(self):
        a = create_version(self.project.pk)
        other = Project.objects.create(name="Other")
        other_version = create_version(other.pk)
        before = serialize_project(self.project.pk)

        with self.assertRaisesRegex(ProjectCheckoutError, "does not exist in this project"):
            checkout_version(self.project.pk, other_version.pk)

        self.project.refresh_from_db()
        self.assertEqual(self.project.current_version_id, a.pk)
        self.assertEqual(serialize_project(self.project.pk), before)

    def test_checkout_requires_active_version(self):
        a = create_version(self.project.pk)
        self.project.current_version = None
        self.project.save(update_fields=["current_version"])

        with self.assertRaisesRegex(ProjectCheckoutError, "no active version"):
            checkout_version(self.project.pk, a.pk)

    def test_checkout_rejects_unknown_version(self):
        create_version(self.project.pk)

        with self.assertRaisesRegex(ProjectCheckoutError, "does not exist in this project"):
            checkout_version(self.project.pk, uuid4())

    def test_checkout_rejects_invalid_ids(self):
        with self.assertRaisesRegex(ProjectCheckoutError, "Invalid project UUID"):
            checkout_version("not-a-uuid", uuid4())
        with self.assertRaisesRegex(ProjectCheckoutError, "Invalid version UUID"):
            checkout_version(self.project.pk, "not-a-uuid")

    def test_checkout_rejects_unknown_project(self):
        with self.assertRaisesRegex(ProjectCheckoutError, "Project does not exist"):
            checkout_version(uuid4(), uuid4())

    def test_checkout_rolls_back_database_and_head_on_failure(self):
        a = create_version(self.project.pk)
        self._change_system("Changed")
        b = create_version(self.project.pk)
        before = serialize_project(self.project.pk)

        from metadata.services.versioning import checkout as checkout_module

        real_apply = checkout_module.apply_project_changes

        def apply_then_fail(project_id, delta):
            real_apply(project_id, delta)
            raise RuntimeError("Simulated failure after writing")

        with patch.object(checkout_module, "apply_project_changes", side_effect=apply_then_fail):
            with self.assertRaisesRegex(RuntimeError, "Simulated failure"):
                checkout_version(self.project.pk, a.pk)

        self.project.refresh_from_db()
        self.system.refresh_from_db()
        self.assertEqual(self.project.current_version_id, b.pk)
        self.assertEqual(self.system.name, "Changed")
        self.assertEqual(serialize_project(self.project.pk), before)
