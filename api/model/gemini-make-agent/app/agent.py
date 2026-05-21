from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools import AgentTool
from app.tools import (
    interface_config_tool, update_interface_patch_tool, system_context_tool,
    run_seed_script_tool, get_available_paths_tool,
    get_interface_full_context_tool, validate_save_candidate_tool, render_candidate_preview_tool,
)

_EDITABLE_FIELDS = """
Layout fields (sections/pages):
  sections[].layout        : "card" | "list" | "table" | "detail" | "gallery" | "filter" | "form"
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

Detail style (layout="detail"):
  sections[].style.image_position : "left" | "top" | "right"
  sections[].style.image_size     : "sm" | "md" | "lg"

Universal style controls:
  sections[].style.color         : "blue" | "green" | "purple" | "orange" | "rose" | "slate"
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
  styling.radius, styling.text_color, styling.accent_color
  tokens (valid Tailwind CSS classes):
    page.body.bg, page.body.text, page.container.max_width, page.header.height,
    component.card.bg, component.card.border, component.card.shadow, component.nav.active,
    element.button.primary, element.button.secondary, element.input.bg, element.input.border,
    element.text.accent, element.text.muted,
    region.sidebar.bg, region.sidebar.width, region.footer.bg, region.header.bg
"""

# ── Candidate Generation Pipeline ────────────────────────────────────────────

reason_agent = Agent(
    name="reason_agent",
    model="openai/gpt-4o",
    description="Analyses UML metadata and designer prompt to produce a structured reasoning JSON for interface generation.",
    instruction="""You analyse a system's UML metadata and a designer prompt to produce a structured reasoning JSON that will guide generation of 3 interface candidates.

Message format: interface_id=<uuid> prompt=<designer intent>

Workflow:
1. Call get_interface_full_context(interface_id) to get the interface structure, classifiers, relations, use cases, and activities.
2. Reason about:
   - Which pages the actor needs (one per major use-case or object workspace)
   - OOUI principles that apply (workspace, navigation area, object detail, collection)
   - Which model belongs on which page as primary_model
   - All navigation transitions between pages (who navigates where, what ID is passed)
   - Which pages appear in the nav bar
   - What operations the actor can perform on each model
   - 3 structurally distinct diversity directions for the candidates
3. Output ONLY a JSON object with this exact shape (no markdown, no explanation):
{
  "interface_id": "<uuid>",
  "actor_role": "<actor name>",
  "ooui_principles": ["<principle>", ...],
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
    "card-forward layout with prominent imagery and grid browsing",
    "data-dense table with sidebar filter and inline actions",
    "immersive detail-first with expanded object view"
  ]
}

Rules:
- page name must be Title_Case with underscores (e.g. Browse_Products, Product_Detail)
- page id must be snake_case matching the name lowercased
- navigation_edges must cover EVERY meaningful user transition
- stays:true means after the action the user stays on the current page
- diversity_hints must be genuinely structurally different, not just colour variations
- Output ONLY the JSON object. No markdown fences.
""",
    tools=[get_interface_full_context_tool],
)


generate_agent = Agent(
    name="generate_agent",
    model="openai/gpt-4o",
    description="Generates 3 complete Interface DSL candidates from the reasoning JSON.",
    instruction=f"""You generate 3 complete Interface DSL candidates from the reasoning JSON produced by reason_agent.

The reasoning JSON is in the conversation history. Read it and generate one candidate per diversity_hint.

For EACH candidate (index 0, 1, 2):
1. Build a complete pages[] and sections[] using the reasoning JSON.
2. Call validate_and_save_candidate(interface_id, candidate_index, name, description, pages, sections).
   - If it returns errors, fix them and call again.
   - Do NOT proceed to the next candidate until the current one is saved OK.

SECTION RULES — every section must have ALL applicable fields:

primary_model:     exact model name from classifiers (or "" for chrome sections)
layout:            one of: {" | ".join(sorted(["card","list","table","detail","gallery","filter","form",
                   "activity_action","promo-bar","logo","search-bar","icon-actions","nav-links",
                   "main-header","minimal-header","site-nav","site-footer","service-bar","link-grid","brand-strip"]))}
col_span:          12 | 6 | 4 | 3
position:          "header" | "hero" | "main" | "sidebar" | "footer"
view_detail_page:  target page NAME (Title_Case) if this list/card navigates to a detail — from navigation_edges
operations:        {{"create": bool, "update": bool, "delete": bool}} — from actor_permissions
query:             {{"limit": int, "order_by": [...]}}  for list/card/table sections
attributes:        list of attribute names or objects:
  - plain string: "name"
  - with render+action: {{"name": "field", "render": {{"as": "text"|"link"|"button"|"badge"}}, "action": {{"type": "navigate"|"filter"|"operation"|"none", "targetPageId": "<page_name>"}}}}
  - dot-notation for FK: "Product.name"
style:             all applicable fields per layout:
  color: blue|green|purple|orange|rose|slate
  density: compact|normal|spacious
  shadow: none|sm|md|lg|xl
  border: none|light|colored|strong
  bg: white|light|gray|dark
  header_style: default|large|small|colored|hidden
  card_style (card): default|product|category|compact
  display_mode (card): grid|carousel|banner
  list_style (list): default|product|cart-item
  form_style (form): default|auth|step|summary
  cta_label: any string
  success_page (form): target page NAME — from navigation_edges
  image_position (detail): left|top|right
  image_size (detail): sm|md|lg

NAVIGATION COMPLETENESS — mandatory:
- Every list/card section that has a navigation_edge leading to a detail page MUST set view_detail_page
- Every form section MUST set style.success_page from navigation_edges
- site-nav OR nav-links chrome section MUST be included in EVERY candidate listing all nav_bar_pages
- icon-actions chrome section MUST list all icon_actions from reasoning JSON

DIVERSITY — candidates must have genuinely different layouts:
- Candidate 0: follow diversity_hints[0]
- Candidate 1: follow diversity_hints[1]
- Candidate 2: follow diversity_hints[2]

After all 3 candidates are saved, output: "All 3 candidates saved. Transferring to render_agent."
Then transfer to render_agent.
""",
    tools=[validate_save_candidate_tool, get_available_paths_tool],
)


render_agent = Agent(
    name="render_agent",
    model="openai/gpt-4o",
    description="Renders preview HTML for all 3 saved candidates.",
    instruction="""You render preview HTML for all 3 saved interface candidates.

The interface_id is in the conversation history.

For candidate_index 0, 1, 2:
  Call render_candidate_preview(interface_id, candidate_index).
  If it returns an error, report it but continue with the next candidate.

After all renders are attempted, output: "Previews rendered. Pipeline complete."
""",
    tools=[render_candidate_preview_tool],
)


candidate_pipeline_agent = Agent(
    name="candidate_pipeline_agent",
    model="openai/gpt-4o",
    description="Runs the 3-candidate interface generation pipeline: reason → generate 3 candidates → render previews.",
    instruction=f"""You generate 3 interface design candidates for a given interface.

Message format: interface_id=<uuid> prompt=<designer intent>

━━━ PHASE 1 — REASON ━━━
1. Call get_interface_full_context(interface_id) to get classifiers, relations, use cases, activities.
2. Analyse the data and the designer prompt. Produce an internal reasoning plan covering:
   - Which pages the actor needs (one per major use-case or object workspace)
   - Which model is primary on each page
   - Navigation transitions between pages (what triggers them, what ID is passed)
   - Which pages appear in the nav bar
   - What operations the actor can perform per model
   - 3 structurally distinct layout directions for the candidates

━━━ PHASE 2 — GENERATE ━━━
For each candidate (index 0, 1, 2):
  - Build complete pages[] and sections[] following the layout direction for that index.
  - Call validate_and_save_candidate(interface_id, candidate_index, name, description, pages, sections).
    If it returns errors, fix them and call again. Do NOT proceed to next candidate until saved OK.

PAGE rules — every page MUST have:
  id:       snake_case identifier (e.g. "browse_products")
  name:     Title_Case_with_underscores (e.g. "Browse_Products")
  sections: list of section id strings that belong on this page (e.g. ["s0_0", "s0_1"])
            ← THIS IS CRITICAL. Each non-chrome section MUST appear in exactly ONE page's sections list.
            Chrome sections (site-nav, icon-actions, search-bar in header/footer) are auto-injected; omit them from sections lists.

Section rules — every section MUST include:
  id:            unique string (e.g. "s0_0", "s1_browse_main")
  primary_model: exact model name from classifiers (or "" for chrome)
  layout:        card | list | table | detail | gallery | filter | form | site-nav | icon-actions | search-bar
  col_span:      12 | 6 | 4 | 3
  position:      header | hero | main | sidebar | footer
  view_detail_page: target page NAME (Title_Case) if list/card navigates to detail
  operations:    {{"create": bool, "update": bool, "delete": bool}}
  query:         {{"limit": int, "order_by": [...]}} for list/card/table
  attributes:    list of strings or objects: {{"name": "field", "render": {{"as": "text|link|button|badge"}}, "action": {{"type": "navigate|filter|operation|none"}}}}
  style:         color (blue|green|purple|orange|rose|slate), density (compact|normal|spacious),
                 shadow (none|sm|md|lg), border (none|light|colored), bg (white|light|dark),
                 + layout-specific: card_style, display_mode, list_style, form_style, image_position, etc.

Candidate diversity:
  - Candidate 0: card-forward layout with prominent imagery and grid browsing
  - Candidate 1: data-dense table with sidebar filter and inline actions
  - Candidate 2: immersive detail-first with expanded object view

Navigation completeness (MANDATORY):
  - Every list/card section with a detail navigation target MUST set view_detail_page
  - Every form section MUST set style.success_page
  - Include a site-nav or nav-links chrome section in EVERY candidate covering nav pages
  - Include an icon-actions chrome section listing icon actions

━━━ PHASE 3 — RENDER ━━━
For candidate_index 0, 1, 2:
  Call render_candidate_preview(interface_id, candidate_index).
  If it returns an error, report it and continue.

━━━ DONE ━━━
After all 3 phases complete, output exactly: "done"

IMPORTANT: You MUST execute ALL THREE PHASES before outputting "done".
Do not output "done" after only phase 1 or 2.
""",
    tools=[
        get_interface_full_context_tool,
        validate_save_candidate_tool,
        render_candidate_preview_tool,
        get_available_paths_tool,
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
- Never truncate the script — include all model creation code.
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

If the message contains 'project_name=' (seed data request): transfer to seed_agent.
If the message contains 'generate_candidates' (3-candidate generation): call candidate_pipeline_agent with the message and wait for it to complete.
Otherwise (interface_id= UI edit request): handle it directly.

--- UI edit workflow ---
Message format: interface_id=<uuid> user_request=<design change description>

1. Call get_interface_config(interface_id=<uuid>) to get the current data.
2. Analyze the request and determine all needed changes (layout, style, data mapping, queries, tokens).
3. If data mapping or queries are requested:
   a. Call get_system_context(system_id) to find valid fields and relations.
   b. Call get_available_paths(system_id, class_id) to get valid paths.
4. Build ONE patch dict with only the changed fields.
5. Call apply_interface_patch(interface_id=<uuid>, patch=<patch_dict>) EXACTLY ONCE to persist.

Path Binding (Multi-class mapping):
To show data from related classes, use dot-notation in attributes (e.g. "seller.name").
For field rendering, prefer render.as:
- Text field: "name" or {{"name": "name", "render": {{"as": "text"}}}}
- Link navigation field: {{"name": "seller.name", "render": {{"as": "link"}}, "action": {{"type": "navigate", "targetPageId": "seller-detail"}}}}
- Button operation field: {{"name": "order.status", "render": {{"as": "button"}}, "action": {{"type": "operation", "class": "Order", "operation": "approve"}}}}
- Badge/status field: {{"name": "status", "render": {{"as": "badge"}}, "action": {{"type": "filter", "field": "status"}}}}
- Text utility field: {{"name": "customer.email", "render": {{"as": "text"}}, "action": {{"type": "copy"}}}}
Backward compatibility: if the user explicitly says is_link, {{"name": "seller.name", "is_link": true}} is also valid.

Patch shape (only include changed fields):
{{
  "sections": [{{
    "id": "...", 
    "attributes": ["name", {{"name": "seller.name", "render": {{"as": "link"}}, "action": {{"type": "navigate", "targetPageId": "seller-detail"}}}}, {{"name": "status", "render": {{"as": "badge"}}, "action": {{"type": "filter", "field": "status"}}}}],
    "query": {{"limit": 5, "order_by": [{{"field": "price", "direction": "desc"}}]}},
    "style": {{"color": "blue"}}
  }}],
  "pages":    [{{"id": "...", "layout": {{"value": "horizontal"}}, "gap": {{"value": "compact"}}}}],
  "styling":  {{"radius": "xl", "accent_color": "blue-600"}},
  "tokens":   {{"page.body.bg": "bg-slate-900", "page.body.text": "text-slate-100"}}
}}

Editable fields:
{_EDITABLE_FIELDS}

Rules:
- NEVER modify: sections[].class, sections[].operations, sections[].name.
- Always keep "id" in every section/page entry in the patch.
- Call apply_interface_patch exactly once with the complete combined patch.
""",
    tools=[
        interface_config_tool, update_interface_patch_tool, system_context_tool, get_available_paths_tool,
        AgentTool(agent=candidate_pipeline_agent),
    ],
    sub_agents=[seed_agent],
)

app = App(name="app", root_agent=root_agent)
