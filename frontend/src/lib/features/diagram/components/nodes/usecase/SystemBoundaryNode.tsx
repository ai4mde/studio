import React, { CSSProperties } from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../shared/NodeWrapper";

export const SystemBoundaryNode: React.FC<NodeProps> = (node) => {
    const boundaryStyle: CSSProperties = {
        width: `${node.data?.width}px`,
        height: `${node.data?.height}px`,
        border: "2px solid #000",
        backgroundColor: "#f9f9f9",
        position: "relative",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
    };

    const headerStyle: CSSProperties = {
        padding: "8px",
        fontWeight: "bold",
        fontSize: "24px",
        textAlign: "center",
    };

    const bodyStyle: CSSProperties = {
        flex: 1,
    };

    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div style={boundaryStyle}>
                <div style={headerStyle}>
                    {node.data?.system_name ?? node.data?.name}
                </div>
                <div style={bodyStyle} />
            </div>
        </NodeWrapper>
    );
};
