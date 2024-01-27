import React from 'react'
import { NodeProps } from 'reactflow'
import NodeWrapper from '../../shared/NodeWrapper'

export const ForkNode: React.FC<NodeProps> = (node) => (
    <NodeWrapper node={node} selected={node.selected}>
        <div className="h-14 w-2 bg-black"></div>
    </NodeWrapper>
)
