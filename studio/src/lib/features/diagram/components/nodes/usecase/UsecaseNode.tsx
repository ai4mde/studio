import { NodeProps } from 'reactflow'
import React from 'react'
import NodeWrapper from '../shared/NodeWrapper'

export const UsecaseNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div
                style={{
                    borderRadius: '50% / 50%',
                }}
                className="border border-solid border-black bg-white"
            >
                <div className="p-6">{node?.data?.name}</div>
            </div>
        </NodeWrapper>
    )
}
