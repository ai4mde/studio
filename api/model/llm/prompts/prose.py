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

═══════════════════════════════════════════════════════════════════════════════
TARGET ACTOR: {data[actor_name]}
═══════════════════════════════════════════════════════════════════════════════
You are generating an interface SPECIFICALLY for the actor "{data[actor_name]}".
This actor can ONLY see and edit data that belongs to their use cases.
Other actors' data MUST be hidden or read-only.

OOUI Baseline: By default, EVERY Model gets a CRUD page with ALL attributes.
Your job is to:
1. Design the visual STYLING and LAYOUT
2. CRITICALLY: Filter attributes based on WHO OWNS them (see ATTRIBUTE OWNERSHIP below)
3. Customize Model pages (rename, regroup, hide attributes, change operations)

MANDATORY OOUI RULES (always apply, regardless of designer requirements):

COMPOSITION GROUPING:
- Classes linked by COMPOSITION MUST be grouped together (parent + children in same category)

USE CASE GROUPING:
- Use cases tell you which classes an actor interacts with -> group those classes in the same category
- Use case pre/postconditions hint at the workflow flow

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
      "operations": ["create", "update"],
      "attributes": ["editable_attr1", "editable_attr2"],
      "readonly_attributes": ["viewonly_attr1", "viewonly_attr2"],
      "hidden": false
    }}
  ]
}}
CANDIDATE_1_END

PAGE OVERRIDE RULES:
- "page_overrides" is REQUIRED for EVERY class this actor interacts with.
- Set "hidden": true ONLY for classes the actor should NOT see at all (unrelated classes).
- "attributes": list ONLY the attrs this actor can EDIT (editable fields).
- "readonly_attributes": list attrs this actor can VIEW but NOT EDIT.
- IMPORTANT: An attribute should appear in EITHER "attributes" OR "readonly_attributes", NOT both.
- IMPORTANT: For classes this actor interacts with, include ALL relevant attributes - either as editable OR readonly.
- DO NOT exclude attributes that the actor needs to see - put them in "readonly_attributes" instead.

═══════════════════════════════════════════════════════════════════════════════
ATTRIBUTE OWNERSHIP ANALYSIS (CRITICAL — MUST follow these rules precisely):
═══════════════════════════════════════════════════════════════════════════════

BEFORE generating, you MUST analyze each class's attributes and decide ownership:

STEP 0: Identify the target actor's ROLE from their use cases:
  - "Submit", "Apply", "Request", "Fill", "Enter" → This actor is a REQUESTER/APPLICANT
  - "Review", "Approve", "Reject", "Decide", "Process" → This actor is a DECISION-MAKER
  - "Manage", "Configure", "Admin" → This actor is an ADMINISTRATOR
  - "View", "Check", "Monitor", "Analyze" → This actor is a VIEWER/ANALYST

STEP 1: Categorize every attribute into ONE of these types:

  TYPE A - SYSTEM-MANAGED (NEVER editable by any actor):
    - id, uuid, created_at, updated_at, timestamps
    - auto-calculated totals, counts, derived values (marked as "derived" in class)
    - audit fields (created_by, modified_by)
    → Rule: EXCLUDE from "attributes", may include in "readonly_attributes" if viewing needed

  TYPE B - OWNER-CONTROLLED (only ONE actor creates/edits):
    - Look at use case: WHO performs the action that SETS this value?
    - Common patterns:
      * If use case is "Submit X" or "Apply for X" → actor owns INPUT fields (name, amount, description, etc.)
      * If use case is "Approve X" or "Review X" → actor owns DECISION fields (status, approved_amount, notes)
    → Rule: ONLY the owner actor gets this in "attributes" with appropriate operations
             Other actors: EXCLUDE or put in "readonly_attributes"

  TYPE C - STATUS/DECISION FIELDS (set by decision-makers):
    - Attributes with names like: status, state, result, decision, approved, rejected, rating, score
    - Usually set by: Admin, Manager, Officer, Reviewer, Approver roles
    → Rule: EXCLUDE for applicants/requesters. Include ONLY for decision actors.

  TYPE D - SHARED REFERENCE (read-only for most):
    - Reference data like name, description for linked objects
    - Foreign key display fields
    → Rule: Put in "readonly_attributes" for viewing, NOT in "attributes"

STEP 2: For EACH use case the actor has, identify:
  - What data does this use case CREATE? → actor owns those attributes (put in "attributes")
  - What data does this use case READ? → put in "readonly_attributes"
  - What data does this use case UPDATE? → check if actor is the owner
  - What data does this use case DECIDE? → status/decision fields belong here

STEP 3: Apply strict filtering:
  ✗ WRONG: Giving Applicant access to edit "status" or "decision" fields
  ✗ WRONG: Giving Reviewer ability to "create" when they only "review"
  ✗ WRONG: Showing all attributes when actor only needs 2-3 fields
  ✓ CORRECT: Applicant creates/updates ONLY their own data fields
  ✓ CORRECT: Reviewer gets "update" only for decision fields, rest readonly
  ✓ CORRECT: Operator views many fields but edits only process-related ones

EXAMPLE - Loan System:
  LoanApplication class has: [applicant_name, loan_amount, purpose, status, officer_notes, approved_amount]
  
  For Applicant interface:
    "attributes": ["applicant_name", "loan_amount", "purpose"],  // owns these
    "readonly_attributes": ["status"],  // can see but not change
    "operations": ["create", "update"]
    // officer_notes, approved_amount: EXCLUDED - not their data
  
  For Loan Officer interface:
    "attributes": ["status", "officer_notes", "approved_amount"],  // decides these
    "readonly_attributes": ["applicant_name", "loan_amount", "purpose"],  // reviews
    "operations": ["update"]  // no create - applicant creates
    
  For Admin interface:
    "attributes": ["status"],  // can override
    "readonly_attributes": ["applicant_name", "loan_amount", "purpose", "officer_notes", "approved_amount"],
    "operations": ["update", "delete"]

═══════════════════════════════════════════════════════════════════════════════
ACTIVITY PAGE FILTERING:
═══════════════════════════════════════════════════════════════════════════════
- Activity pages auto-generate from activity diagrams.
- Use "activity_attributes" and "activity_operations" to filter what shows in workflow tasks.
- Match the activity action type:
  - "Fill in" / "Submit" / "Enter" → ["create", "update"] + input fields only
  - "Review" / "Decide" / "Approve" / "Reject" → ["update"] + decision fields only
  - "View" / "Check" / "Verify" → [] (read-only) + relevant display fields

NOTE: Activity workflow pages are automatically generated by the system based on UML activity diagrams.
You do NOT need to create activity pages. Focus only on styling, layout, and Model page customization.

Make each candidate VISUALLY DISTINCT!

═══════════════════════════════════════════════════════════════════════════════
GENERATING INTERFACE FOR ACTOR: {data[actor_name]}
═══════════════════════════════════════════════════════════════════════════════

Available classes (format: attr_name:type, derived attrs marked):
{data[classes]}

Class relationships:
{data[relationships]}

This actor's use cases (CRITICAL - determines attribute ownership):
{data[use_cases]}

Activity workflows for this actor:
{data[activities]}

Designer requirements:
'{data[requirements]}'

FINAL CHECKLIST before generating each candidate:
□ Did I identify what ROLE this actor has? (requester/decision-maker/admin/viewer)
□ For each class, did I put ONLY this actor's owned attributes in "attributes"?
□ Did I put OTHER actors' attributes in "readonly_attributes" or exclude them?
□ Did I exclude system/derived fields from editable attributes?
□ Do the operations match the actor's role? (requesters create, reviewers only update)
"""


PROSE_REFINE_INTERFACE = """
You are refining an existing UI based on user feedback.
Only change what the user requested. Keep everything else the same.

Available Models (class_name -> attributes):
{data[classes]}

Current styling:
{data[current_styling]}

Current pages:
{data[current_pages]}

Current additional pages:
{data[current_additional_pages]}

User's refinement request:
'{data[refinement_prompt]}'

IMPORTANT:
- Only modify what the user asked for. Keep unchanged parts exactly the same.
- class_name in page_overrides MUST match one of the Available Models above EXACTLY.
- If user only changes styling, omit page_overrides and additional_pages.
- If user only changes pages, keep the same styling values.
- Use "attributes" for editable fields and "readonly_attributes" for view-only fields.

Output the COMPLETE refined interface in JSON format:

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
      "attributes": ["editable_attr1", "editable_attr2"],
      "readonly_attributes": ["viewonly_attr1", "viewonly_attr2"],
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

page_overrides and additional_pages are optional - omit if unchanged.
"""