import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import React, { useState } from "react";
import { Save } from "lucide-react";
import { Node } from "reactflow";
import style from "./editdimensions.module.css";

type Props = {
    node: Node;
    dimension: "width" | "height";
}

const Button: React.FC<any> = ({ dirty }) => {
    return (
        <button type="submit" className={style.save} disabled={!dirty}>
            <Save size={12} />
        </button>
    );
};

export const EditDimensions: React.FC<Props> = ({ node, dimension }) => {
    const [value, setValue] = useState(node.data[dimension]);
    const { diagram } = useDiagramStore();

    const handleSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        partialUpdateNode(diagram, node.id, {
            cls: {
                [dimension]: value,
            },
        });
    };

    return (
        <div className="flex w-full flex-col gap-2 font-mono">
            <span className="w-full border-b border-solid border-gray-400 py-1 font-mono text-xs">
                {dimension.charAt(0).toUpperCase() + dimension.slice(1)}
            </span>
            <form
                className={[
                    style.editdimensions,
                    value != node.data[dimension] && style.dirty,
                ]
                    .filter(Boolean)
                    .join(" ")}
                onSubmit={handleSubmit}
            >
                <input
                    type="number"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                ></input>
                <Button dirty={value != node.data[dimension]} />
            </form>
        </div>
    );
};

export default EditDimensions;