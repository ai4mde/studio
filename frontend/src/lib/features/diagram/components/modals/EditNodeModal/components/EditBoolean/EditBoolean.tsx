import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { Save } from "lucide-react";
import React, { useState } from "react";
import { Node } from "reactflow";
import style from "./editboolean.module.css";
import { FormHelperText, Switch } from "@mui/joy";

type Props = {
    node: Node;
    attribute: string;
    helperText: {
        trueText: string;
        falseText: string;
    }
}

const Button: React.FC<any> = ({ dirty }) => {
    return (
        <button type="submit" className={style.save} disabled={!dirty}>
            <Save size={12} />
        </button>
    );
};

export const EditBoolean: React.FC<Props> = ({ node, attribute, helperText }) => {
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
                { value ? helperText.trueText : helperText.falseText }
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
                <div className="flex items-center justify-between w-full">
                    <div className="flex items-stretch">
                        <Switch
                            checked={value}
                            onChange={(e) => setValue(e.target.checked)}
                        />
                    </div>
                    <Button dirty={value != node.data[attribute]} />
                </div>
            </form>
        </div>
    );
};

export default EditBoolean;