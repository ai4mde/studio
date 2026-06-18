import os
from typing import Dict, Any
from anthropic import Anthropic
from groq import Groq
from openai import OpenAI
from llm.prompts.diagram import DIAGRAM_GENERATE_ATTRIBUTE, DIAGRAM_GENERATE_METHOD
from llm.prompts.prose import PROSE_GENERATE_METADATA
from llm.prompts.generator import GEMINI_MAKE_PROTOTYPE

def remove_reply_markdown(reply: str) -> str:
    # Handle both ```json ... ``` and ``` ... ```
    """Strip Markdown fences from an LLM response payload."""
    reply = reply.strip()
    if reply.startswith("```"):
        lines = reply.splitlines()
        if len(lines) > 2:
            # Remove first and last line if they are backticks
            return '\n'.join(lines[1:-1])
    return reply


def call_openai(model: str, prompt: str, base_url: str = None) -> str:
    """Send a prompt to an OpenAI-compatible chat completion endpoint."""
    if base_url:
        api_key = os.environ.get("GEMINI_API_KEY")
        key_name = "GEMINI_API_KEY"
    else:
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
        key_name = "OPENAI_API_KEY / OPENAI_KEY"

    if not api_key:
        raise Exception(f"Missing API Key: {key_name} is not set in the environment.")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    try: 
        chat_completion = client.chat.completions.create(
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model = model,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Failed to call OpenAI/Gemini ({model}), error: {str(e)}")


def call_anthropic(model: str, prompt: str) -> str:
    """Send a prompt to Anthropic and return the generated text."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise Exception("Missing API Key: ANTHROPIC_API_KEY is not set in the environment.")
    client = Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        raise Exception(f"Failed to call Anthropic ({model}), error: {str(e)}")


def call_groq(model: str, prompt: str) -> str:
    """Send a prompt to Groq and return the generated text."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise Exception("Missing API Key: GROQ_API_KEY is not set in the environment.")

    client = Groq(
        api_key=api_key,
    )
    try: 
        chat_completion = client.chat.completions.create(
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ],
            model = model,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Failed to call Groq ({model}), error: {str(e)}")



def llm_handler(prompt_name: str, model: str = "llama-3.3-70b-versatile", input_data: Dict[str, Any] = {}) -> str:

    """Render a named prompt and dispatch it to the configured LLM provider."""
    if not input_data:
        raise Exception("No input data given")
    
    if prompt_name == "DIAGRAM_GENERATE_ATTRIBUTE":
        prompt = DIAGRAM_GENERATE_ATTRIBUTE.format(data=input_data)
    elif prompt_name == "DIAGRAM_GENERATE_METHOD":
        prompt = DIAGRAM_GENERATE_METHOD.format(data=input_data)
    elif prompt_name == "PROSE_GENERATE_METADATA":
        prompt = PROSE_GENERATE_METADATA.format(data=input_data)
    elif prompt_name == "GEMINI_MAKE_PROTOTYPE":
        prompt = GEMINI_MAKE_PROTOTYPE.format(**input_data)
    else:
        raise Exception("Invalid prompt name")
    
    if model.startswith('gpt'):
        return call_openai(model=model, prompt=prompt)
    elif model.startswith('gemini'):
        return call_openai(
            model=model,
            prompt=prompt,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    elif model.startswith('claude'):
        return call_anthropic(model=model, prompt=prompt)
    else:
        return call_groq(model=model, prompt=prompt)
