import React from "react";
import { DiagramUsageItem } from "$diagram/types/diagramUsage";
import { ConfirmDeleteModal } from "../ConfirmDeleteModal/ConfirmDeleteModal";
import { DiagramUsageList } from "../ConfirmDeleteModal/DiagramUsageList";

type Props = {
    open: boolean;
    onClose: () => void;
    usages: DiagramUsageItem[];
    onProceed: () => void;
    isDeleting?: boolean;
};

export const ConfirmDeleteRelationModal: React.FC<Props> = ({
    open,
    onClose,
    usages,
    onProceed,
    isDeleting = false,
}) => {
    return (
        <ConfirmDeleteModal
            open={open}
            onClose={onClose}
            onProceed={onProceed}
            isDeleting={isDeleting}
        >
            <p>This action also deletes the relation associated to this edge.</p>

            {usages.length > 0 && (
                <>
                    <p>Edges referring to this relation in the following diagrams will also be deleted:</p>
                    <DiagramUsageList usages={usages} />
                </>
            )}
        </ConfirmDeleteModal>
    );
};
