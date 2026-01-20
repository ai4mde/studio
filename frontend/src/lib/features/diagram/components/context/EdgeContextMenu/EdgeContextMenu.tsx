import { useDiagramStore } from "$diagram/stores";
import { useEdgeContextMenu } from "$diagram/stores/contextMenus";
import { useEditConnectionModal } from "$diagram/stores/modals";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Edit, Trash } from "lucide-react";
import React from "react";
import ContextMenu from "$diagram/components/context/ContextMenu/ContextMenu";

const EdgeContextMenu: React.FC = () => {
    const { x, y, edge, close } = useEdgeContextMenu();
    const { diagram } = useDiagramStore();
    const editEdge = useEditConnectionModal();

    const onEdit = () => {
        edge && editEdge.open(edge.id);
        close();
    };

    const onRemove = async () => {
        if (edge) {
            await authAxios.delete(`/v1/diagram/${diagram}/edge/${edge.id}/`);
            await queryClient.refetchQueries({ queryKey: ["diagram", diagram] });
            close();
        }
    };

    const onDeleteCompletely = async () => {
        if (edge) {
            await authAxios.delete(`/v1/diagram/${diagram}/edge/${edge.id}/hard/`);
            await queryClient.refetchQueries({ queryKey: ["diagram", diagram] });
            close();
        }
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
                <hr className="my-1" />
                <li>
                    <button onClick={onDeleteCompletely}>
                        <span>Delete Completely</span>
                        <Trash size={14} />
                    </button>
                </li>
            </>
        </ContextMenu>
    );
};

export default EdgeContextMenu;
