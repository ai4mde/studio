from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools import AgentTool
from app.tools import (
    interface_config_tool, update_interface_patch_tool, system_context_tool,
    run_seed_script_tool, get_available_paths_tool,
    get_interface_full_context_tool, validate_save_candidate_tool, render_candidate_preview_tool,
    get_design_system_tool, apply_design_system_to_interface_tool, list_design_specs_tool,
    select_design_specs_for_interface_tool,
)

_EDITABLE_FIELDS = """
Layout fields (sections/pages):
  sections[].layout        : "card" | "list" | "table" | "detail" | "gallery" | "filter" | "form" | "activity_action"
  sections[].col_span      : 12 | 6 | 4 | 3
  sections[].position      : "main" | "sidebar" | "header" | "footer"

Data & Query fields:
  sections[].attributes    : list of attribute names OR objects. Supports dot-notation for cross-class data (e.g. ["name", "seller.name"])
    Attribute object shape:
      {name: string, render: {as: "text" | "link" | "button" | "badge"}, action: {type: string}}
      Backward-compatible shortcut: {name: string, is_link: bool}
    Render modes:
      text   = normal field value
      link   = clickable field value for detail/navigation affordance
      button = field value styled as a button
      badge  = compact status/category pill
    Action types:
      none      = no interaction
      navigate  = go to a target page/detail affordance; may include targetPageId and params
      operation = trigger a custom operation; include class/operation/operationId and params when known
      copy      = copy the field value
      filter    = filter list content by this field/value
      expand    = expand long text
      tooltip   = show explanatory hover text; include tooltip
  sections[].query.limit   : number
  sections[].query.offset  : number
  sections[].query.order_by: list of field names (e.g. ["-created_at", "name"])
  sections[].query.filters : dict of field lookups (e.g. {"is_active": true, "price__gt": 100})

Card style (layout="card"):
  sections[].style.display_mode : "grid" | "carousel" | "banner"
  sections[].style.card_style   : "default" | "product" | "category" | "compact"
  sections[].style.columns      : "1" | "2" | "3" | "4"

List style (layout="list"):
  sections[].style.list_style   : "default" | "product" | "cart-item"

Form style (layout="form"):
  sections[].style.form_style   : "default" | "auth" | "step" | "summary"
  sections[].style.login_label  : any string (button label for auth)
  sections[].style.step_icon    : emoji or "" (icon for step header)
  sections[].style.total_label  : any string (label for total row in summary)
  sections[].style.cta_label    : any string (primary action button label; "" = hidden)

Workflow controls (layout/type="activity_action"):
  sections[].type             : "activity_action"
  sections[].label            : button/link label shown to the user
  sections[].workflow.action  : "complete" | "navigate" | "complete_then_page"
    complete           = complete the current ActiveProcessNode and auto-redirect to the next active workflow page
    navigate           = go to workflow.target_page without completing the workflow step
    complete_then_page = complete the workflow step and then redirect to workflow.target_page
  sections[].workflow.target_page : target page NAME (Title_Case) for navigate/complete_then_page
  sections[].style.variant    : "button" | "link" | "fab" | "wizard_next" | "auto"
  sections[].style.align      : "left" | "center" | "right"
  sections[].style.size       : "sm" | "md" | "lg"

Detail style (layout="detail"):
  sections[].style.image_position : "left" | "top" | "right"
  sections[].style.image_size     : "sm" | "md" | "lg"

Universal style controls:
  sections[].style.color         : "accent" | "accent-secondary" | "blue" | "green" | "purple" | "orange" | "rose" | "slate"
    IMPORTANT: Use "accent" (follows design spec primary color via CSS variable) instead of hardcoded color names.
    "accent" = design spec primary brand color; "accent-secondary" = second brand color.
    Hardcoded names (green/blue/etc.) ignore the design spec and lock the section to that Tailwind color.
  sections[].style.density       : "compact" | "normal" | "spacious"
  sections[].style.shadow        : "none" | "sm" | "md" | "lg"
  sections[].style.border        : "none" | "light" | "colored"
  sections[].style.bg            : "white" | "light" | "dark" | "transparent"
  sections[].style.header_style  : "default" | "large" | "hidden"

Static label controls (empty string = hidden):
  sections[].style.seller_label       : any string (e.g. "Sold by")
  sections[].style.availability_label : any string (e.g. "In stock")
  sections[].style.delivery_label     : any string (e.g. "Free delivery")

Page layout:
  pages[].layout.value : "vertical" | "vertical-reverse" | "horizontal" | "horizontal-reverse"
  pages[].gap.value    : "compact" | "normal" | "spacious"

Style/token fields (global theme):
  styling.radius          : 0 | 4 | 8 | 16 | 24  (border radius in px)
  styling.textColor       : "#hex"
  styling.accentColor     : "#hex"
  styling.backgroundColor : "#hex"
  styling.fontFamily      : "inter" | "roboto" | "poppins" | "playfair" | "mono" | "geist"
  styling.pageMaxWidth    : "sm" | "md" | "lg" | "xl" | "2xl" | "full"
  styling.buttonStyle     : "solid" | "outline" | "ghost" | "gradient"
  styling.cardHover       : "lift" | "glow" | "border" | "none"
  styling.imageRatio      : "1:1" | "4:3" | "16:9" | "portrait" | "wide"
  styling.divider         : "none" | "line" | "shadow" | "wave"
  styling.selectedStyle   : "modern" (leave unchanged)
  tokens (Tailwind CSS classes for fine-grained override):
    page.body.bg, page.body.text, page.header.text,
    region.header.bg, region.footer.bg,
    element.button.primary, element.button.secondary,
    component.card.bg, component.card.border, component.card.shadow,
    page.font.family, page.font.cdn, page.radius.px, page.container.class,
    theme.button.style, theme.card.hover, theme.image.ratio, theme.divider
"""

# ── Candidate Generation Pipeline ────────────────────────────────────────────

reason_agent = Agent(
    name="reason_agent",
    model="openai/gpt-4o",
    description="Analyses UML metadata and designer prompt to produce a structured reasoning JSON for interface generation.",
    instruction="""You analyse a system's UML metadata and a designer prompt to produce a structured reasoning JSON that will guide generation of 3 interface candidates.

Message format: interface_id=<uuid> prompt=<designer intent> selected_specs=[...]

Workflow:
1. Call get_interface_full_context(interface_id) to get the interface structure, classifiers, relations, activity_diagrams, and workflow_plan.
2. Reason about:
   - Visual Tone: How do the selected_specs align with the user prompt?
   - Completeness: Plan for a full app experience (Site Nav, Headers, Footers, Search, etc.).
   - Pages: Which pages the actor needs (one per major use-case or object workspace).
   - OOUI: workspace, navigation area, object detail, collection.
   - Transitions: All navigation transitions between pages.
   - 3 structurally distinct diversity directions for the candidates.
3. Output ONLY a JSON object with this exact shape (no markdown, no explanation):
{
  "visual_understanding": "<one paragraph explaining how the selected styles and components will fulfill the user's request>",
  "interface_id": "<uuid>",
  "actor_role": "<actor name>",
  "pages": [
    {"id": "<snake_case_id>", "name": "<Title_Case_name>", "primary_model": "<ModelName>", "intent": "<one sentence>"}
  ],
  "navigation_edges": [
    {"from": "<page_id>", "trigger": "<user action>", "to": "<page_id>", "passes": "<Model.id or null>"},
    {"from": "<page_id>", "trigger": "<user action>", "creates": "<ModelName>", "stays": true}
  ],
  "nav_bar_pages": ["<page_id>", ...],
  "icon_actions": ["<page_id or action>", ...],
  "actor_permissions": {"<ModelName>": ["view"|"create"|"update"|"delete"], ...},
  "diversity_hints": [
    "Direction 0: <describe specific column layout + dominant section type + density — e.g. 'compact table layout with sidebar filter, col_span=3 filter + col_span=12 table, 5 focused pages each serving one use-case'>",
    "Direction 1: <describe different layout — e.g. 'spacious card grid (col_span=6 splits on list pages, col_span=4 on dashboard), gallery for browsing, 3 combined pages'>",
    "Direction 2: <describe yet another layout — e.g. 'full-width gallery layout (col_span=12), detail-oriented with large detail views, 4 pages, prominent form sections'>"
  ]
}

Rules:
- page name must be Title_Case with underscores (e.g. Browse_Products)
- primary_model in pages[] MUST be the EXACT classifier name as it appears in the system context.
- nav_bar_pages MUST include the primary entry points.
- diversity_hints MUST be CONCRETE: specify column splits, dominant layout types, section counts, and density.
  Good example: "compact table layout with col_span=3 filter sidebar, 5 focused pages, 1 table section per page"
  Bad example: "data-rich layout"
- Output ONLY the JSON object.
""",
    tools=[get_interface_full_context_tool],
)


generate_agent = Agent(
    name="generate_agent",
    model="openai/gpt-4o",
    description="Generates 3 complete Interface DSL candidates from the reasoning JSON.",
    instruction=f"""You generate 3 complete Interface DSL candidates from the reasoning JSON.

COMPLETENESS & FIDELITY MANDATE: Every candidate MUST be a "ready-to-use" high-fidelity app.
1. REQUIRED CHROME (Every page):
   - 'main-header' or 'minimal-header' (position="header")
   - 'site-nav' or 'nav-links' (position="header", list all nav_bar_pages in 'methods')
   - 'site-footer' or 'brand-strip' (position="footer")

2. HIGH-FIDELITY STYLING:
   - Typography: Use `style.text_class` (e.g., "si-text-hero", "si-text-display", "si-text-lead") for prominent headers to trigger the deep typography tokens (letter-spacing, line-height) from the style guide.
   - Layout: Use `style.is_full_width: true` for sections that should span the entire screen (e.g., hero gallery).
   - Surfaces: Use `style.surface_level: "elevated"` for cards that should use the elevated background color from the spec.

DATA STRUCTURE — CRITICAL:
The function validate_and_save_candidate requires TWO separate arrays:
- pages[]: page objects that reference sections by ID only: {{id, name, sections: [{{value: "section_id"}}, ...]}}
- sections[]: the FULL section definitions — ALL sections for ALL pages in one flat list.
  Pages do NOT embed section data. They only list section IDs.

SECTION RULES:
- id: unique string
- layout: one of: {", ".join(sorted(["card","list","table","detail","gallery","filter","form",
                   "activity_action","promo-bar","logo","search-bar","icon-actions","nav-links",
                   "main-header","minimal-header","site-nav","site-footer","service-bar","link-grid","brand-strip"]))}
- style: use appropriate colors, density, and high-fidelity markers (text_class, is_full_width, surface_level).

For EACH candidate (index 0, 1, 2):
1. Build the flat sections[] list and pages[] references.
2. Call validate_and_save_candidate(interface_id, candidate_index, name, description, pages, sections).
   - Fix errors if any and retry.
   - Wait for "OK" before moving to next index.

After all 3 are saved, output: "All 3 candidates saved. Transferring to render_agent."
""",
    tools=[validate_save_candidate_tool, get_available_paths_tool],
)


render_agent = Agent(
    name="render_agent",
    model="openai/gpt-4o",
    description="Renders preview HTML for all 3 saved candidates.",
    instruction="""You render preview HTML for all 3 saved interface candidates.
For candidate_index 0, 1, 2:
  Call render_candidate_preview(interface_id, candidate_index).
After all renders are attempted, output: "Previews rendered. Pipeline complete."
""",
    tools=[render_candidate_preview_tool],
)


candidate_pipeline_agent = Agent(
    name="candidate_pipeline_agent",
    model="openai/gpt-4o",
    description="Runs the 3-candidate interface generation pipeline: reason → generate 3 candidates → render previews.",
    instruction=f"""You generate 3 interface design candidates by executing three phases in order.

Message format: interface_id=<uuid> prompt=<designer intent>

━━━ PHASE 1 — REASON ━━━
1. Call get_interface_full_context(interface_id) to load classifiers, attributes, activity diagrams.
   CRITICAL: From the response, extract and memorize the EXACT attribute names for each classifier.
   Example: if classifier "Loan Application" has attributes [{name:"loan_amount"},{name:"approved"},...]
   then the ONLY valid attributes for that model are exactly: "loan_amount", "approved", etc.
   Store this as a reference: model → [exact_field_name_1, exact_field_name_2, ...]
2. Call select_design_specs_for_interface(interface_id, count=3, prompt=<user prompt>).
3. Call reason_agent with message: "interface_id=<uuid> prompt=<prompt> selected_specs=<spec names list>"
   reason_agent returns a JSON with pages[], navigation_edges[], diversity_hints[].
   Save that JSON — you will use it in Phase 2.

━━━ PHASE 2 — GENERATE (YOU must call validate_and_save_candidate yourself, 3 times) ━━━

MANDATORY: For each candidate index 0, 1, 2 you MUST call validate_and_save_candidate directly.
Do NOT delegate this to any other agent. You must make the actual function call yourself.

DATA STRUCTURE — CRITICAL:
validate_and_save_candidate requires TWO separate top-level arrays:
  pages    — each item: {{id, name, sections: [{{value: "section_id"}}, ...]}}
             pages do NOT contain section data — only a list of section ID references
  sections — flat list of ALL section objects for ALL pages combined
             each item: {{id, name, layout, position, col_span, primary_model, attributes, operations, style}}

ALLOWED LAYOUTS: {", ".join(sorted(["card","list","table","detail","gallery","filter","form",
               "activity_action","promo-bar","logo","search-bar","icon-actions","nav-links",
               "main-header","minimal-header","site-nav","site-footer","service-bar","link-grid","brand-strip"]))}

CHROME SECTIONS (add to EVERY page's reference list, include once in sections[]):
  - site_nav: layout="site-nav", position="header", col_span=12, primary_model="", attributes=[]
  - icon_actions: layout="icon-actions", position="header", col_span=12, primary_model="", attributes=[]
  - site_footer: layout="site-footer", position="footer", col_span=12, primary_model="", attributes=[]

DATA SECTIONS (for layout in card/list/table/detail/gallery/form/filter):
  - MANDATORY: Every data section MUST have a non-empty attributes list.
    CRITICAL: Use ONLY attribute names that ACTUALLY EXIST in the classifier from get_interface_full_context.
    Read the classifier's attributes[] array CAREFULLY — copy the exact field names character for character.
    NEVER invent attribute names. If the classifier has "loan_amount" not "amount_requested", use "loan_amount".
    Use ALL relevant fields (4-8 names). NEVER leave attributes as [].
  - Set operations: {{"create": bool, "update": bool, "delete": bool}} based on actor permissions
  - style: {{"color": "accent|accent-secondary", "density": "compact|normal|spacious",
             "shadow": "none|sm|md", "bg": "white|light|dark|transparent"}}
    ALWAYS use "accent" for data section colors — this uses the design spec's brand color via CSS variables.

PAGE-DRIVEN LAYOUT SELECTION — MANDATORY:
Choose each section's layout based on what the PAGE IS, not which candidate index:
  Browse / listing page  (e.g. Browse_Products, Order_History, Applications_List)
    → "card" (with style.columns="3"), "gallery", or "table"
  Detail / view page     (e.g. Product_Detail, Loan_Detail, Profile)
    → "detail" for the primary section (shows image + fields)
  Input / create page    (e.g. Apply_Loan, Checkout, Fill_In_Application)
    → "form"
  Dashboard / overview   (e.g. Dashboard, Home, Overview)
    → mix of "card" sections with col_span=4 or col_span=6
  Filter / search page   (e.g. Search, Catalog with filters)
    → layout="filter" section with position="sidebar", col_span=3
      PLUS a main data section with col_span=12, position="main"

STRUCTURAL DIVERSITY — across the 3 candidates:
Each candidate follows a different visual direction from reason_agent's diversity_hints[].
  Candidate 0 → diversity_hints[0]
  Candidate 1 → diversity_hints[1]
  Candidate 2 → diversity_hints[2]

Make candidates structurally different using these axes:
  - Column organization: one candidate uses col_span=12 dominant, another uses col_span=6 splits
    (col_span=4+4+4 for dashboards), another uses filter sidebar (col_span=3)
  - Density and spacing: each candidate uses a different style.density ("compact"/"normal"/"spacious")
  - For the SAME page purpose, pick DIFFERENT layouts across candidates:
    e.g. browse page → candidate 0 uses "table", candidate 1 uses "card", candidate 2 uses "gallery"
  - Page count can differ: one candidate splits content into more focused pages, another combines

NEVER make all 3 candidates identical in page structure and section layout types.

PROCEDURE for each candidate index 0, 1, 2:
  a. Design all sections (chrome + data sections for every page).
  b. Build sections[] — the flat list of all section objects.
  c. Build pages[] — each page lists only {{value: section_id}} references (no section data).
  d. CALL validate_and_save_candidate(
       interface_id=<uuid>,
       candidate_index=<0|1|2>,
       name=<short name>,
       description=<one sentence>,
       pages=<pages list>,
       sections=<sections list>,
       prompt=<original user prompt from the message>
     )
  e. If the call returns an error, fix it and retry.
  f. Only move to the next candidate after this one is confirmed saved.

━━━ PHASE 3 — RENDER ━━━
After all 3 candidates are saved (after you received 3 success responses from validate_and_save_candidate),
call render_candidate_preview(interface_id, candidate_index) for each index 0, 1, 2.
""",
    tools=[
        get_interface_full_context_tool,
        validate_save_candidate_tool,
        render_candidate_preview_tool,
        get_available_paths_tool,
        list_design_specs_tool,
        get_design_system_tool,
        select_design_specs_for_interface_tool,
        AgentTool(agent=reason_agent),
    ],
)


seed_agent = Agent(
    name="seed_agent",
    model="openai/gpt-4o",
    description="Generates and runs realistic seed data for a running Django prototype based on its UML classifiers.",
    instruction="""You generate and run seed data for a running Django prototype.

Message format: system_id=<uuid> project_name=<name>

Workflow:
1. Call get_system_context with the system_id from the message to get all classifiers and attributes.
2. Build a self-contained Python seed script that:
   a. Starts with Django setup boilerplate (see below), filling in the actual system_id and project_name.
   b. Imports models from shared_models.models.
   c. For each model, checks the row count first — skip if count > 0 (delta seeding).
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
- NEVER truncate the script — include all model creation code.
- Use realistic domain-appropriate data (not "test1", "foo", "bar").
- String field values must match any enum constraints visible in classifier attributes.
""",
    tools=[system_context_tool, run_seed_script_tool],
)

root_agent = Agent(
    name="gemini_make_agent",
    model="openai/gpt-4o",
    description="Routes requests to the appropriate specialist agent.",
    instruction=f"""You are a routing agent for a UI design editor.

IMPORTANT: Before calling ANY tool, you MUST output a <understanding> block in Chinese.
Describe:
- Your understanding of the user's design request.
- Which visual style (.md spec) you plan to use and why.
- Which key components (e.g. site-nav, specific layouts) you will add to make the UI complete.

--- Routing Logic ---
If the message contains 'project_name=' (seed data request): transfer to seed_agent.
If the message contains 'generate_candidates' (3-candidate generation): call candidate_pipeline_agent with the message and wait.
Otherwise (interface_id= UI edit request): handle it directly.

--- UI edit workflow ---
Message format: interface_id=<uuid> user_request=<design change description>

1. Call get_interface_config(interface_id=<uuid>) to get the current data.
2. Check whether the interface already has design tokens (data.tokens is non-empty).
   - If data.tokens is EMPTY/NULL (first-time edit) OR the request involves a theme/style change:
     a. Call select_design_specs_for_interface(interface_id, count=3, prompt=...) using user_request as prompt.
     b. Select the best matching spec from the results.
     c. Call apply_design_system_to_interface_tool(interface_id, spec_name="...").
     d. If ONLY a theme/style change was requested and no layout changes are needed, STOP here.
3. Determine all needed layout/section changes. Persist them using apply_interface_patch.
   - ENSURE UI COMPLETENESS: If Header/Nav/Footer are missing, add them.
   - DESIGN TOKENS: When patching sections, include style.color="accent" for all data sections
     so they inherit the design spec brand color instead of using hardcoded Tailwind colors.

Editable fields:
{_EDITABLE_FIELDS}

Rules:
- NEVER modify: sections[].class, sections[].operations, sections[].name.
- Always keep "id" in every section/page entry in the patch.
- Call apply_interface_patch exactly once with the complete combined patch.
""",
    tools=[
        interface_config_tool, update_interface_patch_tool, system_context_tool, get_available_paths_tool,
        get_design_system_tool, apply_design_system_to_interface_tool, list_design_specs_tool,
        select_design_specs_for_interface_tool,
        AgentTool(agent=candidate_pipeline_agent),
    ],
    sub_agents=[seed_agent],
)

app = App(name="app", root_agent=root_agent)
candidate_app = App(name="candidate_app", root_agent=candidate_pipeline_agent)
