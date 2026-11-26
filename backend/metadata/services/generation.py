
import django
from django.core import serializers

from diagram.api.schemas.diagram import DiagramReadFull
from diagram.models import Diagram
from metadata.models import Classifier
from ai.services.handler import llm_handler, remove_reply_markdown


def _generate(
    classifier: Classifier,
    prompt_name: str,
    input_data: dict,
    model: str,
    related_records,
) -> str | None:
    if classifier.type != "class":
        return None

    uml_class = classifier.data

    classifier_metadata = serializers.serialize(
        "json",
        [classifier, uml_class, *related_records(uml_class)],
    )

    diagrams = Diagram.objects.filter(system=classifier.system)
    diagram_data = [
        DiagramReadFull.model_validate(diagram).model_dump(mode="json")
        for diagram in diagrams
    ]

    input_data.update({
        "django_version": django.get_version(),
        "classifier_metadata": classifier_metadata,
        "diagrams_metadata": diagram_data,
    })

    reply = llm_handler(
        prompt_name=prompt_name,
        model=model,
        input_data=input_data,
    )

    return remove_reply_markdown(reply)


def generate_attribute(
    classifier: Classifier,
    name: str,
    type: str,
    description: str,
    model: str = "mixtral-8x7b-32768",
) -> str | None:
    return _generate(
        classifier=classifier,
        prompt_name="DIAGRAM_GENERATE_ATTRIBUTE",
        input_data={
            "attribute_name": name,
            "attribute_return_type": type,
            "attribute_description": description,
        },
        model=model,
        related_records=lambda cls: cls.attributes.all(),
    )


def generate_method(
    classifier: Classifier,
    name: str,
    description: str,
    model: str = "mixtral-8x7b-32768",
) -> str | None:
    return _generate(
        classifier=classifier,
        prompt_name="DIAGRAM_GENERATE_METHOD",
        input_data={
            "method_name": name,
            "method_description": description,
        },
        model=model,
        related_records=lambda cls: cls.operations.all(),
    )
