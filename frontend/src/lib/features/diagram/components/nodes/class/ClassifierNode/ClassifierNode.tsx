import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../../shared/NodeWrapper";

const ClassifierNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="font-mono border border-solid border-black bg-white flex flex-col">
                <div className="flex flex-col items-center gap-1 py-2 px-3">
                    <span className="text-xs">{`<<${node.data?.type}>>`}</span>
                    <span className="font-bold">{node.data?.name}</span>
                </div>
            </div>
        </NodeWrapper>
    );
};

export default ClassifierNode;
