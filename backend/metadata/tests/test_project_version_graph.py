"""Tests for finding common ancestors in a project version graph."""

from uuid import uuid4

from django.test import TestCase

from metadata.models import Project, ProjectVersion
from metadata.services.versioning.graph import (
    ProjectVersionGraphError,
    find_common_ancestor,
)


class ProjectVersionGraphTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Example")

    def _version(self, parent=None, merge_parent=None, project=None):
        return ProjectVersion.objects.create(
            project=project or self.project,
            parent=parent,
            merge_parent=merge_parent,
            delta=[],
        )

    def test_same_version_is_its_own_common_ancestor(self):
        a = self._version()

        self.assertEqual(find_common_ancestor(a, a).pk, a.pk)

    def test_ancestor_and_descendant(self):
        a = self._version()
        b = self._version(parent=a)
        c = self._version(parent=b)

        self.assertEqual(find_common_ancestor(a.pk, c.pk).pk, a.pk)
        self.assertEqual(find_common_ancestor(c.pk, b.pk).pk, b.pk)

    def test_sibling_branches_share_their_branch_point(self):
        a = self._version()
        b = self._version(parent=a)
        c = self._version(parent=b)
        e = self._version(parent=b)
        f = self._version(parent=e)

        self.assertEqual(find_common_ancestor(c.pk, f.pk).pk, b.pk)
        self.assertEqual(find_common_ancestor(f.pk, c.pk).pk, b.pk)

    def test_merge_parent_counts_as_ancestor(self):
        a = self._version()
        b = self._version(parent=a)
        c = self._version(parent=b)
        e = self._version(parent=b)
        f = self._version(parent=e)
        g = self._version(parent=c, merge_parent=f)

        self.assertEqual(find_common_ancestor(g, f).pk, f.pk)
        self.assertEqual(find_common_ancestor(g, c).pk, c.pk)
        self.assertEqual(find_common_ancestor(g, e).pk, e.pk)

    def test_ancestry_through_a_merge_is_preserved(self):
        a = self._version()
        b = self._version(parent=a)
        c = self._version(parent=b)
        e = self._version(parent=b)
        f = self._version(parent=e)
        g = self._version(parent=c, merge_parent=f)
        h = self._version(parent=g)
        j = self._version(parent=f)

        self.assertEqual(find_common_ancestor(h, j).pk, f.pk)

    def test_separate_roots_have_no_common_ancestor(self):
        a = self._version()
        b = self._version()

        self.assertIsNone(find_common_ancestor(a, b))

    def test_criss_cross_merge_has_ambiguous_base(self):
        a = self._version()
        b = self._version(parent=a)
        e = self._version(parent=a)
        g = self._version(parent=b, merge_parent=e)
        h = self._version(parent=e, merge_parent=b)

        with self.assertRaisesRegex(ProjectVersionGraphError, "Multiple common ancestors"):
            find_common_ancestor(g, h)

    def test_unknown_version_is_rejected(self):
        a = self._version()

        with self.assertRaisesRegex(ProjectVersionGraphError, "Version does not exist"):
            find_common_ancestor(a, uuid4())

    def test_invalid_version_uuid_is_rejected(self):
        a = self._version()

        with self.assertRaisesRegex(ProjectVersionGraphError, "Invalid version UUID"):
            find_common_ancestor(a, "not-a-uuid")

    def test_versions_from_different_projects_are_rejected(self):
        a = self._version()
        other_project = Project.objects.create(name="Other")
        b = self._version(project=other_project)

        with self.assertRaisesRegex(ProjectVersionGraphError, "different projects"):
            find_common_ancestor(a, b)

    def test_cross_project_parent_is_rejected(self):
        other_project = Project.objects.create(name="Other")
        other_root = self._version(project=other_project)
        a = self._version()
        invalid = self._version(parent=other_root)

        with self.assertRaisesRegex(ProjectVersionGraphError, "crosses project boundaries"):
            find_common_ancestor(a, invalid)

    def test_cycle_is_rejected(self):
        a = self._version()
        b = self._version(parent=a)
        ProjectVersion.objects.filter(pk=a.pk).update(parent=b)

        with self.assertRaisesRegex(ProjectVersionGraphError, "Cycle detected"):
            find_common_ancestor(a, b)

    def test_root_with_merge_parent_is_rejected(self):
        a = self._version()
        invalid = self._version(merge_parent=a)

        with self.assertRaisesRegex(ProjectVersionGraphError, "root version"):
            find_common_ancestor(a, invalid)

    def test_finding_ancestor_does_not_change_history(self):
        a = self._version()
        b = self._version(parent=a)
        c = self._version(parent=a)
        count_before = ProjectVersion.objects.count()

        self.assertEqual(find_common_ancestor(b, c).pk, a.pk)
        self.assertEqual(ProjectVersion.objects.count(), count_before)
        self.assertIsNone(Project.objects.get(pk=self.project.pk).current_version_id)
