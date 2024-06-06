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
import React, { useEffect, useState } from "react";
import { SendHorizonal } from "lucide-react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { wsURL } from "$lib/shared/globals";

export const ChatbotWindow: React.FC = () => {
    const [chatbotOpen, setChatbotOpen] = useAtom(chatbotOpenAtom);
    const close = () => setChatbotOpen(false);
    const { sendMessage, lastJsonMessage, readyState } = useWebSocket(
        `${wsURL}/chat/changes/demo`,
    );
    const [messageHistory, setMessageHistory] = useState<any[]>([]);

    useEffect(() => {
        if (lastJsonMessage !== null) {
            setMessageHistory((prev) => prev.concat(lastJsonMessage));
        }
    }, [lastJsonMessage, setMessageHistory]);

    return (
        <Modal open={chatbotOpen} onClose={close} hideBackdrop>
            <ModalDialog>
                <ModalClose />
                <div className="flex w-[33vw] min-w-96 flex-col gap-4 p-4">
                    <div className="flex h-96 flex-col items-center justify-start gap-2 overflow-y-scroll">
                        {readyState != ReadyState.OPEN && <CircularProgress />}
                        {messageHistory.map((message) => {
                            if (message.sent) {
                                return (
                                    <span className="w-[90%] place-self-end rounded-md bg-stone-200 p-2">
                                        {message.message}
                                    </span>
                                );
                            }
                            if (message.message) {
                                return (
                                    <span className="w-[90%] place-self-start rounded-md bg-blue-200 p-2">
                                        {message.message}
                                    </span>
                                );
                            }
                        })}
                    </div>
                    <form
                        onSubmit={(form) => {
                            form.preventDefault();
                            const formData = new FormData(form.currentTarget);
                            sendMessage(formData.get("message") as string);
                            setMessageHistory((prev) =>
                                prev.concat({
                                    sent: true,
                                    message: formData.get("message"),
                                }),
                            );
                            form.currentTarget.reset();
                        }}
                        className="flex flex-row gap-1"
                    >
                        <Input
                            type="text"
                            name="message"
                            size="sm"
                            fullWidth
                            required
                        />
                        <IconButton color="primary" variant="solid">
                            <SendHorizonal size={16} />
                        </IconButton>
                    </form>
                </div>
            </ModalDialog>
        </Modal>
    );
};
