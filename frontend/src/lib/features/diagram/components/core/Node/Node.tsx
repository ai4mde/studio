import React from "react";
import { NodeProps } from "reactflow";
import { nodeTypes } from "./nodeTypes";

export const Node: React.FC<NodeProps> = () => {
    return <div className="p-4 bg-white">Node</div>;
};

export const PreviewNode: React.FC<NodeProps> = (node) => {
    const Elem = nodeTypes[node.type] ?? Node;
    node.data._preview = true;

    return <Elem {...node} />;
};
