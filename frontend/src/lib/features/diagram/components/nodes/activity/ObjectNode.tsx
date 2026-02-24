import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../shared/NodeWrapper";

export const ObjectNode: React.FC<NodeProps> = (node) => {
    const name = node.data?.clsName ?? "Object";
    const state = node.data?.state;

    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="px-4 py-3 bg-white border border-solid border-black text-center min-w-[100px]">
                <div className="font-medium">
                    {name}
                </div>

                {state && (
                    <div className="text-sm text-gray-600 mt-1">
                        [{state}]
                    </div>
                )}
            </div>
        </NodeWrapper>
    );
};
