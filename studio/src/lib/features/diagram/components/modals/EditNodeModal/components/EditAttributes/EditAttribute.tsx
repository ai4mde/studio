import { X } from "lucide-react";
import React from "react";
import style from "./editattributes.module.css";
import { Tooltip } from "@mui/joy";

const EditAttribute: React.FC<{
    attribute: any;
    update: (v: any) => void;
    del: () => void;
    dirty?: boolean;
    create?: boolean;
}> = ({ attribute, del, update, dirty, create }) => {
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
            <Tooltip
                size="sm"
                placement="left"
                title={`Make attribute ${
                    attribute?.derived ? "public" : "derived"
                }`}
            >
                <button
                    className="p-2"
                    onClick={() => {
                        update({ ...attribute, derived: !attribute?.derived });
                    }}
                >
                    {attribute?.derived ? "/" : "+"}
                </button>
            </Tooltip>
            <input
                type="text"
                value={attribute?.name}
                onChange={(e) => update({ ...attribute, name: e.target.value })}
            ></input>
            <span className="p-2">:</span>
            <select
                value={attribute?.type}
                onChange={(e) => update({ ...attribute, type: e.target.value })}
            >
                <option value="str">string</option>
                <option value="int">integer</option>
                <option value="bool">boolean</option>
            </select>
            <button type="button" onClick={del} className={style.delete}>
                <X size={12} />
            </button>
        </div>
    );
};

export default EditAttribute;
