import { authAxios, useAuthStore } from '$auth/state/auth';
import { trackEvent } from '$lib/features/analytics/trackEvent';
import { Button, Modal, ModalClose, ModalDialog, Typography } from '@mui/joy';
import { AlignJustify, Code2, Database, GalleryHorizontal, GripVertical, HelpCircle, Info, LayoutGrid, Loader2, Maximize2, Minimize2, Monitor, PlayCircle, Plus, RefreshCw, Table2, User, Wand2 } from 'lucide-react';
import { startInterfaceTour } from './useInterfaceTour';
import { startWorkflowGuidance } from './useWorkflowGuidance';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { prototypeURL } from '$shared/globals';
import useLocalStorage from './useLocalStorage';

type LayoutOption = 'card' | 'list' | 'table' | 'detail' | 'gallery' | 'filter' | 'form'
    | 'activity_action'
    | 'promo-bar' | 'logo' | 'search-bar' | 'icon-actions' | 'nav-links' | 'main-header' | 'minimal-header'
    | 'commerce-header' | 'dashboard-header' | 'split-header' | 'app-header' | 'compact-header' | 'mega-header'
    | 'service-bar' | 'link-grid' | 'brand-strip' | 'compact-footer' | 'legal-footer' | 'newsletter-footer' | 'social-footer' | 'mega-footer'
    | 'site-nav' | 'site-footer';
type ColorOption = 'blue' | 'green' | 'purple' | 'orange' | 'rose' | 'slate';
type DensityOption = 'compact' | 'normal' | 'spacious';
type NavHeightOption = 'compact' | 'normal' | 'tall' | 'xl';
type DisplayModeOption = 'grid' | 'carousel' | 'banner';
type BannerHeightOption = 'sm' | 'md' | 'lg' | 'xl';
type ImageRatioOption = 'wide' | '16:9' | '4:3' | '1:1' | 'portrait';
type CardStyleOption = 'default' | 'product' | 'category' | 'compact';
type ListStyleOption = 'default' | 'product' | 'cart-item' | 'related';
type FormStyleOption = 'default' | 'auth' | 'step' | 'summary';
type ImagePositionOption = 'left' | 'top' | 'right';
type ImageSizeOption = 'sm' | 'md' | 'lg';
type ColSpanOption = 12 | 6 | 4 | 3;
type PositionOption = 'header' | 'hero' | 'main' | 'sidebar' | 'footer';
type RegionSelection = { region: 'sidebar'; side?: 'left' | 'right' | '' } | null;
type SidebarSideOption = 'left' | 'right';
type ShadowOption = 'none' | 'sm' | 'md' | 'lg' | 'xl';
type BorderOption = 'none' | 'light' | 'colored' | 'strong';
type BgOption = 'white' | 'light' | 'gray' | 'dark';
type HeaderStyleOption = 'default' | 'large' | 'small' | 'colored' | 'hidden';
type LogoSizeOption = 'sm' | 'md' | 'lg' | 'xl';
type LogoShapeOption = 'rounded' | 'circle' | 'square';
type LogoVariantOption = 'lockup' | 'image-only' | 'text-only';
type ActionVariantOption = 'link' | 'ghost' | 'button';
type AsyncStatus = 'idle' | 'ok' | 'error';

const CHROME_LAYOUTS: LayoutOption[] = [
    'promo-bar', 'logo', 'search-bar', 'icon-actions', 'nav-links', 'main-header', 'minimal-header',
    'commerce-header', 'dashboard-header', 'split-header', 'app-header', 'compact-header', 'mega-header',
    'service-bar', 'link-grid', 'brand-strip', 'compact-footer', 'legal-footer', 'newsletter-footer', 'social-footer', 'mega-footer', 'site-nav', 'site-footer',
];
const HEADER_LAYOUTS: LayoutOption[] = ['promo-bar', 'logo', 'search-bar', 'icon-actions', 'nav-links', 'main-header', 'minimal-header', 'commerce-header', 'dashboard-header', 'split-header', 'app-header', 'compact-header', 'mega-header', 'site-nav'];
const FOOTER_LAYOUTS: LayoutOption[] = ['service-bar', 'link-grid', 'brand-strip', 'compact-footer', 'legal-footer', 'newsletter-footer', 'social-footer', 'mega-footer', 'site-footer'];
const CHROME_LAYOUT_SET = new Set(CHROME_LAYOUTS);
const HEADER_LAYOUT_SET = new Set(HEADER_LAYOUTS);
const FOOTER_LAYOUT_SET = new Set(FOOTER_LAYOUTS);
const MAX_AUTO_PREVIEW_BYTES = 2_000_000;

const sectionRefId = (ref: any) => typeof ref === 'string' ? ref : ref?.value;

const LAYOUT_CONTROLS: Partial<Record<LayoutOption, readonly string[]>> = {
    table:   ['color', 'density', 'shadow', 'border', 'bg', 'header_style'],
    card:    ['display_mode', 'card_style', 'columns', 'banner_height', 'image_ratio', 'color', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label', 'seller_label', 'availability_label', 'delivery_label'],
    list:    ['list_style', 'color', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label', 'availability_label', 'delivery_label'],
    detail:  ['image_position', 'image_size', 'color', 'density', 'shadow', 'border', 'bg', 'header_style'],
    gallery: ['columns', 'color', 'density', 'shadow', 'border', 'bg', 'header_style'],
    filter:  ['color', 'density', 'bg'],
    form:    ['form_style', 'color', 'density', 'login_label', 'step_icon', 'total_label', 'cta_label', 'success_page'],
    activity_action: ['activity_label', 'activity_workflow_action', 'activity_target_page', 'activity_variant', 'activity_align', 'activity_size'],
};

const COMPONENT_CONTROLS: Record<string, readonly string[]> = {
    NavBar: ['methods', 'nav_height', 'density', 'bg', 'shadow', 'sidebar_side', 'sidebar_width'],
    Logo: ['text', 'logo_url', 'tagline', 'logo_size', 'logo_shape', 'logo_variant', 'density', 'bg', 'shadow'],
    BrandLockup: ['text', 'logo_url', 'tagline', 'logo_size', 'logo_shape', 'logo_variant', 'density', 'bg', 'shadow'],
    ImageLogo: ['text', 'logo_url', 'tagline', 'logo_size', 'logo_shape', 'logo_variant', 'density', 'bg', 'shadow'],
    IconActions: ['methods', 'action_variant', 'show_logout', 'logout_label', 'density'],
    SearchBar: ['text', 'density', 'bg', 'shadow', 'sidebar_side', 'sidebar_width'],
    SiteFooter: ['text', 'methods', 'density', 'bg', 'shadow'],
    FooterLinkGrid: ['methods', 'density', 'bg'],
    ProductCardGrid: ['display_mode', 'card_style', 'columns', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label', 'seller_label', 'availability_label', 'delivery_label'],
    CategoryTileGrid: ['display_mode', 'card_style', 'columns', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label'],
    PersonCardGrid: ['display_mode', 'card_style', 'columns', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label'],
    CardGrid: ['display_mode', 'card_style', 'columns', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label'],
    ObjectCardGrid: ['display_mode', 'card_style', 'columns', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label'],
    ImageCard: ['display_mode', 'card_style', 'columns', 'banner_height', 'image_ratio', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label'],
    ImageCardGrid: ['display_mode', 'card_style', 'columns', 'banner_height', 'image_ratio', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label'],
    DataTable: ['density', 'shadow', 'border', 'bg', 'header_style'],
    ObjectList: ['list_style', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label'],
    LineItemList: ['list_style', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label'],
    RelatedObjectList: ['list_style', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label'],
    ProductDetailPanel: ['image_position', 'image_size', 'density', 'shadow', 'border', 'bg', 'header_style'],
    MediaDetailPanel: ['image_position', 'image_size', 'density', 'shadow', 'border', 'bg', 'header_style'],
    ObjectDetailPanel: ['density', 'shadow', 'border', 'bg', 'header_style'],
    DetailPanel: ['density', 'shadow', 'border', 'bg', 'header_style'],
    SummaryPanel: ['density', 'shadow', 'border', 'bg', 'header_style', 'sidebar_side', 'sidebar_width'],
    ObjectForm: ['form_style', 'density', 'bg', 'cta_label', 'success_page'],
    AddressForm: ['form_style', 'density', 'bg', 'cta_label', 'success_page'],
    PaymentMethodForm: ['form_style', 'density', 'bg', 'cta_label', 'success_page'],
    ReviewForm: ['form_style', 'density', 'bg', 'cta_label', 'success_page'],
    FilterPanel: ['density', 'bg', 'sidebar_side', 'sidebar_width'],
};

const METHODS_HINTS: Partial<Record<LayoutOption, string>> = {
    'promo-bar':      'Each line = promo strip item (e.g. "Gratis verzending vanaf €25,-"). Text field = right-side CTA label.',
    'logo':           'Text field = brand name. Logo URL/tagline/size/shape are editable below.',
    'search-bar':     'Text field = search input placeholder.',
    'icon-actions':   'Each line = action label (e.g. "Inloggen", "♡", "Cart icon").',
    'nav-links':      'Line 1 = categories label. Lines 2–4 = extra nav links. Lines 5+ = top-right links.',
    'main-header':    'Text field = search placeholder.',
    'minimal-header': 'Text field = cart amount in header button (e.g. "0,00").',
    'commerce-header': 'Full commerce header with promo/search/actions/nav treatment.',
    'dashboard-header': 'Dense app dashboard header with workspace navigation.',
    'split-header': 'Dark split header with compact brand/search/action treatment.',
    'app-header': 'Application-style top bar for operational tools.',
    'compact-header': 'Compact one-row header for focused workflows.',
    'mega-header': 'Large navigation-heavy header for multi-page apps.',
    'service-bar':    'Each line = a service bar link in the footer.',
    'link-grid':      'Line 1 = column title. Lines 2+ = footer links in that column.',
    'brand-strip':    'Each line = a brand name shown in the brand strip.',
    'compact-footer': 'Small legal/status footer.',
    'legal-footer': 'Legal links and copyright-style footer.',
    'newsletter-footer': 'Footer with subscribe/CTA emphasis.',
    'social-footer': 'Footer with brand/social/action links.',
    'mega-footer': 'Large multi-column footer.',
    'site-nav':       'Lines 1–3: promo strip items. Line 4: right-side highlight text.',
    'site-footer':    'Each line becomes a service-bar link in the footer.',
};

const PROMPT_GUIDE_EXAMPLES = [
    {
        title: 'Generate 3 Distinct Candidates',
        prompt: 'Generate 3 visually distinct candidates based on the current system and existing pages. Keep the domain models, page purpose, CRUD permissions, workflow actions, and data relationships correct. Candidate 1 should be a polished dashboard with wide top navigation and compact summary sections. Candidate 2 should be a split workspace with useful left or right sidebar content. Candidate 3 should be a more editorial/product-style layout with a stronger hero or header region and richer cards. Do not drop important sections.'
    },
    {
        title: 'Header, Footer, Navigation Variety',
        prompt: 'Generate 3 candidates with very different header, footer, and navigation patterns. Use the current app pages as the navigation source. Candidate 1 should use top nav integrated into a clean app header. Candidate 2 should use a compact command header with separate horizontal nav. Candidate 3 should use a full-height sidebar nav with a simpler header. If the header does not contain page navigation, add a separate navbar. Footer should mirror page navigation with useful links, not become an action button. Use light text on dark header/footer backgrounds.'
    },
    {
        title: 'Different Region Placement',
        prompt: 'Create 3 layout variants that organize the same system pages in meaningfully different ways. Do not put every section in the main region. Use main, left sidebar, right sidebar, hero/header, and footer regions appropriately. Put overviews, filters, or summaries in sidebars when useful. Put primary records and main actions in the main region. Keep each page readable, balanced, and suitable for repeated business use.'
    },
    {
        title: 'Marketplace Style',
        prompt: 'Design this marketplace app with rich but practical ecommerce UI. Keep Customer and Seller workflows correct. Use product browsing pages with strong search, category navigation, product cards, comparison-friendly grids, and clear detail navigation. Seller pages should feel like an operational dashboard with product management, order management, and performance sections. Generate 3 candidates with different ecommerce visual styles, but keep all navigation and item detail links working.'
    },
    {
        title: 'Hospital Management Style',
        prompt: 'Design this hospital management system as a calm professional operations app. Keep Patient, Doctor, and Admin pages aligned with their real responsibilities. Use clear navigation, compact data tables, patient and appointment detail panels, status badges, and action areas. Generate 3 candidates with different layouts: clinical dashboard, sidebar workspace, and appointment-focused command center. Do not remove medically relevant sections or mix actor responsibilities.'
    },
    {
        title: 'Regenerate Selected Candidate',
        prompt: 'Regenerate based on the selected candidate. Preserve the selected candidate page structure, section purpose, query constraints, item navigation, operations, and workflow behavior unless I explicitly ask to change them. Only improve the visual design: make spacing, typography, header, navigation, footer, cards, tables, and sidebar placement more polished. Keep the same page responsibilities and do not drop sections.'
    },
    {
        title: 'More Expressive, Still Correct',
        prompt: 'Make the design more visually expressive while staying system-correct. You may change layout, region placement, styling, density, card/table/gallery choices, header/footer/nav style, and visual hierarchy. Do not change the meaning of pages, models, CRUD permissions, workflow actions, target pages, or required relationships. Keep navigation usable on every page.'
    },
    {
        title: 'Color, Sidebar, Width, and Font Size',
        prompt: 'Use teal accent, right sidebar navigation, full width main content, table layout, sidebar width 4, make body text 18px.'
    },
    {
        title: 'Exact Header and Button Colors',
        prompt: 'Make the header green (#16a34a), primary buttons black (#000000), button text white (#ffffff), navigation teal (#0f766e), footer near-black (#111827), and table headers pale yellow (#fef3c7). Do not change the layout, pages, sections, data fields, actions, or navigation structure.'
    },
    {
        title: 'Precise Region Color Targets',
        prompt: 'Only change colors. Use a white page background, dark charcoal body text, emerald header background, white header text, black primary buttons, slate secondary buttons, light gray cards, and thin neutral table borders. Keep spacing, section placement, widths, typography scale, and all content the same.'
    },
    {
        title: 'Header Only Color Change',
        prompt: 'Only change the header styling. Make the header background forest green (#166534), header text white (#ffffff), and header navigation links light mint (#dcfce7). Keep buttons, cards, tables, footer, layout, widths, and content unchanged.'
    },
    {
        title: 'Button Only Color Change',
        prompt: 'Only change button colors. Make primary buttons black (#000000) with white text (#ffffff), secondary buttons white with black text and a light gray border, and link buttons dark teal. Do not change headers, tables, cards, spacing, layout, or page structure.'
    },
    {
        title: 'Table Color Targets',
        prompt: 'Only update table styling. Use pale yellow table headers (#fef3c7), dark slate table header text (#1f2937), neutral table borders (#d1d5db), and white table rows. Keep all columns, filters, actions, layout, and surrounding sections the same.'
    },
    {
        title: 'Dark Header and Footer',
        prompt: 'Make the header and footer near-black (#111827) with white text. Keep the main page background white, cards light gray, primary buttons black, and table headers neutral light gray. Do not change the page layout or remove any sections.'
    },
    {
        title: 'Green Header, Black Buttons Smoke Test',
        prompt: 'Test color rendering with a green header (#16a34a), black primary buttons (#000000), white button text (#ffffff), teal navigation (#0f766e), near-black footer (#111827), and pale yellow table headers (#fef3c7). Preserve the existing layout exactly.'
    },
    {
        title: 'Named Colors Without Hex',
        prompt: 'Use a green header, black primary buttons, white button text, teal navigation, light gray cards, and pale yellow table headers. Keep the layout and all page content unchanged.'
    },
    {
        title: 'Brand Palette Across Regions',
        prompt: 'Apply this brand palette without changing structure: emerald header, teal navigation, black primary buttons, slate secondary buttons, white content background, light gray cards, pale yellow table headers, and near-black footer. Preserve all pages, fields, actions, and section placement.'
    },
    {
        title: 'Remove Purple and Green Defaults',
        prompt: 'Do not use purple buttons or generic green accents. Use black primary buttons, neutral gray borders, white cards, a teal navigation bar, and a dark charcoal footer. Keep the current layout and content.'
    },
    {
        title: 'Amber Form with Larger Type',
        prompt: 'Change to amber accent, compact form layout, wide main content, larger font size, extra large titles.'
    },
    {
        title: 'Mixed Color Targets and Typography',
        prompt: 'Use navy header, beige cards, gold buttons, contained main layout, left sidebar navigation, smaller table text and bigger hero title.'
    },
];

const POSITION_OPTIONS: { value: PositionOption; label: string; bg: string; color: string; border: string }[] = [
    { value: 'header',  label: 'Header',  bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' },
    { value: 'hero',    label: 'Hero',    bg: '#faf5ff', color: '#7e22ce', border: '#e9d5ff' },
    { value: 'main',    label: 'Main',    bg: '#f0fdf4', color: '#15803d', border: '#bbf7d0' },
    { value: 'sidebar', label: 'Sidebar', bg: '#fff7ed', color: '#c2410c', border: '#fed7aa' },
    { value: 'footer',  label: 'Footer',  bg: '#f8fafc', color: '#475569', border: '#e2e8f0' },
];

interface InterfaceDesignerProps {
    interfaceId?: string | null;
    systemId?: string | null;
}

type LayoutGroup = { label: string; options: { value: LayoutOption; label: string; icon: React.ReactNode }[] };
const LAYOUT_GROUPS: LayoutGroup[] = [
    { label: 'Generic', options: [
        { value: 'table',   label: 'Table',   icon: <Table2 size={13} /> },
        { value: 'card',    label: 'Card',    icon: <LayoutGrid size={13} /> },
        { value: 'list',    label: 'List',    icon: <AlignJustify size={13} /> },
        { value: 'detail',  label: 'Detail',  icon: <Code2 size={13} /> },
        { value: 'gallery', label: 'Gallery', icon: <GalleryHorizontal size={13} /> },
        { value: 'filter',  label: 'Filter',  icon: <AlignJustify size={13} /> },
        { value: 'form',    label: 'Form',    icon: <Code2 size={13} /> },
        { value: 'activity_action', label: 'Activity Button', icon: <Code2 size={13} /> },
    ]},
    { label: 'Header', options: [
        { value: 'promo-bar',      label: 'Promo Bar',    icon: <Monitor size={13} /> },
        { value: 'logo',           label: 'Logo',         icon: <Monitor size={13} /> },
        { value: 'search-bar',     label: 'Search Bar',   icon: <Monitor size={13} /> },
        { value: 'icon-actions',   label: 'Icon Actions', icon: <Monitor size={13} /> },
        { value: 'nav-links',      label: 'Nav Links',    icon: <Monitor size={13} /> },
        { value: 'main-header',    label: 'Main Header',  icon: <Monitor size={13} /> },
        { value: 'minimal-header', label: 'Min. Header',  icon: <Monitor size={13} /> },
        { value: 'commerce-header', label: 'Commerce',    icon: <Monitor size={13} /> },
        { value: 'dashboard-header', label: 'Dashboard',  icon: <Monitor size={13} /> },
        { value: 'split-header',    label: 'Split',       icon: <Monitor size={13} /> },
        { value: 'app-header',      label: 'App Header',  icon: <Monitor size={13} /> },
        { value: 'compact-header',  label: 'Compact',     icon: <Monitor size={13} /> },
        { value: 'mega-header',     label: 'Mega Header', icon: <Monitor size={13} /> },
    ]},
    { label: 'Footer', options: [
        { value: 'service-bar', label: 'Service Bar', icon: <Monitor size={13} /> },
        { value: 'link-grid',   label: 'Link Grid',   icon: <Monitor size={13} /> },
        { value: 'brand-strip', label: 'Brand Strip', icon: <Monitor size={13} /> },
        { value: 'compact-footer', label: 'Compact', icon: <Monitor size={13} /> },
        { value: 'legal-footer', label: 'Legal', icon: <Monitor size={13} /> },
        { value: 'newsletter-footer', label: 'Newsletter', icon: <Monitor size={13} /> },
        { value: 'social-footer', label: 'Social', icon: <Monitor size={13} /> },
        { value: 'mega-footer', label: 'Mega Footer', icon: <Monitor size={13} /> },
        { value: 'site-nav',    label: 'Site Nav',    icon: <Monitor size={13} /> },
        { value: 'site-footer', label: 'Site Footer', icon: <Monitor size={13} /> },
    ]},
];

const normalizePreviewPageName = (value: any) =>
    String(value || '')
        .replace(/^templates\//i, '')
        .replace(/\.html?$/i, '')
        .replace(/[^a-z0-9]+/gi, '')
        .toLowerCase();

const previewPathPageKey = (path: any, interfaceName?: string) => {
    const stem = String(path || '').split('/').pop()?.replace(/\.html?$/i, '') || '';
    const interfacePrefix = interfaceName ? `${String(interfaceName).toLowerCase()}_` : '';
    const withoutKnownPrefix = interfacePrefix && stem.toLowerCase().startsWith(interfacePrefix)
        ? stem.slice(interfacePrefix.length)
        : stem.replace(/^[^_]+_/, '');
    return normalizePreviewPageName(withoutKnownPrefix);
};

const previewFileMatchesPage = (file: any, page: any, interfaceName?: string) => {
    const pageKey = normalizePreviewPageName(page?.name || page?.id);
    if (!pageKey) return false;
    if (normalizePreviewPageName(file?.page) === pageKey) return true;

    return previewPathPageKey(file?.path, interfaceName) === pageKey;
};

const slugifyPathSegment = (value: string | undefined) => {
    let result = '';
    for (const char of String(value || '').trim().toLowerCase()) {
        result += /[a-z0-9_]/.test(char) ? char : '_';
    }
    let start = 0;
    let end = result.length;
    while (start < end && result[start] === '_') start += 1;
    while (end > start && result[end - 1] === '_') end -= 1;
    return result.slice(start, end);
};

const djangoName = (value: string | undefined) =>
    slugifyPathSegment(value);

const trimTrailingSlashes = (value: string) => {
    let end = value.length;
    while (end > 0 && value[end - 1] === '/') end -= 1;
    return value.slice(0, end);
};

const livePathForPage = (interfaceName: string | undefined, page: any) => {
    const app = djangoName(interfaceName);
    if (!app) return '/';
    if (!page || String(page?.id || page?.name || '').toLowerCase() === 'task') return `/${app}/`;
    const pageType = String(page?.type?.value || page?.type || '').toLowerCase();
    if (pageType === 'activity') return `/${app}/`;
    const pageName = djangoName(page?.name || page?.id);
    return pageName ? `/${app}/render_${app}_${pageName}` : `/${app}/`;
};

const normalizeDesignTokens = (raw: any, styling: any) => {
    const tokens = raw ? { ...raw } : {};
    [
        'region.header.bg_hex', 'region.header.text_hex',
        'region.footer.bg_hex', 'region.footer.text_hex',
        'region.main.bg_hex', 'region.sidebar.bg_hex', 'region.border_hex',
        'component.card.bg_hex', 'component.card.border_hex',
        'color.secondary.hex',
        'button.primary.bg_hex', 'button.primary.text_hex',
        'button.secondary.bg_hex', 'button.secondary.text_hex',
        'button.ghost.text_hex', 'button.danger.bg_hex', 'button.link.text_hex',
        'input.bg_hex', 'input.border_hex', 'input.border_focus_hex', 'input.text_hex',
        'nav.bg_hex', 'nav.text_hex',
        'table.header.bg_hex', 'table.header.text_hex',
        'badge.info.bg_hex', 'text.muted.hex',
    ].forEach((key) => {
        if ((tokens[key] == null || tokens[key] === '') && styling?.[key]) {
            tokens[key] = styling[key];
        }
    });
    const defaultBlues = new Set(['', '#2563eb', '#0000a4', 'var(--accent)']);
    const stylingAccent = styling?.accentColor || styling?.accent_color;
    const existingAccent = tokens['accent.hex'];
    const accent = stylingAccent && (existingAccent == null || defaultBlues.has(String(existingAccent)))
        ? stylingAccent
        : existingAccent;
    if (!accent) return tokens;
    tokens['accent.hex'] = accent;
    if ((tokens['color.secondary.hex'] == null || tokens['color.secondary.hex'] === '') && styling?.accentSecondary) {
        tokens['color.secondary.hex'] = styling.accentSecondary;
    }
    ['region.header.bg_hex', 'region.footer.bg_hex', 'button.primary.bg_hex', 'button.primary.border_hex', 'input.border_focus_hex'].forEach((key) => {
        if (tokens[key] == null || defaultBlues.has(String(tokens[key]))) tokens[key] = accent;
    });
    if (tokens['region.header.text_hex'] == null || tokens['region.header.text_hex'] === '') {
        tokens['region.header.text_hex'] = '#ffffff';
    }
    if (tokens['region.footer.text_hex'] == null || tokens['region.footer.text_hex'] === '') {
        tokens['region.footer.text_hex'] = '#ffffff';
    }
    return tokens;
};

const COMPONENT_OPTIONS_BY_LAYOUT: Partial<Record<LayoutOption, string[]>> = {
    gallery: ['ProductCardGrid', 'CategoryTileGrid', 'PersonCardGrid', 'CardGrid'],
    card: ['ProductCardGrid', 'CategoryTileGrid', 'PersonCardGrid', 'CardGrid', 'ImageCard', 'ImageCardGrid', 'SummaryPanel'],
    table: ['DataTable', 'ObjectList', 'LineItemList', 'RelatedObjectList'],
    list: ['ObjectList', 'LineItemList', 'RelatedObjectList'],
    detail: ['ProductDetailPanel', 'DetailPanel', 'SummaryPanel'],
    form: ['ObjectForm', 'AddressForm', 'PaymentMethodForm', 'ReviewForm'],
    filter: ['FilterPanel', 'SearchBar'],
    'search-bar': ['SearchBar'],
    'logo': ['Logo', 'BrandLockup', 'ImageLogo'],
    'main-header': ['HeaderTemplate', 'NavBar'],
    'minimal-header': ['HeaderTemplate', 'NavBar'],
    'commerce-header': ['HeaderTemplate'],
    'dashboard-header': ['HeaderTemplate'],
    'split-header': ['HeaderTemplate'],
    'app-header': ['HeaderTemplate'],
    'compact-header': ['HeaderTemplate'],
    'mega-header': ['HeaderTemplate'],
    'site-nav': ['NavBar'],
    'nav-links': ['NavBar'],
    'icon-actions': ['IconActions'],
    'site-footer': ['FooterTemplate', 'SiteFooter', 'FooterLinkGrid'],
    'compact-footer': ['FooterTemplate', 'SiteFooter'],
    'legal-footer': ['FooterTemplate', 'SiteFooter'],
    'newsletter-footer': ['FooterTemplate', 'SiteFooter'],
    'social-footer': ['FooterTemplate', 'SiteFooter'],
    'mega-footer': ['FooterTemplate', 'SiteFooter', 'FooterLinkGrid'],
    'link-grid': ['FooterLinkGrid'],
    'service-bar': ['FooterTemplate', 'SiteFooter'],
    'brand-strip': ['FooterTemplate', 'SiteFooter'],
    activity_action: ['WorkflowActionButton', 'StartWorkflowButton'],
};

const FIELD_LAYOUT_SLOTS: Record<string, { slot: string; label: string; multiple?: boolean }[]> = {
    ProductCardGrid: [
        { slot: 'image', label: 'Image' },
        { slot: 'video', label: 'Video' },
        { slot: 'title', label: 'Title' },
        { slot: 'subtitle', label: 'Subtitle' },
        { slot: 'primary', label: 'Primary' },
        { slot: 'secondary', label: 'Secondary', multiple: true },
        { slot: 'hidden', label: 'Hidden', multiple: true },
    ],
    CategoryTileGrid: [
        { slot: 'image', label: 'Image' },
        { slot: 'title', label: 'Title' },
        { slot: 'subtitle', label: 'Subtitle' },
        { slot: 'secondary', label: 'Secondary', multiple: true },
        { slot: 'hidden', label: 'Hidden', multiple: true },
    ],
    PersonCardGrid: [
        { slot: 'image', label: 'Avatar' },
        { slot: 'title', label: 'Name' },
        { slot: 'subtitle', label: 'Role' },
        { slot: 'secondary', label: 'Secondary', multiple: true },
        { slot: 'hidden', label: 'Hidden', multiple: true },
    ],
    CardGrid: [
        { slot: 'media', label: 'Media' },
        { slot: 'title', label: 'Title' },
        { slot: 'subtitle', label: 'Subtitle' },
        { slot: 'primary', label: 'Primary' },
        { slot: 'secondary', label: 'Secondary', multiple: true },
        { slot: 'hidden', label: 'Hidden', multiple: true },
    ],
    ImageCard: [
        { slot: 'image', label: 'Image' },
        { slot: 'media', label: 'Extra media', multiple: true },
        { slot: 'title', label: 'Title' },
        { slot: 'subtitle', label: 'Subtitle' },
        { slot: 'primary', label: 'Primary' },
        { slot: 'secondary', label: 'Secondary', multiple: true },
        { slot: 'hidden', label: 'Hidden', multiple: true },
    ],
    ImageCardGrid: [
        { slot: 'image', label: 'Image' },
        { slot: 'media', label: 'Extra media', multiple: true },
        { slot: 'title', label: 'Title' },
        { slot: 'subtitle', label: 'Subtitle' },
        { slot: 'primary', label: 'Primary' },
        { slot: 'secondary', label: 'Secondary', multiple: true },
        { slot: 'hidden', label: 'Hidden', multiple: true },
    ],
    DataTable: [{ slot: 'columns', label: 'Columns', multiple: true }, { slot: 'hidden', label: 'Hidden', multiple: true }],
    ObjectList: [{ slot: 'columns', label: 'Fields', multiple: true }, { slot: 'hidden', label: 'Hidden', multiple: true }],
    LineItemList: [{ slot: 'columns', label: 'Line fields', multiple: true }, { slot: 'hidden', label: 'Hidden', multiple: true }],
    RelatedObjectList: [{ slot: 'columns', label: 'Related fields', multiple: true }, { slot: 'hidden', label: 'Hidden', multiple: true }],
    ProductDetailPanel: [
        { slot: 'image', label: 'Image' },
        { slot: 'video', label: 'Video' },
        { slot: 'title', label: 'Title' },
        { slot: 'hero', label: 'Hero fields', multiple: true },
        { slot: 'fields', label: 'Detail fields', multiple: true },
        { slot: 'hidden', label: 'Hidden', multiple: true },
    ],
    DetailPanel: [
        { slot: 'title', label: 'Title' },
        { slot: 'hero', label: 'Hero fields', multiple: true },
        { slot: 'fields', label: 'Detail fields', multiple: true },
        { slot: 'hidden', label: 'Hidden', multiple: true },
    ],
    SummaryPanel: [
        { slot: 'title', label: 'Title' },
        { slot: 'fields', label: 'Summary fields', multiple: true },
        { slot: 'hidden', label: 'Hidden', multiple: true },
    ],
    ObjectForm: [{ slot: 'fields', label: 'Editable fields', multiple: true }, { slot: 'hidden', label: 'Hidden', multiple: true }],
    AddressForm: [{ slot: 'fields', label: 'Address fields', multiple: true }, { slot: 'hidden', label: 'Hidden', multiple: true }],
    PaymentMethodForm: [{ slot: 'fields', label: 'Payment fields', multiple: true }, { slot: 'hidden', label: 'Hidden', multiple: true }],
    ReviewForm: [{ slot: 'fields', label: 'Review fields', multiple: true }, { slot: 'hidden', label: 'Hidden', multiple: true }],
    FilterPanel: [{ slot: 'fields', label: 'Filter fields', multiple: true }, { slot: 'hidden', label: 'Hidden', multiple: true }],
    SearchBar: [{ slot: 'fields', label: 'Search fields', multiple: true }, { slot: 'hidden', label: 'Hidden', multiple: true }],
};

const COL_SPAN_OPTIONS: { value: ColSpanOption; label: string }[] = [
    { value: 12, label: 'Full' },
    { value: 6,  label: '1/2' },
    { value: 4,  label: '1/3' },
    { value: 3,  label: '1/4' },
];

const COLOR_OPTIONS: ColorOption[] = ['blue', 'green', 'purple', 'orange', 'rose', 'slate'];
const COLOR_HEX: Record<ColorOption, string> = {
    blue: '#3b82f6', green: '#22c55e', purple: '#a855f7',
    orange: '#f97316', rose: '#f43f5e', slate: '#64748b',
};

const statusTone = (status: string, idle: { border: string; background: string; color: string }) => {
    if (status === 'ok') {
        return { border: '#86efac', background: '#f0fdf4', color: '#16a34a' };
    }
    if (status === 'error') {
        return { border: '#fca5a5', background: '#fef2f2', color: '#dc2626' };
    }
    return idle;
};

const statusLabel = (status: string, ok: string, error: string, idle: string) => {
    if (status === 'ok') return ok;
    if (status === 'error') return error;
    return idle;
};

const spacingTokensFor = (value: string) => {
    if (value === '12px') {
        return { 'spacing.sm': '6px', 'spacing.md': value, 'spacing.lg': '18px', 'spacing.xl': '24px' };
    }
    if (value === '20px') {
        return { 'spacing.sm': '10px', 'spacing.md': value, 'spacing.lg': '32px', 'spacing.xl': '40px' };
    }
    return { 'spacing.sm': '8px', 'spacing.md': value, 'spacing.lg': '24px', 'spacing.xl': '32px' };
};

const getPageTypeValue = (page: any) => typeof page?.type === 'string' ? page.type : page?.type?.value;
const isActivityActionSection = (section: any) => {
    const layout = typeof section?.layout === 'string' ? section.layout : section?.layout?.value;
    return section?.type === 'activity_action' || layout === 'activity_action';
};
const makeActivityActionSection = (page: any) => {
    const label = page?.action?.label || page?.name || 'Complete step';
    return {
        id: `activity-action-${page?.id || label}`,
        name: label,
        label,
        type: 'activity_action',
        layout: 'activity_action',
        class: '',
        operations: { create: false, update: false, delete: false },
        attributes: [],
        methods: [],
        col_span: 12,
        position: 'main',
        style: { variant: 'button', align: 'right', size: 'lg' },
        workflow: { action: 'complete' },
    };
};

const makeChromeSection = (layout: LayoutOption, position: PositionOption) => {
    const label = layout
        .split('-')
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
    const methods = layout === 'logo' || layout === 'search-bar' || layout === 'minimal-header'
        ? []
        : [{ name: layout === 'link-grid' ? 'Customer service' : 'Contact' }];
    let text = '';
    if (layout === 'logo') {
        text = 'Brand';
    } else if (layout === 'search-bar') {
        text = 'Search products';
    } else if (layout === 'minimal-header') {
        text = '0,00';
    }
    return {
        id: `${position}-${layout}-${Date.now()}`,
        name: label,
        label,
        layout,
        class: '',
        operations: { create: false, update: false, delete: false },
        attributes: [],
        methods,
        text,
        col_span: 12,
        position,
        style: {},
    };
};

export const InterfaceDesigner: React.FC<InterfaceDesignerProps> = ({ interfaceId, systemId }) => {
    const storagePrefix = interfaceId || 'new-interface';
    const [sections, setSections] = useLocalStorage(`interface:${storagePrefix}:sections`, []);
    const [pages, setPages] = useLocalStorage(`interface:${storagePrefix}:pages`, []);
    const [styling, setStyling] = useLocalStorage(`interface:${storagePrefix}:styling`, {});
    const [tokens, setTokens] = useLocalStorage(`interface:${storagePrefix}:tokens`, {});

    const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
    const [selectedRegion, setSelectedRegion] = useState<RegionSelection>(null);
    const [previewHtml, setPreviewHtml] = useState<string>('');
    const [previewError, setPreviewError] = useState('');
    const [previewPageIndex, setPreviewPageIndex] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isSeedingData, setIsSeedingData] = useState(false);
    const [seedStatus, setSeedStatus] = useState<AsyncStatus>('idle');
    const [isMapping, setIsMapping] = useState(false);
    const [mapStatus, setMapStatus] = useState<AsyncStatus>('idle');
    const [isSyncingLive, setIsSyncingLive] = useState(false);
    const [syncStatus, setSyncStatus] = useState<AsyncStatus>('idle');
    const [isVisualChecking, setIsVisualChecking] = useState(false);
    const [visualCheckStatus, setVisualCheckStatus] = useState<AsyncStatus>('idle');
    const [visualCheckSummary, setVisualCheckSummary] = useState('');
    const [previewMode, setPreviewMode] = useState<'design' | 'live'>('design');
    const [isFullScreen, setIsFullScreen] = useState(false);
    const [isMetadataOpen, setIsMetadataOpen] = useState(false);
    const [isMetadataExpanded, setIsMetadataExpanded] = useState(false);
    const [isLoadingMetadata, setIsLoadingMetadata] = useState(false);
    const [metadataJson, setMetadataJson] = useState('');
    const [metadataError, setMetadataError] = useState('');

    // First-time tour banner
    const TOUR_SEEN_KEY = 'studio_interface_tour_seen';
    const [showTourBanner, setShowTourBanner] = useState(false);

    useEffect(() => {
        if (!localStorage.getItem(TOUR_SEEN_KEY)) {
            const t = setTimeout(() => setShowTourBanner(true), 800);
            return () => clearTimeout(t);
        }
    }, []);

    useEffect(() => {
        trackEvent('session_start', { interface_id: interfaceId, system_id: systemId });
    }, [interfaceId]);

    const dismissTourBanner = () => {
        localStorage.setItem(TOUR_SEEN_KEY, '1');
        setShowTourBanner(false);
    };

    const startTour = () => {
        localStorage.setItem(TOUR_SEEN_KEY, '1');
        setShowTourBanner(false);
        startInterfaceTour({
            switchToExplore: () => setDesignMode('explore'),
            switchToRefine: () => setDesignMode('refine'),
        });
    };

    // Explore / Refine mode
    const [designMode, setDesignMode] = useState<'explore' | 'refine'>('refine');
    const [candidates, setCandidates] = useState<any[]>([]);
    const [explorePrompt, setExplorePrompt] = useState('');
    const [isGeneratingCandidates, setIsGeneratingCandidates] = useState(false);
    const [candidateStatus, setCandidateStatus] = useState('');
    const [previewCandidateIdx, setPreviewCandidateIdx] = useState<number | null>(null);

    const containerRef = useRef<HTMLDivElement>(null);

    const toggleBrowserFullScreen = () => {
        if (containerRef.current == null) return;
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            containerRef.current.requestFullscreen().catch(err => {
                console.error(`Error attempting to enable full-screen mode: ${err.message}`);
            });
        }
    };
    const [liveKey, setLiveKey] = useState(0);
    const [liveUser, setLiveUser] = useState('jan_devries');
    const [isEditingLiveUser, setIsEditingLiveUser] = useState(false);
    const [liveUserDraft, setLiveUserDraft] = useState('');

    const [currentPrompt, setCurrentPrompt] = useState('');
    const [isLoadingAgent, setIsLoadingAgent] = useState(false);
    const [agentStatus, setAgentStatus] = useState('');
    const [isAIExpanded, setIsAIExpanded] = useState(true);
    const [isPromptGuideOpen, setIsPromptGuideOpen] = useState(false);
    const [promptGuideTarget, setPromptGuideTarget] = useState<'explore' | 'refine'>('refine');
    const [isFieldComposerOpen, setIsFieldComposerOpen] = useState(false);
    const [systemClassifiers, setSystemClassifiers] = useState<any[]>([]);
    const [currentInterface, setCurrentInterface] = useState<any>(null);
    const [draggedField, setDraggedField] = useState<string | null>(null);

    const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const hotReloadTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    // Timestamp set whenever sections/pages are loaded from DB — saves within 500ms of a DB load are skipped to avoid write-back loops.
    // Initialized to Date.now() so the initial localStorage-seeded render is also skipped.
    const dbLoadTimestamp = useRef(Date.now());
    // Capture latest sections/pages/previewPageIndex/styling for the debounced callback
    const latestState = useRef({ sections, pages, previewPageIndex, styling, tokens });
    useEffect(() => { latestState.current = { sections, pages, previewPageIndex, styling, tokens }; }, [sections, pages, previewPageIndex, styling, tokens]);

    useEffect(() => {
        if (!systemId) return;
        let cancelled = false;
        authAxios.get(`/v1/metadata/systems/${systemId}/classifiers/`)
            .then((res) => { if (!cancelled) setSystemClassifiers(Array.isArray(res.data) ? res.data : []); })
            .catch(() => { if (!cancelled) setSystemClassifiers([]); });
        return () => { cancelled = true; };
    }, [systemId]);

    useEffect(() => {
        if (!interfaceId) return;
        let cancelled = false;
        authAxios.get(`/v1/metadata/interfaces/${interfaceId}/`)
            .then((res) => {
                if (cancelled) return;
                const iface = res.data as any;
                const data = iface?.data || {};
                setCurrentInterface(iface);
                dbLoadTimestamp.current = Date.now();
                setSections(data.sections || []);
                setPages(data.pages || []);
                setStyling(data.styling || {});
                setTokens(normalizeDesignTokens(data.tokens || {}, data.styling || {}));
                setPreviewPageIndex(0);
                setPreviewCandidateIdx(null);
            })
            .catch(() => {
                if (!cancelled) setCurrentInterface(null);
            });
        return () => { cancelled = true; };
    }, [interfaceId]);

    useEffect(() => {
        const pageList = pages as any[];
        const sectionList = sections as any[];
        if (!Array.isArray(pageList) || !Array.isArray(sectionList) || pageList.length === 0) return;

        let changed = false;
        const nextSections = [...sectionList];
        const nextPages = pageList.map((page: any) => {
            if (getPageTypeValue(page) !== 'activity') return page;
            const refs = page.sections || [];
            const hasActivityButton = refs.some((ref: any) => {
                const sectionId = typeof ref === 'string' ? ref : ref?.value;
                const section = nextSections.find((s: any) => s.id === sectionId);
                return isActivityActionSection(section);
            });
            if (hasActivityButton) return page;

            const activityButton = makeActivityActionSection(page);
            if (!nextSections.some((s: any) => s.id === activityButton.id)) {
                nextSections.push(activityButton);
            }
            changed = true;
            return {
                ...page,
                sections: [
                    ...refs,
                    { label: activityButton.name, value: activityButton.id },
                ],
            };
        });

        if (changed) {
            setSections(nextSections);
            setPages(nextPages);
        }
    }, [pages, sections, setPages, setSections]);

    const resolveLiveUser = useCallback(() => {
        const actor = systemClassifiers.find((cls: any) => String(cls?.id) === String(currentInterface?.actor));
        const actorName = String(actor?.data?.name || currentInterface?.name || '').toLowerCase();
        if (actorName.includes('seller')) return 'techstore';
        if (actorName.includes('customer')) return 'jan_devries';
        if (actorName.includes('system')) return 'system';
        if (actorName.includes('applicant')) return 'demo-applicant';
        if (actorName.includes('loan') && actorName.includes('officer')) return 'demo-loan-officer';
        return slugifyPathSegment(actorName) || 'jan_devries';
    }, [currentInterface, systemClassifiers]);

    useEffect(() => {
        setLiveUser(resolveLiveUser());
    }, [resolveLiveUser]);

    const selectedSection = (sections as any[]).find((s: any) => s.id === selectedSectionId);
    const selectedCandidate = (
        designMode === 'explore'
        && previewCandidateIdx !== null
        && candidates[previewCandidateIdx]
    ) ? candidates[previewCandidateIdx] : null;
    const visiblePages = (
        designMode === 'explore'
        && previewCandidateIdx !== null
        && Array.isArray(candidates[previewCandidateIdx]?.pages)
    )
        ? candidates[previewCandidateIdx].pages
        : pages;
    const selectedVisiblePage = (visiblePages as any[])[previewPageIndex];
    const selectedCandidateHtml = selectedCandidate
        ? (
            (selectedCandidate.preview_files || []).find((f: any) =>
                previewFileMatchesPage(f, selectedVisiblePage, currentInterface?.name)
            )?.content
            || selectedCandidate.preview_html
        )
        : '';

    // postMessage -> select section from iframe click / drag-reorder
    useEffect(() => {
        const handler = (e: MessageEvent) => {
            if (e.data?.type === 'navigate-page') {
                const targetPage = e.data.page;
                const pageIndex = (latestState.current.pages as any[]).findIndex((page: any) =>
                    page?.name === targetPage || page?.id === targetPage
                );
                if (pageIndex !== -1) {
                    setPreviewPageIndex(pageIndex);
                    setSelectedSectionId(null);
                    setSelectedRegion(null);
                }
            } else if (e.data?.type === 'section-selected') {
                setSelectedSectionId(e.data.id);
                setSelectedRegion(null);
            } else if (e.data?.type === 'region-selected') {
                if (e.data.region === 'sidebar') {
                    setSelectedSectionId(null);
                    setSelectedRegion({ region: 'sidebar', side: e.data.side || '' });
                }
            } else if (e.data?.type === 'section-reorder') {
                const { fromId, toId } = e.data;
                setSections((prev: any[]) => {
                    const arr = [...prev];
                    const fi = arr.findIndex((s: any) => s.id === fromId);
                    const ti = arr.findIndex((s: any) => s.id === toId);
                    if (fi === -1 || ti === -1) return prev;
                    arr.splice(ti, 0, arr.splice(fi, 1)[0]);
                    return arr;
                });
                setPages((prev: any[]) => prev.map((page: any) => {
                    const rawIds: string[] = (page.sections || []).map((ref: any) =>
                        typeof ref === 'string' ? ref : ref?.value
                    );
                    const fi = rawIds.indexOf(fromId);
                    const ti = rawIds.indexOf(toId);
                    if (fi === -1 || ti === -1) return page;
                    const newRefs = [...(page.sections || [])];
                    newRefs.splice(ti, 0, newRefs.splice(fi, 1)[0]);
                    return { ...page, sections: newRefs };
                }));
            } else if (e.data?.type === 'section-move') {
                const { fromId, beforeId, newPosition, sidebarSide } = e.data;
                setSections((prev: any[]) => {
                    const arr = [...prev];
                    const fi = arr.findIndex((s: any) => s.id === fromId);
                    if (fi === -1) return prev;
                    const [moving] = arr.splice(fi, 1);
                    const normalizedPosition = ['header', 'hero', 'main', 'sidebar', 'footer'].includes(newPosition)
                        ? newPosition
                        : (moving.position || 'main');
                    const nextStyle = { ...moving.style };
                    if (normalizedPosition === 'sidebar' && ['left', 'right'].includes(sidebarSide)) {
                        nextStyle.sidebar_side = sidebarSide;
                    } else if (normalizedPosition !== 'sidebar') {
                        delete nextStyle.sidebar_side;
                    }
                    const nextMoving = { ...moving, position: normalizedPosition, style: nextStyle };
                    const ti = beforeId === '__end__' ? arr.length : arr.findIndex((s: any) => s.id === beforeId);
                    arr.splice(ti === -1 ? arr.length : ti, 0, nextMoving);
                    return arr;
                });
                setPages((prev: any[]) => prev.map((page: any) => {
                    const refs = [...(page.sections || [])];
                    const fi = refs.findIndex((ref: any) => sectionRefId(ref) === fromId);
                    if (fi === -1) return page;
                    const [movingRef] = refs.splice(fi, 1);
                    const ti = beforeId === '__end__' ? refs.length : refs.findIndex((ref: any) => sectionRefId(ref) === beforeId);
                    refs.splice(ti === -1 ? refs.length : ti, 0, movingRef);
                    return { ...page, sections: refs };
                }));
            } else if (e.data?.type === 'section-resize') {
                const { id, col_span } = e.data;
                setSections((prev: any[]) => prev.map((s: any) =>
                    s.id === id ? { ...s, col_span } : s
                ));
            } else if (e.data?.type === 'section-sidebar-width') {
                const { id, sidebar_width } = e.data;
                const nextWidth = Number(sidebar_width);
                if (!Number.isFinite(nextWidth) || nextWidth < 1) return;
                setSections((prev: any[]) => prev.map((s: any) =>
                    s.id === id ? { ...s, style: { ...s.style, sidebar_width: Math.round(nextWidth) } } : s
                ));
            } else if (e.data?.type === 'section-height') {
                const { id, min_height } = e.data;
                const nextHeight = Number(min_height);
                if (!Number.isFinite(nextHeight) || nextHeight < 0) return;
                setSections((prev: any[]) => prev.map((s: any) =>
                    s.id === id ? { ...s, min_height: Math.round(nextHeight) } : s
                ));
            } else if (e.data?.type === 'section-duplicate') {
                const { id } = e.data;
                const cloneId = `${id}-copy-${Date.now()}`;
                setSections((prev: any[]) => {
                    const idx = prev.findIndex((s: any) => s.id === id);
                    if (idx === -1) return prev;
                    const clone = { ...prev[idx], id: cloneId };
                    const next = [...prev];
                    next.splice(idx + 1, 0, clone);
                    return next;
                });
                setPages((prev: any[]) => prev.map((page: any) => {
                    const refs = page.sections || [];
                    const fi = refs.findIndex((ref: any) =>
                        (typeof ref === 'string' ? ref : ref?.value) === id
                    );
                    if (fi === -1) return page;
                    const cloneRef = typeof refs[fi] === 'string'
                        ? cloneId
                        : { ...refs[fi], value: cloneId };
                    const next = [...refs];
                    next.splice(fi + 1, 0, cloneRef);
                    return { ...page, sections: next };
                }));
            } else if (e.data?.type === 'section-delete') {
                const { id } = e.data;
                setSections((prev: any[]) => prev.filter((s: any) => s.id !== id));
                setPages((prev: any[]) => prev.map((page: any) => ({
                    ...page,
                    sections: (page.sections || []).filter((ref: any) =>
                        (typeof ref === 'string' ? ref : ref?.value) !== id
                    ),
                })));
            } else if (e.data?.type === 'section-insert' || e.data?.type === 'section-move') {
                const { fromId, beforeId, newPosition } = e.data;
                setSections((prev: any[]) => {
                    const arr = [...prev];
                    const fi = arr.findIndex((s: any) => s.id === fromId);
                    if (fi === -1) return prev;
                    const [moved] = arr.splice(fi, 1);
                    if (newPosition) moved.position = newPosition;
                    if (beforeId === '__end__') {
                        arr.push(moved);
                    } else {
                        const ti = arr.findIndex((s: any) => s.id === beforeId);
                        arr.splice(ti === -1 ? arr.length : ti, 0, moved);
                    }
                    return arr;
                });
                setPages((prev: any[]) => prev.map((page: any) => {
                    const refs = [...(page.sections || [])];
                    const fi = refs.findIndex((ref: any) =>
                        (typeof ref === 'string' ? ref : ref?.value) === fromId
                    );
                    if (fi === -1) return page;
                    const [moved] = refs.splice(fi, 1);
                    if (beforeId === '__end__') {
                        refs.push(moved);
                    } else {
                        const ti = refs.findIndex((ref: any) =>
                            (typeof ref === 'string' ? ref : ref?.value) === beforeId
                        );
                        refs.splice(ti === -1 ? refs.length : ti, 0, moved);
                    }
                    return { ...page, sections: refs };
                }));
            }
        };
        window.addEventListener('message', handler);
        return () => window.removeEventListener('message', handler);
    }, [setSections, setPages]);

    const doRefreshPreview = useCallback(async () => {
        if (!interfaceId) return;
        const { sections: secs, pages: pgs, previewPageIndex: idx, styling: stl, tokens: tks } = latestState.current;
        const effectiveTokens = normalizeDesignTokens(tks, stl);
        setIsRefreshing(true);
        setPreviewError('');
        try {
            const res = await authAxios.post(`/v1/metadata/interfaces/${interfaceId}/generate/`, {
                prompt: '',
                interface_data_override: {
                    sections: secs,
                    pages: pgs,
                    ...(stl && Object.keys(stl).length ? { styling: stl } : {}),
                    ...(effectiveTokens && Object.keys(effectiveTokens).length ? { tokens: effectiveTokens } : {}),
                },
                inject_click_handlers: true,
            });
            const htmlFiles = (res.data.files || []).filter((f: any) => f.path.endsWith('.html'));
            const targetPage = (pgs as any[])[idx];
            const html = htmlFiles.find((f: any) => previewFileMatchesPage(f, targetPage, res.data?.interface_name))?.content
                ?? htmlFiles[idx]?.content
                ?? htmlFiles[0]?.content;
            if (html) {
                setPreviewHtml(html);
            } else {
                setPreviewError('Preview generated no HTML files.');
            }
        } catch (error: any) {
            setPreviewError(error?.response?.data?.detail || error?.message || 'Preview generation failed.');
        } finally {
            setIsRefreshing(false);
        }
    }, [interfaceId]);

    const checkAndSwitchLive = useCallback(async () => {
        try {
            const res = await authAxios.get('/v1/generator/prototypes/active_prototype/');
            if (res.data?.running === true) {
                setPreviewMode('live');
            } else {
                setPreviewMode('design');
            }
        } catch {
            setPreviewMode('design');
        }
    }, []);

    const openPromptGuide = useCallback((target: 'explore' | 'refine') => {
        setPromptGuideTarget(target);
        setIsPromptGuideOpen(true);
    }, []);

    const applyPromptGuideExample = useCallback((prompt: string) => {
        if (promptGuideTarget === 'explore') {
            setExplorePrompt(prompt);
        } else {
            setCurrentPrompt(prompt);
            setIsAIExpanded(true);
        }
        setIsPromptGuideOpen(false);
    }, [promptGuideTarget]);

    const handleMapUml = useCallback(async () => {
        if (!interfaceId) return;
        setIsMapping(true);
        setMapStatus('idle');
        if (saveTimer.current) {
            clearTimeout(saveTimer.current);
            saveTimer.current = null;
        }
        try {
            const { data: mapResult } = await authAxios.post(`/v1/generator/prototypes/map_uml_to_interface/`, { interface_id: interfaceId });
            if (!mapResult?.ok) {
                throw new Error(mapResult?.message || 'UML mapping failed');
            }
            setMapStatus('ok');
            const res = await authAxios.get(`/v1/metadata/interfaces/${interfaceId}/`);
            const data = (res.data as any)?.data || {};
            dbLoadTimestamp.current = Date.now();
            setSections(data.sections || []);
            setPages(data.pages || []);
            if (saveTimer.current) {
                clearTimeout(saveTimer.current);
                saveTimer.current = null;
            }
        } catch (error) {
            console.error('UML mapping failed:', error);
            setMapStatus('error');
        } finally {
            setIsMapping(false);
            setTimeout(() => setMapStatus('idle'), 4000);
        }
    }, [interfaceId, setSections, setPages]);

    const handleSeedData = useCallback(async () => {
        setIsSeedingData(true);
        setSeedStatus('idle');
        try {
            const params = systemId ? `?system_id=${systemId}` : '';
            await authAxios.post(`/v1/generator/prototypes/seed/${params}`);
            setSeedStatus('ok');
            setLiveUser(resolveLiveUser());
            setLiveKey((k: number) => k + 1);
            checkAndSwitchLive();
        } catch {
            setSeedStatus('error');
        } finally {
            setIsSeedingData(false);
            setTimeout(() => setSeedStatus('idle'), 3000);
        }
    }, [systemId, checkAndSwitchLive, resolveLiveUser]);

    const buildGeneratorPrototypePayload = useCallback(async (overrideSections?: any[], overridePages?: any[], overrideStyling?: any, overrideTokens?: any) => {
        if (!interfaceId || !systemId) {
            throw new Error('Missing interface or system id.');
        }

        const [{ data: iface }, { data: diagrams }, { data: allInterfaces }] = await Promise.all([
            authAxios.get(`/v1/metadata/interfaces/${interfaceId}/`),
            authAxios.get(`/v1/diagram/system/${systemId}/`),
            authAxios.get(`/v1/metadata/interfaces/`, { params: { system: systemId } }),
        ]);
        const { sections: secs, pages: pgs, styling: stl, tokens: tks } = latestState.current;
        const effectiveSections = overrideSections ?? secs;
        const effectivePages = overridePages ?? pgs;
        const effectiveStyling = overrideStyling ?? stl;
        const effectiveTokens = normalizeDesignTokens(overrideTokens ?? tks ?? (iface as any).data?.tokens, effectiveStyling);
        const hasPreviewOverride = Boolean(
            overrideSections || overridePages || overrideStyling || overrideTokens
        );
        const syncedInterface = {
            ...iface,
            data: {
                ...(iface as any).data,
                sections: effectiveSections,
                pages: effectivePages,
                ...(effectiveStyling && Object.keys(effectiveStyling).length ? { styling: effectiveStyling } : {}),
                ...(effectiveTokens && Object.keys(effectiveTokens).length ? { tokens: effectiveTokens } : {}),
            },
        };
        const prototypeName = `sync${Date.now()}`;
        let databasePrototypeName = '';
        let previousPrototypeId = '';
        try {
            const { data: activePrototype } = await authAxios.get('/v1/generator/prototypes/active_prototype/');
            if (activePrototype?.running && activePrototype?.system === systemId && activePrototype?.name) {
                databasePrototypeName = activePrototype.name;
                previousPrototypeId = activePrototype.prototype_id || '';
            }
        } catch {
            databasePrototypeName = '';
            previousPrototypeId = '';
        }

        const body = {
            name: prototypeName,
            description: `Synced from ${iface?.name || 'preview'}`,
            system: systemId,
            database_hash: `sync-${systemId}-${interfaceId}`,
            metadata: {
                diagrams,
                interfaces: (Array.isArray(allInterfaces) && allInterfaces.length ? allInterfaces : [iface]).map((itf: any) => ({
                    label: itf.name,
                    value: itf.id === syncedInterface.id ? syncedInterface : itf,
                })),
                useAuthentication: true,
                layout_config: {
                    source: 'agent-design-sync',
                    interface_data_source: hasPreviewOverride ? 'preview_override' : 'saved_interface',
                    synced_at: new Date().toISOString(),
                },
            },
        };

        return {
            endpoint: 'POST /v1/generator/prototypes/',
            query: { database_prototype_name: databasePrototypeName },
            previous_prototype_id: previousPrototypeId,
            body,
        };
    }, [interfaceId, systemId]);

    const handleViewGeneratorMetadata = useCallback(async () => {
        setIsMetadataOpen(true);
        setIsLoadingMetadata(true);
        setMetadataError('');
        setMetadataJson('');
        try {
            let overrideSections: any[] | undefined;
            let overridePages: any[] | undefined;
            let overrideStyling: Record<string, unknown> | undefined;
            let overrideTokens: Record<string, unknown> | undefined;
            if (designMode === 'explore' && previewCandidateIdx !== null && candidates[previewCandidateIdx]) {
                const cand = candidates[previewCandidateIdx];
                overrideSections = cand.sections;
                overridePages = cand.pages;
                overrideStyling = cand.styling;
                overrideTokens = normalizeDesignTokens(cand.tokens, cand.styling);
            }
            const payload = await buildGeneratorPrototypePayload(overrideSections, overridePages, overrideStyling, overrideTokens);
            setMetadataJson(JSON.stringify(payload, null, 2));
        } catch (error: any) {
            setMetadataError(error?.response?.data?.detail || error?.message || 'Failed to build generator metadata.');
        } finally {
            setIsLoadingMetadata(false);
        }
    }, [buildGeneratorPrototypePayload, designMode, previewCandidateIdx, candidates]);

    const runVisualCheckForCurrentDesign = useCallback(async () => {
        if (!interfaceId) return null;
        const { sections: secs, pages: pgs, styling: stl, tokens: tks } = latestState.current;
        const activeCandidate = designMode === 'explore' && previewCandidateIdx !== null ? candidates[previewCandidateIdx] : null;
        const effectiveStyling = activeCandidate?.styling || stl;
        const effectiveTokens = normalizeDesignTokens(activeCandidate?.tokens || tks, effectiveStyling);
        const { data } = await authAxios.post('/v1/generator/prototypes/visual_check/', {
            interface_id: interfaceId,
            live_user: liveUser,
            sections: activeCandidate?.sections || secs,
            pages: activeCandidate?.pages || pgs,
            ...(effectiveStyling && Object.keys(effectiveStyling).length ? { styling: effectiveStyling } : {}),
            ...(effectiveTokens && Object.keys(effectiveTokens).length ? { tokens: effectiveTokens } : {}),
        });
        return data;
    }, [interfaceId, designMode, previewCandidateIdx, candidates, liveUser]);

    const handleSyncLivePrototype = useCallback(async () => {
        if (!interfaceId || !systemId || isSyncingLive) return;
        setIsSyncingLive(true);
        setSyncStatus('idle');
        setVisualCheckStatus('idle');
        setVisualCheckSummary('');
        try {
            // In explore mode, use the selected candidate's layout data directly
            // so the live prototype matches what the preview shows.
            let overrideSections: any[] | undefined;
            let overridePages: any[] | undefined;
            let overrideStyling: Record<string, unknown> | undefined;
            let overrideTokens: Record<string, unknown> | undefined;
            if (designMode === 'explore' && previewCandidateIdx !== null && candidates[previewCandidateIdx]) {
                const cand = candidates[previewCandidateIdx];
                overrideSections = cand.sections;
                overridePages = cand.pages;
                overrideStyling = cand.styling;
                overrideTokens = normalizeDesignTokens(cand.tokens, cand.styling);
            }
            const payload = await buildGeneratorPrototypePayload(overrideSections, overridePages, overrideStyling, overrideTokens);
            const databasePrototypeName = payload.query.database_prototype_name || '';
            const previousPrototypeId = payload.previous_prototype_id || '';
            const databasePrototypeQuery = databasePrototypeName
                ? `?database_prototype_name=${encodeURIComponent(databasePrototypeName)}`
                : '';
            const { data: prototype } = await authAxios.post(`/v1/generator/prototypes/${databasePrototypeQuery}`, payload.body);
            await authAxios.post(`/v1/generator/prototypes/run/${prototype.id}`);
            if (previousPrototypeId && previousPrototypeId !== prototype.id) {
                try {
                    await authAxios.delete(`/v1/generator/prototypes/${previousPrototypeId}/`);
                } catch {
                    // The new live prototype is already running; deletion failure should not break sync.
                }
            }
            const params = systemId ? `?system_id=${systemId}` : '';
            await authAxios.post(`/v1/generator/prototypes/seed/${params}`);
            setPreviewMode('live');
            setLiveUser(resolveLiveUser());
            setLiveKey((k: number) => k + 1);
            try {
                setIsVisualChecking(true);
                const checkData = await runVisualCheckForCurrentDesign();
                const failed = (checkData?.checks || []).filter((item: any) => !item.ok);
                setVisualCheckStatus(failed.length ? 'error' : 'ok');
                setVisualCheckSummary(failed.length
                    ? `${failed.length}/${(checkData?.checks || []).length} preview/live pages differ`
                    : `${(checkData?.checks || []).length} preview/live pages match`);
                setSyncStatus(failed.length ? 'error' : 'ok');
            } finally {
                setIsVisualChecking(false);
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Live prototype sync failed.';
            setVisualCheckSummary(message);
            setSyncStatus('error');
        } finally {
            setIsSyncingLive(false);
            setTimeout(() => setSyncStatus('idle'), 3000);
        }
    }, [interfaceId, systemId, isSyncingLive, buildGeneratorPrototypePayload, designMode, previewCandidateIdx, candidates, resolveLiveUser, runVisualCheckForCurrentDesign]);

    const handleVisualCheck = useCallback(async () => {
        if (!interfaceId || isVisualChecking) return;
        setIsVisualChecking(true);
        setVisualCheckStatus('idle');
        setVisualCheckSummary('');
        try {
            const data = await runVisualCheckForCurrentDesign();
            const failed = (data?.checks || []).filter((item: any) => !item.ok);
            setVisualCheckStatus(failed.length ? 'error' : 'ok');
            setVisualCheckSummary(failed.length
                ? `${failed.length}/${(data?.checks || []).length} preview/live pages differ`
                : `${(data?.checks || []).length} preview/live pages match`);
        } catch (error: any) {
            setVisualCheckStatus('error');
            setVisualCheckSummary(error?.response?.data?.detail || error?.message || 'Visual check failed');
        } finally {
            setIsVisualChecking(false);
            setTimeout(() => setVisualCheckStatus('idle'), 5000);
        }
    }, [interfaceId, isVisualChecking, runVisualCheckForCurrentDesign]);

    const doHotReload = useCallback(async () => {
        if (!interfaceId) return;
        const { sections: secs, pages: pgs, styling: stl, tokens: tks } = latestState.current;
        const activeCandidate = designMode === 'explore' && previewCandidateIdx !== null ? candidates[previewCandidateIdx] : null;
        const effectiveStyling = activeCandidate?.styling || stl;
        const effectiveTokens = normalizeDesignTokens(activeCandidate?.tokens || tks, effectiveStyling);
        try {
            await authAxios.post('/v1/generator/prototypes/hot_reload/', {
                interface_id: interfaceId,
                sections: activeCandidate?.sections || secs,
                pages: activeCandidate?.pages || pgs,
                ...(effectiveStyling && Object.keys(effectiveStyling).length ? { styling: effectiveStyling } : {}),
                ...(effectiveTokens && Object.keys(effectiveTokens).length ? { tokens: effectiveTokens } : {}),
            });
            setLiveKey((k: number) => k + 1);
        } catch {
            // fail silently — live prototype may not be running
        }
    }, [interfaceId, designMode, previewCandidateIdx, candidates]);

    const handleSwitchToLive = useCallback(async () => {
        await handleSyncLivePrototype();
    }, [handleSyncLivePrototype]);

    // Debounce: refresh 600 ms after any sections/pages/page-index/styling change
    useEffect(() => {
        if (!interfaceId) return;
        const previewPayloadSize = JSON.stringify({ sections, pages, styling }).length;
        if (previewPayloadSize > MAX_AUTO_PREVIEW_BYTES) {
            setPreviewError('Preview is paused for this large interface. Use Refresh to generate it manually.');
            return;
        }
        if (refreshTimer.current) clearTimeout(refreshTimer.current);
        refreshTimer.current = setTimeout(doRefreshPreview, 600);
        return () => { if (refreshTimer.current) clearTimeout(refreshTimer.current); };
    }, [sections, pages, previewPageIndex, styling, interfaceId, doRefreshPreview]);

    // Debounce: hot-reload live prototype 800 ms after sections/pages/styling/tokens change
    useEffect(() => {
        if (!interfaceId || previewMode !== 'live') return;
        if (hotReloadTimer.current) clearTimeout(hotReloadTimer.current);
        hotReloadTimer.current = setTimeout(doHotReload, 800);
        return () => { if (hotReloadTimer.current) clearTimeout(hotReloadTimer.current); };
    }, [sections, pages, styling, tokens, interfaceId, previewMode, doHotReload]);

    // Debounce: persist sections+pages to DB 800 ms after any change, skipping DB-load write-backs
    useEffect(() => {
        if (!interfaceId) return;
        if (previewMode === 'live') return;
        if (saveTimer.current) clearTimeout(saveTimer.current);
        if (Date.now() - dbLoadTimestamp.current < 1000) return;
        saveTimer.current = setTimeout(() => {
            authAxios.patch(`/v1/metadata/interfaces/${interfaceId}/data/`, {
                sections,
                pages,
                styling,
                tokens: normalizeDesignTokens(tokens, styling),
            }).catch((e: any) => console.error('Failed to persist sections/pages:', e));
        }, 800);
        return () => { if (saveTimer.current) clearTimeout(saveTimer.current); };
    }, [sections, pages, styling, tokens, interfaceId, previewMode]);

const updateSection = useCallback((sectionId: string, field: string, value: any) => {
        setSections((prev: any[]) => prev.map((s: any) => {
            if (s.id !== sectionId) return s;
            if (field === 'layout') {
                const nextLayout = value as LayoutOption;
                let nextPosition = s.position;
                if (HEADER_LAYOUT_SET.has(nextLayout)) {
                    nextPosition = 'header';
                } else if (FOOTER_LAYOUT_SET.has(nextLayout)) {
                    nextPosition = 'footer';
                }
                const options = COMPONENT_OPTIONS_BY_LAYOUT[nextLayout] || [];
                const nextComponent = options.includes(s.component) ? s.component : (options[0] || s.component || '');
                return { ...s, layout: value, position: nextPosition, component: nextComponent };
            }
            if (field === 'col_span') return { ...s, col_span: value };
            if (field === 'text') return { ...s, text: value };
            if (field === 'label') return { ...s, label: value, name: value || s.name };
            if (field === 'component') return { ...s, component: value };
            if (field === 'field_layout') return { ...s, field_layout: value };
            if (field === 'behavior') return { ...s, behavior: value };
            if (field === 'related_to') {
                return {
                    ...s,
                    related_to: value || null,
                    relationship: value ? (s.relationship ?? { mode: 'direct' }) : undefined,
                    relation_field: value ? s.relation_field : undefined,
                };
            }
            if (field === 'relationship_mode') {
                return { ...s, relationship: { ...s.relationship, mode: value } };
            }
            if (field === 'relation_field') return { ...s, relation_field: value || null };
            if (field === 'data_source_from') {
                const model = s.primary_model || value || '';
                return {
                    ...s,
                    data_source: {
                        ...s.data_source,
                        mode: 'query',
                        from: { model },
                        joins: s.data_source?.joins || [],
                    },
                };
            }
            if (field === 'query_limit') {
                const parsed = Number.parseInt(String(value || ''), 10);
                return { ...s, query: { ...s.query, limit: Number.isNaN(parsed) ? null : parsed } };
            }
            if (field === 'item_click_type') {
                const behavior = { ...s.behavior };
                if (!value || value === 'none') {
                    delete behavior.item_click;
                } else {
                    behavior.item_click = { ...behavior.item_click, type: value };
                }
                return { ...s, behavior };
            }
            if (field === 'item_click_target_page') {
                const behavior = s.behavior ? { ...s.behavior } : {};
                behavior.item_click = {
                    ...behavior.item_click,
                    type: value ? 'navigate' : (behavior.item_click?.type || 'none'),
                    target_page: value || '',
                };
                if (!value) delete behavior.item_click.target_page;
                return { ...s, behavior };
            }
            if (field === 'workflow_action') return { ...s, workflow: { ...s.workflow, action: value } };
            if (field === 'workflow_target_page') return { ...s, workflow: { ...s.workflow, target_page: value } };
            return { ...s, style: { ...s.style, [field]: value } };
        }));
    }, [setSections]);

    // Load a complete DSL candidate from the agent (replaces all pages + sections).
    // Each candidate carries the agent's own per-section style decisions — no uniform override.
    const applyVariantDSL = useCallback((variantPages: any[], variantSections: any[]) => {
        setPages(variantPages);
        setSections(variantSections);
    }, [setPages, setSections]);

    const loadCandidates = useCallback(async () => {
        if (!interfaceId) return;
        try {
            const res = await authAxios.get(`/v1/metadata/interfaces/${interfaceId}/`);
            const found = (res.data as any)?.data?.candidates || [];
            setCandidates(found);
            if (found.length === 0) setCandidateStatus(prev => prev.startsWith('Done') ? 'No candidates saved by agent. Check agent logs.' : prev);
        } catch (e: any) {
            setCandidateStatus(`Failed to load candidates: ${e?.message || 'unknown error'}`);
        }
    }, [interfaceId]);

    useEffect(() => {
        if (designMode === 'explore' && interfaceId) loadCandidates();
    }, [designMode, interfaceId, loadCandidates]);

    const handleGenerateCandidates = async () => {
        if (!explorePrompt.trim() || isGeneratingCandidates || !interfaceId || !systemId) return;
        const prompt = explorePrompt;
        setIsGeneratingCandidates(true);
        setCandidateStatus('Connecting to agent...');
        trackEvent('candidates_generated', { prompt, interface_id: interfaceId, system_id: systemId });
        setCandidates([]);
        setPreviewCandidateIdx(null);
        let lastStatus = '';
        try {
            const bearerToken = useAuthStore.getState().bearerToken;
            const authHeader = bearerToken ? `Bearer ${bearerToken}` : '';
            const base = trimTrailingSlashes(authAxios.defaults.baseURL || '');
            const response = await fetch(`${base}/v1/generator/prototypes/generate_candidates/`, {
                method: 'POST', credentials: 'include',
                headers: { 'Content-Type': 'application/json', ...(authHeader ? { Authorization: authHeader } : {}) },
                body: JSON.stringify({ interface_id: interfaceId, system_id: systemId, prompt }),
            });
            if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buf = '';
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buf += decoder.decode(value, { stream: true });
                const lines = buf.split('\n');
                buf = lines.pop() || '';
                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const c = JSON.parse(line);
                        if (c.status) { lastStatus = c.status; setCandidateStatus(c.status); }
                        if (c.status === 'error') {
                            setCandidateStatus(`Error: ${c.message || c.agent_error || 'candidate generation failed'}`);
                            setIsGeneratingCandidates(false);
                            return;
                        }
                        if (c.status === 'done') {
                            setCandidateStatus(`Done! Loading ${c.candidate_count ?? ''} candidate${c.candidate_count === 1 ? '' : 's'}...`);
                            await loadCandidates();
                            setIsGeneratingCandidates(false);
                            return;
                        }
                    } catch { /* ignore */ }
                }
            }
            // Only show success if agent explicitly returns "done"; otherwise keep the last received status (may be an error message)
            if (lastStatus === 'done') setCandidateStatus('Done! Loading candidates...');
        } catch (e: any) {
            setCandidateStatus(`Error: ${e.message}`);
        } finally {
            setIsGeneratingCandidates(false);
            await loadCandidates();
        }
    };

    const handleRegenerateCandidates = async (idx: number) => {
        if (!explorePrompt.trim() || isGeneratingCandidates || !interfaceId || !systemId || !candidates[idx]) return;
        const designer_requirements = explorePrompt;
        setIsGeneratingCandidates(true);
        setCandidateStatus(`Regenerating 3 candidates from Candidate ${idx + 1}...`);
        trackEvent('candidates_regenerated', { from_candidate_index: idx, prompt: designer_requirements, interface_id: interfaceId, system_id: systemId });
        setCandidates([]);
        setPreviewCandidateIdx(null);
        try {
            const bearerToken = useAuthStore.getState().bearerToken;
            const authHeader = bearerToken ? `Bearer ${bearerToken}` : '';
            const base = trimTrailingSlashes(authAxios.defaults.baseURL || '');
            const response = await fetch(`${base}/v1/generator/prototypes/regenerate_candidates/`, {
                method: 'POST', credentials: 'include',
                headers: { 'Content-Type': 'application/json', ...(authHeader ? { Authorization: authHeader } : {}) },
                body: JSON.stringify({
                    interface_id: interfaceId,
                    system_id: systemId,
                    selected_candidate_index: idx,
                    designer_requirements,
                }),
            });
            if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buf = '';
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buf += decoder.decode(value, { stream: true });
                const lines = buf.split('\n');
                buf = lines.pop() || '';
                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const c = JSON.parse(line);
                        if (c.status) setCandidateStatus(c.status);
                        if (c.status === 'error') {
                            setCandidateStatus(`Error: ${c.message || c.agent_error || 'candidate regeneration failed'}`);
                            setIsGeneratingCandidates(false);
                            return;
                        }
                        if (c.status === 'done') {
                            setCandidateStatus(`Done! Regenerated ${c.candidate_count ?? 3} candidates from Candidate ${idx + 1}.`);
                            await loadCandidates();
                            setIsGeneratingCandidates(false);
                            return;
                        }
                    } catch { /* ignore */ }
                }
            }
        } catch (e: any) {
            setCandidateStatus(`Error: ${e.message}`);
        } finally {
            setIsGeneratingCandidates(false);
            await loadCandidates();
        }
    };

    const handleApplyCandidate = useCallback(async (idx: number) => {
        if (!interfaceId) return;
        try {
            const res = await authAxios.post(`/v1/metadata/interfaces/${interfaceId}/candidates/${idx}/apply/`);
            const d = res.data as any;
            if (d?.pages) applyVariantDSL(d.pages, d.sections);
            if (d?.styling && Object.keys(d.styling).length) setStyling(d.styling);
            if (d?.tokens && Object.keys(d.tokens).length) setTokens(normalizeDesignTokens(d.tokens, d.styling));
            setDesignMode('refine');
            setPreviewCandidateIdx(null);
            trackEvent('candidate_selected', { candidate_index: idx, interface_id: interfaceId });
        } catch { /* ignore */ }
    }, [interfaceId, applyVariantDSL, setStyling, setTokens]);

    const updatePageProperty = useCallback((pageIndex: number, field: string, value: any) => {
        setPages((prev: any[]) => {
            const next = [...prev];
            if (next[pageIndex]) {
                next[pageIndex] = { ...next[pageIndex], [field]: value };
            }
            return next;
        });
    }, [setPages]);

    const updatePageLayoutSetting = useCallback((pageIndex: number, field: string, value: any) => {
        setPages((prev: any[]) => {
            const next = [...prev];
            if (next[pageIndex]) {
                const existing = next[pageIndex].layout && typeof next[pageIndex].layout === 'object'
                    ? next[pageIndex].layout
                    : { value: next[pageIndex].layout || 'vertical' };
                next[pageIndex] = {
                    ...next[pageIndex],
                    layout: { ...existing, [field]: value },
                };
            }
            return next;
        });
    }, [setPages]);

    const handleSendMessage = async () => {
        if (!currentPrompt.trim() || isLoadingAgent || !interfaceId) return;
        const prompt = currentPrompt;
        setCurrentPrompt('');
        setIsLoadingAgent(true);
        setAgentStatus('Initiating...');
        trackEvent('refinement_submitted', { prompt, interface_id: interfaceId });

        try {
            const bearerToken = useAuthStore.getState().bearerToken;
            const authHeader = bearerToken ? `Bearer ${bearerToken}` : '';
            const base = trimTrailingSlashes(authAxios.defaults.baseURL || '');
            const response = await fetch(`${base}/v1/metadata/interfaces/${interfaceId}/generate/`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    ...(authHeader ? { Authorization: authHeader } : {}),
                },
                body: JSON.stringify({
                    prompt,
                    model: 'gpt-4o-mini',
                }),
            });


            if (!response.ok) {
                const errText = await response.text();
                setAgentStatus(`Error ${response.status}: ${errText.slice(0, 200)}`);
                return;
            }

            if (!response.body) throw new Error('Streaming not supported');
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const chunk = JSON.parse(line);
                        if (chunk.status && chunk.status !== 'Done') {
                            setAgentStatus(chunk.status);
                        }
                        if (chunk.status === 'Done') {
                            const htmlFiles = (chunk.files || []).filter((f: any) => f.path.endsWith('.html'));
                            const targetPage = (pages as any[])[previewPageIndex];
                            const html = htmlFiles.find((f: any) => previewFileMatchesPage(f, targetPage, chunk.interface_name))?.content
                                ?? htmlFiles[0]?.content;
                            if (html) setPreviewHtml(html);
                            setAgentStatus(chunk.message || 'Complete.');
                            const freshData = chunk.interface_data || {};
                            if (freshData.sections) setSections(freshData.sections);
                            if (freshData.pages) setPages(freshData.pages);
                        }
                    } catch (e) {
                        console.error('Failed to parse chunk', e);
                    }
                }
            }
        } catch (e: any) {
            setAgentStatus(`Error: ${e.message}`);
        } finally {
            setIsLoadingAgent(false);
        }
    };

    const rawSectionLayout = selectedSection?.layout;
    const secLayout: LayoutOption = ((typeof rawSectionLayout === 'string' ? rawSectionLayout : rawSectionLayout?.value) as LayoutOption) || 'table';
    const secColSpan: ColSpanOption = (selectedSection?.col_span as ColSpanOption) ?? 12;
    const secStyle = selectedSection?.style || {};
    const secColor: ColorOption = (secStyle.color as ColorOption) || 'blue';
    const secDensity: DensityOption = (secStyle.density as DensityOption) || 'normal';
    const secNavHeight: NavHeightOption = (secStyle.nav_height as NavHeightOption) || 'normal';
    const secColumns = String(secStyle.columns ?? '3');
    const secDisplayMode: DisplayModeOption = (secStyle.display_mode as DisplayModeOption) || 'grid';
    const secBannerHeight: BannerHeightOption = (secStyle.banner_height as BannerHeightOption) || 'md';
    const secImageRatio: ImageRatioOption = (secStyle.image_ratio as ImageRatioOption) || 'wide';
    const secCardStyle: CardStyleOption = (secStyle.card_style as CardStyleOption) || 'default';
    const secListStyle: ListStyleOption = (secStyle.list_style as ListStyleOption) || 'default';
    const secFormStyle: FormStyleOption = (secStyle.form_style as FormStyleOption) || 'default';
    const secImagePosition: ImagePositionOption = (secStyle.image_position as ImagePositionOption) || 'top';
    const secImageSize: ImageSizeOption = (secStyle.image_size as ImageSizeOption) || 'md';
    const secShadow: ShadowOption = (secStyle.shadow as ShadowOption) || 'none';
    const secBorder: BorderOption = (secStyle.border as BorderOption) || 'none';
    const secBg: BgOption = (secStyle.bg as BgOption) || 'white';
    const secHeaderStyle: HeaderStyleOption = (secStyle.header_style as HeaderStyleOption) || 'default';
    const secSidebarSide: SidebarSideOption = (secStyle.sidebar_side as SidebarSideOption) || 'left';
    const secSidebarWidth = Number(secStyle.sidebar_width || 3);
    const secLogoSize: LogoSizeOption = (secStyle.logo_size as LogoSizeOption) || 'md';
    const secLogoShape: LogoShapeOption = (secStyle.logo_shape as LogoShapeOption) || 'rounded';
    const secLogoVariant: LogoVariantOption = (secStyle.logo_variant as LogoVariantOption) || 'lockup';
    const secActionVariant: ActionVariantOption = (secStyle.action_variant as ActionVariantOption) || 'link';
    const secShowLogout = !(secStyle.show_logout === false || secStyle.show_logout === 'false' || secStyle.show_logout === '0' || secStyle.show_logout === 'hidden');
    const isActivityAction = isActivityActionSection(selectedSection);
    const isChromeLayout = CHROME_LAYOUT_SET.has(secLayout);
    const isMethodOnly = !isActivityAction && !isChromeLayout && !(selectedSection?.attributes?.length) && !!(selectedSection?.methods?.length);
    const attrNameOf = (attr: any) => typeof attr === 'string' ? attr : attr?.name || '';
    const selectedPrimaryModel = selectedSection?.primary_model || selectedSection?.class || '';
    const selectedModelClassifier = systemClassifiers.find((cls: any) =>
        cls?.data?.name === selectedPrimaryModel || cls?.id === selectedSection?.class
    );
    const primaryClassFields = (selectedModelClassifier?.data?.attributes || []).map((attr: any) => attr.name).filter(Boolean);
    const selectedAttrs = (selectedSection?.attributes || []).map((attr: any) => ({
        raw: attr,
        name: attrNameOf(attr),
        source: typeof attr === 'object' ? attr?.source || '' : '',
        type: typeof attr === 'object' ? attr?.type || '' : '',
        value: typeof attr === 'object' ? attr?.value || '' : '',
        readonly: typeof attr === 'object' && !!(attr?.readonly || attr?.source === 'related'),
    })).filter((attr: any) => attr.name);
    const selectedPrimaryAttrs = selectedAttrs.filter((attr: any) => !attr.name.includes('.'));
    const selectedRelatedAttrs = selectedAttrs.filter((attr: any) => attr.name.includes('.') || attr.readonly);
    const editablePrimaryAttrs = selectedPrimaryAttrs.filter((attr: any) =>
        !attr.readonly && !!(selectedSection?.operations?.create || selectedSection?.operations?.update)
    );
    const readonlyPrimaryAttrs = selectedPrimaryAttrs.filter((attr: any) =>
        attr.readonly || !(selectedSection?.operations?.create || selectedSection?.operations?.update)
    );
    const selectedPrimaryAttrNames = new Set(selectedPrimaryAttrs.map((attr: any) => attr.name));
    const hiddenPrimaryFields = primaryClassFields.filter((field: string) => !selectedPrimaryAttrNames.has(field));
    const secComponent = selectedSection?.component || (COMPONENT_OPTIONS_BY_LAYOUT[secLayout]?.[0] ?? '');
    const componentOptions = Array.from(new Set([
        ...(COMPONENT_OPTIONS_BY_LAYOUT[secLayout] || []),
        ...(secComponent ? [secComponent] : []),
    ]));
    const sectionKind = selectedSection?.component_type || selectedSection?.type || '';
    const isChromeSection = isChromeLayout
        || [
            'HeaderTemplate', 'FooterTemplate', 'NavBar', 'SearchBar', 'IconActions',
            'Logo', 'BrandLockup', 'ImageLogo', 'SiteFooter', 'FooterLinkGrid',
        ].includes(String(secComponent));
    const isChromeOrControlSection = isActivityAction
        || isMethodOnly
        || isChromeSection
        || (!isChromeSection && ['chrome', 'control', 'activity_action'].includes(String(sectionKind)));
    const showComponentSelector = componentOptions.length > 1 && !isChromeOrControlSection;
    const showFieldComposer = !!selectedSection && !isChromeOrControlSection && !!selectedPrimaryModel;
    const fieldLayout = selectedSection?.field_layout && typeof selectedSection.field_layout === 'object'
        ? selectedSection.field_layout
        : {};
    const fieldLayoutFields = fieldLayout.field_styles && typeof fieldLayout.field_styles === 'object' && !Array.isArray(fieldLayout.field_styles)
        ? fieldLayout.field_styles
        : {};
    const fieldLayoutSlots = FIELD_LAYOUT_SLOTS[secComponent] || FIELD_LAYOUT_SLOTS[COMPONENT_OPTIONS_BY_LAYOUT[secLayout]?.[0] || ''] || [];
    const availableFieldNames = selectedAttrs.map((attr: any) => attr.name);
    const orderedFieldNames = React.useMemo(() => {
        return availableFieldNames
            .map((field: string, index: number) => {
                const order = Number(fieldLayoutFields[field]?.order);
                return {
                    field,
                    index,
                    order: Number.isFinite(order) ? order : Number.POSITIVE_INFINITY,
                };
            })
            .sort((a, b) => a.order === b.order ? a.index - b.index : a.order - b.order)
            .map((item) => item.field);
    }, [availableFieldNames, fieldLayoutFields]);
    const fieldLayoutValue = (slot: string) => {
        const value = fieldLayout[slot];
        if (Array.isArray(value)) return value.map((item: any) => typeof item === 'object' ? item?.field : item).filter(Boolean).join(', ');
        return value || '';
    };
    const updateFieldLayoutSlot = (slot: string, rawValue: string, multiple?: boolean) => {
        if (!selectedSection) return;
        const nextValue = multiple
            ? rawValue.split(',').map((item) => item.trim()).filter(Boolean)
            : rawValue;
        updateSection(selectedSection.id, 'field_layout', {
            ...fieldLayout,
            [slot]: nextValue,
        });
    };
    const updateFieldLayoutField = (field: string, key: string, value: string) => {
        if (!selectedSection) return;
        const current = fieldLayoutFields[field] || {};
        const next = { ...current };
        if (value === '' || value === 'auto') delete next[key];
        else next[key] = key === 'order' || key === 'col_span' ? Number(value) : value;
        updateSection(selectedSection.id, 'field_layout', {
            ...fieldLayout,
            field_styles: {
                ...fieldLayoutFields,
                [field]: next,
            },
        });
    };
    const multipleFieldSlots = new Set(fieldLayoutSlots.filter((slot) => slot.multiple).map((slot) => slot.slot));
    const assignableFieldSlots = fieldLayoutSlots.map((slot) => slot.slot);
    const currentFieldSlot = (field: string) => {
        const cfg = fieldLayoutFields[field] || {};
        if (cfg.visible === 'hidden') return 'hidden';
        for (const slot of assignableFieldSlots) {
            const value = fieldLayout[slot];
            if (Array.isArray(value)) {
                if (value.some((item: any) => (typeof item === 'object' ? item?.field : item) === field)) return slot;
            } else if (value === field) {
                return slot;
            }
        }
        return '';
    };
    const updateFieldSlot = (field: string, nextSlot: string) => {
        if (!selectedSection) return;
        const nextLayout: any = { ...fieldLayout };
        for (const slot of assignableFieldSlots) {
            const value = nextLayout[slot];
            if (Array.isArray(value)) {
                nextLayout[slot] = value.filter((item: any) => (typeof item === 'object' ? item?.field : item) !== field);
            } else if (value === field) {
                delete nextLayout[slot];
            }
        }
        const nextFieldStyles = { ...fieldLayoutFields };
        const currentCfg = { ...nextFieldStyles[field] };
        if (nextSlot === 'hidden') {
            currentCfg.visible = 'hidden';
            nextFieldStyles[field] = currentCfg;
            nextLayout.hidden = Array.from(new Set([...(Array.isArray(nextLayout.hidden) ? nextLayout.hidden : []), field]));
        } else {
            delete currentCfg.visible;
            nextFieldStyles[field] = currentCfg;
            nextLayout.hidden = (Array.isArray(nextLayout.hidden) ? nextLayout.hidden : []).filter((item: any) => item !== field);
            if (nextSlot) {
                if (multipleFieldSlots.has(nextSlot)) {
                    nextLayout[nextSlot] = Array.from(new Set([...(Array.isArray(nextLayout[nextSlot]) ? nextLayout[nextSlot] : []), field]));
                } else {
                    nextLayout[nextSlot] = field;
                }
            }
        }
        nextLayout.field_styles = nextFieldStyles;
        updateSection(selectedSection.id, 'field_layout', nextLayout);
    };
    const updateFieldVisibility = (field: string, visible: string) => {
        if (!selectedSection) return;
        if (visible === 'hidden') {
            updateFieldSlot(field, 'hidden');
            return;
        }
        const nextLayout: any = { ...fieldLayout };
        nextLayout.hidden = (Array.isArray(nextLayout.hidden) ? nextLayout.hidden : []).filter((item: any) => item !== field);
        const current = { ...fieldLayoutFields[field] };
        delete current.visible;
        nextLayout.field_styles = { ...fieldLayoutFields, [field]: current };
        updateSection(selectedSection.id, 'field_layout', nextLayout);
    };
    const reorderFieldLayoutFields = (sourceField: string, targetField: string) => {
        if (!selectedSection || sourceField === targetField) return;
        const nextOrder = [...orderedFieldNames];
        const sourceIndex = nextOrder.indexOf(sourceField);
        const targetIndex = nextOrder.indexOf(targetField);
        if (sourceIndex < 0 || targetIndex < 0) return;

        nextOrder.splice(sourceIndex, 1);
        nextOrder.splice(targetIndex, 0, sourceField);

        const nextFieldStyles = { ...fieldLayoutFields };
        nextOrder.forEach((field, index) => {
            nextFieldStyles[field] = {
                ...nextFieldStyles[field],
                order: index + 1,
            };
        });
        updateSection(selectedSection.id, 'field_layout', {
            ...fieldLayout,
            field_styles: nextFieldStyles,
        });
    };

    const hasMediaAttr = selectedAttrs.some((attr: any) => {
        const name = String(attr.name || '').toLowerCase();
        const rawType = typeof attr.raw === 'object' ? String(attr.raw?.type || '').toLowerCase() : '';
        return rawType === 'image' || rawType === 'video' || /image|photo|avatar|thumbnail|media|video/.test(name);
    });
    const componentControls = COMPONENT_CONTROLS[secComponent];
    const baseLayoutControls = CHROME_LAYOUT_SET.has(secLayout)
        ? ['text', 'methods', ...(['nav-links', 'site-nav'].includes(secLayout) ? ['nav_height'] : []), 'density', 'bg', 'shadow', 'sidebar_side', 'sidebar_width']
        : (LAYOUT_CONTROLS[secLayout] ?? []);
    const layoutControls = new Set(Array.from(new Set([...(baseLayoutControls || []), ...(componentControls || [])]))
        .filter((control) => (control !== 'image_position' && control !== 'image_size') || hasMediaAttr || secComponent.toLowerCase().includes('media') || secComponent.toLowerCase().includes('productdetail')));
    const hasControl = (c: string) => layoutControls.has(c) && (!['sidebar_side', 'sidebar_width'].includes(c) || selectedSection?.position === 'sidebar');
    const hasDataShape = !!selectedPrimaryModel || selectedAttrs.length > 0;
    const isChromeLike = CHROME_LAYOUT_SET.has(secLayout) || ['NavBar', 'Logo', 'BrandLockup', 'ImageLogo', 'IconActions', 'SearchBar', 'SiteFooter', 'FooterLinkGrid'].includes(secComponent);
    let baseLayoutGroupsForSelected = LAYOUT_GROUPS;
    if (isChromeLike && !hasDataShape) {
        baseLayoutGroupsForSelected = LAYOUT_GROUPS.filter(group => group.label === 'Header' || group.label === 'Footer');
    } else if (hasDataShape) {
        baseLayoutGroupsForSelected = LAYOUT_GROUPS
            .filter(group => group.label === 'Generic')
            .map(group => ({
                ...group,
                options: group.options.filter(opt => opt.value !== 'activity_action'),
            }));
    }
    const layoutGroupsForSelected = baseLayoutGroupsForSelected.filter(group => group.options.length > 0);

    const currentPage = (pages as any[])[previewPageIndex];
    const isActivityPage = (page: any) => getPageTypeValue(page) === 'activity';
    const mapTone = statusTone(mapStatus, { border: '#e9d5ff', background: '#faf5ff', color: '#7c3aed' });
    const seedTone = statusTone(seedStatus, { border: '#d1d5db', background: '#fff', color: '#374151' });
    const syncTone = statusTone(syncStatus, { border: '#bfdbfe', background: '#eff6ff', color: '#1d4ed8' });
    const visualCheckTone = statusTone(visualCheckStatus, { border: '#d1d5db', background: '#fff', color: '#374151' });
    const mapButtonLabel = statusLabel(mapStatus, 'Mapped!', 'Failed', 'Map UML');
    const seedButtonLabel = statusLabel(seedStatus, 'Seeded!', 'Failed', 'Seed Data');
    const syncButtonLabel = statusLabel(syncStatus, 'Synced!', 'Sync Failed', 'Sync Live');
    const visualCheckButtonLabel = statusLabel(visualCheckStatus, 'Matched', 'Diff', 'Visual Check');
    let candidatePreviewMessage = 'Select a candidate to preview.';
    if (isGeneratingCandidates) {
        candidatePreviewMessage = 'Generating candidates...';
    } else if (candidates.length === 0) {
        candidatePreviewMessage = 'Generate candidates to see previews here.';
    }
    let previewEmptyMessage = 'Loading preview...';
    if (previewError) {
        previewEmptyMessage = previewError;
    } else if ((sections as any[]).length === 0) {
        previewEmptyMessage = 'Add sections and pages to see a preview.';
    } else if ((pages as any[]).length === 0) {
        previewEmptyMessage = 'Add pages in the Pages tab to see a preview.';
    }
    const pageLayout = currentPage?.layout?.value || 'vertical';
    const pageMainWidth = currentPage?.layout?.main_width || 'contained';
    const pageHeaderWidth = currentPage?.layout?.header_width || 'contained';
    const pageHeroWidth = currentPage?.layout?.hero_width || 'contained';
    const pageFooterWidth = currentPage?.layout?.footer_width || 'contained';
    const pageSidebarBg: BgOption | 'transparent' = currentPage?.layout?.sidebar_bg || 'transparent';
    const pageSidebarShadow: ShadowOption = currentPage?.layout?.sidebar_shadow || 'none';
    const pageGap = currentPage?.gap?.value || 'normal';

    const btnBase: React.CSSProperties = {
        display: 'flex', alignItems: 'center', gap: 4,
        padding: '4px 8px', borderRadius: 6, fontSize: 12,
        cursor: 'pointer', transition: 'all 0.15s',
    };
    const active = (on: boolean): React.CSSProperties => ({
        background: on ? '#2563eb' : '#fff',
        color: on ? '#fff' : '#374151',
        border: `1px solid ${on ? '#2563eb' : '#d1d5db'}`,
    });

    const stl = styling as Record<string, string>;
    const designTokens = tokens as Record<string, string>;
    const updateStyling = (key: string, value: string) =>
        setStyling((prev: Record<string, string>) => ({ ...prev, [key]: value }));
    const updateDesignToken = (key: string, value: string) =>
        setTokens((prev: Record<string, string>) => {
            const next = { ...prev };
            if (value === '' || value == null) delete next[key];
            else next[key] = value;
            return normalizeDesignTokens(next, styling);
        });
    const updateTokenGroup = (updates: Record<string, string>, legacy?: Record<string, string>) => {
        setTokens((prev: Record<string, string>) => normalizeDesignTokens({ ...prev, ...updates }, styling));
        if (legacy) setStyling((prev: Record<string, string>) => ({ ...prev, ...legacy }));
    };
    const tokenValue = (key: string, fallback = '') => String(designTokens?.[key] ?? fallback);

    const BG_PRESETS = [
        { label: 'White', hex: '#ffffff' },
        { label: 'Light', hex: '#f8fafc' },
        { label: 'Warm',  hex: '#fdf8f0' },
        { label: 'Gray',  hex: '#f1f5f9' },
        { label: 'Dark',  hex: '#0f172a' },
    ];
    const ACCENT_PRESETS = [
        { label: 'Blue',   hex: '#3b82f6' },
        { label: 'Green',  hex: '#22c55e' },
        { label: 'Purple', hex: '#a855f7' },
        { label: 'Orange', hex: '#f97316' },
        { label: 'Rose',   hex: '#f43f5e' },
        { label: 'Slate',  hex: '#64748b' },
    ];
    const TOKEN_COLOR_PRESETS = [
        { label: 'Blue', hex: '#2563eb' },
        { label: 'Sky', hex: '#60a5fa' },
        { label: 'Red', hex: '#dc2626' },
        { label: 'Green', hex: '#16a34a' },
        { label: 'Purple', hex: '#7c3aed' },
        { label: 'Orange', hex: '#f97316' },
        { label: 'Pink', hex: '#db2777' },
        { label: 'Slate', hex: '#111827' },
        { label: 'Gray', hex: '#6b7280' },
        { label: 'White', hex: '#ffffff' },
    ];
    const tokenColorPicker = (
        label: string,
        tokenKey: string,
        fallback: string,
        legacyKey?: string,
        extraUpdates?: (hex: string) => Record<string, string>,
    ) => {
        const value = tokenValue(tokenKey, fallback);
        return (
            <div key={tokenKey} style={{ display: 'grid', gap: 5, padding: '8px 0', borderBottom: '1px solid #f1f5f9' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: '#334155' }}>{label}</span>
                    <span style={{ fontSize: 10, color: '#64748b', fontFamily: 'monospace' }}>{value}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexWrap: 'wrap' }}>
                    {TOKEN_COLOR_PRESETS.map(p => (
                        <button
                            key={`${tokenKey}-${p.hex}`}
                            title={p.label}
                            onClick={() => {
                                const updates = { [tokenKey]: p.hex, ...(extraUpdates ? extraUpdates(p.hex) : {}) };
                                updateTokenGroup(updates, legacyKey ? { [legacyKey]: p.hex } : undefined);
                            }}
                            style={{
                                width: 19,
                                height: 19,
                                borderRadius: 999,
                                background: p.hex,
                                cursor: 'pointer',
                                border: value.toLowerCase() === p.hex.toLowerCase() ? '2px solid #111827' : '1px solid #cbd5e1',
                                boxShadow: value.toLowerCase() === p.hex.toLowerCase() ? '0 0 0 2px #bfdbfe' : 'none',
                            }}
                        />
                    ))}
                    <span style={{ position: 'relative', width: 22, height: 22, borderRadius: 999, overflow: 'hidden', border: '1px solid #cbd5e1', cursor: 'pointer', background: value }}>
                        <input
                            aria-label={`${label} custom color`}
                            type="color"
                            value={/^#[0-9a-fA-F]{6}$/.test(value) ? value : fallback}
                            onChange={(e) => {
                                const hex = e.target.value;
                                const updates = { [tokenKey]: hex, ...(extraUpdates ? extraUpdates(hex) : {}) };
                                updateTokenGroup(updates, legacyKey ? { [legacyKey]: hex } : undefined);
                            }}
                            style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}
                        />
                    </span>
                </div>
            </div>
        );
    };

    return (
        <>
        <div ref={containerRef} style={{ 
            display: 'flex', 
            height: isFullScreen ? '90vh' : '72vh', 
            border: '1px solid #e5e7eb', 
            borderRadius: 8, 
            overflow: 'hidden',
            background: '#fff',
            transition: 'all 0.3s ease-in-out'
        }}>

            {/* -- LEFT PANEL -- */}
            <div id="tour-left-panel" style={{
                width: isFullScreen ? 0 : 272,
                flexShrink: 0,
                borderRight: isFullScreen ? 'none' : '1px solid #e5e7eb',
                display: 'flex',
                flexDirection: 'column',
                background: '#f9fafb',
                overflow: 'hidden',
                transition: 'all 0.3s ease-in-out',
                opacity: isFullScreen ? 0 : 1
            }}>

                {/* Explore / Refine mode toggle */}
                <div id="tour-mode-toggle" style={{ padding: '8px 10px', borderBottom: '1px solid #e5e7eb', display: 'flex', gap: 0, background: '#fff' }}>
                    <div style={{ display: 'flex', width: '100%', borderRadius: 6, overflow: 'hidden', border: '1px solid #d1d5db' }}>
                        {(['explore', 'refine'] as const).map(m => (
                            <button key={m} onClick={() => setDesignMode(m)}
                                style={{
                                    flex: 1, padding: '4px 0', fontSize: 12, cursor: 'pointer', border: 'none',
                                    background: designMode === m ? '#2563eb' : '#fff',
                                    color: designMode === m ? '#fff' : '#6b7280',
                                    fontWeight: designMode === m ? 600 : 400,
                                }}>
                                {m === 'explore' ? '✦ Explore' : '⟲ Refine'}
                            </button>
                        ))}
                    </div>
                </div>

                {/* EXPLORE PANEL */}
                {designMode === 'explore' && (
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                        <div id="tour-explore-prompt" style={{ padding: '10px 10px 8px', borderBottom: '1px solid #e5e7eb' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 2 }}>
                                <Typography level="title-sm" sx={{ fontSize: 13 }}>Generate 3 Candidates</Typography>
                                <button
                                    type="button"
                                    onClick={() => openPromptGuide('explore')}
                                    style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: 3,
                                        border: 'none',
                                        background: 'transparent',
                                        color: '#2563eb',
                                        fontSize: 11,
                                        cursor: 'pointer',
                                        padding: 0,
                                    }}
                                >
                                    <Info size={12} /> Guide
                                </button>
                            </div>
                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 8px' }}>Describe the actor's goals — the agent creates 3 distinct interface designs.</p>
                            <textarea
                                rows={3}
                                placeholder="e.g. Change the theme to a dark blue accent with green highlights"
                                value={explorePrompt}
                                onChange={e => setExplorePrompt(e.target.value)}
                                disabled={isGeneratingCandidates}
                                style={{ width: '100%', padding: '6px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', resize: 'none', boxSizing: 'border-box', marginBottom: 6 }}
                            />
                            {/* Prompt suggestion chips — generate style when empty, regenerate style when candidates exist */}
                            {(() => {
                                const hasCandidate = candidates.length > 0;
                                const chips = hasCandidate
                                    ? ['Purple buttons', 'Left sidebar nav', 'Compact table layout', 'Green accent', 'Dark background blue accent', 'Compact header', 'Body text 18px', 'Right sidebar width 4']
                                    : ['Green enterprise compact dashboard', 'Left sidebar with table layout', 'Blue header compact layout', 'Full width card gallery', 'Compact dashboard with dark nav', 'Teal accent right sidebar full width', 'Amber compact form larger font'];
                                return (
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
                                        {chips.map(chip => (
                                            <button
                                                key={chip}
                                                disabled={isGeneratingCandidates}
                                                onClick={() => setExplorePrompt(p => p.trim() ? `${p.trim()}, ${chip}` : chip)}
                                                style={{
                                                    background: '#f0fdf4',
                                                    border: '1px solid #bbf7d0',
                                                    borderRadius: 12,
                                                    padding: '2px 8px',
                                                    fontSize: 10,
                                                    color: '#15803d',
                                                    cursor: isGeneratingCandidates ? 'not-allowed' : 'pointer',
                                                    whiteSpace: 'nowrap',
                                                    opacity: isGeneratingCandidates ? 0.5 : 1,
                                                }}
                                            >
                                                {hasCandidate ? `+ ${chip}` : chip}
                                            </button>
                                        ))}
                                    </div>
                                );
                            })()}
                            {candidateStatus && (
                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 6px', background: '#f9fafb', padding: '4px 8px', borderRadius: 4, wordBreak: 'break-word' }}>
                                    {isGeneratingCandidates && <Loader2 size={10} style={{ display: 'inline', marginRight: 4, animation: 'spin 1s linear infinite' }} />}
                                    {candidateStatus}
                                </p>
                            )}
                            <Button
                                id="tour-generate-btn"
                                size="sm" fullWidth
                                onClick={handleGenerateCandidates}
                                loading={isGeneratingCandidates}
                                disabled={!explorePrompt.trim() || isGeneratingCandidates || !interfaceId || !systemId}
                            >
                                Generate Candidates
                            </Button>
                        </div>

                        {/* Candidate cards */}
                        <div id="tour-candidate-area" style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
                            {candidates.length === 0 && !isGeneratingCandidates && (
                                <p style={{ fontSize: 12, color: '#9ca3af', textAlign: 'center', marginTop: 24 }}>
                                    No candidates yet. Enter a prompt and generate.
                                </p>
                            )}
                            {candidates.map((candidate: any, idx: number) => {
                                const isExpanded = previewCandidateIdx === idx;
                                const compliance = candidate.compliance || null;
                                const complianceIssues = Array.isArray(compliance?.issues) ? compliance.issues : [];
                                const hasCompliance = compliance && typeof compliance.passed === 'boolean';
                                const visualCheck = candidate.visual_check || null;
                                const visualPages = Array.isArray(visualCheck?.pages) ? visualCheck.pages : [];
                                const visualIssues = visualPages.flatMap((page: any) => Array.isArray(page?.issues) ? page.issues : []);
                                const hasVisualCheck = visualCheck && (typeof visualCheck.passed === 'boolean' || visualCheck.skipped);
                                let visualCheckBackground = '#fef2f2';
                                let visualCheckBorder = '#fecaca';
                                let visualCheckColor = '#b91c1c';
                                if (visualCheck?.skipped) {
                                    visualCheckBackground = '#f8fafc';
                                    visualCheckBorder = '#e2e8f0';
                                    visualCheckColor = '#475569';
                                } else if (visualCheck?.passed) {
                                    visualCheckBackground = '#ecfdf5';
                                    visualCheckBorder = '#bbf7d0';
                                    visualCheckColor = '#166534';
                                }
                                let visualCheckMessage = `Screenshot warnings: ${visualIssues.length}`;
                                if (visualIssues.length) {
                                    visualCheckMessage += ` - ${visualIssues.slice(0, 2).join(' ')}`;
                                }
                                if (visualCheck?.skipped) {
                                    visualCheckMessage = `Screenshot check skipped: ${visualCheck.reason || 'unavailable'}`;
                                } else if (visualCheck?.passed) {
                                    visualCheckMessage = `Screenshot OK (${visualPages.length} page${visualPages.length === 1 ? '' : 's'})`;
                                }
                                let complianceMessage = 'Compliance warnings: ' + complianceIssues.length;
                                if (complianceIssues.length) {
                                    complianceMessage += ` - ${complianceIssues.slice(0, 2).join(' ')}`;
                                }
                                if (compliance?.passed) {
                                    complianceMessage = `Compliance OK (${compliance.checked || 0} checks)`;
                                }
                                return (
                                    <div key={candidate.id || candidate.name || `candidate-${idx + 1}`} style={{
                                        border: `1px solid ${isExpanded ? '#2563eb' : '#e5e7eb'}`,
                                        borderRadius: 8, marginBottom: 8, overflow: 'hidden',
                                        background: isExpanded ? '#eff6ff' : '#fff',
                                    }}>
                                        <div style={{ padding: '8px 10px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                                                <span style={{ fontSize: 13, fontWeight: 600, color: '#1f2937' }}>
                                                    {candidate.name || `Candidate ${idx + 1}`}
                                                </span>
                                                <span style={{
                                                    fontSize: 10, padding: '1px 6px', borderRadius: 10,
                                                    background: isExpanded ? '#2563eb' : '#f3f4f6',
                                                    color: isExpanded ? '#fff' : '#6b7280',
                                                }}>
                                                    {`${(candidate.pages || []).length}p · ${(candidate.sections || []).length}s`}
                                                </span>
                                            </div>
                                            {candidate.description && (
                                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 8px', lineHeight: 1.4 }}>{candidate.description}</p>
                                            )}
                                            {hasCompliance && (
                                                <div
                                                    title={complianceIssues.join('\n')}
                                                    style={{
                                                        fontSize: 10,
                                                        lineHeight: 1.35,
                                                        margin: '0 0 8px',
                                                        padding: '4px 6px',
                                                        borderRadius: 5,
                                                        background: compliance.passed ? '#ecfdf5' : '#fff7ed',
                                                        border: `1px solid ${compliance.passed ? '#bbf7d0' : '#fed7aa'}`,
                                                        color: compliance.passed ? '#166534' : '#9a3412',
                                                    }}
                                                >
                                                    {complianceMessage}
                                                </div>
                                            )}
                                            {hasVisualCheck && (
                                                <div
                                                    title={visualCheck.skipped ? visualCheck.reason : visualIssues.join('\n')}
                                                    style={{
                                                        fontSize: 10,
                                                        lineHeight: 1.35,
                                                        margin: '0 0 8px',
                                                        padding: '4px 6px',
                                                        borderRadius: 5,
                                                        background: visualCheckBackground,
                                                        border: `1px solid ${visualCheckBorder}`,
                                                        color: visualCheckColor,
                                                    }}
                                                >
                                                    {visualCheckMessage}
                                                </div>
                                            )}

                                            {/* mini preview */}
                                            {candidate.preview_html && (
                                                <div style={{ height: 90, borderRadius: 5, overflow: 'hidden', border: '1px solid #e5e7eb', marginBottom: 8, pointerEvents: 'none' }}>
                                                    <iframe
                                                        srcDoc={candidate.preview_html}
                                                        title={`candidate-${idx}-mini`}
                                                        style={{ width: '200%', height: '200%', border: 'none', transform: 'scale(0.5)', transformOrigin: 'top left', pointerEvents: 'none' }}
                                                        sandbox="allow-scripts allow-same-origin"
                                                    />
                                                </div>
                                            )}

                                            <div style={{ display: 'flex', gap: 6 }}>
                                                <button
                                                    onClick={() => {
                                                        if (!isExpanded) trackEvent('candidate_previewed', { candidate_index: idx, interface_id: interfaceId });
                                                        setPreviewCandidateIdx(isExpanded ? null : idx);
                                                    }}
                                                    style={{
                                                        flex: 1, padding: '4px 0', borderRadius: 5, fontSize: 11, cursor: 'pointer',
                                                        background: isExpanded ? '#2563eb' : '#f3f4f6',
                                                        color: isExpanded ? '#fff' : '#374151',
                                                        border: `1px solid ${isExpanded ? '#2563eb' : '#d1d5db'}`,
                                                    }}>
                                                    {isExpanded ? 'Hide' : 'Preview'}
                                                </button>
                                                <button
                                                    onClick={() => handleRegenerateCandidates(idx)}
                                                    disabled={!explorePrompt.trim() || isGeneratingCandidates}
                                                    title="Use this candidate as the baseline and regenerate 3 candidates from the current prompt"
                                                    style={{
                                                        flex: 1, padding: '4px 0', borderRadius: 5, fontSize: 11,
                                                        cursor: (!explorePrompt.trim() || isGeneratingCandidates) ? 'not-allowed' : 'pointer',
                                                        background: '#f3f4f6',
                                                        color: (!explorePrompt.trim() || isGeneratingCandidates) ? '#9ca3af' : '#374151',
                                                        border: '1px solid #d1d5db',
                                                    }}>
                                                    Regenerate 3
                                                </button>
                                                <button
                                                    onClick={() => handleApplyCandidate(idx)}
                                                    style={{
                                                        flex: 1, padding: '4px 0', borderRadius: 5, fontSize: 11, cursor: 'pointer',
                                                        background: '#2563eb', color: '#fff', border: '1px solid #2563eb', fontWeight: 600,
                                                    }}>
                                                    Apply →
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* REFINE PANEL — existing section list */}
                {designMode === 'refine' && <>

                {/* Section list */}
                <div id="tour-sections-panel" style={{ padding: '10px 10px 6px', borderBottom: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6, marginBottom: 8 }}>
                        <Typography level="title-sm" sx={{ fontSize: 13 }}>Sections</Typography>
                        <div style={{ display: 'flex', gap: 4 }}>
                            <button
                                title="Add editable header component"
                                onClick={() => {
                                    const section = makeChromeSection('logo', 'header');
                                    setSections((prev: any[]) => [...prev, section]);
                                    setPages((prev: any[]) => prev.map((page: any) => {
                                        const refs = page.sections || [];
                                        const ids = refs.map((ref: any) => typeof ref === 'string' ? ref : ref?.value);
                                        return ids.includes(section.id)
                                            ? page
                                            : { ...page, sections: [{ value: section.id }, ...refs] };
                                    }));
                                    setSelectedSectionId(section.id);
                                }}
                                style={{ ...btnBase, padding: '3px 6px', fontSize: 11, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe' }}
                            >
                                <Plus size={12} /> Header
                            </button>
                            <button
                                title="Add editable footer component"
                                onClick={() => {
                                    const section = makeChromeSection('service-bar', 'footer');
                                    setSections((prev: any[]) => [...prev, section]);
                                    setPages((prev: any[]) => prev.map((page: any) => {
                                        const refs = page.sections || [];
                                        const ids = refs.map((ref: any) => typeof ref === 'string' ? ref : ref?.value);
                                        return ids.includes(section.id)
                                            ? page
                                            : { ...page, sections: [...refs, { value: section.id }] };
                                    }));
                                    setSelectedSectionId(section.id);
                                }}
                                style={{ ...btnBase, padding: '3px 6px', fontSize: 11, background: '#f8fafc', color: '#475569', border: '1px solid #e2e8f0' }}
                            >
                                <Plus size={12} /> Footer
                            </button>
                        </div>
                    </div>
                    <div style={{ overflowY: 'auto', maxHeight: 176 }}>
                        {(sections as any[]).length === 0 && (
                            <p style={{ fontSize: 12, color: '#9ca3af', margin: 0 }}>
                                Add sections in the Section Components tab first.
                            </p>
                        )}
                        {(sections as any[]).map((s: any) => {
                            const posOpt = POSITION_OPTIONS.find(p => p.value === (s.position || 'main')) ?? POSITION_OPTIONS[2];
                            return (
                            <button
                                key={s.id}
                                onClick={() => {
                                    setSelectedRegion(null);
                                    setSelectedSectionId(s.id === selectedSectionId ? null : s.id);
                                }}
                                style={{
                                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                    width: '100%', textAlign: 'left', padding: '5px 8px',
                                    borderRadius: 5, marginBottom: 2, cursor: 'pointer',
                                    background: selectedSectionId === s.id ? '#dbeafe' : 'transparent',
                                    border: `1px solid ${selectedSectionId === s.id ? '#93c5fd' : 'transparent'}`,
                                    fontSize: 13, color: '#1f2937',
                                }}
                            >
                                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                                    {s.name || 'Unnamed'}
                                </span>
                                <span style={{ display: 'flex', gap: 3, flexShrink: 0, marginLeft: 4, alignItems: 'center' }}>
                                    {(s.position && s.position !== 'main') && (
                                        <span style={{
                                            fontSize: 9, padding: '1px 5px', borderRadius: 8,
                                            background: posOpt.bg, color: posOpt.color, border: `1px solid ${posOpt.border}`,
                                            fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em',
                                        }}>
                                            {posOpt.label}
                                        </span>
                                    )}
                                    <span style={{ fontSize: 11, color: !CHROME_LAYOUT_SET.has(s.layout as LayoutOption) && !(s.attributes?.length) && s.methods?.length ? '#9333ea' : '#6b7280' }}>
                                        {!CHROME_LAYOUT_SET.has(s.layout as LayoutOption) && !(s.attributes?.length) && s.methods?.length ? 'action' : (s.layout || 'table')}
                                    </span>
                                </span>
                            </button>
                            );
                        })}
                    </div>
                </div>

                {/* Properties panel */}
                <div id="tour-section-inspector" style={{ flex: 1, overflowY: 'auto', padding: 10 }}>
                    {selectedRegion && (
                        <>
                            <button
                                onClick={() => setSelectedRegion(null)}
                                style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer', padding: '0 0 10px', marginBottom: 2 }}
                            >
                                ← Page settings
                            </button>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 12 }}>
                                <div style={{ minWidth: 0 }}>
                                    <Typography level="title-sm" sx={{ fontSize: 13 }}>
                                        Sidebar Region
                                    </Typography>
                                    <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 2 }}>
                                        {selectedRegion.side ? `${selectedRegion.side} sidebar` : 'sidebar'} layout area
                                    </div>
                                </div>
                                <span style={{
                                    fontSize: 10,
                                    padding: '2px 7px',
                                    borderRadius: 999,
                                    background: '#fff7ed',
                                    color: '#c2410c',
                                    border: '1px solid #fed7aa',
                                    fontWeight: 700,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.04em',
                                    flexShrink: 0,
                                }}>
                                    Sidebar
                                </span>
                            </div>

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Background</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 12 }}>
                                {(['transparent', 'white', 'light', 'gray', 'dark'] as const).map(b => (
                                    <button key={b} style={{ ...btnBase, ...active(pageSidebarBg === b), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updatePageLayoutSetting(previewPageIndex, 'sidebar_bg', b === 'transparent' ? '' : b)}>
                                        {b}
                                    </button>
                                ))}
                            </div>

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Shadow</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 12 }}>
                                {(['none', 'sm', 'md', 'lg', 'xl'] as ShadowOption[]).map(s => (
                                    <button key={s} style={{ ...btnBase, ...active(pageSidebarShadow === s), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updatePageLayoutSetting(previewPageIndex, 'sidebar_shadow', s)}>
                                        {s}
                                    </button>
                                ))}
                            </div>
                        </>
                    )}
                    {!selectedRegion && !selectedSection && (
                        <>
                            <Typography level="title-sm" sx={{ mb: 1.5, fontSize: 13 }}>
                                Page Settings ({currentPage?.name || 'Untitled'})
                            </Typography>

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Page Layout</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
                                {[
                                    { label: 'Down', value: 'vertical' },
                                    { label: 'Up', value: 'vertical-reverse' },
                                    { label: 'Right', value: 'horizontal' },
                                    { label: 'Left', value: 'horizontal-reverse' },
                                ].map(opt => (
                                    <button key={opt.value} style={{ ...btnBase, ...active(pageLayout === opt.value) }}
                                        onClick={() => updatePageLayoutSetting(previewPageIndex, 'value', opt.value)}>
                                        {opt.label}
                                    </button>
                                ))}
                            </div>

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Region Width</p>
                            {[
                                { label: 'Main', field: 'main_width', value: pageMainWidth, options: ['contained', 'wide', 'full'] },
                                { label: 'Header', field: 'header_width', value: pageHeaderWidth, options: ['contained', 'full'] },
                                { label: 'Hero', field: 'hero_width', value: pageHeroWidth, options: ['contained', 'full'] },
                                { label: 'Footer', field: 'footer_width', value: pageFooterWidth, options: ['contained', 'full'] },
                            ].map(row => (
                                <div key={row.field} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                                    <span style={{ width: 44, fontSize: 11, color: '#4b5563' }}>{row.label}</span>
                                    <div style={{ display: 'flex', gap: 4 }}>
                                        {row.options.map(opt => (
                                            <button key={opt} style={{ ...btnBase, ...active(row.value === opt), padding: '3px 7px', fontSize: 11 }}
                                                onClick={() => updatePageLayoutSetting(previewPageIndex, row.field, opt)}>
                                                {opt}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ))}

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Page Gap</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 14 }}>
                                {[
                                    { label: 'Compact', value: 'compact' },
                                    { label: 'Normal', value: 'normal' },
                                    { label: 'Spacious', value: 'spacious' },
                                ].map(opt => (
                                    <button key={opt.value} style={{ ...btnBase, ...active(pageGap === opt.value), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updatePageProperty(previewPageIndex, 'gap', opt)}>
                                        {opt.label}
                                    </button>
                                ))}
                            </div>

                            {/* Global Theme */}
                            <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: 12 }}>
                                <p style={{ fontSize: 12, fontWeight: 700, color: '#111827', margin: '0 0 3px' }}>Design System Tokens</p>
                                <p style={{ fontSize: 10, color: '#64748b', margin: '0 0 8px', lineHeight: 1.35 }}>
                                    Shared tokens consumed by preview and live: colors, radius, spacing, shadows and typography.
                                </p>

                                <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: '2px 8px 8px', background: '#fff', marginBottom: 10 }}>
                                    {tokenColorPicker('Accent', 'accent.hex', '#2563eb', 'accentColor', (hex) => ({
                                        'button.ghost.text_hex': hex,
                                        'button.link.text_hex': hex,
                                        'input.border_focus_hex': hex,
                                        'badge.info.bg_hex': hex,
                                    }))}
                                    {tokenColorPicker('Page background', 'page.body.bg_hex', '#f9fafb', 'backgroundColor', (hex) => ({
                                        'page.bg.hex': hex,
                                    }))}
                                    {tokenColorPicker('Main surface', 'region.main.bg_hex', '#ffffff')}
                                    {tokenColorPicker('Text', 'page.body.text_hex', '#111827', 'textColor', (hex) => ({
                                        'text.primary.hex': hex,
                                    }))}
                                    {tokenColorPicker('Header', 'region.header.bg_hex', tokenValue('accent.hex', '#2563eb'), undefined, () => ({
                                        'region.header.text_hex': '#ffffff',
                                    }))}
                                    {tokenColorPicker('Navigation', 'nav.bg_hex', tokenValue('accent.hex', '#2563eb'), undefined, () => ({
                                        'nav.text_hex': '#ffffff',
                                    }))}
                                    {tokenColorPicker('Footer', 'region.footer.bg_hex', tokenValue('accent.hex', '#2563eb'), undefined, () => ({
                                        'region.footer.text_hex': '#ffffff',
                                    }))}
                                    {tokenColorPicker('Primary button', 'button.primary.bg_hex', tokenValue('accent.hex', '#2563eb'), undefined, (hex) => ({
                                        'button.primary.border_hex': hex,
                                        'button.primary.text_hex': '#ffffff',
                                    }))}
                                    {tokenColorPicker('Card surface', 'component.card.bg_hex', '#ffffff', undefined, (hex) => ({
                                        'component.table.bg_hex': hex,
                                        'component.list.bg_hex': hex,
                                        'component.detail.bg_hex': hex,
                                        'component.form.bg_hex': hex,
                                    }))}
                                    {tokenColorPicker('Borders', 'region.border_hex', '#e5e7eb', undefined, (hex) => ({
                                        'region.border_strong_hex': hex,
                                        'component.card.border_hex': hex,
                                        'input.border_hex': hex,
                                        'table.border_hex': hex,
                                    }))}

                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, paddingTop: 8 }}>
                                        <label style={{ display: 'grid', gap: 3 }}>
                                            <span style={{ fontSize: 10, fontWeight: 700, color: '#475569' }}>Radius</span>
                                            <select
                                                value={tokenValue('page.radius.px', String(stl.radius || '8'))}
                                                onChange={(e) => updateTokenGroup({
                                                    'page.radius.px': e.target.value,
                                                    'button.radius.px': e.target.value,
                                                    'input.radius.px': e.target.value,
                                                }, { radius: e.target.value })}
                                                style={{ height: 28, borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 11, padding: '0 7px', background: '#fff' }}
                                            >
                                                <option value="0">0</option>
                                                <option value="4">4</option>
                                                <option value="8">8</option>
                                                <option value="12">12</option>
                                                <option value="16">16</option>
                                                <option value="24">24</option>
                                            </select>
                                        </label>
                                        <label style={{ display: 'grid', gap: 3 }}>
                                            <span style={{ fontSize: 10, fontWeight: 700, color: '#475569' }}>Base spacing</span>
                                            <select
                                                value={tokenValue('spacing.md', '16px')}
                                                onChange={(e) => updateTokenGroup(spacingTokensFor(e.target.value))}
                                                style={{ height: 28, borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 11, padding: '0 7px', background: '#fff' }}
                                            >
                                                <option value="12px">Compact</option>
                                                <option value="16px">Normal</option>
                                                <option value="20px">Spacious</option>
                                            </select>
                                        </label>
                                        <label style={{ display: 'grid', gap: 3 }}>
                                            <span style={{ fontSize: 10, fontWeight: 700, color: '#475569' }}>Shadow</span>
                                            <select
                                                value={tokenValue('component.card.shadow', '0 1px 2px 0 rgb(0 0 0 / 0.05)')}
                                                onChange={(e) => {
                                                    const presets: Record<string, string> = {
                                                        none: 'none',
                                                        sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
                                                        md: '0 8px 18px -8px rgb(15 23 42 / 0.22)',
                                                        lg: '0 18px 36px -18px rgb(15 23 42 / 0.30)',
                                                    };
                                                    const shadow = presets[e.target.value] || presets.sm;
                                                    updateTokenGroup({
                                                        'shadow.sm': presets.sm,
                                                        'shadow.md': presets.md,
                                                        'shadow.lg': presets.lg,
                                                        'component.card.shadow': shadow,
                                                    });
                                                }}
                                                style={{ height: 28, borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 11, padding: '0 7px', background: '#fff' }}
                                            >
                                                <option value="none">None</option>
                                                <option value="sm">Small</option>
                                                <option value="md">Medium</option>
                                                <option value="lg">Large</option>
                                            </select>
                                        </label>
                                        <label style={{ display: 'grid', gap: 3 }}>
                                            <span style={{ fontSize: 10, fontWeight: 700, color: '#475569' }}>Font</span>
                                            <select
                                                value={tokenValue('page.font.family', stl.fontFamily || 'inter')}
                                                onChange={(e) => {
                                                    updateDesignToken('page.font.family', e.target.value);
                                                    updateStyling('fontFamily', e.target.value);
                                                }}
                                                style={{ height: 28, borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 11, padding: '0 7px', background: '#fff' }}
                                            >
                                                <option value="inter">Inter</option>
                                                <option value="roboto">Roboto</option>
                                                <option value="poppins">Poppins</option>
                                                <option value="playfair">Playfair</option>
                                                <option value="mono">Mono</option>
                                                <option value="geist">Geist</option>
                                            </select>
                                        </label>
                                    </div>

                                    <button
                                        onClick={() => {
                                            setTokens({});
                                            setStyling({});
                                        }}
                                        style={{ marginTop: 8, fontSize: 11, color: '#64748b', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, cursor: 'pointer', padding: '4px 8px' }}
                                    >
                                        Reset design system
                                    </button>
                                </div>

                                <details>
                                    <summary style={{ fontSize: 11, color: '#64748b', cursor: 'pointer', fontWeight: 700, marginBottom: 8 }}>Legacy quick presets</summary>

                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Background</p>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 8 }}>
                                    {BG_PRESETS.map(p => (
                                        <button key={p.hex} title={p.label}
                                            onClick={() => updateStyling('backgroundColor', p.hex)}
                                            style={{
                                                width: 20, height: 20, borderRadius: '50%', background: p.hex, cursor: 'pointer',
                                                border: stl.backgroundColor === p.hex ? '2px solid #2563eb' : '1.5px solid #d1d5db',
                                                outline: stl.backgroundColor === p.hex ? '2px solid #93c5fd' : 'none',
                                                outlineOffset: 1, flexShrink: 0,
                                            }} />
                                    ))}
                                    <label title="Custom colour" style={{ position: 'relative', width: 20, height: 20, borderRadius: '50%', overflow: 'hidden', cursor: 'pointer', border: '1.5px solid #d1d5db', flexShrink: 0 }}>
                                        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', fontSize: 11, background: stl.backgroundColor && !BG_PRESETS.some(p => p.hex === stl.backgroundColor) ? stl.backgroundColor : 'linear-gradient(135deg,#ff6b6b,#ffd93d,#6bcb77,#4d96ff)' }}>
                                            {stl.backgroundColor && !BG_PRESETS.some(p => p.hex === stl.backgroundColor) ? '' : '＋'}
                                        </span>
                                        <input type="color" value={stl.backgroundColor || '#ffffff'}
                                            onChange={e => updateStyling('backgroundColor', e.target.value)}
                                            style={{ position: 'absolute', opacity: 0, inset: 0, cursor: 'pointer', width: '100%', height: '100%' }} />
                                    </label>
                                    {stl.backgroundColor && <span style={{ fontSize: 10, color: '#9ca3af', fontFamily: 'monospace' }}>{stl.backgroundColor}</span>}
                                </div>

                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Accent Color</p>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 8 }}>
                                    {ACCENT_PRESETS.map(p => (
                                        <button key={p.hex} title={p.label}
                                            onClick={() => updateStyling('accentColor', p.hex)}
                                            style={{
                                                width: 20, height: 20, borderRadius: '50%', background: p.hex, cursor: 'pointer',
                                                border: stl.accentColor === p.hex ? '2px solid #1d4ed8' : '2px solid transparent',
                                                outline: stl.accentColor === p.hex ? '2px solid #93c5fd' : 'none',
                                                outlineOffset: 1, flexShrink: 0,
                                            }} />
                                    ))}
                                    <label title="Custom colour" style={{ position: 'relative', width: 20, height: 20, borderRadius: '50%', overflow: 'hidden', cursor: 'pointer', border: '1.5px solid #d1d5db', flexShrink: 0 }}>
                                        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', fontSize: 11, background: stl.accentColor && !ACCENT_PRESETS.some(p => p.hex === stl.accentColor) ? stl.accentColor : 'conic-gradient(red,yellow,lime,aqua,blue,magenta,red)' }}>
                                            {stl.accentColor && !ACCENT_PRESETS.some(p => p.hex === stl.accentColor) ? '' : '＋'}
                                        </span>
                                        <input type="color" value={stl.accentColor || '#3b82f6'}
                                            onChange={e => updateStyling('accentColor', e.target.value)}
                                            style={{ position: 'absolute', opacity: 0, inset: 0, cursor: 'pointer', width: '100%', height: '100%' }} />
                                    </label>
                                    {stl.accentColor && <span style={{ fontSize: 10, color: '#9ca3af', fontFamily: 'monospace' }}>{stl.accentColor}</span>}
                                </div>

                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Text Color</p>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 8 }}>
                                    {[{ label: 'Dark', hex: '#111827' }, { label: 'Gray', hex: '#374151' }, { label: 'Smoke', hex: '#f9fafb' }, { label: 'White', hex: '#ffffff' }].map(p => (
                                        <button key={p.hex} title={p.label}
                                            onClick={() => updateStyling('textColor', p.hex)}
                                            style={{ width: 20, height: 20, borderRadius: '50%', background: p.hex, cursor: 'pointer', border: stl.textColor === p.hex ? '2px solid #2563eb' : '1.5px solid #d1d5db', outline: stl.textColor === p.hex ? '2px solid #93c5fd' : 'none', outlineOffset: 1, flexShrink: 0 }} />
                                    ))}
                                    <span title="Custom" style={{ position: 'relative', width: 20, height: 20, borderRadius: '50%', overflow: 'hidden', cursor: 'pointer', border: '1.5px solid #d1d5db', flexShrink: 0 }}>
                                        <input aria-label="Custom text color" type="color" value={stl.textColor || '#111827'} onChange={e => updateStyling('textColor', e.target.value)}
                                            style={{ position: 'absolute', opacity: 0, inset: 0, cursor: 'pointer', width: '100%', height: '100%' }} />
                                    </span>
                                    {stl.textColor && <span style={{ fontSize: 10, color: '#9ca3af', fontFamily: 'monospace' }}>{stl.textColor}</span>}
                                </div>

                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Font</p>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 8 }}>
                                    {([{ value: 'inter', label: 'Inter' }, { value: 'roboto', label: 'Roboto' }, { value: 'poppins', label: 'Poppins' }, { value: 'playfair', label: 'Serif' }, { value: 'mono', label: 'Mono' }, { value: 'geist', label: 'Geist' }]).map(f => (
                                        <button key={f.value} style={{ ...btnBase, ...active((stl.fontFamily || 'inter') === f.value), padding: '2px 6px', fontSize: 11 }}
                                            onClick={() => updateStyling('fontFamily', f.value)}>{f.label}</button>
                                    ))}
                                </div>

                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Radius</p>
                                <div style={{ display: 'flex', gap: 3, marginBottom: 8 }}>
                                    {([{ v: '0', l: '0' }, { v: '4', l: 'S' }, { v: '8', l: 'M' }, { v: '16', l: 'L' }, { v: '24', l: 'XL' }]).map(r => (
                                        <button key={r.v} style={{ ...btnBase, ...active((stl.radius || '8') === r.v), padding: '2px 6px', fontSize: 11 }}
                                            onClick={() => updateStyling('radius', r.v)}>{r.l}</button>
                                    ))}
                                </div>

                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Button Style</p>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 8 }}>
                                    {([{ v: 'solid', l: 'Solid' }, { v: 'outline', l: 'Outline' }, { v: 'ghost', l: 'Ghost' }, { v: 'gradient', l: 'Gradient' }]).map(b => (
                                        <button key={b.v} style={{ ...btnBase, ...active((stl.buttonStyle || 'solid') === b.v), padding: '2px 6px', fontSize: 11 }}
                                            onClick={() => updateStyling('buttonStyle', b.v)}>{b.l}</button>
                                    ))}
                                </div>

                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Card Hover</p>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 8 }}>
                                    {([{ v: 'lift', l: 'Lift' }, { v: 'glow', l: 'Glow' }, { v: 'border', l: 'Border' }, { v: 'none', l: 'None' }]).map(h => (
                                        <button key={h.v} style={{ ...btnBase, ...active((stl.cardHover || 'lift') === h.v), padding: '2px 6px', fontSize: 11 }}
                                            onClick={() => updateStyling('cardHover', h.v)}>{h.l}</button>
                                    ))}
                                </div>

                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Image Ratio</p>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 8 }}>
                                    {([{ v: '1:1', l: '1:1' }, { v: '4:3', l: '4:3' }, { v: '16:9', l: '16:9' }, { v: 'portrait', l: 'Port' }, { v: 'wide', l: 'Wide' }]).map(r => (
                                        <button key={r.v} style={{ ...btnBase, ...active((stl.imageRatio || '4:3') === r.v), padding: '2px 6px', fontSize: 11 }}
                                            onClick={() => updateStyling('imageRatio', r.v)}>{r.l}</button>
                                    ))}
                                </div>

                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Page Width</p>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 8 }}>
                                    {([{ v: 'sm', l: 'SM' }, { v: 'md', l: 'MD' }, { v: 'lg', l: 'LG' }, { v: 'xl', l: 'XL' }, { v: '2xl', l: '2XL' }, { v: 'full', l: 'Full' }]).map(w => (
                                        <button key={w.v} style={{ ...btnBase, ...active((stl.pageMaxWidth || 'xl') === w.v), padding: '2px 6px', fontSize: 11 }}
                                            onClick={() => updateStyling('pageMaxWidth', w.v)}>{w.l}</button>
                                    ))}
                                </div>

                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Section Divider</p>
                                <div style={{ display: 'flex', gap: 3, marginBottom: 10 }}>
                                    {([{ v: 'none', l: 'None' }, { v: 'line', l: 'Line' }, { v: 'shadow', l: 'Shadow' }, { v: 'wave', l: 'Wave' }]).map(d => (
                                        <button key={d.v} style={{ ...btnBase, ...active((stl.divider || 'none') === d.v), padding: '2px 6px', fontSize: 11 }}
                                            onClick={() => updateStyling('divider', d.v)}>{d.l}</button>
                                    ))}
                                </div>

                                {Object.keys(stl).length > 0 && (
                                    <button onClick={() => setStyling({})}
                                        style={{ fontSize: 11, color: '#9ca3af', background: 'none', border: 'none', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}>
                                        Reset theme
                                    </button>
                                )}
                                </details>
                            </div>
                        </>
                    )}
                    {!selectedRegion && selectedSection && (
                        <>
                            <button
                                onClick={() => setSelectedSectionId(null)}
                                style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer', padding: '0 0 10px', marginBottom: 2 }}
                            >
                                ← Page settings
                            </button>
                            {(() => {
                                const posOpt = POSITION_OPTIONS.find(p => p.value === (selectedSection.position || 'main')) ?? POSITION_OPTIONS[2];
                                return (
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 12 }}>
                                        <div style={{ minWidth: 0 }}>
                                            <Typography level="title-sm" sx={{ fontSize: 13 }}>
                                                {selectedSection.name}
                                            </Typography>
                                            <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 2 }}>
                                                {selectedSection.layout || 'table'} component
                                            </div>
                                        </div>
                                        <span style={{
                                            fontSize: 10,
                                            padding: '2px 7px',
                                            borderRadius: 999,
                                            background: posOpt.bg,
                                            color: posOpt.color,
                                            border: `1px solid ${posOpt.border}`,
                                            fontWeight: 700,
                                            textTransform: 'uppercase',
                                            letterSpacing: '0.04em',
                                            flexShrink: 0,
                                        }}>
                                            {posOpt.label}
                                        </span>
                                    </div>
                                );
                            })()}

                            {showFieldComposer && (
                            <>
                            <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 8, marginBottom: 12, background: '#f9fafb' }}>
                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Fields</p>
                                <div style={{ display: 'grid', gap: 6 }}>
                                    <div>
                                        <div style={{ fontSize: 11, fontWeight: 700, color: '#166534', marginBottom: 3 }}>Editable primary fields</div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                            {editablePrimaryAttrs.length ? editablePrimaryAttrs.map((attr: any) => (
                                                <span key={attr.name} style={{ fontSize: 11, padding: '2px 6px', borderRadius: 999, background: '#dcfce7', color: '#166534', border: '1px solid #bbf7d0' }}>{attr.name}</span>
                                            )) : <span style={{ fontSize: 11, color: '#9ca3af' }}>None</span>}
                                        </div>
                                    </div>
                                    <div>
                                        <div style={{ fontSize: 11, fontWeight: 700, color: '#374151', marginBottom: 3 }}>Read-only primary fields</div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                            {readonlyPrimaryAttrs.length ? readonlyPrimaryAttrs.map((attr: any) => (
                                                <span key={attr.name} style={{ fontSize: 11, padding: '2px 6px', borderRadius: 999, background: '#f3f4f6', color: '#374151', border: '1px solid #e5e7eb' }}>{attr.name}</span>
                                            )) : <span style={{ fontSize: 11, color: '#9ca3af' }}>None</span>}
                                        </div>
                                    </div>
                                    <div>
                                        <div style={{ fontSize: 11, fontWeight: 700, color: '#7c2d12', marginBottom: 3 }}>Related read-only fields</div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                            {selectedRelatedAttrs.length ? selectedRelatedAttrs.map((attr: any) => (
                                                <span key={attr.name} style={{ fontSize: 11, padding: '2px 6px', borderRadius: 999, background: '#ffedd5', color: '#7c2d12', border: '1px solid #fed7aa' }}>{attr.name}</span>
                                            )) : <span style={{ fontSize: 11, color: '#9ca3af' }}>None</span>}
                                        </div>
                                    </div>
                                    {hiddenPrimaryFields.length > 0 && (
                                        <details>
                                            <summary style={{ fontSize: 11, fontWeight: 700, color: '#6b7280', cursor: 'pointer' }}>Hidden primary class fields ({hiddenPrimaryFields.length})</summary>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 5 }}>
                                                {hiddenPrimaryFields.map((field: string) => (
                                                    <span key={field} style={{ fontSize: 11, padding: '2px 6px', borderRadius: 999, background: '#fff', color: '#6b7280', border: '1px solid #e5e7eb' }}>{field}</span>
                                                ))}
                                            </div>
                                        </details>
                                    )}
                                </div>
                            </div>

                            <div style={{ border: '1px solid #d1d5db', borderRadius: 8, padding: 8, marginBottom: 12, background: '#fff', display: 'grid', gap: 8 }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                                    <div style={{ minWidth: 0 }}>
                                        <p style={{ fontSize: 11, color: '#111827', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 800 }}>Field Composer</p>
                                        <p style={{ fontSize: 10, color: '#6b7280', margin: '2px 0 0' }}>Configure field slots, visibility, order and sizing in a wider dialog.</p>
                                    </div>
                                    {fieldLayoutSlots.length > 0 && (
                                        <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 999, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', whiteSpace: 'nowrap' }}>
                                            {fieldLayoutSlots.length} slots
                                        </span>
                                    )}
                                </div>
                                <Button
                                    size="sm"
                                    variant="soft"
                                    onClick={() => setIsFieldComposerOpen(true)}
                                    disabled={availableFieldNames.length === 0}
                                >
                                    Open Field Composer
                                </Button>
                                {availableFieldNames.length === 0 && (
                                    <p style={{ fontSize: 11, color: '#64748b', margin: 0 }}>
                                        No fields selected for this section. Add attributes in Section Components first.
                                    </p>
                                )}
                            </div>

                            <Modal open={isFieldComposerOpen && showFieldComposer} onClose={() => setIsFieldComposerOpen(false)}>
                            <ModalDialog
                                layout="center"
                                sx={{
                                    width: 'min(920px, 92vw)',
                                    maxHeight: '86vh',
                                    overflow: 'hidden',
                                    p: 0,
                                }}
                            >
                            <ModalClose />
                            <div style={{ padding: 16, overflowY: 'auto', maxHeight: '86vh', background: '#fff' }}>
                            <div style={{ border: '1px solid #d1d5db', borderRadius: 8, padding: 12, background: '#fff' }}>
                                <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 8, marginBottom: 8 }}>
                                    <div>
                                        <p style={{ fontSize: 11, color: '#111827', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 800 }}>Field Composer</p>
                                        <p style={{ fontSize: 10, color: '#6b7280', margin: '2px 0 0' }}>Slot, visibility, order and sizing for fields this component can render.</p>
                                    </div>
                                    {fieldLayoutSlots.length > 0 && (
                                        <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 999, background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe', whiteSpace: 'nowrap' }}>
                                            {fieldLayoutSlots.length} slots
                                        </span>
                                    )}
                                </div>
                                {availableFieldNames.length === 0 ? (
                                    <p style={{ fontSize: 11, color: '#64748b', margin: 0 }}>
                                        No fields selected for this section. Add attributes in Section Components first.
                                    </p>
                                ) : (
                                    <div style={{ display: 'grid', gap: 6 }}>
                                        {orderedFieldNames.map((field) => {
                                            const cfg = fieldLayoutFields[field] || {};
                                            return (
                                                <div
                                                    key={field}
                                                    onDragOver={(e) => e.preventDefault()}
                                                    onDrop={(e) => {
                                                        e.preventDefault();
                                                        const sourceField = draggedField || e.dataTransfer.getData('text/plain');
                                                        reorderFieldLayoutFields(sourceField, field);
                                                        setDraggedField(null);
                                                    }}
                                                    style={{
                                                        border: `1px solid ${draggedField && draggedField !== field ? '#2563eb' : '#e5e7eb'}`,
                                                        borderRadius: 8,
                                                        padding: 8,
                                                        display: 'grid',
                                                        gap: 8,
                                                        background: draggedField === field ? '#eff6ff' : '#ffffff',
                                                        boxShadow: '0 1px 2px rgba(15, 23, 42, 0.05)',
                                                        opacity: draggedField === field ? 0.72 : 1,
                                                    }}
                                                >
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 5, minWidth: 0 }}>
                                                        <button
                                                            type="button"
                                                            draggable
                                                            onDragStart={(e) => {
                                                                setDraggedField(field);
                                                                e.dataTransfer.effectAllowed = 'move';
                                                                e.dataTransfer.setData('text/plain', field);
                                                            }}
                                                            onDragEnd={() => setDraggedField(null)}
                                                            aria-label={`Drag ${field}`}
                                                            title="Drag to reorder"
                                                            style={{
                                                                border: '1px solid #d1d5db',
                                                                borderRadius: 5,
                                                                background: '#f9fafb',
                                                                color: '#4b5563',
                                                                width: 24,
                                                                height: 24,
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                justifyContent: 'center',
                                                                cursor: 'grab',
                                                                padding: 0,
                                                                flexShrink: 0,
                                                            }}
                                                        >
                                                            <GripVertical size={14} />
                                                        </button>
                                                        <div style={{ fontSize: 12, fontWeight: 800, color: '#111827', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }} title={field}>{field}</div>
                                                        <span style={{ fontSize: 10, color: currentFieldSlot(field) === 'hidden' ? '#b91c1c' : '#6b7280', background: currentFieldSlot(field) === 'hidden' ? '#fee2e2' : '#f3f4f6', borderRadius: 999, padding: '2px 6px', flexShrink: 0 }}>
                                                            {currentFieldSlot(field) || 'auto'}
                                                        </span>
                                                    </div>
                                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                                                        <label style={{ display: 'grid', gap: 2 }}>
                                                            <span style={{ fontSize: 10, color: '#6b7280' }}>Slot</span>
                                                            <select
                                                                value={currentFieldSlot(field)}
                                                                onChange={(e) => updateFieldSlot(field, e.target.value)}
                                                                style={{ height: 28, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 7px', fontSize: 11, background: '#fff' }}
                                                            >
                                                                <option value="">Auto</option>
                                                                {fieldLayoutSlots.map((slot) => (
                                                                    <option key={slot.slot} value={slot.slot}>{slot.label}</option>
                                                                ))}
                                                            </select>
                                                        </label>
                                                        <label style={{ display: 'grid', gap: 2 }}>
                                                            <span style={{ fontSize: 10, color: '#6b7280' }}>Visible</span>
                                                            <select
                                                                value={cfg.visible || 'show'}
                                                                onChange={(e) => updateFieldVisibility(field, e.target.value)}
                                                                style={{ height: 28, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 7px', fontSize: 11, background: '#fff' }}
                                                            >
                                                                <option value="show">Show</option>
                                                                <option value="hidden">Hide</option>
                                                            </select>
                                                        </label>
                                                        <label style={{ display: 'grid', gap: 2 }}>
                                                            <span style={{ fontSize: 10, color: '#6b7280' }}>Order</span>
                                                            <input
                                                                type="number"
                                                                min={0}
                                                                value={cfg.order ?? ''}
                                                                onChange={(e) => updateFieldLayoutField(field, 'order', e.target.value)}
                                                                placeholder="Auto"
                                                                style={{ height: 28, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 7px', fontSize: 11 }}
                                                            />
                                                        </label>
                                                        <label style={{ display: 'grid', gap: 2 }}>
                                                            <span style={{ fontSize: 10, color: '#6b7280' }}>Width</span>
                                                            <select
                                                                value={cfg.col_span || 'auto'}
                                                                onChange={(e) => updateFieldLayoutField(field, 'col_span', e.target.value)}
                                                                style={{ height: 28, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 7px', fontSize: 11, background: '#fff' }}
                                                            >
                                                                <option value="auto">Auto</option>
                                                                <option value="3">25%</option>
                                                                <option value="4">33%</option>
                                                                <option value="6">50%</option>
                                                                <option value="8">66%</option>
                                                                <option value="12">100%</option>
                                                            </select>
                                                        </label>
                                                        <label style={{ display: 'grid', gap: 2 }}>
                                                            <span style={{ fontSize: 10, color: '#6b7280' }}>Text</span>
                                                            <select
                                                                value={cfg.text_size || 'auto'}
                                                                onChange={(e) => updateFieldLayoutField(field, 'text_size', e.target.value)}
                                                                style={{ height: 28, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 7px', fontSize: 11, background: '#fff' }}
                                                            >
                                                                <option value="auto">Auto</option>
                                                                <option value="xs">XS</option>
                                                                <option value="sm">SM</option>
                                                                <option value="md">MD</option>
                                                                <option value="lg">LG</option>
                                                                <option value="xl">XL</option>
                                                            </select>
                                                        </label>
                                                        <label style={{ display: 'grid', gap: 2 }}>
                                                            <span style={{ fontSize: 10, color: '#6b7280' }}>Height</span>
                                                            <select
                                                                value={cfg.height || 'auto'}
                                                                onChange={(e) => updateFieldLayoutField(field, 'height', e.target.value)}
                                                                style={{ height: 28, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 7px', fontSize: 11, background: '#fff' }}
                                                            >
                                                                <option value="auto">Auto</option>
                                                                <option value="sm">SM</option>
                                                                <option value="md">MD</option>
                                                                <option value="lg">LG</option>
                                                                <option value="xl">XL</option>
                                                            </select>
                                                        </label>
                                                        <label style={{ display: 'grid', gap: 2 }}>
                                                            <span style={{ fontSize: 10, color: '#6b7280' }}>Align</span>
                                                            <select
                                                                value={cfg.align || 'auto'}
                                                                onChange={(e) => updateFieldLayoutField(field, 'align', e.target.value)}
                                                                style={{ height: 28, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 7px', fontSize: 11, background: '#fff' }}
                                                            >
                                                                <option value="auto">Auto</option>
                                                                <option value="left">Left</option>
                                                                <option value="center">Center</option>
                                                                <option value="right">Right</option>
                                                            </select>
                                                        </label>
                                                        <label style={{ display: 'grid', gap: 2 }}>
                                                            <span style={{ fontSize: 10, color: '#6b7280' }}>Label</span>
                                                            <select
                                                                value={cfg.label || 'auto'}
                                                                onChange={(e) => updateFieldLayoutField(field, 'label', e.target.value)}
                                                                style={{ height: 28, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 7px', fontSize: 11, background: '#fff' }}
                                                            >
                                                                <option value="auto">Auto</option>
                                                                <option value="show">Show</option>
                                                                <option value="hidden">Hide</option>
                                                            </select>
                                                        </label>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                                {fieldLayoutSlots.length > 0 && (
                                    <details style={{ marginTop: 12, borderTop: '1px solid #e5e7eb', paddingTop: 10 }}>
                                        <summary style={{ fontSize: 11, color: '#6b7280', cursor: 'pointer', fontWeight: 700 }}>Advanced raw slots</summary>
                                        <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
                                            {fieldLayoutSlots.map((slot) => (
                                                <label key={slot.slot} style={{ display: 'grid', gap: 3 }}>
                                                    <span style={{ fontSize: 11, fontWeight: 700, color: '#374151' }}>{slot.label}</span>
                                                    {slot.multiple ? (
                                                        <input
                                                            value={fieldLayoutValue(slot.slot)}
                                                            onChange={(e) => updateFieldLayoutSlot(slot.slot, e.target.value, true)}
                                                            placeholder={availableFieldNames.slice(0, 4).join(', ')}
                                                            style={{ height: 30, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 8px', fontSize: 12 }}
                                                        />
                                                    ) : (
                                                        <select
                                                            value={fieldLayoutValue(slot.slot)}
                                                            onChange={(e) => updateFieldLayoutSlot(slot.slot, e.target.value)}
                                                            style={{ height: 30, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 8px', fontSize: 12 }}
                                                        >
                                                            <option value="">None</option>
                                                            {availableFieldNames.map((field) => (
                                                                <option key={field} value={field}>{field}</option>
                                                            ))}
                                                        </select>
                                                    )}
                                                </label>
                                            ))}
                                        </div>
                                    </details>
                                )}
                            </div>
                            </div>
                            </ModalDialog>
                            </Modal>
                            </>
                            )}

                            {showComponentSelector && (
                            <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 8, marginBottom: 12, background: '#fff' }}>
                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Component</p>
                                <select
                                    value={secComponent}
                                    onChange={(e) => updateSection(selectedSection.id, 'component', e.target.value)}
                                    style={{ width: '100%', height: 30, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 8px', fontSize: 12 }}
                                >
                                    {componentOptions.map((component) => (
                                        <option key={component} value={component}>{component}</option>
                                    ))}
                                </select>
                            </div>
                            )}

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Layout</p>
                            {isActivityAction && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                                    <span style={{ ...btnBase, ...active(true), cursor: 'default', pointerEvents: 'none' }}>Activity Button</span>
                                    <span style={{ fontSize: 11, color: '#9ca3af' }}>workflow step action</span>
                                </div>
                            )}
                            {!isActivityAction && isMethodOnly && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                                    <span style={{ ...btnBase, ...active(true), cursor: 'default', pointerEvents: 'none' }}>Action Panel</span>
                                    <span style={{ fontSize: 11, color: '#9ca3af' }}>auto — no attributes</span>
                                </div>
                            )}
                            {!isActivityAction && !isMethodOnly && (
                                <div style={{ marginBottom: 10 }}>
                                    {layoutGroupsForSelected.map(group => (
                                        <div key={group.label} style={{ marginBottom: 4 }}>
                                            <p style={{ fontSize: 9, color: '#9ca3af', margin: '0 0 2px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{group.label}</p>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                                                {group.options.map(opt => (
                                                    <button key={opt.value} style={{ ...btnBase, ...active(secLayout === opt.value), padding: '3px 6px', fontSize: 11 }}
                                                        onClick={() => updateSection(selectedSection.id, 'layout', opt.value)}>
                                                        {opt.icon}{opt.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Position</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 10 }}>
                                {POSITION_OPTIONS.map(opt => {
                                    const curPos = selectedSection.position || 'main';
                                    const isActive = curPos === opt.value;
                                    return (
                                        <button key={opt.value}
                                            onClick={() => setSections((prev: any[]) => prev.map((s: any) =>
                                                s.id === selectedSection.id ? { ...s, position: opt.value } : s
                                            ))}
                                            style={{
                                                ...btnBase, padding: '3px 7px', fontSize: 11,
                                                background: isActive ? opt.bg : '#fff',
                                                color: isActive ? opt.color : '#374151',
                                                border: `1px solid ${isActive ? opt.border : '#d1d5db'}`,
                                            }}>
                                            {opt.label}
                                        </button>
                                    );
                                })}
                            </div>

                            {hasControl('sidebar_side') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Sidebar Side</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {([{value:'left',label:'Left'},{value:'right',label:'Right'}] as {value:SidebarSideOption;label:string}[]).map(o => (
                                    <button key={o.value} style={{ ...btnBase, ...active(secSidebarSide === o.value), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'sidebar_side', o.value)}>{o.label}</button>
                                ))}
                            </div></>)}

                            {hasControl('sidebar_width') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Sidebar Width</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {[2,3,4,5,6].map(n => (
                                    <button key={n} style={{ ...btnBase, ...active(secSidebarWidth === n), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'sidebar_width', n)}>{n}/12</button>
                                ))}
                            </div></>)}

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Width</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {COL_SPAN_OPTIONS.map(opt => (
                                    <button key={opt.value} style={{ ...btnBase, ...active(secColSpan === opt.value), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'col_span', opt.value)}>
                                        {opt.label}
                                    </button>
                                ))}
                            </div>

                            {!isChromeOrControlSection && (
                            <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 8, marginBottom: 12, background: '#f9fafb' }}>
                                <p style={{ fontSize: 11, color: '#374151', margin: '0 0 6px', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>Query / Interaction</p>
                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px' }}>Data Source From</p>
                                <div style={{ width: '100%', minHeight: 30, borderRadius: 6, border: '1px solid #e5e7eb', padding: '6px 8px', fontSize: 12, marginBottom: 4, boxSizing: 'border-box', background: '#f9fafb', color: '#374151' }}>
                                    {selectedPrimaryModel || 'Select a primary class first'}
                                </div>
                                <p style={{ fontSize: 10, color: '#9ca3af', margin: '0 0 8px' }}>Query returns this primary class. Joins can reference other classes, but the rendered records stay on this class.</p>
                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px' }}>Limit</p>
                                <input
                                    type="number"
                                    min="1"
                                    value={selectedSection.query?.limit || ''}
                                    onChange={e => updateSection(selectedSection.id, 'query_limit', e.target.value)}
                                    placeholder="e.g. 4"
                                    style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 8, boxSizing: 'border-box' }}
                                />
                                {(['card', 'list', 'table', 'gallery', 'timeline', 'map'].includes(secLayout) || ['object_collection', 'child_collection', 'related_collection'].includes(String(selectedSection.role || ''))) && (
                                    <>
                                        <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px' }}>Item Click Action</p>
                                        <select
                                            value={selectedSection.behavior?.item_click?.type || 'none'}
                                            onChange={e => updateSection(selectedSection.id, 'item_click_type', e.target.value)}
                                            style={{ width: '100%', height: 30, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 8px', fontSize: 12, marginBottom: 8 }}
                                        >
                                            <option value="none">None</option>
                                            <option value="navigate">Navigate</option>
                                            <option value="select">Select</option>
                                        </select>
                                        {selectedSection.behavior?.item_click?.type === 'navigate' && (
                                            <select
                                                value={selectedSection.behavior?.item_click?.target_page || ''}
                                                onChange={e => updateSection(selectedSection.id, 'item_click_target_page', e.target.value)}
                                                style={{ width: '100%', height: 30, borderRadius: 6, border: '1px solid #d1d5db', padding: '0 8px', fontSize: 12 }}
                                            >
                                                <option value="">Target page</option>
                                                {(pages as any[]).filter((p: any) => !p.type || p.type?.value !== 'activity').map((p: any) => (
                                                    <option key={p.id || p.name} value={p.name}>{p.name}</option>
                                                ))}
                                            </select>
                                        )}
                                    </>
                                )}
                            </div>
                            )}

                            {hasControl('logo_url') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Logo Image URL</p>
                            <input type="text" placeholder="https://.../logo.png"
                                value={secStyle.logo_url ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'logo_url', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('logo_size') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Logo Size</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['sm','md','lg','xl'] as LogoSizeOption[]).map(v => (
                                    <button key={v} style={{ ...btnBase, ...active(secLogoSize === v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'logo_size', v)}>{v}</button>
                                ))}
                            </div></>)}

                            {hasControl('logo_shape') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Logo Shape</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['rounded','circle','square'] as LogoShapeOption[]).map(v => (
                                    <button key={v} style={{ ...btnBase, ...active(secLogoShape === v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'logo_shape', v)}>{v}</button>
                                ))}
                            </div></>)}

                            {hasControl('logo_variant') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Logo Variant</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
                                {([{value:'lockup',label:'Image + Text'},{value:'image-only',label:'Image Only'},{value:'text-only',label:'Text Only'}] as {value:LogoVariantOption;label:string}[]).map(o => (
                                    <button key={o.value} style={{ ...btnBase, ...active(secLogoVariant === o.value), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'logo_variant', o.value)}>{o.label}</button>
                                ))}
                            </div></>)}

                            {hasControl('action_variant') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Action Style</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['link','ghost','button'] as ActionVariantOption[]).map(v => (
                                    <button key={v} style={{ ...btnBase, ...active(secActionVariant === v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'action_variant', v)}>{v}</button>
                                ))}
                            </div></>)}

                            {hasControl('show_logout') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Logout Link</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {([{value:true,label:'Show'},{value:false,label:'Hide'}] as {value:boolean;label:string}[]).map(o => (
                                    <button key={String(o.value)} style={{ ...btnBase, ...active(secShowLogout === o.value), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'show_logout', o.value)}>{o.label}</button>
                                ))}
                            </div></>)}

                            {/* card: display_mode */}
                            {hasControl('display_mode') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Display</p>
                            <div style={{ display: 'flex', gap: 3, marginBottom: 10 }}>
                                {([{v:'grid',l:'Grid'},{v:'carousel',l:'Carousel'},{v:'banner',l:'Banner'}] as {v:DisplayModeOption;l:string}[]).map(o => (
                                    <button key={o.v} style={{ ...btnBase, ...active(secDisplayMode === o.v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'display_mode', o.v)}>{o.l}</button>
                                ))}
                            </div></>)}

                            {/* card: card_style */}
                            {hasControl('card_style') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Card Style</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 10 }}>
                                {([{v:'default',l:'Default'},{v:'product',l:'Product'},{v:'category',l:'Category'},{v:'compact',l:'Compact'}] as {v:CardStyleOption;l:string}[]).map(o => (
                                    <button key={o.v} style={{ ...btnBase, ...active(secCardStyle === o.v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'card_style', o.v)}>{o.l}</button>
                                ))}
                            </div></>)}

                            {/* list: list_style */}
                            {hasControl('list_style') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>List Style</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 10 }}>
                                {([{v:'default',l:'Default'},{v:'product',l:'Product'},{v:'cart-item',l:'Line Item'},{v:'related',l:'Related'}] as {v:ListStyleOption;l:string}[]).map(o => (
                                    <button key={o.v} style={{ ...btnBase, ...active(secListStyle === o.v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'list_style', o.v)}>{o.l}</button>
                                ))}
                            </div></>)}

                            {/* form: form_style */}
                            {hasControl('form_style') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Form Style</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginBottom: 10 }}>
                                {([{v:'default',l:'Default'},{v:'auth',l:'Auth'},{v:'step',l:'Step'},{v:'summary',l:'Summary'}] as {v:FormStyleOption;l:string}[]).map(o => (
                                    <button key={o.v} style={{ ...btnBase, ...active(secFormStyle === o.v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'form_style', o.v)}>{o.l}</button>
                                ))}
                            </div></>)}

                            {/* columns */}
                            {hasControl('columns') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Columns</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {['2','3','4','5','6'].map(n => (
                                    <button key={n} style={{ ...btnBase, ...active(secColumns === n), width: 28, justifyContent: 'center' }}
                                        onClick={() => updateSection(selectedSection.id, 'columns', n)}>{n}</button>
                                ))}
                            </div></>)}

                            {hasControl('banner_height') && secDisplayMode === 'banner' && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Banner Height</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['sm','md','lg','xl'] as BannerHeightOption[]).map(h => (
                                    <button key={h} style={{ ...btnBase, ...active(secBannerHeight === h), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'banner_height', h)}>{h}</button>
                                ))}
                            </div></>)}

                            {hasControl('image_ratio') && secDisplayMode === 'banner' && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Image Ratio</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
                                {(['wide','16:9','4:3','1:1','portrait'] as ImageRatioOption[]).map(r => (
                                    <button key={r} style={{ ...btnBase, ...active(secImageRatio === r), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'image_ratio', r)}>{r}</button>
                                ))}
                            </div></>)}

                            {/* image_position (detail) */}
                            {hasControl('image_position') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Image Position</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {([{value:'left',label:'Left'},{value:'top',label:'Top'},{value:'right',label:'Right'}] as {value:ImagePositionOption;label:string}[]).map(o => (
                                    <button key={o.value} style={{ ...btnBase, ...active(secImagePosition === o.value), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'image_position', o.value)}>{o.label}</button>
                                ))}
                            </div>
                            {secImagePosition !== 'top' && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Image Size</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {([{value:'sm',label:'Small'},{value:'md',label:'Medium'},{value:'lg',label:'Large'}] as {value:ImageSizeOption;label:string}[]).map(o => (
                                    <button key={o.value} style={{ ...btnBase, ...active(secImageSize === o.value), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'image_size', o.value)}>{o.label}</button>
                                ))}
                            </div></>)}</>)}

                            {/* universal style */}
                            {hasControl('color') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Color</p>
                            <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
                                {COLOR_OPTIONS.map(c => (
                                    <button key={c} title={c} onClick={() => updateSection(selectedSection.id, 'color', c)}
                                        style={{ width: 22, height: 22, borderRadius: '50%', background: COLOR_HEX[c], cursor: 'pointer',
                                            border: secColor === c ? `3px solid ${COLOR_HEX[c]}` : '2px solid transparent',
                                            outline: secColor === c ? '2px solid #93c5fd' : 'none', outlineOffset: 1 }} />
                                ))}
                            </div></>)}

                            {hasControl('density') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Density</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['compact','normal','spacious'] as DensityOption[]).map(d => (
                                    <button key={d} style={{ ...btnBase, ...active(secDensity === d), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'density', d)}>{d}</button>
                                ))}
                            </div></>)}

                            {hasControl('nav_height') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Nav Height</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['compact','normal','tall','xl'] as NavHeightOption[]).map(h => (
                                    <button key={h} style={{ ...btnBase, ...active(secNavHeight === h), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'nav_height', h)}>{h}</button>
                                ))}
                            </div></>)}

                            {hasControl('shadow') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Shadow</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['none','sm','md','lg','xl'] as ShadowOption[]).map(s => (
                                    <button key={s} style={{ ...btnBase, ...active(secShadow === s), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'shadow', s)}>{s}</button>
                                ))}
                            </div></>)}

                            {hasControl('border') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Border</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['none','light','colored','strong'] as BorderOption[]).map(b => (
                                    <button key={b} style={{ ...btnBase, ...active(secBorder === b), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'border', b)}>{b}</button>
                                ))}
                            </div></>)}

                            {hasControl('bg') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Background</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['white','light','gray','dark'] as BgOption[]).map(b => (
                                    <button key={b} style={{ ...btnBase, ...active(secBg === b), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'bg', b)}>{b}</button>
                                ))}
                            </div></>)}

                            {hasControl('header_style') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Section Title</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
                                {([{value:'default',label:'Default'},{value:'large',label:'Large'},{value:'small',label:'Small'},{value:'colored',label:'Colored'},{value:'hidden',label:'Hidden'}] as {value:HeaderStyleOption;label:string}[]).map(o => (
                                    <button key={o.value} style={{ ...btnBase, ...active(secHeaderStyle === o.value), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'header_style', o.value)}>{o.label}</button>
                                ))}
                            </div></>)}

                            {/* label inputs */}
                            {hasControl('tagline') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Logo Tagline</p>
                            <input type="text" placeholder="Short subtitle under the brand"
                                value={secStyle.tagline ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'tagline', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('logout_label') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Logout Label</p>
                            <input type="text" placeholder="Logout"
                                value={secStyle.logout_label ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'logout_label', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('cta_label') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>CTA Button Label</p>
                            <input type="text" placeholder="e.g. In winkelwagen"
                                value={secStyle.cta_label ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'cta_label', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('success_page') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>After Submit → Go to Page</p>
                            <input type="text" placeholder="e.g. view_cart"
                                value={secStyle.success_page ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'success_page', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('seller_label') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Seller Label</p>
                            <input type="text" placeholder="e.g. Verkoop door bol"
                                value={secStyle.seller_label ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'seller_label', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('availability_label') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Availability Label</p>
                            <input type="text" placeholder="e.g. Op voorraad"
                                value={secStyle.availability_label ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'availability_label', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('delivery_label') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Delivery Label</p>
                            <input type="text" placeholder="e.g. ✓ Morgen in huis"
                                value={secStyle.delivery_label ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'delivery_label', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('login_label') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Login Button Label</p>
                            <input type="text" placeholder="e.g. Inloggen"
                                value={secStyle.login_label ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'login_label', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('step_icon') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Step Icon (emoji)</p>
                            <input type="text" placeholder="e.g. 📦 🏠 💳"
                                value={secStyle.step_icon ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'step_icon', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('total_label') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Label</p>
                            <input type="text" placeholder="e.g. Nog te betalen:"
                                value={secStyle.total_label ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'total_label', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('activity_label') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Activity Button Label</p>
                            <input type="text" placeholder="e.g. Complete step"
                                value={selectedSection.label ?? selectedSection.name ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'label', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            /></>)}

                            {hasControl('activity_workflow_action') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Workflow Action</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
                                {(['complete','navigate','complete_then_page'] as const).map(v => (
                                    <button key={v} style={{ ...btnBase, ...active((selectedSection.workflow?.action || 'complete') === v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'workflow_action', v)}>{v}</button>
                                ))}
                            </div></>)}

                            {hasControl('activity_target_page') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Target Page</p>
                            <select
                                value={selectedSection.workflow?.target_page ?? ''}
                                onChange={e => updateSection(selectedSection.id, 'workflow_target_page', e.target.value)}
                                style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                            >
                                <option value="">Auto next workflow page</option>
                                {(pages as any[]).map((p: any) => <option key={p.id || p.name} value={p.name}>{p.name}</option>)}
                            </select></>)}

                            {hasControl('activity_variant') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Activity Variant</p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
                                {(['button','wizard_next','link','fab','auto'] as const).map(v => (
                                    <button key={v} style={{ ...btnBase, ...active((secStyle.variant || 'button') === v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'variant', v)}>{v}</button>
                                ))}
                            </div></>)}

                            {hasControl('activity_align') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Activity Align</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['left','center','right'] as const).map(v => (
                                    <button key={v} style={{ ...btnBase, ...active((secStyle.align || 'right') === v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'align', v)}>{v}</button>
                                ))}
                            </div></>)}

                            {hasControl('activity_size') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Activity Size</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['sm','md','lg'] as const).map(v => (
                                    <button key={v} style={{ ...btnBase, ...active((secStyle.size || 'lg') === v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'size', v)}>{v}</button>
                                ))}
                            </div></>)}

                            {hasControl('text') && (
                                <>
                                    <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 2px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Text</p>
                                    {METHODS_HINTS[secLayout] && (
                                        <p style={{ fontSize: 10, color: '#9ca3af', margin: '0 0 4px' }}>{METHODS_HINTS[secLayout]}</p>
                                    )}
                                    <input
                                        type="text"
                                        placeholder="Brand name, search placeholder, footer note..."
                                        value={selectedSection.text ?? ''}
                                        onChange={e => updateSection(selectedSection.id, 'text', e.target.value)}
                                        style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, boxSizing: 'border-box' }}
                                    />
                                </>
                            )}

                            {hasControl('methods') && (
                                <>
                                    <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 2px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Section Actions (one per line)</p>
                                    <p style={{ fontSize: 10, color: '#9ca3af', margin: '0 0 4px' }}>Rendered once for the whole section, not once per record.</p>
                                    {!hasControl('text') && METHODS_HINTS[secLayout] && (
                                        <p style={{ fontSize: 10, color: '#9ca3af', margin: '0 0 4px' }}>{METHODS_HINTS[secLayout]}</p>
                                    )}
                                    <textarea
                                        rows={4}
                                        placeholder="Gratis verzending vanaf €25,-&#10;Bezorging zelfde dag*&#10;Gratis retourneren"
                                        value={(selectedSection.methods || []).map((m: any) =>
                                            typeof m === 'string' ? m : (m?.name || m?.label || '')
                                        ).join('\n')}
                                        onChange={e => {
                                            const lines = e.target.value.split('\n').map((l: string) => ({ name: l }));
                                            setSections((prev: any[]) => prev.map((s: any) =>
                                                s.id === selectedSection.id ? { ...s, methods: lines } : s
                                            ));
                                        }}
                                        style={{ width: '100%', padding: '4px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', marginBottom: 10, resize: 'vertical', boxSizing: 'border-box' }}
                                    />
                                </>
                            )}
                        </>
                    )}
                </div>

                {/* AI generate */}
                <div style={{ borderTop: '1px solid #e5e7eb' }}>
                    <button
                        type="button"
                        style={{ display: 'flex', width: '100%', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', cursor: 'pointer', userSelect: 'none', border: 0, background: 'transparent', textAlign: 'left' }}
                        onClick={() => setIsAIExpanded(v => !v)}
                    >
                        <Typography level="title-sm" sx={{ fontSize: 13 }}>AI Generate</Typography>
                        <span style={{ fontSize: 10, color: '#9ca3af' }}>{isAIExpanded ? '▲' : '▼'}</span>
                    </button>

                    {isAIExpanded && (
                        <div style={{ padding: '0 12px 12px' }}>
                            {/* Width chip for the first available main section */}
                            {(() => {
                                const mainSection = selectedSection
                                    || (sections as any[]).find((s: any) => !s.position || s.position === 'main');
                                const compName = mainSection?.component || mainSection?.layout || null;
                                if (!compName) return null;
                                const suggestion = `Change width of ${compName} to 1/3`;
                                return (
                                    <div style={{ marginBottom: 10 }}>
                                        <button
                                            onClick={() => setCurrentPrompt(suggestion)}
                                            style={{
                                                fontSize: 10, padding: '2px 8px', borderRadius: 12,
                                                background: '#eff6ff', color: '#1d4ed8', border: '1px solid #dbeafe',
                                                cursor: 'pointer', whiteSpace: 'nowrap',
                                            }}
                                        >
                                            {suggestion}
                                        </button>
                                    </div>
                                );
                            })()}

                            {agentStatus && (
                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 6px', background: '#f9fafb', padding: '4px 8px', borderRadius: 4 }}>
                                    {agentStatus}
                                </p>
                            )}
                            <div id="tour-prompt-panel" style={{ display: 'flex', gap: 6 }}>
                                <input
                                    type="text"
                                    placeholder="Describe a design change..."
                                    value={currentPrompt}
                                    onChange={e => setCurrentPrompt(e.target.value)}
                                    onKeyDown={e => { if (e.key === 'Enter') handleSendMessage(); }}
                                    disabled={isLoadingAgent}
                                    style={{ flex: 1, padding: '6px 10px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', outline: 'none' }}
                                />
                                <Button size="sm" onClick={handleSendMessage}
                                    loading={isLoadingAgent} disabled={!currentPrompt.trim() || isLoadingAgent}>
                                    Go
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
                </>}
            </div>

            {/* -- RIGHT PANEL (preview) -- */}
            <div id="tour-preview-area" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

                {/* Toolbar */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderBottom: '1px solid #e5e7eb', background: '#fff', flexWrap: 'wrap' }}>
                    {/* Design / Live toggle */}
                    <div id="tour-design-live-toggle" style={{ display: 'flex', borderRadius: 6, overflow: 'hidden', border: '1px solid #d1d5db', marginRight: 4 }}>
                        {(['design', 'live'] as const).map(mode => (
                            <button key={mode} onClick={() => mode === 'live' ? handleSwitchToLive() : setPreviewMode(mode)}
                                style={{
                                    padding: '2px 10px', fontSize: 12, cursor: 'pointer', border: 'none',
                                    background: previewMode === mode ? '#1d4ed8' : '#fff',
                                    color: previewMode === mode ? '#fff' : '#6b7280',
                                }}>
                                {mode === 'design' ? 'Design' : 'Live'}
                            </button>
                        ))}
                    </div>
                    <span id="tour-page-tabs" style={{ display: 'contents' }}>
                    {previewMode === 'design' && (visiblePages as any[]).map((p: any, idx: number) => (
                        <button key={p.id || p.name || `page-${idx + 1}`} onClick={() => {
                            setPreviewPageIndex(idx);
                            setSelectedSectionId(null);
                            setSelectedRegion(null);
                        }}
                            style={{
                                display: 'flex', alignItems: 'center', gap: 5,
                                padding: '2px 8px', borderRadius: 10, fontSize: 12, cursor: 'pointer',
                                background: previewPageIndex === idx ? '#dbeafe' : '#f3f4f6',
                                color: previewPageIndex === idx ? '#1d4ed8' : '#6b7280',
                                border: 'none',
                            }}>
                            <span>{p.name || `Page ${idx + 1}`}</span>
                            {isActivityPage(p) && (
                                <span style={{
                                    fontSize: 9,
                                    lineHeight: '14px',
                                    padding: '0 6px',
                                    borderRadius: 999,
                                    background: '#dcfce7',
                                    color: '#15803d',
                                    border: '1px solid #86efac',
                                    fontWeight: 700,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.03em',
                                }}>
                                    Activity
                                </span>
                            )}
                        </button>
                    ))}
                    </span>
                    <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
                        {previewMode === 'design' && isRefreshing && <Loader2 size={14} style={{ color: '#9ca3af', animation: 'spin 1s linear infinite' }} />}

                        {/* Full Screen Toggles */}
                        <div style={{ display: 'flex', gap: 2, marginRight: 4 }}>
                            <button onClick={() => setIsFullScreen(!isFullScreen)} title={isFullScreen ? "Exit Focus Mode" : "Focus Mode (Hide Sidebar)"}
                                style={{ display: 'flex', alignItems: 'center', padding: '4px', borderRadius: 6, border: '1px solid #d1d5db', background: isFullScreen ? '#eff6ff' : '#fff', cursor: 'pointer', color: isFullScreen ? '#1d4ed8' : '#6b7280' }}>
                                {isFullScreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                            </button>
                            <button onClick={toggleBrowserFullScreen} title="Browser Fullscreen"
                                style={{ display: 'flex', alignItems: 'center', padding: '4px', borderRadius: 6, border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer', color: '#6b7280' }}>
                                <Monitor size={14} />
                            </button>
                        </div>

                        {previewMode === 'design' && (
                            <button onClick={doRefreshPreview}
                                style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 6, border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer', fontSize: 12 }}>
                                <RefreshCw size={12} />Refresh
                            </button>
                        )}
                        {previewMode === 'live' && (
                            <button onClick={() => setLiveKey((k: number) => k + 1)}
                                style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 6, border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer', fontSize: 12 }}>
                                <RefreshCw size={12} />Refresh
                            </button>
                        )}
                        {previewMode === 'live' && (
                            <div id="tour-live-user-btn" style={{ position: 'relative' }}>
                                {isEditingLiveUser ? (
                                    <form
                                        onSubmit={e => {
                                            e.preventDefault();
                                            const val = liveUserDraft.trim();
                                            if (val) { setLiveUser(val); setLiveKey(k => k + 1); }
                                            setIsEditingLiveUser(false);
                                        }}
                                        style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                                    >
                                        <input
                                            autoFocus
                                            value={liveUserDraft}
                                            onChange={e => setLiveUserDraft(e.target.value)}
                                            onBlur={() => setIsEditingLiveUser(false)}
                                            placeholder="username"
                                            style={{
                                                width: 120, padding: '2px 7px', fontSize: 12,
                                                border: '1px solid #93c5fd', borderRadius: 6,
                                                outline: 'none',
                                            }}
                                        />
                                    </form>
                                ) : (
                                    <button
                                        onClick={() => { setLiveUserDraft(liveUser); setIsEditingLiveUser(true); }}
                                        title="Change the logged-in prototype user"
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: 5,
                                            padding: '2px 8px', borderRadius: 6, fontSize: 12,
                                            border: '1px solid #bfdbfe', background: '#eff6ff',
                                            color: '#1d4ed8', cursor: 'pointer',
                                        }}>
                                        <User size={12} />
                                        {liveUser}
                                    </button>
                                )}
                            </div>
                        )}
                        <button id="tour-map-uml-btn" onClick={handleMapUml} disabled={isMapping || !interfaceId}
                            title="Map UML diagrams to interface pages and sections via AI"
                            style={{
                                display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 6, fontSize: 12,
                                cursor: isMapping ? 'default' : 'pointer',
                                border: `1px solid ${mapTone.border}`,
                                background: mapTone.background,
                                color: mapTone.color,
                                opacity: isMapping || !interfaceId ? 0.6 : 1,
                            }}>
                            {isMapping ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Wand2 size={12} />}
                            {mapButtonLabel}
                        </button>
                        <button onClick={handleSeedData} disabled={isSeedingData}
                            style={{
                                display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 6, fontSize: 12, cursor: isSeedingData ? 'default' : 'pointer',
                                border: `1px solid ${seedTone.border}`,
                                background: seedTone.background,
                                color: seedTone.color,
                                opacity: isSeedingData ? 0.6 : 1,
                            }}>
                            {isSeedingData ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Database size={12} />}
                            {seedButtonLabel}
                        </button>
                        <button id="tour-sync-live-btn" onClick={handleSyncLivePrototype} disabled={isSyncingLive || !interfaceId || !systemId}
                            title="Regenerate a live prototype from the current preview"
                            style={{
                                display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 6, fontSize: 12,
                                cursor: isSyncingLive ? 'default' : 'pointer',
                                border: `1px solid ${syncTone.border}`,
                                background: syncTone.background,
                                color: syncTone.color,
                                opacity: isSyncingLive ? 0.6 : 1,
                            }}>
                            {isSyncingLive ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <RefreshCw size={12} />}
                            {syncButtonLabel}
                        </button>
                        <button onClick={handleVisualCheck} disabled={isVisualChecking || !interfaceId}
                            title={visualCheckSummary || 'Compare current design schema against the live prototype'}
                            style={{
                                display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 6, fontSize: 12,
                                cursor: isVisualChecking ? 'default' : 'pointer',
                                border: `1px solid ${visualCheckTone.border}`,
                                background: visualCheckTone.background,
                                color: visualCheckTone.color,
                                opacity: isVisualChecking ? 0.6 : 1,
                            }}>
                            {isVisualChecking ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Monitor size={12} />}
                            {visualCheckButtonLabel}
                        </button>
                        <button onClick={handleViewGeneratorMetadata} disabled={!interfaceId || !systemId || isLoadingMetadata}
                            title="View metadata sent to the prototype generator"
                            style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, borderRadius: 6,
                                border: '1px solid #d1d5db', background: '#fff', color: '#4b5563',
                                cursor: !interfaceId || !systemId || isLoadingMetadata ? 'default' : 'pointer',
                                opacity: !interfaceId || !systemId || isLoadingMetadata ? 0.55 : 1,
                            }}>
                            {isLoadingMetadata ? <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} /> : <Code2 size={13} />}
                        </button>
                        <button
                            onClick={() => {
                                const actor = systemClassifiers.find(
                                    (cls: any) => String(cls?.id) === String(currentInterface?.actor)
                                );
                                const actorName = String(
                                    actor?.data?.name || currentInterface?.name || 'Actor'
                                );
                                startWorkflowGuidance({
                                    allPages: pages as any[],
                                    allSections: sections as any[],
                                    actorName,
                                    switchToLive: () => {
                                        setPreviewMode('live');
                                        setLiveKey((k: number) => k + 1);
                                    },
                                    navigateToPage: (idx) => {
                                        setPreviewPageIndex(idx);
                                        setSelectedSectionId(null);
                                        setLiveKey((k: number) => k + 1);
                                    },
                                    switchActor: (username) => {
                                        setLiveUser(username);
                                        setLiveKey((k: number) => k + 1);
                                    },
                                });
                            }}
                            title="Test workflow step-by-step"
                            style={{
                                display: 'flex', alignItems: 'center', gap: 4,
                                padding: '3px 8px', borderRadius: 6, fontSize: 12,
                                border: '1px solid #a7f3d0', background: '#ecfdf5',
                                color: '#065f46', cursor: 'pointer',
                            }}>
                            <PlayCircle size={13} />
                            Test Workflow
                        </button>
                        <button
                            onClick={() => startInterfaceTour({ switchToExplore: () => setDesignMode('explore'), switchToRefine: () => setDesignMode('refine') })}
                            title="Start guided tour"
                            style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                width: 28, height: 28, borderRadius: 6,
                                border: '1px solid #d1d5db', background: '#fff',
                                color: '#6b7280', cursor: 'pointer',
                            }}>
                            <HelpCircle size={14} />
                        </button>
                    </div>
                </div>

                {/* iframe */}
                <div style={{ flex: 1, overflow: 'hidden', background: '#f8fafc' }}>
                    {previewMode === 'live' && (
                        <iframe
                            key={`live-${liveKey}-${previewPageIndex}`}
                            src={`${prototypeURL}/autologin?as=${encodeURIComponent(liveUser)}&next=${encodeURIComponent(livePathForPage(currentInterface?.name, selectedVisiblePage))}`}
                            title="Live prototype"
                            style={{ width: '100%', height: '100%', border: 'none' }}
                        />
                    )}
                    {previewMode !== 'live' && designMode === 'explore' && selectedCandidateHtml && (
                        <iframe
                            key={`candidate-${previewCandidateIdx}-${previewPageIndex}`}
                            srcDoc={selectedCandidateHtml}
                            title={`Candidate ${previewCandidateIdx + 1} preview`}
                            style={{ width: '100%', height: '100%', border: 'none' }}
                            sandbox="allow-scripts allow-same-origin"
                        />
                    )}
                    {previewMode !== 'live' && designMode === 'explore' && !selectedCandidateHtml && (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', flexDirection: 'column', gap: 12 }}>
                            <p style={{ fontSize: 13, color: '#9ca3af' }}>
                                {candidatePreviewMessage}
                            </p>
                            {isGeneratingCandidates && <Loader2 size={20} style={{ color: '#9ca3af', animation: 'spin 1s linear infinite' }} />}
                        </div>
                    )}
                    {previewMode !== 'live' && designMode !== 'explore' && previewHtml && !previewError && (
                        <iframe
                            key={`${interfaceId}-${previewPageIndex}`}
                            srcDoc={previewHtml}
                            title="Page preview"
                            style={{ width: '100%', height: '100%', border: 'none' }}
                            sandbox="allow-scripts allow-same-origin"
                        />
                    )}
                    {previewMode !== 'live' && designMode !== 'explore' && (!previewHtml || previewError) && (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                            <p style={{ fontSize: 13, color: '#9ca3af' }}>
                                {previewEmptyMessage}
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
        <Modal open={isPromptGuideOpen} onClose={() => setIsPromptGuideOpen(false)}>
            <ModalDialog
                variant="plain"
                sx={{
                    width: { xs: '94vw', sm: 640 },
                    maxWidth: '94vw',
                    height: { xs: '86vh', sm: '78vh' },
                    maxHeight: '86vh',
                    m: 0,
                    p: 0,
                    borderRadius: '12px',
                    overflow: 'hidden',
                    boxShadow: 'lg',
                }}
            >
                <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#ffffff' }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '14px 44px 12px 16px',
                        borderBottom: '1px solid #e5e7eb',
                    }}>
                        <Info size={17} color="#2563eb" />
                        <div style={{ minWidth: 0 }}>
                            <Typography level="title-sm">Prompt Examples</Typography>
                            <Typography level="body-xs" sx={{ color: '#64748b' }}>
                                Click Use to fill the {promptGuideTarget === 'explore' ? 'candidate generator' : 'refine prompt'}.
                            </Typography>
                        </div>
                        <ModalClose />
                    </div>
                    <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: 14, background: '#f8fafc' }}>
                        {PROMPT_GUIDE_EXAMPLES.map((example) => (
                            <div
                                key={example.title}
                                style={{
                                    background: '#fff',
                                    border: '1px solid #e2e8f0',
                                    borderRadius: 8,
                                    padding: 12,
                                    marginBottom: 10,
                                    boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 7 }}>
                                    <Typography level="title-sm" sx={{ fontSize: 13 }}>{example.title}</Typography>
                                    <Button size="sm" variant="soft" onClick={() => applyPromptGuideExample(example.prompt)}>
                                        Use
                                    </Button>
                                </div>
                                <p style={{
                                    margin: 0,
                                    fontSize: 12,
                                    lineHeight: 1.55,
                                    color: '#475569',
                                    whiteSpace: 'pre-wrap',
                                }}>
                                    {example.prompt}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </ModalDialog>
        </Modal>
        <Modal open={isMetadataOpen} onClose={() => setIsMetadataOpen(false)}>
            <ModalDialog
                variant="plain"
                sx={{
                    width: isMetadataExpanded ? '96vw' : '76vw',
                    height: isMetadataExpanded ? '92vh' : '76vh',
                    maxWidth: 'none',
                    p: 0,
                    overflow: 'hidden',
                    borderRadius: '10px',
                    boxShadow: 'lg',
                }}
            >
                <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#fff' }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '12px 44px 12px 14px',
                        borderBottom: '1px solid #e5e7eb',
                    }}>
                        <Code2 size={16} color="#2563eb" />
                        <div style={{ minWidth: 0 }}>
                            <Typography level="title-sm">Generator Metadata JSON</Typography>
                            <Typography level="body-xs" sx={{ color: '#64748b' }}>
                                Current preview state combined with diagrams and all interfaces.
                            </Typography>
                        </div>
                        <button
                            onClick={() => setIsMetadataExpanded((value) => !value)}
                            title={isMetadataExpanded ? 'Shrink modal' : 'Expand modal'}
                            style={{
                                marginLeft: 'auto',
                                width: 28,
                                height: 28,
                                borderRadius: 6,
                                border: '1px solid #d1d5db',
                                background: '#fff',
                                color: '#4b5563',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                            }}
                        >
                            {isMetadataExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                        </button>
                        <ModalClose />
                    </div>
                    <div style={{
                        flex: 1,
                        minHeight: 0,
                        overflow: 'auto',
                        background: '#0f172a',
                        padding: 16,
                    }}>
                        {isLoadingMetadata && (
                            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#cbd5e1', gap: 8 }}>
                                <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                                Building metadata...
                            </div>
                        )}
                        {!isLoadingMetadata && metadataError && (
                            <pre style={{ margin: 0, color: '#fecaca', whiteSpace: 'pre-wrap', fontSize: 12 }}>{metadataError}</pre>
                        )}
                        {!isLoadingMetadata && !metadataError && (
                            <pre style={{
                                margin: 0,
                                color: '#dbeafe',
                                fontSize: 12,
                                lineHeight: 1.55,
                                fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                                whiteSpace: 'pre',
                            }}>{metadataJson}</pre>
                        )}
                    </div>
                </div>
            </ModalDialog>
        </Modal>
        {/* First-time tour banner */}
        {showTourBanner && (
            <div style={{
                position: 'fixed', bottom: 28, left: '50%', transform: 'translateX(-50%)',
                zIndex: 9999,
                display: 'flex', alignItems: 'center', gap: 12,
                background: '#1e293b', color: '#f1f5f9',
                padding: '12px 20px', borderRadius: 12,
                boxShadow: '0 8px 32px rgba(0,0,0,0.22)',
                fontSize: 13, fontWeight: 500,
                animation: 'slideUp 0.35s cubic-bezier(0.16,1,0.3,1)',
            }}>
                <HelpCircle size={16} style={{ color: '#7dd3fc', flexShrink: 0 }} />
                <span>First time here? Take a 30-second tour of the interface editor.</span>
                <button
                    onClick={startTour}
                    style={{
                        padding: '5px 14px', borderRadius: 8, border: 'none',
                        background: '#2563eb', color: '#fff', fontSize: 12,
                        fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap',
                    }}>
                    Start Tour
                </button>
                <button
                    onClick={dismissTourBanner}
                    style={{
                        padding: '5px 12px', borderRadius: 8,
                        border: '1px solid #475569', background: 'transparent',
                        color: '#94a3b8', fontSize: 12, cursor: 'pointer', whiteSpace: 'nowrap',
                    }}>
                    Skip
                </button>
            </div>
        )}
        <style>{`
            @keyframes slideUp {
                from { opacity: 0; transform: translateX(-50%) translateY(16px); }
                to   { opacity: 1; transform: translateX(-50%) translateY(0); }
            }
        `}</style>
        </>
    );
};
