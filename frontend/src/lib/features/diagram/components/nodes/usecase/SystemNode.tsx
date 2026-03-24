import { NodeProps } from "reactflow";
import React from "react";
import NodeWrapper from "../shared/NodeWrapper";

export const SystemNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="p-1">{node.id.split("-").slice(-1)}</div>
        </NodeWrapper>
    );
};
