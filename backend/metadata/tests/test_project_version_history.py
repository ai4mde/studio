from copy import deepcopy
from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase

from metadata.models import Project, ProjectVersion, System
from metadata.services.versioning import (
    ProjectVersionError,
    create_version,
    generate_delta,
    reconstruct_version,
    serialize_project,
)
from metadata.services.versioning import versions as version_module
from metadata.services.versioning.constants import CHECKPOINT_INTERVAL


class ProjectVersionHistoryTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Example", description="Original")
        self.system = System.objects.create(project=self.project, name="Main")

    def test_first_version_stores_only_creates(self):
        expected = serialize_project(self.project.pk)

        a = create_version(self.project.pk, "Initial version")

        self.project.refresh_from_db()
        self.assertIsNone(a.parent_id)
        self.assertIsNone(a.merge_parent_id)
        self.assertEqual(a.message, "Initial version")
        self.assertEqual(self.project.current_version_id, a.pk)
        self.assertTrue(a.delta)
        self.assertEqual({op["operation"] for op in a.delta}, {"CREATE"})
        self.assertEqual(reconstruct_version(a.pk), expected)

    def test_second_version_only_stores_changed_objects(self):
        a = create_version(self.project.pk)
        state_a = reconstruct_version(a.pk)
        self.system.name = "Renamed"
        self.system.save(update_fields=["name"])
        second_system = System.objects.create(project=self.project, name="Second")
        expected_b = serialize_project(self.project.pk)

        b = create_version(self.project.pk, "Edit systems")

        self.project.refresh_from_db()
        self.assertEqual(b.parent_id, a.pk)
        self.assertIsNone(b.merge_parent_id)
        self.assertEqual(self.project.current_version_id, b.pk)
        self.assertEqual({op["operation"] for op in b.delta}, {"CREATE", "UPDATE"})
        self.assertEqual(len(b.delta), 2)
        self.assertEqual(reconstruct_version(b.pk), expected_b)
        self.assertEqual(reconstruct_version(a.pk), state_a)
        self.assertIn(str(second_system.pk), expected_b["models"]["metadata.System"])

    def test_deleted_object_disappears_from_reconstructed_state(self):
        a = create_version(self.project.pk)
        system_id = str(self.system.pk)
        self.system.delete()
        b = create_version(self.project.pk)

        self.assertEqual(len(b.delta), 1)
        self.assertEqual(b.delta[0]["operation"], "DELETE")
        self.assertIn(system_id, reconstruct_version(a.pk)["models"]["metadata.System"])
        self.assertNotIn(system_id, reconstruct_version(b.pk)["models"]["metadata.System"])

    def test_no_changes_do_not_create_a_version(self):
        a = create_version(self.project.pk)
        with self.assertRaisesRegex(ProjectVersionError, "No changes"):
            create_version(self.project.pk)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_version_id, a.pk)
        self.assertEqual(ProjectVersion.objects.filter(project=self.project).count(), 1)

    def test_reconstruction_ignores_merge_parent_delta(self):
        a = create_version(self.project.pk)
        state_a = reconstruct_version(a.pk)

        # Local branch: A -> B
        b_state = deepcopy(state_a)
        b_state["models"]["metadata.System"][str(self.system.pk)]["name"] = "Local"
        b = ProjectVersion.objects.create(
            project=self.project,
            parent=a,
            delta=generate_delta(state_a, b_state),
        )

        # Imported branch: A -> E
        e_state = deepcopy(state_a)
        e_state["models"]["metadata.Project"][str(self.project.pk)]["description"] = "Imported"
        e = ProjectVersion.objects.create(
            project=self.project,
            parent=a,
            delta=generate_delta(state_a, e_state),
        )

        # Merge: B + E -> G, with G.delta relative only to B
        g_state = deepcopy(b_state)
        g_state["models"]["metadata.Project"][str(self.project.pk)]["description"] = "Imported"
        g = ProjectVersion.objects.create(
            project=self.project,
            parent=b,
            merge_parent=e,
            delta=generate_delta(b_state, g_state),
        )

        self.assertEqual(reconstruct_version(e.pk), e_state)
        self.assertEqual(reconstruct_version(b.pk), b_state)
        self.assertEqual(reconstruct_version(g.pk), g_state)

    def test_can_branch_from_an_older_active_version(self):
        a = create_version(self.project.pk)
        self.system.name = "Branch B"
        self.system.save(update_fields=["name"])
        b = create_version(self.project.pk)

        # Simulate checkout of A: first restore its database state, then
        # move current_version. The real checkout service comes later.
        self.system.name = "Main"
        self.system.save(update_fields=["name"])
        self.project.current_version = a
        self.project.save(update_fields=["current_version"])

        self.system.name = "Branch E"
        self.system.save(update_fields=["name"])
        e = create_version(self.project.pk)

        self.assertEqual(e.parent_id, a.pk)
        self.assertEqual(b.parent_id, a.pk)
        self.assertEqual(
            reconstruct_version(b.pk)["models"]["metadata.System"][str(self.system.pk)]["name"],
            "Branch B",
        )
        self.assertEqual(
            reconstruct_version(e.pk)["models"]["metadata.System"][str(self.system.pk)]["name"],
            "Branch E",
        )

    def test_unknown_version_is_rejected(self):
        with self.assertRaisesRegex(ProjectVersionError, "Version does not exist"):
            reconstruct_version(uuid4())

    def test_stale_delta_is_rejected_during_reconstruction(self):
        a = create_version(self.project.pk)
        corrupted = ProjectVersion.objects.create(
            project=self.project,
            parent=a,
            delta=[{
                "operation": "UPDATE",
                "model": "metadata.System",
                "id": str(self.system.pk),
                "changes": {"name": {"old": "Unexpected", "new": "New"}},
            }],
        )

        with self.assertRaisesRegex(ProjectVersionError, "Stale UPDATE"):
            reconstruct_version(corrupted.pk)

    def test_existing_versions_without_active_head_cannot_start_new_root(self):
        a = create_version(self.project.pk)
        self.project.current_version = None
        self.project.save(update_fields=["current_version"])
        with self.assertRaisesRegex(ProjectVersionError, "no active version"):
            create_version(self.project.pk)
        self.assertTrue(ProjectVersion.objects.filter(pk=a.pk).exists())

    def test_reconstruction_rejects_history_across_projects(self):
        other = Project.objects.create(name="Other")
        a = create_version(self.project.pk)
        invalid = ProjectVersion.objects.create(project=other, parent=a, delta=[])

        with self.assertRaisesRegex(ProjectVersionError, "crosses project boundaries"):
            reconstruct_version(invalid.pk)

    def test_invalid_project_does_not_create_versions(self):
        with self.assertRaisesRegex(ProjectVersionError, "Project does not exist"):
            create_version(uuid4())
        self.assertEqual(ProjectVersion.objects.count(), 0)


    def _create_multiple_versions(self, count: int) -> list[ProjectVersion]:
        """Create multiple versions by changing the project name."""
        versions: list[ProjectVersion] = []

        for number in range(1, count + 1):
            self.project.name = f"Version {number}"
            self.project.save(update_fields=["name"])

            version = create_version(self.project.pk)
            versions.append(version)

        return versions

    def test_checkpoint_created_at_interval(self):
        """Check that a checkpoint is created after the configured interval."""
        versions = self._create_multiple_versions(CHECKPOINT_INTERVAL)

        for version in versions[:-1]:
            self.assertIsNone(version.checkpoint)

        self.assertIsNotNone(versions[-1].checkpoint)

    def test_checkpoint_contains_correct_state(self):
        """Check that a checkpoint stores the complete project state."""
        versions = self._create_multiple_versions(CHECKPOINT_INTERVAL)
        version = versions[-1]

        self.assertIsNotNone(version.checkpoint)

        self.assertEqual(
            version.checkpoint,
            serialize_project(self.project.pk),
        )

        self.assertEqual(
            reconstruct_version(version.pk),
            version.checkpoint,
        )

    def test_reconstruction_uses_nearest_checkpoint(self):
        """Check that reconstruction skips deltas before the checkpoint."""
        versions = self._create_multiple_versions(CHECKPOINT_INTERVAL + 2)

        original_apply_delta = version_module.apply_delta

        with patch.object(
            version_module,
            "apply_delta",
            wraps=original_apply_delta,
        ) as mocked_apply:
            state = reconstruct_version(versions[-1].pk)

        # Only the two versions after the checkpoint need their deltas applied.
        self.assertEqual(mocked_apply.call_count, 2)

        self.assertEqual(
            state,
            serialize_project(self.project.pk),
        )
