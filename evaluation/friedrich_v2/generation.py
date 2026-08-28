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
STATE_SCHEMA = "friedrich-v2-generation-state/v1"


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


def verify_generation_worktree(path: str | Path, expected_commit: str) -> None:
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
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CohortInfrastructureError("Could not verify the frozen generation worktree") from exc
    if commit != expected_commit:
        raise CohortInfrastructureError(
            f"Generation worktree is at {commit}, expected {expected_commit}"
        )
    if status:
        raise CohortInfrastructureError("Generation worktree has tracked or untracked changes")


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
        "cohort_id": config["cohort_id"],
        "cases": {
            case_id: {
                candidate_id: {"candidate_id": candidate_id, "attempts": [], "generation_status": "pending"}
                for candidate_id in EXPECTED_CANDIDATE_IDS
            }
            for case_id in config["small_validation"]["case_ids"]
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
    for case_id in config["small_validation"]["case_ids"]:
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
    for case_id in config["small_validation"]["case_ids"]:
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
        "cohort_id": config["cohort_id"],
        "cohort_stage": "development_validation",
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
    config = load_small_validation_config(config_path)
    source_path = Path(source_manifest_path).resolve()
    source_payload = load_source_manifest(source_path, verify_files=True)
    expected_source_hash = config.get("source", {}).get("source_manifest_sha256")
    if expected_source_hash != sha256_file(source_path):
        raise ValueError("Source manifest does not match the frozen small-validation configuration")
    source_cases = {case["case_id"]: case for case in source_payload["cases"]}
    missing = set(config["small_validation"]["case_ids"]) - set(source_cases)
    if missing:
        raise ValueError(f"Small-validation cases are missing from source manifest: {sorted(missing)}")
    output = Path(output_root).resolve()
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
    result = argparse.ArgumentParser(description="Generate the frozen five-case Friedrich V2 small-validation cohort")
    result.add_argument("--config", required=True)
    result.add_argument("--source-manifest", required=True)
    result.add_argument("--generation-worktree", required=True)
    result.add_argument("--output-root")
    return result


def main() -> None:
    args = parser().parse_args()
    config_path = Path(args.config).resolve()
    config = load_small_validation_config(config_path)
    verify_generation_worktree(args.generation_worktree, config["generation"]["system_commit"])
    endpoint = str(config["generation"]["endpoint"])
    timeout = int(config["generation"]["request_timeout_seconds"])
    repository_root = config_path.parents[3]
    frozen_output = (repository_root / config["artifacts"]["output_root"]).resolve()
    output_root = Path(args.output_root).resolve() if args.output_root else frozen_output
    if output_root != frozen_output:
        raise ValueError("Output root differs from the frozen small-validation configuration")
    run(config_path, args.source_manifest, output_root, HttpSingleCandidateGenerator(endpoint, timeout))


if __name__ == "__main__":
    main()
