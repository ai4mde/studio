import React from "react";
import Diagram from "$diagram/components/core/Diagram/Diagram";
import { Navigate, useParams } from "react-router";

export const DiagramPage: React.FC = () => {
    const { diagramId } = useParams();

    if (!diagramId) {
        return <Navigate to="/diagram"></Navigate>;
    }

    return <Diagram diagram={diagramId}></Diagram>;
};

export default DiagramPage;
