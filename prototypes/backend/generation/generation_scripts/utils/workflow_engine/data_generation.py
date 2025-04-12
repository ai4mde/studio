from functools import cached_property
import json
from typing import Any, NamedTuple

from utils.file_generation import write_to_file


class Node(NamedTuple):
    id: str
    name: str | None
    type: str
    actor_node: str | None
    next_nodes: list["Node"] | None
    conditions: list[str] | None


class Edge(NamedTuple):
    target_node: str
    condition: str


class Diagram(NamedTuple):
    name: str
    nodes: Node


class ActivityDiagramParser:
    """
        Parser for the activity diagrams metadata. It converts the metadata into a tree of nodes.
        The tree is built recursively, starting from the initial node and following the edges to the next nodes.
        This new structure is used to generate a dictionary with the input data for the workflow engine.
    """

    def __init__(self, metadata: dict[str, Any]):
        self.metadata = metadata
        self.visited_nodes: dict[str, Node] = {}
        self.action_nodes: dict[str, dict[str, Any]] = {}
        self.process_id = 1
        self.action_node_id = 1
        self.rules_id = 1
        
    
    @cached_property
    def actors(self) -> dict[str, str]:
        """Returns id of the actors associated with their name"""
        return {
            actor_node['id']: actor_node['cls']['name'].lower()
            for usecase_diagram in filter(lambda diagram: diagram['type'] == 'usecase', self.metadata['diagrams'])
            for actor_node in filter(lambda node: node['cls']['type'] == 'actor', usecase_diagram['nodes'])
        }

    def find_node(self, nodes: list[dict[str, Any]], node_id: str) -> dict[str, Any]:
        """Find a node by its uuid in a list of nodes"""
        filtered_nodes = list(filter(lambda node: node['id'] == node_id, nodes))
        if not filtered_nodes:
            raise ValueError(f"Node with id {node_id} not found")
        return filtered_nodes[0]

    def find_edges(self, edges: list[dict[str, Any]], source_id: str) -> list[Edge]:
        """Find all edges that have a given source Node"""
        return [
            Edge(
                target_node=edge['target_ptr'],
                condition=edge['rel']['guard']
            ) for edge in filter(lambda edge: edge['source_ptr'] == source_id, edges)
        ]

    def parse_node(self, diagram: dict[str, Any], current_node_id: str) -> Node:
        """Parse a node recursively to build the Node structure"""
        # Base case: If the node has already been visited, return the existing node to avoid duplicates
        if current_node_id in self.visited_nodes:
            return self.visited_nodes[current_node_id]
        
        # Find the current node and its outgoing edges
        current_node = self.find_node(diagram['nodes'], current_node_id)
        outgoing_edges = self.find_edges(diagram['edges'], current_node_id)

        # Base case: If the current node is a final node or has no outgoing edges (end of diagram)
        if current_node['cls']['type'] == 'final' or not outgoing_edges:
            node = Node(
                id=current_node['id'],
                name=current_node['cls'].get('name'),
                type=current_node['cls']['type'],
                actor_node=self.actors.get(current_node['cls'].get('actorNode')),
                next_nodes=None,
                conditions=None,
            )
            self.visited_nodes[current_node_id] = node
            return node

        # Recursive case: Parse the next nodes
        next_nodes, conditions = [], []
        for edge in outgoing_edges:
            next_node = self.parse_node(diagram, edge.target_node)
            next_nodes.append(next_node)
            conditions.append(edge.condition)

        # Create the current Node
        node = Node(
            id=current_node['id'],
            name=current_node['cls'].get('name'),
            type=current_node['cls']['type'],
            actor_node=self.actors.get(current_node['cls'].get('actorNode')),
            next_nodes=next_nodes,
            conditions=conditions,
        )
        self.visited_nodes[current_node_id] = node
        return node

    def parse_activity_diagram(self, diagram: dict[str, Any]) -> Node:
        """Parse an activity diagram starting from the initial node"""
        start_node = list(filter(lambda node: node['cls']['type'] == 'initial', diagram['nodes']))
        if len(start_node) != 1:
            raise ValueError("Activity diagrams must have exactly one start node")
        return self.parse_node(diagram, start_node[0]['id'])

    def parse_metadata(self) -> list[Diagram]:
        """Parse all activity diagrams in the metadata"""
        return [
            Diagram(
                name=diagram['name'],
                nodes=self.parse_activity_diagram(diagram),
            ) for diagram in filter(lambda diagram: diagram['type'] == 'activity', self.metadata['diagrams'])
        ]

    def create_action_nodes(self, node: Node) -> tuple[list[dict[str, Any]], int | None]:
        """Create action nodes starting from the initial node"""
        start_node = None

        # Avoid revisiting nodes
        if node.id in self.action_nodes:
            return ([], None)

        if node.type == 'action':
            if not node.actor_node:
                raise ValueError(f"Node {node.name} does not have a required actor node")

            # Set the first action node as the start node
            if not start_node:
                start_node = self.action_node_id

            # Create the action node
            self.action_nodes[node.id] = {
                "id": self.action_node_id,
                "actor": node.actor_node,
                "name": node.name,
                "process": self.process_id,
            }
            self.action_node_id += 1

        # Recursively process the next nodes
        for next_node in node.next_nodes or []:
            _, recursive_start_node = self.create_action_nodes(next_node)
            if start_node is None and recursive_start_node is not None:
                start_node = recursive_start_node

        return list(self.action_nodes.values()), start_node

    def create_condition(self, node: Node) -> dict[str, dict | str]:
        """Recursively create a rule for an action node. The input node should be of type 'action'"""
        rule: dict = {}
        if not node.next_nodes:
            return rule
        for next_node, condition in zip(node.next_nodes or [], node.conditions or []):
            condition = condition if condition else '*'
            if next_node.type == 'action':
                rule[condition] = f"NEXT({self.action_nodes[next_node.id]['id']})"
            elif next_node.type == 'final':
                rule[condition] = "END"
            # TODO add logic for parallel nodes
            else:
                rule[condition] = self.create_condition(next_node)
        return rule

    def create_rules(self) -> list[dict[str, Any]]:
        """Create rules for each action node"""
        rules = []
        for node_uuid, action_node in self.action_nodes.items():
            if node_uuid not in self.visited_nodes:
                raise ValueError(f"Something went wrong in the generation process, node {node_uuid} not found")
            node = self.visited_nodes[node_uuid]

            # Create the rule
            rules.append({
                "id": self.rules_id,
                "condition": self.create_condition(node),
                "action_node": action_node['id'],
            })
            self.rules_id += 1
        return rules

    def get_workflow_engine_data(self) -> dict[str, list[dict[str, Any]]]:
        """Wrapper function that combines all steps to generate the data for the workflow engine"""
        # Parse the metadata into a more usable format
        diagrams = self.parse_metadata()

        # Create a process for each diagram
        processes = []
        rules = []
        action_nodes = []
        for diagram in diagrams:
            process = {
                "id": self.process_id,
                "name": diagram.name,
            }

            # Create action nodes for the diagram
            nodes, start_node = self.create_action_nodes(diagram.nodes)
            if start_node is None:
                raise ValueError(f"Diagram {diagram.name} does not have a start node")
            action_nodes.extend(nodes)

            # Add the start node to the process
            process['start'] = start_node
            processes.append(process)

            # Create the rules connecting the action nodes
            rules.extend(self.create_rules())

            # Reset the action nodes for the next diagram
            self.action_nodes = {}
            self.process_id += 1
        return {
            "processes": processes,
            "action_nodes": action_nodes,
            "rules": rules,
        }


def generate_data(system_id: str, project_name: str, metadata: str) -> bool:
    OUTPUT_FILE_PATH = f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/workflow_engine/migrations/workflow_engine_data.json"
    parser = ActivityDiagramParser(json.loads(metadata))
    workflow_engine_data = parser.get_workflow_engine_data()

    if write_to_file(OUTPUT_FILE_PATH, json.dumps(workflow_engine_data, indent=4)):
        return True

    raise Exception(f"Failed to generate {project_name}/workflow_engine/migrations/workflow_engine_data.json")
