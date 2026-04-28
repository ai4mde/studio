import json

from django.core import serializers
from django.test import TestCase

from metadata.models import Classifier, Project, Relation, System
from llm.retrieval.domain_retriever import DomainRetriever
from llm.templates.renderer import render_prompt
from llm.prompts.diagram import DIAGRAM_GENERATE_ATTRIBUTE


def attr(name, type_="int", description=""):
    return {
        "name": name,
        "type": type_,
        "enum": None,
        "derived": False,
        "description": description,
        "body": None,
    }


def method(name, return_type="int", description="", body="return 1"):
    return {
        "name": name,
        "type": return_type,
        "description": description,
        "body": body,
    }


class DomainRetrieverSmokeTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="M02 Smoke Project",
            description="Project for testing domain-aware retrieval context.",
        )
        self.system = System.objects.create(
            project=self.project,
            name="Loan System",
            description="System for testing selective retrieval.",
        )

        self.order = Classifier.objects.create(
            project=self.project,
            system=self.system,
            data={
                "name": "Order",
                "type": "class",
                "attributes": [
                    attr("amount", "int", "Requested amount"),
                    attr("status", "str", "Order status"),
                ],
                "methods": [
                    method(
                        "calculate_total",
                        "int",
                        "Calculate order total",
                        "return self.amount",
                    )
                ],
            },
        )

        self.customer = Classifier.objects.create(
            project=self.project,
            system=self.system,
            data={
                "name": "Customer",
                "type": "class",
                "attributes": [
                    attr("income", "int", "Customer income"),
                ],
                "methods": [
                    method(
                        "is_eligible",
                        "bool",
                        "Check eligibility",
                        "return self.income > 0",
                    )
                ],
            },
        )

        self.product = Classifier.objects.create(
            project=self.project,
            system=self.system,
            data={
                "name": "Product",
                "type": "class",
                "attributes": [
                    attr("price", "int", "Product price"),
                ],
                "methods": [],
            },
        )

        Relation.objects.create(
            system=self.system,
            source=self.order,
            target=self.customer,
            data={
                "type": "association",
                "multiplicity": {
                    "source": "1",
                    "target": "1",
                },
            },
        )

        Relation.objects.create(
            system=self.system,
            source=self.order,
            target=self.product,
            data={
                "type": "composition",
                "multiplicity": {
                    "source": "1",
                    "target": "*",
                },
            },
        )

    def test_m02_retrieves_target_related_classes_relations_and_methods(self):
        context = DomainRetriever(self.system).retrieve(self.order)

        assert context.target_class_name == "Order"
        assert [a["name"] for a in context.target_class_attributes] == [
            "amount",
            "status",
        ]

        related_by_name = {related.class_name: related for related in context.related_classes}

        assert set(related_by_name.keys()) == {"Customer", "Product"}

        customer = related_by_name["Customer"]
        assert customer.direction == "outgoing"
        assert customer.relation_type == "association"
        assert customer.multiplicity_source == "1"
        assert customer.multiplicity_target == "1"
        assert customer.attributes[0]["name"] == "income"

        product = related_by_name["Product"]
        assert product.direction == "outgoing"
        assert product.relation_type == "composition"
        assert product.multiplicity_source == "1"
        assert product.multiplicity_target == "*"
        assert product.attributes[0]["name"] == "price"

        method_keys = {
            (existing.class_name, existing.method_name)
            for existing in context.existing_methods
        }
        assert ("Order", "calculate_total") in method_keys
        assert ("Customer", "is_eligible") in method_keys

    def test_m02_ignores_unrelated_classes_and_other_systems(self):
        for index in range(20):
            Classifier.objects.create(
                project=self.project,
                system=self.system,
                data={
                    "name": f"Unrelated{index}",
                    "type": "class",
                    "attributes": [attr(f"field_{index}")],
                    "methods": [],
                },
            )

        other_system = System.objects.create(
            project=self.project,
            name="Other System",
            description="Should not leak into retrieval context.",
        )
        external = Classifier.objects.create(
            project=self.project,
            system=other_system,
            data={
                "name": "ExternalCustomer",
                "type": "class",
                "attributes": [attr("external_score")],
                "methods": [],
            },
        )
        Relation.objects.create(
            system=other_system,
            source=external,
            target=external,
            data={
                "type": "association",
                "multiplicity": {
                    "source": "1",
                    "target": "1",
                },
            },
        )

        context = DomainRetriever(self.system).retrieve(self.order)

        assert context.target_class_name == "Order"
        assert len(context.related_classes) == 2
        assert {related.class_name for related in context.related_classes} == {
            "Customer",
            "Product",
        }

    def test_m02_rag_context_is_smaller_than_baseline_full_diagram_dump(self):
        unrelated_classes = []
        for index in range(20):
            unrelated = Classifier.objects.create(
                project=self.project,
                system=self.system,
                data={
                    "name": f"Unrelated{index}",
                    "type": "class",
                    "attributes": [
                        attr(
                            f"field_{index}",
                            "str",
                            "Noise field not relevant to Order generation.",
                        )
                    ],
                    "methods": [],
                },
            )
            unrelated_classes.append(unrelated)

        other_system = System.objects.create(
            project=self.project,
            name="Other System",
            description="Should not leak into retrieval context.",
        )
        other_system_class = Classifier.objects.create(
            project=self.project,
            system=other_system,
            data={
                "name": "OtherSystemClass",
                "type": "class",
                "attributes": [
                    attr("external_score", "int", "External score from another system.")
                ],
                "methods": [],
            },
        )

        # Retrieve after noise has been created, so the test proves that M02 filters it out.
        context = DomainRetriever(self.system).retrieve(self.order)
        rag_context = context.to_template_dict()

        # Simulate the old full-diagram baseline for the current system.
        # This intentionally includes unrelated classes in the same system.
        baseline_full_system_dump = serializers.serialize(
            "json",
            [
                self.order,
                self.customer,
                self.product,
                *unrelated_classes,
            ],
        )

        rag_context_dump = json.dumps(rag_context, indent=2)

        rag_prompt = render_prompt(
            "DIAGRAM_GENERATE_ATTRIBUTE_RAG",
            {
                "django_version": "5.0.2",
                "attribute_name": "risk_score",
                "attribute_type": "int",
                "attribute_return_type": "int",
                "attribute_description": "Calculate a risk score using customer income and product price.",
                "classifier_metadata": json.dumps(self.order.data),
                "retrieved_context": rag_context,
            },
        )

        # Positive evidence: relevant 1-hop domain context is present.
        assert "Order" in rag_prompt
        assert "Customer" in rag_prompt
        assert "Product" in rag_prompt

        # Negative evidence: unrelated same-system classes are excluded.
        assert "Unrelated0" not in rag_prompt
        assert "Unrelated19" not in rag_prompt

        # Negative evidence: classes from another system are excluded.
        assert "OtherSystemClass" not in rag_prompt
        assert other_system_class.data["name"] not in rag_context_dump

        # Baseline sanity check: the simulated full-system dump really contains noise.
        assert "Unrelated0" in baseline_full_system_dump
        assert "Unrelated19" in baseline_full_system_dump

        # Main size evidence: retrieved context payload is smaller than full-system dump.
        assert len(rag_context_dump) < len(baseline_full_system_dump)