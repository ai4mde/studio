import { authAxios } from "$auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import {
    Alert,
    Button,
    Card,
    CircularProgress,
    FormControl,
    FormHelperText,
    FormLabel,
    Textarea,
} from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import React, { useRef, useState } from "react";
import { useNavigate } from "react-router";
import { markHitlPipeline, saveHitlCandidateSession } from "../hitlStorage";
import { HitlCandidateGenerationResponse, Pipeline } from "../types";
import HitlCandidateWorkflow from "./HitlCandidateWorkflow";

export const InitialGenerationFlow: React.FC = () => {
    const navigate = useNavigate();
    const [requirements, setRequirements] = useState("");
    const preparedPipeline = useRef<Pipeline | null>(null);
    const [workflow, setWorkflow] = useState<{
        pipeline: Pipeline;
        candidates: HitlCandidateGenerationResponse;
    } | null>(null);
    const [statusMessage, setStatusMessage] = useState<{
        tone: "danger" | "success";
        message: string;
    } | null>(null);

    const startGeneration = useMutation({
        mutationFn: async (processText: string) => {
            const createResponse = preparedPipeline.current
                ? null
                : await authAxios.post<Pipeline>("/v1/prose/pipelines/");
            const pipeline = preparedPipeline.current ?? createResponse!.data;
            preparedPipeline.current = pipeline;
            markHitlPipeline(pipeline.id);
            const requirementsResponse = await authAxios.post<Pipeline>(
                `/v1/prose/pipelines/${pipeline.id}/requirements/`,
                { requirements: processText },
            );
            preparedPipeline.current = requirementsResponse.data;
            const candidatesResponse =
                await authAxios.post<HitlCandidateGenerationResponse>(
                    "/v1/generate-model",
                    {
                        process_text: processText,
                        mode: "refinement",
                        pipeline_profile: "semantic_deterministic",
                    },
                );
            return {
                pipeline: requirementsResponse.data,
                candidates: candidatesResponse.data,
            };
        },
        onSuccess: ({ pipeline, candidates }) => {
            saveHitlCandidateSession(pipeline.id, candidates);
            setWorkflow({ pipeline, candidates });
            setStatusMessage(null);
            queryClient.invalidateQueries({ queryKey: ["pipelines"] });
            navigate(`/process-generation/${pipeline.id}`, { replace: true });
        },
        onError: () => {
            setStatusMessage({
                tone: "danger",
                message:
                        "We could not generate candidates right now. Your process description is ready to retry.",
            });
        },
    });

    if (workflow) {
        return (
            <HitlCandidateWorkflow
                pipeline={workflow.pipeline}
                initialCandidateSession={workflow.candidates}
            />
        );
    }

    return (
        <div className="flex flex-col gap-4">
            <Card>
                <form
                    className="flex flex-col gap-3"
                    onSubmit={(event) => {
                        event.preventDefault();
                        const trimmed = requirements.trim();
                        if (!trimmed) {
                            return;
                        }
                        setStatusMessage(null);
                        startGeneration.mutate(trimmed);
                    }}
                >
                    <div className="flex flex-col gap-1">
                        <h2 className="text-lg font-semibold">Process Description</h2>
                        <p className="text-sm text-stone-600">
                            Enter the business process description to generate three
                            candidate activity diagrams.
                        </p>
                    </div>
                    <FormControl>
                        <FormLabel>Process Description</FormLabel>
                        <Textarea
                            minRows={12}
                            name="requirements"
                            placeholder="Describe the process step by step..."
                            required
                            value={requirements}
                            onChange={(event) => setRequirements(event.target.value)}
                        />
                        <FormHelperText>
                            Paste the original process text here.
                        </FormHelperText>
                    </FormControl>
                    <div className="flex flex-row gap-2">
                        <Button
                            type="submit"
                            color="primary"
                            disabled={!requirements.trim() || startGeneration.isPending}
                        >
                            {startGeneration.isPending ? (
                                <CircularProgress size="sm" />
                            ) : (
                                <>
                                    <Sparkles size={16} />
                                    <span className="pl-2">Generate Candidates</span>
                                </>
                            )}
                        </Button>
                    </div>
                    {statusMessage ? (
                        <Alert color={statusMessage.tone} variant="soft">
                            {statusMessage.message}
                        </Alert>
                    ) : null}
                </form>
            </Card>
        </div>
    );
};

export default InitialGenerationFlow;
