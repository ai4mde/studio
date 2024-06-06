import React from "react";
import style from "./contextmenu.module.css";

type Props = {
    children: React.ReactNode;
    x: number;
    y: number;
};

const ContextMenu: React.FC<Props> = ({ children, x, y }) => {
    return (
        <div
            className={style.pane}
            style={{
                left: x,
                top: y,
            }}
        >
            <ul>{children}</ul>
        </div>
    );
};

export default ContextMenu;
