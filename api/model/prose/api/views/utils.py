
import re
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


def parse_llm_response(response: str):
    match = re.search(r'METADATA_START\s*(.*?)\s*METADATA_END', response, re.DOTALL)
    if not match:
        return None
    json_text = _strip_markdown_json(match.group(1))
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return None

    classifiers = []
    for cls_item in data.get("classes", []):
        attributes = []
        for attr in cls_item.get("attributes", []):
            attributes.append({
                "name": attr["name"],
                "type": attr.get("type", "str"),
                "enum": None,
                "derived": False,
                "description": None,
                "body": None,
            })
        classifiers.append({
            'id': uuid4().hex,
            'data': {
                'name': cls_item['name'],
                'type': 'class',
                'attributes': attributes,
            },
        })

    cls_by_name = {cls['data']['name']: cls for cls in classifiers}
    relations = []
    for rel_item in data.get("relationships", []):
        source_name = rel_item.get("source", "")
        target_name = rel_item.get("target", "")
        src_cls = cls_by_name.get(source_name)
        tgt_cls = cls_by_name.get(target_name)
        if not src_cls or not tgt_cls:
            continue
        relations.append({
            'id': uuid4().hex,
            'source': src_cls['id'],
            'target': tgt_cls['id'],
            'data': {
                "type": "association",
                "multiplicity": {
                    "source": rel_item.get("source_multiplicity", "*"),
                    "target": rel_item.get("target_multiplicity", "*"),
                },
                "derived": False,
                "label": " ",
            },
        })

    return {"classifiers": classifiers, "relations": relations}


def parse_pages_response(response: str, classifiers: list):
    """
    Parse LLM response for page generation.

    Expected JSON format wrapped in PAGES_START / PAGES_END markers:
    {
      "pages": [
        {"page_name": "...", "category": "...", "class_name": "...",
         "operations": ["create","update"], "attributes": ["name","price"]}
      ]
    }

    Returns Interface.data structure with sections, pages, categories, styling.
    """
    match = re.search(r'PAGES_START\s*(.*?)\s*PAGES_END', response, re.DOTALL)
    if not match:
        return None
    json_text = _strip_markdown_json(match.group(1))
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return None

    class_lookup = {}
    for cls in classifiers:
        name = cls.get('data', {}).get('name', '')
        if name:
            class_lookup[name] = cls
            class_lookup[name.lower()] = cls

    sections = []
    pages = []
    categories_seen = {}

    def parse_row(row, class_lookup, categories_seen):
        page_name = (row.get('page_name') or '').strip()
        category_name = (row.get('category') or '').strip()
        class_name = (row.get('class_name') or '').strip()
        ops_raw = row.get('operations', [])
        attrs_raw = row.get('attributes', [])
        if not page_name or not class_name:
            return None, None, None
        cls = class_lookup.get(class_name) or class_lookup.get(class_name.lower())
        if not cls:
            print(f"[parse_pages] Warning: class '{class_name}' not found in classifiers")
            return None, None, None
        class_id = str(cls['id'])
        ops_list = [op.strip().lower() for op in ops_raw] if isinstance(ops_raw, list) else []
        operations = {
            "create": "create" in ops_list,
            "update": "update" in ops_list,
            "delete": "delete" in ops_list,
        }
        attrs_list = [a.strip() for a in attrs_raw] if isinstance(attrs_raw, list) else []
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
        if category_name and category_name not in categories_seen:
            categories_seen[category_name] = {
                "id": str(uuid4()),
                "name": category_name,
            }
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
        return section, page, class_name

    for row in data.get("pages", []):
        try:
            section, page, class_name = parse_row(row, class_lookup, categories_seen)
            if section and page:
                sections.append(section)
                pages.append(page)
                print(f"[parse_pages] Parsed: {section['name']} -> {class_name}")
        except Exception as e:
            print(f"[parse_pages] Error parsing row: {e}")

    print(f"[parse_pages] Total parsed: {len(sections)} sections, {len(pages)} pages")
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
            readonly_attrs_filter = override.get('readonly_attributes', [])  # readonly attrs
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
            readonly_attrs_filter = []
        
        class_id = str(cls['id'])
        
        # Build operations
        operations = {
            "create": "create" in ops_list,
            "update": "update" in ops_list,
            "delete": "delete" in ops_list,
        }
        
        # Build attributes (with validation)
        attributes = []
        readonly_attributes = []
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
        
        # Validate readonly_attrs_filter against actual class attributes
        if readonly_attrs_filter:
            invalid_readonly = [a for a in readonly_attrs_filter if a not in valid_attr_names]
            if invalid_readonly:
                print(f"[validation] WARNING: readonly_attrs {invalid_readonly} not found in class '{cls_name}', ignoring them")
            readonly_attrs_filter = [a for a in readonly_attrs_filter if a in valid_attr_names]
        
        for attr in cls_attrs:
            attr_entry = {
                "name": attr['name'],
                "type": attr.get('type', 'str'),
                "derived": attr.get('derived', False),
                "enum": attr.get('enum'),
                "body": attr.get('body'),
                "description": attr.get('description'),
            }
            # Check if this attr is explicitly readonly
            if readonly_attrs_filter and attr['name'] in readonly_attrs_filter:
                readonly_attributes.append(attr_entry)
            # Check if this attr is explicitly editable
            elif attrs_filter and attr['name'] in attrs_filter:
                attributes.append(attr_entry)
            elif attrs_filter is None and not readonly_attrs_filter:
                # No filter specified at all - all are editable by default
                attributes.append(attr_entry)
            elif attrs_filter is None and attr['name'] not in (readonly_attrs_filter or []):
                # Only readonly specified, rest are editable
                attributes.append(attr_entry)
            # else: attribute is intentionally excluded (not in either list)
        
        # Resolve OOUX action node gates from override (by name, validated against activity_actions)
        action_names = {a['name'] for a in activity_actions}
        def _resolve_action_node(name):
            if not name:
                return None
            if name in action_names:
                return name
            print(f"[validation] WARNING: action_node '{name}' not found in activity actions, ignoring")
            return None

        create_action_node = _resolve_action_node(override.get("create_action_node") if override else None)
        update_action_node = _resolve_action_node(override.get("update_action_node") if override else None)
        delete_action_node = _resolve_action_node(override.get("delete_action_node") if override else None)

        # Create section
        section_id = str(uuid4())
        section = {
            "id": section_id,
            "name": page_name,
            "text": "",
            "class": class_id,
            "model_name": cls_name,
            "attributes": attributes,
            "readonly_attributes": readonly_attributes,
            "operations": operations,
            "create_action_node": create_action_node,
            "update_action_node": update_action_node,
            "delete_action_node": delete_action_node,
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
                activity_readonly_filter = None
                activity_ops_list = None
                if override:
                    activity_attrs_filter = override.get('activity_attributes') or override.get('attributes')
                    activity_readonly_filter = override.get('activity_readonly_attributes') or override.get('readonly_attributes')
                    activity_ops_list = override.get('activity_operations') or override.get('operations')
                
                # Validate activity_attrs_filter
                valid_names = {a['name'] for a in cls_attrs}
                if activity_attrs_filter:
                    activity_attrs_filter = [a for a in activity_attrs_filter if a in valid_names]
                    if not activity_attrs_filter:
                        activity_attrs_filter = None
                
                # Validate activity_readonly_filter
                if activity_readonly_filter:
                    activity_readonly_filter = [a for a in activity_readonly_filter if a in valid_names]

                # Build editable and readonly attributes
                # Key change: For activity pages, show ALL class attributes
                # - Attributes in activity_attrs_filter -> editable
                # - Attributes in activity_readonly_filter -> readonly
                # - Remaining attributes -> also readonly (so user can see all data)
                attributes = []
                readonly_attributes = []
                for attr in cls_attrs:
                    attr_entry = {
                        "name": attr['name'],
                        "type": attr.get('type', 'str'),
                        "derived": attr.get('derived', False),
                        "enum": attr.get('enum'),
                        "body": attr.get('body'),
                        "description": attr.get('description'),
                    }
                    # Check if this attr is explicitly editable
                    if activity_attrs_filter and attr['name'] in activity_attrs_filter:
                        attributes.append(attr_entry)
                    # Check if this attr is explicitly readonly OR not in any filter (default to readonly)
                    elif activity_readonly_filter and attr['name'] in activity_readonly_filter:
                        readonly_attributes.append(attr_entry)
                    elif activity_attrs_filter is None:
                        # No filter specified - all are editable by default
                        attributes.append(attr_entry)
                    else:
                        # Filter specified but attr not in it - make it readonly so user can still see
                        readonly_attributes.append(attr_entry)
                
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
                    "readonly_attributes": readonly_attributes,
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