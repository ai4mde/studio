from google.adk.agents import Agent
from google.adk.apps import App
from app.tools import interface_config_tool, update_interface_patch_tool, system_context_tool, run_seed_script_tool

_EDITABLE_FIELDS = """
Layout fields (sections/pages):
  sections[].layout        : "card" | "list" | "table" | "detail" | "gallery" | "filter" | "form"
  sections[].col_span      : 12 | 6 | 4 | 3
  sections[].position      : "main" | "sidebar" | "header" | "footer"

Data & Query fields:
  sections[].attributes    : list of attribute names. Supports dot-notation for cross-class data (e.g. ["name", "seller.name"])
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
Otherwise (interface_id= UI edit request): handle it directly.

--- UI edit workflow ---
Message format: interface_id=<uuid> user_request=<design change description>

1. Call get_interface_config(interface_id=<uuid>) to get the current data.
2. Analyze the request and determine all needed changes (layout, style, data mapping, queries, tokens).
3. If data mapping (attributes) or queries are requested, call get_system_context(system_id) to find valid fields and relations.
4. Build ONE patch dict with only the changed fields.
5. Call apply_interface_patch(interface_id=<uuid>, patch=<patch_dict>) EXACTLY ONCE to persist.

Path Binding (Multi-class mapping):
To show data from related classes, use dot-notation in sections[].attributes (e.g. "seller.name"). 
Only use paths that exist in the system relations (e.g. if Product has a relation to Seller).

Patch shape (only include changed fields):
{{
  "sections": [{{
    "id": "...", 
    "layout": "card", 
    "attributes": ["name", "price", "seller.name"],
    "query": {{"limit": 5, "order_by": ["-price"]}},
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
    tools=[interface_config_tool, update_interface_patch_tool, system_context_tool],
    sub_agents=[seed_agent],
)

app = App(name="app", root_agent=root_agent)
