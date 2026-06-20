# Step 3 Evidence - ai_config detection (BookLoan.late_risk)

Artifact under test: docs/evidence/step3_generated_models.py  
Resolved metadata: docs/evidence/step3_generator_metadata_sent.json  
Generator diff: docs/evidence/step3_generate_models.diff  
Verifier log: docs/evidence/step3_verify.log

## Definition Of Done

- [x] `generate_models.py` change is additive-only: `step3_generate_models.diff` shows only `detect_ai_config(...)` plus the two `main()` detection lines .... PASS
- [x] Resolved metadata carries `BookLoan.late_risk.ai_config` via raw `n.cls.data` passthrough .... PASS
- [x] Standalone `generate_models.py` run logged `BookLoan.late_risk` detection and count `1` .... PASS
- [x] `step3_verify.py` reached `[DONE] Step 3 ai_config detection VERIFIED.` with all `[PASS]` lines and no `AssertionError` .... PASS
- [x] Generated `models.py` contains no new hook/signal/runtime code tokens versus Step 1 .... PASS
- [x] Deliverables written under `docs/evidence/` and `docs/evidence/scripts/` .... PASS
- [x] Step 3 constraints respected: no generator.sh, A2 route, makemigrations, migrate, UI, compose, template, or api/model changes .... PASS

## Metadata PASS

```text
[step3-meta][PASS] BookLoan.late_risk.ai_config present in metadata: keys=['ai_config_version', 'context', 'model_profile', 'output', 'template', 'trigger']
```

## Detection Lines

```text
[AI4MDE][ai_config] model=BookLoan attribute=late_risk trigger={'type': 'post_save', 'class': 'BookLoan'} model_profile=cheap write_back=late_risk version=1.0
[AI4MDE][ai_config] detected 1 AI-managed attribute(s)
```

## Generated BookLoan Field

```python
late_risk = models.CharField(max_length=255, default='', null=True, blank=True)
```

## Verifier Result

```text
[PASS] resolved metadata carries BookLoan.late_risk.ai_config
[PASS] generator logged ai_config detection for BookLoan.late_risk
[PASS] BookLoan.late_risk rendered as stored CharField (FKs preserved)
[PASS] no new hook/AI code in generated models.py (detection-only)
[PASS] BookLoan delta == {late_risk CharField} + {__str__ self.Loan -> self.late_risk} (order-insensitive)
[DONE] Step 3 ai_config detection VERIFIED.
```

## Finding

ai_config flows from `Classifier.data` into the resolved generator metadata via raw passthrough (`n.cls.data`), confirmed by `[step3-meta][PASS]`.

`generate_models.py` now detects and logs attribute-level `ai_config`. The generator source change is additive and log-only; see `docs/evidence/step3_generate_models.diff`.

No hook, signal, or runtime code is emitted in Step 3. The generated output has no new `ai_config`, `post_save`, `receiver`, `signals`, or `.update(` tokens versus Step 1.

Generated `models.py` gains the ordinary stored `late_risk` `CharField`.

`BookLoan.__str__` changes from `self.Loan` to `self.late_risk`. This is an existing generator side effect of `define_object_name_attribute` (`prototypes/backend/generation/generation_scripts/utils/definitions/model.py:98-111`) selecting the first `STRING` attribute once `late_risk` is added; it is not caused by `ai_config` and is not Step 4 behavior.

Open item for Step 5/7: `__str__` now depends on an AI-populated field that is empty until the M07 hook runs.

## Raw Logs

- docs/evidence/step3_build_metadata.log
- docs/evidence/step3_detection.log
- docs/evidence/step3_verify.log
