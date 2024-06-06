import SystemLayout from "$browser/components/systems/SystemLayout";
import { ShowMetadata } from "$metadata/components/ShowMetadata";
import React from "react";
import { useParams } from "react-router";

const SystemMetadata: React.FC = () => {
    const { systemId } = useParams();

    if (!systemId) {
        return <></>;
    }

    return (
        <SystemLayout>
            <div className="flex h-full w-full flex-col gap-1 p-3">
                <ShowMetadata systemId={systemId} />
            </div>
        </SystemLayout>
    );
};

export default SystemMetadata;
