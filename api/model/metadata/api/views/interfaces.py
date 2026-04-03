from typing import List, Optional, Dict, Any

from metadata.api.schemas import CreateInterface, ReadInterface, UpdateInterface
from metadata.models import System, Interface, Classifier, Relation
from diagram.models import Node
from django.http import HttpRequest
from metadata.api.views.defaulting import create_default_interface
from llm.handler import llm_handler
from prose.api.views.utils import parse_pages_response, parse_interface_candidates, parse_refined_interface
from metadata.api.views.preview_generator import generate_preview_html
from ninja import Router, Schema
from ninja.errors import HttpError
import json
import re


# Constants
LLM_EMPTY_RESPONSE_MSG = "LLM returned empty response"
LLM_MODEL_NAME = "gpt-4o"

interfaces = Router()

# Store candidates temporarily (in production, use cache/session)
_candidates_cache: Dict[str, List[Dict]] = {}


class GeneratePagesRequest(Schema):
    requirements: str
    model: str = LLM_MODEL_NAME


class GenerateCandidatesRequest(Schema):
    """Request for AI-driven multi-candidate UI generation."""
    requirements: str = ""
    model: str = LLM_MODEL_NAME


class SelectCandidateRequest(Schema):
    """Select one of the generated UI candidates."""
    candidate_index: int  # 1, 2, or 3


class RefineInterfaceRequest(Schema):
    """Human-in-the-loop refinement request."""
    refinement_prompt: str
    model: str = LLM_MODEL_NAME


@interfaces.get("/", response=List[ReadInterface])
def list_interfaces(request, system: Optional[str] = None):
    qs = None
    if system:
        qs = Interface.objects.filter(system=system).order_by('id')
    else:
        qs = Interface.objects.all()
    return qs


@interfaces.get("/{uuid:id}/", response=ReadInterface)
def read_interface(request, id):
    return Interface.objects.get(id=id)


@interfaces.post("/", response=ReadInterface)
def create_interface(request, interface: CreateInterface):
    return Interface.objects.create(
        name=interface.name,
        description=interface.description,
        system=System.objects.get(pk=interface.system),
        actor=Classifier.objects.get(pk=interface.actor),
        data=interface.data
    )


@interfaces.post("/default", response=List[ReadInterface])
def create_default_interfaces(request, system_id: str):
    system = System.objects.get(pk=system_id)
    if not system:
        return []
    
    actors = system.classifiers.filter(data__type='actor')

    out = []
    for actor in actors:
        interface = create_default_interface(system, actor)
        out.append(interface)
    
    return out


@interfaces.put("/{uuid:id}/", response=bool)
def update_interface(request, id, interface: UpdateInterface):
    try: 
        Interface.objects.filter(id=id).update(name=interface.name,
                                               description=interface.description,
                                               system=interface.system, 
                                               data=interface.data)
    except Interface.DoesNotExist:
        return False
    return True


@interfaces.delete("/{uuid:interface_id}", response=bool)
def delete_interface(request, interface_id):
    try:
        Interface.objects.filter(id=interface_id).delete()
    except Interface.DoesNotExist:
        return False
    return True


@interfaces.post("/{uuid:interface_id}/generate_pages/", response=ReadInterface)
def generate_pages(request, interface_id, body: GeneratePagesRequest):
    """
    Generate UI pages for an interface using LLM based on OOUI principles.
    
    The LLM will create pages that bind to classes in the system,
    following Object-Oriented User Interface patterns.
    """
    interface = Interface.objects.get(id=interface_id)
    system = interface.system
    
    # Get all classes in the system
    classifiers = list(system.classifiers.filter(data__type='class'))
    if not classifiers:
        raise HttpError(400, "No classes found in system. Create classes first.")
    
    # Format classes for the prompt
    classes_str = ""
    classifier_data = []
    for cls in classifiers:
        name = cls.data.get('name', 'Unknown')
        attrs = cls.data.get('attributes', [])
        attr_names = [a['name'] for a in attrs]
        classes_str += f"- {name}: [{', '.join(attr_names)}]\n"
        classifier_data.append({
            'id': str(cls.id),
            'data': cls.data,
        })
    
    # Call LLM
    try:
        response = llm_handler(
            "PROSE_GENERATE_PAGES",
            body.model,
            input_data={
                "requirements": body.requirements,
                "classes": classes_str,
            },
        )
    except Exception as e:
        raise HttpError(503, f"Failed to call LLM: {e}")
    
    if not response:
           raise HttpError(503, LLM_EMPTY_RESPONSE_MSG)
    
    # Debug: print LLM response
    print("=" * 50)
    print("LLM RESPONSE:")
    print(response)
    print("=" * 50)
    print("CLASSIFIERS:")
    print(classifier_data)
    print("=" * 50)
    
    # Parse response
    parsed_data = parse_pages_response(response, classifier_data)
    
    # Debug: print parsed data
    print("PARSED DATA:")
    print(parsed_data)
    print("=" * 50)
    
    if not parsed_data or "pages" not in parsed_data:
        raise HttpError(422, "Failed to parse LLM response into pages")
    
    # Update interface data
    interface.data = parsed_data
    interface.save()
    
    return interface


def _get_system_metadata_full(system: System, actor_name: str = None):
    """Extract classes, use cases, activities, and relationships from system (unfiltered)."""
    def parse_classes(classes):
        classes_str = ""
        classifier_data = []
        class_id_to_name = {}
        for cls in classes:
            name = cls.data.get('name', 'Unknown')
            attrs = cls.data.get('attributes', [])
            attr_details = []
            for a in attrs:
                attr_type = a.get('type', 'str')
                attr_name = a['name']
                is_derived = a.get('derived', False)
                if is_derived:
                    attr_details.append(f"{attr_name}(derived:{attr_type})")
                else:
                    attr_details.append(f"{attr_name}:{attr_type}")
            classes_str += f"- {name}: [{', '.join(attr_details)}]\n"
            classifier_data.append({'id': str(cls.id), 'data': cls.data})
            class_id_to_name[str(cls.id)] = name
        return classes_str, classifier_data, class_id_to_name

    def parse_relationships(relations):
        relationships_str = ""
        composition_groups = {}
        for rel in relations:
            source_name = rel.source.data.get('name', '?')
            target_name = rel.target.data.get('name', '?')
            rel_type = rel.data.get('type', 'association')
            mult = rel.data.get('multiplicity', {})
            src_mult = mult.get('source', '*') if mult else '*'
            tgt_mult = mult.get('target', '*') if mult else '*'
            relationships_str += f"- {source_name} --[{rel_type}]--> {target_name} ({src_mult}..{tgt_mult})\n"
            if rel_type == 'composition':
                parent = source_name
                child = target_name
                if parent not in composition_groups:
                    composition_groups[parent] = []
                composition_groups[parent].append(child)
        if not relationships_str:
            relationships_str = "No relationships defined."
        return relationships_str, composition_groups

    def parse_usecases(actors, use_cases, uc_relations, actor_name):
        actor_usecases = {}
        for rel in uc_relations:
            src_name = rel.source.data.get('name', '')
            tgt_name = rel.target.data.get('name', '')
            src_type = rel.source.data.get('type', '')
            tgt_type = rel.target.data.get('type', '')
            if src_type == 'actor' and tgt_type == 'usecase':
                actor_usecases.setdefault(src_name, []).append(tgt_name)
            elif tgt_type == 'actor' and src_type == 'usecase':
                actor_usecases.setdefault(tgt_name, []).append(src_name)
        usecases_str = ""
        if actor_name:
            actors_to_show = [a for a in actors if a.data.get('name', '') == actor_name]
            other_actors = [a for a in actors if a.data.get('name', '') != actor_name]
        else:
            actors_to_show = actors
            other_actors = []
        for actor in actors_to_show:
            a_name = actor.data.get('name', 'Unknown')
            actor_ucs = actor_usecases.get(a_name, [])
            if actor_ucs:
                usecases_str += f"THIS ACTOR '{a_name}' can perform:\n"
                for uc_name in actor_ucs:
                    uc_data = next((uc.data for uc in use_cases if uc.data.get('name') == uc_name), {})
                    precondition = uc_data.get('precondition', '')
                    postcondition = uc_data.get('postcondition', '')
                    usecases_str += f"  → {uc_name}"
                    if precondition:
                        usecases_str += f" [pre: {precondition}]"
                    if postcondition:
                        usecases_str += f" [post: {postcondition}]"
                    usecases_str += "\n"
            else:
                usecases_str += f"THIS ACTOR '{a_name}' (no use cases linked)\n"
        if other_actors:
            usecases_str += "\nOTHER ACTORS (for context - attributes owned by these actors should be readonly or hidden):\n"
            for actor in other_actors:
                a_name = actor.data.get('name', 'Unknown')
                actor_ucs = actor_usecases.get(a_name, [])
                if actor_ucs:
                    usecases_str += f"  {a_name}: {', '.join(actor_ucs)}\n"
        if not actor_name:
            linked_ucs = set(uc for ucs in actor_usecases.values() for uc in ucs)
            for uc in use_cases:
                uc_name = uc.data.get('name', '')
                if uc_name not in linked_ucs:
                    usecases_str += f"  - {uc_name} (not linked to an actor)\n"
        return usecases_str

    def parse_activities(swimlanes, actions, actor_name, class_id_to_name):
        swimlane_info = {}
        for sw in swimlanes:
            sw_name = sw.data.get('name', '')
            sw_actor = sw.data.get('actorNodeName', '') or sw.data.get('name', '')
            swimlane_info[str(sw.id)] = sw_actor
            swimlane_info[sw_name] = sw_actor
        activity_actions = []
        ui_tasks = []
        auto_tasks = []
        for action in actions:
            action_name = action.data.get('name', 'Unknown')
            is_automatic = action.data.get('isAutomatic', False)
            action_actor = action.data.get('actorNodeName', '')
            if not action_actor and action.data.get('actorNode'):
                try:
                    node = Node.objects.get(id=action.data['actorNode'])
                    action_actor = node.cls.data.get('name', '') if node.cls else ''
                except Node.DoesNotExist:
                    action_actor = ''
            if actor_name and action_actor and action_actor != actor_name:
                continue
            action_classes = action.data.get('classes', {})
            input_classes = action_classes.get('input', []) if isinstance(action_classes, dict) else []
            output_classes = action_classes.get('output', []) if isinstance(action_classes, dict) else []
            input_names = [class_id_to_name.get(cid, cid) for cid in input_classes]
            output_names = [class_id_to_name.get(cid, cid) for cid in output_classes]
            action_info = {
                'id': str(action.id),
                'name': action_name,
                'actor': action_actor,
                'is_automatic': is_automatic,
                'input_classes': input_names,
                'output_classes': output_names,
            }
            activity_actions.append(action_info)
            if is_automatic:
                auto_tasks.append(f"  - [AUTO] {action_name} (actor: {action_actor}, uses: {', '.join(input_names + output_names) or 'none'})")
            else:
                ui_tasks.append(f"  - [UI] {action_name} (actor: {action_actor}, uses: {', '.join(input_names + output_names) or 'none'})")
        if ui_tasks or auto_tasks:
            activities_str = "UI Tasks (require interface pages):\n"
            activities_str += '\n'.join(ui_tasks) if ui_tasks else "  (none)\n"
            activities_str += "\nAutomatic Tasks (no interface needed):\n"
            activities_str += '\n'.join(auto_tasks) if auto_tasks else "  (none)\n"
        else:
            activities_str = "No activity workflows defined."
        return activities_str, activity_actions

    # Main function logic
    classes = list(system.classifiers.filter(data__type='class'))
    relations = list(system.relations.filter(data__type__in=['composition', 'association', 'generalization']).select_related('source', 'target'))
    actors = list(system.classifiers.filter(data__type='actor'))
    use_cases = list(system.classifiers.filter(data__type='usecase'))
    uc_relations = list(system.relations.filter(data__type='interaction'))
    swimlanes = list(system.classifiers.filter(data__type='swimlane'))
    actions = list(system.classifiers.filter(data__type='action'))

    classes_str, classifier_data, class_id_to_name = parse_classes(classes)
    relationships_str, composition_groups = parse_relationships(relations)
    usecases_str = parse_usecases(actors, use_cases, uc_relations, actor_name)
    activities_str, activity_actions = parse_activities(swimlanes, actions, actor_name, class_id_to_name)

    return {
        "classes_str": classes_str or "No classes defined.",
        "relationships_str": relationships_str,
        "usecases_str": usecases_str or "No use cases defined.",
        "activities_str": activities_str,
        "classifier_data": classifier_data,
        "composition_groups": composition_groups,
        "activity_actions": activity_actions,
        "relevant_class_ids": None,
    }
# Helper functions for system metadata parsing
def parse_classes(classes):
    classes_str = ""
    classifier_data = []
    class_id_to_name = {}
    for cls in classes:
        name = cls.data.get('name', 'Unknown')
        attrs = cls.data.get('attributes', [])
        attr_details = []
        for a in attrs:
            attr_type = a.get('type', 'str')
            attr_name = a['name']
            is_derived = a.get('derived', False)
            if is_derived:
                attr_details.append(f"{attr_name}(derived:{attr_type})")
            else:
                attr_details.append(f"{attr_name}:{attr_type}")
        classes_str += f"- {name}: [{', '.join(attr_details)}]\n"
        classifier_data.append({'id': str(cls.id), 'data': cls.data})
        class_id_to_name[str(cls.id)] = name
    return classes_str, classifier_data, class_id_to_name

def parse_relationships(relations):
    relationships_str = ""
    composition_groups = {}
    for rel in relations:
        source_name = rel.source.data.get('name', '?')
        target_name = rel.target.data.get('name', '?')
        rel_type = rel.data.get('type', 'association')
        mult = rel.data.get('multiplicity', {})
        src_mult = mult.get('source', '*') if mult else '*'
        tgt_mult = mult.get('target', '*') if mult else '*'
        relationships_str += f"- {source_name} --[{rel_type}]--> {target_name} ({src_mult}..{tgt_mult})\n"
        if rel_type == 'composition':
            parent = source_name
            child = target_name
            if parent not in composition_groups:
                composition_groups[parent] = []
            composition_groups[parent].append(child)
    if not relationships_str:
        relationships_str = "No relationships defined."
    return relationships_str, composition_groups

def parse_usecases(actors, use_cases, uc_relations, actor_name):
    actor_usecases = {}
    for rel in uc_relations:
        src_name = rel.source.data.get('name', '')
        tgt_name = rel.target.data.get('name', '')
        src_type = rel.source.data.get('type', '')
        tgt_type = rel.target.data.get('type', '')
        if src_type == 'actor' and tgt_type == 'usecase':
            actor_usecases.setdefault(src_name, []).append(tgt_name)
        elif tgt_type == 'actor' and src_type == 'usecase':
            actor_usecases.setdefault(tgt_name, []).append(src_name)
    usecases_str = ""
    if actor_name:
        actors_to_show = [a for a in actors if a.data.get('name', '') == actor_name]
        other_actors = [a for a in actors if a.data.get('name', '') != actor_name]
    else:
        actors_to_show = actors
        other_actors = []
    for actor in actors_to_show:
        a_name = actor.data.get('name', 'Unknown')
        actor_ucs = actor_usecases.get(a_name, [])
        if actor_ucs:
            usecases_str += f"THIS ACTOR '{a_name}' can perform:\n"
            for uc_name in actor_ucs:
                uc_data = next((uc.data for uc in use_cases if uc.data.get('name') == uc_name), {})
                precondition = uc_data.get('precondition', '')
                postcondition = uc_data.get('postcondition', '')
                usecases_str += f"  → {uc_name}"
                if precondition:
                    usecases_str += f" [pre: {precondition}]"
                if postcondition:
                    usecases_str += f" [post: {postcondition}]"
                usecases_str += "\n"
        else:
            usecases_str += f"THIS ACTOR '{a_name}' (no use cases linked)\n"
    if other_actors:
        usecases_str += "\nOTHER ACTORS (for context - attributes owned by these actors should be readonly or hidden):\n"
        for actor in other_actors:
            a_name = actor.data.get('name', 'Unknown')
            actor_ucs = actor_usecases.get(a_name, [])
            if actor_ucs:
                usecases_str += f"  {a_name}: {', '.join(actor_ucs)}\n"
    if not actor_name:
        linked_ucs = set(uc for ucs in actor_usecases.values() for uc in ucs)
        for uc in use_cases:
            uc_name = uc.data.get('name', '')
            if uc_name not in linked_ucs:
                usecases_str += f"  - {uc_name} (not linked to an actor)\n"
    return usecases_str

def parse_activities(swimlanes, actions, actor_name, class_id_to_name):
    swimlane_info = {}
    for sw in swimlanes:
        sw_name = sw.data.get('name', '')
        sw_actor = sw.data.get('actorNodeName', '') or sw.data.get('name', '')
        swimlane_info[str(sw.id)] = sw_actor
        swimlane_info[sw_name] = sw_actor

    def process_action(action, actor_name, class_id_to_name):
        action_name = action.data.get('name', 'Unknown')
        is_automatic = action.data.get('isAutomatic', False)
        action_actor = action.data.get('actorNodeName', '')
        if not action_actor and action.data.get('actorNode'):
            try:
                node = Node.objects.get(id=action.data['actorNode'])
                action_actor = node.cls.data.get('name', '') if node.cls else ''
            except Node.DoesNotExist:
                action_actor = ''
        if actor_name and action_actor and action_actor != actor_name:
            return None, None
        action_classes = action.data.get('classes', {})
        input_classes = action_classes.get('input', []) if isinstance(action_classes, dict) else []
        output_classes = action_classes.get('output', []) if isinstance(action_classes, dict) else []
        input_names = [class_id_to_name.get(cid, cid) for cid in input_classes]
        output_names = [class_id_to_name.get(cid, cid) for cid in output_classes]
        action_info = {
            'id': str(action.id),
            'name': action_name,
            'actor': action_actor,
            'is_automatic': is_automatic,
            'input_classes': input_names,
            'output_classes': output_names,
        }
        task_str = f"  - [{'AUTO' if is_automatic else 'UI'}] {action_name} (actor: {action_actor}, uses: {', '.join(input_names + output_names) or 'none'})"
        return action_info, task_str

    activity_actions = []
    ui_tasks = []
    auto_tasks = []
    for action in actions:
        action_info, task_str = process_action(action, actor_name, class_id_to_name)
        if action_info is None:
            continue
        activity_actions.append(action_info)
        if action_info['is_automatic']:
            auto_tasks.append(task_str)
        else:
            ui_tasks.append(task_str)

    if ui_tasks or auto_tasks:
        activities_str = "UI Tasks (require interface pages):\n"
        activities_str += '\n'.join(ui_tasks) if ui_tasks else "  (none)\n"
        activities_str += "\nAutomatic Tasks (no interface needed):\n"
        activities_str += '\n'.join(auto_tasks) if auto_tasks else "  (none)\n"
    else:
        activities_str = "No activity workflows defined."
    return activities_str, activity_actions


def _get_system_metadata(system: System, actor_name: str = None):
    def expand_relevant_classes(relevant_class_names, composition, association_groups):
        changed = True
        while changed:
            changed = False
            for parent, children in composition.items():
                if parent in relevant_class_names:
                    for child in children:
                        if child not in relevant_class_names:
                            relevant_class_names.add(child)
                            changed = True
                for child in children:
                    if child in relevant_class_names and parent not in relevant_class_names:
                        relevant_class_names.add(parent)
                        changed = True
            for cls_name, connected in association_groups.items():
                if cls_name in relevant_class_names:
                    for c in connected:
                        if c not in relevant_class_names:
                            relevant_class_names.add(c)
                            changed = True
        return relevant_class_names
    """Extract classes, use cases, activities, and relationships from system.
    If actor_name is provided, filter use cases and activities to only those relevant to that actor."""
    result = _get_system_metadata_full(system, actor_name)
    
    if not actor_name:
        return result  # no filtering needed
    
    # ── Compute relevant classes for this actor ──
    relevant_class_names = set()
    class_name_to_id = {}
    class_id_to_name = {}
    for cls in result["classifier_data"]:
        name = cls['data'].get('name', '')
        cid = cls['id']
        class_name_to_id[name] = cid
        class_name_to_id[name.lower()] = cid
        class_id_to_name[cid] = name
    
    # 1. From activity actions: input/output classes
    for action in result["activity_actions"]:
        for cls_name in action.get('input_classes', []) + action.get('output_classes', []):
            relevant_class_names.add(cls_name)
    
    # 2. From use cases: match use case names to class names (like defaulting.py)
    # Pre-compute actor's use cases from interaction relations
    actor_ucs = set()
    for rel in system.relations.filter(data__type='interaction').select_related('source', 'target'):
        src = rel.source.data
        tgt = rel.target.data
        if src.get('type') == 'actor' and src.get('name') == actor_name:
            actor_ucs.add(tgt.get('name', '').lower())
        elif tgt.get('type') == 'actor' and tgt.get('name') == actor_name:
            actor_ucs.add(src.get('name', '').lower())
    
    for uc in system.classifiers.filter(data__type='usecase'):
        uc_name = uc.data.get('name', '').lower()
        if uc_name in actor_ucs:
            uc_words = set(uc_name.split())
            # Match class by splitting CamelCase into words
            for cls in result["classifier_data"]:
                cls_name = cls['data'].get('name', '')
                cls_words = {w.lower() for w in re.findall(r'[A-Z][a-z]*|[a-z]+', cls_name) if len(w) > 2}
                if cls_words & uc_words:
                    relevant_class_names.add(cls_name)
    
    # 3. Expand with composition and association-connected classes
    association_groups = {}
    for rel in system.relations.filter(data__type__in=['composition', 'association']).select_related('source', 'target'):
        src_name = rel.source.data.get('name', '')
        tgt_name = rel.target.data.get('name', '')
        rel_type = rel.data.get('type', '')
        if rel_type == 'association':
            association_groups.setdefault(src_name, []).append(tgt_name)
            association_groups.setdefault(tgt_name, []).append(src_name)
    composition = result["composition_groups"]
    relevant_class_names = expand_relevant_classes(relevant_class_names, composition, association_groups)

    # If no relevant classes found (e.g. no use cases/activities reference classes), keep all
    if not relevant_class_names:
        return result

    # Filter classifier_data and rebuild classes_str
    filtered_classifiers = []
    filtered_classes_str = ""
    for cls in result["classifier_data"]:
        name = cls['data'].get('name', '')
        if name in relevant_class_names:
            filtered_classifiers.append(cls)
            attrs = cls['data'].get('attributes', [])
            attr_names = [a['name'] for a in attrs]
            filtered_classes_str += f"- {name}: [{', '.join(attr_names)}]\n"

    result["classifier_data"] = filtered_classifiers
    result["classes_str"] = filtered_classes_str or "No classes defined."
    result["relevant_class_ids"] = {class_name_to_id.get(n) for n in relevant_class_names if class_name_to_id.get(n)}

    return result


@interfaces.post("/{uuid:interface_id}/generate_candidates/")
def generate_candidates(request, interface_id, body: GenerateCandidatesRequest):
    """
    Generate 2-3 UI candidates using AI (OOUI principles).
    
    This is the AI-driven approach that generates multiple style options
    for the user to choose from.
    """
    interface = Interface.objects.get(id=interface_id)
    system = interface.system
    
    # Get actor name to filter activities/use cases for this interface
    iface_actor_name = None
    if interface.actor:
        iface_actor_name = interface.actor.data.get('name')
    
    metadata = _get_system_metadata(system, actor_name=iface_actor_name)
    
    if not metadata["classifier_data"]:
        raise HttpError(400, "No classes found in system. Create classes first.")
    
    # Call LLM for multi-candidate generation
    try:
        response = llm_handler(
            "PROSE_GENERATE_INTERFACE_CANDIDATES",
            body.model,
            input_data={
                "actor_name": iface_actor_name or "Unknown Actor",
                "classes": metadata["classes_str"],
                "relationships": metadata["relationships_str"],
                "use_cases": metadata["usecases_str"],
                "activities": metadata["activities_str"],
                "requirements": body.requirements or "Generate a standard CRUD interface for all classes.",
            },
        )
    except Exception as e:
        raise HttpError(503, f"Failed to call LLM: {e}")
    
    if not response:
           raise HttpError(503, LLM_EMPTY_RESPONSE_MSG)
    
    print("=" * 50)
    print("LLM CANDIDATES RESPONSE:")
    print(response)
    print("=" * 50)
    
    # Parse candidates with extra context for OOUI grouping and activity pages
    candidates = parse_interface_candidates(
        response, 
        metadata["classifier_data"],
        composition_groups=metadata.get("composition_groups", {}),
        activity_actions=metadata.get("activity_actions", []),
    )
    
    if not candidates:
        raise HttpError(422, "Failed to parse any UI candidates from LLM response")
    
    # Cache candidates for later selection
    cache_key = str(interface_id)
    _candidates_cache[cache_key] = candidates
    
    # Return preview of candidates with HTML preview
    preview = []
    for c in candidates:
        # Generate static HTML preview for this candidate
        html_preview = generate_preview_html(
            c, 
            name=c.get("style_name", "UI Preview")
        )
        
        preview.append({
            "candidate_index": c.get("candidate_index"),
            "style_name": c.get("style_name"),
            "num_pages": len(c.get("pages", [])),
            "num_sections": len(c.get("sections", [])),
            "styling": c.get("styling", {}),
            "html_preview": html_preview,
        })
    
    return {
        "interface_id": str(interface_id),
        "candidates_count": len(candidates),
        "candidates": preview,
        "message": "Use /select_candidate/ to choose one and apply it.",
    }


@interfaces.post("/{uuid:interface_id}/select_candidate/", response=ReadInterface)
def select_candidate(request, interface_id, body: SelectCandidateRequest):
    """
    Select one of the generated UI candidates and apply it to the interface.
    """
    cache_key = str(interface_id)
    
    if cache_key not in _candidates_cache:
        raise HttpError(400, "No candidates found. Call /generate_candidates/ first.")
    
    candidates = _candidates_cache[cache_key]
    
    # Find matching candidate
    selected = None
    for c in candidates:
        if c.get("candidate_index") == body.candidate_index:
            selected = c
            break
    
    if not selected:
        raise HttpError(400, f"Candidate {body.candidate_index} not found. Available: {[c.get('candidate_index') for c in candidates]}")
    
    # Apply to interface
    interface = Interface.objects.get(id=interface_id)
    
    # Remove temporary fields before saving
    interface_data = {k: v for k, v in selected.items() if k not in ["candidate_index", "style_name"]}
    
    # Initialize refinement counter
    interface_data["_refinement_count"] = 0
    
    interface.data = interface_data
    interface.save()
    
    # Clean up cache
    del _candidates_cache[cache_key]
    
    return interface


@interfaces.post("/{uuid:interface_id}/refine/", response=ReadInterface)
def refine_interface(request, interface_id, body: RefineInterfaceRequest):
    """
    Human-in-the-loop refinement: modify the selected UI based on user feedback.
    
    Maximum 3 refinements allowed per interface.
    Example prompts:
    - "Change the navigation bar to blue"
    - "Put order details on the right side"
    - "Use a dark theme with rounded corners"
    """
    interface = Interface.objects.get(id=interface_id)
    system = interface.system
    
    if not interface.data:
        raise HttpError(400, "No interface data found. Generate or select a UI first.")
    
    # Check refinement limit
    refinement_count = interface.data.get("_refinement_count", 0)
    if refinement_count >= 3:
        raise HttpError(400, "Maximum 3 refinements reached. Please edit the code manually for further changes.")
    
    # Get classifier data for validation
    iface_actor_name = None
    if interface.actor:
        iface_actor_name = interface.actor.data.get('name')
    metadata = _get_system_metadata(system, actor_name=iface_actor_name)
    
    # Build a human-readable summary of current state for LLM
    current_data = interface.data
    
    # Extract current styling
    current_styling = json.dumps(current_data.get('styling', {}), indent=2)
    
    def get_page_summary(sections):
        current_pages_list = []
        for section in sections:
            model_name = section.get('model_name', '')
            page_name = section.get('name', '')
            ops = section.get('operations', {})
            attrs = [a['name'] for a in section.get('attributes', [])]
            if model_name:
                current_pages_list.append(f"- {page_name} (model: {model_name}, ops: {ops}, attrs: {attrs})")
        return '\n'.join(current_pages_list) if current_pages_list else 'Default CRUD for all models'

    def get_additional_page_summary(sections):
        additional_pages_list = []
        for section in sections:
            if not section.get('model_name') and section.get('page_type'):
                additional_pages_list.append(f"- {section.get('name', '')} (type: {section.get('page_type', 'custom')})")
        return '\n'.join(additional_pages_list) if additional_pages_list else 'None'

    current_pages_str = get_page_summary(current_data.get('sections', []))
    additional_pages_str = get_additional_page_summary(current_data.get('sections', []))
    
    # Call LLM for refinement
    refine_input = {
        "actor_name": iface_actor_name or "Unknown Actor",
        "classes": metadata["classes_str"],
        "relationships": metadata["relationships_str"],
        "use_cases": metadata["usecases_str"],
        "activities": metadata["activities_str"],
        "current_styling": current_styling,
        "current_pages": current_pages_str,
        "current_additional_pages": additional_pages_str,
        "refinement_prompt": body.refinement_prompt,
    }
    try:
        response = llm_handler(
            "PROSE_REFINE_INTERFACE",
            body.model,
            input_data=refine_input,
        )
    except Exception as e:
        raise HttpError(503, f"Failed to call LLM: {e}")
    
    if not response:
           raise HttpError(503, LLM_EMPTY_RESPONSE_MSG)
    
    print("=" * 50)
    print("LLM REFINEMENT RESPONSE:")
    print(response)
    print("=" * 50)
    
    # Parse refined interface
    refined_data = parse_refined_interface(
        response, 
        metadata["classifier_data"],
        composition_groups=metadata.get("composition_groups", {}),
        activity_actions=metadata.get("activity_actions", []),
    )
    
    if not refined_data:
        # Retry once - LLM responses can be inconsistent
        print("[refine] First parse failed, retrying LLM call...")
        try:
            response = llm_handler(
                "PROSE_REFINE_INTERFACE",
                body.model,
                input_data=refine_input,
            )
            refined_data = parse_refined_interface(
                response, 
                metadata["classifier_data"],
                composition_groups=metadata.get("composition_groups", {}),
                activity_actions=metadata.get("activity_actions", []),
            )
        except Exception:
            pass
    
    if not refined_data:
        raise HttpError(422, "Failed to parse refined interface from LLM response. Try again or rephrase your request.")
    
    # Update refinement counter
    refined_data["_refinement_count"] = refinement_count + 1
    
    # Preserve HTML preview capability
    refined_data["_last_refinement"] = body.refinement_prompt
    
    # Save
    interface.data = refined_data
    interface.save()
    
    return interface


@interfaces.get("/{uuid:interface_id}/refinement_status/")
def refinement_status(request, interface_id):
    """
    Check how many refinements have been used for this interface.
    """
    interface = Interface.objects.get(id=interface_id)
    
    count = interface.data.get("_refinement_count", 0) if interface.data else 0
    
    return {
        "interface_id": str(interface_id),
        "refinements_used": count,
        "refinements_remaining": max(0, 3 - count),
        "can_refine": count < 3,
    }


class GenerateLayoutRequest(Schema):
    """Request for LLM-generated custom layout HTML."""
    prompt: str
    model: str = LLM_MODEL_NAME
    background_color: str = "#FFFFFF"
    text_color: str = "#000000"
    accent_color: str = "#3B82F6"
    radius: int = 8


@interfaces.post("/{uuid:interface_id}/generate_layout/")
def generate_layout(request, interface_id, body: GenerateLayoutRequest):
    """
    Generate a free-form layout HTML from a natural language prompt.
    Stores the result in interface.data.styling.customHtml.
    """
    if not body.prompt.strip():
        raise HttpError(400, "Prompt cannot be empty.")

    try:
        html = llm_handler(
            "PROSE_GENERATE_CUSTOM_LAYOUT",
            body.model,
            input_data={
                "prompt": body.prompt,
                "background_color": body.background_color,
                "text_color": body.text_color,
                "accent_color": body.accent_color,
                "radius": body.radius,
            },
        )
    except Exception as e:
        raise HttpError(503, f"Failed to call LLM: {e}")

    if not html:
        raise HttpError(503, LLM_EMPTY_RESPONSE_MSG)

    # Strip any accidental markdown fences
    html = re.sub(r'^```[a-z]*\s*', '', html.strip())
    html = re.sub(r'```\s*$', '', html)

    # Persist into the interface's styling.customHtml
    interface = Interface.objects.get(id=interface_id)
    data = dict(interface.data) if interface.data else {}
    styling = dict(data.get("styling", {}))
    styling["layoutType"] = "custom"
    styling["customHtml"] = html.strip()
    data["styling"] = styling
    interface.data = data
    interface.save()

    return {"custom_html": html.strip()}


class GenerateStyleRequest(Schema):
    """Request for LLM-generated complete design style."""
    prompt: str
    model: str = LLM_MODEL_NAME


class GenerateOOUIPageRequest(Schema):
    """Request for fully free OOUI page template generation."""
    prompt: str
    model: str = LLM_MODEL_NAME


def _build_model_context(interface_data: dict) -> str:
    """Build a concise model-context string from interface.data for the OOUI page prompt."""
    sections = interface_data.get("sections", [])
    if not sections:
        return "No models defined yet."
    lines = []
    for sec in sections:
        name = sec.get("model_name") or sec.get("name", "Unknown")
        attrs = sec.get("attributes", [])
        ops = sec.get("operations", {})
        attr_names = [a.get("name", "") for a in attrs if a.get("name")]
        ops_list = [k for k, v in ops.items() if v]
        lines.append(
            f"- {name}: fields=[{', '.join(attr_names)}], operations=[{', '.join(ops_list)}]"
        )
    return "\n".join(lines)


def _san(name: str) -> str:
    """Replicate generator.sh name sanitization to compute exact Django variable/URL names."""
    if not name:
        return "object"
    name = str(name).replace(' ', '_').replace('-', '_')
    while '__' in name:
        name = name.replace('__', '_')
    result = re.sub(r'[^a-zA-Z0-9_]', '', name)
    return result or 'object'


def _build_page_contexts(interface) -> list:
    """
    Pre-compute, for every page in the interface, the exact Django template variable names,
    URL names, field names, and operations. This lets the LLM write vanilla Django HTML
    without knowledge of Jinja2 or the generation pipeline.
    """
    data = interface.data or {}
    sections_by_id = {s["id"]: s for s in data.get("sections", [])}
    pages = data.get("pages", [])
    app_name = _san(interface.name)

    # Classifier lookup by ID for model name resolution
    cls_lookup = {}
    try:
        for c in interface.system.classifiers.all():
            cls_lookup[str(c.id)] = c
    except Exception:
        pass

    page_contexts = []
    for page_data in pages:
        page_name = _san(page_data.get("name", "page"))

        sections_out = []
        for sec_ref in page_data.get("sections", []):
            sec_id = sec_ref.get("value") if isinstance(sec_ref, dict) else sec_ref
            section = sections_by_id.get(str(sec_id))
            if not section:
                continue

            class_id = section.get("class")
            cls = cls_lookup.get(str(class_id)) if class_id else None
            cls_data = cls.data if cls else {}
            raw_model_name = (cls_data.get("name") or section.get("model_name") or section.get("name") or "Object")
            model_name = _san(raw_model_name)
            section_name = _san(section.get("name") or model_name)

            attrs = []
            for attr in section.get("attributes", []):
                a_name = _san(attr.get("name", ""))
                if not a_name:
                    continue
                a_type = attr.get("type", "str")
                enum_choices = []
                if a_type == "enum":
                    enum_val = attr.get("enum") or {}
                    enum_choices = enum_val.get("literals", []) if isinstance(enum_val, dict) else []
                attrs.append({
                    "name": a_name,
                    "type": a_type,
                    "derived": attr.get("derived", False),
                    "enum_choices": enum_choices,
                })

            ops = section.get("operations", {})
            sections_out.append({
                "display_name": section.get("name") or raw_model_name,
                "section_name": section_name,
                "model_name": model_name,
                "list_var": f"{model_name}_list",
                "obj_var": model_name,
                "attributes": attrs,
                "has_create": bool(ops.get("create", False)),
                "has_update": bool(ops.get("update", False)),
                "has_delete": bool(ops.get("delete", False)),
                "render_url": f"{app_name}:render_{app_name}_{page_name}",
                "create_url": f"{app_name}:{page_name}_{section_name}_create",
                "delete_url": f"{app_name}:{page_name}_{section_name}_delete",
                "detail_url": f"{app_name}:{model_name.lower()}_detail",
            })

        if sections_out:
            page_contexts.append({
                "page_name": page_name,
                "display_name": page_data.get("name", page_name),
                "app_name": app_name,
                "sections": sections_out,
            })

    return page_contexts


def _format_pages_spec(page_contexts: list) -> str:
    """Format page contexts into a human-readable spec string for the LLM prompt."""
    lines = []
    for pc in page_contexts:
        lines.append(f"\n{'='*60}")
        lines.append(f"PAGE: {pc['page_name']}  (label: \"{pc['display_name']}\")")
        lines.append(f"  Base template: {{% extends \"{pc['app_name']}_base.html\" %}}")
        lines.append(f"  Render URL:    {{% url '{pc['app_name']}:render_{pc['app_name']}_{pc['page_name']}' %}}")

        for sec in pc["sections"]:
            lines.append(f"\n  SECTION: {sec['display_name']}")
            lines.append(f"    Model: {sec['model_name']}")
            lines.append(f"    Loop over records:   {{% for {sec['obj_var']} in {sec['list_var']} %}}...{{% endfor %}}")
            lines.append(f"    Detail link:  {{% url '{sec['detail_url']}' {sec['obj_var']}.id %}}")

            if sec["attributes"]:
                lines.append("    Fields (access as {{ obj.field }}):")
                for a in sec["attributes"]:
                    t = a["type"]
                    extra = f"  choices: {a['enum_choices']}" if t == "enum" and a["enum_choices"] else ""
                    ro = "  [read-only]" if a["derived"] else ""
                    lines.append(f"      {{ {sec['obj_var']}.{a['name']} }}  — type: {t}{extra}{ro}")

            if sec["has_create"]:
                lines.append(f"    Create form:")
                lines.append(f"      Toggle ON:  GET {{% url '{sec['render_url']}' %}}?create_{sec['section_name']}=true")
                lines.append(f"      Check open: {{% if create_{sec['section_name']} %}}...{{% endif %}}")
                lines.append(f"      POST to:    {{% url '{sec['create_url']}' %}}")

            if sec["has_update"]:
                lines.append(f"    Edit button (GET param):")
                lines.append(f"      Send:  instance_id_{sec['model_name']}={{ {sec['obj_var']}.id }}")
                lines.append(f"      Check: {{% if {sec['obj_var']} == update_instance %}}  (show edit form){{% endif %}}")

            if sec["has_delete"]:
                lines.append(f"    Delete form:  POST to {{% url '{sec['delete_url']}' {sec['obj_var']}.id %}}")

    return "\n".join(lines)


@interfaces.post("/{uuid:interface_id}/generate_style/")
def generate_style(request, interface_id, body: GenerateStyleRequest):
    """
    Generate a complete design theme (colors, layout, font, CSS) from a natural language prompt.
    Stores the result in interface.data.styling and returns the updated styling fields.
    """
    if not body.prompt.strip():
        raise HttpError(400, "Prompt cannot be empty.")

    try:
        raw = llm_handler(
            "PROSE_GENERATE_STYLE",
            body.model,
            input_data={"prompt": body.prompt},
        )
    except Exception as e:
        raise HttpError(503, f"Failed to call LLM: {e}")

    if not raw:
        raise HttpError(503, LLM_EMPTY_RESPONSE_MSG)

    # Extract JSON between STYLE_START and STYLE_END markers
    match = re.search(r'STYLE_START\s*([\s\S]*?)\s*STYLE_END', raw)
    if not match:
        raise HttpError(503, "LLM response did not contain valid STYLE_START/STYLE_END markers.")

    try:
        style = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise HttpError(503, f"LLM returned invalid JSON: {e}")

    # Validate and sanitise fields
    allowed_layouts = {"sidebar", "topnav", "dashboard", "split", "wizard", "minimal", "cards", "tabs", "drawer", "custom"}
    layout_type = style.get("layout_type", "sidebar")
    if layout_type not in allowed_layouts:
        layout_type = "sidebar"

    allowed_display_modes = {"table", "cards", "list"}
    display_mode = style.get("display_mode", "table")
    if display_mode not in allowed_display_modes:
        display_mode = "table"

    result = {
        "accentColor":     style.get("accent_color", "#3B82F6"),
        "backgroundColor": style.get("background_color", "#FFFFFF"),
        "textColor":       style.get("text_color", "#000000"),
        "radius":          int(style.get("radius", 8)),
        "fontUrl":         style.get("font_url", ""),
        "layoutType":      layout_type,
        "displayMode":     display_mode,
        "customCss":       style.get("custom_css", ""),
    }

    # Persist into the interface's styling
    interface = Interface.objects.get(id=interface_id)
    data = dict(interface.data) if interface.data else {}
    styling = dict(data.get("styling", {}))
    styling.update({
        "accentColor":     result["accentColor"],
        "backgroundColor": result["backgroundColor"],
        "textColor":       result["textColor"],
        "radius":          result["radius"],
        "fontUrl":         result["fontUrl"],
        "layoutType":      result["layoutType"],
        "displayMode":     result["displayMode"],
        "customCss":       result["customCss"],
    })
    data["styling"] = styling
    interface.data = data
    interface.save()

    return result


@interfaces.post("/{uuid:interface_id}/generate_ooui_page/")
def generate_ooui_page(request, interface_id, body: GenerateOOUIPageRequest):
    """
    Generate per-page Django HTML templates from a designer prompt.
    Python pre-computes exact variable/URL names so the LLM writes plain Django HTML
    (no Jinja2 knowledge needed). Results stored as customDjangoTemplates in interface.data.
    """
    if not body.prompt.strip():
        raise HttpError(400, "Prompt cannot be empty.")

    interface = Interface.objects.get(id=interface_id)
    page_contexts = _build_page_contexts(interface)

    if not page_contexts:
        raise HttpError(400, "No pages defined on this interface yet. Generate pages first.")

    pages_spec = _format_pages_spec(page_contexts)

    try:
        raw = llm_handler(
            "PROSE_GENERATE_DJANGO_TEMPLATE",
            body.model,
            input_data={
                "pages_spec": pages_spec,
                "prompt": body.prompt,
            },
        )
    except Exception as e:
        raise HttpError(503, f"Failed to call LLM: {e}")

    if not raw:
        raise HttpError(503, LLM_EMPTY_RESPONSE_MSG)

    # Parse PAGE_START:name ... PAGE_END:name blocks
    templates = {}
    for match in re.finditer(r'PAGE_START:(\w+)\n([\s\S]*?)\nPAGE_END:\1', raw):
        page_name = match.group(1)
        html = match.group(2).strip()
        # Strip accidental markdown fences
        html = re.sub(r'^```[a-z]*\s*', '', html)
        html = re.sub(r'```\s*$', '', html).strip()
        templates[page_name] = html

    if not templates:
        raise HttpError(503, "LLM did not return any PAGE_START/PAGE_END blocks.")

    # Persist customDjangoTemplates to interface.data.styling
    data = dict(interface.data) if interface.data else {}
    styling = dict(data.get("styling", {}))
    styling["customDjangoTemplates"] = templates
    # Clear legacy Jinja2 field if present (new approach supersedes it)
    styling.pop("customPageJinja2", None)
    data["styling"] = styling
    interface.data = data
    interface.save()

    return {
        "pages_generated": list(templates.keys()),
        "count": len(templates),
        "templates": templates,
    }


__all__ = ["interfaces"]
