import { X } from "lucide-react";
import React from "react";
import style from "./editliterals.module.css";

const EditLiteral: React.FC<{
    literal: any;
    update: (v: any) => void;
    del: () => void;
    dirty?: boolean;
    create?: boolean;
}> = ({ literal, del, update, dirty, create }) => {
    return (
        <div
            className={[
                style.attribute,
                create && style.new,
                dirty && style.dirty,
            ]
                .filter(Boolean)
                .join(" ")}
        >
            <input
                type="text"
                value={literal}
                onChange={(e) => update(e.target.value)}
            ></input>
            <button type="button" onClick={del} className={style.delete}>
                <X size={12} />
            </button>
        </div>
    );
};

export default EditLiteral;
