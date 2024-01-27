import React from 'react'
import { NodeProps } from 'reactflow'
import NodeWrapper from '../../shared/NodeWrapper'

const EnumNode: React.FC<NodeProps> = (node) => {
    return (
        <NodeWrapper node={node} selected={node.selected}>
            <div className="font-mono border border-solid border-black bg-white flex flex-col">
                <div className="flex flex-col items-center gap-1 py-2 px-3">
                    <span className="text-xs">{`<<enumeration>>`}</span>
                    <span className="font-bold">{node.data?.name}</span>
                </div>
                <div className="flex flex-col border-t border-solid border-black p-1">
                    {node.data?.literals?.map((literal: any, idx: number) => (
                        <div
                            key={`literal-${node.id}-${idx}`}
                            className="flex flex-row align-center justify-start p-1 text-sm"
                        >
                            <span>&nbsp;{literal}</span>
                        </div>
                    ))}
                </div>
            </div>
        </NodeWrapper>
    )
}

export default EnumNode
