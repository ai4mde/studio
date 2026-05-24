import { authAxios, useAuthStore } from '$auth/state/auth';
import { Button, Modal, ModalClose, ModalDialog, Tooltip, Typography } from '@mui/joy';
import Editor from '@monaco-editor/react';
import { AlignJustify, Code2, Database, Eye, GalleryHorizontal, Info, LayoutGrid, Loader2, Maximize2, Minimize2, Monitor, Plus, RefreshCw, Table2 } from 'lucide-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { prototypeURL } from '$shared/globals';
import useLocalStorage from './useLocalStorage';

type LayoutOption = 'card' | 'list' | 'table' | 'detail' | 'gallery' | 'filter' | 'form'
    | 'activity_action'
    | 'promo-bar' | 'logo' | 'search-bar' | 'icon-actions' | 'nav-links' | 'main-header' | 'minimal-header'
    | 'service-bar' | 'link-grid' | 'brand-strip'
    | 'site-nav' | 'site-footer';
type ColorOption = 'blue' | 'green' | 'purple' | 'orange' | 'rose' | 'slate';
type DensityOption = 'compact' | 'normal' | 'spacious';
type DisplayModeOption = 'grid' | 'carousel' | 'banner';
type CardStyleOption = 'default' | 'product' | 'category' | 'compact';
type ListStyleOption = 'default' | 'product' | 'cart-item';
type FormStyleOption = 'default' | 'auth' | 'step' | 'summary';
type ImagePositionOption = 'left' | 'top' | 'right';
type ImageSizeOption = 'sm' | 'md' | 'lg';
type ColSpanOption = 12 | 6 | 4 | 3;
type PositionOption = 'header' | 'hero' | 'main' | 'sidebar' | 'footer';
type ShadowOption = 'none' | 'sm' | 'md' | 'lg' | 'xl';
type BorderOption = 'none' | 'light' | 'colored' | 'strong';
type BgOption = 'white' | 'light' | 'gray' | 'dark';
type HeaderStyleOption = 'default' | 'large' | 'small' | 'colored' | 'hidden';

const CHROME_LAYOUTS: LayoutOption[] = [
    'promo-bar', 'logo', 'search-bar', 'icon-actions', 'nav-links', 'main-header', 'minimal-header',
    'service-bar', 'link-grid', 'brand-strip', 'site-nav', 'site-footer',
];
const HEADER_LAYOUTS: LayoutOption[] = ['promo-bar', 'logo', 'search-bar', 'icon-actions', 'nav-links', 'main-header', 'minimal-header', 'site-nav'];
const FOOTER_LAYOUTS: LayoutOption[] = ['service-bar', 'link-grid', 'brand-strip', 'site-footer'];

const LAYOUT_CONTROLS: Partial<Record<LayoutOption, readonly string[]>> = {
    table:   ['color', 'density', 'shadow', 'border', 'bg', 'header_style'],
    card:    ['display_mode', 'card_style', 'columns', 'color', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label', 'seller_label', 'availability_label', 'delivery_label'],
    list:    ['list_style', 'color', 'density', 'shadow', 'border', 'bg', 'header_style', 'cta_label', 'availability_label', 'delivery_label'],
    detail:  ['image_position', 'image_size', 'color', 'density', 'shadow', 'border', 'bg', 'header_style'],
    gallery: ['columns', 'color', 'density', 'shadow', 'border', 'bg', 'header_style'],
    filter:  ['color', 'density', 'bg'],
    form:    ['form_style', 'color', 'density', 'login_label', 'step_icon', 'total_label', 'cta_label', 'success_page'],
    activity_action: ['activity_label', 'activity_workflow_action', 'activity_target_page', 'activity_variant', 'activity_align', 'activity_size'],
};

const METHODS_HINTS: Partial<Record<LayoutOption, string>> = {
    'promo-bar':      'Each line = promo strip item (e.g. "Gratis verzending vanaf €25,-"). Text field = right-side CTA label.',
    'logo':           'Text field = brand name shown in the logo.',
    'search-bar':     'Text field = search input placeholder.',
    'icon-actions':   'Each line = action label (e.g. "Inloggen", "♡", "Cart icon").',
    'nav-links':      'Line 1 = categories label. Lines 2–4 = extra nav links. Lines 5+ = top-right links.',
    'main-header':    'Text field = search placeholder.',
    'minimal-header': 'Text field = cart amount in header button (e.g. "0,00").',
    'service-bar':    'Each line = a service bar link in the footer.',
    'link-grid':      'Line 1 = column title. Lines 2+ = footer links in that column.',
    'brand-strip':    'Each line = a brand name shown in the brand strip.',
    'site-nav':       'Lines 1–3: promo strip items. Line 4: right-side highlight text.',
    'site-footer':    'Each line becomes a service-bar link in the footer.',
};

const POSITION_OPTIONS: { value: PositionOption; label: string; bg: string; color: string; border: string }[] = [
    { value: 'header',  label: 'Header',  bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' },
    { value: 'hero',    label: 'Hero',    bg: '#faf5ff', color: '#7e22ce', border: '#e9d5ff' },
    { value: 'main',    label: 'Main',    bg: '#f0fdf4', color: '#15803d', border: '#bbf7d0' },
    { value: 'sidebar', label: 'Sidebar', bg: '#fff7ed', color: '#c2410c', border: '#fed7aa' },
    { value: 'footer',  label: 'Footer',  bg: '#f8fafc', color: '#475569', border: '#e2e8f0' },
];

interface AgentDesignProps {
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
    ]},
    { label: 'Footer', options: [
        { value: 'service-bar', label: 'Service Bar', icon: <Monitor size={13} /> },
        { value: 'link-grid',   label: 'Link Grid',   icon: <Monitor size={13} /> },
        { value: 'brand-strip', label: 'Brand Strip', icon: <Monitor size={13} /> },
        { value: 'site-nav',    label: 'Site Nav',    icon: <Monitor size={13} /> },
        { value: 'site-footer', label: 'Site Footer', icon: <Monitor size={13} /> },
    ]},
];

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

const getPageTypeValue = (page: any) => typeof page?.type === 'string' ? page.type : page?.type?.value;
const isActivityActionSection = (section: any) => section?.type === 'activity_action' || section?.layout === 'activity_action';
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
    return {
        id: `${position}-${layout}-${Date.now()}`,
        name: label,
        label,
        layout,
        class: '',
        operations: { create: false, update: false, delete: false },
        attributes: [],
        methods: layout === 'logo' || layout === 'search-bar' || layout === 'minimal-header'
            ? []
            : [{ name: layout === 'link-grid' ? 'Customer service' : 'Contact' }],
        text: layout === 'logo'
            ? 'Brand'
            : layout === 'search-bar'
                ? 'Search products'
                : layout === 'minimal-header'
                    ? '0,00'
                    : '',
        col_span: 12,
        position,
        style: {},
    };
};

export const AgentDesign: React.FC<AgentDesignProps> = ({ interfaceId, systemId }) => {
    const [sections, setSections] = useLocalStorage('sections', []);
    const [pages, setPages] = useLocalStorage('pages', []);
    const [styling, setStyling] = useLocalStorage('styling', {});

    const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
    const [previewHtml, setPreviewHtml] = useState<string>('');
    const [previewError, setPreviewError] = useState('');
    const [previewPageIndex, setPreviewPageIndex] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [rightView, setRightView] = useState<'preview' | 'code'>('preview');
    const [isSeedingData, setIsSeedingData] = useState(false);
    const [seedStatus, setSeedStatus] = useState<'idle' | 'ok' | 'error'>('idle');
    const [isSyncingLive, setIsSyncingLive] = useState(false);
    const [syncStatus, setSyncStatus] = useState<'idle' | 'ok' | 'error'>('idle');
    const [previewMode, setPreviewMode] = useState<'design' | 'live'>('design');
    const [isFullScreen, setIsFullScreen] = useState(false);
    const [isMetadataOpen, setIsMetadataOpen] = useState(false);
    const [isMetadataExpanded, setIsMetadataExpanded] = useState(false);
    const [isLoadingMetadata, setIsLoadingMetadata] = useState(false);
    const [metadataJson, setMetadataJson] = useState('');
    const [metadataError, setMetadataError] = useState('');

    // Explore / Refine mode
    const [designMode, setDesignMode] = useState<'explore' | 'refine'>('refine');
    const [candidates, setCandidates] = useState<any[]>([]);
    const [explorePrompt, setExplorePrompt] = useState('');
    const [isGeneratingCandidates, setIsGeneratingCandidates] = useState(false);
    const [candidateStatus, setCandidateStatus] = useState('');
    const [previewCandidateIdx, setPreviewCandidateIdx] = useState<number | null>(null);

    const containerRef = useRef<HTMLDivElement>(null);

    const toggleBrowserFullScreen = () => {
        if (!containerRef.current) return;
        if (!document.fullscreenElement) {
            containerRef.current.requestFullscreen().catch(err => {
                console.error(`Error attempting to enable full-screen mode: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    };
    const [liveKey, setLiveKey] = useState(0);
    const [liveUser, setLiveUser] = useState('jan_devries');

    const [currentPrompt, setCurrentPrompt] = useState('');
    const [isLoadingAgent, setIsLoadingAgent] = useState(false);
    const [agentStatus, setAgentStatus] = useState('');
    const [isAIExpanded, setIsAIExpanded] = useState(true);

    const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const hotReloadTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    // Capture latest sections/pages/previewPageIndex/styling for the debounced callback
    const latestState = useRef({ sections, pages, previewPageIndex, styling });
    useEffect(() => { latestState.current = { sections, pages, previewPageIndex, styling }; }, [sections, pages, previewPageIndex, styling]);

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

    const selectedSection = (sections as any[]).find((s: any) => s.id === selectedSectionId);

    // postMessage -> select section from iframe click / drag-reorder
    useEffect(() => {
        const handler = (e: MessageEvent) => {
            if (e.data?.type === 'section-selected') {
                setSelectedSectionId(e.data.id);
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
            } else if (e.data?.type === 'section-resize') {
                const { id, col_span } = e.data;
                setSections((prev: any[]) => prev.map((s: any) =>
                    s.id === id ? { ...s, col_span } : s
                ));
            } else if (e.data?.type === 'section-height') {
                const { id, min_height } = e.data;
                setSections((prev: any[]) => prev.map((s: any) =>
                    s.id === id ? { ...s, min_height } : s
                ));
            }
        };
        window.addEventListener('message', handler);
        return () => window.removeEventListener('message', handler);
    }, [setSections, setPages]);

    const doRefreshPreview = useCallback(async () => {
        if (!interfaceId) return;
        const { sections: secs, pages: pgs, previewPageIndex: idx, styling: stl } = latestState.current;
        setIsRefreshing(true);
        setPreviewError('');
        try {
            const res = await authAxios.post(`/v1/metadata/interfaces/${interfaceId}/generate/`, {
                prompt: '',
                interface_data_override: { sections: secs, pages: pgs, ...(stl && Object.keys(stl).length ? { styling: stl } : {}) },
                inject_click_handlers: true,
            });
            const htmlFiles = (res.data.files || []).filter((f: any) => f.path.endsWith('.html'));
            const html = htmlFiles[idx]?.content ?? htmlFiles[0]?.content;
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

    const handleSeedData = useCallback(async () => {
        setIsSeedingData(true);
        setSeedStatus('idle');
        try {
            const params = systemId ? `?system_id=${systemId}` : '';
            await authAxios.post(`/v1/generator/prototypes/seed/${params}`);
            setSeedStatus('ok');
            setLiveUser('jan_devries');
            setLiveKey((k: number) => k + 1);
            checkAndSwitchLive();
        } catch {
            setSeedStatus('error');
        } finally {
            setIsSeedingData(false);
            setTimeout(() => setSeedStatus('idle'), 3000);
        }
    }, [systemId, checkAndSwitchLive]);

    const buildGeneratorPrototypePayload = useCallback(async (overrideSections?: any[], overridePages?: any[], overrideStyling?: any) => {
        if (!interfaceId || !systemId) throw new Error('Missing interface or system id.');

            const [{ data: iface }, { data: diagrams }, { data: allInterfaces }] = await Promise.all([
                authAxios.get(`/v1/metadata/interfaces/${interfaceId}/`),
                authAxios.get(`/v1/diagram/system/${systemId}/`),
                authAxios.get(`/v1/metadata/interfaces/`, { params: { system: systemId } }),
            ]);
            const { sections: secs, pages: pgs, styling: stl } = latestState.current;
            const effectiveSections = overrideSections ?? secs;
            const effectivePages = overridePages ?? pgs;
            const effectiveStyling = overrideStyling ?? stl;
            const syncedInterface = {
                ...iface,
                data: {
                    ...((iface as any).data || {}),
                    sections: effectiveSections,
                    pages: effectivePages,
                    ...(effectiveStyling && Object.keys(effectiveStyling).length ? { styling: effectiveStyling } : {}),
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
                system_id: systemId,
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
            let overrideStyling: any | undefined;
            if (designMode === 'explore' && previewCandidateIdx !== null && candidates[previewCandidateIdx]) {
                const cand = candidates[previewCandidateIdx];
                overrideSections = cand.sections;
                overridePages = cand.pages;
                overrideStyling = cand.styling;
            }
            const payload = await buildGeneratorPrototypePayload(overrideSections, overridePages, overrideStyling);
            setMetadataJson(JSON.stringify(payload, null, 2));
        } catch (error: any) {
            setMetadataError(error?.response?.data?.detail || error?.message || 'Failed to build generator metadata.');
        } finally {
            setIsLoadingMetadata(false);
        }
    }, [buildGeneratorPrototypePayload, designMode, previewCandidateIdx, candidates]);

    const handleSyncLivePrototype = useCallback(async () => {
        if (!interfaceId || !systemId || isSyncingLive) return;
        setIsSyncingLive(true);
        setSyncStatus('idle');
        try {
            // In explore mode, use the selected candidate's layout data directly
            // so the live prototype matches what the preview shows.
            let overrideSections: any[] | undefined;
            let overridePages: any[] | undefined;
            let overrideStyling: any | undefined;
            if (designMode === 'explore' && previewCandidateIdx !== null && candidates[previewCandidateIdx]) {
                const cand = candidates[previewCandidateIdx];
                overrideSections = cand.sections;
                overridePages = cand.pages;
                overrideStyling = cand.styling;
            }
            const payload = await buildGeneratorPrototypePayload(overrideSections, overridePages, overrideStyling);
            const databasePrototypeName = payload.query.database_prototype_name || '';
            const previousPrototypeId = payload.previous_prototype_id || '';
            const { data: prototype } = await authAxios.post(`v1/generator/prototypes/?database_prototype_name=${encodeURIComponent(databasePrototypeName)}`, payload.body);
            await authAxios.post(`/v1/generator/prototypes/run/${prototype.id}`);
            if (previousPrototypeId && previousPrototypeId !== prototype.id) {
                try {
                    await authAxios.delete(`/v1/generator/prototypes/${previousPrototypeId}/`);
                } catch {
                    // The new live prototype is already running; deletion failure should not break sync.
                }
            }
            if (!databasePrototypeName) {
                const params = systemId ? `?system_id=${systemId}` : '';
                await authAxios.post(`/v1/generator/prototypes/seed/${params}`);
            }
            setPreviewMode('live');
            setLiveUser('jan_devries');
            setLiveKey((k: number) => k + 1);
            setSyncStatus('ok');
        } catch (error) {
            setSyncStatus('error');
        } finally {
            setIsSyncingLive(false);
            setTimeout(() => setSyncStatus('idle'), 3000);
        }
    }, [interfaceId, systemId, isSyncingLive, buildGeneratorPrototypePayload, designMode, previewCandidateIdx, candidates]);

    const doHotReload = useCallback(async () => {
        if (!interfaceId) return;
        const { sections: secs, pages: pgs, styling: stl } = latestState.current;
        try {
            await authAxios.post('/v1/generator/prototypes/hot_reload/', {
                interface_id: interfaceId,
                sections: secs,
                pages: pgs,
                ...(stl && Object.keys(stl).length ? { styling: stl } : {}),
            });
            setLiveKey((k: number) => k + 1);
        } catch {
            // fail silently — live prototype may not be running
        }
    }, [interfaceId]);

    // Debounce: refresh 600 ms after any sections/pages/page-index/styling change
    useEffect(() => {
        if (!interfaceId) return;
        if (refreshTimer.current) clearTimeout(refreshTimer.current);
        refreshTimer.current = setTimeout(doRefreshPreview, 600);
        return () => { if (refreshTimer.current) clearTimeout(refreshTimer.current); };
    }, [sections, pages, previewPageIndex, styling, interfaceId, doRefreshPreview]);

    // Debounce: hot-reload live prototype 800 ms after sections/pages/styling change
    useEffect(() => {
        if (!interfaceId || previewMode !== 'live') return;
        if (hotReloadTimer.current) clearTimeout(hotReloadTimer.current);
        hotReloadTimer.current = setTimeout(doHotReload, 800);
        return () => { if (hotReloadTimer.current) clearTimeout(hotReloadTimer.current); };
    }, [sections, pages, styling, interfaceId, previewMode, doHotReload]);

const updateSection = useCallback((sectionId: string, field: string, value: string | number) => {
        setSections((prev: any[]) => prev.map((s: any) => {
            if (s.id !== sectionId) return s;
            if (field === 'layout') {
                const nextLayout = value as LayoutOption;
                const nextPosition = HEADER_LAYOUTS.includes(nextLayout)
                    ? 'header'
                    : FOOTER_LAYOUTS.includes(nextLayout)
                        ? 'footer'
                        : s.position;
                return { ...s, layout: value, position: nextPosition };
            }
            if (field === 'col_span') return { ...s, col_span: value };
            if (field === 'text') return { ...s, text: value };
            if (field === 'label') return { ...s, label: value, name: value || s.name };
            if (field === 'workflow_action') return { ...s, workflow: { ...(s.workflow || {}), action: value } };
            if (field === 'workflow_target_page') return { ...s, workflow: { ...(s.workflow || {}), target_page: value } };
            return { ...s, style: { ...(s.style || {}), [field]: value } };
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
            const found = ((res.data as any)?.data || {}).candidates || [];
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
        setPreviewCandidateIdx(null);
        let lastStatus = '';
        try {
            const bearerToken = useAuthStore.getState().bearerToken;
            const authHeader = bearerToken ? `Bearer ${bearerToken}` : '';
            const base = (authAxios.defaults.baseURL || '').replace(/\/+$/, '');
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
                        if (c.status === 'done') {
                            setCandidateStatus('Done! Loading candidates...');
                            await loadCandidates();
                            setIsGeneratingCandidates(false);
                            return;
                        }
                    } catch { /* ignore */ }
                }
            }
            // 只有 agent 明確回傳 "done" 才顯示成功；否則保留最後收到的狀態（可能是錯誤訊息）
            if (lastStatus === 'done') setCandidateStatus('Done! Loading candidates...');
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
            setDesignMode('refine');
            setPreviewCandidateIdx(null);
        } catch { /* ignore */ }
    }, [interfaceId, applyVariantDSL, setStyling]);

    const updatePageProperty = useCallback((pageIndex: number, field: string, value: any) => {
        setPages((prev: any[]) => {
            const next = [...prev];
            if (next[pageIndex]) {
                next[pageIndex] = { ...next[pageIndex], [field]: value };
            }
            return next;
        });
    }, [setPages]);

    const handleSendMessage = async () => {
        if (!currentPrompt.trim() || isLoadingAgent || !interfaceId) return;
        const prompt = currentPrompt;
        setCurrentPrompt('');
        setIsLoadingAgent(true);
        setAgentStatus('Initiating... (启动中...)');

        try {
            const bearerToken = useAuthStore.getState().bearerToken;
            const authHeader = bearerToken ? `Bearer ${bearerToken}` : '';
            const base = (authAxios.defaults.baseURL || '').replace(/\/+$/, '');
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
                            if (htmlFiles[0]?.content) setPreviewHtml(htmlFiles[0].content);
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

    const secLayout: LayoutOption = (selectedSection?.layout as LayoutOption) || 'table';
    const secColSpan: ColSpanOption = (selectedSection?.col_span as ColSpanOption) ?? 12;
    const secStyle = selectedSection?.style || {};
    const secColor: ColorOption = (secStyle.color as ColorOption) || 'blue';
    const secDensity: DensityOption = (secStyle.density as DensityOption) || 'normal';
    const secColumns = String(secStyle.columns ?? '3');
    const secDisplayMode: DisplayModeOption = (secStyle.display_mode as DisplayModeOption) || 'grid';
    const secCardStyle: CardStyleOption = (secStyle.card_style as CardStyleOption) || 'default';
    const secListStyle: ListStyleOption = (secStyle.list_style as ListStyleOption) || 'default';
    const secFormStyle: FormStyleOption = (secStyle.form_style as FormStyleOption) || 'default';
    const secImagePosition: ImagePositionOption = (secStyle.image_position as ImagePositionOption) || 'top';
    const secImageSize: ImageSizeOption = (secStyle.image_size as ImageSizeOption) || 'md';
    const secShadow: ShadowOption = (secStyle.shadow as ShadowOption) || 'none';
    const secBorder: BorderOption = (secStyle.border as BorderOption) || 'none';
    const secBg: BgOption = (secStyle.bg as BgOption) || 'white';
    const secHeaderStyle: HeaderStyleOption = (secStyle.header_style as HeaderStyleOption) || 'default';
    const isActivityAction = selectedSection?.type === 'activity_action' || selectedSection?.layout === 'activity_action';
    const isMethodOnly = !isActivityAction && !(selectedSection?.attributes?.length) && !!(selectedSection?.methods?.length);

    const layoutControls: readonly string[] = CHROME_LAYOUTS.includes(secLayout)
        ? ['text', 'methods']
        : (LAYOUT_CONTROLS[secLayout] ?? []);
    const hasControl = (c: string) => layoutControls.includes(c);

    const currentPage = (pages as any[])[previewPageIndex];
    const isActivityPage = (page: any) => getPageTypeValue(page) === 'activity';
    const pageLayout = currentPage?.layout?.value || 'vertical';
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
    const updateStyling = (key: string, value: string) =>
        setStyling((prev: Record<string, string>) => ({ ...prev, [key]: value }));

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
            <div style={{
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
                <div style={{ padding: '8px 10px', borderBottom: '1px solid #e5e7eb', display: 'flex', gap: 0, background: '#fff' }}>
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
                        <div style={{ padding: '10px 10px 8px', borderBottom: '1px solid #e5e7eb' }}>
                            <Typography level="title-sm" sx={{ fontSize: 13, mb: 0.5 }}>Generate 3 Candidates</Typography>
                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 8px' }}>Describe the actor's goals — the agent creates 3 distinct interface designs.</p>
                            <textarea
                                rows={3}
                                placeholder="e.g. Customer browsing products, adding to cart and checking out"
                                value={explorePrompt}
                                onChange={e => setExplorePrompt(e.target.value)}
                                disabled={isGeneratingCandidates}
                                style={{ width: '100%', padding: '6px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', resize: 'none', boxSizing: 'border-box', marginBottom: 8 }}
                            />
                            {candidateStatus && (
                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 6px', background: '#f9fafb', padding: '4px 8px', borderRadius: 4, wordBreak: 'break-word' }}>
                                    {isGeneratingCandidates && <Loader2 size={10} style={{ display: 'inline', marginRight: 4, animation: 'spin 1s linear infinite' }} />}
                                    {candidateStatus}
                                </p>
                            )}
                            <Button
                                size="sm" fullWidth
                                onClick={handleGenerateCandidates}
                                loading={isGeneratingCandidates}
                                disabled={!explorePrompt.trim() || isGeneratingCandidates || !interfaceId || !systemId}
                            >
                                Generate Candidates
                            </Button>
                        </div>

                        {/* Candidate cards */}
                        <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
                            {candidates.length === 0 && !isGeneratingCandidates && (
                                <p style={{ fontSize: 12, color: '#9ca3af', textAlign: 'center', marginTop: 24 }}>
                                    No candidates yet. Enter a prompt and generate.
                                </p>
                            )}
                            {candidates.map((candidate: any, idx: number) => {
                                const isExpanded = previewCandidateIdx === idx;
                                return (
                                    <div key={idx} style={{
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
                                                    onClick={() => setPreviewCandidateIdx(isExpanded ? null : idx)}
                                                    style={{
                                                        flex: 1, padding: '4px 0', borderRadius: 5, fontSize: 11, cursor: 'pointer',
                                                        background: isExpanded ? '#2563eb' : '#f3f4f6',
                                                        color: isExpanded ? '#fff' : '#374151',
                                                        border: `1px solid ${isExpanded ? '#2563eb' : '#d1d5db'}`,
                                                    }}>
                                                    {isExpanded ? 'Hide' : 'Preview'}
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
                <div style={{ padding: '10px 10px 6px', borderBottom: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6, marginBottom: 8 }}>
                        <Typography level="title-sm" sx={{ fontSize: 13 }}>Sections</Typography>
                        <div style={{ display: 'flex', gap: 4 }}>
                            <button
                                title="Add editable header component"
                                onClick={() => {
                                    const section = makeChromeSection('logo', 'header');
                                    setSections((prev: any[]) => [...prev, section]);
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
                                onClick={() => setSelectedSectionId(s.id === selectedSectionId ? null : s.id)}
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
                                    <span style={{ fontSize: 11, color: !(s.attributes?.length) && s.methods?.length ? '#9333ea' : '#6b7280' }}>
                                        {!(s.attributes?.length) && s.methods?.length ? 'action' : (s.layout || 'table')}
                                    </span>
                                </span>
                            </button>
                            );
                        })}
                    </div>
                </div>

                {/* Properties panel */}
                <div style={{ flex: 1, overflowY: 'auto', padding: 10 }}>
                    {!selectedSection ? (
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
                                        onClick={() => updatePageProperty(previewPageIndex, 'layout', opt)}>
                                        {opt.label}
                                    </button>
                                ))}
                            </div>

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
                                <p style={{ fontSize: 12, fontWeight: 600, color: '#374151', margin: '0 0 8px' }}>Global Theme</p>

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
                                    <label title="Custom" style={{ position: 'relative', width: 20, height: 20, borderRadius: '50%', overflow: 'hidden', cursor: 'pointer', border: '1.5px solid #d1d5db', flexShrink: 0 }}>
                                        <input type="color" value={stl.textColor || '#111827'} onChange={e => updateStyling('textColor', e.target.value)}
                                            style={{ position: 'absolute', opacity: 0, inset: 0, cursor: 'pointer', width: '100%', height: '100%' }} />
                                    </label>
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
                            </div>
                        </>
                    ) : (
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

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Layout</p>
                            {isActivityAction ? (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                                    <span style={{ ...btnBase, ...active(true), cursor: 'default', pointerEvents: 'none' }}>Activity Button</span>
                                    <span style={{ fontSize: 11, color: '#9ca3af' }}>workflow step action</span>
                                </div>
                            ) : isMethodOnly ? (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                                    <span style={{ ...btnBase, ...active(true), cursor: 'default', pointerEvents: 'none' }}>Action Panel</span>
                                    <span style={{ fontSize: 11, color: '#9ca3af' }}>auto — no attributes</span>
                                </div>
                            ) : (
                                <div style={{ marginBottom: 10 }}>
                                    {LAYOUT_GROUPS.map(group => (
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

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Width</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {COL_SPAN_OPTIONS.map(opt => (
                                    <button key={opt.value} style={{ ...btnBase, ...active(secColSpan === opt.value), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'col_span', opt.value)}>
                                        {opt.label}
                                    </button>
                                ))}
                            </div>

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
                                {([{v:'default',l:'Default'},{v:'product',l:'Product'},{v:'cart-item',l:'Cart Item'}] as {v:ListStyleOption;l:string}[]).map(o => (
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
                                    <button key={v} style={{ ...btnBase, ...active(((selectedSection.workflow || {}).action || 'complete') === v), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'workflow_action', v)}>{v}</button>
                                ))}
                            </div></>)}

                            {hasControl('activity_target_page') && (
                            <><p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Target Page</p>
                            <select
                                value={(selectedSection.workflow || {}).target_page ?? ''}
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
                                    <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 2px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Methods (one per line)</p>
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
                    <div
                        style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', cursor: 'pointer', userSelect: 'none' }}
                        onClick={() => setIsAIExpanded(v => !v)}
                    >
                        <Typography level="title-sm" sx={{ fontSize: 13 }}>AI Generate</Typography>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <Tooltip title="Try these commands to change layout or style" variant="soft">
                                <span
                                    style={{ fontSize: 11, color: '#2563eb', cursor: 'help', display: 'flex', alignItems: 'center', gap: 2 }}
                                    onClick={e => e.stopPropagation()}
                                >
                                    <Info size={12} /> Prompting Guide
                                </span>
                            </Tooltip>
                            <span style={{ fontSize: 10, color: '#9ca3af' }}>{isAIExpanded ? '▲' : '▼'}</span>
                        </div>
                    </div>

                    {isAIExpanded && (
                        <div style={{ padding: '0 12px 12px' }}>
                            {/* Example Prompt Chips */}
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
                                {[
                                    'Dark mode with emerald accents',
                                    'Convert to multi-step Wizard',
                                    'Modern style with large border radius',
                                    'Split layout: Details left, List right',
                                    'Compact density and flat card style',
                                ].map(suggestion => (
                                    <button
                                        key={suggestion}
                                        onClick={() => setCurrentPrompt(suggestion)}
                                        style={{
                                            fontSize: 10, padding: '2px 8px', borderRadius: 12,
                                            background: '#eff6ff', color: '#1d4ed8', border: '1px solid #dbeafe',
                                            cursor: 'pointer', whiteSpace: 'nowrap'
                                        }}
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>

                            {agentStatus && (
                                <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 6px', background: '#f9fafb', padding: '4px 8px', borderRadius: 4 }}>
                                    {agentStatus}
                                </p>
                            )}
                            <div style={{ display: 'flex', gap: 6 }}>
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
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

                {/* Toolbar */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderBottom: '1px solid #e5e7eb', background: '#fff', flexWrap: 'wrap' }}>
                    {/* Design / Live toggle */}
                    <div style={{ display: 'flex', borderRadius: 6, overflow: 'hidden', border: '1px solid #d1d5db', marginRight: 4 }}>
                        {(['design', 'live'] as const).map(mode => (
                            <button key={mode} onClick={() => mode === 'live' ? checkAndSwitchLive() : setPreviewMode(mode)}
                                style={{
                                    padding: '2px 10px', fontSize: 12, cursor: 'pointer', border: 'none',
                                    background: previewMode === mode ? '#1d4ed8' : '#fff',
                                    color: previewMode === mode ? '#fff' : '#6b7280',
                                }}>
                                {mode === 'design' ? 'Design' : 'Live'}
                            </button>
                        ))}
                    </div>
                    {previewMode === 'design' && (pages as any[]).map((p: any, idx: number) => (
                        <button key={idx} onClick={() => setPreviewPageIndex(idx)}
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
                        <button onClick={handleSeedData} disabled={isSeedingData}
                            style={{
                                display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 6, fontSize: 12, cursor: isSeedingData ? 'default' : 'pointer',
                                border: `1px solid ${seedStatus === 'ok' ? '#86efac' : seedStatus === 'error' ? '#fca5a5' : '#d1d5db'}`,
                                background: seedStatus === 'ok' ? '#f0fdf4' : seedStatus === 'error' ? '#fef2f2' : '#fff',
                                color: seedStatus === 'ok' ? '#16a34a' : seedStatus === 'error' ? '#dc2626' : '#374151',
                                opacity: isSeedingData ? 0.6 : 1,
                            }}>
                            {isSeedingData ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Database size={12} />}
                            {seedStatus === 'ok' ? 'Seeded!' : seedStatus === 'error' ? 'Failed' : 'Seed Data'}
                        </button>
                        <button onClick={handleSyncLivePrototype} disabled={isSyncingLive || !interfaceId || !systemId}
                            title="Regenerate a live prototype from the current preview"
                            style={{
                                display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 6, fontSize: 12,
                                cursor: isSyncingLive ? 'default' : 'pointer',
                                border: `1px solid ${syncStatus === 'ok' ? '#86efac' : syncStatus === 'error' ? '#fca5a5' : '#bfdbfe'}`,
                                background: syncStatus === 'ok' ? '#f0fdf4' : syncStatus === 'error' ? '#fef2f2' : '#eff6ff',
                                color: syncStatus === 'ok' ? '#16a34a' : syncStatus === 'error' ? '#dc2626' : '#1d4ed8',
                                opacity: isSyncingLive ? 0.6 : 1,
                            }}>
                            {isSyncingLive ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <RefreshCw size={12} />}
                            {syncStatus === 'ok' ? 'Synced!' : syncStatus === 'error' ? 'Sync Failed' : 'Sync Live'}
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
                    </div>
                </div>

                {/* iframe */}
                <div style={{ flex: 1, overflow: 'hidden', background: '#f8fafc' }}>
                    {designMode === 'explore' && previewCandidateIdx !== null && candidates[previewCandidateIdx]?.preview_html ? (
                        <iframe
                            key={`candidate-${previewCandidateIdx}`}
                            srcDoc={candidates[previewCandidateIdx].preview_html}
                            title={`Candidate ${previewCandidateIdx + 1} preview`}
                            style={{ width: '100%', height: '100%', border: 'none' }}
                            sandbox="allow-scripts allow-same-origin"
                        />
                    ) : designMode === 'explore' ? (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', flexDirection: 'column', gap: 12 }}>
                            <p style={{ fontSize: 13, color: '#9ca3af' }}>
                                {isGeneratingCandidates ? 'Generating candidates...' : candidates.length === 0 ? 'Generate candidates to see previews here.' : 'Select a candidate to preview.'}
                            </p>
                            {isGeneratingCandidates && <Loader2 size={20} style={{ color: '#9ca3af', animation: 'spin 1s linear infinite' }} />}
                        </div>
                    ) : previewMode === 'live' ? (
                        <iframe
                            key={`live-${liveKey}`}
                            src={`${prototypeURL}/autologin?as=${liveUser}`}
                            title="Live prototype"
                            style={{ width: '100%', height: '100%', border: 'none' }}
                        />
                    ) : previewHtml && !previewError ? (
                        <iframe
                            key={`${interfaceId}-${previewPageIndex}`}
                            srcDoc={previewHtml}
                            title="Page preview"
                            style={{ width: '100%', height: '100%', border: 'none' }}
                            sandbox="allow-scripts allow-same-origin"
                        />
                    ) : (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                            <p style={{ fontSize: 13, color: '#9ca3af' }}>
                                {previewError
                                    ? previewError
                                    : (sections as any[]).length === 0
                                    ? 'Add sections and pages to see a preview.'
                                    : (pages as any[]).length === 0
                                        ? 'Add pages in the Pages tab to see a preview.'
                                        : 'Loading preview...'}
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
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
                        {isLoadingMetadata ? (
                            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#cbd5e1', gap: 8 }}>
                                <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                                Building metadata...
                            </div>
                        ) : metadataError ? (
                            <pre style={{ margin: 0, color: '#fecaca', whiteSpace: 'pre-wrap', fontSize: 12 }}>{metadataError}</pre>
                        ) : (
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
        </>
    );
};
