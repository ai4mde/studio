# Step 8 — Customer.reading_plan End-to-End (second integration milestone)

**Result: PASS (8A split gate + 8B deterministic chain + 8C real provider).** Calling
`customer.generate_reading_plan()` drives the full runtime through a _different_ applicability
cell than Step 7: a **user-action** trigger (M07) → plain-function bound method → an **M04
prompt chain** (`analyze_taste → recommend → sequence`), each step rendering a declared prompt
template (M01) → routing to the **strong** model (M06) → parsing structured output (M03), with
the chain grounded in the member's real borrow history pulled from the generated ORM (M02) →
the compact plan written back to `Customer.reading_plan` (M07 write-back) → a full chain trace
logged. The generated `late_risk` path (`ai_hooks.py`, the `BookLoan` model block) is
byte-identical to Step 7 — the trigger split added a parallel user-action path without
disturbing the post_save path.

## Claim demonstrated

_A second, orthogonal application feature (a personalized reading plan) is produced end-to-end
by reusable mechanisms driven by declarative `ai_config` (M05) — covering an applicability cell
deliberately distinct from Step 7._ This is the first time **M04 Prompt Chaining** fires inside
the generated application, and the first time a **user-action** trigger and a **multi-step**
invocation are demonstrated. Together with Step 7 this substantiates the RO1/RO3 claim that the
catalogue covers more than one integration shape, each with real-provider evidence.

### Applicability cells covered (RO1 / RO3 evidence)

| Dimension       | Step 7 — `BookLoan.late_risk`    | Step 8 — `Customer.reading_plan`   |
| --------------- | -------------------------------- | ---------------------------------- |
| Trigger (M07)   | event-driven `post_save`         | `user_action` (bound method)       |
| Invocation      | single shot                      | M04 chain (3 steps)                |
| Model (M06)     | cheap → Groq                     | strong → OpenAI                    |
| Grounding (M02) | field enrichment of one row      | aggregate borrow-history traversal |
| Output (M03)    | constrained label (LOW/MED/HIGH) | structured plan → compact summary  |
| Character       | passive field enrichment         | active personalized workflow       |

The two cells share the same vendored mechanism kernel and the same declarative `ai_config`
surface; only the declared trigger/template/profile differ.

## Scope (boundary preserved)

Shell-level end-to-end only. The member-facing **UI button** (a member triggers
`generate_reading_plan` in the browser) is **deferred to 8D** so UI concerns cannot block the
mechanism evidence. The generated `librarian` interface is unchanged and carries no
`reading_plan` page.

## Architecture realized

### Generator: trigger-type split + decoupled emission gates

The Step-7 generator treated every `ai_config` attribute as a `post_save` hook. Step 8 splits
`ai_managed` by `trigger.type`:

- `post_save` items → `shared_models/ai_hooks.py` (**unchanged**, late_risk)
- `user_action` items → `shared_models/ai_actions.py` (**new**), attaching a plain-function
  bound method `Customer.generate_reading_plan = generate_reading_plan` via `apps.ready()`.

Emission was decoupled into three independent gates — `if has_hooks` (ai_hooks.py),
`if has_actions` (ai_actions.py), `if has_hooks or has_actions` (apps.py + the `ai_runtime`
package) — so the runtime is no longer coupled to the post_save mechanism. The apps template
imports each glue module conditionally. For this app both flags are true, so the late_risk
output is unaffected; the decoupling makes the "mechanisms are independent" claim true in code.

### M04 vendored (A-lite, extends Step 7)

| `ai_runtime/` file                                                       | Mechanism               | Origin                                                                |
| ------------------------------------------------------------------------ | ----------------------- | --------------------------------------------------------------------- |
| `chains.py`                                                              | **M04 Prompt Chaining** | **vendored** (pure Python) from `llm/chains/base.py`, django-stripped |
| `reading_plan.py`                                                        | M04 orchestration + M02 | **generated** (3 schemas, 3 `ChainStep`s, `_build_taste_context`)     |
| `templates.py`                                                           | M01 (registry extended) | **vendored** + 3 reading_plan entries added                           |
| `parsers.py`                                                             | M03 Structured Output   | **vendored** (unchanged from Step 7)                                  |
| `routing.py`                                                             | M06 Model Routing       | **generated** (`_fake_content` widened to a superset)                 |
| `prompt_templates/reading_plan_{analyze_taste,recommend,sequence}_v1.j2` | M01-in-M04              | **new**                                                               |

The vendored `chains.py` contains no `llm`/`django` reference — its only framework coupling
(`settings.LLM_STORE_CHAIN_TRACE`) was rewritten to an environment read. The extraction was
limited to one module and an import-namespace change; no chain logic was altered. This low
extraction cost is further RO2 evidence for the framework-neutral claim, now for a
multi-step mechanism.

## Per-DoD outcome

| DoD condition                                                                                       | Outcome | Evidence                                                |
| --------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------- |
| `generate_models.py` diff = split + decoupled gates + actions/ai_actions + reading_plan/chains only | PASS    | `step8_generate_models.diff`                            |
| 8A split: `reading_plan` generated, `user_action` detected, NO `sender=Customer` post_save hook     | PASS    | `step8_generate.log`, `step8_app_ai_hooks.py`           |
| late_risk regression: `ai_hooks.py` + `BookLoan` block byte-identical to Step 7                     | PASS    | `step8_verify.log`                                      |
| `templates.py` registers the 3 reading_plan prompts                                                 | PASS    | `step8_app_ai_runtime_templates.py`, `step8_verify.log` |
| vendored `chains.py` pure Python (no `llm`/`django`)                                                | PASS    | `step8_app_ai_runtime_chains.py`, `step8_verify.log`    |
| `ai_actions.py` attaches a bound method (not staticmethod)                                          | PASS    | `step8_app_ai_actions.py`, `step8_verify.log`           |
| M02 substrate: chain consumes the member's real borrow history                                      | PASS    | `[smoke] M02 substrate OK` marker (8B + 8C)             |
| 8B deterministic chain end-to-end + write-back ≤255                                                 | PASS    | `step8b_smoke.log`, `step8b_ai_invocations.jsonl`       |
| 8C real-provider (strong → OpenAI) chain end-to-end + write-back ≤255                               | PASS    | `step8c_smoke.log`, `step8c_ai_invocations.jsonl`       |

## End-to-end evidence

### 8B — deterministic (fake mode, no network)

`AI_RUNTIME_FAKE=1`. The M02 context builder returned exactly the three seeded books
(`Dune`, `Foundation`, `Neuromancer`); one `event=invoke_chain` record with three
`step_details` (`analyze_taste → recommend → sequence`), each `success=true`; the superset fake
content satisfies all chain schemas simultaneously; `reading_plan` written to a 31-char summary.

```
[smoke] M02 substrate OK: 3 borrowed books -> ['Dune', 'Foundation', 'Neuromancer']
[smoke] reading_plan='1) Book A; 2) Book B; 3) Book C'
[smoke] PASS: user_action -> M04 chain (analyze_taste -> recommend -> sequence) -> reading_plan written (31 chars, mode=fake)
[DONE] Step 8 reading_plan chain end-to-end VERIFIED.
```

Chain record (single `invoke_chain` line, `status=success`, `mode=fake`, 3 `step_details`):

```json
{
  "event": "invoke_chain",
  "trigger": "user_action",
  "model": "Customer",
  "pk": 1,
  "model_profile": "strong",
  "mode": "fake",
  "write_back": {
    "field": "reading_plan",
    "value": "1) Book A; 2) Book B; 3) Book C"
  },
  "status": "success",
  "failed_step": null,
  "step_details": [
    {
      "step": "analyze_taste",
      "prompt_name": "reading_plan_analyze_taste_v1",
      "output_key": "taste",
      "success": true
    },
    {
      "step": "recommend",
      "prompt_name": "reading_plan_recommend_v1",
      "output_key": "recommendation",
      "success": true
    },
    {
      "step": "sequence",
      "prompt_name": "reading_plan_sequence_v1",
      "output_key": "plan",
      "success": true
    }
  ],
  "ai_config_version": "1.0"
}
```

(`model_profile=strong` with `mode=fake` is expected: the profile is the declared routing
target; fake mode short-circuits the network call. `step_details.raw_response` carries the
superset fake JSON for each step — omitted here for brevity, present in
`step8b_ai_invocations.jsonl`.)

### 8C — real provider (strong → OpenAI)

`OPENAI_API_KEY` injected from the gitignored `config/secrets.env` (aliased from `OPENAI_KEY`),
`openai` 2.44.0 temporarily installed in the prototypes venv. The borrow-history setup is forced
into fake mode (try/finally), so the late_risk `post_save` fired during setup makes no real Groq
call; only the reading_plan chain runs real. The model kept the genuinely-borrowed titles and
produced a sequenced plan:

```
[smoke] M02 substrate OK: 3 borrowed books -> ['Dune', 'Foundation', 'Neuromancer']
[smoke] reading_plan='1) Dune; 2) The Left Hand of Darkness; 3) Neuromancer'
[smoke] event=invoke_chain status=success mode=real steps=3
[smoke] PASS: user_action -> M04 chain (analyze_taste -> recommend -> sequence) -> reading_plan written (53 chars, mode=real)
[DONE] Step 8 reading_plan chain end-to-end VERIFIED.
```

The real chain consumed the member's actual borrow history (M02) and emitted a 53-char
write-back (≤255), demonstrating the full M02 → M04 → M01/M03 path under a real strong model.

### Convergence

```
[PASS] 8C real strong-model chain verified
[PASS] Step 8 verified: M04 user-action chain produces reading_plan end-to-end; late_risk post_save path unchanged vs Step 7
```

## Mechanisms exercised

M05 (declarative `ai_config`) · M07 (user-action trigger + write-back) · **M04 (prompt chain)**
· M01 (per-step templates) · M02 (borrow-history grounding) · M03 (structured parse) · M06
(strong → OpenAI routing). Combined with Step 7, the catalogue subset M01–M07 is now
demonstrated across two distinct applicability cells with real-provider evidence.
