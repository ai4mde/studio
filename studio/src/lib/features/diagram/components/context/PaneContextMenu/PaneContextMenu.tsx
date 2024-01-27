import { usePaneContextMenu } from "$diagram/stores/contextMenus";
import React from "react";
import { useNewNodeModal } from "$diagram/stores/modals";
import {
    Bot,
    BoxSelect,
    Clipboard,
    DownloadCloud,
    Image,
    Plus,
} from "lucide-react";
import ContextMenu from "$diagram/components/context/ContextMenu/ContextMenu";

const PaneContextMenu: React.FC = () => {
    const { x, y, close } = usePaneContextMenu();
    const newNodeModal = useNewNodeModal();

    return (
        <ContextMenu x={x} y={y}>
            <>
                <li>
                    <button
                        onClick={() => {
                            newNodeModal.open();
                            close();
                        }}
                    >
                        <span>New Node</span>
                        <Plus size={14} />
                    </button>
                </li>
                <hr className="my-1" />
                <li>
                    <button disabled>
                        <span>Paste</span>
                        <Clipboard size={14} />
                    </button>
                </li>
                <hr className="my-1" />
                <li>
                    <button disabled>
                        <span>Copy Diagram as Image</span>
                        <Image size={14} />
                    </button>
                </li>
                <li>
                    <button disabled>
                        <span>Select All</span>
                        <BoxSelect size={14} />
                    </button>
                </li>
                <li>
                    <button disabled>
                        <span>Open Chatbot</span>
                        <Bot size={14} />
                    </button>
                </li>
                <li>
                    <button>
                        <span>Import Component</span>
                        <DownloadCloud size={14} />
                    </button>
                </li>
            </>
        </ContextMenu>
    );
};

export default PaneContextMenu;
