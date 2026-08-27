import { useSystemRevisions } from "$lib/features/ai/queries";
import { HitlRevision } from "$lib/features/ai/types";
import { runHitlOperation, useHitlOperation } from "$lib/features/ai/hitlOperation";
import { chatbotOpenAtom } from "$lib/features/chatbot/atoms";
import { useDiagram } from "$lib/features/diagram/queries/diagram";
import {
    useEditorPersistence,
    waitForEditorPersistence,
} from "$lib/features/diagram/editorPersistence";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import {
    Accordion,
    AccordionDetails,
    AccordionGroup,
    AccordionSummary,
    Alert,
    Button,
    Card,
    Chip,
    CircularProgress,
    Divider,
    LinearProgress,
    Modal,
    ModalClose,
    ModalDialog,
} from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { useAtom } from "jotai";
import { Bot, History, RefreshCw, RotateCcw } from "lucide-react";
import React, { useMemo, useState } from "react";

type Props = {
    diagramId: string;
};

const revisionOriginLabel: Record<string, string> = {
    baseline: "Baseline",
    human_sync: "Human Sync",
    ai_refinement: "AI Refinement",
};

const formatTimestamp = (value?: string | null) => {
    if (!value) {
        return "Unknown time";
    }
    return new Date(value).toLocaleString();
};

const candidateMeta = (revision: HitlRevision) => {
    if (
        revision.candidate_index === null ||
        revision.candidate_index === undefined ||
        revision.candidate_count === null ||
        revision.candidate_count === undefined
    ) {
        return null;
    }
    return `Candidate ${revision.candidate_index} of ${revision.candidate_count}`;
};

export const HitlPanel: React.FC<Props> = ({ diagramId }) => {
    const [, setChatbotOpen] = useAtom(chatbotOpenAtom);
    const { data: diagramData, isSuccess: hasDiagramData } = useDiagram(diagramId);
    const systemId = diagramData?.system_id;
    const revisions = useSystemRevisions(systemId);
    const [feedback, setFeedback] = useState<{
        tone: "success" | "danger";
        message: string;
    } | null>(null);
    const [revisionToRestore, setRevisionToRestore] = useState<HitlRevision | null>(null);
    const activeOperation = useHitlOperation((state) => state.activeOperation);
    const pendingEditorSaves = useEditorPersistence(
        (state) => state.pendingByDiagram[diagramId] ?? 0,
    );
    const editorSaveFailures = useEditorPersistence((state) => state.failures);
    const hasEditorSaveFailure = Object.values(editorSaveFailures).some(
        (failure) => failure.diagramId === diagramId,
    );
    const revisionOperationPending = activeOperation !== null;

    const currentRevision = useMemo(
        () => revisions.data?.revisions.find((revision) => revision.is_current) ?? null,
        [revisions.data],
    );

    const syncMutation = useMutation({
        mutationFn: async () => {
            await runHitlOperation("sync", async () => {
                await waitForEditorPersistence(diagramId);
                await authAxios.post("/v1/synchronize-human-edit", {
                    system_id: systemId,
                });
            });
        },
        onSuccess: async () => {
            setFeedback({
                tone: "success",
                message: "Manual changes synced successfully.",
            });
            await Promise.all([
                queryClient.invalidateQueries({ queryKey: ["diagram", diagramId] }),
                queryClient.invalidateQueries({
                    queryKey: ["system-revisions", systemId],
                }),
                queryClient.invalidateQueries({ queryKey: ["system", `${systemId}`] }),
            ]);
        },
        onError: () => {
            setFeedback({
                tone: "danger",
                message: hasEditorSaveFailure
                    ? "A recent editor change was not saved. Retry that edit before syncing with AI."
                    : "We could not sync the current manual changes. Please review the diagram and try again.",
            });
        },
    });

    const restoreMutation = useMutation({
        mutationFn: async (revisionId: string) => {
            await runHitlOperation("restore", async () => {
                await authAxios.post("/v1/restore-revision", {
                    system_id: systemId,
                    revision_id: revisionId,
                });
            });
        },
        onSuccess: async () => {
            setRevisionToRestore(null);
            setFeedback({
                tone: "success",
                message: "Revision restored successfully.",
            });
            await Promise.all([
                queryClient.invalidateQueries({ queryKey: ["diagram", diagramId] }),
                queryClient.invalidateQueries({
                    queryKey: ["system-revisions", systemId],
                }),
                queryClient.invalidateQueries({ queryKey: ["system", `${systemId}`] }),
            ]);
        },
        onError: () => {
            setRevisionToRestore(null);
            setFeedback({
                tone: "danger",
                message: "We could not restore that revision. Please try again.",
            });
        },
    });

    if (!hasDiagramData) {
        return (
            <aside className="h-full w-[22rem] border-l border-stone-200 bg-white">
                <LinearProgress />
            </aside>
        );
    }

    return (
        <>
            <aside className="h-full w-[22rem] shrink-0 overflow-x-hidden overflow-y-auto border-l border-stone-200 bg-white p-3">
                <div className="min-w-0 flex flex-col gap-3">
                    <Card>
                        <div className="min-w-0 flex flex-col gap-3">
                            <div className="flex min-w-0 items-start justify-between gap-2">
                                <div className="min-w-0 flex-1">
                                    <div className="text-sm font-semibold text-stone-500">
                                        HITL Controls
                                    </div>
                                    <div className="break-words text-lg font-semibold">
                                        {diagramData?.name ?? "Activity Diagram"}
                                    </div>
                                </div>
                                {currentRevision ? (
                                    <Chip
                                        className="shrink-0"
                                        size="sm"
                                        color="primary"
                                        variant="soft"
                                    >
                                        Revision {currentRevision.revision_index}
                                    </Chip>
                                ) : null}
                            </div>
                            <div className="flex flex-col gap-2">
                                <Button
                                    className="w-full"
                                    color="primary"
                                    onClick={() => syncMutation.mutate()}
                                    disabled={
                                        !systemId ||
                                        revisionOperationPending ||
                                        pendingEditorSaves > 0 ||
                                        hasEditorSaveFailure
                                    }
                                >
                                    {activeOperation === "sync" ? (
                                        <CircularProgress size="sm" />
                                    ) : (
                                        <>
                                            <RefreshCw size={16} />
                                            <span className="pl-2">Sync with AI</span>
                                        </>
                                    )}
                                </Button>
                                <Button
                                    className="w-full"
                                    variant="outlined"
                                    color="neutral"
                                    onClick={() => setChatbotOpen(true)}
                                    disabled={revisionOperationPending}
                                >
                                    <Bot size={16} />
                                    <span className="pl-2">Open AI Refinement</span>
                                </Button>
                            </div>
                            <div className="text-sm text-stone-600">
                                Use each editor's own save action when it appears. Once your
                                process edits are saved, use Sync with AI before refinement.
                                Layout-only changes do not need to be synced.
                            </div>
                            {pendingEditorSaves > 0 ? (
                                <Alert color="neutral" variant="soft">
                                    Saving the latest editor changes…
                                </Alert>
                            ) : null}
                            {hasEditorSaveFailure ? (
                                <Alert color="danger" variant="soft">
                                    A recent editor change was not saved. Retry that edit
                                    before syncing with AI.
                                </Alert>
                            ) : null}
                            {currentRevision ? (
                                <div className="text-sm text-stone-600">
                                    Current revision:{" "}
                                    {revisionOriginLabel[currentRevision.revision_origin] ??
                                        currentRevision.revision_origin}
                                </div>
                            ) : null}
                            {feedback ? (
                                <Alert color={feedback.tone} variant="soft">
                                    {feedback.message}
                                </Alert>
                            ) : null}
                        </div>
                    </Card>

                    <Card>
                        <AccordionGroup disableDivider>
                            <Accordion>
                                <AccordionSummary>Original Process Text</AccordionSummary>
                                <AccordionDetails>
                                    <div className="max-h-80 overflow-y-auto whitespace-pre-wrap break-words text-sm text-stone-700">
                                        {revisions.data?.process_text?.trim() ||
                                            "Original process text is unavailable."}
                                    </div>
                                </AccordionDetails>
                            </Accordion>
                        </AccordionGroup>
                    </Card>

                    <Card>
                        <div className="min-w-0 flex flex-col gap-3">
                            <div className="flex items-center gap-2">
                                <History size={16} />
                                <div className="text-lg font-semibold">Revision History</div>
                            </div>
                            <Divider />
                            {revisions.isLoading ? (
                                <CircularProgress />
                            ) : revisions.isError ? (
                                <Alert color="danger" variant="soft">
                                    We could not load revision history right now.
                                </Alert>
                            ) : (
                                <div className="flex flex-col gap-3">
                                    {(revisions.data?.revisions ?? [])
                                        .slice()
                                        .sort((a, b) => b.revision_index - a.revision_index)
                                        .map((revision) => (
                                            <div
                                                key={revision.revision_id}
                                                className="min-w-0 rounded-md border border-stone-200 p-3"
                                            >
                                                <div className="flex min-w-0 items-start justify-between gap-2">
                                                    <div className="flex min-w-0 flex-1 flex-col gap-1">
                                                        <div className="break-words font-semibold">
                                                            Revision {revision.revision_index}{" "}
                                                            {"\u2014"}{" "}
                                                            {revisionOriginLabel[
                                                                revision.revision_origin
                                                            ] ?? revision.revision_origin}
                                                        </div>
                                                        <div className="break-words text-xs text-stone-500">
                                                            {formatTimestamp(revision.created_at)}
                                                        </div>
                                                        {revision.refinement_instruction ? (
                                                            <div className="break-words text-sm text-stone-700">
                                                                "{revision.refinement_instruction}"
                                                            </div>
                                                        ) : null}
                                                        {candidateMeta(revision) ? (
                                                            <div className="text-xs text-stone-500">
                                                                {candidateMeta(revision)}
                                                            </div>
                                                        ) : null}
                                                    </div>
                                                    {revision.is_current ? (
                                                        <Chip
                                                            className="shrink-0"
                                                            size="sm"
                                                            color="success"
                                                            variant="soft"
                                                        >
                                                            Current
                                                        </Chip>
                                                    ) : (
                                                        <Button
                                                            className="shrink-0"
                                                            size="sm"
                                                            variant="outlined"
                                                            color="neutral"
                                                            onClick={() =>
                                                                setRevisionToRestore(revision)
                                                            }
                                                            disabled={revisionOperationPending}
                                                        >
                                                            <RotateCcw size={14} />
                                                            <span className="pl-2">Restore</span>
                                                        </Button>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                </div>
                            )}
                        </div>
                    </Card>
                </div>
            </aside>

            <Modal
                open={Boolean(revisionToRestore)}
                onClose={() => {
                    if (activeOperation !== "restore") {
                        setRevisionToRestore(null);
                    }
                }}
            >
                <ModalDialog>
                    <div className="flex w-full flex-row justify-between gap-2">
                        <div className="flex flex-col">
                            <h2 className="font-semibold">
                                Restore Revision {revisionToRestore?.revision_index}?
                            </h2>
                            <p className="text-sm text-stone-600">
                                The current diagram will be replaced by the selected
                                revision.
                            </p>
                        </div>
                        <ModalClose
                            disabled={activeOperation === "restore"}
                            sx={{
                                position: "relative",
                                top: 0,
                                right: 0,
                            }}
                        />
                    </div>
                    <Divider />
                    <div className="flex flex-row gap-3">
                        <Button
                            variant="outlined"
                            color="neutral"
                            onClick={() => setRevisionToRestore(null)}
                            disabled={activeOperation === "restore"}
                        >
                            Cancel
                        </Button>
                        <Button
                            color="primary"
                            onClick={() =>
                                revisionToRestore &&
                                restoreMutation.mutate(revisionToRestore.revision_id)
                            }
                            disabled={revisionOperationPending}
                        >
                            {activeOperation === "restore" ? (
                                <CircularProgress size="sm" />
                            ) : (
                                "Restore"
                            )}
                        </Button>
                    </div>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default HitlPanel;
