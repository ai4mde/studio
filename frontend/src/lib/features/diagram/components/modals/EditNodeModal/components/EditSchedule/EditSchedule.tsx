import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { Save } from "lucide-react";
import React, { useState } from "react";
import { Node } from "reactflow";
import { Cron } from "react-js-cron";
import "react-js-cron/dist/styles.css";
import style from "./editschedule.module.css";

type Props = {
    node: Node;
    attribute: string;
};

const Button: React.FC<any> = ({ dirty }) => (
    <button type="submit" className={style.save} disabled={!dirty}>
        <Save size={12} />
    </button>
);

export const EditSchedule: React.FC<Props> = ({ node, attribute }) => {
    const [value, setValue] = useState(node.data[attribute] ?? "");
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
        <form
            className={[
                style.editschedule,
                value !== node.data[attribute] && style.dirty,
            ]
                .filter(Boolean)
                .join(" ")}
            onSubmit={handleSubmit}
        >
            <div className="flex flex-col gap-2 w-full">
                <label className="block text-xs font-semibold mb-1">Schedule</label>
                <Cron
                    value={value}
                    setValue={setValue}
                    humanizeValue
                    leadingZero
                />
                <Button dirty={value !== node.data[attribute]} />
            </div>
        </form>
    );
};

export default EditSchedule;