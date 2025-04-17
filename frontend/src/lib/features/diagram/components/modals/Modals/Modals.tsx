import {
    useEditConnectionModal,
    useEditNodeModal,
    useImportNodeModal,
    useNewConnectionModal,
    useNewNodeModal
} from "$diagram/stores/modals";
import React from "react";
import EditConnectionModal from "../EditConnectionModal/EditConnectionModal";
import EditNodeModal from "../EditNodeModal/EditNodeModal";
import { ImportNodeModal } from "../ImportNodeModal/ImportNodeModal";
import NewConnectionModal from "../NewConnectionModal/NewConnectionModal";
import { NewNodeModal } from "../NewNodeModal/NewNodeModal";

export const Modals: React.FC = () => {
    const newNodeModal = useNewNodeModal();
    const importNodeModal = useImportNodeModal();
    const editNodeModal = useEditNodeModal();
    const newConnectionModal = useNewConnectionModal();
    const editConnectionModal = useEditConnectionModal();

    return (
        <>
            {newNodeModal.active && <NewNodeModal />}
            {importNodeModal.active && <ImportNodeModal />}
            {editNodeModal.active && editNodeModal.node && <EditNodeModal />}
            {newConnectionModal.active && <NewConnectionModal />}
            {editConnectionModal.active && <EditConnectionModal />}
            { }
        </>
    );
};

export default Modals;
