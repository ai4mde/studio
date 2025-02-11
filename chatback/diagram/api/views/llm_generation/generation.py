from diagram.models import System, Diagram
from diagram.api.schemas import FullDiagram
from typing import Dict, Any
from openai import OpenAI
import os

def execute_prompt(prompt_path: str, prompt_data: Dict[str, Any] ) -> str:
    try:
        with open(prompt_path, 'r') as file:
            prompt = file.read()
        prompt = prompt.format(
            data=prompt_data
        )
    except Exception as e:
        raise Exception("Failed to format prompt, error: " + str(e))
    
    messages = [{"role": "user", "content": prompt}]
    reply = None

    try:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_KEY"),
        )

        chat = client.chat.completions.create(
            messages=messages,
            model="gpt-4o", # TODO: put in env
        )
        reply = chat.choices[0].message.content
    except Exception as e:
        raise Exception("Error while connecting to ChatGPT: " + str(e))
    
    return reply


def remove_reply_markdown(reply: str) -> str:
    lines = reply.splitlines()
    if len(lines) > 2:
        return '\n'.join(lines[1:-1])
    return ""   