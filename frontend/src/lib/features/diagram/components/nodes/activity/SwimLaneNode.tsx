import React, { CSSProperties } from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../shared/NodeWrapper";

export const SwimLaneNode: React.FC<NodeProps> = (node) => {
    const swimlaneNodeStyle: CSSProperties = {
        display: 'flex',
        flexDirection: node.data?.vertical ? 'column' : 'row',
        border: '2px solid #000',
        borderRadius: '4px',
        backgroundColor: '#f9f9f9',
        width: node.data?.width ? `${node.data.width}px`: '150px',
        height: node.data?.height ? `${node.data.height}px`: '400px',
    };

    const swimlaneHeaderStyle: CSSProperties = {
        backgroundColor: '#ddd',
        padding: '8px',
        fontWeight: 'bold',
        textAlign: 'center',
        borderBottom: node.data?.vertical ? '2px solid #000' : 'none',
        borderLeft: node.data?.vertical ? 'none': '2px solid #000',
        writingMode: node.data?.vertical ? 'horizontal-tb' : 'vertical-rl' ,
        transform: node.data?.vertical ?  'none': 'rotate(180deg)',
    };

    const swimlaneBodyStyle: CSSProperties = {
        flex: 1,
        padding: '8px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
    };


    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div style={swimlaneNodeStyle}>
                <div style={swimlaneHeaderStyle}>
                    {node.data?.actorNodeName}
                </div>
                <div style={swimlaneBodyStyle}>
                </div>
            </div>
        </NodeWrapper>
    )
}