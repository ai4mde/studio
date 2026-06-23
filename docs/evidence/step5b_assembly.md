# Step 5B Evidence - generator assembly

Generator diff: docs/evidence/step5b_generate_models.diff  
Generation log: docs/evidence/step5b_generation.log  
Verifier log: docs/evidence/step5b_verify.log

## Definition Of Done

- [x] `step5b_generate_models.diff` shows only the Step 5B additions inside the existing `if hooks:` block .... PASS
- [x] New templates exist: `shared_models_apps.py.jinja2` and `ai_runtime_init.py.jinja2` .... PASS
- [x] Standalone generation exited successfully .... PASS
- [x] Generated `ai_runtime/__init__.py` is at the project root, sibling of `shared_models` .... PASS
- [x] `models.py` class content is unchanged from Step 4; class order differs only due to metadata node order .... PASS
- [x] `ai_hooks.py` is byte-identical to Step 4 .... PASS
- [x] `apps.py` parses and `SharedModelsConfig.ready()` imports `shared_models.ai_hooks` .... PASS
- [x] `ai_runtime` stub parses and exposes `invoke(ai_config, instance)` .... PASS
- [x] Stub writes one JSONL record to `settings.BASE_DIR / "ai_invocations.jsonl"` and returns `None` .... PASS
- [x] Stub has no LLM dependency/reference and performs no write-back .... PASS
- [x] No generator.sh, A2 route, makemigrations, migrate, runserver, UI, compose edit, or repository operation was used .... PASS

## Standalone Run

```text
[AI4MDE][ai_config] model=BookLoan attribute=late_risk trigger={'type': 'post_save', 'class': 'BookLoan'} model_profile=cheap write_back=late_risk version=1.0
[AI4MDE][ai_config] detected 1 AI-managed attribute(s)
```

## Verifier Result

```text
[PASS] models.py & ai_hooks.py content unchanged vs Step 4 (class reorder is a benign metadata-ordering effect)
[PASS] apps.py: SharedModelsConfig.ready() imports shared_models.ai_hooks
[PASS] ai_runtime stub: invoke()->None, JSONL at settings.BASE_DIR, no LLM deps
[DONE] Step 5B generator assembly VERIFIED.
```

## Finding

The generator now emits `shared_models/apps.py`, wiring `SharedModelsConfig.ready()` to import `shared_models.ai_hooks` and register the M07 receivers.

The generator also emits a top-level `ai_runtime/__init__.py` stub fulfilling:

```python
invoke(ai_config, instance) -> None
```

The stub writes one JSONL record to `settings.BASE_DIR / "ai_invocations.jsonl"`, contains no LLM dependency or client reference, and performs no write-back.

`models.py` and `ai_hooks.py` content are unchanged from Step 4. `models.py` class order differs only because model generation follows metadata node order, which changed between the Step 3 and Step 5 metadata after the Step 5A re-import. This is benign and does not affect migration or runtime behavior.

The stub is replaced by the real M01-M06 runtime at Step 6/7 behind the same import contract.

## Generated Files

- docs/evidence/step5b_generated_models.py
- docs/evidence/step5b_generated_ai_hooks.py
- docs/evidence/step5b_generated_apps.py
- docs/evidence/step5b_generated_ai_runtime_init.py
