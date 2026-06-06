"""Prompts for resolving UML-to-interface semantic choices."""

import json


def build_resolve_interface_semantics_prompt(
    allowed: dict,
    actor_permissions: dict,
    model_graph: dict,
    decisions: list,
    interface_plan: dict,
) -> str:
    """Build the Gemini prompt that resolves UML semantics into safe UI overrides.

    The LLM chooses layout/component plus the real activity target model,
    readonly/editable fields, and optional deterministic field updates.
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
    return (
        "Resolve UI semantic decisions for a UML-derived interface. Output JSON only.\n"
        "Do not invent models, fields, pages, or unsupported components.\n"
        "Use forms only when the user must enter/create/update data. Use detail/summary "
        "for review, consult, monitor, confirm, approve, discharge, analyze.\n\n"
        "For every workflow activity step, describe behavior in workflow_steps JSON. Do not rely on "
        "the page title alone. For create_record, choose the created target_model, readonly_fields for "
        "context summary, editable_fields the user must enter, and context_binding for existing related "
        "objects that should come from the workflow context. For update_record, choose the existing "
        "target_model/context_model plus readonly_fields, editable_fields, and field_updates when the "
        "change is deterministic. For select_existing, choose the target_model and readonly_fields to "
        "display in the selection list. For check and notify, choose readonly_fields that explain the "
        "decision/message. Never return all model fields unless the action truly requires them.\n\n"
        "Also resolve workflow semantics for activity steps. Use generic intents, not domain-specific code: "
        "select_existing for choosing an existing database object, check for a decision/validation step, "
        "create_record for creating a domain object, update_record for changing an existing context object, "
        "notify for a user/system notification, confirm for review/finish steps. For check steps, identify "
        "the context model, condition field, operator, threshold, true_next and false_next when possible. "
        "For update_record steps, prefer field_updates when the update is deterministic, e.g. decrement "
        "Product.stock_quantity or Book.copies_available by the quantity/order line. Use operations: "
        "set, increment, decrement. Use numeric value strings only; leave complex formulas out.\n\n"
        f"Allowed values: {json.dumps(allowed)}\n"
        f"Actor permissions: {json.dumps(actor_permissions, ensure_ascii=False)}\n"
        f"Model graph fields: {json.dumps(model_fields, ensure_ascii=False)[:8000]}\n"
        f"Decisions: {json.dumps(decisions, ensure_ascii=False)}\n"
        f"Initial plan summary: {json.dumps(plan_summary, ensure_ascii=False)[:12000]}\n\n"
        "Schema:\n"
        "{\n"
        '  "models": {"ModelName": {"layout": "table|list|gallery|calendar|timeline|map", "component": "..." }},\n'
        '  "activity_steps": {"Exact action name": {"model": "ExistingModelName", "readonly_fields": ["existing_field"], "editable_fields": ["existing_field"], "layout": "form|detail|list", "component": "ObjectForm|DetailPanel|SummaryPanel|ObjectList", "role": "object_form|object_detail|object_collection"}},\n'
        '  "workflow_steps": {"Exact action name": {"intent": "select_existing|check|create_record|update_record|notify|confirm", "context_model": "ExistingModelName", "target_model": "ExistingModelName", "input_models": ["ExistingModelName"], "output_models": ["ExistingModelName"], "readonly_fields": ["existing_field"], "editable_fields": ["existing_field"], "context_binding": {"model": "ExistingModelName", "mode": "hidden|readonly|select"}, "field_updates": [{"field": "existing_field", "operation": "set|increment|decrement", "value": "1"}], "condition": {"model": "ExistingModelName", "field": "existing_field", "operator": ">|>=|==|!=|<|<=", "threshold": "0"}, "true_next": "Exact next action name", "false_next": "Exact next action name"}}\n'
        "}\n"
    )
