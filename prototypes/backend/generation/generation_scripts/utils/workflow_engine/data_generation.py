import re
from functools import cached_property
import json
import logging
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
        self.nodes: dict[str, Node] = {}
        self.action_nodes: dict[str, dict[str, Any]] = {}
        self.join_nodes: dict[str, dict[str, Any]] = {}
        self.process_id = 1
        self.action_node_id = 1
        self.join_node_id = 1
        self.rules_id = 1
        
    def _cls(self, node: dict[str, Any]) -> dict[str, Any]:
        cls = node.get("cls") or {}
        if isinstance(cls.get("data"), dict):
            return cls["data"]
        return cls

    def _node_type(self, node: dict[str, Any]) -> str | None:
        return self._cls(node).get("type")

    def _edge_data(self, edge: dict[str, Any]) -> dict[str, Any]:
        rel = edge.get("rel") or {}
        if isinstance(rel.get("data"), dict):
            return rel["data"]
        return rel

    @cached_property
    def class_attributes(self) -> dict[str, list[dict[str, Any]]]:
        result = {}
        for diagram in self.metadata.get("diagrams", []):
            if diagram.get("type") != "classes":
                continue
            for node in diagram.get("nodes", []):
                cls = self._cls(node)
                if cls.get("type") != "class":
                    continue
                name = cls.get("name")
                if name:
                    result[name] = cls.get("attributes") or []
        return result

    def _availability_condition_from_guard(self, guard: str) -> Condition | None:
        text = re.sub(r"[\[\]{}()]+", " ", str(guard or "")).strip().lower()
        if not text:
            return None

        unavailable_terms = ("unavailable", "not available", "out of stock", "no stock", "none available")
        available_terms = ("available", "in stock", "has stock", "stock available")
        if any(term in text for term in unavailable_terms):
            return Condition(True, None, None, None, None, None, None)
        if not any(term in text for term in available_terms):
            return None

        preferred_names = (
            "copies_available",
            "available_count",
            "quantity_available",
            "stock_quantity",
            "stock",
            "available",
            "capacity",
            "quantity",
        )
        for class_name, attrs in self.class_attributes.items():
            numeric_candidates = []
            for attr in attrs:
                attr_name = str(attr.get("name") or "")
                attr_type = str(attr.get("type") or "").lower()
                if attr_type not in {"int", "integer", "float", "decimal"}:
                    continue
                lowered = attr_name.lower()
                score = 0
                if lowered in preferred_names:
                    score += 4
                if any(term in lowered for term in ("available", "stock", "capacity", "quantity")):
                    score += 2
                if score:
                    numeric_candidates.append((score, attr_name, "int"))
            if numeric_candidates:
                numeric_candidates.sort(reverse=True)
                _, attr_name, attr_type = numeric_candidates[0]
                return Condition(False, ">", "0", None, attr_name, class_name, attr_type)
        return None

    def _edge_condition(self, edge_data: dict[str, Any]) -> Condition | None:
        condition = edge_data.get("condition")
        if condition:
            return Condition(
                isElse=condition.get('isElse'),
                operator=condition.get('operator'),
                threshold=condition.get('threshold'),
                aggregator=condition.get('aggregator'),
                target_attribute=condition.get('target_attribute'),
                target_class_name=condition.get('target_class_name'),
                target_attribute_type=condition.get('target_attribute_type'),
            )
        return self._availability_condition_from_guard(edge_data.get("guard") or "")

    def _edge_source(self, edge: dict[str, Any]) -> str | None:
        source = edge.get("source_ptr") or edge.get("source")
        if isinstance(source, dict):
            return source.get("id")
        return source

    def _edge_target(self, edge: dict[str, Any]) -> str | None:
        target = edge.get("target_ptr") or edge.get("target")
        if isinstance(target, dict):
            return target.get("id")
        return target

    def _actor_name(self, cls_data: dict[str, Any]) -> str | None:
        actor_ref = cls_data.get("actorNode")
        if actor_ref and self.actors.get(actor_ref):
            return self.actors[actor_ref]
        actor_name = cls_data.get("actorNodeName")
        return app_name_sanitization(actor_name) if actor_name else None

    
    @cached_property
    def actors(self) -> dict[str, str]:
        """Returns id of the actors associated with their name.
        Maps both diagram node id and cls_ptr (classifier id) so that
        activity actorNode fields referencing either format are resolved.
        """
        result = {}
        for usecase_diagram in filter(lambda diagram: diagram.get('type') == 'usecase', self.metadata.get('diagrams', [])):
            for actor_node in filter(lambda node: self._node_type(node) == 'actor', usecase_diagram.get('nodes', [])):
                actor_cls = self._cls(actor_node)
                name = app_name_sanitization(actor_cls.get('name', 'actor'))
                result[actor_node['id']] = name
                if actor_node.get('cls_ptr'):
                    result[actor_node['cls_ptr']] = name
        return result
    
    @cached_property
    def interface_map(self) -> dict[str, str]:
        """Map from the action node UUID or actor/page fallback key to an interface url."""
        interface_map = {}

        for interface in self.metadata.get('interfaces', []):
            interface_name = interface['value']['name']
            app_name = app_name_sanitization(interface_name)

            for page in interface['value']['data'].get('pages', []):
                page_type = page.get('type') or {}
                if page_type.get('value') != 'activity':
                    continue
                
                page_name = page.get('name') or page.get('id') or ''
                url = (
                    f"/{app_name}"
                    f"/render_{app_name}_"
                    f"{page_name_sanitization(page_name)}"
                )
                action = page.get('action') or {}
                if isinstance(action, dict) and action.get('value'):
                    interface_map[str(action['value'])] = url
                page_key = page_name_sanitization(page_name).lower()
                interface_map[f"{app_name}:{page_key}"] = url
                if isinstance(action, dict) and action.get('label'):
                    action_key = page_name_sanitization(action.get('label')).lower()
                    interface_map[f"{app_name}:{action_key}"] = url

        return interface_map

    def _get_incoming_edges_count(self, edges: list[dict[str, Any]], target_id: str) -> int:
        """Get the number of incoming edges for a node"""
        return sum(
            1 for _ in filter(lambda edge: self._edge_target(edge) == target_id, edges)
        )

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
                target_node=self._edge_target(edge),
                condition=self._edge_condition(self._edge_data(edge)),
            ) for edge in filter(lambda edge: self._edge_source(edge) == source_id and self._edge_target(edge), edges)
        ]

    def create_nodes(self, diagram: dict[str, Any], node_id: str) -> dict[str, Node] | None:
        """Create all nodes in the diagram recursively"""
        # Avoid revisiting nodes
        if node_id in self.nodes:
            return None
        
        # Find the current node and its outgoing edges as well as a count of incoming edges
        current_node = self.find_node(diagram['nodes'], node_id)
        outgoing_edges = self.find_edges(diagram['edges'], node_id)
        incoming_edges_count = self._get_incoming_edges_count(diagram['edges'], node_id)
        current_cls = self._cls(current_node)

        node = Node(
            id=current_node['id'],
            name=current_cls.get('name'),
            type=current_cls.get('type'),
            actor_node=self._actor_name(current_cls),
            next_nodes=[edge.target_node for edge in outgoing_edges],
            conditions=[edge.condition for edge in outgoing_edges],
            incoming_edges_count=incoming_edges_count,
            url=(
                self.interface_map.get(current_node['id'])
                or self.interface_map.get(
                    f"{self._actor_name(current_cls)}:{page_name_sanitization(current_cls.get('name') or '').lower()}"
                )
            ),
            custom_code=current_cls.get('customCode'),
        )
        self.nodes[node_id] = node

        # Recursively create nodes for the next nodes
        for edge in outgoing_edges:
            self.create_nodes(diagram, edge.target_node)
        return self.nodes

    def parse_activity_diagram(self, diagram: dict[str, Any]) -> tuple[CronJob | None, dict[str, Node] | None]:
        """Parse an activity diagram starting from the initial node"""
        self.nodes = {}

        start_node = list(filter(lambda node: self._node_type(node) == 'initial', diagram.get('nodes', [])))
        if len(start_node) != 1:
            raise ValueError("Activity diagrams must have exactly one start node")
        start_node = start_node[0]
        start_cls = self._cls(start_node)
        cron_job = CronJob(
            process_id=0, # Corrected later in get_workflow_engine_data
            schedule=start_cls.get('schedule', '')
        ) if start_cls.get('scheduled', False) and start_cls.get('schedule', '') else None
        self.create_nodes(diagram, start_node['id'])

        initial_node = self.nodes.get(start_node['id'])
        if initial_node and not initial_node.next_nodes:
            orphan_start_edges = [
                edge for edge in diagram.get('edges', [])
                if not self._edge_source(edge) and self._edge_target(edge)
            ]
            if orphan_start_edges:
                targets = [self._edge_target(edge) for edge in orphan_start_edges if self._edge_target(edge)]
                self.nodes[start_node['id']] = initial_node._replace(
                    next_nodes=targets,
                    conditions=[None for _ in targets],
                )
                for target in targets:
                    self.create_nodes(diagram, target)
        return cron_job, dict(self.nodes)

    def parse_metadata(self) -> list[Diagram]:
        """Parse all activity diagrams in the metadata"""
        diagrams = []
        for diagram in filter(lambda diagram: diagram.get('type') == 'activity', self.metadata.get('diagrams', [])):
            try:
                cron_job, nodes = self.parse_activity_diagram(diagram)
            except Exception as exc:
                logging.warning(
                    "Skipping activity diagram %s during workflow generation: %s",
                    diagram.get("name") or diagram.get("id") or "<unnamed>",
                    exc,
                )
                continue
            if nodes is None:
                continue
            diagrams.append(Diagram(
                name=diagram.get('name') or 'Activity Diagram',
                nodes=nodes,
                cron_job=cron_job
            ))
        return diagrams

    def _first_reachable_action_id(self, nodes: dict[str, Node], start_ids: list[str] | None) -> str | None:
        queue = list(start_ids or [])
        seen = set()
        while queue:
            node_id = queue.pop(0)
            if node_id in seen:
                continue
            seen.add(node_id)
            node = nodes.get(node_id)
            if not node:
                continue
            if node.type == "action":
                return node_id
            queue.extend(node.next_nodes or [])
        return None

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
        if not start_node.next_nodes:
            raise ValueError("An initial node must have at least one outgoing edge")

        first_action_id = self._first_reachable_action_id(nodes, start_node.next_nodes)
        if not first_action_id or first_action_id not in self.action_nodes:
            raise ValueError("An initial node must lead to at least one action node")

        # Get the ID of the first executable action node
        start_node_id = self.action_nodes[first_action_id]['id']

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
            if isinstance(next_value, list) and len(next_value) == 1 and set(rule_entry.keys()) & set(next_value[0].keys()) == set({"next"}):
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
            if not condition:
                # No reachable next nodes — treat as workflow end
                rule['next'] = "END"
            elif len(condition) == 1 and len(condition[0].keys()) == 1:
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
            self.nodes = diagram.nodes
            self.action_nodes = {}
            self.join_nodes = {}
        
            process = {
                "id": self.process_id,
                "name": diagram.name,
            }

            if diagram.cron_job:
                cron_jobs.append(
                    CronJob(
                        process_id=self.process_id,
                        schedule=diagram.cron_job.schedule
                    )
                )

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
