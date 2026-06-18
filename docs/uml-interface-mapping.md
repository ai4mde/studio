# UML Interface Mapping Summary

This document summarizes how the LLM interface generator maps UML diagrams into pages, sections, workflows, and local edits.

## Goal

UML mapping owns the structural contract of the generated interface:

- which actor gets which pages;
- which models each page can read or mutate;
- how pages navigate to each other;
- how activity workflows become step-by-step UI;
- which sections are required for each page.

The LLM and Designer layer should mainly change layout, styling, tokens, and visual composition. They should not invent actor permissions, unrelated model pages, or deprecated fields such as `item_actions`.

## Main Pipeline

The current mapping flow is:

1. Read system metadata from class, use case, and activity diagrams.
2. Extract UML intelligence with `uml_mapping/uml_extractor.py`.
3. Build page, section, operation, and workflow plans with `uml_mapping/navigation_planner.py` and `uml_mapping/usecase_workflow.py`.
4. Materialize required sections and chrome with `uml_mapping/mapping_sections.py`.
5. Normalize and clean the resulting interface data.
6. Let LLM candidates and Designer patches modify presentation while preserving the UML-derived structure.

## Class Diagram To Model Graph

Class diagrams are converted into a `model_graph`.

Each UML class becomes a model entry containing:

- `name`
- `attributes`
- `layout_score`
- `compositions_owned`
- `composition_parent`
- `aggregations_owned`
- `associations`
- `specializes`
- `specialized_by`

Relationships are interpreted by type:

- `composition`: parent owns child; often becomes a detail page plus child collection.
- `aggregation`: related model, but weaker ownership.
- `association`: navigable model relationship.
- `directed_association`: navigable only from source to target.
- `generalization` / `inheritance`: child specializes parent.

Multiplicity is important. The mapper reads both flat and nested metadata shapes:

```json
{
  "multiplicity": {
    "source": "*",
    "target": "1"
  }
}
```

This prevents many-to-one context parents from being mistaken for owned collections. For example, `Product -> Seller` with many products sold by one seller should not automatically create a Customer-facing Seller workspace.

## Layout Scoring

Before the LLM sees the interface, the mapper scores model attributes for likely layouts:

- image, rating, price fields suggest `gallery` or `card`;
- status and date fields suggest `list`, `table`, or `timeline`;
- many fields or long text suggest `detail`;
- contact and identity fields suggest `form`;
- latitude/longitude fields suggest `map`.

These scores are hints, not final design decisions. Later stages combine them with use case role, workflow role, and LLM candidate styling.

## Use Case Diagram To Actor Scope

Use case diagrams determine actor-specific permissions and page intent.

The extractor infers:

- actor name;
- use cases connected to that actor;
- CRUD-like permissions from use case verbs;
- primary model for each use case;
- context models mentioned by a use case;
- page role, such as collection, detail, workflow entry, or object workspace.

Typical verb mapping:

- `view`, `browse`, `search`, `list` -> `read`
- `create`, `add`, `submit`, `place` -> `create`
- `update`, `edit`, `manage`, `approve` -> `update`
- `delete`, `remove`, `cancel` -> `delete`

Important rule:

`context_models` are not actor permissions.

If a use case says "View Product Detail" and mentions `Product`, `ProductImage`, `Seller`, and `Review`, only the true primary/access models become actor scope. Supporting models can be rendered as context or related data, but they do not automatically become standalone pages.

## Actor Page Generation

The mapper creates pages from actor scope, not from every class in the diagram.

A model can become a page when:

- the actor has inferred permission for it;
- it is directly required by a workflow;
- it is a child collection that belongs on a parent detail page;
- it is explicitly referenced by a valid navigation plan.

A model should not become a page only because:

- it appears as a related class;
- it is mentioned as use case context;
- it is a many-to-one parent of an accessible model;
- it exists somewhere in the class diagram.

This is the generic fix that prevents Customer actors from receiving unrelated Seller pages.

## Activity Diagram To Workflow

Activity diagrams become workflow plans.

The mapper reads:

- start and end nodes;
- action nodes;
- decision nodes;
- control-flow edges;
- class references attached to activity nodes.

Workflow steps are materialized as activity pages or activity sections. The step intent decides the section behavior:

- create record -> form section with `create` operation;
- update record -> form/detail section with `update` operation;
- read/check step -> detail or list section;
- decision step -> branching metadata with true/false next steps.

Workflow data is kept separate from normal collection/detail navigation so that a workflow can guide the user through a process without polluting the actor's main page set.

## Navigation Plan

The navigation planner produces:

- `pages`
- `sections`
- `operations`
- `workflows`
- item click behavior

Collection pages can navigate to detail pages with `behavior.item_click`:

```json
{
  "behavior": {
    "item_click": {
      "type": "navigate",
      "target_page": "Product Detail"
    }
  }
}
```

Record-level navigation should use `behavior.item_click`. The deprecated `item_actions` field should not be generated or saved.

## Section Materialization

`uml_mapping/mapping_sections.py` turns the plan into complete page structure.

It ensures:

- header, footer, and navigation chrome exist;
- normal pages receive global chrome sections;
- every page has at least one valid content section;
- workflow entry sections are present where needed;
- pre-workflow collection sections exist when a workflow needs selected context;
- detail pages get logical child collections;
- invalid or unreferenced non-global sections are removed;
- duplicate header shells are deduped.

This stage is structural. Candidate generation should not repeatedly re-invent these same required sections.

## Related Data Rules

Related data is placed according to relationship semantics:

- owned children can appear as child collection sections under a parent detail page;
- context parents can appear as readonly fields or detail context;
- related collections can appear when they are navigable and useful for the current actor;
- unrelated models are not materialized just because they exist in UML.

Example:

- Customer can browse `Product`.
- Product detail can show seller information as context.
- Customer should not get an independent `Sellers` page unless the actor has an actual Seller-related use case or permission.

## LLM Candidate Layer

LLM candidates should operate inside the UML-derived structure.

They may change:

- layout choices;
- components;
- spacing;
- density;
- color tokens;
- header and footer variants;
- section presentation.

They should not change:

- actor permissions;
- model ownership;
- workflow order;
- unrelated page access;
- deprecated fields.

Candidate generation now removes `item_actions` defensively before saving. This protects the interface even if an old prompt, old candidate, or external caller still sends the field.

## Designer Patch Layer

Designer edits go through `interface_patch.py`.

Patch behavior is intentionally local:

- merge incoming page/section/style changes;
- preserve existing pages, sections, and workflows;
- normalize supported fields;
- drop deprecated fields such as `item_actions`;
- avoid re-running the full UML mapper unless the user explicitly regenerates/maps.

This keeps manual design edits from accidentally changing the actor's UML-derived page scope.

## Item Actions Policy

`item_actions` is deprecated.

Use these replacements:

- detail navigation: `behavior.item_click`
- workflow entry: workflow operation or navigation method
- model-level method buttons: section `methods` or action panels
- bulk/table actions: section operations or method sections

The schema explicitly tells the LLM not to use `item_actions`, and backend candidate/patch code filters it out.

## Important Files

- `api/model/llm/interface_generator/uml_mapping/uml_extractor.py`
  Extracts model graph, actor permissions, layout signals, and workflow intelligence from UML metadata.

- `api/model/llm/interface_generator/uml_mapping/navigation_planner.py`
  Builds pages, sections, operations, workflows, and item click behavior.

- `api/model/llm/interface_generator/uml_mapping/usecase_workflow.py`
  Builds use case navigation and workflow-specific structures.

- `api/model/llm/interface_generator/uml_mapping/mapping_sections.py`
  Materializes required sections, chrome, child collections, workflow entry sections, and cleanup.

- `api/model/llm/interface_generator/candidate_generation.py`
  Generates and cleans LLM design candidates.

- `api/model/llm/interface_generator/interface_patch.py`
  Applies local Designer/API patches safely.

- `api/model/llm/interface_generator/interface_schemas.py`
  Defines the schema and prompt constraints for valid interface data.

## Short Mental Model

UML decides what exists and what the actor may do.

The mapper turns that into pages, sections, workflows, and navigation.

The LLM decides how the valid structure looks.

Designer patches edit local presentation safely.

Deprecated or structurally unsafe fields are filtered before saving.
