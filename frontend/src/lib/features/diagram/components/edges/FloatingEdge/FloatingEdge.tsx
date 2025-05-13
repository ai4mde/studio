import { getEdgeParams } from "$diagram/components/utils";
import { Position } from "postcss";
import React, { useCallback } from "react";
import { EdgeProps, getStraightPath, useStore, useReactFlow } from "reactflow";
import { partialUpdateEdge } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";

type PositionHandler = {
    x: number;
    y: number;
}


const FloatingEdge: React.FC<EdgeProps> = ({
    id,
    source,
    target,
    markerEnd,
    markerStart,
    style,
    data,
}) => {
    const sourceNode = useStore(
        useCallback((store) => store.nodeInternals.get(source), [source]),
    );
    const targetNode = useStore(
        useCallback((store) => store.nodeInternals.get(target), [target]),
    );

    if (!sourceNode || !targetNode) {
        return null;
    }

    const { diagram } = useDiagramStore();
    const reactFlowInstance = useReactFlow();
    const positionHandlers = (data?.position_handlers ?? []) as PositionHandler[];
    const edgeSegmentsCount = positionHandlers.length + 1;
    const edgeSegmentsArray = [];

    const { sx, sy, tx, ty } = getEdgeParams(sourceNode, targetNode);

    // Generate edge segments
    for (let i = 0; i < edgeSegmentsCount; i++) {
        let segmentSourceX, segmentSourceY, segmentTargetX, segmentTargetY;

        if (i === 0) {
            segmentSourceX = sx;
            segmentSourceY = sy;
        } else {
            const handler = positionHandlers[i - 1];
            segmentSourceX = handler.x;
            segmentSourceY = handler.y;
        }

        if (i === edgeSegmentsCount - 1) {
            segmentTargetX = tx;
            segmentTargetY = ty;
        } else {
            const handler = positionHandlers[i];
            segmentTargetX = handler.x;
            segmentTargetY = handler.y;
        }

        const [edgePath] = getStraightPath({
            sourceX: segmentSourceX,
            sourceY: segmentSourceY,
            targetX: segmentTargetX,
            targetY: segmentTargetY,
        });
        edgeSegmentsArray.push(edgePath);
    }

    const edgePath = edgeSegmentsArray.join(" ");

    const shift = {
        x: sx < tx ? 18 : -10,
        y: sy < ty ? -10 : 18,
    };

    return (
        <>
            <path
                id={id}
                stroke="black"
                strokeWidth="1"
                strokeDasharray={
                    data?.type == "dependency" ? "10,10" : undefined
                }
                d={edgePath}
                markerEnd={markerEnd}
                markerStart={markerStart}
                style={style}
                onClick={(event) => {
                    const position = reactFlowInstance.screenToFlowPosition({
                        x: event.clientX,
                        y: event.clientY,
                    });
                    partialUpdateEdge(diagram, id, {
                        rel: {
                            position_handlers: [
                                ...positionHandlers,
                                { x: position.x, y: position.y },
                            ],
                        },
                    });
                }}
            />
            <text
                style={{ userSelect: "none" }}
                textAnchor="middle"
                x={(sx + tx) / 2}
                y={(sy + ty) / 2}
                fontSize="12"
            >
                {data?.type === "extension" ? "<<extends>>" : data?.type === "inclusion" ? "<<includes>>" : data?.label ?? ""}
            </text>
            <text
                style={{ userSelect: "none" }}
                textAnchor="middle"
                x={sx + shift.x}
                y={sy + shift.y}
                fontSize="12"
            >
                {data?.multiplicity?.source ?? ""}
                {data?.type === "objectflow" ? data?.cls : ""}
            </text>
            <text
                style={{ userSelect: "none" }}
                textAnchor="middle"
                x={tx - shift.x}
                y={ty + shift.y}
                fontSize="12"
            >
                {data?.multiplicity?.target ?? ""}
                {data?.type === "objectflow" ? data?.cls : ""}
            </text>
            <text
                style={{ userSelect: "none" }}
                textAnchor="start"
                x={sx + shift.x}
                y={sy - shift.y}
                fontSize="12"
            >
                {data?.labels?.source ?? ""}
            </text>
            <text
                style={{ userSelect: "none" }}
                textAnchor="start"
                x={tx - shift.x}
                y={ty - shift.y}
                fontSize="12"
            >
                {data?.labels?.target ?? ""}
            </text>
            {positionHandlers.map((handler, index) => (
                <circle
                    key={`handler-${id}-${index}`}
                    cx={handler.x}
                    cy={handler.y}
                    r={5}
                    fill="black"
                    style={{ pointerEvents: "auto" }}
                    onMouseDown={(event) => {
                    event.preventDefault();
                    const onMouseMove = (moveEvent: MouseEvent) => {
                        const position = reactFlowInstance.screenToFlowPosition({
                        x: moveEvent.clientX,
                        y: moveEvent.clientY,
                        });
    
                        // Update the handler's position in the array
                        positionHandlers[index] = { x: position.x, y: position.y };
    
                        // Update the edge with the new position
                        const circleElement = event.target as SVGCircleElement;
                        circleElement.setAttribute("cx", position.x.toString());
                        circleElement.setAttribute("cy", position.y.toString());
                    }
    
                    const onMouseUp = () => {
                        // Remove event listeners when the mouse is released
                        window.removeEventListener("mousemove", onMouseMove);
                        window.removeEventListener("mouseup", onMouseUp);
    
                        // Update the edge with the new position
                        partialUpdateEdge(diagram, id, {
                        rel: {
                            position_handlers: positionHandlers,
                        },
                        });
                    };
    
                    // Attach event listeners for dragging
                    window.addEventListener("mousemove", onMouseMove);
                    window.addEventListener("mouseup", onMouseUp);
                    }}
                    onContextMenu={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    const updatedPositionHandlers = positionHandlers.filter((_, i) => i !== index);
                    partialUpdateEdge(diagram, id, {
                        rel: {
                        position_handlers: updatedPositionHandlers,
                        },
                    });
                    }}
                />
            ))}
        </>
    );
};

export default FloatingEdge;
