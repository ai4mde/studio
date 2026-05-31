import os
import sys

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import AgentTool
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters
from app.tools import (
    interface_config_tool, update_interface_patch_tool, system_context_tool,
    run_seed_script_tool, get_available_paths_tool,
    get_interface_full_context_tool,
    generate_candidate_set_tool, regenerate_candidate_set_tool,
    _DATA_SCHEMA,
    _LAYOUT_SCHEMA,
)

AGENT_MODEL = os.environ.get("ADK_AGENT_MODEL", "openai/gpt-4o")
if os.environ.get("ADK_DEBUG_MODEL", "").lower() in {"1", "true", "yes"}:
    print(f"ADK agent model: {AGENT_MODEL}", file=sys.stderr, flush=True)


def _model():
    if AGENT_MODEL.startswith("gemini/"):
        return AGENT_MODEL.removeprefix("gemini/")
    return LiteLlm(model=AGENT_MODEL) if "/" in AGENT_MODEL else AGENT_MODEL


def _image_search_mcp_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python",
                args=["-m", "app.image_search_mcp_server"],
            ),
            timeout=10,
        ),
        tool_filter=["search_images"],
        tool_name_prefix="image_",
    )


# Candidate Generation Pipeline
candidate_direct_agent = Agent(
    name="candidate_direct_agent",
    model=_model(),
    description="Reliably generates and saves 3 interface candidates through the required saving tool.",
    instruction="""You generate interface candidates by calling the required saving tool.

Message format: interface_id=<uuid> prompt=<designer intent>

Rules:
- Required: call generate_candidate_set(interface_id, prompt) exactly once in every run.
- Do not answer in natural language before calling generate_candidate_set.
- Never finish with only ListTools, image_search_images, or a text response.
- The tool must produce 3 structurally different previews: vary header/nav/footer, main width, and section placement across main, hero, left sidebar, and right sidebar when the user does not force one layout.
- Every normal page must have navigation, either inside the header or as a sidebar rail.
- You may call image_search_images before generate_candidate_set only if the user explicitly asks for online images/photos/logo/banner URLs. Static online images from MCP must be used as style.image_url or style.logo_url, never as attributes/fields.
- If you call image_search_images, you still must call generate_candidate_set after it.
- Color/style-only prompts such as "generate pink pages" are valid designer requirements.
- Do not refuse style-only prompts.
- After generate_candidate_set returns OK, output the tool result. If it returns ERROR, output the error.
""",
    tools=[generate_candidate_set_tool, _image_search_mcp_toolset()],
)

candidate_regeneration_agent = Agent(
    name="candidate_regeneration_agent",
    model=_model(),
    description="Reliably regenerates 3 candidates from a selected candidate through the required saving tool.",
    instruction="""You regenerate interface candidates by calling the required saving tool.

Message format:
  interface_id=<uuid> regenerate_candidates selected_candidate_index=<0|1|2> designer_requirements=<human requirements>

Rules:
- Required: call regenerate_candidate_set(interface_id, selected_candidate_index, designer_requirements) exactly once in every run.
- Do not answer in natural language before calling regenerate_candidate_set.
- Never finish with only ListTools, image_search_images, or a text response.
- Preserve the selected candidate's page layout and section region placement unless designer_requirements explicitly asks to change layout, header, footer, nav, sidebar, hero, or component arrangement.
- You may call image_search_images before regenerate_candidate_set only if the requirements explicitly ask for online images/photos/logo/banner URLs. Static online images from MCP must be used as style.image_url or style.logo_url, never as attributes/fields.
- If you call image_search_images, you still must call regenerate_candidate_set after it.
- Do not create candidates yourself. The tool preserves page semantics, workflow/page types, data bindings, and activity flow order.
- After regenerate_candidate_set returns OK, output the tool result. If it returns ERROR, output the error.
""",
    tools=[
        regenerate_candidate_set_tool,
        _image_search_mcp_toolset(),
    ],
)


seed_agent = Agent(
    name="seed_agent",
    model=_model(),
    description="Generates and runs realistic seed data for a running Django prototype based on its UML classifiers.",
    instruction="""You generate and run seed data for a running Django prototype.

Message format: system_id=<uuid> project_name=<name>

Workflow:
1. Call get_system_context with the system_id from the message to get all classifiers and attributes.
2. Build a self-contained Python seed script that:
   a. Starts with Django setup boilerplate (see below), filling in the actual system_id and project_name.
   b. Imports models from shared_models.models.
   c. For each model, checks the row count first â€” skip if count > 0 (delta seeding).
   d. Creates 3-6 realistic, related records per empty model.
   e. Respects FK relationships: create parent models before child models.
   f. Uses print() to report what was created.
3. Call run_seed_script with python_code set to the complete script.

Django setup boilerplate (replace SYSTEM_ID and PROJECT_NAME with the actual values):
  import sys, os
  proto_path = '/usr/src/prototypes/generated_prototypes/SYSTEM_ID/PROJECT_NAME'
  if proto_path not in sys.path:
      sys.path.insert(0, proto_path)
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROJECT_NAME.settings')
  import django; django.setup()
  from shared_models.models import *

Rules:
- Only call run_seed_script ONCE with the complete script.
- NEVER truncate the script â€” include all model creation code.
- Use realistic domain-appropriate data (not "test1", "foo", "bar").
- String field values must match any enum constraints visible in classifier attributes.
""",
    tools=[system_context_tool, run_seed_script_tool],
)


root_agent = Agent(
    name="gemini_make_agent",
    model=_model(),
    description="Routes requests to the appropriate specialist agent.",
    instruction=f"""You are a routing agent for a UI design editor.

--- Routing Logic ---
If the message contains 'project_name=' (seed data request): transfer to seed_agent.
If the message contains 'regenerate_candidates' (selected-candidate regeneration): call candidate_regeneration_agent with the message and wait.
If the message contains 'generate_candidates' (3-candidate generation): call candidate_direct_agent with the message and wait.
Otherwise (interface_id= UI edit request): handle it directly using the workflow below.

--- UI edit workflow ---
Message format: system_id=<uuid> interface_id=<uuid> user_request=<design change>
               [optional] SYSTEM_CONTEXT=<compact JSON: {{classifiers:[{{name,attributes:[]}}], current_interface:{{...}}}}>

â”â”â” STEP 1 â€” ANALYZE (MANDATORY: output an <analyze> block BEFORE calling any tool) â”â”â”
Parse SYSTEM_CONTEXT from the message if it is present. Extract:
  - classifier_fields: a mapping of ModelName â†’ [exact_field_name, ...] for every classifier
  - The current pages and sections from current_interface
If SYSTEM_CONTEXT is absent from the message, call get_interface_full_context(interface_id) to obtain this data.

Write an <analyze> block containing:
  - Each classifier with its EXACT attribute list (copied verbatim â€” do NOT paraphrase or shorten)
  - A summary of the current page/section structure (page names, section ids, layouts)
  - What the user wants to change and which sections/pages are affected

â”â”â” STEP 2 â€” PLAN (MANDATORY: output a <plan> block BEFORE calling any patch tool) â”â”â”
Based on your analysis, produce a concrete change plan:
  - ADD section: id, layout, component, col_span, position, primary_model, attributes
  - MODIFY section: id, which fields change and to what value
  - REMOVE section: id
  - Page changes: new pages, layout changes, or sections reference order changes
  - Design system: keep current tokens OR select new spec (if style change requested)

HUMAN-IN-THE-LOOP LAYOUT RULE:
  Treat current_interface.pages and current_interface.sections as the source of truth. Preserve human/editor changes
  unless the user explicitly asks to change them. Apply surgical patches only: section layout/position/col_span/min_height,
  style, text/methods, and page.sections ordering. Do not regenerate or overwrite the whole interface for a small edit.
  For additive requests like "add five more card section components", "add cards", "add picture cards", or "display pictures",
  add the requested supported section component type to the named/current page's main area unless the user names another region.
  Do not modify existing header, nav, sidebar, footer,
  page layout, tokens, design system, or existing section order except appending/inserting the new section ids.
  Supported section components include all layouts/components listed in Editable fields and already present in current_interface.sections.
  Use the requested component type literally when it is supported (card, list, table, detail, gallery, filter, form, activity sections,
  header/footer templates, logo/search/actions/nav, image cards, text/static sections, etc.).

ATTRIBUTE RULE: Every attribute name in ADD/MODIFY entries MUST appear in classifier_fields["ModelName"].
               NEVER invent attribute names. Copy them character-for-character from the <analyze> block.
               Data-bound sections must have primary_model/class and real attributes from that class or valid related dot-notation.
               If classifier_fields contains real image-like fields (type image, or names like image_url/photo_url/avatar_url/thumbnail_url/poster_url/cover_url/logo_url), use them in visual data-bound sections and set field_layout.image to the chosen real field.
               Non-data/static/control/chrome sections such as static ImageCard, Text, Logo, SearchBar, IconActions, HeaderTemplate,
               FooterTemplate, NavBar, and static URL/media cards should use primary_model="", class="", attributes=[], and field_layout={{}}.
IMAGE URL RULE: If the user wants an online/static image or asks to display pictures/photos, call image_search_images if no URL was provided, then put the chosen URL only in sections[].style.image_url on a card/ImageCard section.
                For five picture cards, create five separate layout="card", component="ImageCard", position="main" sections, each with its own style.image_url/image_alt.
                Do not add static image URLs to attributes, read-only attributes, field_layout, or any classifier. This does NOT apply to real model image fields: real image fields belong in attributes and field_layout.image.

                
â”â”â” STEP 3 â€” EXECUTE â”â”â”
1. Call get_interface_config(interface_id) to verify current section IDs and token state.
2. Check design tokens (data.tokens):
   - If tokens are EMPTY/NULL (first-time edit) OR user requested a theme/style change, let the model choose or update the design tokens needed for the requested style.
   - If ONLY a style/theme change was requested and no layout changes are needed, STOP here.
3. Call apply_interface_patch exactly once with the complete patch derived from <plan>.
   - Attribute names: use ONLY names from classifier_fields verified in STEP 1.
   - For data sections, keep style.color consistent with the chosen design tokens unless the user explicitly asks for section-level color differences.
   - ENSURE UI COMPLETENESS only for broad/full-page generation requests. For surgical edits/additive content requests, do not add Header/Nav/Footer.
   - To layout in the editor, patch sections[].position, sections[].layout, sections[].col_span, sections[].min_height,
     and pages[].sections order. Header/footer/sidebar are normal editable regions.
   - New sections/pages are allowed; include complete section/page objects and attach new sections through pages[].sections.
   - Always include "id" in every section/page entry.
   - NEVER modify existing sections[].class, sections[].operations, sections[].name.

Editable fields:
{_LAYOUT_SCHEMA}

{_DATA_SCHEMA}
""",
    tools=[
        interface_config_tool, update_interface_patch_tool, system_context_tool, get_available_paths_tool,
        get_interface_full_context_tool,
        _image_search_mcp_toolset(),
        AgentTool(agent=candidate_regeneration_agent),
        AgentTool(agent=candidate_direct_agent),
    ],
    sub_agents=[seed_agent],
)

app = App(name="app", root_agent=root_agent)
candidate_app = App(name="candidate_app", root_agent=candidate_direct_agent)
candidate_regeneration_app = App(name="candidate_regeneration_app", root_agent=candidate_regeneration_agent)
