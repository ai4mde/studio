# Round 1 Smoke Test Evidence: M01 + M04

## Scope

This evidence covers mechanism-level smoke tests for:

- M01 Template-Driven Prompt Construction
- M04 Structured Output Parsing

No live LLM calls were executed in this round.

## Test Environment

Tests were executed with Python 3.11.9 in a local thesis test virtual environment.

## M01 Results

Validated:

- All registered templates resolve to existing `.j2` files.
- `DIAGRAM_GENERATE_ATTRIBUTE` renders with complete context.
- Missing context keys raise explicit `UndefinedError` through Jinja2 `StrictUndefined`.
- RAG template renders retrieved context, related classes, and existing methods.
- Attribute and method templates are functionally equivalent to preserved baseline constants after whitespace normalization.

## M04 Results

Validated:

- Clean JSON, fenced JSON, and preamble-wrapped JSON are parsed successfully.
- Empty responses produce structured `EMPTY_RESPONSE` failures.
- Natural-language responses without JSON are currently reported as `JSON_DECODE_ERROR`.
- Truncated JSON produces structured `JSON_DECODE_ERROR`.
- Schema-invalid JSON produces structured `SCHEMA_VALIDATION_ERROR`.
- Fenced Python code and unfenced valid Python code are parsed successfully.
- Explanation-plus-code responses are rejected with structured `PYTHON_SYNTAX_ERROR`.
- Syntax-invalid Python code is rejected with structured `PYTHON_SYNTAX_ERROR`.
- Very short plain-text responses are rejected with structured `SHORT_RESPONSE`.

## Observation

The current M04 JSON parser provides structured failures, but it does not distinguish natural-language no-JSON responses from malformed JSON; both are currently surfaced as `JSON_DECODE_ERROR`.
