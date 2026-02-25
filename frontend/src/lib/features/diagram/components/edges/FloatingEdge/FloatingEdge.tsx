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

    let longestDx = 0;
    let longestDy = 0;

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
            longestDx = dx;
            longestDy = dy;
        }
    }

    const isInterface = data?.type === "interface";
    const gapLen = 22; // Length of the gap for interface edge

    // Ball and socket are placed along the longest segment, so we need the direction of that segment
    const segLen = Math.hypot(longestDx, longestDy);
    const ux = longestDx / segLen;
    const uy = longestDy / segLen;

    // Overall direction from source to targe5t
    const overallDx = endX - startX;
    const overallDy = endY - startY;

    // If the longest segment points "backwards" flip it
    const dot = ux * overallDx + uy * overallDy;
    const dirX = dot >= 0 ? ux : -ux;
    const dirY = dot >= 0 ? uy : -uy;
    const perX = -dirY;
    const perY = dirX;

    // Parameters for the interface symbol
    const ballR = 8;
    const socketR = ballR + 3;
    const symbolGap = 1;

    // Push the ball along the edge direction towards the soource
    const ballCx = labelX - dirX * symbolGap;
    const ballCy = labelY - dirY * symbolGap;

    // Push the socket along the edge direction towards the target
    const socketCx = labelX + dirX * symbolGap;
    const socketCy = labelY + dirY * symbolGap;

    // Calculate the position of the endpoints of the socket circle
    const socketAx = socketCx + perX * socketR;
    const socketAy = socketCy + perY * socketR;
    const socketBx = socketCx - perX * socketR;
    const socketBy = socketCy - perY * socketR;

    // Hide the edge line under the symbol by drawing white lines over it
    const gapX1 = labelX - ux  * (gapLen / 2);
    const gapY1 = labelY - uy  * (gapLen / 2);
    const gapX2 = labelX + ux  * (gapLen / 2);
    const gapY2 = labelY + uy  * (gapLen / 2);

    // Label placement for provided/required itnerface names
    const labelOffsetAlong = 14;
    const labelOffsetPerp = 12;

    // Put both labels on the same side of the edge, depending on the overall direction
    const providedLabelX = ballCx - dirX * labelOffsetAlong + perX * labelOffsetPerp;
    const providedLabelY = ballCy - dirY * labelOffsetAlong + perY * labelOffsetPerp;

    const requiredLabelX = socketCx + dirX * labelOffsetAlong + perX * labelOffsetPerp;
    const requiredLabelY = socketCy + dirY * labelOffsetAlong + perY * labelOffsetPerp;

    // Allign text so it grows away from the symbol
    const providedAnchor: "start" | "end" = dirX > 0 ? "end": "start";
    const requiredAnchor: "start" | "end" = dirX > 0 ? "start": "end";

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

    const socketSweep = (
        cx: number, cy: number,
        ax: number, ay: number,
        bx: number, by: number,
        dirX: number, dirY: number
        ) => {
        // Get correct orientation for the socket arc
        const a = Math.atan2(ay - cy, ax - cx);
        const b = Math.atan2(by - cy, bx - cx);

        const mid = (sweep: 0 | 1) => {
            let d = sweep ? (b - a) : (a - b);
            while (d < 0) d += Math.PI * 2;
            while (d > Math.PI * 2) d -= Math.PI * 2;
            const m = sweep ? (a + d / 2) : (a - d / 2);
            return { x: cx + Math.cos(m), y: cy + Math.sin(m) };
        };

        const m0 = mid(0);
        const m1 = mid(1);

        const dot0 = (m0.x - cx) * dirX + (m0.y - cy) * dirY;
        const dot1 = (m1.x - cx) * dirX + (m1.y - cy) * dirY;

        return (dot1 > dot0 ? 1 : 0) as 0 | 1;
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
                    style={{ userSelect: "none"}}
                    textAnchor="middle"
                    x={midX}
                    y={midY + 18}
                    fontSize="18"
                >
                    {data.condition.isElse
                        ? "[Else]"
                        : data.condition.aggregator
                            ? `[${data.condition.aggregator}(${data.condition.target_class_name}.${data.condition.target_attribute}) ${data.condition.operator} ${data.condition.threshold}]`
                            : `[${data.condition.target_class_name}.${data.condition.target_attribute} ${data.condition.operator} ${data.condition.threshold}]`}
                </text>
            )}
            {data?.guard && String(data.guard).trim() !== "" && !data?.condition && (
                <text
                    style={{ userSelect: "none"}}
                    textAnchor="middle"
                    x={midX}
                    y={midY + 18}
                    fontSize="18"
                >
                    [{String(data.guard).trim()}]
                </text>
            )}
            {isInterface && (() => {
                const sweep = socketSweep(
                    socketCx, socketCy,
                    socketAx, socketAy,
                    socketBx, socketBy,
                    dirX, dirY
                );

                return (
                    <>  
                        {/* Draw a white line to hide the edge under the socket */}
                        <path
                            d={`M ${gapX1} ${gapY1} L ${gapX2} ${gapY2}`}
                            stroke="white"
                            strokeWidth={6}
                            strokeLinecap="round"
                            fill="none"
                            pointerEvents="none"
                        />
                        {/* Provided interface (ball) */}
                        <circle
                            cx={ballCx}
                            cy={ballCy}
                            r={ballR}
                            fill="white"
                            stroke="black"
                            strokeWidth={1.5}
                            pointerEvents="none"
                        />
                        {/* Required interface (socket) */}
                        <path
                            d={`M ${socketAx} ${socketAy} A ${ballR} ${ballR} 0 0 ${sweep} ${socketBx} ${socketBy}`}
                            fill="none"
                            stroke="black"
                            strokeWidth={1.5}
                            strokeLinecap="round"
                            pointerEvents="none"
                        />

                        {/* Labels for the interfaces */}
                        <text
                            x={providedLabelX}
                            y={providedLabelY}
                            textAnchor={providedAnchor}
                            dominantBaseline="middle"
                            fontSize="12"
                            style={{ userSelect: "none" }}
                            pointerEvents="none"
                        >
                            {data.provided_name}
                        </text>
                        <text
                            x={requiredLabelX}
                            y={requiredLabelY}
                            textAnchor={requiredAnchor}
                            dominantBaseline="middle"
                            fontSize="12"
                            style={{ userSelect: "none" }}
                            pointerEvents="none"
                        >
                            {data.required_name}
                        </text>
                    </>
                );
            })()}
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
                r={4}
                fill="black"
                style={{ pointerEvents: "auto", cursor: "grab" }}
                onMouseDown={startEndpointDrag("source")}
            />
            <circle
                cx={endX}
                cy={endY}
                r={4}
                fill="black"
                style={{ pointerEvents: "auto", cursor: "grab" }}
                onMouseDown={startEndpointDrag("target")}
            />
            {positionHandlers.map((handler, index) => (
                <circle
                    key={`handler-${id}-${index}`}
                    cx={handler.x}
                    cy={handler.y}
                    r={4}
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
