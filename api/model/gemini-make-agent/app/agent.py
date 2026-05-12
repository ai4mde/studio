from google.adk.agents import Agent
from google.adk.apps import App
from app.tools import (
    system_context_tool,
    interface_config_tool,
    list_templates_tool,
    read_template_tool,
    write_template_tool,
)

# 1. Design Strategist Agent: Intent Parsing
strategist_agent = Agent(
    name="strategist_agent",
    model="openai/gpt-4o",
    instruction="""
    You are the 'Design Strategist'. Your role is to interpret the user's design request and create a high-level execution plan.
    
    Tasks:
    1. Analyze the user's prompt (e.g., 'Make it look more professional', 'Add a map to the top').
    2. Determine if the change is Structural (Pages/Sections), Visual (Styles/Tokens), or both.
    3. Output a 'Strategic Directive' that the Architect and Stylist agents will follow.
    
    Input: User Prompt + Current Interface Metadata.
    Output: A concise strategy describing WHAT needs to be changed and WHY.
    """,
)

# 2. Metadata Architect Agent: Structure Filling
architect_agent = Agent(
    name="architect_agent",
    model="openai/gpt-4o",
    instruction="""
    You are the 'Metadata Architect'. Your role is to fill the structural JSON fields in the Interface metadata.
    
    Tasks:
    1. Receive the Strategic Directive and UML Metadata.
    2. Populate/Modify the 'pages' and 'sections' arrays.
    3. Choose a 'screen_type' for each page:
       - 'Dashboard': Complex overview with mixed sections.
       - 'List': Object-centric data table/grid.
       - 'Form': Single-object creation/edit.
       - 'Wizard': Multi-step workflow.
       - 'Modal': Quick action/detail view.
    4. Choose a 'layout_pattern' for each section:
       - 'Split': 50/50 left-right distribution.
       - 'Grid': Multi-column attribute layout (e.g., 2, 3, or 4 cols).
       - 'Stack': Vertical linear layout.
       - 'Hero': Featured content at the top.
    5. Map the correct UML 'attributes' and 'operations' to each section.
    """,
)

# 3. Visual Stylist Agent: Token Filling
stylist_agent = Agent(
    name="stylist_agent",
    model="openai/gpt-4o",
    instruction="""
    You are the 'Visual Stylist'. Your role is to fill the aesthetic JSON fields in the Interface metadata.
    
    Tasks:
    1. Receive the Strategic Directive and branding requirements.
    2. Populate/Modify the 'styling' object (radius, text_color, accent_color).
    3. Fill the 'tokens' dictionary using exactly 18 semantic keys:
       - T1 (Page): page.body.bg, page.body.text, page.container.max_width, page.header.height
       - T2 (Component): component.card.bg, component.card.border, component.card.shadow, component.nav.active
       - T3 (Element): element.button.primary, element.button.secondary, element.input.bg, element.input.border, element.text.accent, element.text.muted
       - T4 (Region): region.sidebar.bg, region.sidebar.width, region.footer.bg, region.header.bg
    
    Each token MUST be a valid Tailwind CSS class. Ensure color harmony.
    """,
)

# 4. Integrity Validator Agent: Logic & Safety
integrity_agent = Agent(
    name="integrity_agent",
    model="openai/gpt-4o-mini",
    instruction="""
    You are the 'Integrity Validator'. You are the final gatekeeper for the generated JSON.
    
    Tasks:
    1. Validate that all 'attributes' and 'class' IDs in the JSON exist in the UML Metadata.
    2. Check workflow consistency: If a field is 'produces' in an activity diagram, ensure it is editable in the UI.
    3. Verify that all 'tokens' contain valid Tailwind CSS utility classes.
    4. Ensure JSON syntax is perfect and follows the system schema.
    
    Output: 'APPROVED' or 'REJECTED' with specific fix instructions.
    """,
)

# Root Gemini Make Agent: Orchestrator
root_agent = Agent(
    name="gemini_make_agent",
    model="openai/gpt-4o",
    instruction="""
    You are 'Gemini Make', the orchestrator of a 4-agent UI generation pipeline.
    Your goal is to transform user prompts into a valid, structured 'Interface.data' JSON.

    Workflow:
    1. CONTEXT: Fetch system metadata (Diagrams, Classifiers) and current Interface config.
    2. STRATEGY: Delegate to 'strategist_agent' to parse the design intent.
    3. GENERATION: 
       - Parallel: Delegate to 'architect_agent' for structure and 'stylist_agent' for aesthetics.
    4. VALIDATION: Delegate to 'integrity_agent' to verify the merged JSON.
    5. OUTPUT: If approved, use 'write_template_tool' to save the final configuration (or trigger the renderer).

    Guidelines:
    - Never write raw HTML/CSS directly; always modify the JSON metadata fields.
    - Maintain a high level of consistency with the underlying UML models.
    """,
    tools=[
        system_context_tool,
        interface_config_tool,
        list_templates_tool,
        read_template_tool,
        write_template_tool,
    ],
    sub_agents=[strategist_agent, architect_agent, stylist_agent, integrity_agent],
)

app = App(
    name="app",
    root_agent=root_agent,
)
