# Step 0 Evidence: Smoke Test Baseline

## Purpose

Establish the known-good Studio environment from which Step 1 (Library case generation) proceeds. This file records that the four implemented foundation mechanisms (M01, M02, M03, M04 in current thesis numbering) pass their smoke tests on the standard Studio dev environment.

M05 (Declarative LLM Configuration), M06 (Model Routing & Abstraction), and M07 (Event-Driven LLM Invocation) are NOT implemented and NOT covered by this evidence file.

## Environment metadata

- Date: 2026-06-08
- Branch: s4386299-thesis-clean
- Commit SHA: 9b9e8537d53e8e6d090f62e8ce11603486c69b93
- Python version: Python 3.11.9
- Interpreter path: /Users/bemmgr/allCodes/thesisProject/studio/api/model/.venv-thesis-test/bin/python
- Virtualenv path: api/model/.venv-thesis-test
- Dependency install method: pip (inside the venv)
- Studio runtime: docker compose stack (postgres exposed on localhost:5432)
- Test runner for M02 in this session: Django native (`python manage.py test`)

## pyproject.toml changes during Step 0

Three changes, net of the SQLite-detour reversion:

1. Added `pytest = "^8.4"` to [tool.poetry.group.dev.dependencies] (was missing entirely)
2. Added `pydantic = "^2.0"` to [tool.poetry.dependencies] (it was a transitive dep via django-ninja; now explicit because llm/parsers imports it directly)
3. Added section `[tool.pytest.ini_options]` with `DJANGO_SETTINGS_MODULE = "model.settings"`

Important clarification on item 3: this section is retained for FUTURE pytest-based tests. The M01–M04 smoke tests recorded in this evidence file were executed via Django's native test runner (`python manage.py test`), which does NOT read pyproject.toml. DJANGO_SETTINGS_MODULE for the native runner is resolved via the environment (typically defaulting to `model.settings` from manage.py itself). The [tool.pytest.ini_options] entry is not currently exercised.

Detour note: an earlier exploration in this step attempted an SQLite-based offline test path (a model.test_settings module + --no-migrations flag). It was abandoned because Studio's metadata migrations contain a PostgreSQL-tolerant construct (`models.CharField()` without max_length) that SQLite cannot replay. The detour was fully reverted; only the three changes above remain.

## Local docker-compose adjustment (uncommitted, intentional)

There is a local-only modification to docker-compose.yaml:

```
- pgsql-data:/var/lib/postgresql/data    (upstream)
+ pgsql-data:/var/lib/postgresql/        (local)
```

This works around a pre-existing local Docker volume state issue (incompatible Postgres data dir from a prior image version). Not pushed upstream because it is environment-specific.

## Dependency version pinning (Step 0 finding)

During Phase 3 verification, M02 initially failed with:
`TypeError: NinjaAPI.__init__() got an unexpected keyword argument 'csrf'`

The error traced to `model/api.py` line 10, which passes `csrf=False` to NinjaAPI. This parameter was removed in django-ninja versions later than the one Studio's `poetry.lock` pins.

Root cause: pip does not read `poetry.lock`. The initial install used the loose range `django-ninja = "^1.1.0"` in `pyproject.toml` and resolved to the latest 1.x release, which dropped the `csrf=` keyword. The Studio team's locked version retains it.

Resolution: pinned `django-ninja==1.2.1` in the venv via:

    pip install "django-ninja==1.2.1"

Studio source code was NOT modified.

Broader observation: other dependencies installed by pip may also have drifted from their locked versions (e.g., openai, groq, sentry-sdk). These have not caused failures in M01–M04 smoke tests because those tests do not exercise the affected code paths. Before Step 7 (end-to-end Library case demo, which exercises LLM provider clients), the venv should be rebuilt using a method that honors `poetry.lock` (e.g., `poetry install --no-root --sync`).

## Mechanism-to-test-file mapping (verbatim, do not summarize)

Test file names in api/model/llm/tests/ use legacy mechanism numbering from an earlier draft of the catalogue. The mapping to current thesis numbering is:

| Test file         | Current thesis mechanism ID | Mechanism name                      |
| ----------------- | --------------------------- | ----------------------------------- |
| test_m01_smoke.py | M01                         | Template-Driven Prompt Construction |
| test_m02_smoke.py | M02                         | Retrieval-Augmented Generation      |
| test_m04_smoke.py | M03                         | Structured Output Parsing           |
| test_m05_smoke.py | M04                         | Prompt Chaining                     |

File names are not renamed at this stage. Renaming is deferred until after MVP completion (M05–M07 implementation) to avoid disturbing green smoke tests during implementation.

## Test execution status

| Test file         | Thesis ID | Result | When verified                                                | DB required      |
| ----------------- | --------- | ------ | ------------------------------------------------------------ | ---------------- |
| test_m01_smoke.py | M01       | PASS   | Earlier in this Step 0 session                               | No (pure-Python) |
| test_m02_smoke.py | M02       | PASS   | Phase 3 of this Step 0 session (against Dockerized Postgres) | Yes              |
| test_m04_smoke.py | M03       | PASS   | Earlier in this Step 0 session                               | No (pure-Python) |
| test_m05_smoke.py | M04       | PASS   | Earlier in this Step 0 session                               | No (pure-Python) |

Full output of the Phase 3 M02 verification run is in `step0_smoke_tests.log` in the same directory.

The M01/M03/M04 results from earlier in the session are anchored to the same venv and the same code state; they were not re-run in Phase 3 because they do not depend on database availability and re-running would add no thesis-relevant evidence beyond what is already established.

## Interpretation

All four implemented foundation mechanisms (M01, M02, M03, M04) are verified on the Studio standard dev environment. This is the known-good baseline from which Step 1 (Library case model generation) proceeds.
