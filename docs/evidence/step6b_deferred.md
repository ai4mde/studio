# Step 6B Deferred - real provider routing

Step 6B was not run because the required real-provider gate did not pass.

## Preflight Result

```text
OPENAI_API_KEY_PRESENT= 0
GROQ_API_KEY_PRESENT= 0
```

Provider package check:

```text
ModuleNotFoundError: No module named 'openai'
```

The combined `import openai, groq` check stops at the missing `openai` package, so `groq` package importability was not reached by the prescribed command.

## Missing Conditions

- `OPENAI_API_KEY` is absent.
- `GROQ_API_KEY` is absent.
- `openai` is not importable in the `studio-prototypes` venv.

## Remediation

Before rerunning Step 6B, provide the missing provider keys and align the prototypes venv dependencies, for example by running the project-approved dependency sync (`poetry install --no-root --sync`) so both `openai` and `groq` are importable.

Step 6A remains valid and completed with deterministic fake routing evidence.
