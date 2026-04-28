import re

import pytest
from jinja2 import UndefinedError

from llm.prompts.diagram import (
    DIAGRAM_GENERATE_ATTRIBUTE,
    DIAGRAM_GENERATE_METHOD,
)
from llm.templates.registry import TEMPLATE_REGISTRY, get_template_path
from llm.templates.renderer import render_prompt


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sample_attribute_context():
    return {
        "django_version": "5.0.2",
        "classifier_metadata": '{"name": "Loan", "attributes": [{"name": "amount", "type": "int"}]}',
        "attribute_name": "risk_score",
        "attribute_return_type": "int",
        "attribute_description": "Calculate a simple risk score for the loan.",
    }


def sample_method_context():
    return {
        "django_version": "5.0.2",
        "classifier_metadata": '{"name": "Loan", "attributes": [{"name": "amount", "type": "int"}]}',
        "method_name": "approve",
        "method_description": "Approve the loan if it satisfies basic eligibility rules.",
    }


def sample_rag_context():
    context = sample_attribute_context()
    context["retrieved_context"] = {
        "target_class_name": "Loan",
        "target_class_attributes": [
            {"name": "amount", "type": "int"},
            {"name": "status", "type": "str"},
        ],
        "related_classes": [
            {
                "class_name": "Applicant",
                "relation_type": "association",
                "direction": "outgoing",
                "multiplicity_source": "1",
                "multiplicity_target": "1",
                "attributes": [
                    {"name": "income", "type": "int"},
                    {"name": "credit_score", "type": "int"},
                ],
                "methods": [],
            },
            {
                "class_name": "Collateral",
                "relation_type": "composition",
                "direction": "outgoing",
                "multiplicity_source": "1",
                "multiplicity_target": "*",
                "attributes": [
                    {"name": "value", "type": "int"},
                ],
                "methods": [],
            },
        ],
        "existing_methods": [
            {
                "class_name": "Applicant",
                "method_name": "is_eligible",
                "description": "Check whether the applicant is eligible.",
                "body": "",
                "return_type": "bool",
            }
        ],
    }
    return context


def test_all_registered_templates_resolve_to_existing_files():
    assert len(TEMPLATE_REGISTRY) == 8

    for prompt_name in TEMPLATE_REGISTRY:
        path = get_template_path(prompt_name)
        assert path.exists(), f"Missing template file for {prompt_name}: {path}"
        assert path.suffix == ".j2"


def test_diagram_attribute_template_renders_with_complete_context():
    rendered = render_prompt(
        "DIAGRAM_GENERATE_ATTRIBUTE",
        sample_attribute_context(),
    )

    assert rendered.strip()
    assert "risk_score" in rendered
    assert "Calculate a simple risk score" in rendered
    assert "Django 5.0.2" in rendered


def test_missing_context_key_raises_explicit_undefined_error():
    with pytest.raises(UndefinedError):
        render_prompt("DIAGRAM_GENERATE_ATTRIBUTE", {})


def test_rag_template_renders_related_classes_and_methods():
    rendered = render_prompt(
        "DIAGRAM_GENERATE_ATTRIBUTE_RAG",
        sample_rag_context(),
    )

    assert "Retrieved context" in rendered
    assert "Target class: Loan" in rendered
    assert "Applicant" in rendered
    assert "Collateral" in rendered
    assert "Applicant.is_eligible()" in rendered


def test_m01_attribute_template_is_functionally_equivalent_to_baseline_constant():
    context = sample_attribute_context()

    baseline = DIAGRAM_GENERATE_ATTRIBUTE.format(data=context)
    m01 = render_prompt("DIAGRAM_GENERATE_ATTRIBUTE", context)

    assert normalize(baseline) == normalize(m01)


def test_m01_method_template_is_functionally_equivalent_to_baseline_constant():
    context = sample_method_context()

    baseline = DIAGRAM_GENERATE_METHOD.format(data=context)
    m01 = render_prompt("DIAGRAM_GENERATE_METHOD", context)

    assert normalize(baseline) == normalize(m01)
