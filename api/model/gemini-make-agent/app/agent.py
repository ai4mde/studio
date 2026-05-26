import os

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import AgentTool
from app.tools import (
    interface_config_tool, update_interface_patch_tool, system_context_tool,
    run_seed_script_tool, get_available_paths_tool,
    get_interface_full_context_tool, get_candidate_regeneration_context_tool,
    generate_candidate_set_tool, regenerate_candidate_set_tool,
    validate_save_candidate_tool, render_candidate_preview_tool,
    get_design_system_tool, apply_design_system_to_interface_tool, list_design_specs_tool,
    select_design_specs_for_interface_tool,
)

AGENT_MODEL = os.environ.get("ADK_AGENT_MODEL", "openai/gpt-4o")
print(f"ADK agent model: {AGENT_MODEL}", flush=True)


def _model():
    if AGENT_MODEL.startswith("gemini/"):
        return AGENT_MODEL.removeprefix("gemini/")
    return LiteLlm(model=AGENT_MODEL) if "/" in AGENT_MODEL else AGENT_MODEL

_EDITABLE_FIELDS = """
Layout fields (sections/pages):
  sections[].layout        : "card" | "list" | "table" | "detail" | "gallery" | "filter" | "form" | "activity_action" | "activity_start" | "activity_tasks"
  sections[].component     : UI Kit component name, e.g. ProductCardGrid, DataTable, DetailPanel, ObjectForm, SearchBar, IconActions, NavBar, FooterLinkGrid
  sections[].role          : semantic role, e.g. object_collection, object_detail, object_summary, child_collection, object_form, search_control, navigation, chrome_action, workflow_entry
  sections[].col_span      : 12 | 6 | 4 | 3
  sections[].position      : "main" | "sidebar" | "header" | "footer"
  sections[].style.sidebar_side : "left" | "right" when position="sidebar"; use left for navigation/filter rails and right for summaries/actions.

Data & Query fields:
  sections[].attributes    : list of attribute names OR objects. Supports dot-notation for cross-class data (e.g. ["name", "seller.name"])
    Attribute objects may mark read-only values: {name: "Seller.name", readonly: true, source: "related"}.
    Attributes are DISPLAY fields only. Do not use them as the query/SQL select list.
  sections[].field_layout  : for data/form components only. Use only slots consumed by that component; do not invent slots.
    Card/Gallery: image, video, media, title, subtitle, primary, secondary, hidden.
    Table/List: columns, hidden.
    Detail: image, video, media, title, hero, fields, hidden.
    Form/Filter: fields, hidden.
    Media slots: use image for image fields, video for video URL/file fields, or media for whichever field should occupy the main media area.
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

reason_agent = Agent(
    name="reason_agent",
    model=_model(),
    description="Analyses UML metadata and designer prompt to produce a structured reasoning JSON for interface generation.",
    instruction="""You analyse a system's UML metadata and a designer prompt to produce a structured reasoning JSON that will guide generation of 3 interface candidates.

Message format: interface_id=<uuid> prompt=<designer intent> selected_specs=[...]

Workflow:
1. Call get_interface_full_context(interface_id) to get the interface structure, classifiers, relations, usecase_navigation, activity_diagrams, and workflow_plan.
2. Reason about:
   - Visual Tone: How do the selected_specs align with the user prompt?
   - Completeness: Plan for a full app experience (Site Nav, Headers, Footers, Search, etc.).
   - Pages/sections: Start from system.usecase_navigation.ooui_plan. Its pages[] and sections[] are the canonical OOUI blueprint. Do not invent one page per use case.
   - Component model: layout controls page arrangement; component controls the UI Kit component; field_layout controls field slots inside data components; behavior controls search/nav/workflow/action components.
   - Pages: Pages are OOUI object workspaces; use cases become capabilities on those pages.
   - Navigation and buttons: Use system.usecase_navigation.nav_bar_pages for site navigation and icon_actions for compact header/cart/account/order buttons.
   - Permissions: Use system.usecase_navigation.actor_permissions to decide section operations. Do not expose create/update/delete controls that the use case permissions do not allow.
   - Workflow entry: Use system.usecase_navigation.workflow_entry_points to place activity_start sections on normal usecase pages such as Cart/Purchase. Label them with button_label (e.g. "Checkout"). This button is NOT the whole page: the page must first contain normal business data sections for the objects the user reviews/edits before starting the workflow.
   - Workflow: Use system.workflow_plan/activity_diagrams for executable task pages. Each activity page needs task-specific content first (form/list/detail/table for the object being reviewed or edited), then an activity_action control to complete/continue the task.
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
- nav_bar_pages MUST include the actor's usecase_navigation.nav_bar_pages primary entry points.
- actor_permissions MUST be copied or conservatively derived from usecase_navigation.actor_permissions.
- Workflow/activity pages MUST NOT be placed in nav_bar_pages. Normal usecase pages may contain activity_start buttons that launch them.
- Do NOT create standalone pages for inline operation use cases such as Add/Remove/Select/Write Review unless the OOUI mapping says they are workspaces. Put those as buttons/forms/actions on the relevant object page.
- diversity_hints MUST be CONCRETE: specify column splits, dominant layout types, section counts, and density.
  Good example: "compact table layout with col_span=3 filter sidebar, 5 focused pages, 1 table section per page"
  Bad example: "data-rich layout"
- Output ONLY the JSON object.
""",
    tools=[get_interface_full_context_tool],
)


generate_agent = Agent(
    name="generate_agent",
    model=_model(),
    description="Generates 3 complete Interface DSL candidates from the reasoning JSON.",
    instruction=f"""You generate 3 complete Interface DSL candidates from the reasoning JSON.

COMPLETENESS & FIDELITY MANDATE: Every candidate MUST be a "ready-to-use" high-fidelity app.
1. REQUIRED CHROME (Every page):
   - Header/nav/footer/sidebar are designable regions, not fixed boilerplate.
   - Header is a composable layout region like main: any section layout may use position="header" when it belongs above the page body, including tables, cards, summaries, forms, hero content, nav, logo, search, and actions.
   - Header ordering and col_span matter. Compose multi-row headers by ordering several header sections and using col_span values (for example logo col_span=3, search col_span=6, icon actions col_span=3, nav col_span=12).
   - Sidebar and footer are also composable layout regions like main: any suitable section layout may use position="sidebar" or position="footer", not only filter/nav/footer chrome. Use col_span and ordering to create side rails, utility panels, summary/footer cards, legal/footer nav, actions, and data snippets.
   - For sidebar region width, set style.sidebar_width to 2..6. Main content automatically uses remaining horizontal space.
   - Use varied chrome across candidates unless the user explicitly asks for one fixed pattern.
   - 'site-nav' or 'nav-links' may be position="header" OR position="sidebar" with style.sidebar_side="left" or "right".
   - Sidebar order matters: a sidebar nav can appear at the top, between filters/summaries/actions, or near the bottom by ordering that section differently in the page's sections list. Do not always place sidebar nav first.
   - 'site-footer', 'brand-strip', service bars, and link grids may vary in density and composition.

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
                   "activity_action","activity_start","activity_tasks","promo-bar","logo","search-bar","icon-actions","nav-links",
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
    model=_model(),
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
    model=_model(),
    description="Runs the 3-candidate interface generation pipeline: reason → generate 3 candidates → render previews.",
    instruction=f"""You generate 3 interface design candidates by executing three phases in order.

Message format: interface_id=<uuid> prompt=<designer intent>

IMPORTANT STYLE-PROMPT RULE:
- Color/style-only prompts such as "generate pink pages", "purple style page", "dark minimalist", or "make it blue"
  are valid designer requirements, not refusal cases.
- Interpret them as: preserve the current interface metadata, pages, workflow, data bindings, and interactions,
  then generate 3 functional candidates using that visual theme.
- Never refuse because a prompt only names a color or visual style. The app must remain functional and data-driven.
- If a prompt names a color, that color must be visibly reflected in tokens, nav/header accents, buttons, and key UI states.

━━━ PHASE 1 — REASON ━━━
1. Call get_interface_full_context(interface_id) to load classifiers, attributes, usecase_navigation, activity diagrams.
   CRITICAL: From the response, extract and memorize the EXACT attribute names for each classifier.
   Example: if classifier "Loan Application" has attributes [{{name:"loan_amount"}},{{name:"approved"}},...]
   then the ONLY valid attributes for that model are exactly: "loan_amount", "approved", etc.
   Store this as a reference: model → [exact_field_name_1, exact_field_name_2, ...]
   Also extract system.usecase_navigation.ooui_plan: pages[] are object workspaces, sections[] are the intended section blueprint, operations[] are inline object actions, workflows[] are activity workflow entries.
   Use system.usecase_navigation.nav_bar_pages for navigation, workflow_entry_points for activity_start buttons, and actor_permissions for data operations.
2. Call select_design_specs_for_interface(interface_id, count=3, prompt=<user prompt>).
3. Use the compact context plus selected specs directly. Do not call a separate reasoning agent.
   Save that JSON — you will use it in Phase 2.

━━━ PHASE 2 — GENERATE (YOU must call validate_and_save_candidate yourself, 3 times) ━━━

MANDATORY: For each candidate index 0, 1, 2 you MUST call validate_and_save_candidate directly.
Do NOT delegate this to any other agent. You must make the actual function call yourself.

DATA STRUCTURE — CRITICAL:
validate_and_save_candidate requires TWO separate top-level arrays:
  pages may include layout/gap settings; each page's sections field still contains only section ID references.
  pages    — each item: {{id, name, sections: [{{value: "section_id"}}, ...]}}
             pages do NOT contain section data — only a list of section ID references
  sections — flat list of ALL section objects for ALL pages combined
             each item: {{id, name, role, layout, component, position, col_span, primary_model, attributes, field_layout, behavior, operations, style}}

OOUI BLUEPRINT:
  - Prefer section IDs/roles from system.usecase_navigation.ooui_plan.sections when building sections[].
  - Each data section has exactly one primary_model. Only fields from primary_model may be editable.
  - related_visible_fields such as Product.name may be displayed using dot notation but are read-only in that section.
  - Inline operations from ooui_plan.operations become buttons/custom operations on the source page/section, not standalone pages.

ALLOWED LAYOUTS: {", ".join(sorted(["card","list","table","detail","gallery","filter","form",
               "activity_action","activity_start","activity_tasks","promo-bar","logo","search-bar","icon-actions","nav-links",
               "main-header","minimal-header","site-nav","site-footer","service-bar","link-grid","brand-strip"]))}

CHROME SECTIONS (add to EVERY page's reference list, include once in sections[]):
  - Navigation can be horizontal header nav OR a left sidebar rail.
    For sidebar navigation use role="navigation", layout="site-nav" or "nav-links", component="NavBar", position="sidebar", col_span=12, style.sidebar_side="left".
  - Header can be main-header, minimal-header, or separate logo/search-bar/icon-actions sections.
  - Footer can be site-footer, service-bar + link-grid, or brand-strip.
  - Use pages[].layout.*_width to control region width. Set main_width="full" only for intentionally edge-to-edge applications; otherwise prefer contained or wide. Keep page body/main background aligned unless the prompt explicitly wants visible margins.
  - Generate different chrome structure across the 3 candidates when the prompt does not force one pattern.

WORKFLOW ENTRY SECTIONS:
  - For each system.usecase_navigation.workflow_entry_points item, add or keep an activity_start section on that normal OOUI object page.
   - Use style.cta_label from button_label, for example "Checkout".
   - Never make an activity_start button the only meaningful section on that page. Add the pre-workflow workspace first: lists/tables/details/forms for the use case's primary_model and related child collections.
   - If the use case exposes child collection models such as Item/Line/Entry/Detail/Selection rows, render them as list/table sections before the activity_start button. Enable update/delete where the user is expected to adjust the collection before submitting, such as quantity changes or removing rows.
   - Do not put activity pages such as Payment or Shipping Address in the normal site nav; they are entered through the workflow engine only.

ACTIVITY TASK PAGES:
  - An activity page must not be only a Continue/Start button.
  - Add task content before activity_action: for "View Cart" show editable cart/item rows; for "Enter Shipping Address" show an address form; for "Select Payment Method" show payment/method form; for confirmation steps show order/detail/list content.
  - Keep activity_action as the final control on the page, after the user-facing task data.

DATA SECTIONS (for layout in card/list/table/detail/gallery/form/filter):
  - MANDATORY: Every data section MUST have a non-empty attributes list.
    CRITICAL: Use ONLY attribute names that ACTUALLY EXIST in the classifier from get_interface_full_context.
    Read the classifier's attributes[] array CAREFULLY — copy the exact field names character for character.
    NEVER invent attribute names. If the classifier has "loan_amount" not "amount_requested", use "loan_amount".
    Use ALL relevant fields (4-8 names). NEVER leave attributes as [].
  - Set operations: {{"create": bool, "update": bool, "delete": bool}} based on usecase_navigation.actor_permissions.
    Never enable create/update/delete for a model unless actor_permissions for that model includes it.
  - style: {{"color": "accent|accent-secondary", "density": "compact|normal|spacious",
             "shadow": "none|sm|md", "bg": "white|light|dark|transparent"}}
    ALWAYS use "accent" for data section colors — this uses the design spec's brand color via CSS variables.
  - component: choose the UI Kit component. Examples:
    gallery Product -> ProductCardGrid; gallery Category -> CategoryTileGrid; gallery person/user/customer/seller -> PersonCardGrid;
    table -> DataTable; list child item/line -> LineItemList; detail Product -> ProductDetailPanel; form -> ObjectForm/AddressForm/PaymentMethodForm/ReviewForm; filter -> FilterPanel.
  - field_layout: for display/form components, map fields into supported slots only. Example ProductCardGrid: {{"image":"image_url","video":"video_url","title":"name","primary":"price","secondary":["brand"],"hidden":["id"]}}.
    For video fields, include the video field in attributes as {{"name":"video_url","type":"video"}} and put it in field_layout.video or field_layout.media.
    To control individual field position/size, use field_layout.field_styles, e.g.
      {{"field_styles": {{"price": {{"order": 2, "col_span": 4, "text_size": "xl", "align": "right"}}, "description": {{"order": 3, "col_span": 12, "label": "hidden"}}}}}}
    For DataTable/List use {{"columns":["name","status","created_at"]}}. For ObjectForm/Filter use {{"fields":["name","status"]}}. Do not output groups/labels unless the renderer explicitly consumes them.
  - data_source/query: leave them empty by default. Only add query for explicit filtering/sorting/limits or page semantics such as "active only", "my orders", "same category", "recent", "top 5". Only add data_source when joins or a non-default source are actually needed.
  - behavior: for controls like SearchBar/NavBar/IconActions, use {{"type":"search|navigate|action","target_page":"Page_Name","target_model":"ModelName","fields":["name"],"param":"q"}}.
    For card/list/table/gallery item navigation, use {{"item_click": {{"type":"navigate","target_page":"Detail_Page","params":{{"id":"$Model.id"}}}}}}.

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
  Candidate 0 → diversity_hints[0]
  Candidate 1 → diversity_hints[1]
  Candidate 2 → diversity_hints[2]

Make candidates structurally different using these axes:
  - Column organization: one candidate uses col_span=12 dominant, another uses col_span=6 splits
    (col_span=4+4+4 for dashboards), another uses filter sidebar (col_span=3)
  - Chrome/regions: vary header/nav/footer/sidebar composition. At least one candidate should use a sidebar navigation rail when the app has multiple normal pages.
    Vary the rail's side and vertical placement: top, middle, or bottom relative to other sidebar sections.
    Other candidates should use different header/footer treatments, not the exact same site-nav/header/footer layout.
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
       pages=<JSON string containing pages list>,
       sections=<JSON string containing sections list>,
       tokens=<optional JSON string, not object>,
       styling=<optional JSON string, not object>,
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
        select_design_specs_for_interface_tool,
    ],
)

candidate_direct_agent = Agent(
    name="candidate_direct_agent",
    model=_model(),
    description="Reliably generates and saves 3 interface candidates through one deterministic tool call.",
    instruction="""You generate interface candidates by calling exactly one tool.

Message format: interface_id=<uuid> prompt=<designer intent>

Rules:
- Immediately call generate_candidate_set(interface_id, prompt).
- Color/style-only prompts such as "generate pink pages" are valid designer requirements.
- Do not refuse style-only prompts.
- After the tool returns OK, output the tool result. If it returns ERROR, output the error.
""",
    tools=[generate_candidate_set_tool],
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
- Do not create candidates yourself. The tool preserves page semantics, workflow/page types, data bindings, and activity flow order.
- After the tool returns OK, output the tool result. If it returns ERROR, output the error.
""",
    tools=[
        regenerate_candidate_set_tool,
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

root_agent = Agent(
    name="gemini_make_agent",
    model=_model(),
    description="Routes requests to the appropriate specialist agent.",
    instruction=f"""You are a routing agent for a UI design editor.

--- Routing Logic ---
If the message contains 'project_name=' (seed data request): transfer to seed_agent.
If the message contains 'regenerate_candidates' (selected-candidate regeneration): call candidate_regeneration_agent with the message and wait.
If the message contains 'generate_candidates' (3-candidate generation): call candidate_pipeline_agent with the message and wait.
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
  - ADD section: id, layout, col_span, position, primary_model, attributes (from classifier_fields ONLY)
  - MODIFY section: id, which fields change and to what value
  - REMOVE section: id
  - Page changes: new pages, layout changes, or sections reference order changes
  - Design system: keep current tokens OR select new spec (if style change requested)

HUMAN-IN-THE-LOOP LAYOUT RULE:
  Treat current_interface.pages and current_interface.sections as the source of truth. Preserve human/editor changes
  unless the user explicitly asks to change them. Apply surgical patches only: section layout/position/col_span/min_height,
  style, text/methods, and page.sections ordering. Do not regenerate or overwrite the whole interface for a small edit.

ATTRIBUTE RULE: Every attribute name in ADD/MODIFY entries MUST appear in classifier_fields["ModelName"].
               NEVER invent attribute names. Copy them character-for-character from the <analyze> block.

━━━ STEP 3 — EXECUTE ━━━
1. Call get_interface_config(interface_id) to verify current section IDs and token state.
2. Check design tokens (data.tokens):
   - If tokens are EMPTY/NULL (first-time edit) OR user requested a theme/style change:
     a. Call select_design_specs_for_interface(interface_id, count=3, prompt=<user_request>).
     b. Select the best spec. Call apply_design_system_to_interface_tool(interface_id, spec_name="...", prompt=<user_request>).
        If the user names a color such as purple, violet, blue, green, orange, rose, pink, red, dark, black, or slate,
        that color request is mandatory and must be reflected in tokens/accent/nav/button colors.
     c. If ONLY a style/theme change was requested and no layout changes are needed, STOP here.
3. Call apply_interface_patch exactly once with the complete patch derived from <plan>.
   - Attribute names: use ONLY names from classifier_fields verified in STEP 1.
   - style.color must be "accent" for all data sections (inherits brand color from spec).
   - ENSURE UI COMPLETENESS: if Header/Nav/Footer are missing, add them.
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
        get_design_system_tool, apply_design_system_to_interface_tool, list_design_specs_tool,
        select_design_specs_for_interface_tool,
        AgentTool(agent=candidate_regeneration_agent),
        AgentTool(agent=candidate_direct_agent),
    ],
    sub_agents=[seed_agent],
)

app = App(name="app", root_agent=root_agent)
candidate_app = App(name="candidate_app", root_agent=candidate_direct_agent)
candidate_regeneration_app = App(name="candidate_regeneration_app", root_agent=candidate_regeneration_agent)
