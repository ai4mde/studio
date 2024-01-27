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
        useCallback((store) => store.nodeInternals.get(source), [source])
    );
    const targetNode = useStore(
        useCallback((store) => store.nodeInternals.get(target), [target])
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
            <path
                id={id}
                className="react-flow__edge-path !stroke-black !stroke-2"
                d={edgePath}
                markerEnd={markerEnd}
                markerStart={markerStart}
                style={style}
            />
            <text
                style={{ userSelect: "none" }}
                textAnchor="start"
                x={sx + shift.x}
                y={sy + shift.y}
                fontSize="12"
            >
                {data?.labelFrom ?? ""}
            </text>
            <text
                style={{ userSelect: "none" }}
                textAnchor="start"
                x={tx - shift.x}
                y={ty + shift.y}
                fontSize="12"
            >
                {data?.labelTo ?? ""}
            </text>
        </>
    );
};

export default FloatingEdge;
