import os
from typing import Dict, Any, Optional
from groq import Groq
from openai import OpenAI
from llm.templates.renderer import render_prompt


def call_openai(model: str, prompt: str) -> str:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
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


def llm_handler(
    prompt_name: str,
    model: str = "llama-3.3-70b-versatile",
    input_data: Optional[Dict[str, Any]] = None,
) -> str:

    if not input_data:
        raise Exception("No input data given")

    prompt = render_prompt(prompt_name=prompt_name, context=input_data)
    
    if model == 'gpt-4o':
        return call_openai(model = model, prompt = prompt)
    else:
        return call_groq(model = model, prompt = prompt)
