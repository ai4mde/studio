import { getEdgeParams } from "$diagram/components/utils";
import { useDiagramStore } from "$diagram/stores";
import React, { useCallback } from "react";
import {
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
  getSmoothStepPath,
  getStraightPath,
  useReactFlow,
  useStore,
} from "reactflow";
import { partialUpdateEdge } from "$diagram/mutations/diagram";

type PositionHandler = {
    x: number;
    y: number;
    active?: boolean;
};

const PositionableEdge: React.FC<EdgeProps> = ({
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
    const { diagram, edges } = useDiagramStore();
    const reactFlowInstance = useReactFlow();
    const positionHandlers = (data?.positionHandlers ?? []) as PositionHandler[];
    const type = data?.type ?? "default";
    const edgeSegmentsCount = positionHandlers.length + 1;
    const edgeSegmentsArray = [];

    let pathFunction;
    switch (type) {
        case "straight":
            pathFunction = getStraightPath;
            break;
        case "smoothstep":
            pathFunction = getSmoothStepPath;
            break;
        default:
            pathFunction = getBezierPath;
    }

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

        const [edgePath, labelX, labelY] = pathFunction({
            sourceX: segmentSourceX,
            sourceY: segmentSourceY,
            targetX: segmentTargetX,
            targetY: segmentTargetY,
        })
        edgeSegmentsArray.push({edgePath, labelX, labelY});
    }

    return (
        <>
      {edgeSegmentsArray.map(({ edgePath }, index) => (
        <path
          key={`edge${id}_segment${index}`}
          id={`${id}_segment${index}`}
          d={edgePath}
          style={style}
          markerEnd={markerEnd}
          markerStart={markerStart}
          className="react-flow__edge-path"
          onClick={(event) => {
            const position = reactFlowInstance.project({
              x: event.clientX,
              y: event.clientY,
            });

            const edge = edges.find((edge) => edge.id === id);
            const newPositionHandlers = [
                ...edge.data.positionHandlers,
                { x: position.x, y: position.y },
            ]
            partialUpdateEdge(diagram, id, {
                rel: {
                    positionHandlers: newPositionHandlers,
                }
            });
          }}
          // Remove this correctly
          onContextMenu={(event) => {
            event.preventDefault();
            const edges = reactFlowInstance.getEdges();
            const newEdges = edges.filter((edge) => edge.id !== id);
            reactFlowInstance.setEdges(newEdges);
          }}
        />
      ))}
      {positionHandlers.map(({ x, y, active }, handlerIndex) => (
        <EdgeLabelRenderer key={`edge${id}_handler${handlerIndex}`}>
          <div
            className="positionHandlerContainer"
            style={{
              transform: `translate(-50%, -50%) translate(${x}px, ${y}px)`,
            }}
          >
            <button
              className={`positionHandler ${active ? "active" : ""}`}
              style={{
                backgroundColor: style?.stroke || "black",
                width: 10,
                height: 10,
                borderRadius: "50%",
                border: "none",
                cursor: "pointer",
              }}
              onMouseDown={() => {
                const edges = reactFlowInstance.getEdges();
                const newEdges = edges.map((edge) => edge);
                const edgeIndex = newEdges.findIndex((edge) => edge.id === id);

                if (newEdges[edgeIndex].data) {
                  (
                    newEdges[edgeIndex].data
                      ?.positionHandlers as Array<PositionHandler>
                  )[handlerIndex].active = true;
                }
                reactFlowInstance.setEdges(newEdges);
              }}
              onContextMenu={(event) => {
                event.preventDefault();
                const edges = reactFlowInstance.getEdges();
                const newEdges = edges.map((edge) => edge);
                const edgeIndex = newEdges.findIndex((edge) => edge.id === id);

                if (newEdges[edgeIndex].data) {
                  (
                    newEdges[edgeIndex].data
                      ?.positionHandlers as Array<PositionHandler>
                  ).splice(handlerIndex, 1);
                }
                reactFlowInstance.setEdges(newEdges);
              }}
            />
          </div>
        </EdgeLabelRenderer>
      ))}
    </>
    );
}