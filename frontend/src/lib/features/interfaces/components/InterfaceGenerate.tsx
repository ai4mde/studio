import { authAxios } from "$auth/state/auth";
import { baseURL } from "$shared/globals";
import { RefreshCw, Sparkles, Check, MessageSquare, Wand2 } from "lucide-react";
import React, { useRef, useState } from "react";

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
        } catch (err) {
            console.error(err);
            setError(err instanceof Error ? err.message : "Apply failed");
        } finally {
            setApplying(false);
        }
    };

    // No session yet — show prompt input
    if (!sessionId) {
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

    // Applied successfully
    if (applied) {
        return (
            <div className="flex flex-col items-center justify-center gap-4 py-12">
                <div className="flex items-center gap-2 text-green-600">
                    <Check size={32} />
                    <h2 className="text-lg font-semibold">Theme Applied Successfully!</h2>
                </div>
                <p className="text-sm text-gray-500">The selected variant has been saved to this interface.</p>
                <button
                    onClick={() => {
                        setSessionId(null);
                        setVariants([]);
                        setSelectedVariant(null);
                        setPrompt("");
                        setApplied(false);
                        setRefineHistory([]);
                    }}
                    className="text-sm text-indigo-600 hover:underline"
                >
                    Generate New Variants
                </button>
            </div>
        );
    }

    // Session active — show variants
    return (
        <div className="flex flex-col gap-4 h-full">
            {/* Header */}
            <div className="flex items-center justify-between shrink-0">
                <div>
                    <h2 className="text-sm font-semibold text-gray-800">
                        3 Style Variants Generated
                    </h2>
                    <p className="text-xs text-gray-400 mt-0.5">
                        Prompt: &ldquo;{variants.length > 0 ? prompt : "..."}&rdquo;
                    </p>
                </div>
                <button
                    onClick={() => {
                        setSessionId(null);
                        setVariants([]);
                        setSelectedVariant(null);
                        setRefineHistory([]);
                    }}
                    className="text-xs text-gray-500 hover:text-gray-700"
                >
                    Start Over
                </button>
            </div>

            {/* Variant Grid */}
            <div className="grid grid-cols-3 gap-4 flex-1 min-h-0">
                {variants.map((v) => {
                    const isSelected = selectedVariant === v.id;
                    const refreshKey = iframeRefs.current[v.id] || 0;
                    return (
                        <div
                            key={v.id}
                            className={`flex flex-col rounded-xl border-2 transition-all overflow-hidden ${
                                isSelected
                                    ? "border-indigo-500 ring-2 ring-indigo-200 shadow-lg"
                                    : "border-gray-200 hover:border-indigo-300 hover:shadow"
                            }`}
                        >
                            {/* Variant header */}
                            <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border-b shrink-0">
                                <div className="flex flex-col min-w-0">
                                    <span className="text-xs font-semibold text-gray-700 truncate">
                                        {v.name}
                                    </span>
                                    <span className="text-xs text-gray-400 truncate">
                                        {v.description}
                                    </span>
                                </div>
                                <button
                                    onClick={() => setSelectedVariant(v.id)}
                                    className={`shrink-0 ml-2 px-2 py-1 rounded text-xs font-medium transition-colors ${
                                        isSelected
                                            ? "bg-indigo-600 text-white"
                                            : "bg-white border border-gray-300 text-gray-600 hover:bg-indigo-50"
                                    }`}
                                >
                                    {isSelected ? (
                                        <span className="flex items-center gap-1">
                                            <Check size={10} /> Selected
                                        </span>
                                    ) : (
                                        "Select"
                                    )}
                                </button>
                            </div>
                            {/* Preview iframe */}
                            <div className="flex-1 min-h-[300px] bg-white">
                                <iframe
                                    key={`${v.id}_${refreshKey}`}
                                    src={`${baseURL}/v1/generator/interface-gen/${sessionId}/preview/${v.id}/`}
                                    className="w-full h-full border-0"
                                    sandbox="allow-same-origin allow-scripts"
                                    title={`Preview: ${v.name}`}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Refinement Panel (shown when a variant is selected) */}
            {selectedVariant && (
                <div className="shrink-0 border-t pt-4 flex flex-col gap-3">
                    <div className="flex items-start gap-4">
                        <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                                <MessageSquare size={14} className="text-indigo-500" />
                                <span className="text-xs font-semibold text-gray-600">
                                    Refine &ldquo;{variants.find((v) => v.id === selectedVariant)?.name}&rdquo;
                                </span>
                            </div>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-300"
                                    placeholder="e.g. Make the buttons rounder, use more contrast, darker background..."
                                    value={refinePrompt}
                                    onChange={(e) => setRefinePrompt(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter") {
                                            e.preventDefault();
                                            handleRefine();
                                        }
                                    }}
                                    disabled={refining}
                                />
                                <button
                                    onClick={handleRefine}
                                    disabled={refining || !refinePrompt.trim()}
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
                                    onClick={handleApply}
                                    disabled={applying}
                                    className="flex items-center gap-1.5 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {applying ? (
                                        <RefreshCw size={14} className="animate-spin" />
                                    ) : (
                                        <Check size={14} />
                                    )}
                                    Apply Theme
                                </button>
                            </div>
                        </div>
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
            )}

            {error && (
                <p className="rounded-md bg-red-50 border border-red-100 px-3 py-2 text-xs text-red-600">
                    {error}
                </p>
            )}
        </div>
    );
};

export default InterfaceGenerate;
