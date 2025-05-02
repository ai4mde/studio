import re
from functools import cached_property
import json
from typing import Any, NamedTuple

from utils.file_generation import write_to_file
from utils.sanitization import page_name_sanitization, app_name_sanitization


class Condition(NamedTuple):
    isElse: bool
    operator: str | None
    threshold: str | None
    aggregator: str | None
    target_attribute: str | None
    target_class_name: str | None
    target_attribute_type: str | None


class Node(NamedTuple):
    id: str
    name: str | None
    type: str
    actor_node: str | None
    next_nodes: list["Node"] | None
    conditions: list[Condition | None] | None
    url: str | None = None
    custom_code: str | None = None


class Edge(NamedTuple):
    target_node: str
    condition: Condition | None


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
            actor_node['id']: app_name_sanitization(actor_node['cls']['name'])
            for usecase_diagram in filter(lambda diagram: diagram['type'] == 'usecase', self.metadata['diagrams'])
            for actor_node in filter(lambda node: node['cls']['type'] == 'actor', usecase_diagram['nodes'])
        }
    
    @cached_property
    def interface_map(self) -> dict[str, str]:
        """Map from the action node UUID to a possible interface url"""
        return {
            page['action']['value']: f"/{app_name_sanitization(interface['value']['name'])}/render_{app_name_sanitization(interface['value']['name'])}_{page_name_sanitization(page['name'])}"
            for interface in self.metadata['interfaces']
            for page in interface['value']['data']['pages']
            if page['type']['value'] != 'normal'
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
                condition=Condition(
                    isElse=edge['rel']['condition']['isElse'],
                    operator=edge['rel']['condition']['operator'],
                    threshold=edge['rel']['condition']['threshold'],
                    aggregator=edge['rel']['condition']['aggregator'],
                    target_attribute=edge['rel']['condition']['target_attribute'],
                    target_class_name=edge['rel']['condition']['target_class_name'],
                    target_attribute_type=edge['rel']['condition']['target_attribute_type'],
                ) if edge['rel']['condition'] else None,
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
                url=self.interface_map.get(current_node['id']),
                custom_code=current_node['cls'].get('customCode') if current_node['cls'].get('isAutomatic') else None,
            )
            self.visited_nodes[current_node_id] = node
            return node

        # Create the current node and mark it as visited
        node = Node(
            id=current_node['id'],
            name=current_node['cls'].get('name'),
            type=current_node['cls']['type'],
            actor_node=self.actors.get(current_node['cls'].get('actorNode')),
            next_nodes=[],
            conditions=[],
            url=self.interface_map.get(current_node['id']),
            custom_code=current_node['cls'].get('customCode'),
        )
        self.visited_nodes[current_node_id] = node

        # Recursive case: Parse the next nodes
        next_nodes, conditions = [], []
        for edge in outgoing_edges:
            next_node = self.parse_node(diagram, edge.target_node)
            next_nodes.append(next_node)
            conditions.append(edge.condition)

        # Update the current node with the found next nodes and conditions
        node = node._replace(
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
                "url": node.url,
                "custom_code": node.custom_code
            }
            self.action_node_id += 1

        # Recursively process the next nodes
        for next_node in node.next_nodes or []:
            _, recursive_start_node = self.create_action_nodes(next_node)
            if start_node is None and recursive_start_node is not None:
                start_node = recursive_start_node

        return list(self.action_nodes.values()), start_node

    def create_condition(self, node: Node) -> list[dict[str, Any]]:
        """Recursively create a rule for an action node. The input node should be of type 'action'"""
        rule: list[dict[str, Any]] = []
        if not node.next_nodes:
            return rule
        for next_node, condition in zip(node.next_nodes or [], node.conditions or []):
            # TODO add logic for parallel nodes
            next_value = (
                "END" if next_node.type == "final"
                else self.action_nodes[next_node.id]['id']
                if next_node.type == "action"
                else self.create_condition(next_node)
            )

            # Flatten the next value if possible
            if isinstance(next_value, list) and len(next_value) == 1 and len(next_value[0].keys()) == 1 and (
                isinstance(next_value[0].get("next"), int) or next_value[0].get("next") == "END"
            ):
                next_value = next_value[0].get("next")
            rule_entry = {"next": next_value}
            if condition and not condition.isElse:
                rule_entry["condition"] = condition._asdict()
            rule.append(rule_entry)
        return rule

    def create_rules(self) -> list[dict[str, Any]]:
        """Create rules for each action node"""
        rules = []
        for node_uuid, action_node in self.action_nodes.items():
            if node_uuid not in self.visited_nodes:
                raise ValueError(f"Something went wrong in the generation process, node {node_uuid} not found")
            node = self.visited_nodes[node_uuid]


            rule = {
                "id": self.rules_id,
                "action_node": action_node['id'],
            }
    
            # Only add the condition if there are multiple next nodes
            condition = self.create_condition(node)
            if len(condition) == 1 and len(condition[0].keys()) == 1 and (
                isinstance(condition[0].get("next"), int) or condition[0].get("next") == "END"
            ):
                rule['next'] = condition[0].get("next")
            else:
                rule['condition'] = condition
            rules.append(rule)
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
    CUSTOM_CODE_FILE_PATH = f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/workflow_engine/custom_code.py"

    # Parse the metadata and generate the workflow engine data
    parser = ActivityDiagramParser(json.loads(metadata))
    workflow_engine_data = parser.get_workflow_engine_data()

    # Process custom code for action nodes
    custom_code_to_add = []
    for action_node in workflow_engine_data['action_nodes']:
        if action_node['custom_code']:
            # Generate a unique function name
            name_pattern = r"def\s+(\w+)\s*\("
            action_node_name = action_node['name'].replace(" ", "_")
            code = re.sub(name_pattern, r"def \1" + f"_{action_node_name}" + "(", action_node['custom_code'])
            custom_code_to_add.append(code)

            # Store a reference to the function in the action node
            match = re.search(name_pattern, code)
            if not match:
                raise ValueError(f"Custom code for action node {action_node['name']} does not contain a function definition")
            action_node['custom_code'] = f"workflow_engine.custom_code.{match.group(1)}"

    # Add the custom code to the workflow engine file
    if custom_code_to_add:
        custom_code_content = f"from workflow_engine.models import ActiveProcess\n\n" + "\n\n".join(custom_code_to_add)
        if not write_to_file(CUSTOM_CODE_FILE_PATH, custom_code_content):
            raise Exception(f"Failed to generate {project_name}/workflow_engine/custom_code.py")

    # Export the workflow engine data to a JSON file which can be used during the migration
    if write_to_file(OUTPUT_FILE_PATH, json.dumps(workflow_engine_data, indent=4)):
        return True

    raise Exception(f"Failed to generate {project_name}/workflow_engine/migrations/workflow_engine_data.json")
