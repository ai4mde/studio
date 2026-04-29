"""
Composition layer — schemas, skeleton registry, and capability inference.

Separates the three concerns from the prototype generation roadmap:
  1. Business semantics  (diagrams, interface definitions)
  2. Composition         (page structure, region placement)   ← this module
  3. Visual styling      (themes, Tailwind tokens)

PageComposition is the shared source consumed by both preview rendering and
the emit (prototype file generation) path.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────────────────────
# Layout role — tells the HTML renderer where each region belongs
# ─────────────────────────────────────────────────────────────────────────────

REGION_LAYOUT_ROLE: dict[str, str] = {
    "hero_primary":   "main",
    "hero_secondary": "aside-left",
    "detail_main":    "main",
    "detail_tabs":    "main",
    "supporting":     "main",
    "summary_rail":   "aside-right",
    "action_rail":    "aside-right",
}


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SectionCapabilityProfile:
    """Inferred structural capability for one interface section."""
    section_id: str
    section_name: str
    capability: str           # gallery | stat-cards | data-table | form-fields |
                              # related-items | activity-feed | featured-content |
                              # rich-text | navigation | filters | actions
    component_variant: str = "default"
    confidence: float = 1.0


@dataclass
class RegionSpec:
    """Capacity and preferred content families for one layout region."""
    region_id: str
    min_sections: int = 1
    max_sections: int = 3
    preferred_capabilities: list[str] = field(default_factory=list)
    required: bool = False


@dataclass
class TemplateSkeleton:
    """Reusable structural reference for one page layout variant."""
    id: str           # "<archetype>/<layout-descriptor>", e.g. "product-detail/buybox-right"
    archetype: str
    description: str
    region_order: list[str]
    region_specs: dict[str, RegionSpec] = field(default_factory=dict)
    # "single-col" | "two-col-right-rail" | "two-col-left-sidebar" | "three-col"
    responsive: str = "single-col"


@dataclass
class PageCompositionBinding:
    """Maps one section to a region with a resolved capability."""
    region_id: str
    section_id: str
    capability: str
    component_variant: str = "default"


@dataclass
class PageComposition:
    """Selected structural plan for one page — shared by preview and emit."""
    page_id: str
    page_archetype: str
    skeleton_id: str
    region_order: list[str]
    bindings: list[PageCompositionBinding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "page_archetype": self.page_archetype,
            "skeleton_id": self.skeleton_id,
            "region_order": self.region_order,
            "bindings": [
                {
                    "region_id": b.region_id,
                    "section_id": b.section_id,
                    "capability": b.capability,
                    "component_variant": b.component_variant,
                }
                for b in self.bindings
            ],
        }

    @classmethod
    def from_dict(cls, page_id: str, data: dict) -> "PageComposition":
        bindings = [
            PageCompositionBinding(
                region_id=b["region_id"],
                section_id=b.get("section_id", ""),
                capability=b.get("capability", "data-table"),
                component_variant=b.get("component_variant", "default"),
            )
            for b in (data.get("bindings") or [])
            if isinstance(b, dict) and b.get("region_id")
        ]
        return cls(
            page_id=page_id,
            page_archetype=data.get("page_archetype", "data-list"),
            skeleton_id=data.get("skeleton_id", "data-list/standard"),
            region_order=data.get("region_order") or [],
            bindings=bindings,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Curated skeleton registry
# ─────────────────────────────────────────────────────────────────────────────

def _sk(
    id: str,
    archetype: str,
    description: str,
    region_order: list[str],
    region_specs: dict[str, RegionSpec],
    responsive: str = "single-col",
) -> TemplateSkeleton:
    return TemplateSkeleton(
        id=id,
        archetype=archetype,
        description=description,
        region_order=region_order,
        region_specs=region_specs,
        responsive=responsive,
    )


SKELETON_REGISTRY: dict[str, TemplateSkeleton] = {sk.id: sk for sk in [

    # ── Product Detail ────────────────────────────────────────────────────────
    _sk(
        "product-detail/buybox-right",
        archetype="product-detail",
        description="Gallery left, price+CTA right rail, specs and reviews stacked below",
        region_order=["hero_primary", "action_rail", "detail_tabs", "supporting"],
        region_specs={
            "hero_primary":  RegionSpec("hero_primary",  1, 2, ["gallery", "featured-content"], required=True),
            "action_rail":   RegionSpec("action_rail",   1, 1, ["actions"],                     required=True),
            "detail_tabs":   RegionSpec("detail_tabs",   1, 3, ["featured-content", "data-table", "rich-text"]),
            "supporting":    RegionSpec("supporting",    0, 3, ["related-items", "activity-feed"]),
        },
        responsive="two-col-right-rail",
    ),
    _sk(
        "product-detail/stack",
        archetype="product-detail",
        description="Single-column stacked: image → buybox → specs → reviews",
        region_order=["hero_primary", "action_rail", "detail_tabs", "supporting"],
        region_specs={
            "hero_primary":  RegionSpec("hero_primary",  1, 1, ["gallery"],                     required=True),
            "action_rail":   RegionSpec("action_rail",   1, 1, ["actions"],                     required=True),
            "detail_tabs":   RegionSpec("detail_tabs",   1, 2, ["featured-content", "rich-text"]),
            "supporting":    RegionSpec("supporting",    0, 2, ["activity-feed", "related-items"]),
        },
        responsive="single-col",
    ),
    _sk(
        "product-detail/media-focus",
        archetype="product-detail",
        description="Wide media zone top, compact action rail, tabbed detail below",
        region_order=["hero_primary", "hero_secondary", "action_rail", "detail_tabs", "supporting"],
        region_specs={
            "hero_primary":   RegionSpec("hero_primary",   1, 1, ["gallery"],                         required=True),
            "hero_secondary": RegionSpec("hero_secondary", 1, 2, ["featured-content", "rich-text"]),
            "action_rail":    RegionSpec("action_rail",    1, 1, ["actions"],                         required=True),
            "detail_tabs":    RegionSpec("detail_tabs",    1, 3, ["data-table", "rich-text"]),
            "supporting":     RegionSpec("supporting",     0, 2, ["related-items"]),
        },
        responsive="two-col-right-rail",
    ),

    # ── Data List ─────────────────────────────────────────────────────────────
    _sk(
        "data-list/filter-sidebar",
        archetype="data-list",
        description="Left filter sidebar + right results grid or table",
        region_order=["hero_secondary", "detail_main", "supporting"],
        region_specs={
            "hero_secondary": RegionSpec("hero_secondary", 1, 2, ["filters", "navigation"]),
            "detail_main":    RegionSpec("detail_main",    1, 1, ["data-table", "related-items"], required=True),
            "supporting":     RegionSpec("supporting",     0, 1, ["stat-cards"]),
        },
        responsive="two-col-left-sidebar",
    ),
    _sk(
        "data-list/standard",
        archetype="data-list",
        description="Full-width list with inline search bar and table",
        region_order=["hero_secondary", "detail_main"],
        region_specs={
            "hero_secondary": RegionSpec("hero_secondary", 0, 1, ["filters"]),
            "detail_main":    RegionSpec("detail_main",    1, 1, ["data-table"], required=True),
        },
        responsive="single-col",
    ),
    _sk(
        "data-list/card-grid",
        archetype="data-list",
        description="Search/filter bar top, card grid results below",
        region_order=["hero_secondary", "detail_main", "supporting"],
        region_specs={
            "hero_secondary": RegionSpec("hero_secondary", 0, 1, ["filters"]),
            "detail_main":    RegionSpec("detail_main",    1, 1, ["related-items"], required=True),
            "supporting":     RegionSpec("supporting",     0, 1, ["stat-cards"]),
        },
        responsive="single-col",
    ),

    # ── Cart ──────────────────────────────────────────────────────────────────
    _sk(
        "cart/split-summary",
        archetype="cart",
        description="Cart item list left, order summary right rail",
        region_order=["detail_main", "summary_rail", "action_rail"],
        region_specs={
            "detail_main":  RegionSpec("detail_main",  1, 1, ["data-table"],                    required=True),
            "summary_rail": RegionSpec("summary_rail", 1, 1, ["featured-content", "stat-cards"], required=True),
            "action_rail":  RegionSpec("action_rail",  1, 1, ["actions"]),
        },
        responsive="two-col-right-rail",
    ),
    _sk(
        "cart/empty-state",
        archetype="cart",
        description="Centered empty-state card + recommendations below",
        region_order=["hero_primary", "supporting"],
        region_specs={
            "hero_primary": RegionSpec("hero_primary", 1, 1, ["featured-content"], required=True),
            "supporting":   RegionSpec("supporting",   0, 1, ["related-items"]),
        },
        responsive="single-col",
    ),

    # ── Account / Profile ─────────────────────────────────────────────────────
    _sk(
        "account/sidebar-nav",
        archetype="profile-detail",
        description="Left navigation sidebar + main content area",
        region_order=["hero_secondary", "detail_main", "supporting"],
        region_specs={
            "hero_secondary": RegionSpec("hero_secondary", 1, 1, ["navigation"],                required=True),
            "detail_main":    RegionSpec("detail_main",    1, 2, ["form-fields", "data-table"], required=True),
            "supporting":     RegionSpec("supporting",     0, 2, ["activity-feed", "stat-cards"]),
        },
        responsive="two-col-left-sidebar",
    ),
    _sk(
        "account/tabbed",
        archetype="profile-detail",
        description="Profile header + tabbed content sections",
        region_order=["hero_primary", "detail_tabs", "supporting"],
        region_specs={
            "hero_primary": RegionSpec("hero_primary", 1, 1, ["featured-content"]),
            "detail_tabs":  RegionSpec("detail_tabs",  1, 3, ["form-fields", "data-table", "activity-feed"], required=True),
            "supporting":   RegionSpec("supporting",   0, 1, ["stat-cards"]),
        },
        responsive="single-col",
    ),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    _sk(
        "dashboard/stat-grid",
        archetype="dashboard",
        description="KPI stat cards row + main data table + side panel",
        region_order=["hero_secondary", "detail_main", "supporting", "summary_rail"],
        region_specs={
            "hero_secondary": RegionSpec("hero_secondary", 1, 4, ["stat-cards"]),
            "detail_main":    RegionSpec("detail_main",    1, 2, ["data-table", "activity-feed"], required=True),
            "supporting":     RegionSpec("supporting",     0, 2, ["related-items", "activity-feed"]),
            "summary_rail":   RegionSpec("summary_rail",   0, 2, ["stat-cards", "featured-content"]),
        },
        responsive="two-col-right-rail",
    ),
    _sk(
        "dashboard/full-width",
        archetype="dashboard",
        description="Full-width: stat row then stacked sections",
        region_order=["hero_secondary", "detail_main", "supporting"],
        region_specs={
            "hero_secondary": RegionSpec("hero_secondary", 1, 3, ["stat-cards"]),
            "detail_main":    RegionSpec("detail_main",    1, 2, ["data-table", "activity-feed"], required=True),
            "supporting":     RegionSpec("supporting",     0, 2, ["related-items"]),
        },
        responsive="single-col",
    ),

    # ── Wizard / Checkout ─────────────────────────────────────────────────────
    _sk(
        "wizard-form/stepper",
        archetype="wizard-form",
        description="Top progress stepper + form content + order summary rail",
        region_order=["hero_primary", "detail_main", "summary_rail", "action_rail"],
        region_specs={
            "hero_primary":  RegionSpec("hero_primary",  1, 1, ["navigation"]),
            "detail_main":   RegionSpec("detail_main",   1, 1, ["form-fields"],       required=True),
            "summary_rail":  RegionSpec("summary_rail",  0, 1, ["featured-content"]),
            "action_rail":   RegionSpec("action_rail",   1, 1, ["actions"]),
        },
        responsive="two-col-right-rail",
    ),

    # ── Detail Form ───────────────────────────────────────────────────────────
    _sk(
        "detail-form/card",
        archetype="detail-form",
        description="Centered card form with section grouping",
        region_order=["hero_primary", "detail_main", "action_rail"],
        region_specs={
            "hero_primary": RegionSpec("hero_primary", 0, 1, ["featured-content"]),
            "detail_main":  RegionSpec("detail_main",  1, 2, ["form-fields"], required=True),
            "action_rail":  RegionSpec("action_rail",  1, 1, ["actions"]),
        },
        responsive="single-col",
    ),
]}


def skeleton_ids_by_archetype() -> dict[str, list[str]]:
    """Return skeleton IDs grouped by archetype — useful for prompt context."""
    result: dict[str, list[str]] = {}
    for sk in SKELETON_REGISTRY.values():
        result.setdefault(sk.archetype, []).append(sk.id)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Section capability inference
# ─────────────────────────────────────────────────────────────────────────────

# (matching_semantic_roles, capability, component_variant)
_ROLE_TO_CAPABILITY: list[tuple[frozenset[str], str, str]] = [
    (frozenset({"image_primary", "image_gallery"}),         "gallery",          "image-card-grid"),
    (frozenset({"image_primary"}),                          "gallery",          "image-card-grid"),
    (frozenset({"image_gallery"}),                          "gallery",          "image-card-grid"),
    (frozenset({"price_current", "quantity_input"}),        "actions",          "buybox"),
    (frozenset({"price_current", "availability"}),          "actions",          "buybox"),
    (frozenset({"price_current"}),                          "actions",          "price-cta"),
    (frozenset({"rating_score", "review_text"}),            "activity-feed",    "review-list"),
    (frozenset({"rating_score", "rating_count"}),           "activity-feed",    "review-summary"),
    (frozenset({"spec_group"}),                             "featured-content", "spec-table"),
    (frozenset({"spec_name", "spec_value"}),                "featured-content", "spec-table"),
    (frozenset({"delivery_date", "delivery_option"}),       "featured-content", "delivery-info"),
    (frozenset({"delivery_date"}),                          "featured-content", "delivery-info"),
    (frozenset({"description_long"}),                       "rich-text",        "content-block"),
    (frozenset({"description_short", "title"}),             "featured-content", "summary-card"),
]

# (name_keywords, capability, component_variant)
_NAME_TO_CAPABILITY: list[tuple[list[str], str, str]] = [
    (["filter", "search", "facet"],                          "filters",          "filter-bar"),
    (["nav", "menu", "category", "sidebar"],                 "navigation",       "nav-list"),
    (["stat", "metric", "kpi", "dashboard", "overview"],     "stat-cards",       "kpi-row"),
    (["review", "rating", "feedback", "comment"],            "activity-feed",    "review-list"),
    (["gallery", "image", "photo", "media"],                 "gallery",          "image-card-grid"),
    (["cart", "basket", "bag"],                              "data-table",       "cart-item-list"),
    (["checkout", "payment", "billing"],                     "form-fields",      "payment-form"),
    (["order", "purchase", "history", "transaction"],        "data-table",       "order-list"),
    (["wishlist", "saved", "bookmark", "favorite"],          "related-items",    "product-card-grid"),
    (["recommendation", "related", "similar", "suggested"], "related-items",    "product-card-grid"),
    (["profile", "account", "setting", "preference"],       "form-fields",      "profile-form"),
    (["address", "shipping", "delivery"],                    "form-fields",      "address-form"),
    (["specification", "attribute", "detail", "feature", "spec"], "featured-content", "spec-table"),
    (["description", "about", "overview", "content"],       "rich-text",        "content-block"),
    (["summary", "info"],                                    "featured-content", "summary-card"),
    (["action", "cta", "buy", "add to cart"],                "actions",          "buybox"),
    (["list", "table", "index"],                             "data-table",       "data-table"),
]


def infer_section_capability(
    section_id: str,
    section_name: str,
    semantic_roles: list[str] | None = None,
    has_list_op: bool = False,
    has_create_op: bool = False,
    has_update_op: bool = False,
) -> SectionCapabilityProfile:
    """Infer the structural capability for a section from its fields and name."""
    roles_set = frozenset(semantic_roles or [])

    # 1. Role-based matching (highest confidence)
    for required_roles, capability, variant in _ROLE_TO_CAPABILITY:
        if required_roles & roles_set:
            return SectionCapabilityProfile(
                section_id=section_id,
                section_name=section_name,
                capability=capability,
                component_variant=variant,
                confidence=0.95,
            )

    # 2. Name-based matching
    lower_name = section_name.lower()
    for keywords, capability, variant in _NAME_TO_CAPABILITY:
        if any(kw in lower_name for kw in keywords):
            return SectionCapabilityProfile(
                section_id=section_id,
                section_name=section_name,
                capability=capability,
                component_variant=variant,
                confidence=0.80,
            )

    # 3. CRUD operation fallback
    if has_create_op or has_update_op:
        return SectionCapabilityProfile(
            section_id=section_id,
            section_name=section_name,
            capability="form-fields",
            component_variant="crud-form",
            confidence=0.60,
        )
    if has_list_op:
        return SectionCapabilityProfile(
            section_id=section_id,
            section_name=section_name,
            capability="data-table",
            component_variant="data-table",
            confidence=0.60,
        )

    return SectionCapabilityProfile(
        section_id=section_id,
        section_name=section_name,
        capability="data-table",
        component_variant="data-table",
        confidence=0.40,
    )
