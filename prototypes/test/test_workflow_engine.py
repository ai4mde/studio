import sys
import unittest
from pathlib import Path


class WorkflowEngineGenerationTests(unittest.TestCase):
    def test_activity_guard_available_generates_exclusive_condition_rule(self):
        generation_scripts = (
            Path(__file__).resolve().parents[1]
            / "backend"
            / "generation"
            / "generation_scripts"
        )
        sys.path.insert(0, str(generation_scripts))
        try:
            from utils.workflow_engine.data_generation import ActivityDiagramParser
        finally:
            try:
                sys.path.remove(str(generation_scripts))
            except ValueError:
                pass

        metadata = {
            "interfaces": [],
            "diagrams": [
                {
                    "id": "classes",
                    "type": "classes",
                    "nodes": [{
                        "id": "book-node",
                        "cls": {"data": {
                            "type": "class",
                            "name": "Book",
                            "attributes": [{"name": "copies_available", "type": "int"}],
                        }},
                    }],
                    "edges": [],
                },
                {
                    "id": "activity",
                    "name": "Borrowing",
                    "type": "activity",
                    "nodes": [
                        {"id": "initial", "cls": {"data": {"type": "initial", "name": "Initial"}}},
                        {"id": "check", "cls": {"data": {"type": "action", "name": "Check Availability", "actorNodeName": "Librarian"}}},
                        {"id": "decision", "cls": {"data": {"type": "decision", "name": "Decision"}}},
                        {"id": "create", "cls": {"data": {"type": "action", "name": "Create Loan Record", "actorNodeName": "Librarian"}}},
                        {"id": "notify", "cls": {"data": {"type": "action", "name": "Notify Unavailable", "actorNodeName": "Librarian"}}},
                        {"id": "final", "cls": {"data": {"type": "final", "name": "Final"}}},
                    ],
                    "edges": [
                        {"id": "e1", "source_ptr": "initial", "target_ptr": "check", "rel": {"data": {"type": "controlflow"}}},
                        {"id": "e2", "source_ptr": "check", "target_ptr": "decision", "rel": {"data": {"type": "controlflow"}}},
                        {"id": "e3", "source_ptr": "decision", "target_ptr": "create", "rel": {"data": {"type": "controlflow", "guard": "[available]"}}},
                        {"id": "e4", "source_ptr": "decision", "target_ptr": "notify", "rel": {"data": {"type": "controlflow", "guard": "[unavailable]"}}},
                        {"id": "e5", "source_ptr": "create", "target_ptr": "final", "rel": {"data": {"type": "controlflow"}}},
                        {"id": "e6", "source_ptr": "notify", "target_ptr": "final", "rel": {"data": {"type": "controlflow"}}},
                    ],
                },
            ],
        }

        _, workflow_data = ActivityDiagramParser(metadata).get_workflow_engine_data()
        check_action = next(node for node in workflow_data["action_nodes"] if node["name"] == "Check Availability")
        check_rule = next(rule for rule in workflow_data["rules"] if rule["action_node"] == check_action["id"])
        branch = check_rule["condition"][0]["next"]

        self.assertEqual(branch[0]["condition"]["target_class_name"], "Book")
        self.assertEqual(branch[0]["condition"]["target_attribute"], "copies_available")
        self.assertEqual(branch[0]["condition"]["operator"], ">")
        self.assertEqual(branch[0]["condition"]["threshold"], "0")
        self.assertEqual(len(branch), 2)
        self.assertNotIn("condition", branch[1])


if __name__ == "__main__":
    unittest.main()
