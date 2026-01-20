import { useDiagramStore } from "$diagram/stores";
import { useEdgeContextMenu } from "$diagram/stores/contextMenus";
import { useEditConnectionModal, useConfirmDeleteRelationModal } from "$diagram/stores/modals";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Edit, Trash } from "lucide-react";
import React, { useState, useEffect } from "react";
import ContextMenu from "$diagram/components/context/ContextMenu/ContextMenu";

const EdgeContextMenu: React.FC = () => {
    const { x, y, edge, close } = useEdgeContextMenu();
    const { diagram } = useDiagramStore();

    const [canRemove, setCanRemove] = useState(false);
    const [checkingUsage, setCheckingUsage] = useState(false);

    const editEdge = useEditConnectionModal();
    const confirmDeleteRelationModal = useConfirmDeleteRelationModal();

    useEffect(() => {
        let cancelled = false;

        const run = async () => {
            if (!edge) return;
            setCheckingUsage(true);
            setCanRemove(false);

            try {
                const res = await authAxios.get(`/v1/diagram/${diagram}/edge/${edge.id}/relation-usage/`,);
                const usages = res.data?.usages ?? [];
                const allowRemove = usages.length > 0;
                if (!cancelled) setCanRemove(allowRemove);
            } catch  (err) {
                console.error("relation-usage failed", err)
                if (!cancelled) setCanRemove(false);
            } finally {
                if (!cancelled) setCheckingUsage (false);
            }
        };

        run();
        return () => {
            cancelled = true;
        };
    }, [edge?.id, diagram]);

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
            const res = await authAxios.get(`/v1/diagram/${diagram}/edge/${edge.id}/relation-usage/`,);
            confirmDeleteRelationModal.open({
                edgeId: edge.id,
                usages: res.data.usages,
            });

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
                    <button 
                        onClick={onRemove}
                        disabled={!canRemove || checkingUsage}
                    >
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
