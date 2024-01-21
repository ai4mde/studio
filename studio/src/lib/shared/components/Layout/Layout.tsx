import { Button, Tooltip } from "@mui/joy";
import { useAtom } from "jotai";
import { Bot, Package, Settings } from "lucide-react";
import React from "react";
// import ChatbotWindow from 'src/nextgen/chatbot/components/ChatbotWindow/ChatbotWindow'
import { chatbotOpenAtom } from "$chatbot/atoms";
// import Navigation from 'src/nextgen/layout/components/Navigation/Navigation'
import { navigationPortalAtom } from "$shared/hooks/navigationPortal";
import style from "./layout.module.css";

export const Layout: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [, setChatbot] = useAtom(chatbotOpenAtom);
  const [ref] = useAtom(navigationPortalAtom);

  return (
    <>
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
              <Bot
                style={{
                  fill: "transparent",
                  stroke: "black",
                }}
                size={20}
              />
            </Button>
          </Tooltip>

          <Tooltip title="Settings" variant="solid">
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
        </div>
      </header>
      {/* <Navigation /> */}
      <main
        className={style.main}
        style={{
          left: "3rem",
        }}
      >
        {children}
      </main>
      {/* <ChatbotWindow /> */}
    </>
  );
};

export default Layout;
