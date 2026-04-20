import re
from functools import cached_property
import json
from typing import Any, NamedTuple

from utils.file_generation import write_to_file
from utils.loading_json_utils import (
    _classifier_lookup,
    _edge_relation_data,
    _edge_source_ref,
    _edge_target_ref,
    _interface_data,
    _interface_label,
    _node_classifier_data,
    _node_classifier_ref,
    _relation_lookup,
    _relation_record_lookup,
)
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
    next_nodes: list[str] | None
    conditions: list[Condition | None] | None
    url: str | None = None
    custom_code: str | None = None
    incoming_edges_count: int = 0


class Edge(NamedTuple):
    target_node: str
    condition: Condition | None


class CronJob(NamedTuple):
    process_id: int
    schedule: str


class Diagram(NamedTuple):
    name: str
    nodes: dict[str, Node]
    cron_job: CronJob | None = None


class ActivityDiagramParser:
    """
        Parser for the activity diagrams metadata. It converts the metadata into a tree of nodes.
        The tree is built recursively, starting from the initial node and following the edges to the next nodes.
        This new structure is used to generate a dictionary with the input data for the workflow engine.
    """

    def __init__(self, metadata: dict[str, Any]):
        self.metadata = metadata
        self.classifiers_by_id = _classifier_lookup(metadata)
        self.relations_by_id = _relation_lookup(metadata)
        self.relation_records_by_id = _relation_record_lookup(metadata)
        self.nodes: dict[str, Node] = {}
        self.action_nodes: dict[str, dict[str, Any]] = {}
        self.join_nodes: dict[str, dict[str, Any]] = {}
        self.process_id = 1
        self.action_node_id = 1
        self.join_node_id = 1
        self.rules_id = 1
        
    
    @cached_property
    def actors(self) -> dict[str, str]:
        """Returns id of the actors associated with their name"""
        return {
            actor_node['id']: app_name_sanitization(_node_classifier_data(actor_node, self.classifiers_by_id).get('name', ''))
            for usecase_diagram in filter(lambda diagram: diagram['type'] == 'usecase', self.metadata['diagrams'])
            for actor_node in filter(lambda node: _node_classifier_data(node, self.classifiers_by_id).get('type') == 'actor', usecase_diagram['nodes'])
            if _node_classifier_data(actor_node, self.classifiers_by_id).get('name')
        }
    
    @cached_property
    def interface_map(self) -> dict[str, str]:
        """Map from the action node UUID to a possible interface url"""
        return {
            page['action']['value']: f"/{app_name_sanitization(_interface_label(interface))}/render_{app_name_sanitization(_interface_label(interface))}_{page_name_sanitization(page['name'])}"
            for interface in self.metadata['interfaces']
            for page in _interface_data(interface).get('pages', [])
            if page.get('type', {}).get('value') != 'normal' and page.get('action', {}).get('value')
        }

    def _get_incoming_edges_count(self, edges: list[dict[str, Any]], target_id: str) -> int:
        """Get the number of incoming edges for a node"""
        return sum(
            1 for _ in filter(lambda edge: self._resolve_node_id_from_ref(edges[0].get('diagram'), _edge_target_ref(edge, self.relation_records_by_id)) == target_id, edges)
        )

    def _get_diagram(self, diagram_id: str | None) -> dict[str, Any] | None:
        if not diagram_id:
            return None
        return next((diagram for diagram in self.metadata['diagrams'] if diagram.get('id') == diagram_id), None)

    def _resolve_node_id_from_ref(self, diagram_id: str | None, node_ref: str | None) -> str | None:
        if not node_ref:
            return None
        diagram = self._get_diagram(diagram_id)
        if not diagram:
            return node_ref
        for node in diagram.get('nodes', []):
            if node.get('id') == node_ref or _node_classifier_ref(node) == node_ref:
                return node.get('id')
        return node_ref

    def find_node(self, nodes: list[dict[str, Any]], node_id: str) -> dict[str, Any]:
        """Find a node by its uuid in a list of nodes"""
        filtered_nodes = list(filter(lambda node: node['id'] == node_id or _node_classifier_ref(node) == node_id, nodes))
        if not filtered_nodes:
            raise ValueError(f"Node with id {node_id} not found")
        return filtered_nodes[0]

    def find_edges(self, edges: list[dict[str, Any]], source_id: str) -> list[Edge]:
        """Find all edges that have a given source Node"""
        diagram_id = edges[0].get('diagram') if edges else None
        out: list[Edge] = []
        for edge in filter(
            lambda edge: self._resolve_node_id_from_ref(diagram_id, _edge_source_ref(edge, self.relation_records_by_id)) == source_id,
            edges,
        ):
            target_node = self._resolve_node_id_from_ref(diagram_id, _edge_target_ref(edge, self.relation_records_by_id))
            if not target_node:
                continue
            edge_data = _edge_relation_data(edge, self.relations_by_id)
            condition_data = edge_data.get('condition')
            out.append(
                Edge(
                    target_node=target_node,
                    condition=Condition(
                        isElse=condition_data['isElse'],
                        operator=condition_data['operator'],
                        threshold=condition_data['threshold'],
                        aggregator=condition_data['aggregator'],
                        target_attribute=condition_data['target_attribute'],
                        target_class_name=condition_data['target_class_name'],
                        target_attribute_type=condition_data['target_attribute_type'],
                    ) if condition_data else None,
                )
            )
        return out

    def create_nodes(self, diagram: dict[str, Any], node_id: str) -> dict[str, Node] | None:
        """Create all nodes in the diagram recursively"""
        # Avoid revisiting nodes
        if node_id in self.nodes:
            return None
        
        # Find the current node and its outgoing edges as well as a count of incoming edges
        current_node = self.find_node(diagram['nodes'], node_id)
        outgoing_edges = self.find_edges(diagram['edges'], node_id)
        incoming_edges_count = self._get_incoming_edges_count(diagram['edges'], node_id)
        current_node_data = _node_classifier_data(current_node, self.classifiers_by_id)

        node = Node(
            id=current_node['id'],
            name=current_node_data.get('name'),
            type=current_node_data['type'],
            actor_node=self.actors.get(current_node_data.get('actorNode', '')) if current_node_data.get('actorNode') else None,
            next_nodes=[edge.target_node for edge in outgoing_edges],
            conditions=[edge.condition for edge in outgoing_edges],
            incoming_edges_count=incoming_edges_count,
            url=self.interface_map.get(current_node['id']),
            custom_code=current_node_data.get('customCode'),
        )
        self.nodes[node_id] = node

        # Recursively create nodes for the next nodes
        for edge in outgoing_edges:
            self.create_nodes(diagram, edge.target_node)
        return self.nodes

    def parse_activity_diagram(self, diagram: dict[str, Any]) -> tuple[CronJob | None, dict[str, Node] | None]:
        """Parse an activity diagram starting from the initial node"""
        start_node = list(filter(lambda node: _node_classifier_data(node, self.classifiers_by_id).get('type') == 'initial', diagram['nodes']))
        if len(start_node) != 1:
            raise ValueError("Activity diagrams must have exactly one start node")
        start_node = start_node[0]
        start_node_data = _node_classifier_data(start_node, self.classifiers_by_id)
        cron_job = CronJob(
            process_id=self.process_id,
            schedule=start_node_data.get('schedule', '')
        ) if start_node_data.get('scheduled', False) and start_node_data.get('schedule', '') else None
        return cron_job, self.create_nodes(diagram, start_node['id'])

    def parse_metadata(self) -> list[Diagram]:
        """Parse all activity diagrams in the metadata"""
        diagrams = []
        for diagram in filter(lambda diagram: diagram['type'] == 'activity', self.metadata['diagrams']):
            cron_job, nodes = self.parse_activity_diagram(diagram)
            if nodes is None:
                continue
            diagrams.append(Diagram(
                name=diagram['name'],
                nodes=nodes,
                cron_job=cron_job
            ))
        return diagrams

    def create_relevant_nodes(self, nodes: dict[str, Node]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
        for id, node in nodes.items():
            if node.type == 'action':
                if not node.actor_node:
                    raise ValueError(f"Node {node.name} does not have a required actor node")
                self.action_nodes[id] = {
                    "id": self.action_node_id,
                    "actor": node.actor_node,
                    "name": node.name,
                    "process": self.process_id,
                    "url": node.url,
                    "custom_code": node.custom_code
                }
                self.action_node_id += 1
            elif node.type == 'join':
                self.join_nodes[id] = {
                    "id": self.join_node_id,
                    "incoming_edges_count": node.incoming_edges_count,
                    "process": self.process_id,
                }
                self.join_node_id += 1
            else:
                continue


        # Find the initial node
        start_node = next((node for node in nodes.values() if node.type == 'initial'), None)
        if not start_node:
            raise ValueError("Activity diagrams must have exactly one start node")
        if not start_node.next_nodes or len(start_node.next_nodes or []) != 1:
            raise ValueError("An initial node must have exactly one outgoing edge")
        
        # Get the ID of the start node
        start_node_id = self.action_nodes[start_node.next_nodes[0]]['id']

        # Return the action nodes, join nodes and the start node ID
        return list(self.action_nodes.values()), list(self.join_nodes.values()), start_node_id

    def create_condition(self, node: Node) -> list[dict[str, Any]]:
        """Recursively create a condition for an action node. The input node should be of type 'action'"""
        rule: list[dict[str, Any]] = []
        if not node.next_nodes:
            return rule
        for next_node, condition in zip(node.next_nodes or [], node.conditions or []):
            next_node_obj = self.nodes.get(next_node)
            if not next_node_obj:
                raise ValueError(f"Something went wrong in the generation process, node {next_node} not found when creating a rule for it")
            next_value = (
                "END" if next_node_obj.type == "final"
                else self.action_nodes[next_node]['id']
                if next_node_obj.type == "action"
                else self.create_condition(next_node_obj)
            )

            if isinstance(next_value, list):
                if all(
                    isinstance(entry, dict) and len(entry.keys()) == 1 and(
                        isinstance(entry.get("next"), int) or entry.get("next") == "END"
                    ) for entry in next_value
                ):
                    next_value = (
                        [entry.get("next") for entry in next_value]
                        if len(next_value) > 1 
                        else (
                            next_value[0]["next"]
                            if len(next_value) == 1
                            else []
                        )
                    )

            # This is a branch consisting only of ignored nodes, we can skip it
            if isinstance(next_value, list) and not next_value:
                continue

            rule_entry = {"next": next_value}
            if next_node_obj.type == "join":
                rule_entry["check"] = self.join_nodes[next_node]['id']
            if condition and not condition.isElse:
                rule_entry["condition"] = condition._asdict()

            # Further flatten the next value if possible
            if isinstance(next_value, list) and len(next_value) == 1 and isinstance(next_value[0], dict) and set(rule_entry.keys()) & set(next_value[0].keys()) == set({"next"}):
                rule_entry = {
                    **rule_entry,
                    **next_value[0],
                }
            rule.append(rule_entry)
        return rule

    def create_rules(self) -> list[dict[str, Any]]:
        rules: list[dict[str, Any]] = []
        for uuid, action_node in self.action_nodes.items():
            node = self.nodes.get(uuid)
            if not node:
                raise ValueError(f"Something went wrong in the generation process, node {uuid} not found when creating a rule for it")
            rule = {
                "id": self.rules_id,
                "action_node": action_node['id'],
            }

            # Only add the condition if there are multiple next nodes and these nodes have either a condtion or check
            condition = self.create_condition(node)
            if len(condition) == 1 and len(condition[0].keys()) == 1:
                if isinstance(condition[0].get("next"), int) or condition[0].get("next") == "END":
                    rule['next'] = condition[0].get("next")
                elif isinstance(condition[0].get("next"), list) and all(
                    isinstance(entry, int) or entry == "END" for entry in condition[0]["next"]
                ):
                    rule['next'] = condition[0].get("next")
                else:
                    rule['condition'] = condition
            else:
                rule['condition'] = condition
            
            # Add the rule to the list of rules
            rules.append(rule)
            self.rules_id += 1
        return rules

    def get_workflow_engine_data(self) -> tuple[list[CronJob], dict[str, list[dict[str, Any]]]]:
        """Wrapper function that combines all steps to generate the data for the workflow engine"""
        # Parse the metadata into a more usable format
        diagrams = self.parse_metadata()

        # Create a process for each diagram
        process_entries = []
        rule_entries = []
        action_node_entries = []
        join_node_entries = []
        cron_jobs = []
        for diagram in diagrams:
            process = {
                "id": self.process_id,
                "name": diagram.name,
            }

            if diagram.cron_job:
                cron_jobs.append(diagram.cron_job)

            # Create action and join nodes as well as the start node
            action_nodes, join_nodes, start_node = self.create_relevant_nodes(diagram.nodes)
            
            # Add the action and join nodes to the process
            action_node_entries.extend(action_nodes)
            join_node_entries.extend(join_nodes)

            # Add the start node to the process
            process['start'] = start_node
            process_entries.append(process)

            # Create the rules connecting the action nodes
            rule_entries.extend(self.create_rules())

            # Reset the class attributes for the next process
            self.nodes = {}
            self.action_nodes = {}
            self.join_nodes = {}

            # Increment the process ID for the next process
            self.process_id += 1
        
        # Return the data for the workflow engine
        return (
            cron_jobs,
            {
                "processes": process_entries,
                "action_nodes": action_node_entries,
                "join_nodes": join_node_entries,
                "rules": rule_entries,
            }
        )



def _add_null_guards(code: str) -> str:
    """Add null guards after .first() assignments to prevent NoneType errors."""
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        match = re.match(r'^(\s+)(\w+)\s*=\s*\w+\.first\(\)\s*$', line)
        if match:
            indent = match.group(1)
            var_name = match.group(2)
            new_lines.append(f'{indent}if {var_name} is None:')
            new_lines.append(f'{indent}    return')
    return '\n'.join(new_lines)


def generate_data(system_id: str, project_name: str, metadata: str) -> list[CronJob]:
    OUTPUT_FILE_PATH = f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/workflow_engine/migrations/workflow_engine_data.json"
    CUSTOM_CODE_FILE_PATH = f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/workflow_engine/custom_code.py"

    # Parse the metadata and generate the workflow engine data
    parser = ActivityDiagramParser(json.loads(metadata))
    cron_jobs, workflow_engine_data = parser.get_workflow_engine_data()

    # Process custom code for action nodes
    custom_code_to_add = []
    for action_node in workflow_engine_data['action_nodes']:
        if action_node['custom_code']:
            # Generate a unique function name
            name_pattern = r"def\s+(\w+)\s*\("
            action_node_name = action_node['name'].replace(" ", "_")
            code = re.sub(name_pattern, r"def \1" + f"_{action_node_name}" + "(", action_node['custom_code'])
            code = _add_null_guards(code)
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
        return cron_jobs

    raise Exception(f"Failed to generate {project_name}/workflow_engine/migrations/workflow_engine_data.json")
