
import json

from django.core.exceptions import ValidationError
from django.test import TestCase

from diagram.models import Diagram, Edge, Node
from generator.services.metadata import build_generator_metadata
from metadata.models import (
    Classifier,
    Interface,
    Page,
    PageSection,
    Project,
    Relation,
    SectionComponent,
    System,
)


class GeneratorMetadataTests(TestCase):
    def setUp(self):
        project = Project.objects.create(name="Test Project")
        self.system = System.objects.create(
            project=project,
            name="Test System",
        )
        self.other_system = System.objects.create(
            project=project,
            name="Other System",
        )

    def test_build_generator_metadata(self):
        # Class diagram with two classifiers and a relation
        source = Classifier.create(
            system_id=self.system.id,
            classifier_type="class",
            data={"name": "Customer"},
        )
        target = Classifier.create(
            system_id=self.system.id,
            classifier_type="class",
            data={"name": "Order"},
        )

        diagram = Diagram.objects.create(
            system=self.system,
            name="Class Diagram",
            type="class",
        )

        Node.objects.create(diagram=diagram, classifier=source)
        Node.objects.create(diagram=diagram, classifier=target)

        relation = Relation.create(
            system_id=self.system.id,
            source_id=source.id,
            target_id=target.id,
            relation_type="association",
            data={
                "multiplicity": {
                    "source_lower": 1,
                    "source_upper": 1,
                    "target_lower": 0,
                    "target_upper": None,
                },
            },
        )
        Edge.objects.create(diagram=diagram, relation=relation)

        # Interface with a page and section
        interface = Interface.objects.create(
            system=self.system,
            name="Customer Interface",
            description="Customer-facing pages",
        )

        page = Page.objects.create(
            interface=interface,
            name="Orders",
        )
        section = SectionComponent.objects.create(
            interface=interface,
            name="Order Section",
            uml_class=target.data,
        )
        PageSection.objects.create(
            page=page,
            section=section,
            order=0,
        )

        # An unselected interface should not be included
        Interface.objects.create(
            system=self.system,
            name="Admin Interface",
            description="Admin pages",
        )

        # A diagram from another system should not be included
        Diagram.objects.create(
            system=self.other_system,
            name="Unrelated Diagram",
            type="class",
        )

        metadata = build_generator_metadata(
            system=self.system,
            interface_ids=[interface.id],
            use_authentication=True,
        )

        data = metadata.model_dump(mode="json")

        # Correct top-level generator structure
        self.assertEqual(
            set(data),
            {"diagrams", "interfaces", "use_authentication"},
        )
        self.assertTrue(data["use_authentication"])
        json.dumps(data)  # Must be JSON serializable

        # Complete diagrams for the selected system
        self.assertEqual(len(data["diagrams"]), 1)
        self.assertEqual(data["diagrams"][0]["name"], "Class Diagram")
        self.assertEqual(len(data["diagrams"][0]["nodes"]), 2)
        self.assertEqual(len(data["diagrams"][0]["edges"]), 1)
        self.assertEqual(
            data["diagrams"][0]["edges"][0]["relation"]["type"],
            "association",
        )

        # Only the selected interface, including its contents
        self.assertEqual(len(data["interfaces"]), 1)
        generated_interface = data["interfaces"][0]

        self.assertEqual(generated_interface["name"], "Customer Interface")
        self.assertEqual(len(generated_interface["pages"]), 1)
        self.assertEqual(len(generated_interface["sections"]), 1)

        self.assertEqual(
            generated_interface["pages"][0]["page_sections"][0]["section"],
            str(section.id),
        )

    def test_reject_interface_from_another_system(self):
        other_interface = Interface.objects.create(
            system=self.other_system,
            name="Other Interface",
            description="",
        )

        with self.assertRaises(ValidationError):
            build_generator_metadata(
                system=self.system,
                interface_ids=[other_interface.id],
                use_authentication=True,
            )
