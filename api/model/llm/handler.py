import os
from typing import Any, Dict

from openai import OpenAI

from .prompts.diagram import DIAGRAM_GENERATE_ATTRIBUTE, DIAGRAM_GENERATE_METHOD
from .prompts.prose import PROSE_GENERATE_METADATA


def remove_reply_markdown(reply: str) -> str:
    lines = reply.splitlines()
    if len(lines) > 2:
        return "\n".join(lines[1:-1])
    return ""


def _resolve_openai_chat_model(model: str) -> str:
    """
    All chat completions use OpenAI. Legacy Groq-style ids (llama, mixtral, …)
    are mapped to a default OpenAI model.
    """
    m = (model or "").strip()
    if m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3"):
        return m
    return "gpt-4o-mini"


def call_openai(model: str, prompt: str) -> str:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    openai_model = _resolve_openai_chat_model(model)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=openai_model,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise Exception("Failed to call LLM, error " + str(e))


def llm_handler(
    prompt_name: str,
    model: str = "gpt-4o-mini",
    input_data: Dict[str, Any] | None = None,
) -> str:
    if not input_data:
        raise Exception("No input data given")

    if prompt_name == "DIAGRAM_GENERATE_ATTRIBUTE":
        prompt = DIAGRAM_GENERATE_ATTRIBUTE.format(data=input_data)
    elif prompt_name == "DIAGRAM_GENERATE_METHOD":
        prompt = DIAGRAM_GENERATE_METHOD.format(data=input_data)
    elif prompt_name == "PROSE_GENERATE_METADATA":
        prompt = PROSE_GENERATE_METADATA.format(data=input_data)
    else:
        raise Exception("Invalid prompt name")

    return call_openai(model=model, prompt=prompt)
