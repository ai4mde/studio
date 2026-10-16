# Final V2 Generator application

This document describes the Generator application from `feature/final-v2-integration`
(commit `56e82629`) prepared for integration with the laboratory `develop` branch.
The official 40-case, 120-candidate thesis experiment used
`feature/thesis-ui-isolation` (commit `3227af4b`), as recorded in the
[frozen run manifest](https://github.com/ai4mde/studio/blob/3426872e1537d6fa443f58bbd71318caa068edac/evaluation/friedrich_v2/cohorts/final_frozen_40x3_20260910/run_manifest.json)
on the separate evaluation branch (SHA-256:
`fd7bbff59ac127cbefdd03a26d4242b5eb7e2a5230ff9a6676bb6d3d861048d7`).
Final V2 has different generation logic and must not be described as the code
that produced those frozen candidates.

## Application runtime

### Authentication scope

Generator writes (`generate-model`, `select-candidate`, `refine-model`,
`synchronize-human-edit`, and `restore-revision`) require the laboratory's
existing JWT Bearer token. The frontend reads that token from its existing auth
store for each request, including after a page reload. Revision history uses
the laboratory's existing authenticated API default. Anonymous requests are
rejected. Generator write routes do not accept cookie-only authentication,
because the laboratory cookie authenticator currently has CSRF checking disabled.

Project and System records have no user ownership or membership policy in the
laboratory application. Authenticated users therefore retain the laboratory's
existing shared-project access; these endpoints do not establish per-user
authorization. Other laboratory routes still accept cookie-authenticated writes
without CSRF checks. Both limitations require a laboratory-wide security decision.

### Human edit and refinement workflow

The editor saves changes before **Sync with AI**. Sync validates the saved
ActivityGraph and creates a Human Sync revision with updated topology and
semantic artifacts. Refinement uses that synchronized revision, then creates a
new revision after import: **Save → Sync → Revision → Refinement**. Pending or
failed editor saves block Sync and Restore; Restore waits for pending saves.
Layout-only changes do not require Sync. When the saved process still matches
the revision's AI4MDE export, Sync may reuse its existing artifacts.

Sync can return 422 for an incomplete or unsupported process structure (for
example, a deleted node that leaves a branch without a valid closure). It does
not replace the saved model or create a revision in that case. A saved process
edit without Sync causes Refinement to return 409. Refinement also returns 409
when a meaningful editable field cannot survive its ActivityGraph conversion;
the saved model remains intact. It compares native process fields and revision
state before generation and again before import, while ignoring diagram layout.

The local editor tracks pending and failed PATCH saves, but the laboratory API
does not provide an atomic version lock for independent browser tabs or clients.
Concurrent writes across clients remain a laboratory-wide limitation.

The Final V2 application uses the `semantic_deterministic` generation profile.
`/refine-model` supports planning-artifact refinement when the selected system
has persisted process text, topology, and semantic artifacts. The legacy `stable`
profile remains a separate path.

Pipeline:

1. Process Text
2. Topology Artifact Generator
3. Semantic Sketch Planner
4. Deterministic Sketch Builder
5. Sketch Repair
6. Deterministic Compiler
7. ActivityGraph
8. Validation
9. Converter
10. AI4MDE Import

## Runtime Dependency Tree

Request entry:

- `/api/v1/generate-model`
  - [api/model/model/api.py](../api/model/model/api.py)
  - `generate_model(...)`

Pipeline orchestration:

- [api/model/model/experiment_pipeline.py](../api/model/model/experiment_pipeline.py)
  - `run_pipeline(...)`

Generation entry:

- [api/model/llm/baseline_generator.py](../api/model/llm/baseline_generator.py)
  - `generate_activity_model(...)`

Core runtime dispatch:

- [api/model/llm/refinement_generator.py](../api/model/llm/refinement_generator.py)
  - `model_activity(...)`
  - routes `pipeline_profile="semantic_deterministic"` to
  - `debug_model_activity_with_semantic_deterministic_profile(...)`

Semantic-deterministic stages:

1. Topology Artifact Generator
   - File: [api/model/llm/topology_experiment.py](../api/model/llm/topology_experiment.py)
   - Function: `generate_topology_artifact(process_text)`
   - Input: `process_text`
   - Output: `TopologyArtifact`

2. Semantic Sketch Planner
   - File: [api/model/llm/semantic_sketch_experiment.py](../api/model/llm/semantic_sketch_experiment.py)
   - Function: `generate_semantic_sketch_plan(process_text, topology_artifact=...)`
   - Input: `process_text`, `TopologyArtifact`
   - Output: `SemanticSketchPlan`

3. Deterministic Sketch Builder
   - File: [api/model/llm/topology_to_sketch_compiler.py](../api/model/llm/topology_to_sketch_compiler.py)
   - Function: `compile_topology_and_semantics_to_activity_sketch(...)`
   - Input: `TopologyArtifact`, `SemanticSketchPlan`
   - Output: `ActivitySketch`

4. Sketch Repair
   - File: [api/model/llm/sketch_repair.py](../api/model/llm/sketch_repair.py)
   - Function: `repair_activity_sketch(...)`
   - Input: `ActivitySketch`
   - Output: repaired `ActivitySketch`, repair report

5. Deterministic Compiler
   - File: [api/model/llm/experimental_compiler.py](../api/model/llm/experimental_compiler.py)
   - Function: `compile_activity_sketch(...)`
   - Input: repaired `ActivitySketch`
   - Output: `ActivityGraph`

6. Validation
   - File: [api/model/llm/refinement_generator.py](../api/model/llm/refinement_generator.py)
   - Function: `debug_model_activity_with_semantic_deterministic_profile(...)`
   - Uses:
     - [api/model/llm/sketch_alignment.py](../api/model/llm/sketch_alignment.py)
       - `validate_graph_against_sketch(...)`
     - [api/model/llm/semantic_analysis.py](../api/model/llm/semantic_analysis.py)
       - `analyze_semantic_graph(...)`
     - [api/model/llm/topology_analysis.py](../api/model/llm/topology_analysis.py)
       - `analyze_activity_graph(...)`
   - Input: `ActivityGraph`, repaired `ActivitySketch`
   - Output: diagnostics only

7. Converter
   - File: [api/model/llm/converter.py](../api/model/llm/converter.py)
   - Function: `convert_to_ai4mde(...)`
   - Input: `ActivityGraph`
   - Output: AI4MDE export JSON

8. AI4MDE Import
   - File: [api/model/model/experiment_pipeline.py](../api/model/model/experiment_pipeline.py)
   - Function: `import_to_ai4mde(...)`
   - Input: AI4MDE export JSON
   - Output: imported project/system/diagram records

## Active Generation Pipeline

Exact active dependency chain:

`api.py -> experiment_pipeline.py -> baseline_generator.py -> refinement_generator.py -> topology_experiment.py -> semantic_sketch_experiment.py -> topology_to_sketch_compiler.py -> sketch_repair.py -> experimental_compiler.py -> sketch_alignment.py / semantic_analysis.py / topology_analysis.py -> converter.py -> experiment_pipeline.py`

## Required Runtime Files

Core entrypoints:

- [api/model/model/api.py](../api/model/model/api.py)
- [api/model/model/experiment_pipeline.py](../api/model/model/experiment_pipeline.py)
- [api/model/llm/baseline_generator.py](../api/model/llm/baseline_generator.py)
- [api/model/llm/refinement_generator.py](../api/model/llm/refinement_generator.py)
- [api/model/llm/pipeline_profiles.py](../api/model/llm/pipeline_profiles.py)

Active semantic-deterministic components:

- [api/model/llm/topology_experiment.py](../api/model/llm/topology_experiment.py)
- [api/model/llm/semantic_sketch_experiment.py](../api/model/llm/semantic_sketch_experiment.py)
- [api/model/llm/topology_to_sketch_compiler.py](../api/model/llm/topology_to_sketch_compiler.py)
- [api/model/llm/sketch_repair.py](../api/model/llm/sketch_repair.py)
- [api/model/llm/experimental_compiler.py](../api/model/llm/experimental_compiler.py)
- [api/model/llm/converter.py](../api/model/llm/converter.py)

Schemas:

- [api/model/llm/topology_artifact_model.py](../api/model/llm/topology_artifact_model.py)
- [api/model/llm/semantic_sketch_plan_model.py](../api/model/llm/semantic_sketch_plan_model.py)
- [api/model/llm/activity_sketch_model.py](../api/model/llm/activity_sketch_model.py)
- [api/model/llm/activity_model.py](../api/model/llm/activity_model.py)

Shared support:

- [api/model/llm/prompt_builder.py](../api/model/llm/prompt_builder.py)
- [api/model/llm/handler.py](../api/model/llm/handler.py)
- [api/model/llm/keyword_hints.py](../api/model/llm/keyword_hints.py)
- [api/model/llm/normalization.py](../api/model/llm/normalization.py)

Active prompt templates:

- [api/model/llm/templates/activity_topology_experiment_prompt.jinja](../api/model/llm/templates/activity_topology_experiment_prompt.jinja)
- [api/model/llm/templates/activity_semantic_sketch_experiment_prompt.jinja](../api/model/llm/templates/activity_semantic_sketch_experiment_prompt.jinja)
- [api/model/llm/templates/activity_baseline_prompt.jinja](../api/model/llm/templates/activity_baseline_prompt.jinja)
- [api/model/llm/templates/activity_refinement_prompt.jinja](../api/model/llm/templates/activity_refinement_prompt.jinja)

## Validation Files

- [api/model/llm/topology_analysis.py](../api/model/llm/topology_analysis.py)
- [api/model/llm/semantic_analysis.py](../api/model/llm/semantic_analysis.py)
- [api/model/llm/sketch_alignment.py](../api/model/llm/sketch_alignment.py)

These are part of runtime diagnostics for `semantic_deterministic`.

## Converter / Import Path

Conversion:

- [api/model/llm/converter.py](../api/model/llm/converter.py)
  - `convert_to_ai4mde(...)`

Import:

- [api/model/model/experiment_pipeline.py](../api/model/model/experiment_pipeline.py)
  - `import_to_ai4mde(...)`
  - `resolve_experiment_project(...)`

## Active Refinement Files

When a selected system has persisted process text, topology, and semantic
artifacts, `/refine-model` uses these files for planning-artifact refinement:

- [api/model/llm/refinement_generator.py](../api/model/llm/refinement_generator.py)
- [api/model/model/experiment_pipeline.py](../api/model/model/experiment_pipeline.py)
- [api/model/model/api.py](../api/model/model/api.py)
- [api/model/llm/topology_experiment.py](../api/model/llm/topology_experiment.py)
- [api/model/llm/semantic_sketch_experiment.py](../api/model/llm/semantic_sketch_experiment.py)
- [api/model/llm/topology_to_sketch_compiler.py](../api/model/llm/topology_to_sketch_compiler.py)
- [api/model/llm/sketch_repair.py](../api/model/llm/sketch_repair.py)
- [api/model/llm/experimental_compiler.py](../api/model/llm/experimental_compiler.py)
- [api/model/llm/converter.py](../api/model/llm/converter.py)

## Submission scope

Standalone experiment runners and the manual sketch debugger from the source
branch are excluded from this application integration. They are not runtime
dependencies of the Final V2 generation path. Other available profiles retain
their own paths and are not part of the official 120-candidate experiment.
