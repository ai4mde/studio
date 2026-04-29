import { authAxios } from "$auth/state/auth";
import { baseURL } from "$shared/globals";
import { RefreshCw, Sparkles, Check, MessageSquare, Wand2, Layout, ChevronLeft, ChevronRight } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";

type VariantSummary = {
    id: string;
    name: string;
    description: string;
    composition_summary?: {
        pages: Array<{
            page_id: string;
            skeleton_id: string;
            page_archetype: string;
            region_count: number;
            binding_count: number;
        }>;
    };
};

type PageInfo = { id: string; name: string };

type Props = {
    interfaceId: string;
    systemId: string;
    onVariantTokensChange?: (theme: { name: string; tokens: Record<string, string> }) => void;
};

function SkeletonBadge({ skeletonId }: { skeletonId: string }) {
    if (!skeletonId) return null;
    const parts = skeletonId.split("/");
    const label = parts[parts.length - 1] ?? skeletonId;
    return (
        <span className="inline-flex items-center gap-1 rounded bg-indigo-50 border border-indigo-100 px-1.5 py-0.5 text-[10px] font-mono text-indigo-600">
            <Layout size={9} />
            {label}
        </span>
    );
}

function CompositionSummaryBar({ variant }: { variant: VariantSummary }) {
    const pages = variant.composition_summary?.pages ?? [];
    if (pages.length === 0) return null;
    return (
        <div className="flex items-center gap-2 flex-wrap px-1">
            {pages.map((p) => (
                <SkeletonBadge key={p.page_id} skeletonId={p.skeleton_id} />
            ))}
        </div>
    );
}

const InterfaceGenerate: React.FC<Props> = ({ interfaceId, systemId, onVariantTokensChange }) => {
    const [prompt, setPrompt] = useState("");
    const [generating, setGenerating] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [variants, setVariants] = useState<VariantSummary[]>([]);
    const [pages, setPages] = useState<PageInfo[]>([]);
    const [selectedVariant, setSelectedVariant] = useState<string | null>(null);
    const [selectedPageIndex, setSelectedPageIndex] = useState(0);
    const [refinePrompt, setRefinePrompt] = useState("");
    const [refining, setRefining] = useState(false);
    const [applying, setApplying] = useState(false);
    const [error, setError] = useState("");
    const [refineHistory, setRefineHistory] = useState<string[]>([]);
    const [applied, setApplied] = useState(false);
    const iframeKeys = useRef<Record<string, number>>({});
    const [restoring, setRestoring] = useState(true);

    const bumpIframe = (variantId: string) => {
        iframeKeys.current[variantId] = (iframeKeys.current[variantId] || 0) + 1;
    };

    const pushVariantTheme = async (sid: string, variantId: string, fallbackName: string) => {
        if (!onVariantTokensChange) return;
        try {
            const { data } = await authAxios.get(
                `/v1/generator/interface-gen/${sid}/variant/${variantId}/`,
            );
            onVariantTokensChange({ name: data.name ?? fallbackName, tokens: data.tokens ?? {} });
        } catch { /* non-critical */ }
    };

    // Restore saved session on mount
    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const { data } = await authAxios.get(
                    `/v1/generator/interface-gen/restore/${interfaceId}/`,
                );
                if (cancelled) return;
                setSessionId(data.session_id);
                setVariants(data.variants || []);
                setPages(data.pages || []);
                setRefineHistory(data.refine_history || []);
                setSelectedVariant(data.selected_variant_id || null);
                setPrompt(data.original_prompt || "");
                if (data.applied) setApplied(true);
                const selectedId = data.selected_variant_id || (data.variants?.[0]?.id ?? null);
                if (selectedId) {
                    const name = data.variants?.find((v: VariantSummary) => v.id === selectedId)?.name ?? "";
                    await pushVariantTheme(data.session_id, selectedId, name);
                }
            } catch {
                // No saved session — that's fine
            } finally {
                if (!cancelled) setRestoring(false);
            }
        })();
        return () => { cancelled = true; };
    }, [interfaceId]);

    const handleGenerate = async () => {
        if (!prompt.trim()) return;
        setGenerating(true);
        setError("");
        setVariants([]);
        setPages([]);
        setSessionId(null);
        setSelectedVariant(null);
        setSelectedPageIndex(0);
        setRefineHistory([]);
        setApplied(false);
        try {
            const { data } = await authAxios.post("/v1/generator/interface-gen/generate/", {
                interface_id: interfaceId,
                prompt: prompt.trim(),
            }, { timeout: 120000 });
            setSessionId(data.session_id);
            setVariants(data.variants);
            // Fetch session to get pages list and full composition_summary
            try {
                const { data: sess } = await authAxios.get(`/v1/generator/interface-gen/${data.session_id}/`);
                setPages(sess.pages || []);
                if (sess.variants) setVariants(sess.variants);
            } catch { /* non-critical */ }
            if (data.variants?.length > 0) {
                const first = data.variants[0];
                await pushVariantTheme(data.session_id, first.id, first.name);
            }
        } catch (err) {
            console.error(err);
            setError(err instanceof Error ? err.message : "Generation failed");
        } finally {
            setGenerating(false);
        }
    };

    const handleRefine = async () => {
        if (!refinePrompt.trim() || !sessionId || !selectedVariant) return;
        setRefining(true);
        setError("");
        try {
            const activeVariantId = selectedVariant;
            const { data } = await authAxios.post(
                `/v1/generator/interface-gen/${sessionId}/refine/`,
                { variant_id: activeVariantId, prompt: refinePrompt.trim() },
                { timeout: 120000 },
            );
            const updated = data.variant;
            setVariants((prev) =>
                prev.map((v) =>
                    v.id === updated.id
                        ? { ...v, name: updated.name, description: updated.description, composition_summary: updated.composition_summary }
                        : v,
                ),
            );
            setRefineHistory(data.refine_history || []);
            setRefinePrompt("");
            bumpIframe(activeVariantId);
            setSelectedVariant((prev) => prev); // force re-render
            await pushVariantTheme(sessionId, activeVariantId, updated.name ?? "");
        } catch (err) {
            console.error(err);
            setError(err instanceof Error ? err.message : "Refinement failed");
        } finally {
            setRefining(false);
        }
    };

    const handleApply = async () => {
        if (!sessionId || !selectedVariant) return;
        setApplying(true);
        setError("");
        try {
            await authAxios.post(`/v1/generator/interface-gen/${sessionId}/apply/`, {
                variant_id: selectedVariant,
            });
            setApplied(true);
        } catch (err) {
            console.error(err);
            setError(err instanceof Error ? err.message : "Apply failed");
        } finally {
            setApplying(false);
        }
    };

    // No session yet — show prompt input
    if (!sessionId) {
        if (restoring) {
            return (
                <div className="flex items-center justify-center gap-2 py-12 text-sm text-gray-400">
                    <RefreshCw size={16} className="animate-spin" />
                    Restoring previous session…
                </div>
            );
        }
        return (
            <div className="flex flex-col items-center justify-center gap-6 py-12">
                <div className="flex flex-col items-center gap-2">
                    <Wand2 size={40} className="text-indigo-400" />
                    <h2 className="text-lg font-semibold text-gray-800">AI Interface Generator</h2>
                    <p className="text-sm text-gray-500 text-center max-w-md">
                        Describe the interface style. The AI will generate 3 structurally distinct layout variants —
                        each with a different page skeleton and section arrangement — for you to compare, refine, and apply.
                    </p>
                </div>
                <div className="w-full max-w-lg flex flex-col gap-3">
                    <textarea
                        className="w-full resize-none rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                        rows={4}
                        placeholder="e.g. Modern e-commerce product page — dark hero section, prominent buy-box, tabbed specifications below..."
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                                e.preventDefault();
                                handleGenerate();
                            }
                        }}
                        disabled={generating}
                    />
                    <button
                        onClick={handleGenerate}
                        disabled={generating || !prompt.trim()}
                        className="flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        {generating ? (
                            <>
                                <RefreshCw size={16} className="animate-spin" />
                                Generating 3 Layout Variants…
                            </>
                        ) : (
                            <>
                                <Sparkles size={16} />
                                Generate 3 Layout Variants
                            </>
                        )}
                    </button>
                    <p className="text-xs text-gray-400 text-center">⌘ Enter to submit</p>
                    {error && (
                        <p className="rounded-md bg-red-50 border border-red-100 px-3 py-2 text-xs text-red-600">
                            {error}
                        </p>
                    )}
                </div>
            </div>
        );
    }

    const activeTab = selectedVariant || (variants.length > 0 ? variants[0].id : null);
    const activeVariant = variants.find((v) => v.id === activeTab) ?? null;

    return (
        <div className="flex flex-col" style={{ height: "calc(100vh - 200px)" }}>
            {/* Header row */}
            <div className="flex items-center justify-between shrink-0 px-4 py-2 border-b bg-gray-50">
                <div className="flex items-center gap-2 truncate max-w-md">
                    <p className="text-xs text-gray-400 truncate">
                        &ldquo;{variants.length > 0 ? prompt : "..."}&rdquo;
                    </p>
                    {applied && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-green-50 border border-green-200 px-2 py-0.5 text-xs font-medium text-green-700">
                            <Check size={10} /> Applied
                        </span>
                    )}
                </div>
                <button
                    onClick={() => {
                        setSessionId(null);
                        setVariants([]);
                        setPages([]);
                        setSelectedVariant(null);
                        setSelectedPageIndex(0);
                        setRefineHistory([]);
                        setApplied(false);
                    }}
                    className="text-xs text-gray-500 hover:text-gray-700"
                >
                    Start Over
                </button>
            </div>

            {/* Variant tabs */}
            <div className="flex items-start shrink-0 border-b bg-white overflow-x-auto">
                {variants.map((v) => {
                    const isActive = activeTab === v.id;
                    return (
                        <button
                            key={v.id}
                            onClick={() => {
                                setSelectedVariant(v.id);
                                pushVariantTheme(sessionId!, v.id, v.name);
                            }}
                            className={`flex flex-col gap-0.5 px-4 py-2.5 text-sm font-medium transition-colors text-left shrink-0 ${
                                isActive
                                    ? "text-indigo-600 border-b-2 border-indigo-600 bg-white"
                                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                            }`}
                        >
                            <span className="flex items-center gap-1.5">
                                {v.name}
                            </span>
                            <CompositionSummaryBar variant={v} />
                            {v.description && (
                                <span className="text-[10px] font-normal text-gray-400 max-w-[200px] truncate hidden sm:block">
                                    {v.description}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Page navigation (shown only when interface has multiple pages) */}
            {pages.length > 1 && (
                <div className="shrink-0 flex items-center gap-1 px-3 py-1.5 border-b bg-gray-50 overflow-x-auto">
                    <button
                        onClick={() => setSelectedPageIndex((i) => Math.max(0, i - 1))}
                        disabled={selectedPageIndex === 0}
                        className="p-0.5 rounded text-gray-400 hover:text-gray-700 disabled:opacity-30"
                    >
                        <ChevronLeft size={14} />
                    </button>
                    {pages.map((p, idx) => (
                        <button
                            key={p.id}
                            onClick={() => setSelectedPageIndex(idx)}
                            className={`px-2.5 py-0.5 rounded text-xs font-medium transition-colors ${
                                idx === selectedPageIndex
                                    ? "bg-indigo-100 text-indigo-700"
                                    : "text-gray-500 hover:bg-gray-100"
                            }`}
                        >
                            {p.name || `Page ${idx + 1}`}
                        </button>
                    ))}
                    <button
                        onClick={() => setSelectedPageIndex((i) => Math.min(pages.length - 1, i + 1))}
                        disabled={selectedPageIndex === pages.length - 1}
                        className="p-0.5 rounded text-gray-400 hover:text-gray-700 disabled:opacity-30"
                    >
                        <ChevronRight size={14} />
                    </button>
                </div>
            )}

            {/* Large preview area */}
            <div className="flex-1 min-h-0 bg-gray-100 overflow-hidden">
                {variants.map((v) => {
                    const isActive = activeTab === v.id;
                    const refreshKey = (iframeKeys.current[v.id] || 0) * 100 + selectedPageIndex;
                    return (
                        <div
                            key={v.id}
                            className={`h-full ${isActive ? "block" : "hidden"}`}
                        >
                            <iframe
                                key={`${v.id}_${refreshKey}`}
                                src={`${baseURL}/v1/generator/interface-gen/${sessionId}/preview/${v.id}/?page_index=${selectedPageIndex}`}
                                className="w-full h-full border-0"
                                style={{ minHeight: "500px" }}
                                sandbox="allow-same-origin allow-scripts"
                                title={`Preview: ${v.name}`}
                            />
                        </div>
                    );
                })}
            </div>

            {/* Bottom action bar */}
            <div className="shrink-0 border-t bg-white px-4 py-3 flex flex-col gap-2">
                <div className="flex items-center gap-2">
                    <MessageSquare size={14} className="text-indigo-500 shrink-0" />
                    <input
                        type="text"
                        className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-300"
                        placeholder={`Refine "${activeVariant?.name ?? ""}" — style: "darker bg, rounded buttons" or layout: "move filters to sidebar"`}
                        value={refinePrompt}
                        onChange={(e) => setRefinePrompt(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                e.preventDefault();
                                if (activeTab) setSelectedVariant(activeTab);
                                handleRefine();
                            }
                        }}
                        disabled={refining}
                    />
                    <button
                        onClick={() => {
                            if (activeTab) setSelectedVariant(activeTab);
                            handleRefine();
                        }}
                        disabled={refining || !refinePrompt.trim() || !activeTab}
                        className="flex items-center gap-1.5 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {refining ? (
                            <RefreshCw size={14} className="animate-spin" />
                        ) : (
                            <Sparkles size={14} />
                        )}
                        Refine
                    </button>
                    <button
                        onClick={() => {
                            if (activeTab) setSelectedVariant(activeTab);
                            handleApply();
                        }}
                        disabled={applying || !activeTab}
                        className="flex items-center gap-1.5 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {applying ? (
                            <RefreshCw size={14} className="animate-spin" />
                        ) : (
                            <Check size={14} />
                        )}
                        {applied ? "Re-apply Layout + Theme" : "Apply Layout + Theme"}
                    </button>
                </div>

                {/* Refine History */}
                {refineHistory.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                        {refineHistory.map((h, i) => (
                            <span
                                key={i}
                                className="rounded-full bg-violet-50 border border-violet-100 px-2 py-0.5 text-xs text-violet-600"
                                title={h}
                            >
                                {h.length > 40 ? h.slice(0, 40) + "…" : h}
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {error && (
                <p className="rounded-md bg-red-50 border border-red-100 px-3 py-2 text-xs text-red-600 mx-4 mb-2">
                    {error}
                </p>
            )}
        </div>
    );
};

export default InterfaceGenerate;
