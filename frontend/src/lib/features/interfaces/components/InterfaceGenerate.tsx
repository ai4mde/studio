import { authAxios } from "$auth/state/auth";
import { baseURL } from "$shared/globals";
import { RefreshCw, Sparkles, Check, MessageSquare, Wand2 } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

type VariantSummary = {
    id: string;
    name: string;
    description: string;
};

type Props = {
    interfaceId: string;
    systemId: string;
};

const InterfaceGenerate: React.FC<Props> = ({ interfaceId, systemId }) => {
    const qc = useQueryClient();
    const [prompt, setPrompt] = useState("");
    const [generating, setGenerating] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [variants, setVariants] = useState<VariantSummary[]>([]);
    const [selectedVariant, setSelectedVariant] = useState<string | null>(null);
    const [refinePrompt, setRefinePrompt] = useState("");
    const [refining, setRefining] = useState(false);
    const [applying, setApplying] = useState(false);
    const [error, setError] = useState("");
    const [refineHistory, setRefineHistory] = useState<string[]>([]);
    const [applied, setApplied] = useState(false);
    const iframeRefs = useRef<Record<string, number>>({});
    const [restoring, setRestoring] = useState(true);

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
                setRefineHistory(data.refine_history || []);
                setSelectedVariant(data.selected_variant_id || null);
                setPrompt(data.original_prompt || "");
                if (data.applied) setApplied(true);
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
        setSessionId(null);
        setSelectedVariant(null);
        setRefineHistory([]);
        setApplied(false);
        try {
            const { data } = await authAxios.post("/v1/generator/interface-gen/generate/", {
                interface_id: interfaceId,
                prompt: prompt.trim(),
            }, { timeout: 120000 });
            setSessionId(data.session_id);
            setVariants(data.variants);
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
            const { data } = await authAxios.post(
                `/v1/generator/interface-gen/${sessionId}/refine/`,
                { variant_id: selectedVariant, prompt: refinePrompt.trim() },
                { timeout: 120000 },
            );
            // Update variant info
            const updated = data.variant;
            setVariants((prev) =>
                prev.map((v) =>
                    v.id === updated.id ? { ...v, name: updated.name, description: updated.description } : v,
                ),
            );
            setRefineHistory(data.refine_history || []);
            setRefinePrompt("");
            // Force iframe refresh
            iframeRefs.current[selectedVariant] = (iframeRefs.current[selectedVariant] || 0) + 1;
            // Trigger re-render
            setSelectedVariant((prev) => prev);
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
            // Invalidate interface cache so ShowInterface re-seeds localStorage with new styling
            qc.invalidateQueries({ queryKey: ["interface", interfaceId] });
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
                        Describe how you want the interface to look. The AI will generate 3 distinct style variants for you to preview and refine.
                    </p>
                </div>
                <div className="w-full max-w-lg flex flex-col gap-3">
                    <textarea
                        className="w-full resize-none rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                        rows={4}
                        placeholder="e.g. Modern dark theme with purple accents, clean typography, rounded cards with subtle shadows..."
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
                                Generating 3 Variants…
                            </>
                        ) : (
                            <>
                                <Sparkles size={16} />
                                Generate 3 Variants
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

    // Applied — don't show a separate screen, continue showing variants
    // The "applied" badge is shown in the header below

    // Auto-select first variant as the active tab
    const activeTab = selectedVariant || (variants.length > 0 ? variants[0].id : null);

    // Session active — show variants as tabs with large preview
    return (
        <div className="flex flex-col" style={{ height: "calc(100vh - 200px)" }}>
            {/* Header row */}
            <div className="flex items-center justify-between shrink-0 px-4 py-2 border-b bg-gray-50">
                <div className="flex items-center gap-2 truncate max-w-md">
                    <p className="text-xs text-gray-400 truncate">
                        Prompt: &ldquo;{variants.length > 0 ? prompt : "..."}&rdquo;
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
                        setSelectedVariant(null);
                        setRefineHistory([]);
                        setApplied(false);
                    }}
                    className="text-xs text-gray-500 hover:text-gray-700"
                >
                    Start Over
                </button>
            </div>

            {/* Variant tabs */}
            <div className="flex items-center shrink-0 border-b bg-white">
                {variants.map((v) => {
                    const isActive = activeTab === v.id;
                    return (
                        <button
                            key={v.id}
                            onClick={() => setSelectedVariant(v.id)}
                            className={`relative px-5 py-3 text-sm font-medium transition-colors ${
                                isActive
                                    ? "text-indigo-600 border-b-2 border-indigo-600 bg-white"
                                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                            }`}
                        >
                            <span>{v.name}</span>
                            <span className="ml-2 text-xs font-normal text-gray-400 hidden sm:inline">
                                {v.description && v.description.length > 50
                                    ? v.description.slice(0, 50) + "…"
                                    : v.description}
                            </span>
                        </button>
                    );
                })}
            </div>

            {/* Large preview area */}
            <div className="flex-1 min-h-0 bg-gray-100 overflow-hidden">
                {variants.map((v) => {
                    const isActive = activeTab === v.id;
                    const refreshKey = iframeRefs.current[v.id] || 0;
                    return (
                        <div
                            key={v.id}
                            className={`h-full ${isActive ? "block" : "hidden"}`}
                        >
                            <iframe
                                key={`${v.id}_${refreshKey}`}
                                src={`${baseURL}/v1/generator/interface-gen/${sessionId}/preview/${v.id}/`}
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
                        placeholder={`Refine "${variants.find((v) => v.id === activeTab)?.name || ""}" — e.g. darker background, rounder buttons...`}
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
                        {applied ? "Re-apply Theme" : "Apply Theme"}
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
