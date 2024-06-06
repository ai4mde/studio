import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../../shared/NodeWrapper";

const ClassNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="flex flex-col border border-solid border-black bg-white text-center font-mono">
                <span className="px-6 py-2 font-bold">{node.data?.name}</span>
                <div className="flex flex-col border-t border-solid border-black p-1">
                    {node.data?.attributes?.map(
                        (attribute: any, idx: number) => (
                            <div
                                key={`attribute-${node.id}-${idx}`}
                                className="align-center flex flex-row justify-between gap-2 px-1 text-sm"
                            >
                                <span>
                                    {attribute?.derived ? "/" : "+"}
                                    {attribute?.name}
                                </span>
                                <span>: {attribute?.type}</span>
                            </div>
                        ),
                    )}
                </div>
                <div className="flex flex-col border-t border-solid border-black p-1">
                    {node.data?.methods?.map((method: any, idx: number) => (
                        <div
                            key={`method-${node.id}-${idx}`}
                            className="align-center flex flex-row justify-between gap-1 px-1 text-sm"
                        >
                            <span>+{method?.name}()</span>
                            <span>:</span>
                            <span>{method?.type}</span>
                        </div>
                    ))}
                </div>
            </div>
        </NodeWrapper>
    );
};

export default ClassNode;
