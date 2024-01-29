import {
    useEdgeContextMenu,
    useNodeContextMenu,
    usePaneContextMenu,
    useSelectionContextMenu,
} from "../stores/contextMenus";

export const closeAll = () => {
    usePaneContextMenu.getState().close();
    useNodeContextMenu.getState().close();
    useSelectionContextMenu.getState().close();
    useEdgeContextMenu.getState().close();
};
