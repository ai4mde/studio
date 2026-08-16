from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from .adapters import activity_graph_to_eval_graph, friedrich_reference_to_eval_graph
from .eval_graph import SCORING_NODE_TYPES, normalize_label


class EvalGraphAdapterTests(unittest.TestCase):
    def test_normalize_label_is_lexical_and_deterministic(self) -> None:
        self.assertEqual(normalize_label("  Not_OK -- (retry)? "), "not ok retry")
        self.assertIsNone(normalize_label(None))

    def test_normalize_label_ignores_trivial_formatting(self) -> None:
        variants = [
            "Process Order",
            "process order",
            "  Process   Order  ",
            "Process_Order",
            "Process-Order",
            "Process: Order!",
        ]
        for value in variants:
            with self.subTest(value=value):
                self.assertEqual(normalize_label(value), "process order")

    def test_reference_gateway_direction_is_inferred_from_sequence_flows(self) -> None:
        xml = b"""\
<IBISWorkflow><Workflows><WorkflowGroup><Workflow>
  <WorkflowModule moduleType="StartEvent"><ModuleId>start</ModuleId>
    <Connection moduleOutId="choice" type="SequenceFlow" />
  </WorkflowModule>
  <WorkflowModule moduleType="Gateway"><ModuleId>choice</ModuleId>
    <Properties><Property name="GatewayType">ExclusiveDataBased</Property></Properties>
    <Connection moduleOutId="yes" type="SequenceFlow"><ConnectionName>YES</ConnectionName></Connection>
    <Connection moduleOutId="join" type="SequenceFlow"><ConnectionName>NO</ConnectionName></Connection>
  </WorkflowModule>
  <WorkflowModule moduleType="Task"><ModuleId>yes</ModuleId><ModuleName>Do_Work</ModuleName>
    <Connection moduleOutId="join" type="SequenceFlow" />
  </WorkflowModule>
  <WorkflowModule moduleType="Gateway"><ModuleId>join</ModuleId>
    <Properties><Property name="GatewayType">ExclusiveDataBased</Property></Properties>
    <Connection moduleOutId="end" type="SequenceFlow" />
  </WorkflowModule>
  <WorkflowModule moduleType="StopEvent"><ModuleId>end</ModuleId></WorkflowModule>
</Workflow></WorkflowGroup></Workflows></IBISWorkflow>
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.xml"
            path.write_bytes(xml)
            graph = friedrich_reference_to_eval_graph(path)

        types_by_id = {node.id: node.type for node in graph.nodes}
        self.assertEqual(types_by_id["choice"], "decision")
        self.assertEqual(types_by_id["join"], "merge")
        self.assertIn(
            ("choice", "yes", "yes"),
            {(edge.source, edge.target, edge.label) for edge in graph.edges},
        )

    def test_activity_graph_maps_only_shared_control_flow(self) -> None:
        graph = activity_graph_to_eval_graph(
            {
                "nodes": [
                    {"id": "start", "type": "initial"},
                    {"id": "check", "type": "decision", "label": "Approved?"},
                    {"id": "work", "type": "action", "name": "Do_Work"},
                    {"id": "data", "type": "object", "name": "Record"},
                ],
                "edges": [
                    {"source": "start", "target": "check", "type": "control"},
                    {
                        "source": "check",
                        "target": "work",
                        "type": "control",
                        "condition": "YES",
                    },
                    {"source": "work", "target": "data", "type": "object"},
                ],
            }
        )

        self.assertEqual(
            [node.type for node in graph.nodes], ["initial", "decision", "action"]
        )
        self.assertEqual(graph.nodes[1].label, "approved")
        self.assertEqual(graph.nodes[2].label, "do work")
        self.assertEqual(graph.edges[1].label, "yes")
        self.assertTrue(
            all(
                node.type in SCORING_NODE_TYPES | {"initial", "final"}
                for node in graph.nodes
            )
        )


if __name__ == "__main__":
    unittest.main()
