import { authAxios } from "$auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import {
    Alert,
    Button,
    Card,
    CircularProgress,
    Divider,
    Modal,
    ModalClose,
    ModalDialog,
    Textarea,
} from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { Check, Expand, RefreshCw, Sparkles } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { clearHitlCandidateSession, loadHitlCandidateSession, saveHitlCandidateSession } from "../hitlStorage";
import {
    HitlCandidate,
    HitlCandidateGenerationResponse,
    HitlNodePositions,
    HitlSelectedCandidateResponse,
    Pipeline,
} from "../types";
import CandidatePreview from "./CandidatePreview";

type Props = {
    pipeline: Pipeline;
    initialCandidateSession?: HitlCandidateGenerationResponse;
};

const candidateLabel = (candidate: HitlCandidate) =>
    `Candidate ${candidate.candidate_index} of ${candidate.candidate_count}`;

export const HitlCandidateWorkflow: React.FC<Props> = ({
    pipeline,
    initialCandidateSession,
}) => {
    const navigate = useNavigate();
    const [candidateSession, setCandidateSession] =
        useState<HitlCandidateGenerationResponse | null>(null);
    const [generationMessage, setGenerationMessage] = useState<string | null>(null);
    const [selectionMessage, setSelectionMessage] = useState<string | null>(null);
    const [previewCandidate, setPreviewCandidate] = useState<HitlCandidate | null>(null);
    const [candidateLayouts, setCandidateLayouts] = useState<
        Record<string, HitlNodePositions>
    >({});

    useEffect(() => {
        setCandidateSession(
            initialCandidateSession ?? loadHitlCandidateSession(pipeline.id),
        );
        setGenerationMessage(null);
        setSelectionMessage(null);
        setPreviewCandidate(null);
        setCandidateLayouts({});
    }, [initialCandidateSession, pipeline.id]);

    const generation = useMutation({
        mutationFn: async () => {
            const response = await authAxios.post<HitlCandidateGenerationResponse>(
                "/v1/generate-model",
                {
                    process_text: pipeline.requirements,
                    mode: "refinement",
                    pipeline_profile: "semantic_deterministic",
                },
            );
            return response.data;
        },
        onSuccess: (payload) => {
            saveHitlCandidateSession(pipeline.id, payload);
            setCandidateSession(payload);
            setGenerationMessage("Three candidates are ready to review.");
            setSelectionMessage(null);
            setPreviewCandidate(null);
            setCandidateLayouts({});
            queryClient.invalidateQueries({ queryKey: ["projects"] });
        },
        onError: () => {
            setGenerationMessage(
                "We could not generate candidates right now. Please try again.",
            );
        },
    });

    const selection = useMutation({
        mutationFn: async ({
            candidateId,
            nodePositions,
        }: {
            candidateId: string;
            nodePositions?: HitlNodePositions;
        }) => {
            const response = await authAxios.post<HitlSelectedCandidateResponse>(
                "/v1/select-candidate",
                {
                    candidate_id: candidateId,
                    node_positions: nodePositions,
                },
            );
            return response.data;
        },
        onSuccess: (payload) => {
            setPreviewCandidate(null);
            clearHitlCandidateSession(pipeline.id);
            setSelectionMessage("Candidate selected. Opening the editor.");
            queryClient.invalidateQueries({ queryKey: ["projects"] });
            queryClient.invalidateQueries({ queryKey: ["systems", payload.project_id] });
            navigate(payload.ui_path ?? `/diagram/${payload.diagram_id}`);
        },
        onMutate: () => {
            setSelectionMessage(null);
        },
        onError: () => {
            setSelectionMessage(
                "We could not select that candidate. Please try again.",
            );
        },
    });

    const actionNames = useMemo(() => {
        if (!candidateSession?.candidates?.length) {
            return new Map<string, string[]>();
        }
        return new Map(
            candidateSession.candidates.map((candidate) => [
                candidate.candidate_id,
                (candidate.activity_graph?.nodes ?? [])
                    .filter((node) => node.type === "action")
                    .map((node) => String(node.name ?? "").trim())
                    .filter(Boolean),
            ]),
        );
    }, [candidateSession]);

    const hasRequirements = Boolean(pipeline.requirements?.trim());

    return (
        <div className="flex flex-col gap-4">
            <Card>
                <div className="flex flex-col gap-3">
                    <div>
                        <h2 className="text-lg font-semibold">Process description</h2>
                        <p className="text-sm text-stone-600">
                            This text is used to generate three activity-diagram candidates.
                        </p>
                    </div>
                    <Textarea
                        minRows={8}
                        value={pipeline.requirements}
                        disabled
                    />
                    <div className="flex flex-row flex-wrap gap-2">
                        <Button
                            color="primary"
                            onClick={() => generation.mutate()}
                            disabled={!hasRequirements || generation.isPending}
                        >
                            {generation.isPending ? (
                                <CircularProgress size="sm" />
                            ) : candidateSession ? (
                                <>
                                    <RefreshCw size={16} />
                                    <span className="pl-2">Generate Again</span>
                                </>
                            ) : (
                                <>
                                    <Sparkles size={16} />
                                    <span className="pl-2">Generate Candidates</span>
                                </>
                            )}
                        </Button>
                    </div>
                    {generationMessage && (
                        <Alert
                            color={generation.isError ? "danger" : "success"}
                            variant="soft"
                        >
                            {generationMessage}
                        </Alert>
                    )}
                </div>
            </Card>

            {candidateSession?.candidates?.length ? (
                <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-1">
                        <h2 className="text-lg font-semibold">Select a candidate</h2>
                        <p className="text-sm text-stone-600">
                            Exactly one candidate will become the official starting model.
                        </p>
                    </div>
                    <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
                        {candidateSession.candidates.map((candidate) => (
                            <Card key={candidate.candidate_id} className="flex flex-col gap-3">
                                <div className="flex items-start justify-between gap-2">
                                    <div>
                                        <div className="text-sm font-semibold text-stone-500">
                                            {candidateLabel(candidate)}
                                        </div>
                                        <div className="text-lg font-semibold">
                                            {candidate.name}
                                        </div>
                                    </div>
                                    <Button
                                        size="sm"
                                        onClick={() =>
                                            selection.mutate({
                                                candidateId: candidate.candidate_id,
                                                nodePositions:
                                                    candidateLayouts[candidate.candidate_id],
                                            })
                                        }
                                        disabled={selection.isPending}
                                    >
                                        {selection.isPending &&
                                        selection.variables?.candidateId ===
                                            candidate.candidate_id ? (
                                            <CircularProgress size="sm" />
                                        ) : (
                                            <>
                                                <Check size={16} />
                                                <span className="pl-2">Select Candidate</span>
                                            </>
                                        )}
                                    </Button>
                                </div>
                                <CandidatePreview candidate={candidate} />
                                <Button
                                    variant="outlined"
                                    color="neutral"
                                    onClick={() => setPreviewCandidate(candidate)}
                                    disabled={selection.isPending}
                                >
                                    <Expand size={16} />
                                    <span className="pl-2">Preview & Arrange</span>
                                </Button>
                                <Divider />
                                <div className="flex flex-col gap-2">
                                    <div className="text-sm font-semibold text-stone-500">
                                        Key actions
                                    </div>
                                    <div className="flex flex-col gap-1 text-sm text-stone-700">
                                        {(actionNames.get(candidate.candidate_id) ?? []).map(
                                            (name) => (
                                                <span key={`${candidate.candidate_id}-${name}`}>
                                                    {name}
                                                </span>
                                            ),
                                        )}
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>
                    {selectionMessage && (
                        <Alert
                            color={selection.isError ? "danger" : "success"}
                            variant="soft"
                        >
                            {selectionMessage}
                        </Alert>
                    )}
                </div>
            ) : null}

            <Modal
                open={previewCandidate !== null}
                onClose={() => {
                    if (!selection.isPending) {
                        setPreviewCandidate(null);
                    }
                }}
            >
                <ModalDialog
                    sx={{
                        width: "min(96vw, 1440px)",
                        maxWidth: "none",
                        height: "92vh",
                        p: 2,
                    }}
                >
                    <ModalClose disabled={selection.isPending} />
                    {previewCandidate ? (
                        <div className="flex h-full min-h-0 flex-col gap-3">
                            <div className="pr-10">
                                <div className="text-sm font-semibold text-stone-500">
                                    {candidateLabel(previewCandidate)}
                                </div>
                                <h2 className="text-xl font-semibold">
                                    Preview & Arrange
                                </h2>
                                <p className="text-sm text-stone-600">
                                    Drag nodes to arrange the visual layout. Pan, zoom, and
                                    fit the view as needed. Process content and connections
                                    cannot be changed here.
                                </p>
                            </div>
                            <CandidatePreview
                                key={previewCandidate.candidate_id}
                                candidate={previewCandidate}
                                className="min-h-0 flex-1"
                                interactive
                                initialPositions={
                                    candidateLayouts[previewCandidate.candidate_id]
                                }
                                onPositionsChange={(positions) =>
                                    setCandidateLayouts((layouts) => ({
                                        ...layouts,
                                        [previewCandidate.candidate_id]: positions,
                                    }))
                                }
                            />
                            {selection.isError && selectionMessage ? (
                                <Alert color="danger" variant="soft">
                                    {selectionMessage}
                                </Alert>
                            ) : null}
                            <div className="flex justify-end gap-2">
                                <Button
                                    variant="outlined"
                                    color="neutral"
                                    onClick={() => setPreviewCandidate(null)}
                                    disabled={selection.isPending}
                                >
                                    Close
                                </Button>
                                <Button
                                    onClick={() =>
                                        selection.mutate({
                                            candidateId: previewCandidate.candidate_id,
                                            nodePositions:
                                                candidateLayouts[
                                                    previewCandidate.candidate_id
                                                ],
                                        })
                                    }
                                    disabled={selection.isPending}
                                >
                                    {selection.isPending ? (
                                        <CircularProgress size="sm" />
                                    ) : (
                                        <>
                                            <Check size={16} />
                                            <span className="pl-2">Select Candidate</span>
                                        </>
                                    )}
                                </Button>
                            </div>
                        </div>
                    ) : null}
                </ModalDialog>
            </Modal>
        </div>
    );
};

export default HitlCandidateWorkflow;
