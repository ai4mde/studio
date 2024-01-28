import { chatbotOpenAtom } from "$chatbot/atoms";
import {
    CircularProgress,
    IconButton,
    Modal,
    ModalClose,
    ModalDialog,
} from "@mui/joy";
import { useAtom } from "jotai";
import { Input } from "@mui/joy";
import React from "react";
import { SendHorizonal } from "lucide-react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { wsURL } from "$lib/shared/globals";

export const ChatbotWindow: React.FC = () => {
    const [chatbotOpen, setChatbotOpen] = useAtom(chatbotOpenAtom);
    const close = () => setChatbotOpen(false);
    const { sendMessage, lastMessage, readyState } = useWebSocket(
        `${wsURL}/chat/changes/demo`,
    );

    return (
        <Modal open={chatbotOpen} onClose={close} hideBackdrop>
            <ModalDialog>
                <ModalClose />
                <div className="flex w-[33vw] min-w-96 flex-col gap-4 p-4">
                    <div className="flex h-96 flex-col overflow-y-scroll">
                        {readyState != ReadyState.OPEN && <CircularProgress />}
                    </div>
                    <form onSubmit={() => {}} className="flex flex-row gap-1">
                        <Input type="text" size="sm" fullWidth />
                        <IconButton color="primary" variant="solid">
                            <SendHorizonal size={16} />
                        </IconButton>
                    </form>
                </div>
            </ModalDialog>
        </Modal>
    );
};
