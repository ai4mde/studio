import Editor from "@monaco-editor/react";
import { X } from "lucide-react";
import React from "react";
import style from "./editmethods.module.css";

const EditMethod: React.FC<{
    method: any;
    update: (v: any) => void;
    del: () => void;
    dirty?: boolean;
    create?: boolean;
}> = ({ method, del, update, dirty, create }) => {
    return (
        <div
            className={[style.method, create && style.new, dirty && style.dirty]
                .filter(Boolean)
                .join(" ")}
        >
            <div className={style.header}>
                <span className="p-2">+</span>
                <input
                    type="text"
                    value={method?.name}
                    onChange={(e) =>
                        update({ ...method, name: e.target.value })
                    }
                ></input>
                <span className="p-2">:</span>
                <select
                    value={method?.type}
                    onChange={(e) =>
                        update({ ...method, type: e.target.value })
                    }
                >
                    <option value="str">string</option>
                    <option value="int">integer</option>
                    <option value="bool">boolean</option>
                </select>
                <button type="button" onClick={del} className={style.delete}>
                    <X size={12} />
                </button>
            </div>
            <div className={style.body}>
                <Editor
                    value={method?.body}
                    language="python"
                    options={{
                        lineNumbers: "off",
                        folding: false,
                    }}
                    height="12rem"
                    width="100%"
                    onChange={(e) => update({ ...method, body: e ?? "" })}
                />
            </div>
        </div>
    );
};

export default EditMethod;
