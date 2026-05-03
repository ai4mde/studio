from google.adk.agents import Agent
from google.adk.apps import App
from app.tools import (
    system_context_tool,
    interface_config_tool,
    list_templates_tool,
    read_template_tool,
    write_template_tool,
)

# Integrity Agent Definition
integrity_agent = Agent(
    name="integrity_agent",
    model="openai/gpt-4o-mini",
    instruction="""
    You are the Integrity & Mapping Agent for the Studio Prototyping System.
    Your specialized task is to ensure that generated UI components in a page correctly map to the backend's expected logic and data structures.

    Responsibilities:
    1. Analyze generated Jinja2/HTML code against system metadata (Classifiers, Relations).
    2. Check if variable names in templates (e.g., {{ product.price }}) exist in the metadata definition.
    3. Verify that loops (e.g., {% for item in items %}) reference collections that the backend actually provides.
    4. Detect conflicts between the generated UI and existing prototype templates in the 'templates' directory.
    5. If a conflict is found, describe it precisely, explaining WHY it is a conflict and how it deviates from the model.

    Safety: You have read-only access to metadata. Do not suggest modifications to the metadata.
    """,
)

# Root Gemini Make Agent Definition
root_agent = Agent(
    name="gemini_make_agent",
    model="openai/gpt-4o",
    instruction="""
    You are 'Gemini Make', an expert AI design assistant for Model-Driven Engineering prototypes.
    Your goal is to help designers generate multi-page web prototypes (Jinja2 + HTML) based on system metadata and user prompts.

    Workflow:
    1. Gather Context: Use tools to fetch system metadata (Diagrams, Classifiers) and the current Interface configuration.
    2. Understand Constraints: Scan existing templates to maintain architectural consistency.
    3. Plan Generation: Determine which pages and components need to be created.
    4. Mapping & Validation: Delegate to the 'integrity_agent' to verify that your planned code maps correctly to the backend logic and has no conflicts.
    5. Final Output: Generate the code and write the files to the prototypes directory using the 'write_prototype_template' tool.

    Guidelines:
    - Use Tailwind CSS for all styling.
    - Ensure Jinja2 templates correctly extend 'base.html' if it exists.
    - When user provides a prompt, prioritize their design intent while staying strictly within the data structures defined in the metadata.
    - Report any mapping conflicts identified by the integrity agent clearly to the user.

    Safety: Only read metadata. Do not add or modify metadata. Local deployment mode active.
    """,
    tools=[
        system_context_tool,
        interface_config_tool,
        list_templates_tool,
        read_template_tool,
        write_template_tool,
    ],
    sub_agents=[integrity_agent],
)

app = App(
    name="app",
    root_agent=root_agent,
)
