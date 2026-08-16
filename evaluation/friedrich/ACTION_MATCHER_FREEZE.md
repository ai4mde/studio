# Friedrich Action matcher freeze

## Freeze identity

- Version: `friedrich-action-matcher-v1.0.0`
- Freeze date: `2026-08-16`
- Branch: `feature/friedrich-evaluation`
- Production-system base: `e1d576c6bdf181a79dd9649f207f7fad4f89d714`
- Revised matcher SHA-256:
  `ab604fafbd51b679af7c1fb6de1c96302c07bc9c08a1051b89f3e800b8e3dde7`

This version is frozen for formal Friedrich evaluation. Formal evaluation
outcomes must not be used to change thresholds, matching rules, operation
families, normalization, topology behavior, or ambiguity handling. Reopening is
allowed only for a documented correctness defect or major systematic execution
failure, never merely to improve Precision, Recall, or F1.

## Frozen configuration

- Deterministic label normalization:
  `evaluation.friedrich.eval_graph.normalize_label`
- Semantic threshold: `0.44`
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Model revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- Semantic score: maximum of original full-label cosine and canonical
  operation/object-label cosine
- Operation compatibility: the frozen small conflict map in
  `evaluation.friedrich.action_matching`; no additional operation threshold
- Linguistic normalization: dependency-root verb lemmatization plus unique
  WordNet noun-to-verb derivation; ambiguous or missing derivations remain
  unresolved rather than being guessed
- One-to-one semantics: deterministic maximum-weight bipartite optimization
- Topology activation: only when the remaining reference node has multiple
  generated candidates or the generated node has multiple competing references
- Topology evidence: nearest already-matched predecessor/successor actions,
  traversing routing/control nodes only; rank by corresponding anchor count,
  path-distance difference, then semantic score; accept only a unique reciprocal
  winner
- Invalid-candidate safety: topology and assignment cannot admit below-threshold
  or operation-incompatible candidates
- Assignment ambiguity: accept only edges present in every numerically equivalent
  optimal assignment; preserve the interchangeable residual component as
  unresolved
- Assignment objective equality: `numpy.isclose(rtol=1e-5, atol=1e-8)`; this is
  a numerical reproducibility tolerance, not a semantic threshold
- Formal unresolved policy: unresolved reference nodes remain unmatched and are
  counted as FN; unresolved generated nodes remain unmatched and are counted as
  FP; unresolved component counts are reported separately

## Runtime dependencies

- Python `3.12.13`
- `sentence-transformers==5.7.0`
- `torch==2.13.0`
- `transformers==5.15.0`
- `numpy==2.5.2`
- `scipy==1.18.0`
- `spacy==3.8.14`
- `en-core-web-sm==3.8.0`
- `nltk==3.10.0`
- WordNet archive SHA-256:
  `cbda5ea6eef7f36a97a43d4a75f85e07fccbb4f23657d27b4ccbc93e2646ab59`

The executable dependency declaration is `requirements-calibration.txt`.
Evaluation runners set a fixed Torch seed, use CPU execution with one Torch
thread and deterministic algorithms, disable model telemetry, normalize
embeddings, and sort labels, candidates, and node IDs before deterministic
assignment.

## Source hashes

- `action_matching.py`:
  `9bab1ea7ed3c6eeb143c812bd1bb661eae875471295428649e32f1936422d164`
- `revised_action_matching.py`:
  `ab604fafbd51b679af7c1fb6de1c96302c07bc9c08a1051b89f3e800b8e3dde7`
- `linguistic_operations.py`:
  `83549846323b9d2216d590165f51836484e7bf099458149e5eece6fda4b5cd63`
- `eval_graph.py`:
  `ae7828914d979c83ee6e7923eaa5df06022120f8a00818ee04051b7d2136f9e8`
- `requirements-calibration.txt`:
  `3856272bc96ef7767870694bdd64d2df2dec2aaa430ef058862572174b4bd1d5`

## Protected evidence hashes

- Frozen pilot annotations:
  `5d0b01e8ed28032f7904c72d6a4e5517e82fc276f73f0d617f5d680b348494a1`
- Original action similarity evidence:
  `bf6fea332902e99dbdcd32db63963da63484fa78a2ee8e9fa07e36c8d98e0e6b`
- Frozen development annotations:
  `4e5ea31e8d18690edb9891a35d1ecb4d4de748460e0d5128d23b245e1d989c6e`
- First held-out reviewed matches:
  `c9b79287baee181dce679858c4a37c3275d45e754eb829faf710ad92b7a21900`
- First held-out missed matches:
  `2bfdeb8a3b3f9caf6dcb2a2263a9ba105ae21f188603f251a2007a1855907637`
- Previous untouched raw results:
  `7e3777a12e8a1ee812ded94124258b3a4c7aefc616f77c8148ea6595d849a496`
- Previous untouched manual review:
  `cd04a0c65b3a3a1e7715539a0abf44724889ba4939879d3633968ce42c4da1b9`
- Final untouched raw results:
  `081f021482c40f30941a12541f97cd11989477735b170551672f52fcf0285931`
- Final untouched manual review:
  `887ab0113a28487a4ab06ac469be3097a24068fdfe9b1381a4ef5a95928c67c6`

## Validation outcome

The unresolved-assignment regression retained all 33 manually correct
correspondences and replaced four false forced correspondences with one explicit
unresolved component. Corrected behavior therefore favors honest lower coverage
over arbitrary one-to-one completion. See `topology_activation_regression.json`
and `unresolved_assignment_regression.json` for the audit records.

## Known limitations

- Semantically related lifecycle stages can still be confused when they share
  business objects, such as registration/submission, creation/sending, or
  receiving/rejecting.
- Sparse labels and source-model wording errors can reduce embedding quality.
- WordNet does not provide every defensible domain-specific noun/verb relation;
  missing or ambiguous derivations intentionally remain unresolved.
- Granularity differences between combined and split actions are reported but
  are not repaired by the matcher.
- Local predecessor/successor topology is deliberately limited and is not full
  graph isomorphism.
- Conservative unresolved scoring may lower Precision/Recall compared with
  silently excluding difficult components; this is intentional and must not be
  changed based on formal evaluation results.

These are documented evaluator limitations. They must not be addressed with
case IDs, literal-label exceptions, expanded synonym lists, new operation
families, or additional calibrated thresholds during formal evaluation.
