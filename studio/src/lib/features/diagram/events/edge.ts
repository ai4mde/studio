import { useEdgeContextMenu } from "$diagram/stores";
import {
    Edge,
    EdgeChange,
    EdgeMouseHandler,
    applyEdgeChanges as flowEdgeChanges,
} from "reactflow";
import { closeAll } from "./shared";

export const applyEdgeChanges = (
    changes: EdgeChange[],
    eds: Edge[],
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _: string,
) => {
    return flowEdgeChanges(changes, eds);
};

export const onEdgeContextMenu: EdgeMouseHandler = (event, edge) => {
    event.preventDefault();
    closeAll();
    useEdgeContextMenu.getState().open(event.clientX, event.clientY, edge);
};
