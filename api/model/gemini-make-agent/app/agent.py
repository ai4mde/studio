from google.adk.agents import Agent
from google.adk.apps import App
from app.tools import interface_config_tool, update_interface_patch_tool

_LAYOUT_FIELDS = """
sections[].layout        : "card" | "list" | "table" | "detail" | "gallery"
sections[].col_span      : 12 | 6 | 4 | 3
sections[].style.color   : "blue" | "green" | "purple" | "orange" | "rose" | "slate"
sections[].style.density : "compact" | "normal" | "spacious"
sections[].style.columns : "1" | "2" | "3" | "4"
sections[].style.image_position : "left" | "top" | "right"
sections[].style.image_size     : "sm" | "md" | "lg"
pages[].layout.value : "vertical" | "vertical-reverse" | "horizontal" | "horizontal-reverse"
pages[].gap.value    : "compact" | "normal" | "spacious"
"""

_STYLE_FIELDS = """
styling.radius, styling.text_color, styling.accent_color
tokens (all must be valid Tailwind CSS utility classes):
  page.body.bg, page.body.text, page.container.max_width, page.header.height,
  component.card.bg, component.card.border, component.card.shadow, component.nav.active,
  element.button.primary, element.button.secondary, element.input.bg, element.input.border,
  element.text.accent, element.text.muted,
  region.sidebar.bg, region.sidebar.width, region.footer.bg, region.header.bg
"""

layout_agent = Agent(
    name="layout_agent",
    model="openai/gpt-4o-mini",
    instruction=f"""You apply layout changes to UI sections and pages.

You receive a message containing: interface_id, the current sections/pages JSON, and the user's request.

Steps:
1. Determine which sections/pages need changes.
2. Build a patch dict with ONLY changed entries. Always include "id" for each changed item.
3. Call apply_interface_patch(interface_id="<uuid>", patch={{"sections": [...], "pages": [...]}}) to save.

Do NOT touch: class, attributes, operations, methods, name.

Editable fields:
{_LAYOUT_FIELDS}

Example patch:
{{"sections": [{{"id": "abc-123", "layout": "card", "col_span": 6, "style": {{"color": "blue"}}}}]}}
""",
    tools=[update_interface_patch_tool],
)

stylist_agent = Agent(
    name="stylist_agent",
    model="openai/gpt-4o-mini",
    instruction=f"""You apply visual style changes to a UI interface.

You receive a message containing: interface_id, the current styling/tokens JSON, and the user's request.

Steps:
1. Determine which style values need changes.
2. Build a patch dict with ONLY changed values.
3. Call apply_interface_patch(interface_id="<uuid>", patch={{"styling": {{...}}, "tokens": {{...}}}}) to save.

Editable fields:
{_STYLE_FIELDS}

Example patch:
{{"styling": {{"radius": "xl", "accent_color": "blue-600"}},
  "tokens": {{"page.body.bg": "bg-slate-900", "page.body.text": "text-slate-100"}}}}
""",
    tools=[update_interface_patch_tool],
)

root_agent = Agent(
    name="gemini_make_agent",
    model="openai/gpt-4o",
    instruction="""You orchestrate UI edits for a design editor.

Message format: interface_id=<uuid> user_request=<design change description>

Workflow:
1. Call get_interface_config(interface_id=<uuid>) to get the current interface data.
2. Decide which sub-agent to use based on the request:
   - Layout/structure changes (layout, columns, col_span) → layout_agent
   - Color/style/theme changes (colors, tokens, radius) → stylist_agent
   - Both types → call layout_agent first, then stylist_agent
3. Transfer to the chosen sub-agent. Include in your transfer message:
   - interface_id=<uuid>
   - The relevant current data (sections/pages for layout_agent; styling/tokens for stylist_agent)
   - The user's original request

Rules:
- Never modify: sections[].class, sections[].attributes, sections[].operations, sections[].name.
- Sub-agents persist changes directly; you do not need to call any save function yourself.
""",
    tools=[interface_config_tool],
    sub_agents=[layout_agent, stylist_agent],
)

app = App(name="app", root_agent=root_agent)
