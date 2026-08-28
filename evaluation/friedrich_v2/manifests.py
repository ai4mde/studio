from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .core import sha256_file


SOURCE_SCHEMA = "friedrich-v2-source-manifest/v1"
GENERATED_SCHEMA = "friedrich-v2-generated-manifest/v3"
UNRESOLVED_COHORT = "UNRESOLVED"
EXPECTED_CANDIDATE_COUNT = 3
EXPECTED_CANDIDATE_IDS = tuple(f"candidate_{index}" for index in range(1, 4))
MAXIMUM_ATTEMPTS_PER_CANDIDATE = 3


class ManifestError(ValueError):
    pass


def _load(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ManifestError("Manifest root must be an object")
    return payload


def _verify_file(record: Mapping[str, Any], path_key: str, hash_key: str) -> None:
    path = Path(str(record.get(path_key, "")))
    expected = record.get(hash_key)
    if not path.is_file():
        raise ManifestError(f"Missing input file: {path}")
    if not isinstance(expected, str) or sha256_file(path) != expected:
        raise ManifestError(f"Hash mismatch for {path}")


def load_source_manifest(path: str | Path, verify_files: bool = True) -> dict[str, Any]:
    payload = _load(path)
    if payload.get("schema_version") != SOURCE_SCHEMA:
        raise ManifestError("A Friedrich V2 source manifest is required")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) != 47:
        raise ManifestError("The source manifest must contain exactly 47 cases")
    ids = [case.get("case_id") for case in cases if isinstance(case, Mapping)]
    if len(ids) != 47 or len(set(ids)) != 47:
        raise ManifestError("Source case IDs must be present and unique")
    required = {
        "case_id", "process_text_path", "process_text_sha256",
        "reference_model_path", "reference_model_sha256", "source_repository_commit",
        "source_format", "language",
    }
    for case in cases:
        if not isinstance(case, Mapping) or set(case) != required:
            raise ManifestError("Source cases contain missing or non-provenance fields")
        if verify_files:
            _verify_file(case, "process_text_path", "process_text_sha256")
            _verify_file(case, "reference_model_path", "reference_model_sha256")
    return payload


def load_generated_manifest(
    path: str | Path,
    expected_case_ids: set[str],
    verify_files: bool = True,
) -> dict[str, Any]:
    payload = _load(path)
    if payload.get("schema_version") != GENERATED_SCHEMA:
        raise ManifestError("A Friedrich V2 generated-input manifest is required")
    if payload.get("cohort_id") in {None, "", UNRESOLVED_COHORT}:
        raise ManifestError("Generated model cohort is unresolved")
    if payload.get("cohort_stage") not in {"development_validation", "development_full", "final_baseline"}:
        raise ManifestError("Generated cohort_stage is missing or unsupported")
    if payload.get("condition") != "ai_only_three_candidate_baseline":
        raise ManifestError("Generated manifest must declare the AI-only three-candidate condition")
    if payload.get("expected_candidate_count") != EXPECTED_CANDIDATE_COUNT:
        raise ManifestError("Generated manifest must require exactly 3 candidates per case")
    if payload.get("human_selection") is not False:
        raise ManifestError("AI-only baseline must explicitly set human_selection=false")
    if payload.get("maximum_attempts_per_candidate") != MAXIMUM_ATTEMPTS_PER_CANDIDATE:
        raise ManifestError("Generated manifest must freeze exactly 3 attempts per candidate")
    if payload.get("run_integrity_status") != "valid":
        raise ManifestError("Generated cohort is not marked valid after infrastructure preflight")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ManifestError("Generated manifest cases must be a list")
    ids = [case.get("case_id") for case in cases if isinstance(case, Mapping)]
    if set(ids) != expected_case_ids or len(cases) != len(set(ids)):
        raise ManifestError("Generated manifest must identify each source case exactly once")
    required = {"case_id", "candidates"}
    for case in cases:
        if not isinstance(case, Mapping) or set(case) != required:
            raise ManifestError("Generated cases contain unexpected fields")
        candidates = case.get("candidates")
        if not isinstance(candidates, list) or len(candidates) != EXPECTED_CANDIDATE_COUNT:
            raise ManifestError(f"Case {case.get('case_id')} must contain exactly 3 candidates")
        candidate_ids = [candidate.get("candidate_id") for candidate in candidates if isinstance(candidate, Mapping)]
        if len(candidate_ids) != EXPECTED_CANDIDATE_COUNT or len(set(candidate_ids)) != EXPECTED_CANDIDATE_COUNT:
            raise ManifestError(f"Case {case.get('case_id')} has duplicate or missing candidate IDs")
        if tuple(sorted(candidate_ids)) != EXPECTED_CANDIDATE_IDS:
            raise ManifestError(f"Case {case.get('case_id')} must use candidate_1, candidate_2, and candidate_3")
        candidate_required = {
            "candidate_id", "generation_index", "generation_status", "attempt_count", "attempts",
            "generated_model_path", "generated_model_sha256", "failure_reason", "failure_stage",
        }
        for candidate in candidates:
            if not isinstance(candidate, Mapping) or set(candidate) != candidate_required:
                raise ManifestError(f"Case {case.get('case_id')} candidate contains unexpected fields")
            expected_id = f"candidate_{candidate.get('generation_index')}"
            if candidate.get("candidate_id") != expected_id or candidate.get("generation_index") not in {1, 2, 3}:
                raise ManifestError(f"Case {case.get('case_id')} candidate ID and generation index disagree")
            status = candidate.get("generation_status")
            if status not in {"success", "failed"}:
                raise ManifestError(f"Case {case.get('case_id')} candidate has invalid generation_status")
            attempts = candidate.get("attempts")
            attempt_count = candidate.get("attempt_count")
            if (
                not isinstance(attempt_count, int)
                or isinstance(attempt_count, bool)
                or not 1 <= attempt_count <= MAXIMUM_ATTEMPTS_PER_CANDIDATE
                or not isinstance(attempts, list)
                or len(attempts) != attempt_count
            ):
                raise ManifestError(f"Case {case.get('case_id')} candidate has invalid attempt_count")
            allowed_attempt_fields = {
                "attempt_index", "attempt_status", "failure_reason", "failure_stage", "evidence",
            }
            for index, attempt in enumerate(attempts, start=1):
                if not isinstance(attempt, Mapping):
                    raise ManifestError(f"Case {case.get('case_id')} attempt must be an object")
                if not {"attempt_index", "attempt_status"} <= set(attempt) or not set(attempt) <= allowed_attempt_fields:
                    raise ManifestError(f"Case {case.get('case_id')} attempt contains unexpected fields")
                if attempt.get("attempt_index") != index or attempt.get("attempt_status") not in {"success", "failed"}:
                    raise ManifestError(f"Case {case.get('case_id')} attempts must be ordered and valid")
            statuses = [attempt["attempt_status"] for attempt in attempts]
            if status == "success":
                if statuses[-1] != "success" or "success" in statuses[:-1]:
                    raise ManifestError(f"Case {case.get('case_id')} candidate must stop at first success")
                if (
                    candidate.get("failure_reason") is not None and candidate.get("failure_reason") != ""
                ) or (
                    candidate.get("failure_stage") is not None and candidate.get("failure_stage") != ""
                ):
                    raise ManifestError(f"Successful candidate cannot have final failure fields")
                if not candidate.get("generated_model_path") or not candidate.get("generated_model_sha256"):
                    raise ManifestError(f"Successful case {case.get('case_id')} candidate requires path and hash")
                if verify_files:
                    _verify_file(candidate, "generated_model_path", "generated_model_sha256")
            else:
                if attempt_count != MAXIMUM_ATTEMPTS_PER_CANDIDATE or any(item != "failed" for item in statuses):
                    raise ManifestError(f"Failed case {case.get('case_id')} candidate requires 3 failed attempts")
                if candidate.get("generated_model_path") is not None or candidate.get("generated_model_sha256") is not None:
                    raise ManifestError(f"Failed case {case.get('case_id')} candidate cannot have an artifact")
                if not isinstance(candidate.get("failure_reason"), str) or not candidate["failure_reason"].strip():
                    raise ManifestError(f"Failed case {case.get('case_id')} candidate requires failure_reason")
    provenance = payload.get("generation_provenance")
    provenance_required = {
        "generated_system_commit", "pipeline_profile", "generation_configuration",
        "model_identifier", "runtime_environment", "retry_failure_policy",
    }
    if not isinstance(provenance, Mapping) or set(provenance) != provenance_required:
        raise ManifestError("Complete generated-system provenance is required")
    if any(provenance.get(field) is None or provenance.get(field) == "" for field in provenance_required):
        raise ManifestError("Generated-system provenance fields must not be empty")
    return payload
