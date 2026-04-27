import {
    FormControl,
    Input,
    Option,
    Select,
} from "@mui/joy";
import { ChevronDown, ChevronRight, Plus } from "lucide-react";
import React, { useEffect, useState } from 'react';
import useLocalStorage from './useLocalStorage';

// ─── Tailwind color data ────────────────────────────────────────────────────

const SHADES = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900'] as const;

const COLOR_FAMILIES = [
    'slate', 'gray', 'zinc', 'red', 'orange', 'yellow',
    'green', 'teal', 'blue', 'indigo', 'violet', 'purple', 'pink',
] as const;

const COLOR_HEX: Record<string, Record<string, string>> = {
    slate:  { '50':'#f8fafc','100':'#f1f5f9','200':'#e2e8f0','300':'#cbd5e1','400':'#94a3b8','500':'#64748b','600':'#475569','700':'#334155','800':'#1e293b','900':'#0f172a' },
    gray:   { '50':'#f9fafb','100':'#f3f4f6','200':'#e5e7eb','300':'#d1d5db','400':'#9ca3af','500':'#6b7280','600':'#4b5563','700':'#374151','800':'#1f2937','900':'#111827' },
    zinc:   { '50':'#fafafa','100':'#f4f4f5','200':'#e4e4e7','300':'#d4d4d8','400':'#a1a1aa','500':'#71717a','600':'#52525b','700':'#3f3f46','800':'#27272a','900':'#18181b' },
    red:    { '50':'#fef2f2','100':'#fee2e2','200':'#fecaca','300':'#fca5a5','400':'#f87171','500':'#ef4444','600':'#dc2626','700':'#b91c1c','800':'#991b1b','900':'#7f1d1d' },
    orange: { '50':'#fff7ed','100':'#ffedd5','200':'#fed7aa','300':'#fdba74','400':'#fb923c','500':'#f97316','600':'#ea580c','700':'#c2410c','800':'#9a3412','900':'#7c2d12' },
    yellow: { '50':'#fefce8','100':'#fef9c3','200':'#fef08a','300':'#fde047','400':'#facc15','500':'#eab308','600':'#ca8a04','700':'#a16207','800':'#854d0e','900':'#713f12' },
    green:  { '50':'#f0fdf4','100':'#dcfce7','200':'#bbf7d0','300':'#86efac','400':'#4ade80','500':'#22c55e','600':'#16a34a','700':'#15803d','800':'#166534','900':'#14532d' },
    teal:   { '50':'#f0fdfa','100':'#ccfbf1','200':'#99f6e4','300':'#5eead4','400':'#2dd4bf','500':'#14b8a6','600':'#0d9488','700':'#0f766e','800':'#115e59','900':'#134e4a' },
    blue:   { '50':'#eff6ff','100':'#dbeafe','200':'#bfdbfe','300':'#93c5fd','400':'#60a5fa','500':'#3b82f6','600':'#2563eb','700':'#1d4ed8','800':'#1e40af','900':'#1e3a8a' },
    indigo: { '50':'#eef2ff','100':'#e0e7ff','200':'#c7d2fe','300':'#a5b4fc','400':'#818cf8','500':'#6366f1','600':'#4f46e5','700':'#4338ca','800':'#3730a3','900':'#312e81' },
    violet: { '50':'#f5f3ff','100':'#ede9fe','200':'#ddd6fe','300':'#c4b5fd','400':'#a78bfa','500':'#8b5cf6','600':'#7c3aed','700':'#6d28d9','800':'#5b21b6','900':'#4c1d95' },
    purple: { '50':'#faf5ff','100':'#f3e8ff','200':'#e9d5ff','300':'#d8b4fe','400':'#c084fc','500':'#a855f7','600':'#9333ea','700':'#7e22ce','800':'#6b21a8','900':'#581c87' },
    pink:   { '50':'#fdf2f8','100':'#fce7f3','200':'#fbcfe8','300':'#f9a8d4','400':'#f472b6','500':'#ec4899','600':'#db2777','700':'#be185d','800':'#9d174d','900':'#831843' },
};

function getHex(tw: string): string {
    if (tw === 'white') return '#ffffff';
    if (tw === 'black') return '#000000';
    if (tw === 'transparent') return 'transparent';
    const [fam, shade] = tw.split('-');
    return COLOR_HEX[fam]?.[shade] ?? '#cccccc';
}

// ─── Tailwind class parser / builder ────────────────────────────────────────

const _CP = `(?:white|black|transparent|(?:${COLOR_FAMILIES.join('|')})-(?:${SHADES.join('|')}))`;

// Pre-compiled per-prefix regexes so extractColor/replaceColor don't rebuild on every call
const _COLOR_RE: Record<'bg-' | 'text-' | 'border-', [RegExp, RegExp]> = {
    'bg-':     [new RegExp(`\\bbg-(${_CP})\\b`),     new RegExp(`\\bbg-(${_CP})`, 'g')],
    'text-':   [new RegExp(`\\btext-(${_CP})\\b`),   new RegExp(`\\btext-(${_CP})`, 'g')],
    'border-': [new RegExp(`\\bborder-(${_CP})\\b`), new RegExp(`\\bborder-(${_CP})`, 'g')],
};

function extractColor(classes: string, prefix: 'bg-' | 'text-' | 'border-'): string | null {
    const m = classes.match(_COLOR_RE[prefix][0]);
    return m ? m[1] : null;
}

function replaceColor(classes: string, prefix: 'bg-' | 'text-' | 'border-', color: string | null): string {
    const cleaned = classes.replace(_COLOR_RE[prefix][1], '').replace(/\s+/g, ' ').trim();
    return color ? `${cleaned} ${prefix}${color}`.trim() : cleaned;
}

function extractRounded(classes: string): string {
    if (/\brounded-none\b/.test(classes)) return 'none';
    const m = classes.match(/\brounded(-(?:sm|md|lg|xl|2xl|3xl|full))?\b/);
    if (!m) return 'none';
    return m[1] ? m[1].slice(1) : 'default';
}

function replaceRounded(classes: string, val: string): string {
    const cleaned = classes.replace(/\brounded(?:-(?:none|sm|md|lg|xl|2xl|3xl|full))?\b/g, '').replace(/\s+/g, ' ').trim();
    if (val === 'none') return `${cleaned} rounded-none`.trim();
    if (val === 'default') return `${cleaned} rounded`.trim();
    return `${cleaned} rounded-${val}`.trim();
}

function extractShadow(classes: string): string {
    if (/\bshadow-none\b/.test(classes)) return 'none';
    const m = classes.match(/\bshadow(-(?:sm|md|lg|xl|2xl|inner))?\b/);
    if (!m) return 'none';
    return m[1] ? m[1].slice(1) : 'default';
}

function replaceShadow(classes: string, val: string): string {
    const cleaned = classes.replace(/\bshadow(?:-(?:none|sm|md|lg|xl|2xl|inner))?\b/g, '').replace(/\s+/g, ' ').trim();
    if (val === 'none') return `${cleaned} shadow-none`.trim();
    if (val === 'default') return `${cleaned} shadow`.trim();
    return `${cleaned} shadow-${val}`.trim();
}

function extractFont(classes: string): string {
    const m = classes.match(/\bfont-(sans|serif|mono)\b/);
    return m ? m[1] : '';
}

function replaceFont(classes: string, val: string): string {
    const cleaned = classes.replace(/\bfont-(?:sans|serif|mono)\b/g, '').replace(/\s+/g, ' ').trim();
    return val ? `${cleaned} font-${val}`.trim() : cleaned;
}

function extractPadding(classes: string): string {
    const m = classes.match(/\bp-(\d+)\b/);
    return m ? m[1] : '';
}

function replacePadding(classes: string, val: string): string {
    const cleaned = classes.replace(/\bp-\d+\b/g, '').replace(/\s+/g, ' ').trim();
    return val ? `${cleaned} p-${val}`.trim() : cleaned;
}

// ─── Human-readable token labels ────────────────────────────────────────────

const TOKEN_LABELS: Record<string, string> = {
    'page.body': 'Page Background',
    'page.main': 'Main Container',
    'page.surface': 'Content Surface',
    'component.button.primary': 'Primary Button',
    'component.button.secondary': 'Secondary Button',
    'component.card': 'Card',
    'component.table': 'Table',
    'element.input.editable': 'Input Field',
    'element.input.readonly': 'Read-only Field',
    'element.label': 'Label Text',
    'element.heading': 'Heading',
    'element.th': 'Table Header',
    'element.td': 'Table Cell',
    'region.form': 'Form Area',
    'region.header': 'Header',
    'region.nav': 'Navigation',
    'region.sidebar': 'Sidebar',
    'region.dashboard': 'Dashboard',
    'region.wizard': 'Wizard',
    'region.wizard.step': 'Wizard Step',
    'region.modal': 'Modal',
};

const TOKEN_GROUPS: { label: string; prefix: string }[] = [
    { label: 'Page', prefix: 'page.' },
    { label: 'Components', prefix: 'component.' },
    { label: 'Elements', prefix: 'element.' },
    { label: 'Regions', prefix: 'region.' },
];

// ─── Color picker sub-component ─────────────────────────────────────────────

type ColorPickerProps = {
    value: string | null;    // e.g. 'blue-600', 'white', null
    onChange: (color: string | null) => void;
};

const ColorPicker: React.FC<ColorPickerProps> = ({ value, onChange }) => {
    const currentFamily = value ? value.split('-')[0] : '';
    const currentShade = value?.includes('-') ? value.split('-')[1] : '';
    const specialColors = [
        { tw: 'white', hex: '#ffffff', label: 'White' },
        { tw: 'black', hex: '#000000', label: 'Black' },
    ];

    return (
        <div className="space-y-2">
            {/* Current color swatch + label */}
            <div className="flex items-center gap-2">
                <div
                    className="w-8 h-8 rounded border border-gray-300 flex-shrink-0"
                    style={{ backgroundColor: value ? getHex(value) : '#e5e7eb' }}
                />
                <span className="text-sm text-gray-600">{value || 'None'}</span>
                {value && (
                    <button
                        type="button"
                        className="text-xs text-gray-400 hover:text-gray-600 ml-auto"
                        onClick={() => onChange(null)}
                    >
                        Clear
                    </button>
                )}
            </div>

            {/* Special colors */}
            <div className="flex gap-1">
                {specialColors.map(({ tw, hex, label }) => (
                    <button
                        key={tw}
                        type="button"
                        title={label}
                        className={`w-7 h-7 rounded border-2 transition-all ${value === tw ? 'border-blue-500 scale-110' : 'border-gray-300 hover:border-gray-400'}`}
                        style={{ backgroundColor: hex }}
                        onClick={() => onChange(tw)}
                    />
                ))}
            </div>

            {/* Color family row */}
            <div className="flex flex-wrap gap-1">
                {COLOR_FAMILIES.map(fam => (
                    <button
                        key={fam}
                        type="button"
                        title={fam}
                        className={`w-6 h-6 rounded-full border-2 transition-all ${currentFamily === fam ? 'border-blue-500 scale-110' : 'border-transparent hover:border-gray-300'}`}
                        style={{ backgroundColor: COLOR_HEX[fam]['500'] }}
                        onClick={() => {
                            const shade = currentShade && SHADES.includes(currentShade as any) ? currentShade : '500';
                            onChange(`${fam}-${shade}`);
                        }}
                    />
                ))}
            </div>

            {/* Shade row (only when a color family is selected) */}
            {currentFamily && COLOR_HEX[currentFamily] && (
                <div className="flex gap-1">
                    {SHADES.map(shade => (
                        <button
                            key={shade}
                            type="button"
                            title={shade}
                            className={`w-6 h-6 rounded border-2 transition-all ${currentShade === shade ? 'border-blue-500 scale-110 ring-1 ring-blue-400' : 'border-transparent hover:border-gray-300'}`}
                            style={{ backgroundColor: COLOR_HEX[currentFamily][shade] }}
                            onClick={() => onChange(`${currentFamily}-${shade}`)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

// ─── Single token editor ─────────────────────────────────────────────────────

type TokenEditorProps = {
    tokenKey: string;
    value: string;
    onChange: (key: string, newValue: string) => void;
};

const TokenEditor: React.FC<TokenEditorProps> = ({ tokenKey, value, onChange }) => {
    const [showRaw, setShowRaw] = useState(false);

    const bgColor = extractColor(value, 'bg-');
    const textColor = extractColor(value, 'text-');
    const borderColor = extractColor(value, 'border-');
    const rounded = extractRounded(value);
    const shadow = extractShadow(value);
    const font = extractFont(value);
    const padding = extractPadding(value);

    const hasBg = bgColor !== null || /\bbg-/.test(value);
    const hasText = textColor !== null || /\btext-(?:white|black|gray|slate|blue|red|green|yellow|purple|pink|indigo|violet|teal|orange|zinc)/.test(value);
    const hasBorder = borderColor !== null || /\bborder\b/.test(value);
    const hasRounded = /\brounded/.test(value);
    const hasShadow = /\bshadow/.test(value);
    const hasFont = /\bfont-(?:sans|serif|mono)\b/.test(value);
    const hasPadding = /\bp-\d/.test(value);

    const label = TOKEN_LABELS[tokenKey] || tokenKey;

    return (
        <div className="border border-gray-100 rounded-lg p-3 bg-white space-y-3">
            <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-700">{label}</span>
                <button
                    type="button"
                    className="text-xs text-gray-400 hover:text-gray-600"
                    onClick={() => setShowRaw(v => !v)}
                >
                    {showRaw ? 'Visual' : 'Raw CSS'}
                </button>
            </div>

            {showRaw ? (
                <input
                    type="text"
                    value={value}
                    onChange={e => onChange(tokenKey, e.target.value)}
                    className="w-full text-xs font-mono border border-gray-300 rounded px-2 py-1 focus:outline-none focus:border-blue-400"
                    placeholder="Tailwind classes…"
                />
            ) : (
                <div className="space-y-3">
                    {/* Background color */}
                    {hasBg && (
                        <div>
                            <p className="text-xs font-medium text-gray-500 mb-1">Background</p>
                            <ColorPicker
                                value={bgColor}
                                onChange={c => onChange(tokenKey, replaceColor(value, 'bg-', c))}
                            />
                        </div>
                    )}

                    {/* Text color */}
                    {hasText && (
                        <div>
                            <p className="text-xs font-medium text-gray-500 mb-1">Text Color</p>
                            <ColorPicker
                                value={textColor}
                                onChange={c => onChange(tokenKey, replaceColor(value, 'text-', c))}
                            />
                        </div>
                    )}

                    {/* Border color */}
                    {hasBorder && (
                        <div>
                            <p className="text-xs font-medium text-gray-500 mb-1">Border Color</p>
                            <ColorPicker
                                value={borderColor}
                                onChange={c => onChange(tokenKey, replaceColor(value, 'border-', c))}
                            />
                        </div>
                    )}

                    {/* Corner radius */}
                    {hasRounded && (
                        <div>
                            <p className="text-xs font-medium text-gray-500 mb-1">Corner Radius</p>
                            <div className="flex flex-wrap gap-1">
                                {[
                                    { val: 'none', label: 'None' },
                                    { val: 'sm', label: 'SM' },
                                    { val: 'default', label: 'MD' },
                                    { val: 'lg', label: 'LG' },
                                    { val: 'xl', label: 'XL' },
                                    { val: '2xl', label: '2XL' },
                                    { val: 'full', label: 'Full' },
                                ].map(({ val, label: lbl }) => (
                                    <button
                                        key={val}
                                        type="button"
                                        className={`px-2 py-1 text-xs rounded border transition-all ${rounded === val ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-300 hover:border-blue-300'}`}
                                        onClick={() => onChange(tokenKey, replaceRounded(value, val))}
                                    >
                                        {lbl}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Shadow */}
                    {hasShadow && (
                        <div>
                            <p className="text-xs font-medium text-gray-500 mb-1">Shadow</p>
                            <div className="flex flex-wrap gap-1">
                                {[
                                    { val: 'none', label: 'None' },
                                    { val: 'sm', label: 'SM' },
                                    { val: 'default', label: 'MD' },
                                    { val: 'lg', label: 'LG' },
                                    { val: 'xl', label: 'XL' },
                                ].map(({ val, label: lbl }) => (
                                    <button
                                        key={val}
                                        type="button"
                                        className={`px-2 py-1 text-xs rounded border transition-all ${shadow === val ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-300 hover:border-blue-300'}`}
                                        onClick={() => onChange(tokenKey, replaceShadow(value, val))}
                                    >
                                        {lbl}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Font family */}
                    {hasFont && (
                        <div>
                            <p className="text-xs font-medium text-gray-500 mb-1">Font</p>
                            <div className="flex gap-1">
                                {[
                                    { val: 'sans', label: 'Sans' },
                                    { val: 'serif', label: 'Serif' },
                                    { val: 'mono', label: 'Mono' },
                                ].map(({ val, label: lbl }) => (
                                    <button
                                        key={val}
                                        type="button"
                                        className={`px-3 py-1 text-xs rounded border transition-all ${font === val ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-300 hover:border-blue-300'}`}
                                        onClick={() => onChange(tokenKey, replaceFont(value, val))}
                                    >
                                        {lbl}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Padding */}
                    {hasPadding && (
                        <div>
                            <p className="text-xs font-medium text-gray-500 mb-1">Padding</p>
                            <div className="flex flex-wrap gap-1">
                                {[
                                    { val: '1', label: 'XS' },
                                    { val: '2', label: 'SM' },
                                    { val: '3', label: 'MD' },
                                    { val: '4', label: 'LG' },
                                    { val: '6', label: 'XL' },
                                    { val: '8', label: '2XL' },
                                    { val: '10', label: '3XL' },
                                ].map(({ val, label: lbl }) => (
                                    <button
                                        key={val}
                                        type="button"
                                        className={`px-2 py-1 text-xs rounded border transition-all ${padding === val ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-300 hover:border-blue-300'}`}
                                        onClick={() => onChange(tokenKey, replacePadding(value, val))}
                                    >
                                        {lbl}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* If no properties detected, show raw input */}
                    {!hasBg && !hasText && !hasBorder && !hasRounded && !hasShadow && !hasFont && !hasPadding && (
                        <input
                            type="text"
                            value={value}
                            onChange={e => onChange(tokenKey, e.target.value)}
                            className="w-full text-xs font-mono border border-gray-300 rounded px-2 py-1 focus:outline-none focus:border-blue-400"
                            placeholder="Tailwind classes…"
                        />
                    )}
                </div>
            )}
        </div>
    );
};

// ─── Types ───────────────────────────────────────────────────────────────────

type Theme = {
    name?: string;
    description?: string;
    tokens?: Record<string, string>;
};

type Props = {
    theme: Theme | null;
    onThemeChange: (t: Theme) => void;
};

// ─── Main Styling component ──────────────────────────────────────────────────

export const Styling: React.FC<Props> = ({ theme, onThemeChange }) => {

    const [data, setData, isSuccess] = useLocalStorage('styling', '');
    const [logoFile] = useLocalStorage('logoFile', null);
    const [logoDimensions] = useLocalStorage('logoDimensions', { width: 0, height: 0 });
    const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
        Page: true,
        Components: false,
        Elements: false,
        Regions: false,
    });

    useEffect(() => {
        if (!data || Object.keys(data).length === 0) {
            setData({
                radius: 0,
                backgroundColor: '#FFFFFF',
                textColor: '#000000',
                accentColor: '#F5F5F4',
                selectedStyle: 'modern',
                selectedLayout: 'sidebar_left',
            });
        }
    }, [data, setData]);

    const handleTokenChange = (key: string, newValue: string) => {
        onThemeChange({ ...theme, tokens: { ...(theme?.tokens ?? {}), [key]: newValue } });
    };

    const toggleGroup = (label: string) => {
        setExpandedGroups(prev => ({ ...prev, [label]: !prev[label] }));
    };

    return (
        <>
            {isSuccess && (
                <div className="max-w-[340px] mx-auto mt-4 ml-2 space-y-4">
                    {/* Logo */}
                    <FormControl>
                        <h3 className="text-xl font-bold">Logo</h3>
                        <input type="file" accept="image/*" className="hidden" id="logoInput" />
                        <label htmlFor="logoInput" className="cursor-pointer">
                            <Plus />
                            {logoFile ? `${logoFile.name} (${logoDimensions.width}x${logoDimensions.height}px)` : ''}
                        </label>
                    </FormControl>

                    {/* Style */}
                    <FormControl required>
                        <h3 className="text-xl font-bold">Style</h3>
                        <Select
                            placeholder="Choose one…"
                            value={data.selectedStyle}
                            onChange={(_, v) => setData({ ...data, selectedStyle: v })}
                        >
                            <Option value="basic">Basic</Option>
                            <Option value="modern">Modern</Option>
                            <Option value="abstract">Abstract</Option>
                            <Option value="elegant">Elegant</Option>
                            <Option value="brutalist">Brutalist</Option>
                            <Option value="glassmorphism">Glassmorphism</Option>
                            <Option value="dark">Dark</Option>
                        </Select>
                    </FormControl>

                    {/* Layout */}
                    <FormControl required>
                        <h3 className="text-xl font-bold">Layout</h3>
                        <Select
                            placeholder="Choose one…"
                            value={data.selectedLayout || 'sidebar_left'}
                            onChange={(_, v) => setData({ ...data, selectedLayout: v })}
                        >
                            <Option value="sidebar_left">Sidebar Left</Option>
                            <Option value="sidebar_right">Sidebar Right</Option>
                            <Option value="top_nav">Top Navigation</Option>
                            <Option value="top_nav_sidebar">Top Nav + Sidebar</Option>
                        </Select>
                    </FormControl>

                    {/* Background color */}
                    <FormControl>
                        <h3 className="text-xl font-bold">Background color</h3>
                        <div className="flex w-full flex-row justify-between pb-1">
                            <Input
                                type="text"
                                value={data.backgroundColor}
                                onChange={e => setData({ ...data, backgroundColor: e.target.value })}
                                placeholder="#FFFFFF"
                            />
                            <input
                                type="color"
                                value={data.backgroundColor}
                                onChange={e => setData({ ...data, backgroundColor: e.target.value })}
                                className="w-[50px] h-[50px] border border-gray-500 p-0 cursor-pointer"
                            />
                        </div>
                    </FormControl>

                    {/* Text color */}
                    <FormControl>
                        <h3 className="text-xl font-bold">Text color</h3>
                        <div className="flex w-full flex-row justify-between pb-1">
                            <Input
                                type="text"
                                value={data.textColor}
                                onChange={e => setData({ ...data, textColor: e.target.value })}
                                placeholder="#000000"
                            />
                            <input
                                type="color"
                                value={data.textColor}
                                onChange={e => setData({ ...data, textColor: e.target.value })}
                                className="w-[50px] h-[50px] border border-gray-500 p-0 cursor-pointer"
                            />
                        </div>
                    </FormControl>

                    {/* Accent color */}
                    <FormControl>
                        <h3 className="text-xl font-bold">Accent color</h3>
                        <div className="flex w-full flex-row justify-between pb-1">
                            <Input
                                type="text"
                                value={data.accentColor}
                                onChange={e => setData({ ...data, accentColor: e.target.value })}
                                placeholder="#777777"
                            />
                            <input
                                type="color"
                                value={data.accentColor}
                                onChange={e => setData({ ...data, accentColor: e.target.value })}
                                className="w-[50px] h-[50px] border border-gray-500 p-0 cursor-pointer"
                            />
                        </div>
                    </FormControl>

                    {/* Radius */}
                    <FormControl required>
                        <h3 className="text-xl font-bold">Radius</h3>
                        <Input
                            type="number"
                            value={data.radius}
                            onChange={e => {
                                const v = parseInt(e.target.value, 10);
                                if (v >= 0 && v <= 10) setData({ ...data, radius: v });
                            }}
                            required
                        />
                    </FormControl>

                    {/* Theme Tokens */}
                    {theme?.tokens && Object.keys(theme.tokens).length > 0 && (
                        <div className="pt-2 border-t border-gray-200 space-y-3">
                            <div>
                                <h3 className="text-xl font-bold">Theme Tokens</h3>
                                {theme.name && (
                                    <p className="text-sm text-gray-500 mt-0.5">{theme.name}</p>
                                )}
                                <p className="text-xs text-gray-400 mt-0.5">
                                    Fine-tune individual UI elements. Click "Raw CSS" for full control.
                                </p>
                            </div>

                            {TOKEN_GROUPS.map(({ label, prefix }) => {
                                const groupTokens = Object.entries(theme.tokens!).filter(
                                    ([k]) => k.startsWith(prefix)
                                );
                                if (groupTokens.length === 0) return null;
                                const isOpen = expandedGroups[label];
                                return (
                                    <div key={label} className="border border-gray-200 rounded-lg overflow-hidden">
                                        <button
                                            type="button"
                                            className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 text-left"
                                            onClick={() => toggleGroup(label)}
                                        >
                                            <span className="font-semibold text-sm">{label}</span>
                                            <span className="flex items-center gap-2">
                                                <span className="text-xs text-gray-400">{groupTokens.length} items</span>
                                                {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                            </span>
                                        </button>
                                        {isOpen && (
                                            <div className="p-2 space-y-2 bg-gray-50">
                                                {groupTokens.map(([key, value]) => (
                                                    <TokenEditor
                                                        key={key}
                                                        tokenKey={key}
                                                        value={value}
                                                        onChange={handleTokenChange}
                                                    />
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}

                            {/* Ungrouped tokens */}
                            {(() => {
                                const ungrouped = Object.entries(theme.tokens!).filter(
                                    ([k]) => !TOKEN_GROUPS.some(g => k.startsWith(g.prefix))
                                );
                                if (ungrouped.length === 0) return null;
                                return (
                                    <div className="space-y-2">
                                        {ungrouped.map(([key, value]) => (
                                            <TokenEditor
                                                key={key}
                                                tokenKey={key}
                                                value={value}
                                                onChange={handleTokenChange}
                                            />
                                        ))}
                                    </div>
                                );
                            })()}
                        </div>
                    )}
                </div>
            )}
        </>
    );
};

export default Styling;
