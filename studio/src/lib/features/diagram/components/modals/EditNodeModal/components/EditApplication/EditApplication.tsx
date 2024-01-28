import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import React from "react";
import { Save } from "lucide-react";
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
        <div className="flex w-full flex-col gap-2 font-mono">
            <span className="w-full border-b border-solid border-gray-400 py-1 font-mono text-xs">
                Application Settings
            </span>
            <form onSubmit={handleSubmit}>
                <Button dirty={false} />
            </form>
        </div>
    );
};

export default EditApplication;
