import React from "react";
import {
    Modal,
    ModalDialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
} from "@mui/joy";

type Props = {
    open: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
    onProceed: () => void;
    proceedText?: string;
    cancelText?: string;
    isDeleting?: boolean;
};

export const ConfirmDeleteModal: React.FC<Props> = ({
    open,
    onClose,
    title = "Warning",
    children,
    onProceed,
    proceedText = "Continue",
    cancelText = "Cancel",
    isDeleting = false,
}) => {
    return (
        <Modal open={open} onClose={(_, reason) => reason !== "backdropClick" && onClose()}>
            <ModalDialog>
                <DialogTitle>{title}</DialogTitle>
                <DialogContent>{children}</DialogContent>
                <DialogActions>
                    <Button variant="plain" onClick={onClose} disabled={isDeleting}>
                        {cancelText}
                    </Button>
                    <Button color="danger" onClick={onProceed} loading={isDeleting}>
                        {proceedText}
                    </Button>
                </DialogActions>
            </ModalDialog>
        </Modal>
    );
};
