import { useDiagramStore } from "$diagram/stores";
import { Tooltip } from "@mui/joy";
import React from "react";
import { Handle, NodeProps, Position } from "reactflow";

const NodeWrapper: React.FC<{
    children: React.ReactNode;
    selected?: boolean;
    node: NodeProps;
}> = ({ node, children, selected }) => {
    const { connecting, projectSettings } = useDiagramStore();

    const nodeName = node.type.charAt(0)?.toUpperCase() + node.type.slice(1);
    
    // Color hierarchy: override > project settings > defaults
    let backgroundColor = "#FFFFFF";
    let textColor = "#000000";
    
    if (node.data?.background_color_hex_override) {
        backgroundColor = node.data.background_color_hex_override;
    } else if (projectSettings?.classifier_colors?.[node.data?.type]) {
        backgroundColor = projectSettings.classifier_colors[node.data.type].background_hex;
    }
    
    if (node.data?.text_color_hex_override) {
        textColor = node.data.text_color_hex_override;
    } else if (projectSettings?.classifier_colors?.[node.data?.type]) {
        textColor = projectSettings.classifier_colors[node.data.type].text_hex;
    }

    if (node.data?._preview) {
        return <div className="relative z-0">{children}</div>;
    }

    return (
        <Tooltip title={`${nodeName}`} variant="soft">
            <div
                className={[
                    "flex p-1.5 z-0 ring-1 ring-transparent hover:ring-blue-200",
                    selected && "ring-blue-400",
                    connecting && "ring-purple-400 bg-purple-400",
                ]
                    .filter(Boolean)
                    .join(" ")}
            >
                <Handle
                    type="source"
                    id="glob"
                    style={{
                        width: "auto",
                        height: "auto",
                        position: "fixed",
                        inset: "0",
                        transform: "none",
                        borderRadius: "none",
                        background: "none",
                        border: "none",
                        zIndex: connecting ? -10 : 0,
                    }}
                    position={Position.Top}
                />
                <Handle
                    type="target"
                    id="glob"
                    style={{
                        width: "auto",
                        height: "auto",
                        position: "fixed",
                        inset: "0",
                        transform: "none",
                        borderRadius: "0",
                        background: "none",
                        border: "none",
                        zIndex: connecting ? 10 : -10,
                    }}
                    position={Position.Top}
                />
                <div 
                    className="relative z-0"
                    style={{ backgroundColor, color: textColor }}
                >
                    {children}
                </div>
            </div>
        </Tooltip>
    );
};

export default NodeWrapper;
