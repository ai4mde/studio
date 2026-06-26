import React from "react";
import { NodeProps } from "reactflow";

export const FallbackNode: React.FC<NodeProps> = () => {
    return <div className="p-4 bg-white">Node</div>;
};
