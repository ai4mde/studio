# Step 6 Evidence - M06 model routing gate

Template diff: docs/evidence/step6_ai_runtime_template.diff  
Generator log: docs/evidence/step6_generate.log  
6A smoke log: docs/evidence/step6a_smoke.log  
6A JSONL: docs/evidence/step6a_ai_invocations.jsonl  
Verifier log: docs/evidence/step6_verify.log

## Definition Of Done

- [x] Only `templates/ai_runtime_init.py.jinja2` and evidence scripts changed .... PASS
- [x] Generator re-materialized fresh `LibraryStep6` with SQLite and exited `[generator.sh exit=0]` .... PASS
- [x] Generated `models.py`, `ai_hooks.py`, and `apps.py` are byte-identical to Step 5C baselines .... PASS
- [x] Emitted `ai_runtime/__init__.py` is a router with `MODEL_PROFILES` and `call_model` .... PASS
- [x] Router contains cheap -> groq / llama-3.3-70b-versatile and strong -> openai / gpt-4o .... PASS
- [x] Provider imports are lazy inside provider functions, not module top level .... PASS
- [x] `invoke` still returns `None`; no parse/write-back is added .... PASS
- [x] 6A fake routing produced exactly one `invoke_routed` JSONL record .... PASS
- [x] 6A routed cheap -> groq / llama-3.3-70b-versatile and direct strong -> openai / gpt-4o .... PASS
- [x] `late_risk` stayed unchanged (`""`) in 6A .... PASS
- [x] 6B was not silently skipped; deferral is documented in `step6b_deferred.md` .... PASS
- [x] Host verifier passed .... PASS

## Preflight

```text
OPENAI_API_KEY_PRESENT= 0
GROQ_API_KEY_PRESENT= 0
ModuleNotFoundError: No module named 'openai'
```

6B was deferred because the real-provider gate did not pass. Missing conditions: both provider keys are absent, and `openai` is not importable in the `studio-prototypes` venv. The combined package check did not reach `groq` after the `openai` import failure.

## Generator

```text
[generator.sh exit=0]
```

The generated app uses SQLite (`db.sqlite3` in the generated project root). Migrations completed successfully; no cron-stage abort was observed.

## 6A Smoke

```text
[smoke] BookLoan pk=1 late_risk='' (expect '' - no write-back at Step 6)
[smoke] strong route: mode=fake provider=openai model=gpt-4o
[smoke] PASS: cheap->groq/llama + strong->openai/gpt-4o; mode=fake; late_risk unchanged
[DONE] Step 6 routing smoke VERIFIED.
```

JSONL record:

```json
{"timestamp": "2026-06-26T16:44:07.856599+00:00", "event": "invoke_routed", "model": "BookLoan", "pk": 1, "model_profile": "cheap", "mode": "fake", "provider": "groq", "routed_model": "llama-3.3-70b-versatile", "write_back": "late_risk", "ai_config_version": "1.0", "response_preview": "{\"late_risk\": \"LOW\", \"reason\": \"fake deterministic response\"}"}
```

## Host Verify

```text
[INFO] 6B deferred with documented reason (step6b_deferred.md present)
[PASS] Step 6 (M06) verified: generated hook unchanged; runtime routes by model_profile; late_risk unchanged
```

## Finding

The generated hook and domain model are byte-identical to Step 5C while the runtime behind `ai_runtime.invoke` now routes by `ai_config.model_profile` through one `call_model` entrypoint.

The routing table is:

- `cheap` -> `groq` / `llama-3.3-70b-versatile`
- `strong` -> `openai` / `gpt-4o`

This was proven deterministically in 6A. 6B real-provider evidence is deferred until provider keys and packages are available.

`late_risk` remains unchanged because Step 6 is routing only; parse/write-back is deferred to Step 7.
