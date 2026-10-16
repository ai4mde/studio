import { nodeTypes } from "$diagram/components/core/Node/Node";
import { edgeTypes, Markers } from "$diagram/components/edges";
import { Background, Controls, Node, NodeChange, ReactFlow, applyNodeChanges } from "reactflow";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { HitlCandidate, HitlNodePositions } from "../types";

type Props = {
    candidate: HitlCandidate;
    className?: string;
    interactive?: boolean;
    initialPositions?: HitlNodePositions;
    onPositionsChange?: (positions: HitlNodePositions) => void;
};

const nodePositions = (nodes: Node[]): HitlNodePositions =>
    Object.fromEntries(
        nodes.map((node) => [
            node.id,
            {
                x: Math.round(node.position.x),
                y: Math.round(node.position.y),
            },
        ]),
    );

const CandidatePreview: React.FC<Props> = ({
    candidate,
    className = "h-56",
    interactive = false,
    initialPositions,
    onPositionsChange,
}) => {
    const preview = useMemo(() => {
        const exported = Array.isArray(candidate.ai4mde)
            ? candidate.ai4mde[0]
            : candidate.ai4mde;
        const diagram =
            exported?.diagrams?.find((entry: any) => entry?.type === "activity") ??
            exported?.diagrams?.[0];

        if (!exported || !diagram) {
            return { nodes: [], edges: [] };
        }

        const classifiers = new Map<string, Record<string, any>>(
            (exported.classifiers ?? []).map((entry: Record<string, any>) => [
                String(entry.id),
                entry,
            ]),
        );
        const relations = new Map<string, Record<string, any>>(
            (exported.relations ?? []).map((entry: Record<string, any>) => [
                String(entry.id),
                entry,
            ]),
        );

        const swimlaneGroupUUID = (diagram.nodes ?? []).find(
            (node: any) => classifiers.get(String(node.cls))?.data?.type === "swimlanegroup",
        )?.id;
        const nodeIdByClassifierId = new Map<string, string>(
            (diagram.nodes ?? []).map((node: any) => [
                String(node.cls),
                String(node.id),
            ]),
        );

        const nodes = (diagram.nodes ?? []).map((node: any) => {
            const classifier = classifiers.get(String(node.cls));
            const classifierData = classifier?.data ?? {};
            const arrangedPosition = initialPositions?.[String(node.id)];
            return {
                id: String(node.id),
                type: classifierData.type,
                position: arrangedPosition ?? {
                    x: node?.data?.position?.x ?? 0,
                    y: node?.data?.position?.y ?? 0,
                },
                data: {
                    ...classifierData,
                    systemName: exported.name,
                    systemId: exported.id,
                    _preview: true,
                },
                parentNode:
                    classifierData.parentNode ??
                    (classifierData.actorNode ? swimlaneGroupUUID : null),
                extent: classifierData.actorNode ? "parent" : undefined,
                connectable: false,
                deletable: false,
                draggable: interactive,
                selectable: false,
                zIndex:
                    classifierData.type === "swimlanegroup" ||
                    classifierData.type === "system_boundary"
                        ? -1
                        : 1,
            };
        });

        const edges = (diagram.edges ?? []).map((edge: any) => {
            const relation = relations.get(String(edge.rel));
            const relationData = relation?.data ?? {};
            const source = nodeIdByClassifierId.get(String(relation?.source));
            const target = nodeIdByClassifierId.get(String(relation?.target));
            return {
                id: String(edge.id),
                type: "floating",
                markerEnd: `${relationData.type}-end`,
                markerStart: `${relationData.type}-start`,
                source: source ?? String(relation?.source),
                target: target ?? String(relation?.target),
                data: {
                    ...relationData,
                    edge_data: edge?.data ?? {},
                    _preview: true,
                },
                selectable: false,
                focusable: false,
            };
        });

        return { nodes, edges };
    }, [candidate, initialPositions, interactive]);
    const [nodes, setNodes] = useState<Node[]>(preview.nodes);
    const nodesRef = useRef<Node[]>(preview.nodes);

    useEffect(() => {
        nodesRef.current = preview.nodes;
        setNodes(preview.nodes);
    }, [preview.nodes]);

    const handleNodesChange = (changes: NodeChange[]) => {
        setNodes((currentNodes) => {
            const nextNodes = applyNodeChanges(changes, currentNodes);
            nodesRef.current = nextNodes;
            return nextNodes;
        });
    };

    const handleNodeDragStop = (_event: React.MouseEvent, node: Node) => {
        const positions = {
            ...nodePositions(nodesRef.current),
            [node.id]: {
                x: Math.round(node.position.x),
                y: Math.round(node.position.y),
            },
        };
        onPositionsChange?.(positions);
    };

    return (
        <div
            className={`${className} overflow-hidden rounded-md border border-stone-200 bg-white`}
        >
            <Markers />
            <ReactFlow
                nodes={nodes}
                edges={preview.edges}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                fitView
                panOnDrag={interactive}
                zoomOnScroll={interactive}
                zoomOnPinch={interactive}
                zoomOnDoubleClick={interactive}
                elementsSelectable={false}
                nodesConnectable={false}
                nodesDraggable={interactive}
                onNodesChange={interactive ? handleNodesChange : undefined}
                onNodeDragStop={interactive ? handleNodeDragStop : undefined}
                proOptions={{ hideAttribution: true }}
            >
                <Background />
                {interactive ? <Controls showInteractive={false} /> : null}
            </ReactFlow>
        </div>
    );
};

export default CandidatePreview;
