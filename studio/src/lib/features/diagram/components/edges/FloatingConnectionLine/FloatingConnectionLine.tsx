import { getEdgeParams } from "$diagram/components/utils";
import { ConnectionLineComponent, getStraightPath } from "reactflow";
import style from "./floatingconnectionline.module.css";

const FloatingConnectionLine: ConnectionLineComponent = ({
    toX,
    toY,
    fromNode,
}) => {
    if (!fromNode) {
        return null;
    }

    const toNode = {
        id: "",
        data: {},
        width: 1,
        height: 1,
        position: {
            x: toX,
            y: toY,
        },
    };

    const { sx, sy, tx, ty } = getEdgeParams(fromNode, toNode);

    const [edgePath] = getStraightPath({
        sourceX: sx,
        sourceY: sy,
        targetX: tx,
        targetY: ty,
    });

    return (
        <g>
            <path
                fill="none"
                stroke="#222"
                strokeWidth={1.5}
                className={style.backdrop}
                d={edgePath}
            />
            <circle
                cx={toX}
                cy={toY}
                fill="#fff"
                r={3}
                stroke="#222"
                strokeWidth={1.5}
            />
        </g>
    );
};

export default FloatingConnectionLine;
