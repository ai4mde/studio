## Core Artifact Definitions

| Artifact | Purpose | Producer | Consumer | Ownership | Stability Expectation | Canonical or Transitional |
| --- | --- | --- | --- | --- | --- | --- |
| `ProcessText` | Source description of the business process to model | user request, experiment pipeline, future API callers | planner prompt, graph prompt, refinement flow | application boundary / orchestration layer | Stable as input concept; content is free-form | Canonical |
| `TopologyPlan` | Lightweight control-flow plan that captures main flow and high-level control blocks before graph realization | topology-sketch LLM flow in `api/model/llm/refinement_generator.py` using `ActivitySketch` | baseline graph realization prompt, sketch-alignment diagnostics | planning layer | Structurally stable enough for prompt handoff, but semantically still evolving | Canonical concept, transitional implementation name |
| `ActivityGraph` | Clean, implementation-neutral activity graph represented as `nodes` and `edges` | graph LLM flow after parse/validation, AI4MDE unwrap/extract path | diagnostics, refinement prompts, converter, candidate display logic | clean modelling layer | Should become the primary stable internal artifact | Canonical |
| `NormalizedActivityGraph` | Alias-normalized version of the clean graph just before Pydantic validation | `normalize_activity_graph` | `ActivityModel.model_validate` | normalization sub-layer | Transitional internal artifact; stable shape should converge into `ActivityGraph` | Transitional |
| `TopologyAnalysisReport` | Heuristic report about coarse structural topology quality | `analyze_activity_graph` | experiments, debugging, future audit tooling | diagnostics layer | Best-effort, advisory only | Transitional / diagnostic |
| `SketchAlignmentReport` | Heuristic report describing drift between `TopologyPlan` and realized `ActivityGraph` | `validate_graph_against_sketch` | debugging, experiments, architecture audit | diagnostics layer | Best-effort, advisory only | Transitional / diagnostic |
| `AI4MDEExport` | Native Studio single-system export payload suitable for import or UI rendering | `convert_to_ai4mde` | experiment pipeline, import helpers, Studio import path, frontend-renderable flows | translation / integration layer | Should be stable relative to Studio native schema, even if clean-layer artifacts evolve | Canonical downstream integration artifact |
| `CandidateSet` | Collection of independently generated initial `ActivityGraph` instances, optionally paired with converted exports | `generate_initial_candidates`, `generate_and_convert_candidates` | refinement-selection workflows, experiments | orchestration layer | Workflow-specific, not a core domain artifact | Transitional |

## Detailed Artifact Notes

### `ProcessText`

- Purpose: represent the original natural-language description of a process.
- Producer: external caller.
- Consumer: both planning and graph-generation prompts.
- Ownership: orchestration layer, not the LLM schema layer.
- Stability: very stable as a concept, deliberately unstructured.
- Boundary note: should not absorb instructions, model state, or export metadata.

### `TopologyPlan`

- Current implementation artifact: `ActivitySketch`.
- Purpose: define the intended control-flow topology without node ids, edge ids, or native export concerns.
- Producer: optional sketch generation step.
- Consumer: baseline generation prompt and sketch-alignment diagnostics.
- Ownership: planning layer.
- Stability: should be stable at the level of control blocks (`decision`, `loop`, `parallel`) and reconnection semantics, but currently carries some prompt-era terminology drift (`sketch`, `scaffold`, `plan`).
- Boundary note: should not contain graph realization details, UUIDs, full node sets, or AI4MDE metadata.

### `ActivityGraph`

- Current implementation artifact: `ActivityModel`.
- Purpose: the clean internal graph contract for activity generation.
- Producer: graph-generation LLM flow or AI4MDE unwrap/extract path.
- Consumer: refinement prompts, diagnostics, converter.
- Ownership: clean modelling layer.
- Stability: should be the main stable internal artifact because it is simpler and less product-coupled than AI4MDE export.
- Boundary note: should not embed Studio-native classifier/relation layout, project metadata, or database identifiers.

### `NormalizedActivityGraph`

- Purpose: absorb legacy aliases and vocabulary drift before clean validation.
- Producer: `normalize_activity_graph`.
- Consumer: `ActivityModel.model_validate`.
- Ownership: normalization sub-layer inside clean modelling.
- Stability: intentionally conservative and internal.
- Boundary note: should not repair topology or invent semantic structure.

### `AI4MDEExport`

- Purpose: express a realized activity graph in the native Studio import/export schema.
- Producer: `convert_to_ai4mde`.
- Consumer: Studio import path, experiment pipeline, export validation, frontend flows that expect native format.
- Ownership: translation/integration layer, even though implementation currently lives in `api/model/llm/converter.py`.
- Stability: should remain stable relative to Studio native schema.
- Boundary note: this is a downstream integration artifact, not the core modelling artifact.

## Ownership Recommendations

1. Treat `ActivityGraph` as the primary canonical internal artifact.
2. Treat `TopologyPlan` as the primary planning artifact.
3. Treat `AI4MDEExport` as a downstream translation target owned by integration concerns.
4. Treat reports (`TopologyAnalysisReport`, `SketchAlignmentReport`) as diagnostics, never as canonical graph state.
5. Treat `NormalizedActivityGraph` as an internal processing artifact, not a public contract.
