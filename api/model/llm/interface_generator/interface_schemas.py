"""Prompt schema constants used by the interface generation agents."""
_LAYOUT_SCHEMA = """
=== SECTION FIELDS ===
layout: "card"|"list"|"table"|"detail"|"gallery"|"filter"|"form"
        |"activity_action"|"activity_start"|"activity_tasks"
        |"promo-bar"|"logo"|"search-bar"|"icon-actions"|"nav-links"
        |"site-nav"|"main-header"|"minimal-header"|"commerce-header"
        |"dashboard-header"|"split-header"|"app-header"|"compact-header"
        |"mega-header"|"hero-header"|"tabbed-header"|"glass-header"
        |"command-header"
        |"service-bar"|"link-grid"|"brand-strip"|"site-footer"
        |"compact-footer"|"legal-footer"|"newsletter-footer"|"social-footer"
        |"mega-footer"|"split-footer"|"app-footer"|"cta-footer"|"minimal-footer"

component: match to layout:
  table Ã¢â€ â€™ DataTable
  card Ã¢â€ â€™ CardGrid | ProductCardGrid | PersonCardGrid | ObjectCardGrid | ImageCard | ImageCardGrid | CategoryTileGrid
  list Ã¢â€ â€™ ObjectList | LineItemList | RelatedObjectList
  detail Ã¢â€ â€™ DetailPanel | ProductDetailPanel
  gallery Ã¢â€ â€™ ImageCardGrid | ObjectCardGrid
  form Ã¢â€ â€™ ObjectForm
  filter Ã¢â€ â€™ (keep existing or use ObjectForm)
  site-nav Ã¢â€ â€™ NavBar
  site-footer Ã¢â€ â€™ SiteFooter
  logo Ã¢â€ â€™ Logo | BrandLockup | ImageLogo
  search-bar Ã¢â€ â€™ SearchBar
  icon-actions Ã¢â€ â€™ IconActions
  nav-links Ã¢â€ â€™ NavBar
  header templates Ã¢â€ â€™ HeaderTemplate
  footer templates Ã¢â€ â€™ FooterTemplate

position: "main"|"sidebar"|"header"|"hero"|"footer"
col_span: 12|6|4|3

style (include only relevant keys):
  color: "accent"|"accent-secondary"|"neutral"
         (semantic token alias only; exact colors belong in top-level tokens)
  density: "compact"|"normal"|"spacious"
  columns: "1"|"2"|"3"|"4"          (card/gallery only)
  display_mode: "grid"|"carousel"|"banner"  (card only)
  card_style: "default"|"product"|"category"|"compact"
  list_style: "default"|"product"|"cart-item"|"related"
  form_style: "default"|"auth"|"step"|"summary"
  image_position: "left"|"top"|"right"    (detail only)
  image_size: "sm"|"md"|"lg"             (detail only)
  image_ratio: "wide"|"16:9"|"4:3"|"1:1"
  banner_height: "sm"|"md"|"lg"|"xl"
  shadow: "none"|"sm"|"md"|"lg"
  border: "none"|"light"|"colored"
  bg: "white"|"light"|"dark"|"transparent"
  header_style: "default"|"large"|"hidden"
  nav_height: "compact"|"normal"|"tall"|"xl"   (nav/header sections)
  sidebar_side: "left"|"right"                 (sidebar sections only)
  sidebar_width: 2..6                          (sidebar sections only)
  logo_size: "sm"|"md"|"lg"|"xl"
  logo_shape: "rounded"|"circle"|"square"
  logo_variant: "lockup"|"image-only"|"text-only"   (logo sections: lockup=icon+text, image-only=icon only, text-only=text only)
  logo_url: image URL string (only if user asked for logo image)
  image_url: image URL string (only for ImageCard/banner)
  cta_label: button text string e.g. "Save" | "Submit" | "Continue"  (form sections)
  login_label: auth submit button label (form_style="auth") e.g. "Sign in" | "Log in"
  step_icon: emoji or "" for step header icon (form_style="step") e.g. "Ã°Å¸â€œâ€¹" | "Ã°Å¸â€™Â³"
  total_label: label for total row (form_style="summary") e.g. "Total" | "Order total"
  seller_label: e.g. "Sold by" (card/list sections Ã¢â‚¬â€ empty string to hide)
  availability_label: e.g. "In stock" | "Out of stock" (card/list/detail Ã¢â‚¬â€ empty string to hide)
  delivery_label: e.g. "Free delivery" | "Ships in 2-3 days" (card/list/detail Ã¢â‚¬â€ empty string to hide)
  action_variant: "link"|"ghost"|"button"  (icon-actions sections: how action items are styled)
  show_logout: true|false                  (icon-actions sections: show/hide logout link)
  logout_label: string e.g. "Sign out"    (icon-actions sections: label for logout link)
  variant: "button"|"link"|"fab"|"wizard_next"|"auto"  (activity_action sections only: visual style of the action)
  align: "left"|"center"|"right"                       (activity_action sections only)
  size: "sm"|"md"|"lg"                                 (activity_action sections only)

=== PAGE FIELDS ===
layout.value: "vertical"|"horizontal"|"vertical-reverse"|"horizontal-reverse"
layout.main_width: "contained"|"wide"|"full"
layout.header_width: "contained"|"full"
layout.hero_width: "contained"|"full"
layout.footer_width: "contained"|"full"
gap.value: "compact"|"normal"|"spacious"

page.sections entries are normally {"value": "section_id"}.
To group 2-3 related sections (e.g. a detail panel + a stats table) inside one
visual card frame, use a card container object instead of a bare ref:
  {"type": "card", "id": "unique_card_id", "label": "Card Title", "sections": [{"value": "section_id"}, ...]}
Only use card containers for main-position data sections that logically belong
together. Chrome sections (header, footer, nav) must remain bare refs.

=== GLOBAL STYLING (one set per candidate) ===
fontFamily: "inter"|"roboto"|"poppins"|"playfair"|"mono"|"geist"
textSize: "xs"|"sm"|"md"|"lg"|"xl"
  xs = body 13px, ultra-compact data-dense
  sm = body 14px, compact dashboard
  md = body 16px, default balanced
  lg = body 18px, readable/spacious
  xl = body 20px, large/editorial/accessibility
accentColor: hex e.g. "#2563eb"
accentSecondary: hex e.g. "#60a5fa"
backgroundColor: hex e.g. "#ffffff"
textColor: hex e.g. "#111827"
radius: 0|4|8|16|24
buttonStyle: "solid"|"outline"|"ghost"|"gradient"
cardHover: "lift"|"glow"|"border"|"none"
imageRatio: "1:1"|"4:3"|"16:9"|"portrait"|"wide"
divider: "none"|"line"|"shadow"|"wave"
pageMaxWidth: "sm"|"md"|"lg"|"xl"|"2xl"|"full"

Fine-grained color overrides (hex Ã¢â‚¬â€ set independently from accentColor/backgroundColor to establish visual hierarchy):
  region.header.bg_hex: hex Ã¢â‚¬â€ header bar background
  region.header.text_hex: hex Ã¢â‚¬â€ header text/icon color (default = auto contrast on header bg)
  region.footer.bg_hex: hex Ã¢â‚¬â€ footer background (default = backgroundColor)
  region.footer.text_hex: hex Ã¢â‚¬â€ footer text color
  region.main.bg_hex: hex Ã¢â‚¬â€ main content area background
  region.sidebar.bg_hex: hex Ã¢â‚¬â€ sidebar background (when nav is in sidebar position)
  region.border_hex: hex Ã¢â‚¬â€ default divider / border color
  component.card.bg_hex: hex Ã¢â‚¬â€ card tile background
  component.card.border_hex: hex Ã¢â‚¬â€ card border color
  button.primary.bg_hex: hex Ã¢â‚¬â€ primary button fill (default = accentColor)
  button.primary.text_hex: hex Ã¢â‚¬â€ primary button label color (default = auto contrast)
  button.secondary.bg_hex: hex Ã¢â‚¬â€ secondary button fill (default = surface)
  button.secondary.text_hex: hex Ã¢â‚¬â€ secondary button label color
  button.ghost.text_hex: hex Ã¢â‚¬â€ ghost/text button color (default = accentColor)
  button.danger.bg_hex: hex Ã¢â‚¬â€ danger/destructive button fill (default = #dc2626; use orange or deep red for softer themes)
  button.link.text_hex: hex Ã¢â‚¬â€ inline link color (default = accentColor)
  input.bg_hex: hex Ã¢â‚¬â€ input/searchbar field background
  input.border_hex: hex Ã¢â‚¬â€ input/searchbar border
  input.border_focus_hex: hex Ã¢â‚¬â€ input/searchbar active border and search submit button fill
  input.text_hex: hex Ã¢â‚¬â€ input/searchbar text color
  nav.bg_hex: hex Ã¢â‚¬â€ nav bar/sidebar background (default = region.header.bg_hex)
  nav.text_hex: hex Ã¢â‚¬â€ nav links/icon color (default = auto contrast on nav bg)
  table.header.bg_hex: hex Ã¢â‚¬â€ table column header background
  table.header.text_hex: hex Ã¢â‚¬â€ table column header text color
  badge.info.bg_hex: hex Ã¢â‚¬â€ info/status badge background (default = accentColor)
  text.muted.hex: hex Ã¢â‚¬â€ secondary/muted text color used in labels, captions, table headers

=== ROLE Ã¢â€ â€™ LAYOUT (non-negotiable, must match exactly) ===
role='object_collection'       Ã¢â€ â€™ layout: table|card|gallery|list  (per candidate direction)
role='child_collection'        Ã¢â€ â€™ same as object_collection
role='object_detail'           Ã¢â€ â€™ layout: detail,  component: DetailPanel or ProductDetailPanel
role='object_summary'          Ã¢â€ â€™ layout: detail,  component: DetailPanel
role='object_form'             Ã¢â€ â€™ layout: form,    component: ObjectForm
role='navigation'              Ã¢â€ â€™ layout: site-nav, component: NavBar
role='header'                  Ã¢â€ â€™ layout: any header template (app-header, glass-header, minimal-header, compact-header, dashboard-header, split-header, hero-header, tabbed-header, command-header)
role='footer'                  Ã¢â€ â€™ layout: any footer template (site-footer, compact-footer, app-footer, minimal-footer, mega-footer, cta-footer)
activity_action/activity_start/activity_tasks Ã¢â€ â€™ keep layout unchanged (chrome); other sections on activity pages Ã¢â€ â€™ infer: select/chooseÃ¢â€ â€™ card, enter/fillÃ¢â€ â€™ form, review/confirmÃ¢â€ â€™ detail

=== RULES ===
- nav/header chrome sections Ã¢â€ â€™ position="header" (or "sidebar" for sidebar nav)
- footer chrome sections Ã¢â€ â€™ position="footer"
- hero sections Ã¢â€ â€™ position="hero", col_span=12
- sidebar sections Ã¢â€ â€™ must include style.sidebar_side and style.sidebar_width
- Every page MUST have navigation (header nav OR sidebar NavBar)
- Data sections: omit style.color or use a semantic token alias only; exact colors belong in top-level tokens.
- Activity chrome (activity_action/activity_start/activity_tasks): keep layout as-is; content sections: infer layout from step name
"""

_DATA_SCHEMA = """
=== DATA, FIELD, AND BEHAVIOR FIELDS ===
sections[].attributes:
  List of real display fields, either field names or attribute objects.
  Supports related fields with dot notation, e.g. "seller.name".
  Attribute objects may use:
    {name, type?, readonly?, source?, render?, action?}
  Attributes are display fields only; do not treat them as query/SQL select lists.
  Static image URLs from search/MCP are never attributes.
  If a primary or related model has a real image-like field, include it for visual layouts
  such as card, gallery, detail, list item, profile, product, catalog, media, and hero.
  Image-like fields include type "image" or names such as image_url, photo_url,
  avatar_url, thumbnail_url, poster_url, cover_url, and logo_url.

sections[].field_layout:
  Use only slots consumed by the component.
  Card/Gallery slots: image, video, media, title, subtitle, primary, secondary, hidden.
  Table/List slots: columns, hidden.
  Detail slots: image, video, media, title, hero, fields, hidden.
  Form/Filter slots: fields, hidden.
  If a section has an image-like field in attributes, set field_layout.image to that
  field unless video/media is more specific. Do not hide other media fields unless asked.
  Per-field overrides live in field_layout.field_styles:
    {"field_name": {"order": 0, "col_span": 12, "height": "sm|md|lg|xl", "text_size": "xs|sm|md|lg|xl", "align": "left|center|right", "label": "show|hidden"}}

sections[].behavior:
  Use for workflow/search/navigation behavior, e.g. SearchBar/NavBar/IconActions.
  Collection components use behavior.item_click for whole-item interactions:
    {item_click: {type: "navigate", target_page: "Product_Detail", params: {"product_id": "$Product.product_id"}}}
  Render modes: text, link, button, badge.
  Action types: none, navigate, operation, copy, filter, expand, tooltip.

sections[].methods and sections[].item_actions:
  Use "methods" only for section-level actions that apply to the whole section.
    Examples: refresh products, generate summary, export section, batch validate.
  Use "item_actions" for per-record actions inside list/card/gallery/table sections.
    Examples: add this product to cart, view this order, approve this request, remove this item.
  Each item_action targets the current record of the section primary_model.
  Do not place per-record actions in methods. Do not place section-level actions in item_actions.
  Action objects may use {name, label, body?, parameters?, call_name?, target_model?}.

sections[].data_source:
  data_source.mode = "query"
  data_source.from.model must equal the section primary_model. It controls which
  records are returned and rendered.
  data_source.joins = optional list of joins:
    {type: "left|inner|right", model: "ModelName", on: "ModelA.field_id = ModelB.id"}
  Use joins to reference other classes for filters, sorting, or read-only context.
  Joins must not change the rendered result class. Do not emit data_source for
  ordinary sections unless joins are needed.

sections[].query:
  Optional retrieval constraints only. It is separate from attributes.
  select: exact primary fields or valid related dot notation.
  limit, offset, order_by, filters are allowed when the user asks for
  filtering/sorting/limits or the page semantics require them.

sections[].operations:
  CRUD flags or list. create/update/delete control row/form actions.
  select means choose/pick/multi-select, not read/view.

Static online image URLs:
  Use MCP/search URLs only when the user explicitly asks for online images/photos/logo/banner imagery.
  Put URLs in style.image_url or style.logo_url, never in attributes.
"""

_CANDIDATE_FULL_SCHEMA = f"""\nYou output layout + style decisions for an interface. DO NOT change: id, name, primary_model, class, attributes, operations, role, behavior, data_source, query, field_layout, methods, item_actions.

{_LAYOUT_SCHEMA}
- 3 candidates must be structurally different: vary nav placement, data section layouts, density, font, component treatment, or contained/wide page width. Use full width only when explicitly requested.
- Every candidate MUST include a top-level tokens object. tokens is the source of truth for exact colors/typography used by rendering.
- styling is a compact human-readable style summary; tokens must contain the complete concrete values for fine-grained rendering.
"""

_CANDIDATE_TOKENS_EXAMPLE = (
    '"tokens": {"accent.hex": "#hex", "color.secondary.hex": "#hex", '
    '"page.body.bg_hex": "#hex", "page.body.text_hex": "#hex", '
    '"region.header.bg_hex": "#hex", "region.header.text_hex": "#hex", '
    '"region.footer.bg_hex": "#hex", "region.footer.text_hex": "#hex", '
    '"region.main.bg_hex": "#hex", "region.sidebar.bg_hex": "#hex", "region.border_hex": "#hex", '
    '"component.card.bg_hex": "#hex", "component.card.border_hex": "#hex", '
    '"button.primary.bg_hex": "#hex", "button.primary.text_hex": "#hex", '
    '"button.secondary.bg_hex": "#hex", "button.secondary.text_hex": "#hex", '
    '"button.ghost.text_hex": "#hex", "button.danger.bg_hex": "#hex", "button.link.text_hex": "#hex", '
    '"input.bg_hex": "#hex", "input.border_hex": "#hex", "input.border_focus_hex": "#hex", "input.text_hex": "#hex", '
    '"nav.bg_hex": "#hex", "nav.text_hex": "#hex", '
    '"table.header.bg_hex": "#hex", "table.header.text_hex": "#hex", '
    '"badge.info.bg_hex": "#hex", "text.muted.hex": "#hex", '
    '"typography.body.size": "16px", "typography.label.size": "14px", "typography.caption.size": "12px"}'
)
