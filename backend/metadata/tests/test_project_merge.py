"""Tests for merging two project states against their common ancestor."""

from copy import deepcopy
from unittest import expectedFailure
from uuid import uuid4

from django.test import SimpleTestCase

from metadata.services.versioning.delta import empty_project_state
from metadata.services.versioning.merge import ProjectMergeError, merge_project_states


class ProjectMergeTests(SimpleTestCase):
    def setUp(self):
        self.project_id = str(uuid4())
        self.system_id = str(uuid4())
        self.classifier_id = str(uuid4())
        self.base = empty_project_state(self.project_id)
        self.base["models"]["metadata.Project"][self.project_id] = {
            "id": self.project_id,
            "name": "Example",
            "description": "Original",
        }
        self.base["models"]["metadata.System"][self.system_id] = {
            "id": self.system_id,
            "project_id": self.project_id,
            "name": "Main",
            "description": "Original",
        }
        self.base["models"]["metadata.Classifier"][self.classifier_id] = {
            "id": self.classifier_id,
            "system_id": self.system_id,
            "type": "class",
        }
        self.local = deepcopy(self.base)
        self.incoming = deepcopy(self.base)

    def _system(self, state):
        return state["models"]["metadata.System"][self.system_id]

    def test_unchanged_states_merge(self):
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertEqual(result, {"state": self.base, "conflicts": []})

    def test_local_only_change_is_kept(self):
        self._system(self.local)["name"] = "Local"
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertEqual(self._system(result["state"])["name"], "Local")
        self.assertEqual(result["conflicts"], [])

    def test_incoming_only_change_is_kept(self):
        self._system(self.incoming)["name"] = "Incoming"
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertEqual(self._system(result["state"])["name"], "Incoming")
        self.assertEqual(result["conflicts"], [])

    def test_independent_field_changes_are_combined(self):
        self._system(self.local)["name"] = "Local name"
        self._system(self.incoming)["description"] = "Incoming description"
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertEqual(self._system(result["state"]), {
            "id": self.system_id,
            "project_id": self.project_id,
            "name": "Local name",
            "description": "Incoming description",
        })
        self.assertEqual(result["conflicts"], [])

    def test_identical_changes_are_not_conflicts(self):
        self._system(self.local)["name"] = "Shared"
        self._system(self.incoming)["name"] = "Shared"
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertEqual(self._system(result["state"])["name"], "Shared")
        self.assertEqual(result["conflicts"], [])

    def test_conflicting_field_changes_return_no_state(self):
        self._system(self.local)["name"] = "Local"
        self._system(self.incoming)["name"] = "Incoming"
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertIsNone(result["state"])
        self.assertEqual(result["conflicts"], [{
            "kind": "FIELD", "model": "metadata.System", "id": self.system_id,
            "field": "name", "base": "Main", "local": "Local", "incoming": "Incoming",
        }])

    def test_multiple_field_conflicts_are_reported(self):
        self._system(self.local).update(name="Local", description="Local")
        self._system(self.incoming).update(name="Incoming", description="Incoming")
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertIsNone(result["state"])
        self.assertEqual([item["field"] for item in result["conflicts"]], ["description", "name"])

    def test_object_created_on_one_branch_is_included(self):
        new_id = str(uuid4())
        self.local["models"]["metadata.System"][new_id] = {
            "id": new_id, "project_id": self.project_id, "name": "New", "description": "",
        }
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertIn(new_id, result["state"]["models"]["metadata.System"])
        self.assertEqual(result["conflicts"], [])

    def test_both_branches_create_identical_object(self):
        new_id = str(uuid4())
        row = {"id": new_id, "project_id": self.project_id, "name": "New", "description": ""}
        self.local["models"]["metadata.System"][new_id] = deepcopy(row)
        self.incoming["models"]["metadata.System"][new_id] = deepcopy(row)
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertEqual(result["state"]["models"]["metadata.System"][new_id], row)
        self.assertEqual(result["conflicts"], [])

    def test_both_branches_create_different_object_with_same_id(self):
        new_id = str(uuid4())
        local_row = {"id": new_id, "project_id": self.project_id, "name": "Local"}
        incoming_row = {"id": new_id, "project_id": self.project_id, "name": "Incoming"}
        self.local["models"]["metadata.System"][new_id] = local_row
        self.incoming["models"]["metadata.System"][new_id] = incoming_row
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertIsNone(result["state"])
        self.assertEqual(result["conflicts"], [{
            "kind": "CREATE_CREATE", "model": "metadata.System", "id": new_id,
            "field": None, "base": None, "local": local_row, "incoming": incoming_row,
        }])

    def test_deleted_on_one_branch_unchanged_on_other(self):
        del self.local["models"]["metadata.Classifier"][self.classifier_id]
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertNotIn(self.classifier_id, result["state"]["models"]["metadata.Classifier"])
        self.assertEqual(result["conflicts"], [])

    def test_deleted_on_both_branches(self):
        del self.local["models"]["metadata.Classifier"][self.classifier_id]
        del self.incoming["models"]["metadata.Classifier"][self.classifier_id]
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertNotIn(self.classifier_id, result["state"]["models"]["metadata.Classifier"])
        self.assertEqual(result["conflicts"], [])

    def test_local_delete_incoming_update_conflicts(self):
        del self.local["models"]["metadata.Classifier"][self.classifier_id]
        self.incoming["models"]["metadata.Classifier"][self.classifier_id]["type"] = "enum"
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertIsNone(result["state"])
        self.assertEqual(result["conflicts"][0]["kind"], "DELETE_UPDATE")
        self.assertIsNone(result["conflicts"][0]["local"])

    def test_local_update_incoming_delete_conflicts(self):
        self.local["models"]["metadata.Classifier"][self.classifier_id]["type"] = "enum"
        del self.incoming["models"]["metadata.Classifier"][self.classifier_id]
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertIsNone(result["state"])
        self.assertEqual(result["conflicts"][0]["kind"], "UPDATE_DELETE")
        self.assertIsNone(result["conflicts"][0]["incoming"])

    def test_merge_detects_dangling_reference_between_branches(self):
        # Both branches are individually valid. Combined, local deletes S1
        # while incoming creates a new classifier that references S1.
        del self.local["models"]["metadata.Classifier"][self.classifier_id]
        del self.local["models"]["metadata.System"][self.system_id]
        other_id = str(uuid4())
        self.incoming["models"]["metadata.Classifier"][other_id] = {
            "id": other_id, "system_id": self.system_id, "type": "class",
        }
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertIsNone(result["state"])
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertEqual(result["conflicts"][0]["kind"], "MISSING_REFERENCE")
        self.assertEqual(result["conflicts"][0]["id"], other_id)
        self.assertEqual(result["conflicts"][0]["field"], "system_id")

    def test_merge_does_not_modify_inputs(self):
        self._system(self.local)["name"] = "Local"
        self._system(self.incoming)["description"] = "Incoming"
        originals = deepcopy((self.base, self.local, self.incoming))
        result = merge_project_states(self.base, self.local, self.incoming)
        self.assertEqual((self.base, self.local, self.incoming), originals)
        self._system(result["state"])["name"] = "Mutated"
        self.assertEqual((self.base, self.local, self.incoming), originals)

    def test_different_project_ids_are_rejected(self):
        other = empty_project_state(uuid4())
        with self.assertRaisesRegex(ProjectMergeError, "different projects"):
            merge_project_states(self.base, self.local, other)

    def test_deleting_project_row_is_rejected(self):
        del self.local["models"]["metadata.Project"][self.project_id]
        with self.assertRaisesRegex(ProjectMergeError, "preserve the project row"):
            merge_project_states(self.base, self.local, self.incoming)

    def test_invalid_primary_key_is_rejected(self):
        self._system(self.local)["id"] = str(uuid4())
        with self.assertRaises(ProjectMergeError):
            merge_project_states(self.base, self.local, self.incoming)

    def test_merge_is_deterministic(self):
        self._system(self.local)["name"] = "Local"
        self._system(self.incoming)["name"] = "Incoming"
        first = merge_project_states(self.base, self.local, self.incoming)
        second = merge_project_states(self.base, self.local, self.incoming)
        self.assertEqual(first, second)

    def test_new_relation_to_existing_object_is_preserved(self):
        """A newly created reference is safe when its target survives the merge."""
        new_id = str(uuid4())
        self.incoming["models"]["metadata.Classifier"][new_id] = {
            "id": new_id,
            "system_id": self.system_id,
            "type": "class",
        }
        self._system(self.local)["name"] = "Renamed locally"

        result = merge_project_states(self.base, self.local, self.incoming)

        self.assertEqual(result["conflicts"], [])
        self.assertEqual(
            result["state"]["models"]["metadata.Classifier"][new_id]["system_id"],
            self.system_id,
        )
        self.assertEqual(self._system(result["state"])["name"], "Renamed locally")

    def test_retarget_existing_object_before_deleting_old_reference(self):
        """One branch can delete an object if the other changes references away from it."""
        new_system_id = str(uuid4())
        new_system = {
            "id": new_system_id,
            "project_id": self.project_id,
            "name": "Replacement",
            "description": "",
        }
        self.local["models"]["metadata.System"][new_system_id] = deepcopy(new_system)
        self.local["models"]["metadata.Classifier"][self.classifier_id][
            "system_id"
        ] = new_system_id
        self.incoming["models"]["metadata.System"][new_system_id] = deepcopy(new_system)
        self.incoming["models"]["metadata.Classifier"][self.classifier_id][
            "system_id"
        ] = new_system_id
        del self.incoming["models"]["metadata.System"][self.system_id]
        del self.local["models"]["metadata.System"][self.system_id]

        result = merge_project_states(self.base, self.local, self.incoming)

        self.assertEqual(result["conflicts"], [])
        self.assertNotIn(self.system_id, result["state"]["models"]["metadata.System"])
        self.assertEqual(
            result["state"]["models"]["metadata.Classifier"][self.classifier_id]["system_id"],
            new_system_id,
        )

    def test_multiple_missing_references_are_reported(self):
        """Report each dangling relationship created by combining branches."""
        del self.local["models"]["metadata.Classifier"][self.classifier_id]
        del self.local["models"]["metadata.System"][self.system_id]
        new_ids = [str(uuid4()), str(uuid4())]
        for object_id in new_ids:
            self.incoming["models"]["metadata.Classifier"][object_id] = {
                "id": object_id,
                "system_id": self.system_id,
                "type": "class",
            }

        result = merge_project_states(self.base, self.local, self.incoming)

        self.assertIsNone(result["state"])
        self.assertEqual(len(result["conflicts"]), 2)
        self.assertEqual({c["kind"] for c in result["conflicts"]}, {"MISSING_REFERENCE"})
        self.assertEqual({c["id"] for c in result["conflicts"]}, set(new_ids))

    def test_conflicts_across_multiple_models_are_reported(self):
        """Collect conflicting edits on both Project and System."""
        self.local["models"]["metadata.Project"][self.project_id]["name"] = "Local project"
        self.incoming["models"]["metadata.Project"][self.project_id]["name"] = "Incoming project"
        self._system(self.local)["name"] = "Local system"
        self._system(self.incoming)["name"] = "Incoming system"

        result = merge_project_states(self.base, self.local, self.incoming)

        self.assertIsNone(result["state"])
        self.assertEqual(
            {(c["model"], c["field"]) for c in result["conflicts"]},
            {("metadata.Project", "name"), ("metadata.System", "name")},
        )

    def test_different_foreign_key_changes_conflict(self):
        """Two branches retargeting the same FK differently need resolution."""
        system_ids = [str(uuid4()), str(uuid4())]
        for state, new_id in zip((self.local, self.incoming), system_ids):
            state["models"]["metadata.System"][new_id] = {
                "id": new_id,
                "project_id": self.project_id,
                "name": "New system",
                "description": "",
            }
            state["models"]["metadata.Classifier"][self.classifier_id]["system_id"] = new_id

        result = merge_project_states(self.base, self.local, self.incoming)

        self.assertIsNone(result["state"])
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertEqual(result["conflicts"][0]["kind"], "FIELD")
        self.assertEqual(result["conflicts"][0]["field"], "system_id")

    def test_field_and_missing_reference_conflicts_are_both_reported(self):
        """Future behavior: report both conflict kinds in the same merge."""
        self.local["models"]["metadata.Project"][self.project_id]["name"] = "Local"
        self.incoming["models"]["metadata.Project"][self.project_id]["name"] = "Incoming"
        del self.local["models"]["metadata.Classifier"][self.classifier_id]
        del self.local["models"]["metadata.System"][self.system_id]
        new_id = str(uuid4())
        self.incoming["models"]["metadata.Classifier"][new_id] = {
            "id": new_id,
            "system_id": self.system_id,
            "type": "class",
        }

        result = merge_project_states(self.base, self.local, self.incoming)

        self.assertIsNone(result["state"])
        self.assertEqual(
            {conflict["kind"] for conflict in result["conflicts"]},
            {"FIELD", "MISSING_REFERENCE"},
        )

    def test_invalid_input_foreign_key_is_rejected(self):
        """Future behavior: reject an input branch that is already internally invalid."""
        self.local["models"]["metadata.Classifier"][self.classifier_id][
            "system_id"
        ] = str(uuid4())

        with self.assertRaisesRegex(ProjectMergeError, "reference"):
            merge_project_states(self.base, self.local, self.incoming)