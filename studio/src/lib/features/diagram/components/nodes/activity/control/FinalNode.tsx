import React from 'react'
import { NodeProps } from 'reactflow'
import NodeWrapper from '../../shared/NodeWrapper'

export const FinalNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="h-14 w-14 bg-black rounded-full p-1">
                <div className="w-full h-full bg-black border-[.3rem] border-solid border-white rounded-full"></div>
            </div>
        </NodeWrapper>
    )
}
