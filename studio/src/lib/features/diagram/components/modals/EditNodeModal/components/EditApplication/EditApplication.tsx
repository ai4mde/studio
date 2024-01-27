import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import React from "react";
import { Save } from "react-feather";
import { Node } from "reactflow";
import style from "./editapplication.module.css";

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

export const EditApplication: React.FC<Props> = ({ node }) => {
    const { diagram } = useDiagramStore();

    const handleSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        partialUpdateNode(diagram, node.id, {
            data: {
                // whatever json you want to push
            },
        });
    };

    return (
        <div className="flex flex-col gap-2 font-mono w-full">
            <span className="text-xs font-mono py-1 w-full border-b border-solid border-gray-400">
                Application Settings
            </span>
            <form onSubmit={handleSubmit}>
                <Button dirty={false} />
            </form>
        </div>
    );
};

export default EditApplication;
