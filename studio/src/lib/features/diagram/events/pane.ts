/* eslint-disable @typescript-eslint/no-unused-vars */
import { Viewport } from "reactflow";
import { usePaneContextMenu } from "../stores/contextMenus";
import { closeAll } from "./shared";

export const onMove = (
    _event: MouseEvent | TouchEvent,
    _viewport: Viewport,
) => {
    closeAll();
};

export const onPaneClick = (_event: React.MouseEvent) => {
    closeAll();
};

export const onPaneContextMenu = (event: React.MouseEvent) => {
    event.preventDefault();
    closeAll();
    usePaneContextMenu.getState().open(event.clientX, event.clientY);
};
