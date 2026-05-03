import json
import os
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.models import MockModel

# Mocked DSL Response
MOCK_DSL = {
  "page": { "ui": { "layout": { "type": "shell", "regions": { "main": { "items": ["section-hero"] } } } } },
  "sections": {
    "section-hero": {
      "id": "section-hero",
      "class": "Product",
      "ui": {
        "layout": { "type": "split", "regions": { "start": { "span": 7, "items": ["gallery"] }, "end": { "span": 5, "items": ["summary", "actions"] } } },
        "components": [
          { "id": "gallery", "type": "MediaGallery", "bind": { "images": "images" } },
          { "id": "summary", "type": "ContentSummary", "bind": { "title": "title", "price": "price", "description": "description" } },
          { "id": "actions", "type": "ActionGroup", "actions": [ { "label": "Add to Cart", "role": "primary" }, { "label": "View Specs", "role": "secondary" } ] }
        ]
      }
    }
  },
  "data": { 
    "Product": { 
      "title": "Mountain Bike Pro", 
      "price": 1200, 
      "description": "A high-end bike for professionals.", 
      "images": ["https://via.placeholder.com/600", "https://via.placeholder.com/150"] 
    } 
  }
}

# Define a specialized agent for DSL generation with a MockModel
dsl_generator_agent = Agent(
    name="dsl_generator",
    model=MockModel(response=json.dumps(MOCK_DSL)),
    instruction="Generate a UI DSL JSON based on user requirements.",
)

def run_pipeline(prompt):
    print(f"Running pipeline for: {prompt}")
    
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="dsl_test")
    runner = Runner(agent=dsl_generator_agent, session_service=session_service, app_name="dsl_test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text=prompt)]
    )

    events = runner.run(
        new_message=message,
        user_id="test_user",
        session_id=session.id
    )

    full_response = ""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    full_response += part.text

    # Try to parse and pretty print the JSON
    try:
        # Remove markdown if the agent added it despite instructions
        clean_json = full_response.strip().replace("```json", "").replace("```", "")
        dsl_json = json.loads(clean_json)
        print("\n--- GENERATED DSL JSON ---")
        print(json.dumps(dsl_json, indent=2))
        return dsl_json
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print("Raw output:", full_response)
        return None

if __name__ == "__main__":
    # Test with a simple prompt
    run_pipeline("Create a product detail page for a high-end mountain bike.")
