import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../../shared/NodeWrapper";

const SignalNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="font-mono border border-solid border-black bg-white flex flex-col">
                <div className="flex flex-col items-center gap-1 py-2 px-3">
                    <span className="text-xs">{`<<signal>>`}</span>
                    <span className="font-bold">{node.data?.name}</span>
                </div>
                {node.data?.attributes?.length > 0 && (
                    <div className="flex flex-col border-t border-solid border-black p-1">
                        {node.data.attributes.map((attribute: any, idx: number) => (
                            <div
                                key={`attribute-${node.id}-${idx}`}
                                className="flex flex-row justify-between gap-2 px-1 text-sm"
                            >
                                <span>
                                    {attribute?.derived ? "/" : "+"}
                                    {attribute?.name}
                                </span>
                                <span>: {attribute?.type}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </NodeWrapper>
    );
};

export default SignalNode;
