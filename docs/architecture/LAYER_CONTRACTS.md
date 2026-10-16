## Layer Responsibility Audit

| Layer | Owns | Must NOT Do | Current Violations / Overlaps |
| --- | --- | --- | --- |
| Intake / Orchestration | session flow, choosing baseline vs refinement vs candidate generation, passing `ProcessText`, preserving metadata across calls | define graph semantics, define native export schema, repair topology | `api/model/llm/refinement_generator.py` combines orchestration with parsing, conversion, metadata extraction, and diagnostics |
| Planner | high-level control-flow planning, branch/rejoin intent, loop semantics at plan level | emit node ids, edge ids, full graph JSON, native export data | Prompt is clean about this, but naming drift (`sketch`, `scaffold`, `plan`) weakens the contract |
| Prompt Builder | rendering prompt text from already-decided artifacts and mode | own domain semantics, duplicate schemas, decide architectural policy | Jinja prompts currently contain many normative topology rules, so prompt layer partially owns semantics |
| LLM Invocation | call the model and request structured output | define business semantics, own artifact contracts, drift from model schema | `api/model/llm/handler.py` duplicates artifact schema definitions; `ACTIVITY_SKETCH_SCHEMA` is not aligned with `ActivitySketch` because `loop_back_to` is missing |
| Normalization | canonicalize vocabulary and field aliases conservatively | invent graph structure, repair semantics, reinterpret conditions as labels | Current implementation is mostly clean; this is one of the clearer layers |
| Clean Validation | enforce clean-graph structural integrity and schema shape | act as topology planner, perform heuristic diagnostics, enforce product-native export structure | Error wording calls some checks “semantic validation,” which blurs structural vs semantic responsibility |
| Diagnostics | report heuristic topology problems and planner/realizer drift | block generation, mutate graphs, become the canonical validator | `validate_graph_against_sketch` and `analyze_activity_graph` are advisory, but naming with `validate_` implies authority |
| Refinement | apply instruction-driven updates to an existing clean graph contract | convert to native export, own project metadata, own session ids | `refine_activity_model` currently refines and converts in one step, mixing clean-layer and integration-layer responsibilities |
| Converter / Translator | map clean graph semantics into native AI4MDE export format | own clean-graph semantics, own experiment workflow, define planner rules | `convert_to_ai4mde` includes strong assumptions about decision text duplication and native field policy; it also validates exact native shape |
| Native Export Validation | enforce Studio export contract exactly | own clean artifact policy, planner semantics, graph heuristics | `validate_ai4mde_json` lives in the converter module, coupling translation and validation tightly |
| Persistence / Import | import validated export into DB models | interpret free-form clean graph semantics, repair export payloads | Import path depends on converter correctness and native schema assumptions but is appropriately downstream |

## Current Major Violations

1. `refinement_generator.py` is overloaded.
   It currently acts as orchestrator, planner dispatcher, prompt caller, JSON parser, clean validator entrypoint, AI4MDE unwrap helper, candidate generator, and refinement-to-export wrapper.

2. Prompt templates own real semantic policy.
   Rules such as decision-to-merge closure, loop backward edges, and minimal topology redesign live in prompt text, which means layer responsibility is partly delegated to LLM instruction wording.

3. Handler-level schemas duplicate domain models.
   `ACTIVITY_SCHEMA` and `ACTIVITY_SKETCH_SCHEMA` in `api/model/llm/handler.py` are separate from `ActivityModel` and `ActivitySketch`, creating drift risk.

4. Converter straddles translation and contract enforcement.
   `api/model/llm/converter.py` both translates clean graphs and performs exact native export validation, so it behaves as translator plus native-schema authority.

5. Diagnostics are semantically important but non-authoritative.
   `topology_analysis.py` and `sketch_alignment.py` encode architecture rules that matter, but because they are heuristic reports, ownership is ambiguous.

## Recommended Stable Contracts

### Planner

- Owns:
  `TopologyPlan` only.
- Must not:
  emit full graph structure or native export details.

### Realizer

- Owns:
  transforming `ProcessText` plus optional `TopologyPlan` into `ActivityGraph`.
- Must not:
  redesign topology beyond minimal completion, invent export metadata, or act as importer.

### Normalizer

- Owns:
  field/type alias cleanup.
- Must not:
  fix missing merges, infer loops, or translate branch conditions into labels.

### Clean Validator

- Owns:
  `ActivityGraph` structural correctness.
- Must not:
  become a topology heuristic layer or native export validator.

### Diagnostics

- Owns:
  architecture health reporting.
- Must not:
  silently mutate artifacts or define the only source of semantic truth.

### Converter

- Owns:
  deterministic translation from `ActivityGraph` to `AI4MDEExport`.
- Must not:
  reinterpret planning intent or redesign graph semantics.

### Import Layer

- Owns:
  persistence of already-valid native exports.
- Must not:
  repair modelling-layer errors.

## Stabilization Recommendations

1. Document `ActivityGraph` as the clean canonical layer boundary.
2. Document `TopologyPlan` as the planner boundary, regardless of whether the implementation class keeps the name `ActivitySketch` for now.
3. Re-label diagnostics as diagnostics in docs and comments to reduce validator confusion.
4. Treat converter concerns as downstream integration responsibilities, not core modelling responsibilities.
5. Treat prompt templates as delivery mechanisms for policy, not the long-term canonical home of policy.
