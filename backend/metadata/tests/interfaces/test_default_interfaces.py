
from django.test import TestCase

from metadata.models import (
    Attribute,
    Category,
    Classifier,
    Interface,
    Page,
    PageSection,
    Project,
    Relation,
    SectionAttribute,
    SectionComponent,
    System,
)
from metadata.models.types import (
    ClassifierType,
    DataType,
    RelationType,
)
from metadata.services.interfaces.default import (
    CrudType,
    create_default_interface,
    get_class_acted_on,
    get_crud_type,
    get_default_use_cases,
    get_directly_linked_use_cases,
    get_extended_use_cases,
)


class DefaultInterfaceTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.system = System.objects.create(
            project=self.project,
            name="Test System",
        )

        self.actor = self._classifier(
            "Administrator", ClassifierType.ACTOR
        )
        self.customer = self._classifier(
            "Customer", ClassifierType.CLASS
        )
        self.order = self._classifier(
            "Order", ClassifierType.CLASS
        )

        self.email = Attribute.objects.create(
            uml_class=self.customer.data,
            name="email",
            type=DataType.STRING,
        )
        self.age = Attribute.objects.create(
            uml_class=self.customer.data,
            name="age",
            type=DataType.INT,
        )

    def _classifier(self, name, classifier_type, system=None):
        return Classifier.create(
            system_id=(system or self.system).pk,
            classifier_type=classifier_type,
            data={"name": name},
        )

    def _relation(self, source, target, relation_type):
        return Relation.create(
            system_id=self.system.pk,
            source_id=source.pk,
            target_id=target.pk,
            relation_type=relation_type,
            data={},
        )

    def test_directly_linked_use_cases(self):
        create = self._classifier(
            "Create Customer", ClassifierType.USECASE
        )
        view = self._classifier(
            "View Customer", ClassifierType.USECASE
        )
        unrelated = self._classifier(
            "Delete Order", ClassifierType.USECASE
        )

        self._relation(self.actor, create, RelationType.INTERACTION)
        self._relation(view, self.actor, RelationType.INTERACTION)

        result = get_directly_linked_use_cases(
            self.system, self.actor
        )

        self.assertEqual(
            {use_case.pk for use_case in result},
            {create.pk, view.pk},
        )
        self.assertNotIn(unrelated.pk, [item.pk for item in result])

    def test_extended_use_cases(self):
        create = self._classifier(
            "Create Customer", ClassifierType.USECASE
        )
        update = self._classifier(
            "Update Customer", ClassifierType.USECASE
        )

        self._relation(self.actor, create, RelationType.INTERACTION)
        self._relation(create, update, RelationType.EXTENSION)

        directly_linked = get_directly_linked_use_cases(
            self.system, self.actor
        )
        extended = get_extended_use_cases(
            self.system, directly_linked
        )

        self.assertEqual(
            [use_case.pk for use_case in extended],
            [update.pk],
        )

    def test_crud_detection_and_class_matching(self):
        expected = {
            "Create Customer": CrudType.CREATE,
            "View Customer": CrudType.READ,
            "Edit Customer": CrudType.UPDATE,
            "Delete Customer": CrudType.DELETE,
            "Manage Customer": CrudType.OTHER,
        }

        for name, crud_type in expected.items():
            with self.subTest(name=name):
                self.assertEqual(get_crud_type(name), crud_type)

        self.assertEqual(
            get_class_acted_on(self.system, "Create Customer"),
            self.customer,
        )
        self.assertIsNone(
            get_class_acted_on(self.system, "View Invoice")
        )

    def test_groups_use_cases_by_class(self):
        names = [
            "Create Customer",
            "View Customer",
            "Update Customer",
            "Delete Order",
            "Manage Customer",
        ]

        use_cases = [
            self._classifier(name, ClassifierType.USECASE)
            for name in names
        ]

        result = get_default_use_cases(self.system, use_cases)

        self.assertEqual(len(result), 2)

        by_class = {
            item.classifier.pk: item
            for item in result
        }

        customer = by_class[self.customer.pk]
        self.assertEqual(
            customer.name,
            "create customer and view customer and update customer",
        )
        self.assertIn(CrudType.CREATE, customer.crud_types)
        self.assertIn(CrudType.READ, customer.crud_types)
        self.assertIn(CrudType.UPDATE, customer.crud_types)

        self.assertEqual(
            {attribute.pk for attribute in customer.attributes},
            {self.email.pk, self.age.pk},
        )

        order = by_class[self.order.pk]
        self.assertEqual(order.name, "delete order")
        self.assertIn(CrudType.DELETE, order.crud_types)

    def test_creates_default_interface_with_components(self):
        create = self._classifier(
            "Create Customer", ClassifierType.USECASE
        )
        update = self._classifier(
            "Update Customer", ClassifierType.USECASE
        )

        self._relation(self.actor, create, RelationType.INTERACTION)
        self._relation(create, update, RelationType.EXTENSION)

        interface = create_default_interface(
            self.system, self.actor
        )

        self.assertIsInstance(interface, Interface)
        self.assertEqual(interface.system, self.system)
        self.assertEqual(interface.actor, self.actor.data)
        self.assertEqual(interface.name, "Administrator")
        self.assertEqual(
            interface.description, "Administrator application"
        )

        # Original styling defaults.
        self.assertEqual(interface.radius, 0)
        self.assertEqual(interface.text_color, "#000000")
        self.assertEqual(interface.accent_color, "#F5F5F4")
        self.assertEqual(interface.background_color, "#FFFFFF")
        self.assertEqual(interface.style, "modern")

        self.assertEqual(
            Category.objects.filter(interface=interface).count(), 1
        )
        self.assertEqual(
            Page.objects.filter(interface=interface).count(), 1
        )
        self.assertEqual(
            SectionComponent.objects.filter(
                interface=interface
            ).count(), 1
        )

        section = SectionComponent.objects.get(interface=interface)

        self.assertEqual(section.uml_class, self.customer.data)
        self.assertTrue(section.allow_create)
        self.assertTrue(section.allow_update)
        self.assertFalse(section.allow_delete)

        section_attributes = SectionAttribute.objects.filter(
            section=section
        )
        self.assertEqual(section_attributes.count(), 2)
        self.assertEqual(
            set(section_attributes.values_list("attribute_id", flat=True)),
            {self.email.pk, self.age.pk},
        )

        page = Page.objects.get(interface=interface)
        self.assertEqual(page.category.name, "Customer")

        page_section = PageSection.objects.get(page=page)
        self.assertEqual(page_section.section, section)
        self.assertEqual(page_section.order, 0)

    def test_actor_without_use_cases_creates_empty_interface(self):
        interface = create_default_interface(
            self.system, self.actor
        )

        self.assertEqual(interface.name, "Administrator")
        self.assertFalse(interface.pages.exists())
        self.assertFalse(interface.categories.exists())
        self.assertFalse(interface.sections.exists())

    def test_rejects_non_actor_without_creating_interface(self):
        before = Interface.objects.count()

        with self.assertRaises(ValueError):
            create_default_interface(
                self.system, self.customer
            )

        self.assertEqual(Interface.objects.count(), before)

    def test_rejects_actor_from_another_system(self):
        other_system = System.objects.create(
            project=self.project,
            name="Other System",
        )
        other_actor = self._classifier(
            "Other Actor",
            ClassifierType.ACTOR,
            system=other_system,
        )

        before = Interface.objects.count()

        with self.assertRaises(ValueError):
            create_default_interface(
                self.system, other_actor
            )

        self.assertEqual(Interface.objects.count(), before)
