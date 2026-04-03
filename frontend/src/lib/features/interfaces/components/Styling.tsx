import {
    FormControl,
    Input,
    Option,
    Select,
    Textarea,
} from "@mui/joy";
import { authAxios } from '$auth/state/auth';
import { Plus, Sparkles, CheckCircle } from "lucide-react";
import React, { useEffect, useState } from 'react';
import useLocalStorage from './useLocalStorage';


type Props = {
    interfaceId: string;
}

export const Styling: React.FC<Props> = ({ interfaceId }) => {

    const [data, setData, isSuccess] = useLocalStorage('styling', '');
    const [logoFile, setLogoFile] = useLocalStorage('logoFile', null);
    const [logoDimensions, setLogoDimensions] = useLocalStorage('logoDimensions', { width: 0, height: 0 });

    const [isGeneratingLayout, setIsGeneratingLayout] = useState(false);
    const [layoutGenerated, setLayoutGenerated] = useState(false);
    const [layoutError, setLayoutError] = useState('');
    const [layoutPrompt, setLayoutPrompt] = useState('');

    const [isGeneratingStyle, setIsGeneratingStyle] = useState(false);
    const [styleGenerated, setStyleGenerated] = useState(false);
    const [styleError, setStyleError] = useState('');
    const [stylePrompt, setStylePrompt] = useState('');

    const [isGeneratingOOUI, setIsGeneratingOOUI] = useState(false);
    const [oouiGenerated, setOouiGenerated] = useState(false);
    const [oouiPageCount, setOouiPageCount] = useState(0);
    const [oouiError, setOouiError] = useState('');
    const [oouiPrompt, setOouiPrompt] = useState('');

    useEffect(() => {
        if (!data || Object.keys(data).length === 0) {
            const defaultStyling = {
                radius: 0,
                backgroundColor: '#FFFFFF',
                textColor: '#000000',
                accentColor: '#F5F5F4',
                selectedStyle: 'modern'
            };
            setData(defaultStyling);
        }
    }, [data, setData]);

    const handleRadiusChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(event.target.value, 10);
        if (value >= 0 && value <= 10) {
            const newData = { ...data, radius: value };
            setData(newData);
        }
    }

    const handleBackgroundColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newData = { ...data, backgroundColor: event.target.value };
        setData(newData);
    }

    const handleTextColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newData = { ...data, textColor: event.target.value };
        setData(newData);
    }

    const handleAccentColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newData = { ...data, accentColor: event.target.value };
        setData(newData);
    }

    const handleStyleChange = (event, newValue) => {
        const newData = { ...data, selectedStyle: newValue };
        setData(newData);
    };

    const handleLayoutChange = (event, newValue) => {
        setLayoutGenerated(false);
        setLayoutError('');
        setLayoutPrompt('');
        const newData = { ...data, layoutType: newValue };
        setData(newData);
    };

    const handleFontUrlChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newData = { ...data, fontUrl: event.target.value };
        setData(newData);
    };

    const handleCustomCssChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newData = { ...data, customCss: event.target.value };
        setData(newData);
    };

    const handleGenerateStyle = async () => {
        if (!stylePrompt.trim()) return;
        setIsGeneratingStyle(true);
        setStyleError('');
        setStyleGenerated(false);
        try {
            const response = await authAxios.post(
                `/v1/metadata/interfaces/${interfaceId}/generate_style/`,
                { prompt: stylePrompt }
            );
            const s = response.data;
            setData({
                ...data,
                backgroundColor: s.backgroundColor,
                textColor:       s.textColor,
                accentColor:     s.accentColor,
                radius:          s.radius,
                fontUrl:         s.fontUrl,
                layoutType:      s.layoutType,
                displayMode:     s.displayMode,
                customCss:       s.customCss,
            });
            setStyleGenerated(true);
            setLayoutGenerated(false);
        } catch (err: any) {
            setStyleError(err.response?.data?.detail || 'Failed to generate style. Please try again.');
        } finally {
            setIsGeneratingStyle(false);
        }
    };

    const handleGenerateOOUIPage = async () => {
        if (!oouiPrompt.trim()) return;
        setIsGeneratingOOUI(true);
        setOouiError('');
        setOouiGenerated(false);
        try {
            const response = await authAxios.post(
                `/v1/metadata/interfaces/${interfaceId}/generate_ooui_page/`,
                { prompt: oouiPrompt }
            );
            setData({ ...data, customDjangoTemplates: response.data.templates });
            setOouiPageCount(response.data.count);
            setOouiGenerated(true);
        } catch (err: any) {
            setOouiError(err.response?.data?.detail || 'Failed to generate OOUI page. Please try again.');
        } finally {
            setIsGeneratingOOUI(false);
        }
    };

    const handleResetOOUIPage = () => {
        const { customDjangoTemplates: _, customPageJinja2: __, ...rest } = data;
        setData(rest);
        setOouiGenerated(false);
        setOouiPageCount(0);
        setOouiPrompt('');
    };

    const handleGenerateLayout = async () => {
        if (!layoutPrompt.trim()) return;
        setIsGeneratingLayout(true);
        setLayoutError('');
        setLayoutGenerated(false);
        try {
            const response = await authAxios.post(
                `/v1/metadata/interfaces/${interfaceId}/generate_layout/`,
                {
                    prompt: layoutPrompt,
                    background_color: data.backgroundColor || '#FFFFFF',
                    text_color: data.textColor || '#000000',
                    accent_color: data.accentColor || '#3B82F6',
                    radius: data.radius ?? 8,
                }
            );
            // Backend already saved customHtml; sync to localStorage
            const newData = { ...data, layoutType: 'custom', customHtml: response.data.custom_html };
            setData(newData);
            setLayoutGenerated(true);
        } catch (err: any) {
            setLayoutError(err.response?.data?.detail || 'Failed to generate layout. Please try again.');
        } finally {
            setIsGeneratingLayout(false);
        }
    };

    /*const handleLogoChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                const img = new Image();
                img.onload = function () {
                    const maxWidth = 512;
                    const maxHeight = 512;
                    const width = img.width;
                    const height = img.height;
                    if (width <= maxWidth && height <= maxHeight) {
                        setLogoFile(file);
                        setLogoDimensions({ width, height });
                    } else {
                        alert(`Maximum allowed dimensions: ${maxWidth} x ${maxHeight} px.`);
                    }
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    };*/

    return (
        <>
            {isSuccess && (
                <div className="max-w-[480px] mx-auto mt-4 ml-2 space-y-4">

                    {/* ── DESIGN BRIEF ────────────────────────────────── */}
                    <FormControl>
                        <h3 className="text-xl font-bold flex items-center gap-1.5">
                            <Sparkles size={16} className="text-violet-500" />
                            Design Brief
                        </h3>
                        <p className="text-xs text-gray-500 mb-2">
                            Describe the design you want in plain language — mood, industry, colours, layout, typography. AI will generate <strong>all</strong> style settings at once.
                        </p>
                        <div className="flex flex-wrap gap-1.5 mb-2">
                            {[
                                'Dark fintech dashboard, deep navy + electric blue accent, Inter font, sharp corners',
                                'Warm e-commerce store, cream background, terracotta accent, rounded cards, friendly',
                                'Clean minimal SaaS, white background, indigo accent, subtle shadows, modern tabs layout',
                                'Medical portal, light blue + white, professional sidebar, compact tables, clinical feel',
                                'Bold startup app, black background, neon green accent, monospace font, edgy hacker aesthetic',
                                'Luxury brand portal, ivory + gold accent, elegant serif font, generous whitespace, minimal',
                            ].map((ex) => (
                                <button
                                    key={ex}
                                    type="button"
                                    onClick={() => { setStylePrompt(ex); setStyleGenerated(false); }}
                                    className="text-[10px] px-2 py-1 rounded-full border border-violet-300 text-violet-700 hover:bg-violet-50 text-left leading-snug"
                                >
                                    {ex}
                                </button>
                            ))}
                        </div>
                        <Textarea
                            minRows={3}
                            value={stylePrompt}
                            onChange={(e) => { setStylePrompt(e.target.value); setStyleGenerated(false); }}
                            placeholder="e.g. Dark fintech dashboard with electric blue accent, Inter font, sharp corners…"
                        />
                        <button
                            type="button"
                            onClick={handleGenerateStyle}
                            disabled={isGeneratingStyle || !stylePrompt.trim()}
                            className="mt-2 flex items-center gap-2 px-4 py-2 bg-violet-600 text-white text-sm rounded-md hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Sparkles size={14} />
                            {isGeneratingStyle ? 'Generating…' : 'Generate Design'}
                        </button>
                        {styleGenerated && (
                            <div className="mt-2 flex items-center gap-1.5 text-green-600 text-xs">
                                <CheckCircle size={14} />
                                Design generated! All fields updated below. Click Save to apply.
                            </div>
                        )}
                        {styleError && (
                            <p className="mt-2 text-xs text-red-500">{styleError}</p>
                        )}
                    </FormControl>

                    <hr className="border-gray-200" />

                    {/* ── OOUI FREE-FORM PAGE GENERATOR ──────────────── */}
                    <FormControl>
                        <h3 className="text-xl font-bold flex items-center gap-1.5">
                            <Sparkles size={16} className="text-indigo-500" />
                            OOUI Free Page Template
                        </h3>
                        <p className="text-xs text-gray-500 mb-2">
                            Describe any layout imaginable — kanban board, magazine grid, bento, timeline, gallery, etc.
                            AI generates a <strong>fully unconstrained</strong> page template following OOUI principles
                            (objects first, actions secondary). Overrides the Display Mode setting above.
                        </p>
                        {(data.customDjangoTemplates && Object.keys(data.customDjangoTemplates).length > 0) && (
                            <div className="mb-2 flex items-center gap-2 p-2 bg-indigo-50 border border-indigo-200 rounded-md">
                                <CheckCircle size={14} className="text-indigo-600 shrink-0" />
                                <span className="text-xs text-indigo-700 flex-1">Custom OOUI templates active ({Object.keys(data.customDjangoTemplates).length} page{Object.keys(data.customDjangoTemplates).length !== 1 ? 's' : ''}) — standard Display Mode is bypassed.</span>
                                <button
                                    type="button"
                                    onClick={handleResetOOUIPage}
                                    className="text-[10px] text-red-500 hover:text-red-700 underline shrink-0"
                                >
                                    Reset
                                </button>
                            </div>
                        )}
                        <div className="flex flex-wrap gap-1.5 mb-2">
                            {[
                                'Kanban board: one column per object type, each card shows object name and key fields, drag-free scrollable',
                                'Bento grid: mixed-size tiles, hero tile for most important object, smaller tiles for secondary data',
                                'Magazine grid: large hero card per object, subtitle below, soft shadows, editorial feel',
                                'Timeline: records sorted by date field down a vertical line with connector dots, clean and modern',
                                'Data dashboard: KPI stat cards at top, table list below, accent metric highlights',
                                'Gallery: image-placeholder cards in masonry layout, hover overlay shows actions',
                            ].map((ex) => (
                                <button
                                    key={ex}
                                    type="button"
                                    onClick={() => { setOouiPrompt(ex); setOouiGenerated(false); }}
                                    className="text-[10px] px-2 py-1 rounded-full border border-indigo-300 text-indigo-700 hover:bg-indigo-50 text-left leading-snug"
                                >
                                    {ex}
                                </button>
                            ))}
                        </div>
                        <Textarea
                            minRows={3}
                            value={oouiPrompt}
                            onChange={(e) => { setOouiPrompt(e.target.value); setOouiGenerated(false); }}
                            placeholder="e.g. Kanban board with one column per object type, cards show key fields, accent header…"
                        />
                        <button
                            type="button"
                            onClick={handleGenerateOOUIPage}
                            disabled={isGeneratingOOUI || !oouiPrompt.trim()}
                            className="mt-2 flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Sparkles size={14} />
                            {isGeneratingOOUI ? 'Generating…' : 'Generate OOUI Page'}
                        </button>
                        {oouiGenerated && (
                            <div className="mt-2 flex items-center gap-1.5 text-green-600 text-xs">
                                <CheckCircle size={14} />
                                {oouiPageCount} page template{oouiPageCount !== 1 ? 's' : ''} generated! Click Save to apply.
                            </div>
                        )}
                        {oouiError && (
                            <p className="mt-2 text-xs text-red-500">{oouiError}</p>
                        )}
                    </FormControl>

                    <hr className="border-gray-200" />

                    <FormControl>
                        <h3 className="text-xl font-bold">Logo</h3>
                        <input
                            type="file"
                            accept="image/*"
                            //onChange={handleLogoChange}
                            className="hidden"
                            id="logoInput"
                        />
                        <label htmlFor="logoInput" className="cursor-pointer">
                            <Plus />
                            {logoFile ? `${logoFile.name} (${logoDimensions.width}x${logoDimensions.height}px)` : ''}
                        </label>
                    </FormControl>

                    <FormControl required>
                        <h3 className="text-xl font-bold">Style</h3>
                        <Select
                            placeholder="Choose one…"
                            value={data.selectedStyle}
                            onChange={handleStyleChange}
                        >
                            <Option value="basic">Basic</Option>
                            <Option value="modern">Modern</Option>
                            <Option value="abstract">Abstract</Option>
                        </Select>
                    </FormControl>

                    <FormControl required>
                        <h3 className="text-xl font-bold">Display Mode</h3>
                        <p className="text-xs text-gray-500 mb-1">How data records are shown on list pages.</p>
                        <Select
                            placeholder="Choose display mode…"
                            value={data.displayMode || 'table'}
                            onChange={(_, v) => setData({ ...data, displayMode: v })}
                        >
                            <Option value="table">Table — rows and columns</Option>
                            <Option value="cards">Cards — visual card grid per record</Option>
                            <Option value="list">List — compact rows with avatar</Option>
                        </Select>
                    </FormControl>

                    <FormControl required>
                        <h3 className="text-xl font-bold">Layout</h3>
                        <Select
                            placeholder="Choose layout…"
                            value={data.layoutType || 'sidebar'}
                            onChange={handleLayoutChange}
                        >
                            <Option value="sidebar">Sidebar — classic left nav</Option>
                            <Option value="topnav">Top Nav — horizontal menu bar</Option>
                            <Option value="dashboard">Dashboard — icon rail + dark panel</Option>
                            <Option value="split">Split — master / detail panes</Option>
                            <Option value="wizard">Wizard — step-by-step flow</Option>
                            <Option value="minimal">Minimal — clean centered content</Option>
                            <Option value="cards">Cards — responsive card grid</Option>
                            <Option value="tabs">Tabs — tabbed navigation</Option>
                            <Option value="drawer">Drawer — hamburger side panel</Option>
                            <Option value="custom">✨ Custom — AI free-style layout</Option>
                        </Select>
                    </FormControl>

                    {data.layoutType === 'custom' && (
                        <FormControl>
                            <h3 className="text-xl font-bold">Describe Your Layout</h3>
                            <p className="text-xs text-gray-500 mb-2">
                                Describe what you want in plain language — colours, structure, mood, inspiration. The AI will generate the full layout.
                            </p>
                            <div className="flex flex-wrap gap-1.5 mb-2">
                                {[
                                    'Dark sidebar with glowing accent nav links, top search bar, card grid main area',
                                    'Clean white top nav with pill-shaped active tab, wide content below, minimal and modern',
                                    'Full-height split: left list panel, right detail pane with sticky action bar',
                                    'Glassmorphism header, blurred background, floating content cards with soft shadows',
                                    'Retro terminal style: black background, green monospace font, table-heavy layout',
                                    'Corporate blue header, breadcrumb trail, tabbed sections, compact data tables',
                                ].map((example) => (
                                    <button
                                        key={example}
                                        type="button"
                                        onClick={() => { setLayoutPrompt(example); setLayoutGenerated(false); }}
                                        className="text-[10px] px-2 py-1 rounded-full border border-violet-300 text-violet-700 hover:bg-violet-50 text-left leading-snug"
                                    >
                                        {example}
                                    </button>
                                ))}
                            </div>
                            <Textarea
                                minRows={4}
                                value={layoutPrompt}
                                onChange={(e) => { setLayoutPrompt(e.target.value); setLayoutGenerated(false); }}
                                placeholder="Describe the layout you want…"
                            />
                            <button
                                type="button"
                                onClick={handleGenerateLayout}
                                disabled={isGeneratingLayout || !layoutPrompt.trim()}
                                className="mt-2 flex items-center gap-2 px-4 py-2 bg-violet-600 text-white text-sm rounded-md hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Sparkles size={14} />
                                {isGeneratingLayout ? 'Generating…' : 'Generate Layout'}
                            </button>
                            {layoutGenerated && (
                                <div className="mt-2 flex items-center gap-1.5 text-green-600 text-xs">
                                    <CheckCircle size={14} />
                                    Layout generated! Click Save to apply it.
                                </div>
                            )}
                            {layoutError && (
                                <p className="mt-2 text-xs text-red-500">{layoutError}</p>
                            )}
                        </FormControl>
                    )}

                    <FormControl>
                        <h3 className="text-xl font-bold">Google Font URL</h3>
                        <Input
                            type="text"
                            value={data.fontUrl || ''}
                            onChange={handleFontUrlChange}
                            placeholder="https://fonts.googleapis.com/css2?family=…"
                        />
                    </FormControl>

                    <FormControl>
                        <h3 className="text-xl font-bold">Custom CSS</h3>
                        <Textarea
                            minRows={4}
                            value={data.customCss || ''}
                            onChange={handleCustomCssChange}
                            placeholder=".my-class { color: red; }"
                        />
                    </FormControl>

                    <FormControl>
                        <h3 className="text-xl font-bold">Background color</h3>
                        <div className="flex w-full flex-row justify-between pb-1">
                            <Input
                                type="text"
                                value={data.backgroundColor}
                                onChange={handleBackgroundColorChange}
                                //pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
                                placeholder="#FFFFFF"
                            />
                            <input
                                type="color"
                                value={data.backgroundColor}
                                onChange={handleBackgroundColorChange}
                                className="w-[50px] h-[50px] border border-gray-500 p-0 cursor-pointer"
                                style={{ backgroundColor: data.backgroundColor }}
                            />
                        </div>
                    </FormControl>

                    <FormControl>
                        <h3 className="text-xl font-bold">Text color</h3>
                        <div className="flex w-full flex-row justify-between pb-1">
                            <Input
                                type="text"
                                value={data.textColor}
                                onChange={handleTextColorChange}
                                //pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
                                placeholder="#000000"
                            />
                            <input
                                type="color"
                                value={data.textColor}
                                onChange={handleTextColorChange}
                                className="w-[50px] h-[50px] border border-gray-500 p-0 cursor-pointer"
                                style={{ backgroundColor: data.textColor }}
                            />
                        </div>
                    </FormControl>

                    <FormControl>
                        <h3 className="text-xl font-bold">Accent color</h3>
                        <div className="flex w-full flex-row justify-between pb-1">
                            <Input
                                type="text"
                                value={data.accentColor}
                                onChange={handleAccentColorChange}
                                placeholder="#777777"
                            />
                            <input
                                type="color"
                                value={data.accentColor}
                                onChange={handleAccentColorChange}
                                className="w-[50px] h-[50px] border border-gray-500 p-0 cursor-pointer"
                                style={{ backgroundColor: data.accentColor }}
                            />
                        </div>
                    </FormControl>

                    <FormControl required>
                        <h3 className="text-xl font-bold">Radius</h3>
                        <Input
                            type="number"
                            value={data.radius}
                            onChange={handleRadiusChange}
                            required
                        />
                    </FormControl>
                </div>
            )}
        </>
    )
}

export default Styling
