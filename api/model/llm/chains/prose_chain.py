from __future__ import annotations

from typing import Callable

from llm.chains.base import ChainRunner, ChainStep
from llm.chains.schemas import (
    Step1EntitiesOutput,
    Step2RelationsOutput,
    Step3ValidationOutput,
)


PROSE_CHAIN_STEPS: list[ChainStep] = [
    ChainStep(
        name="extract_entities",
        prompt_name="PROSE_STEP1_EXTRACT_ENTITIES",
        output_schema=Step1EntitiesOutput,
        output_key="entities_result",
        description="Extract class entities and attributes from requirements.",
    ),
    ChainStep(
        name="infer_relations",
        prompt_name="PROSE_STEP2_INFER_RELATIONS",
        output_schema=Step2RelationsOutput,
        output_key="relations_result",
        description="Infer relations between extracted entities.",
    ),
    ChainStep(
        name="validate_model",
        prompt_name="PROSE_STEP3_VALIDATE",
        output_schema=Step3ValidationOutput,
        output_key="validation_result",
        description="Validate and correct the combined model.",
    ),
]


def create_prose_chain_runner(llm_caller: Callable[[str], str]) -> ChainRunner:
    return ChainRunner(steps=list(PROSE_CHAIN_STEPS), llm_caller=llm_caller)
