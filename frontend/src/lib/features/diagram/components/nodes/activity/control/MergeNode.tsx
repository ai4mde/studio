import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../../shared/NodeWrapper";

export const MergeNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="p-2">
                <div className="h-14 w-14 aspect-square rotate-45 border border-solid border-black"></div>
            </div>
        </NodeWrapper>
    );
};
