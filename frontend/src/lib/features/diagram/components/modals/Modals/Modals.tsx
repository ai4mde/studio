import {
    useEditConnectionModal,
    useEditNodeModal,
    useImportNodeModal,
    useNewConnectionModal,
    useNewNodeModal,
    useConfirmDeleteClassifierModal,
    useConfirmDeleteRelationModal
} from "$diagram/stores/modals";
import React, { useState } from "react";
import EditConnectionModal from "../EditConnectionModal/EditConnectionModal";
import EditNodeModal from "../EditNodeModal/EditNodeModal";
import { ImportNodeModal } from "../ImportNodeModal/ImportNodeModal";
import NewConnectionModal from "../NewConnectionModal/NewConnectionModal";
import { NewNodeModal } from "../NewNodeModal/NewNodeModal";
import { ConfirmDeleteClassifierModal } from "../ConfirmDeleteClassifierModal/ConfirmDeleteClassifierModal";
import { ConfirmDeleteRelationModal } from "../ConfirmDeleteRelationModal/ConfirmDeleteRelationModal";
import { useDiagramStore } from "$diagram/stores";
import {
    deleteClassifierEverywhere,
    deleteRelationEverywhere,
} from "$diagram/queries/usage";

export const Modals: React.FC = () => {
    const { nodes, edges, systemId } = useDiagramStore();

    const newNodeModal = useNewNodeModal();
    const importNodeModal = useImportNodeModal();
    const editNodeModal = useEditNodeModal();
    const newConnectionModal = useNewConnectionModal();
    const editConnectionModal = useEditConnectionModal();
    const confirmDeleteClassifierModal = useConfirmDeleteClassifierModal();
    const confirmDeleteRelationModal = useConfirmDeleteRelationModal();

    const [ isDeleting, setIsDeleting ] = useState(false);
    const [ isDeletingRelation, setIsDeletingRelation ] = useState(false);

    const onProceedDelete = async () => {
        if (confirmDeleteClassifierModal.nodeId) {
            try {
                setIsDeleting(true);
                const node = nodes.find((n) => n.id === confirmDeleteClassifierModal.nodeId);
                if (node?.data?.classifierId) {
                    await deleteClassifierEverywhere(systemId, node.data.classifierId);
                }
                confirmDeleteClassifierModal.close();
            } finally {
                setIsDeleting(false);
            }
        }
    }

    const onProceedDeleteRelation = async () => {
        if (confirmDeleteRelationModal.edgeId) {
            try {
                setIsDeletingRelation(true);
                const edge = edges.find((e) => e.id === confirmDeleteRelationModal.edgeId);
                if (edge?.data?.relationId) {
                    await deleteRelationEverywhere(systemId, edge.data.relationId);
                }
                confirmDeleteRelationModal.close();
            } finally {
                setIsDeletingRelation(false);
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

            {confirmDeleteRelationModal.active && (
                <ConfirmDeleteRelationModal
                    open={confirmDeleteRelationModal.active}
                    onClose={confirmDeleteRelationModal.close}
                    usages={confirmDeleteRelationModal.usages}
                    onProceed={onProceedDeleteRelation}
                    isDeleting={isDeletingRelation}
                />
            )}
        </>
    );
};

export default Modals;
