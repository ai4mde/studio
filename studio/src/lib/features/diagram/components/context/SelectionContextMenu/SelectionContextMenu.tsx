import { useSelectionContextMenu } from "$diagram/stores/contextMenus";
import React from "react";
import { Copy, UploadCloud } from "lucide-react";
import ContextMenu from "$diagram/components/context/ContextMenu/ContextMenu";

const SelectionContextMenu: React.FC = () => {
    const { x, y } = useSelectionContextMenu();

    return (
        <ContextMenu x={x} y={y}>
            <>
                <li>
                    <button disabled>
                        <span>Copy</span>
                        <Copy size={14} />
                    </button>
                </li>
                <hr className="my-1" />
                <li>
                    <button>
                        <span>Upload as Component</span>
                        <UploadCloud size={14} />
                    </button>
                </li>
            </>
        </ContextMenu>
    );
};

export default SelectionContextMenu;
