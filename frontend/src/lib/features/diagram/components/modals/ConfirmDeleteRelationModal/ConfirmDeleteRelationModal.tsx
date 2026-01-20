import React from "react";
import {Modal, ModalDialog, DialogTitle, DialogContent, DialogActions, Button} from "@mui/joy";
import { DiagramUsageItem } from "$diagram/types/diagramUsage";

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
    isDeleting = false
}) => {
    return (
        <Modal open={open} onClose={(_, reason) => reason !== "backdropClick" && onClose()}>
            <ModalDialog>
                <DialogTitle>Warning</DialogTitle>
                <DialogContent>
                    <p>This action also deletes the relation associated to this edge.</p>

                    {usages.length > 0 && (
                        <>
                            <p>Edges referring to this relation in the following diagams will also be deleted:</p>
                            <ul className="list-disc pl-6 mt-2 space-y-1">
                                {usages.map((u) => (
                                    <li>Diagram {u.diagram_name} in system {u.system_name}.</li>
                                ))}
                            </ul>
                        </>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button
                        variant="plain"
                        onClick={onClose}
                        disabled={isDeleting}
                    >
                        Cancel
                    </Button>
                    <Button
                        color="danger"
                        onClick={onProceed}
                        loading={isDeleting}
                    >
                        Continue
                    </Button>
                </DialogActions>
            </ModalDialog>
        </Modal>
    );
};