from google.adk.agents import Agent
from google.adk.apps import App
from app.tools import interface_config_tool, update_interface_patch_tool

_EDITABLE_FIELDS = """
Layout fields (sections/pages):
  sections[].layout        : "card" | "list" | "table" | "detail" | "gallery" | "filter" | "form"
  sections[].col_span      : 12 | 6 | 4 | 3
  sections[].position      : "main" | "sidebar" | "header" | "footer"

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

root_agent = Agent(
    name="gemini_make_agent",
    model="openai/gpt-4o",
    instruction=f"""You edit UI interfaces for a design editor.

Message format: interface_id=<uuid> user_request=<design change description>

Workflow:
1. Call get_interface_config(interface_id=<uuid>) to get the current data.
2. Analyze the request and determine all needed changes (layout, style, tokens — handle all in one pass).
3. Build ONE patch dict with only the changed fields.
4. Call apply_interface_patch(interface_id=<uuid>, patch=<patch_dict>) EXACTLY ONCE to persist.

Patch shape (only include changed fields):
{{
  "sections": [{{"id": "...", "layout": "card", "col_span": 6, "style": {{"color": "blue", "density": "normal"}}}}],
  "pages":    [{{"id": "...", "layout": {{"value": "horizontal"}}, "gap": {{"value": "compact"}}}}],
  "styling":  {{"radius": "xl", "accent_color": "blue-600"}},
  "tokens":   {{"page.body.bg": "bg-slate-900", "page.body.text": "text-slate-100"}}
}}

Editable fields:
{_EDITABLE_FIELDS}

Rules:
- NEVER modify: sections[].class, sections[].attributes, sections[].operations, sections[].name.
- Always keep "id" in every section/page entry in the patch.
- Call apply_interface_patch exactly once with the complete combined patch.
""",
    tools=[interface_config_tool, update_interface_patch_tool],
)

app = App(name="app", root_agent=root_agent)
