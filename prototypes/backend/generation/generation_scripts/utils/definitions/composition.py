from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal


ComponentFamily = Literal[
    "hero",
    "gallery",
    "summary",
    "pricing",
    "actions",
    "attributes",
    "related-items",
    "reviews",
    "trust-signals",
    "table",
    "filters",
    "form",
    "timeline",
    "tabs",
    "custom",
]

Prominence = Literal["primary", "secondary", "supporting", "contextual"]


@dataclass(slots=True)
class SectionCapabilityProfile:
    section_id: str
    section_name: str
    capability: str
    component_family: ComponentFamily
    prominence: Prominence
    data_source: str | None = None
    actions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RegionDefinition:
    id: str
    label: str
    allowed_families: list[ComponentFamily]
    min_items: int = 0
    max_items: int | None = None
    required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TemplateSkeleton:
    id: str
    archetype: str
    label: str
    description: str
    viewport: Literal["mobile", "tablet", "desktop", "responsive"] = "responsive"
    regions: list[RegionDefinition] = field(default_factory=list)
    responsive_rules: list[str] = field(default_factory=list)
    prominence_rules: list[str] = field(default_factory=list)
    source: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CompositionBinding:
    section_id: str
    capability: str
    component_family: ComponentFamily
    region_id: str
    component_variant: str
    priority: int
    visibility: Literal["default", "collapsed", "hidden"] = "default"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PageComposition:
    page_id: str
    page_name: str
    page_archetype: str
    selected_variant_id: str
    skeleton_id: str
    bindings: list[CompositionBinding] = field(default_factory=list)
    region_order: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CompositionVariant:
    id: str
    label: str
    strategy: str
    skeleton_id: str
    composition: PageComposition
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["composition"] = self.composition.to_dict()
        return payload