import SystemLayout from "$browser/components/systems/SystemLayout";
import ShowPrototypes from "lib/features/prototypes/components/ShowPrototypes"
import CreatePrototype from "lib/features/prototypes/components/CreatePrototype";
import React from "react";
import { useParams } from "react-router";
import { createPrototypeAtom } from "$lib/features/prototypes/atoms";
import { useAtom } from "jotai";

const SystemInterfaces: React.FC = () => {
    const { systemId } = useParams();
    const [, setCreate] = useAtom(createPrototypeAtom);

    if (!systemId) {
        return <></>;
    }

    return (
        <SystemLayout>
            <CreatePrototype />
            <div className="flex h-full w-full flex-col gap-1 p-3">
                <ShowPrototypes systemId={systemId}/>
                <button
                    onClick={() => setCreate(true)}
                    className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fill items-center justify-center"
                >
                    Generate new prototype
                </button>
            </div>
        </SystemLayout>
    );
};

export default SystemInterfaces;

