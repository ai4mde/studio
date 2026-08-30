import logging
import os
import json
import time
import traceback
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore[misc, assignment]

from openai import OpenAI
from .prompts.diagram import DIAGRAM_GENERATE_ATTRIBUTE, DIAGRAM_GENERATE_METHOD
from .prompts.prose import PROSE_GENERATE_METADATA

# Responsibility:
# - perform provider-specific LLM calls
# - hold structured output schemas used at call time
# - keep transport concerns separate from ActivityGraph orchestration
#
# Must NOT:
# - own canonical architecture terminology
# - own the source of truth for ActivityGraph or TopologyPlan contracts
# - perform ActivityGraph normalization or AI4MDEExport conversion
#
# ARCHITECTURE NOTE:
# This module is architecturally ambiguous because it mixes provider transport,
# response-format schemas, prompt-name dispatch, and debug logging. The
# structured schemas here also duplicate contracts that are represented
# elsewhere as Pydantic models.
#
# Future stabilization may separate:
# - provider transport
# - structured output schema definitions
# - prompt dispatch helpers
# while preserving runtime behavior.

logger = logging.getLogger(__name__)

ACTIVITY_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": [
                            "initial",
                            "action",
                            "decision",
                            "merge",
                            "fork",
                            "join",
                            "final",
                            "object",
                        ],
                    },
                    "name": {"type": ["string", "null"]},
                    "label": {"type": ["string", "null"]},
                    "partition": {"type": ["string", "null"]},
                    "origin_step_id": {"type": ["string", "null"]},
                    "origin_block_id": {"type": ["string", "null"]},
                },
                "required": ["id", "type", "name", "label", "partition"],
                "additionalProperties": False,
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["control", "object"],
                        "default": "control",
                    },
                    "label": {"type": ["string", "null"]},
                    "condition": {"type": ["string", "null"]},
                },
                "required": ["source", "target", "type", "label", "condition"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["nodes", "edges"],
    "additionalProperties": False,
}

ACTIVITY_SKETCH_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "main_flow": {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "properties": {
                            "step_id": {"type": "string"},
                            "action": {"type": "string"},
                        },
                        "required": ["step_id", "action"],
                        "additionalProperties": False,
                    },
                ],
            },
        },
        "control_blocks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "block_id": {"type": ["string", "null"]},
                    "type": {
                        "type": "string",
                        "enum": ["decision", "loop", "parallel"],
                    },
                    "entry_after": {"type": ["string", "null"]},
                    "entry_after_step_id": {"type": ["string", "null"]},
                    "branches": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "returns_to_main_flow": {"type": "boolean"},
                                "steps": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "step_id": {"type": ["string", "null"]},
                                            "action": {"type": "string"},
                                        },
                                        "required": ["action"],
                                        "additionalProperties": False,
                                    },
                                },
                                "next_block_id": {"type": ["string", "null"]},
                                "child_block_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": [
                                "label",
                                "returns_to_main_flow",
                                "steps",
                                "next_block_id",
                                "child_block_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "requires_merge": {"type": "boolean"},
                    "exit_to": {"type": ["string", "null"]},
                    "exit_to_step_id": {"type": ["string", "null"]},
                    "loop_back_to": {"type": ["string", "null"]},
                    "loop_back_to_step_id": {"type": ["string", "null"]},
                    "loop_back_to_block_id": {"type": ["string", "null"]},
                    "notes": {"type": ["string", "null"]},
                },
                "required": [
                    "type",
                    "entry_after",
                    "entry_after_step_id",
                    "branches",
                    "requires_merge",
                    "exit_to",
                    "exit_to_step_id",
                    "loop_back_to",
                    "loop_back_to_step_id",
                    "loop_back_to_block_id",
                    "notes",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["main_flow", "control_blocks"],
    "additionalProperties": False,
}

def _debug_log(run_id: str, hypothesis_id: str, location: str, message: str, data: Dict[str, Any]) -> None:
    """
    Append one JSON log line when debugging is enabled.

    Logging is intentionally best-effort only:
    - disabled by default unless ``AI4MDE_DEBUG_LOG`` is set
    - creates parent directories when needed
    - never raises if file logging fails
    """
    log_target = os.environ.get("AI4MDE_DEBUG_LOG", "").strip()
    if not log_target:
        return

    payload = {
        "sessionId": os.environ.get("AI4MDE_DEBUG_SESSION", "local"),
        "id": f"log_{uuid.uuid4().hex}",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }

    try:
        log_path = Path(log_target)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except OSError:
        return


def remove_reply_markdown(reply: str) -> str:
    lines = reply.splitlines()
    if len(lines) > 2:
        return '\n'.join(lines[1:-1])
    return ""


def _is_activity_prompt(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    return (
        "uml activity diagram" in prompt_lower
        or "clean activity model" in prompt_lower
        or ('"nodes"' in prompt and '"edges"' in prompt)
    )


def _activity_response_format() -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "activity_model",
            "schema": ACTIVITY_SCHEMA,
            "strict": True,
        },
    }


def _activity_sketch_response_format() -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "activity_sketch",
            "schema": ACTIVITY_SKETCH_SCHEMA,
            "strict": True,
        },
    }


def _extract_message_content(chat_completion: Any) -> Optional[str]:
    if not getattr(chat_completion, "choices", None):
        return None
    message = chat_completion.choices[0].message
    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            elif hasattr(part, "type") and getattr(part, "type", None) == "text":
                text_parts.append(getattr(part, "text", ""))
        joined = "".join(text_parts).strip()
        return joined or None
    return None


def call_openai(
    model: str,
    prompt: str,
    *,
    response_format: Optional[Dict[str, Any]] = None,
    require_structured_output: bool = False,
) -> str:
    run_id = f"call_openai_{uuid.uuid4().hex[:8]}"
    # region agent log
    _debug_log(run_id, "H1", "handler.py:call_openai:entry", "Entered call_openai", {
        "model": model,
        "prompt_len": len(prompt),
    })
    # endregion
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    try:
        request_kwargs: Dict[str, Any] = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "model": model,
        }
        structured_response_format = response_format
        if structured_response_format is None and model in {"gpt-4o-mini", "gpt-4o"} and _is_activity_prompt(prompt):
            structured_response_format = _activity_response_format()

        if structured_response_format is not None:
            try:
                chat_completion = client.chat.completions.create(
                    **request_kwargs,
                    response_format=structured_response_format,
                )
                content = _extract_message_content(chat_completion)
                if not content:
                    raise ValueError(
                        "Structured output response did not include JSON content."
                    )
                _debug_log(run_id, "H1A", "handler.py:call_openai:structured", "Structured OpenAI response content observed", {
                    "content_is_none": content is None,
                    "content_type": str(type(content)),
                    "has_choices": len(chat_completion.choices) > 0,
                })
                return content
            except Exception as structured_error:
                if require_structured_output:
                    raise ValueError(
                        "Structured output request failed before a valid JSON response was returned."
                    ) from structured_error
                logger.warning(
                    "Structured output request failed; falling back to unconstrained generation.",
                    exc_info=True,
                )
                _debug_log(run_id, "H1B", "handler.py:call_openai:structured_fallback", "Structured OpenAI call failed, falling back to default chat completion", {
                    "error_type": type(structured_error).__name__,
                    "error_text": str(structured_error),
                    "traceback": traceback.format_exc(),
                })

        chat_completion = client.chat.completions.create(**request_kwargs)
        content = _extract_message_content(chat_completion)
        # region agent log
        _debug_log(run_id, "H1", "handler.py:call_openai:return", "OpenAI response content observed", {
            "content_is_none": content is None,
            "content_type": str(type(content)),
            "has_choices": len(chat_completion.choices) > 0,
        })
        # endregion
        return content
    except Exception as e:
        # region agent log
        _debug_log(run_id, "H2", "handler.py:call_openai:except", "Exception raised in call_openai", {
            "error_type": type(e).__name__,
            "error_text": str(e),
        })
        # endregion
        raise Exception("Failed to call LLM, error " + str(e))


def call_groq(model: str, prompt: str) -> str:
    run_id = f"call_groq_{uuid.uuid4().hex[:8]}"
    # region agent log
    _debug_log(run_id, "H3", "handler.py:call_groq:entry", "Entered call_groq", {
        "model": model,
        "prompt_len": len(prompt),
    })
    # endregion
    if Groq is None:
        raise ImportError(
            "The 'groq' package is not installed. Install it to use Groq models, "
            "or use model='gpt-4o' for OpenAI."
        )
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
        )
        content = chat_completion.choices[0].message.content
        # region agent log
        _debug_log(run_id, "H3", "handler.py:call_groq:return", "Groq response content observed", {
            "content_is_none": content is None,
            "content_type": str(type(content)),
            "has_choices": len(chat_completion.choices) > 0,
        })
        # endregion
        return content
    except Exception as e:
        # region agent log
        _debug_log(run_id, "H4", "handler.py:call_groq:except", "Exception raised in call_groq", {
            "error_type": type(e).__name__,
            "error_text": str(e),
        })
        # endregion
        raise Exception("Failed to call LLM, error " + str(e))


def llm_handler(prompt_name: str, model: str = "llama-3.3-70b-versatile", input_data: Dict[str, Any] = {}) -> str:

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

    if model == 'gpt-4o':
        return call_openai(model=model, prompt=prompt)
    else:
        if Groq is None:
            return call_openai(model="gpt-4o", prompt=prompt)
        return call_groq(model=model, prompt=prompt)
