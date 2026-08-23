from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from archive.standalone_experiments import run_semantic_sketch_builder_experiment as runner  # noqa: E402


def _workflow(case_id: str) -> dict[str, str]:
    return {
        "case_id": case_id,
        "name": case_id,
        "process_text": f"Process text for {case_id}.",
    }


def _completed_payload(case_id: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "workflow": case_id,
        "status": "completed",
        "topology_artifact": {"structures": []},
        "semantic_sketch_plan": {"root_actions": [], "branch_plans": []},
        "semantic_deterministic_activity_sketch": {"main_flow": [], "control_blocks": []},
    }


def _success_payload(case_id: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "workflow": case_id,
        "process_text": f"Process text for {case_id}.",
        "status": "completed",
        "topology_artifact": {"structures": []},
        "semantic_sketch_plan": {"root_actions": [], "branch_plans": []},
        "semantic_deterministic_activity_sketch": {"main_flow": [], "control_blocks": []},
        "semantic_deterministic_preservation_report": {
            "summary": {
                "parent_preservation_ratio": 1.0,
                "parent_branch_preservation_ratio": 1.0,
            }
        },
    }


def _write_checkpoint(output_dir: Path, workflow: dict[str, str], payload: dict[str, object]) -> None:
    output_path = runner._workflow_output_path(output_dir, workflow)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def test_completed_case_is_skipped(tmp_path: Path, monkeypatch) -> None:
    workflow = _workflow("1-1")
    _write_checkpoint(tmp_path, workflow, _completed_payload("1-1"))
    called = 0

    def fake_run_case(*args, **kwargs):
        nonlocal called
        called += 1
        return _success_payload("1-1")

    monkeypatch.setattr(runner, "run_semantic_experiment_case", fake_run_case)

    exit_code = runner.run_batch(
        [workflow],
        output_dir=tmp_path,
        model="gpt-4o",
        use_semantic_sketch_builder=True,
        include_current_topology_guided=False,
        inter_case_delay=0,
    )

    assert exit_code == 0
    assert called == 0


def test_unfinished_case_runs_and_is_checkpointed(tmp_path: Path, monkeypatch) -> None:
    workflow = _workflow("2-1")
    called = 0

    def fake_run_case(case, **kwargs):
        nonlocal called
        called += 1
        return _success_payload(case["case_id"])

    monkeypatch.setattr(runner, "run_semantic_experiment_case", fake_run_case)

    exit_code = runner.run_batch(
        [workflow],
        output_dir=tmp_path,
        model="gpt-4o",
        use_semantic_sketch_builder=True,
        include_current_topology_guided=False,
        inter_case_delay=0,
    )

    assert exit_code == 0
    assert called == 1
    output_path = runner._workflow_output_path(tmp_path, workflow)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "completed"


def test_resume_skips_completed_cases_and_runs_only_missing_one(tmp_path: Path, monkeypatch) -> None:
    workflows = [_workflow("1-1"), _workflow("2-1"), _workflow("2-2")]
    _write_checkpoint(tmp_path, workflows[0], _completed_payload("1-1"))
    _write_checkpoint(tmp_path, workflows[1], _completed_payload("2-1"))
    called_case_ids: list[str] = []

    def fake_run_case(case, **kwargs):
        called_case_ids.append(case["case_id"])
        return _success_payload(case["case_id"])

    monkeypatch.setattr(runner, "run_semantic_experiment_case", fake_run_case)

    exit_code = runner.run_batch(
        workflows,
        output_dir=tmp_path,
        model="gpt-4o",
        use_semantic_sketch_builder=True,
        include_current_topology_guided=False,
        inter_case_delay=0,
    )

    assert exit_code == 0
    assert called_case_ids == ["2-2"]


def test_rate_limit_stop_preserves_earlier_checkpoints_and_stops_later_cases(tmp_path: Path, monkeypatch) -> None:
    workflows = [_workflow("1-1"), _workflow("2-1"), _workflow("2-2")]
    called_case_ids: list[str] = []

    def fake_run_case(case, **kwargs):
        called_case_ids.append(case["case_id"])
        if case["case_id"] == "2-1":
            raise Exception("429 Too Many Requests")
        return _success_payload(case["case_id"])

    monkeypatch.setattr(runner, "run_semantic_experiment_case", fake_run_case)

    exit_code = runner.run_batch(
        workflows,
        output_dir=tmp_path,
        model="gpt-4o",
        use_semantic_sketch_builder=True,
        include_current_topology_guided=False,
        inter_case_delay=0,
    )

    assert exit_code == 1
    assert called_case_ids == ["1-1", "2-1"]
    first_payload = json.loads(runner._workflow_output_path(tmp_path, workflows[0]).read_text(encoding="utf-8"))
    second_payload = json.loads(runner._workflow_output_path(tmp_path, workflows[1]).read_text(encoding="utf-8"))
    assert first_payload["status"] == "completed"
    assert second_payload["status"] == "failed_rate_limit"
    assert not runner._workflow_output_path(tmp_path, workflows[2]).exists()


def test_failed_case_is_retryable_later(tmp_path: Path, monkeypatch) -> None:
    workflows = [_workflow("1-1"), _workflow("2-1")]
    _write_checkpoint(tmp_path, workflows[0], _completed_payload("1-1"))
    failed_payload = {
        "case_id": "2-1",
        "workflow": "2-1",
        "status": "failed_rate_limit",
        "error_message": "429 Too Many Requests",
    }
    _write_checkpoint(tmp_path, workflows[1], failed_payload)
    called_case_ids: list[str] = []

    def fake_run_case(case, **kwargs):
        called_case_ids.append(case["case_id"])
        return _success_payload(case["case_id"])

    monkeypatch.setattr(runner, "run_semantic_experiment_case", fake_run_case)

    exit_code = runner.run_batch(
        workflows,
        output_dir=tmp_path,
        model="gpt-4o",
        use_semantic_sketch_builder=True,
        include_current_topology_guided=False,
        inter_case_delay=0,
    )

    assert exit_code == 0
    assert called_case_ids == ["2-1"]


def test_force_rerun_ignores_completed_checkpoint(tmp_path: Path, monkeypatch) -> None:
    workflow = _workflow("1-1")
    _write_checkpoint(tmp_path, workflow, _completed_payload("1-1"))
    called = 0

    def fake_run_case(case, **kwargs):
        nonlocal called
        called += 1
        return _success_payload(case["case_id"])

    monkeypatch.setattr(runner, "run_semantic_experiment_case", fake_run_case)

    exit_code = runner.run_batch(
        [workflow],
        output_dir=tmp_path,
        model="gpt-4o",
        use_semantic_sketch_builder=True,
        include_current_topology_guided=False,
        force=True,
        inter_case_delay=0,
    )

    assert exit_code == 0
    assert called == 1


def test_inter_case_delay_occurs_only_between_completed_run_cases(tmp_path: Path, monkeypatch) -> None:
    workflows = [_workflow("1-1"), _workflow("2-1"), _workflow("2-2"), _workflow("3-6")]
    _write_checkpoint(tmp_path, workflows[0], _completed_payload("1-1"))
    _write_checkpoint(tmp_path, workflows[2], _completed_payload("2-2"))
    called_case_ids: list[str] = []
    sleep_calls: list[float] = []

    def fake_run_case(case, **kwargs):
        called_case_ids.append(case["case_id"])
        return _success_payload(case["case_id"])

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(runner, "run_semantic_experiment_case", fake_run_case)

    exit_code = runner.run_batch(
        workflows,
        output_dir=tmp_path,
        model="gpt-4o",
        use_semantic_sketch_builder=True,
        include_current_topology_guided=False,
        inter_case_delay=1.5,
        sleep_fn=fake_sleep,
    )

    assert exit_code == 0
    assert called_case_ids == ["2-1", "3-6"]
    assert sleep_calls == [1.5]


def test_main_filters_dataset_by_case_ids(tmp_path: Path, monkeypatch) -> None:
    dataset_path = tmp_path / "cases.json"
    dataset_path.write_text(
        json.dumps(
            {
                "workflows": [
                    _workflow("1-1"),
                    _workflow("2-1"),
                    _workflow("4-1"),
                ]
            }
        ),
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    def fake_run_batch(workflows, **kwargs):
        captured["case_ids"] = [workflow["case_id"] for workflow in workflows]
        captured["kwargs"] = kwargs
        return 0

    monkeypatch.setattr(runner, "run_batch", fake_run_batch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_semantic_sketch_builder_experiment.py",
            "--dataset",
            str(dataset_path),
            "--output",
            str(tmp_path / "out"),
            "--case-ids",
            "2-1",
            "4-1",
            "--inter-case-delay",
            "3.5",
            "--force",
            f"--{runner.EXPERIMENT_FLAG_NAME}",
        ],
    )

    exit_code = runner.main()

    assert exit_code == 0
    assert captured["case_ids"] == ["2-1", "4-1"]
    assert captured["kwargs"]["force"] is True
    assert captured["kwargs"]["inter_case_delay"] == 3.5
    assert captured["kwargs"]["use_semantic_sketch_builder"] is True
