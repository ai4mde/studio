"""Tests for resolving merge conflicts without database writes."""

from copy import deepcopy
from uuid import uuid4

from django.test import SimpleTestCase

from metadata.services.versioning.delta import empty_project_state
from metadata.services.versioning.merge import merge_project_states
from metadata.services.versioning.resolution import (
    ProjectMergeResolutionError,
    resolve_merge_conflicts,
)


class ProjectMergeResolutionTests(SimpleTestCase):
    def setUp(self):
        self.project_id = str(uuid4())
        self.system_id = str(uuid4())
        self.classifier_id = str(uuid4())
        self.base = empty_project_state(self.project_id)
        self.base["models"]["metadata.Project"][self.project_id] = {
            "id": self.project_id, "name": "Example", "description": "Original",
        }
        self.base["models"]["metadata.System"][self.system_id] = {
            "id": self.system_id, "project_id": self.project_id,
            "name": "Main", "description": "Original",
        }
        self.base["models"]["metadata.Classifier"][self.classifier_id] = {
            "id": self.classifier_id, "system_id": self.system_id, "type": "class",
        }
        self.local = deepcopy(self.base)
        self.incoming = deepcopy(self.base)

    def system(self, state):
        return state["models"]["metadata.System"][self.system_id]

    def field_conflict(self):
        self.system(self.local)["name"] = "Local"
        self.system(self.incoming)["name"] = "Incoming"
        return self.resolution("LOCAL")

    def resolution(self, choice, kind="FIELD", label="metadata.System", object_id=None, field="name", **kwargs):
        return {
            "kind": kind, "model": label, "id": object_id or self.system_id,
            "field": field, "choice": choice, **kwargs,
        }

    def test_no_conflicts_needs_no_resolutions(self):
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [])
        self.assertEqual(result, self.base)
        self.assertIsNot(result, self.base)

    def test_select_local_field_value(self):
        resolution = self.field_conflict()
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertEqual(self.system(result)["name"], "Local")

    def test_select_incoming_field_value(self):
        resolution = self.field_conflict()
        resolution["choice"] = "INCOMING"
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertEqual(self.system(result)["name"], "Incoming")

    def test_select_base_field_value(self):
        resolution = self.field_conflict()
        resolution["choice"] = "BASE"
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertEqual(self.system(result)["name"], "Main")

    def test_custom_field_value(self):
        resolution = self.field_conflict()
        resolution.update(choice="CUSTOM", value="Reviewed")
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertEqual(self.system(result)["name"], "Reviewed")

    def test_independent_changes_survive_conflict_resolution(self):
        resolution = self.field_conflict()
        self.system(self.local)["description"] = "Local description"
        self.incoming["models"]["metadata.Project"][self.project_id]["description"] = "Incoming project"
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertEqual(self.system(result)["description"], "Local description")
        self.assertEqual(result["models"]["metadata.Project"][self.project_id]["description"], "Incoming project")

    def test_multiple_conflicts_resolved_independently(self):
        resolution = self.field_conflict()
        self.system(self.local)["description"] = "Local description"
        self.system(self.incoming)["description"] = "Incoming description"
        second = self.resolution("INCOMING", field="description")
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution, second])
        self.assertEqual(self.system(result)["name"], "Local")
        self.assertEqual(self.system(result)["description"], "Incoming description")

    def test_missing_resolution_is_rejected(self):
        self.field_conflict()
        with self.assertRaisesRegex(ProjectMergeResolutionError, "Missing conflict resolutions"):
            resolve_merge_conflicts(self.base, self.local, self.incoming, [])

    def test_unknown_resolution_is_rejected(self):
        with self.assertRaisesRegex(ProjectMergeResolutionError, "Unknown or stale"):
            resolve_merge_conflicts(self.base, self.local, self.incoming, [self.resolution("LOCAL")])

    def test_duplicate_resolution_is_rejected(self):
        resolution = self.field_conflict()
        with self.assertRaisesRegex(ProjectMergeResolutionError, "Duplicate"):
            resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution, resolution])

    def test_invalid_choice_is_rejected(self):
        resolution = self.field_conflict()
        resolution["choice"] = "DELETE_OBJECT"
        with self.assertRaisesRegex(ProjectMergeResolutionError, "Invalid field resolution"):
            resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])

    def test_custom_field_requires_value(self):
        resolution = self.field_conflict()
        resolution["choice"] = "CUSTOM"
        with self.assertRaisesRegex(ProjectMergeResolutionError, "requires a value"):
            resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])

    def test_custom_field_rejects_non_json_value(self):
        resolution = self.field_conflict()
        resolution.update(choice="CUSTOM", value=object())
        with self.assertRaisesRegex(ProjectMergeResolutionError, "JSON serializable"):
            resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])

    def test_create_create_conflict_selects_incoming_row(self):
        object_id = str(uuid4())
        self.local["models"]["metadata.System"][object_id] = {
            "id": object_id, "project_id": self.project_id, "name": "Local", "description": "",
        }
        self.incoming["models"]["metadata.System"][object_id] = {
            "id": object_id, "project_id": self.project_id, "name": "Incoming", "description": "",
        }
        resolution = self.resolution("INCOMING", kind="CREATE_CREATE", object_id=object_id, field=None)
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertEqual(result["models"]["metadata.System"][object_id]["name"], "Incoming")

    def test_delete_update_conflict_can_keep_updated_object(self):
        del self.local["models"]["metadata.Classifier"][self.classifier_id]
        self.incoming["models"]["metadata.Classifier"][self.classifier_id]["type"] = "enum"
        resolution = self.resolution("INCOMING", kind="DELETE_UPDATE", label="metadata.Classifier", object_id=self.classifier_id, field=None)
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertEqual(result["models"]["metadata.Classifier"][self.classifier_id]["type"], "enum")

    def test_delete_update_conflict_can_delete_object(self):
        del self.local["models"]["metadata.Classifier"][self.classifier_id]
        self.incoming["models"]["metadata.Classifier"][self.classifier_id]["type"] = "enum"
        resolution = self.resolution("LOCAL", kind="DELETE_UPDATE", label="metadata.Classifier", object_id=self.classifier_id, field=None)
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertNotIn(self.classifier_id, result["models"]["metadata.Classifier"])

    def test_update_delete_conflict_can_delete_object(self):
        self.local["models"]["metadata.Classifier"][self.classifier_id]["type"] = "enum"
        del self.incoming["models"]["metadata.Classifier"][self.classifier_id]
        resolution = self.resolution("INCOMING", kind="UPDATE_DELETE", label="metadata.Classifier", object_id=self.classifier_id, field=None)
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertNotIn(self.classifier_id, result["models"]["metadata.Classifier"])

    def reference_conflict(self):
        # Local deletes S1 and its original classifier; incoming creates C2 -> S1.
        del self.local["models"]["metadata.Classifier"][self.classifier_id]
        del self.local["models"]["metadata.System"][self.system_id]
        new_id = str(uuid4())
        self.incoming["models"]["metadata.Classifier"][new_id] = {
            "id": new_id, "system_id": self.system_id, "type": "class",
        }
        resolution = self.resolution(
            "RESTORE_TARGET", kind="MISSING_REFERENCE", label="metadata.Classifier",
            object_id=new_id, field="system_id",
        )
        return new_id, resolution

    def test_missing_reference_restores_target(self):
        new_id, resolution = self.reference_conflict()
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertIn(self.system_id, result["models"]["metadata.System"])
        self.assertEqual(result["models"]["metadata.Classifier"][new_id]["system_id"], self.system_id)

    def test_missing_reference_can_delete_referencing_object(self):
        new_id, resolution = self.reference_conflict()
        resolution["choice"] = "DELETE_OBJECT"
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertNotIn(new_id, result["models"]["metadata.Classifier"])
        self.assertNotIn(self.system_id, result["models"]["metadata.System"])

    def test_restoration_does_not_modify_inputs(self):
        _, resolution = self.reference_conflict()
        copies = deepcopy((self.base, self.local, self.incoming))
        resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertEqual(copies, (self.base, self.local, self.incoming))

    def test_field_and_reference_conflicts_can_be_resolved_together(self):
        new_id, reference_resolution = self.reference_conflict()
        self.local["models"]["metadata.Project"][self.project_id]["name"] = "Local project"
        self.incoming["models"]["metadata.Project"][self.project_id]["name"] = "Incoming project"
        field_resolution = self.resolution("INCOMING", label="metadata.Project", object_id=self.project_id)
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [reference_resolution, field_resolution])
        self.assertIn(new_id, result["models"]["metadata.Classifier"])
        self.assertEqual(result["models"]["metadata.Project"][self.project_id]["name"], "Incoming project")

    def test_custom_reference_to_missing_target_is_rejected(self):
        """Reject a chosen FK value that does not exist in the combined state."""
        second_id, third_id = str(uuid4()), str(uuid4())
        for state, target_id in ((self.local, second_id), (self.incoming, third_id)):
            state["models"]["metadata.System"][target_id] = {
                "id": target_id, "project_id": self.project_id,
                "name": "New", "description": "",
            }
            state["models"]["metadata.Classifier"][self.classifier_id]["system_id"] = target_id
        resolution = self.resolution(
            "CUSTOM", label="metadata.Classifier", object_id=self.classifier_id,
            field="system_id", value=str(uuid4()),
        )
        with self.assertRaisesRegex(ProjectMergeResolutionError, "invalid reference"):
            resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])

    def test_invalid_input_foreign_key_is_rejected(self):
        self.local["models"]["metadata.Classifier"][self.classifier_id]["system_id"] = str(uuid4())
        with self.assertRaisesRegex(ProjectMergeResolutionError, "invalid foreign-key reference"):
            resolve_merge_conflicts(self.base, self.local, self.incoming, [])

    def test_custom_field_preserves_primary_key(self):
        resolution = self.field_conflict()
        resolution.update(choice="CUSTOM", value="Arbitrary")
        # Regular name changes are fine; the merge never permits custom PKs because
        # primary keys cannot become field conflicts in well-formed input states.
        result = resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
        self.assertEqual(self.system(result)["id"], self.system_id)

    def test_conflicts_are_recomputed_on_each_attempt(self):
        resolution = self.field_conflict()
        original = merge_project_states(self.base, self.local, self.incoming)["conflicts"]
        self.assertEqual(len(original), 1)
        self.system(self.incoming)["name"] = "Local"
        with self.assertRaisesRegex(ProjectMergeResolutionError, "Unknown or stale"):
            resolve_merge_conflicts(self.base, self.local, self.incoming, [resolution])
