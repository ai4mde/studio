import {
    useEdgeContextMenu,
    useNodeContextMenu,
    usePaneContextMenu,
    useSelectionContextMenu,
} from "$diagram/stores/contextMenus";
import React from "react";
import { createPortal } from "react-dom";
import EdgeContextMenu from "../EdgeContextMenu/EdgeContextMenu";
import NodeContextMenu from "../NodeContextMenu/NodeContextMenu";
import PaneContextMenu from "../PaneContextMenu/PaneContextMenu";
import SelectionContextMenu from "../SelectionContextMenu/SelectionContextMenu";

const ContextMenus: React.FC = () => {
    const paneContextMenu = usePaneContextMenu();
    const nodeContextMenu = useNodeContextMenu();
    const selectionContextMenu = useSelectionContextMenu();
    const edgeContextMenu = useEdgeContextMenu();

    return createPortal(
        <>
            {paneContextMenu.active && <PaneContextMenu />}
            {nodeContextMenu.active && <NodeContextMenu />}
            {selectionContextMenu.active && <SelectionContextMenu />}
            {edgeContextMenu.active && <EdgeContextMenu />}
        </>,
        document.body
    );
};

export default ContextMenus;
