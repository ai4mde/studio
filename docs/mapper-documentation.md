# Interface Generator — File Reference

`api/model/llm/interface_generator/`

---

## django_service.py

Entry point exposed to Django/Ninja. Orchestrates the full UML → interface metadata pipeline.

| Function | Purpose |
|---|---|
| `map_uml_to_interface(interface_id)` | Main pipeline: fetch system data → TKB → workflow → save to `Interface.data` |
| `map_uml_to_all_interfaces(system_id)` | Runs `map_uml_to_interface` for every interface in a system |
| `apply_prompt_to_interface(interface_id, system_id, user_request)` | LLM (Gemini) edit: converts a natural-language UI request into an interface patch |
| `_generate_missing_method_bodies(system_data, model_graph, system_id)` | Auto-generates LLM method bodies for classifier methods that have a description but no body |
| `_sync_all_classifier_methods_to_interfaces(system_id)` | After mapping, re-syncs all Classifier method bodies into Interface sections |
| `_sync_method_to_interface_sections(classifier_id, model_name, method, system_id)` | Writes a single method into every Interface section referencing that classifier |
| `_ensure_action_panel_sections(interface_id, system_id)` | Adds an action panel section to each detail/form page that has classifier methods |
| `_build_model_attrs_from_system(system_data)` | Builds `{model_name: {attr_names}}` dict from system classifier data |
| `_normalize_section_model(section, page_model_by_id)` | Normalises `primary_model`, `class`, and `layout` fields on a section |
| `_interface_to_agent_dict(interface)` | Serialises an Interface ORM object to a plain dict |
| `_strip_json_fence(value)` | Strips ` ```json ``` ` fences from LLM responses |

---

## candidate_defaults.py

Default structures for header, footer, navigation, and page categories used during candidate generation and mapping chrome injection.

| Function | Purpose |
|---|---|
| `_default_section_for_page(page, model, model_attrs, candidate_index)` | Builds a fallback content section for a page with no sections |
| `_header_sections_for_candidate(normal_pages, candidate_index)` | Returns header section list (logo + nav + search) for a candidate |
| `_footer_sections_for_candidate(candidate_index, normal_pages)` | Returns footer section list for a candidate |
| `_top_nav_section_for_candidate(normal_pages, candidate_index)` | Builds a top-bar nav section with links to all normal pages |
| `_sidebar_nav_section_for_candidate(normal_pages, candidate_index)` | Builds a sidebar nav section |
| `_ensure_normal_page_navigation(pages, sections, normal_pages, candidate_index)` | Ensures every normal page has exactly one nav section assigned |
| `_create_or_promote_nav_section(...)` | Creates a new nav section or promotes an existing one to be the canonical nav |
| `_assign_nav_to_pages(normal_pages, keep_nav_id, section_map)` | Assigns the chosen nav section ref to every normal page |
| `_inject_footer_nav_methods(sections, nav_methods)` | Writes nav link methods into the footer section |
| `_find_nav_section_ids(section_map)` | Returns `(top_nav_ids, sidebar_ids, other_nav_ids)` from section map |
| `_default_category_for_model(model, model_id_by_name)` | Returns a category dict for a model name |
| `_assign_default_page_categories(pages, sections, model_id_by_name)` | Assigns categories to pages that have none |
| `_merge_page_categories(categories, pages)` | Merges a categories list with any new categories derived from pages |
| `_model_for_page_category(page, sections_by_id, known_models)` | Infers the primary model for a page's category from its sections |

---

## candidate_generation.py

Generates and regenerates sets of 3 visual interface candidates using the LLM, then normalises and saves them.

| Function | Purpose |
|---|---|
| `generate_candidate_set(interface_id, prompt)` | **Public** — generates 3 candidates from scratch via LLM, saves to `Interface.data` |
| `regenerate_candidate_set(interface_id, selected_candidate_index, designer_requirements)` | **Public** — regenerates 3 variants from a selected candidate |
| `validate_and_save_candidate(interface_id, candidate_index, ...)` | Validates and writes a single candidate into the interface |
| `get_candidate_regeneration_context(interface_id, candidate_index, designer_requirements)` | Builds the prompt context string for regeneration |
| `_llm_generate_3_candidates(pages, sections, prompt)` | Calls LLM and returns raw list of 3 candidate dicts |
| `_llm_regenerate_3_candidates(pages, sections, designer_requirements, base_styling)` | Calls LLM for regeneration with a base styling seed |
| `_normalize_candidate_data(...)` | Full normalisation pass on pages + sections for a candidate |
| `_normalize_candidate_sections(sections, model_attrs, ...)` | Normalises layout, model, attributes, and component per section |
| `_normalize_candidate_pages(pages, candidate_index)` | Normalises page ids and type fields |
| `_merge_llm_candidate(base_pages, base_sections, llm_candidate)` | Merges LLM overrides onto the base structure |
| `_apply_design_intent_patch(...)` | Applies nav/table/hero/beige patches based on design intent text |
| `_build_gen_styling(llm_cand, base_styling, raw_base_tokens, index)` | Builds final `(styling, tokens, description)` for generation |
| `_build_regen_styling(llm_cand, base_styling, raw_base_tokens, index)` | Same for regeneration |
| `_candidate_compliance_report(...)` | Checks a candidate against visual requirements and returns a report |
| `_run_candidate_visual_check(interface_id, candidate_index)` | Takes Playwright screenshots and runs compliance check |
| `_render_candidate_preview_local(interface_id, candidate_index)` | Renders a local HTML preview for a candidate |
| `_norm_candidate_styling(styling)` | Normalises the styling dict |
| `_norm_candidate_tokens(tokens, styling)` | Normalises the design token dict |
| `_parse_llm_json(text)` | Parses JSON from raw LLM text, tolerating partial responses |
| `_candidate_list_from_llm_response(text)` | Extracts a list of candidate dicts from an LLM response |

---

## interface_patch.py

Applies a partial JSON patch (from LLM or user) to an existing Interface, field by field.

| Function | Purpose |
|---|---|
| `apply_interface_patch(interface_id, patch)` | **Public** — merges patch into `Interface.data` and saves |
| `_apply_sections_patch(data, patch_sections)` | Upserts section records from the patch |
| `_apply_pages_patch(data, patch_pages)` | Upserts page records from the patch |
| `_apply_patch_fields(data, patch)` | Applies top-level fields (tokens, styling, layout_config) from patch |
| `_apply_workflow_and_normalize(data, system_id, actor_id)` | Re-runs workflow logic and normalises after patching |
| `_validate_section_attrs(patch_sections, system_id)` | Validates that section attributes exist on the corresponding classifier |
| `_build_known_attrs_from_orm(system_id)` | Builds `{model_name: {attr_names}}` from DB classifiers |
| `_drop_deprecated_section_fields(section)` | Removes obsolete fields from a section dict |
| `_norm_card_sections(ref)` | Normalises a section reference to `{"value": id}` |
| `_norm_refs(refs)` | Normalises a list of section references |

---

## interface_schemas.py

String constants that define the JSON schema for interface sections, pages, tokens, and styling — used inside LLM prompts so the model knows the expected output format.

| Constant | Purpose |
|---|---|
| `_LAYOUT_SCHEMA` | Allowed layout and component values for sections |
| `_DATA_SCHEMA` | Full interface data structure schema (pages, sections, tokens, styling) |

---

## section_utils.py

Utility library for section and page normalisation, relationship inference, workflow page construction, and field layout computation.

| Function group | Functions | Purpose |
|---|---|---|
| **Operations** | `_normalize_section_operations` | Converts operations to `{read, create, update, delete}` bool dict |
| **Layout** | `_normalize_layout_alias`, `_infer_section_layout`, `_normalize_section_layout_component` | Resolves layout aliases; infers layout from page/role |
| **Component** | `_infer_section_component`, `_infer_data_component`, `_form_component`, `_card_component`, `_infer_chrome_component` | Picks the correct React component for a section |
| **Field layout** | `_normalize_field_layout`, `_normalize_section_attrs`, `_finalize_data_section_bindings` | Assigns field slots (title, subtitle, image, price, etc.) |
| **Workflow pages** | `_workflow_task_section`, `_ensure_workflow_pages`, `_normalize_activity_action_sections`, `_deduplicate_activity_action_sections` | Creates and deduplicates activity/workflow pages and sections |
| **Chrome** | `_normalize_chrome_section`, `_normalize_chrome_sections` | Normalises header/footer/sidebar sections |
| **Navigation** | `_navigation_methods`, `_workflow_icon_links` | Builds nav link method lists and workflow icon link lists |
| **Select-existing** | `_normalize_select_existing_sections`, `_is_select_existing_text` | Marks sections that let users select an existing record |
| **Relationships** | `_ensure_section_data_relationships`, `_ensure_logical_related_sections`, `_ensure_item_click_navigation` | Injects query filters, related sections, and click-through navigation |
| **Model helpers** | `_canonical_model_name`, `_relation_cardinality`, `_is_direct_single_relation`, `_is_direct_child_relation`, `_bridge_child_model`, `_model_field_names`, `_model_graph_attr_names` | Model graph traversal and cardinality helpers |
| **Query helpers** | `_query_filter_exists`, `_append_query_filter`, `_build_collection_query` (via nav_planner) | Builds and merges section query filters |
| **Page type** | `_page_type_value`, `_infer_page_type_value`, `_canonical_page_type` | Reads/infers page type (normal/activity) |
| **Misc** | `_ref_id`, `_fuzzy_model_key`, `_fallback_model_for_page`, `_snake_name`, `_guess_relation_field` | ID extraction, fuzzy matching, snake_case |

---

## token_normalizer.py

Tiny utility module for normalising IDs and names to consistent slugs.

| Function | Purpose |
|---|---|
| `_as_list(payload, key)` | Safely extracts a list from a dict or returns the payload if already a list |
| `_name_id(value)` | Converts a display name to a lowercase underscore id |
| `_page_name(value)` | Normalises a page name to Title_Case |
| `_workflow_page_name(value)` | Same but prefixes with `wf_` for workflow pages |
| `_section_id(value)` | Converts a section name to a lowercase underscore id |
| `_sid(name)` | Alias for `_section_id` |

---

## workflow_application.py

Applies built-in workflow logic (activity diagram steps) to the pages/sections structure produced by the TKB.

| Function | Purpose |
|---|---|
| `_apply_builtin_workflow_logic(interface_dict, system_id, actor_id, ...)` | **Main entry** — inserts workflow pages and sections from activity diagrams into the interface |
| `_build_model_attrs(system_context)` | Builds `{model: {attr_names}}` from system context |

---

## semantic_mapper/engine.py

The TKB (Transformation Knowledge Base) execution engine. Reads `interface_mapper_rules.yaml` and transforms UML metadata into pages + sections.

| Class / Function | Purpose |
|---|---|
| `TransformationEngine` | Main class — loads YAML rules and runs the transformation |
| `TransformationEngine.transform(metadata)` | Runs all rules against the input metadata; returns `{interfaces, semantic_profiles, section_composition}` |
| `TransformationEngine._semantic_interpretation_pass(ctx)` | First pass: computes semantic profiles (CRUD/Lookup/Config/Search/StateTransition) per entity |
| `TransformationEngine._process_classifier_for_profile(...)` | Assigns intent profile to a classifier based on intent_rules |
| `TransformationEngine._process_activity_diagram_for_workflow(...)` | Identifies workflow patterns in activity diagrams |
| `TransformationEngine._execute(rule, ctx)` | Dispatches a single YAML rule to the correct handler |
| `TransformationEngine._run_on_nodes(rule, diagram, node_type, ctx)` | Runs a rule against every matching node type in a diagram |
| `TransformationEngine._run_on_edges(rule, diagram, ctx)` | Runs a rule against every matching edge |
| `TransformationEngine._run_on_pattern(rule, diagram, ctx)` | Runs a rule against structural multi-node patterns |
| `TransformationEngine._apply_rule(rule, source, ctx)` | Applies mappings and writes pages/sections via `_Context` |
| `TransformationEngine._post_assign_sections(ctx)` | After all rules: assigns sections to their actor interfaces |
| `TransformationEngine._write_register(...)` | Writes a page or section into the context output |
| `_Context` | Internal state holder during a transform run: stores diagrams, node index, output interfaces |
| `_Context.transform(metadata)` | Runs full rule set |
| `_Context.add_page / add_section` | Registers pages/sections per actor |
| `_Context.build_output()` | Assembles final output dict |
| `_add_classifier_sections(ctx)` | Fallback: adds basic sections for classifiers not covered by rules |
| `generate_interface_metadata(metadata_json)` | Standalone entry point: JSON string in → JSON string out |
| `_interpret_entity_intents(...)` | Infers semantic intent (CRUD/Lookup/Config etc.) from class attributes and use case names |
| `_match_pattern(diagram, pattern, ctx)` | Finds node groups matching a structural pattern spec |
| `_eval / _eval_path_expr / _resolve_path` | Expression evaluator for YAML rule `mapping` values |

---

## semantic_mapper/adapter.py

Converts `system_data` (Django ORM format) into the TKB engine's expected input format, and extracts the per-actor result from TKB output.

| Function | Purpose |
|---|---|
| `system_data_to_tkb_input(system_data)` | **Main** — enriches diagrams and returns TKB-ready metadata dict |
| `enrich_diagrams(system_data)` | Builds fully-enriched diagram list (class, use case, activity) |
| `extract_interface_for_actor(tkb_output, actor_name, system_data)` | Extracts `(pages, sections)` for a specific actor from TKB output |
| `_enrich_nodes(diagram, classifiers)` | Embeds classifier data into diagram nodes |
| `_enrich_edges(diagram, relations, node_by_cls, dtype)` | Embeds relation data into diagram edges |
| `_resolve_class_uuids(sections, cls_name_by_id)` | Replaces classifier UUID references with model names |

---

## semantic_mapper/sanitization.py

Name sanitisation utilities — ensures all generated identifiers are valid Python/Django identifiers.

| Function | Purpose |
|---|---|
| `general_name_sanitization(proposed_name)` | Base: alphanumeric + underscores, dedupes `__`, strips reserved keywords |
| `project_name_sanitization` | Alias of general |
| `app_name_sanitization` | Alias of general |
| `app_namespace_sanitization` | Lowercased app name, blocks reserved names like `admin` |
| `model_name_sanitization` | TitleCase model name |
| `attribute_name_sanitization` | snake_case attribute name |
| `page_name_sanitization` | Page name slug |
| `section_name_sanitization` | Section name slug |
| `category_name_sanitization` | Category name slug |
| `custom_method_name_sanitization` | Method name slug |

---

## uml_mapping/uml_extractor.py

Extracts structured intelligence from raw UML diagrams: model graph, actor permissions, use case roles, and activity steps.

| Function | Purpose |
|---|---|
| `extract_uml_intelligence(system_data, actor_id, actor_name)` | **Main** — returns `{model_graph, actor_permissions, actor_intel, workflow_intel}` |
| `extract_class_diagram(classifiers, relations)` | Builds model graph with attributes, associations, and cardinalities |
| `extract_use_case_diagram(...)` | Extracts use cases with inferred model, permissions, and page role |
| `extract_activity_diagrams(system_data, classifiers, relations)` | Extracts activity diagram steps with actor, model, and component hint |
| `detect_semantic_decisions(model_name, model_info)` | Detects semantic patterns (e.g. status field → state machine, price → commerce) |
| `score_layout(attr_names)` | Scores which layout (gallery/table/card/list) fits a model's attributes |
| `_expand_actor_scope(model_graph, initial_permissions)` | Expands actor permissions transitively through model associations |
| `_infer_permissions(uc_name)` | Infers CRUD permissions from use case name tokens |
| `_infer_page_role(uc_name, has_workflow)` | Infers page role (collection/detail/workflow_entry) from use case name |
| `_best_model_for_text(text, model_names, model_attr_names)` | Fuzzy-matches a text string to the most likely model name |
| `_sys_as_list(system_data, key)` | Safely extracts a list from system_data |
| `_cardinality(source_mult, target_mult)` | Converts UML multiplicity strings to `1-1 / 1-many / many-many` |

---

## uml_mapping/metadata_context.py

Fetches and assembles the raw system context data from Django ORM into a plain dict.

| Function | Purpose |
|---|---|
| `_fetch_system_context_data(system_id)` | Queries Django for classifiers, relations, diagrams, and activity diagrams; returns unified system dict |
| `_actor_name_from_context(system_context, actor_id)` | Looks up an actor's name from the system context by UUID |
| `_node_position(node)` | Extracts `(x, y)` position from a node for sorting |

---

## uml_mapping/usecase_workflow.py

Builds the `usecase_navigation` dict — the cross-reference between use cases, workflow entries, steps, and interface pages.

| Function | Purpose |
|---|---|
| `_build_usecase_navigation(system_data, actor_id, actor_name, ...)` | **Main** — returns `{pages, workflow_entries, steps, nav_links}` for the actor |
| `_workflow_plan(system_data, actor_id, actor_name)` | Builds workflow step list from activity diagrams |
| `_nav_mapping_for_usecase(usecase, workflow_entry)` | Determines page id, model, and operation kind for a single use case |
| `_usecase_has_workflow_entry(usecase, ...)` | Checks if a use case is the entry point for an activity workflow |
| `_build_activity_diagrams(system_data)` | Enriches raw activity diagrams with resolved actor and classifier data |
| `_build_activity_diagram_nodes(raw_nodes, classifiers, global_node_cls)` | Resolves node types and classifier refs |
| `_build_activity_diagram_edges(raw_edges, relations, node_by_cls)` | Resolves edge source/target to node ids |
| `_activity_action_indexes(system_data)` | Builds index of all activity action nodes and first-step ids |
| `_activity_models_for_step(step, workflow_entries, known_models)` | Infers which models a workflow step operates on |
| `_infer_usecase_model(name, explicit_classes, classifiers, model_names)` | Fuzzy-matches a use case to its primary model |
| `_is_child_collection_model(model_name)` | Returns True if the model name implies a child/line-item (e.g. OrderItem) |
| `_plural_page_id(model)` | Returns the pluralised page id for a model (e.g. `Book` → `books`) |
| `_inline_operation_kind(...)` | Infers whether a use case is create/update/delete/select |
| `_actor_refs(system_data, actor_id, actor_name)` | Returns the set of classifier UUIDs that represent the actor |

---

## uml_mapping/mapping_sections.py

Materialises the final pages and sections structure during UML mapping — adds chrome, content, workflow entry, and navigation sections.

| Function | Purpose |
|---|---|
| `_ensure_mapping_content_sections(pages, sections, usecase_navigation, model_attrs, model_graph)` | Ensures every page has correct content sections from use case navigation |
| `_ensure_mapping_chrome_sections(pages, sections)` | Injects header and footer chrome; ensures normal pages have navigation |
| `_ensure_workflow_entry_sections(pages, sections, usecase_navigation)` | Adds workflow start/entry sections for workflow entry pages |
| `_ensure_pre_workflow_content_sections(...)` | Adds pre-workflow content sections (record selection before starting a workflow) |
| `_ensure_usecase_pages(pages, usecase_navigation)` | Ensures a page exists for every use case in the navigation plan |
| `_ensure_collection_detail_navigation(...)` | Adds click-through navigation from collection sections to detail pages |
| `_materialize_nav_plan_sections(pages, sections, nav_plan, model_attrs)` | Creates actual section dicts from the navigation plan |
| `_apply_nav_methods(pages, sections, usecase_navigation)` | Writes nav link methods into chrome sections |
| `_drop_unreferenced_non_global_sections(pages, sections)` | Removes sections not referenced by any page (except global chrome) |
| `_dedupe_agent_header_shells(pages, sections)` | Removes duplicate header shell sections |
| `_inject_chrome_sections(new_sections, sections, section_map, pages, prepend)` | Inserts chrome sections into the sections list and page refs |
| `_ensure_candidate_content_structure(...)` | Ensures candidate pages all have content sections (used during candidate flow) |
| `_make_workflow_start_section(entry, page)` | Builds a workflow start button section dict |
| `_make_pre_workflow_section(...)` | Builds a pre-workflow record selection section dict |
| `_apply_section_nav(section, nav_ids, nav_names, workflow_icon_links)` | Writes nav methods into a section |
| `category_names_for_pages(pages)` | Collects unique category labels from a pages list |

---

## uml_mapping/navigation_planner.py

Plans which sections belong on which page, what layout/component they use, and how queries filter them — based on use case navigation and semantic profiles.

| Function | Purpose |
|---|---|
| `build_navigation_plan(uml_intel, actor_permissions, model_attrs, ...)` | **Main** — returns a plan dict mapping each page to its sections with full field/query/component specs |
| `_compose_page_sections(page, model_attrs, actor_permissions, ...)` | Determines the full section set for a single page |
| `_apply_composition_pattern(page, pattern_entry, ...)` | Applies a TKB composition pattern to produce sections for a page |
| `_match_composition_pattern(page, model_attrs, ...)` | Finds the best matching composition pattern for a page |
| `_section_for_page(page, model_attrs, actor_permissions)` | Builds the primary section for a page |
| `_child_section(page_id, model, model_attrs, ...)` | Builds a child collection section |
| `_collection_section_for_model(...)` | Builds an `object_collection` section |
| `_detail_section_for_model(...)` | Builds an `object_detail` section |
| `_filter_section_for_model(...)` | Builds a filter section |
| `_sections_for_activity_step(step, model_attrs, workflow_entries)` | Builds sections for a single activity workflow step |
| `_nav_plan_process_pages(...)` | Processes normal pages in the nav plan |
| `_nav_plan_process_workflow_entry(...)` | Processes workflow entry pages |
| `_nav_plan_process_step(...)` | Processes individual workflow steps |
| `_pick_fields(model_attrs, model, role, limit)` | Selects the most relevant fields for a section by role |
| `_pick_fields_by_names(...)` | Picks fields prioritising specific semantic buckets |
| `_operations_for_model(model, actor_permissions)` | Returns allowed CRUD operations for a model |
| `_operations_for_page(model, actor_permissions, page)` | Same, constrained to page type |
| `_layout_for_page_role(page)` | Maps page role to default layout |
| `_component_for_section(role, layout, model, page_id)` | Maps role + layout to React component name |
| `_field_layout_for_component(component, attrs, related_attrs)` | Assigns field slots (title/subtitle/image etc.) for a component |
| `_query_for_section(...)` | Builds the query filter dict for a section |
| `_build_section_from_pattern_entry(...)` | Builds a section dict from a TKB composition pattern entry |
| `_augment_roles_from_operation(roles, operation_kind, page_id, model)` | Adds extra section roles implied by an operation |
