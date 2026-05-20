import { NodeProps } from "reactflow";
import NodeWrapper from "../../shared/NodeWrapper";
import React from "react";

export const DecisionNode: React.FC<NodeProps> = (node) => {
    const text = node.data?.name || node.data?.label || "";

    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="p-2">
                <div className="h-14 w-14 aspect-square rotate-45 bg-white border border-solid border-black"></div>
                {text ? (
                    <div className="mt-2 max-w-[180px] rounded bg-white/90 px-2 py-1 text-center text-xs font-medium leading-tight text-black shadow-sm ring-1 ring-black/15">
                        {text}
                    </div>
                ) : null}
            </div>
        </NodeWrapper>
    );
};
