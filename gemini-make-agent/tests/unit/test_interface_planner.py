from app.interface_planner import generate_interface_plan
from app.uml_extractor import _action_component, extract_use_case_diagram


def test_usecase_association_edges_assign_actor_permissions():
    classifiers = {
        "actor_doctor": {"type": "actor", "name": "Doctor"},
        "uc_manage": {
            "type": "usecase",
            "name": "Manage Appointments",
            "classes": ["model_appointment", "model_patient"],
        },
        "model_appointment": {"type": "class", "name": "Appointment"},
        "model_patient": {"type": "class", "name": "Patient"},
    }
    relations = {
        "rel_uses": {
            "source": "actor_doctor",
            "target": "uc_manage",
            "data": {"type": "association", "label": "uses"},
        }
    }
    diagrams = [{
        "type": "usecase",
        "nodes": [{"id": "n_actor", "cls": "actor_doctor"}, {"id": "n_uc", "cls": "uc_manage"}],
        "edges": [{"rel": "rel_uses"}],
    }]

    actor_intel = extract_use_case_diagram(
        classifiers,
        relations,
        diagrams,
        "actor_doctor",
        "Doctor",
        {"Appointment", "Patient"},
        set(),
    )

    assert actor_intel["target_permissions"]["Appointment"] == ["read", "update"]
    assert actor_intel["target_permissions"]["Patient"] == ["read"]
    assert actor_intel["target_use_cases"][0]["name"] == "Manage Appointments"


def test_usecase_infers_models_from_linked_action_classes():
    classifiers = {
        "actor_applicant": {"type": "actor", "name": "Applicant"},
        "uc_fill": {
            "type": "usecase",
            "name": "Fill In Loan Application",
            "classes": [],
            "actions": ["action_fill"],
        },
        "action_fill": {
            "type": "action",
            "name": "Fill In Loan Application",
            "classes": ["model_loan"],
        },
        "model_loan": {"type": "class", "name": "LoanApplication"},
    }
    relations = {
        "rel_uses": {
            "source": "actor_applicant",
            "target": "uc_fill",
            "data": {"type": "association", "label": "uses"},
        }
    }
    diagrams = [{
        "type": "usecase",
        "nodes": [{"id": "n_actor", "cls": "actor_applicant"}, {"id": "n_uc", "cls": "uc_fill"}],
        "edges": [{"rel": "rel_uses"}],
    }]

    actor_intel = extract_use_case_diagram(
        classifiers,
        relations,
        diagrams,
        "actor_applicant",
        "Applicant",
        {"LoanApplication"},
        set(),
    )

    assert actor_intel["target_permissions"]["LoanApplication"] == ["read"]
    assert actor_intel["target_use_cases"][0]["primary_model"] == "LoanApplication"


def test_workflow_use_case_keeps_model_workspace():
    plan = generate_interface_plan({
        "model_graph": {
            "Patient": {
                "attributes": [
                    {"name": "patient_id"},
                    {"name": "first_name"},
                    {"name": "last_name"},
                    {"name": "phone"},
                ],
                "layout_score": {"table": 0.8, "list": 0.4, "gallery": 0.2},
                "compositions_owned": [],
                "associations": [],
            }
        },
        "actor_intel": {
            "target_permissions": {"Patient": ["create", "read", "update"]},
            "target_use_cases": [{
                "name": "Request Admission",
                "primary_model": "Patient",
                "page_role": "workflow_entry",
                "permissions": ["create", "read", "update"],
                "has_workflow": True,
            }],
        },
        "workflow_intel": {
            "workflows": [{
                "name": "Admission",
                "is_multi_step": True,
                "steps": [
                    {"action": "Request Admission", "model": "Patient", "component_hint": "ObjectForm"},
                    {"action": "Review Patient", "model": "Patient", "component_hint": "DetailPanel"},
                    {"action": "Discharge Patient", "model": "Patient", "component_hint": "DetailPanel"},
                ],
            }]
        },
        "actor_name": "Doctor",
    })

    pages = {page["id"]: page for page in plan["pages"]}
    assert "patient" in pages
    assert pages["patient"]["type"]["value"] != "activity" if isinstance(pages["patient"].get("type"), dict) else True
    assert any(page.get("type", {}).get("value") == "activity" for page in plan["pages"] if isinstance(page.get("type"), dict))
    assert any(sec["page_id"] == "patient" and sec["layout"] == "detail" for sec in plan["sections"])


def test_activity_review_consult_monitor_are_not_forms_by_default():
    assert _action_component("Review Appointment") == "DetailPanel"
    assert _action_component("Consult Patient") == "DetailPanel"
    assert _action_component("Monitor Admission") == "DetailPanel"


def test_collection_layouts_use_model_semantics_not_all_tables():
    base_info = {
        "layout_score": {"table": 0.85, "list": 0.35, "gallery": 0.1},
        "attributes": [{"name": "first_name"}, {"name": "last_name"}, {"name": "phone"}],
    }
    plan = generate_interface_plan({
        "model_graph": {
            "Doctor": dict(base_info),
            "Appointment": {
                "layout_score": {"table": 0.7, "calendar": 0.9, "list": 0.35},
                "attributes": [{"name": "scheduled_date"}, {"name": "start_time"}, {"name": "status"}],
            },
            "Admission": {
                "layout_score": {"table": 0.7, "timeline": 0.8, "list": 0.75},
                "attributes": [{"name": "status"}, {"name": "start_date"}, {"name": "end_date"}],
            },
        },
        "actor_intel": {
            "target_permissions": {
                "Doctor": ["read"],
                "Appointment": ["read"],
                "Admission": ["read"],
            },
            "target_use_cases": [],
        },
        "workflow_intel": {"workflows": []},
        "actor_name": "Patient",
    })

    sections_by_model = {sec["primary_model"]: sec for sec in plan["sections"] if sec["role"] == "object_collection"}
    assert sections_by_model["Doctor"]["component"] == "PersonCardGrid"
    assert sections_by_model["Appointment"]["component"] == "CalendarView"
    assert sections_by_model["Admission"]["component"] == "TimelineList"


def test_loan_application_app_gets_mixed_pages_and_activity_components():
    uml = {
        "model_graph": {
            "Applicant": {
                "layout_score": {"table": 0.7, "gallery": 0.1, "list": 0.35},
                "attributes": [
                    {"name": "first_name"},
                    {"name": "last_name"},
                    {"name": "email"},
                    {"name": "phone"},
                ],
                "compositions_owned": [],
                "associations": [],
            },
            "LoanApplication": {
                "layout_score": {"table": 0.85, "timeline": 0.8, "list": 0.75},
                "attributes": [
                    {"name": "amount"},
                    {"name": "reason"},
                    {"name": "status"},
                    {"name": "risk"},
                    {"name": "submitted_date"},
                ],
                "compositions_owned": [
                    {"model": "Document", "cardinality": "1-many"},
                    {"model": "ApplicationNote", "cardinality": "1-many"},
                ],
                "associations": [],
            },
            "Document": {
                "layout_score": {"table": 0.7, "list": 0.35},
                "attributes": [{"name": "file_content"}, {"name": "upload_date"}, {"name": "valid"}],
                "compositions_owned": [],
                "associations": [],
            },
            "ApplicationNote": {
                "layout_score": {"table": 0.4, "list": 0.35},
                "attributes": [{"name": "comment"}, {"name": "created_at"}],
                "compositions_owned": [],
                "associations": [],
            },
        },
        "actor_intel": {
            "target_permissions": {
                "Applicant": ["create", "read", "update"],
                "LoanApplication": ["create", "read", "update"],
                "Document": ["create", "read"],
                "ApplicationNote": ["read"],
            },
            "target_use_cases": [
                {
                    "name": "Fill in application",
                    "primary_model": "LoanApplication",
                    "page_role": "workflow_entry",
                    "permissions": ["create", "read", "update"],
                    "has_workflow": True,
                },
            ],
        },
        "workflow_intel": {
            "workflows": [{
                "name": "Loan application flow",
                "is_multi_step": True,
                "steps": [
                    {"action": "Fill in application", "model": "LoanApplication", "component_hint": "ObjectForm", "actor_node_name": "Applicant"},
                    {"action": "Analyze documents", "model": "Document", "component_hint": "DetailPanel", "actor_node_name": "Document analyst"},
                    {"action": "Assess risk", "model": "LoanApplication", "component_hint": "DetailPanel", "actor_node_name": "Loan officer"},
                    {"action": "Approve loan", "model": "LoanApplication", "component_hint": "DetailPanel", "actor_node_name": "Loan officer"},
                ],
            }]
        },
        "actor_name": "Applicant",
    }

    applicant_plan = generate_interface_plan(uml)
    collection_sections = {
        sec["primary_model"]: sec
        for sec in applicant_plan["sections"]
        if sec["role"] == "object_collection"
    }
    assert collection_sections["Applicant"]["component"] == "PersonCardGrid"
    assert collection_sections["LoanApplication"]["component"] == "TimelineList"
    fill_section = next(sec for sec in applicant_plan["sections"] if sec["name"] == "Fill in application")
    assert fill_section["component"] == "ObjectForm"

    analyst_uml = {**uml, "actor_name": "Document analyst"}
    analyst_plan = generate_interface_plan(analyst_uml)
    analyze_section = next(sec for sec in analyst_plan["sections"] if sec["name"] == "Analyze documents")
    assert analyze_section["layout"] == "detail"
    assert analyze_section["component"] == "DetailPanel"

    officer_uml = {**uml, "actor_name": "Loan officer"}
    officer_plan = generate_interface_plan(officer_uml)
    approve_section = next(sec for sec in officer_plan["sections"] if sec["name"] == "Approve loan")
    assert approve_section["layout"] == "detail"
    assert approve_section["component"] == "SummaryPanel"


def test_workflow_use_case_adds_tracking_collection_page():
    plan = generate_interface_plan({
        "model_graph": {
            "LoanApplication": {
                "layout_score": {"table": 0.85, "timeline": 0.8, "list": 0.75},
                "attributes": [{"name": "status"}, {"name": "risk"}, {"name": "submitted_date"}],
                "compositions_owned": [],
                "associations": [],
            },
        },
        "actor_intel": {
            "target_permissions": {"LoanApplication": ["create", "read", "update"]},
            "target_use_cases": [{
                "name": "Fill in application",
                "primary_model": "LoanApplication",
                "page_role": "workflow_entry",
                "permissions": ["create", "read", "update"],
                "has_workflow": True,
            }],
        },
        "workflow_intel": {"workflows": []},
        "actor_name": "Applicant",
    })

    pages = {page["id"]: page for page in plan["pages"]}
    assert "loanapplication" in pages
    assert "loanapplications" in pages
    loan_collection = next(
        sec for sec in plan["sections"]
        if sec["page_id"] == "loanapplications" and sec["role"] == "object_collection"
    )
    assert loan_collection["component"] == "TimelineList"


def test_activity_step_semantic_override_can_choose_summary_panel():
    uml = {
        "model_graph": {
            "Admission": {
                "attributes": [{"name": "status"}, {"name": "risk_level"}, {"name": "notes"}],
                "layout_score": {"table": 0.8},
                "compositions_owned": [],
                "associations": [],
            }
        },
        "actor_intel": {
            "target_permissions": {"Admission": ["read", "update"]},
            "target_use_cases": [],
        },
        "workflow_intel": {
            "workflows": [{
                "name": "Admission",
                "is_multi_step": True,
                "steps": [
                    {"action": "Request Admission", "model": "Admission", "component_hint": "ObjectForm"},
                    {"action": "Monitor Admission", "model": "Admission", "component_hint": "ObjectForm"},
                    {"action": "Discharge Patient", "model": "Admission", "component_hint": "DetailPanel"},
                ],
            }]
        },
        "actor_name": "Doctor",
    }
    plan = generate_interface_plan(uml, {
        "activity_steps": {
            "Monitor Admission": {
                "layout": "detail",
                "component": "SummaryPanel",
                "role": "object_detail",
            }
        }
    })
    monitor_section = next(sec for sec in plan["sections"] if sec["name"] == "Monitor Admission")
    assert monitor_section["layout"] == "detail"
    assert monitor_section["component"] == "SummaryPanel"
