from typing import List, Optional, Dict, Any

from metadata.api.schemas import CreateInterface, ReadInterface, UpdateInterface
from metadata.models import System, Interface, Classifier
from django.http import HttpRequest
from metadata.api.views.defaulting import create_default_interface
from llm.handler import llm_handler
from prose.api.views.utils import parse_pages_response, parse_interface_candidates, parse_refined_interface
from metadata.api.views.preview_generator import generate_preview_html
from ninja import Router, Schema
from ninja.errors import HttpError
import json

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
        raise HttpError(503, "LLM returned empty response")
    
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


def _get_system_metadata(system: System):
    """Extract classes, use cases, and activities from system."""
    # Classes
    classes = list(system.classifiers.filter(data__type='class'))
    classes_str = ""
    classifier_data = []
    for cls in classes:
        name = cls.data.get('name', 'Unknown')
        attrs = cls.data.get('attributes', [])
        attr_names = [a['name'] for a in attrs]
        classes_str += f"- {name}: [{', '.join(attr_names)}]\n"
        classifier_data.append({
            'id': str(cls.id),
            'data': cls.data,
        })
    
    # Use cases
    use_cases = list(system.classifiers.filter(data__type='usecase'))
    usecases_str = ""
    for uc in use_cases:
        name = uc.data.get('name', 'Unknown')
        usecases_str += f"- {name}\n"
    
    # Activities (from activity diagrams if available)
    activities_str = "No activity workflows defined."
    # TODO: Extract activity model data when available
    
    return {
        "classes_str": classes_str or "No classes defined.",
        "usecases_str": usecases_str or "No use cases defined.",
        "activities_str": activities_str,
        "classifier_data": classifier_data,
    }


@interfaces.post("/{uuid:interface_id}/generate_candidates/")
def generate_candidates(request, interface_id, body: GenerateCandidatesRequest):
    """
    Generate 2-3 UI candidates using AI (OOUI principles).
    
    This is the AI-driven approach that generates multiple style options
    for the user to choose from.
    """
    interface = Interface.objects.get(id=interface_id)
    system = interface.system
    
    metadata = _get_system_metadata(system)
    
    if not metadata["classifier_data"]:
        raise HttpError(400, "No classes found in system. Create classes first.")
    
    # Call LLM for multi-candidate generation
    try:
        response = llm_handler(
            "PROSE_GENERATE_INTERFACE_CANDIDATES",
            body.model,
            input_data={
                "classes": metadata["classes_str"],
                "use_cases": metadata["usecases_str"],
                "activities": metadata["activities_str"],
                "requirements": body.requirements or "Generate a standard CRUD interface for all classes.",
            },
        )
    except Exception as e:
        raise HttpError(503, f"Failed to call LLM: {e}")
    
    if not response:
        raise HttpError(503, "LLM returned empty response")
    
    print("=" * 50)
    print("LLM CANDIDATES RESPONSE:")
    print(response)
    print("=" * 50)
    
    # Parse candidates
    candidates = parse_interface_candidates(response, metadata["classifier_data"])
    
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
    metadata = _get_system_metadata(system)
    
    # Call LLM for refinement
    try:
        response = llm_handler(
            "PROSE_REFINE_INTERFACE",
            body.model,
            input_data={
                "current_interface": json.dumps(interface.data, indent=2),
                "refinement_prompt": body.refinement_prompt,
            },
        )
    except Exception as e:
        raise HttpError(503, f"Failed to call LLM: {e}")
    
    if not response:
        raise HttpError(503, "LLM returned empty response")
    
    print("=" * 50)
    print("LLM REFINEMENT RESPONSE:")
    print(response)
    print("=" * 50)
    
    # Parse refined interface
    refined_data = parse_refined_interface(response, metadata["classifier_data"])
    
    if not refined_data:
        raise HttpError(422, "Failed to parse refined interface from LLM response")
    
    # Update refinement counter
    refined_data["_refinement_count"] = refinement_count + 1
    
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
