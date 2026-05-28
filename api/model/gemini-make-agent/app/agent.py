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
    analyze_interface_from_uml_tool, save_interface_plan_tool,
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

_EDITABLE_FIELDS = """
Layout fields (sections/pages):
  sections[].layout        : "card" | "list" | "table" | "detail" | "gallery" | "filter" | "form" | "activity_action" | "activity_start" | "activity_tasks" | supported header/footer template layouts
  sections[].component     : UI Kit component name, e.g. ProductCardGrid, DataTable, DetailPanel, ObjectForm, HeaderTemplate, FooterTemplate, SearchBar, IconActions, NavBar, FooterLinkGrid
  sections[].role          : semantic role, e.g. object_collection, object_detail, object_summary, child_collection, object_form, search_control, navigation, chrome_action, workflow_entry
  sections[].col_span      : 12 | 6 | 4 | 3
  sections[].position      : "main" | "sidebar" | "header" | "footer"
  sections[].style.sidebar_side : "left" | "right" when position="sidebar"; use left for navigation/filter rails and right for summaries/actions.

Data & Query fields:
  sections[].attributes    : list of attribute names OR objects. Supports dot-notation for cross-class data (e.g. ["name", "seller.name"])
    Attribute objects may mark read-only values: {name: "Seller.name", readonly: true, source: "related"}.
    Attributes are DISPLAY fields only. Do not use them as the query/SQL select list.
    Every attribute MUST be a real primary-model field or a valid related-class dot-notation field. Static image URLs from search/MCP are not attributes and must never be placed here.
  sections[].field_layout  : for data/form components only. Use only slots consumed by that component; do not invent slots.
    Card/Gallery: image, video, media, title, subtitle, primary, secondary, hidden.
    Table/List: columns, hidden.
    Detail: image, video, media, title, hero, fields, hidden.
    Form/Filter: fields, hidden.
    Media slots: use image for the primary image field, video for the primary video URL/file field, or media for whichever field should occupy the main media area. If a card section has multiple image/video fields, include all of them in attributes; field_layout.image only marks the cover image and must not hide the other media fields unless the user explicitly asked to hide them.
    Per-field layout overrides live in field_layout.field_styles:
      {"field_name": {"order": 0, "col_span": 12, "height": "sm"|"md"|"lg"|"xl", "text_size": "xs"|"sm"|"md"|"lg"|"xl", "align": "left"|"center"|"right", "label": "show"|"hidden"}}
  sections[].behavior      : for control/chrome components, e.g. SearchBar/NavBar/IconActions workflow/search config with target_page, target_model, fields, param.
    For collection components (card/list/table/gallery), use behavior.item_click for whole-item interactions:
      {item_click: {type: "navigate", target_page: "Product_Detail", params: {"product_id": "$Product.product_id"}}}
    Attribute object shape:
      {name: string, type?: "str" | "int" | "bool" | "enum" | "image" | "video", render: {as: "text" | "link" | "button" | "badge"}, action: {type: string}}
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
  sections[].data_source.mode       : "query"
  sections[].data_source.from.model : primary source model name
  sections[].data_source.joins      : optional list of {type: "left"|"inner"|"right", model: "ModelName", on: "ModelA.field_id = ModelB.id"}
    data_source defines where rows come from. It is separate from display attributes.
    Do not emit data_source for ordinary sections unless joins or a non-default source are needed.
  sections[].query.select  : optional list of query/SQL select columns, separate from attributes. Use exact primary fields or valid related dot notation (e.g. ["id", "name", "Seller.name"]).
  sections[].query.limit   : number
  sections[].query.offset  : number
  sections[].query.order_by: list of {field: string, direction: "asc"|"desc"}
  sections[].query.filters : list of {field: string, operator: "eq"|"neq"|"lt"|"lte"|"gt"|"gte"|"contains"|"in"|"isnull", value: string}
    Do not emit query for ordinary sections unless the user asked for filtering/sorting/limits, or the page semantics require it. query is for data retrieval constraints, not display fields.
  sections[].operations    : CRUD flags or list. create/update/delete control row/form actions. select is not read/view; use select only for choose/pick workflows or multi-select/bulk actions such as delete selected.

Card style (layout="card"):
  sections[].style.display_mode : "grid" | "carousel" | "banner"
  sections[].style.card_style   : "default" | "product" | "category" | "compact"
  sections[].style.columns      : "1" | "2" | "3" | "4"
  sections[].style.banner_height: "sm" | "md" | "lg" | "xl" for ImageCard/banner sections.
  sections[].style.image_ratio  : "wide" | "16:9" | "4:3" | "1:1" for image card media cropping.
  Header/footer templates: by default, create header/footer region sections using existing template layouts, not custom image/card compositions.
    Header layouts: "promo-bar" | "logo" | "search-bar" | "icon-actions" | "nav-links" | "site-nav" | "main-header" | "minimal-header" | "commerce-header" | "dashboard-header" | "split-header" | "app-header" | "compact-header" | "mega-header" | "hero-header" | "tabbed-header" | "glass-header" | "command-header".
    Footer layouts: "service-bar" | "link-grid" | "brand-strip" | "site-footer" | "compact-footer" | "legal-footer" | "newsletter-footer" | "social-footer" | "mega-footer" | "split-footer" | "app-footer" | "cta-footer" | "minimal-footer".
    Use component="HeaderTemplate" for combined header templates and component="FooterTemplate" for combined footer templates.
  Static online image URLs from MCP/search may be used only when the user explicitly asks for online images/photos/banner imagery. Put URLs in style.image_url or style.logo_url, never in attributes.

Logo image style (layout="logo"):
  sections[].style.logo_url     : image URL for the logo/brand mark. Use MCP-found image URL here when creating an image-based logo.
  sections[].style.logo_size    : "sm" | "md" | "lg" | "xl". Use sm/md in dense top bars, lg/xl in spacious/showcase headers.
  sections[].style.logo_shape   : "rounded" | "circle" | "square".

List style (layout="list"):
  sections[].style.list_style   : "default" | "product" | "cart-item" | "related"

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

Workflow launch/task panels:
  sections[].layout/type      : "activity_start" | "activity_tasks"
    activity_start = start an available workflow process from a normal usecase page (e.g. Checkout on Cart/Purchase page)
    activity_tasks = show active executable tasks. Activity pages themselves must not be put in normal site navigation.

Detail style (layout="detail"):
  sections[].style.image_position : "left" | "top" | "right"
  sections[].style.image_size     : "sm" | "md" | "lg"

Universal style controls:
  sections[].style.color         : "accent" | "accent-secondary" | "blue" | "green" | "purple" | "orange" | "rose" | "slate"
    IMPORTANT: Use "accent" (follows design spec primary color via CSS variable) instead of hardcoded color names.
    "accent" = design spec primary brand color; "accent-secondary" = second brand color.
    Hardcoded names (green/blue/etc.) ignore the design spec and lock the section to that Tailwind color.
  sections[].style.density       : "compact" | "normal" | "spacious"
  sections[].style.nav_height    : navigation/header nav only, "compact" | "normal" | "tall" | "xl"
  sections[].style.sidebar_width : sidebar only, integer 2..6 meaning the sidebar region width in twelfths of the content row
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
  pages[].layout.main_width   : "contained" | "wide" | "full"
  pages[].layout.header_width : "contained" | "full"
  pages[].layout.hero_width   : "contained" | "full"
  pages[].layout.footer_width : "contained" | "full" (usually "full" for normal site footers)
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

candidate_direct_agent = Agent(
    name="candidate_direct_agent",
    model=_model(),
    description="Reliably generates and saves 3 interface candidates through one deterministic tool call.",
    instruction="""You generate interface candidates by calling exactly one tool.

Message format: interface_id=<uuid> prompt=<designer intent>

Rules:
- Immediately call generate_candidate_set(interface_id, prompt).
- The tool must produce 3 structurally different previews: vary header/nav/footer, main width, and section placement across main, hero, left sidebar, and right sidebar when the user does not force one layout.
- Every normal page must have navigation, either inside the header or as a sidebar rail.
- Only call image_search_images first if the user explicitly asks for online images/photos/logo/banner URLs. Static online images from MCP must be used as style.image_url or style.logo_url, never as attributes/fields.
- Color/style-only prompts such as "generate pink pages" are valid designer requirements.
- Do not refuse style-only prompts.
- After the tool returns OK, output the tool result. If it returns ERROR, output the error.
""",
    tools=[generate_candidate_set_tool, _image_search_mcp_toolset()],
)

candidate_regeneration_agent = Agent(
    name="candidate_regeneration_agent",
    model=_model(),
    description="Reliably regenerates 3 candidates from a selected candidate through one deterministic tool call.",
    instruction="""You regenerate interface candidates by calling exactly one tool.

Message format:
  interface_id=<uuid> regenerate_candidates selected_candidate_index=<0|1|2> designer_requirements=<human requirements>

Rules:
- Immediately call regenerate_candidate_set(interface_id, selected_candidate_index, designer_requirements).
- Preserve the selected candidate's page layout and section region placement unless designer_requirements explicitly asks to change layout, header, footer, nav, sidebar, hero, or component arrangement.
- Only call image_search_images first if the requirements explicitly ask for online images/photos/logo/banner URLs. Static online images from MCP must be used as style.image_url or style.logo_url, never as attributes/fields.
- Do not create candidates yourself. The tool preserves page semantics, workflow/page types, data bindings, and activity flow order.
- After the tool returns OK, output the tool result. If it returns ERROR, output the error.
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

interface_mapper_agent = Agent(
    name="interface_mapper_agent",
    model=_model(),
    description="Maps a system's UML (class, use-case, activity diagrams) to interface pages and sections.",
    instruction="""You map UML diagrams to a concrete interface structure for a specific actor.

WORKFLOW
========
1. Call analyze_interface_from_uml(interface_id) to extract full UML intelligence.
   The result includes:
   - actor_permissions: which models this actor can access and with what CRUD rights
   - model_graph_summary: attributes, layout scores, relationships for each model
   - workflows: sequences from activity diagrams with suggested components per step
   - interface_plan.pages and interface_plan.sections: rule-based initial mapping
   - semantic_decisions: list of layout/component choices that need your judgment

2. Review the rule-based interface_plan. Then resolve each entry in semantic_decisions:
   Apply your knowledge of UX patterns and the domain (inferred from model names/attributes):

   CalendarView → use when model is appointment/booking/meeting/event AND has time-range fields
   TimelineList → use when model is history/log/audit/feed/transaction and data is chronological
   MapView      → use when model has geo coordinates (latitude, longitude)
   PersonCardGrid → use for user/customer/patient/doctor/member/employee collections
   DataTable    → default for most business entities with status and many attributes
   CardGrid     → use for visual/product-like entities without a more specific component
   DetailPanel  → standard detail view; ProductDetailPanel only for "Product" specifically
   StepperWorkflow → multi-step activity workflows (3+ steps from activity diagram)

   Activity step components:
   - ObjectForm only when the actor must enter, create, submit, or edit data.
   - DetailPanel for consult, review, monitor, analyze, verify, approve/reject, discharge, or confirm existing data.
   - SummaryPanel when the step summarizes status, outcome, risk, or decision.
   - ObjectList when the step requires selecting or comparing records.

3. Apply your semantic decisions to refine the interface_plan:
   - Replace or keep components in sections where you chose differently from the rule-based default
   - Add/remove sections if the UML intelligence justifies it (e.g., a workflow with 5 steps
     from the activity diagram that the rule-based planner missed)
   - Ensure every model in actor_permissions has at least one page
   - Ensure detail pages exist for models where update/create permission is granted

4. Call save_interface_plan(
       interface_id=<id>,
       pages_json=<JSON string of final pages array>,
       sections_json=<JSON string of final sections array>
   ) to persist the result.

5. Reply with a short summary: how many pages and sections were created, and any notable
   semantic decisions you made (e.g. "Used CalendarView for Appointment because it has
   start_time/end_time fields").

RULES
=====
- Only use models present in actor_permissions — do not invent pages for inaccessible models.
- Do not generate candidates. Do not touch design tokens or styling.
- Keep section IDs stable (use the ids from interface_plan — do not invent new ones unless adding a section).
- Every data-bound section (card/list/table/detail/gallery/filter/form/calendar/timeline/map, or any section with attributes)
  must preserve primary_model and class. Only chrome/control sections such as header, footer, nav, activity_start,
  activity_tasks, and activity_action may use empty primary_model/class.
- The pages_json and sections_json you pass to save_interface_plan must be valid JSON strings.
""",
    tools=[analyze_interface_from_uml_tool, save_interface_plan_tool],
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
If the message contains 'map_uml_to_interface' (UML-to-interface mapping): call interface_mapper_agent with the message and wait.
Otherwise (interface_id= UI edit request): handle it directly using the workflow below.

--- UI edit workflow ---
Message format: system_id=<uuid> interface_id=<uuid> user_request=<design change>
               [optional] SYSTEM_CONTEXT=<compact JSON: {{classifiers:[{{name,attributes:[]}}], current_interface:{{...}}}}>

━━━ STEP 1 — ANALYZE (MANDATORY: output an <analyze> block BEFORE calling any tool) ━━━
Parse SYSTEM_CONTEXT from the message if it is present. Extract:
  - classifier_fields: a mapping of ModelName → [exact_field_name, ...] for every classifier
  - The current pages and sections from current_interface
If SYSTEM_CONTEXT is absent from the message, call get_interface_full_context(interface_id) to obtain this data.

Write an <analyze> block containing:
  - Each classifier with its EXACT attribute list (copied verbatim — do NOT paraphrase or shorten)
  - A summary of the current page/section structure (page names, section ids, layouts)
  - What the user wants to change and which sections/pages are affected

━━━ STEP 2 — PLAN (MANDATORY: output a <plan> block BEFORE calling any patch tool) ━━━
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
               Non-data/static/control/chrome sections such as static ImageCard, Text, Logo, SearchBar, IconActions, HeaderTemplate,
               FooterTemplate, NavBar, and static URL/media cards should use primary_model="", class="", attributes=[], and field_layout={{}}.
IMAGE URL RULE: If the user wants an online/static image or asks to display pictures/photos, call image_search_images if no URL was provided, then put the chosen URL only in sections[].style.image_url on a card/ImageCard section.
                For five picture cards, create five separate layout="card", component="ImageCard", position="main" sections, each with its own style.image_url/image_alt.
                Do not add static image URLs to attributes, read-only attributes, field_layout, or any classifier.

━━━ STEP 3 — EXECUTE ━━━
1. Call get_interface_config(interface_id) to verify current section IDs and token state.
2. Check design tokens (data.tokens):
   - If tokens are EMPTY/NULL (first-time edit) OR user requested a theme/style change:
     a. If the user names a color such as purple, violet, blue, green, orange, rose, pink, red, dark, black, or slate,
        that color request is mandatory and must be reflected in tokens/accent/nav/button colors.
     b. If ONLY a style/theme change was requested and no layout changes are needed, STOP here.
3. Call apply_interface_patch exactly once with the complete patch derived from <plan>.
   - Attribute names: use ONLY names from classifier_fields verified in STEP 1.
   - style.color must be "accent" for all data sections (inherits brand color from spec).
   - ENSURE UI COMPLETENESS only for broad/full-page generation requests. For surgical edits/additive content requests, do not add Header/Nav/Footer.
   - To layout in the editor, patch sections[].position, sections[].layout, sections[].col_span, sections[].min_height,
     and pages[].sections order. Header/footer/sidebar are normal editable regions.
   - New sections/pages are allowed; include complete section/page objects and attach new sections through pages[].sections.
   - Always include "id" in every section/page entry.
   - NEVER modify existing sections[].class, sections[].operations, sections[].name.

Editable fields:
{_EDITABLE_FIELDS}
""",
    tools=[
        interface_config_tool, update_interface_patch_tool, system_context_tool, get_available_paths_tool,
        get_interface_full_context_tool,
        _image_search_mcp_toolset(),
        AgentTool(agent=candidate_regeneration_agent),
        AgentTool(agent=candidate_direct_agent),
        AgentTool(agent=interface_mapper_agent),
    ],
    sub_agents=[seed_agent],
)

app = App(name="app", root_agent=root_agent)
candidate_app = App(name="candidate_app", root_agent=candidate_direct_agent)
candidate_regeneration_app = App(name="candidate_regeneration_app", root_agent=candidate_regeneration_agent)
