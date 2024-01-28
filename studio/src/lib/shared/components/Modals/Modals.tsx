import { ChatbotWindow } from "$lib/features/chatbot/components/ChatbotWindow/ChatbotWindow";
import { navigationPortalAtom } from "$shared/hooks/navigationPortal";
import { useAtom } from "jotai";
import React from "react";
import { createPortal } from "react-dom";

const Modals: React.FC = () => {
    const [navigationPortal] = useAtom(navigationPortalAtom);

    return (
        <>
            {navigationPortal.current &&
                createPortal(
                    <>
                        <ChatbotWindow />
                    </>,
                    navigationPortal.current
                )}
        </>
    );
};

export default Modals;
