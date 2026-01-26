import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../../shared/NodeWrapper";

export const ForkNode: React.FC<NodeProps> = (node) => (
    <NodeWrapper node={node} selected={node.selected}>
        <div
            className="bg-black"
            style={{
                width: node.data.width,
                height: node.data.height,
            }}
        ></div>
    </NodeWrapper>
);
