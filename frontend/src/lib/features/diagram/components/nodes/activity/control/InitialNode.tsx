import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../../shared/NodeWrapper";

export const InitialNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="h-14 w-14 aspect-square bg-black rounded-full"></div>
        </NodeWrapper>
    );
};
