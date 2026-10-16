| Canonical Term | Deprecated / Alias Terms | Locations |
| --- | --- | --- |
| `ProcessText` | process description, requirements, prose, natural-language process description | `api/model/llm/refinement_generator.py`, `api/model/llm/prompt_builder.py`, `api/model/llm/templates/activity_*.jinja`, `api/model/model/experiment_pipeline.py`, `api/model/prose/api/views/pipelines.py` |
| `TopologyPlan` | activity sketch, sketch, topology sketch, control-flow scaffold, scaffold | `api/model/llm/activity_sketch_model.py`, `api/model/llm/refinement_generator.py`, `api/model/llm/prompt_builder.py`, `api/model/llm/templates/activity_sketch_prompt.jinja`, `api/model/llm/templates/activity_baseline_prompt.jinja`, `api/model/llm/sketch_alignment.py`, `api/model/llm/sketch_experiment.py` |
| `ActivityGraph` | activity model, graph, clean graph, clean model, graph JSON, activity diagram JSON | `api/model/llm/activity_model.py`, `api/model/llm/refinement_generator.py`, `api/model/llm/baseline_generator.py`, `api/model/llm/templates/activity_baseline_prompt.jinja`, `api/model/llm/templates/activity_refinement_prompt.jinja`, `api/model/llm/topology_analysis.py`, `api/model/llm/sketch_alignment.py`, tests under `api/model/llm/test_*.py` |
| `NormalizedActivityGraph` | normalized payload, normalized graph, lightly normalized clean-graph payload | `api/model/llm/normalization.py`, `api/model/llm/refinement_generator.py` |
| `AI4MDEExport` | AI4MDE JSON, AI4MDE model, systems export, wrapped export, system JSON, native Studio shape | `api/model/llm/converter.py`, `api/model/llm/refinement_generator.py`, `api/model/model/experiment_pipeline.py`, `api/model/llm/test_converter_export.py`, `api/model/llm/_test_helpers.py` |
| `TopologyAnalysisReport` | topology report, topology issues, topology metrics | `api/model/llm/topology_analysis.py`, `api/model/llm/sketch_experiment.py`, `api/model/llm/test_sketch_experiment.py` |
| `SketchAlignmentReport` | sketch alignment, graph-against-sketch validation, planner/decoder drift report | `api/model/llm/sketch_alignment.py`, `api/model/llm/refinement_generator.py`, `api/model/llm/test_baseline.py`, `api/model/llm/test_sketch_experiment.py` |
| `CandidateSet` | initial candidates, generated candidates, multi-candidate output | `api/model/llm/refinement_generator.py`, `api/model/llm/test_refinement.py`, `api/model/model/experiment_pipeline.py` |
| `ControlFlowEdge` | control, controlflow, control_flow, control-flow | `api/model/llm/normalization.py`, `api/model/llm/activity_model.py`, `api/model/llm/converter.py`, `api/model/metadata/specification/activity/relations.py`, prompts and tests |
| `ObjectFlowEdge` | object, objectflow, object_flow, object-flow | `api/model/llm/normalization.py`, `api/model/llm/activity_model.py`, `api/model/llm/converter.py`, `api/model/metadata/specification/activity/relations.py` |
| `NodeDisplayText` | label, title, text | `api/model/llm/normalization.py`, prompt templates, tests |
| `ActionName` | name, label, title, text | `api/model/llm/normalization.py`, `api/model/llm/activity_model.py`, `api/model/llm/templates/activity_refinement_prompt.jinja`, `api/model/llm/converter.py` |
| `BranchLabel` | label, branch, text, title | `api/model/llm/normalization.py`, prompt templates, tests, `api/model/llm/converter.py` |
| `BranchCondition` | condition, guard, structured condition | `api/model/llm/activity_model.py`, `api/model/llm/converter.py`, `api/model/metadata/specification/activity/relations.py`, `docs/users-guide.md` |
| `ControlNode` | control, control classifier, decision/merge/fork/join node | `api/model/metadata/specification/activity/classifiers/control.py`, `api/model/llm/converter.py`, prompts, topology modules |

## Key Drift Findings

1. `ActivitySketch` is the implemented type name, but the prompts frame it as a `topology plan`, and the sketch prompt calls it a `scaffold`. These are the same artifact in practice.
2. `ActivityModel` is the formal Pydantic type for the clean `nodes`/`edges` JSON, but the codebase also calls it `graph`, `clean model`, `clean graph`, and `activity diagram`.
3. `normalize_activity_graph` documents its output as a `clean-graph payload`, but downstream code usually calls the same artifact a `clean model`.
4. `convert_to_ai4mde` produces a single-system export, but the surrounding vocabulary alternates between `AI4MDE JSON`, `systems export`, `wrapped export`, and `system JSON`.
5. Edge type vocabulary drifts between clean-layer terms (`control`, `object`) and native export terms (`controlflow`, `objectflow`). Normalization and conversion explicitly bridge this gap.
6. Semantic text on edges drifts between `label`, `branch`, `condition`, and `guard`. The clean graph preserves both `label` and `condition`; the native AI4MDE relation also carries `guard`.
7. Decision node text drifts between `name` and `label`. The clean graph treats `label` as optional decision text, while the converter duplicates decision text into both `name` and `label` for native compatibility.
8. The word `validation` refers to at least four different things:
   structural schema validation, conservative normalization, heuristic topology diagnostics, and AI4MDE export validation.

## Recommended Canonical Naming

1. Use `ProcessText` for the input natural-language artifact.
2. Use `TopologyPlan` as the canonical architecture term for the planner output.
   Keep `ActivitySketch` as the current implementation type name until renaming is explicitly requested.
3. Use `ActivityGraph` as the canonical architecture term for the clean `nodes`/`edges` artifact.
   Treat `ActivityModel`, `clean model`, and `clean graph` as implementation aliases.
4. Use `NormalizedActivityGraph` for the post-normalization artifact returned just before Pydantic validation.
5. Use `AI4MDEExport` for the converted native export artifact.
   Reserve `system JSON` or `systems export` for transport/container shape discussion only.
6. Use `ControlFlowEdge` and `ObjectFlowEdge` as architecture terms, with explicit mapping to native `controlflow` / `objectflow`.
7. Use `ActionName` for action node semantic text, `NodeDisplayText` for generic node display text, `BranchLabel` for outgoing branch text, and `BranchCondition` for executable branch semantics.
8. Use `TopologyAnalysisReport` and `SketchAlignmentReport` for diagnostics, not `validation`, to reduce confusion with hard validators.

## Deprecation Guidance

The following aliases appear often enough to be considered active drift and should be treated as deprecated in new documentation:

| Prefer | Deprecate In New Docs |
| --- | --- |
| `TopologyPlan` | sketch, scaffold, topology sketch |
| `ActivityGraph` | clean graph, graph JSON, activity model |
| `NormalizedActivityGraph` | normalized payload, clean-graph payload |
| `AI4MDEExport` | wrapped export, system JSON, AI4MDE model |
| `ControlFlowEdge` | controlflow, control-flow, control_flow when discussing clean-layer semantics |
| `BranchLabel` | branch text, edge text |
| `BranchCondition` | guard when discussing clean-layer semantics |
