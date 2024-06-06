import { NodeProps } from "reactflow";
import NodeWrapper from "../shared/NodeWrapper";
import React from "react";

export const ActorNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="flex flex-col gap-1 items-center text-sm">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="40"
                    height="80"
                    viewBox="-1 -1 41 81"
                >
                    <circle
                        cx="20"
                        cy="10"
                        r="10"
                        style={{
                            fill: "none",
                            stroke: "black",
                            strokeWidth: 2,
                        }}
                    />
                    <line
                        x1="0"
                        y1="30"
                        x2="40"
                        y2="30"
                        style={{
                            stroke: "black",
                            strokeWidth: 2,
                        }}
                    />
                    <line
                        x1="20"
                        y1="20"
                        x2="20"
                        y2="50"
                        style={{
                            stroke: "black",
                            strokeWidth: 2,
                        }}
                    />
                    <line
                        x1="20"
                        y1="50"
                        x2="40"
                        y2="80"
                        style={{
                            stroke: "black",
                            strokeWidth: 2,
                        }}
                    />
                    <line
                        x1="20"
                        y1="50"
                        x2="0"
                        y2="80"
                        style={{
                            stroke: "black",
                            strokeWidth: 2,
                        }}
                    />
                </svg>
                <span>{node.data?.name}</span>
            </div>
        </NodeWrapper>
    );
};
