import React from 'react'
import { NodeProps } from 'reactflow'
import NodeWrapper from '../../shared/NodeWrapper'

export const BufferNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="p-4 rounded-md bg-white border border-solid border-black"></div>
        </NodeWrapper>
    )
}
