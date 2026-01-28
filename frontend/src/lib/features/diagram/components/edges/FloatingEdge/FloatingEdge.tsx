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
    const edgeData = (data?.edge_data ?? {}) as any;
    const positionHandlers = (edgeData.position_handlers ?? []) as PositionHandler[];
    const sourceOffset = (edgeData.source_offset ?? { x: 0, y: 0 }) as PositionHandler;
    const targetOffset = (edgeData.target_offset ?? { x: 0, y: 0 }) as PositionHandler;

    const edgeSegmentsCount = positionHandlers.length + 1;
    const edgeSegmentsArray = [];

    const { sx, sy, tx, ty } = getEdgeParams(sourceNode, targetNode);

    const startX = sx + sourceOffset.x;
    const startY = sy + sourceOffset.y;
    const endX = tx + targetOffset.x;
    const endY = ty + targetOffset.y;


    // Generate edge segments
    for (let i = 0; i < edgeSegmentsCount; i++) {
        let segmentSourceX, segmentSourceY, segmentTargetX, segmentTargetY;

        if (i === 0) {
            segmentSourceX = startX;
            segmentSourceY = startY;
        } else {
            const handler = positionHandlers[i - 1];
            segmentSourceX = handler.x;
            segmentSourceY = handler.y;
        }

        if (i === edgeSegmentsCount - 1) {
            segmentTargetX = endX;
            segmentTargetY = endY;
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
        x: startX < endX ? 18 : -10,
        y: startY < endY ? -10 : 18,
    };

    const points = [
        { x: startX, y: startY },
        ...positionHandlers,
        { x: endX, y: endY },
    ]

    // Find longest segment
    let maxLen = -1;
    let labelX = (sx + tx) / 2;
    let labelY = (sy + ty) / 2;

    for (let i = 0; i < points.length - 1; i++) {
        const a = points[i];
        const b = points[i + 1];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const len = Math.hypot(dx, dy);

        if (len > maxLen) {
            maxLen = len;
            labelX = (a.x + b.x) / 2;
            labelY = (a.y + b.y) / 2;
        }
    }

    const midIndex = Math.floor((points.length - 1) / 2);
    const p1 = points[midIndex];
    const p2 = points[midIndex + 1] || points[midIndex];
    const midX = (p1.x + p2.x) / 2;
    const midY = (p1.y + p2.y) / 2;

    const handleEdgeClick = (event: React.MouseEvent<SVGPathElement>) => {
        const position = reactFlowInstance.screenToFlowPosition({
            x: event.clientX,
            y: event.clientY,
        });

        partialUpdateEdge(diagram, id, {
            data: {
                position_handlers: [
                    ...positionHandlers,
                    { x: position.x, y: position.y },
                ],
            },
        });
    };

    const startEndpointDrag =
        (which: "source" | "target") =>
            (event: React.MouseEvent<SVGCircleElement>) => {
                event.preventDefault();
                event.stopPropagation();

                const base = which === "source" ? { x: sx, y: sy } : { x: tx, y: ty };

                const onMouseMove = (moveEvent: MouseEvent) => {
                    const pos = reactFlowInstance.screenToFlowPosition({
                        x: moveEvent.clientX,
                        y: moveEvent.clientY,
                    });

                    const circle = event.target as SVGCircleElement;
                    circle.setAttribute("cx", String(pos.x));
                    circle.setAttribute("cy", String(pos.y));
                };

                const onMouseUp = (upEvent: MouseEvent) => {
                    window.removeEventListener("mousemove", onMouseMove);
                    window.removeEventListener("mouseup", onMouseUp);

                    const pos = reactFlowInstance.screenToFlowPosition({
                        x: upEvent.clientX,
                        y: upEvent.clientY,
                    });

                    const newOffset = { x: pos.x - base.x, y: pos.y - base.y };

                    partialUpdateEdge(diagram, id, {
                        data:
                            which === "source"
                                ? { source_offset: newOffset }
                                : { target_offset: newOffset },
                    });
                };

                window.addEventListener("mousemove", onMouseMove);
                window.addEventListener("mouseup", onMouseUp);
            };


    return (
        <>
            <path
                d={edgePath}
                stroke="transparent"
                strokeWidth={10}
                fill="none"
                style={{ pointerEvents: "stroke" }}
                onClick={handleEdgeClick}
            />

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
            />
            <text
                style={{ userSelect: "none" }}
                textAnchor="middle"
                x={labelX}
                y={labelY}
                fontSize="12"
            >
                {data?.type === "extension" ? "<<extends>>" : data?.type === "inclusion" ? "<<includes>>" : data?.label ?? ""}
            </text>
            {data?.condition && (
                <text
                    style={{ userSelect: "none", fill: "red" }}
                    textAnchor="middle"
                    x={midX}
                    y={midY + 15}
                    fontSize="20"
                >
                    {data.condition.isElse
                        ? "[Else]"
                        : data.condition.aggregator
                            ? `${data.condition.aggregator}(${data.condition.target_class_name}.${data.condition.target_attribute}) ${data.condition.operator} ${data.condition.threshold}`
                            : `${data.condition.target_class_name}.${data.condition.target_attribute} ${data.condition.operator} ${data.condition.threshold}`}
                </text>
            )}
            <text
                style={{ userSelect: "none" }}
                textAnchor="middle"
                x={startX + shift.x}
                y={startY + shift.y}
                fontSize="12"
            >
                {data?.multiplicity?.source ?? ""}
                {data?.type === "objectflow" ? data?.cls : ""}
            </text>
            <text
                style={{ userSelect: "none" }}
                textAnchor="middle"
                x={endX - shift.x}
                y={endY + shift.y}
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
            <circle
                cx={startX}
                cy={startY}
                r={6}
                fill="black"
                style={{ pointerEvents: "auto", cursor: "grab" }}
                onMouseDown={startEndpointDrag("source")}
            />
            <circle
                cx={endX}
                cy={endY}
                r={6}
                fill="black"
                style={{ pointerEvents: "auto", cursor: "grab" }}
                onMouseDown={startEndpointDrag("target")}
            />
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
                                data: {
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
                            data: {
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
