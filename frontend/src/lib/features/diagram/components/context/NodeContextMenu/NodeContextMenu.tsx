import ContextMenu from "$diagram/components/context/ContextMenu/ContextMenu";
import { startManualConnect } from "$diagram/events";
import { useDiagramStore } from "$diagram/stores";
import { useNodeContextMenu } from "$diagram/stores/contextMenus";
import { useEditNodeModal } from "$diagram/stores/modals";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Copy, Edit, GitBranchPlus, Trash, UploadCloud } from "lucide-react";
import React, { MouseEventHandler } from "react";
import { useStoreApi } from "reactflow";

const NodeContextMenu: React.FC = () => {
    const { x, y, node, close } = useNodeContextMenu();
    const { diagram } = useDiagramStore();
    const editNode = useEditNodeModal();
    const { setState, getState } = useStoreApi();

    const onEdit = () => {
        node && editNode.open(node.id);
        close();
    };

    const onRemove = async () => {
        if (node) {
            await authAxios.delete(`/v1/diagram/${diagram}/node/${node.id}/`);
            await queryClient.refetchQueries({
                queryKey: [`diagram`],
            });
            close();
        }
    };

    const onDeleteCompletely = async () => {
        if (node) {
            await authAxios.delete(`/v1/diagram/${diagram}/node/${node.id}/hard/`);
            await queryClient.refetchQueries({
                queryKey: [`diagram`],
            });
            close();
        }
    };

    const onConnect: MouseEventHandler<HTMLButtonElement> = (e) => {
        node && startManualConnect(e, node, getState, setState);
        close();
    };

    return (
        <ContextMenu x={x} y={y}>
            <>
                <li>
                    <button onClick={onEdit}>
                        <span>Edit</span>
                        <Edit size={14} />
                    </button>
                </li>
                <hr className="my-1" />
                <li>
                    <button onClick={onRemove}>
                        <span>Remove from Diagram</span>
                        <Trash size={14} />
                    </button>
                </li>
                <li>
                    <button onClick={onDeleteCompletely}>
                        <span>Delete Completely</span>
                        <Trash size={14} />
                    </button>
                </li>
                <li>
                    <button disabled>
                        <span>Copy</span>
                        <Copy size={14} />
                    </button>
                </li>
                <hr className="my-1" />
                <li>
                    <button onClick={onConnect}>
                        <span>Connect</span>
                        <GitBranchPlus size={14} />
                    </button>
                </li>
                <hr className="my-1" />
                <li>
                    <button>
                        <span>Upload as Component</span>
                        <UploadCloud size={14} />
                    </button>
                </li>
            </>
        </ContextMenu>
    );
};

export default NodeContextMenu;
