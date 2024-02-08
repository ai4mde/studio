import { ListPipelines } from "$lib/features/ai/components/ListPipelines";
import { Steps } from "$lib/features/ai/components/Steps";
import React from "react";

type Props = Record<string, never>;

export const BuildIndex: React.FC<Props> = () => {
    return (
        <div className="flex h-full w-full flex-col gap-4 p-4">
            <div className="flex flex-col">
                <span className="text-2xl font-bold">Build</span>
                <span className="text-lg">
                    Extract architectural metadata from requirements text
                </span>
            </div>
            <div className="w-full rounded-md bg-gray-100 p-4">
                <div className="p-1">
                    <Steps step={1} />
                </div>
            </div>
            <ListPipelines />
        </div>
    );
};

export default BuildIndex;
