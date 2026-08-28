# Friedrich V2 Evaluation

Friedrich V2 is a clean, reproducible workspace for comparing Friedrich reference
process models with generated UML ActivityGraph models. The AI-only baseline preserves
and evaluates exactly three generation-order candidates per case, with no human or
reference-based candidate selection. It evaluates business
activities (**Action**), required matched-action precedence (**Flow**), and
behavioral control facts (**Structure**) without requiring exact BPMN/UML topology.

The raw source dataset remains external and read-only at:

`/Users/queenie/Desktop/evaluation-data/Text2Process`

The old `evaluation/friedrich/` namespace is legacy. V2 never imports it, searches
it, or uses its manifests, checkpoints, correspondences, generated `run_1.json`
files, scores, reviews, or results implicitly.

## Evaluation flow

```text
Friedrich raw dataset
-> EvalGraph conversion
-> Action evaluation
-> Flow evaluation
-> Structure evaluation
-> Redundant Control Nodes
-> Model-validity diagnostics
-> Human Review
-> Final results
```

## Workspace map

| Path | Purpose | Edit policy |
| --- | --- | --- |
| `manifests/source_manifest.json` | Immutable source paths, hashes, format, language, and source commit for 47 cases | Regenerate only from the raw source repository |
| `manifests/generated_manifest.template.json` | Explicitly unresolved template for an immutable 47 x 3 generated-model cohort | Copy and complete only after the cohort configuration is frozen |
| `core.py` | EvalGraph, metrics, hashing, and dependency-free graph utilities | Evaluation code |
| `adapters.py` | inubit `.diagram.zip`, ProcessEditor `.model`, and ActivityGraph JSON conversion | Evaluation code |
| `action.py` | Explicitly configured semantic one-to-one Action matching | Evaluation code |
| `flow.py` | Non-redundant matched-action precedence scoring | Evaluation code |
| `structure.py` | Atomic exclusive, parallel, and loop behavioral facts | Evaluation code |
| `diagnostics.py` | Redundant-control and separate model-validity diagnostics | Evaluation code |
| `human_review.py` | Review queue, validation, and review-adjusted sensitivity logic | Evaluation code |
| `runner.py` | Immutable end-to-end evaluator and provenance writer | Evaluation code |
| `results/` | Documentation for generated result runs; actual run directories go here | Never manually edit generated run files |
| `tests/` | Synthetic deterministic tests; no model downloads or APIs | Test code |

## Input and output boundary

**Source inputs** are the process descriptions and reference BPMN/ProcessEditor
models named by `source_manifest.json`. **Generated-system inputs** are all three
ActivityGraph JSON candidates for every case, named by a separate generated manifest.
`candidate_1`, `candidate_2`, and `candidate_3` indicate generation order only, never
quality. The supplied template deliberately has cohort `UNRESOLVED` and cannot be evaluated.

Each successful run creates exactly six derived files in a new immutable directory:

* `candidate_summary.csv`: 141 candidate-slot rows with generation status, attempt
  count, optional failure evidence, and metrics for successful candidates. Failed
  candidates remain present with blank/NA metric fields, never substituted zeros.
* `case_summary.csv`: 47 rows with complete/incomplete/failed status. Primary arithmetic
  mean/minimum/maximum fields are populated only for complete 3/3 cases; successful
  outputs from incomplete cases appear only under explicitly secondary fields.
* `automatic_items.jsonl`: Action correspondences, Flow relations, Structure facts,
  diagnostic candidates, candidate identity, evidence, and every automatic label.
* `human_review.csv`: deterministic ambiguity triggers, unsupported items,
  redundancy candidates, generation failures, and a deterministic TP audit sample.
* `aggregate_summary.json`: separate generation reliability and model-quality sections,
  complete-case primary macro denominators, complete-case variability, secondary
  successful-output micro aggregates, diagnostics, review categories, and optional
  nested review-adjusted sensitivity.
* `provenance.json`: exact manifest hashes, cohort, evaluator commit/state, Python,
  Action model configuration, threshold, and review seed.

These six files are derived and safe to regenerate into a **new** run directory.
They must not be manually edited, except that `human_review.csv` may be copied out,
completed by reviewers, and supplied to a later sensitivity run with `--review-file`.
Raw automatic scores always remain primary; review-adjusted scores never replace them.

The generation and evaluation unit is one `(case_id, candidate_id)` model. Candidate
observations total 141, but they are nested within 47 process descriptions. The primary
reporting/statistical unit is therefore the Friedrich case (`N = 47`), not `N = 141`.

## Metric rules

Action uses one-to-one semantic matching. The embedding model,
immutable model revision, local cache, and threshold are all required CLI inputs;
V2 does not load old cached correspondences.

The frozen small-validation Action configuration was recovered from the original
35-pair Friedrich calibration pilot (29 text-only eligible pairs):

* model `sentence-transformers/all-MiniLM-L6-v2`;
* revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`;
* L2-normalized embeddings and cosine-equivalent dot product;
* inclusive threshold `0.44`;
* lexicographic assignment: maximum threshold-eligible cardinality first, then
  maximum total semantic similarity.

The V2 matcher uses the original full normalized labels. It does not import the later
V1 linguistic-operation guards or topology-assisted correspondence rules. The recovered
CPU dependency pins are in `requirements-action.txt`; real runs load the immutable model
revision from a supplied local cache without downloading it.

Action correctness is semantic rather than exact-string based. Longer paraphrases may
match when the frozen matcher places them at or above `0.44`. Exact duplicate normalized
reference labels alone use graph precedence to align comparable occurrences. Parallel or
otherwise incomparable duplicates retain deterministic assignments but are marked
occurrence-ambiguous. Raw split/combined disagreements remain one-to-one FP/FN; possible
one-to-many or many-to-one clusters are sent to Human Review without partial credit.

Flow projects reachability onto matched actions and deterministically removes
transitive relations. Unmatched generated actions remain traversable, so `A -> X -> B`
can preserve reference precedence `A -> B`. Cyclic ordering belongs to Structure,
and parallel siblings do not become precedence facts.

Flow precision/recall/F1 is conditional on matched Action anchors. Reference fact
coverage uses the transitive reduction over all reference Actions as its denominator
and counts only facts whose two endpoints are matched; an empty denominator has coverage
`1.0`. Action-anchor coverage is reported separately, as are facts depending on
occurrence-ambiguous, contested, or Human-Review-pending anchors. No coverage-weighted
F1 is produced.

Structure compares equally weighted atomic behavioral facts: mode, one fact per
branch, convergence/synchronization, and loop body/exit. It does not compare exact
gateway IDs or whole-region topology. Internal sequential order remains a Flow concern.
Mode identity is independent of the exact convergence continuation where possible;
branch and convergence differences remain separate facts. Topology-level mode facts are
always extracted, control-node labels never become Actions, and anchor-dependent facts
are marked `anchor_limited`. Structure anchor coverage is reported separately.
When both exclusive regions provide complete, unique, identically normalized guard
vocabularies, guard-to-branch-outcome mappings are additional Structure facts. Reversed
outcomes therefore reduce raw Structure credit. Missing, duplicated, differently worded,
or otherwise non-comparable guards remain unscored and are retained as review evidence.

Behaviorally neutral control nodes are excluded from Structure F1 and reported as
**Redundant Control Nodes**. Automatic candidates require unchanged Action
reachability and Structure facts after contraction. Every candidate still requires
Human Review; low-confidence UML/BPMN notation differences are never auto-confirmed.

Automatic evaluation consists of raw Action, conditional Flow, and behavioral Structure
scores. Human Review is targeted to deterministic uncertainty such as contested or
duplicate Action correspondence, split/combined granularity, ignored BPMN-specific
evidence, task/control interpretation, anchor-limited Structure, and guard/outcome or
scope ambiguity. Model-validity and redundant-control findings remain separate
diagnostics and do not form another F1.

Every triggered automatic item receives its own candidate-aware review row. Conceptually
equivalent rows share a deterministic cluster id and carry the complete cluster member
inventory, allowing one adjudication to propagate without losing candidate/item identity.

Human Review rows always retain both `case_id` and `candidate_id`. Review adjustments
are applied to each candidate first, then summarized across three candidates per case,
then macro-averaged across 47 cases. No global count subtraction replaces this nesting.

Reviewers classify source scope as `in_scope_executable_action`, `trigger_event`,
`precondition`, `postcondition`, `out_of_scope_interaction`, or
`reference_only_modelling_addition`. A deviation may be accepted only when the source
text explicitly states or logically entails it and it does not remove required behavior,
introduce an unsupported alternative, impose unsupported ordering, or reverse a required
branch outcome. Ambiguity permits multiple reasonable interpretations, not every one.

Normalized branch guards are preserved as evidence. Clearly comparable guard mappings
contribute raw Structure facts; missing, duplicate/conflicting, non-comparable, and
reference-inconsistent mappings remain deterministic review evidence. The evaluator does
not use an LLM guard scorer or automatically adjudicate unsafe semantics.

Model-validity diagnostics inventory unreachable nodes, disconnected components,
non-final dead ends, initial/final and final-reachability anomalies, cycles without exits,
actionless branches, malformed gateway degrees or fork/join pairing, guard issues, and
likely duplicate generated Actions. Status/count reporting is separate from primary F1;
a behavioral defect may additionally appear as a Structure error.

## Generation failures

Each permanent candidate slot may receive at most three complete top-level generation
attempts in the future cohort-generation process. Built-in pipeline planning, correction,
repair, deterministic compilation, and validation remain inside one top-level attempt.
The slot stops at its first valid ActivityGraph and keeps the same `candidate_id` across
attempts. A valid but poor model is a success and must not be retried based on evaluation.

The evaluator performs no generation and no retry. It consumes a frozen v3 manifest:

* `generation_status=success` requires one to three ordered attempts ending at the
  first success, plus an existing ActivityGraph path and matching SHA-256.
* `generation_status=failed` requires three failed attempts, a final failure reason,
  and null artifact path/hash. Action, Flow, and Structure are not applicable.
* `maximum_attempts_per_candidate=3` and `run_integrity_status=valid` are mandatory.
  A cohort-wide authentication, configuration, runtime, or storage failure must pause
  or invalidate the run instead of becoming 141 candidate failures.

A case is complete only with 3/3 successful candidates. Cases with one or two successes
are incomplete; cases with no successes are failed. Only complete cases enter primary
model-quality macro scores and variability. Aggregate reliability reports expected,
successful, and failed candidates; success rate; complete/incomplete/failed cases;
complete-case rate; and success/failure counts by attempt. Successful outputs from
incomplete cases remain available only as conditional secondary descriptions.

Every failed slot creates one candidate-aware `Generation` audit row with attempt
evidence. It creates no Action/Flow/Structure FP/FN and cannot change review-adjusted
model-quality counts. Generation audit rows leave disagreement explanation categories
blank; generation reliability and model quality are never combined into one score.

## Unsupported semantics and coverage

Inclusive/complex gateways and combined converging-diverging gateways are retained
as `unsupported_control` nodes. Action remains scorable; the current conservative
policy marks Flow and Structure unscorable for that case rather than silently
converting uncertain semantics. Coverage is reported.
Case `7-1` is parsed directly from its ProcessEditor `.model`; its inclusive gateway
is therefore explicit and unscorable for affected behavioral metrics.

## Running

No generated cohort is selected yet. After creating and validating a generated V2
manifest, run from the repository root with all parameters explicit:

```bash
python3 -m evaluation.friedrich_v2.runner \
  --source-manifest evaluation/friedrich_v2/manifests/source_manifest.json \
  --generated-manifest /absolute/path/generated_manifest.json \
  --output-dir evaluation/friedrich_v2/results/<new-run-id> \
  --action-model <model-name> \
  --action-model-revision <immutable-revision> \
  --action-threshold <validated-threshold> \
  --model-cache /absolute/path/to/local/model-cache
```

The runner performs no generation or API calls. A model library may read/download a
model only according to the explicitly supplied cache/model configuration; for a
frozen run, pre-populate the cache and use an immutable model revision.

## Cohort archive

Generated artifacts remain outside result runs and should be archived immutably:

```text
cohort/
├── generated_manifest.json
└── cases/<case_id>/<candidate_id>/
    ├── activity_graph.json
    ├── raw_generation_response.json
    └── stage_artifacts.json
```

The manifest hashes the evaluated `activity_graph.json` for every successful candidate and records
the cohort stage, AI-only condition, system commit, profile/configuration, model,
runtime, retry/failure policy, expected count of three, and `human_selection=false`.
All three candidates must remain archived even if their scores differ.

Attempt records are stored inside each candidate manifest record with ordered
`attempt_index`, `attempt_status`, and optional failure reason, stage, or evidence.
Failed candidate directories may preserve attempt evidence without containing an
`activity_graph.json`; successful candidates archive the first valid graph only.

## Reuse boundary

V2 reimplements the methodologically neutral legacy foundations: normalized labels,
EvalGraph validation, reference format interpretation, reachability, and SCC logic.
It does not import legacy code and does not reuse strict whole-region scoring,
calibration outputs, thresholds, score files, manifests, checkpoints, or reviews.

Before the small validation run, freeze its generated-system model identifier,
runtime description, retry/failure policy, artifact capture procedure, Action embedding
model revision, and threshold. The current stable system commit may remain labelled as
a development/evaluation baseline until the final baseline decision is made.

## Small-validation generation

`generation.py` owns three permanent candidate slots independently of the backend. It
invokes the unchanged `/api/v1/generate-model` endpoint once per attempt with
`mode=baseline` and `pipeline_profile=semantic_deterministic`. Baseline mode is used here
only because it returns exactly one model from the same semantic-deterministic generation
pipeline; refinement mode hardcodes an all-or-nothing three-model batch.

Each slot stops at the first adapter-valid ActivityGraph or becomes failed after exactly
three unsuccessful attempts. Atomic generation state is written after every attempt, so
resuming skips every already-terminal slot. The driver never loads references, evaluator
scores, or Human Review data and therefore cannot implement best-of-three selection.
Process texts are decoded as UTF-8 with a deterministic Windows-1252 fallback for legacy
Friedrich files that are not UTF-8 encoded.

After explicit approval to generate, the frozen driver command is:

```bash
python3 -m evaluation.friedrich_v2.generation \
  --config evaluation/friedrich_v2/config/small_validation_config.json \
  --source-manifest evaluation/friedrich_v2/manifests/source_manifest.json \
  --generation-worktree /absolute/path/to/the/frozen-generation-worktree
```

Generated cohort directories are runtime artifacts and must not be committed. Evaluate
the resulting five-case manifest with `--small-validation-config`; omitting that option
retains the full 47-case behavior.
