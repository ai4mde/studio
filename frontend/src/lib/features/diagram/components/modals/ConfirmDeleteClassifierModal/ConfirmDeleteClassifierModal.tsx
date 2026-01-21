import React from "react";
import { DiagramUsageItem } from "$diagram/types/diagramUsage";
import { ConfirmDeleteModal } from "../ConfirmDeleteModal/ConfirmDeleteModal";
import { DiagramUsageList } from "../ConfirmDeleteModal/DiagramUsageList";

type Props = {
    open: boolean;
    onClose: () => void;
    classifierName: string;
    usages: DiagramUsageItem[];
    onProceed: () => void;
    isDeleting?: boolean;
};

export const ConfirmDeleteClassifierModal: React.FC<Props> = ({
    open,
    onClose,
    classifierName,
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
            <p>This action also deletes the classifier associated to the node {classifierName}.</p>

            {usages.length > 0 && (
                <>
                    <p>Nodes linked to this classifier in the following diagrams will also be deleted:</p>
                    <DiagramUsageList usages={usages} />
                </>
            )}
        </ConfirmDeleteModal>
    );
};
