import { partialUpdateNode } from "$diagram/mutations/diagram";
import {
    Node,
    NodeChange,
    NodeMouseHandler,
    applyNodeChanges as flowNodeChanges,
} from "reactflow";
import { useNodeContextMenu } from "../stores/contextMenus";
import { closeAll } from "./shared";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const onNodeClick: NodeMouseHandler = (event, _) => {
    event.preventDefault();
};

export const onNodeContextMenu: NodeMouseHandler = (event, node) => {
    event.preventDefault();
    closeAll();
    useNodeContextMenu.getState().open(event.clientX, event.clientY, node);
};

export const applyNodeChanges = (
    changes: NodeChange[],
    nds: Node[],
    diagram: string,
) => {
    const _changes = changes.filter((chg) => {
        if (chg.type == "select") {
            return true;
        }

        if (chg.type == "position" && !chg.dragging) {
            const node = nds.find((e) => e.id == chg.id);

            node &&
                partialUpdateNode(diagram, node.id, {
                    data: {
                        position: node.position,
                        background_color_hex: node.data?.background_color_hex,
                        text_color_hex: node.data?.text_color_hex,
                    },
                });
            return false;
        }

        if (chg.type == "remove") {
            // const node = nds.find((e) => e.id == chg.id)
            // useDialogMenu
            //     .getState()
            //     .openDialog(
            //         `Delete node`,
            //         `Are you sure you want to delete node ${node.data.name}?`,
            //         true,
            //         (v) => (v ? deleteNode(diagramURL, node) : null)
            //     )
            return false;
        }
        return true;
    });

    return flowNodeChanges(_changes, nds);
};
