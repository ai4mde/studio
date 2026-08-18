# T5 Real Mode Dependency Evidence

Date: 2026-07-09

## Summary

Track B is implemented in the allowed dependency write set:

- `prototypes/pyproject.toml`
- `prototypes/poetry.lock`

Added direct dependencies:

- `openai = "^1.47.0"`
- `groq = "^0.15.0"`

The lock file contains:

- `openai 1.47.0`
- `groq 0.15.0`

## Evidence

- `docs/evidence/t5_real_mode_rebuild.log`
- `docs/evidence/t5_real_mode_import_versions.log`
- `docs/evidence/t5_docker_compose_ps.log`
- `docs/evidence/t5_static_checks.json`

Results:

- `docker compose build studio-prototypes` completed successfully.
- `docker compose up -d studio-prototypes` recreated and started the service.
- Rebuilt container import check passed:

```text
openai 1.47.0 groq 0.15.0
```

## Real Provider Call

The dependency/rebuild gate was verified through image rebuild and import/version checks. A real provider invocation with `AI_RUNTIME_FAKE=0` was not run by Codex because it requires live API keys and external provider calls. The tracked dependency fix is persistent across rebuilds; the final real call can be run with keys supplied via local override/env only.

Per T5 spec workflow, no git commit was created by Codex.
