"""Prompts for resolving UML-to-interface semantic choices."""

import json


def build_resolve_interface_semantics_prompt(
    allowed: dict,
    actor_permissions: dict,
    model_graph: dict,
    workflow_intel: dict,
    decisions: list,
    interface_plan: dict,
) -> str:
    """Build prompt that resolves UML semantics into safe UI overrides.

    The LLM chooses layout/component, actor-to-model scope, plus the real
    activity target model and readonly/editable fields.
    django_service validates the returned JSON against the UML model graph
    before applying it.
    """
    model_fields = {
        model: [
            attr.get("name")
            for attr in (info.get("attributes") or [])
            if attr.get("name")
        ]
        for model, info in (model_graph or {}).items()
    }
    plan_summary = {
        "pages": interface_plan.get("pages", []),
        "sections": interface_plan.get("sections", []),
    }
    workflow_summary = [
        {
            "name": workflow.get("name"),
            "steps": [
                {
                    "action": step.get("action"),
                    "model": step.get("model"),
                    "actor": step.get("actor_node_name"),
                    "component_hint": step.get("component_hint"),
                }
                for step in (workflow.get("steps") or [])
                if step.get("action")
            ],
        }
        for workflow in (workflow_intel or {}).get("workflows", [])
    ]
    return (
        "Resolve UI semantic decisions for a UML-derived interface. Output JSON only.\n"
        "Do not invent models, fields, pages, or unsupported components.\n"
        "Use forms only when the user must enter/create/update data. Use detail/summary "
        "for review, consult, monitor, confirm, approve, discharge, analyze.\n\n"
        "For every workflow activity step listed in Workflow steps, describe behavior in workflow_steps JSON. "
        "Use the exact action names as keys. Do not omit workflow_steps for activity actions. Do not rely on "
        "the page title alone. For create_record, choose the created target_model, readonly_fields for "
        "context summary, editable_fields the user must enter, and context_binding for existing related "
        "objects that should come from the workflow context. For update_record, choose the existing "
        "target_model/context_model plus readonly_fields and editable_fields the actor should change. "
        "For select_existing, choose the target_model and readonly_fields to "
        "display in the selection list. For check and notify, choose readonly_fields that explain the "
        "decision/message. Never return all model fields unless the action truly requires them.\n\n"
        "Also resolve workflow semantics for activity steps. Use generic intents, not domain-specific code: "
        "select_existing for choosing an existing database object, check for a decision/validation step, "
        "create_record for creating a domain object, update_record for changing an existing context object, "
        "notify for a user/system notification, confirm for review/finish steps. For check steps, identify "
        "the context model, condition field, operator, threshold, true_next and false_next when possible. "
        "For update_record steps, do not auto-update values. Put fields such as status, stock_quantity, "
        "copies_available, approval_status, or assigned_doctor in editable_fields so the responsible actor "
        "can confirm the value before saving. Leave complex formulas out.\n\n"
        "Intent examples: Request Appointment, Apply For Loan, Submit Application, Book Visit usually "
        "create_record for the requested/application model. Schedule Appointment, Approve Application, "
        "Update Status usually update_record for an existing context object. Check Availability or Verify "
        "Eligibility usually check with a condition. Notify Applicant or Send Reminder usually notify.\n\n"
        "Also classify actor-to-model scope in actor_model_scopes. Use self_profile only when the actor "
        "is literally the person/entity represented by that model, such as Patient actor with Patient model "
        "or Applicant actor with Applicant model. Role actors such as Document Analyst, Loan Officer, "
        "Doctor, Admin, Reviewer, or Librarian should usually see collection or assigned records for their "
        "work models, not self_profile. For example Document Analyst + Document = collection, not self_profile.\n\n"
        f"Allowed values: {json.dumps(allowed)}\n"
        f"Actor permissions: {json.dumps(actor_permissions, ensure_ascii=False)}\n"
        f"Model graph fields: {json.dumps(model_fields, ensure_ascii=False)[:8000]}\n"
        f"Workflow steps: {json.dumps(workflow_summary, ensure_ascii=False)[:12000]}\n"
        f"Decisions: {json.dumps(decisions, ensure_ascii=False)}\n"
        f"Initial plan summary: {json.dumps(plan_summary, ensure_ascii=False)[:12000]}\n\n"
        "Schema:\n"
        "{\n"
        '  "actor_model_scopes": {"ModelName": "self_profile|collection|assigned|hidden"},\n'
        '  "models": {"ModelName": {"layout": "table|list|gallery|timeline|map", "component": "..." }},\n'
        '  "activity_steps": {"Exact action name": {"model": "ExistingModelName", "readonly_fields": ["existing_field"], "editable_fields": ["existing_field"], "layout": "form|detail|list", "component": "ObjectForm|DetailPanel|SummaryPanel|ObjectList", "role": "object_form|object_detail|object_collection"}},\n'
        '  "workflow_steps": {"Exact action name": {"intent": "select_existing|check|create_record|update_record|notify|confirm", "context_model": "ExistingModelName", "target_model": "ExistingModelName", "input_models": ["ExistingModelName"], "output_models": ["ExistingModelName"], "readonly_fields": ["existing_field"], "editable_fields": ["existing_field"], "context_binding": {"model": "ExistingModelName", "mode": "hidden|readonly|select"}, "condition": {"model": "ExistingModelName", "field": "existing_field", "operator": ">|>=|==|!=|<|<=", "threshold": "0"}, "true_next": "Exact next action name", "false_next": "Exact next action name"}}\n'
        "}\n"
    )
