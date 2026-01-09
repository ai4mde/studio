import {
    useEditConnectionModal,
    useEditNodeModal,
    useImportNodeModal,
    useNewConnectionModal,
    useNewNodeModal,
    useConfirmDeleteClassifierModal
} from "$diagram/stores/modals";
import React, { useState } from "react";
import EditConnectionModal from "../EditConnectionModal/EditConnectionModal";
import EditNodeModal from "../EditNodeModal/EditNodeModal";
import { ImportNodeModal } from "../ImportNodeModal/ImportNodeModal";
import NewConnectionModal from "../NewConnectionModal/NewConnectionModal";
import { NewNodeModal } from "../NewNodeModal/NewNodeModal";
import { ConfirmDeleteClassifierModal } from "../ConfirmDeleteClassifierModal/ConfirmDeleteClassifierModal";
import { useDiagramStore } from "$diagram/stores";
import { queryClient } from "$shared/hooks/queryClient";
import { authAxios } from "$lib/features/auth/state/auth";

export const Modals: React.FC = () => {
    const { diagram } = useDiagramStore();

    const newNodeModal = useNewNodeModal();
    const importNodeModal = useImportNodeModal();
    const editNodeModal = useEditNodeModal();
    const newConnectionModal = useNewConnectionModal();
    const editConnectionModal = useEditConnectionModal();
    const confirmDeleteClassifierModal = useConfirmDeleteClassifierModal();

    const [ isDeleting, setIsDeleting ] = useState(false);

    const onProceedDelete = async () => {
        if (confirmDeleteClassifierModal.nodeId) {
            try {
                setIsDeleting(true);
                await authAxios.delete(`/v1/diagram/${diagram}/node/${confirmDeleteClassifierModal.nodeId}/hard/`);
                await queryClient.refetchQueries({
                    queryKey: [`diagram`],
                });
                confirmDeleteClassifierModal.close();
            } finally {
                setIsDeleting(false);
            }
        }
    }

    return (
        <>
            {newNodeModal.active && <NewNodeModal />}
            {importNodeModal.active && <ImportNodeModal />}
            {editNodeModal.active && editNodeModal.node && <EditNodeModal />}
            {newConnectionModal.active && <NewConnectionModal />}
            {editConnectionModal.active && <EditConnectionModal />}

            {confirmDeleteClassifierModal.active && (
                <ConfirmDeleteClassifierModal
                    open={confirmDeleteClassifierModal.active}
                    onClose={confirmDeleteClassifierModal.close}
                    classifierName={confirmDeleteClassifierModal.classifierName}
                    usages={confirmDeleteClassifierModal.usages}
                    onProceed={onProceedDelete}
                    isDeleting={isDeleting}
                />
            )}
        </>
    );
};

export default Modals;
