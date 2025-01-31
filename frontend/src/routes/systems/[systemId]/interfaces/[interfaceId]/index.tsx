import SystemLayout from "$browser/components/systems/SystemLayout";
import ShowInterface from "lib/features/interfaces/components/ShowInterface";
import React from "react";
import { useParams } from "react-router";

const SystemInterfaces: React.FC = () => {
    const { systemId } = useParams();
    const { interfaceId } = useParams();

    if (!systemId) {
        return <></>;
    }

    if (!interfaceId) {
        return <></>;
    }

    return (
        <SystemLayout>
            <div className="flex h-full w-full flex-col gap-1 p-3">
                <ShowInterface systemId={systemId} app_comp={interfaceId} />
            </div>
        </SystemLayout>
    );
};

export default SystemInterfaces;

