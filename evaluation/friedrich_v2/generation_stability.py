from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .core import sha256_file
from .generation import (
    CohortInfrastructureError,
    GenerationInvocationError,
    HttpSingleCandidateGenerator,
    SingleCandidateGenerator,
    _extract_single_candidate,
    _read_process_text,
    _write_json_atomic,
    verify_generation_worktree,
)
from .manifests import load_source_manifest


CONFIG_SCHEMA = "friedrich-v2-generation-stability-config/v1"
STATE_SCHEMA = "friedrich-v2-generation-stability-state/v1"
MANIFEST_SCHEMA = "friedrich-v2-generation-stability-manifest/v1"
RUN_TYPE = "generation_stability_47x1"
CANDIDATE_ID = "candidate_1"
MAXIMUM_ATTEMPTS = 3
GENERATOR_COMMIT = "4be4c5b7b30aaff0433d4406056a0cf5c8fc63a9"
GENERATOR_BRANCH = "feature/final-v2-stable"
GENERATOR_WORKTREE = Path("/Users/queenie/Desktop/studio-final-v2-stable")
DATASET_COMMIT = "4015ddfe5338ae3f1e12fb2d8c474244fbf8647d"


def _contains_secret_field(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower()
            if any(token in normalized for token in ("api_key", "secret", "credential", "password", "token")):
                return True
            if _contains_secret_field(nested):
                return True
    if isinstance(value, list):
        return any(_contains_secret_field(item) for item in value)
    return False


def _snapshot_id(snapshot_path: Path) -> str:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    files = snapshot.get("files")
    if not isinstance(files, Mapping):
        raise ValueError("Generation-stability orchestration snapshot is malformed")
    repository_root = snapshot_path.parents[2]
    actual = {
        name: sha256_file(repository_root / name)
        for name in files
    }
    if actual != files:
        raise ValueError("Generation-stability orchestration files differ from the frozen snapshot")
    snapshot_id = hashlib.sha256(
        json.dumps(actual, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if snapshot.get("snapshot_id") != snapshot_id:
        raise ValueError("Generation-stability orchestration snapshot ID is inconsistent")
    return snapshot_id


def load_config(
    config_path: str | Path,
    source_manifest_path: str | Path,
    snapshot_path: str | Path,
) -> dict[str, Any]:
    path = Path(config_path).resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected_root_fields = {
        "schema_version", "run_id", "run_type", "orchestration_snapshot_id",
        "generator", "source", "case_ids", "candidates_per_case", "generation",
        "runtime", "artifacts", "authorization",
    }
    if not isinstance(payload, dict) or payload.get("schema_version") != CONFIG_SCHEMA:
        raise ValueError("A versioned Friedrich 47x1 generation-stability configuration is required")
    if set(payload) != expected_root_fields:
        raise ValueError("Generation-stability configuration has missing or unexpected root fields")
    if _contains_secret_field(payload):
        raise ValueError("Generation-stability configuration must not contain secret fields")
    if payload.get("run_type") != RUN_TYPE:
        raise ValueError(f"run_type must be {RUN_TYPE}")
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id.startswith("v2_stability_47x1_"):
        raise ValueError("Generation-stability run_id must use the v2_stability_47x1_ prefix")

    snapshot = Path(snapshot_path).resolve()
    actual_snapshot_id = _snapshot_id(snapshot)
    if payload.get("orchestration_snapshot_id") != actual_snapshot_id:
        raise ValueError("Generation-stability orchestration snapshot identity differs")

    generator = payload.get("generator")
    expected_generator = {
        "repository_identity": "AI4MDE Studio V1-based Final V2 stability candidate",
        "base_commit": "8b3cdab756622cab7ecd1ed143b4a736d14f46ed",
        "commit": GENERATOR_COMMIT,
        "branch": GENERATOR_BRANCH,
        "worktree": str(GENERATOR_WORKTREE),
    }
    if generator != expected_generator:
        raise ValueError("Generation-stability generator identity differs from the frozen candidate")

    source_path = Path(source_manifest_path).resolve()
    source_payload = load_source_manifest(source_path, verify_files=True)
    source_ids = [case["case_id"] for case in source_payload["cases"]]
    source_commits = {case["source_repository_commit"] for case in source_payload["cases"]}
    source = payload.get("source")
    expected_source = {
        "repository_identity": "FabianFriedrich/Text2Process",
        "dataset_commit": DATASET_COMMIT,
        "source_manifest_path": "evaluation/friedrich_v2/manifests/source_manifest.json",
        "source_manifest_sha256": sha256_file(source_path),
        "process_text_decoding_policy": "decode as UTF-8; on UnicodeDecodeError decode as Windows-1252",
    }
    if source != expected_source or source_commits != {DATASET_COMMIT}:
        raise ValueError("Generation-stability source identity differs from the frozen dataset")
    if payload.get("case_ids") != source_ids or len(source_ids) != 47:
        raise ValueError("Generation-stability run requires exactly all 47 source cases in frozen order")
    if payload.get("candidates_per_case") != 1:
        raise ValueError("Generation-stability run requires exactly 1 candidate per case")

    generation = payload.get("generation")
    expected_generation = {
        "system_commit": GENERATOR_COMMIT,
        "endpoint": "http://api.ai4mde.localhost/api/v1/generate-model",
        "mode": "baseline",
        "pipeline_profile": "semantic_deterministic",
        "response_mode": "full",
        "candidate_count": 1,
        "maximum_attempts_per_candidate": MAXIMUM_ATTEMPTS,
        "accept_first_technically_valid_graph": True,
        "use_experimental_compiler": False,
        "enable_sketch_review_agent": False,
        "enable_prompted_sketch_repair_agent": False,
        "enable_graph_repair_agent": False,
        "human_selection": False,
        "topology_model": "gpt-4o",
        "semantic_model": "gpt-4o",
        "request_timeout_seconds": 300,
        "retry_policy": (
            "one permanent candidate slot per case; maximum 3 complete top-level attempts; "
            "accept first technically valid and imported ActivityGraph; never inspect model quality or scores"
        ),
    }
    if generation != expected_generation:
        raise ValueError("Generation-stability generation profile or retry policy differs")

    expected_runtime = {
        "generation_python": "3.12.1",
        "openai_sdk": "1.47.0",
        "generation_api_image_digest": "sha256:baf5891969578626335d24d9a4f41489ee7a6d37d7c9398850a85ad062daba7a",
        "postgres_image_digest": "sha256:0b657ff48d7f76a1e907f381b1693eb4f2bf54c1d2df4feb6743d7dc601768dd",
        "traefik_image_digest": "sha256:a9890c898f379c1905ee5b28342f6b408dc863f08db2dab20e46c267d1ff463a",
        "generation_python_hash_seed": "random as defined by the frozen Dockerfile",
    }
    if payload.get("runtime") != expected_runtime:
        raise ValueError("Generation-stability runtime identity differs")

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, Mapping) or set(artifacts) != {
        "output_root", "attempt_provenance_policy", "hash_policy"
    }:
        raise ValueError("Generation-stability artifact configuration differs")
    output = Path(str(artifacts.get("output_root", "")))
    if (
        output.is_absolute()
        or ".." in output.parts
        or output.parent.as_posix() != "evaluation/friedrich_v2/cohorts"
        or not output.name.startswith("v2_stability_47x1_")
        or run_id not in output.name
    ):
        raise ValueError("Generation-stability output root is not isolated for this run")
    if payload.get("authorization") != {
        "status": "ready_for_generation",
        "purpose": "47-case by 1-candidate generation-only technical stability test",
    }:
        raise ValueError("Generation-stability run is not authorized")
    return payload


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


def _new_state(config: Mapping[str, Any], config_path: Path) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA,
        "run_id": config["run_id"],
        "config_sha256": sha256_file(config_path),
        "cases": {
            case_id: {
                "case_id": case_id,
                "candidate_id": CANDIDATE_ID,
                "generation_status": "pending",
                "attempts": [],
            }
            for case_id in config["case_ids"]
        },
    }


def _load_or_create_state(output_root: Path, config: Mapping[str, Any], config_path: Path) -> dict[str, Any]:
    state_path = output_root / "generation_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if (
            state.get("schema_version") != STATE_SCHEMA
            or state.get("run_id") != config["run_id"]
            or state.get("config_sha256") != sha256_file(config_path)
            or set(state.get("cases", {})) != set(config["case_ids"])
            or len(state.get("cases", {})) != len(config["case_ids"])
        ):
            raise ValueError("Existing generation-stability checkpoint differs from the frozen run")
        return state
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"Generation-stability output directory is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    state = _new_state(config, config_path)
    _write_json_atomic(state_path, state)
    return state


def _archive_success(
    candidate_dir: Path,
    response: Mapping[str, Any],
    graph: Mapping[str, Any],
    system: Mapping[str, Any],
) -> dict[str, Any]:
    paths = {
        "raw_response": candidate_dir / "raw_generation_response.json",
        "activity_graph": candidate_dir / "activity_graph.json",
        "topology_artifact": candidate_dir / "topology_artifact.json",
        "semantic_sketch_plan": candidate_dir / "semantic_sketch_plan.json",
        "ai4mde_export": candidate_dir / "ai4mde_export.json",
        "technical_status": candidate_dir / "technical_status.json",
    }
    _write_json_atomic(paths["raw_response"], response)
    _write_json_atomic(paths["activity_graph"], graph)
    _write_json_atomic(paths["topology_artifact"], system.get("topology_artifact"))
    _write_json_atomic(paths["semantic_sketch_plan"], system.get("semantic_sketch_plan"))
    _write_json_atomic(paths["ai4mde_export"], system.get("ai4mde"))
    _write_json_atomic(paths["technical_status"], {
        "adapter_validation": "passed",
        "technical_validity": system.get("technical_validity"),
        "import_status": "passed",
        "import_error": None,
        "executed_stages": system.get("executed_stages") or [],
    })
    return {
        f"{name}_path": str(path.resolve())
        for name, path in paths.items()
    } | {
        f"{name}_sha256": sha256_file(path)
        for name, path in paths.items()
    }


def _preserve_process_text(candidate_dir: Path, source_path: Path) -> dict[str, str]:
    process_text_path = candidate_dir / "process_text.txt"
    if not process_text_path.exists():
        process_text_path.parent.mkdir(parents=True, exist_ok=True)
        process_text_path.write_bytes(source_path.read_bytes())
    return {
        "process_text_path": str(process_text_path.resolve()),
        "process_text_sha256": sha256_file(process_text_path),
    }


def _validate_import(system: Mapping[str, Any]) -> None:
    if system.get("import_error") is not None:
        raise GenerationInvocationError(
            "Generated ActivityGraph failed AI4MDE import",
            stage="ai4mde_import",
            evidence={"import_error": system.get("import_error")},
        )
    ai4mde = system.get("ai4mde")
    if not isinstance(ai4mde, list) or not ai4mde:
        raise GenerationInvocationError(
            "Generation response does not contain an AI4MDE export",
            stage="ai4mde_import",
        )


def generate(
    *,
    config: Mapping[str, Any],
    config_path: Path,
    source_cases: Mapping[str, Mapping[str, Any]],
    output_root: Path,
    generator: SingleCandidateGenerator,
) -> dict[str, Any]:
    state = _load_or_create_state(output_root, config, config_path)
    state_path = output_root / "generation_state.json"
    request_payload = _request_payload(config)
    for case_id in config["case_ids"]:
        candidate = state["cases"][case_id]
        if candidate["generation_status"] in {"success", "failed"}:
            continue
        source_path = Path(source_cases[case_id]["process_text_path"])
        process_text = _read_process_text(source_path)
        candidate_dir = output_root / "cases" / case_id / CANDIDATE_ID
        candidate.update(_preserve_process_text(candidate_dir, source_path))
        _write_json_atomic(state_path, state)
        attempts_dir = candidate_dir / "attempts"
        for attempt_index in range(len(candidate["attempts"]) + 1, MAXIMUM_ATTEMPTS + 1):
            attempted_at = datetime.now(timezone.utc).isoformat()
            response: Mapping[str, Any] | None = None
            try:
                response = generator.generate(process_text, request_payload)
                graph, system = _extract_single_candidate(response, request_payload)
                _validate_import(system)
                evidence = _archive_success(candidate_dir, response, graph, system)
                evidence.update({
                    "process_text_path": candidate["process_text_path"],
                    "process_text_sha256": candidate["process_text_sha256"],
                })
                candidate["attempts"].append({
                    "attempt_index": attempt_index,
                    "attempt_status": "success",
                    "attempted_at_utc": attempted_at,
                    "evidence": evidence,
                })
                candidate.update({
                    "generation_status": "success",
                    "attempt_count": attempt_index,
                    "generated_model_path": evidence["activity_graph_path"],
                    "generated_model_sha256": evidence["activity_graph_sha256"],
                    "technical_validity_status": "passed",
                    "import_status": "passed",
                    "failure_reason": None,
                    "failure_stage": None,
                })
                _write_json_atomic(state_path, state)
                break
            except CohortInfrastructureError:
                _write_json_atomic(state_path, state)
                raise
            except GenerationInvocationError as exc:
                failure_path = attempts_dir / f"attempt_{attempt_index}_failure.json"
                response_evidence: dict[str, str] = {}
                if isinstance(response, Mapping):
                    response_path = attempts_dir / f"attempt_{attempt_index}_raw_generation_response.json"
                    _write_json_atomic(response_path, response)
                    response_evidence = {
                        "raw_response_path": str(response_path.resolve()),
                        "raw_response_sha256": sha256_file(response_path),
                    }
                failure = {
                    "attempt_index": attempt_index,
                    "attempted_at_utc": attempted_at,
                    "failure_reason": str(exc),
                    "failure_stage": exc.stage,
                    "evidence": {**exc.evidence, **response_evidence},
                }
                _write_json_atomic(failure_path, failure)
                candidate["attempts"].append({
                    "attempt_index": attempt_index,
                    "attempt_status": "failed",
                    "attempted_at_utc": attempted_at,
                    "failure_reason": str(exc),
                    "failure_stage": exc.stage,
                    "evidence": {
                        "failure_artifact_path": str(failure_path.resolve()),
                        "failure_artifact_sha256": sha256_file(failure_path),
                        **response_evidence,
                    },
                })
                if attempt_index == MAXIMUM_ATTEMPTS:
                    candidate.update({
                        "generation_status": "failed",
                        "attempt_count": attempt_index,
                        "generated_model_path": None,
                        "generated_model_sha256": None,
                        "technical_validity_status": "failed",
                        "import_status": "failed" if exc.stage == "ai4mde_import" else "not_reached",
                        "failure_reason": str(exc),
                        "failure_stage": exc.stage,
                    })
                _write_json_atomic(state_path, state)
    return state


def build_manifest(config: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    cases = []
    for case_id in config["case_ids"]:
        candidate = state["cases"][case_id]
        if candidate["generation_status"] not in {"success", "failed"}:
            raise ValueError(f"Generation-stability candidate {case_id} is not terminal")
        cases.append({"case_id": case_id, "candidates": [candidate]})
    return {
        "schema_version": MANIFEST_SCHEMA,
        "run_id": config["run_id"],
        "run_type": RUN_TYPE,
        "generation_only": True,
        "scoring_status": "not_run_by_design",
        "human_review_status": "not_run_by_design",
        "expected_case_count": 47,
        "expected_candidate_count_per_case": 1,
        "maximum_attempts_per_candidate": MAXIMUM_ATTEMPTS,
        "generator": config["generator"],
        "orchestration_snapshot_id": config["orchestration_snapshot_id"],
        "source": config["source"],
        "generation": config["generation"],
        "runtime": config["runtime"],
        "cases": cases,
    }


def run(
    config_path: str | Path,
    source_manifest_path: str | Path,
    snapshot_path: str | Path,
    output_root: str | Path,
    generator: SingleCandidateGenerator,
) -> Path:
    config_path = Path(config_path).resolve()
    source_path = Path(source_manifest_path).resolve()
    config = load_config(config_path, source_path, snapshot_path)
    repository_root = config_path.parents[3]
    expected_output = (repository_root / config["artifacts"]["output_root"]).resolve()
    output = Path(output_root).resolve()
    if output != expected_output:
        raise ValueError("Output root differs from the frozen generation-stability configuration")
    source = load_source_manifest(source_path, verify_files=True)
    source_cases = {case["case_id"]: case for case in source["cases"]}
    state = generate(
        config=config,
        config_path=config_path,
        source_cases=source_cases,
        output_root=output,
        generator=generator,
    )
    manifest_path = output / "generation_manifest.json"
    _write_json_atomic(manifest_path, build_manifest(config, state))
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen Friedrich 47x1 generation-only stability test")
    parser.add_argument("--config", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--orchestration-snapshot", required=True)
    parser.add_argument("--generation-worktree", required=True)
    parser.add_argument("--output-root")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    source_path = Path(args.source_manifest).resolve()
    snapshot_path = Path(args.orchestration_snapshot).resolve()
    config = load_config(config_path, source_path, snapshot_path)
    if Path(args.generation_worktree).resolve() != GENERATOR_WORKTREE:
        raise CohortInfrastructureError("Generation worktree differs from the frozen stability candidate")
    verify_generation_worktree(GENERATOR_WORKTREE, GENERATOR_COMMIT, GENERATOR_BRANCH)
    repository_root = config_path.parents[3]
    frozen_output = (repository_root / config["artifacts"]["output_root"]).resolve()
    output = Path(args.output_root).resolve() if args.output_root else frozen_output
    generator = HttpSingleCandidateGenerator(
        str(config["generation"]["endpoint"]),
        int(config["generation"]["request_timeout_seconds"]),
    )
    run(config_path, source_path, snapshot_path, output, generator)


if __name__ == "__main__":
    main()
