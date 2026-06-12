## Actual End-to-End Pipeline

```text
ProcessText
  ↓
TopologyPlanner (optional on baseline generation only)
  ↓
TopologyPlan
  ↓
Graph Realization Prompt Builder
  ↓
LLM Graph Generation / Refinement
  ↓
RawActivityGraphJSON
  ↓
Normalization
  ↓
NormalizedActivityGraph
  ↓
ActivityGraph Validation
  ↓
ActivityGraph
  ↓
Optional Diagnostics
  ├─ TopologyAnalysisReport
  └─ SketchAlignmentReport
  ↓
Converter
  ↓
AI4MDEExport
  ↓
AI4MDE Export Validation
  ↓
Optional Studio Import
```

## Stage Audit

| Stage | Input Artifact | Output Artifact | Responsibility | Current Implementation Location | Problems / Ambiguities | Overlap With Other Layers |
| --- | --- | --- | --- | --- | --- | --- |
| `ProcessText` intake | external request text | `ProcessText` | Hold the source business process narrative | `api/model/llm/refinement_generator.py`, `api/model/model/experiment_pipeline.py` | Also called process description, requirements, prose | Overlaps with prose pipeline vocabulary |
| Optional topology planning | `ProcessText` | `TopologyPlan` | Produce a lightweight control-flow plan before graph generation | `api/model/llm/prompt_builder.py`, `api/model/llm/templates/activity_sketch_prompt.jinja`, `api/model/llm/refinement_generator.py`, `api/model/llm/activity_sketch_model.py` | Only runs for initial generation, not refinement; named `sketch` in code but `topology plan` in prompt | Prompt layer partly owns topology semantics |
| Prompt construction | `ProcessText`, optional `TopologyPlan`, optional current model + instruction | prompt string | Render generation or refinement instructions | `api/model/llm/prompt_builder.py`, Jinja templates in `api/model/llm/templates/` | Baseline prompt acts like a graph realizer spec; refinement prompt mixes output schema, behavioral rules, and repair instructions | Shares responsibility with validators and diagnostics |
| LLM invocation | prompt string | raw JSON text | Call model and request structured JSON | `api/model/llm/handler.py`, called by `api/model/llm/refinement_generator.py` | `ACTIVITY_SKETCH_SCHEMA` in `handler.py` is out of sync with `ActivitySketch` model: it omits `loop_back_to` from properties and required fields while the Pydantic model supports it | Structured-output schema duplicates domain model schema |
| JSON extraction / recovery | raw LLM text | JSON payload string | Strip markdown fences and recover first JSON region | `api/model/llm/refinement_generator.py` | Recovery logic is operational, not architectural, but lives in the core modelling module | Slight overlap with handler/output-format concerns |
| Normalization | parsed raw JSON | `NormalizedActivityGraph` | Canonicalize aliases without inventing structure | `api/model/llm/normalization.py` | Described as `clean-graph payload`; terminology differs from `clean model`; only light semantic handling | Shares semantic vocabulary cleanup with prompts and converter |
| Clean graph validation | `NormalizedActivityGraph` | `ActivityGraph` | Enforce minimal structural validity: known node ids, duplicate id rejection, field shape | `api/model/llm/activity_model.py`, invoked in `api/model/llm/refinement_generator.py` | This is called “semantic validation” in errors, but it only enforces structural graph integrity, not UML semantics | Overlaps with topology diagnostics and prompt rules |
| Optional sketch alignment diagnostics | `TopologyPlan` + `ActivityGraph` | `SketchAlignmentReport` | Detect planner/realizer drift | `api/model/llm/sketch_alignment.py` | Purely heuristic and non-blocking, but terminology uses `validate_...` which sounds authoritative | Overlaps with planner semantics and topology analysis |
| Optional topology diagnostics | `ActivityGraph` | `TopologyAnalysisReport` | Detect coarse topology issues | `api/model/llm/topology_analysis.py` | Heuristic and non-blocking; still encodes important semantic assumptions | Overlaps with prompt rules and sketch alignment |
| Candidate generation wrapper | `ProcessText` | list of `ActivityGraph` | Repeat initial generation N times | `api/model/llm/refinement_generator.py` | Not a true layer but exposed as one in docs/comments | Overlaps with experiment/session orchestration |
| Refinement wrapper | `ProcessText` + current model + instruction | `AI4MDEExport` | Run the same core generation path in refinement mode, then convert | `api/model/llm/refinement_generator.py` | Mixed responsibility: refinement orchestration plus conversion plus metadata preservation | Overlaps with converter and experiment/session concerns |
| Conversion | `ActivityGraph` | `AI4MDEExport` | Translate clean graph into native Studio export format | `api/model/llm/converter.py` | Performs semantic mapping and native-shape validation assumptions, not just mechanical conversion | Overlaps with metadata specification layer |
| AI4MDE export validation | `AI4MDEExport` | validated `AI4MDEExport` | Enforce exact native Studio export structure | `api/model/llm/converter.py` | Hard-codes reference keys and native activity classifier shapes inside the LLM package | Overlaps strongly with metadata schemas/specifications |
| Optional import | `AI4MDEExport` | persisted Studio system/diagram | Import export into DB-backed Studio model | `api/model/model/experiment_pipeline.py`, `metadata.models.Project.import_systems_from_json`, test helpers | Import is downstream of conversion but still treated as part of some tests and experiment flows | Crosses into product persistence layer |

## Observed Architecture Drift

1. The clean graph core and the AI4MDE-native export path are coupled in `refinement_generator.py`.
2. Prompt templates currently carry a meaningful share of semantic topology policy.
3. `validation` means different things at different stages:
   schema validation, graph integrity checks, heuristic diagnostics, export-shape validation.
4. The LLM package contains both architecture-level clean artifacts and product-native AI4MDE transport concerns.
5. The topology planning layer exists, but only as an optional baseline-generation prepass, not as a universally owned architectural stage.

## Recommended Stable Pipeline Framing

For architecture documentation, the cleanest stable framing is:

1. `ProcessText -> TopologyPlan` as optional planning.
2. `ProcessText + optional TopologyPlan -> ActivityGraph` as realization.
3. `ActivityGraph -> NormalizedActivityGraph -> ActivityGraph validation` as clean-layer stabilization.
4. `ActivityGraph -> AI4MDEExport` as downstream translation.
5. Diagnostics (`TopologyAnalysisReport`, `SketchAlignmentReport`) as non-canonical side outputs, not core artifacts.
