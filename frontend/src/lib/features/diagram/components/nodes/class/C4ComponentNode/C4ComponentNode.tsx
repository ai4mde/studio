import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../../shared/NodeWrapper";
import { useDiagramStore } from "$diagram/stores/diagramState";

const C4ComponentNode: React.FC<NodeProps> = (node) => {
    const diagramSystemId = useDiagramStore((state) => state.systemId);
    const systemId = node.data?.systemId;
    const systemName = node.data?.systemName;

    const norm = (v: unknown) => (v ?? "").toString().toLowerCase();
    const sameSystem = norm(systemId) === norm(diagramSystemId);

    const showSystem =
        !!systemId &&
        !!systemName &&
        !sameSystem;

    return (
        <NodeWrapper node={node} selected={node.selected}>
                    <div className="font-mono border border-solid border-black bg-white flex flex-col">
                        <div className="flex flex-col items-center gap-1 py-2 px-3">
                            <span className="text-xs">{`<<component>>`}</span>
                            <span className="font-bold">{node.data?.name}</span>
                        </div>
                        <div className="flex flex-col border-t border-solid border-black p-1 w-48 items-center justify-center">
                            <span className="text-xs break-words whitespace-normal text-center">{node.data?.label}</span>
                        </div>
                    </div>
                </NodeWrapper>
    );
};

export default C4ComponentNode;
