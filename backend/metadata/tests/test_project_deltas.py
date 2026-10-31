from copy import deepcopy
from uuid import uuid4

from django.test import SimpleTestCase

from metadata.services.versioning import (
    ProjectDeltaError,
    apply_delta,
    empty_project_state,
    generate_delta,
    invert_delta,
)


class ProjectDeltaTests(SimpleTestCase):
    def setUp(self):
        self.project_id = str(uuid4())
        self.system_id = str(uuid4())
        self.first_id = str(uuid4())
        self.second_id = str(uuid4())
        self.old = empty_project_state(self.project_id)
        self.old["models"]["metadata.Project"][self.project_id] = {
            "id": self.project_id,
            "name": "Example",
            "description": "",
        }
        self.old["models"]["metadata.System"][self.system_id] = {
            "id": self.system_id,
            "project_id": self.project_id,
            "name": "Main",
            "description": "",
        }
        self.old["models"]["metadata.Classifier"][self.first_id] = {
            "id": self.first_id, "system_id": self.system_id, "type": "class"
        }

    def test_create_includes_complete_row(self):
        new = deepcopy(self.old)
        new["models"]["metadata.Classifier"][self.second_id] = {
            "id": self.second_id, "system_id": self.system_id, "type": "enum"
        }
        delta = generate_delta(self.old, new)
        self.assertEqual(len(delta), 1)
        self.assertEqual(delta[0]["operation"], "CREATE")
        self.assertEqual(delta[0]["model"], "metadata.Classifier")
        self.assertEqual(delta[0]["data"], new["models"]["metadata.Classifier"][self.second_id])
        self.assertEqual(apply_delta(self.old, delta), new)

    def test_delete_includes_complete_previous_row(self):
        new = deepcopy(self.old)
        removed = new["models"]["metadata.Classifier"].pop(self.first_id)
        delta = generate_delta(self.old, new)
        self.assertEqual(len(delta), 1)
        self.assertEqual(delta[0]["operation"], "DELETE")
        self.assertEqual(delta[0]["data"], removed)
        self.assertEqual(apply_delta(self.old, delta), new)

    def test_update_stores_only_modified_fields(self):
        new = deepcopy(self.old)
        new["models"]["metadata.System"][self.system_id]["name"] = "Renamed"
        new["models"]["metadata.System"][self.system_id]["description"] = "Updated"
        delta = generate_delta(self.old, new)
        self.assertEqual(len(delta), 1)
        self.assertEqual(delta[0]["operation"], "UPDATE")
        self.assertEqual(delta[0]["changes"], {
            "description": {"old": "", "new": "Updated"},
            "name": {"old": "Main", "new": "Renamed"},
        })
        self.assertEqual(apply_delta(self.old, delta), new)

    def test_no_changes_produces_empty_delta(self):
        self.assertEqual(generate_delta(self.old, deepcopy(self.old)), [])
        self.assertEqual(apply_delta(self.old, []), self.old)

    def test_initial_version_is_all_creates(self):
        delta = generate_delta(empty_project_state(self.project_id), self.old)
        self.assertEqual(len(delta), 3)
        self.assertEqual({op["operation"] for op in delta}, {"CREATE"})
        self.assertEqual(apply_delta(empty_project_state(self.project_id), delta), self.old)

    def test_round_trip_mixed_changes_and_inverse(self):
        new = deepcopy(self.old)
        del new["models"]["metadata.Classifier"][self.first_id]
        new["models"]["metadata.Classifier"][self.second_id] = {
            "id": self.second_id, "system_id": self.system_id, "type": "enum"
        }
        new["models"]["metadata.Project"][self.project_id]["name"] = "Renamed"
        original = deepcopy(self.old)
        delta = generate_delta(self.old, new)
        self.assertEqual({op["operation"] for op in delta}, {"CREATE", "UPDATE", "DELETE"})
        self.assertEqual(apply_delta(self.old, delta), new)
        self.assertEqual(apply_delta(new, invert_delta(delta)), self.old)
        self.assertEqual(self.old, original)  # neither comparison nor application mutates inputs

    def test_output_is_deterministic(self):
        new = deepcopy(self.old)
        new["models"]["metadata.System"][self.system_id]["name"] = "Changed"
        self.assertEqual(generate_delta(self.old, new), generate_delta(self.old, new))

    def test_rejects_comparing_different_projects(self):
        other = empty_project_state(uuid4())
        with self.assertRaisesRegex(ProjectDeltaError, "different projects"):
            generate_delta(self.old, other)

    def test_rejects_stale_update(self):
        new = deepcopy(self.old)
        new["models"]["metadata.System"][self.system_id]["name"] = "Updated"
        delta = generate_delta(self.old, new)
        diverged = deepcopy(self.old)
        diverged["models"]["metadata.System"][self.system_id]["name"] = "Different"
        with self.assertRaisesRegex(ProjectDeltaError, "Stale UPDATE"):
            apply_delta(diverged, delta)

    def test_rejects_stale_delete(self):
        new = deepcopy(self.old)
        del new["models"]["metadata.Classifier"][self.first_id]
        delta = generate_delta(self.old, new)
        diverged = deepcopy(self.old)
        diverged["models"]["metadata.Classifier"][self.first_id]["type"] = "signal"
        with self.assertRaisesRegex(ProjectDeltaError, "Stale DELETE"):
            apply_delta(diverged, delta)

    def test_rejects_duplicate_operations(self):
        new = deepcopy(self.old)
        new["models"]["metadata.Project"][self.project_id]["name"] = "Changed"
        op = generate_delta(self.old, new)[0]
        with self.assertRaisesRegex(ProjectDeltaError, "Duplicate operation"):
            apply_delta(self.old, [op, op])

    def test_schema_field_changes_need_migration(self):
        new = deepcopy(self.old)
        new["models"]["metadata.System"][self.system_id]["extra_field"] = "value"
        with self.assertRaisesRegex(ProjectDeltaError, "schema migration"):
            generate_delta(self.old, new)

    def test_multiple_deltas_reconstruct_version_history(self):
        b = deepcopy(self.old)
        b["models"]["metadata.Project"][self.project_id]["name"] = "B"
        c = deepcopy(b)
        c["models"]["metadata.Project"][self.project_id]["name"] = "C"
        a_delta = generate_delta(empty_project_state(self.project_id), self.old)
        b_delta = generate_delta(self.old, b)
        c_delta = generate_delta(b, c)
        reconstructed = empty_project_state(self.project_id)
        for delta in (a_delta, b_delta, c_delta):
            reconstructed = apply_delta(reconstructed, delta)
        self.assertEqual(reconstructed, c)

    def test_rejects_missing_or_invalid_operations(self):
        with self.assertRaisesRegex(ProjectDeltaError, "Unknown delta operation"):
            apply_delta(self.old, [{"operation": "MOVE", "model": "metadata.System", "id": self.system_id}])
        with self.assertRaisesRegex(ProjectDeltaError, "Cannot UPDATE missing"):
            apply_delta(self.old, [{"operation": "UPDATE", "model": "metadata.System", "id": self.second_id, "changes": {"name": {"old": "A", "new": "B"}}}])
