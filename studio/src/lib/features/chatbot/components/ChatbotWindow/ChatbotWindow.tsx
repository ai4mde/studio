import React from "react";
import { chatbotOpen } from "$chatbot/atoms";
import { useAtom } from "jotai";

export const ChatbotWindow: React.FC = () => {
    const [, setChatbotOpen] = useAtom(chatbotOpen)
    const close = () => setChatbotOpen(false)

    return <div className="inset-0">
        <button onClick={close}>Close</button>
    </div>
}