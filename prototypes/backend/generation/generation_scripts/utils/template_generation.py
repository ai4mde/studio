from utils.definitions.application_component import ApplicationComponent
from utils.definitions.page import Page
from utils.sanitization import project_name_sanitization, app_name_sanitization, page_name_sanitization, app_namespace_sanitization
from utils.file_generation import ensure_generated_directory, generate_output_file, read_template_file, write_to_file
from utils.definitions.model import AttributeType
from utils.loading_json_utils import make_activity_start_section, make_activity_tasks_section
import re
import difflib


UNIFIED_TEMPLATE = "page_unified.html.jinja2"
ACCENT_HEX_TOKEN = "accent.hex"


HEADER_CHROME_LAYOUTS = {
    'promo-bar', 'promo-strip', 'logo', 'search-bar', 'icon-actions',
    'nav', 'nav-links', 'nav-bar', 'main-header', 'minimal-header',
    'commerce-header', 'dashboard-header', 'split-header', 'app-header',
    'compact-header', 'mega-header', 'hero-header', 'tabbed-header',
    'glass-header', 'command-header', 'site-nav',
}

FOOTER_CHROME_LAYOUTS = {
    'service-bar', 'service-strip', 'link-grid', 'footer-links',
    'brand-strip', 'footer-brand', 'site-footer', 'compact-footer',
    'legal-footer', 'newsletter-footer', 'social-footer', 'mega-footer',
    'split-footer', 'app-footer', 'cta-footer', 'minimal-footer',
}

MAX_WIDTH_CLASS = {
    "sm": "max-w-3xl", "md": "max-w-4xl", "lg": "max-w-5xl",
    "xl": "max-w-6xl", "2xl": "max-w-7xl", "full": "max-w-full",
}

TAILWIND_HEX = {
    "white": "#ffffff", "black": "#000000",
    "slate-50": "#f8fafc", "slate-100": "#f1f5f9", "slate-200": "#e2e8f0",
    "slate-700": "#334155", "slate-800": "#1e293b", "slate-900": "#0f172a",
    "gray-50": "#f9fafb", "gray-100": "#f3f4f6", "gray-200": "#e5e7eb",
    "gray-700": "#374151", "gray-800": "#1f2937", "gray-900": "#111827",
    "blue-50": "#eff6ff", "blue-100": "#dbeafe", "blue-200": "#bfdbfe",
    "blue-700": "#1d4ed8", "blue-950": "#172554",
    "purple-50": "#faf5ff", "purple-100": "#f3e8ff", "purple-200": "#e9d5ff",
    "violet-100": "#ede9fe", "violet-200": "#ddd6fe",
    "yellow-400": "#facc15",
}


def _class_to_hex(value: str | None) -> str | None:
    if not value:
        return None
    value = str(value).strip()
    if value.startswith("#"):
        return value
    if value.startswith(("bg-[", "text-[", "border-[")):
        return value.split("[", 1)[1].split("]", 1)[0]
    for part in value.split():
        for prefix in ("bg-", "text-", "border-"):
            if part.startswith(prefix):
                color = part[len(prefix):]
                if color in TAILWIND_HEX:
                    return TAILWIND_HEX[color]
    return None


def _expand_legacy_token_hex(tokens: dict) -> None:
    for class_key, hex_key in (
        ("page.body.bg", "page.body.bg_hex"),
        ("page.body.text", "page.body.text_hex"),
        ("region.header.bg", "region.header.bg_hex"),
        ("region.footer.bg", "region.footer.bg_hex"),
        ("element.text.accent", ACCENT_HEX_TOKEN),
    ):
        if not tokens.get(hex_key):
            color = _class_to_hex(tokens.get(class_key))
            if color:
                tokens[hex_key] = color


def _collect_position_sections(pages, position):
    seen = set()
    out = []
    chrome_layouts = set()
    if position == 'header':
        chrome_layouts = HEADER_CHROME_LAYOUTS
    elif position == 'footer':
        chrome_layouts = FOOTER_CHROME_LAYOUTS
    for page in pages:
        for sc in page.section_components:
            if (sc.position == position or sc.layout in chrome_layouts) and sc.id not in seen:
                seen.add(sc.id)
                out.append(sc)
    return out


def generate_base_page(application_component: ApplicationComponent, output_templates_directory: str, tokens_override: dict = None) -> bool:
    application_name = app_name_sanitization(application_component.name)

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/base.html.jinja2"
    OUTPUT_FILE_PATH = output_templates_directory + "/" + application_name + "_base.html"

    logo = "" # TODO: retrieve from metadata
    categories = application_component.categories
    tokens = dict(tokens_override or getattr(application_component, "tokens", {}) or {})
    default_blues = {"", None, "#2563eb", "#0000a4", "var(--accent)"}
    styling_accent = (application_component.styling.accent_color or '') if application_component.styling else ''
    if styling_accent and tokens.get(ACCENT_HEX_TOKEN) in default_blues:
        tokens[ACCENT_HEX_TOKEN] = styling_accent
    accent_hex = tokens.get(ACCENT_HEX_TOKEN) or styling_accent or '#0000a4'
    header_sections = _collect_position_sections(application_component.pages, 'header')
    footer_sections = _collect_position_sections(application_component.pages, 'footer')

    data = {
        "application_name": application_name,
        "application_namespace": app_namespace_sanitization(application_name),
        "logo": logo,
        "pages": application_component.pages,
        "categories": categories,
        "authentication_present": application_component.authentication_present,
        "settings": application_component.settings,
        "styling": application_component.styling,
        "header_sections": header_sections,
        "footer_sections": footer_sections,
        "_accent_hex": accent_hex,
        "_brand_name": application_name,
        "tokens": tokens,
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    return False


def _make_task_home_page(application_component: ApplicationComponent) -> Page:
    application_name = app_name_sanitization(application_component.name)
    start_section = make_activity_start_section(application_name, "Home", {
        "id": "task-home-activity-start",
        "name": "Processes you can start",
        "label": "Processes you can start",
        "col_span": 6,
        "style": {"columns": "1", "card_style": "elevated", "cta_label": "Start"},
    })
    tasks_section = make_activity_tasks_section(application_name, "Home", {
        "id": "task-home-activity-tasks",
        "name": "Tasks to complete",
        "label": "Tasks to complete",
        "col_span": 6,
        "style": {"columns": "1", "card_style": "elevated"},
    })
    chrome_sections = _collect_position_sections(application_component.pages, 'header')
    # Sidebar sections are data-specific filter panels belonging to their source pages;
    # including them here would generate form actions pointing to a non-existent 'task' URL.
    chrome_sections.extend(_collect_position_sections(application_component.pages, 'footer'))
    return Page(
        id="task-home",
        application=application_name,
        name="Tasks",
        category=None,
        activity_name=None,
        type="normal",
        section_components=[start_section, tasks_section] + chrome_sections,
        layout="vertical",
        gap="normal",
    )


def generate_home_page(application_component: ApplicationComponent, output_templates_directory: str, tokens: dict) -> bool:
    application_name = app_name_sanitization(application_component.name)

    OUTPUT_FILE_PATH = output_templates_directory + "/" + application_name + "_home.html"
    home_page = _make_task_home_page(application_component)
    home_page.is_task_page = True
    gen_html = _render_unified_page(
        page=home_page,
        all_pages=application_component.pages,
        tokens=tokens,
        styling=application_component.styling,
        application_name=application_name,
        project_name=project_name_sanitization(application_component.project),
        preview_mode=False,
    )
    write_to_file(OUTPUT_FILE_PATH, gen_html)
    return True


def _render_unified_page(page, all_pages, tokens, styling, application_name, project_name, preview_mode=False):
    """Render one page using the shared unified unified template."""
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/" + UNIFIED_TEMPLATE
    template = read_template_file(TEMPLATE_PATH)
    return template.render(
        project_name=project_name,
        application_name=application_name,
        application_namespace=app_namespace_sanitization(application_name),
        page=page,
        AttributeType=AttributeType,
        styling=styling,
        tokens=tokens,
        all_pages=all_pages,
        preview_mode=preview_mode,
        _accent_hex=tokens.get(ACCENT_HEX_TOKEN, (styling.accent_color if styling and getattr(styling, 'accent_color', None) else '#0000a4')),
        _brand_name=tokens.get("brand.name", application_name),
    )


def generate_action_log_page(application_component: ApplicationComponent, OUTPUT_TEMPLATES_DIRECTORY: str) -> bool:
    application_name = app_name_sanitization(application_component.name)

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/workflow_engine/action_log.html.jinja2"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/" + application_name + "_action_log.html"

    data = {
        "application_name": application_name,
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    return False


def generate_change_user_assignment(application_component: ApplicationComponent, OUTPUT_TEMPLATES_DIRECTORY: str) -> bool:
    application_name = app_name_sanitization(application_component.name)

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/workflow_engine/change_user_assignment.html.jinja2"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/" + application_name + "_change_user_assignment.html"

    data = {
        "application_name": application_name,
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    return False


_FONT_CDN = {
    "inter":    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    "roboto":   "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap",
    "poppins":  "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
    "playfair": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&display=swap",
    "mono":     "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap",
    "geist":    "https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap",
}
_FONT_CSS_NAME = {
    "inter": "Inter", "roboto": "Roboto", "poppins": "Poppins",
    "playfair": "'Playfair Display'", "mono": "'JetBrains Mono'", "geist": "Geist",
}
_DEFAULT_BLUES = {"", None, "#2563eb", "#0000a4", "var(--accent)"}


def _apply_styling_to_tokens(tokens: dict, styling, application_name: str) -> None:
    """Merge styling attributes into the tokens dict in-place."""
    if not styling:
        return
    styling_accent = getattr(styling, 'accent_color', None)
    if styling_accent and tokens.get(ACCENT_HEX_TOKEN) in _DEFAULT_BLUES:
        tokens[ACCENT_HEX_TOKEN] = styling_accent
    accent = tokens.get(ACCENT_HEX_TOKEN)
    if accent:
        tokens.setdefault("region.header.bg", f"bg-[{accent}]")
        tokens.setdefault("page.header.text", "text-white")
        tokens.setdefault("brand.name", application_name)
    if getattr(styling, 'background_color', None):
        tokens.setdefault("page.body.bg", f"bg-[{styling.background_color}]")
        tokens.setdefault("page.body.bg_hex", styling.background_color)
    if getattr(styling, 'text_color', None):
        tokens.setdefault("page.body.text", f"text-[{styling.text_color}]")
        tokens.setdefault("page.body.text_hex", styling.text_color)


def _apply_accent_fallbacks(tokens: dict) -> None:
    """Propagate the accent hex token to header/footer/button keys if they are still default blues."""
    accent_hex = tokens.get(ACCENT_HEX_TOKEN)
    if not accent_hex:
        return
    for key in ("region.header.bg_hex", "region.footer.bg_hex", "button.primary.bg_hex", "button.primary.border_hex", "input.border_focus_hex"):
        if tokens.get(key) in _DEFAULT_BLUES:
            tokens[key] = accent_hex
    tokens.setdefault("region.header.text_hex", "#ffffff")
    tokens.setdefault("region.footer.text_hex", "#ffffff")


def _apply_font_and_theme_tokens(tokens: dict, styling) -> None:
    """Apply font, radius, and theme tokens from styling in-place."""
    font = getattr(styling, 'font_family', 'inter') if styling else 'inter'
    tokens.setdefault("page.font.family", _FONT_CSS_NAME.get(font, "Inter"))
    tokens.setdefault("page.font.cdn", _FONT_CDN.get(font, _FONT_CDN["inter"]))
    radius = getattr(styling, 'radius', 8) if styling else 8
    tokens.setdefault("page.radius.px", str(radius))
    max_w = getattr(styling, 'page_max_width', 'xl') if styling else 'xl'
    tokens.setdefault("page.container.class", MAX_WIDTH_CLASS.get(max_w, "max-w-6xl"))
    tokens.setdefault("theme.button.style", getattr(styling, 'button_style', 'solid') if styling else 'solid')
    tokens.setdefault("theme.card.hover", getattr(styling, 'card_hover', 'lift') if styling else 'lift')
    tokens.setdefault("theme.image.ratio", getattr(styling, 'image_ratio', '4:3') if styling else '4:3')
    tokens.setdefault("theme.divider", getattr(styling, 'divider', 'none') if styling else 'none')


def _generate_manager_pages(application_component: ApplicationComponent, output_dir: str) -> None:
    """Generate manager-only pages (action log and user assignment)."""
    if not generate_action_log_page(application_component, output_dir):
        raise Exception("Failed to generate action log page")
    if not generate_change_user_assignment(application_component, output_dir):
        raise Exception("Failed to generate change user assignment page")


def generate_templates(application_component: ApplicationComponent, system_id: str, _variant_id: str = "") -> bool:
    project_name = project_name_sanitization(application_component.project)
    application_name = app_name_sanitization(application_component.name)
    pages_in_app = application_component.pages
    styling = application_component.styling

    tokens = dict(getattr(application_component, "tokens", {}) or {})
    _expand_legacy_token_hex(tokens)
    _apply_styling_to_tokens(tokens, styling, application_name)
    _apply_font_and_theme_tokens(tokens, styling)
    _apply_accent_fallbacks(tokens)

    OUTPUT_TEMPLATES_DIRECTORY = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name + "/" + application_name + "/templates"

    try:
        ensure_generated_directory(OUTPUT_TEMPLATES_DIRECTORY)
    except:
        raise Exception("Failed to create templates directory for " + application_name + " application")

    if not generate_base_page(application_component, OUTPUT_TEMPLATES_DIRECTORY, tokens):
        raise Exception("Failed to generate base page")

    if not generate_home_page(application_component, OUTPUT_TEMPLATES_DIRECTORY, tokens):
        raise Exception("Failed to generate home page")

    if application_component.settings and application_component.settings.manager_access:
        _generate_manager_pages(application_component, OUTPUT_TEMPLATES_DIRECTORY)

    for page in pages_in_app:
        OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/" + application_name + "_" + page_name_sanitization(page.name) + ".html"
        # Render actual prototype page HTML from the shared unified template.
        gen_html = _render_unified_page(
            page=page,
            all_pages=pages_in_app,
            tokens=tokens,
            styling=styling,
            application_name=application_name,
            project_name=project_name,
            preview_mode=False,
        )

        write_to_file(OUTPUT_FILE_PATH, gen_html)

    return True
