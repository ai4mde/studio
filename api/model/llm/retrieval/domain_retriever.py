from __future__ import annotations

from typing import Any

from django.db.models import Q

from metadata.models import Classifier, Relation, System

from .context import ExistingMethodInfo, RelatedClassInfo, RetrievalContext


class DomainRetriever:
    def __init__(self, system: System, include_target_methods: bool = True):
        self.system = system
        self.include_target_methods = include_target_methods

    def retrieve(self, target_classifier: Classifier) -> RetrievalContext:
        target_data = self._as_dict(target_classifier.data)
        target_name = self._as_str(target_data.get("name"), fallback=str(target_classifier.id))
        target_attributes = self._as_list_of_dict(target_data.get("attributes"))

        context = RetrievalContext(
            target_class_name=target_name,
            target_class_attributes=target_attributes,
        )

        if self.include_target_methods:
            target_methods = self._extract_methods(class_name=target_name, classifier_data=target_data)
            self._extend_unique_methods(context.existing_methods, target_methods)

        relations = (
            Relation.objects.filter(system=self.system)
            .filter(Q(source=target_classifier) | Q(target=target_classifier))
            .select_related("source", "target")
        )

        for relation in relations:
            relation_data = self._as_dict(relation.data)
            multiplicity = self._as_dict(relation_data.get("multiplicity"))

            outgoing = relation.source_id == target_classifier.id
            related_classifier = relation.target if outgoing else relation.source
            related_data = self._as_dict(related_classifier.data)
            related_name = self._as_str(related_data.get("name"), fallback=str(related_classifier.id))

            context.related_classes.append(
                RelatedClassInfo(
                    class_name=related_name,
                    relation_type=self._as_str(relation_data.get("type"), fallback="association"),
                    direction="outgoing" if outgoing else "incoming",
                    multiplicity_source=self._as_optional_str(multiplicity.get("source")),
                    multiplicity_target=self._as_optional_str(multiplicity.get("target")),
                    attributes=self._as_list_of_dict(related_data.get("attributes")),
                    methods=self._as_list_of_dict(related_data.get("methods")),
                )
            )

            related_methods = self._extract_methods(
                class_name=related_name,
                classifier_data=related_data,
            )
            self._extend_unique_methods(context.existing_methods, related_methods)

        return context

    def _extract_methods(self, class_name: str, classifier_data: dict[str, Any]) -> list[ExistingMethodInfo]:
        methods: list[ExistingMethodInfo] = []
        for method in self._as_list_of_dict(classifier_data.get("methods")):
            method_name = self._as_optional_str(method.get("name"))
            if not method_name:
                continue

            methods.append(
                ExistingMethodInfo(
                    class_name=class_name,
                    method_name=method_name,
                    description=self._as_str(method.get("description"), fallback=""),
                    body=self._as_str(method.get("body"), fallback=""),
                    return_type=self._as_optional_str(method.get("type")),
                )
            )
        return methods

    def _extend_unique_methods(
        self, existing: list[ExistingMethodInfo], incoming: list[ExistingMethodInfo]
    ) -> None:
        seen = {(method.class_name, method.method_name, method.body) for method in existing}
        for method in incoming:
            key = (method.class_name, method.method_name, method.body)
            if key in seen:
                continue
            existing.append(method)
            seen.add(key)

    def _as_dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _as_list_of_dict(self, value: Any) -> list[dict]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    def _as_optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def _as_str(self, value: Any, *, fallback: str) -> str:
        if value is None:
            return fallback
        return str(value)
