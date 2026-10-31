from copy import deepcopy
from uuid import uuid4

from django.test import TestCase

from metadata.models import ClassClassifier, Classifier, Project, System
from metadata.services.versioning.applicator import (
    ProjectApplicationError,
    apply_project_changes,
)
from metadata.services.versioning.delta import apply_delta, generate_delta
from metadata.services.versioning.serializer import serialize_project


class ProjectApplicatorTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Example", description="Original")
        self.system = System.objects.create(project=self.project, name="Main")

    def _apply_state(self, target):
        previous = serialize_project(self.project.pk)
        delta = generate_delta(previous, target)
        apply_project_changes(self.project.pk, delta)
        self.assertEqual(serialize_project(self.project.pk), target)

    def test_create_update_and_delete_are_incremental(self):
        # CREATE a new system, UPDATE the existing system, UPDATE the project.
        before = serialize_project(self.project.pk)
        desired = deepcopy(before)
        new_id = str(uuid4())
        desired["models"]["metadata.System"][new_id] = {
            "id": new_id,
            "project_id": str(self.project.pk),
            "name": "New system",
            "description": "",
        }
        desired["models"]["metadata.System"][str(self.system.pk)]["name"] = "Updated"
        desired["models"]["metadata.Project"][str(self.project.pk)]["description"] = "Changed"
        self._apply_state(desired)

        self.system.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(self.system.name, "Updated")
        self.assertEqual(self.project.description, "Changed")
        self.assertTrue(System.objects.filter(pk=new_id).exists())

        # DELETE only the new system; retain the UUID and row of the old one.
        target = deepcopy(desired)
        del target["models"]["metadata.System"][new_id]
        self._apply_state(target)
        self.assertFalse(System.objects.filter(pk=new_id).exists())
        self.assertTrue(System.objects.filter(pk=self.system.pk).exists())

    def test_foreign_key_dependencies_and_one_to_one_primary_key(self):
        before = serialize_project(self.project.pk)
        desired = deepcopy(before)
        classifier_id = str(uuid4())
        desired["models"]["metadata.Classifier"][classifier_id] = {
            "id": classifier_id,
            "system_id": str(self.system.pk),
            "type": "class",
        }
        # ClassClassifier's primary key is classifier_id, NOT id.
        desired["models"]["metadata.ClassClassifier"][classifier_id] = {
            "classifier_id": classifier_id,
            "name": "Customer",
        }
        delta = generate_delta(before, desired)
        self.assertEqual(apply_delta(before, delta), desired)
        apply_project_changes(self.project.pk, delta)

        self.assertTrue(Classifier.objects.filter(pk=classifier_id).exists())
        self.assertTrue(ClassClassifier.objects.filter(pk=classifier_id).exists())
        self.assertEqual(serialize_project(self.project.pk), desired)

        # A later DELETE can remove both rows safely.
        self._apply_state(before)
        self.assertFalse(Classifier.objects.filter(pk=classifier_id).exists())
        self.assertFalse(ClassClassifier.objects.filter(pk=classifier_id).exists())

    def test_retarget_reference_before_deleting_its_old_parent(self):
        classifier = Classifier.objects.create(
            system=self.system,
            type="class",
        )
        before = serialize_project(self.project.pk)
        desired = deepcopy(before)
        new_system_id = str(uuid4())
        desired["models"]["metadata.System"][new_system_id] = {
            "id": new_system_id,
            "project_id": str(self.project.pk),
            "name": "Replacement",
            "description": "",
        }
        desired["models"]["metadata.Classifier"][str(classifier.pk)]["system_id"] = new_system_id
        del desired["models"]["metadata.System"][str(self.system.pk)]

        self._apply_state(desired)
        classifier.refresh_from_db()
        self.assertEqual(str(classifier.system_id), new_system_id)
        self.assertFalse(System.objects.filter(pk=self.system.pk).exists())

    def test_stale_update_does_not_modify_database(self):
        before = serialize_project(self.project.pk)
        target = deepcopy(before)
        target["models"]["metadata.System"][str(self.system.pk)]["name"] = "New name"
        delta = generate_delta(before, target)
        self.system.name = "Concurrent edit"
        self.system.save(update_fields=["name"])

        with self.assertRaisesRegex(ProjectApplicationError, "Stale UPDATE"):
            apply_project_changes(self.project.pk, delta)
        self.system.refresh_from_db()
        self.assertEqual(self.system.name, "Concurrent edit")

    def test_rejects_foreign_key_outside_project_without_changes(self):
        before = serialize_project(self.project.pk)
        other = Project.objects.create(name="Other")
        desired = deepcopy(before)
        desired["models"]["metadata.System"][str(self.system.pk)]["project_id"] = str(other.pk)

        with self.assertRaises(ProjectApplicationError):
            apply_project_changes(self.project.pk, generate_delta(before, desired))
        self.system.refresh_from_db()
        self.assertEqual(self.system.project_id, self.project.pk)

    def test_rejects_deleting_project(self):
        before = serialize_project(self.project.pk)
        desired = deepcopy(before)
        del desired["models"]["metadata.Project"][str(self.project.pk)]
        with self.assertRaises(ProjectApplicationError):
            apply_project_changes(self.project.pk, generate_delta(before, desired))
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_changes_rollback_on_database_constraint_failure(self):
        # The first CREATE succeeds; the second violates a NOT NULL constraint.
        before = serialize_project(self.project.pk)
        desired = deepcopy(before)
        desired["models"]["metadata.System"][str(self.system.pk)]["name"] = "Changed"
        first_id = "00000000-0000-0000-0000-000000000001"
        invalid_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
        desired["models"]["metadata.System"][first_id] = {
            "id": first_id,
            "project_id": str(self.project.pk),
            "name": "Valid",
            "description": "",
        }
        desired["models"]["metadata.System"][invalid_id] = {
            "id": invalid_id,
            "project_id": str(self.project.pk),
            "name": None,
            "description": "",
        }
        with self.assertRaises(Exception):
            apply_project_changes(self.project.pk, generate_delta(before, desired))

        self.assertEqual(serialize_project(self.project.pk), before)
        self.assertFalse(System.objects.filter(pk=first_id).exists())

    def test_does_not_change_the_active_version(self):
        before = serialize_project(self.project.pk)
        desired = deepcopy(before)
        desired["models"]["metadata.Project"][str(self.project.pk)]["name"] = "Edited"
        self._apply_state(desired)
        self.project.refresh_from_db()
        self.assertIsNone(self.project.current_version_id)

    def test_other_project_is_unchanged(self):
        other = Project.objects.create(name="Other")
        other_system = System.objects.create(project=other, name="Unrelated")
        before_other = serialize_project(other.pk)

        before = serialize_project(self.project.pk)
        target = deepcopy(before)
        target["models"]["metadata.System"][str(self.system.pk)]["name"] = "Changed"
        self._apply_state(target)

        self.assertEqual(serialize_project(other.pk), before_other)
        other_system.refresh_from_db()
        self.assertEqual(other_system.name, "Unrelated")

    def test_rejects_invalid_project_id(self):
        with self.assertRaisesRegex(ProjectApplicationError, "Invalid project UUID"):
            apply_project_changes("not-a-uuid", [])
