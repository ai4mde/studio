# Production Surface

This document is the single source of truth for the active thesis production runtime.

## Official Runtime

The official thesis runtime is the `semantic_deterministic` generation profile.

Refinement is not part of that baseline freeze yet. The existing `/refine-model`
workflow still defaults to the legacy graph-level `stable` profile until a
planning-artifact refinement path is introduced.

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
  - [api/model/model/api.py](/Users/queenie/Desktop/studio/api/model/model/api.py)
  - `generate_model(...)`

Pipeline orchestration:

- [api/model/model/experiment_pipeline.py](/Users/queenie/Desktop/studio/api/model/model/experiment_pipeline.py)
  - `run_pipeline(...)`

Generation entry:

- [api/model/llm/baseline_generator.py](/Users/queenie/Desktop/studio/api/model/llm/baseline_generator.py)
  - `generate_activity_model(...)`

Core runtime dispatch:

- [api/model/llm/refinement_generator.py](/Users/queenie/Desktop/studio/api/model/llm/refinement_generator.py)
  - `model_activity(...)`
  - routes `pipeline_profile="semantic_deterministic"` to
  - `debug_model_activity_with_semantic_deterministic_profile(...)`

Semantic-deterministic stages:

1. Topology Artifact Generator
   - File: [api/model/llm/topology_experiment.py](/Users/queenie/Desktop/studio/api/model/llm/topology_experiment.py)
   - Function: `generate_topology_artifact(process_text)`
   - Input: `process_text`
   - Output: `TopologyArtifact`

2. Semantic Sketch Planner
   - File: [api/model/llm/semantic_sketch_experiment.py](/Users/queenie/Desktop/studio/api/model/llm/semantic_sketch_experiment.py)
   - Function: `generate_semantic_sketch_plan(process_text, topology_artifact=...)`
   - Input: `process_text`, `TopologyArtifact`
   - Output: `SemanticSketchPlan`

3. Deterministic Sketch Builder
   - File: [api/model/llm/topology_to_sketch_compiler.py](/Users/queenie/Desktop/studio/api/model/llm/topology_to_sketch_compiler.py)
   - Function: `compile_topology_and_semantics_to_activity_sketch(...)`
   - Input: `TopologyArtifact`, `SemanticSketchPlan`
   - Output: `ActivitySketch`

4. Sketch Repair
   - File: [api/model/llm/sketch_repair.py](/Users/queenie/Desktop/studio/api/model/llm/sketch_repair.py)
   - Function: `repair_activity_sketch(...)`
   - Input: `ActivitySketch`
   - Output: repaired `ActivitySketch`, repair report

5. Deterministic Compiler
   - File: [api/model/llm/experimental_compiler.py](/Users/queenie/Desktop/studio/api/model/llm/experimental_compiler.py)
   - Function: `compile_activity_sketch(...)`
   - Input: repaired `ActivitySketch`
   - Output: `ActivityGraph`

6. Validation
   - File: [api/model/llm/refinement_generator.py](/Users/queenie/Desktop/studio/api/model/llm/refinement_generator.py)
   - Function: `debug_model_activity_with_semantic_deterministic_profile(...)`
   - Uses:
     - [api/model/llm/sketch_alignment.py](/Users/queenie/Desktop/studio/api/model/llm/sketch_alignment.py)
       - `validate_graph_against_sketch(...)`
     - [api/model/llm/semantic_analysis.py](/Users/queenie/Desktop/studio/api/model/llm/semantic_analysis.py)
       - `analyze_semantic_graph(...)`
     - [api/model/llm/topology_analysis.py](/Users/queenie/Desktop/studio/api/model/llm/topology_analysis.py)
       - `analyze_activity_graph(...)`
   - Input: `ActivityGraph`, repaired `ActivitySketch`
   - Output: diagnostics only

7. Converter
   - File: [api/model/llm/converter.py](/Users/queenie/Desktop/studio/api/model/llm/converter.py)
   - Function: `convert_to_ai4mde(...)`
   - Input: `ActivityGraph`
   - Output: AI4MDE export JSON

8. AI4MDE Import
   - File: [api/model/model/experiment_pipeline.py](/Users/queenie/Desktop/studio/api/model/model/experiment_pipeline.py)
   - Function: `import_to_ai4mde(...)`
   - Input: AI4MDE export JSON
   - Output: imported project/system/diagram records

## Active Generation Pipeline

Exact active dependency chain:

`api.py -> experiment_pipeline.py -> baseline_generator.py -> refinement_generator.py -> topology_experiment.py -> semantic_sketch_experiment.py -> topology_to_sketch_compiler.py -> sketch_repair.py -> experimental_compiler.py -> sketch_alignment.py / semantic_analysis.py / topology_analysis.py -> converter.py -> experiment_pipeline.py`

## Required Runtime Files

Core entrypoints:

- [api/model/model/api.py](/Users/queenie/Desktop/studio/api/model/model/api.py)
- [api/model/model/experiment_pipeline.py](/Users/queenie/Desktop/studio/api/model/model/experiment_pipeline.py)
- [api/model/llm/baseline_generator.py](/Users/queenie/Desktop/studio/api/model/llm/baseline_generator.py)
- [api/model/llm/refinement_generator.py](/Users/queenie/Desktop/studio/api/model/llm/refinement_generator.py)
- [api/model/llm/pipeline_profiles.py](/Users/queenie/Desktop/studio/api/model/llm/pipeline_profiles.py)

Active semantic-deterministic components:

- [api/model/llm/topology_experiment.py](/Users/queenie/Desktop/studio/api/model/llm/topology_experiment.py)
- [api/model/llm/semantic_sketch_experiment.py](/Users/queenie/Desktop/studio/api/model/llm/semantic_sketch_experiment.py)
- [api/model/llm/topology_to_sketch_compiler.py](/Users/queenie/Desktop/studio/api/model/llm/topology_to_sketch_compiler.py)
- [api/model/llm/sketch_repair.py](/Users/queenie/Desktop/studio/api/model/llm/sketch_repair.py)
- [api/model/llm/experimental_compiler.py](/Users/queenie/Desktop/studio/api/model/llm/experimental_compiler.py)
- [api/model/llm/converter.py](/Users/queenie/Desktop/studio/api/model/llm/converter.py)

Schemas:

- [api/model/llm/topology_artifact_model.py](/Users/queenie/Desktop/studio/api/model/llm/topology_artifact_model.py)
- [api/model/llm/semantic_sketch_plan_model.py](/Users/queenie/Desktop/studio/api/model/llm/semantic_sketch_plan_model.py)
- [api/model/llm/activity_sketch_model.py](/Users/queenie/Desktop/studio/api/model/llm/activity_sketch_model.py)
- [api/model/llm/activity_model.py](/Users/queenie/Desktop/studio/api/model/llm/activity_model.py)

Shared support:

- [api/model/llm/prompt_builder.py](/Users/queenie/Desktop/studio/api/model/llm/prompt_builder.py)
- [api/model/llm/handler.py](/Users/queenie/Desktop/studio/api/model/llm/handler.py)
- [api/model/llm/keyword_hints.py](/Users/queenie/Desktop/studio/api/model/llm/keyword_hints.py)
- [api/model/llm/normalization.py](/Users/queenie/Desktop/studio/api/model/llm/normalization.py)

Active prompt templates:

- [api/model/llm/templates/activity_topology_experiment_prompt.jinja](/Users/queenie/Desktop/studio/api/model/llm/templates/activity_topology_experiment_prompt.jinja)
- [api/model/llm/templates/activity_semantic_sketch_experiment_prompt.jinja](/Users/queenie/Desktop/studio/api/model/llm/templates/activity_semantic_sketch_experiment_prompt.jinja)
- [api/model/llm/templates/activity_baseline_prompt.jinja](/Users/queenie/Desktop/studio/api/model/llm/templates/activity_baseline_prompt.jinja)
- [api/model/llm/templates/activity_refinement_prompt.jinja](/Users/queenie/Desktop/studio/api/model/llm/templates/activity_refinement_prompt.jinja)

## Validation Files

- [api/model/llm/topology_analysis.py](/Users/queenie/Desktop/studio/api/model/llm/topology_analysis.py)
- [api/model/llm/semantic_analysis.py](/Users/queenie/Desktop/studio/api/model/llm/semantic_analysis.py)
- [api/model/llm/sketch_alignment.py](/Users/queenie/Desktop/studio/api/model/llm/sketch_alignment.py)

These are part of runtime diagnostics for `semantic_deterministic`.

## Converter / Import Path

Conversion:

- [api/model/llm/converter.py](/Users/queenie/Desktop/studio/api/model/llm/converter.py)
  - `convert_to_ai4mde(...)`

Import:

- [api/model/model/experiment_pipeline.py](/Users/queenie/Desktop/studio/api/model/model/experiment_pipeline.py)
  - `import_to_ai4mde(...)`
  - `resolve_experiment_project(...)`

## Files Likely Needed Later For Refinement

Even though `semantic_deterministic` does not yet support refinement, these files are the expected extension points:

- [api/model/llm/refinement_generator.py](/Users/queenie/Desktop/studio/api/model/llm/refinement_generator.py)
- [api/model/model/experiment_pipeline.py](/Users/queenie/Desktop/studio/api/model/model/experiment_pipeline.py)
- [api/model/model/api.py](/Users/queenie/Desktop/studio/api/model/model/api.py)
- [api/model/llm/topology_experiment.py](/Users/queenie/Desktop/studio/api/model/llm/topology_experiment.py)
- [api/model/llm/semantic_sketch_experiment.py](/Users/queenie/Desktop/studio/api/model/llm/semantic_sketch_experiment.py)
- [api/model/llm/topology_to_sketch_compiler.py](/Users/queenie/Desktop/studio/api/model/llm/topology_to_sketch_compiler.py)
- [api/model/llm/sketch_repair.py](/Users/queenie/Desktop/studio/api/model/llm/sketch_repair.py)
- [api/model/llm/experimental_compiler.py](/Users/queenie/Desktop/studio/api/model/llm/experimental_compiler.py)
- [api/model/llm/converter.py](/Users/queenie/Desktop/studio/api/model/llm/converter.py)

## Archived / Non-Production Files

Standalone experiment and debug scripts are archived under:

- [archive/standalone_experiments](/Users/queenie/Desktop/studio/archive/standalone_experiments)

These are not part of the official production runtime:

- manual sketch debugger
- standalone topology artifact experiment runner
- standalone topology-to-sketch experiment runner
- standalone semantic sketch builder experiment runner

Legacy agentic and ablation paths may still exist in code, but they are not the official thesis production runtime unless explicitly selected by another profile.
