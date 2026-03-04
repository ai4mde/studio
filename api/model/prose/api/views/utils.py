
import re
import csv
from io import StringIO
from uuid import uuid4

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


import json


def parse_interface_candidates(response: str, classifiers: list):
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
                json_str = match.group(1).strip()
                candidate_data = json.loads(json_str)
                
                # Convert candidate to Interface.data format
                interface_data = _convert_candidate_to_interface(candidate_data, classifiers)
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


def _convert_candidate_to_interface(candidate_data: dict, classifiers: list):
    """
    Convert LLM candidate output to proper Interface.data structure.
    
    OOUI + Override approach:
    1. By default, generate CRUD pages for ALL Models
    2. Apply page_overrides to customize (rename, hide, filter attrs/ops)
    """
    # Build class lookup
    class_lookup = {}
    for cls in classifiers:
        name = cls.get('data', {}).get('name', '')
        if name:
            class_lookup[name] = cls
            class_lookup[name.lower()] = cls
    
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
    
    # Build override lookup from page_overrides
    overrides = {}
    for override in candidate_data.get('page_overrides', []):
        cls_name = override.get('class_name', '')
        if cls_name:
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
        
        # Build attributes
        attributes = []
        cls_attrs = cls.get('data', {}).get('attributes', [])
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
    
    # Handle additional_pages (non-CRUD pages like dashboard, reports, settings)
    for extra_page in candidate_data.get('additional_pages', []):
        try:
            extra_page_name = extra_page.get('page_name', '')
            extra_category = extra_page.get('category', 'Extra')
            page_type = extra_page.get('page_type', 'custom')
            description = extra_page.get('description', '')
            related_models = extra_page.get('related_models', [])
            
            if not extra_page_name:
                continue
            
            # Handle category
            if extra_category and extra_category not in categories_seen:
                cat_id = str(uuid4())
                categories_seen[extra_category] = {
                    "id": cat_id,
                    "name": extra_category,
                }
            
            # Create a placeholder section for this extra page
            section_id = str(uuid4())
            section = {
                "id": section_id,
                "name": extra_page_name,
                "text": description,
                "class": None,
                "model_name": None,
                "page_type": page_type,
                "related_models": related_models,
                "attributes": [],
                "operations": {"create": False, "update": False, "delete": False},
            }
            sections.append(section)
            
            # Create page
            page_id = str(uuid4())
            page = {
                "id": page_id,
                "name": extra_page_name,
                "type": {"label": page_type.capitalize(), "value": page_type},
                "action": None,
                "category": {
                    "label": extra_category,
                    "value": categories_seen.get(extra_category, {"id": str(uuid4()), "name": extra_category}),
                },
                "sections": [
                    {
                        "label": extra_page_name,
                        "value": section_id,
                    }
                ],
            }
            pages.append(page)
        except Exception as e:
            print(f"[convert_candidate] Error adding extra page: {e}")
    
    if not sections:
        return None
    
    return {
        "sections": sections,
        "pages": pages,
        "categories": list(categories_seen.values()),
        "styling": styling,
        "settings": {"managerAccess": False},
    }


def parse_refined_interface(response: str, classifiers: list):
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
        print("[parse_refined] No REFINED or CANDIDATE block found")
        return None
    
    try:
        json_str = match.group(1).strip()
        refined_data = json.loads(json_str)
        return _convert_candidate_to_interface(refined_data, classifiers)
    except json.JSONDecodeError as e:
        print(f"[parse_refined] JSON error: {e}")
        return None
    except Exception as e:
        print(f"[parse_refined] Error: {e}")
        return None