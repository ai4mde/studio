PROSE_GENERATE_METADATA = """
Act like an API endpoint that translates human language to UML classes.
Each class has a name and attributes (of type int/str/bool).
Also, classes can have relationships to each other (0 to any, 1 to 1, etc.)
You will receive a request that contains human-written text with system requirements.
You will answer each request with 2 csv lists.
Use the terms 'START' AND 'END' in the first and last line of the list such that the data can be extracted easily.
The first list contains the classes and their attributes, e.g.:

START
"class_name","attributes"
"Product","[str:name, int:price, bool:available]"
"Customer","[str:first_name, str:last_name]"
"Airline","[str:name, str:country]"
END

The second lists contains the relationships. (Source, target, source multiplicity, target multiplicity) For example:

START
"source_class_name","target_class_name","source_multiplicity","target_multiplicity"
"Product","Customer","1","*"
"Customer","Airline", "*", "1"
END

Adhere to this formatting in your response. Only show the .csv lists in your output. If requests are made that are out of scope, return an error.

Handle the following request:
'{data[requirements]}'
"""


PROSE_GENERATE_PAGES = """
Act like an API endpoint that generates UI page definitions based on OOUI (Object-Oriented User Interface) principles.

You will receive:
1. A list of classes with their attributes
2. Human-written requirements describing what UI pages/screens are needed

For each page, you must:
- Bind it to a specific Class (OOUI principle: users interact with objects)
- Specify which attributes to display
- Specify which CRUD operations are available (create/update/delete)

Output a CSV list with the following format:

START
"page_name","category","class_name","operations","attributes"
"Product List","Products","Product","[create,update,delete]","[name,price,available]"
"Customer Overview","Customers","Customer","[create,update]","[first_name,last_name]"
"Order Management","Orders","Order","[create,update,delete]","[order_date,status,total]"
END

Rules:
- page_name: descriptive name for the page
- category: navigation category (group related pages)
- class_name: MUST match one of the provided classes exactly
- operations: subset of [create,update,delete]
- attributes: subset of the class's attributes

Only output the CSV list between START and END markers.
If the request is unclear, make reasonable assumptions based on typical CRUD applications.

Available classes:
{data[classes]}

Generate pages for the following requirements:
'{data[requirements]}'
"""


PROSE_GENERATE_INTERFACE_CANDIDATES = """
You are an AI UI Designer for Model-Driven Engineering (MDE) with OOUI principles.

OOUI Baseline: By default, EVERY Model gets a CRUD page with ALL attributes.
Your job is to:
1. Design the visual STYLING and LAYOUT
2. OPTIONALLY customize Model pages (rename, regroup, hide attributes, change operations)
3. OPTIONALLY add EXTRA pages (dashboard, reports, settings, etc.)

You will receive UML Models. Generate EXACTLY 3 candidates.

CRITICAL RULE - Follow User Requirements:
- Whatever the user SPECIFIES, ALL 3 candidates MUST follow exactly!
- Only the parts NOT specified by the user can differ between candidates.

Examples:
- User says "brown color" → ALL 3 use brown (vary layout, style, radius)
- User says "sidebar layout" → ALL 3 use sidebar (vary colors, style)
- User says "modern style, dark theme" → ALL 3 are modern + dark (vary layout, radius)
- User says nothing specific → ALL 3 can be completely different

LAYOUT OPTIONS:
- "sidebar" - Left sidebar navigation (best for many models)
- "topnav" - Horizontal top navigation (clean, professional)
- "dashboard" - Widget/card grid (data-heavy apps)
- "split" - Two-panel master-detail
- "wizard" - Step-by-step workflow
- "minimal" - Single page with tabs

COLOR REFERENCE (only use if NO color preference specified):
- Light professional (blues, grays)
- Dark mode (dark bg, bright accents)
- Warm tones (oranges, browns)
- Cool tones (teals, purples)
- High contrast (black/white)
- Nature (greens, earth tones)
- Vibrant (bright pinks, yellows)

STYLE VARIATIONS:
- "modern" (rounded, shadows, cards)
- "basic" (sharp edges, simple)
- "abstract" (geometric, artistic)

Output format with CANDIDATE markers:

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
      "page_name": "Custom Page Name",
      "category": "Category Name",
      "operations": ["create", "update", "delete"],
      "attributes": ["attr1", "attr2"],
      "hidden": false
    }}
  ],
  "additional_pages": [
    {{
      "page_name": "Dashboard",
      "category": "Home",
      "page_type": "dashboard",
      "description": "Overview with key metrics"
    }},
    {{
      "page_name": "Reports",
      "category": "Analytics",
      "page_type": "report",
      "related_models": ["Order", "Product"]
    }}
  ]
}}
CANDIDATE_1_END

PAGE OVERRIDE RULES:
- "page_overrides" is OPTIONAL. If omitted, all Models get default CRUD pages.
- Only include classes you want to CUSTOMIZE (rename, hide attrs, change ops).
- Set "hidden": true to EXCLUDE a Model from the UI.
- "attributes": list only the attrs to SHOW (omit = show all).
- Models NOT in page_overrides get full CRUD with all attributes.

ADDITIONAL PAGES:
- "additional_pages" is OPTIONAL. Use it to add non-CRUD pages.
- page_type options: "dashboard", "report", "settings", "profile", "search", "custom"
- "related_models": list of Models this page displays data from (for context)
- These pages are in addition to auto-generated Model pages.

Make each candidate VISUALLY DISTINCT!

Available classes:
{data[classes]}

Available use cases:
{data[use_cases]}

Activity workflows:
{data[activities]}

Designer requirements:
'{data[requirements]}'
"""


PROSE_REFINE_INTERFACE = """
You are refining an existing UI based on user feedback.

Current Interface:
{data[current_interface]}

User's refinement request:
'{data[refinement_prompt]}'

You can modify:
1. Styling (colors, layout, radius, style)
2. Page overrides (rename, hide, change attributes/operations for Model pages)
3. Additional pages (add/remove dashboard, reports, settings, etc.)

Output the refined interface in JSON format:

REFINED_START
{{
  "style": "...",
  "styling": {{
    "radius": <number>,
    "textColor": "#hexcolor",
    "accentColor": "#hexcolor",
    "backgroundColor": "#hexcolor",
    "selectedStyle": "<modern|basic|abstract>",
    "layoutType": "<sidebar|topnav|dashboard|split|wizard|minimal>"
  }},
  "page_overrides": [
    {{
      "class_name": "ClassName",
      "page_name": "Custom Name",
      "category": "Category",
      "operations": ["create", "update", "delete"],
      "attributes": ["attr1", "attr2"],
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

Only make the changes requested. page_overrides and additional_pages are optional.
"""