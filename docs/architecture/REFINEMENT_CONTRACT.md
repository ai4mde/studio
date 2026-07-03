# Refinement Contract

This document defines the invariant contract for the semantic-deterministic
refinement engine.

## Pipeline

`User Instruction`
`+ Current Revision`
`+ Business Process Description`
`-> Refinement Planner`
`-> Updated Topology Artifact + Updated Semantic Sketch Plan`
`-> Topology/Semantic Reconciliation`
`-> Validation`
`-> Deterministic Sketch Builder`
`-> Deterministic Compiler`
`-> ActivityGraph`

## Ownership

`TopologyArtifact` owns:
- control-flow structure
- decisions
- loops
- parallel blocks
- nesting
- branch handles
- parent / parent_branch attachment

`SemanticSketchPlan` owns:
- root-scope actions
- branch-local action steps
- branch intent

The deterministic builder/compiler must treat topology as authoritative for
structure and semantics as authoritative for action content.

## Planner Contract

Planner inputs:
- `process_text`
- `current_topology_artifact`
- `current_semantic_sketch_plan`
- `natural_language_refinement_instruction`

Planner outputs:
- `updated_topology_artifact`
- `updated_semantic_sketch_plan`
- `refinement_trace`

Planner rules:
- always return complete artifacts, never patches
- preserve unrelated parts conservatively when the instruction is ambiguous
- never rely on graph-level edits
- `refinement_trace` is metadata only and must not drive execution

## Reconciliation Contract

The reconciliation layer is refinement-type agnostic.

Its responsibilities are:
- treat `updated_topology_artifact` as authoritative
- derive the required semantic coverage directly from topology
- preserve planner-provided semantic information whenever it remains valid
- preserve unchanged semantic information from the current revision whenever it
  still matches the updated topology
- remove obsolete semantic entries whose topology no longer exists
- synthesize only the minimum missing semantic entries required for completeness

The reconciliation layer must not branch on instruction types such as:
- insert action
- delete decision
- add loop
- remove parallel structure

## Artifact Invariants

These invariants must hold before deterministic compilation:

### Topology -> Semantic coverage

For every root-level topology structure `T`:
- `SemanticSketchPlan.root_actions` must contain exactly one `ROOT_START`
- `SemanticSketchPlan.root_actions` must contain exactly one `AFTER_<T.id>`

For every topology branch `(structure_id, branch)`:
- `SemanticSketchPlan.branch_plans` must contain exactly one matching branch
  plan

### Semantic uniqueness

- each root slot id must be unique
- each `(structure_id, branch)` pair must be unique

### Structural consistency

- semantic entries may only reference topology structures and branches that
  exist in the updated topology
- removed topology must imply removal of obsolete semantic entries
- newly introduced topology must imply synthesized semantic coverage if the
  planner omitted it

## Deterministic Builder Assumptions

The deterministic builder assumes:
- topology ordering/nesting is valid
- every required root slot has one semantic action
- every required branch has one semantic plan

The builder may safely default placeholder action text for synthesized semantic
entries, but it must not invent or alter topology.

## Deterministic Compiler Assumptions

The deterministic compiler assumes:
- the reconciled semantic plan is complete for the reconciled topology
- branch intents are structurally valid for the builder/compiler contract
- compilation should succeed without refinement-type-specific code paths

## Design Goal

All future refinement capabilities should use this single contract.

Adding support for a new user refinement instruction must improve planner
quality, not introduce new refinement-type-specific deterministic code paths.
