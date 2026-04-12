import { authAxios } from "$lib/features/auth/state/auth";
import {
    GeneratorApp,
    GeneratorPipelineStatus,
    GeneratorTheme,
    useGeneratorPipeline,
    useRefinePipeline,
} from "$lib/features/prototypes/pipelineQueries";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, RefreshCw, Sparkles, History } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";

// ── Theme token viewer ────────────────────────────────────────────────────────

const TokenRow: React.FC<{ tokenKey: string; classes: string }> = ({ tokenKey, classes }) => {
    // Extract a representative bg/text class for a visual swatch
    const bgClass = classes.split(" ").find((c) => c.startsWith("bg-"));
    const textClass = classes.split(" ").find((c) => c.startsWith("text-") && c.includes("-"));

    return (
        <div className="flex items-start gap-2 py-1.5 border-b border-gray-100 last:border-0">
            <div
                className={`mt-0.5 h-4 w-4 shrink-0 rounded border border-gray-200 shadow-sm ${bgClass ?? "bg-gray-100"} ${textClass ?? ""}`}
            />
            <div className="flex flex-col min-w-0">
                <span className="text-xs font-mono font-semibold text-gray-700 truncate">{tokenKey}</span>
                <span className="text-xs text-gray-400 truncate">{classes}</span>
            </div>
        </div>
    );
};

const ThemePanel: React.FC<{ theme: GeneratorTheme }> = ({ theme }) => (
    <div className="flex flex-col gap-1">
        <div className="flex items-center gap-1.5 mb-1">
            <Sparkles size={13} className="text-violet-500" />
            <span className="text-xs font-semibold text-violet-700">{theme.name}</span>
            <span className="ml-auto text-xs text-gray-400">{Object.keys(theme.tokens).length} tokens</span>
        </div>
        <div className="max-h-52 overflow-y-auto pr-1">
            {Object.entries(theme.tokens).map(([k, v]) => (
                <TokenRow key={k} tokenKey={k} classes={v} />
            ))}
        </div>
    </div>
);

// ── Actor / Page tab bars ─────────────────────────────────────────────────────

const ActorTabs: React.FC<{
    apps: GeneratorApp[];
    activeId: string;
    onSelect: (id: string) => void;
}> = ({ apps, activeId, onSelect }) => (
    <div className="flex overflow-x-auto border-b border-gray-200 bg-gray-50 shrink-0">
        <span className="px-3 py-2 text-xs font-medium text-gray-400 self-center shrink-0">Actor:</span>
        {apps.map((a) => (
            <button
                key={a.actor_id}
                onClick={() => onSelect(a.actor_id)}
                className={`px-4 py-2 text-xs whitespace-nowrap border-r border-gray-200 transition-colors ${
                    activeId === a.actor_id
                        ? "bg-white font-semibold text-indigo-700 border-b-2 border-b-indigo-500"
                        : "text-gray-500 hover:bg-gray-100"
                }`}
            >
                {a.actor_name}
            </button>
        ))}
    </div>
);

const PageTabs: React.FC<{
    pages: { page_id: string; name: string }[];
    activeName: string;
    onSelect: (name: string) => void;
}> = ({ pages, activeName, onSelect }) => (
    <div className="flex overflow-x-auto border-b border-gray-200 bg-white shrink-0">
        {pages.map((p) => (
            <button
                key={p.page_id}
                onClick={() => onSelect(p.name)}
                className={`px-4 py-2 text-xs whitespace-nowrap border-r border-gray-200 transition-colors ${
                    activeName === p.name
                        ? "bg-gray-50 font-semibold text-gray-800 border-b-2 border-b-blue-500"
                        : "text-gray-500 hover:bg-gray-50"
                }`}
            >
                {p.name}
            </button>
        ))}
    </div>
);

// ── Refinement history ────────────────────────────────────────────────────────

const HistoryPanel: React.FC<{ history: string[] }> = ({ history }) => {
    if (history.length === 0) return null;
    return (
        <div className="flex flex-col gap-1">
            <div className="flex items-center gap-1.5 text-xs font-medium text-gray-400">
                <History size={12} />
                Recent prompts
            </div>
            <div className="flex flex-col gap-1 max-h-32 overflow-y-auto">
                {history.map((h, i) => (
                    <div
                        key={i}
                        className="rounded bg-gray-50 border border-gray-100 px-2 py-1.5 text-xs text-gray-600 truncate"
                        title={h}
                    >
                        {h}
                    </div>
                ))}
            </div>
        </div>
    );
};

// ── Main page ─────────────────────────────────────────────────────────────────

export const DesignRefinePage: React.FC = () => {
    const { threadId } = useParams<{ threadId: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const { data, isLoading, isError } = useGeneratorPipeline(threadId);
    const refine = useRefinePipeline(threadId ?? "");

    const [activeActorId, setActiveActorId] = useState<string>("");
    const [activePage, setActivePage] = useState<string>("");
    const [previewHtml, setPreviewHtml] = useState<string>("");
    const [previewLoading, setPreviewLoading] = useState(false);
    const [prompt, setPrompt] = useState("");
    const [history, setHistory] = useState<string[]>([]);
    const [liveData, setLiveData] = useState<GeneratorPipelineStatus | null>(null);
    const previewFetchRef = useRef(0);

    // Initialise actor/page selection when data arrives
    useEffect(() => {
        const source = liveData ?? data;
        if (!source) return;
        const apps = source.ui_design?.ui_ir?.apps ?? [];
        if (!activeActorId && apps.length > 0) {
            setActiveActorId(apps[0].actor_id);
            const firstPage = apps[0].pages?.[0];
            if (firstPage) setActivePage(firstPage.name);
        }
    }, [data, liveData]);

    // Fetch preview HTML whenever actor or page changes
    useEffect(() => {
        if (!threadId || !activeActorId || !activePage) return;
        const seq = ++previewFetchRef.current;
        setPreviewLoading(true);
        authAxios
            .get<string>(
                `/v1/generator/pipeline/${threadId}/preview/?actor=${activeActorId}&page=${activePage}`,
                { responseType: "text" },
            )
            .then((res) => {
                if (seq !== previewFetchRef.current) return; // stale
                setPreviewHtml(res.data);
            })
            .finally(() => {
                if (seq === previewFetchRef.current) setPreviewLoading(false);
            });
    }, [threadId, activeActorId, activePage]);

    const handleRefine = async () => {
        if (!prompt.trim() || !threadId) return;
        const trimmedPrompt = prompt.trim();
        try {
            const result = await refine.mutateAsync({ prompt: trimmedPrompt });
            setLiveData(result);
            setHistory((h) => [trimmedPrompt, ...h].slice(0, 10));
            setPrompt("");
            // Invalidate so other consumers reflect new theme
            queryClient.invalidateQueries({ queryKey: ["generator-pipeline", threadId] });
            // Re-fetch preview with new theme — trigger by bumping the page state
            setActivePage((p) => {
                // tiny toggle trick: set same value causes no re-render; use a counter flag instead
                return p;
            });
            // Force preview refresh
            previewFetchRef.current++;
            const seq = previewFetchRef.current;
            setPreviewLoading(true);
            authAxios
                .get<string>(
                    `/v1/generator/pipeline/${threadId}/preview/?actor=${activeActorId}&page=${activePage}`,
                    { responseType: "text" },
                )
                .then((res) => {
                    if (seq !== previewFetchRef.current) return;
                    setPreviewHtml(res.data);
                })
                .finally(() => {
                    if (seq === previewFetchRef.current) setPreviewLoading(false);
                });
        } catch {
            // error displayed via refine.isError
        }
    };

    const source = liveData ?? data;
    const apps = source?.ui_design?.ui_ir?.apps ?? [];
    const activeApp = apps.find((a) => a.actor_id === activeActorId);
    const pages = activeApp?.pages ?? [];
    const theme = source?.theme ?? null;

    // ── loading / error guards ───────────────────────────────────────────────
    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="flex flex-col items-center gap-3 text-gray-500">
                    <RefreshCw size={24} className="animate-spin" />
                    <span className="text-sm">Loading pipeline…</span>
                </div>
            </div>
        );
    }

    if (isError || !source) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="flex flex-col items-center gap-3 text-gray-500">
                    <span className="text-sm font-medium text-red-500">Pipeline not found</span>
                    <button
                        className="text-xs text-indigo-600 hover:underline"
                        onClick={() => navigate(-1)}
                    >
                        Go back
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="absolute inset-0 flex flex-col overflow-hidden bg-white">
            {/* ── Header ───────────────────────────────────────────────── */}
            <header className="flex shrink-0 items-center gap-3 border-b border-gray-200 bg-white px-4 py-3">
                <button
                    onClick={() => {
                        const sysId = source?.system_id;
                        if (sysId) {
                            navigate(`/systems/${sysId}`);
                        } else if (window.history.length > 1) {
                            navigate(-1);
                        } else {
                            navigate("/");
                        }
                    }}
                    className="flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
                >
                    <ArrowLeft size={13} />
                    Back
                </button>
                <div className="flex flex-col">
                    <span className="text-sm font-semibold text-gray-900">UI Design Refine</span>
                    <span className="font-mono text-xs text-gray-400">{threadId}</span>
                </div>
                <div className="ml-auto flex items-center gap-2">
                    {theme && (
                        <span className="flex items-center gap-1 rounded-full bg-violet-50 px-2.5 py-1 text-xs font-medium text-violet-700">
                            <Sparkles size={11} />
                            {theme.name}
                        </span>
                    )}
                </div>
            </header>

            {/* ── Body ─────────────────────────────────────────────────── */}
            <div className="flex flex-1 overflow-hidden">
                {/* Left: Preview panel */}
                <div className="flex flex-1 flex-col overflow-hidden border-r border-gray-200">
                    {/* Actor tabs */}
                    {apps.length > 0 && (
                        <ActorTabs
                            apps={apps}
                            activeId={activeActorId}
                            onSelect={(id) => {
                                setActiveActorId(id);
                                const app = apps.find((a) => a.actor_id === id);
                                const first = app?.pages?.[0];
                                if (first) setActivePage(first.name);
                            }}
                        />
                    )}

                    {/* Page tabs */}
                    {pages.length > 0 && (
                        <PageTabs
                            pages={pages}
                            activeName={activePage}
                            onSelect={setActivePage}
                        />
                    )}

                    {/* Preview iframe */}
                    <div className="relative flex-1 overflow-hidden bg-gray-50">
                        {previewLoading && (
                            <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80">
                                <RefreshCw size={20} className="animate-spin text-indigo-400" />
                            </div>
                        )}
                        {previewHtml ? (
                            <iframe
                                key={`${activeActorId}__${activePage}__${history.length}`}
                                sandbox="allow-same-origin allow-scripts"
                                srcDoc={previewHtml}
                                className="h-full w-full border-0"
                                title={`Preview: ${activeApp?.actor_name} / ${activePage}`}
                            />
                        ) : (
                            <div className="flex h-full items-center justify-center text-sm text-gray-400">
                                {apps.length === 0
                                    ? "No pages generated yet."
                                    : "Select an actor and page to preview."}
                            </div>
                        )}
                    </div>
                </div>

                {/* Right: Control panel */}
                <div className="flex w-80 shrink-0 flex-col gap-4 overflow-y-auto p-4">
                    {/* Theme tokens */}
                    {theme ? (
                        <section>
                            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                                Current Theme
                            </h2>
                            <div className="rounded-lg border border-violet-100 bg-violet-50 p-3">
                                <ThemePanel theme={theme} />
                            </div>
                        </section>
                    ) : (
                        <div className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-xs text-gray-400">
                            No theme generated yet.
                        </div>
                    )}

                    {/* Prompt input */}
                    <section className="flex flex-col gap-2">
                        <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                            Refine UI Style
                        </h2>
                        <textarea
                            className="w-full resize-none rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-300"
                            rows={4}
                            placeholder="e.g. Make it more minimal with a dark sidebar, use green accents, round corners more..."
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                                    e.preventDefault();
                                    handleRefine();
                                }
                            }}
                            disabled={refine.isPending}
                        />
                        <button
                            onClick={handleRefine}
                            disabled={refine.isPending || !prompt.trim()}
                            className="flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {refine.isPending ? (
                                <>
                                    <RefreshCw size={14} className="animate-spin" />
                                    Generating…
                                </>
                            ) : (
                                <>
                                    <Sparkles size={14} />
                                    Apply style
                                </>
                            )}
                        </button>
                        <p className="text-xs text-gray-400">⌘ Enter to submit</p>

                        {refine.isError && (
                            <p className="rounded-md bg-red-50 border border-red-100 px-3 py-2 text-xs text-red-600">
                                Refinement failed. Please try again.
                            </p>
                        )}
                    </section>

                    {/* History */}
                    <section>
                        <HistoryPanel history={history} />
                    </section>
                </div>
            </div>
        </div>
    );
};

export default DesignRefinePage;
