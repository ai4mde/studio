import os
from typing import Dict, Any
from groq import Groq
from openai import OpenAI
from llm.prompts.diagram import DIAGRAM_GENERATE_ATTRIBUTE, DIAGRAM_GENERATE_METHOD
from llm.prompts.prose import PROSE_GENERATE_METADATA
from llm.prompts.generator import GEMINI_MAKE_PROTOTYPE


def remove_reply_markdown(reply: str) -> str:
    # Handle both ```json ... ``` and ``` ... ```
    reply = reply.strip()
    if reply.startswith("```"):
        lines = reply.splitlines()
        if len(lines) > 2:
            # Remove first and last line if they are backticks
            return '\n'.join(lines[1:-1])
    return reply


def call_openai(model: str, prompt: str, base_url: str = None) -> str:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY") if not base_url else os.environ.get("GEMINI_API_KEY"),
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
        raise Exception("Failed to call LLM, error " + str(e))


def call_groq(model: str, prompt: str) -> str:
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
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
    elif prompt_name == "GEMINI_MAKE_PROTOTYPE":
        prompt = GEMINI_MAKE_PROTOTYPE.format(**input_data)
    else:
        raise Exception("Invalid prompt name")
    
    if model.startswith('gpt'):
        return call_openai(model = model, prompt = prompt)
    elif model.startswith('gemini'):
        return call_openai(
            model = model, 
            prompt = prompt, 
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    else:
        return call_groq(model = model, prompt = prompt)
