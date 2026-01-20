import ContextMenu from "$diagram/components/context/ContextMenu/ContextMenu";
import { startManualConnect } from "$diagram/events";
import { useDiagramStore } from "$diagram/stores";
import { useNodeContextMenu } from "$diagram/stores/contextMenus";
import { useEditNodeModal, useConfirmDeleteClassifierModal } from "$diagram/stores/modals";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Copy, Edit, GitBranchPlus, Trash, UploadCloud } from "lucide-react";
import React, { MouseEventHandler, useState, useEffect } from "react";
import { useStoreApi } from "reactflow";

const NodeContextMenu: React.FC = () => {
    const { x, y, node, close } = useNodeContextMenu();
    const { diagram } = useDiagramStore();
    const { setState, getState } = useStoreApi();

    const [canRemove, setCanRemove] = useState(true);
    const [checkingUsage, setCheckingUsage] = useState(false);

    const editNode = useEditNodeModal();
    const confirmDeleteClassifierModal = useConfirmDeleteClassifierModal();

    useEffect(() => {
        let cancelled = false;

        const run = async () => {
            if (!node) return;
            setCheckingUsage(true);

            try {
                const res = await authAxios.get(`/v1/diagram/${diagram}/node/${node.id}/classifier-usage/`,);
                const usages = res.data?.usages ?? [];
                const allowRemove = usages.length > 0;
                if (!cancelled) setCanRemove(allowRemove);
            } catch {
                if (!cancelled) setCanRemove(true);
            } finally {
                if (!cancelled) setCheckingUsage(false);
            }
        };

        run();
        return () => {
            cancelled = true;
        };
    }, [node?.id, diagram]);

    
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
            const res = await authAxios.get(`/v1/diagram/${diagram}/node/${node.id}/classifier-usage/`);
            confirmDeleteClassifierModal.open({
                nodeId: node.id,
                classifierName: res.data.classifier_name,
                usages: res.data.usages,
            });

            close();
        }
    };

    const onConnect: MouseEventHandler<HTMLButtonElement> = (e) => {
        node && startManualConnect(e, node, getState, setState);
        close();
    };

    return (
        <>
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
        </>
    );
};

export default NodeContextMenu;
