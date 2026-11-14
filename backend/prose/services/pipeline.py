from ai.services.handler import llm_handler
from prose.models import Pipeline
from prose.services.parsing import parse_llm_response


def run_pipeline(
    pipeline: Pipeline,
    model: str = "llama-3.3-70b-versatile",
) -> Pipeline | None:
    response = llm_handler(
        "PROSE_GENERATE_METADATA",
        model,
        input_data={"requirements": pipeline.requirements},
    )

    if not response:
        return None

    pipeline.output = parse_llm_response(response)
    pipeline.step = 5
    pipeline.save()

    return pipeline
