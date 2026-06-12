## Semantic Rule Inventory

| Rule | Current Location(s) | Duplicated? | Contradictory? | Enforced or Suggested? | Recommended Canonical Ownership |
| --- | --- | --- | --- | --- | --- |
| Decision branches should normally produce at least two outgoing branches | `api/model/llm/topology_analysis.py`, `api/model/llm/sketch_alignment.py`, prompt templates | Yes | No | Heuristic in diagnostics, suggested in prompts | clean semantic validator or explicit topology rule catalog |
| Decision branches should use outgoing branch labels | `activity_baseline_prompt.jinja`, `activity_refinement_prompt.jinja`, `topology_analysis.py`, tests | Yes | No | Suggested in prompts, heuristic in diagnostics | clean semantic validator / topology policy |
| Decision with planned closure should reconnect via merge | `activity_baseline_prompt.jinja`, `activity_sketch_prompt.jinja`, `sketch_alignment.py`, tests | Yes | No | Suggested in prompts, heuristic in alignment | planner + clean semantic validator |
| Parallel split should use fork | `activity_baseline_prompt.jinja`, `sketch_alignment.py` | Yes | No | Suggested in prompt, heuristic in alignment | planner + clean semantic validator |
| Parallel branches with planned closure should reconnect via join | `activity_baseline_prompt.jinja`, `activity_sketch_prompt.jinja`, `sketch_alignment.py`, `topology_analysis.py`, tests | Yes | No | Suggested in prompt, heuristic in diagnostics | planner + clean semantic validator |
| Fork should have at least two outgoing branches | `topology_analysis.py` | No | No | Heuristic | clean semantic validator |
| Join should have at least two incoming branches | `topology_analysis.py` | No | No | Heuristic | clean semantic validator |
| Merge should have at least two incoming branches | `topology_analysis.py` | No | No | Heuristic | clean semantic validator |
| Loop / retry patterns should use backward edges | `activity_baseline_prompt.jinja`, `activity_sketch_prompt.jinja`, `sketch_alignment.py`, tests | Yes | No | Suggested in prompt, heuristic in alignment | planner + clean semantic validator |
| Retry loops should normally use `type=\"loop\"` in the plan | `activity_sketch_prompt.jinja` | No | No | Suggested | planner |
| Retry loops should normally use `requires_merge=false` | `activity_sketch_prompt.jinja`, `activity_sketch_model.py`, tests | Yes | No | Defaulted in planner model, suggested in prompt | planner |
| Do not add a merge merely because one loop branch returns backward | `activity_baseline_prompt.jinja`, `activity_sketch_prompt.jinja`, tests | Yes | No | Suggested in prompts, indirectly tested through alignment semantics | planner + clean semantic validator |
| Loops must include an exit path | `activity_baseline_prompt.jinja`, `sketch_alignment.py` | Yes | No | Suggested in prompt, heuristic in alignment | clean semantic validator |
| Branches marked `returns_to_main_flow=true` should reconnect to main flow | `activity_baseline_prompt.jinja`, `sketch_alignment.py` | Yes | No | Suggested in prompt, heuristic in alignment | planner + alignment diagnostics |
| `exit_to` should reconnect to a specific later main-flow action | `activity_sketch_prompt.jinja`, `activity_baseline_prompt.jinja`, `sketch_alignment.py` | Yes | No | Suggested in planner/realizer prompts, heuristic in alignment | planner |
| `entry_after` / `exit_to` / `loop_back_to` action references should map to realized actions | `sketch_alignment.py` | No | No | Heuristic | planner/alignment diagnostics |
| Model must have one initial node | `activity_baseline_prompt.jinja`, `activity_refinement_prompt.jinja`, `topology_analysis.py` | Yes | Slightly: prompt says one initial, analysis flags zero or multiple | Suggested in prompts, heuristic in diagnostics | clean structural validator |
| Model must have at least one final node | `activity_baseline_prompt.jinja`, `activity_refinement_prompt.jinja`, `topology_analysis.py` | Yes | No | Suggested in prompts, heuristic in diagnostics | clean structural validator |
| Every edge must connect valid node ids | prompts, `activity_model.py`, converter validation, tests | Yes | No | Hard-enforced in clean validator and converter | clean structural validator |
| Node ids must be unique | prompt templates, `activity_model.py` | Yes | No | Hard-enforced in clean validator | clean structural validator |
| Use `name` for action nodes | prompt templates, `normalization.py`, `activity_model.py`, converter, tests | Yes | Slightly: native export also duplicates text into `label`/`name` for some node types | Suggested in prompts, enforced indirectly through normalization and consumer expectations | clean artifact contract |
| Decision node text may live on node `label` | refinement prompt, `activity_model.py`, converter, tests | Yes | Yes: converter also mirrors decision text into `name` | Suggested in prompt, operationalized in converter | clean artifact contract + converter mapping note |
| Edge `condition` must not be silently converted into `label` | `normalization.py`, tests | Yes | No | Hard-enforced by normalization behavior | normalization |
| Clean edge type aliases should normalize to `control` / `object` | `normalization.py`, tests | Yes | No | Hard-enforced | normalization |
| Native export relation types should be `controlflow` / `objectflow` | `converter.py`, metadata activity relations, tests | Yes | No | Hard-enforced in converter/export validation | converter / native export validation |
| Object-flow edges should carry the related object classifier id in native export | `converter.py`, tests | Yes | No | Hard-enforced in converter | converter |
| Decision semantic text should survive conversion to native export | `converter.py`, tests | Yes | Slightly: duplicated into both `name` and `label` | Hard-enforced by converter behavior | converter |

## Contradictions and Tensions

1. `ActivityGraph` clean semantics prefer clearer separation between node `label`, action `name`, edge `label`, and edge `condition`, but native AI4MDE export expects some control nodes to carry both `name` and `label`.
2. `validation` naming is overloaded.
   Structural graph checks, heuristic topology checks, sketch alignment checks, and export-shape checks all read like authoritative validators.
3. The sketch prompt and baseline prompt define several topology rules that are not hard-enforced anywhere in clean validation.
4. The handler sketch schema is not fully aligned with planner semantics because `loop_back_to` exists in the `ActivitySketch` Pydantic model and prompt but not in the structured-output schema definition.

## Duplication Hotspots

1. Decision/merge semantics:
   prompts, `sketch_alignment.py`, `topology_analysis.py`, tests.
2. Parallel/fork/join semantics:
   prompts, `sketch_alignment.py`, `topology_analysis.py`, tests.
3. Loop semantics:
   sketch prompt, baseline prompt, `ActivitySketch` defaults, `sketch_alignment.py`, tests.
4. Label/name/condition vocabulary:
   prompts, normalization, converter, metadata activity relations, tests.

## Recommended Ownership Model

1. `Planner` should own plan-level semantics:
   control block kinds, `requires_merge`, `returns_to_main_flow`, `exit_to`, `loop_back_to`.
2. `Clean structural validator` should own hard graph integrity:
   id uniqueness, valid endpoints, required top-level shape, possibly start/end cardinality.
3. `Clean semantic validator` should eventually own hard graph semantics:
   branch counts, merge/join expectations, loop exit requirements.
4. `Diagnostics` should own heuristic and audit-oriented reporting:
   topology issue summaries, drift analysis, coarse stability metrics.
5. `Converter` should own only deterministic mapping into native AI4MDE schema.
6. `Native export validator` should own exact Studio payload shape.

## Stabilization Takeaway

The semantic rules already exist; the main issue is not absence but distribution. They are currently split across prompts, diagnostics, normalization, converter behavior, and tests, with different enforcement strengths. The next stabilization step should be to declare one canonical ownership location per rule category before any refactoring or behavior changes are attempted.
