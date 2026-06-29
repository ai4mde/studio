# Step 7 — BookLoan.late_risk End-to-End (first integration milestone)

**Result: PASS (7A deterministic + 7B real provider).** Creating a `BookLoan` drives the full
runtime: `post_save` (M07) → generated hook → `ai_runtime.invoke` → build context from the
generated ORM (M02) → render the declared prompt template (M01) → route by `model_profile`
(M06) → parse the structured output (M03) → return the value → the existing hook writes
`late_risk` (M07 write-back) → a full invocation trace is logged. The generated event glue
(`ai_hooks.py`), domain model (`models.py`), and wiring (`apps.py`) are byte-identical to
Step 5C; only `ai_runtime` changed — from the Step 6 router (returned `None`) to the full
runtime that returns a parsed value.

## Claim demonstrated

_A real application feature (late-return risk) is produced end-to-end by reusable mechanisms
driven by declarative `ai_config` (M05) — not by per-feature glue._ This is the first RO4
case-based demonstration and the first time **M01+M02+M03+M05+M06+M07** fire together inside
the generated application.

## Scope (boundary preserved)

Shell-level end-to-end only. The librarian **page-layer** demo (create a `BookLoan` in the
browser, see `late_risk`) is **deferred to a follow-on (7C)** so UI issues cannot block the
mechanism evidence.

## Architecture realized: A-lite vendoring

studio-prototypes mounts only `./prototypes` (not `./api`), so the generator cannot read
`api/model/llm/` at generation time. The minimal mechanism subset was therefore vendored once,
author-side, into generator assets and copied into the generated app:

| `ai_runtime/` file                         | Mechanism                     | Origin                                                              |
| ------------------------------------------ | ----------------------------- | ------------------------------------------------------------------- |
| `templates.py`                             | M01 Template-Driven Prompt    | **vendored** (pure Python) from `llm/templates/{registry,renderer}` |
| `parsers.py`                               | M03 Structured Output Parsing | **vendored** (pure Python) from `llm/parsers/{base,json_parser}`    |
| `routing.py`                               | M06 Model Routing             | **generated** (Step 6 router relocated)                             |
| `context.py`                               | M02 Retrieval/grounding       | **generated** (Library-specific ORM traversal)                      |
| `__init__.py` (`invoke`)                   | orchestration                 | **generated**                                                       |
| `prompt_templates/library_late_risk_v1.j2` | M01 template                  | **new**                                                             |

The generated `ai_runtime/` package is self-contained at the **mechanism-code level**; the
import contract `from ai_runtime import invoke` is unchanged.

**Vendoring effort (RO2 evidence).** The vendored subset is the minimal A-lite set: M01
`templates.py` and M03 `parsers.py`. Both are pure Python — verified to contain no `llm`,
`import llm`, or `django` reference. The extraction was limited to **merging two modules each
into one file and removing the now-internal relative imports**; no mechanism logic was changed.
This low extraction cost (effectively an import-namespace change) is the operational evidence
for the framework-neutral claim: the mechanism kernel does not bind to AI4MDE internals and can
be carried into an independent application with minimal effort.

## Per-DoD outcome

| DoD condition                                                                                        | Outcome | Evidence                                                                          |
| ---------------------------------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------- |
| Only the §3 files changed; `ai_hooks.py.jinja2`/`models.py.jinja2`/`generator.sh`/`api/**` untouched | PASS    | `step7_generate_models.diff` (import os/shutil + ai_runtime materialization only) |
| `models.py`/`ai_hooks.py`/`apps.py` byte-identical to Step 5C                                        | PASS    | `step7_verify.log`                                                                |
| `ai_runtime/` is a package; vendored files free of `llm`/`django`                                    | PASS    | `step7_ai_runtime_tree.log`, `step7_app_ai_runtime_*`, `step7_verify.log`         |
| M01 template entered the generated runtime                                                           | PASS    | `step7_app_prompt_library_late_risk_v1.j2`                                        |
| 7A deterministic end-to-end + write-back                                                             | PASS    | `step7a_smoke.log`, `step7a_ai_invocations.jsonl`                                 |
| 7B real-provider end-to-end + write-back                                                             | PASS    | `step7b_smoke.log`, `step7b_ai_invocations.jsonl`                                 |
| `late_risk` written; mechanisms traced                                                               | PASS    | invocation records below                                                          |

## End-to-end evidence

### 7A — deterministic (fake mode, no network)

`AI_RUNTIME_FAKE=1`. One `event=invoke` record, `status=success`, context grounded from the
ORM, parsed `LOW`, `BookLoan.late_risk` written to `"LOW"`. Full record:

```json
{
  "timestamp": "2026-06-29T12:37:50.443344+00:00",
  "event": "invoke",
  "trigger": "post_save",
  "model": "BookLoan",
  "pk": 1,
  "model_profile": "cheap",
  "mode": "fake",
  "provider": "groq",
  "routed_model": "llama-3.3-70b-versatile",
  "template": "library_late_risk_v1",
  "context": {
    "book_title": "The Test Book",
    "author_name": "A. Writer",
    "customer_name": "C. Reader",
    "loan_date": "2026-01-01",
    "due_date": "2026-01-15",
    "return_date": ""
  },
  "raw_output": "{\"late_risk\": \"LOW\", \"reason\": \"fake deterministic response\"}",
  "parsed_output": "LOW",
  "write_back": { "field": "late_risk", "value": "LOW" },
  "status": "success",
  "error": null,
  "ai_config_version": "1.0"
}
```

Mechanism trace in this single record: `trigger=post_save` (M07); `context={...}` grounded from
the generated ORM (M02); `template=library_late_risk_v1` (M01); `model_profile=cheap →
provider=groq → routed_model=llama-3.3-70b-versatile` (M06); `raw_output → parsed_output=LOW`
(M03); `write_back={field:late_risk, value:LOW}` + `status=success` (M07 write-back).

### 7B — real provider (Groq)

`mode=real`, `model_profile=cheap → groq`. The same pipeline ran against the **real** provider;
`BookLoan pk=2` was assigned `late_risk='LOW'` and the smoke completed. Full record:

```json
{
  "timestamp": "2026-06-29T12:46:54.677523+00:00",
  "event": "invoke",
  "trigger": "post_save",
  "model": "BookLoan",
  "pk": 2,
  "model_profile": "cheap",
  "mode": "real",
  "provider": "groq",
  "routed_model": "llama-3.3-70b-versatile",
  "template": "library_late_risk_v1",
  "context": {
    "book_title": "The Test Book",
    "author_name": "A. Writer",
    "customer_name": "C. Reader",
    "loan_date": "2026-01-01",
    "due_date": "2026-01-15",
    "return_date": ""
  },
  "raw_output": "{\"late_risk\": \"LOW\"}",
  "parsed_output": "LOW",
  "write_back": { "field": "late_risk", "value": "LOW" },
  "status": "success",
  "error": null,
  "ai_config_version": "1.0"
}
```

This is the first verification of M03 against **real** model output. Here Groq returned clean
bare JSON (`{"late_risk": "LOW"}`) — no code fence, no extra keys — which `JsonOutputParser`
validated against the `Literal[LOW,MEDIUM,HIGH]` schema built from `ai_config.output.allowed_values`
(M05 → M03), `status=success`. Step 6B established that real Groq output can also arrive wrapped
in markdown fences and with extra keys; the vendored parser strips fences and ignores extra keys,
so both shapes validate. (A response that violated the schema would yield `status=parse_error`
with `raw_output`/`error` recorded and no write-back — that is M03 enforcement working, not a
failure to fix in place.)

## Findings & known behaviors (carried forward)

1. **Provider dependency is an environment prerequisite.** The generator emits no dependency
   file; the generated app reuses the studio-prototypes venv. For 7B, `groq` was installed
   temporarily into `/usr/src/.venv` (A2) and `GROQ_API_KEY` injected only on the `exec -e`
   command line (B3; `config/prototypes.env` is git-tracked, so keys are never written there).
   The runtime is self-contained at the mechanism-code level, **not** at the dependency-packaging
   level. Emitting a requirements declaration for the generated app is future generator work.
2. **Vendored snapshot reuse.** `templates.py`/`parsers.py` are a snapshot of the Studio
   mechanism subset, not a live shared dependency; the framing is "portable mechanism artifact,"
   with possible snapshot drift disclosed.
3. **M02 is pattern-level, app-specific.** `context.py` realizes `ai_config.context` for the
   Library model by ORM traversal (`instance.Loan.*`, `instance.Book.Author`,
   `instance.Loan.Customer`); it is hand-written for this demonstrator. Auto-deriving traversal
   from `ai_config` for arbitrary models is future generator work.
4. **Receiver fires on every save (no `created` guard).** The smoke creates once → one
   invocation. At scale, every `BookLoan` update re-invokes the LLM (the write-back uses
   `.update()`, which emits no `post_save`, so there is no recursion). Trigger semantics
   (create-only / field-watch) are a possible `ai_config.trigger` extension.
5. **`__str__` reflects `late_risk`.** With `late_risk` populated, `BookLoan.__str__` now returns
   the risk label (benign generator side effect, previously recorded).

## RO mapping

- **RO4 (case-based demonstration):** first end-to-end AI-enabled feature in the repeatable
  vehicle; rich per-mechanism trace (7A + 7B records).
- **RO2 (evolvability/robustness, effort):** generated hook/model unchanged while the runtime
  was swapped (Step 6 → 7) behind a stable contract; model backend selected by `model_profile`;
  low vendoring extraction cost recorded.
- **RO1/RO3 (catalogue, applicability):** event-driven, single-invocation, field-enrichment cell
  of the applicability space (Step 8 will cover the action-driven, multi-step chaining cell).

No constraint was violated: only the runtime template/assets + generate_models.py materialization

- evidence scripts changed; no `ai_hooks.py.jinja2`/`models.py.jinja2`/`generator.sh`/`api/**`
  edit, no `docker-compose.yaml` edit, no write-back logic added to the hook.
