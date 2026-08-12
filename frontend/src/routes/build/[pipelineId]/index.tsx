import { authAxios } from "$auth/state/auth";
import { HitlCandidateWorkflow } from "$lib/features/ai/components/HitlCandidateWorkflow";
import { AddToDiagram } from "$lib/features/ai/components/AddToDiagram";
import { RunModel } from "$lib/features/ai/components/RunModel";
import { SelectModel } from "$lib/features/ai/components/SelectModel";
import { Steps } from "$lib/features/ai/components/Steps";
import { UploadRequirements } from "$lib/features/ai/components/UploadRequirements";
import { clearHitlPipeline, isHitlPipeline } from "$lib/features/ai/hitlStorage";
import { usePipeline } from "$lib/features/ai/queries";
import { Button, IconButton, LinearProgress } from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, Trash } from "lucide-react";
import React from "react";
import { useNavigate, useParams } from "react-router";

type Props = Record<string, never>;

export const PipelineIndex: React.FC<Props> = () => {
    const { pipelineId } = useParams();
    const { isSuccess, data } = usePipeline(pipelineId);
    const navigate = useNavigate();
    const deletePipeline = useMutation({
        mutationFn: async () => {
            await authAxios.delete(`/v1/prose/pipelines/${pipelineId}/`);
            clearHitlPipeline(pipelineId ?? "");
            navigate("/build/");
        },
    });

    if (!pipelineId) {
        return <></>;
    }

    if (!isSuccess) {
        return <LinearProgress />;
    }

    const hitlWorkflow = isHitlPipeline(data.id);
    const currentStep = hitlWorkflow && data.step >= 3 ? 3 : data.step;

    const workflow = hitlWorkflow ? (
        data.step < 3 ? (
            <UploadRequirements pipeline={data} />
        ) : (
            <HitlCandidateWorkflow pipeline={data} />
        )
    ) : data.step < 3 ? (
        <UploadRequirements pipeline={data} />
    ) : data.step === 3 ? (
        <SelectModel pipeline={data} />
    ) : data.step === 4 ? (
        <RunModel pipeline={data} />
    ) : (
        <AddToDiagram pipeline={data} />
    );

    return (
        <div className="flex h-full w-full flex-col gap-4 p-4">
            <div className="flex w-full flex-row gap-2">
                <IconButton component="a" href="/build/">
                    <ArrowLeft size={16} />
                </IconButton>
                <div className="flex flex-col">
                    <span className="text-2xl font-bold">Build</span>
                    <span className="text-lg">
                        Extract architectural metadata from requirements text
                    </span>
                </div>
                <div className="ml-auto flex items-center">
                    <Button
                        color="danger"
                        className="ml-auto flex flex-row gap-2"
                        size="sm"
                        onClick={() => deletePipeline.mutate()}
                    >
                        <Trash size={16} />
                        <span>Delete Pipeline</span>
                    </Button>
                </div>
            </div>

            <div className="w-full rounded-md bg-gray-100 p-4">
                <div className="p-1">
                    <Steps step={currentStep} variant={hitlWorkflow ? "hitl" : "legacy"} />
                </div>
            </div>
            {workflow}
        </div>
    );
};

export default PipelineIndex;
