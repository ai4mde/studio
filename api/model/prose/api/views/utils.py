
import re
import csv
import json
from io import StringIO
from uuid import uuid4


def _strip_markdown_json(text: str) -> str:
    """Strip markdown code fences from JSON text.
    LLMs often wrap JSON in ```json ... ``` blocks."""
    text = text.strip()
    # Remove ```json or ``` at start
    text = re.sub(r'^```(?:json)?\s*', '', text)
    # Remove ``` at end
    text = re.sub(r'```\s*$', '', text)
    return text.strip()

def parse_relations(csv_table, classifiers):
    relations = []
    reader = csv.DictReader(StringIO(csv_table))
    for row in reader:
        try:
            source_name = row['source_class_name']
            target_name = row['target_class_name']
            source_mult = row['source_multiplicity']
            target_mult = row['target_multiplicity']
            rel = {}
            rel['id'] = uuid4().hex
            print(rel)
            for cls in classifiers:
                if cls['data']['name'] == source_name:
                    rel['source'] = cls['id']
                if cls['data']['name'] == target_name:
                    rel['target'] = cls['id']
            rel['data'] = {"type": "association", "multiplicity": {"source": source_mult, "target": target_mult}, "derived": False, "label": " "}
            relations.append(rel)
            print(rel)
        except:
            pass
    return relations


def parse_classifiers(csv_table):
    classifiers = []
    reader = csv.DictReader(StringIO(csv_table))
    
    for row in reader:
        try:
            attributes = []
            attr_str = row['attributes'].strip('[]')
            if attr_str:
                for attr in attr_str.split(','):
                    type_name, attr_name = attr.strip().split(':')
                    attributes.append({
                        "name": attr_name.strip(),
                        "type": type_name.strip(),
                        "enum": None,
                        "derived": False,
                        "description": None,
                        "body": None
                    })
            data = {
                'name': row['class_name'],
                'type': 'class',
                "attributes": attributes,
            }
            cls = {
                'id': uuid4().hex,
                'data': data,
            }
            classifiers.append(cls)
        except:
            pass
    return classifiers



def parse_llm_response(response: str):
    tables = re.findall(r'START\n(.*?)\nEND', response, re.DOTALL)
    if len(tables) != 2:
        return
    classifiers_csv_table = tables[0]
    relations_csv_table = tables[1]
    classifiers = parse_classifiers(classifiers_csv_table)
    relations = parse_relations(relations_csv_table, classifiers)
    output = {
        "classifiers": classifiers,
        "relations": relations
    }
    return output


def parse_pages_response(response: str, classifiers: list):
    """
    Parse LLM response for page generation.
    
    Expected CSV format:
    "page_name","category","class_name","operations","attributes"
    
    Returns Interface.data structure with sections, pages, categories, styling.
    """
    tables = re.findall(r'START\n(.*?)\nEND', response, re.DOTALL)
    if len(tables) < 1:
        return None

    pages_csv = tables[0].strip()
    
    # Check if header row exists, if not add it
    lines = pages_csv.split('\n')
    if lines and 'page_name' not in lines[0].lower():
        # No header detected, add one
        pages_csv = '"page_name","category","class_name","operations","attributes"\n' + pages_csv
    
    reader = csv.DictReader(StringIO(pages_csv))

    sections = []
    pages = []
    categories_seen = {}

    # Build lookup: class name -> classifier (both exact and lowercase)
    class_lookup = {}
    for cls in classifiers:
        name = cls.get('data', {}).get('name', '')
        if name:
            class_lookup[name] = cls  # Exact match
            class_lookup[name.lower()] = cls  # Lowercase match

    for row in reader:
        try:
            page_name = row.get('page_name', '').strip().strip('"')
            category_name = row.get('category', '').strip().strip('"')
            class_name = row.get('class_name', '').strip().strip('"')
            ops_str = row.get('operations', '[]').strip().strip('"').strip('[]')
            attrs_str = row.get('attributes', '[]').strip().strip('"').strip('[]')
            
            # Skip empty rows
            if not page_name or not class_name:
                continue

            # Find the matching class (try exact, then lowercase)
            cls = class_lookup.get(class_name) or class_lookup.get(class_name.lower())
            if not cls:
                print(f"[parse_pages] Warning: class '{class_name}' not found in classifiers")
                continue
            class_id = str(cls['id'])

            # Parse operations
            ops_list = [op.strip().lower() for op in ops_str.split(',') if op.strip()]
            operations = {
                "create": "create" in ops_list,
                "update": "update" in ops_list,
                "delete": "delete" in ops_list,
            }

            # Parse attributes
            attrs_list = [a.strip() for a in attrs_str.split(',') if a.strip()]
            attributes = []
            if cls and 'attributes' in cls.get('data', {}):
                for attr in cls['data']['attributes']:
                    if attr['name'] in attrs_list:
                        attributes.append({
                            "name": attr['name'],
                            "type": attr.get('type', 'str'),
                            "derived": attr.get('derived', False),
                            "enum": attr.get('enum'),
                            "body": attr.get('body'),
                            "description": attr.get('description'),
                        })

            # Create section (OOUI: binds to a Class)
            section_id = str(uuid4())
            section = {
                "id": section_id,
                "name": page_name,
                "text": "",
                "class": class_id,
                "model_name": class_name,
                "attributes": attributes,
                "operations": operations,
            }
            sections.append(section)

            # Handle category
            if category_name and category_name not in categories_seen:
                cat_id = str(uuid4())
                categories_seen[category_name] = {
                    "id": cat_id,
                    "name": category_name,
                }

            # Create page
            page_id = str(uuid4())
            page = {
                "id": page_id,
                "name": page_name,
                "type": {"label": "Normal", "value": "normal"},
                "action": None,
                "category": {
                    "label": category_name,
                    "value": {
                        "id": categories_seen.get(category_name, {}).get("id", str(uuid4())),
                        "name": category_name,
                    }
                },
                "sections": [
                    {
                        "label": page_name,
                        "value": section_id,
                    }
                ],
            }
            pages.append(page)
            print(f"[parse_pages] Parsed: {page_name} -> {class_name}")

        except Exception as e:
            print(f"[parse_pages] Error parsing row: {e}")
            pass

    print(f"[parse_pages] Total parsed: {len(sections)} sections, {len(pages)} pages")
    # Default styling
    styling = {
        "radius": 0,
        "textColor": "#000000",
        "accentColor": "#F5F5F4",
        "selectedStyle": "modern",
        "backgroundColor": "#FFFFFF",
    }

    return {
        "sections": sections,
        "pages": pages,
        "categories": list(categories_seen.values()),
        "styling": styling,
        "settings": {"managerAccess": False},
    }


def parse_interface_candidates(response: str, classifiers: list, composition_groups: dict = None, activity_actions: list = None):
    """
    Parse LLM response containing multiple UI candidates.
    
    Expected format:
    CANDIDATE_1_START
    {...json...}
    CANDIDATE_1_END
    
    Returns list of Interface.data candidates (2-3 items).
    """
    candidates = []
    
    # Extract all candidate blocks
    for i in range(1, 4):  # Up to 3 candidates
        pattern = rf'CANDIDATE_{i}_START\s*(.*?)\s*CANDIDATE_{i}_END'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            try:
                json_str = _strip_markdown_json(match.group(1))
                candidate_data = json.loads(json_str)
                
                # Convert candidate to Interface.data format
                interface_data = _convert_candidate_to_interface(
                    candidate_data, classifiers,
                    composition_groups=composition_groups or {},
                    activity_actions=activity_actions or [],
                )
                if interface_data:
                    interface_data['candidate_index'] = i
                    interface_data['style_name'] = candidate_data.get('style', f'style_{i}')
                    candidates.append(interface_data)
            except json.JSONDecodeError as e:
                print(f"[parse_candidates] JSON error in candidate {i}: {e}")
            except Exception as e:
                print(f"[parse_candidates] Error parsing candidate {i}: {e}")
    
    print(f"[parse_candidates] Parsed {len(candidates)} candidates")
    return candidates


def _convert_candidate_to_interface(candidate_data: dict, classifiers: list, composition_groups: dict = None, activity_actions: list = None):
    """
    Convert LLM candidate output to proper Interface.data structure.
    
    OOUI + Override approach:
    1. By default, generate CRUD pages for ALL Models
    2. Apply page_overrides to customize (rename, hide, filter attrs/ops)
    3. Group composed classes under same category (OOUI principle)
    4. Support activity page type for workflow UI tasks
    5. Validate all references (class names, activity names)
    """
    composition_groups = composition_groups or {}
    activity_actions = activity_actions or []
    
    # Build class lookup
    class_lookup = {}
    valid_class_names = set()
    for cls in classifiers:
        name = cls.get('data', {}).get('name', '')
        if name:
            class_lookup[name] = cls
            class_lookup[name.lower()] = cls
            valid_class_names.add(name)
    
    # Determine composition-based category grouping
    # If Parent --[composition]--> Child, both should be in same category
    composition_category = {}  # class_name -> category_name from parent
    for parent, children in composition_groups.items():
        for child in children:
            composition_category[child] = parent  # child grouped under parent's name
    
    sections = []
    pages = []
    categories_seen = {}
    
    # Valid styles and layouts
    VALID_STYLES = ["basic", "abstract", "modern"]
    VALID_LAYOUTS = ["sidebar", "topnav", "dashboard", "split", "wizard", "minimal"]
    
    raw_styling = candidate_data.get('styling', {})
    selected_style = raw_styling.get('selectedStyle', 'modern')
    layout_type = raw_styling.get('layoutType', 'sidebar')
    
    # Normalize selectedStyle to valid value
    if selected_style not in VALID_STYLES:
        selected_style = 'modern'
    
    # Normalize layoutType to valid value
    if layout_type not in VALID_LAYOUTS:
        layout_type = 'sidebar'
    
    styling = {
        "radius": raw_styling.get('radius', 0),
        "textColor": raw_styling.get('textColor', '#000000'),
        "accentColor": raw_styling.get('accentColor', '#F5F5F4'),
        "selectedStyle": selected_style,
        "backgroundColor": raw_styling.get('backgroundColor', '#FFFFFF'),
        "layoutType": layout_type,
    }
    
    # Build override lookup from page_overrides (with validation)
    overrides = {}
    for override in candidate_data.get('page_overrides', []):
        cls_name = override.get('class_name', '')
        if cls_name:
            # Validation: check class_name exists
            if cls_name not in valid_class_names and cls_name.lower() not in class_lookup:
                print(f"[validation] WARNING: page_override class_name '{cls_name}' not found in models, skipping")
                continue
            overrides[cls_name] = override
            overrides[cls_name.lower()] = override
    
    # Also support legacy 'pages' format
    for page in candidate_data.get('pages', []):
        cls_name = page.get('class_name', '')
        if cls_name and cls_name not in overrides:
            overrides[cls_name] = page
            overrides[cls_name.lower()] = page
    
    # OOUI: Generate pages for ALL Models, applying overrides
    for cls in classifiers:
        cls_name = cls.get('data', {}).get('name', '')
        if not cls_name:
            continue
        
        # Check for override
        override = overrides.get(cls_name) or overrides.get(cls_name.lower())
        
        # Skip if hidden
        if override and override.get('hidden', False):
            continue
        
        # Get page settings (override or default)
        if override:
            page_name = override.get('page_name') or override.get('name') or cls_name
            category_name = override.get('category', 'Models')
            ops_list = override.get('operations', ['create', 'update', 'delete'])
            attrs_filter = override.get('attributes', None)  # None = show all
        else:
            page_name = cls_name
            # OOUI: Use composition grouping for category if available
            if cls_name in composition_category:
                category_name = composition_category[cls_name]
            elif cls_name in composition_groups:
                category_name = cls_name  # Parent class = its own category
            else:
                category_name = 'Models'
            ops_list = ['create', 'update', 'delete']
            attrs_filter = None
        
        class_id = str(cls['id'])
        
        # Build operations
        operations = {
            "create": "create" in ops_list,
            "update": "update" in ops_list,
            "delete": "delete" in ops_list,
        }
        
        # Build attributes (with validation)
        attributes = []
        cls_attrs = cls.get('data', {}).get('attributes', [])
        valid_attr_names = {attr['name'] for attr in cls_attrs}
        
        # Validate attrs_filter against actual class attributes
        if attrs_filter is not None:
            invalid_attrs = [a for a in attrs_filter if a not in valid_attr_names]
            if invalid_attrs:
                print(f"[validation] WARNING: attrs {invalid_attrs} not found in class '{cls_name}', ignoring them")
            attrs_filter = [a for a in attrs_filter if a in valid_attr_names]
            # If all attrs were invalid, show all
            if not attrs_filter:
                attrs_filter = None
        
        for attr in cls_attrs:
            # If attrs_filter is specified, only include those attrs
            if attrs_filter is None or attr['name'] in attrs_filter:
                attributes.append({
                    "name": attr['name'],
                    "type": attr.get('type', 'str'),
                    "derived": attr.get('derived', False),
                    "enum": attr.get('enum'),
                    "body": attr.get('body'),
                    "description": attr.get('description'),
                })
        
        # Create section
        section_id = str(uuid4())
        section = {
            "id": section_id,
            "name": page_name,
            "text": "",
            "class": class_id,
            "model_name": cls_name,
            "attributes": attributes,
            "operations": operations,
        }
        sections.append(section)
        
        # Handle category
        if category_name and category_name not in categories_seen:
            cat_id = str(uuid4())
            categories_seen[category_name] = {
                "id": cat_id,
                "name": category_name,
            }
        
        # Create page
        page_id = str(uuid4())
        page = {
            "id": page_id,
            "name": page_name,
            "type": {"label": "Normal", "value": "normal"},
            "action": None,
            "category": {
                "label": category_name,
                "value": categories_seen.get(category_name, {"id": str(uuid4()), "name": category_name}),
            },
            "sections": [
                {
                    "label": page_name,
                    "value": section_id,
                }
            ],
        }
        pages.append(page)
    
    # Auto-inject activity pages from activity_actions (not LLM-dependent)
    # Collect activity action names so we can remove conflicting normal pages
    activity_action_names = {a['name'] for a in activity_actions if not a.get('is_automatic')}
    # Remove normal pages whose name matches an activity action (to avoid duplicate URLs)
    conflicting_section_ids = set()
    for page in pages[:]:
        if page.get('type', {}).get('value') == 'normal' and page.get('name') in activity_action_names:
            for sec_ref in page.get('sections', []):
                conflicting_section_ids.add(sec_ref.get('value'))
            pages.remove(page)
    if conflicting_section_ids:
        sections[:] = [s for s in sections if s.get('id') not in conflicting_section_ids]
    
    for action in activity_actions:
        if action.get('is_automatic'):
            continue  # automatic tasks don't need UI pages
        
        action_name = action['name']
        action_id = action['id']
        
        # Determine the primary class for this activity page
        # 1. Use input/output classes if explicitly defined on the action
        activity_class_names = []
        for cls_name in action.get('input_classes', []) + action.get('output_classes', []):
            if cls_name in valid_class_names and cls_name not in activity_class_names:
                activity_class_names.append(cls_name)
        
        # 2. If no explicit classes, infer from action name matching class names
        if not activity_class_names:
            action_lower = action_name.lower().replace('_', ' ')
            action_words = set(action_lower.split())
            # Also add singular forms (strip trailing 's') for plural matching
            action_words_singulars = action_words | {w.rstrip('s') for w in action_words if len(w) > 3}
            for cls_name in valid_class_names:
                # Split CamelCase into words: "LoanApplication" -> ["loan", "application"]
                cls_words = [w.lower() for w in re.findall(r'[A-Z][a-z]*|[a-z]+', cls_name) if len(w) > 2]
                # Match if any class word appears in the action words (including singulars)
                if any(w in action_words_singulars for w in cls_words):
                    activity_class_names.append(cls_name)
        
        # Category: "Activities"
        activity_category = "Activities"
        if activity_category not in categories_seen:
            cat_id = str(uuid4())
            categories_seen[activity_category] = {
                "id": cat_id,
                "name": activity_category,
            }
        
        page_sections_refs = []
        
        if activity_class_names:
            # Create a section per matched class (with CRUD forms)
            for cls_name in activity_class_names:
                cls = class_lookup.get(cls_name)
                if not cls:
                    continue
                class_id = str(cls['id'])
                cls_attrs = cls.get('data', {}).get('attributes', [])

                # Use override's activity_attributes or attributes to filter
                override = overrides.get(cls_name) or overrides.get(cls_name.lower())
                activity_attrs_filter = None
                activity_ops_list = None
                if override:
                    activity_attrs_filter = override.get('activity_attributes') or override.get('attributes')
                    activity_ops_list = override.get('activity_operations') or override.get('operations')
                if activity_attrs_filter:
                    valid_names = {a['name'] for a in cls_attrs}
                    activity_attrs_filter = [a for a in activity_attrs_filter if a in valid_names]
                    if not activity_attrs_filter:
                        activity_attrs_filter = None

                attributes = []
                for attr in cls_attrs:
                    if activity_attrs_filter is None or attr['name'] in activity_attrs_filter:
                        attributes.append({
                            "name": attr['name'],
                            "type": attr.get('type', 'str'),
                            "derived": attr.get('derived', False),
                            "enum": attr.get('enum'),
                            "body": attr.get('body'),
                            "description": attr.get('description'),
                        })
                
                # Build activity operations from override or default
                if activity_ops_list is not None:
                    activity_operations = {
                        "create": "create" in activity_ops_list,
                        "update": "update" in activity_ops_list,
                        "delete": "delete" in activity_ops_list,
                    }
                else:
                    activity_operations = {"create": True, "update": True, "delete": False}

                section_id = str(uuid4())
                section = {
                    "id": section_id,
                    "name": action_name,
                    "text": "",
                    "class": class_id,
                    "model_name": cls_name,
                    "page_type": "activity",
                    "activity_name": action_name,
                    "activity_id": action_id,
                    "attributes": attributes,
                    "operations": activity_operations,
                }
                sections.append(section)
                page_sections_refs.append({
                    "label": action_name,
                    "value": section_id,
                })
        else:
            # No matching class found — create a template-only section
            section_id = str(uuid4())
            section = {
                "id": section_id,
                "name": action_name,
                "text": "",
                "class": None,
                "model_name": None,
                "page_type": "activity",
                "activity_name": action_name,
                "activity_id": action_id,
                "attributes": [],
                "operations": {"create": False, "update": False, "delete": False},
            }
            sections.append(section)
            page_sections_refs.append({
                "label": action_name,
                "value": section_id,
            })
        
        # Create page
        page_id = str(uuid4())
        page = {
            "id": page_id,
            "name": action_name,
            "type": {"label": "Activity", "value": "activity"},
            "action": {"label": action_name, "value": action_id},
            "category": {
                "label": activity_category,
                "value": categories_seen[activity_category],
            },
            "sections": page_sections_refs,
        }
        pages.append(page)
    
    if not sections:
        return None
    
    return {
        "sections": sections,
        "pages": pages,
        "categories": list(categories_seen.values()),
        "styling": styling,
        "settings": {"managerAccess": False},
    }


def parse_refined_interface(response: str, classifiers: list, composition_groups: dict = None, activity_actions: list = None):
    """
    Parse LLM response for refined interface.
    
    Expected format:
    REFINED_START
    {...json...}
    REFINED_END
    
    Also supports fallback to CANDIDATE_N_START format if REFINED format not found.
    """
    # Try REFINED format first
    pattern = r'REFINED_START\s*(.*?)\s*REFINED_END'
    match = re.search(pattern, response, re.DOTALL)
    
    if not match:
        # Fallback: try CANDIDATE_N format (LLM sometimes uses wrong format)
        pattern = r'CANDIDATE_\d+_START\s*(.*?)\s*CANDIDATE_\d+_END'
        match = re.search(pattern, response, re.DOTALL)
    
    if not match:
        # Last resort: try to find any JSON object in the response
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        json_match = re.search(json_pattern, response, re.DOTALL)
        if json_match:
            print("[parse_refined] No markers found, trying raw JSON extraction")
            match = json_match
        
    if not match:
        print("[parse_refined] No REFINED or CANDIDATE block found")
        print(f"[parse_refined] Full response: {response[:500]}")
        return None
    
    try:
        json_str = _strip_markdown_json(match.group(1) if hasattr(match, 'group') and match.lastindex else match.group(0))
        refined_data = json.loads(json_str)
        print(f"[parse_refined] Successfully parsed JSON with keys: {list(refined_data.keys())}")
        return _convert_candidate_to_interface(
            refined_data, classifiers,
            composition_groups=composition_groups or {},
            activity_actions=activity_actions or [],
        )
    except json.JSONDecodeError as e:
        print(f"[parse_refined] JSON error: {e}")
        print(f"[parse_refined] Attempted to parse: {json_str[:300]}")
        return None
    except Exception as e:
        print(f"[parse_refined] Error: {e}")
        return None