import { MouseEvent } from "react";
import { useSelectionContextMenu } from "../stores/contextMenus";
import { useDiagramStore } from "../stores/diagramState";
import { closeAll } from "./shared";

export const onSelectionContextMenu = (event: MouseEvent) => {
    const { nodes, edges } = useDiagramStore.getState();
    event.preventDefault();
    closeAll();
    useSelectionContextMenu
        .getState()
        .open(event.clientX, event.clientY, nodes, edges);
};
