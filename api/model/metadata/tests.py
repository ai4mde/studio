# Create your tests here.

from django.test import TestCase

from metadata.models import Project, System


class SystemModelTests(TestCase):
    def test_create_system(self):
        project = Project.objects.create(
            name="Test Project",
            description="Test description",
        )
        system = System.objects.create(
            name="Test System",
            description="System description",
            project=project,
        )

        self.assertEqual(system.name, "Test System")
        self.assertEqual(system.project.name, "Test Project")