# Step 4 Evidence - ai_hooks generation

Generator diff: docs/evidence/step4_generate_models.diff  
Generated models: docs/evidence/step4_generated_models.py  
Generated hooks: docs/evidence/step4_generated_ai_hooks.py  
Generation log: docs/evidence/step4_generation.log  
Verifier log: docs/evidence/step4_verify.log

## Definition Of Done

- [x] `step4_generate_models.diff` shows only the `main()` tail restructure and Step 4 hook-generation block .... PASS
- [x] New template exists at `prototypes/backend/generation/templates/ai_hooks.py.jinja2` .... PASS
- [x] Standalone `generate_models.py` run exited successfully .... PASS
- [x] `step4_generated_models.py` is byte-identical to `step3_generated_models.py` .... PASS
- [x] `step4_generated_ai_hooks.py` exists and parses as valid Python .... PASS
- [x] `step4_generated_ai_hooks.py` contains exactly one BookLoan `post_save` receiver .... PASS
- [x] Embedded `_AI_CONFIG` equals declared `BookLoan.late_risk.ai_config` .... PASS
- [x] Hook uses `from ai_runtime import invoke` as the single-entry contract .... PASS
- [x] Hook uses `except ImportError` .... PASS
- [x] Hook has `if value is None` .... PASS
- [x] Hook writes back with `BookLoan.objects.filter(pk=instance.pk).update(late_risk=value)` .... PASS
- [x] Hook does not use `instance.save()` .... PASS
- [x] No hook wiring was added .... PASS
- [x] No `ai_runtime` file/package was created .... PASS
- [x] No generator.sh, A2 route, migration, runserver, UI, compose edit, or git operation was used .... PASS

## Standalone Run

```text
[AI4MDE][ai_config] model=BookLoan attribute=late_risk trigger={'type': 'post_save', 'class': 'BookLoan'} model_profile=cheap write_back=late_risk version=1.0
[AI4MDE][ai_config] detected 1 AI-managed attribute(s)
```

## Verifier Result

```text
[PASS] models.py unchanged vs Step 3
[PASS] ai_hooks.py parses as valid Python
[PASS] imports present; exactly one @receiver(post_save, sender=BookLoan)
[PASS] embedded _AI_CONFIG matches the declared ai_config exactly
[PASS] single-entry invoke contract, None guard, recursion-safe .update(), no instance.save()
[DONE] Step 4 ai_hooks generation VERIFIED.
```

## Generated Hook Finding

The generator emits `shared_models/ai_hooks.py` as M07 event-driven invocation glue from model-level `ai_config`.

The embedded `ai_config` round-trips exactly against the declared `ai_config` in the resolved generator metadata.

The hook delegates all mechanism work to the single runtime entrypoint:

```python
ai_runtime.invoke(ai_config, instance) -> value
```

The generated write-back is recursion-safe because it uses:

```python
BookLoan.objects.filter(pk=instance.pk).update(late_risk=value)
```

The generated hook does not call `instance.save()`.

The generated `models.py` is byte-identical to Step 3.

Step 4 does not wire `ai_hooks.py` and does not implement `ai_runtime`. Both are deferred to Step 5.

## Raw Logs

- docs/evidence/step4_generation.log
- docs/evidence/step4_verify.log
