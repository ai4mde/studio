# Design Agent — Architecture & Implementation Summary

> UML metadata → deterministic page synthesis → LLM-driven AST generation → themed HTML output

## Pipeline Overview

A **4-node LangGraph pipeline** that transforms UML activity/class/usecase diagrams into a complete Django + HTMX web UI with theme tokens and layout chrome:

```
parser_node → ui_designer_node → theme_node → layout_options_node → END
```

**Key files:**

| File | Role |
|------|------|
| `agents/nodes.py` | All 4 pipeline nodes + guardrails + helper algorithms |
| `agents/pipeline.py` | LangGraph graph construction & invocation |
| `agents/state.py` | `PipelineState` TypedDict (all pipeline I/O) |
| `agents/renderer.py` | AST → Django/Jinja2 HTML with theme token injection |
| `llm/prompts/agents.py` | All LLM prompt templates |

---

## 1. Parser Node

**Input:** Raw UML metadata (classifiers + relations JSON)
**Output:** `parser_dsl`, `diagram_summary`, `screens`, `flow_graph`

### 1.1 `_build_parser_dsl`

The core extraction function. Produces a canonical DSL:

```python
{
  "actors": [...],
  "entities": [{"name", "fields": [...]}],
  "actions": [{
    "name", "actor", "auto",
    "entity_flow": {entity: "produces"|"consumes"|"read_write"},
    "state_transitions": {entity: {"from_states": [...], "to_states": [...]}},
    "step_order", "upstream_actions", "downstream_actions", "control_flow"
  }],
  "workflow": {"nodes": [...], "edges": [...]},
  "field_context": {entity: [{field, type, decision_condition?, decided_by_actor?, decided_by_action_id?, auto_computed?}]},
  "entity_first_produced_by": {entity: actor_name},
  "entity_associations": {entity: [{entity_name, label, multiplicity}]}
}
```

### 1.2 BFS Algorithms

| Algorithm | Purpose | Traversal Rule |
|-----------|---------|----------------|
| `_directed_bfs` | Find entities connected to an action (forward/backward) | Traverses control nodes freely; **peeks one hop** through intermediate action nodes to reach adjacent object nodes, but does NOT continue BFS beyond that action |
| `_state_bfs` | Extract `from_states`/`to_states` per action | Same one-hop-peek strategy at action boundaries — prevents reaching states many actions away and polluting results |
| `_input_entities_for` | Map each action to consumed/produced entity IDs | Wraps `_directed_bfs` for forward + reverse adjacency |

**Why one-hop peek?** Without it, BFS through chains of actions reaches distant states (e.g. `Assess completeness → fork → ... → [Created]`). Limiting to one hop ensures only directly adjacent states are captured.

### 1.3 Field-Level Context

- **Decision fields:** Fields referenced in decision node conditions → tracked with `decided_by_actor` and `decided_by_action_id`
- **Auto-computed fields:** Extracted from automatic action `customCode` via regex `entity.field = ...`
- **First producer tracking:** `entity_first_produced_by` maps each entity to the actor who first creates it

---

## 2. Page Synthesis (`_synthesise_pages`)

**Deterministic** — same input always produces same page structure. Runs BEFORE any LLM call.

### Algorithm

1. **Filter:** Skip `auto: True` actions (no human UI needed)
2. **Cluster:** Greedy merging per actor group
   - Affinity scoring: same actor (0.4) + adjacent in workflow (0.3) + shared entity (0.3)
   - Merge pairs if average affinity ≥ 0.5 and combined size ≤ 5
3. **Cut:** Split oversized clusters into chunks of ≤ 5

### Output: `page_ir`

Each page carries full context for the LLM:

- `intent_hints[].attribute_contracts[]` — per-field metadata: `field_type`, `decision_condition`, `decided_by_actor`, `decided_by_action_id`, `auto_computed`, `associated_entity`
- `intent_hints[].workflow_context` — `entity_flow`, `state_transitions`, `entity_first_produced_by`, `step_order`, `control_flow`, `actor_name`
- `intent_hints[].binding_groups[]` — grouped entity bindings with operations

---

## 3. UI Designer Node

**Input:** `page_ir` + `parser_dsl` + live design references
**Output:** `ui_design` (ui_ir with AST + field_policies per component)

### 3.1 Field Mode Reasoning

The LLM decides `editable | readonly | hidden` for each field using structured metadata:

| Entity Flow | Scenario | Rule |
|-------------|----------|------|
| `consumes` | Review/approve prior work | All readonly, **EXCEPT** fields with `decided_by_actor` matching this actor AND `decided_by_action_id` matching this page's action |
| `produces` + first producer | Initial data entry (no `from_states`) | Input fields → editable; other actors' decisions → hidden; `auto_computed` → hidden |
| `produces` + not first producer | Decision/processing (has `from_states`) | Prior data → readonly (never hidden); `auto_computed` → readonly; this actor's decisions → editable |
| `read_write` | Modify + read | Creation input → readonly; `auto_computed` → readonly; new output fields → editable |

**Hard constraints:**
- `produces`/`read_write` pages must have ≥ 1 editable field
- Every `attribute_contract` field must appear in `field_policies`
- `from_states` non-empty → all prior fields at minimum readonly (never hidden)

### 3.2 Live Design Reference Fetching

No hardcoded patterns — the pipeline fetches real HTML at runtime:

- `_discover_design_urls()` — scrapes index pages from Flowbite, DaisyUI, MerakiUI
- `_build_ui_layout_references()` — full page layouts with PALETTE/LAYOUT/TYPOGRAPHY hints
- `_build_component_style_references()` — individual component snippets (button, input, table)

### 3.3 AST Node Types

| Type | Key Fields | Renders As |
|------|-----------|------------|
| **Element** | `tag`, `variant`, `attrs`, `htmx`, `bind`, `text`, `children` | `<tag attrs hx-attrs>{{bind}}</tag>` |
| **Loop** | `loop`, `as`, `children` | `{% for as in loop %}...{% endfor %}` |
| **Conditional** | `if`, `children`, `elif`, `else_children` | `{% if %}...{% elif %}...{% else %}...{% endif %}` |
| **Raw** | `inner_html` | Raw HTML passthrough |

---

## 4. Guardrails (Post-LLM Enforcement)

Applied sequentially after LLM output:

| Guardrail | Purpose |
|-----------|---------|
| `_guardrail_page_completeness` | Inject entire pages the LLM omitted from its output |
| `_guardrail_completeness` | Backfill fields the LLM omitted — `from_states` present → readonly, absent → hidden |
| `_guardrail_entity_flow` | Force `consumes` → readonly (with decided_by exemption); guarantee ≥ 1 editable for produces/read_write |
| `_enforce_field_policies` | Strip hidden field AST nodes; convert readonly fields to display-only (remove htmx, add variant="readonly") |

### Decision exemption logic (`_guardrail_entity_flow`)

When `entity_flow == "consumes"`, a field can remain editable if:
1. `decided_by_action_id` exists for that field, AND
2. That action_id is among this page's actions

This prevents blanket readonly on fields that this actor's action actually decides.

---

## 5. Theme Node

**Input:** `ui_design` AST variants + live design references
**Output:** `theme` dict with Tailwind token mappings

### Token Resolution Strategy (renderer)

Priority order for `_resolve_variant_class(tag, variant, theme)`:
1. `element.{tag}.{variant}`
2. `component.{tag}.{variant}`
3. `component.{variant}`
4. `region.{variant}`
5. `{variant}` (bare)

### Required Structural Tokens

Always injected regardless of AST content:
- `page.body` — `<body>` background, text color, font family
- `page.main` — `<main>` max-width, padding, margin
- `page.surface` — content card: border, shadow, radius, padding

---

## 6. Layout Options Node

**Output:** 5 visually distinct global layout chrome presets

Each option includes:
- `elements` — named chrome pieces (navbar, sidebar, footer) with Tailwind HTML + position + config
- `theme_tokens` — overrides for all theme token keys (page.body, page.main, page.surface vary dramatically)

Options are designed to be fundamentally different approaches (topbar-only, dark sidebar, glassmorphism, icon-rail, bottom-tab), not just recolored variants.

---

## 7. Renderer (`renderer.py`)

Converts AST → Django/Jinja2 HTML:

- `normalize_node()` — moves `hx-*` keys from attrs into htmx map
- `render_node()` — dispatches on node type, resolves variant → Tailwind classes via theme
- `render_page()` — concatenates rendered nodes into full page HTML

**Design:** No semantic knowledge. Emit generic HTML + Jinja2 control flow. Theme token resolver injects Tailwind classes at render time. AST authoring is decoupled from visual styling.

---

## 8. State (`PipelineState`)

```python
class PipelineState(TypedDict):
    # Inputs
    project_name: str
    metadata: str                    # raw JSON
    system_id: str
    authentication_present: bool

    # Parser outputs
    screens: List[ScreenInfo]
    diagram_summary: DiagramSummary
    parser_dsl: Optional[dict]
    flow_graph: Optional[dict]

    # Page synthesis (deterministic)
    page_ir: Optional[dict]

    # LLM outputs
    ui_design: Optional[UIDesign]
    theme: Optional[dict]
    layout_options: Optional[list]

    # Refinement
    refine_prompt: Optional[str]
```

---

## 9. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Live design library fetching at runtime | No hardcoded patterns → always fresh; LLM sees real modern design |
| Deterministic page synthesis before LLM | Reproducible structure; LLM only handles styling/field modes |
| BFS one-hop peek at action boundaries | Prevents reaching distant states while still capturing adjacent object nodes |
| Auto-computed field detection via regex on customCode | Lets prompt distinguish system-set fields from user-editable ones |
| `decided_by_action_id` tracking | Enables precise per-page exemption from consumes→readonly rule |
| Guardrails post-LLM (not pre-validation) | Catches common LLM errors without blocking output; graceful degradation |
| Variant-driven theming (no semantic tokens) | LLM invents variants freely; theme uses only what ui_ir actually emits |
| 5 layout options (not configurable count) | Enough variety without overwhelming the designer |
