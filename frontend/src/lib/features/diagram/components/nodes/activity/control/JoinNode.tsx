import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../../shared/NodeWrapper";

export const JoinNode: React.FC<NodeProps> = (node) => {
    return (
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
};
