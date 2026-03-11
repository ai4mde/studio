import React from "react";
import { NodeProps } from "reactflow";
import NodeWrapper from "../shared/NodeWrapper";
import { useDiagramStore } from "$diagram/stores/diagramState";

const ComponentNode: React.FC<NodeProps> = (node) => {
  const diagramSystemId = useDiagramStore((state) => state.systemId);
  const systemId = node.data?.systemId;
  const systemName = node.data?.systemName;

  const norm = (v: unknown) => (v ?? "").toString().toLowerCase();
  const sameSystem = norm(systemId) === norm(diagramSystemId);

  const showSystem = !!systemId && !!systemName && !sameSystem;

  return (
    <NodeWrapper node={node} selected={node.selected}>
      <div className="flex flex-col border border-solid border-black bg-white text-center font-mono">
        <div className="flex flex-col items-center gap-1 px-6 py-2">
          <span className="text-xs">{`<<${node.data?.type}>>`}</span>
          <span className="font-bold">
            {node.data?.name}
            {showSystem && (
              <span className="ml-2 rounded-md bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-700">
                {systemName}
              </span>
            )}
          </span>
        </div>

        <div className="flex flex-col border-t border-solid border-black p-1">
          {node.data?.internals?.map((internal: any, idx: number) => (
            <div
              key={`internal-${node.id}-${idx}`}
              className="align-center flex flex-row justify-between gap-2 px-1 text-sm"
            >
              <span>{internal?.name}</span>
              <span>: {internal?.typeName ?? internal?.type ?? ""}</span>
            </div>
          ))}
        </div>
      </div>
    </NodeWrapper>
  );
};

export default ComponentNode;