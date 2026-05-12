UI_TOKEN_SCHEMA = """
The UI is styled using 18 semantic tokens across 4 tiers. Each token MUST be a Tailwind CSS utility class.

Tier 1: Page (Global layout and background)
- page.body.bg: Main background color
- page.body.text: Primary text color
- page.container.max_width: Max width for content (e.g., max-w-7xl)
- page.header.height: Height of the header (e.g., h-16)

Tier 2: Component (Cards, containers, navigation)
- component.card.bg: Background for cards
- component.card.border: Border color/style for cards
- component.card.shadow: Shadow intensity (e.g., shadow-md)
- component.nav.active: Background for active nav items

Tier 3: Element (Buttons, inputs, icons)
- element.button.primary: Primary action button style
- element.button.secondary: Secondary action button style
- element.input.bg: Background for input fields
- element.input.border: Border for input fields
- element.text.accent: Color for accents/highlights
- element.text.muted: Color for secondary/muted text

Tier 4: Region (Specific areas like Sidebar, Footer)
- region.sidebar.bg: Background for sidebar
- region.sidebar.width: Width of the sidebar (e.g., w-64)
- region.footer.bg: Background for footer
- region.header.bg: Background for top header
"""
