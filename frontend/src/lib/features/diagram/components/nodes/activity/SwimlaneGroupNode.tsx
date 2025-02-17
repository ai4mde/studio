import React, { CSSProperties } from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../shared/NodeWrapper";

export const SwimlaneGroupNode: React.FC<NodeProps> = (node) => {
    const swimlaneGroupStyle: CSSProperties = {
        display: 'flex',
        flexDirection: node.data?.horizontal ? 'column' : 'row',
        backgroundColor: '#f9f9f9',
        width: node.data?.horizontal ? `${node.data.width}px` : `${node.data.width * node.data.swimlanes.length}px`,
        height: node.data?.horizontal ? `${node.data.height * node.data.swimlanes.length}px` : `${node.data.height}px`,
    };

    const swimlaneStyle = (index: number, total: number): CSSProperties => ({
        display: 'flex',
        flexDirection: node.data?.horizontal ? 'row' : 'column',
        border: '2px solid #000',
        backgroundColor: '#f9f9f9',
        flex: 1,
        borderRight: index === total - 1 || node.data?.horizontal ? '2px solid #000' : 'none',
        borderBottom: index === total - 1 || !node.data?.horizontal ? '2px solid #000' : 'none',
    });

    const swimlaneHeaderStyle: CSSProperties = {
        backgroundColor: '#ddd',
        padding: '8px',
        fontWeight: 'bold',
        textAlign: 'center',
        borderBottom: node.data?.horizontal ? 'none' : '2px solid #000',
        borderLeft: node.data?.horizontal ? '2px solid #000' : 'none',
        writingMode: node.data?.horizontal ? 'vertical-rl': 'horizontal-tb',
        transform: node.data?.horizontal ? 'rotate(180deg)' : 'none',
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
            <div style={swimlaneGroupStyle}>
                {node.data?.swimlanes?.map((swimlane, index) => (
                    <div key={index} style={swimlaneStyle(index, node.data.swimlanes.length)}>
                        <div style={swimlaneHeaderStyle}>
                            {swimlane.actorNodeName}
                        </div>
                        <div style={swimlaneBodyStyle}>
                        </div>
                    </div>
                ))}
            </div>
        </NodeWrapper>
    );
};