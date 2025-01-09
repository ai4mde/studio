import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import React, { useState } from "react";
import { Save } from "lucide-react";
import { Node } from "reactflow";
import style from "./editboolean.module.css";

type Props = {
    node: Node;
    attribute: string;
}

const Button: React.FC<any> = ({ dirty }) => {
    return (
        <button type="submit" className={style.save} disabled={!dirty}>
            <Save size={12} />
        </button>
    );
};

export const EditBoolean: React.FC<Props> = ({ node, attribute }) => {
    const [value, setValue] = useState(node.data[attribute]);
    const { diagram } = useDiagramStore();

    const handleSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        partialUpdateNode(diagram, node.id, {
            cls: {
                [attribute]: value,
            },
        });
    };

    return (
        <div className="flex w-full flex-col gap-2 font-mono">
            <span className="w-full border-b border-solid border-gray-400 py-1 font-mono text-xs">
                {attribute.charAt(0).toUpperCase() + attribute.slice(1)}
            </span>
            <form
                className={[
                    style.editboolean,
                    value != node.data[attribute] && style.dirty,
                ]
                    .filter(Boolean)
                    .join(" ")}
                onSubmit={handleSubmit}
            >
                <input
                    type="checkbox"
                    checked={value}
                    onChange={(e) => setValue(e.target.checked)}
                />
                <Button dirty={value != node.data[attribute]} />
            </form>
        </div>
    );
};

export default EditBoolean;