# Coding Agent Guide

## Prerequisites

Install the CLI (one-time):
```bash
uv tool install google-agents-cli
```

---

## Generic Component & Routing Contract (MANDATORY)

To ensure that design candidates are both visually polished and functionally connected (routing/navigation), the agent MUST follow these generic semantic rules when generating DSL.

### 1. Component Naming Suffixes
The backend infers the business role and routing intent from the component name suffix. Use these patterns for ANY application:

| Suffix Pattern | Inferred Role | Inferred Intent | Usage |
| :--- | :--- | :--- | :--- |
| `*DetailPanel`, `*View` | `detail` | `view_object` | Object details, viewing data |
| `*Form`, `*Step` | `form` | `manage_object` | Create, Edit, multi-step wizards |
| `*Grid`, `*Gallery`, `*TileGrid` | `collection` | `view_collection` | Image/card layouts, catalogs |
| `*Table`, `*List`, `*ObjectList` | `collection` | `view_collection` | Tabular data, lists, management views |
| `*LineItemList` | `child_collection` | `view_related` | Sub-items (e.g., Order items inside an Order) |
| `*NavBar`, `*SideBar` | `navigation` | `navigate` | Navigation menus |
| `*SearchBar` | `search` | `query` | Search bars |

### 2. High-Fidelity Field Mapping
Use `field_layout` to map raw attributes to high-fidelity visual slots. This is the primary driver for "polished" pages.
- `image`: URL for main image/avatar.
- `title`: Primary name/label.
- `primary`: Prominent value (e.g., Price, Status).
- `secondary`: Array of supporting metadata fields.
- `badges`: Fields to be rendered as status tags/badges.

### 3. Visual Traits
Apply `style` traits to trigger UI enhancements:
- `surface_level`: `elevated` (shadows), `sunken` (inset), `flat`.
- `density`: `spacious` (luxury/Apple-style), `compact` (efficiency), `normal`.
- `color`: Use `accent` for brand-color inheritance.

### 4. Explicit Overrides
If using a custom component name that doesn't fit the suffixes, you MUST provide explicit metadata:
```json
{
  "component": "CustomWidget",
  "role": "detail",
  "intent": "view_object"
}
```

---

## Development Phases

### Phase 1: Understand Requirements
Before writing any code, understand the project's requirements, constraints, and success criteria.

### Phase 2: Build and Implement
Implement agent logic in `app/`. Use `agents-cli playground` for interactive testing. Iterate based on user feedback.

### Phase 3: The Evaluation Loop (Main Iteration Phase)
Start with 1-2 eval cases, run `agents-cli eval run`, iterate. Expect 5-10+ iterations. See the **Evaluation Guide** for metrics, evalset schema, LLM-as-judge config, and common gotchas.

### Phase 4: Pre-Deployment Tests
Run `uv run pytest tests/unit tests/integration`. Fix issues until all tests pass.

### Phase 5: Deploy to Dev
**Requires explicit human approval.** Run `agents-cli deploy` only after user confirms. See the **Deployment Guide** for details.

### Phase 6: Production Deployment
Ask the user: Option A (simple single-project) or Option B (full CI/CD pipeline with `agents-cli infra cicd`).

## Development Commands

| Command | Purpose |
|---------|---------|
| `agents-cli playground` | Interactive local testing |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |
| `agents-cli eval run` | Run evaluation against evalsets |
| `agents-cli lint` | Check code quality |
| `agents-cli infra single-project` | Set up project infrastructure (Terraform) |
| `agents-cli deploy` | Deploy to dev |
| `agents-cli scaffold enhance` | Add deployment target or CI/CD to project |
| `agents-cli scaffold upgrade` | Upgrade project to latest version |

---

## Operational Guidelines for Coding Agents

- **Code preservation**: Only modify code directly targeted by the user's request. Preserve all surrounding code, config values (e.g., `model`), comments, and formatting.
- **NEVER change the model** unless explicitly asked.
- **Model 404 errors**: Fix `GOOGLE_CLOUD_LOCATION` (e.g., `global` instead of `us-east1`), not the model name.
- **ADK tool imports**: Import the tool instance, not the module: `from google.adk.tools.load_web_page import load_web_page`
- **Run Python with `uv`**: `uv run python script.py`. Run `agents-cli install` first.
- **Stop on repeated errors**: If the same error appears 3+ times, fix the root cause instead of retrying.
- **Terraform conflicts** (Error 409): Use `terraform import` instead of retrying creation.
