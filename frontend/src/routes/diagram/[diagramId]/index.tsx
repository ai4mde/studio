import React from "react";
import Diagram from "$diagram/components/core/Diagram/Diagram";
import HitlPanel from "$diagram/components/hitl/HitlPanel";
import { Navigate, useParams } from "react-router";

export const DiagramPage: React.FC = () => {
    const { diagramId } = useParams();

    if (!diagramId) {
        return <Navigate to="/diagram"></Navigate>;
    }
    return (
        <div className="flex h-full w-full overflow-hidden">
            <div className="min-w-0 flex-1">
                <Diagram diagram={diagramId}></Diagram>
            </div>
            <HitlPanel diagramId={diagramId} />
        </div>
    );
};

export default DiagramPage;
