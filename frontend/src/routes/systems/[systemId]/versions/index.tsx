import SystemLayout from "$browser/components/systems/SystemLayout";
import ShowReleases from "lib/features/releases/components/ShowReleases";
import React from "react";
import { useParams } from "react-router";

const SystemInterfaces: React.FC = () => {
    const { systemId } = useParams();

    if (!systemId) {
        return <></>;
    }

    return (
        <SystemLayout>
            <div className="flex h-full w-full flex-col gap-1 p-3">
                <ShowReleases system={systemId} />
            </div>
        </SystemLayout>
    );
};

export default SystemInterfaces;

