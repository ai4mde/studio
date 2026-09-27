# AI Evaluator V2 — continuous-scoring strict output schema draft

## Contract

- Schema version: `ai-evaluator-v2/1.1`
- One response object per candidate
- No wrapper array
- All properties are required
- Unknown properties are forbidden at every object level
- `overall_score` is a continuous whole-graph quality score in the closed interval 0.0–1.0
- Dimension assessments are diagnoses, not numeric subscores

The runner must also validate the cross-field rules listed after the JSON Schema. Some cross-field dependencies are intentionally enforced by the runner because they are not expressible in the strict Structured Outputs subset without making the schema unnecessarily complex.

## Strict Structured Outputs configuration

```json
{
  "type": "json_schema",
  "name": "ai_evaluator_v2_result",
  "strict": true,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "schema_version": {
        "type": "string",
        "enum": ["ai-evaluator-v2/1.1"],
        "description": "Fixed output-contract version."
      },
      "case_id": {
        "type": "string",
        "description": "Case identifier copied exactly from the candidate input."
      },
      "candidate_id": {
        "type": "string",
        "description": "Candidate identifier copied exactly from the candidate input."
      },
      "action_assessment": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "status": {
            "type": "string",
            "enum": ["preserved", "defect", "uncertain", "not_applicable"],
            "description": "Diagnostic status for Action semantics; not a subscore."
          },
          "summary": {
            "type": "string",
            "description": "Concise account of preserved or defective action meaning."
          }
        },
        "required": ["status", "summary"]
      },
      "flow_assessment": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "status": {
            "type": "string",
            "enum": ["preserved", "defect", "uncertain", "not_applicable"],
            "description": "Diagnostic status for Flow and precedence semantics; not a subscore."
          },
          "summary": {
            "type": "string",
            "description": "Concise account of preserved or defective ordering, reachability, continuation, or termination."
          }
        },
        "required": ["status", "summary"]
      },
      "control_flow_assessment": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "status": {
            "type": "string",
            "enum": ["preserved", "defect", "uncertain", "not_applicable"],
            "description": "Diagnostic status for Control-Flow semantics; not a subscore."
          },
          "summary": {
            "type": "string",
            "description": "Concise account of preserved or defective decisions, alternatives, loops, concurrency, synchronization, or termination behavior."
          }
        },
        "required": ["status", "summary"]
      },
      "main_error_type": {
        "type": "string",
        "enum": [
          "none",
          "missing_action",
          "extra_or_duplicated_action",
          "incorrect_action_meaning_or_grouping",
          "wrong_ordering_or_precedence",
          "wrong_branching_or_condition",
          "wrong_continuation_or_termination",
          "wrong_loop_or_recurrence",
          "wrong_parallelism_or_synchronization",
          "mixed_or_cascading",
          "other_semantic_defect"
        ],
        "description": "Dominant root semantic defect. Use none only when no meaningful defect is found."
      },
      "explanation": {
        "type": "string",
        "description": "Concise audit explanation connecting source behavior, generated behavior, and whole-graph impact."
      },
      "overall_score": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "One continuous holistic whole-graph semantic-quality score."
      },
      "severity": {
        "type": "string",
        "enum": ["none", "minor", "moderate", "major", "fundamental"],
        "description": "Qualitative semantic-impact descriptor, not a numeric score band or subscore."
      },
      "confidence": {
        "type": "string",
        "enum": ["high", "medium", "low"],
        "description": "Confidence in the provisional evaluation from the supplied evidence, independent of graph quality."
      },
      "ambiguity_flag": {
        "type": "boolean",
        "description": "Whether material source or representation ambiguity could affect diagnosis or score."
      },
      "ambiguity_explanation": {
        "type": "string",
        "description": "Explanation of material ambiguity, or an empty string when ambiguity_flag is false."
      },
      "requires_human_review": {
        "type": "boolean",
        "description": "Whether uncertainty or input inconsistency could plausibly change the diagnosis or score."
      },
      "review_reason": {
        "type": "string",
        "description": "Reason human review is required, or an empty string when requires_human_review is false."
      }
    },
    "required": [
      "schema_version",
      "case_id",
      "candidate_id",
      "action_assessment",
      "flow_assessment",
      "control_flow_assessment",
      "main_error_type",
      "explanation",
      "overall_score",
      "severity",
      "confidence",
      "ambiguity_flag",
      "ambiguity_explanation",
      "requires_human_review",
      "review_reason"
    ]
  }
}
```

## Required runner validation

After schema validation, reject a result as invalid unless all of these rules hold:

1. `schema_version` equals `ai-evaluator-v2/1.1`.
2. `case_id` and `candidate_id` exactly match the request input.
3. `overall_score` is a finite JSON number in the inclusive range `0.0` through `1.0`; no fixed score levels or quarter-point rounding are applied.
4. `overall_score` is `1.00` if and only if no meaningful semantic defect is found. In that situation, `main_error_type` and `severity` are both `none`.
5. If `overall_score` is below `1.00`, `main_error_type` and `severity` must both be non-`none`. The non-`none` severity labels describe impact qualitatively; there are no numerical severity cutoffs or severity-to-score mappings.
6. If `ambiguity_flag` is `false`, `ambiguity_explanation` must be the empty string; if true, it must be non-empty.
7. If `requires_human_review` is `false`, `review_reason` must be the empty string; if true, it must be non-empty.
8. `requires_human_review` is not derived mechanically from the score. A low-quality graph can be diagnosed confidently, and a provisionally correct graph can still require review because the source is ambiguous.

## Field semantics

### Dimension status

- `preserved`: no meaningful defect found in that semantic dimension.
- `defect`: at least one meaningful semantic defect found in that dimension.
- `uncertain`: the supplied evidence does not support a confident dimension judgement.
- `not_applicable`: the process contains no meaningful construct in that dimension beyond trivial sequence. Use sparingly; Action semantics will ordinarily be applicable.

The three statuses must never be converted into numeric subscores or averaged.

### Confidence

- `high`: supplied evidence supports a clear diagnosis and score boundary.
- `medium`: diagnosis is more likely than alternatives, but interpretation or boundary uncertainty remains.
- `low`: material uncertainty could readily change the diagnosis or score.

### Review flag

Set `requires_human_review` to true when source ambiguity, a JSON/rendering conflict, malformed or materially incomplete input, or low confidence could plausibly change the diagnosis or score. Do not set it automatically for every defect or every score below 1.00.

## Canonical result example

```json
{
  "schema_version": "ai-evaluator-v2/1.1",
  "case_id": "example-1",
  "candidate_id": "candidate_1",
  "action_assessment": {
    "status": "preserved",
    "summary": "All material business actions are present with compatible meanings."
  },
  "flow_assessment": {
    "status": "defect",
    "summary": "The rejection branch rejoins after notification instead of before it."
  },
  "control_flow_assessment": {
    "status": "defect",
    "summary": "One rejection outcome bypasses its required notification, while the central approval path is preserved."
  },
  "main_error_type": "wrong_continuation_or_termination",
  "explanation": "The source requires rejected requests to trigger a notification before the process ends, but the graph lets that branch bypass notification. The defect affects one bounded outcome and leaves the main process structure intact, so its whole-graph impact is moderate.",
  "overall_score": 0.62,
  "severity": "moderate",
  "confidence": "high",
  "ambiguity_flag": false,
  "ambiguity_explanation": "",
  "requires_human_review": false,
  "review_reason": ""
}
```
