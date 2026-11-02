import { useDiagramStore } from "$diagram/stores";
import { useEdgeContextMenu } from "$diagram/stores/contextMenus";
import { useEditConnectionModal, useConfirmDeleteRelationModal } from "$diagram/stores/modals";
import { deleteEdge } from "$diagram/mutations/diagram";
import { getRelationUsage } from "$diagram/queries/usage";
import { Edit, Trash } from "lucide-react";
import React, { useState, useEffect } from "react";
import ContextMenu from "$diagram/components/context/ContextMenu/ContextMenu";

const EdgeContextMenu: React.FC = () => {
    const { x, y, edge, close } = useEdgeContextMenu();
    const { diagram, systemId, systemName } = useDiagramStore();

    const [canRemove, setCanRemove] = useState(false);
    const [checkingUsage, setCheckingUsage] = useState(false);

    const editEdge = useEditConnectionModal();
    const confirmDeleteRelationModal = useConfirmDeleteRelationModal();

    useEffect(() => {
        let cancelled = false;

        const run = async () => {
            if (!edge || !systemId) return;
            setCheckingUsage(true);
            setCanRemove(false);

            try {
                const usages = await getRelationUsage(
                    systemId,
                    systemName,
                    diagram,
                    edge.data?.relationId,
                );
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
    }, [edge?.id, diagram, systemId]);

    const onEdit = () => {
        edge && editEdge.open(edge.id);
        close();
    };

    const onRemove = async () => {
        if (edge) {
            await deleteEdge(diagram, edge.id);
            close();
        }
    };

    const onDeleteCompletely = async () => {
        if (edge) {
            const usages = await getRelationUsage(
                systemId,
                systemName,
                diagram,
                edge.data?.relationId,
            );
            confirmDeleteRelationModal.open({
                edgeId: edge.id,
                usages,
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
