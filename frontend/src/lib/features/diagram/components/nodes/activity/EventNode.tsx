import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../shared/NodeWrapper";

export const EventNode: React.FC<NodeProps> = (node) => {
    const name = node.data?.name ?? "Event";

    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="relative overflow-visible">
                {/* Body */}
                <div className="relative flex items-center justify-center h-10 px-4 pr-7 bg-white border border-solid border-black border-r-0 min-w-[120px]">
                    <div className="text-sm font-medium truncate max-w-[160px]">{name}</div>

                    {/* Triangle tip */}
                    <div
                        className="absolute top-1/2 -right-0 -translate-y-1/2 translate-x-[13px] w-0 h-0"
                        style={{
                            borderTop: "20px solid transparent",
                            borderBottom: "20px solid transparent",
                            borderLeft: "14px solid black", // border outline
                        }}
                    />
                    <div
                        className="absolute top-1/2 -right-0 -translate-y-1/2 translate-x-[12px] w-0 h-0"
                        style={{
                            borderTop: "19px solid transparent",
                            borderBottom: "19px solid transparent",
                            borderLeft: "13px solid white", // fill
                        }}
                    />
                </div>
            </div>
        </NodeWrapper>
    );
};
