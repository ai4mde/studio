PROSE_GENERATE_STYLE = """
You are a senior UI/UX designer and CSS expert. A designer has described the visual style they want for a web application.
Generate a COMPLETE, PRODUCTION-QUALITY design configuration that makes the app look exactly like they described.

Available layout types:
  sidebar   — classic left navigation panel
  topnav    — horizontal menu bar at top
  dashboard — icon rail + dark side panel (great for data-heavy apps)
  split     — master-detail two-pane layout
  wizard    — step-by-step guided flow
  minimal   — clean centered content, minimal chrome
  cards     — responsive card grid layout
  tabs      — tabbed section navigation
  drawer    — hamburger menu side drawer

Available display modes (how data rows are shown):
  table — classic rows/columns (default)
  cards — each record as a visual card in a grid
  list  — compact list rows with avatar-style left side

Output ONLY a JSON object between STYLE_START and STYLE_END markers. No extra text, no markdown.

STYLE_START
{{
  "accent_color": "<hex>",
  "background_color": "<hex>",
  "text_color": "<hex>",
  "radius": <0-20>,
  "font_url": "<Google Fonts CSS2 URL or empty string>",
  "layout_type": "<layout value>",
  "display_mode": "<table|cards|list>",
  "custom_css": "<comprehensive CSS string — see requirements below>"
}}
STYLE_END

CUSTOM CSS REQUIREMENTS — you MUST generate CSS for ALL of these:

1. Table header — background gradient or solid, font size, letter spacing, color
2. Table rows — alternating row colors OR hover highlight, transition animations
3. Table cells — padding, font size, line height
4. Action buttons (Edit / Delete / Save) — unique gradient, box-shadow, hover transform, border-radius
5. Primary .btn — gradient background using accent, shadow, hover scale/glow effect
6. .btn-outline — border style, hover fill animation
7. Form inputs — border, focus ring with accent glow, background, placeholder color
8. .badge — pill style with appropriate background/text for the theme
9. Cards (.card-item if used) — border, shadow, hover lift effect, inner layout
10. Links .object-link — color, underline style, hover effect
11. Scrollbar — custom webkit scrollbar matching the theme
12. Body/page background — can be gradient, pattern-like with CSS, or solid
13. Typography — font-weight hierarchy, letter-spacing for headings, line-height

The CSS must DEEPLY transform the visual appearance — not just recolor but reshape the aesthetic.
Use CSS variables, gradients, box-shadows, transitions, transforms, and border-radius freely.
Think: what would a Dribbble-quality UI for this description look like?

Rules:
- All hex colors: full 6-digit format #rrggbb
- radius: 0=sharp, 4=subtle, 8=rounded, 16=pill-shaped
- font_url: valid Google Fonts URL or empty string. Example: https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap
- custom_css: escape all double-quote characters as \\", newlines as \\n within the JSON string
- display_mode: pick whichever matches the description best (cards/list make visual sense for product listings, task boards; table for structured data)
- Make the design match the designer's description PRECISELY — if they say dark, go dark; if they say luxury, use gold; if they say hacker, use monospace green-on-black

Designer's description:
"{data[prompt]}"
"""

PROSE_GENERATE_DJANGO_TEMPLATE = """
You are a world-class UI engineer at a top product design studio. Your job is to write Django HTML templates that look like they came from a premium SaaS product — NOT a generic CRUD app. Stakeholders will judge the prototype by how it looks.

━━━━━━━━━━━━━━━━━━━━━━━━ CRITICAL RULE — BE GENUINELY DIFFERENT ━━━━━━━━━━━━━━━━━━━━━━━━
❌ DO NOT generate a table with rows, or plain div cards stacked vertically.
❌ DO NOT copy the default "list of records in a box" pattern.
❌ DO NOT produce a generic CRUD form page.
✅ INVENT a real visual metaphor that matches the designer's brief and the data.
✅ Use <style> blocks freely — write real CSS (grid-template-areas, clip-path, backdrop-filter, animations, etc.)
✅ Every page must have a distinct, memorable visual identity.

━━━━━━━━━━━━━━━━━━━━━━━━ DJANGO TEMPLATE SYNTAX ━━━━━━━━━━━━━━━━━━━━━━━━
Use standard Django template tags only (NOT Jinja2):
  {{ variable }}                     render a value
  {% for obj in list %}...{% endfor %}
  {% if condition %}...{% endif %}
  {% url 'namespace:view_name' %}
  {% url 'namespace:view_name' arg %}
  {% csrf_token %}                   required in every POST form

━━━━━━━━━━━━━━━━━━━━━━━━ OOUI PRINCIPLES ━━━━━━━━━━━━━━━━━━━━━━━━
Objects first, actions second.
  ✓ Each object gets prominent visual space — large name, visible key fields
  ✓ Actions (Edit/Delete/Create) appear near the object, never dominate the page
  ✗ Never lead with a big "Add New" button before showing existing objects

━━━━━━━━━━━━━━━━━━━━━━━━ DESIGN TOOLKIT ━━━━━━━━━━━━━━━━━━━━━━━━
You may use:
  • <style> blocks with full CSS — grid-template-areas, CSS custom properties, @keyframes, backdrop-filter, clip-path, gradients, transitions
  • Tailwind utility classes for spacing/typography (loaded globally)
  • Custom CSS variables: bg-bg-main, text-text-main, bg-accent, text-accent, rounded-custom (Tailwind custom tokens)
  • Inline SVG icons
  • Any CSS layout: asymmetric grid, masonry, magazine columns, hero+sidebar split, kanban lanes, bento tiles, timeline rail, etc.

━━━━━━━━━━━━━━━━━━━━━━━━ REQUIRED TEMPLATE STRUCTURE ━━━━━━━━━━━━━━━━━━━━━━━━
Each template MUST:
  1. First line: {% extends "APP_NAME_base.html" %}  (use actual app name)
  2. All content inside: {% block content %}...{% endblock %}
  3. NO <html>, <head>, <body>, <script src>, <link> tags
  4. Cover ALL sections: list, create form (toggle), edit form (toggle), delete

━━━━━━━━━━━━━━━━━━━━━━━━ PAGE SPECIFICATIONS ━━━━━━━━━━━━━━━━━━━━━━━━
{pages_spec}

━━━━━━━━━━━━━━━━━━━━━━━━ INTERACTION PATTERNS ━━━━━━━━━━━━━━━━━━━━━━━━
Show create form only when URL param present:
  <form method="get" action="{% url 'APP:render_APP_PAGE' %}">
    <input type="hidden" name="create_SECTION" value="true">
    <button>+ Add</button>
  </form>
  {% if create_SECTION %}
  <form method="post" action="{% url 'APP:PAGE_SECTION_create' %}">{% csrf_token %}
    <!-- inputs for each field -->
    <button type="submit">Save</button>
  </form>
  {% endif %}

Delete (POST form, inline with object):
  <form method="post" action="{% url 'APP:PAGE_SECTION_delete' obj.id %}">{% csrf_token %}
    <button type="submit" onclick="return confirm('Delete?')">✕</button>
  </form>

Edit (GET param to same render URL):
  <form method="get" action="{% url 'APP:render_APP_PAGE' %}">
    <input type="hidden" name="instance_id_MODELNAME" value="{{ obj.id }}">
    <button type="submit">Edit</button>
  </form>
  {% if update_instance %}
  <form method="post" action="{% url 'APP:modelname_update' %}">{% csrf_token %}
    <input type="hidden" name="instance_id_MODELNAME" value="{{ update_instance.id }}">
    <!-- edit fields -->
    <button type="submit">Save</button>
  </form>
  {% endif %}

━━━━━━━━━━━━━━━━━━━━━━━━ DESIGNER'S BRIEF ━━━━━━━━━━━━━━━━━━━━━━━━
"{prompt}"

━━━━━━━━━━━━━━━━━━━━━━━━ OUTPUT FORMAT ━━━━━━━━━━━━━━━━━━━━━━━━
One template per page. Wrap each in:

PAGE_START:page_name
{% extends "APP_NAME_base.html" %}
{% block content %}
<style>
/* your custom CSS here — be bold */
</style>
<!-- your HTML here — be genuinely different from a plain CRUD table -->
{% endblock %}
PAGE_END:page_name

Rules:
- page_name must exactly match the name in the spec
- No markdown code fences inside the markers
- Each template is self-contained and complete
- The result must look like a premium product, not a tutorial scaffold
"""

PROSE_GENERATE_OOUI_PAGE = """
You are an expert UI/UX designer specialising in OOUI (Object-Oriented User Interface) design.
Your task: generate a Jinja2 template file that replaces the default page template for a Django prototype application.

━━━━━━━━━━━━━━━━━━━━━━━━ SYSTEM ARCHITECTURE ━━━━━━━━━━━━━━━━━━━━━━━━
This project uses a TWO-LEVEL TEMPLATE system:
  Level 1 — Jinja2 (runs at BUILD time, knows the schema/structure)
  Level 2 — Django templates (runs at RUNTIME, renders real database records)

You output Level 1: a Jinja2 template.
The Jinja2 engine renders it to produce a Level 2 Django template file.

━━━━━━━━━━━━━━━━━━━━━━━━ JINJA2 VARIABLES AVAILABLE ━━━━━━━━━━━━━━━━━━━━━━━━
  application_name   — Django app name (string, e.g. "inventory")
  page               — Page object; page.section_components = list of sections; str(page) = page URL name
  styling            — Styling object; styling.accent_color, styling.background_color, etc.
  AttributeType      — Enum: AttributeType.STRING, INTEGER, DATE, DATETIME, BOOLEAN, ENUM

Per section_component (in Jinja2 for-loop over page.section_components):
  section_component.primary_model      — Django model class name, e.g. "Product"
  section_component.display_name       — Human label, e.g. "Products"
  section_component.text               — Optional description string
  section_component.attributes         — List of Attribute; each has .name, .type, .derived, .enum_literals
  section_component.parent_models      — List of FK parent model names (strings)
  section_component.has_create_operation   — bool
  section_component.has_update_operation   — bool
  section_component.has_delete_operation   — bool
  section_component.custom_methods     — List of custom method names
  str(section_component)               — sanitized name used in URL patterns

━━━━━━━━━━━━━━━━━━━━━━━━ CRITICAL ESCAPING RULES ━━━━━━━━━━━━━━━━━━━━━━━━

RULE 1 — Jinja2 evaluates its own {{ }} and {% %} at build time.
         To output Django {{ }} and {% %} literally, you MUST use raw/endraw blocks:

  To get Django:  {% for product in product_list %}
  Jinja2 writes:  {%- raw %}{%{% endraw %} for {{ section_component.primary_model }} in {{ section_component.primary_model }}_list {% raw %}%}{% endraw %}

  To get Django:  {% endfor %}
  Jinja2 writes:  {% raw %}{% endfor %}{% endraw %}

  To get Django:  {% if create_products %}...{% endif %}
  Jinja2 writes:  {% raw %}{%{% endraw %} if create_{{ section_component }} {% raw %}%}{% endraw %}...{% raw %}{% endif %}{% endraw %}

  To get Django:  {% csrf_token %}
  Jinja2 writes:  {% raw %}{% csrf_token %}{% endraw %}

  To get Django:  {{ product.name }}
  Jinja2 writes:  {% raw %}{{{% endraw %} {{ section_component.primary_model }}.name {% raw %}}}{% endraw %}

  To output the value of a Jinja2 attribute directly (resolved at build time), use {{ }} normally:
    {{ section_component.display_name }}  →  resolves to e.g. "Products" at build time

RULE 2 — Jinja2 loops (over sections) use normal Jinja2 syntax, NOT wrapped in raw:
  CORRECT:   {%- for section_component in page.section_components %}
  WRONG:     {% raw %}{%{% endraw %} for section_component in page.section_components {% raw %}%}{% endraw %}

RULE 3 — The extends and block tags MUST appear once, escaped for Jinja2 output:
  {% raw %}{%{% endraw %} extends "{{ application_name }}_base.html" {% raw %}%}{% endraw %}
  {% raw %}{% block content %}{% endraw %}
  ...content...
  {% raw %}{% endblock %}{% endraw %}

━━━━━━━━━━━━━━━━━━━━━━━━ DJANGO RUNTIME VARIABLES ━━━━━━━━━━━━━━━━━━━━━━━━
These Django template variables exist at runtime (use the escaping rules above):

  {model}_list            — QuerySet e.g. product_list, order_list
  update_instance         — instance currently being edited (or None)
  create_{section}        — bool: is create form open for this section?

URL patterns (apply escaping rule 1):
  Render page:   {% url 'app:render_app_page' %}
  Create:        {% url 'app:page_section_create' %}
  Delete:        {% url 'app:page_section_delete' obj.id %}
  Detail:        {% url 'app:model_detail' obj.id %}

In Jinja2, these become:
  {% raw %}{%{% endraw %} url '{{ application_name }}:render_{{ application_name }}_{{ page }}' {% raw %}%}{% endraw %}
  {% raw %}{%{% endraw %} url '{{ application_name }}:{{ page }}_{{ section_component }}_create' {% raw %}%}{% endraw %}
  {% raw %}{%{% endraw %} url '{{ application_name }}:{{ page }}_{{ section_component }}_delete' {{ section_component.primary_model }}.id {% raw %}%}{% endraw %}
  {% raw %}{%{% endraw %} url '{{ application_name }}:{{ section_component.primary_model|lower }}_detail' {{ section_component.primary_model }}.id {% raw %}%}{% endraw %}

━━━━━━━━━━━━━━━━━━━━━━━━ OOUI DESIGN PRINCIPLES ━━━━━━━━━━━━━━━━━━━━━━━━
OOUI = Object-Oriented User Interface. The UI is built around OBJECTS (nouns), not ACTIONS (verbs).

  ✓ Objects are CENTER STAGE — each object type has a dedicated visual area
  ✓ Show object names as prominent, clickable headings (detail links)
  ✓ Properties of an object are shown together, grouped
  ✓ Actions (Edit, Delete, Create) are SECONDARY — smaller, tucked away
  ✓ The user SEES and NAVIGATES objects, then discovers what they can do
  ✗ Do NOT design around "click here to CREATE", "click here to DELETE"
  ✗ Avoid action-first layouts (wizard steps, action menus as primary focus)

Examples of OOUI-compliant layouts (choose what fits the domain):
  - Kanban board columns per object type, cards per object
  - Magazine/blog grid: large image-style card per object with key attributes
  - Object detail panel: object selected on left, full properties on right
  - Bento grid: different sized tiles for different object types
  - Timeline: objects arranged chronologically
  - Gallery with hover overlays for actions

━━━━━━━━━━━━━━━━━━━━━━━━ COMPLETE EXAMPLE (minimal) ━━━━━━━━━━━━━━━━━━━━━━━━

{% raw %}{%{% endraw %} extends "{{ application_name }}_base.html" {% raw %}%}{% endraw %}
{% raw %}{% block content %}{% endraw %}
<div style="padding:2rem; display:flex; flex-direction:column; gap:3rem;">
{%- for section_component in page.section_components %}
<section>
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;">
    <h2 style="font-size:1.25rem; font-weight:700;">{{ section_component.display_name }}</h2>
    {% if section_component.has_create_operation %}
    {% raw %}{%{% endraw %} if not create_{{ section_component }} {% raw %}%}{% endraw %}
    <form method="get" action="{% raw %}{%{% endraw %} url '{{ application_name }}:render_{{ application_name }}_{{ page }}' {% raw %}%}{% endraw %}">
      <input type="hidden" name="create_{{ section_component }}" value="true">
      <button type="submit" style="background:#6366f1;color:#fff;padding:0.4rem 1rem;border-radius:6px;border:none;cursor:pointer;">+ Add</button>
    </form>
    {% raw %}{% endif %}{% endraw %}
    {% endif %}
  </div>
  {% if section_component.has_create_operation %}
  {% raw %}{%{% endraw %} if create_{{ section_component }} {% raw %}%}{% endraw %}
  <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:1.5rem;margin-bottom:1.5rem;">
    <form method="post" action="{% raw %}{%{% endraw %} url '{{ application_name }}:{{ page }}_{{ section_component }}_create' {% raw %}%}{% endraw %}">
      {% raw %}{% csrf_token %}{% endraw %}
      {%- for attribute in section_component.attributes %}{% if not attribute.derived %}
      <div style="margin-bottom:1rem;"><label style="display:block;font-weight:600;margin-bottom:0.25rem;">{{ attribute.name | replace('_',' ') | title }}</label>
        {% if attribute.type == AttributeType.STRING %}<input type="text" name="{{ attribute }}" style="width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:0.5rem;">
        {%- elif attribute.type == AttributeType.INTEGER %}<input type="number" name="{{ attribute }}" style="width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:0.5rem;">
        {%- elif attribute.type == AttributeType.DATE %}<input type="date" name="{{ attribute }}" style="width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:0.5rem;">
        {%- elif attribute.type == AttributeType.BOOLEAN %}<input type="checkbox" name="{{ attribute }}">
        {%- elif attribute.type == AttributeType.ENUM %}<select name="{{ attribute }}" style="width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:0.5rem;">{% for lit in attribute.enum_literals %}<option value="{{ lit }}">{{ lit }}</option>{% endfor %}</select>
        {%- endif %}</div>
      {% endif %}{%- endfor %}
      {%- for pm in section_component.parent_models %}
      <div style="margin-bottom:1rem;"><label style="display:block;font-weight:600;margin-bottom:0.25rem;">{{ pm }}</label>
        <select name="{{ pm }}" style="width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:0.5rem;">
          {% raw %}{%{% endraw %} for i in parent_{{ pm }}_list {% raw %}%}{% endraw %}{% raw %}<option value="{{ i.id }}">{{ i }}</option>{% endraw %}{% raw %}{% endfor %}{% endraw %}
        </select></div>
      {%- endfor %}
      <input type="submit" value="Save" style="background:#6366f1;color:#fff;padding:0.4rem 1.2rem;border-radius:6px;border:none;cursor:pointer;">
    </form>
  </div>
  {% raw %}{% endif %}{% endraw %}
  {% endif %}
  <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap:1rem;">
  {% raw %}{%{% endraw %} for {{ section_component.primary_model }} in {{ section_component.primary_model }}_list {% raw %}%}{% endraw %}
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:1.25rem;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
    {%- if section_component.attributes %}
    <a href="{% raw %}{%{% endraw %} url '{{ application_name }}:{{ section_component.primary_model|lower }}_detail' {{ section_component.primary_model }}.id {% raw %}%}{% endraw %}" style="font-size:1rem;font-weight:700;color:#6366f1;text-decoration:none;">{% raw %}{{{% endraw %} {{ section_component.primary_model }}.{{ section_component.attributes[0] }} {% raw %}}}{% endraw %}</a>
    {%- for attribute in section_component.attributes[1:] %}
    <div style="margin-top:0.5rem;font-size:0.85rem;color:#64748b;"><span style="font-weight:600;">{{ attribute.name | replace('_',' ') | title }}:</span> {% raw %}{{{% endraw %} {{ section_component.primary_model }}.{{ attribute }} {% raw %}}}{% endraw %}</div>
    {%- endfor %}
    {%- endif %}
    <div style="margin-top:1rem;display:flex;gap:0.5rem;">
      {% if section_component.has_update_operation %}
      <form method="get" action="{% raw %}{%{% endraw %} url '{{ application_name }}:render_{{ application_name }}_{{ page }}' {% raw %}%}{% endraw %}">
        <input type="hidden" name="instance_id_{{ section_component.primary_model }}" value="{% raw %}{{{% endraw %} {{ section_component.primary_model }}.id {% raw %}}}{% endraw %}">
        <button type="submit" style="font-size:0.75rem;color:#6366f1;background:none;border:none;cursor:pointer;text-decoration:underline;">Edit</button>
      </form>
      {% endif %}
      {% if section_component.has_delete_operation %}
      <form method="post" action="{% raw %}{%{% endraw %} url '{{ application_name }}:{{ page }}_{{ section_component }}_delete' {{ section_component.primary_model }}.id {% raw %}%}{% endraw %}">
        {% raw %}{% csrf_token %}{% endraw %}
        <button type="submit" style="font-size:0.75rem;color:#ef4444;background:none;border:none;cursor:pointer;" onclick="return confirm('Delete?')">Delete</button>
      </form>
      {% endif %}
    </div>
  </div>
  {% raw %}{% endfor %}{% endraw %}
  </div>
</section>
{%- endfor %}
</div>
{% raw %}{% endblock %}{% endraw %}

━━━━━━━━━━━━━━━━━━━━━━━━ YOUR TASK ━━━━━━━━━━━━━━━━━━━━━━━━

Domain / Model context:
{data[model_context]}

Designer's aesthetic prompt:
"{data[prompt]}"

Now generate a COMPLETE, CREATIVE, PRODUCTION-QUALITY Jinja2 page template that:
  1. Strictly follows the escaping rules above (this is critical — wrong escaping breaks the app)
  2. Embodies OOUI principles (objects first, actions secondary)
  3. Matches the designer's aesthetic description faithfully
  4. Uses inline CSS freely to achieve the desired look (Tailwind classes are available but optional)
  5. Handles ALL of: list display, create form, edit, delete actions for EACH section_component
  6. Is fully self-contained — no external script tags, no <html>/<body>/<head> tags

Output ONLY the Jinja2 template content between PAGE_JINJA2_START and PAGE_JINJA2_END.
Do NOT include any explanation, markdown, or code fences inside the markers.

PAGE_JINJA2_START
[your complete Jinja2 template here]
PAGE_JINJA2_END
"""

PROSE_GENERATE_CUSTOM_LAYOUT = """
You are a web UI designer. Generate a complete HTML layout for a web application based on the designer's description.

The HTML is injected into a Django template that already provides Tailwind CSS (via CDN) and custom CSS variables.
Available Tailwind color aliases: bg-bg-main, text-text-main, bg-accent, text-accent, bg-accent-light, rounded-custom.
You may also use any standard Tailwind utility classes or inline styles.

RULES:
- Output ONLY the raw HTML. No markdown, no code fences, no explanation.
- Do NOT include <html>, <head>, <body>, <script>, or <link> tags — only the inner body content.
- The layout MUST include ALL four sentinel comments exactly as shown — they will be replaced at generation time:
    <!-- %NAV% -->      navigation links (already rendered as <a> tags)
    <!-- %TITLE% -->    current page title text
    <!-- %CONTENT% -->  the main page content (table / form / etc.)
    <!-- %ACTIONS% -->  action buttons (create, save, etc.)
- Use the provided colors to make the design consistent.
- The design should be production-quality, not a rough sketch.

Colors:
  Background: {data[background_color]}
  Text:       {data[text_color]}
  Accent:     {data[accent_color]}
  Radius:     {data[radius]}px

Designer description:
"{data[prompt]}"

Output the HTML now:
"""


PROSE_GENERATE_METADATA = """
You translate human requirements into UML classes and relationships.
Attribute types: int | str | bool.

Output a single JSON object wrapped in METADATA_START / METADATA_END markers:

METADATA_START
{{"classes": [...], "relationships": [...]}}
METADATA_END

Rules:
- Output only the JSON between the markers. No extra text.
- If the request is out of scope, output an empty classes and relationships arrays.

Handle the following request:
'{data[requirements]}'
"""


PROSE_GENERATE_PAGES = """
Generate UI page definitions following OOUI principles (users interact with objects).

For each page:
- Bind it to a specific class
- Specify which attributes to display
- Specify which CRUD operations are available

Output a single JSON object wrapped in PAGES_START / PAGES_END markers:

PAGES_START
{{"pages": [...]}}
PAGES_END

Rules:
- class_name MUST exactly match one of the provided classes.
- operations: any subset of ["create","update","delete"].
- attributes: any subset of the class's attributes.
- Output only the JSON between the markers. No extra text.

Available classes:
{data[classes]}

Generate pages for the following requirements:
'{data[requirements]}'
"""


PROSE_GENERATE_INTERFACE_CANDIDATES = """
You are an OOUI interface designer. Generate EXACTLY 3 visually distinct candidates for actor "{data[actor_name]}".

RULES:
- User-specified styling/layout constraints MUST apply to ALL 3 candidates. Only vary what is unspecified.
- Layouts: sidebar | topnav | dashboard | split | wizard | minimal
- Styles: modern | basic | abstract
- Every class the actor interacts with needs a page_override entry.
- "attributes": fields this actor can EDIT. "readonly_attributes": fields this actor can VIEW only. Never put the same field in both.
- Derived/system fields (id, timestamps, auto-counts) go in "readonly_attributes" or are omitted — never editable.
- Identify actor role from use cases: Submit/Apply → requester (owns input fields, no status/decision fields); Review/Approve → decision-maker (owns status/decision fields, reads input); Admin → full access.
- Set "hidden": true for classes the actor never interacts with.

CTA GATING (OOUX):
- "create_action_node" / "update_action_node" / "delete_action_node": name of the activity action node that must be active for this CTA to appear. null = always visible.
- Match names exactly to the Activity workflows listed below.

Output format — repeat for CANDIDATE_2 and CANDIDATE_3:

CANDIDATE_1_START
{{
  "style": "Descriptive Name",
  "styling": {{
    "radius": <0-20>,
    "textColor": "#hexcolor",
    "accentColor": "#hexcolor",
    "backgroundColor": "#hexcolor",
    "selectedStyle": "<modern|basic|abstract>",
    "layoutType": "<sidebar|topnav|dashboard|split|wizard|minimal|cards|tabs|drawer|custom>",
    "customHtml": "<full body HTML using <!-- %NAV% --> <!-- %TITLE% --> <!-- %CONTENT% --> <!-- %ACTIONS% --> sentinels, or empty string if not custom layout>",
    "fontUrl": "<Google Fonts URL or empty string>",
    "customCss": "<any extra CSS rules, or empty string>"
  }},
  "page_overrides": [
    {{
      "class_name": "ClassName",
      "page_name": "Page Name",
      "category": "Category",
      "operations": ["create", "update"],
      "attributes": ["editable_attr"],
      "readonly_attributes": ["viewonly_attr"],
      "create_action_node": null,
      "update_action_node": null,
      "delete_action_node": null,
      "hidden": false
    }}
  ]
}}
CANDIDATE_1_END

Classes ({data[actor_name]} interacts with):
{data[classes]}

Relationships:
{data[relationships]}

Use cases:
{data[use_cases]}

Activity workflows:
{data[activities]}

Designer requirements:
'{data[requirements]}'
"""


PROSE_REFINE_INTERFACE = """
You are refining an existing UI for actor "{data[actor_name]}" based on user feedback. Only change what was requested; keep everything else identical.

Models: {data[classes]}
Relationships: {data[relationships]}
Use cases: {data[use_cases]}
Activity workflows: {data[activities]}

Current styling: {data[current_styling]}
Current pages: {data[current_pages]}
Current additional pages: {data[current_additional_pages]}

Refinement request: '{data[refinement_prompt]}'

Rules:
- "attributes": editable fields. "readonly_attributes": view-only fields. Never both.
- CTA gates: set create_action_node/update_action_node/delete_action_node to the exact activity action name, or null.
- If only styling changed, omit page_overrides. If only pages changed, keep styling values.

Output the complete refined interface:

REFINED_START
{{
  "style": "Descriptive Name",
  "styling": {{
    "radius": <0-20>,
    "textColor": "#hexcolor",
    "accentColor": "#hexcolor",
    "backgroundColor": "#hexcolor",
    "selectedStyle": "<modern|basic|abstract>",
    "layoutType": "<sidebar|topnav|dashboard|split|wizard|minimal|cards|tabs|drawer|custom>",
    "customHtml": "<full body HTML using <!-- %NAV% --> <!-- %TITLE% --> <!-- %CONTENT% --> <!-- %ACTIONS% --> sentinels, or empty string if not custom layout>",
    "fontUrl": "<Google Fonts URL or empty string>",
    "customCss": "<any extra CSS rules, or empty string>"
  }},
  "page_overrides": [
    {{
      "class_name": "ExactModelName",
      "page_name": "Custom Name",
      "category": "Category",
      "operations": ["create", "update"],
      "attributes": ["editable_attr"],
      "readonly_attributes": ["viewonly_attr"],
      "create_action_node": null,
      "update_action_node": null,
      "delete_action_node": null,
      "hidden": false
    }}
  ],
  "additional_pages": [
    {{
      "page_name": "Dashboard",
      "category": "Home",
      "page_type": "dashboard",
      "description": "Overview page"
    }}
  ]
}}
REFINED_END

page_overrides and additional_pages are optional — omit if unchanged.
"""