import { authAxios } from '$auth/state/auth';
import { Button, Typography } from '@mui/joy';
import Editor from '@monaco-editor/react';
import { AlignJustify, Code2, Eye, LayoutGrid, Loader2, RefreshCw, Table2 } from 'lucide-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import useLocalStorage from './useLocalStorage';

type LayoutOption = 'card' | 'list' | 'table';
type ColorOption = 'blue' | 'green' | 'purple' | 'orange' | 'rose' | 'slate';
type DensityOption = 'compact' | 'normal' | 'spacious';

interface AgentDesignProps {
    interfaceId?: string | null;
}

const LAYOUT_OPTIONS: { value: LayoutOption; label: string; icon: React.ReactNode }[] = [
    { value: 'card', label: 'Card', icon: <LayoutGrid size={13} /> },
    { value: 'list', label: 'List', icon: <AlignJustify size={13} /> },
    { value: 'table', label: 'Table', icon: <Table2 size={13} /> },
];

const COLOR_OPTIONS: ColorOption[] = ['blue', 'green', 'purple', 'orange', 'rose', 'slate'];
const COLOR_HEX: Record<ColorOption, string> = {
    blue: '#3b82f6', green: '#22c55e', purple: '#a855f7',
    orange: '#f97316', rose: '#f43f5e', slate: '#64748b',
};

export const AgentDesign: React.FC<AgentDesignProps> = ({ interfaceId }) => {
    const [sections, setSections] = useLocalStorage('sections', []);
    const [pages, setPages] = useLocalStorage('pages', []);

    const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
    const [previewHtml, setPreviewHtml] = useState<string>('');
    const [previewPageIndex, setPreviewPageIndex] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [rightView, setRightView] = useState<'preview' | 'code'>('preview');

    const [currentPrompt, setCurrentPrompt] = useState('');
    const [isLoadingAgent, setIsLoadingAgent] = useState(false);
    const [agentStatus, setAgentStatus] = useState('');

    const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
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

    // Debounce: refresh 600 ms after any sections/pages/page-index change
    useEffect(() => {
        if (!interfaceId) return;
        if (refreshTimer.current) clearTimeout(refreshTimer.current);
        refreshTimer.current = setTimeout(doRefreshPreview, 600);
        return () => { if (refreshTimer.current) clearTimeout(refreshTimer.current); };
    }, [sections, pages, previewPageIndex, interfaceId, doRefreshPreview]);

    const updateSection = useCallback((sectionId: string, field: string, value: string) => {
        setSections((prev: any[]) => prev.map((s: any) => {
            if (s.id !== sectionId) return s;
            if (field === 'layout') return { ...s, layout: value };
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
        setAgentStatus('');
        try {
            const res = await authAxios.post(`/v1/metadata/interfaces/${interfaceId}/generate/`, {
                prompt,
                model: 'gemini-1.5-pro',
            });
            const htmlFiles = (res.data.files || []).filter((f: any) => f.path.endsWith('.html'));
            if (htmlFiles[0]?.content) setPreviewHtml(htmlFiles[0].content);
            setAgentStatus(res.data.message || 'Done.');
        } catch (e: any) {
            setAgentStatus(`Error: ${e.message}`);
        } finally {
            setIsLoadingAgent(false);
        }
    };

    const secLayout: LayoutOption = (selectedSection?.layout as LayoutOption) || 'table';
    const secStyle = selectedSection?.style || {};
    const secColor: ColorOption = (secStyle.color as ColorOption) || 'blue';
    const secDensity: DensityOption = (secStyle.density as DensityOption) || 'normal';
    const secColumns = String(secStyle.columns ?? '3');

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
        <div style={{ display: 'flex', height: '72vh', border: '1px solid #e5e7eb', borderRadius: 8, overflow: 'hidden' }}>

            {/* -- LEFT PANEL -- */}
            <div style={{ width: 272, flexShrink: 0, borderRight: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', background: '#f9fafb', overflow: 'hidden' }}>

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
                                <span style={{ fontSize: 11, color: '#6b7280', flexShrink: 0, marginLeft: 4 }}>
                                    {s.layout || 'table'}
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
                            <div style={{ display: 'flex', gap: 4, marginBottom: 10 }}>
                                {LAYOUT_OPTIONS.map(opt => (
                                    <button key={opt.value} style={{ ...btnBase, ...active(secLayout === opt.value) }}
                                        onClick={() => updateSection(selectedSection.id, 'layout', opt.value)}>
                                        {opt.icon}{opt.label}
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
                        </>
                    )}
                </div>

                {/* AI generate */}
                <div style={{ borderTop: '1px solid #e5e7eb', padding: 10 }}>
                    <Typography level="title-sm" sx={{ mb: 1, fontSize: 13 }}>AI Generate</Typography>
                    {agentStatus && (
                        <p style={{ fontSize: 11, color: '#6b7280', margin: '0 0 6px' }}>{agentStatus}</p>
                    )}
                    <div style={{ display: 'flex', gap: 6 }}>
                        <input
                            type="text"
                            placeholder="Describe a design change..."
                            value={currentPrompt}
                            onChange={e => setCurrentPrompt(e.target.value)}
                            onKeyDown={e => { if (e.key === 'Enter') handleSendMessage(); }}
                            disabled={isLoadingAgent}
                            style={{ flex: 1, padding: '5px 8px', borderRadius: 6, fontSize: 12, border: '1px solid #d1d5db', outline: 'none' }}
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
                    <span style={{ fontSize: 12, color: '#9ca3af', marginRight: 4 }}>Preview</span>
                    {(pages as any[]).map((p: any, idx: number) => (
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
                        {isRefreshing && <Loader2 size={14} style={{ color: '#9ca3af', animation: 'spin 1s linear infinite' }} />}
                        <button onClick={doRefreshPreview}
                            style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 6, border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer', fontSize: 12 }}>
                            <RefreshCw size={12} />Refresh
                        </button>
                    </div>
                </div>

                {/* iframe */}
                <div style={{ flex: 1, overflow: 'hidden', background: '#f8fafc' }}>
                    {previewHtml ? (
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
