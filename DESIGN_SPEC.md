# DESIGN_SPEC: Gemini Make Agent

## Overview
The **Gemini Make Agent** is an AI-powered design-to-code assistant integrated into the Studio platform. It transforms designer prompts and system metadata (diagrams, classifiers, relations, interfaces) into functional Jinja2 and HTML templates for the prototyping engine.

The agent ensures that generated UI components align with the project's backend logic and existing template patterns, providing conflict detection when generated code diverges from established structures.

## Core Capabilities
1.  **Context-Aware Generation**: Reads full system metadata and user prompts to generate multi-page application structures.
2.  **Logic Mapping & Integrity**: A specialized sub-agent verifies that generated components (e.g., specific lists, detail views) map correctly to the backend's expected data keys and logic.
3.  **File System Integration**: Writes generated templates directly to the `prototypes/backend/generation/templates` directory.
4.  **Conflict Detection**: Identifies and reports mismatches between generated UI expectations and existing backend template logic.

## Architecture & Sub-Agents
-   **Root Agent (Gemini Make)**: Orchestrates the generation process, gathers context, and manages the user conversation.
-   **Integrity Agent (Sub-Agent)**: Specialized in static analysis of generated templates vs. backend logic. It checks if variable names, loops, and conditional blocks match the data structures defined in the metadata.

## Tools Required
-   `get_system_context(system_id)`: Fetches diagrams, classifiers, and relations.
-   `get_interface_config(interface_id)`: Fetches current page/section definitions.
-   `list_existing_templates()`: Scans `prototypes/backend/generation/templates` for established patterns.
-   `write_template_file(filename, content)`: Saves the generated Jinja2/HTML to disk.
-   `verify_template_logic(content, metadata)`: (Used by Integrity Agent) Compares template variables against metadata definitions.

## Constraints & Safety Rules
-   **Read-Only Metadata**: The agent MUST NOT modify the system metadata (Project, Classifiers, etc.).
-   **Local Scope**: Operates only within the current project's prototyping directories.
-   **Explicit Conflict Reporting**: If a conflict is found, the agent must describe it clearly to the user rather than silently attempting to "fix" it by changing the metadata.

## Success Criteria
-   Generated templates are syntactically correct Jinja2/HTML.
-   Templates correctly reference variables derived from the system's Classifiers.
-   Conflicts with existing backend logic are successfully flagged before writing files.
