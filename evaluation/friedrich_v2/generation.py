from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .action import ACTION_MODEL_NAME, ACTION_MODEL_REVISION, ACTION_SIMILARITY_THRESHOLD
from .adapters import activity_graph_to_eval_graph
from .core import canonical_json, sha256_file
from .manifests import (
    EXPECTED_CANDIDATE_IDS,
    MAXIMUM_ATTEMPTS_PER_CANDIDATE,
    load_source_manifest,
)


CONFIG_SCHEMA = "friedrich-v2-small-validation-config/v1"
RUN_CONFIG_SCHEMA = "friedrich-v2-run-config/v1"
STATE_SCHEMA = "friedrich-v2-generation-state/v1"

V2_GENERATOR_COMMIT = "4be4c5b7b30aaff0433d4406056a0cf5c8fc63a9"
V2_GENERATOR_BRANCH = "feature/final-v2-stable"
V2_EVALUATION_VERSION = "Revised Generator V2 / Final V2"
V2_DATASET_COMMIT = "4015ddfe5338ae3f1e12fb2d8c474244fbf8647d"
HISTORICAL_EVALUATOR_COMMIT = "b14870429d8cdf39712314e714d3228bca0ab3f2"
PREFLIGHT_CASE_IDS = ("3-1", "3-6", "3-2", "3-3", "4-1")
RUN_TYPE_TO_COHORT_STAGE = {
    "preflight": "development_validation",
    "formal_47x3": "final_baseline",
}
HISTORICAL_OUTPUT_ROOTS = {
    "evaluation/friedrich_v2/cohorts/small_validation_20260828",
    "evaluation/friedrich_v2/results/small_validation_20260828",
}

FROZEN_GENERATION_SETTINGS = {
    "mode": "baseline",
    "pipeline_profile": "semantic_deterministic",
    "response_mode": "full",
    "candidate_count": 3,
    "maximum_attempts_per_candidate": 3,
    "accept_first_valid_graph": True,
    "use_experimental_compiler": False,
    "enable_sketch_review_agent": False,
    "enable_prompted_sketch_repair_agent": False,
    "enable_graph_repair_agent": False,
    "human_selection": False,
}


class GenerationInvocationError(RuntimeError):
    def __init__(self, reason: str, *, stage: str = "generation_endpoint", evidence: Mapping[str, Any] | None = None) -> None:
        super().__init__(reason)
        self.stage = stage
        self.evidence = dict(evidence or {})


class CohortInfrastructureError(RuntimeError):
    pass


class SingleCandidateGenerator(Protocol):
    def generate(self, process_text: str, request_payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class HttpSingleCandidateGenerator:
    endpoint: str
    timeout_seconds: int

    def generate(self, process_text: str, request_payload: Mapping[str, Any]) -> Mapping[str, Any]:
        payload = dict(request_payload)
        payload["process_text"] = process_text
        request = Request(
            self.endpoint,
            data=canonical_json(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - frozen local endpoint
                body = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {401, 403}:
                raise CohortInfrastructureError(f"Generation endpoint authentication failed with HTTP {exc.code}") from exc
            raise GenerationInvocationError(
                f"Generation endpoint returned HTTP {exc.code}",
                evidence={"http_status": exc.code, "response_body": body},
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise GenerationInvocationError(
                f"Generation endpoint transport failed: {type(exc).__name__}",
                evidence={"error_type": type(exc).__name__, "message": str(exc)},
            ) from exc
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise GenerationInvocationError(
                "Generation endpoint returned invalid JSON",
                evidence={"response_body": body},
            ) from exc
        if not isinstance(parsed, Mapping):
            raise GenerationInvocationError("Generation endpoint response must be an object")
        return parsed


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _contains_secret_field(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower()
            if any(token in normalized for token in ("api_key", "secret", "credential", "password", "token")):
                return True
            if _contains_secret_field(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_secret_field(item) for item in value)
    return False


def load_small_validation_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != CONFIG_SCHEMA:
        raise ValueError("A Friedrich V2 small-validation configuration is required")
    if _contains_secret_field(payload):
        raise ValueError("Small-validation configuration must not contain secret fields")
    generation = payload.get("generation")
    evaluation = payload.get("evaluation")
    cases = payload.get("small_validation", {}).get("case_ids")
    if not isinstance(generation, Mapping) or not isinstance(evaluation, Mapping):
        raise ValueError("Small-validation generation and evaluation configuration are required")
    expected_generation = {
        "system_commit": "8b3cdab756622cab7ecd1ed143b4a736d14f46ed",
        "mode": "baseline",
        "pipeline_profile": "semantic_deterministic",
        "response_mode": "full",
        "candidate_count": 3,
        "maximum_attempts_per_candidate": 3,
        "accept_first_valid_graph": True,
        "use_experimental_compiler": False,
        "enable_sketch_review_agent": False,
        "enable_prompted_sketch_repair_agent": False,
        "enable_graph_repair_agent": False,
        "human_selection": False,
    }
    for key, expected in expected_generation.items():
        if generation.get(key) != expected:
            raise ValueError(f"Small-validation generation setting {key} must equal {expected!r}")
    if evaluation.get("action_model") != ACTION_MODEL_NAME:
        raise ValueError("Small-validation Action model does not match the frozen model")
    if evaluation.get("action_model_revision") != ACTION_MODEL_REVISION:
        raise ValueError("Small-validation Action revision does not match the frozen revision")
    if evaluation.get("action_threshold") != ACTION_SIMILARITY_THRESHOLD:
        raise ValueError("Small-validation Action threshold does not match the frozen threshold")
    if cases != ["3-1", "3-6", "3-2", "3-3", "4-1"]:
        raise ValueError("Small-validation case set or order differs from the frozen five-case set")
    if payload.get("preflight", {}).get("status") != "ready_for_generation":
        raise ValueError("Small-validation preflight is not frozen as ready_for_generation")
    return payload


def _validate_v2_output_root(value: Any, *, run_type: str, run_id: str, kind: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"V2 {kind} output root must be a non-empty repository-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"V2 {kind} output root must remain inside the evaluator repository")
    normalized = path.as_posix()
    if normalized in HISTORICAL_OUTPUT_ROOTS or "small_validation_20260828" in path.parts:
        raise ValueError("V2 run configuration must not target historical V1 output paths")
    run_prefix = "v2_preflight_" if run_type == "preflight" else "v2_formal_47x3"
    expected_parent = f"evaluation/friedrich_v2/{kind}"
    if path.parent.as_posix() != expected_parent or not path.name.startswith(run_prefix):
        raise ValueError(f"V2 {kind} output root does not match run_type={run_type}")
    if run_id not in path.name:
        raise ValueError(f"V2 {kind} output root must contain the run_id")
    return normalized


def load_run_config(path: str | Path, source_manifest_path: str | Path) -> dict[str, Any]:
    """Load a strict V2 execution configuration without changing scoring policy."""
    config_path = Path(path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    required_root_fields = {
        "schema_version", "run_id", "run_type", "evaluation_version",
        "generator_commit", "generator_branch", "generator_worktree",
        "dataset_commit", "evaluator_base_commit", "evaluator_snapshot_id",
        "case_ids", "candidates_per_case", "source", "generation", "runtime",
        "evaluation", "artifacts", "preflight",
    }
    if not isinstance(payload, dict) or payload.get("schema_version") != RUN_CONFIG_SCHEMA:
        raise ValueError("A Friedrich V2 versioned run configuration is required")
    if set(payload) != required_root_fields:
        raise ValueError("V2 run configuration contains missing or unexpected root fields")
    if _contains_secret_field(payload):
        raise ValueError("V2 run configuration must not contain secret fields")

    run_type = payload.get("run_type")
    if run_type not in RUN_TYPE_TO_COHORT_STAGE:
        raise ValueError("V2 run_type must be preflight or formal_47x3")
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("V2 run_id must be a non-empty string")
    if payload.get("evaluation_version") != V2_EVALUATION_VERSION:
        raise ValueError("V2 evaluation_version is not the frozen Revised Generator V2 identity")
    if payload.get("generator_commit") != V2_GENERATOR_COMMIT:
        raise ValueError("V2 generator commit differs from the frozen Revised Generator V2 commit")
    if payload.get("generator_branch") != V2_GENERATOR_BRANCH:
        raise ValueError("V2 generator branch differs from the frozen Revised Generator V2 branch")
    if Path(str(payload.get("generator_worktree", ""))).resolve() != Path(
        "/Users/queenie/Desktop/studio-final-v2-stable"
    ):
        raise ValueError("V2 generator worktree differs from the frozen Revised Generator V2 worktree")
    if payload.get("dataset_commit") != V2_DATASET_COMMIT:
        raise ValueError("V2 dataset commit differs from the frozen Friedrich dataset")
    if payload.get("evaluator_base_commit") != HISTORICAL_EVALUATOR_COMMIT:
        raise ValueError("V2 evaluator base commit does not preserve the historical frozen release")
    snapshot_id = payload.get("evaluator_snapshot_id")
    if (
        not isinstance(snapshot_id, str)
        or len(snapshot_id) != 64
        or any(character not in "0123456789abcdef" for character in snapshot_id)
    ):
        raise ValueError("V2 evaluator snapshot identity must be a 64-character SHA-256")
    if payload.get("candidates_per_case") != 3:
        raise ValueError("V2 runs require exactly 3 candidates per case")

    source_path = Path(source_manifest_path).resolve()
    source = load_source_manifest(source_path, verify_files=True)
    source_ids = tuple(case["case_id"] for case in source["cases"])
    source_commits = {case["source_repository_commit"] for case in source["cases"]}
    source_config = payload.get("source")
    if not isinstance(source_config, Mapping):
        raise ValueError("V2 source configuration is required")
    if set(source_config) != {
        "repository_identity", "dataset_commit", "source_manifest_path",
        "source_manifest_sha256", "process_text_decoding_policy",
    }:
        raise ValueError("V2 source configuration contains missing or unexpected fields")
    if source_config.get("source_manifest_sha256") != sha256_file(source_path):
        raise ValueError("V2 source manifest hash differs from the configured source manifest")
    if source_config.get("dataset_commit") != V2_DATASET_COMMIT or source_commits != {V2_DATASET_COMMIT}:
        raise ValueError("V2 source manifest does not identify the frozen dataset commit")

    case_ids = payload.get("case_ids")
    expected_ids = PREFLIGHT_CASE_IDS if run_type == "preflight" else source_ids
    if not isinstance(case_ids, list) or tuple(case_ids) != expected_ids:
        expected = "the five frozen developmental cases" if run_type == "preflight" else "all 47 source cases"
        raise ValueError(f"V2 {run_type} must contain exactly {expected} in frozen order")

    generation = payload.get("generation")
    if not isinstance(generation, Mapping):
        raise ValueError("V2 generation configuration is required")
    if set(generation) != {
        "repository_identity", "system_commit", "endpoint", "mode", "pipeline_profile",
        "response_mode", "candidate_count", "maximum_attempts_per_candidate",
        "accept_first_valid_graph", "use_experimental_compiler", "enable_sketch_review_agent",
        "enable_prompted_sketch_repair_agent", "enable_graph_repair_agent", "human_selection",
        "topology_model", "semantic_model", "model_identifier_status",
        "request_parameter_policy", "candidate_retry_policy", "request_timeout_seconds",
    }:
        raise ValueError("V2 generation configuration contains missing or unexpected fields")
    if generation.get("system_commit") != payload["generator_commit"]:
        raise ValueError("V2 generation system commit disagrees with run identity")
    for key, expected in FROZEN_GENERATION_SETTINGS.items():
        if generation.get(key) != expected:
            raise ValueError(f"V2 generation setting {key} must equal {expected!r}")
    frozen_generation_identity = {
        "endpoint": "http://api.ai4mde.localhost/api/v1/generate-model",
        "topology_model": "gpt-4o",
        "semantic_model": "gpt-4o",
        "request_timeout_seconds": 300,
        "request_parameter_policy": {
            "temperature": "not explicitly set",
            "seed": "not explicitly set",
            "top_p": "not explicitly set",
            "penalties": "not explicitly set",
        },
    }
    for key, expected in frozen_generation_identity.items():
        if generation.get(key) != expected:
            raise ValueError(f"V2 generation setting {key} differs from the frozen profile")
    expected_retry_policy = (
        "three permanent candidate slots; maximum 3 complete top-level attempts per slot; "
        "accept first adapter-valid ActivityGraph; never retry a successful slot; never inspect evaluation scores"
    )
    if generation.get("candidate_retry_policy") != expected_retry_policy:
        raise ValueError("V2 candidate retry/failure policy differs from the frozen policy")

    evaluation = payload.get("evaluation")
    if not isinstance(evaluation, Mapping):
        raise ValueError("V2 evaluation configuration is required")
    if set(evaluation) != {
        "evaluator_snapshot_id", "action_model", "action_model_revision", "action_threshold",
        "human_review_seed", "failure_policy", "aggregation_policy",
    }:
        raise ValueError("V2 evaluation configuration contains missing or unexpected fields")
    frozen_evaluation = {
        "action_model": ACTION_MODEL_NAME,
        "action_model_revision": ACTION_MODEL_REVISION,
        "action_threshold": ACTION_SIMILARITY_THRESHOLD,
        "human_review_seed": 20260827,
    }
    for key, expected in frozen_evaluation.items():
        if evaluation.get(key) != expected:
            raise ValueError(f"V2 evaluation setting {key} must equal {expected!r}")
    if evaluation.get("evaluator_snapshot_id") != snapshot_id:
        raise ValueError("V2 evaluator snapshot fields disagree")
    expected_failure_policy = (
        "failed candidates retain N/A Action, Flow, and Structure metrics; successful candidates "
        "are never retried for model quality"
    )
    expected_aggregation_policy = (
        "three candidates nested within each case; arithmetic mean/minimum/maximum only for "
        "complete 3-of-3 cases"
    )
    if evaluation.get("failure_policy") != expected_failure_policy:
        raise ValueError("V2 failure policy differs from the frozen methodology")
    if evaluation.get("aggregation_policy") != expected_aggregation_policy:
        raise ValueError("V2 aggregation policy differs from the frozen methodology")

    runtime = payload.get("runtime")
    frozen_runtime = {
        "generation_python": "3.12.1",
        "openai_sdk": "1.47.0",
        "generation_api_image_digest": "sha256:baf5891969578626335d24d9a4f41489ee7a6d37d7c9398850a85ad062daba7a",
        "postgres_image_digest": "sha256:0b657ff48d7f76a1e907f381b1693eb4f2bf54c1d2df4feb6743d7dc601768dd",
        "traefik_image_digest": "sha256:a9890c898f379c1905ee5b28342f6b408dc863f08db2dab20e46c267d1ff463a",
        "generation_python_hash_seed": "random as defined by the frozen Dockerfile",
    }
    if runtime != frozen_runtime:
        raise ValueError("V2 runtime identity differs from the frozen generation runtime")

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise ValueError("V2 artifact configuration is required")
    if set(artifacts) != {
        "output_root", "results_output_root", "attempt_provenance_policy", "hash_policy",
    }:
        raise ValueError("V2 artifact configuration contains missing or unexpected fields")
    cohort_root = _validate_v2_output_root(
        artifacts.get("output_root"), run_type=run_type, run_id=run_id, kind="cohorts"
    )
    results_root = _validate_v2_output_root(
        artifacts.get("results_output_root"), run_type=run_type, run_id=run_id, kind="results"
    )
    if cohort_root == results_root:
        raise ValueError("V2 cohort and result output roots must be distinct")
    status = payload.get("preflight", {}).get("status")
    if set(payload.get("preflight", {})) != {"status", "purpose"}:
        raise ValueError("V2 authorization configuration contains missing or unexpected fields")
    if status not in {"ready_for_generation", "planned_not_authorized"}:
        raise ValueError("V2 run configuration has an unsupported authorization status")
    return payload


def _case_ids(config: Mapping[str, Any]) -> tuple[str, ...]:
    if config.get("schema_version") == RUN_CONFIG_SCHEMA:
        return tuple(config["case_ids"])
    return tuple(config["small_validation"]["case_ids"])


def _cohort_stage(config: Mapping[str, Any]) -> str:
    if config.get("schema_version") == RUN_CONFIG_SCHEMA:
        return RUN_TYPE_TO_COHORT_STAGE[str(config["run_type"])]
    return "development_validation"


def verify_generation_worktree(
    path: str | Path, expected_commit: str, expected_branch: str | None = None
) -> None:
    worktree = Path(path).resolve()
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=worktree,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=worktree,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        branch = (
            subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=worktree,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            if expected_branch is not None
            else None
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CohortInfrastructureError("Could not verify the frozen generation worktree") from exc
    if commit != expected_commit:
        raise CohortInfrastructureError(
            f"Generation worktree is at {commit}, expected {expected_commit}"
        )
    if status:
        raise CohortInfrastructureError("Generation worktree has tracked or untracked changes")
    if expected_branch is not None and branch != expected_branch:
        raise CohortInfrastructureError(
            f"Generation worktree is on branch {branch}, expected {expected_branch}"
        )


def _request_payload(config: Mapping[str, Any]) -> dict[str, Any]:
    generation = config["generation"]
    return {
        "mode": generation["mode"],
        "pipeline_profile": generation["pipeline_profile"],
        "response_mode": generation["response_mode"],
        "use_experimental_compiler": generation["use_experimental_compiler"],
        "enable_sketch_review_agent": generation["enable_sketch_review_agent"],
        "enable_prompted_sketch_repair_agent": generation["enable_prompted_sketch_repair_agent"],
        "enable_graph_repair_agent": generation["enable_graph_repair_agent"],
    }


def _read_process_text(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def _extract_single_candidate(
    response: Mapping[str, Any], request_payload: Mapping[str, Any]
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    echoed_fields = (
        "mode",
        "pipeline_profile",
        "use_experimental_compiler",
        "enable_sketch_review_agent",
        "enable_prompted_sketch_repair_agent",
        "enable_graph_repair_agent",
    )
    mismatches = {
        field: {"expected": request_payload[field], "actual": response.get(field)}
        for field in echoed_fields
        if response.get(field) != request_payload[field]
    }
    if mismatches:
        raise CohortInfrastructureError(
            f"Generation endpoint response does not match frozen request settings: {mismatches}"
        )
    systems = response.get("systems")
    if not isinstance(systems, list) or len(systems) != 1 or not isinstance(systems[0], Mapping):
        raise GenerationInvocationError("Single-candidate invocation did not return exactly one system")
    system = systems[0]
    graph = system.get("activity_graph")
    if not isinstance(graph, Mapping):
        raise GenerationInvocationError("Generation response does not contain an ActivityGraph", stage="response_validation")
    try:
        activity_graph_to_eval_graph(graph)
    except (TypeError, ValueError) as exc:
        raise GenerationInvocationError(
            f"Generated ActivityGraph failed V2 adapter validation: {exc}",
            stage="activity_graph_validation",
        ) from exc
    return dict(graph), system


def _new_state(config: Mapping[str, Any], config_path: Path) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA,
        "config_sha256": sha256_file(config_path),
        "cohort_id": config.get("cohort_id", config.get("run_id")),
        "cases": {
            case_id: {
                candidate_id: {"candidate_id": candidate_id, "attempts": [], "generation_status": "pending"}
                for candidate_id in EXPECTED_CANDIDATE_IDS
            }
            for case_id in _case_ids(config)
        },
    }


def _load_or_create_state(output_root: Path, config: Mapping[str, Any], config_path: Path) -> dict[str, Any]:
    state_path = output_root / "generation_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("schema_version") != STATE_SCHEMA or state.get("config_sha256") != sha256_file(config_path):
            raise ValueError("Existing generation state does not match the frozen configuration")
        return state
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"Generation output directory is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    state = _new_state(config, config_path)
    _write_json_atomic(state_path, state)
    return state


def _archive_success(
    candidate_dir: Path,
    response: Mapping[str, Any],
    graph: Mapping[str, Any],
    system: Mapping[str, Any],
) -> dict[str, str]:
    response_path = candidate_dir / "raw_generation_response.json"
    graph_path = candidate_dir / "activity_graph.json"
    topology_path = candidate_dir / "topology_artifact.json"
    semantic_path = candidate_dir / "semantic_sketch_plan.json"
    stage_path = candidate_dir / "stage_artifacts.json"
    _write_json_atomic(response_path, response)
    _write_json_atomic(graph_path, graph)
    if system.get("topology_artifact") is not None:
        _write_json_atomic(topology_path, system["topology_artifact"])
    if system.get("semantic_sketch_plan") is not None:
        _write_json_atomic(semantic_path, system["semantic_sketch_plan"])
    _write_json_atomic(stage_path, {
        "executed_stages": system.get("executed_stages") or [],
        "topology_artifact_path": str(topology_path.resolve()) if topology_path.exists() else None,
        "semantic_sketch_plan_path": str(semantic_path.resolve()) if semantic_path.exists() else None,
        "import_error": system.get("import_error"),
    })
    return {
        "activity_graph_path": str(graph_path.resolve()),
        "activity_graph_sha256": sha256_file(graph_path),
        "raw_response_path": str(response_path.resolve()),
        "stage_artifacts_path": str(stage_path.resolve()),
    }


def generate_candidate_slots(
    *,
    config: Mapping[str, Any],
    config_path: Path,
    source_cases: Mapping[str, Mapping[str, Any]],
    output_root: Path,
    generator: SingleCandidateGenerator,
) -> dict[str, Any]:
    state = _load_or_create_state(output_root, config, config_path)
    request_payload = _request_payload(config)
    state_path = output_root / "generation_state.json"
    for case_id in _case_ids(config):
        source_case = source_cases[case_id]
        process_text = _read_process_text(source_case["process_text_path"])
        for candidate_id in EXPECTED_CANDIDATE_IDS:
            candidate = state["cases"][case_id][candidate_id]
            if candidate["generation_status"] in {"success", "failed"}:
                continue
            candidate_dir = output_root / "cases" / case_id / candidate_id
            for attempt_index in range(len(candidate["attempts"]) + 1, MAXIMUM_ATTEMPTS_PER_CANDIDATE + 1):
                attempt_dir = candidate_dir / "attempts"
                try:
                    attempted_at = datetime.now(timezone.utc).isoformat()
                    response = generator.generate(process_text, request_payload)
                    graph, system = _extract_single_candidate(response, request_payload)
                    evidence = _archive_success(candidate_dir, response, graph, system)
                    candidate["attempts"].append({
                        "attempt_index": attempt_index,
                        "attempt_status": "success",
                        "evidence": {**evidence, "attempted_at_utc": attempted_at},
                    })
                    candidate.update({
                        "generation_status": "success",
                        "generated_model_path": evidence["activity_graph_path"],
                        "generated_model_sha256": evidence["activity_graph_sha256"],
                        "failure_reason": None,
                        "failure_stage": None,
                    })
                    _write_json_atomic(state_path, state)
                    break
                except CohortInfrastructureError:
                    _write_json_atomic(state_path, state)
                    raise
                except GenerationInvocationError as exc:
                    failure_path = attempt_dir / f"attempt_{attempt_index}_failure.json"
                    failure = {
                        "attempt_index": attempt_index,
                        "failure_reason": str(exc),
                        "failure_stage": exc.stage,
                        "evidence": exc.evidence,
                    }
                    _write_json_atomic(failure_path, failure)
                    candidate["attempts"].append({
                        "attempt_index": attempt_index,
                        "attempt_status": "failed",
                        "failure_reason": str(exc),
                        "failure_stage": exc.stage,
                        "evidence": {
                            "failure_artifact_path": str(failure_path.resolve()),
                            "attempted_at_utc": attempted_at,
                        },
                    })
                    if attempt_index == MAXIMUM_ATTEMPTS_PER_CANDIDATE:
                        candidate.update({
                            "generation_status": "failed",
                            "generated_model_path": None,
                            "generated_model_sha256": None,
                            "failure_reason": str(exc),
                            "failure_stage": exc.stage,
                        })
                    _write_json_atomic(state_path, state)
    return state


def build_generated_manifest(config: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    cases = []
    for case_id in _case_ids(config):
        candidates = []
        for generation_index, candidate_id in enumerate(EXPECTED_CANDIDATE_IDS, start=1):
            state_candidate = state["cases"][case_id][candidate_id]
            if state_candidate["generation_status"] not in {"success", "failed"}:
                raise ValueError(f"Candidate {case_id}/{candidate_id} is not terminal")
            candidates.append({
                "candidate_id": candidate_id,
                "generation_index": generation_index,
                "generation_status": state_candidate["generation_status"],
                "attempt_count": len(state_candidate["attempts"]),
                "attempts": state_candidate["attempts"],
                "generated_model_path": state_candidate.get("generated_model_path"),
                "generated_model_sha256": state_candidate.get("generated_model_sha256"),
                "failure_reason": state_candidate.get("failure_reason"),
                "failure_stage": state_candidate.get("failure_stage"),
            })
        cases.append({"case_id": case_id, "candidates": candidates})
    generation = config["generation"]
    runtime = config["runtime"]
    return {
        "schema_version": "friedrich-v2-generated-manifest/v3",
        "cohort_id": config.get("cohort_id", config.get("run_id")),
        "cohort_stage": _cohort_stage(config),
        "condition": "ai_only_three_candidate_baseline",
        "expected_candidate_count": 3,
        "human_selection": False,
        "maximum_attempts_per_candidate": 3,
        "run_integrity_status": "valid",
        "generation_provenance": {
            "generated_system_commit": generation["system_commit"],
            "pipeline_profile": generation["pipeline_profile"],
            "generation_configuration": _request_payload(config),
            "model_identifier": {
                "topology": generation["topology_model"],
                "semantic": generation["semantic_model"],
            },
            "runtime_environment": runtime,
            "retry_failure_policy": generation["candidate_retry_policy"],
        },
        "cases": cases,
    }


def run(config_path: str | Path, source_manifest_path: str | Path, output_root: str | Path, generator: SingleCandidateGenerator) -> Path:
    config_path = Path(config_path).resolve()
    source_path = Path(source_manifest_path).resolve()
    schema = json.loads(config_path.read_text(encoding="utf-8")).get("schema_version")
    config = (
        load_run_config(config_path, source_path)
        if schema == RUN_CONFIG_SCHEMA
        else load_small_validation_config(config_path)
    )
    source_payload = load_source_manifest(source_path, verify_files=True)
    expected_source_hash = config.get("source", {}).get("source_manifest_sha256")
    if expected_source_hash != sha256_file(source_path):
        raise ValueError("Source manifest does not match the frozen execution configuration")
    source_cases = {case["case_id"]: case for case in source_payload["cases"]}
    missing = set(_case_ids(config)) - set(source_cases)
    if missing:
        raise ValueError(f"Configured cases are missing from source manifest: {sorted(missing)}")
    output = Path(output_root).resolve()
    if schema == RUN_CONFIG_SCHEMA:
        expected_output = (config_path.parents[3] / config["artifacts"]["output_root"]).resolve()
        if output != expected_output:
            raise ValueError("Output root differs from the V2 run configuration")
        if config["preflight"]["status"] != "ready_for_generation":
            raise CohortInfrastructureError("V2 run configuration is planned but not authorized for generation")
    state = generate_candidate_slots(
        config=config,
        config_path=config_path,
        source_cases=source_cases,
        output_root=output,
        generator=generator,
    )
    manifest_path = output / "generated_manifest.json"
    _write_json_atomic(manifest_path, build_generated_manifest(config, state))
    return manifest_path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Generate a strictly configured Friedrich V2 cohort")
    result.add_argument("--config", required=True)
    result.add_argument("--source-manifest", required=True)
    result.add_argument("--generation-worktree", required=True)
    result.add_argument("--output-root")
    return result


def main() -> None:
    args = parser().parse_args()
    config_path = Path(args.config).resolve()
    source_path = Path(args.source_manifest).resolve()
    schema = json.loads(config_path.read_text(encoding="utf-8")).get("schema_version")
    config = (
        load_run_config(config_path, source_path)
        if schema == RUN_CONFIG_SCHEMA
        else load_small_validation_config(config_path)
    )
    if schema == RUN_CONFIG_SCHEMA:
        if config["preflight"]["status"] != "ready_for_generation":
            raise CohortInfrastructureError("V2 run configuration is planned but not authorized for generation")
        if Path(args.generation_worktree).resolve() != Path(config["generator_worktree"]).resolve():
            raise CohortInfrastructureError("Generation worktree differs from the V2 run configuration")
    verify_generation_worktree(
        args.generation_worktree,
        config["generation"]["system_commit"],
        config["generator_branch"] if schema == RUN_CONFIG_SCHEMA else None,
    )
    endpoint = str(config["generation"]["endpoint"])
    timeout = int(config["generation"]["request_timeout_seconds"])
    repository_root = config_path.parents[3]
    frozen_output = (repository_root / config["artifacts"]["output_root"]).resolve()
    output_root = Path(args.output_root).resolve() if args.output_root else frozen_output
    if output_root != frozen_output:
        raise ValueError("Output root differs from the frozen execution configuration")
    run(config_path, source_path, output_root, HttpSingleCandidateGenerator(endpoint, timeout))


if __name__ == "__main__":
    main()
