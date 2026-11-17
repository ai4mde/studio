from dataclasses import dataclass
from enum import Enum

from django.db import transaction

from metadata.models import (
    Attribute,
    Category,
    Classifier,
    Interface,
    Page,
    PageSection,
    SectionAttribute,
    SectionComponent,
    System,
)
from metadata.models.types import ClassifierType, RelationType


class CrudType(Enum):
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4
    OTHER = 5


@dataclass
class DefaultUsecase:
    name: str
    crud_types: list[CrudType]
    classifier: Classifier
    attributes: list[Attribute]


def get_directly_linked_use_cases(
    system: System,
    actor: Classifier,
) -> list[Classifier]:
    use_cases = []

    relations = system.relations.filter(
        type=RelationType.INTERACTION,
    ).select_related("source", "target")

    for relation in relations:
        if relation.source_id == actor.pk:
            other = relation.target
        elif relation.target_id == actor.pk:
            other = relation.source
        else:
            continue

        if other.type == ClassifierType.USECASE:
            use_cases.append(other)

    return use_cases


def get_extended_use_cases(
    system: System,
    use_cases: list[Classifier],
) -> list[Classifier]:
    extended = []
    use_case_ids = {use_case.pk for use_case in use_cases}

    relations = system.relations.filter(
        type=RelationType.EXTENSION,
    ).select_related("source", "target")

    for relation in relations:
        if (
            relation.source_id in use_case_ids
            and relation.target_id not in use_case_ids
            and relation.target not in extended
            and relation.target.type == ClassifierType.USECASE
        ):
            extended.append(relation.target)

    return extended


def get_crud_type(use_case_name: str) -> CrudType:
    name = use_case_name.lower()
    
    operations = {
        CrudType.CREATE: {"create", "make", "new", "post"},
        CrudType.READ: {'read', 'view', 'get', 'see'},
        CrudType.UPDATE: {'update', 'edit', 'patch', 'put'},
        CrudType.DELETE: {'delete', 'remove', 'erase'},
    }
    
    for crud_type, keywords in operations.items():
        if any(keyword in name for keyword in keywords):
            return crud_type

    return CrudType.OTHER


def get_class_acted_on(
    system: System,
    use_case_name: str,
) -> Classifier | None:
    classes = system.classifiers.filter(type=ClassifierType.CLASS)
    
    for classifier in classes:
        if classifier.data.name.lower() in use_case_name.lower():
            return classifier

    return None


def get_default_use_cases(
    system: System,
    relevant_use_cases: list[Classifier],
) -> list[DefaultUsecase]:
    grouped = {}

    for use_case in relevant_use_cases:
        name = use_case.data.name.lower()
        classifier = get_class_acted_on(system, name)
        
        if classifier is None:
            continue

        crud_type = get_crud_type(name)

        if classifier.pk not in grouped:
            grouped[classifier.pk] = {
                "classifier": classifier,
                "names": [],
                "crud_types": [],
            }

        group = grouped[classifier.pk]
        group["crud_types"].append(crud_type)
        
        if crud_type != CrudType.OTHER:
            group["names"].append(name)

    result = []

    for group in grouped.values():
        if not group["names"]:
            continue

        classifier = group["classifier"]
        
        result.append(
            DefaultUsecase(
                name=" and ".join(group["names"]),
                crud_types=group["crud_types"],
                classifier=classifier,
                attributes=list(classifier.data.attributes.all())
            )
        )

    return result


@transaction.atomic
def create_default_interface(
    system: System,
    actor: Classifier,
) -> Interface:
    if actor.type != ClassifierType.ACTOR:
        raise ValueError("Classifier is not an actor")

    if actor.system_id != system.pk:
        raise ValueError("Actor does not belong to this system")

    directly_linked = get_directly_linked_use_cases(system, actor)
    extended = get_extended_use_cases(system, directly_linked)

    default_use_cases = get_default_use_cases(system, directly_linked + extended)
    
    actor_name = actor.data.name
    
    interface = Interface.objects.create(
        system=system,
        actor=actor.data,
        name=actor_name,
        description=f"{actor_name} application",
    )
    
    for use_case in default_use_cases:
        uml_class = use_case.classifier.data
        
        category = Category.objects.create(
            interface=interface,
            name=uml_class.name,
        )
        
        section = SectionComponent.objects.create(
            interface=interface,
            name=use_case.name,
            uml_class=uml_class,
            allow_create=CrudType.CREATE in use_case.crud_types,
            allow_update=CrudType.UPDATE in use_case.crud_types,
            allow_delete=CrudType.DELETE in use_case.crud_types,
        )
        
        for index, attribute in enumerate(use_case.attributes):
            SectionAttribute.objects.create(
                section=section,
                attribute=attribute,
                order=index,
            )

        page = Page.objects.create(
            interface=interface,
            name=f"{use_case.name} page",
            category=category
        )
        
        PageSection.objects.create(
            page=page,
            section=section,
            order=0,
        )
    
    return interface
