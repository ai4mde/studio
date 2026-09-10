from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from llm.handler import (
    FROZEN_CANDIDATE_SEEDS,
    FROZEN_SEMANTIC_DETERMINISTIC_MODEL,
    FROZEN_SEMANTIC_DETERMINISTIC_SETTINGS,
    call_openai,
    frozen_candidate_seed,
    frozen_semantic_deterministic_request_settings,
)
from llm.refinement_generator import generate_initial_candidates
from llm.semantic_sketch_experiment import generate_semantic_sketch_plan
from llm.topology_experiment import generate_topology_artifact


def test_frozen_openai_request_contains_explicit_model_settings_and_seed() -> None:
    completion = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
    )

    with patch("llm.handler.OpenAI") as openai_client:
        openai_client.return_value.chat.completions.create.return_value = completion
        with frozen_candidate_seed(2):
            call_openai(
                model=FROZEN_SEMANTIC_DETERMINISTIC_MODEL,
                prompt="test prompt",
                use_frozen_semantic_deterministic_settings=True,
            )
            call_openai(
                model=FROZEN_SEMANTIC_DETERMINISTIC_MODEL,
                prompt="correction prompt",
                use_frozen_semantic_deterministic_settings=True,
            )

    assert openai_client.call_count == 2
    assert all(
        call.kwargs == {"api_key": None, "max_retries": 2}
        for call in openai_client.call_args_list
    )
    requests = [call.kwargs for call in openai_client.return_value.chat.completions.create.call_args_list]
    assert [request["messages"][0]["content"] for request in requests] == [
        "test prompt",
        "correction prompt",
    ]
    assert all(
        {
            key: value
            for key, value in request.items()
            if key not in {"messages"}
        }
        == {
            "model": "gpt-4.1-2025-04-14",
            "temperature": 0.15,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "n": 1,
            "max_completion_tokens": 8192,
            "seed": 20260911,
        }
        for request in requests
    )


def test_both_planners_use_frozen_model_and_request_configuration() -> None:
    with patch("llm.topology_experiment.call_openai", return_value='{"structures": []}') as topology_call:
        generate_topology_artifact("A clerk archives a request.")

    topology_kwargs = topology_call.call_args.kwargs
    assert topology_kwargs["model"] == FROZEN_SEMANTIC_DETERMINISTIC_MODEL
    assert topology_kwargs["use_frozen_semantic_deterministic_settings"] is True

    semantic_payload = {
        "root_actions": [
            {
                "slot_id": "ROOT_START",
                "actions": [{"action": "clerk archives request"}],
            }
        ],
        "branch_plans": [],
    }
    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        return_value=json.dumps(semantic_payload),
    ) as semantic_call:
        generate_semantic_sketch_plan(
            "A clerk archives a request.",
            topology_artifact={"structures": []},
        )

    semantic_kwargs = semantic_call.call_args.kwargs
    assert semantic_kwargs["model"] == FROZEN_SEMANTIC_DETERMINISTIC_MODEL
    assert semantic_kwargs["use_frozen_semantic_deterministic_settings"] is True


def test_three_semantic_deterministic_candidates_use_established_seed_mapping() -> None:
    observed_seeds: list[int] = []

    def fake_model_activity(**_kwargs: object) -> dict:
        observed_seeds.append(frozen_semantic_deterministic_request_settings()["seed"])
        return {"nodes": [], "edges": []}

    with patch("llm.refinement_generator.model_activity", side_effect=fake_model_activity):
        generate_initial_candidates(
            "A simple process.",
            n=3,
            pipeline_profile="semantic_deterministic",
        )

    assert observed_seeds == [
        FROZEN_CANDIDATE_SEEDS[1],
        FROZEN_CANDIDATE_SEEDS[2],
        FROZEN_CANDIDATE_SEEDS[3],
    ]
    assert FROZEN_SEMANTIC_DETERMINISTIC_SETTINGS == {
        "temperature": 0.15,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "n": 1,
        "max_completion_tokens": 8192,
    }
