from django.core.exceptions import ValidationError
from django.test import TestCase

from metadata.models import Project, ProjectVersion


class ProjectVersionModelTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Project")

    def test_diverging_branches_and_merge_are_preserved(self):
        a = ProjectVersion.objects.create(project=self.project, delta=[{"type": "create"}])
        b = ProjectVersion.objects.create(project=self.project, parent=a)
        c = ProjectVersion.objects.create(project=self.project, parent=b)
        d = ProjectVersion.objects.create(project=self.project, parent=c)
        e = ProjectVersion.objects.create(project=self.project, parent=b)
        f = ProjectVersion.objects.create(project=self.project, parent=e)
        g = ProjectVersion.objects.create(
            project=self.project, parent=d, merge_parent=f
        )
        self.project.current_version = g
        self.project.full_clean()
        self.project.save(update_fields=["current_version"])

        self.assertEqual(self.project.versions.count(), 7)
        self.assertEqual(g.parent, d)
        self.assertEqual(g.merge_parent, f)
        self.assertEqual(self.project.current_version, g)
        self.assertEqual(f.parent, e)
        self.assertEqual(e.parent, b)
        self.assertEqual(a.delta, [{"type": "create"}])

    def test_branch_parent_must_belong_to_same_project(self):
        other_project = Project.objects.create(name="Other")
        other_version = ProjectVersion.objects.create(project=other_project)
        version = ProjectVersion(project=self.project, parent=other_version)

        with self.assertRaises(ValidationError):
            version.full_clean()

    def test_active_head_must_belong_to_same_project(self):
        other_project = Project.objects.create(name="Other")
        other_version = ProjectVersion.objects.create(project=other_project)
        self.project.current_version = other_version

        with self.assertRaises(ValidationError):
            self.project.full_clean()
