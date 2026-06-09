# Step 1 — Library Model Generation + BookLoan Verification (Evidence)

## Purpose

Demonstrate that the Library domain model is produced **reproducibly** by Studio's
official generator route — i.e. that the app's structure is _generated deterministically
from a declarative model_, not hand-written. The specific risk gate is the **BookLoan
associative class**, which must receive two ForeignKeys (to `Loan` and to `Book`).

This step contains **no AI**: no `ai_config`, no LLM, no hooks. It is the structural
baseline on which Steps 2–8 build.

## Environment metadata

- Date: 2026-06-09
- Working branch: `s4386299-thesis-clean` (synced against `origin/develop`)
- Studio services: `studio-api`, `studio-prototypes`, `postgres`, `traefik` (docker compose)
- Python / Django (generated runtime): Django 5.0.2 via `/usr/src/.venv`
- `manage.py` (studio-api): `/usr/src/model/manage.py`
- Generated prototype path (studio-prototypes):
  `/usr/src/prototypes/generated_prototypes/<SYSTEM_ID>/LibraryStep1/`
- SYSTEM_ID for this run: `7d735a07-b6cd-409d-9cc7-f3a07cbec983`
- Prototype name: `LibraryStep1`

## What was done

### Phase 1D — import into Studio DB (PASSED)

The Library project (`step1_library_model.json`, import/export normalized format) was
imported via the ORM (`Project.import_from_json`). Verified DB state:

- 6 classifiers = **5 classes + 1 enum**
- **4 relations** (all `1 -> *`, one-side as source)
- classes diagram: **nodes=6, edges=4**
- interfaces: 0 (expected for a pure class-model step)

### Phase 1E/1F — official generator route (A2)

Generation was triggered through the official route, not a local dry-run:

    Studio DB
      -> Django generator API   POST /api/v1/generator/prototypes/
        -> studio-prototypes Flask /generate
          -> generator.sh

The generator produced `shared_models/models.py` (plus the always-generated
`workflow_engine` and `noauth_home`/auth scaffolding apps).

## Core result (the risk gate — PASSED)

The official generator produced `BookLoan` as a Django model with **two** ForeignKeys:

```python
class BookLoan(models.Model):
    Loan = models.ForeignKey("Loan", on_delete=models.CASCADE)
    Book = models.ForeignKey("Book", on_delete=models.CASCADE)
    def __str__(self):
        return str(self.Loan)
```

`Book` received the nested `class Category(models.TextChoices)` with five literals
(`FICTION, NON_FICTION, SCIENCE, HISTORY, CHILDREN`) plus `Author = ForeignKey("Author")`;
`Loan` received `Customer = ForeignKey("Customer")`. The generated file is syntactically
valid (AST-parsed). **The associative-class risk (Guus landmine #1) does not block the
Library case.** FK fields are named after the target class (PascalCase) — a generator
convention, recorded here for later phases (1G' / Step 7 ORM access uses PascalCase).

> Note: `step1_models_baseline_expected.py` is a **preflight** expectation produced locally
> from the real generator code; the **formal 1F evidence** is the generated
> `shared_models/models.py` from the official route (attached as `step1_generated_models.py`).
> BookCategory literals are an illustrative set (a Guus meeting example), not a constrained
> domain decision.

## Phase 1G' — model-layer verification (no full migration)

Full generated-app migration is blocked (see findings below), so runtime ORM tests
(`BookLoan.objects.create(...)`, `loan.bookloan_set.all()`) are **deferred** — they belong
to a migratable generated app and would be a false claim now. Instead, 1G' verifies the
model layer in two valid parts (`step1_model_layer_verify.py`):

- **Part A (Studio DB):** 5 classes + 1 enum + 4 associations; BookLoan has exactly two
  _incoming_ associations (from Loan and from Book); enum has five literals.
- **Part B (generated `models.py`, static/AST):** BookLoan two FKs, Book.Author FK,
  Loan.Customer FK, and the 5-literal `Category` enum.

This explicitly does **not** claim the generated app runtime is operational.

## Runtime-scaffold finding (Studio generator boundary)

Producing a _fully runnable_ app exposed a Studio generator constraint independent of the
Library model: a runnable prototype appears to require **auth + at least one interface**.

- **auth-off:** the always-generated `workflow_engine/models.py` does
  `from shared_models.models import User`, but `User` is only emitted when auth is on →
  `django.setup()` fails (no migration).
- **auth-on + zero interface:** `workflow_engine/views.py` does
  `from shared_models.views import GenericView, ...`, but `shared_models/views.py` is only
  populated during _interface_ generation (`generate_application.py` →
  `view_generation.generate_views`, rendering `shared_views.py.jinja2`). With zero
  interfaces that file stays the empty `startapp` stub → `ImportError: GenericView`.

**Conclusion:** the pure zero-interface "runnable app" configuration does not exist in the
current Studio; the Loan Application Demo runs because it has interfaces (and auth). This is
recorded as a finding, not worked around. The Library domain-model generation itself is
unaffected and verified above.

## Interpretation (one line)

The Library domain model — including the BookLoan associative class with two ForeignKeys —
is generated correctly and reproducibly by Studio's official generator route, establishing
the structural baseline for the AI mechanisms in Steps 2–8.

## Known followups

- **Guus check-in (planned at Step 1):** confirm (a) the BookLoan two-FK result matches
  expectation, and (b) whether the auth+interface requirement for a runnable app is intended
  generator behaviour or a bug. This directly affects how Step 5–7 obtain a migratable app.
- Steps 5–7 require a runnable generated app; the auth+interface requirement must be
  resolved before the end-to-end `late_risk` demo (Step 7).

## Artifacts

- `step1_library_model.json` — design artifact (import format)
- `step1_generator_metadata_sent.json` — exact resolved (③) payload sent in 1E
- `step1_generated_models.py` — formal 1F artifact (generated `shared_models/models.py`)
- `preflight/step1_models_baseline_expected.py` — preflight expectation (reference)
- `step1_model_layer_verify.py` — Phase 1G' verification script
- `step1_library_generation.log` — full stdout of 1D / 1E / 1F / 1G'
