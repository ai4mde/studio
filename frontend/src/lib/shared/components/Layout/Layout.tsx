import { chatbotOpenAtom } from "$chatbot/atoms";
import LoginScreen from "$lib/features/auth/components/LoginScreen";
import { useAuthStore } from "$lib/features/auth/state/auth";
import Modals from "$shared/components/Modals/Modals";
import { Navigation } from "$shared/components/Navigation/Navigation";
import { navigationPortalAtom } from "$shared/hooks/navigationPortal";
import { Button, Tooltip } from "@mui/joy";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useAtom } from "jotai";
import { MessageSquare, Package, Settings } from "lucide-react";
import React from "react";
import style from "./style.module.css";

export const Layout: React.FC<React.PropsWithChildren> = ({ children }) => {
    const [, setChatbot] = useAtom(chatbotOpenAtom);
    const [ref] = useAtom(navigationPortalAtom);
    const { isAuthenticated } = useAuthStore();

    if (!isAuthenticated) {
        return <LoginScreen />;
    }

    return (
        <>
            <ReactQueryDevtools />
            <header className="fixed flex flex-row w-full h-12 gap-2 border-solid border-b border-b-stone-300">
                <a
                    href="/"
                    className="flex flex-row items-center gap-1 select-none text-sm h-full text-stone-800 hover:bg-blue-50 border-r border-solid border-r-stone-200 px-4"
                >
                    <Package size={20} />
                    <span className="ml-1 font-bold">AI4MDE</span>
                    <span>Studio</span>
                </a>

                <div ref={ref} className="h-full w-full" />

                <div className="flex flex-row w-fit ml-auto pr-4 pl-2 items-center">
                    <Tooltip title="Chatbot" variant="solid">
                        <Button
                            aria-label="Chatbot"
                            onClick={() => setChatbot(true)}
                            variant="plain"
                            color="neutral"
                        >
                            <MessageSquare
                                style={{
                                    fill: "transparent",
                                    stroke: "black",
                                }}
                                size={20}
                            />
                        </Button>
                    </Tooltip>

                    {/* This button can be enabled when
                        settings functionality is added. */}

                    {/*<Tooltip title="Settings" variant="solid">
                        <Button
                            type="link"
                            href="/settings"
                            component="a"
                            variant="plain"
                            color="neutral"
                        >
                            <Settings
                                style={{
                                    fill: "transparent",
                                    stroke: "black",
                                }}
                                size={20}
                            />
                        </Button>
                    </Tooltip>
                    */}
                </div>
            </header>
            <Navigation />
            <main
                className={style.main}
                style={{
                    left: "3rem",
                }}
            >
                {children}
            </main>
            <Modals />
        </>
    );
};

export default Layout;
