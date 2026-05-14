import { authAxios, useAuthStore } from '$auth/state/auth';
import { Button, Tooltip, Typography } from '@mui/joy';
import Editor from '@monaco-editor/react';
import { AlignJustify, Code2, Database, Eye, GalleryHorizontal, Info, LayoutGrid, Loader2, Maximize2, Minimize2, Monitor, RefreshCw, Table2 } from 'lucide-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { prototypeURL } from '$shared/globals';
import useLocalStorage from './useLocalStorage';

type LayoutOption = 'card' | 'list' | 'table' | 'detail' | 'gallery';
type ColorOption = 'blue' | 'green' | 'purple' | 'orange' | 'rose' | 'slate';
type DensityOption = 'compact' | 'normal' | 'spacious';
type ImagePositionOption = 'left' | 'top' | 'right';
type ImageSizeOption = 'sm' | 'md' | 'lg';
type ColSpanOption = 12 | 6 | 4 | 3;

interface AgentDesignProps {
    interfaceId?: string | null;
    systemId?: string | null;
}

const LAYOUT_OPTIONS: { value: LayoutOption; label: string; icon: React.ReactNode }[] = [
    { value: 'card', label: 'Card', icon: <LayoutGrid size={13} /> },
    { value: 'list', label: 'List', icon: <AlignJustify size={13} /> },
    { value: 'table', label: 'Table', icon: <Table2 size={13} /> },
    { value: 'detail', label: 'Detail', icon: <Code2 size={13} /> },
    { value: 'gallery', label: 'Gallery', icon: <GalleryHorizontal size={13} /> },
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

export const AgentDesign: React.FC<AgentDesignProps> = ({ interfaceId, systemId }) => {
    const [sections, setSections] = useLocalStorage('sections', []);
    const [pages, setPages] = useLocalStorage('pages', []);

    const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
    const [previewHtml, setPreviewHtml] = useState<string>('');
    const [previewPageIndex, setPreviewPageIndex] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [rightView, setRightView] = useState<'preview' | 'code'>('preview');
    const [isSeedingData, setIsSeedingData] = useState(false);
    const [seedStatus, setSeedStatus] = useState<'idle' | 'ok' | 'error'>('idle');
    const [previewMode, setPreviewMode] = useState<'design' | 'live'>('design');
    const [isFullScreen, setIsFullScreen] = useState(false);

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

    const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const hotReloadTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    // Capture latest sections/pages/previewPageIndex for the debounced callback
    const latestState = useRef({ sections, pages, previewPageIndex });
    useEffect(() => { latestState.current = { sections, pages, previewPageIndex }; }, [sections, pages, previewPageIndex]);

    const selectedSection = (sections as any[]).find((s: any) => s.id === selectedSectionId);

    // postMessage -> select section from iframe click
    useEffect(() => {
        const handler = (e: MessageEvent) => {
            if (e.data?.type === 'section-selected') {
                setSelectedSectionId(e.data.id);
            }
        };
        window.addEventListener('message', handler);
        return () => window.removeEventListener('message', handler);
    }, []);

    const doRefreshPreview = useCallback(async () => {
        if (!interfaceId) return;
        const { sections: secs, pages: pgs, previewPageIndex: idx } = latestState.current;
        setIsRefreshing(true);
        try {
            const res = await authAxios.post(`/v1/metadata/interfaces/${interfaceId}/generate/`, {
                prompt: '',
                interface_data_override: { sections: secs, pages: pgs },
                inject_click_handlers: true,
            });
            const htmlFiles = (res.data.files || []).filter((f: any) => f.path.endsWith('.html'));
            const html = htmlFiles[idx]?.content ?? htmlFiles[0]?.content;
            if (html) setPreviewHtml(html);
        } catch {
            // fail silently - preview is best-effort
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

    const doHotReload = useCallback(async () => {
        if (!interfaceId) return;
        const { sections: secs, pages: pgs } = latestState.current;
        try {
            await authAxios.post('/v1/generator/prototypes/hot_reload/', {
                interface_id: interfaceId,
                sections: secs,
                pages: pgs,
            });
            setLiveKey((k: number) => k + 1);
        } catch {
            // fail silently — live prototype may not be running
        }
    }, [interfaceId]);

    // Debounce: refresh 600 ms after any sections/pages/page-index change
    useEffect(() => {
        if (!interfaceId) return;
        if (refreshTimer.current) clearTimeout(refreshTimer.current);
        refreshTimer.current = setTimeout(doRefreshPreview, 600);
        return () => { if (refreshTimer.current) clearTimeout(refreshTimer.current); };
    }, [sections, pages, previewPageIndex, interfaceId, doRefreshPreview]);

    // Debounce: hot-reload live prototype 800 ms after sections/pages change
    useEffect(() => {
        if (!interfaceId || previewMode !== 'live') return;
        if (hotReloadTimer.current) clearTimeout(hotReloadTimer.current);
        hotReloadTimer.current = setTimeout(doHotReload, 800);
        return () => { if (hotReloadTimer.current) clearTimeout(hotReloadTimer.current); };
    }, [sections, pages, interfaceId, previewMode, doHotReload]);

    const updateSection = useCallback((sectionId: string, field: string, value: string | number) => {
        setSections((prev: any[]) => prev.map((s: any) => {
            if (s.id !== sectionId) return s;
            if (field === 'layout') return { ...s, layout: value };
            if (field === 'col_span') return { ...s, col_span: value };
            return { ...s, style: { ...(s.style || {}), [field]: value } };
        }));
    }, [setSections]);

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
    const secImagePosition: ImagePositionOption = (secStyle.image_position as ImagePositionOption) || 'top';
    const secImageSize: ImageSizeOption = (secStyle.image_size as ImageSizeOption) || 'md';
    const isMethodOnly = !(selectedSection?.attributes?.length) && !!(selectedSection?.methods?.length);

    const currentPage = (pages as any[])[previewPageIndex];
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

    return (
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

                {/* Section list */}
                <div style={{ padding: '10px 10px 6px', borderBottom: '1px solid #e5e7eb' }}>
                    <Typography level="title-sm" sx={{ mb: 1, fontSize: 13 }}>Sections</Typography>
                    <div style={{ overflowY: 'auto', maxHeight: 176 }}>
                        {(sections as any[]).length === 0 && (
                            <p style={{ fontSize: 12, color: '#9ca3af', margin: 0 }}>
                                Add sections in the Section Components tab first.
                            </p>
                        )}
                        {(sections as any[]).map((s: any) => (
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
                                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {s.name || 'Unnamed'}
                                </span>
                                <span style={{ fontSize: 11, color: !(s.attributes?.length) && s.methods?.length ? '#9333ea' : '#6b7280', flexShrink: 0, marginLeft: 4 }}>
                                    {!(s.attributes?.length) && s.methods?.length ? 'action' : (s.layout || 'table')}
                                </span>
                            </button>
                        ))}
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
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
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
                        </>
                    ) : (
                        <>
                            <Typography level="title-sm" sx={{ mb: 1.5, fontSize: 13 }}>
                                {selectedSection.name}
                            </Typography>

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Layout</p>
                            {isMethodOnly ? (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                                    <span style={{ ...btnBase, ...active(true), cursor: 'default', pointerEvents: 'none' }}>Action Panel</span>
                                    <span style={{ fontSize: 11, color: '#9ca3af' }}>auto — no attributes</span>
                                </div>
                            ) : (
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
                                    {LAYOUT_OPTIONS.map(opt => (
                                        <button key={opt.value} style={{ ...btnBase, ...active(secLayout === opt.value) }}
                                            onClick={() => updateSection(selectedSection.id, 'layout', opt.value)}>
                                            {opt.icon}{opt.label}
                                        </button>
                                    ))}
                                </div>
                            )}

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Width</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {COL_SPAN_OPTIONS.map(opt => (
                                    <button key={opt.value} style={{ ...btnBase, ...active(secColSpan === opt.value), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'col_span', opt.value)}>
                                        {opt.label}
                                    </button>
                                ))}
                            </div>

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Color</p>
                            <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
                                {COLOR_OPTIONS.map(c => (
                                    <button key={c} title={c}
                                        onClick={() => updateSection(selectedSection.id, 'color', c)}
                                        style={{
                                            width: 22, height: 22, borderRadius: '50%',
                                            background: COLOR_HEX[c], cursor: 'pointer',
                                            border: secColor === c ? `3px solid ${COLOR_HEX[c]}` : '2px solid transparent',
                                            outline: secColor === c ? '2px solid #93c5fd' : 'none',
                                            outlineOffset: 1,
                                        }}
                                    />
                                ))}
                            </div>

                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Density</p>
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {(['compact', 'normal', 'spacious'] as DensityOption[]).map(d => (
                                    <button key={d} style={{ ...btnBase, ...active(secDensity === d), padding: '3px 7px', fontSize: 11 }}
                                        onClick={() => updateSection(selectedSection.id, 'density', d)}>
                                        {d}
                                    </button>
                                ))}
                            </div>

                            {secLayout === 'card' && (
                                <>
                                    <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Columns</p>
                                    <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                        {['1', '2', '3', '4'].map(n => (
                                            <button key={n} style={{ ...btnBase, ...active(secColumns === n), width: 28, justifyContent: 'center' }}
                                                onClick={() => updateSection(selectedSection.id, 'columns', n)}>
                                                {n}
                                            </button>
                                        ))}
                                    </div>
                                </>
                            )}

                            {secLayout === 'detail' && (
                                <>
                                    <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Image Position</p>
                                    <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                        {([
                                            { value: 'left', label: 'Left' },
                                            { value: 'top', label: 'Top' },
                                            { value: 'right', label: 'Right' },
                                        ] as { value: ImagePositionOption; label: string }[]).map(opt => (
                                            <button key={opt.value}
                                                style={{ ...btnBase, ...active(secImagePosition === opt.value), padding: '3px 7px', fontSize: 11 }}
                                                onClick={() => updateSection(selectedSection.id, 'image_position', opt.value)}>
                                                {opt.label}
                                            </button>
                                        ))}
                                    </div>
                                    {secImagePosition !== 'top' && (
                                        <>
                                            <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Image Size</p>
                                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                                {([
                                                    { value: 'sm', label: 'Small' },
                                                    { value: 'md', label: 'Medium' },
                                                    { value: 'lg', label: 'Large' },
                                                ] as { value: ImageSizeOption; label: string }[]).map(opt => (
                                                    <button key={opt.value}
                                                        style={{ ...btnBase, ...active(secImageSize === opt.value), padding: '3px 7px', fontSize: 11 }}
                                                        onClick={() => updateSection(selectedSection.id, 'image_size', opt.value)}>
                                                        {opt.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </>
                                    )}
                                </>
                            )}
                        </>
                    )}
                </div>

                {/* AI generate */}
                <div style={{ borderTop: '1px solid #e5e7eb', padding: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                        <Typography level="title-sm" sx={{ fontSize: 13 }}>AI Generate</Typography>
                        <Tooltip title="Try these commands to change layout or style" variant="soft">
                            <span style={{ fontSize: 11, color: '#2563eb', cursor: 'help', display: 'flex', alignItems: 'center', gap: 2 }}>
                                <Info size={12} /> Prompting Guide
                            </span>
                        </Tooltip>
                    </div>

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
                                padding: '2px 10px', borderRadius: 10, fontSize: 12, cursor: 'pointer',
                                background: previewPageIndex === idx ? '#dbeafe' : '#f3f4f6',
                                color: previewPageIndex === idx ? '#1d4ed8' : '#6b7280',
                                border: 'none',
                            }}>
                            {p.name || `Page ${idx + 1}`}
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
                    </div>
                </div>

                {/* iframe */}
                <div style={{ flex: 1, overflow: 'hidden', background: '#f8fafc' }}>
                    {previewMode === 'live' ? (
                        <iframe
                            key={`live-${liveKey}`}
                            src={`${prototypeURL}/autologin?as=${liveUser}`}
                            title="Live prototype"
                            style={{ width: '100%', height: '100%', border: 'none' }}
                        />
                    ) : previewHtml ? (
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
                                {(sections as any[]).length === 0
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
    );
};
