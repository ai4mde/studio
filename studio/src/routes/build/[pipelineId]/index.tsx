import { AddToSystem } from "$lib/features/ai/components/AddToSystem";
import { ListPipelines } from "$lib/features/ai/components/ListPipelines";
import { RunModel } from "$lib/features/ai/components/RunModel";
import { SelectModel } from "$lib/features/ai/components/SelectModel";
import { Steps } from "$lib/features/ai/components/Steps";
import { UploadRequirements } from "$lib/features/ai/components/UploadRequirements";
import { usePipeline } from "$lib/features/ai/queries";
import {
    Divider,
    IconButton,
    LinearProgress,
    Step,
    StepIndicator,
    Stepper,
} from "@mui/joy";
import { ArrowLeft, Check, Loader } from "lucide-react";
import React from "react";
import { useParams } from "react-router";

type Props = Record<string, never>;

export const PipelineIndex: React.FC<Props> = () => {
    const { pipelineId } = useParams();
    const { isSuccess, data } = usePipeline(pipelineId);

    if (!pipelineId) {
        return <></>;
    }

    if (!isSuccess) {
        return <LinearProgress />;
    }

    return (
        <div className="flex h-full w-full flex-col gap-4 p-4">
            <div className="flex flex-row gap-2">
                <IconButton component="a" href="/build/">
                    <ArrowLeft size={16} />
                </IconButton>
                <div className="flex flex-col">
                    <span className="text-2xl font-bold">Build</span>
                    <span className="text-lg">
                        Extract architectural metadata from requirements text
                    </span>
                </div>
            </div>

            <div className="w-full rounded-md bg-gray-100 p-4">
                <div className="p-1">
                    <Steps step={data.step} />
                </div>
            </div>
            {data.step < 3 && <UploadRequirements pipeline={data} />}
            {data.step == 3 && <SelectModel pipeline={data} />}
            {data.step == 4 && <RunModel pipeline={data} />}
            {data.step == 5 && <AddToSystem pipeline={data} />}
        </div>
    );
};

export default PipelineIndex;
