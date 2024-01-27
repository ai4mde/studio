import React from 'react'
import NodeWrapper from '../shared/NodeWrapper'
import { NodeProps } from 'reactflow'

export const ActionNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="p-4 rounded-md text-xl bg-white border border-solid border-black">
                {node.data?.name}
            </div>
        </NodeWrapper>
    )
}
