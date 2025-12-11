import { getEdgeParams } from "$diagram/components/utils";
import React, { useCallback } from "react";
import { EdgeProps, getStraightPath, useStore } from "reactflow";

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

    const { sx, sy, tx, ty } = getEdgeParams(sourceNode, targetNode);

    const [edgePath] = getStraightPath({
        sourceX: sx,
        sourceY: sy,
        targetX: tx,
        targetY: ty,
    });

    const shift = {
        x: sx < tx ? 18 : -10,
        y: sy < ty ? -10 : 18,
    };

    return (
        <>
            {/* Invisible thick hit area */}
            <path
                id={id + '-hitbox'}
                d={edgePath}
                fill="none"
                stroke="transparent"
                strokeWidth={7}
                className="react-flow__edge-interaction"
            />

            {/* Visible line */}
            <path
                id={id}
                stroke="black" stroke-width="1"
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
        </>
    );
};

export default FloatingEdge;
