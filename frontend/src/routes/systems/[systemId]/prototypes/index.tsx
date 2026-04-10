import SystemLayout from "$browser/components/systems/SystemLayout";
import { createPrototypeAtom } from "$lib/features/prototypes/atoms";
import { useAtom } from "jotai";
import CreatePrototype from "lib/features/prototypes/components/CreatePrototype";
import ShowPrototypes from "lib/features/prototypes/components/ShowPrototypes";
import { PipelinePrototype } from "lib/features/prototypes/components/PipelinePrototype";
import React, { useState } from "react";
import { useParams } from "react-router";

const SystemInterfaces: React.FC = () => {
    const { systemId } = useParams();
    const [, setCreate] = useAtom(createPrototypeAtom);
    const [pipelineOpen, setPipelineOpen] = useState(false);

    if (!systemId) {
        return <></>;
    }

    return (
        <SystemLayout>
            <CreatePrototype />
            <PipelinePrototype open={pipelineOpen} onClose={() => setPipelineOpen(false)} />
            <div className="flex h-full w-full flex-col gap-1 p-3">
                <ShowPrototypes />
                <div className="flex flex-col gap-2">
                    <button
                        onClick={() => setPipelineOpen(true)}
                        className="flex flex-col gap-1 p-4 rounded-md bg-blue-50 hover:bg-blue-100 border border-blue-200 items-center justify-center"
                    >
                        <span className="font-semibold text-blue-700">Generate with Agent Pipeline</span>
                        <span className="text-xs text-blue-500">Parser → Screen type → LLM views → Human review → Build</span>
                    </button>
                    <button
                        onClick={() => setCreate(true)}
                        className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fill items-center justify-center"
                    >
                        <span>Generate new prototype (classic)</span>
                    </button>
                </div>
            </div>
        </SystemLayout>
    );
};

export default SystemInterfaces;

