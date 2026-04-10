import {
    Button,
    CircularProgress,
    Divider,
    FormControl,
    FormLabel,
    Modal,
    ModalClose,
    ModalDialog,
    Switch,
    Textarea,
    Typography,
} from "@mui/joy";
import { useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight, CheckCircle, MessageSquare, Sparkles } from "lucide-react";
import React, { useState } from "react";
import { useParams } from "react-router";
import {
    PipelineStatus,
    ScreenInfo,
    UIDesign,
    UXDraft,
    UXReview,
    useResumePipeline,
    useRunPipeline,
} from "../pipelineQueries";
import { useSystemDiagrams, useSystemInterfaces } from "../queries";

const SCREEN_TYPE_COLORS: Record<string, string> = {
    list: "bg-blue-100 text-blue-800",
    dashboard: "bg-purple-100 text-purple-800",
    form: "bg-green-100 text-green-800",
    activity: "bg-orange-100 text-orange-800",
    modal: "bg-yellow-100 text-yellow-800",
    wizard: "bg-pink-100 text-pink-800",
};

// ── UX Generator output panel ─────────────────────────────────────────────────

const UXGeneratorPanel: React.FC<{ draft: UXDraft }> = ({ draft }) => (
    <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm flex flex-col gap-2">
        <div className="flex items-center gap-2 font-semibold text-blue-700">
            <Sparkles size={14} />
            Agent 1 — UX Generator
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-700">
            <div>
                <div className="font-medium text-gray-500 mb-1">Objects</div>
                {draft.objects.map((o) => (
                    <span key={o} className="inline-block mr-1 mb-1 rounded-full bg-white border border-blue-200 px-2 py-0.5">{o}</span>
                ))}
            </div>
            <div>
                <div className="font-medium text-gray-500 mb-1">Screens</div>
                {draft.screens.map((s) => (
                    <span key={s} className="inline-block mr-1 mb-1 rounded-full bg-white border border-blue-200 px-2 py-0.5">{s}</span>
                ))}
            </div>
            {Object.keys(draft.actor_screens ?? {}).length > 0 && (
                <div className="col-span-2">
                    <div className="font-medium text-gray-500 mb-1">Actor Screens</div>
                    {Object.entries(draft.actor_screens).map(([actor, screens]) => (
                        <div key={actor} className="mb-1">
                            <span className="font-semibold text-blue-600 mr-1">{actor}:</span>
                            {screens.map((s) => (
                                <span key={s} className="inline-block mr-1 rounded-full bg-white border border-blue-100 px-2 py-0.5 text-gray-600">{s}</span>
                            ))}
                        </div>
                    ))}
                </div>
            )}
            <div className="col-span-2">
                <div className="font-medium text-gray-500 mb-1">Flows</div>
                {draft.flows.map((f, i) => (
                    <div key={i} className="flex items-center gap-1 text-gray-600">
                        <ArrowRight size={10} className="text-blue-400 shrink-0" />
                        {f}
                    </div>
                ))}
            </div>
            <div className="col-span-2">
                <div className="font-medium text-gray-500 mb-1">UI Suggestions</div>
                {draft.ui_suggestions.map((s, i) => (
                    <div key={i} className="text-gray-600">• {s}</div>
                ))}
            </div>
        </div>
    </div>
);

// ── Page preview panel ───────────────────────────────────────────────────────

const PagePreviewPanel: React.FC<{ design: UIDesign; uxDraft?: UXDraft | null }> = ({ design, uxDraft }) => {
    const previews = design.page_previews;
    const actorHtmlMap = design.actor_base_html ?? {};
    const actorScreens = uxDraft?.actor_screens ?? {};
    const actors = Object.keys(actorHtmlMap).length > 0 ? Object.keys(actorHtmlMap) : Object.keys(actorScreens);
    const hasActors = actors.length > 0;

    if (!previews || Object.keys(previews).length === 0) return null;

    const allPages = Object.keys(previews);
    const [activeActor, setActiveActor] = useState<string>(hasActors ? actors[0] : "");

    // When an actor is selected, filter to their screens; otherwise show all
    const visiblePages = hasActors && activeActor && actorScreens[activeActor]
        ? allPages.filter((p) =>
            actorScreens[activeActor].some((s) => s.toLowerCase() === p.toLowerCase())
        )
        : allPages;

    const [activePage, setActivePage] = useState<string>(allPages[0]);
    // Reset page selection when actor changes
    const currentPage = visiblePages.includes(activePage) ? activePage : (visiblePages[0] ?? allPages[0]);

    // For the iframe: use the actor-specific base.html style if available, else use style_css alone
    const actorStyleHtml = hasActors && activeActor && actorHtmlMap[activeActor]
        ? `<!-- actor nav context: ${activeActor} -->`
        : "";
    const srcdoc = `<style>${design.style_css}</style>${actorStyleHtml}<body style="margin:0;padding:16px;background:#fff">${previews[currentPage] ?? ""}</body>`;

    return (
        <div className="rounded-md border border-gray-200 bg-white flex flex-col overflow-hidden">
            {/* Actor tab bar (only shown when multiple actors exist) */}
            {hasActors && (
                <div className="flex overflow-x-auto border-b border-gray-300 bg-gray-100">
                    <span className="px-2 py-1.5 text-xs text-gray-400 font-medium self-center shrink-0">Actor:</span>
                    {actors.map((a) => (
                        <button
                            key={a}
                            onClick={() => setActiveActor(a)}
                            className={`px-3 py-1.5 text-xs whitespace-nowrap border-r border-gray-300 transition-colors ${
                                activeActor === a
                                    ? "bg-white font-semibold text-indigo-700 border-b-2 border-b-indigo-500"
                                    : "text-gray-500 hover:bg-gray-50"
                            }`}
                        >
                            {a}
                        </button>
                    ))}
                </div>
            )}
            {/* Page tab bar */}
            <div className="flex overflow-x-auto border-b border-gray-200 bg-gray-50">
                {visiblePages.map((p) => (
                    <button
                        key={p}
                        onClick={() => setActivePage(p)}
                        className={`px-3 py-1.5 text-xs whitespace-nowrap border-r border-gray-200 transition-colors ${
                            currentPage === p
                                ? "bg-white font-semibold text-gray-800 border-b-2 border-b-blue-500"
                                : "text-gray-500 hover:bg-gray-100"
                        }`}
                    >
                        {p}
                    </button>
                ))}
            </div>
            {/* Preview iframe */}
            <iframe
                key={`${activeActor}__${currentPage}`}
                sandbox="allow-same-origin"
                srcDoc={srcdoc}
                style={{ width: "100%", height: 380, border: "none" }}
                title={`Preview: ${activeActor ? activeActor + " / " : ""}${currentPage}`}
            />
        </div>
    );
};

// ── UI Designer output panel ─────────────────────────────────────────────────

const UIDesignPanel: React.FC<{ design: UIDesign }> = ({ design }) => {
    const g = design.style_guide;
    const colorEntries = [
        ["primary", g.primary], ["secondary", g.secondary], ["accent", g.accent],
        ["bg", g.background], ["text", g.text_primary],
    ].filter(([, v]) => v);
    return (
        <div className="rounded-md border border-violet-200 bg-violet-50 p-3 text-sm flex flex-col gap-2">
            <div className="flex items-center gap-2 font-semibold text-violet-700">
                <Sparkles size={14} />
                Agent 3 — UI Designer
                <span className="ml-auto text-xs font-normal text-violet-400 italic">{g.mood}</span>
            </div>
            <div className="flex flex-wrap gap-2 items-center">
                {colorEntries.map(([name, hex]) => (
                    <span key={name} className="flex items-center gap-1 text-xs">
                        <span
                            className="inline-block w-3.5 h-3.5 rounded-full border border-gray-200 shadow-sm"
                            style={{ backgroundColor: hex as string }}
                        />
                        <span className="text-gray-500">{name}</span>
                    </span>
                ))}
            </div>
            <div className="grid grid-cols-2 gap-1 text-xs text-gray-600">
                <div><span className="text-gray-400">Heading: </span>{g.font_heading}</div>
                <div><span className="text-gray-400">Body: </span>{g.font_body}</div>
                <div><span className="text-gray-400">Layout: </span>{g.pattern}</div>
                <div><span className="text-gray-400">Stack: </span>{g.ui_kit}</div>
                <div><span className="text-gray-400">Radius: </span>{g.border_radius}</div>
            </div>
        </div>
    );
};

// ── UX Reviewer output panel ──────────────────────────────────────────────────

const UXReviewerPanel: React.FC<{ review: UXReview }> = ({ review }) => (
    <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm flex flex-col gap-2">
        <div className="flex items-center gap-2 font-semibold text-amber-700">
            <AlertTriangle size={14} />
            Agent 2 — UX Reviewer
            <span className="ml-auto text-xs font-normal">
                {review.issues.length} issue{review.issues.length !== 1 ? "s" : ""} found
            </span>
        </div>
        {review.issues.length > 0 ? (
            <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                    <div className="font-medium text-red-500 mb-1">Issues</div>
                    {review.issues.map((issue, i) => (
                        <div key={i} className="text-gray-700">• {issue}</div>
                    ))}
                </div>
                <div>
                    <div className="font-medium text-green-600 mb-1">Improvements</div>
                    {review.improvements.map((imp, i) => (
                        <div key={i} className="text-gray-700 flex items-start gap-1">
                            <CheckCircle size={10} className="text-green-500 shrink-0 mt-0.5" />
                            {imp}
                        </div>
                    ))}
                </div>
            </div>
        ) : (
            <div className="text-xs text-green-700 flex items-center gap-1">
                <CheckCircle size={12} /> No issues found — UX looks complete.
            </div>
        )}
    </div>
);

// ── Screen review table ────────────────────────────────────────────────────────

const ScreenTable: React.FC<{ screens: ScreenInfo[] }> = ({ screens }) => (
    <div className="overflow-x-auto rounded-md border border-gray-200">
        <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
                <tr>
                    <th className="px-3 py-2 text-left font-medium">Page</th>
                    <th className="px-3 py-2 text-left font-medium">Screen type</th>
                    <th className="px-3 py-2 text-left font-medium">Models</th>
                    <th className="px-3 py-2 text-center font-medium">Create</th>
                    <th className="px-3 py-2 text-center font-medium">Update</th>
                    <th className="px-3 py-2 text-center font-medium">Delete</th>
                </tr>
            </thead>
            <tbody>
                {screens.map((s) => (
                    <tr key={s.page_id} className="border-t border-gray-100">
                        <td className="px-3 py-2 font-mono text-gray-800">{s.page_name}</td>
                        <td className="px-3 py-2">
                            <span
                                className={`rounded-full px-2 py-0.5 text-xs font-semibold ${SCREEN_TYPE_COLORS[s.screen_type] ?? "bg-gray-100 text-gray-700"}`}
                            >
                                {s.screen_type}
                            </span>
                        </td>
                        <td className="px-3 py-2 text-gray-500">{s.models.join(", ") || "—"}</td>
                        <td className="px-3 py-2 text-center">{s.has_create ? "✓" : "—"}</td>
                        <td className="px-3 py-2 text-center">{s.has_update ? "✓" : "—"}</td>
                        <td className="px-3 py-2 text-center">{s.has_delete ? "✓" : "—"}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
);

// ── HITL review panel ──────────────────────────────────────────────────────────

const HITLPanel: React.FC<{
    status: PipelineStatus;
    threadId: string;
    onDone: () => void;
}> = ({ status, threadId, onDone }) => {
    const [feedback, setFeedback] = useState("");
    const resume = useResumePipeline(threadId);
    const queryClient = useQueryClient();

    const approve = async () => {
        await resume.mutateAsync({ approved: true, feedback: feedback || undefined });
        queryClient.invalidateQueries({ queryKey: ["pipeline", threadId] });
        onDone();
    };

    const reject = async () => {
        await resume.mutateAsync({ approved: false, feedback: feedback || undefined });
        queryClient.invalidateQueries({ queryKey: ["pipeline", threadId] });
    };

    return (
        <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 text-gray-600 text-sm">
                <MessageSquare size={14} />
                <span>
                    Both agents have completed. Review the outputs below and approve or give feedback.
                </span>
            </div>

            {/* Agent 1: UX Generator */}
            {status.ux_draft && <UXGeneratorPanel draft={status.ux_draft} />}

            {/* Agent 2: UX Reviewer */}
            {status.ux_review && <UXReviewerPanel review={status.ux_review} />}

            {/* Agent 3: UI Designer */}
            {status.ui_design && <UIDesignPanel design={status.ui_design} />}

            {/* Page previews */}
            {status.ui_design?.page_previews && (
                <PagePreviewPanel design={status.ui_design} uxDraft={status.ux_review?.final_version ?? status.ux_draft} />
            )}

            {/* Parsed screens summary */}
            {status.screens.length > 0 && (
                <details className="text-xs">
                    <summary className="cursor-pointer text-gray-500 hover:text-gray-700 mb-1">
                        Parsed screens ({status.screens.length})
                    </summary>
                    <ScreenTable screens={status.screens} />
                </details>
            )}

            <FormControl>
                <FormLabel>Feedback (optional)</FormLabel>
                <Textarea
                    placeholder="e.g. Add a Cancel Order confirmation modal, rename Dashboard to Overview..."
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    minRows={2}
                />
            </FormControl>

            <div className="flex gap-2 justify-end">
                <Button
                    variant="outlined"
                    color="neutral"
                    onClick={reject}
                    loading={resume.isPending}
                >
                    Reject & give feedback
                </Button>
                <Button onClick={approve} loading={resume.isPending} color="success">
                    Approve & generate
                </Button>
            </div>

            {resume.isError && (
                <Typography color="danger" fontSize="sm">
                    {resume.error?.message ?? "Resume failed."}
                </Typography>
            )}
        </div>
    );
};

// ── Main component ─────────────────────────────────────────────────────────────

type Props = {
    open: boolean;
    onClose: () => void;
};

export const PipelinePrototype: React.FC<Props> = ({ open, onClose }) => {
    const { systemId } = useParams();
    const [interfaces] = useSystemInterfaces(systemId);
    const [diagrams] = useSystemDiagrams(systemId);
    const [useAuthentication, setUseAuthentication] = useState(true);
    const [name, setName] = useState("");
    const [nameError, setNameError] = useState<string | null>(null);
    const [threadId, setThreadId] = useState<string | null>(null);
    const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
    const runPipeline = useRunPipeline();
    const queryClient = useQueryClient();

    const reset = () => {
        setThreadId(null);
        setPipelineStatus(null);
        setName("");
        setNameError(null);
        runPipeline.reset();
    };

    const handleClose = () => {
        reset();
        onClose();
    };

    const handleSubmit: React.FormEventHandler<HTMLFormElement> = async (e) => {
        e.preventDefault();
        setNameError(null);

        const trimmed = name.trim();
        if (!/^[a-zA-Z0-9]+$/.test(trimmed)) {
            setNameError("Name may only contain alphanumeric characters.");
            return;
        }

        const metadata = JSON.stringify({
            diagrams,
            interfaces: interfaces.map((i: any) => ({ label: i.name, value: i })),
            useAuthentication,
        });

        const result = await runPipeline.mutateAsync({
            project_name: trimmed,
            application_name: trimmed,
            metadata,
            system_id: systemId ?? "",
            authentication_present: useAuthentication,
        });

        setThreadId(result.thread_id);
        setPipelineStatus(result);
    };

    const handleDone = () => {
        queryClient.invalidateQueries({ queryKey: ["generator", "prototypes", systemId] });
        handleClose();
    };

    const isInterrupted = pipelineStatus?.interrupted && threadId;
    const isRunning = runPipeline.isPending;
    const isSuccess = pipelineStatus?.success;
    const isError = pipelineStatus?.error || runPipeline.isError;

    return (
        <Modal open={open} onClose={handleClose}>
            <ModalDialog sx={{ width: 860, maxHeight: "90vh", overflowY: "auto" }}>
                <div className="flex w-full flex-row justify-between pb-1">
                    <div className="flex flex-col">
                        <h1 className="font-bold">Generate Prototype (Agent Pipeline)</h1>
                        <h3 className="text-sm text-gray-500">
                            Parser → UX Generator → UX Reviewer → Human review → Build
                        </h3>
                    </div>
                    <ModalClose sx={{ position: "relative", top: 0, right: 0 }} />
                </div>
                <Divider />

                {/* Step 1: name + auth form */}
                {!pipelineStatus && (
                    <form onSubmit={handleSubmit} className="flex flex-col gap-3 pt-2">
                        <FormControl error={!!nameError}>
                            <FormLabel>Prototype name</FormLabel>
                            <input
                                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                                placeholder="alphanumeric only"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                            />
                            {nameError && (
                                <Typography fontSize="xs" color="danger">
                                    {nameError}
                                </Typography>
                            )}
                        </FormControl>

                        <FormControl>
                            <FormLabel>Use authentication</FormLabel>
                            <Switch
                                checked={useAuthentication}
                                onChange={(e) => setUseAuthentication(e.target.checked)}
                            />
                        </FormControl>

                        {runPipeline.isError && (
                            <Typography color="danger" fontSize="sm">
                                {(runPipeline.error as Error)?.message ?? "Pipeline start failed."}
                            </Typography>
                        )}

                        <div className="flex justify-end gap-2 pt-1">
                            <Button variant="outlined" color="neutral" onClick={handleClose} type="button">
                                Cancel
                            </Button>
                            <Button type="submit" loading={isRunning}>
                                Run pipeline
                            </Button>
                        </div>
                    </form>
                )}

                {/* Step 2: loading */}
                {isRunning && !pipelineStatus && (
                    <div className="flex flex-col items-center gap-3 py-6">
                        <CircularProgress />
                        <Typography fontSize="sm" textColor="neutral.500">
                            Running UX Generator + Reviewer agents…
                        </Typography>
                    </div>
                )}

                {/* Step 3: HITL review */}
                {isInterrupted && pipelineStatus && threadId && (
                    <div className="pt-2">
                        <HITLPanel
                            status={pipelineStatus}
                            threadId={threadId}
                            onDone={handleDone}
                        />
                    </div>
                )}

                {/* Step 4: success */}
                {isSuccess && (
                    <div className="flex flex-col items-center gap-3 py-6">
                        <Typography color="success" fontWeight="bold">
                            ✓ Prototype generated successfully!
                        </Typography>
                        <Button onClick={handleDone}>Done</Button>
                    </div>
                )}

                {/* Error state */}
                {isError && pipelineStatus?.error && (
                    <div className="flex flex-col items-center gap-3 py-4">
                        <Typography color="danger" fontSize="sm">
                            {pipelineStatus.error}
                        </Typography>
                        <Button variant="outlined" onClick={reset}>
                            Try again
                        </Button>
                    </div>
                )}
            </ModalDialog>
        </Modal>
    );
};

export default PipelinePrototype;
