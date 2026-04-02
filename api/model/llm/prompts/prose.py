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
    "layoutType": "<sidebar|topnav|dashboard|split|wizard|minimal>"
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
    "layoutType": "<sidebar|topnav|dashboard|split|wizard|minimal>"
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