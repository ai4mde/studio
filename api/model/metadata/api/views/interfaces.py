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

# Constant for repeated error message
LLM_EMPTY_RESPONSE_MSG = "LLM returned empty response"

interfaces = Router()

# Store candidates temporarily (in production, use cache/session)
_candidates_cache: Dict[str, List[Dict]] = {}


class GeneratePagesRequest(Schema):
    requirements: str
    model: str = "llama-3.3-70b-versatile"


class GenerateCandidatesRequest(Schema):
    """Request for AI-driven multi-candidate UI generation."""
    requirements: str = ""
    model: str = "llama-3.3-70b-versatile"


class SelectCandidateRequest(Schema):
    """Select one of the generated UI candidates."""
    candidate_index: int  # 1, 2, or 3


class RefineInterfaceRequest(Schema):
    """Human-in-the-loop refinement request."""
    refinement_prompt: str
    model: str = "llama-3.3-70b-versatile"


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


def _get_system_metadata(system: System, actor_name: str = None):
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
    # Build association groups alongside composition
    association_groups = {}  # class_name -> [connected_class_names]
    for rel in system.relations.filter(
        data__type__in=['composition', 'association']
    ).select_related('source', 'target'):
        src_name = rel.source.data.get('name', '')
        tgt_name = rel.target.data.get('name', '')
        rel_type = rel.data.get('type', '')
        if rel_type == 'association':
            association_groups.setdefault(src_name, []).append(tgt_name)
            association_groups.setdefault(tgt_name, []).append(src_name)
    
    composition = result["composition_groups"]
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
        # Also expand via associations
        for cls_name, connected in association_groups.items():
            if cls_name in relevant_class_names:
                for c in connected:
                    if c not in relevant_class_names:
                        relevant_class_names.add(c)
                        changed = True
    
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
    try:
        response = llm_handler(
            "PROSE_REFINE_INTERFACE",
            body.model,
            input_data={
                "classes": metadata["classes_str"],
                "current_styling": current_styling,
                "current_pages": current_pages_str,
                "current_additional_pages": additional_pages_str,
                "refinement_prompt": body.refinement_prompt,
            },
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
                input_data={
                    "classes": metadata["classes_str"],
                    "current_styling": current_styling,
                    "current_pages": current_pages_str,
                    "current_additional_pages": additional_pages_str,
                    "refinement_prompt": body.refinement_prompt,
                },
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


__all__ = ["interfaces"]
