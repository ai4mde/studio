import { chatbotOpenAtom } from "$chatbot/atoms";
import { Modal, ModalClose, ModalDialog } from "@mui/joy";
import { useAtom } from "jotai";
import React from "react";

export const ChatbotWindow: React.FC = () => {
    const [chatbotOpen, setChatbotOpen] = useAtom(chatbotOpenAtom);
    const close = () => setChatbotOpen(false);

    return (
        <Modal open={true} onClose={close} hideBackdrop>
            <ModalDialog>
                <ModalClose />
                <div className="flex flex-col w-96 p-4"></div>
            </ModalDialog>
        </Modal>
    );
};
