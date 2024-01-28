import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import React, { useState } from "react";
import { Save } from "lucide-react";
import { Node } from "reactflow";
import style from "./editname.module.css";

type Props = {
    node: Node;
};

const Button: React.FC<any> = ({ dirty }) => {
    return (
        <button type="submit" className={style.save} disabled={!dirty}>
            <Save size={12} />
        </button>
    );
};

export const EditName: React.FC<Props> = ({ node }) => {
    const [name, setName] = useState(node.data.name);
    const { diagram } = useDiagramStore();

    const handleSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        partialUpdateNode(diagram, node.id, {
            data: {
                name: name,
            },
        });
    };

    return (
        <div className="flex w-full flex-col gap-2 font-mono">
            <span className="w-full border-b border-solid border-gray-400 py-1 font-mono text-xs">
                Name
            </span>
            <form
                className={[
                    style.editname,
                    name != node.data.name && style.dirty,
                ]
                    .filter(Boolean)
                    .join(" ")}
                onSubmit={handleSubmit}
            >
                <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                ></input>
                <Button dirty={name != node.data.name} />
            </form>
        </div>
    );
};

export default EditName;
